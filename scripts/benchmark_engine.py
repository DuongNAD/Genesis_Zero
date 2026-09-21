#!/usr/bin/env python3
"""scripts/benchmark_engine.py — Simulation Engine Throughput & Profiling Benchmark.

Measures:
1. Headless simulation throughput (pure simulation loop ticks/s and CLI run).
2. cProfile cumulative time analysis of key bottlenecks:
   - World.dist
   - World.passable
   - lawhook.build_ctx
3. Invariant B-02 Seed Determinism verification (byte-for-byte JSONL matching).
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path if not present
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from genesis.run import _m0_loop, main
from genesis.tick import build_match

# Unoptimized Baseline Constants (from 400-tick baseline measurements on seed 42)
BASELINE_CUMTIME = {
    "dist": 0.532,
    "passable": 0.351,
    "build_ctx": 0.281,
    "total": 1.164,
}
BASELINE_TICKS_PER_SEC = 695.0
TARGET_TICKS_PER_SEC = 900.0
TARGET_REDUCTION_RATIO = 0.50  # >= 50% cumulative time reduction


def measure_pure_simulation(seed: int = 42, ticks: int = 400, runs: int = 3) -> tuple[float, float]:
    """Measure pure simulation loop throughput (no disk I/O)."""
    times: list[float] = []
    for _ in range(runs):
        world, creatures, _, rng = build_match(seed)
        t0 = time.perf_counter()
        _m0_loop(world, creatures, None, rng, ticks, match_seed=seed)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)

    best_elapsed = min(times)
    ticks_per_sec = ticks / best_elapsed if best_elapsed > 0 else 0.0
    return best_elapsed, ticks_per_sec


def measure_in_process_cli(seed: int = 42, ticks: int = 400, runs: int = 3) -> tuple[float, float, bytes]:
    """Measure full simulation with LogWriter JSONL emission."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / f"bench_{seed}.jsonl"
        times: list[float] = []
        last_bytes = b""
        for _ in range(runs):
            if out_path.exists():
                out_path.unlink()
            t0 = time.perf_counter()
            main(["--seed", str(seed), "--ticks", str(ticks), "--out", str(out_path), "--no-render"])
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
            last_bytes = out_path.read_bytes()

        best_elapsed = min(times)
        ticks_per_sec = ticks / best_elapsed if best_elapsed > 0 else 0.0
        return best_elapsed, ticks_per_sec, last_bytes


def profile_bottlenecks(seed: int = 42, ticks: int = 400) -> dict[str, dict[str, float]]:
    """Run cProfile on 400 ticks and extract metrics for dist, passable, and build_ctx."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / f"profile_{seed}.jsonl"
        pr = cProfile.Profile()
        pr.enable()
        main(["--seed", str(seed), "--ticks", str(ticks), "--out", str(out_path), "--no-render"])
        pr.disable()

        ps = pstats.Stats(pr)
        metrics: dict[str, dict[str, float]] = {}

        # Look up function stats by matching filename and function name
        for (filename, _lineno, func_name), (_cc, nc, tottime, cumtime, _callers) in ps.stats.items():
            fn_norm = filename.replace("\\", "/")
            if "genesis/world.py" in fn_norm and func_name == "dist":
                metrics["dist"] = {"ncalls": nc, "tottime": tottime, "cumtime": cumtime}
            elif "genesis/world.py" in fn_norm and func_name == "passable":
                metrics["passable"] = {"ncalls": nc, "tottime": tottime, "cumtime": cumtime}
            elif "genesis/lawhook.py" in fn_norm and func_name == "build_ctx":
                metrics["build_ctx"] = {"ncalls": nc, "tottime": tottime, "cumtime": cumtime}

        return metrics


def verify_determinism(seed: int = 42, ticks: int = 400) -> bool:
    """Verify Invariant B-02: two independent simulation runs yield 100% byte-for-byte identical output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p1 = Path(tmp_dir) / "run1.jsonl"
        p2 = Path(tmp_dir) / "run2.jsonl"
        main(["--seed", str(seed), "--ticks", str(ticks), "--out", str(p1), "--no-render"])
        main(["--seed", str(seed), "--ticks", str(ticks), "--out", str(p2), "--no-render"])
        b1 = p1.read_bytes()
        b2 = p2.read_bytes()
        return (len(b1) > 0) and (b1 == b2)


def main_cli() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Simulation Engine Throughput & Bottlenecks.")
    parser.add_argument("--seed", type=int, default=42, help="Simulation seed (default: 42)")
    parser.add_argument("--ticks", type=int, default=400, help="Number of ticks (default: 400)")
    parser.add_argument("--runs", type=int, default=3, help="Benchmark iterations (default: 3)")
    parser.add_argument("--check-only", action="store_true", help="Quick pass/fail check without verbose tables")
    args = parser.parse_args()

    print("=" * 72)
    print(" GENESIS ZERO — SIMULATION ENGINE THROUGHPUT & PROFILING BENCHMARK")
    print(f" Seed: {args.seed} | Ticks: {args.ticks} | Repetitions: {args.runs}")
    print("=" * 72)

    # 1. Determinism Verification (Invariant B-02)
    print("\n[Phase 1] Verifying Invariant B-02 (Seed Determinism)...")
    is_deterministic = verify_determinism(args.seed, args.ticks)
    det_status = "PASS (100% Bitwise Parity)" if is_deterministic else "FAIL (Output Mismatch)"
    print(f"  Invariant B-02 Parity: {det_status}")

    # 2. Pure Simulation Throughput
    print("\n[Phase 2] Measuring Pure Simulation Throughput (Headless Engine)...")
    pure_el, pure_tps = measure_pure_simulation(args.seed, args.ticks, args.runs)
    print(f"  Best Elapsed: {pure_el:.4f}s")
    print(f"  Throughput:   {pure_tps:.1f} ticks/s (Target: >= {TARGET_TICKS_PER_SEC} ticks/s)")
    pure_pass = pure_tps >= TARGET_TICKS_PER_SEC

    # 3. In-Process CLI Throughput
    print("\n[Phase 3] Measuring In-Process Full Run (with JSONL logging)...")
    cli_el, cli_tps, out_bytes = measure_in_process_cli(args.seed, args.ticks, args.runs)
    print(f"  Best Elapsed: {cli_el:.4f}s")
    print(f"  Throughput:   {cli_tps:.1f} ticks/s")
    print(f"  JSONL Size:   {len(out_bytes):,} bytes")

    # 4. cProfile Bottleneck Profiling
    print("\n[Phase 4] Profiling Core Bottlenecks via cProfile...")
    prof_metrics = profile_bottlenecks(args.seed, args.ticks)

    print("\n" + "-" * 72)
    print(f"{'Target Function':<24} | {'Base Cum (s)':<12} | {'Opt Cum (s)':<12} | {'Reduction':<10} | {'Status':<6}")
    print("-" * 72)

    all_reductions_pass = True
    total_base = BASELINE_CUMTIME["total"]
    total_opt = 0.0

    for name in ("dist", "passable", "build_ctx"):
        base_cum = BASELINE_CUMTIME.get(name, 0.0)
        data = prof_metrics.get(name, {})
        opt_cum = data.get("cumtime", 0.0)
        total_opt += opt_cum
        reduct = ((base_cum - opt_cum) / base_cum) * 100 if base_cum > 0 else 0.0
        passed = reduct >= (TARGET_REDUCTION_RATIO * 100)
        if not passed:
            all_reductions_pass = False
        print(f"{name:<24} | {base_cum:<12.4f} | {opt_cum:<12.4f} | {reduct:>8.1f}% | {'PASS' if passed else 'FAIL'}")

    total_reduct = ((total_base - total_opt) / total_base) * 100 if total_base > 0 else 0.0
    total_passed = total_reduct >= (TARGET_REDUCTION_RATIO * 100)
    print("-" * 72)
    print(f"{'TOTAL (3 Bottlenecks)':<24} | {total_base:<12.4f} | {total_opt:<12.4f} | {total_reduct:>8.1f}% | {'PASS' if total_passed else 'FAIL'}")
    print("-" * 72)

    # Final Acceptance Summary
    print("\n" + "=" * 72)
    print(" ACCEPTANCE CRITERIA VERIFICATION SUMMARY")
    print("=" * 72)
    print(f" 1. Pure Throughput >= 900 ticks/s:       {pure_tps:.1f} ticks/s -> {'PASS' if pure_pass else 'FAIL'}")
    print(f" 2. Bottlenecks Cumtime Reduction >= 50%: {total_reduct:.1f}% reduction -> {'PASS' if total_passed and all_reductions_pass else 'FAIL'}")
    print(f" 3. Invariant B-02 Seed Determinism:      100% Byte-for-Byte -> {'PASS' if is_deterministic else 'FAIL'}")
    print("=" * 72)

    success = pure_pass and total_passed and is_deterministic
    if success:
        print("\n>>> ALL SIMULATION ENGINE ACCEPTANCE TARGETS ACHIEVED SUCCESSFULLY <<<")
        return 0
    else:
        print("\n>>> ONE OR MORE BENCHMARK TARGETS WERE NOT MET <<<")
        return 1


if __name__ == "__main__":
    sys.exit(main_cli())

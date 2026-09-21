"""Paired B-10 experiment. --plan records the protocol without model calls."""
import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SEEDS = (7, 9, 42, 55, 101)


def summarize(rows):
    if not rows:
        raise ValueError("Scorer produced no rows")
    values = [float(r["match"]) for r in rows]
    return {
        "mean_match": statistics.mean(values),
        "best_match": max(values),
        "found_fraction": statistics.mean(float(r["found"]) for r in rows),
    }


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", required=True, help="Frontier LLM endpoint URL")
    ap.add_argument("--model", required=True, help="Frontier LLM model name")
    ap.add_argument("--out", type=Path, required=True, help="Output directory")
    ap.add_argument("--local-url", default=None, help="Local LLM endpoint URL (for 3-way benchmark)")
    ap.add_argument("--local-model", default=None, help="Local LLM model name (for 3-way benchmark)")
    ap.add_argument("--ticks", type=int, default=200)
    ap.add_argument("--thinking-tokens", type=int, default=2048)
    ap.add_argument("--timeout", type=float, default=7200)
    ap.add_argument("--plan", action="store_true", help="Record protocol without calling models")
    return ap


def validate_args(a, ap):
    from urllib.parse import urlsplit

    url = urlsplit(a.url)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query:
        ap.error("Endpoint must be HTTP(S), without credentials or query parameters")

    if a.local_url is not None:
        l_url = urlsplit(a.local_url)
        if (
            l_url.scheme not in ("http", "https")
            or not l_url.hostname
            or l_url.username
            or l_url.password
            or l_url.query
        ):
            ap.error("Local endpoint must be HTTP(S), without credentials or query parameters")

    if bool(a.local_url) != bool(a.local_model):
        ap.error("Both --local-url and --local-model must be specified for 3-way benchmarking")

    if a.ticks <= 0 or a.timeout <= 0 or a.thinking_tokens < 0:
        ap.error("ticks/timeout must be positive; thinking-tokens non-negative")


def build_protocol(a, root=ROOT):
    is_3way = bool(a.local_url and a.local_model)
    if is_3way:
        order = [
            tuple(["frontier", "local", "reflex"][(i + j) % 3] for j in range(3))
            for i in range(len(SEEDS))
        ]
    else:
        order = [("frontier", "reflex") if i % 2 == 0 else ("reflex", "frontier") for i in range(len(SEEDS))]

    protocol = {
        "schema_version": "1.0",
        "benchmark_type": "3-way" if is_3way else "2-way",
        "seeds": list(SEEDS),
        "ticks": a.ticks,
        "arm": "STANDARD",
        "hunch": False,
        "model": a.model,
        "url": a.url,
        "local_model": a.local_model,
        "local_url": a.local_url,
        "thinking_tokens": a.thinking_tokens,
        "primary": "paired per-seed mean_match delta; exploratory n=5",
        "order": order,
        "source_sha256": {
            p: hashlib.sha256((root / p).read_bytes()).hexdigest()
            for p in (
                "genesis/prompt.py",
                "genesis/llm_client.py",
                "genesis/score.py",
                "genesis/strategist.py",
                "genesis/run.py",
            )
            if (root / p).exists()
        },
    }
    return protocol, is_3way


def run_benchmark(a, runner_fn=None):
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    protocol, is_3way = build_protocol(a)
    (a.out / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    if a.plan:
        print("Protocol written. No model calls or measured results.")
        return 0

    from genesis.score import score_match

    results, valid = [], True
    for i, seed in enumerate(SEEDS):
        pair, truths = {}, []
        for controller in protocol["order"][i]:
            stem = a.out / f"{seed}-{controller}"
            log, truth = stem.with_suffix(".jsonl"), stem.with_suffix(".truth.json")
            if controller == "frontier":
                backend = "frontier"
                model = a.model
                target_url = a.url
            elif controller == "local":
                backend = "local"
                model = a.local_model
                target_url = a.local_url
            else:
                backend = "reflex"
                model = a.model
                target_url = a.url

            env = dict(
                os.environ,
                PYTHONIOENCODING="utf-8",
                PYTHONUTF8="1",
                GENESIS_LLM_BACKEND=backend,
                GENESIS_LLM_MODEL=model,
                GENESIS_THINKING_TOKENS=str(a.thinking_tokens),
            )
            cmd = [
                sys.executable,
                "-X",
                "utf8",
                "-m",
                "genesis.run",
                "--seed",
                str(seed),
                "--ticks",
                str(a.ticks),
                "--no-render",
                "--out",
                str(log),
                "--truth",
                str(truth),
            ]
            if controller in ("frontier", "local"):
                cmd += ["--llm", "all", "--llm-url", target_url]
            else:
                cmd += ["--controller", "reflex"]

            if runner_fn is not None:
                runner_fn(
                    cmd=cmd,
                    cwd=ROOT,
                    env=env,
                    log=log,
                    truth=truth,
                    seed=seed,
                    controller=controller,
                    timeout=a.timeout,
                )
            else:
                with stem.with_suffix(".stderr.log").open("w", encoding="utf-8") as errors:
                    subprocess.run(
                        cmd,
                        cwd=ROOT,
                        env=env,
                        check=True,
                        timeout=a.timeout,
                        stdout=subprocess.DEVNULL,
                        stderr=errors,
                    )

            truths.append(json.loads(truth.read_text(encoding="utf-8")))
            rows = score_match(log, truth)
            metrics = summarize(rows)
            with stem.with_suffix(".csv").open("w", encoding="utf-8", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
            misses = sum(e.get("kind") == "LLM_MISS" for e in events)
            calls = sum(e.get("kind") == "LLM_CALL" for e in events)
            pair[controller] = {**metrics, "llm_calls": calls, "llm_misses": misses}
            if controller in ("frontier", "local") and (misses or not calls):
                valid = False

        for t in truths[1:]:
            if t != truths[0]:
                raise RuntimeError(f"Seed {seed}: paired truth mismatch")

        if is_3way:
            delta_fr = pair["frontier"]["mean_match"] - pair["reflex"]["mean_match"]
            delta_lr = pair["local"]["mean_match"] - pair["reflex"]["mean_match"]
            delta_fl = pair["frontier"]["mean_match"] - pair["local"]["mean_match"]
            results.append({
                "seed": seed,
                **pair,
                "delta": delta_fr,
                "delta_frontier_reflex": delta_fr,
                "delta_local_reflex": delta_lr,
                "delta_frontier_local": delta_fl,
            })
        else:
            delta = pair["frontier"]["mean_match"] - pair["reflex"]["mean_match"]
            results.append({
                "seed": seed,
                **pair,
                "delta": delta,
            })
        (a.out / "pairs.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    if is_3way:
        mean_fr = statistics.mean(r["delta_frontier_reflex"] for r in results)
        mean_lr = statistics.mean(r["delta_local_reflex"] for r in results)
        mean_fl = statistics.mean(r["delta_frontier_local"] for r in results)
        report = {
            "status": "complete" if valid else "degraded_model_calls",
            "benchmark_type": "3-way",
            "mean_paired_delta": mean_fr,
            "mean_delta_frontier_reflex": mean_fr,
            "mean_delta_local_reflex": mean_lr,
            "mean_delta_frontier_local": mean_fl,
            "pairs": results,
        }
    else:
        report = {
            "status": "complete" if valid else "degraded_model_calls",
            "benchmark_type": "2-way",
            "mean_paired_delta": statistics.mean(r["delta"] for r in results),
            "pairs": results,
        }
    (a.out / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if valid else 1


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    validate_args(a, ap)
    return run_benchmark(a)



if __name__ == "__main__":
    raise SystemExit(main())

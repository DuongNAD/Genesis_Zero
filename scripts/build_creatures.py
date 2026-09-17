#!/usr/bin/env python3
"""Genesis Zero — Dựng model 3D sinh vật tự động bằng Blender + AGY CLI.
Thay thế hoàn toàn Meshy AI:
- Hoàn toàn miễn phí, chạy trực tiếp trên máy qua Blender 5.2.1 LTS.
- Dựng mô hình hữu cơ đầy đủ giải phẫu, khớp với 6 Vector Traits và 12 Features.
- Tự động gắn Rigging Armature phân cấp và Keyframe Animation (Idle, Walk, Swim, Fly).
- Hỗ trợ AGY CLI (mô hình kiến trúc mcp-agy) để suy luận từ prompt và tinh chỉnh agentic.

Cách dùng:
    # 1. Sinh trực tiếp 1 sinh vật (L1, seed 1) trong 1 giây:
    python scripts/build_creatures.py --species L1 --seed 1

    # 2. Sinh toàn bộ 7 loài cho N seed:
    python scripts/build_creatures.py --all --seeds 2

    # 3. Sử dụng AGY CLI để suy luận agentic từ prompt:
    python scripts/build_creatures.py --agy --species L1 --seed 1
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from genesis import config
from genesis.creature_builder import build_creature_blender_code
from genesis.domain import domain_of
from genesis.features import describe, roll_for_species
from genesis.mesh_prompts import creature_prompt
from genesis.traits import founder_traits

OUT_DIR = ROOT / "assets" / "creatures"

BLENDER_BIN_CANDIDATES = [
    "/Applications/Blender.app/Contents/MacOS/Blender",
    shutil.which("blender") or "",
]


def find_blender() -> str:
    override = os.environ.get("GENESIS_BLENDER_BIN") or os.environ.get("BLENDER_BIN")
    base = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Blender Foundation"
    candidates = [override] if override else [
        *BLENDER_BIN_CANDIDATES,
        *(str(p) for p in sorted(base.glob("Blender*/blender.exe"), reverse=True)),
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise RuntimeError("Không tìm thấy Blender; đặt GENESIS_BLENDER_BIN tới blender executable.")


def find_agy() -> str:
    agy_path = (
        os.environ.get("AGY_BIN_PATH")
        or shutil.which("agy")
        or os.path.expanduser("~/.local/bin/agy")
        or os.path.expanduser("~/.gemini/antigravity-cli/bin/agy")
    )
    if os.path.isfile(agy_path) and os.access(agy_path, os.X_OK):
        return agy_path
    raise RuntimeError("Không tìm thấy agy CLI trên PATH hoặc ~/.local/bin/agy!")


def build_single_creature(
    species_id: str,
    seed: int,
    blender_bin: str,
    verbose: bool = False,
    *,
    output_dir: Path | None = None,
    timeout: float = 180,
) -> Path:
    """Sinh mô hình sinh vật bằng Blender headless procedural generator."""
    if species_id not in config.FOUNDERS:
        raise ValueError(f"Unknown species: {species_id}")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    destination = (output_dir or OUT_DIR).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    out_glb = destination / f"creature_{species_id}_s{seed}.glb"
    out_blend = destination / f"creature_{species_id}_s{seed}.blend"
    if output_dir is not None and (out_glb.exists() or out_blend.exists()):
        raise FileExistsError("Output exists; choose a new --output directory")

    code = build_creature_blender_code(
        species_id=species_id,
        seed=seed,
        out_glb=out_glb.as_posix(),
        out_blend=out_blend.as_posix(),
    )
    code = "import bpy\nbpy.context.preferences.filepaths.save_version = 0\n" + code
    compile(code, "<local-creature>", "exec")

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
        tf.write(code)
        tmp_script = tf.name

    try:
        cmd = [blender_bin, "--background", "--factory-startup", "--python", tmp_script]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            print(f"Lỗi khi chạy Blender cho {species_id}_s{seed}:\n{proc.stderr[:400]}")
            raise RuntimeError(f"Blender failed with exit code {proc.returncode}")
        if not (out_glb.is_file() and out_glb.stat().st_size > 0):
            raise RuntimeError("Blender exited successfully but GLB was not produced")
        if verbose:
            print(proc.stdout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Blender timeout after {timeout}s") from exc
    finally:
        if os.path.isfile(tmp_script):
            os.remove(tmp_script)

    print(f"  ✓ {species_id}_s{seed} → {out_glb.name} (GLB + Rig + Anim)")
    return out_glb


def run_with_agy(species_id: str, seed: int) -> None:
    """Chạy thông qua AGY CLI (Antigravity) với kiến trúc FastMCP / Subprocess như mcp-agy."""
    agy_bin = find_agy()
    traits = founder_traits(species_id)
    dom = domain_of(species_id).value
    feats = roll_for_species(species_id, seed)
    prompt = creature_prompt(traits, dom, feats)

    print(f"\n[AGY CLI] Khởi chạy Antigravity phân tích và sinh mô hình cho {species_id}_s{seed}...")
    print(f"  * Prompt: {prompt}")
    print(f"  * Đặc điểm: {describe(feats)}")

    agy_prompt = (
        f"Bạn là chuyên gia 3D Blender. Hãy sử dụng MCP server 'blender' để kiểm tra "
        f"và xuất mô hình sinh vật '{species_id}_s{seed}' theo mô tả sinh học sau: {prompt}. "
        f"Lưu file tại {OUT_DIR}/creature_{species_id}_s{seed}.glb."
    )

    cmd = [
        agy_bin,
        "--output-format", "text",
        "--dangerously-skip-permissions",
        "--print", agy_prompt,
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        print("[AGY Response]:")
        print(proc.stdout[:800])
        if proc.stderr:
            print(f"[AGY Stderr]: {proc.stderr[:300]}")
    except Exception as e:
        print(f"Lỗi khi gọi agy CLI: {e}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Genesis Zero — Studio sinh 3D Blender + AGY")
    ap.add_argument("--species", default="L1", help="Mã loài (L1..L5, W1, A1)")
    ap.add_argument("--seed", type=int, default=1, help="Hạt giống sinh thái (seed)")
    ap.add_argument("--all", action="store_true", help="Sinh toàn bộ các loài trong config.POPULATION")
    ap.add_argument("--seeds", type=int, default=1, help="Số lượng seed khi chạy --all")
    ap.add_argument("--agy", action="store_true", help="Sử dụng AGY CLI để suy luận và điều khiển sinh vật")
    ap.add_argument("--verbose", action="store_true", help="In chi tiết log Blender")
    ap.add_argument("--output", type=Path, default=None,
                    help="Thư mục output riêng (bắt đầu trống; mặc định assets/creatures)")
    args = ap.parse_args()

    blender_bin = find_blender()

    if args.agy:
        run_with_agy(args.species, args.seed)
        return 0

    if args.all:
        species_list = sorted(config.POPULATION)
        total = len(species_list) * args.seeds
        print(f"Bắt đầu sinh {total} sinh vật 3D bằng Blender ({len(species_list)} loài x {args.seeds} seed)...")
        for s in range(1, args.seeds + 1):
            for sp in species_list:
                build_single_creature(sp, s, blender_bin, verbose=args.verbose)
        print(f"\nHoàn tất sinh {total} sinh vật vào {OUT_DIR}!")
        return 0

    print(f"Bắt đầu sinh mô hình sinh vật {args.species} (seed {args.seed})...")
    build_single_creature(args.species, args.seed, blender_bin, verbose=args.verbose,
                          output_dir=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Genesis Zero — xuất toàn bộ mô tả 3D ra file để gửi thẳng cho MeshyAI.

    python scripts/mesh_export.py                 # ghi assets/meshy/
    python scripts/mesh_export.py --send          # gửi thật (cần MESHY_API_KEY)
    python scripts/mesh_export.py --send --only terrain_water
    python scripts/mesh_export.py --creatures 2   # hâm thêm 2 seed (14 mesh sinh vật)

Không có `--send` thì KHÔNG gọi mạng: chỉ ghi file để đọc và sửa câu chữ trước.
Sinh mesh tốn tiền thật, nên gửi phải là một hành động cố ý.

15 mesh tĩnh (địa hình, quả, xác, bản đồ) sinh MỘT LẦN dùng mãi. Mesh sinh vật
KHÔNG nằm ở đây: chúng phụ thuộc vector trait, tầng sống (W-18), và ba đặc điểm
bốc thăm theo (species_id, seed) (W-19). `--creatures N` xuất trước mô tả cho
N seed (7 loài × N seed) để hâm đệm — đơn vị hâm đệm là (loài, seed) vì sau W-19
đặc điểm và tầng đã đi vào khoá đệm, không còn là 20 vector trait thuần tuý nữa.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import net_config
from genesis import config
from genesis.domain import domain_of
from genesis.features import roll_for_species
from genesis.mesh_prompts import all_static_prompts, creature_prompt, meshy_payload
from genesis.traits import founder_traits

OUT = Path(__file__).resolve().parent.parent / "assets" / "meshy"


def creature_rows(seeds: int) -> list[dict]:
    """Mô tả sinh vật theo (loài, seed) để hâm đệm.

    Sau W-18/W-19, ngoại hình là hàm của (trait, tầng, ba đặc điểm). Ba đặc điểm
    được bốc theo (species_id, seed), nên đơn vị đệm đúng là (loài, seed).
    Mỗi seed có 7 loài (theo config.POPULATION), nên N seed cho 7×N mô tả.
    """
    out: list[dict] = []
    for seed in range(1, seeds + 1):
        for species_id in sorted(config.POPULATION):
            tr = founder_traits(species_id)
            dom = domain_of(species_id).value
            feats = roll_for_species(species_id, seed)
            prompt = creature_prompt(tr, dom, feats)
            out.append({
                "id": f"creature_{species_id}_s{seed}",
                "nhom": "sinh_vat",
                "species_id": species_id,
                "seed": seed,
                "domain": dom,
                "features": [f.key for f in feats],
                "prompt": prompt,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="gọi API Meshy thật")
    ap.add_argument("--creatures", type=int, default=0,
                    help="xuất thêm mô tả sinh vật cho N seed (7 loài × N seed)")
    ap.add_argument("--only", default="", help="chỉ làm một id")
    args = ap.parse_args()

    rows = all_static_prompts()
    if args.creatures:
        rows += creature_rows(args.creatures)
    if args.only:
        rows = [r for r in rows if r["id"] == args.only]
        if not rows:
            print(f"không có id {args.only!r}")
            return 2

    OUT.mkdir(parents=True, exist_ok=True)
    for r in rows:
        r["payload"] = meshy_payload(r["prompt"])
    (OUT / "prompts.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # Bản người đọc: sửa câu chữ ở đây rồi chạy lại là ra JSON mới.
    lines = ["# Mô tả 3D — sinh từ genesis/mesh_prompts.py", "",
             "> **Đừng sửa file này bằng tay.** Nó được sinh lại mỗi lần chạy",
             "> `python scripts/mesh_export.py`. Sửa `genesis/mesh_prompts.py`.", ""]
    for nhom in ("dia_hinh", "vat_the", "ban_do", "sinh_vat"):
        sel = [r for r in rows if r["nhom"] == nhom]
        if not sel:
            continue
        lines.append(f"## {nhom}  ({len(sel)})\n")
        for r in sel:
            lines.append(f"### `{r['id']}`\n\n{r['prompt']}\n")
    (OUT / "prompts.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"đã ghi {len(rows)} mô tả → {OUT}/prompts.json và prompts.md")

    if not args.send:
        print("chưa gửi. Thêm --send để gọi Meshy thật (tốn tiền).")
        return 0

    key = os.environ.get("MESHY_API_KEY", "").strip()
    if not key:
        print("thiếu MESHY_API_KEY trong biến môi trường — KHÔNG đặt khoá vào kho.")
        return 2

    import httpx

    results = {}
    with httpx.Client(timeout=60.0,
                      headers={"Authorization": f"Bearer {key}"}) as cli:
        for r in rows:
            resp = cli.post(str(net_config.MESHY_URL), json=r["payload"])
            ok = resp.status_code < 300
            body = resp.json() if ok else {"status": resp.status_code,
                                           "text": resp.text[:200]}
            results[r["id"]] = body
            print(f"  {'✓' if ok else '✗'} {r['id']}  {resp.status_code}")
    (OUT / "tasks.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"id tác vụ → {OUT}/tasks.json (poll để lấy file mesh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

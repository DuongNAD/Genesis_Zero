#!/usr/bin/env python3
"""Genesis Zero — xuất toàn bộ mô tả 3D ra file để gửi thẳng cho MeshyAI.

    python scripts/mesh_export.py                 # ghi assets/meshy/
    python scripts/mesh_export.py --send          # gửi thật (cần MESHY_API_KEY)
    python scripts/mesh_export.py --send --only terrain_water

Không có `--send` thì KHÔNG gọi mạng: chỉ ghi file để đọc và sửa câu chữ trước.
Sinh mesh tốn tiền thật, nên gửi phải là một hành động cố ý.

15 mesh tĩnh (địa hình, quả, xác, bản đồ) sinh MỘT LẦN dùng mãi. Mesh sinh vật
KHÔNG nằm ở đây: chúng phụ thuộc vector trait, chỉ biết lúc `/join`, và
`net/mesh.py` lo theo quota. `--creatures` xuất trước 20 vector trait hay gặp
nhất để hâm cache — trần đo được ở [N-13] là 20 vector, không phải 180.000
trạng thái cơ thể.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genesis import config
from genesis.mesh_prompts import all_static_prompts, creature_prompt, meshy_payload
from genesis.traits import Traits
import net_config

OUT = Path(__file__).resolve().parent.parent / "assets" / "meshy"


def creature_rows(limit: int) -> list[dict[str, str]]:
    """Các vector trait hợp lệ, ưu tiên vector 'tròn trịa' (ít cực đoan) trước.

    Tổng sáu trait luôn bằng `config.TRAIT_SUM`, nên không gian nhỏ hơn nhiều so
    với 6^6 — và phần lớn người chơi rơi vào vùng giữa.
    """
    names = ("brain", "attack", "armor", "speed", "sense", "stomach")
    rows = []
    for combo in itertools.product(range(config.TRAIT_MIN, config.TRAIT_MAX + 1),
                                   repeat=len(names)):
        if sum(combo) != config.TRAIT_SUM:
            continue
        spread = max(combo) - min(combo)
        rows.append((spread, combo))
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for _, combo in rows[:limit]:
        tr = Traits(**dict(zip(names, combo)))
        out.append({
            "id": "creature_" + "".join(str(v) for v in combo),
            "nhom": "sinh_vat",
            "prompt": creature_prompt(tr),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="gọi API Meshy thật")
    ap.add_argument("--creatures", type=int, default=0,
                    help="xuất thêm N vector trait hay gặp nhất (N-13 đo được: 20)")
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

"""W-19 — dựng mô tả sinh vật cho Meshy: tầng + ba đặc điểm + trait, rồi nhờ
Gemini viết lại cho trôi.

    python scripts/creature_design.py --seed 21
    python scripts/creature_design.py --seed 21 --rewrite      # gọi Gemini thật
    python scripts/creature_design.py --seed 21 --out assets/meshy/creatures.json

Khoá đọc từ `.env` (đã gitignore) hoặc từ biến môi trường `GEMINI_API_KEYS`.
KHÔNG có khoá nào nằm trong kho.

## Đường đi

    tầng + 3 đặc điểm + vector trait
        -> `mesh_prompts.creature_prompt`   (tất định, đúng, hơi khô)
        -> `genai.rewrite`                  (trôi hơn, KHÔNG được thêm bộ phận)
        -> `verify_rewrite`                 (rơi về bản gốc nếu đánh rơi gì)
        -> Meshy

Bước xác thực ở giữa là bước đáng nói: hình 3D là một **kênh quan sát gián tiếp**
của người chơi, nên một model tả thêm cái vây không có thật là một kênh nói dối
mà không ai kiểm được.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_dotenv(path: Path = Path(".env")) -> int:
    """Nạp `.env` vào môi trường. Trả số biến đã nạp. Không ghi đè biến có sẵn."""
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=21)
    ap.add_argument("--map", default=None)
    ap.add_argument("--rewrite", action="store_true",
                    help="gọi Gemini viết lại (cần GEMINI_API_KEYS)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    load_dotenv()

    from genesis import config
    from genesis.domain import _BASE, domain_of
    from genesis.features import kit_of, roll_for_species
    from genesis.genai import keys, rewrite
    from genesis.mesh_prompts import creature_prompt
    from genesis.traits import founder_traits

    if a.rewrite and not keys():
        print("thiếu GEMINI_API_KEYS (đặt trong .env) — chạy không có --rewrite "
              "vẫn ra mô tả gốc.", file=sys.stderr)

    rows = []
    for sp in sorted(config.POPULATION):
        tr = founder_traits(sp)
        feats = roll_for_species(sp, a.seed)
        kit = kit_of(feats)
        dom = domain_of(sp)
        goc = creature_prompt(tr, dom.value, feats)
        text, src = (rewrite(goc) if a.rewrite else (goc, "goc"))
        rows.append({
            "species_id": sp, "seed": a.seed, "domain": dom.value,
            "features": [f.key for f in feats],
            "features_vn": [f.vn for f in feats],
            "prompt_goc": goc, "prompt": text, "nguon": src,
        })
        # In CẢ HAI mặt của đặc điểm, không chỉ mặt ngoại hình. Đó là cả điểm
        # của W-19: `look` và `effect` phải khớp nhau, và cách duy nhất người
        # đọc kiểm được điều đó là nhìn thấy chúng cạnh nhau.
        co_che = []
        vao_them = {t.value for t in kit.extra_terrain}
        for d in kit.extra_domains:
            vao_them |= {t.value for t in _BASE[d]}
        vao_them -= {t.value for t in _BASE[dom]}
        if vao_them:
            co_che.append("vào thêm " + "/".join(sorted(vao_them)))
        if kit.climb_bonus:
            co_che.append(f"trèo +{kit.climb_bonus}")
        for ten, giatri in (("hao sức", kit.upkeep_mult), ("đòn", kit.damage_mult),
                            ("chịu đòn", kit.dmg_taken_mult)):
            if abs(giatri - 1.0) > 1e-9:
                co_che.append(f"{ten} ×{giatri:.2f}")
        if kit.thorns:
            co_che.append(f"gai {kit.thorns:g}")

        print(f"── {sp} · {dom.value} · {' · '.join(f.vn for f in feats)}  [{src}]")
        print(f"   cơ chế: {' · '.join(co_che) or 'không đổi gì'}")
        print(f"   hình:   {text}\n")

    if a.out is not None:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"→ {a.out}  ({len(rows)} sinh vật)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

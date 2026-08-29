#!/usr/bin/env python3
"""X-03 · Ba nhánh prior: đo **rò rỉ tri thức có sẵn** (03 §10.2).

    python scripts/x03_prior.py --seeds 12 --ticks 400 [--llm-url http://127.0.0.1:8080]

    prior_leak = t_discover(INVERTED) − t_discover(ALIGNED)

`prior_leak` lớn nghĩa là điểm ở nhánh `ALIGNED` phần lớn là **nhớ bài**, không
phải suy luận — và khi đó `PRIOR_NEUTRAL` mới là nhánh chuẩn để báo cáo Q1.

Tài liệu gọi đây là *"phép đo mà tôi chưa thấy ai làm gọn ghẽ cho agent LLM"* và
*"thứ đáng viết bài nhất trong toàn bộ dự án"*. Nó chỉ có nghĩa khi có **model
thật**: không có model thì cả ba nhánh chạy cùng một tầng phản xạ, và phản xạ
không đọc màu quả, nên `prior_leak` bằng 0 **theo định nghĩa**. Chạy script này
không có `--llm-url` chỉ kiểm được rằng ba nhánh thật sự khác nhau ở bề mặt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

from genesis.lawdsl import to_vietnamese
from genesis.lawgen import generate_cached
from genesis.prior import ARMS, fruit_valence
from genesis.tick import build_match

PRIOR_ARMS = ("PRIOR_ALIGNED", "PRIOR_INVERTED", "PRIOR_NEUTRAL")


def surfaces_per_arm(seed: int) -> dict[str, str]:
    """Câu luật ăn quả của một seed, viết ra ở cả ba nhánh."""
    laws = generate_cached(seed, arm="PRIOR")
    out = {}
    for arm in PRIOR_ARMS:
        world, _, _, _ = build_match(seed, prior_arm=arm, laws=laws)
        eat = [
            to_vietnamese(law, world.surface_map)
            for law in laws
            if law.trigger.kind.value == "EAT"
        ]
        out[arm] = eat[0] if eat else ""
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--llm-url", default=None,
                    help="không có thì chỉ kiểm ba nhánh KHÁC NHAU, không đo được prior_leak")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)

    rows = []
    for seed in range(1, a.seeds + 1):
        s = surfaces_per_arm(seed)
        rows.append({"seed": seed, **s})
        print(f"seed {seed:>3}")
        for arm in PRIOR_ARMS:
            print(f"   {arm:<16} {s[arm]}")

    distinct = sum(
        1 for r in rows if r["PRIOR_ALIGNED"] != r["PRIOR_INVERTED"]
    )
    print(f"\nsố seed mà ALIGNED khác INVERTED: {distinct}/{len(rows)}")
    if distinct < len(rows):
        print("✗ có seed mà hai nhánh trùng nhau — phép đo mất tương phản", file=sys.stderr)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    if not a.llm_url:
        print(
            "\nCHƯA ĐO ĐƯỢC prior_leak: không có model thì cả ba nhánh chạy cùng\n"
            "một tầng phản xạ, mà phản xạ không đọc màu quả — kết quả sẽ là 0\n"
            "theo định nghĩa, không phải theo phát hiện. Chạy lại với --llm-url.",
            file=sys.stderr,
        )
        return 0 if distinct == len(rows) else 1

    print("\n(đo prior_leak với model thật: xem scripts/x06_report.py)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

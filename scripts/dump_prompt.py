#!/usr/bin/env python3
"""In prompt của một cá thể tại một lượt, để mắt người soi (nghiệm thu B-02).

    python scripts/dump_prompt.py --seed 3 --creature L1:0 --tick 100

Khối SYSTEM in ra giữa `[SYSTEM]` và `[USER]` để so bằng `diff` — xem
docs/tasks/B-02-prompt.md §5.
"""

from __future__ import annotations

import argparse
import sys

import httpx

from genesis.lawgen import generate_cached
from genesis.prompt import system_block
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick
from genesis.world import visible

DEFAULT_PERSONA = "Đi thành bầy, chia phần cho con yếu."


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--creature", default="L1:0")
    ap.add_argument("--tick", type=int, default=100)
    ap.add_argument("--persona", default=DEFAULT_PERSONA)
    ap.add_argument("--arm", default="STANDARD")
    ap.add_argument("--no-laws", action="store_true")
    ap.add_argument("--llm-url", default=None,
                    help="không đưa = chạy không model; sổ tay vẫn đầy vì nó nạp từ sự kiện thật")
    ap.add_argument("--tokens", action="store_true", help="chỉ in số ký tự và token ước lượng")
    a = ap.parse_args(argv)

    world, creatures, state, rng = build_match(seed=a.seed)
    if a.creature not in {x.id for x in creatures}:
        print(f"không có sinh vật {a.creature!r}", file=sys.stderr)
        return 2

    # Chạy ván THẬT với luật ẩn và với một tâm trí thật, nếu không sổ tay rỗng và
    # bài kiểm quan trọng nhất của B-07 ("đọc bằng mắt, bạn có suy ra được luật
    # không?") không kiểm được gì cả.
    laws = None if a.no_laws else generate_cached(a.seed, arm=a.arm)
    offline = httpx.MockTransport(lambda req: httpx.Response(503, text="không có model"))
    strat = LlmStrategist(
        a.llm_url or "http://offline",
        [a.creature],
        personas={a.creature.rpartition(":")[0]: a.persona},
        transport=None if a.llm_url else offline,
    )
    for t in range(a.tick):
        tick(world, creatures, t, rng, state, laws=laws, strategist=strat)

    c = next(x for x in creatures if x.id == a.creature)
    s, u = strat.build_prompt(c, world, visible(c, world, creatures), a.tick)

    if a.tokens:
        # ~3 ký tự/token cho tiếng Việt có dấu ở tokenizer BPE thường dùng.
        print(f"system {len(s)} ký tự (~{len(s)//3} token)")
        print(f"user   {len(u)} ký tự (~{len(u)//3} token)")
        print(f"tổng   {len(s)+len(u)} ký tự (~{(len(s)+len(u))//3} token)")
        return 0

    print("[SYSTEM]")
    print(s)
    print("[USER]")
    print(u)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

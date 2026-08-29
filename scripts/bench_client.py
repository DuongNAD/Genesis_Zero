#!/usr/bin/env python3
"""Đo lớp gọi model trên một llama-server thật (nghiệm thu B-03/S-02).

    python scripts/bench_client.py --url http://localhost:8080 --n 50

In ba con số quyết định:
  * tỉ lệ JSON hợp lệ — grammar có ăn không;
  * t_prefill lần 1 so lần 2 — prefix cache có trúng không (phải < 1/3);
  * 5 lời gọi song song so 1 lời gọi — `gather` có thật không (phải < 1.5x).
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import time

import httpx

from genesis.llm_client import ask
from genesis.prompt import system_block, user_block
from genesis.strategist import schema_for
from genesis.tick import build_match
from genesis.world import visible


async def run(url: str, n: int, a_slots: int = 4) -> int:
    world, creatures, _, _ = build_match(seed=3)
    c = creatures[0]
    system = system_block(c, "Đi thành bầy.", world.surface_map)
    schema = schema_for(c.traits, "decide")
    seen = visible(c, world, creatures)

    ok = 0
    times: list[float] = []
    prompt_ms: list[float] = []
    cached: list[int] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(n):
            user = user_block(c, world, i, None, None, seen=seen, notepad=f"lượt {i}")
            t0 = time.perf_counter()
            r = await ask(url, 0, system, user, c.traits.token_budget, schema, client=client)
            times.append(time.perf_counter() - t0)
            ok += r is not None
            if r is not None:
                tm = r.get("timings") or {}
                prompt_ms.append(float(tm.get("prompt_ms", 0.0)))
                cached.append(int(tm.get("cache_n", 0)))

        print(f"valid_json {ok}/{n}")
        print(f"tổng mỗi lời gọi, trung vị {statistics.median(times):.2f}s")

        # ── prefix cache: đo LẠNH rồi ĐO NÓNG, trên một slot chưa ai dùng ──
        # Đo "lần 1 vs lần 2" của vòng lặp trên là sai: tới lúc ấy slot đã ấm từ
        # một lần chạy trước và `cache_n` đã cao ngay ở lần đầu, nên tỉ lệ nói
        # về nhiễu chứ không nói về cache. Con số cần nhìn là **tỉ lệ token được
        # dùng lại**, không phải tỉ lệ thời gian.
        cold_slot = 3
        marker = f"[{time.time_ns()}]"      # ép prefix chưa từng thấy
        # Ngân sách rộng: ta đo prefill, và một câu trả lời bị cắt làm `ask`
        # trả None — lúc ấy không có `timings` nào để đọc.
        budget = c.traits.token_budget
        cold = await ask(url, cold_slot, system + marker, user, budget, schema, client=client)
        warm = await ask(url, cold_slot, system + marker, user, budget, schema, client=client)
        if cold and warm:
            tc, tw = cold["timings"], warm["timings"]
            pn = float(tw.get("prompt_n", 0)) + float(tw.get("cache_n", 0))
            print(f"prefix cache · lạnh: dùng lại {tc.get('cache_n', 0):.0f} token, "
                  f"prefill {tc.get('prompt_ms', 0):.0f}ms")
            print(f"prefix cache · nóng: dùng lại {tw.get('cache_n', 0):.0f}/{pn:.0f} token "
                  f"({100 * float(tw.get('cache_n', 0)) / max(pn, 1):.0f}%), "
                  f"prefill {tw.get('prompt_ms', 0):.0f}ms")

        user = user_block(c, world, 0, None, None, seen=seen)
        t0 = time.perf_counter()
        await ask(url, 0, system, user, c.traits.token_budget, schema, client=client)
        one = time.perf_counter() - t0
        for k in (4, 5):
            t0 = time.perf_counter()
            await asyncio.gather(*[
                ask(url, s, system, user_block(c, world, s, None, None, seen=seen),
                    c.traits.token_budget, schema, client=client)
                for s in range(k)
            ])
            many = time.perf_counter() - t0
            note = "" if k <= a_slots else f"  (> {a_slots} slot: có lời gọi phải XẾP HÀNG)"
            print(f"1 lời gọi {one:.2f}s · {k} song song {many:.2f}s "
                  f"· tỉ lệ {many/one:.2f} (cần < 1.5){note}")
    return 0 if ok == n else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--slots", type=int, default=4,
                    help="số slot llama-server đang chạy (-np); nhiều hơn thì xếp hàng")
    a = ap.parse_args(argv)
    return asyncio.run(run(a.url, a.n, a.slots))


if __name__ == "__main__":
    raise SystemExit(main())

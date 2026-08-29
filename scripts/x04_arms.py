#!/usr/bin/env python3
"""X-04 · Chạy và so sánh các nhánh đối chứng (03 §10).

    python scripts/x04_arms.py --seeds 10 --ticks 400

Bốn nhánh, khác nhau đúng một biến:
  LLM     — có tầng chiến lược LLM (dùng model giả của scripts/fake_model_server.py
            qua httpx.MockTransport, KHÔNG mở cổng)
  REFLEX  — chỉ tầng phản xạ (strategist=None)
  RANDOM  — goal chọn ngẫu nhiên mỗi khi hết ttl (tất định theo creature_rng)
  SILENT  — như LLM nhưng không bao giờ `say` (tắt kênh nói)

In bảng: nhánh × (alive_ratio trung bình, số chết, match cao nhất nếu có).
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys
from typing import Any

import httpx

from genesis import config, law_config
from genesis.batch import Run, run_many
from genesis.creature import Creature
from genesis.lawgen import generate_cached
from genesis.reflex import ActiveGoal, Goal
from genesis.situations import sample_situations
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, creature_rng, tick
from genesis.verify import match
from genesis.world import World


class RandomStrategist:
    """Tầng chiến lược RANDOM: goal chọn ngẫu nhiên mỗi khi hết ttl.

    Tất định theo seed nhờ genesis.tick.creature_rng, KHÔNG dùng random module-level.
    """

    def __init__(self, match_seed: int) -> None:
        self.match_seed = match_seed

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        if current is not None and current.ttl > 0:
            return None
        crng = creature_rng(self.match_seed, tick_no, c.id)
        valid_goals = config.GOALS_BY_BRAIN[c.traits.brain]
        goal = Goal(crng.choice(valid_goals))
        ttl = crng.randint(2, 12)
        target = None
        if goal in (Goal.HUNT, Goal.FLEE, Goal.FOLLOW) and seen:
            target = crng.choice(seen).id
        return ActiveGoal(goal=goal, target=target, ttl=ttl)


def make_mock_transport(seed: int, silent: bool = False) -> httpx.MockTransport:
    """Tạo MockTransport giả lập llama-server cục bộ qua httpx mà không mở cổng mạng."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8") or "{}")
        prompt = body.get("prompt", "")
        if "[CÂU HỎI]" in prompt:
            out: dict[str, Any] = {"answers": []}
        elif "[GHI SỔ LUẬT]" in prompt:
            out = {
                "op": "SET",
                "slot": 0,
                "conf": 2,
                "law": {
                    "trigger": {"kind": "DRINK"},
                    "conds": [],
                    "effect": {"kind": "HEAL", "mag": "SMALL", "dur": "INSTANT"},
                },
            }
        elif "[DỊCH CƠ THỂ]" in prompt:
            out = {"from": "brain", "to": "speed", "why": "thich nghi"}
        else:
            h = int(hashlib.md5(f"{seed}:{prompt}".encode()).hexdigest()[:8], 16)
            prng = random.Random(h)
            out = {
                "goal": prng.choice(["FORAGE", "REST", "WANDER", "FLEE"]),
                "ttl": prng.randint(3, 8),
                "want_codex": prng.random() < 0.25,
            }
            if not silent and prng.random() < 0.3:
                out["say"] = {
                    "signal": prng.choice(["ALARM", "AGGR", "SUBM", "NEUTRAL"]),
                    "text": "chao",
                }
        payload = json.dumps(out, ensure_ascii=False)
        return httpx.Response(
            200,
            json={
                "content": payload,
                "tokens_predicted": max(1, len(payload) // 4),
            },
        )

    return httpx.MockTransport(handler)


def run_arm_one(arm: str, seed: int, ticks: int) -> dict[str, Any]:
    """Chạy một ván đơn lẻ cho một nhánh đối chứng cụ thể."""
    world, creatures, state, rng = build_match(seed)
    laws = generate_cached(seed, arm="STANDARD")

    strategist: Any = None
    if arm == "REFLEX":
        strategist = None
    elif arm == "RANDOM":
        strategist = RandomStrategist(seed)
    elif arm == "LLM":
        transport = make_mock_transport(seed, silent=False)
        strategist = LlmStrategist(
            "http://fake-model",
            [c.id for c in creatures],
            transport=transport,
        )
    elif arm == "SILENT":
        transport = make_mock_transport(seed, silent=True)
        strategist = LlmStrategist(
            "http://fake-model",
            [c.id for c in creatures],
            transport=transport,
        )
    else:
        raise ValueError(f"Nhánh không hợp lệ: {arm!r}")

    alive_ticks = {c.id: 0 for c in creatures}
    deaths = {c.id: 0 for c in creatures}
    prev_alive = {c.id: c.alive for c in creatures}

    for t in range(ticks):
        tick(world, creatures, t, rng, state, laws=laws, strategist=strategist)
        for c in creatures:
            if c.alive:
                alive_ticks[c.id] += 1
            elif prev_alive[c.id]:
                deaths[c.id] += 1
            prev_alive[c.id] = c.alive

    max_match = 0.0
    if strategist is not None and hasattr(strategist, "codices") and laws:
        sits = [
            sample_situations(l, law_config.N_SITUATIONS, random.Random(seed * 1000 + i))
            for i, l in enumerate(laws)
        ]
        for c in creatures:
            cx = strategist.codex_of(c)
            for entry in cx.entries():
                if entry is not None:
                    for i, l in enumerate(laws):
                        m = match(entry.law, l, sits[i])
                        if m > max_match:
                            max_match = m

    avg_alive_ratio = sum(alive_ticks[c.id] / ticks for c in creatures) / len(creatures)
    total_deaths = sum(deaths.values())

    return {
        "arm": arm,
        "seed": seed,
        "ticks": ticks,
        "alive_ratio": round(avg_alive_ratio, 4),
        "deaths": total_deaths,
        "max_match": round(max_match, 4),
    }


def _run_task(args: tuple[str, int, int]) -> dict[str, Any]:
    return run_arm_one(*args)


def run_arms(seeds: int, ticks: int, workers: int = 0) -> dict[str, Any]:
    """Chạy và so sánh 4 nhánh đối chứng trên N seeds."""
    # Hâm nóng cache luật bằng genesis.batch.run_many trước khi chạy song song
    warm_jobs = [
        Run(seed=s, arm="STANDARD", ticks=ticks, laws_on=True)
        for s in range(1, seeds + 1)
    ]
    run_many(warm_jobs, workers=workers)

    arms = ["LLM", "SILENT", "REFLEX", "RANDOM"]
    tasks = [(arm, s, ticks) for arm in arms for s in range(1, seeds + 1)]

    if workers in (0, 1):
        results = [_run_task(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(_run_task, tasks))

    summary: dict[str, dict[str, Any]] = {}
    for arm in arms:
        arm_res = [r for r in results if r["arm"] == arm]
        ratios = [r["alive_ratio"] for r in arm_res]
        deaths = [r["deaths"] for r in arm_res]
        matches = [r["max_match"] for r in arm_res]

        summary[arm] = {
            "mean_alive_ratio": round(statistics.fmean(ratios), 4) if ratios else 0.0,
            "total_deaths": sum(deaths),
            "mean_deaths": round(statistics.fmean(deaths), 2) if deaths else 0.0,
            "max_match": round(max(matches, default=0.0), 4),
            "n_runs": len(arm_res),
        }

    return {
        "seeds": seeds,
        "ticks": ticks,
        "summary": summary,
        "runs": results,
    }


def print_table(data: dict[str, Any]) -> None:
    """In bảng so sánh 4 nhánh ra stdout."""
    seeds = data["seeds"]
    ticks = data["ticks"]
    summary = data["summary"]

    print("=" * 72)
    print(f"KẾT QUẢ SO SÁNH 4 NHÁNH ĐỐI CHỨNG (X-04)")
    print(f"Số seeds: {seeds} | Ticks mỗi ván: {ticks}")
    print("=" * 72)
    print(f"{'Nhánh':<12} | {'alive_ratio TB':>15} | {'Tổng số chết':>14} | {'Match cao nhất':>15}")
    print("-" * 12 + "-+-" + "-" * 15 + "-+-" + "-" * 14 + "-+-" + "-" * 15)

    for arm in ["LLM", "SILENT", "REFLEX", "RANDOM"]:
        s = summary.get(arm, {})
        ratio = f"{s.get('mean_alive_ratio', 0.0):.4f}"
        deaths = str(s.get("total_deaths", 0))
        max_m = f"{s.get('max_match', 0.0):.4f}"
        print(f"{arm:<12} | {ratio:>15} | {deaths:>14} | {max_m:>15}")

    print("=" * 72)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scripts.x04_arms", description="Chạy và so sánh 4 nhánh đối chứng")
    ap.add_argument("--seeds", type=int, default=10, help="Số lượng seeds (mặc định: 10)")
    ap.add_argument("--ticks", type=int, default=400, help="Số tick mỗi ván (mặc định: 400)")
    ap.add_argument("--workers", type=int, default=4, help="Số workers chạy song song (mặc định: 4)")
    ap.add_argument("--out", type=Path, default=None, help="Đường dẫn file JSON xuất kết quả nếu cần")
    a = ap.parse_args(argv)

    data = run_arms(a.seeds, a.ticks, workers=a.workers)
    print_table(data)

    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

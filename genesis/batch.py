"""Genesis Zero — batch: chạy nhiều ván song song rồi gom lại (X-01).

Sim mất ~0,2 s cho 400 tick, nên phần đắt không phải mô phỏng mà là **sinh luật**
(cổng khả giải chạy một ván thật cho mỗi bộ). `generate_cached` đã đệm việc đó,
và ở đây ta hâm nóng đệm **trước** khi rẽ nhánh tiến trình: nếu không, mười tiến
trình con cùng sinh một bộ luật cho cùng một seed và ghi đè nhau.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Any

from genesis.creature import creature_sort_key
from genesis.lawgen import generate_cached
from genesis.tick import build_match, tick
from genesis.traits import founder_traits


@dataclass(frozen=True)
class Run:
    seed: int
    arm: str
    ticks: int
    laws_on: bool
    map_name: str | None = None


def run_one(job: Run) -> list[dict[str, Any]]:
    """Một ván không LLM, trả một dòng mỗi cá thể. Thuần hàm theo `job`."""
    world, creatures, state, rng = build_match(job.seed, map_name=job.map_name)
    laws = generate_cached(job.seed, arm=job.arm) if job.laws_on else None

    alive_ticks = {c.id: 0 for c in creatures}
    deaths = {c.id: 0 for c in creatures}
    prev_alive = {c.id: c.alive for c in creatures}
    for t in range(job.ticks):
        tick(world, creatures, t, rng, state, laws=laws)
        for c in creatures:
            if c.alive:
                alive_ticks[c.id] += 1
            elif prev_alive[c.id]:
                deaths[c.id] += 1
            prev_alive[c.id] = c.alive

    return [
        {
            "seed": job.seed,
            "arm": job.arm,
            "map": job.map_name or "DONG_CO",
            "world": "LAW" if job.laws_on else "FLAT",
            "creature_id": c.id,
            "species_id": c.species,
            "founder_brain": founder_traits(c.species).brain,
            "brain_end": c.traits.brain,
            "alive_ratio": round(alive_ticks[c.id] / job.ticks, 4),
            "deaths": deaths[c.id],
            "eat_count": c.eat_count,
            # `reset_body` xoá `shift_log` mỗi lần chết, nên đây là số lần dịch
            # KỂ TỪ LẦN CHẾT GẦN NHẤT, không phải cả ván. Đặt tên cho đúng.
            "shifts_since_death": len(c.shift_log),
        }
        for c in sorted(creatures, key=creature_sort_key)
    ]


def _warm(job: tuple[int, str]) -> None:
    generate_cached(job[0], arm=job[1])


def run_many(jobs: list[Run], workers: int = 0) -> list[dict[str, Any]]:
    # Hâm nóng đệm luật TRƯỚC khi rẽ nhánh: bỏ bước này thì N tiến trình con cùng
    # chạy cổng khả giải cho cùng một seed — mất N lần công, và chúng ghi đè file
    # đệm của nhau. Nhưng hâm tuần tự cũng sai: cổng mất 2–7 s một bộ, nên 40 seed
    # là hơn hai phút chỉ để đứng chờ trong khi 10 lõi ngồi không.
    todo = sorted({(x.seed, x.arm) for x in jobs if x.laws_on})
    if todo:
        if workers in (0, 1) or len(todo) == 1:
            for seed, arm in todo:
                generate_cached(seed, arm=arm)
        else:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                list(ex.map(_warm, todo))

    if workers in (0, 1):
        return [row for j in jobs for row in run_one(j)]
    out: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for rows in ex.map(run_one, jobs):
            out.extend(rows)
    return out

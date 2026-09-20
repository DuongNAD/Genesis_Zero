"""Genesis Zero v5 — lawhook: cắm luật ẩn vào vòng tick (L-02).

Ranh giới: file này DỊCH trạng thái thế giới thật thành `LawEvent`/`Ctx` rồi gọi
`laweval.evaluate`. Bản thân `laweval` vẫn là hàm thuần và không biết gì về world —
nhờ vậy bộ chấm ở `verify.py` dùng đúng một hàm đánh giá với vòng tick, và
"luật thật" trong ván khớp từng bit với "luật thật" lúc chấm.
"""

from __future__ import annotations

import random

from genesis import config
from genesis.creature import Creature
from genesis.lawdsl import EffectKind, Law, Mag
from genesis.laweval import Ctx, LawEvent, evaluate
from genesis.world import World, phase_at

# Độ lớn rổ -> con số thật. Agent không đo được con số nên chỉ cần nhất quán.
_MAG_VALUE: dict[Mag | None, float] = {Mag.SMALL: 3.0, Mag.MED: 10.0, Mag.BIG: 22.0, None: 10.0}
_DUR_TICKS: dict[str, int] = {"INSTANT": 0, "SHORT": 2, "LONG": 6}

_BAND = ("LOW", "MID", "HIGH")


def _band(value: float, hi: float) -> str:
    if hi <= 0:
        return "LOW"
    r = value / hi
    return _BAND[0] if r < 1 / 3 else (_BAND[1] if r < 2 / 3 else _BAND[2])


def build_ctx(c: Creature, world: World, tick_no: int, creatures: list[Creature],
              recent: dict[str, int]) -> Ctx:
    """Dựng ngữ cảnh ĐẦY ĐỦ cho một cá thể.

    Bất biến: điền MỌI trường, không chỉ trường mà luật đang xét cần — cùng lý do
    với L-04 B1. Thiếu trường thì luật khác đánh giá thành None và ăn điểm oan.
    """
    x, y = world.wrap(*c.pos)
    counts: dict[str, dict[int, int]] = {
        "SAME_SP": {1: 0, 2: 0, 3: 0},
        "OTHER_SP": {1: 0, 2: 0, 3: 0},
        "ANY": {1: 0, 2: 0, 3: 0},
    }
    for o in creatures:
        if o is c or not o.alive:
            continue
        d = world.dist(c.pos, o.pos)
        if d > 3:
            continue
        key = "SAME_SP" if o.species == c.species else "OTHER_SP"
        for r in range(max(1, d), 4):
            counts[key][r] += 1
            counts["ANY"][r] += 1
    return Ctx(
        phase=phase_at(tick_no),
        terrain=str(world.grid[y][x]),
        hp_band=_band(c.hp, float(config.HP_MAX)),
        energy_band=_band(c.energy, c.traits.energy_max),
        age_band="YOUNG" if c.age < 100 else "OLD",
        # Gió là một nhãn quan sát được; chưa có hướng đi nên quy ước theo chẵn/lẻ tick.
        wind_rel="WITH" if (tick_no % 2 == 0) else "AGAINST",
        alone=counts["ANY"][2] == 0,
        recent=dict(recent),
        counts=counts,
        subject={
            "ARMOR>=3": c.traits.armor >= 3,
            "SPEED>=3": c.traits.speed >= 3,
            "BRAIN<=1": c.traits.brain <= 1,
            "SAME_SP": True,
        },
    )


def apply_creature_effect(c: Creature, e, rng: random.Random, world: World) -> str | None:
    """Áp dụng hệ quả lên MỘT cá thể. Trả tên hệ quả đã áp dụng, hoặc None."""
    mag = _MAG_VALUE[e.mag]
    dur = _DUR_TICKS.get(e.dur.value if e.dur else "INSTANT", 0)
    if e.kind == EffectKind.DAMAGE:
        c.hp -= mag
    elif e.kind == EffectKind.HEAL:
        c.hp = min(float(config.HP_MAX), c.hp + mag)
    elif e.kind == EffectKind.ENERGY_GAIN:
        c.energy = min(c.traits.energy_max, c.energy + mag)
    elif e.kind == EffectKind.ENERGY_DRAIN:
        c.energy -= mag
    elif e.kind == EffectKind.POISON:
        c.poison_ticks = max(c.poison_ticks, max(dur, 1))
        c.poison_from = c.poison_from or "LAW"
    elif e.kind == EffectKind.STUN:
        c.stun_ticks = max(c.stun_ticks, max(dur, 1))
    elif e.kind == EffectKind.TELEPORT:
        r = e.r or 1
        cand = [p for p in
                ((c.pos[0] + dx, c.pos[1] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1))
                if world.passable(p, c)]
        if cand:
            c.pos = world.wrap(*rng.choice(sorted(cand)))
    else:
        return None
    return e.kind.value


def collect_law_effects(laws: list[Law], events: list[tuple[Creature, LawEvent]]):
    """Pha 4: THU hết (cá thể, hệ quả) rồi mới áp dụng — không sửa gì ở đây.

    Giữ đúng tính đồng thời của W-11: hai con cùng châm ngòi một luật trong một tick
    thì cả hai nhận hệ quả, tính từ trạng thái TRƯỚC tick.
    """
    out: list[tuple[Creature, object, int]] = []
    for c, ev in events:
        for i, law in enumerate(laws):
            eff = evaluate(law, ev)
            if eff is not None:
                out.append((c, eff, i))
    return out

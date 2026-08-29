"""Genesis Zero v5 — LawEval: Đánh giá luật trên một tình huống (hàm thuần)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from genesis.lawdsl import CondKind, Effect, Law, TriggerKind

if TYPE_CHECKING:
    from genesis.lawdsl import Cond


@dataclass(frozen=True)
class Ctx:
    """Ngữ cảnh ĐẦY ĐỦ để đánh giá BẤT KỲ cond nào — không chỉ cond của luật đang xét."""

    phase: str  # "DAY"|"NIGHT"
    terrain: str  # PLAIN|WATER|BUSH|ROCK|FIRE
    hp_band: str  # LOW|MID|HIGH
    energy_band: str  # LOW|MID|HIGH
    age_band: str  # YOUNG|OLD
    wind_rel: str  # WITH|AGAINST
    alone: bool
    recent: dict[str, int]  # tên trigger -> số tick TRƯỚC ĐÂY đã làm (0 = tick này)
    counts: dict[str, dict[int, int]]  # "SAME_SP"/"OTHER_SP"/"ANY" -> {bán kính: số con}
    subject: dict[str, bool]  # "ARMOR>=3"/"SPEED>=3"/"BRAIN<=1"/"SAME_SP" -> bool

    def __hash__(self) -> int:
        return hash((
            self.phase,
            self.terrain,
            self.hp_band,
            self.energy_band,
            self.age_band,
            self.wind_rel,
            self.alone,
            tuple(sorted(self.recent.items())),
            tuple((k, tuple(sorted(v.items()))) for k, v in sorted(self.counts.items())),
            tuple(sorted(self.subject.items())),
        ))


@dataclass(frozen=True)
class LawEvent:
    kind: TriggerKind
    arg: str | None = None
    n: int | None = None
    k: int | None = None
    r: int | None = None
    ctx: Ctx | None = None
    meta: tuple[tuple[str, object], ...] = ()


def trigger_matches(law: Law, ev: LawEvent) -> bool:
    """Kiểm tra sự kiện ev có khớp trigger của luật không (hàm thuần)."""
    t = law.trigger
    if t.kind != ev.kind:
        return False
    if t.arg is not None:
        if t.kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY, TriggerKind.ADJACENT):
            if t.arg == "ANY":
                if ev.arg not in ("SAME_SP", "OTHER_SP", "ANY"):
                    return False
            elif ev.arg != t.arg:
                return False
        elif ev.arg != t.arg:
            return False
    if t.n is not None:
        if ev.n is None or ev.n < t.n:
            return False
    if t.k is not None:
        if ev.k is None or ev.k < t.k:
            return False
    if t.r is not None:
        if ev.r is None or ev.r > t.r:
            return False
    return True


def cond_holds(c: Cond, ctx: Ctx) -> bool:
    """Kiểm tra điều kiện c có thoả mãn trong ngữ cảnh ctx không (hàm thuần)."""
    if c.kind == CondKind.PHASE:
        return ctx.phase == c.arg
    if c.kind == CondKind.TERRAIN:
        return ctx.terrain == c.arg
    if c.kind == CondKind.HP:
        return ctx.hp_band == c.arg
    if c.kind == CondKind.ENERGY:
        return ctx.energy_band == c.arg
    if c.kind == CondKind.RECENT:
        if c.arg is None or c.k is None:
            return False
        return ctx.recent.get(c.arg, 10**9) <= c.k
    if c.kind == CondKind.COUNT:
        if c.arg is None or c.r is None or c.n is None or c.op is None:
            return False
        val = ctx.counts.get(c.arg, {}).get(c.r, 0)
        if c.op == ">=":
            return val >= c.n
        if c.op == "<=":
            return val <= c.n
        return False
    if c.kind == CondKind.AGE:
        return ctx.age_band == c.arg
    if c.kind == CondKind.WIND:
        return ctx.wind_rel == c.arg
    if c.kind == CondKind.SUBJECT:
        if c.arg is None:
            return False
        return bool(ctx.subject.get(c.arg, False))
    if c.kind == CondKind.ALONE:
        return ctx.alone
    return False


def evaluate(law: Law, ev: LawEvent) -> Effect | None:
    """Đánh giá luật trên sự kiện ev.

    Trả law.effect khi trigger khớp VÀ mọi cond đúng; ngược lại None.
    """
    if not trigger_matches(law, ev):
        return None
    if ev.ctx is None:
        return None
    for c in law.conds:
        if not cond_holds(c, ev.ctx):
            return None
    return law.effect

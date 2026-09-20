"""Genesis Zero v5 — Không gian tình huống và lấy mẫu phân tầng."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from genesis import law_config as lc
from genesis.lawdsl import CondKind, Law, TriggerKind
from genesis.laweval import Ctx, LawEvent, evaluate, trigger_matches

if TYPE_CHECKING:
    from genesis.lawdsl import Cond

Situation = LawEvent

_RECENT_ACTIONS = ("DRINK", "EAT", "ATTACK", "HIT_BY", "STEP_ON", "SPEAK", "REST")
_SUBJECT_KEYS = ("ARMOR>=3", "SPEED>=3", "BRAIN<=1", "SAME_SP")
_TERRAINS = ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE")
_LEVELS = ("LOW", "MID", "HIGH")
_PHASES = ("DAY", "NIGHT")
_AGES = ("YOUNG", "OLD")
_WINDS = ("WITH", "AGAINST")
_FRUITS_CORPSE = ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "CORPSE")
_SIGNALS = ("ALARM", "AGGR", "SUBM", "NEUTRAL")


def strata_of(law: Law, s: Situation) -> str:
    """Xác định tầng của tình huống s đối với luật: 'fires' | 'near_miss' | 'unrelated'."""
    if evaluate(law, s) is not None:
        return "fires"
    if trigger_matches(law, s):
        return "near_miss"
    return "unrelated"


def _random_ctx_dict(rng: random.Random) -> dict:
    counts: dict[str, dict[int, int]] = {
        "SAME_SP": {1: rng.randint(0, 3), 2: rng.randint(0, 4), 3: rng.randint(0, 5)},
        "OTHER_SP": {1: rng.randint(0, 3), 2: rng.randint(0, 4), 3: rng.randint(0, 5)},
        "ANY": {1: 0, 2: 0, 3: 0},
    }
    for r in (1, 2, 3):
        counts["ANY"][r] = counts["SAME_SP"][r] + counts["OTHER_SP"][r]

    return {
        "phase": rng.choice(_PHASES),
        "terrain": rng.choice(_TERRAINS),
        "hp_band": rng.choice(_LEVELS),
        "energy_band": rng.choice(_LEVELS),
        "age_band": rng.choice(_AGES),
        "wind_rel": rng.choice(_WINDS),
        "alone": rng.choice([True, False]),
        "recent": {act: rng.randint(0, 30) for act in _RECENT_ACTIONS},
        "counts": counts,
        "subject": {k: rng.choice([True, False]) for k in _SUBJECT_KEYS},
    }


def _apply_cond_hold(ctx_dict: dict, c: Cond, rng: random.Random) -> None:
    if c.kind == CondKind.PHASE:
        ctx_dict["phase"] = c.arg or "DAY"
    elif c.kind == CondKind.TERRAIN:
        ctx_dict["terrain"] = c.arg or "PLAIN"
    elif c.kind == CondKind.HP:
        ctx_dict["hp_band"] = c.arg or "MID"
    elif c.kind == CondKind.ENERGY:
        ctx_dict["energy_band"] = c.arg or "MID"
    elif c.kind == CondKind.AGE:
        ctx_dict["age_band"] = c.arg or "YOUNG"
    elif c.kind == CondKind.WIND:
        ctx_dict["wind_rel"] = c.arg or "WITH"
    elif c.kind == CondKind.ALONE:
        ctx_dict["alone"] = True
    elif c.kind == CondKind.SUBJECT:
        if c.arg:
            ctx_dict["subject"][c.arg] = True
    elif c.kind == CondKind.RECENT:
        if c.arg and c.k is not None:
            ctx_dict["recent"][c.arg] = rng.randint(0, c.k)
    elif c.kind == CondKind.COUNT:
        if c.arg and c.r is not None and c.n is not None and c.op:
            r = c.r
            n = c.n
            if c.arg in ("SAME_SP", "OTHER_SP"):
                if c.op == ">=":
                    ctx_dict["counts"][c.arg][r] = rng.randint(n, n + 3)
                else:  # "<="
                    ctx_dict["counts"][c.arg][r] = rng.randint(0, n)
                ctx_dict["counts"]["ANY"][r] = (
                    ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                )
            elif c.arg == "ANY":
                if c.op == ">=":
                    ctx_dict["counts"]["SAME_SP"][r] = n
                    ctx_dict["counts"]["ANY"][r] = (
                        ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                    )
                else:  # "<="
                    ctx_dict["counts"]["SAME_SP"][r] = 0
                    ctx_dict["counts"]["OTHER_SP"][r] = rng.randint(0, n)
                    ctx_dict["counts"]["ANY"][r] = (
                        ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                    )


def _apply_cond_break(ctx_dict: dict, c: Cond, rng: random.Random) -> None:
    if c.kind == CondKind.PHASE:
        ctx_dict["phase"] = "NIGHT" if c.arg == "DAY" else "DAY"
    elif c.kind == CondKind.TERRAIN:
        opts = [t for t in _TERRAINS if t != c.arg]
        ctx_dict["terrain"] = rng.choice(opts)
    elif c.kind == CondKind.HP:
        opts = [b for b in _LEVELS if b != c.arg]
        ctx_dict["hp_band"] = rng.choice(opts)
    elif c.kind == CondKind.ENERGY:
        opts = [b for b in _LEVELS if b != c.arg]
        ctx_dict["energy_band"] = rng.choice(opts)
    elif c.kind == CondKind.AGE:
        ctx_dict["age_band"] = "OLD" if c.arg == "YOUNG" else "YOUNG"
    elif c.kind == CondKind.WIND:
        ctx_dict["wind_rel"] = "AGAINST" if c.arg == "WITH" else "WITH"
    elif c.kind == CondKind.ALONE:
        ctx_dict["alone"] = False
    elif c.kind == CondKind.SUBJECT:
        if c.arg:
            ctx_dict["subject"][c.arg] = False
    elif c.kind == CondKind.RECENT:
        if c.arg and c.k is not None:
            ctx_dict["recent"][c.arg] = rng.randint(c.k + 1, c.k + 20)
    elif c.kind == CondKind.COUNT:
        if c.arg and c.r is not None and c.n is not None and c.op:
            r = c.r
            n = c.n
            if c.arg in ("SAME_SP", "OTHER_SP"):
                if c.op == ">=":
                    ctx_dict["counts"][c.arg][r] = rng.randint(0, max(0, n - 1))
                else:  # "<="
                    ctx_dict["counts"][c.arg][r] = rng.randint(n + 1, n + 4)
                ctx_dict["counts"]["ANY"][r] = (
                    ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                )
            elif c.arg == "ANY":
                if c.op == ">=":
                    ctx_dict["counts"]["SAME_SP"][r] = 0
                    ctx_dict["counts"]["OTHER_SP"][r] = rng.randint(0, max(0, n - 1))
                    ctx_dict["counts"]["ANY"][r] = (
                        ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                    )
                else:  # "<="
                    ctx_dict["counts"]["SAME_SP"][r] = n + 1
                    ctx_dict["counts"]["OTHER_SP"][r] = 0
                    ctx_dict["counts"]["ANY"][r] = (
                        ctx_dict["counts"]["SAME_SP"][r] + ctx_dict["counts"]["OTHER_SP"][r]
                    )


def _dict_to_ctx(d: dict) -> Ctx:
    return Ctx(
        phase=d["phase"],
        terrain=d["terrain"],
        hp_band=d["hp_band"],
        energy_band=d["energy_band"],
        age_band=d["age_band"],
        wind_rel=d["wind_rel"],
        alone=d["alone"],
        recent=dict(d["recent"]),
        counts={k: dict(v) for k, v in d["counts"].items()},
        subject=dict(d["subject"]),
    )


def _make_matching_event(
    law: Law,
    ctx: Ctx,
    rng: random.Random,
    meta: tuple[tuple[str, object], ...] = (),
) -> LawEvent:
    t = law.trigger
    arg = t.arg
    if t.kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY, TriggerKind.ADJACENT):
        if t.arg == "ANY":
            arg = rng.choice(["SAME_SP", "OTHER_SP", "ANY"])
    return LawEvent(
        kind=t.kind,
        arg=arg,
        n=t.n,
        k=t.k,
        r=t.r,
        ctx=ctx,
        meta=meta,
    )


def _make_unrelated_event(law: Law, ctx: Ctx, rng: random.Random) -> LawEvent:
    other_kinds = [k for k in TriggerKind if k != law.trigger.kind]
    kind = rng.choice(other_kinds)
    arg: str | None = None
    n: int | None = None
    k: int | None = None
    r: int | None = None

    if kind == TriggerKind.EAT:
        arg = rng.choice(_FRUITS_CORPSE)
    elif kind in (TriggerKind.ATTACK, TriggerKind.HIT_BY):
        arg = rng.choice(["SAME_SP", "OTHER_SP", "ANY"])
    elif kind == TriggerKind.STEP_ON:
        arg = rng.choice(_TERRAINS)
    elif kind == TriggerKind.ADJACENT:
        arg = rng.choice(["SAME_SP", "OTHER_SP", "ANY"])
        n = rng.choice([1, 2, 3])
    elif kind == TriggerKind.SPEAK:
        arg = rng.choice(_SIGNALS)
    elif kind == TriggerKind.REST:
        k = rng.choice([2, 3, 4, 5])
    elif kind == TriggerKind.DEATH_NEAR:
        r = rng.choice([1, 2, 3])
    elif kind == TriggerKind.PHASE_ENTER:
        arg = rng.choice(_PHASES)

    return LawEvent(
        kind=kind,
        arg=arg,
        n=n,
        k=k,
        r=r,
        ctx=ctx,
        meta=(),
    )


def sample_situations(law: Law, n: int, rng: random.Random) -> list[Situation]:
    """Lấy mẫu phân tầng không gian tình huống cho luật theo tỉ lệ quy định."""
    situations: list[Situation] = []

    if not law.conds:
        # B3: 0 conds -> 50% fires / 50% unrelated
        n_fires = n // 2
        n_unrelated = n - n_fires

        for _ in range(n_fires):
            ctx_dict = _random_ctx_dict(rng)
            ctx = _dict_to_ctx(ctx_dict)
            s = _make_matching_event(law, ctx, rng, meta=())
            situations.append(s)

        for _ in range(n_unrelated):
            ctx_dict = _random_ctx_dict(rng)
            ctx = _dict_to_ctx(ctx_dict)
            s = _make_unrelated_event(law, ctx, rng)
            situations.append(s)
    else:
        n_fires = round(n * lc.SITUATION_STRATA.get("fires", 0.4))
        n_near_miss = round(n * lc.SITUATION_STRATA.get("near_miss", 0.4))
        n_unrelated = n - n_fires - n_near_miss

        # 1. Tầng fires: trigger đúng, mọi cond đúng
        for _ in range(n_fires):
            ctx_dict = _random_ctx_dict(rng)
            for c in law.conds:
                _apply_cond_hold(ctx_dict, c, rng)
            ctx = _dict_to_ctx(ctx_dict)
            s = _make_matching_event(law, ctx, rng, meta=())
            situations.append(s)

        # 2. Tầng near_miss: trigger đúng, cond sai
        if len(law.conds) == 1:
            for _ in range(n_near_miss):
                ctx_dict = _random_ctx_dict(rng)
                _apply_cond_break(ctx_dict, law.conds[0], rng)
                ctx = _dict_to_ctx(ctx_dict)
                meta = (("broken_cond", (0,)),)
                s = _make_matching_event(law, ctx, rng, meta=meta)
                situations.append(s)
        else:
            base = n_near_miss // 3
            rem = n_near_miss % 3
            counts_by_case = [base + (1 if i < rem else 0) for i in range(3)]

            # Trường hợp 0: hỏng cond 0 riêng (cond 1 đúng)
            for _ in range(counts_by_case[0]):
                ctx_dict = _random_ctx_dict(rng)
                _apply_cond_hold(ctx_dict, law.conds[1], rng)
                _apply_cond_break(ctx_dict, law.conds[0], rng)
                ctx = _dict_to_ctx(ctx_dict)
                s = _make_matching_event(law, ctx, rng, meta=(("broken_cond", (0,)),))
                situations.append(s)

            # Trường hợp 1: hỏng cond 1 riêng (cond 0 đúng)
            for _ in range(counts_by_case[1]):
                ctx_dict = _random_ctx_dict(rng)
                _apply_cond_hold(ctx_dict, law.conds[0], rng)
                _apply_cond_break(ctx_dict, law.conds[1], rng)
                ctx = _dict_to_ctx(ctx_dict)
                s = _make_matching_event(law, ctx, rng, meta=(("broken_cond", (1,)),))
                situations.append(s)

            # Trường hợp 2: hỏng cả hai
            for _ in range(counts_by_case[2]):
                ctx_dict = _random_ctx_dict(rng)
                _apply_cond_break(ctx_dict, law.conds[0], rng)
                _apply_cond_break(ctx_dict, law.conds[1], rng)
                ctx = _dict_to_ctx(ctx_dict)
                s = _make_matching_event(law, ctx, rng, meta=(("broken_cond", (0, 1)),))
                situations.append(s)

        # 3. Tầng unrelated: trigger không khớp
        for _ in range(n_unrelated):
            ctx_dict = _random_ctx_dict(rng)
            ctx = _dict_to_ctx(ctx_dict)
            s = _make_unrelated_event(law, ctx, rng)
            situations.append(s)

    rng.shuffle(situations)
    return situations

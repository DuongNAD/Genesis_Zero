"""Tests cho genesis/laweval.py và genesis/situations.py — Không gian tình huống và lấy mẫu phân tầng."""

from __future__ import annotations

import collections
import random

import pytest

from genesis import law_config as lc
from genesis.lawdsl import (
    Cond,
    CondKind,
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
    random_law,
    vocab_for_brain,
)
from genesis.laweval import (
    Ctx,
    LawEvent,
    cond_holds,
    evaluate,
    trigger_matches,
)
from genesis.situations import sample_situations, strata_of


def test_acceptance_20_seeds() -> None:
    """Nghiệm thu chính: 20 seeds × 5 laws, kiểm tỉ lệ phân tầng, broken_cond và acc0."""
    for seed in range(20):
        for idx in range(5):
            law = random_law(random.Random(seed * 100 + idx))
            ss = sample_situations(law, lc.N_SITUATIONS, random.Random(seed))
            assert len(ss) == lc.N_SITUATIONS
            c = collections.Counter(strata_of(law, s) for s in ss)
            if law.conds:
                for k, want in (("fires", 0.4), ("near_miss", 0.4), ("unrelated", 0.2)):
                    assert abs(c[k] / lc.N_SITUATIONS - want) < 0.03, (law, dict(c))
                miss = collections.Counter(
                    dict(s.meta).get("broken_cond")
                    for s in ss
                    if strata_of(law, s) == "near_miss"
                )
                assert max(miss.values()) / min(miss.values()) < 1.6, miss
            else:
                assert abs(c["fires"] / lc.N_SITUATIONS - 0.5) < 0.05, dict(c)
                assert c["near_miss"] == 0
            acc0 = sum(evaluate(law, s) is None for s in ss) / lc.N_SITUATIONS
            assert 0.45 <= acc0 <= 0.65, (law, acc0)
            for s in ss:
                assert (strata_of(law, s) == "fires") == (evaluate(law, s) is not None)


def test_determinism() -> None:
    """B4: sample_situations tất định với cùng law và seed."""
    law = random_law(random.Random(3))
    s1 = sample_situations(law, 50, random.Random(9))
    s2 = sample_situations(law, 50, random.Random(9))
    assert s1 == s2


def test_pure_functions() -> None:
    """B5: evaluate, trigger_matches, cond_holds không làm đột biến dữ liệu đầu vào."""
    law = random_law(random.Random(3))
    ss = sample_situations(law, 10, random.Random(1))
    s0 = ss[0]
    before_ctx = (
        s0.ctx.phase,
        s0.ctx.terrain,
        s0.ctx.hp_band,
        s0.ctx.energy_band,
        s0.ctx.age_band,
        s0.ctx.wind_rel,
        s0.ctx.alone,
        dict(s0.ctx.recent),
        {k: dict(v) for k, v in s0.ctx.counts.items()},
        dict(s0.ctx.subject),
    )
    before_event = (s0.kind, s0.arg, s0.n, s0.k, s0.r, s0.meta)

    for _ in range(10):
        _ = evaluate(law, s0)
        _ = trigger_matches(law, s0)
        if s0.ctx is not None and law.conds:
            _ = cond_holds(law.conds[0], s0.ctx)

    after_ctx = (
        s0.ctx.phase,
        s0.ctx.terrain,
        s0.ctx.hp_band,
        s0.ctx.energy_band,
        s0.ctx.age_band,
        s0.ctx.wind_rel,
        s0.ctx.alone,
        dict(s0.ctx.recent),
        {k: dict(v) for k, v in s0.ctx.counts.items()},
        dict(s0.ctx.subject),
    )
    after_event = (s0.kind, s0.arg, s0.n, s0.k, s0.r, s0.meta)

    assert before_ctx == after_ctx
    assert before_event == after_event


def test_ctx_full_population_invariant_b1() -> None:
    """B1: Mọi trường trong Ctx đều phải được điền đầy đủ cho tất cả tình huống."""
    law = random_law(random.Random(42))
    ss = sample_situations(law, 100, random.Random(42))
    for s in ss:
        ctx = s.ctx
        assert ctx is not None
        assert ctx.phase in ("DAY", "NIGHT")
        assert ctx.terrain in ("PLAIN", "WATER", "BUSH", "ROCK", "FIRE")
        assert ctx.hp_band in ("LOW", "MID", "HIGH")
        assert ctx.energy_band in ("LOW", "MID", "HIGH")
        assert ctx.age_band in ("YOUNG", "OLD")
        assert ctx.wind_rel in ("WITH", "AGAINST")
        assert isinstance(ctx.alone, bool)
        assert len(ctx.recent) >= 7
        for act in ("DRINK", "EAT", "ATTACK", "HIT_BY", "STEP_ON", "SPEAK", "REST"):
            assert act in ctx.recent
            assert isinstance(ctx.recent[act], int)
        for sp in ("SAME_SP", "OTHER_SP", "ANY"):
            assert sp in ctx.counts
            for r in (1, 2, 3):
                assert r in ctx.counts[sp]
                assert isinstance(ctx.counts[sp][r], int)
        for sub in ("ARMOR>=3", "SPEED>=3", "BRAIN<=1", "SAME_SP"):
            assert sub in ctx.subject
            assert isinstance(ctx.subject[sub], bool)


def test_frozen_and_hashable() -> None:
    """Ctx và LawEvent là frozen dataclass và có thể đưa vào set/dict."""
    law = random_law(random.Random(7))
    ss = sample_situations(law, 20, random.Random(7))
    s_set = set(ss)
    assert len(s_set) == len(ss)

    ctx_set = {s.ctx for s in ss if s.ctx is not None}
    assert len(ctx_set) > 0

    s0 = ss[0]
    with pytest.raises(Exception):
        s0.kind = TriggerKind.EAT  # type: ignore

    if s0.ctx is not None:
        with pytest.raises(Exception):
            s0.ctx.phase = "NIGHT"  # type: ignore


def test_d1_zero_conds_strata_invariant_b3() -> None:
    """B3: Luật 0 cond phân tầng 50% fires / 50% unrelated, near_miss = 0."""
    v0 = vocab_for_brain(0)
    law = random_law(random.Random(12), v0)
    assert len(law.conds) == 0

    ss = sample_situations(law, 400, random.Random(12))
    c = collections.Counter(strata_of(law, s) for s in ss)
    assert c["near_miss"] == 0
    assert c["fires"] == 200
    assert c["unrelated"] == 200


def test_d2_one_cond_near_miss_distribution() -> None:
    """Luật 1 cond có near_miss tập trung 100% vào chiều cond 0."""
    law = Law(
        Trigger(TriggerKind.EAT, "FRUIT_A"),
        (Cond(CondKind.PHASE, "NIGHT"),),
        Effect(EffectKind.DAMAGE, Mag.SMALL, Dur.INSTANT),
    )
    ss = sample_situations(law, 400, random.Random(42))
    c = collections.Counter(strata_of(law, s) for s in ss)
    assert c["fires"] == 160
    assert c["near_miss"] == 160
    assert c["unrelated"] == 80

    miss = collections.Counter(
        dict(s.meta).get("broken_cond")
        for s in ss
        if strata_of(law, s) == "near_miss"
    )
    assert set(miss.keys()) == {(0,)}
    assert miss[(0,)] == 160


def test_d3_two_conds_near_miss_distribution() -> None:
    """Luật 2 conds có near_miss trải đều 3 trường hợp: (0,), (1,), (0, 1)."""
    law = Law(
        Trigger(TriggerKind.EAT, "FRUIT_A"),
        (Cond(CondKind.PHASE, "NIGHT"), Cond(CondKind.HP, "LOW")),
        Effect(EffectKind.DAMAGE, Mag.SMALL, Dur.INSTANT),
    )
    ss = sample_situations(law, 400, random.Random(42))
    c = collections.Counter(strata_of(law, s) for s in ss)
    assert c["fires"] == 160
    assert c["near_miss"] == 160
    assert c["unrelated"] == 80

    miss = collections.Counter(
        dict(s.meta).get("broken_cond")
        for s in ss
        if strata_of(law, s) == "near_miss"
    )
    assert set(miss.keys()) == {(0,), (1,), (0, 1)}
    assert max(miss.values()) / min(miss.values()) < 1.1


def test_cond_holds_evaluation_rules() -> None:
    """Kiểm tra quy tắc đánh giá từng loại Cond."""
    ctx = Ctx(
        phase="DAY",
        terrain="WATER",
        hp_band="LOW",
        energy_band="HIGH",
        age_band="YOUNG",
        wind_rel="WITH",
        alone=True,
        recent={"DRINK": 2, "EAT": 10},
        counts={
            "SAME_SP": {1: 1, 2: 2, 3: 3},
            "OTHER_SP": {1: 0, 2: 1, 3: 2},
            "ANY": {1: 1, 2: 3, 3: 5},
        },
        subject={
            "ARMOR>=3": True,
            "SPEED>=3": False,
            "BRAIN<=1": True,
            "SAME_SP": False,
        },
    )

    assert cond_holds(Cond(CondKind.PHASE, "DAY"), ctx) is True
    assert cond_holds(Cond(CondKind.PHASE, "NIGHT"), ctx) is False

    assert cond_holds(Cond(CondKind.TERRAIN, "WATER"), ctx) is True
    assert cond_holds(Cond(CondKind.TERRAIN, "PLAIN"), ctx) is False

    assert cond_holds(Cond(CondKind.HP, "LOW"), ctx) is True
    assert cond_holds(Cond(CondKind.HP, "HIGH"), ctx) is False

    assert cond_holds(Cond(CondKind.ENERGY, "HIGH"), ctx) is True
    assert cond_holds(Cond(CondKind.ENERGY, "LOW"), ctx) is False

    assert cond_holds(Cond(CondKind.AGE, "YOUNG"), ctx) is True
    assert cond_holds(Cond(CondKind.AGE, "OLD"), ctx) is False

    assert cond_holds(Cond(CondKind.WIND, "WITH"), ctx) is True
    assert cond_holds(Cond(CondKind.WIND, "AGAINST"), ctx) is False

    assert cond_holds(Cond(CondKind.ALONE), ctx) is True

    # RECENT (B6)
    assert cond_holds(Cond(CondKind.RECENT, "DRINK", k=5), ctx) is True
    assert cond_holds(Cond(CondKind.RECENT, "DRINK", k=1), ctx) is False
    assert cond_holds(Cond(CondKind.RECENT, "REST", k=5), ctx) is False

    # COUNT (B7)
    assert cond_holds(Cond(CondKind.COUNT, "SAME_SP", r=2, op=">=", n=2), ctx) is True
    assert cond_holds(Cond(CondKind.COUNT, "SAME_SP", r=2, op=">=", n=3), ctx) is False
    assert cond_holds(Cond(CondKind.COUNT, "OTHER_SP", r=1, op="<=", n=0), ctx) is True

    # SUBJECT
    assert cond_holds(Cond(CondKind.SUBJECT, "ARMOR>=3"), ctx) is True
    assert cond_holds(Cond(CondKind.SUBJECT, "SPEED>=3"), ctx) is False

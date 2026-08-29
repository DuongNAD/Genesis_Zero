"""Tests cho genesis/lawgen.py — Bốc thăm luật và Gate A (L-03)."""

from __future__ import annotations

import random
import pytest

from genesis import config
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
)
from genesis.lawgen import (
    generate,
    is_solo_exploitable,
    observable,
    requires_cooperation,
)


def test_determinism_b1_b2() -> None:
    """Bất biến B1, B2: generate tất định theo seed và không bị ảnh hưởng bởi module random."""
    # check_solvable=False cho nhanh: bài này kiểm TẤT ĐỊNH, không kiểm khả giải.
    random.seed(999)
    a = generate(42, "STANDARD", check_solvable=False)
    random.seed(123)
    b = generate(42, "STANDARD", check_solvable=False)
    assert a == b

    c = generate(43, "STANDARD", check_solvable=False)
    assert a != c


def test_observable_gate_a() -> None:
    """Gate A: observable kiểm tra bán kính không vượt quá SIGHT_BASE + min_sense."""
    # SIGHT_BASE = 2
    # min_sense = 1 -> max_r = 3
    # min_sense = 0 -> max_r = 2

    # DEATH_NEAR
    l_dn3 = Law(
        Trigger(TriggerKind.DEATH_NEAR, r=3),
        (),
        Effect(EffectKind.DAMAGE, Mag.SMALL, Dur.INSTANT),
    )
    assert observable(l_dn3, min_sense=1) is True
    assert observable(l_dn3, min_sense=0) is False

    l_dn2 = Law(
        Trigger(TriggerKind.DEATH_NEAR, r=2),
        (),
        Effect(EffectKind.DAMAGE, Mag.SMALL, Dur.INSTANT),
    )
    assert observable(l_dn2, min_sense=0) is True

    # COUNT cond
    l_cnt3 = Law(
        Trigger(TriggerKind.EAT, "FRUIT_A"),
        (Cond(CondKind.COUNT, "SAME_SP", r=3, op=">=", n=1),),
        Effect(EffectKind.HEAL, Mag.SMALL, Dur.SHORT),
    )
    assert observable(l_cnt3, min_sense=1) is True
    assert observable(l_cnt3, min_sense=0) is False

    l_cnt2 = Law(
        Trigger(TriggerKind.EAT, "FRUIT_A"),
        (Cond(CondKind.COUNT, "SAME_SP", r=2, op=">=", n=1),),
        Effect(EffectKind.HEAL, Mag.SMALL, Dur.SHORT),
    )
    assert observable(l_cnt2, min_sense=0) is True

    # Khác không bị chặn
    l_plain = Law(
        Trigger(TriggerKind.DRINK),
        (Cond(CondKind.PHASE, "DAY"),),
        Effect(EffectKind.ENERGY_GAIN, Mag.MED, Dur.INSTANT),
    )
    assert observable(l_plain, min_sense=0) is True


def test_cooperation_and_solo_definitions() -> None:
    """Kiểm tra phân loại luật đơn độc và luật hợp tác (§6.3)."""
    # 1. Trigger ADJACENT với n>=1
    l_adj = Law(
        Trigger(TriggerKind.ADJACENT, "SAME_SP", n=1),
        (),
        Effect(EffectKind.HEAL, Mag.SMALL, Dur.LONG),
    )
    assert requires_cooperation(l_adj) is True
    assert is_solo_exploitable(l_adj) is False

    # 2. Cond COUNT với op=">=" và n>=1
    l_count = Law(
        Trigger(TriggerKind.EAT, "FRUIT_B"),
        (Cond(CondKind.COUNT, "SAME_SP", r=2, op=">=", n=1),),
        Effect(EffectKind.ENERGY_GAIN, Mag.BIG, Dur.INSTANT),
    )
    assert requires_cooperation(l_count) is True
    assert is_solo_exploitable(l_count) is False

    # Cond COUNT với op="<=" thì không phải đòi hỏi hợp tác
    l_count_le = Law(
        Trigger(TriggerKind.EAT, "FRUIT_B"),
        (Cond(CondKind.COUNT, "SAME_SP", r=2, op="<=", n=1),),
        Effect(EffectKind.ENERGY_GAIN, Mag.BIG, Dur.INSTANT),
    )
    assert requires_cooperation(l_count_le) is False
    assert is_solo_exploitable(l_count_le) is True

    # 3. Cond SUBJECT == "SAME_SP"
    l_subj = Law(
        Trigger(TriggerKind.DRINK),
        (Cond(CondKind.SUBJECT, "SAME_SP"),),
        Effect(EffectKind.DAMAGE, Mag.MED, Dur.SHORT),
    )
    assert requires_cooperation(l_subj) is True
    assert is_solo_exploitable(l_subj) is False

    # Luật thông thường: đơn độc
    l_solo = Law(
        Trigger(TriggerKind.EAT, "FRUIT_C"),
        (Cond(CondKind.PHASE, "NIGHT"),),
        Effect(EffectKind.POISON, Mag.MED, Dur.LONG),
    )
    assert requires_cooperation(l_solo) is False
    assert is_solo_exploitable(l_solo) is True


def test_generate_arms() -> None:
    """Kiểm tra số lượng và cấu hình luật cho từng arm."""
    # SOLO_LAB
    laws_solo = generate(10, "SOLO_LAB", check_solvable=False)
    assert len(laws_solo) == lc.LAWS_PER_MATCH["SOLO_LAB"] == 1
    assert laws_solo[0].tier() == "D1"

    # HARSH
    laws_harsh = generate(10, "HARSH", check_solvable=False)
    assert len(laws_harsh) == lc.LAWS_PER_MATCH["HARSH"] == 4
    tiers_harsh = [l.tier() for l in laws_harsh]
    assert tiers_harsh == ["D2", "D2", "D3", "D4"]

    # Invalid arm
    with pytest.raises(ValueError, match="Unknown arm"):
        generate(10, "INVALID_ARM", check_solvable=False)


def test_acceptance_200_seeds() -> None:
    """Nghiệm thu: 200 bộ luật STANDARD thoả Gate A và ràng buộc §6.3.

    `check_solvable=False`: bài này kiểm Gate A + §6.3, không kiểm khả giải.
    Bật cổng khả giải lên thì `generate` mất ~2 s/bộ và 200 bộ = ~7 phút —
    treo cả bộ test. Cổng B/C có bài riêng ở tests/test_gates.py.
    """
    for i in range(200):
        laws = generate(i, "STANDARD", check_solvable=False)
        assert len(laws) == lc.LAWS_PER_MATCH["STANDARD"]
        assert all(observable(l, 1) for l in laws), (i, laws)
        assert any(is_solo_exploitable(l) for l in laws), (i, laws)
        assert any(requires_cooperation(l) for l in laws), (i, laws)
        assert sorted(l.tier() for l in laws) != ["D1", "D1", "D1"], (i, laws)
        for l in laws:
            assert is_solo_exploitable(l) != requires_cooperation(l)

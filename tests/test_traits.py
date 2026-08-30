"""Genesis Zero — kiểm thử cho vector trait và chỉ số dẫn xuất (W-07)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, astuple

import pytest

from genesis import config
from genesis.traits import Traits, founder_traits


def test_founder_traits_all_species() -> None:
    """Mọi loài trong config.FOUNDERS đều sinh vector Traits hợp lệ với tổng 12."""
    for sp, v in config.FOUNDERS.items():
        t = founder_traits(sp)
        assert astuple(t) == v
        assert sum(astuple(t)) == config.TRAIT_SUM
        assert all(config.TRAIT_MIN <= val <= config.TRAIT_MAX for val in astuple(t))


def test_derived_properties_table() -> None:
    """Kiểm tra bảng chỉ số dẫn xuất chuẩn cho 5 loài founder."""
    L1, L2, L3, L4, L5 = (founder_traits(s) for s in ("L1", "L2", "L3", "L4", "L5"))

    # Các chỉ số KHÔNG phụ thuộc hằng số bị tune ở W-12 -> khoá cứng được
    assert (L1.token_budget, L1.think_interval, L1.damage,
            L1.moves_per_tick, L1.sight_radius) == (176, 3, 13, 2, 3)
    assert (L2.token_budget, L2.think_interval, L2.damage) == (140, 4, 16)
    assert (L3.token_budget, L3.sight_radius, L3.moves_per_tick) == (140, 5, 2)
    assert abs(L4.dmg_taken_mult - 0.40) < 1e-9
    assert (L5.moves_per_tick, L5.token_budget, L5.think_interval) == (3, 32, 7)
    assert abs(L5.dmg_taken_mult - 1.0) < 1e-9

    # energy_max và upkeep PHỤ THUỘC hằng số tune -> suy từ config, đừng khoá cứng.
    # Bẫy: bản đầu khoá `L1.energy_max == 80`; W-12 tune ENERGY_BASE 60->85 là test đỏ
    # dù code đúng. Test không được phạt việc tune — đó là cả mục đích của mốc M1.
    for sp, tr in (("L1", L1), ("L2", L2), ("L3", L3), ("L4", L4), ("L5", L5)):
        want_e = config.ENERGY_BASE + config.ENERGY_PER_STOMACH * tr.stomach
        assert tr.energy_max == want_e, (sp, tr.energy_max, want_e)
        want_u = (config.UPKEEP_BASE + config.UPKEEP_BRAIN * tr.brain
                  + config.UPKEEP_ATTACK * tr.attack + config.UPKEEP_ARMOR * tr.armor
                  + config.UPKEEP_SPEED * tr.speed + config.UPKEEP_SENSE * tr.sense
                  + config.UPKEEP_STOMACH * tr.stomach)
        assert abs(tr.upkeep - want_u) < 1e-9, sp
    # quan hệ phải giữ: bụng to hơn thì bể năng lượng lớn hơn
    assert L4.energy_max > L1.energy_max > L2.energy_max


def test_traits_frozen_immutability() -> None:
    """B1: Traits là frozen dataclass, không thể gán đè thuộc tính tại chỗ."""
    t = founder_traits("L1")
    with pytest.raises(FrozenInstanceError):
        t.brain = 5  # type: ignore[misc]


def test_traits_invariants_post_init() -> None:
    """B1: __post_init__ bắt mọi vi phạm tổng != 12 hoặc ngoài [TRAIT_MIN, TRAIT_MAX]."""
    # Tổng > 12
    with pytest.raises(AssertionError):
        Traits(5, 5, 5, 5, 5, 5)

    # Tổng < 12
    with pytest.raises(AssertionError):
        Traits(4, 3, 1, 2, 1, 0)

    # Trait vượt MAX (12 > 5) dù tổng = 12
    with pytest.raises(AssertionError):
        Traits(0, 0, 0, 0, 0, 12)

    # Trait âm dù tổng = 12
    with pytest.raises(AssertionError):
        Traits(-1, 4, 3, 2, 2, 2)


def test_traits_shift_immutability_and_values() -> None:
    """B2 & B3: shift() trả về instance MỚI, giữ nguyên instance cũ và tổng luôn = 12."""
    L1 = founder_traits("L1")  # (4, 3, 1, 2, 1, 1)
    n = L1.shift("brain", "armor")

    assert n is not L1
    assert n.brain == 3
    assert n.armor == 2
    assert L1.brain == 4
    assert L1.armor == 1
    assert sum(astuple(n)) == config.TRAIT_SUM


def test_traits_shift_bounds_checking() -> None:
    """B3: shift() kiểm tra cả 2 đầu frm và to, ném ValueError nếu chạm biên."""
    L5 = founder_traits("L5")  # (0, 2, 0, 5, 3, 2)

    # frm đã ở mức 0 -> không thể giảm tiếp
    with pytest.raises(ValueError, match="Không thể giảm"):
        L5.shift("armor", "brain")

    # to đã ở mức MAX (5) -> không thể tăng tiếp
    with pytest.raises(ValueError, match="Không thể tăng"):
        L5.shift("attack", "speed")

    # cả hai đầu đều chạm biên (frm=0, to=5) -> ném ValueError
    with pytest.raises(ValueError):
        L5.shift("brain", "speed")

    # frm không hợp lệ
    with pytest.raises(ValueError, match="nguồn không hợp lệ"):
        L5.shift("invalid_trait", "brain")

    # to không hợp lệ
    with pytest.raises(ValueError, match="đích không hợp lệ"):
        L5.shift("attack", "invalid_trait")


def test_founder_traits_fallback_for_unknown_species() -> None:
    """Loài lạ không có trong config.FOUNDERS nhận vector mặc định chia đều 12 điểm."""
    alien = founder_traits("Alien")
    assert astuple(alien) == (2, 2, 2, 2, 2, 2)
    assert sum(astuple(alien)) == config.TRAIT_SUM

    mutant = founder_traits("Mutant")
    assert astuple(mutant) == (2, 2, 2, 2, 2, 2)


def test_think_interval_clamps_at_minimum() -> None:
    """think_interval không bao giờ nhỏ hơn config.THINK_MIN dù brain = 5."""
    t = Traits(brain=5, attack=2, armor=1, speed=2, sense=1, stomach=1)
    assert t.think_interval == config.THINK_MIN

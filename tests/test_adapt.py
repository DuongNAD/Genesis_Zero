"""Genesis Zero — kiểm thử cho genesis/adapt.py và cơ chế thích nghi (W-12)."""

from __future__ import annotations

from dataclasses import astuple
import inspect
import json
from pathlib import Path
import random

import pytest

from genesis import config
import genesis.adapt as A
from genesis.adapt import award_adapt, maybe_shift, reset_body
from genesis.creature import Creature
from genesis.run import main
from genesis.tick import build_match, tick
from genesis.traits import Traits, founder_traits


def _make_creature(species: str = "L1") -> Creature:
    t = founder_traits(species)
    return Creature(
        id=f"{species}:0",
        species=species,
        traits=t,
        pos=(0, 0),
        hp=float(config.HP_MAX),
        energy=t.energy_max,
    )


def test_award_adapt_eat() -> None:
    """Ăn đủ ADAPT_ON_EAT lần thì +1 adapt_point và trả về 1."""
    c = _make_creature("L1")
    for _ in range(config.ADAPT_ON_EAT - 1):
        assert award_adapt(c, "eat") == 0
        assert c.adapt_points == 0

    assert award_adapt(c, "eat") == 1
    assert c.adapt_points == 1
    assert c.eat_count == config.ADAPT_ON_EAT

    # Chu kỳ tiếp theo
    for _ in range(config.ADAPT_ON_EAT - 1):
        assert award_adapt(c, "eat") == 0
    assert award_adapt(c, "eat") == 1
    assert c.adapt_points == 2


def test_award_adapt_win() -> None:
    """Thắng trận cộng ADAPT_ON_WIN adapt_point và trả về ADAPT_ON_WIN."""
    c = _make_creature("L2")
    pts = award_adapt(c, "win")
    assert pts == config.ADAPT_ON_WIN
    assert c.adapt_points == config.ADAPT_ON_WIN
    assert c.win_count == 1

    pts2 = award_adapt(c, "win")
    assert pts2 == config.ADAPT_ON_WIN
    assert c.adapt_points == 2 * config.ADAPT_ON_WIN
    assert c.win_count == 2


def test_award_adapt_survive() -> None:
    """Sống liên tục ADAPT_ON_SURVIVE tick thì +1 adapt_point."""
    c = _make_creature("L3")
    for _ in range(config.ADAPT_ON_SURVIVE - 1):
        assert award_adapt(c, "survive") == 0
        assert c.adapt_points == 0

    assert award_adapt(c, "survive") == 1
    assert c.adapt_points == 1
    assert c.ticks_alive_streak == config.ADAPT_ON_SURVIVE


def test_award_adapt_invalid_reason() -> None:
    """Lý do lạ ném ValueError."""
    c = _make_creature("L1")
    with pytest.raises(ValueError):
        award_adapt(c, "fly")


def test_maybe_shift_no_points() -> None:
    """Không có điểm thích nghi thì không dịch."""
    c = _make_creature("L1")
    c.adapt_points = 0
    res = maybe_shift(c, random.Random(42))
    assert res is None
    assert c.traits == founder_traits("L1")
    assert c.shift_log == []


def test_maybe_shift_l1_founder() -> None:
    """L1 founder (4,3,1,2,1,1): CHUYÊN HOÁ — lấy từ thấp nhất, dồn vào cao nhất.

    Luật đổi ở W-12: bản đầu "cao nhất -> thấp nhất" tất yếu kéo mọi loài về
    (2,2,2,2,2,2) chỉ sau ba lần dịch, xoá sạch bản sắc loài. Xem genesis/adapt.py.
    """
    c = _make_creature("L1")
    c.adapt_points = 1
    before = astuple(c.traits)
    res = maybe_shift(c, random.Random(1))
    assert res == ("armor", "brain")          # armor=1 thấp nhất -> brain=4 cao nhất
    assert c.adapt_points == 0
    assert c.shift_log == [("armor", "brain")]
    assert sum(astuple(c.traits)) == config.TRAIT_SUM
    assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in astuple(c.traits))
    assert astuple(c.traits) != before
    assert c.traits.brain == 5
    assert c.traits.armor == 0


def test_maybe_shift_tie_breaking_order() -> None:
    """Hoà max/min phá bằng thứ tự config.TRAIT_NAMES."""
    # L4 founder: brain:1, attack:1, armor:5, speed:1, sense:2, stomach:2
    # armor=5 đã chạm trần nên KHÔNG nhận thêm; cao nhất còn nhận được là sense(2).
    # thấp nhất là 1 (brain, attack, speed) -> phá hoà bằng thứ tự -> brain.
    c = _make_creature("L4")
    c.adapt_points = 1
    res = maybe_shift(c, random.Random(99))
    assert res == ("brain", "sense"), res
    assert c.traits.brain == 0
    assert c.traits.sense == 3
    assert c.traits.armor == 5


def test_maybe_shift_equal_traits() -> None:
    """Khi mọi trait bằng nhau (2,2,2,2,2,2), frm == to -> không dịch, trả None."""
    t = Traits(2, 2, 2, 2, 2, 2)
    c = Creature(
        id="EQUAL:0",
        species="EQUAL",
        traits=t,
        pos=(0, 0),
        hp=50.0,
        energy=t.energy_max,
        adapt_points=1,
    )
    res = maybe_shift(c, random.Random(1))
    assert res is None
    assert c.traits == t


def test_reset_body() -> None:
    """reset_body đưa về founder traits, xoá adapt_points và shift_log. B1: không có hàm reset."""
    c = _make_creature("L1")
    c.adapt_points = 5
    c.traits = founder_traits("L1").shift("brain", "armor")
    c.shift_log = [("brain", "armor")]
    reset_body(c)
    assert c.traits == founder_traits("L1")
    assert c.adapt_points == 0
    assert c.shift_log == []

    # Kiểm tra B1: adapt module không có reset / reset_all
    assert not hasattr(A, "reset")
    assert not hasattr(A, "reset_all")


def test_integration_trait_shift_in_simulation(tmp_path: Path) -> None:
    """Chạy simulation ghi nhận sự kiện TRAIT_SHIFT trong log."""
    out_file = tmp_path / "w12.jsonl"
    main(["--seed", "33", "--ticks", "400", "--no-render", "--out", str(out_file)])

    rows = [
        json.loads(line)
        for line in out_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    shifts = [r for r in rows if r["kind"] == "TRAIT_SHIFT"]
    assert len(shifts) > 0, "Không có sự kiện TRAIT_SHIFT nào trong 400 tick"

    for sh in shifts:
        assert "creature_id" in sh
        assert "species_id" in sh
        assert "frm" in sh
        assert "to" in sh
        assert "traits" in sh
        assert sum(sh["traits"]) == config.TRAIT_SUM
        assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in sh["traits"])


def test_permutation_invariance_with_adapt() -> None:
    """B4: Hoán vị thứ tự danh sách creatures vẫn cho kết quả y hệt."""
    def run(shuffle_seed: int | None = None, ticks: int = 200) -> list:
        w, cs, st, rng = build_match(seed=99)
        if shuffle_seed is not None:
            random.Random(shuffle_seed).shuffle(cs)
        for t in range(ticks):
            tick(w, cs, t, rng, st)
        return sorted(
            (
                c.id,
                round(c.energy, 6),
                round(c.hp, 6),
                c.pos,
                c.alive,
                c.age,
                c.dead_until,
                c.poison_ticks,
                c.adapt_points,
                c.eat_count,
                c.win_count,
                c.ticks_alive_streak,
                astuple(c.traits),
            )
            for c in cs
        )

    base = run(None)
    for s in (1, 5, 42):
        assert run(s) == base, f"Thứ tự list ảnh hưởng kết quả thích nghi (shuffle seed {s})"

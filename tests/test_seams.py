"""Genesis Zero — kiểm thử cho 3 đường may mở rộng (N-01, N-02, N-03)."""

from __future__ import annotations

import json
from pathlib import Path
import random

import pytest

from genesis import config
from genesis.creature import Creature
from genesis.logio import COMMON_FIELDS, EVENT_KINDS, LogWriter
from genesis.reflex import ActiveGoal, Goal
from genesis.registry import (
    SpeciesRegistry,
    SpeciesSpec,
    from_config,
    registry_from_config,
)
from genesis.strategist import (
    LlmStrategist,
    ReflexStrategist,
    RemoteClientStrategist,
    Strategist,
)
from genesis.tick import SimState, build_match, tick
from genesis.traits import founder_traits


def test_strategist_protocol_and_classes() -> None:
    """N-01: Các lớp hiện thực đều thoả Strategist Protocol."""
    assert isinstance(ReflexStrategist(), Strategist)
    assert isinstance(RemoteClientStrategist({}), Strategist)
    assert isinstance(LlmStrategist("http://x", []), Strategist)


def test_remote_client_strategist_queue() -> None:
    """N-01: RemoteClientStrategist trả None khi rỗng, trả Goal khi có trong hàng đợi."""
    w, cs, st, rng = build_match(seed=1)
    strat = RemoteClientStrategist({})
    assert strat.decide(cs[0], w, []) is None

    goal = ActiveGoal(goal=Goal.FORAGE, target=None, ttl=5)
    strat_with_goal = RemoteClientStrategist({cs[0].id: goal})
    decided = strat_with_goal.decide(cs[0], w, [])
    assert decided == goal
    # Gọi lần 2: hàng đợi đã lấy ra nên trả None
    assert strat_with_goal.decide(cs[0], w, []) is None


def test_llm_strategist_roi_ve_phan_xa() -> None:
    """N-01/B-05: chưa có câu trả lời nào của model thì vẫn phải ra được ý đồ.

    Đây là hình dạng cuối của cái stub cũ: đường may thứ nhất không còn chỗ nào
    `NotImplementedError`, và tầng phản xạ đỡ dưới đúng như bất biến 1 của B-05.
    """
    w, cs, _, _ = build_match(seed=1)
    llama = LlmStrategist("http://khong-ton-tai", [c.id for c in cs])
    g = llama.decide(cs[0], w, [], random.Random(0))
    assert g is not None


def test_tick_without_mode_branch() -> None:
    """B1: tick() không có nhánh theo chế độ và không isinstance Strategist."""
    src = Path("genesis/tick.py").read_text(encoding="utf-8")
    assert "isinstance(" not in src or "Strategist" not in src.split("isinstance(")[1][:60]
    assert 'mode ==' not in src
    assert "mode ==" not in src


def test_registry_from_config_matches_population() -> None:
    """B2 & B3: registry_from_config tạo đúng số lượng và thứ tự cố định."""
    r = registry_from_config()
    ids = [s.species_id for s in r]
    assert ids == sorted(ids), ids
    assert sum(s.pop for s in r) == sum(config.POPULATION.values())

    r2 = from_config()
    assert [s.species_id for s in r2] == ids


def test_registry_operations() -> None:
    """N-02: Các thao tác add, remove, mark_feral, __iter__."""
    reg = SpeciesRegistry()
    tr = founder_traits("L1")
    spec_b = SpeciesSpec(species_id="b_species", display_name="B", persona="pB", traits=tr, pop=2)
    spec_a = SpeciesSpec(species_id="a_species", display_name="A", persona="pA", traits=tr, pop=3)

    # Thêm thứ tự b trước a
    ids_b = reg.add(spec_b)
    ids_a = reg.add(spec_a)

    assert ids_b == ["b_species:0", "b_species:1"]
    assert ids_a == ["a_species:0", "a_species:1", "a_species:2"]

    # __iter__ luôn trả về theo thứ tự sorted: a_species trước b_species
    iter_ids = [s.species_id for s in reg]
    assert iter_ids == ["a_species", "b_species"]

    # mark_feral
    assert not reg["b_species"].is_feral
    reg.mark_feral("b_species", True)
    assert reg["b_species"].is_feral

    # remove
    reg.remove("a_species")
    assert "a_species" not in reg
    assert len(reg) == 1


def test_add_species_mid_match() -> None:
    """B4: Thêm loài và cá thể giữa ván, sim tiếp tục chạy bình thường."""
    w, cs, st, rng = build_match(seed=3)
    r = registry_from_config()
    for t in range(30):
        tick(w, cs, t, rng, st)

    tr = next(iter(r)).traits
    new_ids = r.add(SpeciesSpec("zz_new", "Moi", "x", tr, 2))
    assert len(new_ids) == 2 and all(i.startswith("zz_new:") for i in new_ids)

    # Thêm thực thể mới vào cs
    for cid in new_ids:
        cs.append(
            Creature(
                id=cid,
                species="zz_new",
                traits=tr,
                pos=(0, 0),
                hp=float(config.HP_MAX),
                energy=tr.energy_max,
            )
        )

    for t in range(30, 60):
        tick(w, cs, t, rng, st)

    assert any(c.id.startswith("zz_new:") for c in cs)


def test_tick_with_remote_strategist() -> None:
    """Vòng tick chạy với RemoteClientStrategist và giữ goal khi trả None."""
    w, cs, st, rng = build_match(seed=5)
    custom_goal = ActiveGoal(goal=Goal.REST, target=None, ttl=10)
    queue_dict = {cs[0].id: custom_goal}
    strat = RemoteClientStrategist(queue_dict)

    # Tick 0: nhận custom_goal
    tick(w, cs, 0, rng, st, strategist=strat)
    assert st.active_goals[cs[0].id].goal == Goal.REST

    # Tick 1: queue_dict đã rỗng -> strat trả None -> giữ goal cũ
    tick(w, cs, 1, rng, st, strategist=strat)
    assert st.active_goals[cs[0].id].goal == Goal.REST


def test_log_fields_and_event_kinds(tmp_path: Path) -> None:
    """N-03: Kiểm tra COMMON_FIELDS và các EVENT_KINDS bắt buộc."""
    for kind in ("LAW_FIRED", "TRAIT_SHIFT", "DRINK", "PHASE_CHANGE"):
        assert kind in EVENT_KINDS, f"{kind} thiếu trong EVENT_KINDS"

    log_path = tmp_path / "test_log.jsonl"
    with LogWriter(log_path, "match_test") as log:
        log.write(0, "RUN_START", seed=1)
        log.write(1, "DRINK", creature_id="L1:0", species_id="L1", pos=[1, 2])
        log.write(2, "PHASE_CHANGE", phase="DAWN")
        log.write(3, "TRAIT_SHIFT", creature_id="L1:0", frm="speed", to="sense", traits=[4, 3, 1, 1, 2, 1])
        log.write(4, "LAW_FIRED", creature_id="L1:0", law_id="L0", effect="test")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        row = json.loads(line)
        for field in COMMON_FIELDS:
            assert field in row, f"Trường {field} thiếu trong dòng log: {row}"

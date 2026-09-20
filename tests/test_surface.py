"""Tests cho genesis/surface.py và các tính năng mở rộng sandbox v5 (W-13)."""

from __future__ import annotations

import collections
import json
import random
from pathlib import Path

from genesis import law_config
from genesis.creature import Creature
from genesis.run import main
from genesis.surface import SurfaceMap, roll_surface_map
from genesis.tick import SimState, tick
from genesis.world import Terrain, World, phase_at


def test_surface_map_lookup() -> None:
    """SurfaceMap tra xuôi và tra ngược chính xác."""
    m = SurfaceMap({
        "FRUIT_A": "quả đỏ tròn",
        "FRUIT_B": "quả xanh dài",
        "FRUIT_C": "quả vàng gai",
        "FRUIT_D": "quả tím dẹt",
    })
    assert m.surface_of("FRUIT_A") == "quả đỏ tròn"
    assert m.surface_of("FRUIT_B") == "quả xanh dài"
    assert m.class_of("quả đỏ tròn") == "FRUIT_A"
    assert m.class_of("quả vàng gai") == "FRUIT_C"
    assert m.class_of("không tồn tại") is None


def test_roll_surface_map_determinism_and_uniqueness() -> None:
    """roll_surface_map tất định theo seed và tạo hoán vị 4 lớp quả."""
    sm1 = roll_surface_map(random.Random(42))
    sm2 = roll_surface_map(random.Random(42))
    assert sm1 == sm2

    sm_diff = roll_surface_map(random.Random(99))
    assert sm1.cls_to_surface != sm_diff.cls_to_surface

    expected_classes = {"FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D"}
    assert set(sm1.cls_to_surface.keys()) == expected_classes
    assert len(set(sm1.cls_to_surface.values())) == 4


def test_phase_at_cycle() -> None:
    """phase_at luân phiên DAY và NIGHT theo PHASE_LEN."""
    assert phase_at(0) == "DAY"
    assert phase_at(law_config.PHASE_LEN - 1) == "DAY"
    assert phase_at(law_config.PHASE_LEN) == "NIGHT"
    assert phase_at(2 * law_config.PHASE_LEN - 1) == "NIGHT"
    assert phase_at(2 * law_config.PHASE_LEN) == "DAY"


def test_drink_action_and_last_drink_tick() -> None:
    """Con đứng trên ô WATER được ghi nhận DRINK và cập nhật last_drink_tick."""
    from genesis.traits import founder_traits

    world = World(10, 10, random.Random(1))
    world.grid[5][5] = Terrain.WATER
    c = Creature(
        id="L1:0",
        species="L1",
        traits=founder_traits("L1"),
        pos=(5, 5),
        hp=50.0,
        energy=100.0,
    )
    assert c.last_drink_tick == -1

    creatures = [c]
    st = SimState(match_seed=1)
    rng = random.Random(1)
    tick(world, creatures, 15, rng, st)

    assert c.last_drink_tick == 15


def test_acceptance_w13_full(tmp_path: Path) -> None:
    """Nghiệm thu toàn bộ W-13 qua một ván 400 tick."""
    out_file = tmp_path / "w13_test.jsonl"
    main(["--seed", "55", "--ticks", "400", "--no-render", "--out", str(out_file)])

    rows = [json.loads(line) for line in out_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    k = collections.Counter(r["kind"] for r in rows)
    assert k["DRINK"] > 0, k
    assert k["PHASE_CHANGE"] == 400 // law_config.PHASE_LEN, (k["PHASE_CHANGE"], 400 // law_config.PHASE_LEN)

    # Chỉ đếm QUẢ. Rong (W-18 §6) cũng sinh ra sự kiện `EAT` nhưng nó không phải
    # đề bài: bề mặt quả bị hoán vị mỗi ván vì luật ẩn nói về chúng, còn rong thì
    # giữ đúng một tên. Trộn nó vào phép đếm này là đo cân bằng của bốn lớp quả
    # bằng một mẫu có năm thứ.
    f = collections.Counter(r.get("fruit_surface") for r in rows
                            if r["kind"] == "EAT" and r.get("fruit_surface") != "rong")
    assert len(f) == 4, f
    assert max(f.values()) / min(f.values()) < 1.6, f

    # Bất biến B1: KHÔNG rò tên lớp
    content = out_file.read_text(encoding="utf-8")
    for cls_name in ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D"):
        assert cls_name not in content

"""Tests cho genesis/world.py — tầm nhìn và quy tắc bụi rậm (W-08)."""

from __future__ import annotations

import ast
from pathlib import Path
import random

import pytest

from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.traits import founder_traits
from genesis.world import Terrain, World, visible


def _mk_creature(cid: str, species: str, pos: tuple[int, int], alive: bool = True) -> Creature:
    traits = founder_traits(species)
    return Creature(
        id=cid,
        species=species,
        traits=traits,
        pos=pos,
        hp=float(config.HP_MAX),
        energy=traits.energy_max,
        alive=alive,
    )


def test_acceptance_criteria() -> None:
    """Nghiệm thu toàn bộ bất biến theo đặc tả W-08."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.PLAIN
    w.grid[10][10] = Terrain.BUSH

    hider = _mk_creature("L2:0", "L2", (10, 10))  # đứng trong bụi
    seer = _mk_creature("L1:0", "L1", (12, 10))  # L1 sight_radius = 3, dist = 2
    assert seer.traits.sight_radius == 3 and w.dist(seer.pos, hider.pos) == 2
    assert visible(seer, w, [hider, seer]) == []  # trong bụi, cách 2 -> KHÔNG thấy
    seer.pos = (11, 10)  # cách 1
    assert visible(seer, w, [hider, seer]) == [hider]  # cách 1 -> thấy

    # ngoài bụi thì thấy bình thường trong tầm
    hider.pos = (13, 10)
    seer.pos = (11, 10)  # dist 2, ô PLAIN
    assert visible(seer, w, [hider, seer]) == [hider]
    hider.pos = (15, 10)  # dist 4 > 3
    assert visible(seer, w, [hider, seer]) == []

    # B1: bán kính của NGƯỜI QUAN SÁT, không phải người bị nhìn
    far = _mk_creature("L3:0", "L3", (16, 10))  # L3 sight_radius = 5
    seer.pos = (11, 10)  # L1 radius 3; dist(11,16) = 5
    assert visible(seer, w, [far, seer]) == []  # L1 KHÔNG thấy L3
    assert visible(far, w, [far, seer]) == [seer]  # nhưng L3 thấy L1

    # B2: con chết không xuất hiện
    dead = _mk_creature("L4:0", "L4", (12, 10), alive=False)
    assert visible(seer, w, [dead, seer]) == []

    # B3: hoán vị đầu vào -> kết quả y hệt, và đã sắp
    a = _mk_creature("L5:0", "L5", (12, 10))
    b = _mk_creature("L1:1", "L1", (10, 11))
    c = _mk_creature("L4:1", "L4", (11, 11))
    r1 = visible(seer, w, [a, b, c, seer])
    r2 = visible(seer, w, [c, seer, a, b])
    assert r1 == r2, (r1, r2)
    assert r1 == sorted(r1, key=creature_sort_key)
    assert seer not in r1  # không tự thấy mình

    # B4: hàm thuần
    snap = [(x.id, x.pos, x.energy, x.alive) for x in (a, b, c, seer)]
    for _ in range(3):
        visible(seer, w, [a, b, c, seer])
    assert snap == [(x.id, x.pos, x.energy, x.alive) for x in (a, b, c, seer)]

    # B5: vòng mép — hai con ở hai rìa đối diện vẫn thấy nhau
    e1 = _mk_creature("L1:0", "L1", (0, 5))
    e2 = _mk_creature("L2:1", "L2", (23, 5))
    assert w.dist(e1.pos, e2.pos) == 1
    assert visible(e1, w, [e1, e2]) == [e2]


def test_no_circular_import() -> None:
    """world.py không import creature.py ở top-level (chống import vòng)."""
    world_path = Path(__file__).parent.parent / "genesis" / "world.py"
    tree = ast.parse(world_path.read_text(encoding="utf-8"))
    top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    bad = [
        n
        for n in top
        if isinstance(n, ast.ImportFrom) and n.module and "creature" in n.module and n.level == 0
    ]
    assert not bad, "import vòng: world.py import creature.py ở top-level"


def test_observer_in_bush_can_see_target_on_plain() -> None:
    """B6: Người quan sát đứng trong bụi vẫn nhìn thấy đối tượng ở ngoài bụi."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.PLAIN
    w.grid[10][10] = Terrain.BUSH

    obs_in_bush = _mk_creature("L1:0", "L1", (10, 10))  # trong bụi
    target_in_plain = _mk_creature("L2:0", "L2", (12, 10))  # ngoài bụi, dist 2 <= 3
    assert visible(obs_in_bush, w, [obs_in_bush, target_in_plain]) == [target_in_plain]


def test_bush_visibility_thresholds() -> None:
    """Bụi rậm: dist=0 và dist=1 thì thấy, dist>=2 thì vô hình."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.PLAIN
    w.grid[5][5] = Terrain.BUSH

    hider = _mk_creature("L2:0", "L2", (5, 5))
    seer = _mk_creature("L3:0", "L3", (5, 5))  # L3 radius = 5, dist = 0
    assert visible(seer, w, [hider, seer]) == [hider]

    seer.pos = (6, 5)  # dist = 1
    assert visible(seer, w, [hider, seer]) == [hider]

    seer.pos = (7, 5)  # dist = 2 <= 5
    assert visible(seer, w, [hider, seer]) == []

    seer.pos = (8, 5)  # dist = 3 <= 5
    assert visible(seer, w, [hider, seer]) == []


def test_rock_does_not_block_vision() -> None:
    """B7: Không raycasting, ROCK không chắn tầm nhìn."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.PLAIN
    w.grid[10][11] = Terrain.ROCK

    seer = _mk_creature("L1:0", "L1", (10, 10))  # radius = 3
    target = _mk_creature("L2:0", "L2", (10, 12))  # dist = 2 qua ô ROCK
    assert visible(seer, w, [seer, target]) == [target]


def test_sorting_with_multi_digit_indices() -> None:
    """B3: Sắp xếp theo creature_sort_key đúng chuẩn số học cho id nhiều chữ số."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.PLAIN

    seer = _mk_creature("L1:0", "L1", (10, 10))
    c_10 = _mk_creature("L5:10", "L5", (11, 10))
    c_2 = _mk_creature("L5:2", "L5", (11, 10))
    c_1 = _mk_creature("L5:1", "L5", (11, 10))
    c_l1_1 = _mk_creature("L1:1", "L1", (11, 10))

    result = visible(seer, w, [c_10, c_2, c_1, c_l1_1, seer])
    assert [c.id for c in result] == ["L1:1", "L5:1", "L5:2", "L5:10"]


def test_empty_or_self_only_returns_empty() -> None:
    """Danh sách rỗng hoặc chỉ có chính mình trả về []."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    seer = _mk_creature("L1:0", "L1", (10, 10))
    assert visible(seer, w, []) == []
    assert visible(seer, w, [seer]) == []


def test_all_dead_returns_empty() -> None:
    """Tất cả con khác đều chết thì trả về []."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    seer = _mk_creature("L1:0", "L1", (10, 10))
    d1 = _mk_creature("L2:0", "L2", (11, 10), alive=False)
    d2 = _mk_creature("L3:0", "L3", (10, 11), alive=False)
    assert visible(seer, w, [seer, d1, d2]) == []

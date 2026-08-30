"""Tests cho genesis/world.py — lưới, địa hình, khoảng cách toroidal."""

from __future__ import annotations

import random
from collections import Counter

import pytest

from genesis import config
from genesis.world import TERRAIN_GLYPHS, Terrain, World

# Ba loại địa hình được bộ sinh rải; FIRE chỉ đến từ luật SPREAD.
GENERATED_TERRAINS = (Terrain.PLAIN, Terrain.WATER, Terrain.BUSH, Terrain.ROCK)


def test_terrain_enum() -> None:
    """Terrain enum có đúng 8 giá trị (5 gốc + DEEP, TREE, CAVE của W-18/W-19)."""
    assert Terrain.PLAIN == "PLAIN"
    assert Terrain.WATER == "WATER"
    assert Terrain.BUSH == "BUSH"
    assert Terrain.ROCK == "ROCK"
    assert Terrain.FIRE == "FIRE"
    assert Terrain.DEEP == "DEEP"
    assert Terrain.TREE == "TREE"
    assert Terrain.CAVE == "CAVE"
    # Tám, và **chỉ** tám. Ba kiểu nước của đề bài (ao / hồ / biển) sinh ra từ
    # CÁCH XẾP chứ không từ enum mới — `erode_cores` biến lõi mảng nước thành
    # DEEP và lõi khối đá thành CAVE. Thêm loại địa hình là thêm miền cho
    # `TERRAIN` trong DSL luật, mà quy nạp đang hỏng sẵn.
    assert len(Terrain) == 8


def test_acceptance_criteria() -> None:
    """Kiểm tra toàn bộ khẳng định trong mục nghiệm thu của phiếu việc."""
    w = World(config.GRID_W, config.GRID_H, random.Random(7))
    assert w.dist((0, 0), (23, 23)) == 1, w.dist((0, 0), (23, 23))
    assert w.dist((0, 0), (12, 12)) == 12, w.dist((0, 0), (12, 12))
    assert w.dist((0, 0), (0, 23)) == 1
    assert w.dist((5, 5), (5, 5)) == 0
    assert len(w.neighbors((0, 0))) == 8
    assert w.neighbors((5, 5)) == w.neighbors((5, 5))
    assert len(set(w.neighbors((5, 5)))) == 8

    c = Counter(w.grid[y][x] for y in range(24) for x in range(24))
    # FIRE không sinh tự nhiên (law_config.FIRE_BASE_SPREAD=False) — chỉ xuất hiện
    # khi có luật SPREAD. Chỉ kiểm ba loại địa hình ĐƯỢC SINH.
    assert all(c[t] >= 20 for t in GENERATED_TERRAINS), c
    assert c[Terrain.FIRE] == 0, "FIRE không được sinh tự nhiên"
    assert sum(c.values()) == 576

    # Tất định: cùng seed -> cùng bản đồ
    a = World(24, 24, random.Random(99)).grid
    b = World(24, 24, random.Random(99)).grid
    assert a == b


def test_toroidal_distance_both_axes() -> None:
    """B1: dist tính khoảng cách Chebyshev CÓ vòng mép ở cả hai chiều."""
    w = World(config.GRID_W, config.GRID_H, random.Random(0))
    # Vòng mép x: (0, 10) đến (23, 10) -> dx=1, dy=0 -> max=1
    assert w.dist((0, 10), (23, 10)) == 1
    # Vòng mép y: (10, 0) đến (10, 23) -> dx=0, dy=1 -> max=1
    assert w.dist((10, 0), (10, 23)) == 1
    # Vòng mép cả hai chiều
    assert w.dist((1, 1), (22, 22)) == 3
    assert w.dist((0, 0), (20, 20)) == 4


def test_non_toroidal_distance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Khi config.TOROIDAL = False, khoảng cách không vòng mép."""
    monkeypatch.setattr(config, "TOROIDAL", False)
    w = World(24, 24, random.Random(0))
    assert w.dist((0, 0), (23, 23)) == 23
    assert w.dist((0, 0), (0, 23)) == 23
    assert w.dist((0, 0), (23, 0)) == 23


def test_neighbors_fixed_order_and_count() -> None:
    """B2: neighbors trả về 8 ô theo đúng thứ tự cố định."""
    w = World(config.GRID_W, config.GRID_H, random.Random(0))
    pos = (10, 10)
    nbrs = w.neighbors(pos)
    expected = [
        (10, 9),   # N
        (11, 9),   # NE
        (11, 10),  # E
        (11, 11),  # SE
        (10, 11),  # S
        (9, 11),   # SW
        (9, 10),   # W
        (9, 9),    # NW
    ]
    assert nbrs == expected
    # Gọi nhiều lần luôn giữ nguyên thứ tự
    for _ in range(5):
        assert w.neighbors(pos) == expected


def test_neighbors_toroidal_wrapping() -> None:
    """B3: neighbors ở biên và góc wrap đúng khi TOROIDAL=True."""
    w = World(24, 24, random.Random(0))
    # Góc (0, 0)
    nbrs_origin = w.neighbors((0, 0))
    assert len(nbrs_origin) == 8
    assert nbrs_origin[0] == (0, 23)   # N
    assert nbrs_origin[1] == (1, 23)   # NE
    assert nbrs_origin[2] == (1, 0)    # E
    assert nbrs_origin[3] == (1, 1)    # SE
    assert nbrs_origin[4] == (0, 1)    # S
    assert nbrs_origin[5] == (23, 1)   # SW
    assert nbrs_origin[6] == (23, 0)   # W
    assert nbrs_origin[7] == (23, 23)  # NW


def test_wrap_and_neighbors_non_toroidal(monkeypatch: pytest.MonkeyPatch) -> None:
    """B3: khi config.TOROIDAL = False, wrap kẹp vào biên và neighbors chỉ trả ô trong lưới."""
    monkeypatch.setattr(config, "TOROIDAL", False)
    w = World(24, 24, random.Random(0))

    # wrap kẹp biên
    assert w.wrap(-5, 10) == (0, 10)
    assert w.wrap(30, 30) == (23, 23)

    # Góc (0, 0) chỉ có 3 ô hợp lệ: E(1,0), SE(1,1), S(0,1)
    corner_nbrs = w.neighbors((0, 0))
    assert corner_nbrs == [(1, 0), (1, 1), (0, 1)]

    # Cạnh (0, 10) chỉ có 5 ô hợp lệ
    edge_nbrs = w.neighbors((0, 10))
    assert len(edge_nbrs) == 5
    for nx, ny in edge_nbrs:
        assert 0 <= nx < 24 and 0 <= ny < 24


def test_passable() -> None:
    """W-18: `passable` trả lời cho MỘT con vật, không cho cả thế giới.

    `creature=None` nghĩa là "hỏi cho một sinh vật CẠN trung bình", nên nó đi
    được đúng ba ô: đất bằng, bụi, và nước NÔNG. Đá thì không ai qua; nước sâu
    dành cho tầng NƯỚC; cây và lửa đòi trait đủ ngưỡng mà `None` thì không có
    trait nào.
    """
    w = World(config.GRID_W, config.GRID_H, random.Random(7))
    walkable = {Terrain.PLAIN, Terrain.BUSH, Terrain.WATER}
    for y in range(w.h):
        for x in range(w.w):
            pos = (x, y)
            want = w.grid[y][x] in walkable
            assert w.passable(pos) is want
            assert w.passable(pos, creature=None) is want


def test_passable_theo_TRAIT_khong_theo_loai() -> None:
    """"Sư tử không trèo được cây, khỉ thì được" — và nó đọc VECTOR TRAIT.

    Không hard-code loài nào cả. Với `FOUNDERS` hiện tại, ngưỡng `CLIMB_SPEED`
    chia đàn đúng làm hai nhóm có thật, nên ổ sinh thái xuất hiện ngay với năm
    loài sẵn có — không cần thêm loài nào.
    """
    from genesis.creature import Creature
    from genesis.traits import founder_traits

    w = World(config.GRID_W, config.GRID_H, random.Random(7))
    tree = next(((x, y) for y in range(w.h) for x in range(w.w)
                 if w.grid[y][x] == Terrain.TREE), None)
    assert tree is not None, "seed này phải có ít nhất một ô cây"

    def make(sp):
        return Creature(id=f"{sp}:0", species=sp, traits=founder_traits(sp),
                        pos=(0, 0), hp=1.0, energy=1.0)

    khi = make("L5")     # speed 5 — trèo được
    su_tu = make("L2")   # speed 1, attack 4 — không trèo được
    assert w.passable(tree, khi) is True
    assert w.passable(tree, su_tu) is False


def test_terrain_patch_distribution_multiple_seeds() -> None:
    """Mỗi loại địa hình có ít nhất 20 ô trên lưới 24x24 qua nhiều seed khác nhau."""
    for seed in (0, 1, 7, 42, 99, 123, 2026, 9999):
        w = World(config.GRID_W, config.GRID_H, random.Random(seed))
        c = Counter(w.grid[y][x] for y in range(w.h) for x in range(w.w))
        assert all(c[t] >= 20 for t in GENERATED_TERRAINS), f"seed={seed}: {c}"
        assert sum(c.values()) == w.w * w.h


def test_glyph_mapping() -> None:
    """Ký tự hiển thị bản đồ đúng quy định."""
    assert TERRAIN_GLYPHS[Terrain.PLAIN] == "."
    assert TERRAIN_GLYPHS[Terrain.WATER] == "~"
    assert TERRAIN_GLYPHS[Terrain.BUSH] == '"'
    assert TERRAIN_GLYPHS[Terrain.ROCK] == "#"
    assert TERRAIN_GLYPHS[Terrain.FIRE] == "^"


def test_passable_wraps_out_of_range() -> None:
    """passable phải wrap trước khi lập chỉ mục.

    Hồi quy: bản đầu dùng thẳng self.grid[y][x], nên (-1,-1) lọt qua lập chỉ mục
    âm của Python và trả về ô góc đối diện, còn (24,24) ném IndexError.
    """
    w = World(24, 24, random.Random(7))
    assert w.passable((-1, -1)) == w.passable((23, 23))
    assert w.passable((24, 24)) == w.passable((0, 0))
    assert w.passable((-1, 5)) == w.passable((23, 5))
    assert w.passable((5, 30)) == w.passable((5, 6))


def test_terrain_constants_live_in_config() -> None:
    """MỌI hằng số nằm ở config.py — không rải rác nơi khác."""
    import genesis.world as world_mod
    assert not hasattr(world_mod, "TERRAIN_SEEDS_PER_TYPE")
    assert not hasattr(world_mod, "TERRAIN_WALK_STEPS")
    assert config.TERRAIN_SEEDS_PER_TYPE >= 1
    assert config.TERRAIN_WALK_STEPS >= 1

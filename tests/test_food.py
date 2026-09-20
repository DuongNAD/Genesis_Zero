"""Tests cho genesis/world.py — hệ thống thức ăn (plants, spawn_plants, eat_plant)."""

from __future__ import annotations

import random
import subprocess
import sys

from genesis import config
from genesis.world import PLANT_GLYPH, Terrain, World, spawn_plants


def test_acceptance_criteria() -> None:
    """Kiểm tra toàn bộ khẳng định trong mục nghiệm thu của phiếu việc."""
    w = World(config.GRID_W, config.GRID_H, random.Random(3))
    r = random.Random(3)
    grown = [spawn_plants(w, r, t) for t in range(100)]
    assert len(w.plants) == config.PLANT_MAX, len(w.plants)
    assert all(w.grid[y][x] == Terrain.PLAIN for (x, y) in w.plants)
    assert max(grown) <= config.PLANT_RESPAWN, max(grown)
    assert sum(grown) == config.PLANT_MAX, sum(grown)   # không mọc thừa rồi cắt
    assert grown[-1] == 0                                # đã đầy thì thôi

    # ăn
    pos = next(iter(w.plants))
    assert w.eat_plant(pos) == config.PLANT_ENERGY
    assert pos not in w.plants
    assert w.eat_plant(pos) == 0.0
    x, y = pos
    assert w.eat_plant((x + config.GRID_W, y + config.GRID_H)) == 0.0   # wrap, không IndexError

    # tất định
    def run(seed: int) -> list[tuple[int, int]]:
        ww = World(24, 24, random.Random(seed))
        rr = random.Random(seed)
        for t in range(50):
            spawn_plants(ww, rr, t)
        return sorted(ww.plants)

    assert run(9) == run(9)

    # bản đồ đầy -> trả 0, không treo
    full = World(24, 24, random.Random(1))
    for yy in range(24):
        for xx in range(24):
            if full.grid[yy][xx] == Terrain.PLAIN:
                full.plants[(xx, yy)] = "FRUIT_A"
    assert spawn_plants(full, random.Random(1), 0) == 0


def test_plants_dict_structure_and_ticks() -> None:
    """B1: plants là dict lưu vị trí -> lớp quả FRUIT_A..D."""
    w = World(config.GRID_W, config.GRID_H, random.Random(42))
    assert isinstance(w.plants, dict)
    assert len(w.plants) == 0

    r = random.Random(42)
    spawn_plants(w, r, tick=5)
    assert len(w.plants) == config.PLANT_RESPAWN
    assert all(cls in ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D") for cls in w.plants.values())

    spawn_plants(w, r, tick=12)
    assert len(w.plants) == config.PLANT_RESPAWN * 2
    assert all(cls in ("FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D") for cls in w.plants.values())


def test_plant_max_checked_each_spawn_step() -> None:
    """B2: Kiểm tra trần PLANT_MAX trước mỗi lần mọc, không vượt trần khi cận kề trần."""
    w = World(config.GRID_W, config.GRID_H, random.Random(10))
    r = random.Random(10)

    # Giả lập đã có PLANT_MAX - 1 cây
    plain_cells = [
        (x, y)
        for y in range(w.h)
        for x in range(w.w)
        if w.grid[y][x] == Terrain.PLAIN
    ]
    for i in range(config.PLANT_MAX - 1):
        w.plants[plain_cells[i]] = "FRUIT_A"

    assert len(w.plants) == config.PLANT_MAX - 1
    # Một lần gọi chỉ được mọc đúng 1 cây để đạt trần, không được mọc config.PLANT_RESPAWN cây
    count = spawn_plants(w, r, tick=1)
    assert count == 1
    assert len(w.plants) == config.PLANT_MAX

    # Lần gọi tiếp theo không mọc thêm cây nào
    assert spawn_plants(w, r, tick=2) == 0
    assert len(w.plants) == config.PLANT_MAX


def test_no_spawn_on_non_plain_or_occupied() -> None:
    """Cây chỉ mọc trên ô PLAIN trống, không mọc lên WATER/BUSH/ROCK hay ô đã có cây."""
    w = World(config.GRID_W, config.GRID_H, random.Random(77))
    r = random.Random(77)

    for t in range(20):
        spawn_plants(w, r, tick=t)

    for (x, y) in w.plants:
        assert w.grid[y][x] == Terrain.PLAIN


def test_eat_plant_wrapping_and_energy() -> None:
    """eat_plant wrap toạ độ đúng cách, trả đúng config.PLANT_ENERGY và xoá cây."""
    w = World(config.GRID_W, config.GRID_H, random.Random(5))
    r = random.Random(5)
    spawn_plants(w, r, tick=0)

    target_pos = next(iter(w.plants))
    tx, ty = target_pos

    # Ăn qua toạ độ lệch vòng mép (wrap)
    wrapped_pos = (tx + w.w * 3, ty - w.h * 2)
    energy = w.eat_plant(wrapped_pos)
    assert energy == float(config.PLANT_ENERGY)
    assert target_pos not in w.plants

    # Ăn lại ô vừa ăn trả 0.0
    assert w.eat_plant(target_pos) == 0.0
    assert w.eat_plant(wrapped_pos) == 0.0


def test_spawn_plants_no_plain_cells_terminates() -> None:
    """B6: Khi bản đồ không có ô PLAIN nào, spawn_plants trả 0 ngay và không treo."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    # Biến toàn bộ bản đồ thành ROCK
    for y in range(w.h):
        for x in range(w.w):
            w.grid[y][x] = Terrain.ROCK

    r = random.Random(1)
    assert spawn_plants(w, r, tick=0) == 0
    assert len(w.plants) == 0


def test_plant_glyph_and_print_map() -> None:
    """PLANT_GLYPH là '*' và lệnh --print-map in ra bản đồ có chứa '*'."""
    assert PLANT_GLYPH == "*"
    cmd = [sys.executable, "-m", "genesis.run", "--seed", "7", "--print-map"]
    res = subprocess.run(cmd, capture_output=True, encoding="utf-8", check=True)
    out = res.stdout
    assert "*" in out
    assert out.count("*") == config.PLANT_MAX
    lines = [line for line in out.splitlines() if line]
    assert len(lines) == config.GRID_H
    assert all(len(line) == config.GRID_W for line in lines)


def test_food_constants_in_config() -> None:
    """B4: Mọi hằng số lấy từ genesis/config.py."""
    import genesis.world as world_mod
    assert not hasattr(world_mod, "PLANT_ENERGY")
    assert not hasattr(world_mod, "PLANT_RESPAWN")
    assert not hasattr(world_mod, "PLANT_MAX")
    # KHÔNG khoá cứng giá trị: W-12 là mốc tune, config.py sẽ đổi vài chục lần.
    # Chỉ kiểm hằng số có mặt và quan hệ giữa chúng còn hợp lý.
    assert config.PLANT_ENERGY > 0
    assert 1 <= config.PLANT_RESPAWN <= config.PLANT_MAX
    assert config.PLANT_MAX < config.GRID_W * config.GRID_H

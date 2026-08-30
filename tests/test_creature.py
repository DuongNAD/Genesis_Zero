"""Genesis Zero — kiểm thử cho creature và vòng tick M0."""

from __future__ import annotations

import collections
import json
from pathlib import Path
import random

import pytest

from genesis import config
from genesis.creature import (
    Creature,
    random_step,
    spawn_population,
    upkeep_and_check_death,
)
from genesis.run import main
from genesis.traits import founder_traits
from genesis.world import Terrain, World


def test_creature_dataclass_fields() -> None:
    traits = founder_traits("L1")
    c = Creature(
        id="Sp:0",
        species="Sp",
        traits=traits,
        pos=(2, 3),
        hp=50.0,
        energy=100.0,
    )
    assert c.id == "Sp:0"
    assert c.species == "Sp"
    assert c.traits == traits
    assert c.pos == (2, 3)
    assert c.hp == 50.0
    assert c.energy == 100.0
    assert c.age == 0
    assert c.alive is True
    assert c.dead_until == -1


def test_spawn_population_basic() -> None:
    rng = random.Random(2)
    w = World(config.GRID_W, config.GRID_H, rng)
    cs = spawn_population(w, random.Random(2))

    total = sum(config.POPULATION.values())
    # Quần thể co theo môi trường sống của TỪNG loài (W-18 chặng B) — xem
    # `config.CELLS_PER_CREATURE`. Nói "không vượt quá" để bài kiểm còn đúng khi
    # ai đó đổi bản đồ mặc định.
    assert 0 < len(cs) <= total
    assert cs == sorted(cs, key=lambda c: c.id)
    # `passable(pos, c)` — hỏi CHO CON NÀY. Hỏi `passable(pos)` là hỏi cho một
    # sinh vật cạn trung bình, và với câu hỏi ấy thì mọi con cá đều "sai chỗ".
    assert all(w.passable(c.pos, c) for c in cs)
    assert all(c.energy == c.traits.energy_max for c in cs)
    assert all(c.hp == float(config.HP_MAX) for c in cs)
    assert len({c.id for c in cs}) == len(cs)

    # Khớp định dạng ID với config.POPULATION
    want_ids = sorted(f"{sp}:{i}" for sp, n in config.POPULATION.items() for i in range(n))
    assert [c.id for c in cs] == want_ids


def test_spawn_population_determinism() -> None:
    w1 = World(config.GRID_W, config.GRID_H, random.Random(8))
    w2 = World(config.GRID_W, config.GRID_H, random.Random(8))
    a = [c.pos for c in spawn_population(w1, random.Random(8))]
    b = [c.pos for c in spawn_population(w2, random.Random(8))]
    assert a == b


def test_spawn_population_dynamic_species(monkeypatch: pytest.MonkeyPatch) -> None:
    custom_pop = {"Alien": 2, "Mutant": 3}
    monkeypatch.setattr(config, "POPULATION", custom_pop)

    w = World(config.GRID_W, config.GRID_H, random.Random(10))
    cs = spawn_population(w, random.Random(10))

    assert len(cs) == 5
    want_ids = ["Alien:0", "Alien:1", "Mutant:0", "Mutant:1", "Mutant:2"]
    assert [c.id for c in cs] == want_ids
    assert [c.species for c in cs] == ["Alien", "Alien", "Mutant", "Mutant", "Mutant"]


def test_random_step_movement() -> None:
    w = World(config.GRID_W, config.GRID_H, random.Random(42))
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(5, 5),
        hp=float(config.HP_MAX),
        energy=traits.energy_max,
    )

    rng = random.Random(123)
    initial_energy = c.energy
    steps = random_step(c, w, rng)

    assert steps == c.traits.moves_per_tick
    assert c.energy == initial_energy - config.COST_MOVE * steps
    assert w.passable(c.pos)


def test_random_step_trapped() -> None:
    w = World(10, 10, random.Random(1))
    # Tạo bẫy toàn ROCK xung quanh (1, 1)
    for y in range(10):
        for x in range(10):
            w.grid[y][x] = Terrain.ROCK
    w.grid[1][1] = Terrain.PLAIN

    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(1, 1),
        hp=float(config.HP_MAX),
        energy=traits.energy_max,
    )
    rng = random.Random(99)
    steps = random_step(c, w, rng)
    assert steps == 0
    assert c.pos == (1, 1)
    assert c.energy == traits.energy_max


def test_random_step_dead_does_not_move() -> None:
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(5, 5),
        hp=float(config.HP_MAX),
        energy=50.0,
        alive=False,
    )
    rng = random.Random(1)
    steps = random_step(c, w, rng)
    assert steps == 0
    assert c.pos == (5, 5)
    assert c.energy == 50.0


def test_upkeep_and_death() -> None:
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(0, 0),
        hp=float(config.HP_MAX),
        energy=10.0,
    )

    # Còn năng lượng -> chưa chết
    just_died = upkeep_and_check_death(c, 1)
    assert just_died is False
    assert c.alive is True
    assert c.energy == 10.0 - c.traits.upkeep
    assert c.age == 1

    # Năng lượng về <= 0 -> chết
    c.energy = 0.1
    just_died = upkeep_and_check_death(c, 2)
    assert just_died is True
    assert c.alive is False
    assert c.energy == 0.1 - c.traits.upkeep
    assert c.age == 2

    # Đã chết -> gọi lại không chết lần hai
    just_died_again = upkeep_and_check_death(c, 3)
    assert just_died_again is False
    assert c.alive is False


def test_creature_death_stays_in_list() -> None:
    w = World(config.GRID_W, config.GRID_H, random.Random(2))
    cs = spawn_population(w, random.Random(2))
    c0 = cs[0]
    c0.energy = 0.1
    assert upkeep_and_check_death(c0, 1) is True and c0.alive is False
    assert cs[0] is c0 and len(cs) == sum(config.POPULATION.values())
    assert upkeep_and_check_death(c0, 2) is False


def test_starvation_without_food() -> None:
    """W-04: KHÔNG có thức ăn thì sinh vật chết đói đúng lịch.

    Đây mới là hợp đồng thật của W-04. Bản trước kiểm nó qua một lần chạy đầy đủ
    và khẳng định "15 con chết hết, không hồi sinh" — đúng ở W-04 nhưng SAI ngay
    khi W-05 thêm ăn và hồi sinh. Kiểm ở mức đơn vị thì hợp đồng đứng vững qua
    mọi mốc sau.
    """
    w = World(config.GRID_W, config.GRID_H, random.Random(5))
    cs = spawn_population(w, random.Random(5))
    rng = random.Random(5)
    died_at: dict[str, int] = {}
    for tick in range(60):
        w.plants.clear()                      # thế giới không có gì ăn
        for c in cs:
            if not c.alive:
                continue
            random_step(c, w, rng)
            if upkeep_and_check_death(c, tick):
                died_at[c.id] = tick

    assert len(died_at) == len(cs)            # chết hết
    for c in cs:
        budget = c.traits.energy_max / (c.traits.upkeep + config.COST_MOVE * c.traits.moves_per_tick)
        assert abs(died_at[c.id] - budget) < 5, (c.id, died_at[c.id], budget)


def test_run_is_independent_of_output_filename(tmp_path: Path) -> None:
    """Cùng seed + cùng tham số phải cho CÙNG thế giới, bất kể tên file.

    Hồi quy: một bản trước dò chuỗi "w04" trong đường dẫn output rồi tắt ăn/xác/
    hồi sinh để test cũ khỏi đỏ. Cùng seed cho hai thế giới khác hẳn nhau — phá
    tận gốc bất biến tái lập của cả dự án.
    """
    a = tmp_path / "plain.jsonl"
    b = tmp_path / "w04_w05_test.jsonl"
    main(["--seed", "11", "--ticks", "80", "--no-render", "--out", str(a)])
    main(["--seed", "11", "--ticks", "80", "--no-render", "--out", str(b)])
    ra = [json.loads(l) for l in a.read_text(encoding="utf-8").splitlines() if l.strip()]
    rb = [json.loads(l) for l in b.read_text(encoding="utf-8").splitlines() if l.strip()]
    ka = collections.Counter(r["kind"] for r in ra)
    kb = collections.Counter(r["kind"] for r in rb)
    assert ka == kb, (ka, kb)
    assert ka["EAT"] > 0 and ka["RESPAWN"] > 0


def test_id_sort_key_survives_double_digits(monkeypatch: pytest.MonkeyPatch) -> None:
    """B4: thứ tự duyệt phải đúng cả khi một loài có hơn 9 con.

    Hồi quy: bản đầu sắp bằng chuỗi id, nên "L5:10" rơi vào giữa "L5:1" và
    "L5:2". Thứ tự duyệt đổi -> ván đổi -> mất tính tái lập, không báo lỗi.
    """
    from genesis.creature import creature_sort_key

    monkeypatch.setattr(config, "POPULATION", {"Sw": 12})
    w = World(config.GRID_W, config.GRID_H, random.Random(4))
    cs = spawn_population(w, random.Random(4))

    assert [c.id for c in cs] == [f"Sw:{i}" for i in range(12)]
    # và sắp bằng chuỗi thì KHÔNG cho kết quả đó -> test này có ý nghĩa
    assert sorted((c.id for c in cs)) != [f"Sw:{i}" for i in range(12)]
    # khoá dùng được cho hai loài lẫn nhau
    dummy_traits = founder_traits("Ax")
    assert creature_sort_key(Creature("Ax:2", "Ax", dummy_traits, (0, 0), 1.0, 1.0)) == ("Ax", 2)
    assert creature_sort_key(Creature("Ax:10", "Ax", dummy_traits, (0, 0), 1.0, 1.0)) == ("Ax", 10)


"""Genesis Zero — kiểm thử vòng đời sinh vật: ăn, chết, xác, phân huỷ, hồi sinh (W-05)."""

from __future__ import annotations

import collections
import json
import random
from pathlib import Path

from genesis import config
from genesis.creature import (
    Creature,
    creature_sort_key,
    kill,
    resolve_eat,
    spawn_population,
    try_respawn,
)

# `_resolve_eating` sống ở `genesis.tick`. Bản cũ nhập nó qua `genesis.run` —
# chạy được, vì `run` tình cờ có nhập nó — nhưng đó là một re-export tình cờ,
# và `ruff --fix` xoá đúng nó vì `run` không dùng tới. Nhập từ chỗ nó thật sự ở.
from genesis.run import main
from genesis.tick import _resolve_eating
from genesis.traits import founder_traits
from genesis.world import (
    CORPSE_GLYPH,
    PLANT_GLYPH,
    World,
    decay_corpses,
)


def test_corpse_constants_and_init() -> None:
    """Kiểm tra khởi tạo corpses trong World và CORPSE_GLYPH."""
    assert CORPSE_GLYPH == "x"
    assert PLANT_GLYPH == "*"
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    assert isinstance(w.corpses, dict)
    assert len(w.corpses) == 0


def test_resolve_eat_basic() -> None:
    """resolve_eat ăn cây, tăng năng lượng và xoá cây khỏi world."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(5, 5),
        hp=float(config.HP_MAX),
        energy=50.0,
    )
    # Không có cây -> trả về 0.0, năng lượng giữ nguyên
    assert resolve_eat(c, w) == 0.0
    assert c.energy == 50.0

    # Đặt cây tại ô của c
    w.plants[(5, 5)] = "FRUIT_A"
    gained = resolve_eat(c, w)
    assert gained == float(config.PLANT_ENERGY)
    assert c.energy == 50.0 + config.PLANT_ENERGY
    assert (5, 5) not in w.plants

    # Ăn lại ô vừa ăn -> 0.0
    assert resolve_eat(c, w) == 0.0


def test_resolve_eat_dead_creature() -> None:
    """Sinh vật chết không thể ăn."""
    w = World(config.GRID_W, config.GRID_H, random.Random(1))
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(5, 5),
        hp=0.0,
        energy=0.0,
        alive=False,
    )
    w.plants[(5, 5)] = "FRUIT_A"
    assert resolve_eat(c, w) == 0.0
    assert c.energy == 0.0
    assert (5, 5) in w.plants


def test_food_conflict_determinism() -> None:
    """B1: Hai con cùng ô có cây, hoán vị list phải cho kết quả y hệt."""
    w = World(24, 24, random.Random(1))
    cs = spawn_population(w, random.Random(1))
    a, b = cs[0], cs[-1]
    assert creature_sort_key(a) < creature_sort_key(b)
    cell = a.pos
    w.plants.clear()
    w.plants[cell] = "FRUIT_A"
    b.pos = cell
    # Phải rút bớt năng lượng: sinh vật mới sinh đã ở trần nên ăn không tăng gì.
    a.energy = b.energy = a.traits.energy_max / 2
    e0 = (a.energy, b.energy)

    # Thứ tự NGƯỢC
    _resolve_eating(w, [b, a], None, 0)
    r1 = (a.energy, b.energy)

    # Khôi phục và chạy thứ tự XUÔI
    a.energy, b.energy = e0
    w.plants[cell] = "FRUIT_A"
    _resolve_eating(w, [a, b], None, 0)

    assert r1 == (a.energy, b.energy), (r1, (a.energy, b.energy))
    assert a.energy > b.energy  # id nhỏ hơn được ăn
    assert cell not in w.plants  # cây bị ăn đúng một lần


def test_kill_and_decay_corpses() -> None:
    """Xác sinh ra khi kill và phân huỷ đúng hạn theo config.CORPSE_DECAY."""
    w = World(24, 24, random.Random(2))
    c = spawn_population(w, random.Random(2))[0]
    kill(c, w, tick=10, cause="starve")

    assert c.pos in w.corpses
    assert c.alive is False
    assert c.dead_until == 10 + config.RESPAWN_DELAY

    # Chưa đủ thời gian phân huỷ
    assert decay_corpses(w, 10 + config.CORPSE_DECAY - 1) == 0
    assert c.pos in w.corpses

    # Quá hạn phân huỷ -> xoá xác
    assert decay_corpses(w, 10 + config.CORPSE_DECAY + 1) == 1
    assert not w.corpses


def test_try_respawn_timing_and_state() -> None:
    """try_respawn chỉ hồi sinh khi đủ RESPAWN_DELAY, reset age=0 nhưng giữ nguyên id."""
    w = World(24, 24, random.Random(3))
    c = spawn_population(w, random.Random(3))[0]
    orig_id = c.id
    c.age = 15
    kill(c, w, tick=10, cause="starve")

    rng = random.Random(42)
    # Chưa đủ RESPAWN_DELAY
    assert try_respawn(c, w, 10 + config.RESPAWN_DELAY - 1, rng) is False
    assert c.alive is False

    # Đủ thời gian -> hồi sinh
    assert try_respawn(c, w, 10 + config.RESPAWN_DELAY, rng) is True
    assert c.alive is True
    assert c.id == orig_id
    assert c.age == 0
    assert c.hp == float(config.HP_MAX)
    assert c.dead_until == -1
    assert c.energy == config.RESPAWN_ENERGY_RATIO * c.traits.energy_max
    assert w.passable(c.pos)

    # Đã sống lại -> gọi tiếp trả False
    assert try_respawn(c, w, 10 + config.RESPAWN_DELAY + 1, rng) is False


def test_acceptance_run_scenario_300_ticks(tmp_path: Path, monkeypatch) -> None:
    """Kiểm tra kịch bản nghiệm thu 300 tick: DEATH, RESPAWN, EAT đều xảy ra, quần thể ổn định."""
    monkeypatch.setattr(config, "REPRODUCTION_ENABLED", False)
    out_file = tmp_path / "w05.jsonl"
    main(["--seed", "11", "--ticks", "300", "--no-render", "--out", str(out_file)])

    rows = [json.loads(l) for l in out_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    k = collections.Counter(r["kind"] for r in rows)
    total = sum(config.POPULATION.values())

    assert k["DEATH"] > 0 and k["RESPAWN"] > 0 and k["EAT"] > 0, k

    # Quần thể LUÔN đúng 15 con, không con nào biến mất
    ids = {r["creature_id"] for r in rows if r.get("creature_id")}
    assert len(ids) == total, (len(ids), total)

    # Hồi sinh đúng RESPAWN_DELAY tick sau khi chết
    d: dict[str, int] = {}
    ok = 0
    for r in rows:
        if r["kind"] == "DEATH":
            d[r["creature_id"]] = r["t"]
        elif r["kind"] == "RESPAWN" and r["creature_id"] in d:
            assert r["t"] - d.pop(r["creature_id"]) >= config.RESPAWN_DELAY
            ok += 1
    assert ok > 0

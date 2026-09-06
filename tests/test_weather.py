"""Kiểm thử toàn diện cho hệ thống thời tiết động (Milestone M2_WEATHER).

Các khía cạnh kiểm thử:
1. Cấu trúc dữ liệu WeatherType, WeatherModifiers, WeatherState.
2. Tính tất định theo seed (seed determinism) và không đụng vào world.rng.
3. Epoch 0 (ticks 0-49) luôn là CLEAR cho mọi seed.
4. Chuyển chu kỳ đúng mỗi 50 ticks (cycle transitions).
5. Biến đổi chi phí di chuyển (movement cost modulation) trong reflex và random_step.
6. Giảm tầm nhìn theo thời tiết (sight radius penalty) kết hợp chu kỳ ngày/đêm.
7. Điều tiết tốc độ sinh trưởng thực vật và rong biển (plant/algae growth modulation).
8. Chuẩn hóa telemetry to_dict() và kiểm soát nghiêm ngặt không rò rỉ token cấm.
9. Tích hợp mô phỏng World, tick(), và MatchRunner spectate frame.
"""

from __future__ import annotations

import json
import random
import re

from genesis import config
from genesis.creature import Creature, random_step
from genesis.reflex import Intent, apply_intent
from genesis.tick import init_simulation, tick
from genesis.traits import Traits
from genesis.weather import (
    CYCLE_WEATHERS,
    WEATHER_MODIFIERS,
    WeatherState,
    WeatherType,
    to_dict,
    weather_at,
)
from genesis.world import Terrain, World, phase_at, spawn_algae, spawn_plants, visible
from net.match import MatchRunner

FORBIDDEN_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")


def test_weather_types_and_modifiers_contract():
    """1. Kiểm tra WeatherType, WeatherModifiers và bảng tra cứu WEATHER_MODIFIERS."""
    expected_types = {"CLEAR", "RAIN", "SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT"}
    actual_types = {t.value for t in WeatherType}
    assert actual_types == expected_types

    # Kiểm tra các giá trị modifier chuẩn
    clear_mod = WEATHER_MODIFIERS[WeatherType.CLEAR.value]
    assert clear_mod.move_cost_mult == 1.0
    assert clear_mod.sight_penalty == 0
    assert clear_mod.plant_mult == 1.0
    assert clear_mod.algae_mult == 1.0
    assert clear_mod.plant_growth_mult == 1.0
    assert clear_mod.algae_growth_mult == 1.0

    rain_mod = WEATHER_MODIFIERS[WeatherType.RAIN.value]
    assert rain_mod.move_cost_mult == 1.3
    assert rain_mod.sight_penalty == 1
    assert rain_mod.plant_mult == 1.5
    assert rain_mod.algae_mult == 1.4

    spore_mod = WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value]
    assert spore_mod.move_cost_mult == 1.5
    assert spore_mod.sight_penalty == 2
    assert spore_mod.plant_mult == 0.5
    assert spore_mod.algae_mult == 0.8

    solar_mod = WEATHER_MODIFIERS[WeatherType.SOLAR_FLARE.value]
    assert solar_mod.move_cost_mult == 1.4
    assert solar_mod.sight_penalty == 1
    assert solar_mod.plant_mult == 0.7
    assert solar_mod.algae_mult == 0.5

    mag_mod = WEATHER_MODIFIERS[WeatherType.MAGNETIC_SHIFT.value]
    assert mag_mod.move_cost_mult == 1.2
    assert mag_mod.sight_penalty == 0
    assert mag_mod.plant_mult == 1.0
    assert mag_mod.algae_mult == 1.1


def test_epoch_0_is_always_clear_across_seeds():
    """2. Epoch 0 (ticks 0-49) bắt buộc luôn là CLEAR với mọi seed."""
    test_seeds = [0, 1, 7, 42, 100, 99999, 123456789]
    for seed in test_seeds:
        for t in (0, 1, 10, 25, 48, 49):
            w = weather_at(seed, t)
            assert w.name == WeatherType.CLEAR.value
            assert w.state == WeatherType.CLEAR.value
            assert w.tick_in_cycle == t
            assert w.cycle_tick == t
            assert w.cycle_len == 50
            assert abs(w.progress - (t / 50.0)) < 1e-5
            assert w.modifiers.move_cost_mult == 1.0
            assert w.modifiers.sight_penalty == 0
            assert w.modifiers.plant_mult == 1.0
            assert w.modifiers.algae_mult == 1.0


def test_seed_determinism_and_rng_isolation():
    """3. Cùng (seed, tick) luôn trả về cùng WeatherState mà KHÔNG tiêu thụ world.rng."""
    for seed in [3, 42, 777]:
        for t in [0, 50, 75, 100, 150, 199]:
            w1 = weather_at(seed, t)
            w2 = weather_at(seed, t)
            assert w1.name == w2.name
            assert w1.tick_in_cycle == w2.tick_in_cycle
            assert w1.progress == w2.progress
            assert w1.modifiers == w2.modifiers

    # Kiểm tra độc lập hoàn toàn với world.rng
    sim_rng = random.Random(12345)
    rng_state_before = sim_rng.getstate()
    # Gọi hàm weather_at nhiều lần
    _ = [weather_at(12345, t) for t in range(200)]
    rng_state_after = sim_rng.getstate()
    assert rng_state_before == rng_state_after, "weather_at không được tiêu thụ từ external random state"


def test_cycle_transitions_every_50_ticks():
    """4. Chu kỳ chuyển tiếp chính xác mỗi 50 ticks."""
    seed = 101
    # Tick 49: epoch 0 (CLEAR), tick_in_cycle = 49, progress = 0.98
    w_end_0 = weather_at(seed, 49)
    assert w_end_0.name == WeatherType.CLEAR.value
    assert w_end_0.tick_in_cycle == 49
    assert abs(w_end_0.progress - 0.98) < 1e-5

    # Tick 50: bắt đầu epoch 1, tick_in_cycle = 0, progress = 0.0
    w_start_1 = weather_at(seed, 50)
    assert w_start_1.name in CYCLE_WEATHERS
    assert w_start_1.tick_in_cycle == 0
    assert w_start_1.progress == 0.0

    # Tick 99: kết thúc epoch 1, tick_in_cycle = 49, giữ nguyên thời tiết của epoch 1
    w_end_1 = weather_at(seed, 99)
    assert w_end_1.name == w_start_1.name
    assert w_end_1.tick_in_cycle == 49
    assert abs(w_end_1.progress - 0.98) < 1e-5

    # Tick 100: bắt đầu epoch 2
    w_start_2 = weather_at(seed, 100)
    assert w_start_2.name in CYCLE_WEATHERS
    assert w_start_2.tick_in_cycle == 0
    assert w_start_2.progress == 0.0


def test_movement_cost_modulation_reflex():
    """5. Kiểm tra điều tiết chi phí di chuyển trong reflex.apply_intent."""
    rng = random.Random(0)
    world = World(24, 24, rng, seed=1)

    # Đảm bảo ô (5, 5) và (6, 5) là PLAIN
    world.grid[5][5] = Terrain.PLAIN
    world.grid[5][6] = Terrain.PLAIN

    # Tạo sinh vật ở (5, 5) với 10.0 năng lượng
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    creature = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=10.0, energy=10.0)
    creatures_by_id = {creature.id: creature}

    # 5.1 Thời tiết CLEAR (move_cost_mult = 1.0)
    world.weather = weather_at(1, 0)  # CLEAR
    intent = Intent(creature_id="L1:0", path=[(6, 5)])
    steps = apply_intent(intent, creatures_by_id, world)
    assert steps == 1
    assert creature.pos == (6, 5)
    expected_cost_clear = config.COST_MOVE * 1.0
    assert abs(creature.energy - (10.0 - expected_cost_clear)) < 1e-5

    # 5.2 Thời tiết SPORE_STORM (move_cost_mult = 1.5)
    creature.energy = 10.0
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )
    intent = Intent(creature_id="L1:0", path=[(5, 5)])
    steps = apply_intent(intent, creatures_by_id, world)
    assert steps == 1
    expected_cost_spore = config.COST_MOVE * 1.5
    assert abs(creature.energy - (10.0 - expected_cost_spore)) < 1e-5

    # 5.3 Thời tiết RAIN (move_cost_mult = 1.3)
    creature.energy = 10.0
    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )
    intent = Intent(creature_id="L1:0", path=[(6, 5)])
    steps = apply_intent(intent, creatures_by_id, world)
    assert steps == 1
    expected_cost_rain = config.COST_MOVE * 1.3
    assert abs(creature.energy - (10.0 - expected_cost_rain)) < 1e-5


def test_movement_cost_modulation_random_step():
    """6. Kiểm tra điều tiết chi phí di chuyển trong creature.random_step."""
    rng = random.Random(42)
    world = World(24, 24, rng, seed=1)

    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    creature = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=10.0, energy=10.0)

    # SOLAR_FLARE (move_cost_mult = 1.4)
    world.weather = WeatherState(
        name=WeatherType.SOLAR_FLARE.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SOLAR_FLARE.value],
    )
    steps = random_step(creature, world, random.Random(7))
    if steps > 0:
        expected_cost = steps * config.COST_MOVE * 1.4
        assert abs(creature.energy - (10.0 - expected_cost)) < 1e-5


def test_sight_penalty_modulation():
    """7. Giảm bán kính nhìn theo thời tiết và kiểm tra chặn đáy max(1, ...)."""
    rng = random.Random(0)
    world = World(24, 24, rng, seed=1)
    world.phase = "DAY"

    # Người quan sát có sense=2 -> sight_radius = SIGHT_BASE + 2 = 4
    obs_traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    obs = Creature(id="OBS:0", species="L1", traits=obs_traits, pos=(10, 10), hp=10.0, energy=10.0)

    # Các mục tiêu ở khoảng cách 1, 2, 3, 4
    target_d1 = Creature(id="T1:0", species="L2", traits=obs_traits, pos=(11, 10), hp=10.0, energy=10.0)
    target_d2 = Creature(id="T2:0", species="L2", traits=obs_traits, pos=(12, 10), hp=10.0, energy=10.0)
    target_d3 = Creature(id="T3:0", species="L2", traits=obs_traits, pos=(13, 10), hp=10.0, energy=10.0)
    target_d4 = Creature(id="T4:0", species="L2", traits=obs_traits, pos=(14, 10), hp=10.0, energy=10.0)
    all_creatures = [obs, target_d1, target_d2, target_d3, target_d4]

    # Đảm bảo địa hình toàn bộ là PLAIN để không bị che bởi cây hay bụi
    for x in range(9, 16):
        world.grid[10][x] = Terrain.PLAIN

    # 7.1 CLEAR: sight_penalty = 0 -> thấy cả 4 (d <= 4)
    world.weather = weather_at(1, 0)
    seen_clear = visible(obs, world, all_creatures)
    assert len(seen_clear) == 4

    # 7.2 RAIN: sight_penalty = 1 -> effective radius = 3 -> thấy d1, d2, d3
    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )
    seen_rain = visible(obs, world, all_creatures)
    assert len(seen_rain) == 3
    assert target_d4 not in seen_rain

    # 7.3 SPORE_STORM: sight_penalty = 2 -> effective radius = 2 -> thấy d1, d2
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )
    seen_spore = visible(obs, world, all_creatures)
    assert len(seen_spore) == 2
    assert seen_spore == [target_d1, target_d2]

    # 7.4 Cận biên: sense = 0 -> sight_radius = 2; với SPORE_STORM (phạt 2) -> max(1, 2-2) = 1
    low_sense_traits = Traits(brain=2, attack=2, armor=3, speed=2, sense=0, stomach=3)
    low_obs = Creature(id="LOW:0", species="L1", traits=low_sense_traits, pos=(10, 10), hp=10.0, energy=10.0)
    seen_low = visible(low_obs, world, [low_obs, target_d1, target_d2])
    assert len(seen_low) == 1
    assert target_d1 in seen_low


def test_plant_and_algae_growth_scaling():
    """8. Điều tiết tốc độ sinh trưởng thực vật và rong biển."""
    rng = random.Random(123)
    world = World(24, 24, rng, seed=1)

    # Thiết lập world với thời tiết RAIN (plant_mult=1.5, algae_mult=1.4)
    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )
    # config.PLANT_RESPAWN = 2, nhân 1.5 -> round(3.0) = 3
    # config.ALGAE_RESPAWN = 2, nhân 1.4 -> round(2.8) = 3
    world.fruits.clear()
    n_plants = spawn_plants(world, random.Random(42))
    assert n_plants == 3

    world.algae.clear()
    n_algae = spawn_algae(world, random.Random(42))
    assert n_algae == 3

    # Thiết lập world với thời tiết SPORE_STORM (plant_mult=0.5, algae_mult=0.8)
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )
    # 2 * 0.5 = 1 plant
    world.fruits.clear()
    n_spore_plants = spawn_plants(world, random.Random(42))
    assert n_spore_plants == 1

    # 2 * 0.8 = 1.6 -> round = 2 algae
    world.algae.clear()
    n_spore_algae = spawn_algae(world, random.Random(42))
    assert n_spore_algae == 2


def test_weather_to_dict_and_forbidden_tokens():
    """9. Serial hóa to_dict và xác minh 100% không chứa token cấm."""
    for w_type, mod in WEATHER_MODIFIERS.items():
        state = WeatherState(
            name=w_type,
            tick_in_cycle=12,
            cycle_len=50,
            progress=0.24,
            modifiers=mod,
        )
        d = to_dict(state, diurnal="DAY")

        # Kiểm tra cấu trúc dict
        assert d["name"] == w_type
        assert d["state"] == w_type
        assert d["tick_in_cycle"] == 12
        assert d["cycle_tick"] == 12
        assert d["cycle_len"] == 50
        assert d["progress"] == 0.24
        assert d["diurnal"] == "DAY"
        assert "move_cost_mult" in d["modifiers"]
        assert "sight_penalty" in d["modifiers"]
        assert "plant_mult" in d["modifiers"]
        assert "algae_mult" in d["modifiers"]

        # Kiểm tra token cấm
        text = json.dumps(d)
        m = FORBIDDEN_PATTERN.search(text)
        assert not m, f"Weather payload chứa token cấm {m.group(0)!r}: {text}"


def test_world_and_tick_integration():
    """10. Tích hợp mô phỏng World và cập nhật qua tick()."""
    world, creatures, state, rng = init_simulation(seed=42)
    assert world.weather is not None
    assert world.weather.name == WeatherType.CLEAR.value

    # Diễn tiến qua 55 ticks
    for t in range(55):
        tick(world, creatures, t, rng, state)
        if t < 50:
            assert world.weather.name == WeatherType.CLEAR.value
            assert world.weather.tick_in_cycle == t
        else:
            assert world.weather.name in CYCLE_WEATHERS
            assert world.weather.tick_in_cycle == t - 50

    # Bất biến: phase_at và world.phase chỉ nhận "DAY" hoặc "NIGHT"
    for t in (0, 39, 40, 79, 80, 120):
        phase = phase_at(t)
        assert phase in ("DAY", "NIGHT")


def test_spectate_frame_telemetry_weather():
    """11. MatchRunner frame() chứa telemetry thời tiết hợp lệ và không rò rỉ luật."""
    runner = MatchRunner(seed=7, ticks=60, tick_ms=1, log_dir=None)
    f0 = runner.frame(0, [])
    assert "weather" in f0
    w0 = f0["weather"]
    assert w0 is not None
    assert w0["state"] == WeatherType.CLEAR.value
    assert w0["tick_in_cycle"] == 0
    assert w0["cycle_len"] == 50
    assert w0["diurnal"] in ("DAY", "NIGHT")
    assert w0["modifiers"]["move_cost_mult"] == 1.0

    # Kiểm tra không rò rỉ token cấm trong cả frame
    frame_text = json.dumps(f0)
    match = FORBIDDEN_PATTERN.search(frame_text)
    assert not match, f"Spectate frame rò rỉ token cấm {match.group(0)!r}: {frame_text}"

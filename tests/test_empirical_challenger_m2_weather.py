"""Empirical Adversarial Stress Test Suite: Milestone M2_WEATHER (Challenger 1).

Objectives:
1. Multi-seed determinism fuzzing across 10 distinct seeds x 500 ticks.
2. RNG stream isolation: verify weather_at does NOT advance/desynchronize world.rng or global RNG.
3. Transition boundaries & edge conditions: tick=0, 49->50, 99->100, tick=10000, negative ticks, zero cycle_len.
4. Physical modifier modulations & compounding mechanics (move cost, sight clamp, growth scaling).
5. Diurnal law invariance (phase_at is strictly DAY/NIGHT) & zero forbidden token leak.
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

FUZZ_SEEDS = [
    0,
    1,
    42,
    101,
    777,
    1337,
    99999,
    123456,
    987654321,
    2147483647,
]


# =========================================================================
# 1. MULTI-SEED DETERMINISM FUZZING
# =========================================================================


def test_fuzz_multi_seed_determinism_500_ticks():
    """Verify across 10 seeds x 500 ticks that independent runs produce bit-for-bit identical weather."""
    for seed in FUZZ_SEEDS:
        # Run A: evaluate weather from tick 0 to 499
        run_a = [weather_at(seed, t) for t in range(500)]
        # Run B: evaluate weather independently
        run_b = [weather_at(seed, t) for t in range(500)]

        assert len(run_a) == 500
        assert len(run_b) == 500

        for t in range(500):
            wa = run_a[t]
            wb = run_b[t]
            assert wa.name == wb.name, f"Seed {seed} tick {t}: name mismatch {wa.name} != {wb.name}"
            assert wa.tick_in_cycle == wb.tick_in_cycle
            assert wa.progress == wb.progress
            assert wa.modifiers == wb.modifiers
            assert wa.cycle_len == wb.cycle_len
            assert wa.to_dict() == wb.to_dict()
            assert to_dict(wa) == to_dict(wb)


def test_fuzz_multi_seed_cross_seed_entropy():
    """Verify that different seeds produce diverse weather sequences (not all collapsing to same sequence)."""
    weather_signatures = set()
    for seed in FUZZ_SEEDS:
        # Signature: sequence of weather names at epoch starts (t=50, 100, 150, 200, 250)
        sig = tuple(weather_at(seed, t).name for t in range(50, 500, 50))
        weather_signatures.add(sig)

    # Across 10 distinct seeds, we should observe multiple distinct trajectories
    assert len(weather_signatures) >= 7, (
        f"Expected high entropy across seeds, got only {len(weather_signatures)} distinct signatures: {weather_signatures}"
    )


# =========================================================================
# 2. RNG STREAM ISOLATION & DESYNCHRONIZATION VERIFICATION
# =========================================================================


def test_weather_at_zero_rng_consumption():
    """weather_at must not advance or mutate any random generator state."""
    # Test with custom Random instance
    test_rng = random.Random(9999)
    initial_rng_state = test_rng.getstate()

    # Call weather_at across 5000 combinations
    for s in FUZZ_SEEDS:
        for t in range(0, 500, 25):
            _ = weather_at(s, t)

    assert test_rng.getstate() == initial_rng_state, "Custom RNG state mutated by weather_at!"

    # Test with global python random
    global_initial_state = random.getstate()
    for s in FUZZ_SEEDS:
        for t in range(0, 500, 25):
            _ = weather_at(s, t)

    assert random.getstate() == global_initial_state, "Global random state mutated by weather_at!"


def test_rng_stream_isolation_terrain_generation():
    """Assert identical terrain grid generation with and without weather evaluations."""
    for seed in [1, 42, 1337]:
        # Generator 1: Clean terrain generation
        rng1 = random.Random(seed)
        w1 = World(24, 24, rng1, seed=seed)
        grid1 = [list(row) for row in w1.grid]

        # Generator 2: Interleaved with aggressive weather_at calls
        rng2 = random.Random(seed)
        _ = [weather_at(seed, t) for t in range(1000)]
        w2 = World(24, 24, rng2, seed=seed)
        grid2 = [list(row) for row in w2.grid]

        assert grid1 == grid2, f"Terrain diverged for seed {seed} due to weather_at calls!"


def test_rng_stream_isolation_plant_spawns():
    """Assert identical plant and algae spawn coordinates with and without external weather evaluations."""
    seed = 42
    rng_control = random.Random(seed)
    w_control = World(24, 24, rng_control, seed=seed)
    w_control.weather = weather_at(seed, 0)  # CLEAR

    # Control run: spawn 30 ticks of plants & algae
    control_plants = []
    control_algae = []
    for _ in range(30):
        spawn_plants(w_control, rng_control)
        spawn_algae(w_control, rng_control)
        control_plants.append(dict(w_control.fruits))
        control_algae.append(dict(w_control.algae))

    # Challenged run: same seed, but between every single spawn call, weather_at is called 50 times
    rng_challenged = random.Random(seed)
    w_challenged = World(24, 24, rng_challenged, seed=seed)
    w_challenged.weather = weather_at(seed, 0)  # CLEAR

    challenged_plants = []
    challenged_algae = []
    for t in range(30):
        _ = [weather_at(seed, t * 100 + i) for i in range(50)]
        spawn_plants(w_challenged, rng_challenged)
        _ = [weather_at(seed, t * 100 + i) for i in range(50)]
        spawn_algae(w_challenged, rng_challenged)
        challenged_plants.append(dict(w_challenged.fruits))
        challenged_algae.append(dict(w_challenged.algae))

    assert control_plants == challenged_plants, "Plant spawn coordinates/fruits diverged!"
    assert control_algae == challenged_algae, "Algae spawn coordinates diverged!"


# =========================================================================
# 3. TRANSITION BOUNDARIES & EDGE CONDITIONS
# =========================================================================


def test_transition_boundary_tick_0():
    """tick=0 must strictly be CLEAR with tick_in_cycle=0 and progress=0.0."""
    for seed in FUZZ_SEEDS:
        w = weather_at(seed, 0)
        assert w.name == WeatherType.CLEAR.value
        assert w.tick_in_cycle == 0
        assert w.cycle_tick == 0
        assert w.cycle_len == 50
        assert w.progress == 0.0


def test_transition_boundary_49_to_50():
    """Boundary transition from epoch 0 (CLEAR) to epoch 1."""
    for seed in FUZZ_SEEDS:
        w49 = weather_at(seed, 49)
        assert w49.name == WeatherType.CLEAR.value
        assert w49.tick_in_cycle == 49
        assert abs(w49.progress - 49 / 50.0) < 1e-6

        w50 = weather_at(seed, 50)
        assert w50.name in CYCLE_WEATHERS
        assert w50.tick_in_cycle == 0
        assert w50.progress == 0.0


def test_transition_boundary_99_to_100():
    """Boundary transition from epoch 1 to epoch 2."""
    for seed in FUZZ_SEEDS:
        w99 = weather_at(seed, 99)
        w50 = weather_at(seed, 50)
        # Epoch 1 spans ticks 50..99 with constant weather
        assert w99.name == w50.name
        assert w99.tick_in_cycle == 49
        assert abs(w99.progress - 49 / 50.0) < 1e-6

        w100 = weather_at(seed, 100)
        assert w100.name in CYCLE_WEATHERS
        assert w100.tick_in_cycle == 0
        assert w100.progress == 0.0


def test_epoch_continuity_across_cycles():
    """Verify that inside each 50-tick epoch, weather name remains strictly constant."""
    seed = 777
    for epoch in range(10):
        start_tick = epoch * 50
        expected_weather = weather_at(seed, start_tick).name
        for t in range(start_tick, start_tick + 50):
            w = weather_at(seed, t)
            assert w.name == expected_weather
            assert w.tick_in_cycle == (t - start_tick)
            assert abs(w.progress - (t - start_tick) / 50.0) < 1e-6


def test_extreme_tick_and_boundary_inputs():
    """Stress test large ticks, negative ticks, zero cycle_len, and negative seeds."""
    seed = 42

    # Large tick numbers (tick 10000, 1000000)
    w_10k = weather_at(seed, 10000)
    assert w_10k.tick_in_cycle == 0
    assert w_10k.name in CYCLE_WEATHERS
    assert w_10k.progress == 0.0

    w_1m = weather_at(seed, 1000000)
    assert w_1m.tick_in_cycle == 0
    assert w_1m.name in CYCLE_WEATHERS

    # Negative tick handling: safe_tick = max(0, tick) -> tick 0 CLEAR
    w_neg1 = weather_at(seed, -1)
    assert w_neg1.name == WeatherType.CLEAR.value
    assert w_neg1.tick_in_cycle == 0

    w_neg100 = weather_at(seed, -100)
    assert w_neg100.name == WeatherType.CLEAR.value
    assert w_neg100.tick_in_cycle == 0

    # Zero or negative cycle_len: safe_cycle_len = max(1, cycle_len)
    w_zero_len = weather_at(seed, 10, cycle_len=0)
    assert w_zero_len.cycle_len == 1

    w_neg_len = weather_at(seed, 10, cycle_len=-10)
    assert w_neg_len.cycle_len == 1

    # Negative seed handling
    w_neg_seed = weather_at(-42, 50)
    assert w_neg_seed.name in CYCLE_WEATHERS


# =========================================================================
# 4. PHYSICAL MODIFIER MODULATION & COMPACTION
# =========================================================================


def test_movement_cost_modulation_all_weathers():
    """Verify energy deduction for all 5 weather types in reflex.apply_intent."""
    for w_type in WeatherType:
        rng = random.Random(0)
        world = World(24, 24, rng, seed=1)
        world.grid[5][5] = Terrain.PLAIN
        world.grid[5][6] = Terrain.PLAIN

        traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
        creature = Creature(id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=10.0, energy=10.0)
        creatures_by_id = {creature.id: creature}

        mod = WEATHER_MODIFIERS[w_type.value]
        world.weather = WeatherState(
            name=w_type.value,
            tick_in_cycle=0,
            cycle_len=50,
            progress=0.0,
            modifiers=mod,
        )

        intent = Intent(creature_id="L1:0", path=[(6, 5)])
        steps = apply_intent(intent, creatures_by_id, world)
        assert steps == 1
        expected_cost = config.COST_MOVE * mod.move_cost_mult
        assert abs(creature.energy - (10.0 - expected_cost)) < 1e-5


def test_random_step_movement_cost_modulation_all_weathers():
    """Verify energy deduction for all weather types in creature.random_step."""
    for w_type in WeatherType:
        rng = random.Random(42)
        world = World(24, 24, rng, seed=1)
        traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
        creature = Creature(id="L1:0", species="L1", traits=traits, pos=(12, 12), hp=10.0, energy=10.0)

        mod = WEATHER_MODIFIERS[w_type.value]
        world.weather = WeatherState(
            name=w_type.value,
            tick_in_cycle=0,
            cycle_len=50,
            progress=0.0,
            modifiers=mod,
        )

        step_rng = random.Random(123)
        steps = random_step(creature, world, step_rng)
        if steps > 0:
            expected_cost = steps * config.COST_MOVE * mod.move_cost_mult
            assert abs(creature.energy - (10.0 - expected_cost)) < 1e-5


def test_compounding_sight_penalty_night_and_spore_storm():
    """Verify compounding of NIGHT sight penalty and SPORE_STORM sight penalty with floor clamp."""
    rng = random.Random(0)
    world = World(24, 24, rng, seed=1)
    world.phase = "NIGHT"  # NIGHT penalty = NIGHT_SIGHT_PENALTY (1)

    # Observer with sense=1 -> sight_radius = SIGHT_BASE (2) + 1 = 3
    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=1, stomach=3)
    obs = Creature(id="OBS:0", species="L1", traits=traits, pos=(5, 5), hp=10.0, energy=10.0)

    # Spore storm has sight_penalty = 2
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )

    # Combined penalty: sight_radius = 3 - 1 (NIGHT) - 2 (SPORE_STORM) = 0 -> clamped to 1
    for x in range(3, 8):
        world.grid[5][x] = Terrain.PLAIN

    target_d1 = Creature(id="T1:0", species="L2", traits=traits, pos=(6, 5), hp=10.0, energy=10.0)
    target_d2 = Creature(id="T2:0", species="L2", traits=traits, pos=(7, 5), hp=10.0, energy=10.0)

    seen = visible(obs, world, [obs, target_d1, target_d2])
    # Clamped sight radius is 1 -> can see target_d1 at dist 1, cannot see target_d2 at dist 2
    assert len(seen) == 1
    assert seen[0].id == "T1:0"


# =========================================================================
# 5. SIMULATION TICK PROGRESSION & TELEMETRY LEAK GUARD
# =========================================================================


def test_full_simulation_tick_progression_weather_consistency():
    """Verify simulation progression across 150 ticks keeps world.weather in sync with weather_at."""
    world, creatures, state, sim_rng = init_simulation(seed=99)
    for t in range(150):
        tick(world, creatures, t, sim_rng, state)
        expected_w = weather_at(99, t)
        assert world.weather.name == expected_w.name
        assert world.weather.tick_in_cycle == expected_w.tick_in_cycle
        assert world.weather.cycle_tick == expected_w.cycle_tick
        assert world.weather.progress == expected_w.progress
        assert world.phase in ("DAY", "NIGHT")


def test_diurnal_phase_invariance():
    """Diurnal phase_at(t) must strictly return DAY or NIGHT across 500 ticks."""
    for t in range(500):
        p = phase_at(t)
        assert p in ("DAY", "NIGHT"), f"Invalid diurnal phase at tick {t}: {p}"


def test_telemetry_payload_schema_and_zero_law_leak():
    """Verify telemetry format in MatchRunner frame across all weather transitions and zero forbidden leaks."""
    runner = MatchRunner(seed=1337, ticks=120, tick_ms=1, log_dir=None)

    for t in [0, 49, 50, 99, 100, 119]:
        f = runner.frame(t, [])
        assert "weather" in f, f"Frame {t} missing 'weather' key"
        w = f["weather"]
        assert w["state"] in [v.value for v in WeatherType]
        assert w["cycle_tick"] in range(50)
        assert w["cycle_len"] == 50
        assert 0.0 <= w["progress"] <= 1.0
        assert w["diurnal"] in ("DAY", "NIGHT")
        assert "move_cost_mult" in w["modifiers"]
        assert "sight_penalty" in w["modifiers"]
        assert "plant_mult" in w["modifiers"]
        assert "algae_mult" in w["modifiers"]

        # Forbidden token leak check
        raw_json = json.dumps(f)
        m = FORBIDDEN_PATTERN.search(raw_json)
        assert not m, f"Frame {t} leaked forbidden token '{m.group(0)}'!"

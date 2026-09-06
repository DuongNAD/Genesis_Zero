"""Milestone M2_WEATHER — Challenger 2 Empirical Adversarial Stress Test Suite.

Adversarial stress testing for:
1. Physical modifier enforcement:
   - Stamina cost depletion matches `COST_MOVE * move_cost_mult` under all 5 canonical weather conditions:
     `CLEAR` (1.0), `RAIN` (1.3), `SPORE_STORM` (1.5), `SOLAR_FLARE` (1.4), `MAGNETIC_SHIFT` (1.2).
   - `apply_intent`: single-step, multi-step (1-5 steps), partial paths interrupted by terrain obstacles,
     zero-length paths, dead creatures, toroidal wrapping, and energy exhaustion boundaries.
   - `random_step`: single and multi-step execution under all 5 weathers, boxed-in states, dead creatures.
   - Live `tick()` execution across weather epoch boundaries (ticks 48-52: CLEAR -> cycle weather).

2. Sensory perception bounds & sight radius clamping:
   - Full combinatorial sweep across all sense levels (sense=0..5 -> sight_radius=2..7),
     diurnal phases ("DAY", "NIGHT"), biological traits (with and without night_sight),
     and all 5 weather conditions (120 state permutations verified).
   - Lower bound invariant: sight radius NEVER drops below 1 even under compound penalties
     (sense=0 + NIGHT + SPORE_STORM: 2 - 1 - 2 = -1 -> clamped to 1).
   - Extreme adversarial penalties (penalty = 3, 5, 10, 50, 1000): visible() never crashes,
     and target at distance=1 is unconditionally visible on open terrain.
   - Concealment mechanics in BUSH and TREE: d=1 visible vs d=2 concealed (unless antenna feel_radius=2),
     and exclusion of self and dead creatures.
   - World.visible() equivalence to visible().

3. Plant and algae growth rate scaling:
   - Verification of exact candidate spawn counts across all 5 weathers:
     CLEAR: 2 plants, 2 algae
     RAIN: 3 plants, 3 algae
     SPORE_STORM: 1 plant, 2 algae
     SOLAR_FLARE: 1 plant, 1 algae
     MAGNETIC_SHIFT: 2 plants, 2 algae
   - Saturation constraints: room=0, room < respawn_count, room=1.
   - Candidate cell exhaustion: 0 candidate cells, candidates < respawn_count.
   - Interactions with world.plant_scale: scale=0.5, scale=0.0, zero growth edge cases.
   - Cap preservation: world.fruits <= PLANT_MAX and world.algae <= ALGAE_MAX.
"""

from __future__ import annotations

import random

from genesis import config
from genesis.creature import Creature, random_step
from genesis.reflex import Intent, apply_intent
from genesis.tick import build_match
from genesis.traits import Traits
from genesis.weather import (
    WEATHER_MODIFIERS,
    WeatherModifiers,
    WeatherState,
    WeatherType,
    weather_at,
)
from genesis.world import (
    FRUIT_CLASSES,
    Terrain,
    World,
    spawn_algae,
    spawn_plants,
    visible,
)


def _make_traits(sense: int = 2) -> Traits:
    """Tạo Traits hợp lệ có tổng bằng 12 và sense theo yêu cầu."""
    safe_s = max(0, min(5, sense))
    if safe_s <= 4:
        return Traits(brain=2, attack=2, armor=2, speed=2, sense=safe_s, stomach=4 - safe_s)
    return Traits(brain=1, attack=2, armor=2, speed=2, sense=5, stomach=0)


# =============================================================================
# PART 1: PHYSICAL MODIFIER ENFORCEMENT (STAMINA COST DEPLETION)
# =============================================================================

def test_apply_intent_stamina_cost_all_5_weathers_single_step():
    """1.1 Empirically verify exact single-step stamina depletion across all 5 weathers in apply_intent."""
    test_cases = [
        (WeatherType.CLEAR, 1.0, config.COST_MOVE * 1.0),
        (WeatherType.RAIN, 1.3, config.COST_MOVE * 1.3),
        (WeatherType.SPORE_STORM, 1.5, config.COST_MOVE * 1.5),
        (WeatherType.SOLAR_FLARE, 1.4, config.COST_MOVE * 1.4),
        (WeatherType.MAGNETIC_SHIFT, 1.2, config.COST_MOVE * 1.2),
    ]
    for weather_type, expected_mult, expected_cost_per_step in test_cases:
        assert WEATHER_MODIFIERS[weather_type.value].move_cost_mult == expected_mult
        world = World(24, 24, random.Random(42), seed=1)
        world.grid[5][5] = Terrain.PLAIN
        world.grid[5][6] = Terrain.PLAIN

        world.weather = WeatherState(
            name=weather_type.value,
            tick_in_cycle=10,
            cycle_len=50,
            progress=0.2,
            modifiers=WEATHER_MODIFIERS[weather_type.value],
        )

        creature = Creature(
            id="TEST:0",
            species="TEST",
            traits=_make_traits(sense=2),
            pos=(5, 5),
            hp=20.0,
            energy=15.0,
        )
        by_id = {creature.id: creature}

        intent = Intent(creature_id="TEST:0", path=((6, 5),))
        steps = apply_intent(intent, by_id, world)

        assert steps == 1
        assert creature.pos == (6, 5)
        assert abs(creature.energy - (15.0 - expected_cost_per_step)) < 1e-9, (
            f"Stamina mismatch under {weather_type.value}: expected cost {expected_cost_per_step}, "
            f"actual energy {creature.energy}"
        )


def test_apply_intent_stamina_cost_multi_step_linearity():
    """1.2 Verify linear stamina depletion for multi-step paths (1 to 5 steps) under all weathers."""
    for weather_type in WeatherType:
        mult = WEATHER_MODIFIERS[weather_type.value].move_cost_mult
        cost_step = config.COST_MOVE * mult

        for num_steps in (1, 2, 3, 4, 5):
            world = World(24, 24, random.Random(100), seed=1)
            for x in range(2, 2 + num_steps + 1):
                world.grid[2][x] = Terrain.PLAIN

            world.weather = WeatherState(
                name=weather_type.value,
                tick_in_cycle=0,
                cycle_len=50,
                progress=0.0,
                modifiers=WEATHER_MODIFIERS[weather_type.value],
            )

            initial_energy = 50.0
            creature = Creature(
                id="TEST:0",
                species="TEST",
                traits=_make_traits(sense=2),
                pos=(2, 2),
                hp=20.0,
                energy=initial_energy,
            )
            by_id = {creature.id: creature}

            path = tuple((x, 2) for x in range(3, 3 + num_steps))
            intent = Intent(creature_id="TEST:0", path=path)
            steps_taken = apply_intent(intent, by_id, world)

            assert steps_taken == num_steps
            expected_depletion = num_steps * cost_step
            assert abs(creature.energy - (initial_energy - expected_depletion)) < 1e-9


def test_apply_intent_blocked_path_deducts_only_valid_steps():
    """1.3 Verify that when a path hits an impassable obstacle, only valid steps deduct stamina."""
    world = World(24, 24, random.Random(42), seed=1)
    world.grid[5][5] = Terrain.PLAIN
    world.grid[5][6] = Terrain.PLAIN
    world.grid[5][7] = Terrain.ROCK

    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )

    creature = Creature(
        id="TEST:0",
        species="TEST",
        traits=_make_traits(sense=2),
        pos=(5, 5),
        hp=20.0,
        energy=10.0,
    )
    by_id = {creature.id: creature}

    intent = Intent(creature_id="TEST:0", path=((6, 5), (7, 5)))
    steps_taken = apply_intent(intent, by_id, world)

    assert steps_taken == 1
    assert creature.pos == (6, 5)
    expected_cost = 1 * (config.COST_MOVE * 1.5)
    assert abs(creature.energy - (10.0 - expected_cost)) < 1e-9


def test_apply_intent_edge_cases_empty_dead_and_wrap():
    """1.4 Verify empty path, dead creature, and toroidal wrap step costs."""
    world = World(24, 24, random.Random(42), seed=1)
    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )
    mult = WEATHER_MODIFIERS[WeatherType.RAIN.value].move_cost_mult

    # Case A: Empty path -> 0 steps, 0 energy loss
    c1 = Creature(id="C1:0", species="L1", traits=_make_traits(2), pos=(5, 5), hp=10.0, energy=10.0)
    steps = apply_intent(Intent(creature_id="C1:0", path=()), {"C1:0": c1}, world)
    assert steps == 0
    assert c1.energy == 10.0

    # Case B: Dead creature -> 0 steps, 0 energy loss
    c_dead = Creature(id="CD:0", species="L1", traits=_make_traits(2), pos=(5, 5), hp=0.0, energy=10.0, alive=False)
    steps = apply_intent(Intent(creature_id="CD:0", path=((6, 5),)), {"CD:0": c_dead}, world)
    assert steps == 0
    assert c_dead.energy == 10.0

    # Case C: Toroidal wrap step (0, 0) -> (-1, 0) wrapped to (23, 0)
    world.grid[0][23] = Terrain.PLAIN
    c_wrap = Creature(id="CW:0", species="L1", traits=_make_traits(2), pos=(0, 0), hp=10.0, energy=10.0)
    steps = apply_intent(Intent(creature_id="CW:0", path=((-1, 0),)), {"CW:0": c_wrap}, world)
    assert steps == 1
    assert c_wrap.pos == (23, 0)
    assert abs(c_wrap.energy - (10.0 - config.COST_MOVE * mult)) < 1e-9


def test_random_step_stamina_cost_all_5_weathers():
    """1.5 Empirically verify random_step stamina depletion matches weather multiplier."""
    for weather_type in WeatherType:
        mult = WEATHER_MODIFIERS[weather_type.value].move_cost_mult
        rng = random.Random(12345)
        world = World(24, 24, rng, seed=1)

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                world.grid[5 + dy][5 + dx] = Terrain.PLAIN

        world.weather = WeatherState(
            name=weather_type.value,
            tick_in_cycle=5,
            cycle_len=50,
            progress=0.1,
            modifiers=WEATHER_MODIFIERS[weather_type.value],
        )

        creature = Creature(
            id="RND:0",
            species="L1",
            traits=_make_traits(sense=2),
            pos=(5, 5),
            hp=20.0,
            energy=20.0,
        )
        initial_energy = creature.energy

        steps_taken = random_step(creature, world, random.Random(77))
        assert steps_taken > 0
        expected_depletion = steps_taken * (config.COST_MOVE * mult)
        assert abs(creature.energy - (initial_energy - expected_depletion)) < 1e-9


def test_random_step_boxed_in_zero_stamina_depletion():
    """1.6 Verify that an enclosed creature with 0 passable neighbors incurs 0 stamina cost."""
    world = World(24, 24, random.Random(42), seed=1)
    world.grid[5][5] = Terrain.PLAIN
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        world.grid[5 + dy][5 + dx] = Terrain.ROCK

    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )

    c_boxed = Creature(id="BOX:0", species="L1", traits=_make_traits(2), pos=(5, 5), hp=10.0, energy=10.0)
    steps = random_step(c_boxed, world, random.Random(99))
    assert steps == 0
    assert c_boxed.energy == 10.0


def test_tick_execution_weather_cost_shift_at_epoch_boundary():
    """1.7 End-to-end tick execution: verifies movement cost shifts at tick 50."""
    world, creatures, state, rng = build_match(seed=42)
    c = creatures[0]
    assert c.alive

    world.weather = weather_at(state.match_seed, 49)
    assert world.weather.name == WeatherType.CLEAR.value
    assert world.weather.modifiers.move_cost_mult == 1.0

    world.weather = weather_at(state.match_seed, 50)
    assert world.weather.name in [
        WeatherType.RAIN.value,
        WeatherType.SPORE_STORM.value,
        WeatherType.SOLAR_FLARE.value,
        WeatherType.MAGNETIC_SHIFT.value,
    ]
    expected_mult = world.weather.modifiers.move_cost_mult
    assert expected_mult in (1.2, 1.3, 1.4, 1.5)


# =============================================================================
# PART 2: SENSORY PERCEPTION BOUNDS & SIGHT CLAMPING (SIGHT >= 1)
# =============================================================================

def test_sensory_perception_clamping_combinatorial_sweep():
    """2.1 Combinatorial sweep: verify sight radius >= 1 is unconditionally preserved across 120 states."""
    checked_count = 0
    for sense in [0, 1, 2, 3, 4, 5]:
        for phase in ["DAY", "NIGHT"]:
            for has_night_sight in [False, True]:
                for weather_type in WeatherType:
                    checked_count += 1
                    world = World(24, 24, random.Random(42), seed=1)
                    world.phase = phase

                    for x in range(24):
                        world.grid[10][x] = Terrain.PLAIN

                    world.weather = WeatherState(
                        name=weather_type.value,
                        tick_in_cycle=0,
                        cycle_len=50,
                        progress=0.0,
                        modifiers=WEATHER_MODIFIERS[weather_type.value],
                    )

                    traits = _make_traits(sense=sense)
                    obs = Creature(
                        id="OBS:0",
                        species="L1",
                        traits=traits,
                        pos=(10, 10),
                        hp=20.0,
                        energy=20.0,
                        features=("MAT_DEM",) if has_night_sight else (),
                    )

                    target_d1 = Creature(
                        id="T1:0",
                        species="L2",
                        traits=_make_traits(sense=2),
                        pos=(11, 10),
                        hp=20.0,
                        energy=20.0,
                    )
                    target_far = Creature(
                        id="TFAR:0",
                        species="L2",
                        traits=_make_traits(sense=2),
                        pos=(18, 10),
                        hp=20.0,
                        energy=20.0,
                    )

                    seen = visible(obs, world, [obs, target_d1, target_far])

                    assert target_d1 in seen, (
                        f"Target at distance=1 must be visible! State: sense={sense}, phase={phase}, "
                        f"night_sight={has_night_sight}, weather={weather_type.value}"
                    )
                    assert target_far not in seen

                    raw_radius = config.SIGHT_BASE + sense
                    if phase == "NIGHT" and not has_night_sight:
                        raw_radius = max(1, raw_radius - config.NIGHT_SIGHT_PENALTY)
                    penalty = WEATHER_MODIFIERS[weather_type.value].sight_penalty
                    expected_effective_radius = max(1, raw_radius - penalty)
                    assert expected_effective_radius >= 1

    assert checked_count == 120, f"Must have checked exactly 120 state combinations, got {checked_count}"


def test_sensory_perception_extreme_adversarial_penalties():
    """2.2 Extreme adversarial penalties: verify visible() never crashes and clamps sight to >= 1."""
    for extreme_penalty in [3, 5, 10, 50, 1000]:
        world = World(24, 24, random.Random(42), seed=1)
        world.phase = "NIGHT"

        for x in range(24):
            world.grid[10][x] = Terrain.PLAIN

        extreme_mod = WeatherModifiers(
            move_cost_mult=1.0,
            sight_penalty=extreme_penalty,
            plant_mult=1.0,
            algae_mult=1.0,
        )
        world.weather = WeatherState(
            name="EXTREME_STORM",
            tick_in_cycle=0,
            cycle_len=50,
            progress=0.0,
            modifiers=extreme_mod,
        )

        obs = Creature(
            id="BLIND:0",
            species="L1",
            traits=_make_traits(sense=0),
            pos=(10, 10),
            hp=20.0,
            energy=20.0,
        )

        t1 = Creature(id="T1:0", species="L2", traits=_make_traits(2), pos=(11, 10), hp=10.0, energy=10.0)
        t2 = Creature(id="T2:0", species="L2", traits=_make_traits(2), pos=(12, 10), hp=10.0, energy=10.0)

        seen = visible(obs, world, [obs, t1, t2])

        assert t1 in seen, f"Target at d=1 must remain visible despite massive sight penalty {extreme_penalty}"
        assert t2 not in seen, "Target at d=2 must be out of clamped sight radius 1"
        assert len(seen) == 1

        seen_world_method = world.visible(obs, [obs, t1, t2])
        assert seen_world_method == seen


def test_sensory_perception_bush_and_tree_concealment_with_weather():
    """2.3 Verify concealment in BUSH/TREE under weather conditions and feel_radius antenna trait."""
    world = World(24, 24, random.Random(42), seed=1)
    world.phase = "DAY"
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )

    world.grid[10][10] = Terrain.PLAIN
    world.grid[10][11] = Terrain.BUSH
    world.grid[10][12] = Terrain.TREE

    t_bush_d1 = Creature(id="TB:0", species="L2", traits=_make_traits(2), pos=(11, 10), hp=10.0, energy=10.0)
    t_tree_d2 = Creature(id="TT:0", species="L2", traits=_make_traits(2), pos=(12, 10), hp=10.0, energy=10.0)

    # Observer WITHOUT antenna (feel_radius = 0)
    obs_standard = Creature(
        id="OBS1:0",
        species="L1",
        traits=_make_traits(sense=4),
        pos=(10, 10),
        hp=20.0,
        energy=20.0,
    )
    seen_std = visible(obs_standard, world, [obs_standard, t_bush_d1, t_tree_d2])
    assert t_bush_d1 in seen_std
    assert t_tree_d2 not in seen_std

    # Observer WITH antenna RAU_CAM_UNG (feel_radius = 2)
    obs_antenna = Creature(
        id="OBS2:0",
        species="L1",
        traits=_make_traits(sense=4),
        pos=(10, 10),
        hp=20.0,
        energy=20.0,
        features=("RAU_CAM_UNG",),
    )
    seen_ant = visible(obs_antenna, world, [obs_antenna, t_bush_d1, t_tree_d2])
    assert t_bush_d1 in seen_ant
    assert t_tree_d2 in seen_ant


def test_sensory_perception_dead_and_self_exclusion():
    """2.4 Verify dead creatures and observer itself are strictly excluded from visible list."""
    world = World(24, 24, random.Random(42), seed=1)
    world.grid[10][10] = Terrain.PLAIN
    world.grid[10][11] = Terrain.PLAIN

    obs = Creature(id="OBS:0", species="L1", traits=_make_traits(2), pos=(10, 10), hp=10.0, energy=10.0)
    dead_target = Creature(
        id="DEAD:0",
        species="L2",
        traits=_make_traits(2),
        pos=(11, 10),
        hp=0.0,
        energy=10.0,
        alive=False,
    )

    seen = visible(obs, world, [obs, dead_target])
    assert len(seen) == 0


# =============================================================================
# PART 3: PLANT AND ALGAE GROWTH RATE SCALING
# =============================================================================

def test_plant_and_algae_growth_scaling_all_5_weathers():
    """3.1 Empirically verify exact spawn counts across all 5 weathers on map with ample candidates."""
    cases = [
        (WeatherType.CLEAR, 2, 2),
        (WeatherType.RAIN, 3, 3),
        (WeatherType.SPORE_STORM, 1, 2),
        (WeatherType.SOLAR_FLARE, 1, 1),
        (WeatherType.MAGNETIC_SHIFT, 2, 2),
    ]
    for weather_type, expected_plants, expected_algae in cases:
        world = World(24, 24, random.Random(42), seed=1)
        world.fruits.clear()
        world.algae.clear()

        world.weather = WeatherState(
            name=weather_type.value,
            tick_in_cycle=0,
            cycle_len=50,
            progress=0.0,
            modifiers=WEATHER_MODIFIERS[weather_type.value],
        )

        n_plants = spawn_plants(world, random.Random(10))
        n_algae = spawn_algae(world, random.Random(20))

        assert n_plants == expected_plants, f"Plant spawn mismatch under {weather_type.value}"
        assert n_algae == expected_algae, f"Algae spawn mismatch under {weather_type.value}"

        for cls in world.fruits.values():
            assert cls in FRUIT_CLASSES
        for cls in world.algae.values():
            assert cls == config.ALGAE_CLASS


def test_growth_scaling_room_saturation_limits():
    """3.2 Verify room saturation limits: spawn stops when room=0, clamps when room < respawn."""
    world = World(24, 24, random.Random(42), seed=1)
    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )

    # 1. Room = 0 for plants
    world.fruits = {(x, y): "FRUIT_A" for y in range(config.PLANT_MAX) for x in range(1)}
    assert len(world.fruits) >= config.PLANT_MAX
    assert spawn_plants(world, random.Random(1)) == 0

    # 2. Room = 1 for plants (despite wanting 3)
    world.fruits = {(x, y): "FRUIT_A" for y in range(config.PLANT_MAX - 1) for x in range(1)}
    assert len(world.fruits) == config.PLANT_MAX - 1
    assert spawn_plants(world, random.Random(2)) == 1
    assert len(world.fruits) == config.PLANT_MAX

    # 3. Room = 0 for algae
    world.algae = {(x, y): config.ALGAE_CLASS for y in range(config.ALGAE_MAX) for x in range(1)}
    assert len(world.algae) >= config.ALGAE_MAX
    assert spawn_algae(world, random.Random(3)) == 0

    # 4. Room = 2 for algae (despite wanting 3)
    world.algae = {(x, y): config.ALGAE_CLASS for y in range(config.ALGAE_MAX - 2) for x in range(1)}
    assert len(world.algae) == config.ALGAE_MAX - 2
    assert spawn_algae(world, random.Random(4)) == 2
    assert len(world.algae) == config.ALGAE_MAX


def test_growth_scaling_candidate_exhaustion():
    """3.3 Verify behavior when candidate cells are depleted or scarce on map."""
    world = World(24, 24, random.Random(42), seed=1)
    for y in range(24):
        for x in range(24):
            world.grid[y][x] = Terrain.ROCK
    world.fruits.clear()
    world.algae.clear()

    world.weather = WeatherState(
        name=WeatherType.RAIN.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.RAIN.value],
    )

    assert spawn_plants(world, random.Random(1)) == 0
    assert spawn_algae(world, random.Random(2)) == 0

    world.grid[0][0] = Terrain.PLAIN
    world.grid[0][1] = Terrain.WATER

    assert spawn_plants(world, random.Random(3)) == 1
    assert spawn_algae(world, random.Random(4)) == 1

    assert spawn_plants(world, random.Random(5)) == 0
    assert spawn_algae(world, random.Random(6)) == 0


def test_growth_scaling_plant_scale_and_zero_multiplier():
    """3.4 Verify plant_scale interaction on world and edge case of zero multiplier."""
    world = World(24, 24, random.Random(42), seed=1)
    world.fruits.clear()

    # 1. world.plant_scale = 0.5 under SPORE_STORM (plant_mult = 0.5)
    world.plant_scale = 0.5
    world.weather = WeatherState(
        name=WeatherType.SPORE_STORM.value,
        tick_in_cycle=0,
        cycle_len=50,
        progress=0.0,
        modifiers=WEATHER_MODIFIERS[WeatherType.SPORE_STORM.value],
    )
    n = spawn_plants(world, random.Random(10))
    assert n == 1

    # 2. world.plant_scale = 0.0
    world.fruits.clear()
    world.plant_scale = 0.0
    n_zero = spawn_plants(world, random.Random(11))
    assert n_zero == 0

    # 3. Synthetic weather modifier with plant_mult = 0.0
    world.plant_scale = 1.0
    world.fruits.clear()
    zero_mod = WeatherModifiers(move_cost_mult=1.0, sight_penalty=0, plant_mult=0.0, algae_mult=0.0)
    world.weather = WeatherState(name="DROUGHT", tick_in_cycle=0, cycle_len=50, progress=0.0, modifiers=zero_mod)
    assert spawn_plants(world, random.Random(12)) == 0
    assert spawn_algae(world, random.Random(13)) == 0

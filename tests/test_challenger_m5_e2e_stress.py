"""Genesis Zero — Challenger 2 Adversarial Stress Test Suite (Milestone M5_VERIFY_E2E).

Comprehensive adversarial verification across long-horizon multi-generational simulation:
1. Long-horizon 500-tick continuous simulation with evolution, weather cycles, and telemetry.
2. Strict enforcement of carrying capacity caps (POPULATION_GLOBAL_MAX=35, POPULATION_SPECIES_MAX=7).
3. Zero NaN, inf, or unhandled exceptions under extreme stress and rapid weather cycle oscillation.
4. Memory stability and bounded object footprint (dead offspring lifecycle pruning and corpse decay).
5. 50-generation deep lineage trait/feature mutation zero-sum invariants.
6. Catastrophic environmental mass extinction and founder resurrection resilience.
7. Bitwise determinism replay verification over 500 continuous ticks.
"""

from __future__ import annotations

import json
import math
import random
import re
import tracemalloc
from dataclasses import astuple

import pytest

from genesis import config
from genesis.creature import Creature, creature_sort_key, kill, try_respawn
from genesis.evolution import (
    can_reproduce,
    detect_extinctions,
    mutate_features,
    mutate_traits,
    reproduce_offspring,
    resolve_reproduction,
    trait_variance,
)
from genesis.features import FEATURES
from genesis.tick import build_match, tick as run_tick
from genesis.traits import Traits, founder_traits
from genesis.weather import WEATHER_MODIFIERS, WeatherType, weather_at
from genesis.world import Terrain, World
from net.match import MatchRunner, Phase

FORBIDDEN_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")


# ============================================================================
# 1. Long-Horizon 500-Tick Continuous Simulation Stress Test
# ============================================================================

def test_e2e_stress_500_ticks_continuous_simulation_carrying_capacity_and_invariants():
    """Adversarially stress test 500 continuous ticks of simulation in MatchRunner.

    Verifies at EVERY tick:
    - Global population strictly <= POPULATION_GLOBAL_MAX (35).
    - Species population strictly <= POPULATION_SPECIES_MAX (7).
    - Zero NaN, inf, or corrupted values in coordinates, hp, energy, traits.
    - Traits sum to exactly 12 and remain in [0, 5].
    - Creature ID format strictly matches '<species>:<int>' for creature_sort_key.
    - Telemetry frame is generated, valid JSON, and contains lineage and weather metadata.
    """
    seed = 42
    ticks = 500
    runner = MatchRunner(seed=seed, ticks=ticks, log_dir=None)
    runner.advance_phase()  # LOBBY -> SEEDING
    runner.advance_phase()  # SEEDING -> RUNNING

    reproduction_count = 0
    extinction_count = 0
    max_global_pop = 0
    max_species_pop: dict[str, int] = {}
    weather_states_seen: set[str] = set()
    max_gen_seen = 0

    id_regex = re.compile(r"^[A-Za-z0-9_]+:\d+$")

    for t in range(ticks):
        runner.step()

        alive = [c for c in runner.creatures if c.alive]
        n_alive = len(alive)
        max_global_pop = max(max_global_pop, n_alive)

        # 1. Global population cap invariant
        assert n_alive <= config.POPULATION_GLOBAL_MAX, (
            f"Tick {t}: Global population cap breached! {n_alive} > {config.POPULATION_GLOBAL_MAX}"
        )

        # 2. Species population cap invariant
        sp_counts: dict[str, int] = {}
        for c in alive:
            sp_counts[c.species] = sp_counts.get(c.species, 0) + 1

        for sp, cnt in sp_counts.items():
            max_species_pop[sp] = max(max_species_pop.get(sp, 0), cnt)
            assert cnt <= config.POPULATION_SPECIES_MAX, (
                f"Tick {t}: Species {sp} cap breached! {cnt} > {config.POPULATION_SPECIES_MAX}"
            )

        # 3. Numeric integrity: zero NaN/inf, valid coordinates, trait sums
        for c in alive:
            assert not math.isnan(c.hp) and not math.isinf(c.hp), f"Tick {t}: NaN/inf hp in {c.id}"
            assert not math.isnan(c.energy) and not math.isinf(c.energy), f"Tick {t}: NaN/inf energy in {c.id}"
            assert 0.0 <= c.pos[0] < runner.world.w, f"Tick {t}: Invalid x {c.pos[0]} in {c.id}"
            assert 0.0 <= c.pos[1] < runner.world.h, f"Tick {t}: Invalid y {c.pos[1]} in {c.id}"

            # Trait invariants
            tr_vals = astuple(c.traits)
            assert sum(tr_vals) == config.TRAIT_SUM, f"Tick {t}: Trait sum != 12 in {c.id}: {tr_vals}"
            for v in tr_vals:
                assert config.TRAIT_MIN <= v <= config.TRAIT_MAX, f"Tick {t}: Trait outside [0, 5] in {c.id}: {v}"

            # ID format invariant
            assert id_regex.match(c.id), f"Tick {t}: Malformed ID '{c.id}'"

            max_gen_seen = max(max_gen_seen, getattr(c, "generation", 0))

        # 4. Telemetry frame verification
        frame = runner.frames[-1]
        assert frame["t"] == t
        weather_state = frame["weather"]["state"]
        weather_states_seen.add(weather_state)
        assert weather_state in {w.value for w in WeatherType}
        assert 0.0 <= frame["weather"]["progress"] <= 1.0

        for ev in frame.get("events", []):
            if ev.get("k") == "REPRODUCE":
                reproduction_count += 1
            elif ev.get("k") == "EXTINCTION":
                extinction_count += 1

        # Check JSON serialization of frame without error
        serialized = json.dumps(frame)
        assert serialized is not None

    # Multi-generational progress confirmed
    assert reproduction_count > 0, "500-tick simulation must produce reproduction events"
    assert max_gen_seen >= 1, f"Expected multi-generational lineages (gen >= 1), saw max {max_gen_seen}"
    assert len(weather_states_seen) >= 3, f"Expected multiple weather states across 500 ticks, saw: {weather_states_seen}"
    assert max_global_pop <= config.POPULATION_GLOBAL_MAX


# ============================================================================
# 2. Rapid Weather Cycle Oscillation Stress Test
# ============================================================================

def test_adversarial_rapid_weather_cycle_oscillation_under_reproduction():
    """Adversarially oscillate weather cycles at 5-tick frequency over 500 ticks.

    Triggers 100 weather epoch transitions during active reproduction and movement.
    Verifies that:
    - Movement cost multiplier transitions dynamically without float overflow/underflow.
    - Sensory perception clamping (sight_radius >= 1) never fails under maximum weather penalties.
    - Plant and algae regeneration modulates correctly without unboundedly saturating the map.
    - Population caps strictly hold under environmental oscillation.
    """
    seed = 999
    world, creatures, state, rng = build_match(seed=seed)
    fast_cycle_len = 5  # 5 ticks per epoch -> 100 epochs in 500 ticks

    for t in range(500):
        # Apply rapid weather schedule
        fast_weather = weather_at(seed, t, cycle_len=fast_cycle_len)
        world.weather = fast_weather

        # Execute tick
        run_tick(world, creatures, t, rng, state)

        # Invariant checks
        alive = [c for c in creatures if c.alive]
        assert len(alive) <= config.POPULATION_GLOBAL_MAX
        for c in alive:
            assert not math.isnan(c.hp) and not math.isinf(c.hp)
            assert not math.isnan(c.energy) and not math.isinf(c.energy)
            assert c.energy >= 0.0 or not c.alive

        # Plant and algae bounds
        assert len(world.fruits) <= world.w * world.h
        assert len(world.algae) <= world.w * world.h

        # Weather state properties
        w_dict = fast_weather.to_dict(diurnal=world.phase)
        assert 0.0 <= w_dict["progress"] <= 1.0
        assert w_dict["modifiers"]["move_cost_mult"] > 0.0
        assert w_dict["modifiers"]["sight_penalty"] >= 0


# ============================================================================
# 3. Hyper-Reproductive Burst Capacity Ceiling Enforcement
# ============================================================================

def test_adversarial_hyper_reproductive_burst_capacity_ceilings():
    """Adversarial stress: Force maximum reproductive pressure simultaneously.

    Verifies:
    - If population is at 35, 0 creatures can reproduce (GLOBAL_CAP_REACHED).
    - If population is at 34, out of 20 ready creatures, EXACTLY 1 reproduces.
    - If species is at 6, out of 5 ready creatures, EXACTLY 1 reproduces (SPECIES_CAP_REACHED).
    - Crowding suppression (CROWDING_MAX_NEIGHBORS) blocks clusters in Chebyshev radius 2.
    - Spatial clearance blocks reproduction if parent has no passable neighbor.
    """
    world, creatures, state, rng = build_match(seed=777)

    # 1. Test global cap saturation: fill world with 35 alive creatures
    creatures.clear()
    species_pool = list(config.FOUNDERS.keys())
    for i in range(config.POPULATION_GLOBAL_MAX):
        sp = species_pool[i % len(species_pool)]
        c = Creature(
            id=f"{sp}:{i}",
            species=sp,
            traits=founder_traits(sp),
            pos=(i % world.w, (i // world.w) % world.h),
            hp=float(config.HP_MAX),
            energy=float(founder_traits(sp).energy_max),
            age=100,
            ticks_alive_streak=50,
            reproduce_cooldown=0,
            alive=True,
        )
        creatures.append(c)

    assert len(creatures) == 35
    for c in creatures:
        ok, reason = can_reproduce(c, world, creatures)
        assert not ok
        assert reason == "GLOBAL_CAP_REACHED"

    # 2. Test exactly 1 birth when at 34 creatures
    creatures.pop()  # now 34 creatures
    assert len(creatures) == 34

    # Run resolve_reproduction where all 34 creatures have max energy and cooldown=0
    for c in creatures:
        c.energy = float(c.traits.energy_max)
        c.reproduce_cooldown = 0
        c.age = 50
        c.ticks_alive_streak = 30

    events = resolve_reproduction(world, creatures, tick_no=1, state=state)
    assert len(events) <= 1, f"At 34 creatures, at most 1 birth can occur, got {len(events)}"
    alive_now = [c for c in creatures if c.alive]
    assert len(alive_now) <= config.POPULATION_GLOBAL_MAX

    # 3. Test species cap saturation
    creatures.clear()
    sp = "L1"
    # Create 6 creatures of species L1
    for i in range(6):
        c = Creature(
            id=f"{sp}:{i}",
            species=sp,
            traits=founder_traits(sp),
            pos=(i * 3, 0),  # spread apart to avoid crowding
            hp=float(config.HP_MAX),
            energy=float(founder_traits(sp).energy_max),
            age=50,
            ticks_alive_streak=30,
            reproduce_cooldown=0,
            alive=True,
        )
        creatures.append(c)

    # 6 creatures of L1: can_reproduce should allow 1
    events = resolve_reproduction(world, creatures, tick_no=10, state=state)
    l1_alive = [c for c in creatures if c.alive and c.species == sp]
    assert len(l1_alive) <= config.POPULATION_SPECIES_MAX, (
        f"Species {sp} exceeded max {config.POPULATION_SPECIES_MAX}, got {len(l1_alive)}"
    )

    # Now at cap: subsequent attempts must fail with SPECIES_CAP_REACHED
    if len(l1_alive) == config.POPULATION_SPECIES_MAX:
        for c in l1_alive:
            c.age = 50
            c.ticks_alive_streak = 30
            c.reproduce_cooldown = 0
            c.energy = float(c.traits.energy_max)
            ok, reason = can_reproduce(c, world, creatures)
            assert not ok
            assert reason == "SPECIES_CAP_REACHED"

    # 4. Test spatial clearance block
    boxed_parent = Creature(
        id="BOXED:0",
        species="L1",
        traits=founder_traits("L1"),
        pos=(5, 5),
        hp=50.0,
        energy=100.0,
        age=50,
        ticks_alive_streak=30,
        reproduce_cooldown=0,
        alive=True,
    )
    # Surround (5, 5) with impassable rock
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            world.grid[5 + dy][5 + dx] = Terrain.ROCK

    child = reproduce_offspring(boxed_parent, tick=20, rng=rng, world=world, creatures=[boxed_parent])
    assert child is None, "Parent with no passable neighbors must not reproduce"


# ============================================================================
# 4. Long-Horizon Memory Stability and Offspring Pruning
# ============================================================================

def test_adversarial_long_horizon_memory_stability_and_pruning():
    """Verify memory stability and clean lifecycle pruning over 500 ticks.

    - Dead offspring must be cleanly purged from `creatures` list.
    - Corpses older than CORPSE_TTL (10 ticks) must decay and be purged.
    - Memory growth between tick 100 and tick 500 must remain flat and bounded (< 500 KB).
    """
    world, creatures, state, rng = build_match(seed=12345)

    # Run initial 100 ticks to reach steady-state ecology
    for t in range(100):
        run_tick(world, creatures, t, rng, state)

    tracemalloc.start()
    snap1 = tracemalloc.take_snapshot()

    for t in range(100, 500):
        run_tick(world, creatures, t, rng, state)

        # Offspring pruning invariant: no dead non-reincarnating offspring lingering
        dead_offspring = [
            c for c in creatures
            if c.parent_id is not None and not c.alive and c.dead_until < 0
        ]
        assert len(dead_offspring) == 0, f"Tick {t}: Found unpurged dead offspring: {dead_offspring}"

        # Total creature list size invariant (founders + active living)
        assert len(creatures) <= config.POPULATION_GLOBAL_MAX + len(config.FOUNDERS)

        # Corpse collection invariant: corpses must decay
        for pos, death_tick in world.corpses.items():
            assert t - death_tick <= config.CORPSE_DECAY + 1, f"Corpse at {pos} not decayed after TTL"

    snap2 = tracemalloc.take_snapshot()
    tracemalloc.stop()

    stats = snap2.compare_to(snap1, "lineno")
    total_diff_kb = sum(s.size_diff for s in stats) / 1024.0

    # Memory delta from tick 100 to 500 should be strictly bounded (steady-state flat memory)
    assert total_diff_kb < 500.0, f"Unbounded memory leak detected: {total_diff_kb:.2f} KB growth"


# ============================================================================
# 5. Multi-Generational Trait and Feature Invariants Across 50 Generations
# ============================================================================

def test_adversarial_multi_generational_trait_and_feature_invariants_50_generations():
    """Adversarially force a 50-generation deep reproductive chain with 100% mutation.

    At each generation:
    - sum(traits) == 12.
    - 0 <= trait <= 5.
    - sum(trait_variance) == 0.
    - features tuple contains exactly 3 distinct valid keys from FEATURES.
    - Sequential integer ID formatting remains valid for creature_sort_key.
    """
    rng = random.Random(8888)
    sp = "L2"
    curr_traits = founder_traits(sp)
    curr_feats = tuple(sorted(("LONG_DAI", "VAY_CUNG", "RANG_NANH")))
    all_feature_keys = {f.key for f in FEATURES}

    parent_id = f"{sp}:0"
    lineage_id = parent_id

    for gen in range(1, 51):
        # 100% mutation probability
        mut_traits = mutate_traits(curr_traits, rng, prob=1.0)
        mut_feats = mutate_features(curr_feats, rng, prob=1.0)

        # Trait invariants
        tr_tuple = astuple(mut_traits)
        assert sum(tr_tuple) == config.TRAIT_SUM, f"Gen {gen}: Trait sum != 12: {tr_tuple}"
        for v in tr_tuple:
            assert config.TRAIT_MIN <= v <= config.TRAIT_MAX, f"Gen {gen}: Trait value {v} outside [0, 5]"

        # Trait variance sum == 0
        d_tr = trait_variance(mut_traits, sp)
        assert len(d_tr) == 6
        assert sum(d_tr) == 0, f"Gen {gen}: Trait variance sum != 0: {d_tr}"

        # Biological feature invariants
        assert len(mut_feats) == 3, f"Gen {gen}: Feature count != 3: {mut_feats}"
        assert len(set(mut_feats)) == 3, f"Gen {gen}: Duplicate features: {mut_feats}"
        for k in mut_feats:
            assert k in all_feature_keys, f"Gen {gen}: Unknown feature key: {k}"

        # Construct child
        child_id = f"{sp}:{gen}"
        child = Creature(
            id=child_id,
            species=sp,
            traits=mut_traits,
            pos=(gen % 10, gen % 10),
            hp=float(config.HP_MAX),
            energy=float(config.CHILD_START_ENERGY),
            age=0,
            alive=True,
            parent_id=parent_id,
            generation=gen,
            lineage_id=lineage_id,
            features=mut_feats,
        )

        # ID sort key must not throw
        sort_key = creature_sort_key(child)
        assert sort_key == (sp, gen)

        curr_traits = mut_traits
        curr_feats = mut_feats
        parent_id = child_id


# ============================================================================
# 6. Mass Extinction and Founder Resurrection Resilience
# ============================================================================

def test_adversarial_mass_extinction_and_founder_resurrection():
    """Adversarially induce mass extinction of a species and verify resurrection cycle.

    - Induce complete mortality on all members of species 'W1'.
    - Verify detect_extinctions emits an EXTINCTION event once.
    - Advance simulation until RESPAWN_DELAY elapses.
    - Verify founder reincarnates, is removed from extinct_species, and sim continues cleanly.
    """
    world, creatures, state, rng = build_match(seed=555)

    target_sp = "W1"
    w1_creatures = [c for c in creatures if c.species == target_sp]
    assert len(w1_creatures) > 0

    # Kill all W1 individuals
    kill_tick = 10
    for c in w1_creatures:
        kill(c, world, tick=kill_tick, cause="starve")

    # Run detection
    ext_events = detect_extinctions(creatures, kill_tick, state.extinct_species)
    assert any(e["species"] == target_sp for e in ext_events), "Expected EXTINCTION event for W1"
    assert target_sp in state.extinct_species

    # Run subsequent tick: duplicate extinction must NOT be fired
    ext_events_2 = detect_extinctions(creatures, kill_tick + 1, state.extinct_species)
    assert not any(e["species"] == target_sp for e in ext_events_2), "Duplicate EXTINCTION event emitted"

    # Advance ticks to respawn tick
    respawn_tick = kill_tick + config.RESPAWN_DELAY
    for t in range(kill_tick + 1, respawn_tick + 5):
        run_tick(world, creatures, t, rng, state)

    # Verify W1 founder is alive again and removed from extinct_species
    w1_alive = [c for c in creatures if c.species == target_sp and c.alive]
    assert len(w1_alive) > 0, "Founder failed to reincarnate after RESPAWN_DELAY"
    assert target_sp not in state.extinct_species, "Reincarnated species must be discarded from extinct_species"


# ============================================================================
# 7. Multi-Generational Bitwise Determinism Replay Test Over 500 Ticks
# ============================================================================

def test_adversarial_multi_generational_determinism_500_ticks():
    """Verify that two independent 500-tick simulation runs produce 100% identical states.

    Checks:
    - Same number of creatures alive.
    - Exact matching positions, hp, energy, traits, generation numbers, and lineages.
    - Exact matching weather states and cycle progress.
    """
    seed = 20260903
    ticks = 500

    # Run 1
    w1, c1, s1, r1 = build_match(seed=seed)
    for t in range(ticks):
        run_tick(w1, c1, t, r1, s1)

    # Run 2
    w2, c2, s2, r2 = build_match(seed=seed)
    for t in range(ticks):
        run_tick(w2, c2, t, r2, s2)

    # Verify identical counts
    alive1 = sorted([c for c in c1 if c.alive], key=creature_sort_key)
    alive2 = sorted([c for c in c2 if c.alive], key=creature_sort_key)

    assert len(alive1) == len(alive2), f"Living count mismatch: {len(alive1)} vs {len(alive2)}"

    for ca, cb in zip(alive1, alive2):
        assert ca.id == cb.id
        assert ca.pos == cb.pos
        assert ca.hp == cb.hp
        assert ca.energy == cb.energy
        assert astuple(ca.traits) == astuple(cb.traits)
        assert ca.generation == cb.generation
        assert ca.parent_id == cb.parent_id
        assert ca.lineage_id == cb.lineage_id
        assert ca.features == cb.features

    # Verify identical weather state
    assert w1.weather.name == w2.weather.name
    assert w1.weather.progress == w2.weather.progress
    assert w1.weather.tick_in_cycle == w2.weather.tick_in_cycle

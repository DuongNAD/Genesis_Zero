"""Milestone M1_EVO — Adversarial Stress Tests for Extinction and Recovery Dynamics.

Empirical verification for Challenger 2:
1. Founder death and respawn blocked by SPECIES cap (7) when offspring saturate capacity,
   followed by delayed recovery when offspring capacity opens.
2. Founder death and respawn blocked by GLOBAL cap (35) when global population saturates,
   followed by delayed recovery and clean re-extinction cycle tracking.
3. Competing founders vying for a single available capacity slot (34 -> 35),
   guaranteeing zero overshoot (never 36) and deterministic resolution.
4. Biological mortality vs founder reincarnation: dead offspring are permanently
   pruned and never reincarnate, whereas founders recover.
5. Total simulation extinction (all organisms dead) followed by synchronous
   founder recovery and ecosystem resumption.
6. Spatial confinement / impassable terrain handling during founder respawn.
7. Repeated founder death-rebirth cycles (100 cycles) verifying trait sum and bound invariants.
8. High-turnover multi-generational stress test (1,000 ticks) verifying cap conservation,
   extinction tracking correctness, and memory boundedness.
"""

from __future__ import annotations

from dataclasses import astuple

from genesis import config
from genesis.creature import Creature, creature_sort_key, kill
from genesis.tick import build_match, tick
from genesis.traits import founder_traits
from genesis.world import Terrain


def test_founder_respawn_blocked_by_species_cap_and_delayed_recovery():
    """Verify that when offspring saturate the species cap (7), a dead founder

    is blocked from respawning until offspring mortality opens capacity.
    """
    world, _, state, rng = build_match(seed=101)
    traits = founder_traits("L1")

    # Founder F
    founder = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5),
        hp=50.0, energy=traits.energy_max, age=40, ticks_alive_streak=30,
        reproduce_cooldown=0, parent_id=None,
    )

    # 6 living offspring
    offspring = [
        Creature(
            id=f"L1:{i}", species="L1", traits=traits, pos=(5 + (i % 3), 5 + (i // 3)),
            hp=50.0, energy=traits.energy_max, age=20, ticks_alive_streak=20,
            parent_id="L1:0", generation=1,
        )
        for i in range(1, 7)
    ]

    creatures = [founder, *offspring]
    assert len([c for c in creatures if c.alive and c.species == "L1"]) == 7

    # Tick 10: Founder dies
    kill(founder, world, tick=10, cause="starve")
    assert founder.alive is False
    assert founder.dead_until == 10 + config.RESPAWN_DELAY  # 30

    # Species alive count drops to 6
    assert sum(1 for c in creatures if c.alive and c.species == "L1") == 6

    # Tick 20: Offspring reproduces a 7th living offspring
    new_child = Creature(
        id="L1:7", species="L1", traits=traits, pos=(4, 4),
        hp=50.0, energy=30.0, age=0, parent_id="L1:1", generation=2,
    )
    creatures.append(new_child)
    assert sum(1 for c in creatures if c.alive and c.species == "L1") == 7

    # Run tick 30 (dead_until reached, but species cap is saturated at 7)
    # Keep offspring fed so they do not starve prematurely during saturation check
    for c in [*offspring, new_child]:
        c.energy = c.traits.energy_max
        c.hp = 50.0

    tick(world, creatures, tick_no=30, rng=rng, state=state)

    # Founder MUST remain dead because species cap is 7
    assert founder.alive is False, "Founder must NOT respawn when species cap is saturated"
    assert founder.dead_until == 30
    assert sum(1 for c in creatures if c.alive and c.species == "L1") <= config.POPULATION_SPECIES_MAX

    # Run for 5 more ticks under saturation (ticks 31-35)
    for t in range(31, 36):
        for c in [*offspring, new_child]:
            if c.alive:
                c.energy = c.traits.energy_max
                c.hp = 50.0
        tick(world, creatures, tick_no=t, rng=rng, state=state)
        assert founder.alive is False, f"Tick {t}: Founder must NOT respawn while species cap is 7"
        assert sum(1 for c in creatures if c.alive and c.species == "L1") == config.POPULATION_SPECIES_MAX

    # Founder MUST still be present in creatures list (never pruned)
    assert any(c.id == "L1:0" for c in creatures)

    # Tick 36: Explicitly kill one offspring (e.g. new_child L1:7) to open capacity slot
    kill(new_child, world, tick=36, cause="combat")
    assert sum(1 for c in creatures if c.alive and c.species == "L1") == 6

    # Run tick 36
    tick(world, creatures, tick_no=36, rng=rng, state=state)

    # Now founder MUST have successfully respawned!
    assert founder.alive is True, "Founder must respawn once species capacity slot is liberated"
    assert founder.dead_until == -1
    assert sum(1 for c in creatures if c.alive and c.species == "L1") <= config.POPULATION_SPECIES_MAX
    # And dead offspring new_child must have been pruned
    assert not any(c.id == "L1:7" for c in creatures), "Dead offspring must be pruned from entity pool"


def test_founder_respawn_blocked_by_global_cap_extinction_and_re_extinction():
    """Verify global cap (35) blocks founder respawn, keeping species extinct,

    and that freeing global capacity triggers recovery and subsequent re-extinction cleanly.
    """
    world, creatures, state, rng = build_match(seed=202)
    state.extinct_species = set()

    # Isolate founder of L1
    founder_l1 = next(c for c in creatures if c.species == "L1" and c.parent_id is None)

    # Permanently remove all other L1 creatures
    creatures[:] = [c for c in creatures if c.species != "L1" or c.id == founder_l1.id]

    # Kill founder_l1 at tick 10
    kill(founder_l1, world, tick=10, cause="starve")
    assert founder_l1.dead_until == 10 + config.RESPAWN_DELAY  # 30

    # Fill other species up to exactly 35 living creatures
    other_species = [c for c in creatures if c.species != "L1" and c.alive]
    needed = config.POPULATION_GLOBAL_MAX - len(other_species)
    for i in range(needed):
        sp = "L2"
        extra = Creature(
            id=f"L2:99{i}", species=sp, traits=founder_traits(sp), pos=(10, 10),
            hp=50.0, energy=50.0, parent_id="L2:0", generation=1,
        )
        creatures.append(extra)

    # Verify exactly 35 alive creatures, 0 of which are L1
    assert sum(1 for c in creatures if c.alive) == config.POPULATION_GLOBAL_MAX
    assert sum(1 for c in creatures if c.alive and c.species == "L1") == 0

    # Run ticks 11 to 35: dead_until (30) passes, but global cap is maintained at 35
    for t in range(11, 36):
        # Keep non-L1 population saturated at POPULATION_GLOBAL_MAX (35)
        alive_non_l1 = [c for c in creatures if c.alive and c.species != "L1"]
        while len(alive_non_l1) < config.POPULATION_GLOBAL_MAX:
            idx = len(creatures)
            extra = Creature(
                id=f"L2:fill_{idx}", species="L2", traits=founder_traits("L2"), pos=(10, 10),
                hp=50.0, energy=50.0, parent_id="L2:0", generation=1,
            )
            creatures.append(extra)
            alive_non_l1.append(extra)

        for c in creatures:
            if c.alive:
                c.energy = c.traits.energy_max
                c.hp = 50.0

        tick(world, creatures, tick_no=t, rng=rng, state=state)

        # Before tick 30, founder is waiting for dead_until; at/after tick 30, founder is blocked by cap
        assert founder_l1.alive is False, f"Tick {t}: Founder must NOT respawn while global cap is 35"
        assert "L1" in state.extinct_species, f"Tick {t}: L1 must remain extinct while founder is dead"
        assert sum(1 for c in creatures if c.alive) <= config.POPULATION_GLOBAL_MAX

    # Tick 36: Liberate 2 global slots by killing 2 non-L1 creatures
    victim1 = next(c for c in creatures if c.alive and c.species != "L1")
    kill(victim1, world, tick=36, cause="hazard")
    victim2 = next(c for c in creatures if c.alive and c.species != "L1")
    kill(victim2, world, tick=36, cause="hazard")

    # Run tick 36
    tick(world, creatures, tick_no=36, rng=rng, state=state)

    # L1 founder MUST have respawned!
    assert founder_l1.alive is True, "Founder must respawn once global capacity opens"
    assert sum(1 for c in creatures if c.alive) <= config.POPULATION_GLOBAL_MAX
    assert "L1" not in state.extinct_species, "L1 must recover from extinction upon founder respawn"

    # Tick 50: Kill founder_l1 again -> must trigger re-extinction cleanly
    kill(founder_l1, world, tick=50, cause="starve")
    tick(world, creatures, tick_no=50, rng=rng, state=state)
    assert "L1" in state.extinct_species, "L1 must be marked extinct again after founder re-death"


def test_competing_founders_single_slot_no_overshoot():
    """Two dead founders from different species have dead_until reached at the same tick,

    with exactly 1 global slot available (34 alive, cap=35).
    Verify exactly 1 founder respawns, alive count is 35 (never 36), and the other waits.
    """
    world, _, state, rng = build_match(seed=303)
    state.extinct_species = set()

    traits_l1 = founder_traits("L1")
    traits_l2 = founder_traits("L2")

    f1 = Creature(id="L1:0", species="L1", traits=traits_l1, pos=(2, 2), hp=0.0, energy=0.0, alive=False, parent_id=None)
    f2 = Creature(id="L2:0", species="L2", traits=traits_l2, pos=(8, 8), hp=0.0, energy=0.0, alive=False, parent_id=None)

    f1.dead_until = 25
    f2.dead_until = 25

    # 34 alive creatures from species L3
    living_34 = [
        Creature(
            id=f"L3:{i}", species="L3", traits=founder_traits("L3"), pos=(10, 10),
            hp=50.0, energy=50.0, alive=True, parent_id=None if i == 0 else "L3:0",
        )
        for i in range(34)
    ]

    creatures = [f1, f2, *living_34]
    assert sum(1 for c in creatures if c.alive) == 34

    # Run tick 25
    tick(world, creatures, tick_no=25, rng=rng, state=state)

    total_alive_after = sum(1 for c in creatures if c.alive)
    assert total_alive_after == 35, f"Expected exactly 35 alive creatures, got {total_alive_after}"

    # Verify exactly one of f1, f2 respawned and the other is still dead
    assert (f1.alive and not f2.alive) or (f2.alive and not f1.alive)
    # By sort order (L1 < L2), f1 should have claimed the slot
    assert f1.alive is True, "f1 (L1:0) should claim the slot by sort order"
    assert f2.alive is False, "f2 (L2:0) must be blocked from exceeding global cap"

    # Tick 26: Free a slot by killing one L3 creature
    kill(living_34[1], world, tick=26, cause="starve")
    tick(world, creatures, tick_no=26, rng=rng, state=state)

    # Now f2 must also have respawned!
    assert f2.alive is True, "f2 must respawn in subsequent tick when slot becomes available"
    assert sum(1 for c in creatures if c.alive) <= config.POPULATION_GLOBAL_MAX


def test_offspring_extinction_irreversible_only_founders_recover():
    """When all organisms of a species (1 founder + 5 offspring) die,

    offspring are permanently pruned and never reincarnate; only founder respawns.
    """
    world, _, state, rng = build_match(seed=404)
    traits = founder_traits("L1")

    founder = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5),
        hp=50.0, energy=50.0, alive=True, parent_id=None,
    )
    offspring = [
        Creature(
            id=f"L1:{i}", species="L1", traits=traits, pos=(5 + i, 5),
            hp=50.0, energy=50.0, alive=True, parent_id="L1:0", generation=i,
        )
        for i in range(1, 6)
    ]

    creatures = [founder, *offspring]

    # Kill all 6 creatures at tick 5
    for c in creatures:
        kill(c, world, tick=5, cause="starve")

    # Founder dead_until = 25; offspring dead_until = -1
    assert founder.dead_until == 25
    for child in offspring:
        assert child.dead_until == -1

    # Run ticks 5 to 24
    for t in range(5, 25):
        tick(world, creatures, tick_no=t, rng=rng, state=state)
        assert sum(1 for c in creatures if c.alive) == 0

    # At tick 24, all dead offspring should already have been pruned from creatures
    assert len([c for c in creatures if c.parent_id is not None]) == 0, "Dead offspring must be pruned"
    assert len(creatures) == 1, "Only founder should remain in creature list"
    assert creatures[0].id == "L1:0"

    # Run tick 25: Founder respawns
    tick(world, creatures, tick_no=25, rng=rng, state=state)

    assert founder.alive is True
    assert founder.generation == 0
    assert founder.age == 0
    assert sum(1 for c in creatures if c.alive) == 1
    # Zero offspring were resurrected
    assert not any(c.parent_id is not None for c in creatures)


def test_total_simulation_extinction_and_synchronous_recovery():
    """All creatures in the simulation die. Verify 20 ticks of complete zero-population

    integrity, followed by synchronous recovery of all founders.
    """
    world, creatures, state, rng = build_match(seed=505)
    state.extinct_species = set()

    founder_count = sum(1 for c in creatures if c.parent_id is None)
    all_species = {c.species for c in creatures}

    # Kill all organisms at tick 10
    for c in creatures:
        kill(c, world, tick=10, cause="hazard")

    # Run tick 11: total extinction detected
    tick(world, creatures, tick_no=11, rng=rng, state=state)
    assert sum(1 for c in creatures if c.alive) == 0
    assert state.extinct_species == all_species, "All species must be marked extinct"

    # Run ticks 12 to 29: zero alive, plants/algae still grow, world is stable
    for t in range(12, 30):
        tick(world, creatures, tick_no=t, rng=rng, state=state)
        assert sum(1 for c in creatures if c.alive) == 0
        assert state.extinct_species == all_species

    # Tick 30: All founders reach dead_until (10 + 20 = 30)
    tick(world, creatures, tick_no=30, rng=rng, state=state)

    alive_now = [c for c in creatures if c.alive]
    assert len(alive_now) == founder_count, f"Expected {founder_count} founders alive, got {len(alive_now)}"
    assert len(state.extinct_species) == 0, "All species must have recovered from extinction"

    # Run 20 more ticks: founders move, feed, and survive without errors
    for t in range(31, 51):
        tick(world, creatures, tick_no=t, rng=rng, state=state)
        assert sum(1 for c in creatures if c.alive) > 0, "Recovered ecosystem must sustain living organisms"


def test_founder_respawn_spatial_confinement_impassable_grid():
    """If all cells in the world are made impassable to a founder,

    the founder does not crash try_respawn and remains waiting until terrain opens.
    """
    world, creatures, state, rng = build_match(seed=606)

    founder = next(c for c in creatures if c.species == "L1" and c.parent_id is None)
    creatures[:] = [founder]

    kill(founder, world, tick=5, cause="starve")
    assert founder.dead_until == 25

    # Run until tick 24
    for t in range(6, 25):
        tick(world, creatures, tick_no=t, rng=rng, state=state)

    # At tick 25, flood entire world with DEEP water (strictly impassable to terrestrial L1)
    for y in range(world.h):
        for x in range(world.w):
            world.grid[y][x] = Terrain.DEEP

    # Tick 25: Founder tries to respawn, but 0 passable cells exist
    tick(world, creatures, tick_no=25, rng=rng, state=state)
    assert founder.alive is False, "Founder must NOT respawn without passable cells"
    assert founder.dead_until == 25

    # Restore plain terrain at (5, 5)
    world.grid[5][5] = Terrain.PLAIN

    # Tick 26: Now passable cell exists -> Founder respawns at (5, 5)
    tick(world, creatures, tick_no=26, rng=rng, state=state)
    assert founder.alive is True
    assert founder.pos == (5, 5)


def test_repeated_founder_death_rebirth_trait_invariants_100_cycles():
    """Founder undergoes 100 consecutive death and respawn cycles.

    Verify strict conservation of:
    - sum(traits) == 12
    - 0 <= trait <= 5
    - parent_id is None
    - creature_sort_key stability
    """
    world, creatures, state, rng = build_match(seed=707)
    founder = next(c for c in creatures if c.species == "L1" and c.parent_id is None)
    creatures[:] = [founder]

    current_tick = 1
    for cycle in range(1, 101):
        # Kill founder
        kill(founder, world, tick=current_tick, cause="starve")
        assert founder.alive is False
        dead_until = founder.dead_until

        # Advance to dead_until
        while current_tick <= dead_until:
            tick(world, creatures, tick_no=current_tick, rng=rng, state=state)
            current_tick += 1

        # Founder should now be alive
        assert founder.alive is True, f"Cycle {cycle}: Founder failed to respawn"
        vals = astuple(founder.traits)
        assert sum(vals) == 12, f"Cycle {cycle}: Trait sum violated: {vals}"
        assert all(0 <= v <= 5 for v in vals), f"Cycle {cycle}: Trait bounds violated: {vals}"
        assert founder.parent_id is None, f"Cycle {cycle}: Founder parent_id corrupted"

        sp, idx = creature_sort_key(founder)
        assert sp == "L1" and idx == 0


def test_population_dynamics_multi_generational_high_turnover_stress():
    """1,000 continuous simulation ticks with high turnover (forced high energy + 25% mortality).

    Every tick verifies:
    - total alive <= POPULATION_GLOBAL_MAX (35)
    - species alive <= POPULATION_SPECIES_MAX (7)
    - len(creatures) is bounded (dead offspring pruned)
    - species with 0 alive are in extinct_species, species with >0 alive are not.
    """
    world, creatures, state, rng = build_match(seed=808)
    state.extinct_species = set()

    max_alive = 0
    max_creatures_list_len = 0
    extinction_event_counts: dict[str, int] = {}

    for t in range(1, 1001):
        # 1. Boost energy of living organisms to encourage reproduction
        for c in creatures:
            if c.alive:
                c.energy = c.traits.energy_max
                if c.age < config.REPRODUCE_MIN_AGE:
                    c.age = config.REPRODUCE_MIN_AGE
                if c.ticks_alive_streak < config.REPRODUCE_MIN_STREAK:
                    c.ticks_alive_streak = config.REPRODUCE_MIN_STREAK

        # 2. Induce high mortality every 10 ticks (kill 25% of living population)
        if t % 10 == 0:
            living = [c for c in creatures if c.alive]
            to_kill = rng.sample(living, k=max(1, len(living) // 4))
            for c in to_kill:
                kill(c, world, tick=t, cause="starve")

        # 3. Step tick
        tick(world, creatures, tick_no=t, rng=rng, state=state)

        # 4. Invariant checks
        alive = [c for c in creatures if c.alive]
        total_alive = len(alive)
        max_alive = max(max_alive, total_alive)
        max_creatures_list_len = max(max_creatures_list_len, len(creatures))

        assert total_alive <= config.POPULATION_GLOBAL_MAX, (
            f"Tick {t}: Global cap exceeded! {total_alive} > {config.POPULATION_GLOBAL_MAX}"
        )

        sp_counts: dict[str, int] = {}
        for c in alive:
            sp_counts[c.species] = sp_counts.get(c.species, 0) + 1
            assert sp_counts[c.species] <= config.POPULATION_SPECIES_MAX, (
                f"Tick {t}: Species cap exceeded for {c.species}! {sp_counts[c.species]} > {config.POPULATION_SPECIES_MAX}"
            )

        # Extinction set consistency
        all_species = {c.species for c in creatures}
        for sp in all_species:
            cnt = sp_counts.get(sp, 0)
            if cnt == 0:
                assert sp in state.extinct_species, f"Tick {t}: Species {sp} has 0 alive but not in extinct_species"
            else:
                assert sp not in state.extinct_species, f"Tick {t}: Species {sp} has {cnt} alive but in extinct_species"

        # Memory boundedness: creatures list should never balloon (max = 35 living + founders)
        assert len(creatures) <= config.POPULATION_GLOBAL_MAX + 30, (
            f"Tick {t}: Creature list ballooned to {len(creatures)}! Pruning failure."
        )

    assert max_alive <= config.POPULATION_GLOBAL_MAX
    assert max_creatures_list_len <= config.POPULATION_GLOBAL_MAX + 30

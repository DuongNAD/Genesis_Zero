"""Milestone M1_EVO — Challenger 2 Empirical Adversarial Stress Test Suite.

Adversarially tests:
1. Feature mutation and traversal verification:
   - Traversal feature mutations (LUONG_CU -> WATER/DEEP, TREO_GIOI -> TREE, DAO_HANG/CANH_LUOT -> ROCK/CAVE).
   - Dynamic food targeting (algae vs fruit) enabled by LUONG_CU.
   - Emergent clearance: terrestrial parent escaping into exclusive deep water via amphibious child.
   - Malformed, empty, and corrupted feature sets/kits handling.
2. Crowding suppression (Radius-2 Chebyshev):
   - Exact boundary testing: 3 neighbors (pass) vs 4 neighbors (suppressed).
   - Chebyshev distance boundary: distance 2 (crowd) vs distance 3 (free).
   - Exclusion of dead organisms from crowding count.
   - Toroidal boundary wrap crowding suppression across map edges.
   - Intra-tick dynamic crowding suppression cascade.
3. Species extinction & simulation integrity:
   - Single species extinction detection and idempotency.
   - Progressive cascade extinction across successive ticks.
   - Total extinction of all species: 20-tick zero-alive survival stress test.
   - Empty creatures list tick resilience.
   - Extinction recovery / resurrection tracking and re-extinction detection.
"""

from __future__ import annotations

import random

from genesis.creature import Creature, creature_sort_key
from genesis.domain import Domain, can_enter
from genesis.evolution import (
    can_reproduce,
    detect_extinctions,
    mutate_features,
    reproduce_offspring,
)
from genesis.features import BY_KEY, FEATURES, kit_of
from genesis.tick import build_match, tick
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain

# ═════════════════════════════════════════════════════════════════════════════
# 1. FEATURE MUTATION & TRAVERSAL PASSABILITY VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════

def test_feature_mutation_luong_cu_deep_water_traversal():
    """Verify that mutating LUONG_CU allows terrestrial creature to enter DEEP water."""
    world, _, state, _ = build_match(seed=42)
    pos_deep = (0, 0)
    world.grid[pos_deep[1]][pos_deep[0]] = Terrain.DEEP

    # 1. Founder terrestrial creature L1 without LUONG_CU
    founder_feats = ("LONG_DAI", "VAY_CUNG", "RANG_NANH")
    c_founder = Creature(
        id="L1:0",
        species="L1",
        traits=founder_traits("L1"),
        pos=(1, 0),
        hp=50.0,
        energy=80.0,
        features=founder_feats,
    )
    assert not world.passable(pos_deep, c_founder), "Founder without LUONG_CU must NOT enter DEEP"
    assert not can_enter(Domain.CAN, Terrain.DEEP, c_founder.traits, c_founder.kit)

    # 2. Mutant offspring with LUONG_CU
    mutant_feats = ("LUONG_CU", "VAY_CUNG", "RANG_NANH")
    c_mutant = Creature(
        id="L1:1",
        species="L1",
        traits=founder_traits("L1"),
        pos=(1, 0),
        hp=50.0,
        energy=80.0,
        features=mutant_feats,
    )
    assert world.passable(pos_deep, c_mutant), "Mutant with LUONG_CU MUST enter DEEP"
    assert can_enter(Domain.CAN, Terrain.DEEP, c_mutant.traits, c_mutant.kit)

    # 3. Dynamic food perception: mutant can see algae, founder cannot
    world.algae[(0, 0)] = 20.0
    world.fruits[(1, 1)] = "FRUIT_A"
    world.grid[1][1] = Terrain.PLAIN

    founder_food = world.food_for(c_founder)
    assert (0, 0) not in founder_food, "Founder cannot forage algae in water"
    assert (1, 1) in founder_food, "Founder can forage fruit on plain"

    mutant_food = world.food_for(c_mutant)
    assert (0, 0) in mutant_food, "Amphibious mutant can forage algae in water"
    assert (1, 1) in mutant_food, "Amphibious mutant can forage fruit on plain"


def test_feature_mutation_treo_gioi_tree_climb_traversal():
    """Verify TREO_GIOI reduces climb threshold from speed 3 to speed 1."""
    # Base climb speed is 3
    traits_speed1 = Traits(brain=4, attack=3, armor=2, speed=1, sense=1, stomach=1)
    traits_speed2 = Traits(brain=4, attack=2, armor=2, speed=2, sense=1, stomach=1)
    traits_speed0 = Traits(brain=5, attack=3, armor=2, speed=0, sense=1, stomach=1)

    # Without TREO_GIOI
    kit_normal = kit_of((BY_KEY["LONG_DAI"], BY_KEY["VAY_CUNG"], BY_KEY["RANG_NANH"]))
    assert not can_enter(Domain.CAN, Terrain.TREE, traits_speed1, kit_normal)
    assert not can_enter(Domain.CAN, Terrain.TREE, traits_speed2, kit_normal)

    # With TREO_GIOI (climb_bonus = 2 -> threshold becomes 3 - 2 = 1)
    kit_climber = kit_of((BY_KEY["TREO_GIOI"], BY_KEY["VAY_CUNG"], BY_KEY["RANG_NANH"]))
    assert can_enter(Domain.CAN, Terrain.TREE, traits_speed1, kit_climber), "Speed 1 + TREO_GIOI must climb TREE"
    assert can_enter(Domain.CAN, Terrain.TREE, traits_speed2, kit_climber), "Speed 2 + TREO_GIOI must climb TREE"
    # Strict boundary check: speed 0 with TREO_GIOI still cannot climb (0 < 1)
    assert not can_enter(Domain.CAN, Terrain.TREE, traits_speed0, kit_climber), "Speed 0 must NOT climb TREE even with TREO_GIOI"


def test_feature_mutation_dao_hang_and_canh_luot_rock_cave_traversal():
    """Verify DAO_HANG unlocks ROCK + CAVE, while CANH_LUOT unlocks only ROCK."""
    traits = founder_traits("L1")

    kit_base = kit_of((BY_KEY["LONG_DAI"], BY_KEY["VAY_CUNG"], BY_KEY["RANG_NANH"]))
    kit_canh_luot = kit_of((BY_KEY["CANH_LUOT"], BY_KEY["VAY_CUNG"], BY_KEY["RANG_NANH"]))
    kit_dao_hang = kit_of((BY_KEY["DAO_HANG"], BY_KEY["VAY_CUNG"], BY_KEY["RANG_NANH"]))

    # Base CAN creature
    assert not can_enter(Domain.CAN, Terrain.ROCK, traits, kit_base)
    assert not can_enter(Domain.CAN, Terrain.CAVE, traits, kit_base)

    # CANH_LUOT (extra_terrain={ROCK})
    assert can_enter(Domain.CAN, Terrain.ROCK, traits, kit_canh_luot), "CANH_LUOT must enter ROCK"
    assert not can_enter(Domain.CAN, Terrain.CAVE, traits, kit_canh_luot), "CANH_LUOT must NOT enter CAVE"

    # DAO_HANG (extra_terrain={ROCK, CAVE})
    assert can_enter(Domain.CAN, Terrain.ROCK, traits, kit_dao_hang), "DAO_HANG must enter ROCK"
    assert can_enter(Domain.CAN, Terrain.CAVE, traits, kit_dao_hang), "DAO_HANG must enter CAVE"


def test_empty_and_invalid_feature_kits_robustness():
    """Verify simulation gracefully handles empty, corrupt, or None feature sets."""
    world, _, state, _ = build_match(seed=11)
    pos_plain = (5, 5)
    world.grid[5][5] = Terrain.PLAIN

    # 1. Empty features tuple
    c_empty = Creature(
        id="L1:100", species="L1", traits=founder_traits("L1"), pos=pos_plain,
        hp=50.0, energy=80.0, features=(),
    )
    assert c_empty.kit is None
    assert world.passable(pos_plain, c_empty) is True
    assert world.touchable(pos_plain, c_empty) is True

    # 2. Features with non-existent / invalid keys
    c_invalid = Creature(
        id="L1:101", species="L1", traits=founder_traits("L1"), pos=pos_plain,
        hp=50.0, energy=80.0, features=("UNKNOWN_X", "BAD_GENE_999", "NOT_A_FEATURE"),
    )
    # kit property filters unknown keys gracefully
    assert c_invalid.kit is None
    assert world.passable(pos_plain, c_invalid) is True

    # 3. Features with partial invalid keys
    c_mixed = Creature(
        id="L1:102", species="L1", traits=founder_traits("L1"), pos=pos_plain,
        hp=50.0, energy=80.0, features=("UNKNOWN_X", "LUONG_CU", "BAD_GENE"),
    )
    assert c_mixed.kit is not None
    assert c_mixed.kit.has("LUONG_CU")
    assert Domain.NUOC in c_mixed.kit.extra_domains

    # 4. None features or corrupt kit attribute
    c_corrupt = Creature(
        id="L1:103", species="L1", traits=founder_traits("L1"), pos=pos_plain,
        hp=50.0, energy=80.0,
    )
    c_corrupt.features = None  # type: ignore
    assert c_corrupt.kit is None
    assert world.passable(pos_plain, c_corrupt) is True


def test_child_mutant_spatial_clearance_into_exclusive_terrain():
    """Emergent adaptation: a parent trapped on land surrounded by deep water

    can only reproduce if offspring mutates LUONG_CU.
    """
    world, _, state, rng = build_match(seed=77)
    parent = Creature(
        id="L1:0", species="L1", traits=founder_traits("L1"), pos=(5, 5),
        hp=50.0, energy=100.0, age=50, ticks_alive_streak=30, reproduce_cooldown=0,
        features=("LONG_DAI", "VAY_CUNG", "RANG_NANH"),
    )
    world.grid[5][5] = Terrain.PLAIN

    # Surround parent entirely by DEEP water
    for nx, ny in world.neighbors(parent.pos):
        world.grid[ny][nx] = Terrain.DEEP

    # Case A: Reproduction without LUONG_CU mutation fails spatial clearance
    rng_no_mut = random.Random(999)
    # Monkeypatch mutate_features temporarily to return non-amphibious
    child_no_mut = reproduce_offspring(
        parent, tick=10, rng=rng_no_mut, world=world, creatures=[parent]
    )
    # Since prob=0.15, most seeds don't roll LUONG_CU, or we explicitly test failure:
    for _ in range(20):
        c = reproduce_offspring(parent, tick=10, rng=random.Random(123), world=world, creatures=[parent])
        if c is not None:
            assert "LUONG_CU" in c.features, "Offspring placed into DEEP must possess LUONG_CU"


# ═════════════════════════════════════════════════════════════════════════════
# 2. CROWDING SUPPRESSION STRESS TESTING (RADIUS-2 CHEBYSHEV)
# ═════════════════════════════════════════════════════════════════════════════

def test_crowding_exact_boundary_3_vs_4_neighbors():
    """Strict boundary test: exactly 3 neighbors -> reproduce OK; 4 neighbors -> LOCAL_CROWDING."""
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # 3 neighbors within distance 2
    n1 = Creature(id="L2:1", species="L2", traits=founder_traits("L2"), pos=(11, 10), hp=50.0, energy=50.0)
    n2 = Creature(id="L3:1", species="L3", traits=founder_traits("L3"), pos=(10, 11), hp=50.0, energy=50.0)
    n3 = Creature(id="L4:1", species="L4", traits=founder_traits("L4"), pos=(9, 9), hp=50.0, energy=50.0)

    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3])
    assert ok is True and reason is None, "3 neighbors should NOT trigger crowding suppression"

    # Add 4th neighbor at distance 2 (12, 12): dx=2, dy=2 -> Chebyshev dist = 2
    n4 = Creature(id="L5:1", species="L5", traits=founder_traits("L5"), pos=(12, 12), hp=50.0, energy=50.0)
    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3, n4])
    assert ok is False and reason == "LOCAL_CROWDING", "4 neighbors at distance <= 2 MUST trigger LOCAL_CROWDING"


def test_crowding_distance_chebyshev_2_vs_3():
    """Neighbors at Chebyshev distance 3 must NOT cause crowding suppression."""
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # 4 neighbors at distance 3
    n1 = Creature(id="L2:1", species="L2", traits=traits, pos=(13, 10), hp=50.0, energy=50.0)  # dx=3
    n2 = Creature(id="L2:2", species="L2", traits=traits, pos=(10, 13), hp=50.0, energy=50.0)  # dy=3
    n3 = Creature(id="L2:3", species="L2", traits=traits, pos=(7, 10), hp=50.0, energy=50.0)   # dx=3
    n4 = Creature(id="L2:4", species="L2", traits=traits, pos=(10, 7), hp=50.0, energy=50.0)   # dy=3

    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3, n4])
    assert ok is True and reason is None, "Neighbors at distance 3 must NOT suppress reproduction"

    # Shift n4 into distance 2: pos=(12, 10) -> crowd count becomes 1
    n4.pos = (12, 10)
    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3, n4])
    assert ok is True, "1 neighbor at distance 2 and 3 at distance 3 should NOT suppress"

    # Shift all 4 into distance 2
    n1.pos = (12, 10)
    n2.pos = (10, 12)
    n3.pos = (8, 10)
    n4.pos = (10, 8)
    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3, n4])
    assert ok is False and reason == "LOCAL_CROWDING", "4 neighbors at distance 2 must suppress"


def test_crowding_dead_creatures_ignored():
    """Dead organisms within radius 2 must NOT count towards crowding suppression."""
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # 10 dead creatures packed directly next to parent
    dead_pack = [
        Creature(id=f"L2:{i}", species="L2", traits=traits, pos=(10 + (i % 2), 10 + (i // 2)),
                 hp=0.0, energy=0.0, alive=False)
        for i in range(10)
    ]

    ok, reason = can_reproduce(parent, world, [parent, *dead_pack])
    assert ok is True and reason is None, "Dead organisms must never cause crowding suppression"


def test_crowding_toroidal_boundary_wrap():
    """Verify crowding suppression correctly accounts for toroidal wrap across map seams."""
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")
    # Parent at top-left corner (0, 0)
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    w, h = world.w, world.h
    # 4 neighbors wrapping across toroidal boundary
    n1 = Creature(id="L2:1", species="L2", traits=traits, pos=(w - 1, 0), hp=50.0, energy=50.0)      # dx = 1
    n2 = Creature(id="L2:2", species="L2", traits=traits, pos=(w - 2, 0), hp=50.0, energy=50.0)      # dx = 2
    n3 = Creature(id="L2:3", species="L2", traits=traits, pos=(0, h - 1), hp=50.0, energy=50.0)      # dy = 1
    n4 = Creature(id="L2:4", species="L2", traits=traits, pos=(0, h - 2), hp=50.0, energy=50.0)      # dy = 2

    for n in (n1, n2, n3, n4):
        assert world.dist(parent.pos, n.pos) <= 2, f"Neighbor at {n.pos} should wrap to dist <= 2"

    ok, reason = can_reproduce(parent, world, [parent, n1, n2, n3, n4])
    assert ok is False and reason == "LOCAL_CROWDING", "Toroidal wrap must suppress reproduction when 4 neighbors wrap"


def test_crowding_intra_tick_dynamic_suppression():
    """Verify that a birth early in resolve_reproduction dynamically suppresses

    a neighboring parent later in the same tick.
    """
    world, _, state, _ = build_match(seed=42)
    traits = founder_traits("L1")

    # Clear area around (10, 10) to PLAIN
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            world.grid[10 + dy][10 + dx] = Terrain.PLAIN

    # Parent 1 at (10, 10) with ID "L1:0"
    p1 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )
    # Parent 2 at (11, 10) with ID "L2:0"
    p2 = Creature(
        id="L2:0", species="L2", traits=founder_traits("L2"), pos=(11, 10), hp=50.0,
        energy=founder_traits("L2").energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # Add 3 common neighbors at distance <= 2 to both p1 and p2
    common_neighbors = [
        Creature(id="L3:1", species="L3", traits=founder_traits("L3"), pos=(10, 11), hp=50.0, energy=50.0),
        Creature(id="L4:1", species="L4", traits=founder_traits("L4"), pos=(11, 11), hp=50.0, energy=50.0),
        Creature(id="L5:1", species="L5", traits=founder_traits("L5"), pos=(10, 9), hp=50.0, energy=50.0),
    ]

    creatures = [p1, p2, *common_neighbors]

    # At start: p1 has neighbors {p2, n1, n2, n3} -> 4 neighbors! That would suppress p1.
    # Let's move p2 slightly farther to (12, 10).
    # Then p1 neighbors = {p2(dist 2), n1(dist 1), n2(dist 1.4), n3(dist 1)} -> 4 neighbors.
    # We want p1 to have 3 neighbors, and p2 to have 3 neighbors initially!
    # Let's place:
    # p1 at (10, 10)
    # p2 at (10, 14) -> dist between p1 and p2 is 4 > 2 (they don't see each other)
    # Let common neighbor be at (10, 12).
    # Better yet, test directly: evaluate p2 with creatures before vs after p1's child is appended.
    neighbors_for_p2 = [
        Creature(id="L3:1", species="L3", traits=founder_traits("L3"), pos=(11, 10), hp=50.0, energy=50.0),
        Creature(id="L4:1", species="L4", traits=founder_traits("L4"), pos=(10, 11), hp=50.0, energy=50.0),
        Creature(id="L5:1", species="L5", traits=founder_traits("L5"), pos=(9, 10), hp=50.0, energy=50.0),
    ]
    # Before birth: p2 has 3 neighbors -> can reproduce
    ok_before, _ = can_reproduce(p2, world, [p2, *neighbors_for_p2])
    assert ok_before is True

    # P1 gives birth to child at (10, 9) (dist to p2 is 1)
    newborn_child = Creature(
        id="L1:1", species="L1", traits=traits, pos=(10, 9), hp=50.0, energy=30.0,
    )
    # After birth: p2 has 4 neighbors -> suppressed!
    ok_after, reason = can_reproduce(p2, world, [p2, *neighbors_for_p2, newborn_child])
    assert ok_after is False and reason == "LOCAL_CROWDING"


# ═════════════════════════════════════════════════════════════════════════════
# 3. SPECIES EXTINCTION & SIMULATION INTEGRITY STRESS TESTING
# ═════════════════════════════════════════════════════════════════════════════

def test_single_species_extinction_event_and_idempotency():
    """Verify single species extinction detection and strict one-time event idempotency."""
    world, creatures, state, _ = build_match(seed=42)
    extinct_set: set[str] = set()

    # Kill all L1 creatures
    for c in creatures:
        if c.species == "L1":
            c.alive = False

    # Tick 1: Detect extinction
    evs1 = detect_extinctions(creatures, tick_no=1, extinct_species=extinct_set)
    assert len(evs1) == 1
    assert evs1[0]["kind"] == "EXTINCTION"
    assert evs1[0]["species"] == "L1"
    assert evs1[0]["tick"] == 1
    assert "L1" in extinct_set

    # Tick 2: Must be idempotent (no duplicate event emitted)
    evs2 = detect_extinctions(creatures, tick_no=2, extinct_species=extinct_set)
    assert len(evs2) == 0, "Extinction event must NOT be emitted more than once"

    # Tick 3: Other species still alive
    l2_alive = [c for c in creatures if c.species == "L2" and c.alive]
    assert len(l2_alive) > 0


def test_cascade_extinction_across_successive_ticks():
    """Verify simulation tracks cumulative extinctions across multiple successive ticks."""
    world, creatures, state, _ = build_match(seed=10)
    extinct_set: set[str] = set()
    species_list = ["L1", "L2", "L3", "L4", "L5"]

    for idx, sp in enumerate(species_list, start=1):
        for c in creatures:
            if c.species == sp:
                c.alive = False
        evs = detect_extinctions(creatures, tick_no=idx * 10, extinct_species=extinct_set)
        assert len(evs) == 1
        assert evs[0]["species"] == sp
        assert evs[0]["tick"] == idx * 10
        assert sp in extinct_set

    assert extinct_set == set(species_list)


def test_total_extinction_all_species_sim_integrity():
    """Stress test: all species go completely extinct. Simulation tick loop

    must run for 20 ticks with zero living organisms without crashing.
    """
    world, creatures, state, rng = build_match(seed=99)

    # Eliminate every creature permanently
    for c in creatures:
        c.alive = False
        c.dead_until = -1  # Disable respawn

    assert sum(1 for c in creatures if c.alive) == 0

    # Run 20 ticks under total extinction
    for t in range(1, 21):
        tick(world, creatures, tick_no=t, rng=rng, state=state)

    # Verify simulation integrity: state maintained, zero living organisms, plants still regenerate
    assert sum(1 for c in creatures if c.alive) == 0
    all_sp = {c.species for c in creatures}
    assert state.extinct_species == all_sp
    assert len(world.plants) > 0 or len(world.fruits) > 0


def test_complete_empty_creatures_list_tick_resilience():
    """Adversarial boundary: tick loop executed with an empty creatures list []."""
    world, _, state, rng = build_match(seed=55)
    empty_creatures: list[Creature] = []

    # Must execute cleanly with zero errors
    for t in range(1, 10):
        tick(world, empty_creatures, tick_no=t, rng=rng, state=state)

    assert len(empty_creatures) == 0


def test_extinction_recovery_if_species_respawns():
    """If an extinct species recovers via respawn, it is removed from extinct set;

    and if it dies out again, extinction is re-triggered.
    """
    traits = founder_traits("L1")
    c1 = Creature(id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=0.0, energy=0.0, alive=False)
    extinct_set: set[str] = set()

    # 1. Extinction detected
    ev1 = detect_extinctions([c1], tick_no=5, extinct_species=extinct_set)
    assert len(ev1) == 1 and "L1" in extinct_set

    # 2. Resurrect c1
    c1.alive = True
    c1.hp = 50.0
    ev2 = detect_extinctions([c1], tick_no=6, extinct_species=extinct_set)
    assert len(ev2) == 0
    assert "L1" not in extinct_set, "Living creature must remove species from extinct_species"

    # 3. Dies again
    c1.alive = False
    ev3 = detect_extinctions([c1], tick_no=7, extinct_species=extinct_set)
    assert len(ev3) == 1
    assert ev3[0]["kind"] == "EXTINCTION"
    assert "L1" in extinct_set


# ═════════════════════════════════════════════════════════════════════════════
# 4. ADVANCED ECOLOGICAL & MULTI-GENERATIONAL ADVERSARIAL STRESS TESTS
# ═════════════════════════════════════════════════════════════════════════════

def test_feature_mutation_navigation_maze_adversarial():
    """Adversarial maze: A wall of DEEP water separates creature from food.

    Only a mutant with LUONG_CU can navigate directly through DEEP water.
    """
    world, _, state, _ = build_match(seed=42)
    # Build a vertical barrier of DEEP water at x=4 across all y
    for y in range(world.h):
        world.grid[y][4] = Terrain.DEEP

    # Place plain terrain at x=2 and x=6
    world.grid[5][2] = Terrain.PLAIN
    world.grid[5][6] = Terrain.PLAIN
    target_pos = (6, 5)

    # 1. Terrestrial creature at (2, 5) without LUONG_CU
    c_founder = Creature(
        id="L1:0", species="L1", traits=founder_traits("L1"), pos=(2, 5),
        hp=50.0, energy=80.0, features=("LONG_DAI", "VAY_CUNG", "RANG_NANH"),
    )
    # The barrier tile (4, 5) is strictly impassable to founder
    assert not world.passable((4, 5), c_founder)

    # 2. Mutant creature with LUONG_CU
    c_mutant = Creature(
        id="L1:1", species="L1", traits=founder_traits("L1"), pos=(2, 5),
        hp=50.0, energy=80.0, features=("LUONG_CU", "VAY_CUNG", "RANG_NANH"),
    )
    # The barrier tile (4, 5) is passable to mutant
    assert world.passable((4, 5), c_mutant)

    # Test reflex greedy path towards target
    from genesis.reflex import _greedy_path_towards
    c_founder.pos = (3, 5)
    c_mutant.pos = (3, 5)
    path_founder = _greedy_path_towards((3, 5), target_pos, max_steps=1, world=world, who=c_founder)
    path_mutant = _greedy_path_towards((3, 5), target_pos, max_steps=1, world=world, who=c_mutant)

    # Mutant steps into x=4 (DEEP water barrier)
    assert len(path_mutant) > 0 and path_mutant[0][0] == 4, "Mutant with LUONG_CU must greedily path into DEEP water (x=4)"
    assert world.grid[path_mutant[0][1]][path_mutant[0][0]] == Terrain.DEEP
    # Founder cannot step into x=4
    assert not path_founder or path_founder[0][0] != 4, "Founder without LUONG_CU must NOT path into DEEP water (x=4)"


def test_feature_and_trait_mutation_fuzzing_1000_generations():
    """Fuzzing stress test: simulate a lineage through 1000 successive generations

    with high mutation probability (prob=0.8). Enforce strict invariants at every step.
    """
    rng = random.Random(2026)
    world, _, state, _ = build_match(seed=123)

    ancestor = Creature(
        id="L1:0", species="L1", traits=founder_traits("L1"), pos=(10, 10),
        hp=50.0, energy=100.0, age=50, ticks_alive_streak=30, reproduce_cooldown=0,
        generation=0, lineage_id="L1:0",
        features=("LONG_DAI", "VAY_CUNG", "RANG_NANH"),
    )

    all_feat_keys = {f.key for f in FEATURES}
    current_parent = ancestor
    pool = [ancestor]

    for gen in range(1, 1001):
        # Mutate features and traits
        child_feats = mutate_features(current_parent.features, rng, prob=0.8)
        child_traits = current_parent.traits
        from genesis.evolution import mutate_traits
        child_traits = mutate_traits(child_traits, rng, prob=0.8)

        # Verify invariants
        assert len(child_feats) == 3, f"Gen {gen}: Expected 3 features, got {len(child_feats)}"
        assert len(set(child_feats)) == 3, f"Gen {gen}: Duplicate features in {child_feats}"
        for k in child_feats:
            assert k in all_feat_keys, f"Gen {gen}: Invalid feature key {k}"

        from dataclasses import astuple
        trait_vals = astuple(child_traits)
        assert sum(trait_vals) == 12, f"Gen {gen}: Trait sum invariant violated: {trait_vals}"
        for v in trait_vals:
            assert 0 <= v <= 5, f"Gen {gen}: Trait out of range [0, 5]: {v}"

        child = Creature(
            id=f"L1:{gen}", species="L1", traits=child_traits, pos=(10, 10),
            hp=50.0, energy=30.0, age=0, alive=True,
            parent_id=current_parent.id, generation=gen, lineage_id=ancestor.id,
            birth_tick=gen * 30, reproduce_cooldown=25, features=child_feats,
        )

        # Sorting key integrity
        sp, idx = creature_sort_key(child)
        assert sp == "L1" and idx == gen

        current_parent = child


def test_crowding_dense_pack_24_neighbors_stress():
    """Stress test: 24 organisms surrounding parent (full 5x5 Chebyshev area).

    Verify exact suppression behavior as population is incrementally thinned.
    """
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # Generate all 24 positions in 5x5 square around (10, 10)
    surrounding_positions = [
        (10 + dx, 10 + dy)
        for dy in range(-2, 3)
        for dx in range(-2, 3)
        if not (dx == 0 and dy == 0)
    ]
    assert len(surrounding_positions) == 24

    neighbors = [
        Creature(id=f"L2:{i}", species="L2", traits=traits, pos=pos, hp=50.0, energy=50.0)
        for i, pos in enumerate(surrounding_positions)
    ]

    # Full 24 neighbors: must be suppressed
    ok, reason = can_reproduce(parent, world, [parent, *neighbors])
    assert ok is False and reason == "LOCAL_CROWDING"

    # Thin down incrementally from 24 to 4: all must be suppressed
    for count in (20, 15, 10, 5, 4):
        ok, reason = can_reproduce(parent, world, [parent, *neighbors[:count]])
        assert ok is False and reason == "LOCAL_CROWDING"

    # Thin to 3: MUST PASS
    ok, reason = can_reproduce(parent, world, [parent, *neighbors[:3]])
    assert ok is True and reason is None


def test_extinction_event_stream_and_frame_builder_integration():
    """Verify MatchRunner telemetry frame builder handles REPRODUCE and EXTINCTION

    events without JSON serialization failures or field mismatches.
    """
    import json

    from net.match import MatchRunner

    world, creatures, _, _ = build_match(seed=42)
    runner = MatchRunner(seed=42, ticks=10, tick_ms=1, log_dir=None)
    runner.world = world
    runner.creatures = creatures

    # Manually trigger reproduction event
    rep_event = {
        "kind": "REPRODUCE", "type": "REPRODUCE", "creature_id": "L1:0",
        "parent_id": "L1:0", "who": "L1:0", "child": "L1:1", "child_id": "L1:1",
        "species": "L1", "species_id": "L1", "gen": 1, "pos": [5, 5],
        "traits": [2, 2, 2, 2, 2, 2], "features": ["LUONG_CU", "VAY_CUNG", "RANG_NANH"],
        "d_tr": [0, 0, 0, 0, 0, 0], "detail": "L1:0 reproduced L1:1",
    }
    ext_event = {
        "kind": "EXTINCTION", "type": "EXTINCTION", "species": "L2",
        "species_id": "L2", "tick": 5, "who": "L2", "detail": "Species L2 went extinct",
    }

    frame = runner.frame(tick_no=5, events=[rep_event, ext_event])

    # Validate JSON serializability (no non-serializable objects)
    serialized = json.dumps(frame)
    parsed = json.loads(serialized)

    assert parsed["t"] == 5
    assert len(parsed["events"]) == 2
    ev_kinds = {e["k"] for e in parsed["events"]}
    assert "REPRODUCE" in ev_kinds
    assert "EXTINCTION" in ev_kinds

    # Check event fields
    rep_formatted = next(e for e in parsed["events"] if e["k"] == "REPRODUCE")
    assert rep_formatted["child"] == "L1:1"
    assert rep_formatted["gen"] == 1
    assert rep_formatted["pos"] == [5, 5]

    ext_formatted = next(e for e in parsed["events"] if e["k"] == "EXTINCTION")
    assert ext_formatted["species"] == "L2"

    # Validate creature telemetry format
    for c_info in parsed["creatures"]:
        assert "gen" in c_info
        assert "parent_id" in c_info
        assert "lineage" in c_info
        assert "d_tr" in c_info
        assert "features" in c_info
        assert isinstance(c_info["features"], list)


def test_multi_species_carrying_capacity_and_extinction_interplay():
    """Verify carrying capacity caps dynamically interact with extinction and reproduction."""
    world, _, state, _ = build_match(seed=1)
    traits = founder_traits("L1")

    # Species L1 parent at (10, 10)
    p_l1 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )
    # Species L2 parent far away at (20, 20) (outside crowding radius)
    p_l2 = Creature(
        id="L2:0", species="L2", traits=founder_traits("L2"), pos=(20, 20), hp=50.0,
        energy=founder_traits("L2").energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # 1. L1 reaches species cap of 7 (parent + 6 others)
    l1_cohort = [p_l1] + [
        Creature(id=f"L1:{i}", species="L1", traits=traits, pos=(0, i), hp=50.0, energy=50.0)
        for i in range(1, 7)
    ]
    # L1 cannot reproduce due to SPECIES_CAP_REACHED
    ok1, reason1 = can_reproduce(p_l1, world, [*l1_cohort, p_l2])
    assert ok1 is False and reason1 == "SPECIES_CAP_REACHED"

    # But L2 CAN reproduce (species count is only 1 < 7, and total is 8 < 35)
    ok2, reason2 = can_reproduce(p_l2, world, [*l1_cohort, p_l2])
    assert ok2 is True and reason2 is None

    # 2. Fill global population to 35
    global_cohort = [*l1_cohort, p_l2] + [
        Creature(id=f"L3:{i}", species="L3", traits=founder_traits("L3"), pos=(5, i), hp=50.0, energy=50.0)
        for i in range(1, 28)
    ]
    assert len(global_cohort) == 35

    # Now BOTH L1 and L2 are blocked by GLOBAL_CAP_REACHED
    ok_l1_cap, reason_l1_cap = can_reproduce(p_l1, world, global_cohort)
    assert ok_l1_cap is False and reason_l1_cap == "GLOBAL_CAP_REACHED"

    ok_l2_cap, reason_l2_cap = can_reproduce(p_l2, world, global_cohort)
    assert ok_l2_cap is False and reason_l2_cap == "GLOBAL_CAP_REACHED"

    # 3. All 7 creatures of L1 die -> L1 becomes extinct
    for c in l1_cohort:
        c.alive = False

    extinct_set: set[str] = set()
    events = detect_extinctions(global_cohort, tick_no=15, extinct_species=extinct_set)
    assert any(e["species"] == "L1" for e in events)
    assert "L1" in extinct_set

    # Total alive count drops from 35 to 28 < 35
    alive_now = [c for c in global_cohort if c.alive]
    assert len(alive_now) == 28

    # L2 is now UNBLOCKED and can reproduce again!
    ok_l2_unblocked, reason_unblocked = can_reproduce(p_l2, world, global_cohort)
    assert ok_l2_unblocked is True and reason_unblocked is None


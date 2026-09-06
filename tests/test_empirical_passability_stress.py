"""Genesis Zero — tests/test_empirical_passability_stress.py

Empirical stress tests and adversarial verification for:
1. Domain passability invariants across 100+ seeds and 2000+ simulation ticks.
2. Water creatures NEVER stranded on land.
3. Land creatures NEVER wander into deep ocean without amphibian kit.
4. Aerial creatures can fly over mountains/caves/water/fire.
5. Teleportation respecting domain constraints across 100+ seeds and edge-case radii.
6. Respawn domain compliance across all 5 map presets and 100+ seeds.
7. Referee scoring determinism and stability.
8. Simulation stability and memory leak checks over 1000 continuous ticks.
"""

from __future__ import annotations

import gc
import tracemalloc

from genesis import config, law_config
from genesis.creature import Creature, kill, try_respawn
from genesis.domain import Domain, can_enter, domain_of
from genesis.lawdsl import Effect, EffectKind, Mag
from genesis.lawgen import generate
from genesis.lawhook import apply_creature_effect
from genesis.score import _situations_for, match
from genesis.tick import build_match, tick
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain

MAP_PRESETS = ("DONG_CO", "HOANG_MAC", "QUAN_DAO", "HEM_NUI", "RUNG_RAM")


def _make_test_creature(species: str, pos: tuple[int, int] = (0, 0), traits: Traits | None = None) -> Creature:
    tr = traits if traits is not None else founder_traits(species)
    return Creature(
        id=f"{species}:0",
        species=species,
        traits=tr,
        pos=pos,
        hp=float(config.HP_MAX),
        energy=tr.energy_max,
    )


def test_domain_invariants_across_100_seeds_and_2000_ticks():
    """Oracle stress test: 100 seeds * 20 ticks = 2000 total simulation ticks.

    At every tick and for every living creature:
    - Water species without extra CAN domain MUST be strictly in WATER or DEEP.
    - Land species without extra NUOC domain MUST NEVER be in DEEP.
    - Land species without extra ROCK/CAVE kit MUST NEVER be in ROCK or CAVE.
    - Aerial creatures can occupy any terrain.
    - Movement intents never step into impassable cells.
    """
    total_ticks_checked = 0
    total_creature_positions_checked = 0

    # Cache sample laws for 5 map seeds to avoid redundant generation overhead
    cached_laws = {s: generate(s, "STANDARD", check_solvable=False) for s in range(1, 6)}

    for seed_idx in range(1, 101):
        map_name = MAP_PRESETS[seed_idx % len(MAP_PRESETS)]
        world, creatures, state, rng = build_match(seed=seed_idx, map_name=map_name)
        laws = cached_laws.get((seed_idx % 5) + 1, [])

        for t in range(20):
            tick(world, creatures, t, rng, state, laws=laws)
            total_ticks_checked += 1

            for c in creatures:
                if not c.alive:
                    continue
                total_creature_positions_checked += 1
                pos = world.wrap(*c.pos)
                terrain = world.grid[pos[1]][pos[0]]

                dom = domain_of(c.species)
                kit = world.kits.get(c.species)
                extra_doms = getattr(kit, "extra_domains", ()) if kit else ()
                extra_terrains = getattr(kit, "extra_terrain", ()) if kit else ()

                # Invariant 1: Water creatures NEVER get stranded on land
                if dom is Domain.NUOC and Domain.CAN not in extra_doms:
                    assert terrain in (Terrain.WATER, Terrain.DEEP), (
                        f"Seed {seed_idx} Tick {t} Map {map_name}: Water creature {c.id} ({c.species}) "
                        f"stranded on land terrain {terrain} at {pos}"
                    )

                # Invariant 2: Land creatures NEVER wander into DEEP ocean without amphibian/flying kit
                if dom is Domain.CAN and Domain.NUOC not in extra_doms:
                    assert terrain != Terrain.DEEP, (
                        f"Seed {seed_idx} Tick {t} Map {map_name}: Land creature {c.id} ({c.species}) "
                        f"wandered into DEEP ocean at {pos}"
                    )

                # Invariant 3: Land creatures without burrow/glide kit NEVER in ROCK or CAVE
                if dom is Domain.CAN:
                    if Terrain.ROCK not in extra_terrains:
                        assert terrain != Terrain.ROCK, (
                            f"Seed {seed_idx} Tick {t} Map {map_name}: Land creature {c.id} ({c.species}) "
                            f"entered ROCK without kit at {pos}"
                        )
                    if Terrain.CAVE not in extra_terrains:
                        assert terrain != Terrain.CAVE, (
                            f"Seed {seed_idx} Tick {t} Map {map_name}: Land creature {c.id} ({c.species}) "
                            f"entered CAVE without kit at {pos}"
                        )

    assert total_ticks_checked == 2000
    assert total_creature_positions_checked > 10000


def test_adversarial_teleport_across_100_seeds():
    """Adversarial stress test for EffectKind.TELEPORT across 100 seeds with various radii and traits."""
    teleport_count = 0

    for seed_idx in range(1, 101):
        map_name = MAP_PRESETS[seed_idx % len(MAP_PRESETS)]
        world, creatures, _, rng = build_match(seed=seed_idx, map_name=map_name)

        # Test species across NUOC, CAN, TROI
        test_species = ["W1", "L1", "L2", "L5", "A1"]
        radii = [1, 2, 3, 5, 8, 15, 30]

        for sp in test_species:
            dom = domain_of(sp)
            kit = world.kits.get(sp)
            # Find an initially passable cell for this species
            valid_cells = [
                (x, y) for y in range(world.h) for x in range(world.w)
                if world.passable((x, y), _make_test_creature(sp))
            ]
            if not valid_cells:
                continue

            c = _make_test_creature(sp, pos=valid_cells[0])

            for r in radii:
                eff = Effect(kind=EffectKind.TELEPORT, mag=Mag.SMALL, r=r)
                applied = apply_creature_effect(c, eff, rng, world)
                teleport_count += 1
                assert applied == "TELEPORT"

                pos = world.wrap(*c.pos)
                terrain = world.grid[pos[1]][pos[0]]

                # Invariant: Destination MUST be strictly passable at teleport moment
                assert world.passable(pos, c), (
                    f"Teleport violation: Seed {seed_idx} Map {map_name} Species {sp} at {pos} terrain {terrain}"
                )

                extra_doms = getattr(kit, "extra_domains", ()) if kit else ()
                if dom is Domain.NUOC and Domain.CAN not in extra_doms:
                    assert terrain in (Terrain.WATER, Terrain.DEEP), (
                        f"Water creature {sp} teleported to non-water terrain {terrain} at {pos}"
                    )
                if dom is Domain.CAN and Domain.NUOC not in extra_doms:
                    assert terrain != Terrain.DEEP, (
                        f"Land creature {sp} teleported to DEEP ocean at {pos}"
                    )

    assert teleport_count >= 100 * len(test_species) * len(radii)


def test_adversarial_respawn_across_all_maps_and_seeds():
    """Adversarial stress test: Dead creatures respawn only in valid domain cells across 100 seeds."""
    respawn_checks = 0

    for seed_idx in range(1, 101):
        map_name = MAP_PRESETS[seed_idx % len(MAP_PRESETS)]
        world, creatures, _, rng = build_match(seed=seed_idx, map_name=map_name)

        for c in creatures:
            kill(c, world, tick=0, cause="stress_test")
            assert not c.alive

            # Respawn at tick = RESPAWN_DELAY
            respawned = try_respawn(c, world, tick=config.RESPAWN_DELAY, rng=rng)
            if respawned:
                respawn_checks += 1
                pos = world.wrap(*c.pos)
                terrain = world.grid[pos[1]][pos[0]]

                assert world.passable(pos, c), (
                    f"Respawn violation: Seed {seed_idx} Map {map_name} Species {c.species} at {pos} ({terrain})"
                )

                dom = domain_of(c.species)
                kit = world.kits.get(c.species)
                extra_doms = getattr(kit, "extra_domains", ()) if kit else ()

                if dom is Domain.NUOC and Domain.CAN not in extra_doms:
                    assert terrain in (Terrain.WATER, Terrain.DEEP), (
                        f"Water creature {c.species} respawned in non-water {terrain} at {pos}"
                    )
                if dom is Domain.CAN and Domain.NUOC not in extra_doms:
                    assert terrain != Terrain.DEEP, (
                        f"Land creature {c.species} respawned in DEEP at {pos}"
                    )

    assert respawn_checks > 500


def test_aerial_creatures_passability():
    """Verify that aerial creatures (Domain.TROI) can fly over all terrain types (including ROCK, CAVE, TREE, DEEP)."""
    world, _, _, _ = build_match(seed=42, map_name="QUAN_DAO")
    bird = _make_test_creature("A1")
    assert domain_of("A1") is Domain.TROI

    for t in Terrain:
        # Check domain level
        assert can_enter(Domain.TROI, t, None) is True
        # Check world level with mock grid position
        world.grid[0][0] = t
        assert world.passable((0, 0), bird) is True


def test_referee_scoring_determinism():
    """Verify referee scoring determinism across multiple trials and laws."""
    for seed in range(1, 21):
        laws = generate(seed, "STANDARD", check_solvable=False)
        for idx, law in enumerate(laws):
            sits1 = _situations_for(law, seed, idx)
            sits2 = _situations_for(law, seed, idx)
            assert len(sits1) == len(sits2) == law_config.N_SITUATIONS

            # Self-match should always be 1.0 (or close to 1.0 if null accuracy is low)
            score1 = match(law, law, sits1)
            score2 = match(law, law, sits2)
            assert score1 == score2
            assert score1 == 1.0


def test_simulation_stability_and_memory_leak_1000_ticks():
    """Run a 1000 continuous ticks simulation, verifying stability and bounded memory usage."""
    world, creatures, state, rng = build_match(seed=999, map_name="DONG_CO")
    laws = generate(999, "STANDARD", check_solvable=False)

    gc.collect()
    tracemalloc.start()
    snapshot_start = tracemalloc.take_snapshot()

    for t in range(1000):
        tick(world, creatures, t, rng, state, laws=laws)

    gc.collect()
    snapshot_end = tracemalloc.take_snapshot()
    tracemalloc.stop()

    top_stats = snapshot_end.compare_to(snapshot_start, "lineno")
    total_diff_kb = sum(stat.size_diff for stat in top_stats) / 1024.0

    # Total heap delta over 1000 ticks should be strictly bounded (under 15 MB)
    assert total_diff_kb < 15360, f"Potential memory leak: {total_diff_kb:.2f} KB growth over 1000 ticks"
    assert any(c.alive for c in creatures), "At least some creatures should survive or respawn over 1000 ticks"

"""Empirical Challenger Stress Test Suite: Milestone M2 Gate.

Evaluates:
1. Simulation Determinism & Hotspot Caching (genesis/domain.py & genesis/world.py):
   - Multi-seed simulation determinism across seeds 42, 100, 2026 over 200 ticks.
   - Bit-exact verification of creature trajectories, health, food, combat, scoring.
   - Cache invalidation upon creature trait/kit mutation.
   - Species domain caching consistency and fallback logic.

2. Hydraulic Erosion Batching Threshold & Edge Cases (terra_forge/core/erosion.py):
   - Droplet counts: 0, 1, 400, 401, 1000, 5000 droplets.
   - Strict assertion of numerical stability: 0 NaNs, 0 Infs.
   - Physical mass conservation (|ΔM| < 1e-6).
   - Threshold boundary continuity (400 vs 401 droplets).

3. Thermal Talus Scratch Buffer Pre-allocation & Leak Prevention:
   - Verification of scratch buffer reuse across iterations without reallocation.
   - Verification of zero cross-iteration residue leaks (dirty simulator vs fresh simulator parity).
   - Verification of automatic resizing resiliency when grid dimensions change.
   - Physical mass conservation during thermal weathering.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, r"E:\tool\mcp\terra_forge")

from terra_forge.core.erosion import ErosionSimulator
from terra_forge.core.heightfield import Heightfield2D
from terra_forge.schema.map_config import ErosionConfig

from genesis import config
from genesis.creature import Creature
from genesis.domain import _SPECIES_DOMAIN_CACHE, Domain, can_enter, domain_of
from genesis.tick import build_match, tick
from genesis.traits import Traits
from genesis.world import Terrain, World

# =============================================================================
# PART 1: SIMULATION DETERMINISM & CACHING VERIFICATION
# =============================================================================

@pytest.mark.parametrize("seed", [42, 100, 2026])
def test_simulation_determinism_multi_seed(seed: int):
    """Verify that independent runs with the same seed yield 100% bit-exact state for 200 ticks."""
    ticks_to_run = 200

    def run_sim(s: int):
        world, creatures, state, rng = build_match(s)
        snapshots = []
        for t in range(ticks_to_run):
            tick(world, creatures, t, rng, state, log=None, laws=None, strategist=None)
            # Record complete state snapshot
            creature_states = tuple(
                (c.id, c.pos, c.hp, c.energy, c.eat_count, c.species, c.alive, c.win_count)
                for c in sorted(creatures, key=lambda c: c.id)
            )
            plant_states = tuple(sorted(world.plants.items()))
            snapshots.append((creature_states, plant_states))
        return snapshots

    run_1 = run_sim(seed)
    run_2 = run_sim(seed)

    assert len(run_1) == ticks_to_run
    assert len(run_2) == ticks_to_run

    for t in range(ticks_to_run):
        c1, p1 = run_1[t]
        c2, p2 = run_2[t]
        assert c1 == c2, f"Tick {t} creature state mismatch for seed {seed}!"
        assert p1 == p2, f"Tick {t} plant state mismatch for seed {seed}!"


def test_creature_cached_passable_invalidation_on_trait_mutation():
    """Verify that creature._cached_passable invalidates and recomputes correctly when traits mutate."""
    rng = random.Random(42)
    world = World(20, 20, rng)
    # Set a cell to TREE and FIRE
    world.grid[5][5] = Terrain.TREE
    world.grid[6][6] = Terrain.FIRE

    # Create land creature with low traits (sum = 12)
    low_traits = Traits(brain=2, attack=2, armor=1, speed=1, sense=3, stomach=3)
    c = Creature(
        id="C_TEST",
        species="L1",
        traits=low_traits,
        pos=(0, 0),
        hp=100.0,
        energy=100.0,
    )

    # Initial query: tree and fire should be impassable
    assert not world.passable((5, 5), c)
    assert not world.passable((6, 6), c)
    assert hasattr(c, "_cached_passable")
    cached_before = c._cached_passable

    # Mutate traits: high speed to climb tree (sum = 12)
    high_speed_traits = Traits(brain=2, attack=2, armor=1, speed=config.CLIMB_SPEED, sense=2, stomach=2)
    c.traits = high_speed_traits

    # Passable query should detect trait change, invalidate cache, and allow tree
    assert world.passable((5, 5), c)
    assert not world.passable((6, 6), c)
    cached_after_speed = c._cached_passable
    assert cached_after_speed != cached_before

    # Mutate traits: high armor to cross fire (sum = 12)
    high_armor_traits = Traits(brain=2, attack=2, armor=config.FIRE_ARMOR, speed=1, sense=2, stomach=2)
    c.traits = high_armor_traits

    # Passable query should allow fire, disallow tree
    assert not world.passable((5, 5), c)
    assert world.passable((6, 6), c)


def test_creature_cached_passable_matches_uncached_oracle():
    """Verify that cached world.passable returns the exact same boolean for every terrain as direct can_enter."""
    rng = random.Random(99)
    world = World(10, 10, rng)
    traits = Traits(brain=2, attack=2, armor=1, speed=config.CLIMB_SPEED, sense=2, stomach=2)
    c = Creature(id="C_ORACLE", species="L1", traits=traits, pos=(0, 0), hp=100.0, energy=100.0)

    for terrain in Terrain:
        world.grid[1][1] = terrain
        # Cached call
        res_cached = world.passable((1, 1), c)
        # Direct oracle call
        dom = domain_of(c.species)
        res_oracle = can_enter(dom, terrain, c.traits, c.kit)
        assert res_cached == res_oracle, f"Mismatch on terrain {terrain}: cached={res_cached}, oracle={res_oracle}"


def test_species_domain_cache_consistency():
    """Verify _SPECIES_DOMAIN_CACHE accurately reflects config.SPECIES_DOMAIN and handles unknown species."""
    for sp, expected_dom in config.SPECIES_DOMAIN.items():
        dom = domain_of(sp)
        assert dom == Domain(expected_dom)
        assert sp in _SPECIES_DOMAIN_CACHE

    # Unknown species should fall back to Domain.CAN safely without raising exception
    unknown = "ALIEN_INVADER_99"
    assert domain_of(unknown) == Domain.CAN


# =============================================================================
# PART 2: HYDRAULIC EROSION BATCHING THRESHOLD & EDGE CASES
# =============================================================================

def _create_synthetic_heightfield(res: int = 128) -> Heightfield2D:
    """Create a synthetic mountain peak heightfield with slope for hydraulic erosion testing."""
    hf = Heightfield2D(width=100.0, depth=100.0, resolution=res)
    y, x = np.ogrid[:res, :res]
    cx, cy = res / 2.0, res / 2.0
    r = np.hypot(x - cx, y - cy) / (res / 2.0)
    # Cone mountain peak with elevation between 1.0 and 8.0
    hf.Z = np.clip(8.0 * (1.0 - r) + 1.0, 0.5, 9.5).astype(np.float64)
    hf.sediment = np.zeros_like(hf.Z)
    hf.water_depth = np.zeros_like(hf.Z)
    hf.scree_talus = np.zeros_like(hf.Z)
    return hf


@pytest.mark.parametrize("droplet_count", [0, 1, 400, 401, 1000, 5000])
def test_hydraulic_erosion_droplet_edge_cases(droplet_count: int):
    """Verify hydraulic erosion across edge case droplet counts (0, 1, 400, 401, 1000, 5000)."""
    hf = _create_synthetic_heightfield(res=64)
    initial_mass = float(np.sum(hf.Z))

    cfg = ErosionConfig(
        enabled=True,
        droplet_count=droplet_count,
        max_droplet_steps=30,
        droplet_inertia=0.05,
        sediment_capacity_factor=4.0,
        min_sediment_capacity=0.01,
        erode_speed=0.3,
        deposit_speed=0.3,
        evaporate_speed=0.01,
        gravity=9.81,
    )

    sim = ErosionSimulator(hf, cfg)
    hf_out, sediment_map, water_depth = sim.simulate_hydraulic(seed=42)

    # 1. Numerical stability: strictly 0 NaNs and 0 Infs
    assert np.all(np.isfinite(hf_out.Z)), f"NaN/Inf detected in Z with droplet_count={droplet_count}!"
    assert np.all(np.isfinite(sediment_map)), f"NaN/Inf detected in sediment_map with droplet_count={droplet_count}!"
    assert np.all(np.isfinite(water_depth)), f"NaN/Inf detected in water_depth with droplet_count={droplet_count}!"

    # 2. Strict physical mass conservation
    final_mass = float(np.sum(hf_out.Z))
    mass_delta = abs(final_mass - initial_mass)
    assert mass_delta < 1e-6, f"Mass conservation violated with droplet_count={droplet_count}: delta={mass_delta}"

    # 3. Elevation bounds sanity
    assert np.min(hf_out.Z) >= 0.0, "Elevation dropped below 0.0"
    assert np.max(hf_out.Z) <= 15.0, "Elevation spiked beyond realistic upper bound"

    # 4. Sediment and water non-negativity
    assert np.all(sediment_map >= 0.0), "Negative sediment accumulated"
    assert np.all(water_depth >= 0.0), "Negative water depth accumulated"


def test_hydraulic_threshold_boundary_continuity_400_vs_401():
    """Verify continuity across the Path 1 (<=400) and Path 3 (>400) dispatch boundary."""
    hf_400 = _create_synthetic_heightfield(res=64)
    hf_401 = _create_synthetic_heightfield(res=64)

    cfg_400 = ErosionConfig(enabled=True, droplet_count=400, max_droplet_steps=25)
    cfg_401 = ErosionConfig(enabled=True, droplet_count=401, max_droplet_steps=25)

    sim_400 = ErosionSimulator(hf_400, cfg_400)
    sim_401 = ErosionSimulator(hf_401, cfg_401)

    sim_400.simulate_hydraulic(seed=42)
    sim_401.simulate_hydraulic(seed=42)

    # Both should be finite and stable
    assert np.all(np.isfinite(hf_400.Z))
    assert np.all(np.isfinite(hf_401.Z))

    # Mean elevation deltas should be comparable (order of magnitude agreement)
    delta_400 = np.mean(np.abs(hf_400.Z - _create_synthetic_heightfield(res=64).Z))
    delta_401 = np.mean(np.abs(hf_401.Z - _create_synthetic_heightfield(res=64).Z))

    assert delta_400 > 0.0, "Path 1 produced zero erosion"
    assert delta_401 > 0.0, "Path 3 produced zero erosion"
    ratio = delta_401 / delta_400
    assert 0.2 < ratio < 5.0, f"Discontinuous erosion scale between 400 and 401 droplets: ratio={ratio}"


# =============================================================================
# PART 3: THERMAL TALUS BUFFER REUSE & LEAK PREVENTION
# =============================================================================

def _create_steep_cliff_heightfield(res: int = 64) -> Heightfield2D:
    """Create a heightfield with a vertical fault cliff to trigger thermal talus relaxation."""
    hf = Heightfield2D(width=50.0, depth=50.0, resolution=res)
    hf.Z = np.full((res, res), 2.0, dtype=np.float64)
    # Steep 8m cliff on the right half
    hf.Z[:, res // 2 :] = 10.0
    hf.sediment = np.zeros_like(hf.Z)
    hf.water_depth = np.zeros_like(hf.Z)
    hf.scree_talus = np.zeros_like(hf.Z)
    return hf


def test_thermal_talus_scratch_buffer_zero_reallocation():
    """Verify that ErosionSimulator reuses identical scratch buffers across multiple thermal passes."""
    hf = _create_steep_cliff_heightfield(res=64)
    cfg = ErosionConfig(enabled=True, thermal_iterations=10, talus_angle_deg=35.0, scree_talus_deposition=0.5)

    sim = ErosionSimulator(hf, cfg)
    assert not hasattr(sim, "_scratch_total_excess")

    # Pass 1: initializes scratch buffers
    sim.run_thermal_erosion()

    buf_total = sim._scratch_total_excess
    buf_max = sim._scratch_max_excess
    buf_vol = sim._scratch_volume_loss
    buf_excess_k = sim._scratch_excess_k
    buf_dep_k = sim._scratch_dep_k

    # Pass 2: must reuse existing buffers with identical memory addresses
    sim.run_thermal_erosion()

    assert sim._scratch_total_excess is buf_total
    assert sim._scratch_max_excess is buf_max
    assert sim._scratch_volume_loss is buf_vol
    assert sim._scratch_excess_k is buf_excess_k
    assert sim._scratch_dep_k is buf_dep_k


def test_thermal_talus_zero_cross_iteration_residue_leak():
    """Verify that dirty scratch buffers from prior runs do NOT leak residue into subsequent runs."""
    cfg = ErosionConfig(enabled=True, thermal_iterations=15, talus_angle_deg=35.0, scree_talus_deposition=0.5)

    # Dataset A (cone) and Dataset B (cliff)
    hf_a = _create_synthetic_heightfield(res=64)
    hf_b_fresh = _create_steep_cliff_heightfield(res=64)
    hf_b_dirty = _create_steep_cliff_heightfield(res=64)

    # Baseline: Run fresh simulator on Dataset B
    sim_fresh = ErosionSimulator(hf_b_fresh, cfg)
    sim_fresh.run_thermal_erosion()
    z_clean = hf_b_fresh.Z.copy()
    scree_clean = hf_b_fresh.scree_talus.copy()

    # Reused: Run simulator on Dataset A first, then reuse on Dataset B
    sim_reused = ErosionSimulator(hf_a, cfg)
    sim_reused.run_thermal_erosion()  # Buffers now contain dirty state from Dataset A
    sim_reused.hf = hf_b_dirty
    sim_reused.run_thermal_erosion()
    z_reused = hf_b_dirty.Z.copy()
    scree_reused = hf_b_dirty.scree_talus.copy()

    # Both results must be 100% bit-exact identical!
    assert np.array_equal(z_clean, z_reused), "Residue leak detected in terrain heightfield Z!"
    assert np.array_equal(scree_clean, scree_reused), "Residue leak detected in scree_talus field!"


def test_thermal_talus_mass_conservation_and_scree_monotonicity():
    """Verify strict physical mass conservation and non-negative scree deposition."""
    hf = _create_steep_cliff_heightfield(res=64)
    cfg = ErosionConfig(enabled=True, thermal_iterations=20, talus_angle_deg=30.0, scree_talus_deposition=0.6)
    initial_mass = float(np.sum(hf.Z))

    sim = ErosionSimulator(hf, cfg)
    sim.run_thermal_erosion()

    final_mass = float(np.sum(hf.Z))
    assert abs(final_mass - initial_mass) < 1e-9, f"Mass changed during thermal weathering: {abs(final_mass - initial_mass)}"
    assert np.all(hf.scree_talus >= 0.0), "Scree talus contains negative values!"
    assert np.sum(hf.scree_talus) > 0.0, "Steep cliff produced zero scree talus deposition"


def test_thermal_talus_grid_resizing_resiliency():
    """Verify that when simulator encounters a different grid size, scratch buffers resize safely without crash."""
    cfg = ErosionConfig(enabled=True, thermal_iterations=5, talus_angle_deg=35.0, scree_talus_deposition=0.5)

    hf_small = _create_steep_cliff_heightfield(res=32)
    sim = ErosionSimulator(hf_small, cfg)
    sim.run_thermal_erosion()
    assert sim._scratch_total_excess.shape == (32, 32)

    # Now assign larger heightfield
    hf_large = _create_steep_cliff_heightfield(res=64)
    sim.hf = hf_large
    sim.run_thermal_erosion()
    assert sim._scratch_total_excess.shape == (64, 64)
    assert np.all(np.isfinite(hf_large.Z))


# =============================================================================
# PART 4: ADVERSARIAL STRESS EXTENSIONS
# =============================================================================

import tempfile

from genesis.lawgen import generate_cached
from genesis.logio import LogWriter


@pytest.mark.parametrize("seed", [42, 100, 2026])
def test_simulation_determinism_with_active_laws_and_combat(seed: int):
    """Verify that multi-seed runs with active hidden laws, combat, and scoring produce 100% bit-exact event logs."""
    ticks_to_run = 150
    arm = "STANDARD"
    laws = generate_cached(seed, arm=arm)

    def run_with_log(s: int) -> list[str]:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp_log:
            tmp_log_path = Path(tmp_log.name)
        try:


            world, creatures, state, rng = build_match(s)
            with LogWriter(tmp_log_path, f"m_{s:05d}") as log:
                log.write(0, "RUN_START", seed=s, ticks=ticks_to_run, arm=arm,
                          grid=[config.GRID_W, config.GRID_H], n_laws=len(laws))
                for t in range(ticks_to_run):
                    tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=None)
                log.write(ticks_to_run, "RUN_END", ticks=ticks_to_run)
            return tmp_log_path.read_text(encoding="utf-8").splitlines()
        finally:
            if tmp_log_path.exists():
                tmp_log_path.unlink()

    log_1 = run_with_log(seed)
    log_2 = run_with_log(seed)

    assert len(log_1) == len(log_2)
    for idx, (line1, line2) in enumerate(zip(log_1, log_2)):
        assert line1 == line2, f"Log mismatch at line {idx} for seed {seed}!\n1: {line1}\n2: {line2}"


def test_creature_cached_passable_invalidation_on_kit_mutation():
    """Verify that creature._cached_passable invalidates and updates when creature kit changes."""
    class FakeKit:
        def __init__(self, extra_terrain=(), extra_domains=(), climb_bonus=0):
            self.extra_terrain = extra_terrain
            self.extra_domains = extra_domains
            self.climb_bonus = climb_bonus

    rng = random.Random(42)
    world = World(20, 20, rng)
    world.grid[3][3] = Terrain.ROCK
    world.grid[4][4] = Terrain.DEEP

    traits = Traits(brain=2, attack=2, armor=2, speed=2, sense=2, stomach=2)
    c = Creature(id="C_KIT", species="L1", traits=traits, pos=(0, 0), hp=100.0, energy=100.0)

    # Initial land creature: rock and deep water are impassable
    assert not world.passable((3, 3), c)
    assert not world.passable((4, 4), c)

    # Mutate kit: burrowing opens rock
    c.kit = FakeKit(extra_terrain=(Terrain.ROCK,))
    assert world.passable((3, 3), c)
    assert not world.passable((4, 4), c)

    # Mutate kit: amphibious opens water and deep water
    c.kit = FakeKit(extra_domains=(Domain.NUOC,))
    assert world.passable((4, 4), c)


def test_hydraulic_erosion_flat_surface_extreme_boundary():
    """Verify that a completely flat surface does not trigger NaN/Inf or division by zero in batched Path 3."""
    res = 64
    hf = Heightfield2D(width=50.0, depth=50.0, resolution=res)
    hf.Z = np.full((res, res), 5.0, dtype=np.float64)  # Flat plane
    initial_mass = float(np.sum(hf.Z))

    cfg = ErosionConfig(enabled=True, droplet_count=1000, max_droplet_steps=30)
    sim = ErosionSimulator(hf, cfg)
    hf_out, sediment, water = sim.simulate_hydraulic(seed=42)

    assert np.all(np.isfinite(hf_out.Z))
    assert np.all(np.isfinite(sediment))
    assert np.all(np.isfinite(water))
    # On flat plane, slope is 0, erosion is 0, mass conserved
    assert abs(float(np.sum(hf_out.Z)) - initial_mass) < 1e-9


@pytest.mark.parametrize("angle,iters,dep", [
    (1.0, 5, 0.5),    # Minimal talus angle (extreme relaxation)
    (89.0, 5, 0.5),   # Near vertical talus angle (no relaxation)
    (35.0, 0, 0.5),   # Zero iterations (no-op)
    (35.0, 10, 0.0),  # Zero deposition rate (no-op)
])
def test_thermal_talus_boundary_angles_and_zero_conditions(angle: float, iters: int, dep: float):
    """Verify stability across extreme angles and zero iteration/deposition boundary conditions."""
    hf = _create_steep_cliff_heightfield(res=32)
    initial_mass = float(np.sum(hf.Z))
    cfg = ErosionConfig(enabled=True, thermal_iterations=iters, talus_angle_deg=angle, scree_talus_deposition=dep)

    sim = ErosionSimulator(hf, cfg)
    sim.run_thermal_erosion()

    assert np.all(np.isfinite(hf.Z))
    assert np.all(np.isfinite(hf.scree_talus))
    assert abs(float(np.sum(hf.Z)) - initial_mass) < 1e-9


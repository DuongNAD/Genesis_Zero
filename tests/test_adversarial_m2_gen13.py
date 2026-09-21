"""Milestone M2 Empirical Adversarial Challenge Test Suite (Gen 13).

Empirically verifies correctness, physical/topographical invariants,
and performance gains across the 7 optimizations in Milestone M2:
1. Feature 10: Binary .anmw FNV-1a checksum acceleration & bit-exact parity
2. Feature 9: NavMesh spawn clearance 2D mask rasterization & collision avoidance
3. Feature 11: Vectorized mesh index quad construction
4. Features 12 & 13: Hydraulic threshold & thermal talus scratch buffer reuse
5. Feature 14: Simulation tick loop hotspot caching (domain & passable)
"""

from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

TERRA_FORGE_PATH = Path(r"E:\tool\mcp\terra_forge")
if str(TERRA_FORGE_PATH) not in sys.path:
    sys.path.insert(0, str(TERRA_FORGE_PATH))

# Skip the entire module if terra_forge is not available (e.g., in CI)
pytest.importorskip("terra_forge")

from terra_forge.core.erosion import ErosionConfig, ErosionSimulator
from terra_forge.core.heightfield import Heightfield2D
from terra_forge.core.open_mesh import OpenWorldMesh
from terra_forge.core.world_artifact import _HAS_NUMBA_FNV, WorldArtifact, fnv1a_32
from terra_forge.navigation.navmesh import (
    NavMeshReachabilityValidator,
    ObstacleGridSynchronizer,
    cell_to_world,
)

from genesis import config
from genesis.domain import _SPECIES_DOMAIN_CACHE, Domain, domain_of
from genesis.world import Terrain, World


def fnv1a_32_reference(data: bytes | bytearray | memoryview | np.ndarray) -> int:
    """Pure-Python reference implementation of 32-bit FNV-1a."""
    h = 0x811C9DC5
    for b in data:
        h ^= int(b)
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def ref_quad_indices(H: int, W: int) -> np.ndarray:
    """Sequential reference implementation of quad triangle indices."""
    indices = []
    for iy in range(H - 1):
        for ix in range(W - 1):
            v00 = iy * W + ix
            v10 = v00 + 1
            v01 = v00 + W
            v11 = v01 + 1
            indices.extend([v00, v01, v10, v10, v01, v11])
    return np.array(indices, dtype=np.uint32)


# ==============================================================================
# 1. FEATURE 10: FNV-1a CHECKSUM PARITY & INVARIANTS
# ==============================================================================

def test_fnv1a_numba_environment():
    """Assert that Numba JIT acceleration is active in current Python environment."""
    pytest.importorskip("numba")
    assert _HAS_NUMBA_FNV is True, "Numba JIT acceleration must be enabled for fnv1a_32"


@pytest.mark.parametrize("buffer_input", [
    b"",
    b"\x00",
    b"\x01",
    b"\xff",
    b"hello world",
    b"Genesis_Zero_Milestone_M2_Performance",
    b"\x00" * 10000,
    b"\xff" * 10000,
    bytes([i % 256 for i in range(65536)]),
], ids=[
    "empty", "null_byte", "one_byte", "ff_byte",
    "ascii_short", "ascii_medium", "zeros_10k", "ffs_10k", "pattern_64k"
])
def test_fnv1a_bit_exact_parity_with_reference(buffer_input):
    """Verify bit-exact hash parity between accelerated fnv1a_32 and pure-Python reference."""
    res_opt = fnv1a_32(buffer_input)
    res_ref = fnv1a_32_reference(buffer_input)
    assert res_opt == res_ref, f"Mismatch for input of length {len(buffer_input)}: {res_opt:#x} != {res_ref:#x}"


def test_fnv1a_random_buffers_adversarial_fuzzing():
    """Fuzz test fnv1a_32 against reference over multiple buffer sizes and seeds."""
    rng = random.Random(42)
    sizes = [1, 7, 13, 64, 512, 4096, 32768, 131072, 1048576]
    for sz in sizes:
        buf = rng.randbytes(sz)
        assert fnv1a_32(buf) == fnv1a_32_reference(buf)


def test_world_artifact_256_checksum_invariant():
    """Verify canonical world_256.anmw has exact 0x861B9B50 checksum and executes < 3ms."""
    pytest.importorskip("numba")
    path = Path("assets/world_256.anmw")
    assert path.exists(), "assets/world_256.anmw must exist"

    with open(path, "rb") as f:
        data = f.read()

    payload = data[36:]
    assert len(data) == 1_114_148, f"Expected 1114148 bytes, got {len(data)}"

    # 1. Accelerated checksum
    t0 = time.perf_counter()
    c_opt = fnv1a_32(payload)
    dt_opt_ms = (time.perf_counter() - t0) * 1000

    # 2. Reference checksum
    c_ref = fnv1a_32_reference(payload)

    # Invariants
    assert c_opt == 0x861B9B50, f"Expected 0x861B9B50, got 0x{c_opt:08X}"
    assert c_ref == 0x861B9B50, f"Reference expected 0x861B9B50, got 0x{c_ref:08X}"
    assert c_opt == c_ref, "Accelerated and reference hashes must be bit-exact"

    # Performance constraint: warmed Numba hash of 1.11 MB must be under 3.0 ms
    for _ in range(5):
        _ = fnv1a_32(payload)
    t0 = time.perf_counter()
    for _ in range(20):
        _ = fnv1a_32(payload)
    avg_opt_ms = (time.perf_counter() - t0) / 20 * 1000
    assert avg_opt_ms < 3.0, f"Hash of 1.11MB took {avg_opt_ms:.3f} ms (must be < 3.0 ms)"

    # 3. Codec integration
    artifact = WorldArtifact.from_file(str(path))
    assert artifact.checksum() == 0x861B9B50


# ==============================================================================
# 2. FEATURE 9: NAVMESH CLEARANCE 2D MASK & SAFE SPAWN SELECTION
# ==============================================================================

@pytest.mark.parametrize("num_obstacles", [0, 50, 300, 1000])
def test_navmesh_spawn_clearance_no_intersections(num_obstacles):
    """Assert safe spawn point never intersects any obstacle clearance zone under various obstacle densities."""
    artifact = WorldArtifact.from_file("assets/world_256.anmw")
    shape = (artifact.height, artifact.width)
    bounds = (-100.0, -100.0, 100.0, 100.0)
    elevation_2d = artifact.elevation.reshape(shape)

    sync = ObstacleGridSynchronizer(shape=shape, world_bounds=bounds)
    rng = random.Random(1337 + num_obstacles)
    tall_species = [0, 1, 2, 3, 4, 5, 6]
    for i in range(num_obstacles):
        sp = rng.choice(tall_species)
        x = rng.uniform(-90.0, 90.0)
        z = rng.uniform(-90.0, 90.0)
        scale = rng.uniform(0.8, 2.2)
        sync.register_flora_instance(i, sp, x, z, scale)

    val = NavMeshReachabilityValidator(elevation=elevation_2d, sea_level=artifact.sea_level, world_bounds=bounds)
    walkable = val.compute_walkable_mask(sync.obstacle_grid)

    t0 = time.perf_counter()
    spawn_cell = val.find_safe_spawn_point(walkable, sync)
    dt_ms = (time.perf_counter() - t0) * 1000

    r, c = spawn_cell
    assert 0 <= r < shape[0] and 0 <= c < shape[1], f"Spawn cell ({r}, {c}) out of bounds"
    assert walkable[r, c], f"Spawn cell ({r}, {c}) is not walkable"
    assert sync.canopy_clearance_mask[r, c], f"Spawn cell ({r}, {c}) overlaps canopy clearance mask"

    wx, wy, wz = cell_to_world(r, c, shape, elevation_2d, bounds)
    assert sync.is_flora_clear_for_spawn(wx, wz), f"Spawn position ({wx}, {wz}) failed is_flora_clear_for_spawn"

    # Exhaustive distance check against every solid obstacle
    for obs in sync.solid_obstacles:
        d = math.hypot(wx - obs.x, wz - obs.z)
        assert d >= obs.spawn_clearance, (
            f"Spawn point ({wx:.2f}, {wz:.2f}) intersects obstacle {obs.instance_index} "
            f"at ({obs.x:.2f}, {obs.z:.2f}): dist={d:.3f} < clearance={obs.spawn_clearance:.3f}"
        )


def test_navmesh_clearance_mask_speedup():
    """Verify that canopy clearance mask lookup is at least 15x faster than linear scanning."""
    shape = (256, 256)
    bounds = (-100.0, -100.0, 100.0, 100.0)
    sync = ObstacleGridSynchronizer(shape=shape, world_bounds=bounds)
    rng = random.Random(42)
    for i in range(300):
        sync.register_flora_instance(i, 1, rng.uniform(-90, 90), rng.uniform(-90, 90), rng.uniform(0.8, 2.0))

    queries = [(rng.uniform(-90, 90), rng.uniform(-90, 90)) for _ in range(1000)]

    # Mask lookups
    t0 = time.perf_counter()
    for qx, qz in queries:
        _ = sync.is_flora_clear_for_spawn(qx, qz)
    t_opt = time.perf_counter() - t0

    # Legacy linear scan
    t0 = time.perf_counter()
    for qx, qz in queries:
        res = True
        for obs in sync.solid_obstacles:
            if math.hypot(qx - obs.x, qz - obs.z) < obs.spawn_clearance:
                res = False
                break
    t_legacy = time.perf_counter() - t0

    speedup = t_legacy / max(1e-6, t_opt)
    assert speedup >= 15.0, f"Expected >= 15x speedup, got {speedup:.1f}x (opt={t_opt*1000:.2f}ms, legacy={t_legacy*1000:.2f}ms)"


# ==============================================================================
# 3. FEATURE 11: VECTORIZED OPENMESH QUAD INDEX TOPOLOGY
# ==============================================================================

@pytest.mark.parametrize("H, W", [
    (16, 16),
    (32, 64),
    (64, 64),
    (64, 128),
    (256, 256),
])
def test_openmesh_quad_indices_exact_topology(H, W):
    """Assert vectorized meshgrid quad generation matches reference nested loop identically."""
    # 1. Vectorized logic as implemented in open_mesh.py
    iy, ix = np.meshgrid(
        np.arange(H - 1, dtype=np.uint32),
        np.arange(W - 1, dtype=np.uint32),
        indexing="ij",
    )
    v00 = iy * np.uint32(W) + ix
    v10 = v00 + np.uint32(1)
    v01 = v00 + np.uint32(W)
    v11 = v01 + np.uint32(1)

    quads = np.empty((H - 1, W - 1, 2, 3), dtype=np.uint32)
    quads[:, :, 0, 0] = v00
    quads[:, :, 0, 1] = v01
    quads[:, :, 0, 2] = v10
    quads[:, :, 1, 0] = v10
    quads[:, :, 1, 1] = v01
    quads[:, :, 1, 2] = v11
    vec_indices = quads.ravel()

    # 2. Reference nested loop
    ref_indices = ref_quad_indices(H, W)

    # Invariants
    assert len(vec_indices) == (H - 1) * (W - 1) * 6
    assert np.array_equal(vec_indices, ref_indices), f"Index topology mismatch for grid {H}x{W}"

    # Check CCW winding order for arbitrary sample quad
    sample_quad_idx = 0
    t1 = vec_indices[0:3]
    t2 = vec_indices[3:6]
    assert list(t1) == [0, W, 1]
    assert list(t2) == [1, W, W + 1]


def test_openmesh_full_terrain_generation():
    """Test full OpenWorldMesh build_geometry with vectorized indices."""
    heightfield = np.zeros((64, 64), dtype=np.float32)
    mesh = OpenWorldMesh(heightfield)
    assert mesh.indices is not None
    assert len(mesh.indices) == 63 * 63 * 6
    assert mesh.vertices.shape == (64 * 64, 3)
    assert mesh.normals.shape == (64 * 64, 3)


# ==============================================================================
# 4. FEATURES 12 & 13: EROSION THRESHOLD & SCRATCH BUFFER REUSE
# ==============================================================================

def test_hydraulic_erosion_droplet_threshold_and_throughput():
    """Verify Path 3 vectorized execution for droplet counts > 400 with high throughput."""
    hf = Heightfield2D(resolution=64)
    hf.Z += np.random.RandomState(42).normal(0.0, 1.0, (64, 64))

    cfg_large = ErosionConfig(droplet_count=2000)
    sim = ErosionSimulator(hf, config=cfg_large)

    t0 = time.perf_counter()
    new_hf, _, _ = sim.simulate_hydraulic(seed=42)
    dt = time.perf_counter() - t0

    throughput = 2000 / dt
    assert throughput > 3000, f"Throughput {throughput:.1f} drop/s is below expected 3,000 drop/s"
    assert np.all(np.isfinite(new_hf.Z)), "Hydraulic erosion produced non-finite elevation values"


def test_thermal_erosion_scratch_buffer_zero_allocation():
    """Verify persistent scratch arrays are reused across iterations without heap reallocation."""
    hf = Heightfield2D(resolution=128)
    hf.Z += np.linspace(0, 10, 128)[:, None]
    cfg = ErosionConfig(thermal_iterations=5, talus_angle_deg=35.0)
    sim = ErosionSimulator(hf, config=cfg)

    # First run: allocates buffers
    sim.run_thermal_erosion()
    id_excess_1 = id(sim._scratch_total_excess)
    id_max_1 = id(sim._scratch_max_excess)
    id_loss_1 = id(sim._scratch_volume_loss)
    id_k_1 = id(sim._scratch_excess_k)

    # Second run: must reuse exact memory pointers
    sim.run_thermal_erosion()
    assert id(sim._scratch_total_excess) == id_excess_1
    assert id(sim._scratch_max_excess) == id_max_1
    assert id(sim._scratch_volume_loss) == id_loss_1
    assert id(sim._scratch_excess_k) == id_k_1

    # Resize check: must cleanly adapt to new resolution
    hf_small = Heightfield2D(resolution=64)
    sim_small = ErosionSimulator(hf_small, config=cfg)
    sim_small._scratch_total_excess = sim._scratch_total_excess # inject mismatched buffer
    sim_small.run_thermal_erosion()
    assert sim_small._scratch_total_excess.shape == (64, 64)


# ==============================================================================
# 5. FEATURE 14: SIMULATION TICK & DOMAIN CACHING
# ==============================================================================

def test_species_domain_cache_and_resolution():
    """Verify _SPECIES_DOMAIN_CACHE stores and returns identical Domain enum objects."""
    for sp, raw in config.SPECIES_DOMAIN.items():
        dom = domain_of(sp)
        assert dom == Domain(raw)
        assert dom is _SPECIES_DOMAIN_CACHE[sp]

    # Non-configured species defaults to CAN
    assert domain_of("fictional_creature_xyz") == Domain.CAN


def test_creature_passable_caching_and_mutation():
    """Verify creature passability caching on creature instance and invalidation on trait/kit changes."""
    world = World(25, 25, random.Random(42))
    creature = SimpleNamespace(species="an_co", kit=None, traits={"speed": 2, "armor": 1})

    # Initial query sets cache
    res1 = world.passable((5, 5), creature=creature)
    assert hasattr(creature, "_cached_passable")
    cache1 = creature._cached_passable
    assert isinstance(cache1[2], frozenset)

    # Repeated query on identical creature state reuses cached frozenset
    res2 = world.passable((5, 5), creature=creature)
    assert creature._cached_passable is cache1
    assert res1 == res2

    # Trait mutation forces cache update
    creature.traits = {"speed": 10, "armor": 5}
    res3 = world.passable((5, 5), creature=creature)
    cache2 = creature._cached_passable
    assert cache2 is not cache1
    assert cache2[0] == creature.traits

    # Kit mutation forces cache update
    kit_extra = SimpleNamespace(extra_terrain=(Terrain.ROCK,), extra_domains=())
    creature.kit = kit_extra
    res4 = world.passable((5, 5), creature=creature)
    cache3 = creature._cached_passable
    assert cache3 is not cache2
    assert cache3[1] == kit_extra

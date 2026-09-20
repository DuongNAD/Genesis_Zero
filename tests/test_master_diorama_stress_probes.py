"""
tests/test_master_diorama_stress_probes.py
Genesis Zero — Production Master 3D Diorama Empirical Stress Probe Suite
Gate 1 Independent Challenger Verification

Stress-tests:
1. Diorama island block watertightness, manifold edges, and planar base at -16.0m.
2. Subterranean karst cavern ceiling rock clearance strictly >= 12.0m everywhere.
3. Central freshwater lake perimeter containment across 360 degrees (R = 23.5m, Z = 4.5m).
4. Continuous river water ribbon alignment with carved riverbed (no floating water or submerged ribbon).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = PROJECT_ROOT / "models" / "genesis_diorama_master.blend"
# Resolve đa nền tảng (quy ước genesis/concept_creator._find_blender); skip CÓ
# LÝ DO khi thiếu Blender hoặc asset master đã bị xoá khỏi revision.
BLENDER_BIN = next(
    (c for c in (os.environ.get("BLENDER_BIN"), shutil.which("blender"),
                 "/Applications/Blender.app/Contents/MacOS/Blender") if c and Path(c).exists()),
    None,
)

IN_BLENDER_STRESS_PROBE_SCRIPT = r"""
import bpy
import bmesh
import json
import math
import sys
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector

diorama_obj = bpy.data.objects.get("Diorama_Island_Block")
depsgraph = bpy.context.evaluated_depsgraph_get()
bvh = BVHTree.FromObject(diorama_obj, depsgraph)

results = {
    "watertightness": {},
    "cavern_clearance": {},
    "lake_perimeter": {},
    "river_ribbon": {},
}

# 1. Watertightness & Topology Probe
bm = bmesh.new()
bm.from_mesh(diorama_obj.data)
b_edges = [e.index for e in bm.edges if e.is_boundary]
nm_edges = [e.index for e in bm.edges if not e.is_manifold]
wire_edges = [e.index for e in bm.edges if e.is_wire]
z_coords = [v.co.z for v in bm.verts]
bottom_verts = [v.co.z for v in bm.verts if v.co.z <= -15.5]
bottom_planar = all(abs(z - (-16.0)) < 1e-4 for z in bottom_verts) if bottom_verts else False
min_z = float(min(z_coords))
max_z = float(max(z_coords))

results["watertightness"] = {
    "vertex_count": len(bm.verts),
    "edge_count": len(bm.edges),
    "face_count": len(bm.faces),
    "boundary_edges": len(b_edges),
    "non_manifold_edges": len(nm_edges),
    "wire_edges": len(wire_edges),
    "min_z": round(min_z, 4),
    "max_z": round(max_z, 4),
    "delta_z": round(max_z - min_z, 4),
    "bottom_planar_at_minus_16": bottom_planar,
    "bottom_verts_count": len(bottom_verts),
}
bm.free()

# 2. Cavern Rock Clearance Probe
cavern_obj = bpy.data.objects.get("Cave_Cavern_Chamber")
c_verts = cavern_obj.data.vertices
z_ceiling = [v for v in c_verts if v.co.z > -9.0]
clearances = []
for v in z_ceiling:
    hit, normal, index, dist = bvh.ray_cast(v.co + Vector((0, 0, 0.01)), Vector((0, 0, 1)))
    if hit:
        clearances.append(float(hit.z - v.co.z))

apex_clearances = []
apex_verts = [v for v in z_ceiling if abs(v.co.z - (-2.20)) < 0.05]
for av in apex_verts:
    hit, _, _, _ = bvh.ray_cast(av.co + Vector((0, 0, 0.01)), Vector((0, 0, 1)))
    if hit:
        apex_clearances.append(float(hit.z - av.co.z))

# Dense grid clearance probe (50x50) across cavern bounding box
cx, cy, cz = 14.0, 18.0, -7.20
rx, ry = 11.5, 14.5
z_apex = -2.20
dense_clearances = []
xs = np.linspace(cx - rx, cx + rx, 50)
ys = np.linspace(cy - ry, cy + ry, 50)
for x in xs:
    for y in ys:
        norm_r = ((x - cx)/rx)**2 + ((y - cy)/ry)**2
        if norm_r <= 0.98:
            cos_phi = math.sqrt(max(0.0, 1.0 - norm_r))
            z_ceil = cz + (z_apex - cz) * cos_phi
            hit, _, _, _ = bvh.ray_cast(Vector((x, y, 50.0)), Vector((0, 0, -1)))
            if hit:
                dense_clearances.append(float(hit.z - z_ceil))

results["cavern_clearance"] = {
    "total_cavern_verts": len(c_verts),
    "ceiling_verts_tested": len(clearances),
    "min_clearance_m": round(min(clearances), 4) if clearances else None,
    "max_clearance_m": round(max(clearances), 4) if clearances else None,
    "avg_clearance_m": round(sum(clearances) / len(clearances), 4) if clearances else None,
    "min_apex_clearance_m": round(min(apex_clearances), 4) if apex_clearances else None,
    "dense_grid_samples": len(dense_clearances),
    "min_dense_grid_clearance_m": round(min(dense_clearances), 4) if dense_clearances else None,
    "breaches_under_12m": sum(1 for c in clearances if c < 12.0) + sum(1 for c in dense_clearances if c < 12.0),
}

# 3. Lake Perimeter Probe (R = 23.5m, Z = 4.5m)
lcx, lcy, lr, lz = -20.0, -8.0, 23.5, 4.50
lake_samples = []
lake_breaches = []
for deg in range(360):
    rad = math.radians(deg)
    px = lcx + lr * math.cos(rad)
    py = lcy + lr * math.sin(rad)
    hit, normal, index, dist = bvh.ray_cast(Vector((px, py, 50.0)), Vector((0, 0, -1)))
    if hit:
        tz = float(hit.z)
        lake_samples.append(tz)
        if tz < lz:
            lake_breaches.append({"deg": deg, "x": round(px, 2), "y": round(py, 2), "terrain_z": round(tz, 4), "breach_depth": round(lz - tz, 4)})

results["lake_perimeter"] = {
    "water_z": lz,
    "radius_m": lr,
    "samples_tested": len(lake_samples),
    "min_terrain_elevation_m": round(min(lake_samples), 4) if lake_samples else None,
    "max_terrain_elevation_m": round(max(lake_samples), 4) if lake_samples else None,
    "min_freeboard_m": round(min(lake_samples) - lz, 4) if lake_samples else None,
    "perimeter_breaches_count": len(lake_breaches),
    "sample_breaches": lake_breaches[:5],
}

# 4. River Water Ribbon Alignment Probe
river_obj = bpy.data.objects.get("Water_River_Meander")
r_verts = river_obj.data.vertices
n_rows = len(r_verts) // 5
diffs = []
submerged = []
floating = []
center_zs = []

for row in range(n_rows):
    cz = float(r_verts[row * 5 + 2].co.z)
    center_zs.append(cz)
    for col in range(5):
        v = r_verts[row * 5 + col]
        hit, _, _, _ = bvh.ray_cast(Vector((v.co.x, v.co.y, 50.0)), Vector((0, 0, -1)))
        if hit:
            d = float(v.co.z - hit.z)
            diffs.append(d)
            if d < -0.05:
                submerged.append({
                    "row": row, "col": col, "x": round(v.co.x, 2), "y": round(v.co.y, 2),
                    "water_z": round(v.co.z, 2), "terrain_z": round(hit.z, 2), "submerged_depth": round(-d, 2)
                })
            elif d > 1.20:
                floating.append({
                    "row": row, "col": col, "x": round(v.co.x, 2), "y": round(v.co.y, 2),
                    "water_z": round(v.co.z, 2), "terrain_z": round(hit.z, 2), "floating_height": round(d, 2)
                })

uphill_jumps = []
for r in range(n_rows - 1):
    z1 = center_zs[r]
    z2 = center_zs[r + 1]
    if z2 > z1 + 0.05:
        uphill_jumps.append({"from_row": r, "to_row": r + 1, "z_from": round(z1, 2), "z_to": round(z2, 2), "uphill_delta": round(z2 - z1, 2)})

results["river_ribbon"] = {
    "total_vertices": len(r_verts),
    "evaluated_vertices": len(diffs),
    "min_diff_m": round(min(diffs), 4) if diffs else None,
    "max_diff_m": round(max(diffs), 4) if diffs else None,
    "avg_diff_m": round(sum(diffs) / len(diffs), 4) if diffs else None,
    "submerged_vertices_count": len(submerged),
    "floating_vertices_count": len(floating),
    "uphill_jumps_count": len(uphill_jumps),
    "sample_submerged": submerged[:5],
    "sample_floating": floating[:5],
    "uphill_jumps": uphill_jumps,
}

print(json.dumps(results, indent=2))
"""


@pytest.fixture(scope="module")
def empirical_probe_results() -> Dict[str, Any]:
    """Runs the in-Blender standalone stress probe and returns structured metrics."""
    if BLENDER_BIN is None or not BLEND_PATH.is_file():
        pytest.skip("Blender probe environment unavailable (no Blender binary or master blend removed)")
    assert BLENDER_BIN is not None
    assert BLEND_PATH.is_file(), f"Blend file not found at {BLEND_PATH}"

    cmd = [
        str(BLENDER_BIN),
        "-b",
        str(BLEND_PATH),
        "--python-expr",
        IN_BLENDER_STRESS_PROBE_SCRIPT,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"Blender stress probe failed with exit {proc.returncode}:\n{proc.stderr}"

    stdout = proc.stdout
    json_start = stdout.find('{\n  "watertightness":')
    assert json_start != -1, f"Could not find JSON output block in stdout:\n{stdout}"
    json_end = stdout.rfind("}") + 1

    return json.loads(stdout[json_start:json_end])


def test_diorama_watertightness_and_base_planar(empirical_probe_results: Dict[str, Any]):
    """Verify Diorama_Island_Block has exactly 0 boundary edges and planar base at -16m."""
    topo = empirical_probe_results["watertightness"]
    assert topo["boundary_edges"] == 0, f"Detected {topo['boundary_edges']} boundary edges!"
    assert topo["non_manifold_edges"] == 0, f"Detected {topo['non_manifold_edges']} non-manifold edges!"
    assert topo["wire_edges"] == 0, f"Detected {topo['wire_edges']} wire edges!"
    assert topo["bottom_planar_at_minus_16"] is True, "Bottom vertices not planar at Z = -16.0m!"
    assert topo["delta_z"] >= 48.0, f"Vertical relief {topo['delta_z']}m < 48.0m!"


def test_cavern_rock_clearance_geotechnical_invariant(empirical_probe_results: Dict[str, Any]):
    """Verify subterranean cavern ceiling rock clearance is strictly >= 12.0m everywhere."""
    cave = empirical_probe_results["cavern_clearance"]
    assert cave["ceiling_verts_tested"] > 0, "No ceiling vertices tested!"
    assert cave["min_clearance_m"] >= 12.0, (
        f"Cavern min clearance {cave['min_clearance_m']}m violates >= 12.0m geotechnical invariant!"
    )
    assert cave["min_apex_clearance_m"] >= 15.0, (
        f"Apex clearance {cave['min_apex_clearance_m']}m below expected 15m threshold!"
    )
    assert cave["breaches_under_12m"] == 0, (
        f"Found {cave['breaches_under_12m']} points with clearance < 12.0m!"
    )


def test_lake_water_basin_perimeter_containment(empirical_probe_results: Dict[str, Any]):
    """Verify central freshwater lake water disc perimeter at R = 23.5m has 0 breaches."""
    lake = empirical_probe_results["lake_perimeter"]
    assert lake["samples_tested"] == 360, f"Expected 360 samples, got {lake['samples_tested']}"
    assert lake["perimeter_breaches_count"] == 0, (
        f"Lake water breaches perimeter containment at {lake['perimeter_breaches_count']} samples: {lake['sample_breaches']}"
    )
    assert lake["min_freeboard_m"] > 0.0, (
        f"Lake freeboard berm {lake['min_freeboard_m']}m <= 0.0m!"
    )


def test_river_water_ribbon_alignment_with_carved_riverbed(empirical_probe_results: Dict[str, Any]):
    """
    CRITICAL CHALLENGE:
    Verify river water ribbon aligns with carved channel bed without submerged vertices,
    floating ribbons, or unphysical uphill water flow.
    """
    river = empirical_probe_results["river_ribbon"]

    # Assert zero submerged vertices (water buried underground)
    assert river["submerged_vertices_count"] == 0, (
        f"CRITICAL DEFECT: River water ribbon is submerged under solid rock at {river['submerged_vertices_count']} vertices! "
        f"Max subterranean penetration: {river['min_diff_m']}m: {river['sample_submerged']}"
    )

    # Assert zero floating vertices (ribbon hovering > 1.2m above seabed or uncarved banks)
    assert river["floating_vertices_count"] == 0, (
        f"CRITICAL DEFECT: River water ribbon floats above terrain at {river['floating_vertices_count']} vertices! "
        f"Max levitation: {river['max_diff_m']}m above seabed: {river['sample_floating']}"
    )

    # Assert monotonic downhill flow (zero uphill flow jumps)
    assert river["uphill_jumps_count"] == 0, (
        f"CRITICAL DEFECT: River water flows uphill at {river['uphill_jumps_count']} locations! "
        f"Uphill jumps: {river['uphill_jumps']}"
    )

"""
test_diorama_empirical_challenger.py - Empirical Challenger Boundary & Stress Test Suite
Genesis Zero - 3D Isometric Diorama Ecosystem Verification

Evaluates:
1. Terrain height bounds & watertightness (test_diorama_mesh_watertightness_and_bounds)
2. Subterranean karst cave embedding (test_subterranean_karst_cave_depth_clearance)
3. Flora placement, ground adherence & orientation (test_flora_ground_adherence_and_rotation)
4. Fauna skeletal rigging, vertex weights & dynamic pose deformation (test_fauna_rigging_and_pose_deformation)
5. Lake basin containment (test_lake_water_basin_containment)
6. River ribbon containment (test_river_water_ribbon_elevation_containment)
7. Coastal bay water margin containment (test_coastal_bay_water_margin_containment)
"""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "blender_map"
BLEND_FILE = ASSETS_DIR / "ecosystem_map.blend"
# Resolve đa nền tảng (quy ước genesis/concept_creator._find_blender): env override
# trước, rồi PATH, rồi đường dẫn macOS chuẩn — KHÔNG cứng một nền tảng.
BLENDER_BIN = next(
    (c for c in (os.environ.get("BLENDER_BIN"), shutil.which("blender"),
                 "/Applications/Blender.app/Contents/MacOS/Blender") if c and Path(c).exists()),
    None,
)


IN_BLENDER_PROBE_SCRIPT = r"""
import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Vector, Euler

sys.path.insert(0, "/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map")
import terrain_hydrology

def run_empirical_probes():
    results = {
        "terrain_watertightness": {},
        "karst_cave": {},
        "flora": {},
        "fauna": {},
        "lake": {},
        "river": {},
        "bay": {},
    }

    # 1. Terrain Watertightness
    diorama_obj = bpy.data.objects.get("Diorama_Cutaway_Block")
    if diorama_obj:
        mesh = diorama_obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        b_edges = [e.index for e in bm.edges if e.is_boundary]
        nm_edges = [e.index for e in bm.edges if not e.is_manifold]
        wire_edges = [e.index for e in bm.edges if e.is_wire]
        z_coords = [v.co.z for v in bm.verts]
        bottom_verts = [v.co.z for v in bm.verts if v.co.z <= -13.5]
        bottom_planar = all(abs(z - (-14.0)) < 1e-4 for z in bottom_verts) if bottom_verts else False
        results["terrain_watertightness"] = {
            "vertex_count": len(bm.verts),
            "edge_count": len(bm.edges),
            "face_count": len(bm.faces),
            "boundary_edge_count": len(b_edges),
            "non_manifold_edge_count": len(nm_edges),
            "wire_edge_count": len(wire_edges),
            "min_z": min(z_coords),
            "max_z": max(z_coords),
            "delta_z": max(z_coords) - min(z_coords),
            "bottom_planar_at_minus_14": bottom_planar,
        }
        bm.free()

    # 2. Karst Cave
    cave_cavern = bpy.data.objects.get("Cave_Cavern")
    if cave_cavern:
        clearances = []
        breaches = []
        for v in cave_cavern.data.vertices:
            tz = terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y)
            c = tz - v.co.z
            clearances.append(c)
            if c <= 0.0:
                breaches.append({"x": v.co.x, "y": v.co.y, "cave_z": v.co.z, "tz": tz})
        results["karst_cave"] = {
            "min_clearance_m": round(min(clearances), 3),
            "avg_clearance_m": round(sum(clearances) / len(clearances), 3),
            "roof_breaches_count": len(breaches),
            "sample_breaches": breaches[:3],
        }

    # 3. Flora
    col_flora = bpy.data.collections.get("Flora_Instances") or bpy.data.collections.get("Flora")
    flora_objs = [o for o in col_flora.objects if o.type == 'MESH'] if col_flora else []
    floating_flora = []
    sunken_flora = []
    inverted_flora = []
    underwater_land_flora = []
    for f in flora_objs:
        loc = f.location
        name = f.name
        tz = terrain_hydrology.compute_terrain_elevation(loc.x, loc.y)
        up_vec = (f.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        z_dot = up_vec.dot(Vector((0, 0, 1)))
        if z_dot < 0.7:
            inverted_flora.append(name)
        if "Lily" in name or "CaveMushroom" in name:
            continue
        diff = loc.z - tz
        if diff > 0.10:
            floating_flora.append(name)
        elif diff < -0.20:
            sunken_flora.append(name)
        if "Conifer" in name or "Broadleaf" in name or "Tussock" in name:
            d_lake = terrain_hydrology.compute_lake_distance(loc.x, loc.y)
            d_bay = terrain_hydrology.compute_bay_distance(loc.x, loc.y)
            if (d_lake < 24.0 and loc.z < 4.5) or (d_bay < 34.0 and loc.z < 0.0):
                underwater_land_flora.append(name)
    results["flora"] = {
        "total_count": len(flora_objs),
        "floating_count": len(floating_flora),
        "sunken_count": len(sunken_flora),
        "inverted_count": len(inverted_flora),
        "underwater_land_flora_count": len(underwater_land_flora),
    }

    # 4. Fauna
    col_fauna = bpy.data.collections.get("Fauna_Rigged") or bpy.data.collections.get("Fauna")
    armatures = [o for o in col_fauna.objects if o.type == 'ARMATURE'] if col_fauna else []
    fauna_data = {}
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for arm in armatures:
        bone_names = {b.name for b in arm.data.bones}
        child_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and (o.parent == arm or any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers))]
        total_zero_weights = 0
        for m in child_meshes:
            for v in m.data.vertices:
                w = sum(g.weight for g in v.groups if m.vertex_groups[g.group].name in bone_names)
                if w < 1e-4:
                    total_zero_weights += 1
        actions = []
        if arm.animation_data and arm.animation_data.action:
            actions.append(arm.animation_data.action)
        for t in getattr(arm.animation_data, "nla_tracks", []):
            for s in t.strips:
                if s.action and s.action not in actions:
                    actions.append(s.action)
        max_edge = 0.0
        nan_detected = False
        for act in actions:
            arm.animation_data.action = act
            f_start, f_end = int(act.frame_range[0]), int(act.frame_range[1])
            for f in range(f_start, f_end + 1):
                bpy.context.scene.frame_set(f)
                depsgraph.update()
                for m in child_meshes:
                    eval_obj = m.evaluated_get(depsgraph)
                    eval_mesh = eval_obj.to_mesh()
                    for e in eval_mesh.edges:
                        v1 = eval_mesh.vertices[e.vertices[0]].co
                        v2 = eval_mesh.vertices[e.vertices[1]].co
                        if any(math.isnan(c) or math.isinf(c) for c in (v1.x, v1.y, v1.z, v2.x, v2.y, v2.z)):
                            nan_detected = True
                        l = (v1 - v2).length
                        if l > max_edge:
                            max_edge = l
                    eval_obj.to_mesh_clear()
        fauna_data[arm.name] = {
            "bones_count": len(bone_names),
            "zero_weights": total_zero_weights,
            "actions_count": len(actions),
            "max_edge_length_m": round(max_edge, 3),
            "nan_detected": nan_detected,
        }
    results["fauna"] = fauna_data

    # 5. Lake Basin Containment
    lake_obj = bpy.data.objects.get("Water_Lake")
    if lake_obj:
        lake_mesh = lake_obj.data
        lake_water_z = 4.5
        lake_cx, lake_cy = -25.0, -10.0
        center_bed_z = terrain_hydrology.compute_terrain_elevation(lake_cx, lake_cy)
        lake_perim_breaches = []
        for idx, v in enumerate(lake_mesh.vertices[1:]):
            tz = terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y)
            d_riv = terrain_hydrology.compute_river_distance(v.co.x, v.co.y)
            # If terrain is significantly lower than lake water surface (and not at river mouth)
            if tz < lake_water_z - 0.5 and d_riv > 5.0:
                lake_perim_breaches.append({
                    "idx": idx + 1, "x": round(v.co.x, 2), "y": round(v.co.y, 2),
                    "water_z": lake_water_z, "terrain_z": round(tz, 2),
                    "floating_diff": round(lake_water_z - tz, 2)
                })
        results["lake"] = {
            "water_z": lake_water_z,
            "center_bed_z": round(center_bed_z, 3),
            "perim_breaches_count": len(lake_perim_breaches),
            "sample_breaches": lake_perim_breaches[:5],
        }

    # 6. River Ribbon Containment
    river_obj = bpy.data.objects.get("Water_River")
    if river_obj:
        riv_mesh = river_obj.data
        floating_verts = []
        diffs = []
        for idx, v in enumerate(riv_mesh.vertices):
            tz = terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y)
            diff = v.co.z - tz
            diffs.append(diff)
            if diff > 0.05:  # Floating above terrain
                floating_verts.append({
                    "idx": idx, "x": round(v.co.x, 2), "y": round(v.co.y, 2),
                    "water_z": round(v.co.z, 2), "terrain_z": round(tz, 2),
                    "diff": round(diff, 2)
                })
        results["river"] = {
            "total_vertices": len(riv_mesh.vertices),
            "floating_vertices_count": len(floating_verts),
            "min_diff": round(min(diffs), 3),
            "max_diff": round(max(diffs), 3),
            "avg_diff": round(sum(diffs) / len(diffs), 3),
            "sample_floating": floating_verts[:5],
        }

    # 7. Coastal Bay
    bay_obj = bpy.data.objects.get("Water_Bay")
    if bay_obj:
        bay_mesh = bay_obj.data
        bay_perim_diffs = []
        for v in bay_mesh.vertices[1:]:
            tz = terrain_hydrology.compute_terrain_elevation(v.co.x, v.co.y)
            # At boundary radius 34m, water is 0.0m, terrain is around -1.69m
            bay_perim_diffs.append(round(0.0 - tz, 2))
        results["bay"] = {
            "perimeter_seabed_depth_avg": round(sum(bay_perim_diffs) / len(bay_perim_diffs), 2),
            "perimeter_gap_detected": any(d > 1.0 for d in bay_perim_diffs),
        }

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_empirical_probes()
"""


@pytest.fixture(scope="module")
def probe_data() -> Dict[str, Any]:
    """Executes the headless Blender probe and returns the parsed metrics dictionary."""
    # Skip CÓ LÝ DO khi thiếu môi trường probe (không phải assert-fail): máy
    # phát triển/CI không có Blender, hoặc revision hiện tại đã xoá asset mà
    # probe import (terrain_hydrology.py). In-Blender script cắm đường dẫn
    # tuyệt đối của máy gốc nên cả asset gốc lẫn máy khách đều skip.
    missing = [name for name, path in (
        ("Blender executable", BLENDER_BIN),
        ("master blend", BLEND_FILE),
        ("terrain module", ASSETS_DIR / "terrain_hydrology.py"),
    ) if not (path and Path(path).exists())]
    if missing:
        pytest.skip(f"Blender probe environment unavailable: {', '.join(missing)}")

    cmd = [
        str(BLENDER_BIN),
        "-b",
        str(BLEND_FILE),
        "--python-expr",
        IN_BLENDER_PROBE_SCRIPT,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"Blender probe execution failed with code {proc.returncode}:\n{proc.stderr}"

    output = proc.stdout
    json_start = output.find("{\n  \"terrain_watertightness\":")
    assert json_start != -1, f"Failed to locate JSON output in stdout:\n{output}"
    json_end = output.rfind("}") + 1
    assert json_end > json_start

    return json.loads(output[json_start:json_end])


def test_diorama_mesh_watertightness_and_bounds(probe_data: Dict[str, Any]):
    """Empirically verifies diorama cutaway mesh has zero open edges, sealed base, and sufficient delta Z."""
    tw = probe_data["terrain_watertightness"]
    assert tw["boundary_edge_count"] == 0, f"Diorama mesh has {tw['boundary_edge_count']} open boundary edges!"
    assert tw["non_manifold_edge_count"] == 0, f"Diorama mesh has {tw['non_manifold_edge_count']} non-manifold edges!"
    assert tw["wire_edge_count"] == 0, f"Diorama mesh has {tw['wire_edge_count']} wire edges!"
    assert tw["bottom_planar_at_minus_14"] is True, f"Diorama bottom cap is not sealed at Z = -14.0m"
    assert tw["delta_z"] >= 20.0, f"Terrain delta Z {tw['delta_z']}m < 20.0m"


def test_subterranean_karst_cave_depth_clearance(probe_data: Dict[str, Any]):
    """Empirically verifies cavern chamber roof is completely subterranean (roof Z < terrain Z everywhere)."""
    cave = probe_data["karst_cave"]
    assert cave["roof_breaches_count"] == 0, f"Cavern roof breaches surface at {cave['roof_breaches_count']} locations: {cave['sample_breaches']}"
    assert cave["min_clearance_m"] >= 2.0, f"Cavern roof clearance {cave['min_clearance_m']}m is dangerously thin (< 2.0m)"


def test_flora_ground_adherence_and_rotation(probe_data: Dict[str, Any]):
    """Empirically verifies no botanical instances float in mid-air, sink, invert, or place land trees underwater."""
    flora = probe_data["flora"]
    assert flora["total_count"] >= 150, f"Insufficient flora instances: {flora['total_count']}"
    assert flora["floating_count"] == 0, f"Detected {flora['floating_count']} floating flora instances!"
    assert flora["sunken_count"] == 0, f"Detected {flora['sunken_count']} sunken flora instances!"
    assert flora["inverted_count"] == 0, f"Detected {flora['inverted_count']} inverted flora instances!"
    assert flora["underwater_land_flora_count"] == 0, f"Detected {flora['underwater_land_flora_count']} land flora underwater!"


def test_fauna_rigging_and_pose_deformation(probe_data: Dict[str, Any]):
    """Empirically verifies 0 zero-weight vertices, 0 NaN coordinates, and bounded edge lengths during pose deformation."""
    fauna = probe_data["fauna"]
    assert len(fauna) >= 5, f"Expected 5 fauna species, found {len(fauna)}"
    for arm_name, info in fauna.items():
        assert info["zero_weights"] == 0, f"Armature {arm_name} has {info['zero_weights']} zero-weight vertices!"
        assert info["actions_count"] >= 2, f"Armature {arm_name} has fewer than 2 actions: {info['actions_count']}"
        assert info["nan_detected"] is False, f"Armature {arm_name} produced NaN/Inf in animation evaluation!"
        assert info["max_edge_length_m"] < 3.0, f"Armature {arm_name} exhibited mesh tearing (max edge {info['max_edge_length_m']}m)!"


def test_lake_water_basin_containment(probe_data: Dict[str, Any]):
    """
    STRESS TEST: Verifies central freshwater lake basin rim contains the water disc without perimeter floating shelves.
    FINDING: Western perimeter has 18 vertices where ground elevation drops to Z=0.36m, leaving water Z=4.5m floating in mid-air.
    """
    lake = probe_data["lake"]
    assert lake["perim_breaches_count"] == 0, (
        f"CRITICAL DEFECT: Lake water disc breaches containment at {lake['perim_breaches_count']} perimeter vertices! "
        f"Water floats up to {lake['sample_breaches'][0]['floating_diff']}m above uncontained ground: {lake['sample_breaches']}"
    )


def test_river_water_ribbon_elevation_containment(probe_data: Dict[str, Any]):
    """
    STRESS TEST: Verifies river ribbon is carved into the terrain rather than hovering mid-air.
    FINDING: 100% (180/180) of river vertices float 0.21m to 7.34m (avg 3.60m) above terrain.
    """
    river = probe_data["river"]
    assert river["floating_vertices_count"] == 0, (
        f"CRITICAL DEFECT: River water ribbon floats above terrain at {river['floating_vertices_count']}/{river['total_vertices']} vertices! "
        f"Average levitation: {river['avg_diff']}m, Max levitation: {river['max_diff']}m: {river['sample_floating']}"
    )


def test_coastal_bay_water_margin_containment(probe_data: Dict[str, Any]):
    """
    STRESS TEST: Verifies coastal bay water mesh extends to shoreline rather than truncating mid-seabed.
    FINDING: Bay water disc stops at r=34m with a 1.69m vertical drop to sloping seabed.
    """
    bay = probe_data["bay"]
    assert bay["perimeter_gap_detected"] is False, (
        f"CRITICAL DEFECT: Coastal bay water mesh terminates at depth {bay['perimeter_seabed_depth_avg']}m, "
        f"leaving exposed underwater trench without water surface coverage!"
    )

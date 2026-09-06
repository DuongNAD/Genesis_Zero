"""
Genesis Zero — 4-Tier Opaque-Box E2E Test Suite for 3D Ecological Environment Map.

Authoritative Requirements Source:
- ORIGINAL_REQUEST.md (§ 2026-09-03T16:45:06Z, R1-R5, Acceptance Criteria 110-126)
- TEST_INFRA.md (§ Feature Inventory & Real-World Application Scenarios)
- PROJECT.md (§ Architecture, Milestones, and Interface Contracts)

Test Architecture:
- Tier 1: Feature Coverage (existence of deliverables, 6 collections, terrain, water, flora, fauna, lights, camera)
- Tier 2: Boundary & Corner Cases (elevation delta >= 15m, span in [100, 500]m, use_smooth True, GLB size > 100KB, keyframes >= 20, loopable)
- Tier 3: Cross-Feature Combinations (flora bounded to terrain elevation, water in depressions, armature modifiers, lighting viewport coverage)
- Tier 4: Real-World Scenarios (headless verify script execution, glTF 2.0 chunk/animation parse, high-res render validation)
"""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

# Target Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "blender_map"
BLEND_FILE = ASSETS_DIR / "ecosystem_map.blend"
GLB_FILE = ASSETS_DIR / "ecosystem_map.glb"
PREVIEW_FILE = ASSETS_DIR / "render_preview.png"
VERIFY_SCRIPT = ASSETS_DIR / "verify_ecosystem.py"
BLENDER_BIN = Path("/Applications/Blender.app/Contents/MacOS/Blender")

# Invariant Thresholds
REQUIRED_COLLECTIONS = frozenset({"Terrain", "Water", "Flora", "Fauna", "Lighting", "Camera"})
TERRAIN_MIN_DELTA_Z = 15.0
TERRAIN_SPAN_MIN = 100.0
TERRAIN_SPAN_MAX = 500.0
MIN_GLB_BYTES = 100 * 1024  # 100 KB
MIN_IMAGE_WIDTH = 1280
MIN_IMAGE_HEIGHT = 720
MIN_ACTION_FRAMES = 20
MIN_ARMATURE_BONES = 10


# -----------------------------------------------------------------------------
# Headless Blender Inspection Helper & Fixture
# -----------------------------------------------------------------------------

INSPECT_BLEND_SCRIPT = r"""
import bpy
import json
import mathutils

def inspect():
    out = {}

    # 1. Collections
    out["collection_names"] = list(bpy.data.collections.keys())
    out["collections"] = {}
    for col in bpy.data.collections:
        objs = []
        for obj in col.objects:
            objs.append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(c, 3) for c in obj.location],
                "dimensions": [round(c, 3) for c in obj.dimensions],
            })
        out["collections"][col.name] = objs

    # 2. Terrain
    col_terrain = bpy.data.collections.get("Terrain")
    t_objs = [o for o in (col_terrain.objects if col_terrain else []) if o.type == 'MESH']
    if not t_objs:
        t_objs = [o for o in bpy.data.objects if o.type == 'MESH' and "terrain" in o.name.lower()]

    if t_objs:
        t = t_objs[0]
        mesh = t.data
        verts = mesh.vertices
        z_vals = [v.co.z for v in verts] if len(verts) > 0 else [0.0]
        bbox = [t.matrix_world @ mathutils.Vector(corner) for corner in t.bound_box]
        xs = [v.x for v in bbox]
        ys = [v.y for v in bbox]
        zs = [v.z for v in bbox]
        out["terrain"] = {
            "name": t.name,
            "dimensions": [round(t.dimensions.x, 3), round(t.dimensions.y, 3), round(t.dimensions.z, 3)],
            "vertex_count": len(verts),
            "polygon_count": len(mesh.polygons),
            "min_z": round(min(z_vals), 3),
            "max_z": round(max(z_vals), 3),
            "delta_z": round(max(z_vals) - min(z_vals), 3),
            "span_x": round(max(xs) - min(xs), 3),
            "span_y": round(max(ys) - min(ys), 3),
            "span_z": round(max(zs) - min(zs), 3),
            "materials": [m.name for m in t.data.materials if m],
            "has_color_attributes": bool(hasattr(mesh, "color_attributes") and len(mesh.color_attributes) > 0),
        }
    else:
        out["terrain"] = None

    # 3. Water
    col_water = bpy.data.collections.get("Water")
    w_objs = [o for o in (col_water.objects if col_water else []) if o.type == 'MESH']
    if not w_objs:
        w_objs = [o for o in bpy.data.objects if o.type == 'MESH' and "water" in o.name.lower()]

    out["water"] = []
    for w in w_objs:
        mats = []
        for m in w.data.materials:
            if not m:
                continue
            mat_info = {
                "name": m.name,
                "has_nodes": bool(getattr(m, "node_tree", None)),
                "transmission": 0.0,
                "ior": 1.0,
                "roughness": 0.0,
                "has_volume_absorption": False,
            }
            if getattr(m, "node_tree", None):
                for node in m.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        trans = node.inputs.get("Transmission Weight") or node.inputs.get("Transmission")
                        ior = node.inputs.get("IOR")
                        rough = node.inputs.get("Roughness")
                        mat_info["transmission"] = trans.default_value if trans else 0.0
                        mat_info["ior"] = ior.default_value if ior else 1.0
                        mat_info["roughness"] = rough.default_value if rough else 0.0
                    elif node.type == 'VOLUME_ABSORPTION':
                        mat_info["has_volume_absorption"] = True
            mats.append(mat_info)

        z_vals = [v.co.z for v in w.data.vertices] if len(w.data.vertices) > 0 else [0.0]
        out["water"].append({
            "name": w.name,
            "dimensions": [round(c, 3) for c in w.dimensions],
            "location": [round(c, 3) for c in w.location],
            "vertex_count": len(w.data.vertices),
            "min_z": round(min(z_vals), 3),
            "max_z": round(max(z_vals), 3),
            "materials": mats,
        })

    # 4. Flora
    col_flora = bpy.data.collections.get("Flora")
    f_objs = [o for o in (col_flora.objects if col_flora else []) if o.type == 'MESH']
    species_set = set()
    flora_list = []
    non_smooth_flora = []

    for f in f_objs:
        parts = f.name.split("_")
        if len(parts) >= 2 and parts[0].lower() == "flora":
            s_name = parts[1]
        else:
            s_name = parts[0]
        species_set.add(s_name)

        polys = f.data.polygons
        smooth_count = sum(1 for p in polys if p.use_smooth)
        total_count = len(polys)
        is_smooth = (smooth_count == total_count) if total_count > 0 else True
        if not is_smooth:
            non_smooth_flora.append(f.name)

        flora_list.append({
            "name": f.name,
            "species": s_name,
            "location": [round(c, 3) for c in f.location],
            "dimensions": [round(c, 3) for c in f.dimensions],
            "polygon_count": total_count,
            "is_smooth": is_smooth,
        })

    out["flora"] = {
        "count": len(f_objs),
        "species": list(species_set),
        "species_count": len(species_set),
        "non_smooth_count": len(non_smooth_flora),
        "non_smooth_names": non_smooth_flora[:5],
        "objects": flora_list,
    }

    # 5. Fauna
    col_fauna = bpy.data.collections.get("Fauna")
    fauna_objs = col_fauna.objects if col_fauna else []
    armatures = [o for o in fauna_objs if o.type == 'ARMATURE']
    if not armatures:
        armatures = [o for o in bpy.data.objects if o.type == 'ARMATURE']

    def get_action_fcurves(act):
        curves = []
        if hasattr(act, 'fcurves'):
            return list(act.fcurves)
        if hasattr(act, 'layers'):
            for layer in act.layers:
                for strip in getattr(layer, 'strips', []):
                    for cb in getattr(strip, 'channelbags', []):
                        for fc in getattr(cb, 'fcurves', []):
                            curves.append(fc)
        return curves

    out["fauna"] = []
    for arm in armatures:
        arm_info = {
            "name": arm.name,
            "bones": [b.name for b in arm.data.bones],
            "bone_count": len(arm.data.bones),
            "actions": [],
            "active_action": arm.animation_data.action.name if (arm.animation_data and arm.animation_data.action) else None,
            "nla_tracks": [t.name for t in arm.animation_data.nla_tracks] if arm.animation_data else [],
            "child_meshes": [],
        }

        # Find deformed child meshes
        for o in bpy.data.objects:
            if o.type == 'MESH':
                has_arm_mod = any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers)
                if o.parent == arm or has_arm_mod:
                    polys = o.data.polygons
                    smooth_count = sum(1 for p in polys if p.use_smooth)
                    is_smooth = (smooth_count == len(polys)) if len(polys) > 0 else True
                    vgroups = [vg.name for vg in o.vertex_groups]
                    arm_info["child_meshes"].append({
                        "name": o.name,
                        "vertex_count": len(o.data.vertices),
                        "polygon_count": len(polys),
                        "is_smooth": is_smooth,
                        "vertex_groups": vgroups,
                        "has_armature_modifier": has_arm_mod,
                    })

        # Actions
        actions_to_check = set()
        if arm.animation_data and arm.animation_data.action:
            actions_to_check.add(arm.animation_data.action)
        if arm.animation_data:
            for track in arm.animation_data.nla_tracks:
                for strip in track.strips:
                    if strip.action:
                        actions_to_check.add(strip.action)

        for act in actions_to_check:
            f_range = act.frame_range
            f_start = int(f_range[0])
            f_end = int(f_range[1])
            f_count = f_end - f_start + 1

            is_loop = True
            for fcurve in get_action_fcurves(act):
                kfs = [kp for kp in fcurve.keyframe_points if int(round(kp.co[0])) in (f_start, f_end)]
                if len(kfs) >= 2:
                    val_start = [kp.co[1] for kp in kfs if int(round(kp.co[0])) == f_start]
                    val_end = [kp.co[1] for kp in kfs if int(round(kp.co[0])) == f_end]
                    if val_start and val_end and abs(val_start[0] - val_end[0]) > 0.08:
                        is_loop = False
                        break

            arm_info["actions"].append({
                "name": act.name,
                "frame_start": f_start,
                "frame_end": f_end,
                "frame_count": f_count,
                "is_loopable": is_loop,
            })

        out["fauna"].append(arm_info)

    # 6. Lighting
    col_light = bpy.data.collections.get("Lighting")
    light_objs = [o for o in (col_light.objects if col_light else []) if o.type == 'LIGHT']
    if not light_objs:
        light_objs = [o for o in bpy.data.objects if o.type == 'LIGHT']

    out["lighting"] = []
    for l in light_objs:
        out["lighting"].append({
            "name": l.name,
            "light_type": l.data.type,
            "energy": l.data.energy,
            "color": [round(c, 3) for c in l.data.color],
        })

    # 7. World
    w = bpy.context.scene.world
    out["world"] = {
        "name": w.name if w else None,
        "has_nodes": w.use_nodes if w else False,
    }

    # 8. Camera
    col_cam = bpy.data.collections.get("Camera")
    cam_objs = [o for o in (col_cam.objects if col_cam else []) if o.type == 'CAMERA']
    if not cam_objs:
        cam_objs = [o for o in bpy.data.objects if o.type == 'CAMERA']

    scene_cam = bpy.context.scene.camera
    out["camera"] = []
    for c in cam_objs:
        out["camera"].append({
            "name": c.name,
            "location": [round(v, 3) for v in c.location],
            "rotation_euler": [round(v, 3) for v in c.rotation_euler],
            "focal_length": c.data.lens,
            "clip_end": c.data.clip_end,
            "is_scene_camera": (c == scene_cam),
        })

    # 9. Diorama & Cave collections
    col_dio = bpy.data.collections.get("Diorama_Block")
    out["diorama_block"] = [o.name for o in col_dio.objects] if col_dio else []

    col_cave = bpy.data.collections.get("Subterranean_Cave")
    out["subterranean_cave"] = [o.name for o in col_cave.objects] if col_cave else []

    # 10. Geometry Nodes Modifiers & Node Groups
    out["nodes_modifiers"] = [o.name for o in bpy.data.objects for m in o.modifiers if m.type == 'NODES']
    out["node_groups"] = [ng.name for ng in bpy.data.node_groups if ng.type == 'GEOMETRY']

    print("__BLEND_DATA_START__")
    print(json.dumps(out))
    print("__BLEND_DATA_END__")

inspect()
"""


@pytest.fixture(scope="module")
def blend_scene_data() -> dict[str, Any]:
    """Execute headless Blender inspection script against ecosystem_map.blend and cache metadata."""
    if not BLEND_FILE.exists():
        pytest.fail(f"Deliverable ecosystem_map.blend not found at {BLEND_FILE}")

    cmd = [
        str(BLENDER_BIN),
        "--background",
        str(BLEND_FILE),
        "--python-expr",
        INSPECT_BLEND_SCRIPT,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, (
        f"Blender inspection exited with code {proc.returncode}.\nStderr: {proc.stderr}\nStdout: {proc.stdout}"
    )

    stdout = proc.stdout
    start_tag = "__BLEND_DATA_START__"
    end_tag = "__BLEND_DATA_END__"

    assert start_tag in stdout and end_tag in stdout, (
        f"Blender output missing JSON markers.\nStdout: {stdout[:1000]}"
    )

    json_str = stdout.split(start_tag)[1].split(end_tag)[0].strip()
    return json.loads(json_str)


@pytest.fixture(scope="module")
def glb_metadata() -> dict[str, Any]:
    """Parse glTF 2.0 binary chunks from ecosystem_map.glb and extract structure."""
    if not GLB_FILE.exists():
        pytest.fail(f"Deliverable ecosystem_map.glb not found at {GLB_FILE}")

    file_size = GLB_FILE.stat().st_size
    with open(GLB_FILE, "rb") as f:
        header = f.read(12)
        assert len(header) == 12, "GLB header truncated"
        magic, version, length = struct.unpack("<4sII", header)
        assert magic == b"glTF", f"Invalid GLB magic bytes: {magic!r}"
        assert version == 2, f"Expected glTF 2.0, got version {version}"
        assert length == file_size, f"GLB header length {length} does not match file size {file_size}"

        # Parse Chunk 0 (JSON)
        chunk0_header = f.read(8)
        assert len(chunk0_header) == 8, "GLB chunk 0 header truncated"
        chunk0_len, chunk0_type = struct.unpack("<II", chunk0_header)
        assert chunk0_type == 0x4E4F534A, f"Expected JSON chunk (0x4E4F534A), got {hex(chunk0_type)}"

        chunk0_bytes = f.read(chunk0_len)
        assert len(chunk0_bytes) == chunk0_len, "GLB JSON chunk data truncated"
        json_meta = json.loads(chunk0_bytes.decode("utf-8"))

        # Check Chunk 1 (BIN buffer, if present)
        has_bin = False
        bin_len = 0
        chunk1_header = f.read(8)
        if len(chunk1_header) == 8:
            chunk1_len, chunk1_type = struct.unpack("<II", chunk1_header)
            if chunk1_type == 0x004E4942:  # b'BIN\x00'
                has_bin = True
                bin_len = chunk1_len

    return {
        "file_size": file_size,
        "json": json_meta,
        "has_bin_chunk": has_bin,
        "bin_chunk_len": bin_len,
    }


@pytest.fixture(scope="module")
def preview_image_data() -> dict[str, Any]:
    """Inspect render_preview.png using Pillow and compute image statistics."""
    if not PREVIEW_FILE.exists():
        pytest.fail(f"Deliverable render_preview.png not found at {PREVIEW_FILE}")

    file_size = PREVIEW_FILE.stat().st_size
    img = Image.open(PREVIEW_FILE)
    width, height = img.size
    mode = img.mode

    arr = np.array(img)
    std_dev = float(np.std(arr))
    mean_val = float(np.mean(arr))

    # Detect magenta/pink missing texture error artifact (R > 220, G < 50, B > 220)
    magenta_ratio = 0.0
    if len(arr.shape) == 3 and arr.shape[2] >= 3:
        r = arr[:, :, 0]
        g = arr[:, :, 1]
        b = arr[:, :, 2]
        magenta_mask = (r > 220) & (g < 50) & (b > 220)
        magenta_ratio = float(np.sum(magenta_mask) / (width * height))

    return {
        "file_size": file_size,
        "width": width,
        "height": height,
        "mode": mode,
        "std_dev": std_dev,
        "mean_val": mean_val,
        "magenta_ratio": magenta_ratio,
    }


# =============================================================================
# TIER 1: FEATURE COVERAGE (Opaque-Box Structural Existence)
# =============================================================================


def test_tier1_deliverable_files_exist():
    """R4 / AC 111, 124, 125: All three deliverables must exist on disk."""
    assert BLEND_FILE.exists(), f"Deliverable missing: {BLEND_FILE}"
    assert GLB_FILE.exists(), f"Deliverable missing: {GLB_FILE}"
    assert PREVIEW_FILE.exists(), f"Deliverable missing: {PREVIEW_FILE}"


def test_tier1_scene_collections_presence(blend_scene_data: dict[str, Any]):
    """R4 / AC 112: Scene contains 6 structured collections: Terrain, Water, Flora, Fauna, Lighting, Camera."""
    col_names = set(blend_scene_data["collection_names"])
    missing = REQUIRED_COLLECTIONS - col_names
    assert not missing, f"Missing required collections in .blend: {missing}. Found: {col_names}"


def test_tier1_collections_contain_objects(blend_scene_data: dict[str, Any]):
    """R4 / AC 112: Every required collection must contain at least 1 object."""
    cols = blend_scene_data["collections"]
    for req_col in REQUIRED_COLLECTIONS:
        objs = cols.get(req_col, [])
        assert len(objs) >= 1, f"Collection '{req_col}' is empty (must contain >= 1 object)"


def test_tier1_terrain_mesh_exists(blend_scene_data: dict[str, Any]):
    """R1 / AC 115: Terrain collection contains a valid terrain mesh object."""
    terrain = blend_scene_data["terrain"]
    assert terrain is not None, "No terrain mesh object found in scene"
    assert terrain["vertex_count"] > 100, f"Terrain vertex count too low: {terrain['vertex_count']}"
    assert len(terrain["materials"]) >= 1, "Terrain mesh has no material assigned"


def test_tier1_water_river_and_lake_present(blend_scene_data: dict[str, Any]):
    """R1 / AC 116: At least one continuous river mesh and one lake basin mesh exist."""
    water_objs = blend_scene_data["water"]
    assert len(water_objs) >= 2, f"Expected >= 2 water objects, found {len(water_objs)}"

    names = [w["name"].lower() for w in water_objs]
    has_river = any("river" in n for n in names)
    has_lake = any("lake" in n for n in names)

    assert has_river, f"No river mesh identified in water objects: {names}"
    assert has_lake, f"No lake mesh identified in water objects: {names}"


def test_tier1_water_pbr_material_properties(blend_scene_data: dict[str, Any]):
    """R1 / AC 116: Water meshes must feature translucent PBR water material."""
    water_objs = blend_scene_data["water"]
    for w in water_objs:
        mats = w.get("materials", [])
        assert len(mats) >= 1, f"Water object {w['name']} has no material assigned"
        # At least one material has transmission or low roughness
        has_translucent = any(m.get("transmission", 0.0) >= 0.5 or m.get("ior", 1.0) > 1.2 for m in mats)
        assert has_translucent, f"Water object {w['name']} material lacks translucent PBR properties: {mats}"


def test_tier1_flora_species_minimum(blend_scene_data: dict[str, Any]):
    """R2 / AC 119: At least 3 distinct plant/tree species are placed across the map."""
    flora = blend_scene_data["flora"]
    assert flora["count"] >= 3, f"Total flora instances too low: {flora['count']}"
    assert flora["species_count"] >= 3, (
        f"Found {flora['species_count']} distinct flora species, expected >= 3. Species: {flora['species']}"
    )


def test_tier1_fauna_species_and_armatures(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: At least 2 distinct animal species present with rigged skeletal armatures."""
    fauna = blend_scene_data["fauna"]
    assert len(fauna) >= 2, f"Expected >= 2 animal armatures, found {len(fauna)}"
    for arm in fauna:
        assert arm["bone_count"] >= MIN_ARMATURE_BONES, (
            f"Armature {arm['name']} has insufficient bones: {arm['bone_count']} < {MIN_ARMATURE_BONES}"
        )
        assert len(arm["child_meshes"]) >= 1, f"Armature {arm['name']} has no associated skinned mesh"


def test_tier1_fauna_active_actions_assigned(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: Each fauna armature has an active animation action assigned."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        assert arm["active_action"] is not None, f"Armature {arm['name']} has no active action assigned"
        assert len(arm["actions"]) >= 1, f"Armature {arm['name']} has no animation actions"


def test_tier1_lighting_and_camera_configured(blend_scene_data: dict[str, Any]):
    """R4 / AC 112: Atmospheric lighting and framed scene camera are configured."""
    lights = blend_scene_data["lighting"]
    assert len(lights) >= 1, "No light objects found in Lighting collection"
    has_sun = any(l["light_type"] == 'SUN' for l in lights)
    assert has_sun, f"No SUN light found in lighting objects: {[l['light_type'] for l in lights]}"

    cams = blend_scene_data["camera"]
    assert len(cams) >= 1, "No camera found in Camera collection"
    has_scene_cam = any(c["is_scene_camera"] for c in cams)
    assert has_scene_cam, "Active scene camera not assigned to a camera object"


# =============================================================================
# TIER 2: BOUNDARY & CORNER CASES (Metric Invariants & Tolerances)
# =============================================================================


def test_tier2_terrain_elevation_delta_boundary(blend_scene_data: dict[str, Any]):
    """R1 / AC 115: Terrain elevation delta must satisfy delta Z >= 15.0m."""
    terrain = blend_scene_data["terrain"]
    delta_z = terrain["delta_z"]
    assert delta_z >= TERRAIN_MIN_DELTA_Z, (
        f"Terrain elevation delta {delta_z:.2f}m violates requirement >= {TERRAIN_MIN_DELTA_Z}m "
        f"(min_z={terrain['min_z']}m, max_z={terrain['max_z']}m)"
    )


def test_tier2_terrain_horizontal_span_bounds(blend_scene_data: dict[str, Any]):
    """R1 / AC 115: Terrain horizontal span must be between 100m and 500m."""
    terrain = blend_scene_data["terrain"]
    span_x = terrain["span_x"]
    span_y = terrain["span_y"]

    assert TERRAIN_SPAN_MIN <= span_x <= TERRAIN_SPAN_MAX, (
        f"Terrain span_x {span_x:.1f}m outside allowed range [{TERRAIN_SPAN_MIN}, {TERRAIN_SPAN_MAX}]"
    )
    assert TERRAIN_SPAN_MIN <= span_y <= TERRAIN_SPAN_MAX, (
        f"Terrain span_y {span_y:.1f}m outside allowed range [{TERRAIN_SPAN_MIN}, {TERRAIN_SPAN_MAX}]"
    )


def test_tier2_flora_smooth_shading_compliance(blend_scene_data: dict[str, Any]):
    """R2 / AC 119: 100% of polygon faces across flora meshes must have use_smooth == True."""
    flora = blend_scene_data["flora"]
    assert flora["non_smooth_count"] == 0, (
        f"Found {flora['non_smooth_count']} flora meshes with flat-shaded faces: {flora['non_smooth_names']}"
    )


def test_tier2_fauna_smooth_shading_compliance(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: All fauna creature meshes must have smooth shading enabled."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        for m in arm["child_meshes"]:
            assert m["is_smooth"], f"Fauna mesh {m['name']} under {arm['name']} has flat shading (use_smooth != True)"


def test_tier2_glb_file_size_threshold(glb_metadata: dict[str, Any]):
    """R4 / AC 124: Exported GLB file size must strictly exceed 100 KB."""
    file_size = glb_metadata["file_size"]
    assert file_size > MIN_GLB_BYTES, (
        f"GLB file size {file_size} bytes ({file_size / 1024:.1f} KB) is <= threshold {MIN_GLB_BYTES} bytes (100 KB)"
    )


def test_tier2_action_keyframe_counts(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: Action keyframe frame counts must be >= 20 frames."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        for act in arm["actions"]:
            assert act["frame_count"] >= MIN_ACTION_FRAMES, (
                f"Action '{act['name']}' in {arm['name']} has too few frames: "
                f"{act['frame_count']} < {MIN_ACTION_FRAMES}"
            )


def test_tier2_action_looping_boundary(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: Locomotion / Idle cycle actions must have matching start/end keyframe poses for looping."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        for act in arm["actions"]:
            assert act["is_loopable"], (
                f"Action '{act['name']}' in {arm['name']} is not cleanly loopable: start and end poses differ."
            )


def test_tier2_water_elevation_bounds(blend_scene_data: dict[str, Any]):
    """R1 / AC 115, 116, 182: Water elevation across 4-tier continuous hydrology and cave pool (-10.0m <= Z <= 25.0m)."""
    water_objs = blend_scene_data["water"]
    for w in water_objs:
        assert -10.0 <= w["min_z"] <= 25.0, (
            f"Water mesh {w['name']} min_z={w['min_z']}m outside plausible water elevation [-10.0, 25.0]"
        )


# =============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (System Interactions & Couplings)
# =============================================================================


def test_tier3_flora_elevation_distribution(blend_scene_data: dict[str, Any]):
    """R2 / AC 119, 186: Flora species distribution must respect elevation and topography."""
    flora = blend_scene_data["flora"]
    objects = flora["objects"]

    # Conifers should have instances reaching higher elevations
    conifers = [o for o in objects if "conifer" in o["species"].lower() or "pine" in o["species"].lower()]
    reeds = [o for o in objects if "reed" in o["species"].lower() or "cattail" in o["species"].lower()]
    lilies = [o for o in objects if "lily" in o["species"].lower()]

    if conifers:
        conifer_max_z = max(o["location"][2] for o in conifers)
        assert conifer_max_z >= 10.0, (
            f"Alpine conifers should inhabit higher ground, but max Z is {conifer_max_z:.1f}m (< 10.0m)"
        )

    if reeds:
        reed_z_vals = [o["location"][2] for o in reeds]
        assert min(reed_z_vals) <= 5.0, (
            f"Reeds/cattails should populate lowlands near water, but min Z is {min(reed_z_vals):.1f}m (> 5.0m)"
        )

    if lilies:
        lily_z_vals = [o["location"][2] for o in lilies]
        assert all(abs(z - 4.5) <= 1.0 or abs(z - 2.0) <= 1.0 for z in lily_z_vals), (
            f"Water lilies must float near lake water level (~4.5m), found Z: {lily_z_vals}"
        )


def test_tier3_water_recessed_in_terrain_depressions(blend_scene_data: dict[str, Any]):
    """R1 / AC 115, 116: Water surfaces must reside within terrain depression elevations."""
    terrain = blend_scene_data["terrain"]
    water_objs = blend_scene_data["water"]

    lake_objs = [w for w in water_objs if "lake" in w["name"].lower()]
    if lake_objs:
        lake = lake_objs[0]
        # Lake surface should be below mountain ridges
        assert lake["location"][2] < terrain["max_z"], (
            f"Lake surface Z={lake['location'][2]}m is higher than mountain summit Z={terrain['max_z']}m"
        )


def test_tier3_fauna_armature_modifier_binding(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: Fauna creature meshes must bind to skeletal armatures via ARMATURE modifier."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        assert len(arm["child_meshes"]) >= 1, f"No skinned meshes found under {arm['name']}"
        for cm in arm["child_meshes"]:
            assert cm["has_armature_modifier"], (
                f"Skinned mesh '{cm['name']}' is missing ARMATURE modifier bound to {arm['name']}"
            )


def test_tier3_fauna_vertex_groups_match_bones(blend_scene_data: dict[str, Any]):
    """R3 / AC 120: Skinned mesh vertex groups must correlate with armature bones."""
    fauna = blend_scene_data["fauna"]
    for arm in fauna:
        bone_names = set(arm["bones"])
        for cm in arm["child_meshes"]:
            vgroups = set(cm["vertex_groups"])
            common = bone_names & vgroups
            assert len(common) >= 5, (
                f"Skinned mesh '{cm['name']}' has only {len(common)} vertex groups matching bones in {arm['name']}. "
                f"Bones: {bone_names}, Vertex Groups: {vgroups}"
            )


def test_tier3_lighting_sun_energy_and_scene_camera(blend_scene_data: dict[str, Any]):
    """R4 / AC 112: Sun light energy and scene camera orientation ensure illuminated viewport."""
    lights = blend_scene_data["lighting"]
    sun_lights = [l for l in lights if l["light_type"] == 'SUN']
    assert sun_lights, "No SUN light found in scene"
    assert sun_lights[0]["energy"] >= 1.0, f"Sun light energy too weak: {sun_lights[0]['energy']} < 1.0"

    cams = blend_scene_data["camera"]
    scene_cams = [c for c in cams if c["is_scene_camera"]]
    assert scene_cams, "No active scene camera designated"
    cam = scene_cams[0]
    # Camera should be elevated to view the landscape
    assert cam["location"][2] >= 10.0, f"Camera height Z={cam['location'][2]}m is too low for landscape vista"


def test_tier3_flora_spatial_scattering_extent(blend_scene_data: dict[str, Any]):
    """R2 / AC 119: Flora instances must be scattered across the terrain rather than collapsed to a single point."""
    flora = blend_scene_data["flora"]
    objs = flora["objects"]
    assert len(objs) >= 5, f"Flora instance count too low: {len(objs)}"

    xs = [o["location"][0] for o in objs]
    ys = [o["location"][1] for o in objs]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)

    assert dx >= 40.0, f"Flora X distribution span too narrow: {dx:.1f}m < 40m"
    assert dy >= 40.0, f"Flora Y distribution span too narrow: {dy:.1f}m < 40m"


# =============================================================================
# TIER 4: REAL-WORLD SCENARIOS (End-to-End Operational Workflows)
# =============================================================================


def test_tier4_headless_verification_script_execution():
    """R5 / AC 123: Automated headless verification script executes cleanly with zero errors."""
    if not VERIFY_SCRIPT.exists():
        pytest.fail(f"verify_ecosystem.py script not found at {VERIFY_SCRIPT}")

    cmd = [
        str(BLENDER_BIN),
        "--background",
        str(BLEND_FILE),
        "--python",
        str(VERIFY_SCRIPT),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, (
        f"Headless verification script failed with returncode {proc.returncode}.\n"
        f"Stderr: {proc.stderr}\nStdout: {proc.stdout}"
    )


def test_tier4_glb_binary_structure_and_chunks(glb_metadata: dict[str, Any]):
    """R4 / AC 124: GLB file has valid glTF 2.0 binary chunks, scenes, meshes, and materials."""
    meta = glb_metadata["json"]

    assert "asset" in meta, "GLB missing 'asset' declaration"
    assert meta["asset"].get("version") == "2.0", f"Expected version 2.0, got {meta['asset'].get('version')}"

    assert len(meta.get("scenes", [])) >= 1, "GLB contains no scenes"
    assert len(meta.get("nodes", [])) >= 5, f"GLB contains too few nodes: {len(meta.get('nodes', []))}"
    assert len(meta.get("meshes", [])) >= 2, f"GLB contains too few meshes: {len(meta.get('meshes', []))}"
    assert len(meta.get("materials", [])) >= 2, f"GLB contains too few materials: {len(meta.get('materials', []))}"
    assert glb_metadata["has_bin_chunk"], "GLB missing binary buffer chunk"
    assert glb_metadata["bin_chunk_len"] > 1000, "GLB binary buffer chunk unexpectedly small"


def test_tier4_glb_embedded_animations(glb_metadata: dict[str, Any]):
    """R4 / AC 124: GLB file contains embedded animation clips covering idle and locomotion."""
    meta = glb_metadata["json"]
    anims = meta.get("animations", [])
    assert len(anims) >= 2, f"GLB contains fewer than 2 animation clips: found {len(anims)}"

    anim_names = [a.get("name", "") for a in anims]
    assert any("idle" in n.lower() or "glide" in n.lower() for n in anim_names), (
        f"Missing idle/glide animation clip in GLB: {anim_names}"
    )
    assert any("walk" in n.lower() or "flap" in n.lower() for n in anim_names), (
        f"Missing locomotion (walk/flap) animation clip in GLB: {anim_names}"
    )


def test_tier4_render_preview_image_resolution_and_format(preview_image_data: dict[str, Any]):
    """R5 / AC 125: Preview render image must be high-resolution (>= 1280x720)."""
    width = preview_image_data["width"]
    height = preview_image_data["height"]

    assert width >= MIN_IMAGE_WIDTH, f"Preview image width {width} < required {MIN_IMAGE_WIDTH}"
    assert height >= MIN_IMAGE_HEIGHT, f"Preview image height {height} < required {MIN_IMAGE_HEIGHT}"


def test_tier4_render_preview_illumination_and_color_integrity(preview_image_data: dict[str, Any]):
    """R5 / AC 125: Preview render image must be non-blank, illuminated, and free of missing shader pink artifacts."""
    std_dev = preview_image_data["std_dev"]
    assert std_dev > 10.0, f"Preview image pixel standard deviation {std_dev:.1f} indicates blank or solid image"

    magenta_ratio = preview_image_data["magenta_ratio"]
    assert magenta_ratio < 0.02, (
        f"Preview image contains {magenta_ratio * 100:.2f}% magenta pixels, indicating missing shader textures"
    )


def test_tier4_independent_headless_render_execution(tmp_path: Path):
    """R5 / AC 125: Headless Blender can independently render frame 1 from ecosystem_map.blend."""
    out_target = tmp_path / "test_frame_render"
    cmd = [
        str(BLENDER_BIN),
        "--background",
        str(BLEND_FILE),
        "--render-output",
        str(out_target),
        "--render-frame",
        "1",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    assert proc.returncode == 0, (
        f"Independent render failed with exit code {proc.returncode}.\n"
        f"Stderr: {proc.stderr}\nStdout: {proc.stdout}"
    )

    rendered_files = list(tmp_path.glob("test_frame_render*"))
    assert rendered_files, f"No render output file found in {tmp_path}"
    assert rendered_files[0].stat().st_size > 10_000, "Rendered output file unexpectedly small (< 10 KB)"


# =============================================================================
# TIER 5: DIORAMA CUTAWAY & 4-ZONE ECOSYSTEM REQUIREMENTS (2026-09-03T17:21:58Z)
# =============================================================================


def test_tier1_diorama_8_clean_collections(blend_scene_data: dict[str, Any]):
    """R5 / AC 171, 198: All 8 clean collections from prompt 2026-09-03T17:21:58Z must exist."""
    cols = set(blend_scene_data["collection_names"])
    expected_8 = {
        "Diorama_Block", "Terrain", "Hydrology", "Subterranean_Cave",
        "Flora_Instances", "Fauna_Rigged", "Lighting", "Cameras"
    }
    missing = expected_8 - cols
    assert not missing, f"Missing required collections from 8-collection spec: {missing}"


def test_tier2_diorama_cutaway_block_base_depth(blend_scene_data: dict[str, Any]):
    """R1 / AC 180: Diorama cutaway block must reach down to base depth Z <= -12.0m."""
    terrain = blend_scene_data["terrain"]
    assert terrain is not None, "Terrain mesh not found"
    assert terrain["min_z"] <= -12.0, (
        f"Diorama base depth min_z={terrain['min_z']}m must reach Z <= -12.0m (geological strata cutaway)"
    )


def test_tier2_subterranean_karst_cave_presence(blend_scene_data: dict[str, Any]):
    """R1 / AC 183: Subterranean karst cave network must contain cavern room, speleothems, and cave pool."""
    cave_objs = [o.lower() for o in blend_scene_data.get("subterranean_cave", [])]
    assert any("cavern" in o or "cave" in o for o in cave_objs), f"Cavern room mesh missing: {cave_objs}"
    assert any("speleo" in o or "stalactite" in o for o in cave_objs), f"Speleothems missing: {cave_objs}"
    assert any("pool" in o for o in cave_objs), f"Cave pool missing: {cave_objs}"


def test_tier2_fauna_5_species_coverage(blend_scene_data: dict[str, Any]):
    """R3 / AC 191: 5 distinct animal species representing 4 biomes with >= 90 total bones."""
    fauna = blend_scene_data["fauna"]
    assert len(fauna) >= 5, f"Expected 5 fauna species, found {len(fauna)}"
    total_bones = sum(arm["bone_count"] for arm in fauna)
    assert total_bones >= 90, f"Expected >= 90 total skeletal bones across fauna, found {total_bones}"


def test_tier3_water_volume_absorption_shader(blend_scene_data: dict[str, Any]):
    """R4 / AC 196: Water PBR shader must include Volume Absorption for realistic depth gradients."""
    water_objs = blend_scene_data["water"]
    has_vol_absorb = False
    for w in water_objs:
        for m in w.get("materials", []):
            if m.get("has_volume_absorption", False):
                has_vol_absorb = True
                break
    assert has_vol_absorb, "Water material lacks ShaderNodeVolumeAbsorption for depth absorption"


def test_tier4_isometric_3_4_camera_framing(blend_scene_data: dict[str, Any]):
    """R5 / AC 197: Primary scene camera must be positioned in 3/4 isometric perspective framing."""
    cams = blend_scene_data["camera"]
    scene_cams = [c for c in cams if c["is_scene_camera"]]
    assert scene_cams, "No active scene camera found"
    cam = scene_cams[0]
    loc = cam["location"]
    assert loc[0] >= 100.0 and loc[1] <= -100.0 and loc[2] >= 100.0, (
        f"Active camera at {loc} is not in 3/4 isometric diorama position"
    )


def test_tier4_glb_multi_clip_animations_and_skins(glb_metadata: dict[str, Any]):
    """R5 / AC 199: GLB binary must contain >= 8 animation clips and >= 4 skins."""
    meta = glb_metadata["json"]
    anims = meta.get("animations", [])
    skins = meta.get("skins", [])
    assert len(anims) >= 8, f"Expected >= 8 animation clips in GLB, found {len(anims)}"
    assert len(skins) >= 4, f"Expected >= 4 skins in GLB, found {len(skins)}"


def test_tier5_geometry_nodes_modifiers_and_groups(blend_scene_data: dict[str, Any]):
    """R2 / AC 186: Genuine Geometry Nodes modifiers and node groups must exist in scene across 4 biomes."""
    mods = blend_scene_data.get("nodes_modifiers", [])
    groups = blend_scene_data.get("node_groups", [])
    assert len(mods) >= 4, f"Expected >= 4 NODES modifiers on scatter objects, found {len(mods)}: {mods}"
    assert len(groups) >= 4, f"Expected >= 4 Geometry Nodes groups, found {len(groups)}: {groups}"
    for biome in ["Alpine", "Lowland", "Aquatic", "Cave"]:
        assert any(biome.lower() in m.lower() for m in mods), f"Missing NODES modifier for biome {biome}: {mods}"
        assert any(biome.lower() in g.lower() for g in groups), f"Missing NodeGroup for biome {biome}: {groups}"



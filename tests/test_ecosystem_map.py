"""Abiotic delivery contracts from PROJECT.md Architecture and M4/M5 interfaces.

Replaces obsolete fauna/rigging, six-collection and single-preview requirements.
Structural checks do not certify AAA appearance, water contact, or browser FPS.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from genesis.concept_creator import _find_blender

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "blender_map"
WATER = ("Water_Lake_Central", "Water_River_Meander", "Water_Bay_Marine", "Water_Cave_Pool")
CAVE = ("Cave_Cavern_Chamber", "Cave_Arch_Entrance", "Cave_Speleothems", "Cave_Mineral_Clusters")
RENDERS = ("render_iso_overview.png", "render_ne_angle.png", "render_top_down.png",
           "render_closeup_water_cavern.png")
# Exported mesh taxonomy: additions require review rather than a biological-name blacklist.
MESH_ROLES = ("Diorama_Island_Block", *WATER, *CAVE, "Diorama_Abiotic_RockCrag",
              "Diorama_RockCrag_", "Diorama_Abiotic_RiverPebble", "Diorama_RiverPebble_")

PROBE = r'''
import bpy, json, math
scene = bpy.context.scene
out = {'objects': {}, 'materials': {}, 'actions': len(bpy.data.actions),
       'camera': scene.camera.name if scene.camera else None,
       'libraries': [lib.filepath for lib in bpy.data.libraries]}
for obj in scene.objects:
    data = {'type': obj.type, 'modifiers': [m.type for m in obj.modifiers]}
    if obj.type == 'MESH':
        mesh = obj.data
        points = [obj.matrix_world @ v.co for v in mesh.vertices]
        data.update(vertices=len(points), polygons=len(mesh.polygons),
                    materials=[m.name for m in mesh.materials if m],
                    finite=all(math.isfinite(c) for p in points for c in p),
                    smooth=sum(p.use_smooth for p in mesh.polygons),
                    bounds=[[min(p[i] for p in points), max(p[i] for p in points)]
                            for i in range(3)] if points else [])
    elif obj.type == 'CAMERA':
        data.update(clip_start=obj.data.clip_start, clip_end=obj.data.clip_end)
    elif obj.type == 'LIGHT':
        data.update(light_type=obj.data.type, energy=obj.data.energy)
    out['objects'][obj.name] = data
for mat in bpy.data.materials:
    nodes = list(mat.node_tree.nodes) if mat.use_nodes else []
    out['materials'][mat.name] = {
        'nodes': [n.bl_idname for n in nodes],
        'pbr': [{k: n.inputs[k].default_value for k in
                 ('Roughness', 'Metallic', 'IOR', 'Transmission Weight')}
                for n in nodes if n.type == 'BSDF_PRINCIPLED'],
        'linked_outputs': [s.name for n in nodes if n.type == 'OUTPUT_MATERIAL'
                           for s in n.inputs if s.is_linked],
    }
print('ABIOTIC_PROBE=' + json.dumps(out))
'''


@pytest.fixture(scope="module")
def blend_scene_data():
    path = ASSETS / "ecosystem_map.blend"
    assert path.is_file(), str(path)
    blender = _find_blender()
    if blender is None:
        pytest.skip("Blender not installed; GLB/manifest/render checks still run")
    proc = subprocess.run(
        [blender, "--background", str(path), "--python-exit-code", "1", "--python-expr", PROBE],
        capture_output=True, encoding="utf-8", timeout=180,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = [s for s in proc.stdout.splitlines() if s.startswith("ABIOTIC_PROBE=")]
    assert len(lines) == 1, proc.stdout + proc.stderr
    return json.loads(lines[0].split("=", 1)[1])


def parse_glb(raw):
    assert len(raw) >= 28, "Truncated GLB"
    magic, version, size = struct.unpack_from("<4sII", raw)
    assert (magic, version, size) == (b"glTF", 2, len(raw))
    chunks = []
    offset = 12
    while offset < len(raw):
        assert offset + 8 <= len(raw), "Truncated chunk header"
        length, kind = struct.unpack_from("<II", raw, offset)
        assert length % 4 == 0, "Unaligned chunk"
        offset += 8
        assert offset + length <= len(raw), "Truncated chunk payload"
        chunks.append((kind, raw[offset:offset + length]))
        offset += length
    assert [c[0] for c in chunks] == [0x4E4F534A, 0x004E4942]
    meta = json.loads(chunks[0][1])
    assert meta["asset"]["version"] == "2.0"
    assert len(meta["buffers"]) == 1
    buffer = meta["buffers"][0]
    assert "uri" not in buffer, "GLB must be self-contained"
    assert 0 < buffer["byteLength"] <= len(chunks[1][1])
    assert len(chunks[1][1]) - buffer["byteLength"] <= 3
    return meta, chunks[1][1][:buffer["byteLength"]]


@pytest.fixture(scope="module")
def glb_metadata():
    return parse_glb((ASSETS / "ecosystem_map.glb").read_bytes())


def test_tier1_deliverable_files_exist():
    for path in (ASSETS / "ecosystem_map.blend", ASSETS / "ecosystem_map.glb",
                 *(ASSETS / p for p in RENDERS), ROOT / "assets/world_256.anmw",
                 ROOT / "assets/map_manifest.json", ASSETS / "viewer.html",
                 ASSETS / "simulation_heightmap.json"):
        assert path.is_file() and path.stat().st_size > 0, str(path)


def test_tier1_abiotic_scene_roles(blend_scene_data):
    """Object roles supersede the legacy Terrain/Flora/Fauna collection layout."""
    objects = blend_scene_data["objects"]
    meshes = {n: o for n, o in objects.items() if o["type"] == "MESH"}
    assert {"Diorama_Island_Block", *WATER, *CAVE} <= meshes.keys()
    assert all(n.startswith(MESH_ROLES) for n in meshes), set(meshes)
    assert not [n for n, o in objects.items() if o["type"] == "ARMATURE"]
    assert not [n for n, o in meshes.items() if "ARMATURE" in o["modifiers"]]
    assert blend_scene_data["actions"] == 0
    assert not blend_scene_data["libraries"], "External .blend dependency"
    for name, obj in meshes.items():
        assert obj["vertices"] >= 3 and obj["polygons"] > 0, name
        assert obj["finite"] and obj["materials"], name


def test_terrain_scale_relief_and_smooth_surface(blend_scene_data):
    terrain = blend_scene_data["objects"]["Diorama_Island_Block"]
    assert terrain["type"] == "MESH" and terrain["vertices"] > 100
    for low, high in terrain["bounds"][:2]:
        assert 100 <= high - low <= 500
    assert terrain["bounds"][2][1] >= 30, "Alpine relief missing"
    assert terrain["smooth"] > 0


@pytest.mark.parametrize("name", WATER + CAVE)
def test_water_and_karst_meshes(blend_scene_data, name):
    mesh = blend_scene_data["objects"][name]
    assert mesh["type"] == "MESH" and mesh["polygons"] > 0
    assert mesh["materials"] and mesh["finite"]


def test_geological_scatter_present(blend_scene_data):
    objects = blend_scene_data["objects"]
    for role in ("Diorama_RockCrag_", "Diorama_RiverPebble_"):
        assert any(n.startswith(role) and o["type"] == "MESH" for n, o in objects.items()), role


def test_water_shader_depth_absorption(blend_scene_data):
    for name in WATER:
        materials = [blend_scene_data["materials"][m]
                     for m in blend_scene_data["objects"][name]["materials"]]
        assert any("ShaderNodeVolumeAbsorption" in m["nodes"]
                   and "Volume" in m["linked_outputs"] for m in materials), name
        assert any(p["Transmission Weight"] > 0 and 1.2 < p["IOR"] < 1.5
                   and 0 <= p["Roughness"] < 0.5
                   for m in materials for p in m["pbr"]), name


def test_terrain_pbr_surface_connected(blend_scene_data):
    terrain = blend_scene_data["objects"]["Diorama_Island_Block"]
    materials = [blend_scene_data["materials"][m] for m in terrain["materials"]]
    assert any(m["pbr"] and "Surface" in m["linked_outputs"] for m in materials)


def test_lighting_and_inspection_views(blend_scene_data):
    objects = blend_scene_data["objects"]
    assert any(o["type"] == "LIGHT" and o["light_type"] == "SUN" and o["energy"] > 0
               for o in objects.values())
    active_camera = blend_scene_data["camera"]
    assert active_camera in objects, "Scene has no active render camera"
    assert objects[active_camera]["type"] == "CAMERA"
    for name in ("CAM_Inspect_isometric_diorama", "CAM_Inspect_iso_ne",
                 "CAM_Inspect_topdown", "CAM_Inspect_closeup_water_cavern"):
        camera = objects[name]
        assert camera["type"] == "CAMERA"
        assert 0 < camera["clip_start"] < camera["clip_end"]


def test_glb_static_abiotic_export_and_budget(glb_metadata):
    meta, _ = glb_metadata
    assert 100_000 < (ASSETS / "ecosystem_map.glb").stat().st_size <= 10_000_000
    assert not meta.get("skins") and not meta.get("animations")
    mesh_names = {n["name"] for n in meta["nodes"] if "mesh" in n}
    assert {"Diorama_Island_Block", *WATER, *CAVE} <= mesh_names
    assert all(n.startswith(MESH_ROLES) for n in mesh_names)
    triangles = 0
    for mesh in meta["meshes"]:
        assert mesh["primitives"]
        for prim in mesh["primitives"]:
            assert prim.get("mode", 4) == 4
            assert not {"JOINTS_0", "WEIGHTS_0"} & prim["attributes"].keys()
            count = meta["accessors"][prim["indices"]]["count"]
            assert count > 0 and count % 3 == 0
            triangles += count // 3
    assert 0 < triangles <= 300_000


def test_blend_glb_mesh_parity(blend_scene_data, glb_metadata):
    meta, _ = glb_metadata
    source = {n for n, o in blend_scene_data["objects"].items() if o["type"] == "MESH"}
    exported = {n["name"] for n in meta["nodes"] if "mesh" in n}
    assert source == exported


@pytest.mark.parametrize("section", ("worldArtifact", "modelAsset"))
def test_manifest_asset_integrity(section):
    manifest = json.loads((ROOT / "assets/map_manifest.json").read_text(encoding="utf-8"))
    assert manifest["mapId"] == "genesis_primordial_abiotic"
    entry = manifest[section]
    raw = (ROOT / entry["path"]).read_bytes()
    assert len(raw) == entry["bytes"]
    assert "sha256:" + hashlib.sha256(raw).hexdigest() == entry["checksum"]


def test_world_artifact_v2_payload_checksum():
    raw = (ROOT / "assets/world_256.anmw").read_bytes()
    magic, version, width, height, sea, seed, generator, scale, checksum = struct.unpack_from(
        "<4sIIIfIIfI", raw)
    assert (magic, version, width, height) == (b"ANMW", 2, 256, 256)
    assert sea == 0 and scale == 200 and generator == 2
    assert len(raw) == 36 + width * height * 17
    actual = 0x811C9DC5
    for byte in raw[36:]:
        actual = ((actual ^ byte) * 0x01000193) & 0xFFFFFFFF
    assert actual == checksum
    floats = np.frombuffer(raw, dtype="<f4", count=width * height * 4, offset=36)
    assert np.isfinite(floats).all()
    biomes = np.frombuffer(raw, dtype="u1", offset=36 + width * height * 16)
    assert (biomes < 22).all()


@pytest.mark.parametrize("name", RENDERS)
def test_acceptance_render_decodes_and_is_not_blank(name):
    with Image.open(ASSETS / name) as image:
        assert image.format == "PNG"
        assert image.width >= 1280 and image.height >= 720
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722])
    assert luminance.std() > 10, "Blank/near-uniform acceptance render"
    assert np.ptp(luminance) > 80
    r, g, b = np.moveaxis(rgb, -1, 0)
    assert np.mean((r > 220) & (g < 50) & (b > 220)) < 0.001

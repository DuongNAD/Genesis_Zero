"""
Adversarial test suite for Genesis Zero 3D creature assets.
Author: challenger_creatures_1
Empirically challenges the 3D meshes and glTF binary files across all 10 target species.
"""

import json
import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_CREATURES = PROJECT_ROOT / "assets" / "creatures"

TARGET_SPECIES = [
    "sand_skink",
    "snow_ferret",
    "alpine_ibex",
    "meadow_hare",
    "marsh_croc",
    "abyssal_hunter",
    "storm_eagle",
    "giant_tarantula",
    "armored_sentinel",
    "carnivore_apex",
]

CANONICAL_8_ANIMATIONS = [
    "Idle_Normal",
    "Idle_Alert",
    "Walk",
    "Run",
    "Attack",
    "Hurt_Defend",
    "Eat",
    "Death",
]

BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"


def resolve_creature_file(species: str, ext: str) -> Path:
    p = ASSETS_CREATURES / f"{species}{ext}"
    if p.exists():
        return p
    # Fallback to aliases
    for f in ASSETS_CREATURES.glob(f"*{species}*{ext}"):
        if f.exists():
            return f
    return p


class TestAdversarialBlenderBMesh:
    """Empirical challenge of BMesh topology directly via Blender headless CLI."""

    @pytest.fixture(scope="class")
    @classmethod
    def blender_executable(cls):
        if os.path.exists(BLENDER_BIN):
            return BLENDER_BIN
        which_b = shutil.which("blender")
        if which_b and os.path.exists(which_b):
            return which_b
        pytest.skip(f"Blender executable not found at {BLENDER_BIN} or in PATH")

    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_bmesh_invariants_per_species(self, blender_executable, species):
        blend_file = resolve_creature_file(species, ".blend")
        assert blend_file.exists(), f"Blend file for {species} does not exist: {blend_file}"
        assert blend_file.stat().st_size > 1024, f"Blend file for {species} is too small: {blend_file.stat().st_size} bytes"

        # Python expression executed inside headless Blender
        expr = f"""
import bpy, bmesh, json, sys

filepath = {str(blend_file)!r}
bpy.ops.wm.open_mainfile(filepath=filepath)

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
armatures = [o for o in bpy.data.objects if o.type == 'ARMATURE']

data = {{
    "mesh_count": len(meshes),
    "armature_count": len(armatures),
    "meshes": {{}}
}}

for m in meshes:
    bm = bmesh.new()
    bm.from_mesh(m.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
    incontig_edges = sum(1 for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous)
    wire_edges = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    multi_face_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    ngons = sum(1 for f in bm.faces if len(f.verts) > 4)
    total_faces = len(bm.faces)
    total_verts = len(bm.verts)

    total_polys = len(m.data.polygons)
    smooth_polys = sum(1 for p in m.data.polygons if p.use_smooth)
    non_smooth_polys = total_polys - smooth_polys

    # Check zero-area faces (degenerate faces)
    zero_area_faces = sum(1 for f in bm.faces if f.calc_area() < 1e-7)

    bm.free()

    data["meshes"][m.name] = {{
        "total_verts": total_verts,
        "loose_verts": loose_verts,
        "wire_edges": wire_edges,
        "incontig_edges": incontig_edges,
        "multi_face_edges": multi_face_edges,
        "non_manifold_edges": non_manifold_edges,
        "ngons": ngons,
        "total_polygons": total_polys,
        "smooth_polygons": smooth_polys,
        "non_smooth_polygons": non_smooth_polys,
        "zero_area_faces": zero_area_faces,
        "has_armature_mod": any(mod.type == 'ARMATURE' and mod.object is not None for mod in m.modifiers),
    }}

print("RESULT_START:" + json.dumps(data) + ":RESULT_END")
"""
        cmd = [blender_executable, "-b", "--python-expr", expr]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)

        assert "RESULT_START:" in res.stdout, f"Failed to get output from Blender for {species}:\n{res.stderr}"
        start = res.stdout.find("RESULT_START:") + len("RESULT_START:")
        end = res.stdout.find(":RESULT_END", start)
        payload = json.loads(res.stdout[start:end])

        assert payload["mesh_count"] >= 1, f"{species} has no MESH objects in {blend_file}"
        assert payload["armature_count"] >= 1, f"{species} has no ARMATURE objects in {blend_file}"

        for mname, mdata in payload["meshes"].items():
            assert mdata["loose_verts"] == 0, f"{species}:{mname} has {mdata['loose_verts']} loose vertices (must be strictly 0)"
            assert mdata["incontig_edges"] == 0, f"{species}:{mname} has {mdata['incontig_edges']} incontiguous edges (must be strictly 0)"
            assert mdata["wire_edges"] == 0, f"{species}:{mname} has {mdata['wire_edges']} wire edges (must be strictly 0)"
            assert mdata["multi_face_edges"] == 0, f"{species}:{mname} has {mdata['multi_face_edges']} multi-face edges (must be strictly 0)"
            assert mdata["non_manifold_edges"] == 0, f"{species}:{mname} has {mdata['non_manifold_edges']} non-manifold edges (must be strictly 0)"
            assert mdata["ngons"] == 0, f"{species}:{mname} has {mdata['ngons']} ngons (>4 verts) (must be strictly 0)"
            assert mdata["non_smooth_polygons"] == 0, f"{species}:{mname} has {mdata['non_smooth_polygons']} non-smooth polygons (must be 100% smooth)"
            assert mdata["has_armature_mod"] is True, f"{species}:{mname} is missing active Armature modifier linked to skeletal rig"


class TestAdversarialGltfBinary:
    """Empirical adversarial checks on glTF 2.0 .glb binary structures."""

    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_glb_header_and_chunks(self, species):
        glb_file = resolve_creature_file(species, ".glb")
        assert glb_file.exists(), f"GLB file for {species} does not exist: {glb_file}"
        file_size = glb_file.stat().st_size
        assert file_size > 1024, f"GLB file for {species} too small: {file_size} bytes"

        with open(glb_file, "rb") as f:
            header = f.read(12)
            magic, ver, total_len = struct.unpack("<4sII", header)
            assert magic == b"glTF", f"{species}: invalid glTF magic: {magic}"
            assert ver == 2, f"{species}: invalid glTF version: {ver}"
            assert total_len == file_size, f"{species}: glTF header length {total_len} != file size {file_size}"

            # Chunk 0 (JSON)
            c0_header = f.read(8)
            c0_len, c0_type = struct.unpack("<II", c0_header)
            assert c0_type == 0x4E4F534A, f"{species}: Chunk 0 type is not JSON (0x4E4F534A): {hex(c0_type)}"
            c0_data = f.read(c0_len)
            parsed_json = json.loads(c0_data.decode("utf-8"))
            assert isinstance(parsed_json, dict), f"{species}: glTF JSON is not a valid dict"

            # Chunk 1 (BIN)
            c1_header = f.read(8)
            assert len(c1_header) == 8, f"{species}: Missing binary buffer chunk 1"
            c1_len, c1_type = struct.unpack("<II", c1_header)
            assert c1_type == 0x004E4942, f"{species}: Chunk 1 type is not BIN (0x004E4942): {hex(c1_type)}"

            bin_data = f.read(c1_len)
            assert len(bin_data) == c1_len, f"{species}: Binary chunk truncated"

            # Total consumed length
            total_consumed = 12 + 8 + c0_len + 8 + c1_len
            assert total_consumed == file_size, f"{species}: Unconsumed trailing bytes in GLB: {file_size - total_consumed}"

    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_gltf_skins_and_joint_hierarchy(self, species):
        glb_file = resolve_creature_file(species, ".glb")
        with open(glb_file, "rb") as f:
            f.seek(12)
            c0_len, _ = struct.unpack("<II", f.read(8))
            meta = json.loads(f.read(c0_len).decode("utf-8"))

        nodes = meta.get("nodes", [])
        skins = meta.get("skins", [])
        meshes = meta.get("meshes", [])

        assert len(skins) >= 1, f"{species}: No skins array in glTF (skeletal mesh requires skin)"
        skin = skins[0]
        joints = skin.get("joints", [])
        assert len(joints) >= 6, f"{species}: Skin has only {len(joints)} joints (expected at least 6 bones)"

        for j in joints:
            assert 0 <= j < len(nodes), f"{species}: Joint index {j} out of range [0, {len(nodes)})"
            jnode = nodes[j]
            assert "name" in jnode, f"{species}: Joint node {j} has no name"

        # Check mesh primitives have skinning vertex attributes
        assert len(meshes) >= 1, f"{species}: No meshes found in glTF"
        for m_idx, mesh in enumerate(meshes):
            for p_idx, prim in enumerate(mesh.get("primitives", [])):
                attrs = prim.get("attributes", {})
                assert "JOINTS_0" in attrs, f"{species}: Mesh {m_idx} prim {p_idx} missing JOINTS_0"
                assert "WEIGHTS_0" in attrs, f"{species}: Mesh {m_idx} prim {p_idx} missing WEIGHTS_0"

    @pytest.mark.parametrize("species", TARGET_SPECIES)
    def test_gltf_canonical_8_animations(self, species):
        glb_file = resolve_creature_file(species, ".glb")
        with open(glb_file, "rb") as f:
            f.seek(12)
            c0_len, _ = struct.unpack("<II", f.read(8))
            meta = json.loads(f.read(c0_len).decode("utf-8"))

        nodes = meta.get("nodes", [])
        skins = meta.get("skins", [])
        joints_set = set(skins[0].get("joints", [])) if skins else set()
        animations = meta.get("animations", [])
        accessors = meta.get("accessors", [])

        anim_map = {a.get("name"): a for a in animations}

        # 1. Assert all 8 canonical animations exist with exact names
        for canon in CANONICAL_8_ANIMATIONS:
            assert canon in anim_map, f"{species}: Missing canonical animation '{canon}'. Present: {list(anim_map.keys())}"

        # 2. Assert channels and samplers validity
        for canon in CANONICAL_8_ANIMATIONS:
            clip = anim_map[canon]
            samplers = clip.get("samplers", [])
            channels = clip.get("channels", [])

            assert len(samplers) > 0, f"{species}:{canon} has 0 samplers"
            assert len(channels) > 0, f"{species}:{canon} has 0 channels"

            for ch_idx, ch in enumerate(channels):
                s_idx = ch.get("sampler")
                assert 0 <= s_idx < len(samplers), f"{species}:{canon} channel {ch_idx} sampler index {s_idx} out of range"
                target = ch.get("target", {})
                tnode = target.get("node")
                assert tnode is not None, f"{species}:{canon} channel {ch_idx} missing target node"
                assert 0 <= tnode < len(nodes), f"{species}:{canon} channel {ch_idx} target node {tnode} out of range"
                assert tnode in joints_set, f"{species}:{canon} channel {ch_idx} targets node {tnode} ({nodes[tnode].get('name')}) which is not in skeletal joints"
                assert target.get("path") in {"translation", "rotation", "scale", "weights"}, f"{species}:{canon} channel {ch_idx} invalid target path {target.get('path')}"

            # 3. Assert samplers reference valid accessors and durations > 0
            for s_idx, s in enumerate(samplers):
                in_idx = s.get("input")
                out_idx = s.get("output")
                assert 0 <= in_idx < len(accessors), f"{species}:{canon} sampler {s_idx} input accessor {in_idx} out of range"
                assert 0 <= out_idx < len(accessors), f"{species}:{canon} sampler {s_idx} output accessor {out_idx} out of range"

                in_acc = accessors[in_idx]
                assert in_acc.get("count", 0) > 0, f"{species}:{canon} sampler {s_idx} input accessor has 0 keyframes"
                min_t = in_acc.get("min", [0])[0]
                max_t = in_acc.get("max", [0])[0]
                assert max_t > min_t, f"{species}:{canon} sampler {s_idx} duration must be > 0 (got min={min_t}, max={max_t})"

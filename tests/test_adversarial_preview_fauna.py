"""Genesis Zero — Empirical Challenger 2 Adversarial Stress Test Suite.

Adversarially stresses:
1. Fauna Rigging & Animation Continuity:
   - Action keyframe looping boundary (first frame vs last frame posture matching).
   - Absence of gimbal lock singularities (pitch angle bounds) and absence of frame-to-frame jitter.
2. Armature Deformations & Skinning:
   - Zero unweighted / detached vertices.
   - Dynamic vertex deformation verification under armature modifier.
   - Safe edge stretch/compression bounds without mesh tearing or collapse.
3. GLB Binary Integrity & Schema:
   - Binary header and chunk layout (magic, length, JSON, BIN).
   - Quaternions unit-length normalization (|q| = 1.0).
   - Strictly monotonic animation timestamps.
   - Non-singular InverseBindMatrices and 100% normalized vertex skin weights.
   - Material bindings validity.
4. Render Preview Photometrics & Shader Integrity:
   - 1080p resolution (1920x1080).
   - Dynamic range, contrast, and luminance distribution.
   - Zero overexposure or pure black clipping.
   - Zero magenta missing-shader artifacts.
"""

from __future__ import annotations

import json
import struct
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets" / "blender_map"
BLEND_FILE = ASSETS_DIR / "ecosystem_map.blend"
GLB_FILE = ASSETS_DIR / "ecosystem_map.glb"
PREVIEW_FILE = ASSETS_DIR / "render_preview.png"
BLENDER_BIN = Path("/Applications/Blender.app/Contents/MacOS/Blender")


# ============================================================================
# Pillar 1 & 2: Blender Headless Inspection (Continuity, Rigging, Deformation)
# ============================================================================

BLENDER_STRESS_SCRIPT = r"""
import bpy
import json
import math
from mathutils import Vector

result = {
    "fauna": {},
    "errors": [],
}

for arm_name, mesh_name in [("Stag_Armature", "Stag_Model"), ("Eagle_Armature", "Eagle_Model")]:
    arm = bpy.data.objects.get(arm_name)
    mesh_obj = bpy.data.objects.get(mesh_name)
    if not arm or not mesh_obj:
        result["errors"].append(f"Missing {arm_name} or {mesh_name}")
        continue

    arm_data = {
        "bones_count": len(arm.data.bones),
        "mesh_verts": len(mesh_obj.data.vertices),
        "mesh_polys": len(mesh_obj.data.polygons),
        "zero_weight_verts": 0,
        "actions": {},
        "deformations": {},
    }

    # 1. Check for unweighted / zero-weight vertices
    bone_names = {b.name for b in arm.data.bones}
    zero_weight_count = 0
    for v in mesh_obj.data.vertices:
        total_w = sum(g.weight for g in v.groups if mesh_obj.vertex_groups[g.group].name in bone_names)
        if total_w < 1e-5:
            zero_weight_count += 1
    arm_data["zero_weight_verts"] = zero_weight_count

    # 2. Inspect Actions (Loop posture matching, jitter, gimbal lock)
    actions = []
    if arm.animation_data and arm.animation_data.action:
        actions.append(arm.animation_data.action)
    for t in getattr(arm.animation_data, "nla_tracks", []):
        for s in t.strips:
            if s.action and s.action not in actions:
                actions.append(s.action)

    for act in actions:
        arm.animation_data.action = act
        f_start, f_end = int(act.frame_range[0]), int(act.frame_range[1])

        # Start frame
        bpy.context.scene.frame_set(f_start)
        start_rot = {pb.name: Vector(pb.rotation_euler).copy() for pb in arm.pose.bones}
        start_loc = {pb.name: Vector(pb.location).copy() for pb in arm.pose.bones}

        # End frame
        bpy.context.scene.frame_set(f_end)
        max_d_rot = 0.0
        max_d_loc = 0.0
        for pb in arm.pose.bones:
            d_rot = (Vector(pb.rotation_euler) - start_rot[pb.name]).length
            d_loc = (Vector(pb.location) - start_loc[pb.name]).length
            if d_rot > max_d_rot: max_d_rot = d_rot
            if d_loc > max_d_loc: max_d_loc = d_loc

        # Jitter & Gimbal lock audit across full duration
        max_step_rot = 0.0
        max_pitch_deg = 0.0
        for f in range(f_start, f_end):
            bpy.context.scene.frame_set(f)
            p1 = {pb.name: Vector(pb.rotation_euler).copy() for pb in arm.pose.bones}
            for pb in arm.pose.bones:
                if pb.rotation_mode == 'XYZ':
                    p_deg = abs(math.degrees(pb.rotation_euler.y))
                    if p_deg > max_pitch_deg: max_pitch_deg = p_deg
            bpy.context.scene.frame_set(f + 1)
            for pb in arm.pose.bones:
                step_d = (Vector(pb.rotation_euler) - p1[pb.name]).length
                if step_d > max_step_rot: max_step_rot = step_d

        arm_data["actions"][act.name] = {
            "frame_range": [f_start, f_end],
            "max_d_rot_rad": max_d_rot,
            "max_d_loc": max_d_loc,
            "max_step_rot_deg": math.degrees(max_step_rot),
            "max_pitch_deg": max_pitch_deg,
        }

    # 3. Dynamic Deformation & Edge Stretching Audit
    sub = mesh_obj.modifiers.get("Subsurf")
    if sub: sub.show_viewport = False

    rest_mesh = mesh_obj.data
    rest_edges = []
    for edge in rest_mesh.edges:
        v1 = rest_mesh.vertices[edge.vertices[0]].co
        v2 = rest_mesh.vertices[edge.vertices[1]].co
        rest_edges.append((edge.vertices[0], edge.vertices[1], (v2 - v1).length))

    for act in actions:
        arm.animation_data.action = act
        f_start, f_end = int(act.frame_range[0]), int(act.frame_range[1])
        test_frames = [f_start, (f_start + f_end) // 2, f_end]
        max_disp = 0.0
        min_stretch = 1.0
        max_stretch = 1.0

        for f in test_frames:
            bpy.context.scene.frame_set(f)
            depsgraph = bpy.context.evaluated_depsgraph_get()
            eval_mesh_obj = mesh_obj.evaluated_get(depsgraph)
            eval_mesh = eval_mesh_obj.to_mesh()

            for v_idx in range(len(eval_mesh.vertices)):
                d = (eval_mesh.vertices[v_idx].co - rest_mesh.vertices[v_idx].co).length
                if d > max_disp: max_disp = d

            for v1_idx, v2_idx, r_len in rest_edges:
                if r_len < 1e-5: continue
                e_len = (eval_mesh.vertices[v2_idx].co - eval_mesh.vertices[v1_idx].co).length
                ratio = e_len / r_len
                if ratio > max_stretch: max_stretch = ratio
                if ratio < min_stretch: min_stretch = ratio

            eval_mesh_obj.to_mesh_clear()

        arm_data["deformations"][act.name] = {
            "max_displacement_m": max_disp,
            "min_stretch_ratio": min_stretch,
            "max_stretch_ratio": max_stretch,
        }

    result["fauna"][arm_name] = arm_data

print("===BLENDER_STRESS_OUTPUT_START===")
print(json.dumps(result))
print("===BLENDER_STRESS_OUTPUT_END===")
"""


@pytest.fixture(scope="module")
def blender_stress_data() -> dict:
    """Runs headless Blender stress inspection and returns telemetry."""
    assert BLEND_FILE.is_file(), f"Blend file not found: {BLEND_FILE}"
    assert BLENDER_BIN.is_file(), f"Blender binary not found: {BLENDER_BIN}"

    cmd = [
        str(BLENDER_BIN),
        "-b",
        str(BLEND_FILE),
        "--python-expr",
        BLENDER_STRESS_SCRIPT,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, f"Blender failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"

    output = proc.stdout
    start_tag = "===BLENDER_STRESS_OUTPUT_START==="
    end_tag = "===BLENDER_STRESS_OUTPUT_END==="
    assert start_tag in output and end_tag in output, "Missing stress JSON markers"
    raw_json = output.split(start_tag)[1].split(end_tag)[0].strip()
    return json.loads(raw_json)


def test_adversarial_animation_loop_continuity_and_gimbal_lock(blender_stress_data: dict):
    """Stress-test animation looping continuity and gimbal lock immunity."""
    fauna = blender_stress_data["fauna"]
    assert "Stag_Armature" in fauna and "Eagle_Armature" in fauna

    for arm_name, arm_info in fauna.items():
        actions = arm_info["actions"]
        assert len(actions) >= 2, f"{arm_name} must have at least 2 actions"
        for act_name, act_data in actions.items():
            # 1. Posture matching between start and end frame
            assert act_data["max_d_rot_rad"] < 1e-4, (
                f"{arm_name} {act_name} has rotation loop discontinuity: {act_data['max_d_rot_rad']:.6f} rad"
            )
            assert act_data["max_d_loc"] < 1e-4, (
                f"{arm_name} {act_name} has translation loop discontinuity: {act_data['max_d_loc']:.6f}"
            )

            # 2. Smooth kinematics / no jitter
            assert act_data["max_step_rot_deg"] < 15.0, (
                f"{arm_name} {act_name} has angular jitter > 15 deg/frame: {act_data['max_step_rot_deg']:.2f} deg"
            )

            # 3. Gimbal lock immunity (pitch angle < 75 deg)
            assert act_data["max_pitch_deg"] < 75.0, (
                f"{arm_name} {act_name} exceeds safe Euler pitch: {act_data['max_pitch_deg']:.2f} deg"
            )


def test_adversarial_armature_deformations_and_no_zero_weights(blender_stress_data: dict):
    """Stress-test vertex skinning: zero unweighted vertices and bounded stretching."""
    fauna = blender_stress_data["fauna"]
    for arm_name, arm_info in fauna.items():
        # Assert zero unweighted vertices
        assert arm_info["zero_weight_verts"] == 0, (
            f"{arm_name} has {arm_info['zero_weight_verts']} unweighted detached vertices!"
        )

        # Assert dynamic deformation and bounded stretching
        deformations = arm_info["deformations"]
        for act_name, def_data in deformations.items():
            assert def_data["max_displacement_m"] > 0.05, (
                f"{arm_name} {act_name} failed to deform mesh dynamically: disp={def_data['max_displacement_m']:.4f}m"
            )
            assert def_data["min_stretch_ratio"] > 0.40, (
                f"{arm_name} {act_name} causes extreme edge collapse: min_ratio={def_data['min_stretch_ratio']:.4f}"
            )
            assert def_data["max_stretch_ratio"] < 2.00, (
                f"{arm_name} {act_name} causes extreme edge stretching: max_ratio={def_data['max_stretch_ratio']:.4f}"
            )


# ============================================================================
# Pillar 3: Pure Python GLB Binary Structure & Schema Integrity
# ============================================================================

@pytest.fixture(scope="module")
def glb_data() -> tuple[dict, bytes]:
    """Parses GLB 2.0 binary chunks directly."""
    assert GLB_FILE.is_file(), f"GLB file not found: {GLB_FILE}"
    raw = GLB_FILE.read_bytes()
    assert len(raw) > 12, "GLB too short"

    magic, version, length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF", f"Invalid magic: {magic}"
    assert version == 2, f"Expected glTF version 2, got {version}"
    assert length == len(raw), f"Header length {length} != file size {len(raw)}"

    chunk0_len, chunk0_type = struct.unpack_from("<II", raw, 12)
    assert chunk0_type == 0x4E4F534A, "Chunk 0 must be JSON"
    json_bytes = raw[20 : 20 + chunk0_len]
    gltf = json.loads(json_bytes.decode("utf-8"))

    bin_offset = 20 + chunk0_len
    chunk1_len, chunk1_type = struct.unpack_from("<II", raw, bin_offset)
    assert chunk1_type == 0x004E4942, "Chunk 1 must be BIN"
    bin_bytes = raw[bin_offset + 8 : bin_offset + 8 + chunk1_len]

    return gltf, bin_bytes


def _read_accessor_data(gltf: dict, bin_bytes: bytes, acc_idx: int) -> np.ndarray:
    acc = gltf["accessors"][acc_idx]
    bv = gltf["bufferViews"][acc["bufferView"]]
    offset = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    count = acc["count"]
    ctype = acc["componentType"]
    ttype = acc["type"]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[ttype]
    elem_size = components * (4 if ctype == 5126 else (2 if ctype in (5123, 5122) else 1))
    stride = bv.get("byteStride", elem_size)
    fmt = {5126: "f", 5123: "H", 5122: "h", 5121: "B", 5120: "b"}[ctype]

    arr = []
    for i in range(count):
        pos = offset + i * stride
        chunk = bin_bytes[pos : pos + elem_size]
        arr.append(struct.unpack(f"<{components}{fmt}", chunk))
    return np.array(arr)


def test_adversarial_glb_animation_quaternions_and_timestamps(glb_data: tuple[dict, bytes]):
    """Stress-test GLB animation channels: normalized quaternions and monotonic time."""
    gltf, bin_bytes = glb_data
    animations = gltf.get("animations", [])
    assert len(animations) >= 4, f"Expected >=4 animations, got {len(animations)}"

    for anim in animations:
        name = anim.get("name")
        samplers = anim["samplers"]
        channels = anim["channels"]

        # Verify time monotonicity
        for s in samplers:
            times = _read_accessor_data(gltf, bin_bytes, s["input"]).flatten()
            assert np.all(np.diff(times) > 0), f"Animation {name} has non-monotonic keyframe timestamps!"

        # Verify quaternion normalization and posture loop in GLB
        for ch in channels:
            if ch["target"]["path"] == "rotation":
                s = samplers[ch["sampler"]]
                quats = _read_accessor_data(gltf, bin_bytes, s["output"])
                norms = np.linalg.norm(quats, axis=1)
                max_norm_err = np.max(np.abs(norms - 1.0))
                assert max_norm_err < 1e-4, f"Animation {name} has non-unit quaternion: err={max_norm_err:.2e}"

                # Loop posture check on rotation
                q_start, q_end = quats[0], quats[-1]
                dot = np.clip(np.abs(np.dot(q_start, q_end)), -1.0, 1.0)
                angle_deg = np.degrees(2.0 * np.arccos(dot))
                assert angle_deg < 0.1, (
                    f"Animation {name} rotation loop boundary delta exceeds 0.1 deg: {angle_deg:.4f} deg"
                )


def test_adversarial_glb_skins_and_weights_integrity(glb_data: tuple[dict, bytes]):
    """Stress-test GLB skins: non-singular inverseBindMatrices and normalized weights."""
    gltf, bin_bytes = glb_data
    skins = gltf.get("skins", [])
    assert len(skins) >= 2, f"Expected >=2 skins, got {len(skins)}"

    for _s_idx, skin in enumerate(skins):
        joints = skin["joints"]
        assert len(joints) >= 10, f"Skin {skin.get('name')} joint count < 10"

        # Check InverseBindMatrices
        ibms = _read_accessor_data(gltf, bin_bytes, skin["inverseBindMatrices"])
        assert len(ibms) == len(joints), "IBM count mismatch"
        for ibm_flat in ibms:
            det = np.linalg.det(ibm_flat.reshape((4, 4)))
            assert abs(det) > 1e-5, f"Singular inverseBindMatrix in skin {skin.get('name')}: det={det}"

    # Verify skinning on mesh nodes
    skinned_nodes = [n for n in gltf["nodes"] if "skin" in n]
    assert len(skinned_nodes) >= 2, "Expected >=2 skinned nodes"
    for n in skinned_nodes:
        m = gltf["meshes"][n["mesh"]]
        s = gltf["skins"][n["skin"]]
        for _p_idx, prim in enumerate(m["primitives"]):
            joints_arr = _read_accessor_data(gltf, bin_bytes, prim["attributes"]["JOINTS_0"])
            weights_arr = _read_accessor_data(gltf, bin_bytes, prim["attributes"]["WEIGHTS_0"])

            # Verify joint indices bounds
            assert np.max(joints_arr) < len(s["joints"]), "Joint index exceeds skin joints count"

            # Verify weight normalization
            weight_sums = np.sum(weights_arr, axis=1)
            max_err = np.max(np.abs(weight_sums - 1.0))
            assert max_err < 1e-4, f"Mesh {m.get('name')} weights not normalized: max_err={max_err}"


def test_adversarial_glb_materials_and_bindings(glb_data: tuple[dict, bytes]):
    """Stress-test GLB material references and PBR properties."""
    gltf, _ = glb_data
    materials = gltf.get("materials", [])
    assert len(materials) >= 10, f"Expected >=10 materials, got {len(materials)}"

    for _m_idx, mat in enumerate(materials):
        pbr = mat.get("pbrMetallicRoughness", {})
        rough = pbr.get("roughnessFactor", 1.0)
        metal = pbr.get("metallicFactor", 0.0)
        assert 0.0 <= rough <= 1.0, f"Material {mat.get('name')} roughness out of bounds: {rough}"
        assert 0.0 <= metal <= 1.0, f"Material {mat.get('name')} metallic out of bounds: {metal}"

    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            m_idx = prim.get("material")
            assert m_idx is not None, f"Mesh {mesh.get('name')} primitive missing material binding"
            assert 0 <= m_idx < len(materials), f"Invalid material index {m_idx}"


# ============================================================================
# Pillar 4: Render Quality, Photometric Distribution & Missing Shader Audit
# ============================================================================

def test_adversarial_render_preview_photometrics_and_zero_magenta():
    """Stress-test render preview: 1080p, illumination distribution, zero magenta artifacts."""
    assert PREVIEW_FILE.is_file(), f"Render preview not found: {PREVIEW_FILE}"
    img = Image.open(PREVIEW_FILE)

    # 1. Exact resolution check
    assert img.size == (1920, 1080), f"Render resolution {img.size} != (1920, 1080)"

    arr = np.array(img.convert("RGB"), dtype=np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # 2. Luminance distribution & dynamic range
    assert 140.0 < lum.mean() < 240.0, f"Luminance mean out of proper illumination range: {lum.mean():.2f}"
    assert lum.std() > 10.0, f"Image lacks contrast: std={lum.std():.2f}"
    dynamic_range = lum.max() - lum.min()
    assert dynamic_range > 80.0, f"Dynamic range too narrow: {dynamic_range:.2f}"

    # 3. Clipping checks
    pure_black_count = np.sum((r == 0) & (g == 0) & (b == 0))
    blown_out_white_count = np.sum((r == 255) & (g == 255) & (b == 255))
    assert pure_black_count == 0, f"Pure black clipping detected: {pure_black_count} pixels"
    assert blown_out_white_count == 0, f"Blown out pure white clipping detected: {blown_out_white_count} pixels"

    # 4. Strict Magenta Missing-Shader Pixel Detection
    # Standard magenta
    mag_standard = np.sum((r > 180) & (b > 180) & (g < 50))
    assert mag_standard == 0, f"Magenta missing shader pixels found (standard criterion): {mag_standard}"

    # Relative chromaticity magenta (high R+B, low G)
    sum_rgb = r + g + b + 1e-5
    chrom_magenta = np.sum(((r + b) / sum_rgb > 0.85) & (g / sum_rgb < 0.12) & (sum_rgb > 100))
    assert chrom_magenta == 0, f"Chromaticity magenta missing shader pixels found: {chrom_magenta}"

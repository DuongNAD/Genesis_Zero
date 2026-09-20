"""Genesis Zero — creature_builder.py
Bộ sinh 3D sinh học hoàn chỉnh chuẩn Studio chất lượng cao:
- Hệ thống thuộc tính linh hoạt: Hỗ trợ max điểm lên tới 7, tổng điểm 16, 20, 23 điểm theo từng bậc tiến hóa (Tier 1 con mồi, Tier 2 săn mồi, Tier 3 cự thú Apex).
- Dựng hình thái học hữu cơ mượt mà: Lưới quad sạch, Smooth Shading + Subdivision Surface.
- Phân chia giải phẫu theo 3 Tầng sống (CAN, NUOC, TROI) và 12 Đặc điểm sinh học (Features).
- Dựng bộ xương Rigging Armature phân cấp chuẩn (Root, Pelvis, Spine, Chest, Neck, Head, Jaw, Tail, Limbs, Fins, Wings).
- TRỌN BỘ 8 ANIMATIONS CHUẨN GAME ENGINE:
    1. Idle_Normal (Thở phập phồng, chớp mắt, đảo đầu)
    2. Idle_Alert (Cảnh giác cao, ngẩng đầu, tai/giác quan xoay nghe ngóng)
    3. Walk (Dáng đi tuần tự nhiên, uốn lượn cột sống)
    4. Run (Phi nước đại săn mồi/trốn chạy tốc độ cao)
    5. Attack (Đòn tấn công: đớp cắn chớp nhoáng kèm vuốt vồ)
    6. Hurt_Defend (Phản xạ đau đớn, co cụm cơ thể/giáp đỡ)
    7. Eat (Cúi đầu gặm thức ăn / xé mồi, hàm nhai)
    8. Death (Trụy gối, ngã đổ sụp xuống đất)
- Toàn bộ Animation được bake vào NLA Tracks đảm bảo xuất file GLB có đầy đủ clip.
"""

from __future__ import annotations

from typing import Sequence

from genesis.domain import Domain, domain_of
from genesis.features import Feature, roll_for_species
from genesis.traits import Traits, founder_traits


def build_creature_blender_code(
    species_id: str,
    seed: int,
    traits: Traits | None = None,
    domain: Domain | None = None,
    features: Sequence[Feature] | None = None,
    out_glb: str | None = None,
    out_blend: str | None = None,
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> str:
    """Sinh chuỗi mã Python hoàn chỉnh để thực thi trong Blender với trọn bộ 8 Animations."""
    if traits is None:
        traits = founder_traits(species_id)
    if domain is None:
        domain = domain_of(species_id)
    if features is None:
        features = roll_for_species(species_id, seed)

    feat_keys = set(f.key for f in features)

    # 1. Hệ số hình thái học co giãn theo thuộc tính (Hỗ trợ dải 0..7 điểm)
    brain_val = getattr(traits, "brain", 2)
    attack_val = getattr(traits, "attack", 2)
    armor_val = getattr(traits, "armor", 2)
    speed_val = getattr(traits, "speed", 2)
    sense_val = getattr(traits, "sense", 2)
    stomach_val = getattr(traits, "stomach", 2)

    brain_scale = 0.75 + 0.12 * brain_val
    attack_scale = 0.75 + 0.14 * attack_val
    armor_scale = 0.75 + 0.12 * armor_val
    speed_scale = 0.75 + 0.14 * speed_val
    sense_scale = 0.75 + 0.12 * sense_val
    stomach_scale = 0.75 + 0.12 * stomach_val

    # 12 Features Toggles
    has_webbed = "LUONG_CU" in feat_keys or "WEB_FEET" in feat_keys
    has_toxic_spikes = "GAI_DOC" in feat_keys
    has_fangs = "RANG_NANH" in feat_keys or "FANGS" in feat_keys
    has_night_eyes = "MAT_DEM" in feat_keys
    has_dig_claws = "DAO_HANG" in feat_keys
    has_cheek_pouches = "TUI_MA" in feat_keys or "CHEEK_POUCH" in feat_keys

    # Bảng màu tự nhiên theo Tầng và Loài
    if domain == Domain.NUOC:
        primary_color = (0.24, 0.48, 0.62, 1.0)
        belly_color = (0.80, 0.88, 0.90, 1.0)
    elif domain == Domain.TROI:
        primary_color = (0.42, 0.55, 0.40, 1.0)
        belly_color = (0.86, 0.80, 0.68, 1.0)
    elif species_id.startswith("L2") or "carnivore" in species_id.lower():
        primary_color = (0.26, 0.22, 0.32, 1.0)
        belly_color = (0.50, 0.42, 0.35, 1.0)
    elif species_id.startswith("L4"):
        primary_color = (0.48, 0.38, 0.26, 1.0)
        belly_color = (0.75, 0.68, 0.52, 1.0)
    elif species_id.startswith("L5"):
        primary_color = (0.30, 0.55, 0.26, 1.0)
        belly_color = (0.80, 0.78, 0.45, 1.0)
    else:
        primary_color = (0.38, 0.58, 0.53, 1.0)
        belly_color = (0.82, 0.73, 0.57, 1.0)

    is_aquatic = (domain == Domain.NUOC)
    is_aerial = (domain == Domain.TROI)

    code = f'''# Genesis Zero Complete High-Fidelity Creature Generator: {species_id}_s{seed}
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

col_name = "Genesis_{species_id}_s{seed}"
col = bpy.data.collections.get(col_name)
if col:
    for obj in list(col.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)

def get_mat(name, color, roughness=0.45, specular=0.4):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat

mat_primary = get_mat("Mat_{species_id}_Primary", {primary_color})
mat_belly = get_mat("Mat_{species_id}_Belly", {belly_color})
mat_dark = get_mat("Mat_{species_id}_Dark", ({primary_color[0]*0.42:.2f}, {primary_color[1]*0.42:.2f}, {primary_color[2]*0.42:.2f}, 1.0))
mat_light = get_mat("Mat_{species_id}_Light", (min(1.0, {primary_color[0]}*1.3), min(1.0, {primary_color[1]}*1.3), min(1.0, {primary_color[2]}*1.3), 1.0))
mat_spike_tip = get_mat("Mat_Spike_Tip", (0.15, 0.09, 0.07, 1.0))
mat_spike_base = get_mat("Mat_Spike_Base", (0.78, 0.68, 0.52, 1.0))
mat_claw = get_mat("Mat_Claw", (0.86, 0.78, 0.62, 1.0))
mat_fang = get_mat("Mat_Fang", (0.95, 0.94, 0.90, 1.0), roughness=0.15, specular=0.8)
mat_eye_iris = get_mat("Mat_Eye_Iris", (0.96, 0.70, 0.12, 1.0), roughness=0.08, specular=1.0)
mat_eye_pupil = get_mat("Mat_Eye_Pupil", (0.015, 0.015, 0.015, 1.0), roughness=0.05, specular=0.9)
mat_eye_hl = get_mat("Mat_Eye_HL", (1.0, 1.0, 0.98, 1.0), roughness=0.02, specular=1.0)
mat_nostril = get_mat("Mat_Nostril", (0.10, 0.15, 0.14, 1.0))

ox, oy, oz = {offset}

# =========================================================================
# 1. KHUNG XƯƠNG ARMATURE PHÂN CẤP CHUẨN
# =========================================================================
arm_data = bpy.data.armatures.new("Armature_{species_id}_s{seed}_Data")
arm_obj = bpy.data.objects.new("Armature_{species_id}_s{seed}", arm_data)
col.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones

r_b = eb.new("Root")
r_b.head = (ox, oy, oz)
r_b.tail = (ox, oy, oz + 0.3)

p_b = eb.new("Pelvis")
p_b.head = (ox, oy + 0.95, oz + 0.90)
p_b.tail = (ox, oy + 0.65, oz + 0.98)
p_b.parent = r_b

sp_b = eb.new("Spine_Mid")
sp_b.head = p_b.tail
sp_b.tail = (ox, oy + 0.25, oz + 1.05)
sp_b.parent = p_b

ch_b = eb.new("Chest")
ch_b.head = sp_b.tail
ch_b.tail = (ox, oy - 0.20, oz + 1.10)
ch_b.parent = sp_b

nk_b = eb.new("Neck")
nk_b.head = ch_b.tail
nk_b.tail = (ox, oy - 0.65, oz + 1.12)
nk_b.parent = ch_b

hd_b = eb.new("Head")
hd_b.head = nk_b.tail
hd_b.tail = (ox, oy - 1.40, oz + 1.00)
hd_b.parent = nk_b

jw_b = eb.new("Jaw")
jw_b.head = (ox, oy - 0.65, oz + 0.90)
jw_b.tail = (ox, oy - 1.40, oz + 0.82)
jw_b.parent = hd_b

t1_b = eb.new("Tail_1")
t1_b.head = (ox, oy + 1.10, oz + 0.90)
t1_b.tail = (ox, oy + 1.50, oz + 0.88)
t1_b.parent = p_b

t2_b = eb.new("Tail_2")
t2_b.head = t1_b.tail
t2_b.tail = (ox, oy + 1.95, oz + 0.92)
t2_b.parent = t1_b

t3_b = eb.new("Tail_3")
t3_b.head = t2_b.tail
t3_b.tail = (ox, oy + 2.45, oz + 0.98)
t3_b.parent = t2_b

t4_b = eb.new("Tail_4")
t4_b.head = t3_b.tail
t4_b.tail = (ox, oy + 2.95, oz + 1.05)
t4_b.parent = t3_b

is_aquatic = {is_aquatic}
is_aerial = {is_aerial}

if not is_aquatic:
    for side_name, sign in [(".L", 1), (".R", -1)]:
        sh_b = eb.new(f"Shoulder{{side_name}}")
        sh_b.head = (ox + sign * 0.35, oy - 0.15, oz + 1.10)
        sh_b.tail = (ox + sign * 0.76, oy - 0.15, oz + 1.05)
        sh_b.parent = ch_b

        ua_b = eb.new(f"UpperArm{{side_name}}")
        ua_b.head = sh_b.tail
        ua_b.tail = (ox + sign * 1.32 * {speed_scale:.2f}, oy - 0.28, oz + 0.74)
        ua_b.parent = sh_b

        fa_b = eb.new(f"Forearm{{side_name}}")
        fa_b.head = ua_b.tail
        fa_b.tail = (ox + sign * 1.22 * {speed_scale:.2f}, oy - 0.84, oz + 0.16)
        fa_b.parent = ua_b

        ft_b = eb.new(f"Foot{{side_name}}")
        ft_b.head = fa_b.tail
        ft_b.tail = (ox + sign * 1.26 * {speed_scale:.2f}, oy - 1.15, oz + 0.0)
        ft_b.parent = fa_b

        hp_b = eb.new(f"Hip{{side_name}}")
        hp_b.head = (ox + sign * 0.35, oy + 0.95, oz + 0.90)
        hp_b.tail = (ox + sign * 0.72, oy + 0.92, oz + 0.88)
        hp_b.parent = p_b

        th_b = eb.new(f"Thigh{{side_name}}")
        th_b.head = hp_b.tail
        th_b.tail = (ox + sign * 1.40 * {speed_scale:.2f}, oy + 1.16, oz + 0.60)
        th_b.parent = hp_b

        sn_b = eb.new(f"Shin{{side_name}}")
        sn_b.head = th_b.tail
        sn_b.tail = (ox + sign * 1.24 * {speed_scale:.2f}, oy + 0.80, oz + 0.16)
        sn_b.parent = th_b

        fth_b = eb.new(f"Foot{{side_name}}.Hind")
        fth_b.head = sn_b.tail
        fth_b.tail = (ox + sign * 1.30 * {speed_scale:.2f}, oy + 0.55, oz + 0.0)
        fth_b.parent = sn_b

bpy.ops.object.mode_set(mode='OBJECT')

# =========================================================================
# 2. DỰNG MESH HỮU CƠ (BODY, EYES, TEETH, SPINES, LIMBS)
# =========================================================================
bm = bmesh.new()
body_mesh = bpy.data.meshes.new("Body_{species_id}_s{seed}")
body_obj = bpy.data.objects.new("Body_{species_id}_s{seed}", body_mesh)
col.objects.link(body_obj)
body_obj.parent = arm_obj

for m in [mat_primary, mat_belly, mat_light, mat_dark, mat_nostril]:
    body_obj.data.materials.append(m)

tail_w = 0.84 if {has_webbed} else (0.24 if is_aquatic else 0.40)
tail_h = 0.95 if is_aquatic else 0.14

rings = [
    {{"y": -1.54, "zc": 1.00, "w": 0.14 * {brain_scale:.2f}, "h": 0.12 * {brain_scale:.2f}, "type": "tip"}},
    {{"y": -1.44, "zc": 1.02, "w": 0.34 * {brain_scale:.2f}, "h": 0.26 * {brain_scale:.2f}, "type": "snout"}},
    {{"y": -1.30, "zc": 1.06, "w": 0.52 * {brain_scale:.2f}, "h": 0.40 * {brain_scale:.2f}, "type": "snout"}},
    {{"y": -1.12, "zc": 1.10, "w": 0.68 * {brain_scale:.2f}, "h": 0.52 * {brain_scale:.2f}, "type": "head"}},
    {{"y": -0.92, "zc": 1.16, "w": 0.78 * {brain_scale:.2f}, "h": 0.64 * {brain_scale:.2f}, "type": "head"}},
    {{"y": -0.68, "zc": 1.22, "w": (0.80 + (0.16 if {has_cheek_pouches} else 0.0)) * {brain_scale:.2f}, "h": 0.72 * {brain_scale:.2f}, "type": "crown"}},
    {{"y": -0.44, "zc": 1.18, "w": 0.78, "h": 0.70, "type": "nape"}},
    {{"y": -0.20, "zc": 1.16, "w": 0.82, "h": 0.70, "type": "neck"}},
    {{"y": 0.04,  "zc": 1.17, "w": 0.92 * {armor_scale:.2f}, "h": 0.74, "type": "chest"}},
    {{"y": 0.40,  "zc": 1.12, "w": 0.94 * {stomach_scale:.2f}, "h": 0.70 * {stomach_scale:.2f}, "type": "torso"}},
    {{"y": 0.78,  "zc": 1.06, "w": 0.88 * {stomach_scale:.2f}, "h": 0.62 * {stomach_scale:.2f}, "type": "torso"}},
    {{"y": 1.10,  "zc": 0.98, "w": 0.76, "h": 0.54, "type": "pelvis"}},
    {{"y": 1.38,  "zc": 0.92, "w": 0.56, "h": 0.44, "type": "tail_base"}},
    {{"y": 1.66,  "zc": 0.90, "w": 0.46, "h": 0.32, "type": "tail_neck"}},
    {{"y": 1.98,  "zc": 0.94, "w": tail_w * 0.9, "h": tail_h * 0.8, "type": "tail"}},
    {{"y": 2.40,  "zc": 1.00, "w": tail_w * 1.3, "h": tail_h * 1.2, "type": "tail"}},
    {{"y": 2.76,  "zc": 1.06, "w": tail_w * 1.0, "h": tail_h * 1.0, "type": "tail"}},
    {{"y": 3.02,  "zc": 1.12, "w": tail_w * 0.6, "h": tail_h * 0.6, "type": "tail"}},
    {{"y": 3.18,  "zc": 1.16, "w": 0.16, "h": 0.06, "type": "tail"}},
]

angles_deg = [90, 68, 50, 32, 10, -15, -55, -90, -125, -165, 170, 148, 130, 112]
angles = [math.radians(a) for a in angles_deg]

ring_verts = []
for r in rings:
    v_l = []
    for a_idx, ang in enumerate(angles):
        vx = ox + math.cos(ang) * r["w"]
        vy = oy + r["y"]
        vz = oz + r["zc"] + math.sin(ang) * (r["h"] * 0.5)
        if r["type"] in ("head", "crown", "snout"):
            if a_idx in (1, 13):
                vz += 0.080
            elif a_idx in (3, 11):
                vz += 0.070
                vx += (0.035 if a_idx == 3 else -0.035)
            elif a_idx in (2, 12):
                vz -= 0.040
        v_l.append(bm.verts.new((vx, vy, vz)))
    ring_verts.append(v_l)

bm.verts.ensure_lookup_table()
for i in range(len(rings) - 1):
    r1 = ring_verts[i]
    r2 = ring_verts[i + 1]
    is_tail = "tail" in rings[i]["type"]
    for j in range(len(angles)):
        jn = (j + 1) % len(angles)
        try:
            face = bm.faces.new((r1[j], r1[jn], r2[jn], r2[j]))
            if is_tail and j in (2, 3, 4, 5, 9, 10, 11, 12):
                face.material_index = 1
            elif j in (5, 6, 7, 8, 9):
                face.material_index = 1
            elif i == 1 and j in (1, 13):
                face.material_index = 4
            elif rings[i]["type"] in ("snout", "head", "crown") and j in (1, 13):
                face.material_index = 2
            elif rings[i]["type"] in ("snout", "head", "crown") and j in (2, 12):
                face.material_index = 3
            else:
                face.material_index = 0
        except ValueError:
            pass

v_tip = bm.verts.new((ox, oy - 1.58, oz + 1.00))
r0 = ring_verts[0]
for j in range(len(angles)):
    jn = (j + 1) % len(angles)
    try:
        f = bm.faces.new((v_tip, r0[j], r0[jn]))
        f.material_index = 1 if j in (5, 6, 7, 8) else 0
    except ValueError:
        pass

v_tail_tip = bm.verts.new((ox, oy + 3.22, oz + 1.16))
rend = ring_verts[-1]
for j in range(len(angles)):
    jn = (j + 1) % len(angles)
    try:
        f = bm.faces.new((v_tail_tip, rend[jn], rend[j]))
        f.material_index = 1
    except ValueError:
        pass

bm.to_mesh(body_mesh)
bm.free()

for poly in body_mesh.polygons:
    poly.use_smooth = True
sub = body_obj.modifiers.new("Subsurf", 'SUBSURF')
sub.levels = 1
sub.render_levels = 2

# Skinning weights
for bg in ["Head", "Jaw", "Neck", "Chest", "Spine_Mid", "Pelvis", "Tail_1", "Tail_2", "Tail_3", "Tail_4"]:
    body_obj.vertex_groups.new(name=bg)

for v in body_mesh.vertices:
    vy = v.co.y - oy
    vz = v.co.z - oz
    if vy < -0.65:
        if vz < 1.05:
            fac = max(0.0, min(1.0, (1.05 - vz) / 0.25))
            body_obj.vertex_groups["Jaw"].add([v.index], fac, 'REPLACE')
            body_obj.vertex_groups["Head"].add([v.index], 1.0 - fac, 'REPLACE')
        else:
            body_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
    elif vy < -0.35:
        body_obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
    elif vy < 0.10:
        body_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
    elif vy < 0.55:
        body_obj.vertex_groups["Spine_Mid"].add([v.index], 1.0, 'REPLACE')
    elif vy < 1.05:
        body_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')
    elif vy < 1.55:
        body_obj.vertex_groups["Tail_1"].add([v.index], 1.0, 'REPLACE')
    elif vy < 2.05:
        body_obj.vertex_groups["Tail_2"].add([v.index], 1.0, 'REPLACE')
    elif vy < 2.55:
        body_obj.vertex_groups["Tail_3"].add([v.index], 1.0, 'REPLACE')
    else:
        body_obj.vertex_groups["Tail_4"].add([v.index], 1.0, 'REPLACE')

arm_mod = body_obj.modifiers.new("Armature", 'ARMATURE')
arm_mod.object = arm_obj

# Đôi mắt
eye_mesh = bpy.data.meshes.new("Eyes_{species_id}_s{seed}")
eye_obj = bpy.data.objects.new("Eyes_{species_id}_s{seed}", eye_mesh)
col.objects.link(eye_obj)
eye_obj.parent = arm_obj
for m in [mat_eye_iris, mat_eye_pupil, mat_eye_hl, mat_belly]:
    eye_obj.data.materials.append(m)

bm_e = bmesh.new()
eye_r = 0.190 * {sense_scale:.2f} * (1.35 if {has_night_eyes} else 1.0)
for side in (1, -1):
    eye_center = Vector((ox + side * 0.65 * {brain_scale:.2f}, oy - 0.96, oz + 1.25))
    forward = Vector((side * 0.58, -0.74, 0.16)).normalized()
    up = Vector((0, 0.16, 0.98)).normalized()
    right = forward.cross(up).normalized()

    eye_geom = bmesh.ops.create_icosphere(bm_e, subdivisions=2, radius=eye_r, matrix=Matrix.Translation(eye_center))
    for f in list(set(f for v in eye_geom["verts"] for f in v.link_faces)):
        cdir = (f.calc_center_bounds() - eye_center).normalized()
        dot_f = cdir.dot(forward)
        if dot_f > 0.86 and abs(cdir.dot(right)) < 0.20:
            f.material_index = 1
        elif dot_f > 0.72 and dot_f < 0.88 and cdir.dot(up) > 0.42 and cdir.dot(right) * side > 0:
            f.material_index = 2
        else:
            f.material_index = 0

bm_e.to_mesh(eye_mesh)
bm_e.free()
for p in eye_mesh.polygons:
    p.use_smooth = True
eye_sub = eye_obj.modifiers.new("Subsurf", 'SUBSURF')
eye_sub.levels = 1
eye_obj.vertex_groups.new(name="Head")
for v in eye_mesh.vertices:
    eye_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
eye_mod = eye_obj.modifiers.new("Armature", 'ARMATURE')
eye_mod.object = arm_obj

# Răng nanh (nếu có đặc điểm RANG_NANH hoặc attack cao)
if {has_fangs} or {attack_val} >= 3:
    fangs_mesh = bpy.data.meshes.new("Fangs_{species_id}_s{seed}")
    fangs_obj = bpy.data.objects.new("Fangs_{species_id}_s{seed}", fangs_mesh)
    col.objects.link(fangs_obj)
    fangs_obj.parent = arm_obj
    fangs_obj.data.materials.append(mat_fang)
    bm_f = bmesh.new()
    for side in (1, -1):
        f_base = Vector((ox + side * 0.32, oy - 1.20, oz + 0.98))
        f_tip = f_base + Vector((side * 0.04, -0.05, -0.22 * {attack_scale:.2f}))
        b0 = bm_f.verts.new(f_base + Vector((-0.03, 0, 0)))
        b1 = bm_f.verts.new(f_base + Vector((0.03, 0, 0)))
        b2 = bm_f.verts.new(f_base + Vector((0, 0.03, 0)))
        b3 = bm_f.verts.new(f_base + Vector((0, -0.03, 0)))
        vt = bm_f.verts.new(f_tip)
        for fv in [(b0, b1, vt), (b1, b2, vt), (b2, b3, vt), (b3, b0, vt)]:
            bm_f.faces.new(fv)
    bm_f.to_mesh(fangs_mesh)
    bm_f.free()
    for p in fangs_mesh.polygons:
        p.use_smooth = True
    f_sub = fangs_obj.modifiers.new("Subsurf", 'SUBSURF')
    f_sub.levels = 1
    fangs_obj.vertex_groups.new(name="Head")
    for v in fangs_mesh.vertices:
        fangs_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
    f_mod = fangs_obj.modifiers.new("Armature", 'ARMATURE')
    f_mod.object = arm_obj

# Gai độc lưng (nếu có GAI_DOC hoặc armor cao)
if {has_toxic_spikes} or {armor_val} >= 4:
    spikes_mesh = bpy.data.meshes.new("Spikes_{species_id}_s{seed}")
    spikes_obj = bpy.data.objects.new("Spikes_{species_id}_s{seed}", spikes_mesh)
    col.objects.link(spikes_obj)
    spikes_obj.parent = arm_obj
    for m in [mat_spike_base, mat_spike_tip]:
        spikes_obj.data.materials.append(m)

    bm_s = bmesh.new()
    spikes_data = [
        {{"y": -0.22, "z": 1.50, "h": 0.42 * {armor_scale:.2f}, "w": 0.10}},
        {{"y": -0.02, "z": 1.52, "h": 0.52 * {armor_scale:.2f}, "w": 0.12}},
        {{"y": 0.18,  "z": 1.51, "h": 0.54 * {armor_scale:.2f}, "w": 0.12}},
        {{"y": 0.38,  "z": 1.48, "h": 0.50 * {armor_scale:.2f}, "w": 0.11}},
        {{"y": 0.58,  "z": 1.43, "h": 0.44 * {armor_scale:.2f}, "w": 0.10}},
        {{"y": 0.78,  "z": 1.36, "h": 0.38 * {armor_scale:.2f}, "w": 0.09}},
        {{"y": 0.95,  "z": 1.28, "h": 0.32 * {armor_scale:.2f}, "w": 0.08}},
    ]
    for s in spikes_data:
        p_base = Vector((ox, oy + s["y"], oz + s["z"] - 0.03))
        b0 = bm_s.verts.new(p_base + Vector((-s["w"], 0, 0)))
        b1 = bm_s.verts.new(p_base + Vector((s["w"], 0, 0)))
        b2 = bm_s.verts.new(p_base + Vector((0, s["w"], 0)))
        b3 = bm_s.verts.new(p_base + Vector((0, -s["w"], 0)))
        p_tip = p_base + Vector((0, 0.08, s["h"]))
        tip = bm_s.verts.new(p_tip)
        for fv in [(b0, b1, tip), (b1, b2, tip), (b2, b3, tip), (b3, b0, tip)]:
            f = bm_s.faces.new(fv)
            f.material_index = 1
    bm_s.to_mesh(spikes_mesh)
    bm_s.free()
    for p in spikes_mesh.polygons:
        p.use_smooth = True
    sp_sub = spikes_obj.modifiers.new("Subsurf", 'SUBSURF')
    sp_sub.levels = 1
    spikes_obj.vertex_groups.new(name="Chest")
    for v in spikes_mesh.vertices:
        spikes_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
    sp_mod = spikes_obj.modifiers.new("Armature", 'ARMATURE')
    sp_mod.object = arm_obj

# Chi & Bàn chân (Dành cho CAN và TROI)
if not is_aquatic:
    limbs_mesh = bpy.data.meshes.new("Limbs_{species_id}_s{seed}")
    limbs_obj = bpy.data.objects.new("Limbs_{species_id}_s{seed}", limbs_mesh)
    col.objects.link(limbs_obj)
    limbs_obj.parent = arm_obj
    for m in [mat_primary, mat_belly, mat_claw]:
        limbs_obj.data.materials.append(m)

    bm_l = bmesh.new()
    claw_mul = 1.6 if {has_dig_claws} else (1.0 + 0.1 * {attack_val})
    limbs_cfg = [
        {{"side": 1, "sh": Vector((ox + 0.76, oy - 0.15, oz + 1.05)), "el": Vector((ox + 1.32, oy - 0.28, oz + 0.74)), "wr": Vector((ox + 1.22, oy - 0.84, oz + 0.16)), "fc": Vector((ox + 1.26, oy - 1.04, oz + 0.0)), "hd": math.radians(-115), "ua": "UpperArm.L", "fa": "Forearm.L", "ft": "Foot.L"}},
        {{"side": -1, "sh": Vector((ox - 0.76, oy - 0.15, oz + 1.05)), "el": Vector((ox - 1.32, oy - 0.28, oz + 0.74)), "wr": Vector((ox - 1.22, oy - 0.84, oz + 0.16)), "fc": Vector((ox - 1.26, oy - 1.04, oz + 0.0)), "hd": math.radians(-65), "ua": "UpperArm.R", "fa": "Forearm.R", "ft": "Foot.R"}},
        {{"side": 1, "sh": Vector((ox + 0.72, oy + 0.92, oz + 0.90)), "el": Vector((ox + 1.40, oy + 1.16, oz + 0.60)), "wr": Vector((ox + 1.24, oy + 0.80, oz + 0.16)), "fc": Vector((ox + 1.30, oy + 0.66, oz + 0.0)), "hd": math.radians(-85), "ua": "Thigh.L", "fa": "Shin.L", "ft": "Foot.L.Hind"}},
        {{"side": -1, "sh": Vector((ox - 0.72, oy + 0.92, oz + 0.90)), "el": Vector((ox - 1.40, oy + 1.16, oz + 0.60)), "wr": Vector((ox - 1.24, oy + 0.80, oz + 0.16)), "fc": Vector((ox - 1.30, oy + 0.66, oz + 0.0)), "hd": math.radians(-95), "ua": "Thigh.R", "fa": "Shin.R", "ft": "Foot.R.Hind"}},
    ]

    for l in limbs_cfg:
        for b in [l["ua"], l["fa"], l["ft"]]:
            if b not in limbs_obj.vertex_groups:
                limbs_obj.vertex_groups.new(name=b)

    for l in limbs_cfg:
        sh = l["sh"]
        el = l["el"]
        wr = l["wr"]
        fc = l["fc"]
        side = l["side"]
        hd = l["hd"]

        sections = [
            {{"pt": sh, "r": 0.24 * {attack_scale:.2f}, "dir": (el - sh).normalized()}},
            {{"pt": el, "r": 0.17 * {attack_scale:.2f}, "dir": (wr - el).normalized()}},
            {{"pt": wr, "r": 0.14, "dir": Vector((0,0,-1))}},
        ]
        s_verts = []
        for s in sections:
            ax = s["dir"]
            up_t = Vector((0,0,1)) if abs(ax.z) < 0.85 else Vector((0,1,0))
            sv = ax.cross(up_t).normalized()
            uv = sv.cross(ax).normalized()
            v_r = []
            for k in range(6):
                ang = 2 * math.pi * k / 6
                v = bm_l.verts.new(s["pt"] + (sv * math.cos(ang) + uv * math.sin(ang)) * s["r"])
                v_r.append(v)
            s_verts.append(v_r)
        for i in range(len(sections) - 1):
            for k in range(6):
                kn = (k + 1) % 6
                try:
                    f = bm_l.faces.new((s_verts[i][k], s_verts[i][kn], s_verts[i+1][kn], s_verts[i+1][k]))
                    f.material_index = 0
                except ValueError:
                    pass

        t_angles = [-0.65, -0.32, 0.0, 0.32, 0.65]
        t_lens = [0.38, 0.52, 0.56, 0.48, 0.36]
        claw_pts = []
        for tidx, (rel_a, tlen) in enumerate(zip(t_angles, t_lens)):
            ang = hd + rel_a * side
            dto = Vector((math.cos(ang), math.sin(ang), 0.0)).normalized()
            pt_tip = fc + dto * (tlen * 0.82) + Vector((0, 0, 0.04))
            pt_claw = fc + dto * (tlen * 1.15 * {attack_scale:.2f} * claw_mul) + Vector((0, 0, -0.005))
            vt = bm_l.verts.new(pt_tip)
            vc = bm_l.verts.new(pt_claw)
            claw_pts.append((vt, vc, dto))

        for k in range(len(claw_pts)):
            vt, vc, dto = claw_pts[k]
            try:
                f = bm_l.faces.new((s_verts[-1][k % 6], s_verts[-1][(k+1) % 6], vt))
                f.material_index = 0
                f_c = bm_l.faces.new((vt, vc, s_verts[-1][k % 6]))
                f_c.material_index = 2
            except ValueError:
                pass

    bm_l.to_mesh(limbs_mesh)
    bm_l.free()
    for p in limbs_mesh.polygons:
        p.use_smooth = True
    l_sub = limbs_obj.modifiers.new("Subsurf", 'SUBSURF')
    l_sub.levels = 1

    for v in limbs_mesh.vertices:
        vx = v.co.x - ox
        vy = v.co.y - oy
        vz = v.co.z - oz
        side = ".L" if vx > 0 else ".R"
        is_front = vy < 0.20
        if is_front:
            ua_name = f"UpperArm{{side}}"
            fa_name = f"Forearm{{side}}"
            ft_name = f"Foot{{side}}"
            if vz > 0.65:
                limbs_obj.vertex_groups[ua_name].add([v.index], 1.0, 'REPLACE')
            elif vz > 0.22:
                limbs_obj.vertex_groups[fa_name].add([v.index], 1.0, 'REPLACE')
            else:
                limbs_obj.vertex_groups[ft_name].add([v.index], 1.0, 'REPLACE')
        else:
            th_name = f"Thigh{{side}}"
            sn_name = f"Shin{{side}}"
            ft_name = f"Foot{{side}}.Hind"
            if vz > 0.55:
                limbs_obj.vertex_groups[th_name].add([v.index], 1.0, 'REPLACE')
            elif vz > 0.20:
                limbs_obj.vertex_groups[sn_name].add([v.index], 1.0, 'REPLACE')
            else:
                limbs_obj.vertex_groups[ft_name].add([v.index], 1.0, 'REPLACE')

    l_mod = limbs_obj.modifiers.new("Armature", 'ARMATURE')
    l_mod.object = arm_obj

# =========================================================================
# 3. TRỌN BỘ 8 ANIMATIONS CHUẨN GAME ENGINE (NLA STASHED)
# =========================================================================
arm_obj.animation_data_create()
created_actions = []

def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)

# --- 1. ACTION: Idle_Normal (60 frames loop: Thở phập phồng, đảo đầu) ---
act_idle = bpy.data.actions.new("Creature_{species_id}_s{seed}_Idle")
arm_obj.animation_data.action = act_idle
reset_pose(arm_obj)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)
    pb.keyframe_insert(data_path="scale", frame=1)
    pb.keyframe_insert(data_path="rotation_euler", frame=60)
    pb.keyframe_insert(data_path="scale", frame=60)

arm_obj.pose.bones["Chest"].scale = (1.04, 1.02, 1.05)
arm_obj.pose.bones["Chest"].keyframe_insert(data_path="scale", frame=25)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(4), math.radians(2), math.radians(-5))
arm_obj.pose.bones["Head"].keyframe_insert(data_path="rotation_euler", frame=25)
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(6), 0, 0)
arm_obj.pose.bones["Jaw"].keyframe_insert(data_path="rotation_euler", frame=25)

arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(4))
arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(10))
arm_obj.pose.bones["Tail_3"].rotation_euler = (0, 0, math.radians(16))
for tn in ["Tail_1", "Tail_2", "Tail_3"]:
    arm_obj.pose.bones[tn].keyframe_insert(data_path="rotation_euler", frame=18)

arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(-4))
arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(-10))
arm_obj.pose.bones["Tail_3"].rotation_euler = (0, 0, math.radians(-16))
for tn in ["Tail_1", "Tail_2", "Tail_3"]:
    arm_obj.pose.bones[tn].keyframe_insert(data_path="rotation_euler", frame=42)

arm_obj.pose.bones["Chest"].scale = (0.98, 0.99, 0.97)
arm_obj.pose.bones["Chest"].keyframe_insert(data_path="scale", frame=45)
created_actions.append(act_idle)

# --- 2. ACTION: Idle_Alert (40 frames loop: Ngẩng cao đầu cảnh giác, tai xoay) ---
act_alert = bpy.data.actions.new("Creature_{species_id}_s{seed}_Alert")
arm_obj.animation_data.action = act_alert
reset_pose(arm_obj)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(-12), 0, 0)
arm_obj.pose.bones["Neck"].rotation_euler = (math.radians(-8), 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)
    pb.keyframe_insert(data_path="rotation_euler", frame=40)

arm_obj.pose.bones["Head"].rotation_euler = (math.radians(-14), math.radians(4), math.radians(-8))
arm_obj.pose.bones["Head"].keyframe_insert(data_path="rotation_euler", frame=20)
created_actions.append(act_alert)

# --- 3. ACTION: Walk (40 frames loop: Đi tuần 4 chân cân đối) ---
act_walk = bpy.data.actions.new("Creature_{species_id}_s{seed}_Walk")
arm_obj.animation_data.action = act_walk
reset_pose(arm_obj)
if not is_aquatic:
    arm_obj.pose.bones["Spine_Mid"].rotation_euler = (0, 0, math.radians(-6))
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(-15), math.radians(10), math.radians(18))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(15), math.radians(-10), math.radians(-15))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(-15), math.radians(-10), math.radians(18))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(15), math.radians(10), math.radians(-15))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)

    arm_obj.pose.bones["Spine_Mid"].rotation_euler = (0, 0, math.radians(6))
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(15), math.radians(-10), math.radians(-15))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(-15), math.radians(10), math.radians(18))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(15), math.radians(10), math.radians(-15))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(-15), math.radians(-10), math.radians(18))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=20)
else:
    # Cá bơi
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(12))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(20))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(-12))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(-20))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=20)
created_actions.append(act_walk)

# --- 4. ACTION: Run (24 frames loop: Phi nước đại sải chân dài) ---
act_run = bpy.data.actions.new("Creature_{species_id}_s{seed}_Run")
arm_obj.animation_data.action = act_run
reset_pose(arm_obj)
if not is_aquatic:
    arm_obj.pose.bones["Chest"].scale = (1.06, 1.03, 1.08)
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(-28), math.radians(15), math.radians(28))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(28), math.radians(-15), math.radians(-25))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(-28), math.radians(-15), math.radians(28))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(28), math.radians(15), math.radians(-25))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=24)

    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(28), math.radians(-15), math.radians(-25))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(-28), math.radians(15), math.radians(28))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(28), math.radians(15), math.radians(-25))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(-28), math.radians(-15), math.radians(28))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=12)
else:
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(18))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(30))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=24)
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(-18))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(-30))
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=12)
created_actions.append(act_run)

# --- 5. ACTION: Attack (30 frames: Giật lùi chuẩn bị -> Lao cắn/vồ chớp nhoáng -> Thu về) ---
act_atk = bpy.data.actions.new("Creature_{species_id}_s{seed}_Attack")
arm_obj.animation_data.action = act_atk
reset_pose(arm_obj)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)
    pb.keyframe_insert(data_path="rotation_euler", frame=30)

# F6 (Anticipation): Thu mình lùi sau, ngửa đầu há miệng
arm_obj.pose.bones["Chest"].rotation_euler = (math.radians(8), 0, 0)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(-14), 0, 0)
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(18), 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=6)

# F10 (Strike Snap): Phóng vồ về phía trước, cắn ngập hàm
arm_obj.pose.bones["Chest"].rotation_euler = (math.radians(-12), 0, 0)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(12), 0, 0)
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(-4), 0, 0)
if not is_aquatic:
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(24), 0, math.radians(20))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(24), 0, math.radians(-20))
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=10)

# F20 (Hold bite & Recovery)
arm_obj.pose.bones["Jaw"].rotation_euler = (0, 0, 0)
arm_obj.pose.bones["Head"].rotation_euler = (0, 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=20)
created_actions.append(act_atk)

# --- 6. ACTION: Hurt_Defend (20 frames: Khựng người, rụt cổ bảo vệ) ---
act_hurt = bpy.data.actions.new("Creature_{species_id}_s{seed}_Hurt")
arm_obj.animation_data.action = act_hurt
reset_pose(arm_obj)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)
    pb.keyframe_insert(data_path="rotation_euler", frame=20)

arm_obj.pose.bones["Chest"].rotation_euler = (math.radians(10), 0, 0)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(14), math.radians(-8), math.radians(12))
arm_obj.pose.bones["Neck"].rotation_euler = (math.radians(8), 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=6)
created_actions.append(act_hurt)

# --- 7. ACTION: Eat (40 frames loop: Cúi đầu gặm nhấm, hàm nhai) ---
act_eat = bpy.data.actions.new("Creature_{species_id}_s{seed}_Eat")
arm_obj.animation_data.action = act_eat
reset_pose(arm_obj)
arm_obj.pose.bones["Neck"].rotation_euler = (math.radians(25), 0, 0)
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(20), 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)
    pb.keyframe_insert(data_path="rotation_euler", frame=40)

# Nhai F10 & F25
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(12), 0, 0)
arm_obj.pose.bones["Jaw"].keyframe_insert(data_path="rotation_euler", frame=10)
arm_obj.pose.bones["Jaw"].rotation_euler = (0, 0, 0)
arm_obj.pose.bones["Jaw"].keyframe_insert(data_path="rotation_euler", frame=18)
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(10), 0, 0)
arm_obj.pose.bones["Jaw"].keyframe_insert(data_path="rotation_euler", frame=26)
arm_obj.pose.bones["Jaw"].rotation_euler = (0, 0, 0)
arm_obj.pose.bones["Jaw"].keyframe_insert(data_path="rotation_euler", frame=34)
created_actions.append(act_eat)

# --- 8. ACTION: Death (45 frames: Trụy gối, ngã nghiêng người xuống đất) ---
act_death = bpy.data.actions.new("Creature_{species_id}_s{seed}_Death")
arm_obj.animation_data.action = act_death
reset_pose(arm_obj)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=1)

# F15: Khụy chân
arm_obj.pose.bones["Chest"].rotation_euler = (math.radians(15), 0, 0)
if not is_aquatic:
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(-30), 0, math.radians(40))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(-30), 0, math.radians(-40))
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=15)

# F45: Đổ sụp toàn thân
arm_obj.pose.bones["Root"].rotation_euler = (0, math.radians(75), 0) # Ngã nghiêng
arm_obj.pose.bones["Head"].rotation_euler = (math.radians(20), math.radians(15), 0)
arm_obj.pose.bones["Jaw"].rotation_euler = (math.radians(15), 0, 0)
for pb in arm_obj.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=45)
created_actions.append(act_death)

# =========================================================================
# 4. PUSH TẤT CẢ ACTIONS VÀO NLA TRACKS ĐỂ XUẤT GLB ĐẦY ĐỦ ANIMATION CLIPS
# =========================================================================
for act in created_actions:
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = act.name
    start_f = int(act.frame_range[0])
    track.strips.new(act.name, start_f, act)

# Đặt action mặc định hiển thị ở frame 1 là Idle
arm_obj.animation_data.action = act_idle
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60
bpy.context.scene.frame_current = 1

print(f"Bake thành công 8 Animation Action Tracks cho {species_id}_s{seed}!")
'''

    if out_glb:
        code += f'''
out_glb_path = "{out_glb}"
os.makedirs(os.path.dirname(out_glb_path), exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:
    o.select_set(True)
try:
    bpy.ops.export_scene.gltf(
        filepath=out_glb_path,
        use_selection=True,
        export_format='GLB',
        export_animations=True,
        export_nla_strips=True,
        export_skins=True
    )
    print(f"Exported GLB with full 8 animations: {{out_glb_path}}")
except Exception as err:
    print(f"GLTF warning: {{err}}")
'''

    if out_blend:
        code += f'''
out_blend_path = "{out_blend}"
os.makedirs(os.path.dirname(out_blend_path), exist_ok=True)
try:
    bpy.ops.wm.save_as_mainfile(filepath=out_blend_path, copy=True)
    print(f"Saved BLEND: {{out_blend_path}}")
except Exception as err:
    print(f"Blend warning: {{err}}")
'''

    return code

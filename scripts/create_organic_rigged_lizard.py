import math
import os

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector


def clear_collection(col_name="Genesis_Lizard"):
    col = bpy.data.collections.get(col_name)
    if col:
        for obj in list(col.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    return col

def get_or_create_material(name, color, roughness=0.45, specular=0.4):
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
    else:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = color
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = roughness
            if "Specular IOR Level" in bsdf.inputs:
                bsdf.inputs["Specular IOR Level"].default_value = specular
    return mat

def setup_materials():
    return {
        # Màu da lưng ngọc lục celadon tự nhiên
        "green": get_or_create_material("Lizard_Green", (0.38, 0.58, 0.53, 1.0), roughness=0.45, specular=0.35),
        # Màu ngọc sáng cho gờ sống đón sáng
        "light_green": get_or_create_material("Lizard_LightGreen", (0.50, 0.68, 0.62, 1.0), roughness=0.42, specular=0.38),
        # Màu ngọc sẫm cho sọc rãnh hoa văn sinh học
        "dark_green": get_or_create_material("Lizard_DarkGreen", (0.20, 0.34, 0.30, 1.0), roughness=0.48, specular=0.30),
        # Màu vàng cát kem ấm tự nhiên cho bụng, hàm dưới, viền đuôi
        "belly": get_or_create_material("Lizard_Belly", (0.82, 0.73, 0.57, 1.0), roughness=0.48, specular=0.32),
        # Gai sừng tự nhiên 2 màu: Chóp sừng nâu đen đậm, gốc vàng cát
        "spike_tip": get_or_create_material("Lizard_Spike_Tip", (0.15, 0.09, 0.07, 1.0), roughness=0.35, specular=0.45),
        "spike_base": get_or_create_material("Lizard_Spike_Base", (0.78, 0.68, 0.52, 1.0), roughness=0.45, specular=0.35),
        # Mắt sinh vật sống: Giác mạc ướt bóng, tròng vàng hổ phách, đồng tử đen
        "eye_iris": get_or_create_material("Lizard_Eye_Iris", (0.96, 0.70, 0.12, 1.0), roughness=0.08, specular=1.0),
        "eye_pupil": get_or_create_material("Lizard_Eye_Pupil", (0.015, 0.015, 0.015, 1.0), roughness=0.05, specular=0.9),
        "eye_highlight": get_or_create_material("Lizard_Eye_Highlight", (1.0, 1.0, 0.98, 1.0), roughness=0.02, specular=1.0),
        # Móng vuốt chất sừng tự nhiên
        "claw": get_or_create_material("Lizard_Claw", (0.86, 0.78, 0.62, 1.0), roughness=0.35, specular=0.45),
        # Lỗ mũi
        "nostril": get_or_create_material("Lizard_Nostril", (0.10, 0.16, 0.14, 1.0), roughness=0.6, specular=0.2),
    }

def build_lizard_armature(collection, offset=(0, 0, 0)):
    ox, oy, oz = offset

    arm_data = bpy.data.armatures.new("Lizard_Armature_Data")
    arm_obj = bpy.data.objects.new("Lizard_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    eb = arm_data.edit_bones

    root_b = eb.new("Root")
    root_b.head = (ox, oy, oz)
    root_b.tail = (ox, oy, oz + 0.3)

    pelvis_b = eb.new("Pelvis")
    pelvis_b.head = (ox, oy + 0.95, oz + 0.90)
    pelvis_b.tail = (ox, oy + 0.65, oz + 0.98)
    pelvis_b.parent = root_b

    spine_b = eb.new("Spine_Mid")
    spine_b.head = pelvis_b.tail
    spine_b.tail = (ox, oy + 0.25, oz + 1.05)
    spine_b.parent = pelvis_b

    chest_b = eb.new("Chest")
    chest_b.head = spine_b.tail
    chest_b.tail = (ox, oy - 0.20, oz + 1.10)
    chest_b.parent = spine_b

    neck_b = eb.new("Neck")
    neck_b.head = chest_b.tail
    neck_b.tail = (ox, oy - 0.65, oz + 1.12)
    neck_b.parent = chest_b

    head_b = eb.new("Head")
    head_b.head = neck_b.tail
    head_b.tail = (ox, oy - 1.40, oz + 1.00)
    head_b.parent = neck_b

    jaw_b = eb.new("Jaw")
    jaw_b.head = (ox, oy - 0.65, oz + 0.90)
    jaw_b.tail = (ox, oy - 1.40, oz + 0.82)
    jaw_b.parent = head_b

    tail1_b = eb.new("Tail_1")
    tail1_b.head = (ox, oy + 1.10, oz + 0.90)
    tail1_b.tail = (ox, oy + 1.50, oz + 0.88)
    tail1_b.parent = pelvis_b

    tail2_b = eb.new("Tail_2")
    tail2_b.head = tail1_b.tail
    tail2_b.tail = (ox, oy + 1.95, oz + 0.92)
    tail2_b.parent = tail1_b

    tail3_b = eb.new("Tail_3")
    tail3_b.head = tail2_b.tail
    tail3_b.tail = (ox, oy + 2.45, oz + 0.98)
    tail3_b.parent = tail2_b

    tail4_b = eb.new("Tail_4")
    tail4_b.head = tail3_b.tail
    tail4_b.tail = (ox, oy + 2.95, oz + 1.05)
    tail4_b.parent = tail3_b

    for side_name, sign in [(".L", 1), (".R", -1)]:
        sh_b = eb.new(f"Shoulder{side_name}")
        sh_b.head = (ox + sign * 0.35, oy - 0.15, oz + 1.10)
        sh_b.tail = (ox + sign * 0.76, oy - 0.15, oz + 1.05)
        sh_b.parent = chest_b

        ua_b = eb.new(f"UpperArm{side_name}")
        ua_b.head = sh_b.tail
        ua_b.tail = (ox + sign * 1.32, oy - 0.28, oz + 0.74)
        ua_b.parent = sh_b

        fa_b = eb.new(f"Forearm{side_name}")
        fa_b.head = ua_b.tail
        fa_b.tail = (ox + sign * 1.22, oy - 0.84, oz + 0.16)
        fa_b.parent = ua_b

        ft_b = eb.new(f"Foot{side_name}")
        ft_b.head = fa_b.tail
        ft_b.tail = (ox + sign * 1.26, oy - 1.15, oz + 0.0)
        ft_b.parent = fa_b

        hip_b = eb.new(f"Hip{side_name}")
        hip_b.head = (ox + sign * 0.35, oy + 0.95, oz + 0.90)
        hip_b.tail = (ox + sign * 0.72, oy + 0.92, oz + 0.88)
        hip_b.parent = pelvis_b

        th_b = eb.new(f"Thigh{side_name}")
        th_b.head = hip_b.tail
        th_b.tail = (ox + sign * 1.40, oy + 1.16, oz + 0.60)
        th_b.parent = hip_b

        shn_b = eb.new(f"Shin{side_name}")
        shn_b.head = th_b.tail
        shn_b.tail = (ox + sign * 1.24, oy + 0.80, oz + 0.16)
        shn_b.parent = th_b

        fth_b = eb.new(f"Foot{side_name}.Hind")
        fth_b.head = shn_b.tail
        fth_b.tail = (ox + sign * 1.30, oy + 0.55, oz + 0.0)
        fth_b.parent = shn_b

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def apply_organic_smoothing(obj, subsurf_levels=1):
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.data.update()

    sub = obj.modifiers.get("Subsurf")
    if not sub:
        sub = obj.modifiers.new("Subsurf", 'SUBSURF')
    sub.levels = subsurf_levels
    sub.render_levels = 2

def create_organic_lizard(collection, mats, arm_obj, offset=(0, 0, 0)):
    ox, oy, oz = offset

    # -------------------------------------------------------------
    # 1. THÂN, ĐẦU VỚI MÕM MŨI TRÒN TRỊA & LIỀN KHỐI (Smooth Tapered Snout)
    # -------------------------------------------------------------
    rings_data = [
        # Chóp mũi thon tròn mượt mà (Smooth rounded nose tip)
        {"y": -1.54, "zc": 1.00, "w": 0.14, "h": 0.12, "type": "snout_tip", "tilt_z": 0.04, "yaw": -0.06},
        {"y": -1.44, "zc": 1.02, "w": 0.34, "h": 0.26, "type": "snout_tip", "tilt_z": 0.04, "yaw": -0.06},
        {"y": -1.30, "zc": 1.06, "w": 0.52, "h": 0.40, "type": "snout",     "tilt_z": 0.03, "yaw": -0.05},
        {"y": -1.12, "zc": 1.10, "w": 0.68, "h": 0.52, "type": "snout",     "tilt_z": 0.03, "yaw": -0.05},
        {"y": -0.92, "zc": 1.16, "w": 0.78, "h": 0.64, "type": "head",      "tilt_z": 0.02, "yaw": -0.04},
        {"y": -0.68, "zc": 1.22, "w": 0.80, "h": 0.72, "type": "crown",     "tilt_z": 0.01, "yaw": -0.02},
        {"y": -0.44, "zc": 1.18, "w": 0.78, "h": 0.70, "type": "nape",      "tilt_z": 0.00, "yaw": 0.00},
        {"y": -0.20, "zc": 1.16, "w": 0.82, "h": 0.70, "type": "neck",      "tilt_z": 0.00, "yaw": 0.00},
        {"y": 0.04,  "zc": 1.17, "w": 0.92, "h": 0.74, "type": "chest",     "tilt_z": 0.00, "yaw": 0.00},
        {"y": 0.40,  "zc": 1.12, "w": 0.94, "h": 0.70, "type": "torso",     "tilt_z": 0.00, "yaw": 0.01},
        {"y": 0.78,  "zc": 1.06, "w": 0.88, "h": 0.62, "type": "torso",     "tilt_z": 0.00, "yaw": 0.02},
        {"y": 1.10,  "zc": 0.98, "w": 0.76, "h": 0.54, "type": "pelvis",    "tilt_z": 0.00, "yaw": 0.03},
        {"y": 1.38,  "zc": 0.92, "w": 0.56, "h": 0.44, "type": "tail_base", "tilt_z": 0.00, "yaw": 0.04},
        {"y": 1.66,  "zc": 0.90, "w": 0.46, "h": 0.32, "type": "tail_neck", "tilt_z": 0.01, "yaw": 0.06},
        {"y": 1.98,  "zc": 0.94, "w": 0.84, "h": 0.20, "type": "tail_paddle", "tilt_z": 0.03, "yaw": 0.09},
        {"y": 2.40,  "zc": 1.00, "w": 1.18, "h": 0.14, "type": "tail_paddle_max", "tilt_z": 0.06, "yaw": 0.12},
        {"y": 2.76,  "zc": 1.06, "w": 0.94, "h": 0.12, "type": "tail_paddle", "tilt_z": 0.08, "yaw": 0.14},
        {"y": 3.02,  "zc": 1.12, "w": 0.54, "h": 0.09, "type": "tail_tip",    "tilt_z": 0.10, "yaw": 0.15},
        {"y": 3.18,  "zc": 1.16, "w": 0.16, "h": 0.06, "type": "tail_tip",    "tilt_z": 0.11, "yaw": 0.16},
    ]

    angles_deg = [
        90,    # 0: Sống lưng
        68,    # 1: Gờ sọ trong phải
        50,    # 2: Sọc hoa văn sọ phải
        32,    # 3: Gờ chân mày phải
        10,    # 4: Mép môi trên phải (Mép cười)
        -15,   # 5: Mép hàm dưới phải
        -55,   # 6: Đáy hàm/cằm phải
        -90,   # 7: Đáy cằm & yếm họng
        -125,  # 8: Đáy hàm/cằm trái
        -165,  # 9: Mép hàm dưới trái
        170,   # 10: Mép môi trên trái (Mép cười)
        148,   # 11: Gờ chân mày trái
        130,   # 12: Sọc hoa văn sọ trái
        112,   # 13: Gờ sọ trong trái
    ]
    angles = [math.radians(a) for a in angles_deg]

    bm = bmesh.new()
    body_mesh = bpy.data.meshes.new("Genesis_Lizard_Body")
    body_obj = bpy.data.objects.new("Genesis_Lizard_Body", body_mesh)
    collection.objects.link(body_obj)
    body_obj.parent = arm_obj

    for mat in [mats["green"], mats["belly"], mats["light_green"], mats["dark_green"], mats["nostril"]]:
        body_obj.data.materials.append(mat)
    MAT_GREEN = 0
    MAT_BELLY = 1
    MAT_LIGHT_GREEN = 2
    MAT_DARK_GREEN = 3
    MAT_NOSTRIL = 4

    ring_verts = []
    for _r_idx, r in enumerate(rings_data):
        y = r["y"]
        zc = r["zc"] + r.get("tilt_z", 0.0)
        w = r["w"]
        h = r["h"]
        rtype = r["type"]
        yaw = r.get("yaw", 0.0)

        xc_offset = yaw * 1.8

        v_list = []
        for a_idx, ang in enumerate(angles):
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)

            vx = ox + xc_offset + cos_a * w
            vy = oy + y
            vz = oz + zc + sin_a * (h * 0.5)

            if rtype in ("snout", "head", "crown", "nape"):
                if a_idx in (1, 13):
                    vz += 0.080
                elif a_idx in (3, 11):
                    vz += 0.070
                    vx += (0.035 if a_idx == 3 else -0.035)
                elif a_idx in (2, 12):
                    vz -= 0.040
                elif a_idx == 0:
                    vz += 0.045

            # Rãnh mép môi cười (Mouth smile crease)
            if rtype in ("snout", "head"):
                if a_idx in (4, 10):
                    vx *= 1.03
                    vz += 0.015
                elif a_idx in (5, 9):
                    vx *= 0.98
                    vz -= 0.015

            # Yếm họng
            if rtype in ("head", "crown") and a_idx == 7:
                vz -= 0.06

            vert = bm.verts.new((vx, vy, vz))
            v_list.append(vert)
        ring_verts.append(v_list)

    bm.verts.ensure_lookup_table()

    # Nối mặt Quad sạch sẽ
    for i in range(len(rings_data) - 1):
        r1 = ring_verts[i]
        r2 = ring_verts[i + 1]
        rtype = rings_data[i]["type"]
        is_tail = "tail" in rtype

        for j in range(len(angles)):
            jn = (j + 1) % len(angles)
            v0 = r1[j]
            v1 = r1[jn]
            v2 = r2[jn]
            v3 = r2[j]

            try:
                face = bm.faces.new((v0, v1, v2, v3))
            except ValueError:
                continue

            if is_tail and j in (2, 3, 4, 5, 9, 10, 11, 12):
                face.material_index = MAT_BELLY
            elif j in (5, 6, 7, 8, 9):
                face.material_index = MAT_BELLY # Bụng & hàm dưới màu cát
            elif i == 1 and j in (1, 13):
                face.material_index = MAT_NOSTRIL # Lỗ mũi sinh học trên mõm
            elif rtype in ("snout", "head", "crown", "nape") and j in (1, 13):
                face.material_index = MAT_LIGHT_GREEN
            elif (rtype in ("snout", "head", "crown", "nape") and j in (2, 12)) or (rtype in ("snout", "head", "crown", "nape") and j == 0):
                face.material_index = MAT_DARK_GREEN
            else:
                face.material_index = MAT_GREEN

    # Nắp chóp mũi bằng 1 đỉnh tâm tròn vòm (Spherical cap at tip)
    snout_yaw = rings_data[0]["yaw"] * 1.8
    v_tip = bm.verts.new((ox + snout_yaw, oy - 1.58, oz + rings_data[0]["zc"] + rings_data[0]["tilt_z"]))
    r0 = ring_verts[0]
    for j in range(len(angles)):
        jn = (j + 1) % len(angles)
        try:
            f = bm.faces.new((v_tip, r0[j], r0[jn]))
            f.material_index = MAT_BELLY if j in (5, 6, 7, 8) else MAT_GREEN
        except ValueError:
            pass

    # Nắp chóp đuôi bằng 1 đỉnh tâm
    tail_yaw = rings_data[-1]["yaw"] * 1.8
    v_tail_tip = bm.verts.new((ox + tail_yaw, oy + 3.22, oz + rings_data[-1]["zc"] + rings_data[-1]["tilt_z"]))
    rend = ring_verts[-1]
    for j in range(len(angles)):
        jn = (j + 1) % len(angles)
        try:
            f = bm.faces.new((v_tail_tip, rend[jn], rend[j]))
            f.material_index = MAT_BELLY
        except ValueError:
            pass

    bm.to_mesh(body_mesh)
    bm.free()

    apply_organic_smoothing(body_obj, subsurf_levels=1)

    # Phân bổ trọng số Skinning giải phẫu cho Head và Jaw:
    body_groups = ["Head", "Jaw", "Neck", "Chest", "Spine_Mid", "Pelvis", "Tail_1", "Tail_2", "Tail_3", "Tail_4"]
    for bg in body_groups:
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
            fac = (vy - (-0.65)) / 0.30
            body_obj.vertex_groups["Head"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Neck"].add([v.index], fac, 'REPLACE')
        elif vy < 0.10:
            fac = (vy - (-0.35)) / 0.45
            body_obj.vertex_groups["Neck"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Chest"].add([v.index], fac, 'REPLACE')
        elif vy < 0.55:
            fac = (vy - 0.10) / 0.45
            body_obj.vertex_groups["Chest"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Spine_Mid"].add([v.index], fac, 'REPLACE')
        elif vy < 1.05:
            fac = (vy - 0.55) / 0.50
            body_obj.vertex_groups["Spine_Mid"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Pelvis"].add([v.index], fac, 'REPLACE')
        elif vy < 1.55:
            fac = (vy - 1.05) / 0.50
            body_obj.vertex_groups["Pelvis"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Tail_1"].add([v.index], fac, 'REPLACE')
        elif vy < 2.05:
            fac = (vy - 1.55) / 0.50
            body_obj.vertex_groups["Tail_1"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Tail_2"].add([v.index], fac, 'REPLACE')
        elif vy < 2.55:
            fac = (vy - 2.05) / 0.50
            body_obj.vertex_groups["Tail_2"].add([v.index], 1.0 - fac, 'REPLACE')
            body_obj.vertex_groups["Tail_3"].add([v.index], fac, 'REPLACE')
        else:
            body_obj.vertex_groups["Tail_4"].add([v.index], 1.0, 'REPLACE')

    arm_mod = body_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj

    # -------------------------------------------------------------
    # 2. ĐÔI MẮT HỔ PHÁCH SỐNG ĐỘNG
    # -------------------------------------------------------------
    eye_mesh = bpy.data.meshes.new("Genesis_Lizard_Eyes")
    eye_obj = bpy.data.objects.new("Genesis_Lizard_Eyes", eye_mesh)
    collection.objects.link(eye_obj)
    eye_obj.parent = arm_obj
    eye_obj.data.materials.append(mats["eye_iris"])       # 0
    eye_obj.data.materials.append(mats["eye_pupil"])      # 1
    eye_obj.data.materials.append(mats["eye_highlight"])  # 2
    eye_obj.data.materials.append(mats["belly"])          # 3

    bm_e = bmesh.new()
    for side in (1, -1):
        eye_center = Vector((ox + side * 0.65, oy - 0.96, oz + 1.25))
        forward = Vector((side * 0.58, -0.74, 0.16)).normalized()
        up = Vector((0, 0.16, 0.98)).normalized()
        right = forward.cross(up).normalized()

        eye_geom = bmesh.ops.create_icosphere(
            bm_e,
            subdivisions=2,
            radius=0.190,
            matrix=Matrix.Translation(eye_center)
        )
        eye_faces = list(set(f for v in eye_geom["verts"] for f in v.link_faces))

        for f in eye_faces:
            center_dir = (f.calc_center_bounds() - eye_center).normalized()
            dot_f = center_dir.dot(forward)

            if dot_f > 0.86 and abs(center_dir.dot(right)) < 0.20:
                f.material_index = 1
            elif dot_f > 0.72 and dot_f < 0.88 and center_dir.dot(up) > 0.42 and center_dir.dot(right) * side > 0:
                f.material_index = 2
            else:
                f.material_index = 0

        # Mí mắt dưới sinh học
        rim_b0 = bm_e.verts.new(eye_center + right * 0.21 - up * 0.12 - forward * 0.04)
        rim_b1 = bm_e.verts.new(eye_center + right * 0.06 - up * 0.22 + forward * 0.05)
        rim_b2 = bm_e.verts.new(eye_center - right * 0.18 - up * 0.17 + forward * 0.03)
        bm_e.verts.new(eye_center - right * 0.22 - up * 0.05 - forward * 0.05)

        rim_out0 = bm_e.verts.new(eye_center + right * 0.28 - up * 0.26 - forward * 0.10)
        rim_out1 = bm_e.verts.new(eye_center + right * 0.09 - up * 0.34 + forward * 0.02)
        rim_out2 = bm_e.verts.new(eye_center - right * 0.24 - up * 0.28 + forward * 0.0)

        try:
            f_rim0 = bm_e.faces.new((rim_b0, rim_b1, rim_out1, rim_out0))
            f_rim0.material_index = 3
        except ValueError:
            pass
        try:
            f_rim1 = bm_e.faces.new((rim_b1, rim_b2, rim_out2, rim_out1))
            f_rim1.material_index = 3
        except ValueError:
            pass

    bm_e.to_mesh(eye_mesh)
    bm_e.free()
    apply_organic_smoothing(eye_obj, subsurf_levels=1)

    eye_obj.vertex_groups.new(name="Head")
    for v in eye_mesh.vertices:
        eye_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
    eye_mod = eye_obj.modifiers.new("Armature", 'ARMATURE')
    eye_mod.object = arm_obj

    # -------------------------------------------------------------
    # 3. HÀNG GAI LƯNG SỪNG UỐN CONG & GAI SƯỜN
    # -------------------------------------------------------------
    spikes_info = [
        {"y": -0.42, "z": 1.48, "h": 0.32, "w": 0.088, "pitch": 12, "curve": 0.04},
        {"y": -0.22, "z": 1.50, "h": 0.42, "w": 0.102, "pitch": 15, "curve": 0.06},
        {"y": -0.02, "z": 1.52, "h": 0.52, "w": 0.122, "pitch": 18, "curve": 0.08},
        {"y": 0.18,  "z": 1.51, "h": 0.54, "w": 0.126, "pitch": 21, "curve": 0.08},
        {"y": 0.38,  "z": 1.48, "h": 0.50, "w": 0.118, "pitch": 24, "curve": 0.07},
        {"y": 0.58,  "z": 1.43, "h": 0.44, "w": 0.108, "pitch": 27, "curve": 0.06},
        {"y": 0.78,  "z": 1.36, "h": 0.38, "w": 0.096, "pitch": 30, "curve": 0.05},
        {"y": 0.95,  "z": 1.28, "h": 0.32, "w": 0.086, "pitch": 33, "curve": 0.04},
        {"y": 1.10,  "z": 1.20, "h": 0.27, "w": 0.076, "pitch": 35, "curve": 0.03},
        {"y": 1.24,  "z": 1.11, "h": 0.22, "w": 0.066, "pitch": 38, "curve": 0.03},
        {"y": 1.37,  "z": 1.02, "h": 0.17, "w": 0.056, "pitch": 40, "curve": 0.02},
        {"y": 1.48,  "z": 0.96, "h": 0.13, "w": 0.048, "pitch": 42, "curve": 0.02},
    ]

    spikes_mesh = bpy.data.meshes.new("Genesis_Lizard_Spikes")
    spikes_obj = bpy.data.objects.new("Genesis_Lizard_Spikes", spikes_mesh)
    collection.objects.link(spikes_obj)
    spikes_obj.parent = arm_obj
    spikes_obj.data.materials.append(mats["spike_base"])
    spikes_obj.data.materials.append(mats["spike_tip"])

    bm_s = bmesh.new()
    for s in spikes_info:
        sy = s["y"]
        sz = s["z"]
        sh = s["h"]
        sw = s["w"]
        pitch = math.radians(s["pitch"])
        curve = s["curve"]

        dir_vec = Vector((0, math.sin(pitch), math.cos(pitch)))
        side_vec = Vector((1, 0, 0))
        ortho_vec = Vector((0, math.cos(pitch), -math.sin(pitch)))

        p_base = Vector((ox, oy + sy, oz + sz - 0.03))
        b0 = bm_s.verts.new(p_base - side_vec * sw - ortho_vec * sw * 0.7)
        b1 = bm_s.verts.new(p_base + side_vec * sw - ortho_vec * sw * 0.7)
        b2 = bm_s.verts.new(p_base + side_vec * sw + ortho_vec * sw * 0.7)
        b3 = bm_s.verts.new(p_base - side_vec * sw + ortho_vec * sw * 0.7)

        p_mid = p_base + dir_vec * (sh * 0.44) + Vector((0, curve * 0.5, -curve * 0.2))
        mw = sw * 0.56
        m0 = bm_s.verts.new(p_mid - side_vec * mw - ortho_vec * mw * 0.7)
        m1 = bm_s.verts.new(p_mid + side_vec * mw - ortho_vec * mw * 0.7)
        m2 = bm_s.verts.new(p_mid + side_vec * mw + ortho_vec * mw * 0.7)
        m3 = bm_s.verts.new(p_mid - side_vec * mw + ortho_vec * mw * 0.7)

        p_tip = p_base + dir_vec * sh + Vector((0, curve, -curve * 0.5))
        tip = bm_s.verts.new(p_tip)

        f_b0 = bm_s.faces.new((b0, b1, m1, m0))
        f_b1 = bm_s.faces.new((b1, b2, m2, m1))
        f_b2 = bm_s.faces.new((b2, b3, m3, m2))
        f_b3 = bm_s.faces.new((b3, b0, m0, m3))
        for f in (f_b0, f_b1, f_b2, f_b3):
            f.material_index = 0

        f_t0 = bm_s.faces.new((m0, m1, tip))
        f_t1 = bm_s.faces.new((m1, m2, tip))
        f_t2 = bm_s.faces.new((m2, m3, tip))
        f_t3 = bm_s.faces.new((m3, m0, tip))
        for f in (f_t0, f_t1, f_t2, f_t3):
            f.material_index = 1

    # Gai sườn
    flank_spikes_data = [
        {"y": 0.12, "z": 1.07, "w_span": 0.92, "len": 0.25, "yaw": 28},
        {"y": 0.35, "z": 1.04, "w_span": 0.94, "len": 0.27, "yaw": 30},
        {"y": 0.58, "z": 0.99, "w_span": 0.90, "len": 0.24, "yaw": 32},
        {"y": 0.80, "z": 0.92, "w_span": 0.82, "len": 0.20, "yaw": 35},
    ]
    for fs in flank_spikes_data:
        fy = fs["y"]
        fz = fs["z"]
        wspan = fs["w_span"]
        flen = fs["len"]
        yaw = math.radians(fs["yaw"])

        for side in (1, -1):
            base_pt = Vector((ox + side * wspan, oy + fy, oz + fz))
            out_dir = Vector((side * math.cos(yaw), math.sin(yaw), -0.06)).normalized()
            tip_pt = base_pt + out_dir * flen

            b0 = bm_s.verts.new(base_pt + Vector((0, -0.07, 0.045)))
            b1 = bm_s.verts.new(base_pt + Vector((0, 0.07, 0.045)))
            b2 = bm_s.verts.new(base_pt + Vector((0, 0.0, -0.055)))
            t0 = bm_s.verts.new(tip_pt)

            f1 = bm_s.faces.new((b0, b1, t0))
            f2 = bm_s.faces.new((b1, b2, t0))
            f3 = bm_s.faces.new((b2, b0, t0))
            f4 = bm_s.faces.new((b0, b2, b1))
            for f in (f1, f2, f3, f4):
                f.material_index = 0

    bm_s.to_mesh(spikes_mesh)
    bm_s.free()
    apply_organic_smoothing(spikes_obj, subsurf_levels=1)

    for bg in ["Neck", "Chest", "Spine_Mid", "Pelvis", "Tail_1"]:
        spikes_obj.vertex_groups.new(name=bg)
    for v in spikes_mesh.vertices:
        vy = v.co.y - oy
        if vy < -0.30:
            spikes_obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
        elif vy < 0.25:
            spikes_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
        elif vy < 0.70:
            spikes_obj.vertex_groups["Spine_Mid"].add([v.index], 1.0, 'REPLACE')
        elif vy < 1.15:
            spikes_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')
        else:
            spikes_obj.vertex_groups["Tail_1"].add([v.index], 1.0, 'REPLACE')

    spikes_mod = spikes_obj.modifiers.new("Armature", 'ARMATURE')
    spikes_mod.object = arm_obj

    # -------------------------------------------------------------
    # 4. BỐN CHI CƠ BẮP & BÀN CHÂN 5 NGÓN MÀNG BƠI & MÓNG VUỐT 3D
    # -------------------------------------------------------------
    limbs_mesh = bpy.data.meshes.new("Genesis_Lizard_Limbs")
    limbs_obj = bpy.data.objects.new("Genesis_Lizard_Limbs", limbs_mesh)
    collection.objects.link(limbs_obj)
    limbs_obj.parent = arm_obj
    limbs_obj.data.materials.append(mats["green"])      # 0
    limbs_obj.data.materials.append(mats["belly"])      # 1
    limbs_obj.data.materials.append(mats["claw"])       # 2

    bm_l = bmesh.new()

    limbs_config = [
        # Chi trước trái
        {
            "name": "front_left",
            "side": 1,
            "shoulder": Vector((ox + 0.76, oy - 0.15, oz + 1.05)),
            "elbow": Vector((ox + 1.32, oy - 0.28, oz + 0.74)),
            "wrist": Vector((ox + 1.22, oy - 0.84, oz + 0.16)),
            "foot_center": Vector((ox + 1.26, oy - 1.04, oz + 0.0)),
            "is_front": True,
            "toe_heading": math.radians(-115),
            "bone_ua": "UpperArm.L",
            "bone_fa": "Forearm.L",
            "bone_ft": "Foot.L",
        },
        # Chi trước phải
        {
            "name": "front_right",
            "side": -1,
            "shoulder": Vector((ox - 0.76, oy - 0.15, oz + 1.05)),
            "elbow": Vector((ox - 1.32, oy - 0.28, oz + 0.74)),
            "wrist": Vector((ox - 1.22, oy - 0.84, oz + 0.16)),
            "foot_center": Vector((ox - 1.26, oy - 1.04, oz + 0.0)),
            "is_front": True,
            "toe_heading": math.radians(-65),
            "bone_ua": "UpperArm.R",
            "bone_fa": "Forearm.R",
            "bone_ft": "Foot.R",
        },
        # Chi sau trái
        {
            "name": "hind_left",
            "side": 1,
            "shoulder": Vector((ox + 0.72, oy + 0.92, oz + 0.90)),
            "elbow": Vector((ox + 1.40, oy + 1.16, oz + 0.60)),
            "wrist": Vector((ox + 1.24, oy + 0.80, oz + 0.16)),
            "foot_center": Vector((ox + 1.30, oy + 0.66, oz + 0.0)),
            "is_front": False,
            "toe_heading": math.radians(-85),
            "bone_ua": "Thigh.L",
            "bone_fa": "Shin.L",
            "bone_ft": "Foot.L.Hind",
        },
        # Chi sau phải
        {
            "name": "hind_right",
            "side": -1,
            "shoulder": Vector((ox - 0.72, oy + 0.92, oz + 0.90)),
            "elbow": Vector((ox - 1.40, oy + 1.16, oz + 0.60)),
            "wrist": Vector((ox - 1.24, oy + 0.80, oz + 0.16)),
            "foot_center": Vector((ox - 1.30, oy + 0.66, oz + 0.0)),
            "is_front": False,
            "toe_heading": math.radians(-95),
            "bone_ua": "Thigh.R",
            "bone_fa": "Shin.R",
            "bone_ft": "Foot.R.Hind",
        },
    ]

    limb_vgroups = {}
    for l_cfg in limbs_config:
        for bname in [l_cfg["bone_ua"], l_cfg["bone_fa"], l_cfg["bone_ft"]]:
            if bname not in limb_vgroups:
                limb_vgroups[bname] = limbs_obj.vertex_groups.new(name=bname)

    def build_organic_leg(limb):
        sh = limb["shoulder"]
        el = limb["elbow"]
        wr = limb["wrist"]
        fc = limb["foot_center"]
        side_sign = limb["side"]
        heading = limb["toe_heading"]

        arm_sections = [
            {"pt": sh, "r": 0.24, "dir": (el - sh).normalized(), "part": "ua"},
            {"pt": sh * 0.45 + el * 0.55, "r": 0.20, "dir": (el - sh).normalized(), "part": "ua"},
            {"pt": el, "r": 0.17, "dir": (wr - el).normalized(), "part": "fa"},
            {"pt": el * 0.45 + wr * 0.55, "r": 0.15, "dir": (wr - el).normalized(), "part": "fa"},
            {"pt": wr, "r": 0.14, "dir": Vector((0, 0, -1)), "part": "fa"},
        ]

        toe_dir = Vector((math.cos(heading), math.sin(heading), 0)).normalized()
        up_global = Vector((0, 0, 1))
        side_foot = toe_dir.cross(up_global).normalized()

        sec_verts = []
        for s_idx, s in enumerate(arm_sections):
            axis = s["dir"]
            if s_idx == len(arm_sections) - 1:
                side_v = side_foot
                up_v = toe_dir
            else:
                up_temp = Vector((0, 0, 1)) if abs(axis.z) < 0.85 else Vector((0, 1, 0))
                side_v = axis.cross(up_temp).normalized()
                up_v = side_v.cross(axis).normalized()

            v_ring = []
            for k in range(6):
                ang = 2 * math.pi * k / 6
                rad_vec = side_v * math.cos(ang) + up_v * math.sin(ang)
                v = bm_l.verts.new(s["pt"] + rad_vec * s["r"])
                v_ring.append(v)
            sec_verts.append(v_ring)

        for i in range(len(arm_sections) - 1):
            s1 = sec_verts[i]
            s2 = sec_verts[i + 1]
            for k in range(6):
                kn = (k + 1) % 6
                try:
                    f = bm_l.faces.new((s1[k], s1[kn], s2[kn], s2[k]))
                    f.material_index = 1 if math.sin(2 * math.pi * k / 6) < -0.2 else 0
                except ValueError:
                    pass

        wrist_ring = sec_verts[-1]
        heel_pt = wr - toe_dir * 0.12 + Vector((0, 0, -0.15))
        v_heel = bm_l.verts.new(heel_pt)

        toe_angles = [-0.65, -0.32, 0.0, 0.32, 0.65]
        toe_lengths = [0.38, 0.52, 0.56, 0.48, 0.36]

        toe_top_bases = []
        toe_bot_bases = []
        toe_top_tips = []
        toe_bot_tips = []
        claw_tips = []

        for _tidx, (rel_ang, tlen) in enumerate(zip(toe_angles, toe_lengths)):
            ang = heading + rel_ang * side_sign
            dir_toe = Vector((math.cos(ang), math.sin(ang), 0.0)).normalized()

            p_tb_top = fc + dir_toe * (tlen * 0.30) + Vector((0, 0, 0.07))
            p_tb_bot = fc + dir_toe * (tlen * 0.30) + Vector((0, 0, 0.005))
            p_tt_top = fc + dir_toe * (tlen * 0.82) + Vector((0, 0, 0.045))
            p_tt_bot = fc + dir_toe * (tlen * 0.82) + Vector((0, 0, 0.003))
            p_claw = fc + dir_toe * (tlen * 1.16) + Vector((0, 0, -0.005))

            v_tb_top = bm_l.verts.new(p_tb_top)
            v_tb_bot = bm_l.verts.new(p_tb_bot)
            v_tt_top = bm_l.verts.new(p_tt_top)
            v_tt_bot = bm_l.verts.new(p_tt_bot)
            v_claw = bm_l.verts.new(p_claw)

            toe_top_bases.append(v_tb_top)
            toe_bot_bases.append(v_tb_bot)
            toe_top_tips.append(v_tt_top)
            toe_bot_tips.append(v_tt_bot)
            claw_tips.append(v_claw)

        # Mu chân
        for i in range(len(toe_top_bases) - 1):
            w_v1 = wrist_ring[i % 6]
            w_v2 = wrist_ring[(i + 1) % 6]
            try:
                f_top = bm_l.faces.new((w_v1, w_v2, toe_top_bases[i + 1], toe_top_bases[i]))
                f_top.material_index = 0
            except ValueError:
                pass

        # Đáy chân
        for i in range(len(toe_bot_bases) - 1):
            try:
                f_bot = bm_l.faces.new((v_heel, toe_bot_bases[i], toe_bot_bases[i + 1]))
                f_bot.material_index = 1
            except ValueError:
                pass

        # Gót chân
        try:
            f_h1 = bm_l.faces.new((wrist_ring[4], wrist_ring[5], v_heel))
            f_h1.material_index = 1
            f_h2 = bm_l.faces.new((wrist_ring[5], wrist_ring[0], v_heel))
            f_h2.material_index = 1
        except ValueError:
            pass

        # Màng bơi sinh thái lõm cong
        for i in range(len(toe_top_tips) - 1):
            mid_web_top = (toe_top_bases[i].co + toe_top_bases[i+1].co + toe_top_tips[i].co + toe_top_tips[i+1].co) * 0.25 - dir_toe * 0.04 + Vector((0, 0, 0.015))
            mid_web_bot = mid_web_top + Vector((0, 0, -0.012))
            v_mw_top = bm_l.verts.new(mid_web_top)
            v_mw_bot = bm_l.verts.new(mid_web_bot)

            try:
                f_w1 = bm_l.faces.new((toe_top_bases[i], toe_top_tips[i], v_mw_top))
                f_w2 = bm_l.faces.new((v_mw_top, toe_top_tips[i+1], toe_top_bases[i+1]))
                f_w3 = bm_l.faces.new((toe_top_bases[i], v_mw_top, toe_top_bases[i+1]))
                for fw in (f_w1, f_w2, f_w3):
                    fw.material_index = 0
            except ValueError:
                pass

            try:
                f_wb1 = bm_l.faces.new((toe_bot_bases[i], v_mw_bot, toe_bot_tips[i]))
                f_wb2 = bm_l.faces.new((v_mw_bot, toe_bot_bases[i+1], toe_bot_tips[i+1]))
                f_wb3 = bm_l.faces.new((toe_bot_bases[i], toe_bot_bases[i+1], v_mw_bot))
                for fwb in (f_wb1, f_wb2, f_wb3):
                    fwb.material_index = 1
            except ValueError:
                pass

        # Thân ngón & MÓNG VUỐT 3D CHẤT SỪNG
        for i in range(len(toe_top_tips)):
            t_top = toe_top_tips[i]
            t_bot = toe_bot_tips[i]
            b_top = toe_top_bases[i]
            b_bot = toe_bot_bases[i]
            c_tip = claw_tips[i]

            try:
                f_digit = bm_l.faces.new((b_top, t_top, t_bot, b_bot))
                f_digit.material_index = 0
            except ValueError:
                pass

            ang = heading + toe_angles[i] * side_sign
            ang_perp = ang + math.pi / 2
            perp_toe = Vector((math.cos(ang_perp), math.sin(ang_perp), 0.0)).normalized() * 0.048

            c_l = bm_l.verts.new(t_bot.co - perp_toe + Vector((0, 0, 0.015)))
            c_r = bm_l.verts.new(t_bot.co + perp_toe + Vector((0, 0, 0.015)))

            try:
                f_c1 = bm_l.faces.new((t_top, c_l, c_tip))
                f_c2 = bm_l.faces.new((t_top, c_tip, c_r))
                f_c3 = bm_l.faces.new((t_bot, c_r, c_tip))
                f_c4 = bm_l.faces.new((t_bot, c_tip, c_l))
                for cf in (f_c1, f_c2, f_c3, f_c4):
                    cf.material_index = 2
            except ValueError:
                pass

    for limb in limbs_config:
        build_organic_leg(limb)

    bm_l.to_mesh(limbs_mesh)
    bm_l.free()
    apply_organic_smoothing(limbs_obj, subsurf_levels=1)

    for v in limbs_mesh.vertices:
        vx = v.co.x - ox
        vy = v.co.y - oy
        vz = v.co.z - oz

        side = ".L" if vx > 0 else ".R"
        is_front = vy < 0.20

        if is_front:
            ua_name = f"UpperArm{side}"
            fa_name = f"Forearm{side}"
            ft_name = f"Foot{side}"
            if vz > 0.65:
                limbs_obj.vertex_groups[ua_name].add([v.index], 1.0, 'REPLACE')
            elif vz > 0.22:
                fac = (vz - 0.22) / 0.43
                limbs_obj.vertex_groups[ua_name].add([v.index], fac, 'REPLACE')
                limbs_obj.vertex_groups[fa_name].add([v.index], 1.0 - fac, 'REPLACE')
            else:
                limbs_obj.vertex_groups[ft_name].add([v.index], 1.0, 'REPLACE')
        else:
            th_name = f"Thigh{side}"
            sh_name = f"Shin{side}"
            ft_name = f"Foot{side}.Hind"
            if vz > 0.55:
                limbs_obj.vertex_groups[th_name].add([v.index], 1.0, 'REPLACE')
            elif vz > 0.20:
                fac = (vz - 0.20) / 0.35
                limbs_obj.vertex_groups[th_name].add([v.index], fac, 'REPLACE')
                limbs_obj.vertex_groups[sh_name].add([v.index], 1.0 - fac, 'REPLACE')
            else:
                limbs_obj.vertex_groups[ft_name].add([v.index], 1.0, 'REPLACE')

    limbs_mod = limbs_obj.modifiers.new("Armature", 'ARMATURE')
    limbs_mod.object = arm_obj

    print("All organic meshes constructed and bound to armature!")
    return arm_obj

# -----------------------------------------------------------------
# 5. TẠO CÁC ANIMATION (Idle & Walk Animations)
# -----------------------------------------------------------------
def create_animations(arm_obj):
    arm_obj.animation_data_create()

    # ANIMATION 1: Lizard_Idle
    act_idle = bpy.data.actions.new("Lizard_Idle")
    arm_obj.animation_data.action = act_idle

    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="scale", frame=1)

    # Frame 25: Hít thở vào (lồng ngực nở, đầu hơi ngước, mồm hé thở)
    pb_chest = arm_obj.pose.bones["Chest"]
    pb_chest.scale = (1.04, 1.02, 1.05)
    pb_chest.keyframe_insert(data_path="scale", frame=25)

    pb_head = arm_obj.pose.bones["Head"]
    pb_head.rotation_euler = (math.radians(5), math.radians(2), math.radians(-6))
    pb_head.keyframe_insert(data_path="rotation_euler", frame=25)

    pb_jaw = arm_obj.pose.bones["Jaw"]
    pb_jaw.rotation_euler = (math.radians(7), 0, 0) # Miệng hé mở sinh học khi hít thở
    pb_jaw.keyframe_insert(data_path="rotation_euler", frame=25)

    # Frame 18: Đuôi uốn sóng sang trái
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(4))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(9))
    arm_obj.pose.bones["Tail_3"].rotation_euler = (0, 0, math.radians(16))
    arm_obj.pose.bones["Tail_4"].rotation_euler = (0, 0, math.radians(24))
    for tname in ["Tail_1", "Tail_2", "Tail_3", "Tail_4"]:
        arm_obj.pose.bones[tname].keyframe_insert(data_path="rotation_euler", frame=18)

    # Frame 42: Đuôi uốn sóng sang phải, thở ra
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(-4))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(-9))
    arm_obj.pose.bones["Tail_3"].rotation_euler = (0, 0, math.radians(-16))
    arm_obj.pose.bones["Tail_4"].rotation_euler = (0, 0, math.radians(-24))
    for tname in ["Tail_1", "Tail_2", "Tail_3", "Tail_4"]:
        arm_obj.pose.bones[tname].keyframe_insert(data_path="rotation_euler", frame=42)

    pb_chest.scale = (0.98, 0.99, 0.97)
    pb_chest.keyframe_insert(data_path="scale", frame=45)
    pb_head.rotation_euler = (math.radians(-2), math.radians(-1), math.radians(4))
    pb_head.keyframe_insert(data_path="rotation_euler", frame=45)
    pb_jaw.rotation_euler = (0, 0, 0)
    pb_jaw.keyframe_insert(data_path="rotation_euler", frame=45)

    # Frame 60: Hoàn tất vòng lặp kín
    for pb in arm_obj.pose.bones:
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)
        pb.keyframe_insert(data_path="rotation_euler", frame=60)
        pb.keyframe_insert(data_path="scale", frame=60)

    # ANIMATION 2: Lizard_Walk
    act_walk = bpy.data.actions.new("Lizard_Walk")
    arm_obj.animation_data.action = act_walk

    arm_obj.pose.bones["Spine_Mid"].rotation_euler = (0, 0, math.radians(-6))
    arm_obj.pose.bones["Chest"].rotation_euler = (0, 0, math.radians(6))
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(-15), math.radians(10), math.radians(20))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(15), math.radians(-10), math.radians(-15))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(-15), math.radians(-10), math.radians(20))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(15), math.radians(10), math.radians(-15))
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(-10))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(-16))

    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)

    arm_obj.pose.bones["Spine_Mid"].rotation_euler = (0, 0, math.radians(6))
    arm_obj.pose.bones["Chest"].rotation_euler = (0, 0, math.radians(-6))
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(15), math.radians(-10), math.radians(-15))
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(-15), math.radians(10), math.radians(20))
    arm_obj.pose.bones["Thigh.R"].rotation_euler = (math.radians(15), math.radians(10), math.radians(-15))
    arm_obj.pose.bones["Thigh.L"].rotation_euler = (math.radians(-15), math.radians(-10), math.radians(20))
    arm_obj.pose.bones["Tail_1"].rotation_euler = (0, 0, math.radians(10))
    arm_obj.pose.bones["Tail_2"].rotation_euler = (0, 0, math.radians(16))

    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=20)

    # Đặt active animation là Lizard_Idle ở frame 1 để chụp pose tự nhiên mỉm cười
    arm_obj.animation_data.action = act_idle
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60
    bpy.context.scene.frame_current = 1

    print("Created animations: Lizard_Idle and Lizard_Walk successfully!")

# -----------------------------------------------------------------
# THỰC THI CHÍNH
# -----------------------------------------------------------------
col = clear_collection("Genesis_Lizard")
mats = setup_materials()

spider_arm = bpy.data.objects.get("Spider_Armature")
ground = bpy.data.objects.get("Natural_Ground")
if spider_arm:
    spider_arm.location.x = -12.0
if ground:
    ground.location.x = -12.0

lizard_ground = bpy.data.objects.get("Lizard_Ground")
if not lizard_ground:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=3.4,
        depth=0.2,
        location=(3.2, 0, -0.1)
    )
    lizard_ground = bpy.context.active_object
    lizard_ground.name = "Lizard_Ground"
    mat_studio = get_or_create_material("Studio_Ground", (0.94, 0.94, 0.94, 1.0), roughness=0.9)
    lizard_ground.data.materials.append(mat_studio)
    col.objects.link(lizard_ground)
    if lizard_ground.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(lizard_ground)
else:
    lizard_ground.location = Vector((3.2, 0, -0.1))

# 1. Dựng Rig Armature
arm_obj = build_lizard_armature(col, offset=(3.2, 0, 0.0))

# 2. Dựng mô hình sinh học tròn trịa mượt mà và bind vào Rig
create_organic_lizard(col, mats, arm_obj, offset=(3.2, 0, 0.0))

# 3. Tạo các Animation
create_animations(arm_obj)

# 4. Ánh sáng studio mềm mại tự nhiên
def setup_lizard_lights(col):
    lights_data = [
        {"name": "Lizard_Key_Light", "type": 'POINT', "energy": 480, "color": (1.0, 0.98, 0.95), "loc": (3.2 + 2.5, -3.2, 3.4)},
        {"name": "Lizard_Fill_Light", "type": 'POINT', "energy": 220, "color": (0.90, 0.95, 1.0), "loc": (3.2 - 2.8, -2.4, 2.4)},
        {"name": "Lizard_Rim_Light", "type": 'POINT', "energy": 420, "color": (1.0, 0.92, 0.82), "loc": (3.2 + 0.8, 3.8, 3.2)},
        {"name": "Lizard_Top_Light", "type": 'POINT', "energy": 190, "color": (0.98, 1.0, 0.98), "loc": (3.2, 0.0, 4.2)},
    ]
    for ld in lights_data:
        light_obj = bpy.data.objects.get(ld["name"])
        if not light_obj:
            ldata = bpy.data.lights.new(name=ld["name"], type=ld["type"])
            light_obj = bpy.data.objects.new(name=ld["name"], object_data=ldata)
            col.objects.link(light_obj)
        light_obj.data.energy = ld["energy"]
        light_obj.data.color = ld["color"]
        light_obj.location = Vector(ld["loc"])

setup_lizard_lights(col)

# 5. Camera chính góc 3/4
cam_lizard = bpy.data.objects.get("Camera_Lizard")
if not cam_lizard:
    cam_data = bpy.data.cameras.new("Camera_Lizard")
    cam_lizard = bpy.data.objects.new("Camera_Lizard", cam_data)
    bpy.context.scene.collection.objects.link(cam_lizard)

cam_lizard.location = Vector((3.2 + 2.4, -3.4, 1.85))
cam_lizard.rotation_euler = Euler((math.radians(68), 0, math.radians(35)), 'XYZ')
cam_lizard.data.lens = 55

bpy.context.scene.camera = cam_lizard

for window in bpy.context.window_manager.windows:
    screen = window.screen
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.region_3d.view_perspective = 'CAMERA'

# 6. Xuất GLB (kèm rig + animation) và lưu blend
out_dir = "/Users/duongnad/Documents/project/Genesis_Zero/assets"
os.makedirs(out_dir, exist_ok=True)
glb_path = os.path.join(out_dir, "genesis_lizard.glb")

bpy.ops.object.select_all(action='DESELECT')
for obj in col.objects:
    if obj.name != "Lizard_Ground":
        obj.select_set(True)

try:
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        use_selection=True,
        export_format='GLB',
        export_animations=True,
        export_skins=True
    )
    print(f"Exported rigged & animated GLB to {glb_path}")
except Exception as e:
    print(f"GLTF export warning: {e}")

try:
    bpy.ops.wm.save_mainfile()
    bpy.ops.wm.save_as_mainfile(filepath="/Users/duongnad/Documents/project/Genesis_Zero/assets/genesis_lizard.blend", copy=True)
    print("Blender projects saved.")
except Exception as e:
    print(f"Save blend warning: {e}")

print("Organic Rigged & Animated Lizard Model Finished!")

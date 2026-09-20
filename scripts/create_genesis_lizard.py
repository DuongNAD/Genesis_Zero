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

def get_or_create_material(name, color, roughness=0.55, specular=0.35):
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
        # Màu da lưng celadon tự nhiên
        "green": get_or_create_material("Lizard_Green", (0.39, 0.58, 0.53, 1.0), roughness=0.52, specular=0.35),
        # Màu xanh ngọc sáng cho gờ sọ và sống lưng
        "light_green": get_or_create_material("Lizard_LightGreen", (0.52, 0.70, 0.64, 1.0), roughness=0.50, specular=0.38),
        # Màu xanh đậm cho sọc hoa văn sọ rõ nét tự nhiên
        "dark_green": get_or_create_material("Lizard_DarkGreen", (0.18, 0.32, 0.28, 1.0), roughness=0.56, specular=0.30),
        # Màu vàng cát ấm bụng, hàm dưới, viền đuôi
        "belly": get_or_create_material("Lizard_Belly", (0.80, 0.72, 0.56, 1.0), roughness=0.58, specular=0.32),
        # Gai sừng 2 màu: chóp nâu đen đậm, gốc vàng cát
        "spike_tip": get_or_create_material("Lizard_Spike_Tip", (0.15, 0.09, 0.07, 1.0), roughness=0.40, specular=0.45),
        "spike_base": get_or_create_material("Lizard_Spike_Base", (0.78, 0.68, 0.52, 1.0), roughness=0.55, specular=0.35),
        # Mắt: Tròng vàng hổ phách sáng, đồng tử đen, đốm trắng giác mạc
        "eye_iris": get_or_create_material("Lizard_Eye_Iris", (0.96, 0.70, 0.12, 1.0), roughness=0.10, specular=1.0),
        "eye_pupil": get_or_create_material("Lizard_Eye_Pupil", (0.02, 0.02, 0.02, 1.0), roughness=0.08, specular=0.8),
        "eye_highlight": get_or_create_material("Lizard_Eye_Highlight", (1.0, 1.0, 0.98, 1.0), roughness=0.02, specular=1.0),
        # Móng vuốt ngà cát
        "claw": get_or_create_material("Lizard_Claw", (0.86, 0.78, 0.62, 1.0), roughness=0.38, specular=0.45),
    }

def create_creature(collection, mats, offset=(0, 0, 0)):
    ox, oy, oz = offset

    root = bpy.data.objects.new("Genesis_Lizard_Root", None)
    root.empty_display_type = 'ARROWS'
    root.empty_display_size = 0.5
    root.location = Vector((ox, oy, oz))
    collection.objects.link(root)

    # -------------------------------------------------------------
    # 1. THÂN, ĐẦU SINH HỌC & ĐUÔI MÁI CHÈO
    # -------------------------------------------------------------
    rings_data = [
        {"y": -1.40, "zc": 0.92, "w": 0.40, "h": 0.28, "type": "snout_tip", "tilt_z": 0.04, "yaw": -0.06},
        {"y": -1.22, "zc": 1.02, "w": 0.58, "h": 0.44, "type": "snout",     "tilt_z": 0.03, "yaw": -0.05},
        {"y": -0.98, "zc": 1.12, "w": 0.74, "h": 0.58, "type": "head",      "tilt_z": 0.02, "yaw": -0.04},
        {"y": -0.72, "zc": 1.22, "w": 0.78, "h": 0.70, "type": "crown",     "tilt_z": 0.01, "yaw": -0.02},
        {"y": -0.46, "zc": 1.18, "w": 0.76, "h": 0.68, "type": "nape",      "tilt_z": 0.00, "yaw": 0.00},
        {"y": -0.22, "zc": 1.16, "w": 0.80, "h": 0.68, "type": "neck",      "tilt_z": 0.00, "yaw": 0.00},
        {"y": 0.02,  "zc": 1.17, "w": 0.90, "h": 0.72, "type": "chest",     "tilt_z": 0.00, "yaw": 0.00},
        {"y": 0.38,  "zc": 1.12, "w": 0.92, "h": 0.68, "type": "torso",     "tilt_z": 0.00, "yaw": 0.01},
        {"y": 0.78,  "zc": 1.06, "w": 0.86, "h": 0.60, "type": "torso",     "tilt_z": 0.00, "yaw": 0.02},
        {"y": 1.10,  "zc": 0.98, "w": 0.74, "h": 0.52, "type": "pelvis",    "tilt_z": 0.00, "yaw": 0.03},
        {"y": 1.38,  "zc": 0.92, "w": 0.54, "h": 0.42, "type": "tail_base", "tilt_z": 0.00, "yaw": 0.04},
        {"y": 1.66,  "zc": 0.90, "w": 0.44, "h": 0.30, "type": "tail_neck", "tilt_z": 0.01, "yaw": 0.06},
        {"y": 1.98,  "zc": 0.94, "w": 0.80, "h": 0.20, "type": "tail_paddle", "tilt_z": 0.03, "yaw": 0.09},
        {"y": 2.40,  "zc": 1.00, "w": 1.14, "h": 0.14, "type": "tail_paddle_max", "tilt_z": 0.06, "yaw": 0.12},
        {"y": 2.76,  "zc": 1.06, "w": 0.90, "h": 0.12, "type": "tail_paddle", "tilt_z": 0.08, "yaw": 0.14},
        {"y": 3.02,  "zc": 1.12, "w": 0.50, "h": 0.09, "type": "tail_tip",    "tilt_z": 0.10, "yaw": 0.15},
        {"y": 3.18,  "zc": 1.16, "w": 0.15, "h": 0.06, "type": "tail_tip",    "tilt_z": 0.11, "yaw": 0.16},
    ]

    angles_deg = [
        90,    # 0: Sống lưng
        68,    # 1: Gờ sọ trong phải
        50,    # 2: Sọc tối sọ phải
        32,    # 3: Gờ chân mày phải
        12,    # 4: Mép má/hàm phải
        -25,   # 5: Sườn phải
        -60,   # 6: Mép bụng phải
        -90,   # 7: Đáy bụng (yếm cổ họng)
        -120,  # 8: Mép bụng trái
        -155,  # 9: Sườn trái
        168,   # 10: Mép má/hàm trái
        148,   # 11: Gờ chân mày trái
        130,   # 12: Sọc tối sọ trái
        112,   # 13: Gờ sọ trong trái
    ]
    angles = [math.radians(a) for a in angles_deg]

    bm = bmesh.new()
    body_mesh = bpy.data.meshes.new("Genesis_Lizard_Body")
    body_obj = bpy.data.objects.new("Genesis_Lizard_Body", body_mesh)
    collection.objects.link(body_obj)
    body_obj.parent = root

    for mat in [mats["green"], mats["belly"], mats["light_green"], mats["dark_green"]]:
        body_obj.data.materials.append(mat)
    MAT_GREEN = 0
    MAT_BELLY = 1
    MAT_LIGHT_GREEN = 2
    MAT_DARK_GREEN = 3

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

            vx = xc_offset + cos_a * w
            vz = zc + sin_a * (h * 0.5)

            # Cấu trúc sọ tự nhiên: gờ sống và rãnh hoa văn
            if rtype in ("snout", "head", "crown", "nape"):
                if a_idx in (1, 13):
                    vz += 0.090  # Gờ sống nổi
                elif a_idx in (3, 11):
                    vz += 0.080  # Gờ chân mày
                    vx += (0.04 if a_idx == 3 else -0.04)
                elif a_idx in (2, 12):
                    vz -= 0.050  # Rãnh sọ sâu tạo sọc hoa văn
                elif a_idx == 0:
                    vz += 0.050

            # Mép miệng cười sinh học
            if rtype in ("snout_tip", "snout", "head") and a_idx in (4, 10):
                vz -= 0.045
                vx *= 1.03

            # Yếm cổ họng
            if rtype == "head" and a_idx == 7:
                vz -= 0.06

            vert = bm.verts.new((vx, y, vz))
            v_list.append(vert)
        ring_verts.append(v_list)

    bm.verts.ensure_lookup_table()

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

            # Phân bố màu sắc sinh học
            if is_tail and j in (2, 3, 4, 5, 9, 10, 11, 12):
                face.material_index = MAT_BELLY  # Viền đuôi mái chèo màu cát
            elif j in (4, 5, 6, 7, 8, 9):
                face.material_index = MAT_BELLY  # Bụng & hàm dưới màu cát
            elif rtype in ("snout", "head", "crown", "nape") and j in (1, 13):
                face.material_index = MAT_LIGHT_GREEN # Gờ sọ sáng
            elif rtype in ("snout", "head", "crown", "nape") and j in (2, 12):
                face.material_index = MAT_DARK_GREEN  # Sọc sọ tối rõ nét
            elif rtype in ("snout", "head", "crown", "nape") and j == 0:
                face.material_index = MAT_DARK_GREEN
            else:
                face.material_index = MAT_GREEN

    # Nắp mõm trước: 2 lỗ mũi tự nhiên
    snout_verts = ring_verts[0]
    cap_lines = [
        (snout_verts[0], snout_verts[1], snout_verts[13]),
        (snout_verts[1], snout_verts[2], snout_verts[12], snout_verts[13]),
        (snout_verts[2], snout_verts[3], snout_verts[11], snout_verts[12]),
        (snout_verts[3], snout_verts[4], snout_verts[10], snout_verts[11]),
        (snout_verts[4], snout_verts[5], snout_verts[9], snout_verts[10]),
        (snout_verts[5], snout_verts[6], snout_verts[8], snout_verts[9]),
        (snout_verts[6], snout_verts[7], snout_verts[8]),
    ]
    for cf in cap_lines:
        try:
            f = bm.faces.new(cf)
            if cf[0] in (snout_verts[4], snout_verts[5], snout_verts[6]):
                f.material_index = MAT_BELLY
            elif cf[0] in (snout_verts[1], snout_verts[2]):
                f.material_index = MAT_DARK_GREEN # Lỗ mũi sinh học
            else:
                f.material_index = MAT_GREEN
        except ValueError:
            pass

    # Nắp chóp đuôi sau
    tail_verts = ring_verts[-1]
    tail_cap_lines = [
        (tail_verts[13], tail_verts[12], tail_verts[1], tail_verts[0]),
        (tail_verts[12], tail_verts[11], tail_verts[2], tail_verts[1]),
        (tail_verts[11], tail_verts[10], tail_verts[3], tail_verts[2]),
        (tail_verts[10], tail_verts[9], tail_verts[4], tail_verts[3]),
        (tail_verts[9], tail_verts[8], tail_verts[5], tail_verts[4]),
        (tail_verts[8], tail_verts[7], tail_verts[6], tail_verts[5]),
    ]
    for tf in tail_cap_lines:
        try:
            f = bm.faces.new(tf)
            f.material_index = MAT_BELLY
        except ValueError:
            pass

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(body_mesh)
    bm.free()

    for poly in body_mesh.polygons:
        poly.use_smooth = False
    body_mesh.update()

    # -------------------------------------------------------------
    # 2. HÀNG GAI LƯNG SỪNG UỐN CONG TỰ NHIÊN (12 Horn Spines)
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
    spikes_obj.parent = root
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

        p_base = Vector((0, sy, sz - 0.03))
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

    bmesh.ops.triangulate(bm_s, faces=bm_s.faces[:])
    bm_s.to_mesh(spikes_mesh)
    bm_s.free()
    for p in spikes_mesh.polygons:
        p.use_smooth = False
    spikes_mesh.update()

    # -------------------------------------------------------------
    # 3. GAI MẠNG SƯỜN TỰ NHIÊN
    # -------------------------------------------------------------
    flank_mesh = bpy.data.meshes.new("Genesis_Lizard_FlankSpikes")
    flank_obj = bpy.data.objects.new("Genesis_Lizard_FlankSpikes", flank_mesh)
    collection.objects.link(flank_obj)
    flank_obj.parent = root
    flank_obj.data.materials.append(mats["spike_base"])

    bm_f = bmesh.new()
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
            base_pt = Vector((side * wspan, fy, fz))
            out_dir = Vector((side * math.cos(yaw), math.sin(yaw), -0.06)).normalized()
            tip_pt = base_pt + out_dir * flen

            b0 = bm_f.verts.new(base_pt + Vector((0, -0.07, 0.045)))
            b1 = bm_f.verts.new(base_pt + Vector((0, 0.07, 0.045)))
            b2 = bm_f.verts.new(base_pt + Vector((0, 0.0, -0.055)))
            t0 = bm_f.verts.new(tip_pt)

            bm_f.faces.new((b0, b1, t0))
            bm_f.faces.new((b1, b2, t0))
            bm_f.faces.new((b2, b0, t0))
            bm_f.faces.new((b0, b2, b1))

    bm_f.to_mesh(flank_mesh)
    bm_f.free()
    for p in flank_mesh.polygons:
        p.use_smooth = False
    flank_mesh.update()

    # -------------------------------------------------------------
    # 4. MẮT HỔ PHÁCH SỐNG ĐỘNG
    # -------------------------------------------------------------
    eye_mesh = bpy.data.meshes.new("Genesis_Lizard_Eyes")
    eye_obj = bpy.data.objects.new("Genesis_Lizard_Eyes", eye_mesh)
    collection.objects.link(eye_obj)
    eye_obj.parent = root
    eye_obj.data.materials.append(mats["eye_iris"])       # 0: Vàng hổ phách
    eye_obj.data.materials.append(mats["eye_pupil"])      # 1: Đồng tử đen
    eye_obj.data.materials.append(mats["eye_highlight"])  # 2: Đốm trắng
    eye_obj.data.materials.append(mats["belly"])          # 3: Mí mắt dưới màu cát

    bm_e = bmesh.new()
    for side in (1, -1):
        eye_center = Vector((side * 0.65, -0.96, 1.25))
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

        # Mảng da mí mắt dưới màu cát nối từ má lên
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
    for p in eye_mesh.polygons:
        p.use_smooth = False
    eye_mesh.update()

    # -------------------------------------------------------------
    # 5. BỐN CHI CƠ BẮP & BÀN CHÂN MÀNG BƠI UỐN CONG TỰ NHIÊN
    # -------------------------------------------------------------
    limbs_mesh = bpy.data.meshes.new("Genesis_Lizard_Limbs")
    limbs_obj = bpy.data.objects.new("Genesis_Lizard_Limbs", limbs_mesh)
    collection.objects.link(limbs_obj)
    limbs_obj.parent = root
    limbs_obj.data.materials.append(mats["green"])      # 0: Da xanh
    limbs_obj.data.materials.append(mats["belly"])      # 1: Đáy chân cát
    limbs_obj.data.materials.append(mats["claw"])       # 2: Móng vuốt ngà cát

    bm_l = bmesh.new()

    limbs_config = [
        # Chi trước trái
        {
            "name": "front_left",
            "side": 1,
            "shoulder": Vector((0.76, -0.15, 1.05)),
            "elbow": Vector((1.32, -0.28, 0.74)),
            "wrist": Vector((1.22, -0.84, 0.16)),
            "foot_center": Vector((1.26, -1.04, 0.0)),
            "is_front": True,
            "toe_heading": math.radians(-115),
        },
        # Chi trước phải
        {
            "name": "front_right",
            "side": -1,
            "shoulder": Vector((-0.76, -0.15, 1.05)),
            "elbow": Vector((-1.32, -0.28, 0.74)),
            "wrist": Vector((-1.22, -0.84, 0.16)),
            "foot_center": Vector((-1.26, -1.04, 0.0)),
            "is_front": True,
            "toe_heading": math.radians(-65),
        },
        # Chi sau trái
        {
            "name": "hind_left",
            "side": 1,
            "shoulder": Vector((0.72, 0.92, 0.90)),
            "elbow": Vector((1.40, 1.16, 0.60)),
            "wrist": Vector((1.24, 0.80, 0.16)),
            "foot_center": Vector((1.30, 0.66, 0.0)),
            "is_front": False,
            "toe_heading": math.radians(-85),
        },
        # Chi sau phải
        {
            "name": "hind_right",
            "side": -1,
            "shoulder": Vector((-0.72, 0.92, 0.90)),
            "elbow": Vector((-1.40, 1.16, 0.60)),
            "wrist": Vector((-1.24, 0.80, 0.16)),
            "foot_center": Vector((-1.30, 0.66, 0.0)),
            "is_front": False,
            "toe_heading": math.radians(-95),
        },
    ]

    def build_organic_leg(limb):
        sh = limb["shoulder"]
        el = limb["elbow"]
        wr = limb["wrist"]
        fc = limb["foot_center"]
        side_sign = limb["side"]
        heading = limb["toe_heading"]

        arm_sections = [
            {"pt": sh, "r": 0.24, "dir": (el - sh).normalized()},
            {"pt": sh * 0.45 + el * 0.55, "r": 0.20, "dir": (el - sh).normalized()},
            {"pt": el, "r": 0.17, "dir": (wr - el).normalized()},
            {"pt": el * 0.45 + wr * 0.55, "r": 0.15, "dir": (wr - el).normalized()},
            {"pt": wr, "r": 0.14, "dir": Vector((0, 0, -1))},
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

        # 5 ngón chân
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
            p_claw = fc + dir_toe * (tlen * 1.18) + Vector((0, 0, 0.0))

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

        # Màng bơi sinh thái có độ lõm cong tự nhiên (Scalloped Webbing)
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

        # Thân ngón & Móng vuốt tự nhiên
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

            c_l = bm_l.verts.new(t_bot.co - perp_toe)
            c_r = bm_l.verts.new(t_bot.co + perp_toe)

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

    bmesh.ops.triangulate(bm_l, faces=bm_l.faces[:])
    bm_l.to_mesh(limbs_mesh)
    bm_l.free()
    for p in limbs_mesh.polygons:
        p.use_smooth = False
    limbs_mesh.update()

    print("Created organic natural low-poly lizard creature successfully!")
    return root

# Khởi tạo và tạo mới collection
col = clear_collection("Genesis_Lizard")
mats = setup_materials()

spider_arm = bpy.data.objects.get("Spider_Armature")
ground = bpy.data.objects.get("Natural_Ground")

if spider_arm:
    spider_arm.location.x = -12.0
if ground:
    ground.location.x = -12.0

# Thềm studio trắng sạch sẽ
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

# Tạo sinh vật tự nhiên tại thềm X = 3.2
lizard_root = create_creature(col, mats, offset=(3.2, 0, 0.0))

# Ánh sáng studio tự nhiên
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

# Camera chính góc 3/4 chụp gần, lấp đầy khung hình
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

# Xuất GLB và lưu blend file
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
        export_format='GLB'
    )
    print(f"Exported GLB successfully to {glb_path}")
except Exception as e:
    print(f"GLTF export warning: {e}")

try:
    bpy.ops.wm.save_mainfile()
    bpy.ops.wm.save_as_mainfile(filepath="/Users/duongnad/Documents/project/Genesis_Zero/assets/genesis_lizard.blend", copy=True)
    print("Blender projects saved.")
except Exception as e:
    print(f"Save blend warning: {e}")

print("Natural Organic Low-Poly Lizard Model Completed!")

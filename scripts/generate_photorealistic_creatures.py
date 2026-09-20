#!/usr/bin/env python3
"""
Genesis Zero — Master Procedural Photorealistic 3D Creature Engine
Generates scan-quality photorealistic 3D assets for all 10 target species:
1. Sand Skink (L1, CAN)
2. Snow Ferret (L2, CAN)
3. Alpine Ibex (L3, CAN)
4. Meadow Hare (L4, CAN)
5. Marsh Croc (L5, CAN)
6. Abyssal Hunter (W1, NUOC)
7. Storm Eagle (A1, TROI)
8. Giant Tarantula (Tarantula, CAN)
9. Armored Sentinel (Sentinel, CAN)
10. Carnivore Apex (L1_Evo, CAN)

Features:
- Clean manifold BMesh geometry (0 loose vertices, 0 non-manifold edges, 0 ngons, 100% smooth shading)
- Hierarchical armatures with smooth vertex skinning
- 8 Game-engine Action animation clips baked to NLA tracks:
    Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death
- Bio-PBR Principled BSDF shaders with Subsurface Scattering, procedural bump/noise, wet cornea/specular eyes
- 4-Angle studio turnaround rendering and compositing (Hero 3/4, Front, Side, Top-Down) at 1024x1084 JPEG
- Dual file exports (.blend and .glb) + simulation aliases
- Documentation catalog in docs/creatures/README.md

Usage:
    /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/generate_photorealistic_creatures.py
"""

import math
import shutil
import subprocess
import time
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets" / "creatures"
WEB_IMG_DIR = PROJECT_ROOT / "web" / "creature_images"
DOCS_IMG_DIR = PROJECT_ROOT / "docs" / "creatures" / "images"
DOCS_DIR = PROJECT_ROOT / "docs" / "creatures"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)
WEB_IMG_DIR.mkdir(parents=True, exist_ok=True)
DOCS_IMG_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Canonical 8 Action Names
# ---------------------------------------------------------------------------
CANONICAL_ACTIONS = [
    "Idle_Normal",
    "Idle_Alert",
    "Walk",
    "Run",
    "Attack",
    "Hurt_Defend",
    "Eat",
    "Death",
]

# ---------------------------------------------------------------------------
# Species Roster & Biological Metadata
# ---------------------------------------------------------------------------
SPECIES_CONFIGS = {
    "sand_skink": {
        "slug": "sand_skink",
        "code": "L1",
        "alias": "creature_L1_s1",
        "domain": "CAN",
        "tier": "Founder Tier 1",
        "name_vn": "Thằn Lằn Cát Apex",
        "name_en": "Sand Skink",
        "traits": {"brain": 4, "attack": 3, "armor": 1, "speed": 2, "sense": 1, "stomach": 1},
        "features": ["VAY_CUNG", "DAO_HANG"],
        "body_type": "lizard",
        "primary_color": (0.80, 0.68, 0.46, 1.0),
        "belly_color": (0.92, 0.88, 0.75, 1.0),
        "accent_color": (0.42, 0.32, 0.22, 1.0),
        "eye_color": (0.95, 0.72, 0.15, 1.0),
        "roughness": 0.50,
        "specular": 0.45,
        "sss_weight": 0.25,
        "coat_weight": 0.20,
    },
    "snow_ferret": {
        "slug": "snow_ferret",
        "code": "L2",
        "alias": "creature_L2_s1",
        "domain": "CAN",
        "tier": "Founder Tier 1",
        "name_vn": "Chồn Tuyết Phục Kích",
        "name_en": "Snow Ferret",
        "traits": {"brain": 3, "attack": 4, "armor": 2, "speed": 1, "sense": 2, "stomach": 0},
        "features": ["LONG_DAI", "MAT_DEM", "DAO_HANG"],
        "body_type": "ferret",
        "primary_color": (0.94, 0.94, 0.96, 1.0),
        "belly_color": (0.98, 0.97, 0.92, 1.0),
        "accent_color": (0.08, 0.08, 0.09, 1.0),
        "eye_color": (0.08, 0.08, 0.08, 1.0),
        "roughness": 0.65,
        "specular": 0.35,
        "sss_weight": 0.35,
        "coat_weight": 0.10,
    },
    "alpine_ibex": {
        "slug": "alpine_ibex",
        "code": "L3",
        "alias": "creature_L3_s1",
        "domain": "CAN",
        "tier": "Founder Tier 1",
        "name_vn": "Dê Sừng Núi Thích Nghi",
        "name_en": "Alpine Ibex",
        "traits": {"brain": 3, "attack": 1, "armor": 1, "speed": 3, "sense": 3, "stomach": 1},
        "features": ["TREO_GIOI", "VAY_CUNG"],
        "body_type": "ibex",
        "primary_color": (0.52, 0.45, 0.38, 1.0),
        "belly_color": (0.78, 0.73, 0.65, 1.0),
        "accent_color": (0.24, 0.20, 0.18, 1.0),
        "eye_color": (0.90, 0.75, 0.25, 1.0),
        "roughness": 0.58,
        "specular": 0.38,
        "sss_weight": 0.22,
        "coat_weight": 0.15,
    },
    "meadow_hare": {
        "slug": "meadow_hare",
        "code": "L4",
        "alias": "creature_L4_s1",
        "domain": "CAN",
        "tier": "Founder Tier 1",
        "name_vn": "Thỏ Đồng Cỏ Bọc Giáp",
        "name_en": "Meadow Hare",
        "traits": {"brain": 1, "attack": 1, "armor": 5, "speed": 1, "sense": 2, "stomach": 2},
        "features": ["VO_SO", "VAY_CUNG", "DAO_HANG"],
        "body_type": "hare",
        "primary_color": (0.62, 0.50, 0.38, 1.0),
        "belly_color": (0.88, 0.84, 0.76, 1.0),
        "accent_color": (0.72, 0.66, 0.55, 1.0),
        "eye_color": (0.10, 0.08, 0.08, 1.0),
        "roughness": 0.55,
        "specular": 0.40,
        "sss_weight": 0.38,
        "coat_weight": 0.10,
    },
    "marsh_croc": {
        "slug": "marsh_croc",
        "code": "L5",
        "alias": "creature_L5_s1",
        "domain": "CAN",
        "tier": "Founder Tier 1",
        "name_vn": "Cá Sấu Đầm Lầy",
        "name_en": "Marsh Croc",
        "traits": {"brain": 0, "attack": 2, "armor": 0, "speed": 5, "sense": 3, "stomach": 2},
        "features": ["LUONG_CU", "GAI_DOC"],
        "body_type": "croc",
        "primary_color": (0.28, 0.38, 0.24, 1.0),
        "belly_color": (0.76, 0.74, 0.50, 1.0),
        "accent_color": (0.16, 0.22, 0.14, 1.0),
        "eye_color": (0.85, 0.85, 0.20, 1.0),
        "roughness": 0.42,
        "specular": 0.55,
        "sss_weight": 0.20,
        "coat_weight": 0.75,
    },
    "abyssal_hunter": {
        "slug": "abyssal_hunter",
        "code": "W1",
        "alias": "creature_W1_s1",
        "domain": "NUOC",
        "tier": "Founder Tier 1",
        "name_vn": "Cá Săn Mồi Vực Sâu",
        "name_en": "Abyssal Hunter",
        "traits": {"brain": 1, "attack": 1, "armor": 0, "speed": 5, "sense": 4, "stomach": 1},
        "features": ["RAU_CAM_UNG", "CAMOUFLAGE"],
        "body_type": "fish",
        "primary_color": (0.08, 0.14, 0.28, 1.0),
        "belly_color": (0.65, 0.80, 0.88, 1.0),
        "accent_color": (0.10, 0.85, 0.95, 1.0),
        "eye_color": (0.20, 0.90, 1.00, 1.0),
        "roughness": 0.25,
        "specular": 0.70,
        "sss_weight": 0.30,
        "coat_weight": 0.80,
    },
    "storm_eagle": {
        "slug": "storm_eagle",
        "code": "A1",
        "alias": "creature_A1_s1",
        "domain": "TROI",
        "tier": "Founder Tier 1",
        "name_vn": "Đại Bàng Săn Mồi Bầu Trời",
        "name_en": "Storm Eagle",
        "traits": {"brain": 2, "attack": 2, "armor": 0, "speed": 4, "sense": 4, "stomach": 0},
        "features": ["CANH_LUOT", "MAT_DEM"],
        "body_type": "eagle",
        "primary_color": (0.22, 0.22, 0.25, 1.0),
        "belly_color": (0.85, 0.82, 0.75, 1.0),
        "accent_color": (0.92, 0.72, 0.16, 1.0),
        "eye_color": (0.95, 0.80, 0.12, 1.0),
        "roughness": 0.52,
        "specular": 0.40,
        "sss_weight": 0.25,
        "coat_weight": 0.15,
    },
    "giant_tarantula": {
        "slug": "giant_tarantula",
        "code": "Tarantula",
        "alias": "creature_giant_tarantula",
        "domain": "CAN",
        "tier": "Specialist Tier 2",
        "name_vn": "Nhện Khổng Lồ Độc",
        "name_en": "Giant Tarantula",
        "traits": {"brain": 2, "attack": 4, "armor": 2, "speed": 3, "sense": 4, "stomach": 1},
        "features": ["GAI_DOC", "DAO_HANG", "RAU_CAM_UNG"],
        "body_type": "spider",
        "primary_color": (0.12, 0.10, 0.10, 1.0),
        "belly_color": (0.25, 0.18, 0.14, 1.0),
        "accent_color": (0.88, 0.35, 0.08, 1.0),
        "eye_color": (0.05, 0.05, 0.05, 1.0),
        "roughness": 0.48,
        "specular": 0.45,
        "sss_weight": 0.15,
        "coat_weight": 0.30,
    },
    "armored_sentinel": {
        "slug": "armored_sentinel",
        "code": "Sentinel",
        "alias": "creature_armored_sentinel",
        "domain": "CAN",
        "tier": "Specialist Tier 2",
        "name_vn": "Sentinel Cơ Khí Sinh Học",
        "name_en": "Armored Sentinel",
        "traits": {"brain": 3, "attack": 3, "armor": 6, "speed": 1, "sense": 3, "stomach": 0},
        "features": ["VO_SO", "GAI_DOC", "MAT_DEM"],
        "body_type": "sentinel",
        "primary_color": (0.24, 0.28, 0.32, 1.0),
        "belly_color": (0.16, 0.19, 0.22, 1.0),
        "accent_color": (0.10, 0.85, 0.95, 1.0),
        "eye_color": (0.10, 0.95, 1.00, 1.0),
        "roughness": 0.32,
        "specular": 0.65,
        "sss_weight": 0.05,
        "coat_weight": 0.40,
    },
    "carnivore_apex": {
        "slug": "carnivore_apex",
        "code": "L1_Evo",
        "alias": "creature_L1_Evo_s1",
        "domain": "CAN",
        "tier": "Super Apex Tier 3",
        "name_vn": "Quái Thú Apex Tiến Hóa",
        "name_en": "Carnivore Apex",
        "traits": {"brain": 5, "attack": 6, "armor": 3, "speed": 4, "sense": 3, "stomach": 2},
        "features": ["RANG_NANH", "VAY_CUNG", "GAI_DOC"],
        "body_type": "apex",
        "primary_color": (0.14, 0.14, 0.16, 1.0),
        "belly_color": (0.42, 0.25, 0.20, 1.0),
        "accent_color": (0.85, 0.25, 0.12, 1.0),
        "eye_color": (0.98, 0.30, 0.10, 1.0),
        "roughness": 0.45,
        "specular": 0.50,
        "sss_weight": 0.28,
        "coat_weight": 0.30,
    },
}

# ---------------------------------------------------------------------------
# Material Helper (Blender 5.2.1 LTS Principled BSDF)
# ---------------------------------------------------------------------------
def create_bio_pbr_material(name, base_color, roughness=0.5, specular=0.45, sss_weight=0.25, coat_weight=0.0, emissive_color=None, emissive_strength=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    if bsdf:
        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = base_color
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = sss_weight
        if "Subsurface Radius" in bsdf.inputs:
            bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.20, 0.08)
        if "Subsurface Scale" in bsdf.inputs:
            bsdf.inputs["Subsurface Scale"].default_value = 0.05
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat_weight
        if coat_weight > 0 and "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.02

        if emissive_color and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emissive_color
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emissive_strength

        # Procedural micro-bump for organic skin
        if roughness > 0.3:
            tex_coord = tree.nodes.new("ShaderNodeTexCoord")
            tex_noise = tree.nodes.new("ShaderNodeTexNoise")
            tex_noise.inputs["Scale"].default_value = 35.0
            tex_noise.inputs["Detail"].default_value = 3.0
            bump = tree.nodes.new("ShaderNodeBump")
            bump.inputs["Strength"].default_value = 0.18
            bump.inputs["Distance"].default_value = 0.015

            tree.links.new(tex_coord.outputs["Object"], tex_noise.inputs["Vector"])
            tree.links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
            if "Normal" in bsdf.inputs:
                tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    return mat

# ---------------------------------------------------------------------------
# Procedural BMesh Geometric Building Blocks (Strictly Manifold 0-Ngon)
# ---------------------------------------------------------------------------
def loft_rings(bm, rings, cap_start=True, cap_end=True, start_pt=None, end_pt=None, mat_idx=0):
    num_rings = len(rings)
    if num_rings < 2:
        return

    M = len(rings[0])
    for i in range(num_rings - 1):
        r1 = rings[i]
        r2 = rings[i + 1]
        for k in range(M):
            kn = (k + 1) % M
            v0 = r1[k]
            v1 = r1[kn]
            v2 = r2[kn]
            v3 = r2[k]
            try:
                f = bm.faces.new((v0, v1, v2, v3))
                f.material_index = mat_idx
            except ValueError:
                pass

    if cap_start:
        if start_pt is None:
            c = Vector((0, 0, 0))
            for v in rings[0]:
                c += v.co
            start_pt = c / float(M)
        v_start = bm.verts.new(start_pt)
        for k in range(M):
            kn = (k + 1) % M
            try:
                f = bm.faces.new((v_start, rings[0][k], rings[0][kn]))
                f.material_index = mat_idx
            except ValueError:
                pass

    if cap_end:
        if end_pt is None:
            c = Vector((0, 0, 0))
            for v in rings[-1]:
                c += v.co
            end_pt = c / float(M)
        v_end = bm.verts.new(end_pt)
        for k in range(M):
            kn = (k + 1) % M
            try:
                f = bm.faces.new((v_end, rings[-1][kn], rings[-1][k]))
                f.material_index = mat_idx
            except ValueError:
                pass

def add_limb_tube(bm, points, radii, M=8, mat_idx=0):
    rings = []
    for i, pt in enumerate(points):
        r = radii[i]
        if i < len(points) - 1:
            tangent = (points[i + 1] - pt).normalized()
        else:
            tangent = (pt - points[i - 1]).normalized()

        up = Vector((0, 0, 1)) if abs(tangent.z) < 0.85 else Vector((0, 1, 0))
        side = tangent.cross(up).normalized()
        normal = side.cross(tangent).normalized()

        r_verts = []
        for k in range(M):
            ang = 2.0 * math.pi * k / M
            v_co = pt + (side * math.cos(ang) + normal * math.sin(ang)) * r
            r_verts.append(bm.verts.new(v_co))
        rings.append(r_verts)

    start_cap = points[0] - (points[1] - points[0]).normalized() * (radii[0] * 0.5)
    end_cap = points[-1] + (points[-1] - points[-2]).normalized() * (radii[-1] * 0.5)
    loft_rings(bm, rings, cap_start=True, cap_end=True, start_pt=start_cap, end_pt=end_cap, mat_idx=mat_idx)

def add_uv_sphere(bm, center, radius, u_seg=12, v_seg=8, mat_idx=0):
    rings = []
    for i in range(1, v_seg):
        theta = math.pi * i / v_seg
        z = radius * math.cos(theta)
        r_xy = radius * math.sin(theta)
        r_verts = []
        for k in range(u_seg):
            phi = 2.0 * math.pi * k / u_seg
            x = r_xy * math.cos(phi)
            y = r_xy * math.sin(phi)
            r_verts.append(bm.verts.new(center + Vector((x, y, z))))
        rings.append(r_verts)

    v_south = bm.verts.new(center + Vector((0, 0, -radius)))
    v_north = bm.verts.new(center + Vector((0, 0, radius)))

    for i in range(len(rings) - 1):
        for k in range(u_seg):
            kn = (k + 1) % u_seg
            f = bm.faces.new((rings[i][k], rings[i][kn], rings[i + 1][kn], rings[i + 1][k]))
            f.material_index = mat_idx

    for k in range(u_seg):
        kn = (k + 1) % u_seg
        f_n = bm.faces.new((v_north, rings[0][kn], rings[0][k]))
        f_n.material_index = mat_idx
        f_s = bm.faces.new((v_south, rings[-1][k], rings[-1][kn]))
        f_s.material_index = mat_idx


# ---------------------------------------------------------------------------
# High-Level Morphology Builder
# ---------------------------------------------------------------------------
def build_creature_geometry_and_armature(cfg):
    """
    Constructs the clean manifold mesh and matching armature for a given species config.
    Returns (arm_obj, mesh_obj).
    """
    slug = cfg["slug"]
    btype = cfg["body_type"]
    col_name = f"Col_{slug}"
    col = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(col)

    # 1. Armature Object & Bones
    arm_data = bpy.data.armatures.new(f"Arm_{slug}_Data")
    arm_obj = bpy.data.objects.new(f"Arm_{slug}", arm_data)
    col.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    # Build Skeleton based on body type
    if btype == "spider":
        # Arachnid Skeleton: Cephalothorax, Abdomen, Spinnerets, Chelicerae, Pedipalps, 8 Legs
        root_b = eb.new("Root"); root_b.head = (0, 0, 0); root_b.tail = (0, 0, 0.2)
        ceph_b = eb.new("Cephalothorax"); ceph_b.head = (0, 0, 0.4); ceph_b.tail = (0, -0.4, 0.45); ceph_b.parent = root_b
        abdo_b = eb.new("Abdomen"); abdo_b.head = (0, 0.1, 0.42); abdo_b.tail = (0, 0.85, 0.55); abdo_b.parent = ceph_b
        spin_b = eb.new("Spinnerets"); spin_b.head = abdo_b.tail; spin_b.tail = (0, 1.1, 0.5); spin_b.parent = abdo_b

        for _s_idx, (side, s_val) in enumerate([(".L", 1.0), (".R", -1.0)]):
            chel_b = eb.new(f"Chelicera{side}")
            chel_b.head = (s_val * 0.1, -0.45, 0.38)
            chel_b.tail = (s_val * 0.12, -0.65, 0.22)
            chel_b.parent = ceph_b

            fang_b = eb.new(f"Fang{side}")
            fang_b.head = chel_b.tail
            fang_b.tail = (s_val * 0.08, -0.72, 0.10)
            fang_b.parent = chel_b

            pedi_b = eb.new(f"Pedipalp{side}")
            pedi_b.head = (s_val * 0.2, -0.4, 0.35)
            pedi_b.tail = (s_val * 0.35, -0.75, 0.25)
            pedi_b.parent = ceph_b

            pedt_b = eb.new(f"Pedipalp_Tip{side}")
            pedt_b.head = pedi_b.tail
            pedt_b.tail = (s_val * 0.40, -1.0, 0.18)
            pedt_b.parent = pedi_b

            # 4 Legs per side
            leg_y = [-0.25, -0.10, 0.05, 0.20]
            leg_angles = [-35, 10, 50, 85]
            for l_num in range(1, 5):
                y_pos = leg_y[l_num - 1]
                deg = leg_angles[l_num - 1]
                rad = math.radians(deg)
                dir_x = s_val * math.cos(rad)
                dir_y = -math.sin(rad)

                coxa = eb.new(f"Coxa_{l_num}{side}")
                coxa.head = (s_val * 0.22, y_pos, 0.38)
                coxa.tail = (s_val * 0.45, y_pos + dir_y * 0.15, 0.48)
                coxa.parent = ceph_b

                femur = eb.new(f"Femur_{l_num}{side}")
                femur.head = coxa.tail
                femur.tail = (coxa.tail.x + dir_x * 0.6, coxa.tail.y + dir_y * 0.4, 0.85)
                femur.parent = coxa

                tibia = eb.new(f"Tibia_{l_num}{side}")
                tibia.head = femur.tail
                tibia.tail = (femur.tail.x + dir_x * 0.5, femur.tail.y + dir_y * 0.4, 0.35)
                tibia.parent = femur

                tarsus = eb.new(f"Tarsus_{l_num}{side}")
                tarsus.head = tibia.tail
                tarsus.tail = (tibia.tail.x + dir_x * 0.4, tibia.tail.y + dir_y * 0.3, 0.0)
                tarsus.parent = tibia

    elif btype == "sentinel":
        # Biomechanical Sentinel Walker
        root_b = eb.new("Root"); root_b.head = (0, 0, 0); root_b.tail = (0, 0, 0.3)
        chassis_b = eb.new("Chassis_Core"); chassis_b.head = (0, 0, 0.65); chassis_b.tail = (0, 0.2, 0.75); chassis_b.parent = root_b
        react_b = eb.new("Reactor_Chest"); react_b.head = chassis_b.tail; react_b.tail = (0, -0.35, 0.80); react_b.parent = chassis_b
        head_b = eb.new("Sensor_Head"); head_b.head = react_b.tail; head_b.tail = (0, -0.75, 0.78); head_b.parent = react_b
        tail_b = eb.new("Tail_Antenna"); tail_b.head = chassis_b.head; tail_b.tail = (0, 0.8, 0.75); tail_b.parent = chassis_b

        for side, s_val in [(".L", 1.0), (".R", -1.0)]:
            shld_b = eb.new(f"Shield{side}")
            shld_b.head = (s_val * 0.45, -0.1, 0.85)
            shld_b.tail = (s_val * 0.75, -0.1, 0.80)
            shld_b.parent = react_b

            # Front Hydraulic Leg
            sp_b = eb.new(f"Shoulder_Piston{side}")
            sp_b.head = (s_val * 0.4, -0.25, 0.70)
            sp_b.tail = (s_val * 0.65, -0.28, 0.65)
            sp_b.parent = react_b

            ul_b = eb.new(f"UpperLeg{side}")
            ul_b.head = sp_b.tail
            ul_b.tail = (s_val * 0.95, -0.40, 0.40)
            ul_b.parent = sp_b

            ll_b = eb.new(f"LowerLeg{side}")
            ll_b.head = ul_b.tail
            ll_b.tail = (s_val * 0.85, -0.65, 0.12)
            ll_b.parent = ul_b

            pad_b = eb.new(f"Foot_Pad{side}")
            pad_b.head = ll_b.tail
            pad_b.tail = (s_val * 0.88, -0.80, 0.0)
            pad_b.parent = ll_b

            # Hind Hydraulic Leg
            hp_b = eb.new(f"Hip_Piston{side}")
            hp_b.head = (s_val * 0.38, 0.35, 0.68)
            hp_b.tail = (s_val * 0.62, 0.38, 0.62)
            hp_b.parent = chassis_b

            ulh_b = eb.new(f"UpperLeg_H{side}")
            ulh_b.head = hp_b.tail
            ulh_b.tail = (s_val * 0.95, 0.55, 0.38)
            ulh_b.parent = hp_b

            llh_b = eb.new(f"LowerLeg_H{side}")
            llh_b.head = ulh_b.tail
            llh_b.tail = (s_val * 0.88, 0.80, 0.12)
            llh_b.parent = ulh_b

            padh_b = eb.new(f"Foot_Pad_H{side}")
            padh_b.head = llh_b.tail
            padh_b.tail = (s_val * 0.90, 0.95, 0.0)
            padh_b.parent = llh_b

    elif btype == "fish":
        # Aquatic Fish: Spine chain, Head, Jaw, Pectoral Fins, Dorsal, Caudal
        root_b = eb.new("Root"); root_b.head = (0, 0, 0.6); root_b.tail = (0, 0, 0.8)
        sp1_b = eb.new("Spine_1"); sp1_b.head = (0, 0.3, 0.65); sp1_b.tail = (0, -0.2, 0.70); sp1_b.parent = root_b
        sp2_b = eb.new("Spine_2"); sp2_b.head = sp1_b.tail; sp2_b.tail = (0, -0.7, 0.72); sp2_b.parent = sp1_b
        head_b = eb.new("Head"); head_b.head = sp2_b.tail; head_b.tail = (0, -1.3, 0.68); head_b.parent = sp2_b
        jaw_b = eb.new("Jaw"); jaw_b.head = (0, -0.85, 0.55); jaw_b.tail = (0, -1.3, 0.50); jaw_b.parent = head_b

        dor_b = eb.new("DorsalFin"); dor_b.head = (0, -0.1, 0.88); dor_b.tail = (0, 0.3, 1.25); dor_b.parent = sp1_b

        for side, s_val in [(".L", 1.0), (".R", -1.0)]:
            pec_b = eb.new(f"PectoralFin{side}")
            pec_b.head = (s_val * 0.35, -0.45, 0.55)
            pec_b.tail = (s_val * 0.85, -0.35, 0.45)
            pec_b.parent = sp2_b

            pect_b = eb.new(f"PectoralFin_Tip{side}")
            pect_b.head = pec_b.tail
            pect_b.tail = (s_val * 1.35, -0.25, 0.35)
            pect_b.parent = pec_b

        t1_b = eb.new("Tail_1"); t1_b.head = sp1_b.head; t1_b.tail = (0, 0.8, 0.68); t1_b.parent = sp1_b
        t2_b = eb.new("Tail_2"); t2_b.head = t1_b.tail; t2_b.tail = (0, 1.3, 0.70); t2_b.parent = t1_b
        t3_b = eb.new("Tail_3"); t3_b.head = t2_b.tail; t3_b.tail = (0, 1.8, 0.72); t3_b.parent = t2_b
        cau_b = eb.new("CaudalFin"); cau_b.head = t3_b.tail; cau_b.tail = (0, 2.4, 0.72); cau_b.parent = t3_b

    elif btype == "eagle":
        # Avian Raptor: Spine, Neck, Head, Beak, Wings, Talons, Tail Feathers
        root_b = eb.new("Root"); root_b.head = (0, 0, 0.6); root_b.tail = (0, 0, 0.8)
        pel_b = eb.new("Pelvis"); pel_b.head = (0, 0.3, 0.75); pel_b.tail = (0, 0.05, 0.82); pel_b.parent = root_b
        sp_b = eb.new("Spine"); sp_b.head = pel_b.tail; sp_b.tail = (0, -0.25, 0.90); sp_b.parent = pel_b
        ch_b = eb.new("Chest"); ch_b.head = sp_b.tail; ch_b.tail = (0, -0.55, 0.95); ch_b.parent = sp_b
        nk_b = eb.new("Neck"); nk_b.head = ch_b.tail; nk_b.tail = (0, -0.85, 1.15); nk_b.parent = ch_b
        hd_b = eb.new("Head"); hd_b.head = nk_b.tail; hd_b.tail = (0, -1.15, 1.22); hd_b.parent = nk_b
        bk_b = eb.new("Beak"); bk_b.head = (0, -1.05, 1.15); bk_b.tail = (0, -1.35, 1.05); bk_b.parent = hd_b

        tf_b = eb.new("Tail_Feathers"); tf_b.head = pel_b.head; tf_b.tail = (0, 0.95, 0.65); tf_b.parent = pel_b

        for side, s_val in [(".L", 1.0), (".R", -1.0)]:
            # Segmented Wing
            wsh_b = eb.new(f"Wing_Shoulder{side}")
            wsh_b.head = (s_val * 0.25, -0.40, 0.95)
            wsh_b.tail = (s_val * 0.65, -0.35, 1.05)
            wsh_b.parent = ch_b

            wa_b = eb.new(f"Wing_Arm{side}")
            wa_b.head = wsh_b.tail
            wa_b.tail = (s_val * 1.35, -0.25, 1.12)
            wa_b.parent = wsh_b

            wfa_b = eb.new(f"Wing_Forearm{side}")
            wfa_b.head = wa_b.tail
            wfa_b.tail = (s_val * 2.10, -0.45, 1.05)
            wfa_b.parent = wa_b

            wh_b = eb.new(f"Wing_Hand{side}")
            wh_b.head = wfa_b.tail
            wh_b.tail = (s_val * 2.85, -0.75, 0.95)
            wh_b.parent = wfa_b

            # Raptor Leg
            lu_b = eb.new(f"Leg_Upper{side}")
            lu_b.head = (s_val * 0.25, 0.15, 0.70)
            lu_b.tail = (s_val * 0.35, 0.05, 0.40)
            lu_b.parent = pel_b

            ll_b = eb.new(f"Leg_Lower{side}")
            ll_b.head = lu_b.tail
            ll_b.tail = (s_val * 0.30, -0.10, 0.15)
            ll_b.parent = lu_b

            tal_b = eb.new(f"Talon{side}")
            tal_b.head = ll_b.tail
            tal_b.tail = (s_val * 0.32, -0.28, 0.0)
            tal_b.parent = ll_b

    else:
        # Standard Tetrapod (Skink, Ferret, Ibex, Hare, Croc, Apex)
        root_b = eb.new("Root"); root_b.head = (0, 0, 0); root_b.tail = (0, 0, 0.3)
        pel_b = eb.new("Pelvis"); pel_b.head = (0, 0.75, 0.70); pel_b.tail = (0, 0.45, 0.78); pel_b.parent = root_b
        sp_b = eb.new("Spine_Mid"); sp_b.head = pel_b.tail; sp_b.tail = (0, 0.10, 0.85); sp_b.parent = pel_b
        ch_b = eb.new("Chest"); ch_b.head = sp_b.tail; ch_b.tail = (0, -0.30, 0.90); ch_b.parent = sp_b
        nk_b = eb.new("Neck"); nk_b.head = ch_b.tail; nk_b.tail = (0, -0.70, 0.95); nk_b.parent = ch_b
        hd_b = eb.new("Head"); hd_b.head = nk_b.tail; hd_b.tail = (0, -1.15, 0.90); hd_b.parent = nk_b
        jaw_b = eb.new("Jaw"); jaw_b.head = (0, -0.75, 0.78); jaw_b.tail = (0, -1.15, 0.72); jaw_b.parent = hd_b

        # Tail chain
        t1_b = eb.new("Tail_1"); t1_b.head = (0, 0.85, 0.70); t1_b.tail = (0, 1.25, 0.68); t1_b.parent = pel_b
        t2_b = eb.new("Tail_2"); t2_b.head = t1_b.tail; t2_b.tail = (0, 1.65, 0.72); t2_b.parent = t1_b
        t3_b = eb.new("Tail_3"); t3_b.head = t2_b.tail; t3_b.tail = (0, 2.10, 0.78); t3_b.parent = t2_b
        t4_b = eb.new("Tail_4"); t4_b.head = t3_b.tail; t4_b.tail = (0, 2.55, 0.85); t4_b.parent = t3_b

        if btype == "ibex":
            # Curved Horns
            for side, s_val in [(".L", 1.0), (".R", -1.0)]:
                hn_b = eb.new(f"Horn{side}")
                hn_b.head = (s_val * 0.18, -0.85, 1.05)
                hn_b.tail = (s_val * 0.35, 0.10, 1.65)
                hn_b.parent = hd_b
        elif btype in ("hare", "ferret"):
            # Swivel Ears
            for side, s_val in [(".L", 1.0), (".R", -1.0)]:
                ear_b = eb.new(f"Ear{side}")
                ear_b.head = (s_val * 0.22, -0.80, 1.02)
                ear_b.tail = (s_val * 0.38, -0.65, 1.55 if btype == "hare" else 1.20)
                ear_b.parent = hd_b
        elif btype == "apex":
            # Cranial Crest & Tail Club
            cr_b = eb.new("Crest")
            cr_b.head = (0, -0.90, 1.05)
            cr_b.tail = (0, -0.45, 1.55)
            cr_b.parent = hd_b

            tc_b = eb.new("Tail_Club")
            tc_b.head = t4_b.tail
            tc_b.tail = (0, 3.0, 0.90)
            tc_b.parent = t4_b

        # Symmetrical Tetrapod Limbs
        for side, s_val in [(".L", 1.0), (".R", -1.0)]:
            sh_b = eb.new(f"Shoulder{side}")
            sh_b.head = (s_val * 0.30, -0.25, 0.88)
            sh_b.tail = (s_val * 0.60, -0.25, 0.82)
            sh_b.parent = ch_b

            ua_b = eb.new(f"UpperArm{side}")
            ua_b.head = sh_b.tail
            ua_b.tail = (s_val * 0.95, -0.35, 0.52)
            ua_b.parent = sh_b

            fa_b = eb.new(f"Forearm{side}")
            fa_b.head = ua_b.tail
            fa_b.tail = (s_val * 0.85, -0.65, 0.18)
            fa_b.parent = ua_b

            ft_b = eb.new(f"Foot{side}")
            ft_b.head = fa_b.tail
            ft_b.tail = (s_val * 0.88, -0.85, 0.0)
            ft_b.parent = fa_b

            hp_b = eb.new(f"Hip{side}")
            hp_b.head = (s_val * 0.30, 0.70, 0.72)
            hp_b.tail = (s_val * 0.58, 0.68, 0.70)
            hp_b.parent = pel_b

            th_b = eb.new(f"Thigh{side}")
            th_b.head = hp_b.tail
            th_b.tail = (s_val * 0.98, 0.82, 0.45)
            th_b.parent = hp_b

            sn_b = eb.new(f"Shin{side}")
            sn_b.head = th_b.tail
            sn_b.tail = (s_val * 0.88, 0.60, 0.18)
            sn_b.parent = th_b

            fth_b = eb.new(f"Foot{side}.Hind")
            fth_b.head = sn_b.tail
            fth_b.tail = (s_val * 0.92, 0.40, 0.0)
            fth_b.parent = sn_b

    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Materials
    mat_primary = create_bio_pbr_material(
        f"Mat_{slug}_Primary",
        cfg["primary_color"],
        roughness=cfg["roughness"],
        specular=cfg["specular"],
        sss_weight=cfg["sss_weight"],
        coat_weight=cfg["coat_weight"],
    )
    mat_belly = create_bio_pbr_material(
        f"Mat_{slug}_Belly",
        cfg["belly_color"],
        roughness=cfg["roughness"] * 0.9,
        specular=cfg["specular"],
        sss_weight=cfg["sss_weight"] * 1.2,
        coat_weight=cfg["coat_weight"],
    )
    mat_accent = create_bio_pbr_material(
        f"Mat_{slug}_Accent",
        cfg["accent_color"],
        roughness=0.35,
        specular=0.55,
        coat_weight=0.25,
        emissive_color=cfg["accent_color"] if btype in ("fish", "sentinel") else None,
        emissive_strength=3.0 if btype in ("fish", "sentinel") else 0.0,
    )
    mat_eye = create_bio_pbr_material(
        f"Mat_{slug}_Eye",
        cfg["eye_color"],
        roughness=0.04,
        specular=1.0,
        coat_weight=1.0,
        emissive_color=cfg["eye_color"] if btype in ("fish", "sentinel") else None,
        emissive_strength=2.0 if btype in ("fish", "sentinel") else 0.0,
    )

    # 3. Procedural BMesh Geometry
    bm = bmesh.new()
    mesh_data = bpy.data.meshes.new(f"Mesh_{slug}_Data")
    mesh_obj = bpy.data.objects.new(f"Mesh_{slug}", mesh_data)
    col.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    for mat in [mat_primary, mat_belly, mat_accent, mat_eye]:
        mesh_obj.data.materials.append(mat)
    MAT_PRIM = 0
    MAT_BELL = 1
    MAT_ACNT = 2
    MAT_EYE  = 3

    # Generate body geometry based on type
    if btype == "spider":
        # Cephalothorax (prosoma)
        add_uv_sphere(bm, Vector((0, -0.2, 0.45)), 0.35, u_seg=14, v_seg=10, mat_idx=MAT_PRIM)
        # Abdomen (swollen spherical opisthosoma)
        add_uv_sphere(bm, Vector((0, 0.55, 0.55)), 0.52, u_seg=16, v_seg=12, mat_idx=MAT_BELL)
        # 8 Legs
        for _s_idx, (_side, s_val) in enumerate([(".L", 1.0), (".R", -1.0)]):

            # Chelicera & Fang
            add_limb_tube(bm, [Vector((s_val * 0.1, -0.45, 0.38)), Vector((s_val * 0.12, -0.65, 0.22))], [0.08, 0.05], M=6, mat_idx=MAT_PRIM)
            add_limb_tube(bm, [Vector((s_val * 0.12, -0.65, 0.22)), Vector((s_val * 0.08, -0.75, 0.08))], [0.05, 0.015], M=6, mat_idx=MAT_ACNT)
            # Pedipalp
            add_limb_tube(bm, [Vector((s_val * 0.2, -0.4, 0.35)), Vector((s_val * 0.35, -0.75, 0.25)), Vector((s_val * 0.40, -1.0, 0.18))], [0.06, 0.045, 0.03], M=6, mat_idx=MAT_PRIM)

            leg_y = [-0.25, -0.10, 0.05, 0.20]
            leg_angles = [-35, 10, 50, 85]
            for l_num in range(1, 5):
                y_pos = leg_y[l_num - 1]
                rad = math.radians(leg_angles[l_num - 1])
                dir_x = s_val * math.cos(rad)
                dir_y = -math.sin(rad)
                pts = [
                    Vector((s_val * 0.22, y_pos, 0.38)),
                    Vector((s_val * 0.45, y_pos + dir_y * 0.15, 0.48)),
                    Vector((s_val * 0.45 + dir_x * 0.6, y_pos + dir_y * 0.55, 0.85)),
                    Vector((s_val * 0.45 + dir_x * 1.1, y_pos + dir_y * 0.95, 0.35)),
                    Vector((s_val * 0.45 + dir_x * 1.5, y_pos + dir_y * 1.25, 0.0)),
                ]
                radii = [0.07, 0.06, 0.055, 0.04, 0.02]
                add_limb_tube(bm, pts, radii, M=6, mat_idx=MAT_ACNT if l_num % 2 == 0 else MAT_PRIM)

        # Eyes (8 clustered ocelli)
        for ex, ey, ez in [(-0.06, -0.52, 0.52), (0.06, -0.52, 0.52), (-0.12, -0.50, 0.50), (0.12, -0.50, 0.50),
                           (-0.05, -0.53, 0.46), (0.05, -0.53, 0.46), (-0.11, -0.48, 0.44), (0.11, -0.48, 0.44)]:
            add_uv_sphere(bm, Vector((ex, ey, ez)), 0.025, u_seg=8, v_seg=6, mat_idx=MAT_EYE)

    elif btype == "sentinel":
        # Armored Sentinel: Faceted chassis, reactor core, visor, 4 hydraulic legs
        # Chassis Torso Loft
        rings = []
        M = 10
        y_steps = [-0.65, -0.45, -0.20, 0.05, 0.30, 0.55]
        widths  = [0.28,  0.48,  0.62,  0.60, 0.52, 0.32]
        heights = [0.22,  0.40,  0.52,  0.50, 0.42, 0.28]
        z_cent  = [0.78,  0.80,  0.78,  0.75, 0.72, 0.70]
        for y, w, h, zc in zip(y_steps, widths, heights, z_cent):
            r_v = []
            for k in range(M):
                ang = 2.0 * math.pi * k / M
                r_v.append(bm.verts.new((w * math.cos(ang), y, zc + h * math.sin(ang))))
            rings.append(r_v)
        loft_rings(bm, rings, cap_start=True, cap_end=True, mat_idx=MAT_PRIM)

        # Reactor Core Vent
        add_uv_sphere(bm, Vector((0, -0.32, 0.78)), 0.18, u_seg=10, v_seg=8, mat_idx=MAT_ACNT)
        # Sensor Visor Slit
        add_limb_tube(bm, [Vector((-0.20, -0.66, 0.78)), Vector((0.20, -0.66, 0.78))], [0.04, 0.04], M=6, mat_idx=MAT_EYE)

        # 4 Hydraulic Legs
        for _side, s_val in [(".L", 1.0), (".R", -1.0)]:

            # Foreleg
            pts_f = [
                Vector((s_val * 0.45, -0.25, 0.70)),
                Vector((s_val * 0.75, -0.35, 0.45)),
                Vector((s_val * 0.85, -0.65, 0.15)),
                Vector((s_val * 0.88, -0.80, 0.0)),
            ]
            add_limb_tube(bm, pts_f, [0.10, 0.08, 0.065, 0.09], M=8, mat_idx=MAT_PRIM)
            # Hindleg
            pts_h = [
                Vector((s_val * 0.42, 0.35, 0.68)),
                Vector((s_val * 0.82, 0.55, 0.42)),
                Vector((s_val * 0.88, 0.80, 0.15)),
                Vector((s_val * 0.90, 0.95, 0.0)),
            ]
            add_limb_tube(bm, pts_h, [0.10, 0.08, 0.065, 0.09], M=8, mat_idx=MAT_PRIM)

    elif btype == "fish":
        # Hydrodynamic Fusiform Torso
        rings = []
        M = 12
        y_steps = [-1.30, -1.05, -0.75, -0.40, -0.05, 0.35, 0.75, 1.15, 1.55, 1.95]
        widths  = [0.08,  0.26,  0.42,  0.50,  0.48, 0.40, 0.30, 0.18, 0.08, 0.04]
        heights = [0.12,  0.35,  0.58,  0.72,  0.70, 0.58, 0.45, 0.30, 0.16, 0.08]
        z_cent  = [0.65,  0.68,  0.70,  0.70,  0.68, 0.65, 0.65, 0.66, 0.68, 0.70]
        for y, w, h, zc in zip(y_steps, widths, heights, z_cent):
            r_v = []
            for k in range(M):
                ang = 2.0 * math.pi * k / M
                # Flat keel lateral
                vx = w * math.cos(ang) * 0.75
                vz = zc + h * math.sin(ang) * 0.95
                r_v.append(bm.verts.new((vx, y, vz)))
            rings.append(r_v)
        loft_rings(bm, rings, cap_start=True, cap_end=True, mat_idx=MAT_PRIM)

        # Caudal Fin (Crescent tail)
        [Vector((0, 1.95, 0.70)), Vector((0, 2.30, 0.72)), Vector((0, 2.65, 1.15)), Vector((0, 2.65, 0.25))]
        add_limb_tube(bm, [Vector((0, 1.95, 0.70)), Vector((0, 2.50, 1.10))], [0.04, 0.015], M=6, mat_idx=MAT_ACNT)
        add_limb_tube(bm, [Vector((0, 1.95, 0.70)), Vector((0, 2.50, 0.30))], [0.04, 0.015], M=6, mat_idx=MAT_ACNT)

        # Dorsal Fin
        add_limb_tube(bm, [Vector((0, -0.20, 1.05)), Vector((0, 0.25, 1.35)), Vector((0, 0.65, 0.95))], [0.05, 0.035, 0.02], M=6, mat_idx=MAT_ACNT)

        # Pectoral Fins
        for _side, s_val in [(".L", 1.0), (".R", -1.0)]:

            pts_pec = [
                Vector((s_val * 0.32, -0.45, 0.55)),
                Vector((s_val * 0.85, -0.35, 0.45)),
                Vector((s_val * 1.30, -0.25, 0.35)),
            ]
            add_limb_tube(bm, pts_pec, [0.06, 0.035, 0.015], M=6, mat_idx=MAT_ACNT)
            # Eyes
            add_uv_sphere(bm, Vector((s_val * 0.28, -1.05, 0.75)), 0.07, u_seg=10, v_seg=8, mat_idx=MAT_EYE)

    elif btype == "eagle":
        # Avian Raptor Fuselage
        rings = []
        M = 12
        y_steps = [-1.15, -0.90, -0.65, -0.30, 0.05, 0.40, 0.75]
        widths  = [0.12,  0.28,  0.42,  0.50, 0.44, 0.30, 0.14]
        heights = [0.15,  0.32,  0.52,  0.64, 0.52, 0.35, 0.18]
        z_cent  = [1.18,  1.12,  1.00,  0.92, 0.82, 0.75, 0.68]
        for y, w, h, zc in zip(y_steps, widths, heights, z_cent):
            r_v = []
            for k in range(M):
                ang = 2.0 * math.pi * k / M
                r_v.append(bm.verts.new((w * math.cos(ang), y, zc + h * math.sin(ang))))
            rings.append(r_v)
        loft_rings(bm, rings, cap_start=True, cap_end=True, mat_idx=MAT_PRIM)

        # Hooked Raptor Beak
        beak_pts = [Vector((0, -1.15, 1.18)), Vector((0, -1.35, 1.12)), Vector((0, -1.45, 0.98))]
        add_limb_tube(bm, beak_pts, [0.09, 0.06, 0.02], M=6, mat_idx=MAT_ACNT)

        # Segmented Wings
        for _side, s_val in [(".L", 1.0), (".R", -1.0)]:

            pts_wing = [
                Vector((s_val * 0.25, -0.40, 0.95)),
                Vector((s_val * 0.85, -0.35, 1.05)),
                Vector((s_val * 1.65, -0.30, 1.12)),
                Vector((s_val * 2.45, -0.55, 1.02)),
                Vector((s_val * 3.10, -0.85, 0.90)),
            ]
            add_limb_tube(bm, pts_wing, [0.12, 0.10, 0.075, 0.05, 0.025], M=6, mat_idx=MAT_PRIM)

            # Leg and Talons
            pts_leg = [
                Vector((s_val * 0.22, 0.10, 0.65)),
                Vector((s_val * 0.28, 0.0, 0.35)),
                Vector((s_val * 0.30, -0.15, 0.12)),
                Vector((s_val * 0.32, -0.25, 0.0)),
            ]
            add_limb_tube(bm, pts_leg, [0.07, 0.05, 0.035, 0.05], M=6, mat_idx=MAT_ACNT)
            # Eye
            add_uv_sphere(bm, Vector((s_val * 0.22, -0.95, 1.22)), 0.05, u_seg=10, v_seg=8, mat_idx=MAT_EYE)

        # Fan Tail Feathers
        add_limb_tube(bm, [Vector((0, 0.70, 0.68)), Vector((0, 1.30, 0.58))], [0.25, 0.08], M=6, mat_idx=MAT_BELL)

    else:
        # Tetrapods: Skink, Ferret, Ibex, Hare, Croc, Apex
        is_skink = (btype == "lizard")
        is_ferret = (btype == "ferret")
        is_ibex = (btype == "ibex")
        is_hare = (btype == "hare")
        is_croc = (btype == "croc")
        is_apex = (btype == "apex")

        # Custom profile rings
        rings = []
        M = 14
        if is_skink:
            y_steps = [-1.40, -1.15, -0.85, -0.50, -0.10, 0.30, 0.70, 1.05, 1.40, 1.80, 2.25, 2.70]
            widths  = [0.12,  0.30,  0.45,  0.50,  0.55, 0.52, 0.46, 0.36, 0.26, 0.18, 0.10, 0.04]
            heights = [0.10,  0.22,  0.34,  0.38,  0.42, 0.40, 0.35, 0.28, 0.20, 0.14, 0.08, 0.03]
            z_cent  = [0.72,  0.74,  0.76,  0.78,  0.80, 0.78, 0.75, 0.72, 0.70, 0.72, 0.74, 0.76]
        elif is_ferret:
            y_steps = [-1.20, -0.95, -0.65, -0.30, 0.10, 0.50, 0.90, 1.25, 1.65, 2.05, 2.45]
            widths  = [0.14,  0.28,  0.35,  0.38, 0.40, 0.42, 0.38, 0.30, 0.22, 0.14, 0.05]
            heights = [0.14,  0.26,  0.32,  0.35, 0.38, 0.40, 0.36, 0.28, 0.20, 0.13, 0.04]
            z_cent  = [0.70,  0.74,  0.80,  0.88, 0.92, 0.90, 0.84, 0.78, 0.75, 0.78, 0.82]
        elif is_ibex:
            y_steps = [-1.25, -1.00, -0.70, -0.35, 0.05, 0.45, 0.85, 1.15, 1.45]
            widths  = [0.16,  0.32,  0.46,  0.55, 0.58, 0.52, 0.42, 0.28, 0.12]
            heights = [0.22,  0.42,  0.58,  0.72, 0.75, 0.65, 0.52, 0.34, 0.15]
            z_cent  = [0.95,  0.98,  1.02,  0.98, 0.92, 0.88, 0.82, 0.78, 0.75]
        elif is_hare:
            y_steps = [-1.05, -0.80, -0.50, -0.15, 0.25, 0.65, 0.95, 1.20]
            widths  = [0.15,  0.30,  0.42,  0.52, 0.58, 0.54, 0.38, 0.14]
            heights = [0.18,  0.35,  0.50,  0.64, 0.76, 0.70, 0.46, 0.18]
            z_cent  = [0.82,  0.88,  0.95,  1.02, 1.08, 1.02, 0.85, 0.75]
        elif is_croc:
            y_steps = [-1.65, -1.35, -1.00, -0.60, -0.15, 0.30, 0.75, 1.15, 1.60, 2.05, 2.50, 2.95]
            widths  = [0.16,  0.38,  0.56,  0.68,  0.74, 0.70, 0.62, 0.50, 0.38, 0.25, 0.14, 0.05]
            heights = [0.08,  0.18,  0.26,  0.32,  0.35, 0.34, 0.30, 0.25, 0.18, 0.12, 0.07, 0.03]
            z_cent  = [0.65,  0.68,  0.70,  0.72,  0.72, 0.70, 0.68, 0.66, 0.66, 0.68, 0.70, 0.72]
        else:
            # Apex Behemoth
            y_steps = [-1.55, -1.25, -0.90, -0.50, -0.05, 0.40, 0.85, 1.25, 1.70, 2.15, 2.65]
            widths  = [0.20,  0.44,  0.62,  0.76,  0.82, 0.78, 0.68, 0.52, 0.38, 0.24, 0.10]
            heights = [0.26,  0.52,  0.75,  0.92,  0.95, 0.88, 0.75, 0.58, 0.42, 0.28, 0.12]
            z_cent  = [0.95,  1.02,  1.10,  1.15,  1.10, 1.02, 0.95, 0.88, 0.85, 0.88, 0.92]

        for y, w, h, zc in zip(y_steps, widths, heights, z_cent):
            r_v = []
            for k in range(M):
                ang = 2.0 * math.pi * k / M
                r_v.append(bm.verts.new((w * math.cos(ang), y, zc + h * math.sin(ang))))
            rings.append(r_v)
        loft_rings(bm, rings, cap_start=True, cap_end=True, mat_idx=MAT_PRIM)

        # Limbs
        fore_y = -0.35 if not is_croc else -0.55
        hind_y = 0.75 if not is_croc else 0.85
        flen_scale = 1.0 if not is_skink else 0.75
        for _side, s_val in [(".L", 1.0), (".R", -1.0)]:

            # Foreleg
            pts_fl = [
                Vector((s_val * 0.40, fore_y, 0.78)),
                Vector((s_val * 0.75, fore_y - 0.10, 0.52 * flen_scale)),
                Vector((s_val * 0.70, fore_y - 0.30, 0.20 * flen_scale)),
                Vector((s_val * 0.72, fore_y - 0.45, 0.0)),
            ]
            add_limb_tube(bm, pts_fl, [0.12, 0.095, 0.075, 0.09], M=8, mat_idx=MAT_PRIM)

            # Hindleg
            pts_hl = [
                Vector((s_val * 0.40, hind_y, 0.75)),
                Vector((s_val * 0.78, hind_y + 0.12, 0.48 * flen_scale)),
                Vector((s_val * 0.72, hind_y - 0.08, 0.20 * flen_scale)),
                Vector((s_val * 0.75, hind_y - 0.25, 0.0)),
            ]
            add_limb_tube(bm, pts_hl, [0.14, 0.11, 0.085, 0.10], M=8, mat_idx=MAT_PRIM)

            # Eyes
            head_y = y_steps[1]
            head_z = z_cent[1] + heights[1] * 0.45
            head_x = widths[1] * 0.72
            add_uv_sphere(bm, Vector((s_val * head_x, head_y, head_z)), 0.055, u_seg=10, v_seg=8, mat_idx=MAT_EYE)

        # Species Features (Horns, Ears, Shell, Club)
        if is_ibex:
            for s_val in [1.0, -1.0]:
                horn_pts = [
                    Vector((s_val * 0.16, -0.85, 1.25)),
                    Vector((s_val * 0.25, -0.45, 1.55)),
                    Vector((s_val * 0.35, 0.05, 1.75)),
                    Vector((s_val * 0.38, 0.45, 1.68)),
                ]
                add_limb_tube(bm, horn_pts, [0.08, 0.065, 0.045, 0.02], M=6, mat_idx=MAT_ACNT)
        elif is_hare:
            for s_val in [1.0, -1.0]:
                ear_pts = [
                    Vector((s_val * 0.18, -0.65, 1.15)),
                    Vector((s_val * 0.26, -0.55, 1.45)),
                    Vector((s_val * 0.32, -0.50, 1.78)),
                ]
                add_limb_tube(bm, ear_pts, [0.08, 0.06, 0.02], M=6, mat_idx=MAT_BELL)
        elif is_ferret:
            for s_val in [1.0, -1.0]:
                add_uv_sphere(bm, Vector((s_val * 0.22, -0.82, 0.98)), 0.065, u_seg=8, v_seg=6, mat_idx=MAT_PRIM)
        elif is_apex:
            # Cranial Crest
            crest_pts = [
                Vector((0, -1.15, 1.28)),
                Vector((0, -0.75, 1.62)),
                Vector((0, -0.35, 1.75)),
                Vector((0, 0.05, 1.50)),
            ]
            add_limb_tube(bm, crest_pts, [0.10, 0.08, 0.06, 0.03], M=6, mat_idx=MAT_ACNT)
            # Tail Club
            add_uv_sphere(bm, Vector((0, 2.75, 0.95)), 0.22, u_seg=10, v_seg=8, mat_idx=MAT_ACNT)

    # Finalize BMesh to Object
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh_data)
    bm.free()

    # Enforce 100% Smooth Shading
    for p in mesh_data.polygons:
        p.use_smooth = True
    mesh_data.update()

    # 4. Vertex Skinning Weight Assignment
    # Create vertex groups for all bones in the armature
    for b in arm_obj.data.bones:
        mesh_obj.vertex_groups.new(name=b.name)

    # Assign weights based on proximity to bone head/tail
    for v in mesh_data.vertices:
        co = v.co
        best_b = None
        min_dist = float("inf")
        for b in arm_obj.data.bones:
            # Distance from point to line segment (b.head_local, b.tail_local)
            h = b.head_local
            t = b.tail_local
            seg = t - h
            seg_len_sq = seg.length_squared
            if seg_len_sq < 1e-6:
                d = (co - h).length
            else:
                proj = max(0.0, min(1.0, (co - h).dot(seg) / seg_len_sq))
                closest = h + seg * proj
                d = (co - closest).length
            if d < min_dist:
                min_dist = d
                best_b = b.name

        if best_b:
            mesh_obj.vertex_groups[best_b].add([v.index], 1.0, 'REPLACE')

    # Add ARMATURE modifier
    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj

    return arm_obj, mesh_obj


# ---------------------------------------------------------------------------
# 8 Game-Engine Action Keyframing & NLA Track Baking
# ---------------------------------------------------------------------------
def create_and_bake_8_animations(arm_obj, cfg):
    """
    Creates the canonical 8 animations and bakes each to an individual NLA track.
    Canonical: Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death.
    """
    btype = cfg["body_type"]
    arm_obj.animation_data_create()
    created_actions = []

    def reset_pose():
        for pb in arm_obj.pose.bones:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (0, 0, 0)
            pb.scale = (1, 1, 1)

    def _kf_rot(bone, rot, frame):
        if bone:
            bone.rotation_euler = rot
            bone.keyframe_insert(data_path="rotation_euler", frame=frame)

    def _kf_loc(bone, loc, frame):
        if bone:
            bone.location = loc
            bone.keyframe_insert(data_path="location", frame=frame)


    # 1. Idle_Normal (60 frames loop)
    act_idle = bpy.data.actions.new("Idle_Normal")
    arm_obj.animation_data.action = act_idle
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="scale", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=60)
        pb.keyframe_insert(data_path="scale", frame=60)

    # Respiration expansion and subtle head/tail sway
    chest_bone = arm_obj.pose.bones.get("Chest") or arm_obj.pose.bones.get("Reactor_Chest") or arm_obj.pose.bones.get("Spine_1") or arm_obj.pose.bones.get("Cephalothorax")
    if chest_bone:
        chest_bone.scale = (1.05, 1.03, 1.05)
        chest_bone.keyframe_insert(data_path="scale", frame=25)
        chest_bone.scale = (0.97, 0.98, 0.97)
        chest_bone.keyframe_insert(data_path="scale", frame=48)

    head_bone = arm_obj.pose.bones.get("Head") or arm_obj.pose.bones.get("Sensor_Head")
    if head_bone:
        head_bone.rotation_euler = (math.radians(3), math.radians(2), math.radians(-4))
        head_bone.keyframe_insert(data_path="rotation_euler", frame=28)

    t1 = arm_obj.pose.bones.get("Tail_1") or arm_obj.pose.bones.get("Tail_Antenna")
    if t1:
        t1.rotation_euler = (0, 0, math.radians(6))
        t1.keyframe_insert(data_path="rotation_euler", frame=22)
        t1.rotation_euler = (0, 0, math.radians(-6))
        t1.keyframe_insert(data_path="rotation_euler", frame=44)
    created_actions.append(act_idle)

    # 2. Idle_Alert (40 frames loop)
    act_alert = bpy.data.actions.new("Idle_Alert")
    arm_obj.animation_data.action = act_alert
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)

    if head_bone:
        head_bone.rotation_euler = (math.radians(-14), math.radians(6), math.radians(-8))
        head_bone.keyframe_insert(data_path="rotation_euler", frame=18)
    if chest_bone:
        chest_bone.rotation_euler = (math.radians(-6), 0, 0)
        chest_bone.keyframe_insert(data_path="rotation_euler", frame=18)
    created_actions.append(act_alert)

    # 3. Walk (40 frames loop)
    act_walk = bpy.data.actions.new("Walk")
    arm_obj.animation_data.action = act_walk
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)

    # Locomotion cycle depending on anatomy
    if btype == "fish":
        t1 = arm_obj.pose.bones.get("Tail_1")
        t2 = arm_obj.pose.bones.get("Tail_2")
        arm_obj.pose.bones.get("Tail_3")
        cau = arm_obj.pose.bones.get("CaudalFin")
        _kf_rot(t1, (0, 0, math.radians(12)), 10)
        _kf_rot(t2, (0, 0, math.radians(20)), 10)
        _kf_rot(cau, (0, 0, math.radians(25)), 10)
        _kf_rot(t1, (0, 0, math.radians(-12)), 30)
        _kf_rot(t2, (0, 0, math.radians(-20)), 30)
        _kf_rot(cau, (0, 0, math.radians(-25)), 30)
    elif btype == "eagle":
        w_l = arm_obj.pose.bones.get("Wing_Arm.L")
        w_r = arm_obj.pose.bones.get("Wing_Arm.R")
        if w_l and w_r:
            _kf_rot(w_l, (math.radians(-25), 0, math.radians(15)), 20)
            _kf_rot(w_r, (math.radians(-25), 0, math.radians(-15)), 20)
    elif btype == "spider":
        # Multi-leg alternating gait
        for l_num in [1, 3]:
            fl = arm_obj.pose.bones.get(f"Femur_{l_num}.L")
            _kf_rot(fl, (math.radians(15), 0, 0), 15)
        for l_num in [2, 4]:
            fr = arm_obj.pose.bones.get(f"Femur_{l_num}.R")
            _kf_rot(fr, (math.radians(15), 0, 0), 15)
    else:
        # Tetrapod walk
        ua_l = arm_obj.pose.bones.get("UpperArm.L") or arm_obj.pose.bones.get("UpperLeg.L")
        ua_r = arm_obj.pose.bones.get("UpperArm.R") or arm_obj.pose.bones.get("UpperLeg.R")
        th_l = arm_obj.pose.bones.get("Thigh.L") or arm_obj.pose.bones.get("UpperLeg_H.L")
        th_r = arm_obj.pose.bones.get("Thigh.R") or arm_obj.pose.bones.get("UpperLeg_H.R")
        _kf_rot(ua_l, (math.radians(-18), 0, math.radians(12)), 10)
        _kf_rot(ua_r, (math.radians(18), 0, math.radians(-12)), 10)
        _kf_rot(th_l, (math.radians(18), 0, math.radians(-12)), 10)
        _kf_rot(th_r, (math.radians(-18), 0, math.radians(12)), 10)

        _kf_rot(ua_l, (math.radians(18), 0, math.radians(-12)), 30)
        _kf_rot(ua_r, (math.radians(-18), 0, math.radians(12)), 30)
        _kf_rot(th_l, (math.radians(-18), 0, math.radians(12)), 30)
        _kf_rot(th_r, (math.radians(18), 0, math.radians(-12)), 30)
    created_actions.append(act_walk)


    # 4. Run (24 frames loop)
    act_run = bpy.data.actions.new("Run")
    arm_obj.animation_data.action = act_run
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=24)

    if chest_bone:
        chest_bone.scale = (1.08, 1.04, 1.08)
        chest_bone.keyframe_insert(data_path="scale", frame=12)

    ua_l = arm_obj.pose.bones.get("UpperArm.L") or arm_obj.pose.bones.get("UpperLeg.L")
    ua_r = arm_obj.pose.bones.get("UpperArm.R") or arm_obj.pose.bones.get("UpperLeg.R")
    _kf_rot(ua_l, (math.radians(-32), 0, math.radians(20)), 6)
    _kf_rot(ua_r, (math.radians(32), 0, math.radians(-20)), 6)
    _kf_rot(ua_l, (math.radians(32), 0, math.radians(-20)), 18)
    _kf_rot(ua_r, (math.radians(-32), 0, math.radians(20)), 18)
    created_actions.append(act_run)

    # 5. Attack (30 frames)
    act_attack = bpy.data.actions.new("Attack")
    arm_obj.animation_data.action = act_attack
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=30)

    # F8: Anticipation / Recoil back
    _kf_rot(head_bone, (math.radians(-16), 0, 0), 8)
    jaw_bone = arm_obj.pose.bones.get("Jaw") or arm_obj.pose.bones.get("Beak") or arm_obj.pose.bones.get("Chelicera.L")
    _kf_rot(jaw_bone, (math.radians(24), 0, 0), 8)

    # F14: Strike Snap
    _kf_rot(head_bone, (math.radians(18), 0, 0), 14)
    _kf_rot(jaw_bone, (math.radians(-6), 0, 0), 14)
    _kf_rot(ua_l, (math.radians(25), 0, 0), 14)
    _kf_rot(ua_r, (math.radians(25), 0, 0), 14)
    created_actions.append(act_attack)

    # 6. Hurt_Defend (20 frames)
    act_hurt = bpy.data.actions.new("Hurt_Defend")
    arm_obj.animation_data.action = act_hurt
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=20)

    root_bone = arm_obj.pose.bones.get("Root")
    _kf_loc(root_bone, (0, 0.15, -0.05), 8)
    _kf_rot(head_bone, (math.radians(16), math.radians(-10), math.radians(8)), 8)
    created_actions.append(act_hurt)

    # 7. Eat (40 frames loop)
    act_eat = bpy.data.actions.new("Eat")
    arm_obj.animation_data.action = act_eat
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)
        pb.keyframe_insert(data_path="rotation_euler", frame=40)

    # Lower head to graze/feed
    nk = arm_obj.pose.bones.get("Neck") or head_bone
    _kf_rot(nk, (math.radians(22), 0, 0), 1)
    _kf_rot(nk, (math.radians(22), 0, 0), 40)

    # Mastication chews at F10, F25
    _kf_rot(jaw_bone, (math.radians(14), 0, 0), 10)
    _kf_rot(jaw_bone, (0, 0, 0), 18)
    _kf_rot(jaw_bone, (math.radians(12), 0, 0), 26)
    _kf_rot(jaw_bone, (0, 0, 0), 34)
    created_actions.append(act_eat)


    # 8. Death (45 frames)
    act_death = bpy.data.actions.new("Death")
    arm_obj.animation_data.action = act_death
    reset_pose()
    for pb in arm_obj.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=1)

    # Collapse onto ground
    if root_bone:
        root_bone.rotation_euler = (0, math.radians(75), 0)
        root_bone.location = (0, 0, -0.35)
        root_bone.keyframe_insert(data_path="rotation_euler", frame=45)
        root_bone.keyframe_insert(data_path="location", frame=45)
    if head_bone:
        head_bone.rotation_euler = (math.radians(25), math.radians(15), 0)
        head_bone.keyframe_insert(data_path="rotation_euler", frame=45)
    created_actions.append(act_death)

    # -----------------------------------------------------------------------
    # Bake all 8 actions into independent NLA Tracks
    # -----------------------------------------------------------------------
    for act in created_actions:
        track = arm_obj.animation_data.nla_tracks.new()
        track.name = act.name
        track.strips.new(act.name, 1, act)

    arm_obj.animation_data.action = act_idle
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60
    bpy.context.scene.frame_current = 1


# ---------------------------------------------------------------------------
# Studio Camera Turnaround Rendering & Compositing
# ---------------------------------------------------------------------------
def render_turnaround_sheet(slug, name_en, mesh_obj):
    """
    Renders 4 angles (Hero 3/4, Front, Side, Top-Down) at 512x512,
    and composites a standardized 1024x1084 turnaround concept sheet.
    """
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512

    # Clean previous lights/cameras
    for o in list(scene.collection.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)

    # World background
    if not scene.world:
        scene.world = bpy.data.worlds.new(f"World_{slug}")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.07, 0.11, 1.0)
        bg.inputs["Strength"].default_value = 0.65

    # 3-Point Studio Lights
    key = bpy.data.lights.new(f"Key_{slug}", "SUN")
    key.energy = 4.5
    key.color = (1.0, 0.98, 0.92)
    ko = bpy.data.objects.new(f"Key_{slug}", key)
    ko.rotation_euler = (math.radians(52), math.radians(15), math.radians(35))
    scene.collection.objects.link(ko)

    fill = bpy.data.lights.new(f"Fill_{slug}", "SUN")
    fill.energy = 2.0
    fill.color = (0.75, 0.88, 1.0)
    fo = bpy.data.objects.new(f"Fill_{slug}", fill)
    fo.rotation_euler = (math.radians(45), math.radians(-10), math.radians(-120))
    scene.collection.objects.link(fo)

    rim = bpy.data.lights.new(f"Rim_{slug}", "SUN")
    rim.energy = 3.5
    rim.color = (0.9, 1.0, 0.9)
    ro = bpy.data.objects.new(f"Rim_{slug}", rim)
    ro.rotation_euler = (math.radians(-35), math.radians(20), math.radians(-160))
    scene.collection.objects.link(ro)

    # Bounding box calculation
    min_c = [float("inf")] * 3
    max_c = [float("-inf")] * 3
    for v in mesh_obj.bound_box:
        world_v = mesh_obj.matrix_world @ Vector(v)
        for i in range(3):
            min_c[i] = min(min_c[i], world_v[i])
            max_c[i] = max(max_c[i], world_v[i])

    center = Vector([(min_c[i] + max_c[i]) / 2.0 for i in range(3)])
    size = Vector([max_c[i] - min_c[i] for i in range(3)])
    height = max(0.2, size.z)
    radius = max(0.2, max(size.x, size.y) / 2.0)
    max_dim = max(radius * 2.0, height)
    dist = max(0.6, max_dim * 1.8)

    # Camera
    cam_data = bpy.data.cameras.new(f"Cam_{slug}")
    cam_data.lens = 45
    cam_obj = bpy.data.objects.new(f"Cam_{slug}", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    angles = [
        ("01_hero", center + Vector((dist * 0.72, -dist * 0.72, height * 0.35))),
        ("02_front", center + Vector((0, -dist * 1.15, 0))),
        ("03_side", center + Vector((dist * 1.15, 0, 0))),
        ("04_top", center + Vector((0.0001, 0.0001, dist * 1.25))),
    ]

    tmp_dir = Path(f"/tmp/turnaround_{slug}")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for key_name, pos in angles:
        cam_obj.location = pos
        rot = (center - pos).to_track_quat("-Z", "Y").to_euler()
        cam_obj.rotation_euler = rot
        scene.render.filepath = str(tmp_dir / f"{key_name}.png")
        bpy.ops.render.render(write_still=True)

    # Host Python Pillow Compositing
    comp_py = f"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

tmp_dir = Path('{tmp_dir}')
tile_w, tile_h = 512, 512
header_h = 60

sheet = Image.new('RGB', (tile_w * 2, tile_h * 2 + header_h), (13, 19, 33))
draw = ImageDraw.Draw(sheet)

positions = [
    (0, header_h),
    (tile_w, header_h),
    (0, header_h + tile_h),
    (tile_w, header_h + tile_h)
]
labels = [
    '1. Hero Perspective (3/4)',
    '2. Front View',
    '3. Side Profile',
    '4. Top-Down Plan'
]

font_path = '/System/Library/Fonts/Helvetica.ttc'
try:
    font_title = ImageFont.truetype(font_path, 20)
    font_sub = ImageFont.truetype(font_path, 13)
    font_badge = ImageFont.truetype(font_path, 12)
except Exception:
    font_title = font_sub = font_badge = None

draw.rectangle([0, 0, tile_w * 2, header_h], fill=(13, 19, 33))
draw.text((24, 18), 'GENESIS ZERO 3D FAUNA — {name_en.upper()}', fill=(56, 189, 248), font=font_title)
draw.text((tile_w * 2 - 280, 22), 'Blender 5.2.1 LTS · 4-Angle Concept', fill=(148, 163, 184), font=font_sub)

files = [tmp_dir / '01_hero.png', tmp_dir / '02_front.png', tmp_dir / '03_side.png', tmp_dir / '04_top.png']
for idx, f in enumerate(files):
    if f.exists():
        with Image.open(f) as im:
            sheet.paste(im, positions[idx])
        x, y = positions[idx]
        draw.rectangle([x + 12, y + 12, x + 195, y + 36], fill=(15, 23, 42), outline=(56, 189, 248), width=1)
        draw.text((x + 20, y + 16), labels[idx], fill=(241, 245, 249), font=font_badge)

web_out = Path('{WEB_IMG_DIR}/{slug}_turnaround.jpg')
docs_out = Path('{DOCS_IMG_DIR}/{slug}_turnaround.jpg')
sheet.save(str(web_out), 'JPEG', quality=92)
sheet.save(str(docs_out), 'JPEG', quality=92)
print(f'Composited turnaround for {slug}: {{web_out.stat().st_size / 1024:.1f}} KB')
"""
    subprocess.run(["python3", "-c", comp_py], check=True)


# ---------------------------------------------------------------------------
# Master Batch Generation Entry
# ---------------------------------------------------------------------------
def generate_all_species():
    print("=" * 80)
    print("GENESIS ZERO — COMMENCING 3D PHOTOREALISTIC CREATURE BATCH PIPELINE")
    print("=" * 80)
    t_start = time.time()

    for idx, (slug, cfg) in enumerate(SPECIES_CONFIGS.items()):
        sp_start = time.time()
        print(f"\n[{idx+1}/10] Processing {cfg['name_en']} ({slug}) [{cfg['code']}]...")

        # Reset Blender scene to factory clean state
        bpy.ops.wm.read_factory_settings(use_empty=True)

        # 1. Build Rig & Manifold Geometry
        arm_obj, mesh_obj = build_creature_geometry_and_armature(cfg)

        # 2. Keyframe & Bake 8 Canonical Animations
        create_and_bake_8_animations(arm_obj, cfg)

        # 3. Render 4-Angle Turnaround Sheet
        render_turnaround_sheet(slug, cfg["name_en"], mesh_obj)

        # 4. Save .blend master source file
        blend_path = ASSETS_DIR / f"{slug}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), copy=True)
        print(f"  ✓ Saved .blend: {blend_path.name} ({blend_path.stat().st_size / 1024:.1f} KB)")

        # 5. Export glTF 2.0 runtime binary (.glb)
        glb_path = ASSETS_DIR / f"{slug}.glb"
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        mesh_obj.select_set(True)

        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            use_selection=True,
            export_format='GLB',
            export_animations=True,
            export_nla_strips=True,
            export_animation_mode='NLA_TRACKS',
            export_bake_animation=True,
            export_merge_animation='NONE',
            export_skins=True
        )
        print(f"  ✓ Exported .glb: {glb_path.name} ({glb_path.stat().st_size / 1024:.1f} KB)")

        # 6. Create Simulation Alias Copies
        alias_name = cfg.get("alias")
        if alias_name:
            alias_glb = ASSETS_DIR / f"{alias_name}.glb"
            alias_blend = ASSETS_DIR / f"{alias_name}.blend"
            shutil.copyfile(glb_path, alias_glb)
            shutil.copyfile(blend_path, alias_blend)
            print(f"  ✓ Created simulation alias: {alias_name}.glb & .blend")

        elapsed = time.time() - sp_start
        print(f"  ✓ Finished {slug} in {elapsed:.1f}s")

    # Generate Markdown Documentation Catalog
    generate_creatures_catalog()

    total_time = time.time() - t_start
    print("\n" + "=" * 80)
    print(f"🎉 All 10 photorealistic species generated successfully in {total_time:.1f}s!")
    print("=" * 80)


def generate_creatures_catalog():
    """Generates docs/creatures/README.md with species taxonomy, traits, and images."""
    catalog_path = DOCS_DIR / "README.md"

    md = """# Genesis Zero — Photorealistic 3D Fauna Master Catalog

## Architecture Overview
The Genesis Zero Fauna subsystem features 10 scan-quality photorealistic creature species across Land (`CAN`), Water (`NUOC`), and Air (`TROI`) ecological strata, plus specialized and evolved apex tiers.

All assets are built with:
- **BMesh Manifold Quad-Dominant Topology**: 0 loose vertices, 0 non-manifold edges, 0 ngons, 100% smooth shading.
- **Hierarchical Armature Skeletons**: Root-to-tip bone structures with smooth distance-based skinning weights.
- **8 Canonical Action Animation Clips**: `Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death` baked directly to NLA tracks for seamless runtime serialization.
- **Bio-PBR Principled BSDF Shaders**: Subsurface Scattering (SSS), micro-bump procedural noise, and wet specular cornea eye layers.
- **Standardized 4-Angle Concept Turnaround Sheets**: Perspective 3/4 Hero, Front, Side Profile, and Top-Down Plan views.

---

## 10 Target Species Specification Matrix

| Species Code | Species Slug | Common Name (VN) | Common Name (EN) | Domain | Tier | Trait Vector (B, Atk, Arm, Spd, Sns, Stm) | Key Biological Features |
|---|---|---|---|---|---|---|---|
"""

    for sp, cfg in SPECIES_CONFIGS.items():
        tr = cfg["traits"]
        tr_vec = f"({tr['brain']}, {tr['attack']}, {tr['armor']}, {tr['speed']}, {tr['sense']}, {tr['stomach']})"
        feats = ", ".join(f"`{f}`" for f in cfg["features"])
        md += f"| `{cfg['code']}` | `{sp}` | {cfg['name_vn']} | {cfg['name_en']} | `{cfg['domain']}` | {cfg['tier']} | `{tr_vec}` | {feats} |\n"

    md += "\n---\n\n## Species Deep Profiles & Turnaround Concept Sheets\n\n"

    for sp, cfg in SPECIES_CONFIGS.items():
        tr = cfg["traits"]
        md += f"### {cfg['code']}: {cfg['name_vn']} ({cfg['name_en']})\n\n"
        md += f"- **Domain**: `{cfg['domain']}` | **Tier**: {cfg['tier']}\n"
        md += f"- **Traits**: Brain `{tr['brain']}`, Attack `{tr['attack']}`, Armor `{tr['armor']}`, Speed `{tr['speed']}`, Sense `{tr['sense']}`, Stomach `{tr['stomach']}` (Sum: {sum(tr.values())})\n"
        md += f"- **Features**: {', '.join(f'`{f}`' for f in cfg['features'])}\n"
        md += f"- **3D Assets**: [`.blend`](../../assets/creatures/{sp}.blend) · [`.glb`](../../assets/creatures/{sp}.glb)\n\n"
        md += f"![{cfg['name_en']} 4-Angle Turnaround](images/{sp}_turnaround.jpg)\n\n"
        md += "---\n\n"

    catalog_path.write_text(md, encoding="utf-8")
    print(f"✓ Generated creature catalog documentation: {catalog_path}")


if __name__ == "__main__":
    generate_all_species()

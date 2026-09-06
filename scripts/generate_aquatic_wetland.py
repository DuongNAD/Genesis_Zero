"""
generate_aquatic_wetland.py - Procedural 3D Engine for Aquatic & Wetland Flora
Genesis Zero - Blender 5.2.1 LTS
Builds 9 realistic aquatic and wetland plants with clean BMesh topology & PBR materials.
"""

import math
import os
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
sys.path.insert(0, str(ROOT / "assets" / "flora" / "generators"))

from flora_builder import (
    clean_scene,
    create_pbr_bark_material,
    create_pbr_foliage_material,
    add_curved_tube,
    add_cupped_petal,
    add_channeled_blade,
    add_foliage_clump,
    save_and_export
)

def apply_smooth_and_materials(mesh, materials, mat_idx):
    for p in mesh.polygons:
        p.use_smooth = True
    for mat in materials:
        mesh.materials.append(mat)
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

TARGET_DIR = ROOT / "assets" / "flora" / "aquatic_wetland"

# 1. aquatic_wetland_reed (Phragmites australis)
def build_aquatic_wetland_reed():
    clean_scene()
    mat_culm = create_pbr_foliage_material("M_Reed_Culm", (0.35, 0.48, 0.20, 1.0), sss_weight=0.35, roughness=0.5)
    mat_leaf = create_pbr_foliage_material("M_Reed_Leaf", (0.24, 0.52, 0.16, 1.0), sss_weight=0.45)
    mat_plume = create_pbr_foliage_material("M_Reed_Plume", (0.65, 0.48, 0.45, 1.0), sss_color=(0.8, 0.6, 0.55), sss_weight=0.65, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Wetland_Reed_Mesh")
    verts, faces, mat_idx = [], [], []

    for c_i in range(6):
        ang = c_i * 2.0 * math.pi / 6 + random.uniform(-0.1, 0.1)
        dist = 0.08 + 0.14 * (c_i % 3)
        cx, cy = math.cos(ang)*dist, math.sin(ang)*dist
        h = 2.4 + 0.5 * ((c_i * 2) % 3)

        pts = [
            Vector((cx*0.2, cy*0.2, 0)),
            Vector((cx*0.6 + 0.05, cy*0.6, h*0.45)),
            Vector((cx + 0.15, cy, h*0.85)),
            Vector((cx*1.1 + 0.25, cy*1.1, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.018, 0.014, 0.010, 0.005], rad_segs=4, mat_id=0)

        # Alternating linear leaves streaming in wind
        for lv in range(6):
            t_pos = pts[1].lerp(pts[3], (lv+1)/7.0)
            l_ang = ang + (lv % 2) * 2.4 - 1.2
            fwd = Vector((math.cos(l_ang)*0.6 + 0.4, math.sin(l_ang)*0.6, -0.1)).normalized()
            add_channeled_blade(verts, faces, mat_idx, [t_pos, t_pos + fwd*0.18, t_pos + fwd*0.38], [0.018, 0.038, 0.006], [0.003, 0.007, 0.001], mat_id=1)

        # Feathery purplish plume at tip
        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0.08, 0, 0.08)), 0.10, 0.10, 0.26, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_culm, mat_leaf, mat_plume], mat_idx)
    obj = bpy.data.objects.new("Flora_Wetland_Reed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_wetland_reed.blend"), str(TARGET_DIR / "aquatic_wetland_reed.glb"))
    return obj

# 2. aquatic_hornwort (Ceratophyllum demersum)
def build_aquatic_hornwort():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Hornwort_Stem", (0.16, 0.45, 0.22, 1.0), sss_weight=0.55, roughness=0.3)
    mat_leaf = create_pbr_foliage_material("M_Hornwort_Leaf", (0.12, 0.55, 0.20, 1.0), sss_color=(0.2, 0.7, 0.25), sss_weight=0.70, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Hornwort_Mesh")
    verts, faces, mat_idx = [], [], []

    for st_i, rot_z in enumerate([0.0, 2.1, 4.2]):
        cos_z, sin_z = math.cos(rot_z), math.sin(rot_z)
        stem_pts = [
            Vector((cos_z*0.05, sin_z*0.05, 0.05)),
            Vector((cos_z*0.12, sin_z*0.12, 0.30)),
            Vector((cos_z*0.05 + 0.08, sin_z*0.05, 0.60)),
            Vector((cos_z*0.15, sin_z*0.15 + 0.05, 0.85))
        ]
        add_curved_tube(verts, faces, mat_idx, stem_pts, [0.008, 0.007, 0.006, 0.004], rad_segs=4, mat_id=0)

        # Whorls of fine forked needle leaves (bottlebrush / coontail)
        for w in range(10):
            t_pos = stem_pts[0].lerp(stem_pts[3], (w+1)/11.0)
            for leaf_i in range(6):
                ang = leaf_i * 2.0 * math.pi / 6 + w * 0.4
                fwd = Vector((math.cos(ang), math.sin(ang), 0.15)).normalized()
                l_pts = [t_pos, t_pos + fwd*0.05, t_pos + fwd*0.09]
                add_channeled_blade(verts, faces, mat_idx, l_pts, [0.004, 0.008, 0.002], [0.001, 0.002, 0.0005], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Hornwort", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_hornwort.blend"), str(TARGET_DIR / "aquatic_hornwort.glb"))
    return obj

# 3. aquatic_eelgrass (Vallisneria americana)
def build_aquatic_eelgrass():
    clean_scene()
    mat_root = create_pbr_bark_material("M_Eelgrass_Root", (0.28, 0.25, 0.18, 1.0), roughness=0.85)
    mat_blade = create_pbr_foliage_material("M_Eelgrass_Blade", (0.15, 0.58, 0.22, 1.0), sss_color=(0.25, 0.75, 0.3), sss_weight=0.65, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Eelgrass_Mesh")
    verts, faces, mat_idx = [], [], []

    # Basal root knot
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.03)), 0.06, 0.06, 0.03, lat_steps=3, lon_steps=6, mat_id=0)

    # 12 Long flowing ribbon leaves swaying with current
    for b in range(12):
        ang = b * 2.0 * math.pi / 12 + random.uniform(-0.1, 0.1)
        dx, dy = math.cos(ang), math.sin(ang)
        h = 0.55 + 0.25 * (b % 4) / 3.0
        cur_drift = 0.18 * (b % 3)

        b_pts = [
            Vector((0, 0, 0.03)),
            Vector((dx*0.06 + cur_drift*0.2, dy*0.06, h*0.3)),
            Vector((dx*0.12 + cur_drift*0.6, dy*0.12, h*0.65)),
            Vector((dx*0.18 + cur_drift, dy*0.18, h*0.85)),
            Vector((dx*0.22 + cur_drift*1.2, dy*0.22, h*0.75)) # tip undulating
        ]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.015, 0.032, 0.028, 0.022, 0.006], [0.002, 0.005, 0.004, 0.002, 0.0005], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_root, mat_blade], mat_idx)
    obj = bpy.data.objects.new("Flora_Eelgrass", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_eelgrass.blend"), str(TARGET_DIR / "aquatic_eelgrass.glb"))
    return obj

# 4. aquatic_umbrella_papyrus (Cyperus alternifolius)
def build_aquatic_umbrella_papyrus():
    clean_scene()
    mat_culm = create_pbr_foliage_material("M_Papyrus_Culm", (0.22, 0.52, 0.16, 1.0), sss_weight=0.35, roughness=0.45)
    mat_bract = create_pbr_foliage_material("M_Papyrus_Bract", (0.18, 0.60, 0.14, 1.0), sss_weight=0.55, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Umbrella_Papyrus_Mesh")
    verts, faces, mat_idx = [], [], []

    for c_i in range(5):
        ang = c_i * 2.0 * math.pi / 5 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        h = 1.15 + 0.25 * (c_i % 3)
        pts = [
            Vector((dx*0.05, dy*0.05, 0)),
            Vector((dx*0.12, dy*0.12, h*0.5)),
            Vector((dx*0.18, dy*0.18, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.014, 0.011, 0.007], rad_segs=3, mat_id=0) # 3-angled stem

        # Radiating umbrella of 18 narrow drooping bracts at summit
        tip = pts[-1]
        for b_i in range(18):
            u_ang = b_i * 2.0 * math.pi / 18
            fwd = Vector((math.cos(u_ang), math.sin(u_ang), -0.25)).normalized()
            b_pts = [tip, tip + fwd*0.12, tip + fwd*0.25]
            add_channeled_blade(verts, faces, mat_idx, b_pts, [0.01, 0.018, 0.004], [0.001, 0.003, 0.0005], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_culm, mat_bract], mat_idx)
    obj = bpy.data.objects.new("Flora_Umbrella_Papyrus", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_umbrella_papyrus.blend"), str(TARGET_DIR / "aquatic_umbrella_papyrus.glb"))
    return obj

# 5. aquatic_water_hyacinth (Eichhornia crassipes)
def build_aquatic_water_hyacinth():
    clean_scene()
    mat_bulb = create_pbr_foliage_material("M_Hyacinth_Bulb", (0.28, 0.62, 0.22, 1.0), sss_weight=0.55, roughness=0.35)
    mat_flower = create_pbr_foliage_material("M_Hyacinth_Flower", (0.55, 0.35, 0.85, 1.0), sss_color=(0.7, 0.45, 0.95), sss_weight=0.65, roughness=0.28)
    mat_root = create_pbr_foliage_material("M_Hyacinth_Root", (0.12, 0.08, 0.16, 1.0), roughness=0.85)

    mesh = bpy.data.meshes.new("Flora_Water_Hyacinth_Mesh")
    verts, faces, mat_idx = [], [], []

    # Feathery dark root beard below water
    for r in range(6):
        r_ang = r * 2.0 * math.pi / 6
        rx, ry = math.cos(r_ang)*0.03, math.sin(r_ang)*0.03
        r_pts = [Vector((rx, ry, 0)), Vector((rx*1.5, ry*1.5, -0.08)), Vector((rx*2.0, ry*2.0, -0.16))]
        add_curved_tube(verts, faces, mat_idx, r_pts, [0.006, 0.004, 0.002], rad_segs=3, mat_id=2)

    # 6 Bulbous swollen spongy petioles
    for p_i in range(6):
        ang = p_i * 2.0 * math.pi / 6
        dx, dy = math.cos(ang), math.sin(ang)
        p_center = Vector((dx*0.08, dy*0.08, 0.08))
        # Spongy inflated bulb
        add_foliage_clump(verts, faces, mat_idx, p_center, 0.045, 0.045, 0.07, lat_steps=4, lon_steps=8, mat_id=0)
        # Rounded spoon leaf atop bulb
        fwd = Vector((dx, dy, 0.2)).normalized()
        add_cupped_petal(verts, faces, mat_idx, p_center + Vector((0, 0, 0.06)), fwd, Vector((0, 0, 1)), length=0.10, width=0.085, cup_depth=0.012, mat_id=0)

    # Central violet flower spike
    spike_pts = [Vector((0, 0, 0.04)), Vector((0, 0, 0.18)), Vector((0, 0, 0.32))]
    add_curved_tube(verts, faces, mat_idx, spike_pts, [0.010, 0.008, 0.005], rad_segs=4, mat_id=0)
    for fl_i in range(4):
        fl_z = 0.16 + fl_i * 0.045
        fl_ang = fl_i * 1.6
        fl_fwd = Vector((math.cos(fl_ang), math.sin(fl_ang), 0.2)).normalized()
        add_cupped_petal(verts, faces, mat_idx, Vector((0, 0, fl_z)), fl_fwd, Vector((0, 0, 1)), length=0.065, width=0.045, cup_depth=0.006, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bulb, mat_flower, mat_root], mat_idx)
    obj = bpy.data.objects.new("Flora_Water_Hyacinth", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_water_hyacinth.blend"), str(TARGET_DIR / "aquatic_water_hyacinth.glb"))
    return obj

# 6. aquatic_red_azolla (Azolla caroliniana)
def build_aquatic_red_azolla():
    clean_scene()
    mat_red = create_pbr_foliage_material("M_Azolla_Red", (0.75, 0.16, 0.14, 1.0), sss_color=(0.95, 0.25, 0.2), sss_weight=0.65, roughness=0.45)
    mat_green = create_pbr_foliage_material("M_Azolla_Green", (0.25, 0.55, 0.18, 1.0), sss_weight=0.45)

    mesh = bpy.data.meshes.new("Flora_Red_Azolla_Mesh")
    verts, faces, mat_idx = [], [], []

    # Patchwork floating mat of tiny overlapping scale fronds
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.015)), 0.35, 0.30, 0.03, lat_steps=4, lon_steps=10, bump_amp=0.25, mat_id=0)

    # Secondary overlapping lobes
    for l_i, (lx, ly, rx, ry) in enumerate([(0.12, 0.08, 0.16, 0.14), (-0.14, 0.06, 0.18, 0.15), (0.05, -0.12, 0.15, 0.13), (-0.08, -0.10, 0.14, 0.12)]):
        m_id = 0 if l_i % 2 == 0 else 1
        add_foliage_clump(verts, faces, mat_idx, Vector((lx, ly, 0.025)), rx, ry, 0.02, lat_steps=3, lon_steps=8, bump_amp=0.20, mat_id=m_id)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_red, mat_green], mat_idx)
    obj = bpy.data.objects.new("Flora_Red_Azolla", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_red_azolla.blend"), str(TARGET_DIR / "aquatic_red_azolla.glb"))
    return obj

# 7. aquatic_victoria_lily (Victoria amazonica)
def build_aquatic_victoria_lily():
    clean_scene()
    mat_pad = create_pbr_foliage_material("M_Victoria_Pad", (0.16, 0.48, 0.15, 1.0), sss_weight=0.45, roughness=0.35)
    mat_rim = create_pbr_foliage_material("M_Victoria_Rim", (0.55, 0.20, 0.24, 1.0), sss_weight=0.50, roughness=0.40)
    mat_flower = create_pbr_foliage_material("M_Victoria_Flower", (0.95, 0.90, 0.92, 1.0), sss_color=(0.98, 0.75, 0.85), sss_weight=0.70, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Victoria_Lily_Mesh")
    verts, faces, mat_idx = [], [], []

    # Giant circular floating pad with 8cm upturned vertical rim
    r_pad = 0.90
    r_rim_h = 0.08
    rad_segs = 24
    base = len(verts)

    # Center bottom
    verts.append((0, 0, 0))
    # Outer disc ring
    for i in range(rad_segs):
        ang = i * 2.0 * math.pi / rad_segs
        verts.append((r_pad * math.cos(ang), r_pad * math.sin(ang), 0.01))

    for i in range(rad_segs):
        nxt = (i + 1) % rad_segs
        faces.append((base, base + 1 + i, base + 1 + nxt))
        mat_idx.append(0)

    # Upturned vertical rim
    rim_base = len(verts)
    for i in range(rad_segs):
        ang = i * 2.0 * math.pi / rad_segs
        verts.append((r_pad * math.cos(ang), r_pad * math.sin(ang), 0.01 + r_rim_h))

    for i in range(rad_segs):
        nxt = (i + 1) % rad_segs
        v1 = base + 1 + i
        v2 = base + 1 + nxt
        v3 = rim_base + nxt
        v4 = rim_base + i
        faces.append((v2, v1, v4, v3))
        mat_idx.append(1)

    # Large fragrant multi-layered nocturnal blossom
    flw_center = Vector((0.35, -0.25, 0.08))
    add_foliage_clump(verts, faces, mat_idx, flw_center + Vector((0, 0, 0.04)), 0.06, 0.06, 0.05, lat_steps=3, lon_steps=8, mat_id=2)
    for row, p_len, p_w in [(0, 0.12, 0.05), (1, 0.10, 0.045), (2, 0.08, 0.04)]:
        for p in range(12):
            p_ang = (p + row*0.5) * 2.0 * math.pi / 12
            fwd = Vector((math.cos(p_ang), math.sin(p_ang), 0.35 + row*0.15)).normalized()
            add_cupped_petal(verts, faces, mat_idx, flw_center, fwd, Vector((0, 0, 1)), length=p_len, width=p_w, cup_depth=0.01, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_pad, mat_rim, mat_flower], mat_idx)
    obj = bpy.data.objects.new("Flora_Victoria_Lily", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_victoria_lily.blend"), str(TARGET_DIR / "aquatic_victoria_lily.glb"))
    return obj

# 8. aquatic_elodea (Elodea canadensis)
def build_aquatic_elodea():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Elodea_Stem", (0.18, 0.52, 0.22, 1.0), sss_weight=0.60, roughness=0.3)
    mat_leaf = create_pbr_foliage_material("M_Elodea_Leaf", (0.14, 0.60, 0.18, 1.0), sss_color=(0.2, 0.8, 0.25), sss_weight=0.72, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Elodea_Mesh")
    verts, faces, mat_idx = [], [], []

    for s_i in range(3):
        ang = s_i * 2.0 * math.pi / 3 + 0.3
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((dx*0.04, dy*0.04, 0.04)),
            Vector((dx*0.10 + 0.04, dy*0.10, 0.25)),
            Vector((dx*0.14 - 0.03, dy*0.14, 0.50)),
            Vector((dx*0.18, dy*0.18 + 0.04, 0.72))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.007, 0.006, 0.005, 0.003], rad_segs=4, mat_id=0)

        # Whorls of 3 small ovate leaves
        for w in range(12):
            t_pos = pts[0].lerp(pts[3], (w+1)/13.0)
            for l_idx in range(3):
                l_ang = l_idx * 2.0 * math.pi / 3 + w * 0.5
                fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.1)).normalized()
                add_cupped_petal(verts, faces, mat_idx, t_pos, fwd, Vector((0, 0, 1)), length=0.045, width=0.022, cup_depth=0.002, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Elodea", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_elodea.blend"), str(TARGET_DIR / "aquatic_elodea.glb"))
    return obj

# 9. aquatic_mangrove (Rhizophora mangle)
def build_aquatic_mangrove():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Mangrove_Bark", (0.32, 0.18, 0.12, 1.0), roughness=0.75)
    mat_leaf = create_pbr_foliage_material("M_Mangrove_Leaf", (0.12, 0.42, 0.14, 1.0), sss_weight=0.35, roughness=0.3)
    mat_pod = create_pbr_foliage_material("M_Mangrove_Propagule", (0.35, 0.40, 0.18, 1.0), sss_weight=0.40, roughness=0.5)

    mesh = bpy.data.meshes.new("Flora_Mangrove_Mesh")
    verts, faces, mat_idx = [], [], []

    # Elevated trunk starting at z=1.2m
    trunk_pts = [
        Vector((0, 0, 1.2)),
        Vector((0.08, -0.05, 1.9)),
        Vector((0.02, 0.06, 2.6)),
        Vector((0.10, 0.08, 3.2))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.085, 0.070, 0.055, 0.040], rad_segs=6, mat_id=0)

    # 8 Arching stilt / prop roots looping out into the water
    for r_i in range(8):
        ang = r_i * 2.0 * math.pi / 8 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        r_reach = 0.85 + 0.25 * (r_i % 3)
        root_pts = [
            Vector((0, 0, 1.2)),
            Vector((dx*r_reach*0.6, dy*r_reach*0.6, 1.45)), # arched up
            Vector((dx*r_reach*0.9, dy*r_reach*0.9, 0.65)),
            Vector((dx*r_reach, dy*r_reach, 0.0)) # anchoring into mud
        ]
        add_curved_tube(verts, faces, mat_idx, root_pts, [0.040, 0.032, 0.024, 0.016], rad_segs=5, mat_id=0)

    # Branches and foliage canopy
    b_center = trunk_pts[-1]
    for b_i in range(4):
        b_ang = b_i * 2.0 * math.pi / 4 + 0.4
        bx, by = math.cos(b_ang)*0.6, math.sin(b_ang)*0.6
        b_pts = [b_center, b_center + Vector((bx*0.5, by*0.5, 0.3)), b_center + Vector((bx, by, 0.5))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.035, 0.025, 0.015], rad_segs=4, mat_id=0)

        # Foliage clumps
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.15)), 0.45, 0.45, 0.35, lat_steps=4, lon_steps=8, mat_id=1)

        # Hanging pencil-like propagules
        p_tip = b_pts[-1]
        prop_pts = [p_tip, p_tip + Vector((0.04, 0, -0.15)), p_tip + Vector((0.05, 0, -0.30))]
        add_curved_tube(verts, faces, mat_idx, prop_pts, [0.010, 0.012, 0.006], rad_segs=4, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_pod], mat_idx)
    obj = bpy.data.objects.new("Flora_Mangrove", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "aquatic_mangrove.blend"), str(TARGET_DIR / "aquatic_mangrove.glb"))
    return obj

def main():
    print(">>> Generating 9 Aquatic & Wetland Flora...")
    builders = [
        ("aquatic_wetland_reed", build_aquatic_wetland_reed),
        ("aquatic_hornwort", build_aquatic_hornwort),
        ("aquatic_eelgrass", build_aquatic_eelgrass),
        ("aquatic_umbrella_papyrus", build_aquatic_umbrella_papyrus),
        ("aquatic_water_hyacinth", build_aquatic_water_hyacinth),
        ("aquatic_red_azolla", build_aquatic_red_azolla),
        ("aquatic_victoria_lily", build_aquatic_victoria_lily),
        ("aquatic_elodea", build_aquatic_elodea),
        ("aquatic_mangrove", build_aquatic_mangrove)
    ]
    for slug, fn in builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ All 9 Aquatic & Wetland Flora generated successfully!")

if __name__ == "__main__":
    main()

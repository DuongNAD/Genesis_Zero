"""
generate_arid_succulents.py - Procedural 3D Engine for Arid & Succulent Flora
Genesis Zero - Blender 5.2.1 LTS
Builds 10 realistic desert succulents with clean BMesh topology & PBR materials.
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

TARGET_DIR = ROOT / "assets" / "flora" / "arid_succulents"

# 1. succulent_cape_aloe (Aloe ferox)
def build_succulent_cape_aloe():
    clean_scene()
    mat_trunk = create_pbr_bark_material("M_Aloe_Trunk", (0.35, 0.28, 0.20, 1.0), roughness=0.9)
    mat_leaf = create_pbr_foliage_material("M_Aloe_Leaf", (0.12, 0.42, 0.38, 1.0), sss_color=(0.18, 0.6, 0.5), sss_weight=0.50, roughness=0.35)
    mat_flower = create_pbr_foliage_material("M_Aloe_Flower", (0.92, 0.35, 0.08, 1.0), sss_color=(0.98, 0.5, 0.1), sss_weight=0.65, roughness=0.4)

    mesh = bpy.data.meshes.new("Flora_Cape_Aloe_Mesh")
    verts, faces, mat_idx = [], [], []

    # Woody trunk with dried skirt base
    trunk_pts = [Vector((0, 0, 0)), Vector((0.02, 0.01, 0.6)), Vector((0, 0, 1.2))]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.09, 0.08, 0.07], rad_segs=6, mat_id=0)

    # Dried skirt leaves hanging down
    for s_i in range(8):
        s_ang = s_i * 2.0 * math.pi / 8
        fwd = Vector((math.cos(s_ang), math.sin(s_ang), -0.8)).normalized()
        add_cupped_petal(verts, faces, mat_idx, Vector((0, 0, 1.0)), fwd, Vector((0, 0, 1)), length=0.35, width=0.08, cup_depth=0.01, mat_id=0)

    # Apical rosette of 16 thick glaucous leaves with prickles
    apex = trunk_pts[-1]
    for lv in range(16):
        ang = lv * (math.pi * (3.0 - math.sqrt(5.0))) # Golden ratio
        z_up = (lv / 16.0) * 0.15
        pitch = 0.35 - (lv / 16.0) * 0.45
        fwd = Vector((math.cos(ang), math.sin(ang), pitch)).normalized()
        l_pts = [apex + Vector((0, 0, z_up)), apex + fwd*0.25 + Vector((0, 0, z_up+0.05)), apex + fwd*0.55 + Vector((0, 0, z_up))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.06, 0.10, 0.015], [0.012, 0.022, 0.003], mat_id=1)

    # Candelabra 3-pronged orange-red flower spike
    sp_st = apex + Vector((0, 0, 0.12))
    for f_i, (fx, fy) in enumerate([(0, 0), (0.15, 0.10), (-0.14, 0.12)]):
        fl_pts = [sp_st, sp_st + Vector((fx*0.5, fy*0.5, 0.3)), sp_st + Vector((fx, fy, 0.85))]
        add_curved_tube(verts, faces, mat_idx, fl_pts, [0.015, 0.012, 0.006], rad_segs=4, mat_id=0)
        # Dense cylindrical flower raceme
        add_foliage_clump(verts, faces, mat_idx, fl_pts[-1] + Vector((0, 0, 0.08)), 0.065, 0.065, 0.22, lat_steps=4, lon_steps=8, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_trunk, mat_leaf, mat_flower], mat_idx)
    obj = bpy.data.objects.new("Flora_Cape_Aloe", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_cape_aloe.blend"), str(TARGET_DIR / "succulent_cape_aloe.glb"))
    return obj

# 2. succulent_prickly_pear (Opuntia microdasys)
def build_succulent_prickly_pear():
    clean_scene()
    mat_pad = create_pbr_foliage_material("M_Opuntia_Pad", (0.18, 0.58, 0.22, 1.0), sss_color=(0.3, 0.75, 0.3), sss_weight=0.50, roughness=0.4)
    mat_flw = create_pbr_foliage_material("M_Opuntia_Flower", (0.96, 0.82, 0.06, 1.0), sss_color=(0.98, 0.9, 0.2), sss_weight=0.65, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Prickly_Pear_Mesh")
    verts, faces, mat_idx = [], [], []

    # Stacked chain of 9 oval flattened pads (ears)
    pad_configs = [
        # (center, rx, ry, rz)
        (Vector((0, 0, 0.16)), 0.14, 0.045, 0.16), # Base
        (Vector((0.10, 0.02, 0.42)), 0.15, 0.042, 0.17),
        (Vector((-0.12, -0.02, 0.40)), 0.14, 0.040, 0.16),
        (Vector((0.22, 0.04, 0.68)), 0.13, 0.038, 0.15),
        (Vector((0.02, 0.01, 0.70)), 0.14, 0.038, 0.15),
        (Vector((-0.20, -0.04, 0.66)), 0.13, 0.038, 0.15),
        (Vector((0.14, 0.02, 0.94)), 0.12, 0.035, 0.14),
        (Vector((-0.10, -0.02, 0.92)), 0.12, 0.035, 0.14),
        (Vector((0.02, 0.00, 1.15)), 0.11, 0.032, 0.13), # Summit
    ]

    for p_c, rx, ry, rz in pad_configs:
        add_foliage_clump(verts, faces, mat_idx, p_c, rx, ry, rz, lat_steps=4, lon_steps=8, bump_freq=4.0, bump_amp=0.15, mat_id=0)

    # 3 Golden cup flowers atop upper pads
    for fl_pos in [Vector((0.14, 0.02, 1.08)), Vector((-0.10, -0.02, 1.06)), Vector((0.02, 0.00, 1.28))]:
        add_foliage_clump(verts, faces, mat_idx, fl_pos, 0.045, 0.045, 0.035, lat_steps=3, lon_steps=8, mat_id=1)
        for p in range(8):
            ang = p * 2.0 * math.pi / 8
            fwd = Vector((math.cos(ang), math.sin(ang), 0.4)).normalized()
            add_cupped_petal(verts, faces, mat_idx, fl_pos, fwd, Vector((0, 0, 1)), length=0.05, width=0.035, cup_depth=0.006, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_pad, mat_flw], mat_idx)
    obj = bpy.data.objects.new("Flora_Prickly_Pear", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_prickly_pear.blend"), str(TARGET_DIR / "succulent_prickly_pear.glb"))
    return obj

# 3. succulent_tumbleweed (Kali tragus)
def build_succulent_tumbleweed():
    clean_scene()
    mat_wood = create_pbr_bark_material("M_Tumbleweed_Straw", (0.75, 0.58, 0.32, 1.0), roughness=0.92, bump_strength=0.2)

    mesh = bpy.data.meshes.new("Flora_Tumbleweed_Mesh")
    verts, faces, mat_idx = [], [], []

    # Spherical lattice of 16 tangled interlocking branches
    center = Vector((0, 0, 0.45))
    radius = 0.42

    for b in range(16):
        phi = math.acos(-1.0 + 2.0 * b / 16.0)
        theta = math.sqrt(16.0 * math.pi) * phi
        dx = math.sin(phi) * math.cos(theta)
        dy = math.sin(phi) * math.sin(theta)
        dz = math.cos(phi)

        p0 = center
        p1 = center + Vector((dx*0.35, dy*0.35, dz*0.35))
        p2 = center + Vector((dx*0.7 + dy*0.2, dy*0.7 - dx*0.2, dz*0.7)) * radius
        p3 = center + Vector((dx, dy, dz)) * radius

        add_curved_tube(verts, faces, mat_idx, [p0, p1, p2, p3], [0.010, 0.008, 0.006, 0.003], rad_segs=3, mat_id=0)

        # Minor thorny twigs
        t_tip = p3
        add_curved_tube(verts, faces, mat_idx, [t_tip, t_tip + Vector((dy*0.08, -dx*0.08, 0.05))], [0.003, 0.001], rad_segs=3, mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_wood], mat_idx)
    obj = bpy.data.objects.new("Flora_Tumbleweed", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_tumbleweed.blend"), str(TARGET_DIR / "succulent_tumbleweed.glb"))
    return obj

# 4. succulent_desert_rose (Adenium obesum)
def build_succulent_desert_rose():
    clean_scene()
    mat_caudex = create_pbr_bark_material("M_Adenium_Caudex", (0.42, 0.40, 0.35, 1.0), roughness=0.45)
    mat_leaf = create_pbr_foliage_material("M_Adenium_Leaf", (0.12, 0.44, 0.16, 1.0), sss_weight=0.35, roughness=0.3)
    mat_flower = create_pbr_foliage_material("M_Adenium_Bloom", (0.92, 0.18, 0.38, 1.0), sss_color=(0.98, 0.3, 0.5), sss_weight=0.68, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Desert_Rose_Mesh")
    verts, faces, mat_idx = [], [], []

    # Massive swollen pachycaul caudex base
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.28)), 0.28, 0.26, 0.28, lat_steps=5, lon_steps=10, bump_amp=0.25, mat_id=0)

    # 4 Short thick branches emerging from caudex
    for b_i, (bx, by, bz) in enumerate([(0.14, 0.12, 0.85), (-0.16, 0.10, 0.80), (0.10, -0.15, 0.88), (-0.12, -0.14, 0.78)]):
        b_pts = [Vector((bx*0.4, by*0.4, 0.45)), Vector((bx*0.8, by*0.8, 0.65)), Vector((bx, by, bz))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.055, 0.038, 0.024], rad_segs=5, mat_id=0)

        # Glossy spiraled leaves
        tip = b_pts[-1]
        for lv in range(6):
            ang = lv * 2.0 * math.pi / 6 + b_i
            fwd = Vector((math.cos(ang), math.sin(ang), 0.2)).normalized()
            add_cupped_petal(verts, faces, mat_idx, tip, fwd, Vector((0, 0, 1)), length=0.10, width=0.045, cup_depth=0.005, mat_id=1)

        # Trumpet blossoms with crimson pink margins
        for fl in range(2):
            fl_ang = fl * math.pi + b_i
            fl_fwd = Vector((math.cos(fl_ang)*0.4, math.sin(fl_ang)*0.4, 0.8)).normalized()
            # Flared trumpet
            add_curved_tube(verts, faces, mat_idx, [tip, tip + fl_fwd*0.05], [0.012, 0.035], rad_segs=5, mat_id=2, cap_start=True, cap_end=False)
            # 5 Flared petal lobes
            for p in range(5):
                p_ang = p * 2.0 * math.pi / 5 + fl_ang
                p_dir = Vector((math.cos(p_ang), math.sin(p_ang), 0.3)).normalized()
                add_cupped_petal(verts, faces, mat_idx, tip + fl_fwd*0.05, p_dir, Vector((0, 0, 1)), length=0.055, width=0.04, cup_depth=0.006, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_caudex, mat_leaf, mat_flower], mat_idx)
    obj = bpy.data.objects.new("Flora_Desert_Rose", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_desert_rose.blend"), str(TARGET_DIR / "succulent_desert_rose.glb"))
    return obj

# 5. succulent_burros_tail (Sedum morganianum)
def build_succulent_burros_tail():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Sedum_Stem", (0.25, 0.45, 0.32, 1.0), sss_weight=0.35)
    mat_bead = create_pbr_foliage_material("M_Sedum_Bead", (0.35, 0.72, 0.65, 1.0), sss_color=(0.45, 0.85, 0.75), sss_weight=0.65, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Burros_Tail_Mesh")
    verts, faces, mat_idx = [], [], []

    # 6 Long cascading trailing ropes hanging down
    for r_i in range(6):
        ang = r_i * 2.0 * math.pi / 6
        dx, dy = math.cos(ang)*0.10, math.sin(ang)*0.10
        rope_pts = [
            Vector((dx*0.2, dy*0.2, 0.65)),
            Vector((dx*0.8, dy*0.8, 0.55)),
            Vector((dx*1.2, dy*1.2, 0.35)),
            Vector((dx*1.1, dy*1.1, 0.12)),
            Vector((dx*1.0, dy*1.0, 0.02))
        ]
        add_curved_tube(verts, faces, mat_idx, rope_pts, [0.008, 0.007, 0.006, 0.005, 0.004], rad_segs=3, mat_id=0)

        # Packed overlapping plump jelly-bean leaves
        for b in range(16):
            t = (b + 1) / 18.0
            pos = rope_pts[0].lerp(rope_pts[-1], t)
            b_ang = b * 2.4
            b_dx, b_dy = math.cos(b_ang)*0.022, math.sin(b_ang)*0.022
            add_foliage_clump(verts, faces, mat_idx, pos + Vector((b_dx, b_dy, 0)), 0.024, 0.024, 0.028, lat_steps=3, lon_steps=6, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_bead], mat_idx)
    obj = bpy.data.objects.new("Flora_Burros_Tail", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_burros_tail.blend"), str(TARGET_DIR / "succulent_burros_tail.glb"))
    return obj

# 6. succulent_living_stones (Lithops dorotheae)
def build_succulent_living_stones():
    clean_scene()
    mat_stone = create_pbr_foliage_material("M_Lithops_Body", (0.45, 0.40, 0.35, 1.0), sss_weight=0.35, roughness=0.65)
    mat_flw = create_pbr_foliage_material("M_Lithops_Flower", (0.98, 0.82, 0.08, 1.0), sss_weight=0.65, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Living_Stones_Mesh")
    verts, faces, mat_idx = [], [], []

    # Two paired fleshy stone lobes with cleft in center
    for side in [-1, 1]:
        lobe_center = Vector((side * 0.028, 0, 0.035))
        add_foliage_clump(verts, faces, mat_idx, lobe_center, 0.032, 0.042, 0.035, lat_steps=4, lon_steps=8, bump_amp=0.15, mat_id=0)

    # Golden daisy-like flower emerging directly from cleft
    fl_center = Vector((0, 0, 0.075))
    add_foliage_clump(verts, faces, mat_idx, fl_center, 0.015, 0.015, 0.010, lat_steps=3, lon_steps=6, mat_id=1)
    for p in range(16):
        ang = p * 2.0 * math.pi / 16
        fwd = Vector((math.cos(ang), math.sin(ang), 0.1)).normalized()
        add_cupped_petal(verts, faces, mat_idx, fl_center, fwd, Vector((0, 0, 1)), length=0.038, width=0.010, cup_depth=0.002, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stone, mat_flw], mat_idx)
    obj = bpy.data.objects.new("Flora_Living_Stones", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_living_stones.blend"), str(TARGET_DIR / "succulent_living_stones.glb"))
    return obj

# 7. succulent_golden_barrel (Echinocactus grusonii)
def build_succulent_golden_barrel():
    clean_scene()
    mat_body = create_pbr_foliage_material("M_Barrel_Body", (0.16, 0.58, 0.18, 1.0), sss_weight=0.38, roughness=0.4)
    mat_spines = create_pbr_foliage_material("M_Barrel_Spine", (0.95, 0.78, 0.12, 1.0), sss_weight=0.55, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Golden_Barrel_Mesh")
    verts, faces, mat_idx = [], [], []

    # Fluted ribbed sphere with 20 ribs
    center = Vector((0, 0, 0.45))
    r_body = 0.42
    slices = 16
    radial = 40
    base = len(verts)

    # South pole
    verts.append((center.x, center.y, center.z - r_body))
    ring_start = len(verts)

    for s in range(1, slices - 1):
        phi = math.pi * s / (slices - 1.0)
        z_o = -r_body * math.cos(phi)
        r_xy = r_body * math.sin(phi)
        for r in range(radial):
            ang = r * 2.0 * math.pi / radial
            rib = 0.035 * math.cos(ang * 20.0) # 20 deep accordion ribs
            r_eff = max(0.05, r_xy + rib)
            verts.append((center.x + r_eff * math.cos(ang), center.y + r_eff * math.sin(ang), center.z + z_o))

    v_bot = base
    for r in range(radial):
        nxt = (r + 1) % radial
        faces.append((v_bot, ring_start + nxt, ring_start + r))
        mat_idx.append(0)

    rings_cnt = slices - 2
    for s in range(rings_cnt - 1):
        r1 = ring_start + s * radial
        r2 = ring_start + (s + 1) * radial
        for r in range(radial):
            nxt = (r + 1) % radial
            faces.append((r1 + r, r1 + nxt, r2 + nxt, r2 + r))
            mat_idx.append(0)

    v_top = len(verts)
    verts.append((center.x, center.y, center.z + r_body))
    last_ring = ring_start + (rings_cnt - 1) * radial
    for r in range(radial):
        nxt = (r + 1) % radial
        faces.append((v_top, last_ring + r, last_ring + nxt))
        mat_idx.append(0)

    # Golden woolly crown cushion on top
    add_foliage_clump(verts, faces, mat_idx, center + Vector((0, 0, r_body - 0.02)), 0.16, 0.16, 0.06, lat_steps=3, lon_steps=8, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_body, mat_spines], mat_idx)
    obj = bpy.data.objects.new("Flora_Golden_Barrel", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_golden_barrel.blend"), str(TARGET_DIR / "succulent_golden_barrel.glb"))
    return obj

# 8. succulent_joshua_tree (Yucca brevifolia)
def build_succulent_joshua_tree():
    clean_scene()
    mat_trunk = create_pbr_bark_material("M_Joshua_Trunk", (0.32, 0.28, 0.22, 1.0), roughness=0.95)
    mat_foliage = create_pbr_foliage_material("M_Joshua_Blade", (0.15, 0.42, 0.18, 1.0), sss_weight=0.35, roughness=0.45)

    mesh = bpy.data.meshes.new("Flora_Joshua_Tree_Mesh")
    verts, faces, mat_idx = [], [], []

    # Angular zig-zagging trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.08, -0.05, 1.2)),
        Vector((0.02, 0.08, 2.1)),
        Vector((0.15, 0.12, 2.7))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.12, 0.09, 0.07, 0.055], rad_segs=5, mat_id=0)

    # 4 Angular crooked branches
    b_st = trunk_pts[-1]
    for b_i, (bx, by, bz) in enumerate([(0.7, 0.4, 0.6), (-0.6, 0.5, 0.7), (0.5, -0.6, 0.5), (-0.4, -0.5, 0.8)]):
        elbow = b_st + Vector((bx*0.5, by*0.5, bz*0.3))
        tip = b_st + Vector((bx, by, bz))
        add_curved_tube(verts, faces, mat_idx, [b_st, elbow, tip], [0.050, 0.038, 0.025], rad_segs=4, mat_id=0)

        # Dense spherical pom-pom of stiff bayonet blades at each tip
        for bl in range(24):
            phi = math.acos(-1.0 + 2.0 * bl / 24.0)
            theta = math.sqrt(24.0 * math.pi) * phi
            fwd = Vector((math.sin(phi)*math.cos(theta), math.sin(phi)*math.sin(theta), math.cos(phi))).normalized()
            add_channeled_blade(verts, faces, mat_idx, [tip, tip + fwd*0.14, tip + fwd*0.30], [0.02, 0.035, 0.005], [0.004, 0.008, 0.001], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_trunk, mat_foliage], mat_idx)
    obj = bpy.data.objects.new("Flora_Joshua_Tree", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_joshua_tree.blend"), str(TARGET_DIR / "succulent_joshua_tree.glb"))
    return obj

# 9. succulent_bottle_tree (Pachypodium geayi)
def build_succulent_bottle_tree():
    clean_scene()
    mat_trunk = create_pbr_bark_material("M_Bottle_Trunk", (0.52, 0.54, 0.55, 1.0), roughness=0.45)
    mat_leaves = create_pbr_foliage_material("M_Bottle_Leaves", (0.16, 0.52, 0.20, 1.0), sss_weight=0.45)

    mesh = bpy.data.meshes.new("Flora_Bottle_Tree_Mesh")
    verts, faces, mat_idx = [], [], []

    # Tapering bottle trunk
    pts = [
        Vector((0, 0, 0)),
        Vector((0.02, -0.02, 0.8)), # Swollen belly
        Vector((0.01, 0.01, 2.0)),
        Vector((0.00, 0.00, 3.2)) # Narrow neck
    ]
    add_curved_tube(verts, faces, mat_idx, pts, [0.22, 0.28, 0.16, 0.08], rad_segs=8, mat_id=0)

    # Crown of narrow linear leaves at apex
    apex = pts[-1]
    for lv in range(18):
        ang = lv * 2.0 * math.pi / 18
        fwd = Vector((math.cos(ang), math.sin(ang), 0.3)).normalized()
        add_channeled_blade(verts, faces, mat_idx, [apex, apex + fwd*0.18, apex + fwd*0.42], [0.02, 0.038, 0.005], [0.003, 0.007, 0.001], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_trunk, mat_leaves], mat_idx)
    obj = bpy.data.objects.new("Flora_Bottle_Tree", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_bottle_tree.blend"), str(TARGET_DIR / "succulent_bottle_tree.glb"))
    return obj

# 10. succulent_ghost_echeveria (Echeveria elegans)
def build_succulent_ghost_echeveria():
    clean_scene()
    mat_leaf = create_pbr_foliage_material("M_Echeveria_Leaf", (0.42, 0.75, 0.72, 1.0), sss_color=(0.95, 0.65, 0.75), sss_weight=0.68, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Ghost_Echeveria_Mesh")
    verts, faces, mat_idx = [], [], []

    # Tight geometric Fibonacci rosette of spoon leaves
    center = Vector((0, 0, 0.02))
    n_leaves = 24
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))

    for i in range(n_leaves):
        ang = i * golden_angle
        r_dist = 0.02 + 0.06 * math.sqrt(i / n_leaves)
        z_pos = 0.01 + 0.05 * (1.0 - i / n_leaves)
        p_base = center + Vector((math.cos(ang)*r_dist, math.sin(ang)*r_dist, z_pos))

        pitch = 0.2 + 0.4 * (1.0 - i / n_leaves)
        fwd = Vector((math.cos(ang), math.sin(ang), pitch)).normalized()
        up = Vector((0, 0, 1))
        p_len = 0.05 + 0.05 * (i / n_leaves)
        p_w = 0.035 + 0.025 * (i / n_leaves)
        add_cupped_petal(verts, faces, mat_idx, p_base, fwd, up, length=p_len, width=p_w, cup_depth=0.008, mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Ghost_Echeveria", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "succulent_ghost_echeveria.blend"), str(TARGET_DIR / "succulent_ghost_echeveria.glb"))
    return obj

def main():
    print(">>> Generating 10 Arid & Succulent Flora...")
    builders = [
        ("succulent_cape_aloe", build_succulent_cape_aloe),
        ("succulent_prickly_pear", build_succulent_prickly_pear),
        ("succulent_tumbleweed", build_succulent_tumbleweed),
        ("succulent_desert_rose", build_succulent_desert_rose),
        ("succulent_burros_tail", build_succulent_burros_tail),
        ("succulent_living_stones", build_succulent_living_stones),
        ("succulent_golden_barrel", build_succulent_golden_barrel),
        ("succulent_joshua_tree", build_succulent_joshua_tree),
        ("succulent_bottle_tree", build_succulent_bottle_tree),
        ("succulent_ghost_echeveria", build_succulent_ghost_echeveria)
    ]
    for slug, fn in builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ All 10 Arid & Succulent Flora generated successfully!")

if __name__ == "__main__":
    main()

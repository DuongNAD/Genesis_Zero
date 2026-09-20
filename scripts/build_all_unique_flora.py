"""
build_all_unique_flora.py - Procedural 3D Botanical Engine for All Wildflowers, Grasses & Herbs
Genesis Zero - Blender 5.2.1 LTS
Generates unique, realistic 3D models (.blend + .glb) for all species in grasses_herbs + endemic flora.
"""

import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
sys.path.insert(0, str(ROOT / "assets" / "flora" / "generators"))

from flora_builder import (
    add_channeled_blade,
    add_cupped_petal,
    add_curved_tube,
    add_foliage_clump,
    clean_scene,
    create_pbr_bark_material,
    create_pbr_foliage_material,
    save_and_export,
)


def apply_smooth_and_materials(mesh, materials):
    for p in mesh.polygons:
        p.use_smooth = True
    for mat in materials:
        mesh.materials.append(mat)

# -----------------------------------------------------------------------------
# 1. Cúc Vàng Đồng Nội (Oxeye Daisy - flower_oxeye_daisy)
# -----------------------------------------------------------------------------
def build_flower_oxeye_daisy():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Daisy_Stem", (0.18, 0.45, 0.12, 1.0), sss_weight=0.35)
    mat_disc = create_pbr_foliage_material("M_Daisy_Center", (0.95, 0.65, 0.05, 1.0), sss_weight=0.25, roughness=0.7)
    mat_petal = create_pbr_foliage_material("M_Daisy_Petals", (0.96, 0.96, 0.98, 1.0), sss_weight=0.55, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Oxeye_Daisy_Mesh")
    verts, faces, mat_idx = [], [], []

    # Stems: 3 graceful curving stems
    for st_i, (dx, dy, h, lean) in enumerate([(0, 0, 0.65, 0.05), (-0.12, 0.08, 0.55, 0.15), (0.10, -0.06, 0.48, 0.12)]):
        pts = [
            Vector((dx*0.2, dy*0.2, 0.0)),
            Vector((dx*0.6 + lean*0.3, dy*0.6, h*0.4)),
            Vector((dx + lean*0.8, dy, h*0.8)),
            Vector((dx + lean, dy, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.012, 0.010, 0.008, 0.006], rad_segs=4, mat_id=0, cap_start=True, cap_end=False)

        # Flower head at tip
        tip = pts[-1]
        # Golden central disc dome
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.015)), 0.055, 0.055, 0.022, lat_steps=4, lon_steps=8, mat_id=1)

        # 18 Ray petals radiating outward with slight upward cup
        n_petals = 18 if st_i == 0 else 14
        for p in range(n_petals):
            ang = p * 2.0 * math.pi / n_petals
            fwd = Vector((math.cos(ang), math.sin(ang), 0.05 + 0.04*math.sin(ang*3))).normalized()
            up = Vector((-math.sin(ang)*0.1, math.cos(ang)*0.1, 1.0)).normalized()
            add_cupped_petal(verts, faces, mat_idx, tip + fwd*0.03, fwd, up, length=0.10, width=0.026, cup_depth=0.005, mat_id=2)

    # Basal rosette of notched leaves
    for lv in range(12):
        ang = lv * 2.0 * math.pi / 12 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [Vector((0, 0, 0.02)), Vector((dx*0.12, dy*0.12, 0.06)), Vector((dx*0.25, dy*0.25, 0.03))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.02, 0.045, 0.01], [0.002, 0.005, 0.001], mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_disc, mat_petal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Oxeye_Daisy", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_oxeye_daisy.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_oxeye_daisy.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 2. Hoa Hướng Dương Dại (Sunflower - flower_wild_sunflower)
# -----------------------------------------------------------------------------
def build_flower_wild_sunflower():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Sunflower_Stem", (0.22, 0.48, 0.12, 1.0), sss_weight=0.30, roughness=0.65)
    mat_disc = create_pbr_bark_material("M_Sunflower_Disc", (0.22, 0.12, 0.04, 1.0), roughness=0.85)
    mat_petal = create_pbr_foliage_material("M_Sunflower_Petals", (0.98, 0.75, 0.04, 1.0), sss_weight=0.60, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Wild_Sunflower_Mesh")
    verts, faces, mat_idx = [], [], []

    # Main sturdy stem
    stem_pts = [
        Vector((0, 0, 0)),
        Vector((0.05, -0.03, 0.5)),
        Vector((0.08, 0.02, 1.1)),
        Vector((0.15, 0.05, 1.55)),
        Vector((0.25, 0.10, 1.75)) # Nodding forward
    ]
    add_curved_tube(verts, faces, mat_idx, stem_pts, [0.035, 0.030, 0.025, 0.022, 0.020], rad_segs=6, mat_id=0)

    # Broad cordate leaves along stem
    for _l_idx, (sz, z_h, l_ang) in enumerate([(0.35, 0.4, 0.5), (0.32, 0.75, 2.6), (0.28, 1.15, 4.2), (0.22, 1.45, 1.2)]):
        dx, dy = math.cos(l_ang), math.sin(l_ang)
        l_pts = [
            Vector((dx*0.03, dy*0.03, z_h)),
            Vector((dx*sz*0.4, dy*sz*0.4, z_h + 0.08)),
            Vector((dx*sz*0.8, dy*sz*0.8, z_h + 0.04)),
            Vector((dx*sz, dy*sz, z_h - 0.05))
        ]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.04, 0.16, 0.12, 0.02], [0.01, 0.025, 0.015, 0.002], mat_id=0)

    # Large Sunflower Head
    head_center = stem_pts[-1]
    head_norm = Vector((0.7, 0.3, 0.6)).normalized()
    head_right = head_norm.cross(Vector((0, 0, 1))).normalized()
    head_up = head_right.cross(head_norm).normalized()

    # Dark chocolate center disc
    add_foliage_clump(verts, faces, mat_idx, head_center + head_norm*0.03, 0.16, 0.16, 0.05, lat_steps=4, lon_steps=12, mat_id=1)

    # Double row of 24 radiant golden petals
    for row, p_len, p_w in [(0, 0.22, 0.055), (1, 0.19, 0.048)]:
        for p in range(24):
            ang = (p + row*0.5) * 2.0 * math.pi / 24
            rad_dir = head_right * math.cos(ang) + head_up * math.sin(ang)
            fwd = (rad_dir + head_norm * (0.15 - row*0.08)).normalized()
            up = head_norm
            add_cupped_petal(verts, faces, mat_idx, head_center + rad_dir*0.14, fwd, up, length=p_len, width=p_w, cup_depth=0.01, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_disc, mat_petal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Wild_Sunflower", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_sunflower.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_sunflower.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 3. Hoa Anh Túc Lửa (Corn Poppy - flower_corn_poppy)
# -----------------------------------------------------------------------------
def build_flower_corn_poppy():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Poppy_Stem", (0.25, 0.48, 0.18, 1.0), sss_weight=0.30, roughness=0.55)
    mat_center = create_pbr_foliage_material("M_Poppy_Eye", (0.08, 0.06, 0.10, 1.0), sss_weight=0.10, roughness=0.8)
    mat_petal = create_pbr_foliage_material("M_Poppy_Petals", (0.92, 0.10, 0.08, 1.0), sss_color=(0.95, 0.2, 0.05), sss_weight=0.70, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Corn_Poppy_Mesh")
    verts, faces, mat_idx = [], [], []

    # 2 Slender arching flowering stems
    for _s_i, (dx, dy, h) in enumerate([(0, 0, 0.72), (0.15, -0.12, 0.58)]):
        pts = [
            Vector((dx*0.1, dy*0.1, 0)),
            Vector((dx*0.4 - 0.08, dy*0.4, h*0.4)),
            Vector((dx*0.8 + 0.05, dy*0.8, h*0.8)),
            Vector((dx, dy, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.010, 0.008, 0.006, 0.005], rad_segs=4, mat_id=0)

        tip = pts[-1]
        # Dark seed capsule center
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.02)), 0.025, 0.025, 0.03, lat_steps=4, lon_steps=8, mat_id=1)

        # 4 Large crinkled cup-shaped crimson petals
        for p in range(4):
            ang = p * math.pi * 0.5 + 0.35
            fwd = Vector((math.cos(ang), math.sin(ang), 0.45)).normalized()
            up = Vector((-math.sin(ang)*0.2, math.cos(ang)*0.2, 0.8)).normalized()
            add_cupped_petal(verts, faces, mat_idx, tip + fwd*0.015, fwd, up, length=0.13, width=0.11, cup_depth=0.035, mat_id=2)

    # Basal feathery divided leaves
    for lv in range(8):
        ang = lv * 2.0 * math.pi / 8 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [Vector((0, 0, 0.01)), Vector((dx*0.15, dy*0.15, 0.05)), Vector((dx*0.30, dy*0.30, 0.02))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.015, 0.04, 0.008], [0.002, 0.006, 0.001], mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_center, mat_petal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Corn_Poppy", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_corn_poppy.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_corn_poppy.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 4. Hoa Chuông Xanh (English Bluebell - flower_bluebell)
# -----------------------------------------------------------------------------
def build_flower_bluebell():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Bluebell_Stem", (0.22, 0.52, 0.18, 1.0), sss_weight=0.35)
    mat_bell = create_pbr_foliage_material("M_Bluebell_Flower", (0.28, 0.24, 0.85, 1.0), sss_color=(0.35, 0.30, 0.95), sss_weight=0.60, roughness=0.30)

    mesh = bpy.data.meshes.new("Flora_Bluebell_Mesh")
    verts, faces, mat_idx = [], [], []

    # 3 Graceful arching stems that curl at top
    for _st_i, rot_z in enumerate([0.0, 1.8, 3.8]):
        cos_z, sin_z = math.cos(rot_z), math.sin(rot_z)
        stem_pts = [
            Vector((0, 0, 0)),
            Vector((cos_z*0.05, sin_z*0.05, 0.2)),
            Vector((cos_z*0.12, sin_z*0.12, 0.38)),
            Vector((cos_z*0.22, sin_z*0.22, 0.46)),
            Vector((cos_z*0.28, sin_z*0.28, 0.42)) # drooping tip
        ]
        add_curved_tube(verts, faces, mat_idx, stem_pts, [0.010, 0.008, 0.006, 0.005, 0.003], rad_segs=4, mat_id=0)

        # 6-8 Nodding bell flowers hanging beneath the arch
        for b_i in range(7):
            t = (b_i + 1) / 8.0
            p_stalk = stem_pts[1] * (1.0 - t) + stem_pts[3] * t
            hang_dir = Vector((cos_z*0.06, sin_z*0.06, -0.06 - 0.02*b_i))
            bell_tip = p_stalk + hang_dir
            # Flower pedicel
            add_curved_tube(verts, faces, mat_idx, [p_stalk, bell_tip], [0.003, 0.002], rad_segs=3, mat_id=0)
            # Tubular bell with flared mouth
            bell_pts = [
                bell_tip,
                bell_tip + Vector((0, 0, -0.025)),
                bell_tip + Vector((0, 0, -0.055))
            ]
            add_curved_tube(verts, faces, mat_idx, bell_pts, [0.006, 0.014, 0.022], rad_segs=6, mat_id=1, cap_start=True, cap_end=False)

    # Basal linear strap-like leaves
    for lv in range(10):
        ang = lv * 2.0 * math.pi / 10 + 0.4
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [Vector((0, 0, 0.01)), Vector((dx*0.18, dy*0.18, 0.12)), Vector((dx*0.35, dy*0.35, 0.04))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.012, 0.028, 0.006], [0.002, 0.005, 0.001], mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_bell])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Bluebell", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_bluebell.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_bluebell.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 5. Oải Hương Tím Dại (Wild Lavender - flower_wild_lavender)
# -----------------------------------------------------------------------------
def build_flower_wild_lavender():
    clean_scene()
    mat_woody = create_pbr_bark_material("M_Lavender_Wood", (0.35, 0.30, 0.22, 1.0), roughness=0.85)
    mat_green = create_pbr_foliage_material("M_Lavender_Leaf", (0.32, 0.48, 0.35, 1.0), sss_weight=0.25, roughness=0.55)
    mat_flower = create_pbr_foliage_material("M_Lavender_Bloom", (0.55, 0.22, 0.85, 1.0), sss_color=(0.65, 0.3, 0.95), sss_weight=0.50, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Lavender_Mesh")
    verts, faces, mat_idx = [], [], []

    # Woody mound base
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.08)), 0.25, 0.25, 0.12, lat_steps=4, lon_steps=8, mat_id=0)

    # 12 Upright spikes with dense purple florets
    for sp_i in range(12):
        ang = sp_i * 2.0 * math.pi / 12 + random.uniform(-0.1, 0.1)
        rad = 0.10 + 0.08 * (sp_i % 3)
        h = 0.55 + 0.12 * ((sp_i * 2) % 3)
        dx, dy = math.cos(ang), math.sin(ang)

        pts = [
            Vector((dx*rad*0.5, dy*rad*0.5, 0.08)),
            Vector((dx*rad*0.9, dy*rad*0.9, h*0.5)),
            Vector((dx*rad, dy*rad, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.010, 0.007, 0.005], rad_segs=4, mat_id=1)

        # Flower spike tip (multiple interrupted whorls)
        for w_i in range(5):
            z_w = h - (4 - w_i) * 0.035
            add_foliage_clump(verts, faces, mat_idx, Vector((dx*rad, dy*rad, z_w)), 0.032, 0.032, 0.022, lat_steps=3, lon_steps=6, mat_id=2)

    # Narrow gray-green linear foliage
    for f_i in range(24):
        ang = f_i * 2.0 * math.pi / 24
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [Vector((0, 0, 0.06)), Vector((dx*0.12, dy*0.12, 0.16)), Vector((dx*0.22, dy*0.22, 0.10))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.01, 0.016, 0.005], [0.002, 0.004, 0.001], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_woody, mat_green, mat_flower])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Lavender", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_lavender.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_lavender.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 6. Bồ Công Anh Bào Tử Gió (Dandelion - flower_dandelion)
# -----------------------------------------------------------------------------
def build_flower_dandelion():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Dandelion_Stem", (0.28, 0.52, 0.18, 1.0), sss_weight=0.35)
    mat_fluff = create_pbr_foliage_material("M_Dandelion_Puff", (0.95, 0.96, 0.98, 1.0), sss_weight=0.75, roughness=0.90)
    mat_yellow = create_pbr_foliage_material("M_Dandelion_Bloom", (0.98, 0.82, 0.05, 1.0), sss_weight=0.55, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Dandelion_Mesh")
    verts, faces, mat_idx = [], [], []

    # Basal deeply runcinate / lion-toothed leaves
    for lv in range(12):
        ang = lv * 2.0 * math.pi / 12 + 0.1
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [
            Vector((0, 0, 0.01)),
            Vector((dx*0.12, dy*0.12, 0.04)),
            Vector((dx*0.24, dy*0.24, 0.05)),
            Vector((dx*0.35, dy*0.35, 0.02))
        ]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.015, 0.065, 0.05, 0.01], [0.002, 0.008, 0.005, 0.001], mat_id=0)

    # 1 Tall hollow stem bearing white puffball
    stem_puff = [Vector((0, 0, 0)), Vector((0.02, 0.01, 0.18)), Vector((0.01, 0.03, 0.36))]
    add_curved_tube(verts, faces, mat_idx, stem_puff, [0.010, 0.008, 0.006], rad_segs=4, mat_id=0)
    # Spherical white fluffy seedhead (pappus clock)
    add_foliage_clump(verts, faces, mat_idx, stem_puff[-1] + Vector((0, 0, 0.06)), 0.075, 0.075, 0.075, lat_steps=5, lon_steps=10, bump_amp=0.25, mat_id=1)

    # 1 Shorter stem bearing golden open blossom
    stem_bloom = [Vector((0.06, -0.04, 0)), Vector((0.10, -0.08, 0.14)), Vector((0.14, -0.10, 0.26))]
    add_curved_tube(verts, faces, mat_idx, stem_bloom, [0.009, 0.007, 0.005], rad_segs=4, mat_id=0)
    # Yellow ray floret head
    add_foliage_clump(verts, faces, mat_idx, stem_bloom[-1], 0.045, 0.045, 0.018, lat_steps=3, lon_steps=8, mat_id=2)
    for p in range(16):
        ang = p * 2.0 * math.pi / 16
        fwd = Vector((math.cos(ang), math.sin(ang), 0.1)).normalized()
        add_cupped_petal(verts, faces, mat_idx, stem_bloom[-1], fwd, Vector((0, 0, 1)), length=0.045, width=0.012, cup_depth=0.002, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_fluff, mat_yellow])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Dandelion", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_dandelion.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_dandelion.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 7. Cỏ Ba Lá May Mắn (White Clover - grass_white_clover)
# -----------------------------------------------------------------------------
def build_grass_white_clover():
    clean_scene()
    mat_green = create_pbr_foliage_material("M_Clover_Green", (0.16, 0.55, 0.14, 1.0), sss_weight=0.45)
    mat_bloom = create_pbr_foliage_material("M_Clover_Flower", (0.94, 0.94, 0.90, 1.0), sss_weight=0.55, roughness=0.40)

    mesh = bpy.data.meshes.new("Flora_White_Clover_Mesh")
    verts, faces, mat_idx = [], [], []

    # 14 Clover leaves, each with 3 obovate heart-shaped leaflets
    for c_i in range(14):
        ang = c_i * 2.0 * math.pi / 14 + random.uniform(-0.15, 0.15)
        dist = 0.08 + 0.16 * ((c_i * 3) % 5) / 4.0
        c_x, c_y = math.cos(ang) * dist, math.sin(ang) * dist
        h_leaf = 0.08 + 0.08 * (c_i % 3)

        # Petiole stalk
        petiole_pts = [
            Vector((0, 0, 0.01)),
            Vector((c_x * 0.5, c_y * 0.5, h_leaf * 0.6)),
            Vector((c_x, c_y, h_leaf))
        ]
        add_curved_tube(verts, faces, mat_idx, petiole_pts, [0.004, 0.003, 0.002], rad_segs=3, mat_id=0)

        # 3 Trifoliate leaflets spreading at 120 degrees
        leaf_apex = petiole_pts[-1]
        for l_idx in range(3):
            l_ang = ang + l_idx * (2.0 * math.pi / 3.0)
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.15)).normalized()
            up = Vector((0, 0, 1))
            add_cupped_petal(verts, faces, mat_idx, leaf_apex, fwd, up, length=0.048, width=0.042, cup_depth=0.006, mat_id=0)

    # 3 Spherical white clover flower heads
    for _fl_i, (fx, fy, fh) in enumerate([(0.05, 0.05, 0.18), (-0.08, 0.06, 0.16), (0.04, -0.09, 0.15)]):
        f_pts = [Vector((0, 0, 0.01)), Vector((fx*0.5, fy*0.5, fh*0.5)), Vector((fx, fy, fh))]
        add_curved_tube(verts, faces, mat_idx, f_pts, [0.005, 0.004, 0.003], rad_segs=3, mat_id=0)
        # Flower globe
        add_foliage_clump(verts, faces, mat_idx, f_pts[-1] + Vector((0, 0, 0.015)), 0.035, 0.035, 0.035, lat_steps=4, lon_steps=8, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_green, mat_bloom])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_White_Clover", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_white_clover.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_white_clover.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 8. Thảm Rêu Nhung Rừng Ẩm (Velvet Moss - grass_velvet_moss)
# -----------------------------------------------------------------------------
def build_grass_velvet_moss():
    clean_scene()
    mat_rock = create_pbr_bark_material("M_Moss_Substrate", (0.25, 0.22, 0.18, 1.0), roughness=0.90)
    mat_moss = create_pbr_foliage_material("M_Velvet_Moss", (0.08, 0.50, 0.15, 1.0), sss_color=(0.15, 0.65, 0.2), sss_weight=0.65, roughness=0.85)

    mesh = bpy.data.meshes.new("Flora_Velvet_Moss_Mesh")
    verts, faces, mat_idx = [], [], []

    # Undulating forest stone/soil mound base
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.08)), 0.65, 0.55, 0.14, lat_steps=5, lon_steps=10, bump_amp=0.20, mat_id=0)

    # Secondary puffy moss pillows clustering over the rock
    for _m_i, (mx, my, mz, rx, ry, rz) in enumerate([
        (0.15, 0.10, 0.15, 0.28, 0.24, 0.09),
        (-0.20, -0.08, 0.14, 0.32, 0.28, 0.10),
        (0.05, -0.22, 0.12, 0.24, 0.22, 0.08),
        (-0.08, 0.25, 0.13, 0.26, 0.22, 0.08),
        (0.28, -0.15, 0.10, 0.20, 0.18, 0.07)
    ]):
        add_foliage_clump(verts, faces, mat_idx, Vector((mx, my, mz)), rx, ry, rz, lat_steps=4, lon_steps=8, bump_amp=0.15, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_rock, mat_moss])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Velvet_Moss", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_velvet_moss.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_velvet_moss.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 9. Cỏ Đuôi Chuột Lông Vũ (Feather Grass - grass_feather_grass)
# -----------------------------------------------------------------------------
def build_grass_feather_grass():
    clean_scene()
    mat_green = create_pbr_foliage_material("M_Feather_Blade", (0.28, 0.50, 0.16, 1.0), sss_weight=0.35)
    mat_plume = create_pbr_foliage_material("M_Feather_Plume", (0.94, 0.94, 0.92, 1.0), sss_color=(0.98, 0.98, 0.95), sss_weight=0.75, roughness=0.30)

    mesh = bpy.data.meshes.new("Flora_Feather_Grass_Mesh")
    verts, faces, mat_idx = [], [], []

    # Basal slender blade tuft
    for b in range(32):
        ang = b * 2.0 * math.pi / 32 + random.uniform(-0.05, 0.05)
        dx, dy = math.cos(ang), math.sin(ang)
        lean = 0.35 + 0.20 * (b % 3)
        h = 0.55 + 0.25 * ((b * 2) % 4)
        b_pts = [
            Vector((0, 0, 0.02)),
            Vector((dx*lean*0.4, dy*lean*0.4, h*0.5)),
            Vector((dx*lean, dy*lean, h*0.75)),
            Vector((dx*lean*1.2, dy*lean*1.2, h*0.55))
        ]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.015, 0.025, 0.018, 0.004], [0.002, 0.005, 0.003, 0.001], mat_id=0)

    # 6 Silky graceful arching feathery plumes
    for p_i in range(6):
        ang = p_i * 2.0 * math.pi / 6 + 0.3
        dx, dy = math.cos(ang), math.sin(ang)
        culm_pts = [
            Vector((0, 0, 0.05)),
            Vector((dx*0.15, dy*0.15, 0.55)),
            Vector((dx*0.35, dy*0.35, 1.05)),
            Vector((dx*0.65, dy*0.65, 1.25)),
            Vector((dx*0.95, dy*0.95, 1.05)) # gracefully sweeping tail
        ]
        add_curved_tube(verts, faces, mat_idx, culm_pts, [0.010, 0.008, 0.006, 0.004, 0.002], rad_segs=4, mat_id=0)

        # Long silky feathery plume surrounding the arching tip
        for s in range(5):
            t = (s + 1) / 6.0
            p_pos = culm_pts[2] * (1.0 - t) + culm_pts[4] * t
            add_foliage_clump(verts, faces, mat_idx, p_pos, 0.065, 0.065, 0.14, lat_steps=3, lon_steps=6, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_green, mat_plume])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Feather_Grass", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_feather_grass.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_feather_grass.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 10. Cỏ Đuôi Phụng Thảo Nguyên (Switchgrass - grass_switchgrass)
# -----------------------------------------------------------------------------
def build_grass_switchgrass():
    clean_scene()
    mat_amber = create_pbr_foliage_material("M_Switchgrass_Amber", (0.75, 0.55, 0.18, 1.0), sss_weight=0.35, roughness=0.55)
    mat_panicle = create_pbr_foliage_material("M_Switchgrass_Panicle", (0.85, 0.65, 0.25, 1.0), sss_weight=0.50, roughness=0.65)

    mesh = bpy.data.meshes.new("Flora_Switchgrass_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dense fountain clump of tall amber blades
    for b in range(40):
        ang = b * 2.0 * math.pi / 40 + random.uniform(-0.06, 0.06)
        dx, dy = math.cos(ang), math.sin(ang)
        h = 1.10 + 0.40 * (b % 4) / 3.0
        lean = 0.30 + 0.35 * ((b * 3) % 5) / 4.0
        b_pts = [
            Vector((0, 0, 0.02)),
            Vector((dx*lean*0.3, dy*lean*0.3, h*0.5)),
            Vector((dx*lean*0.7, dy*lean*0.7, h*0.9)),
            Vector((dx*lean, dy*lean, h*0.75))
        ]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.022, 0.038, 0.025, 0.005], [0.003, 0.007, 0.004, 0.001], mat_id=0)

    # 8 Tall airy panicle seedheads
    for p_i in range(8):
        ang = p_i * 2.0 * math.pi / 8 + 0.25
        dx, dy = math.cos(ang), math.sin(ang)
        c_pts = [
            Vector((0, 0, 0.05)),
            Vector((dx*0.12, dy*0.12, 0.8)),
            Vector((dx*0.25, dy*0.25, 1.45)),
            Vector((dx*0.32, dy*0.32, 1.70))
        ]
        add_curved_tube(verts, faces, mat_idx, c_pts, [0.012, 0.009, 0.006, 0.003], rad_segs=4, mat_id=0)

        # Open cloud-like panicle head
        add_foliage_clump(verts, faces, mat_idx, c_pts[-1] + Vector((0, 0, 0.08)), 0.16, 0.16, 0.28, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_amber, mat_panicle])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Switchgrass", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_switchgrass.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_switchgrass.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 11. Cỏ Lúa Mì Đỏ Đồng Hoang (Red Fescue - grass_red_fescue)
# -----------------------------------------------------------------------------
def build_grass_red_fescue():
    clean_scene()
    mat_red = create_pbr_foliage_material("M_RedFescue_Anthocyanin", (0.55, 0.18, 0.15, 1.0), sss_color=(0.8, 0.2, 0.1), sss_weight=0.55, roughness=0.45)
    mat_green = create_pbr_foliage_material("M_RedFescue_Base", (0.22, 0.44, 0.14, 1.0), sss_weight=0.35, roughness=0.40)

    mesh = bpy.data.meshes.new("Flora_Red_Fescue_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dense clump of fine reddish hair blades
    for b in range(48):
        ang = b * 2.0 * math.pi / 48 + random.uniform(-0.06, 0.06)
        dx, dy = math.cos(ang), math.sin(ang)
        h = 0.35 + 0.15 * (b % 4) / 3.0
        lean = 0.25 + 0.25 * ((b * 5) % 7) / 6.0
        # Blade gradient
        b_pts = [
            Vector((0, 0, 0.01)),
            Vector((dx*lean*0.35, dy*lean*0.35, h*0.6)),
            Vector((dx*lean*0.8, dy*lean*0.8, h*0.85)),
            Vector((dx*lean, dy*lean, h*0.65))
        ]
        # Alternate materials for rich red-green anthocyanin shift
        m_id = 0 if (b % 3 != 0) else 1
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.012, 0.022, 0.015, 0.003], [0.002, 0.004, 0.002, 0.001], mat_id=m_id)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_red, mat_green])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Red_Fescue", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_red_fescue.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_red_fescue.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 12. Lan Hài Việt Nam (Paphiopedilum vietnamense - endemic_paphiopedilum_vietnamense)
# -----------------------------------------------------------------------------
def build_endemic_paphiopedilum_vietnamense():
    clean_scene()
    mat_rock = create_pbr_bark_material("M_Karst_Stone", (0.35, 0.34, 0.32, 1.0), roughness=0.88)
    mat_leaf = create_pbr_foliage_material("M_Orchid_Mottled_Leaf", (0.16, 0.42, 0.22, 1.0), sss_weight=0.35, roughness=0.35)
    mat_pouch = create_pbr_foliage_material("M_Orchid_Slipper_Pouch", (0.75, 0.18, 0.45, 1.0), sss_color=(0.95, 0.3, 0.6), sss_weight=0.70, roughness=0.25)
    mat_sepal = create_pbr_foliage_material("M_Orchid_Sepal_White", (0.94, 0.88, 0.92, 1.0), sss_color=(0.98, 0.85, 0.95), sss_weight=0.60, roughness=0.30)

    mesh = bpy.data.meshes.new("Flora_Lan_Hai_VN_Mesh")
    verts, faces, mat_idx = [], [], []

    # Karst limestone substrate block
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.05)), 0.22, 0.20, 0.08, lat_steps=4, lon_steps=7, bump_amp=0.25, mat_id=0)

    # 6 Mottled coriaceous leaves in opposite fan
    for lv_i in range(6):
        ang = (lv_i % 2) * math.pi + (lv_i // 2) * 0.35 + 0.1
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [
            Vector((0, 0, 0.06)),
            Vector((dx*0.10, dy*0.10, 0.10)),
            Vector((dx*0.22, dy*0.22, 0.07)),
            Vector((dx*0.28, dy*0.28, 0.03))
        ]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.03, 0.075, 0.055, 0.015], [0.004, 0.010, 0.006, 0.002], mat_id=1)

    # 1 Upright purple hairy scape
    scape_pts = [
        Vector((0, 0, 0.06)),
        Vector((0.02, -0.01, 0.18)),
        Vector((0.03, 0.02, 0.32)),
        Vector((0.04, 0.01, 0.42))
    ]
    add_curved_tube(verts, faces, mat_idx, scape_pts, [0.008, 0.007, 0.006, 0.005], rad_segs=4, mat_id=2)

    tip = scape_pts[-1]

    # Large Slipper Pouch (Cánh Môi Hài Nhung)
    add_foliage_clump(verts, faces, mat_idx, tip + Vector((0.04, 0, -0.04)), 0.042, 0.035, 0.055, lat_steps=4, lon_steps=8, mat_id=2)

    # Broad dorsal sepal (Cánh đài lưng hình tim trắng phớt hồng)
    dorsal_fwd = Vector((0, 0, 1.0))
    dorsal_up = Vector((-1.0, 0, 0))
    add_cupped_petal(verts, faces, mat_idx, tip, dorsal_fwd, dorsal_up, length=0.08, width=0.075, cup_depth=0.015, mat_id=3)

    # 2 Lateral spreading petals (Cánh tràng xòe ngang)
    for side in [-1, 1]:
        lat_fwd = Vector((0.2, side * 0.95, 0.15)).normalized()
        lat_up = Vector((0, 0, 1.0))
        add_cupped_petal(verts, faces, mat_idx, tip, lat_fwd, lat_up, length=0.075, width=0.035, cup_depth=0.008, mat_id=3)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_rock, mat_leaf, mat_pouch, mat_sepal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Lan_Hai_VN", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/understory_shrubs/endemic_paphiopedilum_vietnamense.blend"),
        str(ROOT / "assets/flora/understory_shrubs/endemic_paphiopedilum_vietnamense.glb")
    )
    return obj


# -----------------------------------------------------------------------------
# 13. Hoa Cúc Tím Echinacea (flower_purple_coneflower)
# -----------------------------------------------------------------------------
def build_flower_purple_coneflower():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Echinacea_Stem", (0.22, 0.48, 0.16, 1.0), sss_weight=0.30)
    mat_cone = create_pbr_bark_material("M_Echinacea_Cone", (0.75, 0.35, 0.08, 1.0), roughness=0.85)
    mat_petal = create_pbr_foliage_material("M_Echinacea_Petals", (0.75, 0.15, 0.65, 1.0), sss_color=(0.9, 0.25, 0.8), sss_weight=0.65)

    mesh = bpy.data.meshes.new("Flora_Echinacea_Mesh")
    verts, faces, mat_idx = [], [], []

    stem_pts = [Vector((0, 0, 0)), Vector((0.03, -0.02, 0.35)), Vector((0.02, 0.03, 0.72))]
    add_curved_tube(verts, faces, mat_idx, stem_pts, [0.012, 0.009, 0.006], rad_segs=4, mat_id=0)

    tip = stem_pts[-1]
    # Prominent conical copper-orange cone
    add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.03)), 0.045, 0.045, 0.065, lat_steps=4, lon_steps=8, mat_id=1)

    # 16 Drooping rose-purple ray petals (pointing down at ~40 deg)
    for p in range(16):
        ang = p * 2.0 * math.pi / 16
        fwd = Vector((math.cos(ang), math.sin(ang), -0.45)).normalized()
        up = Vector((0, 0, 1))
        add_cupped_petal(verts, faces, mat_idx, tip + fwd*0.02, fwd, up, length=0.11, width=0.028, cup_depth=0.004, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_cone, mat_petal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Echinacea", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_purple_coneflower.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_purple_coneflower.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 14. Bách Hợp Thung Lũng (Lily of the Valley - flower_lily_valley)
# -----------------------------------------------------------------------------
def build_flower_lily_valley():
    clean_scene()
    mat_leaf = create_pbr_foliage_material("M_LilyValley_Leaf", (0.15, 0.50, 0.18, 1.0), sss_weight=0.45)
    mat_bell = create_pbr_foliage_material("M_LilyValley_Bell", (0.96, 0.98, 0.96, 1.0), sss_weight=0.65, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Lily_Valley_Mesh")
    verts, faces, mat_idx = [], [], []

    # 2 Broad paired oval leaves
    for side in [-1, 1]:
        ang = side * 0.4
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [
            Vector((0, 0, 0.01)),
            Vector((dx*0.08, dy*0.08, 0.12)),
            Vector((dx*0.16, dy*0.16, 0.22)),
            Vector((dx*0.22, dy*0.22, 0.15))
        ]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.03, 0.11, 0.08, 0.015], [0.005, 0.018, 0.012, 0.002], mat_id=0)

    # 1 Slender arching raceme between the leaves
    stem_pts = [Vector((0, 0, 0.02)), Vector((0, 0.03, 0.15)), Vector((0, 0.06, 0.28)), Vector((0, 0.08, 0.25))]
    add_curved_tube(verts, faces, mat_idx, stem_pts, [0.006, 0.004, 0.003, 0.002], rad_segs=3, mat_id=0)

    # 6 Dainty white nodding bell flowers
    for b_i in range(6):
        t = (b_i + 1) / 7.0
        p_stalk = stem_pts[1] * (1.0 - t) + stem_pts[3] * t
        bell_pos = p_stalk + Vector((0.03, 0.02, -0.025))
        add_curved_tube(verts, faces, mat_idx, [p_stalk, bell_pos], [0.002, 0.001], rad_segs=3, mat_id=0)
        # Miniature bell
        bell_pts = [bell_pos, bell_pos + Vector((0, 0, -0.015)), bell_pos + Vector((0, 0, -0.03))]
        add_curved_tube(verts, faces, mat_idx, bell_pts, [0.004, 0.011, 0.015], rad_segs=5, mat_id=1, cap_start=True, cap_end=False)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_leaf, mat_bell])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Lily_Valley", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_lily_valley.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_lily_valley.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 15. Hoa Giọt Tuyết (Snowdrop - flower_snowdrop)
# -----------------------------------------------------------------------------
def build_flower_snowdrop():
    clean_scene()
    mat_green = create_pbr_foliage_material("M_Snowdrop_Green", (0.20, 0.55, 0.22, 1.0), sss_weight=0.35)
    mat_white = create_pbr_foliage_material("M_Snowdrop_White", (0.98, 0.98, 1.0, 1.0), sss_weight=0.65, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Snowdrop_Mesh")
    verts, faces, mat_idx = [], [], []

    # 4 Linear upright green blades
    for _l_i, rot in enumerate([0.1, 0.9, 3.2, 4.0]):
        dx, dy = math.cos(rot), math.sin(rot)
        l_pts = [Vector((0, 0, 0.01)), Vector((dx*0.06, dy*0.06, 0.10)), Vector((dx*0.12, dy*0.12, 0.16))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.01, 0.02, 0.004], [0.001, 0.003, 0.001], mat_id=0)

    # 1 Nodding flower stem arching like a crook
    stem_pts = [Vector((0, 0, 0.01)), Vector((0.02, 0.01, 0.14)), Vector((0.04, 0.02, 0.22)), Vector((0.06, 0.02, 0.20))]
    add_curved_tube(verts, faces, mat_idx, stem_pts, [0.006, 0.004, 0.003, 0.002], rad_segs=4, mat_id=0)

    tip = stem_pts[-1]
    # Green ovary node
    add_foliage_clump(verts, faces, mat_idx, tip, 0.012, 0.012, 0.012, lat_steps=3, lon_steps=6, mat_id=0)

    # 3 Outer large white cupped petals hanging down
    for p in range(3):
        ang = p * 2.0 * math.pi / 3.0
        fwd = Vector((math.cos(ang)*0.4, math.sin(ang)*0.4, -0.9)).normalized()
        up = Vector((math.cos(ang), math.sin(ang), 0.2)).normalized()
        add_cupped_petal(verts, faces, mat_idx, tip + Vector((0, 0, -0.01)), fwd, up, length=0.055, width=0.028, cup_depth=0.006, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_green, mat_white])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Snowdrop", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_snowdrop.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_snowdrop.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 16. Hoa Bìm Bìm Rừng (Morning Glory - flower_morning_glory)
# -----------------------------------------------------------------------------
def build_flower_morning_glory():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Glory_Vine", (0.22, 0.48, 0.16, 1.0), sss_weight=0.35)
    mat_petal = create_pbr_foliage_material("M_Glory_Bloom", (0.55, 0.12, 0.75, 1.0), sss_color=(0.7, 0.2, 0.9), sss_weight=0.65, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Morning_Glory_Mesh")
    verts, faces, mat_idx = [], [], []

    # Twining spiral vine stem climbing a central axis
    vine_pts = []
    for step in range(16):
        t = step / 15.0
        spiral_ang = t * math.pi * 4.0
        rad = 0.08 * (1.0 - t * 0.3)
        vine_pts.append(Vector((rad * math.cos(spiral_ang), rad * math.sin(spiral_ang), t * 0.75)))
    add_curved_tube(verts, faces, mat_idx, vine_pts, 0.008, rad_segs=4, mat_id=0)

    # Broad heart-shaped leaves along vine
    for l_i in range(5):
        t = (l_i + 1) / 6.0
        idx_pt = int(t * 14)
        pos = vine_pts[idx_pt]
        ang = t * math.pi * 4.0 + 0.5
        dx, dy = math.cos(ang), math.sin(ang)
        fwd = Vector((dx, dy, 0.2)).normalized()
        add_cupped_petal(verts, faces, mat_idx, pos, fwd, Vector((0, 0, 1)), length=0.10, width=0.085, cup_depth=0.008, mat_id=0)

    # 2 Flared trumpet/funnel flowers
    for _fl_i, t in enumerate([0.5, 0.85]):
        idx_pt = int(t * 14)
        pos = vine_pts[idx_pt]
        fl_dir = Vector((math.cos(t*6.0), math.sin(t*6.0), 0.4)).normalized()
        tube_pts = [pos, pos + fl_dir*0.05, pos + fl_dir*0.12]
        add_curved_tube(verts, faces, mat_idx, tube_pts, [0.008, 0.025, 0.075], rad_segs=8, mat_id=1, cap_start=False, cap_end=False)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_petal])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Morning_Glory", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_morning_glory.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_morning_glory.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 17. Hoa Phong Lữ Dại (Wild Geranium - flower_wild_geranium)
# -----------------------------------------------------------------------------
def build_flower_wild_geranium():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Geranium_Stem", (0.25, 0.50, 0.18, 1.0), sss_weight=0.35)
    mat_petal = create_pbr_foliage_material("M_Geranium_Bloom", (0.92, 0.55, 0.80, 1.0), sss_color=(0.95, 0.6, 0.85), sss_weight=0.60, roughness=0.30)
    mat_center = create_pbr_foliage_material("M_Geranium_Eye", (0.45, 0.15, 0.40, 1.0), sss_weight=0.25)

    mesh = bpy.data.meshes.new("Flora_Wild_Geranium_Mesh")
    verts, faces, mat_idx = [], [], []

    # Basal divided leaves
    for lv in range(8):
        ang = lv * 2.0 * math.pi / 8 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [Vector((0, 0, 0.02)), Vector((dx*0.10, dy*0.10, 0.08)), Vector((dx*0.20, dy*0.20, 0.05))]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.02, 0.065, 0.01], [0.002, 0.006, 0.001], mat_id=0)

    # 3 Slender flower scapes
    for _s_i, (dx, dy, h) in enumerate([(0, 0, 0.45), (0.10, 0.08, 0.38), (-0.08, -0.06, 0.36)]):
        pts = [Vector((0, 0, 0.02)), Vector((dx*0.5, dy*0.5, h*0.6)), Vector((dx, dy, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.008, 0.006, 0.004], rad_segs=4, mat_id=0)

        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip, 0.015, 0.015, 0.01, lat_steps=3, lon_steps=6, mat_id=2)
        # 5 Saucer-like petals spreading horizontally
        for p in range(5):
            ang = p * 2.0 * math.pi / 5.0
            fwd = Vector((math.cos(ang), math.sin(ang), 0.1)).normalized()
            up = Vector((0, 0, 1))
            add_cupped_petal(verts, faces, mat_idx, tip + fwd*0.01, fwd, up, length=0.065, width=0.045, cup_depth=0.004, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_petal, mat_center])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Wild_Geranium", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_geranium.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_geranium.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 18. Bạc Hà Rừng (Wild Mint - flower_wild_mint)
# -----------------------------------------------------------------------------
def build_flower_wild_mint():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Mint_Stem", (0.35, 0.22, 0.38, 1.0), sss_weight=0.30)
    mat_leaf = create_pbr_foliage_material("M_Mint_Leaf", (0.18, 0.48, 0.22, 1.0), sss_weight=0.40)
    mat_flower = create_pbr_foliage_material("M_Mint_Bloom", (0.85, 0.75, 0.90, 1.0), sss_weight=0.55)

    mesh = bpy.data.meshes.new("Flora_Wild_Mint_Mesh")
    verts, faces, mat_idx = [], [], []

    # 4 Square upright stems
    for _s_i, (sx, sy, sh) in enumerate([(0, 0, 0.52), (0.08, -0.06, 0.46), (-0.06, 0.08, 0.42), (0.05, 0.07, 0.38)]):
        s_pts = [Vector((sx*0.2, sy*0.2, 0)), Vector((sx*0.7, sy*0.7, sh*0.5)), Vector((sx, sy, sh))]
        add_curved_tube(verts, faces, mat_idx, s_pts, [0.012, 0.009, 0.006], rad_segs=4, mat_id=0)

        # Opposite decussate pairs of serrated ovate leaves
        for pair_i in range(5):
            z_p = (pair_i + 1) * (sh / 6.0)
            pair_ang = pair_i * math.pi * 0.5
            # Flower whorl at leaf axils
            add_foliage_clump(verts, faces, mat_idx, Vector((sx, sy, z_p)), 0.035, 0.035, 0.02, lat_steps=3, lon_steps=6, mat_id=2)
            for side in [-1, 1]:
                dx, dy = math.cos(pair_ang) * side, math.sin(pair_ang) * side
                fwd = Vector((dx, dy, 0.15)).normalized()
                add_cupped_petal(verts, faces, mat_idx, Vector((sx, sy, z_p)), fwd, Vector((0, 0, 1)), length=0.075, width=0.045, cup_depth=0.005, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf, mat_flower])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Wild_Mint", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_mint.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_wild_mint.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 19. Cây Xương Bồ Thơm (Sweet Flag - flower_sweet_flag)
# -----------------------------------------------------------------------------
def build_flower_sweet_flag():
    clean_scene()
    mat_blade = create_pbr_foliage_material("M_SweetFlag_Blade", (0.24, 0.54, 0.18, 1.0), sss_weight=0.35)
    mat_spadix = create_pbr_bark_material("M_SweetFlag_Spadix", (0.65, 0.55, 0.22, 1.0), roughness=0.80)

    mesh = bpy.data.meshes.new("Flora_Sweet_Flag_Mesh")
    verts, faces, mat_idx = [], [], []

    # Fan of vertical sword-like blades
    for b in range(16):
        ang = (b - 8) * 0.08
        dx, dy = math.sin(ang), math.cos(ang) * 0.15
        h = 0.85 + 0.25 * (1.0 - abs(b - 7.5)/8.0)
        b_pts = [
            Vector((dx*0.05, dy*0.05, 0.02)),
            Vector((dx*0.12, dy*0.12, h*0.5)),
            Vector((dx*0.18, dy*0.18, h))
        ]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.035, 0.042, 0.008], [0.004, 0.006, 0.001], mat_id=0)

    # 2 Cylindrical greenish-brown spadix spikes emerging from leaf side
    for sp_i in [-0.08, 0.08]:
        spadix_pts = [Vector((sp_i, 0.02, 0.25)), Vector((sp_i*1.2, 0.04, 0.48))]
        add_curved_tube(verts, faces, mat_idx, spadix_pts, [0.016, 0.014], rad_segs=6, mat_id=1, cap_start=True, cap_end=True)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_blade, mat_spadix])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Sweet_Flag", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_sweet_flag.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_sweet_flag.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 20. Cây Ngải Đắng Rừng (Wormwood - flower_wormwood)
# -----------------------------------------------------------------------------
def build_flower_wormwood():
    clean_scene()
    mat_silver = create_pbr_foliage_material("M_Wormwood_Silver", (0.55, 0.65, 0.58, 1.0), sss_weight=0.40, roughness=0.65)
    mat_head = create_pbr_foliage_material("M_Wormwood_Yellow", (0.85, 0.78, 0.25, 1.0), sss_weight=0.30)

    mesh = bpy.data.meshes.new("Flora_Wormwood_Mesh")
    verts, faces, mat_idx = [], [], []

    # Bushy clump of silvery-gray divided branches
    for b in range(12):
        ang = b * 2.0 * math.pi / 12 + random.uniform(-0.1, 0.1)
        dx, dy = math.cos(ang), math.sin(ang)
        h = 0.65 + 0.20 * (b % 3)
        pts = [Vector((0, 0, 0.05)), Vector((dx*0.15, dy*0.15, h*0.5)), Vector((dx*0.35, dy*0.35, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.014, 0.010, 0.005], rad_segs=4, mat_id=0)

        # Drooping panicles of tiny globular flower beads
        for f in range(5):
            z_f = h - (4 - f) * 0.06
            add_foliage_clump(verts, faces, mat_idx, Vector((dx*0.35 + 0.03*f, dy*0.35, z_f)), 0.025, 0.025, 0.025, lat_steps=3, lon_steps=5, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_silver, mat_head])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Wormwood", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/flower_wormwood.blend"),
        str(ROOT / "assets/flora/grasses_herbs/flower_wormwood.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 21. Cỏ Lông Nhím Rừng Đá (Sheep's Fescue - grass_sheeps_fescue)
# -----------------------------------------------------------------------------
def build_grass_sheeps_fescue():
    clean_scene()
    mat_blue = create_pbr_foliage_material("M_Fescue_BlueGray", (0.35, 0.45, 0.48, 1.0), sss_weight=0.30, roughness=0.45)

    mesh = bpy.data.meshes.new("Flora_Sheeps_Fescue_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dome base
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.05)), 0.22, 0.22, 0.08, lat_steps=4, lon_steps=8, mat_id=0)

    # Stiff hedgehog-like spiky needle blades radiating symmetrically in a hemisphere
    for b in range(56):
        ang = b * 2.0 * math.pi / 56 + random.uniform(-0.04, 0.04)
        phi = (b % 4 + 1) * 0.22  # zenith angle
        dx, dy = math.cos(ang) * math.sin(phi), math.sin(ang) * math.sin(phi)
        dz = math.cos(phi)
        b_len = 0.30 + 0.08 * (b % 3)
        b_pts = [
            Vector((0, 0, 0.05)),
            Vector((dx*b_len*0.5, dy*b_len*0.5, 0.05 + dz*b_len*0.5)),
            Vector((dx*b_len, dy*b_len, 0.05 + dz*b_len))
        ]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.015, 0.012, 0.002], [0.003, 0.002, 0.001], mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_blue])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Sheeps_Fescue", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_sheeps_fescue.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_sheeps_fescue.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 22. Thảm Rêu Râu Bạc Vách Đá (Woolly Fringe Moss - grass_woolly_moss)
# -----------------------------------------------------------------------------
def build_grass_woolly_moss():
    clean_scene()
    mat_rock = create_pbr_bark_material("M_Woolly_Granite", (0.30, 0.30, 0.32, 1.0), roughness=0.90)
    mat_woolly = create_pbr_foliage_material("M_Woolly_Moss_Silver", (0.78, 0.82, 0.78, 1.0), sss_weight=0.70, roughness=0.55)

    mesh = bpy.data.meshes.new("Flora_Woolly_Moss_Mesh")
    verts, faces, mat_idx = [], [], []

    # Rocky crag
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.06)), 0.55, 0.45, 0.12, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=0)

    # Silver-tipped woolly fringe cushions
    for _c_i, (cx, cy, cz) in enumerate([(0.12, 0.08, 0.14), (-0.15, -0.06, 0.12), (0.02, -0.18, 0.11), (-0.05, 0.18, 0.13)]):
        add_foliage_clump(verts, faces, mat_idx, Vector((cx, cy, cz)), 0.24, 0.22, 0.08, lat_steps=4, lon_steps=8, bump_amp=0.18, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_rock, mat_woolly])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Woolly_Moss", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_woolly_moss.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_woolly_moss.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 23. Rêu Than Bùn Đầm Lầy (Sphagnum Moss - grass_sphagnum_moss)
# -----------------------------------------------------------------------------
def build_grass_sphagnum_moss():
    clean_scene()
    mat_sphagnum = create_pbr_foliage_material("M_Sphagnum_OrangeGreen", (0.55, 0.65, 0.20, 1.0), sss_color=(0.7, 0.6, 0.15), sss_weight=0.70, roughness=0.60)

    mesh = bpy.data.meshes.new("Flora_Sphagnum_Mesh")
    verts, faces, mat_idx = [], [], []

    # Spongy peat bog hummock
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.08)), 0.70, 0.60, 0.16, lat_steps=5, lon_steps=10, bump_amp=0.22, mat_id=0)

    # 12 Rounded star-shaped capitula tufts
    for t_i in range(12):
        ang = t_i * 2.0 * math.pi / 12 + random.uniform(-0.1, 0.1)
        rad = 0.15 + 0.25 * ((t_i * 3) % 4) / 3.0
        tx, ty = math.cos(ang) * rad, math.sin(ang) * rad
        add_foliage_clump(verts, faces, mat_idx, Vector((tx, ty, 0.14)), 0.14, 0.14, 0.08, lat_steps=3, lon_steps=7, bump_amp=0.15, mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_sphagnum])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Sphagnum", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_sphagnum_moss.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_sphagnum_moss.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 24. Cỏ May Xước Đồng Hoang (Needle Burr - grass_needle_burr)
# -----------------------------------------------------------------------------
def build_grass_needle_burr():
    clean_scene()
    mat_green = create_pbr_foliage_material("M_NeedleBurr_Green", (0.28, 0.52, 0.18, 1.0), sss_weight=0.35)
    mat_burr = create_pbr_foliage_material("M_NeedleBurr_Spike", (0.55, 0.25, 0.45, 1.0), sss_weight=0.45, roughness=0.50)

    mesh = bpy.data.meshes.new("Flora_Needle_Burr_Mesh")
    verts, faces, mat_idx = [], [], []

    # Prostrate creeping stolons and short leaves
    for b in range(24):
        ang = b * 2.0 * math.pi / 24
        dx, dy = math.cos(ang), math.sin(ang)
        b_pts = [Vector((0, 0, 0.01)), Vector((dx*0.12, dy*0.12, 0.06)), Vector((dx*0.25, dy*0.25, 0.02))]
        add_channeled_blade(verts, faces, mat_idx, b_pts, [0.018, 0.025, 0.005], [0.002, 0.004, 0.001], mat_id=0)

    # 6 Upright flowering stalks with needle spikelets
    for st_i in range(6):
        ang = st_i * 2.0 * math.pi / 6 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [Vector((0, 0, 0.02)), Vector((dx*0.08, dy*0.08, 0.18)), Vector((dx*0.15, dy*0.15, 0.35))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.006, 0.004, 0.002], rad_segs=4, mat_id=0)
        # Prickly needle cluster at tip
        add_foliage_clump(verts, faces, mat_idx, pts[-1], 0.035, 0.035, 0.08, lat_steps=3, lon_steps=6, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_green, mat_burr])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Needle_Burr", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_needle_burr.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_needle_burr.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 25. Cỏ Mần Trầu (Goosegrass - grass_goosegrass)
# -----------------------------------------------------------------------------
def build_grass_goosegrass():
    clean_scene()
    mat_green = create_pbr_foliage_material("M_Goosegrass_Green", (0.24, 0.50, 0.16, 1.0), sss_weight=0.35)

    mesh = bpy.data.meshes.new("Flora_Goosegrass_Mesh")
    verts, faces, mat_idx = [], [], []

    # Radiating flattened prostrate culms (like wheel spokes)
    for c in range(5):
        c_ang = c * 2.0 * math.pi / 5.0
        cx, cy = math.cos(c_ang), math.sin(c_ang)
        c_pts = [
            Vector((0, 0, 0.01)),
            Vector((cx*0.15, cy*0.15, 0.18)),
            Vector((cx*0.35, cy*0.35, 0.42))
        ]
        add_curved_tube(verts, faces, mat_idx, c_pts, [0.008, 0.006, 0.004], rad_segs=4, mat_id=0)

        # 3-5 Digitate terminal finger spikes at each culm tip
        tip = c_pts[-1]
        for f in range(4):
            f_ang = c_ang + (f - 1.5) * 0.35
            fx, fy = math.cos(f_ang), math.sin(f_ang)
            finger_pts = [tip, tip + Vector((fx*0.06, fy*0.06, 0.05)), tip + Vector((fx*0.12, fy*0.12, 0.03))]
            add_channeled_blade(verts, faces, mat_idx, finger_pts, [0.008, 0.015, 0.003], [0.001, 0.003, 0.001], mat_id=0)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_green])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Goosegrass", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_goosegrass.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_goosegrass.glb")
    )
    return obj

# -----------------------------------------------------------------------------
# 26. Rêu Rồng Xanh Vách Thác (Umbrella Liverwort - grass_liverwort)
# -----------------------------------------------------------------------------
def build_grass_liverwort():
    clean_scene()
    mat_stone = create_pbr_bark_material("M_Wet_Waterfall_Stone", (0.22, 0.24, 0.26, 1.0), roughness=0.40)
    mat_thallus = create_pbr_foliage_material("M_Liverwort_Thallus", (0.12, 0.48, 0.20, 1.0), sss_weight=0.55, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Liverwort_Mesh")
    verts, faces, mat_idx = [], [], []

    # Wet rock surface
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.04)), 0.45, 0.40, 0.08, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=0)

    # Dichotomously branched lobed thalli spreading across the wet stone
    for th in range(12):
        ang = th * 2.0 * math.pi / 12 + random.uniform(-0.1, 0.1)
        dx, dy = math.cos(ang), math.sin(ang)
        [Vector((0, 0, 0.04)), Vector((dx*0.10, dy*0.10, 0.05)), Vector((dx*0.22, dy*0.22, 0.03))]
        add_cupped_petal(verts, faces, mat_idx, Vector((dx*0.05, dy*0.05, 0.04)), Vector((dx, dy, -0.05)), Vector((0, 0, 1)), length=0.12, width=0.065, cup_depth=-0.005, mat_id=1)

    # 4 Miniature umbrella-like archegoniophores standing erect
    for _u_i, (ux, uy) in enumerate([(0.06, 0.04), (-0.08, 0.05), (0.04, -0.07), (-0.05, -0.06)]):
        stalk_pts = [Vector((ux, uy, 0.04)), Vector((ux, uy, 0.12))]
        add_curved_tube(verts, faces, mat_idx, stalk_pts, [0.004, 0.003], rad_segs=3, mat_id=1)
        # Umbrella cap with 8 finger lobes
        add_foliage_clump(verts, faces, mat_idx, stalk_pts[-1] + Vector((0, 0, 0.005)), 0.025, 0.025, 0.008, lat_steps=3, lon_steps=8, bump_amp=0.35, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stone, mat_thallus])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Liverwort", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        str(ROOT / "assets/flora/grasses_herbs/grass_liverwort.blend"),
        str(ROOT / "assets/flora/grasses_herbs/grass_liverwort.glb")
    )
    return obj

def main():
    print(">>> Generating comprehensive wildflower and grass procedural 3D models in Blender...")
    builders = [
        ("Oxeye Daisy", build_flower_oxeye_daisy),
        ("Wild Sunflower", build_flower_wild_sunflower),
        ("Corn Poppy", build_flower_corn_poppy),
        ("English Bluebell", build_flower_bluebell),
        ("Wild Lavender", build_flower_wild_lavender),
        ("Dandelion Clock", build_flower_dandelion),
        ("White Clover", build_grass_white_clover),
        ("Velvet Forest Moss", build_grass_velvet_moss),
        ("Feather Grass", build_grass_feather_grass),
        ("Switchgrass", build_grass_switchgrass),
        ("Red Fescue", build_grass_red_fescue),
        ("Purple Coneflower", build_flower_purple_coneflower),
        ("Lily of the Valley", build_flower_lily_valley),
        ("Snowdrop", build_flower_snowdrop),
        ("Morning Glory", build_flower_morning_glory),
        ("Wild Geranium", build_flower_wild_geranium),
        ("Wild Mint", build_flower_wild_mint),
        ("Sweet Flag", build_flower_sweet_flag),
        ("Wormwood", build_flower_wormwood),
        ("Sheeps Fescue", build_grass_sheeps_fescue),
        ("Woolly Moss", build_grass_woolly_moss),
        ("Sphagnum Moss", build_grass_sphagnum_moss),
        ("Needle Burr", build_grass_needle_burr),
        ("Goosegrass", build_grass_goosegrass),
        ("Umbrella Liverwort", build_grass_liverwort),
        ("Lan Hai Viet Nam", build_endemic_paphiopedilum_vietnamense)
    ]
    for name, fn in builders:
        print(f"--> Building {name}...")
        fn()
    print("✓ All 26 botanical wildflower & grass models built successfully!")

if __name__ == "__main__":
    main()

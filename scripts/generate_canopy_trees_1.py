"""
generate_canopy_trees_1.py - Procedural 3D Engine for Canopy Trees (Part 1: Trees 1-11)
Genesis Zero - Blender 5.2.1 LTS
Builds 11 photorealistic canopy trees with clean BMesh topology & PBR materials.
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
sys.path.insert(0, str(ROOT / "assets" / "flora" / "generators"))

from flora_builder import (
    add_channeled_blade,
    add_curved_tube,
    add_foliage_clump,
    clean_scene,
    create_pbr_bark_material,
    create_pbr_foliage_material,
    save_and_export,
)


def apply_smooth_and_materials(mesh, materials, mat_idx):
    for p in mesh.polygons:
        p.use_smooth = True
    for mat in materials:
        mesh.materials.append(mat)
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

TARGET_DIR = ROOT / "assets" / "flora" / "canopy_trees"

# 1. tree_silver_birch (Betula pendula)
def build_tree_silver_birch():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Birch_Bark", (0.92, 0.94, 0.95, 1.0), roughness=0.88, bump_strength=0.45)
    mat_leaf = create_pbr_foliage_material("M_Birch_Leaf", (0.35, 0.65, 0.16, 1.0), sss_color=(0.55, 0.85, 0.2), sss_weight=0.55, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Silver_Birch_Mesh")
    verts, faces, mat_idx = [], [], []

    # Slender curved trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.15, -0.08, 2.5)),
        Vector((0.08, 0.12, 5.0)),
        Vector((0.25, 0.05, 7.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.22, 0.17, 0.12, 0.07], rad_segs=8, mat_id=0)

    # 5 Graceful weeping branches
    b_center = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.3
        bx, by = math.cos(ang)*1.8, math.sin(ang)*1.8
        b_pts = [
            b_center,
            b_center + Vector((bx*0.4, by*0.4, 0.8)),
            b_center + Vector((bx*0.8, by*0.8, 0.4)),
            b_center + Vector((bx, by, -0.6)) # pendulous weeping tip
        ]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.06, 0.045, 0.030, 0.015], rad_segs=5, mat_id=0)

        # Fluttering triangular foliage clumps along weeping branch
        for t in [0.45, 0.75, 1.0]:
            p_pos = b_pts[0].lerp(b_pts[-1], t)
            add_foliage_clump(verts, faces, mat_idx, p_pos, 0.85, 0.85, 0.65, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Silver_Birch", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_silver_birch.blend"), str(TARGET_DIR / "tree_silver_birch.glb"))
    return obj

# 2. tree_red_maple (Acer palmatum)
def build_tree_red_maple():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Maple_Bark", (0.35, 0.28, 0.24, 1.0), roughness=0.82)
    mat_leaf = create_pbr_foliage_material("M_Maple_Leaf", (0.85, 0.12, 0.10, 1.0), sss_color=(0.98, 0.25, 0.15), sss_weight=0.62, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Red_Maple_Mesh")
    verts, faces, mat_idx = [], [], []

    # Sculpted low multi-trunk
    for t_i, (dx, dy, h, r_st) in enumerate([(0, 0, 4.2, 0.24), (0.28, -0.18, 3.8, 0.18), (-0.22, 0.24, 3.6, 0.16)]):
        pts = [Vector((dx*0.2, dy*0.2, 0)), Vector((dx*0.6, dy*0.6, h*0.5)), Vector((dx, dy, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [r_st, r_st*0.7, r_st*0.4], rad_segs=6, mat_id=0)

        # Layered horizontal boughs
        tip = pts[-1]
        for l_i in range(3):
            l_ang = l_i * 2.0 * math.pi / 3 + t_i
            lx, ly = math.cos(l_ang)*1.4, math.sin(l_ang)*1.4
            b_pts = [tip, tip + Vector((lx*0.5, ly*0.5, 0.2)), tip + Vector((lx, ly, 0.1))]
            add_curved_tube(verts, faces, mat_idx, b_pts, [0.05, 0.035, 0.015], rad_segs=4, mat_id=0)
            # Horizontal scarlet foliage platforms
            add_foliage_clump(verts, faces, mat_idx, b_pts[-1], 1.10, 1.10, 0.45, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Red_Maple", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_red_maple.blend"), str(TARGET_DIR / "tree_red_maple.glb"))
    return obj

# 3. tree_jungle_palm (Arecaceae sylvestris)
def build_tree_jungle_palm():
    clean_scene()
    mat_trunk = create_pbr_bark_material("M_Palm_Trunk", (0.38, 0.32, 0.25, 1.0), roughness=0.88)
    mat_frond = create_pbr_foliage_material("M_Palm_Frond", (0.16, 0.52, 0.15, 1.0), sss_weight=0.45, roughness=0.35)
    mat_fruit = create_pbr_foliage_material("M_Palm_Fruit", (0.92, 0.55, 0.12, 1.0), sss_weight=0.55, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Jungle_Palm_Mesh")
    verts, faces, mat_idx = [], [], []

    # Columnar ringed trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.10, -0.05, 3.0)),
        Vector((0.05, 0.08, 6.0)),
        Vector((0.12, 0.02, 9.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.22, 0.20, 0.18, 0.16], rad_segs=8, mat_id=0)

    # 14 Large arching pinnate fronds forming umbrella crown
    apex = trunk_pts[-1]
    for f_i in range(14):
        ang = f_i * 2.0 * math.pi / 14
        dx, dy = math.cos(ang), math.sin(ang)
        f_pts = [
            apex,
            apex + Vector((dx*0.8, dy*0.8, 0.8)),
            apex + Vector((dx*1.8, dy*1.8, 0.9)),
            apex + Vector((dx*2.8, dy*2.8, 0.3)),
            apex + Vector((dx*3.4, dy*3.4, -0.6)) # pendulous droop
        ]
        add_channeled_blade(verts, faces, mat_idx, f_pts, [0.08, 0.45, 0.65, 0.40, 0.08], [0.02, 0.06, 0.04, 0.015, 0.002], mat_id=1)

    # Orange dates/fruit clusters hanging beneath crown
    for d_i in range(3):
        d_ang = d_i * 2.0 * math.pi / 3 + 0.4
        dx, dy = math.cos(d_ang)*0.25, math.sin(d_ang)*0.25
        add_foliage_clump(verts, faces, mat_idx, apex + Vector((dx, dy, -0.35)), 0.18, 0.18, 0.28, lat_steps=3, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_trunk, mat_frond, mat_fruit], mat_idx)
    obj = bpy.data.objects.new("Flora_Jungle_Palm", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_jungle_palm.blend"), str(TARGET_DIR / "tree_jungle_palm.glb"))
    return obj

# 4. tree_mountain_cherry (Prunus serrulata)
def build_tree_mountain_cherry():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Cherry_Bark", (0.32, 0.18, 0.14, 1.0), roughness=0.65)
    mat_blossom = create_pbr_foliage_material("M_Cherry_Blossom", (0.96, 0.82, 0.88, 1.0), sss_color=(0.98, 0.88, 0.92), sss_weight=0.72, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Mountain_Cherry_Mesh")
    verts, faces, mat_idx = [], [], []

    # Gnarled trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.12, 0.08, 1.8)),
        Vector((0.05, -0.06, 3.5)),
        Vector((0.18, 0.02, 5.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.26, 0.21, 0.16, 0.10], rad_segs=7, mat_id=0)

    # 4 Wide spreading boughs draped in sakura blossom clouds
    b_st = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.3
        bx, by = math.cos(ang)*2.2, math.sin(ang)*2.2
        b_pts = [b_st, b_st + Vector((bx*0.4, by*0.4, 0.5)), b_st + Vector((bx*0.8, by*0.8, 0.7)), b_st + Vector((bx, by, 0.4))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.08, 0.055, 0.035, 0.015], rad_segs=5, mat_id=0)

        # Billowing sakura blossom clouds
        add_foliage_clump(verts, faces, mat_idx, b_pts[2] + Vector((0, 0, 0.3)), 1.35, 1.35, 0.95, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=1)
        add_foliage_clump(verts, faces, mat_idx, b_pts[3] + Vector((0, 0, 0.1)), 1.10, 1.10, 0.80, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_blossom], mat_idx)
    obj = bpy.data.objects.new("Flora_Mountain_Cherry", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_mountain_cherry.blend"), str(TARGET_DIR / "tree_mountain_cherry.glb"))
    return obj

# 5. tree_blue_gum (Eucalyptus globulus)
def build_tree_blue_gum():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Eucalyptus_Trunk", (0.62, 0.65, 0.60, 1.0), roughness=0.6)
    mat_leaf = create_pbr_foliage_material("M_Eucalyptus_Foliage", (0.22, 0.48, 0.45, 1.0), sss_weight=0.45, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Blue_Gum_Mesh")
    verts, faces, mat_idx = [], [], []

    # Soaring straight trunk with peeling mottled bark
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.06, -0.04, 3.5)),
        Vector((0.02, 0.05, 7.0)),
        Vector((0.08, 0.02, 10.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.32, 0.24, 0.17, 0.10], rad_segs=8, mat_id=0)

    # High sparse canopy of weeping falcate foliage
    apex = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.2
        bx, by = math.cos(ang)*2.0, math.sin(ang)*2.0
        b_pts = [apex, apex + Vector((bx*0.5, by*0.5, 0.8)), apex + Vector((bx, by, 0.3))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.065, 0.040, 0.015], rad_segs=4, mat_id=0)
        # Blue-green glaucous foliage clumps
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.2)), 1.25, 1.25, 0.85, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Blue_Gum", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_blue_gum.blend"), str(TARGET_DIR / "tree_blue_gum.glb"))
    return obj

# 6. tree_italian_cypress (Cupressus sempervirens)
def build_tree_italian_cypress():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Cypress_Bark", (0.30, 0.22, 0.16, 1.0), roughness=0.9)
    mat_foliage = create_pbr_foliage_material("M_Cypress_Foliage", (0.08, 0.25, 0.12, 1.0), sss_weight=0.25, roughness=0.6)

    mesh = bpy.data.meshes.new("Flora_Italian_Cypress_Mesh")
    verts, faces, mat_idx = [], [], []

    # Short basal trunk
    trunk_pts = [Vector((0, 0, 0)), Vector((0, 0, 0.6)), Vector((0, 0, 1.2))]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.18, 0.14, 0.10], rad_segs=6, mat_id=0)

    # Iconic dense columnar spire/flame silhouette
    # Stacked tapering oval foliage lobes
    for _s_i, (z_c, r_xy, r_z) in enumerate([
        (1.8, 0.60, 0.85),
        (3.0, 0.70, 0.95),
        (4.4, 0.65, 0.95),
        (5.8, 0.55, 0.90),
        (7.0, 0.40, 0.80),
        (8.0, 0.22, 0.65),
    ]):
        add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, z_c)), r_xy, r_xy, r_z, lat_steps=4, lon_steps=8, bump_freq=4.0, bump_amp=0.15, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_foliage], mat_idx)
    obj = bpy.data.objects.new("Flora_Italian_Cypress", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_italian_cypress.blend"), str(TARGET_DIR / "tree_italian_cypress.glb"))
    return obj

# 7. tree_sweet_chestnut (Castanea sativa)
def build_tree_sweet_chestnut():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Chestnut_Bark", (0.28, 0.22, 0.16, 1.0), roughness=0.92, bump_strength=0.7)
    mat_leaf = create_pbr_foliage_material("M_Chestnut_Leaf", (0.14, 0.45, 0.15, 1.0), sss_weight=0.38)

    mesh = bpy.data.meshes.new("Flora_Sweet_Chestnut_Mesh")
    verts, faces, mat_idx = [], [], []

    # Massive muscular fluted trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.15, 0.08, 1.8)),
        Vector((-0.08, 0.14, 3.8)),
        Vector((0.05, 0.02, 5.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.55, 0.42, 0.32, 0.22], rad_segs=8, mat_id=0)

    # 4 Heavy spreading boughs
    tip = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.35
        bx, by = math.cos(ang)*2.8, math.sin(ang)*2.8
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.6)), tip + Vector((bx, by, 0.8))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.15, 0.09, 0.04], rad_segs=5, mat_id=0)

        # Broad foliage dome
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.3)), 1.80, 1.80, 1.10, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Sweet_Chestnut", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_sweet_chestnut.blend"), str(TARGET_DIR / "tree_sweet_chestnut.glb"))
    return obj

# 8. tree_chinese_hackberry (Celtis sinensis)
def build_tree_chinese_hackberry():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Hackberry_Bark", (0.38, 0.36, 0.34, 1.0), roughness=0.6)
    mat_leaf = create_pbr_foliage_material("M_Hackberry_Leaf", (0.16, 0.48, 0.18, 1.0), sss_weight=0.42)

    mesh = bpy.data.meshes.new("Flora_Chinese_Hackberry_Mesh")
    verts, faces, mat_idx = [], [], []

    # Smooth grey bark trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.08, -0.06, 2.0)),
        Vector((-0.04, 0.08, 4.2)),
        Vector((0.05, 0.02, 6.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.38, 0.30, 0.22, 0.14], rad_segs=7, mat_id=0)

    # Wide hemispherical dome canopy
    tip = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.2
        bx, by = math.cos(ang)*2.4, math.sin(ang)*2.4
        b_pts = [tip, tip + Vector((bx*0.5, by*0.5, 0.6)), tip + Vector((bx, by, 0.7))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.10, 0.06, 0.025], rad_segs=4, mat_id=0)

        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.3)), 1.50, 1.50, 1.00, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Chinese_Hackberry", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_chinese_hackberry.blend"), str(TARGET_DIR / "tree_chinese_hackberry.glb"))
    return obj

# 9. tree_jacaranda (Jacaranda mimosifolia)
def build_tree_jacaranda():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Jacaranda_Bark", (0.32, 0.26, 0.20, 1.0), roughness=0.85)
    mat_bloom = create_pbr_foliage_material("M_Jacaranda_Bloom", (0.45, 0.28, 0.88, 1.0), sss_color=(0.6, 0.4, 0.98), sss_weight=0.68, roughness=0.28)

    mesh = bpy.data.meshes.new("Flora_Jacaranda_Mesh")
    verts, faces, mat_idx = [], [], []

    # Umbrella spreading trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.10, 0.06, 1.8)),
        Vector((0.02, -0.05, 3.6)),
        Vector((0.12, 0.02, 5.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.28, 0.22, 0.16, 0.10], rad_segs=6, mat_id=0)

    # Explosion of dense violet-indigo bloom clouds
    tip = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.3
        bx, by = math.cos(ang)*2.4, math.sin(ang)*2.4
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.5)), tip + Vector((bx, by, 0.8))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.08, 0.05, 0.02], rad_segs=4, mat_id=0)

        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.25)), 1.60, 1.60, 1.10, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_bloom], mat_idx)
    obj = bpy.data.objects.new("Flora_Jacaranda", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_jacaranda.blend"), str(TARGET_DIR / "tree_jacaranda.glb"))
    return obj

# 10. tree_ginkgo (Ginkgo biloba)
def build_tree_ginkgo():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Ginkgo_Bark", (0.35, 0.32, 0.26, 1.0), roughness=0.88)
    mat_leaf = create_pbr_foliage_material("M_Ginkgo_Gold", (0.95, 0.78, 0.08, 1.0), sss_color=(0.99, 0.88, 0.15), sss_weight=0.60, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Ginkgo_Mesh")
    verts, faces, mat_idx = [], [], []

    # Pyramidal tapering trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.05, -0.03, 2.8)),
        Vector((0.02, 0.04, 5.5)),
        Vector((0.00, 0.00, 8.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.35, 0.26, 0.17, 0.08], rad_segs=7, mat_id=0)

    # Tiered branches with radiant golden fan foliage
    for tier in range(4):
        z_t = 3.0 + tier * 1.4
        r_reach = 2.0 * (1.0 - 0.2 * tier)
        for b in range(3):
            ang = b * 2.0 * math.pi / 3 + tier * 0.8
            bx, by = math.cos(ang)*r_reach, math.sin(ang)*r_reach
            b_st = Vector((0, 0, z_t))
            b_pts = [b_st, b_st + Vector((bx*0.5, by*0.5, 0.2)), b_st + Vector((bx, by, 0.35))]
            add_curved_tube(verts, faces, mat_idx, b_pts, [0.06, 0.04, 0.015], rad_segs=4, mat_id=0)

            # Golden foliage clumps
            add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.15)), 1.10, 1.10, 0.70, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Ginkgo", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_ginkgo.blend"), str(TARGET_DIR / "tree_ginkgo.glb"))
    return obj

# 11. tree_magnolia (Magnolia grandiflora)
def build_tree_magnolia():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Magnolia_Bark", (0.34, 0.30, 0.25, 1.0), roughness=0.82)
    mat_leaf = create_pbr_foliage_material("M_Magnolia_Leaf", (0.10, 0.38, 0.14, 1.0), sss_weight=0.35, roughness=0.25)
    mat_flower = create_pbr_foliage_material("M_Magnolia_Flower", (0.96, 0.95, 0.90, 1.0), sss_color=(0.98, 0.96, 0.92), sss_weight=0.68, roughness=0.22)

    mesh = bpy.data.meshes.new("Flora_Magnolia_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dense conical trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.08, 0.04, 2.0)),
        Vector((-0.03, -0.05, 4.2)),
        Vector((0.05, 0.00, 6.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.30, 0.22, 0.15, 0.08], rad_segs=7, mat_id=0)

    # 4 Dense boughs
    tip = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.3
        bx, by = math.cos(ang)*2.0, math.sin(ang)*2.0
        b_pts = [tip, tip + Vector((bx*0.5, by*0.5, 0.4)), tip + Vector((bx, by, 0.5))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.08, 0.05, 0.02], rad_segs=4, mat_id=0)

        # Dense glossy evergreen crown
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.2)), 1.40, 1.40, 0.95, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

        # Ivory white chalice blossoms
        fl_tip = b_pts[-1] + Vector((bx*0.3, by*0.3, 0.4))
        add_foliage_clump(verts, faces, mat_idx, fl_tip, 0.12, 0.12, 0.10, lat_steps=3, lon_steps=8, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_flower], mat_idx)
    obj = bpy.data.objects.new("Flora_Magnolia", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_magnolia.blend"), str(TARGET_DIR / "tree_magnolia.glb"))
    return obj

def main():
    print(">>> Generating Canopy Trees (Part 1: Trees 1-11)...")
    builders = [
        ("tree_silver_birch", build_tree_silver_birch),
        ("tree_red_maple", build_tree_red_maple),
        ("tree_jungle_palm", build_tree_jungle_palm),
        ("tree_mountain_cherry", build_tree_mountain_cherry),
        ("tree_blue_gum", build_tree_blue_gum),
        ("tree_italian_cypress", build_tree_italian_cypress),
        ("tree_sweet_chestnut", build_tree_sweet_chestnut),
        ("tree_chinese_hackberry", build_tree_chinese_hackberry),
        ("tree_jacaranda", build_tree_jacaranda),
        ("tree_ginkgo", build_tree_ginkgo),
        ("tree_magnolia", build_tree_magnolia)
    ]
    for slug, fn in builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ Canopy Trees Part 1 generated successfully!")

if __name__ == "__main__":
    main()

"""
generate_canopy_trees_2.py - Procedural 3D Engine for Canopy Trees (Part 2: Trees 12-21)
Genesis Zero - Blender 5.2.1 LTS
Builds 10 photorealistic master canopy trees with clean BMesh topology & PBR materials.
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

# 12. tree_golden_larch (Larix decidua)
def build_tree_golden_larch():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Larch_Bark", (0.34, 0.22, 0.16, 1.0), roughness=0.88)
    mat_needle = create_pbr_foliage_material("M_Larch_Needle", (0.92, 0.62, 0.10, 1.0), sss_color=(0.98, 0.75, 0.15), sss_weight=0.55, roughness=0.4)

    mesh = bpy.data.meshes.new("Flora_Golden_Larch_Mesh")
    verts, faces, mat_idx = [], [], []

    # Straight tapering conifer trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.04, -0.02, 3.5)),
        Vector((0.01, 0.03, 7.0)),
        Vector((0.00, 0.00, 10.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.35, 0.25, 0.16, 0.08], rad_segs=8, mat_id=0)

    # 4 Tiers of horizontal whorled branches with golden autumn needles
    for tier in range(4):
        z_t = 3.5 + tier * 1.8
        r_reach = 2.4 * (1.0 - 0.22 * tier)
        for b in range(4):
            ang = b * 2.0 * math.pi / 4 + tier * 0.7
            bx, by = math.cos(ang)*r_reach, math.sin(ang)*r_reach
            b_st = Vector((0, 0, z_t))
            b_pts = [b_st, b_st + Vector((bx*0.5, by*0.5, 0.1)), b_st + Vector((bx, by, 0.2))]
            add_curved_tube(verts, faces, mat_idx, b_pts, [0.06, 0.04, 0.015], rad_segs=4, mat_id=0)
            # Golden needle clusters
            add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.1)), 1.25, 1.25, 0.55, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_needle], mat_idx)
    obj = bpy.data.objects.new("Flora_Golden_Larch", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_golden_larch.blend"), str(TARGET_DIR / "tree_golden_larch.glb"))
    return obj

# 13. tree_oriental_arborvitae (Platycladus orientalis)
def build_tree_oriental_arborvitae():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Arborvitae_Bark", (0.32, 0.24, 0.18, 1.0), roughness=0.85)
    mat_spray = create_pbr_foliage_material("M_Arborvitae_Foliage", (0.12, 0.48, 0.20, 1.0), sss_weight=0.35, roughness=0.5)

    mesh = bpy.data.meshes.new("Flora_Arborvitae_Mesh")
    verts, faces, mat_idx = [], [], []

    # Short trunk
    trunk_pts = [Vector((0, 0, 0)), Vector((0, 0, 0.8)), Vector((0, 0, 1.5))]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.20, 0.15, 0.10], rad_segs=6, mat_id=0)

    # Teardrop ovoid-conical shape with vertical spray lobes
    for _s_i, (zc, rx, rz) in enumerate([
        (2.0, 1.20, 0.90),
        (3.4, 1.35, 1.05),
        (4.8, 1.10, 0.95),
        (5.8, 0.65, 0.80)
    ]):
        add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, zc)), rx, rx, rz, lat_steps=4, lon_steps=8, bump_freq=6.0, bump_amp=0.18, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_spray], mat_idx)
    obj = bpy.data.objects.new("Flora_Oriental_Arborvitae", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "tree_oriental_arborvitae.blend"), str(TARGET_DIR / "tree_oriental_arborvitae.glb"))
    return obj

# 14. canopy_ancient_banyan (Ficus macrophylla)
def build_canopy_ancient_banyan():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Banyan_Trunk", (0.35, 0.32, 0.26, 1.0), roughness=0.88, bump_strength=0.6)
    mat_foliage = create_pbr_foliage_material("M_Banyan_Foliage", (0.08, 0.36, 0.12, 1.0), sss_weight=0.40)

    mesh = bpy.data.meshes.new("Flora_Ancient_Banyan_Mesh")
    verts, faces, mat_idx = [], [], []

    # Fluted central trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.15, -0.10, 2.5)),
        Vector((0.05, 0.12, 5.0)),
        Vector((0.10, 0.02, 7.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.65, 0.52, 0.40, 0.28], rad_segs=8, mat_id=0)

    # 4 Massive spreading boughs
    tip = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.35
        bx, by = math.cos(ang)*3.5, math.sin(ang)*3.5
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.8)), tip + Vector((bx, by, 0.9))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.20, 0.14, 0.08], rad_segs=6, mat_id=0)

        # Hanging aerial stilt roots dropping to ground
        root_pts = [
            b_pts[1],
            b_pts[1] + Vector((0.1, 0.1, -2.5)),
            Vector((b_pts[1].x + 0.15, b_pts[1].y + 0.15, 0))
        ]
        add_curved_tube(verts, faces, mat_idx, root_pts, [0.08, 0.07, 0.09], rad_segs=5, mat_id=0)

        # Broad shade foliage canopy
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.4)), 2.20, 2.20, 1.20, lat_steps=5, lon_steps=10, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_foliage], mat_idx)
    obj = bpy.data.objects.new("Flora_Ancient_Banyan", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_ancient_banyan.blend"), str(TARGET_DIR / "canopy_ancient_banyan.glb"))
    return obj

# 15. canopy_cedar_lebanon (Cedrus libani)
def build_canopy_cedar_lebanon():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Cedar_Bark", (0.26, 0.22, 0.18, 1.0), roughness=0.92, bump_strength=0.7)
    mat_foliage = create_pbr_foliage_material("M_Cedar_Foliage", (0.06, 0.28, 0.10, 1.0), sss_weight=0.30, roughness=0.55)

    mesh = bpy.data.meshes.new("Flora_Cedar_Lebanon_Mesh")
    verts, faces, mat_idx = [], [], []

    # Rugged trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.10, 0.06, 3.0)),
        Vector((0.02, -0.04, 6.0)),
        Vector((0.00, 0.00, 9.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.55, 0.42, 0.30, 0.18], rad_segs=8, mat_id=0)

    # 4 Dramatic horizontal tabular shelf tiers
    for tier in range(4):
        z_t = 3.8 + tier * 1.8
        r_reach = 3.2 * (1.0 - 0.2 * tier)
        for b in range(3):
            ang = b * 2.0 * math.pi / 3 + tier * 0.9
            bx, by = math.cos(ang)*r_reach, math.sin(ang)*r_reach
            b_st = Vector((0, 0, z_t))
            b_pts = [b_st, b_st + Vector((bx*0.5, by*0.5, 0.05)), b_st + Vector((bx, by, 0.1))]
            add_curved_tube(verts, faces, mat_idx, b_pts, [0.12, 0.08, 0.035], rad_segs=5, mat_id=0)

            # Flat horizontal shelf platform foliage
            add_foliage_clump(verts, faces, mat_idx, b_pts[-1], 1.60, 1.60, 0.45, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_foliage], mat_idx)
    obj = bpy.data.objects.new("Flora_Cedar_Lebanon", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_cedar_lebanon.blend"), str(TARGET_DIR / "canopy_cedar_lebanon.glb"))
    return obj

# 16. canopy_ancient_ironwood (Guaiacum officinale)
def build_canopy_ancient_ironwood():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Ironwood_Bark", (0.36, 0.32, 0.26, 1.0), roughness=0.75, bump_strength=0.6)
    mat_foliage = create_pbr_foliage_material("M_Ironwood_Foliage", (0.09, 0.34, 0.14, 1.0), sss_weight=0.35)

    mesh = bpy.data.meshes.new("Flora_Ancient_Ironwood_Mesh")
    verts, faces, mat_idx = [], [], []

    # Gnarled twisted multi-furcated hardwood trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.14, 0.10, 1.5)),
        Vector((-0.10, 0.12, 3.2)),
        Vector((0.05, 0.02, 4.8))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.42, 0.32, 0.24, 0.15], rad_segs=7, mat_id=0)

    # 4 Gnarled boughs
    tip = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.3
        bx, by = math.cos(ang)*2.2, math.sin(ang)*2.2
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.4)), tip + Vector((bx, by, 0.6))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.10, 0.065, 0.025], rad_segs=5, mat_id=0)

        # Compact rounded canopy
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.2)), 1.45, 1.45, 0.95, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_foliage], mat_idx)
    obj = bpy.data.objects.new("Flora_Ancient_Ironwood", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_ancient_ironwood.blend"), str(TARGET_DIR / "canopy_ancient_ironwood.glb"))
    return obj

# 17. canopy_ancient_ginkgo (Ginkgo biloba gigantea)
def build_canopy_ancient_ginkgo():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_AncientGinkgo_Trunk", (0.34, 0.30, 0.24, 1.0), roughness=0.92, bump_strength=0.7)
    mat_leaf = create_pbr_foliage_material("M_AncientGinkgo_Foliage", (0.98, 0.80, 0.05, 1.0), sss_color=(0.99, 0.90, 0.12), sss_weight=0.62, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Ancient_Ginkgo_Mesh")
    verts, faces, mat_idx = [], [], []

    # Immense ancient trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.15, -0.10, 3.5)),
        Vector((0.05, 0.12, 7.0)),
        Vector((0.10, 0.02, 10.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.72, 0.55, 0.40, 0.25], rad_segs=8, mat_id=0)

    # Spreading boughs with hanging "chichi" woody stalactites
    tip = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.25
        bx, by = math.cos(ang)*3.2, math.sin(ang)*3.2
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.8)), tip + Vector((bx, by, 1.1))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.18, 0.12, 0.05], rad_segs=6, mat_id=0)

        # Hanging woody stalactite (chichi)
        ch_st = b_pts[1]
        ch_pts = [ch_st, ch_st + Vector((0.05, 0, -0.8)), ch_st + Vector((0.08, 0, -1.6))]
        add_curved_tube(verts, faces, mat_idx, ch_pts, [0.06, 0.045, 0.015], rad_segs=4, mat_id=0)

        # Giant golden fan crown
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.35)), 2.10, 2.10, 1.35, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Ancient_Ginkgo", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_ancient_ginkgo.blend"), str(TARGET_DIR / "canopy_ancient_ginkgo.glb"))
    return obj

# 18. canopy_sacred_bodhi (Ficus religiosa)
def build_canopy_sacred_bodhi():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Bodhi_Bark", (0.42, 0.40, 0.35, 1.0), roughness=0.72)
    mat_leaf = create_pbr_foliage_material("M_Bodhi_Foliage", (0.12, 0.52, 0.16, 1.0), sss_weight=0.50, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Sacred_Bodhi_Mesh")
    verts, faces, mat_idx = [], [], []

    # Buttressed fluted trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.12, 0.08, 2.5)),
        Vector((-0.06, 0.10, 5.2)),
        Vector((0.04, 0.02, 7.8))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.55, 0.42, 0.30, 0.18], rad_segs=8, mat_id=0)

    # Wide umbrella boughs
    tip = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.3
        bx, by = math.cos(ang)*3.0, math.sin(ang)*3.0
        b_pts = [tip, tip + Vector((bx*0.4, by*0.4, 0.7)), tip + Vector((bx, by, 0.9))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.15, 0.09, 0.035], rad_segs=5, mat_id=0)

        # Hanging aerial root filament
        r_pts = [b_pts[1], b_pts[1] + Vector((0, 0, -2.0)), b_pts[1] + Vector((0, 0, -3.8))]
        add_curved_tube(verts, faces, mat_idx, r_pts, [0.015, 0.010, 0.005], rad_segs=3, mat_id=0)

        # Shimmering heart-shaped drip-tip foliage crown
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.3)), 1.90, 1.90, 1.15, lat_steps=5, lon_steps=9, bump_amp=0.22, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Sacred_Bodhi", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_sacred_bodhi.blend"), str(TARGET_DIR / "canopy_sacred_bodhi.glb"))
    return obj

# 19. canopy_sugar_pine (Pinus lambertiana)
def build_canopy_sugar_pine():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_SugarPine_Bark", (0.35, 0.18, 0.12, 1.0), roughness=0.92, bump_strength=0.75)
    mat_needle = create_pbr_foliage_material("M_SugarPine_Foliage", (0.08, 0.26, 0.12, 1.0), sss_weight=0.28, roughness=0.55)
    mat_cone = create_pbr_bark_material("M_SugarPine_Cone", (0.28, 0.16, 0.10, 1.0), roughness=0.85)

    mesh = bpy.data.meshes.new("Flora_Sugar_Pine_Mesh")
    verts, faces, mat_idx = [], [], []

    # Gigantic columnar trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.06, -0.04, 4.0)),
        Vector((0.02, 0.05, 8.5)),
        Vector((0.00, 0.00, 13.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.55, 0.40, 0.28, 0.14], rad_segs=8, mat_id=0)

    # Horizontal open limbs with giant pendulous cones
    for b_i in range(6):
        ang = b_i * 2.0 * math.pi / 6 + 0.2
        bx, by = math.cos(ang)*2.6, math.sin(ang)*2.6
        z_b = 9.0 + (b_i % 3) * 1.5
        b_st = Vector((0, 0, z_b))
        b_pts = [b_st, b_st + Vector((bx*0.5, by*0.5, 0.1)), b_st + Vector((bx, by, 0.2))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.08, 0.05, 0.02], rad_segs=4, mat_id=0)

        # Foliage cloud
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.15)), 1.35, 1.35, 0.75, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

        # Gigantic pendulous pine cone hanging down from limb tip
        c_tip = b_pts[-1]
        add_foliage_clump(verts, faces, mat_idx, c_tip + Vector((0, 0, -0.35)), 0.10, 0.10, 0.35, lat_steps=4, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_needle, mat_cone], mat_idx)
    obj = bpy.data.objects.new("Flora_Sugar_Pine", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_sugar_pine.blend"), str(TARGET_DIR / "canopy_sugar_pine.glb"))
    return obj

# 20. canopy_bald_cypress (Taxodium distichum)
def build_canopy_bald_cypress():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_BaldCypress_Bark", (0.35, 0.22, 0.16, 1.0), roughness=0.90, bump_strength=0.7)
    mat_needle = create_pbr_foliage_material("M_BaldCypress_Foliage", (0.22, 0.45, 0.25, 1.0), sss_weight=0.45, roughness=0.45)

    mesh = bpy.data.meshes.new("Flora_Bald_Cypress_Mesh")
    verts, faces, mat_idx = [], [], []

    # Flared swollen buttress trunk base
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.08, 0.04, 1.8)),
        Vector((0.02, -0.05, 5.0)),
        Vector((0.00, 0.00, 9.0))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.65, 0.40, 0.26, 0.12], rad_segs=8, mat_id=0)

    # 6 Woody conical "cypress knees" (pneumatophores) rising from mud
    for k_i in range(6):
        k_ang = k_i * 2.0 * math.pi / 6 + 0.3
        kx, ky = math.cos(k_ang)*1.1, math.sin(k_ang)*1.1
        knee_pts = [Vector((kx, ky, 0)), Vector((kx*0.95, ky*0.95, 0.25)), Vector((kx*0.9, ky*0.9, 0.55))]
        add_curved_tube(verts, faces, mat_idx, knee_pts, [0.12, 0.09, 0.03], rad_segs=4, mat_id=0)

    # Soft feathery sage-green weeping boughs
    tip = trunk_pts[-1]
    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.35
        bx, by = math.cos(ang)*2.4, math.sin(ang)*2.4
        b_pts = [tip, tip + Vector((bx*0.5, by*0.5, 0.4)), tip + Vector((bx, by, 0.2))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.08, 0.05, 0.02], rad_segs=4, mat_id=0)

        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.2)), 1.50, 1.50, 0.95, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_needle], mat_idx)
    obj = bpy.data.objects.new("Flora_Bald_Cypress", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_bald_cypress.blend"), str(TARGET_DIR / "canopy_bald_cypress.glb"))
    return obj

# 21. canopy_rainforest_dipterocarp (Dipterocarpus grandiflorus)
def build_canopy_rainforest_dipterocarp():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Dipt_Bark", (0.32, 0.26, 0.20, 1.0), roughness=0.88, bump_strength=0.6)
    mat_leaf = create_pbr_foliage_material("M_Dipt_Foliage", (0.08, 0.38, 0.14, 1.0), sss_weight=0.38)

    mesh = bpy.data.meshes.new("Flora_Dipterocarp_Mesh")
    verts, faces, mat_idx = [], [], []

    # Straight tall clean cylinder trunk
    trunk_pts = [
        Vector((0, 0, 0)),
        Vector((0.04, -0.03, 4.0)),
        Vector((0.02, 0.03, 8.5)),
        Vector((0.00, 0.00, 13.5))
    ]
    add_curved_tube(verts, faces, mat_idx, trunk_pts, [0.45, 0.38, 0.32, 0.22], rad_segs=8, mat_id=0)

    # 4 Massive vertical buttress plank flanges at ground
    for p_i in range(4):
        ang = p_i * 2.0 * math.pi / 4
        px, py = math.cos(ang)*1.2, math.sin(ang)*1.2
        plank_pts = [Vector((0, 0, 2.8)), Vector((px*0.6, py*0.6, 1.4)), Vector((px, py, 0.0))]
        add_channeled_blade(verts, faces, mat_idx, plank_pts, [0.08, 0.10, 0.12], [0.02, 0.03, 0.04], mat_id=0)

    # High emergent cauliflower canopy above the rainforest
    apex = trunk_pts[-1]
    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.25
        bx, by = math.cos(ang)*2.5, math.sin(ang)*2.5
        b_pts = [apex, apex + Vector((bx*0.5, by*0.5, 0.8)), apex + Vector((bx, by, 1.4))]
        add_curved_tube(verts, faces, mat_idx, b_pts, [0.12, 0.08, 0.03], rad_segs=5, mat_id=0)

        # Billowing cauliflower foliage dome
        add_foliage_clump(verts, faces, mat_idx, b_pts[-1] + Vector((0, 0, 0.5)), 1.80, 1.80, 1.30, lat_steps=5, lon_steps=9, bump_amp=0.25, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Dipterocarp", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "canopy_rainforest_dipterocarp.blend"), str(TARGET_DIR / "canopy_rainforest_dipterocarp.glb"))
    return obj

def main():
    print(">>> Generating Canopy Trees (Part 2: Trees 12-21)...")
    builders = [
        ("tree_golden_larch", build_tree_golden_larch),
        ("tree_oriental_arborvitae", build_tree_oriental_arborvitae),
        ("canopy_ancient_banyan", build_canopy_ancient_banyan),
        ("canopy_cedar_lebanon", build_canopy_cedar_lebanon),
        ("canopy_ancient_ironwood", build_canopy_ancient_ironwood),
        ("canopy_ancient_ginkgo", build_canopy_ancient_ginkgo),
        ("canopy_sacred_bodhi", build_canopy_sacred_bodhi),
        ("canopy_sugar_pine", build_canopy_sugar_pine),
        ("canopy_bald_cypress", build_canopy_bald_cypress),
        ("canopy_rainforest_dipterocarp", build_canopy_rainforest_dipterocarp)
    ]
    for slug, fn in builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ Canopy Trees Part 2 generated successfully!")

if __name__ == "__main__":
    main()

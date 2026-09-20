"""
generate_understory_shrubs.py - Procedural 3D Engine for Understory Shrubs
Genesis Zero - Blender 5.2.1 LTS
Builds 12 realistic understory shrubs with clean BMesh topology & PBR materials.
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


def apply_smooth_and_materials(mesh, materials, mat_idx):
    for p in mesh.polygons:
        p.use_smooth = True
    for mat in materials:
        mesh.materials.append(mat)
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

TARGET_DIR = ROOT / "assets" / "flora" / "understory_shrubs"

# 1. shrub_wild_berry (Vaccinium vitis-idaea)
def build_shrub_wild_berry():
    clean_scene()
    mat_wood = create_pbr_bark_material("M_Berry_Wood", (0.28, 0.20, 0.14, 1.0), roughness=0.8)
    mat_leaf = create_pbr_foliage_material("M_Berry_Leaf", (0.12, 0.38, 0.16, 1.0), sss_weight=0.35, roughness=0.3)
    mat_fruit = create_pbr_foliage_material("M_Berry_Fruit", (0.85, 0.08, 0.12, 1.0), sss_color=(0.95, 0.15, 0.1), sss_weight=0.65, roughness=0.18)

    mesh = bpy.data.meshes.new("Flora_Wild_Berry_Mesh")
    verts, faces, mat_idx = [], [], []

    # 4 Low woody rhizome branches
    for b_i, (dx, dy, h) in enumerate([(0.08, 0.06, 0.38), (-0.09, 0.07, 0.35), (0.07, -0.09, 0.40), (-0.06, -0.08, 0.32)]):
        pts = [Vector((0, 0, 0)), Vector((dx*0.4, dy*0.4, h*0.4)), Vector((dx*0.8, dy*0.8, h*0.8)), Vector((dx, dy, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.012, 0.009, 0.006, 0.004], rad_segs=4, mat_id=0)

        # Leathery oval leaves
        for lv in range(6):
            l_ang = lv * 2.0 * math.pi / 6 + b_i
            t_pos = pts[1].lerp(pts[3], (lv + 1) / 7.0)
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.15)).normalized()
            add_cupped_petal(verts, faces, mat_idx, t_pos, fwd, Vector((0, 0, 1)), length=0.06, width=0.035, cup_depth=0.004, mat_id=1)

        # Clustered scarlet berries at branch tip
        tip = pts[-1]
        for _f_i, (bx, by, bz) in enumerate([(0.015, 0.01, -0.01), (-0.015, 0.015, -0.015), (0.01, -0.02, -0.02), (0, 0.02, -0.025)]):
            add_foliage_clump(verts, faces, mat_idx, tip + Vector((bx, by, bz)), 0.018, 0.018, 0.018, lat_steps=3, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_wood, mat_leaf, mat_fruit], mat_idx)
    obj = bpy.data.objects.new("Flora_Wild_Berry", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_wild_berry.blend"), str(TARGET_DIR / "shrub_wild_berry.glb"))
    return obj

# 2. shrub_alpine_rose (Rhododendron ferrugineum)
def build_shrub_alpine_rose():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Rhodo_Bark", (0.24, 0.18, 0.14, 1.0), roughness=0.85)
    mat_leaf = create_pbr_foliage_material("M_Rhodo_Leaf", (0.08, 0.32, 0.14, 1.0), sss_weight=0.35, roughness=0.4)
    mat_bloom = create_pbr_foliage_material("M_Rhodo_Bloom", (0.88, 0.15, 0.55, 1.0), sss_color=(0.98, 0.3, 0.7), sss_weight=0.65, roughness=0.28)

    mesh = bpy.data.meshes.new("Flora_Alpine_Rose_Mesh")
    verts, faces, mat_idx = [], [], []

    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((0, 0, 0.02)),
            Vector((dx*0.18, dy*0.18, 0.25)),
            Vector((dx*0.38, dy*0.38, 0.55)),
            Vector((dx*0.48, dy*0.48, 0.75))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.025, 0.018, 0.014, 0.010], rad_segs=5, mat_id=0)

        # Whorl of glossy dark green leaves
        tip = pts[-1]
        for lv in range(8):
            w_ang = lv * 2.0 * math.pi / 8
            fwd = Vector((math.cos(w_ang), math.sin(w_ang), 0.1)).normalized()
            add_cupped_petal(verts, faces, mat_idx, tip, fwd, Vector((0, 0, 1)), length=0.10, width=0.04, cup_depth=0.005, mat_id=1)

        # Terminal flower truss (3-4 funnel blooms)
        for fl in range(4):
            f_ang = fl * 2.0 * math.pi / 4 + 0.4
            fwd_fl = Vector((math.cos(f_ang), math.sin(f_ang), 0.6)).normalized()
            fl_stem = [tip, tip + fwd_fl*0.06]
            add_curved_tube(verts, faces, mat_idx, fl_stem, [0.006, 0.004], rad_segs=3, mat_id=0)
            # Flared bell mouth
            bell_tip = fl_stem[-1]
            add_curved_tube(verts, faces, mat_idx, [bell_tip, bell_tip + fwd_fl*0.05], [0.012, 0.038], rad_segs=6, mat_id=2, cap_start=True, cap_end=False)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_bloom], mat_idx)
    obj = bpy.data.objects.new("Flora_Alpine_Rose", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_alpine_rose.blend"), str(TARGET_DIR / "shrub_alpine_rose.glb"))
    return obj

# 3. shrub_elderberry (Sambucus nigra)
def build_shrub_elderberry():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Elder_Bark", (0.35, 0.32, 0.28, 1.0), roughness=0.82)
    mat_leaf = create_pbr_foliage_material("M_Elder_Leaf", (0.16, 0.42, 0.18, 1.0), sss_weight=0.4)
    mat_berry = create_pbr_foliage_material("M_Elder_Berry", (0.10, 0.06, 0.16, 1.0), sss_color=(0.2, 0.08, 0.3), sss_weight=0.3, roughness=0.2)

    mesh = bpy.data.meshes.new("Flora_Elderberry_Mesh")
    verts, faces, mat_idx = [], [], []

    for st_i, (dx, dy, h) in enumerate([(0.25, 0.15, 2.2), (-0.3, 0.2, 2.0), (0.1, -0.28, 2.4)]):
        pts = [
            Vector((0, 0, 0)),
            Vector((dx*0.3, dy*0.3, h*0.4)),
            Vector((dx*0.75, dy*0.75, h*0.8)),
            Vector((dx, dy, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.045, 0.032, 0.022, 0.014], rad_segs=6, mat_id=0)

        # Pinnate leaves along branch
        for lv in range(5):
            t = (lv + 1) / 6.0
            pos = pts[1].lerp(pts[3], t)
            l_ang = lv * 1.6 + st_i
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.1)).normalized()
            add_channeled_blade(verts, faces, mat_idx, [pos, pos + fwd*0.15, pos + fwd*0.35], [0.02, 0.09, 0.015], [0.003, 0.01, 0.002], mat_id=1)

        # Broad flat-topped elderberry umbrella umbel
        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.04)), 0.25, 0.25, 0.06, lat_steps=4, lon_steps=10, bump_amp=0.25, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_berry], mat_idx)
    obj = bpy.data.objects.new("Flora_Elderberry", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_elderberry.blend"), str(TARGET_DIR / "shrub_elderberry.glb"))
    return obj

# 4. shrub_stinging_nettle (Urtica dioica)
def build_shrub_stinging_nettle():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Nettle_Stem", (0.24, 0.45, 0.16, 1.0), sss_weight=0.35)
    mat_leaf = create_pbr_foliage_material("M_Nettle_Leaf", (0.18, 0.52, 0.14, 1.0), sss_weight=0.55, roughness=0.45)
    mat_spike = create_pbr_foliage_material("M_Nettle_Spike", (0.35, 0.55, 0.22, 1.0), sss_weight=0.45, roughness=0.6)

    mesh = bpy.data.meshes.new("Flora_Stinging_Nettle_Mesh")
    verts, faces, mat_idx = [], [], []

    for _s_i, (dx, dy, h) in enumerate([(0, 0, 1.1), (0.12, -0.08, 0.95), (-0.1, 0.09, 0.88)]):
        pts = [Vector((dx*0.2, dy*0.2, 0)), Vector((dx*0.5, dy*0.5, h*0.5)), Vector((dx, dy, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.015, 0.011, 0.007], rad_segs=4, mat_id=0)

        # Opposite decussate cordate leaves with saw margins
        for tier in range(6):
            z_t = 0.2 + tier * 0.14
            t_ang = tier * (math.pi * 0.5)
            for side in [-1, 1]:
                ang = t_ang + (0 if side == 1 else math.pi)
                fx, fy = math.cos(ang), math.sin(ang)
                p_st = Vector((dx*0.5*z_t/h + fx*0.01, dy*0.5*z_t/h + fy*0.01, z_t))
                fwd = Vector((fx, fy, -0.1)).normalized()
                add_cupped_petal(verts, faces, mat_idx, p_st, fwd, Vector((0, 0, 1)), length=0.12, width=0.08, cup_depth=0.008, mat_id=1)
                # Hanging flower spikelet
                sp_pts = [p_st, p_st + Vector((fx*0.03, fy*0.03, -0.05)), p_st + Vector((fx*0.04, fy*0.04, -0.09))]
                add_curved_tube(verts, faces, mat_idx, sp_pts, [0.004, 0.003, 0.002], rad_segs=3, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf, mat_spike], mat_idx)
    obj = bpy.data.objects.new("Flora_Stinging_Nettle", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_stinging_nettle.blend"), str(TARGET_DIR / "shrub_stinging_nettle.glb"))
    return obj

# 5. shrub_creeping_juniper (Juniperus procumbens)
def build_shrub_creeping_juniper():
    clean_scene()
    mat_wood = create_pbr_bark_material("M_Juniper_Wood", (0.32, 0.24, 0.18, 1.0), roughness=0.88)
    mat_foliage = create_pbr_foliage_material("M_Juniper_Needle", (0.12, 0.35, 0.30, 1.0), sss_weight=0.28, roughness=0.6)
    mat_berry = create_pbr_foliage_material("M_Juniper_Berry", (0.30, 0.45, 0.55, 1.0), sss_weight=0.45, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Creeping_Juniper_Mesh")
    verts, faces, mat_idx = [], [], []

    # 6 Prostrate spreading branches hugging ground
    for b_i in range(6):
        ang = b_i * 2.0 * math.pi / 6 + 0.15
        dx, dy = math.cos(ang), math.sin(ang)
        rad = 0.85 + 0.25 * (b_i % 3)
        pts = [
            Vector((0, 0, 0.04)),
            Vector((dx*0.25, dy*0.25, 0.14)),
            Vector((dx*0.60, dy*0.60, 0.16)),
            Vector((dx*rad, dy*rad, 0.08))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.035, 0.024, 0.016, 0.008], rad_segs=5, mat_id=0)

        # Dense tiered creeping foliage pads
        for t in [0.35, 0.65, 0.95]:
            p_pos = pts[0].lerp(pts[3], t)
            add_foliage_clump(verts, faces, mat_idx, p_pos + Vector((0, 0, 0.05)), 0.20, 0.20, 0.07, lat_steps=4, lon_steps=8, bump_amp=0.25, mat_id=1)

        # Frosted glaucous blue cones
        add_foliage_clump(verts, faces, mat_idx, pts[2] + Vector((0.03, -0.03, 0.05)), 0.022, 0.022, 0.022, lat_steps=3, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_wood, mat_foliage, mat_berry], mat_idx)
    obj = bpy.data.objects.new("Flora_Creeping_Juniper", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_creeping_juniper.blend"), str(TARGET_DIR / "shrub_creeping_juniper.glb"))
    return obj

# 6. shrub_birds_nest_fern (Asplenium nidus)
def build_shrub_birds_nest_fern():
    clean_scene()
    mat_core = create_pbr_bark_material("M_Fern_Nest_Core", (0.18, 0.14, 0.10, 1.0), roughness=0.92)
    mat_frond = create_pbr_foliage_material("M_Fern_Frond_Green", (0.15, 0.52, 0.12, 1.0), sss_weight=0.52, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Birds_Nest_Fern_Mesh")
    verts, faces, mat_idx = [], [], []

    # Central fibrous nest bowl
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.10)), 0.18, 0.18, 0.12, lat_steps=4, lon_steps=8, mat_id=0)

    # 12 Broad undulating sword fronds radiating outwards
    for f_i in range(12):
        ang = f_i * 2.0 * math.pi / 12
        dx, dy = math.cos(ang), math.sin(ang)
        f_pts = [
            Vector((0, 0, 0.12)),
            Vector((dx*0.20, dy*0.20, 0.38)),
            Vector((dx*0.48, dy*0.48, 0.72)),
            Vector((dx*0.68, dy*0.68, 0.85)),
            Vector((dx*0.82, dy*0.82, 0.75)) # tip curving gracefully down
        ]
        add_channeled_blade(verts, faces, mat_idx, f_pts, [0.04, 0.14, 0.18, 0.12, 0.02], [0.008, 0.025, 0.022, 0.010, 0.002], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_core, mat_frond], mat_idx)
    obj = bpy.data.objects.new("Flora_Birds_Nest_Fern", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_birds_nest_fern.blend"), str(TARGET_DIR / "shrub_birds_nest_fern.glb"))
    return obj

# 7. shrub_wild_hydrangea (Hydrangea macrophylla)
def build_shrub_wild_hydrangea():
    clean_scene()
    mat_wood = create_pbr_bark_material("M_Hydrangea_Wood", (0.30, 0.25, 0.20, 1.0), roughness=0.82)
    mat_leaf = create_pbr_foliage_material("M_Hydrangea_Leaf", (0.14, 0.44, 0.16, 1.0), sss_weight=0.40)
    mat_bloom = create_pbr_foliage_material("M_Hydrangea_Bloom", (0.35, 0.48, 0.88, 1.0), sss_color=(0.5, 0.6, 0.95), sss_weight=0.60, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Wild_Hydrangea_Mesh")
    verts, faces, mat_idx = [], [], []

    for b_i in range(5):
        ang = b_i * 2.0 * math.pi / 5 + 0.3
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((0, 0, 0)),
            Vector((dx*0.2, dy*0.2, 0.45)),
            Vector((dx*0.42, dy*0.42, 0.95)),
            Vector((dx*0.52, dy*0.52, 1.20))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.030, 0.022, 0.016, 0.010], rad_segs=5, mat_id=0)

        # Broad serrated ovate leaves
        for lv in range(4):
            l_pos = pts[1].lerp(pts[3], (lv+1)/5.0)
            l_ang = ang + (lv % 2) * 1.4 - 0.7
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.1)).normalized()
            add_cupped_petal(verts, faces, mat_idx, l_pos, fwd, Vector((0, 0, 1)), length=0.15, width=0.09, cup_depth=0.008, mat_id=1)

        # Massive globular mophead dome
        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.08)), 0.16, 0.16, 0.14, lat_steps=5, lon_steps=10, bump_freq=5.0, bump_amp=0.25, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_wood, mat_leaf, mat_bloom], mat_idx)
    obj = bpy.data.objects.new("Flora_Wild_Hydrangea", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_wild_hydrangea.blend"), str(TARGET_DIR / "shrub_wild_hydrangea.glb"))
    return obj

# 8. shrub_wild_blackberry (Rubus fruticosus)
def build_shrub_wild_blackberry():
    clean_scene()
    mat_cane = create_pbr_foliage_material("M_Bramble_Cane", (0.35, 0.30, 0.18, 1.0), sss_weight=0.25, roughness=0.6)
    mat_leaf = create_pbr_foliage_material("M_Bramble_Leaf", (0.15, 0.42, 0.14, 1.0), sss_weight=0.40)
    mat_berry = create_pbr_foliage_material("M_Bramble_Berry", (0.12, 0.05, 0.15, 1.0), sss_color=(0.25, 0.08, 0.25), sss_weight=0.45, roughness=0.2)

    mesh = bpy.data.meshes.new("Flora_Wild_Blackberry_Mesh")
    verts, faces, mat_idx = [], [], []

    for c_i in range(5):
        ang = c_i * 2.0 * math.pi / 5 + 0.25
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((0, 0, 0)),
            Vector((dx*0.3, dy*0.3, 0.65)),
            Vector((dx*0.7, dy*0.7, 1.25)),
            Vector((dx*1.0, dy*1.0, 0.85)), # arching down to ground
            Vector((dx*1.15, dy*1.15, 0.35))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.022, 0.016, 0.012, 0.008, 0.004], rad_segs=4, mat_id=0)

        # 3-5 foliate palmate leaves
        for lv in range(4):
            l_pos = pts[1].lerp(pts[3], (lv+1)/5.0)
            fwd = Vector((dx + math.sin(lv), dy + math.cos(lv), 0.2)).normalized()
            add_cupped_petal(verts, faces, mat_idx, l_pos, fwd, Vector((0, 0, 1)), length=0.11, width=0.07, cup_depth=0.006, mat_id=1)

        # Glossy aggregate fruit clusters along the arch
        add_foliage_clump(verts, faces, mat_idx, pts[2] + Vector((0, 0, 0.04)), 0.035, 0.035, 0.04, lat_steps=3, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_cane, mat_leaf, mat_berry], mat_idx)
    obj = bpy.data.objects.new("Flora_Wild_Blackberry", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_wild_blackberry.blend"), str(TARGET_DIR / "shrub_wild_blackberry.glb"))
    return obj

# 9. shrub_bay_laurel (Laurus nobilis)
def build_shrub_bay_laurel():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Laurel_Bark", (0.32, 0.28, 0.22, 1.0), roughness=0.85)
    mat_leaf = create_pbr_foliage_material("M_Laurel_Leaf", (0.09, 0.36, 0.12, 1.0), sss_weight=0.30, roughness=0.25)
    mat_flw = create_pbr_foliage_material("M_Laurel_Flw", (0.92, 0.90, 0.55, 1.0), sss_weight=0.55, roughness=0.4)

    mesh = bpy.data.meshes.new("Flora_Bay_Laurel_Mesh")
    verts, faces, mat_idx = [], [], []

    for b_i, (dx, dy, h) in enumerate([(0, 0, 2.3), (0.25, -0.2, 2.0), (-0.22, 0.24, 1.9), (0.2, 0.22, 1.8)]):
        pts = [Vector((dx*0.1, dy*0.1, 0)), Vector((dx*0.4, dy*0.4, h*0.5)), Vector((dx, dy, h))]
        add_curved_tube(verts, faces, mat_idx, pts, [0.040, 0.026, 0.014], rad_segs=5, mat_id=0)

        # Dense glossy leathery leaves
        for lv in range(8):
            h * (0.3 + 0.6 * (lv / 7.0))
            l_ang = lv * 2.4 + b_i
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), 0.2)).normalized()
            p_st = pts[1].lerp(pts[2], (lv+1)/9.0)
            add_channeled_blade(verts, faces, mat_idx, [p_st, p_st + fwd*0.08, p_st + fwd*0.18], [0.015, 0.045, 0.008], [0.003, 0.008, 0.001], mat_id=1)

        # Small creamy yellow flower clusters
        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.02)), 0.045, 0.045, 0.035, lat_steps=3, lon_steps=6, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_flw], mat_idx)
    obj = bpy.data.objects.new("Flora_Bay_Laurel", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_bay_laurel.blend"), str(TARGET_DIR / "shrub_bay_laurel.glb"))
    return obj

# 10. shrub_wild_briar_rose (Rosa canina)
def build_shrub_wild_briar_rose():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Briar_Stem", (0.30, 0.42, 0.18, 1.0), sss_weight=0.25, roughness=0.6)
    mat_leaf = create_pbr_foliage_material("M_Briar_Leaf", (0.16, 0.45, 0.15, 1.0), sss_weight=0.40)
    mat_petal = create_pbr_foliage_material("M_Briar_Petal", (0.96, 0.78, 0.85, 1.0), sss_color=(0.98, 0.85, 0.90), sss_weight=0.68, roughness=0.30)
    mat_hip = create_pbr_foliage_material("M_Briar_Hip", (0.88, 0.15, 0.08, 1.0), sss_weight=0.55, roughness=0.22)

    mesh = bpy.data.meshes.new("Flora_Briar_Rose_Mesh")
    verts, faces, mat_idx = [], [], []

    for b_i in range(4):
        ang = b_i * 2.0 * math.pi / 4 + 0.35
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((0, 0, 0)),
            Vector((dx*0.25, dy*0.25, 0.6)),
            Vector((dx*0.65, dy*0.65, 1.45)),
            Vector((dx*0.95, dy*0.95, 1.20)) # drooping tip
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.024, 0.018, 0.012, 0.006], rad_segs=4, mat_id=0)

        # Pinnate leaves
        for lv in range(4):
            p_pos = pts[1].lerp(pts[3], (lv+1)/5.0)
            fwd = Vector((dx*0.8 + math.sin(lv*2)*0.5, dy*0.8 + math.cos(lv*2)*0.5, 0.1)).normalized()
            add_cupped_petal(verts, faces, mat_idx, p_pos, fwd, Vector((0, 0, 1)), length=0.10, width=0.06, cup_depth=0.005, mat_id=1)

        tip = pts[-1]
        # 5-petaled wild rose
        for p in range(5):
            p_ang = p * 2.0 * math.pi / 5
            fwd = Vector((math.cos(p_ang), math.sin(p_ang), 0.2)).normalized()
            add_cupped_petal(verts, faces, mat_idx, tip + Vector((0, 0, 0.02)), fwd, Vector((0, 0, 1)), length=0.07, width=0.055, cup_depth=0.008, mat_id=2)

        # Scarlet rose hip nearby
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0.04, -0.04, -0.05)), 0.025, 0.025, 0.035, lat_steps=3, lon_steps=6, mat_id=3)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf, mat_petal, mat_hip], mat_idx)
    obj = bpy.data.objects.new("Flora_Briar_Rose", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_wild_briar_rose.blend"), str(TARGET_DIR / "shrub_wild_briar_rose.glb"))
    return obj

# 11. shrub_dwarf_bamboo (Sasa kurilensis)
def build_shrub_dwarf_bamboo():
    clean_scene()
    mat_culm = create_pbr_foliage_material("M_Bamboo_Culm", (0.35, 0.55, 0.18, 1.0), sss_weight=0.35, roughness=0.45)
    mat_leaf = create_pbr_foliage_material("M_Bamboo_Leaf", (0.18, 0.58, 0.15, 1.0), sss_weight=0.55, roughness=0.35)

    mesh = bpy.data.meshes.new("Flora_Dwarf_Bamboo_Mesh")
    verts, faces, mat_idx = [], [], []

    # 7 Slender segmented culms
    for c_i in range(7):
        ang = c_i * 2.0 * math.pi / 7 + random.uniform(-0.1, 0.1)
        dist = 0.08 + 0.10 * (c_i % 3)
        cx, cy = math.cos(ang)*dist, math.sin(ang)*dist
        h = 1.35 + 0.25 * ((c_i * 2) % 3)

        pts = [
            Vector((cx*0.2, cy*0.2, 0)),
            Vector((cx*0.6, cy*0.6, h*0.45)),
            Vector((cx, cy, h*0.85)),
            Vector((cx*1.2, cy*1.2, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.012, 0.010, 0.008, 0.005], rad_segs=4, mat_id=0)

        # Broad palmately tiered drooping leaves at top
        tip = pts[-1]
        for lv in range(6):
            l_ang = lv * 2.0 * math.pi / 6 + c_i
            fwd = Vector((math.cos(l_ang), math.sin(l_ang), -0.2)).normalized()
            add_channeled_blade(verts, faces, mat_idx, [tip, tip + fwd*0.10, tip + fwd*0.24], [0.015, 0.055, 0.008], [0.002, 0.006, 0.001], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_culm, mat_leaf], mat_idx)
    obj = bpy.data.objects.new("Flora_Dwarf_Bamboo", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_dwarf_bamboo.blend"), str(TARGET_DIR / "shrub_dwarf_bamboo.glb"))
    return obj

# 12. shrub_dogwood (Cornus sericea)
def build_shrub_dogwood():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Dogwood_Stem", (0.85, 0.15, 0.12, 1.0), sss_weight=0.45, roughness=0.35)
    mat_leaf = create_pbr_foliage_material("M_Dogwood_Leaf", (0.16, 0.48, 0.16, 1.0), sss_weight=0.42)
    mat_bloom = create_pbr_foliage_material("M_Dogwood_Bloom", (0.95, 0.96, 0.95, 1.0), sss_weight=0.60, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Dogwood_Mesh")
    verts, faces, mat_idx = [], [], []

    # 6 Radiant coral-red arching stems
    for b_i in range(6):
        ang = b_i * 2.0 * math.pi / 6 + 0.2
        dx, dy = math.cos(ang), math.sin(ang)
        pts = [
            Vector((0, 0, 0)),
            Vector((dx*0.25, dy*0.25, 0.65)),
            Vector((dx*0.65, dy*0.65, 1.35)),
            Vector((dx*0.95, dy*0.95, 1.80))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.024, 0.016, 0.011, 0.005], rad_segs=5, mat_id=0)

        # Opposite oval leaves with curved veins
        for lv in range(4):
            p_pos = pts[1].lerp(pts[3], (lv+1)/5.0)
            fwd = Vector((dx*0.7 + math.sin(lv)*0.6, dy*0.7 + math.cos(lv)*0.6, 0.15)).normalized()
            add_cupped_petal(verts, faces, mat_idx, p_pos, fwd, Vector((0, 0, 1)), length=0.12, width=0.07, cup_depth=0.006, mat_id=1)

        # Terminal flat clusters of white flowers / berries
        tip = pts[-1]
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.03)), 0.08, 0.08, 0.035, lat_steps=3, lon_steps=8, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_leaf, mat_bloom], mat_idx)
    obj = bpy.data.objects.new("Flora_Dogwood", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(TARGET_DIR / "shrub_dogwood.blend"), str(TARGET_DIR / "shrub_dogwood.glb"))
    return obj

def main():
    print(">>> Generating 12 Understory Shrubs...")
    builders = [
        ("shrub_wild_berry", build_shrub_wild_berry),
        ("shrub_alpine_rose", build_shrub_alpine_rose),
        ("shrub_elderberry", build_shrub_elderberry),
        ("shrub_stinging_nettle", build_shrub_stinging_nettle),
        ("shrub_creeping_juniper", build_shrub_creeping_juniper),
        ("shrub_birds_nest_fern", build_shrub_birds_nest_fern),
        ("shrub_wild_hydrangea", build_shrub_wild_hydrangea),
        ("shrub_wild_blackberry", build_shrub_wild_blackberry),
        ("shrub_bay_laurel", build_shrub_bay_laurel),
        ("shrub_wild_briar_rose", build_shrub_wild_briar_rose),
        ("shrub_dwarf_bamboo", build_shrub_dwarf_bamboo),
        ("shrub_dogwood", build_shrub_dogwood)
    ]
    for slug, fn in builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ All 12 Understory Shrubs generated successfully!")

if __name__ == "__main__":
    main()

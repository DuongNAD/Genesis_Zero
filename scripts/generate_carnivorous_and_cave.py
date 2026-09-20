"""
generate_carnivorous_and_cave.py - Procedural 3D Engine for Carnivorous Plants & Cave Flora
Genesis Zero - Blender 5.2.1 LTS
Builds 5 carnivorous plants and 4 cave bioluminescent species with clean BMesh topology & PBR materials.
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
    add_cupped_petal,
    add_curved_tube,
    add_foliage_clump,
    clean_scene,
    create_pbr_bark_material,
    create_pbr_emissive_material,
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

CARNIVOROUS_DIR = ROOT / "assets" / "flora" / "carnivorous_vines"
CAVE_DIR = ROOT / "assets" / "flora" / "cave_bioluminescent"

# -----------------------------------------------------------------------------
# CARNIVOROUS PLANTS (5 species)
# -----------------------------------------------------------------------------

# 1. carnivorous_sundew (Drosera capensis)
def build_carnivorous_sundew():
    clean_scene()
    mat_leaf = create_pbr_foliage_material("M_Sundew_Leaf", (0.22, 0.55, 0.16, 1.0), sss_weight=0.45)
    mat_dew = create_pbr_emissive_material("M_Sundew_Dew", (0.85, 0.15, 0.25, 1.0), (0.95, 0.2, 0.3, 1.0), emission_strength=1.5)

    mesh = bpy.data.meshes.new("Flora_Sundew_Mesh")
    verts, faces, mat_idx = [], [], []

    # Rosette of 12 strap leaves with incurved curling tips
    for lv in range(12):
        ang = lv * 2.0 * math.pi / 12
        dx, dy = math.cos(ang), math.sin(ang)
        l_pts = [
            Vector((0, 0, 0.02)),
            Vector((dx*0.08, dy*0.08, 0.08)),
            Vector((dx*0.18, dy*0.18, 0.18)),
            Vector((dx*0.24, dy*0.24, 0.26)),
            Vector((dx*0.22, dy*0.22, 0.29)) # incurved tip
        ]
        add_channeled_blade(verts, faces, mat_idx, l_pts, [0.012, 0.024, 0.022, 0.015, 0.005], [0.002, 0.004, 0.003, 0.002, 0.0005], mat_id=0)

        # Glandular tentacles with glistening dewdrops
        tip = l_pts[3]
        for _t_i, (tx, ty, tz) in enumerate([(0.01, 0.01, 0.015), (-0.01, 0.015, 0.012), (0.015, -0.01, 0.018)]):
            add_foliage_clump(verts, faces, mat_idx, tip + Vector((tx, ty, tz)), 0.008, 0.008, 0.008, lat_steps=3, lon_steps=5, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_leaf, mat_dew], mat_idx)
    obj = bpy.data.objects.new("Flora_Sundew", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CARNIVOROUS_DIR / "carnivorous_sundew.blend"), str(CARNIVOROUS_DIR / "carnivorous_sundew.glb"))
    return obj

# 2. carnivorous_jungle_liana (Liana gigantica)
def build_carnivorous_jungle_liana():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Liana_Bark", (0.28, 0.18, 0.10, 1.0), roughness=0.92, bump_strength=0.7)
    mat_leaf = create_pbr_foliage_material("M_Liana_Leaf", (0.12, 0.42, 0.15, 1.0), sss_weight=0.45)
    mat_flower = create_pbr_foliage_material("M_Liana_Flower", (0.95, 0.42, 0.08, 1.0), sss_color=(0.98, 0.55, 0.15), sss_weight=0.68, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Jungle_Liana_Mesh")
    verts, faces, mat_idx = [], [], []

    # Giant braided corkscrew cable vine spiraling upwards
    vine_pts = []
    n_segs = 20
    for s in range(n_segs):
        t = s / (n_segs - 1.0)
        z = t * 3.2
        ang = t * math.pi * 4.0 # 2 full turns
        vx = 0.28 * math.cos(ang)
        vy = 0.28 * math.sin(ang)
        vine_pts.append(Vector((vx, vy, z)))

    add_curved_tube(verts, faces, mat_idx, vine_pts, [0.045 - 0.02 * (i/n_segs) for i in range(n_segs)], rad_segs=6, mat_id=0)

    # Large cordate leaves along the vine
    for lv in range(8):
        pos = vine_pts[lv * 2 + 1]
        ang = lv * 1.8
        fwd = Vector((math.cos(ang), math.sin(ang), 0.1)).normalized()
        add_cupped_petal(verts, faces, mat_idx, pos, fwd, Vector((0, 0, 1)), length=0.18, width=0.12, cup_depth=0.015, mat_id=1)

    # Cluster of flame-orange trumpet flowers near top
    top_pos = vine_pts[-3]
    for fl in range(4):
        f_ang = fl * 2.0 * math.pi / 4 + 0.3
        fwd = Vector((math.cos(f_ang), math.sin(f_ang), 0.4)).normalized()
        add_curved_tube(verts, faces, mat_idx, [top_pos, top_pos + fwd*0.14], [0.015, 0.045], rad_segs=5, mat_id=2, cap_start=True, cap_end=False)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaf, mat_flower], mat_idx)
    obj = bpy.data.objects.new("Flora_Jungle_Liana", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CARNIVOROUS_DIR / "carnivorous_jungle_liana.blend"), str(CARNIVOROUS_DIR / "carnivorous_jungle_liana.glb"))
    return obj

# 3. carnivorous_cobra_lily (Darlingtonia californica)
def build_carnivorous_cobra_lily():
    clean_scene()
    mat_hood = create_pbr_foliage_material("M_Cobra_Hood", (0.55, 0.65, 0.22, 1.0), sss_color=(0.75, 0.85, 0.35), sss_weight=0.65, roughness=0.35)
    mat_fangs = create_pbr_foliage_material("M_Cobra_Fangs", (0.75, 0.14, 0.28, 1.0), sss_color=(0.9, 0.2, 0.35), sss_weight=0.60, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Cobra_Lily_Mesh")
    verts, faces, mat_idx = [], [], []

    # 3 Curved tubular pitchers swelling into cobra hood
    for _c_i, (dx, dy, h) in enumerate([(0.08, 0.06, 0.72), (-0.09, 0.07, 0.65), (0.05, -0.08, 0.68)]):
        pts = [
            Vector((dx*0.1, dy*0.1, 0)),
            Vector((dx*0.4, dy*0.4, h*0.4)),
            Vector((dx*0.8, dy*0.8, h*0.8)),
            Vector((dx*1.0, dy*1.0, h))
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.018, 0.024, 0.035, 0.045], rad_segs=5, mat_id=0)

        # Inflated cobra head hood dome at summit
        hood_center = pts[-1] + Vector((0.03, 0.02, 0.04))
        add_foliage_clump(verts, faces, mat_idx, hood_center, 0.075, 0.065, 0.065, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=0)

        # 2-lobed fishtail / snake fangs appendage hanging down from mouth
        fang_base = hood_center + Vector((0.05, 0, -0.04))
        for side in [-1, 1]:
            f_dir = Vector((0.02, side * 0.035, -0.08)).normalized()
            add_cupped_petal(verts, faces, mat_idx, fang_base, f_dir, Vector((0, 0, 1)), length=0.085, width=0.035, cup_depth=0.005, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_hood, mat_fangs], mat_idx)
    obj = bpy.data.objects.new("Flora_Cobra_Lily", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CARNIVOROUS_DIR / "carnivorous_cobra_lily.blend"), str(CARNIVOROUS_DIR / "carnivorous_cobra_lily.glb"))
    return obj

# 4. carnivorous_wild_orchid (Oncidium flexuosum)
def build_carnivorous_wild_orchid():
    clean_scene()
    mat_bulb = create_pbr_foliage_material("M_Orchid_Pseudobulb", (0.28, 0.52, 0.22, 1.0), sss_weight=0.45)
    mat_root = create_pbr_foliage_material("M_Orchid_Velamen_Root", (0.85, 0.86, 0.88, 1.0), roughness=0.6)
    mat_skirt = create_pbr_foliage_material("M_Orchid_Dancing_Skirt", (0.98, 0.85, 0.05, 1.0), sss_color=(0.99, 0.9, 0.2), sss_weight=0.70, roughness=0.25)

    mesh = bpy.data.meshes.new("Flora_Wild_Orchid_Mesh")
    verts, faces, mat_idx = [], [], []

    # Flattened pseudobulb base
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.08)), 0.055, 0.035, 0.08, lat_steps=4, lon_steps=8, mat_id=0)

    # White aerial velamen roots dangling
    for r in range(5):
        r_ang = r * 2.0 * math.pi / 5
        rx, ry = math.cos(r_ang)*0.03, math.sin(r_ang)*0.03
        r_pts = [Vector((rx, ry, 0.06)), Vector((rx*1.8, ry*1.8, -0.05)), Vector((rx*2.2, ry*2.2, -0.15))]
        add_curved_tube(verts, faces, mat_idx, r_pts, [0.008, 0.006, 0.004], rad_segs=3, mat_id=1)

    # Arching branching scape with dancing-lady yellow flowers
    scape_pts = [
        Vector((0, 0, 0.12)),
        Vector((0.08, 0.05, 0.32)),
        Vector((0.18, 0.12, 0.52)),
        Vector((0.28, 0.18, 0.65))
    ]
    add_curved_tube(verts, faces, mat_idx, scape_pts, [0.010, 0.008, 0.006, 0.004], rad_segs=4, mat_id=0)

    # 8 Dancing-lady flowers with wide ruffled yellow lip skirts
    for fl_i in range(8):
        t = (fl_i + 1) / 9.0
        pos = scape_pts[1].lerp(scape_pts[3], t)
        fl_ang = fl_i * 2.4
        fl_dx, fl_dy = math.cos(fl_ang)*0.08, math.sin(fl_ang)*0.08
        fl_tip = pos + Vector((fl_dx, fl_dy, 0.04))
        # Pedicel
        add_curved_tube(verts, faces, mat_idx, [pos, fl_tip], [0.003, 0.002], rad_segs=3, mat_id=0)
        # Broad ruffled dancing skirt lip
        fwd = Vector((fl_dx, fl_dy, -0.2)).normalized()
        add_cupped_petal(verts, faces, mat_idx, fl_tip, fwd, Vector((0, 0, 1)), length=0.075, width=0.068, cup_depth=0.008, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bulb, mat_root, mat_skirt], mat_idx)
    obj = bpy.data.objects.new("Flora_Wild_Orchid", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CARNIVOROUS_DIR / "carnivorous_wild_orchid.blend"), str(CARNIVOROUS_DIR / "carnivorous_wild_orchid.glb"))
    return obj

# 5. carnivorous_bladderwort (Utricularia vulgaris)
def build_carnivorous_bladderwort():
    clean_scene()
    mat_stem = create_pbr_foliage_material("M_Bladder_Stem", (0.22, 0.52, 0.25, 1.0), sss_weight=0.55)
    mat_trap = create_pbr_emissive_material("M_Bladder_Trap", (0.55, 0.88, 0.72, 1.0), (0.6, 0.95, 0.75, 1.0), emission_strength=1.2)
    mat_bloom = create_pbr_foliage_material("M_Bladder_Bloom", (0.96, 0.82, 0.08, 1.0), sss_color=(0.98, 0.9, 0.2), sss_weight=0.65, roughness=0.3)

    mesh = bpy.data.meshes.new("Flora_Bladderwort_Mesh")
    verts, faces, mat_idx = [], [], []

    # Submerged feathery floating stem with suction bladders
    sub_pts = [
        Vector((-0.25, -0.1, 0.05)),
        Vector((0, 0, 0.06)),
        Vector((0.25, 0.1, 0.05))
    ]
    add_curved_tube(verts, faces, mat_idx, sub_pts, [0.008, 0.007, 0.006], rad_segs=4, mat_id=0)

    # 12 Pearly translucent suction bladders
    for b_i in range(12):
        t = (b_i + 1) / 13.0
        pos = sub_pts[0].lerp(sub_pts[2], t)
        b_ang = b_i * 2.2
        bx, by = math.cos(b_ang)*0.035, math.sin(b_ang)*0.035
        add_foliage_clump(verts, faces, mat_idx, pos + Vector((bx, by, -0.015)), 0.014, 0.014, 0.014, lat_steps=3, lon_steps=6, mat_id=1)

    # Leafless scape rising above water
    scape_pts = [
        Vector((0, 0, 0.06)),
        Vector((0.02, -0.01, 0.22)),
        Vector((0.03, 0.02, 0.40))
    ]
    add_curved_tube(verts, faces, mat_idx, scape_pts, [0.007, 0.005, 0.003], rad_segs=4, mat_id=0)

    # 2 Spurred snapdragon-like yellow blooms
    tip = scape_pts[-1]
    for fl_i in range(2):
        fl_z = tip.z - fl_i * 0.06
        fl_fwd = Vector((1.0 if fl_i == 0 else -1.0, 0.2, 0.1)).normalized()
        add_cupped_petal(verts, faces, mat_idx, Vector((0.03, 0.02, fl_z)), fl_fwd, Vector((0, 0, 1)), length=0.06, width=0.045, cup_depth=0.008, mat_id=2)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_stem, mat_trap, mat_bloom], mat_idx)
    obj = bpy.data.objects.new("Flora_Bladderwort", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CARNIVOROUS_DIR / "carnivorous_bladderwort.blend"), str(CARNIVOROUS_DIR / "carnivorous_bladderwort.glb"))
    return obj

# -----------------------------------------------------------------------------
# CAVE BIOLUMINESCENT FLORA (4 species)
# -----------------------------------------------------------------------------

# 1. cave_luminescent_moss (Schistostega pennata)
def build_cave_luminescent_moss():
    clean_scene()
    mat_rock = create_pbr_bark_material("M_Cave_Rock", (0.18, 0.18, 0.20, 1.0), roughness=0.85)
    mat_glow = create_pbr_emissive_material("M_Goblin_Glow", (0.12, 0.75, 0.45, 1.0), (0.15, 0.95, 0.55, 1.0), emission_strength=3.5)

    mesh = bpy.data.meshes.new("Flora_Cave_Luminescent_Moss_Mesh")
    verts, faces, mat_idx = [], [], []

    # Wet cave rock substrate mound
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.05)), 0.55, 0.45, 0.10, lat_steps=4, lon_steps=8, bump_amp=0.20, mat_id=0)

    # 6 Glowing protonema retroreflective pads
    for _p_i, (px, py, rx, ry) in enumerate([
        (0.12, 0.08, 0.22, 0.18),
        (-0.15, 0.06, 0.24, 0.19),
        (0.04, -0.14, 0.20, 0.16),
        (-0.08, -0.10, 0.18, 0.15),
        (0.22, -0.06, 0.16, 0.14),
        (-0.20, -0.12, 0.15, 0.13)
    ]):
        add_foliage_clump(verts, faces, mat_idx, Vector((px, py, 0.08)), rx, ry, 0.04, lat_steps=3, lon_steps=7, bump_amp=0.15, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_rock, mat_glow], mat_idx)
    obj = bpy.data.objects.new("Flora_Cave_Luminescent_Moss", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CAVE_DIR / "cave_luminescent_moss.blend"), str(CAVE_DIR / "cave_luminescent_moss.glb"))
    return obj

# 2. cave_bracket_fungi (Trametes versicolor)
def build_cave_bracket_fungi():
    clean_scene()
    mat_rock = create_pbr_bark_material("M_Bracket_Rock", (0.22, 0.22, 0.24, 1.0), roughness=0.88)
    mat_cap = create_pbr_emissive_material("M_Bracket_Cap", (0.15, 0.45, 0.65, 1.0), (0.2, 0.8, 0.9, 1.0), emission_strength=4.0)

    mesh = bpy.data.meshes.new("Flora_Bracket_Fungi_Mesh")
    verts, faces, mat_idx = [], [], []

    # Cave rock face block
    add_foliage_clump(verts, faces, mat_idx, Vector((0, -0.15, 0.25)), 0.45, 0.18, 0.35, lat_steps=4, lon_steps=8, bump_amp=0.15, mat_id=0)

    # 6 Semicircular fan-shaped shelf brackets protruding in tiers
    bracket_configs = [
        # (center, length, width, angle)
        (Vector((-0.12, 0.02, 0.16)), 0.20, 0.28, 0.2),
        (Vector((0.14, 0.04, 0.22)), 0.24, 0.32, -0.15),
        (Vector((-0.04, 0.05, 0.32)), 0.26, 0.35, 0.1),
        (Vector((0.16, 0.03, 0.38)), 0.18, 0.26, -0.2),
        (Vector((-0.15, 0.01, 0.44)), 0.16, 0.22, 0.3),
        (Vector((0.02, 0.04, 0.48)), 0.20, 0.28, 0.05),
    ]

    for p_c, p_len, p_w, p_ang in bracket_configs:
        fwd = Vector((math.sin(p_ang), math.cos(p_ang), -0.05)).normalized()
        up = Vector((0, 0, 1))
        add_cupped_petal(verts, faces, mat_idx, p_c, fwd, up, length=p_len, width=p_w, cup_depth=-0.012, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_rock, mat_cap], mat_idx)
    obj = bpy.data.objects.new("Flora_Bracket_Fungi", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CAVE_DIR / "cave_bracket_fungi.blend"), str(CAVE_DIR / "cave_bracket_fungi.glb"))
    return obj

# 3. cave_jack_o_lantern (Omphalotus olearius)
def build_cave_jack_o_lantern():
    clean_scene()
    mat_cap = create_pbr_foliage_material("M_Jack_Cap", (0.88, 0.42, 0.08, 1.0), sss_color=(0.95, 0.55, 0.15), sss_weight=0.55, roughness=0.35)
    mat_glow = create_pbr_emissive_material("M_Jack_Gills", (0.15, 0.85, 0.55, 1.0), (0.2, 0.98, 0.65, 1.0), emission_strength=4.8)

    mesh = bpy.data.meshes.new("Flora_Jack_O_Lantern_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dense cluster of 6 funnel-shaped mushrooms
    for _m_i, (mx, my, mz, cap_r) in enumerate([
        (0, 0, 0.35, 0.12),
        (0.12, 0.08, 0.30, 0.10),
        (-0.10, 0.10, 0.28, 0.09),
        (0.08, -0.12, 0.26, 0.085),
        (-0.11, -0.09, 0.24, 0.08),
        (0.02, 0.14, 0.22, 0.075)
    ]):
        # Curved stipe
        stipe_pts = [
            Vector((0, 0, 0.02)),
            Vector((mx*0.5, my*0.5, mz*0.5)),
            Vector((mx, my, mz))
        ]
        add_curved_tube(verts, faces, mat_idx, stipe_pts, [0.022, 0.016, 0.012], rad_segs=5, mat_id=0)

        # Funnel cap (concave top) with radiating glowing gills
        tip = stipe_pts[-1]
        # Funnel cap
        add_foliage_clump(verts, faces, mat_idx, tip + Vector((0, 0, 0.02)), cap_r, cap_r, 0.028, lat_steps=3, lon_steps=8, mat_id=0)
        # Radiating decurrent gills under cap
        for gi in range(8):
            g_ang = gi * 2.0 * math.pi / 8
            gx, gy = math.cos(g_ang)*cap_r*0.8, math.sin(g_ang)*cap_r*0.8
            g_pts = [tip, tip + Vector((gx*0.4, gy*0.4, -0.02)), tip + Vector((gx, gy, 0.01))]
            add_channeled_blade(verts, faces, mat_idx, g_pts, [0.006, 0.012, 0.004], [0.001, 0.003, 0.0005], mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_cap, mat_glow], mat_idx)
    obj = bpy.data.objects.new("Flora_Jack_O_Lantern", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CAVE_DIR / "cave_jack_o_lantern.blend"), str(CAVE_DIR / "cave_jack_o_lantern.glb"))
    return obj

# 4. cave_ghost_pipe (Monotropa uniflora)
def build_cave_ghost_pipe():
    clean_scene()
    mat_soil = create_pbr_bark_material("M_Ghost_Soil", (0.16, 0.14, 0.12, 1.0), roughness=0.92)
    mat_wax = create_pbr_emissive_material("M_Ghost_Wax", (0.95, 0.96, 0.98, 1.0), (0.98, 0.98, 1.0, 1.0), emission_strength=1.2)

    mesh = bpy.data.meshes.new("Flora_Ghost_Pipe_Mesh")
    verts, faces, mat_idx = [], [], []

    # Dark humus forest soil mound
    add_foliage_clump(verts, faces, mat_idx, Vector((0, 0, 0.02)), 0.16, 0.15, 0.03, lat_steps=3, lon_steps=7, mat_id=0)

    # 5 Ghostly crystalline translucent white nodding stems
    for _s_i, (sx, sy, h) in enumerate([(0, 0, 0.22), (0.04, 0.03, 0.19), (-0.05, 0.02, 0.18), (0.02, -0.04, 0.17), (-0.03, -0.03, 0.15)]):
        pts = [
            Vector((sx, sy, 0.02)),
            Vector((sx + 0.01, sy, h*0.6)),
            Vector((sx + 0.02, sy + 0.01, h*0.9)),
            Vector((sx + 0.04, sy + 0.02, h)),
            Vector((sx + 0.05, sy + 0.02, h - 0.04)) # nodding downwards 180 deg
        ]
        add_curved_tube(verts, faces, mat_idx, pts, [0.012, 0.010, 0.008, 0.007, 0.005], rad_segs=4, mat_id=1)

        # Nodding bell flower at drooped tip
        tip = pts[-1]
        add_curved_tube(verts, faces, mat_idx, [tip, tip + Vector((0, 0, -0.035))], [0.008, 0.018], rad_segs=5, mat_id=1, cap_start=True, cap_end=False)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_soil, mat_wax], mat_idx)
    obj = bpy.data.objects.new("Flora_Ghost_Pipe", mesh)
    bpy.context.scene.collection.objects.link(obj)
    save_and_export(obj, str(CAVE_DIR / "cave_ghost_pipe.blend"), str(CAVE_DIR / "cave_ghost_pipe.glb"))
    return obj

def main():
    print(">>> Generating 5 Carnivorous Plants & 4 Cave Bioluminescent Flora...")
    c_builders = [
        ("carnivorous_sundew", build_carnivorous_sundew),
        ("carnivorous_jungle_liana", build_carnivorous_jungle_liana),
        ("carnivorous_cobra_lily", build_carnivorous_cobra_lily),
        ("carnivorous_wild_orchid", build_carnivorous_wild_orchid),
        ("carnivorous_bladderwort", build_carnivorous_bladderwort)
    ]
    for slug, fn in c_builders:
        print(f"--> Building {slug}...")
        fn()

    cave_builders = [
        ("cave_luminescent_moss", build_cave_luminescent_moss),
        ("cave_bracket_fungi", build_cave_bracket_fungi),
        ("cave_jack_o_lantern", build_cave_jack_o_lantern),
        ("cave_ghost_pipe", build_cave_ghost_pipe)
    ]
    for slug, fn in cave_builders:
        print(f"--> Building {slug}...")
        fn()
    print("✓ All 9 Carnivorous & Cave species generated successfully!")

if __name__ == "__main__":
    main()

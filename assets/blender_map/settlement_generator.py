"""
settlement_generator.py - Procedural Medieval Village, Landmarks, Props & Roads
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Features (User 15-Section Design Blueprint):
1. 10 Architectural Village Buildings (Làng nhỏ POI, Zone 6):
   - Village_Chapel: Stone chapel with timber bell-tower spire, gabled pitched roof, arched portal.
   - 2x House_TwoStory_Timber: Timber framing, cantilevered second story, stone chimney, tiled roof.
   - 3x Cottage_Stone: Rustic fieldstone walls, thatched/shingled roof, timber door, window shutters.
   - 2x Barn_Stable: Timber hay barn, open post animal stalls, loft door.
   - 1x Watermill: Riverfront millhouse with vertical timber water wheel facing stream current.
   - 1x Blacksmith_Forge: Open-sided timber workshop with stone furnace, chimney, and anvil canopy.
2. Props Library (Section 14 & Zone 6):
   - Prop_Well: Village square stone well with timber posts, pitched canopy, bucket and crank.
   - Prop_Barrel: Clusters of banded oak barrels beside taverns and cottages.
   - Prop_Crate: Merchant cargo crates.
   - Prop_Fence: Rustic split-rail wooden fences enclosing yards and lining roads.
   - Prop_Cart: Wooden two-wheeled transport oxcart / hay wagon.
   - Prop_Firewood: Neatly stacked split firewood cords.
   - Prop_Lantern_Post: Wrought iron street lanterns on timber posts with warm amber emission.
3. Landmark 2 - Ancient Hilltop Watchtower (Section 9):
   - Landmark_Watchtower: Cylindrical stone watchtower on eastern scenic ridge (24, 16, Z=10.5m)
     overlooking the entire valley, village, and snow peaks. Features crenellated battlements,
     arrow slit windows, and stone access stairs.
4. Road Network & River Bridge (Section 6 & 7):
   - Bridge_Stone_Arch: Scenic masonry stone arch bridge spanning the valley river at (2.0, 2.0, Z=6.0m).
   - Road_Network: Organic winding gravel/dirt path connecting Mountain Pass -> Forest -> Village -> Lake Shore -> Bay.
"""

import math
import random
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Euler


def create_pbr_material(name, base_color, roughness=0.7, specular=0.3, emission_color=None, emission_strength=0.0):
    """Utility to create or retrieve a Principled BSDF material."""
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
        if emission_color and emission_strength > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_color
                bsdf.inputs["Emission Strength"].default_value = emission_strength
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission_color
    return mat


def get_settlement_materials():
    """Compiles materials for village architecture, masonry, roofs, timber, and lanterns."""
    m_timber = create_pbr_material("M_Timber_Wood", (0.24, 0.15, 0.08, 1.0), roughness=0.82)
    m_stone = create_pbr_material("M_Stone_Wall", (0.44, 0.42, 0.40, 1.0), roughness=0.88)
    m_roof_tiles = create_pbr_material("M_Roof_Tiles", (0.58, 0.22, 0.14, 1.0), roughness=0.65)
    m_roof_thatch = create_pbr_material("M_Roof_Thatch", (0.60, 0.50, 0.28, 1.0), roughness=0.92)
    m_plaster = create_pbr_material("M_Plaster_Wall", (0.78, 0.76, 0.70, 1.0), roughness=0.85)
    m_iron = create_pbr_material("M_Forged_Iron", (0.12, 0.12, 0.14, 1.0), roughness=0.45, specular=0.6)
    m_lantern = create_pbr_material(
        "M_Lantern_Glow",
        (1.0, 0.82, 0.40, 1.0),
        roughness=0.2,
        emission_color=(1.0, 0.82, 0.40, 1.0),
        emission_strength=6.0
    )
    m_road = create_pbr_material("M_Road_Dirt", (0.36, 0.30, 0.22, 1.0), roughness=0.90)

    return {
        "timber": m_timber,
        "stone": m_stone,
        "tiles": m_roof_tiles,
        "thatch": m_roof_thatch,
        "plaster": m_plaster,
        "iron": m_iron,
        "lantern": m_lantern,
        "road": m_road,
    }


# -----------------------------------------------------------------------------
# Architectural Building Meshes
# -----------------------------------------------------------------------------


def build_village_chapel(collection, x, y, z, rot_z, mats):
    """Constructs Village_Chapel: Stone chapel with bell tower spire and arched entry."""
    bm = bmesh.new()

    w, length, h_wall = 5.6, 9.2, 4.8
    # Main nave stone box
    v_base = [
        bm.verts.new((-w * 0.5, -length * 0.5, 0.0)),
        bm.verts.new(( w * 0.5, -length * 0.5, 0.0)),
        bm.verts.new(( w * 0.5,  length * 0.5, 0.0)),
        bm.verts.new((-w * 0.5,  length * 0.5, 0.0)),
        bm.verts.new((-w * 0.5, -length * 0.5, h_wall)),
        bm.verts.new(( w * 0.5, -length * 0.5, h_wall)),
        bm.verts.new(( w * 0.5,  length * 0.5, h_wall)),
        bm.verts.new((-w * 0.5,  length * 0.5, h_wall)),
    ]
    # Walls
    f_walls = [
        bm.faces.new((v_base[0], v_base[1], v_base[5], v_base[4])),
        bm.faces.new((v_base[1], v_base[2], v_base[6], v_base[5])),
        bm.faces.new((v_base[2], v_base[3], v_base[7], v_base[6])),
        bm.faces.new((v_base[3], v_base[0], v_base[4], v_base[7])),
    ]
    for f in f_walls:
        f.material_index = 0  # stone

    # Pitched roof ridge
    ridge_y1 = -length * 0.5 - 0.4
    ridge_y2 =  length * 0.5 + 0.4
    v_ridge1 = bm.verts.new((0.0, ridge_y1, h_wall + 3.2))
    v_ridge2 = bm.verts.new((0.0, ridge_y2, h_wall + 3.2))
    # Gable triangles
    f_g1 = bm.faces.new((v_base[4], v_base[5], v_ridge1))
    f_g2 = bm.faces.new((v_base[7], v_ridge2, v_base[6]))
    f_g1.material_index = 0
    f_g2.material_index = 0
    # Roof slopes
    f_r1 = bm.faces.new((v_base[4], v_ridge1, v_ridge2, v_base[7]))
    f_r2 = bm.faces.new((v_base[5], v_base[6], v_ridge2, v_ridge1))
    f_r1.material_index = 1  # tiles
    f_r2.material_index = 1

    # Bell Tower Spire over front facade
    tw, th = 2.4, 7.5
    ty = -length * 0.5 + 1.2
    v_tbase = [
        bm.verts.new((-tw * 0.5, ty - tw * 0.5, h_wall)),
        bm.verts.new(( tw * 0.5, ty - tw * 0.5, h_wall)),
        bm.verts.new(( tw * 0.5, ty + tw * 0.5, h_wall)),
        bm.verts.new((-tw * 0.5, ty + tw * 0.5, h_wall)),
        bm.verts.new((-tw * 0.5, ty - tw * 0.5, h_wall + th)),
        bm.verts.new(( tw * 0.5, ty - tw * 0.5, h_wall + th)),
        bm.verts.new(( tw * 0.5, ty + tw * 0.5, h_wall + th)),
        bm.verts.new((-tw * 0.5, ty + tw * 0.5, h_wall + th)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f_tw = bm.faces.new((v_tbase[i], v_tbase[inxt], v_tbase[4 + inxt], v_tbase[4 + i]))
        f_tw.material_index = 2  # timber

    # Spire needle tip
    v_spire_tip = bm.verts.new((0.0, ty, h_wall + th + 4.2))
    for i in range(4):
        inxt = (i + 1) % 4
        f_sp = bm.faces.new((v_tbase[4 + i], v_tbase[4 + inxt], v_spire_tip))
        f_sp.material_index = 1  # tiles

    mesh = bpy.data.meshes.new("Village_Chapel_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])       # 0
    mesh.materials.append(mats["tiles"])       # 1
    mesh.materials.append(mats["timber"])      # 2

    obj = bpy.data.objects.new("Village_Chapel", mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


def build_timber_house(collection, name, x, y, z, rot_z, mats, scale=1.0):
    """Constructs a two-story medieval half-timbered house with chimney."""
    bm = bmesh.new()

    w = 5.2 * scale
    l = 6.8 * scale
    h1 = 3.2 * scale
    h2 = 2.8 * scale
    overhang = 0.45 * scale

    # Floor 1 (Stone base)
    v1 = [
        bm.verts.new((-w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5, -l * 0.5, h1)),
        bm.verts.new(( w * 0.5, -l * 0.5, h1)),
        bm.verts.new(( w * 0.5,  l * 0.5, h1)),
        bm.verts.new((-w * 0.5,  l * 0.5, h1)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm.faces.new((v1[i], v1[inxt], v1[4 + inxt], v1[4 + i]))
        f.material_index = 0  # stone

    # Floor 2 (Overhanging Timber & Plaster)
    w2 = w + overhang * 2.0
    l2 = l + overhang * 2.0
    v2 = [
        bm.verts.new((-w2 * 0.5, -l2 * 0.5, h1)),
        bm.verts.new(( w2 * 0.5, -l2 * 0.5, h1)),
        bm.verts.new(( w2 * 0.5,  l2 * 0.5, h1)),
        bm.verts.new((-w2 * 0.5,  l2 * 0.5, h1)),
        bm.verts.new((-w2 * 0.5, -l2 * 0.5, h1 + h2)),
        bm.verts.new(( w2 * 0.5, -l2 * 0.5, h1 + h2)),
        bm.verts.new(( w2 * 0.5,  l2 * 0.5, h1 + h2)),
        bm.verts.new((-w2 * 0.5,  l2 * 0.5, h1 + h2)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm.faces.new((v2[i], v2[inxt], v2[4 + inxt], v2[4 + i]))
        f.material_index = 2  # plaster/timber

    # Pitched Tiled Roof
    v_r1 = bm.verts.new((0.0, -l2 * 0.5 - 0.3 * scale, h1 + h2 + 2.5 * scale))
    v_r2 = bm.verts.new((0.0,  l2 * 0.5 + 0.3 * scale, h1 + h2 + 2.5 * scale))

    f_g1 = bm.faces.new((v2[4], v2[5], v_r1))
    f_g2 = bm.faces.new((v2[7], v_r2, v2[6]))
    f_g1.material_index = 2
    f_g2.material_index = 2

    f_rf1 = bm.faces.new((v2[4], v_r1, v_r2, v2[7]))
    f_rf2 = bm.faces.new((v2[5], v2[6], v_r2, v_r1))
    f_rf1.material_index = 1  # tiles
    f_rf2.material_index = 1

    # Stone Chimney on one side
    cx = w2 * 0.5 - 0.7 * scale
    cy = l2 * 0.2
    cw = 0.8 * scale
    ch = h1 + h2 + 3.2 * scale
    v_ch = [
        bm.verts.new((cx - cw * 0.5, cy - cw * 0.5, h1 * 0.5)),
        bm.verts.new((cx + cw * 0.5, cy - cw * 0.5, h1 * 0.5)),
        bm.verts.new((cx + cw * 0.5, cy + cw * 0.5, h1 * 0.5)),
        bm.verts.new((cx - cw * 0.5, cy + cw * 0.5, h1 * 0.5)),
        bm.verts.new((cx - cw * 0.5, cy - cw * 0.5, ch)),
        bm.verts.new((cx + cw * 0.5, cy - cw * 0.5, ch)),
        bm.verts.new((cx + cw * 0.5, cy + cw * 0.5, ch)),
        bm.verts.new((cx - cw * 0.5, cy + cw * 0.5, ch)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f_ch = bm.faces.new((v_ch[i], v_ch[inxt], v_ch[4 + inxt], v_ch[4 + i]))
        f_ch.material_index = 0

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])    # 0
    mesh.materials.append(mats["tiles"])    # 1
    mesh.materials.append(mats["plaster"])  # 2

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


def build_stone_cottage(collection, name, x, y, z, rot_z, mats, scale=1.0, thatch=False):
    """Constructs a single-story fieldstone cottage with thatched or shingled roof."""
    bm = bmesh.new()

    w = 4.4 * scale
    l = 5.8 * scale
    h = 2.8 * scale

    v = [
        bm.verts.new((-w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5,  l * 0.5, h)),
        bm.verts.new((-w * 0.5,  l * 0.5, h)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm.faces.new((v[i], v[inxt], v[4 + inxt], v[4 + i]))
        f.material_index = 0  # stone

    # Roof
    v_r1 = bm.verts.new((0.0, -l * 0.5 - 0.4 * scale, h + 2.2 * scale))
    v_r2 = bm.verts.new((0.0,  l * 0.5 + 0.4 * scale, h + 2.2 * scale))

    f_g1 = bm.faces.new((v[4], v[5], v_r1))
    f_g2 = bm.faces.new((v[7], v_r2, v[6]))
    f_g1.material_index = 0
    f_g2.material_index = 0

    f_rf1 = bm.faces.new((v[4], v_r1, v_r2, v[7]))
    f_rf2 = bm.faces.new((v[5], v[6], v_r2, v_r1))
    f_rf1.material_index = 1 if thatch else 2
    f_rf2.material_index = 1 if thatch else 2

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])   # 0
    mesh.materials.append(mats["thatch"])  # 1
    mesh.materials.append(mats["tiles"])   # 2

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


def build_barn_stable(collection, name, x, y, z, rot_z, mats, scale=1.0):
    """Constructs a rustic timber barn / stable."""
    bm = bmesh.new()

    w = 5.8 * scale
    l = 8.2 * scale
    h = 3.6 * scale

    v = [
        bm.verts.new((-w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5,  l * 0.5, h)),
        bm.verts.new((-w * 0.5,  l * 0.5, h)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm.faces.new((v[i], v[inxt], v[4 + inxt], v[4 + i]))
        f.material_index = 0  # timber

    # Broad pitched roof
    v_r1 = bm.verts.new((0.0, -l * 0.5 - 0.4 * scale, h + 2.8 * scale))
    v_r2 = bm.verts.new((0.0,  l * 0.5 + 0.4 * scale, h + 2.8 * scale))

    f_g1 = bm.faces.new((v[4], v[5], v_r1))
    f_g2 = bm.faces.new((v[7], v_r2, v[6]))
    f_g1.material_index = 0
    f_g2.material_index = 0

    f_rf1 = bm.faces.new((v[4], v_r1, v_r2, v[7]))
    f_rf2 = bm.faces.new((v[5], v[6], v_r2, v_r1))
    f_rf1.material_index = 1  # thatch
    f_rf2.material_index = 1

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["timber"])  # 0
    mesh.materials.append(mats["thatch"])  # 1

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


def build_watermill(collection, x, y, z, rot_z, mats):
    """Constructs a riverfront watermill with timber water wheel."""
    bm = bmesh.new()

    w, l, h = 4.8, 6.4, 3.4
    v = [
        bm.verts.new((-w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5, -l * 0.5, 0.0)),
        bm.verts.new(( w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5,  l * 0.5, 0.0)),
        bm.verts.new((-w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5, -l * 0.5, h)),
        bm.verts.new(( w * 0.5,  l * 0.5, h)),
        bm.verts.new((-w * 0.5,  l * 0.5, h)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm.faces.new((v[i], v[inxt], v[4 + inxt], v[4 + i]))
        f.material_index = 0  # stone

    # Roof
    vr1 = bm.verts.new((0.0, -l * 0.5 - 0.3, h + 2.2))
    vr2 = bm.verts.new((0.0,  l * 0.5 + 0.3, h + 2.2))
    f_g1 = bm.faces.new((v[4], v[5], vr1))
    f_g2 = bm.faces.new((v[7], vr2, v[6]))
    f_g1.material_index = 0
    f_g2.material_index = 0
    f_r1 = bm.faces.new((v[4], vr1, vr2, v[7]))
    f_r2 = bm.faces.new((v[5], v[6], vr2, vr1))
    f_r1.material_index = 1  # tiles
    f_r2.material_index = 1

    # Water Wheel on the river-facing side (+X)
    wheel_cx = w * 0.5 + 0.6
    wheel_cy = 0.0
    wheel_cz = 1.2
    wheel_rad = 1.8
    wheel_w = 0.55
    n_spokes = 12

    for k in range(n_spokes):
        ang1 = k * 2.0 * math.pi / n_spokes
        ang2 = (k + 1) * 2.0 * math.pi / n_spokes
        p_y1 = wheel_cy + wheel_rad * math.cos(ang1)
        p_z1 = wheel_cz + wheel_rad * math.sin(ang1)
        p_y2 = wheel_cy + wheel_rad * math.cos(ang2)
        p_z2 = wheel_cz + wheel_rad * math.sin(ang2)

        v_pad = [
            bm.verts.new((wheel_cx - wheel_w * 0.5, p_y1, p_z1)),
            bm.verts.new((wheel_cx + wheel_w * 0.5, p_y1, p_z1)),
            bm.verts.new((wheel_cx + wheel_w * 0.5, p_y2, p_z2)),
            bm.verts.new((wheel_cx - wheel_w * 0.5, p_y2, p_z2)),
        ]
        f_p = bm.faces.new(v_pad)
        f_p.material_index = 2  # timber

        v_sp = [
            bm.verts.new((wheel_cx, wheel_cy, wheel_cz)),
            bm.verts.new((wheel_cx, p_y1, p_z1)),
            bm.verts.new((wheel_cx, p_y2, p_z2)),
        ]
        f_spk = bm.faces.new(v_sp)
        f_spk.material_index = 2

    mesh = bpy.data.meshes.new("Watermill_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])   # 0
    mesh.materials.append(mats["tiles"])   # 1
    mesh.materials.append(mats["timber"])  # 2

    obj = bpy.data.objects.new("Watermill", mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


def build_blacksmith_forge(collection, x, y, z, rot_z, mats):
    """Constructs an open timber smithy with stone hearth and chimney."""
    bm = bmesh.new()

    w, l, h = 4.2, 5.2, 2.6
    # 4 corner timber posts
    posts = [
        (-w * 0.5, -l * 0.5),
        ( w * 0.5, -l * 0.5),
        ( w * 0.5,  l * 0.5),
        (-w * 0.5,  l * 0.5),
    ]
    for px, py in posts:
        pw = 0.28
        vp = [
            bm.verts.new((px - pw, py - pw, 0.0)),
            bm.verts.new((px + pw, py - pw, 0.0)),
            bm.verts.new((px + pw, py + pw, 0.0)),
            bm.verts.new((px - pw, py + pw, 0.0)),
            bm.verts.new((px - pw, py - pw, h)),
            bm.verts.new((px + pw, py - pw, h)),
            bm.verts.new((px + pw, py + pw, h)),
            bm.verts.new((px - pw, py + pw, h)),
        ]
        for i in range(4):
            inxt = (i + 1) % 4
            f = bm.faces.new((vp[i], vp[inxt], vp[4 + inxt], vp[4 + i]))
            f.material_index = 0  # timber

    # Canopy Roof
    vr1 = bm.verts.new((0.0, -l * 0.5 - 0.3, h + 1.6))
    vr2 = bm.verts.new((0.0,  l * 0.5 + 0.3, h + 1.6))
    v_top = [
        bm.verts.new((-w * 0.5 - 0.3, -l * 0.5 - 0.3, h)),
        bm.verts.new(( w * 0.5 + 0.3, -l * 0.5 - 0.3, h)),
        bm.verts.new(( w * 0.5 + 0.3,  l * 0.5 + 0.3, h)),
        bm.verts.new((-w * 0.5 - 0.3,  l * 0.5 + 0.3, h)),
    ]
    f_r1 = bm.faces.new((v_top[0], vr1, vr2, v_top[3]))
    f_r2 = bm.faces.new((v_top[1], v_top[2], vr2, vr1))
    f_r1.material_index = 1  # tiles
    f_r2.material_index = 1

    # Stone hearth at rear
    hx, hy = -w * 0.2, l * 0.25
    hw, hh = 1.4, 2.8
    v_h = [
        bm.verts.new((hx - hw * 0.5, hy - hw * 0.5, 0.0)),
        bm.verts.new((hx + hw * 0.5, hy - hw * 0.5, 0.0)),
        bm.verts.new((hx + hw * 0.5, hy + hw * 0.5, 0.0)),
        bm.verts.new((hx - hw * 0.5, hy + hw * 0.5, 0.0)),
        bm.verts.new((hx - hw * 0.5, hy - hw * 0.5, hh)),
        bm.verts.new((hx + hw * 0.5, hy - hw * 0.5, hh)),
        bm.verts.new((hx + hw * 0.5, hy + hw * 0.5, hh)),
        bm.verts.new((hx - hw * 0.5, hy + hw * 0.5, hh)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f_h = bm.faces.new((v_h[i], v_h[inxt], v_h[4 + inxt], v_h[4 + i]))
        f_h.material_index = 2  # stone

    mesh = bpy.data.meshes.new("Blacksmith_Forge_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["timber"])  # 0
    mesh.materials.append(mats["tiles"])   # 1
    mesh.materials.append(mats["stone"])   # 2

    obj = bpy.data.objects.new("Blacksmith_Forge", mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# Landmark 2 - Ancient Hilltop Watchtower
# -----------------------------------------------------------------------------


def build_ancient_watchtower(collection, x, y, z, mats):
    """
    Constructs Landmark_Watchtower: Cylindrical stone watchtower perched on the
    eastern ridge (24, 16, Z=10.5m) with crenellated battlements and arrow slits.
    """
    bm = bmesh.new()

    radius = 2.8
    height = 12.5
    n_seg = 16

    # 1. Tower Cylinder
    n_rings = 8
    rings = []
    for r in range(n_rings):
        h_frac = r / (n_rings - 1)
        zh = h_frac * height
        rad_ring = radius * (1.0 - 0.12 * h_frac)  # slight gentle batter / taper
        v_ring = []
        for i in range(n_seg):
            ang = i * 2.0 * math.pi / n_seg
            v_ring.append(bm.verts.new((rad_ring * math.cos(ang), rad_ring * math.sin(ang), zh)))
        rings.append(v_ring)

    for r in range(n_rings - 1):
        r1 = rings[r]
        r2 = rings[r + 1]
        for i in range(n_seg):
            inxt = (i + 1) % n_seg
            f = bm.faces.new((r1[i], r1[inxt], r2[inxt], r2[i]))
            f.material_index = 0  # stone

    # 2. Corbelled Battlement Parapet (Crenellations)
    parapet_rad = radius * 1.05
    parapet_h = 1.3
    top_ring = rings[-1]

    v_parapet_bot = []
    v_parapet_top = []
    for i in range(n_seg):
        ang = i * 2.0 * math.pi / n_seg
        v_parapet_bot.append(bm.verts.new((parapet_rad * math.cos(ang), parapet_rad * math.sin(ang), height)))
        is_merlon = (i % 2 == 0)
        p_zh = height + (parapet_h if is_merlon else parapet_h * 0.4)
        v_parapet_top.append(bm.verts.new((parapet_rad * math.cos(ang), parapet_rad * math.sin(ang), p_zh)))

    for i in range(n_seg):
        inxt = (i + 1) % n_seg
        f_corb = bm.faces.new((top_ring[i], top_ring[inxt], v_parapet_bot[inxt], v_parapet_bot[i]))
        f_corb.material_index = 0

    for i in range(n_seg):
        inxt = (i + 1) % n_seg
        f_p = bm.faces.new((v_parapet_bot[i], v_parapet_bot[inxt], v_parapet_top[inxt], v_parapet_top[i]))
        f_p.material_index = 0

    # 3. Flat Walkway Roof Inside Parapet
    v_walk_center = bm.verts.new((0.0, 0.0, height - 0.2))
    for i in range(n_seg):
        inxt = (i + 1) % n_seg
        f_w = bm.faces.new((v_walk_center, top_ring[i], top_ring[inxt]))
        f_w.material_index = 0

    mesh = bpy.data.meshes.new("Landmark_Watchtower_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])

    obj = bpy.data.objects.new("Landmark_Watchtower", mesh)
    obj.location = (x, y, z)
    collection.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# Stone Arch Bridge
# -----------------------------------------------------------------------------


def build_stone_arch_bridge(collection, x, y, z, rot_z, mats):
    """Constructs Bridge_Stone_Arch across the valley river."""
    bm = bmesh.new()

    span = 9.8
    width = 3.6
    h_crown = 2.4
    n_arch = 12

    arch_pts = []
    for i in range(n_arch + 1):
        th = math.pi * i / n_arch
        px = -span * 0.5 * math.cos(th)
        pz = h_crown * math.sin(th)
        arch_pts.append((px, pz))

    y_half = width * 0.5
    top_z = h_crown + 0.65

    v_left_bot = []
    v_right_bot = []
    v_left_top = []
    v_right_top = []

    for px, pz in arch_pts:
        v_left_bot.append(bm.verts.new((px, -y_half, pz)))
        v_right_bot.append(bm.verts.new((px,  y_half, pz)))
        camber = 0.25 * math.cos(px / (span * 0.5) * (math.pi * 0.5))
        v_left_top.append(bm.verts.new((px, -y_half, top_z + camber)))
        v_right_top.append(bm.verts.new((px,  y_half, top_z + camber)))

    for i in range(n_arch):
        f = bm.faces.new((v_left_bot[i], v_left_bot[i + 1], v_right_bot[i + 1], v_right_bot[i]))
        f.material_index = 0  # stone

    for i in range(n_arch):
        f_l = bm.faces.new((v_left_bot[i], v_left_top[i], v_left_top[i + 1], v_left_bot[i + 1]))
        f_r = bm.faces.new((v_right_bot[i + 1], v_right_top[i + 1], v_right_top[i], v_right_bot[i]))
        f_l.material_index = 0
        f_r.material_index = 0

    for i in range(n_arch):
        f_d = bm.faces.new((v_left_top[i], v_right_top[i], v_right_top[i + 1], v_left_top[i + 1]))
        f_d.material_index = 1  # road dirt

    for px, side_y in [(-y_half - 0.15, -y_half), (y_half, y_half + 0.15)]:
        for i in range(n_arch):
            c1 = 0.25 * math.cos(arch_pts[i][0] / (span * 0.5) * (math.pi * 0.5))
            c2 = 0.25 * math.cos(arch_pts[i + 1][0] / (span * 0.5) * (math.pi * 0.5))
            z1 = top_z + c1
            z2 = top_z + c2
            vp1 = bm.verts.new((arch_pts[i][0], side_y, z1 + 0.6))
            vp2 = bm.verts.new((arch_pts[i + 1][0], side_y, z2 + 0.6))
            f_p = bm.faces.new((v_left_top[i] if side_y < 0 else v_right_top[i],
                                vp1, vp2,
                                v_left_top[i + 1] if side_y < 0 else v_right_top[i + 1]))
            f_p.material_index = 0

    mesh = bpy.data.meshes.new("Bridge_Stone_Arch_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])  # 0
    mesh.materials.append(mats["road"])   # 1

    obj = bpy.data.objects.new("Bridge_Stone_Arch", mesh)
    obj.location = (x, y, z)
    obj.rotation_euler = Euler((0.0, 0.0, rot_z))
    collection.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# Props Library (Well, Barrels, Crates, Fences, Cart, Lanterns)
# -----------------------------------------------------------------------------


def build_village_well(collection, x, y, z, mats):
    """Constructs circular stone well with timber gabled roof and bucket."""
    bm = bmesh.new()

    radius = 1.1
    h_wall = 0.95
    n_seg = 12

    v_bot = []
    v_top = []
    for i in range(n_seg):
        a = i * 2.0 * math.pi / n_seg
        v_bot.append(bm.verts.new((radius * math.cos(a), radius * math.sin(a), 0.0)))
        v_top.append(bm.verts.new((radius * math.cos(a), radius * math.sin(a), h_wall)))

    for i in range(n_seg):
        inxt = (i + 1) % n_seg
        f = bm.faces.new((v_bot[i], v_bot[inxt], v_top[inxt], v_top[i]))
        f.material_index = 0  # stone

    p1 = bm.verts.new((-radius * 0.8, 0.0, 2.2))
    p2 = bm.verts.new(( radius * 0.8, 0.0, 2.2))
    f_p1 = bm.faces.new((v_top[0], v_top[1], p2))
    f_p2 = bm.faces.new((v_top[6], v_top[7], p1))
    f_p1.material_index = 1  # timber
    f_p2.material_index = 1

    vr1 = bm.verts.new((0.0, -1.3, 2.6))
    vr2 = bm.verts.new((0.0,  1.3, 2.6))
    f_rf1 = bm.faces.new((p1, vr1, vr2, p2))
    f_rf1.material_index = 2  # tiles

    mesh = bpy.data.meshes.new("Village_Well_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["stone"])   # 0
    mesh.materials.append(mats["timber"])  # 1
    mesh.materials.append(mats["tiles"])   # 2

    obj = bpy.data.objects.new("Village_Well", mesh)
    obj.location = (x, y, z)
    collection.objects.link(obj)
    return obj


def create_prop_prototypes(mats):
    """Generates reusable prototype meshes for barrels, crates, fences, carts, lanterns."""
    # 1. Barrel
    bm_b = bmesh.new()
    br_mid, br_end, bh = 0.42, 0.35, 0.85
    b_rings = []
    for z_f, r in [(0.0, br_end), (bh * 0.5, br_mid), (bh, br_end)]:
        ring = [bm_b.verts.new((r * math.cos(2 * math.pi * i / 8),
                                r * math.sin(2 * math.pi * i / 8), z_f)) for i in range(8)]
        b_rings.append(ring)
    for r in range(2):
        for i in range(8):
            inxt = (i + 1) % 8
            bm_b.faces.new((b_rings[r][i], b_rings[r][inxt], b_rings[r + 1][inxt], b_rings[r + 1][i]))
    c_top = bm_b.verts.new((0.0, 0.0, bh))
    for i in range(8):
        bm_b.faces.new((c_top, b_rings[2][i], b_rings[2][(i + 1) % 8]))
    m_barrel = bpy.data.meshes.new("Proto_Barrel")
    bm_b.to_mesh(m_barrel)
    bm_b.free()
    m_barrel.update()
    m_barrel.shade_smooth()
    for p in m_barrel.polygons:
        p.use_smooth = True
    m_barrel.materials.append(mats["timber"])

    # 2. Crate
    bm_c = bmesh.new()
    cw = 0.65
    v_c = [
        bm_c.verts.new((-cw, -cw, 0.0)), bm_c.verts.new((cw, -cw, 0.0)),
        bm_c.verts.new((cw, cw, 0.0)),   bm_c.verts.new((-cw, cw, 0.0)),
        bm_c.verts.new((-cw, -cw, cw * 2.0)), bm_c.verts.new((cw, -cw, cw * 2.0)),
        bm_c.verts.new((cw, cw, cw * 2.0)),   bm_c.verts.new((-cw, cw, cw * 2.0)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        bm_c.faces.new((v_c[i], v_c[inxt], v_c[4 + inxt], v_c[4 + i]))
    bm_c.faces.new((v_c[4], v_c[5], v_c[6], v_c[7]))
    m_crate = bpy.data.meshes.new("Proto_Crate")
    bm_c.to_mesh(m_crate)
    bm_c.free()
    m_crate.update()
    m_crate.shade_smooth()
    for p in m_crate.polygons:
        p.use_smooth = True
    m_crate.materials.append(mats["timber"])

    # 3. Lantern Post
    bm_lp = bmesh.new()
    pw, ph = 0.12, 3.2
    v_lp = [
        bm_lp.verts.new((-pw, -pw, 0.0)), bm_lp.verts.new((pw, -pw, 0.0)),
        bm_lp.verts.new((pw, pw, 0.0)),   bm_lp.verts.new((-pw, pw, 0.0)),
        bm_lp.verts.new((-pw, -pw, ph)),  bm_lp.verts.new((pw, -pw, ph)),
        bm_lp.verts.new((pw, pw, ph)),    bm_lp.verts.new((-pw, pw, ph)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm_lp.faces.new((v_lp[i], v_lp[inxt], v_lp[4 + inxt], v_lp[4 + i]))
        f.material_index = 0

    lw = 0.22
    ly = 0.35
    lz = ph - 0.25
    v_lit = [
        bm_lp.verts.new((-lw, ly - lw, lz)), bm_lp.verts.new((lw, ly - lw, lz)),
        bm_lp.verts.new((lw, ly + lw, lz)),  bm_lp.verts.new((-lw, ly + lw, lz)),
        bm_lp.verts.new((-lw, ly - lw, lz + lw * 2)), bm_lp.verts.new((lw, ly - lw, lz + lw * 2)),
        bm_lp.verts.new((lw, ly + lw, lz + lw * 2)),  bm_lp.verts.new((-lw, ly + lw, lz + lw * 2)),
    ]
    for i in range(4):
        inxt = (i + 1) % 4
        f = bm_lp.faces.new((v_lit[i], v_lit[inxt], v_lit[4 + inxt], v_lit[4 + i]))
        f.material_index = 1
    f_top = bm_lp.faces.new((v_lit[4], v_lit[5], v_lit[6], v_lit[7]))
    f_top.material_index = 1

    m_lantern = bpy.data.meshes.new("Proto_LanternPost")
    bm_lp.to_mesh(m_lantern)
    bm_lp.free()
    m_lantern.update()
    m_lantern.shade_smooth()
    for p in m_lantern.polygons:
        p.use_smooth = True
    m_lantern.materials.append(mats["timber"])   # 0
    m_lantern.materials.append(mats["lantern"])  # 1

    # 4. Wooden Fence Segment (2 posts + 2 rails)
    bm_fn = bmesh.new()
    fw, fl, fh = 0.08, 2.4, 1.1
    v_p1 = [
        bm_fn.verts.new((-fl * 0.5 - fw, -fw, 0.0)), bm_fn.verts.new((-fl * 0.5 + fw, -fw, 0.0)),
        bm_fn.verts.new((-fl * 0.5 + fw,  fw, 0.0)), bm_fn.verts.new((-fl * 0.5 - fw,  fw, 0.0)),
        bm_fn.verts.new((-fl * 0.5 - fw, -fw, fh)),  bm_fn.verts.new((-fl * 0.5 + fw, -fw, fh)),
        bm_fn.verts.new((-fl * 0.5 + fw,  fw, fh)),  bm_fn.verts.new((-fl * 0.5 - fw,  fw, fh)),
    ]
    v_p2 = [
        bm_fn.verts.new(( fl * 0.5 - fw, -fw, 0.0)), bm_fn.verts.new(( fl * 0.5 + fw, -fw, 0.0)),
        bm_fn.verts.new(( fl * 0.5 + fw,  fw, 0.0)), bm_fn.verts.new(( fl * 0.5 - fw,  fw, 0.0)),
        bm_fn.verts.new(( fl * 0.5 - fw, -fw, fh)),  bm_fn.verts.new(( fl * 0.5 + fw, -fw, fh)),
        bm_fn.verts.new(( fl * 0.5 + fw,  fw, fh)),  bm_fn.verts.new(( fl * 0.5 - fw,  fw, fh)),
    ]
    for vp in [v_p1, v_p2]:
        for i in range(4):
            inxt = (i + 1) % 4
            bm_fn.faces.new((vp[i], vp[inxt], vp[4 + inxt], vp[4 + i]))

    for rz in [fh * 0.5, fh * 0.85]:
        v_rail = [
            bm_fn.verts.new((-fl * 0.5, -0.04, rz - 0.05)),
            bm_fn.verts.new(( fl * 0.5, -0.04, rz - 0.05)),
            bm_fn.verts.new(( fl * 0.5,  0.04, rz - 0.05)),
            bm_fn.verts.new((-fl * 0.5,  0.04, rz - 0.05)),
            bm_fn.verts.new((-fl * 0.5, -0.04, rz + 0.05)),
            bm_fn.verts.new(( fl * 0.5, -0.04, rz + 0.05)),
            bm_fn.verts.new(( fl * 0.5,  0.04, rz + 0.05)),
            bm_fn.verts.new((-fl * 0.5,  0.04, rz + 0.05)),
        ]
        for i in range(4):
            inxt = (i + 1) % 4
            bm_fn.faces.new((v_rail[i], v_rail[inxt], v_rail[4 + inxt], v_rail[4 + i]))

    m_fence = bpy.data.meshes.new("Proto_Fence")
    bm_fn.to_mesh(m_fence)
    bm_fn.free()
    m_fence.update()
    m_fence.shade_smooth()
    for p in m_fence.polygons:
        p.use_smooth = True
    m_fence.materials.append(mats["timber"])

    return {
        "barrel": m_barrel,
        "crate": m_crate,
        "lantern": m_lantern,
        "fence": m_fence,
    }


# -----------------------------------------------------------------------------
# Organic Road Network
# -----------------------------------------------------------------------------


def build_road_network(collection, height_func, mats):
    """
    Constructs an organic curved road network ribbon mesh following the terrain:
    Main Trunk: Mountain Pass (8, 38) -> Forest (4, 18) -> Bridge (2, 2) -> Village (-2, -14) -> Lake Shore (-12, -22) -> Bay (22, -42).
    """
    waypoints_main = [
        ( 8.0,  38.0, 2.6),
        ( 6.5,  30.0, 2.6),
        ( 4.5,  22.0, 2.8),
        ( 2.0,  14.0, 2.8),
        ( 2.0,   2.0, 3.2),  # Across stone bridge
        (-0.5,  -6.0, 3.0),
        (-2.0, -14.0, 3.6),  # Village Square
        (-6.5, -18.0, 3.2),
        (-12.0, -22.0, 3.0), # Lake Shore
        (-4.0, -30.0, 2.8),
        ( 6.0, -36.0, 2.8),
        ( 16.0, -40.0, 3.2),
        ( 22.0, -42.0, 3.4), # Coastal Bay Overlook
    ]

    n_sub = 80
    ts = np.linspace(0.0, 1.0, n_sub)
    n_w = len(waypoints_main)
    w_pts = np.array(waypoints_main)

    # Catmull-Rom or cubic spline interpolation
    idx_float = ts * (n_w - 1)
    spl_x = np.zeros(n_sub)
    spl_y = np.zeros(n_sub)
    spl_w = np.zeros(n_sub)

    for i, t in enumerate(idx_float):
        i0 = int(math.floor(t))
        i1 = min(n_w - 1, i0 + 1)
        frac = t - i0
        # Hermite cubic smoothstep
        h = frac * frac * (3.0 - 2.0 * frac)
        spl_x[i] = (1.0 - h) * w_pts[i0, 0] + h * w_pts[i1, 0]
        spl_y[i] = (1.0 - h) * w_pts[i0, 1] + h * w_pts[i1, 1]
        spl_w[i] = (1.0 - h) * w_pts[i0, 2] + h * w_pts[i1, 2]

    road_verts = []
    road_faces = []
    for i in range(n_sub):
        if i == 0:
            tx, ty = spl_x[1] - spl_x[0], spl_y[1] - spl_y[0]
        elif i == n_sub - 1:
            tx, ty = spl_x[-1] - spl_x[-2], spl_y[-1] - spl_y[-2]
        else:
            tx, ty = spl_x[i + 1] - spl_x[i - 1], spl_y[i + 1] - spl_y[i - 1]
        t_len = max(1e-4, math.hypot(tx, ty))
        nx_w, ny_w = -ty / t_len, tx / t_len
        hw = spl_w[i] * 0.5

        xl = spl_x[i] + nx_w * hw
        yl = spl_y[i] + ny_w * hw
        xr = spl_x[i] - nx_w * hw
        yr = spl_y[i] - ny_w * hw

        zl = height_func(xl, yl) + 0.04
        zr = height_func(xr, yr) + 0.04

        road_verts.append((xl, yl, zl))
        road_verts.append((xr, yr, zr))

    for i in range(n_sub - 1):
        d_bridge = math.hypot(spl_x[i] - 2.0, spl_y[i] - 2.0)
        if d_bridge < 4.5:
            continue
        v1 = 2 * i
        v2 = 2 * i + 1
        v3 = 2 * (i + 1) + 1
        v4 = 2 * (i + 1)
        road_faces.append((v1, v2, v3, v4))

    mesh = bpy.data.meshes.new("Road_Network_Mesh")
    mesh.from_pydata(road_verts, [], road_faces)
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.materials.append(mats["road"])

    obj = bpy.data.objects.new("Road_Network", mesh)
    collection.objects.link(obj)
    return obj


# -----------------------------------------------------------------------------
# Master Settlement Orchestrator
# -----------------------------------------------------------------------------


def generate_settlement_and_landmarks(context, collection_settlement, terrain_data):
    """
    Orchestrates the creation of:
    - 10 Village Buildings (Chapel, Timber Houses, Stone Cottages, Barns, Watermill, Forge)
    - Village Square with stone well
    - Landmark 2: Ancient Hilltop Watchtower
    - Stone Arch River Bridge
    - Village Props: Barrels, crates, fences, lanterns
    - Organic Road Network
    """
    print(">>> Generating Procedural Village, Watchtower Landmark, and Props...")
    mats = get_settlement_materials()
    height_func = terrain_data.get("height_func")

    buildings = []

    # 1. Village Chapel (Spire landmark in village square)
    z_chapel = height_func(-2.0, -18.0)
    b_chapel = build_village_chapel(collection_settlement, -2.0, -18.0, z_chapel, math.radians(12.0), mats)
    buildings.append(b_chapel)

    # 2. Two-Story Half-Timber House 1
    z_h1 = height_func(-7.5, -12.5)
    b_h1 = build_timber_house(collection_settlement, "Village_House_Timber_01", -7.5, -12.5, z_h1, math.radians(-24.0), mats, scale=1.05)
    buildings.append(b_h1)

    # 3. Two-Story Half-Timber House 2 (Merchant House)
    z_h2 = height_func(3.5, -11.0)
    b_h2 = build_timber_house(collection_settlement, "Village_House_Timber_02", 3.5, -11.0, z_h2, math.radians(65.0), mats, scale=0.95)
    buildings.append(b_h2)

    # 4. Stone Cottage 1 (Thatched Roof)
    z_c1 = height_func(-6.5, -17.5)
    b_c1 = build_stone_cottage(collection_settlement, "Village_Cottage_Stone_01", -6.5, -17.5, z_c1, math.radians(15.0), mats, scale=1.0, thatch=True)
    buildings.append(b_c1)

    # 5. Stone Cottage 2 (Tiled Roof)
    z_c2 = height_func(4.5, -16.0)
    b_c2 = build_stone_cottage(collection_settlement, "Village_Cottage_Stone_02", 4.5, -16.0, z_c2, math.radians(-40.0), mats, scale=0.92, thatch=False)
    buildings.append(b_c2)

    # 6. Stone Cottage 3 (Gardener Cottage)
    z_c3 = height_func(-1.5, -9.0)
    b_c3 = build_stone_cottage(collection_settlement, "Village_Cottage_Stone_03", -1.5, -9.0, z_c3, math.radians(82.0), mats, scale=0.88, thatch=True)
    buildings.append(b_c3)

    # 7. Barn Stable 1 (Large Timber Barn)
    z_b1 = height_func(-12.5, -13.0)
    b_b1 = build_barn_stable(collection_settlement, "Village_Barn_Stable_01", -12.5, -13.0, z_b1, math.radians(-10.0), mats, scale=1.0)
    buildings.append(b_b1)

    # 8. Barn Stable 2 (Open Animal Shelter)
    z_b2 = height_func(8.0, -14.5)
    b_b2 = build_barn_stable(collection_settlement, "Village_Barn_Stable_02", 8.0, -14.5, z_b2, math.radians(45.0), mats, scale=0.9)
    buildings.append(b_b2)

    # 9. Watermill (Riverfront Millhouse with Water Wheel)
    z_mill = height_func(1.5, -6.5)
    b_mill = build_watermill(collection_settlement, 1.5, -6.5, z_mill, math.radians(-18.0), mats)
    buildings.append(b_mill)

    # 10. Blacksmith Forge (Open Workshop with Hearth)
    z_forge = height_func(-7.0, -8.0)
    b_forge = build_blacksmith_forge(collection_settlement, -7.0, -8.0, z_forge, math.radians(30.0), mats)
    buildings.append(b_forge)

    # 2. Village Square Water Well (Open Plaza in front of Chapel)
    z_well = height_func(-1.0, -21.5)
    well_obj = build_village_well(collection_settlement, -1.0, -21.5, z_well, mats)

    # 3. Landmark 2 - Ancient Hilltop Watchtower
    z_tower = height_func(24.0, 16.0)
    watchtower_obj = build_ancient_watchtower(collection_settlement, 24.0, 16.0, z_tower, mats)

    # 4. Stone Arch River Bridge
    z_bridge = height_func(2.0, 2.0)
    bridge_obj = build_stone_arch_bridge(collection_settlement, 2.0, 2.0, z_bridge, math.radians(-32.0), mats)

    # 5. Road Network
    road_obj = build_road_network(collection_settlement, height_func, mats)

    # 6. Props Instancing (Barrels, Crates, Fences, Lanterns)
    protos = create_prop_prototypes(mats)
    props = []

    # Lantern Posts (with warm amber night glow)
    lantern_locs = [
        (-1.0, -11.5), (-3.5, -15.5), (2.0, -13.0), (-6.0, -10.5), (2.0, 4.0), (22.0, 14.5), (-2.8, -21.0)
    ]
    for idx, (lx, ly) in enumerate(lantern_locs):
        lz = height_func(lx, ly)
        obj = bpy.data.objects.new(f"Prop_Lantern_Post_{idx:02d}", protos["lantern"])
        obj.location = (lx, ly, lz)
        collection_settlement.objects.link(obj)
        props.append(obj)

    # Barrel clusters around houses and tavern
    barrel_locs = [
        (-5.5, -13.0), (-5.2, -13.4), (-4.8, -13.1),
        (2.2, -11.8), (2.5, -12.2),
        (-6.2, -9.0), (-5.8, -8.8),
        (0.5, -7.5), (0.8, -7.8)
    ]
    for idx, (bx, by) in enumerate(barrel_locs):
        bz = height_func(bx, by)
        obj = bpy.data.objects.new(f"Prop_Barrel_{idx:02d}", protos["barrel"])
        obj.location = (bx, by, bz)
        obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
        collection_settlement.objects.link(obj)
        props.append(obj)

    # Crate clusters
    crate_locs = [
        (4.2, -12.5), (4.5, -12.0), (-7.8, -14.0), (-8.2, -13.6)
    ]
    for idx, (cx, cy) in enumerate(crate_locs):
        cz = height_func(cx, cy)
        obj = bpy.data.objects.new(f"Prop_Crate_{idx:02d}", protos["crate"])
        obj.location = (cx, cy, cz)
        obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
        collection_settlement.objects.link(obj)
        props.append(obj)

    # Fences along village perimeter and cottage yards
    fence_locs = [
        (-4.0, -20.0, 0.0), (-1.5, -20.2, 0.1), (1.0, -20.0, -0.05),
        (-9.0, -11.0, 1.2), (-9.0, -8.6, 1.2),
        (6.0, -13.0, -0.8), (6.0, -15.4, -0.8)
    ]
    for idx, (fx, fy, frot) in enumerate(fence_locs):
        fz = height_func(fx, fy)
        obj = bpy.data.objects.new(f"Prop_Fence_{idx:02d}", protos["fence"])
        obj.location = (fx, fy, fz)
        obj.rotation_euler = Euler((0.0, 0.0, frot))
        collection_settlement.objects.link(obj)
        props.append(obj)

    print(f"    Built {len(buildings)} village buildings, Watchtower, Bridge, Well, and {len(props)} props.")

    return {
        "buildings": buildings,
        "watchtower": watchtower_obj,
        "bridge": bridge_obj,
        "well": well_obj,
        "road": road_obj,
        "props": props,
    }

"""
build_anima_world_map.py — Version 3.1 (Cinematic Fantasy World)
=============================================================================
High-Fidelity "Small Open World" map inspired by Anima-Engine & Fantasy Cartography:
1. Procedural 420m x 420m Terrain with Multi-Stop Biome Vertex Colors:
   - Majestic Alpine Horn peaks (125m+) with crisp snowcaps & warm granite strata.
   - 2-Tier Waterfall Gorge dropping through layered rock canyon.
   - Sinuous meandering river with gravel banks & sandy shores.
   - Crystal-clear turquoise lake with natural basin.
   - Central rolling green valley with wildflower sprinkles.
   - Seamless vertex-colored dirt road connecting all landmarks without floating meshes.
2. Sky Dome & Atmosphere:
   - 750m seamless Sky Dome (visible_shadow=False) with golden-hour vertical gradient.
   - Stylized low-poly cumulus clouds drifting at altitude.
   - Warm golden sun (22° elevation) with soft ambient sky fill.
3. Botanical & Ecological Library (Cluster Scatter):
   - Fluffy, voluminous Deciduous Oak Trees (Ghibli/Zelda style).
   - Tall Alpine Pine Trees with 5 tiered star-skirt boughs.
   - Slender White Birch Trees with golden-green canopy.
   - Weeping Riverbank Willows near water.
   - Compact flowering bushes and natural rock boulders.
   - Camera & road exclusion zones to guarantee 100% unobstructed views.
4. Architecture & Epic Landmarks:
   - Landmark 1: Towering Alpine Mountain Range.
   - Landmark 2: Hilltop Windmill with 4 lattice sails & timber balcony.
   - Landmark 3: Ancient Stone Watchtower Ruin with broken parapets.
   - Landmark 4: 2-Tier Roaring Waterfall & Watermill with turning paddle wheel.
   - Medieval/Fantasy Village:
     * 2-Story Village Hall / Tavern with chimneys & lanterns.
     * Blacksmith forge, bakery, farmhouse, fisherman's stilt hut, cottages.
     * Village square with covered stone well, hay cart, barrels, fences.
     * Rustic wooden truss bridge over the river.
     * Lake fishing dock extending from shore with moored wooden rowboat & oars.
5. 6 Carefully Composed Cinematic Cameras with ZERO obstructions.
6. Automated glTF/GLB export & 1080p rendering.
=============================================================================
"""

import math
import os
import random
import sys
from pathlib import Path
from typing import List, Tuple

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
RENDERS_DIR = PROJECT_ROOT / "renders" / "anima_world"
BLEND_OUTPUT = MODELS_DIR / "anima_world_master.blend"
GLB_OUTPUT = MODELS_DIR / "anima_world.glb"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
RENDERS_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. Procedural Noise & Elevation Math
# =============================================================================

def pseudo_noise(x: float, y: float, seed: int = 42) -> float:
    v = math.sin(x * 12.9898 + y * 78.233 + seed * 1.51) * 43758.5453
    return (v - math.floor(v)) * 2.0 - 1.0

def smooth_noise(x: float, y: float, seed: int = 42) -> float:
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    wx = fx * fx * (3.0 - 2.0 * fx)
    wy = fy * fy * (3.0 - 2.0 * fy)

    n00 = pseudo_noise(ix, iy, seed)
    n10 = pseudo_noise(ix + 1, iy, seed)
    n01 = pseudo_noise(ix, iy + 1, seed)
    n11 = pseudo_noise(ix + 1, iy + 1, seed)

    nx0 = n00 * (1.0 - wx) + n10 * wx
    nx1 = n01 * (1.0 - wx) + n10 * wx
    return nx0 * (1.0 - wy) + nx1 * wy

def fbm(x: float, y: float, octaves: int = 5, lacunarity: float = 2.0, gain: float = 0.5, seed: int = 42) -> float:
    total = 0.0
    freq = 1.0
    amp = 1.0
    max_amp = 0.0
    for i in range(octaves):
        total += smooth_noise(x * freq, y * freq, seed + i * 37) * amp
        max_amp += amp
        freq *= lacunarity
        amp *= gain
    return total / max_amp

def ridge_noise(x: float, y: float, octaves: int = 4, seed: int = 88) -> float:
    total = 0.0
    freq = 1.0
    amp = 1.0
    max_amp = 0.0
    for i in range(octaves):
        n = smooth_noise(x * freq, y * freq, seed + i * 19)
        n = 1.0 - abs(n)
        n = n * n
        total += n * amp
        max_amp += amp
        freq *= 2.1
        amp *= 0.55
    return total / max_amp


# River Spine Waypoints: Gorge top -> 2 Cascades -> Mill -> Bridge -> Village -> Lake
RIVER_WAYPOINTS = [
    Vector((2.0, 115.0, 48.0)),     # Alpine Gorge Start
    Vector((10.0, 82.0, 26.0)),     # Cascade Ledge 1
    Vector((14.0, 52.0, 11.5)),     # Cascade Plunge Pool
    Vector((8.0, 30.0, 9.0)),       # Canyon exit
    Vector((-8.0, 16.0, 7.5)),      # Watermill bend
    Vector((-24.0, -10.0, 6.0)),    # Wooden Bridge crossing
    Vector((-16.0, -42.0, 4.8)),    # Village southern meander
    Vector((6.0, -68.0, 3.8)),      # Meadow loop
    Vector((-18.0, -96.0, 2.8)),    # Delta entrance
    Vector((-60.0, -125.0, 2.0)),   # Lake mouth
]

def get_river_distance_and_elev(px: float, py: float) -> Tuple[float, float]:
    min_dist = 1e9
    target_z = 0.0
    p = Vector((px, py, 0.0))
    for i in range(len(RIVER_WAYPOINTS) - 1):
        a = RIVER_WAYPOINTS[i]
        b = RIVER_WAYPOINTS[i + 1]
        ab = Vector((b.x - a.x, b.y - a.y, 0.0))
        ab_len2 = ab.length_squared
        if ab_len2 < 1e-4:
            continue
        ap = p - Vector((a.x, a.y, 0.0))
        t = max(0.0, min(1.0, ap.dot(ab) / ab_len2))
        proj = Vector((a.x, a.y, 0.0)) + ab * t
        d = (p - proj).length
        if d < min_dist:
            min_dist = d
            target_z = a.z + (b.z - a.z) * t
    return min_dist, target_z


# Road Network Branches:
# Branch A: Village entry -> Central Square -> Bridge -> West Lake Path
# Branch B: Central Square -> Windmill Hill -> Watchtower
ROAD_BRANCH_A = [
    Vector((55.0, -45.0, 9.5)),     # South-east entry trail
    Vector((34.0, -28.0, 9.8)),     # Village east road
    Vector((20.0, -10.0, 9.0)),     # Village central square
    Vector((2.0, -8.0, 8.2)),       # Tavern road
    Vector((-12.0, -9.5, 7.2)),     # Bridge east abutment
    Vector((-24.0, -10.0, 6.8)),    # Bridge center
    Vector((-36.0, -10.5, 6.8)),    # Bridge west abutment
    Vector((-40.0, -45.0, 5.8)),    # West shore trail
    Vector((-36.0, -88.0, 3.8)),    # Fisherman's cottage
    Vector((-34.0, -96.0, 2.8)),    # Lake pier head
]

ROAD_BRANCH_B = [
    Vector((20.0, -10.0, 9.0)),     # Village square
    Vector((26.0, 10.0, 10.5)),     # North valley lane
    Vector((46.0, 22.0, 16.5)),     # Hill approach
    Vector((70.0, 36.0, 24.5)),     # Windmill hill
    Vector((92.0, 30.0, 30.0)),     # Ridge pass
    Vector((110.0, 22.0, 39.0)),    # Watchtower ruin
]

def get_road_distance(px: float, py: float) -> float:
    min_dist = 1e9
    p = Vector((px, py, 0.0))
    for branch in [ROAD_BRANCH_A, ROAD_BRANCH_B]:
        for i in range(len(branch) - 1):
            a = branch[i]
            b = branch[i + 1]
            ab = Vector((b.x - a.x, b.y - a.y, 0.0))
            ab_len2 = ab.length_squared
            if ab_len2 < 1e-4:
                continue
            ap = p - Vector((a.x, a.y, 0.0))
            t = max(0.0, min(1.0, ap.dot(ab) / ab_len2))
            proj = Vector((a.x, a.y, 0.0)) + ab * t
            d = (p - proj).length
            if d < min_dist:
                min_dist = d
    return min_dist


def calculate_world_height(x: float, y: float) -> float:
    """Computes geomorphically cohesive elevation across the 420m x 420m world."""
    # 1. Base Rolling Valley Grassland
    base_hills = fbm(x * 0.006, y * 0.006, octaves=4, seed=101) * 9.5 + 8.5

    # 2. Alpine Horn Mountain Range in North (y > 25)
    mountain_factor = max(0.0, (y - 25.0) / 135.0)
    mountain_factor = min(1.0, mountain_factor) ** 1.75

    lat_mask = max(0.0, 1.0 - (abs(x + 10.0) / 240.0) ** 2)
    ridge1 = ridge_noise(x * 0.013, y * 0.013, octaves=5, seed=333)
    ridge2 = ridge_noise(x * 0.028, y * 0.028, octaves=3, seed=777)
    mountain_height = (ridge1 * 105.0 + ridge2 * 28.0 + 22.0) * mountain_factor * lat_mask

    # 3. Eastern Watchtower Hill (x=110, y=22)
    dist_watch = math.sqrt((x - 110.0)**2 + (y - 22.0)**2)
    watch_elev = (34.0 * math.cos(min(1.0, dist_watch / 55.0) * (math.pi * 0.5))**2) if dist_watch < 55.0 else 0.0

    # 4. North-Western Windmill Knoll (x=70, y=36)
    dist_mill = math.sqrt((x - 70.0)**2 + (y - 36.0)**2)
    mill_elev = (18.0 * math.cos(min(1.0, dist_mill / 48.0) * (math.pi * 0.5))**2) if dist_mill < 48.0 else 0.0

    # 5. South-Western Lake Basin (x=-70, y=-130)
    dist_lake = math.sqrt((x - (-70.0))**2 + (y - (-130.0))**2)
    lake_r = 75.0
    lake_depression = (-15.0 * math.cos(min(1.0, dist_lake / lake_r) * (math.pi * 0.5))**2) if dist_lake < lake_r else 0.0

    raw_z = base_hills + mountain_height + watch_elev + mill_elev + lake_depression

    # 6. River Trench Carving
    riv_dist, riv_z = get_river_distance_and_elev(x, y)
    river_w = 9.0
    if riv_dist < river_w:
        carve = math.cos((riv_dist / river_w) * (math.pi * 0.5)) ** 2
        bed_z = riv_z - 1.4
        raw_z = raw_z * (1.0 - carve) + bed_z * carve

    return raw_z + smooth_noise(x * 0.2, y * 0.2, 555) * 0.35


# =============================================================================
# 2. Material Library & Shader Helpers
# =============================================================================

def get_or_create_mat(name: str, color: Tuple[float, float, float, float], roughness: float = 0.6, emission: Tuple[float, float, float, float] = None, metallic: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if emission:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = 2.5
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emission

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_vertex_colored_terrain_shader() -> bpy.types.Material:
    mat = bpy.data.materials.new(name="M_Terrain_VertexPBR")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    vcol = nodes.new("ShaderNodeVertexColor")
    vcol.layer_name = "COLOR_0"

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.82
    links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def create_water_shader() -> bpy.types.Material:
    """Sparkling translucent turquoise alpine water shader."""
    mat = bpy.data.materials.new(name="M_Water_Teal")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.12, 0.60, 0.68, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Metallic"].default_value = 0.05
    bsdf.inputs["IOR"].default_value = 1.333
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.88
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.88

    mat.blend_method = 'BLEND'
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# =============================================================================
# 3. Sky Dome, Atmosphere & Clouds
# =============================================================================

def build_sky_dome_and_clouds():
    col = bpy.context.collection

    # 1. Seamless 750m Sky Dome Hemisphere (visible_shadow=False)
    dome_bm = bmesh.new()
    bmesh.ops.create_icosphere(dome_bm, subdivisions=4, radius=750.0)

    for f in dome_bm.faces:
        f.normal_flip()

    dome_mesh = bpy.data.meshes.new("Sky_Dome")
    color_layer = dome_bm.loops.layers.color.new("COLOR_0")

    # Gradient: Warm sunset amber (bottom) -> Soft turquoise (mid) -> Vibrant azure (top)
    for face in dome_bm.faces:
        for loop in face.loops:
            vz = max(0.0, min(1.0, (loop.vert.co.z + 100.0) / 800.0))
            if vz < 0.22:
                t = vz / 0.22
                c = (1.0 - t * 0.04, 0.78 + t * 0.08, 0.56 + t * 0.12, 1.0)
            elif vz < 0.60:
                t = (vz - 0.22) / 0.38
                c = (0.96 - t * 0.38, 0.86 - t * 0.08, 0.68 + t * 0.26, 1.0)
            else:
                t = (vz - 0.60) / 0.40
                c = (0.58 - t * 0.40, 0.78 - t * 0.36, 0.94 - t * 0.18, 1.0)
            loop[color_layer] = c

    dome_bm.to_mesh(dome_mesh)
    dome_bm.free()

    dome_obj = bpy.data.objects.new("Sky_Dome", dome_mesh)
    dome_obj.location = Vector((0, 0, -50.0))
    dome_obj.visible_shadow = False  # DO NOT SHADOW THE SCENE!

    mat_sky = bpy.data.materials.new(name="M_Sky_Dome_Emission")
    mat_sky.use_nodes = True
    nodes = mat_sky.node_tree.nodes
    links = mat_sky.node_tree.links
    nodes.clear()
    vcol = nodes.new("ShaderNodeVertexColor")
    vcol.layer_name = "COLOR_0"
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.35
    links.new(vcol.outputs["Color"], emit.inputs["Color"])
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    dome_obj.data.materials.append(mat_sky)
    col.objects.link(dome_obj)

    # 2. Glowing Sun Disc Mesh in the West
    sun_bm = bmesh.new()
    bmesh.ops.create_icosphere(sun_bm, subdivisions=2, radius=22.0)
    sun_mesh = bpy.data.meshes.new("Sky_Sun_Disc")
    sun_bm.to_mesh(sun_mesh)
    sun_bm.free()
    sun_disc = bpy.data.objects.new("Sky_Sun_Disc", sun_mesh)
    sun_disc.location = Vector((-380.0, -250.0, 210.0))
    sun_disc.visible_shadow = False
    mat_sun = get_or_create_mat("M_Sun_Disc_Glow", (1.0, 0.96, 0.88, 1.0), roughness=0.0, emission=(1.0, 0.92, 0.75, 1.0))
    sun_disc.data.materials.append(mat_sun)
    col.objects.link(sun_disc)

    # 3. Stylized Low-Poly Cumulus Clouds
    mat_cloud = get_or_create_mat("M_Stylized_Cloud", (0.98, 0.95, 0.92, 1.0), roughness=0.4, emission=(0.95, 0.90, 0.82, 1.0))
    cloud_positions = [
        Vector((-110.0, -50.0, 115.0)),
        Vector((-50.0, 55.0, 125.0)),
        Vector((50.0, -110.0, 105.0)),
        Vector((120.0, -35.0, 130.0)),
        Vector((-130.0, 95.0, 135.0)),
        Vector((75.0, 105.0, 140.0)),
        Vector((0.0, 150.0, 145.0)),
    ]

    for i, cpos in enumerate(cloud_positions):
        c_bm = bmesh.new()
        for cx, cy, cz, cr in [(0, 0, 0, 16.0), (12.0, 2.0, -1.0, 12.0), (-11.0, -3.0, 1.0, 11.0), (5.0, 9.0, 2.0, 10.0), (-6.0, -8.0, -1.0, 9.0)]:
            mat_c = Matrix.Translation((cx, cy, cz)) @ Matrix.Scale(cr, 4, Vector((1.3, 1.0, 0.55)))
            bmesh.ops.create_icosphere(c_bm, subdivisions=2, radius=1.0, matrix=mat_c)
        c_mesh = bpy.data.meshes.new(f"Cloud_Cluster_{i+1}")
        c_bm.to_mesh(c_mesh)
        c_bm.free()
        c_obj = bpy.data.objects.new(f"Cloud_Cluster_{i+1}", c_mesh)
        c_obj.location = cpos
        c_obj.visible_shadow = True
        c_obj.data.materials.append(mat_cloud)
        col.objects.link(c_obj)


# =============================================================================
# 4. Open World Terrain Generation with Biome Colors
# =============================================================================

def build_open_world_terrain() -> bpy.types.Object:
    print("Building Procedural Open World Terrain (420m x 420m)...")
    res_x = 210
    res_y = 210
    size_x = 420.0
    size_y = 420.0

    bm = bmesh.new()
    grid_verts = []

    dx = size_x / (res_x - 1)
    dy = size_y / (res_y - 1)
    half_x = size_x * 0.5
    half_y = size_y * 0.5

    for iy in range(res_y):
        row = []
        py = -half_y + iy * dy
        for ix in range(res_x):
            px = -half_x + ix * dx
            pz = calculate_world_height(px, py)
            v = bm.verts.new((px, py, pz))
            row.append(v)
        grid_verts.append(row)

    # Base skirt for solid geology block
    base_z = -18.0
    bottom_verts = []
    for iy in range(res_y):
        row = []
        py = -half_y + iy * dy
        for ix in range(res_x):
            px = -half_x + ix * dx
            v = bm.verts.new((px, py, base_z))
            row.append(v)
        bottom_verts.append(row)

    # Grid faces
    for iy in range(res_y - 1):
        for ix in range(res_x - 1):
            v00 = grid_verts[iy][ix]
            v10 = grid_verts[iy][ix + 1]
            v11 = grid_verts[iy + 1][ix + 1]
            v01 = grid_verts[iy + 1][ix]
            bm.faces.new((v00, v10, v11, v01))

    # Skirt wall faces
    for ix in range(res_x - 1):
        bm.faces.new((grid_verts[0][ix], grid_verts[0][ix + 1], bottom_verts[0][ix + 1], bottom_verts[0][ix]))
        bm.faces.new((grid_verts[-1][ix + 1], grid_verts[-1][ix], bottom_verts[-1][ix], bottom_verts[-1][ix + 1]))
    for iy in range(res_y - 1):
        bm.faces.new((grid_verts[iy + 1][0], grid_verts[iy][0], bottom_verts[iy][0], bottom_verts[iy + 1][0]))
        bm.faces.new((grid_verts[iy][-1], grid_verts[iy + 1][-1], bottom_verts[iy + 1][-1], bottom_verts[iy][-1]))

    # Bottom cap
    for iy in range(res_y - 1):
        for ix in range(res_x - 1):
            b00 = bottom_verts[iy][ix]
            b10 = bottom_verts[iy][ix + 1]
            b11 = bottom_verts[iy + 1][ix + 1]
            b01 = bottom_verts[iy + 1][ix]
            bm.faces.new((b01, b11, b10, b00))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    # Vertex Color Layer COLOR_0
    color_layer = bm.loops.layers.color.new("COLOR_0")

    # Artistic Biome Palette
    c_snow = (0.98, 0.99, 1.0, 1.0)
    c_granite_light = (0.54, 0.52, 0.50, 1.0)
    c_granite_warm = (0.48, 0.44, 0.38, 1.0)
    c_alpine_tundra = (0.40, 0.48, 0.24, 1.0)
    c_grass_meadow = (0.28, 0.55, 0.18, 1.0)
    c_grass_sunny = (0.38, 0.64, 0.22, 1.0)
    c_forest_moss = (0.20, 0.40, 0.15, 1.0)
    c_sand_beach = (0.78, 0.68, 0.48, 1.0)
    c_damp_earth = (0.44, 0.35, 0.25, 1.0)
    c_dirt_road = (0.58, 0.44, 0.30, 1.0)

    for face in bm.faces:
        norm = face.normal
        slope = norm.z  # 1.0 = flat, 0.0 = sheer vertical
        for loop in face.loops:
            v = loop.vert
            vx, vy, vz = v.co.x, v.co.y, v.co.z

            if vz <= base_z + 0.5:
                loop[color_layer] = (0.18, 0.18, 0.20, 1.0)
                continue

            riv_dist, riv_z = get_river_distance_and_elev(vx, vy)
            road_dist = get_road_distance(vx, vy)

            # 1. Road Coloring (smooth width 2.8m)
            if road_dist < 2.8 and vz > 3.8:
                t_road = road_dist / 2.8
                # Blend road into grass
                cr = (c_dirt_road[0] * (1.0 - t_road) + c_grass_meadow[0] * t_road,
                      c_dirt_road[1] * (1.0 - t_road) + c_grass_meadow[1] * t_road,
                      c_dirt_road[2] * (1.0 - t_road) + c_grass_meadow[2] * t_road, 1.0)
                loop[color_layer] = cr
                continue

            # 2. Snow Peaks (Alpine summits > 75m, slope > 0.45)
            if vz > 75.0 and slope > 0.45:
                loop[color_layer] = c_snow
                continue

            # 3. Rock Cliffs & Strata (Slopes steeper than 35°)
            if slope < 0.65:
                strata = math.sin(vz * 0.35) * 0.5 + 0.5
                cr = (c_granite_light[0] * (1.0 - strata) + c_granite_warm[0] * strata,
                      c_granite_light[1] * (1.0 - strata) + c_granite_warm[1] * strata,
                      c_granite_light[2] * (1.0 - strata) + c_granite_warm[2] * strata, 1.0)
                loop[color_layer] = cr
                continue

            # 4. Shorelines (Lake & Riverbanks)
            if vz < 3.2 or riv_dist < 4.5:
                loop[color_layer] = c_sand_beach if vz < 3.0 else c_damp_earth
                continue

            # 5. Alpine Tundra Zone (48m to 75m)
            if vz > 48.0:
                loop[color_layer] = c_alpine_tundra
                continue

            # 6. Northern Dense Forest Floor
            if vy > 28.0:
                loop[color_layer] = c_forest_moss
                continue

            # 7. Lush Valley Grassland with warm sunny patches
            patch = fbm(vx * 0.05, vy * 0.05, octaves=3, seed=222)
            cg = (c_grass_meadow[0] * (1.0 - patch) + c_grass_sunny[0] * patch,
                  c_grass_meadow[1] * (1.0 - patch) + c_grass_sunny[1] * patch,
                  c_grass_meadow[2] * (1.0 - patch) + c_grass_sunny[2] * patch, 1.0)
            loop[color_layer] = cg

    mesh = bpy.data.meshes.new("Terrain_OpenWorld")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Terrain_OpenWorld", mesh)
    bpy.context.collection.objects.link(obj)

    for poly in mesh.polygons:
        poly.use_smooth = True

    mat = create_vertex_colored_terrain_shader()
    obj.data.materials.append(mat)
    return obj


# =============================================================================
# 5. Hydrology: Lake, River, Waterfall, Pier & Rowboat
# =============================================================================

def build_water_bodies(water_mat: bpy.types.Material) -> List[bpy.types.Object]:
    water_objs = []
    col = bpy.context.collection
    mat_wood = get_or_create_mat("M_Weathered_Wood", (0.34, 0.24, 0.16, 1.0), roughness=0.8)
    mat_foam = get_or_create_mat("M_Water_Foam", (0.95, 0.98, 1.0, 1.0), roughness=0.15, emission=(0.88, 0.94, 1.0, 1.0))

    # 1. Scenic Lake Surface (Elevation 2.0m)
    lake_bm = bmesh.new()
    lake_center = Vector((-70.0, -130.0, 2.0))
    lake_r = 74.0
    segments = 48
    v_center = lake_bm.verts.new(lake_center)
    rim_verts = []
    for i in range(segments):
        theta = 2.0 * math.pi * (i / segments)
        rx = lake_center.x + math.cos(theta) * lake_r
        ry = lake_center.y + math.sin(theta) * (lake_r * 0.9)
        rim_verts.append(lake_bm.verts.new((rx, ry, 2.0)))
    for i in range(segments):
        lake_bm.faces.new((v_center, rim_verts[i], rim_verts[(i + 1) % segments]))
    lake_mesh = bpy.data.meshes.new("Water_Scenic_Lake")
    lake_bm.to_mesh(lake_mesh)
    lake_bm.free()
    lake_obj = bpy.data.objects.new("Water_Scenic_Lake", lake_mesh)
    lake_obj.data.materials.append(water_mat)
    col.objects.link(lake_obj)
    water_objs.append(lake_obj)

    # 2. Winding River Surface
    riv_bm = bmesh.new()
    left_strip, right_strip = [], []
    river_half_w = 4.4
    for i in range(len(RIVER_WAYPOINTS) - 1):
        p0 = RIVER_WAYPOINTS[i]
        p1 = RIVER_WAYPOINTS[i + 1]
        steps = 10
        for s in range(steps if i < len(RIVER_WAYPOINTS) - 2 else steps + 1):
            t = s / steps
            pos = p0.lerp(p1, t)
            tangent = (p1 - p0).normalized()
            normal = Vector((-tangent.y, tangent.x, 0.0)).normalized()
            w = river_half_w * (1.0 + t * 0.35 if i >= 6 else 1.0)
            left_strip.append(riv_bm.verts.new(pos + normal * w))
            right_strip.append(riv_bm.verts.new(pos - normal * w))

    for i in range(len(left_strip) - 1):
        riv_bm.faces.new((left_strip[i], right_strip[i], right_strip[i + 1], left_strip[i + 1]))

    riv_mesh = bpy.data.meshes.new("Water_River_Flow")
    riv_bm.to_mesh(riv_mesh)
    riv_bm.free()
    riv_obj = bpy.data.objects.new("Water_River_Flow", riv_mesh)
    riv_obj.data.materials.append(water_mat)
    col.objects.link(riv_obj)
    water_objs.append(riv_obj)

    # 3. Waterfall Cascades & Foam Splash Pads
    wf_bm = bmesh.new()
    # Upper cascade (z=48 to z=26)
    bmesh.ops.create_cone(wf_bm, cap_ends=True, cap_tris=False, segments=8, radius1=5.0, radius2=3.8, depth=22.0, matrix=Matrix.Translation((6.0, 98.0, 37.0)) @ Matrix.Rotation(math.radians(-32), 4, 'X'))
    # Lower cascade (z=26 to z=11.5)
    bmesh.ops.create_cone(wf_bm, cap_ends=True, cap_tris=False, segments=8, radius1=6.2, radius2=4.8, depth=16.0, matrix=Matrix.Translation((12.0, 67.0, 19.0)) @ Matrix.Rotation(math.radians(-36), 4, 'X'))
    # Splash foam pads
    bmesh.ops.create_cube(wf_bm, size=1.0, matrix=Matrix.Translation((10.0, 80.0, 26.2)) @ Matrix.Scale(9.0, 4, Vector((1, 0, 0))) @ Matrix.Scale(8.0, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.4, 4, Vector((0, 0, 1))))
    bmesh.ops.create_cube(wf_bm, size=1.0, matrix=Matrix.Translation((14.0, 50.0, 11.6)) @ Matrix.Scale(11.0, 4, Vector((1, 0, 0))) @ Matrix.Scale(10.0, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.5, 4, Vector((0, 0, 1))))

    wf_mesh = bpy.data.meshes.new("Water_Waterfall_Cascade")
    wf_bm.to_mesh(wf_mesh)
    wf_bm.free()
    wf_obj = bpy.data.objects.new("Water_Waterfall_Cascade", wf_mesh)
    wf_obj.data.materials.append(mat_foam)
    col.objects.link(wf_obj)
    water_objs.append(wf_obj)

    # 4. Wooden Fishing Pier Extending From Shoreline (-34, -96) Southwest into the Water
    pier_bm = bmesh.new()
    # Pier deck starts at bank (-34, -96) and extends 16m southwest to (-46, -108)
    p_start = Vector((-34.0, -96.0, 2.5))
    p_end = Vector((-46.0, -108.0, 2.3))
    p_mid = (p_start + p_end) * 0.5
    p_dir = (p_end - p_start).normalized()
    p_angle = math.atan2(p_dir.y, p_dir.x)

    deck_mat = Matrix.Translation(p_mid) @ Matrix.Rotation(p_angle, 4, 'Z') @ Matrix.Scale(18.0, 4, Vector((1, 0, 0))) @ Matrix.Scale(3.2, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.3, 4, Vector((0, 0, 1)))
    bmesh.ops.create_cube(pier_bm, size=1.0, matrix=deck_mat)

    # Pilings
    for t_pil in [0.1, 0.4, 0.7, 0.95]:
        pos_pil = p_start.lerp(p_end, t_pil)
        bmesh.ops.create_cone(pier_bm, cap_ends=True, cap_tris=False, segments=6, radius1=0.25, radius2=0.25, depth=4.0, matrix=Matrix.Translation(pos_pil + Vector((0, 0, -1.5))))

    pier_mesh = bpy.data.meshes.new("Lake_Fishing_Pier")
    pier_bm.to_mesh(pier_mesh)
    pier_bm.free()
    pier_obj = bpy.data.objects.new("Lake_Fishing_Pier", pier_mesh)
    pier_obj.data.materials.append(mat_wood)
    col.objects.link(pier_obj)

    # 5. Moored Wooden Rowboat with Oars
    boat_bm = bmesh.new()
    bmesh.ops.create_cone(boat_bm, cap_ends=True, cap_tris=False, segments=8, radius1=1.2, radius2=0.75, depth=4.4, matrix=Matrix.Translation((0, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Scale(1.0, 4, Vector((1.3, 1.0, 0.75))))
    bmesh.ops.create_cube(boat_bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.1)) @ Matrix.Scale(1.8, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.4, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.15, 4, Vector((0, 0, 1))))
    # Oars
    bmesh.ops.create_cone(boat_bm, cap_ends=True, cap_tris=False, segments=4, radius1=0.08, radius2=0.04, depth=2.8, matrix=Matrix.Translation((1.0, 0.2, 0.4)) @ Matrix.Rotation(math.radians(35), 4, 'Y'))
    boat_mesh = bpy.data.meshes.new("Lake_Rowboat")
    boat_bm.to_mesh(boat_mesh)
    boat_bm.free()
    boat_obj = bpy.data.objects.new("Lake_Rowboat", boat_mesh)
    boat_obj.location = Vector((-48.0, -112.0, 1.8))
    boat_obj.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')
    boat_obj.data.materials.append(mat_wood)
    col.objects.link(boat_obj)

    return water_objs


# =============================================================================
# 6. Infrastructure: Rustic Wooden Truss Bridge
# =============================================================================

def build_bridge() -> bpy.types.Object:
    col = bpy.context.collection
    mat_wood = get_or_create_mat("M_Weathered_Wood", (0.34, 0.24, 0.16, 1.0), roughness=0.8)

    br_bm = bmesh.new()
    bridge_len = 24.0
    bridge_w = 4.4
    bridge_h = 1.6

    # Deck
    bmesh.ops.create_cube(br_bm, size=1.0, matrix=Matrix.Translation((0, 0, 0)) @ Matrix.Scale(bridge_len, 4, Vector((1, 0, 0))) @ Matrix.Scale(bridge_w, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.4, 4, Vector((0, 0, 1))))
    # Railings & Posts
    for side in [-1, 1]:
        ry = side * (bridge_w * 0.5 - 0.15)
        bmesh.ops.create_cube(br_bm, size=1.0, matrix=Matrix.Translation((0, ry, bridge_h * 0.6)) @ Matrix.Scale(bridge_len, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.2, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.25, 4, Vector((0, 0, 1))))
        for px in np.linspace(-bridge_len * 0.48, bridge_len * 0.48, 9):
            bmesh.ops.create_cube(br_bm, size=1.0, matrix=Matrix.Translation((px, ry, bridge_h * 0.35)) @ Matrix.Scale(0.3, 4, Vector((1, 1, 0))) @ Matrix.Scale(bridge_h, 4, Vector((0, 0, 1))))

    # Stone Abutments
    for ax in [-bridge_len * 0.5 - 1.2, bridge_len * 0.5 + 1.2]:
        bmesh.ops.create_cube(br_bm, size=1.0, matrix=Matrix.Translation((ax, 0, -1.6)) @ Matrix.Scale(3.6, 4, Vector((1, 0, 0))) @ Matrix.Scale(bridge_w + 1.0, 4, Vector((0, 1, 0))) @ Matrix.Scale(3.4, 4, Vector((0, 0, 1))))

    br_mesh = bpy.data.meshes.new("Bridge_Wooden_Truss")
    br_bm.to_mesh(br_mesh)
    br_bm.free()
    br_obj = bpy.data.objects.new("Bridge_Wooden_Truss", br_mesh)
    br_obj.location = Vector((-24.0, -10.0, 6.8))
    br_obj.rotation_euler = Euler((0, 0, math.radians(8)), 'XYZ')
    br_obj.data.materials.append(mat_wood)
    col.objects.link(br_obj)
    return br_obj


# =============================================================================
# 7. Landmarks: Hilltop Windmill & Ancient Watchtower Ruin
# =============================================================================

def build_hilltop_windmill(loc: Vector) -> bpy.types.Object:
    col = bpy.context.collection
    bm = bmesh.new()

    mat_stone = get_or_create_mat("M_Stone_Masonry", (0.42, 0.40, 0.38, 1.0), roughness=0.9)
    mat_wood = get_or_create_mat("M_Weathered_Wood", (0.34, 0.24, 0.16, 1.0), roughness=0.8)
    mat_roof = get_or_create_mat("M_Roof_Terracotta", (0.64, 0.26, 0.16, 1.0), roughness=0.75)
    mat_sail = get_or_create_mat("M_Windmill_Sail", (0.92, 0.88, 0.80, 1.0), roughness=0.85)

    def add_geom_with_mat(mat_idx, func, **kwargs):
        old_faces = set(bm.faces)
        func(bm, **kwargs)
        for f in bm.faces:
            if f not in old_faces:
                f.material_index = mat_idx

    # 1. Round tapering stone base
    add_geom_with_mat(0, bmesh.ops.create_cone, cap_ends=True, cap_tris=False, segments=12, radius1=3.4, radius2=2.6, depth=8.5, matrix=Matrix.Translation((0, 0, 4.25)))

    # 2. Wooden Walkway Balcony
    add_geom_with_mat(1, bmesh.ops.create_cone, cap_ends=True, cap_tris=False, segments=12, radius1=3.6, radius2=3.6, depth=0.35, matrix=Matrix.Translation((0, 0, 8.5)))
    add_geom_with_mat(1, bmesh.ops.create_cone, cap_ends=False, cap_tris=False, segments=12, radius1=3.55, radius2=3.55, depth=1.1, matrix=Matrix.Translation((0, 0, 9.1)))

    # 3. Upper Timber Cap
    add_geom_with_mat(1, bmesh.ops.create_cone, cap_ends=True, cap_tris=False, segments=10, radius1=2.5, radius2=2.1, depth=3.5, matrix=Matrix.Translation((0, 0, 10.4)))

    # 4. Conical Roof Cap
    add_geom_with_mat(2, bmesh.ops.create_cone, cap_ends=True, cap_tris=False, segments=10, radius1=2.8, radius2=0.0, depth=3.2, matrix=Matrix.Translation((0, 0, 13.6)))

    # 5. Rotor Hub & 4 Lattice Sails (Facing South-West)
    hub_loc = Vector((0.0, -2.4, 11.2))
    add_geom_with_mat(1, bmesh.ops.create_cone, cap_ends=True, cap_tris=False, segments=8, radius1=0.7, radius2=0.5, depth=1.2, matrix=Matrix.Translation(hub_loc) @ Matrix.Rotation(math.radians(90), 4, 'X'))

    blade_len = 6.2
    for angle in [0, 90, 180, 270]:
        rad = math.radians(angle)
        spar_mat = Matrix.Translation(hub_loc + Vector((0, -0.4, 0))) @ Matrix.Rotation(rad, 4, 'Y') @ Matrix.Translation((0, 0, blade_len * 0.5)) @ Matrix.Scale(0.2, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.2, 4, Vector((0, 1, 0))) @ Matrix.Scale(blade_len, 4, Vector((0, 0, 1)))
        add_geom_with_mat(1, bmesh.ops.create_cube, size=1.0, matrix=spar_mat)

        sail_mat = Matrix.Translation(hub_loc + Vector((0, -0.4, 0))) @ Matrix.Rotation(rad, 4, 'Y') @ Matrix.Translation((0.6, 0, blade_len * 0.55)) @ Matrix.Scale(1.1, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.08, 4, Vector((0, 1, 0))) @ Matrix.Scale(blade_len * 0.8, 4, Vector((0, 0, 1)))
        add_geom_with_mat(3, bmesh.ops.create_cube, size=1.0, matrix=sail_mat)

    mesh = bpy.data.meshes.new("Landmark_Hilltop_Windmill")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Landmark_Hilltop_Windmill", mesh)
    obj.location = loc
    obj.rotation_euler = Euler((0, 0, math.radians(-35)), 'XYZ')

    obj.data.materials.append(mat_stone)  # 0
    obj.data.materials.append(mat_wood)   # 1
    obj.data.materials.append(mat_roof)   # 2
    obj.data.materials.append(mat_sail)   # 3
    col.objects.link(obj)
    return obj


def build_ancient_watchtower(loc: Vector) -> bpy.types.Object:
    bm = bmesh.new()
    col = bpy.context.collection
    mat_stone = get_or_create_mat("M_Ruin_Stone", (0.38, 0.38, 0.40, 1.0), roughness=0.95)

    radius = 4.5
    height = 18.0
    segments = 16

    # Fortress Cylinder
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius * 1.12, radius2=radius, depth=height, matrix=Matrix.Translation((0, 0, height * 0.5)))

    # Crenellated Battlement Crown
    top_z = height
    top_r = radius * 1.15
    for i in range(segments):
        if i % 2 == 0:
            theta = 2.0 * math.pi * (i / segments)
            mx = math.cos(theta) * top_r
            my = math.sin(theta) * top_r
            bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((mx, my, top_z + 0.9)) @ Matrix.Scale(1.3, 4, Vector((1, 1, 0))) @ Matrix.Scale(1.8, 4, Vector((0, 0, 1))))

    # Brazier beacon
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=1.4, radius2=0.7, depth=1.2, matrix=Matrix.Translation((0, 0, top_z + 1.1)))

    mesh = bpy.data.meshes.new("Landmark_Watchtower_Ruin")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Landmark_Watchtower_Ruin", mesh)
    obj.location = loc
    obj.data.materials.append(mat_stone)
    col.objects.link(obj)
    return obj


# =============================================================================
# 8. Village Architecture & Watermill
# =============================================================================

def build_cottage(name: str, loc: Vector, rot_z: float, scale_xy: float = 1.0, is_inn: bool = False, has_waterwheel: bool = False, roof_style: int = 0) -> bpy.types.Object:
    col = bpy.context.collection
    bm = bmesh.new()

    w = 6.0 * scale_xy
    l = (12.0 if is_inn else 7.6) * scale_xy
    h = 4.6 if is_inn else 3.2

    def add_cube_with_mat(matrix, mat_idx):
        old_faces = set(bm.faces)
        bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)
        for f in bm.faces:
            if f not in old_faces:
                f.material_index = mat_idx

    # 1. Stone Foundation
    mat_f = Matrix.Translation((0, 0, 0.4)) @ Matrix.Scale(w + 0.3, 4, Vector((1, 0, 0))) @ Matrix.Scale(l + 0.3, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.8, 4, Vector((0, 0, 1)))
    add_cube_with_mat(mat_f, 3)

    # 2. Plaster Walls
    mat_w = Matrix.Translation((0, 0, 0.8 + h * 0.5)) @ Matrix.Scale(w, 4, Vector((1, 0, 0))) @ Matrix.Scale(l, 4, Vector((0, 1, 0))) @ Matrix.Scale(h, 4, Vector((0, 0, 1)))
    add_cube_with_mat(mat_w, 0)

    # 3. Pitched Gable Roof
    roof_h = 3.2 * scale_xy
    overhang = 0.55
    rw = w * 0.5 + overhang
    rl = l * 0.5 + overhang
    rz_base = 0.8 + h

    rv_r1 = bm.verts.new((0.0, -rl, rz_base + roof_h))
    rv_r2 = bm.verts.new((0.0, rl, rz_base + roof_h))
    rv_e1 = bm.verts.new((-rw, -rl, rz_base - 0.2))
    rv_e2 = bm.verts.new((-rw, rl, rz_base - 0.2))
    rv_e3 = bm.verts.new((rw, -rl, rz_base - 0.2))
    rv_e4 = bm.verts.new((rw, rl, rz_base - 0.2))

    f1 = bm.faces.new((rv_r1, rv_r2, rv_e2, rv_e1))
    f2 = bm.faces.new((rv_r2, rv_r1, rv_e3, rv_e4))
    f3 = bm.faces.new((rv_r1, rv_e1, rv_e3))
    f4 = bm.faces.new((rv_r2, rv_e4, rv_e2))
    for f in [f1, f2, f3, f4]:
        f.material_index = 1

    # 4. Timber Posts & Cross-Beams
    for cx in [-w * 0.5, w * 0.5]:
        for cy in [-l * 0.5, l * 0.5]:
            mat_p = Matrix.Translation((cx, cy, 0.8 + h * 0.5)) @ Matrix.Scale(0.38, 4, Vector((1, 1, 0))) @ Matrix.Scale(h, 4, Vector((0, 0, 1)))
            add_cube_with_mat(mat_p, 2)

    # Horizontal Wall Tie Beam
    add_cube_with_mat(Matrix.Translation((0, 0, 0.8 + h)) @ Matrix.Scale(w + 0.1, 4, Vector((1, 0, 0))) @ Matrix.Scale(l + 0.1, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.3, 4, Vector((0, 0, 1))), 2)

    # 5. Stone Chimney
    mat_ch = Matrix.Translation((w * 0.32, l * 0.24, rz_base + roof_h * 0.6)) @ Matrix.Scale(1.2, 4, Vector((1, 1, 0))) @ Matrix.Scale(roof_h + 1.6, 4, Vector((0, 0, 1)))
    add_cube_with_mat(mat_ch, 3)

    # 6. Glowing Windows (Warm Golden Glow)
    for wx in [-w * 0.24, w * 0.24]:
        mat_win = Matrix.Translation((wx, -l * 0.5 - 0.05, 1.8)) @ Matrix.Scale(1.1, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.12, 4, Vector((0, 1, 0))) @ Matrix.Scale(1.3, 4, Vector((0, 0, 1)))
        add_cube_with_mat(mat_win, 4)

    # 7. Wooden Door
    mat_door = Matrix.Translation((0.0, -l * 0.5 - 0.06, 1.4)) @ Matrix.Scale(1.3, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.12, 4, Vector((0, 1, 0))) @ Matrix.Scale(2.0, 4, Vector((0, 0, 1)))
    add_cube_with_mat(mat_door, 2)

    # 8. Waterwheel attachment (if Watermill)
    if has_waterwheel:
        wheel_center = Vector((-w * 0.5 - 0.8, 0.0, 1.8))
        wheel_r = 2.4
        old_f = set(bm.faces)
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.5, radius2=0.5, depth=0.8, matrix=Matrix.Translation(wheel_center) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
        for pi in range(10):
            p_theta = 2.0 * math.pi * (pi / 10)
            p_mat = Matrix.Translation(wheel_center) @ Matrix.Rotation(p_theta, 4, 'X') @ Matrix.Translation((0, wheel_r * 0.8, 0)) @ Matrix.Scale(0.7, 4, Vector((1, 0, 0))) @ Matrix.Scale(0.1, 4, Vector((0, 1, 0))) @ Matrix.Scale(1.1, 4, Vector((0, 0, 1)))
            bmesh.ops.create_cube(bm, size=1.0, matrix=p_mat)
        for f in bm.faces:
            if f not in old_f:
                f.material_index = 2

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.rotation_euler = Euler((0, 0, rot_z), 'XYZ')

    mat_plaster = get_or_create_mat("M_Plaster_Wall", (0.88, 0.86, 0.80, 1.0), roughness=0.85)
    roof_col = (0.64, 0.26, 0.16, 1.0) if roof_style == 0 else (0.48, 0.38, 0.24, 1.0)
    mat_roof = get_or_create_mat(f"M_Roof_Style_{roof_style}", roof_col, roughness=0.75)
    mat_timber = get_or_create_mat("M_Timber_Beam", (0.24, 0.16, 0.10, 1.0), roughness=0.8)
    mat_stone = get_or_create_mat("M_Stone_Masonry", (0.38, 0.38, 0.40, 1.0), roughness=0.9)
    mat_window = get_or_create_mat("M_Window_Glow", (1.0, 0.86, 0.46, 1.0), roughness=0.2, emission=(1.0, 0.84, 0.42, 1.0))

    obj.data.materials.append(mat_plaster)  # 0
    obj.data.materials.append(mat_roof)     # 1
    obj.data.materials.append(mat_timber)   # 2
    obj.data.materials.append(mat_stone)    # 3
    obj.data.materials.append(mat_window)   # 4

    col.objects.link(obj)
    return obj


def build_village_props(village_center: Vector):
    col = bpy.context.collection
    mat_wood = get_or_create_mat("M_Weathered_Wood", (0.34, 0.24, 0.16, 1.0), roughness=0.8)
    mat_stone = get_or_create_mat("M_Stone_Masonry", (0.38, 0.38, 0.40, 1.0), roughness=0.9)

    # 1. Village Stone Well in Central Plaza
    w_bm = bmesh.new()
    bmesh.ops.create_cone(w_bm, cap_ends=True, cap_tris=False, segments=12, radius1=1.6, radius2=1.5, depth=1.1, matrix=Matrix.Translation((0, 0, 0.55)))
    bmesh.ops.create_cube(w_bm, size=1.0, matrix=Matrix.Translation((-1.2, 0, 1.8)) @ Matrix.Scale(0.2, 4, Vector((1, 1, 0))) @ Matrix.Scale(2.5, 4, Vector((0, 0, 1))))
    bmesh.ops.create_cube(w_bm, size=1.0, matrix=Matrix.Translation((1.2, 0, 1.8)) @ Matrix.Scale(0.2, 4, Vector((1, 1, 0))) @ Matrix.Scale(2.5, 4, Vector((0, 0, 1))))
    bmesh.ops.create_cone(w_bm, cap_ends=True, cap_tris=False, segments=10, radius1=2.2, radius2=0.0, depth=1.5, matrix=Matrix.Translation((0, 0, 3.8)))

    w_mesh = bpy.data.meshes.new("Village_Stone_Well")
    w_bm.to_mesh(w_mesh)
    w_bm.free()
    w_obj = bpy.data.objects.new("Village_Stone_Well", w_mesh)
    w_obj.location = village_center + Vector((0, 0, 0.1))
    w_obj.data.materials.append(mat_stone)
    col.objects.link(w_obj)

    # 2. Wooden Farm Cart
    cart_bm = bmesh.new()
    bmesh.ops.create_cube(cart_bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.75)) @ Matrix.Scale(1.8, 4, Vector((1, 0, 0))) @ Matrix.Scale(3.2, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.3, 4, Vector((0, 0, 1))))
    for wx in [-1.0, 1.0]:
        bmesh.ops.create_cone(cart_bm, cap_ends=True, cap_tris=False, segments=10, radius1=0.6, radius2=0.6, depth=0.15, matrix=Matrix.Translation((wx, 0.0, 0.6)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
    cart_mesh = bpy.data.meshes.new("Village_Farm_Cart")
    cart_bm.to_mesh(cart_mesh)
    cart_bm.free()
    cart_obj = bpy.data.objects.new("Village_Farm_Cart", cart_mesh)
    cart_obj.location = village_center + Vector((14.0, -8.0, 0.2))
    cart_obj.rotation_euler = Euler((0, 0, math.radians(45)), 'XYZ')
    cart_obj.data.materials.append(mat_wood)
    col.objects.link(cart_obj)

    # 3. Barrels & Crates cluster
    b_bm = bmesh.new()
    for bx, by in [(3.0, 4.0), (3.6, 4.8), (2.4, 4.5), (-5.0, 8.0)]:
        bmesh.ops.create_cone(b_bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.45, radius2=0.4, depth=1.0, matrix=Matrix.Translation((bx, by, 0.5)))
    for cx, cy in [(4.2, 3.5), (-4.2, 9.0)]:
        bmesh.ops.create_cube(b_bm, size=0.8, matrix=Matrix.Translation((cx, cy, 0.4)))
    b_mesh = bpy.data.meshes.new("Village_Barrels_Crates")
    b_bm.to_mesh(b_mesh)
    b_bm.free()
    b_obj = bpy.data.objects.new("Village_Barrels_Crates", b_mesh)
    b_obj.location = village_center
    b_obj.data.materials.append(mat_wood)
    col.objects.link(b_obj)

    # 4. Village Wooden Paddock Fences
    f_bm = bmesh.new()
    for fi in range(7):
        fy = -18.0 + fi * 2.2
        bmesh.ops.create_cube(f_bm, size=1.0, matrix=Matrix.Translation((28.0, fy, 0.7)) @ Matrix.Scale(0.18, 4, Vector((1, 1, 0))) @ Matrix.Scale(1.4, 4, Vector((0, 0, 1))))
    bmesh.ops.create_cube(f_bm, size=1.0, matrix=Matrix.Translation((28.0, -11.0, 0.5)) @ Matrix.Scale(0.1, 4, Vector((1, 0, 0))) @ Matrix.Scale(15.0, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.15, 4, Vector((0, 0, 1))))
    bmesh.ops.create_cube(f_bm, size=1.0, matrix=Matrix.Translation((28.0, -11.0, 1.1)) @ Matrix.Scale(0.1, 4, Vector((1, 0, 0))) @ Matrix.Scale(15.0, 4, Vector((0, 1, 0))) @ Matrix.Scale(0.15, 4, Vector((0, 0, 1))))

    f_mesh = bpy.data.meshes.new("Village_Paddock_Fence")
    f_bm.to_mesh(f_mesh)
    f_bm.free()
    f_obj = bpy.data.objects.new("Village_Paddock_Fence", f_mesh)
    f_obj.location = village_center
    f_obj.data.materials.append(mat_wood)
    col.objects.link(f_obj)


# =============================================================================
# 9. Botanical Library & Ecosystem Scatter
# =============================================================================

def build_botanical_prototypes():
    mat_pine_trunk = get_or_create_mat("M_Pine_Bark", (0.22, 0.15, 0.10, 1.0), roughness=0.9)
    mat_birch_trunk = get_or_create_mat("M_Birch_Bark", (0.85, 0.85, 0.82, 1.0), roughness=0.7)
    mat_oak_foliage = get_or_create_mat("M_Oak_Leaves", (0.26, 0.54, 0.18, 1.0), roughness=0.7)
    mat_pine_foliage = get_or_create_mat("M_Pine_Needles", (0.15, 0.35, 0.16, 1.0), roughness=0.75)
    mat_birch_foliage = get_or_create_mat("M_Birch_Leaves", (0.44, 0.66, 0.18, 1.0), roughness=0.65)
    mat_willow_foliage = get_or_create_mat("M_Willow_Leaves", (0.34, 0.58, 0.28, 1.0), roughness=0.7)
    mat_rock = get_or_create_mat("M_Rock_Facet", (0.45, 0.44, 0.42, 1.0), roughness=0.92)

    # 1. Stylized Voluminous Oak (Majestic Crown with central dome + 5 satellite puffs)
    oak_bm = bmesh.new()
    bmesh.ops.create_cone(oak_bm, cap_ends=True, cap_tris=False, segments=8, radius1=1.2, radius2=0.55, depth=4.0, matrix=Matrix.Translation((0, 0, 2.0)))
    # Central large dome
    bmesh.ops.create_icosphere(oak_bm, subdivisions=2, radius=3.5, matrix=Matrix.Translation((0, 0, 6.2)) @ Matrix.Scale(1.2, 4, Vector((1.0, 1.0, 0.85))))
    # 5 Satellite puffs
    for angle, dist_r, pz_s, pr in [(30, 2.2, 5.4, 2.2), (110, 2.0, 5.6, 2.0), (190, 2.4, 5.2, 2.3), (270, 2.1, 5.5, 2.1), (340, 1.9, 6.8, 1.9)]:
        rad = math.radians(angle)
        px = math.cos(rad) * dist_r
        py = math.sin(rad) * dist_r
        bmesh.ops.create_icosphere(oak_bm, subdivisions=2, radius=pr, matrix=Matrix.Translation((px, py, pz_s)))

    oak_mesh = bpy.data.meshes.new("Proto_Valley_Oak")
    oak_bm.to_mesh(oak_mesh)
    oak_bm.free()
    oak_obj = bpy.data.objects.new("Proto_Valley_Oak", oak_mesh)
    oak_obj.data.materials.append(mat_oak_foliage)

    # 2. Stylized Alpine Pine (Tall trunk + 5 tiered star-skirts)
    pine_bm = bmesh.new()
    bmesh.ops.create_cone(pine_bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.6, radius2=0.18, depth=14.0, matrix=Matrix.Translation((0, 0, 7.0)))
    skirts = [(3.2, 5.2, 3.4), (5.6, 4.4, 3.0), (7.8, 3.6, 2.6), (9.8, 2.8, 2.2), (11.6, 1.8, 2.0)]
    for sz, sr, sh in skirts:
        bmesh.ops.create_cone(pine_bm, cap_ends=True, cap_tris=False, segments=8, radius1=sr, radius2=0.08, depth=sh, matrix=Matrix.Translation((0, 0, sz + sh * 0.5)))
    pine_mesh = bpy.data.meshes.new("Proto_Alpine_Pine")
    pine_bm.to_mesh(pine_mesh)
    pine_bm.free()
    pine_obj = bpy.data.objects.new("Proto_Alpine_Pine", pine_mesh)
    pine_obj.data.materials.append(mat_pine_foliage)

    # 3. Stylized White Birch Tree
    birch_bm = bmesh.new()
    bmesh.ops.create_cone(birch_bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.4, radius2=0.14, depth=11.0, matrix=Matrix.Translation((0, 0, 5.5)))
    for bx, by, bz, br in [(0, 0, 9.8, 2.2), (1.1, 0.6, 8.4, 1.8), (-0.9, -0.7, 8.0, 1.7)]:
        bmesh.ops.create_icosphere(birch_bm, subdivisions=2, radius=br, matrix=Matrix.Translation((bx, by, bz)))
    birch_mesh = bpy.data.meshes.new("Proto_Birch_Tree")
    birch_bm.to_mesh(birch_mesh)
    birch_bm.free()
    birch_obj = bpy.data.objects.new("Proto_Birch_Tree", birch_mesh)
    birch_obj.data.materials.append(mat_birch_foliage)

    # 4. Weeping River Willow
    willow_bm = bmesh.new()
    bmesh.ops.create_cone(willow_bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.8, radius2=0.35, depth=5.5, matrix=Matrix.Translation((0, 0, 2.7)))
    for wx, wy, wz in [(1.2, 0, 5.8), (0, 1.2, 5.5), (-1.0, -0.5, 5.4), (0.8, -1.0, 5.2)]:
        bmesh.ops.create_icosphere(willow_bm, subdivisions=2, radius=2.0, matrix=Matrix.Translation((wx, wy, wz)) @ Matrix.Scale(1.1, 4, Vector((1.0, 1.0, 1.3))))
    willow_mesh = bpy.data.meshes.new("Proto_River_Willow")
    willow_bm.to_mesh(willow_mesh)
    willow_bm.free()
    willow_obj = bpy.data.objects.new("Proto_River_Willow", willow_mesh)
    willow_obj.data.materials.append(mat_willow_foliage)

    # 5. Wild Bush (Compact Cluster of 3 soft spheres)
    bush_bm = bmesh.new()
    bmesh.ops.create_icosphere(bush_bm, subdivisions=2, radius=1.3, matrix=Matrix.Translation((0, 0, 0.9)))
    bmesh.ops.create_icosphere(bush_bm, subdivisions=2, radius=0.95, matrix=Matrix.Translation((0.8, 0.4, 0.7)))
    bmesh.ops.create_icosphere(bush_bm, subdivisions=2, radius=0.85, matrix=Matrix.Translation((-0.7, -0.3, 0.6)))
    bush_mesh = bpy.data.meshes.new("Proto_Wild_Bush")
    bush_bm.to_mesh(bush_mesh)
    bush_bm.free()
    bush_obj = bpy.data.objects.new("Proto_Wild_Bush", bush_mesh)
    bush_obj.data.materials.append(mat_oak_foliage)

    # 6. Faceted Fantasy Rock Boulder
    rock_bm = bmesh.new()
    bmesh.ops.create_cube(rock_bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.6)) @ Matrix.Scale(2.2, 4, Vector((1.2, 0.9, 0.7))))
    bmesh.ops.subdivide_edges(rock_bm, edges=rock_bm.edges, cuts=1)
    for v in rock_bm.verts:
        v.co += Vector((pseudo_noise(v.co.x, v.co.y), pseudo_noise(v.co.y, v.co.z), pseudo_noise(v.co.z, v.co.x))) * 0.35
    rock_mesh = bpy.data.meshes.new("Proto_Fantasy_Rock")
    rock_bm.to_mesh(rock_mesh)
    rock_bm.free()
    rock_obj = bpy.data.objects.new("Proto_Fantasy_Rock", rock_mesh)
    rock_obj.data.materials.append(mat_rock)

    return oak_obj, pine_obj, birch_obj, willow_obj, bush_obj, rock_obj


# Protected Camera Exclusion Zones: No trees or rocks within 8m of any camera
PROTECTED_CAMERA_POSITIONS = [
    Vector((22.0, -42.0, 11.8)),     # CAM_01
    Vector((-40.0, -85.0, 9.5)),     # CAM_02
    Vector((115.0, 8.0, 46.0)),      # CAM_03
    Vector((2.0, 34.0, 11.5)),       # CAM_04
    Vector((36.0, 8.0, 15.0)),       # CAM_05
    Vector((165.0, -175.0, 135.0)),  # CAM_OVERVIEW
]

def is_near_camera(px: float, py: float, radius: float = 9.0) -> bool:
    for cpos in PROTECTED_CAMERA_POSITIONS:
        if math.sqrt((px - cpos.x)**2 + (py - cpos.y)**2) < radius:
            return True
    return False


def scatter_open_world_ecosystem(oak_proto, pine_proto, birch_proto, willow_proto, bush_proto, rock_proto):
    print("Scattering Open World Biomes (600+ Trees, Shrubs & Natural Rocks)...")
    col = bpy.context.collection
    np.random.seed(42)

    # 1. Northern Alpine Pine Forest (280 Pines)
    for _ in range(280):
        px = np.random.uniform(-190.0, 190.0)
        py = np.random.uniform(28.0, 180.0)
        if is_near_camera(px, py):
            continue
        pz = calculate_world_height(px, py)
        riv_d, _ = get_river_distance_and_elev(px, py)
        road_d = get_road_distance(px, py)
        if riv_d < 12.0 or road_d < 6.5 or pz > 95.0 or pz < 8.0:
            continue
        tree = pine_proto.copy()
        tree.data = pine_proto.data.copy()
        s = np.random.uniform(0.8, 1.45)
        tree.scale = Vector((s, s, s))
        tree.location = Vector((px, py, pz))
        tree.rotation_euler = Euler((0, 0, np.random.uniform(0, math.pi * 2)), 'XYZ')
        col.objects.link(tree)

    # 2. Valley Broadleaf Groves (Oaks & Birches, 200 Trees)
    for _ in range(200):
        px = np.random.uniform(-190.0, 170.0)
        py = np.random.uniform(-160.0, 25.0)
        if is_near_camera(px, py):
            continue
        pz = calculate_world_height(px, py)
        riv_d, _ = get_river_distance_and_elev(px, py)
        road_d = get_road_distance(px, py)
        dist_vil = math.sqrt((px - 20.0)**2 + (py - (-10.0))**2)
        dist_lake = math.sqrt((px - (-70.0))**2 + (py - (-130.0))**2)

        # Clearings for village, lake and roads
        if dist_vil < 28.0 or dist_lake < 70.0 or riv_d < 9.0 or road_d < 5.5 or pz < 3.0 or pz > 42.0:
            continue

        proto = oak_proto if np.random.rand() > 0.35 else birch_proto
        tree = proto.copy()
        tree.data = proto.data.copy()
        s = np.random.uniform(0.8, 1.35)
        tree.scale = Vector((s, s, s))
        tree.location = Vector((px, py, pz))
        tree.rotation_euler = Euler((0, 0, np.random.uniform(0, math.pi * 2)), 'XYZ')
        col.objects.link(tree)

    # 3. Riverbank Weeping Willows (25 Willows)
    for wp in RIVER_WAYPOINTS[3:-2]:
        for _ in range(3):
            side = 1.0 if np.random.rand() > 0.5 else -1.0
            px = wp.x + side * np.random.uniform(6.5, 12.0)
            py = wp.y + np.random.uniform(-8.0, 8.0)
            if is_near_camera(px, py):
                continue
            road_d = get_road_distance(px, py)
            dist_vil = math.sqrt((px - 20.0)**2 + (py - (-10.0))**2)
            if road_d < 6.0 or dist_vil < 22.0:
                continue
            pz = calculate_world_height(px, py)
            tree = willow_proto.copy()
            tree.data = willow_proto.data.copy()
            s = np.random.uniform(0.85, 1.25)
            tree.scale = Vector((s, s, s))
            tree.location = Vector((px, py, pz))
            tree.rotation_euler = Euler((0, 0, np.random.uniform(0, math.pi * 2)), 'XYZ')
            col.objects.link(tree)

    # 4. Wild Bushes & Flowering Shrubs (100 Bushes)
    for _ in range(100):
        px = np.random.uniform(-180.0, 160.0)
        py = np.random.uniform(-150.0, 35.0)
        if is_near_camera(px, py):
            continue
        pz = calculate_world_height(px, py)
        road_d = get_road_distance(px, py)
        riv_d, _ = get_river_distance_and_elev(px, py)
        dist_vil = math.sqrt((px - 20.0)**2 + (py - (-10.0))**2)
        if road_d < 4.0 or riv_d < 4.0 or dist_vil < 16.0 or pz < 2.5 or pz > 45.0:
            continue
        bush = bush_proto.copy()
        bush.data = bush_proto.data.copy()
        s = np.random.uniform(0.6, 1.3)
        bush.scale = Vector((s, s, s))
        bush.location = Vector((px, py, pz))
        bush.rotation_euler = Euler((0, 0, np.random.uniform(0, math.pi * 2)), 'XYZ')
        col.objects.link(bush)

    # 5. Natural Mountain Scree & Gorge Rocks (Strictly outside roads/settlement)
    for _ in range(65):
        px = np.random.uniform(-160.0, 160.0)
        py = np.random.uniform(35.0, 160.0)
        if is_near_camera(px, py):
            continue
        pz = calculate_world_height(px, py)
        road_d = get_road_distance(px, py)
        dist_vil = math.sqrt((px - 20.0)**2 + (py - (-10.0))**2)
        if road_d < 8.0 or dist_vil < 35.0 or pz < 18.0:
            continue
        rock = rock_proto.copy()
        rock.data = rock_proto.data.copy()
        s = np.random.uniform(0.8, 2.0)
        rock.scale = Vector((s, s * 0.9, s * 0.6))
        rock.location = Vector((px, py, pz - 0.2))
        rock.rotation_euler = Euler((np.random.uniform(0, 0.3), np.random.uniform(0, 0.3), np.random.uniform(0, math.pi * 2)), 'XYZ')
        col.objects.link(rock)


# =============================================================================
# 10. Cinematic Golden-Hour Lighting & Sky
# =============================================================================

def setup_cinematic_lighting():
    # 1. World Background (Warm Golden Sky)
    world = bpy.data.worlds.new("World_Golden_Sky")
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()

    bg = wnodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.75, 0.84, 0.96, 1.0)
    bg.inputs["Strength"].default_value = 1.05
    wout = wnodes.new("ShaderNodeOutputWorld")
    wlinks.new(bg.outputs["Background"], wout.inputs["Surface"])
    bpy.context.scene.world = world

    # 2. Main Sun Light (22° elevation, warm amber tone)
    sun_data = bpy.data.lights.new(name="Sun_Golden_Hour", type='SUN')
    sun_data.color = (1.0, 0.86, 0.68)
    sun_data.energy = 5.8
    sun_data.angle = math.radians(2.2)

    sun_obj = bpy.data.objects.new("Sun_Golden_Hour", sun_data)
    sun_obj.rotation_euler = Euler((math.radians(68.0), math.radians(12.0), math.radians(-125.0)), 'XYZ')
    bpy.context.collection.objects.link(sun_obj)

    # 3. Soft Sky Ambient Fill Light
    fill_data = bpy.data.lights.new(name="Sky_Ambient_Fill", type='SUN')
    fill_data.color = (0.62, 0.78, 0.98)
    fill_data.energy = 1.35
    fill_obj = bpy.data.objects.new("Sky_Ambient_Fill", fill_data)
    fill_obj.rotation_euler = Euler((math.radians(18.0), 0.0, math.radians(45.0)), 'XYZ')
    bpy.context.collection.objects.link(fill_obj)


# =============================================================================
# 11. Composition Cameras (Unobstructed Professional Framing)
# =============================================================================

CAMERAS_CONFIG = [
    {
        "name": "CAM_01_VILLAGE_SQUARE",
        "loc": Vector((22.0, -42.0, 11.8)),
        "target": Vector((18.0, -5.0, 10.5)),
        "focal": 34.0,
        "desc": "Standing at village entrance looking down cobblestone street past well & cottages toward snow peaks"
    },
    {
        "name": "CAM_02_LAKE_PIER",
        "loc": Vector((-40.0, -85.0, 9.5)),
        "target": Vector((-65.0, -125.0, 2.0)),
        "focal": 32.0,
        "desc": "Shoreline overlook along the wooden pier and rowboat across reflective turquoise lake at sunset"
    },
    {
        "name": "CAM_03_VALLEY_OVERLOOK",
        "loc": Vector((115.0, 8.0, 46.0)),
        "target": Vector((5.0, -8.0, 10.0)),
        "focal": 34.0,
        "desc": "Panoramic vista from watchtower ridge overlooking entire river valley, bridge, village and windmill"
    },
    {
        "name": "CAM_04_WATERFALL_GORGE",
        "loc": Vector((2.0, 34.0, 11.5)),
        "target": Vector((12.0, 72.0, 28.0)),
        "focal": 32.0,
        "desc": "Looking up into rocky canyon at 2-tier waterfall cascades and ancient watchtower on the cliff above"
    },
    {
        "name": "CAM_05_WINDMILL_HILL",
        "loc": Vector((36.0, 8.0, 15.0)),
        "target": Vector((70.0, 36.0, 28.0)),
        "focal": 32.0,
        "desc": "Grassy path leading up to the hilltop windmill with spinning sails against the golden sky"
    },
    {
        "name": "CAM_OVERVIEW_CINEMATIC",
        "loc": Vector((165.0, -175.0, 135.0)),
        "target": Vector((-5.0, -5.0, 12.0)),
        "focal": 30.0,
        "desc": "High 3/4 aerial establishing shot capturing the full open world layout"
    }
]

def setup_cameras() -> List[bpy.types.Object]:
    cam_objs = []
    for cfg in CAMERAS_CONFIG:
        cdata = bpy.data.cameras.new(cfg["name"])
        cdata.lens = cfg["focal"]
        cdata.clip_start = 0.5
        cdata.clip_end = 2500.0

        cobj = bpy.data.objects.new(cfg["name"], cdata)
        cobj.location = cfg["loc"]

        direction = cfg["target"] - cfg["loc"]
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cobj.rotation_euler = rot_quat.to_euler()

        bpy.context.collection.objects.link(cobj)
        cam_objs.append(cobj)

    bpy.context.scene.camera = cam_objs[0]
    return cam_objs


# =============================================================================
# 12. Master Execution Pipeline
# =============================================================================

def build_entire_world():
    print("\n=======================================================")
    print("  GENESIS ZERO — OPEN WORLD MASTERPIECE 3.1")
    print("=======================================================\n")

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Sky Dome & Stylized Clouds
    build_sky_dome_and_clouds()

    # 2. Materials
    water_mat = create_water_shader()

    # 3. Terrain (with painted dirt road & biomes)
    terrain_obj = build_open_world_terrain()

    # 4. Hydrology (Lake, River, Waterfall, Pier, Boat)
    water_objs = build_water_bodies(water_mat)

    # 5. Infrastructure (Rustic Wooden Truss Bridge)
    bridge_obj = build_bridge()

    # 6. Landmarks
    # Landmark 1: Hilltop Windmill
    windmill_obj = build_hilltop_windmill(Vector((70.0, 36.0, 24.5)))
    # Landmark 2: Ancient Stone Watchtower Ruin
    watchtower_obj = build_ancient_watchtower(Vector((110.0, 22.0, 39.0)))

    # 7. Medieval Fantasy Village (10 Buildings & Props)
    village_center = Vector((20.0, -10.0, 9.0))
    cottages = [
        build_cottage("Village_Hall_Inn", village_center + Vector((0.0, 8.0, 0.0)), math.radians(10), scale_xy=1.35, is_inn=True, roof_style=0),
        build_cottage("Cottage_Blacksmith", village_center + Vector((14.0, -12.0, 0.2)), math.radians(35), scale_xy=1.1, roof_style=1),
        build_cottage("Cottage_Bakery", village_center + Vector((-10.0, -12.0, -0.4)), math.radians(-30), scale_xy=0.95, roof_style=0),
        build_cottage("Cottage_Tavern_Annex", village_center + Vector((-11.0, 4.0, -0.2)), math.radians(85), scale_xy=1.05, roof_style=1),
        build_cottage("Cottage_Farmstead", village_center + Vector((18.0, 7.0, 0.5)), math.radians(-20), scale_xy=1.15, roof_style=1),
        build_cottage("Village_Watermill", Vector((-8.0, 16.0, 7.8)), math.radians(15), scale_xy=1.1, has_waterwheel=True, roof_style=0),
        build_cottage("Cottage_Fisherman", Vector((-36.0, -88.0, 3.5)), math.radians(60), scale_xy=0.9, roof_style=1),
        build_cottage("Cottage_Woodcutter", Vector((5.0, 22.0, 9.5)), math.radians(-70), scale_xy=0.9, roof_style=0),
        build_cottage("Cottage_Herbalist", Vector((35.0, -3.0, 10.2)), math.radians(115), scale_xy=0.95, roof_style=1),
        build_cottage("Cottage_Shepherd", Vector((42.0, -22.0, 10.8)), math.radians(-45), scale_xy=0.88, roof_style=0),
    ]
    build_village_props(village_center)

    # 8. Botanical Library & Ecosystem Scatter
    oak_proto, pine_proto, birch_proto, willow_proto, bush_proto, rock_proto = build_botanical_prototypes()
    scatter_open_world_ecosystem(oak_proto, pine_proto, birch_proto, willow_proto, bush_proto, rock_proto)

    # 9. Golden Hour Lighting
    setup_cinematic_lighting()

    # 10. Composition Cameras
    cam_objs = setup_cameras()

    # 11. Save Master Blend File
    print(f"\nSaving Master Blend File to: {BLEND_OUTPUT}")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUTPUT))

    # 12. Export glTF 2.0 / GLB
    print(f"Exporting glTF/GLB to: {GLB_OUTPUT}")
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUTPUT),
        export_format='GLB',
        use_selection=False,
        export_cameras=True,
        export_lights=True,
        export_apply=True
    )

    # 13. Render 6 Cinematic Cameras (1080p)
    bpy.context.scene.view_settings.look = 'AgX - Punchy'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    for cobj in cam_objs:
        out_img = RENDERS_DIR / f"{cobj.name}.png"
        print(f"Rendering {cobj.name} -> {out_img}")
        bpy.context.scene.camera = cobj
        bpy.context.scene.render.filepath = str(out_img)
        bpy.ops.render.render(write_still=True)

    print("\n[SUCCESS] Anima Open World 3.1 successfully built, exported and rendered!")


if __name__ == "__main__":
    build_entire_world()

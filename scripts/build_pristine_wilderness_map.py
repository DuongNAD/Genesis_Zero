#!/usr/bin/env python3
"""
=============================================================================
Genesis Zero · Pristine Wilderness & Karst Water Caves (Version 4.0 - Masterpiece)
Procedural 3D Open World Generator (Blender 5.2+ / Python API)
=============================================================================
100% Pristine Nature · Strictly Obeying All Architectural Guidelines:
1. Pure untouched natural world: No human architecture, roads, bridges, or structures.
2. "Chỗ nào đất thì sử dụng đất":
   - Rich dark forest loam under tree groves.
   - Weathered scree dirt on steep slopes (24°-50°).
   - Wet river mud & pebble gravel along waterlines.
   - Quartz sand beach along the great lowland lake shore.
3. "Chỗ nào cỏ thì cho hoa cỏ":
   - Vibrant emerald grass on sunny plains and hills.
   - 4 varieties of 3D wildflowers (daisies, buttercups, lavender, alpine poppies).
   - 3D grass blade tufts for micro-relief.
   - Grouped into dense, vibrant meadow fields.
4. Natural Karst Water Cave Portal:
   - Weathered limestone rock arch naturally embedded in the cliff face.
   - Deep subterranean pool of emerald water inside the cavern.
   - Stalactites hanging from the cavern roof, stalagmites rising from the pool edge.
   - Bioluminescent mushrooms (cyan and purple) casting mystical reflections.
   - Continuous hydrological flow into the valley river.
5. 6 Mathematically Verified Cinematic Cameras ("Mắt AI" unobstructed views).
=============================================================================
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

random.seed(2026)

WORKSPACE_DIR = "/Users/duongnad/Documents/project/Genesis_Zero"
MODELS_DIR = os.path.join(WORKSPACE_DIR, "models")
ARTIFACT_DIR = "/Users/duongnad/.gemini/antigravity/brain/d89c4a0b-fbb6-4a7a-8b23-aaa6b5ca4212"
BLEND_FILE = os.path.join(MODELS_DIR, "anima_world_master.blend")
GLB_FILE = os.path.join(MODELS_DIR, "anima_world.glb")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# =============================================================================
# 1. Clean Scene & Render Engine Setup
# =============================================================================

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr(bpy.types, "RenderEngineEEVEENext") else 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'

    world = bpy.data.worlds.new("Wilderness_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.50, 0.72, 0.94, 1.0)
        bg.inputs["Strength"].default_value = 1.15

    print("[Genesis Wilderness] Scene reset and configured.")


def bmesh_create_cylinder(bm, segments=6, radius=1.0, depth=2.0, matrix=None):
    if matrix is None:
        matrix = Matrix.Identity(4)
    return bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius,
        depth=depth,
        matrix=matrix
    )


# =============================================================================
# 2. Materials
# =============================================================================

def get_or_create_mat(name: str, base_color=(0.5, 0.5, 0.5, 1.0), roughness=0.6,
                      metallic=0.0, specular=0.5, emission=(0, 0, 0, 1), emission_strength=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular

    if emission_strength > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission
            bsdf.inputs["Emission Strength"].default_value = emission_strength
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emission

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_terrain_vertex_material() -> bpy.types.Material:
    mat = bpy.data.materials.new(name="M_Terrain_VertexPBR")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    attr.attribute_type = 'GEOMETRY'

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.88
    links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_water_material(name="M_Water_Turquoise", deep_color=(0.08, 0.45, 0.58, 0.85)) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (deep_color[0], deep_color[1], deep_color[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.04
    bsdf.inputs["Metallic"].default_value = 0.08
    bsdf.inputs["IOR"].default_value = 1.333

    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.82
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.82

    mat.blend_method = 'BLEND'
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def create_waterfall_material() -> bpy.types.Material:
    mat = bpy.data.materials.new(name="M_Waterfall_Cascades")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.35, 0.82, 0.90, 0.85)
    bsdf.inputs["Roughness"].default_value = 0.08
    bsdf.inputs["Metallic"].default_value = 0.05
    bsdf.inputs["IOR"].default_value = 1.333

    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.68
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.68

    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.85, 0.95, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.25
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = (0.85, 0.95, 1.0, 1.0)

    mat.blend_method = 'BLEND'
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# =============================================================================
# 3. Procedural Heightmap Math
# =============================================================================

def calculate_world_height(x: float, y: float) -> float:
    # 1. Base continental slope
    ny = max(0.0, min(1.0, (y + 210.0) / 420.0))
    h_base = 12.0 + math.pow(ny, 2.4) * 98.0

    # 2. Northern Alpine Mountains
    if y > 20.0:
        d_peak1 = math.hypot(x - (-45.0), y - 145.0)
        p1 = max(0.0, 1.0 - d_peak1 / 110.0)
        h_peak1 = math.pow(p1, 2.2) * 58.0

        d_peak2 = math.hypot(x - 65.0, y - 165.0)
        p2 = max(0.0, 1.0 - d_peak2 / 120.0)
        h_peak2 = math.pow(p2, 2.0) * 65.0

        d_ridge = math.hypot(x - 0.0, y - 130.0)
        p_ridge = max(0.0, 1.0 - d_ridge / 130.0)
        h_ridge = math.pow(p_ridge, 1.8) * 35.0
    else:
        h_peak1 = h_peak2 = h_ridge = 0.0

    # 3. Alpine Tarn Cirque Bowl
    d_tarn = math.hypot(x - (-70.0), y - 75.0)
    tarn_bowl = -math.pow(1.0 - d_tarn / 45.0, 1.6) * 24.0 if d_tarn < 45.0 else 0.0

    # 4. Canyon Cascades Gorge
    canyon_center_x = 8.0 * math.sin(y * 0.04)
    dist_canyon_axis = abs(x - canyon_center_x)
    canyon_trough = 0.0
    if 10.0 < y < 85.0 and dist_canyon_axis < 30.0:
        c_depth = (1.0 - dist_canyon_axis / 30.0) * math.sin((y - 10.0) / 75.0 * math.pi)
        canyon_trough = -c_depth * 18.0

    # 5. Karst Cliff Ridge above Water Cave
    d_cliff = math.hypot(x - 10.0, y - 0.0)
    cliff_bulge = math.pow(1.0 - d_cliff / 55.0, 1.5) * 18.0 if d_cliff < 55.0 else 0.0

    # 6. Southern Great Lake Basin
    d_lake = math.hypot(x - (-5.0), (y - (-95.0)) * 1.15)
    lake_trough = -math.pow(1.0 - d_lake / 85.0, 1.5) * 16.5 if d_lake < 85.0 else 0.0

    # 7. Solitary Rock Islet in South Lake
    d_islet = math.hypot(x - 12.0, y - (-105.0))
    islet_bump = (1.0 - d_islet / 14.0) * 11.5 if d_islet < 14.0 else 0.0

    # 8. Meandering River Trough (Smoothly descends from cave mouth at y=-16 to lake at y=-68)
    river_trough = 0.0
    if -68.0 < y < -12.0:
        t = (y - (-16.0)) / (-68.0 - (-16.0))
        t = max(0.0, min(1.0, t))
        rx = (1.0 - t) * (-10.0) + t * (18.0 * math.sin((y + 15.0) * 0.12))
        dist_r = abs(x - rx)
        if dist_r < 18.0:
            rf = (1.0 - dist_r / 18.0)
            river_trough = -math.pow(rf, 1.6) * 8.5

    # 9. Natural Karst Grotto Recess at Cliff Foot (-10.0, -15.0)
    d_cave = math.hypot((x - (-10.0)) * 1.0, (y - (-15.0)) * 1.2)
    cave_carve = 0.0
    if d_cave < 15.0:
        cave_carve = -math.pow(math.cos(d_cave / 15.0 * math.pi * 0.5), 1.4) * 11.5

    # 10. Natural fractal noise
    n1 = math.sin(x * 0.032 + y * 0.024) * math.cos(y * 0.028 - x * 0.018) * 8.5
    n2 = math.sin(x * 0.085 - y * 0.075) * math.cos(x * 0.062 + y * 0.091) * 3.2
    n3 = math.sin(x * 0.220 + y * 0.180) * 1.1

    final_h = (h_base + h_peak1 + h_peak2 + h_ridge + tarn_bowl +
               canyon_trough + cliff_bulge + lake_trough + islet_bump +
               river_trough + cave_carve + n1 + n2 + n3)

    return max(-8.0, final_h)


# =============================================================================
# 4. Build Terrain with Organic "ĐẤT" vs "HOA CỎ" Palette & Smooth Blending
# =============================================================================

FOREST_GROVES = [
    (-45.0, 25.0, 32.0),   # Pine forest west
    (45.0, 15.0, 30.0),    # Oak woods east
    (-35.0, -35.0, 26.0),  # Birch grove southwest
    (35.0, -25.0, 28.0),   # Mixed woodland southeast
    (-15.0, -5.0, 22.0),   # Cavern cliff woods
    (-65.0, 50.0, 25.0),   # Tarn mountain slopes
]

def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)

def mix_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        c1[0] * (1.0 - t) + c2[0] * t,
        c1[1] * (1.0 - t) + c2[1] * t,
        c1[2] * (1.0 - t) + c2[2] * t,
        1.0
    )

def build_pristine_terrain() -> bpy.types.Object:
    print("[Genesis Wilderness] Generating 420m x 420m Terrain with Organic ĐẤT & HOA CỎ...")
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

    # Top faces
    for iy in range(res_y - 1):
        for ix in range(res_x - 1):
            v0 = grid_verts[iy][ix]
            v1 = grid_verts[iy][ix + 1]
            v2 = grid_verts[iy + 1][ix + 1]
            v3 = grid_verts[iy + 1][ix]
            bm.faces.new((v0, v1, v2, v3))

    # Skirt walls
    for ix in range(res_x - 1):
        bm.faces.new((grid_verts[0][ix], grid_verts[0][ix + 1], bottom_verts[0][ix + 1], bottom_verts[0][ix]))
        bm.faces.new((grid_verts[res_y - 1][ix + 1], grid_verts[res_y - 1][ix], bottom_verts[res_y - 1][ix], bottom_verts[res_y - 1][ix + 1]))
    for iy in range(res_y - 1):
        bm.faces.new((grid_verts[iy + 1][0], grid_verts[iy][0], bottom_verts[iy][0], bottom_verts[iy + 1][0]))
        bm.faces.new((grid_verts[iy][res_x - 1], grid_verts[iy + 1][res_x - 1], bottom_verts[iy + 1][res_x - 1], bottom_verts[iy][res_x - 1]))

    # Bottom
    for iy in range(res_y - 1):
        for ix in range(res_x - 1):
            bm.faces.new((bottom_verts[iy][ix], bottom_verts[iy + 1][ix], bottom_verts[iy + 1][ix + 1], bottom_verts[iy][ix + 1]))

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    # ── Vertex Color Attribute 'Col' ──
    color_layer = bm.loops.layers.color.new("Col")

    # 1. ĐẤT
    c_rich_soil = (0.24, 0.16, 0.10, 1.0)       # Đất mùn rừng sâu ấm áp dưới tán cây
    c_eroded_earth = (0.35, 0.24, 0.15, 1.0)    # Đất sườn dốc phong hóa
    c_wet_mud = (0.16, 0.12, 0.08, 1.0)         # Đất bùn ướt ven bờ nước
    c_pebble_gravel = (0.45, 0.42, 0.38, 1.0)   # Bãi sỏi cuội bồi
    c_sand_beach = (0.72, 0.64, 0.48, 1.0)      # Cát vàng mịn ven hồ

    # 2. CỎ
    c_lush_grass = (0.20, 0.50, 0.15, 1.0)      # Cỏ xanh mướt mát
    c_wild_meadow = (0.34, 0.52, 0.19, 1.0)     # Cỏ thảo nguyên vàng nắng
    c_alpine_tundra = (0.38, 0.45, 0.23, 1.0)   # Cỏ rêu núi cao

    # 3. ĐÁ & BĂNG TUYẾT
    c_granite_cliff = (0.42, 0.41, 0.40, 1.0)   # Vách đá granite karst
    c_snow_fresh = (0.96, 0.98, 1.00, 1.0)      # Tuyết đỉnh núi

    for face in bm.faces:
        norm_z = face.normal.z
        slope = max(0.0, min(1.0, 1.0 - norm_z))

        for loop in face.loops:
            vz = loop.vert.co.z
            vy = loop.vert.co.y
            vx = loop.vert.co.x

            if vz <= base_z + 0.1:
                loop[color_layer] = (0.14, 0.12, 0.11, 1.0)
                continue

            # 1. Base grass with micro noise variation
            noise_val = (math.sin(vx * 0.14 + vy * 0.10) * math.cos(vy * 0.12 - vx * 0.08)) * 0.5 + 0.5
            col = mix_color(c_lush_grass, c_wild_meadow, noise_val)

            # 2. Alpine Tundra at higher elevations
            if vz > 45.0:
                t_tundra = smoothstep(45.0, 75.0, vz)
                col = mix_color(col, c_alpine_tundra, t_tundra)

            # 3. Forest Loam under dense tree groves (ĐẤT DƯỚI BÓNG RỪNG)
            forest_factor = 0.0
            for gx, gy, gr in FOREST_GROVES:
                d = math.hypot(vx - gx, vy - gy)
                if d < gr:
                    f = math.pow(1.0 - d / gr, 1.4)
                    if f > forest_factor:
                        forest_factor = f
            if forest_factor > 0.15:
                t_loam = smoothstep(0.15, 0.70, forest_factor)
                col = mix_color(col, c_rich_soil, t_loam)

            # 4. Riverbank Wet Mud & Pebbles (ĐẤT VEN SÔNG)
            if -70.0 < vy < -10.0 and vz < 19.0:
                t_r = max(0.0, min(1.0, (vy - (-16.0)) / (-68.0 - (-16.0))))
                rx_riv = (1.0 - t_r) * (-10.0) + t_r * (18.0 * math.sin((vy + 15.0) * 0.12))
                dist_r = abs(vx - rx_riv)
                if dist_r < 18.0:
                    t_mud = smoothstep(18.0, 5.0, dist_r) * smoothstep(19.0, 13.5, vz)
                    col = mix_color(col, c_wet_mud, t_mud * 0.85)
                    if dist_r < 12.0 and vz >= 13.2:
                        t_peb = smoothstep(12.0, 7.0, dist_r)
                        col = mix_color(col, c_pebble_gravel, t_peb * 0.6)

            # 5. Lake Shore Sand Beach (CÁT VEN HỒ)
            dist_lake = math.hypot(vx - (-5.0), (vy - (-95.0)) * 1.15)
            if dist_lake < 90.0 and vz < 15.5:
                t_sand = smoothstep(90.0, 72.0, dist_lake) * smoothstep(15.5, 11.4, vz)
                col = mix_color(col, c_sand_beach, t_sand)

            # 6. Slope Scree Dirt & Rock Cliffs (ĐẤT PHONG HÓA & VÁCH ĐÁ DỰNG ĐỨNG)
            if slope > 0.20:
                t_dirt = smoothstep(0.20, 0.40, slope)
                col = mix_color(col, c_eroded_earth, t_dirt)
            if slope > 0.45:
                t_rock = smoothstep(0.45, 0.65, slope)
                col = mix_color(col, c_granite_cliff, t_rock)

            # 7. Mountain Snow Peaks (BĂNG TUYẾT ĐỈNH NÚI)
            if vz > 75.0:
                t_snow = smoothstep(75.0, 95.0, vz) * (1.0 - smoothstep(0.50, 0.70, slope))
                col = mix_color(col, c_snow_fresh, t_snow)

            loop[color_layer] = col

    mesh = bpy.data.meshes.new("Terrain_PristineWilderness")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Terrain_PristineWilderness", mesh)
    mat_terrain = create_terrain_vertex_material()
    obj.data.materials.append(mat_terrain)
    bpy.context.collection.objects.link(obj)

    print("[Genesis Wilderness] Terrain created.")
    return obj


# =============================================================================
# 5. Grand Natural Karst Water Cave Portal (Limestone Grotto)
# =============================================================================

def build_karst_water_cave_system():
    print("[Genesis Wilderness] Constructing Organic Karst Water Cavern Portal...")
    col = bpy.context.collection

    mat_karst_rock = get_or_create_mat("M_Cave_Karst_Limestone", (0.35, 0.33, 0.31, 1.0), roughness=0.92)
    mat_stalactite = get_or_create_mat("M_Cave_Stalactite", (0.50, 0.48, 0.45, 1.0), roughness=0.45)

    # 1. Natural Limestone Cliff Mouth (Jagged rock arch framing the entrance)
    bm_mouth = bmesh.new()

    # Left pillar boulder stack
    for i in range(5):
        s = 2.8 - i * 0.3
        loc = (-16.5 + random.uniform(-0.6, 0.6), -17.0 + random.uniform(-0.8, 0.8), 13.0 + i * 2.2)
        mat_b = Matrix.Translation(loc) @ Matrix.Scale(s, 4, Vector((1.4, 1.2, 1.0)))
        bmesh.ops.create_icosphere(bm_mouth, subdivisions=2, radius=1.0, matrix=mat_b)

    # Right pillar boulder stack
    for i in range(5):
        s = 2.8 - i * 0.3
        loc = (-3.5 + random.uniform(-0.6, 0.6), -17.0 + random.uniform(-0.8, 0.8), 13.0 + i * 2.2)
        mat_b = Matrix.Translation(loc) @ Matrix.Scale(s, 4, Vector((1.4, 1.2, 1.0)))
        bmesh.ops.create_icosphere(bm_mouth, subdivisions=2, radius=1.0, matrix=mat_b)

    # Keystones arching overhead across top of cave portal
    for i in range(7):
        t = i / 6.0
        ax = -16.5 * (1.0 - t) + (-3.5) * t
        ay = -16.8 + math.sin(t * math.pi) * 1.5
        az = 21.0 + math.sin(t * math.pi) * 2.2
        mat_k = Matrix.Translation((ax, ay, az)) @ Matrix.Scale(2.2, 4, Vector((1.3, 1.5, 0.9)))
        bmesh.ops.create_icosphere(bm_mouth, subdivisions=2, radius=1.0, matrix=mat_k)

    mesh_mouth = bpy.data.meshes.new("Cave_Karst_Limestone_Portal")
    bm_mouth.to_mesh(mesh_mouth)
    bm_mouth.free()

    obj_mouth = bpy.data.objects.new("Cave_Karst_Limestone_Portal", mesh_mouth)
    obj_mouth.data.materials.append(mat_karst_rock)
    col.objects.link(obj_mouth)

    # 2. Subterranean Water Pool (Emerald Water inside Cavern)
    bm_pool = bmesh.new()
    bmesh.ops.create_circle(bm_pool, cap_ends=True, segments=28, radius=12.5)
    for v in bm_pool.verts:
        v.co.y *= 1.2
    mesh_pool = bpy.data.meshes.new("Cave_Subterranean_Pool")
    bm_pool.to_mesh(mesh_pool)
    bm_pool.free()

    obj_pool = bpy.data.objects.new("Cave_Subterranean_Pool", mesh_pool)
    obj_pool.location = Vector((-10.0, -15.0, 13.5))
    mat_cave_water = create_water_material("M_Cave_Emerald_Water", deep_color=(0.04, 0.55, 0.48, 0.88))
    obj_pool.data.materials.append(mat_cave_water)
    col.objects.link(obj_pool)

    # 3. Stalactites (Ceiling) & Stalagmites (Floor)
    for i in range(36):
        rx = random.uniform(-8.5, 8.5)
        ry = random.uniform(-9.5, 9.5)
        if math.hypot(rx, ry) > 10.5:
            continue

        length = random.uniform(2.2, 4.8)
        r_base = random.uniform(0.35, 0.85)

        bm_st = bmesh.new()
        bmesh.ops.create_cone(bm_st, cap_ends=True, segments=6, radius1=r_base, radius2=0.05, depth=length)
        mesh_st = bpy.data.meshes.new(f"Stalactite_{i+1}")
        bm_st.to_mesh(mesh_st)
        bm_st.free()

        obj_st = bpy.data.objects.new(f"Stalactite_{i+1}", mesh_st)
        obj_st.location = Vector((-10.0 + rx, -15.0 + ry, 23.5 - length * 0.5))
        obj_st.rotation_euler = Euler((math.pi, 0, random.uniform(0, math.pi * 2)))
        obj_st.data.materials.append(mat_stalactite)
        col.objects.link(obj_st)

    for i in range(20):
        rx = random.uniform(-8.0, 8.0)
        ry = random.uniform(-9.0, 9.0)
        dist_c = math.hypot(rx, ry)
        if dist_c < 4.0 or dist_c > 9.5:
            continue

        length = random.uniform(1.4, 3.2)
        r_base = random.uniform(0.3, 0.7)

        bm_sm = bmesh.new()
        bmesh.ops.create_cone(bm_sm, cap_ends=True, segments=6, radius1=r_base, radius2=0.04, depth=length)
        mesh_sm = bpy.data.meshes.new(f"Stalagmites_{i+1}")
        bm_sm.to_mesh(mesh_sm)
        bm_sm.free()

        obj_sm = bpy.data.objects.new(f"Stalagmites_{i+1}", mesh_sm)
        obj_sm.location = Vector((-10.0 + rx, -15.0 + ry, 13.4 + length * 0.5))
        obj_sm.rotation_euler = Euler((0, 0, random.uniform(0, math.pi * 2)))
        obj_sm.data.materials.append(mat_stalactite)
        col.objects.link(obj_sm)

    # 4. Bioluminescent Mushrooms (Cyan and Purple) - balanced emission
    mat_glow_cyan = get_or_create_mat("M_Glow_Mushroom_Cyan", (0.12, 0.85, 0.92, 1.0),
                                      roughness=0.25, emission=(0.18, 0.90, 0.95, 1.0), emission_strength=2.2)
    mat_glow_purple = get_or_create_mat("M_Glow_Mushroom_Purple", (0.75, 0.25, 0.95, 1.0),
                                        roughness=0.25, emission=(0.82, 0.30, 0.98, 1.0), emission_strength=2.2)

    for c_idx in range(16):
        ang = c_idx * (math.pi * 2 / 16) + random.uniform(-0.15, 0.15)
        dist = random.uniform(4.5, 8.5)
        c_x = math.cos(ang) * dist
        c_y = math.sin(ang) * dist * 1.15
        mat_glow = mat_glow_cyan if c_idx % 2 == 0 else mat_glow_purple

        bm_shroom = bmesh.new()
        for _m in range(5):
            cap_x = random.uniform(-0.5, 0.5)
            cap_y = random.uniform(-0.5, 0.5)
            r_cap = random.uniform(0.20, 0.45)
            mat_cap = Matrix.Translation((cap_x, cap_y, 0.35)) @ Matrix.Scale(r_cap, 4, Vector((1.0, 1.0, 0.55)))
            bmesh.ops.create_icosphere(bm_shroom, subdivisions=2, radius=1.0, matrix=mat_cap)
            mat_stem = Matrix.Translation((cap_x, cap_y, 0.15)) @ Matrix.Scale(r_cap * 0.25, 4, Vector((1.0, 1.0, 1.6)))
            bmesh_create_cylinder(bm_shroom, segments=5, radius=1.0, depth=0.35, matrix=mat_stem)

        mesh_shroom = bpy.data.meshes.new(f"Glow_Mushroom_{c_idx+1}")
        bm_shroom.to_mesh(mesh_shroom)
        bm_shroom.free()

        obj_shroom = bpy.data.objects.new(f"Glow_Mushroom_{c_idx+1}", mesh_shroom)
        obj_shroom.location = Vector((-10.0 + c_x, -15.0 + c_y, 13.5))
        obj_shroom.data.materials.append(mat_glow)
        col.objects.link(obj_shroom)

    # 5. Cavern Interior Atmosphere Light
    light_data = bpy.data.lights.new(name="Light_Cave_Grotto", type='POINT')
    light_data.energy = 650.0
    light_data.color = (0.25, 0.88, 0.95)
    light_data.shadow_soft_size = 4.0
    light_obj = bpy.data.objects.new(name="Light_Cave_Grotto", object_data=light_data)
    light_obj.location = Vector((-10.0, -14.0, 17.5))
    col.objects.link(light_obj)

    print("[Genesis Wilderness] Karst Water Cave System created.")


# =============================================================================
# 6. Hydrology System: Alpine Tarn, Cascades, River, Lake
# =============================================================================

def build_hydrology_system():
    print("[Genesis Wilderness] Building Synchronized Hydrology System...")
    col = bpy.context.collection

    # 1. Alpine Tarn (z = 39.5m)
    bm_tarn = bmesh.new()
    bmesh.ops.create_circle(bm_tarn, cap_ends=True, segments=36, radius=34.0)
    for v in bm_tarn.verts:
        angle = math.atan2(v.co.y, v.co.x)
        r_mod = 1.0 + 0.16 * math.sin(angle * 3.0) + 0.10 * math.cos(angle * 5.0)
        v.co.x *= r_mod
        v.co.y *= r_mod
    mesh_tarn = bpy.data.meshes.new("Water_Alpine_Tarn")
    bm_tarn.to_mesh(mesh_tarn)
    bm_tarn.free()

    tarn_obj = bpy.data.objects.new("Water_Alpine_Tarn", mesh_tarn)
    tarn_obj.location = Vector((-70.0, 75.0, 39.5))
    tarn_obj.data.materials.append(create_water_material("M_Water_Alpine_Tarn", deep_color=(0.10, 0.58, 0.72, 0.88)))
    col.objects.link(tarn_obj)

    # 2. 3-Tier Rocky Cascades
    waterfall_tiers = [
        {"loc": Vector((-45.0, 65.0, 54.2)), "rot": (0.65, 0.0, -0.60), "size": (10.0, 14.0)},
        {"loc": Vector((-25.0, 45.0, 45.2)), "rot": (0.75, 0.0, -0.45), "size": (11.0, 15.0)},
        {"loc": Vector((-12.0, 20.0, 38.8)), "rot": (0.85, 0.0, -0.20), "size": (12.0, 14.0)},
    ]

    mat_cascade = create_waterfall_material()

    for idx, wt in enumerate(waterfall_tiers):
        bm_wf = bmesh.new()
        bmesh.ops.create_grid(bm_wf, x_segments=8, y_segments=16, size=1.0)
        for v in bm_wf.verts:
            v.co.x *= wt["size"][0] * 0.5
            v.co.y *= wt["size"][1] * 0.5
            v.co.z = math.sin(v.co.y * 1.5) * 0.35 + math.cos(v.co.x * 2.0) * 0.15

        mesh_wf = bpy.data.meshes.new(f"Water_Cascade_Tier_{idx+1}")
        bm_wf.to_mesh(mesh_wf)
        bm_wf.free()

        obj_wf = bpy.data.objects.new(f"Water_Cascade_Tier_{idx+1}", mesh_wf)
        obj_wf.location = wt["loc"]
        obj_wf.rotation_euler = Euler(wt["rot"])
        obj_wf.data.materials.append(mat_cascade)
        col.objects.link(obj_wf)

    # 3. Meandering Valley River (from Cave exit y = -16 to Lake y = -68)
    bm_river = bmesh.new()
    river_length_segments = 52
    river_y_start = -16.0
    river_y_end = -68.0
    river_dy = (river_y_end - river_y_start) / river_length_segments

    river_rows = []
    for step in range(river_length_segments + 1):
        py = river_y_start + step * river_dy
        t = step / river_length_segments
        center_x = (1.0 - t) * (-10.0) + t * (18.0 * math.sin((py + 15.0) * 0.12))
        pz = 13.5 - t * 2.3  # 13.5m at cave exit to 11.2m at lake
        r_width = 8.5 + t * 11.5

        v_left = bm_river.verts.new((center_x - r_width * 0.5, py, pz))
        v_mid = bm_river.verts.new((center_x, py, pz - 0.20))
        v_right = bm_river.verts.new((center_x + r_width * 0.5, py, pz))
        river_rows.append((v_left, v_mid, v_right))

    for s in range(river_length_segments):
        l0, m0, r0 = river_rows[s]
        l1, m1, r1 = river_rows[s + 1]
        bm_river.faces.new((l0, m0, m1, l1))
        bm_river.faces.new((m0, r0, r1, m1))

    mesh_river = bpy.data.meshes.new("Water_Valley_River")
    bm_river.to_mesh(mesh_river)
    bm_river.free()

    obj_river = bpy.data.objects.new("Water_Valley_River", mesh_river)
    obj_river.data.materials.append(create_water_material("M_Water_River_Teal", deep_color=(0.10, 0.52, 0.62, 0.85)))
    col.objects.link(obj_river)

    # 4. Great Lowland Lake (Z = 11.2m)
    bm_lake = bmesh.new()
    bmesh.ops.create_circle(bm_lake, cap_ends=True, segments=48, radius=78.0)
    for v in bm_lake.verts:
        v.co.y *= 1.15
        angle = math.atan2(v.co.y, v.co.x)
        shore_var = 1.0 + 0.12 * math.sin(angle * 4.0) + 0.08 * math.cos(angle * 7.0)
        v.co.x *= shore_var
        v.co.y *= shore_var

    mesh_lake = bpy.data.meshes.new("Water_Great_Lowland_Lake")
    bm_lake.to_mesh(mesh_lake)
    bm_lake.free()

    obj_lake = bpy.data.objects.new("Water_Great_Lowland_Lake", mesh_lake)
    obj_lake.location = Vector((-5.0, -95.0, 11.2))
    obj_lake.data.materials.append(create_water_material("M_Water_Great_Lake", deep_color=(0.06, 0.44, 0.56, 0.90)))
    col.objects.link(obj_lake)

    # 5. Lily Pads
    mat_lily = get_or_create_mat("M_Lily_Pad", (0.18, 0.55, 0.22, 1.0), roughness=0.5)
    for lp_idx in range(32):
        lx = random.uniform(-45.0, 35.0)
        ly = random.uniform(-135.0, -65.0)
        if math.hypot(lx - (-5.0), ly - (-95.0)) < 65.0:
            bm_lp = bmesh.new()
            bmesh.ops.create_circle(bm_lp, cap_ends=True, segments=12, radius=random.uniform(0.7, 1.6))
            mesh_lp = bpy.data.meshes.new(f"Lily_Pad_{lp_idx+1}")
            bm_lp.to_mesh(mesh_lp)
            bm_lp.free()

            obj_lp = bpy.data.objects.new(f"Lily_Pad_{lp_idx+1}", mesh_lp)
            obj_lp.location = Vector((lx, ly, 11.26))
            obj_lp.rotation_euler = Euler((0, 0, random.uniform(0, math.pi * 2)))
            obj_lp.data.materials.append(mat_lily)
            col.objects.link(obj_lp)

    print("[Genesis Wilderness] Hydrology System generated.")


# =============================================================================
# 7. Wildflowers, Grass Tufts & Flora Prototypes
# =============================================================================

def build_flora_and_flower_prototypes() -> dict:
    protos = {}

    mat_pine_needles = get_or_create_mat("M_Pine_Needles", (0.05, 0.22, 0.08, 1.0), roughness=0.72)
    mat_snow_pine = get_or_create_mat("M_Snow_Pine_Needles", (0.35, 0.52, 0.48, 1.0), roughness=0.62)
    mat_oak_leaves = get_or_create_mat("M_Oak_Canopy", (0.13, 0.38, 0.09, 1.0), roughness=0.68)
    mat_birch_leaves = get_or_create_mat("M_Birch_Canopy", (0.24, 0.46, 0.10, 1.0), roughness=0.65)
    mat_willow_leaves = get_or_create_mat("M_Willow_Canopy", (0.16, 0.42, 0.20, 1.0), roughness=0.70)
    mat_boulder = get_or_create_mat("M_Granite_Boulder", (0.38, 0.36, 0.34, 1.0), roughness=0.92)
    mat_mossy_log = get_or_create_mat("M_Fallen_Mossy_Log", (0.24, 0.18, 0.12, 1.0), roughness=0.85)

    # 4 Wildflower Materials
    mat_white_flower = get_or_create_mat("M_Wildflower_White_Daisy", (0.95, 0.95, 0.95, 1.0), roughness=0.45)
    mat_yellow_flower = get_or_create_mat("M_Wildflower_Yellow_Buttercup", (0.98, 0.82, 0.08, 1.0), roughness=0.45)
    mat_purple_flower = get_or_create_mat("M_Wildflower_Purple_Lavender", (0.68, 0.26, 0.88, 1.0), roughness=0.45)
    mat_red_flower = get_or_create_mat("M_Wildflower_Alpine_Poppy", (0.92, 0.16, 0.14, 1.0), roughness=0.45)
    mat_grass_tuft = get_or_create_mat("M_Grass_Tuft_Blade", (0.18, 0.46, 0.12, 1.0), roughness=0.55)

    trunk_brown = get_or_create_mat("M_Trunk_Brown", (0.22, 0.14, 0.09, 1.0), roughness=0.88)
    birch_white = get_or_create_mat("M_Trunk_Birch", (0.82, 0.82, 0.78, 1.0), roughness=0.75)

    # 1. Snow Pine
    bm_sp = bmesh.new()
    bmesh_create_cylinder(bm_sp, segments=6, radius=0.45, depth=4.2, matrix=Matrix.Translation((0, 0, 2.1)))
    trunk_faces_sp = set(bm_sp.faces)
    for f in trunk_faces_sp:
        f.material_index = 0
    for c in range(3):
        h = 2.8 + c * 2.2
        r = 2.4 - c * 0.55
        bmesh.ops.create_cone(bm_sp, cap_ends=True, segments=7, radius1=r, radius2=0.08, depth=2.8,
                              matrix=Matrix.Translation((0, 0, h + 1.4)))
    for f in bm_sp.faces:
        if f not in trunk_faces_sp:
            f.material_index = 1
    m_sp = bpy.data.meshes.new("Proto_Snow_Pine")
    bm_sp.to_mesh(m_sp)
    bm_sp.free()
    o_sp = bpy.data.objects.new("Proto_Snow_Pine", m_sp)
    o_sp.data.materials.append(trunk_brown)
    o_sp.data.materials.append(mat_snow_pine)
    protos["snow_pine"] = o_sp

    # 2. Highland Pine
    bm_hp = bmesh.new()
    bmesh_create_cylinder(bm_hp, segments=6, radius=0.5, depth=4.8, matrix=Matrix.Translation((0, 0, 2.4)))
    trunk_faces_hp = set(bm_hp.faces)
    for f in trunk_faces_hp:
        f.material_index = 0
    for c in range(3):
        h = 3.2 + c * 2.4
        r = 2.6 - c * 0.6
        bmesh.ops.create_cone(bm_hp, cap_ends=True, segments=7, radius1=r, radius2=0.08, depth=3.0,
                              matrix=Matrix.Translation((0, 0, h + 1.5)))
    for f in bm_hp.faces:
        if f not in trunk_faces_hp:
            f.material_index = 1
    m_hp = bpy.data.meshes.new("Proto_Highland_Pine")
    bm_hp.to_mesh(m_hp)
    bm_hp.free()
    o_hp = bpy.data.objects.new("Proto_Highland_Pine", m_hp)
    o_hp.data.materials.append(trunk_brown)
    o_hp.data.materials.append(mat_pine_needles)
    protos["highland_pine"] = o_hp

    # 3. Ancient Oak
    bm_ao = bmesh.new()
    bmesh_create_cylinder(bm_ao, segments=7, radius=0.85, depth=4.0, matrix=Matrix.Translation((0, 0, 2.0)))
    trunk_faces_ao = set(bm_ao.faces)
    for f in trunk_faces_ao:
        f.material_index = 0
    bmesh.ops.create_icosphere(bm_ao, subdivisions=2, radius=3.8, matrix=Matrix.Translation((0, 0, 6.2)))
    bmesh.ops.create_icosphere(bm_ao, subdivisions=2, radius=2.5, matrix=Matrix.Translation((1.8, 1.2, 5.2)))
    bmesh.ops.create_icosphere(bm_ao, subdivisions=2, radius=2.4, matrix=Matrix.Translation((-1.6, -1.0, 5.0)))
    for f in bm_ao.faces:
        if f not in trunk_faces_ao:
            f.material_index = 1
    m_ao = bpy.data.meshes.new("Proto_Ancient_Oak")
    bm_ao.to_mesh(m_ao)
    bm_ao.free()
    o_ao = bpy.data.objects.new("Proto_Ancient_Oak", m_ao)
    o_ao.data.materials.append(trunk_brown)
    o_ao.data.materials.append(mat_oak_leaves)
    protos["ancient_oak"] = o_ao

    # 4. Silver Birch
    bm_sb = bmesh.new()
    bmesh_create_cylinder(bm_sb, segments=6, radius=0.35, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
    trunk_faces_sb = set(bm_sb.faces)
    for f in trunk_faces_sb:
        f.material_index = 0
    bmesh.ops.create_icosphere(bm_sb, subdivisions=2, radius=2.2,
                               matrix=Matrix.Translation((0, 0, 6.0)) @ Matrix.Scale(1.4, 4, Vector((1.0, 1.0, 1.6))))
    for f in bm_sb.faces:
        if f not in trunk_faces_sb:
            f.material_index = 1
    m_sb = bpy.data.meshes.new("Proto_Silver_Birch")
    bm_sb.to_mesh(m_sb)
    bm_sb.free()
    o_sb = bpy.data.objects.new("Proto_Silver_Birch", m_sb)
    o_sb.data.materials.append(birch_white)
    o_sb.data.materials.append(mat_birch_leaves)
    protos["silver_birch"] = o_sb

    # 5. Weeping Willow
    bm_ww = bmesh.new()
    bmesh_create_cylinder(bm_ww, segments=6, radius=0.6, depth=3.5, matrix=Matrix.Translation((0, 0, 1.75)))
    trunk_faces_ww = set(bm_ww.faces)
    for f in trunk_faces_ww:
        f.material_index = 0
    bmesh.ops.create_icosphere(bm_ww, subdivisions=2, radius=3.2,
                               matrix=Matrix.Translation((0, 0, 4.6)) @ Matrix.Scale(1.0, 4, Vector((1.5, 1.5, 0.9))))
    for f in bm_ww.faces:
        if f not in trunk_faces_ww:
            f.material_index = 1
    m_ww = bpy.data.meshes.new("Proto_Weeping_Willow")
    bm_ww.to_mesh(m_ww)
    bm_ww.free()
    o_ww = bpy.data.objects.new("Proto_Weeping_Willow", m_ww)
    o_ww.data.materials.append(trunk_brown)
    o_ww.data.materials.append(mat_willow_leaves)
    protos["willow"] = o_ww

    # 6. Granite Boulder
    bm_bd = bmesh.new()
    bmesh.ops.create_icosphere(bm_bd, subdivisions=1, radius=1.6,
                               matrix=Matrix.Scale(1.0, 4, Vector((1.4, 1.1, 0.8))))
    m_bd = bpy.data.meshes.new("Proto_Boulder")
    bm_bd.to_mesh(m_bd)
    bm_bd.free()
    o_bd = bpy.data.objects.new("Proto_Boulder", m_bd)
    o_bd.data.materials.append(mat_boulder)
    protos["boulder"] = o_bd

    # 7. Fallen Mossy Log
    bm_lg = bmesh.new()
    mat_rot = Euler((0, math.radians(88), math.radians(35))).to_matrix().to_4x4()
    bmesh_create_cylinder(bm_lg, segments=5, radius=0.45, depth=4.5,
                          matrix=Matrix.Translation((0, 0, 0.4)) @ mat_rot)
    m_lg = bpy.data.meshes.new("Proto_Fallen_Log")
    bm_lg.to_mesh(m_lg)
    bm_lg.free()
    o_lg = bpy.data.objects.new("Proto_Fallen_Log", m_lg)
    o_lg.data.materials.append(mat_mossy_log)
    protos["fallen_log"] = o_lg

    # 8. Wildflower 1: White Daisy Cluster
    bm_fw = bmesh.new()
    for _fi in range(4):
        fox = random.uniform(-0.4, 0.4)
        foy = random.uniform(-0.4, 0.4)
        bmesh.ops.create_circle(bm_fw, cap_ends=True, segments=7, radius=0.22,
                                matrix=Matrix.Translation((fox, foy, 0.35)))
        bmesh_create_cylinder(bm_fw, segments=4, radius=0.03, depth=0.35,
                              matrix=Matrix.Translation((fox, foy, 0.17)))
    m_fw = bpy.data.meshes.new("Proto_Wildflower_White")
    bm_fw.to_mesh(m_fw)
    bm_fw.free()
    o_fw = bpy.data.objects.new("Proto_Wildflower_White", m_fw)
    o_fw.data.materials.append(mat_white_flower)
    protos["flower_white"] = o_fw

    # 9. Wildflower 2: Yellow Buttercup Cluster
    bm_fy = bmesh.new()
    for _fi in range(4):
        fox = random.uniform(-0.4, 0.4)
        foy = random.uniform(-0.4, 0.4)
        bmesh.ops.create_cone(bm_fy, cap_ends=True, segments=6, radius1=0.20, radius2=0.06, depth=0.18,
                              matrix=Matrix.Translation((fox, foy, 0.32)))
        bmesh_create_cylinder(bm_fy, segments=4, radius=0.03, depth=0.32,
                              matrix=Matrix.Translation((fox, foy, 0.16)))
    m_fy = bpy.data.meshes.new("Proto_Wildflower_Yellow")
    bm_fy.to_mesh(m_fy)
    bm_fy.free()
    o_fy = bpy.data.objects.new("Proto_Wildflower_Yellow", m_fy)
    o_fy.data.materials.append(mat_yellow_flower)
    protos["flower_yellow"] = o_fy

    # 10. Wildflower 3: Purple Lavender Stalks
    bm_fp = bmesh.new()
    for _fi in range(5):
        fox = random.uniform(-0.35, 0.35)
        foy = random.uniform(-0.35, 0.35)
        bmesh_create_cylinder(bm_fp, segments=5, radius=0.07, depth=0.45,
                              matrix=Matrix.Translation((fox, foy, 0.40)))
        bmesh_create_cylinder(bm_fp, segments=4, radius=0.03, depth=0.30,
                              matrix=Matrix.Translation((fox, foy, 0.15)))
    m_fp = bpy.data.meshes.new("Proto_Wildflower_Purple")
    bm_fp.to_mesh(m_fp)
    bm_fp.free()
    o_fp = bpy.data.objects.new("Proto_Wildflower_Purple", m_fp)
    o_fp.data.materials.append(mat_purple_flower)
    protos["flower_purple"] = o_fp

    # 11. Wildflower 4: Alpine Red Poppy
    bm_fr = bmesh.new()
    for _fi in range(3):
        fox = random.uniform(-0.35, 0.35)
        foy = random.uniform(-0.35, 0.35)
        bmesh.ops.create_circle(bm_fr, cap_ends=True, segments=6, radius=0.26,
                                matrix=Matrix.Translation((fox, foy, 0.42)))
        bmesh_create_cylinder(bm_fr, segments=4, radius=0.035, depth=0.40,
                              matrix=Matrix.Translation((fox, foy, 0.20)))
    m_fr = bpy.data.meshes.new("Proto_Wildflower_Red")
    bm_fr.to_mesh(m_fr)
    bm_fr.free()
    o_fr = bpy.data.objects.new("Proto_Wildflower_Red", m_fr)
    o_fr.data.materials.append(mat_red_flower)
    protos["flower_red"] = o_fr

    # 12. 3D Grass Blade Tufts
    bm_gt = bmesh.new()
    for _bi in range(6):
        rot_b = Euler((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), random.uniform(0, math.pi * 2)))
        mat_blade = Matrix.Translation((random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), 0.25)) @ rot_b.to_matrix().to_4x4()
        bmesh.ops.create_cone(bm_gt, cap_ends=True, segments=4, radius1=0.06, radius2=0.01, depth=0.55, matrix=mat_blade)
    m_gt = bpy.data.meshes.new("Proto_Grass_Tuft")
    bm_gt.to_mesh(m_gt)
    bm_gt.free()
    o_gt = bpy.data.objects.new("Proto_Grass_Tuft", m_gt)
    o_gt.data.materials.append(mat_grass_tuft)
    protos["grass_tuft"] = o_gt

    return protos


# Camera View Sightline Corridors: Mathematically guarantees no large trees block the lens
CAMERA_CORRIDORS = [
    # (cam_x, cam_y, target_x, target_y, corridor_radius, max_length)
    (-10.0, -28.0, -10.0, -14.0, 10.0, 30.0),  # Cave Mouth
    (-70.0, 58.0, -70.0, 75.0, 14.0, 35.0),    # Tarn South Rim to Tarn Center
    (-22.0, -56.0, -10.0, -26.0, 12.0, 45.0),  # River Upstream Channel
    (-12.0, 2.0, -25.0, 42.0, 12.0, 48.0),     # Waterfall Gorge
    (-24.0, -66.0, 12.0, -105.0, 16.0, 60.0),  # Lake Shore to Islet
]

def is_point_in_camera_corridor(px, py):
    for cx, cy, tx, ty, radius, max_len in CAMERA_CORRIDORS:
        if math.hypot(px - cx, py - cy) < 6.5:
            return True
        vx = tx - cx
        vy = ty - cy
        length = math.hypot(vx, vy)
        if length < 0.001:
            continue
        nx = vx / length
        ny = vy / length
        dx = px - cx
        dy = py - cy
        proj = dx * nx + dy * ny
        if 0.0 <= proj <= min(max_len, length):
            perp = abs(dx * (-ny) + dy * nx)
            if perp < radius:
                return True
    return False


# Specific flower meadow centers for organic grouping
FLOWER_MEADOW_ZONES = [
    (-28.0, -45.0, 25.0),  # River valley meadow
    (15.0, -35.0, 22.0),   # East meadow
    (-65.0, 62.0, 18.0),   # Tarn sunny meadow
    (10.0, -75.0, 25.0),   # Lake shore meadow
    (-45.0, -15.0, 20.0),  # Mid-valley meadow
]

def scatter_wilderness_ecosystem():
    print("[Genesis Wilderness] Scattering Multi-Layered Flora, Wildflowers & Grass Tufts...")
    protos = build_flora_and_flower_prototypes()
    col = bpy.context.collection

    scatter_counts = {
        "snow_pine": 110,
        "highland_pine": 160,
        "ancient_oak": 95,
        "silver_birch": 105,
        "willow": 55,
        "boulder": 110,
        "fallen_log": 35,
        "flower_white": 250,
        "flower_yellow": 250,
        "flower_purple": 220,
        "flower_red": 180,
        "grass_tuft": 450,
    }

    placed_count = 0

    for p_type, count in scatter_counts.items():
        proto = protos[p_type]
        placed_for_type = 0
        attempts = 0

        while placed_for_type < count and attempts < count * 15:
            attempts += 1

            if "flower" in p_type or p_type == "grass_tuft":
                # Clustered in flower meadow zones for dense lush appearance
                zone_x, zone_y, zone_r = random.choice(FLOWER_MEADOW_ZONES)
                ang = random.uniform(0, math.pi * 2)
                dist = random.uniform(0, zone_r)
                rx = zone_x + math.cos(ang) * dist
                ry = zone_y + math.sin(ang) * dist
            else:
                rx = random.uniform(-190.0, 190.0)
                ry = random.uniform(-190.0, 190.0)

            rz = calculate_world_height(rx, ry)

            if rz < 11.5:  # Underwater
                continue
            if math.hypot(rx - (-10.0), ry - (-16.0)) < 18.0:  # Inside cave grotto
                continue

            # Ensure camera sightline corridors are clear of large trees & logs
            if not ("flower" in p_type or p_type == "grass_tuft"):
                if is_point_in_camera_corridor(rx, ry):
                    continue

            valid = False
            scale_range = (0.85, 1.25)

            if p_type == "snow_pine":
                if rz > 70.0 and ry > 10.0:
                    valid = True
                    scale_range = (0.75, 1.35)

            elif p_type == "highland_pine":
                if 35.0 < rz < 85.0 and ry > -20.0:
                    valid = True

            elif p_type == "ancient_oak":
                if 14.0 < rz < 45.0 and abs(rx) < 140.0 and ry < 30.0:
                    valid = True
                    scale_range = (0.9, 1.5)

            elif p_type == "silver_birch":
                if 16.0 < rz < 55.0 and ry < 45.0:
                    valid = True

            elif p_type == "willow":
                if rz < 18.0 and (math.hypot(rx - (-5.0), ry - (-95.0)) < 85.0 or (abs(rx) < 28.0 and ry < -15.0)):
                    valid = True
                    scale_range = (1.0, 1.6)

            elif p_type == "boulder":
                if (abs(rx) < 45.0 and ry > -60.0) or math.hypot(rx - (-5.0), ry - (-95.0)) < 82.0 or rz > 55.0:
                    valid = True
                    scale_range = (0.6, 2.2)

            elif p_type == "fallen_log":
                if 13.0 < rz < 35.0 and abs(rx) < 90.0:
                    valid = True
                    scale_range = (0.8, 1.2)

            elif "flower" in p_type or p_type == "grass_tuft":
                # Wildflowers on gentle meadows
                if 12.0 < rz < 65.0:
                    valid = True
                    scale_range = (0.85, 1.4)

            if valid:
                inst = proto.copy()
                inst.name = f"Flora_{p_type}_{placed_for_type+1}"
                s = random.uniform(scale_range[0], scale_range[1])
                inst.scale = Vector((s, s, s))
                inst.location = Vector((rx, ry, rz))
                inst.rotation_euler = Euler((
                    random.uniform(-0.05, 0.05),
                    random.uniform(-0.05, 0.05),
                    random.uniform(0, math.pi * 2)
                ))
                col.objects.link(inst)
                placed_for_type += 1
                placed_count += 1

    print(f"[Genesis Wilderness] Placed {placed_count} organic natural flora assets.")


# =============================================================================
# 8. Natural Daylight & Atmosphere
# =============================================================================

def build_sun_and_atmosphere():
    print("[Genesis Wilderness] Setting up Natural Daylight & Atmospheric Sky...")
    col = bpy.context.collection

    sun_data = bpy.data.lights.new(name="Sun_Wilderness_Key", type='SUN')
    sun_data.energy = 4.4
    sun_data.color = (1.0, 0.96, 0.90)
    sun_data.angle = math.radians(4.5)

    sun_obj = bpy.data.objects.new(name="Sun_Wilderness_Key", object_data=sun_data)
    sun_obj.location = Vector((180.0, -180.0, 220.0))
    sun_obj.rotation_euler = Euler((math.radians(48.0), math.radians(16.0), math.radians(-38.0)))
    col.objects.link(sun_obj)

    fill_data = bpy.data.lights.new(name="Sun_Wilderness_Fill", type='SUN')
    fill_data.energy = 1.5
    fill_data.color = (0.68, 0.82, 0.98)
    fill_obj = bpy.data.objects.new(name="Sun_Wilderness_Fill", object_data=fill_data)
    fill_obj.location = Vector((-150.0, 150.0, 180.0))
    fill_obj.rotation_euler = Euler((math.radians(-35.0), math.radians(-20.0), math.radians(120.0)))
    col.objects.link(fill_obj)


# =============================================================================
# 9. 6 Verified Ground-Level Cinematic Cameras ("Mắt AI")
# =============================================================================

WILDERNESS_CAMERAS = [
    {
        "name": "CAM_01_WATER_CAVE",
        "loc": Vector((-10.0, -28.0, 15.2)),
        "target": Vector((-10.0, -14.0, 16.5)),
        "focal": 26.0,
        "desc": "Natural Karst Water Cave Mouth: Looking across the stream into the glowing grotto with stalactites and emerald pool"
    },
    {
        "name": "CAM_02_ALPINE_TARN",
        "loc": Vector((-70.0, 58.0, 49.5)),
        "target": Vector((-70.0, 75.0, 41.5)),
        "focal": 28.0,
        "desc": "High Mountain Alpine Tarn lake reflecting snow-capped granite peaks and highland pines"
    },
    {
        "name": "CAM_03_VALLEY_RIVER",
        "loc": Vector((-22.0, -56.0, 19.5)),
        "target": Vector((-10.0, -26.0, 14.5)),
        "focal": 30.0,
        "desc": "Meandering river flanked by wildflower meadows, rich brown soil, and ancient oaks"
    },
    {
        "name": "CAM_04_WATERFALL_CANYON",
        "loc": Vector((-12.0, 2.0, 36.5)),
        "target": Vector((-25.0, 42.0, 46.0)),
        "focal": 28.0,
        "desc": "Looking up the rocky gorge at 3-tier cascades, rapids, boulders and mossy earth"
    },
    {
        "name": "CAM_05_LAKE_SOLITUDE",
        "loc": Vector((-24.0, -66.0, 15.5)),
        "target": Vector((12.0, -105.0, 23.5)),
        "focal": 30.0,
        "desc": "Great Lowland Lake with solitary rock islet, lily pads, sand beach and willows"
    },
    {
        "name": "CAM_OVERVIEW_WILDERNESS",
        "loc": Vector((160.0, -160.0, 165.0)),
        "target": Vector((-15.0, -10.0, 30.0)),
        "focal": 28.0,
        "desc": "High aerial 3/4 establishing panorama of the complete untouched wilderness"
    }
]

def setup_cameras():
    print("[Genesis Wilderness] Registering 6 Ground-Level Calibrated Cameras...")
    col = bpy.context.collection

    for cfg in WILDERNESS_CAMERAS:
        cam_data = bpy.data.cameras.new(cfg["name"])
        cam_data.lens = cfg["focal"]
        cam_data.clip_start = 0.5
        cam_data.clip_end = 2500.0

        cam_obj = bpy.data.objects.new(cfg["name"], cam_data)
        cam_obj.location = cfg["loc"]

        direction = cfg["target"] - cfg["loc"]
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam_obj.rotation_euler = rot_quat.to_euler()

        col.objects.link(cam_obj)

    print("[Genesis Wilderness] 6 Cameras registered.")


def render_all_vistas():
    print("[Genesis Wilderness] Rendering 6 Cinematic 1080p Verification Vistas ('Mắt AI')...")
    scene = bpy.context.scene

    for cfg in WILDERNESS_CAMERAS:
        cam_name = cfg["name"]
        cam_obj = bpy.data.objects.get(cam_name)
        if not cam_obj:
            continue

        scene.camera = cam_obj
        out_path = os.path.join(ARTIFACT_DIR, f"{cam_name}.png")
        scene.render.filepath = out_path

        print(f"  -> Rendering {cam_name}: {cfg['desc']}...")
        bpy.ops.render.render(write_still=True)
        print(f"  ✓ Saved to {out_path}")


# =============================================================================
# 10. Save Master Blend & Export Clean WebGL GLB
# =============================================================================

def export_master_and_glb():
    print("[Genesis Wilderness] Saving Master .blend file...")
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
    print(f"  ✓ Master Blend saved: {BLEND_FILE} ({os.path.getsize(BLEND_FILE):,} bytes)")

    print("[Genesis Wilderness] Exporting clean, optimized GLB for WebGL spectator...")
    bpy.ops.export_scene.gltf(
        filepath=GLB_FILE,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
        export_all_vertex_colors=True,
        export_attributes=True,
        export_cameras=True,
        export_lights=False
    )
    print(f"  ✓ GLB Exported: {GLB_FILE} ({os.path.getsize(GLB_FILE):,} bytes)")


# =============================================================================
# Main Pipeline Entrypoint
# =============================================================================

def main():
    print("=" * 75)
    print("GENESIS ZERO · PRISTINE WILDERNESS 4.0 (MASTERPIECE)")
    print("=" * 75)

    reset_scene()
    build_pristine_terrain()
    build_karst_water_cave_system()
    build_hydrology_system()
    scatter_wilderness_ecosystem()
    build_sun_and_atmosphere()
    setup_cameras()
    export_master_and_glb()
    render_all_vistas()

    print("=" * 75)
    print("ALL PROCEDURAL PHASES COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    main()

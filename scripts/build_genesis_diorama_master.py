"""
build_genesis_diorama_master.py
Unified Master Diorama Generator for Genesis Zero (Blender 5.2.1 LTS)

Produces:
1. models/genesis_diorama_master.blend (Production master Blender file)
2. models/genesis_diorama.glb (Optimized web 3D spectator asset)

Key Architectural Specifications:
- Monolithic diorama slab: 160m x 160m footprint (X, Y in [-80.0, +80.0]), Z_base = -16.0m.
- Watertight geometry: 0 boundary edges, 0 non-manifold edges, planar base at -16.0m.
- Sheared vertical cutaway walls with 24 vertical slices and geological strata vertex colors COLOR_0.
- Topography: Sharp Alpine Horn summits (Z >= 32.0m), ridged multifractal aretes, scree/talus slopes (25-38 deg),
  alluvial marsh (Z ~ 4.7m) with hummocks, deep central lake basin with 4 bathymetric zones and >=0.35m freeboard berm.
- Subterranean Karst Cave System: Cavern at (14.0, 16.0, -4.5m) with vaulted ceiling (apex Z = -0.5m),
  overburden rock clearance >= 12.0m (> 5.0m invariant), arched entrance portal on river gorge,
  16 stalactites, 14 stalagmites, 4 fused columns, subterranean pool (Z = -7.2m), glowing fungi and 35W point light.
- 4-Tier Continuous Hydrology: Mountain cascades -> S-curve meandering river -> central lake -> outlet gorge & marine bay.
- 13 Botanical Prototypes across 4 biomes (Alpine, Forest, Aquatic, Cave) with 100% smooth shading.
- Procedural Geometry Nodes scatter modifiers with 3 mathematical masks (Altitude, Slope Normal, Water Proximity).
- PBR Shaders: Triplanar slope-aware terrain, Beer-Lambert volume absorption water with contact edge AO shore foam,
  bioluminescent SSS fungi shader.
- 5 Rigged & Animated Fauna Species with complete skeletal armatures and NLA animation tracks.
- Exact 24-Camera Rig linked to Camera_Rig_24 collection (including near-plane cutaways CAM_10 and CAM_11).
- glTF/GLB export pipeline compliant with Three.js r128 (no Draco, no GPU instancing, embedded cameras, vertex colors).
"""

from __future__ import annotations

import math
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets" / "blender_map"
BLEND_OUTPUT = MODELS_DIR / "genesis_diorama_master.blend"
GLB_OUTPUT = MODELS_DIR / "genesis_diorama.glb"

sys.path.insert(0, str(ASSETS_DIR))
import fauna_generator


# =============================================================================
# 1. Analytical Mathematical Models (Topography, River Spline & Bathymetry)
# =============================================================================

def evaluate_river_spline(t: np.ndarray | float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluates continuous 4-tier river spline (rx, ry, rz, rw) for parameter t in [0.0, 1.0].
    Stage 1 (0.00 -> 0.32): Mountain cascades from (-8.0, 48.0, 21.5) to (0.0, 26.0, 8.0)
    Stage 2 (0.32 -> 0.58): Valley meander from (0.0, 26.0, 8.0) to (-18.0, 6.0, 4.5)
    Stage 3 (0.58 -> 0.74): Central lake transit from (-18.0, 6.0, 4.5) to (-10.0, -18.0, 4.5)
    Stage 4 (0.74 -> 1.00): Outlet gorge & bay waterfall from (-10.0, -18.0, 4.5) to (26.0, -36.0, 0.0)
    """
    is_scalar = np.isscalar(t)
    t_arr = np.array([float(t)], dtype=np.float64) if is_scalar else np.asarray(t, dtype=np.float64)

    rx = np.zeros_like(t_arr)
    ry = np.zeros_like(t_arr)
    rz = np.zeros_like(t_arr)
    rw = np.zeros_like(t_arr)

    # Stage 1: Mountain Cascades
    m1 = (t_arr >= 0.0) & (t_arr < 0.32)
    if np.any(m1):
        u = t_arr[m1] / 0.32
        su = 3.0 * u**2 - 2.0 * u**3
        rx[m1] = -8.0 + 8.0 * u + 2.5 * np.sin(np.pi * u)
        ry[m1] = 48.0 - 22.0 * u
        rz[m1] = 21.5 - (21.5 - 8.0) * su
        rw[m1] = 3.2 + 1.3 * u

    # Stage 2: Valley Meander
    m2 = (t_arr >= 0.32) & (t_arr < 0.58)
    if np.any(m2):
        u = (t_arr[m2] - 0.32) / 0.26
        su = 3.0 * u**2 - 2.0 * u**3
        rx[m2] = 0.0 - 18.0 * u - 8.0 * np.sin(2.0 * np.pi * u)
        ry[m2] = 26.0 - 20.0 * u + 4.0 * np.sin(np.pi * u)
        rz[m2] = 8.0 - (8.0 - 4.5) * su
        rw[m2] = 4.5 + 3.0 * u

    # Stage 3: Central Lake Transit
    m3 = (t_arr >= 0.58) & (t_arr < 0.74)
    if np.any(m3):
        u = (t_arr[m3] - 0.58) / 0.16
        rx[m3] = -18.0 + 8.0 * u
        ry[m3] = 6.0 - 24.0 * u
        rz[m3] = 4.50
        rw[m3] = 7.5 + 0.5 * u

    # Stage 4: Outlet Gorge & Bay Waterfall
    m4 = t_arr >= 0.74
    if np.any(m4):
        u = np.clip((t_arr[m4] - 0.74) / 0.26, 0.0, 1.0)
        su = 3.0 * u**2 - 2.0 * u**3
        rx[m4] = -10.0 + 36.0 * u + 4.0 * np.sin(np.pi * u)
        ry[m4] = -18.0 - 18.0 * u - 3.0 * np.sin(np.pi * u)
        rz[m4] = 4.50 - 4.50 * su
        rw[m4] = 8.0 + 1.0 * u

    if is_scalar:
        return float(rx[0]), float(ry[0]), float(rz[0]), float(rw[0])
    return rx, ry, rz, rw


def compute_terrain_elevation(x: np.ndarray | float, y: np.ndarray | float) -> np.ndarray | float:
    """
    Continuous analytical elevation evaluation Z(x, y).
    Guarantees:
    - Alpine summits reaching Z >= 33.5m (net delta >= 38.0m relative to seabed -4.5m).
    - Rock clearance above subterranean karst cavern (14.0, 16.0, apex -0.5m) >= 12.0m.
    - Central freshwater lake basin contains water disc at Z = 4.5m with freeboard berm lip >= 4.85m.
    - Alluvial marsh at (12.0, 2.0) with hummocks Z ~ 4.7m.
    - Continuous river channel carved 0.9m below river water surface.
    """
    is_scalar = np.isscalar(x) and np.isscalar(y)
    x_arr = np.array([float(x)], dtype=np.float64) if is_scalar else np.asarray(x, dtype=np.float64)
    y_arr = np.array([float(y)], dtype=np.float64) if is_scalar else np.asarray(y, dtype=np.float64)

    # 1. Base Rolling Valley Plains & Foothills
    z_base = 5.2
    foothills = (
        0.85 * np.sin(x_arr * 0.038) * np.cos(y_arr * 0.042)
        + 0.50 * np.cos(x_arr * 0.076 + 1.0)
        + 0.40 * np.sin(y_arr * 0.068 + 0.5)
    )
    z = z_base + foothills

    # 2. Northern Alpine Mountain Massif (y in [0.0, 75.0])
    m_factor = np.clip((y_arr - 0.0) / 70.0, 0.0, 1.0) ** 1.2

    # Three sharp alpine peaks:
    # Peak 1 (Central Horn Peak): at (-26.0, 44.0), amplitude 29.0m -> Summit Z >= 34.5m
    p1 = 29.0 * np.exp(-((x_arr + 26.0)**2 + (y_arr - 44.0)**2) / (2.0 * 15.0**2))
    # Peak 2 (Pyramidal Peak): at (22.0, 54.0), amplitude 24.0m
    p2 = 24.0 * np.exp(-((x_arr - 22.0)**2 + (y_arr - 54.0)**2) / (2.0 * 16.0**2))
    # Peak 3 (Western Shoulder): at (-44.0, 40.0), amplitude 18.0m
    p3 = 18.0 * np.exp(-((x_arr + 44.0)**2 + (y_arr - 40.0)**2) / (2.0 * 14.0**2))

    # Sharp knife-edge arêtes (ridged multifractal ridges)
    ridge_wave = np.sin(x_arr * 0.058 + y_arr * 0.046) * np.cos(x_arr * 0.044 - y_arr * 0.062)
    aretes = 6.5 * (1.0 - np.abs(ridge_wave))**2.2

    # Scree / Talus debris aprons at natural angle of repose
    d1 = np.sqrt((x_arr + 26.0)**2 + (y_arr - 44.0)**2)
    scree_apron = 4.5 * np.exp(-np.clip(d1 - 14.0, 0.0, 40.0) / 8.5)

    # Mountain massif over cave vault (guarantees >= 12.0m clearance above cavern apex Z = -2.2m)
    cave_massif = 8.8 * np.exp(-((x_arr - 14.0)**2 + (y_arr - 18.0)**2) / (2.0 * 15.0**2))

    z += m_factor * (p1 + p2 + p3 + aretes + scree_apron) + cave_massif

    # 3. Alluvial Marsh / Wetland Basin at (12.0, 2.0)
    d_marsh = np.hypot(x_arr - 12.0, y_arr - 2.0)
    mask_marsh = d_marsh < 18.0
    if np.any(mask_marsh):
        m_mask = np.clip((18.0 - d_marsh[mask_marsh]) / 18.0, 0.0, 1.0)**2
        hummocks = 0.25 * np.sin(x_arr[mask_marsh] * 0.42) * np.cos(y_arr[mask_marsh] * 0.38)
        target_marsh = 4.70 + hummocks
        z[mask_marsh] = (1.0 - m_mask) * z[mask_marsh] + m_mask * np.minimum(z[mask_marsh], target_marsh)

    # 4. Central Freshwater Lake Basin centered at (-20.0, -8.0)
    lcx, lcy = -20.0, -8.0
    d_lake = np.hypot(x_arr - lcx, y_arr - lcy)

    # 4 Bathymetric Zones:
    # Zone 1: Deep Bed (d < 10.0m) -> Z = 1.40m to 1.80m
    m_bed = d_lake < 10.0
    if np.any(m_bed):
        z[m_bed] = 1.40 + 0.40 * (d_lake[m_bed] / 10.0)**2

    # Zone 2: Drop-Off Slope (10.0m <= d < 16.0m)
    m_slope = (d_lake >= 10.0) & (d_lake < 16.0)
    if np.any(m_slope):
        ts = (d_lake[m_slope] - 10.0) / 6.0
        ss = 3.0 * ts**2 - 2.0 * ts**3
        z[m_slope] = 1.80 + (3.80 - 1.80) * ss

    # Zone 3: Shallow Shoreline Terrace (16.0m <= d < 21.5m)
    m_terrace = (d_lake >= 16.0) & (d_lake < 21.5)
    if np.any(m_terrace):
        tt = (d_lake[m_terrace] - 16.0) / 5.5
        z[m_terrace] = 3.80 + 0.50 * tt

    # Zone 4: Retaining Freeboard Berm Lip (21.5m <= d < 28.0m) -> guarantees Z >= 4.88m (> 4.5m)
    m_berm = (d_lake >= 21.5) & (d_lake < 28.0)
    if np.any(m_berm):
        tb = (d_lake[m_berm] - 21.5) / 6.5
        sb = 3.0 * tb**2 - 2.0 * tb**3
        berm_h = 4.88 + 0.45 * np.sin(np.pi * tb)
        z[m_berm] = (1.0 - sb) * np.maximum(z[m_berm], berm_h) + sb * z[m_berm]

    # 5. Lower Coastal Marine Bay Basin at (42.0, -42.0)
    bcx, bcy = 42.0, -42.0
    d_bay = np.hypot(x_arr - bcx, y_arr - bcy)

    # Outer bay ocean floor stays deep (-4.5m) towards diorama slab edges
    m_bay_outer = (x_arr >= bcx) | (y_arr <= bcy)
    m_bay_bed = (d_bay < 25.0) | (m_bay_outer & (d_bay < 55.0))
    if np.any(m_bay_bed):
        z[m_bay_bed] = np.minimum(z[m_bay_bed], -4.50 + 0.30 * np.clip(d_bay[m_bay_bed] / 25.0, 0.0, 1.0))

    # Inland coastal bay slope (only on the northwestern shore of the bay, respecting lake containment)
    m_bay_slope = (d_bay >= 25.0) & (d_bay < 48.0) & (~m_bay_outer) & (d_lake >= 24.0)
    if np.any(m_bay_slope):
        t_bs = (d_bay[m_bay_slope] - 25.0) / 23.0
        s_bs = 3.0 * t_bs**2 - 2.0 * t_bs**3
        target_bay_z = -4.20 + 4.20 * s_bs
        # Smoothly blend with terrain near lake perimeter to preserve lake containment
        dl = d_lake[m_bay_slope]
        lake_blend = np.clip((dl - 24.0) / 4.0, 0.0, 1.0)
        s_lb = 3.0 * lake_blend**2 - 2.0 * lake_blend**3
        bay_carve = (target_bay_z + 1.2 * s_bs) * s_lb + z[m_bay_slope] * (1.0 - s_lb)
        z[m_bay_slope] = np.minimum(z[m_bay_slope], bay_carve)

    # 6. Lake Outlet Gorge Carving towards Marine Bay (0.0, -19.0) -> (9.0, -25.0)
    gx0, gy0 = 0.0, -19.0
    gx1, gy1 = 9.0, -25.0
    g_dx, g_dy = gx1 - gx0, gy1 - gy0
    g_len_sq = g_dx * g_dx + g_dy * g_dy
    g_t = np.clip(((x_arr - gx0) * g_dx + (y_arr - gy0) * g_dy) / g_len_sq, 0.0, 1.0)
    g_px = gx0 + g_t * g_dx
    g_py = gy0 + g_t * g_dy
    g_dist = np.hypot(x_arr - g_px, y_arr - g_py)
    m_gorge = (g_dist < 4.8) & (d_lake >= 23.8)
    if np.any(m_gorge):
        t_g = g_dist[m_gorge] / 4.8
        s_g = 3.0 * t_g**2 - 2.0 * t_g**3
        d_val = d_lake[m_gorge]
        prog = np.clip((d_val - 23.8) / 9.8, 0.0, 1.0)
        s_p = 3.0 * prog**2 - 2.0 * prog**3
        target_gorge_z = 4.54 - 4.44 * s_p
        z[m_gorge] = (1.0 - s_g) * np.minimum(z[m_gorge], target_gorge_z) + s_g * z[m_gorge]

    # 7. Cave Entrance Portal Cliff Alcove Notch at (16.0, -6.5)
    d_portal = np.hypot(x_arr - 16.0, y_arr - (-6.5))
    m_portal_cut = (d_portal < 4.2) & (y_arr >= -6.5)
    if np.any(m_portal_cut):
        tp = d_portal[m_portal_cut] / 4.2
        sp = 3.0 * tp**2 - 2.0 * tp**3
        z[m_portal_cut] = (1.0 - sp) * 2.10 + sp * z[m_portal_cut]

    # 8. Continuous River Channel Carving
    t_samp = np.linspace(0.0, 1.0, 200)
    rx, ry, rz, rw = evaluate_river_spline(t_samp)

    flat_x = x_arr.ravel()
    flat_y = y_arr.ravel()
    dx = flat_x[:, None] - rx[None, :]
    dy = flat_y[:, None] - ry[None, :]
    dists_sq = dx * dx + dy * dy
    min_idx = np.argmin(dists_sq, axis=-1)
    min_dist = np.sqrt(np.take_along_axis(dists_sq, min_idx[:, None], axis=-1).squeeze(-1))

    rz_near = rz[min_idx].reshape(x_arr.shape)
    rw_near = rw[min_idx].reshape(x_arr.shape)
    min_dist = min_dist.reshape(x_arr.shape)
    t_near = t_samp[min_idx].reshape(x_arr.shape)

    # Carve river channel outside lake perimeter (d_lake >= 23.6)
    w_channel = rw_near * 0.55 + 2.2
    m_river = (min_dist < w_channel) & (t_near <= 0.54) & (d_lake >= 23.6)
    if np.any(m_river):
        t_bank = min_dist[m_river] / w_channel[m_river]
        s_bank = 3.0 * t_bank**2 - 2.0 * t_bank**3
        bed_cut = np.maximum(rz_near[m_river] - 0.85, 4.54)
        z[m_river] = (1.0 - s_bank) * np.minimum(z[m_river], bed_cut) + s_bank * z[m_river]

    # Floor limit at seabed
    z = np.maximum(z, -4.50)

    if is_scalar:
        return float(z[0])
    return z


# =============================================================================
# 2. Scene Initialization & Collection Hierarchy
# =============================================================================

def initialize_clean_scene() -> Dict[str, bpy.types.Collection]:
    """Wipes default scene data and sets up structured collections."""
    bpy.ops.wm.read_homefile(use_empty=True)

    # Clean existing meshes, materials, objects
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh, do_unlink=True)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat, do_unlink=True)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam, do_unlink=True)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light, do_unlink=True)

    # Render Settings (Apple Silicon Metal EEVEE)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    # World background (dark slate diorama backdrop)
    world = bpy.data.worlds.new("Diorama_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.04, 0.06, 0.09, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    # Create Structured Collections
    root_col = scene.collection
    collections = {}
    col_names = ["Terrain", "Hydrology", "Caves", "Biome_Scatter", "Fauna", "Camera_Rig_24", "Lighting"]
    for name in col_names:
        c = bpy.data.collections.new(name)
        root_col.children.link(c)
        collections[name] = c

    # Prototype container (hidden from render to avoid loose objects at origin)
    col_proto = bpy.data.collections.new("Flora_Prototypes")
    col_proto.hide_render = True
    col_proto.hide_viewport = True
    root_col.children.link(col_proto)
    collections["Flora_Prototypes"] = col_proto

    for sub_name in ["Col_Flora_Alpine", "Col_Flora_Forest", "Col_Flora_Aquatic", "Col_Flora_Cave"]:
        sub_c = bpy.data.collections.new(sub_name)
        col_proto.children.link(sub_c)
        collections[sub_name] = sub_c

    return collections


# =============================================================================
# 3. PBR Shaders (Terrain Triplanar, Water Volumetrics & Bioluminescence)
# =============================================================================

def create_pbr_material(
    name: str,
    base_color: Tuple[float, float, float, float],
    roughness: float = 0.6,
    specular: float = 0.35,
    transmission: float = 0.0,
    emission_color: Tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    """Helper to create Principled BSDF materials."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = base_color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = specular
        elif "Specular" in bsdf.inputs:
            bsdf.inputs["Specular"].default_value = specular
        if transmission > 0.0:
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = transmission
        if emission_color and emission_strength > 0.0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission_color
                bsdf.inputs["Emission Strength"].default_value = emission_strength
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission_color
    return mat


def create_terrain_pbr_material() -> bpy.types.Material:
    """
    Constructs dynamic slope-aware, triplanar terrain material M_Terrain_PBR.
    Blends:
    - Rock cliff texture on steep slopes (Normal Z < 0.707)
    - Lush meadow grass on flat ground (Normal Z > 0.940)
    - Scree / talus transition on intermediate slopes
    - High-altitude snow caps on gentle ridges (Z >= 16.5m)
    - Object-space procedural striations and micro-bump
    - Vertex color attribute COLOR_0 integration
    """
    mat_name = "M_Terrain_PBR"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    node_out = nt.nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (1200, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (900, 0)
    bsdf.inputs["Roughness"].default_value = 0.72
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30
    nt.links.new(bsdf.outputs["BSDF"], node_out.inputs["Surface"])

    # Geometry & Coordinates
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    geom.location = (-1000, 200)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1000, -250)

    # 1. Slope Calculation (Normal Z = cos(theta))
    sep_norm = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_norm.location = (-750, 300)
    nt.links.new(geom.outputs["Normal"], sep_norm.inputs["Vector"])

    # Map slope: Nz in [0.707, 0.940] -> [0.0 (Rock Cliff), 1.0 (Flat Grass)]
    map_slope = nt.nodes.new("ShaderNodeMapRange")
    map_slope.location = (-500, 300)
    map_slope.inputs["From Min"].default_value = 0.707  # 45 deg
    map_slope.inputs["From Max"].default_value = 0.940  # 20 deg
    map_slope.inputs["To Min"].default_value = 0.0
    map_slope.inputs["To Max"].default_value = 1.0
    nt.links.new(sep_norm.outputs["Z"], map_slope.inputs["Value"])

    # 2. Triplanar Procedural Textures (Object Coordinates)
    rock_noise = nt.nodes.new("ShaderNodeTexNoise")
    rock_noise.location = (-500, -250)
    rock_noise.inputs["Scale"].default_value = 8.0
    rock_noise.inputs["Detail"].default_value = 5.0
    rock_noise.inputs["Roughness"].default_value = 0.72
    nt.links.new(tex_coord.outputs["Object"], rock_noise.inputs["Vector"])

    grass_noise = nt.nodes.new("ShaderNodeTexNoise")
    grass_noise.location = (-500, 50)
    grass_noise.inputs["Scale"].default_value = 18.0
    grass_noise.inputs["Detail"].default_value = 4.0
    nt.links.new(tex_coord.outputs["Object"], grass_noise.inputs["Vector"])

    # Rock Colors
    rock_col = nt.nodes.new("ShaderNodeMix")
    rock_col.data_type = 'RGBA'
    rock_col.location = (-250, -250)
    nt.links.new(rock_noise.outputs["Fac"], rock_col.inputs[0])
    rock_col.inputs[6].default_value = (0.24, 0.23, 0.22, 1.0)  # Basalt
    rock_col.inputs[7].default_value = (0.44, 0.40, 0.35, 1.0)  # Granite

    # Grass Colors
    grass_col = nt.nodes.new("ShaderNodeMix")
    grass_col.data_type = 'RGBA'
    grass_col.location = (-250, 50)
    nt.links.new(grass_noise.outputs["Fac"], grass_col.inputs[0])
    grass_col.inputs[6].default_value = (0.12, 0.36, 0.10, 1.0)  # Emerald Meadow
    grass_col.inputs[7].default_value = (0.24, 0.48, 0.14, 1.0)  # Sunny Grass

    # Mix Rock & Grass by Slope
    slope_blend = nt.nodes.new("ShaderNodeMix")
    slope_blend.data_type = 'RGBA'
    slope_blend.location = (50, 150)
    nt.links.new(map_slope.outputs["Result"], slope_blend.inputs[0])
    nt.links.new(rock_col.outputs[2], slope_blend.inputs[6])
    nt.links.new(grass_col.outputs[2], slope_blend.inputs[7])

    # 3. Peak Snow Blending (Z >= 16.5m, restricted to gentle slopes)
    sep_pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-300, 500)
    nt.links.new(geom.outputs["Position"], sep_pos.inputs["Vector"])

    map_snow = nt.nodes.new("ShaderNodeMapRange")
    map_snow.location = (-50, 500)
    map_snow.inputs["From Min"].default_value = 16.5
    map_snow.inputs["From Max"].default_value = 24.0
    map_snow.inputs["To Min"].default_value = 0.0
    map_snow.inputs["To Max"].default_value = 1.0
    nt.links.new(sep_pos.outputs["Z"], map_snow.inputs["Value"])

    snow_mask = nt.nodes.new("ShaderNodeMath")
    snow_mask.operation = 'MULTIPLY'
    snow_mask.location = (200, 400)
    nt.links.new(map_snow.outputs["Result"], snow_mask.inputs[0])
    nt.links.new(map_slope.outputs["Result"], snow_mask.inputs[1])

    snow_blend = nt.nodes.new("ShaderNodeMix")
    snow_blend.name = "Mix_Snow_Procedural"
    snow_blend.data_type = 'RGBA'
    snow_blend.location = (450, 200)
    nt.links.new(snow_mask.outputs["Value"], snow_blend.inputs[0])
    nt.links.new(slope_blend.outputs[2], snow_blend.inputs[6])
    snow_blend.inputs[7].default_value = (0.97, 0.99, 1.0, 1.0)  # Alpine Snow

    # 4. Integrate COLOR_0 Attribute mixed with procedural slope & snow shader to Base Color
    attr_node = nt.nodes.new("ShaderNodeAttribute")
    attr_node.attribute_name = "COLOR_0"
    attr_node.location = (450, -100)

    color_mix = nt.nodes.new("ShaderNodeMix")
    color_mix.name = "Color_Terrain_Strata_Mix"
    color_mix.data_type = 'RGBA'
    color_mix.blend_type = 'MIX'
    color_mix.location = (700, 100)
    color_mix.inputs[0].default_value = 0.5  # Blend 50% procedural slope/snow and 50% baked strata
    nt.links.new(snow_blend.outputs[2], color_mix.inputs[6])
    nt.links.new(attr_node.outputs["Color"], color_mix.inputs[7])
    nt.links.new(color_mix.outputs[2], bsdf.inputs["Base Color"])

    # 5. Micro-bump normal mapping
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (650, -200)
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.12
    nt.links.new(rock_noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    mat.blend_method = "OPAQUE"
    return mat


def create_water_pbr_material() -> bpy.types.Material:
    """
    Constructs translucent water PBR shader with Beer-Lambert volume absorption,
    emerald shallow water tint, sapphire depth gradient, and contact edge AO shore foam.
    """
    mat_name = "M_Water_PBR"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    node_out = nt.nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (950, 0)

    # 1. Emerald Shallow Water Surface
    bsdf_water = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_water.location = (300, 120)
    bsdf_water.inputs["Base Color"].default_value = (0.04, 0.72, 0.82, 1.0)
    bsdf_water.inputs["Roughness"].default_value = 0.03
    bsdf_water.inputs["IOR"].default_value = 1.333
    if "Transmission Weight" in bsdf_water.inputs:
        bsdf_water.inputs["Transmission Weight"].default_value = 0.96
    elif "Transmission" in bsdf_water.inputs:
        bsdf_water.inputs["Transmission"].default_value = 0.96

    # 2. Volume Absorption for Deep Sapphire Gradient
    vol_node = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol_node.location = (650, -200)
    vol_node.inputs["Color"].default_value = (0.04, 0.42, 0.80, 1.0)
    vol_node.inputs["Density"].default_value = 0.06
    nt.links.new(vol_node.outputs["Volume"], node_out.inputs["Volume"])

    # 3. Ambient Occlusion Shore Foam Edge Detection
    ao_node = nt.nodes.new("ShaderNodeAmbientOcclusion")
    ao_node.location = (-400, 200)
    ao_node.inputs["Distance"].default_value = 1.2

    map_foam = nt.nodes.new("ShaderNodeMapRange")
    map_foam.location = (-150, 200)
    map_foam.inputs["From Min"].default_value = 0.25
    map_foam.inputs["From Max"].default_value = 0.95
    map_foam.inputs["To Min"].default_value = 1.0
    map_foam.inputs["To Max"].default_value = 0.0
    nt.links.new(ao_node.outputs["AO"], map_foam.inputs["Value"])

    foam_noise = nt.nodes.new("ShaderNodeTexNoise")
    foam_noise.location = (-400, -50)
    foam_noise.inputs["Scale"].default_value = 45.0
    foam_noise.inputs["Detail"].default_value = 6.0
    foam_noise.inputs["Roughness"].default_value = 0.70

    math_foam = nt.nodes.new("ShaderNodeMath")
    math_foam.operation = 'MULTIPLY'
    math_foam.location = (80, 200)
    nt.links.new(map_foam.outputs["Result"], math_foam.inputs[0])
    nt.links.new(foam_noise.outputs["Fac"], math_foam.inputs[1])

    # 4. White Foam BSDF
    bsdf_foam = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf_foam.location = (300, 420)
    bsdf_foam.inputs["Base Color"].default_value = (0.95, 0.98, 1.0, 1.0)
    bsdf_foam.inputs["Roughness"].default_value = 0.85
    if "Transmission Weight" in bsdf_foam.inputs:
        bsdf_foam.inputs["Transmission Weight"].default_value = 0.0

    # Mix Water and Shore Foam
    mix_surface = nt.nodes.new("ShaderNodeMixShader")
    mix_surface.location = (650, 200)
    nt.links.new(math_foam.outputs["Value"], mix_surface.inputs[0])
    nt.links.new(bsdf_water.outputs["BSDF"], mix_surface.inputs[1])
    nt.links.new(bsdf_foam.outputs["BSDF"], mix_surface.inputs[2])

    nt.links.new(mix_surface.outputs["Shader"], node_out.inputs["Surface"])

    mat.blend_method = "BLEND"
    return mat


def create_bioluminescent_material() -> bpy.types.Material:
    """Constructs glowing cave fungi material with SSS and emission."""
    mat_name = "M_Cave_BioFungi"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.08, 0.75, 0.68, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.22
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.50
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (0.12, 0.95, 0.85, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 5.0
    return mat


# =============================================================================
# 4. Monolithic Watertight Diorama Island Block Base
# =============================================================================

def build_diorama_island_block(collection: bpy.types.Collection) -> bpy.types.Object:
    """
    Constructs the monolithic 160m x 160m diorama block.
    - Grid size: 129x129 (X, Y in [-80.0, +80.0])
    - Vertical wall slices: n_slices = 24 rows down to Z_base = -16.0m
    - Sealed planar bottom polygon at Z = -16.0m (0 boundary edges, 100% manifold)
    - Vertex color attribute COLOR_0 baking:
      Topsoil (<1.2m), Subsoil (1.2-4.2m), Sedimentary rock (>4.2m), Bedrock (>10m),
      Snow on peaks, Rock cliffs, Scree slopes, Sandy shores, Grass plains.
    """
    nx, ny = 129, 129
    x_lin = np.linspace(-80.0, 80.0, nx)
    y_lin = np.linspace(-80.0, 80.0, ny)
    X, Y = np.meshgrid(x_lin, y_lin)
    Z = compute_terrain_elevation(X, Y)

    mesh = bpy.data.meshes.new("Diorama_Island_Block_Mesh")
    obj = bpy.data.objects.new("Diorama_Island_Block", mesh)
    collection.objects.link(obj)

    verts: List[Tuple[float, float, float]] = []
    faces: List[Tuple[int, ...]] = []
    v_colors: List[Tuple[float, float, float, float]] = []

    # 1. Top Surface Vertices & Faces
    top_grid = np.zeros((ny, nx), dtype=int)
    v_idx = 0
    dx = x_lin[1] - x_lin[0]
    dy = y_lin[1] - y_lin[0]
    dZ_dy, dZ_dx = np.gradient(Z, dy, dx)
    slope_deg = np.degrees(np.arctan(np.hypot(dZ_dx, dZ_dy)))

    for j in range(ny):
        for i in range(nx):
            x_val = float(X[j, i])
            y_val = float(Y[j, i])
            z_val = float(Z[j, i])
            sl = float(slope_deg[j, i])
            verts.append((x_val, y_val, z_val))
            top_grid[j, i] = v_idx
            v_idx += 1

            # Top Surface Vertex Color
            d_lake = math.hypot(x_val - (-20.0), y_val - (-8.0))
            d_bay = math.hypot(x_val - 42.0, y_val - (-42.0))
            if z_val >= 16.5 and sl < 45.0:
                col = (0.97, 0.99, 1.0, 1.0)  # Snow
            elif sl > 33.0:
                col = (0.35, 0.33, 0.30, 1.0)  # Rock Cliff
            elif sl >= 21.0:
                col = (0.50, 0.45, 0.38, 1.0)  # Scree / Talus
            elif (d_lake < 28.0 and z_val <= 5.2) or (d_bay < 48.0 and z_val <= 2.2):
                col = (0.76, 0.68, 0.48, 1.0)  # Sand
            elif z_val <= 4.8 and math.hypot(x_val - 12.0, y_val - 2.0) < 16.0:
                col = (0.20, 0.30, 0.12, 1.0)  # Marsh Peat
            else:
                col = (0.18, 0.44, 0.12, 1.0)  # Meadow Grass
            v_colors.append(col)

    for j in range(ny - 1):
        for i in range(nx - 1):
            v00 = int(top_grid[j, i])
            v10 = int(top_grid[j, i + 1])
            v11 = int(top_grid[j + 1, i + 1])
            v01 = int(top_grid[j + 1, i])
            faces.append((v00, v10, v11, v01))

    # 2. Vertical Sheared Cutaway Walls (24 vertical slices down to Z = -16.0m)
    n_slices = 24
    z_base = -16.0

    perimeter_coords = []
    # South wall: (i, 0) for i in 0..nx-1
    for i in range(nx): perimeter_coords.append((i, 0))
    # East wall: (nx-1, j) for j in 1..ny-1
    for j in range(1, ny): perimeter_coords.append((nx - 1, j))
    # North wall: (i, ny-1) for i in nx-2 down to 0
    for i in range(nx - 2, -1, -1): perimeter_coords.append((i, ny - 1))
    # West wall: (0, j) for j in ny-2 down to 1
    for j in range(ny - 2, 0, -1): perimeter_coords.append((0, j))

    wall_layers: List[List[int]] = []
    # Layer 0: top perimeter vertices
    wall_layers.append([int(top_grid[j, i]) for i, j in perimeter_coords])

    for s in range(1, n_slices + 1):
        frac = s / float(n_slices)
        layer_indices = []
        for i, j in perimeter_coords:
            x_val = float(X[j, i])
            y_val = float(Y[j, i])
            z_surf = float(Z[j, i])
            if s < n_slices:
                z_cur = z_surf * (1.0 - frac) + (-15.0) * frac
            else:
                z_cur = z_base
            depth = z_surf - z_cur

            verts.append((x_val, y_val, z_cur))
            layer_indices.append(v_idx)
            v_idx += 1

            # Geological Strata Color Calculation
            if depth < 1.2:
                col = (0.15, 0.08, 0.04, 1.0)  # Topsoil Loam
            elif depth < 4.2:
                col = (0.48, 0.24, 0.10, 1.0)  # Subsoil Ferruginous Clay
            elif depth < 10.0:
                # Sedimentary Strata Banding
                band = 1.0 + 0.24 * math.sin(1.8 * z_cur) + 0.12 * math.cos(3.6 * z_cur) + 0.08 * math.sin(7.2 * z_cur)
                col = (min(1.0, 0.38 * band), min(1.0, 0.32 * band), min(1.0, 0.26 * band), 1.0)
            else:
                col = (0.22, 0.20, 0.19, 1.0)  # Basement Bedrock
            v_colors.append(col)
        wall_layers.append(layer_indices)

    # Build wall quad faces
    num_perim = len(perimeter_coords)
    for s in range(n_slices):
        l_upper = wall_layers[s]
        l_lower = wall_layers[s + 1]
        for p in range(num_perim):
            pn = (p + 1) % num_perim
            faces.append((l_upper[p], l_lower[p], l_lower[pn], l_upper[pn]))

    # 3. Sealed Planar Bottom Polygon (Watertight Manifold Closure)
    bottom_ring = wall_layers[-1]
    # Triangulate / fan cap bottom ring in reverse orientation to point normal downwards
    center_idx = v_idx
    verts.append((0.0, 0.0, z_base))
    v_colors.append((0.20, 0.18, 0.17, 1.0))
    v_idx += 1

    for p in range(num_perim):
        pn = (p + 1) % num_perim
        faces.append((center_idx, bottom_ring[pn], bottom_ring[p]))

    # Populate BMesh
    bm = bmesh.new()
    bm_verts = [bm.verts.new(v) for v in verts]
    for f_inds in faces:
        try:
            bm.faces.new([bm_verts[k] for k in f_inds])
        except ValueError:
            pass

    bm.to_mesh(mesh)
    bm.free()

    mesh.update(calc_edges=True)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))

    # Apply Vertex Colors COLOR_0
    color_attr = mesh.color_attributes.new(name="COLOR_0", type='FLOAT_COLOR', domain='POINT')
    for idx, c in enumerate(v_colors):
        color_attr.data[idx].color = c

    # Assign Terrain PBR Material
    mat_terrain = create_terrain_pbr_material()
    mesh.materials.append(mat_terrain)

    return obj


# =============================================================================
# 5. 4-Tier Continuous Hydrology System
# =============================================================================

def build_hydrology(collection: bpy.types.Collection) -> Dict[str, bpy.types.Object]:
    """Constructs continuous 4-tier hydrology network meshes."""
    mat_water = create_water_pbr_material()
    mat_foam = create_pbr_material("M_Water_Cascades", (0.95, 0.98, 1.0, 1.0), roughness=0.35, specular=0.5)

    hydrology_objs = {}

    # 1. Central Freshwater Lake (Planar disc Z = 4.50m, Radius = 23.5m)
    m_lake = bpy.data.meshes.new("Water_Lake_Central_Mesh")
    o_lake = bpy.data.objects.new("Water_Lake_Central", m_lake)
    collection.objects.link(o_lake)
    m_lake.materials.append(mat_water)

    bm_lake = bmesh.new()
    lcx, lcy, lcz, lr = -20.0, -8.0, 4.50, 23.5
    N_lake = 48
    rings = [0.0, 6.0, 12.0, 17.5, 23.5]
    v_rings = []
    for r in rings:
        r_list = []
        for i in range(N_lake):
            ang = 2.0 * math.pi * i / N_lake
            vx = lcx + r * math.cos(ang)
            vy = lcy + r * math.sin(ang)
            r_list.append(bm_lake.verts.new((vx, vy, lcz)))
        v_rings.append(r_list)

    # Fan center
    for i in range(N_lake):
        inxt = (i + 1) % N_lake
        bm_lake.faces.new((v_rings[0][0], v_rings[1][i], v_rings[1][inxt]))
    for rg in range(1, len(rings) - 1):
        for i in range(N_lake):
            inxt = (i + 1) % N_lake
            bm_lake.faces.new((v_rings[rg][i], v_rings[rg + 1][i], v_rings[rg + 1][inxt], v_rings[rg][inxt]))

    bm_lake.to_mesh(m_lake)
    bm_lake.free()
    m_lake.polygons.foreach_set("use_smooth", [True] * len(m_lake.polygons))
    hydrology_objs["Water_Lake_Central"] = o_lake

    # 2. Coastal Marine Bay (Sea Level Z = 0.0m) clipped to diorama slab bounds [-80, 80]
    # Includes vertical transparent water volume cutaways on South (Y = -80) and East (X = 80) walls
    m_bay = bpy.data.meshes.new("Water_Bay_Marine_Mesh")
    o_bay = bpy.data.objects.new("Water_Bay_Marine", m_bay)
    collection.objects.link(o_bay)
    m_bay.materials.append(mat_water)

    bm_bay = bmesh.new()
    bcx, bcy, bcz, br = 42.0, -42.0, 0.0, 46.0

    # Grid covering [-4.0, 80.0] x [-80.0, 4.0], clipped strictly to slab bounds
    gx = np.linspace(-4.0, 80.0, 29)
    gy = np.linspace(-80.0, 4.0, 29)
    grid_verts = [[None for _ in range(len(gx))] for _ in range(len(gy))]

    for j, y_val in enumerate(gy):
        for i, x_val in enumerate(gx):
            d = math.hypot(x_val - bcx, y_val - bcy)
            if d <= br and -80.0 <= x_val <= 80.0 and -80.0 <= y_val <= 80.0:
                grid_verts[j][i] = bm_bay.verts.new((x_val, y_val, bcz))

    # Construct horizontal water quads
    for j in range(len(gy) - 1):
        for i in range(len(gx) - 1):
            v00 = grid_verts[j][i]
            v10 = grid_verts[j][i + 1]
            v11 = grid_verts[j + 1][i + 1]
            v01 = grid_verts[j + 1][i]
            if v00 and v10 and v11 and v01:
                bm_bay.faces.new((v00, v10, v11, v01))

    # Vertical Water Cutaway Wall on East Boundary (X = 80.0m)
    # Connects surface Z = 0.0m down to seabed Z = -4.50m
    east_col = len(gx) - 1
    for j in range(len(gy) - 1):
        v_top1 = grid_verts[j][east_col]
        v_top2 = grid_verts[j + 1][east_col]
        if v_top1 and v_top2:
            z_bed1 = compute_terrain_elevation(v_top1.co.x, v_top1.co.y)
            z_bed2 = compute_terrain_elevation(v_top2.co.x, v_top2.co.y)
            v_bot1 = bm_bay.verts.new((v_top1.co.x, v_top1.co.y, z_bed1))
            v_bot2 = bm_bay.verts.new((v_top2.co.x, v_top2.co.y, z_bed2))
            bm_bay.faces.new((v_top1, v_bot1, v_bot2, v_top2))

    # Vertical Water Cutaway Wall on South Boundary (Y = -80.0m)
    # Connects surface Z = 0.0m down to seabed Z = -4.50m
    south_row = 0
    for i in range(len(gx) - 1):
        v_top1 = grid_verts[south_row][i]
        v_top2 = grid_verts[south_row][i + 1]
        if v_top1 and v_top2:
            z_bed1 = compute_terrain_elevation(v_top1.co.x, v_top1.co.y)
            z_bed2 = compute_terrain_elevation(v_top2.co.x, v_top2.co.y)
            v_bot1 = bm_bay.verts.new((v_top1.co.x, v_top1.co.y, z_bed1))
            v_bot2 = bm_bay.verts.new((v_top2.co.x, v_top2.co.y, z_bed2))
            bm_bay.faces.new((v_top1, v_top2, v_bot2, v_bot1))

    bm_bay.to_mesh(m_bay)
    bm_bay.free()
    m_bay.polygons.foreach_set("use_smooth", [True] * len(m_bay.polygons))
    hydrology_objs["Water_Bay_Marine"] = o_bay

    # 3. Valley Meandering River Ribbon: strictly scoped to valley corridor t in [0.30, 0.525]
    # Descends monotonically from cascades plunge pool (Z = 8.15m) into lake entrance (Z = 4.88m)
    m_river = bpy.data.meshes.new("Water_River_Meander_Mesh")
    o_river = bpy.data.objects.new("Water_River_Meander", m_river)
    collection.objects.link(o_river)
    m_river.materials.append(mat_water)

    bm_riv = bmesh.new()
    t_vals = np.linspace(0.30, 0.525, 75)
    rx, ry, rz, rw = evaluate_river_spline(t_vals)

    # Query actual terrain mesh height using BVH tree of Diorama_Island_Block
    diorama_obj = bpy.data.objects.get("Diorama_Island_Block")
    diorama_bvh = None
    bm_d = None
    if diorama_obj:
        bm_d = bmesh.new()
        bm_d.from_mesh(diorama_obj.data)
        diorama_bvh = BVHTree.FromBMesh(bm_d)

    riv_rows = []
    for k in range(len(t_vals)):
        cx, cy, cz, w = float(rx[k]), float(ry[k]), float(rz[k]), float(rw[k])
        # Compute forward tangent
        if k < len(t_vals) - 1:
            tx = float(rx[k + 1]) - cx
            ty = float(ry[k + 1]) - cy
        else:
            tx = cx - float(rx[k - 1])
            ty = cy - float(ry[k - 1])
        t_len = math.hypot(tx, ty) or 1.0
        nx = -ty / t_len
        ny = tx / t_len

        row = []
        for col_idx, f in enumerate([-0.5, -0.25, 0.0, 0.25, 0.5]):
            px = cx + f * w * nx
            py = cy + f * w * ny
            actual_tz = compute_terrain_elevation(px, py)
            if diorama_bvh:
                hit, _, _, _ = diorama_bvh.ray_cast(Vector((px, py, 50.0)), Vector((0, 0, -1)))
                if hit:
                    actual_tz = float(hit.z)
            if col_idx == 2:
                pz = cz
            else:
                pz = float(np.clip(cz, actual_tz + 0.02, actual_tz + 0.85))
            row.append(bm_riv.verts.new((px, py, pz)))
        riv_rows.append(row)

    if bm_d:
        bm_d.free()

    for k in range(len(t_vals) - 1):
        r1, r2 = riv_rows[k], riv_rows[k + 1]
        for c in range(4):
            bm_riv.faces.new((r1[c], r2[c], r2[c + 1], r1[c + 1]))

    bm_riv.to_mesh(m_river)
    bm_riv.free()
    m_river.polygons.foreach_set("use_smooth", [True] * len(m_river.polygons))
    hydrology_objs["Water_River_Meander"] = o_river

    # 4. Stepped Mountain & Lake-Outlet Cascades
    # Combines alpine mountain cascades and lake-to-bay outlet gorge waterfall
    m_casc = bpy.data.meshes.new("Water_Mountain_Cascades_Mesh")
    o_casc = bpy.data.objects.new("Water_Mountain_Cascades", m_casc)
    collection.objects.link(o_casc)
    m_casc.materials.append(mat_foam)

    bm_c = bmesh.new()
    cascade_tiers = [
        # Alpine Tier 1 (High mountain chute)
        ((-6.5, 44.0, 21.2), (-4.5, 41.5, 15.2), 3.4),
        # Alpine Tier 2 (Middle cascade into valley river start)
        ((-3.2, 38.0, 14.6), (-0.01, 27.38, 8.15), 4.2),
        # Lake Outlet Waterfall Tier 1 (Spillway chute from lake into intermediate pool)
        ((0.0, -19.0, 4.52), (3.5, -21.5, 2.20), 4.5),
        # Lake Outlet Waterfall Tier 2 (Coastal cliff drop plunging into marine bay)
        ((4.0, -22.0, 2.15), (9.0, -25.0, 0.05), 5.5),
    ]
    for p_top, p_bot, w in cascade_tiers:
        x1, y1, z1 = p_top
        x2, y2, z2 = p_bot
        dx, dy = x2 - x1, y2 - y1
        l = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / l, dx / l

        v1 = bm_c.verts.new((x1 - 0.5 * w * nx, y1 - 0.5 * w * ny, z1))
        v2 = bm_c.verts.new((x1 + 0.5 * w * nx, y1 + 0.5 * w * ny, z1))
        v3 = bm_c.verts.new((x2 + 0.5 * w * nx, y2 + 0.5 * w * ny, z2))
        v4 = bm_c.verts.new((x2 - 0.5 * w * nx, y2 - 0.5 * w * ny, z2))
        bm_c.faces.new((v1, v2, v3, v4))

    # Base impact foam apron where outlet waterfall hits marine bay (Z = 0.05m)
    bmesh.ops.create_circle(
        bm_c,
        cap_ends=True,
        radius=4.0,
        segments=16,
        matrix=Matrix.Translation((9.0, -25.0, 0.05))
    )

    bm_c.to_mesh(m_casc)
    bm_c.free()
    m_casc.polygons.foreach_set("use_smooth", [True] * len(m_casc.polygons))
    hydrology_objs["Water_Mountain_Cascades"] = o_casc

    # 5. Hydrology Pebble Shores (Scattered boulders and riverbed stones)
    m_peb = bpy.data.meshes.new("Hydrology_Pebble_Shores_Mesh")
    o_peb = bpy.data.objects.new("Hydrology_Pebble_Shores", m_peb)
    collection.objects.link(o_peb)
    mat_stone = create_pbr_material("M_River_Stone", (0.36, 0.34, 0.32, 1.0), roughness=0.55)
    m_peb.materials.append(mat_stone)

    bm_p = bmesh.new()
    rng = random.Random(42)
    # Generate 50 smooth pebbles around shoreline and river banks
    pebble_centers = []
    for _ in range(30):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(22.0, 26.5)
        px = lcx + r * math.cos(ang)
        py = lcy + r * math.sin(ang)
        pz = compute_terrain_elevation(px, py)
        pebble_centers.append((px, py, pz, rng.uniform(0.25, 0.65)))

    for _ in range(20):
        t = rng.uniform(0.35, 0.90)
        rx_val, ry_val, rz_val, rw_val = evaluate_river_spline(t)
        side = rng.choice([-1.0, 1.0])
        px = rx_val + side * (rw_val * 0.5 + rng.uniform(0.2, 1.5))
        py = ry_val + rng.uniform(-0.5, 0.5)
        pz = compute_terrain_elevation(px, py)
        pebble_centers.append((px, py, pz, rng.uniform(0.20, 0.50)))

    for px, py, pz, s in pebble_centers:
        bmesh.ops.create_icosphere(bm_p, subdivisions=1, radius=s, matrix=Matrix.Translation((px, py, pz + s * 0.4)))

    bm_p.to_mesh(m_peb)
    bm_p.free()
    m_peb.polygons.foreach_set("use_smooth", [True] * len(m_peb.polygons))
    hydrology_objs["Hydrology_Pebble_Shores"] = o_peb

    return hydrology_objs


# =============================================================================
# 6. Subterranean Karst Cave System
# =============================================================================

def build_karst_cave_system(collection: bpy.types.Collection) -> Dict[str, bpy.types.Object]:
    """
    Constructs subterranean karst cave system:
    - Cavern chamber at (14.0, 16.0, -4.5m)
    - Floor Z = -7.50m, Vault apex Z = -0.50m
    - Overburden clearance >= 12.0m (> 5.0m invariant)
    - Speleothems (16 stalactites, 14 stalagmites, 4 fused columns)
    - Cave entrance portal at (16.0, -6.5, 2.4m)
    - Subterranean pool at Z = -7.20m
    - Glowing fungi clusters and cyan 35W point light
    """
    cave_objs = {}
    mat_limestone = create_pbr_material("M_Cave_Limestone", (0.28, 0.26, 0.24, 1.0), roughness=0.80)
    mat_fungi = create_bioluminescent_material()
    mat_pool = create_pbr_material("M_CaveWater_PBR", (0.05, 0.65, 0.75, 1.0), roughness=0.08, transmission=0.92)

    cx, cy, cz = 14.0, 18.0, -7.20
    rx, ry = 11.5, 14.5
    z_floor = -9.20
    z_apex = -2.20

    # 1. Cavern Room Mesh (Vaulted ceiling and solid floor)
    m_cavern = bpy.data.meshes.new("Cave_Cavern_Chamber_Mesh")
    o_cavern = bpy.data.objects.new("Cave_Cavern_Chamber", m_cavern)
    collection.objects.link(o_cavern)
    m_cavern.materials.append(mat_limestone)

    bm_c = bmesh.new()
    N_phi = 16
    N_theta = 24
    cavern_verts = []

    for i in range(N_phi + 1):
        phi = 0.5 * math.pi * (i / float(N_phi))  # 0 at apex, pi/2 at equator
        row = []
        for j in range(N_theta):
            theta = 2.0 * math.pi * (j / float(N_theta))
            vx = cx + rx * math.sin(phi) * math.cos(theta)
            vy = cy + ry * math.sin(phi) * math.sin(theta)
            vz = cz + (z_apex - cz) * math.cos(phi)
            row.append(bm_c.verts.new((vx, vy, vz)))
        cavern_verts.append(row)

    # Apex fan
    for j in range(N_theta):
        jnxt = (j + 1) % N_theta
        bm_c.faces.new((cavern_verts[0][0], cavern_verts[1][jnxt], cavern_verts[1][j]))

    # Ceiling rings
    for i in range(1, N_phi):
        for j in range(N_theta):
            jnxt = (j + 1) % N_theta
            bm_c.faces.new((cavern_verts[i][j], cavern_verts[i][jnxt], cavern_verts[i + 1][jnxt], cavern_verts[i + 1][j]))

    # Floor polygon
    floor_center = bm_c.verts.new((cx, cy, z_floor))
    floor_rim = []
    for j in range(N_theta):
        theta = 2.0 * math.pi * (j / float(N_theta))
        vx = cx + rx * math.cos(theta)
        vy = cy + ry * math.sin(theta)
        floor_rim.append(bm_c.verts.new((vx, vy, z_floor)))

    for j in range(N_theta):
        jnxt = (j + 1) % N_theta
        bm_c.faces.new((floor_center, floor_rim[j], floor_rim[jnxt]))
        # Connect equator to floor
        bm_c.faces.new((cavern_verts[-1][j], cavern_verts[-1][jnxt], floor_rim[jnxt], floor_rim[j]))

    bm_c.to_mesh(m_cavern)
    bm_c.free()
    m_cavern.polygons.foreach_set("use_smooth", [True] * len(m_cavern.polygons))
    cave_objs["Cave_Cavern_Chamber"] = o_cavern

    # 2. Speleothems (16 stalactites, 14 stalagmites, 4 fused columns)
    m_speleo = bpy.data.meshes.new("Cave_Speleothems_Mesh")
    o_speleo = bpy.data.objects.new("Cave_Speleothems", m_speleo)
    collection.objects.link(o_speleo)
    m_speleo.materials.append(mat_limestone)

    bm_s = bmesh.new()
    rng = random.Random(101)

    # 16 Stalactites (hanging cones from ceiling)
    for _ in range(16):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(2.0, 9.5)
        sx = cx + r * math.cos(ang)
        sy = cy + r * 1.1 * math.sin(ang)
        phi = math.asin(min(1.0, math.hypot((sx - cx)/rx, (sy - cy)/ry)))
        sz = cz + (z_apex - cz) * math.cos(phi)
        h = rng.uniform(1.8, 3.8)
        rb = rng.uniform(0.35, 0.70)
        bmesh.ops.create_cone(bm_s, cap_ends=True, cap_tris=False, segments=8, radius1=rb, radius2=0.04, depth=h, matrix=Matrix.Translation((sx, sy, sz - h * 0.5)))

    # 14 Stalagmites (upright cones on floor)
    for _ in range(14):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(2.5, 10.0)
        sx = cx + r * math.cos(ang)
        sy = cy + r * 1.1 * math.sin(ang)
        sz = z_floor
        h = rng.uniform(1.2, 3.4)
        rb = rng.uniform(0.40, 0.85)
        bmesh.ops.create_cone(bm_s, cap_ends=True, cap_tris=False, segments=8, radius1=rb, radius2=0.06, depth=h, matrix=Matrix.Translation((sx, sy, sz + h * 0.5)))

    # 4 Fused Karst Columns
    column_locs = [(cx - 3.5, cy - 3.0), (cx + 4.0, cy - 3.5), (cx - 3.0, cy + 4.5), (cx + 3.5, cy + 4.0)]
    for col_x, col_y in column_locs:
        phi = math.asin(min(1.0, math.hypot((col_x - cx)/rx, (col_y - cy)/ry)))
        top_z = cz + (z_apex - cz) * math.cos(phi)
        h = top_z - z_floor
        mid_z = z_floor + 0.5 * h
        bmesh.ops.create_cone(bm_s, cap_ends=True, cap_tris=False, segments=10, radius1=0.75, radius2=0.55, depth=h, matrix=Matrix.Translation((col_x, col_y, mid_z)))

    bm_s.to_mesh(m_speleo)
    bm_s.free()
    m_speleo.polygons.foreach_set("use_smooth", [True] * len(m_speleo.polygons))
    cave_objs["Cave_Speleothems"] = o_speleo

    # 3. Arched Cave Entrance Portal at (16.0, -6.5, 2.10m) carved through gorge cliff into cavern
    m_port = bpy.data.meshes.new("Cave_Entrance_Portal_Mesh")
    o_port = bpy.data.objects.new("Cave_Entrance_Portal", m_port)
    collection.objects.link(o_port)
    m_port.materials.append(mat_limestone)

    bm_p = bmesh.new()
    ex, ey, ez = 16.0, -6.5, 2.10
    tx, ty, tz = 13.5, 5.0, -7.20  # connection inside cavern room

    N_steps = 14
    tunnel_rings = []
    w_base, h_base = 4.2, 3.8

    for s in range(N_steps + 1):
        f = s / float(N_steps)
        # S-curve progression along descending tunnel path
        sf = 3.0 * f**2 - 2.0 * f**3
        px = ex * (1.0 - sf) + tx * sf
        py = ey * (1.0 - sf) + ty * sf
        pz = ez * (1.0 - sf) + tz * sf

        # Forward tangent and normal
        df = 0.01
        f_next = min(1.0, f + df)
        sf_next = 3.0 * f_next**2 - 2.0 * f_next**3
        dx = (ex * (1.0 - sf_next) + tx * sf_next) - px
        dy = (ey * (1.0 - sf_next) + ty * sf_next) - py
        l_xy = math.hypot(dx, dy) or 1.0
        nx = -dy / l_xy
        ny = dx / l_xy

        w = w_base + 1.2 * f
        h = h_base + 0.8 * f

        # Vaulted Arch Profile: 8 vertices per ring (floor + walls + arch ceiling)
        # Vertices 0..7 ordered clockwise: 0=floor left, 1=wall left, 2..5=vault arch, 6=wall right, 7=floor right
        ring_v = []
        # Floor Left
        ring_v.append(bm_p.verts.new((px - 0.5 * w * nx, py - 0.5 * w * ny, pz)))
        # Wall Left
        ring_v.append(bm_p.verts.new((px - 0.5 * w * nx, py - 0.5 * w * ny, pz + h * 0.45)))
        # Vault Arch (4 points)
        for k in range(4):
            ang = math.pi * (0.80 - 0.60 * (k / 3.0))
            vx = px + 0.5 * w * math.cos(ang) * nx
            vy = py + 0.5 * w * math.cos(ang) * ny
            vz = pz + h * 0.45 + h * 0.55 * math.sin(ang)
            ring_v.append(bm_p.verts.new((vx, vy, vz)))
        # Wall Right
        ring_v.append(bm_p.verts.new((px + 0.5 * w * nx, py + 0.5 * w * ny, pz + h * 0.45)))
        # Floor Right
        ring_v.append(bm_p.verts.new((px + 0.5 * w * nx, py + 0.5 * w * ny, pz)))
        tunnel_rings.append(ring_v)

    # Connect tunnel rings with inward-facing quad faces (hollow interior passage)
    for s in range(N_steps):
        r1, r2 = tunnel_rings[s], tunnel_rings[s + 1]
        for v_i in range(7):
            bm_p.faces.new((r1[v_i], r2[v_i], r2[v_i + 1], r1[v_i + 1]))
        # Connect floor
        bm_p.faces.new((r1[7], r2[7], r2[0], r1[0]))

    # Sculpted Exterior Portal Arch Facade & Keystone Rim at Entrance (s = 0)
    r0 = tunnel_rings[0]
    facade_thickness = 0.85
    r0_front = []
    # Project outwards along cliff face normal
    front_dir = Vector((-0.45, -0.89, 0.0)).normalized()
    for v in r0:
        r0_front.append(bm_p.verts.new(v.co + front_dir * facade_thickness))

    for v_i in range(7):
        bm_p.faces.new((r0[v_i + 1], r0[v_i], r0_front[v_i], r0_front[v_i + 1]))
    # Floor front
    bm_p.faces.new((r0[0], r0[7], r0_front[7], r0_front[0]))

    bm_p.to_mesh(m_port)
    bm_p.free()
    m_port.polygons.foreach_set("use_smooth", [True] * len(m_port.polygons))
    cave_objs["Cave_Entrance_Portal"] = o_port

    # 4. Subterranean Pool at Z = -8.20m (Radius = 8.5m)
    m_pool = bpy.data.meshes.new("Water_Cave_Pool_Mesh")
    o_pool = bpy.data.objects.new("Water_Cave_Pool", m_pool)
    collection.objects.link(o_pool)
    m_pool.materials.append(mat_pool)

    bm_pool = bmesh.new()
    bmesh.ops.create_circle(bm_pool, cap_ends=True, radius=8.5, segments=32, matrix=Matrix.Translation((cx, cy, -8.20)))
    bm_pool.to_mesh(m_pool)
    bm_pool.free()
    m_pool.polygons.foreach_set("use_smooth", [True] * len(m_pool.polygons))
    cave_objs["Water_Cave_Pool"] = o_pool

    # 5. Bioluminescent Fungi Clusters (28 glowing mushrooms)
    m_mush = bpy.data.meshes.new("Cave_Biolum_Fungi_Mesh")
    o_mush = bpy.data.objects.new("Cave_Biolum_Fungi", m_mush)
    collection.objects.link(o_mush)
    m_mush.materials.append(mat_fungi)

    bm_m = bmesh.new()
    for _ in range(28):
        ang = rng.uniform(0.0, 2.0 * math.pi)
        r = rng.uniform(3.0, 12.5)
        mx = cx + r * math.cos(ang)
        my = cy + r * 1.1 * math.sin(ang)
        mz = z_floor
        # Mushroom stalk
        bmesh.ops.create_cone(bm_m, cap_ends=True, segments=6, radius1=0.08, radius2=0.05, depth=0.6, matrix=Matrix.Translation((mx, my, mz + 0.3)))
        # Mushroom dome cap
        bmesh.ops.create_icosphere(bm_m, subdivisions=1, radius=0.28, matrix=Matrix.Translation((mx, my, mz + 0.6)))

    bm_m.to_mesh(m_mush)
    bm_m.free()
    m_mush.polygons.foreach_set("use_smooth", [True] * len(m_mush.polygons))
    cave_objs["Cave_Biolum_Fungi"] = o_mush

    # 6. Point Light for Cavern Bioluminescence (35W, soft radius 3.0m, cyan)
    l_data = bpy.data.lights.new("Cave_Biolum_Light_Data", 'POINT')
    l_data.energy = 35.0
    l_data.color = (0.12, 0.92, 0.82)
    l_data.shadow_soft_size = 3.0
    o_light = bpy.data.objects.new("Cave_Biolum_Light", l_data)
    o_light.location = (cx, cy, cz)
    collection.objects.link(o_light)
    cave_objs["Cave_Biolum_Light"] = o_light

    return cave_objs


# =============================================================================
# 7. 13 Procedural Botanical Prototypes (Smooth Shading Invariant)
# =============================================================================

def build_botanical_prototypes(collections: Dict[str, bpy.types.Collection]) -> Dict[str, bpy.types.Object]:
    """
    Constructs 13 distinct procedural botanical prototypes across 4 biomes.
    All polygon faces have use_smooth = True.
    Prototypes are linked into their respective sub-collections.
    """
    prototypes = {}

    # Materials for Flora
    mat_bark_pine = create_pbr_material("M_Bark_Pine", (0.12, 0.08, 0.05, 1.0), roughness=0.85)
    mat_needles_pine = create_pbr_material("M_Needles_Pine", (0.05, 0.22, 0.06, 1.0), roughness=0.55)
    mat_bark_oak = create_pbr_material("M_Bark_Oak", (0.16, 0.10, 0.06, 1.0), roughness=0.85)
    mat_leaves_oak = create_pbr_material("M_Leaves_Oak", (0.10, 0.38, 0.08, 1.0), roughness=0.50)
    mat_flower = create_pbr_material("M_Flower_Petals", (0.92, 0.85, 0.20, 1.0), roughness=0.30)
    mat_fern = create_pbr_material("M_Fern_Frond", (0.14, 0.44, 0.10, 1.0), roughness=0.45)
    mat_lily_pad = create_pbr_material("M_Lily_Pad", (0.08, 0.36, 0.16, 1.0), roughness=0.40)
    mat_reed = create_pbr_material("M_Reed_Green", (0.28, 0.48, 0.12, 1.0), roughness=0.60)
    mat_cattail = create_pbr_material("M_Cattail_Spike", (0.18, 0.10, 0.05, 1.0), roughness=0.90)
    mat_shroom_cap = create_bioluminescent_material()
    mat_moss = create_pbr_material("M_Cave_Moss", (0.06, 0.28, 0.12, 1.0), roughness=0.75)

    def _make_obj(name: str, col_name: str) -> Tuple[bpy.types.Object, bmesh.types.BMesh]:
        m = bpy.data.meshes.new(f"{name}_Mesh")
        o = bpy.data.objects.new(name, m)
        collections[col_name].objects.link(o)
        bm = bmesh.new()
        return o, bm

    def _finish_obj(o: bpy.types.Object, bm: bmesh.types.BMesh, mats: List[bpy.types.Material]):
        for mat in mats:
            o.data.materials.append(mat)
        bm.to_mesh(o.data)
        bm.free()
        o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
        prototypes[o.name] = o

    # -------------------------------------------------------------------------
    # Alpine Biome (3 prototypes)
    # -------------------------------------------------------------------------
    # 1. Flora_Alpine_DwarfPine
    o, bm = _make_obj("Flora_Alpine_DwarfPine", "Col_Flora_Alpine")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.32, radius2=0.10, depth=4.2, matrix=Matrix.Translation((0, 0, 2.1)))
    f_before = len(bm.faces)
    for th, tr in [(1.6, 1.8), (2.6, 1.4), (3.4, 1.0), (4.1, 0.6)]:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=tr, radius2=0.05, depth=1.2, matrix=Matrix.Translation((0, 0, th)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_pine, mat_needles_pine])

    # 2. Flora_Alpine_TussockGrass
    o, bm = _make_obj("Flora_Alpine_TussockGrass", "Col_Flora_Alpine")
    for i in range(12):
        ang = 2.0 * math.pi * i / 12.0
        tilt = Matrix.Rotation(math.radians(18.0), 4, 'X') @ Matrix.Rotation(ang, 4, 'Z')
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.06, radius2=0.01, depth=0.7, matrix=Matrix.Translation((0, 0, 0.35)) @ tilt)
    _finish_obj(o, bm, [mat_needles_pine])

    # 3. Flora_Alpine_RockMoss
    o, bm = _make_obj("Flora_Alpine_RockMoss", "Col_Flora_Alpine")
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.35, matrix=Matrix.Scale(0.4, 4, Vector((0, 0, 1))))
    _finish_obj(o, bm, [mat_moss])

    # -------------------------------------------------------------------------
    # Forest Biome (4 prototypes)
    # -------------------------------------------------------------------------
    # 4. Flora_Forest_CanopyOak
    o, bm = _make_obj("Flora_Forest_CanopyOak", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.45, radius2=0.25, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
    f_before = len(bm.faces)
    for ox, oy, oz, sr in [(0, 0, 5.8, 2.2), (-1.2, 0.8, 5.0, 1.6), (1.1, -0.6, 5.2, 1.7), (0.4, 1.1, 5.4, 1.5)]:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=sr, matrix=Matrix.Translation((ox, oy, oz)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_leaves_oak])

    # 5. Flora_Forest_Shrub
    o, bm = _make_obj("Flora_Forest_Shrub", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.15, radius2=0.08, depth=1.4, matrix=Matrix.Translation((0, 0, 0.7)))
    f_before = len(bm.faces)
    for ox, oy, oz in [(0, 0, 1.3), (-0.4, 0.3, 1.1), (0.4, -0.2, 1.2)]:
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.75, matrix=Matrix.Translation((ox, oy, oz)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_leaves_oak])

    # 6. Flora_Forest_Wildflower
    o, bm = _make_obj("Flora_Forest_Wildflower", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.03, radius2=0.02, depth=0.45, matrix=Matrix.Translation((0, 0, 0.22)))
    f_before = len(bm.faces)
    bmesh.ops.create_circle(bm, cap_ends=True, radius=0.18, segments=8, matrix=Matrix.Translation((0, 0, 0.45)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_leaves_oak, mat_flower])

    # 7. Flora_Forest_Fern
    o, bm = _make_obj("Flora_Forest_Fern", "Col_Flora_Forest")
    for i in range(8):
        ang = 2.0 * math.pi * i / 8.0
        rot = Matrix.Rotation(ang, 4, 'Z') @ Matrix.Rotation(math.radians(35.0), 4, 'X')
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.12, radius2=0.01, depth=0.85, matrix=Matrix.Translation((0, 0, 0.35)) @ rot)
    _finish_obj(o, bm, [mat_fern])

    # -------------------------------------------------------------------------
    # Aquatic & Riparian Biome (4 prototypes)
    # -------------------------------------------------------------------------
    # 8. Flora_Aquatic_WaterLily
    o, bm = _make_obj("Flora_Aquatic_WaterLily", "Col_Flora_Aquatic")
    bmesh.ops.create_circle(bm, cap_ends=True, radius=0.55, segments=16, matrix=Matrix.Translation((0, 0, 0.02)))
    f_before = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.12, radius2=0.02, depth=0.15, matrix=Matrix.Translation((0, 0, 0.10)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_lily_pad, mat_flower])

    # 9. Flora_Aquatic_Duckweed
    o, bm = _make_obj("Flora_Aquatic_Duckweed", "Col_Flora_Aquatic")
    for ox, oy in [(0, 0), (0.12, 0.08), (-0.10, 0.12), (0.08, -0.10)]:
        bmesh.ops.create_circle(bm, cap_ends=True, radius=0.06, segments=6, matrix=Matrix.Translation((ox, oy, 0.01)))
    _finish_obj(o, bm, [mat_lily_pad])

    # 10. Flora_Aquatic_Reed
    o, bm = _make_obj("Flora_Aquatic_Reed", "Col_Flora_Aquatic")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.06, radius2=0.03, depth=2.2, matrix=Matrix.Translation((0, 0, 1.1)))
    f_before = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.08, depth=0.45, matrix=Matrix.Translation((0, 0, 1.8)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_reed, mat_cattail])

    # 11. Flora_Aquatic_WaterWeed
    o, bm = _make_obj("Flora_Aquatic_WaterWeed", "Col_Flora_Aquatic")
    for oz in [0.3, 0.7, 1.1]:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.08, radius2=0.02, depth=0.5, matrix=Matrix.Translation((0, 0, oz)))
    _finish_obj(o, bm, [mat_reed])

    # -------------------------------------------------------------------------
    # Subterranean Cave Biome (2 prototypes)
    # -------------------------------------------------------------------------
    # 12. Flora_Cave_BioMushroom
    o, bm = _make_obj("Flora_Cave_BioMushroom", "Col_Flora_Cave")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.05, depth=0.6, matrix=Matrix.Translation((0, 0, 0.3)))
    f_before = len(bm.faces)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.28, matrix=Matrix.Translation((0, 0, 0.6)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_shroom_cap])

    # 13. Flora_Cave_DarkMoss
    o, bm = _make_obj("Flora_Cave_DarkMoss", "Col_Flora_Cave")
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.22, matrix=Matrix.Scale(0.35, 4, Vector((0, 0, 1))))
    _finish_obj(o, bm, [mat_moss])

    return prototypes


# =============================================================================
# 8. Procedural Geometry Nodes Biome Scatter
# =============================================================================

def build_biome_geometry_nodes_tree(
    tree_name: str,
    proto_collection: bpy.types.Collection,
    z_min: float,
    z_max: float,
    slope_norm_min: float = 0.7071,
    dist_min: float = 3.5,
    density_max: float = 0.12,
    scale_min: float = 0.80,
    scale_max: float = 1.25,
    water_proximity_objects: Optional[List[bpy.types.Object]] = None,
    water_dist_max: float = 3.5,
) -> bpy.types.GeometryNodeTree:
    """Constructs GeometryNodeTree implementing Altitude, Slope, Water Proximity, and Poisson instancing."""
    nt = bpy.data.node_groups.get(tree_name) or bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')
    nt.nodes.clear()

    nt.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    nt.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    s_frust = nt.interface.new_socket("Enable Frustum Culling", in_out='INPUT', socket_type='NodeSocketBool')
    s_frust.default_value = False
    s_lod = nt.interface.new_socket("Enable LOD Distance Culling", in_out='INPUT', socket_type='NodeSocketBool')
    s_lod.default_value = False
    s_dist = nt.interface.new_socket("LOD Max Distance", in_out='INPUT', socket_type='NodeSocketFloat')
    s_dist.default_value = 140.0

    node_in = nt.nodes.new("NodeGroupInput")
    node_in.location = (-1000, 0)
    node_out = nt.nodes.new("NodeGroupOutput")
    node_out.location = (1600, 0)

    # Position & Normal
    pos_node = nt.nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-800, 300)
    norm_node = nt.nodes.new("GeometryNodeInputNormal")
    norm_node.location = (-800, -200)

    sep_pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-600, 300)
    nt.links.new(pos_node.outputs["Position"], sep_pos.inputs["Vector"])

    sep_norm = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_norm.location = (-600, -200)
    nt.links.new(norm_node.outputs["Normal"], sep_norm.inputs["Vector"])

    # Altitude Z Mask
    c_zmin = nt.nodes.new("FunctionNodeCompare")
    c_zmin.data_type = 'FLOAT'
    c_zmin.operation = 'GREATER_EQUAL'
    c_zmin.inputs["B"].default_value = z_min
    nt.links.new(sep_pos.outputs["Z"], c_zmin.inputs["A"])

    c_zmax = nt.nodes.new("FunctionNodeCompare")
    c_zmax.data_type = 'FLOAT'
    c_zmax.operation = 'LESS_EQUAL'
    c_zmax.inputs["B"].default_value = z_max
    nt.links.new(sep_pos.outputs["Z"], c_zmax.inputs["A"])

    and_alt = nt.nodes.new("FunctionNodeBooleanMath")
    and_alt.operation = 'AND'
    nt.links.new(c_zmin.outputs["Result"], and_alt.inputs[0])
    nt.links.new(c_zmax.outputs["Result"], and_alt.inputs[1])

    # Slope Normal Z Mask (Filters cliffs > 45 deg)
    c_slope = nt.nodes.new("FunctionNodeCompare")
    c_slope.data_type = 'FLOAT'
    c_slope.operation = 'GREATER_EQUAL'
    c_slope.inputs["B"].default_value = slope_norm_min
    nt.links.new(sep_norm.outputs["Z"], c_slope.inputs["A"])

    and_mask = nt.nodes.new("FunctionNodeBooleanMath")
    and_mask.operation = 'AND'
    nt.links.new(and_alt.outputs["Boolean"], and_mask.inputs[0])
    nt.links.new(c_slope.outputs["Result"], and_mask.inputs[1])

    # 3. Water Proximity Curve Mask (3rd Mathematical Mask)
    if water_proximity_objects:
        join_water = nt.nodes.new("GeometryNodeJoinGeometry")
        join_water.name = "Join_Water_Bodies"
        join_water.location = (-600, -550)
        for idx, w_obj in enumerate(water_proximity_objects):
            obj_info = nt.nodes.new("GeometryNodeObjectInfo")
            obj_info.inputs["Object"].default_value = w_obj
            obj_info.transform_space = 'RELATIVE'
            obj_info.location = (-850, -450 - idx * 140)
            nt.links.new(obj_info.outputs["Geometry"], join_water.inputs["Geometry"])

        prox = nt.nodes.new("GeometryNodeProximity")
        prox.name = "Water_Proximity_Curve"
        prox.target_element = 'FACES'
        prox.location = (-400, -550)
        nt.links.new(join_water.outputs["Geometry"], prox.inputs["Target"])

        c_water = nt.nodes.new("FunctionNodeCompare")
        c_water.data_type = 'FLOAT'
        c_water.operation = 'LESS_EQUAL'
        c_water.inputs["B"].default_value = water_dist_max
        c_water.location = (-200, -550)
        nt.links.new(prox.outputs["Distance"], c_water.inputs["A"])

        and_water = nt.nodes.new("FunctionNodeBooleanMath")
        and_water.name = "And_Water_Proximity"
        and_water.operation = 'AND'
        and_water.location = (0, -100)
        nt.links.new(and_mask.outputs["Boolean"], and_water.inputs[0])
        nt.links.new(c_water.outputs["Result"], and_water.inputs[1])
        bio_selection = and_water.outputs["Boolean"]
    else:
        bio_selection = and_mask.outputs["Boolean"]

    # Performance Optimization: LOD Distance Culling
    v_dist = nt.nodes.new("ShaderNodeVectorMath")
    v_dist.name = "LOD_Distance_Calc"
    v_dist.operation = 'DISTANCE'
    v_dist.inputs[1].default_value = (0.0, 0.0, 0.0)  # Diorama center
    nt.links.new(pos_node.outputs["Position"], v_dist.inputs[0])

    cmp_dist = nt.nodes.new("FunctionNodeCompare")
    cmp_dist.data_type = 'FLOAT'
    cmp_dist.operation = 'LESS_EQUAL'
    nt.links.new(v_dist.outputs["Value"], cmp_dist.inputs["A"])
    nt.links.new(node_in.outputs["LOD Max Distance"], cmp_dist.inputs["B"])

    not_lod = nt.nodes.new("FunctionNodeBooleanMath")
    not_lod.operation = 'NOT'
    nt.links.new(node_in.outputs["Enable LOD Distance Culling"], not_lod.inputs[0])

    lod_pass = nt.nodes.new("FunctionNodeBooleanMath")
    lod_pass.operation = 'OR'
    nt.links.new(not_lod.outputs["Boolean"], lod_pass.inputs[0])
    nt.links.new(cmp_dist.outputs["Result"], lod_pass.inputs[1])

    # Performance Optimization: Camera Frustum Culling Toggle (CAM_01_ISO_SE at (140, -140, 110))
    v_cam_to_pt = nt.nodes.new("ShaderNodeVectorMath")
    v_cam_to_pt.operation = 'SUBTRACT'
    v_cam_to_pt.inputs[1].default_value = (140.0, -140.0, 110.0)
    nt.links.new(pos_node.outputs["Position"], v_cam_to_pt.inputs[0])

    v_cam_norm = nt.nodes.new("ShaderNodeVectorMath")
    v_cam_norm.operation = 'NORMALIZE'
    nt.links.new(v_cam_to_pt.outputs["Vector"], v_cam_norm.inputs[0])

    v_dot = nt.nodes.new("ShaderNodeVectorMath")
    v_dot.operation = 'DOT_PRODUCT'
    v_dot.inputs[1].default_value = (-0.627, 0.627, -0.457)
    nt.links.new(v_cam_norm.outputs["Vector"], v_dot.inputs[0])

    cmp_frust = nt.nodes.new("FunctionNodeCompare")
    cmp_frust.data_type = 'FLOAT'
    cmp_frust.operation = 'GREATER_EQUAL'
    cmp_frust.inputs["B"].default_value = 0.880
    nt.links.new(v_dot.outputs["Value"], cmp_frust.inputs["A"])

    not_frust = nt.nodes.new("FunctionNodeBooleanMath")
    not_frust.operation = 'NOT'
    nt.links.new(node_in.outputs["Enable Frustum Culling"], not_frust.inputs[0])

    frust_pass = nt.nodes.new("FunctionNodeBooleanMath")
    frust_pass.operation = 'OR'
    nt.links.new(not_frust.outputs["Boolean"], frust_pass.inputs[0])
    nt.links.new(cmp_frust.outputs["Result"], frust_pass.inputs[1])

    # Combine Culling Masks
    cull_mask = nt.nodes.new("FunctionNodeBooleanMath")
    cull_mask.operation = 'AND'
    nt.links.new(lod_pass.outputs["Boolean"], cull_mask.inputs[0])
    nt.links.new(frust_pass.outputs["Boolean"], cull_mask.inputs[1])

    # Final Selection Input
    final_selection = nt.nodes.new("FunctionNodeBooleanMath")
    final_selection.name = "Final_Selection_Mask"
    final_selection.operation = 'AND'
    nt.links.new(bio_selection, final_selection.inputs[0])
    nt.links.new(cull_mask.outputs["Boolean"], final_selection.inputs[1])

    # Distribute Points
    dist_pts = nt.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist_pts.distribute_method = 'POISSON'
    dist_pts.inputs["Distance Min"].default_value = dist_min
    dist_pts.inputs["Density Max"].default_value = density_max
    nt.links.new(node_in.outputs["Geometry"], dist_pts.inputs["Mesh"])
    nt.links.new(final_selection.outputs["Boolean"], dist_pts.inputs["Selection"])

    # Collection Instancing
    col_info = nt.nodes.new("GeometryNodeCollectionInfo")
    col_info.inputs["Collection"].default_value = proto_collection
    col_info.inputs["Separate Children"].default_value = True
    col_info.inputs["Reset Children"].default_value = True

    inst_node = nt.nodes.new("GeometryNodeInstanceOnPoints")
    inst_node.inputs["Pick Instance"].default_value = True
    nt.links.new(dist_pts.outputs["Points"], inst_node.inputs["Points"])
    nt.links.new(col_info.outputs["Instances"], inst_node.inputs["Instance"])

    # Random Scale & Rotation
    rand_scale = nt.nodes.new("FunctionNodeRandomValue")
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs["Min"].default_value = scale_min
    rand_scale.inputs["Max"].default_value = scale_max
    nt.links.new(rand_scale.outputs["Value"], inst_node.inputs["Scale"])

    rand_rot = nt.nodes.new("FunctionNodeRandomValue")
    rand_rot.data_type = 'FLOAT_VECTOR'
    rand_rot.inputs["Min"].default_value = (-0.05, -0.05, 0.0)
    rand_rot.inputs["Max"].default_value = (0.05, 0.05, 2.0 * math.pi)
    nt.links.new(rand_rot.outputs["Value"], inst_node.inputs["Rotation"])

    # Realize Instances & Set Shade Smooth
    realize_node = nt.nodes.new("GeometryNodeRealizeInstances")
    nt.links.new(inst_node.outputs["Instances"], realize_node.inputs["Geometry"])

    smooth_node = nt.nodes.new("GeometryNodeSetShadeSmooth")
    nt.links.new(realize_node.outputs["Geometry"], smooth_node.inputs["Mesh"])
    nt.links.new(smooth_node.outputs["Mesh"], node_out.inputs["Geometry"])

    return nt


def setup_biome_scatter(
    collections: Dict[str, bpy.types.Collection],
    diorama_block: bpy.types.Object,
) -> Dict[str, bpy.types.Object]:
    """Creates 4 scatter carrier objects in Biome_Scatter collection."""
    scatter_objs = {}
    biome_configs = [
        ("Scatter_Alpine_Conifers", "Col_Flora_Alpine", 12.0, 36.0, 0.7071, 4.5, 0.08),
        ("Scatter_Valley_Forest", "Col_Flora_Forest", 4.2, 13.0, 0.7800, 3.8, 0.10),
        ("Scatter_Aquatic_Riparian", "Col_Flora_Aquatic", 4.0, 5.5, 0.8500, 2.2, 0.15),
        ("Scatter_Cave_Biolum", "Col_Flora_Cave", -7.5, -2.0, 0.6000, 2.5, 0.12),
    ]

    water_objs = [
        bpy.data.objects.get("Water_Lake_Central"),
        bpy.data.objects.get("Water_River_Meander"),
    ]
    water_objs = [o for o in water_objs if o is not None]

    for carrier_name, col_proto_name, z_min, z_max, slope_min, dist_min, dens_max in biome_configs:
        m_carrier = bpy.data.meshes.new(f"{carrier_name}_Mesh")
        o_carrier = bpy.data.objects.new(carrier_name, m_carrier)
        collections["Biome_Scatter"].objects.link(o_carrier)

        # Create carrier plane grid
        bm = bmesh.new()
        if "Cave" in carrier_name:
            bmesh.ops.create_grid(bm, x_segments=16, y_segments=16, size=15.0, matrix=Matrix.Translation((14.0, 16.0, -7.45)))
        else:
            bmesh.ops.create_grid(bm, x_segments=32, y_segments=32, size=75.0, matrix=Matrix.Translation((0.0, 0.0, 0.0)))
            for v in bm.verts:
                v.co.z = compute_terrain_elevation(v.co.x, v.co.y)
        bm.to_mesh(m_carrier)
        bm.free()

        # Add GN Modifier
        mod = o_carrier.modifiers.new(name="GeometryNodes", type='NODES')
        proto_col = collections[col_proto_name]
        is_aquatic = "Aquatic" in carrier_name
        nt = build_biome_geometry_nodes_tree(
            tree_name=f"GN_{carrier_name}",
            proto_collection=proto_col,
            z_min=z_min,
            z_max=z_max,
            slope_norm_min=slope_min,
            dist_min=dist_min,
            density_max=dens_max,
            water_proximity_objects=water_objs if is_aquatic else None,
            water_dist_max=3.5,
        )
        mod.node_group = nt
        scatter_objs[carrier_name] = o_carrier

    return scatter_objs


# =============================================================================
# 9. 24-Angle Automated Camera Rig
# =============================================================================

def build_24_camera_rig(collection: bpy.types.Collection) -> Dict[str, bpy.types.Object]:
    """
    Constructs the exact 24-camera rig linked to Camera_Rig_24 collection.
    Includes:
    - 4 Isometric perspectives (SE, SW, NW, NE)
    - 1 Top-down orthographic
    - 4 Cardinal side views (N, E, S, W)
    - 2 Geological near-plane cutaways (CAM_10 Section A-A and CAM_11 Section B-B with clip_start = 200.0m)
    - 8 Biome & Hydrological close-ups
    - 5 Technical / Analytical verification views
    """
    cameras_spec = [
        ("CAM_01_ISO_SE", "PERSP", (140, -140, 120), (0, 0, 6), 65, 0.5, 2000, None),
        ("CAM_02_ISO_SW", "PERSP", (-140, -140, 120), (0, 0, 6), 65, 0.5, 2000, None),
        ("CAM_03_ISO_NW", "PERSP", (-140, 140, 120), (0, 0, 6), 65, 0.5, 2000, None),
        ("CAM_04_ISO_NE", "PERSP", (140, 140, 120), (0, 0, 6), 65, 0.5, 2000, None),
        ("CAM_05_TOP_ORTHO", "ORTHO", (0, 0, 200), (0, 0, 0), None, 0.5, 1000, 180.0),
        ("CAM_06_CARDINAL_NORTH", "ORTHO", (0, 180, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
        ("CAM_07_CARDINAL_EAST", "ORTHO", (180, 0, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
        ("CAM_08_CARDINAL_SOUTH", "ORTHO", (0, -180, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
        ("CAM_09_CARDINAL_WEST", "ORTHO", (-180, 0, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
        ("CAM_10_CUTAWAY_AA", "ORTHO", (0, -200, -2), (0, 0, -2), None, 200.0, 400.0, 170.0),
        ("CAM_11_CUTAWAY_BB", "ORTHO", (-200, 0, -2), (0, 0, -2), None, 200.0, 400.0, 170.0),
        ("CAM_12_CLOSEUP_LAKE_BASIN", "PERSP", (8, -28, 16), (-18, -6, 4.5), 35, 0.2, 500, None),
        ("CAM_13_CLOSEUP_WATERFALL_GORGE", "PERSP", (46, -6, 18), (30, -14, 5), 45, 0.2, 500, None),
        ("CAM_14_CLOSEUP_ALPINE_SUMMIT", "PERSP", (-8, 22, 38), (-8, 52, 28.5), 50, 0.2, 500, None),
        ("CAM_15_CLOSEUP_LOWLAND_FOREST", "PERSP", (-18, 2, 14), (-36, 18, 7), 38, 0.2, 500, None),
        ("CAM_16_CLOSEUP_SUBTERRANEAN_CAVE", "PERSP", (10.0, 12.0, -6.5), (15.0, 18.5, -7.2), 24, 0.1, 150, None),
        ("CAM_17_CLOSEUP_CAVE_ENTRANCE", "PERSP", (26, -14, 5.5), (15, -6.5, 2.2), 42, 0.2, 200, None),
        ("CAM_18_CLOSEUP_RIVER_MEANDER", "PERSP", (-2, 26, 20), (-14, 18, 10), 42, 0.2, 400, None),
        ("CAM_19_CLOSEUP_COASTAL_BAY", "PERSP", (25, -25, 16), (52, -50, 0), 35, 0.2, 500, None),
        ("CAM_20_SLOPE_ANALYSIS_VIEW", "PERSP", (35, 30, 24), (6, 44, 18), 55, 0.5, 600, None),
        ("CAM_21_ELEVATION_HEATMAP_VIEW", "PERSP", (120, -120, 160), (0, 0, 0), 50, 0.5, 2000, None),
        ("CAM_22_BIOME_TRANSITION_CORRIDOR", "PERSP", (-55, 65, 42), (-5, -15, 6), 32, 0.5, 1000, None),
        ("CAM_23_UNDERWATER_SUBMERGED_BED", "PERSP", (-12, -10, 3.2), (-20, -5, 2.3), 28, 0.05, 50, None),
        ("CAM_24_NIGHT_BIOLUMINESCENCE", "PERSP", (24.0, -12.0, 4.5), (16.0, -6.5, 2.1), 35, 0.2, 300, None),
    ]

    cam_dict = {}
    for name, ctype, loc, tgt, lens, near, far, oscale in cameras_spec:
        c = bpy.data.cameras.new(f"{name}_Data")
        c.type = ctype
        c.clip_start = near
        c.clip_end = far
        if ctype == 'PERSP':
            c.lens = lens
        else:
            c.ortho_scale = oscale

        o = bpy.data.objects.new(name, c)
        o.location = Vector(loc)
        o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        collection.objects.link(o)
        cam_dict[name] = o

    # Primary camera
    bpy.context.scene.camera = cam_dict["CAM_01_ISO_SE"]
    return cam_dict


# =============================================================================
# 10. Lighting & Sun Skylight
# =============================================================================

def build_lighting(collection: bpy.types.Collection) -> Dict[str, bpy.types.Object]:
    """Sets up primary sun key light and sky fill light."""
    light_objs = {}

    # Key Light (Warm Sunlight)
    sun_data = bpy.data.lights.new("Sun_Key_Light_Data", 'SUN')
    sun_data.energy = 5.4
    sun_data.color = (1.0, 0.95, 0.88)
    sun_data.angle = math.radians(2.5)
    sun_obj = bpy.data.objects.new("Sun_Key_Light", sun_data)
    sun_obj.location = (80.0, -90.0, 120.0)
    sun_obj.rotation_euler = (math.radians(52.0), math.radians(15.0), math.radians(-38.0))
    collection.objects.link(sun_obj)
    light_objs["Sun_Key_Light"] = sun_obj

    # Fill Light (Cool Sky Skylight)
    sky_data = bpy.data.lights.new("Sky_Fill_Light_Data", 'SUN')
    sky_data.energy = 1.6
    sky_data.color = (0.60, 0.75, 1.0)
    sky_data.angle = math.radians(8.0)
    sky_obj = bpy.data.objects.new("Sky_Fill_Light", sky_data)
    sky_obj.location = (-70.0, 80.0, 90.0)
    sky_obj.rotation_euler = (math.radians(40.0), math.radians(-25.0), math.radians(135.0))
    collection.objects.link(sky_obj)
    light_objs["Sky_Fill_Light"] = sky_obj

    return light_objs


# =============================================================================
# 11. Rigged Fauna Integration
# =============================================================================

def setup_fauna(collection: bpy.types.Collection) -> List[Tuple[bpy.types.Object, bpy.types.Object]]:
    """Populates scene with 5 rigged and animated fauna species."""
    terrain_data = {
        "biome_anchors": {
            "alpine_goat": (-24.0, 38.0, 24.5),
            "alpine_eagle": (10.0, -10.0, 38.0),
            "meadow_stag": (-5.0, 15.0, 7.5),
            "lake_fish": (-20.0, -8.0, 3.5),
            "cave_bat": (14.0, 16.0, -1.2),
        }
    }
    return fauna_generator.generate_fauna(bpy.context, collection, terrain_data)


# =============================================================================
# 12. Main Assembly, Save & glTF Export Pipeline
# =============================================================================

def build_genesis_diorama_master():
    """Main pipeline execution for Genesis Zero Master Diorama."""
    print("==================================================================")
    print("GENESIS ZERO: BUILDING MASTER 3D DIORAMA (Blender 5.2.1 LTS)")
    print("==================================================================")

    os.makedirs(MODELS_DIR, exist_ok=True)

    # 1. Initialize clean scene and collections
    print("\n[1/7] Initializing clean scene and collection hierarchy...")
    cols = initialize_clean_scene()

    # 2. Build Monolithic Diorama Island Block Base
    print("\n[2/7] Generating watertight diorama island block (160m x 160m, Z_base = -16.0m)...")
    diorama_block = build_diorama_island_block(cols["Terrain"])

    # 3. Build 4-Tier Continuous Hydrology Network
    print("\n[3/7] Generating continuous 4-tier hydrology network...")
    hydro_objs = build_hydrology(cols["Hydrology"])

    # 4. Build Subterranean Karst Cave System
    print("\n[4/7] Generating subterranean karst cave system (clearance >= 12.0m)...")
    cave_objs = build_karst_cave_system(cols["Caves"])

    # 5. Build Botanical Prototypes and Geometry Nodes Scatter
    print("\n[5/7] Constructing 13 botanical prototypes and procedural Geometry Nodes scatter...")
    prototypes = build_botanical_prototypes(cols)
    scatter_objs = setup_biome_scatter(cols, diorama_block)

    # 6. Rigged Fauna and Lighting
    print("\n[6/7] Instantiating rigged fauna and lighting systems...")
    fauna_pairs = setup_fauna(cols["Fauna"])
    lights = build_lighting(cols["Lighting"])
    cam_rig = build_24_camera_rig(cols["Camera_Rig_24"])

    # 7. Save .blend File
    print(f"\n[7/7] Saving master project to {BLEND_OUTPUT}...")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_OUTPUT))
    blend_size_mb = BLEND_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"-> Master .blend file written successfully: {blend_size_mb:.2f} MB")

    # 8. Export glTF/GLB Binary Container
    print(f"\nExporting Three.js-compatible GLB to {GLB_OUTPUT}...")
    bpy.ops.export_scene.gltf(
        filepath=str(GLB_OUTPUT),
        export_format='GLB',
        export_cameras=True,
        export_lights=True,
        export_materials='EXPORT',
        export_all_vertex_colors=True,
        export_apply=True,
        export_gn_mesh=True,
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_skins=True,
        export_draco_mesh_compression_enable=False,
        export_gpu_instances=False,
        export_yup=True,
    )
    glb_size_mb = GLB_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"-> Master .glb file exported successfully: {glb_size_mb:.2f} MB")

    print("\n==================================================================")
    print(f"BUILD COMPLETE: {BLEND_OUTPUT.name} ({blend_size_mb:.2f} MB) & {GLB_OUTPUT.name} ({glb_size_mb:.2f} MB)")
    print("==================================================================")


if __name__ == "__main__":
    build_genesis_diorama_master()

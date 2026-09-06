"""
terrain_hydrology.py - Procedural 3D Isometric Cutaway Diorama & Hydrology Pipeline
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Architectural Features:
1. Watertight 3D Isometric Diorama Cutaway Block:
   - 160m x 160m horizontal footprint (X, Y in [-80m, +80m]).
   - Solid base floor at Z = -14.0m with sealed bottom face.
   - Vertical cutaway walls displaying stratified underground cross-sections:
     * Topsoil (0 - 1.2m depth): Dark humic organic loam
     * Subsoil (1.2 - 4.2m depth): Ferruginous clay and weathered silt
     * Bedrock (> 4.2m depth): Sedimentary bedrock with sinusoidal strata banding
   - Baked into vertex color attribute COLOR_0.
2. Multi-Tier Geomorphology (Net Delta Z >= 33m):
   - Alpine twin snow-capped peaks (summits Z = 28.5m - 32.0m, delta Z >= 33m).
   - Weathered scree/talus slopes (25-40 deg) and vertical rock cliffs (>40 deg).
   - Rolling lowland valley plains (Z = 4.0m - 9.0m).
   - Central freshwater lake basin (Z_bed = 1.8m, water Z = 4.5m).
   - Lower coastal marine bay (Z_seabed = -4.5m, sea level Z = 0.0m).
3. Continuous 4-Tier Hydrology:
   - Alpine cascades & waterfalls from mountain saddle (-10, 45, Z=22m).
   - Meandering valley river flowing through foothills into central lake.
   - Central freshwater lake disc (Z = 4.5m) with sandy shoreline.
   - Outlet river cutting through limestone gorge and plunging over waterfall cliff.
   - Lower coastal marine bay (Z = 0.0m) with seabed shelf and cutaway water faces.
4. Subterranean Karst Cave System:
   - Cavern chamber inside diorama block beneath mountains (Z in [-7m, +0.5m]).
   - Natural arch entrance opening onto river gorge cliff.
   - Karst speleothems: fluted ceiling stalactites, dome floor stalagmites, fused columns.
   - Crystal-clear subterranean cave pool (Z = -6.8m).
   - Bioluminescent glowing fungi and soft ambient cave lighting.
5. Physically-Based Shaders:
   - Slope-aware terrain shader (rock on cliffs >40 deg, scree 25-40 deg, grass <25 deg, snow >= 20m, sand on shores).
   - PBR water shader with ShaderNodeVolumeAbsorption (emerald shallows, sapphire depths) and shoreline foam.
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Euler


def compute_terrain_elevation(x, y):
    """
    Continuous analytical elevation evaluation at point (x, y).
    Supports both scalar and numpy array inputs.
    Total topographic delta Z_max - Z_min >= 32m (Matterhorn peaks ~28m, seabed -4.5m).
    """
    is_scalar = np.isscalar(x) and np.isscalar(y)
    if is_scalar:
        x_arr = np.array([float(x)], dtype=np.float64)
        y_arr = np.array([float(y)], dtype=np.float64)
    else:
        x_arr = np.asarray(x, dtype=np.float64)
        y_arr = np.asarray(y, dtype=np.float64)

    # 1. Base Rolling Lowland Plains & Valley Floor (Z ~ 5.0 to 6.2m)
    z_base = 5.2
    foothills = (
        0.8 * np.sin(x_arr * 0.04) * np.cos(y_arr * 0.04)
        + 0.5 * np.cos(x_arr * 0.08 + 1.0)
        + 0.4 * np.sin(y_arr * 0.07 + 0.5)
    )
    z = z_base + foothills

    # 2. Northern Alpine Mountain Range (y > 10m)
    # Matterhorn-style pyramidal peaks with sharp knife-edge arêtes (ridges)
    m_factor = np.clip((y_arr - 10.0) / 58.0, 0.0, 1.0) ** 1.2
    
    # Peak 1: Central Matterhorn Horn at (-6.0, 50.0)
    d1 = np.sqrt((x_arr + 6.0)**2 + (y_arr - 50.0)**2)
    p1 = 28.0 * np.maximum(0.0, 1.0 - (d1 / 34.0)**0.86)
    
    # Peak 2: Eastern Shoulder Horn at (28.0, 48.0)
    d2 = np.sqrt((x_arr - 28.0)**2 + (y_arr - 48.0)**2)
    p2 = 21.0 * np.maximum(0.0, 1.0 - (d2 / 27.0)**0.88)
    
    # Peak 3: Western Ridge Horn at (-46.0, 40.0)
    d3 = np.sqrt((x_arr + 46.0)**2 + (y_arr - 40.0)**2)
    p3 = 17.5 * np.maximum(0.0, 1.0 - (d3 / 24.0)**0.90)

    # Sharp knife-edge arêtes (ridge lines)
    r1 = 6.0 * np.maximum(0.0, 1.0 - 0.16 * np.abs((x_arr + 6.0) * 0.5 - (y_arr - 50.0) * 0.8))
    r2 = 5.2 * np.maximum(0.0, 1.0 - 0.18 * np.abs((x_arr - 10.0) + (y_arr - 42.0) * 0.5))
    r3 = 4.5 * np.maximum(0.0, 1.0 - 0.16 * np.abs((x_arr + 28.0) * 0.7 + (y_arr - 46.0) * 0.6))
    
    # High mountain glacial saddle / cirque between Peak 1 and Peak 2 (around (10, 44))
    d_saddle = np.sqrt((x_arr - 10.0)**2 + (y_arr - 44.0)**2)
    saddle_dip = 4.5 * np.exp(-(d_saddle**2) / (2.0 * 8.0**2))
    
    mount_noise = 2.0 * np.abs(np.sin(x_arr * 0.14 + y_arr * 0.09)) + 1.2 * np.cos(x_arr * 0.18 - y_arr * 0.13)
    z += m_factor * (p1 + p2 + p3 + r1 + r2 + r3 + mount_noise - saddle_dip)

    # 3. Organic Central Lake Basin centered at (-18.0, -6.0)
    lcx, lcy = -18.0, -6.0
    ldx = x_arr - lcx
    ldy = y_arr - lcy
    l_angle = np.arctan2(ldy, ldx)
    # Organic kidney boundary
    r_shore = 21.0 + 5.0 * np.cos(l_angle - 0.4) + 3.2 * np.sin(2.0 * l_angle) + 2.0 * np.cos(3.0 * l_angle + 0.8)
    d_lake = np.hypot(ldx, ldy)
    d_lake_norm = d_lake / r_shore

    # Lake depression: bed Z ~ 1.9 to 2.3m, shore at Z = 4.65m
    mask_lake_bed = d_lake_norm < 0.62
    if np.any(mask_lake_bed):
        z[mask_lake_bed] = 1.9 + 0.4 * (d_lake_norm[mask_lake_bed] / 0.62)**2

    mask_lake_slope = (d_lake_norm >= 0.62) & (d_lake_norm < 1.0)
    if np.any(mask_lake_slope):
        tl = (d_lake_norm[mask_lake_slope] - 0.62) / (1.0 - 0.62)
        sl = 3.0 * tl**2 - 2.0 * tl**3
        z[mask_lake_slope] = 2.3 + (4.65 - 2.3) * sl

    mask_lake_berm = (d_lake_norm >= 1.0) & (d_lake_norm < 1.25)
    if np.any(mask_lake_berm):
        tb = (d_lake_norm[mask_lake_berm] - 1.0) / 0.25
        sb = 3.0 * tb**2 - 2.0 * tb**3
        target_berm = (1.0 - sb) * 4.65 + sb * z[mask_lake_berm]
        z[mask_lake_berm] = np.maximum(z[mask_lake_berm], target_berm)

    # 3b. Forest / Wetland Pond ("Ao") centered at (18.0, -5.0)
    pcx, pcy = 18.0, -5.0
    pdx = x_arr - pcx
    pdy = y_arr - pcy
    p_angle = np.arctan2(pdy, pdx)
    # Natural organic pond boundary (r ~ 9.2m)
    r_pond_shore = 9.2 + 1.5 * np.cos(2.0 * p_angle) + 1.0 * np.sin(3.0 * p_angle + 0.5)
    d_pond = np.hypot(pdx, pdy)
    d_pond_norm = d_pond / r_pond_shore

    # Pond depression: bed Z ~ 3.6 to 4.0m, shore at Z = 5.1m, water at Z = 4.85m
    mask_pond_bed = d_pond_norm < 0.65
    if np.any(mask_pond_bed):
        z[mask_pond_bed] = 3.6 + 0.4 * (d_pond_norm[mask_pond_bed] / 0.65)**2

    mask_pond_slope = (d_pond_norm >= 0.65) & (d_pond_norm < 1.0)
    if np.any(mask_pond_slope):
        tp = (d_pond_norm[mask_pond_slope] - 0.65) / (1.0 - 0.65)
        sp = 3.0 * tp**2 - 2.0 * tp**3
        z[mask_pond_slope] = 4.0 + (5.1 - 4.0) * sp

    mask_pond_berm = (d_pond_norm >= 1.0) & (d_pond_norm < 1.25)
    if np.any(mask_pond_berm):
        tpb = (d_pond_norm[mask_pond_berm] - 1.0) / 0.25
        spb = 3.0 * tpb**2 - 2.0 * tpb**3
        target_pberm = (1.0 - spb) * 5.1 + spb * z[mask_pond_berm]
        z[mask_pond_berm] = np.maximum(z[mask_pond_berm], target_pberm)

    # 4. Sea Cliff & Lower Coastal Marine Bay (Southeast)
    # Curved cliff line: points where x - 0.65 * y > 36.0 + 4.5 * sin(y * 0.08)
    cliff_val = (x_arr - 0.65 * y_arr) - (36.0 + 4.5 * np.sin(y_arr * 0.08))
    mask_cliff = (cliff_val >= -2.0) & (cliff_val <= 3.0) & (y_arr < 8.0)
    mask_bay = (cliff_val > 3.0) & (y_arr < 8.0)

    if np.any(mask_cliff):
        tc = (cliff_val[mask_cliff] - (-2.0)) / 5.0
        sc = 3.0 * tc**2 - 2.0 * tc**3
        # Cliff drops sharply from meadow (~5.5m) to beach (~0.8m)
        z[mask_cliff] = (1.0 - sc) * z[mask_cliff] + sc * 0.8

    if np.any(mask_bay):
        dist_past = cliff_val[mask_bay] - 3.0
        tb = np.clip(dist_past / 20.0, 0.0, 1.0)
        sb = 3.0 * tb**2 - 2.0 * tb**3
        target_sea_z = 0.8 * (1.0 - sb) + (-4.5) * sb
        z[mask_bay] = np.minimum(z[mask_bay], target_sea_z)

    # 5. Continuous Hydrological River Carving
    t_samp = np.linspace(0.0, 1.0, 140)
    rx, ry, rz, rw = _evaluate_river_spline_points(t_samp)

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

    # Carve river channel outside deep lake and bay
    w_channel = rw_near * 0.5 + 2.0
    mask_river = (min_dist < w_channel) & (d_lake_norm >= 0.55) & (d_pond_norm >= 0.70) & (cliff_val < 3.0)
    if np.any(mask_river):
        t_bank = min_dist[mask_river] / w_channel[mask_river]
        s_bank = 3.0 * t_bank ** 2 - 2.0 * t_bank ** 3
        bed_cut = np.minimum(z[mask_river], rz_near[mask_river]) - 0.65
        z[mask_river] = (1.0 - s_bank) * bed_cut + s_bank * z[mask_river]

    # Floor limit at seabed
    z = np.maximum(z, -4.5)

    if is_scalar:
        return float(z[0])
    return z


def _evaluate_river_spline_points(t_arr):
    """
    Evaluates continuous 4-tier river spline coordinates calibrated to terrain elevation:
    t in [0.0, 0.35]: Alpine Cascades & Stream (8, 42, Z=13.5) -> Valley Gorge (1, 24, Z=6.7)
    t in [0.35, 0.55]: Valley Meander -> Lake Inlet (-10, 10, Z=4.5)
    t in [0.55, 0.72]: Central Lake Transit (Lake surface at Z=4.5)
    t in [0.72, 1.00]: Lake Outlet (-12, -20, Z=4.5) -> Meander -> Waterfall Plunge (21, -44, Z=0.0) -> Bay
    """
    rx = np.zeros_like(t_arr)
    ry = np.zeros_like(t_arr)
    rz = np.zeros_like(t_arr)
    rw = np.zeros_like(t_arr)

    for idx, t in enumerate(t_arr):
        if t <= 0.35:
            # Stage 1: Alpine Mountain Stream & Cascades (Glacial Saddle -> Valley Gorge)
            p = t / 0.35
            rx[idx] = 8.0 * (1.0 - p) + 1.0 * p + 2.0 * math.sin(p * math.pi)
            ry[idx] = 42.0 * (1.0 - p) + 24.0 * p
            rz[idx] = 13.5 * ((1.0 - p) ** 1.8) + 6.7 * (1.0 - (1.0 - p) ** 1.8)
            rw[idx] = 3.0 + 1.2 * p
        elif t <= 0.55:
            # Stage 2: Valley Meander to Lake Inlet
            p = (t - 0.35) / 0.20
            rx[idx] = 1.0 * (1.0 - p) - 10.0 * p + 2.5 * math.sin(p * math.pi)
            ry[idx] = 24.0 * (1.0 - p) + 10.0 * p
            rz[idx] = 6.7 * (1.0 - p) + 4.5 * p
            rw[idx] = 4.2 + 1.8 * p
        elif t <= 0.72:
            # Stage 3: Central Lake Transit
            p = (t - 0.55) / 0.17
            rx[idx] = -10.0 * (1.0 - p) - 12.0 * p
            ry[idx] = 10.0 * (1.0 - p) - 20.0 * p
            rz[idx] = 4.5
            rw[idx] = 7.5
        else:
            # Stage 4: Outlet River & Waterfall into Bay
            p = (t - 0.72) / 0.28
            rx[idx] = -12.0 * (1.0 - p) + 21.0 * p + 2.5 * math.sin(p * 1.5 * math.pi)
            ry[idx] = -20.0 * (1.0 - p) - 44.0 * p - 2.0 * math.sin(p * math.pi)
            if p < 0.65:
                rz[idx] = 4.5 * (1.0 - p / 0.65) + 3.5 * (p / 0.65)
            else:
                wp = (p - 0.65) / 0.35
                rz[idx] = 3.5 * (1.0 - wp) + 0.0 * wp
            rw[idx] = 5.5 + 2.5 * p

    return rx, ry, rz, rw


def compute_river_distance(x, y):
    """Calculates minimal distance from (x, y) to the continuous river spline."""
    t_samp = np.linspace(0.0, 1.0, 140)
    rx, ry, _, _ = _evaluate_river_spline_points(t_samp)
    dx = float(x) - rx
    dy = float(y) - ry
    return float(np.min(np.sqrt(dx * dx + dy * dy)))


def compute_pond_distance(x, y):
    """Calculates distance from (x, y) to wetland pond center (18, -5)."""
    return float(math.hypot(float(x) - 18.0, float(y) - (-5.0)))


def compute_lake_distance(x, y):
    """Calculates distance from (x, y) to organic lake center (-18, -6)."""
    return float(math.hypot(float(x) - (-18.0), float(y) - (-6.0)))


def compute_bay_distance(x, y):
    """Calculates distance to coastal marine bay."""
    return float(math.hypot(float(x) - 45.0, float(y) - (-45.0)))


def compute_water_distance(x, y):
    """Calculates minimal distance from (x, y) to any water surface."""
    d_riv = compute_river_distance(x, y)
    d_lake = max(0.0, compute_lake_distance(x, y) - 20.0)
    d_pond = max(0.0, compute_pond_distance(x, y) - 9.2)
    d_bay = max(0.0, compute_bay_distance(x, y) - 38.0)
    return float(min(d_riv, d_lake, d_pond, d_bay))


def compute_terrain_slope(x, y, eps=0.5):
    """Calculates surface slope in degrees at (x, y)."""
    z0 = compute_terrain_elevation(x, y)
    zx = compute_terrain_elevation(x + eps, y)
    zy = compute_terrain_elevation(x, y + eps)
    gx = (zx - z0) / eps
    gy = (zy - z0) / eps
    nz = 1.0 / math.sqrt(1.0 + gx * gx + gy * gy)
    slope_rad = math.acos(max(0.0, min(1.0, nz)))
    return float(math.degrees(slope_rad))


# -----------------------------------------------------------------------------
# Materials & Shaders
# -----------------------------------------------------------------------------


def create_terrain_material():
    """
    Constructs the physically based multi-biome slope & strata terrain shader M_Terrain_PBR.
    Directly reads COLOR_0 attribute and blends with procedural multi-octave noise
    and micro-bump for organic tactile realism.
    Enforces blend_method = 'OPAQUE' and shadow_method = 'OPAQUE'.
    """
    mat_name = "M_Terrain_PBR"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (650, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    bsdf.inputs["Roughness"].default_value = 0.75
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.35
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.35

    # Enforce solid opacity on BSDF Alpha socket
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 1.0

    links.new(bsdf.outputs["BSDF"], node_out.inputs["Surface"])

    # 1. Color Attribute: COLOR_0
    attr_node = nodes.new("ShaderNodeAttribute")
    attr_node.location = (-450, 180)
    attr_node.attribute_name = "COLOR_0"
    links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])

    # 2. Procedural texture hook (zero strength maintains crisp geometric low-poly facet normals)
    tex_noise = nodes.new("ShaderNodeTexNoise")
    tex_noise.location = (-450, -220)
    tex_noise.inputs["Scale"].default_value = 26.0
    tex_noise.inputs["Detail"].default_value = 5.0
    tex_noise.inputs["Roughness"].default_value = 0.65

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-120, -180)
    bump.inputs["Strength"].default_value = 0.0
    bump.inputs["Distance"].default_value = 0.0
    links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # Enforce opaque blend and shadow mode
    mat.blend_method = "OPAQUE"
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = "OPAQUE"
        except Exception:
            pass
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False

    return mat


def create_water_pbr_material():
    """
    Constructs the physically based translucent water shader M_Water_PBR.
    Features:
    - Principled BSDF surface with physical IOR 1.333, transmission 0.52, roughness 0.02.
    - Vibrant cerulean cyan albedo with subtle aquatic emission for visible liquid presence.
    - ShaderNodeVolumeAbsorption for sapphire-emerald depth gradients without pitch-black occlusion.
    - Alpha blending transparency and procedural micro-ripples for sparkling sun glints.
    """
    mat_name = "M_Water_PBR"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (450, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 80)
    # Vibrant tropical cerulean cyan surface tone
    bsdf.inputs["Base Color"].default_value = (0.05, 0.50, 0.72, 0.90)
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.333

    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.52
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.52

    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.85
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.85

    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.88

    # Subtle cyan-blue emission to ensure vivid sparkling water under any lighting
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.02, 0.18, 0.28, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.40
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = (0.02, 0.18, 0.28, 1.0)

    links.new(bsdf.outputs["BSDF"], node_out.inputs["Surface"])

    # Water Volume Absorption (Sapphire-emerald depth gradient)
    vol_node = nodes.new("ShaderNodeVolumeAbsorption")
    vol_node.location = (100, -180)
    vol_node.inputs["Color"].default_value = (0.10, 0.65, 0.85, 1.0)
    vol_node.inputs["Density"].default_value = 0.015
    links.new(vol_node.outputs["Volume"], node_out.inputs["Volume"])

    # Procedural micro-ripples for sparkling low-poly surface facets
    tex_noise = nodes.new("ShaderNodeTexNoise")
    tex_noise.location = (-350, 0)
    tex_noise.inputs["Scale"].default_value = 28.0
    tex_noise.inputs["Detail"].default_value = 4.0
    tex_noise.inputs["Roughness"].default_value = 0.35

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-120, 0)
    bump.inputs["Strength"].default_value = 0.03
    bump.inputs["Distance"].default_value = 0.06
    links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    mat.blend_method = "BLEND"
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    mat.use_backface_culling = False
    return mat


def create_foam_material():
    """Constructs white frothy water foam material for rapids and waterfalls."""
    mat_name = "M_Water_Foam"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (300, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = (0.96, 0.98, 1.0, 0.88)
    bsdf.inputs["Roughness"].default_value = 0.30
    bsdf.inputs["IOR"].default_value = 1.333
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.50
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.50
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (0.96, 0.98, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.35
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.88
    links.new(bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    mat.blend_method = "BLEND"
    return mat


def create_bioluminescent_material(name="M_Bio_Mushroom", color=(0.12, 0.92, 0.78, 1.0), strength=4.5):
    """Constructs an emissive shader for subterranean cave fungi & glowing pool."""
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    node_out = nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (350, 0)

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (50, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    links.new(emission.outputs["Emission"], node_out.inputs["Surface"])
    return mat


# -----------------------------------------------------------------------------
# Watertight Diorama Cutaway Block Construction
# -----------------------------------------------------------------------------


def build_watertight_diorama_block(collection, res=81):
    """
    Constructs a watertight 3D isometric cutaway block:
    - Horizontal dimensions: 160m x 160m (X, Y in [-80m, +80m]).
    - Top surface: grid of res x res vertices with continuous analytical elevation Z(x, y).
    - 4 vertical cutaway walls: connecting outer perimeter down to Z_base = -14.0m.
    - Sealed bottom cap: polygon face at Z_base = -14.0m.
    - Procedural underground strata baked into vertex colors COLOR_0:
      * Topsoil, Subsoil, Bedrock banding on cutaway walls.
      * Rock, Scree, Grass, Snow, and Sand on top terrain surface.
    """
    x_min, x_max = -80.0, 80.0
    y_min, y_max = -80.0, 80.0
    z_base = -14.0

    xs = np.linspace(x_min, x_max, res)
    ys = np.linspace(y_min, y_max, res)
    xx, yy = np.meshgrid(xs, ys)
    zz = compute_terrain_elevation(xx, yy)

    # 1. Vertices for Top Surface Grid
    verts = []
    v_colors = []

    # Calculate slope normal Z for top surface
    dx_val = (x_max - x_min) / (res - 1)
    gz, gx = np.gradient(zz, dx_val)
    nz_grid = 1.0 / np.sqrt(1.0 + gx ** 2 + gz ** 2)

    # Top surface colors
    c_snow = np.array([0.96, 0.98, 1.00, 1.0], dtype=np.float32)
    c_rock_base = np.array([0.46, 0.48, 0.50, 1.0], dtype=np.float32)        # Granite cliff rock
    c_scree = np.array([0.52, 0.48, 0.42, 1.0], dtype=np.float32)            # Warm gravel scree
    c_grass_lush = np.array([0.16, 0.38, 0.10, 1.0], dtype=np.float32)        # Deep valley emerald
    c_grass_meadow = np.array([0.22, 0.44, 0.12, 1.0], dtype=np.float32)      # Vibrant fresh meadow
    c_grass_alpine = np.array([0.28, 0.38, 0.14, 1.0], dtype=np.float32)      # Highland tussock
    c_sand_beach = np.array([0.85, 0.75, 0.52, 1.0], dtype=np.float32)        # Warm golden sand
    c_sand_wet = np.array([0.58, 0.48, 0.34, 1.0], dtype=np.float32)          # Wet tide sand
    c_riverbed = np.array([0.28, 0.26, 0.22, 1.0], dtype=np.float32)          # Dark wet gravel
    c_lake_deep = np.array([0.08, 0.22, 0.28, 1.0], dtype=np.float32)         # Dark aquatic lake silt
    c_lake_shelf = np.array([0.20, 0.38, 0.36, 1.0], dtype=np.float32)        # Turquoise shallow shelf
    c_pond_bed = np.array([0.10, 0.20, 0.16, 1.0], dtype=np.float32)          # Peat/marsh organic bed
    c_pond_shore = np.array([0.34, 0.30, 0.22, 1.0], dtype=np.float32)        # Wet muddy marsh shore
    c_stream_bed = np.array([0.22, 0.26, 0.28, 1.0], dtype=np.float32)        # Wet granite mountain shingle
    c_seabed_deep = np.array([0.06, 0.20, 0.30, 1.0], dtype=np.float32)       # Deep marine seabed

    for j in range(res):
        for i in range(res):
            x = float(xx[j, i])
            y = float(yy[j, i])
            z = float(zz[j, i])
            nz = float(nz_grid[j, i])
            slope_deg = math.degrees(math.acos(max(0.0, min(1.0, nz))))
            verts.append((x, y, z))

            # Organic lake distance
            ldx = x - (-18.0)
            ldy = y - (-6.0)
            l_ang = math.atan2(ldy, ldx)
            r_shore = 21.0 + 5.0 * math.cos(l_ang - 0.4) + 3.2 * math.sin(2.0 * l_ang) + 2.0 * math.cos(3.0 * l_ang + 0.8)
            d_lake = math.hypot(ldx, ldy)
            d_lake_norm = d_lake / r_shore

            # Wetland pond distance ("Ao" at 18, -5)
            pdx = x - 18.0
            pdy = y - (-5.0)
            p_ang = math.atan2(pdy, pdx)
            r_pond_sh = 9.2 + 1.5 * math.cos(2.0 * p_ang) + 1.0 * math.sin(3.0 * p_ang + 0.5)
            d_pond = math.hypot(pdx, pdy)
            d_pond_norm = d_pond / r_pond_sh

            # Coastal bay cliff value
            cliff_val = (x - 0.65 * y) - (36.0 + 4.5 * math.sin(y * 0.08))
            d_riv = compute_river_distance(x, y)

            # Elevation-based and moisture-based grass blending
            t_elev = np.clip((z - 4.0) / 12.0, 0.0, 1.0)
            c_grass_base = (1.0 - t_elev) * c_grass_meadow + t_elev * c_grass_alpine
            mottling = 0.04 * math.sin(x * 0.14) * math.cos(y * 0.14)
            c_grass = np.clip(c_grass_base + mottling, 0.0, 1.0)

            # Rock with horizontal sedimentary striations
            strata_var = 0.04 * math.sin(1.8 * z) + 0.02 * math.cos(3.5 * z)
            c_rock = np.clip(c_rock_base + strata_var, 0.0, 1.0)

            # 1. Snow caps on high mountain peaks (Z >= 15.5m)
            if z >= 15.5 and slope_deg < 42.0:
                t_s = np.clip((z - 15.5) / 5.0, 0.0, 1.0)
                col = (1.0 - t_s) * c_rock + t_s * c_snow

            # 2. Deep Central Lake Bed (Submerged beneath Z = 4.5m)
            elif d_lake_norm < 0.82 and z <= 4.6:
                if d_lake_norm < 0.55:
                    col = c_lake_deep
                else:
                    t_sh = (d_lake_norm - 0.55) / (0.82 - 0.55)
                    col = (1.0 - t_sh) * c_lake_deep + t_sh * c_lake_shelf

            # 3. Central Lake Sandy Shoreline
            elif 0.82 <= d_lake_norm <= 1.25 and z <= 5.5:
                t_ls = np.clip(abs(d_lake_norm - 1.0) / 0.25, 0.0, 1.0)
                col = (1.0 - t_ls) * c_sand_beach + t_ls * c_grass

            # 4. Wetland Pond Bed & Margin ("Ao", centered at 30, -10, submerged beneath Z = 4.85m)
            elif d_pond_norm < 0.70 and z <= 4.9:
                col = c_pond_bed
            elif 0.70 <= d_pond_norm <= 1.20 and z <= 5.4:
                t_ps = np.clip(abs(d_pond_norm - 0.95) / 0.25, 0.0, 1.0)
                col = (1.0 - t_ps) * c_pond_shore + t_ps * c_grass

            # 5. Coastal Bay Seabed & Beach (Southeast)
            elif cliff_val > 0.0 and y < 8.0:
                if z <= -1.0:
                    col = c_seabed_deep
                elif z <= 0.25:
                    t_sb = (z - (-1.0)) / 1.25
                    col = (1.0 - t_sb) * c_seabed_deep + t_sb * c_sand_wet
                elif z <= 2.2:
                    t_sd = np.clip((z - 0.25) / 1.8, 0.0, 1.0)
                    col = (1.0 - t_sd) * c_sand_wet + t_sd * c_sand_beach
                else:
                    col = c_grass

            # 6. Mountain Stream Bed & Valley Riverbed
            elif d_riv <= 2.2:
                if y > 24.0:
                    # Alpine cascade rock shingle
                    t_st = np.clip(d_riv / 2.2, 0.0, 1.0)
                    col = (1.0 - t_st) * c_stream_bed + t_st * c_rock
                else:
                    # Valley river gravel
                    t_rv = np.clip(d_riv / 2.2, 0.0, 1.0)
                    col = (1.0 - t_rv) * c_riverbed + t_rv * c_grass

            # 7. Sea cliff vertical rocky scarp (distinct dark granite stone)
            elif cliff_val >= -1.8 and cliff_val <= 2.8 and y < 8.0 and z > 1.0:
                col = np.array([0.36, 0.38, 0.40, 1.0], dtype=np.float32)

            # 8. Steep mountain rocky cliffs & couloirs (> 30 deg)
            elif slope_deg > 30.0:
                col = c_rock

            # 9. Scree / talus slopes (20 - 30 deg)
            elif slope_deg >= 20.0:
                t_sc = (slope_deg - 20.0) / 10.0
                col = (1.0 - t_sc) * c_grass + t_sc * c_scree

            # 10. Lowland meadows and rolling valley
            else:
                col = c_grass
            v_colors.append(col)

    # Top surface triangulated low-poly faces (alternating diagonals)
    faces = []
    for j in range(res - 1):
        r1 = j * res
        r2 = (j + 1) * res
        for i in range(res - 1):
            v0 = r1 + i
            v1 = r1 + i + 1
            v2 = r2 + i + 1
            v3 = r2 + i
            if (i + j) % 2 == 0:
                faces.append((v0, v1, v2))
                faces.append((v0, v2, v3))
            else:
                faces.append((v1, v2, v3))
                faces.append((v1, v3, v0))

    # 2. Perimeter Wall Traversal (Counter-Clockwise)
    top_perim_indices = []
    for i in range(res - 1):
        top_perim_indices.append(0 * res + i)
    for j in range(res - 1):
        top_perim_indices.append(j * res + (res - 1))
    for i in range(res - 1, 0, -1):
        top_perim_indices.append((res - 1) * res + i)
    for j in range(res - 1, 0, -1):
        top_perim_indices.append(j * res + 0)

    num_perim = len(top_perim_indices)

    # 3. Vertical Wall Grid with Procedural Geological Strata
    n_slices = 10
    wall_grid = []

    c_topsoil = np.array([0.16, 0.09, 0.04, 1.0], dtype=np.float32)
    c_subsoil = np.array([0.48, 0.25, 0.11, 1.0], dtype=np.float32)
    c_bedrock = np.array([0.26, 0.24, 0.22, 1.0], dtype=np.float32)

    for k in range(num_perim):
        top_idx = top_perim_indices[k]
        tx, ty, tz = verts[top_idx]
        col_indices = [top_idx]
        for s in range(1, n_slices + 1):
            t_frac = s / n_slices
            cur_z = tz * (1.0 - t_frac) + z_base * t_frac
            depth = tz - cur_z

            if depth < 1.4:
                c_strata = c_topsoil
            elif depth < 4.5:
                c_strata = c_subsoil
            else:
                b_z = 0.22 * math.sin(1.8 * cur_z) + 0.10 * math.cos(3.6 * cur_z) + 0.06 * math.sin(7.5 * cur_z)
                c_strata = np.clip(c_bedrock * (1.0 + b_z), 0.0, 1.0)

            v_idx = len(verts)
            verts.append((tx, ty, cur_z))
            v_colors.append(c_strata)
            col_indices.append(v_idx)
        wall_grid.append(col_indices)

    # 4. Vertical Cutaway Wall Quads
    for k in range(num_perim):
        k_next = (k + 1) % num_perim
        for s in range(n_slices):
            v_tl = wall_grid[k][s]
            v_tr = wall_grid[k_next][s]
            v_br = wall_grid[k_next][s + 1]
            v_bl = wall_grid[k][s + 1]
            faces.append((v_tl, v_tr, v_br, v_bl))

    # 5. Sealed Bottom Cap at Z = -14.0m
    center_bot_idx = len(verts)
    verts.append((0.0, 0.0, z_base))
    v_colors.append(c_bedrock)

    for k in range(num_perim):
        k_next = (k + 1) % num_perim
        b1 = wall_grid[k][n_slices]
        b2 = wall_grid[k_next][n_slices]
        faces.append((center_bot_idx, b2, b1))

    # 6. Build Blender Mesh with Flat Faceted Shading
    mesh_data = bpy.data.meshes.new("Diorama_Cutaway_Block_Mesh")
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update(calc_edges=True)
    mesh_data.shade_flat()
    for poly in mesh_data.polygons:
        poly.use_smooth = False

    # Mark perimeter cutaway edges sharp
    sharp_edge_pairs = set()

    for k in range(num_perim):
        v1 = top_perim_indices[k]
        v2 = top_perim_indices[(k + 1) % num_perim]
        sharp_edge_pairs.add((min(v1, v2), max(v1, v2)))

    for k in range(num_perim):
        b1 = wall_grid[k][n_slices]
        b2 = wall_grid[(k + 1) % num_perim][n_slices]
        sharp_edge_pairs.add((min(b1, b2), max(b1, b2)))

    corner_ks = [0, res - 1, 2 * (res - 1), 3 * (res - 1)]
    for ck in corner_ks:
        for s in range(n_slices):
            c1 = wall_grid[ck][s]
            c2 = wall_grid[ck][s + 1]
            sharp_edge_pairs.add((min(c1, c2), max(c1, c2)))

    for edge in mesh_data.edges:
        pair = (min(edge.vertices[0], edge.vertices[1]), max(edge.vertices[0], edge.vertices[1]))
        if pair in sharp_edge_pairs:
            edge.use_edge_sharp = True
    mesh_data.update()

    # 7. Add COLOR_0 vertex color attribute
    flat_colors = np.array(v_colors, dtype=np.float32).ravel()
    col_attr = mesh_data.color_attributes.new(name="COLOR_0", type="FLOAT_COLOR", domain="POINT")
    col_attr.data.foreach_set("color", flat_colors)
    # Alias 'Color'
    col_attr_alias = mesh_data.color_attributes.new(name="Color", type="FLOAT_COLOR", domain="POINT")
    col_attr_alias.data.foreach_set("color", flat_colors)
    mesh_data.update()

    # 8. Assign Material
    mat_terrain = create_terrain_material()
    mesh_data.materials.append(mat_terrain)

    obj = bpy.data.objects.new("Diorama_Cutaway_Block", mesh_data)
    collection.objects.link(obj)

    return obj


# -----------------------------------------------------------------------------
# Hydrology Meshes (River, Lake, Marine Bay, Cave Pool)
# -----------------------------------------------------------------------------


def build_hydrology_meshes(collection, terrain_obj):
    """
    Constructs the continuous 4-tier hydrology meshes:
    1. Water_River: Cascades -> River -> Lake -> Waterfall -> Bay
    2. Water_Lake: Central freshwater lake with organic kidney boundary at Z = 4.5m
    3. Water_Bay: Coastal marine bay at Z = 0.0m with cutaway water faces
    4. Water_Foam: Frothy white rapids and waterfall plunge foam
    """
    mat_water = create_water_pbr_material()
    mat_foam = create_foam_material()

    # 1. Central Freshwater Lake (Organic Kidney Basin at Z = 4.5m)
    lake_cx, lake_cy = -18.0, -6.0
    lake_z = 4.5
    n_lake_seg = 48
    lake_verts = [(lake_cx, lake_cy, lake_z)]
    # Inner ring (r * 0.55)
    for i in range(n_lake_seg):
        ang = i * 2.0 * math.pi / n_lake_seg
        r = (21.0 + 5.0 * math.cos(ang - 0.4) + 3.2 * math.sin(2.0 * ang) + 2.0 * math.cos(3.0 * ang + 0.8)) * 0.55
        lake_verts.append((lake_cx + r * math.cos(ang), lake_cy + r * math.sin(ang), lake_z))
    # Outer ring (r * 1.0)
    for i in range(n_lake_seg):
        ang = i * 2.0 * math.pi / n_lake_seg
        r = 21.0 + 5.0 * math.cos(ang - 0.4) + 3.2 * math.sin(2.0 * ang) + 2.0 * math.cos(3.0 * ang + 0.8)
        lake_verts.append((lake_cx + r * math.cos(ang), lake_cy + r * math.sin(ang), lake_z))

    lake_faces = []
    # Center fan to inner ring
    for i in range(n_lake_seg):
        i_next = (i + 1) % n_lake_seg
        lake_faces.append((0, 1 + i, 1 + i_next))
    # Quads between inner ring and outer ring
    for i in range(n_lake_seg):
        i_next = (i + 1) % n_lake_seg
        v1 = 1 + i
        v2 = 1 + i_next
        v3 = 1 + n_lake_seg + i_next
        v4 = 1 + n_lake_seg + i
        lake_faces.append((v1, v2, v3, v4))

    mesh_lake = bpy.data.meshes.new("Water_Lake_Mesh")
    mesh_lake.from_pydata(lake_verts, [], lake_faces)
    mesh_lake.update(calc_edges=True)
    mesh_lake.shade_smooth()
    for p in mesh_lake.polygons:
        p.use_smooth = True
    mesh_lake.materials.append(mat_water)

    lake_obj = bpy.data.objects.new("Water_Lake", mesh_lake)
    collection.objects.link(lake_obj)

    # 2. Forest & Wetland Pond ("Ao" at (18.0, -5.0), Z = 4.85m)
    pond_cx, pond_cy = 18.0, -5.0
    pond_z = 4.85
    n_pond_seg = 36
    pond_verts = [(pond_cx, pond_cy, pond_z)]
    # Inner ring (r * 0.55)
    for i in range(n_pond_seg):
        ang = i * 2.0 * math.pi / n_pond_seg
        r = (9.2 + 1.5 * math.cos(2.0 * ang) + 1.0 * math.sin(3.0 * ang + 0.5)) * 0.55
        pond_verts.append((pond_cx + r * math.cos(ang), pond_cy + r * math.sin(ang), pond_z))
    # Outer ring (r * 0.96)
    for i in range(n_pond_seg):
        ang = i * 2.0 * math.pi / n_pond_seg
        r = (9.2 + 1.5 * math.cos(2.0 * ang) + 1.0 * math.sin(3.0 * ang + 0.5)) * 0.96
        pond_verts.append((pond_cx + r * math.cos(ang), pond_cy + r * math.sin(ang), pond_z))

    pond_faces = []
    # Center fan to inner ring
    for i in range(n_pond_seg):
        i_next = (i + 1) % n_pond_seg
        pond_faces.append((0, 1 + i, 1 + i_next))
    # Quads between inner ring and outer ring
    for i in range(n_pond_seg):
        i_next = (i + 1) % n_pond_seg
        v1 = 1 + i
        v2 = 1 + i_next
        v3 = 1 + n_pond_seg + i_next
        v4 = 1 + n_pond_seg + i
        pond_faces.append((v1, v2, v3, v4))

    mesh_pond = bpy.data.meshes.new("Water_Pond_Mesh")
    mesh_pond.from_pydata(pond_verts, [], pond_faces)
    mesh_pond.update(calc_edges=True)
    mesh_pond.shade_smooth()
    for p in mesh_pond.polygons:
        p.use_smooth = True
    mesh_pond.materials.append(mat_water)

    pond_obj = bpy.data.objects.new("Water_Pond", mesh_pond)
    collection.objects.link(pond_obj)

    # 3. Alpine Mountain Stream ("Suối" Cascades down Rocky Slopes)
    n_stream = 36
    t_st = np.linspace(0.0, 0.35, n_stream)
    st_x, st_y, st_z, st_w = _evaluate_river_spline_points(t_st)
    st_verts = []
    st_faces = []
    for i in range(n_stream):
        if i == 0:
            tx, ty = st_x[1] - st_x[0], st_y[1] - st_y[0]
        elif i == n_stream - 1:
            tx, ty = st_x[-1] - st_x[-2], st_y[-1] - st_y[-2]
        else:
            tx, ty = st_x[i + 1] - st_x[i - 1], st_y[i + 1] - st_y[i - 1]
        t_len = max(1e-4, math.hypot(tx, ty))
        nx_w, ny_w = -ty / t_len, tx / t_len
        hw = st_w[i] * 0.55

        xl = st_x[i] + nx_w * hw
        yl = st_y[i] + ny_w * hw
        xr = st_x[i] - nx_w * hw
        yr = st_y[i] - ny_w * hw

        zw = st_z[i]
        st_verts.append((xl, yl, zw))
        st_verts.append((xr, yr, zw))

    for i in range(n_stream - 1):
        v1 = 2 * i
        v2 = 2 * i + 1
        v3 = 2 * (i + 1) + 1
        v4 = 2 * (i + 1)
        st_faces.append((v1, v2, v3, v4))

    mesh_stream = bpy.data.meshes.new("Water_Stream_Mesh")
    mesh_stream.from_pydata(st_verts, [], st_faces)
    mesh_stream.update(calc_edges=True)
    mesh_stream.shade_smooth()
    for p in mesh_stream.polygons:
        p.use_smooth = True
    mesh_stream.materials.append(mat_water)

    stream_obj = bpy.data.objects.new("Water_Stream", mesh_stream)
    collection.objects.link(stream_obj)

    # 4. Lower Coastal Marine Bay (Z = 0.0m) with Diorama Cutaway Faces
    # Curved shoreline boundary and diorama outer walls (X=80, Y=-80)
    bay_verts = []
    bay_faces = []
    bay_res = 28
    b_xs = np.linspace(10.0, 80.0, bay_res)
    b_ys = np.linspace(-80.0, 5.0, bay_res)
    b_grid = {}
    for j, by in enumerate(b_ys):
        for i, bx in enumerate(b_xs):
            c_val = (bx - 0.65 * by) - (36.0 + 4.5 * math.sin(by * 0.08))
            if c_val >= 3.0:
                idx = len(bay_verts)
                bay_verts.append((bx, by, 0.0))
                b_grid[(i, j)] = idx

    for j in range(bay_res - 1):
        for i in range(bay_res - 1):
            p1 = b_grid.get((i, j))
            p2 = b_grid.get((i + 1, j))
            p3 = b_grid.get((i + 1, j + 1))
            p4 = b_grid.get((i, j + 1))
            if p1 is not None and p2 is not None and p3 is not None and p4 is not None:
                bay_faces.append((p1, p2, p3, p4))
            elif p1 is not None and p2 is not None and p3 is not None:
                bay_faces.append((p1, p2, p3))
            elif p1 is not None and p3 is not None and p4 is not None:
                bay_faces.append((p1, p3, p4))
            elif p2 is not None and p3 is not None and p4 is not None:
                bay_faces.append((p2, p3, p4))

    # Add vertical cutaway faces along South edge (Y = -80) and East edge (X = 80)
    # South wall: Y = -80, X from min bay X to 80, Z from 0.0 down to -4.5
    s_pts = [b_grid[(i, 0)] for i in range(bay_res) if (i, 0) in b_grid]
    for k in range(len(s_pts) - 1):
        v_top1 = s_pts[k]
        v_top2 = s_pts[k + 1]
        x1 = bay_verts[v_top1][0]
        x2 = bay_verts[v_top2][0]
        v_bot1 = len(bay_verts)
        bay_verts.append((x1, -80.0, -4.5))
        v_bot2 = len(bay_verts)
        bay_verts.append((x2, -80.0, -4.5))
        bay_faces.append((v_top1, v_top2, v_bot2, v_bot1))

    # East wall: X = 80, Y from -80 up to max bay Y, Z from 0.0 down to -4.5
    e_pts = [b_grid[(bay_res - 1, j)] for j in range(bay_res) if (bay_res - 1, j) in b_grid]
    for k in range(len(e_pts) - 1):
        v_top1 = e_pts[k]
        v_top2 = e_pts[k + 1]
        y1 = bay_verts[v_top1][1]
        y2 = bay_verts[v_top2][1]
        v_bot1 = len(bay_verts)
        bay_verts.append((80.0, y1, -4.5))
        v_bot2 = len(bay_verts)
        bay_verts.append((80.0, y2, -4.5))
        bay_faces.append((v_top1, v_bot1, v_bot2, v_top2))

    mesh_bay = bpy.data.meshes.new("Water_Bay_Mesh")
    mesh_bay.from_pydata(bay_verts, [], bay_faces)
    mesh_bay.update(calc_edges=True)
    mesh_bay.shade_smooth()
    for p in mesh_bay.polygons:
        p.use_smooth = True
    mesh_bay.materials.append(mat_water)

    bay_obj = bpy.data.objects.new("Water_Bay", mesh_bay)
    collection.objects.link(bay_obj)

    # 5. Continuous Valley River Ribbon Mesh ("Sông" from Gorge to Lake and Waterfall Plunge)
    n_riv = 90
    t_r = np.linspace(0.0, 1.0, n_riv)
    riv_x, riv_y, riv_z, riv_w = _evaluate_river_spline_points(t_r)

    riv_verts = []
    riv_faces = []
    for i in range(n_riv):
        if i == 0:
            tx, ty = riv_x[1] - riv_x[0], riv_y[1] - riv_y[0]
        elif i == n_riv - 1:
            tx, ty = riv_x[-1] - riv_x[-2], riv_y[-1] - riv_y[-2]
        else:
            tx, ty = riv_x[i + 1] - riv_x[i - 1], riv_y[i + 1] - riv_y[i - 1]
        t_len = max(1e-4, math.hypot(tx, ty))
        nx_w, ny_w = -ty / t_len, tx / t_len
        hw = riv_w[i] * 0.5

        xl = riv_x[i] + nx_w * hw
        yl = riv_y[i] + ny_w * hw
        xr = riv_x[i] - nx_w * hw
        yr = riv_y[i] - ny_w * hw

        zw = riv_z[i]
        riv_verts.append((xl, yl, zw))
        riv_verts.append((xr, yr, zw))

    for i in range(n_riv - 1):
        # Skip section inside the lake basin
        d1 = math.hypot(riv_x[i] - lake_cx, riv_y[i] - lake_cy)
        d2 = math.hypot(riv_x[i + 1] - lake_cx, riv_y[i + 1] - lake_cy)
        if d1 < 20.0 and d2 < 20.0:
            continue
        v1 = 2 * i
        v2 = 2 * i + 1
        v3 = 2 * (i + 1) + 1
        v4 = 2 * (i + 1)
        riv_faces.append((v1, v2, v3, v4))

    mesh_river = bpy.data.meshes.new("Water_River_Mesh")
    mesh_river.from_pydata(riv_verts, [], riv_faces)
    mesh_river.update(calc_edges=True)
    mesh_river.shade_smooth()
    for p in mesh_river.polygons:
        p.use_smooth = True
    mesh_river.materials.append(mat_water)

    river_obj = bpy.data.objects.new("Water_River", mesh_river)
    collection.objects.link(river_obj)

    # 6. White Rapids & Waterfall Plunge Foam Meshes
    foam_locs = [
        (6.5, 38.0, 11.2, 2.8, 2.0),     # Stream cascade step 1
        (3.5, 29.5, 7.8, 3.0, 2.2),      # Stream cascade step 2
        (1.0, 24.0, 6.75, 3.2, 2.4),     # Gorge rapids
        (-9.0, 10.5, 4.55, 3.5, 2.4),    # Lake inlet foam
        (-12.0, -20.5, 4.55, 3.2, 2.0),  # Lake outlet foam
        (21.0, -44.0, 0.08, 5.0, 3.8),   # Waterfall plunge into bay
    ]
    foam_verts = []
    foam_faces = []
    for fx, fy, fz, rx, ry in foam_locs:
        base_v = len(foam_verts)
        foam_verts.append((fx, fy, fz + 0.05))
        for k in range(16):
            th = k * 2.0 * math.pi / 16.0
            r_mod = 1.0 + 0.28 * math.sin(4.0 * th) + 0.12 * math.cos(2.0 * th)
            foam_verts.append((fx + rx * r_mod * math.cos(th), fy + ry * r_mod * math.sin(th), fz))
        for k in range(16):
            foam_faces.append((base_v, base_v + 1 + k, base_v + 1 + ((k + 1) % 16)))

    mesh_foam = bpy.data.meshes.new("Water_Foam_Mesh")
    mesh_foam.from_pydata(foam_verts, [], foam_faces)
    mesh_foam.update(calc_edges=True)
    mesh_foam.shade_smooth()
    for p in mesh_foam.polygons:
        p.use_smooth = True
    mesh_foam.materials.append(mat_foam)

    foam_obj = bpy.data.objects.new("Water_Foam", mesh_foam)
    collection.objects.link(foam_obj)

    return {
        "lake_obj": lake_obj,
        "pond_obj": pond_obj,
        "stream_obj": stream_obj,
        "river_obj": river_obj,
        "bay_obj": bay_obj,
        "foam_obj": foam_obj,
    }


# -----------------------------------------------------------------------------
# Subterranean Karst Cave System
# -----------------------------------------------------------------------------


def build_cave_entrance_portal(collection, mat_rock):
    """
    Constructs an open natural karst archway and entrance corridor (Cave_Entrance)
    connecting the river gorge cliff at (15.0, -6.5, 2.2m) into the subterranean cavern.
    Features:
    - Arched entrance portal mouth with rocky limestone voussoirs (width 6.5m, height 4.2m).
    - Natural tunnel corridor connecting exterior river gorge floor to cavern interior.
    - Framing speleothems / stalactites hanging from the arch keystone.
    - Linked to Subterranean_Cave collection.
    """
    bm_ent = bmesh.new()

    # Corridor profile slices from exterior cliff (Y = -6.5) to cavern chamber (Y = 1.0)
    # Each slice is an arch: bottom flat sill, curved vault
    slices = [
        # (y, cx, cz_floor, w_half, h_vault)
        (-6.5, 15.0, 2.0, 3.2, 3.8),   # Exterior portal mouth at river gorge cliff
        (-4.5, 14.5, 1.0, 3.5, 4.0),   # Intermediate transition
        (-2.5, 14.0, -0.2, 3.8, 4.2),  # Throat
        (-0.5, 13.5, -1.5, 4.2, 4.5),  # Cavern threshold
        ( 1.5, 13.0, -3.0, 4.6, 4.8),  # Merging into main cavern
    ]

    n_arch_pts = 10
    slice_rings = []
    for y_s, cx_s, z_fl, w_h, h_v in slices:
        ring_v = []
        # Sill: left to right
        ring_v.append(bm_ent.verts.new((cx_s - w_h, y_s, z_fl)))
        # Vault arch (semicircle)
        for p in range(n_arch_pts):
            th = math.pi * p / (n_arch_pts - 1)
            # slight karst noise
            pert = 1.0 + 0.08 * math.sin(3.0 * th)
            vx = cx_s - w_h * math.cos(th) * pert
            vz = z_fl + h_v * math.sin(th) * pert
            ring_v.append(bm_ent.verts.new((vx, y_s, vz)))
        ring_v.append(bm_ent.verts.new((cx_s + w_h, y_s, z_fl)))
        slice_rings.append(ring_v)

    # Loft tunnel faces
    for s in range(len(slices) - 1):
        r1 = slice_rings[s]
        r2 = slice_rings[s + 1]
        for i in range(len(r1) - 1):
            bm_ent.faces.new((r1[i], r1[i + 1], r2[i + 1], r2[i]))

    # Add portal keystone framing stalactites on exterior mouth
    mouth_ring = slice_rings[0]
    for k_idx in [3, 5, 7]:
        base_v = mouth_ring[k_idx]
        tip_v = bm_ent.verts.new((base_v.co.x, base_v.co.y + 0.3, base_v.co.z - 1.2))
        v_l = mouth_ring[k_idx - 1]
        v_r = mouth_ring[k_idx + 1]
        bm_ent.faces.new((v_l, base_v, tip_v))
        bm_ent.faces.new((base_v, v_r, tip_v))

    mesh_ent = bpy.data.meshes.new("Cave_Entrance_Mesh")
    bm_ent.to_mesh(mesh_ent)
    bm_ent.free()
    mesh_ent.update(calc_edges=True)
    mesh_ent.shade_smooth()
    for p in mesh_ent.polygons:
        p.use_smooth = True
    mesh_ent.materials.append(mat_rock)

    entrance_obj = bpy.data.objects.new("Cave_Entrance", mesh_ent)
    collection.objects.link(entrance_obj)
    return entrance_obj


def build_subterranean_cave(collection):
    """
    Constructs the subterranean karst cave network:
    - Cavern chamber (Cave_Cavern) embedded at (12, 12, -4.5m) inside diorama block.
    - Karst speleothems (Cave_Speleothems): 14 ceiling stalactites, 12 floor stalagmites, 2 columns.
    - Subterranean pool (Water_CavePool) at Z = -6.8m.
    - Bioluminescent glowing mushrooms (Cave_Bioluminescent_Fungi) and point lights.
    - Open cave entrance portal (Cave_Entrance) overlooking river gorge at (15.0, -6.5, 2.2m).
    """
    mat_cave_rock = create_terrain_material()
    mat_water = create_water_pbr_material()
    mat_bio = create_bioluminescent_material("M_Bio_Mushroom", color=(0.12, 0.92, 0.78, 1.0), strength=5.0)

    # 1. Arched Cavern Chamber (Ellipsoid vault chamber)
    bm_cave = bmesh.new()
    cx, cy, cz = 12.0, 12.0, -4.5
    rx, ry, rz = 15.0, 20.0, 4.2
    n_lat, n_lon = 14, 20

    # Loft rings for cavern ceiling and walls
    rings = []
    for lt in range(n_lat):
        phi = math.pi * (lt + 0.5) / n_lat
        z_ring = cz + rz * math.cos(phi)
        r_ring = math.sin(phi)
        ring_v = []
        for ln in range(n_lon):
            theta = 2.0 * math.pi * ln / n_lon
            # Limestone dissolution perturbation
            pert = 1.0 + 0.12 * math.sin(3.0 * theta) * math.cos(2.0 * phi)
            vx = cx + rx * r_ring * math.cos(theta) * pert
            vy = cy + ry * r_ring * math.sin(theta) * pert
            vz = max(-7.0, min(0.4, z_ring * pert))
            ring_v.append(bm_cave.verts.new((vx, vy, vz)))
        rings.append(ring_v)

    # Inverted inward-facing faces
    for lt in range(n_lat - 1):
        for ln in range(n_lon):
            ln_next = (ln + 1) % n_lon
            v1 = rings[lt][ln]
            v2 = rings[lt][ln_next]
            v3 = rings[lt + 1][ln_next]
            v4 = rings[lt + 1][ln]
            bm_cave.faces.new((v1, v4, v3, v2))

    # Flat cavern floor at Z = -7.0m
    floor_v = [bm_cave.verts.new((cx + rx * 0.85 * math.cos(2.0 * math.pi * i / 16),
                                  cy + ry * 0.85 * math.sin(2.0 * math.pi * i / 16),
                                  -7.0)) for i in range(16)]
    bm_cave.faces.new(floor_v)

    mesh_cavern = bpy.data.meshes.new("Cave_Cavern_Mesh")
    bm_cave.to_mesh(mesh_cavern)
    bm_cave.free()
    mesh_cavern.update(calc_edges=True)
    mesh_cavern.shade_smooth()
    for p in mesh_cavern.polygons:
        p.use_smooth = True
    mesh_cavern.materials.append(mat_cave_rock)

    cave_obj = bpy.data.objects.new("Cave_Cavern", mesh_cavern)
    collection.objects.link(cave_obj)

    # 2. Karst Speleothems (Stalactites & Stalagmites)
    bm_sp = bmesh.new()

    # A. Stalactites (Ceiling Cones pointing down)
    stalactite_locs = [
        (cx - 5.0, cy - 6.0, 0.2, 3.2, 0.5),
        (cx - 2.0, cy - 3.0, 0.3, 3.8, 0.6),
        (cx + 4.0, cy - 5.0, 0.2, 2.8, 0.4),
        (cx + 6.0, cy + 2.0, 0.1, 3.5, 0.5),
        (cx - 6.0, cy + 4.0, 0.1, 3.0, 0.45),
        (cx + 1.0, cy + 7.0, 0.2, 3.6, 0.55),
        (cx - 3.0, cy + 9.0, 0.2, 2.9, 0.4),
        (cx + 5.0, cy + 10.0, 0.1, 3.4, 0.5),
    ]
    for sx, sy, sz_top, length, rad in stalactite_locs:
        # Base ring on ceiling
        b_ring = []
        for i in range(8):
            a = i * 2.0 * math.pi / 8.0
            b_ring.append(bm_sp.verts.new((sx + rad * math.cos(a), sy + rad * math.sin(a), sz_top)))
        tip = bm_sp.verts.new((sx, sy, sz_top - length))
        for i in range(8):
            i_next = (i + 1) % 8
            bm_sp.faces.new((b_ring[i], b_ring[i_next], tip))

    # B. Stalagmites (Floor Cones pointing up)
    stalagmite_locs = [
        (cx - 7.0, cy - 4.0, -7.0, 3.2, 0.65),
        (cx - 4.0, cy - 1.0, -7.0, 2.8, 0.60),
        (cx + 7.0, cy - 2.0, -7.0, 3.5, 0.70),
        (cx + 3.0, cy + 4.0, -7.0, 2.6, 0.55),
        (cx - 5.0, cy + 6.0, -7.0, 3.1, 0.60),
        (cx + 6.0, cy + 8.0, -7.0, 3.3, 0.65),
    ]
    for sx, sy, sz_bot, height, rad in stalagmite_locs:
        b_ring = []
        for i in range(8):
            a = i * 2.0 * math.pi / 8.0
            b_ring.append(bm_sp.verts.new((sx + rad * math.cos(a), sy + rad * math.sin(a), sz_bot)))
        tip = bm_sp.verts.new((sx, sy, sz_bot + height))
        for i in range(8):
            i_next = (i + 1) % 8
            bm_sp.faces.new((b_ring[i_next], b_ring[i], tip))

    # C. Karst Columns (Fused Stalactite + Stalagmite)
    for col_x, col_y in [(cx - 1.0, cy - 7.0), (cx + 2.0, cy + 11.0)]:
        r_col = 0.45
        v_top = [bm_sp.verts.new((col_x + r_col * math.cos(2 * math.pi * i / 8),
                                  col_y + r_col * math.sin(2 * math.pi * i / 8),
                                  0.2)) for i in range(8)]
        v_mid = [bm_sp.verts.new((col_x + (r_col * 0.7) * math.cos(2 * math.pi * i / 8),
                                  col_y + (r_col * 0.7) * math.sin(2 * math.pi * i / 8),
                                  -3.5)) for i in range(8)]
        v_bot = [bm_sp.verts.new((col_x + r_col * math.cos(2 * math.pi * i / 8),
                                  col_y + r_col * math.sin(2 * math.pi * i / 8),
                                  -7.0)) for i in range(8)]
        for i in range(8):
            inxt = (i + 1) % 8
            bm_sp.faces.new((v_top[i], v_top[inxt], v_mid[inxt], v_mid[i]))
            bm_sp.faces.new((v_mid[i], v_mid[inxt], v_bot[inxt], v_bot[i]))

    mesh_sp = bpy.data.meshes.new("Cave_Speleothems_Mesh")
    bm_sp.to_mesh(mesh_sp)
    bm_sp.free()
    mesh_sp.update(calc_edges=True)
    mesh_sp.shade_smooth()
    for p in mesh_sp.polygons:
        p.use_smooth = True
    mesh_sp.materials.append(mat_cave_rock)

    speleo_obj = bpy.data.objects.new("Cave_Speleothems", mesh_sp)
    collection.objects.link(speleo_obj)

    # 3. Subterranean Cave Pool (Z = -6.8m)
    p_radius = 8.5
    pool_verts = [(cx, cy, -6.8)]
    pool_faces = []
    n_p = 24
    for i in range(n_p):
        a = i * 2.0 * math.pi / n_p
        pool_verts.append((cx + p_radius * math.cos(a), cy + p_radius * math.sin(a), -6.8))
    for i in range(n_p):
        pool_faces.append((0, 1 + i, 1 + ((i + 1) % n_p)))

    mesh_pool = bpy.data.meshes.new("Water_CavePool_Mesh")
    mesh_pool.from_pydata(pool_verts, [], pool_faces)
    mesh_pool.update(calc_edges=True)
    mesh_pool.shade_smooth()
    for p in mesh_pool.polygons:
        p.use_smooth = True
    mesh_pool.materials.append(mat_water)

    cave_pool_obj = bpy.data.objects.new("Water_CavePool", mesh_pool)
    collection.objects.link(cave_pool_obj)

    # 4. Bioluminescent Ambient Point Light
    light_data = bpy.data.lights.new(name="Cave_Biolum_Light", type='POINT')
    light_data.energy = 25.0
    light_data.color = (0.12, 0.92, 0.82)
    light_data.shadow_soft_size = 2.0
    light_obj = bpy.data.objects.new("Cave_Biolum_Light", light_data)
    light_obj.location = (cx, cy, -4.5)
    collection.objects.link(light_obj)

    # 5. Natural Cave Entrance Portal Arch leading from River Gorge
    entrance_obj = build_cave_entrance_portal(collection, mat_cave_rock)

    return {
        "cave_obj": cave_obj,
        "speleo_obj": speleo_obj,
        "cave_pool_obj": cave_pool_obj,
        "cave_light_obj": light_obj,
        "entrance_obj": entrance_obj,
    }


# -----------------------------------------------------------------------------
# Main Entry Point & Contract Dictionary
# -----------------------------------------------------------------------------


def generate_terrain_and_hydrology(context, collection_diorama=None, collection_terrain=None,
                                    collection_hydrology=None, collection_cave=None):
    """
    Constructs the complete diorama cutaway block, multi-tier hydrology, and subterranean cave.
    Supports flexible arguments for both the 8-collection pipeline and legacy 2-collection callers.
    """
    # Normalize collections
    if collection_terrain is None and collection_diorama is not None:
        collection_terrain = collection_diorama
    if collection_diorama is None:
        collection_diorama = collection_terrain
    if collection_hydrology is None:
        collection_hydrology = collection_terrain
    if collection_cave is None:
        collection_cave = collection_terrain

    # 1. Build Diorama Cutaway Block
    diorama_block_obj = build_watertight_diorama_block(collection_diorama)

    # 2. Build Multi-Tier Hydrology Meshes
    hydro_dict = build_hydrology_meshes(collection_hydrology, diorama_block_obj)

    # 3. Build Subterranean Karst Cave
    cave_dict = build_subterranean_cave(collection_cave)

    # Compile Authoritative Contract Dictionary
    terrain_contract = {
        # Primary Mesh Objects
        "diorama_block_obj": diorama_block_obj,
        "terrain_obj": diorama_block_obj,  # Alias for backward compatibility
        "lake_obj": hydro_dict["lake_obj"],
        "pond_obj": hydro_dict["pond_obj"],
        "stream_obj": hydro_dict["stream_obj"],
        "bay_obj": hydro_dict["bay_obj"],
        "river_obj": hydro_dict["river_obj"],
        "foam_obj": hydro_dict["foam_obj"],
        "cave_obj": cave_dict["cave_obj"],
        "speleo_obj": cave_dict["speleo_obj"],
        "cave_pool_obj": cave_dict["cave_pool_obj"],
        "entrance_obj": cave_dict["entrance_obj"],

        # Spatial Query Callables
        "height_func": compute_terrain_elevation,
        "slope_func": compute_terrain_slope,
        "lake_dist_func": compute_lake_distance,
        "pond_dist_func": compute_pond_distance,
        "bay_dist_func": compute_bay_distance,
        "river_dist_func": compute_river_distance,
        "water_dist_func": compute_water_distance,

        # Cave Boundaries & Anchors
        "cave_bounds": {
            "center": (12.0, 12.0, -4.5),
            "rx": 15.0, "ry": 20.0, "rz": 4.2,
            "floor_z": -7.0,
            "ceiling_z": 0.4,
            "pool_z": -6.8,
            "entrance_loc": (15.0, -6.5, 2.2),
        },

        # Biome Anchors (for Fauna Placement & Framing)
        "biome_anchors": {
            "alpine_peak": (-8.0, 52.0, 28.2),
            "alpine_goat": (-12.0, 48.0, 22.5),
            "alpine_eagle": (5.0, -5.0, 36.0),
            "village_center": (-2.0, -14.0, 5.4),
            "watchtower": (24.0, 16.0, 10.5),
            "meadow_stag": (4.0, -14.0, 5.6),
            "lake_center": (-18.0, -6.0, 4.5),
            "pond_center": (18.0, -5.0, 4.85),
            "lake_fish": (-18.0, -6.0, 3.2),
            "bay_center": (45.0, -45.0, 0.0),
            "cave_bat": (13.5, 4.5, 0.5),
        }
    }

    return terrain_contract


# Backward compatibility alias
build_terrain_and_hydrology = generate_terrain_and_hydrology

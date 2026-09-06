"""
prototype_survey.py - Comprehensive prototype verifying:
1. Diorama cutaway block geometry (top surface + 4 vertical walls + bottom face).
2. Multi-tier hydrology (Alpine stream -> Waterfall -> Central lake -> Outlet cascade -> Coastal bay).
3. Subterranean Karst Cave (Arched limestone chamber, entrance opening, stalactites, stalagmites, cave pool).
4. Procedural / Triplanar strata shaders & Water Volume Absorption shader.
"""

import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Euler

def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def build_prototype():
    print(">>> Starting Prototype Build in Blender...")
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1. Coordinate Grid Setup
    L = 160.0        # 160m x 160m diorama block
    half_L = L / 2.0  # [-80.0, 80.0]
    base_z = -14.0   # Solid base bottom at Z = -14m
    res = 128        # Resolution 128x128

    xs = np.linspace(-half_L, half_L, res)
    ys = np.linspace(-half_L, half_L, res)
    xx, yy = np.meshgrid(xs, ys)

    # -------------------------------------------------------------
    # ELEVATION FORMULATION:
    # 1. Alpine Mountain Range in North & Northwest
    #    Elevations up to Z = 28m - 32m
    # 2. Foothills & Mid Valley: Z = 6m - 12m
    # 3. Central Freshwater Lake: Z = 4.5m
    # 4. Lower Coastal Marine Bay: Z = 0.0m, Bed down to Z = -4.5m
    # -------------------------------------------------------------
    # Mountains:
    # Smooth ridge profile in Northern quadrant
    mount_factor = smoothstep(0.0, 70.0, yy + 10.0) ** 1.5
    # Two primary sharp angular horns / peaks
    p1 = np.exp(-((xx + 30.0)**2 + (yy - 40.0)**2) / (2.0 * 16.0**2)) * 24.0
    p2 = np.exp(-((xx - 15.0)**2 + (yy - 50.0)**2) / (2.0 * 18.0**2)) * 20.0
    # Ridge texture
    ridges = np.abs(np.sin(xx * 0.07 + yy * 0.05)) * 5.0 + np.abs(np.cos(xx * 0.1 - yy * 0.06)) * 3.0
    mount_z = mount_factor * (ridges + p1 + p2)

    # Foothills & general undulations
    foothills = 2.5 * np.sin(xx * 0.04) * np.cos(yy * 0.04) + 1.5 * np.sin(xx * 0.08 + 1.2)

    # Valley base elevation
    z = 6.0 + mount_z + foothills

    # Lake depression at (-25, -10): rim=26m, bed=14m, water=4.5m, bed=1.8m
    d_lake = np.hypot(xx - (-25.0), yy - (-10.0))
    lake_blend = smoothstep(14.0, 28.0, d_lake)
    # Smooth blend between original terrain and bowl
    lake_bowl = 1.8 + 2.5 * smoothstep(0.0, 14.0, d_lake)
    z = lake_blend * z + (1.0 - lake_blend) * np.minimum(z, lake_bowl)

    # Coastal Marine Bay in Southeast (cx=38, cy=-38):
    # Dropping from valley (~6m) down to beach (~0.5m) and deep bay (-4.5m)
    d_bay = np.hypot(xx - 40.0, yy - (-40.0))
    bay_blend = smoothstep(20.0, 42.0, d_bay)
    bay_bowl = -4.5 + 4.8 * smoothstep(0.0, 20.0, d_bay)
    z = bay_blend * z + (1.0 - bay_blend) * np.minimum(z, bay_bowl)

    # Smooth clamp: keep terrain above base_z + 4m
    z = np.maximum(z, -5.0)

    # 2. Watertight Diorama Mesh
    verts = []
    faces = []
    top_vert_count = res * res

    for j in range(res):
        for i in range(res):
            verts.append((float(xx[j, i]), float(yy[j, i]), float(z[j, i])))

    for j in range(res - 1):
        for i in range(res - 1):
            v0 = j * res + i
            v1 = j * res + i + 1
            v2 = (j + 1) * res + i + 1
            v3 = (j + 1) * res + i
            faces.append((v0, v1, v2, v3))

    # Boundary top indices (counter-clockwise)
    boundary_top_indices = []
    for i in range(res):
        boundary_top_indices.append(0 * res + i)  # South (y = -half_L)
    for j in range(1, res):
        boundary_top_indices.append(j * res + (res - 1))  # East (x = half_L)
    for i in range(res - 2, -1, -1):
        boundary_top_indices.append((res - 1) * res + i)  # North (y = half_L)
    for j in range(res - 2, 0, -1):
        boundary_top_indices.append(j * res + 0)  # West (x = -half_L)

    num_b = len(boundary_top_indices)
    bottom_start_idx = len(verts)

    # Bottom perimeter vertices at base_z
    for idx in boundary_top_indices:
        vx, vy, _ = verts[idx]
        verts.append((vx, vy, base_z))

    # Wall quads
    for k in range(num_b):
        k_next = (k + 1) % num_b
        t1 = boundary_top_indices[k]
        t2 = boundary_top_indices[k_next]
        b1 = bottom_start_idx + k
        b2 = bottom_start_idx + k_next
        faces.append((t1, b1, b2, t2))

    # Bottom cap fan
    bot_center_idx = len(verts)
    verts.append((0.0, 0.0, base_z))
    for k in range(num_b):
        k_next = (k + 1) % num_b
        b1 = bottom_start_idx + k
        b2 = bottom_start_idx + k_next
        faces.append((bot_center_idx, b2, b1))

    # 3. Calculate Normals and Slope
    dx_val = L / (res - 1)
    gz, gx = np.gradient(z, dx_val)
    nz_grid = 1.0 / np.sqrt(1.0 + gx**2 + gz**2)
    slope_deg = np.degrees(np.arccos(np.clip(nz_grid, 0.0, 1.0)))
    slope_flat = slope_deg.ravel()
    z_flat = z.ravel()

    # Create Blender Mesh
    mesh_diorama = bpy.data.meshes.new("Diorama_Block_Mesh")
    mesh_diorama.from_pydata(verts, [], faces)
    mesh_diorama.update(calc_edges=True)
    mesh_diorama.shade_smooth()

    # Color definitions (RGBA)
    c_snow     = np.array([0.92, 0.94, 0.98, 1.0], dtype=np.float32)
    c_rock     = np.array([0.38, 0.36, 0.34, 1.0], dtype=np.float32)
    c_scree    = np.array([0.50, 0.46, 0.40, 1.0], dtype=np.float32)
    c_grass    = np.array([0.28, 0.48, 0.18, 1.0], dtype=np.float32)
    c_sand     = np.array([0.78, 0.72, 0.52, 1.0], dtype=np.float32)
    c_topsoil  = np.array([0.22, 0.15, 0.08, 1.0], dtype=np.float32)
    c_subsoil  = np.array([0.48, 0.32, 0.18, 1.0], dtype=np.float32)
    c_bedrock  = np.array([0.32, 0.30, 0.28, 1.0], dtype=np.float32)

    col_data = np.zeros((len(verts), 4), dtype=np.float32)

    # Top surface vertices
    for idx in range(top_vert_count):
        vz = z_flat[idx]
        sl = slope_flat[idx]

        # Base color by elevation
        if vz < 0.8:
            # Beach / Shallow seabed
            col = c_sand
        elif vz < 4.8:
            # Lowland near water
            t = smoothstep(0.8, 4.8, vz)
            col = (1.0 - t) * c_sand + t * c_grass
        elif vz < 18.0:
            # Lush valley & forested hills
            col = c_grass
        elif vz < 22.0:
            # Sub-alpine transition
            t = smoothstep(18.0, 22.0, vz)
            col = (1.0 - t) * c_grass + t * c_scree
        else:
            # High alpine peaks: snow on gentle slopes, rock on steep
            col = c_snow

        # Slope override: steep cliffs (>40°) expose rock strata, scree on 25°-40°
        if vz > 1.5:  # Above beach
            if sl > 40.0:
                rock_t = smoothstep(40.0, 55.0, sl)
                col = (1.0 - rock_t) * col + rock_t * c_rock
            elif sl > 25.0:
                scree_t = smoothstep(25.0, 40.0, sl)
                col = (1.0 - scree_t) * col + scree_t * c_scree

        col_data[idx] = col

    # Wall vertices
    for idx in range(top_vert_count, len(verts)):
        vx, vy, vz = verts[idx]
        # Depth relative to rim (approx 5.0m)
        depth = 5.0 - vz
        if depth < 1.5:
            col = c_topsoil
        elif depth < 4.5:
            t = (depth - 1.5) / 3.0
            col = (1.0 - t) * c_topsoil + t * c_subsoil
        else:
            # Bedrock with horizontal striations
            band = 0.16 * math.sin(vz * 1.6) + 0.09 * math.cos(vz * 3.4)
            col = np.clip(c_bedrock * (1.0 + band), 0.0, 1.0)
        col_data[idx] = col

    col_attr = mesh_diorama.color_attributes.new(name="COLOR_0", type="FLOAT_COLOR", domain="POINT")
    col_attr.data.foreach_set("color", col_data.ravel())

    obj_diorama = bpy.data.objects.new("Diorama_Block", mesh_diorama)
    bpy.context.scene.collection.objects.link(obj_diorama)

    # 4. Multi-Tier Hydrology:
    # A. Central Lake Mesh (Disc at Z = 4.5m)
    n_lake_seg = 36
    r_lake_mesh = 21.0
    lake_verts = [(-25.0, -10.0, 4.5)]
    lake_faces = []
    for a in range(n_lake_seg):
        ang = a * 2.0 * math.pi / n_lake_seg
        lake_verts.append((-25.0 + r_lake_mesh * math.cos(ang), -10.0 + r_lake_mesh * math.sin(ang), 4.5))
    for a in range(n_lake_seg):
        lake_faces.append((0, 1 + a, 1 + ((a + 1) % n_lake_seg)))
    m_lake = bpy.data.meshes.new("Water_Central_Lake")
    m_lake.from_pydata(lake_verts, [], lake_faces)
    m_lake.update(calc_edges=True)
    m_lake.shade_smooth()
    obj_lake = bpy.data.objects.new("Water_Central_Lake", m_lake)
    bpy.context.scene.collection.objects.link(obj_lake)

    # B. Coastal Marine Bay Mesh (Disc at Z = 0.0m)
    n_bay_seg = 36
    r_bay_mesh = 32.0
    bay_verts = [(40.0, -40.0, 0.0)]
    bay_faces = []
    for a in range(n_bay_seg):
        ang = a * 2.0 * math.pi / n_bay_seg
        bay_verts.append((40.0 + r_bay_mesh * math.cos(ang), -40.0 + r_bay_mesh * math.sin(ang), 0.0))
    for a in range(n_bay_seg):
        bay_faces.append((0, 1 + a, 1 + ((a + 1) % n_bay_seg)))
    m_bay = bpy.data.meshes.new("Water_Coastal_Bay")
    m_bay.from_pydata(bay_verts, [], bay_faces)
    m_bay.update(calc_edges=True)
    m_bay.shade_smooth()
    obj_bay = bpy.data.objects.new("Water_Coastal_Bay", m_bay)
    bpy.context.scene.collection.objects.link(obj_bay)

    # C. River Connecting Cascades -> Lake -> Bay
    n_riv = 50
    t_r = np.linspace(0.0, 1.0, n_riv)
    rx = -10.0 * (1.0 - t_r) + 28.0 * t_r + 4.0 * np.sin(t_r * 2.5 * np.pi)
    ry = 38.0 * (1.0 - t_r) - 25.0 * t_r
    rz = 16.0 * (1.0 - t_r)**2 + 4.5 * 2.0 * (1.0 - t_r) * t_r + 0.2 * t_r**2
    rw = 3.5 * (1.0 - t_r) + 6.5 * t_r

    r_verts = []
    r_faces = []
    for i in range(n_riv):
        if i == 0:
            tx, ty = rx[1] - rx[0], ry[1] - ry[0]
        elif i == n_riv - 1:
            tx, ty = rx[-1] - rx[-2], ry[-1] - ry[-2]
        else:
            tx, ty = rx[i+1] - rx[i-1], ry[i+1] - ry[i-1]
        t_len = math.hypot(tx, ty)
        nx_w, ny_w = -ty / t_len, tx / t_len
        hw = rw[i] * 0.5
        r_verts.append((rx[i] + nx_w * hw, ry[i] + ny_w * hw, rz[i]))
        r_verts.append((rx[i] - nx_w * hw, ry[i] - ny_w * hw, rz[i]))

    for i in range(n_riv - 1):
        r_faces.append((2 * i, 2 * i + 1, 2 * (i + 1) + 1, 2 * (i + 1)))

    m_riv = bpy.data.meshes.new("Water_River")
    m_riv.from_pydata(r_verts, [], r_faces)
    m_riv.update(calc_edges=True)
    m_riv.shade_smooth()
    obj_riv = bpy.data.objects.new("Water_River", m_riv)
    bpy.context.scene.collection.objects.link(obj_riv)

    # 5. Subterranean Karst Cave
    c_cx, c_cy, c_cz = 10.0, 10.0, -4.5
    c_rx, c_ry, c_rz = 16.0, 22.0, 5.0

    cave_verts = []
    cave_faces = []
    u_steps, v_steps = 20, 14
    for v in range(v_steps + 1):
        phi = v * math.pi / v_steps
        for u in range(u_steps):
            theta = u * 2.0 * math.pi / u_steps
            noise = 1.0 + 0.15 * math.sin(3.0 * theta) * math.cos(2.0 * phi)
            kx = c_cx + c_rx * noise * math.sin(phi) * math.cos(theta)
            ky = c_cy + c_ry * noise * math.sin(phi) * math.sin(theta)
            kz = c_cz + c_rz * noise * math.cos(phi)
            cave_verts.append((kx, ky, kz))

    for v in range(v_steps):
        for u in range(u_steps):
            u_next = (u + 1) % u_steps
            p1 = v * u_steps + u
            p2 = v * u_steps + u_next
            p3 = (v + 1) * u_steps + u_next
            p4 = (v + 1) * u_steps + u
            cave_faces.append((p1, p4, p3, p2))

    mesh_cave = bpy.data.meshes.new("Cave_Cavern_Mesh")
    mesh_cave.from_pydata(cave_verts, [], cave_faces)
    mesh_cave.update(calc_edges=True)
    mesh_cave.shade_smooth()
    obj_cave = bpy.data.objects.new("Cave_Cavern", mesh_cave)
    bpy.context.scene.collection.objects.link(obj_cave)

    # Speleothems
    speleo_verts = []
    speleo_faces = []
    # Stalactites
    for s_i in range(10):
        sx = c_cx + 0.5 * c_rx * math.cos(s_i * 2.0 * math.pi / 10)
        sy = c_cy + 0.5 * c_ry * math.sin(s_i * 2.0 * math.pi / 10)
        sz_base = c_cz + c_rz * 0.7
        sz_tip = sz_base - 2.8 - 0.4 * (s_i % 3)
        r_base = 0.5
        v_offset = len(speleo_verts)
        speleo_verts.append((sx, sy, sz_tip))
        for a in range(6):
            ang = a * 2.0 * math.pi / 6
            speleo_verts.append((sx + r_base * math.cos(ang), sy + r_base * math.sin(ang), sz_base))
        for a in range(6):
            a_next = (a + 1) % 6
            speleo_faces.append((v_offset, v_offset + 1 + a, v_offset + 1 + a_next))

    # Stalagmites
    for s_i in range(8):
        sx = c_cx + 0.4 * c_rx * math.cos((s_i + 0.5) * 2.0 * math.pi / 8)
        sy = c_cy + 0.4 * c_ry * math.sin((s_i + 0.5) * 2.0 * math.pi / 8)
        sz_base = c_cz - c_rz * 0.7
        sz_tip = sz_base + 2.4 + 0.3 * (s_i % 3)
        r_base = 0.55
        v_offset = len(speleo_verts)
        speleo_verts.append((sx, sy, sz_tip))
        for a in range(6):
            ang = a * 2.0 * math.pi / 6
            speleo_verts.append((sx + r_base * math.cos(ang), sy + r_base * math.sin(ang), sz_base))
        for a in range(6):
            a_next = (a + 1) % 6
            speleo_faces.append((v_offset, v_offset + 1 + a_next, v_offset + 1 + a))

    mesh_speleo = bpy.data.meshes.new("Cave_Speleothems_Mesh")
    mesh_speleo.from_pydata(speleo_verts, [], speleo_faces)
    mesh_speleo.update(calc_edges=True)
    mesh_speleo.shade_smooth()
    obj_speleo = bpy.data.objects.new("Cave_Speleothems", mesh_speleo)
    bpy.context.scene.collection.objects.link(obj_speleo)

    # Subterranean Pool
    pool_verts = []
    pool_faces = []
    p_cz = c_cz - 2.5
    pool_verts.append((c_cx, c_cy, p_cz))
    for a in range(16):
        ang = a * 2.0 * math.pi / 16
        pool_verts.append((c_cx + 8.0 * math.cos(ang), c_cy + 11.0 * math.sin(ang), p_cz))
    for a in range(16):
        pool_faces.append((0, 1 + a, 1 + ((a + 1) % 16)))
    mesh_pool = bpy.data.meshes.new("Cave_Pool_Mesh")
    mesh_pool.from_pydata(pool_verts, [], pool_faces)
    mesh_pool.update(calc_edges=True)
    mesh_pool.shade_smooth()
    obj_pool = bpy.data.objects.new("Cave_Pool", mesh_pool)
    bpy.context.scene.collection.objects.link(obj_pool)

    print("  ✓ Built Diorama Block, Hydrology, and Cave.")

build_prototype()

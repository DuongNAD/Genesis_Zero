"""
flora_generator.py - Procedural 4-Zone Biome Botanical Modeling & Geometry Nodes Scatter
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Architectural Features:
1. 4-Zone Biome Diversity:
   - Alpine Biome: Cold-hardy dwarf pines (Flora_Conifer), alpine tussock grass (Flora_TussockGrass), crustose rock lichens.
   - Lowland & Forest Biome: Deciduous canopy oaks (Flora_Broadleaf), understory flowering shrubs (Flora_Shrub), ferns.
   - Aquatic & Riparian Biome: Marsh cattails and reeds (Flora_Reed), floating water lilies (Flora_Lily), coastal coral greenery (Flora_CoralReef).
   - Subterranean Cave Biome: Bioluminescent glowing mushrooms (Flora_CaveMushroom) with emissive cyan caps, cave moss (Flora_CaveMoss).
2. Geometry Nodes Procedural Scatter Architecture:
   - Procedural node trees utilizing Altitude (Z), Slope Normal (Nz), and Water Proximity masks.
   - Poisson-disk point distribution with scale and rotation variation.
   - Point instancing and GeometryNodeRealizeInstances for robust glTF/GLB export.
3. Botanical Quality Invariants:
   - 100% of polygon faces have use_smooth = True.
   - Multi-material slots for realistic biological texturing.
   - Zero loose prototypes rendering at origin (hide_render = True on prototype container).
"""

import math
import random
import bpy
import bmesh
from mathutils import Vector, Euler


def create_pbr_material(name, base_color, roughness=0.6, specular=0.3, emission_color=None, emission_strength=0.0):
    """Utility to create a Principled BSDF material."""
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


def create_flora_prototypes():
    """
    Creates base procedural botanical prototype meshes with multi-material slots
    and 100% smooth polygon shading (use_smooth = True).
    """
    # Materials
    mat_bark_pine = create_pbr_material("M_Bark_Pine", (0.12, 0.08, 0.05, 1.0), roughness=0.85)
    mat_needles_pine = create_pbr_material("M_Needles_Pine", (0.05, 0.20, 0.06, 1.0), roughness=0.60)

    mat_bark_oak = create_pbr_material("M_Bark_Oak", (0.16, 0.10, 0.06, 1.0), roughness=0.85)
    mat_leaves_oak = create_pbr_material("M_Leaves_Oak", (0.10, 0.36, 0.08, 1.0), roughness=0.50)

    mat_reed_green = create_pbr_material("M_Reed_Green", (0.32, 0.52, 0.14, 1.0), roughness=0.55)
    mat_cattail_brown = create_pbr_material("M_Cattail_Brown", (0.18, 0.10, 0.05, 1.0), roughness=0.90)

    mat_lily_pad = create_pbr_material("M_Lily_Pad", (0.10, 0.38, 0.18, 1.0), roughness=0.40)
    mat_lily_petal = create_pbr_material("M_Lily_Petal", (0.95, 0.85, 0.88, 1.0), roughness=0.30)

    mat_tussock = create_pbr_material("M_Tussock_Grass", (0.45, 0.52, 0.22, 1.0), roughness=0.70)
    mat_coral = create_pbr_material("M_Coral_Reef", (0.92, 0.42, 0.38, 1.0), roughness=0.35)

    mat_shroom_stalk = create_pbr_material("M_Bio_Stalk", (0.85, 0.95, 0.92, 1.0), roughness=0.50)
    mat_shroom_cap = create_pbr_material(
        "M_Bio_Mushroom",
        (0.12, 0.92, 0.82, 1.0),
        roughness=0.25,
        emission_color=(0.12, 0.92, 0.82, 1.0),
        emission_strength=4.5
    )

    # -------------------------------------------------------------------------
    # 1. Alpine Dwarf Conifer / Mountain Pine (Flora_Conifer)
    # -------------------------------------------------------------------------
    m_conifer = bpy.data.meshes.new("Flora_Conifer")
    m_conifer.materials.append(mat_bark_pine)     # 0
    m_conifer.materials.append(mat_needles_pine)  # 1
    verts_c, faces_c, mat_c = [], [], []

    # Trunk cylinder (6 vertical slices, 8 radial segments)
    for s in range(6):
        z = (s / 5.0) * 7.2
        r = 0.36 * (1.0 - 0.65 * (s / 5.0))
        for i in range(8):
            a = i * 2.0 * math.pi / 8.0
            verts_c.append((r * math.cos(a), r * math.sin(a), z))
    for s in range(5):
        for i in range(8):
            inxt = (i + 1) % 8
            faces_c.append((s * 8 + i, s * 8 + inxt, (s + 1) * 8 + inxt, (s + 1) * 8 + i))
            mat_c.append(0)

    # 4 tiered conical skirts with scalloped droop
    for th, tr, td in [(2.2, 2.3, 1.9), (3.8, 1.8, 1.7), (5.2, 1.3, 1.4), (6.4, 0.8, 1.2)]:
        apx = len(verts_c)
        verts_c.append((0.0, 0.0, th + td))
        rim_st = len(verts_c)
        for i in range(10):
            a = i * 2.0 * math.pi / 10.0
            r_mod = tr * (1.0 + 0.15 * math.sin(a * 3.0))
            z_drp = th - 0.25 * math.cos(a * 2.0)
            verts_c.append((r_mod * math.cos(a), r_mod * math.sin(a), z_drp))
        for i in range(10):
            inxt = (i + 1) % 10
            faces_c.append((apx, rim_st + i, rim_st + inxt))
            mat_c.append(1)
        cap = len(verts_c)
        verts_c.append((0.0, 0.0, th + 0.25))
        for i in range(10):
            inxt = (i + 1) % 10
            faces_c.append((cap, rim_st + inxt, rim_st + i))
            mat_c.append(1)

    m_conifer.from_pydata(verts_c, [], faces_c)
    m_conifer.update(calc_edges=True)
    m_conifer.shade_smooth()
    for idx, poly in enumerate(m_conifer.polygons):
        poly.use_smooth = True
        poly.material_index = mat_c[idx]

    # -------------------------------------------------------------------------
    # 1b. Alpine Golden Larch / Autumn Pine (Flora_Larch)
    # -------------------------------------------------------------------------
    mat_needles_larch = create_pbr_material("M_Needles_Larch", (0.82, 0.48, 0.08, 1.0), roughness=0.55)
    m_larch = bpy.data.meshes.new("Flora_Larch")
    m_larch.materials.append(mat_bark_pine)     # 0
    m_larch.materials.append(mat_needles_larch) # 1
    m_larch.from_pydata(verts_c, [], faces_c)
    m_larch.update(calc_edges=True)
    m_larch.shade_smooth()
    for idx, poly in enumerate(m_larch.polygons):
        poly.use_smooth = True
        poly.material_index = mat_c[idx]

    # -------------------------------------------------------------------------
    # 1c. 3D Granite Mountain & River Boulders (Flora_Boulder)
    # -------------------------------------------------------------------------
    mat_boulder = create_pbr_material("M_Rock_Boulder", (0.28, 0.27, 0.25, 1.0), roughness=0.82)
    m_boulder = bpy.data.meshes.new("Flora_Boulder")
    m_boulder.materials.append(mat_boulder)
    verts_rk, faces_rk = [], []
    phi_steps, th_steps = 6, 8
    for p in range(phi_steps):
        phi = math.pi * p / (phi_steps - 1)
        z_rk = 1.1 * math.cos(phi)
        r_rk = 1.5 * math.sin(phi)
        for t in range(th_steps):
            th = 2.0 * math.pi * t / th_steps
            distort = 1.0 + 0.22 * math.sin(2.0 * th) * math.cos(3.0 * phi) + 0.12 * math.cos(3.0 * th)
            verts_rk.append((r_rk * math.cos(th) * distort, r_rk * math.sin(th) * distort, z_rk * distort))
    for p in range(phi_steps - 1):
        for t in range(th_steps):
            t_next = (t + 1) % th_steps
            v1 = p * th_steps + t
            v2 = p * th_steps + t_next
            v3 = (p + 1) * th_steps + t_next
            v4 = (p + 1) * th_steps + t
            faces_rk.append((v1, v2, v3, v4))
    m_boulder.from_pydata(verts_rk, [], faces_rk)
    m_boulder.update(calc_edges=True)
    m_boulder.shade_smooth()
    for poly in m_boulder.polygons:
        poly.use_smooth = True
        poly.material_index = 0

    # -------------------------------------------------------------------------
    # 2. Lowland Broadleaf Deciduous Oak (Flora_Broadleaf)
    # -------------------------------------------------------------------------
    m_broad = bpy.data.meshes.new("Flora_Broadleaf")
    m_broad.materials.append(mat_bark_oak)    # 0
    m_broad.materials.append(mat_leaves_oak)  # 1
    verts_b, faces_b, mat_b = [], [], []

    # Lofted organic trunk
    for s in range(7):
        t = s / 6.0
        z = t * 4.6
        cx = 0.3 * math.sin(t * 1.5)
        cy = 0.2 * (1.0 - math.cos(t * 1.2))
        r = 0.46 * (1.0 - 0.5 * t) + 0.2 * math.exp(-t * 5.0)
        for i in range(8):
            a = i * 2.0 * math.pi / 8.0
            verts_b.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    for s in range(6):
        for i in range(8):
            inxt = (i + 1) % 8
            faces_b.append((s * 8 + i, s * 8 + inxt, (s + 1) * 8 + inxt, (s + 1) * 8 + i))
            mat_b.append(0)

    # 4 overlapping volumetric canopy foliage lobes
    clusters = [
        (Vector((0.0, 0.0, 4.8)), 2.1),
        (Vector((1.2, 0.8, 4.3)), 1.7),
        (Vector((-1.0, 0.9, 4.4)), 1.6),
        (Vector((0.7, -1.1, 4.2)), 1.7),
    ]
    for ctr, rad in clusters:
        sp_st = len(verts_b)
        verts_b.append((ctr.x, ctr.y, ctr.z + rad * 0.9))
        verts_b.append((ctr.x, ctr.y, ctr.z - rad * 0.8))
        ring_st = len(verts_b)
        for lt in range(1, 5):
            phi = math.pi * lt / 5.0
            z_o = rad * math.cos(phi) * 0.85
            r_r = rad * math.sin(phi)
            for ln in range(8):
                th = 2.0 * math.pi * ln / 8.0
                bump = 1.0 + 0.12 * math.sin(3.0 * th) * math.cos(2.0 * phi)
                verts_b.append((ctr.x + r_r * math.cos(th) * bump, ctr.y + r_r * math.sin(th) * bump, ctr.z + z_o * bump))
        for ln in range(8):
            faces_b.append((sp_st, ring_st + ln, ring_st + ((ln + 1) % 8)))
            mat_b.append(1)
        for lt in range(3):
            r1 = ring_st + lt * 8
            r2 = ring_st + (lt + 1) * 8
            for ln in range(8):
                inxt = (ln + 1) % 8
                faces_b.append((r1 + ln, r2 + ln, r2 + inxt, r1 + inxt))
                mat_b.append(1)
        lst_ring = ring_st + 3 * 8
        for ln in range(8):
            faces_b.append((sp_st + 1, lst_ring + ((ln + 1) % 8), lst_ring + ln))
            mat_b.append(1)

    m_broad.from_pydata(verts_b, [], faces_b)
    m_broad.update(calc_edges=True)
    m_broad.shade_smooth()
    for idx, poly in enumerate(m_broad.polygons):
        poly.use_smooth = True
        poly.material_index = mat_b[idx]

    # -------------------------------------------------------------------------
    # 3. Wetland Marsh Cattail / Reed (Flora_Reed)
    # -------------------------------------------------------------------------
    m_reed = bpy.data.meshes.new("Flora_Reed")
    m_reed.materials.append(mat_reed_green)     # 0
    m_reed.materials.append(mat_cattail_brown)  # 1
    verts_r, faces_r, mat_r = [], [], []

    # 8 arching ribbon blades
    for b in range(8):
        ang = b * 2.0 * math.pi / 8.0 + 0.2 * math.sin(b)
        dx, dy = math.cos(ang), math.sin(ang)
        bh = 1.5 + 0.4 * math.sin(b * 2.0)
        lean = 0.35 + 0.15 * math.cos(b)
        for s in range(5):
            t = s / 4.0
            z = t * bh
            roff = lean * (t ** 1.5)
            w = 0.05 * (1.0 - t * 0.85)
            px, py = -dy * w, dx * w
            cx, cy = dx * roff, dy * roff
            verts_r.append((cx - px, cy - py, z))
            verts_r.append((cx + px, cy + py, z))
        base_i = len(verts_r) - 10
        for s in range(4):
            faces_r.append((base_i + 2 * s, base_i + 2 * s + 1, base_i + 2 * (s + 1) + 1, base_i + 2 * (s + 1)))
            mat_r.append(0)

    # 2 upright cattail stalks with brown seed heads
    for k in range(2):
        ka = k * math.pi + 0.5
        sh = 1.65 + 0.2 * k
        stk_st = len(verts_r)
        for s in range(3):
            z = (s / 2.0) * sh
            for i in range(4):
                a = i * math.pi / 2.0
                verts_r.append((0.02 * math.cos(a) + 0.1 * math.cos(ka), 0.02 * math.sin(a) + 0.1 * math.sin(ka), z))
        for s in range(2):
            for i in range(4):
                faces_r.append((stk_st + s * 4 + i, stk_st + s * 4 + ((i + 1) % 4), stk_st + (s + 1) * 4 + ((i + 1) % 4), stk_st + (s + 1) * 4 + i))
                mat_r.append(0)

        hd_st = len(verts_r)
        for s in range(3):
            z = sh * 0.65 + s * 0.15
            for i in range(6):
                a = i * 2.0 * math.pi / 6.0
                verts_r.append((0.045 * math.cos(a) + 0.1 * math.cos(ka), 0.045 * math.sin(a) + 0.1 * math.sin(ka), z))
        for s in range(2):
            for i in range(6):
                faces_r.append((hd_st + s * 6 + i, hd_st + s * 6 + ((i + 1) % 6), hd_st + (s + 1) * 6 + ((i + 1) % 6), hd_st + (s + 1) * 6 + i))
                mat_r.append(1)

    m_reed.from_pydata(verts_r, [], faces_r)
    m_reed.update(calc_edges=True)
    m_reed.shade_smooth()
    for idx, poly in enumerate(m_reed.polygons):
        poly.use_smooth = True
        poly.material_index = mat_r[idx]

    # -------------------------------------------------------------------------
    # 4. Floating Water Lily (Flora_Lily)
    # -------------------------------------------------------------------------
    m_lily = bpy.data.meshes.new("Flora_Lily")
    m_lily.materials.append(mat_lily_pad)    # 0
    m_lily.materials.append(mat_lily_petal)  # 1
    verts_l, faces_l, mat_l = [(0.0, 0.0, 0.0)], [], []
    n_rim = 14
    rim_st = 1
    angles = [0.4 + i * (2.0 * math.pi - 0.8) / (n_rim - 1) for i in range(n_rim)]
    for a in angles:
        w_r = 0.58 * (1.0 + 0.05 * math.sin(a * 5.0))
        verts_l.append((w_r * math.cos(a), w_r * math.sin(a), 0.01 * math.sin(a * 3.0)))
    for i in range(n_rim - 1):
        faces_l.append((0, rim_st + i, rim_st + i + 1))
        mat_l.append(0)

    # 8 sculpted flower petals
    fl_c = (0.05, 0.05, 0.03)
    for p in range(8):
        ang = p * 2.0 * math.pi / 8.0
        pst = len(verts_l)
        verts_l.append(fl_c)
        verts_l.append((fl_c[0] + 0.16 * math.cos(ang), fl_c[1] + 0.16 * math.sin(ang), fl_c[2] + 0.08))
        verts_l.append((fl_c[0] + 0.10 * math.cos(ang - 0.25), fl_c[1] + 0.10 * math.sin(ang - 0.25), fl_c[2] + 0.04))
        verts_l.append((fl_c[0] + 0.10 * math.cos(ang + 0.25), fl_c[1] + 0.10 * math.sin(ang + 0.25), fl_c[2] + 0.04))
        faces_l.append((pst, pst + 2, pst + 1))
        mat_l.append(1)
        faces_l.append((pst, pst + 1, pst + 3))
        mat_l.append(1)

    m_lily.from_pydata(verts_l, [], faces_l)
    m_lily.update(calc_edges=True)
    m_lily.shade_smooth()
    for idx, poly in enumerate(m_lily.polygons):
        poly.use_smooth = True
        poly.material_index = mat_l[idx]

    # -------------------------------------------------------------------------
    # 5. Bioluminescent Subterranean Cave Mushroom (Flora_CaveMushroom)
    # -------------------------------------------------------------------------
    m_shroom = bpy.data.meshes.new("Flora_CaveMushroom")
    m_shroom.materials.append(mat_shroom_stalk)  # 0
    m_shroom.materials.append(mat_shroom_cap)    # 1
    verts_m, faces_m, mat_m = [], [], []

    # Multi-stalk mushroom cluster (3 stalks of varying heights)
    clusters_m = [
        (0.0, 0.0, 0.75, 0.45),
        (0.25, 0.18, 0.55, 0.35),
        (-0.20, 0.15, 0.40, 0.28),
    ]
    for mx, my, m_h, m_rad in clusters_m:
        stk_i = len(verts_m)
        # Stalk
        for s in range(4):
            z = (s / 3.0) * (m_h * 0.8)
            r = 0.05 * (1.0 - 0.2 * (s / 3.0))
            for i in range(6):
                a = i * 2.0 * math.pi / 6.0
                verts_m.append((mx + r * math.cos(a), my + r * math.sin(a), z))
        for s in range(3):
            for i in range(6):
                inxt = (i + 1) % 6
                faces_m.append((stk_i + s * 6 + i, stk_i + s * 6 + inxt, stk_i + (s + 1) * 6 + inxt, stk_i + (s + 1) * 6 + i))
                mat_m.append(0)

        # Glowing Cap (Hemisphere dome)
        cap_i = len(verts_m)
        verts_m.append((mx, my, m_h + 0.15))  # Apex
        cap_rim = len(verts_m)
        for i in range(10):
            a = i * 2.0 * math.pi / 10.0
            verts_m.append((mx + m_rad * math.cos(a), my + m_rad * math.sin(a), m_h))
        for i in range(10):
            inxt = (i + 1) % 10
            faces_m.append((cap_i, cap_rim + i, cap_rim + inxt))
            mat_m.append(1)

        # Cap underside
        under_i = len(verts_m)
        verts_m.append((mx, my, m_h - 0.05))
        for i in range(10):
            inxt = (i + 1) % 10
            faces_m.append((under_i, cap_rim + inxt, cap_rim + i))
            mat_m.append(1)

    m_shroom.from_pydata(verts_m, [], faces_m)
    m_shroom.update(calc_edges=True)
    m_shroom.shade_smooth()
    for idx, poly in enumerate(m_shroom.polygons):
        poly.use_smooth = True
        poly.material_index = mat_m[idx]

    # -------------------------------------------------------------------------
    # 6. Alpine Tussock Grass (Flora_TussockGrass)
    # -------------------------------------------------------------------------
    m_tussock = bpy.data.meshes.new("Flora_TussockGrass")
    m_tussock.materials.append(mat_tussock)
    verts_t, faces_t = [], []
    for b in range(10):
        ang = b * 2.0 * math.pi / 10.0 + random.uniform(-0.1, 0.1)
        bx = math.cos(ang)
        by = math.sin(ang)
        bh = 0.55 + 0.25 * math.sin(b * 3.0)
        lean = 0.30
        for s in range(4):
            t = s / 3.0
            z = t * bh
            r_o = lean * (t ** 1.3)
            w = 0.04 * (1.0 - t * 0.9)
            verts_t.append((bx * r_o - by * w, by * r_o + bx * w, z))
            verts_t.append((bx * r_o + by * w, by * r_o - bx * w, z))
        base_t = len(verts_t) - 8
        for s in range(3):
            faces_t.append((base_t + 2 * s, base_t + 2 * s + 1, base_t + 2 * (s + 1) + 1, base_t + 2 * (s + 1)))

    m_tussock.from_pydata(verts_t, [], faces_t)
    m_tussock.update(calc_edges=True)
    m_tussock.shade_smooth()
    for poly in m_tussock.polygons:
        poly.use_smooth = True

    # -------------------------------------------------------------------------
    # 7. Submerged Marine Coral Reef (Flora_Coral)
    # -------------------------------------------------------------------------
    mat_coral_pink = create_pbr_material("M_Coral_Pink", (0.92, 0.40, 0.52, 1.0), roughness=0.45)
    mat_coral_violet = create_pbr_material("M_Coral_Violet", (0.65, 0.38, 0.85, 1.0), roughness=0.45)
    m_coral = bpy.data.meshes.new("Flora_Coral")
    m_coral.materials.append(mat_coral_pink)    # 0
    m_coral.materials.append(mat_coral_violet)  # 1
    verts_cr, faces_cr, mat_cr = [], [], []
    coral_lobes = [
        (Vector((0.0, 0.0, 0.6)), 0.9, 0),
        (Vector((0.7, 0.5, 0.5)), 0.7, 1),
        (Vector((-0.6, 0.4, 0.5)), 0.65, 0),
    ]
    for cl_pos, cl_rad, cl_mat in coral_lobes:
        sp_st = len(verts_cr)
        verts_cr.append((cl_pos.x, cl_pos.y, cl_pos.z + cl_rad))
        verts_cr.append((cl_pos.x, cl_pos.y, cl_pos.z - cl_rad * 0.5))
        r_st = len(verts_cr)
        for lt in range(1, 4):
            phi = math.pi * lt / 4.0
            z_o = cl_rad * math.cos(phi) * 0.8
            r_r = cl_rad * math.sin(phi)
            for ln in range(8):
                th = 2.0 * math.pi * ln / 8.0
                bump = 1.0 + 0.15 * math.sin(4.0 * th)
                verts_cr.append((cl_pos.x + r_r * math.cos(th) * bump, cl_pos.y + r_r * math.sin(th) * bump, cl_pos.z + z_o))
        for ln in range(8):
            faces_cr.append((sp_st, r_st + ln, r_st + ((ln + 1) % 8)))
            mat_cr.append(cl_mat)
        for lt in range(2):
            r1 = r_st + lt * 8
            r2 = r_st + (lt + 1) * 8
            for ln in range(8):
                inxt = (ln + 1) % 8
                faces_cr.append((r1 + ln, r2 + ln, r2 + inxt, r1 + inxt))
                mat_cr.append(cl_mat)
        lst_r = r_st + 2 * 8
        for ln in range(8):
            faces_cr.append((sp_st + 1, lst_r + ((ln + 1) % 8), lst_r + ln))
            mat_cr.append(cl_mat)
    m_coral.from_pydata(verts_cr, [], faces_cr)
    m_coral.update(calc_edges=True)
    m_coral.shade_smooth()
    for idx, poly in enumerate(m_coral.polygons):
        poly.use_smooth = True
        poly.material_index = mat_cr[idx]

    return {
        "Flora_Conifer": m_conifer,
        "Flora_Larch": m_larch,
        "Flora_Boulder": m_boulder,
        "Flora_Broadleaf": m_broad,
        "Flora_Reed": m_reed,
        "Flora_Lily": m_lily,
        "Flora_CaveMushroom": m_shroom,
        "Flora_TussockGrass": m_tussock,
        "Flora_Coral": m_coral,
    }


def build_biome_geometry_nodes_tree(
    biome_name: str,
    proto_obj: bpy.types.Object,
    z_min: float = None,
    z_max: float = None,
    norm_z_min: float = None,
    lake_dist_min: float = None,
    lake_dist_max: float = None,
    bay_dist_min: float = None,
    dist_min: float = 4.0,
    density_max: float = 0.10,
    scale_min: float = 0.80,
    scale_max: float = 1.25,
    rot_tilt: float = 0.04,
    z_offset: float = 0.0,
) -> bpy.types.GeometryNodeTree:
    """
    Constructs a genuine Blender 5.2.1 LTS GeometryNodeTree for biome procedural scatter:
    - Declares input/output Geometry sockets via NodeTreeInterface.
    - Evaluates mathematical distribution masks: Altitude (Z), Slope Normal (Nz), Water distance.
    - Samples points via Poisson disk distribution.
    - Instances prototype meshes with stochastic scale and rotation.
    - Applies GeometryNodeSetShadeSmooth (100% smooth shading invariant).
    - Applies GeometryNodeRealizeInstances for glTF export & EEVEE Next rendering.
    """
    tree_name = f"GN_{biome_name}_Scatter_Tree"
    nt = bpy.data.node_groups.get(tree_name)
    if not nt:
        nt = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')
    nt.nodes.clear()

    # Sockets for Group Input and Output (Blender 4.0+ / 5.x API)
    if hasattr(nt, "interface"):
        nt.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        nt.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    else:
        nt.inputs.new('NodeSocketGeometry', 'Geometry')
        nt.outputs.new('NodeSocketGeometry', 'Geometry')

    node_in = nt.nodes.new("NodeGroupInput")
    node_in.location = (-1000, 0)
    node_out = nt.nodes.new("NodeGroupOutput")
    node_out.location = (1400, 0)

    # Position & Normal
    pos_node = nt.nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-800, 200)
    norm_node = nt.nodes.new("GeometryNodeInputNormal")
    norm_node.location = (-800, -200)

    sep_p = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_p.location = (-600, 200)
    nt.links.new(pos_node.outputs["Position"], sep_p.inputs["Vector"])

    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_n.location = (-600, -200)
    nt.links.new(norm_node.outputs["Normal"], sep_n.inputs["Vector"])

    masks = []

    # 1. Altitude Z Min
    if z_min is not None:
        c_zmin = nt.nodes.new("FunctionNodeCompare")
        c_zmin.data_type = 'FLOAT'
        c_zmin.operation = 'GREATER_EQUAL'
        nt.links.new(sep_p.outputs["Z"], c_zmin.inputs["A"])
        c_zmin.inputs["B"].default_value = z_min
        masks.append(c_zmin.outputs["Result"])

    # 2. Altitude Z Max
    if z_max is not None:
        c_zmax = nt.nodes.new("FunctionNodeCompare")
        c_zmax.data_type = 'FLOAT'
        c_zmax.operation = 'LESS_EQUAL'
        nt.links.new(sep_p.outputs["Z"], c_zmax.inputs["A"])
        c_zmax.inputs["B"].default_value = z_max
        masks.append(c_zmax.outputs["Result"])

    # 3. Slope Normal Z Min (Filters out steep cliffs & vertical cutaways)
    if norm_z_min is not None:
        c_norm = nt.nodes.new("FunctionNodeCompare")
        c_norm.data_type = 'FLOAT'
        c_norm.operation = 'GREATER_EQUAL'
        nt.links.new(sep_n.outputs["Z"], c_norm.inputs["A"])
        c_norm.inputs["B"].default_value = norm_z_min
        masks.append(c_norm.outputs["Result"])

    # 4. Lake Distance
    if lake_dist_min is not None or lake_dist_max is not None:
        vm_lake = nt.nodes.new("ShaderNodeVectorMath")
        vm_lake.operation = 'DISTANCE'
        nt.links.new(pos_node.outputs["Position"], vm_lake.inputs[0])
        vm_lake.inputs[1].default_value = (-25.0, -10.0, 0.0)
        if lake_dist_min is not None:
            c_lmin = nt.nodes.new("FunctionNodeCompare")
            c_lmin.data_type = 'FLOAT'
            c_lmin.operation = 'GREATER_EQUAL'
            nt.links.new(vm_lake.outputs["Value"], c_lmin.inputs["A"])
            c_lmin.inputs["B"].default_value = lake_dist_min
            masks.append(c_lmin.outputs["Result"])
        if lake_dist_max is not None:
            c_lmax = nt.nodes.new("FunctionNodeCompare")
            c_lmax.data_type = 'FLOAT'
            c_lmax.operation = 'LESS_EQUAL'
            nt.links.new(vm_lake.outputs["Value"], c_lmax.inputs["A"])
            c_lmax.inputs["B"].default_value = lake_dist_max
            masks.append(c_lmax.outputs["Result"])

    # 5. Bay Distance
    if bay_dist_min is not None:
        vm_bay = nt.nodes.new("ShaderNodeVectorMath")
        vm_bay.operation = 'DISTANCE'
        nt.links.new(pos_node.outputs["Position"], vm_bay.inputs[0])
        vm_bay.inputs[1].default_value = (42.0, -42.0, 0.0)
        c_bmin = nt.nodes.new("FunctionNodeCompare")
        c_bmin.data_type = 'FLOAT'
        c_bmin.operation = 'GREATER_EQUAL'
        nt.links.new(vm_bay.outputs["Value"], c_bmin.inputs["A"])
        c_bmin.inputs["B"].default_value = bay_dist_min
        masks.append(c_bmin.outputs["Result"])

    # Combine masks with Boolean AND
    if masks:
        curr_mask = masks[0]
        for m in masks[1:]:
            b_and = nt.nodes.new("FunctionNodeBooleanMath")
            b_and.operation = 'AND'
            nt.links.new(curr_mask, b_and.inputs[0])
            nt.links.new(m, b_and.inputs[1])
            curr_mask = b_and.outputs["Boolean"]
        final_mask = curr_mask
    else:
        final_mask = None

    # Distribute Points on Faces (Poisson Disk Sampling)
    dist_node = nt.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist_node.location = (-100, 0)
    dist_node.distribute_method = 'POISSON'
    dist_node.inputs["Distance Min"].default_value = dist_min
    dist_node.inputs["Density Max"].default_value = density_max
    nt.links.new(node_in.outputs["Geometry"], dist_node.inputs["Mesh"])
    if final_mask:
        nt.links.new(final_mask, dist_node.inputs["Selection"])

    # Object Info for Botanical Prototype
    obj_info = nt.nodes.new("GeometryNodeObjectInfo")
    obj_info.location = (200, 250)
    obj_info.inputs["Object"].default_value = proto_obj
    obj_info.transform_space = 'RELATIVE'

    # Instance on Points
    inst_node = nt.nodes.new("GeometryNodeInstanceOnPoints")
    inst_node.location = (450, 0)
    nt.links.new(dist_node.outputs["Points"], inst_node.inputs["Points"])
    nt.links.new(obj_info.outputs["Geometry"], inst_node.inputs["Instance"])

    # Random Scale Variation
    rand_scale = nt.nodes.new("FunctionNodeRandomValue")
    rand_scale.location = (200, -150)
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs["Min"].default_value = scale_min
    rand_scale.inputs["Max"].default_value = scale_max
    nt.links.new(rand_scale.outputs["Value"], inst_node.inputs["Scale"])

    # Random Rotation Variation
    rand_rot = nt.nodes.new("FunctionNodeRandomValue")
    rand_rot.location = (200, -350)
    rand_rot.data_type = 'FLOAT_VECTOR'
    rand_rot.inputs["Min"].default_value = (-rot_tilt, -rot_tilt, 0.0)
    rand_rot.inputs["Max"].default_value = (rot_tilt, rot_tilt, 2.0 * math.pi)
    nt.links.new(rand_rot.outputs["Value"], inst_node.inputs["Rotation"])

    # Set Shade Smooth (guarantees 100% smooth shading across all instances)
    set_smooth = nt.nodes.new("GeometryNodeSetShadeSmooth")
    set_smooth.location = (700, 0)
    nt.links.new(inst_node.outputs["Instances"], set_smooth.inputs["Geometry"])

    # Realize Instances (CRUCIAL: Enables rendering and glTF export)
    realize_node = nt.nodes.new("GeometryNodeRealizeInstances")
    realize_node.location = (950, 0)
    nt.links.new(set_smooth.outputs["Geometry"], realize_node.inputs["Geometry"])

    # Set Position offset to seamlessly match object carrier world translation
    if abs(z_offset) > 1e-4:
        set_pos = nt.nodes.new("GeometryNodeSetPosition")
        set_pos.location = (1180, 0)
        set_pos.inputs["Offset"].default_value = (0.0, 0.0, -z_offset)
        nt.links.new(realize_node.outputs["Geometry"], set_pos.inputs["Geometry"])
        nt.links.new(set_pos.outputs["Geometry"], node_out.inputs["Geometry"])
    else:
        nt.links.new(realize_node.outputs["Geometry"], node_out.inputs["Geometry"])

    return nt


def setup_geometry_nodes_scatter(scatter_obj, terrain_obj, prototype_obj, biome_name="Alpine", **kwargs):
    """
    Constructs and attaches an active Blender Geometry Nodes modifier to scatter_obj:
    - Creates or updates GN_<Biome>_Scatter_Tree
    - Attaches GN_Scatter_<Biome> modifier
    - Returns the modifier instance
    """
    mod_name = f"GN_Scatter_{biome_name}"
    mod = scatter_obj.modifiers.get(mod_name)
    if not mod:
        mod = scatter_obj.modifiers.new(name=mod_name, type='NODES')
    nt = build_biome_geometry_nodes_tree(biome_name, prototype_obj, **kwargs)
    mod.node_group = nt
    return mod


def generate_and_distribute_flora(context, collection_flora, terrain_data):
    """
    Distributes procedural botanical assets across all 4 biomes using:
    1. Active Geometry Nodes modifiers on 4 dedicated scatter carriers in Flora_Instances.
    2. Landmark hero botanical instances for individual spatial queries and assertions.
    """
    random.seed(42)  # Deterministic procedural placement
    prototypes = create_flora_prototypes()

    m_conifer = prototypes["Flora_Conifer"]
    m_larch = prototypes["Flora_Larch"]
    m_boulder = prototypes["Flora_Boulder"]
    m_broad = prototypes["Flora_Broadleaf"]
    m_reed = prototypes["Flora_Reed"]
    m_lily = prototypes["Flora_Lily"]
    m_shroom = prototypes["Flora_CaveMushroom"]
    m_tussock = prototypes["Flora_TussockGrass"]
    m_coral = prototypes["Flora_Coral"]

    # Create unlinked prototype objects for GeometryNodeObjectInfo
    proto_conifer = bpy.data.objects.get("Flora_Proto_Conifer") or bpy.data.objects.new("Flora_Proto_Conifer", m_conifer)
    proto_broad = bpy.data.objects.get("Flora_Proto_Broadleaf") or bpy.data.objects.new("Flora_Proto_Broadleaf", m_broad)
    proto_reed = bpy.data.objects.get("Flora_Proto_Reed") or bpy.data.objects.new("Flora_Proto_Reed", m_reed)
    proto_shroom = bpy.data.objects.get("Flora_Proto_CaveMushroom") or bpy.data.objects.new("Flora_Proto_CaveMushroom", m_shroom)

    proto_conifer.hide_render = True
    proto_conifer.hide_viewport = True
    proto_broad.hide_render = True
    proto_broad.hide_viewport = True
    proto_reed.hide_render = True
    proto_reed.hide_viewport = True
    proto_shroom.hide_render = True
    proto_shroom.hide_viewport = True

    height_func = terrain_data["height_func"]
    slope_func = terrain_data.get("slope_func", lambda x, y: 15.0)
    river_dist_func = terrain_data.get("river_dist_func", lambda x, y: 30.0)
    lake_dist_func = terrain_data.get("lake_dist_func", lambda x, y: 50.0)
    bay_dist_func = terrain_data.get("bay_dist_func", lambda x, y: 60.0)
    cave_bounds = terrain_data.get("cave_bounds", {
        "center": (12.0, 12.0, -4.5),
        "rx": 15.0, "ry": 20.0, "floor_z": -7.0,
    })

    terrain_obj = terrain_data.get("diorama_block_obj") or terrain_data.get("terrain_obj")
    cave_obj = terrain_data.get("cave_obj") or terrain_data.get("cave_cavern_obj")

    placed_objects = []

    # -------------------------------------------------------------------------
    # PART A: Dedicated 4-Zone Geometry Nodes Scatter Carriers
    # -------------------------------------------------------------------------
    tz0 = height_func(0.0, 0.0)

    biome_scatter_configs = [
        {
            "name": "Flora_Scatter_Alpine",
            "mesh_source": terrain_obj.data,
            "biome": "Alpine",
            "proto": proto_conifer,
            "kwargs": {
                "z_min": 5.0,
                "z_max": 14.5,
                "norm_z_min": 0.60,
                "lake_dist_min": 18.0,
                "bay_dist_min": 30.0,
                "dist_min": 5.5,
                "density_max": 0.04,
                "scale_min": 0.75,
                "scale_max": 1.35,
                "rot_tilt": 0.04,
                "z_offset": tz0,
            },
        },
        {
            "name": "Flora_Scatter_Lowland",
            "mesh_source": terrain_obj.data,
            "biome": "Lowland",
            "proto": proto_broad,
            "kwargs": {
                "z_min": 4.8,
                "z_max": 8.5,
                "norm_z_min": 0.95,
                "lake_dist_min": 24.0,
                "bay_dist_min": 35.0,
                "dist_min": 16.0,
                "density_max": 0.008,
                "scale_min": 0.80,
                "scale_max": 1.25,
                "rot_tilt": 0.0,
                "z_offset": tz0,
            },
        },
        {
            "name": "Flora_Scatter_Aquatic",
            "mesh_source": terrain_obj.data,
            "biome": "Aquatic",
            "proto": proto_reed,
            "kwargs": {
                "z_min": 4.0,
                "z_max": 6.2,
                "lake_dist_min": 18.0,
                "lake_dist_max": 25.0,
                "dist_min": 3.0,
                "density_max": 0.08,
                "scale_min": 0.70,
                "scale_max": 1.20,
                "rot_tilt": 0.0,
                "z_offset": tz0,
            },
        },
        {
            "name": "Flora_Scatter_Cave",
            "mesh_source": cave_obj.data if cave_obj else terrain_obj.data,
            "biome": "Cave",
            "proto": proto_shroom,
            "kwargs": {
                "z_max": -4.0,
                "norm_z_min": 0.60,
                "dist_min": 2.5,
                "density_max": 0.15,
                "scale_min": 0.80,
                "scale_max": 1.50,
                "rot_tilt": 0.0,
                "z_offset": tz0,
            },
        },
    ]

    for cfg in biome_scatter_configs:
        obj_name = cfg["name"]
        sc_mesh = cfg["mesh_source"].copy()
        sc_mesh.name = f"{obj_name}_Mesh"
        sc_mesh.shade_smooth()
        for p in sc_mesh.polygons:
            p.use_smooth = True
        sc_obj = bpy.data.objects.get(obj_name)
        if not sc_obj:
            sc_obj = bpy.data.objects.new(obj_name, sc_mesh)
            collection_flora.objects.link(sc_obj)
        else:
            sc_obj.data = sc_mesh
        sc_obj.location = (0.0, 0.0, tz0)
        setup_geometry_nodes_scatter(
            sc_obj, terrain_obj, cfg["proto"], cfg["biome"], **cfg["kwargs"]
        )
        placed_objects.append(sc_obj)

    # -------------------------------------------------------------------------
    # PART B: Landmark Exemplar Instances (Dense realistic diorama population)
    # -------------------------------------------------------------------------
    # 1. Alpine & Ridge Conifers (Spruce Pines & Golden Larches)
    c_count = 0
    l_count = 0
    attempts = 0

    # 1a. Northwest Forest Ridge (-72 <= x <= -20, -10 <= y <= 45)
    while (c_count < 90 or l_count < 30) and attempts < 600:
        attempts += 1
        x = random.uniform(-72.0, -22.0)
        y = random.uniform(-10.0, 45.0)
        z = height_func(x, y)
        d_lake = lake_dist_func(x, y)
        slope = slope_func(x, y)
        if 4.8 <= z <= 14.5 and d_lake > 15.0 and slope < 48.0:
            if random.random() < 0.72 and c_count < 90:
                obj = bpy.data.objects.new(f"Flora_Conifer_{c_count:03d}", m_conifer)
                c_count += 1
            elif l_count < 30:
                obj = bpy.data.objects.new(f"Flora_Larch_{l_count:03d}", m_larch)
                l_count += 1
            else:
                continue
            obj.location = (x, y, z)
            s = random.uniform(0.75, 1.45)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)

    # 1b. Eastern Hillside Ridge (25 <= x <= 70, 8 <= y <= 50)
    attempts = 0
    while (c_count < 118 or l_count < 40) and attempts < 500:
        attempts += 1
        x = random.uniform(25.0, 70.0)
        y = random.uniform(8.0, 50.0)
        z = height_func(x, y)
        slope = slope_func(x, y)
        if 5.0 <= z <= 14.5 and slope < 45.0:
            if random.random() < 0.75 and c_count < 118:
                obj = bpy.data.objects.new(f"Flora_Conifer_{c_count:03d}", m_conifer)
                c_count += 1
            elif l_count < 40:
                obj = bpy.data.objects.new(f"Flora_Larch_{l_count:03d}", m_larch)
                l_count += 1
            else:
                continue
            obj.location = (x, y, z)
            s = random.uniform(0.75, 1.40)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)

    # 1c. Mountain Saddle Dwarf Pine Pocket (nestled between Matterhorn peaks)
    sp_count = 0
    attempts = 0
    while sp_count < 14 and attempts < 300:
        attempts += 1
        x = random.uniform(4.0, 16.0)
        y = random.uniform(36.0, 46.0)
        z = height_func(x, y)
        d_riv = river_dist_func(x, y)
        if 13.5 <= z <= 17.5 and d_riv > 2.2:
            obj = bpy.data.objects.new(f"Flora_Conifer_{c_count:03d}", m_conifer)
            c_count += 1
            obj.location = (x, y, z)
            s = random.uniform(0.65, 1.05)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((random.uniform(-0.04, 0.04), random.uniform(-0.04, 0.04), random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            sp_count += 1

    # 1d. Alpine High Mountain Terraces (Tussock grass)
    t_count = 0
    attempts = 0
    while t_count < 30 and attempts < 500:
        attempts += 1
        x = random.uniform(-65.0, 65.0)
        y = random.uniform(25.0, 75.0)
        z = height_func(x, y)
        if z >= 14.0:
            obj = bpy.data.objects.new(f"Flora_Tussock_{t_count:03d}", m_tussock)
            obj.location = (x, y, z)
            s = random.uniform(0.8, 1.4)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            t_count += 1

    # 2. Lowland & Valley Biome: Broadleaf Oaks clustered along river and knolls
    b_count = 0
    attempts = 0
    while b_count < 22 and attempts < 600:
        attempts += 1
        x = random.uniform(-6.0, 22.0)
        y = random.uniform(-30.0, 2.0)
        z = height_func(x, y)
        d_lake = lake_dist_func(x, y)
        d_bay = bay_dist_func(x, y)
        d_riv = river_dist_func(x, y)
        slope = slope_func(x, y)
        d_vil = math.hypot(x - (-2.0), y - (-14.0))
        if 4.8 <= z <= 8.5 and d_lake > 16.0 and d_bay > 15.0 and d_riv > 3.0 and slope < 22.0 and d_vil > 14.0:
            obj = bpy.data.objects.new(f"Flora_Broadleaf_{b_count:03d}", m_broad)
            obj.location = (x, y, z)
            s = random.uniform(0.80, 1.30)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            b_count += 1

    # 3. 3D Granite & River Boulders (Riverbed, Cascades, Waterfall Lip, Lake Shore)
    rk_count = 0
    attempts = 0
    while rk_count < 42 and attempts < 500:
        attempts += 1
        mode = random.choice(["river", "lake", "cliff", "scree"])
        if mode == "river":
            x_b = random.uniform(-12.0, 24.0)
            y_b = random.uniform(-40.0, 42.0)
            if river_dist_func(x_b, y_b) > 4.5:
                continue
        elif mode == "lake":
            ang_b = random.uniform(0.0, 2.0 * math.pi)
            r_b = (21.0 + 5.0 * math.cos(ang_b - 0.4) + 3.2 * math.sin(2.0 * ang_b)) * random.uniform(0.95, 1.15)
            x_b = -18.0 + r_b * math.cos(ang_b)
            y_b = -6.0 + r_b * math.sin(ang_b)
        elif mode == "cliff":
            y_b = random.uniform(-65.0, 0.0)
            x_b = (36.0 + 0.65 * y_b + 4.5 * math.sin(y_b * 0.08)) + random.uniform(-2.0, 4.0)
        else:
            x_b = random.uniform(-40.0, 40.0)
            y_b = random.uniform(25.0, 65.0)
        z_b = height_func(x_b, y_b)
        if z_b >= 0.5:
            obj = bpy.data.objects.new(f"Flora_Boulder_{rk_count:03d}", m_boulder)
            obj.location = (x_b, y_b, z_b)
            s = random.uniform(0.65, 1.65)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            rk_count += 1

    # 4. Aquatic & Riparian Biome: Reeds along Organic Lake & Pond Shores
    r_count = 0
    # A. Lake Shore reeds
    for _ in range(35):
        ang = random.uniform(0.0, 2.0 * math.pi)
        r_sh = (21.0 + 5.0 * math.cos(ang - 0.4) + 3.2 * math.sin(2.0 * ang) + 2.0 * math.cos(3.0 * ang + 0.8))
        rad = r_sh * random.uniform(0.96, 1.12)
        px = -18.0 + rad * math.cos(ang)
        py = -6.0 + rad * math.sin(ang)
        pz = height_func(px, py)
        if 4.2 <= pz <= 6.2:
            obj = bpy.data.objects.new(f"Flora_Reed_{r_count:03d}", m_reed)
            obj.location = (px, py, pz)
            s = random.uniform(0.70, 1.20)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            r_count += 1

    # B. Wetland Pond reeds ("Ao" at 18, -5)
    for _ in range(20):
        ang = random.uniform(0.0, 2.0 * math.pi)
        r_psh = 9.2 + 1.5 * math.cos(2.0 * ang) + 1.0 * math.sin(3.0 * ang + 0.5)
        rad = r_psh * random.uniform(0.96, 1.14)
        px = 18.0 + rad * math.cos(ang)
        py = -5.0 + rad * math.sin(ang)
        pz = height_func(px, py)
        if 4.5 <= pz <= 6.0:
            obj = bpy.data.objects.new(f"Flora_Reed_{r_count:03d}", m_reed)
            obj.location = (px, py, pz)
            s = random.uniform(0.70, 1.20)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            r_count += 1

    # Floating Water Lilies in Central Lake (Z = 4.52m) and Wetland Pond (Z = 4.87m)
    l_count = 0
    # Central Lake lilies
    for _ in range(20):
        ang = random.uniform(0.0, 2.0 * math.pi)
        rad = random.uniform(3.0, 16.0)
        px = -18.0 + rad * math.cos(ang)
        py = -6.0 + rad * math.sin(ang)
        obj = bpy.data.objects.new(f"Flora_Lily_{l_count:03d}", m_lily)
        obj.location = (px, py, 4.52)
        s = random.uniform(0.85, 1.40)
        obj.scale = (s, s, s)
        obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
        collection_flora.objects.link(obj)
        placed_objects.append(obj)
        l_count += 1

    # Wetland Pond lilies ("Ao" at 18, -5, Z=4.87m)
    for _ in range(8):
        ang = random.uniform(0.0, 2.0 * math.pi)
        rad = random.uniform(1.5, 6.0)
        px = 18.0 + rad * math.cos(ang)
        py = -5.0 + rad * math.sin(ang)
        obj = bpy.data.objects.new(f"Flora_Lily_{l_count:03d}", m_lily)
        obj.location = (px, py, 4.87)
        s = random.uniform(0.85, 1.30)
        obj.scale = (s, s, s)
        obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
        collection_flora.objects.link(obj)
        placed_objects.append(obj)
        l_count += 1

    # 5. Coastal Marine Bay: Submerged Coral Reef Mounds (Z <= -0.5m)
    cr_count = 0
    attempts = 0
    while cr_count < 25 and attempts < 400:
        attempts += 1
        cx_s = random.uniform(26.0, 72.0)
        cy_s = random.uniform(-75.0, -15.0)
        cz_s = height_func(cx_s, cy_s)
        if cz_s <= -0.5:
            obj = bpy.data.objects.new(f"Flora_Coral_{cr_count:03d}", m_coral)
            obj.location = (cx_s, cy_s, cz_s)
            s = random.uniform(0.9, 1.8)
            obj.scale = (s, s, s)
            obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
            collection_flora.objects.link(obj)
            placed_objects.append(obj)
            cr_count += 1

    # 6. Subterranean Cave Biome: Bioluminescent Mushrooms (Z <= 0.0m)
    m_count = 0
    cc = cave_bounds.get("center", (12.0, 12.0, -4.5))
    floor_z = cave_bounds.get("floor_z", -7.0)
    for _ in range(28):
        ang = random.uniform(0.0, 2.0 * math.pi)
        rad = random.uniform(2.0, 12.0)
        sx = cc[0] + rad * math.cos(ang)
        sy = cc[1] + rad * math.sin(ang)
        sz = floor_z
        obj = bpy.data.objects.new(f"Flora_CaveMushroom_{m_count:03d}", m_shroom)
        obj.location = (sx, sy, sz)
        s = random.uniform(0.8, 1.5)
        obj.scale = (s, s, s)
        obj.rotation_euler = Euler((0.0, 0.0, random.uniform(0.0, 2.0 * math.pi)))
        collection_flora.objects.link(obj)
        placed_objects.append(obj)
        m_count += 1

    if hasattr(context, "view_layer") and context.view_layer:
        context.view_layer.update()

    return placed_objects


# Backward compatibility alias
distribute_flora = generate_and_distribute_flora


"""Procedural 3D Botanical Engine - Part 2 (Ancient Royal Oak)."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# Ensure repository root is in sys.path for importing build_engine_part1
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_engine_part1 import (
    add_curved_tube,
    add_foliage_clump,
    apply_smooth_and_materials,
    clean_scene,
    create_pbr_bark_material,
    create_pbr_foliage_material,
    save_and_export,
)

# -----------------------------------------------------------------------------
# 1. Ancient Royal Oak (Sồi Cổ Thụ Hoàng Gia - canopy_ancient_oak)
# -----------------------------------------------------------------------------


def build_ancient_oak():
    clean_scene()
    mat_bark = create_pbr_bark_material("M_Oak_Bark_Scan", (0.15, 0.10, 0.06, 1.0), roughness=0.92, bump_strength=0.60)
    mat_leaves = create_pbr_foliage_material("M_Oak_Leaves_SSS", (0.08, 0.35, 0.09, 1.0), sss_color=(0.18, 0.52, 0.06, 1.0), sss_weight=0.52, roughness=0.30)

    mesh = bpy.data.meshes.new("Flora_Ancient_Oak_Mesh")
    verts, faces, mat_idx = [], [], []

    # A. Muscular fluted trunk with 6 buttress root flares
    slices = 18
    radial = 20
    base_t = len(verts)
    v_bot = base_t
    verts.append((0.0, 0.0, 0.0))
    ring_start = len(verts)

    for s in range(slices):
        t = s / (slices - 1.0)
        z = t * 7.8
        cx = 0.65 * math.sin(t * 1.6)
        cy = 0.40 * (1.0 - math.cos(t * 1.4))
        flare = 1.95 * math.exp(-t * 3.8)
        base_r = 1.25 * (1.0 - 0.42 * t) + flare
        for r_i in range(radial):
            ang = r_i * 2.0 * math.pi / radial
            buttress = 0.55 * flare * (math.sin(ang * 3.0) ** 2) if t < 0.45 else 0.0
            flute = 0.08 * math.cos(ang * 6.0) * (1.0 - 0.5 * t)
            r_act = base_r + buttress + flute
            verts.append((cx + r_act * math.cos(ang), cy + r_act * math.sin(ang), z))

    # Bottom cap
    for r_i in range(radial):
        nxt = (r_i + 1) % radial
        faces.append((v_bot, ring_start + nxt, ring_start + r_i))
        mat_idx.append(0)

    # Trunk quads
    for s in range(slices - 1):
        r1 = ring_start + s * radial
        r2 = ring_start + (s + 1) * radial
        for r_i in range(radial):
            nxt = (r_i + 1) % radial
            faces.append((r1 + r_i, r1 + nxt, r2 + nxt, r2 + r_i))
            mat_idx.append(0)

    # Top cap
    v_top = len(verts)
    last_z = 7.8
    verts.append((0.65 * math.sin(1.6), 0.40 * (1.0 - math.cos(1.4)), last_z + 0.1))
    last_ring = ring_start + (slices - 1) * radial
    for r_i in range(radial):
        nxt = (r_i + 1) % radial
        faces.append((v_top, last_ring + r_i, last_ring + nxt))
        mat_idx.append(0)

    # B. 5 Major twisted boughs and 10 secondary branches
    trunk_apex = Vector((0.65 * math.sin(1.6), 0.40 * (1.0 - math.cos(1.4)), 6.8))
    bough_configs = [
        (Vector((4.2, 2.6, 9.2)), 0.65, 0.25, [Vector((5.8, 3.8, 9.8)), Vector((5.2, 1.2, 9.0))]),
        (Vector((-3.8, 3.2, 9.5)), 0.60, 0.24, [Vector((-5.2, 4.5, 10.0)), Vector((-4.6, 1.8, 9.2))]),
        (Vector((3.0, -3.8, 8.8)), 0.58, 0.22, [Vector((4.2, -5.2, 9.2)), Vector((1.8, -4.8, 8.5))]),
        (Vector((-3.2, -3.2, 9.0)), 0.55, 0.22, [Vector((-4.5, -4.6, 9.5)), Vector((-2.2, -4.5, 8.6))]),
        (Vector((0.2, 0.2, 11.2)), 0.70, 0.28, [Vector((1.8, 0.8, 12.5)), Vector((-1.6, 1.2, 12.2))]),
    ]

    for p_end, r_st, r_en, sub_branches in bough_configs:
        # Primary bough spline
        mid_pt = trunk_apex.lerp(p_end, 0.5) + Vector((0.35, -0.2, -0.4))
        pts = [trunk_apex, trunk_apex.lerp(mid_pt, 0.5), mid_pt, mid_pt.lerp(p_end, 0.5), p_end]
        radii = [r_st * (1.0 - 0.7 * (i/4.0)) for i in range(5)]
        add_curved_tube(verts, faces, mat_idx, pts, radii, rad_segs=8, mat_id=0, cap_start=False, cap_end=True)

        # Secondary limbs
        for sub_p in sub_branches:
            sub_mid = p_end.lerp(sub_p, 0.5) + Vector((-0.2, 0.2, 0.15))
            sub_pts = [p_end, sub_mid, sub_p]
            sub_radii = [r_en, r_en * 0.65, r_en * 0.35]
            add_curved_tube(verts, faces, mat_idx, sub_pts, sub_radii, rad_segs=6, mat_id=0, cap_start=False, cap_end=True)

    # C. 26 Volumetric foliage clumps forming a magnificent dense crown
    clump_positions = [
        # Central crown dome
        (Vector((0.0, 0.0, 13.5)), 3.6, 3.6, 2.5),
        (Vector((0.0, 0.0, 15.0)), 2.8, 2.8, 2.0),
        # Outer spreading lobes
        (Vector((4.5, 2.8, 10.2)), 3.2, 2.8, 2.2),
        (Vector((-4.0, 3.4, 10.5)), 3.0, 2.8, 2.2),
        (Vector((3.2, -4.0, 9.8)), 3.1, 2.9, 2.2),
        (Vector((-3.5, -3.5, 10.2)), 3.0, 2.8, 2.1),
        (Vector((6.0, 3.8, 10.2)), 2.4, 2.2, 1.8),
        (Vector((5.4, 1.0, 9.4)), 2.3, 2.1, 1.7),
        (Vector((-5.4, 4.6, 10.5)), 2.4, 2.2, 1.8),
        (Vector((-4.8, 1.6, 9.6)), 2.3, 2.1, 1.7),
        (Vector((4.4, -5.4, 9.5)), 2.3, 2.1, 1.7),
        (Vector((1.6, -5.0, 8.8)), 2.2, 2.0, 1.6),
        (Vector((-4.6, -4.8, 9.8)), 2.3, 2.1, 1.7),
        (Vector((-2.0, -4.6, 9.0)), 2.2, 2.0, 1.6),
        (Vector((2.0, 1.0, 13.0)), 2.6, 2.4, 2.0),
        (Vector((-1.8, 1.4, 12.8)), 2.5, 2.3, 1.9),
        (Vector((1.2, 3.8, 10.5)), 2.5, 2.4, 1.9),
        (Vector((-1.4, -2.2, 11.5)), 2.6, 2.4, 1.9),
        (Vector((2.2, -1.8, 11.8)), 2.5, 2.3, 1.8),
        (Vector((-2.5, 2.0, 11.8)), 2.5, 2.3, 1.8),
    ]
    for c_pos, rx, ry, rz in clump_positions:
        add_foliage_clump(verts, faces, mat_idx, c_pos, rx, ry, rz, lat_steps=7, lon_steps=10, bump_freq=3.0, bump_amp=0.16, mat_id=1)

    mesh.from_pydata(verts, [], faces)
    apply_smooth_and_materials(mesh, [mat_bark, mat_leaves])
    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = mat_idx[idx]

    obj = bpy.data.objects.new("Flora_Ancient_Oak", mesh)
    bpy.context.scene.collection.objects.link(obj)

    save_and_export(
        obj,
        "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_ancient_oak.blend",
        "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_ancient_oak.glb"
    )
    return obj

print('Ancient oak defined.')

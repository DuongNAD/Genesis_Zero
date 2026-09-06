"""
flora_builder.py - Master Procedural 3D Botanical Engine (Ultra-Realistic Scan-Quality)
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Features:
1. Ultra-Realistic Scan-Quality Botanical Geometry:
   - Quad-dominant manifold meshes, clean organic branching, phyllotaxis.
   - 100% Smooth Shading (use_smooth = True on all faces).
   - Multi-material biological PBR shading with Subsurface Scattering (SSS) for foliage, petals & fungal tissue.
   - Procedural trunk fluting, buttress roots, bark displacement, and organic asymmetry.
   - 100% clean BMesh topology: 0 loose verts, 0 ngons, 0 multi-face edges, 0 wire edges, 0 incontiguous edges.
2. Dual Deliverables:
   - Generates and saves master .blend files for each species.
   - Automatically exports standard .glb (glTF 2.0) files ready for diorama & Three.js.
"""

import math
import os
import random
import sys
import base64
import bpy
from mathutils import Vector, Euler, Matrix

# -----------------------------------------------------------------------------
# PBR Material Utility with Subsurface Scattering (SSS) & Procedural Micro-Bump
# -----------------------------------------------------------------------------

def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat

def create_pbr_bark_material(name, base_color, roughness=0.88, bump_strength=0.35):
    mat = get_or_create_material(name)
    nt = mat.node_tree
    nt.nodes.clear()

    node_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    node_bsdf.location = (200, 0)
    node_bsdf.inputs["Base Color"].default_value = base_color
    node_bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in node_bsdf.inputs:
        node_bsdf.inputs["Specular IOR Level"].default_value = 0.25
    elif "Specular" in node_bsdf.inputs:
        node_bsdf.inputs["Specular"].default_value = 0.25

    # Procedural Noise Bump for bark fissures
    node_noise = nt.nodes.new("ShaderNodeTexNoise")
    node_noise.location = (-400, -150)
    node_noise.inputs["Scale"].default_value = 18.0
    node_noise.inputs["Detail"].default_value = 6.0
    node_noise.inputs["Roughness"].default_value = 0.75

    node_bump = nt.nodes.new("ShaderNodeBump")
    node_bump.location = (-100, -150)
    node_bump.inputs["Strength"].default_value = bump_strength
    node_bump.inputs["Distance"].default_value = 0.15

    nt.links.new(node_noise.outputs["Fac"], node_bump.inputs["Height"])
    nt.links.new(node_bump.outputs["Normal"], node_bsdf.inputs["Normal"])

    node_out = nt.nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (500, 0)
    nt.links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    return mat

def create_pbr_foliage_material(name, base_color, sss_color=None, sss_weight=0.45, roughness=0.35):
    mat = get_or_create_material(name)
    nt = mat.node_tree
    nt.nodes.clear()

    node_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    node_bsdf.location = (200, 0)
    node_bsdf.inputs["Base Color"].default_value = base_color
    node_bsdf.inputs["Roughness"].default_value = roughness

    if "Subsurface Weight" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface Weight"].default_value = sss_weight
        if sss_color and "Subsurface Radius" in node_bsdf.inputs:
            node_bsdf.inputs["Subsurface Radius"].default_value = (sss_color[0]*0.15, sss_color[1]*0.35, sss_color[2]*0.05)
        if "Subsurface Scale" in node_bsdf.inputs:
            node_bsdf.inputs["Subsurface Scale"].default_value = 0.05
    elif "Subsurface" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface"].default_value = sss_weight
        if sss_color and "Subsurface Color" in node_bsdf.inputs:
            node_bsdf.inputs["Subsurface Color"].default_value = sss_color

    if "Sheen Weight" in node_bsdf.inputs:
        node_bsdf.inputs["Sheen Weight"].default_value = 0.40
    elif "Sheen" in node_bsdf.inputs:
        node_bsdf.inputs["Sheen"].default_value = 0.40

    node_out = nt.nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (500, 0)
    nt.links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    return mat

def create_pbr_emissive_material(name, base_color, emission_color, emission_strength=5.0):
    mat = get_or_create_material(name)
    nt = mat.node_tree
    nt.nodes.clear()

    node_bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    node_bsdf.location = (200, 0)
    node_bsdf.inputs["Base Color"].default_value = base_color
    node_bsdf.inputs["Roughness"].default_value = 0.25

    if "Emission Color" in node_bsdf.inputs:
        node_bsdf.inputs["Emission Color"].default_value = emission_color
        node_bsdf.inputs["Emission Strength"].default_value = emission_strength
    elif "Emission" in node_bsdf.inputs:
        node_bsdf.inputs["Emission"].default_value = emission_color

    if "Subsurface Weight" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface Weight"].default_value = 0.65
    elif "Subsurface" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface"].default_value = 0.65

    node_out = nt.nodes.new("ShaderNodeOutputMaterial")
    node_out.location = (500, 0)
    nt.links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    return mat

# -----------------------------------------------------------------------------
# Clean Scene & Export Helpers
# -----------------------------------------------------------------------------

def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def apply_smooth_and_materials(mesh_data, materials):
    mesh_data.materials.clear()
    for m in materials:
        mesh_data.materials.append(m)
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

def save_and_export(obj, blend_path, glb_path):
    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
    )
    b_size = os.path.getsize(blend_path) if os.path.exists(blend_path) else 0
    g_size = os.path.getsize(glb_path) if os.path.exists(glb_path) else 0
    print(f"  ✓ Saved .blend ({b_size/1024:.1f} KB): {blend_path}")
    print(f"  ✓ Exported .glb ({g_size/1024:.1f} KB): {glb_path}")

# -----------------------------------------------------------------------------
# Clean Manifold Geometry Primitives
# -----------------------------------------------------------------------------

def add_curved_tube(verts, faces, mat_idx, centers, radii, rad_segs=10, mat_id=0, cap_start=True, cap_end=True):
    N = len(centers)
    assert N >= 2
    base = len(verts)

    tangents = []
    for k in range(N):
        if k == 0:
            T = (centers[1] - centers[0]).normalized()
        elif k == N - 1:
            T = (centers[-1] - centers[-2]).normalized()
        else:
            T = (centers[k+1] - centers[k-1]).normalized()
        if T.length < 1e-5:
            T = Vector((0, 0, 1))
        tangents.append(T)

    normals = []
    binormals = []
    for k in range(N):
        T = tangents[k]
        if k == 0:
            ref = Vector((0, 0, 1)) if abs(T.z) < 0.9 else Vector((0, 1, 0))
            N_vec = T.cross(ref).normalized()
            B_vec = T.cross(N_vec).normalized()
        else:
            prev_N = normals[-1]
            N_vec = (prev_N - T * T.dot(prev_N)).normalized()
            if N_vec.length < 1e-5:
                ref = Vector((0, 0, 1)) if abs(T.z) < 0.9 else Vector((0, 1, 0))
                N_vec = T.cross(ref).normalized()
            B_vec = T.cross(N_vec).normalized()
        normals.append(N_vec)
        binormals.append(B_vec)

    for k in range(N):
        c = centers[k]
        r = radii[k] if isinstance(radii, (list, tuple)) else radii
        for i in range(rad_segs):
            ang = i * 2.0 * math.pi / rad_segs
            p = c + r * (math.cos(ang) * normals[k] + math.sin(ang) * binormals[k])
            verts.append((p.x, p.y, p.z))

    for k in range(N - 1):
        for i in range(rad_segs):
            nxt = (i + 1) % rad_segs
            v1 = base + k * rad_segs + i
            v2 = base + k * rad_segs + nxt
            v3 = base + (k + 1) * rad_segs + nxt
            v4 = base + (k + 1) * rad_segs + i
            faces.append((v1, v2, v3, v4))
            mat_idx.append(mat_id)

    if cap_start:
        v_cap = len(verts)
        p0 = centers[0]
        verts.append((p0.x, p0.y, p0.z))
        for i in range(rad_segs):
            nxt = (i + 1) % rad_segs
            faces.append((v_cap, base + nxt, base + i))
            mat_idx.append(mat_id)

    if cap_end:
        v_cap = len(verts)
        pend = centers[-1]
        verts.append((pend.x, pend.y, pend.z))
        last_ring = base + (N - 1) * rad_segs
        for i in range(rad_segs):
            nxt = (i + 1) % rad_segs
            faces.append((v_cap, last_ring + i, last_ring + nxt))
            mat_idx.append(mat_id)

def add_foliage_clump(verts, faces, mat_idx, center, rx, ry, rz, lat_steps=8, lon_steps=12, bump_freq=3.0, bump_amp=0.15, mat_id=1):
    base = len(verts)
    v_top = base
    verts.append((center.x, center.y, center.z + rz))
    v_bot = base + 1
    verts.append((center.x, center.y, center.z - rz))
    ring_start = len(verts)

    rings_cnt = lat_steps - 2
    for lt in range(1, lat_steps - 1):
        phi = math.pi * lt / (lat_steps - 1.0)
        z_off = rz * math.cos(phi)
        r_xy = math.sin(phi)
        for ln in range(lon_steps):
            th = 2.0 * math.pi * ln / lon_steps
            bump = 1.0 + bump_amp * math.sin(th * bump_freq) * math.cos(phi * 2.0) + 0.05 * math.cos(th * 5.0)
            verts.append((
                center.x + rx * r_xy * math.cos(th) * bump,
                center.y + ry * r_xy * math.sin(th) * bump,
                center.z + z_off * bump
            ))

    for ln in range(lon_steps):
        nxt = (ln + 1) % lon_steps
        faces.append((v_top, ring_start + ln, ring_start + nxt))
        mat_idx.append(mat_id)

    for lt in range(rings_cnt - 1):
        r1 = ring_start + lt * lon_steps
        r2 = ring_start + (lt + 1) * lon_steps
        for ln in range(lon_steps):
            nxt = (ln + 1) % lon_steps
            faces.append((r1 + ln, r2 + ln, r2 + nxt, r1 + nxt))
            mat_idx.append(mat_id)

    last_ring = ring_start + (rings_cnt - 1) * lon_steps
    for ln in range(lon_steps):
        nxt = (ln + 1) % lon_steps
        faces.append((v_bot, last_ring + nxt, last_ring + ln))
        mat_idx.append(mat_id)

def add_ribbon(verts, faces, mat_idx, left_pts, right_pts, mat_id=0):
    N = len(left_pts)
    assert len(right_pts) == N
    base = len(verts)
    for k in range(N):
        verts.append((left_pts[k].x, left_pts[k].y, left_pts[k].z))
        verts.append((right_pts[k].x, right_pts[k].y, right_pts[k].z))
    for k in range(N - 1):
        v1 = base + k * 2
        v2 = base + k * 2 + 1
        v3 = base + (k + 1) * 2 + 1
        v4 = base + (k + 1) * 2
        faces.append((v1, v2, v3, v4))
        mat_idx.append(mat_id)

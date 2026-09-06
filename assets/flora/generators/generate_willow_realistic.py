"""
Genesis Zero — Ultra-Realistic Botanical 3D Weeping Willow Generator.
Creates a realistic Salix babylonica with:
- Gnarled organic trunk with buttress roots (tapering quad mesh)
- 5 Primary crown boughs + 15 secondary arching branches
- 40 drooping slender weeping twig whips
- 800+ realistic botanical lanceolate willow leaves distributed along the weeping twigs
"""

import math
import random
import os
import bpy
import mathutils


def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def create_materials():
    # 1. Furrowed Bark PBR
    mat_bark = bpy.data.materials.new(name="M_Willow_Bark")
    mat_bark.use_nodes = True
    nodes = mat_bark.node_tree.nodes
    links = mat_bark.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Base Color"].default_value = (0.22, 0.16, 0.12, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85

    tex_noise = nodes.new("ShaderNodeTexNoise")
    tex_noise.location = (-300, 0)
    tex_noise.inputs["Scale"].default_value = 20.0
    tex_noise.inputs["Detail"].default_value = 6.0

    bump = nodes.new("ShaderNodeBump")
    bump.location = (-50, -100)
    bump.inputs["Strength"].default_value = 0.50
    links.new(tex_noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # 2. Translucent Willow Leaf PBR with Subsurface Scattering
    mat_leaf = bpy.data.materials.new(name="M_Willow_Leaf")
    mat_leaf.use_nodes = True
    lnodes = mat_leaf.node_tree.nodes
    llinks = mat_leaf.node_tree.links
    lnodes.clear()

    lbsdf = lnodes.new("ShaderNodeBsdfPrincipled")
    lbsdf.location = (200, 0)
    lbsdf.inputs["Base Color"].default_value = (0.34, 0.56, 0.14, 1.0)
    lbsdf.inputs["Roughness"].default_value = 0.28

    if "Subsurface Weight" in lbsdf.inputs:
        lbsdf.inputs["Subsurface Weight"].default_value = 0.65
        lbsdf.inputs["Subsurface Radius"].default_value = (0.45, 0.70, 0.12)
    elif "Subsurface" in lbsdf.inputs:
        lbsdf.inputs["Subsurface"].default_value = 0.65

    lout = lnodes.new("ShaderNodeOutputMaterial")
    lout.location = (500, 0)
    llinks.new(lbsdf.outputs["BSDF"], lout.inputs["Surface"])

    return mat_bark, mat_leaf


def create_smooth_tube(points_radii, radial_segs=8):
    """Generates continuous quad manifold cylinder along 3D centerline points."""
    verts = []
    faces = []
    n_pts = len(points_radii)

    for i, (p, r) in enumerate(points_radii):
        if i == 0:
            tang = (points_radii[1][0] - p).normalized()
        elif i == n_pts - 1:
            tang = (p - points_radii[i - 1][0]).normalized()
        else:
            tang = (points_radii[i + 1][0] - points_radii[i - 1][0]).normalized()

        up = mathutils.Vector((0, 0, 1))
        if abs(tang.dot(up)) > 0.95:
            up = mathutils.Vector((1, 0, 0))
        norm = tang.cross(up).normalized()
        binorm = tang.cross(norm).normalized()

        for s in range(radial_segs):
            angle = s * 2.0 * math.pi / radial_segs
            offset = norm * (math.cos(angle) * r) + binorm * (math.sin(angle) * r)
            verts.append(p + offset)

    for ring in range(n_pts - 1):
        r1 = ring * radial_segs
        r2 = (ring + 1) * radial_segs
        for s in range(radial_segs):
            nxt = (s + 1) % radial_segs
            faces.append((r1 + s, r1 + nxt, r2 + nxt, r2 + s))

    # Base cap
    base_center = len(verts)
    verts.append(points_radii[0][0])
    for s in range(radial_segs):
        nxt = (s + 1) % radial_segs
        faces.append((base_center, nxt, s))

    # Tip cap
    tip_center = len(verts)
    verts.append(points_radii[-1][0])
    last_r = (n_pts - 1) * radial_segs
    for s in range(radial_segs):
        nxt = (s + 1) % radial_segs
        faces.append((tip_center, last_r + s, last_r + nxt))

    return verts, faces


def create_willow_leaf(origin, direction, length=0.45, width=0.10):
    """Creates a curved 3D lanceolate willow leaf (4 quad faces with central spine fold)."""
    dir_norm = direction.normalized()
    up = mathutils.Vector((0, 0, -1))  # Leaves hang slightly downward
    side = dir_norm.cross(up).normalized() * (width * 0.5)

    p0 = origin
    p1 = origin + dir_norm * (length * 0.35) - mathutils.Vector((0, 0, 0.04))
    p2 = origin + dir_norm * (length * 0.70) - mathutils.Vector((0, 0, 0.10))
    p3 = origin + dir_norm * length - mathutils.Vector((0, 0, 0.16))  # Drooping tip

    # Leaf blade vertices with V-groove fold
    verts = [
        p0,                         # 0: base
        p1 - side * 0.8,            # 1: left edge low
        p1,                         # 2: center spine low
        p1 + side * 0.8,            # 3: right edge low
        p2 - side,                  # 4: left edge mid
        p2,                         # 5: center spine mid
        p2 + side,                  # 6: right edge mid
        p3                          # 7: tip
    ]

    faces = [
        (0, 1, 2),      # Base left triangle
        (0, 2, 3),      # Base right triangle
        (1, 4, 5, 2),   # Blade mid-left quad
        (2, 5, 6, 3),   # Blade mid-right quad
        (4, 7, 5),      # Tip left triangle
        (5, 7, 6)       # Tip right triangle
    ]
    return verts, faces


def generate_realistic_weeping_willow():
    clean_scene()
    random.seed(2026)

    mat_bark, mat_leaf = create_materials()

    all_verts = []
    all_faces = []
    mat_indices = []

    def add_chunk(verts, faces, mat_id):
        offset = len(all_verts)
        all_verts.extend(verts)
        for f in faces:
            all_faces.append(tuple(v + offset for v in f))
            mat_indices.append(mat_id)

    # -------------------------------------------------------------------------
    # 1. Trunk with Root Flairs (Solid, Natural Curvature)
    # -------------------------------------------------------------------------
    trunk_slices = 12
    trunk_pts = []
    for s in range(trunk_slices):
        t = s / (trunk_slices - 1.0)
        z = t * 3.6
        # Gentle natural lean
        cx = 0.65 * (t ** 1.4)
        cy = 0.25 * math.sin(t * 2.2)
        # Buttress base flare
        flare = 0.65 * math.exp(-t * 5.0)
        r = (0.75 - 0.32 * t) + flare
        pos = mathutils.Vector((cx, cy, z))
        trunk_pts.append((pos, r))

    tv, tf = create_smooth_tube(trunk_pts, radial_segs=12)
    add_chunk(tv, tf, 0)

    crown_origin = trunk_pts[-1][0]

    # -------------------------------------------------------------------------
    # 2. Main Crown Boughs (5 Primary Arched Limbs)
    # -------------------------------------------------------------------------
    num_boughs = 5
    twig_anchor_points = []

    for b in range(num_boughs):
        ang = b * (2.0 * math.pi / num_boughs) + random.uniform(-0.15, 0.15)
        reach = 3.8 + random.uniform(-0.3, 0.4)
        peak_z = crown_origin.z + 1.8 + random.uniform(-0.2, 0.3)

        bough_pts = []
        b_segs = 10
        base_r = 0.32
        tip_r = 0.12

        for bs in range(b_segs):
            bt = bs / (b_segs - 1.0)
            bx = crown_origin.x + math.cos(ang) * (reach * bt)
            by = crown_origin.y + math.sin(ang) * (reach * bt)
            # Arch up then curve gently downward at tip
            bz = crown_origin.z * (1.0 - bt) + peak_z * bt - 0.5 * (bt ** 2.2)
            br = base_r * (1.0 - 0.6 * bt)
            bough_pts.append((mathutils.Vector((bx, by, bz)), br))

        bv, bf = create_smooth_tube(bough_pts, radial_segs=8)
        add_chunk(bv, bf, 0)

        # 3 Secondary branches per bough
        for sub in range(3):
            sub_ang = ang + (sub - 1.0) * 0.42 + random.uniform(-0.1, 0.1)
            sub_start = bough_pts[4 + sub][0]
            sub_len = 2.4 + random.uniform(-0.2, 0.3)
            sub_pts = []
            for ss in range(6):
                st = ss / 5.0
                sx = sub_start.x + math.cos(sub_ang) * (sub_len * st)
                sy = sub_start.y + math.sin(sub_ang) * (sub_len * st)
                sz = sub_start.z + 0.3 * st - 0.7 * (st ** 1.6)
                sr = 0.14 * (1.0 - 0.65 * st)
                sub_pts.append((mathutils.Vector((sx, sy, sz)), sr))

            sbv, sbf = create_smooth_tube(sub_pts, radial_segs=6)
            add_chunk(sbv, sbf, 0)
            twig_anchor_points.append(sub_pts[-1][0])

        twig_anchor_points.append(bough_pts[-1][0])

    # -------------------------------------------------------------------------
    # 3. Cascading Weeping Twigs (Slender Hanging Spline Whips)
    # -------------------------------------------------------------------------
    # Add additional anchors around the canopy perimeter
    perimeter_whips = 35
    all_whips = list(twig_anchor_points)
    for p in range(perimeter_whips):
        ang = p * 2.0 * math.pi / perimeter_whips + random.uniform(-0.08, 0.08)
        rad = 3.4 + random.uniform(-0.6, 0.8)
        px = crown_origin.x + math.cos(ang) * rad
        py = crown_origin.y + math.sin(ang) * rad
        pz = crown_origin.z + 1.2 + random.uniform(-0.4, 0.5)
        all_whips.append(mathutils.Vector((px, py, pz)))

    leaf_count = 0

    for whip_idx, start_pt in enumerate(all_whips):
        drop_h = random.uniform(3.4, 4.5)
        whip_segs = 12
        whip_pts = []
        tang_angle = random.uniform(0, math.pi * 2)

        for ws in range(whip_segs):
            wt = ws / (whip_segs - 1.0)
            wz = start_pt.z - drop_h * wt
            # Subtle breeze curl sway
            sway = 0.28 * math.sin(wt * 3.2 + whip_idx)
            wx = start_pt.x + math.cos(tang_angle) * (0.4 * wt + sway)
            wy = start_pt.y + math.sin(tang_angle) * (0.4 * wt + sway)
            w_r = max(0.012, 0.035 * (1.0 - 0.7 * wt))
            whip_pts.append((mathutils.Vector((wx, wy, wz)), w_r))

        wv, wf = create_smooth_tube(whip_pts, radial_segs=4)
        add_chunk(wv, wf, 0)

        # ---------------------------------------------------------------------
        # 4. Realistic Botanical Leaves Along Each Hanging Twig
        # ---------------------------------------------------------------------
        # Distribute 14-20 alternating leaves along the hanging twig
        for ls in range(2, whip_segs - 1):
            pt = whip_pts[ls][0]
            # Next segment tangent
            tang = (whip_pts[ls + 1][0] - whip_pts[ls - 1][0]).normalized()

            # 2 alternating leaves per node
            for side_mult in [-1, 1]:
                leaf_ang = (ls * 1.618 + (1 if side_mult > 0 else 0) * math.pi)
                out_dir = mathutils.Vector((math.cos(leaf_ang), math.sin(leaf_ang), -0.45)).normalized()

                lv, lf = create_willow_leaf(
                    origin=pt,
                    direction=out_dir,
                    length=random.uniform(0.38, 0.52),
                    width=random.uniform(0.08, 0.12)
                )
                add_chunk(lv, lf, 1)
                leaf_count += 1

    # -------------------------------------------------------------------------
    # 5. Assemble Mesh, Apply Materials & Export
    # -------------------------------------------------------------------------
    mesh = bpy.data.meshes.new("Flora_Weeping_Willow_Mesh")
    mesh.from_pydata(all_verts, [], all_faces)

    mesh.materials.append(mat_bark)
    mesh.materials.append(mat_leaf)
    mesh.update(calc_edges=True)
    mesh.shade_smooth()

    for idx, poly in enumerate(mesh.polygons):
        poly.use_smooth = True
        poly.material_index = mat_indices[idx]

    obj = bpy.data.objects.new("Flora_Weeping_Willow", mesh)
    bpy.context.scene.collection.objects.link(obj)

    blend_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_weeping_willow.blend"
    glb_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_weeping_willow.glb"

    os.makedirs(os.path.dirname(blend_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved BLEND: {blend_path}")

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_yup=True
    )
    print(f"Exported GLB: {glb_path} ({os.path.getsize(glb_path) / 1024:.1f} KB, with {leaf_count} individual botanical leaves)")
    return obj


if __name__ == "__main__":
    generate_realistic_weeping_willow()

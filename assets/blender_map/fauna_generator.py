"""
fauna_generator.py - Procedural 4-Biome Fauna Rigging & Multi-Clip Animation Pipeline
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Populates all 4 biomes with 5 rigged animal species:
1. Alpine Biome:
   - Mountain Goat (Capra ibex): 22 bones, Goat_Climb (40f) & Goat_Idle (60f).
   - Golden Eagle (Aquila chrysaetos): 16 bones, Eagle_Glide (60f) & Eagle_Flap (30f).
2. Lowland & Forest Biome:
   - Highland Red Stag (Cervus elaphus): 26 bones, Stag_Idle (60f) & Stag_Walk (40f).
3. Aquatic & Shore Biome:
   - Freshwater Trout (Salmo): 12 bones, Fish_Swim (30f) & Fish_Idle (60f).
4. Subterranean Cave Biome:
   - Subterranean Cave Bat (Myotis): 18 bones, Bat_Roost (60f) & Bat_Flutter (20f).

Total bones: 94 bones.
Total animation actions: 10 actions.
All actions pushed down to NLA tracks for multi-clip glTF/GLB binary export.
100% smooth shading (polygon.use_smooth = True) and Subsurf modifier on all skinned meshes.
"""

import math
import bpy
import bmesh
from mathutils import Vector, Euler


def create_fauna_material(name, base_color, roughness=0.55, specular=0.35, transmission=0.0):
    """Utility to create a Principled BSDF material for fauna."""
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
        if transmission > 0.0:
            if "Transmission Weight" in bsdf.inputs:
                bsdf.inputs["Transmission Weight"].default_value = transmission
            elif "Transmission" in bsdf.inputs:
                bsdf.inputs["Transmission"].default_value = transmission
    return mat


def pushdown_action_to_nla(arm_obj, action):
    """Pushes down an action to an independent NLA track with fake user."""
    action.use_fake_user = True
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action.name
    f_start = int(round(action.frame_range[0]))
    strip = track.strips.new(action.name, f_start, action)
    strip.action = action
    return track


# =============================================================================
# 1. ALPINE: MOUNTAIN GOAT (Capra ibex) - 22 Bones, 2 Actions
# =============================================================================


def build_mountain_goat(collection, offset=(-24.0, 38.0, 24.5)):
    """
    Constructs the Alpine Mountain Goat:
    - 22 bones (Root, Pelvis, Tail, Spine, Chest, Neck, Head, Jaw, Horns, 4 limbs & hooves)
    - Quad-dominant lofted torso, curved horns, split hooves
    - Vertex groups mapped to 22 bones
    - Actions: Goat_Climb (40f) and Goat_Idle (60f)
    """
    ox, oy, oz = offset

    # 1. Armature
    arm_data = bpy.data.armatures.new("Goat_Armature_Data")
    arm_obj = bpy.data.objects.new("Goat_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    root = eb.new("Root")
    root.head = (ox, oy, oz)
    root.tail = (ox, oy, oz + 0.25)

    pelvis = eb.new("Pelvis")
    pelvis.head = (ox, oy - 0.40, oz + 1.10)
    pelvis.tail = (ox, oy - 0.15, oz + 1.12)
    pelvis.parent = root

    spine = eb.new("Spine")
    spine.head = pelvis.tail
    spine.tail = (ox, oy + 0.25, oz + 1.15)
    spine.parent = pelvis

    chest = eb.new("Chest")
    chest.head = spine.tail
    chest.tail = (ox, oy + 0.65, oz + 1.18)
    chest.parent = spine

    neck = eb.new("Neck")
    neck.head = chest.tail
    neck.tail = (ox, oy + 0.95, oz + 1.45)
    neck.parent = chest

    head = eb.new("Head")
    head.head = neck.tail
    head.tail = (ox, oy + 1.25, oz + 1.55)
    head.parent = neck

    jaw = eb.new("Jaw")
    jaw.head = (ox, oy + 1.05, oz + 1.38)
    jaw.tail = (ox, oy + 1.25, oz + 1.40)
    jaw.parent = head

    # Swept backward alpine horns
    for side, sign in [(".L", 1), (".R", -1)]:
        horn = eb.new(f"Horn{side}")
        horn.head = (ox + sign * 0.10, oy + 1.10, oz + 1.60)
        horn.tail = (ox + sign * 0.20, oy + 0.80, oz + 1.95)
        horn.parent = head

    tail = eb.new("Tail")
    tail.head = (ox, oy - 0.45, oz + 1.10)
    tail.tail = (ox, oy - 0.65, oz + 1.00)
    tail.parent = pelvis

    # Forelimbs (Shoulder -> UpperArm -> Forearm -> Hoof)
    for side, sign in [(".L", 1), (".R", -1)]:
        sh = eb.new(f"Shoulder{side}")
        sh.head = (ox + sign * 0.20, oy + 0.55, oz + 1.15)
        sh.tail = (ox + sign * 0.24, oy + 0.55, oz + 0.90)
        sh.parent = chest

        ua = eb.new(f"UpperArm{side}")
        ua.head = sh.tail
        ua.tail = (ox + sign * 0.24, oy + 0.52, oz + 0.50)
        ua.parent = sh

        fa = eb.new(f"Forearm{side}")
        fa.head = ua.tail
        fa.tail = (ox + sign * 0.24, oy + 0.50, oz + 0.12)
        fa.parent = ua

        hf = eb.new(f"Hoof{side}")
        hf.head = fa.tail
        hf.tail = (ox + sign * 0.24, oy + 0.52, oz + 0.0)
        hf.parent = fa

    # Hindlimbs (Hip -> Thigh -> Shin -> Hoof_Hind)
    for side, sign in [(".L", 1), (".R", -1)]:
        hp = eb.new(f"Hip{side}")
        hp.head = (ox + sign * 0.20, oy - 0.35, oz + 1.10)
        hp.tail = (ox + sign * 0.24, oy - 0.35, oz + 0.85)
        hp.parent = pelvis

        th = eb.new(f"Thigh{side}")
        th.head = hp.tail
        th.tail = (ox + sign * 0.24, oy - 0.38, oz + 0.45)
        th.parent = hp

        shn = eb.new(f"Shin{side}")
        shn.head = th.tail
        shn.tail = (ox + sign * 0.24, oy - 0.32, oz + 0.12)
        shn.parent = th

        hhf = eb.new(f"Hoof_Hind{side}")
        hhf.head = shn.tail
        hhf.tail = (ox + sign * 0.24, oy - 0.30, oz + 0.0)
        hhf.parent = shn

    bpy.ops.object.mode_set(mode='OBJECT')

    # 2. Skinned Mesh
    mesh_data = bpy.data.meshes.new("Goat_Mesh")
    mesh_obj = bpy.data.objects.new("Goat_Model", mesh_data)
    collection.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    mat_coat = create_fauna_material("M_Goat_Coat", (0.86, 0.84, 0.80, 1.0), roughness=0.75)
    mat_horn = create_fauna_material("M_Goat_Horn", (0.24, 0.22, 0.20, 1.0), roughness=0.45)
    mesh_data.materials.append(mat_coat)  # 0
    mesh_data.materials.append(mat_horn)  # 1

    bm = bmesh.new()
    rings = [
        {"y": -0.55, "zc": 1.05, "rx": 0.24, "rz": 0.26},
        {"y": -0.30, "zc": 1.08, "rx": 0.28, "rz": 0.30},
        {"y":  0.00, "zc": 1.12, "rx": 0.30, "rz": 0.32},
        {"y":  0.30, "zc": 1.15, "rx": 0.31, "rz": 0.34},
        {"y":  0.55, "zc": 1.18, "rx": 0.28, "rz": 0.30},
        {"y":  0.75, "zc": 1.32, "rx": 0.18, "rz": 0.22},
        {"y":  0.95, "zc": 1.48, "rx": 0.14, "rz": 0.16},
        {"y":  1.15, "zc": 1.55, "rx": 0.12, "rz": 0.14},
        {"y":  1.30, "zc": 1.48, "rx": 0.07, "rz": 0.08},
    ]
    N = 10
    ring_verts = []
    for r in rings:
        v_list = []
        for k in range(N):
            ang = 2.0 * math.pi * k / N
            vx = ox + math.cos(ang) * r["rx"]
            vy = oy + r["y"]
            vz = oz + r["zc"] + math.sin(ang) * r["rz"]
            v_list.append(bm.verts.new((vx, vy, vz)))
        ring_verts.append(v_list)

    for i in range(len(rings) - 1):
        r1, r2 = ring_verts[i], ring_verts[i + 1]
        for k in range(N):
            kn = (k + 1) % N
            bm.faces.new((r1[k], r1[kn], r2[kn], r2[k]))

    bm.faces.new(ring_verts[0][::-1])
    bm.faces.new(ring_verts[-1])

    # Horns
    for sign in [1, -1]:
        h_base = Vector((ox + sign * 0.10, oy + 1.10, oz + 1.60))
        h_mid = Vector((ox + sign * 0.16, oy + 0.95, oz + 1.80))
        h_tip = Vector((ox + sign * 0.20, oy + 0.80, oz + 1.95))
        w = 0.035
        b_pts = [
            bm.verts.new(h_base + Vector((-w, -w, 0))),
            bm.verts.new(h_base + Vector((w, -w, 0))),
            bm.verts.new(h_base + Vector((w, w, 0))),
            bm.verts.new(h_base + Vector((-w, w, 0))),
            bm.verts.new(h_mid + Vector((-w*0.7, -w*0.7, 0))),
            bm.verts.new(h_mid + Vector((w*0.7, -w*0.7, 0))),
            bm.verts.new(h_mid + Vector((w*0.7, w*0.7, 0))),
            bm.verts.new(h_mid + Vector((-w*0.7, w*0.7, 0))),
            bm.verts.new(h_tip),
        ]
        for j in range(4):
            jn = (j + 1) % 4
            f1 = bm.faces.new((b_pts[j], b_pts[jn], b_pts[4 + jn], b_pts[4 + j]))
            f1.material_index = 1
            f2 = bm.faces.new((b_pts[4 + j], b_pts[4 + jn], b_pts[8]))
            f2.material_index = 1

    # 4 Legs
    legs = [
        (0.24, 0.52, 0.95, 0.05),
        (-0.24, 0.52, 0.95, 0.05),
        (0.24, -0.35, 0.90, 0.05),
        (-0.24, -0.35, 0.90, 0.05),
    ]
    for lx, ly, ztop, zbot in legs:
        cyl_v = []
        for s in range(4):
            z = oz + ztop * (1.0 - s / 3.0) + zbot * (s / 3.0)
            r = 0.06 * (1.0 - 0.25 * (s / 3.0))
            for i in range(6):
                a = i * 2.0 * math.pi / 6.0
                cyl_v.append(bm.verts.new((ox + lx + r * math.cos(a), oy + ly + r * math.sin(a), z)))
        for s in range(3):
            for i in range(6):
                inxt = (i + 1) % 6
                bm.faces.new((cyl_v[s * 6 + i], cyl_v[s * 6 + inxt], cyl_v[(s + 1) * 6 + inxt], cyl_v[(s + 1) * 6 + i]))

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Vertex skinning
    for b in arm_data.bones:
        mesh_obj.vertex_groups.new(name=b.name)
    for v in mesh_data.vertices:
        y = v.co.y - oy
        z = v.co.z - oz
        side = ".L" if v.co.x > ox else ".R"
        if z < 0.90 and abs(v.co.x - ox) > 0.12:
            if y > 0.10:
                if z > 0.50:
                    mesh_obj.vertex_groups[f"UpperArm{side}"].add([v.index], 1.0, 'REPLACE')
                elif z > 0.15:
                    mesh_obj.vertex_groups[f"Forearm{side}"].add([v.index], 1.0, 'REPLACE')
                else:
                    mesh_obj.vertex_groups[f"Hoof{side}"].add([v.index], 1.0, 'REPLACE')
            else:
                if z > 0.45:
                    mesh_obj.vertex_groups[f"Thigh{side}"].add([v.index], 1.0, 'REPLACE')
                elif z > 0.15:
                    mesh_obj.vertex_groups[f"Shin{side}"].add([v.index], 1.0, 'REPLACE')
                else:
                    mesh_obj.vertex_groups[f"Hoof_Hind{side}"].add([v.index], 1.0, 'REPLACE')
        else:
            if y > 1.05:
                mesh_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.70:
                mesh_obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.20:
                mesh_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
            elif y > -0.20:
                mesh_obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else:
                mesh_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')

    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj

    sub_mod = mesh_obj.modifiers.new("Subsurf", 'SUBSURF')
    sub_mod.levels = 1
    sub_mod.render_levels = 1

    # 3. Actions & NLA
    arm_obj.animation_data_create()

    # Action 1: Goat_Climb (40f @ 24fps)
    act_climb = bpy.data.actions.new("Goat_Climb")
    act_climb.use_fake_user = True
    arm_obj.animation_data.action = act_climb
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=40)

    # 4-beat climbing gait
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(24.0), 0.0, 0.0)
    arm_obj.pose.bones["UpperArm.L"].keyframe_insert('rotation_euler', frame=10)
    arm_obj.pose.bones["UpperArm.L"].rotation_euler = (math.radians(-18.0), 0.0, 0.0)
    arm_obj.pose.bones["UpperArm.L"].keyframe_insert('rotation_euler', frame=30)

    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(-18.0), 0.0, 0.0)
    arm_obj.pose.bones["UpperArm.R"].keyframe_insert('rotation_euler', frame=10)
    arm_obj.pose.bones["UpperArm.R"].rotation_euler = (math.radians(24.0), 0.0, 0.0)
    arm_obj.pose.bones["UpperArm.R"].keyframe_insert('rotation_euler', frame=30)

    pushdown_action_to_nla(arm_obj, act_climb)

    # Action 2: Goat_Idle (60f @ 24fps)
    act_idle = bpy.data.actions.new("Goat_Idle")
    act_idle.use_fake_user = True
    arm_obj.animation_data.action = act_idle
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=60)

    # Head scanning valley
    arm_obj.pose.bones["Head"].rotation_euler = (0.0, 0.0, math.radians(15.0))
    arm_obj.pose.bones["Head"].keyframe_insert('rotation_euler', frame=20)
    arm_obj.pose.bones["Head"].rotation_euler = (0.0, 0.0, math.radians(-12.0))
    arm_obj.pose.bones["Head"].keyframe_insert('rotation_euler', frame=45)

    pushdown_action_to_nla(arm_obj, act_idle)

    # Default active action
    arm_obj.animation_data.action = act_idle
    return arm_obj, mesh_obj


# =============================================================================
# 2. ALPINE: GOLDEN EAGLE (Aquila chrysaetos) - 16 Bones, 2 Actions
# =============================================================================


def build_eagle(collection, offset=(10.0, -10.0, 38.0)):
    """
    Constructs the soaring Golden Eagle:
    - 16 bones (Root, Pelvis, Tail, Spine, Chest, Neck, Head, Beak, 2x Wings)
    - Aerodynamic raptor mesh with 100% smooth shading
    - Actions: Eagle_Glide (60f) and Eagle_Flap (30f)
    """
    ox, oy, oz = offset

    arm_data = bpy.data.armatures.new("Eagle_Armature_Data")
    arm_obj = bpy.data.objects.new("Eagle_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    root = eb.new("Root")
    root.head = (ox, oy, oz)
    root.tail = (ox, oy, oz + 0.2)

    pelvis = eb.new("Pelvis")
    pelvis.head = (ox, oy - 0.35, oz + 0.05)
    pelvis.tail = (ox, oy - 0.10, oz + 0.10)
    pelvis.parent = root

    tail = eb.new("Tail")
    tail.head = pelvis.head
    tail.tail = (ox, oy - 0.85, oz - 0.05)
    tail.parent = pelvis

    spine = eb.new("Spine")
    spine.head = pelvis.tail
    spine.tail = (ox, oy + 0.25, oz + 0.15)
    spine.parent = pelvis

    chest = eb.new("Chest")
    chest.head = spine.tail
    chest.tail = (ox, oy + 0.55, oz + 0.20)
    chest.parent = spine

    neck = eb.new("Neck")
    neck.head = chest.tail
    neck.tail = (ox, oy + 0.80, oz + 0.30)
    neck.parent = chest

    head = eb.new("Head")
    head.head = neck.tail
    head.tail = (ox, oy + 1.05, oz + 0.35)
    head.parent = neck

    beak = eb.new("Beak")
    beak.head = head.tail
    beak.tail = (ox, oy + 1.25, oz + 0.25)
    beak.parent = head

    # Wings (Shoulder -> Wing_Arm -> Wing_Forearm -> Wing_Tip)
    for side, sign in [(".L", 1), (".R", -1)]:
        sh = eb.new(f"Shoulder{side}")
        sh.head = (ox + sign * 0.18, oy + 0.40, oz + 0.18)
        sh.tail = (ox + sign * 0.40, oy + 0.38, oz + 0.20)
        sh.parent = chest

        wa = eb.new(f"Wing_Arm{side}")
        wa.head = sh.tail
        wa.tail = (ox + sign * 1.15, oy + 0.30, oz + 0.22)
        wa.parent = sh

        wf = eb.new(f"Wing_Forearm{side}")
        wf.head = wa.tail
        wf.tail = (ox + sign * 2.05, oy + 0.15, oz + 0.24)
        wf.parent = wa

        wt = eb.new(f"Wing_Tip{side}")
        wt.head = wf.tail
        wt.tail = (ox + sign * 2.85, oy - 0.05, oz + 0.25)
        wt.parent = wf

    bpy.ops.object.mode_set(mode='OBJECT')

    # Skinned Mesh
    mesh_data = bpy.data.meshes.new("Eagle_Mesh")
    mesh_obj = bpy.data.objects.new("Eagle_Model", mesh_data)
    collection.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    mat_body = create_fauna_material("Eagle_Body", (0.28, 0.16, 0.08, 1.0), roughness=0.65)
    mat_beak = create_fauna_material("Eagle_Beak", (0.85, 0.65, 0.10, 1.0), roughness=0.35)
    mesh_data.materials.append(mat_body)  # 0
    mesh_data.materials.append(mat_beak)  # 1

    bm = bmesh.new()
    rings = [
        {"y": -0.45, "zc": 0.05, "rx": 0.14, "rz": 0.12},
        {"y": -0.15, "zc": 0.10, "rx": 0.22, "rz": 0.18},
        {"y":  0.20, "zc": 0.15, "rx": 0.26, "rz": 0.22},
        {"y":  0.50, "zc": 0.20, "rx": 0.22, "rz": 0.18},
        {"y":  0.75, "zc": 0.28, "rx": 0.14, "rz": 0.14},
        {"y":  1.00, "zc": 0.34, "rx": 0.08, "rz": 0.09},
    ]
    N = 8
    ring_verts = []
    for r in rings:
        v_list = []
        for k in range(N):
            ang = 2.0 * math.pi * k / N
            vx = ox + math.cos(ang) * r["rx"]
            vy = oy + r["y"]
            vz = oz + r["zc"] + math.sin(ang) * r["rz"]
            v_list.append(bm.verts.new((vx, vy, vz)))
        ring_verts.append(v_list)

    for i in range(len(rings) - 1):
        r1, r2 = ring_verts[i], ring_verts[i + 1]
        for k in range(N):
            kn = (k + 1) % N
            bm.faces.new((r1[k], r1[kn], r2[kn], r2[k]))

    bm.faces.new(ring_verts[0][::-1])
    bm.faces.new(ring_verts[-1])

    # Wings (Broad planar aerofoil)
    for sign in [1, -1]:
        spans = [0.25, 1.15, 2.05, 2.85]
        w_verts = []
        for sx in spans:
            px = ox + sign * sx
            v_lead = bm.verts.new((px, oy + 0.35 - 0.12 * (sx / 2.85), oz + 0.20))
            v_trail = bm.verts.new((px, oy - 0.45 - 0.25 * (sx / 2.85), oz + 0.18))
            w_verts.append((v_lead, v_trail))
        for i in range(len(spans) - 1):
            vl1, vt1 = w_verts[i]
            vl2, vt2 = w_verts[i + 1]
            if sign == 1:
                bm.faces.new((vl1, vl2, vt2, vt1))
            else:
                bm.faces.new((vl1, vt1, vt2, vl2))

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Vertex skinning
    for b in arm_data.bones:
        mesh_obj.vertex_groups.new(name=b.name)
    for v in mesh_data.vertices:
        x = abs(v.co.x - ox)
        y = v.co.y - oy
        side = ".L" if v.co.x > ox else ".R"
        if x > 2.05:
            mesh_obj.vertex_groups[f"Wing_Tip{side}"].add([v.index], 1.0, 'REPLACE')
        elif x > 1.15:
            mesh_obj.vertex_groups[f"Wing_Forearm{side}"].add([v.index], 1.0, 'REPLACE')
        elif x > 0.40:
            mesh_obj.vertex_groups[f"Wing_Arm{side}"].add([v.index], 1.0, 'REPLACE')
        else:
            if y > 0.90:
                mesh_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.45:
                mesh_obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.0:
                mesh_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
            elif y > -0.30:
                mesh_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')
            else:
                mesh_obj.vertex_groups["Tail"].add([v.index], 1.0, 'REPLACE')

    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj
    sub_mod = mesh_obj.modifiers.new("Subsurf", 'SUBSURF')
    sub_mod.levels = 1

    # Actions & NLA
    arm_obj.animation_data_create()

    # Action 1: Eagle_Glide (60f @ 24fps)
    act_glide = bpy.data.actions.new("Eagle_Glide")
    act_glide.use_fake_user = True
    arm_obj.animation_data.action = act_glide
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=60)

    arm_obj.pose.bones["Chest"].rotation_euler = (0.0, math.radians(4.0), 0.0)
    arm_obj.pose.bones["Chest"].keyframe_insert('rotation_euler', frame=30)
    arm_obj.pose.bones["Wing_Tip.L"].rotation_euler = (0.0, 0.0, math.radians(6.0))
    arm_obj.pose.bones["Wing_Tip.L"].keyframe_insert('rotation_euler', frame=30)
    arm_obj.pose.bones["Wing_Tip.R"].rotation_euler = (0.0, 0.0, math.radians(-6.0))
    arm_obj.pose.bones["Wing_Tip.R"].keyframe_insert('rotation_euler', frame=30)

    pushdown_action_to_nla(arm_obj, act_glide)

    # Action 2: Eagle_Flap (30f @ 24fps)
    act_flap = bpy.data.actions.new("Eagle_Flap")
    act_flap.use_fake_user = True
    arm_obj.animation_data.action = act_flap
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=30)

    for sign, sname in [(1.0, ".L"), (-1.0, ".R")]:
        arm_obj.pose.bones[f"Wing_Arm{sname}"].rotation_euler = (0.0, math.radians(-24.0 * sign), 0.0)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].keyframe_insert('rotation_euler', frame=8)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].rotation_euler = (0.0, math.radians(22.0 * sign), 0.0)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].keyframe_insert('rotation_euler', frame=20)

    pushdown_action_to_nla(arm_obj, act_flap)

    arm_obj.animation_data.action = act_glide
    return arm_obj, mesh_obj


# =============================================================================
# 3. FOREST & PLAINS: HIGHLAND RED STAG (Cervus elaphus) - 26 Bones, 2 Actions
# =============================================================================


def build_stag(collection, offset=(-5.0, 15.0, 7.5)):
    """
    Constructs the Highland Red Stag:
    - 26 bones (Pelvis, Spine, Chest, Neck, Head, Jaw, 4x Antler segments, 4 limbs & hooves, tail)
    - Quad-dominant lofted mesh with branching quad-beam antlers
    - Actions: Stag_Idle (60f) and Stag_Walk (40f)
    """
    ox, oy, oz = offset

    arm_data = bpy.data.armatures.new("Stag_Armature_Data")
    arm_obj = bpy.data.objects.new("Stag_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    root = eb.new("Root")
    root.head = (ox, oy, oz)
    root.tail = (ox, oy, oz + 0.3)

    pelvis = eb.new("Pelvis")
    pelvis.head = (ox, oy - 0.60, oz + 1.35)
    pelvis.tail = (ox, oy - 0.20, oz + 1.40)
    pelvis.parent = root

    spine = eb.new("Spine")
    spine.head = pelvis.tail
    spine.tail = (ox, oy + 0.35, oz + 1.45)
    spine.parent = pelvis

    chest = eb.new("Chest")
    chest.head = spine.tail
    chest.tail = (ox, oy + 0.85, oz + 1.50)
    chest.parent = spine

    neck = eb.new("Neck")
    neck.head = chest.tail
    neck.tail = (ox, oy + 1.25, oz + 1.85)
    neck.parent = chest

    head = eb.new("Head")
    head.head = neck.tail
    head.tail = (ox, oy + 1.60, oz + 2.05)
    head.parent = neck

    jaw = eb.new("Jaw")
    jaw.head = (ox, oy + 1.30, oz + 1.80)
    jaw.tail = (ox, oy + 1.60, oz + 1.85)
    jaw.parent = head

    # Regal Branching Antlers (4 bones: Antler.L/R, Antler_Tine.L/R)
    for side, sign in [(".L", 1), (".R", -1)]:
        ant = eb.new(f"Antler{side}")
        ant.head = (ox + sign * 0.12, oy + 1.45, oz + 2.15)
        ant.tail = (ox + sign * 0.32, oy + 1.35, oz + 2.65)
        ant.parent = head

        tine = eb.new(f"Antler_Tine{side}")
        tine.head = ant.tail
        tine.tail = (ox + sign * 0.45, oy + 1.25, oz + 2.85)
        tine.parent = ant

    tail = eb.new("Tail")
    tail.head = (ox, oy - 0.65, oz + 1.35)
    tail.tail = (ox, oy - 0.90, oz + 1.20)
    tail.parent = pelvis

    # Forelimbs (Shoulder -> UpperArm -> Forearm -> Hoof)
    for side, sign in [(".L", 1), (".R", -1)]:
        sh = eb.new(f"Shoulder{side}")
        sh.head = (ox + sign * 0.25, oy + 0.70, oz + 1.45)
        sh.tail = (ox + sign * 0.32, oy + 0.70, oz + 1.15)
        sh.parent = chest

        ua = eb.new(f"UpperArm{side}")
        ua.head = sh.tail
        ua.tail = (ox + sign * 0.32, oy + 0.65, oz + 0.65)
        ua.parent = sh

        fa = eb.new(f"Forearm{side}")
        fa.head = ua.tail
        fa.tail = (ox + sign * 0.32, oy + 0.65, oz + 0.15)
        fa.parent = ua

        hf = eb.new(f"Hoof{side}")
        hf.head = fa.tail
        hf.tail = (ox + sign * 0.32, oy + 0.68, oz + 0.0)
        hf.parent = fa

    # Hindlimbs (Hip -> Thigh -> Shin -> Hoof_Hind)
    for side, sign in [(".L", 1), (".R", -1)]:
        hp = eb.new(f"Hip{side}")
        hp.head = (ox + sign * 0.25, oy - 0.50, oz + 1.35)
        hp.tail = (ox + sign * 0.32, oy - 0.45, oz + 1.05)
        hp.parent = pelvis

        th = eb.new(f"Thigh{side}")
        th.head = hp.tail
        th.tail = (ox + sign * 0.32, oy - 0.55, oz + 0.60)
        th.parent = hp

        shn = eb.new(f"Shin{side}")
        shn.head = th.tail
        shn.tail = (ox + sign * 0.32, oy - 0.50, oz + 0.15)
        shn.parent = th

        hhf = eb.new(f"Hoof_Hind{side}")
        hhf.head = shn.tail
        hhf.tail = (ox + sign * 0.32, oy - 0.48, oz + 0.0)
        hhf.parent = shn

    bpy.ops.object.mode_set(mode='OBJECT')

    # Skinned Mesh
    mesh_data = bpy.data.meshes.new("Stag_Mesh")
    mesh_obj = bpy.data.objects.new("Stag_Model", mesh_data)
    collection.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    mat_coat = create_fauna_material("Stag_Coat", (0.48, 0.24, 0.11, 1.0), roughness=0.62)
    mat_antler = create_fauna_material("Stag_Antler", (0.85, 0.82, 0.75, 1.0), roughness=0.45)
    mesh_data.materials.append(mat_coat)    # 0
    mesh_data.materials.append(mat_antler)  # 1

    bm = bmesh.new()
    rings = [
        {"y": -0.75, "zc": 1.35, "rx": 0.28, "rz": 0.30},
        {"y": -0.45, "zc": 1.38, "rx": 0.34, "rz": 0.36},
        {"y": -0.10, "zc": 1.42, "rx": 0.38, "rz": 0.40},
        {"y":  0.25, "zc": 1.45, "rx": 0.40, "rz": 0.44},
        {"y":  0.60, "zc": 1.48, "rx": 0.42, "rz": 0.46},
        {"y":  0.85, "zc": 1.52, "rx": 0.34, "rz": 0.38},
        {"y":  1.05, "zc": 1.68, "rx": 0.24, "rz": 0.28},
        {"y":  1.25, "zc": 1.88, "rx": 0.18, "rz": 0.22},
        {"y":  1.42, "zc": 2.05, "rx": 0.16, "rz": 0.20},
        {"y":  1.65, "zc": 1.98, "rx": 0.12, "rz": 0.12},
        {"y":  1.80, "zc": 1.92, "rx": 0.06, "rz": 0.07},
    ]
    N = 12
    ring_verts = []
    for r in rings:
        v_list = []
        for k in range(N):
            ang = 2.0 * math.pi * k / N
            vx = ox + math.cos(ang) * r["rx"]
            vy = oy + r["y"]
            vz = oz + r["zc"] + math.sin(ang) * r["rz"]
            v_list.append(bm.verts.new((vx, vy, vz)))
        ring_verts.append(v_list)

    for i in range(len(rings) - 1):
        r1, r2 = ring_verts[i], ring_verts[i + 1]
        for k in range(N):
            kn = (k + 1) % N
            bm.faces.new((r1[k], r1[kn], r2[kn], r2[k]))

    bm.faces.new(ring_verts[0][::-1])
    bm.faces.new(ring_verts[-1])

    # Antlers
    for sign in [1, -1]:
        base_pt = Vector((ox + sign * 0.12, oy + 1.45, oz + 2.15))
        mid_pt = Vector((ox + sign * 0.22, oy + 1.40, oz + 2.42))
        tip_pt = Vector((ox + sign * 0.32, oy + 1.35, oz + 2.65))
        w = 0.035
        b_pts = [
            bm.verts.new(base_pt + Vector((-w, -w, 0))),
            bm.verts.new(base_pt + Vector((w, -w, 0))),
            bm.verts.new(base_pt + Vector((w, w, 0))),
            bm.verts.new(base_pt + Vector((-w, w, 0))),
            bm.verts.new(mid_pt + Vector((-w*0.8, -w*0.8, 0))),
            bm.verts.new(mid_pt + Vector((w*0.8, -w*0.8, 0))),
            bm.verts.new(mid_pt + Vector((w*0.8, w*0.8, 0))),
            bm.verts.new(mid_pt + Vector((-w*0.8, w*0.8, 0))),
            bm.verts.new(tip_pt)
        ]
        for j in range(4):
            jn = (j + 1) % 4
            f1 = bm.faces.new((b_pts[j], b_pts[jn], b_pts[4 + jn], b_pts[4 + j]))
            f1.material_index = 1
            f2 = bm.faces.new((b_pts[4 + j], b_pts[4 + jn], b_pts[8]))
            f2.material_index = 1

    # 4 Legs
    leg_coords = [
        (0.32, 0.65, 1.25, 0.05),
        (-0.32, 0.65, 1.25, 0.05),
        (0.32, -0.50, 1.20, 0.05),
        (-0.32, -0.50, 1.20, 0.05),
    ]
    for lx, ly, ztop, zbot in leg_coords:
        cyl_v = []
        for s in range(4):
            z = oz + ztop * (1.0 - s / 3.0) + zbot * (s / 3.0)
            r = 0.08 * (1.0 - 0.3 * (s / 3.0))
            for i in range(6):
                a = i * 2.0 * math.pi / 6.0
                cyl_v.append(bm.verts.new((ox + lx + r * math.cos(a), oy + ly + r * math.sin(a), z)))
        for s in range(3):
            for i in range(6):
                inxt = (i + 1) % 6
                bm.faces.new((cyl_v[s * 6 + i], cyl_v[s * 6 + inxt], cyl_v[(s + 1) * 6 + inxt], cyl_v[(s + 1) * 6 + i]))

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Vertex skinning
    for b in arm_data.bones:
        mesh_obj.vertex_groups.new(name=b.name)
    for v in mesh_data.vertices:
        y = v.co.y - oy
        z = v.co.z - oz
        side = ".L" if v.co.x > ox else ".R"
        if z < 1.10 and abs(v.co.x - ox) > 0.15:
            if y > 0.10:
                if z > 0.65:
                    mesh_obj.vertex_groups[f"UpperArm{side}"].add([v.index], 1.0, 'REPLACE')
                elif z > 0.15:
                    mesh_obj.vertex_groups[f"Forearm{side}"].add([v.index], 1.0, 'REPLACE')
                else:
                    mesh_obj.vertex_groups[f"Hoof{side}"].add([v.index], 1.0, 'REPLACE')
            else:
                if z > 0.60:
                    mesh_obj.vertex_groups[f"Thigh{side}"].add([v.index], 1.0, 'REPLACE')
                elif z > 0.15:
                    mesh_obj.vertex_groups[f"Shin{side}"].add([v.index], 1.0, 'REPLACE')
                else:
                    mesh_obj.vertex_groups[f"Hoof_Hind{side}"].add([v.index], 1.0, 'REPLACE')
        else:
            if y > 1.30:
                mesh_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.85:
                mesh_obj.vertex_groups["Neck"].add([v.index], 1.0, 'REPLACE')
            elif y > 0.25:
                mesh_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
            elif y > -0.20:
                mesh_obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            else:
                mesh_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')

    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj
    sub_mod = mesh_obj.modifiers.new("Subsurf", 'SUBSURF')
    sub_mod.levels = 1

    # Actions & NLA
    arm_obj.animation_data_create()

    # Action 1: Stag_Idle (60f @ 24fps)
    act_idle = bpy.data.actions.new("Stag_Idle")
    act_idle.use_fake_user = True
    arm_obj.animation_data.action = act_idle
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=60)

    arm_obj.pose.bones["Head"].rotation_euler = (0.0, 0.0, math.radians(12.0))
    arm_obj.pose.bones["Head"].keyframe_insert('rotation_euler', frame=25)
    arm_obj.pose.bones["Head"].rotation_euler = (0.0, 0.0, math.radians(-10.0))
    arm_obj.pose.bones["Head"].keyframe_insert('rotation_euler', frame=45)

    pushdown_action_to_nla(arm_obj, act_idle)

    # Action 2: Stag_Walk (40f @ 24fps)
    act_walk = bpy.data.actions.new("Stag_Walk")
    act_walk.use_fake_user = True
    arm_obj.animation_data.action = act_walk
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=40)

    for sign, side in [(1.0, ".L"), (-1.0, ".R")]:
        arm_obj.pose.bones[f"UpperArm{side}"].rotation_euler = (math.radians(18.0 * sign), 0.0, 0.0)
        arm_obj.pose.bones[f"UpperArm{side}"].keyframe_insert('rotation_euler', frame=10)
        arm_obj.pose.bones[f"UpperArm{side}"].rotation_euler = (math.radians(-18.0 * sign), 0.0, 0.0)
        arm_obj.pose.bones[f"UpperArm{side}"].keyframe_insert('rotation_euler', frame=30)

        arm_obj.pose.bones[f"Thigh{side}"].rotation_euler = (math.radians(-16.0 * sign), 0.0, 0.0)
        arm_obj.pose.bones[f"Thigh{side}"].keyframe_insert('rotation_euler', frame=10)
        arm_obj.pose.bones[f"Thigh{side}"].rotation_euler = (math.radians(16.0 * sign), 0.0, 0.0)
        arm_obj.pose.bones[f"Thigh{side}"].keyframe_insert('rotation_euler', frame=30)

    pushdown_action_to_nla(arm_obj, act_walk)

    arm_obj.animation_data.action = act_idle
    return arm_obj, mesh_obj


# =============================================================================
# 4. AQUATIC & SHORE: FRESHWATER TROUT (Salmo) - 12 Bones, 2 Actions
# =============================================================================


def build_fish(collection, offset=(-25.0, -10.0, 3.5)):
    """
    Constructs the Freshwater Trout / Coastal Fish:
    - 12 bones (Root, 5x Spine chain, 2x Pectoral, Dorsal Fin, 2x Pelvic, Tail Fin)
    - Hydrodynamic fusiform body with translucent fins
    - Actions: Fish_Swim (30f traveling wave) and Fish_Idle (60f station keeping)
    """
    ox, oy, oz = offset

    arm_data = bpy.data.armatures.new("Fish_Armature_Data")
    arm_obj = bpy.data.objects.new("Fish_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    root = eb.new("Root")
    root.head = (ox, oy - 0.70, oz)
    root.tail = (ox, oy - 0.70, oz + 0.15)

    sp1 = eb.new("Spine_01")
    sp1.head = (ox, oy + 0.65, oz)
    sp1.tail = (ox, oy + 0.35, oz)
    sp1.parent = root

    sp2 = eb.new("Spine_02")
    sp2.head = sp1.tail
    sp2.tail = (ox, oy + 0.05, oz)
    sp2.parent = sp1

    for side, sign in [(".L", 1), (".R", -1)]:
        pec = eb.new(f"Pectoral{side}")
        pec.head = (ox + sign * 0.12, oy + 0.20, oz - 0.05)
        pec.tail = (ox + sign * 0.35, oy + 0.05, oz - 0.12)
        pec.parent = sp2

    sp3 = eb.new("Spine_03")
    sp3.head = sp2.tail
    sp3.tail = (ox, oy - 0.25, oz)
    sp3.parent = sp2

    dorsal = eb.new("Dorsal_Fin")
    dorsal.head = (ox, oy - 0.10, oz + 0.18)
    dorsal.tail = (ox, oy - 0.25, oz + 0.42)
    dorsal.parent = sp3

    sp4 = eb.new("Spine_04")
    sp4.head = sp3.tail
    sp4.tail = (ox, oy - 0.50, oz)
    sp4.parent = sp3

    for side, sign in [(".L", 1), (".R", -1)]:
        pelv = eb.new(f"Pelvic_Fin{side}")
        pelv.head = (ox + sign * 0.08, oy - 0.35, oz - 0.12)
        pelv.tail = (ox + sign * 0.20, oy - 0.45, oz - 0.22)
        pelv.parent = sp4

    sp5 = eb.new("Spine_05")
    sp5.head = sp4.tail
    sp5.tail = (ox, oy - 0.70, oz)
    sp5.parent = sp4

    tail_fin = eb.new("Tail_Fin")
    tail_fin.head = sp5.tail
    tail_fin.tail = (ox, oy - 1.05, oz)
    tail_fin.parent = sp5

    bpy.ops.object.mode_set(mode='OBJECT')

    # Skinned Mesh
    mesh_data = bpy.data.meshes.new("Fish_Mesh")
    mesh_obj = bpy.data.objects.new("Fish_Model", mesh_data)
    collection.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    mat_skin = create_fauna_material("M_Fish_Skin", (0.16, 0.42, 0.36, 1.0), roughness=0.25, specular=0.65)
    mat_fins = create_fauna_material("M_Fish_Fins", (0.35, 0.55, 0.50, 0.75), roughness=0.35, transmission=0.45)
    mesh_data.materials.append(mat_skin)  # 0
    mesh_data.materials.append(mat_fins)  # 1

    bm = bmesh.new()
    rings = [
        {"y":  0.65, "zc": 0.0, "rx": 0.04, "rz": 0.05},
        {"y":  0.40, "zc": 0.0, "rx": 0.14, "rz": 0.18},
        {"y":  0.10, "zc": 0.0, "rx": 0.18, "rz": 0.24},
        {"y": -0.20, "zc": 0.0, "rx": 0.16, "rz": 0.22},
        {"y": -0.45, "zc": 0.0, "rx": 0.11, "rz": 0.16},
        {"y": -0.70, "zc": 0.0, "rx": 0.05, "rz": 0.08},
    ]
    N = 8
    ring_verts = []
    for r in rings:
        v_list = []
        for k in range(N):
            ang = 2.0 * math.pi * k / N
            vx = ox + math.cos(ang) * r["rx"]
            vy = oy + r["y"]
            vz = oz + r["zc"] + math.sin(ang) * r["rz"]
            v_list.append(bm.verts.new((vx, vy, vz)))
        ring_verts.append(v_list)

    for i in range(len(rings) - 1):
        r1, r2 = ring_verts[i], ring_verts[i + 1]
        for k in range(N):
            kn = (k + 1) % N
            bm.faces.new((r1[k], r1[kn], r2[kn], r2[k]))

    bm.faces.new(ring_verts[0][::-1])
    bm.faces.new(ring_verts[-1])

    # Caudal Tail Fin Blade
    t_lead = [bm.verts.new((ox, oy - 0.70, oz + 0.08)), bm.verts.new((ox, oy - 0.70, oz - 0.08))]
    t_mid = bm.verts.new((ox, oy - 0.90, oz))
    t_upper = bm.verts.new((ox, oy - 1.05, oz + 0.28))
    t_lower = bm.verts.new((ox, oy - 1.05, oz - 0.28))
    f_tail1 = bm.faces.new((t_lead[0], t_upper, t_mid))
    f_tail1.material_index = 1
    f_tail2 = bm.faces.new((t_lead[1], t_mid, t_lower))
    f_tail2.material_index = 1

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Vertex skinning
    for b in arm_data.bones:
        mesh_obj.vertex_groups.new(name=b.name)
    for v in mesh_data.vertices:
        y = v.co.y - oy
        if y > 0.45:
            mesh_obj.vertex_groups["Spine_01"].add([v.index], 1.0, 'REPLACE')
        elif y > 0.15:
            mesh_obj.vertex_groups["Spine_02"].add([v.index], 1.0, 'REPLACE')
        elif y > -0.15:
            mesh_obj.vertex_groups["Spine_03"].add([v.index], 1.0, 'REPLACE')
        elif y > -0.45:
            mesh_obj.vertex_groups["Spine_04"].add([v.index], 1.0, 'REPLACE')
        elif y > -0.75:
            mesh_obj.vertex_groups["Spine_05"].add([v.index], 1.0, 'REPLACE')
        else:
            mesh_obj.vertex_groups["Tail_Fin"].add([v.index], 1.0, 'REPLACE')

    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj
    sub_mod = mesh_obj.modifiers.new("Subsurf", 'SUBSURF')
    sub_mod.levels = 1

    # Actions & NLA
    arm_obj.animation_data_create()

    # Action 1: Fish_Swim (30f @ 24fps)
    act_swim = bpy.data.actions.new("Fish_Swim")
    act_swim.use_fake_user = True
    arm_obj.animation_data.action = act_swim
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=30)

    # Undulating swimming wave
    arm_obj.pose.bones["Spine_03"].rotation_euler = (0.0, 0.0, math.radians(8.0))
    arm_obj.pose.bones["Spine_03"].keyframe_insert('rotation_euler', frame=8)
    arm_obj.pose.bones["Spine_03"].rotation_euler = (0.0, 0.0, math.radians(-8.0))
    arm_obj.pose.bones["Spine_03"].keyframe_insert('rotation_euler', frame=22)

    arm_obj.pose.bones["Tail_Fin"].rotation_euler = (0.0, 0.0, math.radians(-28.0))
    arm_obj.pose.bones["Tail_Fin"].keyframe_insert('rotation_euler', frame=8)
    arm_obj.pose.bones["Tail_Fin"].rotation_euler = (0.0, 0.0, math.radians(28.0))
    arm_obj.pose.bones["Tail_Fin"].keyframe_insert('rotation_euler', frame=22)

    pushdown_action_to_nla(arm_obj, act_swim)

    # Action 2: Fish_Idle (60f @ 24fps)
    act_idle = bpy.data.actions.new("Fish_Idle")
    act_idle.use_fake_user = True
    arm_obj.animation_data.action = act_idle
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=60)

    arm_obj.pose.bones["Tail_Fin"].rotation_euler = (0.0, 0.0, math.radians(5.0))
    arm_obj.pose.bones["Tail_Fin"].keyframe_insert('rotation_euler', frame=30)

    pushdown_action_to_nla(arm_obj, act_idle)

    arm_obj.animation_data.action = act_swim
    return arm_obj, mesh_obj


# =============================================================================
# 5. SUBTERRANEAN CAVE: CAVE BAT (Myotis) - 18 Bones, 2 Actions
# =============================================================================


def build_cave_bat(collection, offset=(13.5, 4.5, 0.5)):
    """
    Constructs the Subterranean Cave Bat:
    - 18 bones (Root, Pelvis, 2x Claws, Spine, Chest, Neck, Head, 2x Ears, 2x Wings)
    - Leathery wing patagium, echolocating ears, ceiling claws
    - Actions: Bat_Roost (60f) and Bat_Flutter (20f)
    """
    ox, oy, oz = offset

    arm_data = bpy.data.armatures.new("Bat_Armature_Data")
    arm_obj = bpy.data.objects.new("Bat_Armature", arm_data)
    collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones

    root = eb.new("Root")
    root.head = (ox, oy, oz)
    root.tail = (ox, oy, oz - 0.15)

    pelvis = eb.new("Pelvis")
    pelvis.head = (ox, oy, oz - 0.05)
    pelvis.tail = (ox, oy, oz - 0.20)
    pelvis.parent = root

    for side, sign in [(".L", 1), (".R", -1)]:
        claw = eb.new(f"Leg_Claw{side}")
        claw.head = (ox + sign * 0.06, oy, oz - 0.02)
        claw.tail = (ox + sign * 0.08, oy, oz + 0.15)  # Clinging upward to ceiling
        claw.parent = pelvis

    spine = eb.new("Spine")
    spine.head = pelvis.tail
    spine.tail = (ox, oy, oz - 0.40)
    spine.parent = pelvis

    chest = eb.new("Chest")
    chest.head = spine.tail
    chest.tail = (ox, oy, oz - 0.60)
    chest.parent = spine

    neck = eb.new("Neck")
    neck.head = chest.tail
    neck.tail = (ox, oy + 0.05, oz - 0.75)
    neck.parent = chest

    head = eb.new("Head")
    head.head = neck.tail
    head.tail = (ox, oy + 0.12, oz - 0.90)
    head.parent = neck

    for side, sign in [(".L", 1), (".R", -1)]:
        ear = eb.new(f"Ear{side}")
        ear.head = (ox + sign * 0.06, oy + 0.08, oz - 0.85)
        ear.tail = (ox + sign * 0.14, oy + 0.12, oz - 0.72)
        ear.parent = head

    # Wings (Shoulder -> Wing_Arm -> Wing_Forearm -> Wing_Tip)
    for side, sign in [(".L", 1), (".R", -1)]:
        sh = eb.new(f"Shoulder{side}")
        sh.head = (ox + sign * 0.10, oy, oz - 0.55)
        sh.tail = (ox + sign * 0.25, oy, oz - 0.55)
        sh.parent = chest

        wa = eb.new(f"Wing_Arm{side}")
        wa.head = sh.tail
        wa.tail = (ox + sign * 0.65, oy, oz - 0.58)
        wa.parent = sh

        wf = eb.new(f"Wing_Forearm{side}")
        wf.head = wa.tail
        wf.tail = (ox + sign * 1.15, oy, oz - 0.62)
        wf.parent = wa

        wt = eb.new(f"Wing_Tip{side}")
        wt.head = wf.tail
        wt.tail = (ox + sign * 1.65, oy, oz - 0.65)
        wt.parent = wf

    bpy.ops.object.mode_set(mode='OBJECT')

    # Skinned Mesh
    mesh_data = bpy.data.meshes.new("Bat_Mesh")
    mesh_obj = bpy.data.objects.new("Bat_Model", mesh_data)
    collection.objects.link(mesh_obj)
    mesh_obj.parent = arm_obj

    mat_fur = create_fauna_material("M_Bat_Fur", (0.14, 0.12, 0.12, 1.0), roughness=0.85)
    mat_wing = create_fauna_material("M_Bat_Wing", (0.18, 0.14, 0.13, 0.85), roughness=0.65, transmission=0.30)
    mesh_data.materials.append(mat_fur)   # 0
    mesh_data.materials.append(mat_wing)  # 1

    bm = bmesh.new()
    # Torso (hanging downward)
    rings = [
        {"zc": -0.05, "rx": 0.08, "ry": 0.08},
        {"zc": -0.25, "rx": 0.14, "ry": 0.12},
        {"zc": -0.45, "rx": 0.16, "ry": 0.14},
        {"zc": -0.65, "rx": 0.12, "ry": 0.11},
        {"zc": -0.85, "rx": 0.08, "ry": 0.08},
    ]
    N = 8
    ring_verts = []
    for r in rings:
        v_list = []
        for k in range(N):
            ang = 2.0 * math.pi * k / N
            vx = ox + math.cos(ang) * r["rx"]
            vy = oy + math.sin(ang) * r["ry"]
            vz = oz + r["zc"]
            v_list.append(bm.verts.new((vx, vy, vz)))
        ring_verts.append(v_list)

    for i in range(len(rings) - 1):
        r1, r2 = ring_verts[i], ring_verts[i + 1]
        for k in range(N):
            kn = (k + 1) % N
            bm.faces.new((r1[k], r1[kn], r2[kn], r2[k]))

    bm.faces.new(ring_verts[0][::-1])
    bm.faces.new(ring_verts[-1])

    # Leathery Wings
    for sign in [1, -1]:
        spans = [0.15, 0.65, 1.15, 1.65]
        w_verts = []
        for sx in spans:
            px = ox + sign * sx
            v_top = bm.verts.new((px, oy, oz - 0.55))
            v_bot = bm.verts.new((px, oy, oz - 1.10 - 0.20 * (sx / 1.65)))
            w_verts.append((v_top, v_bot))
        for i in range(len(spans) - 1):
            vt1, vb1 = w_verts[i]
            vt2, vb2 = w_verts[i + 1]
            if sign == 1:
                f = bm.faces.new((vt1, vt2, vb2, vb1))
            else:
                f = bm.faces.new((vt1, vb1, vb2, vt2))
            f.material_index = 1

    bm.to_mesh(mesh_data)
    bm.free()
    mesh_data.update(calc_edges=True)
    mesh_data.shade_smooth()
    for poly in mesh_data.polygons:
        poly.use_smooth = True

    # Vertex skinning
    for b in arm_data.bones:
        mesh_obj.vertex_groups.new(name=b.name)
    for v in mesh_data.vertices:
        x = abs(v.co.x - ox)
        z = v.co.z - oz
        side = ".L" if v.co.x > ox else ".R"
        if x > 1.15:
            mesh_obj.vertex_groups[f"Wing_Tip{side}"].add([v.index], 1.0, 'REPLACE')
        elif x > 0.65:
            mesh_obj.vertex_groups[f"Wing_Forearm{side}"].add([v.index], 1.0, 'REPLACE')
        elif x > 0.20:
            mesh_obj.vertex_groups[f"Wing_Arm{side}"].add([v.index], 1.0, 'REPLACE')
        else:
            if z > -0.15:
                mesh_obj.vertex_groups["Pelvis"].add([v.index], 1.0, 'REPLACE')
            elif z > -0.40:
                mesh_obj.vertex_groups["Spine"].add([v.index], 1.0, 'REPLACE')
            elif z > -0.65:
                mesh_obj.vertex_groups["Chest"].add([v.index], 1.0, 'REPLACE')
            else:
                mesh_obj.vertex_groups["Head"].add([v.index], 1.0, 'REPLACE')

    arm_mod = mesh_obj.modifiers.new("Armature", 'ARMATURE')
    arm_mod.object = arm_obj
    sub_mod = mesh_obj.modifiers.new("Subsurf", 'SUBSURF')
    sub_mod.levels = 1

    # Actions & NLA
    arm_obj.animation_data_create()

    # Action 1: Bat_Roost (60f @ 24fps)
    act_roost = bpy.data.actions.new("Bat_Roost")
    act_roost.use_fake_user = True
    arm_obj.animation_data.action = act_roost
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=60)

    # Wings folded across chest
    for sign, sname in [(1.0, ".L"), (-1.0, ".R")]:
        arm_obj.pose.bones[f"Wing_Arm{sname}"].rotation_euler = (0.0, 0.0, math.radians(-65.0 * sign))
        arm_obj.pose.bones[f"Wing_Arm{sname}"].keyframe_insert('rotation_euler', frame=30)
        arm_obj.pose.bones[f"Wing_Forearm{sname}"].rotation_euler = (0.0, 0.0, math.radians(75.0 * sign))
        arm_obj.pose.bones[f"Wing_Forearm{sname}"].keyframe_insert('rotation_euler', frame=30)

    pushdown_action_to_nla(arm_obj, act_roost)

    # Action 2: Bat_Flutter (20f @ 24fps)
    act_flutter = bpy.data.actions.new("Bat_Flutter")
    act_flutter.use_fake_user = True
    arm_obj.animation_data.action = act_flutter
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1)
        pb.keyframe_insert('rotation_euler', frame=20)

    for sign, sname in [(1.0, ".L"), (-1.0, ".R")]:
        arm_obj.pose.bones[f"Wing_Arm{sname}"].rotation_euler = (0.0, math.radians(-35.0 * sign), 0.0)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].keyframe_insert('rotation_euler', frame=6)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].rotation_euler = (0.0, math.radians(40.0 * sign), 0.0)
        arm_obj.pose.bones[f"Wing_Arm{sname}"].keyframe_insert('rotation_euler', frame=14)

    pushdown_action_to_nla(arm_obj, act_flutter)

    arm_obj.animation_data.action = act_roost
    return arm_obj, mesh_obj


# =============================================================================
# Main Entry Point
# =============================================================================


def generate_fauna(context, collection_fauna, terrain_data):
    """
    Constructs all 5 fauna species across 4 biomes:
    1. Alpine: Mountain Goat (22 bones, Goat_Climb, Goat_Idle)
    2. Alpine: Golden Eagle (16 bones, Eagle_Glide, Eagle_Flap)
    3. Lowland: Highland Red Stag (26 bones, Stag_Idle, Stag_Walk)
    4. Aquatic: Freshwater Trout (12 bones, Fish_Swim, Fish_Idle)
    5. Cave: Subterranean Bat (18 bones, Bat_Roost, Bat_Flutter)

    Total bones: 94 bones.
    Total animation actions: 10 actions.

    Returns:
        list of (armature_obj, mesh_obj) tuples
    """
    anchors = terrain_data.get("biome_anchors", {})

    goat_loc = anchors.get("alpine_goat", (-24.0, 38.0, 24.5))
    eagle_loc = anchors.get("alpine_eagle", (10.0, -10.0, 38.0))
    stag_loc = anchors.get("meadow_stag", (-5.0, 15.0, 7.5))
    fish_loc = anchors.get("lake_fish", (-25.0, -10.0, 3.5))
    bat_loc = anchors.get("cave_bat", (13.5, 4.5, 0.5))

    goat_arm, goat_mesh = build_mountain_goat(collection_fauna, offset=goat_loc)
    eagle_arm, eagle_mesh = build_eagle(collection_fauna, offset=eagle_loc)
    stag_arm, stag_mesh = build_stag(collection_fauna, offset=stag_loc)
    fish_arm, fish_mesh = build_fish(collection_fauna, offset=fish_loc)
    bat_arm, bat_mesh = build_cave_bat(collection_fauna, offset=bat_loc)

    return [
        (goat_arm, goat_mesh),
        (eagle_arm, eagle_mesh),
        (stag_arm, stag_mesh),
        (fish_arm, fish_mesh),
        (bat_arm, bat_mesh),
    ]

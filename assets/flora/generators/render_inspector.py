"""
Genesis Zero — Flora 3D Multi-Angle Studio Inspection Renderer.
Renders 4 standardized camera views (Hero 3/4, Front, Side, Top-Down) in Blender
and creates a composite 2x2 verification contact sheet for quality inspection.
"""

import os
import sys
import math
from pathlib import Path
import bpy
import mathutils
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def setup_studio_lighting(scene, center, radius, height, min_z=0.0):
    # Remove existing lights and cameras
    for obj in list(scene.collection.objects):
        if obj.type in {'LIGHT', 'CAMERA'}:
            bpy.data.objects.remove(obj, do_unlink=True)

    # World background
    if not scene.world:
        scene.world = bpy.data.worlds.new("Studio_World")
    scene.world.use_nodes = True
    bg_node = scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.05, 0.07, 0.11, 1.0)
        bg_node.inputs["Strength"].default_value = 0.65

    # 1. Key Light (Warm Sunlight with soft shadow)
    key_data = bpy.data.lights.new(name="Studio_KeyLight", type='SUN')
    key_data.energy = 4.5
    key_data.color = (1.0, 0.97, 0.92)
    key_data.angle = math.radians(6.0)
    key_obj = bpy.data.objects.new(name="Studio_KeyLight", object_data=key_data)
    key_obj.rotation_euler = (math.radians(52), math.radians(15), math.radians(35))
    scene.collection.objects.link(key_obj)

    # 2. Fill Light (Soft cool ambient)
    fill_data = bpy.data.lights.new(name="Studio_FillLight", type='SUN')
    fill_data.energy = 2.0
    fill_data.color = (0.75, 0.88, 1.0)
    fill_data.angle = math.radians(20.0)
    fill_obj = bpy.data.objects.new(name="Studio_FillLight", object_data=fill_data)
    fill_obj.rotation_euler = (math.radians(45), math.radians(-10), math.radians(-120))
    scene.collection.objects.link(fill_obj)

    # 3. Rim / Back Light (Subsurface Scattering accent)
    rim_data = bpy.data.lights.new(name="Studio_RimLight", type='SUN')
    rim_data.energy = 3.5
    rim_data.color = (0.9, 1.0, 0.9)
    rim_obj = bpy.data.objects.new(name="Studio_RimLight", object_data=rim_data)
    rim_obj.rotation_euler = (math.radians(-35), math.radians(20), math.radians(-160))
    scene.collection.objects.link(rim_obj)

    # 4. Circular Pedestal / Ground shadow receiver
    ped_r = max(1.5, radius * 1.8)
    ped_z = min_z - 0.1
    bpy.ops.mesh.primitive_cylinder_add(
        radius=ped_r,
        depth=0.2,
        location=(center[0], center[1], ped_z),
        vertices=48
    )
    ped = bpy.context.active_object
    ped.name = "Studio_Ground"
    ped_mat = bpy.data.materials.new("M_Studio_Ground")
    ped_mat.use_nodes = True
    p_bsdf = ped_mat.node_tree.nodes.get("Principled BSDF")
    if p_bsdf:
        p_bsdf.inputs["Base Color"].default_value = (0.08, 0.12, 0.18, 1.0)
        p_bsdf.inputs["Roughness"].default_value = 0.9
    ped.data.materials.append(ped_mat)


def get_model_bounds():
    mesh_objs = [o for o in bpy.context.scene.collection.objects if o.type == 'MESH' and o.name != "Studio_Ground"]
    if not mesh_objs:
        return (0, 0, 1), 2.0, 2.0, 0.0

    min_coord = [float('inf')] * 3
    max_coord = [float('-inf')] * 3

    for obj in mesh_objs:
        for v in obj.bound_box:
            world_v = obj.matrix_world @ mathutils.Vector(v)
            for i in range(3):
                min_coord[i] = min(min_coord[i], world_v[i])
                max_coord[i] = max(max_coord[i], world_v[i])

    center = [(min_coord[i] + max_coord[i]) / 2.0 for i in range(3)]
    size = [max_coord[i] - min_coord[i] for i in range(3)]
    height = size[2]
    radius = max(size[0], size[1]) / 2.0
    return center, max(0.2, radius), max(0.2, height), min_coord[2]


def render_4_angles(blend_file_path, output_dir, species_name="flora"):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.film_transparent = False

    center, radius, height, min_z = get_model_bounds()
    setup_studio_lighting(scene, center, radius, height, min_z)

    cam_data = bpy.data.cameras.new("Inspector_Cam")
    cam_data.lens = 45  # Balanced studio perspective with natural depth
    cam_obj = bpy.data.objects.new("Inspector_Cam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # Distance tuned for 45mm lens to give 15-20% margin around bounding box
    max_dim = max(radius * 2.0, height)
    dist = max(1.2, max_dim * 1.65)
    cam_target = mathutils.Vector((center[0], center[1], center[2]))

    def aim_camera(cam, pos, target):
        cam.location = pos
        direction = target - pos
        rot_quat = direction.to_track_quat('-Z', 'Y')
        cam.rotation_euler = rot_quat.to_euler()

    angles = [
        ("01_hero_34", "1. Phối Cảnh 3/4 (Hero Perspective)",
         mathutils.Vector((center[0] + dist * 0.72, center[1] - dist * 0.72, center[2] + height * 0.35))),

        ("02_front", "2. Mặt Trước (Front View)",
         mathutils.Vector((center[0], center[1] - dist * 1.05, center[2]))),

        ("03_side", "3. Mặt Bên (Side View)",
         mathutils.Vector((center[0] + dist * 1.05, center[1], center[2]))),

        ("04_top", "4. Nhìn Từ Trên Xuống (Top-Down Plan)",
         mathutils.Vector((center[0] + 0.001, center[1] + 0.001, center[2] + dist * 1.15)))
    ]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered_files = []

    for key, label, cam_pos in angles:
        aim_camera(cam_obj, cam_pos, cam_target)
        img_path = str(out_dir / f"{species_name}_{key}.png")
        scene.render.filepath = img_path
        bpy.ops.render.render(write_still=True)
        rendered_files.append((img_path, label))
        print(f"Rendered: {img_path}")

    # Build 2x2 Composite Contact Sheet if PIL available
    contact_sheet_path = out_dir / f"{species_name}_inspection_sheet.png"
    if HAS_PIL:
        compose_contact_sheet(rendered_files, str(contact_sheet_path), species_name)
    else:
        print("PIL not in Blender environment, skipping internal contact sheet assembly")
    return str(contact_sheet_path), rendered_files


def compose_contact_sheet(rendered_files, output_path, title):
    tile_w, tile_h = 1024, 1024
    sheet = Image.new("RGB", (tile_w * 2, tile_h * 2 + 100), (8, 12, 20))
    draw = ImageDraw.Draw(sheet)

    # Title header banner
    draw.rectangle([0, 0, tile_w * 2, 90], fill=(13, 19, 33))
    header_text = f"GENESIS ZERO 3D FLORA INSPECTION — {title.upper()}"
    draw.text((32, 28), header_text, fill=(56, 189, 248))
    draw.text((tile_w * 2 - 400, 32), "Blender 5.2.1 LTS · Multi-Angle Quality Check", fill=(148, 163, 184))

    positions = [
        (0, 95),             # Top-Left: Hero 3/4
        (tile_w, 95),        # Top-Right: Front
        (0, tile_h + 95),    # Bottom-Left: Side
        (tile_w, tile_h + 95)# Bottom-Right: Top
    ]

    for idx, (img_file, label) in enumerate(rendered_files):
        x, y = positions[idx]
        if os.path.exists(img_file):
            with Image.open(img_file) as im:
                sheet.paste(im, (x, y))
        # Label badge
        badge_box = [x + 20, y + 20, x + 480, y + 65]
        draw.rectangle(badge_box, fill=(15, 23, 42, 220), outline=(56, 189, 248, 180), width=2)
        draw.text((x + 36, y + 32), label, fill=(241, 245, 249))

    # Save
    sheet.save(output_path, quality=95)
    print(f"Contact Sheet saved to: {output_path}")


if __name__ == "__main__":
    # If run inside Blender: python render_inspector.py <blend_path> <output_dir> <name>
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
    else:
        args = argv[1:]

    blend_file = args[0] if len(args) > 0 else bpy.data.filepath
    output_dir = args[1] if len(args) > 1 else "/tmp/flora_inspection"
    name = args[2] if len(args) > 2 else "weeping_willow"

    render_4_angles(blend_file, output_dir, name)

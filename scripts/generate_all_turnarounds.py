#!/usr/bin/env python3
"""
scripts/generate_all_turnarounds.py
Generates standardized 4-angle turnaround sheets for all botanical species in Genesis Zero.
Renders 4 angles (Hero 3/4, Front, Side, Top) in Blender EEVEE and composites them with PIL.
"""

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
DOCS_IMAGES = ROOT / "docs" / "flora" / "images"
WEB_IMAGES = ROOT / "web" / "flora_images"
BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"

CORE_SPECIES = {
    "canopy_ancient_oak",
    "canopy_giant_sequoia",
    "canopy_baobab",
    "understory_tree_fern",
    "aquatic_water_lily",
    "aquatic_sacred_lotus",
    "succulent_saguaro_cactus",
    "carnivorous_venus_flytrap",
    "carnivorous_pitcher_plant",
    "cave_bioluminescent_mushroom",
}

BLENDER_RENDER_SCRIPT = """
import bpy, os, sys, math, time, glob
from pathlib import Path
import mathutils

blend_files = sorted(glob.glob("assets/flora/**/*.blend", recursive=True))
core_species = {
    "canopy_ancient_oak",
    "canopy_giant_sequoia",
    "canopy_baobab",
    "understory_tree_fern",
    "aquatic_water_lily",
    "aquatic_sacred_lotus",
    "succulent_saguaro_cactus",
    "carnivorous_venus_flytrap",
    "carnivorous_pitcher_plant",
    "cave_bioluminescent_mushroom",
}

# Target only non-core species
targets = [f for f in blend_files if Path(f).stem not in core_species]
print(f"Blender Batch Renderer: Processing {len(targets)} species...")

out_base = Path("/tmp/turnaround_renders")
out_base.mkdir(parents=True, exist_ok=True)

t_all_start = time.time()

for idx, bf in enumerate(targets):
    slug = Path(bf).stem
    t0 = time.time()
    bpy.ops.wm.open_mainfile(filepath=bf)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512

    # Get bounds
    mesh_objs = [o for o in scene.collection.objects if o.type == "MESH"]
    min_coord = [float("inf")] * 3
    max_coord = [float("-inf")] * 3
    for obj in mesh_objs:
        for v in obj.bound_box:
            world_v = obj.matrix_world @ mathutils.Vector(v)
            for i in range(3):
                min_coord[i] = min(min_coord[i], world_v[i])
                max_coord[i] = max(max_coord[i], world_v[i])
    center = [(min_coord[i] + max_coord[i]) / 2.0 for i in range(3)]
    size = [max_coord[i] - min_coord[i] for i in range(3)]
    height = max(0.05, size[2])
    radius = max(0.05, max(size[0], size[1]) / 2.0)
    min_z = min_coord[2]

    # Lighting
    for o in list(scene.collection.objects):
        if o.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(o, do_unlink=True)
    if not scene.world:
        scene.world = bpy.data.worlds.new("StudioWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.07, 0.11, 1.0)
        bg.inputs["Strength"].default_value = 0.65

    k = bpy.data.lights.new("Key", "SUN")
    k.energy = 4.5
    k.color = (1.0, 0.97, 0.92)
    ko = bpy.data.objects.new("Key", k)
    ko.rotation_euler = (math.radians(52), math.radians(15), math.radians(35))
    scene.collection.objects.link(ko)

    f = bpy.data.lights.new("Fill", "SUN")
    f.energy = 2.0
    f.color = (0.75, 0.88, 1.0)
    fo = bpy.data.objects.new("Fill", f)
    fo.rotation_euler = (math.radians(45), math.radians(-10), math.radians(-120))
    scene.collection.objects.link(fo)

    r = bpy.data.lights.new("Rim", "SUN")
    r.energy = 3.5
    r.color = (0.9, 1.0, 0.9)
    ro = bpy.data.objects.new("Rim", r)
    ro.rotation_euler = (math.radians(-35), math.radians(20), math.radians(-160))
    scene.collection.objects.link(ro)

    # Circular Pedestal
    ped_r = max(0.8, radius * 1.5)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=ped_r,
        depth=max(0.02, height * 0.02),
        location=(center[0], center[1], min_z - 0.01),
        vertices=32
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

    # Camera
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 45
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    max_dim = max(radius * 2.0, height)
    dist = max(0.35, max_dim * 1.7)
    target = mathutils.Vector((center[0], center[1], center[2]))

    angles = [
        ("01_hero", mathutils.Vector((center[0] + dist * 0.72, center[1] - dist * 0.72, center[2] + height * 0.35))),
        ("02_front", mathutils.Vector((center[0], center[1] - dist * 1.05, center[2]))),
        ("03_side", mathutils.Vector((center[0] + dist * 1.05, center[1], center[2]))),
        ("04_top", mathutils.Vector((center[0] + 0.0001, center[1] + 0.0001, center[2] + dist * 1.15))),
    ]

    spec_dir = out_base / slug
    spec_dir.mkdir(parents=True, exist_ok=True)

    for key, pos in angles:
        cam_obj.location = pos
        rot = (target - pos).to_track_quat("-Z", "Y").to_euler()
        cam_obj.rotation_euler = rot
        scene.render.filepath = str(spec_dir / f"{key}.png")
        bpy.ops.render.render(write_still=True)

    elapsed = time.time() - t0
    print(f"[{idx+1}/{len(targets)}] Rendered {slug} in {elapsed:.2f}s")

print(f"Blender rendering completed in {time.time() - t_all_start:.2f}s")
"""

def composite_all():
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    try:
        font_title = ImageFont.truetype(font_path, 20)
        font_sub = ImageFont.truetype(font_path, 13)
        font_badge = ImageFont.truetype(font_path, 12)
    except Exception:
        font_title = font_sub = font_badge = None

    tile_w, tile_h = 512, 512
    header_h = 60
    positions = [
        (0, header_h),
        (tile_w, header_h),
        (0, header_h + tile_h),
        (tile_w, header_h + tile_h)
    ]
    labels = [
        "1. Hero Perspective (3/4)",
        "2. Front View",
        "3. Side View",
        "4. Top-Down Plan"
    ]

    out_base = Path("/tmp/turnaround_renders")
    species_dirs = sorted([d for d in out_base.iterdir() if d.is_dir()])
    print(f"Compositing {len(species_dirs)} turnaround sheets...")

    count = 0
    for sd in species_dirs:
        slug = sd.name
        tile_files = [
            sd / "01_hero.png",
            sd / "02_front.png",
            sd / "03_side.png",
            sd / "04_top.png"
        ]

        if not all(tf.exists() for tf in tile_files):
            print(f"Skipping {slug}, missing tiles")
            continue

        sheet = Image.new("RGB", (tile_w * 2, tile_h * 2 + header_h), (8, 12, 20))
        draw = ImageDraw.Draw(sheet)

        # Header banner
        draw.rectangle([0, 0, tile_w * 2, header_h], fill=(13, 19, 33))
        display_name = slug.replace("_", " ").upper()
        draw.text((20, 18), f"GENESIS ZERO 3D FLORA — {display_name}", fill=(56, 189, 248), font=font_title)
        draw.text((tile_w * 2 - 280, 22), "Blender 5.2.1 LTS · 4-Angle Turnaround", fill=(148, 163, 184), font=font_sub)

        for idx, tf in enumerate(tile_files):
            with Image.open(tf) as im:
                sheet.paste(im, positions[idx])
            x, y = positions[idx]
            draw.rectangle([x + 12, y + 12, x + 200, y + 36], fill=(15, 23, 42), outline=(56, 189, 248), width=1)
            draw.text((x + 20, y + 16), labels[idx], fill=(241, 245, 249), font=font_badge)

        # Save JPEG to both docs and web
        docs_target = DOCS_IMAGES / f"{slug}_turnaround.jpg"
        web_target = WEB_IMAGES / f"{slug}_turnaround.jpg"

        docs_target.parent.mkdir(parents=True, exist_ok=True)
        web_target.parent.mkdir(parents=True, exist_ok=True)

        sheet.save(str(docs_target), "JPEG", quality=92)
        sheet.save(str(web_target), "JPEG", quality=92)

        sz = docs_target.stat().st_size
        count += 1
        print(f"✓ [{count}/{len(species_dirs)}] Saved {slug}_turnaround.jpg ({sz / 1024:.1f} KB)")

def main():
    print("Starting Genesis Zero All-Flora Turnaround Generation Pipeline...")
    t0 = time.time()

    # Step 1: Run Blender headless batch render
    res = subprocess.run([
        BLENDER_BIN,
        "--background",
        "--python-expr",
        BLENDER_RENDER_SCRIPT
    ], cwd=str(ROOT))

    if res.returncode != 0:
        print("Blender render failed!")
        sys.exit(1)

    # Step 2: Composite all sheets with PIL
    composite_all()

    print(f"All turnarounds successfully generated in {time.time() - t0:.2f}s!")

if __name__ == "__main__":
    main()

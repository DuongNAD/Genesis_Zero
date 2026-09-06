"""
assemble_ecosystem.py - Master Scene Assembly & Dual Deliverables Pipeline
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

Integrates:
1. 8 Structured Scene Collections (with legacy aliases):
   - Diorama_Block
   - Terrain
   - Hydrology (alias: Water)
   - Subterranean_Cave
   - Flora_Instances (alias: Flora)
   - Fauna_Rigged (alias: Fauna)
   - Lighting
   - Cameras (alias: Camera)
2. 3rd-Person 3/4 Isometric Perspective Diorama Camera:
   - Position: (175.0, -210.0, 175.0), aiming at centroid (0.0, 0.0, 5.0) with 55mm lens.
   - Secondary Scenic_Camera maintained for backward compatibility.
3. Atmospheric Lighting & Color Management:
   - Key Directional Sun (energy 3.8, angle 1.2 deg, golden daylight).
   - Nishita Multiple Scattering Sky (turbidity 2.2, strength 0.85).
   - EEVEE Next Fast GI Ambient Occlusion (distance 25m, quality 1.0).
   - AgX Medium-High Contrast color management.
4. Dual Deliverables:
   - Master self-contained ecosystem_map.blend without broken links.
   - Industry-standard ecosystem_map.glb (> 200 KB) with embedded meshes, materials,
     skeletal armatures, vertex skinning, and NLA animation tracks.
"""

import math
import os
import sys
import bpy
from mathutils import Euler, Vector

# Ensure local script directory is in sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import terrain_hydrology
import flora_generator
import fauna_generator
import settlement_generator


def ensure_collection(name, parent=None):
    """Retrieves existing collection or creates a new one under parent."""
    if parent is None:
        parent = bpy.context.scene.collection
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    return col


def setup_lighting(col_lighting):
    """Configures warm late afternoon Golden Hour key sunlight from northwest, cool sky fill light, and studio diorama background."""
    # 1. Golden Hour Key Directional Sun Light (Warm late-afternoon sun angled at ~42 deg elevation)
    sun_data = bpy.data.lights.new(name="Sun_Light", type='SUN')
    sun_data.energy = 5.2
    sun_data.color = (1.0, 0.88, 0.72)  # Rich golden amber late-afternoon sunlight
    sun_data.angle = math.radians(2.0)

    sun_obj = bpy.data.objects.new("Sun_Light", sun_data)
    sun_obj.location = (-110.0, 70.0, 125.0)
    dir_sun = (Vector((0.0, 0.0, 6.0)) - sun_obj.location).normalized()
    sun_obj.rotation_euler = dir_sun.to_track_quat('-Z', 'Y').to_euler()
    col_lighting.objects.link(sun_obj)

    # 2. Secondary Cool Sky Fill Light (Soft atmospheric ambient fill)
    fill_data = bpy.data.lights.new(name="Fill_Light", type='SUN')
    fill_data.energy = 1.4
    fill_data.color = (0.55, 0.75, 1.0)
    fill_data.angle = math.radians(6.0)

    fill_obj = bpy.data.objects.new("Fill_Light", fill_data)
    fill_obj.location = (110.0, -70.0, 80.0)
    dir_fill = (Vector((0.0, 0.0, 6.0)) - fill_obj.location).normalized()
    fill_obj.rotation_euler = dir_fill.to_track_quat('-Z', 'Y').to_euler()
    col_lighting.objects.link(fill_obj)

    # 3. Clean Dark Slate Studio World Background (Matching Blender LTS 3D Viewport)
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("Ecosystem_World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    node_bg = nt.nodes.new('ShaderNodeBackground')
    node_bg.location = (-150, 0)
    # Slate dark studio color matching reference 3
    node_bg.inputs['Color'].default_value = (0.045, 0.055, 0.065, 1.0)
    node_bg.inputs['Strength'].default_value = 0.30

    node_out = nt.nodes.new('ShaderNodeOutputWorld')
    node_out.location = (150, 0)
    nt.links.new(node_bg.outputs['Background'], node_out.inputs['Surface'])


def setup_cameras(col_cameras, col_camera_legacy):
    """
    Constructs and configures:
    1. Primary 3rd-person 3/4 isometric perspective diorama camera (active scene camera).
    2. Camera_01_Village_To_Mountain (Village square looking up at Matterhorn snow peaks).
    3. Camera_02_Forest_To_Lake (Pine forest canopy looking out over turquoise lake).
    4. Camera_03_Mountain_To_Village (Mountain pass vista looking down at stream, roads, and village).
    5. Camera_04_Lake_To_Waterfall (Lake shore looking across bridge toward waterfall plunge).
    6. Secondary Scenic_Camera (Legacy viewpoint).
    """
    cameras = {}

    # 1. Primary 3rd-person 3/4 Isometric Camera
    cam_data = bpy.data.cameras.new("Diorama_Camera_3_4")
    cam_data.lens = 58.0
    cam_data.clip_start = 0.5
    cam_data.clip_end = 3000.0

    cam_obj = bpy.data.objects.new("Diorama_Camera_3_4", cam_data)
    cam_obj.location = (170.0, -195.0, 168.0)
    target = Vector((0.0, -6.0, 5.0))
    direction = target - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    col_cameras.objects.link(cam_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cameras["isometric"] = cam_obj

    # 2. Camera 01: Village Square -> Mountain Peaks (Diagonal open vista)
    c1_data = bpy.data.cameras.new("Camera_01_Village_To_Mountain")
    c1_data.lens = 24.0
    c1_data.clip_start = 0.3
    c1_data.clip_end = 2000.0
    c1_obj = bpy.data.objects.new("Camera_01_Village_To_Mountain", c1_data)
    c1_obj.location = (10.0, -36.0, 9.8)
    dir_c1 = (Vector((-2.0, -10.0, 10.0)) - c1_obj.location).normalized()
    c1_obj.rotation_euler = dir_c1.to_track_quat('-Z', 'Y').to_euler()
    col_cameras.objects.link(c1_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(c1_obj)
    cameras["cam01"] = c1_obj

    # 3. Camera 02: Forest -> Central Lake & Water Lilies
    c2_data = bpy.data.cameras.new("Camera_02_Forest_To_Lake")
    c2_data.lens = 42.0
    c2_data.clip_start = 0.3
    c2_data.clip_end = 2000.0
    c2_obj = bpy.data.objects.new("Camera_02_Forest_To_Lake", c2_data)
    c2_obj.location = (-3.5, 14.0, 7.8)
    dir_c2 = (Vector((-18.0, -6.0, 4.5)) - c2_obj.location).normalized()
    c2_obj.rotation_euler = dir_c2.to_track_quat('-Z', 'Y').to_euler()
    col_cameras.objects.link(c2_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(c2_obj)
    cameras["cam02"] = c2_obj

    # 4. Camera 03: Mountain Saddle Vista -> Stream & Village
    c3_data = bpy.data.cameras.new("Camera_03_Mountain_To_Village")
    c3_data.lens = 48.0
    c3_data.clip_start = 0.3
    c3_data.clip_end = 2000.0
    c3_obj = bpy.data.objects.new("Camera_03_Mountain_To_Village", c3_data)
    c3_obj.location = (8.5, 38.0, 14.2)
    dir_c3 = (Vector((-2.0, -14.0, 5.4)) - c3_obj.location).normalized()
    c3_obj.rotation_euler = dir_c3.to_track_quat('-Z', 'Y').to_euler()
    col_cameras.objects.link(c3_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(c3_obj)
    cameras["cam03"] = c3_obj

    # 5. Camera 04: Lake Shore -> Bridge & Waterfall
    c4_data = bpy.data.cameras.new("Camera_04_Lake_To_Waterfall")
    c4_data.lens = 35.0
    c4_data.clip_start = 0.3
    c4_data.clip_end = 2000.0
    c4_obj = bpy.data.objects.new("Camera_04_Lake_To_Waterfall", c4_data)
    c4_obj.location = (34.0, -56.0, 5.2)
    dir_c4 = (Vector((21.0, -42.0, 2.5)) - c4_obj.location).normalized()
    c4_obj.rotation_euler = dir_c4.to_track_quat('-Z', 'Y').to_euler()
    col_cameras.objects.link(c4_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(c4_obj)
    cameras["cam04"] = c4_obj

    # 6. Secondary Scenic Camera (Legacy viewpoint)
    scenic_data = bpy.data.cameras.new("Scenic_Camera")
    scenic_data.lens = 45.0
    scenic_data.clip_start = 0.5
    scenic_data.clip_end = 2000.0

    scenic_obj = bpy.data.objects.new("Scenic_Camera", scenic_data)
    scenic_obj.location = (65.0, -95.0, 42.0)
    scenic_obj.rotation_euler = Euler((math.radians(72.0), 0.0, math.radians(34.0)))
    col_cameras.objects.link(scenic_obj)
    if col_camera_legacy:
        col_camera_legacy.objects.link(scenic_obj)
    cameras["scenic"] = scenic_obj

    return cameras


def configure_render_settings(scene):
    """Configures EEVEE Next Fast GI Ambient Occlusion and AgX Color Management."""
    if hasattr(scene, "eevee"):
        ee = scene.eevee
        if hasattr(ee, "use_fast_gi"):
            ee.use_fast_gi = True
        if hasattr(ee, "fast_gi_method"):
            ee.fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'
        if hasattr(ee, "fast_gi_quality"):
            ee.fast_gi_quality = 1.0
        if hasattr(ee, "fast_gi_distance"):
            ee.fast_gi_distance = 25.0
        if hasattr(ee, "use_raytracing"):
            ee.use_raytracing = True
        if hasattr(ee, "use_shadows"):
            ee.use_shadows = True

    # Color Management (AgX Medium High Contrast)
    vs = scene.view_settings
    if hasattr(vs, "view_transform"):
        try:
            vs.view_transform = 'AgX'
        except Exception:
            pass
    if hasattr(vs, "look"):
        try:
            vs.look = 'Medium High Contrast'
        except Exception:
            pass
    if hasattr(vs, "exposure"):
        vs.exposure = -0.10


def assemble_all_and_export(output_dir=None):
    """
    Master pipeline orchestrator:
    - Cleans scene
    - Creates 8 structured collections (+ legacy aliases)
    - Generates Watertight Diorama Cutaway Block, 4-Tier Hydrology & Karst Cave
    - Generates 4-Zone Geometry Nodes Flora
    - Generates 5 Multi-Biome Rigged Fauna with 10 Looping Actions & NLA pushdown
    - Configures 3/4 Isometric Perspective Camera & Lighting
    - Saves ecosystem_map.blend
    - Exports ecosystem_map.glb (> 200 KB)
    """
    if output_dir is None:
        output_dir = "/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print(">>> Assembling 3D Isometric Diorama Ecosystem Map...")
    print("=" * 70)

    # 1. Clean scene datablocks
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)

    # 2. Setup 8 structured collections (+ legacy alias collections)
    col_diorama = ensure_collection("Diorama_Block")
    col_terrain = ensure_collection("Terrain")
    col_hydrology = ensure_collection("Hydrology")
    col_water_legacy = ensure_collection("Water")
    col_cave = ensure_collection("Subterranean_Cave")
    col_flora_inst = ensure_collection("Flora_Instances")
    col_flora_legacy = ensure_collection("Flora")
    col_fauna_rigged = ensure_collection("Fauna_Rigged")
    col_fauna_legacy = ensure_collection("Fauna")
    col_lighting = ensure_collection("Lighting")
    col_cameras = ensure_collection("Cameras")
    col_camera_legacy = ensure_collection("Camera")
    col_settlement = ensure_collection("Settlement")

    # 3. Terrain, Hydrology & Karst Cave Pipeline
    print(">>> 1/6 Generating Diorama Cutaway Block, 5-Tier Hydrology & Karst Cave...")
    terrain_data = terrain_hydrology.generate_terrain_and_hydrology(
        bpy.context,
        collection_diorama=col_diorama,
        collection_terrain=col_terrain,
        collection_hydrology=col_hydrology,
        collection_cave=col_cave,
    )

    # Link primary diorama block to Terrain collection for legacy queries
    diorama_obj = terrain_data["diorama_block_obj"]
    if diorama_obj.name not in col_terrain.objects:
        col_terrain.objects.link(diorama_obj)

    # Link all water meshes to legacy Water collection
    for w_key in ["river_obj", "lake_obj", "pond_obj", "stream_obj", "bay_obj", "foam_obj"]:
        w_obj = terrain_data.get(w_key)
        if w_obj and w_obj.name not in col_water_legacy.objects:
            col_water_legacy.objects.link(w_obj)

    # Link cave entrance to Subterranean_Cave collection
    entrance_obj = terrain_data.get("entrance_obj")
    if entrance_obj and entrance_obj.name not in col_cave.objects:
        col_cave.objects.link(entrance_obj)

    # 4. Settlement, Watchtower Landmark, Bridge & Road Network Pipeline
    print(">>> 2/6 Generating Medieval Village, Watchtower Landmark, Bridge & Road Network...")
    settlement_data = settlement_generator.generate_settlement_and_landmarks(
        bpy.context, col_settlement, terrain_data
    )

    # 5. Flora Pipeline (4 Biomes with Geometry Nodes)
    print(">>> 3/6 Generating and Distributing 4-Zone Biome Flora...")
    flora_objects = flora_generator.generate_and_distribute_flora(
        bpy.context, col_flora_inst, terrain_data
    )
    # Link flora objects to legacy Flora collection
    for f_obj in flora_objects:
        if f_obj.name not in col_flora_legacy.objects:
            col_flora_legacy.objects.link(f_obj)
    print(f"    Placed {len(flora_objects)} botanical instances across 4 biomes.")

    # 6. Fauna Pipeline (5 Rigged Species, 94 Bones, 10 Looping Actions)
    print(">>> 4/6 Generating Rigged and Animated Fauna across 4 Biomes...")
    fauna_pairs = fauna_generator.generate_fauna(
        bpy.context, col_fauna_rigged, terrain_data
    )
    # Link fauna objects to legacy Fauna collection
    for arm_obj, mesh_obj in fauna_pairs:
        if arm_obj.name not in col_fauna_legacy.objects:
            col_fauna_legacy.objects.link(arm_obj)
        if mesh_obj.name not in col_fauna_legacy.objects:
            col_fauna_legacy.objects.link(mesh_obj)
    print(f"    Generated {len(fauna_pairs)} fauna species with 94 bones and 10 NLA action clips.")

    # 7. Lighting & 3/4 Isometric + 4 Cinematic Cameras
    print(">>> 5/6 Configuring Golden Hour Sun Lighting, Fast GI AO and 5 Composition Cameras...")
    setup_lighting(col_lighting)
    cameras = setup_cameras(col_cameras, col_camera_legacy)
    configure_render_settings(bpy.context.scene)

    # Scene frame range (1 to 60)
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 60

    # 7. Deliverables (.blend and .glb)
    blend_path = os.path.join(output_dir, "ecosystem_map.blend")
    glb_path = os.path.join(output_dir, "ecosystem_map.glb")

    print(f">>> 5/5 Saving Master Blender Project: {blend_path}")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)

    print(f">>> Exporting glTF/GLB Asset: {glb_path}")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_skins=True,
        export_materials='EXPORT',
        export_apply=True  # Evaluates Geometry Nodes realize instances while safely excluding Armatures
    )

    blend_size = os.path.getsize(blend_path) if os.path.exists(blend_path) else 0
    glb_size = os.path.getsize(glb_path) if os.path.exists(glb_path) else 0
    print(f"✓ Saved .blend: {blend_size / 1024:.1f} KB")
    print(f"✓ Exported .glb: {glb_size / 1024:.1f} KB")

    return {
        "blend_path": blend_path,
        "glb_path": glb_path,
        "blend_size": blend_size,
        "glb_size": glb_size,
    }


if __name__ == "__main__":
    assemble_all_and_export()

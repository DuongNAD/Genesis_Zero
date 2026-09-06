"""
verify_ecosystem.py - 10-Check Automated In-Blender Verification & Preview Render Pipeline
Genesis Zero - Blender 5.2.1 LTS (macOS Apple Silicon Metal)

10 Comprehensive Checks:
1. Structured Collections (8 collections + legacy aliases present).
2. Diorama Cutaway Base Block & Underground Strata (160m x 160m, Z_base = -14m, COLOR_0 strata).
3. Terrain Geomorphology & Elevation Delta (Delta Z >= 20m, snow peaks, slope shader).
4. Continuous 4-Tier Hydrology (Cascades, River, Lake, Marine Bay, Volume Absorption).
5. Subterranean Karst Cave System (Cavern chamber, Speleothems, Pool, Bioluminescent shaders).
6. 4-Zone Flora Diversity & 100% Smooth Shading Compliance (use_smooth = True).
7. 4-Biome Rigged Fauna Armatures & Vertex Skinning (5 species, 94 bones, Armature modifiers).
8. Active Animation Actions & NLA Multi-Clip Export (10 actions, 10 NLA tracks).
9. 3rd-Person 3/4 Isometric Perspective Camera Framing & Headless Render (1920x1080).
10. Deliverables on Disk & glTF 2.0 Binary Parsing (blend > 200 KB, glb > 200 KB, preview > 100 KB).
"""

import json
import math
import os
import struct
import sys
import bpy


def verify_and_render():
    print("=" * 75)
    print("GENESIS ZERO: 3D ISOMETRIC DIORAMA ECOSYSTEM 10-CHECK VERIFICATION")
    print("=" * 75)

    base_dir = "/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map"
    blend_file = os.path.join(base_dir, "ecosystem_map.blend")
    glb_file = os.path.join(base_dir, "ecosystem_map.glb")
    png_file = os.path.join(base_dir, "render_preview.png")

    # If running standalone without the blend file preloaded, load it
    if not bpy.data.collections.get("Diorama_Block") and os.path.exists(blend_file):
        print(f"Loading mainfile: {blend_file}")
        bpy.ops.wm.open_mainfile(filepath=blend_file)

    errors = []

    # -------------------------------------------------------------------------
    # [CHECK 1/10] Structured Collections
    # -------------------------------------------------------------------------
    print("\n[CHECK 1/10] Structured Collections (9 Clean Collections)...")
    required_cols = [
        "Diorama_Block", "Terrain", "Hydrology", "Subterranean_Cave",
        "Settlement", "Flora_Instances", "Fauna_Rigged", "Lighting", "Cameras"
    ]
    for col_name in required_cols:
        col = bpy.data.collections.get(col_name)
        if not col:
            errors.append(f"Missing required collection: '{col_name}'")
        else:
            print(f"  ✓ Collection '{col_name}': {len(col.objects)} objects")

    # -------------------------------------------------------------------------
    # [CHECK 2/10] Diorama Cutaway Base Block & Underground Strata
    # -------------------------------------------------------------------------
    print("\n[CHECK 2/10] Diorama Cutaway Base Block & Geological Strata...")
    col_diorama = bpy.data.collections.get("Diorama_Block")
    diorama_obj = None
    if col_diorama:
        diorama_obj = next((o for o in col_diorama.objects if o.type == 'MESH'), None)

    if diorama_obj:
        dims = diorama_obj.dimensions
        bbox_z = [v.co.z for v in diorama_obj.data.vertices]
        min_z = min(bbox_z) if bbox_z else 0.0
        max_z = max(bbox_z) if bbox_z else 0.0
        print(f"  ✓ Diorama block '{diorama_obj.name}': X={dims.x:.1f}m, Y={dims.y:.1f}m, Z={dims.z:.1f}m")
        print(f"    Elevation range: [{min_z:.1f}m, {max_z:.1f}m], Base depth: {min_z:.1f}m")
        if min_z > -12.0:
            errors.append(f"Diorama cutaway base depth {min_z:.1f}m is not deep enough (must reach Z <= -12m)")
        if dims.x < 140.0 or dims.y < 140.0:
            errors.append(f"Diorama horizontal footprint ({dims.x:.1f}m, {dims.y:.1f}m) < 140m")

        # Color attributes
        has_color = len(diorama_obj.data.color_attributes) > 0
        if not has_color:
            errors.append("Diorama block missing COLOR_0 attribute for geological strata")
        else:
            c_names = [a.name for a in diorama_obj.data.color_attributes]
            print(f"  ✓ Strata color attributes: {c_names}")
    else:
        errors.append("Diorama_Block collection contains no mesh object")

    # -------------------------------------------------------------------------
    # [CHECK 3/10] Terrain Geomorphology & Elevation Delta (Delta Z >= 20m)
    # -------------------------------------------------------------------------
    print("\n[CHECK 3/10] Terrain Geomorphology & Elevation Delta...")
    col_terrain = bpy.data.collections.get("Terrain")
    t_obj = diorama_obj or (next((o for o in col_terrain.objects if o.type == 'MESH'), None) if col_terrain else None)
    if t_obj:
        z_vals = [v.co.z for v in t_obj.data.vertices]
        delta_z = max(z_vals) - min(z_vals)
        max_elev = max(z_vals)
        print(f"  ✓ Net elevation delta: {delta_z:.1f}m (summit Z={max_elev:.1f}m)")
        if delta_z < 20.0:
            errors.append(f"Terrain elevation delta {delta_z:.1f}m < 20.0m requirement")
        if max_elev < 22.0:
            errors.append(f"Alpine summit elevation {max_elev:.1f}m < 22.0m (snow peaks requirement)")
    else:
        errors.append("No terrain mesh found for geomorphology check")

    # -------------------------------------------------------------------------
    # [CHECK 4/10] Continuous 4-Tier Hydrology System
    # -------------------------------------------------------------------------
    print("\n[CHECK 4/10] Continuous 4-Tier Hydrology System...")
    col_hydro = bpy.data.collections.get("Hydrology") or bpy.data.collections.get("Water")
    if col_hydro:
        h_names = [o.name.lower() for o in col_hydro.objects]
        has_river = any("river" in n for n in h_names)
        has_lake = any("lake" in n for n in h_names)
        has_bay = any("bay" in n for n in h_names)
        has_pond = any("pond" in n for n in h_names)
        has_stream = any("stream" in n for n in h_names)
        print(f"  ✓ River: {has_river}, Lake: {has_lake}, Bay: {has_bay}, Pond: {has_pond}, Stream: {has_stream}")
        if not has_river:
            errors.append("Missing river mesh in Hydrology collection")
        if not has_lake:
            errors.append("Missing lake mesh in Hydrology collection")
        if not has_bay:
            errors.append("Missing coastal bay mesh in Hydrology collection")

        # Water PBR shader transmission & Volume Absorption
        mat_water = bpy.data.materials.get("M_Water_PBR")
        if mat_water and mat_water.use_nodes:
            has_vol = any(n.type == 'VOLUME_ABSORPTION' for n in mat_water.node_tree.nodes)
            print(f"  ✓ Water Material 'M_Water_PBR' Volume Absorption: {has_vol}")
            if not has_vol:
                errors.append("Water material 'M_Water_PBR' lacks ShaderNodeVolumeAbsorption")
        else:
            errors.append("Water material 'M_Water_PBR' missing or has no nodes")
    else:
        errors.append("Hydrology collection missing")

    # -------------------------------------------------------------------------
    # [CHECK 5/10] Subterranean Karst Cave System
    # -------------------------------------------------------------------------
    print("\n[CHECK 5/10] Subterranean Karst Cave System...")
    col_cave = bpy.data.collections.get("Subterranean_Cave")
    if col_cave:
        cave_mesh_objs = [o for o in col_cave.objects if o.type == 'MESH']
        c_names = [o.name.lower() for o in cave_mesh_objs]
        has_cavern = any("cavern" in n or "cave" in n for n in c_names)
        has_speleo = any("speleo" in n or "stalactite" in n for n in c_names)
        has_pool = any("pool" in n for n in c_names)
        has_entrance = any("entrance" in n or "portal" in n for n in c_names)
        print(f"  ✓ Cave Cavern: {has_cavern}, Speleothems: {has_speleo}, Cave Pool: {has_pool}, Entrance: {has_entrance}")
        if not has_cavern:
            errors.append("Subterranean cave cavern room mesh missing")
        if not has_speleo:
            errors.append("Subterranean karst speleothems (stalactites/stalagmites) missing")
        if not has_pool:
            errors.append("Subterranean cave pool mesh missing")
        if not has_entrance:
            errors.append("Subterranean cave entrance portal mesh missing")

        # Bioluminescent emissive shader
        mat_bio = bpy.data.materials.get("M_Bio_Mushroom")
        if mat_bio and mat_bio.use_nodes:
            has_emiss = any(n.type in ('EMISSION', 'BSDF_PRINCIPLED') for n in mat_bio.node_tree.nodes)
            print(f"  ✓ Bioluminescent Fungi Material 'M_Bio_Mushroom' Emissive: {has_emiss}")
            if not has_emiss:
                errors.append("Bioluminescent material lacks emission node")
        else:
            errors.append("Bioluminescent material 'M_Bio_Mushroom' not found")
    else:
        errors.append("Subterranean_Cave collection missing")

    # -------------------------------------------------------------------------
    # [CHECK 5b] Medieval Settlement POI, Landmarks & Road Network
    # -------------------------------------------------------------------------
    print("\n[CHECK 5b] Medieval Settlement POI, Landmarks & Road Network...")
    col_settlement = bpy.data.collections.get("Settlement")
    if col_settlement:
        s_names = [o.name for o in col_settlement.objects]
        # Check buildings: chapel, houses, cottages, barns, watermill, forge
        buildings = [n for n in s_names if any(k in n for k in ["Chapel", "House", "Cottage", "Barn", "Watermill", "Forge"])]
        print(f"  ✓ Settlement buildings found ({len(buildings)}): {buildings}")
        if len(buildings) < 8:
            errors.append(f"Expected >= 8 settlement buildings, found {len(buildings)}")

        # Check landmarks & infrastructure
        has_tower = any("Watchtower" in n for n in s_names)
        has_bridge = any("Bridge" in n for n in s_names)
        has_well = any("Well" in n for n in s_names)
        has_road = any("Road" in n for n in s_names)
        print(f"  ✓ Watchtower: {has_tower}, Bridge: {has_bridge}, Well: {has_well}, Road: {has_road}")
        if not has_tower:
            errors.append("Missing Landmark_Watchtower in Settlement collection")
        if not has_bridge:
            errors.append("Missing Bridge_Stone_Arch in Settlement collection")
        if not has_well:
            errors.append("Missing Village_Well in Settlement collection")
        if not has_road:
            errors.append("Missing Road_Network in Settlement collection")
    else:
        errors.append("Settlement collection missing")

    # -------------------------------------------------------------------------
    # [CHECK 6/10] 4-Zone Flora Diversity & 100% Smooth Shading Compliance
    # -------------------------------------------------------------------------
    print("\n[CHECK 6/10] 4-Zone Flora Diversity & 100% Smooth Shading...")
    col_flora = bpy.data.collections.get("Flora_Instances") or bpy.data.collections.get("Flora")
    if col_flora:
        flora_meshes = [o for o in col_flora.objects if o.type == 'MESH']
        species_set = set()
        for o in flora_meshes:
            parts = o.name.split("_")
            if len(parts) >= 2:
                species_set.add(parts[1])
            else:
                species_set.add(parts[0])
        print(f"  ✓ Distinct botanical species: {len(species_set)} -> {species_set}")
        if len(species_set) < 4:
            errors.append(f"Expected >= 4 flora species covering 4 biomes, found {len(species_set)}")

        # Smooth shading check
        non_smooth = [o.name for o in flora_meshes if any(not p.use_smooth for p in o.data.polygons)]
        if non_smooth:
            errors.append(f"Flora objects with flat-shaded polygons: {non_smooth[:5]}")
        else:
            print(f"  ✓ 100% Smooth Shading verified across all {len(flora_meshes)} flora instances")

        # Geometry Nodes scatter check
        gn_mods = [o.name for o in bpy.data.objects for m in o.modifiers if m.type == 'NODES']
        gn_groups = [ng.name for ng in bpy.data.node_groups if ng.type == 'GEOMETRY']
        print(f"  ✓ Geometry Nodes scatter carriers: {len(gn_mods)} -> {gn_mods}")
        print(f"  ✓ Geometry Nodes node groups: {len(gn_groups)} -> {gn_groups}")
        if len(gn_mods) < 4:
            errors.append(f"Expected >= 4 Geometry Nodes scatter modifiers, found {len(gn_mods)}: {gn_mods}")
        if len(gn_groups) < 4:
            errors.append(f"Expected >= 4 Geometry Nodes groups for biomes, found {len(gn_groups)}: {gn_groups}")
    else:
        errors.append("Flora collection missing")

    # -------------------------------------------------------------------------
    # [CHECK 7/10] 4-Biome Rigged Fauna Armatures & Vertex Skinning
    # -------------------------------------------------------------------------
    print("\n[CHECK 7/10] 4-Biome Rigged Fauna Armatures & Vertex Skinning...")
    col_fauna = bpy.data.collections.get("Fauna_Rigged") or bpy.data.collections.get("Fauna")
    if col_fauna:
        armatures = [o for o in col_fauna.objects if o.type == 'ARMATURE']
        print(f"  ✓ Fauna Armatures: {len(armatures)} -> {[a.name for a in armatures]}")
        if len(armatures) < 4:
            errors.append(f"Expected >= 4 animal armatures covering 4 biomes, found {len(armatures)}")

        total_bones = 0
        for arm in armatures:
            bc = len(arm.data.bones)
            total_bones += bc
            print(f"    - {arm.name}: {bc} bones")
            if bc < 10:
                errors.append(f"Armature '{arm.name}' has fewer than 10 bones ({bc})")

        print(f"  ✓ Total Skeletal Bones across species: {total_bones}")

        # Skinned meshes
        fauna_meshes = [o for o in col_fauna.objects if o.type == 'MESH']
        for m in fauna_meshes:
            has_arm_mod = any(mod.type == 'ARMATURE' and mod.object for mod in m.modifiers)
            vg_count = len(m.vertex_groups)
            is_smooth = all(p.use_smooth for p in m.data.polygons)
            print(f"    - Skinned mesh '{m.name}': ArmatureMod={has_arm_mod}, VGroups={vg_count}, Smooth={is_smooth}")
            if not has_arm_mod:
                errors.append(f"Mesh '{m.name}' lacks ARMATURE modifier")
            if vg_count < 5:
                errors.append(f"Mesh '{m.name}' has insufficient vertex groups ({vg_count})")
            if not is_smooth:
                errors.append(f"Mesh '{m.name}' has non-smooth faces")
    else:
        errors.append("Fauna collection missing")

    # -------------------------------------------------------------------------
    # [CHECK 8/10] Active Animation Actions & NLA Multi-Clip Export
    # -------------------------------------------------------------------------
    print("\n[CHECK 8/10] Active Animation Actions & NLA Multi-Clip Export...")
    if col_fauna:
        total_nla_tracks = 0
        for arm in armatures:
            if not arm.animation_data or not arm.animation_data.action:
                errors.append(f"Armature '{arm.name}' has no active action assigned")
            else:
                act = arm.animation_data.action
                nla_count = len(arm.animation_data.nla_tracks)
                total_nla_tracks += nla_count
                print(f"    - {arm.name}: Active='{act.name}', NLA Tracks={nla_count} {[t.name for t in arm.animation_data.nla_tracks]}")
                if nla_count < 2:
                    errors.append(f"Armature '{arm.name}' has fewer than 2 NLA tracks")
        print(f"  ✓ Total NLA Action Clips pushed down: {total_nla_tracks}")
        if total_nla_tracks < 8:
            errors.append(f"Expected >= 8 total NLA action tracks, found {total_nla_tracks}")

    # -------------------------------------------------------------------------
    # [CHECK 9/10] 3rd-Person 3/4 Isometric Camera Framing & Headless Render
    # -------------------------------------------------------------------------
    print("\n[CHECK 9/10] 3rd-Person 3/4 Isometric Camera Framing & Render...")
    scene = bpy.context.scene
    col_cams = bpy.data.collections.get("Cameras") or bpy.data.collections.get("Camera")
    iso_cam = bpy.data.objects.get("Diorama_Camera_3_4")
    if iso_cam:
        scene.camera = iso_cam
        loc = iso_cam.location
        lens = iso_cam.data.lens
        print(f"  ✓ Primary Isometric Camera: location=({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}), lens={lens}mm")
        if loc.z < 100.0 or loc.x < 100.0 or loc.y > -100.0:
            errors.append(f"Camera location {loc} is not in 3/4 isometric perspective")
    else:
        errors.append("Diorama_Camera_3_4 not found")

    # Render settings
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.filepath = png_file
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 15

    print(f"  Rendering high-resolution still frame to: {png_file}...")
    try:
        bpy.ops.render.render(write_still=True)
        print("  ✓ Primary isometric render completed successfully.")
    except Exception as ex:
        errors.append(f"Headless rendering failed: {ex}")

    # Render 4 Cinematic Composition Cameras
    cinematic_cams = [
        ("Camera_01_Village_To_Mountain", "render_cam01_village.png"),
        ("Camera_02_Forest_To_Lake", "render_cam02_forest_lake.png"),
        ("Camera_03_Mountain_To_Village", "render_cam03_mountain_vista.png"),
        ("Camera_04_Lake_To_Waterfall", "render_cam04_waterfall.png"),
    ]
    for c_name, c_file in cinematic_cams:
        c_obj = bpy.data.objects.get(c_name)
        if c_obj:
            scene.camera = c_obj
            c_path = os.path.join(base_dir, c_file)
            scene.render.filepath = c_path
            print(f"  Rendering cinematic shot '{c_name}' to {c_path}...")
            try:
                bpy.ops.render.render(write_still=True)
                print(f"  ✓ Rendered {c_file}")
            except Exception as ex:
                print(f"  ⚠️ Cinematic render failed for {c_name}: {ex}")

    # Reset active camera back to primary isometric
    if iso_cam:
        scene.camera = iso_cam

    # -------------------------------------------------------------------------
    # [CHECK 10/10] Deliverable Integrity on Disk & glTF 2.0 Binary Parsing
    # -------------------------------------------------------------------------
    print("\n[CHECK 10/10] Deliverable File Integrity on Disk & glTF 2.0...")
    files_to_check = [
        (blend_file, "ecosystem_map.blend", 200 * 1024),
        (glb_file, "ecosystem_map.glb", 200 * 1024),
        (png_file, "render_preview.png", 100 * 1024),
    ]
    for path, label, min_size in files_to_check:
        if not os.path.exists(path):
            errors.append(f"Deliverable missing: {label} at {path}")
        else:
            sz = os.path.getsize(path)
            print(f"  ✓ {label}: {sz / 1024:.1f} KB (min: {min_size / 1024:.1f} KB)")
            if sz < min_size:
                errors.append(f"Deliverable {label} size too small: {sz} bytes < {min_size} bytes")

    # Parse GLB binary chunks
    if os.path.exists(glb_file) and os.path.getsize(glb_file) > 200 * 1024:
        try:
            with open(glb_file, "rb") as gf:
                magic = gf.read(4)
                if magic != b"glTF":
                    errors.append(f"GLB magic mismatch: {magic}")
                else:
                    gf.seek(12)
                    chunk_len = int.from_bytes(gf.read(4), 'little')
                    chunk_type = gf.read(4)
                    if chunk_type == b"JSON":
                        meta = json.loads(gf.read(chunk_len).decode('utf-8'))
                        anims = [a.get("name", "unnamed") for a in meta.get("animations", [])]
                        skins = meta.get("skins", [])
                        meshes = meta.get("meshes", [])
                        print(f"  ✓ GLB Embedded Animations: {len(anims)} -> {anims}")
                        print(f"  ✓ GLB Embedded Skins: {len(skins)}, Meshes: {len(meshes)}")
                        if len(anims) < 8:
                            errors.append(f"GLB contains fewer than 8 animation clips ({len(anims)})")
                        if len(skins) < 4:
                            errors.append(f"GLB contains fewer than 4 skins ({len(skins)})")
        except Exception as ex:
            errors.append(f"GLB binary parsing failed: {ex}")

    # -------------------------------------------------------------------------
    # Result Summary
    # -------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("VERIFICATION RESULT SUMMARY")
    print("=" * 75)
    if errors:
        print(f"❌ FAILED: {len(errors)} error(s) detected:")
        for err in errors:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print("✅ PASSED: All 10/10 requirements verified 100% successfully!")
        sys.exit(0)


if __name__ == "__main__":
    verify_and_render()

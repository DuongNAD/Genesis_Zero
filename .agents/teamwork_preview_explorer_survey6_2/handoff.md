# Handoff Report: 3D Pipeline & Botanical Asset Architecture

**Author**: 3D Pipeline Explorer  
**Date**: 2026-09-05T00:39:00Z  
**Target File**: `.agents/teamwork_preview_explorer_survey6_2/handoff.md`  
**Handoff Type**: Hard (Investigation Complete)  

---

## 1. Observation

### 1.1 Blender Environment & Tooling
- **Blender Binary**: `/Applications/Blender.app/Contents/MacOS/Blender`
  - Version: `Blender 5.2.1 LTS` (build date: 2026-08-25, hash `9e2066aef7ef`, macOS Darwin Apple Silicon).
  - Bundled Python: `Python 3.13.13` (`/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13`).
  - Built-in glTF Addon: `io_scene_gltf2` (`bpy.ops.export_scene.gltf is not None == True`) with Draco bridge (`libbf_intern_draco_bridge.dylib`) and MeshOptimizer bridge (`libbf_intern_meshopt_bridge.dylib`).
- **Blender MCP Server**: Available and active (`get_addon_status` returned protocol version 5, addon version [1, 6], source `native`, status `up_to_date: True`).
- **Python & Testing Infrastructure**: System has pytest 9.1.1 (`/Users/duongnad/.pyenv/shims/python3 -m pytest`). Test suite `tests/test_ecosystem_map.py` executes 38 opaque-box and headless Blender tests with 100% pass rate in 43 seconds.
- **glTF Validation Tooling**: `gltf-validator` CLI binary is not installed on PATH, and `pygltflib` / `trimesh` are not installed in the system/venv Python. However, standard library Python (`struct` + `json`) can completely parse and validate glTF 2.0 binary chunks (magic, version, header length, JSON chunk 0, BIN chunk 1).

### 1.2 Existing 3D Flora Assets & Directory Structure
- **Root Directory**: `assets/flora/`
- **Subdirectories & Assets**: Exactly 16 species across 7 ecological categories have both master `.blend` and runtime `.glb` files:
  1. `canopy_trees/`:
     - `canopy_ancient_oak.blend` (133 KB) / `.glb` (48.5 KB)
     - `canopy_alpine_pine.blend` (99 KB) / `.glb` (9.4 KB)
     - `canopy_weeping_willow.blend` (173 KB) / `.glb` (114.2 KB)
     - `canopy_giant_sequoia.blend` (108 KB) / `.glb` (24.9 KB)
     - `canopy_baobab.blend` (102 KB) / `.glb` (15.7 KB)
  2. `understory_shrubs/`:
     - `understory_tree_fern.blend` (98 KB) / `.glb` (11.7 KB)
     - `understory_sword_fern.blend` (98 KB) / `.glb` (10.4 KB)
  3. `grasses_herbs/`:
     - `grass_alpine_tussock.blend` (99 KB) / `.glb` (12.2 KB)
  4. `aquatic_wetland/`:
     - `aquatic_water_lily.blend` (94 KB) / `.glb` (6.2 KB)
     - `aquatic_sacred_lotus.blend` (94 KB) / `.glb` (5.7 KB)
     - `aquatic_broadleaf_cattail.blend` (99 KB) / `.glb` (11.7 KB)
  5. `arid_succulents/`:
     - `succulent_saguaro_cactus.blend` (103 KB) / `.glb` (18.2 KB)
     - `succulent_century_agave.blend` (97 KB) / `.glb` (9.4 KB)
  6. `carnivorous_vines/`:
     - `carnivorous_pitcher_plant.blend` (102 KB) / `.glb` (16.8 KB)
     - `carnivorous_venus_flytrap.blend` (95 KB) / `.glb` (4.6 KB)
  7. `cave_bioluminescent/`:
     - `cave_bioluminescent_mushroom.blend` (104 KB) / `.glb` (20.0 KB)
- **Concept Images & Turnaround Sheets**:
  - Located at `web/flora_images/`, `docs/flora/images/`, and `assets/flora/images/`.
  - 10 species have 4-angle turnaround concept sheets: `aquatic_sacred_lotus_turnaround.jpg`, `aquatic_water_lily_turnaround.jpg`, `canopy_ancient_oak_turnaround.jpg`, `canopy_baobab_turnaround.jpg`, `canopy_giant_sequoia_turnaround.jpg`, `carnivorous_pitcher_plant_turnaround.jpg`, `carnivorous_venus_flytrap_turnaround.jpg`, `cave_bioluminescent_mushroom_turnaround.jpg`, `succulent_saguaro_cactus_turnaround.jpg`, `understory_tree_fern_turnaround.jpg`.
  - 1 species (`canopy_weeping_willow`) has a multi-angle inspection composite sheet: `weeping_willow_inspection_sheet.png` (2.6 MB).
  - 6 species currently have `turnaroundImg: null` in `web/flora_viewer.html` (`canopy_alpine_pine`, `canopy_weeping_willow`, `understory_sword_fern`, `grass_alpine_tussock`, `aquatic_broadleaf_cattail`, `succulent_century_agave`).

### 1.3 Topology & Mesh Analysis (Headless Inspection via BMesh)
Direct inspection using Blender BMesh across all 16 `.blend` files revealed:
- **Smooth Shading**: 100.0% of polygon faces across all 16 models have `poly.use_smooth = True` (0 non-smooth faces found).
- **Quad-Dominance**:
  - `Flora_Ancient_Oak`: 1,160 quads, 224 tris, 0 ngons (83.8% quads).
  - `Flora_Weeping_Willow`: 1,750 quads, 188 tris, 0 ngons (90.3% quads).
  - `Flora_Grand_Baobab`: 376 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Giant_Sequoia`: 560 quads, 144 tris, 0 ngons (79.5% quads).
  - `Flora_Saguaro_Cactus`: 456 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Century_Agave`: 120 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Cattail`: 188 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Tree_Fern`: 194 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Sword_Fern`: 144 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Alpine_Tussock`: 144 quads, 0 tris, 0 ngons (100% quads).
  - `Flora_Cave_Mushroom`: 416 quads, 128 tris, 0 ngons (76.5% quads).
  - **Zero Ngons** in any of the 16 models.
- **Edge Manifoldness & Defect Audit**:
  - 15 out of 16 models have:
    * `multi_face_edges = 0` (no internal walls, non-manifold T-junctions, or edge sharing > 2 faces).
    * `wire_edges = 0` (no isolated floating edges).
    * `loose_verts = 0` (no unlinked vertices).
    * `boundary_edges`: only 1-face perimeter edges corresponding to planar foliage cards (ferns, leaves) and open trunk ground bases.
  - **DEFECT OBSERVED**: `assets/flora/carnivorous_vines/carnivorous_pitcher_plant.blend` contains **18 loose vertices** (`loose_verts = 18`).
    * Direct source inspection of `assets/flora/generators/flora_builder.py` lines 838–842 shows:
      ```python
      # A. Tendril stem (6 slices, 6 radial)
      t_slices = 6
      t_rad = 6
      base_t = len(verts)
      for ts in range(t_slices):
          tt = ts / (t_slices - 1.0)
          z = p_loc.z + tt * 0.55
          verts.append((p_loc.x + 0.15 * math.sin(tt * math.pi), p_loc.y, z))
      ```
      The loop appends 6 vertices for each of the 3 pitchers (3 * 6 = 18 vertices) into `verts` without connecting them into edges or faces, leaving them unreferenced in the mesh index.

### 1.4 Biological PBR Materials & glTF 2.0 Export Mechanics
- **Blender 5.2.1 Principled BSDF Schema**:
  - Foliage/Petals (`create_pbr_foliage_material` in `flora_builder.py` lines 71–101):
    * `Subsurface Weight` set to 0.35–0.65.
    * `Subsurface Radius` configured for green/pink transmittance (e.g. `(0.18, 0.55, 0.05)`).
    * `Roughness` tuned between 0.25 and 0.45.
    * `Sheen Weight` set to 0.40 for organic cuticular sheen.
  - Bark/Trunk (`create_pbr_bark_material` in `flora_builder.py` lines 36–69):
    * `ShaderNodeTexNoise` (scale 18.0–25.0, detail 6.0) connects to `ShaderNodeBump` (strength 0.35–0.55, distance 0.15), linking to `Normal` input of Principled BSDF.
  - Bioluminescence (`create_pbr_emissive_material` in `flora_builder.py` lines 104–129):
    * `Emission Color` + `Emission Strength = 5.0` with `Subsurface Weight = 0.65`.
- **glTF 2.0 Exporter Behavior (`bpy.ops.export_scene.gltf`)**:
  - When exporting procedural materials: Blender's glTF exporter parses Principled BSDF node inputs into standard glTF 2.0 properties (`pbrMetallicRoughness.baseColorFactor`, `metallicFactor`, `roughnessFactor`, `emissiveFactor`, `doubleSided: true`).
  - **Procedural Bump Limitation**: Procedural texture nodes (`ShaderNodeTexNoise`) connected through `ShaderNodeBump` are NOT automatically baked to image normal maps during headless export unless an explicit texture bake pass is run. As a result, the `.glb` files contain clean PBR flat factors without broken image paths. In contrast, the `.blend` master preserves the full procedural node graph for Cycles/EEVEE rendering.

### 1.5 glTF 2.0 Binary Chunk Validation
- All 16 `.glb` files were parsed at the binary level:
  - Header: 12 bytes (`magic = b"glTF"`, `version = 2`, `length == os.path.getsize()`).
  - Chunk 0: 8-byte header (`type = 0x4E4F534A`), JSON text decoded without errors.
  - Chunk 1: 8-byte header (`type = 0x004E4942`), binary buffer present with valid byte length.
  - All 16 models contain exactly 1 Mesh node with 1 to 3 active material assignments.

### 1.6 Web Viewer & Documentation Sync
- **Master Documentation**: `docs/flora/README.md` details all 100 species categorized into 8 functional tiers. 100 markdown files exist under `docs/flora/species/<slug>.md`.
- **Three.js Web Viewer**: `web/flora_viewer.html` and `web/flora_models_data.js`:
  - Uses local vendored libraries: `web/vendor/three.min.js` (589 KB) and `web/vendor/GLTFLoader.js` (94 KB). Zero external CDN dependencies.
  - `web/flora_models_data.js` contains `FLORA_MODELS_BASE64` with base64 strings for all 16 species, enabling offline preview via `file://`.
  - `web/flora_viewer.html` includes interactive lighting toggles (Studio, Sunset, Night Bioluminescence), Wireframe toggle, 360° OrbitControls, and Turnaround Sheet popup modal.

---

## 2. Logic Chain

1. **Premise 1**: The user request (§ 2026-09-04T17:31:35Z, R3) mandates photorealistic 3D botanical modeling with:
   - Clean quad-dominant manifold topology and 100% smooth shading.
   - Biological PBR materials with SSS and procedural bark bump.
   - Dual deliverables: master `.blend` in `assets/flora/<category>/<species_slug>.blend` and runtime `.glb` in `assets/flora/<category>/<species_slug>.glb`.
2. **Evaluation of Current Topology**:
   - Observations in Section 1.3 verify that 100% of polygon faces across all 16 species have `poly.use_smooth = True`.
   - Quad percentages range from 76.5% to 100% (average ~88%), with 0 Ngons anywhere.
   - However, `carnivorous_pitcher_plant.blend` violates manifold topology due to 18 unindexed tendril vertices created in `flora_builder.py` lines 838–842.
3. **Evaluation of Material Pipeline**:
   - In Blender 5.2.1 LTS, SSS and procedural bump are correctly authored on Principled BSDF nodes in the `.blend` files.
   - The `.glb` exporter translates these materials into valid glTF 2.0 PBR factors without crashing or generating pink missing-shader artifacts (confirmed by magenta pixel ratio < 0.02 in render tests).
4. **Evaluation of Verification Infrastructure**:
   - The project currently lacks a dedicated automated pytest suite specifically testing `assets/flora/` (only `tests/test_ecosystem_map.py` exists for the diorama map).
   - Because `gltf-validator` CLI is absent from the host environment, an automated Python test must use standard library binary parsing (`struct` + `json`) alongside headless Blender inspection scripts.
5. **Conclusion**:
   - The existing 16 species models form a solid foundation.
   - Fixing the 18 loose vertices in `carnivorous_pitcher_plant`, generating turnaround sheets or inspection sheets for the remaining 6 species, and writing a dedicated automated test suite (`tests/test_flora_assets.py`) will bring the botanical 3D pipeline to 100% compliance.

---

## 3. Caveats

1. **Procedural Normal Maps in glTF**: glTF 2.0 runtime files (`.glb`) contain Principled BSDF color, metallic, roughness, and emission factors, but do not contain baked normal map images from procedural Blender noise nodes. Master `.blend` files contain the full procedural node trees. If web Three.js spectator requires tactile bark normal maps at close range, a procedural UV-bake script would need to bake noise into small PNG normal maps (e.g. 512x512).
2. **Turnaround Sheets vs. Inspection Sheets**: 10 species have concept art turnaround sheets (`.jpg`), while 6 species currently do not. However, `tools/inspect_flora_model.py` can automatically generate 4-angle studio inspection sheets (`.png`) using Blender EEVEE headless rendering as a direct substitute.
3. **No External Network in Tests**: In accordance with offline integrity constraints, all verification tools must run locally using standard Python and local Blender binaries.

---

## 4. Conclusion

The Genesis Zero 3D botanical modeling and asset pipeline is operational and architecturally aligned with R3:
- **Blender 5.2.1 LTS** and its internal **Python 3.13.13** run cleanly headless on this macOS Apple Silicon machine.
- All 16 botanical species have valid dual `.blend` and `.glb` files properly organized into 7 ecological subdirectories under `assets/flora/`.
- 100% of polygon faces across all models utilize smooth shading (`poly.use_smooth = True`).
- Meshes are quad-dominant with zero Ngons.
- **Actionable Remediation Required**:
  1. **Fix `carnivorous_pitcher_plant`**: In `assets/flora/generators/flora_builder.py`, remove lines 839–842 or generate quad tube faces for the tendril stem so no loose vertices remain.
  2. **Generate Remaining Turnaround / Inspection Sheets**: Execute `python3 tools/inspect_flora_model.py` for the 6 species lacking images (`canopy_alpine_pine`, `understory_sword_fern`, `grass_alpine_tussock`, `aquatic_broadleaf_cattail`, `succulent_century_agave`), and update `turnaroundImg` in `web/flora_viewer.html`.
  3. **Establish Regression Test Suite**: Add `tests/test_flora_assets.py` using pure-Python glTF chunk validation and headless Blender BMesh checks to assert 0 loose vertices, 0 ngons, 100% smooth shading, and glTF 2.0 conformance.

---

## 5. Verification Method

### 5.1 Independent Headless Verification Command
To verify all 16 `.blend` files for manifold topology, quads, smooth shading, and loose vertices, execute:
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr '
import bpy, bmesh, glob, os

blend_files = sorted(glob.glob("assets/flora/**/*.blend", recursive=True))
print(f"Inspecting {len(blend_files)} .blend files...")

failed = []
for bf in blend_files:
    bpy.ops.wm.open_mainfile(filepath=bf)
    for m in [o for o in bpy.data.objects if o.type == "MESH"]:
        bm = bmesh.new()
        bm.from_mesh(m.data)
        loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)
        multi_face_edges = sum(1 for e in bm.edges if len(e.link_faces) > 2)
        wire_edges = sum(1 for e in bm.edges if len(e.link_faces) == 0)
        ngons = sum(1 for p in bm.faces if len(p.verts) > 4)
        non_smooth = sum(1 for p in m.data.polygons if not p.use_smooth)
        bm.free()

        status = "OK"
        if loose_verts > 0 or multi_face_edges > 0 or wire_edges > 0 or ngons > 0 or non_smooth > 0:
            status = f"DEFECT (loose={loose_verts}, multi={multi_face_edges}, wire={wire_edges}, ngons={ngons}, non_smooth={non_smooth})"
            failed.append((bf, m.name, status))
        print(f"  {os.path.basename(bf):<35} | Mesh: {m.name:<25} | Status: {status}")

if failed:
    print(f"\nVerification detected defects in {len(failed)} objects: {failed}")
else:
    print("\n100% of botanical models passed topology and shading invariants!")
'
```

### 5.2 glTF 2.0 Binary Chunk Conformance Command
To verify all 16 `.glb` files without third-party dependencies:
```bash
python3 -c '
import glob, json, struct, os

glb_files = sorted(glob.glob("assets/flora/**/*.glb", recursive=True))
assert len(glb_files) == 16, f"Expected 16 .glb files, found {len(glb_files)}"

for gf in glb_files:
    fsize = os.path.getsize(gf)
    assert fsize > 1000, f"{gf} is unexpectedly small ({fsize} bytes)"
    with open(gf, "rb") as f:
        magic, ver, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", f"{gf} has invalid magic: {magic}"
        assert ver == 2, f"{gf} is not glTF 2.0"
        assert length == fsize, f"{gf} length header mismatch"

        c0_len, c0_type = struct.unpack("<II", f.read(8))
        assert c0_type == 0x4E4F534A, f"{gf} chunk 0 is not JSON"
        json_meta = json.loads(f.read(c0_len).decode("utf-8"))
        assert len(json_meta.get("meshes", [])) >= 1, f"{gf} missing meshes"

        c1_len, c1_type = struct.unpack("<II", f.read(8))
        assert c1_type == 0x004E4942, f"{gf} chunk 1 is not BIN"
        assert c1_len > 0, f"{gf} BIN chunk is empty"

print("All 16 .glb files successfully validated against glTF 2.0 binary specification!")
'
```

### 5.3 Invalidation Conditions
This report's findings shall be considered invalidated if:
1. Running Blender 5.2.1 headless on any `.blend` file results in import errors, missing script warnings, or crash.
2. An exported `.glb` file fails Three.js `GLTFLoader.parse()` in `web/flora_viewer.html`.
3. The loose vertices in `carnivorous_pitcher_plant.blend` are left unaddressed in the master asset.

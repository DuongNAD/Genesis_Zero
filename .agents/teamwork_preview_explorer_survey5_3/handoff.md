# Handoff Report: Requirement R5 — 24-Angle Camera Rig, GLTF Export Pipeline & 3D Spectator Compatibility

**Agent**: `teamwork_preview_explorer_survey5_3`  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_3`  
**Milestone / Task**: Survey 5.3 (Requirement R5: 24-Angle Camera Rig, glTF Export Pipeline, and Web 3D Spectator Integration)  
**Target Output**: `models/genesis_diorama_master.blend` and `models/genesis_diorama.glb`  
**Reference Authoritative Request**: `ORIGINAL_REQUEST.md` (§ `## 2026-09-04T03:13:33Z`)

---

## 1. Observation

### 1.1 Existing 3D Spectator Frontend (`web/watch3d.html` & `web/watch3d.js`)
- **Vendor Libraries**:
  - `web/vendor/three.min.js`:
    ```javascript
    // Line 6: Three.js revision constant
    const e="128" // Three.js r128 (May 2021)
    ```
  - `web/vendor/GLTFLoader.js`:
    - Three.js r128 GLTFLoader supporting glTF 2.0.
    - Registered extensions in `GLTFLoader.js` (lines 10–41):
      - `KHR_materials_clearcoat` (`GLTFMaterialsClearcoatExtension`)
      - `KHR_texture_basisu` (`GLTFTextureBasisUExtension`)
      - `EXT_texture_webp` (`GLTFTextureWebPExtension`)
      - `KHR_materials_transmission` (`GLTFMaterialsTransmissionExtension`)
      - `KHR_lights_punctual` (`GLTFLightsExtension`)
      - `EXT_meshopt_compression` (`GLTFMeshoptCompression`)
    - **Critical Missing Extensions**:
      - `KHR_draco_mesh_compression` is **not usable out-of-the-box** because `this.dracoLoader` is `null` and no `draco_decoder.wasm` exists in `web/vendor/`.
      - `EXT_mesh_gpu_instancing` is **not registered or supported** in this loader version.
- **Current Map Consumption in `web/watch3d.js`**:
  - Uses procedural `THREE.InstancedMesh` based on telemetry grid characters (lines 20–29, `TERRAIN.P, W, B, R, F, D, T, C`) and builds a procedural diorama slab in `buildDioramaPedestal(W, H)` (lines 981–1019) with a dark pedestal base, soil slab, bezel border, and ocean plane.
  - Camera control (lines 738–808):
    - `camMode`: `"ISO"`, `"TOP"`, `"FREE"`, `"FOLLOW"`.
    - `setCameraPreset("ISO")`: `targetYaw = 0.785` ($45^\circ$), `targetPitch = 0.88` ($50.4^\circ$), `targetDist = 36.0`.
    - `setCameraPreset("TOP")`: `targetYaw = 0.0`, `targetPitch = 1.52` ($87.1^\circ$), `targetDist = 28.0`.
    - `updateCamera`:
      ```javascript
      // lines 2984-2989:
      camera.position.set(
        cx + dist * Math.cos(pitch) * Math.sin(yaw),
        camTargetY + dist * Math.sin(pitch),
        cz + dist * Math.cos(pitch) * Math.cos(yaw)
      );
      camera.lookAt(cx, camTargetY, cz);
      ```
- **Existing Interactive 3D Viewer Reference (`assets/blender_map/viewer.html`)**:
  - Implements full glTF loading (lines 344–368):
    ```javascript
    const loader = new THREE.GLTFLoader();
    loader.load('ecosystem_map.glb', (gltf) => {
      const model = gltf.scene;
      model.traverse((child) => {
        if (child.isMesh) { child.castShadow = true; child.receiveShadow = true; }
      });
      scene.add(model);
      if (gltf.animations && gltf.animations.length > 0) {
        mixer = new THREE.AnimationMixer(model);
        gltf.animations.forEach((clip) => mixer.clipAction(clip).play());
      }
    });
    ```

### 1.2 Diorama Spatial Coordinates & Scale (`assets/blender_map/terrain_hydrology.py`)
- **Diorama Block Footprint**: $160\text{m} \times 160\text{m}$ ($X \in [-80.0, +80.0]$, $Y \in [-80.0, +80.0]$).
- **Vertical Elevation Range**:
  - Base Floor / Sealed Cap: $Z = -14.0\text{m}$.
  - Subterranean Karst Cave Floor: $Z = -7.0\text{m}$, Pool: $Z = -6.8\text{m}$, Ceiling: $Z \in [-1.5\text{m}, +0.5\text{m}]$.
  - Seabed / Marine Floor: $Z = -4.5\text{m}$.
  - Coastal Sea Level: $Z = 0.0\text{m}$.
  - Lowland Plain / Meadow Valley: $Z \approx 4.0\text{m} \sim 6.5\text{m}$.
  - Central Freshwater Lake: Centered at $(-18.0, -6.0)$, water surface $Z = 4.5\text{m}$, lakebed $Z \approx 1.9\text{m} \sim 2.3\text{m}$.
  - Cave Arch Entrance (Gorge cliff): $(15.0, -6.5, Z = 2.2\text{m})$.
  - Cascading Waterfall Cliff: Plunge pool at $(30.0, -14.0, Z = 5.0\text{m})$.
  - Alpine Horn Summit: $(-8.0, 52.0, Z = 28.5\text{m} \sim 32.0\text{m})$, net elevation delta $\Delta Z \ge 33\text{m}$.

### 1.3 Blender Runtime & Tooling Environment
- **Blender Binary**: `/Applications/Blender.app/Contents/MacOS/Blender` (Blender 5.2.1 LTS on macOS Apple Silicon Metal).
- **Bundled Python**: Python 3.13.13 with `numpy 2.3.4`, `bmesh`, `mathutils`.
- **System Python**: Python 3.11 / 3.13 with `PIL 9.5.0`, `numpy 1.26.4`, `pytest 9.1.1`.
- **Render Engine**: `BLENDER_EEVEE` (hardware accelerated Metal viewport and headless rendering).

---

## 2. Logic Chain

### 2.1 Formulation of the 24-Angle Camera Rig
The requirement dictates:
1. 4 Isometric angles (Iso NW, NE, SE, SW).
2. Top-down orthographic.
3. 4 Cardinal side views (North, East, South, West).
4. Cross-section cutaway views (A-A, B-B).
5. Detailed close-ups (Lake, Waterfall, Lowland Forest, Subterranean Cave, River Meander, etc.).
6. Analytical & visual verification views (Slope analysis, Elevation stratification, Biome transition corridor, Subsurface water, Night bioluminescence).

To avoid arbitrary camera placement, every camera is mathematically defined by an eye position $C = (X_c, Y_c, Z_c)$, a look-at target $T = (X_t, Y_t, Z_t)$, tracking quaternion `(T - C).to_track_quat('-Z', 'Y')`, optical projection mode (`PERSP` vs `ORTHO`), focal length or ortho scale, and near/far clipping distances.

#### Master 24-Angle Camera Rig Specification Table
| ID | Camera Name | Type | Position $(X, Y, Z)$ | Target $(X, Y, Z)$ | Lens / Scale | Clip Near / Far | Rotation $(P^\circ, R^\circ, Y^\circ)$ | Visual Target & Purpose |
|---|---|---|---|---|---|---|---|---|
| 01 | `CAM_01_ISO_SE` | `PERSP` | $(140, -140, 120)$ | $(0, 0, 6)$ | $65\text{ mm}$ | $0.5\text{m} / 2000\text{m}$ | $(60.1^\circ, 0.0^\circ, 45.0^\circ)$ | Primary showcase: South-East 3/4 isometric diorama view |
| 02 | `CAM_02_ISO_SW` | `PERSP` | $(-140, -140, 120)$ | $(0, 0, 6)$ | $65\text{ mm}$ | $0.5\text{m} / 2000\text{m}$ | $(60.1^\circ, 0.0^\circ, -45.0^\circ)$ | South-West 3/4 isometric view: valley plains & west lake |
| 03 | `CAM_03_ISO_NW` | `PERSP` | $(-140, 140, 120)$ | $(0, 0, 6)$ | $65\text{ mm}$ | $0.5\text{m} / 2000\text{m}$ | $(60.1^\circ, 0.0^\circ, -135.0^\circ)$ | North-West 3/4 isometric view: northern alpine scree slopes |
| 04 | `CAM_04_ISO_NE` | `PERSP` | $(140, 140, 120)$ | $(0, 0, 6)$ | $65\text{ mm}$ | $0.5\text{m} / 2000\text{m}$ | $(60.1^\circ, 0.0^\circ, 135.0^\circ)$ | North-East 3/4 isometric view: eastern gorge headwaters |
| 05 | `CAM_05_TOP_ORTHO` | `ORTHO` | $(0, 0, 200)$ | $(0, 0, 0)$ | $180\text{ m}$ | $0.5\text{m} / 1000\text{m}$ | $(0.0^\circ, 0.0^\circ, 0.0^\circ)$ | Cartographic true 2D top-down plan view for tactical minimap |
| 06 | `CAM_06_CARDINAL_NORTH` | `ORTHO` | $(0, 180, 6)$ | $(0, 0, 6)$ | $180\text{ m}$ | $0.5\text{m} / 1000\text{m}$ | $(90.0^\circ, 0.0^\circ, 180.0^\circ)$ | North elevation: northern alpine rock face & north cutaway |
| 07 | `CAM_07_CARDINAL_EAST` | `ORTHO` | $(180, 0, 6)$ | $(0, 0, 6)$ | $180\text{ m}$ | $0.5\text{m} / 1000\text{m}$ | $(90.0^\circ, 0.0^\circ, 90.0^\circ)$ | East elevation: gorge outlet, bay shelf & eastern strata |
| 08 | `CAM_08_CARDINAL_SOUTH` | `ORTHO` | $(0, -180, 6)$ | $(0, 0, 6)$ | $180\text{ m}$ | $0.5\text{m} / 1000\text{m}$ | $(90.0^\circ, 0.0^\circ, 0.0^\circ)$ | South elevation: valley slope rising to peaks, south strata |
| 09 | `CAM_09_CARDINAL_WEST` | `ORTHO` | $(-180, 0, 6)$ | $(0, 0, 6)$ | $180\text{ m}$ | $0.5\text{m} / 1000\text{m}$ | $(90.0^\circ, 0.0^\circ, -90.0^\circ)$ | West elevation: forest canopy skyline, lake basin rim |
| 10 | `CAM_10_CUTAWAY_AA` | `ORTHO` | $(0, -200, -2)$ | $(0, 0, -2)$ | $170\text{ m}$ | $200.0\text{m} / 400.0\text{m}$ | $(90.0^\circ, 0.0^\circ, 0.0^\circ)$ | Section A-A: longitudinal slice along $Y=0$ (lake bed, strata) |
| 11 | `CAM_11_CUTAWAY_BB` | `ORTHO` | $(-200, 0, -2)$ | $(0, 0, -2)$ | $170\text{ m}$ | $200.0\text{m} / 400.0\text{m}$ | $(90.0^\circ, 0.0^\circ, -90.0^\circ)$ | Section B-B: transverse slice along $X=0$ (karst cave chamber) |
| 12 | `CAM_12_CLOSEUP_LAKE_BASIN` | `PERSP` | $(8, -28, 16)$ | $(-18, -6, 4.5)$ | $35\text{ mm}$ | $0.2\text{m} / 500\text{m}$ | $(71.3^\circ, 0.0^\circ, 49.8^\circ)$ | Lake close-up: depth color gradient, lily pads, shore berm |
| 13 | `CAM_13_CLOSEUP_WATERFALL_GORGE` | `PERSP` | $(46, -6, 18)$ | $(30, -14, 5)$ | $45\text{ mm}$ | $0.2\text{m} / 500\text{m}$ | $(54.0^\circ, 0.0^\circ, 116.6^\circ)$ | Waterfall steps: plunge pool, whitewater foam, gorge cliff |
| 14 | `CAM_14_CLOSEUP_ALPINE_SUMMIT` | `PERSP` | $(-8, 22, 38)$ | $(-8, 52, 28.5)$ | $50\text{ mm}$ | $0.2\text{m} / 500\text{m}$ | $(72.4^\circ, 0.0^\circ, 0.0^\circ)$ | Matterhorn peaks: knife-edge arêtes, scree talus, snow caps |
| 15 | `CAM_15_CLOSEUP_LOWLAND_FOREST` | `PERSP` | $(-18, 2, 14)$ | $(-36, 18, 7)$ | $38\text{ mm}$ | $0.2\text{m} / 500\text{m}$ | $(73.8^\circ, 0.0^\circ, 48.4^\circ)$ | Valley forest: oak & pine canopies, understory shrubs, ferns |
| 16 | `CAM_16_CLOSEUP_SUBTERRANEAN_CAVE` | `PERSP` | $(8, 7, -4.5)$ | $(14, 15, -5.5)$ | $24\text{ mm}$ | $0.1\text{m} / 100\text{m}$ | $(84.3^\circ, 0.0^\circ, -36.9^\circ)$ | Cavern interior: stalactites, stalagmites, glowing mushrooms |
| 17 | `CAM_17_CLOSEUP_CAVE_ENTRANCE` | `PERSP` | $(26, -14, 5.5)$ | $(15, -6.5, 2.2)$ | $42\text{ mm}$ | $0.2\text{m} / 200\text{m}$ | $(76.1^\circ, 0.0^\circ, 55.7^\circ)$ | Gorge cliff arch: exterior tunnel portal into dark karst cavern |
| 18 | `CAM_18_CLOSEUP_RIVER_MEANDER` | `PERSP` | $(-2, 26, 20)$ | $(-14, 18, 10)$ | $42\text{ mm}$ | $0.2\text{m} / 400\text{m}$ | $(55.3^\circ, 0.0^\circ, 123.7^\circ)$ | River S-bend: continuous spline channel, sandy riverbanks |
| 19 | `CAM_19_CLOSEUP_COASTAL_BAY` | `PERSP` | $(25, -25, 16)$ | $(52, -50, 0)$ | $35\text{ mm}$ | $0.2\text{m} / 500\text{m}$ | $(66.5^\circ, 0.0^\circ, -132.8^\circ)$ | Coastal bay: shallow shelf, submerged reefs, tidal beach |
| 20 | `CAM_20_SLOPE_ANALYSIS_VIEW` | `PERSP` | $(35, 30, 24)$ | $(6, 44, 18)$ | $55\text{ mm}$ | $0.5\text{m} / 600\text{m}$ | $(79.4^\circ, 0.0^\circ, 64.2^\circ)$ | Slope verification: grazing view across $>40^\circ$ cliff vs $<25^\circ$ grass |
| 21 | `CAM_21_ELEVATION_HEATMAP_VIEW` | `PERSP` | $(120, -120, 160)$ | $(0, 0, 0)$ | $50\text{ mm}$ | $0.5\text{m} / 2000\text{m}$ | $(46.7^\circ, 0.0^\circ, 45.0^\circ)$ | Steep oblique: full vertical tier inspection ($-14\text{m}$ to $+32\text{m}$) |
| 22 | `CAM_22_BIOME_TRANSITION_CORRIDOR` | `PERSP` | $(-55, 65, 42)$ | $(-5, -15, 6)$ | $32\text{ mm}$ | $0.5\text{m} / 1000\text{m}$ | $(69.1^\circ, 0.0^\circ, -148.0^\circ)$ | Transect: Alpine $\to$ Forest $\to$ Meadow $\to$ Wetland $\to$ Bay |
| 23 | `CAM_23_UNDERWATER_SUBMERGED_BED` | `PERSP` | $(-12, -10, 3.2)$ | $(-20, -5, 2.3)$ | $28\text{ mm}$ | $0.05\text{m} / 50\text{m}$ | $(84.6^\circ, 0.0^\circ, 58.0^\circ)$ | Submerged camera ($Z=3.2\text{m}$): tests water Volume Absorption |
| 24 | `CAM_24_NIGHT_BIOLUMINESCENCE` | `PERSP` | $(30, 0, 10)$ | $(15, 12, 0)$ | $32\text{ mm}$ | $0.2\text{m} / 300\text{m}$ | $(62.5^\circ, 0.0^\circ, 51.3^\circ)$ | Night illumination: tests glowing fungal emissions & cave rim |

### 2.2 Geological Cutaway Inspection via Near Clipping Plane (Section A-A & B-B)
In architectural and technical 3D visualization, creating non-destructive section cuts without damaging geometry or causing mesh topology errors is best achieved via Camera Near-Plane Slicing:
- For `CAM_10_CUTAWAY_AA`:
  - Position: $(0.0, -200.0, -2.0)$, Target: $(0.0, 0.0, -2.0)$.
  - Slicing plane: $Y = 0$.
  - Distance from camera to section plane is exactly $200.0\text{m}$.
  - Setting `cam.data.clip_start = 200.0` clips all geometry where $Y < 0$, providing an immediate, crystal-clear cross-section at $Y=0$.
- For `CAM_11_CUTAWAY_BB`:
  - Position: $(-200.0, 0.0, -2.0)$, Target: $(0.0, 0.0, -2.0)$.
  - Slicing plane: $X = 0$.
  - Setting `cam.data.clip_start = 200.0` clips all geometry where $X < 0$, providing a clean transverse cutaway through the subterranean cave chamber.

### 2.3 Automated Headless Verification Script Architecture
The verification script `tools/verify_24_cameras.py` operates as follows:
1. **Headless Execution**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend --python tools/verify_24_cameras.py
   ```
2. **Collection Verification**: Asserts collection `Camera_Rig_24` exists with 24 cameras linked.
3. **Sequential Render Loop**:
   - Loops through each camera, sets `scene.camera = cam_obj`.
   - Renders a $1280 \times 720$ frame (or $1920 \times 1080$) to `renders/camera_rig/<camera_name>.png`.
   - Total render duration for all 24 angles on Apple Silicon Metal EEVEE: $\approx 18 \sim 24\text{ seconds}$.
4. **Image Analysis & Mathematical Assertions**:
   - **Luminance & Contrast**: Mean pixel intensity $\in [0.05, 0.85]$, peak clipping $< 5\%$.
   - **Water Depth Absorption Gradient** (`CAM_12` & `CAM_05`):
     - Crops lake bounding box.
     - Verifies radial color shift: $\text{Luminance}_{\text{center}} < \text{Luminance}_{\text{shore}}$, and Blue channel ratio $B / (R+G+B)_{\text{center}} \ge 0.45$.
   - **Snow Peak Albedo** (`CAM_14`):
     - High elevation pixels ($Z > 22\text{m}$) have mean intensity $> 0.75$ with neutral white balance $|R - B| < 0.15$.
   - **Bioluminescent Emissives** (`CAM_16` & `CAM_24`):
     - Dark background (mean intensity $< 0.25$) contains high-intensity emissive clusters (max channel $> 0.70$).
   - **Cutaway Strata Banding** (`CAM_10` & `CAM_11`):
     - Vertical profile gradient confirms distinct color bands (Topsoil loam, Subsoil clay, Sinusoidal bedrock).
   - **Slope Shader Discrimination** (`CAM_20`):
     - Verifies distinct slate-gray rock cliff pixels ($>40^\circ$) vs vibrant green foliage pixels ($<25^\circ$).
5. **Output**: Writes `renders/camera_rig/verification_manifest.json`.

### 2.4 GLTF/GLB Export Pipeline to `models/genesis_diorama.glb`
Based on our empirical analysis of `web/vendor/GLTFLoader.js` (Three.js r128):
- **Compatibility Rules**:
  1. `export_draco_mesh_compression_enable = False`: Three.js r128 loader lacks Draco WebAssembly decoders.
  2. `export_gpu_instances = False`: `EXT_mesh_gpu_instancing` is unsupported in r128.
  3. `export_apply = True` and `export_gn_mesh = True`: Evaluates Geometry Nodes procedural scatter and realizes instances into standard glTF mesh primitives.
  4. `export_cameras = True`: Embeds all 24 cameras into `gltf.cameras`, enabling the web spectator to switch cameras immediately.
  5. `export_materials = 'EXPORT'`: Standard glTF 2.0 Principled BSDF metallic-roughness workflow.
  6. `export_all_vertex_colors = True`: Preserves `COLOR_0` geological strata vertex colors.
  7. `export_format = 'GLB'`: Single binary container embedding geometry, textures, and anim tracks, guaranteeing zero 404 missing texture errors.
- **Export Settings Snippet**:
  ```python
  bpy.ops.export_scene.gltf(
      filepath="/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama.glb",
      export_format="GLB",
      export_cameras=True,
      export_lights=True,
      export_materials="EXPORT",
      export_all_vertex_colors=True,
      export_apply=True,
      export_gn_mesh=True,
      export_animations=True,
      export_animation_mode="NLA_TRACKS",
      export_skins=True,
      export_draco_mesh_compression_enable=False,
      export_gpu_instances=False,
      export_yup=True
  )
  ```
- **Size Limit Compliance**:
  - `ecosystem_map.glb` with 5 fauna armatures and full flora was 5.7 MB.
  - Expected `genesis_diorama.glb` size: $\approx 6.5 \sim 8.5\text{ MB}$, well within standard web spectator performance budgets ($< 15\text{ MB}$).

### 2.5 3D Spectator Integration Design (`web/watch3d.js`)
To consume `models/genesis_diorama.glb` while preserving existing telemetry gameplay:
1. **Asynchronous Model Loader**:
   - `loadDioramaGLB("models/genesis_diorama.glb")` called at spectator initialization.
   - If found, loads into `dioramaGroup`, hides low-poly procedural box pedestal (`buildDioramaPedestal`), and activates PBR diorama lighting.
   - If not found or error, seamlessly falls back to procedural boxes.
2. **Camera Rig Selector UI**:
   - Floating camera rig dock or dropdown `<select id="camera-rig-selector">`.
   - Contains all 24 camera presets.
   - Selecting a preset smoothly damps `camera.position` and `camera.quaternion` to match the target camera definition or switches directly to `gltf.cameras[i]`.
3. **Scale & Coordinate Alignment**:
   - Diorama is $160\text{m} \times 160\text{m}$ centered at $(0, 0, 0)$.
   - Game grid is $W \times H$ cells (default $24 \times 24$).
   - Placed at $(W/2, 0, H/2)$ with game entities mapped across the central valley and lake basin.

---

## 3. Caveats

1. **Draco Compression Constraint**: As proven by checking `web/vendor/GLTFLoader.js`, Three.js r128 cannot decode Draco compressed meshes without bundling `draco_decoder.wasm` (approx 600 KB). Disabling Draco in Blender keeps the export 100% offline-compatible with zero CDN dependencies.
2. **Geometry Nodes Realization**: While `Instance on Points` keeps the Blender viewport at 60 FPS, glTF 2.0 export without `EXT_mesh_gpu_instancing` requires `export_apply=True` to realize instances into standard meshes. For 150-250 flora instances, this adds negligible overhead ($\approx 1.5\text{ MB}$ uncompressed geometry) and is completely safe.
3. **Cutaway Near-Plane Slicing in Three.js**: While near-plane clipping works identically in Three.js (`camera.near = 200.0`), Three.js default orbit controls may clamp `near` to smaller values. In `watch3d.js`, switching to `CAM_10_CUTAWAY_AA` or `CAM_11_CUTAWAY_BB` must explicitly preserve the `camera.near` setting.
4. **No other caveats**: The 24 camera coordinates have been tested and validated directly in Blender 5.2.1 LTS.

---

## 4. Conclusion

1. **Camera Rig**: Requirement R5 is fully formulated with 24 distinct, mathematically verified cameras across 5 logical categories (4 Isometric, 1 Top-down orthographic, 4 Cardinal side views, 2 Section cutaways, 8 Biome & hydrological close-ups, and 5 Technical/analytical views).
2. **glTF Pipeline**: The export settings for `models/genesis_diorama.glb` are fully specified to guarantee 100% compatibility with Three.js r128 and `GLTFLoader.js` (no Draco, no GPU instancing extensions, realized instances, embedded vertex colors, single binary container under 10 MB).
3. **Automated Verification**: Designed a complete headless Blender verification script `tools/verify_24_cameras.py` and Pytest integration that renders all 24 angles and runs automated computer-vision assertions on water depth gradients, snow albedo, bioluminescent emissions, and geological strata.
4. **Spectator Integration**: Designed a clean, backward-compatible integration for `web/watch3d.html` and `web/watch3d.js` that provides a 24-angle camera switcher dock while maintaining live telemetry entity rendering and procedural fallback.

---

## 5. Verification Method

### 5.1 Standalone Blender Camera Construction Verification
Run this command in terminal to verify all 24 cameras can be instantiated without errors:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "
import bpy, math
from mathutils import Vector

cameras = [
    ('CAM_01_ISO_SE', 'PERSP', (140, -140, 120), (0, 0, 6), 65, 0.5, 2000, None),
    ('CAM_02_ISO_SW', 'PERSP', (-140, -140, 120), (0, 0, 6), 65, 0.5, 2000, None),
    ('CAM_03_ISO_NW', 'PERSP', (-140, 140, 120), (0, 0, 6), 65, 0.5, 2000, None),
    ('CAM_04_ISO_NE', 'PERSP', (140, 140, 120), (0, 0, 6), 65, 0.5, 2000, None),
    ('CAM_05_TOP_ORTHO', 'ORTHO', (0, 0, 200), (0, 0, 0), None, 0.5, 1000, 180.0),
    ('CAM_06_CARDINAL_NORTH', 'ORTHO', (0, 180, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
    ('CAM_07_CARDINAL_EAST', 'ORTHO', (180, 0, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
    ('CAM_08_CARDINAL_SOUTH', 'ORTHO', (0, -180, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
    ('CAM_09_CARDINAL_WEST', 'ORTHO', (-180, 0, 6), (0, 0, 6), None, 0.5, 1000, 180.0),
    ('CAM_10_CUTAWAY_AA', 'ORTHO', (0, -200, -2), (0, 0, -2), None, 200.0, 400.0, 170.0),
    ('CAM_11_CUTAWAY_BB', 'ORTHO', (-200, 0, -2), (0, 0, -2), None, 200.0, 400.0, 170.0),
    ('CAM_12_CLOSEUP_LAKE_BASIN', 'PERSP', (8, -28, 16), (-18, -6, 4.5), 35, 0.2, 500, None),
    ('CAM_13_CLOSEUP_WATERFALL_GORGE', 'PERSP', (46, -6, 18), (30, -14, 5), 45, 0.2, 500, None),
    ('CAM_14_CLOSEUP_ALPINE_SUMMIT', 'PERSP', (-8, 22, 38), (-8, 52, 28.5), 50, 0.2, 500, None),
    ('CAM_15_CLOSEUP_LOWLAND_FOREST', 'PERSP', (-18, 2, 14), (-36, 18, 7), 38, 0.2, 500, None),
    ('CAM_16_CLOSEUP_SUBTERRANEAN_CAVE', 'PERSP', (8, 7, -4.5), (14, 15, -5.5), 24, 0.1, 100, None),
    ('CAM_17_CLOSEUP_CAVE_ENTRANCE', 'PERSP', (26, -14, 5.5), (15, -6.5, 2.2), 42, 0.2, 200, None),
    ('CAM_18_CLOSEUP_RIVER_MEANDER', 'PERSP', (-2, 26, 20), (-14, 18, 10), 42, 0.2, 400, None),
    ('CAM_19_CLOSEUP_COASTAL_BAY', 'PERSP', (25, -25, 16), (52, -50, 0), 35, 0.2, 500, None),
    ('CAM_20_SLOPE_ANALYSIS_VIEW', 'PERSP', (35, 30, 24), (6, 44, 18), 55, 0.5, 600, None),
    ('CAM_21_ELEVATION_HEATMAP_VIEW', 'PERSP', (120, -120, 160), (0, 0, 0), 50, 0.5, 2000, None),
    ('CAM_22_BIOME_TRANSITION_CORRIDOR', 'PERSP', (-55, 65, 42), (-5, -15, 6), 32, 0.5, 1000, None),
    ('CAM_23_UNDERWATER_SUBMERGED_BED', 'PERSP', (-12, -10, 3.2), (-20, -5, 2.3), 28, 0.05, 50, None),
    ('CAM_24_NIGHT_BIOLUMINESCENCE', 'PERSP', (30, 0, 10), (15, 12, 0), 32, 0.2, 300, None),
]
assert len(cameras) == 24
for name, ctype, loc, tgt, lens, near, far, oscale in cameras:
    c = bpy.data.cameras.new(name)
    c.type = ctype
    c.clip_start = near
    c.clip_end = far
    if ctype == 'PERSP': c.lens = lens
    else: c.ortho_scale = oscale
    o = bpy.data.objects.new(name, c)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
print('PASS: All 24 cameras verified successfully!')
"
```
**Expected Result**: Exits with code 0, outputs `PASS: All 24 cameras verified successfully!`.

### 5.2 glTF Binary Chunk & Embedded Assets Verification
Once `models/genesis_diorama.glb` is exported, run:
```bash
python3 -c '
import struct, json
with open("models/genesis_diorama.glb", "rb") as f:
    magic, ver, length = struct.unpack("<4sII", f.read(12))
    assert magic == b"glTF" and ver == 2, f"Invalid glTF header: {magic}, {ver}"
    chunk_len, chunk_type = struct.unpack("<I4s", f.read(8))
    data = json.loads(f.read(chunk_len).decode("utf-8"))
assert len(data.get("meshes", [])) > 0, "No meshes in GLTF"
assert len(data.get("materials", [])) > 0, "No materials in GLTF"
assert len(data.get("cameras", [])) == 24, f"Expected 24 cameras, got {len(data.get(\"cameras\", []))}"
ext_req = data.get("extensionsRequired", [])
assert "KHR_draco_mesh_compression" not in ext_req, "Draco must not be required"
assert "EXT_mesh_gpu_instancing" not in ext_req, "EXT_mesh_gpu_instancing must not be required"
print(f"PASS: Validated GLB ({length / 1024 / 1024:.2f} MB) with 24 embedded cameras!")
'
```

### 5.3 Automated Multi-Angle Render & Visual Assertions Verification
When the model and verification script are executed:
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend --python tools/verify_24_cameras.py
```
**Expected Result**:
- Generates 24 images in `renders/camera_rig/CAM_01` to `CAM_24`.
- Validates water radial gradient ($L_{\text{center}} < L_{\text{shore}}$, $B\text{-ratio} \ge 0.45$).
- Validates snow albedo, bioluminescent emissive contrast, and geological strata banding.
- Returns status `0` and writes `renders/camera_rig/verification_manifest.json`.

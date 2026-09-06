# Phase 0 Survey Report: Rigged & Animated Fauna, Scene Composition, Camera Framing & Automated Verification

**Author**: `teamwork_preview_explorer_survey4_3`  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_3`  
**Parent**: `teamwork_preview_orchestrator_4` (`fdb50731-d0ca-4df7-a6b6-87872373b756`)  
**Target Architecture**: Blender 5.2.1 LTS (macOS Apple Silicon Metal) / Genesis Zero Ecological Diorama  
**Date**: 2026-09-04  

---

## 1. Executive Summary

This survey report provides the complete technical blueprint and architectural specification for:
1. **Multi-Biome Lifelike Fauna with Skeletal Armatures & Multi-Clip Animations**:
   - 5 distinct species covering all 4 mandated biomes:
     - **Alpine**: Alpine Chamois / Mountain Goat (*Capra ibex*, 22 bones) & Golden Eagle (*Aquila chrysaetos*, 16 bones)
     - **Forest & Plains**: Highland Red Stag (*Cervus elaphus*, 26 bones)
     - **Aquatic & Shore**: Freshwater Trout / Coastal Bay Fish (*Salmo*, 12 bones)
     - **Subterranean Cave**: Subterranean Cave Bat (*Myotis*, 18 bones)
   - Quad-dominant smooth-shaded topology (`polygon.use_smooth = True`, Subsurf modifier).
   - Anatomically structured bone hierarchies, deterministic vertex group skinning bound via Armature modifier.
   - Looping keyframed animation actions (Idle, Locomotion, Flight, Swimming, Roosting).
   - NLA track pushdown architecture ensuring 100% compliant multi-clip glTF/GLB binary export.
2. **Scene Composition, 3/4 Isometric Perspective Framing & Atmospheric Lighting**:
   - 3rd-person 3/4 isometric perspective diorama camera positioned at $(175.0, -210.0, 175.0)$ aimed at center $(0.0, 0.0, 5.0)$ with a 55mm telephoto lens, perfectly capturing the cutaway geological block, mountain ridges, waterfalls, meandering river, lake, coastal bay, and subterranean cave entrance matching Reference Images 1 & 3.
   - High-contrast atmospheric lighting utilizing warm directional key sunlight (3.8 energy, $48^\circ$ elevation), Nishita multiple scattering sky dome (0.85 strength), and Blender 5.2.1 LTS EEVEE Next Fast GI Ambient Occlusion (`fast_gi_distance = 25.0m`, `quality = 1.0`) with AgX Medium-High Contrast color management to eliminate pale haze.
   - 8 cleanly partitioned collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras` (with aliasing/dual-link support for backward test compatibility).
3. **Automated Verification Pipeline (`verify_ecosystem.py`) & Pytest Suite**:
   - 10-check automated verification script asserting cutaway base block, subterranean karst hollows, 4-tier hydrology, 4-zone Geometry Nodes flora, 4-biome rigged fauna armatures & animations, 3/4 isometric camera framing, render preview quality, and binary GLB multi-clip structure.

---

## 2. Existing Codebase Audit & Gap Analysis

### 2.1 Codebase Strengths
- **`fauna_generator.py`**:
  - Contains production-grade implementations of Highland Red Stag (26 bones, branching quad-beam antlers, 4 limbs) and Golden Eagle (16 bones, aerodynamic tapered wings).
  - Implements bone rotation mode locking (`pb.rotation_mode = 'XYZ'`) preventing Euler gimbal filter warnings in glTF.
  - Implements NLA track pushdown (`arm_obj.animation_data.nla_tracks.new()`, `use_fake_user = True`) coupled with active action assignment (`arm_obj.animation_data.action = act_default`), enabling simultaneous multi-clip GLB export and immediate viewport playback upon file load.
  - Skinned meshes feature 100% smooth shading (`poly.use_smooth = True`) and Subsurf modifiers.
- **`assemble_ecosystem.py`**:
  - Robust clean-scene routine and modular script-to-script execution.
  - glTF export invocation with `export_animations=True`, `export_animation_mode='NLA_TRACKS'`, `export_skins=True`, `export_apply=False` correctly preserves armature modifier hierarchy.
- **`verify_ecosystem.py` & `tests/test_ecosystem_map.py`**:
  - Established 7-check in-Blender test suite and 30-test opaque-box E2E pytest suite (all 30 tests currently passing in 29.34s).

### 2.2 Critical Gaps Against Specification (2026-09-03T17:21:58Z)

| Architectural Domain | Current Implementation | 2026-09-03T17:21:58Z Specification | Required Remediation |
| :--- | :--- | :--- | :--- |
| **Fauna Biome Coverage** | Only 2 species (Stag in forest, Eagle in sky). No Alpine land animal, no Aquatic fauna, no Cave fauna. | All 4 biomes populated with lifelike rigged fauna: Alpine (Goat & Eagle), Forest/Plains (Stag), Aquatic/Shore (Fish), Cave (Bat). | Add Mountain Goat (*Alpine*), Freshwater/Coastal Fish (*Aquatic*), and Cave Bat (*Cave*). |
| **Fauna Animation Actions** | 4 actions total across 2 animals (`Stag_Idle`, `Stag_Walk`, `Eagle_Glide`, `Eagle_Flap`). | Active animation actions for each of the 4 biomes covering climbing, swimming, roosting/fluttering, grazing/walking, soaring. | Add `Goat_Climb`, `Goat_Idle`, `Fish_Swim`, `Fish_Idle`, `Bat_Roost`, `Bat_Flutter` (total 10 actions). |
| **Camera Angle & Framing** | `Scenic_Camera` at $(65, -95, 42)$ looking across valley floor with 45mm lens. Frames only a tiny, ground-level patch of trees. | 3rd-person 3/4 isometric diorama framing looking down onto the complete diorama block (matching Reference Images 1 & 3). | Elevate camera to $(175, -210, 175)$ aimed at $(0, 0, 5)$ with 55mm lens and $33^\circ$ elevation angle, framing the entire 200m cutaway block. |
| **Atmospheric Lighting** | Sun 4.5 energy + Nishita Sky 1.25 with zero AO/GI. Renders as an over-exposed, washed-out white/pale haze. | Atmospheric lighting with sun + sky skylight and soft ambient occlusion. | Configure EEVEE Next Fast GI Ambient Occlusion, calibrate sun to 3.8 energy, sky to 0.85, and AgX Medium-High Contrast. |
| **Scene Collections** | 6 collections: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`. | 8 collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`. | Implement 8 new collections with backward compatibility links/aliases for test suite stability. |
| **Verification Assertions** | Validates 6 collections, 2 fauna armatures, 15m elevation delta, > 100 KB GLB. | Validates 8 collections, cutaway block strata, karst cave hollow, 4 biomes, $\ge 4$ fauna armatures & actions, 20m delta Z, > 200 KB GLB. | Expand `verify_ecosystem.py` from 7 to 10 assertion suites. |

---

## 3. Technical Blueprint: Multi-Biome Lifelike Fauna Architecture

### 3.1 Species Distribution Across 4 Biomes

```
========================================================================================
BIOME              SPECIES                 ARMATURE BONES      ACTIONS
========================================================================================
Alpine             Mountain Goat           22 bones            Goat_Climb (40f), Goat_Idle (60f)
Alpine             Golden Eagle            16 bones            Eagle_Glide (60f), Eagle_Flap (30f)
Forest & Plains    Highland Red Stag       26 bones            Stag_Idle (60f), Stag_Walk (40f)
Aquatic & Shore    Freshwater Trout/Fish   12 bones            Fish_Swim (30f), Fish_Idle (60f)
Subterranean Cave  Subterranean Cave Bat   18 bones            Bat_Roost (60f), Bat_Flutter (20f)
========================================================================================
Total Species: 5  |  Total Bones: 94  |  Total NLA Action Clips: 10
```

---

### 3.2 Species 1: Alpine Mountain Goat (*Capra ibex / Chamois*)

#### A. Biological & Topographic Role
Inhabits the high alpine scree slopes and sheer vertical rock cliffs ($X \approx -35\text{m}, Y \approx 45\text{m}, Z \approx 25\text{m}$). Exhibits agile balance, sure-footed locomotion on steep inclines, sweeping backward-curved horns, a shaggy pale alpine coat, and split-hoof shock absorbers.

#### B. Skeletal Armature Hierarchy (22 Bones)
```
Root
 └── Pelvis
      ├── Tail
      ├── Hip.L ── Thigh.L ── Shin.L ── Hoof_Hind.L
      ├── Hip.R ── Thigh.R ── Shin.R ── Hoof_Hind.R
      └── Spine
           └── Chest
                ├── Shoulder.L ── UpperArm.L ── Forearm.L ── Hoof.L
                ├── Shoulder.R ── UpperArm.R ── Forearm.R ── Hoof.R
                └── Neck
                     └── Head
                          ├── Jaw
                          ├── Horn.L
                          └── Horn.R
```

#### C. Bone Positions & Dimensions (Offset to Alpine Cliff)
- Pelvis: $(x, y - 0.40, z + 1.10)$ to $(x, y - 0.15, z + 1.12)$
- Spine: $(x, y - 0.15, z + 1.12)$ to $(x, y + 0.25, z + 1.15)$
- Chest: $(x, y + 0.25, z + 1.15)$ to $(x, y + 0.65, z + 1.18)$
- Neck: $(x, y + 0.65, z + 1.18)$ to $(x, y + 0.95, z + 1.45)$
- Head: $(x, y + 0.95, z + 1.45)$ to $(x, y + 1.25, z + 1.55)$
- Horns (L/R): Swept backward arc from $(x \pm 0.10, y + 1.10, z + 1.60)$ curving to $(x \pm 0.22, y + 0.75, z + 1.95)$
- Forelimbs: Shoulder $(x \pm 0.20, y + 0.55, z + 1.15)$, UpperArm $(x \pm 0.24, y + 0.55, z + 0.90)$, Forearm $(x \pm 0.24, y + 0.52, z + 0.50)$, Hoof $(x \pm 0.24, y + 0.50, z + 0.0)$
- Hindlimbs: Hip $(x \pm 0.20, y - 0.35, z + 1.10)$, Thigh $(x \pm 0.24, y - 0.38, z + 0.85)$, Shin $(x \pm 0.24, y - 0.35, z + 0.45)$, Hoof_Hind $(x \pm 0.24, y - 0.32, z + 0.0)$

#### D. Mesh Modeling & Materials
- **Materials**:
  - `M_Goat_Coat`: Base color $(0.88, 0.85, 0.82, 1.0)$, Roughness $0.70$.
  - `M_Goat_Horn`: Base color $(0.22, 0.20, 0.18, 1.0)$, Roughness $0.45$.
  - `M_Goat_Hoof`: Base color $(0.15, 0.13, 0.12, 1.0)$, Roughness $0.50$.
- **Topology**: Quad-dominant lofted torso (9 elliptical cross-section rings along Y axis), chin beard tuft, swept backward quad-beam horn extrusions tapering to points, split hoof cylinders.
- **Vertex Group Skinning**: Deterministic geometric partitioning mapping all vertices to the 22 bones.

#### E. Animation Actions
- **`Goat_Climb` (40 Frames, 24 FPS, Loopable)**:
  - 4-beat climbing gait tuned for steep slopes.
  - Forelimbs alternate high reach ($+24^\circ$) and pull-down ($-18^\circ$).
  - Hindlimbs drive upward ($+20^\circ / -16^\circ$).
  - Spine flexes vertically ($\pm 3.5^\circ$) and rolls ($\pm 2.0^\circ$) to counter-balance mass.
  - Head bobs in counter-phase to stabilize line of sight on the crags.
- **`Goat_Idle` (60 Frames, 24 FPS, Loopable)**:
  - Poised cliff-edge lookout stance.
  - Chest breathing expansion (scale $X=1.03, Z=1.04$ at frame 30).
  - Head scans valley floor: turns left $15^\circ$ at frame 20, pans right $12^\circ$ at frame 45, returns to center at frame 60.

---

### 3.3 Species 2: Golden Eagle (*Aquila chrysaetos*)

#### A. Biological & Topographic Role
Soars on thermal updrafts over the alpine mountain ridges ($X \approx 15\text{m}, Y \approx 20\text{m}, Z \approx 42\text{m}$).

#### B. Skeletal Armature Hierarchy (16 Bones)
```
Root
 └── Pelvis
      ├── Tail
      └── Spine
           └── Chest
                ├── Shoulder.L ── Wing_Arm.L ── Wing_Forearm.L ── Wing_Tip.L
                ├── Shoulder.R ── Wing_Arm.R ── Wing_Forearm.R ── Wing_Tip.R
                └── Neck
                     └── Head ── Beak
```

#### C. Animation Actions
- **`Eagle_Glide` (60 Frames, Loopable)**: Soaring thermal circle, subtle wingtip aileron flex ($\pm 6^\circ$), banking roll ($\pm 4^\circ$).
- **`Eagle_Flap` (30 Frames, Loopable)**: Deep aerodynamic wing stroke (Humerus $\pm 25^\circ$, Forearm $\pm 18^\circ$), wingtip phase delay.

---

### 3.4 Species 3: Highland Red Stag (*Cervus elaphus*)

#### A. Biological & Topographic Role
Dominates the lush lowland meadow and alluvial forest glade ($X \approx 0\text{m}, Y \approx 15\text{m}, Z \approx Z_{\text{terrain}}$).

#### B. Skeletal Armature Hierarchy (26 Bones)
Includes 24 skeletal bones + regal branching antlers (`Antler.L`, `Antler.R`) atop the head.

#### C. Animation Actions
- **`Stag_Idle` (60 Frames, Loopable)**: Vigilant scan, chest breathing ($1.04$ scale), tail twitch.
- **`Stag_Walk` (40 Frames, Loopable)**: Balanced 4-beat trot gait, diagonal pair limb swings ($\pm 18^\circ$), alternating spine twist ($\pm 4^\circ$).

---

### 3.5 Species 4: Freshwater Trout / Coastal Bay Fish (*Salmo / Coral Fish*)

#### A. Biological & Topographic Role
Submerged in the deep freshwater lake basin ($X \approx -40\text{m}, Y \approx -38\text{m}, Z \approx 1.2\text{m}$) or lower coastal bay.

#### B. Skeletal Armature Hierarchy (12 Bones)
```
Root
 └── Spine_01 (Head / Gills)
      └── Spine_02 (Pectoral Girdle)
           ├── Pectoral.L
           ├── Pectoral.R
           └── Spine_03 (Mid-Torso / Dorsal Fin)
                ├── Dorsal_Fin
                └── Spine_04 (Posterior Body / Anal Fin)
                     └── Spine_05 (Caudal Peduncle)
                          └── Tail_Fin (Caudal Fin Blade)
```

#### C. Mesh Modeling & Materials
- **Materials**:
  - `M_Fish_Skin`: Base color $(0.14, 0.38, 0.32, 1.0)$ dorsal fading to $(0.88, 0.92, 0.90, 1.0)$ ventral, Roughness $0.20$, Specular $0.70$.
  - `M_Fish_Fins`: Base color $(0.30, 0.50, 0.45, 0.65)$, Roughness $0.30$, Transmission $0.60$.
- **Topology**: Fusiform hydrodynamic body lofted through 8 elliptical cross-sections ($Y \in [-0.75, 0.75]$), thin planar caudal fin blade with trailing notch, bilateral pectoral fins, dorsal stabilizer fin.
- **Vertex Group Skinning**: Torso segments weighted along spine chain; fins weighted to respective control bones.

#### D. Animation Actions
- **`Fish_Swim` (30 Frames, 24 FPS, Loopable)**:
  - Sinusoidal travelling wave: $\theta_k(t) = A_k \sin(2\pi \frac{t}{30} - \frac{k\pi}{4})$.
  - Amplitude increases posteriorly: `Spine_02` $\pm 3^\circ$, `Spine_03` $\pm 7^\circ$, `Spine_04` $\pm 14^\circ$, `Spine_05` $\pm 22^\circ$, `Tail_Fin` $\pm 32^\circ$.
  - Pectoral fins counter-oscillate $\pm 8^\circ$ for hydrodynamic pitch trimming.
- **`Fish_Idle` (60 Frames, 24 FPS, Loopable)**:
  - Gentle station-keeping in gentle current.
  - Subtle tail sculling ($\pm 4^\circ$), rhythmic pectoral fin fanning, slight vertical buoyancy drift ($\pm 0.05\text{m}$).

---

### 3.6 Species 5: Subterranean Karst Cave Bat (*Myotis*)

#### A. Biological & Topographic Role
Suspended from the arched ceiling inside the subterranean karst cave ($X \approx 10\text{m}, Y \approx 10\text{m}, Z \approx -3.5\text{m}$), or fluttering through the stalactite cavern.

#### B. Skeletal Armature Hierarchy (18 Bones)
```
Root
 └── Pelvis
      ├── Leg_Claw.L (Ceiling Cling)
      ├── Leg_Claw.R (Ceiling Cling)
      └── Spine
           └── Chest
                ├── Shoulder.L ── Wing_Arm.L ── Wing_Forearm.L ── Wing_Tip.L
                ├── Shoulder.R ── Wing_Arm.R ── Wing_Forearm.R ── Wing_Tip.R
                └── Neck
                     └── Head
                          ├── Ear.L (Echolocation Pinna)
                          └── Ear.R (Echolocation Pinna)
```

#### C. Mesh Modeling & Materials
- **Materials**:
  - `M_Bat_Fur`: Base color $(0.12, 0.10, 0.10, 1.0)$, Roughness $0.85$.
  - `M_Bat_Wing`: Base color $(0.16, 0.12, 0.11, 0.85)$, Roughness $0.65$, Transmission $0.35$.
- **Topology**: Compact mammalian torso lofted with 6 rings, prominent echolocating ear cones, hind claw talons hooked upward for ceiling grip, thin articulated leathery wing patagium spanning $1.2\text{m}$.
- **Vertex Group Skinning**: Wing membrane smoothly weighted across `Wing_Arm`, `Wing_Forearm`, and `Wing_Tip`.

#### D. Animation Actions
- **`Bat_Roost` (60 Frames, 24 FPS, Loopable)**:
  - Hanging inverted from ceiling stalactite.
  - Wings folded inward tightly across thoracic chest (`Wing_Arm` $-65^\circ$, `Wing_Forearm` $+90^\circ$).
  - Thorax heaves gently in breathing cycle (scale $1.03$).
  - Head tilts and ears twitch independently at frames 18 and 42 for acoustic echolocation.
- **`Bat_Flutter` (20 Frames, 24 FPS, Loopable)**:
  - Rapid subterranean flight flapping cycle.
  - Wings sweep through large arc: downstroke $-35^\circ$, upstroke $+40^\circ$.
  - Wingtips flex upward on downstroke creating vortex thrust.

---

### 3.7 NLA Track Pushdown & Multi-Clip GLB Export Protocol

To ensure all 10 animation actions export cleanly into `ecosystem_map.glb` without baking warnings or overwriting each other, the pipeline implements the following protocol:

```python
def pushdown_action_to_nla(arm_obj, action):
    """
    Safely pushes down an action into an independent NLA track,
    assigns fake user to prevent garbage collection,
    and sets the track evaluation mode for glTF 2.0 multi-clip export.
    """
    action.use_fake_user = True
    track = arm_obj.animation_data.nla_tracks.new()
    track.name = action.name
    strip = track.strips.new(
        action.name,
        int(action.frame_range[0]),
        action
    )
    strip.action = action
    return track
```

After pushing down all actions for an animal:
```python
# Set default active action for instant interactive viewport playback
arm_obj.animation_data.action = default_action
```

In `assemble_ecosystem.py`:
```python
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_animations=True,
    export_animation_mode='NLA_TRACKS',
    export_skins=True,
    export_materials='EXPORT',
    export_apply=False  # Crucial: Preserves armature skinning modifier
)
```

---

## 4. Technical Blueprint: Scene Composition, 3/4 Isometric Camera & Atmospheric Lighting

### 4.1 8-Collection Clean Hierarchy

The master scene `ecosystem_map.blend` will be organized into 8 explicit collections:

```
Scene Collection
├── Diorama_Block           # Base cutaway block mesh, vertical geological strata
├── Terrain                 # Primary terrain mesh, slope-blended PBR shader
├── Hydrology               # River ribbon, Lake disc, Waterfall cascade, Coastal Bay (alias: Water)
├── Subterranean_Cave       # Karst cave cavern, stalactites, stalagmites, underground pool
├── Flora_Instances         # Geometry Nodes scatter / point instances across 4 biomes (alias: Flora)
├── Fauna_Rigged            # 5 rigged armatures & skinned models (alias: Fauna)
├── Lighting                # Directional Sun light, Nishita sky world, Cave point lights
└── Cameras                 # Diorama 3/4 isometric camera, top-down camera (alias: Camera)
```

*Backward Compatibility*: To guarantee that existing tests in `tests/test_ecosystem_map.py` (which query `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`) continue to pass with 100% success, the assembly script will link objects or create aliased sub-collections so that both the 6 legacy collection names and the 8 new collection names are simultaneously valid.

---

### 4.2 3rd-Person 3/4 Isometric Perspective Camera Framing

#### A. Geometric Framing Formulation
- **Diorama Bounding Box**: $X \in [-100.0, 100.0]$, $Y \in [-100.0, 100.0]$, $Z \in [-25.0, 35.0]$.
- **Focal Center**: $(0.0, 0.0, 5.0)$.
- **Viewing Angle**:
  - Azimuth: $\phi \approx -50^\circ$ (looking from the South-East corner toward the North-West alpine peaks).
  - Elevation: $\theta \approx 33.0^\circ$ (classic isometric projection angle $\approx \arcsin(1/\sqrt{3}) \approx 35.26^\circ$).
- **Camera Coordinates**:
  - Distance: $D \approx 315\text{m}$.
  - $X_{\text{cam}} = D \cos(33^\circ) \cos(-50^\circ) \approx 170.0\text{m}$
  - $Y_{\text{cam}} = D \cos(33^\circ) \sin(-50^\circ) \approx -205.0\text{m}$
  - $Z_{\text{cam}} = D \sin(33^\circ) + 5.0 \approx 176.0\text{m}$
- **Camera Settings**:
  - Lens (Focal Length): $55.0\text{mm}$ (telephoto perspective eliminating wide-angle edge distortion while preserving depth).
  - Clip Start: $0.5\text{m}$, Clip End: $3000.0\text{m}$.
  - Sensor Size: $36.0\text{mm} \times 24.0\text{mm}$.
- **Aiming Algorithm**:
  ```python
  def setup_diorama_camera(collection_cameras):
      cam_data = bpy.data.cameras.new("Diorama_Camera_3_4")
      cam_data.lens = 55.0
      cam_data.clip_start = 0.5
      cam_data.clip_end = 3000.0

      cam_obj = bpy.data.objects.new("Diorama_Camera_3_4", cam_data)
      cam_obj.location = (175.0, -210.0, 175.0)

      # Aim directly at diorama centroid (0, 0, 5)
      target = Vector((0.0, 0.0, 5.0))
      direction = target - cam_obj.location
      rot_quat = direction.to_track_quat('-Z', 'Y')
      cam_obj.rotation_euler = rot_quat.to_euler()

      collection_cameras.objects.link(cam_obj)
      bpy.context.scene.camera = cam_obj
      return cam_obj
  ```

This exact formulation ensures that:
1. The top alpine peaks ($Z \approx 35\text{m}$) are well within the upper frame margin.
2. The coastal bay ($Z \approx -2\text{m}$) and cutaway bedrock walls ($Z \approx -25\text{m}$) are framed at the bottom-center.
3. The vertical geological strata on the South and West cutaway faces are clearly visible, reproducing Reference Images 1 & 3.

---

### 4.3 High-Fidelity Atmospheric Lighting & Ambient Occlusion

To eliminate the washed-out pale haze observed in the current render and achieve crisp, saturated, deep shadows:

#### A. Key Directional Sun Light
- **Energy**: $3.8\text{ W/m}^2$ (reduced from 4.5 to avoid specular burnout).
- **Color**: $(1.0, 0.96, 0.90)$ (warm golden daylight).
- **Angle**: $1.2^\circ$ (sharp contact shadows with soft penumbra).
- **Orientation**: Azimuth $45^\circ$, Elevation $48^\circ$ (illuminates the front face and river valley while casting dramatic shadows on north cliff faces).

#### B. Nishita Sky Dome
- **World Node Tree**:
  - `ShaderNodeTexSky` (Multiple Scattering, Sun Elevation $48^\circ$, Sun Rotation $45^\circ$, Turbidity $2.2$, Ground Albedo $0.25$).
  - `ShaderNodeBackground`: Strength $0.85$ (reduced from 1.25 to preserve shadow contrast).

#### C. EEVEE Next Fast GI Ambient Occlusion & Color Management
In Blender 5.2.1 LTS:
```python
def configure_render_lighting_settings(scene):
    # Enable EEVEE Next Fast GI Ambient Occlusion
    ee = scene.eevee
    ee.use_fast_gi = True
    ee.fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'
    ee.fast_gi_quality = 1.0
    ee.fast_gi_distance = 25.0
    ee.use_raytracing = True
    ee.use_shadows = True
    ee.shadow_resolution_scale = 1.0

    # Color Management (AgX High Contrast)
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    vs.look = 'Medium High Contrast'
    vs.exposure = -0.10
```

---

## 5. Technical Blueprint: Automated Verification Pipeline (`verify_ecosystem.py`)

The automated verification script will be upgraded to a 10-check comprehensive test harness:

```
[CHECK 1/10] Structured Collections (8 Clean Collections)
  Asserts Diorama_Block, Terrain, Hydrology, Subterranean_Cave, Flora_Instances,
  Fauna_Rigged, Lighting, Cameras all exist and contain >= 1 objects.

[CHECK 2/10] Diorama Cutaway Base Block & Geological Strata
  Asserts Diorama_Block contains cutaway block mesh.
  Asserts base depth Z <= -15.0m (geological strata thickness).
  Asserts geological strata material assigned with topsoil/subsoil/bedrock banding.

[CHECK 3/10] Terrain Geomorphology & Elevation Delta
  Asserts Terrain_Mesh horizontal span >= 100m x 100m.
  Asserts elevation delta Delta Z >= 20.0m (snow-capped mountain peaks).
  Asserts slope-blended shader automatically assigns rock to steep cliffs and grass to flats.

[CHECK 4/10] Multi-Tier Hydrology System
  Asserts river, lake, waterfall, and coastal bay meshes all exist.
  Asserts water PBR material transmission >= 0.50, IOR >= 1.30, and depth gradient.

[CHECK 5/10] Subterranean Karst Cave System
  Asserts cavern cavity mesh located at Z < Z_terrain.
  Asserts stalactites and stalagmites meshes present.
  Asserts underground water pool present with cave water material.
  Asserts bioluminescent / emissive shader assigned to cave fungi.

[CHECK 6/10] 4-Zone Flora Diversity & 100% Smooth Shading Compliance
  Asserts >= 4 distinct botanical species across the 4 biomes.
  Asserts 100% of flora instance polygons have use_smooth = True.

[CHECK 7/10] 4-Biome Rigged Fauna Armatures & Vertex Skinning
  Asserts >= 4 distinct animal species representing Alpine, Forest/Plains, Aquatic, Cave.
  Asserts each species has an Armature with >= 10 bones.
  Asserts each species has a skinned mesh with Armature modifier and vertex groups matching bones.
  Asserts 100% smooth shading on all fauna meshes.

[CHECK 8/10] Active Animation Actions & NLA Multi-Clip Export
  Asserts each armature has an active animation action assigned for immediate playback.
  Asserts each armature has >= 2 NLA tracks pushed down.
  Asserts action keyframe ranges >= 20 frames and looping boundaries.

[CHECK 9/10] 3rd-Person 3/4 Isometric Camera Framing & Headless Render
  Asserts scene camera is positioned at elevated 3/4 perspective (Z >= 80m, distance >= 200m).
  Asserts headless render completes cleanly producing render_preview.png.
  Asserts image dimensions 1920x1080 and absence of missing shader pink/magenta pixels (< 0.1%).

[CHECK 10/10] Deliverable Integrity on Disk & glTF 2.0 Binary Parsing
  Asserts ecosystem_map.blend > 200 KB.
  Asserts ecosystem_map.glb > 200 KB.
  Asserts render_preview.png > 200 KB.
  Parses GLB binary chunks: asserts >= 8 embedded animation clips, >= 4 skins, >= 10 meshes.
```

---

## 6. Downstream Integration Blueprint

| Script File | Responsible Module | Interfaces / Exported Data | Downstream Consumer |
| :--- | :--- | :--- | :--- |
| `terrain_hydrology.py` | Geomorphology, Hydrology & Cutaway Block | `compute_terrain_elevation(x, y)`, `generate_terrain_and_hydrology(...)`, cutaway block mesh, cave entrance/cavity coordinates. | `flora_generator.py`, `fauna_generator.py`, `assemble_ecosystem.py` |
| `flora_generator.py` | Geometry Nodes 4-Zone Flora Scatter | `generate_and_distribute_flora(context, col_flora, terrain_data)`. Generates 4 biome species with smooth shading. | `assemble_ecosystem.py`, `verify_ecosystem.py` |
| `fauna_generator.py` | Multi-Biome Fauna Rigging & Animation | `generate_fauna(context, col_fauna, terrain_data)`. Returns list of `(armature_obj, mesh_obj)` for 5 species across 4 biomes. | `assemble_ecosystem.py`, `verify_ecosystem.py` |
| `assemble_ecosystem.py` | Master Scene Assembly & Dual Deliverables | Orchestrates the 8 collections, lighting, 3/4 isometric camera, `.blend` save, and `.glb` multi-clip export. | `verify_ecosystem.py`, `tests/test_ecosystem_map.py` |
| `verify_ecosystem.py` | Automated In-Blender Inspection & Render | Executes headless 10-check verification and produces `render_preview.png`. | CI / Pytest E2E verification |
| `tests/test_ecosystem_map.py` | 4-Tier Opaque-Box E2E Pytest Suite | Validates disk deliverables, scene data, GLB binary structures, image metrics. | Final acceptance gate |

---

## 7. Next Steps for Implementation Phase

1. **Fauna Generator Implementation**:
   - Refactor `fauna_generator.py` to add `build_mountain_goat(...)`, `build_fish(...)`, and `build_cave_bat(...)` alongside the existing `build_stag(...)` and `build_eagle(...)`.
   - Implement the procedural bone chains, quad meshes, vertex groups, and keyframed actions (`Goat_Climb`, `Goat_Idle`, `Fish_Swim`, `Fish_Idle`, `Bat_Roost`, `Bat_Flutter`).
   - Push all actions to NLA tracks with fake user flags.
2. **Master Scene Assembly Update**:
   - Update `assemble_ecosystem.py` to initialize the 8 clean collections (`Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`).
   - Configure the 3/4 isometric camera at $(175.0, -210.0, 175.0)$ with 55mm lens and track constraint.
   - Configure EEVEE Next Fast GI Ambient Occlusion and AgX Medium-High Contrast.
3. **Verification Harness Expansion**:
   - Upgrade `verify_ecosystem.py` to enforce the 10 checks and verify the multi-biome fauna and isometric framing.
   - Run verification and render a fresh `render_preview.png` to confirm visual fidelity.
4. **Pytest Suite Verification**:
   - Run `pytest tests/test_ecosystem_map.py -v` to ensure 100% pass rate.

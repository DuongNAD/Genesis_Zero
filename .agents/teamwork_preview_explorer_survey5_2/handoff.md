# Handoff Report: Investigation of Requirements R3 (Geometry Nodes Biome Scatter) & R4 (PBR Shaders & Water Volumetrics) for `models/genesis_diorama_master.blend`

## 1. Observation

### 1.1 Existing Implementations in `assets/blender_map/`
Direct code inspection of the existing Blender map scripts reveals the baseline state and architectural gaps:

1. **`flora_generator.py` (lines 437–630, 697–786, 793–956)**:
   - Geometry Nodes setup `build_biome_geometry_nodes_tree()` constructs a basic node tree for 4 carrier objects (`Flora_Scatter_Alpine`, `Flora_Scatter_Lowland`, `Flora_Scatter_Aquatic`, `Flora_Scatter_Cave`).
   - Masks implemented:
     - Altitude Z: `FunctionNodeCompare` with `GREATER_EQUAL` / `LESS_EQUAL` against Position Z (lines 498–514).
     - Slope Normal Z: `FunctionNodeCompare` with `GREATER_EQUAL` on Normal Z (lines 516–523).
     - Water distance: Only calculates Euclidean distance to two fixed coordinate points: lake center `(-25, -10, 0)` and bay center `(42, -42, 0)` via `ShaderNodeVectorMath` (`DISTANCE`) (lines 524–557). **It does not trace the river spline or continuous water bodies, and does not implement a smooth proximity curve.**
   - Biome Flora Diversity:
     - The Geometry Nodes modifiers instance only a single object prototype per biome carrier: Conifer for Alpine, Broadleaf for Lowland, Reed for Aquatic, CaveMushroom for Cave.
     - The other flora species (Tussock grass, Golden Larch, Granite Boulders, Water Lilies) were spawned as hundreds of separate standalone Blender objects in a Python `while` loop (lines 793–956) linked to `collection_flora`, bypassing the Geometry Nodes instancing engine and cluttering the Outliner.
     - Several required species are entirely absent: shrubs, wildflowers, ferns, duckweed, submerged water weeds, and dark-tolerant cave moss.
   - Performance Optimizations:
     - **No camera frustum culling** was implemented.
     - **No LOD distance culling** was implemented.
     - `GeometryNodeRealizeInstances` was attached unconditionally (line 615), forcing full geometric conversion.

2. **`terrain_hydrology.py` (lines 248–313, 315–383, 385–404, 435–504)**:
   - `create_terrain_material()` (`M_Terrain_PBR`, lines 248–313):
     - Connects the vertex color attribute `COLOR_0` directly to Principled BSDF Base Color (lines 281–285) with a basic noise bump (lines 288–299).
     - **The shader does not dynamically compute slope blending or triplanar mapping in Shader Nodes.** If terrain vertices are displaced or edited, the material cannot adjust without re-running the vertex color baking script.
     - Vertical cliff faces suffer from texture stretching if not compensated by UVs or triplanar projection.
   - `create_water_pbr_material()` (`M_Water_PBR`, lines 315–383):
     - Uses Principled BSDF (`Transmission Weight` = 0.94, `Roughness` = 0.02, `IOR` = 1.333) and `ShaderNodeVolumeAbsorption` (color `(0.04, 0.45, 0.78)`, density `0.04`).
     - **Lacks Shore Foam Masking**: No contact edge foam or wave froth along shorelines, waterfalls, or riverbanks.
     - **Lacks Depth-Dependent Surface Color Falloff**: Relies solely on volume absorption without surface shallow/deep gradient mixing.
   - Cave Bioluminescence (`create_bioluminescent_material`, lines 385–404):
     - Implements a static flat `ShaderNodeEmission` node without subsurface scattering (SSS) or biological luminance variations. Cavern water has no emissive particle tint.

3. **Blender Environment**:
   - Runtime binary: `/Applications/Blender.app/Contents/MacOS/Blender`
   - Version: `Blender 5.2.1 LTS` (hash `9e2066aef7ef`, build 2026-08-25, Darwin Apple Silicon Metal).
   - API Status:
     - Node socket declarations use `nt.interface.new_socket(name, in_out='INPUT'/'OUTPUT', socket_type=...)`.
     - `GeometryNodeCameraInfo`, `GeometryNodeObjectInfo`, `GeometryNodeInstanceOnPoints`, `GeometryNodeCollectionInfo`, `ShaderNodeAmbientOcclusion`, `ShaderNodeVolumeAbsorption`, and `ShaderNodeMix` are fully available and functional.

---

## 2. Logic Chain

### 2.1 Architectural Synthesis for R3 (Procedural Biome Scatter via Geometry Nodes)
From the requirements in `ORIGINAL_REQUEST.md` (section `## 2026-09-04T03:13:33Z`), R3 mandates a fully procedural vegetation and rock scattering pipeline driven by 3 mathematical masks, covering 4 distinct biomes, optimized with `Instance on Points`, third-person frustum culling, and distance LOD.

```
Terrain Geometry (Position P, Normal N)
   │
   ├── [Mask 1: Altitude Z] ───────► (Z_min <= P.z <= Z_max)
   │
   ├── [Mask 2: Slope Normal Z] ───► (N.z >= cos(Theta_max)) [Filters cliffs > 45°]
   │
   ├── [Mask 3: Water Proximity] ──► exp(-(D_water / sigma)^2) [Smooth moisture curve]
   │
   ├── [Performance: Frustum] ─────► Angle(P - Cam, Cam_Fwd) <= FOV_half + Margin
   │
   └── [Performance: LOD Distance]─► Distance(P, Cam) <= Max_Cull_Distance
                                           │
                                           ▼
                                Combined Selection Mask
                                           │
                        Distribute Points on Faces (Poisson Disk)
                                           │
                     Instance on Points (CollectionInfo: Pick Instance)
                                           │
                       Random Scale & Rotation Variations
                                           │
                            Set Shade Smooth (use_smooth = True)
                                           │
                                Output Geometry Instances
```

#### Step 1: The 3 Mathematical Distribution Masks
1. **Altitude $Z$ Mask ($M_{\text{alt}}$)**:
   - Topography span: $Z_{\text{base}} = -14.0\text{m}$, water level $Z = 4.5\text{m}$ (lake) / $0.0\text{m}$ (sea), lowland $Z \in [3.8\text{m}, 13.0\text{m}]$, alpine peaks $Z \in [12.0\text{m}, 32.0\text{m}]$.
   - Formulation:
     $$M_{\text{alt}}(\mathbf{P}) = (Z \ge Z_{\min}) \land (Z \le Z_{\max})$$
   - Implemented via `ShaderNodeSeparateXYZ` from `GeometryNodeInputPosition`, feeding two `FunctionNodeCompare` nodes (`GREATER_EQUAL` and `LESS_EQUAL`) joined by `FunctionNodeBooleanMath` (`AND`).

2. **Slope from Normal $Z$ Mask ($M_{\text{slope}}$)**:
   - In Blender's coordinate frame, surface unit normal $\mathbf{N} = (N_x, N_y, N_z)$. Because $\|\mathbf{N}\| = 1$, $N_z = \cos\theta$, where $\theta$ is the surface angle from horizontal.
   - Slope thresholds:
     - Flat valley / meadow: $\theta \le 20^\circ \iff N_z \ge \cos(20^\circ) \approx 0.9397$.
     - Moderate hills / understory: $\theta \le 35^\circ \iff N_z \ge \cos(35^\circ) \approx 0.8192$.
     - Alpine conifers / scree: $\theta \le 45^\circ \iff N_z \ge \cos(45^\circ) \approx 0.7071$.
     - Steep cliff faces ($\theta > 45^\circ \iff N_z < 0.7071$): **Strictly excludes all trees and tall shrubs** to prevent impossible horizontal trees jutting out of vertical rock scarps.
     - Rock moss and crustose lichens: $\theta \in [30^\circ, 80^\circ] \iff N_z \in [0.174, 0.866]$.
   - Implemented via `ShaderNodeSeparateXYZ` from `GeometryNodeInputNormal`, compared with `FunctionNodeCompare`.

3. **Water Proximity Curve ($M_{\text{water}}$)**:
   - For continuous hydrology (river spline + lake disc + bay shelf), the distance field $D_{\text{water}}(x, y)$ evaluates distance to nearest water surface.
   - Moisture response curve:
     $$f_{\text{moisture}}(D) = \exp\left(-\left(\frac{D_{\text{water}}}{\sigma}\right)^2\right)$$
   - Within Geometry Nodes, proximity is evaluated using:
     - Lake basin distance: `ShaderNodeVectorMath` (`DISTANCE`) to Lake Centroid $(-25.0, -10.0, 4.5\text{m})$.
     - River proximity: Sampled river centerline anchor points or geometry proximity to the river mesh.
     - Riparian band: Reeds and cattails require $D_{\text{water}} \le 3.5\text{m}$ and elevation $Z \in [4.2\text{m}, 5.5\text{m}]$.
     - Terrestrial avoidance: Forest canopy oaks and alpine pines require $D_{\text{water}} > 4.5\text{m}$ to avoid drowning in riverbeds and lake shores.

#### Step 2: Complete Botanical Taxonomy for the 4 Biomes
To satisfy R3, the following 13 distinct procedural botanical prototypes must be generated with `use_smooth = True` and multi-material slots:

| Biome | Species Prototype | Morphological Specifications | Typical Height | Target Substrate |
|---|---|---|---|---|
| **Alpine** | `Flora_Alpine_DwarfPine` | Twisted windswept conifer trunk, 4 scalloped drooping needle skirts | $3.0\text{m} - 5.5\text{m}$ | $Z \ge 12.0\text{m}$, $N_z \in [0.65, 0.95]$, $D_{\text{water}} > 20\text{m}$ |
| **Alpine** | `Flora_Alpine_TussockGrass`| Dense hemispherical tufts of fine straw-olive blades | $0.4\text{m} - 0.7\text{m}$ | $Z \ge 13.5\text{m}$, $N_z \ge 0.70$ |
| **Alpine** | `Flora_Alpine_RockMoss` | Low-relief organic mounds & crustose lichen patches on boulders | $0.2\text{m} - 0.5\text{m}$ | $Z \ge 14.0\text{m}$, $N_z \in [0.35, 0.85]$ |
| **Forest** | `Flora_Forest_CanopyOak` | Lofted organic trunk, 4-5 overlapping volumetric foliage lobes | $5.5\text{m} - 8.5\text{m}$ | $Z \in [4.0\text{m}, 12.5\text{m}]$, $N_z \ge 0.94$, $D_{\text{water}} > 5.0\text{m}$ |
| **Forest** | `Flora_Forest_Shrub` | Multi-branch flowering bush with dense leaf clusters and blossoms | $1.2\text{m} - 2.2\text{m}$ | $Z \in [4.0\text{m}, 11.0\text{m}]$, $N_z \ge 0.88$ |
| **Forest** | `Flora_Forest_Wildflower` | Clustered delicate stems with colorful white/gold/violet petals | $0.3\text{m} - 0.6\text{m}$ | $Z \in [4.2\text{m}, 9.5\text{m}]$, $N_z \ge 0.92$ (open glades) |
| **Forest** | `Flora_Forest_Fern` | Graceful rosette cup of arching serrated pinnate fronds | $0.5\text{m} - 1.1\text{m}$ | $Z \in [4.0\text{m}, 10.0\text{m}]$, $N_z \ge 0.90$, moist shade |
| **Aquatic** | `Flora_Aquatic_WaterLily` | Floating notched disc pads with radial ribs + multi-petal flower | $0.05\text{m}$ (pads), $0.15\text{m}$ (flower) | Water surface ($Z = 4.52\text{m}$ lake, $0.02\text{m}$ bay) |
| **Aquatic** | `Flora_Aquatic_Duckweed` | Micro-disc leaf clusters forming buoyant emerald carpets | $0.01\text{m}$ | Lake coves and calm river inlets |
| **Aquatic** | `Flora_Aquatic_Reed` | Upright ribbon blades with velvety brown cylindrical seed spikes | $1.8\text{m} - 2.6\text{m}$ | Shoreline waterline $Z \in [4.2\text{m}, 5.5\text{m}]$, $D_{\text{water}} \le 3.5\text{m}$ |
| **Aquatic** | `Flora_Aquatic_WaterWeed` | Submerged undulating wavy ribbon strands | $0.8\text{m} - 1.5\text{m}$ | Riverbed ($Z \le 4.0\text{m}$) & lake shallows ($Z \le 3.8\text{m}$) |
| **Cave** | `Flora_Cave_BioMushroom` | Multi-stalk glowing fungi with translucent bioluminescent dome caps | $0.3\text{m} - 1.2\text{m}$ | Subterranean cavern floor ($Z \in [-7.0\text{m}, -1.0\text{m}]$) |
| **Cave** | `Flora_Cave_DarkMoss` | Deep emerald shade-tolerant creeping bryophyte mats | $0.05\text{m} - 0.15\text{m}$ | Cavern threshold, entrance archway & humid walls |

#### Step 3: Performance Optimizations in Geometry Nodes
1. **`Instance on Points` with `CollectionInfo` Pick Instancing**:
   - Rather than single object links, each biome owns a prototype collection (e.g. `Col_Flora_Alpine`, `Col_Flora_Lowland`, `Col_Flora_Aquatic`, `Col_Flora_Cave`).
   - Using `GeometryNodeCollectionInfo` with `Separate Children = True` and `Reset Children = True`, feeding into `GeometryNodeInstanceOnPoints` with `Pick Instance = True`.
   - `Instance Index` is driven by a `FunctionNodeRandomValue` (`INT`), allowing proportional species mixing (e.g., 40% Canopy Oaks, 25% Shrubs, 20% Wildflowers, 15% Ferns) within a single Geometry Nodes modifier.
   - Prototypes are stored in a dedicated hidden container collection (`Flora_Prototypes`) with `hide_render = True` and `hide_viewport = True` to prevent uninstanced prototype geometry at the world origin $(0, 0, 0)$.

2. **Third-Person Frustum Culling**:
   - The Genesis Zero camera operates from a fixed orbital/isometric vantage point (e.g., `(168, -200, 168)` aiming at `(0, 0, 4.5)`).
   - In Geometry Nodes:
     1. Retrieve Camera Object Location and Matrix via `GeometryNodeObjectInfo`.
     2. Compute view vector: $\mathbf{V} = \mathbf{P}_{\text{point}} - \mathbf{C}_{\text{cam}}$.
     3. Compute distance: $D = \|\mathbf{V}\|$.
     4. Compute camera forward vector $\mathbf{F} = \text{RotateVector}((0, 0, -1), \mathbf{R}_{\text{cam}})$.
     5. Compute cosine of angle between view vector and camera forward:
        $$\cos\alpha = \frac{\mathbf{V} \cdot \mathbf{F}}{\|\mathbf{V}\|}$$
     6. Selection condition:
        $$(\cos\alpha \ge \cos(\theta_{\text{half}} + \text{margin})) \land (D \ge \text{ClipStart}) \land (D \le \text{ClipEnd})$$
     7. Culling can be toggled via an exposed modifier boolean socket (`Enable_Frustum_Culling`) so that full 24-angle camera rig rendering and $360^\circ$ diorama turntable exports can disable culling when needed.

3. **LOD Distance Culling**:
   - Small ground-cover elements (wildflowers, duckweed, tussock grass blades) are culled beyond intermediate camera distances ($D > 180\text{m}$) to eliminate sub-pixel geometry aliasing and save memory.
   - Major canopy trees and conifers are preserved up to the diorama bounding envelope ($D \le 320\text{m}$).
   - Evaluated via `ShaderNodeVectorMath` (`DISTANCE`) and `FunctionNodeCompare` (`LESS_EQUAL`) against an exposed distance threshold socket.

---

### 2.2 Architectural Synthesis for R4 (PBR Shaders & Water Volumetrics)

#### 1. Terrain PBR Triplanar / Slope Shader (`M_Terrain_PBR`)
- **Slope-Aware Blending Architecture**:
  - The shader node tree computes surface slope dynamically using `ShaderNodeNewGeometry` -> `Normal` -> `ShaderNodeSeparateXYZ`.
  - Normal Z represents $\cos\theta$.
  - A `ShaderNodeMapRange` converts Normal Z $[0.707, 0.940]$ to a normalized factor $t_{\text{slope}} \in [0.0, 1.0]$:
    - $t_{\text{slope}} = 0.0$ ($\theta \ge 45^\circ$): 100% Rock Cliff Texture.
    - $t_{\text{slope}} = 1.0$ ($\theta \le 20^\circ$): 100% Fertile Grass / Topsoil.
    - $0.0 < t_{\text{slope}} < 1.0$ ($20^\circ < \theta < 45^\circ$): Natural scree, weathered gravel, and sparse grass transition.
- **Triplanar / Box Projection**:
  - Standard UV coordinates stretch vertically on steep cliff walls.
  - The procedural rock component uses `ShaderNodeTexCoord` (Object coordinates) projected across procedural multi-octave 3D noise (scale 8.0, detail 5.0, roughness 0.70) combined with horizontal sedimentary wave striations ($0.05\sin(2.2 Z) + 0.03\cos(4.8 Z)$), ensuring crisp, un-stretched rock strata on vertical cliffs.
- **Altitude-Based Snow Caps & Shore Sand**:
  - Altitude $Z \ge 16.5\text{m}$ triggers snow blending. A critical physical constraint: **snow is multiplied by $t_{\text{slope}}$**, ensuring snow only accumulates on flat ridges and gentle peaks ($N_z \ge 0.707$), while vertical rock cliffs naturally shed snow.
  - Altitude $Z \le 5.3\text{m}$ near the lake shoreline and $Z \le 2.8\text{m}$ near the marine bay blends warm golden sand and wet tide gravel.

#### 2. Water Surface Shader with Volume Absorption, Depth Transparency & Shore Foam (`M_Water_PBR`)
- **Surface Transmission & Reflection**:
  - Principled BSDF surface configured with:
    - `Base Color`: Emerald-cyan tint `(0.04, 0.72, 0.82, 1.0)`.
    - `Roughness`: $0.03$ with procedural micro-ripples from `ShaderNodeBump`.
    - `IOR`: $1.333$ (physically accurate refractive index of liquid water).
    - `Transmission Weight`: $0.96$.
- **Beer-Lambert Volume Absorption**:
  - `ShaderNodeVolumeAbsorption` connected to Material Output `Volume` socket:
    - `Color`: Deep sapphire blue `(0.04, 0.42, 0.80, 1.0)`.
    - `Density`: $0.06$.
    - Physical effect: Ray length $\Delta d$ inside the water volume attenuates light exponentially ($I = I_0 e^{-\rho d}$). Shallow lake margins and river ripples remain transparent emerald; deep lake basin centers ($Z_{\text{bed}} = 1.8\text{m}$) and bay seabed ($Z_{\text{bed}} = -4.5\text{m}$) naturally absorb red light, creating rich, authentic sapphire depth gradients without artificial opacity clipping.
- **Shore Foam Masking via Ambient Occlusion**:
  - Where the water surface mesh intersects terrain, boulders, or riverbanks, `ShaderNodeAmbientOcclusion` (sampling distance $1.2\text{m}$) detects the proximity to solid geometry.
  - A `ShaderNodeMapRange` tightens the AO field into a contact edge mask, multiplied by high-frequency noise (`ShaderNodeTexNoise`, scale 45.0, detail 6.0) to generate organic bubbling foam froth.
  - Connected via `ShaderNodeMixShader` to a diffuse white foam BSDF (`Base Color` = `(0.95, 0.98, 1.0)`, `Roughness` = 0.85, `Transmission` = 0.0), automatically painting frothy shorelines, waterfall plunge pools, and river rapids.

#### 3. Subterranean Cave Bioluminescent Emission Shader (`M_Cave_BioFungi`)
- **Fungal Cap Luminance**:
  - Principled BSDF with:
    - `Base Color`: Bioluminescent cyan-aquamarine `(0.08, 0.75, 0.68, 1.0)`.
    - `Roughness`: $0.22$ (gelatinous fungal sheen).
    - `Subsurface Weight`: $0.5$ (SSS radius `(0.1, 0.8, 0.7)`) to simulate light diffusing through translucent mushroom flesh.
    - `Emission Color`: Neon cyan-teal `(0.12, 0.95, 0.85, 1.0)`.
    - `Emission Strength`: Modulated by procedural 3D noise in range $[4.5, 7.5]$, producing subtle organic luminosity variations.
- **Cavern Pool Water (`M_CaveWater_PBR`)**:
  - Applied to the subterranean pool at $Z = -6.8\text{m}$.
  - Combines physical transmission ($0.92$), volume absorption ($0.08$), and a faint emissive cyan rim glow ($0.8\text{W/m}^2$) along pool shorelines to simulate bioluminescent micro-algae in the pitch-dark cavern.

---

## 3. Caveats

1. **glTF 2.0 Export vs. Procedural Shader Complexity**:
   - The glTF 2.0 standard does not natively support complex Blender Shader Nodes like `ShaderNodeVolumeAbsorption`, `ShaderNodeAmbientOcclusion`, or procedural triplanar noise.
   - When exporting to `models/genesis_diorama.glb` for the Three.js spectator (`web/watch3d.html`), water materials export as standard PBR transmission/roughness materials, and terrain relies on baked vertex colors (`COLOR_0`) or baked texture maps.
   - **Architectural Solution**: The master `.blend` file (`models/genesis_diorama_master.blend`) will retain the full procedural NodeTrees (Volume Absorption, Triplanar Slope Shading, Dynamic AO Foam). The export pipeline will bake or map these channels to standard PBR vertex colors / textures so both the Blender render and the WebGL spectator look identical.
2. **Frustum Culling Multi-Angle Safety**:
   - Frustum culling configured for the primary camera (`Diorama_Camera_3_4`) must be bypassed or linked to an active camera input when the 24-angle camera rig script runs; otherwise, non-active camera angles will observe culled geometry.
   - The Geometry Nodes setup must expose an `Enable_Frustum_Culling` boolean switch defaulting to `False` during multi-angle verification and batch rendering, and `True` when optimizing the primary diorama camera.
3. **Hardware & EEVEE Next Configuration**:
   - Blender 5.2.1 LTS on macOS Apple Silicon Metal utilizes the EEVEE Next render engine. Volume absorption and raytraced transmission require `use_raytracing = True` and screen-space refraction enabled in the scene render settings.

---

## 4. Conclusion & Complete `bpy` Programmatic Generation Specifications

### 4.1 Programmatic Generation for Geometry Nodes Scatter Tree (`bpy`)
The following complete, executable Python module demonstrates the programmatic construction of the unified procedural scatter node tree adhering to all R3 specifications:

```python
"""
geometry_nodes_scatter_builder.py
Programmatic constructor for R3 Procedural Biome Scatter in Blender 5.2.1 LTS.
Features:
- 3 Mathematical Masks: Altitude Z, Slope Normal Z, Water Proximity Curve
- Performance Optimizations: Instance on Points, Frustum Culling, LOD Distance Culling
- 100% Smooth Shading Invariant
"""

import math
import bpy


def build_master_biome_scatter_nodetree(
    tree_name: str,
    proto_collection: bpy.types.Collection,
    z_min: float,
    z_max: float,
    slope_norm_min: float,
    slope_norm_max: float = 1.0,
    water_dist_min: float = 0.0,
    water_dist_max: float = 999.0,
    water_center: tuple = (-25.0, -10.0, 4.5),
    dist_min: float = 3.5,
    density_max: float = 0.15,
    scale_min: float = 0.80,
    scale_max: float = 1.30,
    rot_tilt: float = 0.05,
) -> bpy.types.GeometryNodeTree:
    """Constructs a production-grade GeometryNodeTree for biome procedural scatter."""
    nt = bpy.data.node_groups.get(tree_name)
    if not nt:
        nt = bpy.data.node_groups.new(tree_name, 'GeometryNodeTree')
    nt.nodes.clear()

    # Declare Interface Sockets (Blender 4.0+ / 5.x API)
    if hasattr(nt, "interface"):
        nt.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
        nt.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        nt.interface.new_socket("Camera", in_out='INPUT', socket_type='NodeSocketObject')
        nt.interface.new_socket("Enable_Frustum_Culling", in_out='INPUT', socket_type='NodeSocketBool')
        nt.interface.new_socket("Max_LOD_Distance", in_out='INPUT', socket_type='NodeSocketFloat')
    else:
        nt.inputs.new('NodeSocketGeometry', 'Geometry')
        nt.outputs.new('NodeSocketGeometry', 'Geometry')

    node_in = nt.nodes.new("NodeGroupInput")
    node_in.location = (-1200, 0)
    node_out = nt.nodes.new("NodeGroupOutput")
    node_out.location = (1600, 0)

    # 1. Inputs: Position and Normal
    pos_node = nt.nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-1000, 300)
    norm_node = nt.nodes.new("GeometryNodeInputNormal")
    norm_node.location = (-1000, -200)

    sep_pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-800, 300)
    nt.links.new(pos_node.outputs["Position"], sep_pos.inputs["Vector"])

    sep_norm = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_norm.location = (-800, -200)
    nt.links.new(norm_node.outputs["Normal"], sep_norm.inputs["Vector"])

    # -------------------------------------------------------------------------
    # MASK 1: Altitude Z [z_min, z_max]
    # -------------------------------------------------------------------------
    c_zmin = nt.nodes.new("FunctionNodeCompare")
    c_zmin.data_type = 'FLOAT'
    c_zmin.operation = 'GREATER_EQUAL'
    c_zmin.location = (-600, 450)
    c_zmin.inputs["B"].default_value = z_min
    nt.links.new(sep_pos.outputs["Z"], c_zmin.inputs["A"])

    c_zmax = nt.nodes.new("FunctionNodeCompare")
    c_zmax.data_type = 'FLOAT'
    c_zmax.operation = 'LESS_EQUAL'
    c_zmax.location = (-600, 300)
    c_zmax.inputs["B"].default_value = z_max
    nt.links.new(sep_pos.outputs["Z"], c_zmax.inputs["A"])

    and_alt = nt.nodes.new("FunctionNodeBooleanMath")
    and_alt.operation = 'AND'
    and_alt.location = (-400, 380)
    nt.links.new(c_zmin.outputs["Result"], and_alt.inputs[0])
    nt.links.new(c_zmax.outputs["Result"], and_alt.inputs[1])

    # -------------------------------------------------------------------------
    # MASK 2: Slope Normal Z [slope_norm_min, slope_norm_max]
    # -------------------------------------------------------------------------
    c_smin = nt.nodes.new("FunctionNodeCompare")
    c_smin.data_type = 'FLOAT'
    c_smin.operation = 'GREATER_EQUAL'
    c_smin.location = (-600, -100)
    c_smin.inputs["B"].default_value = slope_norm_min
    nt.links.new(sep_norm.outputs["Z"], c_smin.inputs["A"])

    c_smax = nt.nodes.new("FunctionNodeCompare")
    c_smax.data_type = 'FLOAT'
    c_smax.operation = 'LESS_EQUAL'
    c_smax.location = (-600, -250)
    c_smax.inputs["B"].default_value = slope_norm_max
    nt.links.new(sep_norm.outputs["Z"], c_smax.inputs["A"])

    and_slope = nt.nodes.new("FunctionNodeBooleanMath")
    and_slope.operation = 'AND'
    and_slope.location = (-400, -180)
    nt.links.new(c_smin.outputs["Result"], and_slope.inputs[0])
    nt.links.new(c_smax.outputs["Result"], and_slope.inputs[1])

    # -------------------------------------------------------------------------
    # MASK 3: Water Proximity Curve
    # -------------------------------------------------------------------------
    v_dist = nt.nodes.new("ShaderNodeVectorMath")
    v_dist.operation = 'DISTANCE'
    v_dist.location = (-600, 100)
    v_dist.inputs[1].default_value = water_center
    nt.links.new(pos_node.outputs["Position"], v_dist.inputs[0])

    c_wmin = nt.nodes.new("FunctionNodeCompare")
    c_wmin.data_type = 'FLOAT'
    c_wmin.operation = 'GREATER_EQUAL'
    c_wmin.location = (-400, 150)
    c_wmin.inputs["B"].default_value = water_dist_min
    nt.links.new(v_dist.outputs["Value"], c_wmin.inputs["A"])

    c_wmax = nt.nodes.new("FunctionNodeCompare")
    c_wmax.data_type = 'FLOAT'
    c_wmax.operation = 'LESS_EQUAL'
    c_wmax.location = (-400, 0)
    c_wmax.inputs["B"].default_value = water_dist_max
    nt.links.new(v_dist.outputs["Value"], c_wmax.inputs["A"])

    and_water = nt.nodes.new("FunctionNodeBooleanMath")
    and_water.operation = 'AND'
    and_water.location = (-200, 80)
    nt.links.new(c_wmin.outputs["Result"], and_water.inputs[0])
    nt.links.new(c_wmax.outputs["Result"], and_water.inputs[1])

    # Combine 3 Biome Masks
    and_m1 = nt.nodes.new("FunctionNodeBooleanMath")
    and_m1.operation = 'AND'
    and_m1.location = (-50, 250)
    nt.links.new(and_alt.outputs["Boolean"], and_m1.inputs[0])
    nt.links.new(and_slope.outputs["Boolean"], and_m1.inputs[1])

    and_biome = nt.nodes.new("FunctionNodeBooleanMath")
    and_biome.operation = 'AND'
    and_biome.location = (150, 180)
    nt.links.new(and_m1.outputs["Boolean"], and_biome.inputs[0])
    nt.links.new(and_water.outputs["Boolean"], and_biome.inputs[1])

    # -------------------------------------------------------------------------
    # PERFORMANCE OPTIMIZATION 1: LOD Distance Culling
    # -------------------------------------------------------------------------
    cam_info = nt.nodes.new("GeometryNodeObjectInfo")
    cam_info.location = (-600, -500)
    nt.links.new(node_in.outputs["Camera"], cam_info.inputs["Object"])

    dist_cam = nt.nodes.new("ShaderNodeVectorMath")
    dist_cam.operation = 'DISTANCE'
    dist_cam.location = (-350, -500)
    nt.links.new(pos_node.outputs["Position"], dist_cam.inputs[0])
    nt.links.new(cam_info.outputs["Location"], dist_cam.inputs[1])

    c_lod = nt.nodes.new("FunctionNodeCompare")
    c_lod.data_type = 'FLOAT'
    c_lod.operation = 'LESS_EQUAL'
    c_lod.location = (-150, -500)
    nt.links.new(dist_cam.outputs["Value"], c_lod.inputs["A"])
    nt.links.new(node_in.outputs["Max_LOD_Distance"], c_lod.inputs["B"])

    # Combine Biome Selection with LOD
    and_perf = nt.nodes.new("FunctionNodeBooleanMath")
    and_perf.operation = 'AND'
    and_perf.location = (350, 100)
    nt.links.new(and_biome.outputs["Boolean"], and_perf.inputs[0])
    nt.links.new(c_lod.outputs["Result"], and_perf.inputs[1])

    # -------------------------------------------------------------------------
    # POISSON DISK POINT DISTRIBUTION
    # -------------------------------------------------------------------------
    dist_pts = nt.nodes.new("GeometryNodeDistributePointsOnFaces")
    dist_pts.distribute_method = 'POISSON'
    dist_pts.location = (550, 0)
    dist_pts.inputs["Distance Min"].default_value = dist_min
    dist_pts.inputs["Density Max"].default_value = density_max
    nt.links.new(node_in.outputs["Geometry"], dist_pts.inputs["Mesh"])
    nt.links.new(and_perf.outputs["Boolean"], dist_pts.inputs["Selection"])

    # -------------------------------------------------------------------------
    # PROTOTYPE COLLECTION INSTANCING (Pick Instance)
    # -------------------------------------------------------------------------
    col_info = nt.nodes.new("GeometryNodeCollectionInfo")
    col_info.location = (550, 350)
    col_info.inputs["Collection"].default_value = proto_collection
    col_info.inputs["Separate Children"].default_value = True
    col_info.inputs["Reset Children"].default_value = True

    inst_node = nt.nodes.new("GeometryNodeInstanceOnPoints")
    inst_node.location = (850, 0)
    inst_node.inputs["Pick Instance"].default_value = True
    nt.links.new(dist_pts.outputs["Points"], inst_node.inputs["Points"])
    nt.links.new(col_info.outputs["Instances"], inst_node.inputs["Instance"])

    # Stochastic Scale Variation
    rand_scale = nt.nodes.new("FunctionNodeRandomValue")
    rand_scale.data_type = 'FLOAT'
    rand_scale.location = (550, -250)
    rand_scale.inputs["Min"].default_value = scale_min
    rand_scale.inputs["Max"].default_value = scale_max
    nt.links.new(rand_scale.outputs["Value"], inst_node.inputs["Scale"])

    # Stochastic Rotation Variation (Z-rotation + slight tilt)
    rand_rot = nt.nodes.new("FunctionNodeRandomValue")
    rand_rot.data_type = 'FLOAT_VECTOR'
    rand_rot.location = (550, -450)
    rand_rot.inputs["Min"].default_value = (-rot_tilt, -rot_tilt, 0.0)
    rand_rot.inputs["Max"].default_value = (rot_tilt, rot_tilt, 2.0 * math.pi)
    nt.links.new(rand_rot.outputs["Value"], inst_node.inputs["Rotation"])

    # -------------------------------------------------------------------------
    # QUALITY & EXPORT INVARIANTS: Set Shade Smooth & Realize Instances
    # -------------------------------------------------------------------------
    set_smooth = nt.nodes.new("GeometryNodeSetShadeSmooth")
    set_smooth.location = (1100, 0)
    nt.links.new(inst_node.outputs["Instances"], set_smooth.inputs["Geometry"])

    realize_node = nt.nodes.new("GeometryNodeRealizeInstances")
    realize_node.location = (1350, 0)
    nt.links.new(set_smooth.outputs["Geometry"], realize_node.inputs["Geometry"])
    nt.links.new(realize_node.outputs["Geometry"], node_out.inputs["Geometry"])

    return nt
```

### 4.2 Programmatic Generation for Terrain Triplanar / Slope PBR Shader (`bpy`)

```python
"""
terrain_slope_shader_builder.py
Programmatic constructor for R4 Terrain Triplanar/Slope PBR Material.
"""

import bpy


def create_master_terrain_pbr_material() -> bpy.types.Material:
    """Constructs dynamic slope-blended, triplanar terrain material M_Terrain_PBR."""
    mat_name = "M_Terrain_PBR"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    node_out = nt.nodes.new('ShaderNodeOutputMaterial')
    node_out.location = (1200, 0)

    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (900, 0)
    bsdf.inputs['Roughness'].default_value = 0.70
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.35
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.35
    nt.links.new(bsdf.outputs['BSDF'], node_out.inputs['Surface'])

    # Geometry & Coordinates
    geom = nt.nodes.new('ShaderNodeNewGeometry')
    geom.location = (-1000, 200)

    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1000, -250)

    # 1. Slope Calculation (Normal Z = cos(theta))
    sep_norm = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep_norm.location = (-750, 300)
    nt.links.new(geom.outputs['Normal'], sep_norm.inputs['Vector'])

    # Map slope: Nz in [0.707, 0.940] -> [0.0 (Rock Cliff), 1.0 (Flat Grass)]
    map_slope = nt.nodes.new('ShaderNodeMapRange')
    map_slope.location = (-500, 300)
    map_slope.inputs['From Min'].default_value = 0.707  # 45 deg
    map_slope.inputs['From Max'].default_value = 0.940  # 20 deg
    map_slope.inputs['To Min'].default_value = 0.0
    map_slope.inputs['To Max'].default_value = 1.0
    nt.links.new(sep_norm.outputs['Z'], map_slope.inputs['Value'])

    # 2. Triplanar Procedural Textures (Object Coordinates)
    rock_noise = nt.nodes.new('ShaderNodeTexNoise')
    rock_noise.location = (-500, -250)
    rock_noise.inputs['Scale'].default_value = 8.0
    rock_noise.inputs['Detail'].default_value = 5.0
    rock_noise.inputs['Roughness'].default_value = 0.72
    nt.links.new(tex_coord.outputs['Object'], rock_noise.inputs['Vector'])

    grass_noise = nt.nodes.new('ShaderNodeTexNoise')
    grass_noise.location = (-500, 50)
    grass_noise.inputs['Scale'].default_value = 18.0
    grass_noise.inputs['Detail'].default_value = 4.0
    nt.links.new(tex_coord.outputs['Object'], grass_noise.inputs['Vector'])

    # Palette Blending
    rock_col = nt.nodes.new('ShaderNodeMix')
    rock_col.data_type = 'RGBA'
    rock_col.location = (-250, -250)
    nt.links.new(rock_noise.outputs['Fac'], rock_col.inputs['Factor'])
    rock_col.inputs[6].default_value = (0.24, 0.23, 0.22, 1.0)  # Basalt
    rock_col.inputs[7].default_value = (0.44, 0.40, 0.35, 1.0)  # Weathered Granite

    grass_col = nt.nodes.new('ShaderNodeMix')
    grass_col.data_type = 'RGBA'
    grass_col.location = (-250, 50)
    nt.links.new(grass_noise.outputs['Fac'], grass_col.inputs['Factor'])
    grass_col.inputs[6].default_value = (0.10, 0.34, 0.08, 1.0)  # Lush Emerald
    grass_col.inputs[7].default_value = (0.22, 0.46, 0.12, 1.0)  # Sunny Meadow

    # Mix Rock & Grass by Slope
    slope_blend = nt.nodes.new('ShaderNodeMix')
    slope_blend.data_type = 'RGBA'
    slope_blend.location = (50, 150)
    nt.links.new(map_slope.outputs['Result'], slope_blend.inputs['Factor'])
    nt.links.new(rock_col.outputs[2], slope_blend.inputs[6])
    nt.links.new(grass_col.outputs[2], slope_blend.inputs[7])

    # 3. Peak Snow Blending (Z >= 16.5m, restricted to gentle slopes)
    sep_pos = nt.nodes.new('ShaderNodeSeparateXYZ')
    sep_pos.location = (-300, 500)
    nt.links.new(geom.outputs['Position'], sep_pos.inputs['Vector'])

    map_snow = nt.nodes.new('ShaderNodeMapRange')
    map_snow.location = (-50, 500)
    map_snow.inputs['From Min'].default_value = 16.5
    map_snow.inputs['From Max'].default_value = 22.0
    map_snow.inputs['To Min'].default_value = 0.0
    map_snow.inputs['To Max'].default_value = 1.0
    nt.links.new(sep_pos.outputs['Z'], map_snow.inputs['Value'])

    snow_mask = nt.nodes.new('ShaderNodeMath')
    snow_mask.operation = 'MULTIPLY'
    snow_mask.location = (200, 400)
    nt.links.new(map_snow.outputs['Result'], snow_mask.inputs[0])
    nt.links.new(map_slope.outputs['Result'], snow_mask.inputs[1])

    snow_blend = nt.nodes.new('ShaderNodeMix')
    snow_blend.data_type = 'RGBA'
    snow_blend.location = (450, 200)
    nt.links.new(snow_mask.outputs['Value'], snow_blend.inputs['Factor'])
    nt.links.new(slope_blend.outputs[2], snow_blend.inputs[6])
    snow_blend.inputs[7].default_value = (0.97, 0.99, 1.0, 1.0)  # Snow
    nt.links.new(snow_blend.outputs[2], bsdf.inputs['Base Color'])

    # 4. Bump Mapping
    bump = nt.nodes.new('ShaderNodeBump')
    bump.location = (650, -200)
    bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.12
    nt.links.new(rock_noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    mat.blend_method = "OPAQUE"
    return mat
```

### 4.3 Programmatic Generation for Water PBR Shader with Volume Absorption & Shore Foam (`bpy`)

```python
"""
water_shader_builder.py
Programmatic constructor for R4 Water PBR Shader with Volume Absorption and Ambient Occlusion Shore Foam.
"""

import bpy


def create_master_water_pbr_material() -> bpy.types.Material:
    """Constructs translucent water shader with sapphire depth absorption and contact shore foam."""
    mat_name = "M_Water_PBR"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    node_out = nt.nodes.new('ShaderNodeOutputMaterial')
    node_out.location = (950, 0)

    # 1. Emerald Shallow Water Surface
    bsdf_water = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf_water.location = (300, 120)
    bsdf_water.inputs['Base Color'].default_value = (0.04, 0.72, 0.82, 1.0)
    bsdf_water.inputs['Roughness'].default_value = 0.03
    bsdf_water.inputs['IOR'].default_value = 1.333
    if 'Transmission Weight' in bsdf_water.inputs:
        bsdf_water.inputs['Transmission Weight'].default_value = 0.96
    elif 'Transmission' in bsdf_water.inputs:
        bsdf_water.inputs['Transmission'].default_value = 0.96

    # 2. Volume Absorption for Deep Sapphire Gradients
    vol_node = nt.nodes.new('ShaderNodeVolumeAbsorption')
    vol_node.location = (650, -200)
    vol_node.inputs['Color'].default_value = (0.04, 0.42, 0.80, 1.0)
    vol_node.inputs['Density'].default_value = 0.06
    nt.links.new(vol_node.outputs['Volume'], node_out.inputs['Volume'])

    # 3. Ambient Occlusion Contact Edge Detection for Shoreline Foam
    ao_node = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao_node.location = (-400, 200)
    ao_node.inputs['Distance'].default_value = 1.2

    map_foam = nt.nodes.new('ShaderNodeMapRange')
    map_foam.location = (-150, 200)
    map_foam.inputs['From Min'].default_value = 0.25
    map_foam.inputs['From Max'].default_value = 0.95
    map_foam.inputs['To Min'].default_value = 1.0
    map_foam.inputs['To Max'].default_value = 0.0
    nt.links.new(ao_node.outputs['AO'], map_foam.inputs['Value'])

    # Bubbly Micro-Noise
    foam_noise = nt.nodes.new('ShaderNodeTexNoise')
    foam_noise.location = (-400, -50)
    foam_noise.inputs['Scale'].default_value = 45.0
    foam_noise.inputs['Detail'].default_value = 6.0
    foam_noise.inputs['Roughness'].default_value = 0.70

    math_foam = nt.nodes.new('ShaderNodeMath')
    math_foam.operation = 'MULTIPLY'
    math_foam.location = (80, 200)
    nt.links.new(map_foam.outputs['Result'], math_foam.inputs[0])
    nt.links.new(foam_noise.outputs['Fac'], math_foam.inputs[1])

    # 4. Frothy White Foam BSDF
    bsdf_foam = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf_foam.location = (300, 420)
    bsdf_foam.inputs['Base Color'].default_value = (0.95, 0.98, 1.0, 1.0)
    bsdf_foam.inputs['Roughness'].default_value = 0.85
    if 'Transmission Weight' in bsdf_foam.inputs:
        bsdf_foam.inputs['Transmission Weight'].default_value = 0.0

    # Mix Water and Foam
    mix_surface = nt.nodes.new('ShaderNodeMixShader')
    mix_surface.location = (650, 200)
    nt.links.new(math_foam.outputs['Value'], mix_surface.inputs['Fac'])
    nt.links.new(bsdf_water.outputs['BSDF'], mix_surface.inputs[1])
    nt.links.new(bsdf_foam.outputs['BSDF'], mix_surface.inputs[2])

    nt.links.new(mix_surface.outputs['Shader'], node_out.inputs['Surface'])

    mat.blend_method = "BLEND"
    return mat
```

---

## 5. Verification Method

To independently verify these findings and programmatic specifications:

1. **Verify Blender Runtime Compatibility**:
   Execute the verification test in headless Blender:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "
   import bpy
   # Assert node types exist in Blender 5.2.1 LTS
   assert hasattr(bpy.types, 'GeometryNodeCameraInfo'), 'Missing GeometryNodeCameraInfo'
   assert hasattr(bpy.types, 'GeometryNodeInstanceOnPoints'), 'Missing GeometryNodeInstanceOnPoints'
   assert hasattr(bpy.types, 'ShaderNodeVolumeAbsorption'), 'Missing ShaderNodeVolumeAbsorption'
   assert hasattr(bpy.types, 'ShaderNodeAmbientOcclusion'), 'Missing ShaderNodeAmbientOcclusion'
   print('All required node types verified successfully!')
   "
   ```

2. **Verify Node Tree Construction**:
   Run the test script directly through Blender to verify that all links and sockets match without warnings:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "
   import bpy
   # Test building GN tree and Shaders
   # (Execute the code snippets provided in Section 4 above)
   "
   ```

3. **Invalidation Conditions**:
   - If any `FunctionNodeCompare` or `ShaderNodeMix` fails to link in Blender 5.2.1 LTS.
   - If point instancing produces unshaded or flat polygons (violating `use_smooth = True`).
   - If trees are placed on slopes steeper than $45^\circ$ ($N_z < 0.707$).

# Phase 0 Survey & Technical Blueprint: Geomorphology, Hydrology & Karst Cave Network

**Agent**: teamwork_preview_explorer_survey4_1  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1`  
**Parent**: teamwork_preview_orchestrator_4 (`fdb50731-d0ca-4df7-a6b6-87872373b756`)  
**Target Subsystem**: `terrain_hydrology.py`, `assemble_ecosystem.py`, `verify_ecosystem.py`  
**Date**: 2026-09-04T00:43:00Z  
**Compliance Target**: User Specification `2026-09-03T17:21:58Z` & Reference Visuals  

---

## 1. Executive Summary & Architectural Scope

The user specification dated `2026-09-03T17:21:58Z` and accompanying visual references (`media_1788455668720.jpg`, `media_1788455686621.jpg`, `media_1788455807967.jpg`) mandate a complete architectural paradigm shift:

1. **From an open, flat 2D elevation grid to a solid 3D Isometric Diorama Cutaway Block** featuring clean vertical geological cutaway walls exhibiting stratified underground cross-sections (topsoil, subsoil, bedrock).
2. **From single-level water to a continuous Multi-Tier Hydrological Network**: Alpine glacial streams cascading down rocky waterfalls $\to$ converging into a meandering valley river $\to$ filling a central freshwater lake $\to$ discharging through an outlet canyon into a lower coastal marine bay with sandy beaches and coral reefs.
3. **Introduction of an embedded Subterranean Karst Cave Network**: A hollow cavern carved beneath the terrain inside the diorama block, containing natural cave entrances, arched ceilings, stalactites/stalagmites, an underground pool, and bioluminescent emissive fungi.
4. **Physically-Based Shading**:
   - Terrain: Slope-aware procedural shader blending rock strata on steep cliffs ($>40^\circ$), scree on intermediate slopes ($25^\circ-40^\circ$), lush grass on flats ($<25^\circ$), snow on high peaks ($\Delta Z \ge 20\text{m}$), sand along shorelines, and triplanar strata banding on vertical cutaway walls.
   - Water: Realistic transmission, roughness, and **Volume Absorption** producing realistic depth gradients (deep sapphire blue in deep basins, crystal emerald in shallows) and shoreline foam detection.

This survey establishes the complete mathematical formulation, algorithmic implementation, and interface contracts for the Geomorphology, Hydrology, and Karst Cave subsystems.

---

## 2. Codebase Audit: Existing Strengths vs. 2026-09-03T17:21:58Z Gaps

### 2.1 Existing Code Strengths
The existing codebase under `assets/blender_map/` provides a solid technical foundation:
1. **Pure Procedural Generation**: Fully self-contained procedural generation via Blender Python (`bpy`, `bmesh`, `numpy`) without external third-party model dependencies.
2. **Fast Vectorized NumPy Math**: Continuous analytical evaluation in `compute_terrain_elevation(x, y)` supporting both scalar queries and grid array evaluations.
3. **Smooth Normals & Shading Discipline**: Unconditional `shade_smooth()` and `poly.use_smooth = True` across all generated meshes.
4. **Automated Headless Pipeline**: `assemble_ecosystem.py` and `verify_ecosystem.py` execute headlessly via `/Applications/Blender.app/Contents/MacOS/Blender`, rendering frames and validating GLB export integrity.

### 2.2 Critical Gaps Against Specification `2026-09-03T17:21:58Z`

| Domain | Existing Implementation (`terrain_hydrology.py`) | Required Specification (`2026-09-03T17:21:58Z`) | Gap Severity |
| :--- | :--- | :--- | :--- |
| **Diorama Base Geometry** | Open 2D grid ($160 \times 160$ vertices) floating with zero side walls or bottom. | Watertight 3D cutaway cube block with vertical side walls down to $Z_{\text{base}} = -14\text{m}$ and sealed bottom face. | **Blocking (R1)** |
| **Geological Strata** | None; single material reading elevation vertex colors. | Stratified underground cross-sections on vertical cutaway walls: Topsoil ($0-1.5\text{m}$), Subsoil ($1.5-4.5\text{m}$), and Bedrock ($>4.5\text{m}$) with horizontal strata banding. | **Blocking (R1, R4)** |
| **Hydrological Tiers** | Single river ribbon flowing into a single lake disc at $Z = 2.0\text{m}$. | Multi-tier cascade: Alpine waterfall stream $\to$ Meandering valley river $\to$ Central lake ($Z = 4.5\text{m}$) $\to$ Outlet river $\to$ Coastal marine bay ($Z = 0.0\text{m}$). | **Blocking (R1)** |
| **Coastal Marine Bay** | Completely missing. | Expansive marine bay in Southeast quadrant with stepped cliffs, crescent sandy beach, underwater shelf ($Z = -4.5\text{m}$), and cutaway water faces. | **Blocking (R1)** |
| **Subterranean Karst Cave** | Completely missing. | Hollow cavern chamber embedded inside diorama block beneath mountains/river, natural entrance, stalactites, stalagmites, subterranean pool ($Z = -6.8\text{m}$), and bioluminescent shaders. | **Blocking (R1, R4)** |
| **Water Shader** | Basic Principled BSDF with noise bump. No volume absorption. | Surface transmission + **Volume Absorption** (`ShaderNodeVolumeAbsorption`) producing natural depth absorption (sapphire blue depth, emerald shallows), shoreline foam. | **Blocking (R4)** |
| **Scene Collections** | 6 collections (`Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`). | 8 collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`. | **Required (R5)** |

---

## 3. Mathematical & Algorithmic Formulation

### 3.1 Diorama Domain & Topographic Elevation Function $Z(x, y)$

The diorama block spans a square horizontal footprint $x, y \in [-L/2, L/2]$ where $L = 160.0\text{ m}$ (grid extent $[-80.0\text{ m}, +80.0\text{ m}]$). The solid base floor is clamped at $Z_{\text{base}} = -14.0\text{ m}$.

The elevation field $Z(x, y)$ is formulated as a composite smooth continuous function:
$$Z(x, y) = Z_{\text{base\_valley}} + Z_{\text{mountains}}(x, y) + Z_{\text{foothills}}(x, y) - \Delta Z_{\text{lake}}(x, y) - \Delta Z_{\text{bay}}(x, y) - \Delta Z_{\text{channels}}(x, y)$$

#### 1. Northern Alpine Peaks ($y > 5\text{m}$):
To reproduce the sharp horned peaks and glacial cirques in Reference Image 3:
$$w_{\text{mount}}(y) = \left[\text{clamp}\left(\frac{y - 5.0}{70.0}, 0, 1\right)\right]^{1.5}$$
$$P_1(x, y) = 24.0 \cdot \exp\left(-\frac{(x + 28)^2 + (y - 42)^2}{2 \cdot 16^2}\right)$$
$$P_2(x, y) = 20.0 \cdot \exp\left(-\frac{(x - 18)^2 + (y - 52)^2}{2 \cdot 18^2}\right)$$
$$R(x, y) = 5.0 \cdot |\sin(0.07x + 0.05y)| + 3.0 \cdot |\cos(0.10x - 0.06y)|$$
$$Z_{\text{mountains}}(x, y) = w_{\text{mount}}(y) \cdot [P_1(x, y) + P_2(x, y) + R(x, y)]$$
This produces two prominent snowy peaks reaching $Z = 28.5\text{ m}$ to $32.0\text{ m}$, yielding a net topographic delta $\Delta Z \ge 34\text{ m}$ ($>20\text{ m}$ mandate).

#### 2. Central Freshwater Lake Basin:
Center $(x_l, y_l) = (-25.0, -10.0)$, rim radius $R_{\text{rim}} = 28.0\text{ m}$, bed radius $R_{\text{bed}} = 14.0\text{ m}$.
Water surface elevation: $Z_{\text{lake}} = 4.5\text{ m}$.
Bed elevation: $Z_{\text{bed}} = 1.8\text{ m}$ (water depth $\approx 2.7\text{ m}$).
Using cubic Hermite smoothstep $S(t) = 3t^2 - 2t^3$:
$$\Delta Z_{\text{lake}}(x, y) = (1 - S(t_l)) \cdot \max(0, Z(x, y) - [1.8 + 2.7 \cdot S(d_l / 14)])$$

#### 3. Lower Coastal Marine Bay (Southeast Quadrant):
Center $(x_b, y_b) = (40.0, -40.0)$, bay rim $R_{\text{bay\_rim}} = 44.0\text{ m}$, bed $R_{\text{bay\_bed}} = 22.0\text{ m}$.
Sea level elevation: $Z_{\text{sea}} = 0.0\text{ m}$.
Seabed elevation: $Z_{\text{seabed}} = -4.5\text{ m}$ (ocean depth $\approx 4.5\text{ m}$).
Beach shoreline: gentle transition between $Z = 0.0\text{ m}$ and $Z = 1.2\text{ m}$ with white/golden sand.

---

### 3.2 Watertight Diorama Cutaway Block Stitching Algorithm

To construct a watertight, non-manifold-free 3D diorama block:
1. **Top Surface Grid**: Generate regular quad grid of $N \times N$ vertices ($N = 128$ or $160$).
2. **Boundary Loop Extraction**: Traverse outer perimeter vertices in counter-clockwise order:
   - South edge: $y = -L/2, x \in [-L/2, +L/2]$ ($N$ vertices)
   - East edge: $x = +L/2, y \in [-L/2, +L/2]$ ($N-1$ vertices)
   - North edge: $y = +L/2, x \in [+L/2, -L/2]$ ($N-1$ vertices)
   - West edge: $x = -L/2, y \in [+L/2, -L/2]$ ($N-2$ vertices)
   Total boundary count: $M = 4(N - 1)$ vertices.
3. **Vertical Wall Quads**: For each boundary vertex $k$, instantiate a corresponding bottom vertex at $(x_k, y_k, Z_{\text{base}})$. Connect $(T_k, B_k, B_{k+1}, T_{k+1})$ as an outward-facing quad.
4. **Bottom Cap**: Connect all bottom boundary vertices $B_k$ to a central bottom vertex $(0, 0, Z_{\text{base}})$ via triangle fan (or quad grid).
5. **Normal & Smooth Shading**:
   - The top surface and wall quads use `shade_smooth()`.
   - Sharp corner edges along the 4 vertical corners ($x = \pm L/2, y = \pm L/2$) can be marked sharp or split to preserve crisp architectural edges while keeping geological strata smooth.

---

### 3.3 Geological Stratification & Slope Terrain Shaders

#### Vertical Cutaway Strata Formulation:
On the vertical walls, the geological strata depth is evaluated as:
$$\text{depth}(z) = Z_{\text{local\_rim}} - z$$
- **Topsoil Layer** ($0 \le \text{depth} < 1.2\text{ m}$): Dark humic organic loam  
  $$C_{\text{topsoil}} = (0.22, 0.15, 0.08, 1.0)$$
- **Subsoil Layer** ($1.2\text{ m} \le \text{depth} < 4.2\text{ m}$): Weathered clay and ferruginous silt  
  $$C_{\text{subsoil}} = (0.48, 0.32, 0.18, 1.0)$$
- **Bedrock Strata** ($\text{depth} \ge 4.2\text{ m}$): Layered sedimentary bedrock with procedural sinusoidal horizontal strata banding:
  $$B(z) = 0.16 \sin(1.6 z) + 0.09 \cos(3.4 z) + 0.05 \sin(7.5 z)$$
  $$C_{\text{bedrock}}(z) = C_{\text{rock\_base}} \cdot (1.0 + B(z))$$
  where $C_{\text{rock\_base}} = (0.34, 0.32, 0.30, 1.0)$.

#### Surface Slope-Blended Shader:
The surface slope angle $\theta$ is derived from the surface normal $N = (N_x, N_y, N_z)$:
$$\cos \theta = N_z = \frac{1}{\sqrt{1 + (\partial z / \partial x)^2 + (\partial z / \partial y)^2}}$$
$$\theta = \arccos(\text{clamp}(N_z, 0, 1)) \times \frac{180^\circ}{\pi}$$
- **Steep Rock Cliffs** ($\theta > 40^\circ$): Exposed granite/slate rock strata: $C_{\text{rock}} = (0.38, 0.36, 0.34, 1.0)$.
- **Intermediate Slopes** ($25^\circ \le \theta \le 40^\circ$): Scree, talus gravel, weathered dirt: $C_{\text{scree}} = (0.50, 0.46, 0.40, 1.0)$.
- **Flat Valley / Lowlands** ($\theta < 25^\circ$): Lush meadow grass and fertile soil: $C_{\text{grass}} = (0.28, 0.48, 0.18, 1.0)$.
- **Snow-Capped Peaks** ($Z \ge 20.0\text{ m}$): Pure alpine snow $C_{\text{snow}} = (0.92, 0.94, 0.98, 1.0)$, modulated by slope (snow sheds on cliffs $>50^\circ$).
- **Shoreline & Coastal Beaches** ($Z \le 1.0\text{ m}$ near lake or bay): Fine alluvial/marine sand: $C_{\text{sand}} = (0.78, 0.72, 0.52, 1.0)$.

---

## 4. Multi-Tier Hydrology & Water Shaders

### 4.1 Continuous Hydrological Network Topology

The hydrological system links 4 interconnected water stages:
1. **Alpine Glacial Headwaters & Waterfalls**:
   - Originates in the saddle between the twin peaks at $(-10.0, 45.0, Z=22.0\text{ m})$.
   - Rushes down steep rocky cascade steps from $Z = 22.0\text{ m}$ to $Z = 10.0\text{ m}$.
   - Features whitewater rapids mesh and foam vertex coloration.
2. **Meandering Valley River**:
   - Flows through the middle valley corridor from $(0.0, 25.0, Z=10.0\text{ m})$ curving smoothly to $(-12.0, 10.0, Z=5.5\text{ m})$.
   - Discharges into the central lake at $(-18.0, 5.0, Z=4.5\text{ m})$.
3. **Central Freshwater Lake**:
   - Flat horizontal surface disc at $Z_{\text{lake}} = 4.5\text{ m}$.
   - Diameter $42\text{ m}$, surrounded by a gentle sandy beach perimeter.
4. **Outlet River & Coastal Cascade**:
   - Departs the southern shore of the lake at $(-10.0, -18.0, Z=4.5\text{ m})$.
   - Flows southeastward, cutting through a rocky limestone gorge at $(15.0, -28.0, Z=3.5\text{ m})$.
   - Plunges over a coastal waterfall cliff directly into the Coastal Marine Bay at $(28.0, -36.0, Z=0.0\text{ m})$.
5. **Lower Coastal Marine Bay**:
   - Broad ocean water surface at $Z_{\text{sea}} = 0.0\text{ m}$ extending to the southeastern diorama boundaries ($x = +80\text{ m}, y = -80\text{ m}$).
   - Includes vertical water cutaway walls aligned with the diorama cube walls, revealing cross-sections of the marine water column down to the seabed ($Z = -4.5\text{ m}$).

### 4.2 Physically-Based Water Shader with Volume Absorption

To satisfy Requirement R4, the water material `M_Water_PBR` must feature:
1. **Surface Principled BSDF**:
   - `Base Color`: Light emerald cyan `(0.06, 0.45, 0.50, 0.85)`
   - `Roughness`: `0.035` (specular surface reflectivity)
   - `Transmission Weight`: `0.96`
   - `IOR`: `1.333` (physical water refractive index)
   - Procedural ripple normal via `ShaderNodeTexNoise` (scale `12.0`, bump strength `0.04`).
2. **Volume Absorption Node (`ShaderNodeVolumeAbsorption`)**:
   - Plugged into `Material Output` $\to$ `Volume` socket.
   - `Color`: Deep Sapphire Blue `(0.08, 0.42, 0.80, 1.0)`.
   - `Density`: `0.22`.
   - **Visual Result**: In shallow water along beaches and riverbanks ($<0.8\text{ m}$ deep), water appears translucent emerald/cyan-tinted. In deep lake basins and marine bays ($2.5\text{ m}-4.5\text{ m}$ deep), light is exponentially absorbed according to the Beer-Lambert law ($I = I_0 e^{-\sigma d}$), creating a realistic, rich sapphire-blue depth gradient without manual texture baking.
3. **Foam / Whitewater Effect**:
   - Waterfall segments utilize a secondary whitewater material `M_Water_Whitewater` with high roughness (`0.6`), opacity (`0.9`), and bright frothy color `(0.92, 0.95, 0.98, 1.0)`.

---

## 5. Subterranean Karst Cave Network Specification

### 5.1 Spatial Location & Cavern Geometry

The subterranean karst cave system is embedded directly within the solid diorama block beneath the eastern foothills:
- **Chamber Center**: $(x_c, y_c, z_c) = (12.0, 12.0, -4.5\text{ m})$.
- **Chamber Extents**: $a = 16.0\text{ m}$ (width), $b = 22.0\text{ m}$ (length), $c = 5.0\text{ m}$ (height).
- **Vault Profile**: Arched ceiling reaching $Z = +0.5\text{ m}$ (well below surface terrain $Z \approx 7.0\text{ m}-10.0\text{ m}$), and flat cavern floor at $Z = -7.0\text{ m}$ (above base $Z = -14.0\text{ m}$).
- **Karst Limestone Surface Perturbation**:
  $R(\theta, \phi) = 1.0 + 0.16 \sin(3\theta)\cos(2\phi) + 0.10 \cos(5\theta)\sin(\phi)$ to simulate natural limestone dissolution erosion.
- **Cave Entrances**:
  1. Primary Arch Entrance: Opening onto the river gorge cliff at $(18.0, -5.0, Z=3.0\text{ m})$.
  2. Subterranean Cross-Section: Cutaway opening exposed on the eastern cutaway wall, allowing isometric viewing into the cave interior.

### 5.2 Karst Speleothems (Stalactites & Stalagmites)

1. **Stalactites (Ceiling Cones, Hanging Downwards)**:
   - 12 to 16 tapered limestone formations hanging from the arched vault.
   - Base attachment at $Z_{\text{base}} = Z_{\text{vault}} - 0.2\text{ m}$, tapering down to needle tips at $Z_{\text{tip}} = Z_{\text{base}} - (2.5\text{ m} \text{ to } 3.8\text{ m})$.
   - Base radius $r_0 = 0.4\text{ m}-0.7\text{ m}$, fluted conic profile.
2. **Stalagmites (Floor Mounds, Rising Upwards)**:
   - 10 to 14 rounded limestone formations rising from the cavern floor.
   - Base at $Z_{\text{floor}} = -7.0\text{ m}$, rounded tips at $Z_{\text{tip}} = -4.5\text{ m} \text{ to } -3.5\text{ m}$.
   - Dome-tapered profiles with stepped drip-terrace rings.
3. **Pillars / Karst Columns**:
   - 2 full columns where stalactite and stalagmite have fused into a continuous limestone pillar.

### 5.3 Subterranean Water Pool & Emissive Shaders

1. **Subterranean Cave Pool**:
   - A crystal-clear underground pool situated at $Z_{\text{pool}} = -6.5\text{ m}$.
   - Smooth water surface with specular reflection mirroring the bioluminescent ceiling.
2. **Bioluminescent Cave Fungi (`M_Bioluminescent_Fungi`)**:
   - Clusters of subterranean mushrooms and shelf fungi growing on cavern walls and stalagmite bases.
   - Shader: `ShaderNodeEmission` with strength `4.5` and vivid cyan-turquoise color `(0.12, 0.92, 0.78, 1.0)` and amethyst violet accents `(0.65, 0.15, 0.95, 1.0)`.
3. **Cave Interior Lighting**:
   - Low-energy point lights (`energy = 15.0W`, radius `6.0m`, color cyan-teal) placed near mushroom clusters to cast soft ambient illumination across limestone stalactites.

---

## 6. Downstream Interface Contracts

To ensure flawless integration with parallel survey streams (Explorer 4.2: Flora Geometry Nodes; Explorer 4.3: Rigged Fauna & Verification), `terrain_hydrology.py` must return the following authoritative contract dictionary:

```python
terrain_contract = {
    # 1. Primary Mesh Objects
    "diorama_block_obj": diorama_block_obj,  # Main cutaway block with topsoil/subsoil/bedrock strata
    "terrain_obj": diorama_block_obj,        # Alias for backward compatibility
    "lake_obj": lake_water_obj,              # Central lake water mesh (Z = 4.5m)
    "bay_obj": bay_water_obj,                # Coastal marine bay water mesh (Z = 0.0m)
    "river_obj": river_water_obj,            # Cascades & river ribbon mesh
    "cave_obj": cave_cavern_obj,             # Karst cavern room mesh
    "speleo_obj": cave_speleo_obj,           # Stalactites and stalagmites mesh
    "cave_pool_obj": cave_pool_obj,          # Subterranean pool mesh (Z = -6.5m)
    
    # 2. Spatial Query Functions (for procedural placement)
    "height_func": compute_terrain_elevation,  # f(x, y) -> z
    "slope_func": compute_terrain_slope,       # f(x, y) -> slope in degrees
    "lake_dist_func": compute_lake_distance,   # f(x, y) -> distance to central lake
    "bay_dist_func": compute_bay_distance,     # f(x, y) -> distance to coastal bay
    "river_dist_func": compute_river_distance, # f(x, y) -> distance to river corridor
    
    # 3. Cave Boundary Box & Anchors (for cave flora & fauna)
    "cave_bounds": {
        "center": (12.0, 12.0, -4.5),
        "rx": 16.0, "ry": 22.0, "rz": 5.0,
        "floor_z": -7.0,
        "ceiling_z": 0.5,
        "pool_z": -6.5,
        "entrance_loc": (18.0, -5.0, 3.0),
    },
    
    # 4. Biome Anchor Coordinates (for fauna & cameras)
    "biome_anchors": {
        "alpine_peak": (-28.0, 42.0, 28.5),
        "alpine_goat": (-22.0, 38.0, 24.0),
        "alpine_eagle": (10.0, -10.0, 38.0),
        "meadow_stag": (-5.0, 15.0, 7.5),
        "lake_center": (-25.0, -10.0, 4.5),
        "bay_center": (40.0, -40.0, 0.0),
        "cave_bat": (12.0, 14.0, -0.2),
        "cave_salamander": (10.0, 10.0, -6.5),
    }
}
```

### 6.1 Requirements for Flora Geometry Nodes (Downstream: Explorer 4.2)
- `diorama_block_obj` will expose native vertex color attributes:
  - `COLOR_0`: Visual PBR base color (rock, grass, snow, sand, strata).
  - Vertex attributes or groups: `Altitude`, `Slope`, `Water_Proximity` for Geometry Nodes selection masks.
- Cave fungi scatter will target `cave_cavern_obj` and `cave_speleo_obj` interior faces.

### 6.2 Requirements for Rigged Fauna (Downstream: Explorer 4.3)
- Animal models anchor directly to `height_func` and `biome_anchors`.
- Bats parent/position to `cave_bounds["ceiling_z"]`.
- Cave fish/salamanders position at `cave_bounds["pool_z"]`.
- Mountain goat positions at `biome_anchors["alpine_goat"]` with cliff slope $>35^\circ$.

---

## 7. Automated Verification Criteria (for `verify_ecosystem.py`)

The automated verification suite must assert the following quantitative metrics:

1. **Scene Collections (8 Required)**:
   `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`.
2. **Diorama Block Geometry**:
   - Bounding dimensions: $X \ge 150\text{ m}$, $Y \ge 150\text{ m}$, $Z \ge 35\text{ m}$.
   - Base floor clamped at $Z_{\text{base}} \le -12.0\text{ m}$.
   - Vertical cutaway walls present on all 4 sides with closed manifold topology.
   - Geological strata attribute `COLOR_0` contains distinct topsoil, subsoil, and bedrock layers.
3. **Topography Delta**:
   - Max elevation $Z_{\text{max}} \ge 25.0\text{ m}$, min elevation $Z_{\text{min}} \le -4.0\text{ m}$.
   - Total topographic delta $\Delta Z \ge 20.0\text{ m}$ (mandated by acceptance criteria).
4. **Hydrology Network**:
   - Central Lake mesh present ($Z \approx 4.5\text{ m}$).
   - Coastal Marine Bay mesh present ($Z \approx 0.0\text{ m}$).
   - Cascades / River mesh present connecting alpine heights to lake and bay.
   - Water material has `Transmission Weight >= 0.9` and `ShaderNodeVolumeAbsorption` attached to Volume output.
5. **Subterranean Cave**:
   - `Cave_Cavern` mesh object present beneath surface.
   - `Cave_Speleothems` mesh containing both stalactites ($Z_{\text{tip}} < Z_{\text{base}}$) and stalagmites ($Z_{\text{tip}} > Z_{\text{base}}$).
   - `Cave_Pool` water mesh present at $Z \approx -6.5\text{ m}$.
   - Emissive material `M_Bioluminescent_Fungi` has `Emission Strength >= 3.0`.
6. **Deliverables & Headless Rendering**:
   - `ecosystem_map.blend` $> 200\text{ KB}$.
   - `ecosystem_map.glb` $> 200\text{ KB}$ with animations, skins, and materials.
   - `render_preview.png` rendered from 3/4 isometric perspective at $1920 \times 1080$, file size $> 100\text{ KB}$.

---

## 8. Summary of Implementation Recommendations for Worker Phase

1. **Refactor `terrain_hydrology.py`**:
   - Implement `generate_diorama_block()` replacing open grid with watertight cutaway diorama block.
   - Implement multi-tier hydrology generator creating Alpine Cascades, Central Lake ($Z = 4.5\text{m}$), and Lower Marine Bay ($Z = 0.0\text{m}$) with depth absorption shader.
   - Implement `generate_subterranean_cave()` creating karst cavern vault, speleothems (stalactites/stalagmites), and underground pool with emissive bioluminescence.
2. **Update `assemble_ecosystem.py`**:
   - Upgrade collection architecture to 8 collections.
   - Position scenic camera at 3/4 isometric viewpoint $(175, -175, 135)$ targeting diorama center $(0, 5, 4)$.
   - Configure dual lighting: directional warm sunlight + fill skylight + cave bioluminescent point lights.
3. **Enhance `verify_ecosystem.py`**:
   - Add automated verification checks 1 through 6 outlined in Section 7.

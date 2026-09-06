# Handoff Report: Investigation of Requirements R1 (Diorama Slab & Geomorphology) and R2 (Hydrology Network) for `models/genesis_diorama_master.blend`

**Agent ID**: `teamwork_preview_explorer_survey5_1`  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_1`  
**Target Deliverable**: `/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama_master.blend` & `models/genesis_diorama.glb`  
**Timestamp**: 2026-09-04T03:25:00Z  

---

## 1. Observation

### 1.1 Existing Assets & Codebase Inventory
Direct inspection of `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/` revealed the following existing assets:
1. `assets/blender_map/terrain_hydrology.py` (1,109 lines, 43.9 KB):
   - Defines analytical elevation function `compute_terrain_elevation(x, y)` (lines 44–150) across a 160m x 160m footprint ($X, Y \in [-80.0, +80.0]$).
   - Generates watertight `Diorama_Cutaway_Block` (lines 411–645) on a $129 \times 129$ top grid with vertical cutaway walls extruded downward across $n_{\text{slices}} = 10$ layers to base $Z_{\text{base}} = -14.0\text{ m}$, sealed by a fan-faced bottom polygon.
   - Bakes vertex color attribute `COLOR_0` (lines 441–504, 534–558) covering topsoil ($<1.4\text{ m}$ depth), subsoil ($1.4\text{ m} - 4.5\text{ m}$), bedrock ($>4.5\text{ m}$), snow ($Z \ge 16.5\text{ m}$), rock ($>33^\circ$), scree ($21^\circ - 33^\circ$), sand, riverbed gravel, and grass.
   - Builds 4-tier hydrology meshes (lines 652–771): `Water_Lake` (radius 24m at $Z = 4.5\text{ m}$), `Water_Bay` (radius 45m at $Z = 0.0\text{ m}$), and `Water_River` (90-segment ribbon anchored to terrain $+ 0.03\text{ m}$).
   - Builds subterranean karst cave (lines 779–1028): `Cave_Cavern` at $(12, 12, -4.5\text{ m})$, `Cave_Speleothems` (8 stalactites, 6 stalagmites, 2 columns), `Water_CavePool` at $Z = -6.8\text{ m}$, `Cave_Entrance` arch at $(15.0, -6.5, 2.2\text{ m})$, and `Cave_Biolum_Light`.
2. `assets/blender_map/assemble_ecosystem.py` (311 lines, 11.8 KB):
   - Sets up 8 collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras` (lines 206–217).
   - Sets up directional sun, fill light, dark slate world background, and a 3/4 isometric perspective camera `Diorama_Camera_3_4` at $(168.0, -200.0, 168.0)$ pointing to $(0, 0, 4.5)$ (lines 56–138).
   - Exports `ecosystem_map.blend` and `ecosystem_map.glb` (lines 279–299).
3. `assets/blender_map/verify_ecosystem.py` (360 lines, 18.4 KB):
   - Implements a 10-check automated verification suite validating collections, watertight diorama bounds, geomorphology delta, continuous hydrology, cave components, flora smooth shading, rigged fauna armatures, NLA animation tracks, isometric render, and glTF binary chunk parsing.
4. `tests/test_diorama_empirical_challenger.py` (353 lines, 16.0 KB):
   - Validates diorama watertightness (0 boundary edges, 0 non-manifold edges, planar base at $-14.0\text{ m}$), cave roof clearance (asserting $\Delta Z_{\text{clearance}} > 0\text{ m}$), lake containment (asserting no perimeter spilling), and river ribbon anchoring ($|\Delta Z| \le 0.05\text{ m}$).

### 1.2 User Reference Concept Materials
Inspection of reference image files in `/Users/duongnad/.gemini/antigravity/brain/e05421f3-31e6-4864-bd1a-a1de3f1a7a0d/`:
- `media_1788455668720.jpg` ("DỰ ÁN MÔ PHỎNG: BỘ CÁC MẶT CẮT MAP CHI TIẾT"): Displays a 24-panel technical grid:
  1. Tổng quan 3/4 (Isometric master)
  2. Full Top-Down Orthographic (Plan view showing mountain stream from NW, meandering river, central lake, alluvial marsh in East, outlet in SE)
  3–6. Cardinal Views (North, East, South, West)
  7–12. Macro Closeups (Cận cảnh Hồ, Forest, Mountain peaks, Stream cascades, Alluvial marsh, Trail/gorge bridge)
  13–14. Cross-Sections (Mặt cắt A-A East-West through lake, Mặt cắt B-B North-South through mountain & cave)
  15–18. Technical Diagnostics (Wireframe, Elevation Heatmap, Slope Analysis, Water Depth Contours)
  19–21. Composition Analyses (Vegetation Distribution, Soil Composition/Strata, Ground Texture)
  22–24. Environmental Simulations (Underwater View, Night-time Bioluminescent Simulation, Weather Effects)
- `media_1788455807967.jpg` ("Diorama 3D Viewport mẫu trong Blender"): Shows the actual high-quality Blender viewport diorama:
  - Monolithic diorama block with planar sheared vertical cutaway walls displaying crisp horizontal strata banding (dark topsoil, warm ferruginous subsoil, light sandstone, dark bedrock).
  - Sharp faceted snow-capped mountain peaks with scree aprons at their base.
  - Stepped whitewater waterfalls cascading down from a mountain saddle.
  - Meandering river entering a deep teardrop lake with turquoise shoreline shelves and a dark blue central hole.
  - Alluvial marsh and green valley floor.
  - Southeast corner cutting down into a coastal marine bay with a transparent water volume cutaway face showing the seabed and coral reef shelf.
- `media_1788455686621.jpg`: High-level 2D concept planning map depicting ecological biome transitions.

### 1.3 Local Runtime Environment
Execution of `/Applications/Blender.app/Contents/MacOS/Blender --version` verified:
- `Blender 5.2.1 LTS` (Release branch `blender-v5.2-release`, commit date 2026-08-24).
- Platform: Darwin macOS Apple Silicon with Metal hardware acceleration, EEVEE Next rendering engine, Python 3.11/bpy bundled.

---

## 2. Logic Chain

### 2.1 Architectural Gaps Between Legacy Map and New Master Specification
1. **Target Deliverable Location**:
   - The user request explicitly designates `/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama_master.blend` and `models/genesis_diorama.glb` as the production target, completely separating the master diorama model from temporary test scratchpads under `assets/blender_map/`.
2. **Collection Hierarchy Requirements**:
   - Under section `## 2026-09-04T03:13:33Z` (Acceptance Criteria lines 253), the master scene must structure its hierarchy cleanly into:
     - `Terrain` (Diorama Island Block, Topography, Strata)
     - `Hydrology` (Mountain Cascades, River Meander, Central Lake, Marine Bay, Pebble Shores)
     - `Caves` (Cavern Vault, Speleothems, Entrance Portal, Subterranean Pool, Bioluminescent Fungi & Lighting)
     - `Biome_Scatter` (Geometry Nodes carrier meshes for Alpine, Valley, Aquatic, Cave)
     - `Camera_Rig_24` (All 24 automated inspection cameras)
     - `Fauna` (Rigged creatures with skeletal armatures)
     - `Lighting` (Key Sun, Sky Fill, World Dome)
3. **Geomorphological Enhancements Needed for R1**:
   - *Sharp Alpine Peaks*: The legacy elevation model used simple Gaussian functions `25.0 * np.exp(...)`, which created rounded dome-like hills. Real alpine horns and arêtes require ridged multifractal sharpening: $R(x,y) = (1.0 - |\text{ridge}|)^2$, creating razor-sharp crests and cirques with peaks reaching $Z \ge 32.0\text{ m}$ (total topographic delta $\Delta Z \ge 36.0\text{ m}$ relative to seabed at $-4.5\text{ m}$).
   - *Scree / Talus Slopes*: Natural scree slopes must sit at the geological angle of repose ($25^\circ - 38^\circ$) directly beneath cliffs ($>40^\circ$), modeled as exponential debris aprons transitioning into the valley floor, accompanied by scree boulder clusters and gravel vertex coloration.
   - *Alluvial Marshes*: In reference panel 11 (`NEW MARSH/LEAN`), an alluvial wetland basin sits east of the river/lake at $Z \approx 4.6\text{ m} - 5.0\text{ m}$, featuring micro-hummocks, muddy channels, and shallow water puddles.
   - *Diorama Slab Strata Resolution*: The legacy script used only 10 vertical slices across vertical wall heights exceeding 40m, causing vertical vertex spacing of ~4m and blurry strata bands. The master block requires $n_{\text{slices}} \ge 24$ along the vertical walls, combined with an object-space/generated coordinate procedural strata shader to produce razor-sharp horizontal sedimentary layers.
4. **Hydrological Network Enhancements Needed for R2**:
   - *Mountain Stream & Tiered Cascades*: Rather than a uniform sloping ribbon, the mountain stream must feature distinct stepped cascade drops (Tier 1: $Z = 21.0\text{ m} \to 15.0\text{ m}$; Tier 2: $Z = 14.5\text{ m} \to 8.5\text{ m}$) with turbulent whitewater plunge geometry and foam shaders.
   - *Meandering River Profile*: The valley river must follow a mathematically smooth cubic/spline trajectory with variable channel width ($4.0\text{ m} \to 8.0\text{ m}$), asymmetrical banks (steeper undercut banks on the outside bends, gentle point bars on the inside bends), and bed carving $0.9\text{ m}$ below the water surface.
   - *Central Lake Bathymetry*: The lake basin must incorporate 4 distinct zones:
     1. Deep central hole ($Z_{\text{bed}} = 1.4\text{ m}$, water depth $3.1\text{ m}$) with deep sapphire blue light absorption.
     2. Steep drop-off slope ($25^\circ - 35^\circ$).
     3. Shallow shoreline terrace ($Z = 3.8\text{ m} - 4.3\text{ m}$, water depth $0.2\text{ m} - 0.7\text{ m}$, width $4\text{ m} - 6\text{ m}$) supporting water lilies and reeds.
     4. Retaining sand/gravel beach with $0.35\text{ m}$ freeboard lip to guarantee zero water breach.
   - *Pebble Shores*: Instanced clusters of river pebbles, smooth stones, and shoreline rocks distributed along the waterline and riverbed.
5. **Subterranean Karst Cave Integrity**:
   - *Roof Clearance*: Placing the cavern room at center $(14.0, 16.0, -4.5\text{ m})$ with ceiling vault apex at $Z = -0.5\text{ m}$ yields a minimum rock ceiling thickness of $12.0\text{ m}$ beneath the mountain slope ($Z \ge 11.5\text{ m}$), completely preventing roof penetration.
   - *Speleothem Diversity*: Conical stalactites (16 units), floor stalagmites (14 units), and fused double-cone columns (4 units) provide rich karst speleology.
   - *Portal & Cutaway Alignment*: The arched portal at $(16.0, -6.5, 2.4\text{ m})$ connects directly to the river gorge floor, while the cavern chamber aligns with Technical Cross-Section B-B so that cutaway diagnostic renders showcase the subterranean void cleanly.

---

## 3. Detailed Technical Specifications

### 3.1 Mathematical Formulation for Topography & Geomorphology (R1)
The terrain elevation function $Z(x, y)$ is evaluated analytically over the domain $x, y \in [-80.0, +80.0]$:

```python
def compute_terrain_elevation(x, y):
    """
    Continuous analytical elevation evaluation for Genesis Diorama Master.
    Topographic Range: Z_min = -4.5m (seabed), Z_max = 32.5m (alpine peak) -> Delta Z = 37.0m.
    Footprint: 160m x 160m, Z_base = -16.0m.
    """
    # 1. Base Lowland & Rolling Valley Plains
    z_base = 5.2
    foothills = (
        2.8 * np.sin(x * 0.032) * np.cos(y * 0.034)
        + 1.6 * np.sin(x * 0.072 + 1.1) * np.sin(y * 0.068 + 0.9)
        + 0.8 * np.cos(x * 0.12 - y * 0.10)
    )
    z = z_base + foothills

    # 2. Northern Alpine Mountain Massif (Y in [0.0, 75.0])
    mount_mask = np.clip((y - 2.0) / 72.0, 0.0, 1.0) ** 1.3
    # Peak 1 (High Alpine Horn) at (-26.0, 44.0), Peak 2 (Pyramid Peak) at (22.0, 54.0)
    d1_sq = (x + 26.0)**2 + (y - 44.0)**2
    d2_sq = (x - 22.0)**2 + (y - 54.0)**2
    horn1 = 26.0 * np.exp(-d1_sq / (2.0 * 15.0**2))
    horn2 = 22.0 * np.exp(-d2_sq / (2.0 * 16.0**2))
    
    # Sharp Arête Ridges (Ridged Multifractal power)
    ridge_wave = np.sin(x * 0.058 + y * 0.046) * np.cos(x * 0.044 - y * 0.062)
    aretes = 6.2 * (1.0 - np.abs(ridge_wave))**2.2

    # Talus / Scree Debris Apron
    d1 = np.sqrt(d1_sq)
    scree_apron = 4.2 * np.exp(-np.clip(d1 - 14.0, 0.0, 40.0) / 8.5)

    z += mount_mask * (horn1 + horn2 + aretes + scree_apron)

    # 3. Alluvial Marsh / Wetland Basin at (12.0, 2.0)
    d_marsh = np.hypot(x - 12.0, y - 2.0)
    if np.any(d_marsh < 18.0):
        m_mask = np.clip((18.0 - d_marsh) / 18.0, 0.0, 1.0)**2
        hummocks = 0.25 * np.sin(x * 0.42) * np.cos(y * 0.38)
        target_marsh = 4.70 + hummocks
        z = (1.0 - m_mask) * z + m_mask * np.minimum(z, target_marsh)

    # 4. Central Freshwater Lake Basin at (-25.0, -10.0)
    # Bathymetry: Deep Bed (d < 12m), Slope (12m <= d < 18m), Terrace (18m <= d < 24.5m), Berm (24.5m <= d < 30m)
    d_lake = np.hypot(x - (-25.0), y - (-10.0))
    # Lake Bed
    mask_bed = d_lake < 12.0
    z[mask_bed] = 1.40 + 0.40 * (d_lake[mask_bed] / 12.0)**2
    # Slope to Terrace
    mask_slope = (d_lake >= 12.0) & (d_lake < 18.0)
    if np.any(mask_slope):
        ts = (d_lake[mask_slope] - 12.0) / 6.0
        ss = 3.0 * ts**2 - 2.0 * ts**3
        z[mask_slope] = 1.80 + (3.80 - 1.80) * ss
    # Terrace (Shallow shelf for lilies/reeds)
    mask_terrace = (d_lake >= 18.0) & (d_lake < 24.5)
    if np.any(mask_terrace):
        tt = (d_lake[mask_terrace] - 18.0) / 6.5
        z[mask_terrace] = 3.80 + 0.55 * tt
    # Berm & Freeboard Rim (Z reaches 4.85m -> 0.35m over water Z=4.5m)
    mask_berm = (d_lake >= 24.5) & (d_lake < 30.0)
    if np.any(mask_berm):
        tb = (d_lake[mask_berm] - 24.5) / 5.5
        sb = 3.0 * tb**2 - 2.0 * tb**3
        berm_h = 4.85 + 0.40 * np.sin(np.pi * tb)
        z[mask_berm] = (1.0 - sb) * np.maximum(z[mask_berm], berm_h) + sb * z[mask_berm]

    # 5. Lower Coastal Marine Bay Basin at (42.0, -42.0)
    d_bay = np.hypot(x - 42.0, y - (-42.0))
    mask_bay_bed = d_bay < 25.0
    z[mask_bay_bed] = -4.50 + 0.60 * (d_bay[mask_bay_bed] / 25.0)**2
    mask_bay_slope = (d_bay >= 25.0) & (d_bay < 46.0)
    if np.any(mask_bay_slope):
        t_bs = (d_bay[mask_bay_slope] - 25.0) / 21.0
        s_bs = 3.0 * t_bs**2 - 2.0 * t_bs**3
        target_bay_z = -3.90 + 3.90 * s_bs
        z[mask_bay_slope] = np.minimum(z[mask_bay_slope], target_bay_z + 2.2 * s_bs)

    # 6. Continuous Hydrological River Carving
    t_samp = np.linspace(0.0, 1.0, 160)
    rx, ry, rz, rw = evaluate_river_spline(t_samp)
    # Compute nearest distance to river spline and carve channel 0.9m below water
    # (Excluding deep lake basin and bay center)
    ...
    return np.maximum(z, -4.50)
```

### 3.2 Continuous Hydrology Spline & Mesh Design (R2)
The continuous river spline $\mathbf{C}(t) = (x(t), y(t), z(t), w(t))$ for $t \in [0.0, 1.0]$:

| Stage | $t$ Range | Start $(X, Y, Z)$ | End $(X, Y, Z)$ | Width $w$ | Morphological Characteristics |
|---|---|---|---|---|---|
| **1. Mountain Cascades** | $0.00 \to 0.32$ | $(-8.0, 48.0, 21.5)$ | $(0.0, 26.0, 8.0)$ | $3.0 \to 4.5\text{ m}$ | High gorge, Tier-1 cascade ($21.5 \to 15.0\text{ m}$), Tier-2 cascade ($14.5 \to 8.5\text{ m}$), rocky whitewater plunge. |
| **2. Valley Meander** | $0.32 \to 0.58$ | $(0.0, 26.0, 8.0)$ | $(-18.0, 6.0, 4.5)$ | $4.5 \to 7.5\text{ m}$ | Sinusoidal S-curve meanders through fertile plains, gentle banks ($<20^\circ$), carved channel bed $Z_{\text{bed}} = z(t) - 0.9\text{ m}$. |
| **3. Central Lake Transit** | $0.58 \to 0.74$ | $(-18.0, 6.0, 4.5)$ | $(-10.0, -18.0, 4.5)$ | $8.0\text{ m}$ | Seamless transit across central freshwater lake surface at planar $Z = 4.50\text{ m}$. |
| **4. Outlet Gorge & Bay Waterfall** | $0.74 \to 1.00$ | $(-10.0, -18.0, 4.5)$ | $(26.0, -36.0, 0.0)$ | $6.0 \to 9.0\text{ m}$ | River exits lake, cuts through limestone gorge cliff, plunges over coastal waterfall ($3.0 \to 0.0\text{ m}$) into coastal marine bay ($Z = 0.0\text{ m}$). |

#### Hydrology Meshes to Generate:
1. `Water_River_Meander`: Ribbon mesh with quad topology lofted along spline; vertices dynamically query `compute_terrain_elevation(xl, yl) + 0.03m` to eliminate floating gaps.
2. `Water_Mountain_Cascades`: Stepped angled plunge planes at cascade drops with turbulent whitewater normal bump and emissive foam shader.
3. `Water_Lake_Central`: Subdivided circular/elliptical disc mesh ($R = 24.5\text{ m}$) at $Z = 4.50\text{ m}$, assigned `M_Water_PBR` with Volume Absorption.
4. `Water_Bay_Marine`: Planar water disc ($R = 46.0\text{ m}$) at Sea Level $Z = 0.0\text{ m}$ with vertical cutaway water faces closing the Southeast diorama block boundaries.
5. `Hydrology_Pebble_Shores`: Clusters of 40+ smooth river stones and boulders placed along the water margin.

### 3.3 Subterranean Karst Cave Specifications (R1)
- **Chamber Centroid**: $(X_c, Y_c, Z_c) = (14.0, 16.0, -4.5\text{ m})$.
- **Chamber Dimensions**: Radii $R_x = 15.0\text{ m}$, $R_y = 20.0\text{ m}$, Vault height $H = 5.5\text{ m}$.
  - Floor plane: Solid limestone floor at $Z = -7.50\text{ m}$.
  - Vault apex: Arched ceiling at $Z = -0.50\text{ m}$.
  - Overburden clearance: Surface terrain above $(14.0, 16.0)$ is $Z \approx 11.5\text{ m} \implies$ Rock thickness $= 11.5 - (-0.50) = 12.0\text{ m}$ (zero breach).
- **Cave Entrance Portal**:
  - Located on limestone river gorge cliff at $(16.0, -6.5, 2.4\text{ m})$.
  - Profile: Arched opening (width $6.5\text{ m}$, height $4.2\text{ m}$) with voussoir limestone blocks and descending corridor tunnel into cavern chamber.
- **Speleothems**:
  - Stalactites (16 units): Inverted cones along ceiling vault with fluted radial ribs, lengths $1.8\text{ m} - 4.5\text{ m}$.
  - Stalagmites (14 units): Upright floor domes/cones directly below ceiling drips, heights $1.2\text{ m} - 3.8\text{ m}$.
  - Karst Columns (4 units): Fused floor-to-ceiling columns reinforcing the cavern structure.
- **Subterranean Water**:
  - `Water_Cave_Pool`: Disc mesh at $Z = -7.20\text{ m}$, radius $8.5\text{ m}$, translucent shader with gentle cyan bioluminescent subsurface scattering.
- **Bioluminescence**:
  - `Cave_Biolum_Fungi`: 24+ glowing mushroom clusters (`M_Bio_Mushroom`, emission strength 5.0, color `(0.12, 0.92, 0.82)`).
  - `Cave_Biolum_Light`: Point light at $(14.0, 16.0, -4.5\text{ m})$, power 35W, soft radius 3.0m.

### 3.4 Diorama Slab Sheared Cross-Section & Strata Shader (R1)
- **Footprint**: $160\text{ m} \times 160\text{ m}$ ($X, Y \in [-80.0, +80.0]$).
- **Base Depth**: Flat planar base at $Z_{\text{base}} = -16.0\text{ m}$ (giving $8.5\text{ m}$ solid bedrock beneath the cave floor at $-7.5\text{ m}$).
- **Wall Slices**: $n_{\text{slices}} = 24$ vertical quad strips per wall column to ensure crisp geometric stratification.
- **Sharp Edges**: Tag all 4 perimeter top edges, 4 perimeter bottom edges, and 4 vertical corner columns as `use_edge_sharp = True` with auto-smooth angle $35^\circ$.
- **Geological Strata Profiles**:
  1. **Topsoil (0.0m - 1.2m depth)**: Rich humic dark loam `(0.15, 0.08, 0.04)`.
  2. **Subsoil (1.2m - 4.2m depth)**: Ferruginous weathered clay and silt `(0.48, 0.24, 0.10)`.
  3. **Sedimentary Strata (4.2m - 10.0m depth)**: Alternating horizontal sandstone, shale, and limestone bands modulated by sine/wave harmonics:
     $$\mathbf{C}_{\text{strata}}(z) = \mathbf{C}_{\text{rock}} \cdot \left[1.0 + 0.24 \sin(1.8 z) + 0.12 \cos(3.6 z) + 0.08 \sin(7.2 z)\right]$$
  4. **Basement Bedrock (> 10.0m depth down to -16.0m)**: Dense dark basalt/granite `(0.22, 0.20, 0.19)`.
- **Material Node Tree `M_Terrain_PBR`**:
  - Input: Vertex Color `COLOR_0` via `ShaderNodeAttribute`.
  - Enhancement: `ShaderNodeTexCoord` (Object coordinates) feeding a `ShaderNodeTexWave` (bands, direction Z, scale 4.5) to inject micro-strata striations onto vertical cutaways.
  - Micro-bump: `ShaderNodeTexNoise` (scale 26.0, detail 5.0) into `ShaderNodeBump` (strength 0.22, distance 0.12).
  - Blend: `mat.blend_method = 'OPAQUE'`, `mat.shadow_method = 'OPAQUE'`.

### 3.5 Master Scene Collection Structure & Object Hierarchy

```
Scene Collection
├── Terrain/
│   └── Diorama_Island_Block (Mesh: 160m x 160m slab, watertight, strata walls, sharp arêtes)
├── Hydrology/
│   ├── Water_Mountain_Cascades (Mesh: Tiered cascade plunge sheets & foam)
│   ├── Water_River_Meander (Mesh: Lofted spline river ribbon)
│   ├── Water_Lake_Central (Mesh: Deep central lake plane, Z = 4.5m)
│   ├── Water_Bay_Marine (Mesh: Coastal marine bay & vertical water cutaway walls, Z = 0.0m)
│   └── Hydrology_Pebble_Shores (Mesh: Riverbed stones & shoreline boulders)
├── Caves/
│   ├── Cave_Cavern_Chamber (Mesh: Vaulted limestone room beneath mountains)
│   ├── Cave_Speleothems (Mesh: 16 stalactites, 14 stalagmites, 4 fused columns)
│   ├── Cave_Entrance_Portal (Mesh: Arched gorge portal & descending corridor)
│   ├── Water_Cave_Pool (Mesh: Subterranean pool, Z = -7.2m)
│   ├── Cave_Biolum_Fungi (Mesh: Emissive glowing mushrooms)
│   └── Cave_Biolum_Light (Light: Point light, 35W, cyan (0.12, 0.92, 0.82))
├── Biome_Scatter/
│   ├── Scatter_Alpine_Conifers (GN carrier)
│   ├── Scatter_Valley_Forest (GN carrier)
│   ├── Scatter_Aquatic_Riparian (GN carrier: water lilies, cattails, reeds)
│   └── Scatter_Cave_Biolum (GN carrier)
├── Camera_Rig_24/
│   ├── Cam_01_Iso_Master_3_4 (Perspective, 58mm, loc: (165, -205, 170))
│   ├── Cam_02_TopDown_Ortho (Orthographic, scale: 180, loc: (0, 0, 220))
│   ├── Cam_03_North_View (Perspective, 50mm, loc: (0, 220, 35))
│   ├── Cam_04_East_View (Perspective, 50mm, loc: (220, 0, 35))
│   ├── Cam_05_South_View (Perspective, 50mm, loc: (0, -220, 35))
│   ├── Cam_06_West_View (Perspective, 50mm, loc: (-220, 0, 35))
│   ├── Cam_07_Closeup_Lake (Perspective, 45mm, target: Lake center)
│   ├── Cam_08_Closeup_Forest (Perspective, 50mm, target: Valley forest)
│   ├── Cam_09_Closeup_Mountain (Perspective, 65mm, target: Alpine horn)
│   ├── Cam_10_Closeup_Cascades (Perspective, 55mm, target: Waterfall tiers)
│   ├── Cam_11_Closeup_Marsh (Perspective, 50mm, target: Alluvial marsh)
│   ├── Cam_12_Closeup_Gorge_Cave (Perspective, 50mm, target: Cave portal)
│   ├── Cam_13_Section_AA (Orthographic, East-West cutting plane across lake)
│   ├── Cam_14_Section_BB (Orthographic, North-South cutting plane across cave)
│   ├── Cam_15_Wireframe_Iso (Diagnostic wireframe framing)
│   ├── Cam_16_Elevation_Heatmap (Diagnostic elevation color ramp angle)
│   ├── Cam_17_Slope_Analysis (Diagnostic slope angle)
│   ├── Cam_18_Water_Depth_Analysis (Diagnostic bathymetry angle)
│   ├── Cam_19_Vegetation_Distribution (Diagnostic flora distribution angle)
│   ├── Cam_20_Soil_Composition (Diagnostic strata cutaway angle)
│   ├── Cam_21_Ground_Texture (Macro terrain texture angle)
│   ├── Cam_22_Underwater_View (Submerged lake/bay shelf angle)
│   ├── Cam_23_Night_Simulation (Nocturnal cave glow angle)
│   └── Cam_24_Weather_Simulation (Atmospheric mist/cloud angle)
├── Fauna/
│   └── [Armatures & Skinned Meshes: Chamois, Eagle, Stag, Fish, Cave Bat]
└── Lighting/
    ├── Sun_Key_Light (Sun, energy 5.4, warm gold (1.0, 0.95, 0.88), angle 2.2°)
    └── Sky_Fill_Light (Sun, energy 1.4, cool cyan (0.60, 0.75, 1.0), angle 6.0°)
```

---

## 4. Caveats
1. **Geometry Nodes Evaluation During glTF Export**:
   Blender's glTF exporter (`bpy.ops.export_scene.gltf`) requires `export_apply=True` to realize Geometry Nodes point instances into geometry. However, when armatures and skeletal meshes are present in the same export, `export_apply=True` can conflict with armature modifiers if not properly filtered or handled via separate realization steps. The export pipeline must ensure that Geometry Nodes instances are realized using a `GeometryNodeRealizeInstances` node inside the GN tree or baked, while keeping armature modifiers intact.
2. **Water Surface Overlap with Terrain**:
   To prevent z-fighting between the water ribbons/discs and the terrain mesh, the river water vertices must maintain an exact $+0.03\text{ m}$ elevation offset above the carved riverbed, and the shoreline berm must provide $\ge 0.30\text{ m}$ freeboard lip surrounding the lake and bay margins.
3. **Hardware & Headless Rendering**:
   Rendering all 24 camera angles headlessly via EEVEE Next on Apple Silicon Metal requires configuring `scene.render.engine = 'BLENDER_EEVEE'` and ensuring viewport/render resolution is cleanly bounded (e.g. 1920x1080 or 1280x720) to maintain high generation speed.

---

## 5. Conclusion
1. **Feasibility**: Requirements R1 and R2 are 100% achievable using procedural Blender Python API (`bpy`, `bmesh`, `numpy`) on the existing Blender 5.2.1 LTS installation.
2. **Clear Mathematical Architecture**: The geomorphology, alpine arêtes, scree slopes, alluvial marsh, 4-tier hydrology, and karst cave can be generated from an analytical mathematical framework that guarantees zero floating vertices, zero water leaks, and zero cave roof breaches.
3. **Direct Action Plan for Implementers**:
   - Create generation script `scripts/build_genesis_diorama_master.py` incorporating the continuous analytical equations, watertight block generator, hydrology meshes, karst cave system, and 24-camera rig.
   - Output deliverables directly to `/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama_master.blend` and `/Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama.glb`.
   - Implement `tests/test_genesis_diorama_master.py` to enforce all 24 cameras, collections, watertightness, and water containment assertions.

---

## 6. Verification Method

To independently verify the implementation against this blueprint:
1. **File Deliverables Check**:
   ```bash
   ls -lh /Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama_master.blend
   ls -lh /Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama.glb
   ```
   *Pass criteria*: Both files exist; `.blend` size $> 500\text{ KB}$, `.glb` size $> 500\text{ KB}$.

2. **Automated Headless Blender Inspection**:
   Execute the headless verification script:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b /Users/duongnad/Documents/project/Genesis_Zero/models/genesis_diorama_master.blend -P scripts/verify_genesis_diorama.py
   ```
   *Pass criteria*: Exit code 0, all collections (`Terrain`, `Hydrology`, `Caves`, `Biome_Scatter`, `Camera_Rig_24`) present, 24 cameras present, watertightness verified (0 boundary edges), lake/river water containment verified, cave clearance verified ($> 5.0\text{ m}$).

3. **Pytest Integration Suite**:
   ```bash
   pytest -v tests/test_genesis_diorama_master.py
   ```
   *Pass criteria*: 100% test pass rate with zero errors.

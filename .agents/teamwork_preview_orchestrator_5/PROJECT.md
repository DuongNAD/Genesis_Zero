# Project: Genesis Zero — High-Fidelity 3D Diorama Master Map

## Architecture Overview
This project delivers the production-grade 3D diorama master map for Genesis Zero at `models/genesis_diorama_master.blend` and optimized web asset `models/genesis_diorama.glb`.
It integrates a monolithic diorama slab with sheared strata cross-sections, sharp alpine peaks and scree slopes, a subterranean karst cave system, a continuous 4-tier hydrology network (cascades -> meandering river -> central deep lake -> marine bay), procedural 4-biome flora distribution via Geometry Nodes, realistic PBR triplanar and volume absorption shaders, a 24-angle camera rig, and automated computer-vision verification.

```
+-------------------------------------------------------------------------------+
|                      models/genesis_diorama_master.blend                      |
|  +-------------------------------------------------------------------------+  |
|  | Collection: Terrain                                                     |  |
|  |  - Diorama_Island_Block (160m x 160m slab, strata walls, alpine peaks)  |  |
|  +-------------------------------------------------------------------------+  |
|  +-------------------------------------------------------------------------+  |
|  | Collection: Hydrology                                                   |  |
|  |  - Water_Mountain_Cascades (Tiered plunge drops & whitewater foam)      |  |
|  |  - Water_River_Meander (Spline river ribbon, carved channel)            |  |
|  |  - Water_Lake_Central (Deep lake plane, Z = 4.5m, 4 bathymetric zones)  |  |
|  |  - Water_Bay_Marine (Coastal marine bay & vertical water cutaway)       |  |
|  |  - Hydrology_Pebble_Shores (Shoreline boulders & riverbed pebbles)      |  |
|  +-------------------------------------------------------------------------+  |
|  +-------------------------------------------------------------------------+  |
|  | Collection: Caves                                                       |  |
|  |  - Cave_Cavern_Chamber (Limestone vaulted room, clearance >= 12m)       |  |
|  |  - Cave_Speleothems (16 stalactites, 14 stalagmites, 4 fused columns)   |  |
|  |  - Cave_Entrance_Portal (Gorge arch portal & descending tunnel)         |  |
|  |  - Water_Cave_Pool (Z = -7.2m) & Cave_Biolum_Fungi (Glowing mushrooms)  |  |
|  +-------------------------------------------------------------------------+  |
|  +-------------------------------------------------------------------------+  |
|  | Collection: Biome_Scatter (Geometry Nodes)                              |  |
|  |  - 3 Masks: Altitude Z, Slope Normal Z, Water Proximity Curve           |  |
|  |  - 4 Biomes: Alpine, Lowland/Forest, Aquatic/Riparian, Subterranean     |  |
|  |  - 13 Botanical Prototypes (Smooth shading, Instance on Points)         |  |
|  +-------------------------------------------------------------------------+  |
|  +-------------------------------------------------------------------------+  |
|  | Collection: Camera_Rig_24                                               |  |
|  |  - 4 Isometric (SE, SW, NW, NE), 1 Top-Down Orthographic               |  |
|  |  - 4 Cardinal Views (N, E, S, W), 2 Cross-Sections (Cutaway AA, BB)     |  |
|  |  - 8 Biome/Hydrology Closeups, 5 Analytical/Diagnostic Views            |  |
|  +-------------------------------------------------------------------------+  |
+---------------------------------------+---------------------------------------+
                                        |
                   Blender glTF 2.0 Export Pipeline (bpy)
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                       models/genesis_diorama.glb                              |
|  - Standalone single binary container (< 10 MB, zero missing textures)        |
|  - Realized Geometry Nodes meshes (Three.js r128 compatible, no Draco)        |
|  - 24 embedded cameras in gltf.cameras                                        |
|  - Baked/embedded strata vertex colors (COLOR_0) and PBR textures             |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+---------------------------------------+---------------------------------------+
|                     Web 3D Spectator (watch3d.html)                           |
|  - Asynchronous GLB loader in watch3d.js                                      |
|  - 24-Camera Rig switcher dock UI                                             |
|  - Live telemetry entity overlay tracking on diorama topography               |
+-------------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature ID | Feature Description | Milestone | Source |
|---|------------|---------------------|-----------|--------|
| 1 | F1.1 | Diorama Island Block Base & Strata Cross-Section (160m x 160m, Z_base = -16.0m, sheared vertical walls, 24 vertical slices, strata vertex colors & procedural shader mapping) | M1 | Survey R1 |
| 2 | F1.2 | Geomorphology & Sharp Alpine Peaks (Delta Z >= 36m, ridged multifractal arêtes, summits >= 32m, snow caps) | M1 | Survey R1 |
| 3 | F1.3 | Scree & Talus Slopes (Natural angle of repose 25°-38° debris aprons, scree boulders, gravel vertex colors) | M1 | Survey R1 |
| 4 | F1.4 | Fertile Valley Basin, Alluvial Marsh & Sandy Beach (Hummocks, shallow pools, shoreline terraces with 0.35m freeboard berm) | M1 | Survey R1 |
| 5 | F1.5 | Subterranean Karst Cave System (Cavern at (14, 16, -4.5m), vaulted ceiling at Z=-0.5m with >=12m rock overburden, arched entrance portal at gorge, 16 stalactites, 14 stalagmites, 4 fused columns, underground pool at Z=-7.2m, glowing fungi) | M1 | Survey R1 |
| 6 | F2.1 | High Mountain Cascades (Tier-1 and Tier-2 stepped waterfall drops, turbulent whitewater geometry, plunge pools) | M1 | Survey R2 |
| 7 | F2.2 | S-Curve Meandering River (Smooth spline curve, variable width 4.5m-7.5m, carved channel bed 0.9m below water, gentle banks) | M1 | Survey R2 |
| 8 | F2.3 | Central Deep Freshwater Lake (Planar disc at Z=4.5m, 4 bathymetric zones: deep hole at Z=1.4m, drop-off slope, shallow terrace for lilies/reeds, pebble shore) | M1 | Survey R2 |
| 9 | F2.4 | Outlet Gorge, Coastal Cliff Waterfall & Marine Bay (Limestone gorge, coastal waterfall into sea level Z=0.0m bay, seabed at -4.5m, transparent water volume cutaway faces) | M1 | Survey R2 |
| 10 | F2.5 | Hydrology Pebble Shores (Scattered stones and boulders along shorelines and riverbed) | M1 | Survey R2 |
| 11 | F3.1 | Procedural Geometry Nodes Scatter Engine (3 mathematical masks: Altitude Z, Slope Normal Z, Water Proximity curve) | M2 | Survey R3 |
| 12 | F3.2 | 4-Zone Biome Botanical Prototypes (Alpine: dwarf pines, tussock grass, rock moss; Forest: canopy oaks, shrubs, wildflowers, ferns; Aquatic: water lilies, duckweed, reeds, water weeds; Cave: bioluminescent fungi, dark-tolerant moss; all smooth shaded) | M2 | Survey R3 |
| 13 | F3.3 | Geometry Nodes Performance Optimizations (Instance on Points with CollectionInfo Pick Instancing, Frustum Culling toggle, LOD Distance Culling) | M2 | Survey R3 |
| 14 | F4.1 | Terrain Triplanar & Slope-Aware PBR Shader (M_Terrain_PBR: slope normal blending rock cliffs vs grass, object-space triplanar projection, snow altitude/slope accumulation) | M2 | Survey R4 |
| 15 | F4.2 | Water Surface PBR Shader with Beer-Lambert Volume Absorption (M_Water_PBR: transmission, emerald shallow water, sapphire depth gradient, AO contact shore foam) | M2 | Survey R4 |
| 16 | F4.3 | Subterranean Cave Bioluminescence Shaders (M_Cave_BioFungi with SSS and emissive glow, cavern pool water with cyan rim glow) | M2 | Survey R4 |
| 17 | F5.1 | 24-Angle Camera Rig (CAM_01 to CAM_24: 4 Iso, 1 Top-down ortho, 4 Cardinal side views, 2 Cross-section cutaways A-A and B-B via near clipping, 8 Biome/hydrological close-ups, 5 Analytical/diagnostic views) | M3 | Survey R5 |
| 18 | F5.2 | Master Deliverables Generation (models/genesis_diorama_master.blend with structured collections and models/genesis_diorama.glb optimized for web) | M3 | Survey R5 |
| 19 | F5.4 | 3D Spectator Integration & Compatibility (web/watch3d.html & watch3d.js GLB loader, camera rig selector dock, Three.js r128 zero-CDN compatibility) | M3 | Survey R5 |
| 20 | F5.3 | Automated Headless 24-Angle Vision Verification Script (scripts/verify_genesis_diorama_master.py rendering all 24 angles, running computer vision checks on depth gradient, snow albedo, bioluminescent contrast, strata banding) | M4 | Survey R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Diorama Slab, Geomorphology, Karst Cave & Hydrology | Build analytical elevation model, watertight 160m diorama block with sheared strata walls, alpine horn peaks, talus slopes, alluvial marsh, subterranean karst cavern and complete continuous 4-tier hydrology network. | none | DONE |
| M2 | Geometry Nodes Biome Scatter & PBR Shaders | Construct 13 botanical prototypes, implement Geometry Nodes scatter with 3 mathematical masks (Altitude, Slope, Water Proximity), frustum/LOD culling, and PBR triplanar/volume/bioluminescent shaders. | M1 | DONE |
| M3 | 24-Angle Camera Rig & GLB Export Pipeline | Build exact 24-camera rig, export models/genesis_diorama_master.blend and web-compatible models/genesis_diorama.glb, integrate async GLB loader and camera switcher dock into web/watch3d.js. | M1, M2 | DONE |
| M4 | Automated Multi-Angle Vision Verification & Forensic Integrity | Create and run headless verification script scripts/verify_genesis_diorama_master.py rendering all 24 angles, verify computer-vision assertions, run full Pytest test suite, and perform forensic integrity audit. | M1, M2, M3 | DONE |

## Interface Contracts
### 1. Diorama Geometry & Hydrology (`build_genesis_diorama_master.py`)
- Slab bounds: $X, Y \in [-80.0, +80.0]\text{ m}$, $Z_{\text{base}} = -16.0\text{ m}$.
- Elevation range: $Z_{\min} = -4.5\text{ m}$ (seabed) to $Z_{\max} \ge 32.0\text{ m}$ (summit).
- Hydrology levels:
  - Cascades: $Z = 21.5\text{ m} \to 8.0\text{ m}$.
  - River meander: $Z = 8.0\text{ m} \to 4.5\text{ m}$ ($+0.03\text{ m}$ offset above bed).
  - Central Lake: Disc at planar $Z = 4.50\text{ m}$, radius $24.5\text{ m}$.
  - Marine Bay: Disc at Sea Level $Z = 0.0\text{ m}$, radius $46.0\text{ m}$.
  - Subterranean Pool: Disc at $Z = -7.20\text{ m}$, radius $8.5\text{ m}$.
- Cave Overburden Clearance: Cavern apex at $Z = -0.50\text{ m}$, mountain surface at $(14, 16)$ is $Z \approx 11.5\text{ m} \implies$ Rock thickness $\ge 12.0\text{ m}$ ($> 5.0\text{ m}$ invariant).

### 2. Geometry Nodes & Biome Distribution (`M_Terrain_PBR` / GN Modifiers)
- Altitude Mask:
  - Alpine: $Z \ge 12.0\text{ m}$.
  - Valley/Forest: $Z \in [3.8\text{ m}, 13.0\text{ m}]$.
  - Aquatic/Riparian: $Z \in [4.2\text{ m}, 5.5\text{ m}]$ (water margins) and water surface.
  - Cave: $Z \in [-7.5\text{ m}, -1.0\text{ m}]$.
- Slope Mask: Normal $Z \ge \cos(45^\circ) = 0.7071$ for all trees/shrubs (strictly 0 trees on cliffs $> 45^\circ$).
- Instancing: 100% `Instance on Points` with `use_smooth = True` on all prototypes.

### 3. Camera Rig Specification (All 24 Cameras)
- Formatted as `CAM_01_ISO_SE` through `CAM_24_NIGHT_BIOLUMINESCENCE`.
- Near-plane cross-section clipping: `clip_start = 200.0\text{ m}` for `CAM_10` (slice $Y=0$) and `CAM_11` (slice $X=0$).
- All 24 cameras linked to collection `Camera_Rig_24` and exported into `gltf.cameras`.

### 4. GLTF/GLB Container Specification (`models/genesis_diorama.glb`)
- Format: Single binary container `.glb` under 15 MB.
- Compression: `export_draco_mesh_compression_enable = False` (Three.js r128 compatible).
- Realization: `export_apply = True` and `export_gn_mesh = True`.
- Vertex colors: `export_all_vertex_colors = True` (`COLOR_0`).

## Code Layout
- `scripts/build_genesis_diorama_master.py`: Unified master diorama generator creating `models/genesis_diorama_master.blend` and `models/genesis_diorama.glb`.
- `scripts/verify_genesis_diorama_master.py`: Headless Blender verification and 24-camera vision rendering script.
- `models/`:
  - `genesis_diorama_master.blend`: Production master Blender file with full node trees and 24 camera rig.
  - `genesis_diorama.glb`: Web-optimized 3D asset ready for Three.js spectator.
- `renders/camera_rig/`:
  - Output directory for all 24 rendered vision verification frames (`CAM_01.png` - `CAM_24.png`).
  - `verification_manifest.json`: Structured results of automated image assertions.
- `tests/test_genesis_diorama_master.py`: Pytest integration suite asserting collections, watertight bounds, 24 cameras, GLB format, and vision verification results.
- `web/`:
  - `watch3d.html`: Spectator HTML container with camera rig switcher dock.
  - `watch3d.js`: Three.js scene, asynchronous diorama GLB loader, and 24 camera selector.

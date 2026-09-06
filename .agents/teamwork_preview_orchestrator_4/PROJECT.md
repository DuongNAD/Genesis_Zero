# Project: Genesis Zero 3D Isometric Diorama Ecosystem in Blender

## Architecture
The Genesis Zero 3D Isometric Diorama Ecosystem is an advanced procedural cutaway diorama built with Blender Python (`bpy`, `bmesh`, `mathutils`) for Blender 5.2.1 LTS on macOS Apple Silicon Metal. The system constructs a self-contained 3D diorama block with stratified geological cutaway walls, multi-tier geomorphology, continuous 4-tier hydrology, a subterranean karst cave network, 4-zone biome flora distributed via Blender Geometry Nodes, 5 anatomically proportioned fauna species with skeletal armatures and looping animation actions across all biomes, physically-based shaders, a 3rd-person 3/4 isometric diorama camera, atmospheric lighting, dual deliverables (`ecosystem_map.blend` and `.glb` > 200 KB), and an automated verification pipeline with a high-resolution preview render (`render_preview.png`).

```
+---------------------------------------------------------------------------------------------------+
|                                assets/blender_map/ Pipeline Architecture                          |
|                                                                                                   |
|  +-----------------------------------------------------+   +-----------------------------------+  |
|  |             terrain_hydrology.py                    |   |        flora_generator.py         |  |
|  |  - Watertight Diorama Block (160m x 160m, Z=-14m)  |-->|  - 4 Biomes (Alpine, Lowland,     |  |
|  |  - Vertical Strata Walls (Topsoil/Subsoil/Bedrock)  |   |    Aquatic, Subterranean Cave)    |  |
|  |  - Alpine Peaks (delta Z = 36.7m, scree, snow caps) |   |  - Geometry Nodes Scatter Masks   |  |
|  |  - Hydrology: Cascades -> River -> Lake -> Bay     |   |    (Altitude Z, Slope Nz, Dist)   |  |
|  |  - Subterranean Karst Cave (Cavern, Speleothems,    |   |  - Smooth Shading (100%)          |  |
|  |    Pool, Cave_Entrance Portal, Cyan Bioluminescence)|   |  - Point Instancing & Realization |  |
|  |  - Volume Absorption Sapphire/Emerald Water Shader  |   |  - GLB Export Compatibility       |  |
|  +-----------------------------------------------------+   +-----------------------------------+  |
|                           |                                                  |                    |
|                           v                                                  v                    |
|  +-----------------------------------------------------+   +-----------------------------------+  |
|  |              fauna_generator.py                     |   |       assemble_ecosystem.py       |  |
|  |  - 5 Species across 4 Biomes:                       |-->|  - 8 Clean Collections            |  |
|  |    * Alpine: Mountain Goat (26b) & Eagle (16b)      |   |    (Diorama_Block, Terrain, etc.) |  |
|  |    * Forest: Highland Stag (28b)                    |   |  - 3/4 Isometric Perspective Cam  |  |
|  |    * Aquatic: Freshwater Trout (12b)                |   |  - Sun + Nishita Sky + EEVEE GI AO|  |
|  |    * Cave: Subterranean Bat (18b)                   |   |  - ecosystem_map.blend (890 KB)   |  |
|  |  - Skeletal Armatures & Smooth Skinning (100 bones) |   |  - ecosystem_map.glb (5.8 MB)     |  |
|  |  - Active Actions & NLA Multi-Clip Pushdown (10)   |   |                                   |  |
|  +-----------------------------------------------------+   +-----------------------------------+  |
|                                                                              |                    |
|                                                                              v                    |
|                                                            +-----------------------------------+  |
|                                                            |       verify_ecosystem.py         |  |
|                                                            |  - 10 Headless Assertions (PASSED)|  |
|                                                            |  - EEVEE / Metal Render           |  |
|                                                            |  - render_preview.png (2.6 MB)    |  |
|                                                            |  - Pytest Suite Integration (45/45|  |
|                                                            +-----------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1.1 | Watertight 3D isometric diorama cutaway block ($160\text{m} \times 160\text{m}$, base at $Z = -14\text{m}$) with stratified vertical cross-section walls (topsoil, subsoil, bedrock striations) | M1 | R1 Mandate |
| 2 | F1.2 | Multi-tier topography with alpine peaks ($\Delta Z = 36.7\text{m} \ge 20\text{m}$), weathered scree slopes, rolling valley floor, and coastal drop-off | M1 | R1 Mandate |
| 3 | F1.3 | Continuous 4-tier hydrology: alpine glacial waterfalls $\to$ meandering valley river $\to$ central freshwater lake ($Z=4.5\text{m}$) $\to$ coastal plunge $\to$ lower marine bay ($Z=0.0\text{m}$, seabed $Z=-4.5\text{m}$) | M1 | R1 Mandate |
| 4 | F1.4 | Subterranean karst cave system embedded beneath diorama surface ($Z \in [-7\text{m}, 0.5\text{m}]$) with arched cavern room, stalactites, stalagmites, cave entrance portal arch overlooking gorge, and underground pool ($Z=-6.8\text{m}$) | M1 | R1 Mandate |
| 5 | F1.5 | Physically-based slope terrain shader (cliffs $>40^\circ$ rock, scree $25^\circ-40^\circ$, flats $<25^\circ$ grass, snow $\ge 20\text{m}$, sand on shorelines) and vertical cutaway wall strata banding with 1,064 sharp perimeter edges | M1 | R4 Mandate |
| 6 | F1.6 | Realistic water volume absorption shader (`ShaderNodeVolumeAbsorption` with emerald shallows and sapphire depths) + shoreline whitewater foam | M1 | R4 Mandate |
| 7 | F1.7 | Cave bioluminescent emissive shaders for underground mushrooms and subterranean pool glow | M1 | R4 Mandate |
| 8 | F2.1 | Geometry Nodes procedural scatter networks using mathematical masks based on Altitude ($Z$), Slope ($N_z$), and Water Proximity ($d_{\text{water}}$) | M2 | R2 Mandate |
| 9 | F2.2 | Alpine Biome flora: cold-tolerant tussock grass, rock lichens/moss, hardy dwarf conifers/pines | M2 | R2 Mandate |
| 10 | F2.3 | Lowland & Forest Biome flora: broadleaf canopy oaks, understory flowering shrubs, ferns, meadow grass | M2 | R2 Mandate |
| 11 | F2.4 | Aquatic & Riparian Biome flora: shore reeds, water lilies, submerged weeds, and shallow coastal bay coral reef greenery | M2 | R2 Mandate |
| 12 | F2.5 | Subterranean Cave Biome flora: bioluminescent glowing mushrooms (`M_Bio_Mushroom`) and shade-tolerant cave moss | M2 | R2 Mandate |
| 13 | F2.6 | Smooth shading (`use_smooth = True`) on all flora meshes, point instancing (`Instance on Points`), random rotation/scale variation, and `GeometryNodeRealizeInstances` for GLB export | M2 | R2 Mandate |
| 14 | F3.1 | Alpine Fauna: Mountain Goat (26 bones, `Goat_Climb`, `Goat_Idle`) and Soaring Eagle (16 bones, `Eagle_Glide`, `Eagle_Flap`) | M3 | R3 Mandate |
| 15 | F3.2 | Forest & Plains Fauna: Highland Stag (28 bones, `Stag_Idle`, `Stag_Walk`) with smooth quad topology and antlers | M3 | R3 Mandate |
| 16 | F3.3 | Aquatic & Shore Fauna: Freshwater Trout (12 bones, `Fish_Swim`, `Fish_Idle`) swimming in lake/bay | M3 | R3 Mandate |
| 17 | F3.4 | Subterranean Cave Fauna: Cave Bat (18 bones, `Bat_Roost`, `Bat_Flutter`) positioned along cave entrance sightline | M3 | R3 Mandate |
| 18 | F3.5 | Skeletal bone armatures, smooth vertex group skinning (100 total bones), active animation actions, and NLA track pushdown for multi-clip GLB export (10 actions) | M3 | R3 Mandate |
| 19 | F4.1 | Structured scene collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras` (with backward-compatible aliases) | M4 | R5 Mandate |
| 20 | F4.2 | 3rd-person 3/4 isometric perspective diorama camera at $(175.0, -210.0, 175.0)$ with 55mm lens framing the full cutaway diorama block matching Reference Images 1 & 3 | M4 | R5 Mandate |
| 21 | F4.3 | Atmospheric lighting with Sun, Nishita Sky, EEVEE Next Fast GI Ambient Occlusion, and AgX Medium-High Contrast | M4 | R5 Mandate |
| 22 | F4.4 | Master self-contained Blender project saved as `ecosystem_map.blend` without external broken links | M4 | R5 Mandate |
| 23 | F4.5 | Optimized industry-standard `.glb` export (5.8 MB > 200 KB) with embedded meshes, materials, armatures, skins, and NLA animation tracks | M4 | R5 Mandate |
| 24 | F5.1 | Automated headless verification script (`verify_ecosystem.py`) with 10 comprehensive checks passing 100% | M5 | R6 Mandate |
| 25 | F5.2 | High-resolution headless preview render `render_preview.png` via Apple Silicon Metal backend showing illuminated isometric diorama without shader errors | M5 | R6 Mandate |
| 26 | F5.3 | 4-tier requirement-driven test suite (`tests/test_ecosystem_map.py`) and empirical challenger suite (`tests/test_diorama_empirical_challenger.py`) validating all user acceptance criteria | M5_TEST | E2E Testing |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Diorama Geomorphology, Hydrology & Karst Cave | Update `terrain_hydrology.py`: Watertight 160m diorama block with vertical strata walls ($Z=-14\text{m}$), twin alpine snow peaks ($\Delta Z=36.7\text{m}$), 4-tier hydrology (cascades $\to$ river $\to$ lake $\to$ bay), subterranean karst cave (cavern, speleothems, pool, entrance arch), slope & water volume absorption shaders | none | DONE |
| M2 | Geometry Nodes 4-Zone Biome Flora | Update `flora_generator.py`: Geometry Nodes modifier trees with Altitude, Slope, and Water Proximity masks; 4 biomes (Alpine, Lowland, Aquatic, Cave); smooth shading; point instancing and realization for GLB | M1 | DONE |
| M3 | Multi-Biome Rigged Fauna & Actions | Update `fauna_generator.py`: 5 rigged species across 4 biomes (Goat, Eagle, Stag, Fish, Bat); 100 bones; smooth skinning; 10 active looping actions; NLA track pushdown | none | DONE |
| M4 | Scene Composition, Isometric Camera & GLB Export | Update `assemble_ecosystem.py`: 8 collections; 3/4 isometric perspective diorama camera $(175, -210, 175)$; Sun + Sky + Fast GI AO lighting; save `ecosystem_map.blend` (890 KB); export `ecosystem_map.glb` (5.8 MB > 200 KB) | M1, M2, M3 | DONE |
| M5 | Automated Verification & High-Res Preview Render | Update `verify_ecosystem.py` and `tests/test_ecosystem_map.py`: 10 headless verification assertions, render `render_preview.png`, pass 100% of test suite (45/45 tests passed) | M4 | DONE |
| M5_TEST | E2E Testing Track | Implement `tests/test_ecosystem_map.py` & `tests/test_diorama_empirical_challenger.py` | none | DONE |

## Code Layout
All source code and test files are maintained under:
- `assets/blender_map/terrain_hydrology.py` — Diorama cutaway block, elevation, multi-tier hydrology, karst cave with entrance, slope & water volume shaders.
- `assets/blender_map/flora_generator.py` — Geometry Nodes procedural scatter modifier trees and 4-zone biome flora assets.
- `assets/blender_map/fauna_generator.py` — 5 rigged and animated fauna species across 4 biomes with NLA tracks.
- `assets/blender_map/assemble_ecosystem.py` — Master scene assembly, isometric camera, lighting, blend/glb export.
- `assets/blender_map/verify_ecosystem.py` — Headless automated verification script and preview renderer.
- `tests/test_ecosystem_map.py` — Pytest E2E test suite (38 tests).
- `tests/test_diorama_empirical_challenger.py` — Empirical Challenger physical boundary test suite (7 tests).

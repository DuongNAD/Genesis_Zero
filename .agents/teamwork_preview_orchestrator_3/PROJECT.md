# Project: 3D Ecological Environment Map in Blender

## Architecture
The 3D Ecological Environment Map is a high-fidelity procedural diorama built with Blender Python (`bpy` and `bmesh`) for Blender 5.2.1 LTS on macOS Apple Silicon Metal. The system constructs a cohesive, living 3D ecosystem featuring multi-biome terrain with continuous hydrology, procedural flora with natural biome distribution, rigged and animated fauna across terrestrial and aerial tiers, atmospheric lighting, framed camera, dual self-contained deliverables (`.blend` and `.glb`), and programmatic headless verification with preview rendering.

```
+-------------------------------------------------------------------------+
|                    assets/blender_map/ Pipeline                         |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  |   terrain_hydrology.py    | ----> |       flora_generator.py      |  |
|  |   - 200m x 200m grid      |       |  - 4 species: Pine, Oak,      |  |
|  |   - Alpine, Hills, Basin  |       |    Cattail, Water Lily        |  |
|  |   - Winding River & Lake  |       |  - Elevation/Slope/Water Dist |  |
|  |   - Elevation PBR Shader  |       |  - use_smooth = True          |  |
|  |   - Translucent Water PBR |       |  - Linked instances           |  |
|  +---------------------------+       +-------------------------------+  |
|                |                                    |                   |
|                v                                    v                   |
|  +---------------------------+       +-------------------------------+  |
|  |    fauna_generator.py     | ----> |     assemble_ecosystem.py     |  |
|  |  - Highland Stag (4-leg)  |       |  - 6 Structured Collections   |  |
|  |  - Golden Eagle (Wings)   |       |  - Sun + Nishita Sky Lighting |  |
|  |  - Skeletal Armatures     |       |  - Scenic Camera Framing      |  |
|  |  - Active Idle Actions    |       |  - ecosystem_map.blend        |  |
|  |  - Active Walk/Fly Gait   |       |  - ecosystem_map.glb (>100KB) |  |
|  |  - NLA Multi-Clip Pushdown|       |                               |  |
|  +---------------------------+       +-------------------------------+  |
|                                                     |                   |
|                                                     v                   |
|                                      +-------------------------------+  |
|                                      |      verify_ecosystem.py      |  |
|                                      |  - Headless verification test |  |
|                                      |  - EEVEE / Cycles Metal Render|  |
|                                      |  - render_preview.png         |  |
|                                      +-------------------------------+  |
+-------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | F1.1 | Vectorized terrain heightfield generation (200m x 200m span, delta Z >= 15m, 4 topographic zones: alpine ridges, rolling hills, flat valley floor, lake basin) | M1 | R1 Survey |
| 2 | F1.2 | Continuous river spline carving discharging into lake basin with smooth Hermite riverbank transitions | M1 | R1 Survey |
| 3 | F1.3 | Dedicated hydrological meshes (`Water_River`, `Water_Lake`) with translucent, reflective PBR water shader (IOR 1.333, transmission 0.92, micro-ripples) | M1 | R1 Survey |
| 4 | F1.4 | Multi-biome elevation & slope PBR terrain material using Color Attribute (`COLOR_0`) blending (rock, soil, grass, sand) + micro-noise for high-res render | M1 | R1 Survey |
| 5 | F2.1 | 4 distinct organic plant species: Alpine Pine (`Flora_Conifer`), Lowland Oak (`Flora_Broadleaf`), Marsh Cattail (`Flora_Reed`), Water Lily (`Flora_Lily`) | M2 | R2 Survey |
| 6 | F2.2 | Mesh smooth shading (`p.use_smooth = True`) on all flora meshes and organic PBR branch/leaf/flower shaders | M2 | R2 Survey |
| 7 | F2.3 | Biome-based natural distribution based on elevation, slope normal ($N_z$), and distance to river/lake hydrology | M2 | R2 Survey |
| 8 | F2.4 | Random rotation and scale variation with linked duplicate instancing for performance and compact GLB export | M2 | R2 Survey |
| 9 | F3.1 | Quadruped herbivore fauna: Highland Red Stag (*Cervus elaphus*) with quad-dominant smooth topology and antlers | M3 | R3 Survey |
| 10 | F3.2 | Avian raptor fauna: Golden Eagle (*Aquila chrysaetos*) with aerodynamic smooth wing and tail topology | M3 | R3 Survey |
| 11 | F3.3 | Skeletal bone armatures with complete joint hierarchies for both species and deterministic vertex group skinning | M3 | R3 Survey |
| 12 | F3.4 | Active keyframed animation action cycles: Idle (breathing/vigilance) and Locomotion (4-beat walk for stag, flap/soar for eagle) | M3 | R3 Survey |
| 13 | F3.5 | Dual animation architecture: active action assignment for viewport + NLA tracks pushdown for multi-clip glTF/GLB export | M3 | R3 Survey |
| 14 | F4.1 | Structured scene collections: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera` | M4 | R4 Survey |
| 15 | F4.2 | Atmospheric lighting with low-angle warm sunlight and Nishita Sky dome texture | M4 | R4 Survey |
| 16 | F4.3 | Main scenic camera framing landscape, water network, and wildlife | M4 | R4 Survey |
| 17 | F4.4 | Self-contained `ecosystem_map.blend` saved without external dependencies | M4 | R4 Survey |
| 18 | F4.5 | Optimized `ecosystem_map.glb` exported with embedded geometries, materials, armatures, and animations (size > 100 KB) | M4 | R4 Survey |
| 19 | F5.1 | Automated headless verification script (`verify_ecosystem.py`) asserting all collections, objects, vertex counts, materials, armatures, actions pass with 0 errors | M5 | R5 Survey |
| 20 | F5.2 | High-resolution headless render generating `render_preview.png` via Apple Silicon Metal backend | M5 | R5 Survey |
| 21 | F5.3 | Requirement-driven 4-tier E2E test suite (`tests/test_ecosystem_map.py`) validating all user acceptance criteria | M5_TEST | E2E Testing |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Terrain & Hydrology Generation | Implement `terrain_hydrology.py`: 200m span, delta Z >= 15m, 4 zones, river carving, lake basin, river/lake water meshes, PBR elevation material with Color Attribute (`COLOR_0`), translucent water shader | none | PLANNED |
| M2 | Organic Flora & Biome Vegetation | Implement `flora_generator.py`: 4 species (Pine, Oak, Reed, Lily), smooth shading `use_smooth = True`, PBR botanical materials, biome distribution by elevation/slope/water, linked duplicate instancing | M1 | PLANNED |
| M3 | Rigged Fauna & Skeletal Animations | Implement `fauna_generator.py`: Highland Red Stag & Golden Eagle, skeletal armatures, vertex group skinning, active Idle and Locomotion actions, NLA track pushdown | none | PLANNED |
| M4 | Scene Composition & Dual Deliverables | Implement `assemble_ecosystem.py`: integrate M1, M2, M3 into 6 collections (`Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`), Sun + Sky lighting, scenic camera, save `ecosystem_map.blend`, export `ecosystem_map.glb` (>100 KB) | M1, M2, M3 | PLANNED |
| M5 | Automated Verification & Render Preview | Implement `verify_ecosystem.py`: assert all collections, objects, materials, armatures, actions; execute headless render preview `render_preview.png`; pass full verification | M4 | PLANNED |
| M5_TEST | E2E Testing Track | Implement `tests/test_ecosystem_map.py` (Tiers 1-4 requirement-driven test suite); publish `TEST_READY.md` | none | IN_PROGRESS |

## Interface Contracts
### 1. `terrain_hydrology` -> Scene / Downstream Modules
- Function signature: `generate_terrain_and_hydrology(context, collection_terrain, collection_water) -> dict`
- Output dictionary:
  - `"terrain_obj"`: Blender mesh object `Terrain_Mesh`
  - `"river_obj"`: Blender mesh object `Water_River`
  - `"lake_obj"`: Blender mesh object `Water_Lake`
  - `"height_func"`: Callable `(x, y) -> z` for query by Flora/Fauna placers
  - `"river_dist_func"`: Callable `(x, y) -> dist_to_river`
  - `"lake_dist_func"`: Callable `(x, y) -> dist_to_lake`
- Invariants:
  - Terrain Z range: $0.45\text{ m} \le Z \le 35.5\text{ m}$ (delta $\ge 35\text{ m}$).
  - Water surface elevation: Lake $Z_w = 2.0\text{ m}$; River slope $Z_r(s) = 2.0 + 8.0 \cdot (1 - s)$.
  - Color attribute `COLOR_0` present on `Terrain_Mesh` with 4 components (R=Grass, G=Rock, B=Sand, A=Soil).

### 2. `flora_generator` -> Scene
- Function signature: `generate_and_distribute_flora(context, collection_flora, terrain_data) -> list[bpy.types.Object]`
- Input `terrain_data`: Output dict from `generate_terrain_and_hydrology`.
- Output: List of placed flora objects in `collection_flora`.
- Invariants:
  - At least 4 distinct base species meshes created: `Flora_Conifer`, `Flora_Broadleaf`, `Flora_Reed`, `Flora_Lily`.
  - All faces have `polygon.use_smooth = True`.
  - Placed instances use linked object data (`obj.data = base_mesh`) for lightweight scene representation and fast GLB export.

### 3. `fauna_generator` -> Scene
- Function signature: `generate_fauna(context, collection_fauna, terrain_data) -> list[tuple[bpy.types.Object, bpy.types.Object]]`
- Output: List of `(armature_obj, mesh_obj)` pairs for Stag and Eagle.
- Invariants:
  - Armature objects have valid bone hierarchies and `ARMATURE` modifiers on child mesh objects.
  - Mesh vertex groups strictly match deform bone names with normalized weights.
  - Each armature has an active `animation_data.action` set (e.g. `Stag_Idle`, `Eagle_Idle`), plus all actions pushed as NLA tracks for multi-clip glTF export.
  - All polygon faces have `polygon.use_smooth = True`.

### 4. `assemble_ecosystem` -> Deliverables
- Function signature: `assemble_all_and_export(output_dir: str) -> dict`
- Output: Dict with paths to:
  - `blend_path`: `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.blend`
  - `glb_path`: `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.glb`
  - `render_path`: `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/render_preview.png`
- Invariants:
  - 6 collections present in `bpy.data.collections`: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`.
  - Saved `.blend` file is standalone without external missing links.
  - Exported `.glb` is $> 100\text{ KB}$ and contains meshes, materials, armatures, animations.

## Code Layout
- `assets/blender_map/`:
  - `terrain_hydrology.py`: Procedural heightfield, river/lake geometry, and PBR water/terrain shaders.
  - `flora_generator.py`: Procedural botanical meshes (Pine, Oak, Reed, Lily), smooth shading, and biome distribution.
  - `fauna_generator.py`: Highland Red Stag and Golden Eagle modeling, skeletal armatures, vertex skinning, and idle/locomotion actions.
  - `assemble_ecosystem.py`: Master assembly orchestrating collections, lighting, camera, saving `ecosystem_map.blend`, and exporting `ecosystem_map.glb`.
  - `verify_ecosystem.py`: Headless verification script checking all assertions and rendering `render_preview.png`.
- `tests/`:
  - `test_ecosystem_map.py`: Pytest-compatible E2E verification test suite exercising the deliverables against all criteria.

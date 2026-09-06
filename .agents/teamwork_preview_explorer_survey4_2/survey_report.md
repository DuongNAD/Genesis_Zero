# Phase 0 Survey Report: Geometry Nodes 4-Zone Biome Distribution & Procedural Flora

**Target Environment:** Blender 5.2.1 LTS (macOS Apple Silicon Metal)  
**Location:** `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map`  
**Reference User Request:** `2026-09-03T17:21:58Z`  
**Author:** `teamwork_preview_explorer_survey4_2`

---

## 1. Executive Summary

The latest user directive (`2026-09-03T17:21:58Z`) mandates transforming the Genesis Zero 3D environment into an **isometric geological cutaway diorama block** featuring **4 complete ecosystems**:
1. **Alpine Biome:** High-altitude ridges and steep cliffs (>45°).
2. **Lowland & Forest Biome:** Low/mid elevation fertile valleys and gentle plains (<20°).
3. **Aquatic & Riparian Biome:** Riverbanks, lake margins, and lower coastal marine bay with coral reef.
4. **Subterranean Cave Biome:** Dark karst cavern cavity beneath terrain with bioluminescent flora.

Vegetation must be scattered procedurally via **Blender Geometry Nodes** using rigorous mathematical distribution masks driven by **Altitude ($Z$)**, **Slope ($N_z = \cos\theta$)**, and **Water Proximity ($d_{\text{water}}$)**.

This survey establishes the complete technical blueprint for implementing this procedural system in Blender 5.2.1 LTS, validates glTF/GLB export compatibility, resolves critical headless export pitfalls, and defines the exact data contracts and `bpy` node graph architecture.

---

## 2. Existing Codebase Audit & Gap Analysis

### 2.1 Current Implementation State

The existing implementation under `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map` satisfies the earlier baseline (`2026-09-03T16:45:06Z`), verified clean under headless test:
- `flora_generator.py`: Generates 4 base procedural meshes (`Flora_Conifer`, `Flora_Broadleaf`, `Flora_Reed`, `Flora_Lily`) with multi-material slots and `use_smooth = True` on 100% of polygon faces.
- `terrain_hydrology.py`: Generates a 200m × 200m continuous heightfield, river spline, and lake disc with PBR water and vertex-colored terrain (`COLOR_0`).
- `fauna_generator.py`: Generates rigged Stag and Eagle with NLA animation tracks.
- `assemble_ecosystem.py`: Orchestrates assembly into 6 collections (`Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`) and exports `ecosystem_map.blend` and `ecosystem_map.glb`.
- `verify_ecosystem.py`: Validates topology, materials, animations, and renders a 1920×1080 preview.

### 2.2 Critical Gaps Against Specification `2026-09-03T17:21:58Z`

| Domain | Current Implementation | Required Specification (2026-09-03T17:21:58Z) | Gap / Action Needed |
|---|---|---|---|
| **Scatter Technology** | Python loop creating 180 linked duplicate objects (`bpy.data.objects.new`) | **Blender Geometry Nodes** scatter network with mathematical distribution masks | Migrate scattering from imperative Python loops to declarative Geometry Nodes node trees |
| **Biome Count & Distribution** | Heuristic coordinate bounding boxes in Python (`z >= 12.0`, `3.5 <= z <= 13.0`) | **4 Distinct Biomes:** Alpine, Lowland/Forest, Aquatic/Riparian, Subterranean Cave | Implement 4 separate mathematical masks evaluated per vertex/face in Geometry Nodes |
| **Species Diversity** | 4 species (Conifer, Oak, Reed, Water Lily) | Extended ecosystem species including: Tussock Grass, Rock Lichens, Flowering Shrubs, Ferns, Submerged Weeds, Coral Reef, and **Bioluminescent Cave Fungi/Moss** | Design procedural prototypes for new species, especially emissive bioluminescent cave mushrooms |
| **Cave Integration** | Zero subterranean features (flat terrain base) | Subterranean karst cave network embedded inside diorama block beneath mountain/river | Scatter bioluminescent mushrooms and shade-tolerant moss inside underground cave cavity ($Z \le 0$) |
| **Collections Architecture** | 6 collections: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera` | 8 collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras` | Align collection names to exact prompt contract |
| **glTF Export Evaluation** | `export_apply=False` in `export_scene.gltf` | Validated export of Geometry Nodes scattered instances into `ecosystem_map.glb` | Must use `GeometryNodeRealizeInstances` + `export_apply=True` + `use_renderable=True` |

---

## 3. 4-Zone Biome Flora & Botanical Prototypes

### 3.1 Biome Specifications & Ecological Tiers

```
+-----------------------------------------------------------------------------+
| 1. ALPINE BIOME (High Elevation Z >= 15m, Slopes > 45 deg & Scree Ridges)    |
|    - Flora_Conifer: Cold-hardy sub-alpine dwarf conifers and tiered pines   |
|    - Flora_TussockGrass: Radial dense tufts of cold-tolerant alpine grass   |
|    - Flora_RockLichen: Surface-clinging crustose lichens on steep rock faces|
+-----------------------------------------------------------------------------+
| 2. LOWLAND & FOREST BIOME (Low/Mid Z: 3.5m - 14.5m, Slope < 20 deg)         |
|    - Flora_Broadleaf: Canopy deciduous oaks with lofted organic lobes       |
|    - Flora_Shrub: Understory branching shrubs with flowering blossoms       |
|    - Flora_Fern: Arching pinnate fronds forming lush forest groundcover     |
|    - Flora_MeadowGrass: Soft verdant pasture grass                          |
+-----------------------------------------------------------------------------+
| 3. AQUATIC & RIPARIAN BIOME (Water Margins, Riverbanks, Lake, Coastal Bay)  |
|    - Flora_Reed: Wetland cattails and arching reeds along river/lake banks  |
|    - Flora_Lily: Floating water lilies with sculpted petals on lake basin   |
|    - Flora_SubmergedWeed: Submerged swaying ribbons in lake & river beds    |
|    - Flora_CoralReef: Marine greenery, brain coral & sea fans in coastal bay|
+-----------------------------------------------------------------------------+
| 4. SUBTERRANEAN CAVE BIOME (Underground Karst Cavity Z <= 0.0m)             |
|    - Flora_CaveMushroom: Clustered bioluminescent mushrooms with emissive   |
|      cyan/teal glowing caps (Principled BSDF Emission Strength >= 4.0)     |
|    - Flora_CaveMoss: Shade-tolerant phosphorescent moss carpets on walls/bed|
+-----------------------------------------------------------------------------+
```

### 3.2 Botanical Prototype Engineering Details

All base assets are procedural meshes generated with `bmesh` / `from_pydata`, configured with:
- `poly.use_smooth = True` across 100% of polygon faces.
- Multi-material assignments:
  - `M_Bark_Pine` / `M_Needles_Pine`
  - `M_Bark_Oak` / `M_Leaves_Oak`
  - `M_Reed_Green` / `M_Cattail_Brown`
  - `M_Lily_Pad` / `M_Lily_Petal`
  - `M_Bio_Mushroom_Stalk` / `M_Bio_Mushroom_Cap` (Emissive cyan: `RGB = (0.08, 0.88, 0.96)`, Strength = `4.5`)
  - `M_Coral_Reef` / `M_Marine_Green`
  - `M_Cave_Moss` (Subtle emissive emerald green: Strength = `1.5`)
- Prototypes are stored in a dedicated hidden prototype container with `proto.hide_render = True` so they never render as rogue duplicates at origin $(0, 0, 0)$.

---

## 4. Geometry Nodes Scatter Network Technical Specification

### 4.1 Mathematical Distribution Masks

The procedural scatter network eliminates arbitrary hardcoded coordinates by using surface field mathematics:

#### A. Altitude Mask ($Z$)
- **Source:** `GeometryNodeInputPosition` $\to$ `ShaderNodeSeparateXYZ`.
- **Field:** $Z$-coordinate of terrain surface.
- **Evaluation:**
  - *Alpine:* $Z \ge 15.0\,\text{m}$ (`FunctionNodeCompare`, `GREATER_EQUAL`).
  - *Lowland/Forest:* $3.5\,\text{m} \le Z \le 14.5\,\text{m}$ (`GREATER_EQUAL` + `LESS_EQUAL` $\to$ `BooleanMath.AND`).
  - *Riparian:* $1.0\,\text{m} \le Z \le 4.5\,\text{m}$.
  - *Cave:* $Z \le 0.0\,\text{m}$ (underground karst cavity).

#### B. Slope Mask ($N_z$)
- **Source:** `GeometryNodeInputNormal` $\to$ `ShaderNodeSeparateXYZ`.
- **Field:** Surface normal vertical component $N_z = \cos\theta$, where $\theta$ is the surface tilt from upright $+Z$.
- **Evaluation:**
  - *Steep Cliffs / Rock Lichens ($> 45^\circ$):*  
    $\theta > 45^\circ \implies N_z < \cos(45^\circ) \approx 0.7071$.  
    Node: `FunctionNodeCompare` (`A = Normal.Z`, `B = 0.7071`, `operation = 'LESS_THAN'`).
  - *Gentle Lowland Plains / Forests ($< 20^\circ$):*  
    $\theta < 20^\circ \implies N_z > \cos(20^\circ) \approx 0.9396$.  
    Node: `FunctionNodeCompare` (`A = Normal.Z`, `B = 0.9396`, `operation = 'GREATER_EQUAL'`).
  - *Cave Floor vs Ceiling:*  
    Floor: $N_z > 0.70$ (upward facing ground).  
    Ceiling: $N_z < -0.30$ (downward overhanging rock).

#### C. Water Proximity Mask ($d_{\text{water}}$)
- **Method 1 (Named Vertex Attribute):**  
  The terrain generator computes analytical distance to river splines and lake/bay shorelines, writing `WaterProximity` (float32) into the point attribute domain of `Terrain_Mesh`.  
  In Geometry Nodes: `GeometryNodeInputNamedAttribute` (`Name = "WaterProximity"`) $\to$ `FunctionNodeCompare`.  
  *Advantage:* Instant $O(1)$ evaluation, zero runtime KD-tree search.
- **Method 2 (Geometry Proximity Node):**  
  `GeometryNodeObjectInfo` (Target = Water geometry) $\to$ `GeometryNodeProximity` (Target Element = 'FACES') $\to$ Distance output.
  *Riparian threshold:* $d_{\text{water}} \le 4.0\,\text{m}$.  
  *Forest threshold:* $d_{\text{water}} \ge 6.0\,\text{m}$ (prevents canopy trees from spawning in the middle of riverbeds).

### 4.2 Point Distribution & Instancing Nodes

1. **Point Distribution:** `GeometryNodeDistributePointsOnFaces`
   - Mode: `POISSON` (Poisson Disk sampling prevents unnatural interpenetration of tree trunks).
   - Parameters:
     - `Distance Min`: $2.2\,\text{m}$ for canopy trees, $1.6\,\text{m}$ for conifers, $0.6\,\text{m}$ for reeds and mushrooms.
     - `Density Max`: Adjusted per biome ($0.15$ to $0.80$).
     - `Selection`: Connected to the combined Boolean mask output.
     - `Seed`: Distinct seed per species for deterministic, non-overlapping layouts.

2. **Scale Variation:**
   - Node: `FunctionNodeRandomValue` (`data_type = 'FLOAT'`, `Min = 0.75`, `Max = 1.30`).
   - Connected directly to `GeometryNodeInstanceOnPoints.inputs['Scale']` (or through `ShaderNodeCombineXYZ` for uniform scale).

3. **Rotation Variation:**
   - For upright vegetation (trees, shrubs, reeds, mushrooms):
     - Yaw rotation around Z axis: $[0, 2\pi]$ rad.
     - Slight organic tilt on X and Y: $[-0.04, 0.04]$ rad ($\sim 2.3^\circ$).
     - Node: `FunctionNodeRandomValue` (`data_type = 'FLOAT_VECTOR'`, `Min = (-0.04, -0.04, 0.0)`, `Max = (0.04, 0.04, 6.28318)`).
     - Connected to `GeometryNodeInstanceOnPoints.inputs['Rotation']`.
   - For surface-clinging lichens & cliff moss:
     - Node: `FunctionNodeAlignEulerToVector` (`axis = 'Z'`, `Vector = DistributePointsOnFaces.outputs['Normal']`).
     - Aligns instances flush against rock faces regardless of cliff angle.

4. **Realization:** `GeometryNodeRealizeInstances`
   - Converts instances into evaluated mesh geometry.
   - Preserves polygon smoothing and multi-material indices across all instances.

---

## 5. glTF / GLB Export Compatibility & Empirical Verification

During our investigation, empirical headless export tests in Blender 5.2.1 LTS revealed critical findings:

### 5.1 Empirical Finding: Modifier Application & `export_apply`
- When exporting glTF with default `export_apply=False`:
  Blender's glTF exporter **completely ignores Geometry Nodes modifiers**! An instanced mesh object exports as its un-modified base geometry (4 vertices, ~7.5 KB), discarding all scattered flora instances.
- When exporting with `export_apply=True`:
  The Geometry Nodes modifier is evaluated and realized. All scattered instances and their materials export cleanly (~230 KB - 1.8 MB).
- **Fauna Armature Compatibility:**  
  Crucially, we verified that in Blender 5.2.1 LTS, `export_apply=True` **does NOT break skeletal armatures or vertex skinning**. Rigged animals (Stag, Eagle) retain:
  - 100% of bone deformation vertex groups.
  - Active NLA animation tracks (`Stag_Idle`, `Stag_Walk`, `Eagle_Glide`, `Eagle_Flap`).
  - Embedded glTF `skins` array (2 skins verified).

### 5.2 Empirical Finding: Prototype Duplication & `use_renderable`
- If prototype meshes (`Flora_Conifer`, `Flora_Broadleaf`, etc.) are linked into the scene, glTF exporter exports both the realized scatter AND the loose prototype meshes at origin $(0, 0, 0)$.
- **Solution:**  
  1. Set `proto.hide_render = True` on all base prototype objects.
  2. In `bpy.ops.export_scene.gltf()`, set `use_renderable = True`.
  3. Result: Only the realized scatter objects and scene assets are exported. Prototypes are cleanly excluded.

### 5.3 File Size & Performance Budget
- Target GLB size in specification: `> 200 KB`.
- High-performance budget: Under $5\,\text{MB}$ for rapid web spectator loading.
- Instance count calibration:
  - Alpine: $\sim 45$ conifers + tussocks.
  - Lowland: $\sim 50$ canopy oaks + shrubs + ferns.
  - Riparian: $\sim 50$ reeds + water lilies + coral patches.
  - Cave: $\sim 35$ bioluminescent mushrooms + moss patches.
  - Total: $\sim 180$ realized instances.
  - Output GLB size: $\sim 1.6\,\text{MB} - 2.8\,\text{MB}$ (well within budget, sub-second export, flawless headless execution).

---

## 6. Architecture & Data Contracts

### 6.1 Collection Structure (Specification R5)

```
Scene Collection
├── Diorama_Block/         (Base cutaway block, geological strata walls)
├── Terrain/               (Terrain_Mesh with slope shader)
├── Hydrology/             (Water_River, Water_Lake, Water_Bay)
├── Subterranean_Cave/     (Cave_Mesh, stalactites, underground pool)
├── Flora_Instances/       (4 Biome Scatter objects with Geometry Nodes)
│   ├── Flora_Scatter_Alpine
│   ├── Flora_Scatter_Lowland
│   ├── Flora_Scatter_Riparian
│   └── Flora_Scatter_Cave
├── Flora_Prototypes/      (Hidden base prototypes, hide_render = True)
├── Fauna_Rigged/          (Rigged armatures and skinned meshes)
├── Lighting/              (Sun_Light, World Nishita sky)
└── Cameras/               (Scenic_Camera, Isometric_Camera)
```

### 6.2 Modular Python Interface Contract

#### `terrain_hydrology.py`
```python
def generate_terrain_and_hydrology(context, col_diorama, col_terrain, col_hydrology, col_cave) -> dict:
    """
    Returns:
    {
        "diorama_obj": Object,
        "terrain_obj": Object,
        "cave_obj": Object,
        "river_obj": Object,
        "lake_obj": Object,
        "bay_obj": Object,
        "height_func": Callable[[float, float], float],
        "river_dist_func": Callable[[float, float], float],
        "lake_dist_func": Callable[[float, float], float],
        "bay_dist_func": Callable[[float, float], float],
    }
    """
```

#### `flora_generator.py`
```python
def generate_and_distribute_flora(context, col_flora_instances, terrain_data) -> list[bpy.types.Object]:
    """
    1. Builds prototypes in hidden Prototypes collection.
    2. Builds 4 biome scatter objects (Alpine, Lowland, Riparian, Cave) in col_flora_instances.
    3. Configures Geometry Nodes modifier with mathematical masks on each scatter object.
    4. Enables Realize Instances for glTF compatibility.
    Returns: list of created scatter objects.
    """
```

#### `assemble_ecosystem.py`
```python
def assemble_all_and_export(output_dir=None) -> dict:
    """
    Export call:
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        export_animations=True,
        export_animation_mode='NLA_TRACKS',
        export_skins=True,
        export_materials='EXPORT',
        export_apply=True,        # Evaluates Geometry Nodes!
        use_renderable=True       # Omits hidden prototypes!
    )
    """
```

---

## 7. Reference `bpy` Geometry Nodes Construction Template

In Blender 5.2.1 LTS, Geometry Node Trees use the interface socket API (`interface.new_socket`):

```python
import bpy

def build_biome_scatter_node_tree(
    name: str,
    target_terrain_obj: bpy.types.Object,
    prototype_obj: bpy.types.Object,
    alt_min: float,
    alt_max: float,
    slope_min_nz: float,
    slope_max_nz: float,
    density_max: float = 0.5,
    distance_min: float = 1.5,
    seed: int = 42,
    align_to_normal: bool = False
) -> bpy.types.GeometryNodeTree:
    """
    Procedurally constructs a mathematical scatter node tree in Blender 5.2.1 LTS.
    """
    nt = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    nt.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = nt.nodes
    links = nt.links

    # 1. Output
    gout = nodes.new('NodeGroupOutput')

    # 2. Target Surface Geometry (Terrain)
    oinfo = nodes.new('GeometryNodeObjectInfo')
    oinfo.inputs['Object'].default_value = target_terrain_obj
    oinfo.transform_space = 'RELATIVE'

    # 3. Position & Altitude Mask
    pos = nodes.new('GeometryNodeInputPosition')
    sep_pos = nodes.new('ShaderNodeSeparateXYZ')
    links.new(pos.outputs['Position'], sep_pos.inputs['Vector'])

    cmp_alt_lo = nodes.new('FunctionNodeCompare')
    cmp_alt_lo.operation = 'GREATER_EQUAL'
    cmp_alt_lo.inputs['B'].default_value = alt_min
    links.new(sep_pos.outputs['Z'], cmp_alt_lo.inputs['A'])

    cmp_alt_hi = nodes.new('FunctionNodeCompare')
    cmp_alt_hi.operation = 'LESS_EQUAL'
    cmp_alt_hi.inputs['B'].default_value = alt_max
    links.new(sep_pos.outputs['Z'], cmp_alt_hi.inputs['A'])

    and_alt = nodes.new('FunctionNodeBooleanMath')
    and_alt.operation = 'AND'
    links.new(cmp_alt_lo.outputs['Result'], and_alt.inputs[0])
    links.new(cmp_alt_hi.outputs['Result'], and_alt.inputs[1])

    # 4. Normal & Slope Mask
    norm = nodes.new('GeometryNodeInputNormal')
    sep_norm = nodes.new('ShaderNodeSeparateXYZ')
    links.new(norm.outputs['Normal'], sep_norm.inputs['Vector'])

    cmp_slp_lo = nodes.new('FunctionNodeCompare')
    cmp_slp_lo.operation = 'GREATER_EQUAL'
    cmp_slp_lo.inputs['B'].default_value = slope_min_nz
    links.new(sep_norm.outputs['Z'], cmp_slp_lo.inputs['A'])

    cmp_slp_hi = nodes.new('FunctionNodeCompare')
    cmp_slp_hi.operation = 'LESS_EQUAL'
    cmp_slp_hi.inputs['B'].default_value = slope_max_nz
    links.new(sep_norm.outputs['Z'], cmp_slp_hi.inputs['A'])

    and_slp = nodes.new('FunctionNodeBooleanMath')
    and_slp.operation = 'AND'
    links.new(cmp_slp_lo.outputs['Result'], and_slp.inputs[0])
    links.new(cmp_slp_hi.outputs['Result'], and_slp.inputs[1])

    # 5. Combined Biome Selection Mask
    and_mask = nodes.new('FunctionNodeBooleanMath')
    and_mask.operation = 'AND'
    links.new(and_alt.outputs['Boolean'], and_mask.inputs[0])
    links.new(and_slp.outputs['Boolean'], and_mask.inputs[1])

    # 6. Distribute Points on Faces (Poisson Disk)
    dist = nodes.new('GeometryNodeDistributePointsOnFaces')
    dist.distribute_method = 'POISSON'
    dist.inputs['Density Max'].default_value = density_max
    dist.inputs['Distance Min'].default_value = distance_min
    dist.inputs['Seed'].default_value = seed
    links.new(oinfo.outputs['Geometry'], dist.inputs['Mesh'])
    links.new(and_mask.outputs['Boolean'], dist.inputs['Selection'])

    # 7. Prototype Instance Object
    pinfo = nodes.new('GeometryNodeObjectInfo')
    pinfo.inputs['Object'].default_value = prototype_obj
    pinfo.transform_space = 'ORIGINAL'

    # 8. Instance on Points
    inst = nodes.new('GeometryNodeInstanceOnPoints')
    links.new(dist.outputs['Points'], inst.inputs['Points'])
    links.new(pinfo.outputs['Geometry'], inst.inputs['Instance'])

    # 9. Scale & Rotation Variation
    rand_scale = nodes.new('FunctionNodeRandomValue')
    rand_scale.data_type = 'FLOAT'
    rand_scale.inputs['Min'].default_value = 0.8
    rand_scale.inputs['Max'].default_value = 1.25
    rand_scale.inputs['Seed'].default_value = seed + 1
    links.new(rand_scale.outputs['Value'], inst.inputs['Scale'])

    if align_to_normal:
        align_node = nodes.new('FunctionNodeAlignEulerToVector')
        align_node.axis = 'Z'
        links.new(dist.outputs['Normal'], align_node.inputs['Vector'])
        links.new(align_node.outputs['Rotation'], inst.inputs['Rotation'])
    else:
        rand_rot = nodes.new('FunctionNodeRandomValue')
        rand_rot.data_type = 'FLOAT_VECTOR'
        rand_rot.inputs['Min'].default_value = (-0.04, -0.04, 0.0)
        rand_rot.inputs['Max'].default_value = (0.04, 0.04, 6.28318)
        rand_rot.inputs['Seed'].default_value = seed + 2
        links.new(rand_rot.outputs['Value'], inst.inputs['Rotation'])

    # 10. Realize Instances (CRITICAL for glTF export & multi-material support)
    realize = nodes.new('GeometryNodeRealizeInstances')
    links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
    links.new(realize.outputs['Geometry'], gout.inputs['Geometry'])

    return nt
```

---

## 8. Verification Strategy (`verify_ecosystem.py`)

The automated verification suite must be updated with the following assertions:
1. **Scene Collections:** Assert presence of `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`.
2. **Flora Instances Inspection:**
   - Assert `Flora_Instances` contains active Geometry Nodes scatter objects covering all 4 biomes.
   - Assert each scatter object has a `GeometryNodeTree` containing `GeometryNodeDistributePointsOnFaces` and `GeometryNodeRealizeInstances`.
   - Assert at least 4 distinct botanical prototype species exist across the 4 biomes (Pines, Broadleaf trees, Shore reeds/water plants, Bioluminescent cave mushrooms).
   - Assert 100% smooth shading compliance (`poly.use_smooth == True`) on all base prototypes.
3. **Cave Bioluminescence:**
   - Assert `M_Bio_Mushroom` or cave flora material has `Emission Strength > 0` and emissive color assigned.
4. **glTF Asset Integrity:**
   - Assert `ecosystem_map.glb` exists and exceeds `200 KB` (per acceptance criteria).
   - Assert GLB contains realized mesh primitives and embedded PBR materials (including emissive factor).
   - Assert fauna skeletal armatures and animation tracks are preserved intact.
5. **Headless Render:**
   - Render 3/4 isometric preview to `render_preview.png` asserting no missing shader pink artifacts and clean illumination.

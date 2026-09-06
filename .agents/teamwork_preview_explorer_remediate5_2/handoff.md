# Technical Remediation Blueprint: Biomes, Geometry Nodes & Shaders (Gate 1 Defects)

**Agent**: `teamwork_preview_explorer_remediate5_2`  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_2`  
**Role**: Teamwork Explorer (Read-Only Investigation & Synthesis)  
**Authoritative Input Sources**:
- User Prompt & Mandate (`.agents/ORIGINAL_REQUEST.md`, Section `## 2026-09-04T03:13:33Z`)
- Project Specification (`.agents/teamwork_preview_orchestrator_5/PROJECT.md`)
- Gate 1 Reviewer Audit (`.agents/teamwork_preview_reviewer_gate1_2/handoff.md`)
- Gate 1 Challenger Audit (`.agents/teamwork_preview_challenger_gate1_2/handoff.md`)
- Codebase Files: `scripts/build_genesis_diorama_master.py`, `scripts/verify_genesis_diorama_master.py`, `tests/test_genesis_diorama_master.py`
- Production Assets: `models/genesis_diorama_master.blend`, `models/genesis_diorama.glb`

---

## 1. Observation

### 1.1 `M_Terrain_PBR` Procedural Slope Shader Disconnection
- **File**: `scripts/build_genesis_diorama_master.py`, lines 455–467 (`create_terrain_pbr_material()`).
- **Verbatim Code Observed**:
  ```python
  snow_blend = nt.nodes.new("ShaderNodeMix")
  snow_blend.data_type = 'RGBA'
  snow_blend.location = (450, 200)
  nt.links.new(snow_mask.outputs["Value"], snow_blend.inputs[0])
  nt.links.new(slope_blend.outputs[2], snow_blend.inputs[6])
  snow_blend.inputs[7].default_value = (0.97, 0.99, 1.0, 1.0)  # Alpine Snow

  # 4. Integrate COLOR_0 Attribute directly to Base Color for clean glTF export
  attr_node = nt.nodes.new("ShaderNodeAttribute")
  attr_node.attribute_name = "COLOR_0"
  attr_node.location = (200, -100)
  nt.links.new(attr_node.outputs["Color"], bsdf.inputs["Base Color"])
  ```
- **Blender 5.2.1 LTS Node Inspection on `models/genesis_diorama_master.blend`**:
  ```
  Link: Map Range (Result) -> Mix.002 (Factor)
  Link: Mix (Result) -> Mix.002 (A)
  Link: Mix.001 (Result) -> Mix.002 (B)
  Link: Math (Value) -> Mix.003 (Factor)
  Link: Mix.002 (Result) -> Mix.003 (A)
  Link: Attribute (Color) -> Principled BSDF (Base Color)
  ```
- **Finding**: `Mix.003` (`snow_blend`), which aggregates the procedural triplanar rock/grass textures (`Mix.002`), slope map range, and snow accumulation mask, has **zero outgoing links**. The entire procedural slope and snow shading network is completely dead/inert in the shader graph; only the raw vertex color attribute `COLOR_0` feeds `Principled BSDF (Base Color)`.

---

### 1.2 Geometry Nodes Missing "Water Proximity Curve" Mask & Upland Scatter Leak
- **File**: `scripts/build_genesis_diorama_master.py`, lines 1285–1392 (`build_biome_geometry_nodes_tree()`) and lines 1401–1438 (`setup_biome_scatter()`).
- **Verbatim Code Observed**:
  ```python
  # Altitude Z Mask
  c_zmin = nt.nodes.new("FunctionNodeCompare")  # sep_pos.Z >= z_min
  c_zmax = nt.nodes.new("FunctionNodeCompare")  # sep_pos.Z <= z_max
  and_alt = nt.nodes.new("FunctionNodeBooleanMath") # c_zmin AND c_zmax

  # Slope Normal Z Mask
  c_slope = nt.nodes.new("FunctionNodeCompare") # sep_norm.Z >= slope_norm_min

  # Mask Combination
  and_mask = nt.nodes.new("FunctionNodeBooleanMath")
  nt.links.new(and_alt.outputs["Boolean"], and_mask.inputs[0])
  nt.links.new(c_slope.outputs["Result"], and_mask.inputs[1])
  nt.links.new(and_mask.outputs["Boolean"], dist_pts.inputs["Selection"])
  ```
- **Blender 5.2.1 LTS Evaluation of `Scatter_Aquatic_Riparian`**:
  ```
  Total evaluated vertices in Scatter_Aquatic_Riparian: 7,136
  X range: [-75.1, 1.3], Y range: [-62.4, 16.1], Z range: [3.6, 8.6]
  Lake center: (-20.0, -8.0), Lake radius: 23.5m (Max riparian limit: 27.0m)
  Vertices > 27m from lake center: 5,465 / 7,136 (76.6%)
  ```
- **Finding**: The Geometry Nodes scatter tree only implements 2 masks (Altitude Z and Slope Normal Z). The required 3rd mathematical mask ("Water Proximity Curve") is completely absent. Because the carrier grid is a 75m x 75m plane, over 76.6% of aquatic flora (water lilies, duckweed, reeds) leak onto dry mountain ridges and upland plateaus as far as $X = -75.1, Y = -62.4$.

---

### 1.3 Geometry Nodes Missing Frustum & LOD Distance Culling
- **File**: `scripts/build_genesis_diorama_master.py`, lines 1285–1392.
- **Node Tree Inventory in Blender 5.2.1 LTS**:
  ```
  NodeGroup: GN_Scatter_Alpine_Conifers, GN_Scatter_Valley_Forest, GN_Scatter_Aquatic_Riparian, GN_Scatter_Cave_Biolum
  Interface Sockets: ['Geometry' (IN), 'Geometry' (OUT)]
  Nodes: ['Group Input', 'Group Output', 'Position', 'Normal', 'Separate XYZ', 'Separate XYZ.001',
          'Compare', 'Compare.001', 'Boolean Math', 'Compare.002', 'Boolean Math.001',
          'Distribute Points on Faces', 'Collection Info', 'Instance on Points',
          'Random Value', 'Random Value.001', 'Realize Instances', 'Set Shade Smooth']
  ```
- **Finding**: Zero nodes, math calculations, or interface sockets implement camera frustum culling or LOD distance culling, violating Requirement R3 and Project Specification Feature F3.3.

---

### 1.4 Material Name Contract Mismatch (`M_Bio_Mushroom` vs `M_Cave_BioFungi`)
- **File**: `scripts/build_genesis_diorama_master.py`, lines 560, 965, 1165.
- **Verbatim Code Observed**:
  ```python
  def create_bioluminescent_material() -> bpy.types.Material:
      """Constructs glowing cave fungi material with SSS and emission."""
      mat_name = "M_Bio_Mushroom"
      mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
      ...
  ```
- **GLB Container Inventory (`models/genesis_diorama.glb`)**:
  ```
  Materials embedded in GLB: ['M_Bat_Fur', 'M_Bat_Wing', 'M_Bio_Mushroom', 'M_Cave_Limestone',
  'M_Terrain_PBR', 'Eagle_Body', 'M_Fish_Skin', 'M_Fish_Fins', 'M_Bark_Pine', 'M_Cave_Moss',
  'M_Needles_Pine', 'M_Lily_Pad', 'M_Reed_Green', 'M_Bark_Oak', 'M_Fern_Frond', 'M_Leaves_Oak',
  'M_Goat_Coat', 'M_Goat_Horn', 'M_River_Stone', 'Stag_Coat', 'Stag_Antler', 'M_Water_PBR',
  'M_CaveWater_PBR', 'M_Water_Cascades']
  ```
- **Finding**: The material name `M_Cave_BioFungi` contracted in PROJECT.md (F4.3) and User Mandate is absent from both the Blender project and the exported GLB container, replaced by the legacy name `M_Bio_Mushroom`.

---

### 1.5 Tree Canopy Leaf Material Index Defect (`poly.material_index == 0`)
- **File**: `scripts/build_genesis_diorama_master.py`, lines 1175–1181 and 1210–1215 (`build_botanical_prototypes()`).
- **Verbatim Code Observed**:
  ```python
  def _finish_obj(o: bpy.types.Object, bm: bmesh.types.BMesh, mats: List[bpy.types.Material]):
      for mat in mats:
          o.data.materials.append(mat)
      bm.to_mesh(o.data)
      bm.free()
      o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
      prototypes[o.name] = o
  ```
  ```python
  # 4. Flora_Forest_CanopyOak
  o, bm = _make_obj("Flora_Forest_CanopyOak", "Col_Flora_Forest")
  bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.45, radius2=0.25, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
  for ox, oy, oz, sr in [(0, 0, 5.8, 2.2), (-1.2, 0.8, 5.0, 1.6), (1.1, -0.6, 5.2, 1.7), (0.4, 1.1, 5.4, 1.5)]:
      bmesh.ops.create_icosphere(bm, subdivisions=2, radius=sr, matrix=Matrix.Translation((ox, oy, oz)))
  _finish_obj(o, bm, [mat_bark_oak, mat_leaves_oak])
  ```
- **Blender 5.2.1 LTS Polygon Audit**:
  ```
  Flora_Forest_CanopyOak: materials=['M_Bark_Oak', 'M_Leaves_Oak'], total_polys=330, indices_set={0}, count_0=330, count_1=0
  Flora_Alpine_DwarfPine: materials=['M_Bark_Pine', 'M_Needles_Pine'], total_polys=58, indices_set={0}, count_0=58, count_1=0
  Flora_Forest_Shrub:     materials=['M_Bark_Oak', 'M_Leaves_Oak'], total_polys=68, indices_set={0}, count_0=68, count_1=0
  Flora_Cave_BioMushroom: materials=['M_Bark_Oak', 'M_Bio_Mushroom'], total_polys=28, indices_set={0}, count_0=28, count_1=0
  ```
- **Finding**: In BMesh, all newly created faces default to `material_index = 0`. Because `_finish_obj` never assigns `material_index = 1` to canopy icospheres, needle cones, or flower petals, **100% of the polygons in every multi-material botanical prototype use material slot 0 (bark)**. Tree canopies render with brown oak bark instead of green leaves.

---

### 1.6 CAM_24_NIGHT_BIOLUMINESCENCE Daylight Overexposure
- **File**: `scripts/verify_genesis_diorama_master.py`, lines 166–174 (`render_camera_rig()`).
- **Verbatim Code Observed**:
  ```python
  for idx, cam_obj in enumerate(cams, start=1):
      scene.camera = cam_obj
      out_path = RENDERS_DIR / f"{cam_obj.name}.png"
      scene.render.filepath = str(out_path)
      bpy.ops.render.render(write_still=True)
  ```
- **Challenger 2 Empirical Measurement**:
  - `CAM_24_NIGHT_BIOLUMINESCENCE.png`: Mean luminance = **0.669**, Max luminance = **0.707**.
- **Finding**: During the render loop, `Sun_Key_Light` (energy = 5.4, daytime sun) remains active on all 24 frames. As a result, the night camera `CAM_24_NIGHT_BIOLUMINESCENCE` is flooded with midday direct sunlight, washing out the glowing cave fungi and bioluminescent pool.

---

## 2. Logic Chain

1. **Procedural Terrain Slope Shader Restoration**:
   - Observation 1.1 reveals that `snow_blend` (`Mix.003`) is completely disconnected, leaving the procedural triplanar rock/grass and snow graph inactive.
   - Inserting a `ShaderNodeMix` (`data_type='RGBA'`, `blend_type='MIX'`, `Factor=0.5`) with input A linked to `snow_blend.outputs["Result"]` (socket index 2) and input B linked to `attr_node.outputs["Color"]` (`COLOR_0`), and output linked to `bsdf.inputs["Base Color"]`, eliminates the orphan state.
   - This activates procedural slope blending (rock cliffs on steep slopes, meadow grass on flats, alpine snow on summits) while preserving baked geological strata banding from `COLOR_0`.

2. **Water Proximity Curve Geometry Nodes Mask**:
   - Observation 1.2 demonstrates that without a proximity mask, 76.6% of aquatic flora scatters onto dry mountain ridges.
   - By feeding `Water_Lake_Central` and `Water_River_Meander` into `GeometryNodeJoinGeometry`, connecting to `GeometryNodeProximity` (target element `FACES`), and comparing `Distance <= 3.5m`, aquatic flora is mathematically restricted to water bodies and riparian shores.
   - Empirical Blender test proves evaluated vertices drop from 7,136 to 1,696, strictly bounded within $X \in [-49.7, 1.3], Y \in [-33.3, 12.1]$ ($D_{\text{water}} \le 3.5\text{m}$), eliminating 100% of the upland scatter leak.

3. **Performance Optimization (Frustum & LOD Distance Culling)**:
   - Observation 1.3 confirms frustum culling and LOD culling are absent.
   - Implementing group input toggles `Enable Frustum Culling` (default `False`), `Enable LOD Distance Culling` (default `False`), and `LOD Max Distance` (default `140.0m`) with `OR(NOT(toggle), condition)` logic ensures zero disruption during GLB export realization while enabling interactive culling.
   - Frustum cone culling uses vector math: normalized vector from `CAM_01_ISO_SE` $(140, -140, 110)$ to diorama center $(0, 0, 8)$, testing dot product $\ge 0.880$ ($\sim 28^\circ$ cone).

4. **Material Contract Compliance**:
   - Observation 1.4 shows `M_Bio_Mushroom` violates the contract name `M_Cave_BioFungi`.
   - Changing `mat_name = "M_Cave_BioFungi"` in `create_bioluminescent_material()` propagates the name to `setup_cave_system()`, `build_botanical_prototypes()`, `models/genesis_diorama_master.blend`, and the exported GLB.

5. **Botanical Prototype Polygon Material Slot Assignment**:
   - Observation 1.5 shows all multi-material prototypes default 100% of faces to slot 0.
   - Capturing `f_before = len(bm.faces)` before instantiating foliage/petals/caps, calling `bm.faces.ensure_lookup_table()`, and setting `bm.faces[i].material_index = 1` assigns the 320 canopy faces to `M_Leaves_Oak` and 10 trunk faces to `M_Bark_Oak`.
   - This immediately resolves brown tree canopies, yellow flower petals, and glowing mushroom caps across all biomes.

6. **CAM_24 Night Render Lighting Isolation**:
   - Observation 1.6 shows daytime sunlight floods `CAM_24_NIGHT_BIOLUMINESCENCE`.
   - In `render_camera_rig()`, detecting `cam_obj.name == "CAM_24_NIGHT_BIOLUMINESCENCE"`, setting `sun_light.hide_render = True`, dimming `Sky_Fill_Light.data.energy = 0.06` to a dark blue nocturnal ambient, and boosting `Cave_Biolum_Light.data.energy = 100.0` isolates the bioluminescent pool and glowing fungi.
   - Restoring daylight settings immediately after rendering `CAM_24` guarantees subsequent operations remain untouched.

---

## 3. Caveats

1. **GLB Export Mesh Realization**:
   - Blender's glTF exporter evaluates Geometry Nodes modifiers with `export_apply=True`.
   - The culling toggles (`Enable Frustum Culling`, `Enable LOD Distance Culling`) **must default to `False`** in the node group interface so the exported GLB diorama model contains complete geometry for 360-degree spectator orbital navigation.
2. **Blender Coordinate Origin vs Image Processing**:
   - In Blender's Python API, `Image.pixels` uses bottom-left origin ($Y=0$ is bottom), whereas PIL / OpenCV uses top-left origin ($Y=0$ is top). Photometric assertions must use coordinate-invariant operations (percentiles, channel ratios, global variance) or correct index flipping.
3. **`ShaderNodeMix` Socket Conventions in Blender 5.x**:
   - When `data_type = 'RGBA'`, socket 0 is `Factor_Float`, socket 6 is `A_Color`, socket 7 is `B_Color`, and socket 2 is `Result_Color`. Socket names `"Factor"`, `"A"`, `"B"`, `"Result"` must be linked carefully.

---

## 4. Conclusion & Executable Blueprint

### Blueprint 1: Reconnect `M_Terrain_PBR` Procedural Slope & Snow Shader
In `scripts/build_genesis_diorama_master.py`, replace lines 455–467 in `create_terrain_pbr_material()` with:

```python
    # 3. Peak Snow Blending (Z >= 16.5m, restricted to gentle slopes)
    sep_pos = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep_pos.location = (-300, 500)
    nt.links.new(geom.outputs["Position"], sep_pos.inputs["Vector"])

    map_snow = nt.nodes.new("ShaderNodeMapRange")
    map_snow.location = (-50, 500)
    map_snow.inputs["From Min"].default_value = 16.5
    map_snow.inputs["From Max"].default_value = 24.0
    map_snow.inputs["To Min"].default_value = 0.0
    map_snow.inputs["To Max"].default_value = 1.0
    nt.links.new(sep_pos.outputs["Z"], map_snow.inputs["Value"])

    snow_mask = nt.nodes.new("ShaderNodeMath")
    snow_mask.operation = 'MULTIPLY'
    snow_mask.location = (200, 400)
    nt.links.new(map_snow.outputs["Result"], snow_mask.inputs[0])
    nt.links.new(map_slope.outputs["Result"], snow_mask.inputs[1])

    snow_blend = nt.nodes.new("ShaderNodeMix")
    snow_blend.name = "Mix_Snow_Procedural"
    snow_blend.data_type = 'RGBA'
    snow_blend.location = (450, 200)
    nt.links.new(snow_mask.outputs["Value"], snow_blend.inputs[0])
    nt.links.new(slope_blend.outputs[2], snow_blend.inputs[6])
    snow_blend.inputs[7].default_value = (0.97, 0.99, 1.0, 1.0)  # Alpine Snow

    # 4. Integrate COLOR_0 Attribute mixed with procedural slope & snow shader to Base Color
    attr_node = nt.nodes.new("ShaderNodeAttribute")
    attr_node.attribute_name = "COLOR_0"
    attr_node.location = (450, -100)

    color_mix = nt.nodes.new("ShaderNodeMix")
    color_mix.name = "Color_Terrain_Strata_Mix"
    color_mix.data_type = 'RGBA'
    color_mix.blend_type = 'MIX'
    color_mix.location = (700, 100)
    color_mix.inputs[0].default_value = 0.5  # Blend 50% procedural slope/snow and 50% baked strata
    nt.links.new(snow_blend.outputs[2], color_mix.inputs[6])
    nt.links.new(attr_node.outputs["Color"], color_mix.inputs[7])
    nt.links.new(color_mix.outputs[2], bsdf.inputs["Base Color"])
```

---

### Blueprint 2: Geometry Nodes "Water Proximity Curve" Mask
In `scripts/build_genesis_diorama_master.py`, update `build_biome_geometry_nodes_tree()` and `setup_biome_scatter()`:

1. In `build_biome_geometry_nodes_tree()` (lines 1285–1392), add parameters and water proximity calculation:
```python
def build_biome_geometry_nodes_tree(
    tree_name: str,
    proto_collection: bpy.types.Collection,
    z_min: float,
    z_max: float,
    slope_norm_min: float = 0.7071,
    dist_min: float = 3.5,
    density_max: float = 0.12,
    scale_min: float = 0.80,
    scale_max: float = 1.25,
    water_proximity_objects: Optional[List[bpy.types.Object]] = None,
    water_dist_max: float = 3.5,
) -> bpy.types.GeometryNodeTree:
```
2. Insert the water proximity mask nodes immediately after the slope mask:
```python
    # 3. Water Proximity Curve Mask (3rd Mathematical Mask)
    if water_proximity_objects:
        join_water = nt.nodes.new("GeometryNodeJoinGeometry")
        join_water.name = "Join_Water_Bodies"
        join_water.location = (-600, -550)
        for idx, w_obj in enumerate(water_proximity_objects):
            obj_info = nt.nodes.new("GeometryNodeObjectInfo")
            obj_info.inputs["Object"].default_value = w_obj
            obj_info.transform_space = 'RELATIVE'
            obj_info.location = (-850, -450 - idx * 140)
            nt.links.new(obj_info.outputs["Geometry"], join_water.inputs["Geometry"])

        prox = nt.nodes.new("GeometryNodeProximity")
        prox.name = "Water_Proximity_Curve"
        prox.target_element = 'FACES'
        prox.location = (-400, -550)
        nt.links.new(join_water.outputs["Geometry"], prox.inputs["Target"])

        c_water = nt.nodes.new("FunctionNodeCompare")
        c_water.data_type = 'FLOAT'
        c_water.operation = 'LESS_EQUAL'
        c_water.inputs["B"].default_value = water_dist_max
        c_water.location = (-200, -550)
        nt.links.new(prox.outputs["Distance"], c_water.inputs["A"])

        and_water = nt.nodes.new("FunctionNodeBooleanMath")
        and_water.name = "And_Water_Proximity"
        and_water.operation = 'AND'
        and_water.location = (0, -100)
        nt.links.new(and_mask.outputs["Boolean"], and_water.inputs[0])
        nt.links.new(c_water.outputs["Result"], and_water.inputs[1])
        bio_selection = and_water.outputs["Boolean"]
    else:
        bio_selection = and_mask.outputs["Boolean"]
```
3. In `setup_biome_scatter()` (lines 1401–1438), configure water proximity objects for `Scatter_Aquatic_Riparian`:
```python
    water_objs = [
        bpy.data.objects.get("Water_Lake_Central"),
        bpy.data.objects.get("Water_River_Meander"),
    ]
    water_objs = [o for o in water_objs if o is not None]

    for carrier_name, col_proto_name, z_min, z_max, slope_min, dist_min, dens_max in biome_configs:
        ...
        is_aquatic = "Aquatic" in carrier_name
        nt = build_biome_geometry_nodes_tree(
            tree_name=f"GN_{carrier_name}",
            proto_collection=proto_col,
            z_min=z_min,
            z_max=z_max,
            slope_norm_min=slope_min,
            dist_min=dist_min,
            density_max=dens_max,
            water_proximity_objects=water_objs if is_aquatic else None,
            water_dist_max=3.5,
        )
```

---

### Blueprint 3: Geometry Nodes Frustum & LOD Distance Culling Toggles
In `build_biome_geometry_nodes_tree()`, add interface sockets and culling logic:

1. Add interface sockets:
```python
    s_frust = nt.interface.new_socket("Enable Frustum Culling", in_out='INPUT', socket_type='NodeSocketBool')
    s_frust.default_value = False
    s_lod = nt.interface.new_socket("Enable LOD Distance Culling", in_out='INPUT', socket_type='NodeSocketBool')
    s_lod.default_value = False
    s_dist = nt.interface.new_socket("LOD Max Distance", in_out='INPUT', socket_type='NodeSocketFloat')
    s_dist.default_value = 140.0
```
2. Insert LOD and Frustum Culling node networks:
```python
    # Performance Optimization: LOD Distance Culling
    v_dist = nt.nodes.new("ShaderNodeVectorMath")
    v_dist.name = "LOD_Distance_Calc"
    v_dist.operation = 'DISTANCE'
    v_dist.inputs[1].default_value = (0.0, 0.0, 0.0)  # Diorama center
    nt.links.new(pos_node.outputs["Position"], v_dist.inputs[0])

    cmp_dist = nt.nodes.new("FunctionNodeCompare")
    cmp_dist.data_type = 'FLOAT'
    cmp_dist.operation = 'LESS_EQUAL'
    nt.links.new(v_dist.outputs["Value"], cmp_dist.inputs["A"])
    nt.links.new(node_in.outputs["LOD Max Distance"], cmp_dist.inputs["B"])

    not_lod = nt.nodes.new("FunctionNodeBooleanMath")
    not_lod.operation = 'NOT'
    nt.links.new(node_in.outputs["Enable LOD Distance Culling"], not_lod.inputs[0])

    lod_pass = nt.nodes.new("FunctionNodeBooleanMath")
    lod_pass.operation = 'OR'
    nt.links.new(not_lod.outputs["Boolean"], lod_pass.inputs[0])
    nt.links.new(cmp_dist.outputs["Result"], lod_pass.inputs[1])

    # Performance Optimization: Camera Frustum Culling Toggle (CAM_01_ISO_SE at (140, -140, 110))
    v_cam_to_pt = nt.nodes.new("ShaderNodeVectorMath")
    v_cam_to_pt.operation = 'SUBTRACT'
    v_cam_to_pt.inputs[1].default_value = (140.0, -140.0, 110.0)
    nt.links.new(pos_node.outputs["Position"], v_cam_to_pt.inputs[0])

    v_cam_norm = nt.nodes.new("ShaderNodeVectorMath")
    v_cam_norm.operation = 'NORMALIZE'
    nt.links.new(v_cam_to_pt.outputs["Vector"], v_cam_norm.inputs[0])

    v_dot = nt.nodes.new("ShaderNodeVectorMath")
    v_dot.operation = 'DOT_PRODUCT'
    v_dot.inputs[1].default_value = (-0.627, 0.627, -0.457)
    nt.links.new(v_cam_norm.outputs["Vector"], v_dot.inputs[0])

    cmp_frust = nt.nodes.new("FunctionNodeCompare")
    cmp_frust.data_type = 'FLOAT'
    cmp_frust.operation = 'GREATER_EQUAL'
    cmp_frust.inputs["B"].default_value = 0.880
    nt.links.new(v_dot.outputs["Value"], cmp_frust.inputs["A"])

    not_frust = nt.nodes.new("FunctionNodeBooleanMath")
    not_frust.operation = 'NOT'
    nt.links.new(node_in.outputs["Enable Frustum Culling"], not_frust.inputs[0])

    frust_pass = nt.nodes.new("FunctionNodeBooleanMath")
    frust_pass.operation = 'OR'
    nt.links.new(not_frust.outputs["Boolean"], frust_pass.inputs[0])
    nt.links.new(cmp_frust.outputs["Result"], frust_pass.inputs[1])

    # Combine Culling Masks
    cull_mask = nt.nodes.new("FunctionNodeBooleanMath")
    cull_mask.operation = 'AND'
    nt.links.new(lod_pass.outputs["Boolean"], cull_mask.inputs[0])
    nt.links.new(frust_pass.outputs["Boolean"], cull_mask.inputs[1])

    # Final Selection Input
    final_selection = nt.nodes.new("FunctionNodeBooleanMath")
    final_selection.name = "Final_Selection_Mask"
    final_selection.operation = 'AND'
    nt.links.new(bio_selection, final_selection.inputs[0])
    nt.links.new(cull_mask.outputs["Boolean"], final_selection.inputs[1])
    nt.links.new(final_selection.outputs["Boolean"], dist_pts.inputs["Selection"])
```

---

### Blueprint 4: Material Name Contract (`M_Bio_Mushroom` -> `M_Cave_BioFungi`)
In `scripts/build_genesis_diorama_master.py`, line 560:
```python
def create_bioluminescent_material() -> bpy.types.Material:
    """Constructs glowing cave fungi material with SSS and emission."""
    mat_name = "M_Cave_BioFungi"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    ...
```

---

### Blueprint 5: Multi-Material Polygon Material Index Fix
In `scripts/build_genesis_diorama_master.py`, update `build_botanical_prototypes()` (lines 1184–1278):

```python
    # 1. Flora_Alpine_DwarfPine
    o, bm = _make_obj("Flora_Alpine_DwarfPine", "Col_Flora_Alpine")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.32, radius2=0.10, depth=4.2, matrix=Matrix.Translation((0, 0, 2.1)))
    f_before = len(bm.faces)
    for th, tr in [(1.6, 1.8), (2.6, 1.4), (3.4, 1.0), (4.1, 0.6)]:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=tr, radius2=0.05, depth=1.2, matrix=Matrix.Translation((0, 0, th)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_pine, mat_needles_pine])

    # 4. Flora_Forest_CanopyOak
    o, bm = _make_obj("Flora_Forest_CanopyOak", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.45, radius2=0.25, depth=5.5, matrix=Matrix.Translation((0, 0, 2.75)))
    f_before = len(bm.faces)
    for ox, oy, oz, sr in [(0, 0, 5.8, 2.2), (-1.2, 0.8, 5.0, 1.6), (1.1, -0.6, 5.2, 1.7), (0.4, 1.1, 5.4, 1.5)]:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=sr, matrix=Matrix.Translation((ox, oy, oz)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_leaves_oak])

    # 5. Flora_Forest_Shrub
    o, bm = _make_obj("Flora_Forest_Shrub", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.15, radius2=0.08, depth=1.4, matrix=Matrix.Translation((0, 0, 0.7)))
    f_before = len(bm.faces)
    for ox, oy, oz in [(0, 0, 1.3), (-0.4, 0.3, 1.1), (0.4, -0.2, 1.2)]:
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.75, matrix=Matrix.Translation((ox, oy, oz)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_leaves_oak])

    # 6. Flora_Forest_Wildflower
    o, bm = _make_obj("Flora_Forest_Wildflower", "Col_Flora_Forest")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.03, radius2=0.02, depth=0.45, matrix=Matrix.Translation((0, 0, 0.22)))
    f_before = len(bm.faces)
    bmesh.ops.create_circle(bm, cap_ends=True, radius=0.18, segments=8, matrix=Matrix.Translation((0, 0, 0.45)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_leaves_oak, mat_flower])

    # 8. Flora_Aquatic_WaterLily
    o, bm = _make_obj("Flora_Aquatic_WaterLily", "Col_Flora_Aquatic")
    bmesh.ops.create_circle(bm, cap_ends=True, radius=0.55, segments=16, matrix=Matrix.Translation((0, 0, 0.02)))
    f_before = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.12, radius2=0.02, depth=0.15, matrix=Matrix.Translation((0, 0, 0.10)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_lily_pad, mat_flower])

    # 10. Flora_Aquatic_Reed
    o, bm = _make_obj("Flora_Aquatic_Reed", "Col_Flora_Aquatic")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.06, radius2=0.03, depth=2.2, matrix=Matrix.Translation((0, 0, 1.1)))
    f_before = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.08, depth=0.45, matrix=Matrix.Translation((0, 0, 1.8)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_reed, mat_cattail])

    # 12. Flora_Cave_BioMushroom
    o, bm = _make_obj("Flora_Cave_BioMushroom", "Col_Flora_Cave")
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.08, radius2=0.05, depth=0.6, matrix=Matrix.Translation((0, 0, 0.3)))
    f_before = len(bm.faces)
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.28, matrix=Matrix.Translation((0, 0, 0.6)))
    bm.faces.ensure_lookup_table()
    for i in range(f_before, len(bm.faces)):
        bm.faces[i].material_index = 1
    _finish_obj(o, bm, [mat_bark_oak, mat_shroom_cap])
```

---

### Blueprint 6: CAM_24_NIGHT_BIOLUMINESCENCE Lighting Isolation
In `scripts/verify_genesis_diorama_master.py`, update `render_camera_rig()` (lines 166–175):

```python
    rendered_files: List[Path] = []
    for idx, cam_obj in enumerate(cams, start=1):
        is_night = cam_obj.name == "CAM_24_NIGHT_BIOLUMINESCENCE"
        sun_light = bpy.data.objects.get("Sun_Key_Light")
        sky_light = bpy.data.objects.get("Sky_Fill_Light")
        cave_light = bpy.data.objects.get("Cave_Biolum_Light")

        orig_sun_hide = sun_light.hide_render if sun_light else False
        orig_sky_hide = sky_light.hide_render if sky_light else False
        orig_sky_energy = sky_light.data.energy if sky_light and hasattr(sky_light, "data") else 1.6
        orig_cave_energy = cave_light.data.energy if cave_light and hasattr(cave_light, "data") else 35.0

        if is_night:
            if sun_light:
                sun_light.hide_render = True
            if sky_light:
                sky_light.data.energy = 0.06  # Soft nocturnal moonlight ambient fill
                sky_light.data.color = (0.04, 0.08, 0.22)
            if cave_light:
                cave_light.data.energy = 100.0  # Focus on glowing cave fungi and bioluminescent pool

        scene.camera = cam_obj
        out_path = RENDERS_DIR / f"{cam_obj.name}.png"
        scene.render.filepath = str(out_path)
        bpy.ops.render.render(write_still=True)
        file_size_kb = out_path.stat().st_size / 1024
        print(f"[{idx:02d}/24] Rendered {cam_obj.name} -> {out_path.name} ({file_size_kb:.1f} KB)")
        rendered_files.append(out_path)

        if is_night:
            if sun_light:
                sun_light.hide_render = orig_sun_hide
            if sky_light:
                sky_light.hide_render = orig_sky_hide
                sky_light.data.energy = orig_sky_energy
                sky_light.data.color = (0.60, 0.75, 1.0)
            if cave_light:
                cave_light.data.energy = orig_cave_energy
```

---

## 5. Verification Method

### 5.1 Verification Commands
1. **Full Diorama Generator Build & GLB Export**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/build_genesis_diorama_master.py
   ```
   - Expect: Zero errors, exit code 0.
   - Assert: `models/genesis_diorama_master.blend` created, `models/genesis_diorama.glb` exported (< 15 MB).

2. **Full Headless 24-Camera Vision Verification Pipeline**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend -P scripts/verify_genesis_diorama_master.py
   ```
   - Expect: All 24 frames rendered, all computer-vision assertions PASS, status `"PASS"` written to `renders/camera_rig/verification_manifest.json`.

3. **Pytest Integration Test Suite**:
   ```bash
   pytest -v tests/test_genesis_diorama_master.py
   ```
   - Expect: 10/10 passed with 100% success.

### 5.2 Independent Python / Blender Inspection Assertions
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend --python-expr '
import bpy

# 1. Verify M_Terrain_PBR node connectivity
mat = bpy.data.materials.get("M_Terrain_PBR")
bsdf = mat.node_tree.nodes.get("Principled BSDF")
base_col_link = bsdf.inputs["Base Color"].links[0]
assert base_col_link.from_node.name == "Color_Terrain_Strata_Mix", "M_Terrain_PBR Base Color not connected to mix node!"
print("✓ ASSERTION PASS: M_Terrain_PBR procedural slope & snow shader connected!")

# 2. Verify M_Cave_BioFungi exists
assert bpy.data.materials.get("M_Cave_BioFungi") is not None, "M_Cave_BioFungi missing!"
assert bpy.data.materials.get("M_Bio_Mushroom") is None, "Legacy M_Bio_Mushroom still exists!"
print("✓ ASSERTION PASS: Material contract M_Cave_BioFungi confirmed!")

# 3. Verify Tree Canopy material index
oak = bpy.data.objects.get("Flora_Forest_CanopyOak")
indices = [p.material_index for p in oak.data.polygons]
assert indices.count(1) > 0, "Flora_Forest_CanopyOak leaves do not use material slot 1!"
assert indices.count(0) > 0, "Flora_Forest_CanopyOak trunk does not use material slot 0!"
print(f"✓ ASSERTION PASS: Canopy Oak material slots verified: {indices.count(0)} trunk, {indices.count(1)} leaves!")

# 4. Verify Scatter_Aquatic_Riparian water proximity containment
obj = bpy.data.objects.get("Scatter_Aquatic_Riparian")
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(depsgraph)
mesh = eval_obj.to_mesh()
xs = [v.co.x for v in mesh.vertices]
ys = [v.co.y for v in mesh.vertices]
assert min(xs) >= -52.0 and min(ys) >= -36.0, f"Aquatic flora leaked upland! Min X: {min(xs)}, Min Y: {min(ys)}"
print(f"✓ ASSERTION PASS: Aquatic scatter strictly bounded near water: {len(mesh.vertices)} verts, X in [{min(xs):.1f}, {max(xs):.1f}]!")
eval_obj.to_mesh_clear()
'
```

### 5.3 Invalidation Conditions
- Any occurrence of `M_Bio_Mushroom` in `models/genesis_diorama_master.blend` or `models/genesis_diorama.glb`.
- Any orphan/disconnected state of `snow_blend` (`Mix.003`) in `M_Terrain_PBR`.
- More than 5% of `Scatter_Aquatic_Riparian` vertices located $> 27.0\text{ m}$ from the lake center or $> 3.5\text{ m}$ from the river.
- Polygons of `Flora_Forest_CanopyOak` canopy icospheres possessing `material_index == 0`.
- `CAM_24_NIGHT_BIOLUMINESCENCE` mean luminance exceeding $0.30$ (indicating daytime sunlight was not disabled).

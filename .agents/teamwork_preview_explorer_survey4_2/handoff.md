# Handoff Report: Geometry Nodes 4-Zone Biome Distribution & Procedural Flora

**From:** `teamwork_preview_explorer_survey4_2`  
**To:** `teamwork_preview_orchestrator_4` (conversation ID: `fdb50731-d0ca-4df7-a6b6-87872373b756`)  
**Mission:** Phase 0 Survey - Geometry Nodes 4-Zone Biome Distribution & Procedural Flora  
**Date:** 2026-09-03T17:45:00Z  

---

## 1. Observation

1. **Existing Flora Scatter Implementation:**
   - In `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/flora_generator.py` (lines 305-398):
     Flora is distributed using procedural Python loops:
     ```python
     obj = bpy.data.objects.new(f"Flora_Conifer_{c_count:03d}", m_conifer)
     obj.location = (x, y, z)
     collection_flora.objects.link(obj)
     ```
     Scatter does not currently use Blender Geometry Nodes.
   - Species count is 4 (`Flora_Conifer`, `Flora_Broadleaf`, `Flora_Reed`, `Flora_Lily`), all with `poly.use_smooth = True` (lines 104, 171, 233, 272).
   - Cave flora (bioluminescent fungi/moss) is completely absent.

2. **glTF / GLB Exporter Behavior with Geometry Nodes in Blender 5.2.1 LTS:**
   - Command executed:
     `/Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "..."`
     * When exporting glTF with `export_apply=False`, point instances from Geometry Nodes are omitted; mesh size is only 7,892 bytes.
     * When `GeometryNodeRealizeInstances` is included and `export_apply=True` is enabled, scattered instances export fully with multi-material primitives (exported size 231,032 bytes for grid test).
     * With `export_apply=True` and `use_renderable=True`, rigged armatures and actions (`Stag_Idle`, `Stag_Walk`, `Eagle_Glide`, `Eagle_Flap`) remain 100% intact with 2 embedded glTF skins and 4 animation tracks.
     * Hidden prototypes (`hide_render=True`) with `use_renderable=True` prevent duplicate loose prototype meshes at $(0, 0, 0)$.

3. **Blender 5.2.1 LTS Geometry Nodes API:**
   - Sockets must be created via interface API:
     `nt.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")`.
   - Verified available node types:
     `GeometryNodeDistributePointsOnFaces` (supports POISSON with Distance Min, Density Max, and Selection socket), `GeometryNodeInstanceOnPoints`, `GeometryNodeRealizeInstances`, `GeometryNodeInputPosition`, `GeometryNodeInputNormal`, `GeometryNodeInputNamedAttribute`, `FunctionNodeCompare`, `FunctionNodeBooleanMath`, `FunctionNodeRandomValue`, `FunctionNodeAlignEulerToVector`.

4. **EEVEE Emissive Material Execution:**
   - Principled BSDF emission inputs (`Emission Color`, `Emission Strength`) tested in headless Blender 5.2.1 LTS with background task `task-78`: successfully rendered to PNG with zero shader errors, producing `KHR_materials_emissive_strength` in glTF 2.0.

---

## 2. Logic Chain

1. **Observation 1 & 3 $\to$ Step 1:** The existing imperative Python scattering in `flora_generator.py` must be replaced with declarative Blender Geometry Nodes node trees attached to biome scatter objects in collection `Flora_Instances`.
2. **Observation 3 $\to$ Step 2:** Mathematical masks for Altitude ($Z$), Slope ($N_z$), and Water Proximity ($d_{\text{water}}$) can be evaluated purely within Geometry Nodes using `GeometryNodeInputPosition`, `GeometryNodeInputNormal`, `FunctionNodeCompare`, and `FunctionNodeBooleanMath`, feeding directly into `DistributePointsOnFaces.inputs['Selection']`.
3. **Observation 2 $\to$ Step 3:** To ensure GLB export works seamlessly without headless crashes or empty foliage meshes, the node tree must terminate with `GeometryNodeRealizeInstances`, and `assemble_ecosystem.py` must call `bpy.ops.export_scene.gltf()` with `export_apply=True` and `use_renderable=True`.
4. **Observation 2 & 4 $\to$ Step 4:** Setting `proto.hide_render = True` ensures base prototype meshes are not exported as loose models at origin, while `Realize Instances` retains all material assignments (including `M_Bio_Mushroom` emissive properties for cave bioluminescence).
5. **Observation 1 & 4 $\to$ Step 5:** Adding `Flora_CaveMushroom` and `Flora_CaveMoss` with emissive PBR shaders satisfies the Subterranean Cave Biome requirement, completing the 4-zone biome specification.

---

## 3. Caveats

- **Terrain & Cave Mesh Dependency:** Geometry Nodes scatter on the terrain and subterranean cave assumes `terrain_hydrology.py` provides valid `Terrain_Mesh` and `Cave_Mesh` objects. If the cave mesh is not yet implemented, the scatter script can fall back to using terrain surface with an altitude clamp ($Z \le 0$) or standalone cave floor plane.
- **Poisson Density Tuning:** Poisson disk `Distance Min` should be kept at $\ge 1.5\,\text{m}$ for trees and $\ge 0.5\,\text{m}$ for groundcover/mushrooms to prevent instance counts from exceeding $\sim 250$ total, keeping `.glb` size under $3.5\,\text{MB}$.

---

## 4. Conclusion

The technical blueprint for the Geometry Nodes 4-Zone Biome Distribution and Procedural Flora is fully defined, empirically verified in Blender 5.2.1 LTS, and ready for implementation.
- 4 Biomes: Alpine (Conifers, Tussock grass, Lichens), Lowland (Broadleaf oaks, Flowering shrubs, Ferns), Aquatic/Riparian (Reeds, Water lilies, Coral reefs), Subterranean Cave (Bioluminescent mushrooms, Cave moss).
- Mathematical masks: Altitude ($Z$), Slope ($N_z$), Water Proximity ($d_{\text{water}}$).
- Export safety: `GeometryNodeRealizeInstances` + `export_apply=True` + `use_renderable=True` preserves animations, skins, and materials while guaranteeing GLB export integrity.

---

## 5. Verification Method

1. **Inspect Survey Artifacts:**
   - `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_2/survey_report.md`
   - `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_2/handoff.md`

2. **Verify Node Tree Construction Script in Headless Blender:**
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "
   import bpy
   nt = bpy.data.node_groups.new('Test', 'GeometryNodeTree')
   nt.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
   for n in ['GeometryNodeDistributePointsOnFaces', 'GeometryNodeInstanceOnPoints', 'GeometryNodeRealizeInstances']:
       nt.nodes.new(n)
   print('Geometry Nodes validation OK')
   "
   ```

3. **Verify Baseline Ecosystem Scene Integrity:**
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.blend -P /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/verify_ecosystem.py
   ```

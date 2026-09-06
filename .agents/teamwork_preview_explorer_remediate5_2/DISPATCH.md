## 2026-09-04T03:45:00Z
You are teamwork_preview_explorer_remediate5_2.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_2
The project root is: /Users/duongnad/Documents/project/Genesis_Zero

MANDATORY USER REQUEST RECORD:
Read the authoritative user request at:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (under section "## 2026-09-04T03:13:33Z")

PROJECT SPECIFICATION & GATE 1 AUDIT EVIDENCE:
Read PROJECT.md: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_5/PROJECT.md
Read Reviewer 2 report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_gate1_2/handoff.md
Read Challenger 2 report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_gate1_2/handoff.md

OBJECTIVE:
Investigate and formulate an exact, executable remediation blueprint for the Biomes, Geometry Nodes, and Shaders defects uncovered at Gate 1:
1. `M_Terrain_PBR` Procedural Slope Shader:
   - In `scripts/build_genesis_diorama_master.py`, reconnect the procedural slope-aware triplanar and snow blending node tree (`snow_blend` / `Mix.003`) to `Principled BSDF (Base Color)` mixed with `COLOR_0` attribute. Eliminate the inactive/orphan node state.
2. Geometry Nodes "Water Proximity Curve" Mask:
   - Implement the required 3rd mathematical mask in `build_biome_geometry_nodes_tree()` so that `Scatter_Aquatic_Riparian` is strictly constrained to water bodies (distance to lake center and river spline <= 3.5m), eliminating the 69.3% upland scatter leak.
3. Geometry Nodes Frustum & LOD Distance Culling:
   - Implement native distance culling and camera frustum culling toggle nodes in the Geometry Nodes modifier tree as required by R3.
4. Material Name Contract:
   - Rename `M_Bio_Mushroom` to the contract name `M_Cave_BioFungi` across the generator and GLB export.
5. Tree Canopy Leaf Material:
   - Fix the leaf mesh polygons to use green leaf material (`poly.material_index = 1`) rather than defaulting to brown bark.
6. CAM_24_NIGHT_BIOLUMINESCENCE:
   - Adjust render lighting in `verify_genesis_diorama_master.py` for CAM_24 (disable sun light during CAM_24 render, focus on glowing fungi and bioluminescent pool).

OUTPUT:
Write your complete technical recommendations and code snippets in:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_2/handoff.md
Then send a completion message to orchestrator.

## 2026-09-04T03:15:27Z
You are teamwork_preview_explorer_survey5_2.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_2
The project root is: /Users/duongnad/Documents/project/Genesis_Zero
Authoritative user request is in:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md under section "## 2026-09-04T03:13:33Z".

OBJECTIVE:
Investigate requirements R3 (Procedural Biome Scatter via Geometry Nodes) and R4 (PBR Shaders & Water Volumetrics) for building `models/genesis_diorama_master.blend`.
Specifically examine:
1. Existing Geometry Nodes setups and shaders in `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/`.
2. The exact specifications needed for:
   - Procedural Geometry Nodes scatter with 3 mathematical masks: Altitude Z, Slope from Normal Z, and Water Proximity curve.
   - 4 distinct biomes: Alpine (dwarf pines, cold tussock grass, rock moss), Lowland/Forest (broadleaf canopy trees, shrubs, wildflowers, ferns), Aquatic/Riparian (water lilies, duckweed, reeds, water weeds), Cave (bioluminescent fungi, dark-tolerant moss).
   - Performance optimizations: `Instance on Points`, third-person frustum culling, LOD distance culling.
   - Terrain PBR triplanar/slope shader automatically blending between steep rock cliff textures and flat grass/soil.
   - Water surface shader with Volume Absorption, depth-dependent transparency, and shore foam masking.
   - Subterranean cave bioluminescent emission shader for glowing fungi and cavern water.
3. Detail how these Geometry Nodes node trees and Shader node trees must be programmatically generated via `bpy`.

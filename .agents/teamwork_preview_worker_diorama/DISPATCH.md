## 2026-09-03T17:46:30Z

You are teamwork_preview_worker_diorama.
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_diorama.
Your parent is teamwork_preview_orchestrator_4 (conversation ID: fdb50731-d0ca-4df7-a6b6-87872373b756).

MANDATORY FIRST STEP:
Read /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md completely. Specifically focus on the latest user request dated 2026-09-03T17:21:58Z and reference images.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

REFERENCE SURVEY BLUEPRINTS & HANDOFFS:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/survey_report.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_1/handoff.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_2/survey_report.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_2/handoff.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_3/survey_report.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey4_3/handoff.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_4/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_4/TEST_INFRA.md

YOUR FILE WRITE OWNERSHIP:
- assets/blender_map/terrain_hydrology.py
- assets/blender_map/flora_generator.py
- assets/blender_map/fauna_generator.py
- assets/blender_map/assemble_ecosystem.py
- assets/blender_map/verify_ecosystem.py
- tests/test_ecosystem_map.py

YOUR IMPLEMENTATION MISSION:
1. Refactor `terrain_hydrology.py`:
   - Construct watertight 3D isometric diorama cutaway block (160m x 160m, base at Z = -14m) with vertical cutaway walls featuring procedural underground strata (topsoil, subsoil, bedrock striations) baked into `COLOR_0`.
   - Multi-tier geomorphology: Alpine snow peaks (delta Z = 33m >= 20m), scree slopes, plains, coastal drop-off.
   - Continuous 4-tier hydrology: alpine cascades -> meandering valley river -> central lake (Z = 4.5m) -> waterfall plunge -> lower coastal marine bay (Z = 0.0m, seabed Z = -4.5m).
   - Subterranean karst cave network inside diorama block (Z in [-7m, +0.5m]) with arched cavern vault, ceiling stalactites, floor stalagmites, underground pool (Z = -6.8m), and bioluminescent emissive shaders.
   - Physically-based slope terrain shader (cliffs >40 deg rock, scree 25-40 deg, flats <25 deg grass, snow >= 20m, shoreline sand) + triplanar cutaway wall strata.
   - Water volume absorption shader (ShaderNodeVolumeAbsorption with sapphire-emerald depth gradients) + shoreline foam.
2. Refactor `flora_generator.py`:
   - Build Blender Geometry Nodes procedural scatter networks with mathematical masks (Altitude Z, Slope Normal Z, Water Proximity).
   - 4 Biomes: Alpine (conifers, tussocks, lichens), Lowland/Forest (broadleaf oaks, shrubs, ferns), Aquatic/Riparian (reeds, lilies, submerged weeds, coastal coral greenery), Cave (bioluminescent glowing mushrooms `M_Bio_Mushroom`, cave moss).
   - Smooth shading (use_smooth = True on all flora meshes), random rotation/scale variation, point instancing, and `GeometryNodeRealizeInstances` for full GLB export compatibility.
3. Refactor `fauna_generator.py`:
   - 5 procedural animal species across 4 biomes: Mountain Goat (22 bones, Goat_Climb, Goat_Idle), Golden Eagle (16 bones, Eagle_Glide, Eagle_Flap), Highland Stag (26 bones, Stag_Idle, Stag_Walk), Freshwater Trout (12 bones, Fish_Swim, Fish_Idle), Cave Bat (18 bones, Bat_Roost, Bat_Flutter).
   - Complete skeletal armatures, smooth vertex group skinning (total 94 bones), active looping animation actions, and NLA track pushdown (total 10 actions) for multi-clip GLB export.
4. Refactor `assemble_ecosystem.py`:
   - 8 structured collections: `Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras` (with backward-compatible legacy aliasing).
   - 3rd-person 3/4 isometric perspective diorama camera at (175.0, -210.0, 175.0) with 55mm lens framing the full cutaway diorama block matching Reference Images 1 & 3.
   - Atmospheric lighting: Sun, Nishita Sky, EEVEE Next Fast GI Ambient Occlusion, AgX Medium-High Contrast.
   - Save master `ecosystem_map.blend`.
   - Export optimized `ecosystem_map.glb` (> 200 KB) with embedded meshes, materials, armatures, skins, and animations.
5. Refactor `verify_ecosystem.py`:
   - Implement 10 comprehensive headless checks asserting diorama cutaway block, strata attributes, elevation delta >= 20m, 4 water bodies, karst cave with speleothems and pool, 4 biomes, Geometry Nodes flora, 5 fauna armatures with active actions & NLA tracks, isometric camera, and GLB file size > 200 KB.
   - Execute headless render generating high-resolution preview `render_preview.png`.
6. Update `tests/test_ecosystem_map.py`:
   - Ensure all tests in the pytest suite pass cleanly with 100% success.
7. Verification & Deliverables:
   - Run:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python assets/blender_map/assemble_ecosystem.py
     /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python assets/blender_map/verify_ecosystem.py
     pytest tests/test_ecosystem_map.py -v
   - Verify `ecosystem_map.blend` exists.
   - Verify `ecosystem_map.glb` exists and size > 200 KB.
   - Verify `render_preview.png` exists and is high-resolution showing illuminated diorama.
8. Write comprehensive handoff.md in your working directory and notify parent orchestrator via send_message.

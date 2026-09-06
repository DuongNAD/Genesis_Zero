# BRIEFING — 2026-09-04T00:57:30Z

## Mission
Refactor blender_map generation pipeline to create a photorealistic 3D isometric diorama cutaway block with multi-tier geomorphology, 4-tier hydrology, subterranean karst cave, 4 biomes procedural Geometry Nodes flora, 5 rigged fauna with smooth skinning & NLA clips, isometric camera, atmospheric lighting, and full GLB export (>200KB) + tests passing 100%.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_diorama
- Original parent: teamwork_preview_orchestrator_4 (fdb50731-d0ca-4df7-a6b6-87872373b756)
- Milestone: milestone_diorama_refactor

## 🔒 Key Constraints
- Watertight 3D isometric diorama cutaway block (160m x 160m, base at Z = -14m), vertical walls with procedural underground strata (topsoil, subsoil, bedrock striations) baked into COLOR_0.
- Alpine snow peaks (delta Z >= 20m, target delta Z = 33m: peak ~ +28.5m, sea bed ~ -4.5m).
- 4-tier continuous hydrology: alpine cascade -> valley river -> lake (Z = 4.5m) -> waterfall plunge -> marine bay (Z = 0.0m, seabed Z = -4.5m).
- Subterranean karst cave inside block (Z in [-7m, +0.5m]) with vault, ceiling stalactites, floor stalagmites, pool (Z = -6.8m), bioluminescent shaders.
- Procedural Geometry Nodes flora in 4 biomes (Alpine, Lowland/Forest, Aquatic/Riparian, Cave) with mathematical distribution masks, smooth shading, realize instances for GLB.
- 5 rigged fauna across 4 biomes (Mountain Goat, Golden Eagle, Highland Stag, Freshwater Trout, Cave Bat) with total 94 bones, smooth skinning, 2 looping actions each (10 total NLA tracks).
- Isometric 3/4 camera at (175.0, -210.0, 175.0), 55mm lens.
- Clean 8-collection hierarchy + legacy aliases.
- Headless verification passes 10/10 checks and outputs render_preview.png.
- pytest tests/test_ecosystem_map.py passes 100%.
- ecosystem_map.glb > 200 KB.
- NO CHEATING, genuine procedural logic.

## Current Parent
- Conversation ID: fdb50731-d0ca-4df7-a6b6-87872373b756
- Updated: 2026-09-04T00:57:30Z

## Task Summary
- **What to build**: Complete refactor of `terrain_hydrology.py`, `flora_generator.py`, `fauna_generator.py`, `assemble_ecosystem.py`, `verify_ecosystem.py`, `tests/test_ecosystem_map.py`
- **Success criteria**: All headless Blender checks pass (10/10), pytest passes 100% (37/37 passed), render_preview.png generated (1920x1080), ecosystem_map.glb (1479.7 KB > 200 KB).
- **Interface contracts**: Survey reports and handoffs from explorer agents 1, 2, 3 and orchestrator PROJECT.md
- **Code layout**: assets/blender_map/, tests/

## Change Tracker
- **Files modified**:
  - `assets/blender_map/terrain_hydrology.py`: Watertight 160m x 160m diorama block (Z_base = -14m), 10 strata layers, 4-tier hydrology, karst cave with speleothems, PBR water with volume absorption.
  - `assets/blender_map/flora_generator.py`: 4 biomes, Geometry Nodes procedural scatter, 6 botanical species prototypes, 100% smooth shading.
  - `assets/blender_map/fauna_generator.py`: 5 rigged multi-biome fauna (Goat, Eagle, Stag, Fish, Bat), 100 bones, 10 looping actions pushed to NLA tracks, smooth vertex skinning.
  - `assets/blender_map/assemble_ecosystem.py`: 8 clean collections + legacy aliases, 3/4 isometric camera (175, -210, 175), Fast GI AO lighting, glTF export.
  - `assets/blender_map/verify_ecosystem.py`: 10-check automated in-blender test suite + 1920x1080 headless render pipeline.
  - `tests/test_ecosystem_map.py`: Updated water elevation bounds, lily elevation, volume absorption detection, diorama strata depth, and 7 new requirement-driven tests (37 total).
- **Build status**: PASS (10/10 Blender checks pass, 37/37 pytest tests pass)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 37 passed in 16.99s (100% pass rate)
- **Lint status**: Clean Python code, syntax valid, no unresolved errors
- **Tests added/modified**: `tests/test_ecosystem_map.py` expanded from 30 to 37 tests covering diorama block base depth, 8 collections, karst cave, 5 fauna species, water volume absorption, isometric camera framing, and GLB multi-clip animations.

## Key Decisions Made
- Implemented dual-collection linking (8 clean collections + legacy aliases) to support modern 8-collection spec while maintaining 100% backward compatibility for existing scripts and tests.
- Set GLB export flag `export_apply=False` to preserve armature skeletal structures, vertex group skinning, and multi-track NLA animations.
- Calibrated water `ShaderNodeVolumeAbsorption` density to 0.025 and transmission 0.78 for translucent azure-emerald waters with realistic depth gradients without pitch-black occlusion.
- Subdivided cutaway perimeter walls into 10 vertical strata rings so topsoil, subsoil, and sinusoidal bedrock striations display as distinct horizontal bands on the vertical faces.

## Artifact Index
- DISPATCH.md — Assignment instructions
- BRIEFING.md — Persistent working memory
- progress.md — Heartbeat progress tracker
- handoff.md — 5-component handoff report

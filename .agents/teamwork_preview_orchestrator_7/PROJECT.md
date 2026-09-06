# Project: Genesis Zero — Photorealistic Creature Ecosystem Overhaul

## Architecture Overview
This subsystem re-engineered the fauna ecosystem of Genesis Zero into scan-quality photorealistic 3D assets with organic anatomy, bio-PBR shaders, hierarchical armature rigging, 8 baked action animation clips, 4-angle turnaround concept sheets, and an interactive 3D Web Viewer with zero-CORS offline execution.

```
+-----------------------------------------------------------------------------------+
|                           Genesis Zero 3D Fauna Pipeline                          |
+-----------------------------------------------------------------------------------+
                                         |
     +-----------------------------------+------------------------------------+
     |                                                                        |
     v                                                                        v
[Implementation Track]                                               [E2E Testing Track]
- scripts/generate_photorealistic_creatures.py                       - scripts/verify_creatures_pipeline.py
  * Procedural organic BMesh (manifold, 0 loose, 0 ngons)            - tests/test_creature_assets.py
  * Hierarchical skeletal rigging & smooth skinning                  - TEST_READY.md
  * 8 Action animation clips baked to NLA tracks
  * Bio-PBR shaders (SSS, bump/roughness, cornea/specular eyes)
  * Render 4-angle turnaround shots (3/4, Front, Side, Top)
  * Output: assets/creatures/<species>.blend & .glb
            web/creature_images/<species>_turnaround.jpg
            docs/creatures/images/<species>_turnaround.jpg
                                         |
                                         v
                       [Web Viewer & Zero-CORS Integration]
                       - web/creature_viewer.html
                       - web/creature_models_data.js (base64 offline)
                       - scripts/sync_all_creature_models_to_js.py
                                         |
                                         v
                       [Multi-Agent Gate & Forensic Audit]
                       - reviewer_creatures_1: APPROVE
                       - reviewer_creatures_2: APPROVE
                       - challenger_creatures_1: APPROVE
                       - challenger_creatures_2: APPROVE
                       - auditor_creatures_1: CLEAN
```

## Feature Inventory
| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | 10 Species Organic Morphology | Clean manifold BMesh, 0 loose verts, 0 non-manifold edges, 0 ngons, 100% smooth shading | M1 | DONE |
| 2 | Hierarchical Armature Rigging | Bone tree (Root, Pelvis, Spine, Chest, Neck, Head, Jaw, Limbs, Claws, Wings/Fins) | M1 | DONE |
| 3 | 8 Game Engine Action Clips | Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death baked to NLA tracks in glTF | M1 | DONE |
| 4 | Bio-PBR Organic Shaders | Principled BSDF with Subsurface Scattering, procedural bump/roughness, wet cornea/specular eyes | M1 | DONE |
| 5 | Dual Format Deliverables | .blend source and .glb runtime for all 10 target species | M1 | DONE |
| 6 | 4-Angle Concept Turnaround Sheets | Perspective 3/4, Front Ortho, Side Ortho, Top-Down Ortho at web/creature_images/ and docs/creatures/images/ | M2 | DONE |
| 7 | Creature Master Catalog | docs/creatures/README.md with taxonomy, trait vectors, and visual links | M2 | DONE |
| 8 | Interactive 3D Web Viewer | web/creature_viewer.html with 10 species catalog, 3D viewport, OrbitControls | M3 | DONE |
| 9 | 8-Animation Control Rig | Action buttons with 0.2s crossfading, play/pause, playback speed (0.25x, 0.5x, 1x, 2x) | M3 | DONE |
| 10| Armature SkeletonHelper Overlay | Toggle bone visualization overlay | M3 | DONE |
| 11| Biological Traits & Features HUD | Brain, Speed, Armor, Attack, Sense, Stomach + biological traits badges | M3 | DONE |
| 12| 4-Angle Turnaround Modal | High-resolution turnaround concept sheet inspection dialog | M3 | DONE |
| 13| Zero-CORS Offline Data Sync | web/creature_models_data.js with embedded Base64 payload | M3 | DONE |
| 14| Standalone Verification Runner | scripts/verify_creatures_pipeline.py testing all 6 pipeline dimensions (68/68 passed, exit code 0) | E2E | DONE |
| 15| Automated Pytest Suite | tests/test_creature_assets.py with 100% passing tests (44/44 passed) | E2E | DONE |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Test harness `verify_creatures_pipeline.py`, `tests/test_creature_assets.py`, `TEST_READY.md` | none | DONE |
| M1 | Core 3D Fauna Pipeline | Procedural generator for 10 species: BMesh manifold, Armature rig, 8 NLA action clips, PBR shaders, .blend & .glb export | none | DONE |
| M2 | Turnaround Sheets & Catalog | Render 4-angle studio cameras, composite turnaround sheets, update `docs/creatures/README.md` | M1 | DONE |
| M3 | Web Viewer & Zero-CORS Sync | Build `web/creature_viewer.html`, sync script `sync_all_creature_models_to_js.py`, `creature_models_data.js` | M1, M2 | DONE |
| M4 | Verification, Audit & Gate | Run full test suites, Reviewers, Challengers, and Forensic Integrity Auditor | E2E, M1, M2, M3 | DONE |

## Code Layout
- `scripts/generate_photorealistic_creatures.py`: Master procedural generator script executed via headless Blender.
- `assets/creatures/<species>.blend`: Master Blender source files with armatures, materials, and NLA tracks.
- `assets/creatures/<species>.glb`: Runtime glTF 2.0 binary with baked skeleton and 8 animation clips.
- `web/creature_images/<species>_turnaround.jpg`: Web-optimized 4-angle concept turnaround sheets.
- `docs/creatures/images/<species>_turnaround.jpg`: Archival high-res turnaround sheets.
- `docs/creatures/README.md`: Master catalog with taxonomy and trait specifications.
- `web/creature_viewer.html`: Interactive 3D Creature Viewer application.
- `web/creature_models_data.js`: Base64 model data for zero-CORS offline viewing.
- `scripts/sync_all_creature_models_to_js.py`: Synchronizes `.glb` files into `creature_models_data.js`.
- `scripts/verify_creatures_pipeline.py`: Comprehensive 6-dimension verification runner.
- `tests/test_creature_assets.py`: Pytest automated asset verification test suite.

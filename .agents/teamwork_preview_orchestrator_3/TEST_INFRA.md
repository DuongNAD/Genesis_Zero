# E2E Test Infra: 3D Ecological Environment Map

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on internal module implementation details.
- Derives directly from `ORIGINAL_REQUEST.md` (section `## 2026-09-03T16:45:06Z`).
- Methodology: Category-Partition + Boundary Value Analysis + Cross-Feature Interactions + Real-World Workload Scenarios.

## Feature Inventory Mapping
| # | Feature | Source (Requirement) | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|----------------------|:------:|:------:|:------:|:------:|
| 1 | Multi-Biome Terrain Geometry | R1 / AC 115 | 5 | 5 | ✓ | ✓ |
| 2 | Hydrology (River & Lake) | R1 / AC 116 | 5 | 5 | ✓ | ✓ |
| 3 | Terrain & Water PBR Shaders | R1 / AC 115, 116 | 5 | 5 | ✓ | ✓ |
| 4 | Organic Flora (3+ Species) | R2 / AC 119 | 5 | 5 | ✓ | ✓ |
| 5 | Flora Smooth Shading & Distribution | R2 / AC 119 | 5 | 5 | ✓ | ✓ |
| 6 | Lifelike Fauna (2+ Species) | R3 / AC 120 | 5 | 5 | ✓ | ✓ |
| 7 | Skeletal Rigging & Armatures | R3 / AC 120 | 5 | 5 | ✓ | ✓ |
| 8 | Active Animation Cycles | R3 / AC 120 | 5 | 5 | ✓ | ✓ |
| 9 | Scene Composition & 6 Collections | R4 / AC 112 | 5 | 5 | ✓ | ✓ |
| 10 | Dual Deliverables (.blend & .glb) | R4 / AC 111, 124 | 5 | 5 | ✓ | ✓ |
| 11 | Headless Execution & Render Preview | R5 / AC 123, 125 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Test runner: `pytest` and headless Blender runner (`/Applications/Blender.app/Contents/MacOS/Blender -b`).
- Primary test script: `tests/test_ecosystem_map.py`.
- Verification mechanism:
  - Phase 1: Direct file inspection of `ecosystem_map.blend`, `ecosystem_map.glb`, `render_preview.png`.
  - Phase 2: In-Blender assertions inspecting datablocks (`bpy.data.collections`, `bpy.data.objects`, `bpy.data.materials`, `bpy.data.armatures`, `bpy.data.actions`).
  - Phase 3: GLB binary parsing validating chunk headers, mesh primitives, joint hierarchies, animation channels, and textures.
  - Phase 4: Image validation on `render_preview.png` (dimensions >= 1280x720, non-blank, no magenta/pink missing texture artifacts).

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Acceptance Target |
|---|----------|--------------------|-------------------|
| 1 | Complete Scene Boot & Inspection | F1.1 - F5.1 | Zero crash, zero missing data, all 6 collections populated |
| 2 | Game Engine Import Readiness (GLB) | F4.5 | Valid glTF 2.0 binary, size > 100 KB, animations playback |
| 3 | High-Res Offline Rendering | F5.2 | High quality illuminated diorama preview rendered under 10s |
| 4 | Wildlife Animation Evaluation | F3.3, F3.4, F3.5 | Idle and Locomotion keyframes present and deform mesh correctly |
| 5 | Hydrological Alignment & River Discharge | F1.2, F1.3 | River elevations correctly cascade down into lake basin water level |

## Coverage Thresholds
- Tier 1: Feature Coverage (>=5 test cases per feature area)
- Tier 2: Boundary & Corner Cases (>=5 test cases per feature area: delta Z >= 15m, span in [100, 500], size > 100 KB, use_smooth == True, frame counts > 0)
- Tier 3: Cross-Feature Combinations (Pairwise coverage: flora on terrain, fauna on terrain/air, water at river/lake depression, lighting illuminating camera view)
- Tier 4: Real-World Scenarios (End-to-end headless render, clean GLB export load, automated verification script pass)

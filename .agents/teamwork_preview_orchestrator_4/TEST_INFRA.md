# E2E Test Infra: Genesis Zero 3D Isometric Diorama Ecosystem

## Test Philosophy
- Requirement-driven, validating directly against user request `2026-09-03T17:21:58Z` and reference visuals.
- Multi-tier validation:
  * Tier 1: Unit & Component geometry assertions (watertight diorama block, strata attributes, elevation delta >= 20m, cave cavity, 4 water bodies).
  * Tier 2: Biome & Geometry Nodes flora instancing (4 biomes, smooth shading, realize instances).
  * Tier 3: Fauna skeletal armatures (5 species, 94 bones, 10 animation actions, NLA pushdown).
  * Tier 4: Scene assembly, isometric camera framing, EEVEE Next Fast GI AO lighting, GLB export (> 200 KB), and high-resolution preview rendering (`render_preview.png`).

## Feature Inventory Coverage
| # | Feature | Requirement | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|-------------|:------:|:------:|:------:|:------:|
| 1 | F1.1 Diorama Cutaway Block | R1, AC 180 | ✓ | | | ✓ |
| 2 | F1.2 Multi-Tier Elevation (delta >= 20m) | R1, AC 181 | ✓ | | | ✓ |
| 3 | F1.3 4-Tier Hydrology (Cascade/River/Lake/Bay) | R1, AC 182 | ✓ | | | ✓ |
| 4 | F1.4 Subterranean Karst Cave System | R1, AC 183 | ✓ | | | ✓ |
| 5 | F1.5 Slope-Aware Terrain & Strata Shaders | R4, AC 195 | ✓ | | | ✓ |
| 6 | F1.6 Water Volume Absorption Shader | R4, AC 196 | ✓ | | | ✓ |
| 7 | F1.7 Cave Bioluminescent Shaders | R4, AC 196 | ✓ | | | ✓ |
| 8 | F2.1 Geometry Nodes Scatter Masks | R2, AC 186 | | ✓ | | ✓ |
| 9 | F2.2 Alpine Biome Flora | R2, AC 186-187 | | ✓ | | ✓ |
| 10 | F2.3 Lowland & Forest Flora | R2, AC 186-187 | | ✓ | | ✓ |
| 11 | F2.4 Aquatic & Riparian Flora | R2, AC 186-187 | | ✓ | | ✓ |
| 12 | F2.5 Subterranean Cave Flora | R2, AC 186-187 | | ✓ | | ✓ |
| 13 | F2.6 Smooth Shading & GLB Realization | R2, AC 188 | | ✓ | | ✓ |
| 14 | F3.1 Alpine Fauna (Goat & Eagle) | R3, AC 191 | | | ✓ | ✓ |
| 15 | F3.2 Forest Fauna (Stag) | R3, AC 191 | | | ✓ | ✓ |
| 16 | F3.3 Aquatic Fauna (Trout) | R3, AC 191 | | | ✓ | ✓ |
| 17 | F3.4 Cave Fauna (Bat) | R3, AC 191 | | | ✓ | ✓ |
| 18 | F3.5 Armatures, Actions & NLA Tracks | R3, AC 192 | | | ✓ | ✓ |
| 19 | F4.1 Structured 8 Collections | R5, AC 198 | | | | ✓ |
| 20 | F4.2 3/4 Isometric Camera Framing | R5, AC 197 | | | | ✓ |
| 21 | F4.3 Sun/Sky & Fast GI AO Lighting | R5, AC 200 | | | | ✓ |
| 22 | F4.4 Master .blend File | R5, AC 199 | | | | ✓ |
| 23 | F4.5 Master .glb Export (> 200 KB) | R5, AC 199 | | | | ✓ |
| 24 | F5.1 Headless verify_ecosystem.py (10 checks) | R6, AC 198 | ✓ | ✓ | ✓ | ✓ |
| 25 | F5.2 Headless High-Res render_preview.png | R6, AC 200 | | | | ✓ |
| 26 | F5.3 Pytest E2E Test Suite | R6, AC 198 | ✓ | ✓ | ✓ | ✓ |

## Test Execution Commands
1. **Headless Verification Pipeline**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender -b /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.blend --python /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/verify_ecosystem.py
   ```
2. **Pytest E2E Test Suite**:
   ```bash
   pytest tests/test_ecosystem_map.py -v
   ```
3. **GLB Binary Validation**:
   Inspect `assets/blender_map/ecosystem_map.glb` size > 200 KB and parse glTF JSON chunks for skins, armatures, animations, and materials.

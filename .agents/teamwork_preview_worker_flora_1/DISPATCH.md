# Task Assignment: End-to-End Implementation of Botanical Research & 3D Pipeline

## Context
You are the primary Worker for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Explorer 1 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_spec_miner_survey6_1/handoff.md`
4. Explorer 2 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_2/handoff.md`
5. Explorer 3 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3/handoff.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Objectives & Tasks

### 1. Botanical Taxonomy & Catalog Synchronization (R1, R4)
- **Target Species**: 10 core + 2 supplementary species across 6 ecological tiers:
  - Canopy: *Quercus robur* L. (`canopy_ancient_oak`), *Sequoiadendron giganteum* (`canopy_giant_sequoia`), *Adansonia digitata* L. (`canopy_baobab`).
  - Shrubs/Ferns: *Cyathea cooperi* (`understory_tree_fern`).
  - Aquatic: *Nymphaea alba* L. (`aquatic_water_lily`), *Nelumbo nucifera* Gaertn. (`aquatic_sacred_lotus`).
  - Succulents: *Carnegiea gigantea* (`succulent_saguaro_cactus`).
  - Carnivorous/Cave: *Dionaea muscipula* J.Ellis (`carnivorous_venus_flytrap`), *Nepenthes rajah* Hook.f. (`carnivorous_pitcher_plant`), *Mycena chlorophos* (`cave_bioluminescent_mushroom`).
  - Wildflower / Endemic VN: *Leucanthemum vulgare* Lam. (`grass_alpine_tussock` / wildflower), *Paphiopedilum vietnamense* (vncreatures VNC0014).
- **Files to update**:
  - `docs/flora/README.md`: Add a prominent "Bảng Tổng Hợp Đối Chiếu Danh Pháp APG IV & Cơ Sở Dữ Liệu Quốc Tế" right after the introduction. Columns: Mã, Tên Tiếng Việt, Danh Pháp Khoa Học, Phân Loại APG IV (Họ/Bộ), Tầng Sinh Thái, Kích Thước, POWO ID, WFO ID, GBIF Key, CoL ID, vncreatures ID / IUCN, Ảnh 4 Góc (Link).
  - `docs/flora/species/<slug>.md` for each of the target species:
    - Upgrade metadata header with scientific name, author, APG IV clade, order, family, POWO/WFO/GBIF/CoL/vncreatures IDs, natural distribution, habitat coordinates, and IUCN status.
    - Standardize turnaround image link to use relative markdown link: `![Turnaround 4 Góc](../images/<slug>_turnaround.jpg)`.
    - Ensure anatomical descriptions and 3D specifications remain intact.

### 2. 3D Mesh Topology Remediation & Asset Rebuilding (R3)
- In `assets/flora/generators/flora_builder.py`:
  - Locate `build_carnivorous_pitcher_plant()` around lines 838–845 where tendril points are appended to `verts` without creating faces, leaving 18 loose vertices.
  - Fix this by either generating proper quad tube faces for the tendril stem or removing the orphaned point appending so that 0 loose vertices exist.
  - Re-run Blender 5.2.1 LTS in headless mode (`/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/flora/generators/flora_builder.py`) or run a dedicated script to regenerate `assets/flora/carnivorous_vines/carnivorous_pitcher_plant.blend` and `carnivorous_pitcher_plant.glb`.
  - Validate with BMesh headless inspection that all 16 `.blend` files have:
    - 0 loose vertices
    - 0 ngons (> 4 verts)
    - 0 multi-face edges (> 2 faces)
    - 0 wire edges
    - 100% smooth shaded polygons (`poly.use_smooth = True`)
    - Valid Principled BSDF with SSS and procedural bump.

### 3. Web Viewer & Base64 Model Synchronization (R4)
- In `web/flora_models_data.js`:
  - Update base64 string for `canopy_weeping_willow` by reading `assets/flora/canopy_trees/canopy_weeping_willow.glb` (base64 encode it) so it matches the 389 KB model on disk.
- In `web/flora_viewer.html`:
  - Confirm the 10 target species show the '4 Góc 📷' badge.
  - Confirm clicking "Bản vẽ 4 mặt" opens the modal with the proper turnaround sheet and caption.
  - Confirm Three.js 3D viewport smoothly loads all models with 360° orbit/turntable.

### 4. Automated Verification Suite (R5)
- Implement `scripts/verify_flora_pipeline.py`:
  - Standalone script using standard library (`sys`, `os`, `json`, `struct`, `re`).
  - Tests 5 categories:
    1. Metadata Integrity (docs/flora/README.md table, docs/flora/species/ fields, database IDs).
    2. Turnaround Concept Sheets (existence, non-zero size > 50KB, JPEG format).
    3. 3D Model Assets (.blend exists, size > 1KB, zstd frame 0x28B52FFD or BLENDER magic; .glb exists, size > 1KB).
    4. glTF 2.0 Binary Validation (magic `glTF`, version 2, chunk 0 JSON, chunk 1 BIN, mesh/material presence).
    5. Web Viewer & Base64 Data Sync (PLANTS array in flora_viewer.html, flora_models_data.js base64 matches).
  - Print clear, formatted diagnostic table.
  - Exit with Code 0 when all tests pass.
- Implement `tests/test_flora_assets.py`:
  - Pytest-compatible test suite covering all 5 verification dimensions above.
  - Must pass 100% under `pytest tests/test_flora_assets.py` with exit code 0.

### 5. Verification & Testing
- Run `python3 scripts/verify_flora_pipeline.py`.
- Run `pytest tests/test_flora_assets.py`.
- Run headless Blender BMesh inspection on all 16 `.blend` models.
- Document exact execution commands and outputs in your handoff report.

## Output Requirements
Write your detailed handoff report to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`
Follow the Handoff Protocol: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
When finished, send a message to the orchestrator.

## 2026-09-04T17:41:33Z
You are the Flora Pipeline Implementation Worker for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1
Please read your full task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement all tasks:
1. Standardize botanical taxonomy (APG IV, POWO/WFO/GBIF/CoL/vncreatures IDs) in docs/flora/README.md and docs/flora/species/<slug>.md.
2. Fix the 18 loose tendril vertices in carnivorous_pitcher_plant in assets/flora/generators/flora_builder.py, regenerate carnivorous_pitcher_plant.blend and .glb, and verify 0 loose verts, 0 ngons, 100% smooth shading.
3. Synchronize web/flora_models_data.js and web/flora_viewer.html.
4. Implement scripts/verify_flora_pipeline.py and tests/test_flora_assets.py.
5. Run builds, verification scripts, and pytest, ensuring Exit Code 0.
Write your complete handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md and message me when finished.


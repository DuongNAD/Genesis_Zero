# Task Assignment: Independent Code & Asset Review 1

## Context
You are Reviewer 1 for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_1`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`

## Review Scope & Instructions
Perform an independent, objective, and rigorous review of the botanical pipeline implementation:
1. **Botanical Taxonomy (R1, R4)**:
   - Inspect `docs/flora/README.md` (Section 2: APG IV table, database IDs from POWO, WFO, GBIF, CoL, vncreatures, relative turnaround links).
   - Inspect `docs/flora/species/*.md` for the 10 target species (e.g. `canopy_ancient_oak.md`, `carnivorous_pitcher_plant.md`, `aquatic_sacred_lotus.md`, etc.). Check that relative links `![Turnaround 4 Góc](../images/<slug>_turnaround.jpg)` are used instead of absolute `file:///` paths.
2. **3D Mesh Topology & Blender Assets (R3)**:
   - Run headless Blender BMesh inspection on all 16 `.blend` files in `assets/flora/`:
     Verify 0 loose vertices, 0 ngons (>4 verts), 0 multi-face edges, 0 wire edges, and 100% smooth shading (`poly.use_smooth == True`). Specifically verify that `carnivorous_pitcher_plant.blend` has 0 loose vertices.
   - Verify that all 16 `.glb` files conform to glTF 2.0 binary specifications and have valid PBR materials.
3. **Turnaround Concept Sheets & Web Viewer Integration (R2, R4)**:
   - Verify image files in `web/flora_images/` and `docs/flora/images/`.
   - Inspect `web/flora_viewer.html`: verify '4 Góc 📷' badge logic, turnaround modal `<dialog id="turnaround-modal">`, and Three.js 360° viewport.
   - Inspect `web/flora_models_data.js`: verify byte-exact match of all 16 base64 models against `.glb` files on disk.
4. **Automated Verification Suite Execution (R5)**:
   - Run `python3 scripts/verify_flora_pipeline.py` and confirm it passes with Exit Code 0.
   - Run `pytest tests/test_flora_assets.py` and confirm all tests pass with Exit Code 0.

## Output Requirements
Write your detailed review report to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_1/handoff.md`
Your report must explicitly conclude with a clear verdict: **APPROVE** or **REQUEST_CHANGES**.
When finished, send a message to the orchestrator.

## 2026-09-04T17:49:34Z
<USER_REQUEST>
You are Reviewer 1 for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_1
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_1/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Review all deliverables from Worker da451bb5-f34b-4983-b0a9-ab0d6af14b23 (taxonomy in docs/flora/, 3D mesh topology in assets/flora/, web viewer sync in web/, and test execution of scripts/verify_flora_pipeline.py and tests/test_flora_assets.py).
Write your complete report with explicit verdict (APPROVE or REQUEST_CHANGES) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_1/handoff.md and notify me.
</USER_REQUEST>

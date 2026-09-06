# Task Assignment: Independent Code & Asset Review 2

## Context
You are Reviewer 2 for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`

## Review Scope & Instructions
Perform an independent, objective, and rigorous review of the botanical pipeline implementation:
1. **Botanical Taxonomy (R1, R4)**:
   - Check `docs/flora/README.md` and `docs/flora/species/*.md`.
   - Validate taxonomic accuracy: APG IV clades, orders, families, scientific names, authors, and cross-reference identifiers (POWO Kew, WFO, GBIF, CoL, vncreatures).
   - Ensure relative image paths and download links are clean and free of absolute hardcoded paths.
2. **3D Mesh Topology & Blender Assets (R3)**:
   - Independently inspect the 16 `.blend` files in `assets/flora/` using headless Blender Python/BMesh.
   - Verify that `carnivorous_pitcher_plant` defect is resolved (0 loose vertices) and that all models are quad-dominant, non-manifold edge free, and 100% smooth-shaded.
   - Verify glTF 2.0 binary chunks, PBR materials, and SSS settings.
3. **Web Viewer & Concept Art (R2, R4)**:
   - Check `web/flora_images/` turnaround sheets (1024x1024 JPEG).
   - Check `web/flora_viewer.html` and `web/flora_models_data.js`: verify badge logic, modal viewer, Three.js 3D viewport, and base64 parity.
4. **Automated Verification Suite Execution (R5)**:
   - Execute `python3 scripts/verify_flora_pipeline.py`.
   - Execute `pytest tests/test_flora_assets.py`.
   - Verify exit codes, test assertions, and diagnostic outputs.

## Output Requirements
Write your detailed review report to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2/handoff.md`
Your report must explicitly conclude with a clear verdict: **APPROVE** or **REQUEST_CHANGES**.

## 2026-09-04T17:49:34Z
<USER_REQUEST>
You are Reviewer 2 for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Review all deliverables from Worker da451bb5-f34b-4983-b0a9-ab0d6af14b23 (taxonomy in docs/flora/, 3D mesh topology in assets/flora/, web viewer sync in web/, and test execution of scripts/verify_flora_pipeline.py and tests/test_flora_assets.py).
Write your complete report with explicit verdict (APPROVE or REQUEST_CHANGES) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2/handoff.md and notify me.
</USER_REQUEST>

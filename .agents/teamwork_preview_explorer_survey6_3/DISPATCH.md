# Task Assignment: Turnaround Sheets, Web Viewer Integration & Automated Verification

## Context
You are the Web Viewer & Verification Explorer for the Genesis Zero botanical research and 3D modeling pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
Read `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).

## Mission & Objectives
Investigate all requirements, tools, and existing codebase/assets for Turnaround Sheets (R2), Web Viewer Integration (R4), and Automated Verification Suite (R5):
1. Investigate `web/` directory: inspect `web/flora_viewer.html`, `web/flora_models_data.js`, `web/flora_images/`, and related web assets or viewers (e.g. `web/watch3d.html`).
2. Examine the Turnaround sheet specifications:
   - Layout: Upper half = 3/4 Front Perspective view; Lower half = 3 Orthographic views (Front, Side, Top-Down).
   - Storage path: `web/flora_images/<species_slug>_turnaround.jpg` (or `.png`).
   - Tools available for image generation or rendering (Blender camera setup, PIL/Pillow composition, generate_image, etc.).
3. Examine Web Viewer requirements:
   - Badge "4 Góc 📷" on species cards.
   - Modal popup to view full turnaround sheet.
   - Real-time 360° Three.js viewport loading the `.glb` model.
4. Examine existing tests and verification scripts:
   - Check `tests/`, `scripts/`, or existing test infrastructure.
   - Formulate exact automated test requirements for R5: Python/pytest script (e.g. `scripts/verify_flora_pipeline.py` or `tests/test_flora_assets.py`) verifying taxonomy metadata, file existence and size (>0 bytes), glTF 2.0 validity, and web viewer data sync. Must run with exit code 0.

## Output Requirements
Write your detailed findings and report to `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3/handoff.md`.
Follow the Handoff Protocol: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
When finished, send a completion message to the parent orchestrator.

## 2026-09-04T17:33:46Z
You are the Web Viewer and Verification Explorer for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Investigate Turnaround concept sheets (4-angle standard layout in web/flora_images/), Web Viewer integration in web/flora_viewer.html and web/flora_models_data.js (4 Góc badge, turnaround modal, 360 Three.js viewport), and automated verification suite (scripts/verify_flora_pipeline.py or pytest tests/test_flora_assets.py).
Write your complete handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3/handoff.md and notify me when complete.

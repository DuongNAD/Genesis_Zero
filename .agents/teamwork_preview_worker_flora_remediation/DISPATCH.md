# Task Assignment: Remediation of Mesh Contiguity, Relative Links & Test Hardening

## Context
You are the Remediation Worker for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Reviewer 2 Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_flora_2/handoff.md`
4. Challenger 1 Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1/handoff.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Remediation Tasks

### Task 1: Fix Overlapping Faces in Weeping Willow Generator (`generate_willow_realistic.py`)
In `assets/flora/generators/generate_willow_realistic.py`:
- Locate `create_willow_leaf` (lines 143–162).
- Replace the overlapping face definitions (lines 154–161) with clean, non-overlapping, contiguous topology:
  ```python
  faces = [
      (0, 1, 2),      # Base left triangle
      (0, 2, 3),      # Base right triangle
      (1, 4, 5, 2),   # Blade mid-left quad
      (2, 5, 6, 3),   # Blade mid-right quad
      (4, 7, 5),      # Tip left triangle
      (5, 7, 6)       # Tip right triangle
  ]
  ```
- Run the generator with Blender 5.2.1 LTS:
  `/Applications/Blender.app/Contents/MacOS/Blender --background --python assets/flora/generators/generate_willow_realistic.py`
  to regenerate `assets/flora/canopy_trees/canopy_weeping_willow.blend` and `assets/flora/canopy_trees/canopy_weeping_willow.glb`.
- Run headless Blender BMesh inspection to verify that `canopy_weeping_willow.blend` now has:
  `incontiguous_edges == 0`, `loose_verts == 0`, `ngons == 0`, `100% smooth shading`.
- Update the base64 string for `canopy_weeping_willow` in `web/flora_models_data.js` so it matches the regenerated `.glb` file.

### Task 2: Fix Relative Asset Links & Eliminate All `file:///` Paths
- Check all markdown files in `docs/flora/species/` (and `docs/flora/README.md`):
  - Any relative link pointing to `assets/flora/...` from `docs/flora/species/<slug>.md` must use 3 parent levels: `../../../assets/flora/...` (because `docs/flora/species/` is 3 levels deep).
  - Eliminate EVERY hardcoded `file:///` absolute URI across all files in `docs/flora/species/*.md` (e.g. `canopy_weeping_willow.md`, `flower_oxeye_daisy.md`, etc.). Replace with relative paths.
  - In `docs/flora/species/flower_oxeye_daisy.md`, ensure links do not point to non-existent files.
  - In `docs/flora/species/endemic_paphiopedilum_vietnamense.md`, change `../../web/flora_viewer.html` to `../../../web/flora_viewer.html`.
  - Write a Python script to verify that EVERY relative link in every markdown file in `docs/flora/` resolves to an existing physical file on disk (`os.path.exists() == True`).

### Task 3: Strengthen Automated Verification Suites (`scripts/verify_flora_pipeline.py` & `tests/test_flora_assets.py`)
- In `scripts/verify_flora_pipeline.py`:
  - Add Check: Assert 0 occurrences of `file:///` in any `.md` file under `docs/flora/`.
  - Add Check: Assert all markdown links in `docs/flora/species/*.md` resolve to existing filesystem paths.
  - Add Check: BMesh contiguity check asserting 0 incontiguous edges across all 16 `.blend` models.
- In `tests/test_flora_assets.py`:
  - Add corresponding test cases for no `file:///` paths, link resolution validity, and BMesh contiguity (`edge.is_contiguous`).
- Run both:
  - `python3 scripts/verify_flora_pipeline.py`
  - `pytest tests/test_flora_assets.py`
  Confirm 100% pass with Exit Code 0.

## Output Requirements
Write your detailed handoff report to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation/handoff.md`
Follow the Handoff Protocol: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
When finished, send a message to the orchestrator.

## 2026-09-04T17:54:48Z
You are the Flora Remediation Worker for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement all 3 remediation tasks:
1. Fix overlapping quads in create_willow_leaf in assets/flora/generators/generate_willow_realistic.py, rebuild canopy_weeping_willow.blend and .glb, verify 0 incontiguous edges, and update web/flora_models_data.js.
2. Fix directory depth (../../../assets/flora/...) and eliminate ALL file:/// absolute paths across docs/flora/species/*.md, ensuring all markdown links resolve to existing files.
3. Add assertions for no file:/// paths, valid link resolution, and BMesh contiguity to scripts/verify_flora_pipeline.py and tests/test_flora_assets.py. Run both and confirm Exit Code 0.
Write your complete report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation/handoff.md and message me.


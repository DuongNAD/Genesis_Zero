# Task Assignment: Post-Remediation Adversarial Stress Testing

## Context
You are the Post-Remediation Adversarial Challenger for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_rem_1`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Remediation Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_remediation/handoff.md`

## Challenger Mission & Objectives
Perform aggressive adversarial verification on the remediated assets:
1. **Adversarial BMesh Inspection on Weeping Willow**:
   - Write a script invoking Blender 5.2.1 LTS headless BMesh API on `assets/flora/canopy_trees/canopy_weeping_willow.blend`.
   - Specifically test for `edge.is_contiguous == False` across all internal edges. Assert count is strictly 0.
   - Assert 0 loose vertices, 0 ngons, 0 non-smooth polygons across all 16 models in `assets/flora/`.
2. **Link Resolution & Non-Portability Fuzzing**:
   - Parse all links in `docs/flora/README.md` and all 103 files in `docs/flora/species/*.md`.
   - Assert: zero instances of `file:///` anywhere in `docs/flora/`.
   - Assert: every relative file path resolves via `os.path.exists()` without 404/broken links.
3. **glTF 2.0 Binary Parity**:
   - Compare SHA-256 hash of decoded `web/flora_models_data.js` for `canopy_weeping_willow` with the disk file `assets/flora/canopy_trees/canopy_weeping_willow.glb`. Assert 100% match.
4. **Verification Suite Execution**:
   - Execute `python3 scripts/verify_flora_pipeline.py`.
   - Execute `pytest tests/test_flora_assets.py`.
   - Verify exit code 0 and absence of false positives or skipped assertions.

## Output Requirements
Write your detailed report with an explicit verdict (**APPROVE** or **REQUEST_CHANGES**) to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_rem_1/handoff.md`
When finished, send a message to the orchestrator.

## 2026-09-04T18:00:45Z
You are the Post-Remediation Challenger for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_rem_1
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_rem_1/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Adversarially stress-test weeping willow internal edge contiguity via Blender BMesh (assert 0 incontiguous edges), test link resolution and zero file:/// paths across all 103 species markdown files, verify glTF binary hash parity in web/flora_models_data.js, and run test suites.
Write your complete report with explicit verdict (APPROVE or REQUEST_CHANGES) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_rem_1/handoff.md and notify me.


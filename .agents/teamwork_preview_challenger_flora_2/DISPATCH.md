# Task Assignment: Adversarial Verification & Stress Testing 2

## Context
You are Challenger 2 for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_2`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`

## Challenger Mission & Objectives
Empirically and adversarially challenge the web viewer, base64 data parity, and verification scripts:
1. **Base64 Parity & Binary Identity Stress-Test**:
   - Write a script to independently decode all 16 base64 strings from `web/flora_models_data.js`.
   - Compute SHA-256 hashes of the decoded bytes vs the physical `.glb` files in `assets/flora/`. Assert 100% hash equality.
   - Verify that `canopy_weeping_willow` matches the updated high-detail 389 KB model and `carnivorous_pitcher_plant` matches the remediated model.
2. **Web Viewer DOM & Logic Stress-Test**:
   - Parse `web/flora_viewer.html` and extract the `PLANTS` array.
   - For every entry with `turnaroundImg`, verify the physical image file exists on disk and is readable.
   - For every entry with `turnaroundImg`, assert that the '4 Góc 📷' badge HTML is rendered.
   - Verify modal markup (`#turnaround-modal`) and JavaScript event handlers for keyboard Escape and backdrop click.
3. **Verification Suite Adversarial Fuzzing / Stress Test**:
   - Run `python3 scripts/verify_flora_pipeline.py`.
   - Run `pytest tests/test_flora_assets.py`.
   - Test edge cases: simulate corrupted inputs, test against uncompressed vs zstd compressed `.blend` files, and ensure zero flakiness.

## Output Requirements
Write your detailed adversarial findings to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_2/handoff.md`
Include empirical data, scripts executed, pass/fail results, and your explicit verdict: **APPROVE** or **REQUEST_CHANGES**.
When finished, send a message to the orchestrator.

## 2026-09-04T17:49:55Z
You are Challenger 2 for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_2
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_2/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Adversarially stress-test web viewer integration, base64 vs disk binary hash equality, modal dialog behavior, and test suite execution robustness under scripts/verify_flora_pipeline.py and tests/test_flora_assets.py.
Write your complete report with explicit verdict (APPROVE or REQUEST_CHANGES) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_2/handoff.md and notify me.

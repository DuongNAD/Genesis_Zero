# Task Assignment: Adversarial Verification & Stress Testing 1

## Context
You are Challenger 1 for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`

## Challenger Mission & Objectives
Empirically and adversarially stress-test the botanical assets and pipeline:
1. **Adversarial Mesh Stress-Testing**:
   - Write an independent Python script that uses Blender 5.2.1 LTS (`/Applications/Blender.app/Contents/MacOS/Blender`) BMesh API to test every `.blend` model in `assets/flora/`:
     - Test for non-manifold edges, loose vertices, loose edges, face winding consistency, normal orientation, and non-smooth faces.
     - Specifically challenge `carnivorous_pitcher_plant.blend` to prove whether all 18 loose vertices are truly gone and replaced with valid manifold geometry.
     - Calculate exact quad vs triangle ratio for all models.
2. **glTF 2.0 Binary Stress-Testing**:
   - Write an independent binary parser stress-testing all 16 `.glb` files:
     - Check byte alignments (4-byte alignment of chunks), header lengths, JSON chunk size, BIN buffer size.
     - Assert that every bufferView and accessor references valid offsets within the BIN chunk without out-of-bounds reads.
     - Validate that materials have non-negative roughness, metallic in [0, 1], and valid baseColorFactors.
3. **Turnaround & Image Asset Integrity**:
   - Use PIL/Pillow to verify all turnaround sheets in `web/flora_images/`:
     - Verify dimensions (1024x1024), color mode (RGB), format (JPEG), and that images are not truncated or corrupt.
4. **Documentation & Viewer Consistency**:
   - Test that every target species listed in `docs/flora/README.md` has a valid corresponding markdown file in `docs/flora/species/`, that markdown files parse cleanly, and that no broken links or missing files exist.

## Output Requirements
Write your detailed adversarial findings to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1/handoff.md`
Include empirical data, scripts executed, pass/fail results, and your explicit verdict: **APPROVE** or **REQUEST_CHANGES**.
When finished, send a message to the orchestrator.

## 2026-09-04T17:49:55Z
You are Challenger 1 for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Adversarially stress-test 3D mesh topology across all 16 .blend files via Blender BMesh (zero loose verts, zero ngons, 100% smooth shading), glTF 2.0 binary chunks, and turnaround image integrity.
Write your complete report with explicit verdict (APPROVE or REQUEST_CHANGES) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1/handoff.md and notify me.

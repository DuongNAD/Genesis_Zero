# Task Assignment: Forensic Integrity Audit

## Context
You are the Forensic Auditor for the Genesis Zero Botanical Research & 3D Modeling Pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_flora_1`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
1. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).
2. `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_6/PROJECT.md`
3. Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_flora_1/handoff.md`

## Audit Instructions & Forensics Checks
Perform a rigorous, independent forensic integrity audit. The audit is a **BINARY VETO** with zero tolerance for cheating, facade implementations, or hardcoded shortcuts.

Run forensic checks across all deliverables:
1. **Source Code & Script Forensics**:
   - Inspect `assets/flora/generators/flora_builder.py`:
     Verify whether the tendril remediation is genuine procedural 3D cylinder/tube geometry or a facade. Check vertex, face, and material assignments.
   - Inspect `scripts/verify_flora_pipeline.py` and `tests/test_flora_assets.py`:
     Verify that tests perform genuine, dynamic validations (reading files from disk, parsing glTF 2.0 binary chunks, inspecting markdown tables, checking image headers). Verify there are no hardcoded pass return statements, bypassed checks, mock objects, or tautological assertions (`assert True`).
2. **Asset Authenticity Forensics**:
   - Verify that `.blend` and `.glb` files are genuine, non-corrupted 3D models containing real vertices, normals, and materials — not empty stubs or zero-byte placeholders.
   - Verify that images in `web/flora_images/` are authentic 1024x1024 JPEG files containing actual botanical imagery.
   - Verify that `web/flora_models_data.js` base64 strings decode to genuine binary glTF 2.0 files.
3. **Botanical Taxonomy Authenticity**:
   - Verify that the taxonomic data in `docs/flora/README.md` and `docs/flora/species/*.md` represents genuine APG IV classification and real, verifiable database identifiers (POWO Kew, WFO, GBIF, Catalogue of Life, vncreatures) rather than random numbers or placeholders.
4. **Execution Forensics**:
   - Independently execute `python3 scripts/verify_flora_pipeline.py` and `pytest tests/test_flora_assets.py`.
   - Verify the exit code is genuinely 0 and all output logs reflect real test execution.

## Output Requirements
Write your detailed forensic evidence report to:
`/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_flora_1/handoff.md`
Conclude with an unequivocal verdict:
- **CLEAN** (if zero integrity violations are found)
- **INTEGRITY VIOLATION** (if any cheating, hardcoded tests, fake assets, or facades are detected)

When finished, send a message to the orchestrator.

## 2026-09-04T17:49:55Z
You are the Forensic Auditor for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_flora_1
Please read your task assignment at /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_flora_1/DISPATCH.md
and read the mandatory user request at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md.
Perform a rigorous forensic integrity audit: static analysis, genuine vs facade implementations, no fake assertions, genuine 3D meshes and images, authentic APG IV taxonomy and database IDs, and dynamic verification suite execution.
Write your complete forensic report with explicit verdict (CLEAN or INTEGRITY VIOLATION) to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_flora_1/handoff.md and notify me.

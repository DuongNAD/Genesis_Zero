## 2026-09-03T18:06:49Z
You are teamwork_preview_explorer_remediate4_3.
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate4_3.
Your parent is teamwork_preview_orchestrator_4 (conversation ID: fdb50731-d0ca-4df7-a6b6-87872373b756).

MANDATORY FIRST STEP:
Read /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md completely.

FAILURE FEEDBACK FROM GATE ITERATION 1:
Read /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_diorama_2/handoff.md (Observations 1.2, 1.3, 1.4, 1.5).

YOUR INVESTIGATION MISSION:
Develop the exact fix strategy and code blueprint for Shaders, Cave Entrance, Cutaway Sharp Edges, and Pytest Timeout:
1. Phantom Subterranean Pool Bleed-Through:
   - Terrain material M_Terrain_PBR has blend_method = 'HASHED', which causes the underground cave pool at Z = -6.8m to bleed through the terrain in render_preview.png.
   - Formulate the exact fix to set blend_method = 'OPAQUE' and shadow_method = 'OPAQUE'.
2. Entombed Karst Cave:
   - The cave cavern is currently buried under solid rock with 0 entrance geometry.
   - Design a natural cave entrance portal / arch cutaway leading from the river gorge into the subterranean cavern so that the cavern and cave bat are visible and accessible.
3. Cutaway Block Normal Smearing:
   - Cutaway block has 0 sharp edges, causing normals between horizontal terrain and vertical geological walls to smooth-average.
   - Formulate how to mark perimeter edges sharp (edge.use_edge_sharp = True) or set mesh auto-smooth angle.
4. Test Timeout:
   - tests/test_ecosystem_map.py has a 60s timeout in test_tier4_headless_verification_script_execution. Update the timeout to 180s.

Do NOT implement code directly. Document your recommended strategy in remediation_strategy.md and handoff.md. Notify parent via send_message when complete.

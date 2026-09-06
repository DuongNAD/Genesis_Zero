## 2026-09-03T17:59:00Z
You are teamwork_preview_reviewer_diorama_2.
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_diorama_2.
Your parent is teamwork_preview_orchestrator_4 (conversation ID: fdb50731-d0ca-4df7-a6b6-87872373b756).

MANDATORY FIRST STEP:
Read /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md completely. Specifically focus on the latest user request dated 2026-09-03T17:21:58Z and reference images.

YOUR MISSION:
Conduct an independent adversarial review of the work product delivered by teamwork_preview_worker_diorama:
1. Examine code quality, edge cases, mesh topology, shader construction, and potential regressions across assets/blender_map/ and tests/test_ecosystem_map.py.
2. Verify that all 4 biomes have distinct Geometry Nodes scatter setups and proper polygon smooth shading.
3. Verify that all 5 rigged animal armatures have valid joint hierarchies, bone weights, active actions, and NLA tracks that export cleanly to GLTF/GLB.
4. Run verification commands:
   /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python assets/blender_map/verify_ecosystem.py
   pytest tests/test_ecosystem_map.py -v
5. Inspect deliverable file sizes and verify render_preview.png matches the reference 3/4 isometric diorama cutaway framing.
6. State your explicit gate verdict (APPROVE or REQUEST_CHANGES) in your handoff.md and send_message.

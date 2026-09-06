# Task Assignment: Biomes, Shaders, 24 Cameras & Spectator Review (Gate 1)

Assigned to: teamwork_preview_reviewer_gate1_2
Orchestrator: teamwork_preview_orchestrator_5
Project Root: /Users/duongnad/Documents/project/Genesis_Zero
Authoritative Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (Section ## 2026-09-04T03:13:33Z)
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_gate1_2
Target Output: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_gate1_2/handoff.md

## 2026-09-04T03:38:14Z
Review Biomes (R3), PBR Shaders (R4), 24 Camera Rig & Web Spectator Integration (R5).
Specifically verify:
1. Geometry Nodes scatter: 3 mathematical masks (Altitude Z, Slope Normal Z, Water Proximity curve), 13 botanical prototypes, 100% smooth shading (use_smooth = True), Instance on Points, frustum & LOD culling.
2. PBR Shaders: Terrain Triplanar/Slope shader (`M_Terrain_PBR`), Water Volume Absorption shader with contact shore foam (`M_Water_PBR`), Cave Bioluminescence shader (`M_Cave_BioFungi`).
3. 24 Camera Rig: all 24 cameras exist in `Camera_Rig_24` and `gltf.cameras`, exact naming and coordinates, cross-section clipping at 200m.
4. Web Spectator: `web/watch3d.html` camera dropdown, `web/watch3d.js` async GLB loading, camera presets mapping, syntax validation (`node -c web/watch3d.js`).
5. Execution of tests: `pytest -v tests/test_genesis_diorama_master.py`.

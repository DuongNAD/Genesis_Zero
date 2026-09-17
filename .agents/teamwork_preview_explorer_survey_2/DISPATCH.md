## 2026-09-10T05:14:00Z

Task: Phase 0 Survey - Genesis_Zero Integration & Acceptance Infrastructure Investigation
Working Directory: e:\Project\01_AI_Agents\Genesis_Zero\.agents\teamwork_preview_explorer_survey_2\
Original Request: e:\Project\01_AI_Agents\Genesis_Zero\.agents\ORIGINAL_REQUEST.md
Engine Directory: E:\tool\mcp\terra_forge
Target Workspace: e:\Project\01_AI_Agents\Genesis_Zero

Objectives:
1. Read e:\Project\01_AI_Agents\Genesis_Zero\.agents\ORIGINAL_REQUEST.md (§ 2026-09-10T05:12:31Z).
2. Deeply investigate e:\Project\01_AI_Agents\Genesis_Zero:
   - Existing map assets in `assets/blender_map/` (`ecosystem_map.blend`, `ecosystem_map.glb`, renders).
   - Viewer application (`viewer.html`, `web/watch3d.html`, `web/viewer.html` if any) and 60 FPS Three.js rendering requirements.
   - Coordinate contracts: `COORDINATE_CONTRACT.md` (X, Z in [-100, 100], Y in [0, 10], canonical scale 200.0).
   - `map_manifest.schema.json` and existing manifests.
   - Binary format decoding/verification tools: `world_artifact.py`, `world_256.anmw`, FNV-1a checksum validators.
   - NavMesh BFS reachability scripts/algorithms: how `navmeshCoverage >= 0.80` is measured and verified, spawn point definitions.
   - Existing test suite (`pytest`, tests in `Genesis_Zero` or `terra_forge`).
3. Identify existing files, interfaces, acceptance test scripts, and exact verification commands.
4. Output a detailed survey report to e:\Project\01_AI_Agents\Genesis_Zero\.agents\teamwork_preview_explorer_survey_2\handoff.md.

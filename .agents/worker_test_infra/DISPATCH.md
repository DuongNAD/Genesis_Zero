## 2026-09-05T07:35:00Z
You are worker_test_infra.
Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_test_infra.
Workspace root: /Users/duongnad/Documents/project/Genesis_Zero.
Exclusive file ownership: scripts/verify_creatures_pipeline.py, tests/test_creature_assets.py, TEST_READY.md.
Mandatory reading:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (MUST read first)
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7/TEST_INFRA.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_rep_3/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

IMPORTANT: DO NOT invoke subagents. You are an implementation worker; write and verify code directly in your session.

Your Mission:
Implement the automated test suite and standalone verification runner for the 10 target species (sand_skink, snow_ferret, alpine_ibex, meadow_hare, marsh_croc, abyssal_hunter, storm_eagle, giant_tarantula, armored_sentinel, carnivore_apex):
1. scripts/verify_creatures_pipeline.py:
   - Standalone CLI validation script executable via python3 scripts/verify_creatures_pipeline.py.
   - Validates 6 core dimensions:
     a. Taxonomy & Metadata for 10 species.
     b. Turnaround Images: checks web/creature_images/<species>_turnaround.jpg and docs/creatures/images/<species>_turnaround.jpg (JPEG SOI \xff\xd8, EOI \xff\xd9, size > 20KB).
     c. 3D Model deliverables: checks assets/creatures/<species>.blend (magic BLEN or zstd) and assets/creatures/<species>.glb (magic glTF v2).
     d. glTF 2.0 Skinning & 8-Animation Channels: parses .glb JSON chunk, verifies skins > 0, armature nodes, and exactly 8 animation clips (Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death) with samplers/channels > 0.
     e. Headless Blender BMesh Manifold Topology: executes /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "..." to assert 0 loose vertices, 0 incontiguous edges, 0 ngons (>4 vertices), 100% smooth shading.
     f. Web Viewer Sync: validates web/creature_viewer.html and web/creature_models_data.js.
   - Exits 0 on pass with structured ASCII/color reporting.
2. tests/test_creature_assets.py:
   - Pytest test suite covering all 6 dimensions.
3. Publish TEST_READY.md at project root.

Deliverables:
- Keep progress.md updated.
- Write handoff.md in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_test_infra/handoff.md.
- Send message to caller when done.

## 2026-09-05T09:10:10Z
**Context**: Test Infrastructure Verification
**Content**: Heartbeat status check. Please report on the status of scripts/verify_creatures_pipeline.py and tests/test_creature_assets.py.
**Action**: Reply with current status.

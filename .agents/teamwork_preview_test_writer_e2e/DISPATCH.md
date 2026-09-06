## 2026-09-03T16:53:20Z

You are teamwork_preview_test_writer_e2e.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_test_writer_e2e
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).
Test Infra: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_3/TEST_INFRA.md
Project Scope: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_3/PROJECT.md

File Ownership:
You EXCLUSIVELY own tests/test_ecosystem_map.py and /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md.
You must NOT write to or modify files in assets/blender_map/.

Your Mission:
1. Read ORIGINAL_REQUEST.md and TEST_INFRA.md carefully.
2. Implement a comprehensive 4-tier opaque-box E2E test suite in tests/test_ecosystem_map.py that exercises the deliverables generated at assets/blender_map/ (ecosystem_map.blend, ecosystem_map.glb, render_preview.png):
   - Tier 1: Feature Coverage (assertions on existence of blend/glb/png, 6 collections, terrain mesh, water meshes, 3+ flora species, 2+ fauna species, skeletal armatures, active actions).
   - Tier 2: Boundary & Corner Cases (terrain elevation delta >= 15.0m, terrain horizontal span in [100.0, 500.0], polygon.use_smooth is True across flora/fauna, GLB size > 100 KB, action keyframe frame counts >= 20, loopable frames).
   - Tier 3: Cross-Feature Combinations (flora placement bounded to terrain elevations, water meshes located at river/lake depressions, armatures modifying skinned meshes, lighting illuminating camera viewport).
   - Tier 4: Real-World Scenarios (headless Blender inspection script execution passes with 0 exit code, valid glTF 2.0 binary chunks header and animation clips parsed, render_preview.png valid non-blank image).
3. The test file must be runnable via pytest: `pytest -v tests/test_ecosystem_map.py`.
4. Create /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md following the TEST_READY template from the project instructions once the test suite is ready.
5. Write your handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_test_writer_e2e/handoff.md and notify the orchestrator via send_message.

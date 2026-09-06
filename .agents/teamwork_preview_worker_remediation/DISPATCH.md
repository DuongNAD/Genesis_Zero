# Dispatch for Remediation Worker (Iteration 2)

You are teamwork_preview_worker_remediation.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_remediation
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).
Challenger 1 Handoff: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_1/handoff.md
Explorer 1 Report (Lake Basin): /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_1/survey_report.md
Explorer 2 Report (River Channel): /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_2/survey_report.md
Explorer 3 Report (Flora Snapping): /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_iter2_3/survey_report.md

File Ownership:
You EXCLUSIVELY own assets/blender_map/terrain_hydrology.py, assets/blender_map/flora_generator.py, and generating assets/blender_map/ecosystem_map.blend, assets/blender_map/ecosystem_map.glb, assets/blender_map/render_preview.png.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Mission:
1. Read the survey reports from the 3 iteration 2 explorers. They contain the exact mathematical derivations and verified drop-in code.
2. In assets/blender_map/terrain_hydrology.py:
   - Replace the lake basin calculation with the closed-form 4-zone model from Explorer 1 so that the lake rim (r in [28, 42]m) maintains elevation >= 2.45m >= 2.2m across all 360 degrees, submerging the lake bed (r < 24m) to Z in [0.5, 0.8]m, and smoothly blending down to surrounding valley/hills.
   - Implement the continuous segment projection and 3-region lateral river levee architecture from Explorer 2 so that lateral riverbanks at distance w_channel rise strictly >= rz + 0.3m (target rz + 0.5m) above the local river water level, with channel depth >= 0.4m (target 0.8m), completely eliminating floating ribbon edges across all 80 cross-sections.
3. In assets/blender_map/flora_generator.py:
   - Use BVHTree surface snapping (`mathutils.bvhtree.BVHTree.FromBMesh(bm)`) to snap plant/reed root Z coordinates directly onto the discrete polygon facets of Terrain_Mesh, eliminating the 6-9cm quad chord sag.
4. Execute the scene assembler via headless Blender:
   `/Applications/Blender.app/Contents/MacOS/Blender -b --python assets/blender_map/assemble_ecosystem.py`
5. Execute in-blender verification and render:
   `/Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python assets/blender_map/verify_ecosystem.py`
6. Run the exact empirical stress-test checks from Challenger 1's handoff:
   - Check floating lake perimeter vertices: must be 0 / 36.
   - Check floating river sections: must be 0 / 80.
7. Run the full pytest test suite:
   `pytest -v tests/test_ecosystem_map.py`
8. Verify deliverable file sizes on disk (> 100 KB).
9. Write your handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_remediation/handoff.md documenting commands and verbatim outputs. Notify the orchestrator via send_message.

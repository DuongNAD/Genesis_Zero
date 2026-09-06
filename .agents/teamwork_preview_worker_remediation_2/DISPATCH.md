## 2026-09-04T04:17:34Z

You are teamwork_preview_worker_remediation_2.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_remediation_2
The project root is: /Users/duongnad/Documents/project/Genesis_Zero

MANDATORY USER REQUEST RECORD:
You MUST read the authoritative user request at:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (under section "## 2026-09-04T03:13:33Z") before making changes.

PROJECT SPECIFICATION & ARCHITECTURE:
Read: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_5/PROJECT.md

REMEDIATION BLUEPRINTS (CRITICAL - READ ALL 3):
1. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_1/handoff.md:
   - Cave Entrance: replace solid cubes with a genuine hollow arched portal & descending tunnel; carve cliff entrance alcove notch at (16, -6.5).
   - CAM_16: reposition to (10, 12, -6.5m) looking at (15, 18.5, -7.2m) inside the cavern chamber (+3.5m ceiling clearance).
   - Marine Bay: clip water grid to X <= 80m, Y >= -80m, add vertical transparent water cutaway walls to seabed (-4.5m) along East & South edges.
   - River Ribbon: fix line 236 to carve riverbed through lake berm (eliminating the +4.71m uphill surge over the dam at (-7.69, 11.62)), restrict river ribbon to t in [0.30, 0.54] (eliminating all submerged and floating vertices).
   - Outlet Waterfall: create 2-tier stepped waterfall for mountain cascades and lake-to-bay outlet gorge (Z = 4.52 -> 2.20 -> 0.05m) with base foam apron.
   - Tree Canopies: set poly.material_index = 1 on foliage so leaves are green (M_Leaves_Oak).
2. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_2/handoff.md:
   - M_Terrain_PBR: connect snow_blend (Mix.003) into Principled BSDF Base Color mixed with COLOR_0 attribute; eliminate orphan node state.
   - Geometry Nodes: implement the 3rd mathematical mask (Water Proximity to lake and river spline <= 3.5m) so aquatic scatter is restricted to water bodies (0% upland leak).
   - Geometry Nodes: add Frustum & LOD distance culling nodes with interface toggles.
   - Material Name: rename M_Bio_Mushroom to contract name M_Cave_BioFungi in builder and GLB export.
   - CAM_24 Night Lighting: in scripts/verify_genesis_diorama_master.py, hide Sun key light during CAM_24 render, dim ambient fill to nocturnal moonlight, highlight glowing cave fungi.
3. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_3/handoff.md:
   - web/watch3d.js: add _createSafeRigVec3(x, y, z) fallback (lines 767-770) and _isHeadlessOrNodeContext() guard around console.info and loadDioramaGLB auto-invocation. Fixes test_challenger_m4_audio_particles.py and 10/10 scrubber tests.
   - tests/test_genesis_diorama_master.py: add the 5 new rigorous tests (M_Terrain_PBR Base Color link, M_Cave_BioFungi contract, GN water proximity & culling, river ribbon alignment, cave portal & CAM_16 clearance).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
- scripts/build_genesis_diorama_master.py
- scripts/verify_genesis_diorama_master.py
- tests/test_genesis_diorama_master.py
- web/watch3d.js
- models/genesis_diorama_master.blend
- models/genesis_diorama.glb
- renders/camera_rig/

EXECUTION & VERIFICATION REQUIREMENTS:
1. Apply the blueprinted fixes to `scripts/build_genesis_diorama_master.py`, `scripts/verify_genesis_diorama_master.py`, `web/watch3d.js`, and `tests/test_genesis_diorama_master.py`.
2. Build models:
   `/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/build_genesis_diorama_master.py`
3. Render 24 camera angles and run computer-vision verification:
   `/Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend -P scripts/verify_genesis_diorama_master.py`
4. Run integration and stress test suites:
   `pytest -v tests/test_genesis_diorama_master.py tests/test_master_diorama_stress_probes.py`
   `pytest -v tests/test_challenger_m4_audio_particles.py tests/test_challenger_m4_scrubber.py`
   `pytest`
5. Write a comprehensive handoff report documenting all changes, verification output, and file sizes to:
   `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_remediation_2/handoff.md`
Then send a completion message to orchestrator.

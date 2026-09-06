## 2026-09-04T03:20:56Z
You are teamwork_preview_worker_1.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_1
The project root is: /Users/duongnad/Documents/project/Genesis_Zero

MANDATORY USER REQUEST RECORD:
You MUST read the authoritative user request at:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (under section "## 2026-09-04T03:13:33Z") before writing any code.

PROJECT SPECIFICATION & ARCHITECTURE:
Read the project specification at:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_5/PROJECT.md

SURVEY FINDINGS & TECHNICAL BLUEPRINTS:
Read the deep technical handoff reports prepared by the 3 Survey Explorers:
1. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_1/handoff.md (R1 & R2: Diorama slab bounds, analytical elevation equations, sharp alpine horn peaks, scree slopes, alluvial marsh, subterranean karst cave system with >=12m clearance, continuous 4-tier hydrology network).
2. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_2/handoff.md (R3 & R4: Procedural Geometry Nodes scatter with 3 masks: Altitude Z, Slope Normal Z, Water Proximity; 13 botanical prototypes across 4 biomes; smooth shading; Instance on Points with CollectionInfo Pick Instancing; Frustum & LOD culling; Terrain Triplanar/Slope PBR shader; Water Beer-Lambert Volume Absorption shader with AO shore foam; Cave Bioluminescent SSS shader).
3. /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_3/handoff.md (R5: Exact 24 camera rig parameters, near-plane cutaway slicing at 200m, glTF/GLB export pipeline, headless 24-angle vision verification script, 3D spectator integration in web/watch3d.html & watch3d.js).

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

EXCLUSIVE WRITE OWNERSHIP:
You exclusively own and may create/modify:
- scripts/build_genesis_diorama_master.py
- scripts/verify_genesis_diorama_master.py
- tests/test_genesis_diorama_master.py
- models/genesis_diorama_master.blend
- models/genesis_diorama.glb
- renders/camera_rig/
- web/watch3d.js
- web/watch3d.html

EXECUTION & VERIFICATION REQUIREMENTS:
1. Implement `scripts/build_genesis_diorama_master.py` using Blender 5.2.1 LTS (`/Applications/Blender.app/Contents/MacOS/Blender`) to generate `models/genesis_diorama_master.blend` and `models/genesis_diorama.glb`.
2. Implement `scripts/verify_genesis_diorama_master.py` to headlessly inspect the `.blend` file, render all 24 camera angles into `renders/camera_rig/`, and run automated computer-vision assertions (water depth gradient, snow albedo, bioluminescent contrast, strata banding).
3. Implement `tests/test_genesis_diorama_master.py` to assert collections, watertightness (0 boundary edges), water containment, cave clearance, 24 cameras, and glTF binary validity.
4. Integrate asynchronous diorama GLB loading and 24-camera switcher dock into `web/watch3d.js` and `web/watch3d.html`.
5. Execute all builds and test commands:
   - Run generator: `/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/build_genesis_diorama_master.py`
   - Run verification & render: `/Applications/Blender.app/Contents/MacOS/Blender -b models/genesis_diorama_master.blend -P scripts/verify_genesis_diorama_master.py`
   - Run pytest: `pytest -v tests/test_genesis_diorama_master.py`
   - Run full pytest: `pytest`
6. Write a complete handoff report documenting all evidence, commands executed, and file sizes to:
   `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_1/handoff.md`
Then send a completion message to orchestrator.

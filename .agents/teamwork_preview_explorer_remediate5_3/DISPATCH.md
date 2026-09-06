## 2026-09-04T03:45:03Z
You are teamwork_preview_explorer_remediate5_3.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_3
The project root is: /Users/duongnad/Documents/project/Genesis_Zero

MANDATORY USER REQUEST RECORD:
Read the authoritative user request at:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (under section "## 2026-09-04T03:13:33Z")

PROJECT SPECIFICATION & GATE 1 AUDIT EVIDENCE:
Read PROJECT.md: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_5/PROJECT.md
Read Challenger 2 report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_gate1_2/handoff.md
Read Reviewer 2 report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_reviewer_gate1_2/handoff.md

OBJECTIVE:
Investigate and formulate an exact, executable remediation blueprint for the Spectator Regressions and Test Suite Enhancements:
1. `web/watch3d.js` Regressions:
   - Fix line 767-770: Top-level `new THREE.Vector3()` throws `TypeError: THREE.Vector3 is not a constructor` under Node/headless test mocks, breaking `tests/test_challenger_m4_audio_particles.py`. Make Vector3 instantiation safe/lazy or guard against mock Three environments.
   - Fix lines 1066 & 3241: Unconditional `console.info("[Genesis3D] THREE.GLTFLoader not found...")` writes to stdout, corrupting JSON decode in `tests/test_challenger_m4_scrubber.py`. Silence or guard logging when running in headless/Node environments or non-browser contexts.
2. Test Suite Enhancements (`tests/test_genesis_diorama_master.py`):
   - Add direct assertions for `M_Terrain_PBR` Base Color link to procedural blend.
   - Add assertion for `M_Cave_BioFungi` material presence in both `.blend` and `.glb`.
   - Add assertion for Geometry Nodes Water Proximity mask and culling logic.
   - Add assertion for river ribbon vertices alignment (asserting 0 submerged/floating vertices).
   - Add assertion for hollow cave entrance portal and CAM_16 internal clearance.

OUTPUT:
Write your complete technical recommendations and code snippets in:
/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_remediate5_3/handoff.md
Then send a completion message to orchestrator.

## 2026-09-03T17:59:00Z

You are teamwork_preview_auditor_diorama_1.
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_auditor_diorama_1.
Your parent is teamwork_preview_orchestrator_4 (conversation ID: fdb50731-d0ca-4df7-a6b6-87872373b756).

MANDATORY FIRST STEP:
Read /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md completely. Specifically focus on the latest user request dated 2026-09-03T17:21:58Z.

YOUR MISSION (Forensic Integrity Audit):
Perform systematic forensic integrity verification on the work product in assets/blender_map/ and tests/test_ecosystem_map.py:
1. Static Analysis:
   - Check for hardcoded test results, mock return values, bypasses, dummy or facade implementations.
   - Verify that terrain, hydrology, karst cave, flora Geometry Nodes, and fauna armatures/actions are genuinely computed and procedurally generated.
2. Runtime Tracing & Execution Validation:
   - Run the assembly script headlessly and trace object generation:
     /Applications/Blender.app/Contents/MacOS/Blender -b --python assets/blender_map/assemble_ecosystem.py
   - Verify that the resulting ecosystem_map.blend and ecosystem_map.glb are genuinely created from the source code and contain real vertex data, materials, node trees, and armature bones.
   - Run the verification script:
     /Applications/Blender.app/Contents/MacOS/Blender -b assets/blender_map/ecosystem_map.blend --python assets/blender_map/verify_ecosystem.py
   - Verify that verify_ecosystem.py and test_ecosystem_map.py perform real assertions rather than no-op or tautological checks.
3. State your explicit gate verdict (CLEAN or INTEGRITY VIOLATION) in your handoff.md and send_message. Provide full evidence chain.

## 2026-09-05T06:05:14Z
<USER_REQUEST>
You are test_writer_creatures.
Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/test_writer_creatures.
Workspace root: /Users/duongnad/Documents/project/Genesis_Zero.
Mandatory reading:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (MUST read first)
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7/TEST_INFRA.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_rep_3/handoff.md (contains detailed blueprints for verify_creatures_pipeline.py and tests/test_creature_assets.py)

Your Mission:
Implement the complete, rigorous, independent verification test suite for the 10 target species:
sand_skink, snow_ferret, alpine_ibex, meadow_hare, marsh_croc, abyssal_hunter, storm_eagle, giant_tarantula, armored_sentinel, carnivore_apex.

Files to create:
1. scripts/verify_creatures_pipeline.py:
   - Standalone CLI validation script executable with python3 scripts/verify_creatures_pipeline.py.
   - Validates 6 core dimensions:
     a. Taxonomy & Metadata: 10 species recognized, correct domains, trait ranges.
     b. Turnaround Images: Checks web/creature_images/<species>_turnaround.jpg and docs/creatures/images/<species>_turnaround.jpg for JPEG SOI (\xff\xd8) and EOI (\xff\xd9), dimensions, file size > 20KB.
     c. 3D Model deliverables: Checks assets/creatures/<species>.blend (magic BLEN or zstd) and assets/creatures/<species>.glb (magic glTF, version 2).
     d. glTF 2.0 Skinning & 8-Animation Verification: parses JSON chunk of .glb, verifies skins array > 0, armature nodes exist, and exactly 8 animation clips exist (Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death) with keyframe samplers and channels > 0.
     e. Headless Blender BMesh Manifold Verification: executes headless Blender script via /Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "..." to check 0 loose vertices, 0 non-manifold edges, 0 ngons (>4 vertices), 100% smooth shading.
     f. Web Viewer Sync: checks that web/creature_viewer.html references all 10 species and web/creature_models_data.js contains base64 payloads matching .glb sha256.
   - Exits with 0 when all tests pass; prints structured color/ASCII summary report.
2. tests/test_creature_assets.py:
   - Pytest test suite with clean test functions covering R1-R6:
     test_creature_metadata_and_traits, test_creature_turnaround_images, test_creature_blend_and_glb_files, test_creature_gltf_skinning_and_8_animations, test_creature_bmesh_manifold_topology, test_creature_web_viewer_integration.
3. Publish TEST_READY.md at project root /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md when the test runner is complete.

Deliverables:
- Keep progress.md updated.
- Write handoff.md in /Users/duongnad/Documents/project/Genesis_Zero/.agents/test_writer_creatures/handoff.md.
- Send message to caller when done.
</USER_REQUEST>

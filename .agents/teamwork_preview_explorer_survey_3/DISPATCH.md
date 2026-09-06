# Dispatch for Survey Explorer 3

You are teamwork_preview_explorer_survey_3.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md

## 2026-09-03T16:47:04Z
You are teamwork_preview_explorer_survey_3.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).

Your mission:
1. Read ORIGINAL_REQUEST.md at /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md carefully.
2. Investigate technical design & best practices in Blender Python (bpy) for:
   - R3: Lifelike Fauna with Skeletal Rigging & Fluid Animations:
     * At least 2 distinct animal species (e.g. Quadruped such as a Deer/Wolf, and Flying/Avian such as an Eagle/Hawk, or Aquatic such as a Trout/Fish).
     * Mesh modeling with smooth topology and smooth shading.
     * Skeletal armature creation with proper bone hierarchy (root, spine, neck, head, limbs, tail/wings).
     * Vertex weights / armature skinning (vertex groups matching bone names, armature modifier).
     * Active animation actions with keyframes: Idle cycle (breathing, subtle movement) and Locomotion cycle (walk/run/fly), smooth interpolation, looping keyframes.
   - R4: Scene Composition & Dual Deliverables:
     * Collections: Terrain, Water, Flora, Fauna, Lighting, Camera.
     * Atmospheric lighting (Sun light, Sky texture/ambient environment lighting).
     * Main camera framing the scenic landscape.
     * Self-contained .blend file saving (bpy.ops.wm.save_as_mainfile).
     * Optimized .glb export (bpy.ops.export_scene.gltf) with embedded materials, textures, and animations (> 100 KB).
   - R5: Automated Verification & Render Preview:
     * Headless verification script asserting all collections, objects, materials, armatures, actions.
     * Headless rendering (bpy.ops.render.render(write_still=True)) producing render_preview.png.

Scope boundaries:
- Read-only exploration.
- Write your findings to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3/survey_report.md
- Write your handoff to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3/handoff.md
- When finished, send a message back to caller parent via send_message with a summary.

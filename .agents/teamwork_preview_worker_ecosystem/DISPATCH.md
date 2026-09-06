# Dispatch for Ecosystem Worker

You are teamwork_preview_worker_ecosystem.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_ecosystem
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md
Project Scope: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_3/PROJECT.md
Explorer 2 Survey Report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_2/survey_report.md
Explorer 3 Survey Report: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3/survey_report.md

## 2026-09-03T16:53:16Z
You are teamwork_preview_worker_ecosystem.
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_ecosystem
Original Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (read section ## 2026-09-03T16:45:06Z).
Project Scope: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_3/PROJECT.md
Survey Reports:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_2/survey_report.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey_3/survey_report.md

File Ownership:
You EXCLUSIVELY own files under assets/blender_map/ (e.g. terrain_hydrology.py, flora_generator.py, fauna_generator.py, assemble_ecosystem.py, verify_ecosystem.py, ecosystem_map.blend, ecosystem_map.glb, render_preview.png).
Do NOT modify tests/ or files outside assets/blender_map/.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Mission:
1. Read ORIGINAL_REQUEST.md, PROJECT.md, and the two survey reports. They contain verified mathematical formulas, bmesh algorithms, armature hierarchies, shader node setups, and export options tested for Blender 5.2.1 LTS on macOS Apple Silicon.
2. Implement the modular procedural pipeline under assets/blender_map/:
   - `terrain_hydrology.py`:
     * 200m x 200m grid, delta Z >= 15m (alpine ridges, rolling hills, valley floor, lake basin).
     * Continuous winding river spline carving into lake basin.
     * Hydrological meshes: `Water_River` and `Water_Lake`.
     * Water PBR shader: transmission weight 0.92, IOR 1.333, micro-ripples bump, blended transparency.
     * Terrain PBR shader: elevation & slope blending via Color Attribute `COLOR_0` (rock, soil, grass, sand) + micro-noise for high-res render.
   - `flora_generator.py`:
     * 4 distinct species: Alpine Pine (`Flora_Conifer`), Lowland Oak (`Flora_Broadleaf`), Marsh Cattail (`Flora_Reed`), Water Lily (`Flora_Lily`).
     * All polygon faces have `polygon.use_smooth = True` (or `mesh.shade_smooth()`).
     * Natural biome-based distribution (elevation, slope normal, water proximity), random rotation/scale.
     * Linked duplicate instancing for compact, fast GLB export.
   - `fauna_generator.py`:
     * 2 distinct species across 2 tiers: Highland Red Stag (quadruped herbivore with antlers) and Golden Eagle (avian raptor with wings).
     * Smooth quad-dominant topology, `polygon.use_smooth = True`.
     * Skeletal bone armatures with complete hierarchies and vertex group skinning.
     * Active animation actions with keyframes: Idle cycle (breathing/posture) and Locomotion cycle (4-beat walk for stag, flap/soar for eagle).
     * Dual animation architecture: active action on armature for viewport + NLA tracks pushdown for multi-clip glTF/GLB export.
   - `assemble_ecosystem.py`:
     * Assembles scene into 6 collections: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, `Camera`.
     * Atmospheric lighting (Sun energy=4.5, warm angle + Nishita Sky dome texture).
     * Scenic camera framing the ecosystem.
     * Saves self-contained `assets/blender_map/ecosystem_map.blend`.
     * Exports optimized `assets/blender_map/ecosystem_map.glb` (ensuring size > 100 KB with embedded meshes, materials, armatures, animations).
   - `verify_ecosystem.py`:
     * In-blender automated verification script checking all requirements and acceptance criteria.
     * Renders high-resolution `assets/blender_map/render_preview.png` via headless Blender EEVEE/Cycles.
3. Execute the generator using the headless Blender binary:
   `/Applications/Blender.app/Contents/MacOS/Blender -b --python /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/assemble_ecosystem.py`
4. Execute verification and render:
   `/Applications/Blender.app/Contents/MacOS/Blender -b /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/ecosystem_map.blend --python /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map/verify_ecosystem.py`
5. Verify that all 3 deliverables are created:
   - `assets/blender_map/ecosystem_map.blend`
   - `assets/blender_map/ecosystem_map.glb` (check `ls -l`, size MUST be > 100 KB)
   - `assets/blender_map/render_preview.png`
6. Write your handoff report to /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_worker_ecosystem/handoff.md documenting exact build/test commands and output. Notify the orchestrator via send_message.

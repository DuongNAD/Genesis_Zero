## 2026-09-05T06:05:14Z
You are worker_creatures_3d.
Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_creatures_3d.
Workspace root: /Users/duongnad/Documents/project/Genesis_Zero.
Mandatory reading:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (MUST read first)
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_7/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_rep_1/handoff.md (species specs & traits)
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_rep_2/handoff.md (3D generator, rigging & baking blueprint)

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your Mission:
Implement the master procedural 3D fauna generation script scripts/generate_photorealistic_creatures.py and run it via Blender headless /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/generate_photorealistic_creatures.py to generate and export all assets for all 10 target species:
sand_skink, snow_ferret, alpine_ibex, meadow_hare, marsh_croc, abyssal_hunter, storm_eagle, giant_tarantula, armored_sentinel, carnivore_apex.

Key Deliverables:
1. scripts/generate_photorealistic_creatures.py:
   - Procedural BMesh generation for all 10 species:
     Guarantees 100% clean manifold mesh: 0 loose vertices, 0 incontiguous edges, 0 ngons (>4 vertices, use quad loops and polar triangle fans), 100% smooth shading (poly.use_smooth = True).
   - Hierarchical Armature:
     Root -> Pelvis -> Spine -> Chest -> Neck -> Head -> Jaw, with limb chains (Upper -> Fore -> Paw/Claw), tail segments, wings (Wing_Shoulder -> Wing_Arm -> Wing_Forearm -> Wing_Hand) for eagle, fins for abyssal hunter, and 8 legs for tarantula.
     Assign vertex groups with smooth bone falloff weights and add ArmatureModifier.
   - 8 Action Animation Clips:
     Keyframe distinct animations for:
     Idle_Normal (breathing, eye blinking, subtle head/tail movements),
     Idle_Alert (perked ears/posture, rapid scan),
     Walk (natural alternating stride cycle),
     Run (high-speed gallop/flight/swimming cycle),
     Attack (lunge, bite, claw strike or venom sting),
     Hurt_Defend (recoil, flinch, shell tuck),
     Eat (head dip, jaw mastication),
     Death (spasm, slump, collapse).
     Push each action into a distinct NLA track on the armature: arm_obj.animation_data.nla_tracks.new().
   - Bio-PBR Principled BSDF Shaders:
     Subsurface Scattering (ears, throat, soft tissue), procedural bump/roughness (scales, fur, carapace, skin), and dual-layer specular eyes with dark pupils.
   - 4-Angle Turnaround Studio Rendering:
     Render 4 camera views per species: Perspective 3/4 Hero, Front Ortho, Side Ortho, Top-Down Ortho.
     Composite them into a standardized turnaround sheet and save to:
     web/creature_images/<species>_turnaround.jpg AND docs/creatures/images/<species>_turnaround.jpg.
   - Export Deliverables:
     Save .blend file to assets/creatures/<species>.blend.
     Export .glb (glTF 2.0) with embedded skeleton and baked NLA action clips to assets/creatures/<species>.glb.
     (Also create copies/aliases for simulation compatibility: creature_L1_s1.glb .. creature_L5_s1.glb, creature_W1_s1.glb, creature_A1_s1.glb, creature_L1_Evo_s1.glb).
   - Update docs/creatures/README.md with catalog table, taxonomy, traits, and image links.

2. Run the script via /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/generate_photorealistic_creatures.py and verify that all 10 .blend, 10 .glb, and 20 turnaround images are generated without error.

Deliverables:
- Keep progress.md updated.
- Write handoff.md in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_creatures_3d/handoff.md with commands run and full verification output.
- Send message to caller when complete.

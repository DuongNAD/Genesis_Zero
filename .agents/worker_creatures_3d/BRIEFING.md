# BRIEFING — 2026-09-05T06:05:30Z

## Mission
Implement scripts/generate_photorealistic_creatures.py and generate photorealistic 3D rigged, animated, shaded assets with 4-angle turnaround sheets for all 10 target species via Blender headless.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_creatures_3d
- Original parent: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Milestone: Procedural 3D Fauna Generation

## 🔒 Key Constraints
- Procedural BMesh generation for 10 species: clean manifold mesh (0 loose verts, 0 incontiguous edges, 0 ngons >4 verts, 100% smooth shading).
- Hierarchical Armature: Root -> Pelvis -> Spine -> Chest -> Neck -> Head -> Jaw, limbs, tails, wings, fins, 8 legs.
- Smooth bone falloff weights and ArmatureModifier.
- 8 distinct Action Animation Clips pushed to distinct NLA tracks.
- Bio-PBR Principled BSDF shaders (SSS, procedural bump/roughness, specular eyes).
- 4-angle turnaround composite sheets (Perspective 3/4, Front Ortho, Side Ortho, Top-Down Ortho) to web/creature_images/<species>_turnaround.jpg and docs/creatures/images/<species>_turnaround.jpg.
- Export .blend and .glb for all 10 species, plus simulation aliases.
- Update docs/creatures/README.md with catalog table, taxonomy, traits, images.
- Integrity: DO NOT CHEAT. All implementations genuine.

## Current Parent
- Conversation ID: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Updated: 2026-09-05T06:05:30Z

## Task Summary
- **What to build**: Master procedural 3D fauna generator `scripts/generate_photorealistic_creatures.py` and all generated assets.
- **Success criteria**: 10 .blend, 10 .glb (+ aliases), 20 turnaround images, updated docs/creatures/README.md.
- **Interface contracts**: PROJECT.md, explorer_survey_rep_1/handoff.md, explorer_survey_rep_2/handoff.md.

## Change Tracker
- **Files modified**: None yet
- **Build status**: Pending
- **Pending issues**: None

## Quality Status
- **Build/test result**: Pending
- **Lint status**: Clean
- **Tests added/modified**: Verification script and Blender headless run

## Loaded Skills
- None

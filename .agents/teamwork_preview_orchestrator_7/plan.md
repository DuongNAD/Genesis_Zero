# Master Execution Plan: Photorealistic Creature Ecosystem Overhaul

## 1. Objectives & Scope
Upgrade 10 core Genesis Zero species to photorealistic scan-quality:
- Land: Sand Skink (`sand_skink`), Snow Ferret (`snow_ferret`), Alpine Ibex (`alpine_ibex`), Meadow Hare (`meadow_hare`), Marsh Croc (`marsh_croc`)
- Water: Abyssal Hunter / Leviathan (`abyssal_hunter` / `leviathan`)
- Air: Storm Eagle (`storm_eagle`)
- Special & Evolutionary: Giant Tarantula (`giant_tarantula`), Armored Sentinel (`armored_sentinel`), Carnivore Apex / L1_Evo (`carnivore_apex` / `l1_evo`)

## 2. Deliverables Checklist
- [ ] R1: Clean manifold BMesh (0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading) with .blend and .glb for all target species in `assets/creatures/`.
- [ ] R2: Hierarchical Armature and 8 action clips (`Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death`) baked into NLA tracks in glTF 2.0 (`.glb`).
- [ ] R3: Organic PBR shaders (Subsurface Scattering, Bump/Roughness, cornea/specular eyes).
- [ ] R4: 4-Angle Concept Turnaround Sheets (Perspective 3/4, Front, Side, Top-Down) in `web/creature_images/<species>_turnaround.jpg` and `docs/creatures/images/<species>_turnaround.jpg`.
- [ ] R5: Interactive 3D Web Viewer in `web/creature_viewer.html` (species selector, 8-anim controller, playback speed, skeleton overlay, traits/features lookup, turnaround modal, offline zero-CORS).
- [ ] R6: Verification suite: `scripts/verify_creatures_pipeline.py` and `pytest tests/test_creature_assets.py` passing 100% (exit code 0).

## 3. Workflow Steps & Phasing
- Phase 0: Survey & Scope Mapping (3 Explorers / Spec Miner)
- Phase 1: PROJECT.md Architecture & TEST_INFRA.md Design
- Phase 2: Dual Track Execution
  - Track A: E2E Test Suite (`tests/test_creature_assets.py` & `scripts/verify_creatures_pipeline.py`)
  - Track B: High-fidelity Modeling & Procedural Mesh/PBR/Rig/Anim Generator script
- Phase 3: Generation & Baking of 3D Assets (.blend, .glb with NLA tracks)
- Phase 4: Turnaround Sheets Render & Export
- Phase 5: Web Viewer UI/UX Implementation & Offline Zero-CORS Data embedding
- Phase 6: Dual-track Verification, Multi-Reviewer, Adversarial Challenger & Forensic Integrity Audit
- Phase 7: Gate Evaluation & Completion Handoff

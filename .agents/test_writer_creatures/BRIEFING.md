# BRIEFING — 2026-09-05T06:05:30Z

## Mission
Implement the complete, rigorous, independent verification test suite for the 10 target species (`scripts/verify_creatures_pipeline.py` and `tests/test_creature_assets.py`), and publish `TEST_READY.md`.

## 🔒 My Identity
- Archetype: test_writer
- Roles: specialist, qa
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/test_writer_creatures
- Original parent: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Milestone: Creatures Test Suite Creation

## 🔒 Key Constraints
- Write and modify test code and verification scripts only — never implementation code. Escalate any bugs.
- 10 target species: sand_skink, snow_ferret, alpine_ibex, meadow_hare, marsh_croc, abyssal_hunter, storm_eagle, giant_tarantula, armored_sentinel, carnivore_apex.
- 6 verification dimensions:
  1. Taxonomy & Metadata
  2. Turnaround Images (SOI/EOI, dimensions, size > 20KB)
  3. 3D Model deliverables (.blend magic BLEN/zstd, .glb magic glTF v2)
  4. glTF 2.0 Skinning & 8-Animation Verification (Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death)
  5. Headless Blender BMesh Manifold Verification (0 loose vertices, 0 non-manifold edges, 0 ngons, 100% smooth)
  6. Web Viewer Sync (HTML references 10 species, creature_models_data.js matches sha256)
- Keep progress.md updated.
- Create handoff.md in working directory.
- Publish TEST_READY.md at project root.

## Current Parent
- Conversation ID: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Updated: 2026-09-05T06:05:30Z

## Task Summary
- **What to build**: `scripts/verify_creatures_pipeline.py`, `tests/test_creature_assets.py`, `TEST_READY.md`.
- **Success criteria**: All 6 verification dimensions pass cleanly, CLI exits 0 with ASCII/color report, pytest passes all tests.
- **Interface contracts**: PROJECT.md, TEST_INFRA.md, explorer handoff.md.
- **Code layout**: Scripts in `scripts/`, tests in `tests/`.

## Loaded Skills
- None loaded yet.

## Quality Status
- **Build/test result**: Initializing
- **Lint status**: 0 violations
- **Tests added/modified**: Pending creation

## Key Decisions Made
- Starting investigation of mandatory reading files and existing assets.

## Artifact Index
- `scripts/verify_creatures_pipeline.py` — Standalone CLI validation script
- `tests/test_creature_assets.py` — Pytest test suite for creature assets
- `TEST_READY.md` — Test suite publication at project root

# BRIEFING — 2026-09-03T07:13:35Z

## Mission
Apply the verified carrying capacity and offspring mortality remediation to `genesis/creature.py` and `genesis/tick.py`, verify with pytest and ruff, and ensure 100% test pass rate across the repository.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen3
- Original parent: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Milestone: M1_EVO Remediation

## 🔒 Key Constraints
- DO NOT CHEAT. All implementations must be genuine.
- DO NOT hardcode test results or create dummy/facade implementations.
- Preserve founder creature rebirth while ensuring offspring mortality upon death.
- Strictly enforce POPULATION_GLOBAL_MAX (35) and POPULATION_SPECIES_MAX (7) during respawn.
- Prune dead non-reincarnating offspring without pruning founders.
- Ensure 100% pytest pass rate across the entire test suite.
- Ensure ruff check passes with zero lint violations.

## Current Parent
- Conversation ID: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Updated: 2026-09-03T07:07:38Z

## Task Summary
- **What to build**: Update `kill()` and `try_respawn()` in `genesis/creature.py`; update Phase 5 respawn loop and dead offspring pruning in `genesis/tick.py`.
- **Success criteria**: All 4 tests in `tests/test_evolution_adversarial.py` pass; all 31 tests in `tests/test_evolution.py` and `tests/test_adversarial_m1_evo_2.py` pass; 100% pytest pass across repo; zero ruff errors.
- **Interface contracts**: PROJECT.md, TEST_READY.md, DISPATCH.md
- **Code layout**: genesis/creature.py, genesis/tick.py

## Key Decisions Made
- Offspring mortality: `dead_until = -1` when `c.parent_id is not None`.
- Founder respawn: `dead_until = tick + config.RESPAWN_DELAY` when `c.parent_id is None`.
- `try_respawn()`: Reject respawn if `c.parent_id is not None` or if global/species caps are reached.
- Phase 5 in `tick.py`: Track incremental living counts during respawns to guarantee caps; prune dead non-reincarnating offspring (`c.parent_id is None or c.alive or c.dead_until >= 0`).

## Artifact Index
- DISPATCH.md — Assignment from orchestrator
- BRIEFING.md — Worker persistent memory
- progress.md — Liveness heartbeat and progress tracker
- handoff.md — 5-component handoff report

## Change Tracker
- **Files modified**:
  - `genesis/creature.py`: Updated `kill()` to assign `dead_until = -1` for offspring; updated `try_respawn()` with `creatures` pool check against global (35) and species (7) caps, preventing offspring respawn.
  - `genesis/tick.py`: Updated Phase 5 to track `alive_count` and `sp_counts` dynamically before calling `try_respawn()`; added post-tick pruning for dead non-reincarnating offspring preserving founders.
- **Build status**: PASS (100% test pass rate across 933 tests)
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (tests/test_evolution_adversarial.py 4/4; full repo 933/933 passed, 1 skipped)
- **Lint status**: Zero violations on affected files (`ruff check genesis/creature.py genesis/tick.py`)
- **Tests added/modified**: Verified all adversarial carrying capacity and multi-generational tests

## Loaded Skills
- None

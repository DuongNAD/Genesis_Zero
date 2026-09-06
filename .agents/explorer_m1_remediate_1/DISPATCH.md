# Remediation Task: Milestone M1_EVO — Carrying Capacity Remediation Strategy

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Forensic Auditor Full Report (INTEGRITY VIOLATION): `/Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m1_evo_1/handoff.md`
- Reviewer 1 Full Report (REQUEST_CHANGES): `/Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_1/handoff.md`
- Challenger 1 Full Report (REQUEST_CHANGES): `/Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_1/handoff.md`
- Adversarial Test Suite with Failing Tests: `tests/test_evolution_adversarial.py`

## Problem Statement
The Forensic Auditor and Challengers identified that multi-generational simulation violates carrying capacity:
- Active population exceeds `POPULATION_GLOBAL_MAX = 35` (reaching 50–56 organisms).
- Species population exceeds `POPULATION_SPECIES_MAX = 7` (reaching 8–15 organisms).
- Root Cause:
  1. In `genesis/creature.py:kill`, deceased newborn offspring (`generation > 0` or `parent_id is not None`) are assigned a respawn timer (`dead_until = tick + RESPAWN_DELAY`), making them immortal and reincarnating indefinitely alongside new births.
  2. In `genesis/creature.py:try_respawn`, reviving entities does not check carrying capacity (`POPULATION_GLOBAL_MAX` and `POPULATION_SPECIES_MAX`).
  3. `tests/test_evolution_adversarial.py` fails 2 tests.

## Your Task
Investigate `genesis/creature.py`, `genesis/evolution.py`, `genesis/tick.py`, and `tests/test_evolution_adversarial.py`.
Recommend a concrete, non-circumventing fix strategy:
- How should offspring mortality be structured (`c.dead_until = -1` for non-founder offspring)?
- How should `try_respawn()` and `can_reproduce()` strictly enforce both global (35) and species (7) ceilings?
- How should dead offspring be pruned or filtered from active tick loops to prevent entity list accumulation?
- How to ensure 100% test pass across all unit, adversarial, and legacy suites.

Produce your fix recommendation in `analysis.md` and `handoff.md`.

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
Investigate the exact test requirements in `tests/test_evolution_adversarial.py`, `tests/test_evolution.py`, and `tests/test_adversarial_m1_evo_2.py`.
Synthesize the optimal, minimal code diff that satisfies:
1. `tests/test_evolution_adversarial.py` passing 100%.
2. All 901+ existing repository tests passing 100%.
3. Absolute carrying capacity conservation across 10,000 continuous simulation ticks.

Produce your fix recommendation in `analysis.md` and `handoff.md`.

## 2026-09-03T06:48:26Z
You are Remediation Explorer 3 for Milestone M1_EVO.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_3
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_3/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m1_evo_1/handoff.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_1/handoff.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_1/handoff.md

Synthesize the optimal, minimal code diff that satisfies tests/test_evolution_adversarial.py and all existing test suites without regression. Deliver analysis.md and handoff.md, then notify parent.

# Review Task: Milestone M1_EVO — Reviewer 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md`

## Focus Areas
Examine the implementation of Milestone M1_EVO:
- `genesis/creature.py`
- `genesis/evolution.py`
- `genesis/tick.py`
- `genesis/domain.py`
- `genesis/world.py`
- `tests/test_evolution.py`

Verify:
1. Interface conformance: `world.passable` checking individual `creature.kit or world.kits.get(creature.species)`.
2. Regression analysis: Ensure legacy tests (`test_trait_shift.py`, `test_maps.py`, `test_score.py`, `test_llm_tick.py`) pass cleanly without unintended side effects.
3. Code layout & cleanliness: Verify against `PROJECT.md § Code Layout` and ensure zero lint/style regressions.
4. Execute tests: Run `pytest tests/test_evolution.py -v` and `pytest tests/test_trait_shift.py tests/test_score.py tests/test_maps.py -v`.
5. Deliver verdict: Write `APPROVE` or `REQUEST_CHANGES` in your `handoff.md` and notify parent.

## 2026-09-03T06:37:12Z
You are Reviewer 2 for Milestone M1_EVO (Generational Evolution & Mutation).
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md

Review interface conformance, regression prevention in legacy tests, and code quality. Execute tests (`pytest tests/test_evolution.py tests/test_trait_shift.py tests/test_score.py tests/test_maps.py -v`). Deliver your verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

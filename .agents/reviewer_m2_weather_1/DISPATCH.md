# Review Task: Milestone M2_WEATHER — Reviewer 1

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## Focus Areas
Review the implementation of Milestone M2_WEATHER:
1. Determinism and isolation: Verify that `weather_at(seed, tick_no)` in `genesis/weather.py` is pure seed-deterministic and does not mutate or consume from `world.rng`.
2. Simulation modulations: Verify movement stamina cost modulations in `reflex.py` & `creature.py`, sight penalty in `world.py`, and plant/algae growth in `world.py`.
3. Diurnal invariance: Confirm that `phase_at(tick)` remains strictly `"DAY"` or `"NIGHT"`.
4. Run tests: `pytest tests/test_weather.py tests/test_surface.py tests/test_rollout.py -v`.
5. Deliver verdict: `APPROVE` or `REQUEST_CHANGES` in `handoff.md` and notify parent.

## 2026-09-03T07:46:00Z
You are Reviewer 1 for Milestone M2_WEATHER.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m2_weather_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m2_weather_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md

Review determinism and simulation modulations, execute tests (`pytest tests/test_weather.py tests/test_surface.py tests/test_rollout.py -v`), deliver verdict (APPROVE or REQUEST_CHANGES) in handoff.md, and notify parent.

# Adversarial Challenge Task: Milestone M2_WEATHER — Challenger 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## Objectives
Perform empirical adversarial stress testing on the physical modulations of Milestone M2_WEATHER:
1. Physical modifier enforcement: Empirically verify that movement stamina depletion exactly matches `COST_MOVE * move_cost_mult` under all 5 weather conditions (`CLEAR`, `RAIN`, `SPORE_STORM`, `SOLAR_FLARE`, `MAGNETIC_SHIFT`).
2. Sensory perception bounds: Empirically verify that sight radius reduction under `SPORE_STORM` (-2) and `SOLAR_FLARE` (-1) never causes sight radius to drop below 1 or crash `visible()`.
3. Growth rate scaling: Empirically verify that plant and algae candidate spawn counts scale strictly with `plant_mult` and `algae_mult`.
4. Deliver empirical results and verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.

## 2026-09-03T07:45:58Z
You are Challenger 2 for Milestone M2_WEATHER.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m2_weather_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m2_weather_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md

Empirically test physical stamina cost modulations, sensory perception clamping (sight >= 1), and plant/algae scaling. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

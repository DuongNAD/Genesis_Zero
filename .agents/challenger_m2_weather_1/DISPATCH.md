# Adversarial Challenge Task: Milestone M2_WEATHER — Challenger 1

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## Objectives
Perform empirical adversarial stress testing on Milestone M2_WEATHER:
1. Multi-seed determinism fuzzing: Test across 10 distinct world seeds for 500 ticks each to verify that identical `(seed, tick_no)` generates identical weather state and modifier values across independent match runs.
2. Verify that `weather_at` does NOT advance or desynchronize `world.rng` by asserting identical terrain and plant spawn coordinates with and without weather evaluations.
3. Test edge conditions: `tick=0`, transition boundaries `tick=49->50`, `99->100`, and large tick numbers (`tick=10000`).
4. Deliver empirical results and verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.

## 2026-09-03T07:45:58Z
You are Challenger 1 for Milestone M2_WEATHER.
Empirically test multi-seed determinism, transition boundaries, and RNG stream isolation. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

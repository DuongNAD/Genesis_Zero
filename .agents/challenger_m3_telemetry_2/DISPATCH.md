# Adversarial Challenge Task: Milestone M3_TELEMETRY — Challenger 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M3_TELEMETRY Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md`

## Objectives
Perform empirical adversarial stress testing on the REST history endpoint and schema edge cases:
1. `GET /v1/spectate/history` stress: Test rapid polling across 200 simulation ticks, testing `max_frames=0`, `max_frames=1`, `max_frames=2000`, and `max_frames=5000` (expecting 422 Unprocessable Entity).
2. Phase transition safety: Verify history output during phase transitions (`LOBBY` -> `RUNNING` -> `REVEAL`), ensuring full law text is disclosed ONLY during `REVEAL`/`COOLDOWN`.
3. Malformed creature & event stress: Feed duck-typed creature objects and abnormal event dictionaries into `MatchRunner.frame()` to verify defensive `getattr` fallback behavior.
4. Deliver empirical results and verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.

## 2026-09-03T08:06:31Z
You are Challenger 2 for Milestone M3_TELEMETRY.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m3_telemetry_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m3_telemetry_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md

Perform adversarial stress testing on the REST history endpoint, phase transitions, and duck-typed creatures. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

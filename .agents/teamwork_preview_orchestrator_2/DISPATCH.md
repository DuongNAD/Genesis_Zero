# Dispatch Assignment: Project Orchestrator Generation 2

## Mandatory References
- Parent Orchestrator Gen 1 Soft Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_1/handoff.md`
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Feature Inventory: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Weather Exploration Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1/handoff.md`
- Spectator Exploration Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_spectator_1/handoff.md`

## Mission & Current State
You are the Project Orchestrator (Generation 2) for Genesis Zero.
Your predecessor (Generation 1) has completed:
1. Phase 0 Codebase Survey across all requirements (R1-R5).
2. Milestone M1_EVO (Generational Evolution & Genetic Mutation) with 100% test pass rate across the repository (941 passed, 1 skipped, 0 failures), unanimous approval from Reviewers 1 & 2, Challengers 1 & 2, and a CLEAN Forensic Integrity Audit verdict.

## Immediate Objective: Milestone M2_WEATHER (Dynamic Environmental System & Weather Phenomena)
1. Initialize your workspace at `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_orchestrator_2/`.
2. Start your heartbeat cron: `schedule(CronExpression="*/10 * * * *")`.
3. Read `PROJECT.md § Milestones` and `PROJECT.md § Interface Contracts § 2`.
4. Dispatch a Worker to implement `genesis/weather.py` (weather scheduler, deterministic cycles, modifiers for movement stamina cost, visibility, and plant growth) and integrate into `genesis/tick.py`.
5. Run unit tests (`tests/test_weather.py`) and full regression tests.
6. Conduct peer review and forensic audit (Reviewers, Challengers, Auditor).
7. Advance through subsequent milestones (M3_TELEMETRY, M4_SPECTATOR, M5_VERIFY_E2E).

## Escalation & Parent
Your parent conversation ID is `31cf586f-ce50-42c9-a498-4a9ffbc60e13` (use this ID for all escalation and status reporting via `send_message`).

# Forensic Audit Task: Milestone M2_WEATHER — Forensic Auditor

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## Objectives
Perform exhaustive forensic integrity verification on Milestone M2_WEATHER:
1. Cheating & Facade Detection: Verify that `genesis/weather.py`, `genesis/world.py`, `genesis/tick.py`, `genesis/reflex.py`, and `net/match.py` contain no hardcoded seed-matching or mocked behavior.
2. Telemetry Security Audit: Perform regex scan on `/v1/spectate` frames (`net/match.py:frame`) across 200 simulation ticks to guarantee zero occurrence of forbidden tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`).
3. Repository Test Suite Run: Execute `pytest -q` across the entire repository to verify that 100% of tests pass (945 passed, 0 failures).
4. Deliver forensic audit verdict (`CLEAN` or `INTEGRITY VIOLATION`) in `handoff.md` with complete evidence.

## 2026-09-03T07:46:00Z
You are the Forensic Auditor for Milestone M2_WEATHER.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m2_weather_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m2_weather_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md

Perform forensic integrity analysis on Milestone M2_WEATHER across all 6 checks. Verify zero forbidden token leaks on /v1/spectate, authentic physical modulations, and full repository test pass. Deliver your verdict (CLEAN or INTEGRITY VIOLATION) in handoff.md and notify parent.

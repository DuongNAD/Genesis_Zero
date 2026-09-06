# Forensic Audit Task: Milestone M3_TELEMETRY — Forensic Auditor

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M3_TELEMETRY Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md`

## Objectives
Perform exhaustive forensic integrity verification on Milestone M3_TELEMETRY:
1. Cheating & Facade Detection: Verify `net/routes_spectate.py`, `net/match.py`, and `tests/test_telemetry_extension.py` contain no mocked responses, bypassed checks, or hardcoded seed returns.
2. Information Leak Audit: Perform regex scan across all frames returned by `/v1/spectate` and `/v1/spectate/history` in `RUNNING` phase across 100 ticks, verifying 0 forbidden token occurrences (`law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`).
3. Full Repository Test Execution: Run `pytest -q` across the entire repository to ensure 100% pass rate.
4. Deliver forensic audit verdict (`CLEAN` or `INTEGRITY VIOLATION`) in `handoff.md`.

## 2026-09-03T08:06:31Z
Perform forensic integrity analysis across all 6 checks on Milestone M3_TELEMETRY. Run regex leak scan across 100 ticks and full repository pytest suite. Deliver verdict (CLEAN or INTEGRITY VIOLATION) in handoff.md and notify parent.


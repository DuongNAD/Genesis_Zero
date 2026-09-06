# Review Task: Milestone M3_TELEMETRY — Reviewer 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M3_TELEMETRY Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md`

## Focus Areas
Review security and backward compatibility of Milestone M3_TELEMETRY:
1. Zero Law Leakage Invariant: Verify that neither `/v1/spectate` nor `/v1/spectate/history` leak forbidden tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`) during `RUNNING` phase.
2. Backward Compatibility: Verify that existing clients parsing standard frame fields (`t`, `phase`, `creatures`, `plants`, `corpses`, `events`, `terrain`) continue to function without errors.
3. Referee scoring isolation: Confirm zero simulation imports in `genesis/score.py`.
4. Run tests: `pytest tests/test_telemetry_extension.py tests/test_no_law_leak.py tests/test_score.py -v`.

## 2026-09-03T08:06:31Z
You are Reviewer 2 for Milestone M3_TELEMETRY.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m3_telemetry_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m3_telemetry_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md

Review security, backward compatibility, and referee scoring isolation. Execute tests (`pytest tests/test_telemetry_extension.py tests/test_no_law_leak.py tests/test_score.py -v`), deliver verdict (APPROVE or REQUEST_CHANGES) in handoff.md, and notify parent.

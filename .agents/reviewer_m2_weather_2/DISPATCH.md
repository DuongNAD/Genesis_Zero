# Review Task: Milestone M2_WEATHER — Reviewer 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## Focus Areas
Review the telemetry and regression prevention in Milestone M2_WEATHER:
1. Telemetry security & backward compatibility: Verify that `net/match.py:frame()` includes `"weather"` dictionary without leaking any forbidden tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`).
2. Referee isolation & scoring: Verify that referee scoring (`genesis/score.py`) remains 100% compliant with zero simulation imports.
3. Run tests: `pytest tests/test_weather.py tests/test_spectate.py tests/test_no_law_leak.py tests/test_score.py -v`.
4. Deliver verdict: `APPROVE` or `REQUEST_CHANGES` in `handoff.md` and notify parent.

## 2026-09-03T07:45:58Z
You are Reviewer 2 for Milestone M2_WEATHER.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m2_weather_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m2_weather_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md

Review telemetry schema and referee scoring isolation, execute tests (`pytest tests/test_weather.py tests/test_spectate.py tests/test_no_law_leak.py tests/test_score.py -v`), deliver verdict (APPROVE or REQUEST_CHANGES) in handoff.md, and notify parent.

# Review Task: Milestone M3_TELEMETRY — Reviewer 1

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M3_TELEMETRY Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md`

## Focus Areas
Review the telemetry extensions in `net/routes_spectate.py` and `net/match.py`:
1. Replay backlog & queue capacity: Verify `QUEUE_MAX = 1000` and `backlog_size` query parameter in `/v1/spectate`.
2. REST history endpoint: Verify `GET /v1/spectate/history` with `max_frames` in `LOBBY`, `RUNNING`, and `REVEAL` phases.
3. Schema conformance: Verify `weather`, creature lineage (`gen`, `parent_id`, `lineage`, `d_tr`), and `REPRODUCE`/`EXTINCTION` events.
4. Run tests: `pytest tests/test_telemetry_extension.py tests/test_spectate.py -v`.
5. Deliver verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md` and notify parent.

## 2026-09-03T08:06:31Z
You are Reviewer 1 for Milestone M3_TELEMETRY.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m3_telemetry_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m3_telemetry_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/handoff.md

Review telemetry extensions in net/routes_spectate.py and net/match.py, execute tests (`pytest tests/test_telemetry_extension.py tests/test_spectate.py -v`), deliver verdict (APPROVE or REQUEST_CHANGES) in handoff.md, and notify parent.


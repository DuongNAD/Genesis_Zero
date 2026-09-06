# Dispatch Assignment: Milestone M3_TELEMETRY (Telemetry Extension & Backward Compatibility)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M2_WEATHER Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Objectives
1. `net/routes_spectate.py`:
   - Expand `QUEUE_MAX` from 256 to 1000 so late joiners or reconnecting spectators receive a deep historical replay buffer up to 1000 frames upon connecting.
   - Add optional query parameter `backlog_size: int = Query(default=QUEUE_MAX, ge=1, le=2000)` in `spectate_ws` allowing clients to request customized replay buffer depth.
   - Add REST endpoint `GET /v1/spectate/history` returning `{"seed": runner.seed, "ticks": runner.tick_no, "phase": str(runner.phase), "frames": runner.frames[-max_frames:]}` (with `max_frames: int = Query(default=500, le=2000)`) for fast historical scrubbing or offline replay without consuming WebSocket streams.
   - Ensure that in `reveal_frames()`, `REVEAL` phase frames continue to reveal public laws without breaking existing contracts.
2. `net/match.py`:
   - Verify that `MatchRunner.frame()` contains:
     - `"weather"` dictionary (`state`, `cycle_tick`, `cycle_len`, `progress`, `diurnal`, `modifiers`).
     - Creature entries contain: `species`, `domain`, `features`, `gen`, `parent_id`, `lineage`, `d_tr`, `age`.
     - Event filters pass `REPRODUCE` (`k="REPRODUCE"`, `child`, `gen`, `pos`) and `EXTINCTION` (`k="EXTINCTION"`, `species`).
   - Verify strict zero-leak invariant: absolutely no forbidden tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`) appear in serialized frames during `RUNNING` phase.
3. Unit & Integration Tests:
   - Create `tests/test_telemetry_extension.py` verifying:
     - Expanded queue capacity (`QUEUE_MAX = 1000`) and backlog delivery.
     - `GET /v1/spectate/history` endpoint behavior in `LOBBY`, `RUNNING`, and `REVEAL` phases.
     - Complete frame schema conformance: weather, creature lineage, events.
     - Zero forbidden token leakage in history endpoint and WebSocket stream.
     - Backward compatibility: existing clients expecting standard frame fields continue to work seamlessly.
   - Verify that `pytest tests/test_spectate.py tests/test_telemetry_extension.py -v` passes 100%.
   - Verify full repository pytest suite passes 100%.
4. Documentation & Verification:
   - Run `ruff check` on modified files.
   - Write comprehensive handoff report to `handoff.md` in your working directory and notify parent via `send_message`.

## 2026-09-03T07:57:46Z
You are Worker M3_TELEMETRY (Telemetry Extension & Backward Compatibility Specialist) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement:
1. `net/routes_spectate.py`: Expand QUEUE_MAX to 1000, add optional backlog_size query parameter, add GET /v1/spectate/history endpoint.
2. `net/match.py`: Verify frame serialization with weather, lineage metadata, reproduction/extinction public events, and zero forbidden token leaks.
3. `tests/test_telemetry_extension.py`: Comprehensive test suite verifying all new telemetry features, backward compatibility, and zero leaks.
4. Run `pytest tests/test_spectate.py tests/test_telemetry_extension.py -v`, full repository `pytest -q`, and `ruff check`.
5. Write handoff report to `handoff.md` in your working directory and notify parent via send_message when done.

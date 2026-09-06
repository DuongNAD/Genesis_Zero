# BRIEFING — 2026-09-03T08:06:00Z

## Mission
Implement Telemetry Extension & Backward Compatibility (Milestone M3_TELEMETRY) for Genesis Zero, including expanded replay buffer, backlog query parameter, historical scrub REST endpoint, rich frame schema (weather, creature lineage, reproduce/extinction events), zero forbidden law leaks, and comprehensive test coverage.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1
- Original parent: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Milestone: M3_TELEMETRY

## 🔒 Key Constraints
- Strict zero-leak invariant: absolutely no forbidden tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`) appear in serialized frames during RUNNING phase.
- Backward compatibility: existing clients expecting standard frame fields continue to work seamlessly.
- DO NOT CHEAT: All implementations genuine, real state, real behavior.
- Clean code layout: `.agents/` holds only metadata.
- 100% test pass rate across pytest suite.

## Current Parent
- Conversation ID: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Updated: 2026-09-03T08:06:00Z

## Task Summary
- **What to build**:
  1. `net/routes_spectate.py`: Expand `QUEUE_MAX` from 256 to 1000, add optional `backlog_size` query param in `spectate_ws`, add `GET /v1/spectate/history` endpoint with `max_frames`.
  2. `net/match.py`: Verify frame serialization with weather, creature lineage metadata (`species`, `domain`, `features`, `gen`, `parent_id`, `lineage`, `d_tr`, `age`), reproduction/extinction public events (`REPRODUCE`, `EXTINCTION`), and zero forbidden token leaks.
  3. `tests/test_telemetry_extension.py`: Comprehensive test suite verifying new telemetry features, backward compatibility, and zero leaks.
- **Success criteria**: All tests in `tests/test_spectate.py` and `tests/test_telemetry_extension.py` pass; full repo pytest passes 100%; ruff check clean; zero law leak.
- **Interface contracts**: PROJECT.md § 3. WebSocket Telemetry Schema
- **Code layout**: `net/routes_spectate.py`, `net/match.py`, `tests/test_telemetry_extension.py`

## Key Decisions Made
- Replay queue capacity expanded to 1000 with per-client `backlog_size` query parameter (default 1000, clamped `1 <= backlog_size <= 2000`).
- History endpoint `GET /v1/spectate/history` provides instant snapshot of recent frames up to `max_frames` (default 500, max 2000, 422 if >2000), switching between `runner.frames` (in LOBBY/RUNNING) and `runner.reveal_frames()` (in REVEAL/COOLDOWN).
- Creature telemetry fortified with defensive attribute access (`getattr(c, "generation", 0)`, `getattr(c, "parent_id", None)`, etc.) to guarantee backwards-compatibility with duck-typed objects.
- Public event filters preserve `REPRODUCE` (`k`, `who`, `child`, `gen`, `pos`) and `EXTINCTION` (`k`, `who`, `species`) with zero token leak.

## Artifact Index
- `.agents/worker_m3_telemetry_1/DISPATCH.md` — Assignment instructions
- `.agents/worker_m3_telemetry_1/BRIEFING.md` — Situational awareness
- `.agents/worker_m3_telemetry_1/progress.md` — Execution progress & heartbeat
- `.agents/worker_m3_telemetry_1/handoff.md` — Final handoff report
- `tests/test_telemetry_extension.py` — 14 new integration & regression tests

## Change Tracker
- **Files modified**:
  - `net/routes_spectate.py`: Expanded `QUEUE_MAX=1000`, added `GET /v1/spectate/history`, added `backlog_size` query parameter to `spectate_ws`.
  - `net/match.py`: Fortified creature serialization and public event filter in `frame()`.
  - `tests/test_telemetry_extension.py`: Created test suite with 14 comprehensive tests.
  - `PROJECT.md`: Updated milestone status table to mark M3_TELEMETRY complete.
- **Build status**: PASS (27/27 spectate/telemetry tests, 959 passed full repo, ruff check clean).
- **Pending issues**: None

## Quality Status
- **Build/test result**: PASS (100% pass across full test suite)
- **Lint status**: 0 violations (clean `ruff check`)
- **Tests added/modified**: `tests/test_telemetry_extension.py` (+14 tests)

## Loaded Skills
None

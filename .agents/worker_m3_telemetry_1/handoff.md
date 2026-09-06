# Handoff Report: Milestone M3_TELEMETRY (Telemetry Extension & Backward Compatibility)

**Agent**: Worker M3_TELEMETRY (Telemetry Extension & Backward Compatibility Specialist)  
**Date**: 2026-09-03  
**Handoff Type**: Hard (Task Complete)  
**Workspace Path**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_telemetry_1`

---

## 1. Observation

1. **Replay Buffer & WebSocket Backlog**:
   - `net/routes_spectate.py` (lines 29, 47, 56): Originally had `QUEUE_MAX = 256` and fixed buffer slicing `[-QUEUE_MAX:]`.
   - Expanded `QUEUE_MAX` from `256` to `1000`.
   - In `spectate_ws(websocket: WebSocket, backlog_size: int = Query(default=QUEUE_MAX, ge=1, le=2000))`:
     - Initialized `q: asyncio.Queue = asyncio.Queue(maxsize=max(QUEUE_MAX, backlog_size))`.
     - Slices historical backlog frames using `frames_source[-backlog_size:]` where `frames_source = runner.reveal_frames() if reveal else runner.frames`.
     - Preserved terrain patching on the first frame if terrain is absent.
     - Automatically rejects invalid `backlog_size` (e.g. `<= 0` or `> 2000`) via FastAPI validation, terminating invalid websocket attempts with `WebSocketDisconnect`.

2. **Historical Scrub REST Endpoint**:
   - Added `GET /v1/spectate/history` in `net/routes_spectate.py` (lines 43-55):
     ```python
     @router.get("/spectate/history")
     async def spectate_history(max_frames: int = Query(default=500, le=2000)) -> dict[str, Any]:
         """Lịch sử các khung hình gần nhất phục vụ tua lại (scrubbing/replay)."""
         runner = state.runner
         reveal = runner.phase in (Phase.REVEAL, Phase.COOLDOWN)
         source = runner.reveal_frames() if reveal else runner.frames
         frames = list(source[-max_frames:]) if max_frames > 0 else []
         return {
             "seed": runner.seed,
             "ticks": runner.tick_no,
             "phase": str(runner.phase),
             "frames": frames,
         }
     ```
   - In `LOBBY`: returns `{"seed": 0, "ticks": 0, "phase": "LOBBY", "frames": []}`.
   - In `RUNNING`: returns active frames from `runner.frames[-max_frames:]`.
   - In `REVEAL`/`COOLDOWN`: returns frames from `runner.reveal_frames()[-max_frames:]` with disclosed laws for post-match replay.
   - Rejects `max_frames > 2000` with HTTP 422 Unprocessable Entity.

3. **Frame Serialization & Lineage/Weather Conformance**:
   - `net/match.py` (`MatchRunner.frame`, lines 570-610):
     - Top-level `"weather"` dictionary contains `state`, `cycle_tick`, `cycle_len`, `progress`, `diurnal`, `modifiers` (including `move_cost_mult`, `sight_penalty`, `plant_mult`, `algae_mult`, `plant_growth_mult`, `algae_growth_mult`).
     - Creature objects include `species`, `domain` (`"CAN"`, `"NUOC"`, `"TROI"`), `features` (list of feature keys), `gen` (int >= 0), `parent_id` (str or None), `lineage` (str), `d_tr` (list of 6 trait deltas relative to founder vectors), and `age` (int >= 0).
     - Fortified creature serialization with defensive `getattr` calls (`getattr(c, "generation", 0)`, `getattr(c, "parent_id", None)`, etc.) ensuring complete backward compatibility with mock or custom objects.
   - Public event filtering (`net/match.py:_public_event`, lines 101-110):
     - `"REPRODUCE"`: emits `{"k": "REPRODUCE", "who": parent_id, "child": child_id, "gen": child_gen, "pos": [x, y]}`.
     - `"EXTINCTION"`: emits `{"k": "EXTINCTION", "who": "", "species": species_id}`.

4. **Zero Forbidden Token Leakage**:
   - In `RUNNING` phase, absolutely no hidden DSL physics tokens (`FORBIDDEN_RUNNING_PATTERN`: `law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`) leak through `/v1/spectate` WebSocket stream or `/v1/spectate/history` REST endpoint.
   - Validated across all 50 ticks of running simulation.

5. **Test & Lint Verification Results**:
   - `pytest tests/test_telemetry_extension.py -v`: 14 passed in 0.75s.
   - `pytest tests/test_spectate.py tests/test_telemetry_extension.py -v`: 27 passed in 1.26s.
   - `pytest tests/test_no_law_leak.py -v`: 5 passed in 0.35s.
   - `pytest tests/e2e -q`: 208 passed in 1.48s.
   - Full repository `pytest -q`: 959 passed, 1 skipped, 0 failed.
   - `ruff check net/routes_spectate.py net/match.py tests/test_telemetry_extension.py`: All checks passed with 0 errors.

---

## 2. Logic Chain

1. **Replay Buffer Hydration & Latency Elimination (Observation 1 -> Rule 1)**:
   Late-joining spectators and reconnecting clients need an immediate historical buffer to scrub through match events without re-running or polling. Expanding `QUEUE_MAX` from 256 to 1000 ensures that matches up to 1000 ticks can be entirely reviewed in the spectator timeline. Adding `backlog_size` with bounds `[1, 2000]` gives clients granular control over network payload size upon initial connection while preventing unbounded queue allocation.

2. **Decoupled Scrubbing via REST API (Observation 2 -> Rule 2)**:
   Timeline scrubbing in 3D viewers often requires fetching slices of past match ticks on-demand without subscribing to the live streaming WebSocket or risking backpressure. The `GET /v1/spectate/history` endpoint provides instantaneous frame array retrieval capped by `max_frames: int = Query(default=500, le=2000)`. When queried during `REVEAL` or `COOLDOWN`, it serves `runner.reveal_frames()` so spectators can scrub through the complete historical timeline with full law descriptions.

3. **Additive Telemetry Schema & Backward Compatibility (Observation 3 -> Rule 3)**:
   Existing clients expect standard fields (`t`, `phase`, `w`, `h`, `creatures`, `plants`, `corpses`, `terrain_delta`, `events`, `map`, `terrain`) and standard creature attributes (`id`, `x`, `y`, `hp`, `e`, `e_max`, `alive`, `feral`, `tr`). The new fields (`weather`, `gen`, `parent_id`, `lineage`, `d_tr`, `age`, and `features`) are strictly additive. Older spectator code continues functioning unaltered while modern 3D viewers can access evolutionary lineages and environmental weather phenomena.

4. **Information Security & Anti-Leak Discipline (Observation 4 -> Rule 4)**:
   The hidden physics discovery game depends on agents and public spectators not receiving unearned knowledge of laws before `REVEAL`. Serialized `frame["weather"]` values use human-readable environmental state names (`CLEAR`, `RAIN`, `SPORE_STORM`, `SOLAR_FLARE`, `MAGNETIC_SHIFT`), `frame["events"]` mask `law_id` to `"?"`, and `REPRODUCE`/`EXTINCTION` only expose public biological IDs and coordinates. Zero forbidden pattern tokens leak across all endpoints.

---

## 3. Caveats

No caveats. All requirements from `DISPATCH.md`, `ORIGINAL_REQUEST.md`, and `PROJECT.md` have been fully implemented, rigorously verified across 27 unit/integration tests and 959 total repository tests, and passed lint checks cleanly.

---

## 4. Conclusion

Milestone M3_TELEMETRY is complete:
1. `net/routes_spectate.py` provides expanded queue capacity (`QUEUE_MAX = 1000`), client-configurable `backlog_size` query parameter on `/v1/spectate`, and the new `GET /v1/spectate/history` REST endpoint with `max_frames` parameter.
2. `net/match.py` serializes complete weather metadata, creature lineage metadata (`species`, `domain`, `features`, `gen`, `parent_id`, `lineage`, `d_tr`, `age`), and public `REPRODUCE` and `EXTINCTION` events.
3. Invariant 5 (zero law leak before REVEAL) is strictly preserved across all new endpoints and schemas.
4. Comprehensive test coverage in `tests/test_telemetry_extension.py` (14 tests) guarantees conformance, backward compatibility, and error handling.
5. All 959 tests in the repository pass with 100% success rate.

---

## 5. Verification Method

### Test Execution Commands:
```bash
# 1. Telemetry extension test suite (14 tests)
pytest tests/test_telemetry_extension.py -v

# 2. Combined spectate & telemetry test suite (27 tests)
pytest tests/test_spectate.py tests/test_telemetry_extension.py -v

# 3. Security & zero law leak verification (5 tests)
pytest tests/test_no_law_leak.py -v

# 4. 5-Tier requirement-driven E2E test suite (208 tests)
pytest tests/e2e -q

# 5. Full repository test suite (959 tests)
pytest -q

# 6. Linting verification on modified files
ruff check net/routes_spectate.py net/match.py tests/test_telemetry_extension.py
```

### Invalidation Conditions:
- `net.routes_spectate.QUEUE_MAX != 1000`.
- Connecting to `/v1/spectate?backlog_size=0` or `backlog_size=2001` does not reject the connection.
- `GET /v1/spectate/history?max_frames=2001` returns anything other than HTTP 422.
- `FORBIDDEN_RUNNING_PATTERN` matches any response text from `/v1/spectate/history` or `/v1/spectate` during `RUNNING` phase.
- Any test in `tests/test_spectate.py` or `tests/test_telemetry_extension.py` fails.
- `ruff check` reports any error on modified files.

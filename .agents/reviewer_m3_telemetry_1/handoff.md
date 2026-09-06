# Review & Adversarial Challenge Report: Milestone M3_TELEMETRY

**Reviewer**: Reviewer 1 (Roles: Reviewer, Adversarial Critic)  
**Milestone**: M3_TELEMETRY (Telemetry Extension & Backward Compatibility)  
**Date**: 2026-09-03  
**Verdict**: **APPROVE**  
**Integrity Status**: **CLEAN (Zero Integrity Violations)**

---

## 1. Observation

1. **Replay Buffer & Queue Capacity in `net/routes_spectate.py`**:
   - `QUEUE_MAX`: Successfully expanded from `256` to `1000` (line 29).
   - `spectate_ws` endpoint (lines 58-66):
     ```python
     @router.websocket("/spectate")
     async def spectate_ws(
         websocket: WebSocket,
         backlog_size: int = Query(default=QUEUE_MAX, ge=1, le=2000),
     ) -> None:
         await websocket.accept()
         runner = state.runner
         q_size = max(QUEUE_MAX, backlog_size)
         q: asyncio.Queue = asyncio.Queue(maxsize=q_size)
     ```
   - Historical backlog slicing (line 73):
     ```python
     reveal = runner.phase in (Phase.REVEAL, Phase.COOLDOWN)
     frames_source = runner.reveal_frames() if reveal else runner.frames
     backlog = list(frames_source[-backlog_size:])
     ```
   - Terrain patching guarantee on first frame received by connecting client (lines 78-81):
     ```python
     if backlog and not backlog[0].get("terrain"):
         backlog[0] = {**backlog[0], "terrain": runner.terrain_rows()}
     elif not backlog:
         backlog = [runner.frame(runner.tick_no, [])]
     ```
   - Non-blocking push during match step in `net/match.py` (lines 538-540):
     ```python
     for q in list(self.subscribers):
         with contextlib.suppress(Exception):  # hàng đợi đầy: bỏ khung, đừng làm chậm ván
             q.put_nowait(frame)
     ```
   - Subscription lifecycle: Subscriber queues are cleanly unregistered in `finally` block (lines 95-97).

2. **REST Historical Scrub Endpoint (`GET /v1/spectate/history`)**:
   - `net/routes_spectate.py` (lines 43-54):
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
   - In `RUNNING`: returns sliced frames with masked laws (`law: "?"`).
   - In `REVEAL`/`COOLDOWN`: returns sliced frames from `runner.reveal_frames()` with disclosed law definitions.
   - Validation: `max_frames > 2000` returns HTTP 422; `max_frames <= 0` gracefully returns `frames: []`.

3. **Telemetry Frame Schema Conformance in `net/match.py`**:
   - Top-level `"weather"` dictionary (lines 602-606):
     ```python
     "weather": (
         self.world.weather.to_dict(diurnal=getattr(self.world, "phase", "DAY"))
         if (self.world and hasattr(self.world, "weather") and self.world.weather is not None)
         else weather_at(self.seed, tick_no).to_dict(diurnal="DAY")
     ),
     ```
     Contains `state`, `cycle_tick`, `cycle_len`, `progress`, `diurnal`, and `modifiers` (`move_cost_mult`, `sight_penalty`, `plant_mult`, `algae_mult`, `plant_growth_mult`, `algae_growth_mult`).
   - Creature lineage and physical features (lines 583-590):
     ```python
     "species": c.species,
     "domain": config.SPECIES_DOMAIN.get(c.species, "CAN"),
     "features": list(c.features) if getattr(c, "features", ()) else (list(self.world.kits[c.species].keys) if (self.world and hasattr(self.world, "kits") and c.species in self.world.kits) else []),
     "gen": getattr(c, "generation", 0),
     "parent_id": getattr(c, "parent_id", None),
     "lineage": getattr(c, "lineage_id", "") or getattr(c, "id", ""),
     "d_tr": [getattr(c.traits, t, 0) - (config.FOUNDERS[c.species][i] if (hasattr(c, "species") and c.species in config.FOUNDERS) else getattr(c.traits, t, 0)) for i, t in enumerate(config.TRAIT_NAMES)],
     "age": getattr(c, "age", 0),
     ```
   - Public event filtering in `_public_event` (lines 104-110):
     - `REPRODUCE`: `{"k": "REPRODUCE", "who": parent_id, "child": child_id, "gen": child_gen, "pos": [x, y]}`
     - `EXTINCTION`: `{"k": "EXTINCTION", "who": "", "species": species_id}`

4. **Information Security & Anti-Leak Discipline**:
   - Regex scan with `FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")` across both `/v1/spectate` stream and `/v1/spectate/history` in `RUNNING` phase yielded 0 matches.
   - Invariant 1 and 5 (no hidden laws revealed before `REVEAL`) verified.

5. **Independent Test Execution Results**:
   - `pytest tests/test_telemetry_extension.py tests/test_spectate.py -v`: 27 passed in 1.23s.
   - `pytest tests/test_no_law_leak.py -v`: 5 passed in 0.75s.
   - `pytest tests/e2e -q`: 208 passed in 1.48s.
   - Full repository `pytest -q`: 100% passed (959 passed, 1 skipped, 0 failed in 3m 32s).
   - `ruff check net/routes_spectate.py net/match.py tests/test_telemetry_extension.py`: Clean pass (0 errors).

---

## 2. Logic Chain

1. **Queue Capacity Expansion & Late-Joiner Replay (Observation 1 -> Req R4)**:
   By expanding `QUEUE_MAX` from 256 to 1000 and sizing the queue as `max(QUEUE_MAX, backlog_size)`, spectators reconnecting or joining late in matches up to 1000 ticks receive all past match frames without missed history. The use of non-blocking `put_nowait` with suppressed `QueueFull` exceptions ensures that slow consumers never introduce backpressure into the simulation loop, upholding the architectural tenet that presentation must never touch or delay simulation.

2. **Decoupled Timeline Scrubbing via REST (Observation 2 -> Req R3, R4)**:
   3D timeline scrubbing requires arbitrary random access to past frame ranges without consuming WebSocket streaming bandwidth. The endpoint `GET /v1/spectate/history?max_frames=N` provides instant synchronous retrieval of recent frames. Phase-aware source selection correctly switches from `runner.frames` (masked laws) to `runner.reveal_frames()` (disclosed laws) once the match enters `REVEAL`/`COOLDOWN`, allowing full post-match analytical scrub.

3. **Schema Conformance & Backward Compatibility (Observation 3 -> Req R4)**:
   The addition of `weather`, `gen`, `parent_id`, `lineage`, `d_tr`, `features`, and `age` preserves all existing top-level keys (`t`, `phase`, `w`, `h`, `creatures`, `plants`, `corpses`, `terrain_delta`, `events`, `map`, `terrain`) and existing creature keys (`id`, `x`, `y`, `hp`, `e`, `e_max`, `alive`, `feral`, `tr`). Defensive `getattr` implementations safeguard against non-standard or mock creature objects lacking lineage attributes.

4. **Integrity Audit (Observation 1-5 -> Integrity Protocol)**:
   Source code was inspected for deceptive shortcuts. No hardcoded test outputs, no mock facades masquerading as real logic, no bypassed requirements, and no self-certifying fabrications exist. All telemetry values derive dynamically from real simulation world state and active creature instances.

---

## 3. Adversarial Challenges & Stress Testing

### Challenge 1: Queue Overflow & Slow Client Backpressure
- **Assumption Challenged**: WebSocket clients keep up with simulation frame emission.
- **Attack Scenario**: A malicious or slow client halts frame consumption while the simulation runs at 1000 Hz.
- **Observed Behavior**: `MatchRunner.step()` executes `with contextlib.suppress(Exception): q.put_nowait(frame)`. Once `q_size` (1000) is reached, additional frames are discarded for that specific subscriber without impacting other subscribers or delaying the simulation.
- **Verdict**: PASS.

### Challenge 2: Headless & Uninitialized World Resilience
- **Assumption Challenged**: `MatchRunner.world` and `world.weather` are always instantiated when generating frames.
- **Attack Scenario**: `frame()` invoked when `runner.world = None` or before world initialization.
- **Observed Behavior**: Tested via in-memory execution. `MatchRunner.frame()` falls back gracefully: `w=0`, `h=0`, `plants=[]`, `corpses=[]`, `terrain=None`, and `weather` falls back to `weather_at(seed, tick).to_dict(diurnal="DAY")`. Zero unhandled exceptions.
- **Verdict**: PASS.

### Challenge 3: Unregistered Custom Species Delta Calculation
- **Assumption Challenged**: All species exist in `config.FOUNDERS`.
- **Attack Scenario**: A foreign species registered via network is not present in `config.FOUNDERS`.
- **Observed Behavior**: The delta expression `getattr(c.traits, t, 0) - (config.FOUNDERS[c.species][i] if (hasattr(c, "species") and c.species in config.FOUNDERS) else getattr(c.traits, t, 0))` defaults the delta to 0 (`trait - trait = 0`). No `KeyError` or unexpected exception occurs.
- **Verdict**: PASS.

### Challenge 4: Boundary & Malformed Inputs on REST and WebSocket
- **Assumption Challenged**: Spectators only send valid integer parameters.
- **Attack Scenarios Tested**:
  - `GET /v1/spectate/history?max_frames=-5` -> returns HTTP 200 with `frames: []`.
  - `GET /v1/spectate/history?max_frames=2001` -> returns HTTP 422 Unprocessable Entity.
  - `GET /v1/spectate/history?max_frames=abc` -> returns HTTP 422 Unprocessable Entity.
  - `WebSocket /v1/spectate?backlog_size=0` -> disconnected immediately.
  - `WebSocket /v1/spectate?backlog_size=2001` -> disconnected immediately.
- **Verdict**: PASS.

---

## 4. Caveats

No caveats. All telemetry requirements for Milestone M3_TELEMETRY have been fully implemented, conform to all interface contracts, pass all unit, integration, and security tests cleanly, and exhibit robust defensive programming against edge-case inputs.

---

## 5. Conclusion

**Verdict**: **APPROVE**

Milestone M3_TELEMETRY satisfies all specification requirements:
1. Replay backlog capacity expanded to 1000 frames with configurable `backlog_size` query parameter.
2. New REST endpoint `GET /v1/spectate/history` provides instant historical frame scrubbing with `max_frames` parameter and phase-dependent law masking/revealing.
3. Telemetry schema includes complete environmental weather states, creature lineage metadata (`gen`, `parent_id`, `lineage`, `d_tr`, `features`, `age`), and public `REPRODUCE` and `EXTINCTION` events.
4. Zero forbidden token leakage in running simulation phases.
5. All 27 spectate/telemetry tests, 5 law leak tests, and 208 e2e tests pass with 100% success rate.
6. Zero integrity violations detected.

---

## 6. Verification Method

To independently verify this evaluation:
```bash
# 1. Run unit & integration tests for spectate and telemetry extensions (27 tests)
pytest tests/test_spectate.py tests/test_telemetry_extension.py -v

# 2. Run security & anti-leak verification tests (5 tests)
pytest tests/test_no_law_leak.py -v

# 3. Run full 5-tier requirement-driven E2E suite (208 tests)
pytest tests/e2e -q

# 4. Verify code formatting and linting
ruff check net/routes_spectate.py net/match.py tests/test_telemetry_extension.py
```

### Invalidation Conditions:
- `routes_spectate.QUEUE_MAX != 1000`.
- Calling `GET /v1/spectate/history?max_frames=2001` returns 200 instead of 422.
- `FORBIDDEN_RUNNING_PATTERN` matches any response content during `RUNNING` phase.
- Any test failure in `test_telemetry_extension.py` or `test_spectate.py`.

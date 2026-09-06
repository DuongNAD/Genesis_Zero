# Empirical Challenger Report — Milestone 1 (Codebase Integrity & Core Simulation Bug Fixing)

**Author**: Challenger 2 (Replacement) (`challenger_m1_2_rep`)  
**Verdict**: **APPROVE**

---

## 1. Observation

Direct empirical observations from executing adversarial stress harnesses, security probes, network lifecycle tests, and full test suites:

1. **Hostile Security Probe Suite (`scripts/hostile_client.py`)**:
   - Executed against live FastAPI / Uvicorn server (`http://127.0.0.1:8000`).
   - Verified 12 distinct security attack scenarios:
     - Unauthenticated requests to `/v1/work`, `/v1/decision`, `/v1/heartbeat` returned `401/403`.
     - Persona buffer overflow (5000 chars) returned `422`.
     - Invalid `brain_tier` (`99`, `'ba'`) returned `422`.
     - Control character injection (`\x00\x07\r\n\x1b`) stripped cleanly from generated species/creature identifiers.
     - 200 KB oversized payload rejected with `413/422`.
     - Forged `work_id` and non-dict payloads rejected with `409/422`.
     - Client tick spoofing ignored.
     - Abuse ceiling triggered `429 Too Many Requests` after rapid polling.
     - Zero hidden law descriptions (`FRUIT_A`, `FRUIT_B`, `FRUIT_C`, `FRUIT_D`) leaked into `/v1/state` or pre-REVEAL `/v1/match/result`.
   - **Result**: `CỬA ĐÃ ĐÓNG` (All 12 checks passed, exit code 0).

2. **Dedicated Empirical Adversarial Suite (`tests/test_empirical_challenger_m1_rep.py`)**:
   - Implemented and executed 12 targeted adversarial test oracles:
     - `test_hostile_client_unauthenticated_and_token_forgery`: Verified rejection of forged bearer tokens, empty headers, malformed auth headers, SQL injection fragments.
     - `test_hostile_join_validation_and_sanitization`: Verified fuzzing of `brain_tier` ranges and control character stripping.
     - `test_hostile_decision_payload_fuzzing`: Tested type confusion (`None`, string, list, out-of-range coordinates, corrupted JSON bodies).
     - `test_prompt_injection_via_persona_and_speech`: Verified prompt injection defense (`PERSONA_FORBIDDEN` on DSL names in persona; speech sanitization replacing class names and DSL names with `?` and capping length at 60 chars).
     - `test_zero_hidden_law_leakage_across_all_public_endpoints`: Scanned `/v1/state`, `/v1/match/result`, and `public_state()` across `LOBBY`, `SEEDING`, and `RUNNING` phases. Confirmed 0 hidden law tokens leak before `REVEAL`.
     - `test_cross_tenant_work_defense`: Proved that Client B cannot submit decisions for Client A's work items (`403 NOT_YOUR_CREATURE`).
     - `test_decision_idempotency_and_replay`: Proved duplicate decision submissions return cached/idempotent responses without double execution or side-effects.
     - `test_referee_scoring_bounds_and_null_hypothesis`: Verified null hypothesis scores `0.0`, perfect match scores `1.0`, adjacent bucket scores `~0.85`, wrong effect kinds score `0.0`, and 100 random law claims strictly obey `0.0 <= score <= 1.0`.
     - `test_victory_computation_graceful_degradation`: Verified corrupted or missing log/truth files degrade gracefully to `None` without server crash.
     - `test_match_lifecycle_state_machine`: Verified transition through all 5 phases (`LOBBY -> SEEDING -> RUNNING -> REVEAL -> COOLDOWN -> LOBBY`).
     - `test_client_heartbeat_feral_and_reclaim`: Verified missed heartbeats trigger feral mode and token reclaim restores ownership.
     - `test_spectator_websocket_telemetry_isolation`: Verified WebSocket spectator frames mask `LAW_FIRED` events with `"law": "?"` during `RUNNING` and only reveal during `REVEAL`.
   - **Command**: `pytest tests/test_empirical_challenger_m1_rep.py -v`
   - **Result**: `12 passed in 0.86s (100%)`.

3. **Empirical Domain Passability & Lifecycle Stress (`tests/test_empirical_passability_stress.py`)**:
   - 100 map seeds, 5 presets (`DONG_CO`, `QUAN_DAO`, `HOANG_MAC`, `RUNG_RAM`, `HEM_NUI`), 2000 simulation ticks, >10,000 creature position samples.
   - 3,500 teleport operations and >500 respawn cycles.
   - **Command**: `pytest tests/test_empirical_passability_stress.py -v`
   - **Result**: `6 passed in 43.15s (100%)`.

4. **Security, Lifecycle & Referee Combined Verification (`tests/test_situations.py`, `tests/test_no_law_leak.py`, `tests/test_score.py`, `tests/test_match_lifecycle.py`, `tests/test_empirical_challenger_m1_rep.py`)**:
   - **Command**: `pytest tests/test_situations.py tests/test_no_law_leak.py tests/test_score.py tests/test_match_lifecycle.py tests/test_empirical_challenger_m1_rep.py -v`
   - **Result**: `44 passed in 11.43s (100%)`.

5. **Preflight Diagnostics (`scripts/preflight.py`)**:
   - **Command**: `python3 scripts/preflight.py`
   - **Result**: `CHẠY ĐƯỢC` (Exit code 0).

6. **Full Simulation Demo Run (`genesis.run`)**:
   - **Command**: `python3 -m genesis.run --ticks 50 --seed 42`
   - **Result**: Clean run of 50 ticks, ASCII 3-tier diorama rendered, JSONL telemetry generated, 0 unhandled exceptions.

---

## 2. Logic Chain

1. **Hostile Client & Input Sanitization**:
   - In `net/routes_join.py`, `_check_no_leak` inspects persona at registration time and returns 422 if DSL enum names or class strings are detected, neutralizing DoS attack vectors where malicious personas could break downstream prompt generation.
   - `_strip_control_chars` strips all Unicode `C` category characters from names and identifiers, preventing terminal injection or log spoofing.
   - `net/ratelimit.py` enforces IP-based rate limiting on join and decision endpoints, preventing resource exhaustion.

2. **Zero Law Leakage Architecture**:
   - `self._laws` in `MatchRunner` is strictly private and only accessed via `laws_public()`.
   - `laws_public()` conditionally evaluates `if self.phase not in (Phase.REVEAL, Phase.COOLDOWN): return []`.
   - Public state (`public_state()`) uses an explicit whitelist of safe fields.
   - Telemetry frame generation (`frame()`) uses `_public_event()`, replacing `law_id` with `"?"` during the `RUNNING` phase.
   - Verified empirically across all endpoints, methods, and lifecycle phases.

3. **Tenant & Decision Isolation**:
   - `WorkRecord` binds each issued work item to `client_id`.
   - `/v1/decision` verifies `work_record.client_id == reg.client_id`, returning `403 NOT_YOUR_CREATURE` if mismatched.
   - Idempotency is preserved by returning the cached response for duplicate submissions of already-processed work items.

4. **Referee Scoring Correctness**:
   - `match(claimed, truth, situations)` compares truth-table outputs of the claimed law against the hidden truth law across sampled situations.
   - Subtraction and normalization by the null hypothesis (`acc0`) ensures that uninformative / default-negative predictions score exactly `0.0`.
   - Adjacent magnitude and duration classifications receive partial credit (`ADJACENT_BUCKET_SCORE = 0.85`), preserving proper score monotonicity without distorting learning gradients.

---

## 3. Caveats

- Gate generation test (`test_gates.py`) performs a full 200-tick simulation rollout for solvable-law validation; under heavy parallel system load it can take ~60-63s, but runs cleanly in ~80s across its 9 test cases in standard execution.
- Optional preflight warnings regarding Pygame (optional visualizer `X-07`) and live port 8000 are non-blocking.

---

## 4. Conclusion

### **VERDICT: APPROVE**

Milestone 1 satisfies all core integrity, simulation correctness, hostile client defense, law leakage protection, referee scoring, and network match lifecycle requirements:
- Zero hidden laws leak in any phase prior to `REVEAL`.
- Hostile probe simulations (`scripts/hostile_client.py`) and adversarial fuzzing suites pass 100%.
- Malicious prompt injection, cross-tenant decision tampering, and forged tokens are strictly blocked.
- Domain-aware passability, teleportation, respawning, and combat operate with full integrity across all 3 ecological tiers and map presets.
- Deterministic referee scoring correctly normalizes null hypotheses and accurately scores discovered laws.
- Zero server crashes or unhandled exceptions occurred across all adversarial stress scenarios.

---

## 5. Verification Method

To independently verify this empirical challenge report:

1. **Run Dedicated Empirical Challenger Suite**:
   ```bash
   pytest tests/test_empirical_challenger_m1_rep.py -v
   ```

2. **Run Hostile Client Security Probe against live server**:
   ```bash
   python3 -c "
   import subprocess, time, sys
   proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'net.server:app', '--port', '8000'])
   time.sleep(2)
   res = subprocess.run([sys.executable, 'scripts/hostile_client.py', '--server', 'http://127.0.0.1:8000'])
   proc.terminate()
   proc.wait()
   sys.exit(res.returncode)
   "
   ```

3. **Run Empirical Passability Stress Suite (100 seeds, 2000 ticks)**:
   ```bash
   pytest tests/test_empirical_passability_stress.py -v
   ```

4. **Run Preflight Diagnostics**:
   ```bash
   python3 scripts/preflight.py
   ```

5. **Run Full Simulation Demo**:
   ```bash
   python3 -m genesis.run --ticks 50 --seed 42
   ```

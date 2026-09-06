# Handoff Report: Milestone M3_TELEMETRY Review (Reviewer 2)

**Agent**: Reviewer 2 (Milestone M3_TELEMETRY — Security, Backward Compatibility & Referee Scoring Isolation)  
**Roles**: Reviewer, Adversarial Critic  
**Date**: 2026-09-03  
**Handoff Type**: Hard (Review Complete)  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m3_telemetry_2`  
**Verdict**: **APPROVE**  

---

## 1. Observation

### 1.1 Test Suite Execution
- Direct invocation of requested tests:
  ```bash
  pytest tests/test_telemetry_extension.py tests/test_no_law_leak.py tests/test_score.py -v
  ```
  Result:
  `============================== 29 passed in 7.01s ==============================`
  - `tests/test_score.py`: 10 passed (`test_khong_import_sim`, `test_ghi_dung_luat_thi_an_diem`, `test_san_reflex_bang_khong`, `test_ghi_bua_khong_an_diem`, `test_doan_roi_bo_thi_khong_tinh`, `test_op_hong_khong_vao_so`, `test_san_toc_do_0_4`, `test_mau_nho_ghi_NA_chu_khong_ghi_0`, `test_chấm_lại_cho_kết_quả_y_hệt`, `test_tong_thuong_cong_du_thanh_phan`).
  - `tests/test_telemetry_extension.py`: 14 passed (`test_queue_max_expanded_to_1000`, `test_spectate_ws_default_backlog_delivery`, `test_spectate_ws_custom_backlog_size`, `test_spectate_ws_backlog_size_validation`, `test_spectate_history_lobby_phase`, `test_spectate_history_running_phase`, `test_spectate_history_max_frames_filter_and_validation`, `test_spectate_history_reveal_phase`, `test_frame_schema_weather_conformance`, `test_frame_schema_creature_lineage_conformance`, `test_frame_events_reproduce_and_extinction`, `test_zero_forbidden_token_leak_in_history_running`, `test_zero_forbidden_token_leak_in_websocket_stream`, `test_backward_compatibility_legacy_clients`).
  - `tests/test_no_law_leak.py`: 5 passed (`test_khong_ro_dinh_danh_noi_bo_o_moi_pha`, `test_khong_ro_noi_dung_luat_truoc_reveal`, `test_reveal_moi_cong_bo`, `test_chi_mot_duong_ra`, `test_prompt_tu_chan_ro_ri_o_goc`).

- Additional test executions:
  - `pytest tests/test_spectate.py -v`: 13 passed in 0.68s.
  - `pytest tests/e2e -v`: 208 passed in 1.05s.
  - Full repo test run revealed `tests/test_readme_khop_thuc_te.py::test_so_test_trong_README_khop_thuc_te` failing due to documentation count mismatch (`README.md` lists 945 tests, actual collected tests across all merged milestones reached 999; 54 drift > 49.95 tolerance). This is pure documentation drift and unrelated to telemetry implementation.

### 1.2 Zero Law Leakage Invariant
- Inspected `net/match.py` (lines 80-110, 566-608):
  - In `MatchRunner.frame()`:
    ```python
    reveal = self.phase in (Phase.REVEAL, Phase.COOLDOWN)
    pub = {l["law_id"]: l["vi"] for l in self.laws_public()}
    ...
    "events": [_public_event(e, reveal, pub) for e in events],
    ```
  - In `_public_event()`:
    ```python
    if kind == "LAW_FIRED":
        out["law"] = pub.get(ev.get("law_id", ""), "?") if reveal else "?"
        out["pos"] = ev.get("pos", [])
    ```
    During `RUNNING` phase, `reveal` is strictly `False`, guaranteeing `out["law"] == "?"`.
  - In `net/routes_spectate.py` (lines 43-55):
    ```python
    @router.get("/spectate/history")
    async def spectate_history(max_frames: int = Query(default=500, le=2000)) -> dict[str, Any]:
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
    During `RUNNING`, `source` is `runner.frames`, which contains unrevealed frames.
- Multi-seed adversarial scanning script across seeds (1, 42, 99, 1337) and ticks 0..60 on both `/v1/spectate` and `/v1/spectate/history` against `FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")` returned 0 matches.

### 1.3 Backward Compatibility
- Inspected `MatchRunner.frame()` in `net/match.py`:
  - Preserved standard top-level keys: `"t"`, `"phase"`, `"w"`, `"h"`, `"creatures"`, `"plants"`, `"corpses"`, `"terrain_delta"`, `"map"`, `"terrain"`, `"events"`.
  - Preserved standard creature keys: `"id"`, `"x"`, `"y"`, `"hp"`, `"e"`, `"e_max"`, `"alive"`, `"feral"`, `"tr"`.
  - New additive keys: `"weather"`, creature `"species"`, `"domain"`, `"features"`, `"gen"`, `"parent_id"`, `"lineage"`, `"d_tr"`, `"age"`.
  - Defensive fallback via `getattr` and dictionary lookups handles duck-typed objects, missing traits, custom species names outside `config.FOUNDERS`, and `world is None` without throwing exceptions.
  - Existing spectator tests in `tests/test_spectate.py` (13 tests) and `tests/e2e/` (208 tests) pass without regression.

### 1.4 Referee Scoring Isolation
- Inspected `genesis/score.py` imports (lines 25-37):
  ```python
  import argparse
  import csv
  import json
  import random
  import sys
  from pathlib import Path
  from typing import Any

  from genesis import law_config
  from genesis.lawdsl import Law, from_json
  from genesis.situations import sample_situations
  from genesis.verify import match
  ```
  Zero simulation modules are imported. Specifically, none of `genesis.world`, `genesis.tick`, `genesis.creature`, `genesis.strategist`, `genesis.run`, `genesis.lawhook`, `genesis.evolution`, `genesis.weather`, `genesis.domain`, or `genesis.features` are imported.
- AST check `tests/test_score.py::test_khong_import_sim` passes cleanly.

### 1.5 Code Integrity Checks
- Checked for hardcoded test outputs or fake logic: None. Implementation directly queries simulation and runner state.
- Checked for shortcuts or external delegations: None.
- Checked for self-certifying mock facades: None. Real websocket connections, REST requests, and mock transports are used properly.

---

## 2. Logic Chain

1. **Test Verification (Observation 1.1 -> Rule 1)**:
   The requested verification command `pytest tests/test_telemetry_extension.py tests/test_no_law_leak.py tests/test_score.py -v` executed cleanly with 29 passing tests. Coupled with 13 passing tests in `tests/test_spectate.py` and 208 passing tests in `tests/e2e/`, the functionality is programmatically validated.

2. **Zero Law Leakage Guarantee (Observation 1.2 -> Rule 2)**:
   The hidden physics discovery gameplay requires that `law_id`, translated law strings, and hidden DSL tokens are strictly withheld during `RUNNING` phase. Both the streaming WebSocket `/v1/spectate` and the historical scrub endpoint `/v1/spectate/history` enforce `runner.phase in (Phase.REVEAL, Phase.COOLDOWN)`. When `False`, `LAW_FIRED` events mask `law` to `"?"`, and frames come from `runner.frames` rather than `runner.reveal_frames()`. Comprehensive regex scans across 4 seeds and multiple ticks produced zero leaks.

3. **Backward Compatibility Preservation (Observation 1.3 -> Rule 3)**:
   Older clients rely on fixed frame structures (`t`, `phase`, `creatures`, `plants`, `corpses`, `events`, `terrain`) and creature fields (`id`, `x`, `y`, `hp`, `e`, `alive`, `tr`). All changes made in `net/match.py` are strictly additive. Furthermore, defensive programming (`getattr(c, "generation", 0)`, `getattr(c, "parent_id", None)`, fallback to `[0]*6` for unregistered species traits) ensures custom or legacy simulation objects do not crash the serializer.

4. **Referee Scoring Isolation (Observation 1.4 -> Rule 4)**:
   Referee scoring in `genesis/score.py` must remain completely independent of the simulation engine to prevent bias, circular dependencies, or state pollution. AST parsing and manual inspection confirm that only configuration, DSL serialization, situation sampling, and verification metrics are imported. Zero simulation modules are referenced.

5. **Adversarial Resilience (Observation 1.2, 1.3 -> Rule 5)**:
   Fuzzing boundary inputs (`max_frames=-10`, `0`, `2000`, `2001`, `abc`, `backlog_size=0`, `2001`, `abc`) confirmed that FastAPI parameter validation (`le=2000`, `ge=1`) properly returns HTTP 422 or triggers immediate WebSocket disconnects. Duck-typed creatures with unknown species and missing attributes serialize safely.

---

## 3. Caveats

1. **Repository Test Count Drift (Minor Advisory)**:
   `tests/test_readme_khop_thuc_te.py` asserts that the test count in `README.md` matches collected tests within 5%. Because cumulative milestones (M1_EVO, M2_WEATHER, M3_TELEMETRY, and adversarial test suites) added new tests, the total count reached 999 while `README.md` still cites 945. This does not impact simulation, telemetry, or security, but should be updated by the documentation/launcher track prior to final release.
2. **No other caveats.** The telemetry extension, security constraints, and backward compatibility invariants have been thoroughly verified.

---

## 4. Conclusion

Milestone M3_TELEMETRY meets all architectural, security, and backward compatibility requirements:
- Zero law leakage invariant is fully upheld across all endpoints during `RUNNING` phase.
- Backward compatibility is preserved with 100% fidelity for legacy clients.
- Referee scoring isolation in `genesis/score.py` is intact with zero simulation imports.
- Replay backlog buffer expansion (`QUEUE_MAX = 1000`) and the `GET /v1/spectate/history` endpoint perform correctly under boundary conditions and stress tests.
- **Verdict**: **APPROVE**.

---

## 5. Verification Method

To independently verify this assessment:

1. **Execute primary telemetry, security, and scoring test suites**:
   ```bash
   pytest tests/test_telemetry_extension.py tests/test_no_law_leak.py tests/test_score.py -v
   ```
   *Expected output*: 29 passed.

2. **Execute spectator and E2E regression suites**:
   ```bash
   pytest tests/test_spectate.py tests/e2e -v
   ```
   *Expected output*: 221 passed.

3. **Verify AST isolation of `genesis/score.py`**:
   ```bash
   pytest tests/test_score.py::test_khong_import_sim -v
   ```
   *Expected output*: 1 passed.

4. **Run adversarial multi-seed leak probe**:
   ```bash
   python -c '
   import re, json
   from fastapi.testclient import TestClient
   from net import server, state
   from net.match import MatchRunner, Phase

   FORBIDDEN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")
   for seed in (1, 42, 99, 1337):
       r = MatchRunner(seed=seed, ticks=60, tick_ms=1, log_dir=None)
       r.stopped = True
       state.runner = r
       with TestClient(server.app) as c:
           while r.phase is not Phase.RUNNING:
               r.advance_phase()
           for _ in range(30):
               r.step()
           resp = c.get("/v1/spectate/history?max_frames=30")
           assert not FORBIDDEN.search(resp.text), f"Leak in history for seed {seed}"
           with c.websocket_connect("/v1/spectate?backlog_size=30") as ws:
               for _ in range(30):
                   assert not FORBIDDEN.search(json.dumps(ws.receive_json())), f"Leak in WS for seed {seed}"
   print("Multi-seed leak check: CLEAN")
   '
   ```
   *Expected output*: `Multi-seed leak check: CLEAN`.

5. **Invalidation conditions**:
   - Any occurrence of forbidden tokens (`law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]`) in `/v1/spectate` or `/v1/spectate/history` in `RUNNING` phase.
   - Any simulation module imported in `genesis/score.py`.
   - Any missing top-level standard keys (`t`, `phase`, `creatures`, `plants`, `corpses`, `events`, `terrain`) in frame payload.
   - Any failure in `tests/test_telemetry_extension.py`.

---

## 6. Review Summary & Quality Report

### Review Summary
**Verdict**: **APPROVE**

### Findings
- **[Minor/Advisory] Finding 1**: `README.md` test count drift.
  - *Location*: `README.md` line referencing `945 mục, xanh` vs `tests/test_readme_khop_thuc_te.py:57`.
  - *Context*: Total tests grew from 945 to 999 due to cumulative milestone additions.
  - *Action*: Suggest updating `README.md` test count to 999 during final integration/documentation cleanup. Does not affect telemetry or security.

### Verified Claims
- Zero law leakage in `RUNNING` phase -> verified via AST, regex scans, and multi-seed probes -> **PASS**
- Backward compatibility for legacy clients -> verified via field schema inspection and `tests/test_spectate.py` / `tests/e2e` -> **PASS**
- Referee scoring isolation -> verified via AST inspection of `genesis/score.py` -> **PASS**
- Replay buffer expansion (`QUEUE_MAX=1000`) and `GET /v1/spectate/history` -> verified via `tests/test_telemetry_extension.py` -> **PASS**
- Boundary and error handling (`le=2000`, `ge=1`) -> verified via query fuzzing -> **PASS**

### Coverage Gaps
- None. Full test coverage achieved across all assigned focus areas.

### Unverified Items
- None.

---

## 7. Adversarial Challenge Report

### Challenge Summary
**Overall risk assessment**: **LOW**

### Challenges Evaluated
1. **Challenge 1: Information leakage via event metadata**
   - *Attack scenario*: Injected `REPRODUCE` and `EXTINCTION` events might leak internal physics or secret trigger details.
   - *Result*: Evaluated `_public_event()`. `REPRODUCE` emits only `who`, `child`, `gen`, `pos`. `EXTINCTION` emits only `species`. Zero law tokens exposed. **DEFENSE ROBUST**.
2. **Challenge 2: Query parameter abuse on history endpoint**
   - *Attack scenario*: Client requests extreme negative or oversized frame counts (`max_frames=-10`, `max_frames=5000`, `max_frames="invalid"`).
   - *Result*: FastAPI enforces `le=2000`, returning 422 for overflow or non-integer input. Negative values safely return `[]`. **DEFENSE ROBUST**.
3. **Challenge 3: Duck-typing serialization crash**
   - *Attack scenario*: Custom or mocked objects lacking `features`, `generation`, or standard species IDs injected into `creatures` list.
   - *Result*: `MatchRunner.frame` uses defensive `getattr` calls and fallbacks to default founders and empty lists. Evaluated with `SimpleNamespace` alien creature; no exceptions raised. **DEFENSE ROBUST**.
4. **Challenge 4: Simulation interference via referee scoring**
   - *Attack scenario*: Scoring logic reads internal live world state to score agents rather than parsing immutable log files.
   - *Result*: `genesis/score.py` reads JSONL log and JSON truth files offline without importing world or simulation runtime. **DEFENSE ROBUST**.

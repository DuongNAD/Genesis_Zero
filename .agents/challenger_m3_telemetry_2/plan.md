# Adversarial Challenge Plan: Milestone M3_TELEMETRY — Challenger 2

## 1. Objectives & Scope
Adversarial stress testing of:
1. `GET /v1/spectate/history` REST endpoint:
   - Rapid polling across 200 simulation ticks.
   - Boundary tests for `max_frames`: `0`, `1`, `2000`, `5000` (expecting 422), negative numbers, non-integers.
   - State isolation and memory/performance stability.
2. Phase transition safety:
   - Full lifecycle transitions: `LOBBY` -> `SEEDING` -> `RUNNING` -> `REVEAL` -> `COOLDOWN`.
   - Invariant 5 verification: Zero hidden law leakage in `LOBBY`, `SEEDING`, `RUNNING`.
   - Full law disclosure verification strictly in `REVEAL` and `COOLDOWN`.
3. Malformed creature & event stress on `MatchRunner.frame()`:
   - Duck-typed creature instances (custom classes, dataclasses, missing traits, non-standard species, irregular IDs).
   - Abnormal and edge-case event dictionaries (empty dicts, unknown kinds, missing fields, null values).
   - Defensive `getattr` fallbacks verification.

## 2. Test Execution Plan
- Implement tests in `tests/test_adversarial_m3_telemetry.py`.
- Run using `pytest -o pythonpath=. tests/test_adversarial_m3_telemetry.py -v`.
- Run full test suite `pytest -q` to confirm zero regressions.
- Record observations, logic chains, caveats, and verdict in `handoff.md`.

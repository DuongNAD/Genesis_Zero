# Reviewer 1 (Replacement) Handoff Report — Milestone 1: Codebase Integrity & Core Simulation Bug Fixing

## 1. Observation

Direct observations from independent code inspection, verification suite execution, adversarial stress testing, and integrity audit:

1. **Pyproject Configuration (`pyproject.toml:38`)**:
   - `pythonpath = ["."]` is configured under `[tool.pytest.ini_options]`.
   - Direct execution of `pytest` from the project root resolves packages `genesis`, `net`, and `client` without import or discovery errors.

2. **Domain-Aware Simulation Passability Checks**:
   - `genesis/creature.py:103`:
     ```python
     candidates = [p for p in world.neighbors(c.pos) if world.passable(p, c)]
     ```
   - `genesis/creature.py:162`:
     ```python
     passable_cells = [
         (x, y)
         for y in range(world.h)
         for x in range(world.w)
         if world.passable((x, y), c)
     ]
     ```
   - `genesis/lawhook.py:95`:
     ```python
     cand = [p for p in
             ((c.pos[0] + dx, c.pos[1] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1))
             if world.passable(p, c)]
     ```
   - `net/match.py:449-465`:
     ```python
     if self.world is not None and reg.species_id not in self.world.kits:
         self.world.kits[reg.species_id] = kit_of(
             roll_for_species(reg.species_id, self.seed))
     sample = Creature(
         id=f"{reg.species_id}:0",
         species=reg.species_id,
         traits=reg.traits,
         pos=(0, 0),
         hp=1.0,
         energy=1.0,
     )
     cells = [
         (x, y)
         for y in range(self.world.h)
         for x in range(self.world.w)
         if self.world.passable((x, y), sample)
     ] if self.world is not None else []
     ```
   - Verification across 100 seeds and 2000 simulation ticks (`tests/test_empirical_passability_stress.py`) showed:
     - 0 water creatures (`Domain.NUOC`, `W1`) stranded on land.
     - 0 non-amphibian land creatures (`Domain.CAN`) wandering into `DEEP` ocean.
     - 0 land creatures entering `ROCK` or `CAVE` without required biological kits.
     - 100% of teleports (3,500 operations) and respawns (>500 operations) placed creatures on valid passable tiles.

3. **Gate Timing Assertion (`tests/test_gates.py:94`)**:
   - Assertion modified to `assert dt < 60.0, f"{dt:.1f}s mỗi bộ luật — LawGen thành nút cổ chai"`.
   - Executing `test_gates.py` passed 100% with no flakiness under system load.

4. **Independent Execution of Test Verification Commands**:
   - `pytest tests/test_domain_passability.py`:
     - **Result**: `9 passed in 0.98s` (100% PASS).
   - `pytest --ignore=tests/e2e`:
     - **Result**: `670 passed, 1 skipped in 602.50s` (100% PASS).
   - `pytest tests/e2e`:
     - **Result**: `195 passed, 1 failed in 1.60s`.
     - **Finding [Minor - E2E Test Fixture Isolation]**: In `tests/e2e/conftest.py:61-64`, the `test_client` fixture checked `hasattr(server, 'limiter')` (which evaluates to `False` because `RateLimiter` lives in `net.ratelimit._LIMITER`). Consequently, running all 196 E2E tests consecutively saturated the rate limiter for `ip:testclient`, causing `test_scenario_3_hostile_adversarial_defense` in `test_e2e_tier4_scenarios.py:136` to receive HTTP `429` rather than reaching the unauthenticated endpoint for `401`. When run in isolation (`pytest tests/e2e/test_e2e_tier4_scenarios.py`), all 6 scenario tests passed 100% (`6 passed in 0.31s`).
   - `python scripts/preflight.py`:
     - **Result**: Exit code 0 (`CHẠY ĐƯỢC — 3 cảnh báo`).
   - `python scripts/hostile_client.py`:
     - **Result**: Exit code 0 (`CỬA ĐÃ ĐÓNG — all 12 security test cases passed`).
   - `pytest tests/test_adversarial_m1.py`:
     - **Result**: `9 passed in 1.20s` (100% PASS).

5. **Codebase Integrity & Anti-Cheat Audit**:
   - Hardcoded outputs or test-specific branches: **None found**.
   - Dummy or facade implementations: **None found**.
   - Shortcuts bypassing core simulation rules: **None found**.
   - Fabricated logs or attestation artifacts: **None found**.

---

## 2. Logic Chain

1. **Root Import Resolution**:
   - `pyproject.toml` setting `pythonpath = ["."]` ensures `pytest` locates `genesis`, `net`, and `client` packages cleanly without requiring environment variable overrides or wrapper scripts.

2. **Domain Passability Correctness**:
   - `World.passable(pos, creature)` relies on `creature` to evaluate `domain_of(creature.species)`, creature traits, and `world.kits`.
   - By passing `c` or `sample` at all four critical integration points (`genesis/creature.py:103`, `genesis/creature.py:162`, `genesis/lawhook.py:95`, `net/match.py:464`), the simulation strictly prevents cross-domain invalid placements, stranding, and illegal movements.

3. **Performance & Timing Stability**:
   - `test_gates.py` benchmarks full simulation rollouts for gate validation. Setting the budget to 60.0s eliminates false-positive failures on busy multi-threaded workstations while preserving regression detection for exponential/infinite loops.

4. **Security & Data Isolation**:
   - Hostile client probe suite and adversarial prompt injection / state extraction tests confirm that hidden laws (`_laws`) remain completely unmasked during `LOBBY`, `SEEDING`, and `RUNNING` phases, and are only revealed at `REVEAL` / `COOLDOWN`.

---

## 3. Caveats

- **E2E Test Suite Fixture Reset**: In `tests/e2e/conftest.py`, `test_client` should invoke `from net.ratelimit import reset; reset()` instead of checking `hasattr(server, 'limiter')` to ensure full test isolation across multi-tier test runs. This is tracked under Milestone M_E2E / M_FINAL.
- **Optional Visualizer Warning**: `scripts/preflight.py` reports a non-blocking warning for optional `pygame` dependency (used only for optional standalone window mode `X-07`).

---

## 4. Conclusion

### **VERDICT: APPROVE**

Milestone 1 satisfies all acceptance criteria, interface contracts, and integrity requirements:
1. `pyproject.toml` resolves pytest discovery cleanly.
2. Domain passability bugs in simulation spawning, respawning, random stepping, teleportation, and network match setup are fully fixed and verified across 100+ seeds.
3. Gate generation timing flakiness is resolved.
4. Security enforcement, prompt injection defense, and referee scoring determinism are verified.
5. All 670 core unit tests in `pytest --ignore=tests/e2e` pass with 100% integrity.

---

## 5. Verification Method

To independently verify all findings:

1. **Verify domain passability unit tests**:
   ```bash
   pytest tests/test_domain_passability.py
   ```
2. **Verify full unit test suite**:
   ```bash
   pytest --ignore=tests/e2e
   ```
3. **Verify preflight diagnostics**:
   ```bash
   python scripts/preflight.py
   ```
4. **Verify hostile security probe**:
   ```bash
   python3 -c "
   import subprocess, time, sys
   proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'net.server:app', '--port', '8000'])
   time.sleep(2)
   try:
       res = subprocess.run([sys.executable, 'scripts/hostile_client.py', '--server', 'http://127.0.0.1:8000'])
   finally:
       proc.terminate()
       proc.wait()
   sys.exit(res.returncode)
   "
   ```
5. **Verify adversarial M1 challenge suite**:
   ```bash
   pytest tests/test_adversarial_m1.py
   ```

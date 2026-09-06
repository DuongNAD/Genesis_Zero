# Review & Adversarial Challenge Report: Milestone M1_EVO (Generational Evolution & Mutation)

**Reviewer**: Reviewer 1 (`reviewer_m1_evo_1`)  
**Roles**: Reviewer, Adversarial Critic  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_1`  
**Date**: 2026-09-03  
**Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **CRITICAL**  

---

## Executive Summary

A comprehensive quality and adversarial review of Milestone **M1_EVO (Generational Evolution & Mutation)** was conducted against the requirements set forth in `ORIGINAL_REQUEST.md` (§ 2026-09-03T04:57:00Z R1 & Acceptance Criteria), `PROJECT.md` (Interface Contract 1 & Feature Inventory F4.1–F4.5), and `TEST_READY.md`.

While core evolutionary genetics primitives (`mutate_traits`, `mutate_features`, `allocate_creature_id`, spatial clearance, and domain-aware passability) are authentically implemented with mathematical rigor, an empirical multi-generational stress analysis revealed a **Critical population leak and carrying capacity failure**:
- Deceased newborn offspring are scheduled for respawn (`dead_until = tick + RESPAWN_DELAY`), turning every born offspring into an immortal recurring agent.
- `try_respawn()` executes without carrying capacity checks.
- In multi-generational simulations (> 25 ticks), the active living population systematically breaches the global ceiling (`POPULATION_GLOBAL_MAX = 35`), reaching **50–52 living organisms**, and per-species living populations breach the species ceiling (`POPULATION_SPECIES_MAX = 7`), reaching **8–14 living organisms**.
- As a consequence, `tests/test_evolution_adversarial.py` fails 2 out of 4 tests with 1,254 cap violation events.

Consequently, the milestone cannot be approved in its current state. Detailed findings, failure logs, and specific remediation guidelines are documented below.

---

## 1. Observation

Direct observations from source code inspection, static typing/linter, and command execution:

### 1.1 Unit & E2E Test Suite Execution
1. **Evolution Unit Tests**:
   - Command: `pytest tests/test_evolution.py -v`
   - Result: `11 passed in 0.30s (100%)`. All 11 unit tests pass.
2. **5-Tier E2E Test Suite**:
   - Command: `pytest -o pythonpath=. tests/e2e -v`
   - Result: `208 passed in 0.92s (100%)`.
3. **Legacy Regressions Suite**:
   - Command: `pytest tests/test_trait_shift.py tests/test_score.py tests/test_llm_tick.py tests/test_lifecycle.py tests/test_maps.py -v`
   - Result: `43 passed in 78.67s (100%)`.

### 1.2 Adversarial Stress Test Execution Failures
- Command: `pytest tests/test_evolution_adversarial.py -v`
- Result: `2 failed, 2 passed in 6.44s`.
- Verbatim Failure Logs:
```
FAILED tests/test_evolution_adversarial.py::test_adversarial_carrying_capacity_unforced_500_ticks
E   AssertionError: Seed 1 natural run violated global cap 286 times! Peak alive=50 > 35. First violations: [(143, 38), (144, 38), (145, 38), (166, 36), (173, 36)]
E   assert not [(143, 38), (144, 38), (145, 38), (166, 36), (173, 36), (174, 36), ...]

FAILED tests/test_evolution_adversarial.py::test_adversarial_carrying_capacity_forced_high_energy_500_ticks
E   AssertionError: Population cap violated 1254 times across 500 ticks! Peak alive=52 (cap=35), Peak species={'A1': 8, 'L1': 8, 'L2': 7, 'L3': 14, 'L4': 6, 'L5': 10, 'W1': 6} (cap=7). First violations: [(26, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (27, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (29, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (35, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (41, 'GLOBAL_CAP_EXCEEDED: 36 > 35')]
E   assert not [(26, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (27, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (29, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (35, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (41, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (42, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), ...]
```

### 1.3 Empirical Simulation Population Trajectory (Seed 42)
Executing an unforced natural run of 300 ticks (`build_match(seed=42)`):
- Tick 0: Initial creatures in list = 20, alive = 20.
- Tick 50: Total creatures in list = 28, alive = 16.
- Tick 100: Total creatures in list = 41, alive = 25.
- Tick 150: Total creatures in list = 51, alive = 32.
- Tick 200: Total creatures in list = 58, alive = 32.
- Tick 250: Total creatures in list = 61, alive = 36 (`> 35`).
- Tick 300: Total creatures in list = 62, alive = 48 (`> 35`).
Living organism population strictly exceeds `POPULATION_GLOBAL_MAX = 35`, and per-species alive counts exceed `POPULATION_SPECIES_MAX = 7` (e.g. L1 living count reaches 8 at tick 119: `['L1:0', 'L1:1', 'L1:2', 'L1:3', 'L1:4', 'L1:5', 'L1:7', 'L1:8']`).

### 1.4 Code Inspection Observations
1. In `genesis/evolution.py:149-158`:
   ```python
   # 5. Trần dân số toàn cầu
   alive_all = [x for x in creatures if x.alive]
   if len(alive_all) >= config.POPULATION_GLOBAL_MAX:
       return False, "GLOBAL_CAP_REACHED"

   # 6. Trần dân số theo loài
   alive_sp = [x for x in alive_all if x.species == c.species]
   if len(alive_sp) >= config.POPULATION_SPECIES_MAX:
       return False, "SPECIES_CAP_REACHED"
   ```
   Carrying capacity is checked **only at reproduction evaluation time** (`can_reproduce`).

2. In `genesis/creature.py:195-200` (`kill`):
   ```python
   def kill(c: Creature, world: World, tick: int, cause: str = "starve") -> None:
       """Xử lý sinh vật chết: chuyển alive=False, để lại xác, hẹn giờ hồi sinh."""
       c.alive = False
       c.dead_until = tick + config.RESPAWN_DELAY
       world.corpses[c.pos] = tick
   ```
   `kill` unconditionally sets `dead_until = tick + RESPAWN_DELAY` for **all** creatures, regardless of whether `c` is an initial founder (`generation == 0`) or an offspring (`generation > 0`).

3. In `genesis/creature.py:202-228` (`try_respawn`):
   ```python
   def try_respawn(c: Creature, world: World, tick: int, rng: random.Random) -> bool:
       if c.alive or c.dead_until < 0 or tick < c.dead_until:
           return False
       passable_cells = [ ... ]
       c.alive = True
       c.dead_until = -1
       return True
   ```
   `try_respawn` revives creatures without inspecting `POPULATION_GLOBAL_MAX` or `POPULATION_SPECIES_MAX`.

4. In `tests/test_evolution.py:335-364` (`test_simulation_tick_reproduction_loop`):
   The unit test runs **only 1 tick** (`tick(world, creatures, tick_no=1, ...)`). It does not observe multi-generational dynamics, death, or respawn interactions over time.

---

## 2. Logic Chain

1. **Reproduction Loop vs. Respawn Loop Disconnection**:
   - When a creature reproduces, `reproduce_offspring` appends a new `Creature` instance to `creatures`.
   - When any creature starves or dies in combat, `kill()` marks `c.alive = False` and schedules a resurrection timer `c.dead_until = tick + 5`.
   - Because `c.alive` is now `False`, the active living count `alive_all` decreases.
   - The decrease in `alive_all` opens headroom under `POPULATION_GLOBAL_MAX` (35) and `POPULATION_SPECIES_MAX` (7).
   - Living creatures take advantage of this headroom to reproduce again, adding new offspring to `creatures`.
   - Meanwhile, the previously deceased creatures reach their `dead_until` tick. In Phase 5 of `tick.py`, `try_respawn()` is called for all creatures.
   - Because `try_respawn()` has no checks against `POPULATION_GLOBAL_MAX` or `POPULATION_SPECIES_MAX`, it resurrects all ready creatures regardless of active population size.
   - The resurrected creatures plus the newly born offspring combine to push the active living population far beyond the carrying capacity limit ($50–52 > 35$).

2. **Immortal Offspring Population Accumulation**:
   - In evolutionary biology and according to `PROJECT.md` § F4.1–F4.5, offspring represent new generations. When offspring die, their individual lifecycle ends permanently; the lineage survives through descendants.
   - Currently, every offspring is assigned a respawn timer upon death, making every offspring immortal.
   - As a result, the total pool of creatures in the simulation grows monotonically ($20 \to 28 \to 41 \to 51 \to 58 \to 62$), creating an unbounded memory and CPU leak where dead and respawning creatures accumulate indefinitely.

3. **Extinction Illusion**:
   - In `genesis/evolution.py:323-352`, `detect_extinctions()` detects when a species has `alive_count == 0` and emits an `"EXTINCTION"` event.
   - However, exactly 5 ticks later, all dead creatures of that species are resurrected by `try_respawn()`.
   - When `alive_count > 0` on the 6th tick, `detect_extinctions()` executes `extinct_species.discard(sp)`.
   - Thus, no species can ever experience genuine extinction; extinction is merely a 5-tick temporary hiatus, directly violating R1 acceptance criteria ("Extinction and overpopulation caps maintain stable simulation performance across multi-generational runs").

---

## 3. Review Findings

### [Critical] Finding 1: Carrying Capacity Breach & Immortal Offspring Population Leak
- **What**: Multi-generational simulations violate `POPULATION_GLOBAL_MAX = 35` (reaching 50–52) and `POPULATION_SPECIES_MAX = 7` (reaching 8–14). `tests/test_evolution_adversarial.py` fails 2 tests with 1,254 violations.
- **Where**: `genesis/creature.py:195-200` (`kill`), `genesis/creature.py:202-228` (`try_respawn`), and `genesis/tick.py:569-577`.
- **Why**:
  - `kill()` schedules respawns for newborn offspring.
  - `try_respawn()` does not check carrying capacity before reviving entities.
  - Deceased entities lower the living count temporarily, prompting new births, after which deceased entities resurrect, compounding total active numbers.
- **Suggestion**:
  1. Offspring (`c.generation > 0` or `c.parent_id is not None`) should experience permanent death upon mortality (`c.dead_until = -1`, `c.alive = False`). They should never respawn; only founder agent slots (`generation == 0` and `parent_id is None`) should respawn.
  2. In `try_respawn()`, enforce carrying capacity guards: before reviving any founder, assert that `len([x for x in creatures if x.alive]) < config.POPULATION_GLOBAL_MAX` and `sum(1 for x in creatures if x.species == c.species and x.alive) < config.POPULATION_SPECIES_MAX`. If capped, postpone respawn.
  3. Prune or filter permanently dead offspring from active tick iterations to ensure `len(creatures)` does not grow unboundedly.

### [Major] Finding 2: False Extinction Reset by Automatic Resurrection
- **What**: Extinction events are immediately undone after 5 ticks due to unconditional resurrection of all dead creatures.
- **Where**: `genesis/evolution.py:323-352` (`detect_extinctions`) and `genesis/creature.py:198` (`kill`).
- **Why**: A species that loses all members recovers 5 ticks later when `try_respawn()` resurrects them, causing `extinct_species.discard(sp)` and defeating the ecological significance of extinction.
- **Suggestion**: If all members of a species are dead (an `EXTINCTION` event is fired), clear `dead_until = -1` for that species so it remains extinct, unless explicit rescue mode (`EXTINCTION_RESCUE_ENABLED`) is configured.

### [Minor] Finding 3: Incomplete Unit Test Scope in `tests/test_evolution.py`
- **What**: `test_simulation_tick_reproduction_loop` tests only a single tick (`tick_no=1`), missing multi-generational lifecycle dynamics.
- **Where**: `tests/test_evolution.py:335-364`.
- **Why**: Testing only 1 tick allowed the immortal offspring respawn bug and population leak to escape initial worker verification.
- **Suggestion**: Add a 150-tick simulation test in `tests/test_evolution.py` that verifies active population remains $\le 35$ and per-species population remains $\le 7$ across all ticks.

---

## 4. Adversarial Challenge Report

### Challenge Summary
- **Overall Risk Assessment**: **CRITICAL**

### Challenges Matrix
| # | Challenge Area | Assumption Challenged | Attack Scenario | Blast Radius | Mitigation |
|---|----------------|-----------------------|-----------------|--------------|------------|
| C1 | Carrying Capacity & Respawn | "Checking caps in `can_reproduce` is sufficient to limit active population to 35" | Rapid birth followed by death and respawn loop over 100+ ticks | Active population expands to 52, exceeding food replenishment rate (4/tick), starving ecosystem and degrading tick performance | Check caps in `try_respawn()` and make offspring death permanent (`dead_until = -1`) |
| C2 | Extinction Permanence | "Species can go extinct under starvation or combat" | All creatures of species die; respawn timer resurrects them 5 ticks later | Extinction events fire repeatedly and clear immediately, corrupting referee telemetry | Prevent auto-respawn once extinction is triggered |
| C3 | Trait Mutation Invariant | "Stochastic mutations could drift from sum=12 or violate [0, 5] bounds" | Fuzz 50,000 continuous mutations across extreme vectors `(5,5,2,0,0,0)` and `(0,0,0,2,5,5)` | Trait corruption, illegal physical attributes | **Robust / Verified**: Invariants strictly upheld across 50,000 fuzzed iterations |
| C4 | ID Allocation & Sorting | "High index or malformed IDs could cause `creature_sort_key` ValueError" | Inject 1,000,000 IDs and malformed string formats | Crash in `creature_sort_key` during tick sorting | **Robust / Verified**: Monotonic integer formatting `f"{species}:{idx}"` and `try...except ValueError` guard are safe |

---

## 5. Verified Claims vs. Gaps

### Verified Claims
- **Trait Sum Invariant ($\sum = 12$)**: Verified across 50,000 fuzzed iterations and 10,000 continuous generations. Strictly preserved (`Traits.shift` + `Traits.__post_init__`).
- **Trait Value Range ($[0, 5]$)**: Verified across all fuzzed iterations. No value ever drops below 0 or exceeds 5.
- **Biological Feature Mutation**: Verified 1-of-3 swap from `FEATURES`, preserving 3 unique keys and valid `Kit` generation.
- **Sequential Integer ID Formatting**: Verified `allocate_creature_id` generates `f"{species}:{idx}"` with monotonic `idx`, preventing sorting failures in `creature_sort_key`.
- **Spatial Clearance**: Verified that parents enclosed by impassable terrain (`Terrain.ROCK`) return `None` without deducting energy or setting cooldown.
- **Reproduction Gates**: Verified exact boundary behavior for energy (80% / 70%), age (30), streak (20), cooldown (25/12), and local crowding (4).

### Gaps & Failures
- **Carrying Capacity Enforcement**: FAILED. Active population exceeds 35 in runs $> 25$ ticks.
- **Offspring Mortality Model**: FAILED. Offspring respawn infinitely after death.
- **Extinction Permanence**: FAILED. Extinct species resurrect automatically 5 ticks post-extinction.

---

## 6. Caveats

- **Network Joiner Offspring Handling**: In networked multiplayer matches, clients that do not track telemetry frames will leave newborn offspring under the default reflex controller. This is expected behavior and conforms to specifications.
- No other caveats.

---

## 7. Conclusion

Milestone M1_EVO implements the genetic mutation algorithms, feature rolling, and reproduction gates cleanly and authentically without hardcoded shortcuts or integrity violations. However, the simulation's carrying capacity guardrails fail under multi-generational runs because deceased offspring reincarnate infinitely via `try_respawn()`, causing total population to exceed `POPULATION_GLOBAL_MAX = 35` and `POPULATION_SPECIES_MAX = 7`.

**Verdict**: **REQUEST_CHANGES**

---

## 8. Verification Method

To independently verify these findings:

1. **Run Adversarial Carrying Capacity Stress Test**:
   ```bash
   pytest tests/test_evolution_adversarial.py -v
   ```
   *Observed Failure*: 2 failed (`test_adversarial_carrying_capacity_unforced_500_ticks` and `test_adversarial_carrying_capacity_forced_high_energy_500_ticks`).

2. **Run Population Trajectory Reproduction Script**:
   ```bash
   python3 -c "
   from genesis.tick import build_match, tick
   w, creatures, state, rng = build_match(seed=42)
   for t in range(1, 301):
       tick(w, creatures, tick_no=t, rng=rng, state=state)
       alive = sum(1 for c in creatures if c.alive)
       if alive > 35:
           print(f'Cap breached at tick {t}: alive={alive} > 35, total_creatures={len(creatures)}')
           break
   "
   ```
   *Observed Output*: Cap breached around tick 140–250 with alive count $> 35$.

3. **Check Evolution Unit Tests**:
   ```bash
   pytest tests/test_evolution.py -v
   ```
   *Observed Result*: 11 passed (covers single-tick logic only).

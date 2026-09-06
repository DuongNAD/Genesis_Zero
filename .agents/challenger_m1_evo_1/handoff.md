# Handoff Report: Adversarial Challenge — Milestone M1_EVO

**Agent**: Challenger 1 (Empirical Challenger)  
**Recipient**: Parent Orchestrator (`parent`, id: `acd85475-3c3a-47fd-b10c-111536f0a2fe`)  
**Date**: 2026-09-03  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_1`  
**Handoff Type**: Hard (Adversarial Challenge Complete)  
**Verdict**: **`REQUEST_CHANGES`**

---

## 1. Observation

Direct empirical observations from test runs, command outputs, and source code inspection:

1. **Trait Mutation 10,000 Generation Stress Test**:
   - Command: `pytest tests/test_evolution_adversarial.py -k test_adversarial_trait_mutation_10000_generations -v`
   - Scope: 10,000 continuous successive mutation generations across all 5 founder species (`L1`..`L5`) (50,000 mutations) + 10,000 continuous mutations across 4 extreme boundary trait vectors (`[5, 5, 2, 0, 0, 0]`, `[0, 0, 0, 2, 5, 5]`, `[5, 0, 5, 0, 2, 0]`, `[2, 2, 2, 2, 2, 2]`) (40,000 mutations) = **90,000 continuous mutations**.
   - Result: **PASSED (100%)**.
     - $\sum \equiv 12$ across all 90,000 generations (0 sum drift).
     - $\forall v \in \text{traits}: 0 \le v \le 5$ at all times (0 out-of-bounds).
     - $\sum d\_tr \equiv 0$ across all variance evaluations.

2. **Creature ID Sorting Safety Test**:
   - Command: `pytest tests/test_evolution_adversarial.py -k test_adversarial_creature_id_sorting_safety -v`
   - Scope: 1,000,000 creature instances sorted via `creature_sort_key` + hostile edge case strings (`""`, `":"`, `"::"`, `"L1"`, `"L1:abc"`, `"L1:123a"`, `"L1:-5"`, `"L1: 42"`, `"L1:sub:99"`, `"complex:name:with:colons:123"`, `"L1:１２３"`, `"SPECIES:\n42"`, `"SP:\x00:99"`, `"L1:999999999999"`).
   - Result: **PASSED (100%)**.
     - Zero `ValueError` or unhandled exceptions.
     - Graceful fallback to `(species, 999999)` when non-numeric tails are parsed.
     - Deterministic and monotonic order preserved.

3. **Carrying Capacity Fuzzing under Forced High Energy (500 ticks)**:
   - Command: `pytest tests/test_evolution_adversarial.py -k test_adversarial_carrying_capacity_forced_high_energy_500_ticks -v`
   - Result: **FAILED** (Exit code 1).
     - Verbatim error:
       ```
       AssertionError: Population cap violated 1254 times across 500 ticks! Peak alive=52 (cap=35), Peak species={'A1': 8, 'L1': 8, 'L2': 7, 'L3': 14, 'L4': 6, 'L5': 10, 'W1': 6} (cap=7). First violations: [(26, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (27, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (29, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (35, 'GLOBAL_CAP_EXCEEDED: 36 > 35'), (41, 'GLOBAL_CAP_EXCEEDED: 36 > 35')]
       ```
     - Observed peak active population: **52** (Global cap: `POPULATION_GLOBAL_MAX = 35`, +48.6% overflow).
     - Observed peak species population: **14** for species L3 (Species cap: `POPULATION_SPECIES_MAX = 7`, +100% overflow / double the cap).
     - Total tick violations: **1,254 violations**.

4. **Carrying Capacity Invariants in Natural Unforced Simulation (500 ticks)**:
   - Command: `pytest tests/test_evolution_adversarial.py -k test_adversarial_carrying_capacity_unforced_500_ticks -v`
   - Result: **FAILED** across multiple seeds:
     - Seed 1: peak alive = **50** (Global cap: 35; 286 violations; max species alive = 15 vs cap of 7).
     - Seed 2: peak alive = **56** (Global cap: 35; 1,062 violations; max species alive = 15).
     - Seed 42: peak alive = **50** (Global cap: 35; 1,048 violations; max species alive = 13).
     - Seed 100: peak alive = **45** (Global cap: 35; 1,203 violations; max species alive = 13).
     - Seed 2026: peak alive = **43** (Global cap: 35; 692 violations; max species alive = 11).

5. **Source Code Implementation Flaw**:
   - In `genesis/evolution.py:150-157` (`can_reproduce`):
     ```python
     alive_all = [x for x in creatures if x.alive]
     if len(alive_all) >= config.POPULATION_GLOBAL_MAX:
         return False, "GLOBAL_CAP_REACHED"
     alive_sp = [x for x in alive_all if x.species == c.species]
     if len(alive_sp) >= config.POPULATION_SPECIES_MAX:
         return False, "SPECIES_CAP_REACHED"
     ```
     `can_reproduce` only inspects `x.alive`. Any creature currently dead and waiting for its respawn timer (`c.dead_until >= 0`) is omitted from the count.
   - In `genesis/creature.py:202-227` (`try_respawn`):
     ```python
     def try_respawn(c: Creature, world: World, tick: int, rng: random.Random) -> bool:
         if c.alive or c.dead_until < 0 or tick < c.dead_until:
             return False
         ...
         c.alive = True
         return True
     ```
     `try_respawn` does not perform any carrying capacity check (`POPULATION_GLOBAL_MAX` or `POPULATION_SPECIES_MAX`).
   - In `genesis/tick.py:533-577`:
     When an offspring dies, it is not removed from `creatures`; it enters `kill(c)` and receives `c.dead_until = tick + config.RESPAWN_DELAY (20)`. The offspring reincarnates indefinitely, permanently inflating the size of `creatures` (reaching 67 entities by tick 500).

---

## 2. Logic Chain

1. **Reproduction Vacates Slots via Temporary Deaths (Observations 3, 4, 5)**:
   - When a simulation runs, creatures periodically die from starvation, combat, or poison.
   - When creature $C_1$ dies at tick $t$, `kill()` sets $C_1.\text{alive} = \text{False}$ and $C_1.\text{dead\_until} = t + 20$.
   - For the subsequent 20 ticks ($t+1 \dots t+20$), $C_1$ is not counted in `alive_all` inside `can_reproduce()`.
   - As a result, `len(alive_all) < POPULATION_GLOBAL_MAX (35)` and `len(alive_sp) < POPULATION_SPECIES_MAX (7)`.

2. **Uncontrolled Births during Respawn Latency Window (Observation 5)**:
   - Because $C_1$'s slot is perceived as vacant, other mature living creatures reproduce.
   - A new child $C_{\text{new}}$ is created and appended to `creatures`.
   - Now `len(alive_all)` reaches 35 again.

3. **Respawn Timing Collision Breaches Caps (Observations 3, 4, 5)**:
   - At tick $t+20$, $C_1$'s respawn timer expires.
   - In phase 5 of `genesis/tick.py`, `try_respawn(C_1)` is invoked.
   - `try_respawn` checks only whether $C_1$'s respawn timer has elapsed and whether a passable tile exists. It has **no check** against `POPULATION_GLOBAL_MAX` or `POPULATION_SPECIES_MAX`.
   - $C_1$ transitions to $\text{alive} = \text{True}$.
   - The total living population becomes $35 + 1 = 36$.
   - As this cycle repeats over 500 ticks across multiple species and deaths, the total number of creatures in the simulation list accumulates to 67+, and the active living population swells to **52** (forced energy) and up to **56** (natural unforced run in Seed 2), with individual species reaching **14-15** active organisms (double the species limit of 7).

4. **Violation of Architectural Contracts (PROJECT.md § Feature Inventory #22 & §1 Interface Contracts)**:
   - `PROJECT.md` line 116 explicitly mandates:
     *"Enforces len([c for c in creatures if c.alive]) < POPULATION_GLOBAL_MAX (35) and species living count < POPULATION_SPECIES_MAX (7)."*
   - `ORIGINAL_REQUEST.md` line 67 requires:
     *"Extinction and overpopulation caps maintain stable simulation performance across multi-generational runs."*
   - The current implementation fails this contract under both adversarial stress and standard gameplay.

---

## 3. Caveats

- **Trait mutation mechanics** (`mutate_traits`, `trait_variance`, zero-sum invariant) are mathematically sound and robust under 90,000 successive mutation generations.
- **Creature ID sorting** (`creature_sort_key`) is fully robust against malformed strings and scales safely to 1,000,000+ IDs.
- No other components were modified or compromised.

---

## 4. Conclusion

**Verdict: `REQUEST_CHANGES`**

Milestone M1_EVO cannot be approved in its current state because the carrying capacity guardrails collapse during multi-generational simulation, permitting active population to exceed the global cap by up to **+60.0%** (56 vs 35) and the species cap by up to **+114.3%** (15 vs 7).

### Required Remediation for Worker M1_EVO:
To fix this flaw and achieve approval, Worker must implement one or both of the following guardrails:

1. **Cap-Gated Respawning in `genesis/creature.py:try_respawn` or `genesis/tick.py`**:
   Before setting `c.alive = True` in `try_respawn` (or in the respawn phase of `tick.py`), verify carrying capacity:
   ```python
   alive_global = sum(1 for x in creatures if x.alive)
   if alive_global >= config.POPULATION_GLOBAL_MAX:
       return False  # Postpone respawn to next tick
   alive_sp = sum(1 for x in creatures if x.alive and x.species == c.species)
   if alive_sp >= config.POPULATION_SPECIES_MAX:
       return False  # Postpone respawn to next tick
   ```
2. **Account for Pending Respawns in `genesis/evolution.py:can_reproduce`**:
   Ensure `can_reproduce` evaluates total allocated slots (active + pending respawn):
   ```python
   allocated_all = [x for x in creatures if x.alive or x.dead_until >= 0]
   if len(allocated_all) >= config.POPULATION_GLOBAL_MAX:
       return False, "GLOBAL_CAP_REACHED"
   allocated_sp = [x for x in allocated_all if x.species == c.species]
   if len(allocated_sp) >= config.POPULATION_SPECIES_MAX:
       return False, "SPECIES_CAP_REACHED"
   ```
3. **Mortal Offspring Lifecycle**:
   Alternatively, distinguish between immortal founder lineage slots (`parent_id is None` or `generation == 0`) which respawn, and reproduced offspring (`parent_id is not None`) which do not respawn upon death (or are permanently retired when killed, allowing natural extinction and preventing unbounded creature accumulation in `creatures`).

---

## 5. Verification Method

To independently verify these empirical results:

1. **Run Full Adversarial Suite**:
   ```bash
   pytest tests/test_evolution_adversarial.py -v
   ```
   *Expected output*: 2 passed (trait mutations and ID sorting), 2 failed (carrying capacity forced high energy and unforced multi-seed).

2. **Verify Trait Mutation 10,000 Generation Invariant Independently**:
   ```bash
   pytest tests/test_evolution_adversarial.py -k test_adversarial_trait_mutation_10000_generations -v
   ```
   *Result*: `PASSED` (90,000 continuous mutations, 0 drift).

3. **Verify Creature ID Sorting Robustness Independently**:
   ```bash
   pytest tests/test_evolution_adversarial.py -k test_adversarial_creature_id_sorting_safety -v
   ```
   *Result*: `PASSED` (100k-1M IDs, hostile malformed inputs, 0 exceptions).

4. **Verify Carrying Capacity Breach**:
   ```bash
   pytest tests/test_evolution_adversarial.py -k test_adversarial_carrying_capacity_forced_high_energy_500_ticks -v
   ```
   *Result*: `FAILED` (Peak alive=52 > 35, Peak species=14 > 7, 1254 violations).

5. **Verify Unforced Natural Carrying Capacity Breach**:
   ```bash
   pytest tests/test_evolution_adversarial.py -k test_adversarial_carrying_capacity_unforced_500_ticks -v
   ```
   *Result*: `FAILED` (Seed 1 peak alive=50 > 35, Seed 2 peak alive=56 > 35).

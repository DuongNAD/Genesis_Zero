# Handoff Report: Milestone M1_EVO Independent Review (Reviewer 2)

**Reviewer**: Reviewer 2 (Roles: Reviewer, Adversarial Critic)  
**Target Milestone**: `M1_EVO` (Generational Evolution & Mutation)  
**Recipient**: Parent Orchestrator (`parent`, id: `acd85475-3c3a-47fd-b10c-111536f0a2fe`)  
**Date**: 2026-09-03  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m1_evo_2`  
**Verdict**: **REQUEST_CHANGES**  
**Handoff Type**: Hard (Review Complete)

---

## 1. Observation

### 1.1 Source Code & Implementation Inspection
- **`genesis/evolution.py`**:
  - Implements bounded stochastic mutation via `mutate_traits` (lines 31–58) using `traits.shift(donor, recipient)` ensuring `sum(traits) == 12` and all traits within `[0, 5]`.
  - Implements biological feature inheritance and mutation via `mutate_features` (lines 60–83), swapping 1-of-3 features from `FEATURES`.
  - Implements vector trait variance `trait_variance` (lines 85–95) measuring `traits - founder_traits`.
  - Implements reproduction gating `can_reproduce` (lines 117–168) validating:
    - Alive status (`c.alive`)
    - Minimum age (`c.age >= config.REPRODUCE_MIN_AGE`, 30 ticks)
    - Living streak (`c.ticks_alive_streak >= config.REPRODUCE_MIN_STREAK`, 20 ticks)
    - Cooldown (`c.reproduce_cooldown <= 0`)
    - Energy threshold (`c.energy >= 0.80 * energy_max`, reduced to `0.70` with law discovery bonus via `has_law_discovery`)
    - Global population cap (`len(alive) < config.POPULATION_GLOBAL_MAX`, 35)
    - Species population cap (`alive_species < config.POPULATION_SPECIES_MAX`, 7)
    - Local Chebyshev crowding suppression (`radius=2, max_neighbors=4`).
  - Implements spatial clearance placement in `reproduce_offspring` (lines 170–234) ensuring the newborn is placed only in cells passable according to its individual kit (`world.passable(p, child)`).
  - Implements `resolve_reproduction` (lines 236–320) with deterministic ordering via `creature_sort_key`, deducting `config.REPRODUCE_COST` (35.0 energy), setting cooldown (25 ticks or 12 on discovery), and emitting `"REPRODUCE"` event.
  - Implements `detect_extinctions` (lines 323–353) tracking `extinct_species` and emitting `"EXTINCTION"` once per extinction event.
- **`genesis/creature.py`**:
  - `Creature` dataclass extended with lineage fields (lines 38–44): `parent_id`, `lineage_id`, `birth_tick`, `reproduce_cooldown`, `features`, `_kit`.
  - `Creature.kit` property (lines 50–61) lazily builds and caches individual `Kit` from `self.features` via `kit_of`, with fallback to `None`.
  - `allocate_creature_id` (lines 67–81) inspects existing creatures of that species and returns `f"{species}:{max_idx + 1}"`, preventing ID collisions and ensuring integer index monotonicity.
  - `creature_sort_key` (lines 140–144) wraps `int(idx)` in `try...except ValueError` returning `(species, 999999)` for bulletproof sorting crash immunity.
  - `upkeep_and_check_death` (lines 175–176) reads `effective_kit = kit if kit is not None else getattr(c, "kit", None)`.
  - `random_step` and `try_respawn` (lines 153, 213) call `world.passable(p, c)`.
- **`genesis/world.py`**:
  - `passable` (line 294): `kit = getattr(creature, "kit", None) or self.kits.get(creature.species)`.
  - `touchable` (line 302): `kit = getattr(creature, "kit", None) or self.kits.get(creature.species)`.
  - `food_for` (line 322): `kit = getattr(creature, "kit", None) or self.kits.get(creature.species)`.
  - `visible` (lines 428, 448): `kit = getattr(obs, "kit", None) or world.kits.get(obs.species)`.
- **`genesis/tick.py`**:
  - `SimState` extended with `extinct_species: set[str]` and `reproduction_enabled: bool | None = None`.
  - `build_match` accepts `reproduction: bool | None = None` parameter (line 80).
  - Tick phase 3.5 executes reproduction gated by `repro_on` (lines 415–431).
  - Extinction detection integrated at tick phase 5.5 (lines 578–582).
  - **CRITICAL DEFECT OBSERVED in tick phase 5 (lines 568–576)**:
    ```python
    respawn_events: list[dict] = []
    for c in sorted(creatures, key=creature_sort_key):
        crng = creature_rng(state.match_seed, tick_no, c.id)
        if try_respawn(c, world, tick_no, crng):
            respawn_events.append(...)
    ```
    Neither `tick.py` nor `try_respawn` in `creature.py:202` checks `POPULATION_GLOBAL_MAX` or `POPULATION_SPECIES_MAX` before resurrecting dead organisms (`c.alive = True`).

### 1.2 Test Suite Execution Results
1. `pytest tests/test_evolution.py -v`: **11 passed in 0.24s** (100%).
2. `pytest tests/test_trait_shift.py tests/test_score.py tests/test_maps.py -v`: **27 passed in 61.40s** (100%).
3. `pytest tests/test_llm_tick.py tests/test_lifecycle.py -v`: **16 passed in 11.53s** (100%).
4. `pytest tests/test_adversarial_m1.py tests/test_domain_passability.py tests/test_empirical_challenger_m1_rep.py tests/test_empirical_passability_stress.py -v`: **36 passed in 90.80s** (100%).
5. `pytest tests/test_adversarial_m1_evo_2.py -v`: **20 passed in 0.26s** (100%).
6. `pytest tests/test_evolution_adversarial.py -v`: **2 FAILED, 2 passed in 5.51s**:
   - `FAILED tests/test_evolution_adversarial.py::test_adversarial_carrying_capacity_unforced_500_ticks`
     ```
     AssertionError: Seed 1 natural run violated global cap 286 times! Peak alive=50 > 35. First violations: [(143, 38), (144, 38), (145, 38), (166, 36), (173, 36)]
     ```
   - `FAILED tests/test_evolution_adversarial.py::test_adversarial_carrying_capacity_forced_high_energy_500_ticks`
     ```
     AssertionError: Population cap violated 1254 times across 500 ticks! Peak alive=52 (cap=35), Peak species={'A1': 8, 'L1': 8, 'L2': 7, 'L3': 14, 'L4': 6, 'L5': 10, 'W1': 6} (cap=7).
     ```
7. `ruff check genesis/evolution.py genesis/tick.py genesis/creature.py genesis/domain.py tests/test_evolution.py tests/test_trait_shift.py`: **All checks passed! Zero errors.**

---

## 2. Review Summary & Findings

### [Critical] Finding 1: Carrying Capacity Caps Breached via Unconstrained Respawn (Peak Alive = 52 vs Cap 35, Peak Species = 14 vs Cap 7)

- **What**: During natural multi-generational simulations (500 ticks), the global population cap (`POPULATION_GLOBAL_MAX = 35`) was violated 286 times (reaching 50 active organisms), and under forced reproduction it reached 52 active organisms with species populations reaching 14 (cap 7).
- **Where**:
  - `genesis/tick.py:568-576` (Respawn loop in tick execution)
  - `genesis/creature.py:202-228` (`try_respawn`)
- **Why**:
  - While `genesis/evolution.py:can_reproduce` correctly checks that `len([x for x in creatures if x.alive]) < config.POPULATION_GLOBAL_MAX` and `len(alive_species) < config.POPULATION_SPECIES_MAX` before permitting new births, when an existing creature dies, `alive` count drops.
  - Living creatures reproduce to replace the deceased creature, bringing `alive` count back up to the cap (35).
  - Later, when the dead creature's respawn timer (`c.dead_until`) elapses (20 ticks), `try_respawn` in `tick.py:571` resurrects the creature (`c.alive = True`) **unconditionally without checking whether the global or species population cap is currently reached**.
  - In addition, all newborn offspring added to `creatures` are never pruned; when they die, they too enter the `try_respawn` queue and resurrect indefinitely.
  - This causes the total living population to ratchet upwards across generations, breaching acceptance criteria in `ORIGINAL_REQUEST.md` ("Extinction and overpopulation caps maintain stable simulation performance across multi-generational runs") and failing `tests/test_evolution_adversarial.py`.
- **Suggestion**:
  - In `genesis/tick.py:568-576` (or in `try_respawn`), enforce population cap checks before resurrecting dead creatures:
    ```python
    alive_count = sum(1 for x in creatures if x.alive)
    sp_counts = {sp: sum(1 for x in creatures if x.alive and x.species == sp) for sp in config.FOUNDERS}
    for c in sorted(creatures, key=creature_sort_key):
        if not c.alive and c.dead_until >= 0 and tick_no >= c.dead_until:
            if alive_count >= config.POPULATION_GLOBAL_MAX:
                continue  # Defer respawn until space is available
            if sp_counts.get(c.species, 0) >= config.POPULATION_SPECIES_MAX:
                continue  # Defer respawn for this species
            crng = creature_rng(state.match_seed, tick_no, c.id)
            if try_respawn(c, world, tick_no, crng):
                alive_count += 1
                sp_counts[c.species] = sp_counts.get(c.species, 0) + 1
                respawn_events.append(...)
    ```
  - Alternatively, specify whether non-founder offspring (`c.generation > 0`) should die permanently upon death without respawning (generational turnover), or if they do respawn, strictly gate respawn behind the population caps.

---

## 3. Verified Claims

- Trait mutation preserves `sum(traits) == 12` and `0 <= trait <= 5` -> Verified via 1,000 iterations in `test_trait_mutation_invariants_1000_iterations` and 500 extreme-boundary mutations -> **PASS**.
- Trait variance `d_tr` sums to zero -> Verified via `test_trait_variance_vector_sums_to_zero` -> **PASS**.
- Feature mutation rolls valid features in `FEATURES` -> Verified via `test_feature_mutation_valid_pool_and_kit` and 500 adversarial rounds -> **PASS**.
- Interface conformance for `world.passable` with `c.kit or world.kits.get(c.species)` -> Verified via `test_feature_mutation_passability_effect` and custom adversarial kit override probes -> **PASS**.
- Sequential integer ID monotonicity (`f"{species}:{idx}"`) and sorting crash immunity (`creature_sort_key`) -> Verified via `test_lineage_metadata_and_integer_id_sorting` and non-integer ID stress probes -> **PASS**.
- Legacy test isolation for `test_trait_shift.py`, `test_score.py`, and `test_maps.py` -> Verified via `pytest` (27 passed) -> **PASS**.
- Carrying capacity enforcement over 500 ticks -> Verified via `tests/test_evolution_adversarial.py` -> **FAIL (Critical Finding 1)**.

---

## 4. Caveats

- The core evolutionary algorithms, feature mutation mechanics, and interface contracts are cleanly designed and implemented with zero integrity violations.
- The failure is specifically an interaction between the legacy `try_respawn` mechanism and the new generational reproduction loop over extended timelines (>35 ticks). Once `try_respawn` is gated by the population caps, the entire test suite will pass cleanly.

---

## 5. Conclusion

- **Verdict**: **REQUEST_CHANGES**
- Milestone `M1_EVO` cannot be approved until Critical Finding 1 is resolved, ensuring that total living organisms and per-species living counts never exceed `POPULATION_GLOBAL_MAX` (35) and `POPULATION_SPECIES_MAX` (7) during extended simulations, and `tests/test_evolution_adversarial.py` achieves a 100% pass rate.

---

## 6. Verification Method

To reproduce the failure and independently verify the fix:

```bash
# Reproduce the carrying capacity failure:
pytest tests/test_evolution_adversarial.py -v

# Verify baseline evolution tests:
pytest tests/test_evolution.py -v

# Verify legacy isolated regression tests:
pytest tests/test_trait_shift.py tests/test_score.py tests/test_maps.py -v
```

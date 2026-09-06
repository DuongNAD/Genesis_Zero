# Comprehensive Technical Survey: Generational Evolution & Genetic Mutation (R1)

**Author**: Explorer 1 (Evolution & Mutation Specialist)  
**Date**: 2026-09-03  
**Target Milestone**: R1 (Generational Evolution & Genetic Mutation)  
**Status**: COMPLETE  

---

## Executive Summary

This survey analyzes the Genesis Zero core simulation engine and designs the technical architecture for **Generational Evolution & Genetic Mutation (R1)**. 

In the baseline engine, "evolution" is limited to post-mortem adaptation (`genesis/lineage.py`), where upon death a creature's slot is recycled, incrementing `c.generation` and applying a single Lamarckian trait shift biased by the cause of death. Organisms cannot reproduce during life, population size remains strictly frozen to founder slots, features are static per species (`world.kits[species_id]`), and there is no branching lineage tree.

To satisfy Requirement R1, Genesis Zero must transition to **emergent Darwinian generational reproduction**: living organisms that achieve metabolic surplus, survival maturity, and law discovery milestones can reproduce offspring. Offspring inherit parental numeric traits and biological features with bounded stochastic mutations, expanding lineages dynamically while maintaining strict carrying capacity caps and zero simulation regressions.

---

## 1. Codebase Investigation & Baseline Architecture

### 1.1 Investigated Modules & Current Roles

| Module | Current Role | Current Limitation regarding Evolution |
| :--- | :--- | :--- |
| `genesis/creature.py` | Defines `Creature` dataclass, `spawn_population`, `random_step`, `upkeep_and_check_death`, `try_respawn`, `creature_sort_key`. | `id` is hard-coded to `f"{species}:{idx}"` slots (e.g. `"L1:0"`). `generation` exists but only increments on death-rebirth. No `parent_id`, `lineage_id`, or individual feature kit. |
| `genesis/traits.py` | Defines immutable `Traits` (brain, attack, armor, speed, sense, stomach) with invariants $\sum=12, 0 \le v \le 5$, and `shift(frm, to)`. | Operates on individual vectors. Lacks a stochastic mutation generator that safely samples valid donor/recipient pairs with controllable drift variance. |
| `genesis/features.py` | Defines 12 biological features (`LUONG_CU`, `DAO_HANG`, etc.) and `Kit`. Sets features per *species* (`roll_for_species`) stored in `world.kits[species_id]`. | Features are immutable per species across an entire match; individual offspring cannot inherit or mutate distinct morphological features. |
| `genesis/domain.py` | Implements 3-tier passability (`can_enter`, `can_touch`) across `NUOC`, `CAN`, `TROI`. | Checks `can_enter(domain, terrain, traits, kit)`. If individual creatures mutate features, `passable` must check the creature's own `kit`. |
| `genesis/world.py` | 24x24 toroidal grid, terrain erosion (`erode_cores`), plants/algae spawning, passability routing (`passable`, `touchable`, `food_for`). | `world.kits` maps `species_id -> Kit`. Food generation is capped at `PLANT_MAX = 15` and `ALGAE_MAX = 36`, which sets the hard biological boundary for sustainable population size. |
| `genesis/tick.py` | 6-phase deterministic tick cycle: (0) think, (1) collect intents, (2) simultaneous actions, (3) upkeep & combat mortality, (4) hidden laws, (5) death/rebirth, (6) world & logging. | Has no reproduction phase. Population count remains fixed to initial founder counts throughout all ticks. |
| `genesis/lineage.py` | Post-death `inherit(parent, cause)` and `rebirth(c, cause)`. Decays codex confidence on death. | Purely reactive to death. Does not support birth of new distinct individuals, branching lineages, or variance tracking. |
| `net/match.py` | Match lifecycle, WebSocket frame generation (`/v1/spectate`), registration of species and remote clients. | Telemetry `creatures` payload serializes `id, x, y, hp, e, e_max, alive, feral, tr, species, domain, features` (from `world.kits[species]`). Lacks `gen`, `parent_id`, `lineage`, and trait variance deltas. |
| `genesis/score.py` | Match verification and scoring (`score_match`, `decide_victory`). Evaluates hypothesis retention and survival ratio $R_{survive}$. | Expects consistent `creature_id` and `species_id` logs. |

---

## 2. Reproduction Trigger Conditions

To ensure biologically meaningful evolution rather than runaway swarming, reproduction must require meeting three distinct gating dimensions: metabolic energy surplus, survival maturity, and cognitive/discovery fitness.

```
+-----------------------------------------------------------------------------+
|                        REPRODUCTION ELIGIBILITY GATE                        |
|                                                                             |
| 1. Energy Gating:        c.energy >= REPRODUCE_ENERGY_THRESHOLD (80% max)    |
| 2. Maturity Gating:      c.age >= REPRODUCE_MIN_AGE (30 ticks)              |
| 3. Streak Gating:        c.ticks_alive_streak >= REPRODUCE_MIN_STREAK (20)  |
| 4. Refractory Cooldown:  c.reproduce_cooldown <= 0                          |
| 5. Spatial Clearance:    At least 1 passable cell in Chebyshev neighborhood  |
| 6. Population Ceiling:   world_alive < POPULATION_GLOBAL_MAX (35)           |
|                          species_alive < POPULATION_SPECIES_MAX (8)         |
+-----------------------------------------------------------------------------+
                                       | ALL GATES PASS
                                       v
+-----------------------------------------------------------------------------+
|                            REPRODUCTION EXECUTION                           |
|                                                                             |
| * Parent energy deducted: c.energy -= REPRODUCE_COST (35.0 energy)          |
| * Parent cooldown set:    c.reproduce_cooldown = 25 ticks                   |
| * Child allocated:        f"{species}:{next_integer_index}"                 |
| * Child initial energy:   child.energy = 30.0 (or 40% of energy_max)        |
| * Child spawned in:       passable neighbor cell                            |
+-----------------------------------------------------------------------------+
```

### 2.1 Energy Threshold & Metabolic Cost
1. **Surplus Requirement**:
   - Organism must reach `c.energy >= config.REPRODUCE_ENERGY_RATIO * c.traits.energy_max` (recommended: `0.80` to `0.85`).
   - With base stomach traits, `energy_max` ranges from $85$ (`stomach=0`) to $125$ (`stomach=5`). Thus, a creature must accumulate $\ge 68$ to $106$ energy before it can bear offspring.
2. **Reproduction Cost (Energy Conservation)**:
   - Reproduction is not free; parent energy is reduced by `REPRODUCE_COST = 35.0` (or `0.35 * parent.traits.energy_max`).
   - The newborn offspring receives `child.energy = 30.0` (with $5.0$ metabolic waste dissipated as biological heat/tax).
   - This directly prevents infinite reproduction loops: immediately after reproduction, parent energy drops below $0.50 \times \text{energy\_max}$, dropping it out of the reproduction window until it forages again.

### 2.2 Survival Duration & Refractory Period
1. **Maturity Age Gate**:
   - `c.age >= config.REPRODUCE_MIN_AGE` (default: 30 ticks). Newborns cannot reproduce immediately; they must survive childhood.
2. **Survival Streak Gate**:
   - `c.ticks_alive_streak >= config.REPRODUCE_MIN_STREAK` (default: 20 ticks). Organism must have demonstrated sustained viability without near-death resets.
3. **Refractory Cooldown Period**:
   - `c.reproduce_cooldown` initialized to `config.REPRODUCE_COOLDOWN = 25` ticks upon successful birth.
   - Decremented by 1 each tick. No organism can reproduce more than once every 25 ticks.

### 2.3 Law Discovery Achievement Gating & Epistemic Acceleration
Genesis Zero is fundamentally a benchmark of hypothesis formation and scientific induction. Connecting discovery to reproductive fitness creates an emergent evolutionary incentive:
- **Discovery Bonus**: If a creature logs a successful Codex discovery (`len(codex.verified_entries()) > 0` or high confidence hypothesis $\ge 4$):
  - Reproduction cooldown reduced by $50\%$ (`cooldown //= 2`).
  - Energy threshold relaxed to `0.70 * energy_max`.
- This ensures species that accurately decode hidden physical laws out-compete blind forager species, realizing the core thesis of Genesis Zero: *cognitive model size and inductive accuracy yield evolutionary fitness*.

### 2.4 Spatial Clearance & Birth Placement
- The child must spawn in a vacant or passable cell within parent's Chebyshev neighborhood:
  `candidates = [p for p in world.neighbors(parent.pos) if world.passable(p, child) and p not in occupied_cells]`
- If no adjacent passable cell exists (e.g. surrounded by rocks or deep water for a terrestrial creature), birth is postponed until spatial clearance is achieved.

---

## 3. Offspring Inheritance & Bounded Stochastic Mutation Mechanics

### 3.1 Numeric Traits Inheritance & Invariant Guarantees
Offspring inherit parental numeric traits with bounded stochastic mutation.

```
Parent Traits:  [ brain: 3, attack: 2, armor: 2, speed: 2, sense: 2, stomach: 1 ] (Sum = 12)
                                       |
                   Stochastic Mutation Event (p = 0.40)
                   Donor: armor (2 -> 1) | Recipient: speed (2 -> 3)
                                       v
Child Traits:   [ brain: 3, attack: 2, armor: 1, speed: 3, sense: 2, stomach: 1 ] (Sum = 12)
```

#### Mutation Operator Rules
1. **Inheritance Baseline**: `child_traits = parent.traits`
2. **Mutation Trigger**: With probability $P_{\text{mutate\_trait}} = 0.40$ (configurable in `genesis/config.py`):
   - Identify valid donor traits: $G = \{t \in \text{TRAIT\_NAMES} \mid \text{getattr}(child, t) > \text{TRAIT\_MIN}\}$.
   - Identify valid recipient traits: $R = \{t \in \text{TRAIT\_NAMES} \mid t \ne \text{donor}, \text{getattr}(child, t) < \text{TRAIT\_MAX}\}$.
   - Deterministically sample $(\text{frm}, \text{to})$ using child's deterministic RNG stream:
     `rng = creature_rng(seed, tick, f"{child_id}:mutate")`.
   - Apply single-point transfer: `child_traits = child_traits.shift(frm, to)`.
3. **Strict Invariant Guarantees**:
   - **Conservation of Trait Sum**: $\sum_{t} \text{trait}_t \equiv 12$ holds identically.
   - **Range Bounds**: $0 \le \text{trait}_t \le 5$ holds identically.
   - **Brain Drift Boundary**: Brain changes alter LLM token budget and Codex capacity (`CODEX_SIZE_BY_BRAIN`). Shifting brain to 0 or 5 remains within supported ranges $[0, 5]$ since all lookup tables in `genesis/law_config.py` explicitly handle $0..5$.

### 3.2 Biological Features Inheritance & Stochastic Mutation
In the baseline, features are immutable and shared across all individuals of a species via `world.kits[c.species]`. Under R1:
1. **Creature-Level Feature State**:
   - Each creature carries its own `features: tuple[str, ...]` (e.g. `("LUONG_CU", "LONG_DAI", "MAT_DEM")`).
   - Founders inherit `roll_for_species(c.species, seed)`.
2. **Offspring Feature Mutation**:
   - With mutation probability $P_{\text{mutate\_feat}} = 0.15$:
     - Select one existing feature to replace: `drop_feat = rng.choice(child.features)`.
     - Select replacement from unpossessed features: `pool = [f.key for f in FEATURES if f.key not in child.features]`.
     - `new_feat = rng.choice(pool)`.
     - `child.features = tuple(sorted([f for f in child.features if f != drop_feat] + [new_feat]))`.
3. **Individualized `Kit` Compilation**:
   - Compile individualized kit: `child.kit = kit_of(tuple(BY_KEY[k] for k in child.features))`.
   - Update `World.passable`, `World.touchable`, and combat calculations:
     ```python
     kit = getattr(creature, "kit", None) or world.kits.get(creature.species)
     ```
   - If an offspring mutates `LUONG_CU` (amphibious), it immediately gains the ability to traverse both `NUOC` and `CAN` terrains, even if its parent was terrestrial.
   - If an offspring mutates `TREO_GIOI` (climbing), its tree-climb speed threshold decreases by 2.
   - 3D visualizer automatically renders the new morphological meshes based on `c.features` in telemetry!

---

## 4. Lineage Tracking Metadata & Dynamics

### 4.1 Schema Additions to `Creature`

In `genesis/creature.py`:

```python
@dataclass
class Creature:
    id: str                 # Canonical format "<species_id>:<integer_idx>"
    species: str
    traits: Traits
    pos: tuple[int, int]
    hp: float
    energy: float
    age: int = 0
    alive: bool = True
    dead_until: int = -1
    poison_ticks: int = 0
    poison_from: str | None = None
    adapt_points: int = 0
    eat_count: int = 0
    win_count: int = 0
    ticks_alive_streak: int = 0
    shift_log: list[tuple[str, str]] = field(default_factory=list)
    last_drink_tick: int = -1
    stun_ticks: int = 0
    generation: int = 0
    
    # ── R1 Evolutionary Lineage Extensions ──────────────────────────────────
    parent_id: str | None = None               # None for generation 0 founders
    lineage_id: str = ""                       # Root founder ID (e.g. "L1:0")
    birth_tick: int = 0                        # Tick when born
    reproduce_cooldown: int = 0                # Cooldown ticks before next reproduction
    features: tuple[str, ...] = ()             # Individual biological features
    kit: object | None = None                  # Compiled Kit cache
```

### 4.2 Deterministic ID Allocation & Sorting Integrity
- **The Integer Index Invariant**:
  `genesis/creature.py:86` defines:
  ```python
  def creature_sort_key(c: Creature) -> tuple[str, int]:
      species, _, idx = c.id.rpartition(":")
      return (species, int(idx))
  ```
  If child IDs were formatted with alphanumeric tokens like `"L1:0_child_1"`, `int(idx)` would throw `ValueError: invalid literal for int() with base 10: '0_child_1'`.
- **Solution**:
  Maintain a monotonic integer index per species in `SimState.next_species_index: dict[str, int]`.
  Founder creatures occupy indices `0 .. count-1`.
  The first child born to species `L1` receives ID `"L1:2"` (if 2 founders existed), the next `"L1:3"`, etc.
  This preserves 100% determinism, mathematical monotonicity, and clean compatibility with `creature_sort_key`.

### 4.3 Trait Variance Quantification
Trait variance measures genetic divergence from founder archetype:
$$\Delta \vec{T}(c) = \vec{T}(c) - \vec{T}_{\text{founder}}(c.\text{species})$$
$$\forall c, \quad \sum_{i=1}^{6} \Delta T_i(c) \equiv 0$$
- This delta vector `[d_brain, d_attack, d_armor, d_speed, d_sense, d_stomach]` provides an immediate signature of whether a lineage is drifting towards predation (+attack, +speed), survivability (+armor, +stomach), or intelligence (+brain).

---

## 5. Extinction & Overpopulation Caps

### 5.1 Carrying Capacity Constraints (Grid Ecology Balance)

The simulation grid is 24x24 ($576$ tiles). Baseline food economics:
- `PLANT_MAX = 15` (spawns 2 plants/tick on `PLAIN`).
- `ALGAE_MAX = 36` (spawns 2 algae/tick on `WATER`/`DEEP`).
- Total food respawn = $4$ items/tick = $\sim 120$ energy/tick.
- Upkeep per creature $\approx 3.3$ energy/tick.
- Maximum sustainable steady-state population: $\approx 120 / 3.3 \approx 36$ creatures.

If unconstrained, exponential growth $N(t) = N_0 \cdot 2^{t/\tau}$ would trigger:
1. Complete food grid starvation within 15 ticks.
2. $O(N^2)$ CPU bottlenecks in collision detection, visibility scanning (`visible()`), and combat resolution.
3. Telemetry packet bloat over WebSockets.

### 5.2 Quantitative Guardrails

```python
# genesis/config.py additions
POPULATION_GLOBAL_MAX = 35      # Hard ceiling for total active creatures
POPULATION_SPECIES_MAX = 7      # Hard ceiling per species
CROWDING_RADIUS = 2             # Chebyshev radius for crowding check
CROWDING_MAX_NEIGHBORS = 4      # Suppress reproduction if local density >= 4
EXTINCTION_RECOVERY_DELAY = 50  # Ticks before extinct founder rescue spore
EXTINCTION_RESCUE_ENABLED = False # True only in benchmark stability mode
```

1. **Global Population Ceiling**: If `sum(1 for c in creatures if c.alive) >= POPULATION_GLOBAL_MAX`, all reproduction is inhibited globally.
2. **Species Population Ceiling**: If `sum(1 for c in creatures if c.alive and c.species == parent.species) >= POPULATION_SPECIES_MAX`, reproduction for that species is inhibited.
3. **Local Density Crowding**: If count of alive creatures within Chebyshev distance 2 of parent $\ge \text{CROWDING\_MAX\_NEIGHBORS}$, reproduction fails due to spatial competition.
4. **Extinction Mechanics**:
   - If an entire species has 0 alive creatures and 0 respawning slots, species is flagged `is_extinct = True`.
   - Emits an `"EXTINCTION"` telemetry event and records tick.
   - If `EXTINCTION_RESCUE_ENABLED` is enabled, a single dormant founder spore respawns after 50 ticks to prevent trophic collapse.

---

## 6. Telemetry Schema Extensions in `net/match.py`

### 6.1 Telemetry Compatibility Analysis
In `net/match.py`, `MatchRunner.frame(tick_no, events)` formats the WebSocket spectator payload.

#### Current Schema:
```json
{
  "t": 42,
  "phase": "RUNNING",
  "w": 24, "h": 24,
  "creatures": [
    {
      "id": "L1:0", "x": 5, "y": 12,
      "hp": 48.0, "e": 82.5, "e_max": 93.0,
      "alive": true, "feral": false,
      "tr": [4, 3, 1, 2, 1, 1],
      "species": "L1", "domain": "CAN",
      "features": ["LONG_DAI", "VAY_CUNG", "RANG_NANH"]
    }
  ],
  "plants": [[2, 3], [7, 8]],
  "corpses": [],
  "terrain_delta": [],
  "map": "DONG_CO",
  "terrain": null,
  "events": []
}
```

#### Extended Schema (R1 & R4 Compliant):
```json
{
  "t": 42,
  "phase": "RUNNING",
  "w": 24, "h": 24,
  "creatures": [
    {
      "id": "L1:2", "x": 6, "y": 12,
      "hp": 50.0, "e": 30.0, "e_max": 93.0,
      "alive": true, "feral": false,
      "tr": [4, 2, 2, 2, 1, 1],
      "species": "L1", "domain": "CAN",
      "features": ["LONG_DAI", "VAY_CUNG", "TREO_GIOI"],
      "gen": 1,
      "parent_id": "L1:0",
      "lineage": "L1:0",
      "d_tr": [0, -1, 1, 0, 0, 0],
      "age": 12
    }
  ],
  "plants": [[2, 3], [7, 8]],
  "corpses": [],
  "terrain_delta": [],
  "map": "DONG_CO",
  "terrain": null,
  "events": [
    {
      "k": "REPRODUCE",
      "who": "L1:0",
      "child": "L1:2",
      "gen": 1,
      "pos": [6, 12]
    }
  ]
}
```

### 6.2 Backward Compatibility Validation
- Existing keys (`id`, `x`, `y`, `hp`, `e`, `e_max`, `alive`, `feral`, `tr`, `species`, `domain`, `features`) are strictly preserved in their original types and structures.
- All new creature metadata (`gen`, `parent_id`, `lineage`, `d_tr`, `age`) are additive fields.
- `web/watch3d.js` continues to parse `c.features` and `c.tr` without any parse exceptions, and can immediately display generation badges on 3D health bars.
- Existing tests in `tests/test_spectate.py` (`test_3_spectate_frame_schema`) check:
  `for ck in ("id", "x", "y", "hp", "e", "alive", "feral"): assert ck in cr`
  All asserted keys remain fully satisfied.

---

## 7. Integration with Existing Systems

### 7.1 Lifecycle Integration in `genesis/tick.py`
Reproduction should be resolved deterministically in Phase 3.5 (between Upkeep and Law Hooks) or Phase 5 (Mortality & Reproduction):
```python
# Proposed execution in tick.py:
reproduction_events = resolve_reproduction(world, creatures, tick_no, state, log)
```
Order of operations within tick:
1. `_collect_intents` (Phases 1-2)
2. `resolve_combat`, `resolve_eating`
3. `upkeep_and_check_death` (Phase 3)
4. `resolve_reproduction`: Evaluate eligibility -> mutate -> allocate child -> place in neighbor tile -> log `"REPRODUCE"`.
5. `collect_law_effects` (Phase 4): Newborns participate in law hooks starting next tick or immediately.
6. `kill` / `rebirth` / `try_respawn` (Phase 5).

### 7.2 Strategy & Minds Integration (`genesis/minds.py`)
When a child is born:
1. `Minds.notes_of(child)` automatically instantiates fresh `FieldNotes` with capacity appropriate for `child.traits.brain`.
2. `Minds.codex_of(child)` inherits a duplicate of the parent's Codex with confidence decayed by 1 (`forget_on_death` logic from `lineage.py`), representing cultural transmission across generations.
3. For remote clients in `net/match.py`: child ID is appended to `Registration.creature_ids` for that species, allowing client controllers to manage their generational progeny.

---

## 8. Risk Analysis & Edge Cases

| # | Risk / Edge Case | Consequence | Mitigation Strategy |
|---|------------------|-------------|---------------------|
| 1 | **ID Parsing Crash** | `creature_sort_key` crashes on non-integer suffix with `ValueError`. | Strictly enforce monotonic integer IDs (`f"{species}:{idx}"`). Add try/except fallback in `creature_sort_key`. |
| 2 | **Impassable Newborn Placement** | Offspring spawns in deep water or stone, dying immediately or breaking movement invariants. | Placement algorithm runs `world.passable(pos, child)` before confirming birth. If no cell is passable, reproduction delays. |
| 3 | **Starvation Collapse** | Rapid reproduction drains food faster than respawn rate ($4$/tick), killing all creatures. | Strict `POPULATION_GLOBAL_MAX = 35` and metabolic reproduction tax (`35.0` energy deducted from parent). |
| 4 | **Trait Vector Invariant Violation** | Non-zero-sum mutation violates $\sum=12$ or $[0, 5]$ bounds, triggering assertion in `Traits.__post_init__`. | Trait mutation uses `Traits.shift(frm, to)` which mathematically guarantees sum and range conservation. |
| 5 | **Memory Leak in Multi-Gen Runs** | Thousands of dead creature records accumulate in memory across epochs. | Only track active and recent creatures; prune dead lineage records older than 100 ticks in `SimState`. |
| 6 | **Feature Mutation Conflict** | Land creature mutates into water feature without amphibious trait, getting stranded. | `can_enter` respects creature's own `kit`. Feature mutation validates that offspring can traverse its current spawn location. |

---

## 9. Verification & Test Plan

A dedicated test suite `tests/test_evolution.py` and extensions to `tests/e2e/test_e2e_tier1_features.py` must be implemented to verify R1:

1. **Reproduction Eligibility Unit Tests**:
   - `test_reproduction_requires_energy_threshold()`: Verify creature with $<80\%$ energy cannot reproduce.
   - `test_reproduction_requires_maturity_age()`: Verify creature with age $<30$ cannot reproduce.
   - `test_reproduction_cooldown_enforced()`: Verify parent cannot reproduce twice within cooldown window.
   - `test_reproduction_deducts_parent_energy()`: Verify parent energy decreases by reproduction cost.
2. **Genetic Mutation Tests**:
   - `test_trait_sum_invariant_after_mutation()`: Verify $\sum \text{traits} == 12$ across 1,000 successive birth mutations.
   - `test_trait_bounds_invariant_after_mutation()`: Verify all traits remain in $[0, 5]$.
   - `test_feature_mutation_preserves_valid_kit()`: Verify mutated features produce valid compiled `Kit` with proper passability flags.
3. **Lineage Tracking Tests**:
   - `test_lineage_metadata_integrity()`: Verify `parent_id`, `generation == parent.generation + 1`, and `lineage_id` are recorded.
   - `test_trait_variance_vector_sums_to_zero()`: Verify $\sum \Delta T_i \equiv 0$ against founder vector.
4. **Stability & Cap Tests**:
   - `test_population_global_cap_enforced()`: Verify population never exceeds `POPULATION_GLOBAL_MAX` in a 400-tick stress run.
   - `test_species_cap_enforced()`: Verify single dominant species does not exceed `POPULATION_SPECIES_MAX`.
   - `test_extinction_event_logged()`: Verify extinction logging when a species reaches 0 population.
5. **Telemetry Contract Tests**:
   - `test_telemetry_frame_includes_lineage_metadata()`: Verify WebSocket payload contains `gen`, `parent_id`, and `d_tr`.
   - `test_spectator_backward_compatibility()`: Verify all legacy keys pass schema verification.

---

## 10. Conclusion & Recommendation

The proposed Generational Evolution architecture transforms Genesis Zero from a static slot simulation into an emergent evolutionary sandbox. By building directly on the existing `Traits.shift`, `features.kit_of`, and `domain.can_enter` primitives, R1 can be implemented with zero regressions to existing tests, referee scoring, or the 3D visualizer, while fulfilling all acceptance criteria.

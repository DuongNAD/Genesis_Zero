# Handoff Report: Generational Evolution & Genetic Mutation Architecture (R1)

**Agent**: Explorer 1 (Evolution & Mutation Specialist)  
**Recipient**: Parent Orchestrator (`parent`, id: `acd85475-3c3a-47fd-b10c-111536f0a2fe`)  
**Date**: 2026-09-03  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1`  
**Handoff Type**: Hard (Investigation & Technical Survey Complete)  

---

## 1. Observation

Direct observations from source code inspection and test suite execution:

1. **Creature Identity & Lifecycle Model** (`genesis/creature.py`):
   - Lines 33–36:
     ```python
     # Đời thứ mấy của DÒNG DÕI này. `id` định danh dòng dõi, không phải cá thể:
     # giữ nguyên id qua các đời để khe prefix cache, khoá Sổ Luật, sổ ghi công và
     # đường replay không phải dựng lại mỗi lần có con chết (64 lần một ván).
     generation: int = 0
     ```
   - Lines 86–95:
     ```python
     def creature_sort_key(c: Creature) -> tuple[str, int]:
         species, _, idx = c.id.rpartition(":")
         return (species, int(idx))
     ```
     `idx` is directly parsed via `int(idx)`. Any offspring ID format containing non-numeric suffixes (e.g. `"L1:child_1"`) will crash with `ValueError`.
   - `Creature` dataclass currently lacks `parent_id`, `lineage_id`, `birth_tick`, `reproduce_cooldown`, and instance-level `features` / `kit`.

2. **Trait Invariants & Mutation Primitive** (`genesis/traits.py`):
   - Lines 19–26:
     ```python
     values = astuple(self)
     assert sum(values) == config.TRAIT_SUM, (
         f"Tổng trait phải bằng {config.TRAIT_SUM}, nhận {sum(values)}"
     )
     assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in values), (
         f"Trait phải nằm trong [{config.TRAIT_MIN}, {config.TRAIT_MAX}], nhận {values}"
     )
     ```
   - Lines 68–88: `Traits.shift(frm, to)` shifts 1 point from `frm` to `to`, preserving `sum == 12` and `min <= v <= max`.

3. **Feature Distribution & Domain Coupling** (`genesis/features.py`, `genesis/world.py`, `genesis/domain.py`):
   - `genesis/features.py:173-181`: `roll_for_species(species_id, seed)` rolls 3 biological features per species, stored at `world.kits[species_id]`.
   - `genesis/world.py:273-296`: `world.passable(pos, creature=None)` evaluates passability using `self.kits.get(creature.species)`.
   - `genesis/domain.py:77-128`: `can_enter(domain, terrain, traits, kit)` gate order: (1) domain, (2) kit features (`extra_terrain`, `extra_domains`), (3) traits (`speed` for climbing, `armor` for fire).

4. **Carrying Capacity & Food Energy Economics** (`genesis/config.py`, `genesis/world.py`):
   - `config.PLANT_MAX = 15`, `config.PLANT_RESPAWN = 2`, `config.PLANT_ENERGY = 30`.
   - `config.ALGAE_MAX = 36`, `config.ALGAE_RESPAWN = 2`, `config.ALGAE_ENERGY = 32`.
   - Average upkeep per creature is $\approx 3.3$ energy/tick. Total food generation is 4 items/tick ($\approx 120$ energy/tick). Maximum sustainable population is $\approx 36$ creatures.

5. **Spectator Telemetry Payload** (`net/match.py`):
   - Lines 569–581 in `frame(tick_no, events)`:
     ```python
     "creatures": [
         {
             "id": c.id, "x": c.pos[0], "y": c.pos[1],
             "hp": round(c.hp, 1), "e": round(c.energy, 1),
             "e_max": round(c.traits.energy_max, 1),
             "alive": c.alive, "feral": c.species in feral_species,
             "tr": list(astuple(c.traits)),
             "species": c.species,
             "domain": config.SPECIES_DOMAIN.get(c.species, "CAN"),
             "features": list(self.world.kits[c.species].keys) if (self.world and c.species in self.world.kits) else [],
         }
         for c in sorted(self.creatures, key=creature_sort_key)
     ],
     ```
   - Currently lacks `gen`, `parent_id`, `lineage`, and trait variance vector `d_tr`.
   - `web/watch3d.js:504` reads `const feats = c.features || [];` to construct 3D morphology meshes.

6. **Current Test Status**:
   - Running `pytest tests/test_lineage.py -v` executed 27 tests with 100% pass in 0.33s.
   - All tests assert strict invariance of trait sums and non-negative parameters.

---

## 2. Logic Chain

1. **From Observation 1**: Because `creature_sort_key` parses `int(idx)` from `c.id.rpartition(":")`, newborn offspring IDs must be assigned sequential integer indices (e.g. `"L1:2"`, `"L1:3"`) rather than string tags. This guarantees that all sorting, referee scoring, and telemetry serialization remain deterministic and crash-free.
2. **From Observation 2**: Because `Traits` asserts `sum == TRAIT_SUM (12)` and `TRAIT_MIN (0) <= v <= TRAIT_MAX (5)`, all offspring trait mutations must use zero-sum transfer operations (`Traits.shift(frm, to)`). This mathematically prevents score-inflation exploits and guarantees that child trait vectors remain valid instances of `Traits`.
3. **From Observation 3**: Because `world.passable` routes through `self.kits.get(creature.species)`, introducing feature mutations per individual requires `world.passable` and combat to check `getattr(creature, "kit", None) or self.kits.get(creature.species)`. This allows offspring that mutate new features (e.g., `LUONG_CU` for amphibious mobility or `TREO_GIOI` for climbing) to immediately gain corresponding traversal abilities, while preserving complete backward compatibility for founder species.
4. **From Observation 4**: Because food replenishes at a fixed rate of 4 units/tick ($\sim 120$ energy/tick) supporting a theoretical maximum of $\sim 36$ creatures, an unconstrained exponential reproduction loop would crash the ecosystem within 15 ticks. Therefore, introducing `POPULATION_GLOBAL_MAX = 35` and `POPULATION_SPECIES_MAX = 7`, combined with an energy reproduction cost of $35.0$ and a $25$-tick cooldown, is mathematically necessary to guarantee simulation stability.
5. **From Observation 5**: Because `net/match.py` serializes a dictionary of creature attributes and existing tests verify specific keys (`id`, `x`, `y`, `hp`, `e`, `alive`, `feral`), adding `gen`, `parent_id`, `lineage`, and `d_tr` is strictly additive. This guarantees that `web/watch3d.js` and all existing E2E spectate test cases will run without modification.

---

## 3. Caveats

- **Networked Player Lineage Control**: In multi-client network matches (`net/routes_join.py` and `net/routes_work.py`), when a remote client's organism reproduces, the newborn's ID must be appended to `Registration.creature_ids` if the client is active, or handled by the reflex controller if feral.
- **Epistemic Acceleration Tuning**: Relaxing reproduction thresholds upon law discovery creates an evolutionary advantage for high-brain models; however, threshold relaxation must be capped to prevent sudden population spikes when a law is broadcast during REVEAL.
- **Mesh Generation Overhead**: If feature mutation produces a novel combination of 3 features, `web/watch3d.js` procedurally composites the 3D meshes using local Three.js geometries; external Meshy API calls should remain disabled in local offline mode to adhere to zero-CDN requirements.

---

## 4. Conclusion

1. **Feasibility**: Implementation of R1 is fully feasible and directly compatible with Genesis Zero's existing core architecture.
2. **Core Deliverables for Implementation**:
   - **`genesis/creature.py`**: Extend `Creature` dataclass with `parent_id: str | None = None`, `generation: int = 0`, `lineage_id: str = ""`, `birth_tick: int = 0`, `reproduce_cooldown: int = 0`, and `features: tuple[str, ...] = ()`. Add sequential integer ID allocator.
   - **`genesis/evolution.py` (new)**: Implement `reproduce_offspring(parent, tick, rng, world)` containing bounded stochastic trait mutation (`Traits.shift`), feature mutation (`FEATURES` swap), and passability verification.
   - **`genesis/tick.py`**: Insert `resolve_reproduction` in Phase 3.5/5, enforcing global cap ($35$), species cap ($7$), energy threshold ($80\%$), age maturity ($30$), and metabolic energy deduction ($35.0$).
   - **`genesis/domain.py` & `genesis/world.py`**: Update `passable` to inspect `creature.kit or world.kits[creature.species]`.
   - **`net/match.py`**: Extend telemetry frame with `gen`, `parent_id`, `lineage`, `d_tr`, and support `"REPRODUCE"` / `"EXTINCTION"` public events.
   - **`tests/test_evolution.py` (new)**: Unit tests covering reproduction gates, trait bounds, feature mutations, lineage metadata, and population caps.

---

## 5. Verification Method

To independently verify this investigation and future implementation:

1. **Inspect Survey Report**:
   - Review `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1/analysis.md` for mathematical formulations, schema designs, and risk matrices.
2. **Execute Current Lineage & Feature Test Baselines**:
   ```bash
   pytest tests/test_lineage.py tests/test_features.py tests/test_creature.py -v
   ```
   *Expected result*: 100% tests pass (zero collection errors, zero failures).
3. **Execute Spectate & Telemetry Schema Tests**:
   ```bash
   pytest tests/test_spectate.py -v
   ```
   *Expected result*: All WebSocket and schema assertions pass.
4. **Invalidation Conditions**:
   - Any child ID format where `c.id.rpartition(":")[2]` cannot be converted to `int`.
   - Any trait mutation where $\sum \text{traits} \ne 12$ or any trait $< 0$ or $> 5$.
   - Any simulation run where active living population exceeds `POPULATION_GLOBAL_MAX`.

# Task Assignment: Milestone M1_EVO — Generational Evolution & Genetic Mutation

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Context & Authoritative Documents
- User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- Survey Analysis & Architecture: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1/analysis.md`
- Survey Handoff Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1/handoff.md`

## Objectives
Implement the complete Generational Evolution & Genetic Mutation subsystem for Genesis Zero according to the specifications in `PROJECT.md § Interface Contracts (1)` and Explorer 1's handoff:

1. **`genesis/creature.py`**:
   - Extend `Creature` dataclass with:
     - `parent_id: str | None = None`
     - `generation: int = 0`
     - `lineage_id: str = ""`
     - `birth_tick: int = 0`
     - `reproduce_cooldown: int = 0`
     - `features: tuple[str, ...] = ()`
     - Property or method `kit` that returns a `SpeciesKit` based on `self.features` if set.
   - Sequential integer ID allocator for offspring: format `f"{species}:{idx}"` where `idx` is an integer, guaranteeing `creature_sort_key`'s `int(idx)` parsing invariant holds without error.

2. **`genesis/evolution.py` (new module)**:
   - Implement `reproduce_offspring(parent: Creature, tick: int, rng: random.Random, world: World) -> Creature | None`:
     - Gated by spatial clearance: finds an adjacent passable cell for the child (`world.passable(neighbor_pos, child)`).
     - Trait inheritance with bounded stochastic mutation: child inherits parent traits with mutation probability (e.g. 0.40), applying zero-sum point transfers via `Traits.shift(frm, to)` preserving $\sum \text{traits} \equiv 12$ and $0 \le \text{trait} \le 5$.
     - Biological feature inheritance & mutation: child inherits parent's 3 features, with mutation probability (e.g. 0.15) swapping 1 feature for another valid feature from `genesis.features.FEATURES`.
     - Allocates starting child energy (e.g. 30.0), records `parent_id = parent.id`, `generation = parent.generation + 1`, `lineage_id = parent.lineage_id or parent.id`, `birth_tick = tick`.
     - Calculates trait variance vector $\Delta \vec{T} = \text{child.traits} - \text{founder\_traits}$.

3. **`genesis/tick.py`**:
   - Integrate reproduction phase (e.g. Phase 3.5 or Phase 5):
     - Gated by:
       - Energy threshold: `c.energy >= 0.80 * c.traits.energy_max`
       - Maturity age: `c.age >= 30`
       - Survival streak: `c.ticks_alive_streak >= 20`
       - Cooldown: `c.reproduce_cooldown <= 0`
       - Codex law discovery bonus: creatures with verified law discoveries get 50% cooldown reduction.
     - Carrying capacity caps:
       - Global population cap: `POPULATION_GLOBAL_MAX = 35` (total alive creatures < 35)
       - Species population cap: `POPULATION_SPECIES_MAX = 7` (alive creatures of this species < 7)
       - Local crowding: skip if $\ge 4$ creatures in Chebyshev radius 2.
     - On successful birth:
       - Deduct 35.0 energy from parent, set `c.reproduce_cooldown = 25`.
       - Add child to `world.creatures` (or match creatures list).
       - Record `REPRODUCE` event with parent ID and child ID.
     - Extinction detection: if all creatures of a species are dead, record `EXTINCTION` event.

4. **`genesis/domain.py` & `genesis/world.py`**:
   - Ensure `world.passable(pos, creature)` and combat checks inspect `getattr(creature, "kit", None) or world.kits.get(creature.species)`. This allows creatures with mutated features (such as `LUONG_CU` or `TREO_GIOI`) to immediately use their individual traversal abilities.

5. **`tests/test_evolution.py` (new test suite)**:
   - Comprehensive unit tests:
     - Test reproduction gate conditions (energy, age, streak, cooldown).
     - Test trait mutation invariants: sum == 12, min/max bounds across 1000 mutation iterations.
     - Test feature mutation: valid feature pool, kit generation, passability effect.
     - Test lineage tracking metadata and integer ID sorting compatibility.
     - Test carrying capacity caps: simulation never exceeds global or species caps.

6. **Verification**:
   - Run `pytest tests/test_evolution.py -v`.
   - Run the full test suite `pytest` to ensure 0 regressions.
   - Document all commands, file diffs, and test outputs in your `handoff.md`.

## 2026-09-03T05:06:09Z
You are Worker M1_EVO (Evolution & Mutation Specialist) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_evo_1/handoff.md

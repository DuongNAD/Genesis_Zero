# Implementation Task: Milestone M1_EVO Remediation (Worker Gen 3)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Remediation Explorer 1 Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_1/handoff.md`
- Remediation Explorer 2 Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_2/handoff.md`
- Remediation Explorer 3 Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_3/handoff.md`
- Adversarial Test Suite: `tests/test_evolution_adversarial.py`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Apply the verified carrying capacity and offspring mortality remediation synthesized by Explorers 1, 2, and 3:

1. In `genesis/creature.py`:
   - Update `kill(c, world, tick, cause="starve")`:
     ```python
     c.alive = False
     if c.parent_id is not None:
         c.dead_until = -1
     else:
         c.dead_until = tick + config.RESPAWN_DELAY
     world.corpses[c.pos] = tick
     ```
   - Update `try_respawn(c, world, tick, rng, creatures=None)`:
     ```python
     if c.alive or c.dead_until < 0 or tick < c.dead_until or c.parent_id is not None:
         return False
     pool = creatures if creatures is not None else getattr(world, "creatures", None)
     if pool is not None:
         alive_all = [x for x in pool if x.alive]
         if len(alive_all) >= config.POPULATION_GLOBAL_MAX:
             return False
         alive_sp = [x for x in alive_all if x.species == c.species]
         if len(alive_sp) >= config.POPULATION_SPECIES_MAX:
             return False
     ```

2. In `genesis/tick.py`:
   - Update Phase 5 (Respawn Phase):
     ```python
     respawn_events: list[dict] = []
     alive_count = sum(1 for x in creatures if x.alive)
     sp_counts = {sp: sum(1 for x in creatures if x.alive and x.species == sp) for sp in {x.species for x in creatures}}
     for c in sorted(creatures, key=creature_sort_key):
         if not c.alive and c.dead_until >= 0 and tick_no >= c.dead_until and c.parent_id is None:
             if alive_count >= config.POPULATION_GLOBAL_MAX:
                 continue
             if sp_counts.get(c.species, 0) >= config.POPULATION_SPECIES_MAX:
                 continue
             crng = creature_rng(state.match_seed, tick_no, c.id)
             if try_respawn(c, world, tick_no, crng, creatures=creatures):
                 alive_count += 1
                 sp_counts[c.species] = sp_counts.get(c.species, 0) + 1
                 respawn_events.append({
                     "creature_id": c.id,
                     "species_id": c.species,
                     "pos": list(c.pos),
                 })

     from genesis.evolution import detect_extinctions

     if not hasattr(state, "extinct_species"):
         state.extinct_species = set()
     extinction_events = detect_extinctions(creatures, tick_no, state.extinct_species)

     # Clean up dead non-reincarnating offspring while preserving founders
     creatures[:] = [c for c in creatures if c.parent_id is None or c.alive or c.dead_until >= 0]
     ```

3. Verification:
   - Run `pytest tests/test_evolution_adversarial.py -v` (all 4 tests MUST PASS).
   - Run `pytest tests/test_evolution.py tests/test_adversarial_m1_evo_2.py -v` (all 31 tests MUST PASS).
   - Run `pytest tests/test_lifecycle.py tests/test_trait_shift.py tests/test_score.py tests/test_maps.py -v` (MUST PASS).
   - Run `pytest` across the entire repository to confirm 100% pass rate.
   - Run `ruff check` on affected files to ensure zero lint errors.

Write your handoff report to `handoff.md` in your working directory and notify parent via `send_message`.

## 2026-09-03T07:07:38Z
You are Worker M1_EVO Gen 3 for Milestone M1_EVO Remediation.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen3
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen3/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_3/analysis.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m1_remediate_3/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply the verified carrying capacity and offspring mortality remediation to `genesis/creature.py` and `genesis/tick.py`.
Run pytest on `tests/test_evolution_adversarial.py` and across the repository.
Write your handoff report to `handoff.md` in your working directory and notify parent via send_message when done.


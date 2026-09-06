# BRIEFING — 2026-09-03T05:06:09Z

## Mission
Implement Generational Evolution & Genetic Mutation (Milestone M1_EVO) for Genesis Zero with zero regressions.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo
- Original parent: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Milestone: M1_EVO

## 🔒 Key Constraints
- DO NOT CHEAT: no hardcoding test results, dummy implementations, or circumventing tasks. Real state, real behavior.
- Sequential integer ID allocator (species:idx) to preserve creature_sort_key int(idx) invariant.
- Bounded stochastic trait mutation (sum=12, [0,5]) via Traits.shift.
- Feature mutation (1-of-3 swap from FEATURES pool, individual kit in domain passability).
- Population caps (POPULATION_GLOBAL_MAX=35, POPULATION_SPECIES_MAX=7) and crowding suppression.
- Zero regressions across existing test suite.
- Write only to your folder (.agents/worker_m1_evo/).

## Current Parent
- Conversation ID: acd85475-3c3a-47fd-b10c-111536f0a2fe
- Updated: 2026-09-03T05:06:09Z

## Task Summary
- **What to build**: Generational evolution & genetic mutation subsystem (genesis/creature.py, genesis/evolution.py, genesis/tick.py, genesis/domain.py, genesis/world.py, tests/test_evolution.py)
- **Success criteria**: All reproduction gates, trait invariants, feature mutations, lineage tracking, carrying capacity caps functioning genuinely and passing 100% of tests.
- **Interface contracts**: PROJECT.md § Interface Contracts (1)
- **Code layout**: PROJECT.md § Code Layout

## Key Decisions Made
- Offspring ID format strictly integer-indexed per species (e.g. L1:2) ensuring int(idx) parse safety.
- Trait mutation uses Traits.shift(frm, to) ensuring sum=12 and range [0, 5] invariants hold.
- Individual creature kit takes precedence over world.kits[creature.species] in domain and world passability checks.

## Artifact Index
- DISPATCH.md — Assignment from orchestrator
- BRIEFING.md — Persistent working memory
- progress.md — Liveness heartbeat and progress tracking

## Change Tracker
- **Files modified**: None yet
- **Build status**: Baseline pytest: 890 passed, 1 skipped (0 failures)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 890 passed, 1 skipped
- **Lint status**: Clean
- **Tests added/modified**: tests/test_evolution.py (pending)

## Loaded Skills
- None

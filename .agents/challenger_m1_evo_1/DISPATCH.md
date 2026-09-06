# Adversarial Challenge Task: Milestone M1_EVO — Challenger 1

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md`

## Objectives
Perform empirical adversarial testing on Milestone M1_EVO (Generational Evolution & Genetic Mutation):
1. Write an adversarial stress test harness (in a temporary test file or execute via pytest/python) to test:
   - Trait mutation stress: Run 10,000 successive mutation generations to verify zero sum drift ($\sum \equiv 12$) and zero out-of-bound values ($< 0$ or $> 5$).
   - Population cap fuzzing: Force high-energy reproduction conditions across 500 ticks and verify active population never exceeds `POPULATION_GLOBAL_MAX` (35) or `POPULATION_SPECIES_MAX` (7).
   - ID sorting invariant: Verify sorting millions of creature IDs never causes ValueError in `creature_sort_key`.
2. Deliver empirical results and your verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.

## 2026-09-03T06:37:12Z
You are Challenger 1 for Milestone M1_EVO (Generational Evolution & Mutation).
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md

Perform adversarial stress testing on trait mutations (10,000 generations), carrying capacity caps, and creature ID sorting safety. Deliver empirical results and your verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

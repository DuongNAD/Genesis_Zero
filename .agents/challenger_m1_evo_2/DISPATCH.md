# Adversarial Challenge Task: Milestone M1_EVO — Challenger 2

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md`

## Objectives
Perform empirical adversarial testing on Milestone M1_EVO:
1. Feature mutation and traversal verification:
   - Test creatures that mutate traversal features (e.g., `LUONG_CU`, `TREO_GIOI`) to verify they can traverse corresponding terrains (`WATER`, `DEEP`, `TREE`) that founders could not.
   - Verify that invalid feature sets or empty kits are rejected or handled gracefully.
2. Crowding and Extinction stress test:
   - Stress test crowding suppression (verify organisms do not reproduce when radius-2 Chebyshev neighbors $\ge 4$).
   - Test complete species extinction triggers and verify simulation integrity does not crash when 1 or all species go extinct.
3. Deliver empirical results and your verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.

## 2026-09-03T06:37:12Z
You are Challenger 2 for Milestone M1_EVO (Generational Evolution & Mutation).
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m1_evo_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m1_evo_gen2/handoff.md

Perform adversarial stress testing on feature mutation & individual passability, crowding radius limits, and extinction handling. Deliver empirical results and your verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent.

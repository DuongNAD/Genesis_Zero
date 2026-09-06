# Dispatch Assignment: Challenger 2 (Milestone M5_VERIFY_E2E)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (section `## 2026-09-03T04:57:00Z` - R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M5 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1/handoff.md`

## Challenger Objectives
1. **Adversarial End-to-End Simulation Stress Testing**:
   - Execute a long-horizon 500-tick continuous multi-generational simulation combining all new mechanics:
     - Generational reproduction and trait mutation (M1_EVO).
     - Macro-environmental weather cycle transitions (M2_WEATHER).
     - Telemetry frame serialization with weather, lineage, and reproduction/extinction events (M3_TELEMETRY).
   - Invariant Verification:
     - Global population strictly `<= POPULATION_GLOBAL_MAX (35)` at every tick.
     - Species population strictly `<= POPULATION_SPECIES_MAX (7)` at every tick.
     - Zero NaN, inf, or unhandled exceptions across 500 ticks.
     - Memory footprint remains flat (no unbounded object accumulation).
2. **Implementation**:
   - Write and execute an adversarial test module `tests/test_challenger_m5_e2e_stress.py`.
   - If adding test file changes total test count, ensure `README.md` lines 131 and 185 stay synchronized with `test_readme_khop_thuc_te.py`.
3. **Execution**:
   - Run `pytest tests/test_challenger_m5_e2e_stress.py -v`.
   - Run `pytest tests/test_readme_khop_thuc_te.py -v`.
4. **Verdict**:
   - Deliver empirical results and verdict (**`APPROVE`** or **`REQUEST_CHANGES`**) in `handoff.md` and notify parent via `send_message`.

## 2026-09-03T09:08:12Z
You are Challenger 2 for Milestone M5_VERIFY_E2E.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m5_verify_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m5_verify_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1/handoff.md

Adversarially stress test multi-generational simulation over 500 continuous ticks under rapid weather cycles. Verify carrying capacity caps (POPULATION_GLOBAL_MAX=35, POPULATION_SPECIES_MAX=7), memory stability, and zero NaN/crashes. Write adversarial test suite in `tests/test_challenger_m5_e2e_stress.py`. Execute tests. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent via send_message.

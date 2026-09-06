# Dispatch Assignment: Challenger 1 (Milestone M5_VERIFY_E2E)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (section `## 2026-09-03T04:57:00Z` - R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M5 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1/handoff.md`

## Challenger Objectives
1. **Adversarial CLI & Launcher Stress Testing**:
   - Test edge cases and failure modes on `scripts/launch.py` and `scripts/preflight.py`:
     - Invalid arguments and unrecognized flags (verify clean error exit, no stacktrace crash).
     - Boundary tick counts (`--ticks 0`, `--ticks 1`, `--ticks -5`).
     - Negative and overflow seeds (`--seed -1`, `--seed 999999999`).
     - Conflicting mode combinations (`--no-render` + `--web`, etc.).
     - Non-interactive / headless environment behavior.
2. **Implementation**:
   - Write and execute an adversarial test module `tests/test_challenger_m5_launchers.py`.
   - If adding test file changes total test count, ensure `README.md` lines 131 and 185 stay synchronized with `test_readme_khop_thuc_te.py`.
3. **Execution**:
   - Run `pytest tests/test_challenger_m5_launchers.py -v`.
   - Run `pytest tests/test_readme_khop_thuc_te.py -v`.
4. **Verdict**:
   - Deliver empirical results and verdict (**`APPROVE`** or **`REQUEST_CHANGES`**) in `handoff.md` and notify parent via `send_message`.

## 2026-09-03T09:08:12Z
You are Challenger 1 for Milestone M5_VERIFY_E2E.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m5_verify_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m5_verify_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1/handoff.md

Adversarially stress test CLI arguments and launcher edge cases in `scripts/launch.py` and `scripts/preflight.py`. Write adversarial test suite in `tests/test_challenger_m5_launchers.py`. Execute tests. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent via send_message.

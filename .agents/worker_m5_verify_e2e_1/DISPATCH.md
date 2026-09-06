# Dispatch Assignment: Worker M5_VERIFY_E2E (Final Acceptance & Launcher Verification)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically section `## 2026-09-03T04:57:00Z` - R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Visualizer & Server files: `web/watch3d.html`, `web/watch3d.js`, `net/server.py`, `scripts/launch.py`, `run.sh`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Worker Objectives
1. **E2E Test Suite Verification**:
   - Run the 5-tier E2E test suite:
     - Tier 1: `pytest -o pythonpath=. tests/e2e/test_e2e_tier1_features.py -v` (85 tests)
     - Tier 2: `pytest -o pythonpath=. tests/e2e/test_e2e_tier2_boundaries.py -v` (85 tests)
     - Tier 3: `pytest -o pythonpath=. tests/e2e/test_e2e_tier3_combinations.py -v` (20 tests)
     - Tier 4: `pytest -o pythonpath=. tests/e2e/test_e2e_tier4_scenarios.py -v` (6 tests)
     - Tier 5: `pytest -o pythonpath=. tests/e2e/test_e2e_tier5_adversarial.py -v` (12 tests)
     - Total: `pytest -o pythonpath=. tests/e2e -v` (208 tests)
2. **One-Command Launcher Verification**:
   - Verify `run.sh` syntax and execution capability (`bash -n run.sh`).
   - Verify `scripts/launch.py` help and option parsing (`python3 scripts/launch.py --help`).
   - Verify `python3 scripts/preflight.py` diagnostics.
3. **Full Repository Pytest Execution & README Synchronization**:
   - Run `pytest --collect-only -q` to get exact collected count.
   - Ensure `README.md` lines 131 and 185 match the actual collected test count.
   - Run `pytest tests/test_readme_khop_thuc_te.py -v`.
   - Run full repository test suite `pytest -q`. All tests MUST pass with 100% success (0 failures, 0 errors).
4. **Handoff Report**:
   - Deliver comprehensive handoff report to `handoff.md` with:
     - Exact test counts and execution times.
     - Confirmation of all launcher checks.
     - Verification of zero regressions across all 5 milestones.
   - Notify parent via `send_message`.

## 2026-09-03T09:01:14Z
You are Worker M5_VERIFY_E2E (Final Acceptance & Verification Specialist) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m5_verify_e2e_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Execute the objectives:
1. Verify 5-tier E2E test suite in `tests/e2e/` (208 tests): `pytest -o pythonpath=. tests/e2e -v`.
2. Verify 1-command launchers: `bash -n run.sh`, `python3 scripts/launch.py --help`, `python3 scripts/preflight.py`.
3. Check `pytest --collect-only -q` test count, verify `README.md` lines 131 and 185 match, verify `pytest tests/test_readme_khop_thuc_te.py -v`.
4. Run full repository `pytest -q` to confirm 100% pass rate.
5. Write detailed handoff to `handoff.md` and notify parent via `send_message`.

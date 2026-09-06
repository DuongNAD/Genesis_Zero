# Dispatch Assignment: Remediation Worker 1 (Milestone M3_TELEMETRY Remediation)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Remediation Explorer Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m3_remediate_1/handoff.md`
- Patch file: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m3_remediate_1/readme_test_count.patch`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Remediation Objectives
1. Check the exact test count via `python3 -m pytest --collect-only -q`.
2. Update `README.md`:
   - Line 131: Replace `| Test | **945 mục, xanh** |` with `| Test | **<count> mục, xanh** |` (e.g. `1009`).
   - Line 185: Replace `make test         # 945 test` with `make test         # <count> test` (e.g. `1009`).
   - DO NOT modify `tests/test_readme_khop_thuc_te.py` or any test thresholds.
3. Run verification:
   - `pytest tests/test_readme_khop_thuc_te.py -v` (must pass 100%).
   - `pytest tests/test_telemetry_extension.py -v` (must pass 100%).
   - Full repository `pytest -q` (must pass with 0 failures).
   - `git diff README.md` to ensure minimal, exact changes.
4. Document all outputs and results in `handoff.md` and notify parent via `send_message`.

## 2026-09-03T08:25:46Z

You are Remediation Worker 1 for Milestone M3_TELEMETRY.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_remediate_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3_remediate_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m3_remediate_1/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Apply the verified remediation:
1. Update README.md lines 131 and 185 to reflect the collected test count (1009). Do not modify test thresholds in tests/test_readme_khop_thuc_te.py.
2. Run `pytest tests/test_readme_khop_thuc_te.py -v` and full repository `pytest -q`.
3. Deliver handoff report in `handoff.md` and notify parent via `send_message`.

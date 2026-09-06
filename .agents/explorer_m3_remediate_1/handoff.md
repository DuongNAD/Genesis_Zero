# Handoff Report: Milestone M3_TELEMETRY Remediation Analysis

**Agent**: Remediation Explorer 1 (`explorer_m3_remediate_1`)  
**Milestone**: M3_TELEMETRY (Remediation Track)  
**Parent Conversation ID**: `acd85475-3c3a-47fd-b10c-111536f0a2fe`  
**Date**: 2026-09-03  
**Handoff Type**: Hard (Task complete, ready for implementation / integration)  

---

## 1. Observation

1. **Failure in Forensic Audit Check 4 (`.agents/auditor_m3_telemetry_1/handoff.md:21-25`)**:
   Tool command: `pytest -q`
   Verbatim error:
   ```
   =================================== FAILURES ===================================
   ____________________ test_so_test_trong_README_khop_thuc_te ____________________

       def test_so_test_trong_README_khop_thuc_te():
           ...
           that = _so_test_thuc_te()
           for n in ghi:
   >           assert abs(n - that) <= max(5, that * 0.05), (
                   f"README ghi {n} test, thực tế {that}. Sửa README, đừng sửa ngưỡng.")
   E           AssertionError: README ghi 945 test, thực tế 1009. Sửa README, đừng sửa ngưỡng.
   E           assert 64 <= 50.45
   E            +  where 64 = abs((945 - 1009))
   E            +  and   50.45 = max(5, (1009 * 0.05))

   tests/test_readme_khop_thuc_te.py:57: AssertionError
   =========================== short test summary info ============================
   FAILED tests/test_readme_khop_thuc_te.py::test_so_test_trong_README_khop_thuc_te
   1 failed, 1008 passed, 1 skipped in 184.28s
   ```

2. **Collected Test Count via Pytest (`tests/test_readme_khop_thuc_te.py:28-35`)**:
   Tool command: `python3 -m pytest --collect-only -q`
   Calculated count via `_so_test_thuc_te()`: **1009** across 89 test files.
   Categorization breakdown:
   - `tests/e2e/` (5 files): 208 tests
   - Core unit & integration (69 files): 616 tests
   - Adversarial & stress suites (10 files): 109 tests
   - Evolution, weather, & telemetry suites (5 files): 76 tests
   - Total: 1009 tests

3. **Current Documented Counts in `README.md`**:
   - `README.md:131`: `| Test | **945 mục, xanh** |`
   - `README.md:185`: `make test         # 945 test`
   - Matching regex in `tests/test_readme_khop_thuc_te.py:50`: `r"(\d{3,4})\s*mục, xanh|#\s*(\d{3,4})\s*test"`
   - Extraction returns `ghi = [945, 945]`.
   - Tolerance formula: `abs(n - that) <= max(5, that * 0.05)`.
   - Evaluation: `abs(945 - 1009) = 64 > 50.45` -> FAIL.

4. **Single Skipped Test**:
   - `tests/test_r03.py:101`: `pytest.skip("đặt GENESIS_SLOW_TESTS=1 để chạy bài nạp model thật")` is expected when running in default fast mode without external LLM model weights loaded.
   - All other 1008 tests pass.

5. **Telemetry Extension Quality**:
   - `tests/test_telemetry_extension.py` (14 tests), `tests/test_adversarial_m3_telemetry.py` (9 tests), and `tests/test_challenger_m3_telemetry.py` (10 tests) all pass cleanly (33/33 passed).
   - Zero leaks across 600 frames and 100 ticks verified in forensic audit.

---

## 2. Logic Chain

1. **Documentation Asynchrony (Obs 1, Obs 2, Obs 3)**:
   During earlier project iterations, the test suite contained 945 tests. Subsequent milestones M1_EVO, M2_WEATHER, and M3_TELEMETRY added unit, integration, and adversarial tests, expanding the test suite to 1009 tests. Because `README.md` was not updated when these test files were committed, the documented count of 945 drifted by 64 tests from reality.

2. **Inadmissibility of Threshold Alteration (Obs 1, Obs 3)**:
   `tests/test_readme_khop_thuc_te.py` line 58 explicitly raises: `f"README ghi {n} test, thực tế {that}. Sửa README, đừng sửa ngưỡng."`. Modifying the test threshold to accommodate stale documentation is strictly forbidden by repository invariant and project rules. The fix must be applied to `README.md`.

3. **Sufficiency and Minimality of the Proposed Patch (Obs 2, Obs 3, Obs 5)**:
   Updating `README.md` line 131 from `945 mục, xanh` to `1009 mục, xanh` and line 185 from `# 945 test` to `# 1009 test` sets `ghi = [1009, 1009]`.
   Evaluating `abs(1009 - 1009) = 0 <= 50.45` succeeds unconditionally.
   Because all 1008 other tests in the repository pass (Obs 1), this 2-line documentation update immediately yields a 100% test pass rate (1009 passed, 1 skipped, 0 failed), clearing Forensic Audit Check 4.

---

## 3. Caveats

- **No Caveats Regarding Root Cause**: The root cause is unequivocally the test count mismatch between `README.md` and `tests/`.
- **Future Test Count Drift**: When subsequent milestones (e.g. M4_SPECTATOR or M5_VERIFY_E2E) add further tests, `README.md` must be incremented accordingly if the addition pushes the total count beyond the 5% tolerance window `[959, 1059]`.
- **Fast Mode Test Skip**: `tests/test_r03.py` remains skipped in standard runs unless `GENESIS_SLOW_TESTS=1` is set; this is normal project design and does not affect pass rate.

---

## 4. Conclusion

The sole blocker preventing M3_TELEMETRY from achieving forensic audit certification is the documentation desynchronization in `README.md`.

**Actionable Remediation Strategy**:
Apply the unified patch `.agents/explorer_m3_remediate_1/readme_test_count.patch` (or edit lines 131 and 185 in `README.md`):
- Line 131: Replace `| Test | **945 mục, xanh** |` with `| Test | **1009 mục, xanh** |`
- Line 185: Replace `make test         # 945 test` with `make test         # 1009 test`

Do not modify `tests/test_readme_khop_thuc_te.py` or any test thresholds.

---

## 5. Verification Method

To verify the remediation:

1. **Inspect Patch**:
   ```bash
   cat /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m3_remediate_1/readme_test_count.patch
   ```

2. **Apply Patch to `README.md`**:
   ```bash
   git apply /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_m3_remediate_1/readme_test_count.patch
   ```
   *(Or edit `README.md` lines 131 and 185 directly)*

3. **Verify Target Test**:
   ```bash
   pytest tests/test_readme_khop_thuc_te.py -v
   ```
   Expected: `2 passed in < 2.0s` (0 failures).

4. **Verify Full Repository Test Suite**:
   ```bash
   pytest -q
   ```
   Expected: `1009 passed, 1 skipped in ~180s` (Exit code: 0).

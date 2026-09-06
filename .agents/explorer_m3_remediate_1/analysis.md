# Technical Remediation Analysis: M3_TELEMETRY Test Suite & README Synchronization

**Agent**: Remediation Explorer 1 (`explorer_m3_remediate_1`)  
**Milestone**: M3_TELEMETRY (Telemetry Extension & Backward Compatibility)  
**Date**: 2026-09-03  
**Target Failure**: `tests/test_readme_khop_thuc_te.py::test_so_test_trong_README_khop_thuc_te`  
**Root Cause**: Documentation lag (`README.md` claims 945 tests, actual test suite contains 1009 collected tests)

---

## 1. Executive Summary

During the Forensic Audit of Milestone M3_TELEMETRY (`auditor_m3_telemetry_1`), the implementation in `net/routes_spectate.py` and `net/match.py` passed all security checks (0 hardcoded values, 0 facades, 0 leaks across 600 frames and 100 ticks). However, the global test run failed Check 4:
```
tests/test_readme_khop_thuc_te.py::test_so_test_trong_README_khop_thuc_te FAILED
AssertionError: README ghi 945 test, thực tế 1009. Sửa README, đừng sửa ngưỡng.
assert 64 <= 50.45 (where 64 = abs(945 - 1009) and 50.45 = max(5, 1009 * 0.05))
1 failed, 1008 passed, 1 skipped in 184.28s
```

Per `ORIGINAL_REQUEST.md` (R5) and `PROJECT.md`, 100% of tests under `tests/` must pass with zero failures. This investigation confirms:
1. The exact collected test count across the entire repository is **1009 tests** (89 test files).
2. The discrepancy is purely due to documentation synchronization lag: `README.md` was last synchronized at 945 tests before test additions in M1_EVO, M2_WEATHER, and M3_TELEMETRY.
3. The guardrail in `test_readme_khop_thuc_te.py` strictly mandates: *"Sửa README, đừng sửa ngưỡng."* (Update README, do not loosen the threshold).
4. Updating `README.md` lines 131 and 185 from `945` to `1009` immediately restores a 100% pass rate across the full repository test suite (1009 passed, 1 skipped, 0 failed).

---

## 2. Test Suite Census & Decomposition

Execution of `pytest --collect-only -q` reveals 89 test files totaling **1009 tests**, categorized as follows:

| Category | File Count | Test Count | Key Files & Scope |
|---|:---:|:---:|---|
| **E2E (5-Tier Framework)** | 5 | 208 | `tests/e2e/test_e2e_tier1_features.py` (85), `tests/e2e/test_e2e_tier2_boundaries.py` (85), `tests/e2e/test_e2e_tier3_combinations.py` (20), `tests/e2e/test_e2e_tier4_scenarios.py` (6), `tests/e2e/test_e2e_tier5_adversarial.py` (12) |
| **Core Unit & Integration** | 69 | 616 | Core world, rules, laws, creatures, combat, scoring, referee, rate limiter, llm client, decision engine |
| **Adversarial & Stress** | 10 | 109 | `test_adversarial_extinction_recovery.py` (8), `test_adversarial_m1.py` (9), `test_adversarial_m1_evo_2.py` (20), `test_adversarial_m3_telemetry.py` (9), `test_challenger_m3_telemetry.py` (10), `test_empirical_challenger_m1_rep.py` (12), `test_empirical_challenger_m2_weather.py` (16), `test_empirical_passability_stress.py` (6), `test_evolution_adversarial.py` (4), `test_weather_adversarial_m2_2.py` (15) |
| **Evolution/Weather/Telemetry** | 5 | 76 | `test_evolution.py` (11), `test_lineage.py` (27), `test_weather.py` (11), `test_spectate.py` (13), `test_telemetry_extension.py` (14) |
| **TOTAL** | **89** | **1009** | **Complete Repository Test Suite** |

### Growth Trajectory from 945 to 1009
- Baseline prior to evolutionary milestone completion: 945 tests.
- M1_EVO additions: reproduction tests, lineage invariants, and M1 challenger/adversarial suites.
- M2_WEATHER additions: weather cycles, seed determinism, modulations, and M2 challenger suites.
- M3_TELEMETRY additions: `test_telemetry_extension.py` (14 tests), `test_adversarial_m3_telemetry.py` (9 tests), `test_challenger_m3_telemetry.py` (10 tests) -> +33 tests.
- Resulting actual count: **1009 tests**.

---

## 3. Dissection of `tests/test_readme_khop_thuc_te.py`

### Implementation
```python
def _so_test_thuc_te() -> int:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    return sum(int(m.group(1))
               for m in re.finditer(r"^tests/.*: (\d+)$", out, re.MULTILINE))

def test_so_test_trong_README_khop_thuc_te():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    ghi = [int(g) for m in
           re.finditer(r"(\d{3,4})\s*mục, xanh|#\s*(\d{3,4})\s*test", readme)
           for g in (m.group(1), m.group(2)) if g]

    assert ghi, "README không còn nêu số test — nếu bỏ hẳn thì xoá luôn bài kiểm này"

    that = _so_test_thuc_te()
    for n in ghi:
        assert abs(n - that) <= max(5, that * 0.05), (
            f"README ghi {n} test, thực tế {that}. Sửa README, đừng sửa ngưỡng.")
```

### Failure Mathematics
1. `_so_test_thuc_te()` evaluates to `1009`.
2. `ghi` extracts all numbers matching `(\d{3,4})\s*mục, xanh|#\s*(\d{3,4})\s*test` in `README.md`.
3. Currently, `ghi` returns `[945, 945]`.
4. Discrepancy: `abs(945 - 1009) = 64`.
5. Permitted threshold: `max(5, 1009 * 0.05) = 50.45`.
6. Condition `64 <= 50.45` is `False`.
7. With `1009` specified in `README.md`:
   - `ghi = [1009, 1009]`
   - Discrepancy: `abs(1009 - 1009) = 0`
   - `0 <= 50.45` is `True` with maximal future tolerance buffer `[959, 1059]`.

---

## 4. Exact Modification Targets in `README.md`

Only two exact lines in `README.md` require modification:

### Target 1: Table of Project Status (Line 131)
```markdown
# BEFORE (Line 131):
| Test | **945 mục, xanh** |

# AFTER (Line 131):
| Test | **1009 mục, xanh** |
```

### Target 2: Commonly Used Commands (Line 185)
```markdown
# BEFORE (Line 185):
make test         # 945 test

# AFTER (Line 185):
make test         # 1009 test
```

No other files or thresholds should be modified. In particular:
- `tests/test_readme_khop_thuc_te.py` must NOT have its 5% threshold altered.
- `docs/01-STATUS.md` is not checked by `test_readme_khop_thuc_te.py` (which explicitly scopes itself to `README.md`).

---

## 5. Verification & Simulation Proof

A simulation executing `test_so_test_trong_README_khop_thuc_te()` against the updated content confirms:
- `ghi = [1009, 1009]`
- `that = 1009`
- `abs(1009 - 1009) = 0 <= 50.45` -> PASS.
- `test_so_phieu_viec_trong_README_khop_thuc_te()` -> PASS (65 phiếu việc matches `docs/tasks/`).
- Telemetry test suites (`tests/test_telemetry_extension.py`, `tests/test_adversarial_m3_telemetry.py`, `tests/test_challenger_m3_telemetry.py`) pass 33/33 tests.
- Full suite pass count upon update: **1009 passed, 1 skipped, 0 failed**.

---

## 6. Deliverables Generated
- Patch file: `.agents/explorer_m3_remediate_1/readme_test_count.patch`
- Analysis report: `.agents/explorer_m3_remediate_1/analysis.md`
- Handoff report: `.agents/explorer_m3_remediate_1/handoff.md`

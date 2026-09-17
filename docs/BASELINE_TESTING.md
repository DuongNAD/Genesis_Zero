# Regression baseline

## Environment

Use the repository `.venv` (milestone reference: Python 3.11.9). Install the
`dev` extra, including pytest-cov, rather than relying on a system pytest:

```powershell
uv sync --extra dev --locked
powershell -NoProfile -ExecutionPolicy Bypass -File "E:\Project\01_AI_Agents\Genesis_Zero\scripts\run_baseline.ps1"
```

`uv` environments do not normally contain pip; that alone is not a broken venv.
This milestone also bootstrapped pip for environment verification. The baseline
records import results and package versions in `environment.json`; a pip freeze
snapshot (or pip's diagnostic if unavailable) is in `dependencies.txt`.

On Linux/macOS use the repository venv Python to invoke the same Python script.
`make baseline` uses the currently active Python, so activate the venv first.

## Artifacts and exit status

Each invocation creates a unique directory beneath
`E:\Project\01_AI_Agents\Genesis_Zero\runs\baselines`:

- `pytest.log`: full verbose UTF-8 output, captured warnings, traceback summary,
  slowest tests, and terminal Pass/Fail/Error/Skip summary.
- `junit.xml`: machine-readable pytest results.
- `summary.json`: counts, collected/reported comparison, pass/failure percentages,
  problems, elapsed time, completion flag, and pytest exit code.
- `command.json`, `environment.json`, `dependencies.txt`: reproduction inputs.

Watch progress while running with `Get-Content -Wait` on the reported log path.
The script does not stop on ordinary test failures and clears inherited fail-fast
options. It does not override the project's warning filters. All collected tests
are attempted, including after collection errors. A 120-second faulthandler dump
helps diagnose a blocked test without killing the runner.

The whole-suite watchdog defaults to 3600 seconds (`--timeout 7200` to change).
On watchdog expiration the child process tree is terminated, exit status is 124,
and the baseline is marked incomplete. Missing/malformed XML, mismatched item
counts, and pytest abnormal exit statuses are never labelled complete. A completed
baseline with failures retains pytest exit status 1; completion does NOT mean all
tests passed. Pass and fail/error rates exclude skipped tests; skips remain listed
separately. Xfail is represented as skipped by JUnit; terminal output preserves
pytest's detailed categories. Collection errors or multiple setup/teardown reports
can make the collected/report count check conservatively mark a run incomplete.

## Encoding and schema contracts

The three existing launch boundaries (`genesis.run`, launch, preflight) reconfigure
stdout/stderr to UTF-8. Child output readers must also decode UTF-8. CLI regression
tests deliberately set `PYTHONIOENCODING=cp1252` and `PYTHONUTF8=0`, then strictly
decode output as UTF-8; do not change those test inputs to make a failure disappear.
The baseline child itself uses `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`, covering
both default file reads and standard streams.

The manifest resolves `./map_manifest.schema.json` beside itself. The local
Draft-07 schema preserves the validation rules from the Anima-Engine contract
inspected on 2026-09-17, with descriptions condensed and only internal `$ref`s.
No sibling checkout or HTTP schema request is required. It validates structure,
not file existence or checksums: those remain separate data-standardization tests.
In particular the upstream schema does not constrain schemaVersion to exactly 1,
seaLevel to [0,1], or additional metadata/modelAsset; no stricter rules were
invented during this baseline milestone.

## Acceptance scope

A 100% completed baseline is an inventory, not permission to loosen simulation
assertions. Existing Blender/model-dependent skips must be reviewed separately.
Windows subprocess behavior is exercised here; Linux/macOS runtime verification
still requires those platforms. The historic stop at 18% must not be described as
fixed at a specific root cause unless reproduced with a traceback.

## Historical baseline — 2026-09-17 (before crash infrastructure regressions)

Artifacts: `E:\Project\01_AI_Agents\Genesis_Zero\runs\baselines\20260917T123430.643650Z`.
The PowerShell entry point completed with pytest exit 1, `completed=true`:

| Collected/reported | Passed | Failed | Errors | Skipped | Pass rate excluding skips |
|---|---:|---:|---:|---:|---:|
| 1689 / 1689 | 1648 | 2 | 0 | 39 | 99.88% |

Wrapper time: 374.72 seconds; pytest: 373.74 seconds. The runner passed 18% and
finished normally. The historic crash/hang was not reproduced, so no specific
historic crash root cause is claimed. Default warning filters resolved correctly
with Starlette 1.6.0; two deprecations remain visible rather than suppressed.

Failures in this snapshot:
1. `test_chi_mot_duong_ra`: structural test expected the old `_seed_match` reader,
   but initialization was extracted to `_seed_steps`. After collecting this
   baseline, the single allowed initialization name was replaced (not extended).
   Targeted rerun: 1 passed; no simulation or public-law behavior changed.
2. `test_so_test_trong_README_khop_thuc_te`: README says 1066 tests, whereas the
   live collection probe saw 1690. At that time README was updated to 1690 collected
   tests, preserving the historical outcomes instead of claiming the suite was green.
   Targeted rerun of both previously failing tests: 2 passed, 2 deprecation warnings
   in 1.77 seconds. No full-suite rerun had been completed at that point.

The extra isolated-subprocess infrastructure test was added after baseline
collection, explaining 1689 at session start versus 1690 at the later live probe.
The final focused infrastructure/CLI suite passed 22 tests in 2.87 seconds,
including real subprocess Pass/Fail/Error/Skip accounting. A separate watchdog
probe returned 124 and `completed=false`. `pip check`, targeted Ruff, compilation,
local manifest validation and lock consistency checks passed. Coverage plugin
was exercised successfully; the focused coverage result is not full-suite code
coverage. No full-suite rerun after the last structural-test fix is claimed.

Earlier diagnostic runs were made while files were changing and without a fully
standardized UTF-8 environment. Their results are retained in scratch logs but
must not replace this named baseline or be combined with it.

## Measured baseline — 2026-09-17 (full rerun after crash-infrastructure regressions)

Artifacts: `E:\Project\01_AI_Agents\Genesis_Zero\runs\baselines\20260917T132824.203520Z`.
The PowerShell entry point exited 0 with `completed=true`:

| Collected/reported | Passed | Failed | Errors | Skipped | Pass rate excluding skips |
|---|---:|---:|---:|---:|---:|
| 1703 / 1703 | 1664 | 0 | 0 | 39 | 100.00% |

Wrapper time: 238.3 seconds; pytest: 237.74 seconds (`1664 passed, 39 skipped,
2 warnings in 237.74s`). pytest exit code 0, `termination=pytest_finished`, no
fatal markers, watchdog not expired, `log_utf8_valid=true`, `problems=[]`, and
`collected == total_reported == 1703`. This is the first full-suite run after
adding the crash-infrastructure regression tests (`test_crash_signal_is_captured_
and_marks_run_incomplete`, `test_watchdog_expiry_marks_run_incomplete`, and the
`exit_details` classification cases); the run itself reproduced neither a crash
nor a hang: no `Windows fatal exception`, no access-violation status, and
`watchdog_expired=false`. The 1689-item snapshot above is retained as history.

The two failures from the historical snapshot were rerun in isolation twice
(`pytest -x --tb=long -k "test_chi_mot_duong_ra or
test_so_test_trong_README_khop_thuc_te"`): both passed each time, and in this
full rerun they pass as part of the suite. No assertion was loosened to achieve
the 100% executed pass rate; all 39 skips are the same environment/asset
conditionals documented earlier (missing Blender binary, master 3D assets
removed in the current revision, the POSIX-only `SIGINT` launcher test, and the
`GENESIS_SLOW_TESTS=1` marker test).

Warning filters resolved correctly with Starlette 1.6.0; exactly two
deprecations remain visible rather than suppressed — the
`StarletteDeprecationWarning` about `httpx` with `starlette.testclient`
(via `fastapi/testclient.py`) and the `anyio.abc.BlockingPortal` alias
`DeprecationWarning` (via `starlette/testclient.py`). No other warning
categories appeared in this run.

The test inventory (`runs/test_inventory.json`, regenerated by
`scripts/count_tests.py`) records 1703 items across 111 files; README's two
count references match it (`README match: True`), and
`tests/test_readme_khop_thuc_te.py` passes against the updated README.


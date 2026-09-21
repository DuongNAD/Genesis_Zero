"""Empirical challenger test suite for Windows launchers (run.ps1, run.bat).

Milestone: M1 Iteration 2 Gate
Author: teamwork_preview_challenger_m1_iter2_2

Verifies:
1. Byte-level UTF-8 BOM integrity (no double BOM, single UTF-8 BOM header).
2. Elimination of byte 0x93 CP1252 smart-quote collision in PowerShell 5.1 tokenizer.
3. Accurate PowerShell AST parsing with 0 errors and no BadExpression tokens.
4. Execution of run.ps1 and run.bat in offline reflex mode (returncode 0 in ~3s).
5. Accurate returncode propagation (e.g. code 2 on invalid flags).
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
RUN_PS1 = ROOT / "run.ps1"
RUN_BAT = ROOT / "run.bat"


def test_ps1_bom_integrity():
    """Verify that run.ps1 has exactly one UTF-8 BOM header and no duplicate BOM."""
    raw = RUN_PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf"), "run.ps1 must start with UTF-8 BOM (0xEF, 0xBB, 0xBF)"
    assert not raw.startswith(b"\xef\xbb\xbf\xef\xbb\xbf"), "run.ps1 must not have double BOM"
    assert raw.count(b"\xef\xbb\xbf") == 1, "run.ps1 must have exactly 1 UTF-8 BOM occurrence"


def test_ps1_smart_quote_collision_prevented():
    """Verify that byte 0x93 in multi-byte UTF-8 emoji is not parsed as CP1252 smart quote."""
    raw = RUN_PS1.read_bytes()
    assert b"\x93" in raw, "run.ps1 contains 0x93 continuation bytes in UTF-8 emoji (e.g. 📦)"

    # If decoded as CP1252 (simulating missing BOM behavior in PS 5.1)
    cp1252_text = raw.decode("cp1252", errors="replace")
    assert "\u201c" in cp1252_text, "In CP1252, byte 0x93 would decode to smart quote '\u201c'"

    # But decoded as UTF-8 (actual PS 5.1 behavior with UTF-8 BOM)
    utf8_text = raw.decode("utf-8-sig")
    assert "\u201c" not in utf8_text, "Decoded UTF-8 must NOT contain smart quote '\u201c'"
    assert "\U0001f4e6" in utf8_text, "Decoded UTF-8 must contain the intended package emoji 📦"


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows PowerShell")
def test_powershell_ast_clean_parse():
    """Empirically invoke PowerShell 5.1 language parser to verify AST cleanly parses with 0 errors."""
    ps_cmd = (
        "$tokens = $null; $errors = $null; "
        f"$ast = [System.Management.Automation.Language.Parser]::ParseFile('{RUN_PS1}', [ref]$tokens, [ref]$errors); "
        "if ($errors.Count -gt 0) { exit $errors.Count } "
        "$bad = $tokens | Where-Object { $_.Kind -like '*Error*' -or $_.Kind -like '*Bad*' }; "
        "if ($bad.Count -gt 0) { exit 100 } "
        "exit 0"
    )
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 0, f"PowerShell AST parsing failed: stderr={res.stderr}, stdout={res.stdout}"


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows PowerShell and Windows paths")
def test_run_ps1_execution_reflex():
    """Empirical test: run.ps1 runs in ~3s, exits 0, and uses .venv python."""
    start = time.perf_counter()
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_PS1), "--ticks", "5", "--no-render"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    duration = time.perf_counter() - start
    assert res.returncode == 0, f"run.ps1 failed with code {res.returncode}: {res.stderr}\n{res.stdout}"
    assert "(Virtualenv)" in res.stdout, "run.ps1 must execute using the virtual environment Python"
    assert "Khởi chạy mô phỏng" in res.stdout, "run.ps1 must successfully start simulation"
    assert duration < 8.0, f"run.ps1 should complete in ~3s, took {duration:.2f}s"


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows PowerShell and Windows paths")
def test_run_ps1_exit_code_propagation():
    """Empirical test: run.ps1 propagates non-zero exit codes from child process."""
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUN_PS1), "--invalid-test-flag-xyz"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2, f"Expected returncode 2 from argparse error, got {res.returncode}"
    assert "unrecognized arguments: --invalid-test-flag-xyz" in res.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows cmd")
def test_run_bat_execution_reflex():
    """Empirical test: run.bat runs, exits 0, and uses .venv python."""
    res = subprocess.run(
        ["cmd", "/c", str(RUN_BAT), "--ticks", "5", "--no-render"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"run.bat failed with code {res.returncode}: {res.stderr}\n{res.stdout}"
    assert "(Virtualenv)" in res.stdout, "run.bat must execute using the virtual environment Python"
    assert "Khởi chạy mô phỏng" in res.stdout, "run.bat must successfully start simulation"


@pytest.mark.skipif(sys.platform != "win32", reason="Requires Windows cmd")
def test_run_bat_exit_code_propagation():
    """Empirical test: run.bat propagates non-zero exit codes from child process."""
    res = subprocess.run(
        ["cmd", "/c", str(RUN_BAT), "--invalid-test-flag-xyz"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2, f"Expected returncode 2 from argparse error, got {res.returncode}"
    assert "unrecognized arguments: --invalid-test-flag-xyz" in res.stderr

"""Offline regression contracts for baseline collection and local manifest schema."""
import copy
import faulthandler
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from scripts.run_baseline import exit_details, summarize

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def manifest_contract():
    path = ROOT / "assets" / "map_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    schema_path = (path.parent / manifest["$schema"]).resolve()
    assert schema_path.parent == path.parent
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return manifest, Draft7Validator(schema)


def test_manifest_resolves_local_contract(manifest_contract):
    manifest, validator = manifest_contract
    validator.validate(manifest)


@pytest.mark.parametrize("mutation", ["missing", "magic", "bounds", "taxonomy", "views", "camera"])
def test_local_contract_rejects_invalid_manifest(manifest_contract, mutation):
    manifest, validator = manifest_contract
    bad = copy.deepcopy(manifest)
    if mutation == "missing":
        del bad["worldArtifact"]
    elif mutation == "magic":
        bad["worldArtifact"]["magic"] = "BAD"
    elif mutation == "bounds":
        bad["coordinateSystem"]["worldMinXZ"] = -99
    elif mutation == "taxonomy":
        bad["biomeTaxonomy"]["canonicalCount"] = 21
    elif mutation == "views":
        bad["views"] = []
    else:
        bad["views"][0]["camera"]["position"] = [0, 0]
    assert not validator.is_valid(bad)


def test_summary_counts_outcomes_and_failure_rate(tmp_path):
    xml = tmp_path / "junit.xml"
    xml.write_text('<testsuites><testsuite><testcase name="pass"/>'
                   '<testcase name="fail"><failure message="bad"/></testcase>'
                   '<testcase name="error"><error message="fixture"/></testcase>'
                   '<testcase name="skip"><skipped/></testcase></testsuite></testsuites>')
    summary = summarize(xml, 1, "collected 4 items")
    assert summary["completed"]
    assert [summary[k] for k in ("passed", "failed", "errors", "skipped")] == [1, 1, 1, 1]
    assert summary["pass_rate_excluding_skips"] == 33.33
    assert len(summary["problems"]) == 2
    assert not summarize(xml, 124, "collected 4 items")["completed"]
    assert not summarize(xml, 1, "collected 5 items")["completed"]


def test_missing_xml_is_incomplete(tmp_path):
    assert not summarize(tmp_path / "missing.xml", 0, "collected 1 item")["completed"]



def test_runner_in_clean_subprocess(tmp_path):
    """Exercise the real CLI against a tiny isolated suite, without recursive tests."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "run_baseline.py").write_bytes((ROOT / "scripts" / "run_baseline.py").read_bytes())
    tests = tmp_path / "tests"
    tests.mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tests / "test_sample.py").write_text(
        "import pytest\n"
        "def test_pass(): assert True\n"
        "def test_fail(): assert False\n"
        "@pytest.fixture\ndef broken(): raise RuntimeError('fixture error')\n"
        "def test_error(broken): pass\n"
        "@pytest.mark.skip(reason='sample')\ndef test_skip(): pass\n",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTEST_ADDOPTS": "-x"}
    env.pop("PYTEST_CURRENT_TEST", None)
    proc = subprocess.run(
        [sys.executable, str(scripts / "run_baseline.py"), "--output", str(tmp_path / "reports")],
        cwd=tmp_path, env=env, capture_output=True, encoding="utf-8", timeout=45,
    )
    assert proc.returncode == 1, proc.stderr
    report = next((tmp_path / "reports").glob("*/summary.json"))
    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["completed"]
    assert summary["collected"] == 4
    assert [summary[k] for k in ("passed", "failed", "errors", "skipped")] == [1, 1, 1, 1]
    assert (report.parent / "junit.xml").exists()
    assert (report.parent / "environment.json").exists()
    assert (report.parent / "pytest.log").exists()


def _isolated_project(tmp_path: Path, body: str) -> tuple[Path, dict[str, str]]:
    """A throwaway checkout with the runner copied in: no recursion into this suite."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "run_baseline.py").write_bytes((ROOT / "scripts" / "run_baseline.py").read_bytes())
    tests = tmp_path / "tests"
    tests.mkdir()
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tests / "test_sample.py").write_text(body, encoding="utf-8")
    env = {**os.environ, "PYTEST_ADDOPTS": ""}
    env.pop("PYTEST_CURRENT_TEST", None)
    return tmp_path, env


@pytest.mark.parametrize(
    ("exit_code", "log_text", "expected"),
    [
        pytest.param(0, "", "pytest_finished", id="clean-exit"),
        pytest.param(1, "collected 1 item", "pytest_finished", id="finished-with-failures"),
        pytest.param(2, "", "pytest_abnormal", id="interrupted"),
        pytest.param(3, "", "pytest_abnormal", id="internal-error"),
        pytest.param(4, "", "pytest_abnormal", id="usage-error"),
        pytest.param(5, "", "pytest_abnormal", id="no-tests-collected"),
        pytest.param(124, "", "watchdog", id="watchdog-kill"),
        pytest.param(-11, "Fatal Python error: Segmentation fault", "crash", id="posix-signal"),
        pytest.param(3221225477, "Windows fatal exception: access violation", "crash",
                     id="windows-access-violation"),
        pytest.param(0, "Fatal Python error: nested subprocess died", "crash", id="fatal-marker-in-log"),
        pytest.param(7, "", "unexpected_exit", id="unknown-status"),
    ],
)
def test_exit_details_classifies_termination(exit_code: int, log_text: str, expected: str):
    """pytest statuses and OS-level terminations are recorded separately.

    A crash signal recorded on exit 0 (a nested subprocess died) only annotates
    the summary; `completed` keeps its existing accounting contract.
    """
    details = exit_details(exit_code, log_text)
    assert details["termination"] == expected
    if expected == "crash":
        assert details["fatal_markers"] or details["signal_number"] or details["windows_status"]


def test_crash_signal_is_captured_and_marks_run_incomplete(tmp_path):
    """A SIGSEGV mid-run must leave termination=crash with the faulthandler dump.

    This is the isolated reproduction of a pytest process being killed outright:
    the summary must stay incomplete and the log must keep the stack trace.
    """
    if not hasattr(faulthandler, "_sigsegv"):
        pytest.skip("CPython faulthandler._sigsegv unavailable")
    project, env = _isolated_project(
        tmp_path,
        "import faulthandler\n"
        "def test_hard_crash():\n"
        "    faulthandler._sigsegv()\n",
    )
    subprocess.run(
        [sys.executable, str(project / "scripts" / "run_baseline.py"),
         "--output", str(project / "reports")],
        cwd=project, env=env, capture_output=True, encoding="utf-8", timeout=120,
    )
    report = next((project / "reports").glob("*/summary.json"))
    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["completed"] is False
    assert summary["termination"] == "crash"
    assert summary["fatal_markers"], summary
    assert summary["xml_error"] is not None  # the dead session never wrote junit.xml
    log_text = report.parent.joinpath("pytest.log").read_text(encoding="utf-8", errors="replace")
    assert "test_hard_crash" in log_text  # the captured dump names the crashing test
    assert summary["raw_returncode"] == summary["exit_code"]
    assert summary["watchdog_expired"] is False
    if os.name == "nt":
        # This runtime reports exit 3 with a fatal dump; other Windows
        # runtimes can expose the access-violation NTSTATUS directly.
        assert summary["raw_returncode"] in (3, 0xC0000005), summary
        expected_status = "0xC0000005" if summary["raw_returncode"] == 0xC0000005 else None
        assert summary["windows_status"] == expected_status
    else:
        assert summary["signal_number"] == 11


def test_watchdog_expiry_marks_run_incomplete(tmp_path):
    """Expiry must terminate the process tree, keep exit 124, and stay incomplete."""
    project, env = _isolated_project(
        tmp_path,
        "import time\n"
        "def test_hangs():\n"
        "    time.sleep(30)\n",
    )
    proc = subprocess.run(
        [sys.executable, str(project / "scripts" / "run_baseline.py"),
         "--output", str(project / "reports"), "--timeout", "1"],
        cwd=project, env=env, capture_output=True, encoding="utf-8", timeout=120,
    )
    assert proc.returncode == 124
    report = next((project / "reports").glob("*/summary.json"))
    summary = json.loads(report.read_text(encoding="utf-8"))
    assert summary["completed"] is False
    assert summary["watchdog_expired"] is True
    assert summary["termination"] == "watchdog"
    assert summary["exit_code"] == 124
    log_text = report.parent.joinpath("pytest.log").read_text(encoding="utf-8", errors="replace")
    assert "BASELINE WATCHDOG" in log_text

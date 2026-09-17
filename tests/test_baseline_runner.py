"""Baseline outcome accounting must not turn failures into successful runs."""
from pathlib import Path

import pytest

from scripts.run_baseline import summarize

JUNIT = (
    '<testsuites><testsuite><testcase name="pass"/>'
    '<testcase name="fail"><failure/></testcase>'
    '<testcase name="error"><error/></testcase>'
    '<testcase name="skip"><skipped/></testcase></testsuite></testsuites>'
)


@pytest.mark.parametrize("exit_code,completed", [(0, True), (1, True), (2, False), (124, False)])
def test_summary_classifies_junit(tmp_path: Path, exit_code: int, completed: bool):
    xml = tmp_path / "junit.xml"
    xml.write_text(JUNIT, encoding="utf-8")
    summary = summarize(xml, exit_code, log_text="collected 4 items")
    assert summary["passed"] == summary["failed"] == summary["errors"] == summary["skipped"] == 1
    assert summary["total_reported"] == 4
    assert summary["collected"] == 4
    assert summary["pass_rate_excluding_skips"] == 33.33
    assert summary["failure_rate_excluding_skips"] == 66.67
    assert summary["completed"] is completed
    assert summary["exit_code"] == exit_code


def test_missing_junit_is_incomplete(tmp_path: Path):
    summary = summarize(tmp_path / "missing.xml", 0)
    assert summary["completed"] is False
    assert summary["total_reported"] == 0
    assert summary["pass_rate_excluding_skips"] is None


def test_unaccounted_collected_items_are_incomplete(tmp_path: Path):
    """A truncated run (progress shown, XML short) must never look completed."""
    xml = tmp_path / "junit.xml"
    xml.write_text(JUNIT, encoding="utf-8")
    summary = summarize(xml, 2, log_text="collected 900 items")
    assert summary["completed"] is False
    assert summary["collected"] == 900 and summary["total_reported"] == 4


def test_problem_list_captures_outcomes(tmp_path: Path):
    xml = tmp_path / "junit.xml"
    xml.write_text(JUNIT, encoding="utf-8")
    summary = summarize(xml, 1, log_text="collected 4 items")
    kinds = sorted(p["outcome"] for p in summary["problems"])
    assert kinds == ["error", "failure"]


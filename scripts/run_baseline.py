"""Collect an honest regression baseline with the current repository environment."""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = {
    "pytest": "pytest", "pytest-cov": "pytest_cov", "pytest-timeout": "pytest_timeout",
    "pytest-asyncio": "pytest_asyncio", "numpy": "numpy", "jsonschema": "jsonschema",
    "rich": "rich", "httpx": "httpx", "fastapi": "fastapi", "starlette": "starlette",
    "uvicorn": "uvicorn", "pydantic": "pydantic",
}


def exit_details(exit_code: int, log_text: str = "") -> dict:
    """Separate pytest statuses from OS termination; never infer a historic cause."""
    markers = [marker for marker in ("Fatal Python error:", "Windows fatal exception:")
               if marker in log_text]
    signal_number = None
    windows_status = None
    if os.name == "nt" and exit_code & 0xC0000000 == 0xC0000000:
        windows_status = f"0x{exit_code & 0xFFFFFFFF:08X}"
    elif exit_code < 0:
        signal_number = -exit_code
    if exit_code == 124:
        kind = "watchdog"
    elif signal_number or windows_status or markers:
        kind = "crash"
    elif exit_code in (0, 1):
        kind = "pytest_finished"
    elif exit_code in (2, 3, 4, 5):
        kind = "pytest_abnormal"
    else:
        kind = "unexpected_exit"
    return {"termination": kind, "signal_number": signal_number,
            "windows_status": windows_status, "fatal_markers": markers}


def write_summary(output: Path, summary: dict) -> None:
    """Atomic replacement leaves a readable incomplete snapshot if the parent dies."""
    temporary = output / "summary.tmp"
    temporary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    temporary.replace(output / "summary.json")


def summarize(path: Path, exit_code: int, log_text: str = "") -> dict:
    counts = dict(passed=0, failed=0, errors=0, skipped=0)
    problems = []
    xml_error = None
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        xml_error = str(exc)
        tree = ET.ElementTree(ET.Element("testsuites"))
    if xml_error is None:
        for case in tree.iter("testcase"):
            bad = case.find("error") if case.find("error") is not None else case.find("failure")
            if bad is not None:
                kind = "error" if case.find("error") is not None else "failure"
                counts["errors" if kind == "error" else "failed"] += 1
                problems.append({"test": f'{case.get("classname", "")}::{case.get("name", "")}',
                                 "outcome": kind, "message": bad.get("message", "")})
            elif case.find("skipped") is not None:
                counts["skipped"] += 1
            else:
                counts["passed"] += 1
    total = sum(counts.values())
    executed = total - counts["skipped"]
    collected = None
    match = re.search(r"collected (\d+) items?", log_text)
    if match:
        collected = int(match[1])
    return {
        **counts, **exit_details(exit_code, log_text),
        "total_reported": total, "collected": collected, "exit_code": exit_code,
        # A baseline is complete only when pytest finished normally AND every
        # collected item is accounted for in the XML. 124 marks watchdog kill.
        "completed": xml_error is None and exit_code in (0, 1) and collected == total,
        "xml_error": xml_error,
        "pass_rate_excluding_skips": round(100 * counts["passed"] / executed, 2) if executed else None,
        "failure_rate_excluding_skips": round(100 * (counts["failed"] + counts["errors"]) / executed, 2) if executed else None,
        "problems": problems,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "baselines")
    parser.add_argument("--timeout", type=int, default=3600, help="Whole-suite watchdog seconds")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    output = args.output.resolve() / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    output.mkdir(parents=True)
    write_summary(output, {"completed": False, "state": "starting", "exit_code": None})
    environment: dict[str, Any] = {
        "python": platform.python_version(),
        "executable": sys.executable,
        "platform": platform.platform(),
        "packages": {},
        "import_errors": {},
    }
    for distribution, module in DEPENDENCIES.items():
        try:
            importlib.import_module(module)
            environment["packages"][distribution] = importlib.metadata.version(distribution)
        except Exception as exc:
            environment["import_errors"][distribution] = str(exc)
    (output / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True)
    (output / "dependencies.txt").write_bytes(freeze.stdout + freeze.stderr)
    print(f"Baseline artifacts: {output}", flush=True)
    if environment["import_errors"]:
        print(json.dumps(environment["import_errors"], indent=2), flush=True)
        return 2
    xml = output / "junit.xml"
    command = [sys.executable, "-X", "faulthandler", "-u", "-m", "pytest", str(ROOT / "tests"),
               "--capture=fd",
               "-o", "addopts=", "--maxfail=0", "--continue-on-collection-errors",
               "-vv", "-ra", "--tb=short", "--durations=25",
               "-o", "faulthandler_timeout=120", f"--junitxml={xml}"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1")
    # User/CI fail-fast options must not silently truncate a baseline.
    env.pop("PYTEST_ADDOPTS", None)
    (output / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    started = time.monotonic()
    watchdog_expired = False
    # Direct file handles, never PIPE: no reader thread or pipe backpressure.
    # Pin fd capture (disk-backed temporary files) and unbuffered child streams.
    with (output / "pytest.log").open("wb", buffering=0) as log:
        process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=os.name != "nt")
        write_summary(output, {"completed": False, "state": "running", "exit_code": None,
                               "pid": process.pid, "timeout_seconds": args.timeout})
        try:
            code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            watchdog_expired = True
            log.write(b"\nBASELINE WATCHDOG: terminating pytest process tree\n")
            if os.name == "nt":
                # taskkill output uses the Windows locale, not necessarily UTF-8.
                killed = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                        check=False, capture_output=True)
                log.write(f"taskkill exit code: {killed.returncode}\n".encode("utf-8"))
            else:
                import signal
                killpg = getattr(os, "killpg", None)
                sigkill = getattr(signal, "SIGKILL", signal.SIGTERM)
                if killpg is not None:
                    killpg(process.pid, sigkill)
            process.wait()
            code = 124
    raw_log = (output / "pytest.log").read_bytes()
    try:
        log_text = raw_log.decode("utf-8")
        log_utf8_valid = True
    except UnicodeDecodeError:
        log_text = raw_log.decode("utf-8", errors="replace")
        log_utf8_valid = False
    summary = summarize(xml, code, log_text)
    summary.update(state="finished", raw_returncode=process.returncode, pid=process.pid,
                   watchdog_expired=watchdog_expired, timeout_seconds=args.timeout,
                   log_utf8_valid=log_utf8_valid,
                   elapsed_seconds=round(time.monotonic() - started, 2))
    write_summary(output, summary)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Detailed log: {output / 'pytest.log'}", flush=True)
    return code if code else (0 if summary["completed"] else 2)


if __name__ == "__main__":
    raise SystemExit(main())

import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("entry", [["-m", "genesis.run"], ["scripts/launch.py"], ["scripts/preflight.py"]])
def test_cli_help_under_cp1252(entry):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env["PYTHONUTF8"] = "0"
    cmd = [sys.executable, *entry, "--help"]
    proc = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
        cwd=str(os.path.dirname(os.path.dirname(__file__))),
    )
    assert proc.returncode == 0
    expected = "Chạy một ván Genesis Zero" if entry[0] == "-m" else (
        "Chạy chế độ phản xạ" if "launch.py" in entry[0] else "chạy cả bộ test"
    )
    assert expected in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr


@pytest.mark.parametrize("module", ["scripts.launch", "scripts.preflight"])
def test_launcher_help_under_cp1252(module):
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    proc = subprocess.run(
        [sys.executable, "-m", module, "--help"], env=env,
        capture_output=True, encoding="utf-8", timeout=15,
        cwd=os.path.dirname(os.path.dirname(__file__)),
    )
    assert proc.returncode == 0, proc.stderr
    assert "usage:" in proc.stdout
    assert "UnicodeEncodeError" not in proc.stderr

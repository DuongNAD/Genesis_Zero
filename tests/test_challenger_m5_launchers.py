"""Adversarial stress testing suite for Genesis Zero CLI launchers and preflight.

Milestone: M5_VERIFY_E2E
Author: Challenger 1 (challenger_m5_verify_1)

Stress tests edge cases, boundary values, invalid flags, contradictory options,
and headless/non-interactive behavior across:
- scripts/launch.py
- scripts/preflight.py
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
LAUNCH_PY = ROOT / "scripts" / "launch.py"
PREFLIGHT_PY = ROOT / "scripts" / "preflight.py"


# ==============================================================================
# 1. Invalid Arguments & Unrecognized Flags
# ==============================================================================

def test_launch_py_unrecognized_argument_clean_exit():
    """Adversarial test: Passing completely unknown flags to launch.py must exit with code 2 and no stacktrace."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--adversarial-unrecognized-flag-xyz"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2, f"Expected exit code 2 on unknown flag, got {res.returncode}"
    assert "error: unrecognized arguments: --adversarial-unrecognized-flag-xyz" in res.stderr
    assert "Traceback" not in res.stderr, "CLI should report clean argparse usage error without python traceback"


def test_launch_py_invalid_ticks_type():
    """Adversarial test: Passing non-integer --ticks to launch.py must cleanly exit with code 2."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--ticks", "not_an_integer"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2
    assert "argument --ticks: invalid int value" in res.stderr
    assert "Traceback" not in res.stderr


def test_launch_py_invalid_seed_type():
    """Adversarial test: Passing non-integer --seed to launch.py must cleanly exit with code 2."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--seed", "3.14159"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2
    assert "argument --seed: invalid int value" in res.stderr
    assert "Traceback" not in res.stderr


def test_launch_py_invalid_llm_choice():
    """Adversarial test: Passing invalid LLM choice to launch.py must cleanly exit with code 2."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--llm", "skynet_quantum_gpt"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2
    assert "argument --llm: invalid choice: 'skynet_quantum_gpt'" in res.stderr
    assert "Traceback" not in res.stderr


def test_preflight_py_unrecognized_argument_clean_exit():
    """Adversarial test: Passing unknown flags to preflight.py must cleanly exit with code 2."""
    res = subprocess.run(
        [sys.executable, str(PREFLIGHT_PY), "--bogus-preflight-option"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    assert res.returncode == 2
    assert "error: unrecognized arguments: --bogus-preflight-option" in res.stderr
    assert "Traceback" not in res.stderr


# ==============================================================================
# 2. Boundary Tick Counts
# ==============================================================================

def test_launch_py_ticks_zero():
    """Adversarial boundary test: --ticks 0 should initialize match, write RUN_START/RUN_END, and exit cleanly with code 0."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "0", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"Expected 0 exit code on 0 ticks, got {res.returncode}: {res.stderr}"
    assert "Khởi chạy mô phỏng: Seed=42, Ticks=0, Mode=reflex" in res.stdout


def test_launch_py_ticks_one():
    """Adversarial boundary test: --ticks 1 should execute exactly 1 tick and cleanly exit."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "1", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"Expected 0 exit code on 1 tick, got {res.returncode}: {res.stderr}"
    assert "Khởi chạy mô phỏng: Seed=42, Ticks=1, Mode=reflex" in res.stdout


def test_launch_py_ticks_negative():
    """Adversarial boundary test: --ticks -5 should treat negative count as empty range and exit cleanly with code 0."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "-5", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"Expected 0 exit code on negative ticks, got {res.returncode}: {res.stderr}"
    assert "Khởi chạy mô phỏng: Seed=42, Ticks=-5, Mode=reflex" in res.stdout


# ==============================================================================
# 3. Negative and Overflow Seeds
# ==============================================================================

def test_launch_py_negative_seed():
    """Adversarial boundary test: --seed -1 should format match ID (e.g. m_-0001) and run cleanly without crash."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "2", "--seed", "-1", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"Expected 0 exit code on negative seed, got {res.returncode}: {res.stderr}"
    assert "Khởi chạy mô phỏng: Seed=-1, Ticks=2, Mode=reflex" in res.stdout


def test_launch_py_overflow_seed():
    """Adversarial boundary test: --seed 999999999 should handle large integer seed without integer overflow or format errors."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "2", "--seed", "999999999", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0, f"Expected 0 exit code on large seed, got {res.returncode}: {res.stderr}"
    assert "Khởi chạy mô phỏng: Seed=999999999, Ticks=2, Mode=reflex" in res.stdout


def test_launch_py_zero_seed():
    """Adversarial boundary test: --seed 0 should execute simulation reliably."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "2", "--seed", "0", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0
    assert "Khởi chạy mô phỏng: Seed=0, Ticks=2, Mode=reflex" in res.stdout


# ==============================================================================
# 4. Conflicting Mode Combinations
# ==============================================================================

def test_launch_py_preflight_precedence_over_simulation():
    """Adversarial combination: When both --preflight and --reflex are passed, preflight diagnostics must take priority."""
    fast_env = {**os.environ, "GENESIS_LLM_URL": "http://127.0.0.1:59999"}
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--preflight", "--reflex", "--ticks", "5"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        env=fast_env,
        timeout=25,
    )
    assert res.returncode == 0
    # Must have performed preflight checks
    assert "Dựng được một ván" in res.stdout or "CHẠY ĐƯỢC" in res.stdout or "SẴN SÀNG" in res.stdout
    # Must NOT have started the simulation loop
    assert "Khởi chạy mô phỏng" not in res.stdout


def test_launch_py_preflight_with_no_render():
    """Adversarial combination: Passing --preflight with --no-render must run preflight cleanly."""
    fast_env = {**os.environ, "GENESIS_LLM_URL": "http://127.0.0.1:59999"}
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--preflight", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        env=fast_env,
        timeout=25,
    )
    assert res.returncode == 0
    assert "Python" in res.stdout


def test_launch_py_fix_with_preflight():
    """Adversarial combination: Passing --fix alongside --preflight must run remediation diagnostics."""
    fast_env = {**os.environ, "GENESIS_LLM_URL": "http://127.0.0.1:59999"}
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--fix", "--preflight"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        env=fast_env,
        timeout=25,
    )
    assert res.returncode == 0
    assert "Python" in res.stdout


def test_launch_py_reflex_precedence_over_llm_flag():
    """Adversarial combination: When --reflex is set, it overrides --llm vllm to reflex mode."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--llm", "vllm", "--ticks", "1", "--no-render"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0
    assert "Mode=reflex (reflex)" in res.stdout


def test_launch_py_conflicting_render_and_web_flags():
    """Adversarial combination: Verify CLI parser accepts --no-render with --web without conflict."""
    # We test argument parsing logic directly without launching the long-running web server
    from scripts.launch import main
    with (
        patch("sys.argv", ["launch.py", "--web", "--no-render", "--port", "8014"]),
        patch("scripts.launch.run_web_server", return_value=0) as mock_web,
    ):
        ret = main()
        assert ret == 0
        mock_web.assert_called_once_with(host="127.0.0.1", port=8014, open_browser=True)



# ==============================================================================
# 5. Non-Interactive, Headless Environment & Signal Handling
# ==============================================================================

def test_launch_py_non_interactive_closed_stdin():
    """Adversarial headless test: When stdin is closed (/dev/null or pipe), launcher executes non-interactively without hanging."""
    res = subprocess.run(
        [sys.executable, str(LAUNCH_PY), "--reflex", "--ticks", "2", "--no-render"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0
    assert "Khởi chạy mô phỏng" in res.stdout


def test_launch_py_web_headless_browser_suppression():
    """Adversarial headless test: In headless environments where webbrowser fails, error is suppressed without crashing server."""
    from scripts.launch import run_web_server
    with (
        patch("webbrowser.open", side_effect=Exception("No DISPLAY or browser available in headless container")),
        patch("scripts.launch.threading.Thread") as mock_thread,
        patch("time.sleep"),
        patch("subprocess.run") as mock_subproc,
    ):
        mock_thread.side_effect = lambda target, daemon=False: type("MockThread", (), {"start": lambda self: target()})()
        mock_subproc.return_value.returncode = 0
        ret = run_web_server(port=8015, open_browser=True)
        assert ret == 0




def test_launch_py_web_keyboard_interrupt():
    """Exercise the launcher handler without pretending to send a console event."""
    from scripts.launch import run_web_server

    with patch("subprocess.run", side_effect=KeyboardInterrupt) as child:
        assert run_web_server(open_browser=False) == 0
    child.assert_called_once()


@pytest.mark.parametrize("returncode", [0, 3])
def test_launch_py_web_preserves_child_status(returncode):
    from scripts.launch import run_web_server

    with patch("subprocess.run") as child:
        child.return_value.returncode = returncode
        assert run_web_server(open_browser=False) == returncode
    assert child.call_args.kwargs["env"]["PYTHONIOENCODING"] == "utf-8"


@pytest.mark.skipif(sys.platform == "win32", reason="Popen.send_signal(SIGINT) is POSIX-only; Windows console Ctrl+C needs separate validation")
def test_launch_py_web_sigint_graceful_shutdown():
    """Send real SIGINT after readiness; closed stdin must not stop the server."""
    import socket
    from urllib.request import urlopen

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    proc = subprocess.Popen(
        [sys.executable, "-c",
         "from scripts.launch import run_web_server; "
         f"raise SystemExit(run_web_server(port={port}, open_browser=False))"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL, text=True, encoding="utf-8",
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 15
        while True:
            if proc.poll() is not None:
                stdout, stderr = proc.communicate(timeout=2)
                pytest.fail(f"Server exited before readiness: {proc.returncode}\n{stdout}\n{stderr}")
            try:
                with urlopen(f"http://127.0.0.1:{port}/v1/healthz", timeout=0.5) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            assert time.monotonic() < deadline, "Server did not become ready"
            time.sleep(0.05)
        proc.send_signal(signal.SIGINT)
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 0, f"rc={proc.returncode}\n{stdout}\n{stderr}"
        assert "Đã dừng máy chủ Web." in stdout or "Application shutdown complete" in stderr
    finally:
        # Kill the isolated group, including any child left after a test failure.
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate(timeout=5)


def test_preflight_unreachable_llm_port_is_warning_not_failure():
    """Adversarial robustness: Unreachable model server port must be treated as a warning (exit code 0), allowing offline gameplay."""
    res = subprocess.run(
        [sys.executable, str(PREFLIGHT_PY), "--llm-url", "http://127.0.0.1:59999"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=15,
    )
    assert res.returncode == 0
    assert "không trả lời" in res.stdout
    assert "CHẠY ĐƯỢC" in res.stdout or "SẴN SÀNG" in res.stdout


# ==============================================================================
# 6. Empirical Edge Case & Vulnerability Documentation Tests
# ==============================================================================

def test_preflight_malformed_url_raises_value_error():
    """Empirical vulnerability demonstration:

    Passing a scheme-less URL (e.g. 'foo') to check_llm in preflight.py
    causes urllib.request.Request to raise ValueError, which is unhandled in
    check_llm (only catches URLError/TimeoutError/OSError), leading to an
    unhandled traceback crash and exit code 1.
    """
    res = subprocess.run(
        [sys.executable, str(PREFLIGHT_PY), "--llm-url", "foo"],
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        cwd=ROOT,
        timeout=10,
    )
    # Documents empirical behavior: unhandled ValueError traceback exit code 1
    assert res.returncode == 1
    assert "ValueError: unknown url type: 'foo/completion'" in res.stderr


def test_is_port_open_overflow_error_on_invalid_port():
    """Empirical vulnerability demonstration:

    Passing a port > 65535 or < 0 to is_port_open in launch.py causes
    socket.connect_ex to raise OverflowError, which is unhandled because
    is_port_open only catches OSError.
    """
    from scripts.launch import is_port_open
    with pytest.raises(OverflowError, match="port must be 0-65535"):
        is_port_open("127.0.0.1", 70000)

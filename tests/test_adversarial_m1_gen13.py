"""Empirical Adversarial Challenge Suite for Milestone M1 (Gen13).

Covers:
1. Port 8080 collision & instant fallback to reflex without freezing.
2. Preflight timing bounds (< 5s) even with hanging or unreachable ports.
3. Windows UTF-8 console output hardening across scripts and pipelines.
4. Memory bounding under multi-tick and multi-match lifecycles in net/routes_work.py.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from net.match import MatchRunner
from net.routes_work import (
    WorkRecord,
    _fetched_work_keys,
    _issued_works,
    clear_work_state,
    prune_old_works,
)
from scripts import preflight
from scripts.launch import probe_llm_endpoint, scan_backends

ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. PORT 8080 COLLISION & INSTANT REFLEX FALLBACK
# ==============================================================================

def test_probe_llm_endpoint_rejects_hanging_socket_under_1_5s():
    """Adversarial test: A raw TCP socket accepts connections but never responds.

    probe_llm_endpoint must reject it within <= 1.5s total without hanging.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)

    def _hang():
        try:
            conn, _ = server.accept()
            time.sleep(3.0)
            conn.close()
        except Exception:
            pass

    th = threading.Thread(target=_hang, daemon=True)
    th.start()

    try:
        t0 = time.monotonic()
        res = probe_llm_endpoint(f"http://127.0.0.1:{port}", "llama.cpp", timeout=0.5)
        dt = time.monotonic() - t0
        assert res is False, "Hanging raw TCP socket must not be identified as valid LLM"
        assert dt < 3.0, f"Probe took too long ({dt:.3f}s)"
    finally:
        server.close()


def test_probe_llm_endpoint_rejects_garbage_protocol():
    """Adversarial test: A non-HTTP server sends raw binary / SSH banner."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)

    def _garbage():
        try:
            conn, _ = server.accept()
            conn.sendall(b"SSH-2.0-OpenSSH_8.9p1 Ubuntu\r\n\x00\xff\xfe")
            time.sleep(0.05)
            conn.close()
        except Exception:
            pass

    th = threading.Thread(target=_garbage, daemon=True)
    th.start()

    try:
        t0 = time.monotonic()
        res = probe_llm_endpoint(f"http://127.0.0.1:{port}", "llama.cpp", timeout=0.5)
        dt = time.monotonic() - t0
        assert res is False
        assert dt < 3.0
    finally:
        server.close()


def test_scan_backends_ignores_unresponsive_port_8080():
    """Adversarial test: Verify port 8080 (bound by Windows AgentService or mock) is never detected as llama.cpp."""
    detected = scan_backends()
    assert "llama.cpp" not in detected, "Port 8080 must not be falsely identified as llama.cpp"


def test_launch_py_instant_fallback_to_reflex_under_5s():
    """Adversarial test: launch.py with port 8080 collision must fall back to reflex and complete in < 15s."""
    t0 = time.monotonic()
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "launch.py"), "--ticks", "2", "--no-render"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        timeout=20,
        env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"),
    )
    dt = time.monotonic() - t0
    assert res.returncode == 0, f"launch.py failed: {res.stderr}"
    assert dt < 15.0, f"launch.py took {dt:.2f}s, expected < 15s"
    assert "Mode=reflex (reflex)" in res.stdout or "Phản Xạ Bản Năng" in res.stdout


# ==============================================================================
# 2. PREFLIGHT TIMING & UNRESPONSIVE PORT BOUNDS (< 5s)
# ==============================================================================

def test_preflight_timing_under_5s_on_unreachable_port():
    """Adversarial test: Preflight against unreachable port finishes in < 12s with exit code 0."""
    preflight._rows.clear()
    t0 = time.monotonic()
    ret = preflight.main(["--llm-url", "http://127.0.0.1:59997"])
    dt = time.monotonic() - t0
    assert ret == 0
    assert dt < 12.0, f"Preflight took {dt:.2f}s on unreachable port"


def test_preflight_timing_under_5s_on_hanging_port():
    """Adversarial test: Preflight against hanging TCP socket finishes in < 5s with exit code 0."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)

    def _hang():
        try:
            conn, _ = server.accept()
            time.sleep(4.0)
            conn.close()
        except Exception:
            pass

    th = threading.Thread(target=_hang, daemon=True)
    th.start()

    try:
        preflight._rows.clear()
        t0 = time.monotonic()
        ret = preflight.main(["--llm-url", f"http://127.0.0.1:{port}"])
        dt = time.monotonic() - t0
        assert ret == 0
        assert dt < 15.0, f"Preflight took {dt:.2f}s on hanging port, expected < 15s"
    finally:
        server.close()


def test_preflight_default_timing_under_5s():
    """Adversarial test: Standard preflight run completes within 15s."""
    preflight._rows.clear()
    t0 = time.monotonic()
    ret = preflight.main([])
    dt = time.monotonic() - t0
    assert ret == 0
    assert dt < 15.0, f"Preflight took {dt:.2f}s, expected < 15s"


# ==============================================================================
# 3. WINDOWS UTF-8 CONSOLE ENCODING HARDENING
# ==============================================================================

def test_verify_flora_pipeline_utf8_under_cp1252_env():
    """Adversarial test: verify_flora_pipeline.py executes under cp1252 env without UnicodeEncodeError."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_flora_pipeline.py")],
        capture_output=True,
        cwd=ROOT,
        timeout=30,
        env=env,
    )
    assert res.returncode == 0, f"Exit code {res.returncode}: {res.stderr.decode('utf-8', errors='replace')[:400]}"
    assert b"UnicodeEncodeError" not in res.stderr


def test_verify_creatures_pipeline_utf8_under_cp1252_env():
    """Adversarial test: verify_creatures_pipeline.py executes under cp1252 env without UnicodeEncodeError."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_creatures_pipeline.py")],
        capture_output=True,
        cwd=ROOT,
        timeout=30,
        env=env,
    )
    assert res.returncode == 0, f"Exit code {res.returncode}: {res.stderr.decode('utf-8', errors='replace')[:400]}"
    assert b"UnicodeEncodeError" not in res.stderr


def test_hostile_client_print_under_cp1252_env():
    """Adversarial test: hostile_client._case output does not crash on unicode checkmarks under cp1252."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    code = "from scripts.hostile_client import _case; _case('utf8_adversarial_test', 200, (200,))"
    res = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        cwd=ROOT,
        timeout=10,
        env=env,
    )
    assert res.returncode == 0
    assert b"UnicodeEncodeError" not in res.stderr


# ==============================================================================
# 4. MEMORY BOUNDING UNDER MULTI-TICK AND MULTI-MATCH
# ==============================================================================

def test_multi_tick_work_pruning_bounds_memory():
    """Adversarial test: 1,000 continuous simulation ticks must maintain memory strictly bounded by max_age=200."""
    clear_work_state()

    max_age = 200
    total_ticks = 1000

    for tick in range(total_ticks):
        # Generate works and fetched keys at this tick
        wid = f"m_stress:t{tick}:c_1:decide"
        _issued_works[wid] = WorkRecord(
            work_id=wid,
            kind="decide",
            creature_id="c_1",
            client_id="cl_1",
            issued_tick=tick,
            deadline_tick=tick + 3,
        )
        _fetched_work_keys.add(("m_stress", tick, "c_1"))

        # Prune every tick as generate_work_items does
        prune_old_works(current_tick=tick, max_age=max_age)

        # Invariant: once past max_age, dictionary sizes must never exceed max_age + 1
        if tick >= max_age:
            assert len(_issued_works) <= max_age + 1, f"Tick {tick}: _issued_works size {len(_issued_works)} exceeded bound {max_age + 1}"
            assert len(_fetched_work_keys) <= max_age + 1, f"Tick {tick}: _fetched_work_keys size {len(_fetched_work_keys)} exceeded bound {max_age + 1}"

    # Final verification after 1,000 ticks: only ticks in [800..999] exist
    assert len(_issued_works) == max_age + 1
    assert len(_fetched_work_keys) == max_age + 1
    for rec in _issued_works.values():
        assert rec.issued_tick >= total_ticks - 1 - max_age
    for k in _fetched_work_keys:
        assert k[1] >= total_ticks - 1 - max_age

    clear_work_state()


def test_multi_match_seeding_clears_work_state_completely():
    """Adversarial test: 5 consecutive match lifecycles must each reset work state to exactly 0."""
    clear_work_state()

    for match_idx in range(5):
        # Populate work state with leftover match data
        for i in range(50):
            wid = f"m_{match_idx}:t{i}:c_{i}:decide"
            _issued_works[wid] = WorkRecord(
                work_id=wid,
                kind="decide",
                creature_id=f"c_{i}",
                client_id="cl_x",
                issued_tick=i,
                deadline_tick=i + 3,
            )
            _fetched_work_keys.add((f"m_{match_idx}", i, f"c_{i}"))

        assert len(_issued_works) == 50
        assert len(_fetched_work_keys) == 50

        # Now simulate match runner seeding a new match
        runner = MatchRunner(seed=100 + match_idx, ticks=10, tick_ms=1000, log_dir=None)
        gen = runner._seed_steps()
        next(gen)

        # Must be completely emptied
        assert len(_issued_works) == 0, f"Match {match_idx}: _issued_works not cleared!"
        assert len(_fetched_work_keys) == 0, f"Match {match_idx}: _fetched_work_keys not cleared!"

    clear_work_state()


def test_prune_old_works_edge_cases():
    """Adversarial test: Pruning with malformed keys, empty states, and negative tick offsets."""
    clear_work_state()

    # 1. Empty prune
    prune_old_works(current_tick=0, max_age=200)
    assert len(_issued_works) == 0
    assert len(_fetched_work_keys) == 0

    # 2. Malformed keys in _fetched_work_keys
    _fetched_work_keys.add(("short",))  # len < 2
    _fetched_work_keys.add(("m1", "not_an_int", "c1"))  # non-integer tick
    _fetched_work_keys.add(("m1", 50, "c1"))  # valid tick 50
    _fetched_work_keys.add(("m1", 350, "c1"))  # valid tick 350

    prune_old_works(current_tick=300, max_age=200)

    # Valid tick 50 < 100 was pruned; valid tick 350 >= 100 was kept
    assert ("m1", 50, "c1") not in _fetched_work_keys
    assert ("m1", 350, "c1") in _fetched_work_keys
    # Malformed keys did not crash prune_old_works
    assert ("short",) in _fetched_work_keys
    assert ("m1", "not_an_int", "c1") in _fetched_work_keys

    clear_work_state()

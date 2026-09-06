"""Empirical Adversarial Stress & Boundary Testing Suite for Milestone M3_TELEMETRY.

Challenger 1 Verification Suite:
1. High-concurrency backlog stress: 20 concurrent WebSocket clients with diverse backlog sizes (10, 100, 500, 1000)
2. Boundary fuzzing on `backlog_size`: 0, negative values, >2000, non-integers, floats, boolean, nan/inf, SQLi, XSS
3. Boundary testing on REST history endpoint: 0, negative, >2000, non-integers
4. Late-joining frame order, terrain preservation, and shallow copy immutability
5. Late-joining in REVEAL and LOBBY phases
6. Slow consumer backpressure and QueueFull safety
7. Rapid connection/disconnection churn during active simulation stepping
8. Concurrent REST history and streaming WebSocket clients
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from typing import Any

import pytest
import uvicorn
import websockets
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from net import routes_spectate, server, state
from net.match import MatchRunner, Phase


def get_ephemeral_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def clean_runner(monkeypatch):
    r = MatchRunner(seed=42, ticks=1000, tick_ms=1, log_dir=None)
    r.stopped = True
    monkeypatch.setattr(state, "runner", r)
    return r


# ---------------------------------------------------------------------------
# 1. Boundary Fuzzing on backlog_size
# ---------------------------------------------------------------------------


def test_backlog_size_boundary_fuzzing(clean_runner):
    """Fuzz backlog_size with negative, zero, overflow, floats, malformed strings, and injection payloads."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    r.step()

    fuzz_cases = [
        0,
        -1,
        -50,
        -99999,
        2001,
        2500,
        99999,
        10**12,
        "abc",
        "xyz",
        "None",
        "",
        " ",
        "1.5",
        "0.0",
        "2000.1",
        "true",
        "false",
        "nan",
        "inf",
        "-inf",
        "%00",
        ";DROP TABLE",
        "<script>alert(1)</script>",
        "🔥",
    ]

    c = TestClient(server.app)
    for val in fuzz_cases:
        url = f"/v1/spectate?backlog_size={val}"
        with pytest.raises(WebSocketDisconnect) as exc_info, c.websocket_connect(url):
            pass
        # Starlette/FastAPI rejects invalid query params with close code 1008 (Policy Violation)
        assert exc_info.value.code in (1003, 1008), f"Expected 1003/1008 for {val!r}, got {exc_info.value.code}"

    # Server must remain completely healthy with 0 subscribers leaked
    assert len(r.subscribers) == 0


def test_backlog_size_valid_boundaries(clean_runner):
    """Verify lower bound (1), upper bound (2000), and default (1000) acceptances."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    for _ in range(50):
        r.step()

    c = TestClient(server.app)

    # backlog_size = 1 (exact lower bound)
    with c.websocket_connect("/v1/spectate?backlog_size=1") as ws:
        frame = ws.receive_json()
        assert frame["t"] == 49
        assert frame.get("terrain") is not None

    # backlog_size = 2000 (exact upper bound)
    with c.websocket_connect("/v1/spectate?backlog_size=2000") as ws:
        frames = [ws.receive_json() for _ in range(50)]
        assert len(frames) == 50
        assert frames[0]["t"] == 0
        assert frames[-1]["t"] == 49

    # default backlog_size (omitted -> 1000)
    with c.websocket_connect("/v1/spectate") as ws:
        frames = [ws.receive_json() for _ in range(50)]
        assert len(frames) == 50
        assert frames[0]["t"] == 0

    assert len(r.subscribers) == 0


# ---------------------------------------------------------------------------
# 2. Boundary Testing on REST History Endpoint
# ---------------------------------------------------------------------------


def test_spectate_history_boundaries_and_fuzzing(clean_runner):
    """Verify boundaries and input validation for GET /v1/spectate/history."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    for _ in range(30):
        r.step()

    c = TestClient(server.app)

    # max_frames <= 0 returns empty list
    for non_pos in (0, -1, -50):
        resp = c.get(f"/v1/spectate/history?max_frames={non_pos}")
        assert resp.status_code == 200
        assert resp.json()["frames"] == []

    # Valid positive boundaries
    resp1 = c.get("/v1/spectate/history?max_frames=1")
    assert resp1.status_code == 200
    assert len(resp1.json()["frames"]) == 1
    assert resp1.json()["frames"][0]["t"] == 29

    resp2000 = c.get("/v1/spectate/history?max_frames=2000")
    assert resp2000.status_code == 200
    assert len(resp2000.json()["frames"]) == 30

    # Overflows and invalid inputs must return 422 Unprocessable Entity
    invalid_cases = [2001, 5000, 99999, "abc", "10.5", "nan", "inf", ";DROP"]
    for inv in invalid_cases:
        resp = c.get(f"/v1/spectate/history?max_frames={inv}")
        assert resp.status_code == 422, f"Expected 422 for max_frames={inv!r}, got {resp.status_code}"


# ---------------------------------------------------------------------------
# 3. Late Joiner Frame Ordering, Terrain Preservation & Immutability
# ---------------------------------------------------------------------------


def test_late_joiner_terrain_preservation_and_monotonicity(clean_runner):
    """Verify late-joining spectator gets terrain on first frame, strictly monotonic ticks, and original frames are not mutated."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(80):
        r.step()

    # In r.frames, tick 65 originally has terrain=None
    assert r.frames[65].get("terrain") is None

    c = TestClient(server.app)
    # Connect late with backlog_size = 15 (should get ticks 65 to 79)
    with c.websocket_connect("/v1/spectate?backlog_size=15") as ws:
        received = [ws.receive_json() for _ in range(15)]

        # 1. First frame MUST contain full terrain
        first_frame = received[0]
        assert first_frame["t"] == 65
        assert first_frame.get("terrain") is not None
        assert len(first_frame["terrain"]) == r.world.h

        # 2. Subsequent backlog frames MUST NOT contain terrain
        for i, f in enumerate(received[1:], start=1):
            assert f.get("terrain") is None, f"Frame index {i} unexpectedly contained terrain"

        # 3. Step runner to emit live frames
        for _ in range(5):
            r.step()

        live_frames = [ws.receive_json() for _ in range(5)]
        for f in live_frames:
            assert f.get("terrain") is None

        # 4. Total tick sequence must be strictly monotonically increasing by 1
        all_frames = received + live_frames
        ticks = [f["t"] for f in all_frames]
        assert ticks == list(range(65, 85))

    # 5. Immutability check: r.frames[65] must remain terrain=None
    assert r.frames[65].get("terrain") is None


def test_late_joiner_in_reveal_phase(clean_runner):
    """Verify late-joining spectator in REVEAL phase receives revealed laws and first-frame terrain."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(50):
        r.step()

    while r.phase is not Phase.REVEAL:
        r.advance_phase()

    c = TestClient(server.app)
    with c.websocket_connect("/v1/spectate?backlog_size=20") as ws:
        frames = [ws.receive_json() for _ in range(20)]

        assert len(frames) == 20
        assert frames[0]["terrain"] is not None
        assert frames[0]["t"] == 30
        assert frames[-1]["t"] == 49

        for f in frames:
            assert f["phase"] == "REVEAL"
            for ev in f.get("events", []):
                if ev.get("k") == "LAW_FIRED":
                    # In REVEAL phase, law description is disclosed
                    assert ev.get("law") != "?"
                    assert isinstance(ev.get("law"), str)


def test_late_joiner_in_lobby_phase_empty_backlog(clean_runner):
    """Verify connecting in LOBBY phase (zero frames stepped) synthesizes initial frame cleanly."""
    r = clean_runner
    assert r.phase == Phase.LOBBY
    assert len(r.frames) == 0

    c = TestClient(server.app)
    with c.websocket_connect("/v1/spectate") as ws:
        frame = ws.receive_json()
        assert frame["t"] == 0
        assert frame["phase"] == "LOBBY"

        # Advance match to RUNNING and step tick 0
        while r.phase is not Phase.RUNNING:
            r.advance_phase()
        r.step()

        f_run = ws.receive_json()
        assert f_run["phase"] == "RUNNING"
        assert f_run["t"] == 0
        assert f_run.get("terrain") is not None


# ---------------------------------------------------------------------------
# 4. Slow Consumer Backpressure & QueueFull Safety
# ---------------------------------------------------------------------------


def test_slow_consumer_queue_full_safety(clean_runner):
    """Verify slow consumer with backlog queue capacity does not crash or block runner when queue overflows."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    q: asyncio.Queue = asyncio.Queue(maxsize=routes_spectate.QUEUE_MAX)
    r.subscribers.append(q)

    # Step 1500 times without consuming from queue (exceeding QUEUE_MAX=1000)
    for _ in range(1500):
        r.step()

    # Queue must be capped at QUEUE_MAX without raising QueueFull
    assert q.qsize() == routes_spectate.QUEUE_MAX

    # Draining yields frames up to capacity
    drained = []
    while not q.empty():
        drained.append(q.get_nowait())

    assert len(drained) == routes_spectate.QUEUE_MAX
    assert drained[0]["t"] == 0
    assert drained[-1]["t"] == routes_spectate.QUEUE_MAX - 1


# ---------------------------------------------------------------------------
# 5. High Concurrency: 20 Concurrent Clients with Diverse Backlog Sizes
# ---------------------------------------------------------------------------


def test_high_concurrency_20_clients_real_server(clean_runner):
    """Stress test 20 concurrent WebSocket clients with various backlog sizes on a live uvicorn server."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    total_pre_ticks = 100
    for _ in range(total_pre_ticks):
        r.step()

    # Enable ticking inside lifespan loop of the uvicorn thread
    r.tick_ms = 25
    r.stopped = False

    port = get_ephemeral_port()
    config = uvicorn.Config(server.app, host="127.0.0.1", port=port, log_level="error")
    srv = uvicorn.Server(config)
    srv_thread = threading.Thread(target=srv.run, daemon=True)
    srv_thread.start()
    time.sleep(0.5)

    client_specs = (
        [(i, 10, 10) for i in range(5)]
        + [(i, 50, 50) for i in range(5, 10)]
        + [(i, 100, 100) for i in range(10, 15)]
        + [(i, 200, 100) for i in range(15, 20)]  # 100 available, up to 200
    )

    async def single_client(cid: int, backlog_size: int, expected_backlog: int) -> dict[str, Any]:
        url = f"ws://127.0.0.1:{port}/v1/spectate?backlog_size={backlog_size}"
        frames = []
        async with websockets.connect(url, max_size=10 * 1024 * 1024) as ws:
            # 1. Read all backlog frames
            for _ in range(expected_backlog):
                msg = await ws.recv()
                frames.append(json.loads(msg))

            # 2. Read 5 live frames
            for _ in range(5):
                msg = await ws.recv()
                frames.append(json.loads(msg))

        # Assertions per client
        assert len(frames) == expected_backlog + 5
        # First frame must have terrain
        assert frames[0].get("terrain") is not None
        assert len(frames[0]["terrain"]) == r.world.h
        # Subsequent frames must NOT have terrain
        for f in frames[1:]:
            assert f.get("terrain") is None

        # Ticks must be strictly monotonically increasing
        ticks = [f["t"] for f in frames]
        for i in range(len(ticks) - 1):
            assert ticks[i + 1] == ticks[i] + 1

        return {"cid": cid, "count": len(frames)}

    async def run_suite():
        client_tasks = [single_client(cid, bsize, exp) for cid, bsize, exp in client_specs]
        return await asyncio.gather(*client_tasks)

    try:
        results = asyncio.run(run_suite())
        assert len(results) == 20
    finally:
        r.stopped = True
        srv.should_exit = True
        srv_thread.join(timeout=1.0)



# ---------------------------------------------------------------------------
# 6. Rapid Connection/Disconnection Churn Under Active Stepping
# ---------------------------------------------------------------------------


def test_rapid_connection_churn_during_simulation(clean_runner):
    """Verify rapid subscriber connect/disconnect cycles do not cause race conditions or list mutation errors."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    c = TestClient(server.app)

    # 30 rapid connections connecting, reading 1 frame, and disconnecting
    for i in range(30):
        r.step()
        with c.websocket_connect(f"/v1/spectate?backlog_size={(i % 10) + 1}") as ws:
            f = ws.receive_json()
            assert f["phase"] == "RUNNING"

    # Step once more to clean any lingering disconnects
    r.step()
    assert len(r.subscribers) == 0


# ---------------------------------------------------------------------------
# 7. Concurrent REST History and WebSocket Streaming
# ---------------------------------------------------------------------------


def test_concurrent_rest_history_and_websocket_clients(clean_runner):
    """Verify concurrent REST requests to /v1/spectate/history do not interfere with active WebSocket streaming."""
    r = clean_runner
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    for _ in range(40):
        r.step()

    c = TestClient(server.app)

    with c.websocket_connect("/v1/spectate?backlog_size=20") as ws:
        # WS reads its backlog
        ws_frames = [ws.receive_json() for _ in range(20)]
        assert len(ws_frames) == 20

        # Interleaved REST queries
        for limit in (5, 10, 20, 30):
            resp = c.get(f"/v1/spectate/history?max_frames={limit}")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["frames"]) == min(limit, 40)
            assert data["ticks"] == 40

        # WS receives live frame
        r.step()
        live_f = ws.receive_json()
        assert live_f["t"] == 40

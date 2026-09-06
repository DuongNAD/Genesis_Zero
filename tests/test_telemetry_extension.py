"""Kiểm thử mở rộng Telemetry, Replay Buffer và Tương thích ngược (Milestone M3_TELEMETRY).

Các bài kiểm bắt buộc:
1. Hằng số QUEUE_MAX được mở rộng lên 1000.
2. WebSocket /v1/spectate nhận backlog mặc định lên đến QUEUE_MAX khung hình và có địa hình ở khung đầu.
3. WebSocket /v1/spectate hỗ trợ tham số backlog_size tuỳ chỉnh (kẹp giữa 1 và 2000).
4. WebSocket /v1/spectate từ chối giá trị backlog_size không hợp lệ (0, 2001).
5. GET /v1/spectate/history hoạt động chính xác ở các pha LOBBY, RUNNING, REVEAL.
6. GET /v1/spectate/history hỗ trợ max_frames (mặc định 500, le=2000, 422 khi vượt quá).
7. Khung hình tuân thủ đầy đủ schema: weather (state, cycle_tick, cycle_len, progress, diurnal, modifiers).
8. Thực thể sinh vật tuân thủ đầy đủ schema thế hệ và đặc điểm: species, domain, features, gen, parent_id, lineage, d_tr, age.
9. Sự kiện công khai REPRODUCE và EXTINCTION được lọc chính xác và giữ nguyên thông tin cần thiết.
10. Không rò rỉ bất kỳ token cấm nào (FORBIDDEN_RUNNING_PATTERN) qua GET /v1/spectate/history ở pha RUNNING.
11. Không rò rỉ bất kỳ token cấm nào qua luồng WebSocket /v1/spectate ở pha RUNNING.
12. Tính tương thích ngược: tất cả các trường khung hình và sinh vật cũ vẫn nguyên vẹn kiểu dữ liệu.
"""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from net import routes_spectate, server, state
from net.match import MatchRunner, Phase

FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")


@pytest.fixture
def spectate_env(monkeypatch):
    r = MatchRunner(seed=1, ticks=100, tick_ms=1, log_dir=None)
    # stopped = True để runner.loop() của lifespan không tự động tick song song trong background
    r.stopped = True
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def test_queue_max_expanded_to_1000():
    """1. Kiểm tra hằng số QUEUE_MAX trong net/routes_spectate đã mở rộng lên 1000."""
    assert routes_spectate.QUEUE_MAX == 1000


def test_spectate_ws_default_backlog_delivery(spectate_env):
    """2. Kết nối WebSocket không query param nhận toàn bộ backlog lịch sử (lên đến 1000)."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    step_count = 60
    for _ in range(step_count):
        r.step()

    assert len(r.frames) == step_count

    with c.websocket_connect("/v1/spectate") as ws:
        received = [ws.receive_json() for _ in range(step_count)]

    assert len(received) == step_count
    # Khung đầu tiên phải có terrain được bù vào
    assert received[0].get("terrain") is not None
    assert len(received[0]["terrain"]) == r.world.h
    # Khung cuối cùng có tick khớp
    assert received[-1]["t"] == step_count - 1


def test_spectate_ws_custom_backlog_size(spectate_env):
    """3. Tham số backlog_size tuỳ chỉnh điều khiển số khung phát lại cho người xem."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(40):
        r.step()

    requested_backlog = 12
    with c.websocket_connect(f"/v1/spectate?backlog_size={requested_backlog}") as ws:
        received = [ws.receive_json() for _ in range(requested_backlog)]

    assert len(received) == requested_backlog
    # Khung đầu tiên nhận được được bù terrain
    assert received[0].get("terrain") is not None
    # Các khung tương ứng 12 khung gần nhất: ticks 28 -> 39
    ticks = [f["t"] for f in received]
    assert ticks == list(range(40 - requested_backlog, 40))


def test_spectate_ws_backlog_size_validation(spectate_env):
    """4. Kiểm tra giới hạn backlog_size (1 <= backlog_size <= 2000)."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    r.step()

    # backlog_size = 0 vi phạm ge=1
    with pytest.raises(WebSocketDisconnect), c.websocket_connect("/v1/spectate?backlog_size=0"):
        pass

    # backlog_size = 2001 vi phạm le=2000
    with pytest.raises(WebSocketDisconnect), c.websocket_connect("/v1/spectate?backlog_size=2001"):
        pass

    # Các giá trị biên hợp lệ: 1 và 2000
    with c.websocket_connect("/v1/spectate?backlog_size=1") as ws:
        f = ws.receive_json()
        assert f["t"] == 0

    with c.websocket_connect("/v1/spectate?backlog_size=2000") as ws:
        f = ws.receive_json()
        assert f["t"] == 0


def test_spectate_history_lobby_phase(spectate_env):
    """5. GET /v1/spectate/history ở pha LOBBY trả về trạng thái hợp lệ và frames rỗng."""
    c, r = spectate_env
    assert r.phase == Phase.LOBBY

    resp = c.get("/v1/spectate/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["seed"] == r.seed
    assert data["ticks"] == 0
    assert data["phase"] == "LOBBY"
    assert data["frames"] == []


def test_spectate_history_running_phase(spectate_env):
    """6. GET /v1/spectate/history ở pha RUNNING trả về danh sách khung hình đã chạy."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(35):
        r.step()

    resp = c.get("/v1/spectate/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "RUNNING"
    assert data["ticks"] == 35
    assert len(data["frames"]) == 35
    assert [f["t"] for f in data["frames"]] == list(range(35))


def test_spectate_history_max_frames_filter_and_validation(spectate_env):
    """7. GET /v1/spectate/history lọc đúng số lượng khung bằng max_frames và validate le=2000."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(50):
        r.step()

    # Yêu cầu 15 khung gần nhất
    resp = c.get("/v1/spectate/history?max_frames=15")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["frames"]) == 15
    assert [f["t"] for f in data["frames"]] == list(range(35, 50))

    # max_frames = 0 trả frames rỗng
    resp_zero = c.get("/v1/spectate/history?max_frames=0")
    assert resp_zero.status_code == 200
    assert resp_zero.json()["frames"] == []

    # max_frames > 2000 trả lỗi 422
    resp_err = c.get("/v1/spectate/history?max_frames=2001")
    assert resp_err.status_code == 422


def test_spectate_history_reveal_phase(spectate_env):
    """8. GET /v1/spectate/history ở pha REVEAL trả về khung hình với luật đã được giải mã."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(50):
        r.step()

    while r.phase is not Phase.REVEAL:
        r.advance_phase()

    resp = c.get("/v1/spectate/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "REVEAL"
    assert len(data["frames"]) == 50

    law_fired_seen = False
    for f in data["frames"]:
        assert f["phase"] == "REVEAL"
        for ev in f.get("events", []):
            if ev.get("k") == "LAW_FIRED":
                law_fired_seen = True
                assert ev.get("law") != "?", "Pha REVEAL thì trường law trong LAW_FIRED phải được giải mã"
                assert len(ev["law"]) > 0

    assert law_fired_seen, "Phải có ít nhất 1 sự kiện LAW_FIRED ở pha REVEAL"


def test_frame_schema_weather_conformance(spectate_env):
    """9. Khung hình telemetry mang đầy đủ thông tin thời tiết mở rộng."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    r.step()
    frame = r.frame(r.tick_no, [])

    assert "weather" in frame
    w = frame["weather"]
    assert isinstance(w, dict)
    for k in ("state", "cycle_tick", "cycle_len", "progress", "diurnal", "modifiers"):
        assert k in w, f"Thiếu trường weather.{k}"

    assert w["state"] in ("CLEAR", "RAIN", "SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT")
    assert isinstance(w["cycle_tick"], int) and 0 <= w["cycle_tick"] < w["cycle_len"]
    assert w["cycle_len"] == 50
    assert 0.0 <= w["progress"] <= 1.0
    assert w["diurnal"] in ("DAY", "NIGHT")

    mods = w["modifiers"]
    assert isinstance(mods, dict)
    for mk in ("move_cost_mult", "sight_penalty", "plant_mult", "algae_mult", "plant_growth_mult", "algae_growth_mult"):
        assert mk in mods, f"Thiếu trường weather.modifiers.{mk}"
    assert isinstance(mods["move_cost_mult"], (int, float))
    assert isinstance(mods["sight_penalty"], int)


def test_frame_schema_creature_lineage_conformance(spectate_env):
    """10. Sinh vật trong telemetry frame chứa đầy đủ thông tin thế hệ và dòng dõi."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    r.step()
    frame = r.frame(r.tick_no, [])

    assert "creatures" in frame
    creatures = frame["creatures"]
    assert len(creatures) > 0

    for cr in creatures:
        for field in ("species", "domain", "features", "gen", "parent_id", "lineage", "d_tr", "age"):
            assert field in cr, f"Thiếu trường creature.{field}"

        assert cr["domain"] in ("CAN", "NUOC", "TROI")
        assert isinstance(cr["features"], list)
        assert isinstance(cr["gen"], int) and cr["gen"] >= 0
        assert cr["parent_id"] is None or isinstance(cr["parent_id"], str)
        assert isinstance(cr["lineage"], str) and len(cr["lineage"]) > 0
        assert isinstance(cr["d_tr"], list) and len(cr["d_tr"]) == 6
        assert all(isinstance(v, int) for v in cr["d_tr"])
        assert isinstance(cr["age"], int) and cr["age"] >= 0


def test_frame_events_reproduce_and_extinction():
    """11. Bộ lọc _public_event truyền tải chính xác sự kiện REPRODUCE và EXTINCTION."""
    from net.match import _public_event

    # Sự kiện REPRODUCE
    reproduce_ev = {
        "kind": "REPRODUCE",
        "creature_id": "L1:0",
        "child": "L1:1",
        "gen": 1,
        "pos": [5, 7],
    }
    pub_rep = _public_event(reproduce_ev, reveal=False, pub={})
    assert pub_rep == {
        "k": "REPRODUCE",
        "who": "L1:0",
        "child": "L1:1",
        "gen": 1,
        "pos": [5, 7],
    }

    # Sự kiện EXTINCTION
    extinction_ev = {
        "kind": "EXTINCTION",
        "creature_id": "",
        "species": "L3",
    }
    pub_ext = _public_event(extinction_ev, reveal=False, pub={})
    assert pub_ext == {
        "k": "EXTINCTION",
        "who": "",
        "species": "L3",
    }


def test_zero_forbidden_token_leak_in_history_running(spectate_env):
    """12. Đảm bảo tuyệt đối không có token luật cấm rò rỉ qua GET /v1/spectate/history ở pha RUNNING."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(50):
        r.step()

    resp = c.get("/v1/spectate/history?max_frames=100")
    assert resp.status_code == 200
    body = resp.text

    m = FORBIDDEN_RUNNING_PATTERN.search(body)
    assert not m, f"GET /v1/spectate/history rò rỉ token cấm {m.group(0)!r}: {body}"


def test_zero_forbidden_token_leak_in_websocket_stream(spectate_env):
    """13. Đảm bảo tuyệt đối không có token luật cấm rò rỉ qua WebSocket /v1/spectate ở pha RUNNING."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    for _ in range(30):
        r.step()

    with c.websocket_connect("/v1/spectate?backlog_size=30") as ws:
        for _ in range(30):
            frame = ws.receive_json()
            text = json.dumps(frame)
            m = FORBIDDEN_RUNNING_PATTERN.search(text)
            assert not m, f"WebSocket frame rò rỉ token cấm {m.group(0)!r}: {text}"


def test_backward_compatibility_legacy_clients(spectate_env):
    """14. Đảm bảo khách hàng cũ mong đợi schema chuẩn vẫn hoạt động hoàn hảo."""
    c, r = spectate_env
    while r.phase is not Phase.RUNNING:
        r.advance_phase()

    r.step()
    frame = r.frame(r.tick_no, [])

    # Các trường cấp cao truyền thống
    for top_key in ("t", "phase", "w", "h", "creatures", "plants", "corpses", "terrain_delta", "map", "events"):
        assert top_key in frame, f"Mất trường truyền thống {top_key}"

    # Các trường sinh vật truyền thống
    for cr in frame["creatures"]:
        for cr_key in ("id", "x", "y", "hp", "e", "e_max", "alive", "feral", "tr"):
            assert cr_key in cr, f"Mất trường sinh vật truyền thống {cr_key}"
        assert isinstance(cr["id"], str)
        assert isinstance(cr["x"], int)
        assert isinstance(cr["y"], int)
        assert isinstance(cr["hp"], float)
        assert isinstance(cr["e"], float)
        assert isinstance(cr["e_max"], float)
        assert isinstance(cr["alive"], bool)
        assert isinstance(cr["feral"], bool)
        assert isinstance(cr["tr"], list) and len(cr["tr"]) == 6

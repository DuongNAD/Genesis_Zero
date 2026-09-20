"""Genesis Zero — tests/test_work: kiểm thử /v1/match/brief và /v1/work (N-06)."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import net_config
from net import server, state
from net.match import MatchRunner, Phase
from net.routes_join import clear_rate_limits
from net.routes_work import clear_work_state


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limits()
    clear_work_state()
    yield
    clear_rate_limits()
    clear_work_state()


@pytest.fixture
def client(monkeypatch):
    # `ticks=5, tick_ms=1` cộng vòng lặp nền của `lifespan` là một cuộc đua có
    # thật, và nó đã đỏ NGẪU NHIÊN: cả ván dài đúng **5 mili-giây**, nên khi máy
    # bận thì ván trôi hết sang REVEAL trước lúc yêu cầu HTTP tới nơi và `/work`
    # trả `204` thay vì `200`.
    #
    # Đây là loại lỗi tệ hơn một bài đỏ hẳn: nó dạy người ta "chạy lại là được",
    # và rồi CI đỏ thật cũng bị bỏ qua.
    #
    # Không bài nào ở đây CẦN đồng hồ chạy — bài nào muốn một tick cụ thể thì tự
    # gán `r.tick_no`, bài nào muốn đổi pha thì gọi `advance_phase()`. Nên chặn
    # nhịp lại: nhịp chậm cộng `step` rỗng cho một ván đứng yên, và một bài kiểm
    # đứng yên là bài kiểm đọc được. Cùng cách đã dùng ở `tests/test_decision.py`.
    r = MatchRunner(seed=1, ticks=200, tick_ms=10_000, log_dir=None)
    monkeypatch.setattr(r, "step", lambda: None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def test_brief_wrong_phase(client):
    """Pha LOBBY và COOLDOWN -> /match/brief trả về 409."""
    c, r = client
    # Đăng ký ở LOBBY
    reg_resp = c.post("/v1/join", json={"display_name": "Kiến", "brain_tier": 2})
    assert reg_resp.status_code == 200
    token = reg_resp.json()["token"]

    assert r.phase is Phase.LOBBY
    resp = c.get("/v1/match/brief", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409

    # Chuyển tới COOLDOWN
    while r.phase is not Phase.COOLDOWN:
        r.advance_phase()
    assert r.phase is Phase.COOLDOWN
    resp = c.get("/v1/match/brief", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409


def test_brief_success_and_prompt_invariant(client):
    """Pha SEEDING/RUNNING -> /match/brief trả về 200; system_prompt giống hệt từng byte giữa các lần gọi."""
    c, r = client
    reg_resp = c.post("/v1/join", json={"display_name": "Kiến Lửa", "persona": "Đoàn kết", "brain_tier": 3})
    assert reg_resp.status_code == 200
    token = reg_resp.json()["token"]

    r.advance_phase()  # -> SEEDING
    assert r.phase is Phase.SEEDING

    resp1 = c.get("/v1/match/brief", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["match_id"] == r.match_id
    assert data1["ticks_total"] == r.ticks_total
    assert data1["tick_ms"] == r.tick_ms
    assert data1["late_tolerance"] == net_config.LATE_TOLERANCE
    assert "creatures" in data1
    assert len(data1["creatures"]) > 0

    cid, cdata = next(iter(data1["creatures"].items()))
    assert "system_prompt" in cdata
    assert "think_interval" in cdata
    assert "think_offset" in cdata
    assert "token_budget" in cdata
    assert "id_slot_hint" in cdata

    # Gọi lần 2 trong cùng ván
    resp2 = c.get("/v1/match/brief", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data1["creatures"][cid]["system_prompt"] == data2["creatures"][cid]["system_prompt"]


def test_brief_auth_required(client):
    """Không có token hoặc token sai -> 401."""
    c, r = client
    r.advance_phase()  # -> SEEDING
    resp = c.get("/v1/match/brief")
    assert resp.status_code == 401

    resp_bad = c.get("/v1/match/brief", headers={"Authorization": "Bearer token_khong_ton_tai"})
    assert resp_bad.status_code == 401


def test_work_not_running_returns_204(client):
    """Pha != RUNNING -> /work trả về 204 ngay lập tức."""
    c, r = client
    reg_resp = c.post("/v1/join", json={"display_name": "Kiến", "brain_tier": 2})
    token = reg_resp.json()["token"]

    # Ở LOBBY
    assert r.phase is Phase.LOBBY
    t0 = time.monotonic()
    resp = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"}, params={"hold_ms": 5000})
    assert resp.status_code == 204
    assert time.monotonic() - t0 < 0.5

    # Ở SEEDING
    r.advance_phase()
    assert r.phase is Phase.SEEDING
    resp = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"}, params={"hold_ms": 5000})
    assert resp.status_code == 204


def test_work_has_work_immediate(client):
    """Pha RUNNING có việc -> trả 200 ngay lập tức với đủ các trường của WorkItem."""
    c, r = client
    reg_resp = c.post("/v1/join", json={"display_name": "Kiến", "brain_tier": 3, "pop_request": 1})
    token = reg_resp.json()["token"]

    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING
    assert r.phase is Phase.RUNNING

    t0 = time.monotonic()
    resp = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"}, params={"hold_ms": 25000})
    assert resp.status_code == 200
    assert time.monotonic() - t0 < 0.5

    data = resp.json()
    assert "server_tick" in data
    assert "items" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert item["work_id"].startswith(f"{r.match_id}:t{r.tick_no}:")
    assert item["kind"] in ("decide", "codex")
    assert "creature_id" in item
    assert item["issued_tick"] == r.tick_no
    assert item["deadline_tick"] == item["issued_tick"] + net_config.LATE_TOLERANCE
    assert "user_block" in item
    assert "max_tokens" in item
    assert "json_schema" in item


def test_work_no_work_holds_then_204(client):
    """Khi không có việc, long-poll giữ trong hold_ms rồi trả về 204."""
    c, r = client
    reg_resp = c.post("/v1/join", json={"display_name": "Kiến", "brain_tier": 3, "pop_request": 1})
    token = reg_resp.json()["token"]

    # Dừng vòng đồng hồ của lifespan: nếu không, nó nhích tick GIỮA hai lần
    # poll và lần thứ hai lại có việc mới — bài này khi đó đỏ ngẫu nhiên theo
    # tải máy chứ không theo hành vi long-poll.
    r.stopped = True
    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING

    # Lấy việc lần đầu -> có việc
    resp1 = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"}, params={"hold_ms": 50})
    assert resp1.status_code == 200

    # Lấy việc lần 2 ở cùng tick -> đã phát rồi nên không còn việc mới -> giữ 50ms rồi 204
    t0 = time.monotonic()
    resp2 = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"}, params={"hold_ms": 50})
    elapsed = time.monotonic() - t0
    assert resp2.status_code == 204
    assert elapsed >= 0.04


def test_work_only_own_creatures(client):
    """Client chỉ nhận việc cho các cá thể thuộc quyền sở hữu của mình."""
    c, r = client
    reg_a = c.post("/v1/join", json={"display_name": "LoaiA", "brain_tier": 2, "pop_request": 2}).json()
    reg_b = c.post("/v1/join", json={"display_name": "LoaiB", "brain_tier": 2, "pop_request": 2}).json()

    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING

    resp_a = c.get("/v1/work", headers={"Authorization": f"Bearer {reg_a['token']}"})
    assert resp_a.status_code == 200
    for item in resp_a.json()["items"]:
        assert item["creature_id"].startswith("sp_loaia:")

    resp_b = c.get("/v1/work", headers={"Authorization": f"Bearer {reg_b['token']}"})
    assert resp_b.status_code == 200
    for item in resp_b.json()["items"]:
        assert item["creature_id"].startswith("sp_loaib:")


def test_work_auth_required(client):
    """Không có token hoặc token sai -> 401."""
    c, r = client
    r.advance_phase()
    r.advance_phase()
    resp = c.get("/v1/work")
    assert resp.status_code == 401
    resp_bad = c.get("/v1/work", headers={"Authorization": "Bearer bad"})
    assert resp_bad.status_code == 401


def test_prune_old_works():
    """Pruning removes entries older than 200 ticks from _issued_works and _fetched_work_keys."""
    from net.routes_work import WorkRecord, _fetched_work_keys, _issued_works, prune_old_works
    clear_work_state()

    _issued_works["old_work"] = WorkRecord(
        work_id="old_work", kind="decide", creature_id="c1", client_id="cl1",
        issued_tick=50, deadline_tick=53,
    )
    _issued_works["new_work"] = WorkRecord(
        work_id="new_work", kind="decide", creature_id="c1", client_id="cl1",
        issued_tick=260, deadline_tick=263,
    )
    _fetched_work_keys.add(("m1", 50, "c1"))
    _fetched_work_keys.add(("m1", 260, "c1"))

    prune_old_works(current_tick=300, max_age=200)

    assert "old_work" not in _issued_works
    assert "new_work" in _issued_works
    assert ("m1", 50, "c1") not in _fetched_work_keys
    assert ("m1", 260, "c1") in _fetched_work_keys


def test_match_seeding_clears_work_state():
    """Seeding a new match clears _issued_works and _fetched_work_keys to prevent memory accumulation."""
    from net.routes_work import WorkRecord, _fetched_work_keys, _issued_works
    clear_work_state()

    _issued_works["leak_work"] = WorkRecord(
        work_id="leak_work", kind="decide", creature_id="c1", client_id="cl1",
        issued_tick=10, deadline_tick=13,
    )
    _fetched_work_keys.add(("m1", 10, "c1"))

    runner = MatchRunner(seed=42, ticks=10, tick_ms=1000, log_dir=None)
    gen = runner._seed_steps()
    next(gen)

    assert len(_issued_works) == 0
    assert len(_fetched_work_keys) == 0

"""Genesis Zero — tests/test_decision: kiểm thử POST /v1/decision (N-07)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import net_config
from genesis.reflex import Goal
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
    # `tick_ms=1` + vòng lặp nền của `lifespan` = một cuộc đua: đồng hồ ván chạy
    # ~1000 tick/giây, nên giữa lúc `/work` phát việc và lúc `/decision` tới nơi
    # có thể trôi qua vài tick, và bài kiểm lăn ra 410 WORK_EXPIRED một cách
    # ngẫu nhiên. Không bài nào ở đây CẦN đồng hồ chạy — bài nào muốn một tick
    # cụ thể thì tự gán `r.tick_no`. Nên chặn nhịp lại: nhịp chậm cộng `step`
    # rỗng cho một ván đứng yên, và một bài kiểm đứng yên là bài kiểm đọc được.
    r = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    monkeypatch.setattr(r, "step", lambda: None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def _setup_running_work(c, r, brain_tier=3):
    """Helper: Đăng ký loài, chuyển sang RUNNING và lấy một work item."""
    reg_resp = c.post(
        "/v1/join",
        json={"display_name": "Kiến", "brain_tier": brain_tier, "pop_request": 1},
    )
    token = reg_resp.json()["token"]
    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING
    work_resp = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"})
    assert work_resp.status_code == 200
    item = work_resp.json()["items"][0]
    return token, item


def test_decision_too_large_413(client):
    """Body > BODY_MAX_BYTES (8 KB) -> 413."""
    c, r = client
    token, item = _setup_running_work(c, r)

    large_payload = {"work_id": item["work_id"], "junk": "x" * 9000}
    resp = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {token}"},
        json=large_payload,
    )
    assert resp.status_code == 413


def test_decision_unknown_work_404(client):
    """work_id không tồn tại -> 404 UNKNOWN_WORK."""
    c, r = client
    token, _ = _setup_running_work(c, r)

    resp = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": "m_99999:t100:sp_fake:0:decide",
            "tokens_used": 10,
            "payload": {"goal": "FORAGE", "ttl": 5},
        },
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "UNKNOWN_WORK"


def test_decision_not_your_creature_403(client):
    """work_id thuộc sinh vật của client khác -> 403 NOT_YOUR_CREATURE."""
    c, r = client
    # Client A
    reg_a = c.post("/v1/join", json={"display_name": "LoaiA", "brain_tier": 2}).json()
    # Client B
    reg_b = c.post("/v1/join", json={"display_name": "LoaiB", "brain_tier": 2}).json()

    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING

    work_a = c.get("/v1/work", headers={"Authorization": f"Bearer {reg_a['token']}"}).json()["items"][0]

    # Client B cố gửi quyết định cho work của Client A
    resp = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {reg_b['token']}"},
        json={
            "work_id": work_a["work_id"],
            "tokens_used": 20,
            "payload": {"goal": "FORAGE", "ttl": 5},
        },
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "NOT_YOUR_CREATURE"


def test_decision_expired_410(client):
    """server_tick > deadline_tick + LATE_TOLERANCE -> 410 WORK_EXPIRED."""
    c, r = client
    token, item = _setup_running_work(c, r)

    # Tăng tick vượt quá deadline + LATE_TOLERANCE
    r.tick_no = item["deadline_tick"] + net_config.LATE_TOLERANCE + 1

    resp = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "work_id": item["work_id"],
            "tokens_used": 20,
            "payload": {"goal": "FORAGE", "ttl": 5},
        },
    )
    assert resp.status_code == 410
    assert resp.json()["detail"] == "WORK_EXPIRED"


def test_decision_idempotent_duplicate_work_id(client):
    """Gửi lại cùng work_id -> 200 và BỎ QUA lần thứ hai (không áp dụng 2 lần)."""
    c, r = client
    token, item = _setup_running_work(c, r)

    payload = {
        "work_id": item["work_id"],
        "tokens_used": 25,
        "payload": {"goal": "FORAGE", "ttl": 6, "note": "di tim thuc an"},
    }

    resp1 = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["accepted"] is True
    assert "applied_at_tick" in data1

    # Lấy goal đã áp dụng ra khỏi queue (giả lập tick tiêu thụ)
    assert item["creature_id"] in r.decisions
    del r.decisions[item["creature_id"]]

    # Gửi lại lần 2: nhận 200 nhưng r.decisions KHÔNG bị set lại
    resp2 = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["accepted"] is True
    assert item["creature_id"] not in r.decisions


def test_decision_valid_decide_accepted(client):
    """Quyết định hợp lệ -> accepted: true, goal được đưa vào runner.decisions."""
    c, r = client
    token, item = _setup_running_work(c, r)

    payload = {
        "work_id": item["work_id"],
        "tokens_used": 30,
        "payload": {"goal": "FORAGE", "ttl": 4},
    }
    resp = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] is True
    assert data["applied_at_tick"] == r.tick_no
    assert data["latency_ticks"] == 0

    assert item["creature_id"] in r.decisions
    assert r.decisions[item["creature_id"]].goal == Goal.FORAGE
    assert r.decisions[item["creature_id"]].ttl == 4


def test_decision_semantic_fail_returns_200_false(client):
    """Quyết định không hợp lệ ngữ nghĩa -> HTTP 200 kèm accepted: false và lý do."""
    c, r = client
    token, item = _setup_running_work(c, r, brain_tier=1)

    # brain_tier=1 không được dùng goal GUARD (chỉ brain 4-5)
    payload_bad_goal = {
        "work_id": item["work_id"],
        "tokens_used": 15,
        "payload": {"goal": "GUARD", "ttl": 5},
    }
    resp = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=payload_bad_goal)
    assert resp.status_code == 200
    data = resp.json()
    assert data["accepted"] is False
    assert data["reason"] == "SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN"

    # ttl ngoài khoảng [2, 12]
    clear_work_state()
    work_resp2 = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"})
    item2 = work_resp2.json()["items"][0]
    payload_bad_ttl = {
        "work_id": item2["work_id"],
        "tokens_used": 15,
        "payload": {"goal": "FORAGE", "ttl": 99},
    }
    resp2 = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=payload_bad_ttl)
    assert resp2.status_code == 200
    assert resp2.json()["accepted"] is False
    assert resp2.json()["reason"] == "SEMANTIC_TTL_RANGE"


def test_decision_extra_hostile_fields_ignored(client):
    """Payload chứa trường thù địch (pos, hp, score, tick) -> bị bỏ qua, không chạm trạng thái."""
    c, r = client
    token, item = _setup_running_work(c, r)

    creature = next(cr for cr in r.creatures if cr.id == item["creature_id"])
    initial_pos = creature.pos
    initial_hp = creature.hp

    hostile_payload = {
        "work_id": item["work_id"],
        "tokens_used": 30,
        "tick": 999,
        "payload": {
            "goal": "FORAGE",
            "ttl": 5,
            "x": 10,
            "pos": [15, 15],
            "hp": 9999,
            "energy": 9999,
        },
    }
    resp = c.post("/v1/decision", headers={"Authorization": f"Bearer {token}"}, json=hostile_payload)
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True

    # Trạng thái của sinh vật không bị sửa đổi bởi các trường giả mạo
    assert creature.pos == initial_pos
    assert creature.hp == initial_hp


def test_decision_wrong_phase(client):
    """Pha LOBBY / SEEDING / COOLDOWN -> 409; REVEAL -> 410."""
    c, r = client
    token, item = _setup_running_work(c, r)

    r.phase = Phase.REVEAL
    resp_reveal = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"work_id": item["work_id"], "tokens_used": 10, "payload": {"goal": "FORAGE", "ttl": 4}},
    )
    assert resp_reveal.status_code == 410

    r.phase = Phase.COOLDOWN
    resp_cd = c.post(
        "/v1/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"work_id": item["work_id"], "tokens_used": 10, "payload": {"goal": "FORAGE", "ttl": 4}},
    )
    assert resp_cd.status_code == 409


def test_decision_auth_required(client):
    """Không có token hoặc token sai -> 401."""
    c, r = client
    token, item = _setup_running_work(c, r)

    resp = c.post("/v1/decision", json={"work_id": item["work_id"], "tokens_used": 10, "payload": {}})
    assert resp.status_code == 401

    resp_bad = c.post(
        "/v1/decision",
        headers={"Authorization": "Bearer bad"},
        json={"work_id": item["work_id"], "tokens_used": 10, "payload": {}},
    )
    assert resp_bad.status_code == 401

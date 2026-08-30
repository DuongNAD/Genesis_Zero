"""Genesis Zero — tests/test_join: kiểm thử endpoint /v1/join (N-05)."""

from __future__ import annotations

import random

import pytest
from fastapi.testclient import TestClient

from genesis import config
from net import server, state
from net.match import MatchRunner, Phase
from net.routes_join import allocate_traits, clear_rate_limits


@pytest.fixture(autouse=True)
def reset_limits():
    clear_rate_limits()
    yield
    clear_rate_limits()


@pytest.fixture
def client(monkeypatch):
    # Đồng hồ CHẶN LẠI. `ticks` nhỏ cộng `tick_ms=1` cộng vòng lặp nền của
    # `lifespan` là một cuộc đua: cả ván dài vài mili-giây, nên khi máy bận thì
    # nó trôi sang pha khác trước lúc yêu cầu HTTP tới nơi. Đã làm `test_work.py`
    # đỏ ngẫu nhiên (`assert 204 == 200`), và một bài đỏ ngẫu nhiên tệ hơn một
    # bài đỏ hẳn — nó dạy người ta "chạy lại là được".
    #
    # Không bài nào ở đây cần đồng hồ TỰ chạy: bài nào cần đổi pha thì gọi
    # `advance_phase()`, cần một tick cụ thể thì gán `r.tick_no`, cần quét sức
    # khoẻ thì gọi `sweep_health()`. Chặn nhịp lại thì chúng vẫn làm được hết,
    # chỉ khác là kết quả không còn phụ thuộc máy nhanh hay chậm.
    r = MatchRunner(seed=1, ticks=200, tick_ms=10_000, log_dir=None)
    monkeypatch.setattr(r, "step", lambda: None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def test_allocate_traits_all_tiers():
    """allocate_traits luôn trả về Traits có tổng bằng 12 và mỗi trait trong [0, 5]."""
    for tier in range(6):
        for seed in range(20):
            rng = random.Random(seed)
            tr = allocate_traits(tier, rng)
            assert tr.brain == tier
            values = (tr.brain, tr.attack, tr.armor, tr.speed, tr.sense, tr.stomach)
            assert sum(values) == config.TRAIT_SUM
            assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in values)

    with pytest.raises(ValueError):
        allocate_traits(-1)
    with pytest.raises(ValueError):
        allocate_traits(6)


def test_join_brain_tier_5(client):
    """brain_tier = 5 -> traits tổng 12 và các trait khác thấp."""
    c, r = client
    resp = c.post(
        "/v1/join",
        json={
            "display_name": "Kiến Lửa",
            "persona": "Sống theo đàn",
            "brain_tier": 5,
            "pop_request": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["traits"]["brain"] == 5
    assert sum(data["traits"].values()) == 12
    assert all(0 <= v <= 5 for v in data["traits"].values())
    assert data["queued"] is False
    assert data["client_id"].startswith("c_")
    assert data["token"].startswith("gz_live_")
    assert data["species_id"] == "sp_kienlua"
    assert len(data["creature_ids"]) == 3


def test_join_fake_model_allowed(client):
    """Không xác minh model_name / params_b: client khai 999B vẫn được chấp nhận."""
    c, r = client
    resp = c.post(
        "/v1/join",
        json={
            "display_name": "Khủng Long",
            "persona": "To lớn",
            "model_name": "fake-999B",
            "params_b": 999.0,
            "brain_tier": 5,
            "league": "LEAGUE_LLM",
            "pop_request": 2,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert sum(data["traits"].values()) == 12


def test_join_persona_too_long(client):
    """persona > 400 ký tự trả về 422."""
    c, r = client
    resp = c.post(
        "/v1/join",
        json={
            "display_name": "Thỏ",
            "persona": "x" * 401,
            "brain_tier": 2,
        },
    )
    assert resp.status_code == 422


def test_join_display_name_and_persona_sanitized(client):
    """display_name và persona bị strip ký tự điều khiển và newline; display_name cắt còn 24 ký tự."""
    c, r = client
    resp = c.post(
        "/v1/join",
        json={
            "display_name": "Kiến\nLửa\t\x00RấtDàiVượtQuáHaiMươiBốnKýTựNàyNọ",
            "persona": "Mô\ntả\r\ncó\nký\ttự\x00lạ",
            "brain_tier": 1,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # Kiểm tra trong runner registration
    reg = r.registrations[data["client_id"]]
    assert "\n" not in reg.display_name
    assert "\t" not in reg.display_name
    assert "\x00" not in reg.display_name
    assert len(reg.display_name) <= 24
    assert "\n" not in reg.persona
    assert "\t" not in reg.persona


def test_join_queued_when_running(client):
    """Join lúc pha RUNNING -> queued: true và ghi vào runner.queued."""
    c, r = client
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    assert r.phase is Phase.RUNNING

    resp = c.post(
        "/v1/join",
        json={
            "display_name": "Sói",
            "persona": "Đơn độc",
            "brain_tier": 3,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["queued"] is True
    assert data["client_id"] in r.queued
    assert data["client_id"] not in r.registrations


def test_join_rate_limit(client):
    """Rate limit 5 join/giờ mỗi IP -> lần thứ 6 trả về 429 kèm Retry-After."""
    c, r = client
    for i in range(5):
        resp = c.post(
            "/v1/join",
            json={"display_name": f"Loai_{i}", "brain_tier": 2},
        )
        assert resp.status_code == 200

    resp6 = c.post(
        "/v1/join",
        json={"display_name": "Loai_6", "brain_tier": 2},
    )
    assert resp6.status_code == 429
    assert "Retry-After" in resp6.headers


def test_join_invalid_brain_tier(client):
    """brain_tier ngoài 0..5 trả về 422."""
    c, r = client
    resp = c.post(
        "/v1/join",
        json={"display_name": "Cú", "brain_tier": 10},
    )
    assert resp.status_code == 422

    resp_neg = c.post(
        "/v1/join",
        json={"display_name": "Cú", "brain_tier": -1},
    )
    assert resp_neg.status_code == 422


def test_join_unique_species_id(client):
    """Khi trùng display_name, species_id tự động thêm hậu tố để duy nhất."""
    c, r = client
    resp1 = c.post("/v1/join", json={"display_name": "Ong Vò Vẽ", "brain_tier": 2})
    resp2 = c.post("/v1/join", json={"display_name": "Ong Vò Vẽ", "brain_tier": 2})
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["species_id"] != resp2.json()["species_id"]
    assert resp1.json()["species_id"] == "sp_ongvove"
    assert resp2.json()["species_id"] == "sp_ongvove_2"


def test_persona_chua_tu_vung_DSL_bi_tu_choi_o_CUA(client):
    """Persona đi thẳng vào khối B, và `_check_no_leak` **ném** khi thấy tên enum.

    Không bắt ở cửa thì một persona chứa đúng chữ "POISON" được nhận vào rồi làm
    gãy ván ở lần dựng prompt đầu tiên — DoS mở toang, và triệu chứng hiện ra
    cách nguyên nhân cả một pha ván.
    """
    c, r = client
    ok = c.post("/v1/join", json={"display_name": "K", "persona": "Sống theo đàn.",
                                  "brain_tier": 3, "pop_request": 1})
    assert ok.status_code == 200
    for bad in ("Loài ta biết POISON đến từ đâu", "ăn FRUIT_A thì chết",
                "khi HP thấp thì chạy"):
        rr = c.post("/v1/join", json={"display_name": "K", "persona": bad,
                                      "brain_tier": 3, "pop_request": 1})
        assert rr.status_code == 422, (bad, rr.status_code)
        assert "PERSONA_FORBIDDEN" in rr.json()["detail"]

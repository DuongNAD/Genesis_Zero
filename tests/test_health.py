"""Genesis Zero — tests/test_health: kiểm thử /v1/heartbeat và /v1/reclaim (N-09, N-10)."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import net_config
from net.match import MatchRunner, Phase
from net.routes_join import clear_rate_limits
from net.routes_work import clear_work_state
from net import state
import net.server as server


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limits()
    clear_work_state()
    yield
    clear_rate_limits()
    clear_work_state()


@pytest.fixture
def client(monkeypatch):
    r = MatchRunner(seed=1, ticks=10, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def test_heartbeat_hop_le_200(client):
    """Ca 1: Heartbeat hợp lệ trả 200 kèm server_tick, feral, phase."""
    c, r = client
    reg_resp = c.post(
        "/v1/join",
        json={"display_name": "Kiến Lửa", "brain_tier": 3, "pop_request": 2},
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["token"]

    hb_resp = c.post(
        "/v1/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"healthy": True, "queue_depth": 0, "model_ready": True},
    )
    assert hb_resp.status_code == 200
    data = hb_resp.json()
    assert data["ok"] is True
    assert data["server_tick"] == r.tick_no
    assert data["feral"] is False
    assert data["phase"] == str(r.phase)


def test_heartbeat_token_la_401(client):
    """Ca 2: Token không hợp lệ hoặc không có token trả về 401 BAD_TOKEN."""
    c, r = client
    # Không header
    resp1 = c.post(
        "/v1/heartbeat",
        json={"healthy": True, "queue_depth": 0, "model_ready": True},
    )
    assert resp1.status_code == 401
    assert resp1.json()["detail"] == "BAD_TOKEN"

    # Token lạ
    resp2 = c.post(
        "/v1/heartbeat",
        headers={"Authorization": "Bearer fake_token_xyz"},
        json={"healthy": True, "queue_depth": 0, "model_ready": True},
    )
    assert resp2.status_code == 401
    assert resp2.json()["detail"] == "BAD_TOKEN"


def test_heartbeat_go_co_hoang_da_khi_bo_nhip(client):
    """Ca 3: Bỏ nhịp -> sweep_health đánh dấu hoang dã -> heartbeat gỡ cờ."""
    c, r = client
    reg_resp = c.post(
        "/v1/join",
        json={"display_name": "Sói", "brain_tier": 2, "pop_request": 1},
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    client_id = reg_data["client_id"]
    token = reg_data["token"]

    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING

    # Giả lập bỏ nhịp quá limit (10s * 3 = 30s)
    reg = r.registrations[client_id]
    reg.last_heartbeat = r._clock() - 40.0
    r.sweep_health()
    assert r.is_feral(client_id) is True

    # Gửi heartbeat -> gỡ cờ hoang dã
    hb_resp = c.post(
        "/v1/heartbeat",
        headers={"Authorization": f"Bearer {token}"},
        json={"healthy": True, "queue_depth": 0, "model_ready": True},
    )
    assert hb_resp.status_code == 200
    assert hb_resp.json()["feral"] is False
    assert r.is_feral(client_id) is False


def test_reclaim_sai_token_hoac_loai_da_mat(client):
    """Ca 4: Reclaim sai token hoặc species đã bị gỡ trả 404 SPECIES_GONE."""
    c, r = client
    reg_resp = c.post(
        "/v1/join",
        json={"display_name": "Thỏ", "brain_tier": 1, "pop_request": 2},
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    client_id = reg_data["client_id"]
    token = reg_data["token"]
    old_creature_ids = list(reg_data["creature_ids"])

    r.advance_phase()  # -> SEEDING
    r.advance_phase()  # -> RUNNING

    # Đánh dấu hoang dã
    reg = r.registrations[client_id]
    reg.last_heartbeat = r._clock() - 40.0
    r.sweep_health()
    assert r.is_feral(client_id) is True

    # 1. Reclaim với client_id không tồn tại -> 404 SPECIES_GONE
    rec_resp_bad_cid = c.post(
        "/v1/reclaim",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_id": "c_unknown_999"},
    )
    assert rec_resp_bad_cid.status_code == 404
    assert rec_resp_bad_cid.json()["detail"] == "SPECIES_GONE"

    # 2. Reclaim với token không khớp -> 404 SPECIES_GONE
    # (Đăng ký một loài khác để có token hợp lệ khác)
    reg_resp2 = c.post(
        "/v1/join",
        json={"display_name": "Cáo", "brain_tier": 1, "pop_request": 1},
    )
    other_token = reg_resp2.json()["token"]
    rec_resp_wrong_token = c.post(
        "/v1/reclaim",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"client_id": client_id},
    )
    assert rec_resp_wrong_token.status_code == 404
    assert rec_resp_wrong_token.json()["detail"] == "SPECIES_GONE"

    # 3. Reclaim thành công trong hạn -> nhận lại creature_ids CŨ và gỡ cờ hoang dã
    rec_resp_ok = c.post(
        "/v1/reclaim",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_id": client_id},
    )
    assert rec_resp_ok.status_code == 200
    data = rec_resp_ok.json()
    assert data["ok"] is True
    assert data["client_id"] == client_id
    assert data["creature_ids"] == old_creature_ids
    assert r.is_feral(client_id) is False

    # 4. Quá hạn FERAL_GRACE -> loài bị gỡ -> reclaim trả về 404 SPECIES_GONE
    reg.last_heartbeat = r._clock() - 40.0
    reg.feral_since = r.tick_no
    r.tick_no += net_config.FERAL_GRACE + 1
    r.sweep_health()
    assert client_id not in r.registrations

    rec_resp_expired = c.post(
        "/v1/reclaim",
        headers={"Authorization": f"Bearer {token}"},
        json={"client_id": client_id},
    )
    assert rec_resp_expired.status_code == 404
    assert rec_resp_expired.json()["detail"] == "SPECIES_GONE"

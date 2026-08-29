"""Kiểm thử trần chống lạm dụng và client thù địch (N-11)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import net_config
import net.server as server
from net import state
from net.match import MatchRunner, Phase
from net.ratelimit import BAN_SECONDS, STRIKES_BEFORE_BAN, RateLimiter, reset
from scripts.hostile_client import run as hostile_run


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


@pytest.fixture
def env(monkeypatch):
    r = MatchRunner(seed=1, ticks=50, tick_ms=1, log_dir=None)
    monkeypatch.setattr(state, "runner", r)
    reset()
    while r.phase is not Phase.RUNNING:
        r.advance_phase()
    r.stopped = True
    with TestClient(server.app) as c:
        yield c, r
    reset()


def test_join_dem_theo_IP_khac_dem_theo_token():
    """Trộn hai thứ vào một xô thì hoặc cả ký túc xá sau NAT dùng chung hạn mức,
    hoặc kẻ chưa có token thoát khỏi mọi giới hạn."""
    from net.ratelimit import _key_for

    class Req:
        def __init__(self, tok=None):
            self.headers = {"authorization": f"Bearer {tok}"} if tok else {}
            self.client = type("C", (), {"host": "1.2.3.4"})()

    assert _key_for(Req("abc"), "join").startswith("ip:")
    assert _key_for(Req("abc"), "work") == "tok:abc"
    assert _key_for(Req(None), "work").startswith("ip:")


def test_ba_lan_429_lien_tiep_thi_khoa():
    """Một client hỏng đập cửa mãi thì ta vẫn trả tiền CPU cho mỗi lần từ chối."""
    clock = FakeClock()
    lim = RateLimiter(clock=clock)
    for _ in range(net_config.JOIN_PER_HOUR):
        assert lim.check("ip:x", "join") == 0.0
    waits = [lim.check("ip:x", "join") for _ in range(STRIKES_BEFORE_BAN)]
    assert all(w > 0 for w in waits)
    assert waits[-1] == BAN_SECONDS
    assert lim.banned("ip:x") > 0

    clock.t += BAN_SECONDS + 1
    assert lim.banned("ip:x") == 0.0, "hết hạn khoá thì không còn bị khoá"
    # Nhưng trần 5 lượt/GIỜ vẫn còn hiệu lực: khoá 10 phút hết hạn không tặng
    # lại hạn mức giờ. Hết cửa sổ một tiếng thì mới đi tiếp được.
    assert lim.check("ip:x", "join") > 0
    clock.t += 3600
    assert lim.check("ip:x", "join") == 0.0


def test_thanh_cong_xoa_chuoi_strike():
    clock = FakeClock()
    lim = RateLimiter(clock=clock)
    for _ in range(net_config.JOIN_PER_HOUR):
        lim.check("ip:y", "join")
    lim.check("ip:y", "join")            # strike 1
    clock.t += 3601                       # cửa sổ trôi qua -> lại được đi
    assert lim.check("ip:y", "join") == 0.0
    assert lim.check("ip:y", "join") == 0.0


def test_body_qua_lon_bi_chan_o_middleware(env):
    c, _ = env
    r = c.post("/v1/decision", content=b"x" * (net_config.BODY_MAX_BYTES + 10),
               headers={"Authorization": "Bearer bat-ky"})
    assert r.status_code == 413


def test_tran_giu_ket_noi_cung_luc(env):
    """Trần 'lượt/phút' KHÔNG bắt được slow-loris: kẻ tấn công gọi vài lần rồi
    **giữ** mỗi kết nối 25 giây. Tìm ra khi viết `hostile_client.py` — 200 lượt
    `/work` không kèm `hold_ms` treo hơn một tiếng đồng hồ."""
    assert net_config.MAX_CONCURRENT_HOLDS >= 1
    from net.routes_work import _holds
    _holds.clear()
    c, _ = env
    j = c.post("/v1/join", json={"display_name": "K", "brain_tier": 3, "pop_request": 1})
    token = j.json()["token"]
    _holds[token] = net_config.MAX_CONCURRENT_HOLDS
    r = c.get("/v1/work?hold_ms=1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 429 and r.json()["detail"] == "TOO_MANY_HOLDS"
    _holds.clear()


def test_client_thu_dich_khong_tim_ra_cua_nao(env):
    """Bất biến 3 của N-11: chạy bài này TRƯỚC khi phơi ra, không phải sau."""
    c, _ = env
    from net.routes_work import _holds
    _holds.clear()
    assert hostile_run("http://test", client=c) == 0

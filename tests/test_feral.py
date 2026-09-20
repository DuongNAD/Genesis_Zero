"""Kiểm thử tick không chờ ai (N-08) và rớt mạng → hoang dã (N-09).

Điện thoại sẽ ngủ, WiFi sẽ rớt. Không phải "nếu" mà là "khi nào" — nên hành vi
lúc rớt mạng là một tính năng, không phải một trường hợp lỗi.
"""

from __future__ import annotations

from typing import Any, cast

import net_config
from net.match import MatchRunner, Phase, Registration


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class MemLog:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def write(self, t: int, kind: str, **f) -> None:
        self.rows.append({"t": t, "kind": kind, **f})

    def of(self, kind: str) -> list[dict]:
        return [r for r in self.rows if r["kind"] == kind]


def _running(ticks: int = 500) -> tuple[MatchRunner, FakeClock, MemLog]:
    clock, log = FakeClock(), MemLog()
    # log_dir=None: không rải file vào runs/open, và `_seed_match` không đè log giả.
    r = MatchRunner(seed=1, ticks=ticks, tick_ms=4000, clock=clock, log_dir=None)
    r.advance_phase()
    r.advance_phase()
    r.log = cast(Any, log)
    assert r.phase is Phase.RUNNING
    return r, clock, log


def _reg(r: MatchRunner, cid: str = "c1") -> Registration:
    reg = Registration(
        client_id=cid, token="tok", species_id=f"sp_{cid}", display_name=cid,
        persona="", league="LEAGUE_LLM", brain_tier=3, pop=1,
    )
    reg.creature_ids = ["sp_c1:0", "sp_c1:1"]
    reg.last_heartbeat = r._clock()
    r.registrations[cid] = reg
    return reg


# ── N-08 ────────────────────────────────────────────────────────────────────

def test_quyet_dinh_dung_han_thi_ap():
    r, _, log = _running()
    r.tick_no = 100
    applied = []
    assert r.on_decision(99, "w1", lambda: applied.append(1)) == "applied"
    assert applied == [1]
    assert log.of("THINK_LATENCY")[0]["latency_ticks"] == 1


def test_quyet_dinh_qua_han_thi_bo():
    r, _, log = _running()
    r.tick_no = 100
    applied = []
    assert r.on_decision(90, "w2", lambda: applied.append(1)) == "dropped"
    assert applied == [], "quyết định quá hạn KHÔNG được áp"
    assert log.of("DECISION_LATE")[0]["latency_ticks"] == 10


def test_bat_bien_theo_work_id():
    """Gửi lại cùng work_id thì bỏ qua lần thứ hai, và KHÔNG phải lỗi."""
    r, _, _ = _running()
    r.tick_no = 10
    n = []
    assert r.on_decision(10, "w3", lambda: n.append(1)) == "applied"
    assert r.on_decision(10, "w3", lambda: n.append(1)) == "duplicate"
    assert n == [1]


def test_nhip_chung_khong_uu_dai_rieng():
    """Mạng chậm thì CẢ VÁN chậm lại. Nới dung sai riêng cho máy chậm là một ưu
    đãi vô hình nằm đúng trong biến số mà Q1 muốn đo."""
    r, _, log = _running()
    before = r.tick_ms
    for _ in range(20):
        r.latencies.append(net_config.LATE_TOLERANCE + 3)
    assert r.adjust_tick_rate() > before
    assert log.of("TICK_RATE"), "đổi nhịp mà không ghi log thì sau này không lần ra"

    r.latencies.clear()
    for _ in range(20):
        r.latencies.append(0)
    for _ in range(50):
        r.adjust_tick_rate()
    assert r.tick_ms == net_config.TICK_MS_MIN, "phải kẹp ở cận dưới"

    r.latencies.clear()
    for _ in range(20):
        r.latencies.append(99)
    for _ in range(50):
        r.adjust_tick_rate()
    assert r.tick_ms == net_config.TICK_MS_MAX, "phải kẹp ở cận trên"


def test_dung_dong_ho_monotonic():
    """Bẫy §3: `time.time()` nhảy theo NTP và ván sẽ đứng hình hoặc chạy vọt."""
    import inspect
    src = inspect.getsource(MatchRunner)
    assert "time.time(" not in src
    assert MatchRunner()._clock is __import__("time").monotonic


# ── N-09 ────────────────────────────────────────────────────────────────────

def test_bo_ba_nhip_thi_hoang_da_nhung_khong_bien_mat():
    """Bất biến 1: nếu mất kết nối là biến mất thì ai sắp chết cũng rút dây."""
    r, clock, log = _running()
    reg = _reg(r)
    clock.advance(net_config.HEARTBEAT_MS * net_config.HEARTBEAT_MISS / 1000.0 + 1)
    r.sweep_health()
    assert r.is_feral("c1")
    assert "c1" in r.registrations, "loài KHÔNG được biến mất khi mất kết nối"
    assert log.of("NODE_DOWN")[0]["feral"] is True


def test_quay_lai_trong_han_thi_nhan_lai_loai_cu():
    """Bất biến 3: cấp loài mới là xoá sạch dữ liệu của người ta vì lỗi WiFi."""
    r, clock, _ = _running()
    reg = _reg(r)
    ids_before = list(reg.creature_ids)
    clock.advance(60.0)
    r.sweep_health()
    assert r.is_feral("c1")

    r.tick_no += 50
    got = r.reclaim("c1", "tok")
    assert got is not None
    assert got.creature_ids == ids_before
    assert not r.is_feral("c1")
    assert r.reclaim("c1", "sai-token") is None


def test_qua_thoi_han_thi_go_loai():
    r, clock, log = _running()
    _reg(r)
    clock.advance(60.0)
    r.sweep_health()
    assert r.is_feral("c1")
    r.tick_no += net_config.FERAL_GRACE
    r.sweep_health()
    assert "c1" not in r.registrations
    assert log.of("NODE_DOWN")[-1].get("removed") is True


def test_heartbeat_go_co_hoang_da():
    r, clock, _ = _running()
    _reg(r)
    clock.advance(60.0)
    r.sweep_health()
    assert r.is_feral("c1")
    assert r.heartbeat("c1")
    assert not r.is_feral("c1")
    assert not r.heartbeat("khong-ton-tai")

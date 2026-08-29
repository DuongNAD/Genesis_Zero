"""Kiểm thử vòng đời ván và ranh giới tin cậy (N-04)."""

from __future__ import annotations

import net_config
from net.match import JOINABLE, MatchRunner, Phase, Registration


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _runner(ticks: int = 5) -> tuple[MatchRunner, FakeClock]:
    clock = FakeClock()
    return MatchRunner(seed=1, ticks=ticks, tick_ms=1, clock=clock, log_dir=None), clock


def test_vong_pha_day_du():
    r, _ = _runner()
    seen = [r.phase]
    for _ in range(5):
        r.advance_phase()
        seen.append(r.phase)
    assert seen == [
        Phase.LOBBY, Phase.SEEDING, Phase.RUNNING, Phase.REVEAL,
        Phase.COOLDOWN, Phase.LOBBY,
    ]


def test_sanh_trong_van_van_chay():
    """Bất biến 2: bắt sảnh chờ đủ người là cách nhanh nhất để dự án chết."""
    r, _ = _runner()
    assert not r.registrations
    r.advance_phase()                      # -> SEEDING, dựng thế giới
    assert r.creatures, "không có client người thật thì vẫn phải có bot"
    r.advance_phase()                      # -> RUNNING
    for _ in range(5):
        r.step()
    assert r.tick_no == 5


def test_vao_giua_van_thi_xep_hang_van_sau():
    """Bất biến 3: luật đã bị khám phá một nửa, điểm người vào muộn vô nghĩa."""
    r, _ = _runner()
    r.advance_phase(); r.advance_phase()   # -> RUNNING
    assert r.phase not in JOINABLE
    r.queued["c1"] = Registration(
        client_id="c1", token="t", species_id="sp_x", display_name="X",
        persona="", league="LEAGUE_LLM", brain_tier=3, pop=1,
    )
    assert "c1" not in r.registrations
    r.advance_phase(); r.advance_phase()   # -> REVEAL -> COOLDOWN
    assert "c1" not in r.registrations, "chưa tới sảnh mà đã vào"
    r.advance_phase()                      # -> LOBBY
    assert "c1" in r.registrations and not r.queued


def test_thoi_luong_dung_theo_dong_ho():
    r, clock = _runner()
    assert r.phase is Phase.LOBBY
    clock.advance(net_config.LOBBY_SECONDS - 0.01)
    assert r._clock() - r._phase_started < r.phase_budget()
    clock.advance(0.02)
    assert r._clock() - r._phase_started >= r.phase_budget()


def test_open_match_200_tick():
    """Bất biến 4: người lạ không chờ 27 phút."""
    assert net_config.OPEN_MATCH_TICKS == 200
    assert MatchRunner().ticks_total == 200


def test_moi_van_mot_seed_khac():
    r, _ = _runner()
    seeds = []
    for _ in range(3):
        while r.phase is not Phase.SEEDING:
            r.advance_phase()
        seeds.append(r.seed)
        r.advance_phase()
    assert len(set(seeds)) == 3, seeds

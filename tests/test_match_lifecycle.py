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


def test_moi_van_mot_de_bai_KHAC():
    """Ván sau phải là một đề bài khác — không phải "gần như luôn khác".

    Cả dự án đứng trên chỗ người chơi phải TỰ TÌM ra luật. Một ván trùng đề với
    ván trước biến điểm của nó thành điểm trí nhớ, và đó đúng là thứ
    [W-16](../docs/tasks/W-16-cam-nang.md) cấm cẩm nang làm — chép đáp án sang
    ván sau — chỉ khác là ở đây chính thế giới phát lại đề cũ.
    """
    import net_config
    from net.match import MatchRunner

    r = MatchRunner(seed=7, ticks=5, tick_ms=1, log_dir=None)
    sigs = []
    for _ in range(net_config.LAW_NOVELTY_WINDOW + 1):
        r._seed_match()
        sigs.append(r._law_signature(r._laws))

    w = net_config.LAW_NOVELTY_WINDOW
    for i, sig in enumerate(sigs):
        assert sig not in sigs[max(0, i - w + 1):i], (
            f"ván {i} trùng đề với một ván trong cửa sổ {w}")


def test_de_bai_trung_thi_boc_lai_chu_khong_treo(monkeypatch):
    """Ép trùng: nhồi sẵn chữ ký của ván sắp bốc vào cửa sổ nhớ.

    Và kiểm cả nửa kia — bốc lại phải CÓ TRẦN. Vòng lặp không giới hạn ở đây là
    server treo im lặng khi không gian luật của một bản đồ hẹp hơn cửa sổ, mà
    một ván trùng đề còn tệ ít hơn nhiều so với một ván không bao giờ bắt đầu.
    """
    import net_config
    from net.match import MatchRunner

    r = MatchRunner(seed=7, ticks=5, tick_ms=1, log_dir=None)
    r._seed_match()
    first = r._law_signature(r._laws)

    r2 = MatchRunner(seed=7, ticks=5, tick_ms=1, log_dir=None)
    r2._recent_law_sigs.append(first)
    r2._seed_match()
    assert r2._law_signature(r2._laws) != first, "phải bốc lại khi trùng đề"

    # Trần: mọi chữ ký đều "đã gặp" -> vẫn phải trả về, không treo.
    # Hạ trần xuống 2 cho bài kiểm: mỗi lần bốc lại là một lần `lawgen.generate`
    # chạy hết các cổng, và 12 lần đủ để bài này một mình dài hơn cả bộ test.
    monkeypatch.setattr(net_config, "LAW_NOVELTY_TRIES", 2)
    r3 = MatchRunner(seed=7, ticks=5, tick_ms=1, log_dir=None)
    r3._recent_law_sigs = _AlwaysIn()
    r3._seed_match()
    assert r3._laws, "hết lượt bốc lại thì CHẤP NHẬN, không treo"


class _AlwaysIn:
    """Cửa sổ nhớ giả: cái gì cũng bảo là đã gặp rồi."""

    def __contains__(self, x) -> bool:
        return True

    def append(self, x) -> None:
        pass

"""Kiểm thử chạy hàng loạt (X-01) và cổng gác `WORLD_FLAT` (X-02)."""

from __future__ import annotations

from genesis.batch import Run, run_many
from scripts.x02_gate import _welch


def test_song_song_cho_ket_qua_y_het_tuan_tu():
    """Tách tiến trình KHÔNG được đổi kết quả. Nếu đổi thì mọi số đo hàng loạt
    phụ thuộc vào số lõi của máy chạy nó."""
    jobs = [Run(seed=s, arm="STANDARD", ticks=120, laws_on=True) for s in (3, 4)]
    assert run_many(jobs, workers=1) == run_many(jobs, workers=2)


def test_flat_va_law_khac_nhau_dung_mot_bien():
    """Hai nhánh chỉ khác ở chỗ có luật ẩn hay không — cùng seed, cùng mọi thứ."""
    law = run_many([Run(seed=5, arm="STANDARD", ticks=200, laws_on=True)])
    flat = run_many([Run(seed=5, arm="STANDARD", ticks=200, laws_on=False)])
    assert [r["creature_id"] for r in law] == [r["creature_id"] for r in flat]
    assert law != flat, "có luật hay không mà ván giống hệt thì luật đang không kích hoạt"


def test_welch_dung_voi_ca_da_biet():
    """Hai nhóm khác phương sai — t gộp sẽ cho sai số chuẩn sai."""
    import math

    t, df = _welch([1.0] * 10, [2.0] * 10)
    assert math.isnan(t)  # phương sai 0 -> nan, không được ném
    a = [1.0, 2.0, 3.0, 4.0, 5.0]
    b = [3.0, 4.0, 5.0, 6.0, 7.0]
    t, df = _welch(a, b)
    assert round(t, 3) == -2.0 and round(df, 1) == 8.0


def test_duong_co_so_null_brain_khong_duoc_thuong():
    """Cổng gác X-02, tiên đoán (1): ở thế giới KHÔNG có gì để khám phá, loài
    brain cao không được thắng nhờ founder vector.

    Bài này chạy nhỏ (6 seed) chỉ để canh hồi quy — con số công bố lấy từ
    `scripts/x02_gate.py --seeds 40`. Nó đỏ khi ai đó chỉnh `config` theo hướng
    tặng không cho brain, và đó chính xác là lúc cần biết.
    """
    import statistics

    rows = run_many(
        [Run(seed=s, arm="STANDARD", ticks=400, laws_on=False) for s in range(1, 7)],
        workers=3,
    )
    by_sp: dict[str, list[float]] = {}
    for r in rows:
        by_sp.setdefault(r["species_id"], []).append(r["alive_ratio"])
    gap = statistics.fmean(by_sp["L1"]) - statistics.fmean(by_sp["L5"])
    assert gap < 0.05, (
        f"L1 (brain 4) hơn L5 (brain 0) {gap:+.3f} ở thế giới FLAT — brain đang "
        f"được thưởng mà không cần suy luận gì, xem 03 §10.1"
    )

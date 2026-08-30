"""Kiểm thử ba nhánh prior (X-03, 03 §10.2).

    prior_leak = t_discover(INVERTED) − t_discover(ALIGNED)

Tài liệu gọi đây là thứ đáng viết bài nhất của dự án. Nó chỉ đứng được nếu ánh
xạ bề mặt **thật sự đảo** — nên file này kiểm đúng chỗ đó, chứ không kiểm
`prior_leak` (cái ấy cần model thật).
"""

from __future__ import annotations

import random

import pytest

from genesis.lawgen import generate_cached
from genesis.prior import (
    DANGER_ORDER,
    NEUTRAL_SURFACES,
    fruit_valence,
    prior_surface_map,
)
from genesis.tick import build_match

SEEDS = (1, 2, 3, 4, 5, 6)


def test_nhanh_prior_luon_co_luat_an_qua():
    """Không có luật gắn BỀ MẶT với HỆ QUẢ thì prior không có chỗ bám.

    Đếm thật trên nhánh STANDARD: chỉ 3/39 seed sinh ra một luật ăn quả — 92% số
    ván không đo được `prior_leak`, và ta sẽ tưởng hiệu ứng bằng 0 trong khi thực
    ra là không có dữ liệu.
    """
    for seed in SEEDS:
        assert fruit_valence(generate_cached(seed, arm="PRIOR")), seed


def test_aligned_va_inverted_thuc_su_dao():
    for seed in SEEDS:
        laws = generate_cached(seed, arm="PRIOR")
        val = fruit_valence(laws)
        a = prior_surface_map(laws, "PRIOR_ALIGNED", random.Random(seed))
        i = prior_surface_map(laws, "PRIOR_INVERTED", random.Random(seed))
        for cls, kind in val.items():
            sa, si = a.surface_of(cls), i.surface_of(cls)
            assert sa != si, f"{seed} {cls}: hai nhánh trùng nhau"
            if kind == "harm":
                assert "đỏ" in sa, f"{seed}: quả hại ở ALIGNED phải trông nguy hiểm"
                assert "xanh" in si, f"{seed}: quả hại ở INVERTED phải trông lành"
            else:
                assert "xanh" in sa, f"{seed}: quả lành ở ALIGNED phải trông lành"
                assert "đỏ" in si


def test_neutral_khong_goi_gi():
    """Tên không màu, không hình — đó là cả điểm của nhánh này."""
    for seed in SEEDS:
        laws = generate_cached(seed, arm="PRIOR")
        sm = prior_surface_map(laws, "PRIOR_NEUTRAL", random.Random(seed))
        for surface in sm.cls_to_surface.values():
            assert surface in NEUTRAL_SURFACES
            for colour in DANGER_ORDER:
                assert colour not in surface


def test_ba_nhanh_dung_cung_bo_luat():
    """Khác nhau đúng một biến: ánh xạ bề mặt. Cấu trúc luật phải y hệt."""
    for seed in SEEDS:
        laws = generate_cached(seed, arm="PRIOR")
        for arm in ("PRIOR_ALIGNED", "PRIOR_INVERTED", "PRIOR_NEUTRAL"):
            w, _, _, _ = build_match(seed, prior_arm=arm, laws=laws)
            assert generate_cached(seed, arm="PRIOR") == laws


def test_moi_lop_co_dung_mot_be_mat():
    for seed in SEEDS:
        laws = generate_cached(seed, arm="PRIOR")
        for arm in ("PRIOR_ALIGNED", "PRIOR_INVERTED", "PRIOR_NEUTRAL", "PRIOR_FREE"):
            sm = prior_surface_map(laws, arm, random.Random(seed))
            vals = list(sm.cls_to_surface.values())
            assert len(vals) == len(set(vals)) == 4, (arm, vals)


def test_nhanh_la_thi_bao_loi():
    laws = generate_cached(1, arm="PRIOR")
    with pytest.raises(ValueError):
        prior_surface_map(laws, "PRIOR_KHONG_TON_TAI", random.Random(0))


def test_build_match_van_tat_dinh_theo_nhanh():
    laws = generate_cached(1, arm="PRIOR")
    a1 = build_match(1, prior_arm="PRIOR_ALIGNED", laws=laws)[0].surface_map
    a2 = build_match(1, prior_arm="PRIOR_ALIGNED", laws=laws)[0].surface_map
    assert a1 == a2

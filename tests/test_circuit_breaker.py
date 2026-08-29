"""Kiểm thử ngắt mạch model (B-03 §2)."""

from __future__ import annotations

from genesis.llm_client import CircuitBreaker


def test_ba_loi_lien_tiep_thi_mo():
    cb = CircuitBreaker()
    assert not cb.is_open
    cb.record(False)
    cb.record(False)
    assert not cb.is_open, "hai lỗi chưa đủ"
    cb.record(False)
    assert cb.is_open


def test_mot_thanh_cong_thi_dong_lai():
    cb = CircuitBreaker()
    for _ in range(3):
        cb.record(False)
    assert cb.is_open
    cb.record(True)
    assert not cb.is_open


def test_thanh_cong_xoa_chuoi_loi():
    """Ba lỗi RỜI RẠC không được mở mạch — bất biến nói 'liên tiếp'."""
    cb = CircuitBreaker()
    cb.record(False)
    cb.record(False)
    cb.record(True)
    cb.record(False)
    cb.record(False)
    assert not cb.is_open


def test_tu_dong_mo_lai_sau_50_tick():
    """Khi đã ngắt thì không ai gọi model nữa, nên không có lần thành công nào
    để đóng lại. Không có hạn tự mở, ngắt mạch là vĩnh viễn."""
    cb = CircuitBreaker(open_ticks=50)
    for _ in range(3):
        cb.record(False, tick_no=100)
    assert cb.is_open_at(100)
    assert cb.is_open_at(149)
    assert not cb.is_open_at(150)
    assert not cb.is_open, "hết hạn thì trạng thái phải sạch"
    # và sau khi mở lại, phải mất đủ 3 lỗi mới ngắt tiếp
    cb.record(False, tick_no=151)
    assert not cb.is_open_at(151)

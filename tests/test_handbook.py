"""Cẩm nang phương pháp, sống qua nhiều ván (W-16).

Bài kiểm quan trọng nhất ở đây không phải "nó nhớ được không" mà **"nó có nhớ
nhầm thứ không được nhớ không"**. Luật ẩn đổi mỗi ván và bề mặt bị hoán vị lại
mỗi ván; một câu như *"quả đỏ thì độc"* chép sang ván sau là sai — và nếu tình
cờ đúng thì agent ăn điểm mà không quy nạp gì, và cả phép đo mất nghĩa.
"""

from __future__ import annotations

import pytest

from genesis import law_config
from genesis.handbook import (
    MAX_CHARS, MAX_LESSONS, SEED_LESSONS, Handbook, LessonRejected, sanitize_lesson,
)


def test_bai_hoc_ve_PHUONG_PHAP_thi_nhan():
    for s in SEED_LESSONS:
        assert sanitize_lesson(s) == s


@pytest.mark.parametrize("bad, vi_sao", [
    ("quả đỏ thì độc", "bề mặt bị xáo lại mỗi ván"),
    ("Ăn quả tím dẹt lúc đêm thì mất máu", "bề mặt cụ thể"),
    ("FRUIT_A gây hại", "tên lớp"),
    ("khi EAT thì nên cẩn thận", "tên enum DSL"),
    ("law_id L0 là quan trọng nhất", "định danh nội bộ"),
    ("nhớ POISON đến từ đâu", "tên hệ quả"),
    ("", "rỗng"),
    ("x" * (MAX_CHARS + 1), "quá dài"),
])
def test_noi_dung_cua_MOT_van_thi_tu_choi(bad, vi_sao):
    """Từ chối, không lọc âm thầm: một câu bị cắt mất nửa nghĩa tệ hơn không có
    câu nào, và người viết cần biết mình vừa viết thứ không được phép."""
    with pytest.raises(LessonRejected):
        sanitize_lesson(bad)


def test_sach_voi_MOI_hoan_vi_be_mat_chu_khong_rieng_van_nay():
    """Cẩm nang sống qua nhiều ván, nên nó phải sạch với mọi hoán vị — không chỉ
    hoán vị hiện tại."""
    for colour, shape in law_config.FRUIT_SURFACES:
        with pytest.raises(LessonRejected):
            sanitize_lesson(f"nên tránh quả {colour} {shape}")
        with pytest.raises(LessonRejected):
            sanitize_lesson(f"quả {colour} là thứ đáng ngờ")


def test_khong_them_trung_y():
    hb = Handbook("L1")
    assert hb.add(SEED_LESSONS[0]) is True
    assert hb.add(SEED_LESSONS[0].upper()) is False
    assert len(hb.lessons) == 1


def test_day_thi_bo_dong_CU_NHAT():
    """Cẩm nang không bao giờ quên là cẩm nang đóng băng ở ván đầu tiên."""
    hb = Handbook("L1")
    for i in range(MAX_LESSONS + 4):
        hb.add(f"Bài học số {i} về cách thử.")
    assert len(hb.lessons) == MAX_LESSONS
    assert "số 0" not in " ".join(hb.lessons)
    assert f"số {MAX_LESSONS + 3}" in " ".join(hb.lessons)


def test_luu_va_nap_lai(tmp_path):
    hb = Handbook("L1", n_matches=3)
    for s in SEED_LESSONS:
        hb.add(s)
    hb.save(tmp_path)
    back = Handbook.load("L1", tmp_path)
    assert back.lessons == hb.lessons and back.n_matches == 3
    assert Handbook.load("KHONG_CO", tmp_path).lessons == []


def test_file_cu_co_dong_ban_thi_bo_dong_do_khong_vut_ca_so(tmp_path):
    import json

    (tmp_path / "L1.json").write_text(json.dumps({
        "species_id": "L1", "n_matches": 2,
        "lessons": ["Đổi một thứ một lúc.", "quả đỏ thì độc", "Nhớ cả lần không có gì."],
    }, ensure_ascii=False), encoding="utf-8")
    hb = Handbook.load("L1", tmp_path)
    assert len(hb.lessons) == 2
    assert not any("đỏ" in x for x in hb.lessons)


def test_cam_nang_vao_SYSTEM_va_khong_vo_prefix():
    """Cẩm nang bất biến cả ván, nên nó thuộc SYSTEM. Ở khối E thì ta trả giá
    prefill cho một thứ không bao giờ đổi."""
    from genesis.prompt import system_block
    from genesis.tick import build_match

    world, creatures, _, _ = build_match(1)
    c = creatures[0]
    hb = Handbook("L1")
    for s in SEED_LESSONS:
        hb.add(s)
    txt = hb.render()

    khong = system_block(c, "", world.surface_map)
    co = system_block(c, "", world.surface_map, handbook=txt)
    assert txt in co and txt not in khong
    assert co.startswith(khong[:200])          # cẩm nang nối vào CUỐI
    assert co == system_block(c, "", world.surface_map, handbook=txt)


def test_cam_nang_ban_van_bi_chan_o_lop_thu_hai():
    """`sanitize_lesson` chặn ở đầu vào; `_check_no_leak` là lớp thứ hai. Một
    file cẩm nang sửa bằng tay không được đi thẳng vào prompt."""
    from genesis.prompt import PromptLeak, system_block
    from genesis.tick import build_match

    world, creatures, _, _ = build_match(1)
    with pytest.raises(PromptLeak):
        system_block(creatures[0], "", world.surface_map,
                     handbook="[CẨM NANG]\n- nhớ rằng POISON là xấu")


def test_khong_co_cam_nang_thi_van_cu_chay_y_het():
    from genesis.prompt import system_block
    from genesis.tick import build_match

    world, creatures, _, _ = build_match(1)
    a = system_block(creatures[0], "x", world.surface_map)
    b = system_block(creatures[0], "x", world.surface_map, handbook="")
    assert a == b

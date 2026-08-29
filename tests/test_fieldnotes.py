"""Genesis Zero — tests cho fieldnotes (B-07)."""

from __future__ import annotations

import pytest

from genesis.fieldnotes import FieldNotes, Note, sanitize_outcome
from genesis.lawdsl import EffectKind


def test_fieldnotes_acceptance() -> None:
    """Nghiệm thu chuẩn từ yêu cầu VIỆC A."""
    fn = FieldNotes(cap=5)
    for i in range(20):
        fn.record(
            Note(
                t=i,
                who="TÔI",
                action="đi bộ",
                outcome="không thấy gì",
                ctx=(("pha", "ngày"), ("địa hình", "đồng cỏ")),
            )
        )
    fn.record(
        Note(
            t=99,
            who="TÔI",
            action="ăn quả đỏ tròn",
            outcome="mất máu nhiều",
            ctx=(("pha", "đêm"), ("địa hình", "đồng cỏ")),
        )
    )
    out = fn.render(5)
    assert "mất máu nhiều" in out, out  # A1: bằng chứng KHÔNG bị đẩy ra
    assert out.count("\n") <= 5
    assert "[pha ngày" in out or "pha ngày" in out  # A2: ngữ cảnh luôn có
    # A3: chặn tên hệ quả nội bộ
    assert "POISON" not in sanitize_outcome("nó dính POISON 5 tick")
    assert "FRUIT_A" not in sanitize_outcome("nó ăn FRUIT_A")


def test_overflow_priority_abnormal_over_normal() -> None:
    """A1: Sự kiện bất thường không bị các sự kiện bình thường đẩy ra khỏi sổ."""
    fn = FieldNotes(cap=3)
    # Ghi 10 sự kiện bình thường
    for i in range(10):
        fn.record(
            Note(
                t=i,
                who="TÔI",
                action="đi dạo",
                outcome="không thấy gì",
                ctx=(("pha", "ngày"),),
            )
        )

    # Ghi 1 sự kiện bất thường
    fn.record(
        Note(
            t=15,
            who="TÔI",
            action="uống nước",
            outcome="hồi máu nhẹ",
            ctx=(("pha", "ngày"),),
        )
    )

    # Ghi thêm 20 sự kiện bình thường
    for i in range(20, 40):
        fn.record(
            Note(
                t=i,
                who="TÔI",
                action="nghỉ ngơi",
                outcome="không thấy gì",
                ctx=(("pha", "đêm"),),
            )
        )

    rendered = fn.render(3)
    assert "hồi máu nhẹ" in rendered
    # Kết quả mới nhất render trước
    lines = rendered.split("\n")
    assert len(lines) == 3
    assert "t39" in lines[0]


def test_overflow_priority_self_over_other() -> None:
    """A1: Khi cùng bình thường, sự kiện của TÔI ưu tiên hơn THẤY."""
    fn = FieldNotes(cap=2)
    fn.record(
        Note(
            t=1,
            who="THẤY L2:0",
            action="đi bộ",
            outcome="không thấy gì",
            ctx=(("pha", "ngày"),),
        )
    )
    fn.record(
        Note(
            t=2,
            who="TÔI",
            action="đi bộ",
            outcome="không thấy gì",
            ctx=(("pha", "ngày"),),
        )
    )
    fn.record(
        Note(
            t=3,
            who="TÔI",
            action="đi bộ",
            outcome="không thấy gì",
            ctx=(("pha", "ngày"),),
        )
    )

    rendered = fn.render(2)
    assert "THẤY L2:0" not in rendered
    assert "t3 TÔI" in rendered
    assert "t2 TÔI" in rendered


def test_context_always_present() -> None:
    """A2: Ngữ cảnh luôn có mặt đầy đủ kể cả khi bình thường."""
    fn = FieldNotes(cap=2)
    fn.record(
        Note(
            t=10,
            who="TÔI",
            action="đi bộ",
            outcome="không thấy gì",
            ctx=(("pha", "ngày"), ("địa hình", "ô nước")),
        )
    )
    fn.record(
        Note(
            t=11,
            who="TÔI",
            action="đi bộ",
            outcome="không thấy gì",
            ctx={"pha": "đêm", "địa hình": "mỏm đá"},
        )
    )
    out = fn.render(2)
    assert "[pha ngày, địa hình ô nước]" in out or "pha ngày" in out
    assert "[pha đêm, địa hình mỏm đá]" in out or "pha đêm" in out


def test_sanitize_outcome_all_effect_kinds_and_fruits() -> None:
    """A3: sanitize_outcome chặn mọi tên EffectKind và FRUIT_*."""
    for eff in EffectKind:
        dirty = f"nó bị {eff.value} nặng"
        clean = sanitize_outcome(dirty)
        assert eff.value not in clean, f"Rò rỉ EffectKind: {eff.value}"

    for fruit in ["FRUIT_A", "FRUIT_B", "FRUIT_C", "FRUIT_D", "FRUIT_XYZ"]:
        dirty = f"nó hái {fruit}"
        clean = sanitize_outcome(dirty)
        assert fruit not in clean, f"Rò rỉ fruit class: {fruit}"

    clean_law = sanitize_outcome("law_id L01 bị lộ")
    assert "law_id" not in clean_law

    # Tiếng Việt quan sát được giữ nguyên
    vn_text = "nó mất máu và ngã gục"
    assert sanitize_outcome(vn_text) == vn_text


def test_note_frozen_and_render_edge_cases() -> None:
    """Kiểm tra Note là frozen và render với k <= 0 / empty."""
    note = Note(
        t=1,
        who="TÔI",
        action="nghỉ",
        outcome="không thấy gì",
        ctx=(("pha", "ngày"),),
    )
    with pytest.raises(Exception):
        note.t = 2  # type: ignore[misc]

    fn = FieldNotes(cap=5)
    assert fn.render(0) == ""
    assert fn.render(5) == ""
    assert len(fn) == 0

    fn.record(note)
    assert len(fn) == 1
    fn.clear()
    assert len(fn) == 0

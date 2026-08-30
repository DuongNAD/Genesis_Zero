"""Định dạng log là một API. Thêm trường sau = ván cũ không so được với ván mới."""

from __future__ import annotations

from pathlib import Path

import pytest

from genesis.logio import COMMON_FIELDS, EVENT_KINDS, LogWriter, read_log


def test_every_row_has_all_common_fields(tmp_path: Path) -> None:
    p = tmp_path / "a.jsonl"
    with LogWriter(p, "m_test") as log:
        log.write(1, "EAT", creature_id="L1:0", energy=12.3456789)
        log.write(2, "TICK")
    for row in read_log(p):
        for f in COMMON_FIELDS:
            assert f in row, f"thiếu {f} trong {row}"


def test_open_mode_fields_present_but_null(tmp_path: Path) -> None:
    """client_id và model_name có mặt ngay từ M0, luôn null ở Lab mode.

    Đường may thứ 5 của docs/04-THE-GIOI-MO.md §5.
    """
    p = tmp_path / "a.jsonl"
    with LogWriter(p, "m_test") as log:
        log.write(1, "EAT", creature_id="L1:0")
    row = read_log(p)[0]
    assert row["client_id"] is None and row["model_name"] is None
    assert row["match_id"] == "m_test"


def test_floats_rounded(tmp_path: Path) -> None:
    p = tmp_path / "a.jsonl"
    with LogWriter(p, "m") as log:
        log.write(1, "EAT", energy=12.3456789, nested={"a": [1.111111]})
    row = read_log(p)[0]
    assert row["energy"] == 12.3457
    assert row["nested"]["a"] == [1.1111]


def test_key_order_stable_regardless_of_insertion_order(tmp_path: Path) -> None:
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    with LogWriter(a, "m") as log:
        log.write(1, "EAT", alpha=1, zulu=2, mike=3)
    with LogWriter(b, "m") as log:
        log.write(1, "EAT", zulu=2, mike=3, alpha=1)
    assert a.read_text() == b.read_text(), "sort_keys chưa bật -> hai lần chạy sẽ diff bẩn"


def test_unknown_kind_rejected(tmp_path: Path) -> None:
    with LogWriter(tmp_path / "a.jsonl", "m") as log, pytest.raises(ValueError):
        log.write(1, "KHONG_CO_LOAI_NAY")


def test_event_kinds_cover_the_docs() -> None:
    """Các loại mà tài liệu hứa sẽ có. Thiếu = phiếu việc sau sẽ phải sửa format."""
    for k in ("LAW_FIRED", "CODEX_OP", "TEACH", "LLM_SEMANTIC_FAIL",
              "DECISION_LATE", "NODE_DOWN", "PREFIX_INVALIDATED", "ORACLE"):
        assert k in EVENT_KINDS

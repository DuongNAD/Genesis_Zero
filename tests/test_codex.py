"""Genesis Zero — tests cho codex (B-08)."""

from __future__ import annotations

import ast

from genesis import law_config as lc
from genesis.adapt import reset_body
from genesis.codex import Codex
from genesis.creature import Creature
from genesis.lawdsl import (
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
)
from genesis.traits import founder_traits


def _sample_law() -> Law:
    return Law(
        Trigger(TriggerKind.DRINK),
        (),
        Effect(EffectKind.HEAL, Mag.SMALL, Dur.SHORT),
    )


def test_codex_acceptance() -> None:
    """Nghiệm thu chuẩn từ yêu cầu VIỆC B."""
    law = _sample_law()
    cx = Codex(size=2)
    assert cx.apply("SET", 0, law, 3, tick=100).ok
    assert not cx.apply("SET", 5, law, 3, tick=200).ok  # B1 slot ngoài phạm vi
    v = cx.apply("SET", 1, law, 3, tick=105)  # B2 cooldown
    assert not v.ok and v.reason == "CODEX_COOLDOWN"
    assert cx.entries()[0] is not None and cx.entries()[1] is None
    # B4: thu nhỏ KHÔNG cắt ô đang có
    cx.resize(1)
    assert cx.entries()[0] is not None
    assert not cx.apply("SET", 1, law, 3, tick=500).ok
    # B5: reflex KHÔNG import codex
    t = ast.parse(open("genesis/reflex.py").read())
    assert not [
        n
        for n in ast.walk(t)
        if isinstance(n, ast.ImportFrom) and n.module and "codex" in n.module
    ]
    assert "codex" not in open("genesis/reflex.py").read().lower()


def test_codex_operations_set_drop_conf() -> None:
    """Kiểm tra các thao tác SET, DROP, CONF trên Codex."""
    law = _sample_law()
    cx = Codex(size=2)

    # SET hợp lệ
    v_set = cx.apply("SET", 0, law, conf=4, tick=10, source="self")
    assert v_set.ok
    entry = cx.entries()[0]
    assert entry is not None
    assert entry.law == law
    assert entry.conf == 4
    assert entry.written_at == 10
    assert entry.source == "self"

    # CONF cập nhật conf
    v_conf = cx.apply("CONF", 0, None, conf=5, tick=40)
    assert v_conf.ok
    assert cx.entries()[0] is not None
    assert cx.entries()[0].conf == 5

    # CONF trên ô trống -> lỗi
    v_conf_empty = cx.apply("CONF", 1, None, conf=3, tick=70)
    assert not v_conf_empty.ok
    assert v_conf_empty.reason == "CODEX_EMPTY_SLOT"

    # DROP xoá ô
    v_drop = cx.apply("DROP", 0, None, 0, tick=100)
    assert v_drop.ok
    assert cx.entries()[0] is None

    # SET thiếu law -> CODEX_MISSING_LAW
    v_nolaw = cx.apply("SET", 0, None, 3, tick=130)
    assert not v_nolaw.ok
    assert v_nolaw.reason == "CODEX_MISSING_LAW"

    # Thao tác lạ -> CODEX_UNKNOWN_OP
    v_unknown = cx.apply("INVALID_OP", 0, law, 3, tick=160)
    assert not v_unknown.ok
    assert v_unknown.reason == "CODEX_UNKNOWN_OP"


def test_reset_body_does_not_touch_codex() -> None:
    """B3: Chết và adapt.reset_body KHÔNG chạm vào Sổ Luật."""
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        traits=traits,
        pos=(0, 0),
        hp=100.0,
        energy=80.0,
    )
    codex = Codex(size=lc.CODEX_SIZE_BY_BRAIN[c.traits.brain])
    law = _sample_law()
    assert codex.apply("SET", 0, law, 5, tick=50).ok

    # Gọi reset_body
    reset_body(c)

    # Codex vẫn nguyên vẹn
    assert codex.entries()[0] is not None
    assert codex.entries()[0].law == law


def test_resize_expand_and_shrink() -> None:
    """B4: Mở rộng thêm ô mới, thu nhỏ giữ nguyên ô cũ."""
    cx = Codex(size=2)
    law = _sample_law()
    cx.apply("SET", 0, law, 3, tick=10)
    cx.apply("SET", 1, law, 4, tick=40)

    # Mở rộng lên 4
    cx.resize(4)
    assert len(cx.entries()) == 4
    assert cx.entries()[0] is not None
    assert cx.entries()[1] is not None
    assert cx.entries()[2] is None
    assert cx.entries()[3] is None

    # Ghi vào ô mới 2
    assert cx.apply("SET", 2, law, 5, tick=70).ok

    # Thu nhỏ về 1
    cx.resize(1)
    # Cả 3 ô đã ghi vẫn còn trong entries()
    assert cx.entries()[0] is not None
    assert cx.entries()[1] is not None
    assert cx.entries()[2] is not None

    # Nhưng không thể ghi vào slot >= 1
    v_blocked = cx.apply("SET", 1, law, 3, tick=100)
    assert not v_blocked.ok
    assert v_blocked.reason == "CODEX_BAD_SLOT"


def test_no_feedback_on_truth() -> None:
    """B2: apply không kiểm tra tính đúng sai của luật với thế giới, chỉ kiểm cú pháp."""
    fake_law = Law(
        Trigger(TriggerKind.EAT, "quả tưởng tượng"),
        (),
        Effect(EffectKind.TELEPORT, r=3),
    )
    cx = Codex(size=1)
    v = cx.apply("SET", 0, fake_law, 1, tick=0)
    assert v.ok

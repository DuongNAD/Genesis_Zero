"""Genesis Zero — schema phát qua mạng phải giống hệt đường cục bộ (N-06)."""

from __future__ import annotations

import pytest

from genesis.strategist import schema_for
from genesis.tick import build_match
from genesis.traits import founder_traits


def test_duong_mang_va_duong_cuc_bo_dung_cung_mot_schema():
    """Client qua mạng KHÔNG được chơi một trò khác client cục bộ.

    `routes_work.generate_work_items` từng dựng `schema_for(c.traits, kind)` —
    không `targets`, không `sm`. Hậu quả:

    - thiếu `targets`: `target` không enum và không bắt buộc, đúng hai lỗ đã đo
      ở B-01 (16/20 và 8/35 lời gọi trượt).
    - thiếu `sm`: enum `arg` **không chứa bề mặt nào**, nên luật về ăn quả là
      bất khả về cấu trúc — chế độ mở không phát biểu nổi luật ăn quả.
    """
    world, creatures, _, _ = build_match(55)
    c = creatures[0]
    seen = [o.id for o in creatures[1:3]]

    day_du = schema_for(c.traits, "codex", targets=seen, sm=world.surface_map)
    thieu = schema_for(c.traits, "codex")
    assert day_du != thieu, "thiếu sm mà schema không đổi -> bài test này vô nghĩa"

    def args(node):
        out = set()
        for b in node.get("oneOf", [node]):
            out |= set(b["properties"].get("arg", {}).get("enum", []))
        return out

    surfaces = set(world.surface_map.cls_to_surface.values())
    trigger = day_du["properties"]["law"]["properties"]["trigger"]
    assert surfaces <= args(trigger), "enum arg thiếu bề mặt -> không ai nói được về quả"
    assert not (surfaces & args(thieu["properties"]["law"]["properties"]["trigger"]))


def test_decide_qua_mang_co_enum_target():
    world, creatures, _, _ = build_match(55)
    c = creatures[0]
    seen = [o.id for o in creatures[1:3]]
    s = schema_for(c.traits, "decide", targets=seen, sm=world.surface_map)
    assert s["properties"]["target"]["enum"] == sorted(seen)
    assert "target" in s["required"], "thấy ai thì phải BẮT BUỘC nêu tên"


def test_routes_work_truyen_ca_hai():
    """Khoá bằng mã nguồn: gọi `schema_for` ở đường mạng phải có cả hai tham số.

    Kiểm thẳng vào nguồn vì hai đường dựng schema ở hai chỗ khác nhau — đường
    mạng theo pha, đường cục bộ theo đàn — nên không có bất biến kiểu nào bắt
    được việc chúng lệch nhau ngoài việc đọc.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "net" / "routes_work.py").read_text()
    i = src.index("js = schema_for(")
    goi = src[i:i + 200]
    assert "targets=" in goi, "đường mạng quên targets"
    assert "sm=" in goi, "đường mạng quên sm"

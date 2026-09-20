"""Tests cho genesis/reveal.py — REVEAL và diễn giải luật (L-07)."""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path
from typing import Any

from rich.table import Table

from genesis.lawdsl import (
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
)
from genesis.lawgen import generate
from genesis.reveal import build_reveal, render_reveal
from genesis.surface import SurfaceMap, roll_surface_map


def test_reveal_boundary_b4() -> None:
    """Bất biến B4: reveal.py KHÔNG import world, creature, tick."""
    reveal_path = Path("genesis/reveal.py")
    tree = ast.parse(reveal_path.read_text(encoding="utf-8"))
    bad_imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module
        and any(x in node.module for x in ("world", "creature", "tick"))
    ]
    assert not bad_imports, f"Vi phạm ranh giới reveal.py: {bad_imports}"


def test_reveal_surface_not_leaking_classes_b3() -> None:
    """Bất biến B3: Payload REVEAL dùng bề mặt quan sát, không chứa chuỗi FRUIT_."""
    sm = roll_surface_map(random.Random(42))
    # check_solvable=False: bài này kiểm RÒ TÊN LỚP, không kiểm khả giải.
    # Bật cổng lên thì 50 seed × ~2 s = 100 s và nó chiếm 90% thời gian cả bộ test.
    for seed in range(50):
        laws = generate(seed, "STANDARD", check_solvable=False)
        payload = build_reveal(laws, {}, sm)
        dumped = json.dumps(payload, ensure_ascii=False)
        assert "FRUIT_" not in dumped, f"Rò rỉ tên lớp ở seed {seed}: {dumped}"
        for l_dict in payload["laws"]:
            assert "FRUIT_" not in l_dict["vi"], l_dict["vi"]
            assert "FRUIT_" not in json.dumps(l_dict["dsl"], ensure_ascii=False)


def test_reveal_payload_schema_and_render() -> None:
    """Khớp cấu trúc JSON 05 §3.6 và render_reveal tạo Table hợp lệ."""
    sm = roll_surface_map(random.Random(1))
    laws = generate(7, "STANDARD", check_solvable=False)
    payload = build_reveal(laws, {}, sm, log_path="/tmp/m_00412.jsonl")

    assert payload["match_id"] == "m_00412"
    assert set(payload.keys()) >= {"match_id", "laws", "scores", "citations", "deception"}
    assert len(payload["laws"]) == 3

    for l_dict in payload["laws"]:
        assert set(l_dict.keys()) >= {"law_id", "tier", "dsl", "vi", "fired_count"}
        assert l_dict["tier"] in ("D1", "D2", "D3", "D4")
        assert isinstance(l_dict["vi"], str) and len(l_dict["vi"]) > 0

    table = render_reveal(payload)
    assert isinstance(table, Table)
    assert table.row_count == 3


def test_reveal_with_scores_and_discoveries() -> None:
    """Kiểm tra render_reveal khi có thông tin codex và người khám phá."""
    sm = SurfaceMap({
        "FRUIT_A": "quả đỏ tròn",
        "FRUIT_B": "quả xanh dài",
        "FRUIT_C": "quả vàng gai",
        "FRUIT_D": "quả tím dẹt",
    })
    laws = [
        Law(Trigger(TriggerKind.EAT, "FRUIT_A"), (), Effect(EffectKind.DAMAGE, Mag.MED, Dur.INSTANT)),
        Law(Trigger(TriggerKind.DRINK), (), Effect(EffectKind.ENERGY_GAIN, Mag.BIG, Dur.INSTANT)),
    ]
    codices: dict[str, list[Any]] = {
        "sp_kienlua:0": [],
        "sp_meo:1": [],
    }
    payload = build_reveal(laws, codices, sm)
    assert len(payload["scores"]) == 2

    # Giả lập điểm số khám phá
    payload["scores"][0]["per_law"][0]["match"] = 0.95
    payload["scores"][0]["per_law"][0]["t_discover"] = 88
    payload["scores"][1]["per_law"][0]["match"] = 0.85
    payload["scores"][1]["per_law"][0]["t_discover"] = 120

    table = render_reveal(payload)
    assert isinstance(table, Table)
    assert table.row_count == 2

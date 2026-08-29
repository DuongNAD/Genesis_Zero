"""Kiểm thử LLM tự chọn hướng dịch trait (B-13).

Ở v5, **hướng dịch trait ưa thích là chữ ký hành vi rõ nhất của một model** —
rõ hơn cả tỉ lệ sống, vì nó là một *lựa chọn* chứ không phải một *kết quả*. Nên
đường này phải vừa mở (LLM quyết) vừa kín (không phá được bất biến trait).
"""

from __future__ import annotations

import collections
import json
import logging

import httpx
import pytest

from genesis import config
from genesis.adapt import maybe_shift
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick
from genesis.traits import Traits

logging.disable(logging.WARNING)


def _model(frm: str, to: str, why: str = "cần chạy nhanh hơn"):
    def handler(request: httpx.Request) -> httpx.Response:
        p = json.loads(request.content)["prompt"]
        if "[DỊCH CƠ THỂ]" in p:
            out = {"from": frm, "to": to, "why": why}
        else:
            out = {"goal": "FORAGE", "ttl": 4}
        return httpx.Response(200, json={"content": json.dumps(out),
                                         "tokens_predicted": 30})
    return httpx.MockTransport(handler)


def test_tong_van_12_sau_moi_lan_dich():
    """Bất biến 1. Đường LLM vẫn phải đi qua `Traits.shift`, nên không có cửa
    nào phá được tổng 12 hay biên [0,5]."""
    world, creatures, state, rng = build_match(seed=80)
    strat = LlmStrategist("http://m", [c.id for c in creatures],
                          transport=_model("speed", "brain"))
    for t in range(400):
        tick(world, creatures, t, rng, state, strategist=strat)
        for c in creatures:
            vals = (c.traits.brain, c.traits.attack, c.traits.armor,
                    c.traits.speed, c.traits.sense, c.traits.stomach)
            assert sum(vals) == config.TRAIT_SUM
            assert all(config.TRAIT_MIN <= v <= config.TRAIT_MAX for v in vals)


def test_huong_dich_do_llm_chon():
    world, creatures, state, rng = build_match(seed=80)
    strat = LlmStrategist("http://m", [c.id for c in creatures],
                          transport=_model("speed", "brain"))
    for t in range(300):
        tick(world, creatures, t, rng, state, strategist=strat)
    pairs = collections.Counter(
        tuple(p) for c in creatures for p in c.shift_log
    )
    assert pairs, "không ai dịch trait"
    assert pairs.most_common(1)[0][0] == ("speed", "brain"), pairs


def test_dich_khong_hop_le_thi_bo_luot_khong_thu_lai():
    """Thử lại là cho con hay sai được nghĩ nhiều lần về cùng một việc — một ưu
    đãi vô hình, và nó nằm đúng trong biến số mà Q1 muốn đo."""
    world, creatures, state, rng = build_match(seed=80)
    # "khong_ton_tai" không phải tên trait -> validate_shift từ chối
    strat = LlmStrategist("http://m", [c.id for c in creatures],
                          transport=_model("khong_ton_tai", "brain"))
    for t in range(200):
        tick(world, creatures, t, rng, state, strategist=strat)
    assert strat.stats["semantic_fail"] > 0
    assert all(not c.shift_log for c in creatures), "dịch sai mà vẫn đổi cơ thể"


def test_dich_cham_bien_thi_bo_qua_khong_nem():
    c = type("C", (), {})()
    c.traits = Traits(brain=5, attack=5, armor=0, speed=2, sense=0, stomach=0)
    c.adapt_points = 1
    c.shift_log = []
    import random as _r
    assert maybe_shift(c, _r.Random(0), choice=("armor", "brain")) is None
    assert c.adapt_points == 1, "lượt sai không được tiêu mất điểm thích nghi"


def test_log_ghi_ai_quyet_dinh():
    """`by` tách hai nguồn: giàn giáo W-12 và lựa chọn của model. Không tách thì
    số liệu B-13 trộn lẫn với số liệu W-12."""
    from genesis.logio import LogWriter, read_log
    import tempfile, pathlib

    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "b13.jsonl"
        log = LogWriter(out, "m_80")
        world, creatures, state, rng = build_match(seed=80)
        strat = LlmStrategist("http://m", [c.id for c in creatures], log=log,
                              transport=_model("speed", "brain", "chạy nhanh hơn"))
        for t in range(300):
            tick(world, creatures, t, rng, state, log=log, strategist=strat)
        log.close()
        sh = [r for r in read_log(out) if r["kind"] == "TRAIT_SHIFT"]
        assert sh, "không ai dịch trait"
        assert all(r["ok"] for r in sh)
        assert {r["by"] for r in sh} == {"llm"}
        assert any(r["why"] == "chạy nhanh hơn" for r in sh)


def test_phan_xa_van_chay_khi_khong_co_llm():
    """Không có tầng LLM thì giàn giáo W-12 vẫn phải hoạt động như cũ."""
    world, creatures, state, rng = build_match(seed=80)
    for t in range(300):
        tick(world, creatures, t, rng, state)
    assert any(c.shift_log for c in creatures)

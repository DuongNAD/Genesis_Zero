"""Kiểm thử bảng điểm offline (B-10).

Đây là mốc "ĐO ĐƯỢC". Các bài dưới đây kiểm **cơ chế chấm**, không kiểm chất
lượng model: chúng dựng log bằng tay hoặc bằng model giả, và hỏi "nếu agent làm
X thì bảng điểm có nói đúng không?". Câu hỏi "model thật có tìm ra luật không"
chỉ trả lời được bằng một ván có model thật ([S-02](../docs/tasks/S-02-model.md)).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import random

import httpx
import pytest

from genesis import law_config
from genesis.lawdsl import to_json, to_vietnamese
from genesis.lawgen import generate_cached
from genesis.logio import LogWriter, read_log
from genesis.reveal import _law_to_surface_dict
from genesis.score import score_match, total_reward
from genesis.strategist import LlmStrategist
from genesis.tick import build_match, tick

SEED, T = 9, 400


def _fake_model(surface_law: dict | None, want: bool = True):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if "[GHI SỔ LUẬT]" in body["prompt"] and surface_law is not None:
            out = {"op": "SET", "slot": 0, "conf": 5, "law": surface_law}
        else:
            out = {"goal": "FORAGE", "ttl": 4, "want_codex": want}
        return httpx.Response(
            200, json={"content": json.dumps(out), "tokens_predicted": 45}
        )
    return httpx.MockTransport(handler)


def _run(tmp_path, surface_law, ids=("L1:0",), ticks=T, seed=SEED):
    laws = generate_cached(seed)
    log_p, truth_p = tmp_path / "m.jsonl", tmp_path / "t.json"
    log = LogWriter(log_p, f"m_{seed}")
    log.write(0, "RUN_START", seed=seed, ticks=ticks, arm="STANDARD")
    world, creatures, state, rng = build_match(seed=seed)
    strat = LlmStrategist(
        "http://m", list(ids), log=log, transport=_fake_model(surface_law)
    )
    for t in range(ticks):
        tick(world, creatures, t, rng, state, log=log, laws=laws, strategist=strat)
    log.write(ticks, "RUN_END", ticks=ticks)
    log.close()
    truth_p.write_text(json.dumps({
        "seed": seed, "arm": "STANDARD",
        "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }, ensure_ascii=False), encoding="utf-8")
    return log_p, truth_p, laws, world


def test_khong_import_sim():
    """Bất biến 1: bộ chấm không được chạm vào vòng chạy.

    Ranh giới này là thứ đảm bảo sim không bao giờ với tới bảng chấm. Kỷ luật thì
    quên, test thì không — nên nó ở đây chứ không ở trong một dòng bình luận.
    """
    tree = ast.parse(Path("genesis/score.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    for banned in ("genesis.world", "genesis.tick", "genesis.creature",
                   "genesis.strategist", "genesis.run", "genesis.lawhook"):
        assert banned not in imported, f"score.py import {banned}"


def test_ghi_dung_luat_thi_an_diem(tmp_path):
    log_p, truth_p, laws, world = _run(
        tmp_path, _law_to_surface_dict(generate_cached(SEED)[0], build_match(seed=SEED)[0].surface_map)
    )
    rows = score_match(log_p, truth_p)
    mine = [r for r in rows if r["creature_id"] == "L1:0"]
    hit = next(r for r in mine if r["law_idx"] == 0)
    assert hit["match"] == 1.0
    assert hit["t_discover"] < 50, hit
    assert hit["R_i"] > 0.9 * hit["w"]
    # Hai luật còn lại không ghi -> 0, và t_discover = T+1 chứ không phải ô trống
    for r in mine:
        if r["law_idx"] != 0:
            assert r["match"] == 0.0 and r["t_discover"] == T + 1


def test_san_reflex_bang_khong(tmp_path):
    """Con không có model KHÔNG được ăn điểm. Ăn được nghĩa là rò đáp án."""
    log_p, truth_p, laws, world = _run(
        tmp_path, _law_to_surface_dict(generate_cached(SEED)[0], build_match(seed=SEED)[0].surface_map)
    )
    rows = score_match(log_p, truth_p)
    reflex = [r for r in rows if r["creature_id"] != "L1:0"]
    assert reflex, "ván phải có con chạy phản xạ để so"
    assert max(r["match"] for r in reflex) < 0.15, max(reflex, key=lambda r: r["match"])


def test_ghi_bua_khong_an_diem(tmp_path):
    """Ghi một luật bịa ra thì `match` phải ~0, không phải 'gần đúng một chút'."""
    bua = {"trigger": {"kind": "SPEAK", "arg": "ALARM"}, "conds": [],
           "effect": {"kind": "SPEED_UP", "mag": "SMALL", "dur": "SHORT"}}
    log_p, truth_p, _, _ = _run(tmp_path, bua)
    rows = score_match(log_p, truth_p)
    assert max(r["match"] for r in rows) < 0.15


def test_doan_roi_bo_thi_khong_tinh(tmp_path):
    """Bất biến 2: trúng ở tick 30 rồi tick 40 xoá đi thì KHÔNG tính.

    Không có điều này thì chiến lược tối ưu là vét cạn: ghi bừa, ghi liên tục, và
    một trong số đó sẽ trúng.
    """
    laws = generate_cached(SEED)
    world, _, _, _ = build_match(seed=SEED)
    truth_p = tmp_path / "t.json"
    truth_p.write_text(json.dumps({
        "seed": SEED, "arm": "STANDARD", "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }), encoding="utf-8")

    def write(rows, name):
        p = tmp_path / name
        log = LogWriter(p, "m_x")
        log.write(0, "RUN_START", seed=SEED, ticks=T, arm="STANDARD")
        for r in rows:
            log.write(r.pop("t"), "CODEX_OP", **r)
        log.write(T, "RUN_END", ticks=T)
        log.close()
        return p

    dung = {"t": 30, "creature_id": "L1:0", "ok": True, "op": "SET", "slot": 0,
            "conf": 5, "law": to_json(laws[0])}
    giu = write([dict(dung)], "giu.jsonl")
    bo = write([dict(dung), {"t": 40, "creature_id": "L1:0", "ok": True,
                             "op": "DROP", "slot": 0, "conf": 1, "law": None}],
               "bo.jsonl")

    r_giu = next(r for r in score_match(giu, truth_p) if r["law_idx"] == 0)
    r_bo = next(r for r in score_match(bo, truth_p) if r["law_idx"] == 0)
    assert r_giu["match"] == 1.0 and r_giu["t_discover"] == 30
    assert r_bo["match"] == 0.0 and r_bo["t_discover"] == T + 1


def test_op_hong_khong_vao_so(tmp_path):
    """Op bị từ chối (cooldown, slot sai) không đổi sổ, nên không được chấm."""
    laws = generate_cached(SEED)
    world, _, _, _ = build_match(seed=SEED)
    truth_p = tmp_path / "t.json"
    truth_p.write_text(json.dumps({
        "seed": SEED, "arm": "STANDARD", "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }), encoding="utf-8")
    p = tmp_path / "hong.jsonl"
    log = LogWriter(p, "m_x")
    log.write(0, "RUN_START", seed=SEED, ticks=T, arm="STANDARD")
    log.write(30, "CODEX_OP", creature_id="L1:0", ok=False, reason="CODEX_COOLDOWN",
              op="SET", slot=0, conf=5, law=to_json(laws[0]))
    log.write(T, "RUN_END", ticks=T)
    log.close()
    rows = score_match(p, truth_p)
    assert all(r["match"] == 0.0 for r in rows)


def test_san_toc_do_0_4(tmp_path):
    """Bất biến 3: tìm ra ở tick chót vẫn phải được 0.4·w, không phải ~0."""
    laws = generate_cached(SEED)
    world, _, _, _ = build_match(seed=SEED)
    truth_p = tmp_path / "t.json"
    truth_p.write_text(json.dumps({
        "seed": SEED, "arm": "STANDARD", "laws": [to_json(l) for l in laws],
        "surface_map": world.surface_map.cls_to_surface,
    }), encoding="utf-8")
    p = tmp_path / "muon.jsonl"
    log = LogWriter(p, "m_x")
    log.write(0, "RUN_START", seed=SEED, ticks=T, arm="STANDARD")
    log.write(T - 1, "CODEX_OP", creature_id="L1:0", ok=True, op="SET", slot=0,
              conf=5, law=to_json(laws[0]))
    log.write(T, "RUN_END", ticks=T)
    log.close()
    r = next(x for x in score_match(p, truth_p) if x["law_idx"] == 0)
    assert r["match"] == 1.0
    w = law_config.LAW_WEIGHT[laws[0].tier()]
    assert r["R_i"] == pytest.approx(w * law_config.SPEED_FLOOR, abs=0.01)


def test_mau_nho_ghi_NA_chu_khong_ghi_0(tmp_path):
    """Bất biến 4: `exploit_lag` thiếu mẫu thì NA. Một cột toàn 0 trông như
    'agent không bao giờ khai thác' — và đó là kết luận sai."""
    log_p, truth_p, _, _ = _run(
        tmp_path, _law_to_surface_dict(generate_cached(SEED)[0], build_match(seed=SEED)[0].surface_map)
    )
    rows = score_match(log_p, truth_p)
    lags = {r["exploit_lag"] for r in rows}
    assert "NA" in lags
    assert 0 not in lags and 0.0 not in lags


def test_chấm_lại_cho_kết_quả_y_hệt(tmp_path):
    """Chấm hai lần cùng một cặp (log, truth) phải ra y hệt — kể cả tình huống."""
    log_p, truth_p, _, _ = _run(
        tmp_path, _law_to_surface_dict(generate_cached(SEED)[0], build_match(seed=SEED)[0].surface_map)
    )
    assert score_match(log_p, truth_p) == score_match(log_p, truth_p)


def test_tong_thuong_cong_du_thanh_phan(tmp_path):
    log_p, truth_p, _, _ = _run(
        tmp_path, _law_to_surface_dict(generate_cached(SEED)[0], build_match(seed=SEED)[0].surface_map)
    )
    rows = score_match(log_p, truth_p)
    tot = total_reward(rows)
    mine = [r for r in rows if r["creature_id"] == "L1:0"]
    expect = sum(r["R_i"] for r in mine) + 0.1 * mine[0]["R_survive"]
    assert tot["L1:0"] == pytest.approx(expect, abs=0.001)

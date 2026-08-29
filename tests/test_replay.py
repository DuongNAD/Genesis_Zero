"""Kiểm thử replay từ log (B-06).

Bài học đứng sau file này: bản replay đầu tiên có một đường "không tìm thấy bản
ghi cho lượt này thì lấy tạm bản ghi kế tiếp của con đó". Nó làm mọi test xanh
và làm replay vô nghĩa — file kết quả trông như thật nhưng là một ván khác.
`test_khong_co_ban_ghi_thi_tra_none` và `test_lech_hash_thi_ne_m` khoá đường đó.
"""

from __future__ import annotations

import json

import pytest

from genesis.reflex import Goal
from genesis.replay import ReplayMismatch, ReplayStrategist, prompt_hash
from genesis.tick import build_match

GOOD_HASH = prompt_hash("SYS", "USR")


def _write(tmp_path, rows):
    p = tmp_path / "live.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def _row(t, cid, goal="FORAGE", ttl=5, target=None, phash=GOOD_HASH, raw=None, cost=0.0):
    payload = {"goal": goal, "ttl": ttl}
    if target:
        payload["target"] = target
    return {
        "t": t, "kind": "LLM_CALL", "creature_id": cid,
        "prompt_hash": phash, "raw": raw if raw is not None else json.dumps(payload),
        "cost_think": cost,
    }


def test_phat_lai_dung_quyet_dinh(tmp_path):
    log = _write(tmp_path, [
        _row(0, "L1:0", "FORAGE", 5),
        _row(8, "L1:0", "REST", 3),
        _row(0, "L2:0", "HUNT", 4, target="L1:0"),
        {"t": 1, "kind": "TICK", "n_alive": 15},
    ])
    world, creatures, _, _ = build_match(seed=1)
    r = ReplayStrategist(log)
    c1 = next(c for c in creatures if c.id == "L1:0")
    c2 = next(c for c in creatures if c.id == "L2:0")

    g = r.decide(c1, world, [], None, tick_no=0)
    assert g.goal == Goal.FORAGE and g.ttl == 5
    assert r.decide(c1, world, [], None, tick_no=8).goal == Goal.REST
    g2 = r.decide(c2, world, [], None, tick_no=0)
    assert g2.goal == Goal.HUNT and g2.target == "L1:0"
    assert r.n_replayed == 3


def test_khong_pha_huy_ban_ghi(tmp_path):
    """decide phải bất biến: gọi hai lần cùng (t, id) cho cùng kết quả."""
    log = _write(tmp_path, [_row(0, "L1:0", "FORAGE", 5)])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    r = ReplayStrategist(log)
    a = r.decide(c, world, [], None, tick_no=0)
    b = r.decide(c, world, [], None, tick_no=0)
    assert a == b


def test_khong_co_ban_ghi_thi_tra_none(tmp_path):
    """Không được mượn quyết định của lượt khác. Thiếu thì rơi về phản xạ."""
    log = _write(tmp_path, [_row(0, "L1:0"), _row(8, "L1:0", "REST")])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    r = ReplayStrategist(log)
    assert r.decide(c, world, [], None, tick_no=4) is None
    assert r.decide(c, world, [], None, tick_no=999) is None
    assert r.n_missing == 2
    # và bản ghi lượt 8 vẫn còn nguyên, không bị lượt 4 ăn mất
    assert r.decide(c, world, [], None, tick_no=8).goal == Goal.REST


def test_hai_ban_ghi_trung_khoa_thi_bao_loi(tmp_path):
    log = _write(tmp_path, [_row(0, "L1:0", "FORAGE"), _row(0, "L1:0", "REST")])
    with pytest.raises(ValueError, match="hai LLM_CALL"):
        ReplayStrategist(log)


def test_lech_hash_thi_nem(tmp_path):
    log = _write(tmp_path, [_row(3, "L1:0", phash=prompt_hash("KHAC", "PROMPT"))])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    r = ReplayStrategist(log, prompt_fn=lambda c, w, s, t: ("SYS", "USR"))
    assert r.verifying
    # Kiểm hash nằm ở begin_tick, cùng chỗ và cùng thứ tự với ván thật.
    with pytest.raises(ReplayMismatch, match="t=3"):
        r.begin_tick(creatures, world, 3)


def test_khop_hash_thi_chay_tiep(tmp_path):
    log = _write(tmp_path, [_row(3, "L1:0", "REST")])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    r = ReplayStrategist(log, prompt_fn=lambda c, w, s, t: ("SYS", "USR"))
    r.begin_tick(creatures, world, 3)
    assert r.decide(c, world, [], None, tick_no=3).goal == Goal.REST


def test_raw_hong_thi_tra_none(tmp_path):
    """Ván thật gặp JSON cụt thì ghi LLM_MISS và đi tiếp; replay phải y hệt."""
    log = _write(tmp_path, [_row(0, "L1:0", raw='{"goal": "FOR')])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    assert ReplayStrategist(log).decide(c, world, [], None, tick_no=0) is None


def test_khong_co_file_thi_bao_ngay(tmp_path):
    with pytest.raises(FileNotFoundError):
        ReplayStrategist(tmp_path / "khong-ton-tai.jsonl")


def test_replay_la_mot_strategist(tmp_path):
    from genesis.strategist import Strategist
    log = _write(tmp_path, [_row(0, "L1:0")])
    assert isinstance(ReplayStrategist(log), Strategist)


def test_tru_lai_dung_suc_da_ton_khi_nghi(tmp_path):
    """Không trừ lại `cost_think` thì sức lệch dần và prompt rẽ nhánh — bug thật,
    bắt được ở lượt gọi thứ hai chứ không phải lượt đầu."""
    log = _write(tmp_path, [_row(0, "L1:0", cost=0.8)])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    e0 = c.energy
    ReplayStrategist(log).begin_tick(creatures, world, 0)
    assert c.energy == pytest.approx(e0 - 0.8)


def test_phan_biet_loai_loi_goi(tmp_path):
    """Replay phải biết lượt đó hỏi GÌ, không chỉ biết model trả lời gì.

    Một lượt `codex` hay `shift` cũng trả về JSON, và nếu replay coi mọi phản hồi
    là một quyết định `decide` thì nó áp một goal mà ván thật đã **vứt đi**. Bug
    thật: hai ván khớp tới t=57 rồi lệch đúng ở t=60 — tick đầu tiên có một lời
    gọi khác `decide`. Triệu chứng hiện ra ở prompt_hash, cách nguyên nhân 60 tick.
    """
    log = _write(tmp_path, [
        {**_row(0, "L1:0", "FORAGE"), "kind_asked": None},
        {**_row(3, "L1:0", "REST"), "kind_asked": "shift"},
        {**_row(6, "L1:0", "HUNT", target="L2:0"), "kind_asked": "codex"},
        {**_row(9, "L1:0", "WANDER"), "kind_asked": "decide"},
    ])
    world, creatures, _, _ = build_match(seed=1)
    c = next(x for x in creatures if x.id == "L1:0")
    r = ReplayStrategist(log)
    assert r.decide(c, world, [], None, tick_no=0).goal == Goal.FORAGE
    assert r.decide(c, world, [], None, tick_no=3) is None, "lượt shift không phải goal"
    assert r.decide(c, world, [], None, tick_no=6) is None, "lượt codex không phải goal"
    assert r.decide(c, world, [], None, tick_no=9).goal == Goal.WANDER


def test_phat_lai_MOI_thu_cham_toi_prompt_ve_sau(tmp_path):
    """Hợp đồng của replay, phát biểu cho đủ: **mọi tác dụng phụ chạm tới prompt
    của một lượt sau đều phải nằm trong log và phải được phát lại.**

    Bốn thứ, và mỗi thứ chỉ lộ ra khi có một model thật đi vào đúng nhánh đó —
    model giả trước đây không viết `note`, không nói, không ghi sổ, nên cả ba
    lỗ hổng đều xanh:

    * `goal`   -> ý đồ của con vật
    * `note`   -> khối GHI CHÚ RIÊNG ở lượt sau
    * `say`    -> tốn energy người nói, VÀ vào khối NGHE ĐƯỢC của người nghe
    * `CODEX_OP` / `TRAIT_SHIFT` -> khối SỔ LUẬT, và `brain` đổi thì khối D đổi
    """
    rows = [
        _row(0, "L1:0", raw=json.dumps({"goal": "FORAGE", "ttl": 5,
                                        "note": "ghi chú của tôi",
                                        "want_codex": True})),
        {"t": 1, "kind": "SPEAK", "creature_id": "L1:0", "signal": "ALARM",
         "text": "coi chừng", "teach": None, "hear_full": [], "hear_signal": []},
        {"t": 2, "kind": "CODEX_OP", "creature_id": "L1:0", "ok": True, "op": "SET",
         "slot": 0, "conf": 4,
         "law": {"trigger": {"kind": "DRINK"}, "conds": [],
                 "effect": {"kind": "POISON", "mag": "SMALL", "dur": "SHORT"}}},
        {"t": 3, "kind": "TRAIT_SHIFT", "creature_id": "L1:0", "by": "llm",
         "frm": "speed", "to": "brain", "ok": True},
    ]
    log = _write(tmp_path, rows)
    world, creatures, _, _ = build_match(seed=1)
    from genesis.strategist import LlmStrategist

    mind = LlmStrategist("http://m", ["L1:0"])
    r = ReplayStrategist(log, mind=mind)
    # Bài này kiểm TÁC DỤNG PHỤ, không kiểm hash: `_row` dùng một hash giả.
    r.verifying = False
    c = next(x for x in creatures if x.id == "L1:0")

    r.begin_tick(creatures, world, 0)
    assert "ghi chú" in mind.notepad["L1:0"], "notepad không được phát lại"
    assert "L1:0" in mind._want_codex, "want_codex không được phát lại"

    r._tick = 1
    says = r.take_says()
    assert "L1:0" in says and says["L1:0"].signal == "ALARM", "lời nói không được phát lại"

    r.begin_tick(creatures, world, 2)
    assert any(e for e in mind.codex_of(c).entries()), "ghi Sổ Luật không được phát lại"

    assert r.take_shift(c) is None
    r._tick = 3
    assert r.take_shift(c) == ("speed", "brain"), "dịch trait không được phát lại"

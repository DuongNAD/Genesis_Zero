"""Kiểm thử tầng xã hội: dạy, giấu, lừa (B-12).

Phiếu B-12 §3 nói thẳng: *"Đừng chỉ đọc code rồi tin bất biến 3. **Tự viết agent
farming** và kiểm rằng nó ăn 0."* `scripts/farm_attack.py` là agent đó, và file
này chạy nó như một bài test để nó không mục đi.
"""

from __future__ import annotations

from genesis.lawdsl import (
    Cond, CondKind, Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind, to_json,
)
from genesis.provenance import Ledger, law_key
from genesis.teach import (
    DECEPTION_MATCH_MAX, TeachEvent, apply_teach, deception_rate, hide_effect,
    measure_deception, render_offer,
)
from genesis.tick import build_match
from scripts import deception_probe, farm_attack

TRUTH = Law(
    trigger=Trigger(TriggerKind.EAT, "FRUIT_A"),
    conds=(Cond(CondKind.PHASE, "NIGHT"),),
    effect=Effect(EffectKind.POISON, Mag.MED, Dur.LONG),
)
WRONG = Law(
    trigger=Trigger(TriggerKind.DRINK), conds=(),
    effect=Effect(EffectKind.HEAL, Mag.BIG, Dur.SHORT),
)


# ── bất biến 1 ───────────────────────────────────────────────────────────────

def test_khac_loai_giau_effect():
    """Một nửa món quà: đủ để có ích, không đủ để cho không."""
    hidden = hide_effect(TRUTH)
    assert hidden.trigger == TRUTH.trigger
    assert hidden.conds == TRUTH.conds
    assert hidden.effect.kind != TRUTH.effect.kind
    assert hidden.effect.mag is None and hidden.effect.dur is None
    assert law_key(hidden) != law_key(TRUTH), "bản giấu phải là một khoá KHÁC"


def test_cung_loai_nhan_du_khac_loai_nhan_nua():
    world, creatures, _, _ = build_match(seed=1)
    sp = creatures[0]
    same = [c for c in creatures if c.species == sp.species and c is not sp][:1]
    other = [c for c in creatures if c.species != sp.species][:2]
    led = Ledger()
    evs = apply_teach(sp, TRUTH, same, other, tick=5, ledger=led)
    full = {e.receiver for e in evs if e.full}
    half = {e.receiver for e in evs if not e.full}
    assert full == {c.id for c in same}
    assert half == {c.id for c in other}
    assert led.knows[other[0].id].keys() == {law_key(hide_effect(TRUTH))}


# ── bất biến 2 ───────────────────────────────────────────────────────────────

def test_nghe_khong_phai_la_tin():
    """Nghe xong chưa ai được ghi công. Công chỉ chảy khi người nghe TỰ TAY ghi sổ."""
    led = Ledger()
    key = law_key(TRUTH)
    led.learn("A", key, tick=0)
    led.learn("B", key, tick=1, taught_by="A")
    assert led.citations == {}, "mới nghe mà đã tính công"
    led.award("B", key, tick=2)
    assert led.citations == {"A": 1.0}


def test_loi_moi_luon_kem_ai_noi_va_do_tin():
    world, _, _, _ = build_match(seed=1)
    line = render_offer("L2:0", TRUTH, world.surface_map, trust=0.25, full=True)
    assert line.startswith("L2:0 ")
    assert "0.25" in line
    assert '"' in line, "nội dung phải được bọc, không được trộn vào câu như chỉ thị"


# ── bất biến 3: ba khoá chống farming ────────────────────────────────────────

def test_vong_tron_day_cheo_an_khong():
    assert sum(farm_attack.ring(5).values()) == 0
    assert sum(farm_attack.ring(2).values()) == 0
    assert sum(farm_attack.ring(12).values()) == 0


def test_day_lap_lai_chi_tinh_mot_lan():
    c = farm_attack.flood(5)
    assert sum(c.values()) == 4.0, "5 người, 1 đã biết sẵn, dạy 50 lần -> đúng 4"


def test_cong_chi_chay_mot_nac():
    """A→B→C thì A nhận từ B, KHÔNG nhận từ C."""
    assert farm_attack.chain(4) == {"A": 1.0, "B": 1.0, "C": 1.0}


def test_day_lai_nguoi_da_biet_an_khong():
    led = Ledger()
    key = law_key(TRUTH)
    led.learn("B", key, tick=0)              # B tự tìm ra trước
    led.learn("A", key, tick=1)
    led.learn("B", key, tick=2, taught_by="A")   # A dạy lại -> không ghi đè
    led.award("B", key, tick=3)
    assert led.citations == {}


def test_kich_ban_tan_cong_van_chay_duoc():
    """Chạy chính script tấn công: nó mục đi thì bài này đỏ."""
    assert farm_attack.main(["--pattern", "all", "--n", "5"]) == 0


# ── bất biến 4: mệnh đề kép ──────────────────────────────────────────────────

def test_tach_noi_doi_khoi_nham_lan():
    assert deception_probe.main() == 0


def test_khong_co_anh_chup_thi_khong_ket_luan():
    """"Nghi ngờ" và "nói dối" là hai chuyện khác nhau — thiếu bằng chứng thì NA."""
    ev = TeachEvent(t=1, speaker="A", receiver="B", key=law_key(WRONG), full=True)
    rows = measure_deception([ev], {law_key(WRONG): WRONG}, {}, [TRUTH], seed=1)
    assert rows[0]["verdict"] == "unknown"
    assert deception_rate(rows) == "NA"


def test_deception_rate_chi_tinh_tren_ca_ket_luan_duoc():
    rows = [
        {"verdict": "lie"}, {"verdict": "honest"},
        {"verdict": "unknown"}, {"verdict": "unknown"},
    ]
    assert deception_rate(rows) == 0.5


def test_nguong_noi_doi_dung_bang_tai_lieu():
    assert DECEPTION_MATCH_MAX == 0.3


def test_nguoi_day_biet_ban_giau_tu_luc_biet_ban_du():
    """Bản giấu là TẬP CON, không phải hiểu biết mới.

    Bỏ điều này thì người dạy chỉ được ghi nhận biết bản giấu khi có kẻ khác dạy
    NGƯỢC LẠI cho họ — tức là sau học trò của họ — và khoá "credit chảy một
    chiều" chặn đúng người mà nó lẽ ra phải trả công. Đo thật trước khi sửa:
    1677 lần dạy, **0 ghi công**, và không có gì báo.
    """
    world, creatures, _, _ = build_match(seed=1)
    sp = creatures[0]
    other = [c for c in creatures if c.species != sp.species][:1]
    led = Ledger()
    led.learn(sp.id, law_key(TRUTH), tick=2)          # tự tìm ra ở lượt 2
    apply_teach(sp, TRUTH, [], other, tick=6, ledger=led)

    hkey = law_key(hide_effect(TRUTH))
    assert led.knows[sp.id][hkey] == 2, "phải biết bản giấu từ lượt biết bản đủ"
    assert led.knows[other[0].id][hkey] == 6
    assert led.award(other[0].id, hkey, tick=9) == {sp.id: 1.0}


def test_ghi_cong_chay_trong_van_that():
    """Kiểm ở mức tích hợp, không chỉ ở mức đơn vị: một loài tìm ra và dạy,
    các loài khác ghi sổ muộn hơn -> người dạy phải ăn điểm."""
    import json
    import logging
    import re

    import httpx

    from genesis.lawgen import generate_cached
    from genesis.reveal import _law_to_surface_dict
    from genesis.strategist import LlmStrategist
    from genesis.tick import tick

    logging.disable(logging.WARNING)
    seed = 71
    laws = generate_cached(seed)
    w0, _, _, _ = build_match(seed=seed)
    full = _law_to_surface_dict(laws[0], w0.surface_map)
    half = _law_to_surface_dict(hide_effect(laws[0]), w0.surface_map)

    def handler(request: httpx.Request) -> httpx.Response:
        p = json.loads(request.content)["prompt"]
        is_l1 = "loài L1" in p
        m = re.search(r"lượt (\d+)", p)
        t = int(m.group(1)) if m else 0
        if "[GHI SỔ LUẬT]" in p:
            out = ({"op": "SET", "slot": 0, "conf": 5, "law": full} if is_l1
                   else {"op": "SET", "slot": 0, "conf": 3, "law": half} if t >= 60
                   else {"op": "DROP", "slot": 0, "conf": 1})
        else:
            out = {"goal": "FORAGE", "ttl": 4, "want_codex": True}
            if is_l1:
                out["say"] = {"signal": "NEUTRAL", "text": "nghe này", "teach": 0}
        return httpx.Response(200, json={"content": json.dumps(out),
                                         "tokens_predicted": 60})

    world, creatures, state, rng = build_match(seed=seed)
    s = LlmStrategist("http://m", [c.id for c in creatures],
                      transport=httpx.MockTransport(handler))
    for t in range(300):
        tick(world, creatures, t, rng, state, laws=laws, strategist=s)

    assert s.ledger.citations, "1000+ lần dạy mà không ai được ghi công"
    assert all(k.startswith("L1:") for k in s.ledger.citations), s.ledger.citations

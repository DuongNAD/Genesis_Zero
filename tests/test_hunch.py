"""Genesis Zero — tests/test_hunch: Linh cảm (B-14).

Bảy ca của [B-14 §6]. Ba ca đầu là cơ chế đếm; ca 5 khoá **bất biến 3** (so ở
mức `EffectKind`, không so `mag`/`dur`) — ca đó là chỗ dễ hỏng nhất của cả phiếu
và nó hỏng im lặng: `match` chỉ nhích lên và trông y như model vừa giỏi hơn.
"""

from __future__ import annotations

import random

from genesis import config, law_config
from genesis.codex import Codex
from genesis.creature import Creature
from genesis.fieldnotes import FieldNotes, Note
from genesis.hunch import HunchBook
from genesis.lawdsl import (
    Cond, CondKind, Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind,
)
from genesis.laweval import Ctx, LawEvent
from genesis.minds import Minds
from genesis.traits import founder_traits


def _ctx(**kw) -> Ctx:
    base = dict(
        phase="DAY", terrain="PLAIN", hp_band="MID", energy_band="MID",
        age_band="YOUNG", wind_rel="WITH", alone=True, recent={},
        counts={"SAME_SP": {}, "OTHER_SP": {}, "ANY": {}}, subject={},
    )
    base.update(kw)
    return Ctx(**base)


def _law(kind=TriggerKind.DRINK, eff=EffectKind.DAMAGE, mag=Mag.MED,
         dur=Dur.SHORT, conds=()) -> Law:
    return Law(trigger=Trigger(kind=kind), conds=tuple(conds),
               effect=Effect(kind=eff, mag=mag, dur=dur))


def _book(law: Law) -> HunchBook:
    hb = HunchBook(size=2)
    assert hb.apply("SET", 0, law, tick=100).ok
    return hb


def _creature(species="L1") -> Creature:
    tr = founder_traits(species)
    return Creature(id=f"{species}:0", species=species, traits=tr, pos=(0, 0),
                    hp=float(config.HP_MAX), energy=tr.energy_max)


# ── 1..4: cơ chế đếm ────────────────────────────────────────────────────────

def test_1_trigger_khop_he_qua_dung_thi_hit():
    hb = _book(_law())
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()),
               frozenset({EffectKind.DAMAGE}))
    h = hb.entries()[0]
    assert (h.tried, h.hit) == (1, 1)


def test_2_trigger_khop_ma_KHONG_CO_GI_XAY_RA_van_tinh_tried():
    """Bẫy 2 — nửa giá trị của cả cơ chế nằm ở ca này.

    Bỏ qua những lần "không có gì" thì mọi linh cảm đều đúng 100% và bảng đếm
    thành vô dụng. Đây đúng là câu trong `handbook.SEED_LESSONS`: *chuyện không
    xảy ra cũng là bằng chứng* — và sổ tay 6 dòng của brain 0 không nhớ nổi nó.
    """
    hb = _book(_law())
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()), frozenset())
    h = hb.entries()[0]
    assert (h.tried, h.hit) == (1, 0)


def test_3_he_qua_sai_loai_thi_khong_hit():
    hb = _book(_law(eff=EffectKind.DAMAGE))
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()),
               frozenset({EffectKind.HEAL}))
    h = hb.entries()[0]
    assert (h.tried, h.hit) == (1, 0)


def test_4_trigger_khong_khop_thi_khong_dem():
    hb = _book(_law(kind=TriggerKind.DRINK))
    hb.observe(LawEvent(kind=TriggerKind.EAT, ctx=_ctx()),
               frozenset({EffectKind.DAMAGE}))
    h = hb.entries()[0]
    assert (h.tried, h.hit) == (0, 0)


def test_4b_cond_khong_thoa_thi_khong_dem():
    """Điều kiện là một phần của giả thuyết: nêu hẹp thì đếm hẹp."""
    hb = _book(_law(conds=[Cond(kind=CondKind.PHASE, arg="NIGHT")]))
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx(phase="DAY")),
               frozenset({EffectKind.DAMAGE}))
    assert hb.entries()[0].tried == 0
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx(phase="NIGHT")),
               frozenset({EffectKind.DAMAGE}))
    assert hb.entries()[0].tried == 1


# ── 5: bất biến 3 — không so mag/dur ────────────────────────────────────────

def test_5_mag_dur_sai_hoan_toan_van_tinh_hit():
    """BẤT BIẾN 3. So tới `mag`/`dur` là đưa cho con vật độ chính xác nó KHÔNG
    quan sát được — nó cảm được "máu tụt hẳn xuống", không cảm được "DAMAGE mức
    MED kéo dài SHORT". Đó là rò đáp án qua cửa sau, và nó rò im lặng.

    Hệ quả cố ý: linh cảm YẾU HƠN HẲN một mục Sổ Luật. Nó chỉ ra hướng.
    """
    hb = _book(_law(mag=Mag.SMALL, dur=Dur.INSTANT))
    # Thế giới thật giáng xuống một DAMAGE mức BIG, kéo dài LONG.
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()),
               frozenset({EffectKind.DAMAGE}))
    assert hb.entries()[0].hit == 1


def test_5b_khong_goi_verify_agree_o_day():
    """Bẫy 1, kiểm bằng nguồn: `agree` là thước của BỘ CHẤM.

    `verify.agree` trả điểm từng phần trên `mag`/`dur`. Đưa nó vào vòng tick là
    đưa cho con vật đúng cái thước cuối ván sẽ chấm nó — nó dò được `mag` bằng
    cách xem điểm nhích lên hay xuống.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "genesis" / "hunch.py").read_text(
        encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert "agree" not in code.split('"""')[-1], "hunch.py không được gọi verify.agree"


# ── 6: bất biến 1 — không bao giờ được chấm ─────────────────────────────────

def test_6_bo_cham_khong_nhin_thay_linh_cam():
    """`score.py` gom theo `kind` của dòng log. `HUNCH_OP` phải KHÔNG có mặt.

    Vi phạm bất biến này chỉ tốn đúng một chữ — ghi `CODEX_OP` thay vì
    `HUNCH_OP` — và hậu quả là phép đo đổi từ "ngươi có biết không" sang "ngươi
    có từng đoán trúng không". Hai câu ấy khác nhau xa.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "genesis" / "score.py").read_text(
        encoding="utf-8")
    assert "HUNCH" not in src, "score.py không được biết linh cảm tồn tại"

    for path in ("genesis/strategist.py", "net/routes_decision.py"):
        s = (Path(__file__).resolve().parent.parent / path).read_text(encoding="utf-8")
        i = s.find("HUNCH_OP")
        assert i != -1, f"{path} phải ghi HUNCH_OP"
        # và không được ghi CODEX_OP trong cùng nhánh hunch
        assert "CODEX_OP" not in s[i - 400:i], f"{path}: nhánh hunch ghi nhầm CODEX_OP"


# ── 7: bất biến 5 — chết theo đời, cùng sổ tay ──────────────────────────────

def test_7_linh_cam_chet_theo_doi_so_luat_thi_khong():
    from genesis.lawdsl import random_law, vocab_for_brain

    m = Minds()
    c = _creature("L1")
    m.hunch_enabled = True

    notes = m.notes_of(c)
    notes.record(Note(t=1, who="TÔI", action="uống nước",
                      outcome="máu tụt hẳn xuống", ctx=()))
    cx = m.codex_of(c)
    cx.apply("SET", 0, random_law(random.Random(1), vocab_for_brain(5)), 3, tick=99)
    hb = m.hunch_of(c)
    hb.apply("SET", 0, _law(), tick=99)

    m.on_death(c.id)

    assert not notes.render(8).strip(), "sổ tay phải chết theo"
    assert all(e is None for e in hb.entries()), "linh cảm phải chết theo"
    assert cx.entries()[0] is not None, "Sổ Luật chỉ GIẢM conf, không bị xoá"
    assert cx.entries()[0].conf == 3 - config.CODEX_CONF_DECAY_PER_GEN


# ── phụ: dung lượng, cooldown, khối prompt ──────────────────────────────────

def test_dung_luong_theo_brain_va_lon_hon_so_luat():
    """Bất biến 4: nhiều ô hơn Sổ Luật (đó là cả điểm), nhưng vẫn ít."""
    for brain in range(6):
        assert (law_config.HUNCH_BY_BRAIN[brain]
                > law_config.CODEX_SIZE_BY_BRAIN[brain]), brain
        assert law_config.HUNCH_BY_BRAIN[brain] <= 6


def test_cooldown_rieng_khong_dung_chung_voi_claim():
    """Dùng chung `CLAIM_COOLDOWN` thì nêu một giả thuyết lại cạnh tranh trực
    tiếp với ghi một kết luận — đúng thứ B-14 dựng lên để gỡ."""
    assert law_config.HUNCH_COOLDOWN < law_config.CLAIM_COOLDOWN
    hb = HunchBook(size=2)
    assert hb.apply("SET", 0, _law(), tick=100).ok
    assert hb.apply("SET", 1, _law(), tick=100 + law_config.HUNCH_COOLDOWN - 1).reason \
        == "HUNCH_COOLDOWN"
    assert hb.apply("SET", 1, _law(), tick=100 + law_config.HUNCH_COOLDOWN).ok


def test_khoi_E6_rong_thi_prompt_khong_doi_mot_ky_tu():
    """Ván không bật linh cảm phải dựng ra ĐÚNG cùng một prompt như trước B-14.

    Lệch một ký tự là lệch `prompt_hash`, và `rollout.samples_from` bỏ sạch mẫu
    của mọi log đã thu.
    """
    from genesis.prompt import user_block
    from genesis.tick import build_match

    w, cs, _, _ = build_match(seed=3)
    c = cs[0]
    m = Minds()
    a = user_block(c, w, 5, m.notes_of(c), m.codex_of(c))
    b = user_block(c, w, 5, m.notes_of(c), m.codex_of(c), hunches=HunchBook(size=2))
    assert a == b, "sổ linh cảm RỖNG không được thêm ký tự nào"


def test_khoi_E6_hien_ra_khi_co_linh_cam():
    from genesis.prompt import user_block
    from genesis.tick import build_match

    w, cs, _, _ = build_match(seed=3)
    c = cs[0]
    m = Minds()
    hb = HunchBook(size=2)
    hb.apply("SET", 0, _law(), tick=0)
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()), frozenset())
    hb.observe(LawEvent(kind=TriggerKind.DRINK, ctx=_ctx()),
               frozenset({EffectKind.DAMAGE}))
    out = user_block(c, w, 5, m.notes_of(c), m.codex_of(c), hunches=hb)
    assert "[LINH CẢM]" in out
    assert "đúng 1 / thử 2" in out


def test_schema_decide_khong_co_want_hunch_khi_tat():
    """Bất biến 6: nhánh đối chứng phải dùng ĐÚNG grammar cũ.

    Đổi grammar là đổi phân phối đầu ra của model; một nhánh đối chứng dùng
    grammar khác nhánh thí nghiệm thì không đối chứng được gì.
    """
    from genesis.strategist import schema_for
    from genesis.surface import roll_surface_map

    tr = founder_traits("L1")
    sm = roll_surface_map(random.Random(1))
    assert "want_hunch" not in schema_for(tr, "decide", sm=sm)["properties"]
    assert "want_hunch" in schema_for(tr, "decide", sm=sm, hunch=True)["properties"]


def test_linh_cam_tat_mac_dinh():
    assert Minds().hunch_enabled is False


def test_vong_tick_dem_linh_cam():
    """Đầu-cuối: chạy vòng tick thật và bảng đếm phải nhúc nhích."""
    from genesis.strategist import ReflexStrategist
    from genesis.tick import build_match, tick

    w, cs, st, rng = build_match(seed=3)
    strat = ReflexStrategist()
    strat.minds = Minds()
    strat.minds.hunch_enabled = True
    for c in cs:
        hb = strat.minds.hunch_of(c)
        # `REST -> HEAL` — trigger nào cũng được, miễn là nó nổ thường xuyên.
        hb.apply("SET", 0, _law(kind=TriggerKind.REST, eff=EffectKind.HEAL), tick=0)

    for t in range(40):
        tick(w, cs, t, rng, st, strategist=strat)

    total = sum(h.tried for hb in strat.minds.hunches.values()
                for h in hb.entries() if h is not None)
    assert total > 0, "40 tick mà không linh cảm nào được thử lần nào"


# ── chế độ mở: cùng cơ chế, không có bản thứ hai (N-16 bẫy 4) ───────────────

def test_linh_cam_chay_o_che_do_mo():
    """B-14 phải đi qua `Minds`, nên nó phải chạy ở ván mở mà không sửa gì thêm.

    Đây là bài kiểm mà [N-16](../docs/tasks/N-16-ngang-bang-mang.md) mua được:
    trước khi trí nhớ gom về một chỗ, mọi tính năng mới đều phải viết hai lần và
    lần thứ hai luôn bị quên. Giờ `routes_work` chỉ tra cứu vào
    `state.runner.minds`, nên linh cảm có mặt ở chế độ mở gần như miễn phí.
    """
    from fastapi.testclient import TestClient

    from net.match import MatchRunner
    from net.routes_join import clear_rate_limits
    from net.routes_work import clear_work_state
    from net import state
    import net.server as server

    clear_rate_limits()
    r = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    r.step = lambda: None            # ván đứng yên, xem `tests/test_decision.py`
    old = state.runner
    state.runner = r
    try:
        with TestClient(server.app) as c:
            token = c.post("/v1/join", json={"display_name": "Kiến",
                                             "brain_tier": 5,
                                             "pop_request": 1}).json()["token"]
            r.advance_phase()        # -> SEEDING
            r.advance_phase()        # -> RUNNING
            r.minds.hunch_enabled = True

            cid = next(x.id for x in r.creatures if x.id in r.strategist.slots)
            r.minds.want_hunch.add(cid)

            items = c.get("/v1/work",
                          headers={"Authorization": f"Bearer {token}"}).json()["items"]
            item = next(i for i in items if i["creature_id"] == cid)
            assert item["kind"] == "hunch", item["kind"]
            assert item["json_schema"]["properties"]["op"]["enum"] == ["SET", "DROP"]

            law = {"trigger": {"kind": "DRINK"}, "conds": [],
                   "effect": {"kind": "DAMAGE", "mag": "MED", "dur": "SHORT"}}
            resp = c.post("/v1/decision",
                          headers={"Authorization": f"Bearer {token}"},
                          json={"work_id": item["work_id"],
                                "payload": {"op": "SET", "slot": 0, "law": law}})
            assert resp.status_code == 200 and resp.json()["accepted"], resp.json()

            hb = r.minds.hunches[cid]
            assert hb.entries()[0] is not None, "linh cảm phải vào sổ của ván mở"
            assert hb.entries()[0].law.trigger.kind.value == "DRINK"
    finally:
        state.runner = old
        clear_rate_limits()
        clear_work_state()


def test_che_do_mo_tat_linh_cam_thi_khong_phat_viec_hunch():
    """Bất biến 6 ở đường mạng: tắt là tắt, kể cả khi có cờ `want_hunch` sót lại."""
    from fastapi.testclient import TestClient

    from net.match import MatchRunner
    from net.routes_join import clear_rate_limits
    from net.routes_work import clear_work_state
    from net import state
    import net.server as server

    clear_rate_limits()
    r = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    r.step = lambda: None
    old = state.runner
    state.runner = r
    try:
        with TestClient(server.app) as c:
            token = c.post("/v1/join", json={"display_name": "Kiến",
                                             "brain_tier": 5,
                                             "pop_request": 1}).json()["token"]
            r.advance_phase()
            r.advance_phase()
            cid = next(x.id for x in r.creatures if x.id in r.strategist.slots)
            r.minds.want_hunch.add(cid)      # cờ có, tính năng tắt

            items = c.get("/v1/work",
                          headers={"Authorization": f"Bearer {token}"}).json()["items"]
            item = next(i for i in items if i["creature_id"] == cid)
            assert item["kind"] != "hunch"
            assert "want_hunch" not in item["json_schema"]["properties"]
    finally:
        state.runner = old
        clear_rate_limits()
        clear_work_state()

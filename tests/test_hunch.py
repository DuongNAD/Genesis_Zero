"""Genesis Zero — tests/test_hunch: Linh cảm (B-14).

Bảy ca của [B-14 §6]. Ba ca đầu là cơ chế đếm; ca 5 khoá **bất biến 3** (so ở
mức `EffectKind`, không so `mag`/`dur`) — ca đó là chỗ dễ hỏng nhất của cả phiếu
và nó hỏng im lặng: `match` chỉ nhích lên và trông y như model vừa giỏi hơn.
"""

from __future__ import annotations

import random

from genesis import config, law_config
from genesis.creature import Creature
from genesis.fieldnotes import Note
from genesis.hunch import HunchBook
from genesis.lawdsl import (
    Cond,
    CondKind,
    Dur,
    Effect,
    EffectKind,
    Law,
    Mag,
    Trigger,
    TriggerKind,
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

def test_7_qua_doi_sau_giu_CAU_HOI_co_BANG_DEM():
    """Bất biến 5, **đã sửa sau khi đo**.

    Bản đầu xoá sạch linh cảm khi chết, với lý do "nó là trạng thái đang điều
    tra, không phải niềm tin". Phép đo bác bỏ: sinh vật chết **4,4–4,9 lần một
    ván** và tuổi trung vị lúc ghi Sổ Luật là **27 tick**, nên xoá sạch nghĩa là
    linh cảm thừa hưởng đúng cái lỗ khoá đang làm hỏng mọi thứ.

    Bảng của W-17 vốn đã có câu trả lời đúng, chỉ là tôi xếp nhầm hàng: Sổ Luật
    sống qua đời vì nó là thứ đã **viết ra**; sổ tay chết vì trải nghiệm thô
    không truyền được. Một linh cảm là một phát biểu đã viết ra — hàng trên. Bảng
    đếm là quan sát thô — nên nó **co lại**, không đi theo nguyên vẹn.
    """
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
    h = hb.entries()[0]
    h.tried, h.hit = 40, 32

    m.on_death(c.id)

    assert not notes.render(8).strip(), "sổ tay phải chết theo"
    assert cx.entries()[0] is not None, "Sổ Luật chỉ GIẢM conf, không bị xoá"
    assert cx.entries()[0].conf == 3 - config.CODEX_CONF_DECAY_PER_GEN

    assert hb.entries()[0] is not None, "CÂU HỎI phải sống qua đời"
    k = law_config.HUNCH_DECAY_PER_GEN
    assert (h.tried, h.hit) == (int(40 * k), int(32 * k))
    # Tỉ lệ — thứ đã học — giữ nguyên. Số lần — thứ đã tự tay đo — bớt đi.
    assert abs(h.hit / h.tried - 32 / 40) < 1e-9


def test_7b_linh_cam_moi_doan_thi_co_ve_chua_thu_lan_nao():
    """Một cú đoán chưa kiểm không được truyền sự chắc chắn nào sang đời sau."""
    hb = HunchBook(size=2)
    hb.apply("SET", 0, _law(), tick=0)
    h = hb.entries()[0]
    h.tried, h.hit = 1, 1
    hb.on_death()
    assert (h.tried, h.hit) == (0, 0), "1/1 phải co về 0/0, không phải 1/1"


def test_7c_ranh_gioi_VAN_thi_xoa_sach():
    """Đời sau giữ; ván sau thì không — luật đổi mỗi ván nên câu hỏi cũ vô nghĩa."""
    m = Minds()
    c = _creature("L1")
    m.hunch_enabled = True
    m.hunch_of(c).apply("SET", 0, _law(), tick=0)
    m.new_match()
    assert not m.hunches, "sang VÁN mới thì linh cảm phải sạch"


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


def _run(seed: int, ticks: int, law_for_hunch, laws=None):
    """Chạy một ván thật với một linh cảm nhồi sẵn. Trả (tried, hit) cộng dồn."""
    from genesis.strategist import ReflexStrategist
    from genesis.tick import build_match, tick

    w, cs, st, rng = build_match(seed, laws=laws)
    strat = ReflexStrategist()
    strat.minds = Minds()
    strat.minds.hunch_enabled = True
    for c in cs:
        strat.minds.hunch_of(c).apply("SET", 0, law_for_hunch, tick=0)
    for t in range(ticks):
        tick(w, cs, t, rng, st, laws=laws, strategist=strat)
    es = [h for hb in strat.minds.hunches.values() for h in hb.entries() if h]
    return sum(h.tried for h in es), sum(h.hit for h in es)


def test_vong_tick_dem_dung_khi_linh_cam_TRUNG_luat_that():
    """Ca dương ở mức VÁN THẬT, không phải mức hàm.

    Nhồi đúng luật thật của ván làm linh cảm: mỗi lần trigger nổ thì hệ quả phải
    có mặt trong `happened`, nên `hit` phải bằng `tried`. Bài này bắt được cả
    một lớp lỗi mà bài đơn vị không thấy — `happened` dựng sai chỗ, hoặc dựng
    sau khi hệ quả đã bị ghi đè.
    """
    from genesis.lawgen import generate_cached

    laws = generate_cached(9, arm="STANDARD")
    tried, hit = _run(9, 200, laws[0], laws=laws)
    assert tried > 0, "200 tick mà luật thật không nổ lần nào — seed hỏng?"
    assert hit == tried, f"linh cảm TRÙNG luật thật phải đúng mọi lần: {hit}/{tried}"


def test_vong_tick_dem_SAI_khi_linh_cam_truot():
    """Ca âm ở mức ván thật: nghi sai thì `tried` vẫn lên, `hit` phải đứng yên.

    Đây là nửa giá trị của cơ chế — bằng chứng phủ định — và nó chỉ đúng nếu
    `tried` đếm cả những tick không có gì xảy ra.
    """
    from genesis.lawgen import generate_cached

    laws = generate_cached(9, arm="STANDARD")
    # Một luật KHÔNG có trong ván: cùng trigger của luật thật, sai hệ quả.
    wrong = Law(trigger=laws[0].trigger, conds=(),
                effect=Effect(kind=EffectKind.TELEPORT))
    tried, hit = _run(9, 200, wrong, laws=laws)
    assert tried > 0, "trigger vẫn phải nổ — nếu không thì bài này không kiểm gì"
    assert hit == 0, f"nghi sai mà vẫn ăn {hit} lần đúng"


# ── chế độ mở: cùng cơ chế, không có bản thứ hai (N-16 bẫy 4) ───────────────

def test_linh_cam_chay_o_che_do_mo():
    """B-14 phải đi qua `Minds`, nên nó phải chạy ở ván mở mà không sửa gì thêm.

    Đây là bài kiểm mà [N-16](../docs/tasks/N-16-ngang-bang-mang.md) mua được:
    trước khi trí nhớ gom về một chỗ, mọi tính năng mới đều phải viết hai lần và
    lần thứ hai luôn bị quên. Giờ `routes_work` chỉ tra cứu vào
    `state.runner.minds`, nên linh cảm có mặt ở chế độ mở gần như miễn phí.
    """
    from fastapi.testclient import TestClient

    from net import server, state
    from net.match import MatchRunner
    from net.routes_join import clear_rate_limits
    from net.routes_work import clear_work_state

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

    from net import server, state
    from net.match import MatchRunner
    from net.routes_join import clear_rate_limits
    from net.routes_work import clear_work_state

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


def test_bat_hunch_ma_khong_ai_neu_thi_van_chay_Y_HET(tmp_path):
    """Bất biến 6 ở mức VÁN, không chỉ ở mức prompt.

    `hunch_enabled = True` bật thêm một nhánh trong pha 4 của vòng tick — pha ấy
    giờ chạy cả khi `laws` rỗng, để `WORLD_FLAT` vẫn đếm được "đã thử và không
    có gì". Nhánh thêm vào là chỗ dễ làm lệch RNG hoặc lệch thứ tự duyệt, và
    lệch một tick là hỏng cả nhánh đối chứng của X-09.

    Bài này suýt không được viết: `x09` với model giả cho thấy ghi sổ tụt 62 -> 11
    khi bật linh cảm, trông y như linh cảm đang cướp lượt nghĩ. Chạy lại với
    nhánh đối chứng thật (bật cơ chế, không con nào nêu linh cảm) thì hai nhánh
    ra **con số giống hệt** — 18/18, 16/16, 11/11. Cú tụt kia là một ván khác
    hẳn, không phải một cơ chế hỏng.
    """
    from genesis.lawgen import generate_cached
    from genesis.logio import LogWriter
    from genesis.strategist import ReflexStrategist
    from genesis.tick import build_match, tick

    def run(enabled: bool, path):
        laws = generate_cached(9, arm="STANDARD")
        w, cs, st, rng = build_match(9, laws=laws)
        strat = ReflexStrategist()
        strat.minds = Minds()
        strat.minds.hunch_enabled = enabled
        with LogWriter(path, "m") as log:
            for t in range(120):
                tick(w, cs, t, rng, st, log=log, laws=laws, strategist=strat)
        return path.read_text(encoding="utf-8")

    a = run(False, tmp_path / "off.jsonl")
    b = run(True, tmp_path / "on.jsonl")
    assert a == b, "bật cơ chế mà không ai dùng thì ván phải giống hệt tới từng dòng"


def test_linh_cam_KHONG_BAO_GIO_cuop_luot_ghi_so():
    """Thứ tự ưu tiên là một cam kết, không phải một chi tiết.

    `codex` đứng TRƯỚC `hunch`: một kết luận đáng giá hơn một giả thuyết khi cả
    hai cùng chờ. Đảo thứ tự này là làm nhánh thí nghiệm của X-09 ghi sổ ít hơn
    nhánh đối chứng vì một lý do thuần cơ học, và kết quả sẽ đọc thành "linh cảm
    làm hỏng việc khám phá".
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "genesis" / "strategist.py").read_text(
        encoding="utf-8")
    i_codex = src.index('kind = "codex"')
    i_hunch = src.index('kind = "hunch"')
    assert i_codex < i_hunch, "`codex` phải được xét TRƯỚC `hunch`"

    src_net = (Path(__file__).resolve().parent.parent / "net" / "routes_work.py").read_text(
        encoding="utf-8")
    assert src_net.index('kind = "codex"') < src_net.index('kind = "hunch"'), \
        "đường mạng phải giữ CÙNG thứ tự ưu tiên với đường cục bộ"


def test_hoi_han_nguoi_KHONG_dung_len_mot_cuon_so_rong():
    """`hunches` có mặt = đã từng nêu một linh cảm. Đừng phá tính chất ấy.

    `hunch_of` tạo sổ khi chưa có, nên gọi nó chỉ để hỏi hạn nguội sẽ dựng một
    cuốn sổ rỗng cho MỌI cá thể ở MỌI lượt nghĩ — và cả log lẫn bài kiểm đều đọc
    `hunches` như "ai đã nêu gì".
    """
    from genesis import law_config

    m = Minds()
    c = _creature("L1")
    assert m.hunch_last_write(c.id) == -law_config.HUNCH_COOLDOWN
    assert not m.hunches, "chỉ HỎI thôi mà đã dựng sổ"
    m.hunch_of(c)
    assert c.id in m.hunches

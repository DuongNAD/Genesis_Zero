"""Genesis Zero — tests/test_n16_ngang_bang: ván cục bộ và chế độ mở phải chơi CÙNG một trò.

Phiếu [N-16] đếm bảy tính năng mà đường mạng thiếu so với đường cục bộ. Bốn cái
đầu đã vá từng cái một; ba cái cuối — dạy nhau + sổ ghi công, dịch trait, cẩm
nang — thì phiếu nói thẳng **đừng vá từng cái nữa**, mẫu đã rõ sau bốn lần: hai
bản của một khái niệm, và bản nào ít người nhìn hơn thì bản ấy mục.

Nên cách sửa là gom trạng thái về `genesis.minds.Minds`, một bản, cả hai đường
gọi vào. Các bài dưới đây kiểm **kết quả** của việc gom đó, không kiểm cách gom:
mỗi bài đều đỏ trước thay đổi này.
"""

from __future__ import annotations

import random

from fastapi.testclient import TestClient
import pytest

from genesis import config
from genesis.handbook import Handbook
from genesis.lawdsl import random_law, vocab_for_brain
from genesis.teach import law_key
from net.match import MatchRunner
from net.routes_join import clear_rate_limits
from net.routes_work import clear_work_state
from net import state
import net.server as server


@pytest.fixture(autouse=True)
def reset_state():
    clear_rate_limits()
    clear_work_state()
    yield
    clear_rate_limits()
    clear_work_state()


@pytest.fixture
def client(monkeypatch):
    # `tick_ms=1` + vòng lặp nền của `lifespan` = một cuộc đua: đồng hồ ván chạy
    # ~1000 tick/giây, nên giữa lúc `/work` phát việc và lúc `/decision` tới nơi
    # có thể trôi qua vài tick, và bài kiểm lăn ra 410 WORK_EXPIRED một cách
    # ngẫu nhiên. Không bài nào ở đây CẦN đồng hồ chạy — bài nào muốn một tick
    # cụ thể thì tự gán `r.tick_no`. Nên chặn nhịp lại: nhịp chậm cộng `step`
    # rỗng cho một ván đứng yên, và một bài kiểm đứng yên là bài kiểm đọc được.
    r = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    monkeypatch.setattr(r, "step", lambda: None)
    monkeypatch.setattr(state, "runner", r)
    with TestClient(server.app) as c:
        yield c, r


def _join_running(c, r, brain_tier=5):
    resp = c.post("/v1/join",
                  json={"display_name": "Kiến", "brain_tier": brain_tier,
                        "pop_request": 1})
    token = resp.json()["token"]
    r.advance_phase()   # -> SEEDING
    r.advance_phase()   # -> RUNNING
    return token


def _work_item(c, token):
    resp = c.get("/v1/work", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.status_code
    return resp.json()["items"][0]


# ── 1. dạy nhau + sổ ghi công ────────────────────────────────────────────────

def test_day_nhau_va_so_ghi_cong_chay_o_che_do_mo():
    """`say.teach` phải đi qua `Ledger` ở ván mở, y như ván cục bộ (B-12).

    Trước N-16, `_absorb_speech_for_clients` chỉ render chuỗi "nghe được" rồi
    dừng: phần `teach` bị bỏ hẳn, nên `Ledger` ở chế độ mở **luôn rỗng**. Hậu
    quả là toàn bộ B-12 — công chảy một nấc, chống farming, đo nói dối — không
    tồn tại ở đúng chế độ có người lạ, tức đúng chế độ có động cơ để farm.
    """
    r = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    r._seed_match()
    speaker, near, far = [c.id for c in r.creatures][:3]

    law = random_law(random.Random(7), vocab_for_brain(5))
    r.minds.codices[speaker] = r.minds.codex_of(
        next(c for c in r.creatures if c.id == speaker))
    r.minds.codices[speaker].apply("SET", 0, law, 3, tick=0)

    r._absorb_speech_for_clients([{
        "kind": "SPEAK", "creature_id": speaker,
        "signal": "NEUTRAL", "text": "nghe này", "teach": 0,
        "hear_full": [near], "hear_signal": [far],
    }])

    assert r.minds.teach_events, "ván mở phải sinh ra TeachEvent"
    key = law_key(law)
    assert r.minds.ledger.knows.get(speaker, {}).get(key) is not None, \
        "người dạy phải được ghi là đã biết luật mình dạy"
    assert r.minds.ledger.knows.get(near, {}), \
        "người nghe ĐỦ CÂU phải được ghi vào sổ cái"
    # Người nghe xa chỉ nhận bản GIẤU hệ quả — họ biết một thứ khác, không phải
    # cùng một luật. Nhầm chỗ này là phát không công cho cả bản đồ.
    assert key not in r.minds.ledger.knows.get(far, {}), \
        "người nghe xa không được coi là biết luật ĐẦY ĐỦ"


def test_dang_ky_offer_vao_khoi_nghe_duoc(client):
    """Luật được dạy phải hiện ra trong khối NGHE ĐƯỢC của prompt lượt sau."""
    c, r = client
    token = _join_running(c, r)
    speaker, hearer = [x.id for x in r.creatures][:2]
    law = random_law(random.Random(11), vocab_for_brain(5))
    cx = r.minds.codex_of(next(x for x in r.creatures if x.id == speaker))
    cx.apply("SET", 0, law, 3, tick=0)

    r._absorb_speech_for_clients([{
        "kind": "SPEAK", "creature_id": speaker,
        "signal": "NEUTRAL", "text": "nghe này", "teach": 0,
        "hear_full": [hearer], "hear_signal": [],
    }])
    assert r.minds.offers.get(hearer), "người nghe phải giữ lại lời chào hàng"


# ── 2. nói được, không chỉ nghe ─────────────────────────────────────────────

def test_say_tu_decision_toi_duoc_vong_tick(client):
    """Trường `say` có trong schema mà `/decision` không đọc = không ai nói được.

    Đây là một lỗ im lặng hoàn hảo: client gửi lên đúng schema, server trả
    `accepted: true`, và câu nói rơi vào hư không. Ở một ván mở thuần thì
    **không sinh vật nào nói được câu nào**, nên khối "nghe được" vừa vá xong
    cũng không bao giờ có gì để chứa.
    """
    c, r = client
    token = _join_running(c, r)
    item = _work_item(c, token)
    creature = next(x for x in r.creatures if x.id == item["creature_id"])
    goal = config.GOALS_BY_BRAIN[creature.traits.brain][0]
    resp = c.post("/v1/decision",
                  headers={"Authorization": f"Bearer {token}"},
                  json={"work_id": item["work_id"],
                        "payload": {"goal": goal, "ttl": 5,
                                    "say": {"signal": "ALARM", "text": "coi chừng"}}})
    assert resp.status_code == 200 and resp.json()["accepted"], resp.json()

    says = r.strategist.take_says()
    assert item["creature_id"] in says, "câu nói phải tới được vòng tick"
    assert says[item["creature_id"]].signal == "ALARM"
    # Lấy rồi là xoá: một câu nói là của MỘT tick, giữ lại thì con vật lặp đi
    # lặp lại cùng một câu suốt `ttl` của goal.
    assert not r.strategist.take_says()


def test_ghi_chu_qua_mang_duoc_sanitize(client):
    """Ghi chú của người lạ đi thẳng vào khối E lượt sau — phải qua `sanitize`.

    Đường cục bộ đã trả giá cho bài này bằng một ván gãy ở lượt 87: model chỉ
    cần viết chữ "HP" vào ghi chú là `_check_no_leak` ném `PromptLeak`. Ở chế độ
    mở thì chuỗi ấy do người lạ gõ, nên nó không còn là tai nạn mà là một nút
    bấm để giết ván của mọi người.
    """
    c, r = client
    token = _join_running(c, r)
    item = _work_item(c, token)
    creature = next(x for x in r.creatures if x.id == item["creature_id"])
    goal = config.GOALS_BY_BRAIN[creature.traits.brain][0]
    c.post("/v1/decision",
           headers={"Authorization": f"Bearer {token}"},
           json={"work_id": item["work_id"],
                 "payload": {"goal": goal, "ttl": 5, "note": "HP tụt nhanh"}})
    kept = r.minds.notepad.get(item["creature_id"], "")
    assert "HP" not in kept, f"tên lớp nội bộ lọt qua: {kept!r}"


# ── 3. dịch trait do model của người chơi chọn ──────────────────────────────

def test_dich_trait_qua_mang(client):
    """B-13 phải chạy ở chế độ mở: hướng dịch do model người chơi chọn.

    Thiếu nó thì sinh vật của người chơi rơi về giàn giáo if-else của W-12, và
    số liệu B-13 — vốn để đo **chữ ký hành vi** của một model — trộn lẫn giữa
    "model chọn" và "luật cứng chọn" mà không có cột nào phân biệt.
    """
    c, r = client
    token = _join_running(c, r)
    creature = next(x for x in r.creatures if x.id in r.strategist.slots)

    # Vòng tick xin hướng dịch: chưa có câu trả lời -> None, và xếp hàng hỏi.
    assert r.strategist.take_shift(creature) is None
    assert creature.id in r.strategist.want_shift

    item = _work_item(c, token)
    assert item["kind"] == "shift", "đến lượt hỏi thì work phải là kind=shift"
    assert set(item["json_schema"]["properties"]) >= {"from", "to"}

    frm = next(t for t in config.TRAIT_NAMES
               if getattr(creature.traits, t) > config.TRAIT_MIN)
    to = next(t for t in config.TRAIT_NAMES
              if t != frm and getattr(creature.traits, t) < config.TRAIT_MAX)
    resp = c.post("/v1/decision",
                  headers={"Authorization": f"Bearer {token}"},
                  json={"work_id": item["work_id"],
                        "payload": {"from": frm, "to": to, "why": "cần nhớ nhiều hơn"}})
    assert resp.status_code == 200 and resp.json()["accepted"], resp.json()
    assert r.strategist.take_shift(creature) == (frm, to)
    assert r.strategist.shift_why[creature.id] == "cần nhớ nhiều hơn"


def test_dich_trait_sai_thi_bo_luot_khong_hoi_lai(client):
    """Sai thì bỏ lượt, KHÔNG thử lại — thử lại là ưu đãi cho con hay sai."""
    c, r = client
    token = _join_running(c, r)
    creature = next(x for x in r.creatures if x.id in r.strategist.slots)
    r.strategist.take_shift(creature)
    item = _work_item(c, token)
    resp = c.post("/v1/decision",
                  headers={"Authorization": f"Bearer {token}"},
                  json={"work_id": item["work_id"],
                        "payload": {"from": "khong_co_trait_nay", "to": "brain"}})
    assert resp.status_code == 200 and not resp.json()["accepted"]
    # Cùng mức `adapt_points` thì không được hỏi lại.
    assert r.strategist.take_shift(creature) is None
    assert creature.id not in r.strategist.want_shift


def test_bot_cua_server_khong_bi_coi_la_co_model(client):
    """`slots` chỉ chứa sinh vật của NGƯỜI. Bot phải rơi về W-12.

    Nhầm chỗ này thì bot chờ một câu trả lời không bao giờ tới và **bỏ luôn
    lượt dịch trait của mình** — im lặng, không log, chỉ là một quần thể bot
    đứng yên về mặt tiến hoá.
    """
    c, r = client
    _join_running(c, r)
    player_species = {x.species for x in r.creatures if x.id in r.strategist.slots}
    assert player_species, "phải có ít nhất một loài của người chơi"
    for x in r.creatures:
        if x.species not in player_species:
            assert x.id not in r.strategist.slots


# ── 4. cẩm nang sống qua nhiều ván ──────────────────────────────────────────

def test_cam_nang_vao_prompt_o_che_do_mo(client):
    """W-16 bất biến 4: cẩm nang vào SYSTEM. Ở ván mở nó từng không vào đâu cả.

    Chế độ mở là chỗ **duy nhất** mà cùng một người chơi thật sự chơi nhiều ván
    liên tiếp, nên nó từng là chế độ duy nhất không có trí nhớ qua ván — đúng
    ngược lại.
    """
    c, r = client
    token = _join_running(c, r)
    species = next(x.species for x in r.creatures if x.id in r.strategist.slots)

    hb = Handbook(species_id=species, n_matches=4)
    hb.add("Đổi một thứ một lúc, đổi hai thì không quy được nhân quả.")
    r.handbooks[species] = hb
    r._load_handbooks()

    brief = c.get("/v1/match/brief", headers={"Authorization": f"Bearer {token}"})
    assert brief.status_code == 200
    sys_prompts = [v["system_prompt"] for v in brief.json()["creatures"].values()]
    assert any("[CẨM NANG]" in p for p in sys_prompts), "cẩm nang không vào SYSTEM"


def test_cam_nang_song_qua_van_con_so_tay_thi_khong():
    """Ranh giới hai tầng trí nhớ, ngay tại `_seed_match`.

    Sổ tay và Sổ Luật là của MỘT ván — mang sang là chép đáp án, mà luật đổi mỗi
    ván nên đáp án cũ vừa sai vừa làm phép đo mất nghĩa. Cẩm nang chứa **cách
    tìm**, và cách tìm thì đáng sống qua nhiều thế giới.
    """
    r = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    r._seed_match()
    cid = r.creatures[0].id
    species = r.creatures[0].species
    r.minds.notepad[cid] = "ghi chú của ván cũ"
    r.minds.handbooks[species] = "[CẨM NANG] ..."
    hb = Handbook(species_id=species)
    hb.add("Chuyện không xảy ra cũng là bằng chứng.")
    r.handbooks[species] = hb
    n_before = hb.n_matches

    r._seed_match()
    assert not r.minds.notepad, "ghi chú phải chết theo ván"
    assert r.minds.handbooks.get(species), "cẩm nang phải sống qua ván"
    assert hb.n_matches == n_before + 1, "mỗi ván tính một thế giới đã sống qua"


# ── 5. canh chừng: đừng để mọc lại bản thứ hai ──────────────────────────────

def test_routes_work_khong_giu_ban_sao_tri_nho():
    """Bài canh chừng, không phải bài chức năng.

    Cả N-16 là một lỗi lặp lại bốn lần với bốn triệu chứng khác nhau, và mỗi lần
    đều bắt đầu bằng một dict cấp module trông rất vô hại ở `routes_work`. Bài
    này đỏ ngay lúc ai đó dựng lại cuốn sổ thứ hai, thay vì sáu tháng sau khi có
    người ngồi so hai file.
    """
    from pathlib import Path

    src = (Path(__file__).resolve().parent.parent / "net" / "routes_work.py").read_text(
        encoding="utf-8")
    for name in ("_notes", "_codices", "_notepads", "_want_codex", "_heard",
                 "_reputation", "_ledger", "_handbooks"):
        assert f"{name}:" not in src and f"{name} =" not in src, (
            f"`{name}` ở cấp module là bản sao thứ hai của `Minds.{name.lstrip('_')}` "
            f"— trạng thái trí nhớ thuộc về `state.runner.minds`")


def test_loai_cua_NGUOI_LA_cung_co_ba_dac_diem():
    """W-19 ở chế độ mở — và nó là họ lỗi N-16 mọc lại lần thứ chín.

    `build_match` gán `world.kits` cho các loài có mặt lúc dựng thế giới, mà
    sinh vật của người chơi ra đời SAU đó ở `_spawn_registered`. Thiếu một dòng
    thì loài đăng ký qua mạng **không có đặc điểm nào**: không hệ số hao sức,
    không gai, không vào được hang, và mô tả 3D thiếu hẳn một lớp.

    Bot có, người chơi không. Đúng thứ [N-16] tồn tại để dọn — và nó mọc lại
    **ngay lần đầu** ta thêm một khái niệm mới vào thế giới. Bài kiểm này là để
    lần thứ mười có người bắt được trước khi mở tunnel.
    """
    from genesis.features import N_FEATURES
    from genesis.traits import founder_traits
    from net.match import MatchRunner, Registration

    r = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    r._seed_match()
    r.registrations["c1"] = Registration(
        client_id="c1", token="t", species_id="ZZ", display_name="Lạ",
        persona="", league="A", brain_tier=5, pop=2,
        traits=founder_traits("L1"))
    r._spawn_registered()

    kit = r.world.kits.get("ZZ")
    assert kit is not None, "loài của người lạ không có đặc điểm nào"
    assert len(kit.features) == N_FEATURES

    # Tất định: người chơi vào lại cùng một ván thì vẫn là con vật ấy.
    r2 = MatchRunner(seed=1, ticks=10, tick_ms=10_000, log_dir=None)
    r2._seed_match()
    r2.seed = r.seed
    r2.registrations["c1"] = r.registrations["c1"]
    r2._spawn_registered()
    assert ([f.key for f in kit.features]
            == [f.key for f in r2.world.kits["ZZ"].features])

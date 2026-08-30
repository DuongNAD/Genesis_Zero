"""Genesis Zero — W-17: chết là truyền lại, không phải ngủ dậy."""

from __future__ import annotations

import random

import pytest

from genesis import config
from genesis.codex import Codex
from genesis.creature import Creature
from genesis.fieldnotes import FieldNotes, Note
from genesis.lawdsl import random_law, vocab_for_brain
from genesis.lineage import CAUSE_BIAS, forget_on_death, inherit, rebirth
from genesis.traits import Traits, founder_traits


def _tong(t: Traits) -> int:
    return sum(getattr(t, n) for n in config.TRAIT_NAMES)


@pytest.mark.parametrize("sp", ["L1", "L2", "L3", "L4", "L5"])
@pytest.mark.parametrize("cause", ["starve", "combat", "poison"])
def test_ngan_sach_trait_bat_bien_qua_moi_doi(sp, cause):
    """Đột biến KHÔNG được in thêm điểm. Tổng luôn 12, mỗi trait luôn trong [0,5].

    Ngân sách trait là bộ chống gian lận: đòi `brain=5` thì phải trả bằng mọi
    thứ khác. Một đường rò ở đây làm mọi thứ khác vô nghĩa.
    """
    t = founder_traits(sp)
    for _ in range(40):
        t = inherit(t, cause, random.Random(0))
        assert _tong(t) == config.TRAIT_SUM
        for n in config.TRAIT_NAMES:
            assert config.TRAIT_MIN <= getattr(t, n) <= config.TRAIT_MAX


@pytest.mark.parametrize("cause", ["starve", "combat", "poison"])
def test_chet_khong_bao_gio_an_vao_brain(cause):
    """`brain` không bao giờ là nguồn cho đột biến.

    `brain` là trait cao nhất ở ba trong năm loài dựng sẵn, nên để nó làm nguồn
    thì mỗi cái chết là một khoản thuế đánh vào đầu óc: L1 (brain 4) tụt về
    brain 0 sau bốn lần chết, mà một ván có **64 lượt chết**.

    Nó phá đúng thứ dự án sinh ra để đo: brain quyết định từ vựng Sổ Luật
    (`ADJACENT`/`PHASE_ENTER` chỉ có từ brain 4), số ô sổ và ngân sách token.
    Thân xác trôi theo thứ giết nó; đầu óc thì không.
    """
    for sp in ("L1", "L2", "L3", "L4", "L5"):
        t = founder_traits(sp)
        brain0 = t.brain
        for _ in range(30):
            t = inherit(t, cause, random.Random(0))
        assert t.brain == brain0, f"{sp} mất brain sau 30 đời chết vì {cause}"


def test_than_xac_troi_ve_phia_thu_giet_no():
    """Chết đói nhiều đời -> bụng to dần. Đó là bản ghi đọc được bằng mắt."""
    t = founder_traits("L1")
    truoc = t.stomach
    for _ in range(3):
        t = inherit(t, "starve", random.Random(0))
    assert t.stomach > truoc

    t2 = founder_traits("L1")
    truoc2 = t2.armor + t2.attack
    for _ in range(3):
        t2 = inherit(t2, "combat", random.Random(0))
    assert t2.armor + t2.attack > truoc2


def test_dot_bien_tat_dinh():
    """Cùng bố mẹ + cùng nguyên nhân -> cùng đời sau. Ván phải tái lập từ seed."""
    t = founder_traits("L3")
    a = inherit(t, "poison", random.Random(1))
    b = inherit(t, "poison", random.Random(999))
    assert a == b


def test_nguyen_nhan_la_thi_khong_doi_gi():
    """Đột biến là món quà, không phải thuế — không biết lệch đâu thì đừng lệch."""
    t = founder_traits("L2")
    assert inherit(t, None, random.Random(0)) == t
    assert inherit(t, "sét đánh", random.Random(0)) == t


def test_bao_hoa_thi_dung_lai_chu_khong_gay():
    """Trait đích chạm trần thì trả nguyên vector, không cướp điểm vô ích."""
    t = Traits(brain=4, attack=0, armor=1, speed=1, sense=1, stomach=5)
    assert inherit(t, "starve", random.Random(0)) == t


def test_rebirth_giu_id_va_tang_doi():
    """`id` định danh DÒNG DÕI, không phải cá thể — giữ nguyên qua các đời.

    Đổi id mỗi lần chết thì khe prefix cache, khoá Sổ Luật, sổ ghi công và đường
    replay phải dựng lại 64 lần một ván.
    """
    t = founder_traits("L1")
    c = Creature(id="L1:0", species="L1", traits=t, pos=(1, 1), hp=0.0, energy=0.0)
    c.adapt_points = 3
    c.shift_log.append(("brain", "speed"))
    truoc = rebirth(c, "starve", random.Random(0))
    assert c.id == "L1:0"
    assert c.generation == 1
    assert truoc == t and c.traits != t
    assert c.adapt_points == 0 and not c.shift_log


def test_chi_thu_da_VIET_moi_song_qua_cai_chet():
    """Sổ tay chết theo; Sổ Luật đi tiếp nhưng bớt chắc chắn.

    Đây là mấu chốt của cả cơ chế. Hiện Sổ Luật chỉ là tiện nghi — ghi hay không
    thì trí nhớ vẫn nguyên. Từ đây, **không ghi là mất thật**, và đó đúng là cái
    nút Qwen-7B bỏ quên suốt ván (0% mục sổ nói về uống nước, trong khi uống
    chiếm 26% hành động).
    """
    fn = FieldNotes(cap=8)
    cx = Codex(size=2)
    law = random_law(random.Random(1), vocab_for_brain(5))
    cx.apply("SET", 0, law, 3, tick=99)
    fn.record(Note(t=1, who="TÔI", action="uống nước",
                   outcome="máu tụt hẳn xuống", ctx=()))
    assert fn.render(8).strip()

    forget_on_death(fn, cx)
    assert not fn.render(8).strip(), "sổ tay phải CHẾT THEO"
    assert cx._entries[0] is not None, "Sổ Luật phải ĐI TIẾP"
    assert cx._entries[0].conf == 3 - config.CODEX_CONF_DECAY_PER_GEN

    for _ in range(5):
        forget_on_death(fn, cx)
    assert cx._entries[0] is None, "đoán may phải TÀN sau vài đời"


def test_forget_chiu_duoc_None():
    """Cả hai đường chạy đều có ca chưa kịp dựng sổ — không được ném."""
    assert forget_on_death(None, None) == 0


def test_moi_nhom_nguyen_nhan_deu_co_dich_hop_le():
    for cause, targets in CAUSE_BIAS.items():
        assert targets
        for t in targets:
            assert t in config.TRAIT_NAMES
        assert "brain" not in targets, "brain không phải thứ để lệch tới"


def test_duong_mang_cung_quen_nhu_duong_cuc_bo():
    """Chế độ mở phải quên GIỐNG HỆT ván cục bộ khi sang đời mới.

    Đường cục bộ làm việc này trong `strategist.observe`, nhưng ở chế độ mở sổ
    tay và Sổ Luật nằm ở `runner.minds`, và `RemoteClientStrategist` không có
    `observe`. Thiếu móc thì sinh vật qua mạng **giữ nguyên sổ tay thô qua mọi
    đời** — ngược hẳn thiết kế.

    Lần thứ ba cùng một họ lỗi: hai đường chạy, một đường bị bỏ quên. Trước đó
    là `schema_for` (thiếu `targets` lẫn `sm`) và `founder_traits` (không biết
    loài đăng ký lúc chạy).
    """
    from genesis.lawdsl import random_law, vocab_for_brain
    from net.match import MatchRunner

    r = MatchRunner(seed=1, ticks=5, tick_ms=1, log_dir=None)
    fn = FieldNotes(cap=8)
    fn.record(Note(t=1, who="TÔI", action="uống nước",
                   outcome="máu tụt hẳn xuống", ctx=()))
    cx = Codex(size=2)
    cx.apply("SET", 0, random_law(random.Random(1), vocab_for_brain(5)), 3, tick=99)

    # Một chỗ chứa, không hai: sổ tay của ván mở nằm ở `runner.minds`, đúng
    # cùng lớp mà `LlmStrategist` dùng (N-16).
    r.minds.notes["L1:0"] = fn
    r.minds.codices["L1:0"] = cx
    try:
        r._forget_for_dead([{"kind": "DEATH", "creature_id": "L1:0"}])
        assert not fn.render(8).strip(), "sổ tay qua mạng phải CHẾT THEO"
        assert cx._entries[0].conf == 3 - config.CODEX_CONF_DECAY_PER_GEN
    finally:
        r.minds.clear()

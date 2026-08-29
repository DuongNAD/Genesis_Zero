"""Genesis Zero — Gate D: luật phải PHÁT BIỂU ĐƯỢC (L-05)."""

from __future__ import annotations

import pytest

from genesis import law_config as lc
from genesis.lawdsl import Cond, CondKind, Effect, EffectKind, Law, Trigger, TriggerKind
from genesis.lawgen import generate_cached, min_founder_brain, statable


def test_statable_bam_dung_tu_vung_theo_brain():
    """`ADJACENT` chỉ có từ brain 4. Brain 0–3 không nói ra được."""
    law = Law(
        trigger=Trigger(kind=TriggerKind.ADJACENT, arg="OTHER_SP", n=1),
        conds=(),
        effect=Effect(kind=EffectKind.POISON),
    )
    assert not statable(law, 0)
    assert not statable(law, 3)
    assert statable(law, 4)


def test_statable_dem_ca_so_dieu_kien():
    """Brain 0–1 có `max_conds = 0` — một luật có điều kiện là không nói được."""
    law = Law(
        trigger=Trigger(kind=TriggerKind.DRINK),
        conds=(Cond(kind=CondKind.PHASE, arg="NIGHT"),),
        effect=Effect(kind=EffectKind.DAMAGE),
    )
    assert not statable(law, 0)
    assert statable(law, 4)


def test_luat_khong_dieu_kien_co_ban_thi_ai_cung_noi_duoc():
    law = Law(
        trigger=Trigger(kind=TriggerKind.DRINK),
        conds=(),
        effect=Effect(kind=EffectKind.DAMAGE),
    )
    for b in range(6):
        assert statable(law, b), f"brain {b} phải nói được luật D1 cơ bản"


@pytest.mark.parametrize("seed", list(range(12)))
def test_moi_van_deu_co_it_nhat_mot_muc_tieu_cho_con_nao_nho_nhat(seed):
    """Con não nhỏ nhất phải luôn có ÍT NHẤT một luật nhắm được.

    Trước Gate D: **16/40 seed** không có luật nào brain 0 phát biểu nổi — ba
    con L5 chịu hệ quả suốt ván và không cách nào ghi vào Sổ Luật. Ván seed 55
    là ca xấu nhất: `ADJACENT(OTHER_SP) -> POISON` nổ **324 lần**, nhiều nhất
    ván, và **4/5 loài** không có chữ `ADJACENT` trong từ vựng.

    Đây là song sinh của Gate A: Gate A chặn luật không NHÌN thấy được, Gate D
    chặn ván mà thí sinh yếu nhất không NÓI được gì.
    """
    laws = generate_cached(seed, "STANDARD")
    n = sum(statable(l, min_founder_brain()) for l in laws)
    assert n >= lc.LAWSET_MIN_STATABLE, (
        f"seed {seed}: brain {min_founder_brain()} không phát biểu được luật nào "
        f"trong {len(laws)} luật"
    )


def test_gate_d_khong_xoa_phan_thuong_tu_vung_cua_brain():
    """Gate D ràng ở mức BỘ, không mọi luật — nếu không thì brain hết đáng giá.

    Bắt MỌI luật nói được ở brain 0 sẽ ép cả ván về 5 trigger và 0 điều kiện.
    Từ vựng rộng hơn chính là thứ brain đổi lấy bằng 4 điểm trait, nên phải còn
    những ván có luật mà chỉ loài não to phát biểu nổi.
    """
    rieng = 0
    for seed in range(20):
        laws = generate_cached(seed, "STANDARD")
        if any(not statable(l, 0) and statable(l, 5) for l in laws):
            rieng += 1
    assert rieng > 0, "không ván nào có luật riêng cho loài não to -> brain mất giá"

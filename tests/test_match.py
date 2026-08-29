"""Genesis Zero — TÁM CA BẮT BUỘC cho match() (L-06).

Đây là hàm quyết định mọi kết luận của dự án. Sai một cách tinh vi thì nó cho ra
SỐ ĐẸP và mọi thứ phía sau sai mà không ai biết. Hai ca có dấu ★ là hai đầu kẹp
lấy thang đo — không đạt thì KHÔNG được đi tiếp (docs/tasks/L-06-match.md).
"""

from __future__ import annotations

import random

from genesis.lawdsl import (
    Cond, CondKind, Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind, random_law,
)
from genesis.situations import sample_situations
from genesis.verify import ADJACENT_BUCKET_SCORE, agree, match

_T = Trigger(TriggerKind.EAT, "FRUIT_A")
_C1 = Cond(CondKind.PHASE, "NIGHT")
_C2 = Cond(CondKind.HP, "LOW")
_E = Effect(EffectKind.POISON, Mag.MED, Dur.LONG)

TRUTH = Law(_T, (_C1, _C2), _E)
SITS = sample_situations(TRUTH, 400, random.Random(11))


def test_ordering_across_all_cases() -> None:
    """Ràng buộc thật của thang đo: THỨ TỰ giữa các ca, không phải con số tuyệt đối."""
    exact = match(TRUTH, TRUTH, SITS)
    one_bucket = match(Law(_T, (_C1, _C2), Effect(EffectKind.POISON, Mag.BIG, Dur.LONG)), TRUTH, SITS)
    drop_one = match(Law(_T, (_C1,), _E), TRUTH, SITS)
    wrong_eff = match(Law(_T, (_C1, _C2), Effect(EffectKind.HEAL, Mag.MED, Dur.LONG)), TRUTH, SITS)
    assert exact > one_bucket > drop_one > wrong_eff


def test_a_exact_match() -> None:
    """(a) trùng khít -> 1.0"""
    assert match(TRUTH, TRUTH, SITS) == 1.0


def test_b_same_behaviour_different_syntax() -> None:
    """★ (b) khác cú pháp, cùng hành vi -> 1.0.

    Hỏng ca này = chấm oan người ĐÚNG, và mọi so sánh giữa các model thành nhiễu.
    """
    swapped = Law(_T, (_C2, _C1), _E)          # AND đảo thứ tự
    assert match(swapped, TRUTH, SITS) == 1.0


def test_c_partial_credit_is_monotone() -> None:
    """(c) điểm từng phần phải ĐƠN ĐIỆU theo mức độ đúng.

    Phiếu L-06 đoán "đúng trigger, sai cond -> 0.4–0.6". Đo thật thì phải tách hai
    trường hợp, và điều RÀNG BUỘC là THỨ TỰ chứ không phải con số:
      bỏ MỘT trong hai cond  -> 0.66   (còn giữ được một nửa luật)
      bỏ CẢ HAI cond         -> 0.00   (tầng near_miss 40% phạt đúng kiểu
                                        "đoán trigger, kệ cond" — docs/03 §5.6)
    """
    drop_one = match(Law(_T, (_C1,), _E), TRUTH, SITS)
    drop_both = match(Law(_T, (), _E), TRUTH, SITS)
    assert 0.55 <= drop_one <= 0.75, drop_one
    assert drop_both <= 0.05, drop_both
    assert drop_one > drop_both


def test_d_right_trigger_and_cond_wrong_effect() -> None:
    """(d) đúng trigger + cond, sai hệ quả -> <= 0.3"""
    m = match(Law(_T, (_C1, _C2), Effect(EffectKind.HEAL, Mag.MED, Dur.LONG)), TRUTH, SITS)
    assert m <= 0.3, m


def test_e_null_hypothesis_scores_zero() -> None:
    """(e) giả thuyết NULL -> đúng 0.0.

    Không chuẩn hoá theo null thì luật kích hoạt cực hiếm ăn ~0.9 điểm.
    """
    never = Law(Trigger(TriggerKind.LOW_ENERGY), (Cond(CondKind.ALONE, r=2),),
                Effect(EffectKind.STUN, dur=Dur.SHORT))
    assert match(never, TRUTH, SITS) == 0.0


def test_f_random_laws_score_near_zero() -> None:
    """★ (f) 1000 luật ngẫu nhiên -> trung bình <= 0.15.

    Hỏng ca này = đoán bừa CÓ điểm, và toàn bộ RL ở track R sẽ đi tối ưu vào đúng đó.
    """
    rng = random.Random(5)
    scores = [match(random_law(rng), TRUTH, SITS) for _ in range(1000)]
    mean = sum(scores) / len(scores)
    assert mean <= 0.15, mean
    assert max(scores) < 1.0, max(scores)


def test_g_one_magnitude_bucket_off() -> None:
    """(g) đúng hết, lệch ĐÚNG một rổ độ lớn -> 0.80–0.90"""
    m = match(Law(_T, (_C1, _C2), Effect(EffectKind.POISON, Mag.BIG, Dur.LONG)), TRUTH, SITS)
    assert 0.80 <= m <= 0.90, m
    # lệch CẢ HAI chiều thì phải thấp hơn lệch một chiều
    both = match(Law(_T, (_C1, _C2), Effect(EffectKind.POISON, Mag.BIG, Dur.SHORT)), TRUTH, SITS)
    assert both < m, (both, m)


def test_h_right_effect_wrong_trigger() -> None:
    """(h) đúng hệ quả, sai hoàn toàn trigger -> <= 0.2"""
    m = match(Law(Trigger(TriggerKind.DRINK), (_C1, _C2), _E), TRUTH, SITS)
    assert m <= 0.2, m


def test_bucket_adjacency_table() -> None:
    """SMALL liền kề MED, MED liền kề BIG, SMALL KHÔNG liền kề BIG."""
    def e(m): return Effect(EffectKind.DAMAGE, m, Dur.INSTANT)
    assert agree(e(Mag.MED), e(Mag.MED)) == 1.0
    assert agree(e(Mag.SMALL), e(Mag.MED)) == ADJACENT_BUCKET_SCORE
    assert agree(e(Mag.MED), e(Mag.BIG)) == ADJACENT_BUCKET_SCORE
    assert agree(e(Mag.SMALL), e(Mag.BIG)) == 0.0
    assert agree(None, None) == 1.0
    assert agree(None, e(Mag.MED)) == 0.0
    assert agree(e(Mag.MED), None) == 0.0
    assert agree(Effect(EffectKind.HEAL, Mag.MED, Dur.INSTANT), e(Mag.MED)) == 0.0

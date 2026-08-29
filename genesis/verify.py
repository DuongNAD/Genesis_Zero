"""Genesis Zero v5 — verify: chấm luật bằng BẢNG CHÂN TRỊ, không bằng cú pháp.

Hai luật bằng nhau khi chúng cho CÙNG KẾT QUẢ trên CÙNG tình huống. Không cần
canonicalizer, không cần luật viết lại, không cần xử lý giao hoán của AND — điểm
từng phần rơi ra tự nhiên: đoán đúng trigger sai điều kiện được ~0.5, không phải 0.

Ranh giới bắt buộc (docs/03 §5.6): file này KHÔNG import `world.py`, `creature.py`,
`tick.py`. Nó nhận `Law` + `Situation` và trả số. Nhờ vậy vòng tick không bao giờ
chạm được vào bảng chấm — "dò verifier" là bất khả theo kiến trúc, không theo lời hứa.
"""

from __future__ import annotations

from genesis.lawdsl import Dur, Effect, Law, Mag
from genesis.laweval import LawEvent, evaluate

# Rổ liền kề. Bẫy: SMALL liền kề MED, MED liền kề BIG, nhưng SMALL KHÔNG liền kề BIG.
# Viết bảng tường minh — tính bằng chỉ số enum thì thêm một rổ là có bug im lặng.
_MAG_ADJACENT: frozenset[frozenset[Mag]] = frozenset({
    frozenset({Mag.SMALL, Mag.MED}),
    frozenset({Mag.MED, Mag.BIG}),
})
_DUR_ADJACENT: frozenset[frozenset[Dur]] = frozenset({
    frozenset({Dur.INSTANT, Dur.SHORT}),
    frozenset({Dur.SHORT, Dur.LONG}),
})


# Điểm cho việc lệch ĐÚNG một rổ. Chọn 0.85 chứ không phải 0.5, vì thứ tự giữa các ca
# phải đúng: "đúng hết, lệch một rổ độ lớn" là câu trả lời TỐT HƠN HẲN "sai hẳn điều
# kiện". Với 0.5 thì hai ca cho điểm bằng nhau — thang đo mất trật tự.
# (docs/03 §5.3 viết 0.5; phiếu L-06 §6 đòi ca (g) ra 0.80–0.90. Hai chỗ mâu thuẫn;
#  giữ phiếu vì nó ràng buộc thứ tự, và sửa §5.3.)
ADJACENT_BUCKET_SCORE = 0.85


def _bucket_score(a, b, adjacent: frozenset[frozenset]) -> float:
    """1.0 trùng rổ · ADJACENT_BUCKET_SCORE lệch ĐÚNG một rổ · 0.0 còn lại."""
    if a == b:
        return 1.0
    if a is None or b is None:
        return 0.0
    return ADJACENT_BUCKET_SCORE if frozenset({a, b}) in adjacent else 0.0


def agree(a: Effect | None, b: Effect | None) -> float:
    """Mức đồng ý giữa hai hệ quả, 0..1.

    None vs None = 1.0 (cùng dự đoán "không có gì xảy ra").
    None vs có   = 0.0.
    Khác `kind`  = 0.0 — sai loại hệ quả là sai hẳn.
    Cùng `kind`  = trung bình điểm rổ trên các chiều mà `b` (luật THẬT) có định nghĩa.
    """
    if a is None and b is None:
        return 1.0
    if a is None or b is None:
        return 0.0
    if a.kind != b.kind:
        return 0.0
    scores: list[float] = []
    if b.mag is not None:
        scores.append(_bucket_score(a.mag, b.mag, _MAG_ADJACENT))
    if b.dur is not None:
        scores.append(_bucket_score(a.dur, b.dur, _DUR_ADJACENT))
    if not scores:
        return 1.0
    # TÍCH, không phải trung bình: mỗi chiều đều phải đúng. Lệch cả hai chiều thì
    # phạt nặng hơn lệch một chiều, đúng như trực giác.
    out = 1.0
    for s in scores:
        out *= s
    return out


def match(claimed: Law, truth: Law, situations: list[LawEvent]) -> float:
    """Điểm khớp 0..1 giữa luật agent phát biểu và luật thật.

        acc   = trung bình agree(claimed(s), truth(s))
        acc0  = trung bình agree(None,       truth(s))     # giả thuyết NULL
        match = clip((acc - acc0) / (1 - acc0), 0, 1)

    Chuẩn hoá theo null là BẮT BUỘC. Không có nó, một agent ghi luật kích hoạt cực
    hiếm sẽ ăn ~0.9 điểm chỉ vì "hầu như luôn đúng rằng chẳng có gì xảy ra".
    Với chuẩn hoá, giả thuyết null ăn đúng 0.
    """
    if not situations:
        return 0.0
    n = len(situations)
    acc = sum(agree(evaluate(claimed, s), evaluate(truth, s)) for s in situations) / n
    acc0 = sum(agree(None, evaluate(truth, s)) for s in situations) / n
    if acc0 >= 1.0:
        # Luật thật không kích hoạt ở đâu cả -> thang đo suy biến, không chấm được.
        return 0.0
    return max(0.0, min(1.0, (acc - acc0) / (1.0 - acc0)))

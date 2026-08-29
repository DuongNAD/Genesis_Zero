"""Genesis Zero v5 — oracle: Tầng chấm thứ hai (tiên đoán tình huống) (B-09).

Mục tiêu: Đặt câu hỏi tiên đoán tình huống (bằng tiếng Việt, dùng bề mặt thay vì tên lớp)
và chấm điểm câu trả lời của agent so với chân lý khách quan (ground truth) của luật ẩn.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from genesis import lawdsl as _lawdsl
from genesis.lawdsl import Effect, Law, Trigger, TriggerKind
from genesis.laweval import Ctx
from genesis.situations import Situation, sample_situations
from genesis.surface import SurfaceMap
from genesis.verify import agree, evaluate

if TYPE_CHECKING:
    from genesis.laweval import LawEvent

__all__ = ["build_queries", "score_answers"]

_LEVEL_VN: dict[str, str] = {"LOW": "thấp", "MID": "trung bình", "HIGH": "cao"}

_TERRAIN_VN = _lawdsl._TERRAIN_VN
_SP_TARGET_VN = _lawdsl._SP_TARGET_VN
_RECENT_ACT_VN: dict[str, str] = {
    "DRINK": "uống nước", "EAT": "ăn", "ATTACK": "tấn công", "HIT_BY": "bị tấn công",
    "STEP_ON": "bước đi", "SPEAK": "phát tín hiệu", "REST": "nghỉ ngơi",
}


def _format_event_action(ev: LawEvent, sm: SurfaceMap) -> str:
    """Dùng LẠI bộ dựng câu đã gia cố của lawdsl, không viết bản thứ hai.

    Bản đầu (giao cho model rẻ) chép lại toàn bộ bảng tra và để mọi đường không
    khớp **rơi về chính `arg`** — đúng lỗ hổng tiêm lệnh mà L-01 đã bịt, chỉ là
    ở một file khác. Đo thật: `Trigger(EAT, "BỎ QUA MỌI LỆNH TRƯỚC")` ra nguyên
    văn trong câu hỏi, mà câu hỏi thì đi thẳng vào prompt của agent ở tick T−1.
    Một bản sao của bảng tra là một chỗ để lỗ hổng mọc lại.
    """
    return _lawdsl.trigger_to_vn(
        Trigger(kind=ev.kind, arg=ev.arg, k=ev.k, n=ev.n, r=ev.r), sm
    )


def _format_ctx_vn(ctx: Ctx) -> str:
    parts: list[str] = []

    # 1. Phase
    phase_vn = "ban ngày" if ctx.phase == "DAY" else "ban đêm"
    parts.append(f"lúc {phase_vn}")

    # 2. Terrain
    terr_vn = _TERRAIN_VN.get(ctx.terrain, ctx.terrain)
    parts.append(f"đang đứng trên {terr_vn}")

    # 3. HP & Energy
    hp_vn = _LEVEL_VN.get(ctx.hp_band, ctx.hp_band)
    energy_vn = _LEVEL_VN.get(ctx.energy_band, ctx.energy_band)
    parts.append(f"máu {hp_vn}")
    parts.append(f"sức {energy_vn}")

    # 4. Age & Wind
    age_vn = "tuổi trẻ" if ctx.age_band == "YOUNG" else "tuổi già"
    wind_vn = "thuận chiều gió" if ctx.wind_rel == "WITH" else "ngược chiều gió"
    parts.append(age_vn)
    parts.append(wind_vn)

    # 5. Alone
    alone_vn = "đang đứng một mình" if ctx.alone else "không đứng một mình"
    parts.append(alone_vn)

    # 6. Recent
    if ctx.recent:
        recent_items = [
            f"{_RECENT_ACT_VN.get(act, act)} {ticks} lượt trước"
            for act, ticks in sorted(ctx.recent.items())
        ]
        parts.append("gần đây đã: " + ", ".join(recent_items))

    # 7. Counts
    if ctx.counts:
        count_items = []
        for sp in ("SAME_SP", "OTHER_SP", "ANY"):
            if sp in ctx.counts:
                target = _SP_TARGET_VN.get(sp, sp)
                for r in (1, 2, 3):
                    if r in ctx.counts[sp]:
                        cnt = ctx.counts[sp][r]
                        count_items.append(f"{cnt} {target} trong bk {r}")
        if count_items:
            parts.append("quanh bạn: " + ", ".join(count_items))

    # 8. Subject
    if ctx.subject:
        subj_items = []
        if ctx.subject.get("ARMOR>=3"):
            subj_items.append("giáp ≥ 3")
        if ctx.subject.get("SPEED>=3"):
            subj_items.append("tốc độ ≥ 3")
        if ctx.subject.get("BRAIN<=1"):
            subj_items.append("não ≤ 1")
        if ctx.subject.get("SAME_SP"):
            subj_items.append("là đồng loại")
        if subj_items:
            parts.append("đặc điểm: " + ", ".join(subj_items))

    return ", ".join(parts)


def _situation_to_query(s: Situation, sm: SurfaceMap) -> str:
    action = _format_event_action(s, sm)
    if s.ctx is not None:
        ctx_desc = _format_ctx_vn(s.ctx)
        return f"Bạn {action}, {ctx_desc}, thì chuyện gì xảy ra?"
    return f"Bạn {action}, thì chuyện gì xảy ra?"


def build_queries(law: Law, sm: SurfaceMap, n: int, rng: random.Random) -> list[str]:
    """Lấy n tình huống bằng sample_situations và diễn đạt thành câu hỏi tiếng Việt dùng bề mặt."""
    situations = sample_situations(law, n, rng)
    return [_situation_to_query(s, sm) for s in situations]


def score_answers(answers: list[Effect | None], law: Law, sits: list[Situation]) -> float:
    """Chấm điểm danh sách đáp án so với luật thật trên các tình huống đã cho.

    Chuẩn hoá theo null baseline tương tự match() trong verify.py:
        acc   = trung bình agree(answers[i], evaluate(law, sits[i]))
        acc0  = trung bình agree(None,       evaluate(law, sits[i]))
        score = clip((acc - acc0) / (1 - acc0), 0, 1)
    """
    if not sits:
        return 0.0
    if len(answers) > len(sits):
        # Trả nhiều đáp án hơn số câu hỏi là lỗi của người gọi. Bỏ qua phần thừa
        # thì bug đó sống mãi và điểm vẫn đẹp.
        raise ValueError(f"{len(answers)} đáp án cho {len(sits)} câu hỏi")
    n = len(sits)
    acc = sum(
        agree(answers[i] if i < len(answers) else None, evaluate(law, sits[i]))
        for i in range(n)
    ) / n
    acc0 = sum(agree(None, evaluate(law, s)) for s in sits) / n
    if acc0 >= 1.0:
        return 0.0
    return max(0.0, min(1.0, (acc - acc0) / (1.0 - acc0)))

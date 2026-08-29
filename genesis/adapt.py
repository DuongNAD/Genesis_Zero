"""Genesis Zero — adapt: cơ chế thích nghi và dịch trait."""

from __future__ import annotations

import random

from genesis import config
from genesis.creature import Creature
from genesis.traits import founder_traits


def award_adapt(c: Creature, reason: str) -> int:
    """reason in {"eat","win","survive"}. Cộng bộ đếm, trả số adapt_point VỪA được thêm."""
    if reason == "eat":
        c.eat_count += 1
        if c.eat_count % config.ADAPT_ON_EAT == 0:
            c.adapt_points += 1
            return 1
        return 0
    elif reason == "win":
        c.win_count += 1
        c.adapt_points += config.ADAPT_ON_WIN
        return config.ADAPT_ON_WIN
    elif reason == "survive":
        c.ticks_alive_streak += 1
        if c.ticks_alive_streak % config.ADAPT_ON_SURVIVE == 0:
            c.adapt_points += 1
            return 1
        return 0
    else:
        raise ValueError(f"Lý do thích nghi không hợp lệ: {reason!r}")


def maybe_shift(
    c: Creature,
    rng: random.Random,
    choice: tuple[str, str] | None = None,
) -> tuple[str, str] | None:
    """Đủ >=1 adapt_point thì dịch 1 điểm: LẤY từ trait CAO NHẤT, DỒN vào trait THẤP NHẤT.
       Hoà thì phá bằng thứ tự config.TRAIT_NAMES. Trả (frm,to) hoặc None."""
    if c.adapt_points < 1:
        return None

    # CHUYÊN HOÁ, không san bằng. Lấy từ trait THẤP NHẤT (còn > MIN), dồn vào trait
    # CAO NHẤT (còn < MAX). Hoà thì phá bằng thứ tự config.TRAIT_NAMES.
    #
    # Bẫy — vì sao KHÔNG làm ngược lại: luật "cao nhất -> thấp nhất" (bản đầu, theo
    # v4 bước 12) tất yếu hội tụ về (2,2,2,2,2,2). Đo thật: L1 chỉ cần BA lần dịch là
    # thành vector đồng nhất, và sau ~150 tick cả năm loài thành MỘT cơ thể giống hệt
    # nhau. Điều đó xoá sạch bản sắc loài — thứ mà Q1 và cả tầng v5 (brain quyết định
    # dung lượng Sổ Luật) dựa vào. Chuyên hoá thì mỗi loài đi về một cực riêng.
    # B-13 sẽ thay luật này bằng lựa chọn của LLM; đây chỉ là giàn giáo cho M1.
    if choice is not None:
        # B-13: hướng do chính LLM của con đó chọn. Vẫn phải qua `Traits.shift`,
        # nên tổng 12 và biên [0,5] không thể bị phá từ đường này.
        frm, to = choice
        try:
            c.traits = c.traits.shift(frm, to)
        except ValueError:
            return None
        c.adapt_points -= 1
        c.shift_log.append((frm, to))
        return (frm, to)

    givers = [n for n in config.TRAIT_NAMES if getattr(c.traits, n) > config.TRAIT_MIN]
    takers = [n for n in config.TRAIT_NAMES if getattr(c.traits, n) < config.TRAIT_MAX]
    if not givers or not takers:
        return None
    frm = min(givers, key=lambda n: getattr(c.traits, n))
    to = max(takers, key=lambda n: getattr(c.traits, n))

    if frm == to:
        return None

    try:
        new_traits = c.traits.shift(frm, to)
    except ValueError:
        # B2: shift ném ValueError khi chạm biên -> bắt và trả None, không để vỡ vòng tick
        return None

    c.traits = new_traits
    c.adapt_points -= 1
    shift_res = (frm, to)
    c.shift_log.append(shift_res)
    return shift_res


def reset_body(c: Creature) -> None:
    """Về founder vector, xoá adapt_points và mọi điểm đã dịch.
       KHÔNG chạm trí nhớ/Sổ Luật — chết mất cơ thể, không mất hiểu biết."""
    c.traits = founder_traits(c.species)
    c.adapt_points = 0
    c.shift_log.clear()

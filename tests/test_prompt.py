"""Kiểm thử prompt 5 khối (B-02).

Điểm cần nhớ khi đọc file này: test rò rỉ chỉ có giá trị nếu nó **đỏ được**.
`test_leak_guard_is_live` cố tình nhét tên lớp vào và đòi `PromptLeak`. Nếu ai
đó thay `_check_no_leak` bằng một bộ lọc `re.sub` thì test đó đỏ ngay — đó là
mục đích của nó.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from genesis import law_config
from genesis.creature import Creature
from genesis.prompt import (
    BLOCK_A,
    COVENANT_SENTENCE,
    PromptCache,
    PromptLeak,
    system_block,
    user_block,
)
from genesis.surface import SurfaceMap
from genesis.tick import build_match, tick
from genesis.traits import Traits
from genesis.world import visible

PERSONA = "Đi thành bầy, chia phần cho con yếu."


def _match(seed: int = 3):
    world, creatures, state, rng = build_match(seed=seed)
    return world, creatures, state, rng


def test_prefix_chi_vo_khi_brain_doi():
    """Bất biến 1, phát biểu đúng: prefix chỉ được vỡ khi `brain` dịch.

    Không test "không bao giờ vỡ" — W-11 có dịch trait thật, và test kiểu đó chỉ
    xanh nhờ chạy ngắn hơn lần dịch đầu tiên. Test cái đúng: đếm số lần vỡ và
    đòi nó bằng đúng số lần brain đổi, không hơn một lần nào.
    """
    world, creatures, state, rng = _match()
    cache = PromptCache()
    brain_changes = 0
    last_brain = {c.id: c.traits.brain for c in creatures}
    for t in range(400):
        tick(world, creatures, t, rng, state)
        for c in creatures:
            if c.traits.brain != last_brain[c.id]:
                brain_changes += 1
                last_brain[c.id] = c.traits.brain
            cache.get(c, PERSONA, world.surface_map, tick_no=t)
    assert cache.invalidations <= brain_changes
    # Chặt hơn: brain đổi trong CÙNG một bậc từ vựng thì prefix không được vỡ.
    assert cache.invalidations < brain_changes // 2, (
        f"prefix vỡ {cache.invalidations}/{brain_changes} lần brain đổi — "
        f"khối SYSTEM đang mang thứ không thuộc về nó"
    )


def test_moi_thu_bien_dong_nam_o_user_block():
    """Bất biến 2: đời sống của con vật chỉ hiện ra ở khối E."""
    world, creatures, state, rng = _match()
    c = next(x for x in creatures if x.id == "L1:0")
    sysb = system_block(c, PERSONA, world.surface_map)
    u1 = user_block(c, world, 0, None, None, seen=visible(c, world, creatures))
    for t in range(150):
        tick(world, creatures, t, rng, state)
    u2 = user_block(c, world, 150, None, None, seen=visible(c, world, creatures))
    assert u1 != u2, "khối E phải đổi theo ván"
    # Vị trí, máu, sức, tầm nhìn — không chữ nào trong số đó được nằm ở SYSTEM.
    for header in ("[TA]", "[SỔ TAY]", "[SỔ LUẬT CỦA TA]", "[NGHE ĐƯỢC]", "[GHI CHÚ RIÊNG]"):
        assert header not in sysb, f"{header} là khối biến động, không được ở SYSTEM"
    for line in u2.splitlines():
        if line.strip() and not line.startswith("["):
            assert line not in sysb, f"dòng biến động lọt vào SYSTEM: {line!r}"


def test_khoi_a_khong_co_cong_thuc_so():
    """Bất biến 3: nói cơ chế, không nói số. Có số thì model làm toán."""
    assert not re.search(r"=\s*\d+\s*[+*]", BLOCK_A)
    assert "=" not in BLOCK_A
    assert not re.search(r"\d", BLOCK_A), "khối A không được chứa một chữ số nào"


def test_khoi_a2_nguyen_van():
    """Bất biến 4: thiếu câu này thì ta đo model nào cứng đầu, không phải quy nạp."""
    world, creatures, _, _ = _match()
    c = creatures[0]
    s = system_block(c, PERSONA, world.surface_map)
    assert COVENANT_SENTENCE in s
    assert "Màu sắc, hình dạng, âm thanh được xáo lại mỗi lần thế giới sinh ra." in s


def test_khong_ro_ten_lop_trong_van_that():
    """Bất biến 5: chạy ván thật, quả trên bản đồ là FRUIT_*, prompt phải sạch."""
    world, creatures, state, rng = _match()
    for t in range(200):
        tick(world, creatures, t, rng, state)
    assert world.fruits, "ván này phải có quả để test có nghĩa"
    for c in creatures:
        s = system_block(c, PERSONA, world.surface_map)
        u = user_block(c, world, 200, None, None, seen=visible(c, world, creatures))
        assert "FRUIT_" not in s and "FRUIT_" not in u
        assert "law_id" not in s and "law_id" not in u


def test_leak_guard_is_live():
    """Bộ canh phải NÉM, không được vá âm thầm — nếu không mọi test trên là rỗng."""
    world, creatures, _, _ = _match()
    c = creatures[0]

    bad_sm = SurfaceMap(cls_to_surface={"FRUIT_A": "FRUIT_A", "FRUIT_B": "quả xanh dài"})
    with pytest.raises(PromptLeak):
        system_block(c, PERSONA, bad_sm)

    # persona đến từ máy lạ ở chế độ mở: không được mớm đáp án qua nó
    with pytest.raises(PromptLeak):
        system_block(c, "Loài ta biết POISON đến từ đâu.", world.surface_map)

    # `notepad` và `heard` là chữ của NGƯỜI KHÁC: vô hiệu hoá, KHÔNG ném.
    # Ném ở đây nghĩa là bất cứ ai cũng làm gãy ván của ta bằng một chuỗi.
    u = user_block(c, world, 0, None, None, notepad="thử lại FRUIT_C xem sao",
                   heard=["L2:0 nói: ăn FRUIT_A thì POISON"])
    assert "FRUIT_" not in u and "POISON" not in u
    assert "thử lại ? xem sao" in u

    with pytest.raises(ValueError):
        system_block(c, "x" * (law_config.PERSONA_MAX_CHARS + 1), world.surface_map)


_BRAIN_VECTORS = {
    0: Traits(brain=0, attack=2, armor=0, speed=5, sense=3, stomach=2),
    1: Traits(brain=1, attack=1, armor=5, speed=1, sense=2, stomach=2),
    3: Traits(brain=3, attack=4, armor=2, speed=1, sense=2, stomach=0),
    5: Traits(brain=5, attack=5, armor=0, speed=2, sense=0, stomach=0),
}


def test_khoi_d_cat_theo_brain():
    """brain 0–1 câm về mặt khái niệm: không phát biểu nổi một hoàn cảnh nào."""
    world, _, _, _ = _match()
    sm = world.surface_map

    def blk(brain: int) -> str:
        c = Creature(
            id="X:0", species="X", traits=_BRAIN_VECTORS[brain],
            pos=(0, 0), hp=1.0, energy=1.0,
        )
        return system_block(c, "", sm)

    low, mid, high = blk(0), blk(3), blk(5)

    assert blk(0) == blk(1), "brain 0 và 1 dùng chung từ vựng, prompt phải giống hệt"
    assert "ngươi không phát biểu được hoàn cảnh nào" in low
    assert "PHASE" not in low and "TERRAIN" not in low
    assert "SPEAK" not in low and "TELEPORT" not in low

    assert "nhiều nhất 1" in mid
    assert "PHASE" in mid

    assert "nhiều nhất 2" in high
    assert "TELEPORT" in high and "ALONE" in high
    for name in ("EAT", "DRINK", "ATTACK"):
        assert name in low, "trigger nền phải có ở mọi brain"


def test_prompt_cache_bao_prefix_vo():
    """Bẫy §4: brain dịch giữa ván thì cache vỡ — phải đếm được, không im lặng."""
    world, creatures, _, _ = _match()
    c = next(x for x in creatures if x.id == "L1:0")
    cache = PromptCache()
    a = cache.get(c, PERSONA, world.surface_map)
    assert cache.get(c, PERSONA, world.surface_map) == a
    assert cache.invalidations == 0

    # 4 -> 2 là ĐỔI BẬC từ vựng (4–5 xuống 2–3), nên prefix phải vỡ.
    c.traits = dataclasses.replace(
        c.traits, brain=2, attack=c.traits.attack + (c.traits.brain - 2)
    )
    cache.get(c, PERSONA, world.surface_map, tick_no=42)
    assert cache.invalidations == 1


def test_user_block_co_du_nam_muc():
    world, creatures, _, _ = _match()
    c = creatures[0]
    u = user_block(c, world, 7, None, None, heard=["L2:0 nói gì đó"], notepad="ghi")
    for header in ("[TA]", "[SỔ TAY]", "[SỔ LUẬT CỦA TA]", "[NGHE ĐƯỢC]", "[GHI CHÚ RIÊNG]"):
        assert header in u
    assert u.index("[TA]") < u.index("[GHI CHÚ RIÊNG]")

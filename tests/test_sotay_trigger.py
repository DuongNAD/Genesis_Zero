"""Genesis Zero — tests cho tiền đề kích hoạt sổ tay (sotay trigger coverage).

Bảo đảm sổ tay phản ánh đầy đủ các tiền đề trong LawDSL theo thứ tự ưu tiên cố định,
không nhìn vào luật đang chạy và không làm rò đáp án.
"""

from __future__ import annotations

import random

from genesis.creature import Creature
from genesis.lawdsl import TriggerKind
from genesis.strategist import LlmStrategist
from genesis.traits import founder_traits
from genesis.world import World

TRIGGER_PREMISE_MAP: dict[TriggerKind, str] = {
    TriggerKind.EAT: "ăn",
    TriggerKind.DRINK: "uống nước",
    TriggerKind.ATTACK: "trúng đòn",
    TriggerKind.HIT_BY: "trúng đòn",
    TriggerKind.STEP_ON: "bước vào",
    TriggerKind.REST: "đứng yên",
    TriggerKind.LOW_ENERGY: "sức đã cạn",
    TriggerKind.ADJACENT: "có kẻ đứng sát bên",
    TriggerKind.PHASE_ENTER: "trời vừa chuyển sang",
    TriggerKind.SPEAK: "lên tiếng",
    TriggerKind.DEATH_NEAR: "thấy kẻ chết",
}


def test_tu_vung_so_tay_phu_het_trigger_cua_DSL() -> None:
    """Với mỗi TriggerKind trong genesis.lawdsl, khẳng định có một chuỗi tiền đề tương ứng.

    Chấp nhận ATTACK/HIT_BY cùng ánh xạ về 'trúng đòn', REST về 'đứng yên', STEP_ON về 'bước vào'.
    Bài này là bài canh chừng: nó phải ĐỎ nếu ai đó thêm một TriggerKind mới mà quên thêm tiền đề.
    """
    for tk in TriggerKind:
        assert tk in TRIGGER_PREMISE_MAP, f"Thiếu chuỗi tiền đề sổ tay cho TriggerKind.{tk.name}"
        assert TRIGGER_PREMISE_MAP[tk], f"Chuỗi tiền đề rỗng cho TriggerKind.{tk.name}"


def test_kiet_suc_duoc_goi_ten() -> None:
    """Dựng một ván, ép một con có energy thấp và không ăn/uống/đánh, chạy observe.

    Khẳng định sổ tay của nó có chuỗi 'sức đã cạn' chứ không phải 'bước vào'.
    """
    rng = random.Random(42)
    world = World(w=10, h=10, rng=rng)
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        pos=(3, 3),
        age=20,
        hp=100.0,
        energy=10.0,  # 10.0 < 0.25 * traits.energy_max (kiệt sức)
        traits=traits,
    )
    assert c.energy < 0.25 * c.traits.energy_max

    strat = LlmStrategist("http://test-model", [c.id])
    # Chọn tick_no = 1 (không phải mốc chuyển pha)
    tick_no = 1
    events = {
        "move": [{"creature_id": c.id, "moved": True}],
        "law": [{"creature_id": c.id, "effect": "ENERGY_DRAIN"}],
    }
    strat.observe(tick_no, world, [c], events)

    notes = strat.notes_of(c).render(10)
    assert "sức đã cạn" in notes, f"Kỳ vọng 'sức đã cạn' trong sổ tay, thực tế: {notes}"
    assert "bước vào" not in notes, f"Không được ghi 'bước vào' khi đang kiệt sức: {notes}"


def test_uu_tien_khong_nhin_vao_luat() -> None:
    """Chạy CÙNG một tình huống với hai bộ luật khác nhau và khẳng định chuỗi tiền đề GIỐNG HỆT.

    Đây là bài quan trọng nhất: nó chứng minh sổ tay không rò đáp án.
    """
    rng = random.Random(123)
    world = World(w=10, h=10, rng=rng)
    traits = founder_traits("L1")
    c = Creature(
        id="L1:0",
        species="L1",
        pos=(5, 5),
        age=30,
        hp=80.0,
        energy=80.0,
        traits=traits,
    )

    # Tình huống A: Luật gây DAMAGE
    strat_a = LlmStrategist("http://test-model", [c.id])
    events_a = {
        "move": [{"creature_id": c.id, "moved": True}],
        "law": [{"creature_id": c.id, "effect": "DAMAGE"}],
    }
    strat_a.observe(1, world, [c], events_a)

    # Tình huống B: Luật gây HEAL
    strat_b = LlmStrategist("http://test-model", [c.id])
    events_b = {
        "move": [{"creature_id": c.id, "moved": True}],
        "law": [{"creature_id": c.id, "effect": "HEAL"}],
    }
    strat_b.observe(1, world, [c], events_b)

    # Tình huống C: Không có luật nào kích hoạt
    strat_c = LlmStrategist("http://test-model", [c.id])
    events_c = {
        "move": [{"creature_id": c.id, "moved": True}],
    }
    strat_c.observe(1, world, [c], events_c)

    action_a = strat_a.notes_of(c)._items[0][1].action
    action_b = strat_b.notes_of(c)._items[0][1].action
    action_c = strat_c.notes_of(c)._items[0][1].action

    assert action_a == action_b == action_c, (
        f"Tiền đề hành động bị đổi theo luật: A={action_a}, B={action_b}, C={action_c}"
    )


def test_an_uong_van_uu_tien_truoc() -> None:
    """Con vừa ăn/uống/trúng đòn thì dòng của nó vẫn là 'ăn ...' / 'uống nước' / 'trúng đòn'."""
    rng = random.Random(99)
    world = World(w=10, h=10, rng=rng)
    traits = founder_traits("L1")
    # Con vật thỏa mãn tất cả các điều kiện trạng thái khác:
    # 1. Chuyển pha: tick_no = 0 (0 % PHASE_LEN == 0)
    # 2. Kiệt sức: energy = 10 < 0.25 * energy_max
    # 3. Có kẻ đứng sát bên: other tại (3, 4) sát (3, 3)
    # 4. Di chuyển: moved = True
    c = Creature(
        id="L1:0",
        species="L1",
        pos=(3, 3),
        age=15,
        hp=50.0,
        energy=10.0,
        traits=traits,
    )
    other = Creature(
        id="L2:0",
        species="L2",
        pos=(3, 4),
        age=15,
        hp=50.0,
        energy=50.0,
        traits=founder_traits("L2"),
    )

    # 1. Ăn quả: vẫn ghi "ăn ..."
    strat_eat = LlmStrategist("http://test-model", [c.id])
    events_eat = {
        "eat": [{"creature_id": c.id, "fruit_class": "FRUIT_A"}],
        "move": [{"creature_id": c.id, "moved": True}],
    }
    strat_eat.observe(0, world, [c, other], events_eat)
    notes_eat = strat_eat.notes_of(c).render(10)
    assert "ăn " in notes_eat, f"Kỳ vọng 'ăn ...', thực tế: {notes_eat}"
    assert "trời vừa chuyển sang" not in notes_eat
    assert "sức đã cạn" not in notes_eat
    assert "có kẻ đứng sát bên" not in notes_eat
    assert "bước vào" not in notes_eat

    # 2. Uống nước: vẫn ghi "uống nước"
    strat_drink = LlmStrategist("http://test-model", [c.id])
    events_drink = {
        "drink": [{"creature_id": c.id}],
        "move": [{"creature_id": c.id, "moved": True}],
    }
    strat_drink.observe(0, world, [c, other], events_drink)
    notes_drink = strat_drink.notes_of(c).render(10)
    assert "uống nước" in notes_drink, f"Kỳ vọng 'uống nước', thực tế: {notes_drink}"
    assert "trời vừa chuyển sang" not in notes_drink
    assert "sức đã cạn" not in notes_drink
    assert "có kẻ đứng sát bên" not in notes_drink
    assert "bước vào" not in notes_drink

    # 3. Trúng đòn: vẫn ghi "trúng đòn"
    strat_atk = LlmStrategist("http://test-model", [c.id])
    events_atk = {
        "attack": [{"creature_id": c.id}],
        "move": [{"creature_id": c.id, "moved": True}],
    }
    strat_atk.observe(0, world, [c, other], events_atk)
    notes_atk = strat_atk.notes_of(c).render(10)
    assert "trúng đòn" in notes_atk, f"Kỳ vọng 'trúng đòn', thực tế: {notes_atk}"
    assert "trời vừa chuyển sang" not in notes_atk
    assert "sức đã cạn" not in notes_atk
    assert "có kẻ đứng sát bên" not in notes_atk
    assert "bước vào" not in notes_atk


def test_thu_tu_uu_tien_day_du() -> None:
    """Kiểm tra từng nấc ưu tiên 1 -> 2 -> 3 -> 4 -> 5."""
    rng = random.Random(7)
    world = World(w=10, h=10, rng=rng)
    traits = founder_traits("L1")

    c = Creature(
        id="L1:0",
        species="L1",
        pos=(5, 5),
        age=10,
        hp=100.0,
        energy=10.0,  # kiệt sức
        traits=traits,
    )
    other = Creature(
        id="L2:0",
        species="L2",
        pos=(5, 6),  # đứng sát bên
        age=10,
        hp=100.0,
        energy=100.0,
        traits=founder_traits("L2"),
    )

    # Mức 1 thắng Mức 2..5: tick chuyển pha
    strat1 = LlmStrategist("http://test-model", [c.id])
    strat1.observe(0, world, [c, other], {"move": [{"creature_id": c.id, "moved": True}]})
    assert "trời vừa chuyển sang ban ngày" in strat1.notes_of(c).render(10)

    # Mức 2 thắng Mức 3..5: tick không chuyển pha, kiệt sức + đứng cạnh + di chuyển
    strat2 = LlmStrategist("http://test-model", [c.id])
    strat2.observe(1, world, [c, other], {"move": [{"creature_id": c.id, "moved": True}]})
    assert "sức đã cạn" in strat2.notes_of(c).render(10)

    # Mức 3 thắng Mức 4..5: không kiệt sức, đứng cạnh + di chuyển
    c.energy = 80.0
    strat3 = LlmStrategist("http://test-model", [c.id])
    strat3.observe(1, world, [c, other], {"move": [{"creature_id": c.id, "moved": True}]})
    assert "có kẻ đứng sát bên" in strat3.notes_of(c).render(10)

    # Mức 4 thắng Mức 5: không đứng cạnh, di chuyển
    other.pos = (0, 0)  # cách xa
    strat4 = LlmStrategist("http://test-model", [c.id])
    strat4.observe(1, world, [c, other], {"move": [{"creature_id": c.id, "moved": True}]})
    assert "bước vào" in strat4.notes_of(c).render(10)

    # Mức 5: không di chuyển
    strat5 = LlmStrategist("http://test-model", [c.id])
    strat5.observe(1, world, [c, other], {"move": [{"creature_id": c.id, "moved": False}]})
    assert "đứng yên" in strat5.notes_of(c).render(10)

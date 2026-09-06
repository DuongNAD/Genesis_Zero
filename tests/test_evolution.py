"""Genesis Zero — Unit test suite for Generational Evolution & Genetic Mutation (M1_EVO).

Covers:
1. Trait mutation invariants (sum == 12, min 0, max 5 across 1000 iterations).
2. Biological feature inheritance & mutation (valid pool, kit generation, passability effect).
3. Reproduction gate conditions (energy, age, streak, cooldown, law discovery bonus).
4. Spatial clearance requirement for birth placement.
5. Carrying capacity constraints (global cap 35, species cap 7, crowding suppression).
6. Lineage metadata integrity and sequential integer ID sorting compatibility.
7. Extinction detection event generation.
8. Integration inside the deterministic tick pipeline.
"""

from __future__ import annotations

import random
from dataclasses import astuple

from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.domain import Domain, can_enter
from genesis.evolution import (
    can_reproduce,
    detect_extinctions,
    mutate_features,
    mutate_traits,
    reproduce_offspring,
    trait_variance,
)
from genesis.features import FEATURES
from genesis.tick import build_match, tick
from genesis.traits import Traits, founder_traits
from genesis.world import Terrain


def test_trait_mutation_invariants_1000_iterations():
    """Kiểm tra bất biến tổng trait == 12 và 0 <= trait <= 5 qua 1000 lần đột biến."""
    rng = random.Random(42)
    for sp in config.FOUNDERS:
        t = founder_traits(sp)
        for _ in range(200):
            t_mut = mutate_traits(t, rng, prob=1.0)
            values = astuple(t_mut)
            assert sum(values) == config.TRAIT_SUM, f"Tổng trait khác 12: {values}"
            for v in values:
                assert config.TRAIT_MIN <= v <= config.TRAIT_MAX, f"Trait ngoài [0, 5]: {v}"
            # Dùng tiếp t_mut cho lần lặp sau để kiểm tra đột biến luỹ tích
            t = t_mut


def test_trait_variance_vector_sums_to_zero():
    """Vector phương sai d_tr so với founder traits luôn có tổng bằng 0."""
    rng = random.Random(123)
    t = founder_traits("L1")
    for _ in range(50):
        t = mutate_traits(t, rng, prob=0.8)
        d_tr = trait_variance(t, "L1")
        assert len(d_tr) == 6
        assert sum(d_tr) == 0, f"Tổng d_tr khác 0: {d_tr}"


def test_feature_mutation_valid_pool_and_kit():
    """Đột biến feature luôn hoán đổi sang feature hợp lệ trong FEATURES và tạo Kit đúng."""
    rng = random.Random(999)
    initial_feats = tuple(sorted(("LONG_DAI", "VAY_CUNG", "RANG_NANH")))
    all_keys = {f.key for f in FEATURES}

    mutated_count = 0
    for _ in range(100):
        mut_feats = mutate_features(initial_feats, rng, prob=0.5)
        assert len(mut_feats) == 3
        assert len(set(mut_feats)) == 3, "Có feature trùng nhau trong tổ hợp con"
        for k in mut_feats:
            assert k in all_keys, f"Feature key lạ: {k}"
        if mut_feats != initial_feats:
            mutated_count += 1
            # Kiểm tra chỉ khác đúng 1 feature
            diff = set(initial_feats) ^ set(mut_feats)
            assert len(diff) == 2, f"Đột biến phải thay thế đúng 1 feature, nhận diff: {diff}"

    assert mutated_count > 0, "Xác suất 0.5 phải sinh ra ít nhất một đột biến sau 100 lần"


def test_feature_mutation_passability_effect():
    """Cá thể cạn đột biến LUONG_CU có thể bơi xuống DEEP / WATER; đột biến TREO_GIOI trèo được TREE."""
    world, creatures, state, rng = build_match(seed=10)

    # Sinh vật cạn L1 mặc định không bơi được nước sâu DEEP
    c_normal = Creature(
        id="L1:0",
        species="L1",
        traits=founder_traits("L1"),
        pos=(0, 0),
        hp=50.0,
        energy=80.0,
        features=("LONG_DAI", "VAY_CUNG", "RANG_NANH"),
    )
    assert not can_enter(Domain.CAN, Terrain.DEEP, c_normal.traits, c_normal.kit)

    # Sinh vật cạn L1 đột biến có LUONG_CU
    c_amphibious = Creature(
        id="L1:1",
        species="L1",
        traits=founder_traits("L1"),
        pos=(0, 0),
        hp=50.0,
        energy=80.0,
        features=("LUONG_CU", "VAY_CUNG", "RANG_NANH"),
    )
    assert can_enter(Domain.CAN, Terrain.DEEP, c_amphibious.traits, c_amphibious.kit)

    # Sinh vật cạn speed=1 bình thường không trèo được TREE (cần speed >= 3)
    c_slow = Creature(
        id="L1:2",
        species="L1",
        traits=Traits(brain=4, attack=3, armor=2, speed=1, sense=1, stomach=1),
        pos=(0, 0),
        hp=50.0,
        energy=80.0,
        features=("LONG_DAI", "VAY_CUNG", "RANG_NANH"),
    )
    assert not can_enter(Domain.CAN, Terrain.TREE, c_slow.traits, c_slow.kit)

    # Đột biến TREO_GIOI giảm ngưỡng trèo xuống 2 (1 >= 3 - 2 -> trèo được)
    c_climber = Creature(
        id="L1:3",
        species="L1",
        traits=Traits(brain=4, attack=3, armor=2, speed=1, sense=1, stomach=1),
        pos=(0, 0),
        hp=50.0,
        energy=80.0,
        features=("TREO_GIOI", "VAY_CUNG", "RANG_NANH"),
    )
    assert can_enter(Domain.CAN, Terrain.TREE, c_climber.traits, c_climber.kit)


def test_reproduction_gates():
    """Kiểm tra từng cổng điều kiện sinh sản: age, streak, cooldown, energy, alive."""
    world, creatures, state, rng = build_match(seed=1)
    traits = founder_traits("L1")

    # 1. Chưa đủ tuổi (age < 30)
    c1 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max, age=20, ticks_alive_streak=25, reproduce_cooldown=0,
    )
    ok, reason = can_reproduce(c1, world, [c1])
    assert not ok and reason == "AGE_TOO_LOW"

    # 2. Chưa đủ chuỗi sống sót (streak < 20)
    c2 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max, age=35, ticks_alive_streak=10, reproduce_cooldown=0,
    )
    ok, reason = can_reproduce(c2, world, [c2])
    assert not ok and reason == "STREAK_TOO_LOW"

    # 3. Đang trong thời gian hồi chiêu (cooldown > 0)
    c3 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max, age=35, ticks_alive_streak=25, reproduce_cooldown=10,
    )
    ok, reason = can_reproduce(c3, world, [c3])
    assert not ok and reason == "ON_COOLDOWN"

    # 4. Thiếu năng lượng (< 80% energy_max)
    c4 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=0.70 * traits.energy_max, age=35, ticks_alive_streak=25, reproduce_cooldown=0,
    )
    ok, reason = can_reproduce(c4, world, [c4])
    assert not ok and reason == "ENERGY_TOO_LOW"

    # 5. Đã chết
    c5 = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=0.0,
        energy=traits.energy_max, age=35, ticks_alive_streak=25, reproduce_cooldown=0, alive=False,
    )
    ok, reason = can_reproduce(c5, world, [c5])
    assert not ok and reason == "NOT_ALIVE"

    # 6. Đạt tất cả điều kiện
    c_ok = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max * 0.90, age=35, ticks_alive_streak=25, reproduce_cooldown=0,
    )
    ok, reason = can_reproduce(c_ok, world, [c_ok])
    assert ok and reason is None


def test_reproduction_codex_discovery_bonus():
    """Sinh vật có phát hiện luật ẩn được nới lỏng ngưỡng năng lượng và giảm 50% cooldown."""
    world, creatures, state, rng = build_match(seed=1)
    traits = founder_traits("L1")

    # Năng lượng ở mức 75% (dưới ngưỡng 80% mặc định, nhưng trên 70%)
    c = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max * 0.75, age=35, ticks_alive_streak=25, reproduce_cooldown=0,
    )
    # Không có discovery -> từ chối
    ok, reason = can_reproduce(c, world, [c])
    assert not ok and reason == "ENERGY_TOO_LOW"

    # Đánh dấu có discovery -> được chấp thuận
    c.has_discovery = True
    ok, reason = can_reproduce(c, world, [c])
    assert ok and reason is None


def test_carrying_capacity_and_crowding_caps():
    """Kiểm tra trần dân số toàn cầu (35), trần theo loài (7), và chặn do mật độ địa phương."""
    world, _, state, rng = build_match(seed=1)
    traits = founder_traits("L1")

    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(10, 10), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # 1. Trần theo loài: đã có 7 cá thể L1 còn sống
    species_crowd = [parent] + [
        Creature(
            id=f"L1:{i}", species="L1", traits=traits, pos=(0, i), hp=50.0, energy=50.0
        )
        for i in range(1, 7)
    ]
    assert len(species_crowd) == 7
    ok, reason = can_reproduce(parent, world, species_crowd)
    assert not ok and reason == "SPECIES_CAP_REACHED"

    # 2. Trần toàn cầu: 35 cá thể còn sống trên thế giới
    global_crowd = [parent] + [
        Creature(
            id=f"L2:{i}", species="L2", traits=founder_traits("L2"), pos=(0, i % 20), hp=50.0, energy=50.0
        )
        for i in range(1, 35)
    ]
    assert len(global_crowd) == 35
    ok, reason = can_reproduce(parent, world, global_crowd)
    assert not ok and reason == "GLOBAL_CAP_REACHED"

    # 3. Mật độ địa phương: 4 cá thể trong bán kính Chebyshev 2
    neighbors = [
        Creature(id="L2:1", species="L2", traits=traits, pos=(11, 10), hp=50.0, energy=50.0),
        Creature(id="L2:2", species="L2", traits=traits, pos=(10, 11), hp=50.0, energy=50.0),
        Creature(id="L2:3", species="L2", traits=traits, pos=(11, 11), hp=50.0, energy=50.0),
        Creature(id="L2:4", species="L2", traits=traits, pos=(9, 9), hp=50.0, energy=50.0),
    ]
    ok, reason = can_reproduce(parent, world, [parent, *neighbors])
    assert not ok and reason == "LOCAL_CROWDING"


def test_spatial_clearance_gated():
    """Nếu bị vây kín bởi địa hình không đi được, sinh vật không thể sinh con và không mất năng lượng."""
    world, _, state, rng = build_match(seed=5)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:0", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
    )

    # Đặt toàn bộ 8 ô xung quanh thành ROCK
    for nx, ny in world.neighbors(parent.pos):
        world.grid[ny][nx] = Terrain.ROCK

    child = reproduce_offspring(parent, tick=10, rng=rng, world=world)
    assert child is None, "Không có ô đi được lân cận thì phải trả về None"


def test_lineage_metadata_and_integer_id_sorting():
    """Kiểm tra metadata dòng dõi (parent_id, generation, lineage_id) và tính tương thích int(idx)."""
    world, _, state, rng = build_match(seed=7)
    traits = founder_traits("L1")
    parent = Creature(
        id="L1:1", species="L1", traits=traits, pos=(5, 5), hp=50.0,
        energy=traits.energy_max, age=40, ticks_alive_streak=30, reproduce_cooldown=0,
        generation=2, lineage_id="L1:0",
    )

    # Đảm bảo có ô đi được xung quanh
    for nx, ny in world.neighbors(parent.pos):
        world.grid[ny][nx] = Terrain.PLAIN

    existing = [
        Creature(id="L1:0", species="L1", traits=traits, pos=(1, 1), hp=50.0, energy=50.0),
        parent,
        Creature(id="L1:9", species="L1", traits=traits, pos=(2, 2), hp=50.0, energy=50.0),
    ]

    child = reproduce_offspring(parent, tick=50, rng=rng, world=world, creatures=existing)
    assert child is not None
    assert child.parent_id == "L1:1"
    assert child.generation == 3
    assert child.lineage_id == "L1:0"
    assert child.birth_tick == 50
    assert child.energy == config.CHILD_START_ENERGY

    # Kiểm tra định dạng ID số nguyên đơn điệu f"{species}:{idx}"
    assert child.id == "L1:10"

    # Kiểm tra creature_sort_key không quăng ngoại lệ
    species, num_idx = creature_sort_key(child)
    assert species == "L1"
    assert num_idx == 10

    # Kiểm tra sắp xếp danh sách theo creature_sort_key
    all_creatures = [*existing, child]
    sorted_creatures = sorted(all_creatures, key=creature_sort_key)
    sorted_ids = [c.id for c in sorted_creatures]
    assert sorted_ids == ["L1:0", "L1:1", "L1:9", "L1:10"]


def test_extinction_detection():
    """Phát hiện chính xác sự kiện tuyệt chủng khi toàn bộ cá thể của loài chết."""
    traits = founder_traits("L1")
    creatures = [
        Creature(id="L1:0", species="L1", traits=traits, pos=(0, 0), hp=0.0, energy=0.0, alive=False),
        Creature(id="L1:1", species="L1", traits=traits, pos=(1, 1), hp=0.0, energy=0.0, alive=False),
        Creature(id="L2:0", species="L2", traits=founder_traits("L2"), pos=(2, 2), hp=50.0, energy=50.0, alive=True),
    ]

    extinct_set: set[str] = set()
    events = detect_extinctions(creatures, tick_no=42, extinct_species=extinct_set)
    assert len(events) == 1
    assert events[0]["kind"] == "EXTINCTION"
    assert events[0]["species"] == "L1"
    assert "L1" in extinct_set

    # Tick tiếp theo nếu vẫn không có con nào sống, không phát lặp lại
    events2 = detect_extinctions(creatures, tick_no=43, extinct_species=extinct_set)
    assert len(events2) == 0


def test_simulation_tick_reproduction_loop():
    """Chạy vòng tick mô phỏng thật và kiểm chứng sinh sản cá thể mới vào quần thể."""
    world, creatures, state, rng = build_match(seed=42)

    # Chuẩn bị một cá thể đạt đầy đủ điều kiện sinh sản
    eligible_parent = creatures[0]
    eligible_parent.age = 50
    eligible_parent.ticks_alive_streak = 30
    eligible_parent.energy = eligible_parent.traits.energy_max
    eligible_parent.reproduce_cooldown = 0
    initial_energy = eligible_parent.energy
    initial_pop_len = len(creatures)

    # Đảm bảo xung quanh có ít nhất 1 ô passable
    for p in world.neighbors(eligible_parent.pos):
        world.grid[p[1]][p[0]] = Terrain.PLAIN

    # Chạy 1 tick
    tick(world, creatures, tick_no=1, rng=rng, state=state)

    # Sinh vật con phải xuất hiện trong creatures
    assert len(creatures) > initial_pop_len
    new_creatures = [c for c in creatures if c.parent_id == eligible_parent.id]
    assert len(new_creatures) >= 1
    child = new_creatures[0]
    assert child.generation == eligible_parent.generation + 1
    assert eligible_parent.reproduce_cooldown == config.REPRODUCE_COOLDOWN
    # Năng lượng của bố mẹ đã bị trừ chi phí sinh sản (+ chi phí upkeep của tick)
    assert eligible_parent.energy < initial_energy - config.REPRODUCE_COST + 1.0

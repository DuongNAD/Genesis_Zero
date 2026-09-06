"""Genesis Zero — evolution: Cơ chế sinh sản thế hệ & đột biến di truyền (M1_EVO).

Theo tài liệu kiến trúc PROJECT.md § Interface Contracts (1) và W-19:
1. Sinh sản cá thể con (reproduce_offspring) kế thừa trait và biological features từ bố mẹ.
2. Đột biến trait có giới hạn (zero-sum stochastic mutation qua Traits.shift),
   bảo đảm tổng trait luôn = 12 và mỗi trait trong [0, 5].
3. Đột biến đặc điểm sinh học (feature mutation): hoán đổi 1 trong 3 đặc điểm từ FEATURES.
4. Cấp phát ID số nguyên đơn điệu f"{species}:{idx}" để giữ vững bất biến sắp xếp creature_sort_key.
5. Kiểm tra khoảng trống không gian (spatial clearance) xung quanh bố mẹ.
6. Rào cản trần dân số: POPULATION_GLOBAL_MAX = 35, POPULATION_SPECIES_MAX = 7, mật độ Chebyshev.
"""

from __future__ import annotations

import random
from dataclasses import astuple
from typing import TYPE_CHECKING

from genesis import config
from genesis.creature import Creature, allocate_creature_id
from genesis.features import FEATURES, roll_for_species
from genesis.traits import Traits, founder_traits
from genesis.world import World

if TYPE_CHECKING:
    from genesis.codex import Codex
    from genesis.logio import LogWriter
    from genesis.tick import SimState


def mutate_traits(
    traits: Traits,
    rng: random.Random,
    prob: float = config.MUTATE_TRAIT_PROB,
) -> Traits:
    """Đột biến ngẫu nhiên có bảo toàn tổng điểm qua Traits.shift (bảo đảm sum=12, [0,5]).

    Với xác suất `prob`, chọn 1 trait cho (donor > min) và 1 trait nhận (recipient < max, khác donor),
    thực hiện dịch chuyển 1 điểm.
    """
    if rng.random() >= prob:
        return traits

    donors = [t for t in config.TRAIT_NAMES if getattr(traits, t) > config.TRAIT_MIN]
    if not donors:
        return traits

    donor = rng.choice(donors)
    recipients = [
        t for t in config.TRAIT_NAMES
        if t != donor and getattr(traits, t) < config.TRAIT_MAX
    ]
    if not recipients:
        return traits

    recipient = rng.choice(recipients)
    return traits.shift(donor, recipient)


def mutate_features(
    features: tuple[str, ...],
    rng: random.Random,
    prob: float = config.MUTATE_FEAT_PROB,
) -> tuple[str, ...]:
    """Đột biến ngẫu nhiên đặc điểm sinh học: hoán đổi 1 đặc điểm cũ lấy 1 đặc điểm mới từ FEATURES.

    Với xác suất `prob`, chọn 1 feature hiện có để thay thế bằng 1 feature chưa có trong pool.
    Trả về tuple các key đã được sắp xếp tăng dần.
    """
    if not features or rng.random() >= prob:
        return tuple(sorted(features))

    feats_list = list(features)
    drop = rng.choice(feats_list)
    available = [f.key for f in FEATURES if f.key not in feats_list]
    if not available:
        return tuple(sorted(features))

    add = rng.choice(available)
    feats_list.remove(drop)
    feats_list.append(add)
    return tuple(sorted(feats_list))


def trait_variance(traits: Traits, species_or_founder: str | Traits) -> list[int]:
    """Tính vector phương sai trait delta_T = traits - founder_traits.

    Luôn bảo đảm sum(delta_T) == 0 vì cả hai vector đều có tổng bằng 12.
    """
    if isinstance(species_or_founder, str):
        f = founder_traits(species_or_founder)
    else:
        f = species_or_founder
    return [getattr(traits, t) - getattr(f, t) for t in config.TRAIT_NAMES]


def has_law_discovery(c: Creature, strategist=None, codex: Codex | None = None) -> bool:
    """Kiểm tra sinh vật có thành tích khám phá luật ẩn (Sổ Luật tin cậy cao) hay không."""
    if getattr(c, "has_discovery", False):
        return True
    if codex is not None:
        entries = getattr(codex, "entries", None)
        raw_list = entries() if callable(entries) else getattr(codex, "_entries", ())
        return any(e is not None and getattr(e, "conf", 0) >= 3 for e in raw_list)
    if strategist is not None:
        codices = getattr(strategist, "codices", None)
        if codices is None and hasattr(strategist, "mind"):
            codices = getattr(strategist.mind, "codices", None)
        if codices and c.id in codices:
            cx = codices[c.id]
            entries = getattr(cx, "entries", None)
            raw_list = entries() if callable(entries) else getattr(cx, "_entries", ())
            return any(e is not None and getattr(e, "conf", 0) >= 3 for e in raw_list)
    return False


def can_reproduce(
    c: Creature,
    world: World,
    creatures: list[Creature],
    strategist=None,
    codex: Codex | None = None,
) -> tuple[bool, str | None]:
    """Kiểm tra toàn diện các cổng điều kiện sinh sản của sinh vật.

    Trả về (True, None) nếu đủ điều kiện, hoặc (False, lý do) nếu không đạt.
    """
    if not c.alive:
        return False, "NOT_ALIVE"

    # 1. Tuổi tối thiểu
    if c.age < config.REPRODUCE_MIN_AGE:
        return False, "AGE_TOO_LOW"

    # 2. Chuỗi tick sống liên tục
    if c.ticks_alive_streak < config.REPRODUCE_MIN_STREAK:
        return False, "STREAK_TOO_LOW"

    # 3. Thời gian hồi chiêu
    if c.reproduce_cooldown > 0:
        return False, "ON_COOLDOWN"

    # 4. Ngưỡng năng lượng (thưởng giảm ngưỡng khi có khám phá luật)
    discovery = has_law_discovery(c, strategist=strategist, codex=codex)
    energy_ratio = 0.70 if discovery else config.REPRODUCE_ENERGY_RATIO
    if c.energy < energy_ratio * c.traits.energy_max:
        return False, "ENERGY_TOO_LOW"

    # 5. Trần dân số toàn cầu
    alive_all = [x for x in creatures if x.alive]
    if len(alive_all) >= config.POPULATION_GLOBAL_MAX:
        return False, "GLOBAL_CAP_REACHED"

    # 6. Trần dân số theo loài
    alive_sp = [x for x in alive_all if x.species == c.species]
    if len(alive_sp) >= config.POPULATION_SPECIES_MAX:
        return False, "SPECIES_CAP_REACHED"

    # 7. Mật độ lân cận (Chebyshev radius 2)
    crowd = sum(
        1 for x in alive_all
        if x is not c and world.dist(c.pos, x.pos) <= config.CROWDING_RADIUS
    )
    if crowd >= config.CROWDING_MAX_NEIGHBORS:
        return False, "LOCAL_CROWDING"

    return True, None


def reproduce_offspring(
    parent: Creature,
    tick: int,
    rng: random.Random,
    world: World,
    creatures: list[Creature] | None = None,
) -> Creature | None:
    """Sinh sản cá thể con thừa kế trait và features từ bố mẹ có đột biến ngẫu nhiên.

    Gated by spatial clearance: tìm ô lân cận passable với con non.
    Nếu không có ô hợp lệ, trả về None và không trừ năng lượng của bố mẹ.
    """
    if creatures is None:
        creatures = getattr(world, "creatures", [parent])

    # 1. Đột biến trait
    child_traits = mutate_traits(parent.traits, rng)

    # 2. Thừa kế & đột biến features
    parent_feats = parent.features
    if not parent_feats:
        if world.kits and parent.species in world.kits:
            parent_feats = tuple(getattr(world.kits[parent.species], "keys", ()))
        if not parent_feats:
            parent_feats = tuple(f.key for f in roll_for_species(parent.species, 0))

    child_feats = mutate_features(parent_feats, rng)

    # 3. Phân bổ ID nguyên đơn điệu cho con non
    child_id = allocate_creature_id(parent.species, creatures)

    # 4. Khởi tạo đối tượng con non tạm thời để kiểm tra ô đi được
    child = Creature(
        id=child_id,
        species=parent.species,
        traits=child_traits,
        pos=parent.pos,
        hp=float(config.HP_MAX),
        energy=float(config.CHILD_START_ENERGY),
        age=0,
        alive=True,
        parent_id=parent.id,
        generation=parent.generation + 1,
        lineage_id=parent.lineage_id or parent.id,
        birth_tick=tick,
        reproduce_cooldown=config.REPRODUCE_COOLDOWN,
        features=child_feats,
    )

    # 5. Kiểm tra khoảng trống lân cận (passable theo kit riêng của con non)
    neighbors = world.neighbors(parent.pos)
    passable_neighbors = [p for p in neighbors if world.passable(p, child)]
    if not passable_neighbors:
        return None

    occupied = {c.pos for c in creatures if c.alive}
    unoccupied = [p for p in passable_neighbors if p not in occupied]

    if unoccupied:
        child.pos = rng.choice(unoccupied)
    else:
        child.pos = rng.choice(passable_neighbors)

    return child


def resolve_reproduction(
    world: World,
    creatures: list[Creature],
    tick_no: int,
    state: SimState,
    log: LogWriter | None = None,
    strategist=None,
) -> list[dict]:
    """Pha kiểm tra và giải quyết sinh sản cho toàn bộ quần thể trong tick.

    Duyệt tuần tự theo thứ tự tất định (creature_sort_key).
    Trên mỗi ca sinh thành công:
    - Trừ 35.0 energy của bố mẹ.
    - Đặt cooldown (25 tick, hoặc 12 tick nếu có thành tích khám phá luật).
    - Thêm con non vào danh sách creatures.
    - Ghi nhận sự kiện REPRODUCE.
    """
    from genesis.creature import creature_sort_key

    # Giảm cooldown cho các con còn sống
    for c in creatures:
        if c.alive and c.reproduce_cooldown > 0:
            c.reproduce_cooldown -= 1

    events: list[dict] = []
    # Sắp xếp để thứ tự sinh con hoàn toàn tất định
    for c in sorted(creatures, key=creature_sort_key):
        ok, _ = can_reproduce(c, world, creatures, strategist=strategist)
        if not ok:
            continue

        # Luồng RNG riêng tất định cho việc sinh sản của cá thể này ở tick này
        from genesis.tick import creature_rng
        crng = (
            creature_rng(state.match_seed, tick_no, f"REPRODUCE:{c.id}")
            if hasattr(state, "match_seed")
            else random.Random(tick_no)
        )

        child = reproduce_offspring(c, tick_no, crng, world, creatures=creatures)
        if child is None:
            continue

        # Trừ chi phí năng lượng sinh sản của bố mẹ
        c.energy -= config.REPRODUCE_COST

        # Đặt lại cooldown cho bố mẹ (giảm 50% nếu có khám phá luật)
        discovery = has_law_discovery(c, strategist=strategist)
        cooldown = (
            int(config.REPRODUCE_COOLDOWN * 0.5)
            if discovery
            else config.REPRODUCE_COOLDOWN
        )
        c.reproduce_cooldown = cooldown

        # Đưa con non vào quần thể
        creatures.append(child)
        if hasattr(world, "creatures") and world.creatures is not creatures:
            world.creatures.append(child)



        d_tr = trait_variance(child.traits, c.species)
        payload = {
            "kind": "REPRODUCE",
            "type": "REPRODUCE",
            "creature_id": c.id,
            "parent_id": c.id,
            "who": c.id,
            "child": child.id,
            "child_id": child.id,
            "species": c.species,
            "species_id": c.species,
            "gen": child.generation,
            "pos": list(child.pos),
            "x": child.pos[0],
            "y": child.pos[1],
            "traits": list(astuple(child.traits)),
            "features": list(child.features),
            "d_tr": d_tr,
            "detail": f"{c.id} reproduced {child.id} at {child.pos}",
        }
        events.append(payload)

    return events


def detect_extinctions(
    creatures: list[Creature],
    tick_no: int,
    extinct_species: set[str],
) -> list[dict]:
    """Phát hiện các loài vừa rơi vào tuyệt chủng (toàn bộ cá thể alive=False).

    Bảo đảm chỉ phát sự kiện EXTINCTION một lần duy nhất khi loài bị tuyệt chủng.
    """
    all_species = {c.species for c in creatures}
    events: list[dict] = []
    for sp in sorted(all_species):
        alive_count = sum(1 for c in creatures if c.species == sp and c.alive)
        if alive_count == 0:
            if sp not in extinct_species:
                extinct_species.add(sp)
                events.append({
                    "kind": "EXTINCTION",
                    "type": "EXTINCTION",
                    "species": sp,
                    "species_id": sp,
                    "tick": tick_no,
                    "who": sp,
                    "detail": f"Species {sp} went extinct at tick {tick_no}",
                })
        else:
            # Nếu loài có cá thể sống lại (ví dụ hồi sinh), gỡ khỏi tập tuyệt chủng
            extinct_species.discard(sp)

    return events

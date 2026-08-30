"""Genesis Zero — reflex: tầng phản xạ bản năng cho sinh vật."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import random

from genesis import config
from genesis.creature import Creature, creature_sort_key
from genesis.world import World, visible

GOAL_TTL_MIN: int = 2
GOAL_TTL_MAX: int = 12

HP_LOW_RATIO: float = 0.3
# Ngưỡng "no": trên mức này mới đi săn hoặc nghỉ; dưới mức này là đi kiếm ăn.
# Bẫy: bản đầu đặt ngưỡng kiếm ăn ở 0.4, để hở dải 40–80% rơi hết vào WANDER.
# Sinh vật đốt ~3.3/tick trên bể 80–100 nên sống phần lớn thời gian trong dải đó,
# và tầng phản xạ trông như đi lang thang vô định. Một ngưỡng, không có dải chết.
ENERGY_FULL_RATIO: float = 0.8


class Goal(StrEnum):
    FORAGE = "FORAGE"
    HUNT = "HUNT"
    FLEE = "FLEE"
    FOLLOW = "FOLLOW"
    REST = "REST"
    WANDER = "WANDER"
    GUARD = "GUARD"


@dataclass
class ActiveGoal:
    goal: Goal
    target: str | None
    ttl: int


@dataclass(frozen=True)
class Intent:
    creature_id: str
    path: tuple[tuple[int, int], ...]
    attack_id: str | None = None


def choose_goal(
    c: Creature,
    world: World,
    seen: list[Creature],
    rng: random.Random,
) -> ActiveGoal:
    """Chọn mục tiêu theo thứ tự ưu tiên bản năng cho sinh vật."""
    # 1. hp < 30% HP_MAX và có kẻ nguy hiểm trong tầm -> FLEE
    # Kẻ nguy hiểm: khác loài, đang thấy được, damage lớn hơn của mình
    if c.hp < HP_LOW_RATIO * config.HP_MAX:
        dangerous = [
            other
            for other in seen
            if other is not c
            and other.alive
            and other.species != c.species
            and other.traits.damage > c.traits.damage
        ]
        if dangerous:
            target_c = min(
                dangerous,
                key=lambda other: (world.dist(c.pos, other.pos), creature_sort_key(other)),
            )
            return _finalize_goal(c, Goal.FLEE, target_c.id, rng)

    # 2. Chưa no -> đi kiếm ăn. Không tìm thấy cây nào thì reflex_step tự đi tìm.
    if c.energy < ENERGY_FULL_RATIO * c.traits.energy_max:
        return _finalize_goal(c, Goal.FORAGE, None, rng)

    # 3. Đã no và có con khác loài yếu hơn trong tầm -> HUNT
    # Yếu hơn: khác loài, đang thấy được, damage nhỏ hơn của mình
    if c.energy >= ENERGY_FULL_RATIO * c.traits.energy_max:
        weaker = [
            other
            for other in seen
            if other is not c
            and other.alive
            and other.species != c.species
            and other.traits.damage < c.traits.damage
        ]
        if weaker:
            target_c = min(
                weaker,
                key=lambda other: (world.dist(c.pos, other.pos), creature_sort_key(other)),
            )
            return _finalize_goal(c, Goal.HUNT, target_c.id, rng)

        # 4. Đã no, không có con mồi -> nghỉ cho đỡ tốn
        return _finalize_goal(c, Goal.REST, None, rng)

    # 5. còn lại -> WANDER
    return _finalize_goal(c, Goal.WANDER, None, rng)


def _finalize_goal(
    c: Creature,
    goal: Goal,
    target: str | None,
    rng: random.Random,
) -> ActiveGoal:
    allowed = config.GOALS_BY_BRAIN.get(c.traits.brain, [])
    if goal.value not in allowed:
        goal = Goal.WANDER
        target = None
    ttl = rng.randint(GOAL_TTL_MIN, GOAL_TTL_MAX)
    return ActiveGoal(goal=goal, target=target, ttl=ttl)


def reflex_step(
    c: Creature,
    world: World,
    creatures: list[Creature],
    goal: ActiveGoal,
    rng: random.Random,
) -> Intent:
    """Biến mục tiêu thành Intent di chuyển thuần và tất định."""
    if not c.alive:
        return Intent(creature_id=c.id, path=())

    moves = c.traits.moves_per_tick

    if goal.goal in (Goal.REST, Goal.GUARD):
        return Intent(creature_id=c.id, path=())

    if goal.goal == Goal.FORAGE:
        # Cây gần nhất trong tầm nhìn
        # `food_for(c)`, không phải `world.plants`. Một con cá hỏi `world.plants`
        # sẽ nhắm vào quả trên ô `PLAIN` mà nó không bao giờ vào được — bơi về
        # phía bờ rồi đứng đó tới chết, trông y như tầng phản xạ hỏng.
        visible_plants = [
            p
            for p in world.food_for(c)
            if world.dist(c.pos, p) <= c.traits.sight_radius
        ]
        if not visible_plants:
            path = _wander_path(c.pos, moves, world, rng, c)
        else:
            # Hoà thì chọn ô có toạ độ nhỏ nhất
            target_plant = min(
                visible_plants,
                key=lambda p: (world.dist(c.pos, p), p),
            )
            path = _greedy_path_towards(c.pos, target_plant, moves, world, c)
        return Intent(creature_id=c.id, path=path)

    if goal.goal == Goal.HUNT:
        target_c = _find_creature_by_id(creatures, goal.target)
        if target_c is None:
            path = _wander_path(c.pos, moves, world, rng, c)
            return Intent(creature_id=c.id, path=path)

        if world.dist(c.pos, target_c.pos) <= 1:
            return Intent(creature_id=c.id, path=(), attack_id=target_c.id)

        path = _greedy_path_towards(c.pos, target_c.pos, moves, world, c)
        end_pos = path[-1] if path else c.pos
        attack_id = target_c.id if world.dist(end_pos, target_c.pos) <= 1 else None
        return Intent(creature_id=c.id, path=path, attack_id=attack_id)

    if goal.goal == Goal.FLEE:
        target_c = _find_creature_by_id(creatures, goal.target)
        if target_c is None:
            path = _wander_path(c.pos, moves, world, rng, c)
        else:
            path = _greedy_path_away(c.pos, target_c.pos, moves, world, c)
        return Intent(creature_id=c.id, path=path)

    if goal.goal == Goal.FOLLOW:
        seen = visible(c, world, creatures)
        same_species = [
            other
            for other in seen
            if other.species == c.species
        ]
        if not same_species:
            path = _wander_path(c.pos, moves, world, rng, c)
        else:
            target_c = min(
                same_species,
                key=lambda other: (world.dist(c.pos, other.pos), creature_sort_key(other)),
            )
            path = _greedy_path_towards(c.pos, target_c.pos, moves, world, c)
        return Intent(creature_id=c.id, path=path)

    # Goal.WANDER hoặc fallback
    path = _wander_path(c.pos, moves, world, rng, c)
    return Intent(creature_id=c.id, path=path)


def _find_creature_by_id(creatures: list[Creature], cid: str | None) -> Creature | None:
    if cid is None:
        return None
    for other in creatures:
        if other.id == cid and other.alive:
            return other
    return None


def _greedy_path_towards(
    start_pos: tuple[int, int],
    target_pos: tuple[int, int],
    max_steps: int,
    world: World,
    who: Creature | None = None,
) -> tuple[tuple[int, int], ...]:
    """Tìm đường tham lam tiến về đích: giảm dist nhiều nhất, phá hoà bằng toạ độ nhỏ nhất.

    `who` là con vật ĐANG đi. Không truyền nó thì đường đi được tính cho một sinh
    vật cạn trung bình, và cả tầng nước lẫn tầng trời sẽ đi theo bản đồ của người
    khác — W-18 bất biến 2 hỏng ngay ở đây, im lặng."""
    path: list[tuple[int, int]] = []
    curr = start_pos
    for _ in range(max_steps):
        curr_dist = world.dist(curr, target_pos)
        if curr_dist == 0:
            break
        passable_neighbors = [p for p in world.neighbors(curr) if world.passable(p, who)]
        if not passable_neighbors:
            break
        min_d = min(world.dist(p, target_pos) for p in passable_neighbors)
        if min_d >= curr_dist:
            break
        best = min(
            (p for p in passable_neighbors if world.dist(p, target_pos) == min_d),
            key=lambda pos: (pos[0], pos[1]),
        )
        path.append(best)
        curr = best
    return tuple(path)


def _greedy_path_away(
    start_pos: tuple[int, int],
    target_pos: tuple[int, int],
    max_steps: int,
    world: World,
    who: Creature | None = None,
) -> tuple[tuple[int, int], ...]:
    """Tìm đường tham lam chạy xa đích: tăng dist nhiều nhất, phá hoà bằng toạ độ nhỏ nhất."""
    path: list[tuple[int, int]] = []
    curr = start_pos
    for _ in range(max_steps):
        curr_dist = world.dist(curr, target_pos)
        passable_neighbors = [p for p in world.neighbors(curr) if world.passable(p, who)]
        if not passable_neighbors:
            break
        max_d = max(world.dist(p, target_pos) for p in passable_neighbors)
        if max_d <= curr_dist:
            break
        best = min(
            (p for p in passable_neighbors if world.dist(p, target_pos) == max_d),
            key=lambda pos: (pos[0], pos[1]),
        )
        path.append(best)
        curr = best
    return tuple(path)


def _wander_path(
    start_pos: tuple[int, int],
    max_steps: int,
    world: World,
    rng: random.Random,
    who: Creature | None = None,
) -> tuple[tuple[int, int], ...]:
    """Đi ngẫu nhiên từng bước sang ô lân cận passable."""
    path: list[tuple[int, int]] = []
    curr = start_pos
    for _ in range(max_steps):
        candidates = [p for p in world.neighbors(curr) if world.passable(p, who)]
        if not candidates:
            break
        nxt = rng.choice(candidates)
        path.append(nxt)
        curr = nxt
    return tuple(path)


def apply_intent(
    intent: Intent,
    by_id: dict[str, Creature],
    world: World,
) -> int:
    """Áp dụng Intent cho sinh vật: cập nhật vị trí và trừ năng lượng di chuyển."""
    c = by_id.get(intent.creature_id)
    if c is None or not c.alive:
        return 0
    steps = 0
    for pos in intent.path:
        # Bẫy: chỉ đi vào ô passable — và passable CỦA CON NÀY. Con vật đã ở
        # trong tay rồi thì không có cớ gì hỏi bằng bản đồ của loài khác.
        if not world.passable(pos, c):
            break
        c.pos = world.wrap(*pos)
        c.energy -= config.COST_MOVE
        steps += 1
    return steps

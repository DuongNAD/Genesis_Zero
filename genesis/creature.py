"""Genesis Zero — creature: thực thể sống và kinh tế năng lượng."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from genesis import config
from genesis.traits import Traits, founder_traits
from genesis.world import World


@dataclass
class Creature:
    id: str                 # "<species_id>:<n>"
    species: str
    traits: Traits
    pos: tuple[int, int]
    hp: float
    energy: float
    age: int = 0
    alive: bool = True
    dead_until: int = -1
    poison_ticks: int = 0
    poison_from: str | None = None
    adapt_points: int = 0
    eat_count: int = 0
    win_count: int = 0
    ticks_alive_streak: int = 0
    shift_log: list[tuple[str, str]] = field(default_factory=list)
    last_drink_tick: int = -1
    stun_ticks: int = 0
    # Đời thứ mấy của DÒNG DÕI này. `id` định danh dòng dõi, không phải cá thể:
    # giữ nguyên id qua các đời để khe prefix cache, khoá Sổ Luật, sổ ghi công và
    # đường replay không phải dựng lại mỗi lần có con chết (64 lần một ván).
    generation: int = 0


def spawn_population(world: World, rng: random.Random) -> list[Creature]:
    """Tạo quần thể ban đầu trên các ô passable ngẫu nhiên.

    Bẫy: species_id lấy động từ config.POPULATION lúc chạy, không hardcode.
    Danh sách trả về PHẢI được sắp xếp theo id cố định để thứ tự duyệt tất định.
    """
    passable_cells = [
        (x, y)
        for y in range(world.h)
        for x in range(world.w)
        if world.passable((x, y))
    ]
    if not passable_cells:
        raise RuntimeError("Không có ô passable nào để thả sinh vật")

    creatures: list[Creature] = []
    for species_id, count in config.POPULATION.items():
        traits = founder_traits(species_id)
        for i in range(count):
            cid = f"{species_id}:{i}"
            pos = rng.choice(passable_cells)
            creatures.append(
                Creature(
                    id=cid,
                    species=species_id,
                    traits=traits,
                    pos=pos,
                    hp=float(config.HP_MAX),
                    energy=traits.energy_max,
                )
            )

    creatures.sort(key=creature_sort_key)
    return creatures


def creature_sort_key(c: Creature) -> tuple[str, int]:
    """Khoá sắp xếp CHUẨN cho mọi chỗ duyệt creature (bất biến B4).

    Bẫy: đừng sắp bằng chính chuỗi `id`. Sắp chuỗi thì "L5:10" rơi vào giữa
    "L5:1" và "L5:2" ngay khi một loài vượt 9 con — thứ tự duyệt đổi, ván đổi,
    và không có gì báo lỗi. Tách phần số ra rồi sắp bằng số.
    """
    species, _, idx = c.id.rpartition(":")
    return (species, int(idx))


def random_step(c: Creature, world: World, rng: random.Random) -> int:
    """Đi ngẫu nhiên tối đa c.traits.moves_per_tick ô sang ô lân cận passable."""
    if not c.alive:
        return 0
    steps_taken = 0
    for _ in range(c.traits.moves_per_tick):
        candidates = [p for p in world.neighbors(c.pos) if world.passable(p)]
        if not candidates:
            break
        c.pos = rng.choice(candidates)
        c.energy -= config.COST_MOVE
        steps_taken += 1
    return steps_taken


def upkeep_and_check_death(c: Creature, tick: int) -> bool:
    """Trừ upkeep và kiểm tra chết đói.

    Bẫy: nếu đã chết từ trước thì trả False, không báo chết lần hai.
    """
    if not c.alive:
        return False
    c.age += 1
    c.energy -= c.traits.upkeep
    if c.energy <= 0:
        c.alive = False
        return True
    return False


def resolve_eat(c: Creature, world: World) -> float:
    """Ăn cây tại ô c.pos nếu có, tăng năng lượng và trả về năng lượng nhận được."""
    if not c.alive:
        return 0.0
    gained = world.eat_plant(c.pos)
    if gained > 0:
        # Trần năng lượng: ăn khi đã no thì phần thừa mất đi, không tích luỹ.
        gained = min(gained, max(c.traits.energy_max - c.energy, 0.0))
        c.energy += gained
    return gained


def kill(c: Creature, world: World, tick: int, cause: str = "starve") -> None:
    """Xử lý sinh vật chết: chuyển alive=False, để lại xác, hẹn giờ hồi sinh."""
    c.alive = False
    c.dead_until = tick + config.RESPAWN_DELAY
    world.corpses[c.pos] = tick


def try_respawn(c: Creature, world: World, tick: int, rng: random.Random) -> bool:
    """Hồi sinh sinh vật khi đã hết thời gian chờ chết.

    Bẫy: chỉ hồi sinh ở ô passable, reset age=0 nhưng giữ nguyên id và trí nhớ.
    """
    if c.alive or c.dead_until < 0 or tick < c.dead_until:
        return False
    passable_cells = [
        (x, y)
        for y in range(world.h)
        for x in range(world.w)
        if world.passable((x, y))
    ]
    if not passable_cells:
        return False
    c.pos = rng.choice(passable_cells)
    c.energy = float(config.RESPAWN_ENERGY_RATIO * c.traits.energy_max)
    c.hp = float(config.HP_MAX)
    c.age = 0
    c.alive = True
    c.dead_until = -1
    c.poison_ticks = 0
    c.poison_from = None
    c.last_drink_tick = -1
    c.stun_ticks = 0
    return True

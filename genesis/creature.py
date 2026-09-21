"""Genesis Zero — creature: thực thể sống và kinh tế năng lượng."""

from __future__ import annotations

import contextlib
import random
from dataclasses import dataclass, field

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

    # ── M1_EVO: Dòng dõi & Đặc điểm cá thể ────────────────────────────────
    parent_id: str | None = None
    lineage_id: str = ""
    birth_tick: int = 0
    reproduce_cooldown: int = 0
    features: tuple[str, ...] = ()
    _kit: object | None = field(default=None, repr=False, compare=False)
    _sort_key: tuple[str, int] | None = field(default=None, repr=False, compare=False)
    _cached_passable: tuple[object, object, frozenset] | None = field(default=None, repr=False, compare=False)
    _subj_dict: dict[str, bool] | None = field(default=None, repr=False, compare=False)
    _subj_traits: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.lineage_id and self.id:
            self.lineage_id = self.id
        if self._sort_key is None and self.id:
            species, _, idx = self.id.rpartition(":")
            try:
                self._sort_key = (species, int(idx))
            except ValueError:
                self._sort_key = (species, 999999)

    @property
    def kit(self) -> object | None:
        if self._kit is not None:
            return self._kit
        if not self.features:
            return None
        from genesis.features import BY_KEY, kit_of
        feats = tuple(BY_KEY[k] for k in self.features if k in BY_KEY)
        if feats:
            self._kit = kit_of(feats)
            return self._kit
        return None

    @kit.setter
    def kit(self, val: object | None) -> None:
        self._kit = val


def allocate_creature_id(species: str, creatures: list[Creature]) -> str:
    """Cấp phát ID số nguyên tiếp theo cho cá thể mới sinh theo format `{species}:{idx}`.

    Bảo đảm `int(idx)` trong `creature_sort_key` không bao giờ gặp lỗi ValueError.
    """
    max_idx = -1
    for c in creatures:
        if c.species == species:
            s_sp, _, s_idx = c.id.rpartition(":")
            if s_sp == species and s_idx.isdigit():
                val = int(s_idx)
                if val > max_idx:
                    max_idx = val
    return f"{species}:{max_idx + 1}"


def spawn_population(world: World, rng: random.Random) -> list[Creature]:
    """Tạo quần thể ban đầu trên các ô passable ngẫu nhiên.

    Bẫy: species_id lấy động từ config.POPULATION lúc chạy, không hardcode.
    Danh sách trả về PHẢI được sắp xếp theo id cố định để thứ tự duyệt tất định.
    """
    creatures: list[Creature] = []
    for species_id, count in config.POPULATION.items():
        traits = founder_traits(species_id)
        # Ô ĐI ĐƯỢC CỦA LOÀI NÀY, không phải ô đi được của một sinh vật cạn
        # trung bình. Bản cũ hỏi `world.passable((x, y))` không truyền con vật,
        # nên nó **thả cá lên đồng cỏ** — và con cá ấy không đi được một bước
        # nào, không ăn được gì, chết ở đúng chỗ nó sinh ra.
        mau = Creature(id=f"{species_id}:0", species=species_id, traits=traits,
                       pos=(0, 0), hp=1.0, energy=1.0)
        o_song = [
            (x, y)
            for y in range(world.h)
            for x in range(world.w)
            if world.passable((x, y), mau)
        ]
        if not o_song:
            # Loài không có chỗ nào sống được trên bản đồ này -> KHÔNG thả.
            # Ném ở đây là chặn cả ván vì một loài không hợp bản đồ; bỏ qua nó
            # thì bốn loài kia vẫn chơi được, và `HOANG_MAC` vẫn là một ván hợp
            # lệ dù nó không nuôi nổi cá.
            continue
        # Quần thể CO THEO môi trường sống. Xem `config.CELLS_PER_CREATURE`.
        n = max(1, min(count, len(o_song) // config.CELLS_PER_CREATURE))
        for i in range(n):
            cid = f"{species_id}:{i}"
            pos = rng.choice(o_song)
            creatures.append(
                Creature(
                    id=cid,
                    species=species_id,
                    traits=traits,
                    pos=pos,
                    hp=float(config.HP_MAX),
                    energy=traits.energy_max,
                    lineage_id=cid,
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
    sk = getattr(c, "_sort_key", None)
    if sk is not None:
        return sk
    species, _, idx = c.id.rpartition(":")
    try:
        sk = (species, int(idx))
    except ValueError:
        sk = (species, 999999)
    with contextlib.suppress(AttributeError, TypeError):
        c._sort_key = sk
    return sk



def random_step(c: Creature, world: World, rng: random.Random) -> int:
    """Đi ngẫu nhiên tối đa c.traits.moves_per_tick ô sang ô lân cận passable."""
    if not c.alive:
        return 0
    steps_taken = 0
    weather_mod = getattr(getattr(world, "weather", None), "modifiers", None)
    move_mult = getattr(weather_mod, "move_cost_mult", 1.0) if weather_mod else 1.0
    for _ in range(c.traits.moves_per_tick):
        candidates = [p for p in world.neighbors(c.pos) if world.passable(p, c)]
        if not candidates:
            break
        c.pos = rng.choice(candidates)
        c.energy -= config.COST_MOVE * move_mult
        steps_taken += 1
    return steps_taken


def upkeep_and_check_death(c: Creature, tick: int, kit=None) -> bool:
    """Trừ upkeep và kiểm tra chết đói.

    `kit` là ba đặc điểm của loài (W-19): lông dài và túi má đỡ hao sức, vỏ sò
    thì tốn thêm. Nhân chứ không cộng — hai đặc điểm cùng giảm thì tích vẫn > 0,
    còn cộng trừ thì đủ hai cái là upkeep âm và con vật **kiếm được năng lượng
    bằng cách đứng yên**.

    Bẫy: nếu đã chết từ trước thì trả False, không báo chết lần hai.
    """
    if not c.alive:
        return False
    c.age += 1
    effective_kit = kit if kit is not None else getattr(c, "kit", None)
    c.energy -= c.traits.upkeep * (getattr(effective_kit, "upkeep_mult", 1.0) if effective_kit else 1.0)
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
    if c.parent_id is not None:
        c.dead_until = -1
    else:
        c.dead_until = tick + config.RESPAWN_DELAY
    world.corpses[c.pos] = tick


def try_respawn(
    c: Creature,
    world: World,
    tick: int,
    rng: random.Random,
    creatures: list[Creature] | None = None,
) -> bool:
    """Hồi sinh sinh vật khi đã hết thời gian chờ chết.

    Bẫy: chỉ hồi sinh ở ô passable, reset age=0 nhưng giữ nguyên id và trí nhớ.
    """
    if c.alive or c.dead_until < 0 or tick < c.dead_until or c.parent_id is not None:
        return False
    pool = creatures if creatures is not None else getattr(world, "creatures", None)
    if pool is not None:
        alive_all = [x for x in pool if x.alive]
        if len(alive_all) >= config.POPULATION_GLOBAL_MAX:
            return False
        alive_sp = [x for x in alive_all if x.species == c.species]
        if len(alive_sp) >= config.POPULATION_SPECIES_MAX:
            return False
    import genesis.world as _gw
    dom_mod = _gw._domain_mod or _gw._get_domain()
    species = getattr(c, "species", "")
    kit = getattr(c, "kit", None) or getattr(world, "kits", {}).get(species)
    cached_p = getattr(c, "_cached_passable", None)
    if cached_p is not None and cached_p[0] is c.traits and cached_p[1] is kit:
        p_set = cached_p[2]
    else:
        dom = dom_mod.domain_of(species)
        p_set = frozenset(t for t in _gw.Terrain if dom_mod.can_enter(dom, t, c.traits, kit))
        with contextlib.suppress(AttributeError, TypeError):
            c._cached_passable = (c.traits, kit, p_set)

    grid = world.grid
    passable_cells = [
        (x, y)
        for y in range(world.h)
        for x in range(world.w)
        if grid[y][x] in p_set
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


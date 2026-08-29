"""Genesis Zero — world: lưới, địa hình, khoảng cách toroidal."""

from __future__ import annotations

from enum import StrEnum
import random
from typing import TYPE_CHECKING

from genesis import config, law_config
from genesis.surface import SurfaceMap, roll_surface_map

if TYPE_CHECKING:
    from genesis.creature import Creature


# 4 hướng di chuyển cho random walk tạo mảng liền khối
CARDINAL_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
)

# 8 hướng lân cận theo thứ tự cố định (B2: N, NE, E, SE, S, SW, W, NW)
NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, -1),   # N
    (1, -1),   # NE
    (1, 0),    # E
    (1, 1),    # SE
    (0, 1),    # S
    (-1, 1),   # SW
    (-1, 0),   # W
    (-1, -1),  # NW
)


class Terrain(StrEnum):
    PLAIN = "PLAIN"
    WATER = "WATER"
    BUSH = "BUSH"
    ROCK = "ROCK"
    FIRE = "FIRE"


TERRAIN_GLYPHS: dict[Terrain, str] = {
    Terrain.PLAIN: ".",
    Terrain.WATER: "~",
    Terrain.BUSH: '"',
    Terrain.ROCK: "#",
    Terrain.FIRE: "^",
}

PLANT_GLYPH: str = "*"
CORPSE_GLYPH: str = "x"

FRUIT_CLASSES: tuple[str, ...] = tuple(
    f"FRUIT_{chr(ord('A') + i)}" for i in range(law_config.FRUIT_KINDS)
)


class World:
    """Lưới thế giới 2D, quản lý địa hình và tính toán hình học không gian."""

    def __init__(
        self,
        w: int,
        h: int,
        rng: random.Random,
        surface_map: SurfaceMap | None = None,
        map_name: str | None = None,
    ) -> None:
        self.w: int = w
        self.h: int = h
        # `map_name=None` -> đúng bộ sinh cũ, từng byte. Mọi số đo cân bằng của
        # W-12 dựa trên nó, nên bản đồ mới KHÔNG được đổi bản mặc định.
        self.map_name: str = map_name or "DONG_CO"
        self.plant_scale: float = 1.0
        if map_name is not None:
            from genesis.maps import MAPS
            self.plant_scale = MAPS[map_name].plant_scale
        if map_name is None:
            self.grid = self._generate_terrain(rng)
        else:
            from genesis.maps import MAPS, generate_terrain
            self.grid = generate_terrain(MAPS[map_name], w, h, rng)
        # Bẫy: dùng dict, không dùng set để đảm bảo thứ tự lặp tất định
        self.fruits: dict[tuple[int, int], str] = {}
        self.corpses: dict[tuple[int, int], int] = {}
        self.wind: str = rng.choice(law_config.WIND_DIRS)
        self.surface_map: SurfaceMap = (
            surface_map if surface_map is not None else roll_surface_map(rng)
        )

    @property
    def plants(self) -> dict[tuple[int, int], str]:
        return self.fruits

    @plants.setter
    def plants(self, value: dict[tuple[int, int], str]) -> None:
        self.fruits = value

    def _generate_terrain(self, rng: random.Random) -> list[list[Terrain]]:
        # Mặc định toàn bộ bản đồ là PLAIN
        grid: list[list[Terrain]] = [
            [Terrain.PLAIN for _ in range(self.w)] for _ in range(self.h)
        ]

        # Rải hạt giống cho từng loại địa hình phi-PLAIN (thứ tự cố định)
        walkers: list[tuple[int, int, Terrain]] = []
        # FIRE KHÔNG sinh tự nhiên: law_config.FIRE_BASE_SPREAD = False nên lửa chỉ
        # xuất hiện khi có luật SPREAD (L-02+). Sinh sẵn ô lửa trơ vừa vô nghĩa vừa
        # ăn mất ô PLAIN, làm lệch cân bằng đã tune ở W-12.
        for terrain in (Terrain.WATER, Terrain.BUSH, Terrain.ROCK):
            for _ in range(config.TERRAIN_SEEDS_PER_TYPE):
                walkers.append((rng.randrange(self.w), rng.randrange(self.h), terrain))

        # Đặt hạt giống lên lưới
        for x, y, terrain in walkers:
            grid[y][x] = terrain

        # Lan ngẫu nhiên theo kiểu random walk từng bước xen kẽ
        for _ in range(config.TERRAIN_WALK_STEPS):
            new_walkers: list[tuple[int, int, Terrain]] = []
            for cx, cy, terrain in walkers:
                dx, dy = rng.choice(CARDINAL_OFFSETS)
                nx, ny = self.wrap(cx + dx, cy + dy)
                grid[ny][nx] = terrain
                new_walkers.append((nx, ny, terrain))
            walkers = new_walkers

        return grid

    def wrap(self, x: int, y: int) -> tuple[int, int]:
        """Wrap toạ độ vào biên lưới theo config.TOROIDAL."""
        if config.TOROIDAL:
            return x % self.w, y % self.h
        # Bẫy: khi TOROIDAL=False thì kẹp vào biên
        nx = max(0, min(self.w - 1, x))
        ny = max(0, min(self.h - 1, y))
        return nx, ny

    def dist(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        """Khoảng cách Chebyshev có xét vòng mép toroidal ở CẢ HAI chiều."""
        ax, ay = a
        bx, by = b
        dx = abs(ax - bx)
        dy = abs(ay - by)
        if config.TOROIDAL:
            # Bẫy: phải wrap ở cả hai chiều dx và dy
            dx = min(dx, self.w - dx)
            dy = min(dy, self.h - dy)
        return max(dx, dy)

    def neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """Trả về 8 ô lân cận theo thứ tự cố định."""
        x, y = pos
        if config.TOROIDAL:
            return [self.wrap(x + dx, y + dy) for dx, dy in NEIGHBOR_OFFSETS]

        res: list[tuple[int, int]] = []
        for dx, dy in NEIGHBOR_OFFSETS:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < self.w and 0 <= ny < self.h:
                res.append((nx, ny))
        return res

    def passable(self, pos: tuple[int, int], creature=None) -> bool:
        """Kiểm tra ô có đi qua được không. ROCK không đi qua được.

        Bẫy: PHẢI wrap trước khi lập chỉ mục. Không wrap thì `pos = (-1, -1)`
        lọt qua lập chỉ mục âm của Python và im lặng trả về ô ở góc đối diện,
        còn `(24, 24)` thì ném IndexError. Cả hai đều là bug ở mép bản đồ.
        """
        x, y = self.wrap(*pos)
        return self.grid[y][x] != Terrain.ROCK

    def eat_plant(self, pos: tuple[int, int]) -> float:
        """Ăn cây tại pos nếu có, trả về năng lượng. Phải wrap trước khi tra."""
        x, y = self.wrap(*pos)
        if (x, y) in self.fruits:
            del self.fruits[(x, y)]
            return float(config.PLANT_ENERGY)
        return 0.0


def spawn_plants(world: World, rng: random.Random, tick: int = 0) -> int:
    """Sinh thêm cây trên ô PLAIN trống mỗi tick.

    Mỗi cây mọc ra mang một LỚP FRUIT_A..D (rải đều).
    Bẫy: kiểm trần PLANT_MAX trước mỗi lần mọc và dừng ngay khi không còn ô
    PLAIN trống, tránh lặp vô hạn khi bản đồ đầy.
    """
    room = config.PLANT_MAX - len(world.fruits)
    if room <= 0:
        return 0
    candidates = [
        (x, y)
        for y in range(world.h)
        for x in range(world.w)
        if world.grid[y][x] == Terrain.PLAIN and (x, y) not in world.fruits
    ]
    if not candidates:
        return 0
    # Kẹp theo CẢ trần lẫn số ô trống -> không đường nào vượt PLANT_MAX,
    # và quét lưới đúng MỘT lần thay vì một lần cho mỗi cây.
    # Hệ số thức ăn theo bản đồ (W-15): M1 được tune cho ĐỒNG CỎ, và đổi địa
    # hình là đổi độ khó — sa mạc ít ô đi được thì cùng một lượng quả lại dày hơn.
    scale = getattr(world, "plant_scale", 1.0)
    n = min(max(1, round(config.PLANT_RESPAWN * scale)), room, len(candidates))
    for pos in rng.sample(candidates, n):
        world.fruits[pos] = rng.choice(FRUIT_CLASSES)
    return n


def decay_corpses(world: World, tick: int) -> int:
    """Xoá mọi xác đã tồn tại quá config.CORPSE_DECAY tick, trả về số xác đã xoá."""
    to_remove = [
        pos
        for pos, created_tick in world.corpses.items()
        if tick - created_tick >= config.CORPSE_DECAY
    ]
    for pos in to_remove:
        del world.corpses[pos]
    return len(to_remove)


def visible(obs: Creature, world: World, creatures: list[Creature]) -> list[Creature]:
    """Danh sách sinh vật mà `obs` NHÌN THẤY được, sắp theo creature_sort_key."""
    from genesis.creature import creature_sort_key

    # Bẫy B1: Bán kính nhìn lấy từ người quan sát (obs), không phải từ con bị nhìn
    sight_radius = obs.traits.sight_radius
    seen: list[Creature] = []
    for other in creatures:
        # Bẫy B2: Con chết không xuất hiện; không tự thấy chính mình
        if not other.alive or other is obs:
            continue
        d = world.dist(obs.pos, other.pos)
        if d > sight_radius:
            continue
        # Bẫy B6: Bụi rậm xét ô của con BỊ NHÌN, vô hình nếu d > 1
        ox, oy = world.wrap(*other.pos)
        if world.grid[oy][ox] == Terrain.BUSH and d > 1:
            continue
        seen.append(other)

    # Bẫy B3: Thứ tự trả về cố định theo creature_sort_key
    seen.sort(key=creature_sort_key)
    return seen


def phase_at(tick: int) -> str:
    """Trả 'DAY' hoặc 'NIGHT' theo chu kỳ law_config.PHASE_LEN."""
    phase_idx = (tick // law_config.PHASE_LEN) % 2
    return "DAY" if phase_idx == 0 else "NIGHT"

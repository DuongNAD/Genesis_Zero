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
    WATER = "WATER"      # nước NÔNG (mép nước): cạn lội vào uống được, cá sống được
    BUSH = "BUSH"
    ROCK = "ROCK"
    FIRE = "FIRE"
    # ── W-18, hai ô mới ──────────────────────────────────────────────────
    # Chỉ HAI. "Không quá to nhưng phải đầy đủ" đạt được bằng cách tăng số
    # CÁCH XẾP chứ không tăng số loại: ao là một mảng WATER nhỏ, hồ là WATER
    # có lõi DEEP, biển là DEEP lớn viền WATER. Bảy loại địa hình cho ba tầng
    # và ba kiểu nước.
    DEEP = "DEEP"        # nước sâu — chỉ tầng NƯỚC; cạn chết đuối, trời bay qua
    TREE = "TREE"        # cây — cạn phải đủ `speed` mới trèo; đây là "khỉ/sư tử"
    CAVE = "CAVE"        # hang — LÕI của khối đá, chỉ loài biết đào hang vào được


TERRAIN_GLYPHS: dict[Terrain, str] = {
    Terrain.PLAIN: ".",
    Terrain.WATER: "~",
    Terrain.BUSH: '"',
    Terrain.ROCK: "#",
    Terrain.FIRE: "^",
    Terrain.DEEP: "≈",
    Terrain.TREE: "T",
    Terrain.CAVE: "C",
}

# Mã MỘT KÝ TỰ cho đường truyền (khung xem live gửi địa hình dạng chuỗi).
# Một bảng, và mọi chỗ mã hoá địa hình phải đọc từ đây. Trước W-18 thì
# `net/match.py` giữ chuỗi `"PWBRF"` chép tay cùng một tuple thứ tự chép tay —
# thêm một địa hình là ném `ValueError` ở giữa vòng phát khung cho người xem.
TERRAIN_CODE: dict[Terrain, str] = {
    Terrain.PLAIN: "P",
    Terrain.WATER: "W",
    Terrain.BUSH: "B",
    Terrain.ROCK: "R",
    Terrain.FIRE: "F",
    Terrain.DEEP: "D",
    Terrain.TREE: "T",
    Terrain.CAVE: "C",
}

# Thứ tự GIEO HẠT địa hình. Một tuple, và cả hai đường dựng lưới đọc từ đây.
#
# Thứ tự là một phần của bất biến tái lập: nó quyết định RNG được tiêu theo thứ
# tự nào, nên đổi thứ tự là đổi mọi bản đồ của mọi seed. Thêm loại mới thì thêm
# vào CUỐI.
#
# `FIRE` không có mặt: lửa không sinh tự nhiên, nó chỉ đến từ luật `SPREAD`
# (W-13). `DEEP` cũng không: nó không được gieo, nó được xói ra từ lõi nước.
SEEDED_TERRAINS: tuple[Terrain, ...] = (
    Terrain.WATER, Terrain.BUSH, Terrain.ROCK, Terrain.TREE,
)

PLANT_GLYPH: str = "*"
CORPSE_GLYPH: str = "x"

FRUIT_CLASSES: tuple[str, ...] = tuple(
    f"FRUIT_{chr(ord('A') + i)}" for i in range(law_config.FRUIT_KINDS)
)


def erode_cores(grid: list[list[Terrain]], w: int, h: int) -> list[list[Terrain]]:
    """Lõi của mảng nước thành NƯỚC SÂU; lõi của mảng bụi thành CÂY (W-18).

    Không thêm hạt giống mới, chỉ soi lại lưới đã có: ô nào **bốn phía đều cùng
    loại với nó** thì nó nằm trong lõi, không nằm ở mép.

    Cách này cho ba kiểu nước của đề bài mà không cần thêm loại địa hình nào:

        ao   = mảng WATER nhỏ  -> không ô nào đủ bốn hàng xóm -> toàn nước nông
        hồ   = mảng WATER vừa  -> một lõi DEEP nhỏ, viền WATER
        biển = mảng WATER lớn  -> lõi DEEP lớn, viền WATER

    Cùng phép ấy cho đá, và nó cho ra HANG: lõi của một khối đá là chỗ rỗng bên
    trong. Hang **nằm lọt giữa đá** nên không ai đi bộ tới được — chỉ loài biết
    ĐÀO HANG mới vào, vì nó xuyên qua chính lớp đá bao quanh (`DAO_HANG` mở khoá
    cả `ROCK` lẫn `CAVE`). Nên hang là chỗ trốn **tuyệt đối**: kẻ săn nhìn thấy
    con mồi biến mất vào vách đá và không có đường nào theo vào.

    Và nó **bảo đảm bờ bằng cấu trúc**, không bằng kỷ luật: một ô chỉ thành DEEP
    khi bốn phía là nước, nên quanh mọi vùng DEEP luôn còn một viền WATER. Bờ
    nước là ô DUY NHẤT mà tầng NƯỚC và tầng CẠN đứng cạnh nhau được (W-18 §7) —
    mất bờ là ba tầng thành ba ván rời nhau.

    **Chỉ nước, KHÔNG áp cho bụi.** Bản đầu cho lõi bụi thành CÂY — nghe hợp lý
    (giữa rừng thì có tán) và nó **làm hỏng đúng bản đồ rừng**: chỗ bụi dày nhất
    thành ô không vào được, sinh vật bị đẩy ra khoảng trống, và `RUNG_RAM` hoá ra
    cho nhìn thấy nhau **nhiều hơn** `DONG_CO` (2,617 so với 2,534) — ngược hẳn
    lý do bản đồ ấy tồn tại (Q2: giao tiếp đáng giá bao nhiêu).

    Bài học đáng giữ: **độ sâu** là tính chất của lõi nên xói mòn là đúng; **cây**
    là thứ MỌC LÊN nên nó phải được gieo hạt như mọi địa hình khác. Hai thứ khác
    nhau về bản chất thì đừng dùng chung một cơ chế chỉ vì code gọn hơn.

    Hàm này ở cấp module vì có **hai** đường dựng lưới — `World._generate_terrain`
    và `maps.generate_terrain` — và bản đầu tôi chỉ sửa một. Đó là lần thứ chín
    của cùng một họ lỗi trong dự án này, lần này tôi tự tay dựng ra nó. Hai đường
    dựng lưới vẫn là một chỗ đáng gom nữa, nhưng gom chúng là một việc riêng.
    """
    out = [row[:] for row in grid]
    core = {Terrain.WATER: Terrain.DEEP, Terrain.ROCK: Terrain.CAVE}
    for y in range(h):
        for x in range(w):
            here = grid[y][x]
            becomes = core.get(here)
            if becomes is None:
                continue
            # Đọc từ `grid` (ảnh GỐC), ghi vào `out`. Đọc từ bản đang ghi thì ô
            # duyệt trước ảnh hưởng ô duyệt sau và lưới phụ thuộc thứ tự quét —
            # cùng họ với bẫy đồng thời của W-11.
            if all(grid[(y + dy) % h][(x + dx) % w] == here
                   for dx, dy in CARDINAL_OFFSETS):
                out[y][x] = becomes
    return out


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
        # Đặc điểm sinh học theo LOÀI (W-19). Rỗng = ván trước W-19, chạy y hệt
        # như cũ. `build_match` điền vào; loài lạ đăng ký giữa ván thì `.get`
        # trả `None` và con vật ấy đơn giản là không có đặc điểm nào.
        self.kits: dict[str, object] = {}
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
        # Pha hiện tại. `phase_at` là hàm thuần của tick, nên đây chỉ là bản ghi
        # nhớ để `visible` khỏi phải nhận thêm tham số ở cả 14 chỗ gọi. `tick`
        # cập nhật mỗi lượt; mặc định DAY để mọi bài kiểm cũ chạy y hệt.
        self.phase: str = "DAY"
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
        for terrain in SEEDED_TERRAINS:
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

        return erode_cores(grid, self.w, self.h)

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
        """Ô này con vật NÀY đi được không.

        `creature=None` nghĩa là "hỏi cho một sinh vật CẠN trung bình" — đường
        cũ, giữ lại cho bộ sinh quần thể và cho mọi bài kiểm viết trước W-18.

        Đây là đường **DUY NHẤT** trả lời câu "ai đi được đâu" (W-18 bất biến 2).
        `reflex`, render, client, bộ sinh bản đồ đều phải hỏi qua đây. Dựng bảng
        thứ hai ở chỗ khác là lặp lại đúng cái họ lỗi đã cắn tám lần: hai bản của
        một khái niệm, rồi bản ít người nhìn hơn mục đi.

        Bẫy: PHẢI wrap trước khi lập chỉ mục. Không wrap thì `pos = (-1, -1)`
        lọt qua lập chỉ mục âm của Python và im lặng trả về ô ở góc đối diện,
        còn `(24, 24)` thì ném IndexError. Cả hai đều là bug ở mép bản đồ.
        """
        from genesis.domain import Domain, can_enter, domain_of

        x, y = self.wrap(*pos)
        terrain = self.grid[y][x]
        if creature is None:
            return can_enter(Domain.CAN, terrain, None)
        return can_enter(domain_of(creature.species), terrain, creature.traits,
                         self.kits.get(creature.species))

    def touchable(self, pos: tuple[int, int], creature) -> bool:
        """Con vật này ĂN / UỐNG / ĐÁNH được ở ô này không (W-18 bất biến 3)."""
        from genesis.domain import can_touch, domain_of

        x, y = self.wrap(*pos)
        return can_touch(domain_of(creature.species), self.grid[y][x], creature.traits)

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
    # ĐÊM LÀM NGẮN TẦM NHÌN (W-19). Trước đó ngày và đêm khác nhau đúng một
    # chuỗi trong prompt và một trigger `PHASE_ENTER` — nó không đổi một hành vi
    # nào. Nên đặc điểm "mắt đêm" hứa một lợi thế chống lại **một bất lợi không
    # tồn tại**, tức là hình 3D nói dối. Cho đêm một cái giá là cách rẻ nhất để
    # cả chu kỳ ngày/đêm thành một biến số thật, và để một ổ sinh thái ăn đêm
    # trở nên đáng chọn.
    sight_radius = obs.traits.sight_radius
    if world.phase == "NIGHT":
        kit = world.kits.get(obs.species)
        if not (kit is not None and getattr(kit, "night_sight", False)):
            sight_radius = max(1, sight_radius - config.NIGHT_SIGHT_PENALTY)
    seen: list[Creature] = []
    for other in creatures:
        # Bẫy B2: Con chết không xuất hiện; không tự thấy chính mình
        if not other.alive or other is obs:
            continue
        d = world.dist(obs.pos, other.pos)
        if d > sight_radius:
            continue
        # Bẫy B6: Bụi rậm xét ô của con BỊ NHÌN, vô hình nếu d > 1.
        # CÂY che khuất y như bụi (W-18) — và đó không phải chuyện cho đẹp: cây
        # là ô mà chỉ loài biết trèo vào được, nên nếu nó không che thì "trốn lên
        # cây" chỉ là đứng trên bục cho cả bản đồ nhìn. Chỗ trốn phải trốn được.
        ox, oy = world.wrap(*other.pos)
        if world.grid[oy][ox] in (Terrain.BUSH, Terrain.TREE) and d > 1:
            continue
        seen.append(other)

    # Bẫy B3: Thứ tự trả về cố định theo creature_sort_key
    seen.sort(key=creature_sort_key)
    return seen


def phase_at(tick: int) -> str:
    """Trả 'DAY' hoặc 'NIGHT' theo chu kỳ law_config.PHASE_LEN."""
    phase_idx = (tick // law_config.PHASE_LEN) % 2
    return "DAY" if phase_idx == 0 else "NIGHT"

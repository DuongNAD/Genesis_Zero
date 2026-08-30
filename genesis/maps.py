"""Genesis Zero — maps: nhiều bản đồ, mỗi cái đổi *thứ có thể học được* (W-15).

Một bản đồ không phải là trang trí. Nó quyết định **luật nào quan sát được**:
sa mạc gần như không có ô nước, nên mọi luật gắn với `DRINK` ở đó là câu đố không
có lời giải — hệt như một cond không quan sát được ở [L-02]. Vì thế:

**Cổng khả giải phải chạy theo cặp `(bản đồ, seed)`, không phải theo seed.**
`generate_cached` đã khoá theo `(arm, seed)`; bản đồ đi vào `arm` để đệm không
trộn hai thế giới khác nhau vào một khoá.

Năm bản đồ, mỗi cái nhấn một chiều khác nhau của trò chơi:

| Bản đồ | Đổi cái gì | Hệ quả lên trò chơi |
|---|---|---|
| `DONG_CO`  | mặc định, cân bằng | ván chuẩn để so |
| `HOANG_MAC`| ít nước, nhiều đá | uống nước thành sự kiện hiếm; luật `DRINK` khó học |
| `QUAN_DAO` | nhiều nước, đất vụn | di chuyển bị chặn, quần thể tách đàn |
| `HEM_NUI`  | đá thành vách, chừa hành lang | ép chạm mặt nhau; luật `ADJACENT` dễ học |
| `RUNG_RAM` | dày bụi rậm | tầm nhìn bị chặn, `sense` đáng giá hẳn lên |

`RUNG_RAM` là bản đồ đáng chú ý nhất về mặt thiết kế: bụi rậm chặn tầm nhìn
(W-08), mà tầm nghe lấy theo `sight_radius` của người nghe (B-11) — nên nó vừa
làm quan sát gián tiếp khó hơn, vừa làm kênh nói ngắn lại. Đó là bản đồ để hỏi
*"giao tiếp đáng giá bao nhiêu?"* (Q2).
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from genesis import config
from genesis.world import CARDINAL_OFFSETS, SEEDED_TERRAINS, Terrain, erode_cores


@dataclass(frozen=True)
class MapSpec:
    """Một bản đồ = số hạt giống mỗi loại địa hình + số bước lan."""

    name: str
    vn: str
    seeds: dict[Terrain, int]
    walk_steps: int
    note: str
    # Hệ số thức ăn. M1 được tune ở W-12 cho ĐỒNG CỎ; đổi địa hình là đổi độ khó,
    # nên mỗi bản đồ cần một nút riêng để kéo về cùng một dải khó.
    plant_scale: float = 1.0

    def total_seeds(self) -> int:
        return sum(self.seeds.values())


MAPS: dict[str, MapSpec] = {
    "DONG_CO": MapSpec(
        "DONG_CO", "Đồng cỏ",
        {Terrain.WATER: 4, Terrain.BUSH: 4, Terrain.ROCK: 4, Terrain.TREE: 2},
        config.TERRAIN_WALK_STEPS,
        "bản chuẩn, đã tune ở W-12 — mọi bản đồ khác so với nó",
    ),
    "HOANG_MAC": MapSpec(
        "HOANG_MAC", "Hoang mạc",
        {Terrain.WATER: 1, Terrain.BUSH: 1, Terrain.ROCK: 12, Terrain.TREE: 0},
        36,
        "uống nước thành sự kiện hiếm — luật DRINK ở đây rất khó học",
    ),
    "QUAN_DAO": MapSpec(
        "QUAN_DAO", "Quần đảo",
        {Terrain.WATER: 10, Terrain.BUSH: 3, Terrain.ROCK: 2, Terrain.TREE: 1},
        34,
        "đất vụn thành đảo, quần thể tách đàn và ít gặp nhau",
    ),
    "HEM_NUI": MapSpec(
        "HEM_NUI", "Hẻm núi",
        {Terrain.WATER: 3, Terrain.BUSH: 2, Terrain.ROCK: 9, Terrain.TREE: 1},
        40,
        "đá thành vách, chừa hành lang — ép chạm mặt, luật ADJACENT dễ học",
    ),
    "RUNG_RAM": MapSpec(
        "RUNG_RAM", "Rừng rậm",
        {Terrain.WATER: 3, Terrain.BUSH: 11, Terrain.ROCK: 1, Terrain.TREE: 5},
        38,
        "bụi rậm chặn tầm nhìn VÀ tầm nghe — bản đồ để hỏi giao tiếp đáng giá bao nhiêu",
        plant_scale=1.3,
    ),
}

DEFAULT_MAP = "DONG_CO"

# ─── Cân bằng đo được (5 seed × 400 tick, không luật, chỉ phản xạ) ───────────
#
# | bản đồ    | chết nhiều nhất | chưa từng chết | tổng chết |
# |-----------|-----------------|----------------|-----------|
# | DONG_CO   | 8               | 0/75           | 329       |  ✅ đúng M1
# | HOANG_MAC | 9               | 0/75           | 430       |  khó hơn
# | HEM_NUI   | 9               | 0/75           | 410       |  khó hơn
# | QUAN_DAO  | 9               | 3/75           | 309       |  bất bình đẳng
# | RUNG_RAM  | 8               | 2/75           | 192       |  bất bình đẳng
#
# **M1 là tính chất của ĐỒNG CỎ, không phải của mọi bản đồ.** Ngưỡng "chết nhiều
# nhất ≤ 8, không ai bất tử" được tune ở W-12 cho đúng một địa hình; đổi địa hình
# là đổi bài toán. Đã quét `plant_scale` từ 0,8 tới 3,0 trên cả năm bản đồ:
#
# * Ở `HOANG_MAC` và `HEM_NUI`, **thêm thức ăn không cứu được** — chết ở đó đến
#   từ chen chúc và đánh nhau (ít ô đi được hơn), không từ đói. Đây là hai bản
#   đồ *khó hơn*, và đó là chủ ý.
# * Ở `QUAN_DAO` và `RUNG_RAM`, đất vụn tạo ra **túi an toàn**: vài con không bao
#   giờ chết trong khi con khác chết chín lần. Bất bình đẳng ấy là **tính chất
#   của bản đồ**, không phải lỗi cân bằng — và nó chính là thứ làm cho câu hỏi
#   "giao tiếp đáng giá bao nhiêu" (Q2) có nghĩa ở `RUNG_RAM`.
#
# Nên: đừng ép mọi bản đồ về cùng một con số. Ghi số ra, và khi so hai ván thì
# **so trong cùng một bản đồ**.


def generate_terrain(spec: MapSpec, w: int, h: int, rng: random.Random) -> list[list[Terrain]]:
    """Cùng thuật toán random-walk của W-02, khác ở số hạt giống và số bước.

    Giữ nguyên thuật toán là có chủ ý: đổi cả cách sinh thì mọi số đo cân bằng
    của [W-12](../docs/tasks/W-12-thich-nghi.md) phải làm lại từ đầu, và ta sẽ
    không biết khác biệt giữa hai bản đồ đến từ địa hình hay từ bộ sinh.

    `FIRE` vẫn KHÔNG sinh tự nhiên ở bất kỳ bản đồ nào — lửa chỉ xuất hiện qua
    luật `SPREAD` (W-13).
    """
    grid = [[Terrain.PLAIN for _ in range(w)] for _ in range(h)]

    walkers: list[tuple[int, int, Terrain]] = []
    # `SEEDED_TERRAINS`, không phải một tuple chép tay. Bản chép tay ở đây đã
    # lặng lẽ bỏ qua `Terrain.TREE` dù cả năm bản đồ đều khai số hạt cho nó —
    # không lỗi, không cảnh báo, chỉ là không có cây nào mọc.
    for terrain in SEEDED_TERRAINS:
        for _ in range(spec.seeds.get(terrain, 0)):
            walkers.append((rng.randrange(w), rng.randrange(h), terrain))
    for x, y, terrain in walkers:
        grid[y][x] = terrain

    for _ in range(spec.walk_steps):
        nxt: list[tuple[int, int, Terrain]] = []
        for cx, cy, terrain in walkers:
            dx, dy = rng.choice(CARDINAL_OFFSETS)
            nx, ny = (cx + dx) % w, (cy + dy) % h
            grid[ny][nx] = terrain
            nxt.append((nx, ny, terrain))
        walkers = nxt
    # Cùng phép xói mòn với `World._generate_terrain` — MỘT hàm, hai đường gọi.
    # Bản đầu của W-18 chỉ sửa đường kia, nên năm bản đồ không sinh ra ô DEEP nào
    # và tôi suýt kết luận là ngưỡng đặt sai.
    return erode_cores(grid, w, h)


def terrain_mix(grid: list[list[Terrain]]) -> dict[str, float]:
    """Tỉ lệ từng loại ô. Dùng để kiểm rằng một bản đồ THẬT SỰ khác bản đồ kia."""
    flat = [t for row in grid for t in row]
    n = len(flat) or 1
    return {t.value: round(sum(1 for x in flat if x == t) / n, 4) for t in Terrain}

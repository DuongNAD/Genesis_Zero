# W-03 · Sinh thức ăn

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | W-02 |
| **Chặn** | W-05 |
| **File** | `genesis/world.py` |
| **Ước lượng** | ~25 dòng · 30 phút |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 3 |

## 1. Mục tiêu
Nguồn năng lượng vào hệ. Tốc độ mọc so với `upkeep` của 15 con là **cái van chính** điều khiển độ khắc nghiệt của thế giới — bạn sẽ vặn nó rất nhiều ở W-12.

## 2. Đầu vào đã có
`config.PLANT_RESPAWN = 4`, `PLANT_MAX = 40`, `PLANT_ENERGY = 30`.

## 3. Việc phải làm
1. `spawn_plants(world, rng)` gọi **mỗi tick**, tôn trọng `PLANT_RESPAWN` và trần `PLANT_MAX`.
2. Plant chỉ mọc trên `PLAIN`, không mọc lên ô đã có plant.
3. Lưu bằng `dict[tuple[int,int], int]` (vị trí → tick mọc), không phải `set`.

## 4. Chữ ký và bất biến
```python
def spawn_plants(world: World, rng: random.Random) -> int:
    """Trả số plant thực sự mọc trong tick này."""
```
**Bất biến:** dùng `dict`, không `set` — [W-01](W-01-rng-config.md) bất biến 2.

## 5. Bẫy
Trần `PLANT_MAX` phải kiểm **trước mỗi lần mọc**, không phải một lần đầu vòng lặp. Kiểm một lần thì tick nào cũng có thể vượt trần tối đa `PLANT_RESPAWN − 1` và tổng trôi lên chậm rãi qua hàng trăm tick.

## 6. Nghiệm thu
```bash
python - <<'PY'
import random; from genesis.world import World, spawn_plants
w = World(24,24,random.Random(3)); r = random.Random(3)
for _ in range(100): spawn_plants(w, r)
assert len(w.plants) == 40, len(w.plants)
assert all(w.grid[y][x].name == "PLAIN" for (x,y) in w.plants)
print("OK")
PY
```

# W-02 · Lưới, địa hình, khoảng cách toroidal

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | W-01 |
| **Chặn** | W-03, W-04 |
| **File** | `genesis/world.py` |
| **Ước lượng** | ~60 dòng · 1 giờ |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 2 |

## 1. Mục tiêu
Không gian mà mọi thứ khác sống trong đó. `dist` sẽ được gọi hàng triệu lần và mọi quyết định phụ thuộc vào nó — sai ở đây thì mọi thứ phía trên lệch một cách tinh vi.

## 2. Đầu vào đã có
`config.GRID_W`, `GRID_H`, `TOROIDAL`.

## 3. Việc phải làm
1. `Terrain` enum: `PLAIN WATER BUSH ROCK`.
2. Sinh địa hình từ `rng`: mảng vá liền khối, không phải nhiễu muối tiêu. Cách rẻ nhất: rải N hạt giống rồi cho lan ngẫu nhiên K bước.
3. `wrap`, `dist`, `neighbors`, `passable`.

## 4. Chữ ký và bất biến
```python
class Terrain(StrEnum): PLAIN = "PLAIN"; WATER = "WATER"; BUSH = "BUSH"; ROCK = "ROCK"

class World:
    def __init__(self, w: int, h: int, rng: random.Random) -> None: ...
    def wrap(self, x: int, y: int) -> tuple[int, int]: ...
    def dist(self, a: tuple[int,int], b: tuple[int,int]) -> int: ...   # Chebyshev, CÓ wrap
    def neighbors(self, pos) -> list[tuple[int,int]]: ...              # 8 hướng, thứ tự CỐ ĐỊNH
    def passable(self, pos, creature) -> bool: ...                     # ROCK không đi được
```
**Bất biến 1:** `dist` tính wrap ở **cả hai chiều**: `dx = min(dx, W - dx)`, tương tự `dy`, rồi `max(dx, dy)`.
**Bất biến 2:** `neighbors` trả thứ tự **cố định** (ví dụ N, NE, E, SE, S, SW, W, NW). Thứ tự đổi → pathfind tham lam chọn khác → ván khác. Đây là một nguồn phi-tất-định mà không ai ngờ tới.

## 5. Bẫy
`dist((0,0),(23,23)) == 1` trên lưới 24×24 toroidal. Nếu bạn ra 23 thì `wrap` sai và **con vật ở mép bản đồ sẽ hành xử kỳ quặc** — v4 nói bạn sẽ mất một buổi tối tìm. Viết test này trước khi viết `dist`.

## 6. Nghiệm thu
```bash
python - <<'PY'
import random; from genesis.world import World, Terrain
w = World(24, 24, random.Random(7))
assert w.dist((0,0),(23,23)) == 1
assert w.dist((0,0),(12,12)) == 12
assert len(w.neighbors((0,0))) == 8
assert w.neighbors((5,5)) == w.neighbors((5,5))          # thứ tự ổn định
from collections import Counter
c = Counter(w.grid[y][x] for y in range(24) for x in range(24))
assert all(c[t] >= 20 for t in Terrain), c                # cả 4 loại đều có mặt đáng kể
print("OK", c)
PY
python -m genesis.run --seed 7 --print-map   # nhìn bằng mắt: có mảng, không phải muối tiêu
```

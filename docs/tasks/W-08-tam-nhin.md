# W-08 · Tầm nhìn và bụi rậm

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-07 |
| **Chặn** | W-09 |
| **File** | `genesis/world.py` |
| **Ước lượng** | ~25 dòng · 30 phút |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 8 |

## 1. Mục tiêu
Bất đối xứng thông tin. Đây là nền của **toàn bộ** tầng xã hội sau này — nghe lén, ăn theo, lừa nhau — và ở v5 nó còn quyết định luật nào **quan sát được** (Gate A, [03 §3.2](../03-LUAT-AN-V5.md)).

## 2. Đầu vào đã có
`Traits.sight_radius`, `World.dist`, `Terrain.BUSH`.

## 3. Việc phải làm
1. `visible(observer, world, creatures) -> list[Creature]`, lọc `dist <= sight_radius`.
2. Con đứng trong `BUSH` **vô hình** trừ khi `dist <= 1`.
3. Trả về theo **thứ tự id cố định**.

## 4. Chữ ký và bất biến
```python
def visible(obs: Creature, world: World, creatures: list[Creature]) -> list[Creature]: ...
```
**Bất biến 1:** dùng `sight_radius` của **người quan sát**, không phải của người bị quan sát.
**Bất biến 2:** con chết (`alive=False`) không xuất hiện trong `visible`; corpse là thực thể riêng của thế giới.
**Bất biến 3:** thứ tự trả về cố định.

## 5. Bẫy
Bất biến 1 sẽ bị vi phạm lại ở [B-11](B-11-noi-danh-tieng.md) khi làm kênh nói: **nghe được hay không dùng `sense` của người nghe**, không phải của người nói. Đó là điều làm `sense` cao thành "nghe lén giỏi". Viết hàm này cho đúng bây giờ để có mẫu để chép.

## 6. Nghiệm thu
```bash
python - <<'PY'
import random
from genesis.world import World, Terrain
from genesis.creature import Creature
from genesis.traits import Traits
from genesis import config
from genesis.world import visible
w = World(24,24,random.Random(1))
w.grid[10][10] = Terrain.BUSH
hider = Creature("L2:0","L2",(10,10),50,100)
seer  = Creature("L1:0","L1",(12,10),50,100)     # sight_radius 3, dist 2
assert visible(seer, w, [hider, seer]) == []          # trong bụi, cách 2 -> KHÔNG thấy
seer.pos = (11,10)                                     # dist 1
assert visible(seer, w, [hider, seer]) == [hider]      # cách 1 -> thấy
print("OK")
PY
```

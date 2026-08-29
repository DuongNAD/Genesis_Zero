# W-05 · Ăn, chết, xác, hồi sinh

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | W-04, W-03 |
| **Chặn** | W-06 |
| **File** | `genesis/world.py`, `genesis/creature.py` |
| **Ước lượng** | ~50 dòng · 1 giờ |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 5 |

## 1. Mục tiêu
Vòng khép kín: năng lượng vào, năng lượng ra, chết, quay lại. Sau việc này thế giới **tự chạy mãi** mà không cạn — điều kiện để ván 400 tick có ý nghĩa.

## 2. Đầu vào đã có
`spawn_plants` từ W-03, `Creature` từ W-04.

## 3. Việc phải làm
1. Đi lên ô có plant → ăn, `+PLANT_ENERGY`, plant biến mất.
2. `energy <= 0` → chết: `alive = False`, để lại corpse tại `pos`, `dead_until = tick + RESPAWN_DELAY`.
3. Corpse có `CORPSE_ENERGY`, tan sau `CORPSE_DECAY` tick.
4. Tới hạn → hồi sinh ở vị trí ngẫu nhiên `passable`, `energy = RESPAWN_ENERGY_RATIO * energy_max`, `hp = HP_MAX`, `age = 0`.

## 4. Chữ ký và bất biến
```python
def resolve_eat(c: Creature, world: World) -> float: ...      # trả năng lượng nhận
def kill(c: Creature, world: World, tick: int, cause: str) -> None: ...
def try_respawn(c: Creature, world: World, tick: int, rng) -> bool: ...
```
**Bất biến 1:** creature chết **vẫn nằm trong danh sách**, chỉ `alive = False`. **Không xoá khỏi list** — id phải ổn định suốt ván.
**Bất biến 2:** `age` reset khi hồi sinh; `id` thì không bao giờ.
**Bất biến 3 (chuẩn bị cho v5):** trí nhớ và Sổ Luật **không** bị xoá khi chết. Chết mất cơ thể, không mất hiểu biết ([03 §4.4](../03-LUAT-AN-V5.md)). Ở M0 chưa có gì để giữ, nhưng đừng viết một `reset_all()` mà sau này phải gỡ.

## 5. Bẫy
Hai con cùng bước lên một ô plant trong cùng tick. Ai ăn? Phải quyết bằng **quy tắc tất định** (id nhỏ hơn ăn), không phải bằng thứ tự duyệt. Đây là ca đầu tiên của vấn đề đồng thời mà W-11 sẽ giải tổng quát — giải tạm ở đây cho đúng, đừng giải sai rồi quen tay.

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 11 --ticks 300 --out /tmp/w05.jsonl
python - <<'PY'
import json, collections
rows=[json.loads(l) for l in open('/tmp/w05.jsonl')]
k=collections.Counter(r["kind"] for r in rows)
assert k["DEATH"]>0 and k["RESPAWN"]>0, k
pop=collections.Counter()
for r in rows:
    if r["kind"]=="DEATH": pop[r["creature_id"]]+=1
assert len({r["creature_id"] for r in rows if r["creature_id"]})==15
print("OK", k)
PY
```

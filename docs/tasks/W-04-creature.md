# W-04 · Creature và năng lượng

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | W-02 |
| **Chặn** | W-05, W-07 |
| **File** | `genesis/creature.py` |
| **Ước lượng** | ~45 dòng · 45 phút |
| **Giao cho model rẻ?** | ❌ v4 §10 |
| **Tài liệu gốc** | v4 Bước 4 |

## 1. Mục tiêu
Thực thể sống. Ở M0 dùng hằng số cứng cho mọi con — trait vào ở W-07. Mục đích là thấy **kinh tế năng lượng** hoạt động trước khi thêm bất kỳ biến nào.

## 2. Đầu vào đã có
`World` từ W-02.

## 3. Việc phải làm
1. `Creature` dataclass theo §4.
2. Ở M0: `energy_max = 100`, `upkeep = 3.0`, `moves_per_tick = 1` cho mọi con. Cứng, tạm.
   > **Đã bị thay thế 2026-08-28 bởi [W-07](W-07-trait.md).** Ba hằng số `M0_*` đã gỡ khỏi
   > `config.py`; giờ mỗi con dùng chỉ số dẫn xuất từ vector trait của loài mình.
3. Thả 15 con ở vị trí ngẫu nhiên trên ô `passable`.

## 4. Chữ ký và bất biến
```python
@dataclass
class Creature:
    id: str                 # "L1:0" — KHÔNG mã hoá chỉ số loài, xem N-03
    species: str
    pos: tuple[int, int]
    hp: float
    energy: float
    age: int = 0
    alive: bool = True
    dead_until: int = -1
```
**Bất biến 1:** `id` **ổn định suốt ván**, kể cả khi chết và hồi sinh. Slot LLM ghim theo id ([02 §3](../02-SANDBOX-V4.md)).
**Bất biến 2:** danh sách creature duyệt theo **thứ tự id cố định** ở mọi pha. Không bao giờ duyệt theo thứ tự chèn hay theo `sorted()` trên một khoá đổi được.

## 5. Bẫy
`id` là `f"{species_id}:{n}"` với `species_id` **cấp lúc chạy**, không phải hằng số import-time. Ở Lab mode nó tình cờ luôn là `"L1"`, và nếu bạn hardcode thì [N-02](N-02-seam-registry.md) sẽ phải viết lại tầng này. Đường may thứ 3 của [04 §5](../04-THE-GIOI-MO.md).

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 5 --ticks 60 --out /tmp/w04.jsonl
python - <<'PY'
import json
rows=[json.loads(l) for l in open('/tmp/w04.jsonl')]
deaths={r["creature_id"] for r in rows if r["kind"]=="DEATH"}
assert len(deaths)==15, deaths      # 15 con, chết đói HẾT trước tick 40
last=max(r["t"] for r in rows if r["kind"]=="DEATH")
assert last < 40, last
print("OK, con cuối chết ở tick", last)
PY
```

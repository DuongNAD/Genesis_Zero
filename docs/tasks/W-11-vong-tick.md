# W-11 · Vòng tick hoàn chỉnh  ★

| | |
|---|---|
| **Track** | World (v4 M1) |
| **Phụ thuộc** | W-09, W-10 |
| **Chặn** | W-12, L-02, B-05, N-08 |
| **File** | `genesis/world.py` |
| **Ước lượng** | ~100 dòng · 2–3 giờ |
| **Giao cho model rẻ?** | ❌ **tuyệt đối không** — tính đồng thời, không test nào bắt được lỗi tinh vi |
| **Tài liệu gốc** | v4 Bước 11 |

## 1. Mục tiêu
Trái tim của sim. Mọi thứ sau này dựa vào nó, và mọi bug tinh vi nhất của dự án sẽ nằm ở đây. Viết chậm.

## 2. Đầu vào đã có
Mọi thứ từ W-03 tới W-10.

## 3. Việc phải làm — sáu pha, đúng thứ tự này
```python
def tick(world, creatures, tick_no, rng, laws=None):
    # 1. THU intent — duyệt theo THỨ TỰ ID CỐ ĐỊNH, KHÔNG áp dụng gì
    # 2. RESOLVE đồng thời:  di chuyển -> chiến đấu -> ăn
    # 3. ÁP DỤNG chi phí:    upkeep, cost_move, cost_attack, cost_think
    # 4. LUẬT ẨN             <- chỗ L-02 cắm vào, để sẵn tham số `laws`
    # 5. CHẾT / HỒI SINH
    # 6. THẾ GIỚI            spawn plant, phân huỷ corpse, lan lửa, chuyển pha ngày/đêm
    #    GHI LOG
```

## 4. Chữ ký và bất biến
```python
def tick(world: World, creatures: list[Creature], tick_no: int,
         rng: random.Random, laws: list["Law"] | None = None) -> None: ...
```
**Bất biến 1 — quan trọng nhất:** thu **hết** intent rồi mới áp dụng. Trộn hai pha vào một vòng lặp là con đường ngắn nhất tới bug không tái lập được.
**Bất biến 2:** kết quả **không phụ thuộc thứ tự creature trong list**. Đây là bài kiểm tra ở §6 và nó là bài kiểm tra quan trọng nhất của cả dự án.
**Bất biến 3:** danh sách creature **thay đổi được giữa ván** — thêm được (loài mới join ở chế độ mở), không xoá khi chết. Đường may thứ 4 của [04 §5](../04-THE-GIOI-MO.md).
**Bất biến 4:** tham số `laws` có mặt từ **bây giờ**, mặc định `None`. Thêm tham số vào chữ ký này sau khi 5 module gọi nó là một buổi tối sửa import.

## 5. Bẫy
- **Pha 6 không được sửa sinh vật**, chỉ sửa thế giới. Luật `SPREAD` ở v5 sửa **địa hình** nên nó thuộc pha 6, không phải pha 4 ([03 §11 L3](../03-LUAT-AN-V5.md)).
- **Ghi log ở cuối, một chỗ.** Rải `log.write` khắp các pha thì thứ tự dòng phụ thuộc luồng điều khiển và `diff` giữa hai lần chạy sẽ đỏ vì lý do vô hại.

## 6. Nghiệm thu — bài kiểm tra quan trọng nhất dự án
```bash
python - <<'PY'
import random, json, copy
from genesis.run import build_world
# chạy 200 tick với danh sách theo thứ tự gốc
w1, c1 = build_world(seed=99)
w2, c2 = build_world(seed=99)
random.Random(5).shuffle(c2)          # HOÁN VỊ thứ tự creature trong list
from genesis.world import tick
r1 = random.Random(99); r2 = random.Random(99)
for t in range(200): tick(w1, c1, t, r1)
for t in range(200): tick(w2, c2, t, r2)
s1 = sorted((c.id, round(c.energy,4), c.pos, c.hp, c.alive) for c in c1)
s2 = sorted((c.id, round(c.energy,4), c.pos, c.hp, c.alive) for c in c2)
assert s1 == s2, "THỨ TỰ LIST ẢNH HƯỞNG KẾT QUẢ -> pha 1 và 2 đang bị trộn"
print("ĐỒNG THỜI OK")
PY
```
> Test này đỏ nghĩa là bạn đang áp dụng intent trong lúc thu intent. Quay lại pha 1. Đừng vá bằng cách `sort` ở đâu đó — đó là giấu triệu chứng.

# W-06 · Render terminal và log  ✦ CHỐT M0

| | |
|---|---|
| **Track** | World (v4 M0) |
| **Phụ thuộc** | W-05, S-04 |
| **Chặn** | W-07 |
| **File** | `genesis/render.py`, `genesis/run.py` |
| **Ước lượng** | ~70 dòng · 1 giờ |
| **Giao cho model rẻ?** | ⚠️ bố cục giao được; quyết định hiển thị gì thì tự |
| **Tài liệu gốc** | v4 Bước 6, [02 §5](../02-SANDBOX-V4.md) |

## 1. Mục tiêu
Nhìn thấy thế giới. Và chạy **bài kiểm tra rẻ nhất của cả dự án**: ngồi xem nó chạy — có đủ vui để muốn xem tiếp không?

## 2. Đầu vào đã có
`LogWriter` từ S-04, vòng đời đầy đủ từ W-05.

## 3. Việc phải làm
1. `rich.live.Live`: lưới ký tự + panel bên cạnh hiện hp/energy/age từng con.
2. Glyph theo `hashlib.md5(species_id)` từ pool ~30 ký tự Unicode. **Không dùng chữ cái** — với loài động thì chữ cái hết rất nhanh và chẳng mang nghĩa gì ([02 §5](../02-SANDBOX-V4.md)).
3. Màu theo hue loài, độ sáng theo `energy / energy_max`. Con chết vẽ mờ.
4. Ghi JSONL song song, `--no-render` để chạy nhanh không vẽ.

## 4. Chữ ký và bất biến
```python
def render_frame(world: World, creatures: list[Creature], tick: int) -> RenderableType: ...
def glyph_of(species_id: str) -> str: ...   # md5, KHÔNG dùng hash()
```
**Bất biến:** render **không bao giờ** sửa trạng thái. Nó là hàm thuần từ trạng thái ra ảnh. Vi phạm thì `--no-render` sẽ cho ván khác và bạn mất tính tái lập.

## 5. Bẫy
`hash()` của Python có salt ngẫu nhiên mỗi tiến trình — xem [W-01](W-01-rng-config.md) bất biến 3. Dùng `hashlib`.

## 6. Nghiệm thu — ✦ CHỐT M0
```bash
# 1. chạy 300 tick không crash, có render
python -m genesis.run --seed 21 --ticks 300

# 2. hai lần cùng seed cho JSONL GIỐNG HỆT
python -m genesis.run --seed 21 --ticks 300 --no-render --out /tmp/a.jsonl
python -m genesis.run --seed 21 --ticks 300 --no-render --out /tmp/b.jsonl
diff /tmp/a.jsonl /tmp/b.jsonl && echo "TÁI LẬP OK"

# 3. render bật/tắt cho cùng kết quả
python -m genesis.run --seed 21 --ticks 300 --out /tmp/c.jsonl
diff /tmp/a.jsonl /tmp/c.jsonl && echo "RENDER THUẦN OK"
```

**4. Bài kiểm tra thứ tư, không tự động hoá được:** ngồi xem 300 tick. Đủ vui để muốn xem tiếp không?

> Nếu M0 đã chán thì **LLM không cứu được**. Sửa thế giới trước khi đi tiếp: mật độ thức ăn, tốc độ, kích thước lưới. Đây là bài kiểm tra rẻ nhất bạn có, và bỏ qua nó là cách tốn kém nhất để phát hiện vấn đề ở tháng thứ ba.

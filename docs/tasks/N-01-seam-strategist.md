# N-01 · Đường may 1 — `Strategist` là interface

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** W-09 · **Chặn** N-04 |
| **File** | `genesis/strategist.py` · ~15 dòng · **15 phút** |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [04 §5](../04-THE-GIOI-MO.md) đường may 1 |

## 1. Mục tiêu
**Mười lăm phút hôm nay, một ngày viết lại nếu để sau.** Ba nguồn quyết định sẽ tồn tại — phản xạ server, llama cục bộ, client từ xa. Hardcode một cái là phải sửa cả tầng gọi khi thêm cái thứ hai.

## 2. Chữ ký và bất biến
```python
class Strategist(Protocol):
    async def decide(self, c: Creature, world: World, ctx: Ctx) -> Decision | None: ...

class ReflexStrategist:        ...   # luôn None -> tầng phản xạ tự lo
class LocalLlamaStrategist:    ...   # B-05
class RemoteClientStrategist:  ...   # N-07, chỉ đọc hàng đợi quyết định
```
**Bất biến 1:** vòng tick gọi `strategist.decide(...)` và **không biết** hiện thực nào đằng sau. Không có `if mode == "remote"` ở bất kỳ đâu trong `world.py`.
**Bất biến 2:** trả `None` là hợp lệ và có nghĩa "không có ý đồ mới, dùng goal cũ". Cả ba hiện thực phải xử lý được.

## 3. Nghiệm thu
```bash
grep -rn "isinstance.*Strategist\|mode ==" genesis/world.py && echo "VI PHẠM BẤT BIẾN 1" && exit 1
pytest tests/test_strategist_protocol.py -q   # cả 3 hiện thực thoả Protocol, cùng chạy được 50 tick
```

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đã có genesis/reflex.py. Đọc trước: docs/tasks/N-01-seam-strategist.md §2.
VIỆC: genesis/strategist.py: typing.Protocol tên Strategist với async decide(c, world, ctx)
-> Decision|None. Ba lớp ReflexStrategist (trả None), LocalLlamaStrategist (stub raise
NotImplementedError), RemoteClientStrategist (đọc từ một dict hàng đợi truyền vào ctor).
Sửa genesis/world.py để nhận strategist qua tham số thay vì gọi thẳng reflex.
tests/test_strategist_protocol.py: cả ba lớp thoả isinstance(..., Strategist) khi dùng
runtime_checkable; chạy 50 tick với ReflexStrategist không lỗi.
RÀNG BUỘC: KHÔNG thêm nhánh if theo chế độ trong world.py; không tạo file khác.
NGHIỆM THU: pytest tests/test_strategist_protocol.py -q
TRẢ VỀ: chỉ diff.
```

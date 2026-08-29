# N-06 · `/work` long-poll

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-04 · **Chặn** N-07, N-10 |
| **File** | `net/routes_work.py` · ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [05 §3.2 §3.3](../05-GIAO-THUC.md) |

## 1. Mục tiêu
Kênh phát việc. Long-poll vì nó chạy sau **mọi** NAT và firewall mà không cần cấu hình gì — đó là lý do "máy ở đâu cũng được" thành sự thật.

## 2. Chữ ký và bất biến
Hình dạng `WorkItem` chính xác ở [05 §3.3](../05-GIAO-THUC.md).

**Bất biến 1 — gửi khối A–D **một lần** qua `/match/brief`, không gửi lại mỗi tick.** Prompt v5 dài ~1550 token; gửi lại phần bất biến mỗi lần là lãng phí gấp 3 băng thông, và tệ hơn — nó cám dỗ bạn "sửa nhẹ" khối system giữa ván, phá prefix cache của client mà bạn không biết. Gửi một lần thì bất biến "system giống nhau từng byte" được **giao thức** bảo vệ.
**Bất biến 2 — server gửi cả `json_schema`.** Client không biết LawDSL, không biết bộ goal. Nhờ vậy client ~120 dòng và **không bao giờ phải cập nhật** khi bạn đổi luật chơi ([05 §1](../05-GIAO-THUC.md)).
**Bất biến 3 — `deadline_tick = issued_tick + LATE_TOLERANCE`.**
**Bất biến 4 — hold tối đa 25 s** rồi trả `204`. Đừng giữ lâu hơn; proxy trung gian sẽ tự cắt và client thấy lỗi khó hiểu.

## 3. Nghiệm thu
```bash
pytest tests/test_work.py -q
# ca: pha != RUNNING -> 204 · có việc -> trả ngay, không chờ hết hold
#     không việc -> giữ ~25s rồi 204 · mỗi item có đủ trường ở 05 §3.3
#     /match/brief gọi 2 lần trong một ván -> system_prompt GIỐNG HỆT NHAU từng byte
python scripts/net_smoke.py --server http://localhost:8000 --fake-model
# 3 client giả cùng poll 60 giây, không client nào bị bỏ đói
```

## 4. Prompt giao việc
```
BỐI CẢNH: FastAPI + asyncio. Đọc trước: docs/05-GIAO-THUC.md §3.2 và §3.3 (hình dạng JSON
CHÍNH XÁC). Đã có: net/server.py (MatchRunner với hàng đợi việc theo client_id),
genesis/prompt.py (system_block, user_block), genesis/strategist.py (schema_for).
VIỆC: net/routes_work.py:
- GET /v1/match/brief: trả match_id, ticks_total, tick_ms, late_tolerance, và dict creatures
  với system_prompt (ghép từ system_block), think_interval, think_offset, token_budget,
  id_slot_hint. Cache theo (match_id, creature_id) để LUÔN trả cùng chuỗi.
- GET /v1/work?hold_ms=N: long-poll asyncio.Event trên hàng đợi của client. Trả ngay nếu
  có việc; nếu không, chờ tối đa min(hold_ms, 25000) rồi 204. Ngoài pha RUNNING -> 204.
  Mỗi item đủ trường ở 05 §3.3, user_block từ user_block(), json_schema từ schema_for().
tests/test_work.py theo 5 ca ở §3, dùng httpx.ASGITransport.
RÀNG BUỘC: KHÔNG gửi lại system_prompt trong work item. Không busy-wait — dùng
asyncio.Event/Condition. Không tạo/sửa file khác.
NGHIỆM THU: pytest tests/test_work.py -q
TRẢ VỀ: chỉ diff.
```

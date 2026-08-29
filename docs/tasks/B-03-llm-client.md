# B-03 · `llm_client` async, ghim slot

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** S-02 · **Chặn** B-05, N-10 |
| **File** | `genesis/llm_client.py` · ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ✅ hạ tầng thuần |
| **Tài liệu gốc** | v4 Bước 15, Bước 21–22 |

## 1. Mục tiêu
Một lớp gọi model duy nhất, dùng cho cả Lab lẫn client ở chế độ mở.

## 2. Chữ ký và bất biến
```python
async def ask(base_url: str, slot_id: int, system: str, user: str,
              max_tokens: int, schema: dict, timeout: float = 20.0) -> dict | None: ...

class CircuitBreaker:
    def record(self, ok: bool, tick_no: int = 0) -> None: ...
    def is_open_at(self, tick_no: int) -> bool: ...   # hết 50 tick thì tự đóng
    @property
    def is_open(self) -> bool: ...     # 3 lỗi liên tiếp -> mở
```
**Bất biến 1:** gọi `/completion`, **không** `/v1/chat/completions` — chỉ endpoint gốc nhận `id_slot`.
**Bất biến 2:** `{"id_slot": slot_id, "cache_prompt": True}` luôn có mặt. Cùng `creature_id` → **cùng slot suốt ván**, không bao giờ đổi.
**Bất biến 3:** lỗi → trả `None`, không ném. Người gọi rơi về phản xạ. `except: pass` thì không, luôn log.
**Bất biến 3b:** phải có hạn **tự mở lại**. Khi đã ngắt thì không ai gọi model nữa, nên sẽ không bao giờ có một lần thành công để đóng nó lại — ngắt mạch không đồng hồ là ngắt mạch vĩnh viễn. Vì thế `record` và `is_open_at` đều nhận `tick_no`.
**Bất biến 4:** `httpx.AsyncClient` + `asyncio.gather`. **Đừng `await` tuần tự trong vòng lặp** — bug hay gặp nhất khi mới dùng asyncio, và nó biến 4 giây thành 15 giây mà không báo lỗi gì.

## 3. Nghiệm thu
```bash
python scripts/bench_client.py --url http://localhost:8080 --n 50
# valid_json 50/50; t_prefill lần 2 < 1/3 lần 1 (prefix cache hoạt động)
# 5 lời gọi song song mất < 1.5x thời gian 1 lời gọi (gather thật, không tuần tự)
pytest tests/test_circuit_breaker.py tests/test_llm_client.py -q
# cả hai chạy trên httpx.MockTransport: không cần model, không mở cổng, < 1 s.
# test_gather_that_su_song_song đếm số lời gọi CHỒNG NHAU, không đo đồng hồ —
# đo thời gian thì máy bận là đỏ giả.
```

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11 + httpx. Đích là llama.cpp llama-server endpoint /completion.
Đọc trước: docs/tasks/B-03-llm-client.md §2. Đừng đọc tài liệu khác.
VIỆC: genesis/llm_client.py với ask(...) và CircuitBreaker theo chữ ký §2.
Body gửi đi: {"prompt": system+user, "id_slot": slot_id, "cache_prompt": true,
"json_schema": schema, "n_predict": max_tokens, "temperature": 0.7}.
Trả dict đã parse kèm số token thực sinh, hoặc None khi lỗi/timeout (có log warning).
scripts/bench_client.py --url --n: gọi N lần, in tỉ lệ JSON hợp lệ, t_prefill lần 1 vs 2,
và thời gian 5 lời gọi song song so với 1 lời gọi.
tests/test_circuit_breaker.py: 3 lỗi liên tiếp -> is_open True; 1 thành công -> đóng lại.
RÀNG BUỘC: chỉ httpx; KHÔNG await tuần tự trong vòng lặp — dùng asyncio.gather;
không except: pass; không tạo/sửa file khác.
NGHIỆM THU: pytest tests/test_circuit_breaker.py tests/test_llm_client.py -q
# cả hai chạy trên httpx.MockTransport: không cần model, không mở cổng, < 1 s.
# test_gather_that_su_song_song đếm số lời gọi CHỒNG NHAU, không đo đồng hồ —
# đo thời gian thì máy bận là đỏ giả.
TRẢ VỀ: chỉ diff.
```

# N-09 · Rớt mạng, hoang dã, gỡ loài

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-08 · **Chặn** — |
| **File** | `net/health.py` · ~70 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [05 §3.5](../05-GIAO-THUC.md), v4 Bước 22 |

## 1. Mục tiêu
Điện thoại sẽ ngủ, WiFi sẽ rớt. Không phải "nếu" mà là "khi nào".

## 2. Chữ ký và bất biến
```python
HEARTBEAT_MS = 10_000; HEARTBEAT_MISS = 3; FERAL_GRACE = 200   # tick
```
**Bất biến 1 — loài KHÔNG biến mất khi mất kết nối.** Nếu không thì ai sắp chết cũng rút dây. Nó rơi về tầng phản xạ của server và bị đánh dấu **hoang dã**.
**Bất biến 2 — quá `FERAL_GRACE` tick không kết nối thì mới gỡ loài** khỏi registry.
**Bất biến 3 — client quay lại trong thời hạn thì nhận lại loài cũ**, cùng `creature_ids`, cùng codex, cùng danh tiếng. Cấp loài mới là mất hết dữ liệu của người ta.
**Bất biến 4 — con hoang dã vẽ viền đứt** ở [N-12](N-12-xem-live.md) và X-07.

## 3. Nghiệm thu
```bash
pytest tests/test_feral.py -q
# ca: bỏ 3 heartbeat -> is_feral true, ghi NODE_DOWN, con vẫn sống bằng reflex
#     quay lại ở tick +50 -> nhận lại đúng creature_ids và codex nguyên vẹn
#     quay lại ở tick +250 -> loài đã bị gỡ, phải join lại
python scripts/latency_sim.py --profile drop-and-return
```

## 4. Prompt giao việc
```
BỐI CẢNH: FastAPI. Đọc trước: docs/05-GIAO-THUC.md §3.5 và docs/tasks/N-09-hoang-da.md §2.
Đã có: genesis/registry.py (mark_feral, remove), net/server.py (MatchRunner).
VIỆC: net/health.py:
- POST /v1/heartbeat nhận {healthy, queue_depth, model_ready}, cập nhật last_seen_tick.
- HealthMonitor chạy mỗi tick: client bỏ >= 3 nhịp -> registry.mark_feral(True) + log
  NODE_DOWN; quá FERAL_GRACE tick -> registry.remove().
- reclaim(client_id, token): client quay lại trong thời hạn -> mark_feral(False), trả
  ĐÚNG creature_ids cũ. Codex và danh tiếng KHÔNG được reset.
tests/test_feral.py theo 3 ca ở §3.
RÀNG BUỘC: hằng số vào net_config.py, không viết số vào code. Không tạo/sửa file khác.
NGHIỆM THU: pytest tests/test_feral.py -q
TRẢ VỀ: chỉ diff.
```

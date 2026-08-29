# N-07 · `/decision` — nhận và validate phía server

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-06, B-04 · **Chặn** N-08 |
| **File** | `net/routes_decision.py` · ~130 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ khung giao được; **ranh giới tin cậy tự quyết** |
| **Tài liệu gốc** | [05 §3.4](../05-GIAO-THUC.md), [04 §2](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
Ranh giới tin cậy. Đây là nơi thế giới bên ngoài chạm vào trạng thái, và là nơi duy nhất.

## 2. Chữ ký và bất biến
Payload ba `kind` (`decide` / `codex` / `oracle`) ở [05 §3.4](../05-GIAO-THUC.md).

**Bất biến 1 — client chỉ gửi ý đồ.** Không vị trí, không máu, không sát thương, không điểm, không tick. Bảng đầy đủ ở [04 §2](../04-THE-GIOI-MO.md). Trường lạ trong payload → **bỏ im lặng**, đừng để nó chạm vào gì.
**Bất biến 2 — mọi payload qua `validate()` của [B-04](B-04-xac-thuc.md)**, kể cả khi client là chính bạn. Một đường vòng "tin client của mình" là một lỗ hổng chờ tới ngày mở cửa.
**Bất biến 3 — `accepted: false` là `200`, không phải lỗi HTTP.** Quyết định hợp lệ cú pháp nhưng vô nghĩa trong thế giới → ghi `LLM_SEMANTIC_FAIL`, con vật rơi về phản xạ, client không cần làm gì.
**Bất biến 4 — bất biến theo `work_id`.** Gửi lại cùng `work_id` → bỏ qua lần hai, không lỗi. Client được phép thử lại **đúng một lần**.
**Bất biến 5 — server đóng dấu thời gian.** `applied_at_tick` do server ghi. Đây là thứ khiến kênh điểm không giả mạo được ([04 §7.2](../04-THE-GIOI-MO.md)).

## 3. Nghiệm thu
```bash
pytest tests/test_decision.py -q
# ca cho MỖI mã lỗi ở 05 §3.5, cộng:
#   payload có thêm trường "x": 1, "pos": [3,3], "hp": 999 -> bị bỏ, không chạm trạng thái
#   gửi cùng work_id hai lần -> lần hai accepted true nhưng không áp dụng lần nữa
#   work_id của client khác -> 403
python scripts/hostile_client.py --server http://localhost:8000
# client thù địch: gửi pos/hp/score, tick giả, work_id người khác, body 1 MB, 500 req/s
# assert: trạng thái thế giới KHÔNG đổi vì bất kỳ cái nào trong số đó
```
> Viết `hostile_client.py` **trước** khi phơi server ra internet ([N-11](N-11-phoi-internet.md)), không phải sau.

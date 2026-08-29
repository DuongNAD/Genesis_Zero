# B-04 · Xác thực ngữ nghĩa

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-01 · **Chặn** B-05, N-07 |
| **File** | `genesis/validate.py` · ~90 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ danh sách quy tắc đã đầy đủ |
| **Tài liệu gốc** | v4 Bước 16, [05 §3.4](../05-GIAO-THUC.md) |

## 1. Mục tiêu
GBNF đảm bảo **cú pháp**, không đảm bảo **nghĩa**. Model 1.5B sẽ trả `target` trỏ vào con vật không tồn tại hoặc ngoài tầm nhìn. Tỉ lệ này chính là chỉ số so sánh chất lượng giữa các model ở Q1.

## 2. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Verdict: ok: bool; reason: str | None

def validate_decide(payload: dict, c: Creature, world, visible: list[Creature]) -> Verdict: ...
def validate_codex(payload: dict, c: Creature, sm: SurfaceMap, tick: int) -> Verdict: ...
```
Quy tắc, mã lỗi lấy nguyên từ [05 §3.4](../05-GIAO-THUC.md):

| Kiểm | Mã khi sai |
|---|---|
| `target` tồn tại | `SEMANTIC_TARGET_NOT_FOUND` |
| `target` đang nhìn thấy | `SEMANTIC_TARGET_NOT_VISIBLE` |
| `HUNT`/`FOLLOW` bắt buộc có target; `FORAGE` thì không | `SEMANTIC_GOAL_NEEDS_TARGET` |
| `ttl` ∈ [2,12] | `SEMANTIC_TTL_RANGE` |
| `goal` thuộc bộ cho phép của `brain` | `SEMANTIC_GOAL_NOT_ALLOWED_FOR_BRAIN` |
| `slot` < `codex_size` | `CODEX_BAD_SLOT` |
| bề mặt trong luật có tồn tại ván này | `CODEX_UNKNOWN_SURFACE` |
| `tick - last_claim >= CLAIM_COOLDOWN` | `CODEX_COOLDOWN` |

**Bất biến 1:** ghi `LLM_SEMANTIC_FAIL` **tách riêng khỏi** `LLM_MISS`. Trộn hai loại là mất chỉ số so sánh model.
**Bất biến 2:** sai → fallback về phản xạ, **không crash**, không thử lại.
**Bất biến 3:** validate chạy ở **server**, kể cả khi client là chính bạn ([04 §2](../04-THE-GIOI-MO.md)).

## 3. Nghiệm thu
```bash
pytest tests/test_validate.py -q    # một ca cho MỖI mã lỗi ở bảng trên, cả ca hợp lệ
```

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đọc trước: docs/tasks/B-04-xac-thuc.md §2 và docs/05-GIAO-THUC.md §3.4
(danh sách mã lỗi chính xác). Đừng đọc tài liệu khác.
VIỆC: genesis/validate.py với Verdict, validate_decide, validate_codex theo chữ ký §2.
Mỗi quy tắc trong bảng §2 là một nhánh, trả ĐÚNG mã lỗi ghi ở cột phải.
tests/test_validate.py: một ca cho MỖI mã lỗi, cộng một ca hợp lệ cho mỗi hàm.
RÀNG BUỘC: chỉ thư viện chuẩn; không tạo/sửa file khác; không except: pass;
hằng số (CLAIM_COOLDOWN, codex_size) lấy từ law_config, không viết số.
NGHIỆM THU: pytest tests/test_validate.py -q
TRẢ VỀ: chỉ diff.
```

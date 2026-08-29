# W-13 · Mở rộng sandbox cho v5

| | |
|---|---|
| **Track** | World (v5 L1) |
| **Phụ thuộc** | W-12 |
| **Chặn** | L-01, L-03, X-03 |
| **File** | `genesis/world.py`, `genesis/law_config.py` |
| **Ước lượng** | ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ cơ chế giao được; **hoán vị bề mặt thì tự** |
| **Tài liệu gốc** | [03 §11 L1](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Đủ chất liệu để luật ẩn có cái mà nói tới. Không có nước uống thì không có luật *"quả đỏ độc nếu ăn sau khi uống nước"*; không có ngày/đêm thì mọi điều kiện `PHASE` vô nghĩa.

## 2. Đầu vào đã có
M1 hoàn chỉnh. `law_config.py` chưa tồn tại — tạo ở việc này, nội dung ở [03 §12](../03-LUAT-AN-V5.md).

## 3. Việc phải làm
1. Hành động `DRINK` trên ô `WATER`. Ghi log `DRINK`.
2. Tách `PLANT` thành `FRUIT_A..D`. Dinh dưỡng nền **giống nhau** — khác biệt chỉ đến từ luật ẩn.
3. **Hoán vị bề mặt mỗi ván**: `(màu, hình)` gán ngẫu nhiên cho 4 lớp. Agent thấy bề mặt, engine biết lớp.
4. Chu kỳ ngày/đêm `PHASE_LEN = 40` tick, quan sát được.
5. Hướng gió cố định mỗi ván, quan sát được.
6. Địa hình `FIRE` + cơ chế lan (mặc định **tắt**, chỉ bật khi có luật `SPREAD`).

## 4. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class SurfaceMap:
    """Ánh xạ lớp <-> bề mặt, bốc thăm MỖI VÁN."""
    cls_to_surface: dict[str, tuple[str,str]]      # "FRUIT_A" -> ("đỏ","tròn")
    def surface_of(self, cls: str) -> str: ...     # -> "quả đỏ tròn"
    def class_of(self, surface: str) -> str | None: ...

def roll_surface_map(rng: random.Random) -> SurfaceMap: ...
def phase_at(tick: int) -> str: ...                # "DAY" | "NIGHT"
```
**Bất biến 1 — cái quan trọng nhất của việc này:** chuỗi `"FRUIT_A"` **không bao giờ** xuất hiện trong bất cứ thứ gì agent thấy. Prompt, sổ tay, log gửi cho client — chỉ có bề mặt. Rò một lần là hỏng cả phép đo prior ([03 §10.2](../03-LUAT-AN-V5.md)).
**Bất biến 2:** hoán vị bốc từ `rng` của ván, **độc lập** với việc bốc luật. Nếu hai thứ dùng chung một luồng số thì luật và bề mặt tương quan với nhau và bạn tạo ra một manh mối không cố ý.
**Bất biến 3:** dinh dưỡng nền của 4 loại quả **bằng nhau**. Khác nhau thì agent phân biệt được quả bằng cách khác luật ẩn, và bạn không biết nó học cái gì.

## 5. Bẫy
Đừng giảm `sight_radius` vào ban đêm. Nghe rất hợp lý và nó **phá Gate A** cho mọi luật có `PHASE(NIGHT)` — luật chỉ xảy ra đúng lúc bạn nhìn kém nhất thì không định danh được ([03 §11 L1](../03-LUAT-AN-V5.md)). Nếu rất muốn có, để sau khi Q1 xong và chạy lại baseline.

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 55 --ticks 400 --no-render --out /tmp/w13.jsonl
python - <<'PY'
import json, collections, subprocess
rows=[json.loads(l) for l in open('/tmp/w13.jsonl')]
k=collections.Counter(r["kind"] for r in rows)
assert k["DRINK"] > 0, k
ph=[r for r in rows if r["kind"]=="PHASE_CHANGE"]
assert len(ph)==10, len(ph)                       # 400/40
f=collections.Counter(r.get("fruit_surface") for r in rows if r["kind"]=="EAT")
assert len(f)==4 and max(f.values())/min(f.values()) < 1.4, f   # 4 loại, đều nhau ±40%
PY
# hoán vị bề mặt: hai seed khác nhau -> ánh xạ khác nhau
python -c "
import random; from genesis.world import roll_surface_map
a=roll_surface_map(random.Random(1)).cls_to_surface
b=roll_surface_map(random.Random(2)).cls_to_surface
assert a!=b, 'hoán vị không đổi giữa các ván'; print('HOÁN VỊ OK')"
# KHÔNG rò tên lớp ra ngoài
! grep -q 'FRUIT_[A-D]' /tmp/w13.jsonl && echo "KHÔNG RÒ LỚP OK"
```

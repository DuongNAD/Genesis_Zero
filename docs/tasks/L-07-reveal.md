# L-07 · REVEAL và diễn giải luật ra tiếng Việt

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-01, L-06 |
| **Chặn** | N-12 |
| **File** | `genesis/reveal.py` |
| **Ước lượng** | ~80 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ bảng tra cứng, test so chuỗi |
| **Tài liệu gốc** | [03 §1.2](../03-LUAT-AN-V5.md), [05 §3.6](../05-GIAO-THUC.md) |

## 1. Mục tiêu
Khoảnh khắc cuối ván: công bố luật thật, ai đoán đúng, ai bị lừa. Đây **không phải trang trí** — nó là (a) cao trào tự nhiên khiến ván thành tập phim ([04 §8](../04-THE-GIOI-MO.md)), và (b) nguồn dữ liệu SFT hậu nghiệm ([03 §11.6](../03-LUAT-AN-V5.md)).

## 2. Đầu vào đã có
`to_vietnamese` từ L-01, `match` từ L-06, `SurfaceMap` từ W-13.

## 3. Việc phải làm
1. `build_reveal(match_state) -> dict` theo đúng hình dạng ở [05 §3.6](../05-GIAO-THUC.md).
2. In bảng `rich` cho terminal: mỗi luật một dòng tiếng Việt + ai đoán đúng + ở tick nào.
3. Xuất JSON cho `/match/result` và cho `analyze.py`.

## 4. Chữ ký và bất biến
```python
def build_reveal(laws: list[Law], codices: dict[str, list[CodexEntry]],
                 sm: SurfaceMap, log_path: Path) -> dict: ...
def render_reveal(payload: dict) -> RenderableType: ...
```
**Bất biến 1:** đây là nơi **duy nhất** luật thật rời khỏi server. Trước pha `REVEAL`, không endpoint nào, không khung spectator nào chứa nó. Kiểm bằng test tự động ([05 §3.8](../05-GIAO-THUC.md)), không bằng kỷ luật.
**Bất biến 2:** diễn giải theo **bề mặt của ván đó**, không theo lớp. *"Ăn quả đỏ tròn…"*, không phải *"Ăn FRUIT_A…"*.

## 5. Bẫy
Cám dỗ sẽ là log luật thật ngay từ đầu ván "cho tiện debug". Nếu làm vậy thì log là kênh rò rỉ, và bất kỳ ai xem log giữa ván — kể cả một script phân tích chạy nhầm — đều thấy đáp án. Ghi luật thật vào **file riêng** `runs/<match>.truth.json` và chỉ nhập nó lúc chấm.

## 6. Nghiệm thu
```bash
python -m genesis.run --seed 88 --ticks 400 --no-render --out /tmp/r.jsonl --reveal /tmp/r.reveal.json
# 1. không rò trước REVEAL
! grep -q '"kind": *"LAW_TRUTH"' /tmp/r.jsonl && echo "KHÔNG RÒ OK"
python -c "
import json; d=json.load(open('/tmp/r.reveal.json'))
assert len(d['laws'])==3 and all(l['vi'] and 'FRUIT_' not in l['vi'] for l in d['laws'])
assert all('per_law' in s for s in d['scores']); print('REVEAL OK')"
# 2. đọc bằng mắt: câu tiếng Việt có tự nhiên không
python scripts/reveal_preview.py --n 20
```

## 7. Prompt giao việc
```
BỐI CẢNH
Python 3.11 + rich. Đọc trước: docs/05-GIAO-THUC.md §3.6 (hình dạng JSON chính xác) và
docs/03-LUAT-AN-V5.md §1.2. Đừng đọc tài liệu khác.
Đã có: genesis/lawdsl.py (to_vietnamese, Law), genesis/verify.py (match), SurfaceMap.

VIỆC
genesis/reveal.py:
1. build_reveal(laws, codices, sm, log_path) -> dict khớp CHÍNH XÁC hình dạng ở 05 §3.6
   (khoá laws / scores / citations / deception; mỗi law có law_id, tier, dsl, vi, fired_count).
2. render_reveal(payload) -> rich renderable: bảng mỗi luật một dòng, cột "ai đoán đúng"
   và "ở tick nào", sắp theo t_discover tăng dần.
3. scripts/reveal_preview.py --n N: sinh N bộ luật ngẫu nhiên và in câu tiếng Việt của chúng.
4. tests/test_reveal.py: khẳng định không chuỗi nào trong payload chứa "FRUIT_" (phải là
   bề mặt, không phải lớp); khẳng định mọi khoá bắt buộc ở 05 §3.6 đều có mặt.

RÀNG BUỘC
- Không thêm phụ thuộc ngoài rich.
- KHÔNG import genesis/world.py.
- Không tạo file khác. Không sửa file khác trong genesis/.

NGHIỆM THU: pytest tests/test_reveal.py -q && python scripts/reveal_preview.py --n 5

TRẢ VỀ: chỉ diff.
```

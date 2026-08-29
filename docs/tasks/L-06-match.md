# L-06 · `match()` — chấm bằng bảng chân trị  ★★

| | |
|---|---|
| **Track** | Law |
| **Phụ thuộc** | L-04 |
| **Chặn** | B-10, X-02 |
| **File** | `genesis/verify.py` |
| **Ước lượng** | ~90 dòng · 3 giờ (phần lớn là test) |
| **Giao cho model rẻ?** | ❌ **tuyệt đối không** — hàm quan trọng nhất dự án |
| **Tài liệu gốc** | [03 §5.1 §5.3](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Hàm quyết định mọi kết luận của dự án. Sai một cách tinh vi thì nó cho ra **số đẹp** và mọi thứ phía sau sai mà không ai biết. Đây là lý do nó không được giao cho ai và không được viết vội.

## 2. Đầu vào đã có
`sample_situations` từ L-04, `evaluate` từ L-02.

## 3. Việc phải làm
1. So hai luật bằng **kết quả trên tập tình huống**, không bằng cú pháp.
2. So effect ở mức **rổ**; rổ liền kề = 0.5 điểm cho tình huống đó; cách hai rổ = 0.
3. Chuẩn hoá theo null.

## 4. Chữ ký và bất biến
```python
def match(claimed: Law, truth: Law, situations: list[Situation]) -> float:
    """
    acc   = trung bình agree(claimed(s), truth(s))
    acc0  = trung bình agree(None,        truth(s))
    return clip((acc - acc0) / (1 - acc0), 0, 1)
    """

def agree(a: Effect | None, b: Effect | None) -> float:
    """1.0 giống rổ · 0.5 cùng kind, lệch ĐÚNG một rổ · 0.0 còn lại.
       None vs None = 1.0. None vs có = 0.0."""
```
**Bất biến 1:** chuẩn hoá theo null là **bắt buộc**. Không có nó, một agent ghi luật kích hoạt cực hiếm ăn 0.9 điểm vì "hầu như luôn đúng rằng chẳng có gì xảy ra".
**Bất biến 2:** `verify.py` **không import** `world.py`. Nó nhận `Law` và `Situation`, trả số. Ranh giới này đảm bảo sim không bao giờ chạm được vào bảng chấm ([03 §5.6](../03-LUAT-AN-V5.md) dòng "dò verifier").
**Bất biến 3:** hàm thuần, tất định. Cùng đầu vào → cùng số, mọi lần chạy, mọi máy.

## 5. Bẫy
Rổ liền kề: `MED` liền kề `SMALL` và `BIG`; `SMALL` **không** liền kề `BIG`. Viết bảng liền kề tường minh, đừng tính bằng chỉ số enum — thêm một rổ sau này là bạn có một bug im lặng.

## 6. Nghiệm thu — tám ca, không được bỏ ca nào
```bash
pytest tests/test_match.py -q -v
```
```python
# tests/test_match.py — tám ca BẮT BUỘC
# (a) trùng khít                        -> match == 1.0
# (b) khác cú pháp, cùng hành vi         -> match == 1.0     ★ hỏng = chấm oan người đúng
# (c) đúng trigger, sai cond             -> 0.4 <= m <= 0.6
# (d) đúng trigger+cond, sai effect      -> m <= 0.3
# (e) null (không luật)                  -> m == 0.0
# (f) 1000 luật ngẫu nhiên               -> trung bình <= 0.15  ★ hỏng = đoán bừa có điểm
# (g) đúng hết, lệch MỘT rổ độ lớn       -> 0.80 <= m <= 0.90
# (h) đúng effect, sai hoàn toàn trigger -> m <= 0.2
```

> **Không đi tiếp khi ca (b) hoặc ca (f) chưa đạt.**
> (b) hỏng → bạn chấm oan người đúng, và mọi so sánh giữa các model thành nhiễu.
> (f) hỏng → đoán bừa có điểm, và toàn bộ RL ở track R sẽ đi tối ưu vào đúng chỗ đó.
>
> Hai ca này là hai đầu kẹp lấy thang đo. Không có chúng thì bạn không biết thước của mình dài bao nhiêu.

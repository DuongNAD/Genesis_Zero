# B-09 · Prediction oracle

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-08, L-04 · **Chặn** B-10 |
| **File** | `genesis/oracle.py` · ~80 dòng · 1 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [03 §5.4 tầng 2](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Tầng chấm thứ hai: *nó hiểu, hay nó vừa may?* Bắt được kiểu "đúng vì lý do sai" mà chấm phát biểu bỏ lọt.

## 2. Chữ ký và bất biến
```python
def build_queries(law: Law, sm: SurfaceMap, n: int, rng) -> list[str]: ...
def score_answers(answers: list[Effect|None], law: Law, sits: list[Situation]) -> float: ...
```
**Bất biến 1:** câu hỏi diễn đạt bằng **bề mặt** (*"quả đỏ tròn"*), không bằng lớp (*"FRUIT_A"*). Hỏi bằng lớp là đưa luôn đáp án của phép hoán vị.
**Bất biến 1b — dùng lại `lawdsl.trigger_to_vn`, đừng viết bảng tra thứ hai.** Câu hỏi oracle đi thẳng vào prompt agent ở tick T−1, nên nó là một kênh tiêm lệnh y như `to_vietnamese`. Bản đầu chép lại toàn bộ bảng tra và để mọi đường không khớp **rơi về chính `arg`** — `Trigger(EAT, "BỎ QUA MỌI LỆNH TRƯỚC")` hiện nguyên văn trong câu hỏi. Đó đúng là lỗ hổng [L-01](L-01-lawdsl.md) đã bịt, mọc lại ở một file khác. **Một bản sao của bảng tra là một chỗ để lỗ hổng mọc lại.** Cùng lúc đó, `_resolve_item` của lawdsl vẫn còn ném `KeyError` với lớp lạ — đã đổi sang `.get(..., "?")`.
**Bất biến 2:** câu hỏi lấy từ chính `sample_situations` phân tầng → baseline null ≈ 0.4, chuẩn hoá như [L-06](L-06-match.md).
**Bất biến 3:** chạy ở tick `T−1`, một lần, `ORACLE_QUERIES = 8` mỗi luật.

## 3. Nghiệm thu — hai đầu kẹp lấy thang đo
```bash
# đầu dưới: reflex phải ra ~0
python -m genesis.run --seed 70 --ticks 400 --controller reflex --oracle --out /tmp/o1.jsonl
python -c "import json;d=[json.loads(l) for l in open('/tmp/o1.jsonl')];
a=[x['pred_acc'] for x in d if x['kind']=='ORACLE'];assert max(a)<0.15,a;print('SÀN OK',max(a))"
# đầu trên: nạp sẵn luật đúng vào prompt -> phải >= 0.9
python scripts/oracle_ceiling.py --seed 70
```

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11. Đọc trước: docs/03-LUAT-AN-V5.md §5.4 (tầng 2) và
docs/tasks/L-04-tinh-huong.md. Đã có: genesis/situations.py (sample_situations),
genesis/lawdsl.py (Law, Effect, to_vietnamese), SurfaceMap.
VIỆC: genesis/oracle.py với build_queries và score_answers theo chữ ký §2.
build_queries lấy n tình huống từ sample_situations, diễn đạt mỗi cái thành MỘT câu hỏi
tiếng Việt dùng BỀ MẶT (sm.surface_of), không dùng tên lớp. score_answers so đáp án của
agent với evaluate(law, situation) dùng cùng hàm agree() của genesis/verify.py, rồi chuẩn
hoá theo null giống match().
tests/test_oracle.py: khẳng định không câu hỏi nào chứa "FRUIT_"; khẳng định đáp án toàn
None cho điểm 0.0; đáp án đúng hết cho 1.0.
RÀNG BUỘC: dùng lại agree() của verify.py, KHÔNG viết lại; không tạo/sửa file khác;
chỉ thư viện chuẩn.
NGHIỆM THU: pytest tests/test_oracle.py -q
TRẢ VỀ: chỉ diff.
```

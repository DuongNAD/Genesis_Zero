# W-14 · Điều kiện chiến thắng — ba danh hiệu

| | |
|---|---|
| **Track** | World · **Phụ thuộc** B-10 · **Chặn** — |
| **File** | `genesis/victory.py` · ~130 dòng · 2 giờ |
| **Giao cho model rẻ?** | ❌ đây là chỗ dễ kéo dự án về đúng bệnh của v4 |
| **Tài liệu gốc** | [03 §0.1 §5.5 §9](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Một ván phải **kết thúc bằng một câu chuyện**, không chỉ bằng một file CSV.

## 2. Vì sao ba danh hiệu chứ không một
Bản v5 cố ý bỏ "sống lâu" làm mục tiêu duy nhất ([03 §0.1](../03-LUAT-AN-V5.md)):
sinh tồn không có đáp án → không chấm được → không train được. Nhưng bỏ hẳn nó thì
mất phần **vui** — người xem cần một câu chuyện, và *"con nào sống tới cuối"* là
câu chuyện dễ kể nhất trên đời.

Nên: **ba bảng riêng, không cộng vào nhau.**

| Danh hiệu | Thắng bằng | Vì sao có mặt |
|---|---|---|
| `NHA_KHOA_HOC` | `R` cao nhất theo [03 §5.5](../03-LUAT-AN-V5.md) | thứ dự án **đo**, và thứ RL học |
| `KE_SONG_SOT` | tỉ lệ tick còn sống cao nhất | phần vui, phần kể chuyện |
| `NGUOI_DAU_TIEN` | ghi được luật đạt `match ≥ θ` **sớm nhất** và giữ tới cuối | khoảnh khắc kịch tính nhất của một ván |

**Bất biến 1 — không cộng thành một điểm tổng.** Một trọng số duy nhất giữa
"hiểu" và "sống" là một tuyên bố về việc cái nào quan trọng hơn, và **ta không
biết** — đó chính là câu hỏi Q7 mà [X-02](../03-LUAT-AN-V5.md) sinh ra để trả
lời. Để ba bảng riêng thì **khoảng cách giữa chúng là dữ liệu**: một loài đứng
đầu bảng khoa học mà cuối bảng sinh tồn nói lên nhiều hơn bất kỳ điểm tổng nào.

**Bất biến 2 — `NGUOI_DAU_TIEN` chỉ tính ca THẬT SỰ tìm ra.** Cột `t_discover`
toàn `T+1` sắp tăng dần sẽ đẻ ra một "người thắng" chưa hề tìm ra gì.

**Bất biến 3 — nói thẳng khi không ai tìm ra.** Lúc ấy `R = 0.1·R_survive` cho
tất cả và bảng "Nhà khoa học" **chỉ là bảng sinh tồn thu nhỏ**. `render()` in một
dòng cảnh báo; không có nó thì sẽ có người đọc thứ hạng đó như một kết luận về
năng lực quy nạp.

**Bất biến 4 — không import vòng chạy**, cùng ranh giới với [B-10](B-10-score.md).

## 3. Nghiệm thu
```bash
pytest tests/test_victory.py -q
python -c "
from pathlib import Path
from genesis.victory import from_files
print(from_files(Path('runs/real-9.jsonl'), Path('runs/real-9.truth.json')).render())"
curl -s localhost:8000/v1/match/result | jq -e '.victory.boards.NHA_KHOA_HOC[0].rank == 1'
```

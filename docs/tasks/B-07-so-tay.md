# B-07 · Sổ tay sự kiện  ★

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-02, L-02 · **Chặn** B-08 |
| **File** | `genesis/fieldnotes.py` · ~130 dòng · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ vòng đệm giao được; **quy tắc chọn khi tràn và kiểm rò rỉ tự làm** |
| **Tài liệu gốc** | [03 §7.1 §7.2](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
**Không có ký ức sự kiện thì không có quy nạp.** Đây là bổ sung bắt buộc, không phải tuỳ chọn — và nếu mốc "ĐO ĐƯỢC" thất bại thì đây là chỗ đầu tiên phải xem.

## 2. Chữ ký và bất biến
```python
@dataclass(frozen=True)
class Note:
    t: int; who: str            # "TÔI" | "THẤY <id>"
    action: str; outcome: str   # định tính, KHÔNG phải tên effect nội bộ
    ctx: dict                   # pha, địa hình, hành động gần đây — LUÔN đầy đủ

class FieldNotes:
    def record(self, n: Note) -> None: ...
    def render(self, k: int) -> str: ...   # k = events_in_prompt theo brain
```
Định dạng bốn cột, [03 §7.1](../03-LUAT-AN-V5.md):
```
t382 TÔI ăn quả đỏ tròn        → mất máu nhiều, kéo dài   [đêm, vừa uống nước t379]
t361 THẤY L5#2 ăn quả đỏ tròn  → nó mất máu               [đêm]
t340 TÔI ăn quả đỏ tròn        → không thấy gì            [ngày]
```
**Bất biến 1 — chọn khi tràn:** ưu tiên (1) kết quả bất thường, (2) sự kiện của chính mình, (3) mới nhất. **Đừng chỉ lấy N cái gần nhất** — 20 dòng "đi bộ, không có gì" sẽ đẩy hết bằng chứng ra khỏi context và bạn sẽ không hiểu vì sao model to cũng không tìm ra luật.
**Bất biến 1b — ngữ cảnh phải phủ ĐÚNG không gian giả thuyết.** Các chiều trong `ctx` phải khớp một-một với `CondKind` mà từ vựng của con đó cho phép. Thiếu chiều nào thì mọi luật dùng chiều ấy là câu đố không có lời giải — và nó **thất bại trong im lặng**: sổ tay trông vẫn đầy, model vẫn trả lời, điểm vẫn ra 0, và người ta đi đổi model.
> Đã xảy ra thật. Bản đầu ghi ba chiều — pha, địa hình, hướng gió tuyệt đối. Seed 9 có luật `KHI năng lượng dưới 25% THÌ chịu sát thương`, mà sổ không có lấy một chữ về năng lượng: "máu tụt hẳn xuống" hiện ra như chuyện ngẫu nhiên. Đọc bằng mắt (bài kiểm thứ tư bên dưới) thì **tôi cũng không suy ra nổi** — đó chính là lúc bài kiểm ấy trả công.

**Bất biến 1c — chừa chỗ cho đối chứng.** Ưu tiên "bất thường trước" có mặt trái mà bản đầu của phiếu này chưa nói: khi luật kích hoạt liên tục thì **mọi** dòng đều bất thường và các dòng `không thấy gì` bị đẩy ra hết. Đo thật (seed 7, 200 tick): 20/20 dòng là `uống nước → nhiễm độc`, và từ một danh sách chỉ có ví dụ dương thì không tài nào phân biệt `uống nước thì độc` với `uống nước BAN ĐÊM thì độc` — đúng thứ mà cond của luật hỏi. `FieldNotes.NORMAL_QUOTA_RATIO = 0.25` giữ một phần tư chỗ, ở cả lúc loại bớt lẫn lúc `render`.

**Bất biến 2 — ngữ cảnh luôn có mặt:** ghi `[đêm]` lúc tối và **`[ngày]` lúc sáng**, đừng để trống. Để trống thì model học "có ngoặc = có chuyện" — một tương quan giả **do bạn tự tạo ra ở tầng định dạng**.
**Bất biến 3 — không rò nội tâm kẻ khác:** thấy con khác ăn quả thì thấy; `→ nó mất máu` được, `→ nó bị nhiễm độc 5 tick` là **rò đáp án**.
**Bất biến 4:** sự kiện `THẤY` chỉ vào sổ khi nằm trong `sight_radius` của **người quan sát**.

## 3. Nghiệm thu
```bash
python scripts/dump_prompt.py --seed 9 --creature L1:0 --tick 250 > /tmp/n.txt
# `dump_prompt` chạy MỘT VÁN THẬT có luật ẩn và có `LlmStrategist`; không thế thì
# sổ tay rỗng và bài kiểm quan trọng nhất bên dưới không kiểm được gì.
sed -n '/^\[USER/,$p' /tmp/n.txt > /tmp/u.txt
! grep -qE 'POISON|STUN|BLIND|law_id|FRUIT_[A-D]' /tmp/u.txt && echo "KHÔNG RÒ OK"
grep -c 'pha ngày' /tmp/u.txt && grep -c 'pha đêm' /tmp/u.txt   # cả hai đều > 0
pytest tests/test_fieldnotes.py -q -k "overflow_priority"
```
**Và bài kiểm tra thứ tư, quan trọng nhất và không tự động hoá được:**

> Đọc sổ tay ở `/tmp/n.txt` bằng mắt. **Bạn** có suy ra được luật không?
> Nếu bạn không suy ra được thì model cũng không, và lỗi nằm ở đây — không ở model.

# B-02 · Prompt 5 khối, giữ prefix cache

| | |
|---|---|
| **Track** | Brain · **Phụ thuộc** B-01, L-01 · **Chặn** B-05, B-07 |
| **File** | `genesis/prompt.py` · ~180 dòng · 3 giờ |
| **Giao cho model rẻ?** | ⚠️ ghép chuỗi giao được; **nội dung khối A2 tự viết từng câu** |
| **Tài liệu gốc** | v4 Bước 14, [03 §8 §7.4](../03-LUAT-AN-V5.md) |

## 1. Mục tiêu
Nói luật nền, giấu luật ẩn, giấu đối thủ. Đây là chỗ v5 đảo ngược v4 một cách có kiểm soát ([03 §0.4](../03-LUAT-AN-V5.md)) — sai ở đây thì hoặc agent không biết mình phải đi tìm gì, hoặc bạn mớm luôn đáp án.

## 2. Việc phải làm
1. Năm khối theo [03 §8](../03-LUAT-AN-V5.md). 2. Khối D cắt theo brain. 3. Kiểm bất biến prefix bằng test tự động.

## 3. Chữ ký và bất biến
```python
def system_block(c: Creature, persona: str, sm: SurfaceMap) -> str:   # A + A2 + B + D
def user_block(c: Creature, world, tick_no: int, notes: FieldNotes | None,
               codex: Codex | None, heard=(), notepad="", seen=()) -> str:   # E
class PromptCache:          # giữ SYSTEM theo creature_id, phát PREFIX_INVALIDATED
```
**Khối C không còn ở SYSTEM.** Nó đi xuống khối E cùng với mọi số đo cơ thể, kể cả `brain` — xem §4, đó là kết quả của việc chạy chính lệnh nghiệm thu §5.
**Bất biến 1:** `system_block` **giống nhau từng byte** giữa mọi lần gọi của cùng một cá thể trong một ván. Đây là điều kiện để prefix KV cache hoạt động — trên máy chậm nó là khác biệt giữa 3 giây và 12 giây.
**Bất biến 2:** mọi thứ biến động nằm ở **cuối**, trong `user_block`.
**Bất biến 3:** khối A nói **cơ chế nền định tính**, không bao giờ nói công thức số. Nói `damage = 4 + 3*attack` thì model làm toán thay vì hành xử như con vật.
**Bất biến 4:** khối A2 phải có câu *"Bề ngoài của sự vật ở thế giới này không nói lên bản chất"* — chép nguyên văn từ [03 §8](../03-LUAT-AN-V5.md). Thiếu câu này thì bạn đo model nào cứng đầu hơn, không phải model nào quy nạp giỏi hơn.
**Bất biến 5:** không bao giờ xuất hiện tên **lớp** (`FRUIT_A`) ở bất kỳ khối nào — chỉ **bề mặt**. Canh bằng `_check_no_leak`, và nó **ném `PromptLeak`**, không sửa chuỗi. Một bộ lọc `re.sub` trông thì an toàn nhưng nó biến mọi test rò rỉ thành test rỗng — test không bao giờ đỏ được nữa, dù đường rò có thật. Rò rỉ phải làm gãy ván.
**Bất biến 5b — ném cho lỗi của MÌNH, vô hiệu hoá cho chữ của NGƯỜI KHÁC.** `_check_no_leak` ném, và đúng như thế với phần server tự dựng (bề mặt, sổ tay, Sổ Luật): ở đó rò rỉ là lỗi của ta và phải làm gãy ván để ta thấy. Nhưng `heard`, `notepad` và `persona` là chữ **người khác viết**, và ném ở đó nghĩa là bất cứ ai cũng đánh sập được ván của ta bằng một chuỗi. Lỗ này xuất hiện **ba lần ở ba đường** trước khi lộ ra là một chỗ hở của thiết kế chứ không phải ba lỗi rời: lời nói ([B-11](B-11-noi-danh-tieng.md)), ghi chú riêng do chính model viết, và persona của client. Ca ghi chú là tệ nhất — model viết chữ `"HP"` vào `note` và ván **tự chết** ở lượt 87, không cần kẻ thù nào. `user_block` giờ tự làm sạch `heard`/`notepad`; `/join` từ chối persona bẩn tại cửa với `422`.

**Bất biến 6:** tên enum DSL (`POISON`, `PHASE`…) hợp lệ ở **khối D** — đó là từ vựng agent phải dùng để phát biểu luật — và bị cấm ở mọi khối kể chuyện, nơi chúng là đáp án. `persona` do chủ client viết cũng bị soi như mọi khối khác: ở chế độ mở nó đến từ máy lạ.

## 4. Bẫy
`brain` dịch được giữa ván ([B-13](B-13-dich-trait-llm.md)) → khối D đổi → cache vỡ. Chấp nhận được, nhưng **phải log `PREFIX_INVALIDATED`**. Nhiều hơn ~5 lần/ván thì tần suất dịch trait đang ăn hết throughput.

**Đã đo, và bẫy nằm chỗ khác với chỗ đoạn trên đoán.** Bản đầu in cả sáu trait ở khối C, prefix vỡ **79–91 lần/ván** (5 seed × 400 tick × 15 con) — 5,3 lần mỗi con, đúng ngưỡng. Thủ phạm không phải [W-11](W-11-vong-tick.md) dịch trait mà là `reset_body`: chết thì cơ thể về founder, `brain` đổi, prefix vỡ; và một con chết ~4 lần một ván. Thêm nữa, `brain` dao động chủ yếu trong **4↔5** và **3↔4** — những cặp `vocab_for_brain` trả về **cùng một từ vựng**, nên khối D không đổi một byte và prompt lẽ ra không việc gì phải vỡ. Bỏ hết số đo cơ thể khỏi SYSTEM: còn **19–34 lần/ván**, tức 1,27–2,27 mỗi con. Bài học chung: SYSTEM chỉ được chứa thứ **thật sự** quyết định nội dung của nó.

## 5. Nghiệm thu
```bash
python scripts/dump_prompt.py --seed 3 --creature L1:0 --tick 100 > /tmp/p1.txt
python scripts/dump_prompt.py --seed 3 --creature L1:0 --tick 104 > /tmp/p2.txt
diff <(sed -n '/^\[SYSTEM/,/^\[USER/p' /tmp/p1.txt) <(sed -n '/^\[SYSTEM/,/^\[USER/p' /tmp/p2.txt) \
  && echo "PREFIX BẤT BIẾN OK"
! grep -qE 'FRUIT_[A-D]|law_id' /tmp/p1.txt && echo "KHÔNG RÒ OK"
# KHÔNG grep POISON: nó là tên hệ quả trong từ vựng khối D, agent phải thấy để
# phát biểu được luật. Bất biến 6 chặn nó ở các khối kể chuyện, không ở khối D.
grep -q 'không nói lên bản chất' /tmp/p1.txt && echo "KHỐI A2 OK"
python scripts/dump_prompt.py --seed 3 --creature L1:0 --tick 100 --tokens
# đo được: SYSTEM ~596 token, USER ~124. Con số ~1550 ghi ở bản v4 là của prompt
# kể-hết-bằng-văn-xuôi; bản v5 nói ngắn hơn vì luật ẩn phải để agent tự tìm.
pytest tests/test_prompt.py -q
```

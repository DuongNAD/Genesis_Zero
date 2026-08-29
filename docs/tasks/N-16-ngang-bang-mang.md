# N-16 · Ngang bằng giữa ván cục bộ và chế độ mở

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-06, N-07 · **Trạng thái** 🟨 vá 3/5 |
| **Giao cho model rẻ?** | ❌ tự viết — đây là chỗ hai đường dễ lệch nhất |

## 1. Vấn đề

Ván cục bộ chạy qua `LlmStrategist`; chế độ mở chạy qua `RemoteClientStrategist`
+ `routes_work`. **Hai đường, và đường mạng liên tục thiếu thứ đường cục bộ có.**

Đếm bằng cách so hai file:

| tính năng | cục bộ | mạng (trước) | |
|---|---|---|---|
| sổ tay, Sổ Luật, notepad, `want_codex` | ✅ | ✅ | |
| **nghe được** (B-11) | ✅ | ❌ `heard=()` cứng | **đã vá** |
| **`prompt_hash`** | ✅ | ❌ không ghi | **đã vá** |
| **quên khi chết** (W-17) | ✅ | ❌ | **đã vá** |
| **dạy nhau + sổ ghi công** (B-12) | ✅ | ❌ | còn thiếu |
| **dịch trait** (B-13) | ✅ | ❌ | còn thiếu |
| **cẩm nang** (W-16) | ✅ | ❌ | còn thiếu |

## 2. Vì sao hai cái đã vá là quan trọng nhất

**`heard=()`** nghĩa là người chơi qua mạng **không bao giờ nghe thấy ai**. Cả
tầng xã hội không tồn tại ở chế độ mở — mà chế độ mở chính là nơi câu hỏi **Q2
của dự án ("giao tiếp đáng giá bao nhiêu?")** phải được đo, và bản đồ
`RUNG_RAM` được thiết kế riêng để hỏi nó. Chạy Q2 trên ván mở sẽ luôn ra "giao
tiếp đáng giá 0", và câu trả lời ấy là một hiện vật của lỗi.

**`prompt_hash` không được ghi** nghĩa là `rollout.samples_from` **bỏ sạch mọi
mẫu** từ log ván mở — nó đối chiếu băm và bỏ cái không khớp. Ván mở là nơi dữ
liệu thật sẽ đến từ đó; thiếu một trường bốn mươi ký tự làm toàn bộ dữ liệu quý
nhất của dự án không huấn luyện được.

Cả hai **không bao giờ hiện ra ở ván cục bộ**. Chúng chỉ tồn tại đúng ở chế độ
mà không ai chạy cho tới lúc mời người khác vào.

## 3. Ba cái còn thiếu

Lớn hơn, và cần trạng thái sống lâu hơn một tick (sổ ghi công, danh tiếng,
điểm thích nghi). Chúng cần một chỗ chứa theo `(match_id, creature_id)` giống
`_notes`/`_codices`, cộng một móc trong `MatchRunner.step`.

**Đừng vá từng cái một.** Đây là lần thứ tư cùng một họ trong dự án, và mẫu đã
rõ: cách sửa đúng là **gom logic về một chỗ mà cả hai đường gọi vào**
(`lineage.forget_on_death` là ví dụ), không phải đồng bộ hai bản.

Việc thật ở đây là rút phần "trí nhớ và xã hội" khỏi `LlmStrategist` thành một
đối tượng riêng, rồi cho cả hai đường dùng chung. Đó là một thay đổi đáng kể và
**không nên làm chung với việc khác** — nó đụng mọi thứ chạm tới prompt.

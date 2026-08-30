# N-16 · Ngang bằng giữa ván cục bộ và chế độ mở

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-06, N-07 · **Trạng thái** ✅ |
| **Giao cho model rẻ?** | ❌ tự viết — đây là chỗ hai đường dễ lệch nhất |

## 1. Vấn đề

Ván cục bộ chạy qua `LlmStrategist`; chế độ mở chạy qua `RemoteClientStrategist`
+ `routes_work`. **Hai đường, và đường mạng liên tục thiếu thứ đường cục bộ có.**

Đếm bằng cách so hai file:

| tính năng | cục bộ | mạng (trước) | |
|---|---|---|---|
| sổ tay, Sổ Luật, notepad, `want_codex` | ✅ | ✅ | |
| **nghe được** (B-11) | ✅ | ❌ `heard=()` cứng | vá lẻ |
| **`prompt_hash`** | ✅ | ❌ không ghi | vá lẻ |
| **quên khi chết** (W-17) | ✅ | ❌ | vá lẻ |
| **dạy nhau + sổ ghi công** (B-12) | ✅ | ❌ | **gom** |
| **dịch trait** (B-13) | ✅ | ❌ | **gom** |
| **cẩm nang** (W-16) | ✅ | ❌ | **gom** |

Ba cái tìm thêm được **trong lúc gom**, không cái nào nằm trong bảng đếm ban đầu
— và đó là lập luận mạnh nhất cho việc gom thay vì vá lẻ, vì đếm bằng mắt chỉ
tìm ra thứ mình nghĩ đến để đi tìm:

| tính năng | cục bộ | mạng (trước) | |
|---|---|---|---|
| **nói được** (B-11) | ✅ | ❌ `say` có trong schema, `/decision` không đọc | **gom** |
| **sanitize ghi chú** | ✅ | ❌ `.strip()[:N]` | **gom** |
| **headroom token cho `codex`** | ✅ | ❌ chạm trần, đứt giữa `effect` | **gom** |

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

## 4. Đã làm thế nào

`genesis.minds.Minds` giữ toàn bộ trạng thái đó, **một bản**. `MatchRunner` sở
hữu một `Minds` và `net.routes_work` chỉ tra cứu vào `state.runner.minds` —
năm dict cấp module khoá theo `(match_id, creature_id)` biến mất, cùng với chúng
là chỗ để bản thứ hai mọc lại.

| trước | sau |
|---|---|
| `routes_work._notes/._codices/._notepads/._want_codex/._heard` | `state.runner.minds` |
| `MatchRunner._absorb_speech_for_clients` tự render chuỗi | `Minds.absorb_speech` (kèm `teach` + `Ledger`) |
| `MatchRunner._forget_for_dead` tra hai dict | `Minds.on_death` |
| `max_tokens` chép tay | `strategist._budget` |
| khoá ghép `match_id` | `Minds.new_match()` ở ranh giới ván |

`Minds.new_match()` là chỗ **duy nhất** phân biệt hai tầng trí nhớ của W-16: xoá
sổ tay / Sổ Luật / danh tiếng, **giữ** cẩm nang.

`RemoteClientStrategist` nhận đủ ba móc mà `genesis.tick` hỏi bằng `getattr`:
`take_says`, `take_shift`, `slots`. Thiếu chúng thì đường mạng không báo lỗi
gì cả — nó chỉ **im lặng chơi một trò khác**.

## 5. Nghiệm thu
```bash
pytest tests/test_n16_ngang_bang.py -q
```
Mười ca, mỗi ca đỏ trước thay đổi này. Ca cuối
(`test_routes_work_khong_giu_ban_sao_tri_nho`) không kiểm chức năng nào — nó
canh chừng: đỏ ngay lúc ai đó dựng lại cuốn sổ thứ hai ở `routes_work`, thay vì
sáu tháng sau khi có người ngồi so hai file.

## 6. Còn lại, và nói thẳng

Cẩm nang ở chế độ mở **đọc và dùng** được, nhưng chưa ai **viết** vào nó sau
`REVEAL` — đường cục bộ cũng thế (chỉ `scripts/x08_handbook.py` nhét
`SEED_LESSONS` vào để đo). Đó là một việc riêng của W-16, không phải một khoảng
lệch giữa hai đường, nên nó không nằm trong phiếu này.

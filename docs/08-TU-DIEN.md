# 08 · Từ điển

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · **08 Từ điển**

> Mỗi thuật ngữ **một** nghĩa, dùng chung ở mọi tài liệu và mọi tên biến.
> Thấy chỗ nào dùng lệch nghĩa thì đó là lỗi, sửa chỗ đó chứ đừng thêm nghĩa mới vào đây.

## Thế giới

| Thuật ngữ | Nghĩa | Tên trong code |
|---|---|---|
| **tick** | Một bước thời gian của sim. Mọi thứ xảy ra đồng thời trong một tick. | `tick_no` |
| **ván** (match) | Một lần chạy trọn vẹn: sinh thế giới → T tick → REVEAL. Luật ẩn cố định trong ván, đổi giữa các ván. | `match_id` |
| **cá thể** | Một sinh vật. Có id ổn định suốt ván, kể cả khi chết. | `Creature` |
| **loài** (species) | Một nhóm cá thể dùng chung weights model và founder vector. | `species_id` |
| **founder vector** | Vector 6 trait khởi điểm của loài. Tổng luôn = 12. | `FOUNDERS` |
| **trait** | Một trong 6 chiều cơ thể: `brain attack armor speed sense stomach`. | `Traits` |
| **hoang dã** (feral) | Cá thể mà client của nó mất kết nối; rơi về tầng phản xạ của server. | `is_feral` |

## Hai tầng điều khiển

| Thuật ngữ | Nghĩa |
|---|---|
| **tầng phản xạ** | If-else chạy **mỗi tick**, biến goal thành nước đi. Ở server. Không bao giờ tắt. |
| **tầng chiến lược** | LLM chạy **mỗi `think_interval` tick**, trả về một **goal**, không trả nước đi. |
| **goal** | Ý đồ có thời hạn: `FORAGE HUNT FLEE FOLLOW REST WANDER GUARD` + `target` + `ttl`. |
| **intent** | Nước đi cụ thể một tick, do tầng phản xạ sinh. Thu hết rồi mới áp dụng. |

> Lẫn **goal** với **intent** là hiểu sai kiến trúc. Nếu bạn thấy mình gọi LLM mỗi tick thì đã lẫn.

## Luật ẩn

| Thuật ngữ | Nghĩa | Ở đâu |
|---|---|---|
| **luật nền** | Vật lý bất biến mọi ván: năng lượng, sát thương, tầm nhìn, chết. **Nói cho agent biết.** | [03 §0.4](03-LUAT-AN-V5.md) |
| **luật ẩn** | 2–3 quan hệ nhân quả bốc thăm mỗi ván. **Giấu tuyệt đối.** | [03 §2](03-LUAT-AN-V5.md) |
| **LawDSL** | Ký pháp hình thức của luật: `WHEN <trigger> [AND <cond>]{0,2} THEN <effect>` | [03 §2.2](03-LUAT-AN-V5.md) |
| **trigger / cond / effect** | Ba thành phần của một luật. | [03 §2.3](03-LUAT-AN-V5.md) |
| **bề mặt** (surface) | Cái agent **thấy**: "quả đỏ tròn". Bốc thăm lại mỗi ván. | [03 §2.6](03-LUAT-AN-V5.md) |
| **lớp** (class) | Cái engine **biết**: `FRUIT_A`. Agent không bao giờ thấy chuỗi này. | |
| **Sổ Luật** (codex) | Danh sách có số ô cố định chứa luật mà cá thể **tin**. Là thứ được chấm. | [03 §4.1](03-LUAT-AN-V5.md) |
| **sổ tay** (field notes) | Vòng đệm sự kiện đã trải qua/chứng kiến, server dựng, đưa vào prompt. | [03 §7.1](03-LUAT-AN-V5.md) |
| **notepad** | 200 ký tự tự do agent tự viết, chứa giả thuyết dở dang. | [03 §7.3](03-LUAT-AN-V5.md) |
| **REVEAL** | Công bố luật thật sau khi ván kết thúc. | [03 §1.2](03-LUAT-AN-V5.md) |

## Chấm điểm

| Thuật ngữ | Nghĩa |
|---|---|
| **verifier** | Bộ chấm. Chạy **offline sau ván**, đọc JSONL, không import gì từ vòng tick. |
| **tình huống** (situation) | Một bộ (sự kiện + đủ ngữ cảnh) để đánh giá được bất kỳ luật nào. |
| **bảng chân trị** | Cách chấm: hai luật bằng nhau khi cho cùng kết quả trên cùng tập tình huống. |
| **gần trượt** (near miss) | Tình huống trigger đúng nhưng cond sai. 40% mẫu. Tầng quan trọng nhất. |
| **null** | Giả thuyết "không có luật nào". Điểm chuẩn hoá sao cho null = 0 điểm. |
| **`match`** | Điểm khớp 0–1 giữa luật agent phát biểu và luật thật. Ngưỡng "tìm ra" = 0.80. |
| **`t_discover`** | Tick sớm nhất có entry đúng **và** entry đó còn trong sổ tới cuối ván. |
| **Gate A / B / C** | Ba cửa lọc lúc sinh luật: quan sát được / khả giải / định danh được. |
| **định danh được** | Có đủ bằng chứng gần trượt để phân biệt luật thật với luật đơn giản hơn. |

## Thế giới mở

| Thuật ngữ | Nghĩa |
|---|---|
| **server** | Quyền lực tuyệt đối. Giữ trạng thái thế giới và luật ẩn. Một tiến trình, một máy. |
| **client** | Máy của người chơi. Tự host model. **Chỉ mở kết nối đi ra.** Trả về ý đồ, không trả trạng thái. |
| **spectator** | Trình duyệt xem live. Chỉ đọc. Không bao giờ thấy luật ẩn trước REVEAL. |
| **Lab mode** | 5 loài cố định, một người host hết. Tái lập được. Dùng cho Q1–Q7. |
| **Open mode** | Ai cắm máy vào cũng chơi. Không tái lập. Dùng để trình diễn và xây cộng đồng. |
| **dung sai trễ** | Số tick mà một quyết định về muộn vẫn còn được dùng. Quá thì bỏ, rơi về phản xạ. |

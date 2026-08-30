# W-19 · Ba đặc điểm bốc thăm — cầu nối giữa cơ chế và ngoại hình

| | |
|---|---|
| **Track** | World · **Phụ thuộc** W-18, N-13, N-15 · **Chặn** X-11 |
| **File** | `genesis/features.py`, `genesis/genai.py`, `scripts/creature_design.py` |
| **Giao cho model rẻ?** | ❌ tự viết — ranh giới "hình được phép nói gì" là cả thiết kế |
| **Tài liệu gốc** | phiếu này · [03 §4](../03-LUAT-AN-V5.md) quan sát gián tiếp |

## 1. Câu hỏi sinh ra nó

> *"Khi tạo sinh vật, lấy các đặc điểm sinh vật đặc biệt — ví dụ vừa sống dưới
> nước vừa trên cạn, lông dài… random 3 đặc điểm để thiết kế sinh vật qua Meshy
> AI. Phải mô tả kĩ các thứ như 4 chân, lông dài…"*

Đến hết W-18, một loài là **một vector sáu số cộng một tầng**. Hai loài cùng vector
là hai loài giống hệt nhau, và cái tên `L1`..`L5` không mang thêm nghĩa gì. Nhưng
sinh vật thật khác nhau ở những thứ **không cộng lại thành một điểm số**: con thì
đào hang, con lưỡng cư, con lông dài, con có nọc.

## 2. Điều đáng nói nhất: đặc điểm mang HAI mặt, và chúng buộc phải khớp

Mỗi `Feature` có:

* `effect` — nó đổi gì trong vòng tick (đi được ô nào, hao sức bao nhiêu, chịu
  đòn ra sao);
* `look` — nó **trông** thế nào, cụ thể tới mức dựng được hình 3D.

Nên **hình dáng con vật không phải minh hoạ cho luật chơi — nó LÀ luật chơi.** Ai
nhìn thấy chân màng, mõm dài, móng bới thì đọc được là con này bơi được và đào
được, **trước khi nó kịp làm gì**. Đó đúng là thứ [03 §4](../03-LUAT-AN-V5.md)
gọi là quan sát gián tiếp, và nó là một kênh thông tin thật cho agent — không
phải trang trí.

Hệ quả kỷ luật: một đặc điểm mà thiếu `look` thì kênh ấy mất một chiều; thiếu
`note` thì không ai biết nó đổi gì. Bài kiểm đòi **cả hai**.

## 3. Mười hai đặc điểm, bốc ba — 220 tổ hợp

| nhóm | đặc điểm |
|---|---|
| đi lại | lưỡng cư · **biết đào hang** · trèo giỏi · màng lượn |
| phòng thủ | lông dài · vảy cứng · gai độc · vỏ sò |
| giác quan | mắt đêm · râu cảm ứng |
| kiếm ăn | răng nanh · túi má |

Ít tới mức đọc hết bảng là hiểu cả thế giới; nhiều tới mức không ván nào giống
ván nào. Bốc **tất định theo `(loài, seed)`** — bốc lại mỗi lần chạy thì ba đường
gãy cùng lúc: bộ đệm hình 3D khoá theo chuỗi mô tả, `--replay` dựng lại ván cũ,
và bộ chấm so hai ván với nhau.

## 4. Hang, và vì sao nó phải mở khoá CẢ ĐÁ

`CAVE` là **lõi của khối đá**, sinh ra bằng đúng phép xói mòn cho `DEEP` ở W-18.
Nên hang **nằm lọt giữa đá** — không ai đi bộ tới được.

Vậy `DAO_HANG` mở khoá **cả `ROCK` lẫn `CAVE`**: vào được hang nghĩa là xuyên
qua được lớp đá bao quanh. Thiếu `ROCK` thì hang thành một ô mà **chính chủ cũng
không vào nổi**.

Và đó là điều làm hang đáng có: nó là chỗ trốn **tuyệt đối**. Kẻ săn nhìn thấy
con mồi biến mất vào vách đá và không có đường nào theo vào. `HOANG_MAC` có 55 ô
hang, `HEM_NUI` 31, `RUNG_RAM` **không có ô nào** — mỗi bản đồ thưởng cho một
đặc điểm khác nhau.

## 5. Ba nấc mở khoá đường đi, và thứ tự có nghĩa

```
1. TẦNG      — cá không lên bờ, dù nó có đặc điểm gì đi nữa
2. ĐẶC ĐIỂM  — DAO_HANG mở đá + hang; CANH_LUOT mở đá
3. TRAIT     — speed để trèo, armor để băng lửa; TREO_GIOI HẠ ngưỡng trèo
```

Nấc 2 đứng trước nấc 3 là cố ý: đặc điểm là thứ con vật **sinh ra đã có**, còn
trait thì nó **kiếm được** bằng dịch trait ([B-13](B-13-dich-trait-llm.md)). Hai
đường khác nhau tới cùng một chỗ, và cả hai đều mở.

## 6. Tầng viết lại: viết lại được, THÊM thì không

`creature_prompt` ghép ba mảnh (dáng theo tầng · ba đặc điểm · vector trait). Nó
**đúng** nhưng là một danh sách. Gemini viết lại thành một đoạn văn, rồi mới gửi
Meshy.

**Bất biến:** model chỉ được diễn đạt lại, **không được thêm bộ phận**. Lý do
không phải thẩm mỹ mà là đo đạc — nếu nó tả thêm một cái vây không có thật thì
kênh quan sát gián tiếp **nói dối theo cách không ai kiểm được**.
`verify_rewrite` giữ ranh giới bằng cách đòi mọi nhóm giải phẫu trong bản gốc
phải còn trong bản viết lại; hỏng thì rơi về bản gốc, **không bao giờ ném**.

## 7. Bẫy đã trả giá

**Bẫy 1 — Gemini 3 NGHĨ trước khi trả lời, và phần nghĩ ăn cùng ngân sách.** Đo
thật: đầu vào 168 token, `thoughtsTokenCount = 1110`, câu trả lời 101 token. Với
trần 300 nó trả về một mẩu suy nghĩ dở (`/no digits like "4", use "bốn`) — JSON
hợp lệ, `finishReason: STOP`, và rác. Kiểu hỏng tệ nhất: **trông y như model kém**.

**Bẫy 2 — hàng rào khớp theo TỪ ĐƠN bắt oan ngay lần chạy đầu.** Gemini viết
"đứng vững vàng trên bốn **chi**"; bản gốc viết "bốn **chân**". Đúng nghĩa, đúng
số chi, bị loại. Phải khớp theo **nhóm đồng nghĩa**. Và cố ý bỏ "mang"/"mai" ra
khỏi hàng rào: chúng quá thường trong tiếng Việt nên khớp nhầm khắp nơi, mà một
hàng rào khớp nhầm thì tệ hơn không có — nó dạy người sửa sau bỏ qua cảnh báo.

**Bẫy 3 — "tối đa 90 từ" làm model ĐẾM TỪ RA THÀNH CHỮ.** Nó trả về
`(48) Bốn(49) chi(50) ngắn(51) chắc,(52) riêng…`. Một ràng buộc đếm được là một
lời mời đếm, và nó đếm ngay giữa câu trả lời. Nói giới hạn bằng **số CÂU**.

**Bẫy 4 — 2000 token vẫn chưa đủ, và ca đứt trông y hệt ca đánh rơi.** Phần nghĩ
~1100 cộng một đoạn bốn câu là chạm trần; câu trả lời đứt giữa chừng, mất chữ
"móng vuốt" ở cuối, và `verify_rewrite` báo *"đánh rơi bộ phận"*. Ta sẽ đi sửa
**hàng rào** trong khi lỗi nằm ở **ngân sách**. Nên `_one_call` vứt luôn mọi phản
hồi có `finishReason` khác `STOP` — một câu dở tệ hơn không có câu nào.

**Bẫy 5 — bản viết lại bị TỪ CHỐI thì đừng xoay khoá.** Bản đầu gộp "khoá hỏng"
với "model trả bản không đạt" làm một, nên một lần bị bộ kiểm từ chối kéo theo
đủ **14 khoá**, mỗi lần ~30 giây: năm sinh vật mất hơn **25 phút** thay vì hai
phút rưỡi, và không dòng log nào nói vì sao — nó chỉ *chậm*. Khoá hỏng thì xoay
khoá; model trả sai thì tiêu ngân sách thử (`MAX_REWRITE_TRIES = 2`).

**Bẫy 6 — tên model không cố định.** `gemini-2.0-flash` trả 404 kèm câu *"no
longer available, please update to gemini-3.6-flash"*. Đọc từ `GEMINI_MODEL` để
lần sau không phải sửa code.

**Bẫy 7 — KHOÁ.** Không khoá nào vào kho. `.env` gitignore, đọc qua môi trường,
và `tests/test_features.py` quét **mọi file git theo dõi** tìm `AIzaSy`.

## 8. Nghiệm thu

```bash
pytest tests/test_features.py tests/test_domain.py -q
python scripts/creature_design.py --seed 21                 # mô tả gốc
python scripts/creature_design.py --seed 21 --rewrite       # qua Gemini
```

Đã chạy thật (2026-08-30): **5/5 sinh vật qua được Gemini**, mô tả gọn lại
725 → 603 ký tự mà không đánh rơi bộ phận nào. Kết quả ở
`assets/meshy/creatures.json`.

## 9. Chưa làm

**Chiều ngược — từ ngoại hình suy ra đặc điểm.** Đề bài có nhắc *"từ ngoại hình
sinh vật sau khi thiết kế, lấy những đặc điểm khác"*. Chiều ấy cần đọc **ảnh**
model 3D trả về, và nó chỉ có nghĩa khi đã có mesh thật trong tay. Việc riêng,
phiếu riêng.

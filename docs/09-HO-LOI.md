# 09 · Bốn họ lỗi mà dự án này liên tục vấp lại

> [00 Bản đồ](00-INDEX.md) · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md) · **09 Họ lỗi**

Tài liệu này không mô tả hệ thống. Nó mô tả **cách hệ thống này hỏng**, và nó tồn
tại vì bốn kiểu hỏng dưới đây đã lặp lại đủ nhiều lần để không còn là tai nạn.

Mỗi họ đều có chung một tính chất, và đó là lý do chúng đáng một tài liệu riêng:
**không cái nào báo lỗi.** Ván vẫn chạy, test vẫn xanh, file kết quả vẫn trông
như thật. Chúng chỉ làm những con số **sai một cách yên lặng** — mà con số là
toàn bộ lý do dự án này tồn tại.

---

## Họ 1 — Hai bản của một khái niệm, rồi bản ít người nhìn mục đi

**Đã đếm được chín lần.**

| # | Hai chỗ | Triệu chứng |
|---|---|---|
| 1 | `schema_for` ở `strategist` và ở `routes_work` | luật ăn quả **bất khả về cấu trúc** với client qua mạng |
| 2 | `config.FOUNDERS` và trait cấp lúc `/join` | người chơi chọn brain 5 **tụt về brain 2** sau cái chết đầu |
| 3 | quên-khi-chết ở `strategist.observe` và ở `net.match` | sinh vật qua mạng **giữ nguyên sổ tay** qua mọi đời |
| 4 | `heard` ở hai chỗ | người chơi qua mạng **không bao giờ nghe thấy ai** |
| 5 | `max_tokens` chép tay ở `routes_work` | `codex` qua mạng **đứt giữa trường `effect`** |
| 6 | ngân sách oracle chép tay ở `oracle_run` | `pred_acc` ra **đúng 0.000 trên mọi dòng của mọi ván** |
| 7 | bộ dựng lưới ở `world` và ở `maps` | thêm hai địa hình mà **không ô nào mọc ra** |
| 8 | mã địa hình `"PWBRF"` chép tay ở `net/match` | `ValueError` giữa vòng phát khung cho người xem |
| 9 | `world.kits` không gán cho loài đăng ký lúc chạy | loài của **người lạ không có đặc điểm nào** |

**Cách sửa, cả chín lần đều giống nhau:** gom về một chỗ mà cả hai đường gọi
vào — `lineage.forget_on_death`, `genesis.minds.Minds`, `world.TERRAIN_CODE`,
`world.SEEDED_TERRAINS`, `strategist._budget`, `world.food_for`.

**Cách sửa KHÔNG hiệu quả:** đồng bộ hai bản. Nó đúng đúng một ngày.

**Vì sao nó cứ mọc lại:** mỗi lần thêm một khái niệm mới vào thế giới, nó mọc
lại **ngay lần đầu**. Lần thứ chín xảy ra trong cùng buổi vừa dọn xong lần thứ
tám. Nên đừng chờ nó tự hết; hãy hỏi *"khái niệm này có mấy chỗ biết về nó?"*
mỗi lần thêm một khái niệm.

---

## Họ 2 — Cơ chế có luật chơi mà không ai nói cho model biết

**Đã đếm được bốn lần**, và đây là họ tốn nhiều thời gian nhất.

| # | Cơ chế | Model không biết điều gì | Hậu quả đo được |
|---|---|---|---|
| 1 | `want_codex` | rằng đó là **cánh cửa duy nhất** để ghi Sổ Luật | bật **0/44** lượt → `CODEX_OP = 0` → điểm 0 trên cả ba luật |
| 2 | `want_hunch` | y hệt, cho Linh cảm | nhắc tới **1 lần trên 85** lời gọi → `HUNCH_OP = 0`, cả nhánh thí nghiệm của X-09 **không bao giờ chạy** |
| 3 | ghi đè một ô linh cảm | rằng nó **xoá sạch bảng đếm** của ô ấy | ghi đè 3–4 lần/200 tick → **23 ô, 3 lượt thử** |
| 4 | số điều kiện | rằng giả thuyết càng hẹp càng **hiếm được thử** | linh cảm 2 điều kiện gần như không bao giờ khớp |

**Bài học:** một trường trong schema **không tự nói nó dùng để làm gì**. Một quy
tắc chỉ tồn tại trong code là một quy tắc model không biết — và nó sẽ chơi sai
mà không có gì báo, vì "chơi sai" trông y hệt "chơi kém".

Ca 1 sửa bằng **một câu** trong khối D và tỉ lệ bật đi từ `0/44` lên `3/18`. Đó
là tỉ lệ lợi/công cao nhất từng đo được trong dự án này.

**Cách phát hiện:** trước khi kết luận "model không làm được X", hãy đếm xem model
có bao giờ **thử** làm X không. Nếu số lần thử bằng 0 thì bạn đang đo một thứ
không xảy ra.

---

## Họ 3 — Bài canh chừng bắt lời kể về con bọ, thay vì bắt con bọ

**Đã đếm được bốn lần trong một ngày.**

* Bài canh `"mesh"` không được xuất hiện trong `tick.py` → nó bắt một **chú
  thích** nhắc tới chữ ấy.
* Bài canh `"PWBRF"` không được chép tay → bắt chú thích **giải thích lỗi cũ**.
* Bài canh khoá API tìm tiền tố `AIzaSy` → bắt ba file **đang nói về** khoá,
  trong đó có chính nó.
* Bài canh chữ ký hàm `== ["traits"]` → đỏ khi thêm một tham số **server tự
  sinh**, thứ nó không định cấm.

**Cách sửa:**

1. Soi **code**, không soi chú thích — lọc dòng bắt đầu bằng `#` trước khi quét.
2. Khớp theo **hình dạng thật**, không theo tiền tố (`AIzaSy` + 33 ký tự, không
   phải `AIzaSy`).
3. Dùng **danh sách cho phép + danh sách cấm**, không dùng danh sách chính xác —
   danh sách chính xác đỏ mỗi lần thêm thứ vô hại.

**Vì sao nó nguy hiểm:** một hàng rào bắt nhầm sẽ bị người sửa sau **tắt đi**, và
lúc ấy nó tệ hơn không có hàng rào nào.

---

## Họ 4 — Phép đo hỏng trông y hệt phép đo cho kết quả âm

Đây là họ nguy hiểm nhất, vì nó **kết luận thay cho bạn**.

| Ca | Trông như | Thật ra là |
|---|---|---|
| `pred_acc = 0.000` trên mọi dòng | "model không tiên đoán được" | ngân sách token thiếu 7 lần, câu trả lời bị cắt |
| nhánh linh cảm của X-09 | "linh cảm vô dụng" | `want_hunch` không bao giờ được bật |
| `match = 0.000` | "model không quy nạp được" | **vẫn có thể đúng** — nhưng chỉ sau khi loại hết những cái trên |
| `test_work` đỏ rồi xanh | "máy CI dở" | ván dài 5 mili-giây, đua với vòng lặp nền |
| `make lint` in "ruff chưa cài" | "chưa cài ruff" | ruff có cài và vừa tìm ra 403 lỗi |
| `pgrep -f "genesis.run"` trong vòng chờ | "ván vẫn đang chạy" | vòng chờ khớp **chính dòng lệnh của nó**, chờ chính mình, và ván tiếp theo **không bao giờ được khởi động** |

**Ba phép thử rẻ, làm trước khi kết luận bất cứ điều gì:**

1. **Phương sai bằng không là dấu hiệu hỏng, không phải kết quả.** Không model
   nào cho ra đúng cùng một số trên 65 dòng liên tiếp.
2. **Đếm số lần THỬ trước khi đọc tỉ lệ THÀNH CÔNG.** `0/0` và `0/100` là hai câu
   trả lời khác hẳn nhau.
3. **Chạy chế độ gian lận.** Cho một tác nhân biết trước đáp án và đòi điểm tuyệt
   đối. Không đạt thì lỗi ở bộ chấm, và mọi kết luận phía trên đều treo lơ lửng.
   Đây là việc của `scripts/ci_smoke.py`, và nó chạy trong CI mỗi lần push.

**Ca cuối trong bảng đáng nói riêng, vì nó là công cụ theo dõi tự nói dối.**
Lệnh `while pgrep -f "genesis.run"; do sleep 30; done` có một dòng lệnh **chứa
chuỗi `genesis.run`**, nên `pgrep` khớp chính nó. Vòng lặp chờ chính mình, không
bao giờ thoát, và lệnh đứng sau nó — khởi động phép đo — **không bao giờ chạy**.
Nhìn từ ngoài thì mọi thứ đều đúng: có một task đang chạy, `pgrep` xác nhận
"còn chạy", và tôi đã báo cáo hai lượt liền rằng phép đo đang tiến triển.

Cách chờ đúng: **file đánh dấu** do chính việc cần chờ ghi ra.

```bash
nohup sh -c 'việc-cần-chạy; echo done > /tmp/x.done' &
until [ -f /tmp/x.done ]; do sleep 120; done
```

**Và một câu nữa, chép từ phiếu [B-10](tasks/B-10-score.md):** *đừng chẩn đoán
bằng cách đổi model.* Trong hai ngày liên tiếp, mỗi lần con số xấu thì nguyên
nhân đều là hạ tầng của chính chúng ta, không phải năng lực của model.

---

## Đọc cùng

* [06-CONG-VIEC §3](06-CONG-VIEC.md) — thang chẩn đoán tám nấc khi `match = 0`
* [N-16](tasks/N-16-ngang-bang-mang.md) — họ 1, ca kinh điển nhất
* [B-14 §7](tasks/B-14-linh-cam.md) — họ 2 và họ 4 gặp nhau
* [01-STATUS](01-STATUS.md) nhật ký — mọi ca ở trên đều có một dòng kèm số đo

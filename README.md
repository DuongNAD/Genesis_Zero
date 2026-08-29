# Genesis Zero

> Sandbox 2D nơi mỗi sinh vật là một tâm trí LLM riêng, chạy trên máy của một
> người khác nhau, và **vật lý của thế giới được bốc thăm mỗi ván**.
> Không ai biết luật. **Ai tìm ra luật trước thì thắng.**

```bash
git clone https://github.com/DuongNAD/Genesis_Zero.git && cd Genesis_Zero
pip install -r requirements.txt
python -m genesis.run --seed 1 --ticks 200 --controller reflex
```

Một ván chạy được ngay: không model, không mạng, không cấu hình.
→ **[Hướng dẫn đầy đủ](docs/HUONG-DAN.md)**

---

## Vì sao có dự án này

Bản trước chết vì một lý do đơn giản: **sinh tồn không chấm được.** Một con vật
sống 400 lượt — vì nó giỏi, hay vì nó gặp may, hay vì bản đồ dễ? Không tách
được, nên không có tín hiệu để huấn luyện.

Bản này đổi câu hỏi. Thế giới bốc thăm **2–3 luật ẩn** mỗi ván:

```
KHI uống nước                          THÌ mất máu
KHI đứng cạnh kẻ khác loài             THÌ trúng độc
KHI vào ban ngày VÀ vừa nghỉ ngơi      THÌ trúng độc
```

Không sinh vật nào được cho biết. Cách duy nhất để biết là **thử và quan sát** —
và thử có thể chết. Khi tin mình đã tìm ra, sinh vật ghi vào **Sổ Luật**. Không
ai xác nhận đúng sai cho nó.

Nhưng **server sinh ra luật nên server biết đáp án.** Nên có thứ chấm được:

```
match      luật phát biểu khớp luật thật bao nhiêu  (bảng chân trị, 0–1)
t_discover mất bao nhiêu lượt để khớp
R_i        điểm, đã tính cả tốc độ
```

Bề ngoài của quả **bị xáo lại mỗi ván**, nên "quả đỏ thì độc" học từ ván trước
là một cái bẫy, không phải tri thức. Cái duy nhất mang sang được là **phương
pháp**.

## Điều dự án này muốn chứng minh

> **Model to hơn thành loài đỉnh vì nó quy nạp giỏi hơn — không phải vì nó được
> cho nhiều máu hơn.**

Ngân sách trait bắt buộc: **12 điểm cho 6 chỉ số**. Chọn `brain=5` là chấp nhận
giáp mỏng, chân chậm, mắt kém. Não to đổi lấy **từ vựng rộng hơn** (nói được
nhiều loại luật hơn), **sổ nhiều ô hơn**, **ngân sách token lớn hơn** — và trả
bằng thân thể. Khai láo model không lợi gì vì ngân sách tự thực thi.

Đường cơ sở đã đo (40 seed, không model): trong thế giới **không có luật ẩn**,
loài brain 4 sống **kém hơn** loài brain 0 (0,755 so với 0,812). Brain **tốn**
chứ không được thưởng. Nên mọi khoảng cách đo được về sau là khoảng cách **kiếm
được**.

---

## Nó hoạt động thế nào

```
  ┌─ server ván ────────────┐        ┌─ máy người chơi A ──────┐
  │ mô phỏng thế giới       │◄──────►│ client  →  llama-server │
  │ giữ luật ẩn (bí mật)    │  HTTP  └─────────────────────────┘
  │ phát prompt + schema    │        ┌─ máy người chơi B ──────┐
  │ chấm điểm cuối ván      │◄──────►│ client  →  llama-server │
  └─────────────────────────┘        └─────────────────────────┘
```

**Server không gọi model.** Nó gửi đi `user_block` + `json_schema` rồi nhận
`decision` về. Mọi lời gọi model đến từ client, trên GPU của chính người chơi —
nên mười người vào chơi là mười GPU khác gánh, server không thêm tải.

**Client kéo, server không bao giờ đẩy** — chạy được sau mọi NAT, không cần mở
cổng.

Server **không bao giờ nhả tên lớp nội bộ** (`FRUIT_A`…) qua bất kỳ endpoint
nào. Một bộ chặn ném lỗi thay vì lọc âm thầm, và `scripts/hostile_client.py`
kiểm điều đó từ ngoài.

---

## Trạng thái

| | |
|---|---|
| Test | **548 mục, xanh** |
| Phiếu việc | 58, xem [docs/01-STATUS.md](docs/01-STATUS.md) |
| Đường ống | chạy trọn: sinh luật → ván → Sổ Luật → chấm điểm |
| Bộ chấm | **đã kiểm bằng chế độ gian lận: `match = 1.000`** |
| Model 7B thật | ghi sổ đều, **`match` vẫn 0.000** — xem dưới |

### Kết quả trung thực nhất tới giờ

Qwen2.5-7B, ba ván 200 lượt: **149 lần ghi Sổ Luật, 133 được nhận, 0% lượt nghĩ
bị trượt — và `match = 0.000` cả ba.**

Không phải lỗi đường ống. Chế độ gian lận (server giả biết trước đáp án) cho
`match = 1.000`, nên bộ chấm bắt được lời giải đúng.

Chỗ hỏng là **sự chú ý của model**:

```
LÀM GÌ trong ván        VIẾT VỀ GÌ trong Sổ Luật
  EAT     309  48,4%         32   72,7%
  DRINK   168  26,3%          0    0,0%   ←
```

Sinh vật **uống nước 168 lần**, luật `DRINK → DAMAGE` nổ **155 lần**, và sổ tay
ghi rành rành `t99/t84/t64: TÔI uống nước → máu tụt hẳn xuống`. Không con nào
ghi nó. Chúng viết `EAT → HEAL` 24 lần.

Nó làm đúng thí nghiệm rồi không nhìn kết quả. Đó là bài toán còn lại.

---

## Đọc gì tiếp

| bạn muốn | đọc |
|---|---|
| **chạy thử ngay** | [docs/HUONG-DAN.md](docs/HUONG-DAN.md) |
| hiểu thiết kế | [docs/03-LUAT-AN-V5.md](docs/03-LUAT-AN-V5.md) |
| cắm máy vào chơi cùng | [docs/04-THE-GIOI-MO.md](docs/04-THE-GIOI-MO.md) |
| giao thức HTTP | [docs/05-GIAO-THUC.md](docs/05-GIAO-THUC.md) |
| chạy trên Windows | [docs/CHAY-TREN-WINDOWS.md](docs/CHAY-TREN-WINDOWS.md) |
| việc còn lại | [docs/01-STATUS.md](docs/01-STATUS.md) |

Mỗi phiếu trong [docs/tasks/](docs/tasks/) **tự chứa đủ thông tin**: mục tiêu,
bất biến, cách nghiệm thu, và — quan trọng nhất — **những lỗi đã mắc và vì sao**.
Đó là phần đáng đọc nhất của kho này.

## Lệnh hay dùng

```bash
make preflight    # máy này chạy được một ván thật chưa?
make test         # 548 test
make serve        # server ván, cổng 8000
make hostile      # kiểm cửa chống lạm dụng — chạy TRƯỚC khi phơi ra internet
make expose       # mở tunnel ngrok
make site         # dựng docs/site.html để đọc offline
```

Windows: xem bảng thay cho `make` trong [docs/CHAY-TREN-WINDOWS.md](docs/CHAY-TREN-WINDOWS.md).

## Giấy phép

Chưa chọn. Cứ đọc, chạy, và fork thoải mái; hỏi trước nếu muốn dùng thương mại.

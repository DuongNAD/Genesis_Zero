# Genesis Zero

> Sandbox 2D nơi mỗi sinh vật là một tâm trí LLM riêng, chạy trên máy của một
> người khác nhau, và **vật lý của thế giới được bốc thăm mỗi ván**.
> Không ai biết luật. **Ai tìm ra luật trước thì thắng.**

### ⚡ Khởi chạy 1-Chạm (< 60 giây)

**macOS / Linux:**
```bash
git clone https://github.com/DuongNAD/Genesis_Zero.git && cd Genesis_Zero
./run.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/DuongNAD/Genesis_Zero.git && cd Genesis_Zero
.\run.ps1
```

*(Hoặc cài đặt thủ công: `pip install -r requirements.txt` rồi chạy `python -m genesis.run --seed 1 --ticks 200 --controller reflex`)*

Một ván chạy được ngay: tự động thiết lập `.venv`, quét đa backend LLM (Ollama, llama.cpp, vLLM, Mock), tự động fallback về Offline Reflex nếu không có GPU/LLM cục bộ.
→ **[Hướng dẫn đầy đủ](docs/HUONG-DAN.md)**

### B-10 A/B: Frontier Thinking vs ReflexStrategist

Đo so sánh có kiểm soát giữa model tư duy "frontier" và chiến lược offline, cùng seed & cùng bộ chấm:

```bash
# Khoá giao thức trước (không gọi model, in JSON 5 seed):
python scripts/b10_ab.py --url <endpoint> --model <model> --out scratch/ab-plan --plan

# Chạy thật — 5 seed, thứ tự nhánh xen kẽ, ghi log/truth/CSV cho từng nhánh:
python scripts/b10_ab.py --url <endpoint> --model <model> --out scratch/ab1

# Cấu hình backend qua env khi chạy server:
GENESIS_LLM_BACKEND=frontier GENESIS_LLM_MODEL=<model> GENESIS_LLM_API_KEY=<key> python -m genesis.run --seed 7
```

Kết quả gồm `protocol.json` (giao thức khoá), log ván từng seed, và tổng hợp điểm theo nhánh. Mỗi lần chạy cần thư mục `--out` mới; không tái sử dụng thư mục của `--plan`. Giao thức chưa có kết quả đo với model thật.

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

## Thế giới có gì

Lưới 24×24, **ba tầng** sống: nước · cạn · trời. Tầng là thuộc tính của loài và
**không dịch được** — nhưng *đường đi trong tầng* thì kiếm được, và đó là chỗ
thế giới này khác một bàn cờ:

```
sư tử (attack 4, speed 1)  không trèo được cây
khỉ   (speed 5)            trèo được          ← cùng một luật, đọc từ vector trait
thỏ   (đặc điểm ĐÀO HANG)  xuyên được đá vào hang, kẻ săn không theo vào nổi
cá                         chỉ nước; nước SÂU là chỗ trốn tuyệt đối
chim                       bay khắp nơi, nhưng phải HẠ XUỐNG mới chạm được
```

Không loài nào được hard-code: ngưỡng trèo đọc thẳng từ `speed`, nên một dòng dõi
**học được cách trèo** bằng cách dịch trait. Mỗi loài còn bốc **ba đặc điểm sinh
học** trong mười hai (lưỡng cư · lông dài · gai độc · mắt đêm · râu cảm ứng…),
cho 220 tổ hợp — và mỗi đặc điểm mang **hai mặt buộc phải khớp nhau**: nó đổi gì
trong vòng tick, và nó *trông* thế nào. Nên hình 3D không minh hoạ luật chơi, nó
**là** luật chơi: nhìn thấy chân màng và mõm dài là đọc được con này bơi và đào
được, trước khi nó kịp làm gì.

Bảy loại địa hình, và ba kiểu nước (ao · hồ · biển) sinh ra từ **cách xếp** chứ
không từ enum mới — lõi của một mảng nước thành nước sâu, nên **bờ nước được bảo
đảm bằng cấu trúc**. Bờ là ô duy nhất mà tầng nước và tầng cạn đứng cạnh nhau
được, nên cả ba tầng dồn về một vành đai hẹp. Đo được: chim là kẻ săn đứng đầu và
nó **có** săn cá — ở nước nông, không phải ngoài khơi.

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
| Test | **1718 mục được thu thập / 113 files**; baseline 2026-09-17 (20260917T132824Z): 1664 pass, 0 fail, 0 error, 39 skip — 100% ngoài skip. Xem [baseline](docs/BASELINE_TESTING.md). |
| Phiếu việc | 65, xem [docs/01-STATUS.md](docs/01-STATUS.md) |
| Đường ống | chạy trọn: sinh luật → ván → Sổ Luật → chấm điểm |
| Bộ chấm | **đã kiểm bằng chế độ gian lận: `match = 1.000`** |
| Model 7B thật | ghi sổ đều, **`match` vẫn 0.000** — xem dưới |
| Đã loại khỏi nghi can | bộ chấm · sổ tay · ngân sách token · ba cơ chế từng câm lặng |

### Kết quả trung thực nhất tới giờ

Chưa model nào ăn được điểm. Nhưng câu chuyện đằng sau con số 0 đã đổi hai lần.

**Qwen2.5-14B, seed 55, tick 99** — một sinh vật ghi vào Sổ Luật:

```
WHEN DRINK() THEN DAMAGE
```

Đó là **đúng nguyên văn luật thật**. Điểm vẫn `0.000`, và lý do không phải model:
nó ghi `mag=MED`, **quên `dur`**. Bộ chấm **nhân** điểm trên từng chiều luật thật
có định nghĩa — `mag` kề nhau ăn 0,85, `dur` thiếu ăn 0, tích về 0. Mà schema
lúc ấy **không đòi** `mag`/`dur`.

Đếm lại toàn bộ 235 mục Sổ Luật thu được: **chỉ 23% nêu đủ hai trường bộ chấm
cần.** 77% dữ liệu không thể ăn điểm về mặt cấu trúc. Đã vá (`lawdsl.EFFECT_FIELDS`,
một bảng cho cả bộ sinh luật lẫn schema); tỉ lệ giờ là **100%**.

Đây là lần thứ **sáu** cùng một bài học: *cái gì bộ chấm bắt bẻ thì schema phải
đòi trước.* Mỗi lần đều làm dữ liệu chết trong im lặng, và mỗi lần đều suýt
thành một kết luận sai về model.

Ván đầu tiên chạy trên nền đã sửa mới có **5 mục sổ** — quá nhỏ để kết luận gì.
Việc tiếp theo là mẫu đủ lớn, không phải một ván đẹp hơn.

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
make test         # 1718 test (số lượng collection; không phải tất cả đã pass)
make serve        # server ván, cổng 8000
make hostile      # kiểm cửa chống lạm dụng — chạy TRƯỚC khi phơi ra internet
make expose       # mở tunnel ngrok
make site         # dựng docs/site.html để đọc offline
```

Windows: xem bảng thay cho `make` trong [docs/CHAY-TREN-WINDOWS.md](docs/CHAY-TREN-WINDOWS.md).

## Giấy phép

[Apache License 2.0](LICENSE). Đọc, chạy, fork, sửa, dùng thương mại — không
cần hỏi. Chỉ cần giữ lại thông báo bản quyền và ghi rõ chỗ nào bạn đã sửa.

*(Câu cũ ở đây viết "chưa chọn… hỏi trước nếu muốn dùng thương mại". Nó có hai
vấn đề: không có file `LICENSE` thì luật mặc định là **không ai được phép dùng
lại gì cả** — ngược hẳn ý định — và "cho dùng tự do trừ thương mại" không khớp
giấy phép mã nguồn mở chuẩn nào. Apache-2.0 cho dùng thương mại thoải mái, nên
điều kiện "hỏi trước" đã bỏ để tài liệu và giấy phép nói cùng một điều.)*

<!-- test-inventory:start -->
### Danh mục test theo pytest discovery

Số mục bao gồm các biến thể parametrized; collection không đồng nghĩa PASS.

| Thư mục | Số mục |
|---|---:|
| `tests` | 1510 |
| `tests/e2e` | 208 |
| **Tổng** | **1718** |

Đối soát và xuất danh sách từng file/node ID:

```powershell
& "E:\Project\01_AI_Agents\Genesis_Zero\.venv\Scripts\python.exe" "E:\Project\01_AI_Agents\Genesis_Zero\scripts\count_tests.py"
```
<!-- test-inventory:end -->

# Hướng dẫn sử dụng Genesis Zero

Từ cài đặt tới lúc có người khác cắm máy vào chơi cùng.

---

## 0. Trong 60 giây

**Khởi chạy 1-chạm (Khuyên dùng):**

- **macOS / Linux**:
  ```bash
  git clone https://github.com/DuongNAD/Genesis_Zero.git && cd Genesis_Zero
  ./run.sh
  ```
- **Windows (PowerShell)**:
  ```powershell
  git clone https://github.com/DuongNAD/Genesis_Zero.git && cd Genesis_Zero
  .\run.ps1
  ```

*(Hoặc chạy thủ công qua Python: `pip install -r requirements.txt` rồi `python -m genesis.run --seed 1 --ticks 200 --controller reflex`)*

Xong. Bạn vừa chạy một ván 200 lượt: script tự động cấu hình `.venv`, kiểm tra dependencies, tự dò quét LLM và chuyển mượt về phản xạ nếu không có GPU/LLM cục bộ. Màn hình in ra lưới thế giới và bảng tổng kết.

Muốn sinh vật **suy nghĩ** bằng LLM cục bộ (Ollama, llama.cpp, vLLM) thì xem mục 2.

---

## 1. Trò chơi này là gì

Lưới 24×24. Mười lăm sinh vật thuộc năm loài. Chúng ăn, uống, đánh nhau, nói
chuyện, chết, và truyền lại cho đời sau.

Mỗi ván, thế giới **bốc thăm 2–3 luật ẩn** — ví dụ *"uống nước thì mất máu"*
hoặc *"đứng cạnh kẻ khác loài thì trúng độc"*. **Không sinh vật nào được cho
biết.** Cách duy nhất để biết là thử và quan sát.

Điểm **không** tính theo việc sống lâu. Điểm tính theo: **ngươi phát biểu được
luật không, và mất bao lâu để phát biểu đúng.** Server sinh ra luật nên server
biết đáp án — đó là lý do chấm được.

> Muốn hiểu vì sao thiết kế như vậy: [03-LUAT-AN-V5](03-LUAT-AN-V5.md) §0–§1.

---

## 2. Cắm model vào

Sinh vật nghĩ bằng một `llama-server` chạy trên máy **của bạn**.

```bash
# macOS / Linux
SLOTS=8 bash scripts/serve_L2.sh

# Windows
.\scripts\serve_L2.ps1 -Slots 8
```

Rồi chạy một ván có suy nghĩ:

```bash
python -m genesis.run --seed 55 --ticks 200 --arm STANDARD --llm all \
  --llm-url http://127.0.0.1:8080 \
  --out runs/van1.jsonl --truth runs/van1.truth.json
```

Chấm điểm:

```bash
python -m genesis.score runs/van1.jsonl runs/van1.truth.json
```

### Chọn kích thước cho đúng

`-c` là **tổng** KV chia cho mọi slot, **không phải mỗi slot**:

```
-c  =  (token mỗi slot) × (số slot)
```

Token mỗi slot phải **≥ 4096**. Prompt giữa ván đo được là **2737–2826 token**
(sổ tay đầy, Sổ Luật, lời nghe được). Đặt thấp hơn thì llama-server **trả lỗi
HTTP chứ không cắt bớt**, nên triệu chứng là *"model tự dưng im lặng"* — rất dễ
chẩn đoán nhầm sang model yếu.

| VRAM | model | slot | `-c` |
|---|---|---|---|
| 16 GB | 7B q4 | 16 | 65536 |
| 16 GB | 14B q4 | 6 | 24576 |
| 24 GB+ | 14B q4 | 12 | 49152 |

Đo trước khi tin: `python scripts/bench_client.py --llm-url http://127.0.0.1:8080`

---

## 3. Kiểm máy trước khi chạy thật

```bash
make preflight          # nhanh
make preflight-full     # kèm cả bộ test
```

Mỗi mục hỏng in kèm **lệnh sửa**. Mục quan trọng nhất không phải "server sống
chưa" mà **"`json_schema` có RÀNG BUỘC thật không"** — nó hỏi model một enum chỉ
nhận đúng chuỗi bịa `XYZZY`. Trả đúng nghĩa là grammar đang chạy thật.

Vì sao cần: `response_format` **được nhận nhưng không ép**, còn `json_schema`
thì có. Cắm nhầm thì ván vẫn chạy, chỉ là mọi ràng buộc schema đều thành trang
trí.

---

## 4. Mở cho người khác vào chơi

### Bước 1 — dựng server ván

```bash
make serve      # uvicorn cổng 8000
```

Server này **không gọi model**. Nó chỉ mô phỏng thế giới và phát việc; mọi lời
gọi model đến từ client. Nên chạy nó cùng máy với client là chuyện bình thường.

### Bước 2 — kiểm cửa TRƯỚC khi phơi ra ngoài

```bash
make hostile
```

Phải ra `CỬA ĐÃ ĐÓNG`. Đây là thứ [N-11](tasks/N-11-phoi-internet.md) bắt chạy
**trước**, không phải sau.

### Bước 3 — mở đường

```bash
ngrok config add-authtoken <token-của-bạn>    # tự tay, một lần
make expose NGROK_URL=https://<tên-miền>.ngrok-free.dev
```

**Cổng 8000, không phải 80.** Trang ngrok gợi ý `ngrok http 80` và đó là chỗ sai
đầu tiên ai cũng mắc — tunnel lên nhưng trỏ vào chỗ trống, trang báo *"We can't
find your endpoint"*.

Rồi **chạy lại bài kiểm cửa với URL công khai** — TLS và proxy có thể đổi hành vi:

```bash
python scripts/hostile_client.py --server https://<tên-miền>.ngrok-free.dev
```

### Bước 4 — người khác vào

```bash
python client/genesis_client.py \
  --server https://<tên-miền>.ngrok-free.dev \
  --model-url http://localhost:8080 \
  --name "Kiến Lửa" --brain-tier 4 --pop 2
```

`--model-url` là llama-server **của họ**, trên máy họ. Server của bạn không gọi
model hộ ai — nên mười người vào chơi là mười GPU khác gánh.

**Vào giữa ván thì phải chờ.** Sinh vật ra đời ở pha SEEDING, nên loài đăng ký
lúc ván đang chạy sẽ xếp hàng tới ván sau. Client in ra `XẾP HÀNG chờ ván sau`.

### Chọn `brain-tier` thế nào

Ngân sách trait là **12 điểm cho 6 chỉ số**. Bạn chọn `brain`, server chia ngẫu
nhiên `12 − brain` cho năm chỉ số còn lại. Nên `brain=5` nghĩa là giáp mỏng,
chậm, mắt kém, bụng nhỏ.

| brain | được gì | mất gì |
|---|---|---|
| 0–1 | thân thể khoẻ | 5 loại luật, 0 điều kiện, sổ 1 ô |
| 2–3 | cân bằng | 8 loại luật, 1 điều kiện |
| 4–5 | nói được `ADJACENT`, `PHASE_ENTER`, 2 điều kiện, sổ nhiều ô | thân thể yếu |

Không ai xác minh model bạn khai, và cũng không cần: **khai láo không lợi gì**
vì ngân sách tự thực thi.

---

## 5. Xem ván

```bash
make serve
```

Rồi mở [web/watch.html](../web/watch.html) (2D) hoặc
[web/watch3d.html](../web/watch3d.html) (3D, three.js đã vendor sẵn trong repo).

Muốn hình 3D thật thay cho khối hộp:

```bash
export MESHY_API_KEY=...
python scripts/mesh_export.py --creatures 20        # xem trước, KHÔNG gọi mạng
python scripts/mesh_export.py --creatures 20 --send # gọi thật, tốn tiền
```

35 mô tả tĩnh (5 địa hình, 4 quả + xác, 5 bản đồ) sinh một lần dùng mãi. Mesh
sinh vật khoá theo vector trait, nên hai con cùng chỉ số dùng chung một hình.

---

## 6. Đọc kết quả

```bash
python -m genesis.score runs/van1.jsonl runs/van1.truth.json
```

| cột | nghĩa |
|---|---|
| `match` | luật phát biểu khớp luật thật bao nhiêu, 0–1 |
| `found` | có vượt ngưỡng và **giữ tới cuối ván** không |
| `t_discover` | lượt thứ mấy thì khớp |
| `R_i` | điểm cho luật ấy, đã tính cả tốc độ |

`found` đòi mục sổ **còn tới cuối ván**: đoán bừa ở lượt 30 rồi lượt 40 xoá đi
thì **không tính**.

Ba bảng xếp hạng riêng, không cộng vào nhau — Nhà Khoa Học (tìm ra luật), Kẻ
Sống Sót (sống lâu), Người Đầu Tiên (tìm ra trước nhất).

---

## 7. Khi có gì đó sai

| triệu chứng | thường là |
|---|---|
| model "im lặng", ván vẫn chạy | `-c` chia mỗi slot < 4096 → server trả lỗi HTTP |
| nhiều lượt nghĩ bị bỏ, đúng 20003 ms | hạn chờ quá ngắn cho một đợt đầy |
| `match` = 0 khắp nơi | chạy `scripts/fake_model_server.py --cheat-seed N` — nếu vẫn 0 thì lỗi ở bộ chấm |
| ngrok báo `ERR_NGROK_3200` | mới `add-authtoken` chứ chưa `make expose` |
| `We can't find your endpoint` | ngrok trỏ cổng 80, server ở 8000 |
| client in `0 cá thể` | vào giữa ván, đang xếp hàng — bình thường |

Chẩn đoán `match = 0` **theo thứ tự**, đừng đổi model trước:
sổ tay nghèo → luật hiếm kích hoạt → từ vựng quá rộng.
Lý do: [B-10 §4](tasks/B-10-score.md).

---

## 8. Đọc tiếp

| muốn gì | đọc |
|---|---|
| hiểu ý tưởng | [03-LUAT-AN-V5](03-LUAT-AN-V5.md) |
| cắm máy vào chơi | [04-THE-GIOI-MO](04-THE-GIOI-MO.md) |
| chi tiết giao thức HTTP | [05-GIAO-THUC](05-GIAO-THUC.md) |
| chạy trên Windows | [CHAY-TREN-WINDOWS](CHAY-TREN-WINDOWS.md) |
| triển khai server | [deploy/README](../deploy/README.md) |
| việc còn lại | [01-STATUS](01-STATUS.md) |

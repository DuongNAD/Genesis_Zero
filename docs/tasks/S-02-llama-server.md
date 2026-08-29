# S-02 · Build llama.cpp, một model, xác minh `json_schema`

| | |
|---|---|
| **Track** | Setup |
| **Phụ thuộc** | — |
| **Chặn** | B-03 |
| **File** | `scripts/serve_L2.sh`, `scripts/check_schema.py` |
| **Ước lượng** | ~30 dòng · 1–3 giờ (phần lớn là chờ build và tải) |
| **Giao cho model rẻ?** | ⚠️ script giao được, đọc lỗi CUDA thì tự |
| **Tài liệu gốc** | v4 Bước 0.2 |

## 1. Mục tiêu
Biết **hôm nay** rằng build CUDA có chạy không và `json_schema` có ép được cấu trúc không. v4 nói thẳng: nếu build hỏng thì bạn cần biết ngay, không phải sau ba tuần.

## 2. Đầu vào đã có
Không có gì. Chạy song song với S-01.

## 3. Việc phải làm
1. Build `llama.cpp` với CUDA trên PC.
2. Tải **một** model: `Llama-3.1-8B-Instruct-Q4_K_M.gguf` vào `models/`.
3. `scripts/serve_L2.sh` — khởi server, tham số lấy từ biến môi trường có mặc định.
4. `scripts/check_schema.py` — gọi `/completion` 50 lần với một `json_schema` đơn giản, đếm JSON hợp lệ.

## 4. Chữ ký và bất biến
```bash
# scripts/serve_L2.sh
llama-server -m models/Llama-3.1-8B-Instruct-Q4_K_M.gguf \
  -ngl 99 -c "${CTX:-6144}" -np "${SLOTS:-2}" -fa --host 127.0.0.1 --port "${PORT:-8080}"
```
**Bất biến `-c`:** `-c` là **tổng** KV chia cho mọi slot. `CTX` phải là `3072 × SLOTS`. Xem [02 §3](../02-SANDBOX-V4.md).

**Dùng `/completion`, không dùng `/v1/chat/completions`** — chỉ endpoint gốc nhận `id_slot`.

## 5. Bẫy
- Nếu build CUDA hỏng: build CPU trước để không bị chặn, ghi vào [01-STATUS](../01-STATUS.md) là còn nợ, và quay lại sau. Đừng dừng cả dự án ở đây.
- `-fa` (flash attention) không có trên mọi bản build. Hỏng thì bỏ `-fa`, chậm hơn chứ không sai.

## 6. Nghiệm thu
```bash
bash scripts/serve_L2.sh & sleep 20 && curl -sf localhost:8080/health && python scripts/check_schema.py --n 50 --url http://localhost:8080
# in ra: valid_json 50/50, và mỗi lần gọi cùng id_slot thì t_prefill lần 2 < 1/3 lần 1
```


## ✅ Đã chạy thật (2026-08-29)

Model: `Qwen2.5-1.5B-Instruct-Q4_K_M` (1,0 GB), `llama-server` b9430, Metal.

**Điều đầu tiên phải kiểm, và nó không hiển nhiên:** `json_schema` có **thật sự
ràng buộc** hay chỉ là gợi ý? Gửi một schema chỉ nhận đúng một chuỗi bịa:

```bash
curl -s localhost:8080/completion -d '{"prompt":"Trả lời JSON.","n_predict":64,
  "json_schema":{"type":"object","properties":{"goal":{"enum":["XYZZY"]}},
  "required":["goal"]}}' | jq -r .content
# {"goal":"XYZZY"}   <- có hiệu lực. `response_format` thì KHÔNG.
```

Số đo (`scripts/bench_client.py --url http://127.0.0.1:8080 --n 50 --slots 4`):

| | |
|---|---|
| JSON hợp lệ | **49/50** trước khi sửa ngân sách; **50/50** sau |
| prefix cache, **lạnh** | dùng lại 599 token, prefill **158 ms** |
| prefix cache, **nóng** | dùng lại **756/757 token (100%)**, prefill **31 ms** → tỉ lệ **0,20** (ngưỡng 0,34) ✅ |
| 4 lời gọi song song | **2,28×** thời gian một lời gọi (ngưỡng 1,5) ❌ |

**Đo prefill phải lấy từ `timings` của server, không lấy bằng đồng hồ ngoài.**
Với model nhỏ, decode át hết prefill: đo bằng đồng hồ ngoài cho tỉ lệ 0,74 và ta
sẽ kết luận nhầm rằng cache không chạy. Và phải đo **lạnh rồi nóng trên một slot
chưa ai dùng** — đo "lần 1 vs lần 2" của một vòng lặp thì tới lúc ấy slot đã ấm
sẵn, `cache_n` đã cao ngay lần đầu, và tỉ lệ nói về nhiễu.

**Song song không giúp gì trên máy này.** llama.cpp/Metal gần như tuần tự hoá
phần decode, nên thông lượng bị chặn bởi **tổng số lời gọi**, không bởi số tiến
trình. Đây là số liệu quan trọng nhất cho [R-01](R-01-rollout.md): tăng worker không tăng
thông lượng; thứ tăng được là **số máy** — mà đó đúng là hình dạng của chế độ mở
ở [04](../04-THE-GIOI-MO.md).

**Cộng một lỗi trong chính `scripts/serve_L2.sh`:** llama.cpp b9430 đổi `-fa`
thành cờ **có giá trị** (`on|off|auto`). Cờ `-fa` trần của bản cũ nuốt mất tham
số kế tiếp, server chết với một trang usage và không nói gì về nguyên nhân.


## 14B trên máy này: đo được, và nó đắt hơn nhiều so với dự đoán từ số tham số

| | 7B q4 | 14B q4 |
|---|---|---|
| sinh chữ | **~14 tok/s** | **5–6 tok/s** |
| 1 lời gọi (~50 token) | 3,5 s | ~9 s |
| 8 lời gọi song song | 19,9 s | **81,1 s** |
| KV mỗi token | 56 KB | **192 KB** |
| một ván 200 tick | ~1,5 giờ | **~6 giờ** |

Prompt cache vẫn chạy hoàn hảo ở 14B — `timings` báo **nạp đúng 1 token**, phần
còn lại tái dùng. Nút cổ chai thuần là băng thông sinh chữ.

Hai chỗ dễ suy sai:

**KV không tỉ lệ với số tham số.** 14B gấp đôi 7B về tham số nhưng tốn KV **gấp
3,4 lần** mỗi token (48 lớp × 8 đầu KV, so với 28 × 4). Tính `-c` theo "gấp đôi"
là thiếu chỗ.

**Một phép đo lúc máy đang bận là một phép đo sai.** Lần đầu tôi đo 14B trong
lúc một ván đang chạy và ra "31 s một lời gọi, chậm hơn 7B 8,9 lần". Đo lại lúc
máy rảnh: 2,5 lần. Con số đầu suýt thành một kết luận về phần cứng.

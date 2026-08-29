# Chạy Genesis Zero trên Windows

Lõi Python **chạy được nguyên trạng**: không có `os.fork`, không `fcntl`, không
đường dẫn `/tmp` hay `/usr` cứng, mọi thao tác file đi qua `pathlib` và
`encoding="utf-8"`. Chỉ ba thứ phụ thuộc POSIX, và cả ba đều có đường vòng.

| thứ | trên Windows |
|---|---|
| `scripts/serve_L2.sh` | dùng [`scripts/serve_L2.ps1`](../scripts/serve_L2.ps1) |
| `Makefile` | gọi thẳng lệnh Python (bảng dưới) |
| `deploy/systemd/` | không dùng; chạy tay hoặc NSSM/Task Scheduler |

## Cài

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/preflight.py
```

`preflight.py` chạy được trên Windows: nó dùng `shutil.which`, `socket` và
`subprocess`, không lệnh shell nào.

## Thay cho `make`

| `make …` | Windows |
|---|---|
| `make test` | `python -m pytest tests/ -q` |
| `make preflight` | `python scripts/preflight.py` |
| `make serve` | `uvicorn net.server:app --port 8000` |
| `make expose` | `ngrok http 8000 --url https://<tên-miền>.ngrok-free.dev` |
| `make hostile` | `python scripts/hostile_client.py --server http://127.0.0.1:8000` |
| `make site` | `python tools/build_site.py` |
| (dựng model) | `.\scripts\serve_L2.ps1` |

## VRAM: `-c` là TỔNG, không phải mỗi slot

```
-c  =  (token mỗi slot)  ×  (số slot)
```

Token mỗi slot phải **≥ 4096**: prompt giữa ván đo được là 2737–2826 token. Đặt
thấp hơn thì llama-server **trả lỗi HTTP chứ không cắt bớt**, nên triệu chứng là
"model tự dưng im lặng" chứ không phải một lỗi ngữ cảnh đọc được.

Chi phí KV mỗi token khác nhau rất nhiều theo model — **không suy từ số tham số**:

| model | lớp | đầu KV | KV mỗi token |
|---|---|---|---|
| Qwen2.5-7B | 28 | 4 | **56 KB** |
| Qwen2.5-14B | 48 | 8 | **192 KB** |

14B chỉ gấp đôi tham số nhưng tốn KV **gấp 3,4 lần** mỗi token.

### Trên card 16 GB

| model | slot | `-c` | KV | tổng |
|---|---|---|---|---|
| 7B q4 | 8 | 32768 | 1,9 GB | 6,6 GB ✓ |
| 7B q4 | 16 | 65536 | 3,8 GB | 8,5 GB ✓ |
| 7B q4 | 32 | 131072 | 7,5 GB | 12,2 GB ✓ |
| **14B q4** | **6** | **24576** | **4,8 GB** | **13,8 GB ✓** |
| 14B q4 | 8 | 32768 | 6,4 GB | 15,4 GB — sát, dễ OOM |

Số trên chưa kể đệm tính toán và phần Windows giữ lại cho màn hình. Chừa ~1,5 GB.

## Thêm slot ≠ thêm tốc độ tương ứng

Đo trên máy M5 (chưa đo trên CUDA):

| lời gọi song song | tổng | thông lượng |
|---|---|---|
| 1 | 3,5 s | 0,29 lời/s |
| 8 | 19,9 s | 0,40 lời/s |
| 15 | 32,0 s | 0,47 lời/s |

Từ 1 lên 15 chỉ nhanh hơn **1,6 lần**. GPU là nút cổ chai, không phải số slot.
Đo lại trên máy của bạn trước khi tin bảng này:

```powershell
python scripts/bench_client.py --llm-url http://127.0.0.1:8080
```

Code tự dò `/props.total_slots` nên đổi `-np` là nó theo, không phải sửa gì.

## Nhiều người chơi thì KHÔNG cần thêm slot

**Mỗi người chơi chạy model của chính họ.** Server Genesis gửi đi `user_block` +
`json_schema` rồi nhận `decision` về — nó không gọi model hộ ai.

```toml
server    = "https://ván-của-bạn.ngrok-free.dev"   # server ván
model_url = "http://localhost:8080"                # llama-server của HỌ
```

Số slot chỉ giới hạn sinh vật **bạn tự chạy cục bộ**. Mười máy vào chơi là mười
GPU khác gánh. Giới hạn người chơi nằm ở [N-11](tasks/N-11-phoi-internet.md):
5 join/giờ mỗi IP, 120 quyết định/phút mỗi token.

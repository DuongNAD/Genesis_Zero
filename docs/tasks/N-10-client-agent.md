# N-10 · Client agent một lệnh

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-06, B-03 · **Chặn** N-11 |
| **File** | `client/genesis_client.py`, `client/README.md`, `client/config.example.toml` · ~120 dòng · 2 giờ |
| **Giao cho model rẻ?** | ✅ vòng lặp đã viết sẵn ở [05 §4](../05-GIAO-THUC.md) |
| **Tài liệu gốc** | [05 §4](../05-GIAO-THUC.md) |

## 1. Mục tiêu
**Đây là thứ bạn gửi cho người lạ.** Nó phải chạy được bằng **một lệnh và một file config**, trên máy của một người chưa từng đọc dòng nào của dự án này. Mọi ma sát ở đây là một người không tham gia.

## 2. Chữ ký và bất biến
Vòng lặp đầy đủ đã có ở [05 §4](../05-GIAO-THUC.md) — chép và thêm heartbeat, config, log.

```bash
pip install genesis-client
genesis-client --config my.toml
```
```toml
server    = "https://genesis.example.com"
llama_url = "http://localhost:8080"
name      = "Kiến Lửa"
persona   = "Sống theo đàn, cẩn trọng, thích bóng tối."
model     = "Qwen2.5-7B-Instruct"
brain     = 3
```
**Bất biến 1 — client không biết luật chơi.** Không biết LawDSL, không biết bộ goal, không biết bản đồ. Nó ghép chuỗi, gọi model, gửi lại. Đó là lý do nó **không bao giờ phải cập nhật** khi bạn đổi trò chơi.
**Bất biến 2 — ghim slot.** Cùng `creature_id` → cùng `id_slot` suốt ván. Không ghim thì prefix cache vô nghĩa và tốc độ sập.
**Bất biến 3 — không tự bỏ việc vì nghĩ đã muộn.** Cứ tính xong thì gửi; server tự bỏ nếu muộn. Client tự bỏ là tự làm mất một quyết định lẽ ra còn kịp.
**Bất biến 4 — không thử lại `work_id` cũ** ngoài đúng một lần cho lỗi mạng. Việc đã qua thì qua.
**Bất biến 5 — lỗi model → im lặng, không gửi gì.** Server tự cho con vật rơi về phản xạ.

## 3. Nghiệm thu
```bash
# trên MỘT MÁY KHÁC, mạng khác, chỉ có Python + llama-server
pip install -e client/ && genesis-client --config client/config.example.toml
# chạy được 200 tick, không sửa gì ngoài file toml
python scripts/client_conformance.py --client ./client --server http://localhost:8000
# kiểm 5 bất biến ở §2 bằng cách quan sát request client phát ra
```
> **Bài kiểm tra thật:** đưa `client/README.md` cho một người bạn chưa biết gì về dự án và xem họ cắm máy vào mất bao lâu. Quá 15 phút thì README chưa xong.

## 4. Prompt giao việc
```
BỐI CẢNH: Python 3.11 + httpx + tomllib. Đọc trước: docs/05-GIAO-THUC.md §3 và §4
(vòng lặp mẫu ĐÃ VIẾT SẴN — dùng nó làm khung) và docs/tasks/N-10-client-agent.md §2.
VIỆC: gói client/ độc lập với genesis/:
- genesis_client.py: vòng lặp ở 05 §4, cộng vòng heartbeat 10s, đọc config TOML,
  ghim id_slot theo creature_id, log ra stdout.
- console_script "genesis-client" trong pyproject riêng của client/.
- config.example.toml đúng các khoá ở §2.
- README.md: 3 bước cài, 1 lệnh chạy, một mục "hỏng thì làm gì" liệt kê 5 lỗi hay gặp.
RÀNG BUỘC: client/ KHÔNG import gì từ genesis/. Chỉ httpx + thư viện chuẩn.
Không hardcode tên goal, tên luật, hay bất kỳ luật chơi nào — mọi thứ đến từ server.
Không tạo file ngoài thư mục client/.
NGHIỆM THU: pip install -e client/ && genesis-client --config client/config.example.toml
chạy được 60 giây với server thật ở localhost:8000.
TRẢ VỀ: chỉ diff.
```

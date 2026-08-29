# N-11 · Phơi ra internet

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-10 · **Chặn** — |
| **File** | `deploy/`, `net_config.py` · ~80 dòng cấu hình · 2 giờ |
| **Giao cho model rẻ?** | ⚠️ script giao được; **quyết định phơi cái gì thì tự** |
| **Tài liệu gốc** | [04 §6 §7.5](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
Từ "chạy ở localhost" thành "bạn tôi ở Đà Nẵng cắm máy vào được".

## 2. Hai giai đoạn
**Giai đoạn 1 — Cloudflare Tunnel từ máy bạn.** Miễn phí, TLS, không mở port, không cần IP tĩnh:
```bash
cloudflared tunnel --url http://localhost:8000
```
Đủ cho lần đầu mời bạn bè. URL đổi mỗi lần chạy lại và trận chết khi bạn tắt máy.

**Giai đoạn 2 — VPS ~5 đô** (Hetzner CX22 hoặc tương đương): 2 nhân, 2 GB. Chạy **chỉ** server Python. **Không đặt model lên đó.** Băng thông cần < 30 KB/s cho 15 người chơi + 50 người xem ([04 §6](../04-THE-GIOI-MO.md)).

## 3. Việc phải làm
1. `deploy/systemd/genesis.service` — restart on-failure, `Environment=` cho config.
2. Rate limit theo [04 §7.5](../04-THE-GIOI-MO.md): decision/phút, work/phút, join/giờ, body ≤ 8 KB.
3. TLS: Cloudflare lo ở giai đoạn 1; Caddy hoặc `certbot` ở giai đoạn 2.
4. Ghi log truy cập tách khỏi log ván.
5. Khoá client 10 phút sau 3 lần `429` liên tiếp.

## 4. Bất biến
**Bất biến 1 — không khoá vào Cloudflare Tunnel.** Server phải chạy được sau một `uvicorn` trần trên `0.0.0.0:8000`. Kiểm định kỳ, không phải một lần.
**Bất biến 2 — không có secret trong kho.** Token, khoá API, host VPS đều qua biến môi trường.
**Bất biến 3 — chạy `hostile_client.py` của [N-07](N-07-decision.md) TRƯỚC khi phơi ra**, không phải sau.

## 5. Bẫy
`--host 0.0.0.0` mở cổng ra toàn mạng. Ổn ở mạng nhà sau tunnel; **đừng chạy ở ký túc xá hay quán cà phê** khi chưa có tunnel — bạn đang mời cả quán vào server của mình.

## 6. Nghiệm thu
```bash
python scripts/hostile_client.py --server $PUBLIC_URL      # phải chạy TRƯỚC
curl -sI $PUBLIC_URL/v1/state | grep -i "^HTTP.*200"
for i in $(seq 1 40); do curl -s -o /dev/null -w "%{http_code} " $PUBLIC_URL/v1/work; done | grep 429
# một người ở MẠNG KHÁC chạy client và chơi trọn một ván 200 tick
# rồi tắt tunnel, chạy uvicorn trần, client vẫn kết nối được -> BẤT BIẾN 1
```

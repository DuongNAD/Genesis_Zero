# Phơi Genesis Zero ra internet (N-11)

Hai giai đoạn, và **đừng nhảy cóc**.

## Giai đoạn 1 — ngrok từ máy bạn (khuyến nghị)

Miễn phí, có TLS, không mở cổng, không cần IP tĩnh — và gói free của ngrok cho
**một tên miền tĩnh**, nên URL **không đổi** giữa các lần chạy. Đó là khác biệt
đáng kể: người chơi lưu link một lần rồi dùng mãi, thay vì phải hỏi lại mỗi ván.

```bash
brew install ngrok
ngrok config add-authtoken <token-của-bạn>      # TỰ TAY chạy — đừng để token vào kho
make serve                                       # cửa sổ 1: uvicorn cổng 8000
make expose                                      # cửa sổ 2: ngrok trỏ vào 8000
```

`make expose` chạy `ngrok http 8000 --url https://<tên-miền>.ngrok-free.dev`.
**Chú ý cổng:** trang ngrok gợi ý `ngrok http 80`, nhưng server Genesis nghe ở
**8000** — dùng `80` thì ngrok trỏ vào một chỗ trống và trang báo *"We can't find
your endpoint"*.

Trước khi gửi link cho ai, chạy bài kiểm cửa (xem mục dưới) **với URL công khai**.

### Cloudflare Tunnel — phương án thay thế

```bash
cloudflared tunnel --url http://localhost:8000
```

Không cần tài khoản, nhưng URL **đổi mỗi lần chạy lại**.

## Giai đoạn 2 — một VPS ~5 đô

Hetzner CX22 hoặc tương đương: 2 nhân, 2 GB.

```bash
sudo cp deploy/systemd/genesis.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now genesis
```

**Không đặt model lên VPS.** Máy này chỉ chạy server Python; model chạy ở máy của
từng người chơi. Đó là cả kiến trúc: server giữ thế giới, client giữ trí tuệ.

## Trước khi phơi ra — theo đúng thứ tự này

```bash
python scripts/hostile_client.py --server http://localhost:8000
# và LẶP LẠI với URL công khai sau khi bật tunnel:
python scripts/hostile_client.py --server https://<tên-miền>.ngrok-free.dev
```

Nó phải xanh **trước**, không phải sau. Bài kiểm này gửi những thứ mà một client
tử tế không bao giờ gửi: body khổng lồ, token của người khác, `work_id` bịa,
quyết định gửi lại nhiều lần, và ký tự điều khiển trong mọi trường chuỗi.

## Bất biến

1. **Không khoá vào một nhà cung cấp tunnel nào.** Server phải chạy được sau một `uvicorn`
   trần trên `0.0.0.0:8000`. Kiểm định kỳ, không phải một lần — một phụ thuộc
   ngầm vào header của tunnel sẽ chỉ lộ ra vào ngày bạn cần đổi nhà cung cấp.
2. **Không có secret trong kho.** Token, khoá API, host VPS đều qua
   `EnvironmentFile`, `chmod 600`, không commit.
3. **Trần chống lạm dụng bật sẵn** (`net/ratelimit.py`): join 5/giờ mỗi **IP**,
   decision và work 120/phút mỗi **token**, body ≤ 8 KB, và ba lần `429` liên
   tiếp thì khoá 10 phút.

## Ai cũng vào được — đó là chủ ý, nhưng hãy biết rõ

`POST /v1/join` **không cần auth**: bất cứ ai có link đều tạo được một loài. Đó
là thiết kế của chế độ mở ([04 §3](../docs/04-THE-GIOI-MO.md)) — sảnh phải chờ
xét duyệt là cách nhanh nhất để một dự án cộng đồng chết trong tuần đầu. Cái
chặn lạm dụng là **ngân sách**, không phải cổng: 5 join/giờ mỗi IP, 120
decision/phút mỗi token, body ≤ 8 KB, ba lần `429` liên tiếp thì khoá 10 phút,
và tối đa 4 kết nối long-poll giữ cùng lúc mỗi token.

Nếu bạn chỉ muốn thử với bạn bè thì cứ gửi link; muốn đóng lại thì tắt `ngrok`.

## Bẫy

`--host 0.0.0.0` mở cổng ra **toàn mạng**. Ổn ở mạng nhà sau tunnel; **đừng chạy
ở ký túc xá hay quán cà phê** khi chưa có tunnel — bạn đang mời cả quán vào
server của mình.

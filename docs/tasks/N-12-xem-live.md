# N-12 · Trang xem live và bảng xếp hạng

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-08, L-07 · **Chặn** — |
| **File** | `net/routes_spectate.py`, `web/` · ~200 dòng · 3 giờ |
| **Giao cho model rẻ?** | ✅ |
| **Tài liệu gốc** | [05 §3.7 §3.8](../05-GIAO-THUC.md), [04 §8](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
**Đây mới là thứ khiến người ta muốn cắm máy vào.** Và nó gần như miễn phí — dữ liệu đã có sẵn trong log.

## 2. Chữ ký và bất biến
Khung WebSocket mỗi tick ở [05 §3.8](../05-GIAO-THUC.md).

**Bất biến 1 — không bao giờ chứa luật ẩn trước `REVEAL`.** Sự kiện `LAW_FIRED` gửi đi với `"law": "?"`. Kiểm bằng **test tự động**, không bằng kỷ luật.
**Bất biến 2 — `"law":"?"` là cố ý.** Người xem **thấy có gì đó vừa xảy ra** mà không biết là gì. Đó chính là trải nghiệm của sinh vật trong ván, và nó làm người xem cũng chơi trò đoán luật.
**Bất biến 3 — vẽ đồ thị "ai nghe được ai"** ([02 §5](../02-SANDBOX-V4.md)): đường mảnh nối các con trong tầm nghe của nhau, nhấp nháy khi có `SPEAK`. Nó làm **bất đối xứng thông tin hiện ra bằng mắt** — thứ mà toàn bộ thiết kế giao tiếp xoay quanh, và là cảnh quay đắt giá nhất của dự án.
**Bất biến 4 — hình sinh vật suy từ trait**, không từ cỡ model ([02 §5](../02-SANDBOX-V4.md) cấm kỵ).
**Bất biến 5 — phát lại sau `REVEAL`** với `law` điền đầy đủ. Cùng luồng, khác nội dung.

## 3. Nghiệm thu
```bash
pytest tests/test_no_law_leak.py -q
# ★ mở WebSocket trong pha RUNNING, thu 200 khung, assert KHÔNG khung nào chứa
#   law_id, tên effect, hay bất cứ gì khác "?" ở trường law
open $PUBLIC_URL/watch     # nhìn bằng mắt: con hoang dã viền đứt, con chết mờ,
                           # đồ thị nghe nhấp nháy khi có SPEAK
curl -s $PUBLIC_URL/v1/leaderboard?season=2026s3 | jq -e '.rows[0].mean_t_discover'
```

## 4. Prompt giao việc
```
BỐI CẢNH: FastAPI WebSocket + HTML/JS thuần (không framework, không CDN).
Đọc trước: docs/05-GIAO-THUC.md §3.7 §3.8 (hình dạng khung CHÍNH XÁC) và
docs/02-SANDBOX-V4.md §5 (bảng ánh xạ trait -> hình, quy tắc màu).
VIỆC:
- net/routes_spectate.py: WS /v1/spectate đẩy một khung mỗi tick đúng hình dạng 05 §3.8.
  Sự kiện LAW_FIRED PHẢI gửi với "law": "?" khi phase != REVEAL.
  GET /v1/leaderboard?season= theo 05 §3.7.
- web/watch.html + web/watch.js: canvas 2D, vẽ lưới, vẽ sinh vật bằng primitive suy từ
  trait theo 02 §5, màu hue = md5(species_id)%360, độ sáng theo energy/energy_max.
  Con chết vẽ mờ, con feral viền đứt. Vẽ đường mảnh giữa các con trong tầm nghe của nhau,
  nhấp nháy 300ms khi có sự kiện SPEAK.
- tests/test_no_law_leak.py: mở WS ở pha RUNNING, thu 200 khung, assert không khung nào
  chứa chuỗi khớp r"law_id|POISON|DAMAGE|HEAL|SPREAD" và mọi trường law đều là "?".
RÀNG BUỘC: web/ không dùng CDN, không framework, không build step — mở file là chạy.
Kích thước sinh vật KHÔNG được phụ thuộc cỡ model. Không tạo/sửa file ngoài danh sách.
NGHIỆM THU: pytest tests/test_no_law_leak.py -q
TRẢ VỀ: chỉ diff.
```

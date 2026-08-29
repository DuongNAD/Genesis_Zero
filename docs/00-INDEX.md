# 00 · Bản đồ tài liệu

> **00 Bản đồ** · [01 Trạng thái](01-STATUS.md) · [02 Sandbox](02-SANDBOX-V4.md) · [03 Luật ẩn](03-LUAT-AN-V5.md) · [04 Thế giới mở](04-THE-GIOI-MO.md) · [05 Giao thức](05-GIAO-THUC.md) · [06 Công việc](06-CONG-VIEC.md) · [07 Giao việc](07-GIAO-VIEC-CHO-MODEL.md) · [08 Từ điển](08-TU-DIEN.md)

## Ba tầng tài liệu

```
Ý TƯỞNG        03-LUAT-AN-V5   ── vì sao dự án này tồn tại, thiết kế cốt lõi
   │           02-SANDBOX-V4   ── tầng nền mà 03 xây lên trên
   │           04-THE-GIOI-MO  ── nhiều máy qua internet
   ▼
ĐẶC TẢ         05-GIAO-THUC    ── API, schema, mã lỗi. Không có ý kiến, chỉ có sự thật.
   │           08-TU-DIEN      ── mỗi thuật ngữ một nghĩa, dùng chung mọi nơi
   ▼
THI CÔNG       01-STATUS       ── ★ hôm nay đang ở đâu
               06-CONG-VIEC    ── ★ làm gì tiếp, theo thứ tự nào
               07-GIAO-VIEC…   ── việc nào giao được cho model rẻ
               tasks/*.md      ── từng việc một, tự chứa đủ thông tin
```

**Quy tắc vàng:** một sự thật sống ở **đúng một** tài liệu. Chỗ khác thì **liên kết tới**, không chép lại. Chép lại là cách chắc chắn nhất để sáu tháng sau có hai phiên bản mâu thuẫn và không ai biết cái nào đúng.

| Sự thật | Sống ở |
|---|---|
| Tiến độ, cái gì xong | [01-STATUS](01-STATUS.md) — **không nơi nào khác** |
| Hằng số | `config.py`, `law_config.py` — tài liệu chỉ trỏ tới, không chép số |
| Hình dạng API | [05-GIAO-THUC](05-GIAO-THUC.md) |
| Nghĩa của thuật ngữ | [08-TU-DIEN](08-TU-DIEN.md) |
| Vì sao chọn thế này | 02 / 03 / 04 |
| Cách làm một việc cụ thể | `tasks/<mã>.md` |

## Quy ước

**Phiếu việc** đặt tên `<TRACK>-<số>-<slug>.md`:

| Track | Nghĩa | Mã |
|---|---|---|
| Setup | môi trường, model, công cụ | `S-01` … |
| World | sandbox 2D (v4 M0+M1) | `W-01` … |
| Law | động cơ luật ẩn + verifier (v5 M1.5) | `L-01` … |
| Brain | tầng LLM, prompt, sổ luật | `B-01` … |
| Net | thế giới mở qua internet | `N-01` … |
| eXperiment | thí nghiệm, phân tích, báo cáo | `X-01` … |
| Train | vòng huấn luyện RL (M7) | `R-01` … |

**Mỗi phiếu việc có đúng 8 mục.** Không thêm, không bớt — vì phiếu được dán thẳng cho một agent làm, và định dạng ổn định thì kết quả ổn định.

1. Bảng đầu (track, phụ thuộc, file, ước lượng, giao được không)
2. Mục tiêu — một đoạn, vì sao việc này tồn tại
3. Đầu vào đã có — cái gì sẵn rồi
4. Việc phải làm — danh sách đánh số
5. Chữ ký và bất biến — code, không phải văn xuôi
6. Bẫy — chỉ ghi khi có thật
7. Nghiệm thu — **lệnh chạy được**, không phải cảm nhận
8. Prompt giao việc — chỉ có khi phiếu được đánh dấu giao được

**Đánh dấu trạng thái** chỉ dùng 4 ký hiệu, và chỉ ở [01-STATUS](01-STATUS.md):

`⬜ chưa bắt đầu` · `🟨 đang làm` · `✅ xong và đã nghiệm thu` · `🚫 bị chặn`

> "Xong" nghĩa là **lệnh nghiệm thu ở mục 7 đã chạy và đã pass**. Không có nghĩa là "code viết xong rồi". Phân biệt này là toàn bộ giá trị của cột trạng thái.
- [Chạy trên Windows](CHAY-TREN-WINDOWS.md) — PowerShell, VRAM, thay cho make
- [Hướng dẫn sử dụng](HUONG-DAN.md) — cài, chạy, mở cho người khác vào

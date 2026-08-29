# S-05 · `make preflight` — kiểm trước khi chạy thật

| | |
|---|---|
| **Track** | Sàn · **Phụ thuộc** [S-02](S-02-llama-server.md), [N-11](N-11-chong-lam-dung.md) |
| **File** | `scripts/preflight.py` · ~200 dòng |
| **Giao cho model rẻ?** | ⚠️ khung giao được; **mục "json_schema có ràng buộc không" tự viết** |

## 1. Mục tiêu
Một lệnh trả lời đúng một câu hỏi: **máy này chạy được một ván thật chưa?**

```bash
make preflight          # nhanh
make preflight-full     # kèm cả bộ test
```

Mỗi mục hỏng in kèm **lệnh sửa**. Đó là chủ ý: một bản kiểm chỉ nói "hỏng" bắt
người đọc đi tra lại chính thứ mà bản kiểm vừa biết.

## 2. Mục quan trọng nhất: grammar có ép thật không

Không hỏi "server sống chưa" — hỏi **`json_schema` có RÀNG BUỘC không**, bằng
một enum chỉ nhận đúng một chuỗi bịa:

```python
{"x": {"type": "string", "enum": ["XYZZY"]}}
```

Model không thể đoán trúng `XYZZY`. Trả đúng nghĩa là GBNF đang chạy thật.

Vì sao cần: `response_format` **được nhận nhưng không ép**, còn `json_schema`
thì có. Hai đường trông giống hệt nhau ở lớp HTTP — cùng 200, cùng JSON trả về
— và khác nhau ở chỗ một bên cho model viết gì cũng được. Cắm nhầm thì ván vẫn
chạy, chỉ là mọi ràng buộc schema mà [B-01](B-01-schema.md) dựng lên đều thành
trang trí, và triệu chứng là "model hay trả sai định dạng".

## 3. Các mục khác
Python ≥ 3.11 · thư viện bắt buộc/tuỳ chọn · `build_match(1)` chạy được mà
không cần model hay mạng · trang xem 2D/3D và three.js đã vendor · đĩa trống ·
server Genesis cổng 8000 · ngrok đã có authtoken · bộ test.

## 4. Ranh giới
`preflight` **không sửa gì**. Nó đọc và báo. Một script kiểm mà tự cài đặt thì
lần sau người ta chạy nó thay cho việc đọc lỗi.

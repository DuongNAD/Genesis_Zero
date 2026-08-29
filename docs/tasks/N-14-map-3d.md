# N-14 · Trang xem 3D

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-12, W-15, N-13 · **Chặn** — |
| **File** | `web/watch3d.html`, `web/watch3d.js`, `web/vendor/` · ~290 dòng · 3 giờ |
| **Giao cho model rẻ?** | ⚠️ dựng cảnh giao được; **ranh giới "cái gì đến từ khung" thì tự** |
| **Tài liệu gốc** | [02 §5](../02-SANDBOX-V4.md), [05 §3.8](../05-GIAO-THUC.md), [N-13](N-13-mesh-3d.md) |

## 1. Mục tiêu
Sinh vật đã có mesh 3D ([N-13](N-13-mesh-3d.md)) thì thế giới cũng phải là 3D —
một con vật 3D đứng trên một ô vuông phẳng trông sai hơn là cả hai đều phẳng.

## 2. Bất biến
**Bất biến 1 — mọi thứ đến TỪ KHUNG, không từ bảng chép cứng trong JS.**
Ba thứ dựng nên cảnh: địa hình (`frame.terrain`), sinh vật (`frame.creatures[].tr`
— trait **hiện tại**), và đồ thị nghe (`frame.events[].hear`, do server tính).
Bảng chép cứng là bảng sẽ lệch: trait dịch giữa ván, và loài do người lạ tạo ra
lúc chạy thì trang này không thể biết trước. [N-12](N-12-xem-live.md) đã mắc đúng
lỗi đó một lần.

**Bất biến 2 — địa hình gửi MỘT LẦN mỗi ván.** 24×24 là ~3 KB; gửi mỗi tick thì
nó chiếm gần hết băng thông luồng xem. Gửi ở tick 0 dưới dạng chuỗi một ký tự mỗi
ô (`P W B R F`), và `spectate` vá nó vào khung **đầu tiên** của mỗi người xem mới
— người vào giữa ván vẫn phải thấy bản đồ.

**Bất biến 3 — không CDN, không build step.** `three.js` và `GLTFLoader` nằm
trong `web/vendor/` (bản UMD r128, chạy được cả từ `file://`). Server mount
`web/` ở `/watch` để dùng qua HTTP.

**Bất biến 4 — cấm kỵ cũ còn nguyên** ([02 §5](../02-SANDBOX-V4.md)): kích thước
sinh vật **không** phụ thuộc cỡ model.

**Bất biến 5 — luật kích hoạt chỉ là một tia sáng, KHÔNG kèm chữ.** Trước REVEAL
thì người xem cũng đang đoán như chính lũ sinh vật; đó là chủ ý, không phải hạn chế.

## 3. Nghiệm thu
```bash
uvicorn net.server:app --port 8000   # rồi mở http://localhost:8000/watch/watch3d.html
pytest tests/test_spectate.py -q
```

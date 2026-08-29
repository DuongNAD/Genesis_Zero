# N-13 · Hình 3D sinh bằng MeshyAI

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** N-05, N-12 · **Chặn** — |
| **File** | `net/mesh.py`, `web/watch3d.js`, `net_config.py` · ~220 dòng · 4 giờ |
| **Giao cho model rẻ?** | ⚠️ gọi API + hàng đợi + loader giao được; **khoá cache và ba bất biến thì tự quyết** |
| **Tài liệu gốc** | [02 §5](../02-SANDBOX-V4.md), [05 §3.1](../05-GIAO-THUC.md), [N-12](N-12-xem-live.md) |

## 1. Mục tiêu
Ở chế độ mở, loài do người lạ tạo ra **lúc chạy** — không thể vẽ sprite trước cho loài chưa tồn tại. [02 §5](../02-SANDBOX-V4.md) giải bằng primitive procedural. MeshyAI giải hay hơn: sinh mesh 3D thật từ chính vector trait, một lần, rồi dùng lại mãi.

Nhưng nó chỉ đúng nếu **giữ nguyên bất biến "hình = trait, chỉ trait"**. Sai chỗ đó là mất luôn tính chất đẹp nhất của thiết kế gốc.

## 2. Đầu vào đã có
Khối C (mô tả cơ thể định tính, server sinh từ vector trait) đã có ở [B-02](B-02-prompt.md). **Dùng lại đúng chuỗi đó làm prompt cho Meshy** — đừng viết bộ mô tả thứ hai.

## 3. Việc phải làm
1. `mesh_key(traits) -> str` — băm vector trait, **không** băm `client_id` hay `species_id`.
2. Hàng đợi sinh mesh chạy nền + cache trên đĩa theo `mesh_key`.
3. `/join` trả ngay `mesh_status: "pending" | "ready"` + `mesh_url` khi có.
4. Trait dịch → key mới → sinh nền, **vẫn hiển thị mesh cũ** cho tới khi bản mới xong.
5. `web/watch3d.js`: three.js + glTF loader, rơi về primitive procedural khi chưa có mesh.
6. Quota: mỗi client N lượt sinh/ngày, trần toàn cục M lượt/ngày.

## 4. Chữ ký và bất biến
```python
def mesh_key(traits: Traits) -> str:
    """md5 của 6 trait. KHÔNG có client_id, KHÔNG có species_id."""

async def ensure_mesh(traits: Traits) -> str | None:
    """Trả mesh_url nếu cache có; nếu không, xếp hàng sinh nền và trả None."""

def body_prompt(traits: Traits) -> str:
    """DÙNG LẠI khối C của B-02. Không viết mô tả thứ hai."""
```
**Bất biến 1 — hình = trait, chỉ trait.** Prompt gửi Meshy sinh **hoàn toàn** từ vector trait. Không có `display_name`, không có persona, không có gì do client viết. Vi phạm là mất bất biến gốc *và* mở lại cửa tiêm lệnh mà [04 §7.4](../04-THE-GIOI-MO.md) đã đóng.

**Bất biến 2 — cache theo vector trait.** Hai người chơi có cùng cơ thể **dùng chung một mesh**. Không gian trait nhỏ (tổng 12, 6 chiều, mỗi chiều 0–5) nên sau vài chục ván cache hit gần như luôn, và chi phí có trần. Khoá theo `client_id` là chi phí vô hạn tuyến tính theo số người chơi.

**Bất biến 3 — mesh KHÔNG BAO GIỜ chạm vào sim.** Không import vào `world.py`, không vào log trừ một `mesh_id`, không ảnh hưởng replay. Nó là trình bày thuần. Vi phạm là mất tính tái lập.

**Bất biến 4 — `/join` không được chặn.** Meshy text-to-3D mất **phút**, không phải giây. Trả ngay `pending`; bản vẽ procedural của [N-12](N-12-xem-live.md) phải **luôn** chạy được làm nền, ở mọi thời điểm.

**Bất biến 5 — cấm kỵ cũ còn nguyên.** Kích thước trên màn hình **không được** phụ thuộc cỡ model ([02 §5](../02-SANDBOX-V4.md)). Người chạy 70B được mesh đẹp hơn thì không sao; con vật **to hơn** thì không.

## 5. Bẫy
- **Trait dịch giữa ván.** Đây là lý do bất biến 2 khoá theo trait chứ không theo người. Dịch trait → key mới → sinh nền, giữ mesh cũ tới khi xong. Đừng chặn khung hình để chờ.
- **Trang artifact không fetch được host ngoài** (CSP). Chỉ trang xem live trên server của anh mới gọi được Meshy. Đừng thiết kế phụ thuộc vào việc artifact tải mesh.
- **Trần chi phí phải đo, đừng đoán.** Chạy 100 ván rồi đếm số vector trait **khác nhau** thực sự xuất hiện. Nếu con số đó lớn hơn dự kiến nhiều thì quota ở §3.6 phải siết lại trước khi mở cửa.

## 6. Nghiệm thu
```bash
pytest tests/test_mesh.py -q
# ca: mesh_key KHÔNG đổi khi client_id/species_id đổi mà trait giữ nguyên
#     mesh_key ĐỔI khi một trait dịch một điểm
#     /join lúc cache rỗng -> trả trong < 500 ms với mesh_status "pending"
#     trait dịch -> mesh cũ vẫn được trả về cho tới khi bản mới sẵn sàng
#     quota vượt -> 429, KHÔNG làm hỏng ván
! grep -rn "mesh" genesis/world.py genesis/logio.py && echo "MESH KHÔNG CHẠM SIM OK"
# đo trần chi phí thật
python scripts/mesh_cost_probe.py --matches 100
# in ra số vector trait khác nhau đã gặp -> đó là số lần gọi Meshy tối đa sau warmup
```

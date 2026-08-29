# N-15 · Mô tả 3D — sinh vật, địa hình, quả, bản đồ

| | |
|---|---|
| **Track** | Net · **Phụ thuộc** [N-13](N-13-mesh-3d.md), [W-15](W-15-ban-do.md) · **Chặn** không gì |
| **File** | `genesis/mesh_prompts.py` · `scripts/mesh_export.py` · ~230 dòng |
| **Giao cho model rẻ?** | ⚠️ câu chữ mô tả giao được; **hai ràng buộc dưới đây tự viết** |
| **Tài liệu gốc** | [N-13 §4](N-13-mesh-3d.md) · [04 §6](../04-THE-GIOI-MO.md) |

## 1. Mục tiêu
Mọi thứ trong thế giới có một câu mô tả gửi thẳng được cho MeshyAI, sinh một
lần dùng mãi. 35 mô tả: 5 địa hình, 4 quả + xác, 5 bản đồ, 20 vector trait.

```bash
python scripts/mesh_export.py --creatures 20     # ghi assets/meshy/
python scripts/mesh_export.py --send             # gửi thật (cần MESHY_API_KEY)
```

Không có `--send` thì **không gọi mạng**. Sinh mesh tốn tiền thật, nên gửi phải
là một hành động cố ý — không phải tác dụng phụ của việc chạy thử một script.

## 2. Hai bất biến

**Bất biến 1 — quả khoá theo BỀ MẶT, không theo lớp.**
Bề mặt bị hoán vị mỗi ván ([L-04](L-04-tinh-huong.md)): `FRUIT_A` ván này là
"quả đỏ tròn", ván sau là "quả tím dẹt". Sinh mesh theo **lớp** thì hình quả đổi
màu giữa hai ván, và người xem **đọc được luật ẩn qua hình 3D** — một đường rò
đi vòng qua toàn bộ `_check_no_leak`, vì nó không đi qua prompt. Khoá theo bề
mặt thì bốn mesh dùng được cho mọi ván và không mesh nào biết lớp của mình.

**Bất biến 2 — hình sinh vật là hàm THUẦN của vector trait.**
Đây là bất biến 1 của [N-13](N-13-mesh-3d.md) ("hình = trait, chỉ trait") và
`test_khong_mang_thu_do_client_viet` kiểm nó **bằng chữ ký hàm**: `creature_prompt`
nhận đúng một tham số. Không có chỗ để lọt `display_name` hay `persona` vào.

## 3. Vì sao đây KHÔNG phải "bộ mô tả thứ hai"

Thẻ N-13 dặn thẳng: *"đừng viết bộ mô tả thứ hai"* — hai bộ độc lập thì sẽ có
ngày một con `attack=5` trông tay ngắn.

File này là **cùng một bộ, mở rộng**: phần số lấy nguyên `prompt.body_line`,
phần hình sinh từ CHÍNH sáu con số ấy qua bảng tra. `net/mesh.py:body_prompt`
gọi vào đây, nên tới Meshy vẫn chỉ có một đường.

Bản cũ gửi cho Meshy đúng dòng chỉ số khô:

```
đầu óc 4 · tay 3 · giáp 2 · chân 2 · giác quan 1 · bụng 0.
```

Đúng bất biến, và **Meshy không có gì để dựng từ đó**. Giờ:

```
Sinh vật bốn chân hư cấu, thân đối xứng: sọ lớn phồng rõ đường vân chạy dọc,
chi trước cơ bắp móng cong, vài mảng sừng mỏng ở vai, chân vừa dáng đứng cân,
hai mắt nhỏ không râu, bụng nhỏ gọn. Chỉ số: đầu óc 4 · tay 3 · …
```

## 4. Mô tả bản đồ bám theo cân bằng thật

`map_prompt` đọc tỉ lệ địa hình thẳng từ `MapSpec.seeds`. Gõ tay thì đổi cân
bằng bản đồ xong mô tả 3D vẫn nói con số cũ — và không ai phát hiện, vì không
có gì so hai bên với nhau. `test_mo_ta_ban_do_bam_theo_can_bang_that` khoá lại.

## 5. Nghiệm thu
```bash
python -m pytest tests/test_mesh_prompts.py -q     # 10 mục
python scripts/mesh_export.py --creatures 20
python -c "
import json; rows=json.load(open('assets/meshy/prompts.json'))
assert len(rows)==35
assert not any('FRUIT_' in r['prompt'] for r in rows), 'RÒ LỚP QUẢ'
print('35 mô tả, không rò lớp')"
```

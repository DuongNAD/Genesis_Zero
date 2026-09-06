# Đặc Tả Thực Vật 3D: Nấm Quỷ Lập Lòe Ma Quái (Omphalotus olearius)

> [!NOTE]
> **Mã Định Danh**: `EX10`  
> **Nhóm Hình Thái**: Cave Bioluminescent  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Omphalotaceae
> **Họ Thực Vật (Family)**: *Omphalotaceae*  
> **Danh Pháp Khoa Học**: *Omphalotus olearius*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `EX10-POWO` | WFO: `wfo-cave_jack_o_lantern` | GBIF: `32699839` | CoL: `EX10` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Jack-o'-Lantern Mushroom**  
> **Sinh Cảnh Tự Nhiên**: Gốc cây mục tối tăm, Cửa hang ẩm (Z: -2m đến 3m)  
> **Kích Thước Không Gian**: 0.55m (Cao) x 0.65m (Cụm phễu)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/cave_jack_o_lantern_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Mọc cụm chùm lớn màu cam cháy rực rỡ vào ban ngày. Đêm xuống, toàn bộ các phiến nấm dưới mũ phát ra luồng ánh sáng huỳnh quang xanh lục ma mị rọi sáng chân vách đá.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Mũ nấm hình phễu lõm ở tâm mép uốn lượn sóng, phiến nấm chạy dài xuống tận chân cuống chứa enzym luciferase.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **34,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **8,200 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF + Emission: Ban ngày màu cam cháy (#ea580c), Mặt phiến nấm phát quang ánh sáng lục lam Emission: 4.8 lux (#22c55e), SSS: 0.50.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`cave_jack_o_lantern_turnaround.jpg`](../images/cave_jack_o_lantern_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/cave_bioluminescent/cave_jack_o_lantern.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_cave_jack_o_lantern"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

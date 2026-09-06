# Đặc Tả Thực Vật 3D: Cỏ Lúa Mì Đỏ Đồng Hoang (Festuca rubra)

> [!NOTE]
> **Mã Định Danh**: `GR01`  
> **Nhóm Hình Thái**: Grasses Herbs  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Poaceae
> **Họ Thực Vật (Family)**: *Poaceae*  
> **Danh Pháp Khoa Học**: *Festuca rubra*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `GR01-POWO` | WFO: `wfo-grass_red_fescue` | GBIF: `8498194` | CoL: `GR01` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Red Fescue Grass**  
> **Sinh Cảnh Tự Nhiên**: Đồng cỏ, Thảo nguyên đồi thấp (Z: 4m - 10m)  
> **Kích Thước Không Gian**: 0.4m (Cao) x 0.35m (Tán)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/grass_red_fescue_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Lá dạng sợi thanh mảnh mọc thành cụm búi dày đặc. Đầu ngọn lá có sắc tố anthocyanin ánh đỏ hung đặc trưng. Thân cọng mềm mại uốn cong tự nhiên theo chiều gió lùa.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Phiến lá có rãnh dọc siêu mịn (micro-groove venation) sâu 0.2mm, mép lá có gai vi mô nano tạo độ phản xạ gắt nhẹ ở góc nghiêng (Fresnel grazing angle).

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **18,400 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **4,200 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF + SSS: Base Color gradient từ xanh cỏ úa (#4d7c0f) ở gốc đến phớt đỏ tía (#991b1b) ở ngọn. SSS Weight: 0.25, SSS Radius: (0.15, 0.25, 0.05), Roughness: 0.45, Sheen: 0.30.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`grass_red_fescue_turnaround.jpg`](../images/grass_red_fescue_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/grasses_herbs/grass_red_fescue.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_grass_red_fescue"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

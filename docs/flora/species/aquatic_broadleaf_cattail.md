# Đặc Tả Thực Vật 3D: Cỏ Nến Bồn Bồn Đầm Lầy (Typha latifolia)

> [!NOTE]
> **Mã Định Danh**: `AQ04`  
> **Nhóm Hình Thái**: Aquatic Wetland  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Typhaceae
> **Họ Thực Vật (Family)**: *Typhaceae*  
> **Danh Pháp Khoa Học**: *Typha latifolia*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `AQ04-POWO` | WFO: `wfo-aquatic_broadleaf_cattail` | GBIF: `206009893` | CoL: `AQ04` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Broadleaf Cattail**  
> **Sinh Cảnh Tự Nhiên**: Vũng trũng ngập nước, Bãi đầm lầy ao làng (Z: 4.0m - 5.8m)  
> **Kích Thước Không Gian**: 2.2m (Cao) x 0.65m (Tán)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/aquatic_broadleaf_cattail_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Lá thẳng đứng dạng dải hẹp uốn dẻo dai. Trục hoa vươn cao mang bông hoa hình trụ tròn đặc trưng màu nâu nhung mềm mại như xúc xích nhung mượt mà, đỉnh có cọng nhụy đực.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Bông nến nâu có bề mặt vi lông tơ dày đặc (velvet fuzz), khi chín nứt bung ra hàng vạn hạt tơ trắng bay bổng.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **24,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **5,500 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Bông nến nâu sô-cô-la mịn màng (#451a03, Roughness 0.95, Sheen 0.70), Thân và lá xanh lục oliu dẻo dai (#4d7c0f, SSS 0.30, Roughness 0.35).`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`aquatic_broadleaf_cattail_turnaround.jpg`](../images/aquatic_broadleaf_cattail_turnaround.jpg)
- 🎨 **File Nguồn Blender 3D**: [`aquatic_broadleaf_cattail.blend`](../../../assets/flora/aquatic_wetland/aquatic_broadleaf_cattail.blend)
- 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`aquatic_broadleaf_cattail.glb`](../../../assets/flora/aquatic_wetland/aquatic_broadleaf_cattail.glb)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/aquatic_wetland/aquatic_broadleaf_cattail.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_aquatic_broadleaf_cattail"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

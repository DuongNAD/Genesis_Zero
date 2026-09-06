# Đặc Tả Thực Vật 3D: Cây Thau Thao Cổ Rừng Mưa (Dipterocarpus grandiflorus)

> [!NOTE]
> **Mã Định Danh**: `MG12`  
> **Nhóm Hình Thái**: Canopy Trees  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Dipterocarpaceae
> **Họ Thực Vật (Family)**: *Dipterocarpaceae*  
> **Danh Pháp Khoa Học**: *Dipterocarpus grandiflorus*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `MG12-POWO` | WFO: `wfo-canopy_rainforest_dipterocarp` | GBIF: `105364757` | CoL: `MG12` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Emergent Rainforest Giant**  
> **Sinh Cảnh Tự Nhiên**: Rừng mưa nhiệt đới tầng vượt tán (Z: 2m - 10m)  
> **Kích Thước Không Gian**: 25.0m (Cao) x 15.0m (Tán súp lơ vĩ đại)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/canopy_rainforest_dipterocarp_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Đại thụ tầng vượt tán (emergent layer) vươn cao vượt lên trên thảm rừng chung, thân tròn thẳng tắp như cây cột đình khổng lồ, đỉnh nở tán hình bán cầu như cây súp lơ khổng lồ, quả có 2 cánh dài bay xoay tít như chong chóng khi rụng.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Rễ bạnh tam giác khổng lồ cao 4m mở rộng chân đế, quả 2 cánh mỏng có gân song song xoắn ốc.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **90,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **23,000 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Thân xám trắng loang lổ địa y, Tán lá xanh đậm dày cộm chịu nắng gắt tầng trên cùng Roughness 0.30, SSS 0.36.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`canopy_rainforest_dipterocarp_turnaround.jpg`](../images/canopy_rainforest_dipterocarp_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_rainforest_dipterocarp.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_canopy_rainforest_dipterocarp"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

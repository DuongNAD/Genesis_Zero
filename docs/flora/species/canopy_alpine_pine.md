# Đặc Tả Thực Vật 3D: Thông Núi Tuyết Alpine (Pinus cembra)

> [!NOTE]
> **Mã Định Danh**: `MG02`  
> **Nhóm Hình Thái**: Canopy Trees  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Pinaceae
> **Họ Thực Vật (Family)**: *Pinaceae*  
> **Danh Pháp Khoa Học**: *Pinus cembra*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `MG02-POWO` | WFO: `wfo-canopy_alpine_pine` | GBIF: `178561890` | CoL: `MG02` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Swiss Stone Pine**  
> **Sinh Cảnh Tự Nhiên**: Đỉnh Matterhorn, Vách đá bão tuyết (Z: 12m - 18m)  
> **Kích Thước Không Gian**: 14.2m (Cao) x 7.8m (Tán)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/canopy_alpine_pine_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Thân cây vặn xoắn chịu bão tuyết hàng trăm năm, cành gốc gãy cụt hóa lũa bạc màu. Tán lá chia thành các tầng khiên nón xếp lớp so le đón tuyết rơi.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Lá kim mọc thành chùm 5 lá dài cứng cáp, quả thông tím sẫm hình trứng phủ nhựa thơm, lớp vỏ ngoài tróc vảy dày như mai rùa.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **64,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **16,000 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Vỏ thân nâu xám vảy sừng (#451a03), Lá kim xanh đen ánh lục (#064e3b, SSS 0.22, Roughness 0.40), Nhựa thông trong suốt Clearcoat: 0.80.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`canopy_alpine_pine_turnaround.jpg`](../images/canopy_alpine_pine_turnaround.jpg)
- 🎨 **File Nguồn Blender 3D**: [`canopy_alpine_pine.blend`](../../../assets/flora/canopy_trees/canopy_alpine_pine.blend)
- 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`canopy_alpine_pine.glb`](../../../assets/flora/canopy_trees/canopy_alpine_pine.glb)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_alpine_pine.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_canopy_alpine_pine"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

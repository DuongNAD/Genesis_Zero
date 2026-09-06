# Đặc Tả Thực Vật 3D: Liễu Rủ Đầm Nước Mơ Màng (Salix babylonica)

> [!NOTE]
> **Mã Định Danh**: `TR03`  
> **Nhóm Hình Thái**: Canopy Trees  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Salicaceae
> **Họ Thực Vật (Family)**: *Salicaceae*  
> **Danh Pháp Khoa Học**: *Salix babylonica*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `TR03-POWO` | WFO: `wfo-canopy_weeping_willow` | GBIF: `201185841` | CoL: `TR03` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Weeping Willow**  
> **Sinh Cảnh Tự Nhiên**: Bờ hồ trung tâm, Bến nước lạch sông (Z: 4m - 6m)  
> **Kích Thước Không Gian**: 11.8m (Cao) x 12.5m (Tán rủ)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/canopy_weeping_willow_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Thân gỗ to lớn uốn nghiêng là đà mặt nước, cành chính xòe vòm rộng buông rủ hàng ngàn dải cành mảnh mai mềm mại buông thõng chạm mặt hồ gợn sóng.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Dải cành rủ kết hợp các chuỗi lá hẹp hình mũi mác dài uốn lượn tự do, tạo thành rèm tơ xanh mờ ảo đung đưa theo gió.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **72,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **18,000 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Lá xanh vàng non mềm mại (#65a30d), SSS: 0.48, Vỏ thân nứt nẻ rãnh dọc sâu màu xám tro cổ kính (#475569, Roughness 0.88).`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`canopy_weeping_willow_turnaround.jpg`](../images/canopy_weeping_willow_turnaround.jpg)
- 🎨 **File Nguồn Blender 3D**: [`canopy_weeping_willow.blend`](../../../assets/flora/canopy_trees/canopy_weeping_willow.blend)
- 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`canopy_weeping_willow.glb`](../../../assets/flora/canopy_trees/canopy_weeping_willow.glb)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`generate_willow_realistic.py`](../../../assets/flora/generators/generate_willow_realistic.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_weeping_willow.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_canopy_weeping_willow"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

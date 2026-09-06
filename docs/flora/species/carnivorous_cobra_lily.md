# Đặc Tả Thực Vật 3D: Cây Bắt Mồi Rắn Hổ Mang (Darlingtonia californica)

> [!NOTE]
> **Mã Định Danh**: `EX08`  
> **Nhóm Hình Thái**: Carnivorous Vines  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Sarraceniaceae
> **Họ Thực Vật (Family)**: *Sarraceniaceae*  
> **Danh Pháp Khoa Học**: *Darlingtonia californica*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `EX08-POWO` | WFO: `wfo-carnivorous_cobra_lily` | GBIF: `16527913` | CoL: `EX08` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Cobra Lily**  
> **Sinh Cảnh Tự Nhiên**: Đầm than bùn suối lạnh râm mát (Z: 4m - 9m)  
> **Kích Thước Không Gian**: 0.85m (Cao) x 0.65m (Cụm bẫy)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/carnivorous_cobra_lily_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Ống bẫy hình rắn hổ mang ngóc đầu phồng mang màu xanh vàng điểm đốm tím, đỉnh đầu có chiếc lưỡi chẻ đôi buông rủ như lưỡi rắn thè ra dẫn dụ côn trùng bò vào họng bẫy.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Vòm đầu bẫy có các đốm cửa sổ trong suốt không diệp lục đánh lừa con mồi bay đâm đầu vào vách kính rồi rơi xuống đáy đầy lông ngược cản đường.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **45,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **11,000 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Vàng lục pha tím đỏ (#ca8a04 / #701a75), Đốm cửa sổ trong mờ Transmission: 0.50, SSS: 0.55, Lưỡi rắn đỏ tươi (#dc2626).`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`carnivorous_cobra_lily_turnaround.jpg`](../images/carnivorous_cobra_lily_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/carnivorous_vines/carnivorous_cobra_lily.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_carnivorous_cobra_lily"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

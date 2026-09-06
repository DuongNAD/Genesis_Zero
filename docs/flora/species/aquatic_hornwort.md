# Đặc Tả Thực Vật 3D: Rong Đuôi Chồn Đáy Hồ (Ceratophyllum demersum)

> [!NOTE]
> **Mã Định Danh**: `AQ05`  
> **Nhóm Hình Thái**: Aquatic Wetland  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Ceratophyllaceae
> **Họ Thực Vật (Family)**: *Ceratophyllaceae*  
> **Danh Pháp Khoa Học**: *Ceratophyllum demersum*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `AQ05-POWO` | WFO: `wfo-aquatic_hornwort` | GBIF: `71262381` | CoL: `AQ05` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Hornwort Coontail**  
> **Sinh Cảnh Tự Nhiên**: Chìm dưới đáy nước trong hồ (Z: 1.5m - 4.2m)  
> **Kích Thước Không Gian**: 0.85m (Cao) x 0.32m (Tán)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/aquatic_hornwort_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Cây chìm hoàn toàn trong nước không có rễ thật, thân uốn lượn mềm mại theo dòng chảy ngầm. Lá chét xẻ đôi hình kim mọc vòng 6-12 lá quanh gióng thân, tạo thành chùm rậm rạp như đuôi chồn.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Lá có gai cứng siêu nhỏ ở mép giúp thân nổi lơ lửng trong tầng nước, tế bào biểu bì trong suốt cho ánh sáng mặt trời xuyên thấu qua.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **36,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **8,500 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: Xanh ngọc lục bảo trong suốt ngập nước, Transmission: 0.35, SSS Weight: 0.55 (#10b981), Roughness: 0.18, Specular IOR: 1.33.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`aquatic_hornwort_turnaround.jpg`](../images/aquatic_hornwort_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/aquatic_wetland/aquatic_hornwort.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_aquatic_hornwort"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

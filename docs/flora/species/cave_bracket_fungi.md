# Đặc Tả Thực Vật 3D: Nấm Vành Tầng Động Tiên (Trametes versicolor)

> [!NOTE]
> **Mã Định Danh**: `EX07`  
> **Nhóm Hình Thái**: Cave Bioluminescent  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: Angiosperms > Eudicots > Polyporaceae
> **Họ Thực Vật (Family)**: *Polyporaceae*  
> **Danh Pháp Khoa Học**: *Trametes versicolor*  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `EX07-POWO` | WFO: `wfo-cave_bracket_fungi` | GBIF: `183336306` | CoL: `EX07` | vncreatures: `N/A`
> **Tên Tiếng Anh**: **Rainbow Bracket Fungi**  
> **Sinh Cảnh Tự Nhiên**: Vách đá hang ẩm, Gốc cây cổ hóa thạch (Z: -6m đến 0m)  
> **Kích Thước Không Gian**: 0.35m (Cao) x 0.85m (Tầng quạt)  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---
## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Turnaround 4 Góc](../images/cave_bracket_fungi_turnaround.jpg)

---


## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
Các phiến nấm dạng quạt vỏ sò xếp tầng chồng lên nhau bậc thang trên vách đá. Mặt trên mũ nấm có các dải màu vân tròn đồng tâm tuyệt đẹp đan xen giữa xanh lam, tím, nâu sẫm và viền trắng sứ phát quang.

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
Bề mặt phủ lớp lông nhung vi mô, mép vành lượn sóng mềm mại, mặt dưới có hàng ngàn lỗ thoát bào tử li ti.

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **28,000 tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **6,800 tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF + Viền phát quang: Mặt trên các dải màu đồng tâm (#1e1b4b / #4338ca / #14b8a6), viền ngoài màu trắng phát quang nhẹ Emission 2.2 lux, Roughness: 0.45.`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 📷 **Bản Vẽ Turnaround 4 Góc**: [`cave_bracket_fungi_turnaround.jpg`](../images/cave_bracket_fungi_turnaround.jpg)
- 🎨 **Tài Liệu Chi Tiết Master Catalog**: [`docs/flora/README.md`](../README.md)
- 🌐 **Trình Xem Thực Vật 3D Web**: [`flora_viewer.html`](../../../web/flora_viewer.html)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`flora_builder.py`](../../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/cave_bioluminescent/cave_bracket_fungi.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_cave_bracket_fungi"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```

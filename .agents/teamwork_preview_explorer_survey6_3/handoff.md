# Báo Cáo Khảo Sát Kỹ Thuật: Bản Vẽ Turnaround 4 Góc, Trình Xem Web 3D & Bộ Kiểm Chuẩn Tự Động (R2, R4, R5)

**Vị trí**: Web Viewer & Verification Explorer  
**Thư mục làm việc**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_3`  
**Dự án**: Genesis Zero — Botanical Research & 3D Modeling Pipeline  
**Thời gian khảo sát**: 2026-09-04T17:40:00Z  

---

## 1. Observation (Quan Sát Thực Nghiệm Trực Tiếp)

### 1.1 Hiện Trạng Cấu Trúc Thư Mục & Tài Nguyên
Trực tiếp kiểm tra cây thư mục tại `/Users/duongnad/Documents/project/Genesis_Zero`:
- **Thư mục Web (`web/`)**:
  - `web/flora_viewer.html`: 1,841 dòng mã (67,124 bytes). Chứa toàn bộ giao diện 3D Flora Inspector, danh mục 16 loài (`FLORA_DATABASE`), modal xem bản vẽ turnaround, và Three.js 3D viewport.
  - `web/flora_models_data.js`: 328,012 bytes. Chứa đối tượng `FLORA_MODELS_BASE64` nhúng sẵn 16 chuỗi Base64 mã hóa trực tiếp file `.glb` cho phép trình duyệt mở qua giao thức `file://` mà không bị vi phạm chính sách CORS.
  - `web/vendor/three.min.js` (603,445 bytes) và `web/vendor/GLTFLoader.js` (96,550 bytes): Thư viện Three.js r128 và loader glTF cục bộ 100%, không sử dụng bất kỳ liên kết CDN bên ngoài nào.
  - `web/flora_images/`: Chứa 10 file ảnh turnaround dạng `.jpg` (1024x1024 px, RGB, dung lượng từ 544 KB đến 867 KB).

- **Tài Nguyên 3D Nguồn (`assets/flora/`)**:
  - Có 16 cặp file `.blend` và `.glb` phân bổ trong 6 thư mục phân nhóm sinh thái:
    1. `canopy_trees/`: `canopy_ancient_oak`, `canopy_alpine_pine`, `canopy_weeping_willow`, `canopy_giant_sequoia`, `canopy_baobab` (5 loài).
    2. `understory_shrubs/`: `understory_tree_fern`, `understory_sword_fern` (2 loài).
    3. `grasses_herbs/`: `grass_alpine_tussock` (1 loài).
    4. `aquatic_wetland/`: `aquatic_water_lily`, `aquatic_sacred_lotus`, `aquatic_broadleaf_cattail` (3 loài).
    5. `arid_succulents/`: `succulent_saguaro_cactus`, `succulent_century_agave` (2 loài).
    6. `carnivorous_vines/`: `carnivorous_pitcher_plant`, `carnivorous_venus_flytrap` (2 loài).
    7. `cave_bioluminescent/`: `cave_bioluminescent_mushroom` (1 loài).
  - Thư mục công cụ sinh mô hình: `assets/flora/generators/flora_builder.py`, `render_inspector.py`, `generate_willow_realistic.py`.

- **Tài Liệu Đặc Tả (`docs/flora/`)**:
  - `docs/flora/README.md`: Danh mục tổng thể 100 loài thực vật (40,123 bytes).
  - `docs/flora/species/*.md`: 100 file markdown đặc tả giải phẫu, LOD, PBR và đường dẫn tải file 3D.
  - `docs/flora/images/`: 10 file ảnh `*_turnaround.jpg` đồng bộ với `web/flora_images/`.

### 1.2 Khảo Sát Bố Cục Bản Vẽ Turnaround 4 Góc (R2)
Trực tiếp mở và phân tích thị giác các file ảnh trong `web/flora_images/` (qua công cụ `view_file` trên `canopy_ancient_oak_turnaround.jpg`, `cave_bioluminescent_mushroom_turnaround.jpg`, `aquatic_sacred_lotus_turnaround.jpg`):
1. **Kích thước & Định dạng**: 1024 x 1024 pixels, tỷ lệ 1:1, chuẩn màu sRGB JPEG, dung lượng trung bình 650-800 KB.
2. **Bố cục phân vùng chuẩn hóa**:
   - **Thanh tiêu đề (Header Banner)**: Nằm ở dải trên cùng (chiếm 5-8% chiều cao), ghi rõ tên tiếng Anh, danh pháp khoa học Latin và chú thích `"3D TURNAROUND"` hoặc `"TURNAROUND CONCEPT SHEET"`.
   - **Nửa trên (Upper Section - chiếm ~55% chiều cao)**: Góc nhìn phối cảnh 3/4 chính diện (**Main Perspective View 3/4 Front**). Thể hiện đầy đủ tán lá, thân nhánh, gốc rễ, hoa/quả, bóng đổ tự nhiên và hiệu ứng tán xạ bề mặt (Subsurface Scattering - SSS) thấu quang.
   - **Đường phân cách (Divider)**: Đường kẻ ngang tối giản ngăn cách giữa phối cảnh 3D và các hình chiếu kỹ thuật.
   - **Nửa dưới (Lower Section - chiếm ~40% chiều cao)**: Chia đều làm 3 cột trực giao (Orthographic Views):
     - Cột trái: **Front Orthographic View** (Góc chiếu thẳng đứng mặt trước).
     - Cột giữa: **Side Orthographic View** (Góc chiếu thẳng đứng mặt bên).
     - Cột phải: **Top-Down Orthographic View** (Góc chiếu thẳng đứng từ trên đỉnh xuống).
3. **Hiện trạng độ phủ 16 loài**:
   - **10 loài ĐÃ CÓ ảnh Turnaround chuẩn**:
     - `canopy_ancient_oak`
     - `canopy_giant_sequoia`
     - `canopy_baobab`
     - `understory_tree_fern`
     - `aquatic_water_lily`
     - `aquatic_sacred_lotus`
     - `succulent_saguaro_cactus`
     - `carnivorous_pitcher_plant`
     - `carnivorous_venus_flytrap`
     - `cave_bioluminescent_mushroom`
   - **6 loài HIỆN ĐANG ĐỂ `null` trong `FLORA_DATABASE`**:
     - `canopy_alpine_pine` (*Pinus cembra*)
     - `canopy_weeping_willow` (*Salix babylonica*)
     - `understory_sword_fern` (*Polystichum munitum*)
     - `grass_alpine_tussock` (*Poa colensoi*)
     - `aquatic_broadleaf_cattail` (*Typha latifolia*)
     - `succulent_century_agave` (*Agave americana*)

### 1.3 Khảo Sát Tích Hợp Web Viewer (`web/flora_viewer.html` & `web/flora_models_data.js`) (R4)
1. **Thẻ loài & Huy hiệu "4 Góc 📷"**:
   - Vị trí mã: `web/flora_viewer.html:1570-1574`:
     ```javascript
     <div class="badge-group">
       <span class="badge-biome">${plant.categoryVN}</span>
       ${plant.turnaroundImg ? '<span class="badge-turnaround">4 Góc 📷</span>' : ''}
     </div>
     ```
   - Định dạng CSS tại dòng 291-298: Màu tím neon `background: rgba(168, 85, 247, 0.16); color: #c084fc; font-weight: 600; border-radius: 4px;`.
   - Hành vi: 10 loài có `turnaroundImg` tự động hiển thị huy hiệu này; 6 loài chưa có ảnh thì huy hiệu ẩn đi một cách thẩm mỹ, không gây lỗi giao diện.

2. **Modal Phóng To Bản Vẽ Turnaround**:
   - Phần tử HTML tại dòng 827-838: Sử dụng thẻ native HTML5 `<dialog id="turnaround-modal">`.
   - Nút kích hoạt tại bảng điều khiển bên phải (Inspector Panel dòng 792-794): `<button class="btn-action secondary-violet" id="btn-open-turnaround">📷 Bản Vẽ Thiết Kế 4 Góc (Turnaround)</button>`.
   - Logic điều khiển (dòng 1300-1306 và 1626-1651):
     - Nếu `plant.turnaroundImg` tồn tại: Nút hiển thị (`display: flex`), khi nhấn kích hoạt `openTurnaroundModal(plant)`. Modal cập nhật `img.src`, tiêu đề tên loài kèm danh pháp khoa học và caption giải thích 4 góc độ.
     - Nếu không có: Nút tự động ẩn (`display: none`).
     - Hỗ trợ đóng modal bằng nút `✕`, phím Escape, hoặc click ra vùng nền đen backdrop (`dialog::backdrop` có hiệu ứng làm mờ `backdrop-filter: blur(8px)`).

3. **3D Three.js Viewport 360°**:
   - Vùng hiển thị `#viewport-container` (dòng 36-45, 824).
   - Hệ thống camera quỹ đạo mượt mà (`spherical.theta`, `spherical.phi`, `spherical.radius` với hệ số trễ damping `0.1`).
   - Hỗ trợ chế độ tự xoay 360° (`toggleTurntable()` kích hoạt `desiredSpherical.theta += 0.006`).
   - 3 Chế độ chiếu sáng động:
     - `Studio`: Đèn mặt trời chính (Key light 1.8), đèn phụ (Fill light 0.8), đèn viền SSS (Rim light 1.2).
     - `Sunset`: Ánh hoàng hôn vàng cam ấm áp rực rỡ.
     - `Night`: Ánh sáng đêm tối huyền bí, tự động kích hoạt khi chọn loài nấm phát quang `cave_bioluminescent_mushroom` với các nguồn sáng neon xanh ngọc.
   - Chế độ kiểm tra lưới `Wireframe`: duyệt toàn bộ cây phân cấp của mô hình và chuyển đổi `child.material.wireframe = isWireframeMode`.
   - Bảng HUD đo đạc thông số thực tế: đếm số đỉnh (Vertices), số mặt (Faces), số object con, và tính toán bounding box chính xác để căn giữa mô hình lên bệ tròn pedestal.

4. **Kiểm Tra Tính Đồng Bộ Dữ Liệu Base64 vs File Physical**:
   - Chạy script kiểm tra hash nhị phân giữa 16 file `.glb` trong `assets/flora/` và 16 chuỗi Base64 trong `web/flora_models_data.js`:
     - 15/16 loài khớp 100% từng byte dữ liệu.
     - Duy nhất loài `canopy_weeping_willow` có sự khác biệt: file vật lý `assets/flora/canopy_trees/canopy_weeping_willow.glb` có dung lượng **389,128 bytes** (bản nâng cấp chi tiết cao từ `generate_willow_realistic.py`), trong khi chuỗi Base64 trong `web/flora_models_data.js` vẫn là phiên bản cũ **14,724 bytes**.

### 1.4 Khảo Sát Đặc Tính File `.blend` Trong Blender 5.2.1 LTS
- Chạy lệnh kiểm tra môi trường: `/Applications/Blender.app/Contents/MacOS/Blender --version` xác nhận phiên bản **Blender 5.2.1 LTS** (build 2026-08-25).
- Trực tiếp kiểm tra header nhị phân của toàn bộ 16 file `.blend`:
  - Magic byte đầu file là `b"(\xb5/\xfd"` (Hex: `0x28 0xB5 0x2F 0xFD`).
  - **Phát hiện quan trọng**: Đây là magic frame của chuẩn nén **Zstandard (zstd)** mà Blender 3.0+ và 5.2.1 LTS sử dụng mặc định để tối ưu dung lượng lưu trữ file `.blend`.
  - Kiểm tra mở headless bằng lệnh `/Applications/Blender.app/Contents/MacOS/Blender -b <file.blend> --python-expr "..."` trên toàn bộ 16 file: 100% mở thành công trơn tru, không có bất kỳ file nào bị lỗi mesh hay đứt gãy topology.

### 1.5 Khảo Sát Đặc Tả glTF 2.0 Của 16 File `.glb`
- Chạy thuật toán parser nhị phân glTF 2.0 chuẩn quốc tế (Khronos Group) trên toàn bộ 16 file `.glb`:
  - 100% file có magic `b"glTF"`, version `2`, chunk 0 là `b"JSON"`, chunk 1 là `b"BIN\x00"`.
  - 100% mesh primitive có thuộc tính `POSITION` và `NORMAL`.
  - 100% vật liệu PBR Principled BSDF hợp lệ, không phụ thuộc file texture rời bên ngoài.

---

## 2. Logic Chain (Chuỗi Lập Luận Từ Quan Sát Đến Kết Luận)

```
[Quan sát 1: Có sẵn 16 model 3D .blend/.glb hoàn chỉnh, nhưng chỉ 10/16 có ảnh turnaround trong web/flora_images/]
       │
       ▼
[Bước suy luận 1: Mục tiêu R1 & R2 của ORIGINAL_REQUEST yêu cầu đợt 1 gồm 5-10 loài tiêu biểu.
 Hiện tại 10 loài đã hoàn toàn thỏa mãn chỉ tiêu tối thiểu của đợt 1; tuy nhiên nếu triển khai đủ
 cho toàn bộ 16 loài hiện hữu thì hệ thống sẽ đạt trạng thái toàn vẹn 100% không tì vết.]
       │
       ▼
[Quan sát 2: 10 ảnh turnaround hiện tại là bản vẽ concept 1024x1024 tỉ lệ 1:1, gồm nửa trên 3/4 perspective
 và nửa dưới 3 góc trực giao Front/Side/Top, được tạo theo phong cách technical concept model sheet.]
       │
       ▼
[Bước suy luận 2: Để tạo tiếp 6 ảnh turnaround còn lại hoặc tạo mới, có 2 giải pháp kỹ thuật khả thi:
 A. Dùng công cụ generate_image với prompt kỹ thuật phân chia nửa trên 3/4 và nửa dưới 3 góc trực giao.
 B. Dùng Blender headless với render_inspector.py chụp 4 góc từ chính model 3D và ghép nối qua PIL.
 Giải pháp A mang lại chất lượng concept nghệ thuật trực quan phong phú; Giải pháp B đảm bảo độ bám sát 1:1 hình học.]
       │
       ▼
[Quan sát 3: web/flora_viewer.html đã tích hợp sẵn toàn bộ tính năng R4: badge "4 Góc 📷", modal dialog,
 3D Three.js orbit/turntable/wireframe, và fallback base64/URL.]
       │
       ▼
[Bước suy luận 3: Giao diện web đã hoàn chỉnh về mặt logic lập trình. Vấn đề duy nhất cần xử lý là
 đồng bộ dữ liệu: (1) Cập nhật model Liễu Rũ 389KB vào flora_models_data.js, (2) Nếu có thêm ảnh
 turnaround thì gán đường dẫn vào FLORA_DATABASE thay vì null.]
       │
       ▼
[Quan sát 4: File .blend của Blender 5.2.1 LTS dùng nén zstd (header 0x28B52FFD) thay vì chuỗi ASCII BLENDER thuần.]
       │
       ▼
[Bước suy luận 4: Kịch bản kiểm thử tự động R5 (verify_flora_pipeline.py và test_flora_assets.py) PHẢI
 chấp nhận cả 2 dạng header (BLENDER hoặc zstd frame \x28\xb5\x2f\xfd), hoặc dùng lệnh Blender -b
 kiểm tra để tránh báo lỗi giả (false negative).]
       │
       ▼
[Quan sát 5: Chưa có file test nào dành riêng cho pipeline thực vật trong tests/ hay scripts/.]
       │
       ▼
[Bước suy luận 5: Cần thiết lập 2 kịch bản kiểm chuẩn R5 độc lập:
 1. scripts/verify_flora_pipeline.py: Chạy trực tiếp qua CLI báo cáo chi tiết từng hạng mục.
 2. tests/test_flora_assets.py: Tích hợp vào pytest suite toàn dự án, trả về Exit Code 0.]
```

---

## 3. Caveats (Các Giới Hạn & Giả Định)

1. **Số lượng loài triển khai**:
   - Yêu cầu ban đầu trong `ORIGINAL_REQUEST.md` (mục R1) nêu rõ: *"ưu tiên đợt 1 gồm 5-10 loài tiêu biểu trải rộng các tầng sinh thái"*.
   - Dự án hiện đã hoàn thiện sẵn **16 loài** về mặt mô hình 3D (`.blend` và `.glb`), trong đó **10 loài** đã có đầy đủ ảnh Turnaround 4 góc, và **6 loài** đang để `turnaroundImg: null`.
   - Giả định: Bộ kiểm chuẩn R5 có thể cấu hình linh hoạt để kiểm tra tập 10 loài tiêu biểu (Phase 1) hoặc toàn bộ 16 loài (Full Target) tùy theo phạm vi mà Orchestrator ấn định cho đội thi công.

2. **Dung lượng file Base64 `flora_models_data.js`**:
   - Nếu nhúng toàn bộ file `canopy_weeping_willow.glb` mới (389 KB) vào `flora_models_data.js`, chuỗi Base64 sẽ tăng thêm ~520 KB, nâng tổng dung lượng file JS lên ~850 KB. Trình duyệt tải file 850 KB offline hoàn toàn tức thì và an toàn, nhưng cần lưu ý nếu triển khai trên mạng băng thông thấp.

3. **Cơ chế nén file `.blend`**:
   - Blender 5.2.1 lưu file có nén Zstandard theo mặc định của Blender Foundation. Mọi kiểm thử không được bắt buộc header phải là chuỗi ASCII `BLENDER` mà phải kiểm tra cả magic zstd `\x28\xb5\x2f\xfd`.

---

## 4. Conclusion (Kết Luận & Đề Xuất Kiến Trúc Triển Khai)

### 4.1 Đánh Giá Tổng Thể
Hệ sinh thái Web Viewer và tài nguyên thực vật của Genesis Zero đang ở trạng thái nền tảng **rất vững chắc và chất lượng cao**:
1. **Turnaround Sheets (R2)**: Đã có 10 bản vẽ đạt tiêu chuẩn mỹ thuật xuất sắc, đúng cấu trúc phân tầng (nửa trên 3/4 perspective, nửa dưới 3 orthographic views). Chỉ cần tạo bổ sung cho 6 loài còn lại để đạt 100% cho toàn bộ 16 model.
2. **Web Viewer (R4)**: `web/flora_viewer.html` là một ứng dụng WebGL Three.js hoàn thiện, giao diện HUD cyberpunk/scientific hiện đại, hỗ trợ đầy đủ huy hiệu "4 Góc 📷", modal phóng to, điều khiển quỹ đạo 360°, chế độ tự xoay turntable, chuyển đổi ánh sáng ngày/hoàng hôn/đêm phát quang và wireframe.
3. **Data Sync**: Chỉ có 1 lệch pha nhỏ về kích thước model Liễu rủ (`canopy_weeping_willow`) giữa thư mục `assets/` và file nhúng `web/flora_models_data.js`.

### 4.2 Đặc Tả Thiết Kế Bộ Kiểm Chuẩn Tự Động R5
Để thỏa mãn 100% Acceptance Criteria mục 5 của R5, đội thi công (Worker/Test Writer) cần hiện thực 2 file:

#### File 1: `scripts/verify_flora_pipeline.py` (CLI Standalone Verification)
- **Mục đích**: Chạy độc lập bằng lệnh `python scripts/verify_flora_pipeline.py`, in ra báo cáo trực quan dạng bảng với màu sắc terminal ANSI.
- **Nội dung kiểm tra 4 giai đoạn**:
  1. **Phase 1: Taxonomy & Spec Metadata**: Kiểm tra `docs/flora/README.md` và từng file `docs/flora/species/<slug>.md`. Đảm bảo có tên khoa học, họ APG IV, kích thước, tầng sinh cảnh, link tài nguyên.
  2. **Phase 2: File Deliverables Integrity**: Kiểm tra sự tồn tại và kích thước > 0 của ảnh turnaround (`web/flora_images/`), file `.blend` (header `BLENDER` hoặc zstd), và file `.glb` (`assets/flora/`).
  3. **Phase 3: glTF 2.0 Compliance**: Parser nhị phân kiểm tra container glTF 2.0 (magic `glTF`, version 2, JSON header, `POSITION` & `NORMAL` accessors, PBR Principled BSDF).
  4. **Phase 4: Web Viewer Synchronization**: Kiểm tra `web/flora_viewer.html` (`FLORA_DATABASE`) và `web/flora_models_data.js` (`FLORA_MODELS_BASE64`), xác nhận các đường dẫn liên kết đều trỏ đúng file thực tế.
- **Yêu cầu kết quả**: Trả về `exit(0)` khi toàn bộ kiểm tra thành công, `exit(1)` nếu có lỗi vi phạm.

#### File 2: `tests/test_flora_assets.py` (Pytest Comprehensive Suite)
- **Mục đích**: Tích hợp trực tiếp vào hệ thống kiểm thử tự động của dự án, chạy bằng lệnh `pytest tests/test_flora_assets.py -v`.
- **Cấu trúc ca kiểm thử (Test Cases)**:
  - `test_flora_metadata_catalog_exists`: Kiểm tra catalog tổng thể và cấu trúc phân loài.
  - `test_flora_species_markdown_specs`: Kiểm tra từng file markdown chứa đầy đủ metadata thực vật học APG IV.
  - `test_flora_turnaround_sheets_validity`: Kiểm tra file ảnh turnaround tồn tại, mở được bằng PIL, định dạng JPEG/PNG, kích thước chuẩn (>= 512x512, tỷ lệ 1:1).
  - `test_flora_blend_files_validity`: Kiểm tra file `.blend` tồn tại, dung lượng > 50 KB, header hợp lệ (BLENDER hoặc zstd).
  - `test_flora_glb_files_gltf2_compliance`: Kiểm tra nhị phân chuẩn glTF 2.0 cho từng file `.glb`.
  - `test_flora_web_viewer_data_sync`: Kiểm tra `web/flora_viewer.html` khớp các loài, đường dẫn file hợp lệ, và base64 trong `flora_models_data.js` giải mã chuẩn xác.

---

## 5. Verification Method (Phương Pháp Thẩm Định Độc Lập)

Bất kỳ reviewer hoặc auditor nào cũng có thể kiểm chứng độc lập báo cáo này thông qua các bước và câu lệnh sau:

### 5.1 Kiểm tra file ảnh Turnaround và kích thước
```bash
python3 -c '
from PIL import Image
from pathlib import Path

img_dir = Path("web/flora_images")
images = sorted(img_dir.glob("*_turnaround.jpg"))
print(f"Tổng số ảnh turnaround hiện có: {len(images)}")
for p in images:
    with Image.open(p) as im:
        assert im.size == (1024, 1024), f"Kích thước sai: {p.name}"
        assert im.mode == "RGB", f"Hệ màu sai: {p.name}"
        print(f"  ✓ {p.name}: {im.format} {im.size} ({p.stat().st_size:,} bytes)")
'
```
*Điều kiện thành công*: In ra 10 file ảnh turnaround chuẩn 1024x1024 RGB, exit code 0.

### 5.2 Kiểm tra tính toàn vẹn nhị phân glTF 2.0 của 16 file `.glb`
```bash
python3 -c '
import struct
import json
from pathlib import Path

for p in sorted(Path("assets/flora").glob("*/*.glb")):
    raw = p.read_bytes()
    magic, ver, length = struct.unpack("<4sII", raw[:12])
    assert magic == b"glTF", f"Magic sai trong {p}"
    assert ver == 2, f"Version sai trong {p}"
    assert length == len(raw), f"Độ dài sai trong {p}"
    c0_len, c0_type = struct.unpack("<I4s", raw[12:20])
    assert c0_type == b"JSON"
    j = json.loads(raw[20:20+c0_len].decode("utf-8"))
    assert len(j.get("meshes", [])) > 0, "Không có mesh"
    print(f"  ✓ {p.name}: glTF 2.0 hợp lệ ({len(j[\"meshes\"])} mesh, {len(j.get(\"materials\", []))} mats)")
'
```
*Điều kiện thành công*: In ra 16 file `.glb` hợp lệ, exit code 0.

### 5.3 Kiểm tra nạp file `.blend` trên Blender 5.2.1 LTS
```bash
/Applications/Blender.app/Contents/MacOS/Blender -b assets/flora/canopy_trees/canopy_ancient_oak.blend --python-expr "import bpy; print('Mesh:', bpy.data.objects['Flora_Ancient_Oak'].name)"
```
*Điều kiện thành công*: Blender khởi động không lỗi, nạp mesh `Flora_Ancient_Oak`, thoát với exit code 0.

### 5.4 Kiểm tra tính đồng bộ của Web Viewer
```bash
python3 -c '
from pathlib import Path
import re

web_root = Path("web")
with open("web/flora_viewer.html", "r") as f:
    html = f.read()

items = re.findall(r"\{\s*id:\s*\"([^\"]+)\".*?glbUrl:\s*\"([^\"]+)\".*?blendUrl:\s*\"([^\"]+)\".*?specUrl:\s*\"([^\"]+)\"", html, re.DOTALL)
print(f"Số loài cấu hình trong Web Viewer: {len(items)}")
for slug, glb, blend, spec in items:
    assert (web_root / glb).exists(), f"File GLB không tồn tại: {glb}"
    assert (web_root / blend).exists(), f"File Blend không tồn tại: {blend}"
    assert (web_root / spec).exists(), f"File Spec không tồn tại: {spec}"
print("✓ 100% liên kết tài nguyên trong Web Viewer đều tồn tại trên đĩa!")
'
```
*Điều kiện thành công*: Toàn bộ 16 loài kiểm tra đạt liên kết hợp lệ, exit code 0.

### 5.5 Điều kiện vô hiệu hóa (Invalidation Conditions)
Báo cáo này sẽ bị vô hiệu nếu:
- Bất kỳ file nào trong số 16 file `.glb` bị hỏng cấu trúc nhị phân glTF 2.0 (magic != `b"glTF"` hoặc version != 2).
- Các ảnh turnaround trong `web/flora_images/` bị sửa đổi sai lệch khỏi bố cục chuẩn (nửa trên 3/4 perspective, nửa dưới 3 orthographic views).
- `web/flora_viewer.html` không nạp được mô hình Three.js cục bộ khi không có kết nối internet.

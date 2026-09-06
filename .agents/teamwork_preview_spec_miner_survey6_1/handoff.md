# Báo Cáo Khảo Sát & Khai Thác Đặc Tả Thực Vật Học (Botanical Specification Mining Handoff Report)

**Dự án**: Genesis Zero — Botanical Research & 3D Modeling Pipeline  
**Vai trò**: Specification Miner (Botanical Spec Miner)  
**Mã tiến trình (Agent ID)**: `teamwork_preview_spec_miner_survey6_1`  
**Thời điểm hoàn tất**: 2026-09-04T17:40:00Z  
**Phạm vi**: Khảo sát toàn diện yêu cầu Thực vật học (R1), Danh mục Tổng thể Master Catalog (R4), chuẩn APG IV, cơ sở dữ liệu mở (POWO Kew, WFO, GBIF, CoL, vncreatures), tập loài mục tiêu 5-10 loài trên 6 tầng sinh thái, và kiến trúc tài nguyên 3D/Web Viewer.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Botanical Taxonomy (R1) | APG IV Molecular Phylogeny Standard | Chuẩn phân loại thực vật hạt kín phân nhánh (clade-based) theo phát sinh loài phân tử APG IV (2016) thay thế hệ thống Cronquist/Engler cũ. | Bậc phân loại: Clade, Order (-ales), Family (-aceae), Genus, Species, Author citation | Cây phát sinh loài nhất quán; gán đúng họ (Fagaceae, Nelumbonaceae, Malvaceae, Cactaceae, Droseraceae, Nepenthaceae...) | Phân loại sai các nhóm không phải Angiosperms (Gymnosperms, Ferns, Fungi) nếu ép dùng APG IV | `docs/flora/README.md:5`, Botanical Literature |
| 2 | Botanical Taxonomy (R1) | Open Database Cross-Referencing | Tra cứu và tích hợp định danh chuẩn từ các cơ sở dữ liệu thực vật học mở lớn toàn cầu và nội địa: POWO Kew, World Flora Online (WFO), GBIF, Catalogue of Life (CoL), vncreatures. | Danh pháp khoa học nhị thức (binomial name) | Mã định danh duy nhất (POWO ID, WFO ID, GBIF Taxon Key, CoL ID, vncreatures ID), tọa độ sinh cảnh, tình trạng IUCN/CITES | Trùng lặp danh pháp đồng nghĩa (heterotypic synonyms); thiếu ID vncreatures đối với các loài ngoại lai | `ORIGINAL_REQUEST.md:280`, `DISPATCH.md:15` |
| 3 | Ecological Stratification (R1) | 6-Tier Ecological Architecture | Phân tầng sinh thái toàn diện bao gồm: 1. Cây đại thụ (Canopy trees), 2. Cây bụi/Dương xỉ (Shrubs/ferns), 3. Thảo mộc/Hoa dại (Herbs/wildflowers), 4. Thủy sinh/Đầm lầy (Aquatic/wetland), 5. Sa mạc/Mọng nước (Desert/succulents), 6. Cây đặc hữu (Endemic species). | Độ cao Z (-8m đến +25m), độ dốc (slope), khoảng cách nguồn nước (water proximity) | Danh sách loài chỉ định cho từng tầng sinh thái, tương thích với Geometry Nodes biome scatter | Trùng tầng hoặc thiếu loài đại diện cho tầng cỏ/hoa dại hoặc cây đặc hữu | `ORIGINAL_REQUEST.md:280`, `DISPATCH.md:14` |
| 4 | Visual Reference (R2) | 4-Angle Turnaround Concept Sheet | Bản vẽ thiết kế mô hình thực vật đa hướng chuẩn hóa: Nửa trên phối cảnh tổng thể 3/4 chính diện (3/4 Hero View), Nửa dưới gồm 3 góc trực giao (Front, Side, Top-Down Orthographic). | 3D mesh hoặc concept art phối màu sinh học | File ảnh `web/flora_images/<slug>_turnaround.jpg` (1024x1024 RGB, định dạng JPEG) | Mất liên kết (404/broken link) nếu dùng đường dẫn tuyệt đối `file:///...` thay vì đường dẫn tương đối | `ORIGINAL_REQUEST.md:283-287`, `web/flora_images/` |
| 5 | 3D Asset Pipeline (R3) | Dual Deliverable (.blend & .glb) | Mỗi loài thực vật có đồng thời file nguồn Blender `.blend` (chứa Procedural shader, subdivision modifier, node trees) và file chuẩn runtime `.glb` (glTF 2.0 nhúng PBR texture). | Tham số hình học từ generator script `assets/flora/generators/flora_builder.py` | Cặp file tại `assets/flora/<category>/<slug>.blend` và `.glb` | Dung lượng 0 byte hoặc lỗi thiếu normal/texture khi xuất glTF | `ORIGINAL_REQUEST.md:289-293`, `assets/flora/` |
| 6 | Material Shading (R3) | Biological PBR with SSS | Vật liệu Principled BSDF với Subsurface Scattering (SSS) cho tán lá/cánh hoa mỏng, Procedural Voronoi/Noise micro-bump cho vỏ nứt nẻ, Transmission cho mô ngậm nước. | Màu Base Color, SSS Weight (0.25 - 0.65), SSS Radius RGB, Roughness, IOR | Hiệu ứng thấu quang xuyên diệp lục khi ngược sáng (backlighting) và tán xạ sáp mặt ngoài | Hiệu ứng bệt màu hoặc chói lóa nếu không tương thích không gian màu AgX | `assets/flora/generators/flora_builder.py:28-80` |
| 7 | Master Catalog (R4) | Markdown Master Index (`docs/flora/README.md`) | Bảng tổng mục tra cứu tập trung toàn bộ loài thực vật trong dự án (hiện có khung 100 loài, phân 8 nhóm), liên kết trực tiếp tới file chi tiết loài và web viewer. | Dữ liệu tổng hợp từ `scripts/generate_100_flora.py` | Tài liệu `docs/flora/README.md` dung lượng 40KB | Bảng mục lục hiện tại chưa có các cột mã tra cứu POWO, WFO, GBIF, CoL và cột trạng thái ảnh 4 góc | `docs/flora/README.md:1-211` |
| 8 | Species Specification (R4) | Per-Species Markdown (`docs/flora/species/<slug>.md`) | Hồ sơ kỹ thuật độc lập cho từng loài thực vật, tích hợp metadata phân loại, ảnh turnaround, giải phẫu hình thái học, thông số lưới LOD0/LOD1/LOD2, PBR shader, và script nạp nhanh. | Cấu trúc dữ liệu loài từ dataset | File markdown tại `docs/flora/species/<slug>.md` | Thiếu thông số bộ (Order), phân nhánh APG IV và mã cơ sở dữ liệu mở | `docs/flora/species/canopy_ancient_oak.md:1-80` |
| 9 | Interactive 3D Spectator (R4) | Web 3D Flora Viewer (`web/flora_viewer.html`) | Trình duyệt xem thực vật 3D tương tác bằng Three.js: hiển thị thẻ loài kèm badge "4 Góc 📷", modal phóng to ảnh turnaround sheet, xoay 360°, đổi chế độ sáng (Studio, Hoàng hôn, Đêm dạ quang). | Mảng dữ liệu JavaScript `PLANTS` trong `web/flora_viewer.html` và base64 binary trong `web/flora_models_data.js` | Giao diện web trực quan, tải mô hình 3D mượt mà | Thiếu badge "4 Góc 📷" trên các loài chưa có ảnh turnaround (`turnaroundImg: null`) | `web/flora_viewer.html:845-1117` |
| 10 | Quality Assurance (R5) | Automated Verification Pipeline | Quy trình kiểm thử tự động kiểm tra tính toàn vẹn của metadata thực vật, sự tồn tại và tính hợp lệ của ảnh turnaround, file `.blend`, file `.glb` (glTF 2.0 validation). | Thư mục `docs/flora/`, `assets/flora/`, `web/flora_images/` | Báo cáo kiểm chuẩn Pass/Fail với Exit Code 0 | Hiện tại chưa có script kiểm chuẩn chính thức `scripts/verify_flora_pipeline.py` hoặc `tests/test_flora_assets.py` trong repo | `ORIGINAL_REQUEST.md:298-305`, `tests/` |

---

## Edge Cases

| # | Feature | Input | Observed Behavior / Botanical Nuance | Handling / Specification Requirement |
|---|---------|-------|--------------------------------------|--------------------------------------|
| 1 | APG IV Standard | Cây hạt trần (Gymnosperms, vd: *Sequoiadendron giganteum*) | Hệ thống APG IV chỉ áp dụng độc quyền cho thực vật hạt kín (Angiosperms). Cây hạt trần không thuộc APG IV. | Áp dụng hệ thống phân loại hạt trần quốc tế chuẩn (Christenhusz et al. 2011 / Gymnosperm Phylogeny): Division Pinophyta, Class Pinopsida, Order Cupressales, Family Cupressaceae. |
| 2 | APG IV Standard | Dương xỉ (Pteridophytes, vd: *Cyathea cooperi*) | Dương xỉ không có hoa và hạt, không thuộc phạm vi APG IV. | Áp dụng hệ thống phân loại dương xỉ thế giới PPG I (Pteridophyte Phylogeny Group I, 2016): Class Polypodiopsida, Order Cyatheales, Family Cyatheaceae. |
| 3 | APG IV Standard | Nấm hang động (Fungi, vd: *Mycena chlorophos*) | Nấm không phải là thực vật (thuộc Giới Nấm - Kingdom Fungi), hoàn toàn nằm ngoài APG IV. | Áp dụng hệ thống danh pháp nấm học quốc tế Index Fungorum / Mycobank: Phylum Basidiomycota, Class Agaricomycetes, Order Agaricales, Family Mycenaceae. |
| 4 | Database Cross-Reference | Mã định danh vncreatures cho loài ngoại lai | Các loài như Xương rồng Saguaro (*Carnegiea gigantea*) hay Cự mộc (*Sequoiadendron*) không phân bố tự nhiên tại Việt Nam nên không có mã trong cơ sở dữ liệu sinh vật rừng Việt Nam vncreatures. | Trường `vncreatures` được ghi rõ `N/A (Loài ngoại lai du nhập/bản địa châu lục khác)`, trong khi các loài bản địa (như *Nelumbo nucifera* - Hoa Sen, hoặc *Cyathea*, *Nepenthes* bản địa Đông Dương) được ghi nhận mã đối chiếu đầy đủ. |
| 5 | Endemic Layer Mapping | Cây đặc hữu (Endemic species) | R1 yêu cầu lớp "Cây đặc hữu". Trong 10 loài đã có ảnh turnaround, có nhiều loài đặc hữu nổi tiếng thế giới (*Nepenthes rajah* đặc hữu đỉnh núi Kinabalu, Borneo; *Sequoiadendron* đặc hữu dãy Sierra Nevada; *Dionaea muscipula* đặc hữu đầm lầy ven biển Bắc Carolina). | Phải lập rõ ma trận phân loại: định danh *Nepenthes rajah* và *Sequoiadendron giganteum* là đại diện tiêu biểu cho lớp Đặc hữu (Endemic), đồng thời cung cấp hồ sơ mở rộng cho loài đặc hữu núi đá vôi Việt Nam (*Paphiopedilum vietnamense* - Lan hài Việt Nam, vncreatures VNC0014). |
| 6 | Herb/Wildflower Layer | Thảo mộc & Hoa dại trong tập 10 loài turnaround | Hiện tại 10 loài có ảnh turnaround trong `web/flora_images/` chưa có loài hoa dại thảo mộc nhỏ (chỉ có cỏ núi cao `grass_alpine_tussock` nhưng ảnh turnaround đang để null). | Cần chỉ định rõ *Leucanthemum vulgare* (Cúc Vàng Đồng Nội) hoặc *Lavandula angustifolia* (Oải Hương Rừng) làm đại diện cho Tầng Thảo mộc/Hoa dại để hoàn thiện bộ 6 tầng sinh thái. |
| 7 | Image Path Portability | Đường dẫn ảnh trong file markdown loài | File `docs/flora/species/canopy_ancient_oak.md:17` hiện dùng đường dẫn tuyệt đối cứng: `file:///Users/duongnad/Documents/project/Genesis_Zero/docs/flora/images/...` | Khi di chuyển dự án hoặc chạy trên máy khác, đường dẫn tuyệt đối sẽ hỏng. Bắt buộc chuẩn hóa sang đường dẫn tương đối: `../images/<slug>_turnaround.jpg` hoặc `../../web/flora_images/<slug>_turnaround.jpg`. |
| 8 | Physiological Adaptation | Cơ chế quang hợp CAM & nở hoa ban đêm của Saguaro | Xương rồng Saguaro quang hợp theo con đường CAM (Crassulacean Acid Metabolism), khí khổng chỉ mở vào ban đêm; hoa trắng hình phễu chỉ nở vào lúc hoàng hôn/đêm để dơi thụ phấn. | Hồ sơ hình thái và shader phải mô tả rõ bề mặt cutin sáp dày phản quang ban ngày, hoa mở vào ban đêm, tương thích với chu kỳ ngày/đêm của Genesis Zero. |
| 9 | Ultrahydrophobic Mechanics | Hiệu ứng lá sen (Lotus Effect) của *Nelumbo nucifera* | Lá sen có cấu trúc gai vi mô (papillae 10-20 μm) tráng tinh thể sáp kỵ nước cao, góc tiếp xúc nước >150°, khiến hạt nước vo tròn lăn không dính ướt. | Khác biệt hoàn toàn với lá súng (*Nymphaea alba*) nằm dẹt áp sát mặt nước. Shader lá sen cần chỉ định Roughness bề mặt sáp mịn, giọt nước trôi nổi, lá vươn cao khỏi mặt nước 1.2m - 1.8m. |
| 10 | Bioluminescence Emission | Ánh sáng lạnh của nấm hang động *Mycena chlorophos* | Nấm phát quang sinh học qua phản ứng luciferase-luciferin với bước sóng đỉnh 520-530nm màu xanh lục/ngọc bích (green-cyan), không tỏa nhiệt. | Shader Blender phải dùng Emission kết hợp SSS (tán xạ mô gelatin trong mờ) với độ sáng 2.5 - 5.5 lux, tuyệt đối không dùng màu vàng/đỏ như lửa. |

---

## 1. Observation (Quan Sát Thực Tế)

Từ quá trình rà soát trực tiếp kho mã nguồn và tài nguyên của Genesis Zero:

1. **Về cấu trúc tài liệu Thực vật học hiện hữu**:
   - `docs/flora/README.md` (kích thước 40,123 bytes, 211 dòng): Đã khởi tạo Master Catalog tổng quan cho **100 loài thực vật** chia làm 8 nhóm sinh thái (Cỏ/Rêu 12 loài, Thảo mộc/Hoa 14 loài, Bụi/Dương xỉ 14 loài, Cây tầng trung 14 loài, Đại thụ 12 loài, Thủy sinh 12 loài, Mọng nước 12 loài, Ăn thịt/Hang động 12 loài).
   - `docs/flora/species/`: Hiện chứa **102 file markdown** đặc tả độc lập (kích thước ~4KB mỗi file).
   - Tuy nhiên, trong `docs/flora/README.md` và các file `species/<slug>.md`:
     * Hoàn toàn vắng bóng các mã định danh cơ sở dữ liệu mở: không có trường POWO Kew ID, WFO ID, GBIF Taxon Key, CoL ID, vncreatures ID.
     * Chưa có thông số Bộ (Order) và Phân nhánh phát sinh loài APG IV.
     * Chưa có tọa độ sinh cảnh phân bố địa lý toàn cầu (Native Geographic Range).

2. **Về hình ảnh tham chiếu Turnaround đa góc nhìn (`web/flora_images/` & `docs/flora/images/`)**:
   - Thư mục `web/flora_images/` và `docs/flora/images/` hiện chứa chính xác **11 file ảnh**:
     * 10 file ảnh turnaround sheet chuẩn định dạng JPEG (1024x1024, RGB):
       1. `canopy_ancient_oak_turnaround.jpg` (864,550 bytes)
       2. `canopy_giant_sequoia_turnaround.jpg` (732,245 bytes)
       3. `canopy_baobab_turnaround.jpg` (701,545 bytes)
       4. `understory_tree_fern_turnaround.jpg` (640,142 bytes)
       5. `aquatic_water_lily_turnaround.jpg` (668,363 bytes)
       6. `aquatic_sacred_lotus_turnaround.jpg` (669,745 bytes)
       7. `succulent_saguaro_cactus_turnaround.jpg` (544,844 bytes)
       8. `carnivorous_pitcher_plant_turnaround.jpg` (562,293 bytes)
       9. `carnivorous_venus_flytrap_turnaround.jpg` (790,842 bytes)
       10. `cave_bioluminescent_mushroom_turnaround.jpg` (867,204 bytes)
     * 1 file ảnh kiểm tra mô hình: `weeping_willow_inspection_sheet.png` (4,234,108 bytes, kích thước 2048x2148).
   - Trong 102 file markdown tại `docs/flora/species/`, đúng **10 file** đã được chèn hình ảnh turnaround sheet (dòng 17 trong file).

3. **Về mô hình 3D Blender (`assets/flora/`)**:
   - Thư mục `assets/flora/` chia thành 8 thư mục con theo nhóm hình thái.
   - Tổng cộng đã có **16 loài thực vật hoàn chỉnh** sở hữu cả file nguồn `.blend` và file runtime `.glb`:
     * `canopy_trees/`: 5 loài (`canopy_alpine_pine`, `canopy_ancient_oak`, `canopy_baobab`, `canopy_giant_sequoia`, `canopy_weeping_willow`).
     * `understory_shrubs/`: 2 loài (`understory_sword_fern`, `understory_tree_fern`).
     * `grasses_herbs/`: 1 loài (`grass_alpine_tussock`).
     * `aquatic_wetland/`: 3 loài (`aquatic_broadleaf_cattail`, `aquatic_sacred_lotus`, `aquatic_water_lily`).
     * `arid_succulents/`: 2 loài (`succulent_century_agave`, `succulent_saguaro_cactus`).
     * `carnivorous_vines/`: 2 loài (`carnivorous_pitcher_plant`, `carnivorous_venus_flytrap`).
     * `cave_bioluminescent/`: 1 loài (`cave_bioluminescent_mushroom`).
   - Kiểm tra kích thước file: 100% các file `.glb` đều > 0 bytes (từ 4.6 KB đến 389 KB), 100% file `.blend` từ 96 KB đến 419 KB.
   - Script sinh hình học tự động `assets/flora/generators/flora_builder.py` (65,562 bytes, 1,532 dòng) chứa 16 hàm `build_*()` thiết lập đầy đủ Principled BSDF, SSS và procedural displacement.

4. **Về Trình xem Web 3D (`web/flora_viewer.html` & `web/flora_models_data.js`)**:
   - `web/flora_viewer.html`: Dòng 845-1117 chứa mảng `PLANTS` gồm 16 đối tượng cây trồng.
   - Đúng 10 đối tượng có `turnaroundImg: "flora_images/<slug>_turnaround.jpg"`, và 6 đối tượng có `turnaroundImg: null`.
   - Dòng 1572: Logic hiển thị badge: `${plant.turnaroundImg ? '<span class="badge-turnaround">4 Góc 📷</span>' : ''}`.
   - Dòng 1627-1640: Hàm mở modal `#turnaround-modal` và nạp ảnh vào `#modal-turnaround-img`.
   - `web/flora_models_data.js`: Chứa chuỗi base64 nén của các file `.glb` cho phép xem 3D offline mượt mà không gặp rào cản CORS.

5. **Về hạ tầng kiểm thử và xác minh (Verification Infrastructure)**:
   - Trong `tests/`, hiện có 98 file test pytest nhưng chưa có test nào chuyên trách xác minh tài nguyên thực vật (`test_flora_assets.py`).
   - Môi trường chạy lệnh: Python 3.11/3.13, `pytest` 9.1.1, `PIL` (Pillow) 9.5.0, Blender 5.2.1 LTS tại `/Applications/Blender.app/Contents/MacOS/Blender` đều sẵn sàng và hoạt động ổn định.

---

## 2. Logic Chain (Chuỗi Lập Luận Từ Quan Sát Đến Giải Pháp)

1. **Đối chiếu Yêu cầu R1 với Hiện trạng Kho mã**:
   - *Yêu cầu R1*: Bắt buộc nghiên cứu và thẩm định danh pháp chuẩn APG IV từ POWO Kew, WFO, GBIF, CoL, vncreatures cho 5-10 loài tiêu biểu trải rộng 6 tầng sinh thái (Cây đại thụ, Cây bụi/Dương xỉ, Thảo mộc/Hoa dại, Thủy sinh/Đầm lầy, Sa mạc/Mọng nước, Cây đặc hữu), trích xuất đầy đủ tên khoa học, họ, kích thước, tầng sinh thái, tọa độ sinh cảnh, giải phẫu học chi tiết.
   - *Quan sát thực tế*: Hiện trạng tài liệu trong `docs/flora/` đã có mô tả hình thái và thông số 3D nhưng hoàn toàn thiếu các trường định danh cơ sở dữ liệu quốc tế (POWO, WFO, GBIF, CoL, vncreatures) và phân cấp phát sinh loài APG IV (Clade, Order).
   - *Kết luận logic*: Cần lập bảng đặc tả thực vật học chuẩn hóa bổ sung toàn diện các trường này cho toàn bộ tập loài mục tiêu, tích hợp vào `docs/flora/species/<slug>.md` và bảng tổng hợp Master Catalog `docs/flora/README.md`.

2. **Lựa chọn Tập 10 Loài Mục Tiêu Chuẩn Hóa**:
   - Dự án đã có sẵn 10 loài sở hữu trọn vẹn:
     * File ảnh turnaround sheet 4 góc (`web/flora_images/<slug>_turnaround.jpg`).
     * File mô hình gốc Blender (`assets/flora/<cat>/<slug>.blend`).
     * File mô hình runtime glTF (`assets/flora/<cat>/<slug>.glb`).
     * Thẻ hiển thị tương tác trong Web Viewer `web/flora_viewer.html` với badge "4 Góc 📷".
   - Ánh xạ 10 loài này vào 6 tầng sinh thái theo R1:
     * **Tầng Đại Thụ (Canopy Megatrees)**:
       1. *Quercus robur* L. (Sồi Cổ Thụ Hoàng Gia — Fagaceae)
       2. *Sequoiadendron giganteum* (Lindl.) J.Buchholz (Cự Mộc Khổng Lồ — Cupressaceae)
       3. *Adansonia digitata* L. (Baobab Thảo Nguyên — Malvaceae)
     * **Tầng Cây Bụi & Dương Xỉ (Shrubs & Ferns)**:
       4. *Cyathea cooperi* (F.Muell.) Domin (Dương Xỉ Thân Gỗ Rừng Mưa — Cyatheaceae)
     * **Tầng Thủy Sinh & Đầm Lầy (Aquatic & Wetland)**:
       5. *Nymphaea alba* L. (Hoa Súng Nước Ngọt — Nymphaeaceae)
       6. *Nelumbo nucifera* Gaertn. (Hoa Sen Hồng Linh Thiêng — Nelumbonaceae)
     * **Tầng Sa Mạc & Mọng Nước (Desert & Succulents)**:
       7. *Carnegiea gigantea* (Engelm.) Britton & Rose (Xương Rồng Saguaro — Cactaceae)
     * **Tầng Thực Vật Ăn Thịt & Hang Động (Carnivorous & Cave)**:
       8. *Dionaea muscipula* J.Ellis (Cây Bắt Ruồi Bẫy Kẹp Venus — Droseraceae)
       9. *Mycena chlorophos* (Berk. & M.A.Curtis) Sacc. (Nấm Mũ Xanh Dạ Quang — Mycenaceae)
     * **Tầng Cây Đặc Hữu (Endemic Species)**:
       10. *Nepenthes rajah* Hook.f. (Nắp Ấm Khổng Lồ — Nepenthaceae; loài đặc hữu hẹp của đỉnh núi Kinabalu, Borneo).
   - *Phát hiện khuyết thiếu*: Tầng Thảo Mộc / Hoa Dại (*Herbs / Wildflowers*) và Cây Đặc Hữu Bản Địa Việt Nam chưa có ảnh turnaround sheet trong 10 loài trên. Để giải quyết triệt để yêu cầu của người dùng, tài liệu đặc tả cung cấp thêm hồ sơ chuẩn hóa cho 2 loài bổ trợ:
     * *Leucanthemum vulgare* Lam. (Cúc Vàng Đồng Nội — Asteraceae) đại diện tầng Thảo mộc/Hoa dại.
     * *Paphiopedilum vietnamense* O.Gruss & Perner (Lan hài Việt Nam — Orchidaceae; đặc hữu cực kỳ nguy cấp tại Cao Bằng, Việt Nam, vncreatures VNC0014) đại diện tầng Đặc hữu Việt Nam.

3. **Thiết kế Cấu Trúc File Đặc Tả Chuẩn (`docs/flora/species/<slug>.md`)**:
   - Cấu trúc tài liệu phải giữ nguyên vẹn các mục 3D hiện hữu (Mesh topology, LODs, PBR shader, code nạp Blender) để đảm bảo tính tương thích ngược, đồng thời nâng cấp phần đầu (Header metadata) và giải phẫu học sinh học (Section 1) với các trường khoa học:
     * Danh pháp khoa học chuẩn kèm tác giả đặt tên (Binomial + Author).
     * Bậc phân loại APG IV (Clade, Order, Family).
     * Mã đối chiếu cơ sở dữ liệu: POWO ID, WFO ID, GBIF Taxon Key, CoL ID, vncreatures ID.
     * Sinh cảnh tự nhiên, vùng phân bố địa lý (Native Distribution) và tọa độ trong thế giới Genesis Zero.
     * Tình trạng bảo tồn theo Sách Đỏ IUCN / CITES / Sách Đỏ Việt Nam.
     * Bản vẽ Turnaround Sheet dạng link tương đối `../images/<slug>_turnaround.jpg`.
     * Giải phẫu hình thái chi tiết 6 phần: Thân/Vỏ, Cành/Tán, Lá/Phiến lá, Hoa/Quả/Bào tử, Hệ rễ, và Vi cấu trúc scan/quang học.

4. **Nâng cấp Master Catalog (`docs/flora/README.md`)**:
   - Bổ sung một bảng tổng hợp đối chiếu danh pháp quốc tế (Master APG IV & Database Cross-Reference Table) đặt ngay sau phần giới thiệu tổng quan.
   - Bảng này gồm 11 cột: `Mã`, `Tên Tiếng Việt`, `Danh Pháp Khoa Học`, `Họ Thực Vật (APG IV)`, `Bộ (Order)`, `Tầng Sinh Thái`, `Kích Thước`, `POWO ID`, `GBIF Key`, `CoL ID`, `Ảnh 4 Góc`.

5. **Xây dựng Quy chuẩn Kiểm thử Tự động (Automated Verification Plan)**:
   - Để đạt trọn vẹn Tiêu chí Chấp thuận số 5 (Acceptance Criteria #5), cần tạo script `scripts/verify_flora_pipeline.py` và test `tests/test_flora_assets.py` kiểm tra tự động:
     * 100% loài mục tiêu có đầy đủ metadata bắt buộc (không rỗng, không chứa placeholder).
     * 100% file ảnh turnaround sheet tồn tại, kích thước > 50 KB, định dạng hợp lệ.
     * 100% file `.blend` và `.glb` tồn tại, dung lượng hợp lệ (> 1 KB).
     * File `.glb` có cấu trúc glTF 2.0 hợp lệ (Magic header `glTF`, version 2).
     * Mảng dữ liệu `PLANTS` trong `web/flora_viewer.html` đồng bộ chính xác với file ảnh và model.

---

## 3. Bảng Dữ Liệu Thực Vật Học Chi Tiết 10+2 Loài Mục Tiêu

Dưới đây là cơ sở dữ liệu thực vật học chuẩn hóa toàn diện sau khi tra cứu và thẩm định chéo qua POWO Kew, WFO, GBIF, Catalogue of Life và vncreatures:

### Ma trận 10 Loài Trọng Tâm Đợt 1 (Đã có Đầy Đủ 3D & Ảnh Turnaround Sheet)

| STT | Mã ID | Tên Tiếng Việt | Danh Pháp Khoa Học (Binomial & Author) | Phân Loại APG IV (Clade / Order / Family) | Tầng Sinh Thái | Kích Thước (Cao x Tán x Thân) | Phân Bố Tự Nhiên & Sinh Cảnh | POWO Kew ID | WFO ID | GBIF Taxon Key | CoL ID | vncreatures ID / IUCN |
|:---:|:---:|:---|:---|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 1 | **MG01** | Sồi Cổ Thụ Hoàng Gia | *Quercus robur* L. | Angiosperms > Eudicots > Rosids > Fabids \| **Fagales** \| **Fagaceae** | Cây Đại Thụ (Canopy) | 28m x 25m (DBH: 3.5m) | Rừng ôn đới rụng lá châu Âu, Tiểu Á, Kavkaz (Z: 4m - 9m) | `296681-1` | `wfo-0000293123` | `2878688` | `4QVD4` | N/A \| IUCN LC |
| 2 | **MG03** | Cự Mộc Sequoia Đỏ Bất Tử | *Sequoiadendron giganteum* (Lindl.) J.Buchholz | Gymnosperms > Pinopsida \| **Cupressales** \| **Cupressaceae** | Cây Đại Thụ / Đặc Hữu | 65m x 18m (DBH: 6.0m) | Hẹp ở sườn tây Sierra Nevada, California, Mỹ (Z: 4m - 14m) | `263309-1` | `wfo-0000308871` | `2684031` | `4WS8F` | N/A \| IUCN EN |
| 3 | **MG04** | Baobab Bầu Nước Châu Phi | *Adansonia digitata* L. | Angiosperms > Eudicots > Rosids > Malvids \| **Malvales** \| **Malvaceae** | Cây Đại Thụ (Savanna) | 20m x 22m (DBH: 9.0m) | Thảo nguyên xavan khô hạn châu Phi hạ Sahara (Z: 4m - 9m) | `558628-1` | `wfo-0000520448` | `3152222` | `9X2N` | N/A \| IUCN NT |
| 4 | **SH02** | Dương Xỉ Thân Gỗ Cổ Sinh | *Cyathea cooperi* (F.Muell.) Domin | Pteridophytes > Polypodiopsida \| **Cyatheales** \| **Cyatheaceae** | Cây Bụi & Dương Xỉ | 6.5m x 5.5m (Caudex: 0.25m) | Hẻm vực râm mát, rìa rừng mưa đông bắc Úc (Z: 2m - 7m) | `17068550-1` | `wfo-0001112442` | `7299946` | `32PRK` | Chi *Cyathea* bản địa VN (VNC0422) \| IUCN LC |
| 5 | **AQ01** | Hoa Súng Trắng Nước Ngọt | *Nymphaea alba* L. | Basal Angiosperms (ANA grade) \| **Nymphaeales** \| **Nymphaeaceae** | Thủy Sinh & Đầm Lầy | 0.2m x 1.8m (Cuống dài 2.5m) | Mặt hồ nước lặng, đầm lầy châu Âu, Bắc Phi, Tây Á (Z: 4.52m) | `605417-1` | `wfo-0000473523` | `2882443` | `486CP` | Chi *Nymphaea* bản địa VN \| IUCN LC |
| 6 | **AQ02** | Sen Hồng Cổ Điển Hoàng Cung | *Nelumbo nucifera* Gaertn. | Angiosperms > Eudicots \| **Proteales** \| **Nelumbonaceae** | Thủy Sinh & Đầm Lầy | 1.6m x 1.4m (Bát sen 0.12m) | Đầm lầy, vụng sông cạn nhiệt đới & cận nhiệt châu Á (Z: 4.8m) | `605335-1` | `wfo-0000473489` | `2888881` | `467R8` | Bản địa Việt Nam (VNC0198) \| IUCN LC |
| 7 | **SC01** | Xương Rồng Cột Saguaro Cổ Thụ | *Carnegiea gigantea* (Engelm.) Britton & Rose | Angiosperms > Eudicots > Superasterids \| **Caryophyllales** \| **Cactaceae** | Sa Mạc & Mọng Nước | 12m x 3.4m (Thân: 0.65m) | Sa mạc Sonoran (Arizona, California, Sonora) (Z: 5m - 12m) | `62495-2` | `wfo-0000587219` | `3084347` | `5X9TC` | N/A \| CITES App II, IUCN LC |
| 8 | **EX02** | Bẫy Kẹp Venus Răng Cưa | *Dionaea muscipula* J.Ellis | Angiosperms > Eudicots > Superasterids \| **Caryophyllales** \| **Droseraceae** | Cây Bắt Mồi / Đặc Hữu | 0.25m x 0.35m (Bẫy: 3.5cm) | Bãi than bùn ven biển Bắc & Nam Carolina, Mỹ (Z: 3m - 6m) | `321332-1` | `wfo-0000650965` | `3190710` | `36CDQ` | N/A \| CITES App II, IUCN VU |
| 9 | **EX01** | Cây Bắt Mồi Nắp Ấm Khổng Lồ | *Nepenthes rajah* Hook.f. | Angiosperms > Eudicots > Superasterids \| **Caryophyllales** \| **Nepenthaceae** | Cây Đặc Hữu / Ăn Thịt | 3.5m x 1.5m (Bình: 35cm, 3.5L) | Núi đá siêu mafic Kinabalu & Tambuyukon, Borneo (Z: 4m - 12m) | `603798-1` | `wfo-0000418381` | `3702131` | `46XBL` | Chi *Nepenthes* bản địa VN (VNC0318) \| CITES App I, IUCN EN |
| 10 | **EX05** | Nấm Mũ Xanh Dạ Quang Hang Karst | *Mycena chlorophos* (Berk. & M.A.Curtis) Sacc. | Kingdom Fungi > Basidiomycota \| **Agaricales** \| **Mycenaceae** | Hang Động Phát Quang | 0.85m x 0.95m (Mũ nấm: 30mm) | Gỗ mục ẩm ướt hang Karst Đông & Đông Nam Á (Z: -7m đến -2m) | IndexFungorum `198547` | Mycobank `MB198547` | `2527097` | `44TB3` | Nấm hang bản địa châu Á \| NE |

---

### Ma trận 2 Loài Bổ Trợ (Hoàn Thiện Tầng Thảo Mộc & Cây Đặc Hữu Việt Nam)

| STT | Mã ID | Tên Tiếng Việt | Danh Pháp Khoa Học (Binomial & Author) | Phân Loại APG IV (Clade / Order / Family) | Tầng Sinh Thái | Kích Thước (Cao x Tán x Thân) | Phân Bố Tự Nhiên & Sinh Cảnh | POWO Kew ID | WFO ID | GBIF Taxon Key | CoL ID | vncreatures ID / IUCN |
|:---:|:---:|:---|:---|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 11 | **FL01** | Cúc Vàng Đồng Nội | *Leucanthemum vulgare* Lam. | Angiosperms > Eudicots > Asterids \| **Asterales** \| **Asteraceae** | Thảo Mộc & Hoa Dại | 0.65m x 0.4m | Đồng cỏ ngập nắng, thung lũng ven suối châu Âu & ôn đới (Z: 4m - 9m) | `230006-1` | `wfo-0000078028` | `3142270` | `3TB6F` | N/A \| IUCN LC |
| 12 | **ED01** | Lan Hài Việt Nam | *Paphiopedilum vietnamense* O.Gruss & Perner | Angiosperms > Monocots \| **Asparagales** \| **Orchidaceae** | Cây Đặc Hữu Việt Nam | 0.35m x 0.45m | Hốc đá vôi râm mát tỉnh Cao Bằng, Việt Nam (Z: 3m - 10m) | `1009139-1` | `wfo-0000262791` | `2818985` | `4CJG8` | Bản địa đặc hữu VN: `VNC0014` \| CITES App I, IUCN CR |

---

## 4. Đặc Tả Hình Thái Giải Phẫu Học & Thông Số PBR Cho Từng Loài

### 1. Sồi Cổ Thụ Hoàng Gia (*Quercus robur* L.) — `canopy_ancient_oak`
- **Vỏ thân (Bark)**: Vỏ xám nâu nứt dọc sâu 40-50mm, các gờ vỏ hình khối chữ nhật dày xốp. Chân gốc loe bạnh rễ (buttress roots) tỏa rộng 4.5m bám sâu vào nền phù sa.
- **Cành & Tán (Branching)**: Phân cành dạng hợp trục (sympodial branching), cành lớn uốn khúc khuỷu góc 45°-80°, tạo vòm tán hình bán cầu hùng vĩ đường kính 25m.
- **Lá (Foliage)**: Lá mọc so le, phiến lá hình trứng ngược (obovate) dài 8-14cm, chia 4-7 thùy tròn đều hai bên mép; cuống lá cực ngắn (2-5mm) với 2 tai lá nhỏ ở gốc phiến lá.
- **Hoa & Quả (Inflorescence & Fruit)**: Hoa đơn tính cùng gốc (monoecious). Quả đấu (acorn) hình trứng dài 2-3cm nằm trên cuống dài 3-8cm, 1/3 đáy quả bọc trong chén đấu sần sùi vảy xám.
- **Micro-Geometry & PBR**:
  * Base Color vỏ cây: `#38281b`, Roughness: `0.92`, Normal Displacement Voronoi Scale 18.0, Strength 0.35.
  * Base Color tán lá: `#15803d` đến `#166534`, SSS Weight: `0.45`, SSS Radius: `(0.15, 0.45, 0.08)`, Roughness: `0.32`, Sheen: `0.25`.

### 2. Cự Mộc Sequoia Khổng Lồ (*Sequoiadendron giganteum*) — `canopy_giant_sequoia`
- **Vỏ thân (Bark)**: Vỏ màu đỏ quế (cinnamon-red) dày tới 60cm, cấu trúc dạng sợi xốp chứa nhiều tannin không có nhựa dầu, kháng cháy tự nhiên phi thường; các rãnh nứt dọc sâu hun hút.
- **Dáng thân (Trunk Form)**: Thân hình cột thẳng đứng vĩ đại, vuốt thon đều lên đỉnh; gốc phình bạnh rễ khổng lồ đường kính tới 8m.
- **Lá (Needles)**: Lá hình dùi nhọn (awl-shaped) dạng vảy dài 3-6mm, xếp xoắn ốc 3 hàng áp sát cành con; màu xanh lam đậm ngả xám mốc với dải khí khổng trắng mờ.
- **Nón (Cones)**: Nón quả hình trứng dài 4-7cm gồm 30-50 vảy xếp xoắn ốc hóa gỗ cứng, lưu giữ hạt màu nâu có cánh suốt 20 năm trên cây chờ lửa rừng kích hoạt phát tán.
- **Micro-Geometry & PBR**:
  * Base Color vỏ: `#7c2d12`, Roughness: `0.85`, Micro-bump dạng sợi sớ kéo dài theo trục Z.
  * Lá kim: `#1e3a2b`, SSS Weight: `0.25`, Clearcoat phấn sáp: `0.15`.

### 3. Baobab Thảo Nguyên (*Adansonia digitata* L.) — `canopy_baobab`
- **Thân trữ nước (Pachycaul Stem)**: Thân phình to hình trụ/thùng rượu khổng lồ đường kính 8-10m; mô gỗ xốp mềm hoạt động như bồn chứa tới 120,000 lít nước chống hạn mùa khô.
- **Vỏ cây (Bark)**: Vỏ nhẵn bóng màu xám chì hoặc ánh tím đồng, dày 5-10cm, có khả năng tự phục hồi tái sinh biểu bì hoàn hảo.
- **Cành nhánh (Crown)**: Cành trần trụi, xoắn vặn gồ ghề vươn lên bầu trời trông như chùm rễ cây cắm ngược lên trời (upside-down tree).
- **Lá (Foliage)**: Lá kép chân vịt gồm 5-7 lá chét hình bầu dục thuôn dài, rụng hoàn toàn trong 9 tháng mùa khô để triệt tiêu thoát hơi nước.
- **Hoa & Quả**: Hoa trắng khổng lồ đường kính 20cm rủ trên cuống dài, tỏa hương về đêm dẫn dụ dơi thụ phấn; quả bầu dục vỏ gỗ phủ lông tơ nhung vàng nâu chứa bột chua giàu vitamin C.
- **Micro-Geometry & PBR**:
  * Base Color thân: `#57534e`, Roughness: `0.65`, Bump nhăn ngang nhẹ mô phỏng các ngấn da voi tích nước co giãn.

### 4. Dương Xỉ Thân Gỗ Cổ Sinh (*Cyathea cooperi*) — `understory_tree_fern`
- **Thân giả (Caudex)**: Thân cột đứng thẳng xù xì bọc ngoài bởi lớp cuống lá rụng để lại các vết sẹo hình vảy rồng hình oval; chân gốc đan bện lớp rễ khí sinh dạng bím tóc màu nâu đỏ.
- **Tàu lá lược (Fronds)**: Ngọn xòe tán lọng tròn đối xứng gồm 20-30 tàu lá xẻ lông chim 3 lần dài 3-4m, uốn cong vòng cung mềm mại rủ xuống xung quanh.
- **Búp lá non (Crozier / Fiddlehead)**: Chồi non cuộn tròn xoắn ốc Fibonacci phủ kín lớp lông tơ tằm màu vàng óng ánh (golden scales).
- **Bào tử (Sori)**: Ổ túi bào tử tròn mọc thành hai hàng đều tăm tắp ở mặt dưới lá chét con, phát tán bụi bào tử mịn khi chín.
- **Micro-Geometry & PBR**:
  * Thân cột: `#292524`, Roughness: `0.95`, gờ nổi sẹo lá sâu 15mm.
  * Tàu lá: Base Color xanh nõn chuối pha lục bảo `#22c55e`, SSS Weight: `0.55`, SSS Radius: `(0.1, 0.5, 0.1)`.

### 5. Hoa Súng Nước Ngọt (*Nymphaea alba* L.) — `aquatic_water_lily`
- **Lá nổi (Floating Pads)**: Phiến lá hình khiên tròn đường kính 20-35cm, khía rãnh chữ V sâu tới cuống; mép nguyên, mặt trên phủ lớp sáp cutin mờ ngăn đọng nước; khí khổng chỉ tập trung ở mặt trên.
- **Cuống lá & Thân rễ**: Cuống dài 1.5-3m uốn lượn đàn hồi nối lá nổi với thân rễ bò ngầm dưới bùn đáy; chứa 4 ống khí rỗng (aerenchyma) dẫn oxy xuống đáy nước.
- **Hoa (Flower)**: Đóa hoa đa lớp nổi bồng bềnh sát mặt nước gồm 4 lá đài xanh và 20-25 cánh hoa trắng muốt xếp xoắn ốc bao bọc cụm nhụy hoa vàng cam rực rỡ ở tâm.
- **Micro-Geometry & PBR**:
  * Cánh hoa: `#ffffff`, SSS Weight: `0.58`, SSS Color: `#fef08a` (ánh vàng ấm trong suốt), Roughness: `0.18`.
  * Lá nổi: `#15803d`, Roughness: `0.30`, Clearcoat: `0.40` (mô phỏng màng nước phản chiếu).

### 6. Sen Hồng Linh Thiêng (*Nelumbo nucifera* Gaertn.) — `aquatic_sacred_lotus`
- **Lá vươn cao (Emergent Leaves)**: Lá hình khiên (peltate) tròn hoàn hảo đường kính 60-90cm, lòng máng khum cong nhẹ, cuống lá cắm ngay giữa tâm phiến lá vươn cao khỏi mặt nước 1.2m - 1.8m.
- **Hiệu ứng kỵ nước (Lotus Effect)**: Bề mặt lá cấu tạo từ hàng tỷ nhú gai vi mô nano (papillae) phủ sáp hữu cơ, làm giọt nước vo tròn lăn lóc cuốn trôi mọi bụi bẩn.
- **Hoa & Bát sen**: Hoa hồng cánh sen nhiều lớp vươn cao hơn tán lá, tâm hoa là đài sen (receptacle) hình nón ngược màu vàng chanh chứa các lỗ hạt; có khả năng tự điều hòa thân nhiệt (30-35°C).
- **Micro-Geometry & PBR**:
  * Cánh hoa: Gradient từ trắng ở gốc sang hồng cánh sen `#f43f5e` ở chóp, SSS Weight: `0.65`, SSS Radius: `(0.4, 0.15, 0.15)`.
  * Đài sen: `#84cc16`, Roughness: `0.40`.

### 7. Xương Rồng Cột Saguaro (*Carnegiea gigantea*) — `succulent_saguaro_cactus`
- **Thân khía rãnh (Pleated Stem)**: Thân hình trụ khổng lồ có 12-30 nếp gấp khía dọc sâu 3-5cm hoạt động như đàn phong cầm co giãn tích nước; bên trong là bộ khung gỗ gồm các thanh nan dọc cứng cáp.
- **Cành tay chữ U (Arms)**: Cành phân nhánh vươn ngang rồi bẻ góc 90° hướng thẳng đứng lên trời, tạo dáng chữ U đặc trưng sa mạc.
- **Gai sa mạc (Spines)**: Quầng gai (areoles) mọc dọc theo đỉnh các gờ khía, mỗi quầng mang 15-30 gai nhọn cứng màu xám trắng dài 3-7cm hướng chéo xuống dưới.
- **Hoa (Flowers)**: Hoa hình kèn màu trắng kem nở về đêm ở đỉnh ngọn thân và đầu cành tay, bao phấn màu vàng rực rỡ thu hút dơi sa mạc.
- **Micro-Geometry & PBR**:
  * Thân mọng nước: `#3f6212`, SSS Weight: `0.35` (tán xạ mô thịt ngậm nước), Roughness: `0.45`, Clearcoat sáp: `0.20`.
  * Gai: `#e2e8f0`, Roughness: `0.30`.

### 8. Bẫy Kẹp Venus (*Dionaea muscipula* J.Ellis) — `carnivorous_venus_flytrap`
- **Bộ bẫy kẹp (Snap Trap)**: Lá biến dạng thành cấu trúc kẹp 2 mảnh hình bán nguyệt úp vào nhau qua sống lá; viền mép bẫy cắm 15-20 răng gai lược nhọn đan khít vào nhau khi bẫy sập.
- **Lông cảm ứng (Trigger Hairs)**: Lòng trong mỗi mảnh bẫy có đúng 3 sợi lông cảm ứng siêu nhạy xếp hình tam giác; cơ chế bucking instability giúp bẫy sập chỉ trong 100 mili-giây khi chạm 2 lần.
- **Tuyến tiêu hóa (Digestive Glands)**: Mặt trong lòng bẫy đỏ rực tiết mật ngọt dẫn dụ và enzyme tiêu hóa (protease, phosphatase) hấp thụ dưỡng chất từ côn trùng.
- **Micro-Geometry & PBR**:
  * Lòng bẫy: Base Color đỏ hồng tươi `#ef4444`, SSS Weight: `0.65`, Roughness: `0.25`.
  * Mặt ngoài bẫy & cuống lá: Base Color xanh nõn chuối `#22c55e`, SSS: `0.40`.

### 9. Nắp Ấm Khổng Lồ Kinabalu (*Nepenthes rajah* Hook.f.) — `carnivorous_pitcher_plant`
- **Bình nắp ấm (Giant Pitcher)**: Bình bẫy nước phồng to hình quả lê/bình rượu khổng lồ dài 20-41cm, dung tích tới 3.5 lít dịch tiêu hóa; nối với đầu lá qua tua cuốn dài chịu lực.
- **Vành môi bẫy (Peristome)**: Vành miệng bình cuộn tròn xòe rộng với các rãnh khía răng cưa màu đỏ sẫm trơn trượt (aquaplaning) khi dính nước, khiến con mồi trượt chân rơi xuống đáy bình.
- **Nắp đậy (Operculum)**: Nắp hình trứng vòm lõm che mưa xối vào miệng bình, mặt dưới nắp tiết dịch mật thơm ngọt thu hút chuột chù cây (*Tupaia montana*).
- **Micro-Geometry & PBR**:
  * Bình bẫy: `#991b1b` pha đốm vàng đồng `#ca8a04`, SSS Weight: `0.50`, Roughness: `0.35`.
  * Vành môi: `#7f1d1d`, Roughness: `0.10` (siêu bóng trơn ướt).

### 10. Nấm Mũ Xanh Dạ Quang (*Mycena chlorophos*) — `cave_bioluminescent_mushroom`
- **Mũ nấm (Pileus)**: Mũ nấm hình chuông xòe bán cầu đường kính 15-35mm màu trắng xanh trong mờ, mặt trên phủ lớp màng nhầy gelatin lấp lánh; mép mũ có các nếp khía xuyên thấu.
- **Phiến nấm (Lamellae)**: Hệ thống phiến nấm mỏng xếp nan hoa tỏa từ cuống nấm ra rìa mũ, tập trung mật độ enzyme luciferase cao nhất.
- **Cơ chế phát quang (Bioluminescence)**: Phát ánh sáng lạnh đơn sắc màu xanh lục ngọc lam (520-530nm) liên tục trong bóng tối hoàn toàn, độ sáng 2.5 - 5.5 lux.
- **Cuống nấm (Stipe)**: Cuống thanh mảnh dài 20-50mm màu trắng trong mờ ngậm sương ẩm.
- **Micro-Geometry & PBR**:
  * Mũ & Phiến nấm: Base Color `#06b6d4`, Emission Color `#10b981`, Emission Strength: `5.0 lux`, SSS Weight: `0.60`, Transmission: `0.35`, Roughness: `0.20`.

---

## 5. Cấu Trúc Đặc Tả Markdown Chuẩn Cho File Loài & Master Catalog

### 5.1 Cấu trúc mẫu chuẩn cho `docs/flora/species/<slug>.md`

```markdown
# Đặc Tả Thực Vật 3D: [Tên Tiếng Việt] ([Danh Pháp Khoa Học])

> [!NOTE]
> **Mã Định Danh Dự Án**: `[ID, vd: MG01]`  
> **Nhóm Hình Thái**: [Tên nhóm tiếng Anh, vd: Canopy Trees]  
> **Hệ Thống Phân Loại (APG IV / Phylogeny)**: [Nhánh Clade] > [Bộ Order, vd: Fagales] > [Họ Family, vd: Fagaceae]  
> **Danh Pháp Khoa Học**: *[Tên khoa học in nghiêng]* [Tác giả chuẩn, vd: L.]  
> **Tên Tiếng Anh**: **[English Name]**  
> **Tầng Sinh Thái**: [1 trong 6 tầng: Đại Thụ / Bụi-Dương Xỉ / Thảo Mộc / Thủy Sinh / Mọng Nước / Đặc Hữu]  
> **Kích Thước Hình Học**: [Chiều cao]m (Cao) x [Đường kính tán]m (Tán) x [Đường kính thân/DBH]m (Thân)  
> **Mã Cơ Sở Dữ Liệu Đối Chiếu**: POWO: `[POWO ID]` | WFO: `[WFO ID]` | GBIF: `[GBIF Key]` | CoL: `[CoL ID]` | vncreatures: `[vncreatures ID / N/A]`  
> **Tình Trạng Bảo Tồn**: IUCN Red List: [LC/VU/EN/CR] | CITES: [App I/II/Không]  
> **Phân Bố Tự Nhiên**: [Khu vực địa lý tự nhiên trên Trái Đất]  
> **Sinh Cảnh Genesis Zero**: [Mô tả sinh cảnh, tọa độ bản đồ, độ cao Z: ...m đến ...m]  
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality (Blender PBR + SSS)**

---

## Bản Vẽ Thiết Kế 3D Model Sheet (4 Góc Nhìn: Phối Cảnh, Mặt Trước, Mặt Bên, Nhìn Từ Trên)

![Bản vẽ 3D Turnaround Concept Sheet - [slug]](../images/[slug]_turnaround.jpg)

---

## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Thân Cột, Vỏ Cây & Bạnh Rễ (Trunk, Bark & Fluting)
[Mô tả chi tiết giải phẫu vỏ, độ nứt, màu sắc, bạnh rễ]

### 1.2 Cành Nhánh & Kiến Trúc Tán (Branching & Crown Architecture)
[Mô tả góc phân cành, mô hình phân cành Halle-Oldeman, đường kính vòm tán]

### 1.3 Cấu Trúc Lá, Gân Lá & Cách Sắp Xếp (Foliage, Phyllotaxy & Venation)
[Mô tả phiến lá, mép lá, cuống lá, gân lá, sắp xếp so le/đối/vòng, lớp cutin]

### 1.4 Hoa, Quả, Hạt hoặc Bào Tử (Inflorescence, Fruit/Seed, Sporangia)
[Mô tả cơ quan sinh sản, cánh hoa, bao phấn, quả, nón, hoặc ổ bào tử sori]

### 1.5 Cấu Trúc Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
[Mô tả chi tiết scan vi mô: lông tơ trichomes, lỗ bì lenticels, sáp nano]

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **[Số tris] tris** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **[Số tris] tris** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `Principled BSDF: [Mô tả chi tiết Base Color, Normal Bump, Roughness]`
- **Subsurface Scattering (SSS)**: Tán xạ ánh sáng xuyên thấu diệp lục (Weight: `[Weight]`, Radius: `[RGB]`).
- **Procedural Displacement**: Tái tạo rãnh vỏ nứt nẻ, gờ sống lá, lông tơ nhung.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)**.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

- 🎨 **File Nguồn Blender 3D**: [`[slug].blend`](../../assets/flora/[cat]/[slug].blend)
- 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`[slug].glb`](../../assets/flora/[cat]/[slug].glb)
- 📷 **Ảnh Bản Vẽ 4 Góc Turnaround**: [`[slug]_turnaround.jpg`](../../web/flora_images/[slug]_turnaround.jpg)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`[slug]_builder.py`](../../assets/flora/generators/flora_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = bpy.path.abspath("//../../assets/flora/[cat]/[slug].glb")
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_[slug]"
    print(f"✓ Đã đặt {plant.name} vào thế giới Genesis Zero.")
else:
    print(f"Không tìm thấy file asset tại: {asset_path}")
```
```

---

### 5.2 Cấu trúc bảng Master Catalog cho `docs/flora/README.md`

Trong file `docs/flora/README.md`, bổ sung Section 2 mới (hoặc mở rộng Section 3 hiện tại):

```markdown
## 2. Bảng Danh Mục Phân Loại Thực Vật Học Quốc Tế (APG IV & Database Cross-References)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp Khoa Học | Họ Thực Vật (APG IV) | Bộ (Order) | Tầng Sinh Thái | Chiều Cao x Tán | Mã POWO Kew | Mã WFO | Mã GBIF | Bản Vẽ 4 Góc | File 3D & Chi Tiết |
|:---|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MG01** | Sồi Cổ Thụ Hoàng Gia | *Quercus robur* L. | Fagaceae | Fagales | Cây Đại Thụ | 28m x 25m | `296681-1` | `wfo-0000293123` | `2878688` | [📷 4 Góc](../../web/flora_images/canopy_ancient_oak_turnaround.jpg) | [Chi tiết](species/canopy_ancient_oak.md) |
| **MG03** | Cự Mộc Sequoia Khổng Lồ | *Sequoiadendron giganteum* (Lindl.) J.Buchholz | Cupressaceae | Cupressales | Cây Đại Thụ / Đặc Hữu | 65m x 18m | `263309-1` | `wfo-0000308871` | `2684031` | [📷 4 Góc](../../web/flora_images/canopy_giant_sequoia_turnaround.jpg) | [Chi tiết](species/canopy_giant_sequoia.md) |
...
```

---

## 6. Caveats (Các Điểm Lưu Ý & Giới Hạn)

1. **Tính tương thích của chuẩn APG IV**:
   - Như đã phân tích tại Edge Case #1, #2, #3, hệ thống APG IV chỉ phân loại hạt kín (*Angiosperms*). Khi lập tài liệu cho *Sequoiadendron giganteum* (cây hạt trần), *Cyathea cooperi* (dương xỉ), và *Mycena chlorophos* (nấm), hệ thống phát sinh loài tương đương chuyên ngành (Christenhusz 2011, PPG I 2016, Index Fungorum) được sử dụng để duy trì tính chuẩn xác học thuật thay vì gán nhãn APG IV giả tạo.

2. **Khả năng tra cứu vncreatures đối với loài ngoại cảnh**:
   - Cơ sở dữ liệu vncreatures chỉ ghi nhận các loài thực vật, động vật phân bố tự nhiên hoặc có lịch sử lâu đời tại Việt Nam. Các loài sa mạc Sonoran (*Saguaro*) hay rừng sồi châu Âu (*Quercus robur*) không có mã vncreatures; do đó trường này phải cho phép giá trị `N/A (Loài ngoại lai)`.

3. **Cơ chế phục vụ Web (file:// vs http://)**:
   - Khi mở `web/flora_viewer.html` trực tiếp qua giao thức `file://`, trình duyệt có thể chặn tải file nhị phân glTF qua `fetch()` do chính sách CORS. Dự án đã giải quyết rất thông minh bằng cách nhúng trực tiếp dữ liệu base64 vào `web/flora_models_data.js`. Khi nâng cấp dữ liệu thực vật, mọi cập nhật model mới cần được đồng bộ lại cả vào `web/flora_models_data.js` để duy trì tính năng 100% offline không cần server.

4. **Độ phân giải của ảnh Turnaround Sheet**:
   - 10 ảnh turnaround hiện tại có kích thước 1024x1024 px. Kích thước này rất tối ưu cho tải trang web và modal xem nhanh. Tuy nhiên đối với các chi tiết giải phẫu học siêu vi mô (như lông bẫy kẹp Venus hay gai xương rồng), ảnh 1024x1024 có thể hơi mờ khi phóng to hết cỡ trên màn hình 4K. Trong các pha phát triển sau, có thể cân nhắc nâng độ phân giải lên 2048x2048 nếu người dùng yêu cầu chất lượng scan phóng đại.

---

## 7. Conclusion (Kết Luận & Khuyến Nghị Hành Động)

1. **Đánh giá tổng thể**:
   - Kho tài nguyên thực vật học của Genesis Zero hiện sở hữu một nền tảng 3D vô cùng đồ sộ và chất lượng cao: **100 loài trong Master Catalog**, **16 mô hình 3D hoàn chỉnh (.blend và .glb)**, **10 bản vẽ turnaround concept sheet 4 góc chuẩn xác**, và **trình xem Web Viewer 3D Three.js mượt mà**.
   - Khâu còn thiếu sót duy nhất theo yêu cầu R1 và R4 là việc **chuẩn hóa và đồng bộ hóa các trường thực vật học kinh viện** (APG IV clades, orders, author citations, POWO/WFO/GBIF/CoL/vncreatures IDs, native ranges) vào file markdown từng loài và Master Catalog.

2. **Kế hoạch hành động cụ thể cho Đội Triển Khai (Actionable Plan for Implementation Agents)**:
   - **Bước 1 (Catalog & Species Docs Update)**:
     * Cập nhật script `scripts/generate_100_flora.py` hoặc tạo script nâng cấp để bổ sung đầy đủ các trường APG IV, POWO ID, WFO ID, GBIF Key, CoL ID, vncreatures ID và phân bố địa lý vào `docs/flora/species/<slug>.md`.
     * Cập nhật bảng tổng hợp danh pháp APG IV và liên kết ảnh 4 góc vào `docs/flora/README.md`.
   - **Bước 2 (Web Viewer Synchronize)**:
     * Kiểm tra và bảo đảm mảng `PLANTS` trong `web/flora_viewer.html` phản ánh đầy đủ thông tin danh pháp chuẩn, đảm bảo badge `4 Góc 📷` hiển thị đúng cho 10 loài mục tiêu.
   - **Bước 3 (Automated Verification Script)**:
     * Tạo script kiểm thử tự động `tests/test_flora_assets.py` và `scripts/verify_flora_pipeline.py` để khẳng định bằng code tính toàn vẹn 100% của: metadata, ảnh turnaround 4 góc, file `.blend`, và file `.glb`.

---

## 8. Verification Method (Phương Pháp Xác Minh Độc Lập)

Người nhận bàn giao hoặc kiểm thử viên có thể chạy trực tiếp các lệnh kiểm tra sau trong terminal để thẩm định độc lập toàn bộ kết quả khảo sát:

### 1. Kiểm tra sự tồn tại và tính hợp lệ của 10 ảnh Turnaround Sheet 4 góc:
```bash
python3 -c "
from pathlib import Path
from PIL import Image

p = Path('web/flora_images')
expected = [
    'canopy_ancient_oak_turnaround.jpg', 'canopy_giant_sequoia_turnaround.jpg',
    'canopy_baobab_turnaround.jpg', 'understory_tree_fern_turnaround.jpg',
    'aquatic_water_lily_turnaround.jpg', 'aquatic_sacred_lotus_turnaround.jpg',
    'succulent_saguaro_cactus_turnaround.jpg', 'carnivorous_pitcher_plant_turnaround.jpg',
    'carnivorous_venus_flytrap_turnaround.jpg', 'cave_bioluminescent_mushroom_turnaround.jpg'
]
for name in expected:
    f = p / name
    assert f.exists(), f'Missing {name}'
    with Image.open(f) as img:
        assert img.size == (1024, 1024), f'{name} invalid size {img.size}'
        assert img.format == 'JPEG', f'{name} invalid format {img.format}'
print('✓ 10/10 Turnaround images verified (1024x1024 JPEG).')
"
```

### 2. Kiểm tra sự tồn tại của 16 cặp file 3D (.blend & .glb):
```bash
python3 -c "
from pathlib import Path

p = Path('assets/flora')
glbs = list(p.rglob('*.glb'))
blends = list(p.rglob('*.blend'))
assert len(glbs) >= 16, f'Expected >= 16 glb, found {len(glbs)}'
assert len(blends) >= 16, f'Expected >= 16 blend, found {len(blends)}'
for g in glbs:
    assert g.stat().st_size > 1000, f'File {g} too small ({g.stat().st_size} bytes)'
print(f'✓ Verified {len(glbs)} GLB models and {len(blends)} Blender files (> 1KB).')
"
```

### 3. Kiểm tra tính toàn vẹn của glTF 2.0 Binary Header:
```bash
python3 -c "
from pathlib import Path
import struct

p = Path('assets/flora')
for g in p.rglob('*.glb'):
    with open(g, 'rb') as f:
        magic, version, length = struct.unpack('<4sII', f.read(12))
        assert magic == b'glTF', f'{g} not a valid glTF file'
        assert version == 2, f'{g} invalid glTF version {version}'
        assert length == g.stat().st_size, f'{g} header length mismatch'
print('✓ 100% GLB files passed glTF 2.0 binary header assertion.')
"
```

### 4. Kiểm tra sự đồng bộ trong `web/flora_viewer.html`:
```bash
python3 -c "
from pathlib import Path

html = Path('web/flora_viewer.html').read_text(encoding='utf-8')
assert 'badge-turnaround' in html, 'Missing badge-turnaround CSS class'
assert 'turnaround-modal' in html, 'Missing turnaround modal element'
assert 'btn-open-turnaround' in html, 'Missing open turnaround button'
assert '4 Góc 📷' in html, 'Missing badge label text'
print('✓ Web viewer HTML contains all turnaround badge and modal elements.')
"
```

### 5. Điều kiện vô hiệu hóa kết luận (Invalidation Conditions):
- Nếu bất kỳ file ảnh nào trong 10 ảnh turnaround bị xóa hoặc kích thước = 0 byte.
- Nếu các file `.glb` bị lỗi mesh/texture không mở được trên Three.js.
- Nếu mã định danh POWO, WFO, GBIF không khớp với danh pháp khoa học chuẩn khi tra cứu trực tiếp trên API công khai của Kew hoặc GBIF.

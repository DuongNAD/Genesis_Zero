# Danh Mục Thực Vật Toàn Diện (Master Botanical Catalog) — Genesis Zero

> [!IMPORTANT]
> **Quy Chuẩn Thẩm Mỹ**: **Hyper-Realistic Scan-Quality**  
> Toàn bộ 100 loài thực vật được phân loại khoa học theo chuẩn thực vật học quốc tế (APG IV), tích hợp đầy đủ thông số giải phẫu hình thái, độ cong Fibonacci, vi mô mô tế bào, lưới Quads Manifold 100% Smooth Shading và hệ thống vật liệu sinh học PBR (Subsurface Scattering, Procedural Bark Displacement, Transmission & Bioluminescence).

> [!TIP]
> **Trình Xem Thực Vật 3D Trực Quan (Interactive 3D Flora Viewer)**  
> Trải nghiệm và kiểm tra trực quan các mô hình 3D Blender ngay trên trình duyệt với đầy đủ góc xoay 360°, chế độ hiển thị ánh sáng Studio / Hoàng hôn / Đêm phát quang, kiểm tra lưới Wireframe và tải trực tiếp file `.blend` & `.glb`:  
> 🌐 **Mở Web Viewer**: [web/flora_viewer.html](../../web/flora_viewer.html) (hoặc truy cập `http://localhost:8000/watch/flora_viewer.html` khi bật server).

---

## 1. Tổng Quan Thống Kê Thư Viện 100 Loài Thực Vật

- **Tổng số loài được lập đặc tả**: **100 loài thực vật hoàn chỉnh**.
- **Số nhóm sinh thái đại diện**: **8 nhóm phân tầng toàn diện**.
- **Số file đặc tả kỹ thuật độc lập**: **100 file Markdown** tại `docs/flora/species/`.
- **Hệ thống liên kết kép**: Mỗi loài liên kết trực tiếp tới file model 3D nguồn `.blend` và file game engine `.glb`.

```
========================================================================================================================
                                    GENESIS ZERO — 100 FLORA SPECIES TAXONOMY
========================================================================================================================
 1. Cỏ, Rêu & Thảm Đất (12 loài)  : Red Fescue, Tussock, Feather Grass, Velvet Moss, Clover, Sheep Fescue, Sphagnum...
 2. Thảo Mộc & Hoa Dại (14 loài)   : Daisy, Bluebell, Lavender, Dandelion, Poppy, Sunflower, Coneflower, Snowdrop...
 3. Cây Bụi & Dương Xỉ (14 loài)   : Sword Fern, Tree Fern, Lingonberry, Alpine Rose, Elderberry, Blackberry, Bamboo...
 4. Cây Gỗ Tầng Trung (14 loài)    : Silver Birch, Red Maple, Willow, Jungle Palm, Cherry, Eucalyptus, Cypress, Ginkgo...
 5. Đại Thụ Cổ Thụ (12 loài)       : Royal Oak, Alpine Pine, Redwood Sequoia, Baobab, Banyan, Cedar of Lebanon, Bodhi...
 6. Thủy Sinh & Đầm Lầy (12 loài) : Water Lily, Lotus, Wetland Reed, Cattail, Hornwort, Eelgrass, Victoria Amazonica...
 7. Khô Hạn & Mọng Nước (12 loài)  : Saguaro, Cape Aloe, Agave, Prickly Pear, Tumbleweed, Desert Rose, Living Stones...
 8. Ăn Thịt & Hang Động (12 loài)  : Pitcher Plant, Venus Flytrap, Sundew, Jungle Liana, Ghost Mushroom, Cobra Lily...
========================================================================================================================
```

---

## 2. Bảng Tổng Hợp Đối Chiếu Danh Pháp APG IV & Cơ Sở Dữ Liệu Quốc Tế

| Mã | Tên Tiếng Việt | Danh Pháp Khoa Học | Phân Loại APG IV (Họ/Bộ) | Tầng Sinh Thái | Kích Thước | POWO ID | WFO ID | GBIF Key | CoL ID | vncreatures ID / IUCN | Ảnh 4 Góc (Link) |
|:---:|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MG01** | Sồi Cổ Thụ Hoàng Gia | *Quercus robur* L. | Fagaceae / Fagales | Cây Đại Thụ (Canopy) | 28m x 25m | `296681-1` | `wfo-0000293123` | `2878688` | `4QVD4` | N/A \| IUCN LC | [📷 4 Góc](../../web/flora_images/canopy_ancient_oak_turnaround.jpg) |
| **MG03** | Cự Mộc Sequoia Đỏ Bất Tử | *Sequoiadendron giganteum* (Lindl.) J.Buchholz | Cupressaceae / Cupressales | Cây Đại Thụ / Đặc Hữu | 65m x 18m | `263309-1` | `wfo-0000308871` | `2684031` | `4WS8F` | N/A \| IUCN EN | [📷 4 Góc](../../web/flora_images/canopy_giant_sequoia_turnaround.jpg) |
| **MG04** | Baobab Bầu Nước Châu Phi | *Adansonia digitata* L. | Malvaceae / Malvales | Cây Đại Thụ (Savanna) | 20m x 22m | `558628-1` | `wfo-0000520448` | `3152222` | `9X2N` | N/A \| IUCN NT | [📷 4 Góc](../../web/flora_images/canopy_baobab_turnaround.jpg) |
| **SH02** | Dương Xỉ Thân Gỗ Cổ Sinh | *Cyathea cooperi* (F.Muell.) Domin | Cyatheaceae / Cyatheales | Cây Bụi & Dương Xỉ | 6.5m x 5.5m | `17068550-1` | `wfo-0001112442` | `7299946` | `32PRK` | Chi *Cyathea* bản địa VN (VNC0422) \| IUCN LC | [📷 4 Góc](../../web/flora_images/understory_tree_fern_turnaround.jpg) |
| **AQ01** | Hoa Súng Trắng Nước Ngọt | *Nymphaea alba* L. | Nymphaeaceae / Nymphaeales | Thủy Sinh & Đầm Lầy | 0.2m x 1.8m | `605417-1` | `wfo-0000473523` | `2882443` | `486CP` | Chi *Nymphaea* bản địa VN \| IUCN LC | [📷 4 Góc](../../web/flora_images/aquatic_water_lily_turnaround.jpg) |
| **AQ02** | Sen Hồng Cổ Điển Hoàng Cung | *Nelumbo nucifera* Gaertn. | Nelumbonaceae / Proteales | Thủy Sinh & Đầm Lầy | 1.6m x 1.4m | `605335-1` | `wfo-0000473489` | `2888881` | `467R8` | Bản địa Việt Nam (VNC0198) \| IUCN LC | [📷 4 Góc](../../web/flora_images/aquatic_sacred_lotus_turnaround.jpg) |
| **SC01** | Xương Rồng Cột Saguaro Cổ Thụ | *Carnegiea gigantea* (Engelm.) Britton & Rose | Cactaceae / Caryophyllales | Sa Mạc & Mọng Nước | 12m x 3.4m | `62495-2` | `wfo-0000587219` | `3084347` | `5X9TC` | N/A \| CITES App II, IUCN LC | [📷 4 Góc](../../web/flora_images/succulent_saguaro_cactus_turnaround.jpg) |
| **EX02** | Bẫy Kẹp Venus Răng Cưa | *Dionaea muscipula* J.Ellis | Droseraceae / Caryophyllales | Cây Bắt Mồi / Đặc Hữu | 0.25m x 0.35m | `321332-1` | `wfo-0000650965` | `3190710` | `36CDQ` | N/A \| CITES App II, IUCN VU | [📷 4 Góc](../../web/flora_images/carnivorous_venus_flytrap_turnaround.jpg) |
| **EX01** | Cây Bắt Mồi Nắp Ấm Khổng Lồ | *Nepenthes rajah* Hook.f. | Nepenthaceae / Caryophyllales | Cây Đặc Hữu / Ăn Thịt | 3.5m x 1.5m | `603798-1` | `wfo-0000418381` | `3702131` | `46XBL` | Chi *Nepenthes* bản địa VN (VNC0318) \| CITES App I, IUCN EN | [📷 4 Góc](../../web/flora_images/carnivorous_pitcher_plant_turnaround.jpg) |
| **EX05** | Nấm Mũ Xanh Dạ Quang Hang Karst | *Mycena chlorophos* (Berk. & M.A.Curtis) Sacc. | Mycenaceae / Agaricales | Hang Động Phát Quang | 0.85m x 0.95m | IndexFungorum `198547` | Mycobank `MB198547` | `2527097` | `44TB3` | Nấm hang bản địa châu Á \| NE | [📷 4 Góc](../../web/flora_images/cave_bioluminescent_mushroom_turnaround.jpg) |
| **FL01** | Cúc Vàng Đồng Nội | *Leucanthemum vulgare* Lam. | Asteraceae / Asterales | Thảo Mộc & Hoa Dại | 0.65m x 0.4m | `230006-1` | `wfo-0000078028` | `3142270` | `3TB6F` | N/A \| IUCN LC | [Chi tiết](species/flower_oxeye_daisy.md) |
| **ED01** | Lan Hài Việt Nam | *Paphiopedilum vietnamense* O.Gruss & Perner | Orchidaceae / Asparagales | Cây Đặc Hữu Việt Nam | 0.35m x 0.45m | `1009139-1` | `wfo-0000262791` | `2818985` | `4CJG8` | Bản địa đặc hữu VN: `VNC0014` \| CITES App I, IUCN CR | [Chi tiết](species/endemic_paphiopedilum_vietnamense.md) |

---

## 3. Tiêu Chuẩn 3D Hyper-Realistic Scan-Quality

1. **Topology Quad Manifold**: 100% sạch nếp ngắt, không có mặt lật ngược normal, không có ngons (đa giác > 4 đỉnh), góc cạnh uốn cong hữu cơ tự nhiên.
2. **Smooth Shading Bắt Buộc**: Áp dụng `use_smooth = True` trên 100% các mặt polygon để loại bỏ triệt để hiện tượng vát phẳng thô cứng.
3. **Subsurface Scattering (SSS) Chuyên Sâu**:
   - Tán lá, cánh hoa và thân mọng nước được cấu hình thông số tán xạ ngầm (Subsurface Radius & Weight) chính xác theo độ dày tế bào thực tế.
   - Khi có ánh sáng mặt trời chiếu xiên hoặc ngược sáng (backlighting), phiến lá bừng sáng thấu quang chân thực như ảnh chụp vĩ mô tự nhiên.
4. **Vỏ Cây & Thân Gỗ Procedural Micro-Displacement**:
   - Tích hợp mạng Procedural Texture (Voronoi + Noise kết hợp) để sinh rãnh nứt nẻ gồ ghề sâu 5mm - 40mm mà không làm nặng số đỉnh hiển thị.
   - Thêm lớp địa y và rêu phong ẩm ướt ở chân gốc cổ thụ tạo chiều sâu hàng trăm năm tuổi.

---

## 4. Bảng Chi Tiết 100 Loài Thực Vật Theo Từng Nhóm Sinh Thái

### Họ Cỏ, Rêu & Thảm Mặt Đất (Grasses, Mosses & Groundcovers) (12 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **GR01** | Cỏ Lúa Mì Đỏ Đồng Hoang | *Festuca rubra* | Red Fescue Grass | 0.4m (Cao) x 0.35m (Tán) | Đồng cỏ, Thảo nguyên đồi thấp (Z: 4m - 10m) | Lá dạng sợi thanh mảnh mọc thành cụm búi dày đặc. Đầu ngọn lá có ... | [Chi tiết](species/grass_red_fescue.md) |
| **GR02** | Cỏ Tussock Núi Cao | *Chionochloa rigida* | Alpine Tussock Grass | 0.85m (Cao) x 0.75m (Tán) | Đỉnh núi tuyết, Khô lạnh gió rét (Z: 12m - 20m) | Búi cỏ vòm tròn hình cầu rậm rạp, các dải lá già khô vàng rơm uốn... | [Chi tiết](species/grass_alpine_tussock.md) |
| **GR03** | Cỏ Đuôi Chuột Lông Vũ | *Stipa pennata* | Feather Grass | 0.95m (Cao) x 0.55m (Tán) | Thảo nguyên đón gió, Triền đồi cát (Z: 5m - 12m) | Thân mảnh mai vươn thẳng, đầu ngọn mang chùm bông tơ dài mềm mại ... | [Chi tiết](species/grass_feather_grass.md) |
| **GR04** | Thảm Rêu Nhung Rừng Ẩm | *Bryophyta saxatilis* | Velvet Forest Moss | 0.06m (Cao) x 1.4m (Tán phủ) | Chân cổ thụ, Vách đá bóng râm, Bờ suối (Z: 2m - 8m) | Thảm rêu xanh lục bảo xốp dày trải dài theo địa hình gồ ghề, mọc ... | [Chi tiết](species/grass_velvet_moss.md) |
| **GR05** | Cỏ Ba Lá May Mắn | *Trifolium repens* | White Clover | 0.18m (Cao) x 0.45m (Tán) | Bãi cỏ xanh, Bìa rừng, Lối đi ẩm (Z: 3m - 8m) | Cuống mảnh uốn lượn mang bộ 3 lá chét hình tim ngược, mặt lá có v... | [Chi tiết](species/grass_white_clover.md) |
| **GR06** | Cỏ Lông Nhím Rừng Đá | *Festuca ovina* | Sheep's Fescue | 0.32m (Cao) x 0.28m (Tán) | Khe đá núi vôi, Sườn sỏi khô cằn (Z: 8m - 16m) | Bụi cỏ gai nhọn xòe tròn như lưng nhím, lá cuộn tròn hình kim màu... | [Chi tiết](species/grass_sheeps_fescue.md) |
| **GR07** | Thảm Rêu Râu Bạc Vách Đá | *Racomitrium lanuginosum* | Woolly Fringe Moss | 0.08m (Cao) x 0.9m (Tán) | Vách đá phong hóa, Đỉnh núi sương mù (Z: 14m - 22m) | Mọc thành mảng đệm xốp phủ trên mặt đá granit gồ ghề. Đỉnh mỗi ch... | [Chi tiết](species/grass_woolly_moss.md) |
| **GR08** | Cỏ Đuôi Phụng Thảo Nguyên | *Panicum virgatum* | Switchgrass | 1.6m (Cao) x 0.8m (Tán) | Đồng bằng trung tâm, Bờ suối cạn (Z: 4m - 9m) | Thân cỏ cao thẳng đứng mọc thành cụm bụi lớn, mùa thu đổi sang sắ... | [Chi tiết](species/grass_switchgrass.md) |
| **GR09** | Rêu Than Bùn Đầm Lầy | *Sphagnum palustre* | Sphagnum Peat Moss | 0.15m (Cao) x 1.6m (Mảng phủ) | Vùng đầm lầy trũng, Bờ than bùn (Z: 3.5m - 5m) | Cây rêu phân nhánh hình đầu cúc tròn, chứa các tế bào rỗng ngậm n... | [Chi tiết](species/grass_sphagnum_moss.md) |
| **GR10** | Cỏ May Xước Đồng Hoang | *Chrysopogon aciculatus* | Needle Burr Grass | 0.35m (Cao) x 0.4m (Tán) | Lối mòn khô cằn, Vùng chân núi (Z: 5m - 11m) | Thân bò lan bám rễ chặt chẽ dưới đất, phóng các cọng hoa mang chù... | [Chi tiết](species/grass_needle_burr.md) |
| **GR11** | Cỏ Mần Trầu Dược Liệu | *Eleusine indica* | Wiregrass / Goosegrass | 0.45m (Cao) x 0.5m (Tán xòe) | Vành đai làng, Bãi cỏ sinh hoạt (Z: 4m - 8m) | Gốc phân nhánh tỏa tròn sát mặt đất như nan hoa xe bò, cọng hoa d... | [Chi tiết](species/grass_goosegrass.md) |
| **GR12** | Rêu Rồng Xanh Vách Thác | *Marchantia polymorpha* | Umbrella Liverwort | 0.04m (Cao) x 0.8m (Mảng phiến) | Vách đá ẩm cạnh thác nước đổ (Z: 2m - 7m) | Tản lá hình dải xanh đậm chia thùy như vảy rồng bám chặt mặt đá ư... | [Chi tiết](species/grass_liverwort.md) |

### Thảo Mộc & Hoa Rừng Hoang Dã (Wildflowers & Forest Herbs) (14 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **FL01** | Cúc Vàng Đồng Nội | *Leucanthemum vulgare* | Oxeye Daisy | 0.65m (Cao) x 0.4m (Tán) | Thung lũng ngập nắng, Đồng cỏ ven suối (Z: 4m - 9m) | Thân đứng có khía dọc, lá xẻ thùy răng cưa thưa. Đóa hoa đơn độc ... | [Chi tiết](species/flower_oxeye_daisy.md) |
| **FL02** | Hoa Chuông Xanh Rừng Rậm | *Hyacinthoides non-scripta* | English Bluebell | 0.48m (Cao) x 0.32m (Tán) | Tán rừng sồi ẩm râm mát (Z: 5m - 9m) | Cành hoa cong uốn cong một bên duyên dáng, mang 6-12 đóa hoa hình... | [Chi tiết](species/flower_bluebell.md) |
| **FL03** | Oải Hương Tím Dại | *Lavandula angustifolia* | Wild Lavender | 0.72m (Cao) x 0.65m (Tán) | Sườn đồi đá vôi khô nhiều nắng (Z: 6m - 14m) | Bụi bán mộc thân gốc hóa gỗ, cành non vuông vức màu xám xanh mang... | [Chi tiết](species/flower_wild_lavender.md) |
| **FL04** | Bồ Công Anh Bào Tử Gió | *Taraxacum officinale* | Dandelion Spore | 0.38m (Cao) x 0.26m (Tán) | Bãi cỏ nắng, Lối mòn, Đồng nội (Z: 3m - 10m) | Cuống rỗng vươn thẳng từ vòng lá sát đất hình răng sư tử. Đỉnh ma... | [Chi tiết](species/flower_dandelion.md) |
| **FL05** | Bạc Hà Rừng Hoang Dã | *Mentha arvensis* | Wild Corn Mint | 0.52m (Cao) x 0.38m (Tán) | Rìa suối ẩm, Đầm lầy cỏ (Z: 3m - 7m) | Thân 4 cạnh vuông vức màu phớt tím, lá mọc đối chéo chữ thập có r... | [Chi tiết](species/flower_wild_mint.md) |
| **FL06** | Hoa Anh Túc Lửa Hoang | *Papaver rhoeas* | Corn Poppy | 0.75m (Cao) x 0.35m (Tán) | Cánh đồng ngập nắng, Triền dốc cát (Z: 4m - 11m) | Cuống hoa mảnh uốn lượn có lông châm tơ trắng dựng đứng, mang nụ ... | [Chi tiết](species/flower_corn_poppy.md) |
| **FL07** | Bách Hợp Thung Lũng Trắng | *Convallaria majalis* | Lily of the Valley | 0.26m (Cao) x 0.22m (Tán) | Dưới bóng râm cây cổ thụ, Đất mùn rừng (Z: 4m - 8m) | Hai lá gốc lớn hình bầu dục bóng mượt bao bọc cuống hoa mảnh mai ... | [Chi tiết](species/flower_lily_valley.md) |
| **FL08** | Hoa Hướng Dương Dại | *Helianthus annuus* | Wild Prairie Sunflower | 1.85m (Cao) x 0.75m (Tán) | Đồng cỏ hoang dã ngập nắng (Z: 5m - 10m) | Thân thô ráp có lông cứng ráp, mang lá hình tim lớn ráp nhám. Đỉn... | [Chi tiết](species/flower_wild_sunflower.md) |
| **FL09** | Hoa Cúc Tím Echinacea | *Echinacea purpurea* | Purple Coneflower | 1.1m (Cao) x 0.5m (Tán) | Thảo nguyên đón nắng, Bìa rừng sỏi (Z: 4m - 9m) | Thân thẳng cứng cáp mang đóa hoa có tâm hình nón nhô cao như tổ o... | [Chi tiết](species/flower_purple_coneflower.md) |
| **FL10** | Cây Hoa Bìm Bìm Rừng | *Ipomoea purpurea* | Morning Glory | 2.2m (Leo dài) x 0.8m (Tán) | Bờ rào đá làng, Bụi rậm ven suối (Z: 3m - 7m) | Dây leo cuốn uốn lượn mang lá hình tim xanh mướt. Sáng sớm bung n... | [Chi tiết](species/flower_morning_glory.md) |
| **FL11** | Hoa Phong Lữ Dại Rừng Sồi | *Geranium maculatum* | Wild Geranium | 0.55m (Cao) x 0.45m (Tán) | Dưới tán rừng râm mát, Đất mùn (Z: 4m - 8m) | Lá xẻ thùy chân vịt sâu 5 nhánh răng cưa nhọn, hoa 5 cánh màu hồn... | [Chi tiết](species/flower_wild_geranium.md) |
| **FL12** | Cây Xương Bồ Thơm Bờ Suối | *Acorus calamus* | Sweet Flag | 0.9m (Cao) x 0.6m (Tán) | Bờ suối sỏi đá, Rãnh nước nông (Z: 3m - 5m) | Lá dài hình lưỡi kiếm màu xanh bóng có gân giữa nổi rõ, tỏa hương... | [Chi tiết](species/flower_sweet_flag.md) |
| **FL13** | Cây Ngải Đắng Rừng | *Artemisia absinthium* | Wormwood | 1.0m (Cao) x 0.7m (Tán) | Đồi khô sỏi đá, Vùng nắng gắt (Z: 6m - 12m) | Cây bán bụi màu trắng bạc tro do toàn thân và lá xẻ nhiều lần phủ... | [Chi tiết](species/flower_wormwood.md) |
| **FL14** | Hoa Giọt Tuyết Đầu Xuân | *Galanthus nivalis* | Common Snowdrop | 0.18m (Cao) x 0.15m (Tán) | Băng tuyết tan, Bìa rừng mùa xuân (Z: 8m - 15m) | Vươn mình xuyên qua lớp tuyết trắng lạnh giá, cuống hoa cong hình... | [Chi tiết](species/flower_snowdrop.md) |

### Cây Bụi & Dương Xỉ Tầng Dưới (Understory Shrubs & Ferns) (14 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **SH01** | Dương Xỉ Kiếm Khổng Lồ | *Polystichum munitum* | Western Sword Fern | 1.45m (Cao) x 1.65m (Tán) | Tầng dưới rừng sồi ẩm, Hẻm núi đá (Z: 3m - 10m) | Gốc mọc tỏa tròn hình phễu với 30-50 tàu lá kiếm xòe rộng đối xứn... | [Chi tiết](species/understory_sword_fern.md) |
| **SH02** | Dương Xỉ Thân Gỗ Cổ Sinh | *Cyathea cooperi* | Australian Tree Fern | 4.2m (Cao) x 3.8m (Tán) | Hẻm vực râm mát, Hốc thác nước ẩm ướt (Z: 2m - 7m) | Thân cột gỗ xù xì tạo bởi các vết sẹo cuống lá già xếp lớp vảy rồ... | [Chi tiết](species/understory_tree_fern.md) |
| **SH03** | Cây Bụi Quả Mọng Đỏ | *Vaccinium vitis-idaea* | Lingonberry Shrub | 0.75m (Cao) x 0.85m (Tán) | Dưới tán rừng thông sỏi đá (Z: 6m - 14m) | Bụi cây lùn phân nhánh rậm rạp, lá hình trứng ngược dày bóng như ... | [Chi tiết](species/shrub_wild_berry.md) |
| **SH04** | Đỗ Quyên Rừng Núi Cao | *Rhododendron ferrugineum* | Alpine Rose | 1.25m (Cao) x 1.45m (Tán) | Sườn dốc núi đá vôi, Đồng cỏ cao (Z: 10m - 18m) | Cây bụi tán tròn chắc khỏe, cành khúc khuỷu. Đỉnh cành nở rộ chùm... | [Chi tiết](species/shrub_alpine_rose.md) |
| **SH05** | Bụi Cơm Cháy Quả Đen | *Sambucus nigra* | Black Elderberry | 2.6m (Cao) x 2.3m (Tán) | Bìa rừng, Rãnh mương bờ suối (Z: 3m - 8m) | Bụi cây cao thân gỗ vỏ xốp có nhiều lỗ bì, cành xòe vòm. Chùm quả... | [Chi tiết](species/shrub_elderberry.md) |
| **SH06** | Cây Tầm Ma Gai Bảo Vệ | *Urtica dioica* | Stinging Nettle | 1.15m (Cao) x 0.72m (Tán) | Vùng đất trũng ven rừng giàu đạm (Z: 3m - 7m) | Thân mọc đứng 4 cạnh cứng cáp, lá mọc đối hình tim mũi mác với ră... | [Chi tiết](species/shrub_stinging_nettle.md) |
| **SH07** | Bách Bò Phủ Đất | *Juniperus procumbens* | Creeping Juniper | 0.42m (Cao) x 2.1m (Tán lan) | Bờ đá dốc, Vách đá khô cằn (Z: 7m - 18m) | Cành nhánh bò lan sát sạt mặt đất uốn lượn theo từng kẽ đá, đan k... | [Chi tiết](species/shrub_creeping_juniper.md) |
| **SH08** | Dương Xỉ Tổ Chim Rừng Mưa | *Asplenium nidus* | Bird's Nest Fern | 1.1m (Cao) x 1.3m (Tán tròn) | Bám trên chạc ba cây to, Hốc đá ẩm (Z: 3m - 9m) | Các phiến lá đơn nguyên lớn hình dải thuôn màu xanh nõn chuối bón... | [Chi tiết](species/shrub_birds_nest_fern.md) |
| **SH09** | Bụi Cẩm Tú Cầu Rừng | *Hydrangea macrophylla* | Wild Forest Hydrangea | 1.6m (Cao) x 1.8m (Tán tròn) | Khe núi suối ẩm, Tán rừng thưa (Z: 4m - 9m) | Bụi cây tán tròn rậm rạp mang những quả cầu hoa khổng lồ đường kí... | [Chi tiết](species/shrub_wild_hydrangea.md) |
| **SH10** | Cây Dâu Rừng Gai Đen | *Rubus fruticosus* | Wild Blackberry Bush | 1.8m (Cao) x 2.2m (Tán gai) | Bìa rừng, Hàng rào đá, Bụi gai rậm (Z: 3m - 8m) | Cành nhánh dạng cung vươn dài chằng chịt vũ trang bằng vô số gai ... | [Chi tiết](species/shrub_wild_blackberry.md) |
| **SH11** | Bụi Nguyệt Quế Thơm | *Laurus nobilis* | Bay Laurel Shrub | 2.8m (Cao) x 2.2m (Tán) | Sườn đồi đón nắng, Vùng đất đá (Z: 5m - 11m) | Cây bụi thường xanh tán dày, lá bầu dục dày cứng mép lượn sóng mà... | [Chi tiết](species/shrub_bay_laurel.md) |
| **SH12** | Cây Tầm Xuân Hoa Dại | *Rosa canina* | Wild Dog Rose / Briar | 2.1m (Cao) x 1.9m (Tán) | Bờ bụi, Bãi cỏ hoang ven rừng (Z: 4m - 10m) | Cành dài uốn cong cong có gai móc sắc, hoa 5 cánh màu hồng nhạt d... | [Chi tiết](species/shrub_wild_briar_rose.md) |
| **SH13** | Tre Trúc Tầng Dưới Núi Cao | *Sasa kurilensis* | Dwarf Mountain Bamboo | 1.7m (Cao) x 1.4m (Bụi rậm) | Tầng dưới rừng linh sam tuyết (Z: 9m - 16m) | Thân ngầm bò lan phóng lên các dóng trúc nhỏ dẻo dai màu xanh ngọ... | [Chi tiết](species/shrub_dwarf_bamboo.md) |
| **SH14** | Bụi Gai Sơn Thù Du Cành Đỏ | *Cornus sericea* | Red Osier Dogwood | 2.2m (Cao) x 2.4m (Tán cành đỏ) | Bờ suối ẩm ướt, Vùng ngập định kỳ (Z: 3m - 7m) | Cây bụi nổi bật vào mùa đông với toàn bộ hệ cành non chuyển màu đ... | [Chi tiết](species/shrub_dogwood.md) |

### Cây Thân Gỗ Rừng & Tầng Trung (Midstory & Canopy Trees) (14 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **TR01** | Bạch Dương Vỏ Bạc Rừng Bắc | *Betula pendula* | Silver Birch | 12.5m (Cao) x 6.8m (Tán) | Ven đồi thông, Thung lũng đón gió (Z: 5m - 12m) | Thân thon thẳng kiêu hãnh bọc lớp vỏ trắng phấn bong thành từng l... | [Chi tiết](species/tree_silver_birch.md) |
| **TR02** | Phong Đỏ Mùa Thu Rực Rỡ | *Acer palmatum* | Japanese Red Maple | 7.8m (Cao) x 7.2m (Tán) | Thung lũng ven suối róc rách, Khe suối trong (Z: 4m - 10m) | Thân uốn lượn khúc khuỷu nghệ thuật như cây cảnh bonsai tự nhiên,... | [Chi tiết](species/tree_red_maple.md) |
| **TR03** | Liễu Rủ Đầm Nước Mơ Màng | *Salix babylonica* | Weeping Willow | 11.8m (Cao) x 12.5m (Tán rủ) | Bờ hồ trung tâm, Bến nước lạch sông (Z: 4m - 6m) | Thân gỗ to lớn uốn nghiêng là đà mặt nước, cành chính xòe vòm rộn... | [Chi tiết](species/canopy_weeping_willow.md) |
| **TR04** | Cọ Rừng Nhiệt Đới | *Arecaceae sylvestris* | Wild Jungle Palm | 9.5m (Cao) x 5.2m (Tán) | Ven biển nhiệt đới, Bãi cát đầm lầy (Z: 0m - 5m) | Thân cột dẻo dai nghiêng cong tự nhiên chống gió bão, thân mang c... | [Chi tiết](species/tree_jungle_palm.md) |
| **TR05** | Anh Đào Rừng Hoa Tuyết | *Prunus serrulata* | Mountain Wild Cherry | 8.8m (Cao) x 8.4m (Tán) | Sườn núi đá đón nắng xuân (Z: 6m - 13m) | Thân vỏ nâu bóng có nhiều lỗ bì ngang màu đồng. Cành nhánh khẳng ... | [Chi tiết](species/tree_mountain_cherry.md) |
| **TR06** | Dầu Khuynh Diệp Bạc Cao Vút | *Eucalyptus globulus* | Tasmanian Blue Gum | 18.5m (Cao) x 8.2m (Tán) | Đồi dốc thoai thoải, Vùng gió nhiều (Z: 6m - 15m) | Thân cây cao vút đồ sộ, lớp vỏ già bong tróc thành từng dải dài t... | [Chi tiết](species/tree_blue_gum.md) |
| **TR07** | Bách Tùng Cột Tháp | *Cupressus sempervirens* | Mediterranean Cypress | 14.5m (Cao) x 2.4m (Tán tháp) | Lối vào làng cổ, Đồi sỏi đón nắng (Z: 5m - 11m) | Dáng cây hình ngọn tháp nhọn cao vút kiên cường, các cành nhánh á... | [Chi tiết](species/tree_italian_cypress.md) |
| **TR08** | Cây Hạt Dẻ Gai Rừng | *Castanea sativa* | Sweet Chestnut | 15.0m (Cao) x 12.0m (Tán) | Sườn đồi đất chua ẩm mát (Z: 5m - 12m) | Thân vỏ nứt xoắn ốc tuyệt đẹp theo chiều kim đồng hồ. Tán lá rộng... | [Chi tiết](species/tree_sweet_chestnut.md) |
| **TR09** | Cây Cơm Nguội Cổ Thụ | *Celtis sinensis* | Chinese Hackberry | 13.0m (Cao) x 14.0m (Tán vòm) | Đầu làng, Ngã ba đường mòn (Z: 4m - 9m) | Thân bọc lớp vỏ xám nhẵn có các nốt sần nhỏ, cành nhánh xòe vòm b... | [Chi tiết](species/tree_chinese_hackberry.md) |
| **TR10** | Cây Cẩm Quỳ Tím Rực Rỡ | *Jacaranda mimosifolia* | Blue Jacaranda | 11.0m (Cao) x 10.5m (Tán tím) | Thung lũng mùa hạ, Ven đồi thấp (Z: 4m - 10m) | Tán cây xòe rộng rực rỡ như đám mây tím biếc mộng mơ, hoa hình ch... | [Chi tiết](species/tree_jacaranda.md) |
| **TR11** | Ngân Hạnh Rẻ Quạt Vàng | *Ginkgo biloba* | Ginkgo Maidenhair Tree | 16.0m (Cao) x 9.0m (Tán tháp vàng) | Đền đài cổ, Đồi đón gió thu (Z: 5m - 12m) | Hóa thạch sống của thế giới thực vật. Thân thẳng đứng, cành mang ... | [Chi tiết](species/tree_ginkgo.md) |
| **TR12** | Mộc Lan Hoa Trắng Đại Đóa | *Magnolia grandiflora* | Southern Magnolia | 14.0m (Cao) x 11.0m (Tán tháp tròn) | Ven hồ nước ấm, Đất phù sa màu mỡ (Z: 3m - 8m) | Tán lá hình kim tự tháp tròn rậm rạp lá xanh quanh năm. Lá to như... | [Chi tiết](species/tree_magnolia.md) |
| **TR13** | Thông Rụng Lá Larch Vàng | *Larix decidua* | European Golden Larch | 15.5m (Cao) x 7.5m (Tán thon) | Vành đai núi tuyết cao (Z: 10m - 17m) | Loài thông lá kim đặc biệt rụng lá theo mùa. Mùa thu lá kim chuyể... | [Chi tiết](species/tree_golden_larch.md) |
| **TR14** | Trắc Bách Diệp Phương Đông | *Platycladus orientalis* | Oriental Arborvitae | 8.5m (Cao) x 4.2m (Tán xòe rẻ quạt) | Vách đá khô cằn, Cổng làng cổ (Z: 5m - 13m) | Thân phân nhánh từ gốc, các cành xếp thành từng phiến phẳng dẹt h... | [Chi tiết](species/tree_oriental_arborvitae.md) |

### Đại Thụ Cổ Thụ Khổng Lồ (Ancient Megatrees & Apex Giants) (12 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **MG01** | Sồi Cổ Thụ Hoàng Gia | *Quercus robur* | Ancient Royal Oak | 16.8m (Cao) x 18.5m (Tán vĩ đại) | Trọng tâm đồng bằng, Trái tim bản đồ (Z: 5m - 7m) | Thân cổ thụ khổng lồ đường kính 3.5m, gốc xòe hệ rễ bạnh gân guốc... | [Chi tiết](species/canopy_ancient_oak.md) |
| **MG02** | Thông Núi Tuyết Alpine | *Pinus cembra* | Swiss Stone Pine | 14.2m (Cao) x 7.8m (Tán) | Đỉnh Matterhorn, Vách đá bão tuyết (Z: 12m - 18m) | Thân cây vặn xoắn chịu bão tuyết hàng trăm năm, cành gốc gãy cụt ... | [Chi tiết](species/canopy_alpine_pine.md) |
| **MG03** | Cự Mộc Sequoia Đỏ Bất Tử | *Sequoiadendron giganteum* | Giant Redwood | 28.5m (Cao) x 11.5m (Tán) | Rừng nguyên sinh hẻo lánh, Hẻm núi sâu (Z: 4m - 12m) | Cột thân khổng lồ sừng sững đường kính gốc tới 5.0m, vươn cao chọ... | [Chi tiết](species/canopy_giant_sequoia.md) |
| **MG04** | Baobab Bầu Nước Châu Phi | *Adansonia digitata* | Grand Baobab | 13.5m (Cao) x 14.5m (Tán rễ trời) | Thảo nguyên đất đỏ khô cằn (Z: 4m - 9m) | Thân cây phình to hình thùng rượu khổng lồ tích trữ nước, đường k... | [Chi tiết](species/canopy_baobab.md) |
| **MG05** | Đa Búp Đỏ Rễ Bạnh Cổ Đại | *Ficus macrophylla* | Moreton Bay Fig / Banyan | 17.5m (Cao) x 23.0m (Tán trùm) | Rừng nhiệt đới hạ lưu, Vùng ẩm ướt (Z: 2m - 7m) | Cây chiếm diện tích khổng lồ như một khu rừng nhỏ. Từ các cành lớ... | [Chi tiết](species/canopy_ancient_banyan.md) |
| **MG06** | Tuyết Tùng Lebanon Ngàn Năm | *Cedrus libani* | Cedar of Lebanon | 15.8m (Cao) x 16.5m (Tán tầng bậc) | Rặng núi đá cao đón gió (Z: 8m - 16m) | Thân cột to lớn phân cành theo phương ngang tuyệt đối, tạo thành ... | [Chi tiết](species/canopy_cedar_lebanon.md) |
| **MG07** | Thiết Mộc Ngàn Năm | *Guaiacum officinale* | Ironwood Lignum | 12.8m (Cao) x 13.5m (Tán tròn đặc) | Rừng nhiệt đới cổ xưa, Đất sỏi đá (Z: 4m - 10m) | Thân cây đanh cứng như thép, thớ gỗ xoắn ốc chằng chịt, vỏ tróc t... | [Chi tiết](species/canopy_ancient_ironwood.md) |
| **MG08** | Bạch Quả Cổ Đại Ngàn Năm | *Ginkgo biloba gigantea* | Ancient Sacred Ginkgo | 22.0m (Cao) x 16.0m (Tán vàng rực) | Đỉnh đồi thánh địa, Lăng tẩm cổ xưa (Z: 6m - 14m) | Cổ thụ ngàn tuổi thân to 4 người ôm, từ thân buông thõng những bầ... | [Chi tiết](species/canopy_ancient_ginkgo.md) |
| **MG09** | Bồ Đề Cổ Thụ Giác Ngộ | *Ficus religiosa* | Sacred Bodhi Tree | 18.0m (Cao) x 20.0m (Tán vòm thanh tịnh) | Bên bờ sông thiêng, Quảng trường trung tâm (Z: 4m - 8m) | Thân uốn lượn cổ kính với lớp vỏ xám sáng, cành lớn vươn rộng man... | [Chi tiết](species/canopy_sacred_bodhi.md) |
| **MG10** | Thông Trắng Khổng Lồ California | *Pinus lambertiana* | Giant Sugar Pine | 26.0m (Cao) x 10.0m (Tán) | Hẻm vực núi tuyết sâu (Z: 11m - 19m) | Loài thông cao nhất thế giới lá kim, cành nhánh vươn dài nằm ngan... | [Chi tiết](species/canopy_sugar_pine.md) |
| **MG11** | Cây Bách Nước Đầm Lầy | *Taxodium distichum* | Bald Cypress | 17.0m (Cao) x 13.0m (Tán nón rộng) | Ngập nước đáy hồ, Vùng bãi sình lầy (Z: 3.5m - 6m) | Gốc cây phình to hình chuông ngâm trong nước, quanh gốc mọc trồi ... | [Chi tiết](species/canopy_bald_cypress.md) |
| **MG12** | Cây Thau Thao Cổ Rừng Mưa | *Dipterocarpus grandiflorus* | Emergent Rainforest Giant | 25.0m (Cao) x 15.0m (Tán súp lơ vĩ đại) | Rừng mưa nhiệt đới tầng vượt tán (Z: 2m - 10m) | Đại thụ tầng vượt tán (emergent layer) vươn cao vượt lên trên thả... | [Chi tiết](species/canopy_rainforest_dipterocarp.md) |

### Thực Vật Thủy Sinh & Đầm Lầy (Aquatic & Wetland Flora) (12 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **AQ01** | Hoa Súng Trắng Nước Ngọt | *Nymphaea alba* | White Water Lily | 0.18m (Cao) x 1.35m (Tán lá) | Mặt hồ trung tâm, Vùng nước lặng (Z: 4.52m) | Lá tròn dẹt nổi bồng bềnh trên mặt nước có khe khuyết hình chữ V ... | [Chi tiết](species/aquatic_water_lily.md) |
| **AQ02** | Sen Hồng Cổ Điển Hoàng Cung | *Nelumbo nucifera* | Sacred Pink Lotus | 1.25m (Cao) x 1.45m (Tán) | Đầm sen cạn, Vịnh lặng nước trong (Z: 4.87m) | Khác với hoa súng, lá và hoa sen vươn cao khỏi mặt nước trên cuốn... | [Chi tiết](species/aquatic_sacred_lotus.md) |
| **AQ03** | Sậy Nước Bờ Hồ | *Phragmites australis* | Common Wetland Reed | 2.8m (Cao) x 0.85m (Tán) | Bờ cát bùn ven hồ, Vùng nước ngập nông (Z: 4.2m - 5.5m) | Thân sậy cao rỗng dẻo dai màu xanh bóng có ngấn lóng rõ rệt. Lá d... | [Chi tiết](species/aquatic_wetland_reed.md) |
| **AQ04** | Cỏ Nến Bồn Bồn Đầm Lầy | *Typha latifolia* | Broadleaf Cattail | 2.2m (Cao) x 0.65m (Tán) | Vũng trũng ngập nước, Bãi đầm lầy ao làng (Z: 4.0m - 5.8m) | Lá thẳng đứng dạng dải hẹp uốn dẻo dai. Trục hoa vươn cao mang bô... | [Chi tiết](species/aquatic_broadleaf_cattail.md) |
| **AQ05** | Rong Đuôi Chồn Đáy Hồ | *Ceratophyllum demersum* | Hornwort Coontail | 0.85m (Cao) x 0.32m (Tán) | Chìm dưới đáy nước trong hồ (Z: 1.5m - 4.2m) | Cây chìm hoàn toàn trong nước không có rễ thật, thân uốn lượn mềm... | [Chi tiết](species/aquatic_hornwort.md) |
| **AQ06** | Rong Lươn Nước Sâu | *Vallisneria americana* | Eelgrass / Tape Grass | 1.35m (Cao) x 0.22m (Tán) | Đáy suối, Lạch nước chảy nhẹ (Z: 2m - 4.5m) | Mọc từ thân bò ngầm dưới bùn cát, phóng lên các dải lá ruy-băng d... | [Chi tiết](species/aquatic_eelgrass.md) |
| **AQ07** | Thủy Trúc Dù Ven Suối | *Cyperus alternifolius* | Umbrella Papyrus | 1.4m (Cao) x 0.95m (Tán dù) | Ven lạch suối đá, Vũng nước trong (Z: 3.5m - 5.0m) | Thân đứng thẳng 3 cạnh nhẵn bóng không lá. Đỉnh thân xòe một vòng... | [Chi tiết](species/aquatic_umbrella_papyrus.md) |
| **AQ08** | Bèo Nhật Bản Hoa Tím | *Eichhornia crassipes* | Water Hyacinth | 0.45m (Cao) x 0.65m (Cụm nổi) | Mặt đầm nước ấm, Lạch sông lặng (Z: 4.8m) | Cây nổi tự do trên mặt nước nhờ cuống lá phình to thành bọng xốp ... | [Chi tiết](species/aquatic_water_hyacinth.md) |
| **AQ09** | Bèo Hoa Dâu Đỏ Thẫm | *Azolla caroliniana* | Red Azolla Water Velvet | 0.02m (Cao) x 1.8m (Thảm nổi) | Mặt nước tĩnh, Đầm lầy bóng râm (Z: 4.5m) | Dương xỉ thủy sinh tí hon kết thành tấm thảm đỏ tía bồng bềnh phủ... | [Chi tiết](species/aquatic_red_azolla.md) |
| **AQ10** | Hoa Súng Khổng Lồ Victoria | *Victoria amazonica* | Giant Amazon Water Lily | 0.35m (Cao) x 2.4m (Đĩa khổng lồ) | Vịnh hồ nước sâu phẳng lặng (Z: 4.52m) | Lá nổi khổng lồ đường kính tới 2.2m hình chiếc mâm tròn có thành ... | [Chi tiết](species/aquatic_victoria_lily.md) |
| **AQ11** | Rong Đuôi Chó Xanh Mướt | *Elodea canadensis* | Canadian Waterweed | 0.75m (Cao) x 0.18m (Tán) | Đáy nước suối chảy xiết trong vắt (Z: 2m - 4.5m) | Thân chìm phân nhánh mảnh mai mang các vòng 3 lá nhỏ hình bầu dục... | [Chi tiết](species/aquatic_elodea.md) |
| **AQ12** | Cây Thủy Cúc Rừng Ngập Mặn | *Rhizophora mangle* | Red Mangrove | 4.5m (Cao) x 4.8m (Tán rễ kiềng) | Cửa biển nước lợ, Bãi triều (Z: 0m - 2m) | Hệ thống rễ chống hình vòng cung (stilt roots) cắm chằng chịt xuố... | [Chi tiết](species/aquatic_mangrove.md) |

### Thực Vật Khô Hạn & Mọng Nước (Arid & Succulents) (12 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **SC01** | Xương Rồng Trụ Saguaro Cổ Thụ | *Carnegiea gigantea* | Saguaro Giant Cactus | 8.8m (Cao) x 3.4m (Tán tay) | Sa mạc khô hạn, Sườn đá nung nấu (Z: 5m - 12m) | Cột thân khổng lồ hình trụ dày đặc các nếp khía dọc sâu như đàn p... | [Chi tiết](species/succulent_saguaro_cactus.md) |
| **SC02** | Nha Đam Gai Khổng Lồ | *Aloe ferox* | Bitter Cape Aloe | 2.3m (Cao) x 1.85m (Tán) | Vách đá khô cằn gió nóng, Bãi sỏi (Z: 4m - 11m) | Thân đơn hóa gỗ bao phủ bởi lớp lá già khô héo rủ xuống như chiếc... | [Chi tiết](species/succulent_cape_aloe.md) |
| **SC03** | Cây Móng Rồng Agave Kim Nhọn | *Agave americana* | Century Plant | 1.9m (Cao) x 2.5m (Tán hoa hồng) | Gò đồi đất khô, Đất đá vôi bạc màu (Z: 5m - 14m) | Mọc thành đóa hoa hồng gai khổng lồ vĩ đại, gồm 30-40 lá dày hình... | [Chi tiết](species/succulent_century_agave.md) |
| **SC04** | Xương Rồng Tai Thỏ Hoa Vàng | *Opuntia microdasys* | Prickly Pear Cactus | 1.45m (Cao) x 1.55m (Tán) | Cồn cát khô, Triền sỏi nung nắng (Z: 3m - 9m) | Phân nhánh gồm các lóng thân dẹp hình oval tròn trịa xếp tầng so ... | [Chi tiết](species/succulent_prickly_pear.md) |
| **SC05** | Bụi Gai Lăn Sa Mạc | *Kali tragus* | Tumbleweed Skeleton | 0.95m (Cao) x 0.95m (Khung cầu) | Đồng cát lộng gió, Đất khô nứt nẻ (Z: 3m - 10m) | Khi chết khô, cây tự đứt lìa gốc để tạo thành một khối cầu gai cà... | [Chi tiết](species/succulent_tumbleweed.md) |
| **SC06** | Sứ Sa Mạc Thân Phình | *Adenium obesum* | Desert Rose | 1.65m (Cao) x 1.25m (Tán) | Khe vách đá sa mạc, Đất sỏi khô (Z: 5m - 12m) | Gốc thân phình to dị dạng như bình củ khổng lồ tích nước uốn lượn... | [Chi tiết](species/succulent_desert_rose.md) |
| **SC07** | Móng Lừa Chuỗi Ngọc Rủ | *Sedum morganianum* | Burro's Tail | 0.65m (Cao) x 0.42m (Chuỗi rủ) | Vách đá dốc cheo leo, Hốc đá khô (Z: 7m - 15m) | Thân buông thõng rủ dài xuống vách đá, bọc kín bởi hàng trăm lá m... | [Chi tiết](species/succulent_burros_tail.md) |
| **SC08** | Thạch Lan Sỏi Sống Sa Mạc | *Lithops dorotheae* | Living Stones | 0.05m (Cao) x 0.08m (Cặp sỏi) | Bãi sỏi cuội nung lửa sa mạc (Z: 4m - 8m) | Cây ngụy trang hoàn hảo thành hai viên sỏi cuội tròn nứt đôi ở gi... | [Chi tiết](species/succulent_living_stones.md) |
| **SC09** | Xương Rồng Thùng Tròn Vàng | *Echinocactus grusonii* | Golden Barrel Cactus | 0.95m (Cao) x 0.95m (Quả cầu gai) | Sườn đồi cát sỏi khô hạn (Z: 6m - 12m) | Thân hình cầu tròn xoe hoàn hảo màu xanh tươi có 25-35 nếp khía d... | [Chi tiết](species/succulent_golden_barrel.md) |
| **SC10** | Cây Joshua Sa Mạc Gai | *Yucca brevifolia* | Joshua Tree | 6.5m (Cao) x 4.8m (Tán cành gai) | Bình nguyên đá sa mạc lộng gió (Z: 7m - 14m) | Thân gỗ xù xì phân cành ngoằn ngoèo kỳ dị như cánh tay người khổn... | [Chi tiết](species/succulent_joshua_tree.md) |
| **SC11** | Cây Bao Báp Bình Rượu | *Pachypodium geayi* | Madagascar Bottle Tree | 5.5m (Cao) x 2.2m (Thân bình) | Đá vôi khô cằn Madagascar (Z: 5m - 10m) | Thân phình to hình cổ chai thon dần lên đỉnh, toàn bộ thân vỏ xám... | [Chi tiết](species/succulent_bottle_tree.md) |
| **SC12** | Sen Đá Hồng Ngọc Sa Mạc | *Echeveria elegans* | Mexican Snow Ball | 0.15m (Cao) x 0.22m (Đóa hoa hồng) | Kẽ đá vôi nứt, Khe dốc khô (Z: 5m - 11m) | Đóa hoa hồng ngọc bích xếp cánh sít sao hoàn hảo, các lá mọng nướ... | [Chi tiết](species/succulent_ghost_echeveria.md) |

### Thực Vật Ăn Thịt, Ký Sinh & Hang Động Phát Quang (Carnivorous, Vines & Cave) (12 loài)

| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |
|:---|:---|:---|:---|:---:|:---:|:---|:---:|
| **EX01** | Cây Bắt Mồi Nắp Ấm Khổng Lồ | *Nepenthes rajah* | Giant Pitcher Plant | 1.25m (Cao) x 1.55m (Tán) | Rừng mưa nhiệt đới ẩm, Vách đá mùn (Z: 3m - 8m) | Dây leo bò mang các lá to có gân giữa kéo dài thành tua cuốn, đầu... | [Chi tiết](species/carnivorous_pitcher_plant.md) |
| **EX02** | Bẫy Kẹp Venus Răng Cưa | *Dionaea muscipula* | Venus Flytrap | 0.28m (Cao) x 0.38m (Tán bẫy) | Đầm lầy than bùn thiếu đạm, Bãi ngập ẩm (Z: 3m - 6m) | Cụm hoa hình hoa thị sát đất, cuống lá dẹp hình tim mang chiếc bẫ... | [Chi tiết](species/carnivorous_venus_flytrap.md) |
| **EX03** | Cây Bắt Ruồi Bọt Nước | *Drosera capensis* | Cape Sundew | 0.32m (Cao) x 0.28m (Tán) | Bãi rêu bùn ẩm ướt nghèo dinh dưỡng (Z: 3m - 7m) | Các dải lá thuôn dài mọc tỏa từ gốc, toàn bộ mặt trên lá phủ dày ... | [Chi tiết](species/carnivorous_sundew.md) |
| **EX04** | Dây Leo Cổ Đại Liana Rừng Già | *Liana gigantica* | Ancient Jungle Vine | 16.0m (Dài) x 2.2m (Tán leo) | Ký sinh vòm đại thụ, Rừng mưa nhiệt đới (Z: 2m - 16m) | Thân dây leo hóa gỗ to bằng bắp đùi uốn lượn thắt nút xoắn ốc như... | [Chi tiết](species/carnivorous_jungle_liana.md) |
| **EX05** | Nấm Mũ Xanh Dạ Quang | *Mycena chlorophos* | Bioluminescent Ghost Mushroom | 0.48m (Cao) x 0.52m (Cụm tán) | Hang ngầm Karst sâu thẳm, Gỗ mục ẩm ướt (Z: -7m đến -2m) | Mọc thành cụm 3-7 cây nấm thân thanh mảnh trên thân gỗ mục trong ... | [Chi tiết](species/cave_bioluminescent_mushroom.md) |
| **EX06** | Thảm Rêu Huỳnh Quang Động Karst | *Schistostega pennata* | Luminescent Cave Moss | 0.06m (Cao) x 1.1m (Thảm mảng) | Vách đá hang ngầm, Khe nứt đá vôi tối (Z: -8m đến -1m) | Bám thành từng mảng xanh ngọc phát sáng lấp lánh trên vách đá han... | [Chi tiết](species/cave_luminescent_moss.md) |
| **EX07** | Nấm Vành Tầng Động Tiên | *Trametes versicolor* | Rainbow Bracket Fungi | 0.35m (Cao) x 0.85m (Tầng quạt) | Vách đá hang ẩm, Gốc cây cổ hóa thạch (Z: -6m đến 0m) | Các phiến nấm dạng quạt vỏ sò xếp tầng chồng lên nhau bậc thang t... | [Chi tiết](species/cave_bracket_fungi.md) |
| **EX08** | Cây Bắt Mồi Rắn Hổ Mang | *Darlingtonia californica* | Cobra Lily | 0.85m (Cao) x 0.65m (Cụm bẫy) | Đầm than bùn suối lạnh râm mát (Z: 4m - 9m) | Ống bẫy hình rắn hổ mang ngóc đầu phồng mang màu xanh vàng điểm đ... | [Chi tiết](species/carnivorous_cobra_lily.md) |
| **EX09** | Lan Rừng Biểu Sinh Vũ Nữ | *Oncidium flexuosum* | Dancing Lady Epiphytic Orchid | 0.65m (Cao) x 0.85m (Chùm hoa) | Ký sinh chạc ba cổ thụ, Rừng ẩm (Z: 3m - 12m) | Giả hành hình dẹt tích nước bám rễ gió trắng mập vào vỏ đại thụ, ... | [Chi tiết](species/carnivorous_wild_orchid.md) |
| **EX10** | Nấm Quỷ Lập Lòe Ma Quái | *Omphalotus olearius* | Jack-o'-Lantern Mushroom | 0.55m (Cao) x 0.65m (Cụm phễu) | Gốc cây mục tối tăm, Cửa hang ẩm (Z: -2m đến 3m) | Mọc cụm chùm lớn màu cam cháy rực rỡ vào ban ngày. Đêm xuống, toà... | [Chi tiết](species/cave_jack_o_lantern.md) |
| **EX11** | Cây Ma Cà Rồng Hút Nhựa | *Monotropa uniflora* | Ghost Pipe / Corpse Plant | 0.22m (Cao) x 0.18m (Cụm trắng) | Nền rừng râm tối mịt mù, Cửa hang đá (Z: 0m - 5m) | Loài thực vật kỳ dị hoàn toàn không có diệp lục, toàn thân trắng ... | [Chi tiết](species/cave_ghost_pipe.md) |
| **EX12** | Cây Bắt Côn Trùng Bọng Khí | *Utricularia vulgaris* | Greater Bladderwort | 0.4m (Cao hoa) x 0.6m (Tán bọng nước) | Nước hồ cạn ngập nắng, Lạch rêu (Z: 4.2m) | Thân chìm dưới nước mang hàng ngàn bọng hút chân không tí hon tro... | [Chi tiết](species/carnivorous_bladderwort.md) |

---

## 4. Hướng Dẫn Tải & Nạp Model Vào Scene Blender

Mọi loài thực vật trong danh mục đều có file `.blend` và `.glb` tương ứng:

```python
import bpy

# Ví dụ nạp cây Sồi Cổ Thụ Hoàng Gia (canopy_ancient_oak)
model_path = "/Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_ancient_oak.glb"
bpy.ops.import_scene.gltf(filepath=model_path)
obj = bpy.context.selected_objects[0]
obj.location = (0.0, 0.0, 5.0)
print(f"✓ Đã nạp thành công {obj.name} vào thế giới!")
```

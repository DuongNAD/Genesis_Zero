#!/usr/bin/env python3
"""
generate_flora_species_docs.py - Generates 56 Hyper-Realistic Scan-Quality Botanical Markdown Specs
Genesis Zero - Ultra-Realistic Botanical Asset Ecosystem
"""

import os
from pathlib import Path

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
SPECIES_DIR = ROOT / "docs" / "flora" / "species"
SPECIES_DIR.mkdir(parents=True, exist_ok=True)

SPECIES_DATA = [
    # -------------------------------------------------------------------------
    # Nhóm 1: Họ Cỏ & Thảm Mặt Đất (Grasses & Groundcovers)
    # -------------------------------------------------------------------------
    {
        "id": "GR01", "slug": "grass_red_fescue", "cat": "grasses_herbs",
        "vn": "Cỏ Lúa Mì Đỏ Đồng Hoang", "latin": "Festuca rubra", "en": "Red Fescue Grass",
        "family": "Poaceae", "biome": "Đồng cỏ, Thảo nguyên đồi thấp (Z: 4m - 10m)",
        "dims": "0.4m (Cao) x 0.35m (Tán)", "poly_lod0": "18,400 tris", "poly_lod1": "4,200 tris",
        "morphology": "Lá dạng sợi thanh mảnh mọc thành cụm búi dày đặc. Đầu ngọn lá có sắc tố anthocyanin ánh đỏ hung đặc trưng. Thân cọng mềm mại uốn cong tự nhiên theo chiều gió lùa.",
        "micro_geo": "Phiến lá có rãnh dọc siêu mịn (micro-groove venation) sâu 0.2mm, mép lá có gai vi mô nano tạo độ phản xạ gắt nhẹ ở góc nghiêng (Fresnel grazing angle).",
        "pbr": "Principled BSDF + SSS: Base Color gradient từ xanh cỏ úa (#4d7c0f) ở gốc đến phớt đỏ tía (#991b1b) ở ngọn. SSS Weight: 0.25, SSS Radius: (0.15, 0.25, 0.05), Roughness: 0.45, Sheen: 0.30.",
    },
    {
        "id": "GR02", "slug": "grass_alpine_tussock", "cat": "grasses_herbs",
        "vn": "Cỏ Tussock Núi Cao", "latin": "Chionochloa rigida", "en": "Alpine Tussock Grass",
        "family": "Poaceae", "biome": "Đỉnh núi tuyết, Khô lạnh gió rét (Z: 12m - 20m)",
        "dims": "0.85m (Cao) x 0.75m (Tán)", "poly_lod0": "26,500 tris", "poly_lod1": "6,800 tris",
        "morphology": "Búi cỏ vòm tròn hình cầu rậm rạp, các dải lá già khô vàng rơm uốn rủ bao bọc chân gốc tạo lớp cách nhiệt chống băng giá, lõi giữa vươn các ngọn cỏ xanh xám cứng cáp.",
        "micro_geo": "Lá dày cứng có gân sống lưng nổi rõ, bề mặt phủ lớp sáp cutin mờ kháng nước, mép lá sắc cạnh có răng cưa li ti bám tuyết.",
        "pbr": "Principled BSDF: Dual-zone material. Vỏ ngoài màu vàng rơm (#ca8a04, Roughness 0.75), Lõi trong xanh xám tro (#65a30d, Roughness 0.50), SSS mỏng 0.15 chống chói sáng tuyết.",
    },
    {
        "id": "GR03", "slug": "grass_feather_grass", "cat": "grasses_herbs",
        "vn": "Cỏ Đuôi Chuột Lông Vũ", "latin": "Stipa pennata", "en": "Feather Grass",
        "family": "Poaceae", "biome": "Thảo nguyên đón gió, Triền đồi cát (Z: 5m - 12m)",
        "dims": "0.95m (Cao) x 0.55m (Tán)", "poly_lod0": "22,000 tris", "poly_lod1": "5,400 tris",
        "morphology": "Thân mảnh mai vươn thẳng, đầu ngọn mang chùm bông tơ dài mềm mại như đuôi chim phượng hoàng, rung rinh nhịp nhàng theo từng làn gió thoảng.",
        "micro_geo": "Bông tơ cấu tạo từ hàng ngàn sợi lông tơ siêu mảnh (hair cards alpha-masked), tán xạ ánh sáng ngược (backlighting) cực mạnh.",
        "pbr": "Principled BSDF + Anisotropic: Bông tơ màu bạc ngà (#f8fafc), Anisotropic: 0.65, Sheen: 0.85 (tạo viền sáng tơ óng ả khi ngược sáng), SSS Weight: 0.40.",
    },
    {
        "id": "GR04", "slug": "grass_velvet_moss", "cat": "grasses_herbs",
        "vn": "Thảm Rêu Nhung Rừng Ẩm", "latin": "Bryophyta saxatilis", "en": "Velvet Forest Moss",
        "family": "Bryaceae", "biome": "Chân cổ thụ, Vách đá bóng râm, Bờ suối (Z: 2m - 8m)",
        "dims": "0.06m (Cao) x 1.4m (Tán phủ)", "poly_lod0": "32,000 tris", "poly_lod1": "8,000 tris",
        "morphology": "Thảm rêu xanh lục bảo xốp dày trải dài theo địa hình gồ ghề, mọc chùm hàng vạn ngọn rêu tí hon hình sao ngậm nước lấp lánh.",
        "micro_geo": "Dựng bằng lưới vi phồng (micro-displacement) kết hợp hệ thống lông tơ mật độ cao, tích hợp các bọng sương mai phản chiếu hạt nước tròn vo.",
        "pbr": "Principled BSDF + Fuzzy Velvet: Base Color xanh ngọc sẫm (#15803d), SSS: 0.55, SSS Radius: (0.1, 0.4, 0.1), Roughness: 0.80, Sheen Tint: 1.0 (nhung tuyết rực rỡ).",
    },
    {
        "id": "GR05", "slug": "grass_white_clover", "cat": "grasses_herbs",
        "vn": "Cỏ Ba Lá May Mắn", "latin": "Trifolium repens", "en": "White Clover",
        "family": "Fabaceae", "biome": "Bãi cỏ xanh, Bìa rừng, Lối đi ẩm (Z: 3m - 8m)",
        "dims": "0.18m (Cao) x 0.45m (Tán)", "poly_lod0": "14,500 tris", "poly_lod1": "3,600 tris",
        "morphology": "Cuống mảnh uốn lượn mang bộ 3 lá chét hình tim ngược, mặt lá có vệt chữ V màu trắng sữa đặc trưng. Điểm xuyết bông hoa đầu tròn màu trắng ngà cánh bướm.",
        "micro_geo": "Gân lá phân nhánh mạng lưới nổi nhẹ trên mặt lá, phiến lá cong khum lòng máng hứng giọt sương.",
        "pbr": "Principled BSDF: Lá xanh non (#22c55e) kèm dải hoa văn chữ V (#e2e8f0), SSS Weight: 0.38, hoa trắng tinh xảo SSS 0.60 mờ ảo trong nắng.",
    },
    {
        "id": "GR06", "slug": "grass_sheeps_fescue", "cat": "grasses_herbs",
        "vn": "Cỏ Lông Nhím Rừng Đá", "latin": "Festuca ovina", "en": "Sheep's Fescue",
        "family": "Poaceae", "biome": "Khe đá núi vôi, Sườn sỏi khô cằn (Z: 8m - 16m)",
        "dims": "0.32m (Cao) x 0.28m (Tán)", "poly_lod0": "16,000 tris", "poly_lod1": "3,800 tris",
        "morphology": "Bụi cỏ gai nhọn xòe tròn như lưng nhím, lá cuộn tròn hình kim màu xanh xám tro tráng sáp xanh ngọc xỉn, chịu hạn và gió dữ.",
        "micro_geo": "Lá tiết diện bán nguyệt viền gân cứng, đầu kim nhọn hoắt có độ bóng mờ sáp.",
        "pbr": "Principled BSDF: Màu xanh xám băng (#94a3b8 / #475569), Roughness: 0.35, Clearcoat: 0.20 mô phỏng lớp phấn sáp bảo vệ bề mặt.",
    },
    {
        "id": "GR07", "slug": "grass_woolly_moss", "cat": "grasses_herbs",
        "vn": "Thảm Rêu Râu Bạc Vách Đá", "latin": "Racomitrium lanuginosum", "en": "Woolly Fringe Moss",
        "family": "Grimmiaceae", "biome": "Vách đá phong hóa, Đỉnh núi sương mù (Z: 14m - 22m)",
        "dims": "0.08m (Cao) x 0.9m (Tán)", "poly_lod0": "28,000 tris", "poly_lod1": "7,000 tris",
        "morphology": "Mọc thành mảng đệm xốp phủ trên mặt đá granit gồ ghề. Đỉnh mỗi chồi rêu mang một sợi râu trong suốt dài lấp lánh như sương tuyết vĩnh cửu.",
        "micro_geo": "Đầu chồi râu trong suốt có chiết suất khúc xạ ánh sáng (IOR 1.33) tạo quầng hào quang bạc khi ngược nắng.",
        "pbr": "Principled BSDF: Chân rêu xanh lục xám (#3f6212), chóp râu bạc trong suốt Transmission: 0.40, Sheen: 0.95, Roughness: 0.65.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 2: Thảo Mộc & Hoa Rừng (Herbs & Wildflowers)
    # -------------------------------------------------------------------------
    {
        "id": "FL01", "slug": "flower_oxeye_daisy", "cat": "grasses_herbs",
        "vn": "Cúc Vàng Đồng Nội", "latin": "Leucanthemum vulgare", "en": "Oxeye Daisy",
        "family": "Asteraceae", "biome": "Thung lũng ngập nắng, Đồng cỏ ven suối (Z: 4m - 9m)",
        "dims": "0.65m (Cao) x 0.4m (Tán)", "poly_lod0": "24,000 tris", "poly_lod1": "5,800 tris",
        "morphology": "Thân đứng có khía dọc, lá xẻ thùy răng cưa thưa. Đóa hoa đơn độc ở đỉnh với đĩa nhụy hoa vàng cam hình vòm lõm chứa hàng trăm hoa ống li ti, viền ngoài là 20-30 cánh hoa trắng muốt thuôn dài.",
        "micro_geo": "Mặt đĩa nhụy xếp xoắn ốc theo tỷ lệ vàng Fibonacci (34/55 spirals), từng nụ hoa ống có viền cánh 5 cánh siêu nhỏ. Cánh hoa có gân chìm uốn lượn.",
        "pbr": "Principled BSDF: Cánh hoa trắng sứ (#ffffff) SSS 0.45 với bán kính tán xạ vàng nhạt. Nhụy hoa vàng nghệ đậm (#f59e0b) Roughness 0.90 mô phỏng phấn hoa mịn màng.",
    },
    {
        "id": "FL02", "slug": "flower_bluebell", "cat": "grasses_herbs",
        "vn": "Hoa Chuông Xanh Rừng Rậm", "latin": "Hyacinthoides non-scripta", "en": "English Bluebell",
        "family": "Asparagaceae", "biome": "Tán rừng sồi ẩm râm mát (Z: 5m - 9m)",
        "dims": "0.48m (Cao) x 0.32m (Tán)", "poly_lod0": "19,500 tris", "poly_lod1": "4,600 tris",
        "morphology": "Cành hoa cong uốn cong một bên duyên dáng, mang 6-12 đóa hoa hình chuông rủ xuống. Đầu cánh hoa uốn cong quăn ngược ra ngoài, màu xanh lam tím violet huyền ảo.",
        "micro_geo": "Cánh hoa hình ống loe cong mượt mà, gân giữa cánh đậm màu, bao phấn màu kem trắng ẩn sâu trong vòm chuông.",
        "pbr": "Principled BSDF: Lam tím violet (#6366f1 / #8b5cf6), SSS Weight: 0.50 tán xạ ánh sáng lam ngọc, bóng mờ mịn màng Roughness: 0.32.",
    },
    {
        "id": "FL03", "slug": "flower_wild_lavender", "cat": "grasses_herbs",
        "vn": "Oải Hương Tím Dại", "latin": "Lavandula angustifolia", "en": "Wild Lavender",
        "family": "Lamiaceae", "biome": "Sườn đồi đá vôi khô nhiều nắng (Z: 6m - 14m)",
        "dims": "0.72m (Cao) x 0.65m (Tán)", "poly_lod0": "34,000 tris", "poly_lod1": "8,200 tris",
        "morphology": "Bụi bán mộc thân gốc hóa gỗ, cành non vuông vức màu xám xanh mang lá hẹp thuôn. Cành hoa vươn cao kết thành bông dày đặc các vòng hoa tím biếc.",
        "micro_geo": "Bề mặt lá và đài hoa phủ dày đặc lông tơ tiết tinh dầu hình cầu nano, tạo lớp màng mờ vi mô làm mềm phản xạ ánh sáng.",
        "pbr": "Principled BSDF: Cánh hoa tím hoa cà (#a855f7), đài hoa tím sẫm (#581c87), Sheen: 0.60, Roughness: 0.55, SSS: 0.30.",
    },
    {
        "id": "FL04", "slug": "flower_dandelion", "cat": "grasses_herbs",
        "vn": "Bồ Công Anh Bào Tử Gió", "latin": "Taraxacum officinale", "en": "Dandelion Spore",
        "family": "Asteraceae", "biome": "Bãi cỏ nắng, Lối mòn, Đồng nội (Z: 3m - 10m)",
        "dims": "0.38m (Cao) x 0.26m (Tán)", "poly_lod0": "42,000 tris", "poly_lod1": "9,500 tris",
        "morphology": "Cuống rỗng vươn thẳng từ vòng lá sát đất hình răng sư tử. Đỉnh mang quả cầu bồ công anh tròn xoe hoàn hảo cấu tạo từ hàng trăm chiếc dù lông tơ trắng muốt đính hạt.",
        "micro_geo": "Từng chiếc dù hạt (pappus) có cuống tơ siêu mảnh và tán dù tỏa tia lông tơ tẽ đối xứng, hạt thoi có gai ngược bám đất.",
        "pbr": "Principled BSDF: Dù lông tơ màu trắng ngà trong suốt Transmission: 0.35, Sheen: 0.90, SSS: 0.40, Hạt thoi nâu gỗ sẫm (#78350f, Roughness 0.85).",
    },
    {
        "id": "FL05", "slug": "flower_wild_mint", "cat": "grasses_herbs",
        "vn": "Bạc Hà Rừng Hoang Dã", "latin": "Mentha arvensis", "en": "Wild Corn Mint",
        "family": "Lamiaceae", "biome": "Rìa suối ẩm, Đầm lầy cỏ (Z: 3m - 7m)",
        "dims": "0.52m (Cao) x 0.38m (Tán)", "poly_lod0": "18,000 tris", "poly_lod1": "4,200 tris",
        "morphology": "Thân 4 cạnh vuông vức màu phớt tím, lá mọc đối chéo chữ thập có răng cưa sắc nhọn, gân lá chìm sâu. Hoa tím phớt trắng mọc thành cụm tròn quanh nách lá.",
        "micro_geo": "Gân lá nổi gờ mặt dưới và lõm rãnh mặt trên, phiến lá hơi phồng giữa các ô gân tạo độ nhấp nhô sống động.",
        "pbr": "Principled BSDF: Lá xanh đậm (#16a34a) phủ sáp mờ Roughness 0.40, SSS: 0.35, Thân tím hung (#701a75).",
    },
    {
        "id": "FL06", "slug": "flower_corn_poppy", "cat": "grasses_herbs",
        "vn": "Hoa Anh Túc Lửa Hoang", "latin": "Papaver rhoeas", "en": "Corn Poppy",
        "family": "Papaveraceae", "biome": "Cánh đồng ngập nắng, Triền dốc cát (Z: 4m - 11m)",
        "dims": "0.75m (Cao) x 0.35m (Tán)", "poly_lod0": "16,500 tris", "poly_lod1": "3,900 tris",
        "morphology": "Cuống hoa mảnh uốn lượn có lông châm tơ trắng dựng đứng, mang nụ hoa rủ trước khi bung nở thành đóa hoa đỏ rực 4 cánh mỏng manh như lụa, tâm có đốm đen huyền bí.",
        "micro_geo": "Cánh hoa có độ nhăn nheo gợn sóng vi mô như giấy lụa vò nhẹ, mép cánh uốn lượn tự nhiên.",
        "pbr": "Principled BSDF: Đỏ tươi rực rỡ (#dc2626) với đốm đen đáy cánh (#0f172a), SSS cực mạnh 0.70 tán xạ đỏ cam rực lửa khi nắng xuyên qua.",
    },
    {
        "id": "FL07", "slug": "flower_lily_valley", "cat": "grasses_herbs",
        "vn": "Bách Hợp Thung Lũng Trắng", "latin": "Convallaria majalis", "en": "Lily of the Valley",
        "family": "Asparagaceae", "biome": "Dưới bóng râm cây cổ thụ, Đất mùn rừng (Z: 4m - 8m)",
        "dims": "0.26m (Cao) x 0.22m (Tán)", "poly_lod0": "15,800 tris", "poly_lod1": "3,600 tris",
        "morphology": "Hai lá gốc lớn hình bầu dục bóng mượt bao bọc cuống hoa mảnh mai nghiêng nhẹ, treo 6-10 quả chuông hoa màu trắng ngà thanh tao rủ xuống.",
        "micro_geo": "Miệng chuông hoa có 6 răng uốn cong nhẹ ra ngoài, cuống hoa có khớp uốn cong 90 độ mềm mại.",
        "pbr": "Principled BSDF: Cánh chuông trắng ngọc trai (#f8fafc), SSS: 0.65 (trong trẻo thanh khiết), Lá xanh mướt mát SSS 0.40 Roughness 0.28.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 3: Cây Bụi & Dương Xỉ Tầng Dưới (Understory Shrubs & Ferns)
    # -------------------------------------------------------------------------
    {
        "id": "SH01", "slug": "understory_sword_fern", "cat": "understory_shrubs",
        "vn": "Dương Xỉ Kiếm Khổng Lồ", "latin": "Polystichum munitum", "en": "Western Sword Fern",
        "family": "Dryopteridaceae", "biome": "Tầng dưới rừng sồi ẩm, Hẻm núi đá (Z: 3m - 10m)",
        "dims": "1.45m (Cao) x 1.65m (Tán)", "poly_lod0": "48,000 tris", "poly_lod1": "12,000 tris",
        "morphology": "Gốc mọc tỏa tròn hình phễu với 30-50 tàu lá kiếm xòe rộng đối xứng. Từng lá chét có hình lưỡi liềm với cuống nhỏ và tai lá nhọn ở gốc, mép răng cưa sắc.",
        "micro_geo": "Mặt dưới lá chét mang hai hàng ổ túi bào tử (sori) tròn màu nâu vàng xếp đều đặn hai bên gân chính, phiến lá bóng dày có gân phụ xẻ rãnh.",
        "pbr": "Principled BSDF: Xanh lục bảo sẫm (#15803d), mặt trên bóng bẩy Roughness: 0.32, Clearcoat: 0.15, SSS Weight: 0.42, túi bào tử nâu đất (#78350f).",
    },
    {
        "id": "SH02", "slug": "understory_tree_fern", "cat": "understory_shrubs",
        "vn": "Dương Xỉ Thân Gỗ Cổ Sinh", "latin": "Cyathea cooperi", "en": "Australian Tree Fern",
        "family": "Cyatheaceae", "biome": "Hẻm vực râm mát, Hốc thác nước ẩm ướt (Z: 2m - 7m)",
        "dims": "4.2m (Cao) x 3.8m (Tán)", "poly_lod0": "65,000 tris", "poly_lod1": "16,000 tris",
        "morphology": "Thân cột gỗ xù xì tạo bởi các vết sẹo cuống lá già xếp lớp vảy rồng, đỉnh thân xòe tán lọng khổng lồ với các tàu lá dương xỉ 3 lần lông chim cong hình vòm cung kỳ vĩ.",
        "micro_geo": "Cuống lá non cuộn tròn hình xoắn ốc (fiddleheads) phủ đầy lông tơ tơ vàng óng ánh như tơ tằm, thân cột có rễ khí sinh đan kết như bím tóc.",
        "pbr": "Principled BSDF: Thân cột nâu sậm nứt nẻ (#271c14, Roughness 0.90, Normal Bump sâu), Tán lá xanh non tươi sáng SSS 0.50 tán xạ ngược lộng lẫy.",
    },
    {
        "id": "SH03", "slug": "shrub_wild_berry", "cat": "understory_shrubs",
        "vn": "Cây Bụi Quả Mọng Đỏ", "latin": "Vaccinium vitis-idaea", "en": "Lingonberry Shrub",
        "family": "Ericaceae", "biome": "Dưới tán rừng thông sỏi đá (Z: 6m - 14m)",
        "dims": "0.75m (Cao) x 0.85m (Tán)", "poly_lod0": "38,000 tris", "poly_lod1": "9,000 tris",
        "morphology": "Bụi cây lùn phân nhánh rậm rạp, lá hình trứng ngược dày bóng như da. Cành trĩu trịt từng chùm 5-10 quả mọng tròn đỏ tươi như ngọc ruby.",
        "micro_geo": "Quả mọng có vết lõm đài hoa 4 răng ở đỉnh, vỏ quả căng mọng phản chiếu ánh sáng điểm (specular highlight), thịt quả mờ ngậm nước.",
        "pbr": "Principled BSDF: Quả đỏ ruby (#b91c1c), SSS: 0.65 (thấu quang mọng nước ngọt lành), Roughness: 0.20, Lá xanh đậm viền cong Roughness 0.35.",
    },
    {
        "id": "SH04", "slug": "shrub_alpine_rose", "cat": "understory_shrubs",
        "vn": "Đỗ Quyên Rừng Núi Cao", "latin": "Rhododendron ferrugineum", "en": "Alpine Rose",
        "family": "Ericaceae", "biome": "Sườn dốc núi đá vôi, Đồng cỏ cao (Z: 10m - 18m)",
        "dims": "1.25m (Cao) x 1.45m (Tán)", "poly_lod0": "45,000 tris", "poly_lod1": "11,500 tris",
        "morphology": "Cây bụi tán tròn chắc khỏe, cành khúc khuỷu. Đỉnh cành nở rộ chùm 6-12 hoa hình phễu màu hồng cánh sen rực rỡ, lá mặt trên xanh thẫm, mặt dưới rỉ sắt nâu đồng.",
        "micro_geo": "Mặt dưới lá phủ lớp vảy tuyến tròn li ti màu gỉ sắt, nhụy hoa dài cong vút vươn ra khỏi vành phễu hoa có phấn vàng.",
        "pbr": "Principled BSDF: Cánh hoa hồng cánh sen rực rỡ (#ec4899), SSS: 0.55 thấu quang lộng lẫy, Mặt dưới lá nâu gỉ sắt (#9a3412, Roughness 0.80).",
    },
    {
        "id": "SH05", "slug": "shrub_elderberry", "cat": "understory_shrubs",
        "vn": "Bụi Cơm Cháy Quả Đen", "latin": "Sambucus nigra", "en": "Black Elderberry",
        "family": "Adoxaceae", "biome": "Bìa rừng, Rãnh mương bờ suối (Z: 3m - 8m)",
        "dims": "2.6m (Cao) x 2.3m (Tán)", "poly_lod0": "52,000 tris", "poly_lod1": "13,000 tris",
        "morphology": "Bụi cây cao thân gỗ vỏ xốp có nhiều lỗ bì, cành xòe vòm. Chùm quả hình tán phẳng rộng lớn trĩu nặng hàng trăm quả mọng đen bóng như hạt cườm.",
        "micro_geo": "Cuống chùm hoa/quả màu tím đỏ uốn lượn phân nhánh 5 cấp bậc, quả tròn có lớp phấn sáp mờ phủ nhẹ.",
        "pbr": "Principled BSDF: Quả đen tím thẫm (#1e1b4b), Clearcoat: 0.40, Roughness: 0.25, Cuống quả tím đỏ (#9f1239), Lá kép 5-7 lá chét SSS 0.35.",
    },
    {
        "id": "SH06", "slug": "shrub_stinging_nettle", "cat": "understory_shrubs",
        "vn": "Cây Tầm Ma Gai Bảo Vệ", "latin": "Urtica dioica", "en": "Stinging Nettle",
        "family": "Urticaceae", "biome": "Vùng đất trũng ven rừng giàu đạm (Z: 3m - 7m)",
        "dims": "1.15m (Cao) x 0.72m (Tán)", "poly_lod0": "28,000 tris", "poly_lod1": "6,500 tris",
        "morphology": "Thân mọc đứng 4 cạnh cứng cáp, lá mọc đối hình tim mũi mác với răng cưa nhọn kép sâu. Toàn thân và lá phủ dày đặc lông gai rỗng chứa dịch châm chích.",
        "micro_geo": "Gai châm (trichome) trong suốt hình kim nhọn có gốc phồng tròn như bọng thủy tinh, đầu nhọn dễ gãy khi chạm vào.",
        "pbr": "Principled BSDF: Lá xanh xỉn sẫm (#166534), Lông gai trong suốt Transmission: 0.75, Roughness: 0.15, SSS: 0.30.",
    },
    {
        "id": "SH07", "slug": "shrub_creeping_juniper", "cat": "understory_shrubs",
        "vn": "Bách Bò Phủ Đất", "latin": "Juniperus procumbens", "en": "Creeping Juniper",
        "family": "Cupressaceae", "biome": "Bờ đá dốc, Vách đá khô cằn (Z: 7m - 18m)",
        "dims": "0.42m (Cao) x 2.1m (Tán lan)", "poly_lod0": "36,000 tris", "poly_lod1": "8,500 tris",
        "morphology": "Cành nhánh bò lan sát sạt mặt đất uốn lượn theo từng kẽ đá, đan kết thành tấm thảm gai xanh ngọc lam bảo vệ đất chống xói mòn sạt lở.",
        "micro_geo": "Lá kim ngắn hình vảy xếp xoắn ốc 3 lá một vòng khít khao, đầu lá có đầu gai sắc nhọn.",
        "pbr": "Principled BSDF: Xanh ngọc lam mờ (#0e7490 / #047857), Roughness: 0.42, Vỏ cành nâu đỏ nứt nẻ Roughness 0.88.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 4: Cây Thân Gỗ Rừng & Tầng Trung (Midstory & Canopy Trees)
    # -------------------------------------------------------------------------
    {
        "id": "TR01", "slug": "tree_silver_birch", "cat": "canopy_trees",
        "vn": "Bạch Dương Vỏ Bạc Rừng Bắc", "latin": "Betula pendula", "en": "Silver Birch",
        "family": "Betulaceae", "biome": "Ven đồi thông, Thung lũng đón gió (Z: 5m - 12m)",
        "dims": "12.5m (Cao) x 6.8m (Tán)", "poly_lod0": "58,000 tris", "poly_lod1": "14,500 tris",
        "morphology": "Thân thon thẳng kiêu hãnh bọc lớp vỏ trắng phấn bong thành từng lớp mỏng như giấy lụa, điểm xuyết các vết nứt nẻ hình thoi màu đen sẫm. Cành nhánh thanh mảnh uốn cong rủ nhẹ mang lá hình tam giác răng cưa rung rinh.",
        "micro_geo": "Vết nứt nẻ đen sần sùi ở gốc cây có độ sâu rãnh 8mm, các dải vỏ cuộn tròn lượn lách tự nhiên. Lá có cuống mảnh dài tạo dao động con lắc khi có gió.",
        "pbr": "Principled BSDF: Vỏ thân trắng ngà (#f1f5f9) kèm vệt nứt than đen (#0f172a, Roughness 0.95), Tán lá xanh non sáng rực (#84cc16), SSS cực cao 0.52 tạo vòm sáng lung linh.",
    },
    {
        "id": "TR02", "slug": "tree_red_maple", "cat": "canopy_trees",
        "vn": "Phong Đỏ Mùa Thu Rực Rỡ", "latin": "Acer palmatum", "en": "Japanese Red Maple",
        "family": "Sapindaceae", "biome": "Thung lũng ven suối róc rách, Khe suối trong (Z: 4m - 10m)",
        "dims": "7.8m (Cao) x 7.2m (Tán)", "poly_lod0": "62,000 tris", "poly_lod1": "15,000 tris",
        "morphology": "Thân uốn lượn khúc khuỷu nghệ thuật như cây cảnh bonsai tự nhiên, phân nhiều nhánh thấp. Tán lá xòe nhiều tầng lớp như bậc thang mây màu đỏ thắm rực lửa.",
        "micro_geo": "Lá xẻ sâu 5-7 thùy hình sao thanh tú, gân lá phân nhánh chân vịt nổi gờ sắc nét, mép răng cưa đôi mịn màng.",
        "pbr": "Principled BSDF: Đỏ ruby pha cam rực rỡ (#b91c1c / #ea580c), SSS Weight: 0.65 (tán lá phát sáng như ngọn lửa khi ngược nắng), Vỏ thân xám mịn vân dọc thanh tú.",
    },
    {
        "id": "TR03", "slug": "canopy_weeping_willow", "cat": "canopy_trees",
        "vn": "Liễu Rủ Đầm Nước Mơ Màng", "latin": "Salix babylonica", "en": "Weeping Willow",
        "family": "Salicaceae", "biome": "Bờ hồ trung tâm, Bến nước lạch sông (Z: 4m - 6m)",
        "dims": "11.8m (Cao) x 12.5m (Tán rủ)", "poly_lod0": "72,000 tris", "poly_lod1": "18,000 tris",
        "morphology": "Thân gỗ to lớn uốn nghiêng là đà mặt nước, cành chính xòe vòm rộng buông rủ hàng ngàn dải cành mảnh mai mềm mại buông thõng chạm mặt hồ gợn sóng.",
        "micro_geo": "Dải cành rủ kết hợp các chuỗi lá hẹp hình mũi mác dài uốn lượn tự do, tạo thành rèm tơ xanh mờ ảo đung đưa theo gió.",
        "pbr": "Principled BSDF: Lá xanh vàng non mềm mại (#65a30d), SSS: 0.48, Vỏ thân nứt nẻ rãnh dọc sâu màu xám tro cổ kính (#475569, Roughness 0.88).",
    },
    {
        "id": "TR04", "slug": "tree_jungle_palm", "cat": "canopy_trees",
        "vn": "Cọ Rừng Nhiệt Đới", "latin": "Arecaceae sylvestris", "en": "Wild Jungle Palm",
        "family": "Arecaceae", "biome": "Ven biển nhiệt đới, Bãi cát đầm lầy (Z: 0m - 5m)",
        "dims": "9.5m (Cao) x 5.2m (Tán)", "poly_lod0": "42,000 tris", "poly_lod1": "10,500 tris",
        "morphology": "Thân cột dẻo dai nghiêng cong tự nhiên chống gió bão, thân mang các ngấn sẹo tròn vòng quanh. Đỉnh thân trổ vòm 18-24 tàu lá xòe hình quạt lông chim hùng dũng.",
        "micro_geo": "Tàu lá có cuống gai sắc ở gốc, phiến lá gấp nếp hình chữ V sâu giúp tăng độ cứng cáp chống rách gió, gân chính dày đặc.",
        "pbr": "Principled BSDF: Tàu lá xanh bóng bẩy (#15803d, Roughness 0.28, Clearcoat 0.20, SSS 0.38), Thân cột xám vàng có sợi xơ bẹ dừa (#713f12, Roughness 0.92).",
    },
    {
        "id": "TR05", "slug": "tree_mountain_cherry", "cat": "canopy_trees",
        "vn": "Anh Đào Rừng Hoa Tuyết", "latin": "Prunus serrulata", "en": "Mountain Wild Cherry",
        "family": "Rosaceae", "biome": "Sườn núi đá đón nắng xuân (Z: 6m - 13m)",
        "dims": "8.8m (Cao) x 8.4m (Tán)", "poly_lod0": "68,000 tris", "poly_lod1": "17,000 tris",
        "morphology": "Thân vỏ nâu bóng có nhiều lỗ bì ngang màu đồng. Cành nhánh khẳng khiu vươn ngang nở rộ hàng ngàn đóa hoa 5 cánh màu hồng phấn bồng bềnh phủ kín cây.",
        "micro_geo": "Cánh hoa mỏng tang xẻ khuyết sâu ở đỉnh cánh, chùm nhụy hoa vươn dài với hạt phấn vàng óng, cánh hoa rơi rụng lả tả dưới gốc.",
        "pbr": "Principled BSDF: Cánh hoa hồng phấn dịu ngọt (#fbcfe8 / #f472b6), SSS cực cao 0.72 tạo hiệu ứng mây hoa phát sáng trong nắng sớm, Vỏ thân bóng ánh đồng (#7c2d12).",
    },
    {
        "id": "TR06", "slug": "tree_blue_gum", "cat": "canopy_trees",
        "vn": "Dầu Khuynh Diệp Bạc Cao Vút", "latin": "Eucalyptus globulus", "en": "Tasmanian Blue Gum",
        "family": "Myrtaceae", "biome": "Đồi dốc thoai thoải, Vùng gió nhiều (Z: 6m - 15m)",
        "dims": "18.5m (Cao) x 8.2m (Tán)", "poly_lod0": "54,000 tris", "poly_lod1": "13,500 tris",
        "morphology": "Thân cây cao vút đồ sộ, lớp vỏ già bong tróc thành từng dải dài treo lơ lửng để lộ lớp thân non nhẵn mịn loang lổ các mảng màu trắng kem, xanh rêu và xám bạc. Tán lá thưa mang lá liềm cong rủ.",
        "micro_geo": "Các dải vỏ bong uốn cong vênh ra khỏi thân, lá hình lưỡi liềm cong dài có đốm tuyến tinh dầu li ti trong suốt.",
        "pbr": "Principled BSDF: Thân loang lổ nghệ thuật (#e2e8f0 / #84cc16 / #64748b), Roughness mịn 0.38, Lá xanh lam xám bạc (#64748b, SSS 0.35).",
    },
    {
        "id": "TR07", "slug": "tree_italian_cypress", "cat": "canopy_trees",
        "vn": "Bách Tùng Cột Tháp", "latin": "Cupressus sempervirens", "en": "Mediterranean Cypress",
        "family": "Cupressaceae", "biome": "Lối vào làng cổ, Đồi sỏi đón nắng (Z: 5m - 11m)",
        "dims": "14.5m (Cao) x 2.4m (Tán tháp)", "poly_lod0": "38,000 tris", "poly_lod1": "9,500 tris",
        "morphology": "Dáng cây hình ngọn tháp nhọn cao vút kiên cường, các cành nhánh áp sát thân vươn thẳng lên trời tạo thành hình ngọn nến xanh thẫm uy nghi.",
        "micro_geo": "Lưới tán lá gồm các cụm vảy kim cương xếp lợp ngói dày đặc, quả nón hình cầu hóa gỗ nứt thành các mảnh khiên giác.",
        "pbr": "Principled BSDF: Xanh lục sẫm uy nghiêm (#14532d), Roughness: 0.50, SSS nhẹ 0.18 giúp giữ khối tháp vững chãi không bị bẹt sáng.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 5: Đại Thụ Cổ Thụ Khổng Lồ (Ancient Megatrees & Apex Giants)
    # -------------------------------------------------------------------------
    {
        "id": "MG01", "slug": "canopy_ancient_oak", "cat": "canopy_trees",
        "vn": "Sồi Cổ Thụ Hoàng Gia", "latin": "Quercus robur", "en": "Ancient Royal Oak",
        "family": "Fagaceae", "biome": "Trọng tâm đồng bằng, Trái tim bản đồ (Z: 5m - 7m)",
        "dims": "16.8m (Cao) x 18.5m (Tán vĩ đại)", "poly_lod0": "86,000 tris", "poly_lod1": "22,000 tris",
        "morphology": "Thân cổ thụ khổng lồ đường kính 3.5m, gốc xòe hệ rễ bạnh gân guốc bám chặt lòng đất. Cành bàng to như thân cây thường vươn ngang uốn lượn nâng đỡ vòm tán lá sồi ngàn năm bạt ngàn.",
        "micro_geo": "Vỏ cây nứt sâu rãnh 40mm phủ rêu xanh cổ xưa và địa y bạc. Hốc mắt cây cổ thụ hình oval chứa nấm ký sinh. Lá sồi thùy lượn sóng mang quả đấu nón có mũ sần sùi.",
        "pbr": "Principled BSDF Multi-Material: Vỏ sồi nâu xám nứt nẻ (#38281b, Normal Displacement sâu, Roughness 0.95), Tán lá sồi dày SSS 0.45 (#15803d), Điểm rêu bám chân gốc (#4d7c0f).",
    },
    {
        "id": "MG02", "slug": "canopy_alpine_pine", "cat": "canopy_trees",
        "vn": "Thông Núi Tuyết Alpine", "latin": "Pinus cembra", "en": "Swiss Stone Pine",
        "family": "Pinaceae", "biome": "Đỉnh Matterhorn, Vách đá bão tuyết (Z: 12m - 18m)",
        "dims": "14.2m (Cao) x 7.8m (Tán)", "poly_lod0": "64,000 tris", "poly_lod1": "16,000 tris",
        "morphology": "Thân cây vặn xoắn chịu bão tuyết hàng trăm năm, cành gốc gãy cụt hóa lũa bạc màu. Tán lá chia thành các tầng khiên nón xếp lớp so le đón tuyết rơi.",
        "micro_geo": "Lá kim mọc thành chùm 5 lá dài cứng cáp, quả thông tím sẫm hình trứng phủ nhựa thơm, lớp vỏ ngoài tróc vảy dày như mai rùa.",
        "pbr": "Principled BSDF: Vỏ thân nâu xám vảy sừng (#451a03), Lá kim xanh đen ánh lục (#064e3b, SSS 0.22, Roughness 0.40), Nhựa thông trong suốt Clearcoat: 0.80.",
    },
    {
        "id": "MG03", "slug": "canopy_giant_sequoia", "cat": "canopy_trees",
        "vn": "Cự Mộc Sequoia Đỏ Bất Tử", "latin": "Sequoiadendron giganteum", "en": "Giant Redwood",
        "family": "Cupressaceae", "biome": "Rừng nguyên sinh hẻo lánh, Hẻm núi sâu (Z: 4m - 12m)",
        "dims": "28.5m (Cao) x 11.5m (Tán)", "poly_lod0": "92,000 tris", "poly_lod1": "24,000 tris",
        "morphology": "Cột thân khổng lồ sừng sững đường kính gốc tới 5.0m, vươn cao chọc thủng tầng mây trời. Thân hình cột thẳng tắp, không có cành ở 12m đầu tiên, tán cây hình chóp nhọn phía trên.",
        "micro_geo": "Vỏ cây dày tới 30cm bằng sợi xốp màu đỏ quế chống cháy rừng và côn trùng, xẻ các rãnh thẳng đứng sâu hoắm. Tán lá kim nhỏ dạng vảy dẹt.",
        "pbr": "Principled BSDF: Vỏ đỏ quế nồng ấm (#9a3412 / #7c2d12, Roughness 0.95, Micro-fibers), Tán lá kim xanh sẫm (#14532d, SSS 0.25).",
    },
    {
        "id": "MG04", "slug": "canopy_baobab", "cat": "canopy_trees",
        "vn": "Baobab Bầu Nước Châu Phi", "latin": "Adansonia digitata", "en": "Grand Baobab",
        "family": "Malvaceae", "biome": "Thảo nguyên đất đỏ khô cằn (Z: 4m - 9m)",
        "dims": "13.5m (Cao) x 14.5m (Tán rễ trời)", "poly_lod0": "68,000 tris", "poly_lod1": "17,500 tris",
        "morphology": "Thân cây phình to hình thùng rượu khổng lồ tích trữ nước, đường kính thân tới 6m. Đỉnh thân trổ các cành khẳng khiu ngoằn ngoèo xòe ra như bộ rễ cây chổng ngược lên trời.",
        "micro_geo": "Vỏ cây nhẵn bóng màu xám ánh đồng có ánh nhũ, thân có các nếp gấp cuồn cuộn như cơ bắp voi khổng lồ.",
        "pbr": "Principled BSDF: Vỏ thân xám đồng nhẵn bóng (#78716c, Roughness 0.45, Clearcoat 0.15), Lá chân vịt 5 lá chét xanh tươi SSS 0.40.",
    },
    {
        "id": "MG05", "slug": "canopy_ancient_banyan", "cat": "canopy_trees",
        "vn": "Đa Búp Đỏ Rễ Bạnh Cổ Đại", "latin": "Ficus macrophylla", "en": "Moreton Bay Fig / Banyan",
        "family": "Moraceae", "biome": "Rừng nhiệt đới hạ lưu, Vùng ẩm ướt (Z: 2m - 7m)",
        "dims": "17.5m (Cao) x 23.0m (Tán trùm)", "poly_lod0": "95,000 tris", "poly_lod1": "25,000 tris",
        "morphology": "Cây chiếm diện tích khổng lồ như một khu rừng nhỏ. Từ các cành lớn buông rủ hàng chục rễ phụ đâm xuống đất hóa thành các cột chống phụ, gốc cây tỏa các phiến rễ bạnh cao ngang ngực người.",
        "micro_geo": "Rễ bạnh mỏng như bức tường lượn sóng tự nhiên bám đất, búp non đỏ thắm bao bọc đầu chồi, lá bầu dục dày cứng bóng loáng.",
        "pbr": "Principled BSDF: Vỏ thân xám sáng vân ngang (#94a3b8), Rễ bạnh phủ rêu xanh ngọc, Lá bóng bẩy Roughness 0.22, Clearcoat 0.35, SSS 0.36, Búp đỏ rực (#dc2626).",
    },
    {
        "id": "MG06", "slug": "canopy_cedar_lebanon", "cat": "canopy_trees",
        "vn": "Tuyết Tùng Lebanon Ngàn Năm", "latin": "Cedrus libani", "en": "Cedar of Lebanon",
        "family": "Pinaceae", "biome": "Rặng núi đá cao đón gió (Z: 8m - 16m)",
        "dims": "15.8m (Cao) x 16.5m (Tán tầng bậc)", "poly_lod0": "78,000 tris", "poly_lod1": "20,000 tris",
        "morphology": "Thân cột to lớn phân cành theo phương ngang tuyệt đối, tạo thành các thảm sàn xanh phẳng lì xếp tầng lớp bậc thang vươn rộng như những chiếc bàn bay xanh biếc.",
        "micro_geo": "Cành ngang uốn lượn có độ cong võng nhẹ ở đầu cành, quả nón hình trứng mọc đứng thẳng trên mặt trên cành như những ngọn nến thơm ngát nhựa.",
        "pbr": "Principled BSDF: Lá kim xanh lục lam (#0f766e, SSS 0.25, Roughness 0.38), Quả nón tím tro phủ phấn trắng, Vỏ thân nứt hình vảy chữ nhật sẫm màu.",
    },
    {
        "id": "MG07", "slug": "canopy_ancient_ironwood", "cat": "canopy_trees",
        "vn": "Thiết Mộc Ngàn Năm", "latin": "Guaiacum officinale", "en": "Ironwood Lignum",
        "family": "Zygophyllaceae", "biome": "Rừng nhiệt đới cổ xưa, Đất sỏi đá (Z: 4m - 10m)",
        "dims": "12.8m (Cao) x 13.8m (Tán tròn đặc)", "poly_lod0": "66,000 tris", "poly_lod1": "16,500 tris",
        "morphology": "Thân cây đanh cứng như thép, thớ gỗ xoắn ốc chằng chịt, vỏ tróc từng mảng tròn để lộ lớp giác gỗ màu xanh rêu ô-liu đặc trưng. Tán lá tròn xoe dày đặc như chiếc ô sắt xanh biếc.",
        "micro_geo": "Gỗ đặc nặng chìm trong nước, thớ xoắn thể hiện bằng displacement vân xoáy sâu, hoa xanh tím sao 5 cánh điểm xuyết rực rỡ.",
        "pbr": "Principled BSDF: Thân xanh ô-liu ánh vàng đồng (#65a30d / #3f6212, Roughness 0.60, Specular 0.50), Hoa tím xanh lam (#3b82f6, SSS 0.55).",
    },

    # -------------------------------------------------------------------------
    # Nhóm 6: Thực Vật Thủy Sinh & Đầm Lầy (Aquatic & Wetland Flora)
    # -------------------------------------------------------------------------
    {
        "id": "AQ01", "slug": "aquatic_water_lily", "cat": "aquatic_wetland",
        "vn": "Hoa Súng Trắng Nước Ngọt", "latin": "Nymphaea alba", "en": "White Water Lily",
        "family": "Nymphaeaceae", "biome": "Mặt hồ trung tâm, Vùng nước lặng (Z: 4.52m)",
        "dims": "0.18m (Cao) x 1.35m (Tán lá)", "poly_lod0": "32,000 tris", "poly_lod1": "7,500 tris",
        "morphology": "Lá tròn dẹt nổi bồng bềnh trên mặt nước có khe khuyết hình chữ V sâu đến cuống. Đóa hoa súng trắng muốt 20-25 cánh xếp nhiều lớp tỏa tròn kiêu sa, nhụy hoa vàng rực.",
        "micro_geo": "Mặt trên lá bóng mượt phủ lớp sáp kỵ nước (Lotus effect) làm nước đọng thành hạt cầu tròn, mặt dưới lá phớt tím có các khoang khí xốp giúp lá nổi.",
        "pbr": "Principled BSDF: Cánh hoa trắng muốt thấu quang cao SSS 0.70 (#ffffff), Nhụy hoa vàng óng (#eab308), Lá mặt trên xanh bóng (#15803d, Roughness 0.15, Clearcoat 0.45), Mặt dưới phớt tím đỏ (#701a75).",
    },
    {
        "id": "AQ02", "slug": "aquatic_sacred_lotus", "cat": "aquatic_wetland",
        "vn": "Sen Hồng Cổ Điển Hoàng Cung", "latin": "Nelumbo nucifera", "en": "Sacred Pink Lotus",
        "family": "Nelumbonaceae", "biome": "Đầm sen cạn, Vịnh lặng nước trong (Z: 4.87m)",
        "dims": "1.25m (Cao) x 1.45m (Tán)", "poly_lod0": "46,000 tris", "poly_lod1": "11,000 tris",
        "morphology": "Khác với hoa súng, lá và hoa sen vươn cao khỏi mặt nước trên cuống gai cứng cáp. Lá hình khiên tròn trũng lòng máng, đóa sen hồng lớn tỏa ngát hương với đài sen hình nón ngược.",
        "micro_geo": "Bát sen đài hoa có các lỗ tròn chứa hạt sen xanh non, nhụy tơ vàng bao quanh đài, cuống lá phủ gai nhọn li ti bảo vệ thân ngập nước.",
        "pbr": "Principled BSDF: Cánh hoa chuyển sắc từ trắng ở gốc sang hồng sen rực rỡ ở ngọn (#f472b6, SSS 0.68), Đài sen vàng lục (#ca8a04), Lá chống thấm tuyệt đối Roughness 0.10, Sheen 0.40.",
    },
    {
        "id": "AQ03", "slug": "aquatic_wetland_reed", "cat": "aquatic_wetland",
        "vn": "Sậy Nước Bờ Hồ", "latin": "Phragmites australis", "en": "Common Wetland Reed",
        "family": "Poaceae", "biome": "Bờ cát bùn ven hồ, Vùng nước ngập nông (Z: 4.2m - 5.5m)",
        "dims": "2.8m (Cao) x 0.85m (Tán)", "poly_lod0": "28,000 tris", "poly_lod1": "6,800 tris",
        "morphology": "Thân sậy cao rỗng dẻo dai màu xanh bóng có ngấn lóng rõ rệt. Lá dài hình mũi mác vuốt nhọn bay phần phật trong gió, ngọn mang chùy hoa lông tơ màu nâu tía xòe nghiêng.",
        "micro_geo": "Chùy hoa gồm hàng ngàn lông tơ mềm mại đung đưa, thân sậy có các mắt gióng rỗng bên trong với màng mỏng.",
        "pbr": "Principled BSDF: Thân sậy xanh bóng (#22c55e, Roughness 0.25, Clearcoat 0.20), Chùy hoa tím tía ánh bạc (#831843, Anisotropic 0.55, Sheen 0.80), SSS: 0.35.",
    },
    {
        "id": "AQ04", "slug": "aquatic_broadleaf_cattail", "cat": "aquatic_wetland",
        "vn": "Cỏ Nến Bồn Bồn Đầm Lầy", "latin": "Typha latifolia", "en": "Broadleaf Cattail",
        "family": "Typhaceae", "biome": "Vũng trũng ngập nước, Bãi đầm lầy ao làng (Z: 4.0m - 5.8m)",
        "dims": "2.2m (Cao) x 0.65m (Tán)", "poly_lod0": "24,000 tris", "poly_lod1": "5,500 tris",
        "morphology": "Lá thẳng đứng dạng dải hẹp uốn dẻo dai. Trục hoa vươn cao mang bông hoa hình trụ tròn đặc trưng màu nâu nhung mềm mại như xúc xích nhung mượt mà, đỉnh có cọng nhụy đực.",
        "micro_geo": "Bông nến nâu có bề mặt vi lông tơ dày đặc (velvet fuzz), khi chín nứt bung ra hàng vạn hạt tơ trắng bay bổng.",
        "pbr": "Principled BSDF: Bông nến nâu sô-cô-la mịn màng (#451a03, Roughness 0.95, Sheen 0.70), Thân và lá xanh lục oliu dẻo dai (#4d7c0f, SSS 0.30, Roughness 0.35).",
    },
    {
        "id": "AQ05", "slug": "aquatic_hornwort", "cat": "aquatic_wetland",
        "vn": "Rong Đuôi Chồn Đáy Hồ", "latin": "Ceratophyllum demersum", "en": "Hornwort Coontail",
        "family": "Ceratophyllaceae", "biome": "Chìm dưới đáy nước trong hồ (Z: 1.5m - 4.2m)",
        "dims": "0.85m (Cao) x 0.32m (Tán)", "poly_lod0": "36,000 tris", "poly_lod1": "8,500 tris",
        "morphology": "Cây chìm hoàn toàn trong nước không có rễ thật, thân uốn lượn mềm mại theo dòng chảy ngầm. Lá chét xẻ đôi hình kim mọc vòng 6-12 lá quanh gióng thân, tạo thành chùm rậm rạp như đuôi chồn.",
        "micro_geo": "Lá có gai cứng siêu nhỏ ở mép giúp thân nổi lơ lửng trong tầng nước, tế bào biểu bì trong suốt cho ánh sáng mặt trời xuyên thấu qua.",
        "pbr": "Principled BSDF: Xanh ngọc lục bảo trong suốt ngập nước, Transmission: 0.35, SSS Weight: 0.55 (#10b981), Roughness: 0.18, Specular IOR: 1.33.",
    },
    {
        "id": "AQ06", "slug": "aquatic_eelgrass", "cat": "aquatic_wetland",
        "vn": "Rong Lươn Nước Sâu", "latin": "Vallisneria americana", "en": "Eelgrass / Tape Grass",
        "family": "Hydrocharitaceae", "biome": "Đáy suối, Lạch nước chảy nhẹ (Z: 2m - 4.5m)",
        "dims": "1.35m (Cao) x 0.22m (Tán)", "poly_lod0": "22,000 tris", "poly_lod1": "5,200 tris",
        "morphology": "Mọc từ thân bò ngầm dưới bùn cát, phóng lên các dải lá ruy-băng dài thon dẹt uốn lượn uyển chuyển theo nhịp sóng nước, đầu lá tròn viền răng cưa nhỏ.",
        "micro_geo": "Dải lá có cấu trúc khoang khí dọc (aerenchyma) tạo các vệt sọc sáng mờ bên trong lòng lá, mềm mại uốn cong hình sin.",
        "pbr": "Principled BSDF: Xanh lá mạ trong trẻo (#22c55e), Transmission: 0.28, SSS: 0.45, Roughness: 0.15, phản chiếu bọt nước li ti bám mặt lá.",
    },
    {
        "id": "AQ07", "slug": "aquatic_umbrella_papyrus", "cat": "aquatic_wetland",
        "vn": "Thủy Trúc Dù Ven Suối", "latin": "Cyperus alternifolius", "en": "Umbrella Papyrus",
        "family": "Cyperaceae", "biome": "Ven lạch suối đá, Vũng nước trong (Z: 3.5m - 5.0m)",
        "dims": "1.4m (Cao) x 0.95m (Tán dù)", "poly_lod0": "26,000 tris", "poly_lod1": "6,000 tris",
        "morphology": "Thân đứng thẳng 3 cạnh nhẵn bóng không lá. Đỉnh thân xòe một vòng 20-30 lá bắc mỏng thuôn dài tỏa tròn đối xứng như chiếc ô xòe râm mát, tâm trổ chùm hoa nâu nhạt.",
        "micro_geo": "Thân tam giác đặc trưng của họ Cói, vành lá dù có góc nghiêng rủ nhẹ 15 độ ở đầu chóp lá.",
        "pbr": "Principled BSDF: Thân xanh ngọc bích nhẵn bóng (#15803d, Roughness 0.25), Lá dù xanh mướt mát SSS 0.40, Chùm hoa tâm vàng nâu sấy khô (#a16207).",
    },

    # -------------------------------------------------------------------------
    # Nhóm 7: Thực Vật Khô Hạn & Mọng Nước (Arid & Succulents)
    # -------------------------------------------------------------------------
    {
        "id": "SC01", "slug": "succulent_saguaro_cactus", "cat": "arid_succulents",
        "vn": "Xương Rồng Trụ Saguaro Cổ Thụ", "latin": "Carnegiea gigantea", "en": "Saguaro Giant Cactus",
        "family": "Cactaceae", "biome": "Sa mạc khô hạn, Sườn đá nung nấu (Z: 5m - 12m)",
        "dims": "8.8m (Cao) x 3.4m (Tán tay)", "poly_lod0": "54,000 tris", "poly_lod1": "13,500 tris",
        "morphology": "Cột thân khổng lồ hình trụ dày đặc các nếp khía dọc sâu như đàn phong cầm. Cây trưởng thành vươn 2-5 cánh tay uốn cong hướng lên trời kiêu hãnh.",
        "micro_geo": "Các khía rãnh dọc phồng xẹp theo lượng nước trữ, bờ khía cắm các quầng gai (areoles) nâu len dày đặc tỏa 15-20 chiếc gai thép cứng dài 5cm nhọn hoắt.",
        "pbr": "Principled BSDF: Thân xanh xám sáp mờ phủ phấn (#047857 / #065f46, Roughness 0.38, SSS mọng nước 0.30), Gai thép màu vàng nâu sừng (#78350f, Roughness 0.20).",
    },
    {
        "id": "SC02", "slug": "succulent_cape_aloe", "cat": "arid_succulents",
        "vn": "Nha Đam Gai Khổng Lồ", "latin": "Aloe ferox", "en": "Bitter Cape Aloe",
        "family": "Asphodelaceae", "biome": "Vách đá khô cằn gió nóng, Bãi sỏi (Z: 4m - 11m)",
        "dims": "2.3m (Cao) x 1.85m (Tán)", "poly_lod0": "38,000 tris", "poly_lod1": "9,200 tris",
        "morphology": "Thân đơn hóa gỗ bao phủ bởi lớp lá già khô héo rủ xuống như chiếc váy bảo vệ thân. Đỉnh trổ đóa hoa hồng khổng lồ gồm các bẹ lá mọng nước dày cộm viền gai đỏ tía nhọn hoắt. Giữa đóa vươn cành hoa lửa cam rực rỡ.",
        "micro_geo": "Thịt lá chứa khối thạch nha đam trong suốt, vỏ lá dày có các gai nhọn màu đỏ cam phân bố cả ở mép lá và hai mặt lưng bụng.",
        "pbr": "Principled BSDF: Lá xanh lam xỉn tráng sáp (#0f766e), SSS 0.50 (thấu quang thạch trong suốt bên trong), Gai đỏ rực (#b91c1c), Chùm hoa lửa cam cháy (#ea580c, SSS 0.60).",
    },
    {
        "id": "SC03", "slug": "succulent_century_agave", "cat": "arid_succulents",
        "vn": "Cây Móng Rồng Agave Kim Nhọn", "latin": "Agave americana", "en": "Century Plant",
        "family": "Asparagaceae", "biome": "Gò đồi đất khô, Đất đá vôi bạc màu (Z: 5m - 14m)",
        "dims": "1.9m (Cao) x 2.5m (Tán hoa hồng)", "poly_lod0": "36,000 tris", "poly_lod1": "8,800 tris",
        "morphology": "Mọc thành đóa hoa hồng gai khổng lồ vĩ đại, gồm 30-40 lá dày hình mũi kiếm uốn lượn chữ S. Mép lá viền gai móc câu cong ngược, chóp lá kết thúc bằng chiếc gai kim nhọn dài 3cm đen nhánh.",
        "micro_geo": "Mặt lá có hoa văn vân in hằn vết của các lá non trước đó khi còn cuộn búp, lớp phấn sáp xanh xám bạc phủ dày.",
        "pbr": "Principled BSDF: Xanh xám tro băng giá (#64748b / #475569), Clearcoat phủ sáp 0.30, Roughness: 0.40, Gai đầu lá đen sẫm bóng (#0f172a).",
    },
    {
        "id": "SC04", "slug": "succulent_prickly_pear", "cat": "arid_succulents",
        "vn": "Xương Rồng Tai Thỏ Hoa Vàng", "latin": "Opuntia microdasys", "en": "Prickly Pear Cactus",
        "family": "Cactaceae", "biome": "Cồn cát khô, Triền sỏi nung nắng (Z: 3m - 9m)",
        "dims": "1.45m (Cao) x 1.55m (Tán)", "poly_lod0": "34,000 tris", "poly_lod1": "8,000 tris",
        "morphology": "Phân nhánh gồm các lóng thân dẹp hình oval tròn trịa xếp tầng so le nhau như những chiếc tai thỏ ngộ nghĩnh. Mặt thân phủ các chấm quầng gai nhung mịn màu vàng tươi, hoa vàng nở rộ ở mép trên đĩa thân.",
        "micro_geo": "Từng quầng gai chứa hàng trăm gai móc li ti (glochids) hình kim chùm, bề mặt thân lồi lõm nhẹ quanh các quầng gai.",
        "pbr": "Principled BSDF: Thân xanh non mọng nước (#16a34a, SSS 0.45), Chùm gai nhung vàng óng (#facc15, Sheen 0.70), Hoa vàng tươi thấu quang (#eab308, SSS 0.65).",
    },
    {
        "id": "SC05", "slug": "succulent_tumbleweed", "cat": "arid_succulents",
        "vn": "Bụi Gai Lăn Sa Mạc", "latin": "Kali tragus", "en": "Tumbleweed Skeleton",
        "family": "Amaranthaceae", "biome": "Đồng cát lộng gió, Đất khô nứt nẻ (Z: 3m - 10m)",
        "dims": "0.95m (Cao) x 0.95m (Khung cầu)", "poly_lod0": "30,000 tris", "poly_lod1": "7,200 tris",
        "morphology": "Khi chết khô, cây tự đứt lìa gốc để tạo thành một khối cầu gai cành khẳng khiu rỗng ruột tròn xoe, lăn lông lốc theo gió lốc sa mạc để phát tán hạt giống khắp miền hoang dã.",
        "micro_geo": "Mạng lưới cành nhánh đan chéo rối rắm phân nhánh nhị phân, các đốt cành có gai nhọn nhỏ khô giòn.",
        "pbr": "Principled BSDF: Màu vàng rơm khô xơ xác (#d97706 / #b45309), Roughness cực cao 0.92, không có SSS, bề mặt khô mốc có bụi cát bám.",
    },
    {
        "id": "SC06", "slug": "succulent_desert_rose", "cat": "arid_succulents",
        "vn": "Sứ Sa Mạc Thân Phình", "latin": "Adenium obesum", "en": "Desert Rose",
        "family": "Apocynaceae", "biome": "Khe vách đá sa mạc, Đất sỏi khô (Z: 5m - 12m)",
        "dims": "1.65m (Cao) x 1.25m (Tán)", "poly_lod0": "42,000 tris", "poly_lod1": "10,200 tris",
        "morphology": "Gốc thân phình to dị dạng như bình củ khổng lồ tích nước uốn lượn kỳ quái bọc lớp vỏ xám nhẵn. Đỉnh các cành ngắn bung nở chùm hoa cánh sen đỏ thắm rực rỡ tương phản mạnh mẽ.",
        "micro_geo": "Gốc củ có các nếp nhăn và rễ phụ bám đá, hoa hình chuông loe 5 cánh chuyển sắc tuyệt đẹp từ trắng tâm sang đỏ tươi viền ngoài.",
        "pbr": "Principled BSDF: Gốc củ xám lục nhẵn bóng (#64748b, Roughness 0.40), Cánh hoa chuyển sắc đỏ hồng SSS 0.65 (#e11d48), Lá xanh bóng dày Roughness 0.25.",
    },
    {
        "id": "SC07", "slug": "succulent_burros_tail", "cat": "arid_succulents",
        "vn": "Móng Lừa Chuỗi Ngọc Rủ", "latin": "Sedum morganianum", "en": "Burro's Tail",
        "family": "Crassulaceae", "biome": "Vách đá dốc cheo leo, Hốc đá khô (Z: 7m - 15m)",
        "dims": "0.65m (Cao) x 0.42m (Chuỗi rủ)", "poly_lod0": "28,000 tris", "poly_lod1": "6,800 tris",
        "morphology": "Thân buông thõng rủ dài xuống vách đá, bọc kín bởi hàng trăm lá mọng nước hình hạt ngọc thuôn dài xếp chồng so le nhau như vảy rồng hay bím tóc xanh lam.",
        "micro_geo": "Từng hạt lá mọng nước tròn trịa căng đầy như viên ngọc, phủ lớp phấn mờ màu xanh ngọc lam phấn bạc mờ ảo.",
        "pbr": "Principled BSDF: Xanh ngọc lam phấn bạc (#0d9488 / #5eead4), SSS cực cao 0.60 (thấu quang ngậm nước lấp lánh), Clearcoat sáp 0.35, Roughness 0.28.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 8: Ăn Thịt, Ký Sinh & Hang Động Phát Quang (Carnivorous, Vines & Cave)
    # -------------------------------------------------------------------------
    {
        "id": "EX01", "slug": "carnivorous_pitcher_plant", "cat": "carnivorous_vines",
        "vn": "Cây Bắt Mồi Nắp Ấm Khổng Lồ", "latin": "Nepenthes rajah", "en": "Giant Pitcher Plant",
        "family": "Nepenthaceae", "biome": "Rừng mưa nhiệt đới ẩm, Vách đá mùn (Z: 3m - 8m)",
        "dims": "1.25m (Cao) x 1.55m (Tán)", "poly_lod0": "56,000 tris", "poly_lod1": "14,000 tris",
        "morphology": "Dây leo bò mang các lá to có gân giữa kéo dài thành tua cuốn, đầu tua phình to biến thành bình ấm khổng lồ dung tích tới 3.5 lít màu đỏ tía rực rỡ, miệng ấm có vành răng cưa và nắp che mưa.",
        "micro_geo": "Vành miệng ấm (peristome) xếp các nếp sọc gờ răng cưa siêu trơn trượt phủ mật hoa quyến rũ con mồi rơi vào dung dịch enzym tiêu hóa bên trong bình.",
        "pbr": "Principled BSDF: Bình ấm đỏ tía vân sọc vàng cam (#9f1239 / #f59e0b), SSS 0.55 thấu quang dạ dịch, Vành miệng trơn bóng Roughness 0.10, Clearcoat 0.80, Mặt trong tiết dịch tráng men.",
    },
    {
        "id": "EX02", "slug": "carnivorous_venus_flytrap", "cat": "carnivorous_vines",
        "vn": "Bẫy Kẹp Venus Răng Cưa", "latin": "Dionaea muscipula", "en": "Venus Flytrap",
        "family": "Droseraceae", "biome": "Đầm lầy than bùn thiếu đạm, Bãi ngập ẩm (Z: 3m - 6m)",
        "dims": "0.28m (Cao) x 0.38m (Tán bẫy)", "poly_lod0": "32,000 tris", "poly_lod1": "7,800 tris",
        "morphology": "Cụm hoa hình hoa thị sát đất, cuống lá dẹp hình tim mang chiếc bẫy kẹp 2 mảnh hình bán nguyệt úp vào nhau. Viền mép bẫy cắm các răng gai nhọn đan khít vào nhau như chấn song ngục khi bẫy sập.",
        "micro_geo": "Mặt trong lòng bẫy có 3 sợi lông cảm ứng siêu nhạy (trigger hairs), khi con mồi chạm 2 lần trong 20 giây sẽ kích hoạt bẫy sập lại chỉ trong 1/10 giây.",
        "pbr": "Principled BSDF: Lòng bẫy đỏ hồng tươi tiết mật quyến rũ (#ef4444, SSS 0.65), Vỏ ngoài xanh non (#22c55e), Răng gai nhọn cứng cáp sáp mờ Roughness 0.30.",
    },
    {
        "id": "EX03", "slug": "carnivorous_sundew", "cat": "carnivorous_vines",
        "vn": "Cây Bắt Ruồi Bọt Nước", "latin": "Drosera capensis", "en": "Cape Sundew",
        "family": "Droseraceae", "biome": "Bãi rêu bùn ẩm ướt nghèo dinh dưỡng (Z: 3m - 7m)",
        "dims": "0.32m (Cao) x 0.28m (Tán)", "poly_lod0": "42,000 tris", "poly_lod1": "10,000 tris",
        "morphology": "Các dải lá thuôn dài mọc tỏa từ gốc, toàn bộ mặt trên lá phủ dày đặc hàng trăm xúc tu lông tuyến màu đỏ hồng, đỉnh mỗi xúc tu mang giọt chất nhầy trong suốt lấp lánh như giọt sương mai dưới nắng.",
        "micro_geo": "Giọt nhầy có sức căng bề mặt tạo khối cầu trong suốt hoàn hảo có tính dẻo quánh, khi con mồi dính vào thì các xúc tu sẽ uốn cong cuộn tròn lá lại bọc lấy con mồi.",
        "pbr": "Principled BSDF: Giọt nhầy trong suốt hoàn hảo Transmission: 0.95, Roughness: 0.05, IOR: 1.34, Xúc tu lông tơ đỏ tía (#be123c, SSS 0.70), Phiến lá xanh non dẻo mềm.",
    },
    {
        "id": "EX04", "slug": "carnivorous_jungle_liana", "cat": "carnivorous_vines",
        "vn": "Dây Leo Cổ Đại Liana Rừng Già", "latin": "Liana gigantica", "en": "Ancient Jungle Vine",
        "family": "Bignoniaceae", "biome": "Ký sinh vòm đại thụ, Rừng mưa nhiệt đới (Z: 2m - 16m)",
        "dims": "16.0m (Dài) x 2.2m (Tán leo)", "poly_lod0": "58,000 tris", "poly_lod1": "14,200 tris",
        "morphology": "Thân dây leo hóa gỗ to bằng bắp đùi uốn lượn thắt nút xoắn ốc như dây thừng khổng lồ leo quanh thân đại thụ vươn lên đón nắng tầng tán rừng. Dọc thân rủ các chùm hoa hình kèn màu cam cháy lộng lẫy.",
        "micro_geo": "Vỏ thân có các đường gân xoắn vặn và rễ bám đâm sâu vào kẽ vỏ cây chủ, tua cuốn đàn hồi có cơ chế co xoắn như lò xo thép.",
        "pbr": "Principled BSDF: Vỏ thân dây nâu xám nứt nẻ gân guốc (#451a03, Roughness 0.90), Hoa hình kèn cam rực lửa (#f97316, SSS 0.58), Lá hình tim bóng bẩy.",
    },
    {
        "id": "EX05", "slug": "cave_bioluminescent_mushroom", "cat": "cave_bioluminescent",
        "vn": "Nấm Mũ Xanh Dạ Quang", "latin": "Mycena chlorophos", "en": "Bioluminescent Ghost Mushroom",
        "family": "Mycenaceae", "biome": "Hang ngầm Karst sâu thẳm, Gỗ mục ẩm ướt (Z: -7m đến -2m)",
        "dims": "0.48m (Cao) x 0.52m (Cụm tán)", "poly_lod0": "36,000 tris", "poly_lod1": "8,500 tris",
        "morphology": "Mọc thành cụm 3-7 cây nấm thân thanh mảnh trên thân gỗ mục trong hang tối. Mũ nấm hình bán cầu xòe rộng, dưới mũ là hệ thống phiến nấm tỏa tia phát ra ánh sáng lục ngọc lam huỳnh quang kỳ ảo.",
        "micro_geo": "Phiến nấm mỏng tang xếp nan hoa tỏa từ cuống ra rìa mũ, mặt trên mũ phủ lớp chất nhầy gelatin trong mờ giúp khuếch tán ánh sáng dạ quang ra không gian xung quanh.",
        "pbr": "Principled BSDF + Emission Shader: Mũ nấm màu xanh ngọc lam (#06b6d4 / #10b981), Emission Strength: 5.5 lux chiếu sáng rực rỡ bóng đêm hang động, SSS: 0.60 mờ ảo, Cuống nấm trắng mờ trong suốt (#f8fafc).",
    },
    {
        "id": "EX06", "slug": "cave_luminescent_moss", "cat": "cave_bioluminescent",
        "vn": "Thảm Rêu Huỳnh Quang Động Karst", "latin": "Schistostega pennata", "en": "Luminescent Cave Moss",
        "family": "Schistostegaceae", "biome": "Vách đá hang ngầm, Khe nứt đá vôi tối (Z: -8m đến -1m)",
        "dims": "0.06m (Cao) x 1.1m (Thảm mảng)", "poly_lod0": "32,000 tris", "poly_lod1": "7,800 tris",
        "morphology": "Bám thành từng mảng xanh ngọc phát sáng lấp lánh trên vách đá hang ẩm ướt như những viên ngọc lục bảo ẩn giấu trong lòng đất.",
        "micro_geo": "Tế bào thể sơ sợi (protonema) có dạng thấu kính lồi hình cầu hội tụ các tia sáng yếu ớt của hang động phản chiếu ngược lại ra ngoài, tạo cảm giác rêu tự phát sáng huỳnh quang lấp lánh.",
        "pbr": "Principled BSDF + Emission mờ: Màu xanh ngọc lục bảo rực sáng (#10b981), Emission Strength: 2.8 lux, Sheen: 0.95, SSS: 0.55 tạo chiều sâu ngậm sương.",
    },
    {
        "id": "EX07", "slug": "cave_bracket_fungi", "cat": "cave_bioluminescent",
        "vn": "Nấm Vành Tầng Động Tiên", "latin": "Trametes versicolor", "en": "Rainbow Bracket Fungi",
        "family": "Polyporaceae", "biome": "Vách đá hang ẩm, Gốc cây cổ hóa thạch (Z: -6m đến 0m)",
        "dims": "0.35m (Cao) x 0.85m (Tầng quạt)", "poly_lod0": "28,000 tris", "poly_lod1": "6,800 tris",
        "morphology": "Các phiến nấm dạng quạt vỏ sò xếp tầng chồng lên nhau bậc thang trên vách đá. Mặt trên mũ nấm có các dải màu vân tròn đồng tâm tuyệt đẹp đan xen giữa xanh lam, tím, nâu sẫm và viền trắng sứ phát quang.",
        "micro_geo": "Bề mặt phủ lớp lông nhung vi mô, mép vành lượn sóng mềm mại, mặt dưới có hàng ngàn lỗ thoát bào tử li ti.",
        "pbr": "Principled BSDF + Viền phát quang: Mặt trên các dải màu đồng tâm (#1e1b4b / #4338ca / #14b8a6), viền ngoài màu trắng phát quang nhẹ Emission 2.2 lux, Roughness: 0.45.",
    },
]

def generate_spec_md(sp):
    return f"""# Đặc Tả Thực Vật 3D: {sp['vn']} ({sp['latin']})

> [!NOTE]
> **Nhóm Hình Thái**: {sp['cat'].replace('_', ' ').title()}  
> **Họ Thực Vật**: *{sp['family']}*  
> **Danh Pháp Khoa Học**: *{sp['latin']}* (Tên Tiếng Anh: **{sp['en']}**)  
> **Sinh Cảnh Tự Nhiên**: {sp['biome']}  
> **Kích Thước Hình Học**: {sp['dims']}  
> **Quy Chuẩn 3D**: **Hyper-Realistic Scan-Quality**

---

## 1. Giải Phẫu Học & Hình Thái Thực Vật (Botanical Morphology)

### 1.1 Cấu Trúc Tổng Quan
{sp['morphology']}

### 1.2 Cấu Trúc Vi Mô & Chi Tiết Scan (Micro-Geometry)
{sp['micro_geo']}

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Architecture)

| Thông Số Kỹ Thuật | Tiêu Chuẩn Thực Thi | Ghi Chú Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Scan-Quality)** | **{sp['poly_lod0']}** | Lưới Quads 100%, Manifold, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **{sp['poly_lod1']}** | Tối ưu hóa cho thời gian thực, giữ nguyên Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 tris | Dạng Billboard / Low-poly cho góc nhìn xa toàn cảnh |
| **Smooth Shading** | `use_smooth = True` | Áp dụng 100% toàn bộ mặt đa giác |
| **UV Unwrapping** | Non-overlapping | Mật độ Texel Density đồng đều (2048 px/m) |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Graph)

Vật liệu được thiết kế trên hệ thống **Principled BSDF** của Blender 5.2.1 LTS với các đặc tính sinh học tiên tiến:

- **Shader Profile**: `{sp['pbr']}`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực độ tán xạ ánh sáng xuyên thấu qua mô tế bào diệp lục và cánh hoa mỏng.
- **Normal & Micro-Displacement**: Tạo rãnh vỏ nứt nẻ, gân lá nổi khối 3D, độ nhám sáp bảo vệ bề mặt.
- **Color Management**: Tương thích hoàn hảo với không gian màu **AgX (Medium High Contrast)**.

---

## 4. Đường Dẫn File Tài Nguyên 3D (Direct Asset Links)

Toàn bộ mô hình 3D, file nguồn Blender và code tạo hình tự động được liên kết trực tiếp dưới đây:

- 🎨 **Mô hình 3D Gốc Blender**: [`{sp['slug']}.blend`](file://{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.blend)
- 🚀 **Mô hình Xuất Xưởng glTF/GLB**: [`{sp['slug']}.glb`](file://{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.glb)
- 🐍 **Bộ Mã Nguồn Sinh 3D Tự Động**: [`{sp['slug']}_builder.py`](file://{ROOT}/assets/flora/generators/{sp['slug']}_builder.py)

---

## 5. Hướng Dẫn Nạp Vào Thế Giới Genesis Zero

```python
import bpy

# Nạp model 3D vào collection Flora_Instances
filepath = "{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.glb"
bpy.ops.import_scene.gltf(filepath=filepath)
imported_obj = bpy.context.selected_objects[0]
imported_obj.name = "Flora_{sp['slug'].title().replace('_', '')}"
print(f"Đã nạp thành công {{imported_obj.name}} vào thế giới!")
```
"""

def main():
    print(f">>> Đang khởi tạo 56 file đặc tả thực vật Hyper-Realistic Scan-Quality...")
    created_count = 0
    for sp in SPECIES_DATA:
        filename = f"{sp['slug']}.md"
        filepath = SPECIES_DIR / filename
        content = generate_spec_md(sp)
        filepath.write_text(content, encoding="utf-8")
        created_count += 1
    print(f"✓ Đã tạo thành công {created_count} file đặc tả thực vật tại: {SPECIES_DIR}")

if __name__ == "__main__":
    main()

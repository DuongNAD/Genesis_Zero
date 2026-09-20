#!/usr/bin/env python3
"""
generate_100_flora.py - Generates 100 Hyper-Realistic Scan-Quality Botanical Specs and Master Catalog
Genesis Zero - Ultra-Realistic Botanical Asset Ecosystem
"""

from pathlib import Path

ROOT = Path("/Users/duongnad/Documents/project/Genesis_Zero")
DOCS_DIR = ROOT / "docs" / "flora"
SPECIES_DIR = DOCS_DIR / "species"

SPECIES_DIR.mkdir(parents=True, exist_ok=True)

# 100 Botanical Species Dataset
DATA = [
    # -------------------------------------------------------------------------
    # Nhóm 1: Họ Cỏ, Rêu & Thảm Mặt Đất (12 loài)
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
        "morphology": "Cuống mảnh uốn lượn mang bộ 3 lá chét hình tim ngược, mặt lá có vệt chữ V màu trắng sữa đặc trưng. Điểm xuyết hoa đầu tròn màu trắng ngà cánh bướm.",
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
    {
        "id": "GR08", "slug": "grass_switchgrass", "cat": "grasses_herbs",
        "vn": "Cỏ Đuôi Phụng Thảo Nguyên", "latin": "Panicum virgatum", "en": "Switchgrass",
        "family": "Poaceae", "biome": "Đồng bằng trung tâm, Bờ suối cạn (Z: 4m - 9m)",
        "dims": "1.6m (Cao) x 0.8m (Tán)", "poly_lod0": "24,000 tris", "poly_lod1": "5,800 tris",
        "morphology": "Thân cỏ cao thẳng đứng mọc thành cụm bụi lớn, mùa thu đổi sang sắc vàng óng ả. Chùy hoa phân nhánh mở rộng tạo thành đám mây hạt bay lơ lửng.",
        "micro_geo": "Khớp thân gióng đốt nổi u tròn, phiến lá dài hình dải hẹp uốn võng tự nhiên.",
        "pbr": "Principled BSDF: Xanh vàng hổ phách (#d97706), SSS: 0.32, Roughness: 0.40, Sheen: 0.50.",
    },
    {
        "id": "GR09", "slug": "grass_sphagnum_moss", "cat": "grasses_herbs",
        "vn": "Rêu Than Bùn Đầm Lầy", "latin": "Sphagnum palustre", "en": "Sphagnum Peat Moss",
        "family": "Sphagnaceae", "biome": "Vùng đầm lầy trũng, Bờ than bùn (Z: 3.5m - 5m)",
        "dims": "0.15m (Cao) x 1.6m (Mảng phủ)", "poly_lod0": "30,000 tris", "poly_lod1": "7,500 tris",
        "morphology": "Cây rêu phân nhánh hình đầu cúc tròn, chứa các tế bào rỗng ngậm nước gấp 20 lần trọng lượng khô, tạo thành thảm phồng êm như đệm hơi.",
        "micro_geo": "Đầu cành mọc tụ lại thành chỏm hình sao xốp mịn, thân rủ nhiều cành rủ áp sát thân chính.",
        "pbr": "Principled BSDF: Chuyển sắc từ xanh nõn chuối ở ngọn sang vàng đồng rỉ sét ở đáy (#84cc16 / #b45309), Transmission ngậm nước 0.20, SSS 0.60.",
    },
    {
        "id": "GR10", "slug": "grass_needle_burr", "cat": "grasses_herbs",
        "vn": "Cỏ May Xước Đồng Hoang", "latin": "Chrysopogon aciculatus", "en": "Needle Burr Grass",
        "family": "Poaceae", "biome": "Lối mòn khô cằn, Vùng chân núi (Z: 5m - 11m)",
        "dims": "0.35m (Cao) x 0.4m (Tán)", "poly_lod0": "16,500 tris", "poly_lod1": "4,000 tris",
        "morphology": "Thân bò lan bám rễ chặt chẽ dưới đất, phóng các cọng hoa mang chùm quả gai nhọn có móc ngược bám vào lông động vật di cư.",
        "micro_geo": "Gai hạt có ngạnh ngược siêu nhỏ sắc bén, cọng hoa màu phớt tím cứng cáp.",
        "pbr": "Principled BSDF: Thân xanh xám bóng (#4d7c0f), Gai hạt ánh tím hung (#581c87, Roughness 0.30, Specular 0.40).",
    },
    {
        "id": "GR11", "slug": "grass_goosegrass", "cat": "grasses_herbs",
        "vn": "Cỏ Mần Trầu Dược Liệu", "latin": "Eleusine indica", "en": "Wiregrass / Goosegrass",
        "family": "Poaceae", "biome": "Vành đai làng, Bãi cỏ sinh hoạt (Z: 4m - 8m)",
        "dims": "0.45m (Cao) x 0.5m (Tán xòe)", "poly_lod0": "18,000 tris", "poly_lod1": "4,400 tris",
        "morphology": "Gốc phân nhánh tỏa tròn sát mặt đất như nan hoa xe bò, cọng hoa dẹt cứng mang 3-7 bông hình chân vịt xòe ở đỉnh.",
        "micro_geo": "Bông hoa xếp hai hàng bông con hình ngói lợp sít sao, thân cọng có gân gờ sắc cạnh chịu giẫm đạp.",
        "pbr": "Principled BSDF: Xanh lục sáng mướt mát (#22c55e), SSS: 0.35, Roughness: 0.32.",
    },
    {
        "id": "GR12", "slug": "grass_liverwort", "cat": "grasses_herbs",
        "vn": "Rêu Rồng Xanh Vách Thác", "latin": "Marchantia polymorpha", "en": "Umbrella Liverwort",
        "family": "Marchantiaceae", "biome": "Vách đá ẩm cạnh thác nước đổ (Z: 2m - 7m)",
        "dims": "0.04m (Cao) x 0.8m (Mảng phiến)", "poly_lod0": "25,000 tris", "poly_lod1": "6,200 tris",
        "morphology": "Tản lá hình dải xanh đậm chia thùy như vảy rồng bám chặt mặt đá ướt át. Mặt trên tản mang các chén truyền thể hình chén hoa và các cây dù tí hon mang bào tử.",
        "micro_geo": "Bề mặt tản phân chia thành các ô đa giác hình thoi lồi có lỗ khí khổng ở tâm, chén truyền thể đựng các hạt mầm tròn tí hon.",
        "pbr": "Principled BSDF: Xanh ngọc lục thẫm ướt bóng (#047857), Clearcoat 0.65 (màng nước bóng loáng), SSS: 0.48.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 2: Thảo Mộc & Hoa Rừng Hoang Dã (14 loài)
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
    {
        "id": "FL08", "slug": "flower_wild_sunflower", "cat": "grasses_herbs",
        "vn": "Hoa Hướng Dương Dại", "latin": "Helianthus annuus", "en": "Wild Prairie Sunflower",
        "family": "Asteraceae", "biome": "Đồng cỏ hoang dã ngập nắng (Z: 5m - 10m)",
        "dims": "1.85m (Cao) x 0.75m (Tán)", "poly_lod0": "32,000 tris", "poly_lod1": "7,800 tris",
        "morphology": "Thân thô ráp có lông cứng ráp, mang lá hình tim lớn ráp nhám. Đỉnh thân trổ đóa hướng dương rực rỡ với đĩa nhụy hạt nâu sẫm và vành cánh vàng nghệ chói chang luôn hướng theo vệt mặt trời.",
        "micro_geo": "Đĩa hạt xếp theo mẫu hình xoắn ốc kép Fibonacci lộng lẫy, từng cánh hoa có các rãnh gân chạy dọc song song.",
        "pbr": "Principled BSDF: Cánh hoa vàng nghệ rực rỡ (#eab308, SSS 0.55), Nhụy nâu sẫm hạt (#451a03, Roughness 0.90), Thân lá xanh nhám (#15803d).",
    },
    {
        "id": "FL09", "slug": "flower_purple_coneflower", "cat": "grasses_herbs",
        "vn": "Hoa Cúc Tím Echinacea", "latin": "Echinacea purpurea", "en": "Purple Coneflower",
        "family": "Asteraceae", "biome": "Thảo nguyên đón nắng, Bìa rừng sỏi (Z: 4m - 9m)",
        "dims": "1.1m (Cao) x 0.5m (Tán)", "poly_lod0": "26,000 tris", "poly_lod1": "6,200 tris",
        "morphology": "Thân thẳng cứng cáp mang đóa hoa có tâm hình nón nhô cao như tổ ong gai màu cam đồng, bao quanh bởi các cánh hoa dài màu tím hồng rủ nhẹ xuống dưới.",
        "micro_geo": "Tâm nón gồm các gai nhọn cứng sắc nhọn hình vảy nến, cánh hoa rủ cong duyên dáng có rãnh uốn lượn.",
        "pbr": "Principled BSDF: Cánh hoa tím hồng rực (#d946ef, SSS 0.50), Tâm nón màu cam cháy đồng thiếc (#c2410c, Roughness 0.40, Specular 0.60).",
    },
    {
        "id": "FL10", "slug": "flower_morning_glory", "cat": "grasses_herbs",
        "vn": "Cây Hoa Bìm Bìm Rừng", "latin": "Ipomoea purpurea", "en": "Morning Glory",
        "family": "Convolvulaceae", "biome": "Bờ rào đá làng, Bụi rậm ven suối (Z: 3m - 7m)",
        "dims": "2.2m (Leo dài) x 0.8m (Tán)", "poly_lod0": "22,000 tris", "poly_lod1": "5,500 tris",
        "morphology": "Dây leo cuốn uốn lượn mang lá hình tim xanh mướt. Sáng sớm bung nở những đóa hoa hình phễu kèn trumpet màu xanh lam tím chuyển hồng ở tâm, xòe tròn như chiếc váy dạ hội.",
        "micro_geo": "Ống tràng hoa liền mảnh 5 góc gấp nếp ngôi sao tinh xảo, nhụy hoa trắng ngà ẩn trong đáy phễu sâu.",
        "pbr": "Principled BSDF: Cánh hoa lam tím chuyển hồng tâm (#3b82f6 / #ec4899), SSS 0.60 mỏng manh trong suốt đón bình minh, Roughness 0.25.",
    },
    {
        "id": "FL11", "slug": "flower_wild_geranium", "cat": "grasses_herbs",
        "vn": "Hoa Phong Lữ Dại Rừng Sồi", "latin": "Geranium maculatum", "en": "Wild Geranium",
        "family": "Geraniaceae", "biome": "Dưới tán rừng râm mát, Đất mùn (Z: 4m - 8m)",
        "dims": "0.55m (Cao) x 0.45m (Tán)", "poly_lod0": "20,000 tris", "poly_lod1": "4,800 tris",
        "morphology": "Lá xẻ thùy chân vịt sâu 5 nhánh răng cưa nhọn, hoa 5 cánh màu hồng tím hoa cà có các đường gân chỉ tím đậm dẫn đường cho ong bướm vào tâm hoa nhụy vàng.",
        "micro_geo": "Các vệt gân chỉ tím nổi vi mô sắc nét trên nền cánh hoa mịn màng, cuống quả có mỏ chim dài đặc trưng.",
        "pbr": "Principled BSDF: Hồng tím hoa cà (#c084fc) kèm gân tím đậm (#6b21a8), SSS: 0.52, Lá xanh lục xẻ răng cưa SSS 0.38.",
    },
    {
        "id": "FL12", "slug": "flower_sweet_flag", "cat": "grasses_herbs",
        "vn": "Cây Xương Bồ Thơm Bờ Suối", "latin": "Acorus calamus", "en": "Sweet Flag",
        "family": "Acoraceae", "biome": "Bờ suối sỏi đá, Rãnh nước nông (Z: 3m - 5m)",
        "dims": "0.9m (Cao) x 0.6m (Tán)", "poly_lod0": "18,500 tris", "poly_lod1": "4,400 tris",
        "morphology": "Lá dài hình lưỡi kiếm màu xanh bóng có gân giữa nổi rõ, tỏa hương thơm ngát khi vò nhẹ. Từ nách lá trổ bông hoa hình bắp ngô màu vàng lục nghiêng một bên.",
        "micro_geo": "Bông mo trụ dài phủ đầy hoa nhỏ xíu không cánh xếp vảy sít sao như da rắn.",
        "pbr": "Principled BSDF: Lá xanh lục tươi phủ sáp bóng (#16a34a, Roughness 0.22, Clearcoat 0.30), Bông hoa vàng lục oliu (#84cc16).",
    },
    {
        "id": "FL13", "slug": "flower_wormwood", "cat": "grasses_herbs",
        "vn": "Cây Ngải Đắng Rừng", "latin": "Artemisia absinthium", "en": "Wormwood",
        "family": "Asteraceae", "biome": "Đồi khô sỏi đá, Vùng nắng gắt (Z: 6m - 12m)",
        "dims": "1.0m (Cao) x 0.7m (Tán)", "poly_lod0": "26,000 tris", "poly_lod1": "6,500 tris",
        "morphology": "Cây bán bụi màu trắng bạc tro do toàn thân và lá xẻ nhiều lần phủ dày đặc lớp lông tơ tằm mịn màng. Cành trổ vô số hoa đầu tròn li ti màu vàng rơm rủ xuống.",
        "micro_geo": "Lớp lông tơ màu bạc khúc xạ ánh sáng mặt trời bảo vệ cây chống mất nước và tia cực tím sa mạc.",
        "pbr": "Principled BSDF: Màu xanh bạc ánh ngọc trai (#cbd5e1 / #94a3b8), Sheen: 0.85, Roughness: 0.65, SSS: 0.28.",
    },
    {
        "id": "FL14", "slug": "flower_snowdrop", "cat": "grasses_herbs",
        "vn": "Hoa Giọt Tuyết Đầu Xuân", "latin": "Galanthus nivalis", "en": "Common Snowdrop",
        "family": "Amaryllidaceae", "biome": "Băng tuyết tan, Bìa rừng mùa xuân (Z: 8m - 15m)",
        "dims": "0.18m (Cao) x 0.15m (Tán)", "poly_lod0": "14,000 tris", "poly_lod1": "3,400 tris",
        "morphology": "Vươn mình xuyên qua lớp tuyết trắng lạnh giá, cuống hoa cong hình cần câu treo đóa hoa trắng muốt rủ xuống như giọt tuyết ngọc bích, 3 cánh ngoài trắng tinh, 3 cánh trong viền đốm xanh lục.",
        "micro_geo": "Đốm xanh lục hình móng ngựa ở đầu cánh trong, cánh hoa ngoài thon dài hình muỗng úp.",
        "pbr": "Principled BSDF: Cánh hoa trắng tuyết trong mờ (#ffffff, SSS 0.75), Đốm xanh lục bảo (#16a34a), Cuống lá xanh băng giá.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 3: Cây Bụi & Dương Xỉ Tầng Dưới (14 loài)
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
    {
        "id": "SH08", "slug": "shrub_birds_nest_fern", "cat": "understory_shrubs",
        "vn": "Dương Xỉ Tổ Chim Rừng Mưa", "latin": "Asplenium nidus", "en": "Bird's Nest Fern",
        "family": "Aspleniaceae", "biome": "Bám trên chạc ba cây to, Hốc đá ẩm (Z: 3m - 9m)",
        "dims": "1.1m (Cao) x 1.3m (Tán tròn)", "poly_lod0": "32,000 tris", "poly_lod1": "7,800 tris",
        "morphology": "Các phiến lá đơn nguyên lớn hình dải thuôn màu xanh nõn chuối bóng loáng mọc tỏa tròn tạo thành hình chiếc tổ chim hứng lá rụng làm mùn dinh dưỡng.",
        "micro_geo": "Gân chính giữa lá màu đen nâu nổi gồ cứng cáp, mép lá hơi lượn sóng nhấp nhô.",
        "pbr": "Principled BSDF: Xanh nõn chuối thấu quang cao (#84cc16), Clearcoat: 0.35, SSS: 0.50, Gân sống lưng nâu đen (#292524).",
    },
    {
        "id": "SH09", "slug": "shrub_wild_hydrangea", "cat": "understory_shrubs",
        "vn": "Bụi Cẩm Tú Cầu Rừng", "latin": "Hydrangea macrophylla", "en": "Wild Forest Hydrangea",
        "family": "Hydrangeaceae", "biome": "Khe núi suối ẩm, Tán rừng thưa (Z: 4m - 9m)",
        "dims": "1.6m (Cao) x 1.8m (Tán tròn)", "poly_lod0": "48,000 tris", "poly_lod1": "11,800 tris",
        "morphology": "Bụi cây tán tròn rậm rạp mang những quả cầu hoa khổng lồ đường kính 25cm chuyển sắc kỳ ảo giữa xanh lam, tím thạch anh và hồng phấn tùy độ phèn đất.",
        "micro_geo": "Quả cầu hoa cấu thành từ hàng trăm đóa hoa 4 cánh nhỏ vô tính xếp lợp ngói tỉ mỉ.",
        "pbr": "Principled BSDF: Chuyển sắc ombre xanh lam tím (#3b82f6 / #a855f7), SSS: 0.55 mờ ảo, Lá xanh thẫm có răng cưa lớn.",
    },
    {
        "id": "SH10", "slug": "shrub_wild_blackberry", "cat": "understory_shrubs",
        "vn": "Cây Dâu Rừng Gai Đen", "latin": "Rubus fruticosus", "en": "Wild Blackberry Bush",
        "family": "Rosaceae", "biome": "Bìa rừng, Hàng rào đá, Bụi gai rậm (Z: 3m - 8m)",
        "dims": "1.8m (Cao) x 2.2m (Tán gai)", "poly_lod0": "46,000 tris", "poly_lod1": "11,200 tris",
        "morphology": "Cành nhánh dạng cung vươn dài chằng chịt vũ trang bằng vô số gai móc câu sắc nhọn. Chùm quả mọng chuyển từ xanh sang đỏ và đen bóng căng mọng khi chín.",
        "micro_geo": "Quả tụ cấu tạo từ 20-30 quả hạch nhỏ li ti ghép lại, từng hạt mọng có một sợi râu tơ ở đỉnh.",
        "pbr": "Principled BSDF: Quả đen bóng (#0f172a, Clearcoat 0.60, Roughness 0.15, SSS 0.40), Gai móc đỏ hung nhọn hoắt (#991b1b).",
    },
    {
        "id": "SH11", "slug": "shrub_bay_laurel", "cat": "understory_shrubs",
        "vn": "Bụi Nguyệt Quế Thơm", "latin": "Laurus nobilis", "en": "Bay Laurel Shrub",
        "family": "Lauraceae", "biome": "Sườn đồi đón nắng, Vùng đất đá (Z: 5m - 11m)",
        "dims": "2.8m (Cao) x 2.2m (Tán)", "poly_lod0": "38,000 tris", "poly_lod1": "9,400 tris",
        "morphology": "Cây bụi thường xanh tán dày, lá bầu dục dày cứng mép lượn sóng màu xanh đậm bóng loáng chứa nhiều tinh dầu thơm, quả mọng hình trứng đen bóng.",
        "micro_geo": "Phiến lá dai như da thuộc, mặt trên nhẵn bóng có cutin dày, mặt dưới nhạt màu có gân phụ nổi nhẹ.",
        "pbr": "Principled BSDF: Xanh lục sẫm da thuộc (#14532d, Roughness 0.25, Clearcoat 0.25), SSS: 0.32.",
    },
    {
        "id": "SH12", "slug": "shrub_wild_briar_rose", "cat": "understory_shrubs",
        "vn": "Cây Tầm Xuân Hoa Dại", "latin": "Rosa canina", "en": "Wild Dog Rose / Briar",
        "family": "Rosaceae", "biome": "Bờ bụi, Bãi cỏ hoang ven rừng (Z: 4m - 10m)",
        "dims": "2.1m (Cao) x 1.9m (Tán)", "poly_lod0": "42,000 tris", "poly_lod1": "10,200 tris",
        "morphology": "Cành dài uốn cong cong có gai móc sắc, hoa 5 cánh màu hồng nhạt dịu dàng hương thơm thoang thoảng. Mùa thu đơm những quả tầm xuân đỏ tươi hình bầu dục.",
        "micro_geo": "Cánh hoa hình tim khuyết ở đỉnh, quả tầm xuân bóng đỏ mang đài hoa khô dính ở chóp.",
        "pbr": "Principled BSDF: Cánh hoa hồng phấn thanh tao (#fbcfe8, SSS 0.65), Quả đỏ tươi bóng lộn (#dc2626, Clearcoat 0.40).",
    },
    {
        "id": "SH13", "slug": "shrub_dwarf_bamboo", "cat": "understory_shrubs",
        "vn": "Tre Trúc Tầng Dưới Núi Cao", "latin": "Sasa kurilensis", "en": "Dwarf Mountain Bamboo",
        "family": "Poaceae", "biome": "Tầng dưới rừng linh sam tuyết (Z: 9m - 16m)",
        "dims": "1.7m (Cao) x 1.4m (Bụi rậm)", "poly_lod0": "36,000 tris", "poly_lod1": "8,800 tris",
        "morphology": "Thân ngầm bò lan phóng lên các dóng trúc nhỏ dẻo dai màu xanh ngọc, lá tre lớn hình thuôn dài bản rộng xếp xòe hình lòng máng đón tuyết.",
        "micro_geo": "Các gióng trúc có ngấn lóng tròn có lông bao bẹ, phiến lá có gân sọc song song sắc cạnh.",
        "pbr": "Principled BSDF: Thân ngọc bích bóng mượt (#10b981), Lá tre xanh ngọc có sọc sáng mờ SSS 0.45.",
    },
    {
        "id": "SH14", "slug": "shrub_dogwood", "cat": "understory_shrubs",
        "vn": "Bụi Gai Sơn Thù Du Cành Đỏ", "latin": "Cornus sericea", "en": "Red Osier Dogwood",
        "family": "Cornaceae", "biome": "Bờ suối ẩm ướt, Vùng ngập định kỳ (Z: 3m - 7m)",
        "dims": "2.2m (Cao) x 2.4m (Tán cành đỏ)", "poly_lod0": "39,000 tris", "poly_lod1": "9,600 tris",
        "morphology": "Cây bụi nổi bật vào mùa đông với toàn bộ hệ cành non chuyển màu đỏ san hô rực rỡ soi bóng xuống mặt nước băng giá, hoa trắng ngà trổ chùm tròn.",
        "micro_geo": "Vỏ cành non đỏ thắm nhẵn bóng có đốm lỗ bì trắng nhỏ, gân lá cong uốn theo mép lá đặc trưng họ Thù du.",
        "pbr": "Principled BSDF: Cành đỏ san hô chói lọi (#ef4444, Roughness 0.28, Clearcoat 0.30), Lá xanh viền gân cong SSS 0.40.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 4: Cây Thân Gỗ Rừng & Tầng Trung (14 loài)
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
    {
        "id": "TR08", "slug": "tree_sweet_chestnut", "cat": "canopy_trees",
        "vn": "Cây Hạt Dẻ Gai Rừng", "latin": "Castanea sativa", "en": "Sweet Chestnut",
        "family": "Fagaceae", "biome": "Sườn đồi đất chua ẩm mát (Z: 5m - 12m)",
        "dims": "15.0m (Cao) x 12.0m (Tán)", "poly_lod0": "64,000 tris", "poly_lod1": "16,000 tris",
        "morphology": "Thân vỏ nứt xoắn ốc tuyệt đẹp theo chiều kim đồng hồ. Tán lá rộng gồm các lá hình mũi mác dài có răng cưa nhọn như móc câu, mang các quả cầu gai nhọn tròn xoe chứa hạt dẻ nâu bóng.",
        "micro_geo": "Vết nứt xoắn ốc trên thân vỏ vặn theo thân, quả cầu gai (burr) phủ kín gai nhọn sắc chĩa ra tứ phía.",
        "pbr": "Principled BSDF: Thân vỏ xoắn ốc nâu xám (#44403c, Normal xoắn), Quả cầu gai xanh vàng (#a3e635), Hạt dẻ bóng lộn ánh nâu cánh gián (#78350f).",
    },
    {
        "id": "TR09", "slug": "tree_chinese_hackberry", "cat": "canopy_trees",
        "vn": "Cây Cơm Nguội Cổ Thụ", "latin": "Celtis sinensis", "en": "Chinese Hackberry",
        "family": "Cannabaceae", "biome": "Đầu làng, Ngã ba đường mòn (Z: 4m - 9m)",
        "dims": "13.0m (Cao) x 14.0m (Tán vòm)", "poly_lod0": "56,000 tris", "poly_lod1": "14,000 tris",
        "morphology": "Thân bọc lớp vỏ xám nhẵn có các nốt sần nhỏ, cành nhánh xòe vòm bóng râm rợp lối. Mùa quả kết từng chùm quả mọng tròn màu cam đỏ ngọt lành thu hút chim chóc.",
        "micro_geo": "Gốc cây có rễ nổi nhẹ bám đất, lá bất đối xứng ở gốc phiến lá đặc trưng.",
        "pbr": "Principled BSDF: Vỏ thân xám chì (#475569, Roughness 0.55), Tán lá xanh tươi (#22c55e, SSS 0.42), Quả cam đỏ chín mọng (#ea580c).",
    },
    {
        "id": "TR10", "slug": "tree_jacaranda", "cat": "canopy_trees",
        "vn": "Cây Cẩm Quỳ Tím Rực Rỡ", "latin": "Jacaranda mimosifolia", "en": "Blue Jacaranda",
        "family": "Bignoniaceae", "biome": "Thung lũng mùa hạ, Ven đồi thấp (Z: 4m - 10m)",
        "dims": "11.0m (Cao) x 10.5m (Tán tím)", "poly_lod0": "66,000 tris", "poly_lod1": "16,500 tris",
        "morphology": "Tán cây xòe rộng rực rỡ như đám mây tím biếc mộng mơ, hoa hình chuông kèn dài màu tím hoa cà trổ thành từng chùm lớn rủ kín cây, lá kép lông chim 2 lần mịn như lá dương xỉ.",
        "micro_geo": "Cánh hoa hình ống chuông cong uốn lượn có lông tơ mịn ở đáy ống, quả dẹt hình đĩa tròn khô hóa gỗ.",
        "pbr": "Principled BSDF: Cánh hoa tím biếc huyền ảo (#818cf8 / #a855f7), SSS 0.62 thấu quang rực rỡ, Lá xanh mịn thanh tao.",
    },
    {
        "id": "TR11", "slug": "tree_ginkgo", "cat": "canopy_trees",
        "vn": "Ngân Hạnh Rẻ Quạt Vàng", "latin": "Ginkgo biloba", "en": "Ginkgo Maidenhair Tree",
        "family": "Ginkgoaceae", "biome": "Đền đài cổ, Đồi đón gió thu (Z: 5m - 12m)",
        "dims": "16.0m (Cao) x 9.0m (Tán tháp vàng)", "poly_lod0": "60,000 tris", "poly_lod1": "15,000 tris",
        "morphology": "Hóa thạch sống của thế giới thực vật. Thân thẳng đứng, cành mang các chùm lá hình rẻ quạt xẻ đôi độc nhất vô nhị. Mùa thu toàn bộ tán cây đồng loạt biến thành tháp vàng rực lộng lẫy.",
        "micro_geo": "Gân lá hình nan quạt phân nhánh đôi tỏa đều từ cuống không có gân giữa, mép lá lượn sóng mềm mại.",
        "pbr": "Principled BSDF: Vàng rực rỡ mùa thu (#facc15 / #eab308), SSS cực mạnh 0.65 phản chiếu ánh nắng thu rạng rỡ, Vỏ xám rãnh sâu (#57534e).",
    },
    {
        "id": "TR12", "slug": "tree_magnolia", "cat": "canopy_trees",
        "vn": "Mộc Lan Hoa Trắng Đại Đóa", "latin": "Magnolia grandiflora", "en": "Southern Magnolia",
        "family": "Magnoliaceae", "biome": "Ven hồ nước ấm, Đất phù sa màu mỡ (Z: 3m - 8m)",
        "dims": "14.0m (Cao) x 11.0m (Tán tháp tròn)", "poly_lod0": "62,000 tris", "poly_lod1": "15,500 tris",
        "morphology": "Tán lá hình kim tự tháp tròn rậm rạp lá xanh quanh năm. Lá to như bàn tay dày cộm bóng loáng, mặt dưới tráng lớp nhung nâu đỏ như gỉ sắt. Đỉnh cành nở những đóa hoa trắng muốt khổng lồ đường kính tới 30cm tỏa hương chanh ngát.",
        "micro_geo": "Cánh hoa dày như sáp sứ uốn khum lòng thuyền, nhụy hoa hình nón thông cổ xưa chứa nhiều noãn xếp xoắn ốc.",
        "pbr": "Principled BSDF: Cánh hoa trắng sứ (#ffffff, SSS 0.58, Roughness 0.20), Mặt dưới lá nhung nâu đỏ (#78350f, Roughness 0.90), Mặt trên xanh bóng lộn.",
    },
    {
        "id": "TR13", "slug": "tree_golden_larch", "cat": "canopy_trees",
        "vn": "Thông Rụng Lá Larch Vàng", "latin": "Larix decidua", "en": "European Golden Larch",
        "family": "Pinaceae", "biome": "Vành đai núi tuyết cao (Z: 10m - 17m)",
        "dims": "15.5m (Cao) x 7.5m (Tán thon)", "poly_lod0": "55,000 tris", "poly_lod1": "13,800 tris",
        "morphology": "Loài thông lá kim đặc biệt rụng lá theo mùa. Mùa thu lá kim chuyển sang màu vàng cam hổ phách rực rỡ như ngọn đuốc trên nền tuyết trắng, trước khi trút lá trơ cành đón mùa đông giá buốt.",
        "micro_geo": "Lá kim mềm mại mọc thành bó 30-40 lá trên các cành ngắn cựa gà, quả nón nhỏ hình trứng xinh xắn gắn chặt trên cành.",
        "pbr": "Principled BSDF: Lá kim vàng cam hổ phách (#f59e0b / #d97706), SSS: 0.45, Vỏ cây nâu sẫm nứt vảy sừng (#292524).",
    },
    {
        "id": "TR14", "slug": "tree_oriental_arborvitae", "cat": "canopy_trees",
        "vn": "Trắc Bách Diệp Phương Đông", "latin": "Platycladus orientalis", "en": "Oriental Arborvitae",
        "family": "Cupressaceae", "biome": "Vách đá khô cằn, Cổng làng cổ (Z: 5m - 13m)",
        "dims": "8.5m (Cao) x 4.2m (Tán xòe rẻ quạt)", "poly_lod0": "44,000 tris", "poly_lod1": "11,000 tris",
        "morphology": "Thân phân nhánh từ gốc, các cành xếp thành từng phiến phẳng dẹt hình rẻ quạt đứng thẳng song song nhau như những trang sách mở, quả nón có sừng cong ngược kỳ quái.",
        "micro_geo": "Các phiến cành dẹt xếp lớp hướng thẳng đứng, quả nón có 6-8 vảy dày với mấu sừng nhọn uốn cong ở lưng vảy.",
        "pbr": "Principled BSDF: Xanh ngọc lục sẫm (#047857), Roughness: 0.45, Quả nón màu xanh lam xám phủ phấn trắng (#0284c7).",
    },

    # -------------------------------------------------------------------------
    # Nhóm 5: Đại Thụ Cổ Thụ Khổng Lồ (12 loài)
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
        "dims": "12.8m (Cao) x 13.5m (Tán tròn đặc)", "poly_lod0": "66,000 tris", "poly_lod1": "16,500 tris",
        "morphology": "Thân cây đanh cứng như thép, thớ gỗ xoắn ốc chằng chịt, vỏ tróc từng mảng tròn để lộ lớp giác gỗ màu xanh rêu ô-liu đặc trưng. Tán lá tròn xoe dày đặc như chiếc ô sắt xanh biếc.",
        "micro_geo": "Gỗ đặc nặng chìm trong nước, thớ xoắn thể hiện bằng displacement vân xoáy sâu, hoa xanh tím sao 5 cánh điểm xuyết rực rỡ.",
        "pbr": "Principled BSDF: Thân xanh ô-liu ánh vàng đồng (#65a30d / #3f6212, Roughness 0.60, Specular 0.50), Hoa tím xanh lam (#3b82f6, SSS 0.55).",
    },
    {
        "id": "MG08", "slug": "canopy_ancient_ginkgo", "cat": "canopy_trees",
        "vn": "Bạch Quả Cổ Đại Ngàn Năm", "latin": "Ginkgo biloba gigantea", "en": "Ancient Sacred Ginkgo",
        "family": "Ginkgoaceae", "biome": "Đỉnh đồi thánh địa, Lăng tẩm cổ xưa (Z: 6m - 14m)",
        "dims": "22.0m (Cao) x 16.0m (Tán vàng rực)", "poly_lod0": "84,000 tris", "poly_lod1": "21,000 tris",
        "morphology": "Cổ thụ ngàn tuổi thân to 4 người ôm, từ thân buông thõng những bầu nhũ gỗ (chichi) dài hàng mét rủ xuống như thạch nhũ trong hang động. Tán lá rẻ quạt vàng óng trải thảm vàng rực quanh chu vi 30m.",
        "micro_geo": "Các khối nhũ gỗ chichi chảy dài tự nhiên có vân xoắn ốc, quả bạch quả tròn vàng trĩu cành phủ lớp màng mờ.",
        "pbr": "Principled BSDF: Vàng kim rực rỡ hoàng hôn (#eab308, SSS 0.70), Thân vỏ xám cổ nứt rãnh sâu bám rêu phong (#44403c).",
    },
    {
        "id": "MG09", "slug": "canopy_sacred_bodhi", "cat": "canopy_trees",
        "vn": "Bồ Đề Cổ Thụ Giác Ngộ", "latin": "Ficus religiosa", "en": "Sacred Bodhi Tree",
        "family": "Moraceae", "biome": "Bên bờ sông thiêng, Quảng trường trung tâm (Z: 4m - 8m)",
        "dims": "18.0m (Cao) x 20.0m (Tán vòm thanh tịnh)", "poly_lod0": "88,000 tris", "poly_lod1": "22,500 tris",
        "morphology": "Thân uốn lượn cổ kính với lớp vỏ xám sáng, cành lớn vươn rộng mang hàng triệu chiếc lá hình tim có chóp đuôi nhọn dài độc đáo đung đưa rung rinh dù không có gió thoảng.",
        "micro_geo": "Đuôi lá kéo dài thành sợi tơ thanh mảnh (drip tip) dẫn nước mưa rơi thành giọt, gân lá màu trắng ngà nổi bật trên phiến lá xanh biếc.",
        "pbr": "Principled BSDF: Lá xanh ngọc bích sáng bóng (#10b981, Roughness 0.20, SSS 0.48), Gân trắng ngà tinh tế (#f8fafc), Vỏ thân xám bạc nhẵn mịn.",
    },
    {
        "id": "MG10", "slug": "canopy_sugar_pine", "cat": "canopy_trees",
        "vn": "Thông Trắng Khổng Lồ California", "latin": "Pinus lambertiana", "en": "Giant Sugar Pine",
        "family": "Pinaceae", "biome": "Hẻm vực núi tuyết sâu (Z: 11m - 19m)",
        "dims": "26.0m (Cao) x 10.0m (Tán)", "poly_lod0": "76,000 tris", "poly_lod1": "19,000 tris",
        "morphology": "Loài thông cao nhất thế giới lá kim, cành nhánh vươn dài nằm ngang hơi uốn cong ở đầu cành, trĩu nặng những quả thông khổng lồ dài tới 50cm treo lủng lẳng ở đầu cành như đèn lồng.",
        "micro_geo": "Quả thông nón dài 50cm cấu thành từ hàng trăm vảy nón sừng dày có hạt có cánh, vỏ thân nứt thành các tấm khiên lớn màu tím nâu.",
        "pbr": "Principled BSDF: Vỏ thân nâu tím quế (#581c87 / #7c2d12, Roughness 0.90), Quả thông nâu mật ong bóng nhựa (#b45309), Lá kim xanh lam nhạt.",
    },
    {
        "id": "MG11", "slug": "canopy_bald_cypress", "cat": "canopy_trees",
        "vn": "Cây Bách Nước Đầm Lầy", "latin": "Taxodium distichum", "en": "Bald Cypress",
        "family": "Cupressaceae", "biome": "Ngập nước đáy hồ, Vùng bãi sình lầy (Z: 3.5m - 6m)",
        "dims": "17.0m (Cao) x 13.0m (Tán nón rộng)", "poly_lod0": "82,000 tris", "poly_lod1": "20,500 tris",
        "morphology": "Gốc cây phình to hình chuông ngâm trong nước, quanh gốc mọc trồi lên hàng chục chiếc rễ thở đầu gối (cypress knees) nhô khỏi mặt nước như đàn măng đá nhấp nhô giúp cây thở trong bùn ngập.",
        "micro_geo": "Rễ thở đầu gối bằng gỗ xốp hóa sừng nhô cao 1-2m trên mặt nước, lá kim dẹp mềm mại xếp 2 hàng như lông vũ.",
        "pbr": "Principled BSDF: Gốc ngâm nước phủ rêu đen và bèo tấm (#1c1917 / #15803d, Roughness 0.70), Tán lá lông vũ xanh tươi mướt mắt SSS 0.44.",
    },
    {
        "id": "MG12", "slug": "canopy_rainforest_dipterocarp", "cat": "canopy_trees",
        "vn": "Cây Thau Thao Cổ Rừng Mưa", "latin": "Dipterocarpus grandiflorus", "en": "Emergent Rainforest Giant",
        "family": "Dipterocarpaceae", "biome": "Rừng mưa nhiệt đới tầng vượt tán (Z: 2m - 10m)",
        "dims": "25.0m (Cao) x 15.0m (Tán súp lơ vĩ đại)", "poly_lod0": "90,000 tris", "poly_lod1": "23,000 tris",
        "morphology": "Đại thụ tầng vượt tán (emergent layer) vươn cao vượt lên trên thảm rừng chung, thân tròn thẳng tắp như cây cột đình khổng lồ, đỉnh nở tán hình bán cầu như cây súp lơ khổng lồ, quả có 2 cánh dài bay xoay tít như chong chóng khi rụng.",
        "micro_geo": "Rễ bạnh tam giác khổng lồ cao 4m mở rộng chân đế, quả 2 cánh mỏng có gân song song xoắn ốc.",
        "pbr": "Principled BSDF: Thân xám trắng loang lổ địa y, Tán lá xanh đậm dày cộm chịu nắng gắt tầng trên cùng Roughness 0.30, SSS 0.36.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 6: Thực Vật Thủy Sinh & Đầm Lầy (12 loài)
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
    {
        "id": "AQ08", "slug": "aquatic_water_hyacinth", "cat": "aquatic_wetland",
        "vn": "Bèo Nhật Bản Hoa Tím", "latin": "Eichhornia crassipes", "en": "Water Hyacinth",
        "family": "Pontederiaceae", "biome": "Mặt đầm nước ấm, Lạch sông lặng (Z: 4.8m)",
        "dims": "0.45m (Cao) x 0.65m (Cụm nổi)", "poly_lod0": "28,000 tris", "poly_lod1": "6,800 tris",
        "morphology": "Cây nổi tự do trên mặt nước nhờ cuống lá phình to thành bọng xốp hình bóng bay chứa đầy khí. Chùm hoa màu tím lam nhạt rực rỡ, cánh trên có đốm vàng viền lam như mắt chim công.",
        "micro_geo": "Cuống lá phình tròn có cấu trúc bọt xốp nano siêu nhẹ, chùm rễ đen dài buông rủ lọc nước.",
        "pbr": "Principled BSDF: Hoa tím lam viền lam đậm (#a855f7 / #2563eb), đốm vàng (#facc15, SSS 0.65), Cuống bọng xanh ngọc bóng lộn.",
    },
    {
        "id": "AQ09", "slug": "aquatic_red_azolla", "cat": "aquatic_wetland",
        "vn": "Bèo Hoa Dâu Đỏ Thẫm", "latin": "Azolla caroliniana", "en": "Red Azolla Water Velvet",
        "family": "Salviniaceae", "biome": "Mặt nước tĩnh, Đầm lầy bóng râm (Z: 4.5m)",
        "dims": "0.02m (Cao) x 1.8m (Thảm nổi)", "poly_lod0": "35,000 tris", "poly_lod1": "8,800 tris",
        "morphology": "Dương xỉ thủy sinh tí hon kết thành tấm thảm đỏ tía bồng bềnh phủ kín mặt nước như tấm nhung gấm hoàng gia, rễ chùm li ti buông lửng trong nước.",
        "micro_geo": "Từng cây bèo nhỏ như móng tay gồm các vảy lá xếp lợp ngói tam giác có lông nhung kỵ nước tuyệt đối.",
        "pbr": "Principled BSDF: Đỏ tía chuyển xanh lục sẫm (#991b1b / #15803d), Velvet Sheen 0.85, Roughness 0.50.",
    },
    {
        "id": "AQ10", "slug": "aquatic_victoria_lily", "cat": "aquatic_wetland",
        "vn": "Hoa Súng Khổng Lồ Victoria", "latin": "Victoria amazonica", "en": "Giant Amazon Water Lily",
        "family": "Nymphaeaceae", "biome": "Vịnh hồ nước sâu phẳng lặng (Z: 4.52m)",
        "dims": "0.35m (Cao) x 2.4m (Đĩa khổng lồ)", "poly_lod0": "48,000 tris", "poly_lod1": "12,000 tris",
        "morphology": "Lá nổi khổng lồ đường kính tới 2.2m hình chiếc mâm tròn có thành viền dựng đứng vuông góc 8cm như chiếc bánh ngọt, chịu được sức nặng 40kg. Hoa trắng muốt chuyển hồng vào đêm thứ hai.",
        "micro_geo": "Mặt dưới lá có hệ gân sườn nổi cuồn cuộn như khung tàu ngầm đan chéo và phủ đầy gai nhọn chống cá ăn lá, thành lá có 2 rãnh thoát nước mưa.",
        "pbr": "Principled BSDF: Mặt trên xanh lục ngọc (#15803d, Roughness 0.18, Clearcoat 0.40), Mặt dưới đỏ tím gai góc (#831843, Gai vàng đồng nhọn).",
    },
    {
        "id": "AQ11", "slug": "aquatic_elodea", "cat": "aquatic_wetland",
        "vn": "Rong Đuôi Chó Xanh Mướt", "latin": "Elodea canadensis", "en": "Canadian Waterweed",
        "family": "Hydrocharitaceae", "biome": "Đáy nước suối chảy xiết trong vắt (Z: 2m - 4.5m)",
        "dims": "0.75m (Cao) x 0.18m (Tán)", "poly_lod0": "24,000 tris", "poly_lod1": "5,800 tris",
        "morphology": "Thân chìm phân nhánh mảnh mai mang các vòng 3 lá nhỏ hình bầu dục màu xanh lục sẫm trong suốt, tạo thành những dải rừng rậm dưới đáy hồ cung cấp oxy cho cá.",
        "micro_geo": "Lá chỉ dày đúng 2 lớp tế bào nên có độ thấu quang trong suốt gần như tuyệt đối dưới ánh sáng mặt trời chiếu xuyên qua nước.",
        "pbr": "Principled BSDF: Xanh ngọc lục trong suốt, Transmission: 0.42, SSS: 0.60 (#059669), IOR: 1.333 ngập nước.",
    },
    {
        "id": "AQ12", "slug": "aquatic_mangrove", "cat": "aquatic_wetland",
        "vn": "Cây Thủy Cúc Rừng Ngập Mặn", "latin": "Rhizophora mangle", "en": "Red Mangrove",
        "family": "Rhizophoraceae", "biome": "Cửa biển nước lợ, Bãi triều (Z: 0m - 2m)",
        "dims": "4.5m (Cao) x 4.8m (Tán rễ kiềng)", "poly_lod0": "58,000 tris", "poly_lod1": "14,500 tris",
        "morphology": "Hệ thống rễ chống hình vòng cung (stilt roots) cắm chằng chịt xuống bùn lầy như chân nhện khổng lồ nâng bổng thân cây lên khỏi mực nước triều dâng, lá dày bóng chống muối mặn.",
        "micro_geo": "Rễ chống hình cung vòm có lỗ thở bì khổng lồ hút oxy, quả nảy mầm ngay trên cây thành cây con hình ngọn lao trước khi rơi xuống bùn.",
        "pbr": "Principled BSDF: Rễ và thân nâu đỏ ngâm nước (#7c2d12, Roughness 0.70), Lá xanh bóng phủ sáp dày chống muối Roughness 0.20, Clearcoat 0.35.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 7: Thực Vật Khô Hạn & Mọng Nước (12 loài)
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
    {
        "id": "SC08", "slug": "succulent_living_stones", "cat": "arid_succulents",
        "vn": "Thạch Lan Sỏi Sống Sa Mạc", "latin": "Lithops dorotheae", "en": "Living Stones",
        "family": "Aizoaceae", "biome": "Bãi sỏi cuội nung lửa sa mạc (Z: 4m - 8m)",
        "dims": "0.05m (Cao) x 0.08m (Cặp sỏi)", "poly_lod0": "18,000 tris", "poly_lod1": "4,200 tris",
        "morphology": "Cây ngụy trang hoàn hảo thành hai viên sỏi cuội tròn nứt đôi ở giữa. Mặt trên phẳng có hoa văn vân đá cửa sổ quang học đón ánh sáng ngầm, giữa khe nứt trổ đóa cúc vàng rực rỡ.",
        "micro_geo": "Cửa sổ quang học trên mặt sỏi có các đốm mô trong mờ dẫn ánh sáng xuống sâu dưới lòng đất mát mẻ.",
        "pbr": "Principled BSDF: Màu sỏi vân nâu đất loang xám (#78716c / #a8a29e), Cửa sổ trong mờ Transmission: 0.25, Hoa vàng óng SSS 0.60.",
    },
    {
        "id": "SC09", "slug": "succulent_golden_barrel", "cat": "arid_succulents",
        "vn": "Xương Rồng Thùng Tròn Vàng", "latin": "Echinocactus grusonii", "en": "Golden Barrel Cactus",
        "family": "Cactaceae", "biome": "Sườn đồi cát sỏi khô hạn (Z: 6m - 12m)",
        "dims": "0.95m (Cao) x 0.95m (Quả cầu gai)", "poly_lod0": "38,000 tris", "poly_lod1": "9,200 tris",
        "morphology": "Thân hình cầu tròn xoe hoàn hảo màu xanh tươi có 25-35 nếp khía dọc sâu, phủ đầy gai cong màu vàng óng ánh như sợi chỉ vàng dệt nên chiếc vương miện hoàng gia.",
        "micro_geo": "Đỉnh quả cầu có chỏm lông len trắng dày bảo vệ mầm non, gai vàng cong nhẹ sắc như kim thép.",
        "pbr": "Principled BSDF: Thân xanh lục mọng nước (#16a34a, SSS 0.35), Gai vàng hoàng kim rực rỡ (#eab308, Roughness 0.18, Specular 0.60).",
    },
    {
        "id": "SC10", "slug": "succulent_joshua_tree", "cat": "arid_succulents",
        "vn": "Cây Joshua Sa Mạc Gai", "latin": "Yucca brevifolia", "en": "Joshua Tree",
        "family": "Asparagaceae", "biome": "Bình nguyên đá sa mạc lộng gió (Z: 7m - 14m)",
        "dims": "6.5m (Cao) x 4.8m (Tán cành gai)", "poly_lod0": "52,000 tris", "poly_lod1": "13,000 tris",
        "morphology": "Thân gỗ xù xì phân cành ngoằn ngoèo kỳ dị như cánh tay người khổng lồ chắp tay cầu nguyện, đầu các cành mang chùm túm lá hình kiếm gai nhọn hoắt dày đặc.",
        "micro_geo": "Thân bọc lớp lá già khô xơ bao bọc như áo giáp rơm, lá gai có răng cưa sắc bén ở mép.",
        "pbr": "Principled BSDF: Vỏ thân nâu xơ xốp (#57534e, Roughness 0.95), Túm lá xanh xám gai góc (#15803d, Roughness 0.40).",
    },
    {
        "id": "SC11", "slug": "succulent_bottle_tree", "cat": "arid_succulents",
        "vn": "Cây Bao Báp Bình Rượu", "latin": "Pachypodium geayi", "en": "Madagascar Bottle Tree",
        "family": "Apocynaceae", "biome": "Đá vôi khô cằn Madagascar (Z: 5m - 10m)",
        "dims": "5.5m (Cao) x 2.2m (Thân bình)", "poly_lod0": "44,000 tris", "poly_lod1": "10,800 tris",
        "morphology": "Thân phình to hình cổ chai thon dần lên đỉnh, toàn bộ thân vỏ xám bạc phủ kín bởi lớp gai thép sắc nhọn, ngọn mang chùm lá dài hẹp như chiếc vương miện cọ.",
        "micro_geo": "Gai thân mọc chùm 3 chiếc nhọn hoắt bảo vệ bình trữ nước bên trong thân khỏi thú ăn cỏ.",
        "pbr": "Principled BSDF: Thân xám bạc ánh kim loại (#94a3b8, Roughness 0.42), Gai nhọn đen sẫm, Lá xanh mạ đỉnh ngọn SSS 0.35.",
    },
    {
        "id": "SC12", "slug": "succulent_ghost_echeveria", "cat": "arid_succulents",
        "vn": "Sen Đá Hồng Ngọc Sa Mạc", "latin": "Echeveria elegans", "en": "Mexican Snow Ball",
        "family": "Crassulaceae", "biome": "Kẽ đá vôi nứt, Khe dốc khô (Z: 5m - 11m)",
        "dims": "0.15m (Cao) x 0.22m (Đóa hoa hồng)", "poly_lod0": "22,000 tris", "poly_lod1": "5,400 tris",
        "morphology": "Đóa hoa hồng ngọc bích xếp cánh sít sao hoàn hảo, các lá mọng nước dày khum lòng thuyền viền trong mờ như ngọc thạch phủ lớp phấn trắng mờ ảo kiêu sa.",
        "micro_geo": "Lớp phấn sáp farina nano phủ đều bề mặt làm dịu vệt sáng chói, chóp lá có chấm gai đỏ tí hon.",
        "pbr": "Principled BSDF: Xanh ngọc bích phủ phấn trắng kem viền hồng phớt (#5eead4 / #f472b6), SSS: 0.65 thấu quang thạch ngọc bích, Roughness 0.20.",
    },

    # -------------------------------------------------------------------------
    # Nhóm 8: Ăn Thịt, Ký Sinh & Hang Động Phát Quang (12 loài)
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
    {
        "id": "EX08", "slug": "carnivorous_cobra_lily", "cat": "carnivorous_vines",
        "vn": "Cây Bắt Mồi Rắn Hổ Mang", "latin": "Darlingtonia californica", "en": "Cobra Lily",
        "family": "Sarraceniaceae", "biome": "Đầm than bùn suối lạnh râm mát (Z: 4m - 9m)",
        "dims": "0.85m (Cao) x 0.65m (Cụm bẫy)", "poly_lod0": "45,000 tris", "poly_lod1": "11,000 tris",
        "morphology": "Ống bẫy hình rắn hổ mang ngóc đầu phồng mang màu xanh vàng điểm đốm tím, đỉnh đầu có chiếc lưỡi chẻ đôi buông rủ như lưỡi rắn thè ra dẫn dụ côn trùng bò vào họng bẫy.",
        "micro_geo": "Vòm đầu bẫy có các đốm cửa sổ trong suốt không diệp lục đánh lừa con mồi bay đâm đầu vào vách kính rồi rơi xuống đáy đầy lông ngược cản đường.",
        "pbr": "Principled BSDF: Vàng lục pha tím đỏ (#ca8a04 / #701a75), Đốm cửa sổ trong mờ Transmission: 0.50, SSS: 0.55, Lưỡi rắn đỏ tươi (#dc2626).",
    },
    {
        "id": "EX09", "slug": "carnivorous_wild_orchid", "cat": "carnivorous_vines",
        "vn": "Lan Rừng Biểu Sinh Vũ Nữ", "latin": "Oncidium flexuosum", "en": "Dancing Lady Epiphytic Orchid",
        "family": "Orchidaceae", "biome": "Ký sinh chạc ba cổ thụ, Rừng ẩm (Z: 3m - 12m)",
        "dims": "0.65m (Cao) x 0.85m (Chùm hoa)", "poly_lod0": "38,000 tris", "poly_lod1": "9,200 tris",
        "morphology": "Giả hành hình dẹt tích nước bám rễ gió trắng mập vào vỏ đại thụ, cành hoa mảnh uốn lượn phân nhánh mang hàng chục đóa hoa vàng tươi có cánh môi xòe rộng như chiếc váy vũ nữ đang xoay tròn múa.",
        "micro_geo": "Rễ gió có lớp màng xốp velamen hút hơi ẩm khí quyển, cánh môi hoa có các đốm đỏ đồng cộm nổi.",
        "pbr": "Principled BSDF: Cánh môi vàng tươi chói lọi (#facc15, SSS 0.60), Đốm đỏ đồng (#991b1b), Rễ gió trắng xốp (#f1f5f9, Roughness 0.75).",
    },
    {
        "id": "EX10", "slug": "cave_jack_o_lantern", "cat": "cave_bioluminescent",
        "vn": "Nấm Quỷ Lập Lòe Ma Quái", "latin": "Omphalotus olearius", "en": "Jack-o'-Lantern Mushroom",
        "family": "Omphalotaceae", "biome": "Gốc cây mục tối tăm, Cửa hang ẩm (Z: -2m đến 3m)",
        "dims": "0.55m (Cao) x 0.65m (Cụm phễu)", "poly_lod0": "34,000 tris", "poly_lod1": "8,200 tris",
        "morphology": "Mọc cụm chùm lớn màu cam cháy rực rỡ vào ban ngày. Đêm xuống, toàn bộ các phiến nấm dưới mũ phát ra luồng ánh sáng huỳnh quang xanh lục ma mị rọi sáng chân vách đá.",
        "micro_geo": "Mũ nấm hình phễu lõm ở tâm mép uốn lượn sóng, phiến nấm chạy dài xuống tận chân cuống chứa enzym luciferase.",
        "pbr": "Principled BSDF + Emission: Ban ngày màu cam cháy (#ea580c), Mặt phiến nấm phát quang ánh sáng lục lam Emission: 4.8 lux (#22c55e), SSS: 0.50.",
    },
    {
        "id": "EX11", "slug": "cave_ghost_pipe", "cat": "cave_bioluminescent",
        "vn": "Cây Ma Cà Rồng Hút Nhựa", "latin": "Monotropa uniflora", "en": "Ghost Pipe / Corpse Plant",
        "family": "Ericaceae", "biome": "Nền rừng râm tối mịt mù, Cửa hang đá (Z: 0m - 5m)",
        "dims": "0.22m (Cao) x 0.18m (Cụm trắng)", "poly_lod0": "18,000 tris", "poly_lod1": "4,200 tris",
        "morphology": "Loài thực vật kỳ dị hoàn toàn không có diệp lục, toàn thân trắng muốt như tượng sáp hoặc thạch cao trong suốt. Cây sống ký sinh hút chất dinh dưỡng từ mạng lưới nấm ngầm rễ sồi, hoa hình ống rủ xuống như chiếc tẩu thuốc ma.",
        "micro_geo": "Toàn thân cấu tạo từ các vảy lá trong mờ úp sát thân, cánh hoa mờ đục như thủy tinh mờ sáp.",
        "pbr": "Principled BSDF: Trắng muốt ngọc thạch trong mờ (#f8fafc), Transmission: 0.40, SSS cực cao 0.85 (tỏa quầng sáng mờ ảo khi có ánh sáng chiếu vào), Roughness: 0.20.",
    },
    {
        "id": "EX12", "slug": "carnivorous_bladderwort", "cat": "carnivorous_vines",
        "vn": "Cây Bắt Côn Trùng Bọng Khí", "latin": "Utricularia vulgaris", "en": "Greater Bladderwort",
        "family": "Lentibulariaceae", "biome": "Nước hồ cạn ngập nắng, Lạch rêu (Z: 4.2m)",
        "dims": "0.4m (Cao hoa) x 0.6m (Tán bọng nước)", "poly_lod0": "30,000 tris", "poly_lod1": "7,200 tris",
        "morphology": "Thân chìm dưới nước mang hàng ngàn bọng hút chân không tí hon trong suốt. Khi bọ gậy chạm lông cảm ứng, nắp bẫy mở ra hút trọn con mồi và nước vào trong tích tắc 1/1000 giây (nhanh nhất giới thực vật), ngọn vươn cành hoa vàng rực lên khỏi mặt nước.",
        "micro_geo": "Bọng khí trong suốt hình quả lê có van nắp đóng mở linh hoạt với lông kích hoạt siêu vi mô.",
        "pbr": "Principled BSDF: Bọng khí trong suốt Transmission: 0.85 (#a7f3d0), Hoa vàng tươi vươn trên mặt nước SSS 0.60 (#eab308).",
    },
]

def generate_catalog_md(species_list):
    groups = {
        "Họ Cỏ, Rêu & Thảm Mặt Đất (Grasses, Mosses & Groundcovers)": [s for s in species_list if s["id"].startswith("GR")],
        "Thảo Mộc & Hoa Rừng Hoang Dã (Wildflowers & Forest Herbs)": [s for s in species_list if s["id"].startswith("FL")],
        "Cây Bụi & Dương Xỉ Tầng Dưới (Understory Shrubs & Ferns)": [s for s in species_list if s["id"].startswith("SH")],
        "Cây Thân Gỗ Rừng & Tầng Trung (Midstory & Canopy Trees)": [s for s in species_list if s["id"].startswith("TR")],
        "Đại Thụ Cổ Thụ Khổng Lồ (Ancient Megatrees & Apex Giants)": [s for s in species_list if s["id"].startswith("MG")],
        "Thực Vật Thủy Sinh & Đầm Lầy (Aquatic & Wetland Flora)": [s for s in species_list if s["id"].startswith("AQ")],
        "Thực Vật Khô Hạn & Mọng Nước (Arid & Succulents)": [s for s in species_list if s["id"].startswith("SC")],
        "Thực Vật Ăn Thịt, Ký Sinh & Hang Động Phát Quang (Carnivorous, Vines & Cave)": [s for s in species_list if s["id"].startswith("EX")],
    }

    doc = """# Danh Mục Thực Vật Toàn Diện (Master Botanical Catalog) — Genesis Zero

> [!IMPORTANT]
> **Quy Chuẩn Thẩm Mỹ**: **Hyper-Realistic Scan-Quality**
> Toàn bộ 100 loài thực vật được phân loại khoa học theo chuẩn thực vật học quốc tế (APG IV), tích hợp đầy đủ thông số giải phẫu hình thái, độ cong Fibonacci, vi mô mô tế bào, lưới Quads Manifold 100% Smooth Shading và hệ thống vật liệu sinh học PBR (Subsurface Scattering, Procedural Bark Displacement, Transmission & Bioluminescence).

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

## 2. Tiêu Chuẩn 3D Hyper-Realistic Scan-Quality

1. **Topology Quad Manifold**: 100% sạch nếp ngắt, không có mặt lật ngược normal, không có ngons (đa giác > 4 đỉnh), góc cạnh uốn cong hữu cơ tự nhiên.
2. **Smooth Shading Bắt Buộc**: Áp dụng `use_smooth = True` trên 100% các mặt polygon để loại bỏ triệt để hiện tượng vát phẳng thô cứng.
3. **Subsurface Scattering (SSS) Chuyên Sâu**:
   - Tán lá, cánh hoa và thân mọng nước được cấu hình thông số tán xạ ngầm (Subsurface Radius & Weight) chính xác theo độ dày tế bào thực tế.
   - Khi có ánh sáng mặt trời chiếu xiên hoặc ngược sáng (backlighting), phiến lá bừng sáng thấu quang chân thực như ảnh chụp vĩ mô tự nhiên.
4. **Vỏ Cây & Thân Gỗ Procedural Micro-Displacement**:
   - Tích hợp mạng Procedural Texture (Voronoi + Noise kết hợp) để sinh rãnh nứt nẻ gồ ghề sâu 5mm - 40mm mà không làm nặng số đỉnh hiển thị.
   - Thêm lớp địa y và rêu phong ẩm ướt ở chân gốc cổ thụ tạo chiều sâu hàng trăm năm tuổi.

---

## 3. Bảng Chi Tiết 100 Loài Thực Vật Theo Từng Nhóm Sinh Thái
"""

    for group_name, s_list in groups.items():
        doc += f"\n### {group_name} ({len(s_list)} loài)\n\n"
        doc += "| ID | Tên Loài (Tiếng Việt) | Danh Pháp (Latin) | Tên Tiếng Anh | Chiều Cao x Tán | Tầng Sinh Cảnh | Đặc Điểm Hình Thái Nổi Bật | File Đặc Tả & 3D Links |\n"
        doc += "|:---|:---|:---|:---|:---:|:---:|:---|:---:|\n"
        for sp in s_list:
            doc += f"| **{sp['id']}** | {sp['vn']} | *{sp['latin']}* | {sp['en']} | {sp['dims']} | {sp['biome']} | {sp['morphology'][:65]}... | [Chi tiết](species/{sp['slug']}.md) |\n"

    doc += """
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
"""
    return doc

def generate_spec_md(sp):
    return f"""# Đặc Tả Thực Vật 3D: {sp['vn']} ({sp['latin']})

> [!NOTE]
> **Mã Định Danh**: `{sp['id']}`
> **Nhóm Hình Thái**: {sp['cat'].replace('_', ' ').title()}
> **Họ Thực Vật (Family)**: *{sp['family']}*
> **Danh Pháp Khoa Học**: *{sp['latin']}*
> **Tên Tiếng Anh**: **{sp['en']}**
> **Sinh Cảnh Tự Nhiên**: {sp['biome']}
> **Kích Thước Không Gian**: {sp['dims']}
> **Tiêu Chuẩn Đồ Họa**: **Hyper-Realistic Scan-Quality**

---

## 1. Giải Phẫu Hình Thái Thực Vật Học (Botanical Anatomy)

### 1.1 Cấu Trúc Tổng Quan
{sp['morphology']}

### 1.2 Chi Tiết Vi Mô & Dấu Ấn Scan (Micro-Geometry & Surface Detail)
{sp['micro_geo']}

---

## 2. Thông Số Kiến Trúc Lưới 3D (3D Mesh Topology & LODs)

| Thông Số Lưới | Tiêu Chuẩn Scan-Quality | Mô Tả Kỹ Thuật |
|:---|:---|:---|
| **LOD0 (Ultra High)** | **{sp['poly_lod0']}** | Lưới Quads sạch 100%, Manifold kín nước, hỗ trợ Subdivision Surface |
| **LOD1 (Game Engine)** | **{sp['poly_lod1']}** | Tối ưu hóa render thời gian thực, giữ nguyên vẹn Normal Map vi mô |
| **LOD2 (Diorama/Far)** | ~1,200 - 2,500 tris | Dạng Billboard / Low-poly cho góc nhìn viễn cảnh toàn cảnh diorama |
| **Smooth Shading** | `use_smooth = True` | Kích hoạt 100% trên toàn bộ các mặt đa giác, triệt tiêu gãy khúc |
| **UV Unwrapping** | Non-overlapping Island | Tỷ lệ Texel Density đồng đều (2048 px/m), seam giấu khéo léo |

---

## 3. Hệ Thống Vật Liệu Sinh Học PBR (Biological PBR Shader Network)

Vật liệu được xây dựng trên hệ thống Shader chuyên sâu của Blender 5.2.1 LTS:

- **Shader Profile**: `{sp['pbr']}`
- **Subsurface Scattering (SSS)**: Tái hiện chân thực cơ chế ánh sáng đi sâu vào mô tế bào diệp lục và tán xạ ngược ra ngoài khi ngược sáng.
- **Normal & Procedural Displacement**: Tái tạo các khe nứt vỏ cây già cỗi, gờ sống lá, lông tơ nhung và độ cong vi mô của cánh hoa.
- **Color Management**: Tối ưu hóa chuẩn không gian màu **AgX (Medium High Contrast)** cho hình ảnh chân thực và rực rỡ.

---

## 4. Đường Dẫn Tài Nguyên File 3D (Direct Asset Links)

Bạn có thể mở trực tiếp các file 3D của loài thực vật này tại các liên kết sau:

- 🎨 **File Nguồn Blender 3D**: [`{sp['slug']}.blend`](file://{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.blend)
- 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`{sp['slug']}.glb`](file://{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.glb)
- 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`{sp['slug']}_builder.py`](file://{ROOT}/assets/flora/generators/{sp['slug']}_builder.py)

---

## 5. Script Nạp Nhanh Vào Scene Hiện Tại (Python Snippet)

```python
import os
import bpy

asset_path = "{ROOT}/assets/flora/{sp['cat']}/{sp['slug']}.glb"
if os.path.exists(asset_path):
    bpy.ops.import_scene.gltf(filepath=asset_path)
    plant = bpy.context.selected_objects[0]
    plant.name = "Flora_{sp['slug']}"
    print(f"✓ Đã đặt {{plant.name}} vào thế giới Genesis Zero.")
else:
    print(f"Asset file đang được sinh bởi flora_builder.py...")
```
"""

def main():
    print(">>> Đang khởi tạo Master Catalog 100 loài thực vật...")
    catalog_content = generate_catalog_md(DATA)
    (DOCS_DIR / "README.md").write_text(catalog_content, encoding="utf-8")
    print(f"✓ Đã ghi thành công Master Catalog vào {DOCS_DIR / 'README.md'}")

    print(">>> Đang khởi tạo 100 file đặc tả thực vật chi tiết...")
    count = 0
    for sp in DATA:
        spec_content = generate_spec_md(sp)
        spec_path = SPECIES_DIR / f"{sp['slug']}.md"
        spec_path.write_text(spec_content, encoding="utf-8")
        count += 1
    print(f"✓ Đã tạo thành công {count} file đặc tả thực vật tại: {SPECIES_DIR}")

if __name__ == "__main__":
    main()

import os, sys, re, json
from pathlib import Path
sys.path.insert(0, 'scripts')
from generate_100_flora import DATA

HTML_PATH = Path('web/flora_viewer.html')
html_text = HTML_PATH.read_text(encoding='utf-8')

# The 16 core species
EXISTING_16 = [
    "canopy_ancient_oak", "canopy_alpine_pine", "canopy_weeping_willow", "canopy_giant_sequoia",
    "canopy_baobab", "understory_tree_fern", "understory_sword_fern", "grass_alpine_tussock",
    "aquatic_water_lily", "aquatic_sacred_lotus", "aquatic_broadleaf_cattail", "succulent_saguaro_cactus",
    "succulent_century_agave", "carnivorous_pitcher_plant", "carnivorous_venus_flytrap", "cave_bioluminescent_mushroom"
]

def get_rep_id(cat, slug):
    if cat == 'canopy_trees':
        if any(w in slug for w in ['pine', 'spruce', 'larch', 'fir', 'cedar', 'cypress', 'juniper']):
            return 'canopy_alpine_pine'
        elif 'willow' in slug:
            return 'canopy_weeping_willow'
        elif any(w in slug for w in ['sequoia', 'redwood']):
            return 'canopy_giant_sequoia'
        elif 'baobab' in slug:
            return 'canopy_baobab'
        else:
            return 'canopy_ancient_oak'
    elif cat == 'understory_shrubs':
        if 'tree_fern' in slug:
            return 'understory_tree_fern'
        else:
            return 'understory_sword_fern'
    elif cat == 'grasses_herbs':
        return 'grass_alpine_tussock'
    elif cat == 'aquatic_wetland':
        if 'lotus' in slug:
            return 'aquatic_sacred_lotus'
        elif any(w in slug for w in ['reed', 'cattail', 'grass', 'papyrus', 'horsetail']):
            return 'aquatic_broadleaf_cattail'
        else:
            return 'aquatic_water_lily'
    elif cat == 'arid_succulents':
        if any(w in slug for w in ['agave', 'aloe', 'living_stone', 'succulent', 'sansevieria']):
            return 'succulent_century_agave'
        else:
            return 'succulent_saguaro_cactus'
    elif cat == 'carnivorous_vines':
        if any(w in slug for w in ['pitcher', 'liana', 'vine']):
            return 'carnivorous_pitcher_plant'
        else:
            return 'carnivorous_venus_flytrap'
    elif cat == 'cave_bioluminescent':
        return 'cave_bioluminescent_mushroom'
    else:
        return 'understory_sword_fern'

CAT_META = {
    'canopy_trees': ('Tầng Tán Rừng', '🌳'),
    'understory_shrubs': ('Tầng Dưới Tán', '🌿'),
    'grasses_herbs': ('Thảm Cỏ & Hoa', '🌾'),
    'aquatic_wetland': ('Thủy Sinh & Đầm Lầy', '🪷'),
    'arid_succulents': ('Sa Mạc & Mọng Nước', '🌵'),
    'carnivorous_vines': ('Cây Bắt Mồi', '🪴'),
    'cave_bioluminescent': ('Hang Động Phát Quang', '🍄'),
    'endemic_flora': ('Đặc Hữu Việt Nam', '🌺')
}

# Parse existing 16 objects from HTML to preserve their exact formatting
m = re.search(r'const FLORA_DATABASE = \[\n([\s\S]*?)\n    \];', html_text)
existing_block = m.group(1)

# Build remaining objects
new_objects_js = []
for sp in DATA:
    slug = sp['slug']
    if slug in EXISTING_16:
        continue
    cat = sp['cat']
    cat_vn, icon = CAT_META.get(cat, ('Thực Vật', '🌿'))
    if 'flower' in slug or 'daisy' in slug or 'rose' in slug or 'bluebell' in slug or 'lavender' in slug:
        icon = '🌼'
    elif 'pine' in slug or 'spruce' in slug:
        icon = '🌲'
    elif 'palm' in slug:
        icon = '🌴'
    elif 'bamboo' in slug:
        icon = '🎋'
    elif 'mushroom' in slug or 'fungus' in slug:
        icon = '🍄'

    dims = sp.get('dims', '1.0m (Cao) x 1.0m (Tán)')
    parts = dims.split('x')
    height = parts[0].strip() if len(parts) > 0 else '1.0 m'
    span = parts[1].strip() if len(parts) > 1 else '1.0 m'

    rep_id = get_rep_id(cat, slug)
    desc_clean = sp.get('morphology', '').replace('"', '\\"').replace('\n', ' ')
    family = sp.get('family', '')
    biome_short = sp.get('biome', '').split(',')[0].strip()

    tags = [family, biome_short]
    if 'poly_lod0' in sp:
        tags.append(sp['poly_lod0'])

    obj_str = f"""      {{
        id: "{slug}",
        nameVN: "{sp.get('vn', slug)}",
        nameLatin: "{sp.get('latin', '')}",
        category: "{cat}",
        categoryVN: "{cat_vn}",
        icon: "{icon}",
        height: "{height}",
        span: "{span}",
        lifespan: "Thực vật tự nhiên",
        desc: "{desc_clean}",
        glbUrl: "../assets/flora/{cat}/{slug}.glb",
        blendUrl: "../assets/flora/{cat}/{slug}.blend",
        specUrl: "../docs/flora/species/{slug}.md",
        turnaroundImg: null,
        representativeId: "{rep_id}",
        tags: {json.dumps(tags, ensure_ascii=False)}
      }}"""
    new_objects_js.append(obj_str)

# Also add the 103rd species: endemic_paphiopedilum_vietnamense
endemic_obj = f"""      {{
        id: "endemic_paphiopedilum_vietnamense",
        nameVN: "Lan Hài Việt Nam",
        nameLatin: "Paphiopedilum vietnamense",
        category: "understory_shrubs",
        categoryVN: "Tầng Dưới Tán",
        icon: "🌺",
        height: "0.35 m",
        span: "0.45 m",
        lifespan: "50 - 100 năm",
        desc: "Loài lan hài cực kỳ quý hiếm đặc hữu của vùng núi đá vôi Cao Bằng, Việt Nam. Cánh đài lưng trắng phớt hồng, cánh môi phồng to màu hồng tím đậm như chiếc hài nhung tuyệt mỹ.",
        glbUrl: "../assets/flora/understory_shrubs/endemic_paphiopedilum_vietnamense.glb",
        blendUrl: "../assets/flora/understory_shrubs/endemic_paphiopedilum_vietnamense.blend",
        specUrl: "../docs/flora/species/endemic_paphiopedilum_vietnamense.md",
        turnaroundImg: null,
        representativeId: "understory_sword_fern",
        tags: ["Orchidaceae", "Đặc hữu Cao Bằng", "Sách Đỏ CR", "Lan Hài"]
      }}"""
new_objects_js.append(endemic_obj)

full_db_block = existing_block + ",\n" + ",\n".join(new_objects_js)
new_html = html_text.replace(existing_block, full_db_block)

# Update sidebar header and category tab counts
# Total species = 16 + len(new_objects_js)
total_count = 16 + len(new_objects_js)
new_html = re.sub(r'<span id="flora-count">\d+</span>', f'<span id="flora-count">{total_count}</span>', new_html)
new_html = re.sub(r'<h2>🌱 Bộ Sưu Tập Thực Vật \(<span id="flora-count">.*?</span>\)</h2>',
                  f'<h2>🌱 Bộ Sưu Tập Thực Vật (<span id="flora-count">{total_count}</span>)</h2>', new_html)

# Update category tabs HTML
new_tabs = f"""      <button class="tab-btn active" data-cat="all">Tất cả ({total_count})</button>
      <button class="tab-btn" data-cat="canopy_trees">🌳 Tán Rừng (26)</button>
      <button class="tab-btn" data-cat="understory_shrubs">🌿 Dưới Tán (15)</button>
      <button class="tab-btn" data-cat="grasses_herbs">🌾 Đồng Cỏ & Hoa (26)</button>
      <button class="tab-btn" data-cat="aquatic_wetland">🪷 Thủy Sinh (12)</button>
      <button class="tab-btn" data-cat="arid_succulents">🌵 Sa Mạc (12)</button>
      <button class="tab-btn" data-cat="carnivorous_vines">🪴 Bắt Mồi (7)</button>
      <button class="tab-btn" data-cat="cave_bioluminescent">🍄 Hang Động (5)</button>"""

new_html = re.sub(r'<div class="filter-tabs" id="category-tabs">[\s\S]*?</div>\s*<div class="flora-list"',
                  f'<div class="filter-tabs" id="category-tabs">\n{new_tabs}\n    </div>\n    <div class="flora-list"',
                  new_html)

# Update loadPlantModel to support representativeId fallback
old_load = """      // 1. Ưu tiên giải mã nhị phân Base64 nhúng sẵn (Chạy offline 100% không bị chặn CORS file://)
      const b64Data = (typeof window !== 'undefined' && window.FLORA_MODELS_BASE64) ? window.FLORA_MODELS_BASE64[plant.id] : null;"""

new_load = """      // 1. Ưu tiên giải mã nhị phân Base64 nhúng sẵn (Chạy offline 100% không bị chặn CORS file://)
      let b64Data = (typeof window !== 'undefined' && window.FLORA_MODELS_BASE64) ? window.FLORA_MODELS_BASE64[plant.id] : null;
      // Nếu loài thuộc danh mục 103 loài chưa có 3D riêng, nạp mô hình đại diện chi/họ tương ứng
      if (!b64Data && plant.representativeId && window.FLORA_MODELS_BASE64) {
        b64Data = window.FLORA_MODELS_BASE64[plant.representativeId];
      }"""

new_html = new_html.replace(old_load, new_load)

# Also update selectPlant to show model status
old_badge_update = """      document.getElementById('insp-category-badge').textContent = plant.categoryVN;"""
new_badge_update = """      const isMaster = (typeof window !== 'undefined' && window.FLORA_MODELS_BASE64 && window.FLORA_MODELS_BASE64[plant.id]);
      document.getElementById('insp-category-badge').textContent = plant.categoryVN + (isMaster ? ' · 🌟 3D Master' : ' · 🌿 Mẫu Đại Diện Chi');"""
new_html = new_html.replace(old_badge_update, new_badge_update)

HTML_PATH.write_text(new_html, encoding='utf-8')
print(f"✓ Updated {HTML_PATH} with {total_count} species successfully!")

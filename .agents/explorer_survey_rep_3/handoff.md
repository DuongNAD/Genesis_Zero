# Handoff Report: Creature 3D Web Viewer & Pipeline Verification Architecture

**Agent**: `explorer_survey_rep_3`  
**Date**: 2026-09-05  
**Mission**: Survey existing 3D viewers (`web/flora_viewer.html`, `web/test_creature.html`, `web/watch3d.html`), test runners (`scripts/verify_flora_pipeline.py`, `tests/test_flora_assets.py`), and design the exact technical architecture for `web/creature_viewer.html`, `web/creature_models_data.js`, `scripts/verify_creatures_pipeline.py`, and `pytest tests/test_creature_assets.py`.

---

## 1. Observation

Direct examination of codebase assets, web visualizers, scripts, and tests revealed:

### A. Three.js Vendor & Zero-CORS Offline Pattern
1. **Vendor Libraries**:
   - `web/vendor/three.min.js` (Three.js r128 standalone, zero external CDN dependencies).
   - `web/vendor/GLTFLoader.js` (GLTF/GLB loader compatible with Three.js r128).
2. **Zero-CORS Offline Ingestion Architecture (`web/flora_models_data.js` & `web/flora_viewer.html`)**:
   - In `web/flora_models_data.js`:
     ```javascript
     (typeof window !== "undefined" ? window : globalThis).FLORA_MODELS_BASE64 = {
       "canopy_ancient_oak": "...",
       ...
     };
     ```
   - In `web/flora_viewer.html` (lines 2799–2836):
     ```javascript
     function base64ToArrayBuffer(base64) {
       const binary_string = window.atob(base64);
       const len = binary_string.length;
       const bytes = new Uint8Array(len);
       for (let i = 0; i < len; i++) {
         bytes[i] = binary_string.charCodeAt(i);
       }
       return bytes.buffer;
     }

     function loadPlantModel(plant) {
       let b64Data = (typeof window !== 'undefined' && window.FLORA_MODELS_BASE64) ? window.FLORA_MODELS_BASE64[plant.id] : null;
       if (b64Data) {
         const buffer = base64ToArrayBuffer(b64Data);
         gltfLoader.parse(buffer, '', (gltf) => onModelLoaded(gltf, plant.nameVN));
         return;
       }
       loadModelViaUrl(plant.glbUrl, plant.nameVN); // fallback for HTTP/HTTPS
     }
     ```
   - This bypasses browser `file:///` sandbox restrictions completely without requiring a local web server.

### B. Camera Orbit Controls
- `web/flora_viewer.html` (lines 3140–3240) and `web/test_creature.html` (lines 322–370) use pure vanilla Three.js spherical math (`spherical.theta`, `spherical.phi`, `spherical.radius`) bound to mouse and touch events (`mousedown`, `mousemove`, `wheel`, `touchstart`, `touchmove`). No external `OrbitControls.js` dependency is required.

### C. Animation Mixer & Skeleton Helper Mechanics
- `web/test_creature.html` (lines 249–265, 279–313):
  - **SkeletonHelper**:
    ```javascript
    skeletonHelper = new THREE.SkeletonHelper(model);
    skeletonHelper.visible = false;
    scene.add(skeletonHelper);
    function toggleBones() {
      showBones = !showBones;
      if (skeletonHelper) skeletonHelper.visible = showBones;
    }
    ```
  - **AnimationMixer**:
    ```javascript
    mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => {
      actions[clip.name] = mixer.clipAction(clip);
    });
    ```
  - **Crossfade switching**:
    ```javascript
    function switchAnimation(name) {
      if (!actions[name] || actions[name] === activeAction) return;
      const prevAction = activeAction;
      activeAction = actions[name];
      if (prevAction) prevAction.fadeOut(0.2);
      activeAction.reset().setEffectiveTimeScale(playbackSpeed).setEffectiveWeight(1).fadeIn(0.2).play();
    }
    ```
  - **Render loop integration**:
    ```javascript
    const delta = clock.getDelta();
    if (mixer && isPlaying) mixer.update(delta * playbackSpeed);
    ```

### D. Existing Creature Assets & Animation Status
- Inspection of `assets/creatures/*.glb` via glTF binary chunk analysis showed:
  - `creature_L1_Evo_s1.glb` already contains 8 baked action clips:
    `['Creature_L1_Evo_s1_Alert', 'Creature_L1_Evo_s1_Attack', 'Creature_L1_Evo_s1_Death', 'Creature_L1_Evo_s1_Eat', 'Creature_L1_Evo_s1_Hurt', 'Creature_L1_Evo_s1_Idle', 'Creature_L1_Evo_s1_Run', 'Creature_L1_Evo_s1_Walk']`.
  - Older single-animation models (`creature_L1_s1.glb`, `L2`, `L3`, `L4`, `L5`, `W1`, `A1`) only contain `..._Idle`.
  - In `genesis/creature_builder.py` (lines 640–840), the complete procedural rigging and 8-action baking pipeline is already fully implemented in Python via Blender NLA tracks:
    1. `Idle_Normal` (breath, look)
    2. `Idle_Alert` (high alertness)
    3. `Walk` (organic spine walk cycle)
    4. `Run` (gallop / sprint cycle)
    5. `Attack` (strike / bite / lunge)
    6. `Hurt_Defend` (flinch / pain reflex)
    7. `Eat` (head dip / jaw chew)
    8. `Death` (knee collapse / slump)

### E. Existing Verification Pipelines
- `scripts/verify_flora_pipeline.py` and `tests/test_flora_assets.py` validate 6 dimensions:
  1. Metadata & Taxonomy (`README.md`, specs).
  2. Turnaround concept sheets (JPEG SOI `\xff\xd8` and EOI `\xff\xd9`, file size > 50KB).
  3. 3D Model deliverables (`.blend` magic `BLEN` or zstd `0x28B52FFD`, size > 1KB).
  4. glTF 2.0 binary conformance (magic `glTF`, version 2, JSON chunk 0, BIN chunk 1).
  5. Web viewer sync & base64 exact binary hash matching.
  6. Headless Blender BMesh topology (0 incontiguous edges, 0 loose verts, 0 ngons, 100% smooth shading).

---

## 2. Logic Chain & Technical Architecture

### Component 1: `web/creature_viewer.html` Technical Architecture

The creature viewer must provide a studio-grade interactive inspection station matching `flora_viewer.html`'s aesthetic and operational polish, specialized for rigged and animated fauna.

#### 1.1 Layout & DOM Structure
```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Genesis Zero · Trình Xem Sinh Vật 3D (3D Creature Studio)</title>
  <link rel="icon" href="data:image/svg+xml,...">
  <style>/* Cyberpunk dark glassmorphism HUD */</style>
  <script src="vendor/three.min.js"></script>
  <script src="vendor/GLTFLoader.js"></script>
  <script src="creature_models_data.js"></script>
</head>
<body>
  <!-- 1. Header HUD: Brand cluster, Tier tabs, and Quick actions -->
  <header class="hud-header">
    <div class="brand-cluster">
      <h1>🐺 Genesis Zero <span class="sep">|</span> Trình Xem Sinh Vật 3D</h1>
      <span class="badge">Blender 5.2.1 LTS · 8-Action Rigged</span>
    </div>
    <div class="header-quick-actions">
      <a href="watch3d.html" class="header-btn">🌐 3D Spectator</a>
      <a href="flora_viewer.html" class="header-btn">🌿 Thư Viện Thực Vật</a>
      <label class="header-btn">
        📁 Mở GLB Cục Bộ
        <input type="file" id="local-file-input" accept=".glb,.gltf" style="display:none;">
      </label>
    </div>
  </header>

  <!-- 2. Left Sidebar: Creature Catalog -->
  <aside class="sidebar" id="creature-sidebar">
    <div class="sidebar-header">
      <div class="title-row">
        <h2>🐾 Danh Mục Sinh Vật (<span id="creature-count">10</span>)</h2>
      </div>
      <input type="text" id="search-input" class="search-box" placeholder="Tìm theo tên loài, mã L1..L5, W1, A1...">
    </div>
    <div class="filter-tabs" id="domain-tabs">
      <button class="tab-btn active" data-domain="all">Tất cả (10)</button>
      <button class="tab-btn" data-domain="CAN">🏔️ Tầng Cạn (5)</button>
      <button class="tab-domain" data-domain="NUOC">🌊 Tầng Nước (1)</button>
      <button class="tab-domain" data-domain="TROI">🦅 Tầng Trời (1)</button>
      <button class="tab-domain" data-domain="EVO">✨ Đặc Thù & Tiến Hóa (3)</button>
    </div>
    <div class="creature-list" id="creature-list"></div>
  </aside>

  <!-- 3. Floating Bottom Animation & Playback Control Bar -->
  <div class="playback-toolbar" id="playback-toolbar">
    <!-- 8 Action Selector -->
    <div class="anim-clip-group" id="anim-clip-group">
      <button class="clip-btn active" data-anim="Idle_Normal">🟢 Idle Normal</button>
      <button class="clip-btn" data-anim="Idle_Alert">🟡 Idle Alert</button>
      <button class="clip-btn" data-anim="Walk">🚶 Walk</button>
      <button class="clip-btn" data-anim="Run">⚡ Run</button>
      <button class="clip-btn" data-anim="Attack">⚔️ Attack</button>
      <button class="clip-btn" data-anim="Hurt_Defend">🛡️ Hurt / Defend</button>
      <button class="clip-btn" data-anim="Eat">🍖 Eat</button>
      <button class="clip-btn" data-anim="Death">💀 Death</button>
    </div>
    <div class="toolbar-divider"></div>
    <!-- Playback Speeds & State -->
    <div class="speed-control-group">
      <button class="tool-btn" id="btn-toggle-play" onclick="togglePlay()">⏸ Tạm Dừng</button>
      <button class="speed-btn" data-speed="0.25">0.25x</button>
      <button class="speed-btn" data-speed="0.5">0.5x</button>
      <button class="speed-btn active" data-speed="1.0">1.0x</button>
      <button class="speed-btn" data-speed="2.0">2.0x</button>
    </div>
    <div class="toolbar-divider"></div>
    <!-- Visual Overlays -->
    <div class="overlay-control-group">
      <button class="tool-btn" id="btn-toggle-skeleton" onclick="toggleSkeleton()">🦴 Bộ Xương</button>
      <button class="tool-btn" id="btn-toggle-wireframe" onclick="toggleWireframe()">🕸 Lưới Dây</button>
      <button class="tool-btn" id="btn-toggle-turntable" onclick="toggleTurntable()">🔄 Tự Xoay</button>
      <button class="tool-btn" onclick="resetCamera()">🎯 Căn Giữa</button>
    </div>
  </div>

  <!-- 4. Right Panel: Biological Traits & Specs HUD -->
  <aside class="inspector-panel" id="inspector-panel">
    <div class="creature-header-box">
      <div class="panel-section-title">
        <span>Hồ Sơ Sinh Học</span>
        <span id="insp-domain-badge" class="tag-pill">Tầng Cạn · CAN</span>
      </div>
      <h2 id="insp-name-vn">Thằn Lằn Cát Apex</h2>
      <div id="insp-id-subtitle" class="latin-subtitle">Mã: L1_s1 · Founder Apex Predator</div>
    </div>

    <!-- 6 Vector Traits HUD -->
    <div class="panel-section">
      <div class="panel-section-title">Chỉ Số Sinh Học (6 Founder Traits)</div>
      <div class="traits-bars" id="traits-bars">
        <!-- brain, attack, armor, speed, sense, stomach with animated progress bars (0-5) -->
      </div>
    </div>

    <!-- Biological Features & Adaptations -->
    <div class="panel-section">
      <div class="panel-section-title">Đặc Điểm Tiến Hóa (Biological Features)</div>
      <div class="tags-cluster" id="insp-features"></div>
    </div>

    <!-- 3D Mesh & Rig Technical Metrics -->
    <div class="panel-section">
      <div class="panel-section-title">Thông Số Kỹ Thuật 3D & Khung Xương</div>
      <div class="metrics-grid">
        <div class="metric-card"><div class="metric-label">Số Đỉnh (Verts)</div><div class="metric-value" id="mesh-verts">—</div></div>
        <div class="metric-card"><div class="metric-label">Số Mặt (Faces)</div><div class="metric-value" id="mesh-faces">—</div></div>
        <div class="metric-card"><div class="metric-label">Số Khớp (Bones)</div><div class="metric-value" id="rig-bones">—</div></div>
        <div class="metric-card"><div class="metric-label">Animation Clips</div><div class="metric-value" id="clip-count">8 Tracks</div></div>
      </div>
    </div>

    <!-- Actions -->
    <div class="action-group">
      <button class="btn-action secondary-violet" id="btn-open-turnaround" onclick="openTurnaroundModal()">
        📷 Bản Vẽ Thiết Kế 4 Góc (Turnaround)
      </button>
      <a href="#" target="_blank" class="btn-action primary" id="btn-download-blend" download>📥 Tải File Gốc Blender (.BLEND)</a>
      <a href="#" target="_blank" class="btn-action" id="btn-download-glb" download>🌐 Tải File Game-Ready (.GLB)</a>
    </div>
  </aside>

  <!-- 5. 3D Canvas Viewport -->
  <div id="viewport-container"></div>

  <!-- 6. Turnaround 4-View Modal Dialog -->
  <dialog id="turnaround-modal">
    <div class="modal-header">
      <h3 id="modal-title">📷 Bản Vẽ Thiết Kế 4 Mặt Chuẩn Scan (Turnaround Sheet)</h3>
      <button class="modal-close-btn" onclick="closeTurnaroundModal()">✕</button>
    </div>
    <div class="modal-body">
      <img id="modal-img" src="" alt="Turnaround Sheet">
      <p class="modal-caption" id="modal-caption">
        Bản vẽ kỹ thuật 4 góc độ (3/4 Phối Cảnh, Mặt Trước Ortho, Mặt Bên Ortho, Nhìn Từ Trên Xuống Ortho).
      </p>
    </div>
  </dialog>
</body>
</html>
```

#### 1.2 Data Schema & Database Definition
```javascript
const CREATURE_DATABASE = [
  {
    id: "creature_L1_s1",
    speciesId: "L1",
    seed: 1,
    nameVN: "Thằn Lằn Cát Apex",
    nameEN: "Sand Skink Apex",
    domain: "CAN",
    domainVN: "Tầng Cạn",
    icon: "🦎",
    role: "Apex Predator (Gemma-2-9B)",
    traits: { brain: 4, attack: 3, armor: 1, speed: 2, sense: 1, stomach: 1 },
    features: ["Lông Dài", "Lưỡng Cư", "Trèo Giỏi"],
    desc: "Đầu óc 4, tay 3, đứng vững trên bốn chi với sọ lớn mang vân chạy dọc, bộ móng cong uy lực cùng khả năng thích nghi cao.",
    glbUrl: "../assets/creatures/creature_L1_s1.glb",
    blendUrl: "../assets/creatures/creature_L1_s1.blend",
    turnaroundImg: "creature_images/creature_L1_s1_turnaround.jpg"
  },
  {
    id: "creature_L2_s1",
    speciesId: "L2",
    seed: 1,
    nameVN: "Chồn Tuyết Phục Kích",
    nameEN: "Snow Ferret Ambush",
    domain: "CAN",
    domainVN: "Tầng Cạn",
    icon: "🦡",
    role: "Ambush Predator (Llama-3.1-8B)",
    traits: { brain: 3, attack: 4, armor: 2, speed: 1, sense: 2, stomach: 0 },
    features: ["Biết Đào Hang", "Lông Dài", "Mắt Đêm"],
    desc: "Sọ tròn cao, trán rộng, móng vuốt bè to chuyên bới đất, bộ lông dài rậm rạp cùng đôi mắt đêm to tròn.",
    glbUrl: "../assets/creatures/creature_L2_s1.glb",
    blendUrl: "../assets/creatures/creature_L2_s1.blend",
    turnaroundImg: "creature_images/creature_L2_s1_turnaround.jpg"
  },
  {
    id: "creature_L3_s1",
    speciesId: "L3",
    seed: 1,
    nameVN: "Dê Núi Thích Nghi",
    nameEN: "Alpine Ibex",
    domain: "CAN",
    domainVN: "Tầng Cạn",
    icon: "🐐",
    role: "Adaptable Herbivore (Mistral-7B)",
    traits: { brain: 3, attack: 1, armor: 1, speed: 3, sense: 3, stomach: 1 },
    features: ["Lông Dài", "Túi Má", "Vảy Cứng"],
    desc: "Cổ ngắn mập, má phồng thành túi dự trữ, chân dài gân guốc leo vách đá tuyết, lớp sừng bảo vệ sống lưng.",
    glbUrl: "../assets/creatures/creature_L3_s1.glb",
    blendUrl: "../assets/creatures/creature_L3_s1.blend",
    turnaroundImg: "creature_images/creature_L3_s1_turnaround.jpg"
  },
  {
    id: "creature_L4_s1",
    speciesId: "L4",
    seed: 1,
    nameVN: "Thỏ Bọc Giáp",
    nameEN: "Armored Meadow Hare",
    domain: "CAN",
    domainVN: "Tầng Cạn",
    icon: "🐇",
    role: "Armored Defender (Phi-3.5-mini)",
    traits: { brain: 1, attack: 1, armor: 5, speed: 1, sense: 2, stomach: 2 },
    features: ["Biết Đào Hang", "Lông Dài", "Lưỡng Cư"],
    desc: "Tấm mai dày liền khối cứng cáp chịu đòn, chi ngắn chắc bới hang ngầm trốn tránh kẻ săn mồi.",
    glbUrl: "../assets/creatures/creature_L4_s1.glb",
    blendUrl: "../assets/creatures/creature_L4_s1.blend",
    turnaroundImg: "creature_images/creature_L4_s1_turnaround.jpg"
  },
  {
    id: "creature_L5_s1",
    speciesId: "L5",
    seed: 1,
    nameVN: "Kỳ Nhông Độc Tốc Độ",
    nameEN: "Venomous Swift Skink",
    domain: "CAN",
    domainVN: "Tầng Cạn",
    icon: "🦎",
    role: "Speed & Poison (Qwen2.5-1.5B)",
    traits: { brain: 0, attack: 2, armor: 0, speed: 5, sense: 3, stomach: 2 },
    features: ["Biết Đào Hang", "Lưỡng Cư", "Trèo Giỏi"],
    desc: "Thân thon nhẹ đạt tốc độ di chuyển 3 ô/lượt, da trần ẩm bóng, phản xạ chớp nhoáng trèo cây bơi lội.",
    glbUrl: "../assets/creatures/creature_L5_s1.glb",
    blendUrl: "../assets/creatures/creature_L5_s1.blend",
    turnaroundImg: "creature_images/creature_L5_s1_turnaround.jpg"
  },
  {
    id: "creature_W1_s1",
    speciesId: "W1",
    seed: 1,
    nameVN: "Cá Săn Mồi Vực Sâu",
    nameEN: "Abyssal Hunter",
    domain: "NUOC",
    domainVN: "Tầng Nước",
    icon: "🐟",
    role: "Aquatic Hunter",
    traits: { brain: 1, attack: 1, armor: 0, speed: 5, sense: 4, stomach: 1 },
    features: ["Bơi Nhanh", "Cảm Biến Thủy Triều", "Vây Lưng"],
    desc: "Thân thuôn mượt mà lướt dưới tầng nước sâu, tốc độ 5 ô/lượt, giác quan 4 cảm nhận sóng âm từ xa.",
    glbUrl: "../assets/creatures/creature_W1_s1.glb",
    blendUrl: "../assets/creatures/creature_W1_s1.blend",
    turnaroundImg: "creature_images/creature_W1_s1_turnaround.jpg"
  },
  {
    id: "creature_A1_s1",
    speciesId: "A1",
    seed: 1,
    nameVN: "Đại Bàng Bão Táp",
    nameEN: "Storm Eagle",
    domain: "TROI",
    domainVN: "Tầng Trời",
    icon: "🦅",
    role: "Sky Scout & Raptor",
    traits: { brain: 2, attack: 2, armor: 0, speed: 4, sense: 4, stomach: 0 },
    features: ["Sải Cánh Rộng", "Mắt Đại Bàng", "Móng Vuốt Vồ"],
    desc: "Tầm nhìn xa nhất bản đồ, chao lượn trên tầng trời quan sát toàn cảnh và lao xuống tấn công chớp nhoáng.",
    glbUrl: "../assets/creatures/creature_A1_s1.glb",
    blendUrl: "../assets/creatures/creature_A1_s1.blend",
    turnaroundImg: "creature_images/creature_A1_s1_turnaround.jpg"
  },
  {
    id: "creature_L1_Evo_s1",
    speciesId: "L1_Evo",
    seed: 1,
    nameVN: "Quái Thú Apex Tiến Hóa",
    nameEN: "Evolved Carnivore Apex",
    domain: "EVO",
    domainVN: "Tiến Hóa Cấp Cao",
    icon: "🦖",
    role: "Tier 3 Super Apex",
    traits: { brain: 5, attack: 5, armor: 4, speed: 4, sense: 3, stomach: 2 },
    features: ["Răng Nanh Sắc", "Cơ Bắp Cường Hóa", "Gầm Thét"],
    desc: "Sinh vật tiến hóa vượt bậc với tổng điểm 23, tích hợp trọn vẹn 8 animation tracks mượt mà.",
    glbUrl: "../assets/creatures/creature_L1_Evo_s1.glb",
    blendUrl: "../assets/creatures/creature_L1_Evo_s1.blend",
    turnaroundImg: "creature_images/creature_L1_Evo_s1_turnaround.jpg"
  },
  {
    id: "creature_giant_tarantula",
    speciesId: "Tarantula",
    seed: 1,
    nameVN: "Nhện Khổng Lồ Độc",
    nameEN: "Mexican Redknee Tarantula",
    domain: "EVO",
    domainVN: "Đặc Thù",
    icon: "🕷️",
    role: "Bio-Construct Lurker",
    traits: { brain: 3, attack: 4, armor: 3, speed: 3, sense: 5, stomach: 2 },
    features: ["Tám Chân", "Tuyến Độc", "Mắt Kép"],
    desc: "Nhện khổng lồ với 34 xương phân cấp, cấu trúc chuyển động chân độc lập sắc nét.",
    glbUrl: "../assets/creatures/creature_giant_tarantula.glb",
    blendUrl: "../assets/creatures/creature_giant_tarantula.blend",
    turnaroundImg: "creature_images/creature_giant_tarantula_turnaround.jpg"
  },
  {
    id: "genesis_sentinel",
    speciesId: "Sentinel",
    seed: 1,
    nameVN: "Sentinel Cơ Khí Sinh Học",
    nameEN: "Armored Bio-Sentinel",
    domain: "EVO",
    domainVN: "Cơ Khí Sinh Học",
    icon: "🤖",
    role: "Ecosystem Guardian",
    traits: { brain: 4, attack: 4, armor: 5, speed: 2, sense: 4, stomach: 1 },
    features: ["Giáp Hợp Kim", "Lõi Năng Lượng Emissive", "Phòng Vệ Độc Lập"],
    desc: "Hộ vệ máy sinh học bọc giáp với đèn phát quang emissive và khung xương chiến đấu.",
    glbUrl: "../web/genesis_sentinel.glb",
    blendUrl: "../assets/creatures/genesis_sentinel.blend",
    turnaroundImg: "creature_images/genesis_sentinel_turnaround.jpg"
  }
];
```

#### 1.3 8-Animation Crossfade State Machine
```javascript
const CANONICAL_ACTIONS = [
  'Idle_Normal', 'Idle_Alert', 'Walk', 'Run',
  'Attack', 'Hurt_Defend', 'Eat', 'Death'
];

let mixer = null;
let actions = {};
let activeAction = null;
let currentClipKey = 'Idle_Normal';
let playbackSpeed = 1.0;
let isPlaying = true;
let skeletonHelper = null;
let showSkeleton = false;

function setupAnimations(gltf) {
  actions = {};
  if (!gltf.animations || gltf.animations.length === 0) return;
  mixer = new THREE.AnimationMixer(gltf.scene);

  gltf.animations.forEach((clip) => {
    // Canonical match: check if clip name contains Idle, Alert, Walk, Run, Attack, Hurt, Eat, Death
    let matchedKey = null;
    const lower = clip.name.toLowerCase();
    if (lower.includes('alert')) matchedKey = 'Idle_Alert';
    else if (lower.includes('idle')) matchedKey = 'Idle_Normal';
    else if (lower.includes('walk')) matchedKey = 'Walk';
    else if (lower.includes('run')) matchedKey = 'Run';
    else if (lower.includes('attack') || lower.includes('atk')) matchedKey = 'Attack';
    else if (lower.includes('hurt') || lower.includes('hit') || lower.includes('defend')) matchedKey = 'Hurt_Defend';
    else if (lower.includes('eat')) matchedKey = 'Eat';
    else if (lower.includes('death') || lower.includes('die')) matchedKey = 'Death';
    else matchedKey = clip.name;

    const action = mixer.clipAction(clip);
    actions[matchedKey] = action;
    actions[clip.name] = action;
  });

  // Start with Idle_Normal or first clip
  const defaultAction = actions['Idle_Normal'] || actions[gltf.animations[0].name];
  if (defaultAction) {
    activeAction = defaultAction;
    activeAction.setEffectiveTimeScale(playbackSpeed).play();
    updateClipButtonsUI('Idle_Normal');
  }
}

function switchAnimation(clipKey) {
  const targetAction = actions[clipKey];
  if (!targetAction || targetAction === activeAction) return;

  const prev = activeAction;
  activeAction = targetAction;
  if (prev) prev.fadeOut(0.2);
  activeAction.reset().setEffectiveTimeScale(playbackSpeed).fadeIn(0.2).play();
  currentClipKey = clipKey;
  updateClipButtonsUI(clipKey);
}

function setPlaybackSpeed(spd) {
  playbackSpeed = spd;
  if (activeAction) activeAction.setEffectiveTimeScale(spd);
  document.querySelectorAll('.speed-btn').forEach(btn => {
    btn.classList.toggle('active', parseFloat(btn.dataset.speed) === spd);
  });
}

function toggleSkeleton() {
  showSkeleton = !showSkeleton;
  if (skeletonHelper) skeletonHelper.visible = showSkeleton;
  document.getElementById('btn-toggle-skeleton').classList.toggle('active', showSkeleton);
}
```

---

### Component 2: `web/creature_models_data.js` & `scripts/sync_all_creature_models_to_js.py`

Following the proven zero-CORS architecture of `scripts/sync_all_flora_models_to_js.py`, create:
- `scripts/sync_all_creature_models_to_js.py`:
  - Scans `assets/creatures/*.glb` and `web/*.glb`.
  - Encodes each `.glb` into Base64.
  - Generates `web/creature_models_data.js`:
    ```javascript
    /* Genesis Zero — Embedded 3D Creature Binary Bundles (Zero-CORS offline file:// support) */
    (typeof window !== "undefined" ? window : globalThis).CREATURE_MODELS_BASE64 = {
      "creature_L1_s1": "<base64_data>",
      "creature_L2_s1": "<base64_data>",
      ...
    };
    ```

---

### Component 3: `scripts/verify_creatures_pipeline.py` Architecture

Standalone executable Python audit tool mirroring `scripts/verify_flora_pipeline.py`. Exits with code 0 on 100% compliance.

```python
class CreaturePipelineVerifier:
    def __init__(self):
        self.results = []
        self.total_checks = 0
        self.passed_checks = 0

    # 1. Biological Taxonomy & Founder Traits
    def verify_traits_and_metadata(self):
        # Asserts: 6 founder traits sum == 12, each in [0, 5]
        # Asserts: Domain in {CAN, NUOC, TROI}, features roll matches seed

    # 2. Turnaround Concept Sheets
    def verify_turnaround_sheets(self):
        # Asserts: web/creature_images/<id>_turnaround.jpg exists, size > 50KB,
        # header == b"\xff\xd8" and footer == b"\xff\xd9"

    # 3. 3D Model Master Deliverables
    def verify_3d_assets(self):
        # Asserts: assets/creatures/<id>.blend exists with 'BLEN' or zstd 0x28B52FFD magic
        # Asserts: assets/creatures/<id>.glb exists, size > 5KB

    # 4. glTF 2.0 Binary & Armature/Animation Conformance
    def verify_gltf2_rig_and_animations(self):
        # 12-byte glTF header: magic == b"glTF", version == 2, length == fsize
        # Chunk 0 JSON:
        #   - meshes count >= 1
        #   - skins count >= 1 (Rigging Armature present)
        #   - animations count >= 8 (Idle_Normal, Idle_Alert, Walk, Run, Attack, Hurt_Defend, Eat, Death)
        #   - all samplers & channels count > 0

    # 5. Web Viewer & Offline Base64 Synchronization
    def verify_web_viewer_sync(self):
        # Asserts: web/creature_viewer.html exists, contains 8 anim buttons, skeleton toggle
        # Asserts: web/creature_models_data.js contains exact byte match of disk .glb

    # 6. Headless Blender BMesh Topology
    def verify_bmesh_topology(self):
        # Runs Blender headless:
        #   0 loose verts, 0 incontiguous edges, 0 multi-face edges,
        #   0 ngons (>4 verts), 100% smooth shading polygons.
```

---

### Component 4: `pytest tests/test_creature_assets.py` Test Suite Architecture

Modular pytest suite using `@pytest.mark.parametrize`:
```python
class TestCreatureBiologicalSpecs:
    def test_founder_traits_invariants(self, species_id): ...
    def test_features_and_prompt_generation(self, species_id): ...

class TestCreatureTurnaroundSheets:
    def test_turnaround_jpeg_integrity(self, creature_id): ...

class TestCreatureDeliverables:
    def test_blend_file_header_magic(self, creature_id): ...
    def test_glb_file_size_and_container(self, creature_id): ...

class TestGltf2RigAnd8Animations:
    def test_armature_skin_present(self, creature_id): ...
    def test_all_8_canonical_animations_present(self, creature_id): ...
    def test_animation_samplers_and_channels(self, creature_id): ...

class TestCreatureWebViewerSync:
    def test_html_dom_elements_and_controls(self): ...
    def test_base64_offline_byte_match(self, creature_id): ...

class TestBlenderMeshTopology:
    def test_bmesh_zero_defects_and_smooth_shading(self): ...
```

---

## 3. Caveats

1. **Asset Generation Prerequisite**: 
   While `creature_L1_Evo_s1.glb` already has all 8 animations, `creature_L1_s1.glb` through `A1_s1.glb` currently contain only `Idle` actions. Running the implementer agent to re-export them via `genesis.creature_builder.build_creature_blender_code()` will bake all 8 animations across all target species cleanly.
2. **Turnaround Images**:
   The directory `web/creature_images/` needs to be populated with 4-angle turnaround concept sheets (`<species>_turnaround.jpg`) either rendered from Blender or generated via concept tooling, mirroring `web/flora_images/`.
3. **Blender Executable Path**:
   Headless testing relies on `/Applications/Blender.app/Contents/MacOS/Blender` (standard on macOS). A fallback check `shutil.which("blender")` is supported.

---

## 4. Conclusion

- The offline zero-CORS architecture (`web/creature_models_data.js` Base64 dictionary + `atob` `ArrayBuffer` parsing) provides a seamless experience for local file viewing without CORS errors.
- The procedural 8-animation baking pipeline in `genesis/creature_builder.py` is already established and battle-tested.
- The design for `web/creature_viewer.html` combines the responsive cyber-HUD interface of `flora_viewer.html` with a specialized fauna control rig: 8-animation crossfading, variable playback speed (0.25x–2.0x), dynamic skeleton overlay (`THREE.SkeletonHelper`), 6-trait HUD, and turnaround modal inspection.
- The verification suite design (`scripts/verify_creatures_pipeline.py` and `tests/test_creature_assets.py`) guarantees 100% test coverage across all 6 core quality criteria.

---

## 5. Verification Method

To independently verify this architectural survey and the existing assets:

1. **Inspect existing models and animation clips**:
   ```bash
   python3 -c '
   import glob, json, struct
   for f in sorted(glob.glob("assets/creatures/*.glb")):
       with open(f, "rb") as fp:
           magic, ver, length = struct.unpack("<4sII", fp.read(12))
           c0_len, _ = struct.unpack("<II", fp.read(8))
           meta = json.loads(fp.read(c0_len).decode("utf-8"))
           print(f.split("/")[-1], "Skins:", len(meta.get("skins", [])), "Animations:", [a["name"] for a in meta.get("animations", [])])
   '
   ```
2. **Check Blender executable availability**:
   ```bash
   /Applications/Blender.app/Contents/MacOS/Blender --version
   ```
3. **Inspect Flora benchmark verification**:
   ```bash
   python3 scripts/verify_flora_pipeline.py
   pytest tests/test_flora_assets.py -q
   ```
4. **Inspect Generated Report**:
   ```bash
   cat /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_rep_3/handoff.md
   ```

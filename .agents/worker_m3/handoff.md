# Handoff Report — Worker M3: Milestone 3 (3D Visualizer & Compact Map Experience)

## 1. Observation
1. **Initial Codebase State**:
   - `web/watch3d.html` (52 lines) was a barebones container with only a basic 4-item text header and simple log feed. It lacked a Law Journal / Codex HUD, creature inspection card, tactical minimap, camera controls, and victory celebration ceremony.
   - `web/watch3d.js` (288 lines) had all creatures flattened to ground elevation $y=0.10$ (`g.position.set(c.x + 0.5, TERRAIN.P.h, c.y + 0.5)`), ignoring 3-tier domains (`NUOC`, `CAN`, `TROI`), climbing mechanics (`TREE` canopies), and submerged depths.
   - `web/watch3d.js` completely omitted rendering `frame.plants` (fruits/algae) and `frame.corpses` (remains).
   - In `web/watch3d.js:122-168`, `makeBody(c)` only handled simple trait primitives and lacked the 3 domain silhouettes and 12 biological features defined in `genesis/features.py`.
   - `web/watch3d.js:203-209` created `new THREE.BufferGeometry().setFromPoints(...)` on every frame inside `loop()`, creating garbage collection pressure.
   - `web/watch3d.js:213-223` had a single flat wireframe ring for `LAW_FIRED` events without multi-particle shockwaves or elemental cues.

2. **Implemented Changes**:
   - **`web/watch3d.html`**:
     - Built a comprehensive spectator HUD featuring:
       - Header bar with phase badges (`SEEDING`, `LOBBY`, `RUNNING`, `REVEAL`, `COOLDOWN`), tick counter, alive counter, map name, and live 3-tier domain breakdown (`🌊 Nước`, `🌿 Cạn`, `🦅 Trời`).
       - Camera toolbar buttons (`🌐 Isometric (1)`, `🎯 Top-Down (2)`, `🔍 Tự do (3)`), and HUD toggles (`📡 Nghe (G)`, `📜 Sổ luật (J)`, `🗺️ Minimap (M)`).
       - Law Journal / Codex HUD left panel displaying active hypotheses, observation status, confidence ratings, and law triggers counter.
       - Rich event log feed with color-coded tags (`SPEAK` cyan, `LAW_FIRED` gold, `DEATH` red, `ATTACK` orange, `EAT` green).
       - Tactical 2D minimap canvas in bottom-left displaying real-time 24×24 terrain, creature dots, plants, and corpses.
       - Interactive Creature Inspection Card in bottom-right displaying creature ID, domain tag, HP bar, Energy bar, 6 trait values with radar/mini-bars, and 12 biological feature badges with Vietnamese tooltips.
       - REVEAL Phase Grand Victory Ceremony modal displaying the 3 victory podiums (🏆 Nhà khoa học, 🛡️ Kẻ sống sót, ⚡ Người đầu tiên) and public revealed laws.
     - Preserved 100% offline self-containment with zero external CDNs or http/https script tags.
   - **`web/watch3d.js`**:
     - Compact Diorama Framing: Built a floating island base pedestal (`THREE.BoxGeometry(W+1.6, 2.2, H+1.6)` at $y=-1.15$), chamfered bezel border, and translucent ocean water plane (`y=0.02`, opacity 0.65).
     - Camera navigation: Intuitive camera presets (`ISO`, `TOP`, `FREE`, `FOLLOW`) with smooth damping (`targetYaw`, `targetPitch`, `targetDist`, `targetCx`, `targetCz`).
     - 3-Tier Elevation Ecosystem:
       - Airborne sky: $y=2.5$ for `Domain.TROI` (e.g. `A1`) with gentle flight bobbing.
       - Tree canopy: $y=1.45$ for climbing creatures with `speed >= 3` on `TREE` tiles (`'T'`).
       - Ground terrain: $y=0.25$ for `Domain.CAN` on `PLAIN`, `BUSH`, `FIRE`, $y=1.11$ on `ROCK`, $y=0.20$ in `CAVE`.
       - Submerged water: $y=-0.25$ for `Domain.NUOC` (e.g. `W1`) in `WATER`/`DEEP` with undulating swim oscillation.
     - Smooth Entity Movement: Position lerping (`currX`, `currY`, `currZ`) with toroidal boundary wrapping handling and smooth heading rotation (`Math.atan2(dx, dz)`).
     - Food & Corpse Rendering:
       - `frame.plants`: Low-poly fruit clusters (red spheres on land) and aquatic kelp/algae fronds (green cylinders in water).
       - `frame.corpses`: Ivory bone skeletal remains (`#e2e8f0`) with visual decay.
     - Procedural 3D Morphology (`makeBody`):
       - 3 Domain Silhouettes: `NUOC` (streamlined torpedo body, vertical caudal fin, pectoral fins), `TROI` (aerodynamic body, swept-back wings, tail fan), `CAN` (quadrupedal body, 4 legs, tail, raised head).
       - 6 Numeric Traits: `brain` (cranial dome radius + neural halo for $\ge 3$), `attack` (sharp mandibles/fangs), `armor` (dorsal carapace plates), `speed` (body elongation + leg length), `sense` (multi-eye cluster $2 \rightarrow 4 \rightarrow 6$), `stomach` (abdominal girth).
       - 12 Biological Features: `LUONG_CU` (webbed flippers), `DAO_HANG` (heavy digging claws), `TREO_GIOI` (prehensile tail), `CANH_LUOT` (gliding membrane), `LONG_DAI` (shaggy neck ruff), `VAY_CUNG` (scute scales), `GAI_DOC` (bioluminescent purple spikes), `VO_SO` (dome shell carapace), `MAT_DEM` (large luminous night eyes), `RAU_CAM_UNG` (twin sensory antennae), `RANG_NANH` (saber tusks), `TUI_MA` (bulging cheek pouches), plus all aliases.
     - Law Fired Shockwaves: Multi-tier expanding golden ring + ascending torus + particle aura for `LAW_FIRED` events.
     - REVEAL Phase 3D Victory Podiums: 3 gold, silver, and bronze podium pedestals rising at the diorama center.
     - Performance & GC Optimization: Replaced per-frame `new THREE.BufferGeometry` in hearing graph with pre-allocated Float32Array buffers and `THREE.LineSegments`.
     - Mouse Raycasting & Selection: Interactive raycaster to click any creature in 3D, highlight with a glowing blue selection ring, focus camera in follow mode, and populate inspection stats.
   - **`net/match.py`**:
     - Enhanced `frame()` to include `species`, `domain`, and `features` on creature telemetry dictionaries, enabling rich visualizer inspection while strictly adhering to `FORBIDDEN_RUNNING_PATTERN`.

## 2. Logic Chain
1. Requirement R3 and Task 1 mandate a compact diorama island base with stylized bezel border and smooth camera presets. `watch3d.js` was updated to construct base pedestal geometries and smooth damping orbit controls with Isometric, Top-Down, and Follow modes.
2. Requirement R3 and Task 2 require a distinct 3-tier vertical elevation ecosystem. `getElevation()` maps creatures according to domain (`TROI` $\rightarrow$ $y=2.5$, `TREE` climbers $\rightarrow$ $y=1.45$, `CAN` ground $\rightarrow$ $y=0.25$, `NUOC` $\rightarrow$ $y=-0.25$), accompanied by smooth movement interpolation.
3. Requirement R3 and Task 3 require rendering food and corpses from telemetry frames. `syncPlantsAndCorpses()` maps `frame.plants` to fruits/algae and `frame.corpses` to skeletal remains.
4. Requirement R3 and Task 4 require procedural 3D morphology for 6 numeric traits and 12 biological features. `makeBody()` constructs domain-specific silhouettes and procedural geometry attachments for all 12 features from `genesis/features.py`.
5. Requirement R3 and Task 5 require real-time Law Journal HUD, dynamic law activation shockwaves, and REVEAL victory podiums. `watch3d.html` and `watch3d.js` implement the live Codex panel, multi-particle shockwaves, and 3D podiums for the 3 championship titles (`Nhà khoa học`, `Kẻ sống sót`, `Người đầu tiên`).
6. Requirement R3 and Task 6 require zero external CDN dependencies. All assets are local (`web/vendor/three.min.js`, `GLTFLoader.js`), with no `http://` or `https://` URLs in HTML/JS.

## 3. Caveats
- No external CDNs or build tools are used, maintaining full offline self-containment.
- Procedural Three.js morphology serves as a 100% self-sufficient visualizer that does not require external Meshy GLB downloads to run.

## 4. Conclusion
Milestone 3 (3D Visualizer & Compact Map Experience) has been fully implemented, strictly verified against all project invariants, and passes 100% of test suites.

## 5. Verification Method
- **Specific Test Commands**:
  - `pytest tests/test_spectate.py tests/test_mesh.py -v` (26 passed in 5.40s)
  - `pytest tests/e2e -v` (196 passed in 1.88s)
  - `python scripts/preflight.py` (Passed all environment and model binding checks)
- **Key Files**:
  - `web/watch3d.html`
  - `web/watch3d.js`
  - `net/match.py`
  - `genesis/mesh_prompts.py`

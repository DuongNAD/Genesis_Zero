# Original User Request

## 2026-09-02T17:44:36Z

Genesis Zero là một sandbox nơi mỗi sinh vật mang một tâm trí LLM độc lập chạy trên máy người chơi để khám phá các định luật vật lý ngẫu nhiên ẩn giấu của thế giới. Dự án cần được kiểm tra và xử lý toàn diện mọi lỗi tiềm ẩn, hoàn thiện quy trình cài đặt và khởi chạy 1-chạm (zero-friction setup), đồng thời phát triển và hoàn thiện chế độ hiển thị 3D trực quan sinh động trên bản đồ kích thước vừa phải (gọn gàng, tối ưu góc nhìn, hiển thị rõ đặc điểm hình thái sinh vật và tương tác 3 tầng: nước, cạn, trời) để mang lại trải nghiệm thú vị nhất. Hãy sử dụng một đội ngũ đầy đủ các agent (Full team) để phân tách và giải quyết các mảng công việc.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero
Integrity mode: development

## Requirements

### R1. Kiểm tra toàn diện và Khắc phục lỗi (Codebase Integrity & Bug Fixing)
Rà soát toàn bộ kho mã nguồn (mô phỏng thế giới, server/client, referee chấm điểm Sổ Luật, xử lý mạng, bảo mật hostile probe). Khắc phục triệt để mọi lỗi tiềm ẩn, ngoại lệ biên hoặc xung đột cấu hình, bảo đảm 100% test suite và các kịch bản chạy ván mô phỏng đều hoạt động chính xác và trơn tru.

### R2. Bộ cài đặt và Trình khởi chạy 1-chạm (One-Command Setup & Launcher)
Xây dựng giải pháp cài đặt và khởi chạy tự động hóa hoàn toàn cho người dùng mới trên các môi trường phổ biến (macOS, Linux, Windows). Cung cấp cơ chế tự động kiểm tra/thiết lập môi trường ảo (venv), dependencies, cấu hình preflight tự đề xuất cách khắc phục, và cho phép bắt đầu ván đấu ngay lập tức chỉ với một lệnh duy nhất ở cả hai chế độ: offline (reflex/mock) và kết nối LLM cục bộ (Ollama, llama.cpp, vLLM).

### R3. Phát triển Trình hiển thị 3D & Bản đồ Vừa vặn Thú vị (3D Visualizer & Compact Map Experience)
Phát triển và hoàn thiện giao diện 3D (dựa trên nền tảng Three.js trong `web/watch3d.html` hoặc tương đương) với kích thước bản đồ được cân chỉnh vừa phải (compact, không bị quá rộng loãng, tối ưu bao quát toàn cảnh và hiệu năng). Thể hiện sinh động 3 tầng sinh thái (nước, cạn, trời), hiệu ứng thời tiết/sự kiện luật kích hoạt, hình thái 3D phản ánh đặc điểm sinh học của sinh vật, và bảng Sổ Luật trực quan theo thời gian thực.

## Acceptance Criteria

### Verification & Testing
- [ ] Tất cả các kiểm thử hiện có và mới trong test suite (`pytest`) đều chạy thành công mà không phát sinh bất kỳ lỗi hoặc crash nào.
- [ ] Kịch bản kiểm tra an ninh rò rỉ luật (`make hostile` / `scripts/hostile_client.py`) và bộ kiểm tra môi trường (`make preflight` / `scripts/preflight.py`) đều hoàn thành với kết quả hợp lệ.
- [ ] Chạy thành công một ván mô phỏng mẫu từ đầu đến cuối (`python -m genesis.run` hoặc `make demo`) với việc ghi log và tính điểm luật ẩn chính xác.

### Setup & Usability
- [ ] Có script hoặc lệnh khởi chạy 1-chạm duy nhất có thể thiết lập môi trường và khởi động game mà không yêu cầu cấu hình thủ công phức tạp.
- [ ] Trình khởi chạy có thông báo rõ ràng khi thiếu phụ thuộc hoặc khi chạy ở môi trường không có GPU/LLM cục bộ (tự động fallback về reflex controller hợp lệ).
- [ ] Tài liệu hướng dẫn bắt đầu nhanh (Quickstart) được cập nhật ngắn gọn, chính xác và có thể làm theo thành công trong dưới 3 phút.

### 3D Visualizer & Experience
- [ ] Giao diện 3D Visualizer (`web/watch3d.html` hoặc tương đương) khởi chạy mượt mà trên trình duyệt, camera xoay/zoom trực quan, bản đồ kích thước vừa vặn dễ theo dõi.
- [ ] Thể hiện rõ nét 3 tầng không gian (nước sâu/nông, mặt đất/hang, bầu trời) cùng các sinh vật có hình thái tương ứng với traits của chúng.
- [ ] Quá trình ghi nhận và chấm điểm Sổ Luật (Law Journal) cùng các sự kiện luật ẩn kích hoạt được trực quan hóa sinh động trong không gian 3D.

## 2026-09-03T04:57:00Z

Transform Genesis Zero into an advanced evolutionary simulation sandbox featuring generational genetic mutation, dynamic environmental weather cycles, and an interactive 3D spectator with procedural audio and match timeline replay.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero
Integrity mode: development

## Requirements

### R1. Generational Evolution & Genetic Mutation
Organisms that satisfy reproduction thresholds (e.g., survival duration, high energy, or law discovery achievements) can reproduce offspring. Offspring inherit parental numeric traits and biological features with bounded stochastic mutations, enabling emergent survival adaptations and lineage tracking across successive match epochs.

### R2. Dynamic Environmental System & Weather Phenomena
The simulation world undergoes periodic macro-environmental cycles (such as day/night illumination cycles, toxic spore storms, solar flares, or magnetic shifts) that dynamically modulate terrain passability, resource depletion/growth rates, and creature stamina costs across the grid in a seed-deterministic manner.

### R3. Interactive 3D Spectator & Procedural Audio Experience
Enhance the 3D visualizer (`web/watch3d.html` & `web/watch3d.js`) with an interactive match timeline scrubber (allowing pause, rewind, scrub through historical ticks, and variable playback speed), procedural audio synthesized via the browser Web Audio API for organism actions, weather shifts, and law discoveries, and visual particle cues for active weather phenomena, while strictly preserving zero external CDN dependencies.

### R4. Telemetry Extension & Backward Compatibility
The WebSocket telemetry payload (`/v1/spectate`) must broadcast active environmental states, creature generational lineage metadata, and replay history buffers without breaking existing spectator client interfaces or referee scoring pipelines.

### R5. Comprehensive Verification & Regression Prevention
All new mechanics (evolution, weather cycles, audio/replay controls, and telemetry schema) must be accompanied by programmatic unit and integration tests under `tests/`. The entire test suite must pass with 100% success under `pytest`, and the one-command launcher (`run.sh` / `scripts/launch.py`) must boot the enhanced experience with zero manual configuration.

## Acceptance Criteria

### Evolutionary Mechanics
- [ ] Eligible creatures trigger reproduction when energy/survival conditions are met, producing offspring with mutated traits bounded within valid ranges.
- [ ] Creature telemetry records parent ID, generation index, and inherited trait variances.
- [ ] Extinction and overpopulation caps maintain stable simulation performance across multi-generational runs.

### Environmental Dynamics
- [ ] Simulation engine cycles through weather/environmental phases deterministically according to the world seed.
- [ ] Environmental phases apply observable effects to simulation state (e.g., modified movement costs, visibility, or plant regeneration).
- [ ] Telemetry stream broadcasts the current weather state, cycle progress, and active global modifiers on each tick.

### 3D Spectator & UX
- [ ] Spectator UI provides functional timeline controls: Play/Pause, Fast-Forward (1x, 2x, 5x), and Scrubbing through buffered match ticks.
- [ ] Synthesized procedural sound effects trigger via Web Audio API for movement, law discovery shockwaves, creature death, and weather transitions without external audio files.
- [ ] Visual atmospheric cues (lighting tone, sky color, particle fog/rain) reflect the active weather state in real time.
- [ ] Spectator remains completely operational locally offline with zero external network or CDN calls.

### Quality & Test Infrastructure
- [ ] 100% of tests in `tests/` pass with zero collection errors and zero failures when executed via `pytest`.
- [ ] Launch script (`scripts/launch.py` / `run.sh`) successfully initializes the simulation server, launches the match, and opens the spectator.

## 2026-09-03T16:45:06Z

Xây dựng bản đồ môi trường sinh thái 3D hoàn chỉnh bằng Blender với quy mô vừa phải: bao gồm địa hình đa dạng (núi, đồi, sông, hồ), kết hợp hệ thực vật và động vật sống động với bề mặt mịn màng, chân thực và đầy đủ hoạt ảnh (animation). Cung cấp file nguồn `.blend` hoàn chỉnh và file mô hình tối ưu `.glb` kèm hoạt ảnh.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map
Integrity mode: development

## Requirements

### R1. Cohesive Multi-Biome 3D Terrain & Hydrology
A balanced-scale 3D terrain environment featuring distinct topographic zones: mountain ridges, rolling hills, flat valley floors, and lowlands. Hydrology must include at least one river winding through the terrain and discharging into a lake basin. Surfaces must feature smooth transitions between biomes, elevation-appropriate PBR materials (rock, fertile soil, grassland, sand), and dedicated water surface shaders with realistic transparency and reflectivity.

### R2. Organic Flora & Biome Vegetation
A rich variety of 3D vegetation models (trees, shrubs, ground cover) distributed naturally across appropriate biomes based on elevation and water proximity (e.g., lush trees in lowlands/valleys, alpine trees/shrubs on higher ground, wetland plants along shorelines). All plant meshes must have smooth shading enabled, natural organic textures/materials, and varied rotation/scale distribution.

### R3. Lifelike Fauna with Skeletal Rigging and Fluid Animations
Populate the ecological map with realistic 3D animal models suited to the biomes. Models must feature smooth organic topology (smooth shading, realistic forms) and complete skeletal bone armatures. Each creature must include active, smooth animation action cycles (such as idle/breathing/looking around, walking/running, or grazing) without jerky keyframing or mesh distortion.

### R4. Complete Scene Composition & Dual Deliverables
Assemble the complete ecological diorama inside a self-contained Blender scene (`ecosystem_map.blend`) configured with atmospheric lighting (sun/sky), camera framing, and render settings. In addition to the `.blend` file, export an optimized industry-standard 3D asset (`.glb` / `.gltf` with embedded materials, textures, and animations) ready for game engines or web 3D visualizers.

### R5. Execution & Verification Environment
Use the local Blender environment (`/Applications/Blender.app/Contents/MacOS/Blender`) and Blender Python API (`bpy`) to construct, configure, inspect, and render the scene.

## Acceptance Criteria

### Scene File & Structure
- [ ] Self-contained Blender file `ecosystem_map.blend` is created in `/Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map` and opens without errors or broken links.
- [ ] Scene contains structured collections: `Terrain`, `Water`, `Flora`, `Fauna`, `Lighting`, and `Camera`.

### Terrain & Hydrology
- [ ] Terrain mesh spans a balanced scale (elevation delta >= 15m for hills/mountains, horizontal span between 100m and 500m) with smooth slope transitions.
- [ ] At least one continuous river mesh and at least one lake basin mesh exist, textured with translucent water material.

### Flora & Fauna Quality
- [ ] At least 3 distinct plant/tree species are placed across the map with smooth shading enabled (`use_smooth = True`).
- [ ] At least 2 distinct animal species are present with rigged armatures and active animation actions containing keyframes covering at least idle and locomotion cycles.

### Automated Verification & Export
- [ ] Headless Blender verification script executes cleanly against `ecosystem_map.blend` with zero errors, asserting all collections, objects, materials, and animations are present.
- [ ] Exported `.glb` file exists in the working directory (size > 100 KB) and contains mesh geometries, materials, and embedded animations.
- [ ] Headless render produces at least one high-resolution preview image (`render_preview.png`) showing the illuminated scene from the main camera without missing shader errors.

## 2026-09-03T17:21:58Z

Xây dựng bản đồ môi trường sinh thái 3D dạng khối diorama cắt lớp địa chất (geological cutaway diorama block) trong Blender với góc nhìn thứ 3 (isometric/third-person diorama framing), tích hợp 4 hệ sinh thái hoàn chỉnh (Núi cao tuyết phủ, Đồng bằng & Rừng thung lũng, Thủy sinh ven bờ & Rạn san hô hạ lưu, Hang động ngầm Karst phát quang sinh học). Hệ thống bao gồm mạng lưới sông suối thác nước đổ vào hồ và vịnh biển, thực vật phân bổ bằng Geometry Nodes, động vật chân thực có khung xương (rigging) và bộ animation sinh động, cùng vật liệu triplanar/slope shader và water volume shader chân thực.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero/assets/blender_map
Integrity mode: development

## Reference Images
- ![Dự án mô phỏng bộ các mặt cắt map chi tiết](/Users/duongnad/.gemini/antigravity/brain/e05421f3-31e6-4864-bd1a-a1de3f1a7a0d/media_1788455668720.jpg)
- ![Bản đồ phân tầng sinh thái tổng thể](/Users/duongnad/.gemini/antigravity/brain/e05421f3-31e6-4864-bd1a-a1de3f1a7a0d/media_1788455686621.jpg)
- ![Diorama 3D Viewport mẫu trong Blender](/Users/duongnad/.gemini/antigravity/brain/e05421f3-31e6-4864-bd1a-a1de3f1a7a0d/media_1788455807967.jpg)

## Requirements

### R1. Diorama Block Base & Multi-Tier Geomorphology
Construct the 3D world as an isometric diorama cutaway block (cube slice showing stratified underground geological cross-sections on vertical walls: topsoil, subsoil, bedrock). Geomorphology must incorporate:
- Sharp alpine mountain peaks with weathered scree/talus slopes, rock strata cliffs, and snow caps.
- Gentle lowland plains and valley floors with fertile grasslands and alluvial marshes.
- Continuous multi-tier hydrology: alpine streams cascading down rocky waterfalls, converging into a meandering valley river, filling a deep central freshwater lake with shoreline sand, and discharging into a lower coastal marine bay with beaches and cliff cutaways.
- A subterranean karst cave system embedded inside the diorama block beneath the mountain/river, featuring natural cave entrances, arched cave ceilings with stalactites and stalagmites, and an underground pool/stream.

### R2. 4-Zone Biome Distribution & Procedural Flora (Geometry Nodes)
Implement procedural scatter using Blender Geometry Nodes with mathematical masks based on Altitude (Z), Slope (Normal Z), and Water Proximity:
- **Alpine Biome (High elevation, steep > 45°):** Cold-tolerant tussock grass, rock-clinging lichens/moss, and hardy sub-alpine dwarf conifers/pines.
- **Lowland & Forest Biome (Low/mid elevation, slope < 20°):** Multi-tier forest consisting of broadleaf canopy trees, understory flowering shrubs, ferns, and lush meadow grass.
- **Aquatic & Riparian Biome (Water margins, riverbanks, lake, coastal bay):** Shore reeds, water lilies, submerged aquatic weeds, and shallow-water coastal coral reefs with marine greenery in the lower bay.
- **Subterranean Cave Biome (Underground dark cavity):** Clusters of bioluminescent mushrooms/fungi emitting gentle ambient glow, and shade-tolerant cave moss near light portals.
All plant instances must use smooth shading and efficient point instancing (`Instance on Points`) with scale/rotation variation.

### R3. Lifelike Multi-Biome Fauna with Rigging & Organic Animations
Populate all 4 biomes with smooth, anatomically proportioned 3D creature models equipped with skeletal armatures and fluid action animation cycles:
- **Alpine:** Mountain goat/chamois traversing cliff edges (locomotion cycle) and soaring eagle/raptor circling overhead (flight gliding cycle).
- **Forest & Plains:** Herbivore (deer/stag) with idle breathing/looking and walking cycles, plus small forest-floor rodents or birds.
- **Aquatic & Shore:** Benthic and swimming freshwater fish in lake/river, coastal marine life (fish/sea turtle/crabs in coral bay), and amphibians (frogs) or dragonflies along shorelines.
- **Cave:** Roosting and fluttering cave bats clinging to cavern ceiling, and blind cave salamanders/fish in subterranean pools.
All fauna meshes must have smooth normals/shading without tearing or rigid deformation during bone movement.

### R4. Physically-Based Shading, Slope Blending & Water Shaders
- **Terrain Shader:** Slope-aware procedural/triplanar blending transitioning between rock strata on steep vertical cliffs, weathered dirt/scree on intermediate slopes, lush grass/soil on flats, snow on high peaks, and sandy beach along shorelines. Cutaway block sides must display distinct geological strata banding.
- **Water Shader:** Realistic water surface using transmission/roughness and Volume Absorption for depth color gradients (deep sapphire blue in lake/ocean, emerald shallow water), coupled with foam/edge detection along shorelines, waterfalls, and river rocks.
- **Cave & Bioluminescence:** Emissive shaders for cave fungi and underground bioluminescent water giving off surreal soft lighting in dark caverns.

### R5. 3rd-Person Isometric Framing & Dual Deliverables
- Configure primary 3rd-person isometric/orbital camera framing at 3/4 perspective looking down onto the diorama block (matching the user's reference screenshots 1 & 3), illuminated by atmospheric directional sun and sky skylight with soft ambient occlusion.
- Save the master Blender project as `ecosystem_map.blend` in the working directory with organized collections (`Diorama_Block`, `Terrain`, `Hydrology`, `Subterranean_Cave`, `Flora_Instances`, `Fauna_Rigged`, `Lighting`, `Cameras`).
- Export an optimized industry-standard `.glb` package containing all visible meshes, materials, and embedded animations for real-time web/game spectator engines.

### R6. Automated Verification & Inspection Pipeline
Implement and execute a comprehensive Python verification script (`verify_ecosystem.py`) using headless Blender (`/Applications/Blender.app/Contents/MacOS/Blender`) to validate diorama geometry, cave hollow cavities, multi-biome flora instancing, armature action keyframes, and headless multi-angle renders (including 3/4 isometric preview and cross-section).

## Acceptance Criteria

### Diorama Geometry & Hydrology
- [ ] Diorama cutaway base block is present with visible vertical geological strata cross-sections.
- [ ] Terrain features distinct elevation tiers (snow-capped mountain peaks >= 20m delta, rolling hills, flat plains).
- [ ] Hydrology connects alpine waterfall -> meandering river -> central freshwater lake -> lower coastal basin.
- [ ] Subterranean cave network exists beneath terrain with at least one cave entrance, arched cavern room, stalactites/stalagmites, and underground water pool.

### Biomes & Geometry Nodes Flora
- [ ] Geometry Nodes scatter setup distributes flora based on altitude, slope, and water proximity across 4 distinct biomes (Alpine, Lowland/Forest, Aquatic/Riparian, Cave).
- [ ] At least 4 distinct plant/fungi types are instanced (Pines, Broadleaf trees, Shore reeds/water plants, Bioluminescent cave mushrooms).
- [ ] All vegetation instances have smooth shading enabled and natural random rotation/scale distribution.

### Rigged & Animated Fauna
- [ ] At least 4 distinct animal species representing the biomes are present with bone armatures (e.g. Deer, Mountain Goat/Eagle, Fish/Frog, Cave Bat).
- [ ] Each creature has active animation actions with keyframes (idle, locomotion, flight, or swimming) executing smoothly without mesh artifacts.

### Shaders, Render & Deliverables
- [ ] Slope-blended terrain material automatically maps rock onto cliffs (>40°) and grass/soil onto flat ground (<25°).
- [ ] Water shader displays depth-based absorption and visible shoreline transition.
- [ ] Primary camera is positioned in 3rd-person 3/4 isometric diorama framing.
- [ ] Headless Blender script `verify_ecosystem.py` passes 100% of topological, collection, and animation assertions.
- [ ] Master `.blend` file and exported `.glb` file (> 200 KB) exist and load cleanly.
- [ ] High-resolution render preview `render_preview.png` generated showing the complete illuminated diorama.

## 2026-09-04T03:13:33Z

Xây dựng và tái thiết lập toàn diện mô hình map 3D diorama chất lượng cao trong Blender tại `models/genesis_diorama_master.blend` cho Genesis Zero với cấu trúc đảo địa chất nguyên khối (diorama slab), mạng lưới thủy văn tự nhiên (thác nước, sông uốn khúc, hồ sâu trung tâm), hệ thống hang động ngầm karst có thạch nhũ và hồ phát quang, hệ sinh thái phân tầng tự động bằng Geometry Nodes, PBR triplanar/volume shader, camera rig 24 góc kiểm tra thị giác, và xuất bản đồ GLB/GLTF cho 3D Spectator.

Working directory: `/Users/duongnad/Documents/project/Genesis_Zero`
Integrity mode: `development`

## Reference Materials
- 4 ảnh concept mẫu từ người dùng:
  1. Diorama đa quần xã 4 mùa/địa hình có lát cắt địa chất thành khối.
  2. Diorama thung lũng tuyết, sông uốn lượn, hồ trung tâm, thác nước và rạn san hô dưới nước.
  3. Bản đồ quy hoạch chuyển tiếp sinh thái (Sa mạc → Savanna → Núi đá tuyết → Hồ nước → Rừng nhiệt đới).
  4. Bộ 24 góc phân tích kỹ thuật: Mặt cắt A-A/B-B, Wireframe, Elevation Heatmap, Slope Analysis, Phân bố thực vật, Giả lập ngày/đêm và thời tiết.

## Requirements

### R1. Khối Địa Chất Diorama Nguyên Khối & Địa Hình Đa Tầng (Diorama Slab & Geomorphology)
- Tạo khối đế diorama đảo nổi (diorama island block) có vách cắt phẳng (sheared cross-section) lộ các tầng trầm tích và đá nền (strata rock layers).
- Đỉnh núi tuyết đá nhọn với sườn dốc phong hóa tự nhiên và triền đá vụn (scree/talus slopes) chân núi.
- Vùng lòng chảo thung lũng thoải màu mỡ chuyển tiếp mượt mà sang bãi cát và đầm lầy phù sa ven nguồn nước.
- Hệ thống hang động ngầm karst (subterranean cave system) nằm dưới lòng khối địa hình với vòm hang, nhũ đá (stalactites), măng đá (stalagmites) và lòng suối/hồ ngầm.

### R2. Mạng Lưới Thủy Văn Tự Nhiên & Liên Tục (Hydrology Network)
- Dòng suối núi cao chảy men theo hẻm núi, hội tụ thành các con thác nhiều tầng đổ xuống thung lũng.
- Sông chính uốn lượn (meandering river) mềm mại theo đường cong spline, độ sâu lòng sông và bờ thoải tự nhiên.
- Hồ nước ngọt trung tâm sâu với các bậc thềm ven hồ, khóm hoa súng/bèo sen, lau sậy và bãi đá cuội ven bờ.

### R3. Hệ Sinh Thái Procedural Bằng Geometry Nodes (Procedural Biome Scatter)
- Thiết lập hệ thống phân bổ thảm thực vật & đá sỏi hoàn toàn bằng Geometry Nodes dựa trên 3 mask toán học:
  1. **Độ cao (Altitude $Z$)**: Phân tầng tuyết/đá cao, rừng ôn đới thung lũng, và ven nước.
  2. **Độ dốc (Slope từ Normal $Z$)**: Vách dốc >45° chỉ cho phép rêu/đá vụn; sườn thoải <20° phủ cây gỗ tán rộng và tầng cỏ dày.
  3. **Khoảng cách nguồn nước (Proximity to Water Curve)**: Tập trung lau sậy, dương xỉ ẩm và bèo ven sông hồ.
- 4 Quần xã đặc trưng:
  - *Alpine*: Thông tuyết lùn, cỏ bụi lạnh, rêu đá.
  - *Thung lũng & Rừng*: Cây tán rộng, cây bụi, thảm hoa dại và dương xỉ.
  - *Thủy sinh*: Bèo, hoa súng, lau sậy, rong rêu.
  - *Hang động*: Nấm phát quang sinh học dịu nhẹ, rêu chịu tối ở cửa hang.
- Tối ưu hiệu năng: Instance on Points, Frustum Culling theo camera góc nhìn thứ 3 và LOD distance culling.

### R4. Shader & Vật Liệu PBR Tự Nhiên (Triplanar & Water Volumetrics)
- Shader địa hình Triplanar/Box mapping tự động blend giữa kết cấu vách đá dốc và cỏ/đất bằng phẳng.
- Shader nước mặt có chiều sâu hấp thụ ánh sáng (Volume Absorption), độ trong trẻo biến thiên theo độ sâu và viền bọt nước (shore foam masking).
- Shader phát quang sinh học (bioluminescence emission) cho nấm hang động ngầm.

### R5. Hệ Thống Camera Rig 24 Góc & Pipeline Xuất GLTF Cho Game (Verification & Export)
- Thiết lập Camera Rig 24 góc quan sát tự động (bao gồm 4 góc Isometric, Top-down orthographic, các mặt bên North/East/South/West, mặt cắt lát ngang A-A, B-B, và các góc cận cảnh hồ/thác/rừng/hang động).
- Tích hợp pipeline tự động xuất ra file `models/genesis_diorama_master.blend` và phiên bản tối ưu `models/genesis_diorama.glb` (hoặc `.gltf`) tương thích với 3D Spectator của Genesis Zero (`web/watch3d.html`).

## Acceptance Criteria

### Tính Toàn Vẹn Cấu Trúc & Địa Hình
- [ ] File `models/genesis_diorama_master.blend` được tạo hoàn chỉnh, cấu trúc Collection phân cấp mạch lạc (`Terrain`, `Hydrology`, `Caves`, `Biome_Scatter`, `Camera_Rig_24`).
- [ ] Khối đế diorama có mặt cắt địa chất phẳng lộ tầng đá và đất rõ ràng.
- [ ] Hệ thống hang ngầm karst có lối thông tự nhiên và không gian vòm hang hoàn chỉnh bên dưới base mesh.
- [ ] Mạng lưới suối - thác - sông - hồ kết nối thủy văn logic, không bị đứt gãy hình học.

### Cơ Chế Geometry Nodes & Tối Ưu Phân Bổ
- [ ] Geometry Nodes scatter áp dụng đúng logic phân bổ: Không có cây mọc trên vách đá thẳng đứng hoặc trong lòng suối chảy xiết.
- [ ] 100% tài sản scatter sử dụng `Instance on Points` đảm bảo FPS mượt mà trong viewport Blender.
- [ ] Không có hiện tượng cây cối hoặc đá bị trôi lơ lửng trên không hay ngập lút dưới đất.

### Kiểm Tra Thị Giác Đa Góc Độ (Multi-Angle Vision)
- [ ] Script kiểm tra chạy trích xuất thành công bộ ảnh chụp các góc quan sát chính (Top-Down, 4 góc Iso, Cận cảnh hồ, Thác nước, Hang động).
- [ ] Ảnh chụp xác nhận shader nước có độ sâu và gradient màu từ xanh ngọc ven bờ đến xanh thẫm đáy hồ.

### Xuất Bản Đồ Sạch Cho Web Spectator
- [ ] File xuất `models/genesis_diorama.glb` được tạo thành công, dung lượng hợp lý, kiểm tra load được trên Three.js / web visualizer mà không gặp lỗi thiếu texture.

## 2026-09-04T17:31:35Z

Xây dựng hệ thống tự động nghiên cứu cơ sở dữ liệu thực vật học (POWO Kew, WFO, GBIF, CoL, vncreatures), tạo ảnh concept đa góc nhìn (Turnaround sheet gồm 4 góc: 3/4 Front, Front, Side, Top-Down), dựng mô hình 3D thực vật tả thực (Photorealistic PBR) bằng Blender (xuất `.blend` và `.glb`), và cập nhật đồng bộ vào Master Catalog cùng Web Viewer 3D của Genesis Zero.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero
Integrity mode: development

## Requirements

### R1. Thu thập & Chuẩn hóa Dữ liệu Thực vật học (Botanical Taxonomic Research)
Truy vấn và thẩm định danh pháp thực vật học chuẩn quốc tế (APG IV) từ các cơ sở dữ liệu mở lớn (POWO Kew, World Flora Online, GBIF, Catalogue of Life, vncreatures) cho các loài thực vật mục tiêu (ưu tiên đợt 1 gồm 5-10 loài tiêu biểu trải rộng các tầng sinh thái: Cây đại thụ, Cây bụi/Dương xỉ, Thảo mộc/Hoa dại, Thủy sinh/Đầm lầy, Sa mạc/Mọng nước, và Cây đặc hữu). Trích xuất đầy đủ: Tên khoa học, Họ thực vật (Family), Kích thước thực tế (Chiều cao x Tán), Tầng sinh thái, Tọa độ sinh cảnh, và Đặc điểm giải phẫu học chi tiết.

### R2. Tạo Ảnh Tham Chiếu Đa Góc Nhìn Chuẩn Xác (Turnaround Concept Sheets)
Tạo bản vẽ turnaround concept đa góc nhìn chất lượng cao cho từng loài thực vật mục tiêu, tuân thủ bố cục chuẩn hóa:
- Nửa trên: Phối cảnh tổng thể 3/4 chính diện (Main Perspective View 3/4 Front).
- Nửa dưới: 3 hình chiếu trực giao rõ ràng (Front Orthographic View, Side Orthographic View, Top-Down Orthographic View).
Đảm bảo độ chính xác giải phẫu thực vật, chi tiết tán lá, thân nhánh và hoa/quả phục vụ đối chiếu trực quan khi dựng hình 3D. Lưu trữ chuẩn hóa tại `web/flora_images/`.

### R3. Dựng Mô Hình 3D Thực Vật Tả Thực Trong Blender (Blender 3D Modeling & PBR)
Dựng mô hình 3D cho các loài thực vật với chất lượng tả thực cao (Photorealistic / Scan-Quality):
- Cấu trúc lưới sạch (Clean quad-dominant manifold topology), smooth shading toàn diện.
- Vật liệu PBR chuẩn sinh học: Tán lá và cánh hoa có tán xạ dưới bề mặt (Subsurface Scattering - SSS) thấu quang, vỏ cây có chi tiết rãnh nứt vi mô (Procedural bump/micro-displacement).
- Xuất song song: File gốc Blender `.blend` lưu tại `assets/flora/<category>/` và file chuẩn runtime `.glb` (glTF 2.0) nhúng texture PBR tối ưu.

### R4. Cập Nhật Đồng Bộ Danh Mục Sinh Vật & Trình Xem Thực Vật 3D (Catalog & Web Viewer)
- Cập nhật Master Catalog `docs/flora/README.md` và các file chi tiết loài tại `docs/flora/species/<slug>.md` với siêu dữ liệu khoa học, link ảnh turnaround, link tải `.blend` và `.glb`.
- Tích hợp vào Trình xem 3D tương tác `web/flora_viewer.html` và `web/flora_models_data.js`: hiển thị badge "4 Góc 📷", hỗ trợ modal phóng to ảnh turnaround đa góc và xem mô hình 3D xoay 360° theo thời gian thực.

### R5. Cơ Chế Kiểm Chuẩn Tự Động (Automated Verification)
Xây dựng kịch bản kiểm thử tự động (Python/pytest) để thẩm định độc lập:
- Kiểm tra tính toàn vẹn của siêu dữ liệu thực vật học.
- Kiểm tra sự tồn tại và kích thước hợp lệ của tất cả file ảnh turnaround (`.jpg`/`.png`), file mô hình `.blend`, và file `.glb`.
- Thẩm định file `.glb` hợp lệ theo đặc tả glTF 2.0 (không lỗi lưới, không thiếu texture).
- Kiểm tra tính đồng bộ của dữ liệu hiển thị trên `web/flora_viewer.html`.

## Acceptance Criteria

### 1. Dữ Liệu & Danh Pháp Khoa Học
- [ ] 100% các loài trong đợt triển khai có đầy đủ tên khoa học, họ thực vật, kích thước hình thái và mã tra cứu đối chiếu từ POWO Kew, GBIF hoặc CoL.
- [ ] Mỗi loài có tài liệu đặc tả độc lập tại `docs/flora/species/<slug>.md` và được ghi nhận trong bảng tổng hợp `docs/flora/README.md`.

### 2. Ảnh Tham Chiếu Đa Góc Nhìn (Turnaround Sheets)
- [ ] Mỗi loài mục tiêu đều có file ảnh turnaround sheet được lưu tại `web/flora_images/<species_slug>_turnaround.jpg` (hoặc `.png`).
- [ ] Ảnh turnaround hiển thị đầy đủ 4 góc nhìn chuẩn: 3/4 Perspective, Front Orthographic, Side Orthographic, Top-Down Orthographic.

### 3. Mô Hình 3D Blender & File glTF
- [ ] Mỗi loài có file `.blend` gốc tại `assets/flora/<category>/<species_slug>.blend` với hệ thống vật liệu PBR Principled BSDF hoàn chỉnh.
- [ ] Mỗi loài có file `.glb` tại `assets/flora/<category>/<species_slug>.glb` kích thước > 0 bytes, mở được trên Three.js / web viewer.
- [ ] Mô hình có vật liệu tả thực, áp dụng Subsurface Scattering (SSS) trên tán lá/cánh hoa.

### 4. Tích Hợp Web Viewer & Catalog
- [ ] `web/flora_viewer.html` có thẻ thông tin cho từng loài với badge `4 Góc 📷`.
- [ ] Click nút "Bản vẽ 4 mặt" trên giao diện web mở đúng ảnh turnaround sheet của loài đó trong modal.
- [ ] Mô hình 3D tải và xoay 360° trơn tru trong viewport Three.js của web viewer.

### 5. Kiểm Thử Khách Quan (Programmatic Verification)
- [ ] Script kiểm thử tự động (vd: `python scripts/verify_flora_pipeline.py` hoặc `pytest tests/test_flora_assets.py`) chạy hoàn tất với mã thoát 0 (Exit Code 0).
- [ ] Báo cáo kiểm thử xác nhận 100% tài nguyên (metadata, ảnh turnaround, `.blend`, `.glb`) đều đạt chuẩn chất lượng.

## 2026-09-05T05:16:35Z

Tái thiết kế và nâng cấp toàn diện hệ sinh thái sinh vật cốt lõi trong Genesis Zero đạt chất lượng tả thực cao (Photorealistic / Scan-Quality), cấu trúc giải phẫu học hữu cơ mượt mà, vật liệu PBR sinh học chi tiết (vảy sừng, lông mao, màng da thấu quang, mắt ướt phản quang), gắn bộ xương Rigging Armature phân cấp hoàn chỉnh và tạo trọn bộ 8 animation chuyển động sống động chuẩn Game Engine, kèm bản vẽ concept Turnaround 4 góc nhìn và Trình xem Sinh vật 3D Web chuyên dụng.

Working directory: /Users/duongnad/Documents/project/Genesis_Zero
Integrity mode: development

## Requirements

### R1. Tái Thiết Kế Hình Thái Học & Dựng Hình 3D Tả Thực (Photorealistic Creature Anatomy)
Dựng lại toàn diện các loài sinh vật cốt lõi của Genesis Zero bao gồm:
- **Tầng Cạn (Land)**: Thằn lằn cát L1 (*Sand Skink*), Chồn tuyết L2 (*Snow Ferret*), Dê sừng núi L3 (*Alpine Ibex*), Thỏ đồng cỏ L4 (*Meadow Hare*), Cá sấu đầm lầy L5 (*Marsh Croc*).
- **Tầng Nước (Water)**: Cá săn mồi biển sâu W1 (*Abyssal Hunter* / *Leviathan*).
- **Tầng Trời (Air)**: Đại bàng săn mồi bầu trời A1 (*Storm Eagle*).
- **Sinh Vật Đặc Thù & Tiến Hóa**: Nhện khổng lồ nhiều chân (*Giant Tarantula*), Sentinel cơ khí sinh học bọc giáp (*Armored Sentinel*), Quái thú săn mồi tiến hóa Apex (*L1_Evo / Carnivore Apex*).
Đảm bảo giải phẫu học hữu cơ tự nhiên, cấu trúc cơ bắp, đầu, hàm răng, móng vuốt và đuôi chi tiết, loại bỏ hoàn toàn các khối low-poly thô sơ. Lưới BMesh chuẩn manifold: 0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading.

### R2. Bộ Xương Rigging & Trọn Bộ 8 Animations Chuẩn Game Engine (Skeletal Rig & 8 Action Clips)
Gắn bộ xương Rigging Armature phân cấp chuẩn công nghiệp (Root, Pelvis, Spine, Chest, Neck, Head, Jaw, Tail, Limbs, Paws/Claws, Wings/Fins) và tạo trọn bộ 8 animations chuyển động tự nhiên cho từng loài:
1. `Idle_Normal`: Thở phập phồng tự nhiên, chớp mắt, đảo đầu quan sát.
2. `Idle_Alert`: Cảnh giác cao độ, ngẩng đầu nghe ngóng, tai/giác quan xoay hướng âm thanh.
3. `Walk`: Dáng đi tuần tra tự nhiên, nhịp bước chân mượt mà, cột sống uốn lượn hữu cơ.
4. `Run`: Phi nước đại săn mồi hoặc trốn chạy với nhịp co giãn cơ thể tốc độ cao.
5. `Attack`: Đòn tấn công uy lực (vồ mồi, đớp cắn chớp nhoáng, vung móng vuốt hoặc quất đuôi).
6. `Hurt_Defend`: Phản xạ chịu đòn đau đớn, giật lùi, co cụm cơ thể hoặc giơ giáp phòng vệ.
7. `Eat`: Cúi đầu gặm thức ăn / xé mồi, hàm nhai cử động nhịp nhàng.
8. `Death`: Trụy gối, gục ngã đổ sụp xuống đất một cách tự nhiên.
Tất cả animation clips phải được bake hoàn chỉnh vào NLA Tracks trong file glTF 2.0 (`.glb`) để game engine và Three.js nạp và phát trơn tru.

### R3. Vật Liệu PBR Chuẩn Sinh Học (Subsurface Scattering & Organic Shaders)
Thiết lập shader Principled BSDF chuyên sâu với:
- **Tán xạ dưới da (Subsurface Scattering - SSS)**: Cho tai, mũi, màng da, cánh và các mô mềm.
- **Độ nhám và vi nếp nhăn (Roughness & Bump maps)**: Tạo độ sần sùi của lớp biểu bì da gai, rãnh sừng, vi mô lông mao hoặc vảy xếp lớp.
- **Mắt sinh động**: Lớp giác mạc trong suốt có độ phản xạ gương (clearcoat / specular) và con ngươi sâu thẳm sống động.

### R4. Bản Vẽ Concept Turnaround 4 Góc Nhìn (4-Angle Concept Turnaround Sheets)
Render và tổng hợp bản vẽ tham chiếu mỹ thuật 4 góc nhìn chuẩn mực cho từng loài sinh vật (lưu tại `web/creature_images/<species>_turnaround.jpg` và `docs/creatures/images/`):
- **Phần trên**: Phối cảnh 3/4 chính diện (Perspective 3/4 Hero View).
- **Phần dưới**: 3 hình chiếu trực giao rõ nét gồm Mặt trước (*Front Orthographic*), Mặt bên (*Side Orthographic*), và Mặt trên đỉnh (*Top-Down Orthographic*).

### R5. Trình Xem Sinh Vật 3D Chuyên Dụng Tương Tác (Interactive 3D Creature Viewer)
Xây dựng hoặc nâng cấp giao diện Web Viewer chuyên dụng cho sinh vật (`web/creature_viewer.html`):
- Cho phép chọn nhanh giữa các loài sinh vật qua thanh danh mục trực quan.
- Bảng điều khiển Animation: Nút chuyển đổi mượt mà giữa 8 animation clips (`Idle_Normal`, `Walk`, `Run`, `Attack`, v.v.) kèm thanh điều chỉnh tốc độ playback (0.5x, 1.0x, 2.0x).
- Tùy chọn hiển thị Khung xương Skeleton (Armature Visualizer overlay) để kiểm tra các khớp nối.
- Bảng tra cứu thuộc tính sinh học (Traits: Brain, Speed, Armor, Attack, Sense, Stomach) và đặc điểm tiến hóa (Features).
- Nút phóng to bản vẽ Concept Turnaround 4 góc nhìn trong modal chất lượng cao.
- Cơ chế Offline Zero-CORS: Nhúng base64 models hoặc tải mượt mà trên môi trường máy chủ cục bộ.

### R6. Kịch Bản Kiểm Chuẩn Tự Động (Automated Verification Suite)
Viết kịch bản kiểm thử độc lập (`scripts/verify_creatures_pipeline.py` và `pytest tests/test_creature_assets.py`):
- Kiểm tra tính hợp lệ và kích thước file `.blend` và `.glb` cho 100% sinh vật mục tiêu.
- Thẩm định cấu trúc file `.glb` theo đặc tả glTF 2.0: Có chứa đối tượng Armature/Skinning và đủ 8 Animation Tracks hợp lệ (tên track, sampler, keyframe channels > 0).
- Kiểm tra độ sạch của lưới BMesh qua Blender headless: 0 loose vertices, 0 incontiguous edges, 0 ngons, 100% smooth shading.
- Kiểm tra sự tồn tại và tính hợp lệ của tất cả ảnh Turnaround 4 góc nhìn (JPEG SOI/EOI markers, kích thước chuẩn).
- Kiểm tra tính đồng bộ của dữ liệu hiển thị trên Web Viewer.

## Acceptance Criteria

### 1. Mô Hình 3D & Giải Phẫu Học
- [ ] Mỗi loài sinh vật mục tiêu có file `.blend` gốc tại `assets/creatures/<species>.blend` và file `.glb` tại `assets/creatures/<species>.glb`.
- [ ] Lưới BMesh của 100% sinh vật đạt chuẩn sạch: 0 loose vertices, 0 incontiguous edges, 0 ngons (>4 đỉnh), 100% smooth shading.
- [ ] Bề mặt có vật liệu PBR sinh thái chân thực (SSS cho mô mềm, bump cho vảy sừng/lớp biểu bì, mắt có độ bóng gương).

### 2. Khung Xương & Bộ Chuyển Động (Rigging & 8 Animations)
- [ ] 100% sinh vật có khung xương Armature phân cấp chuẩn gắn skin weights hợp lý, không bị lỗi xoắn vặn hay rách lưới khi chuyển động.
- [ ] Mỗi file `.glb` chứa tối thiểu 8 animation tracks được đặt tên chuẩn xác (`Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death`).
- [ ] Các chuyển động phát mượt mà, chu kỳ lặp (loop) tự nhiên không bị giật lag khung hình.

### 3. Bản Vẽ Tham Chiếu Mỹ Thuật (Turnaround Sheets)
- [ ] 100% sinh vật có file ảnh turnaround tại `web/creature_images/<species>_turnaround.jpg` và `docs/creatures/images/<species>_turnaround.jpg`.
- [ ] Ảnh hiển thị đủ 4 góc nhìn chuẩn: 3/4 Perspective, Front Orthographic, Side Orthographic, Top-Down Orthographic.

### 4. Trình Xem Web 3D Tương Tác
- [ ] `web/creature_viewer.html` nạp và hiển thị 3D mượt mà cho 100% sinh vật.
- [ ] Bộ nút chọn animation chuyển đổi realtime tức thì các hành động.
- [ ] Tích hợp tính năng bật/tắt hiển thị xương (Skeleton toggle) và xem bản vẽ 4 góc trong modal.

### 5. Kiểm Thử Tự Động (Programmatic Verification)
- [ ] Kịch bản `python3 scripts/verify_creatures_pipeline.py` chạy hoàn tất với 100% tiêu chí đạt chuẩn (Exit Code 0).
- [ ] Test suite `pytest tests/test_creature_assets.py` vượt qua 100% các bài kiểm tra tự động.

## 2026-09-10T03:22:50Z

# Teamwork Project Prompt — Draft

> Status: Launched — Delegated to teamwork_preview
> Goal: Execute multi-agent refactor & implementation
> Requested team: Full team (Software Architect, Graphics/Simulation Engineer, AI Pipeline Integrator, QA Engineer)

Toàn diện tái cấu trúc và hiện đại hóa engine `terra_forge` (Python/Blender/Headless) để tương thích 100% với hệ sinh thái mô phỏng sự sống `Anima-Engine` (Rust Bevy ECS + React Three.js), tích hợp dịch vụ tạo hình 3D AI `Meshy AI` với cơ chế Local Asset Vault/Cache/LOD, và thiết lập bối cảnh "Thiên nhiên Nguyên thủy Sơ khai" (Primordial Nature) tuyệt đối không có dấu vết nhân tạo.

Working directory: E:\tool\mcp\terra_forge
Target directory: e:\Project\03_Engines_Simulation\Anima-Engine
Integrity mode: benchmark
Meshy API Key: msy_yFOKAOFOk9yjKUcwuk9rlkb0lTyuWMI0sT1T

## Requirements

### R1. Chuẩn hóa Tầng Dữ liệu & Khử phụ thuộc Runtime (Data Contract & Headless Export)
- Hiện thực mô-đun thuần Python/NumPy (không phụ thuộc `bpy`) đọc/ghi chuẩn binary `WorldArtifact` v2 (`ANMW`, FNV-1a 32-bit checksum, kích thước chuẩn 256x256, canonical scale 200.0, world bounds [-100, 100], elevation [0, 10]).
- Xuất đầy đủ 5 tầng trường dữ liệu song song: `elevation` (f32), `moisture` (f32), `temperature` (f32), `flow` (f32), `biome` (u8 chuẩn hóa 22 canonical biomes của Anima-Engine).
- Sinh tự động `map_manifest.json` theo đúng `map_manifest.schema.json` của Anima-Engine.
- Loại bỏ bắt buộc diorama slab (chân đế đóng hộp), hỗ trợ chế độ xuất địa hình liên tục vô hạn/nối ghép (Continuous Open World Heightfield & Chunked Mesh).
- Hỗ trợ xuất trực tiếp mô hình địa hình sang GLB thời gian thực và binary heightfield mà không cần khởi động Blender GUI.

### R2. Tích hợp Đường ống Meshy AI Chuyên sâu & Kho Asset Nội bộ (Meshy AI Pipeline & Asset Vault)
- Xây dựng HTTP Client bất đồng bộ với cơ chế retry, rate limit và quản lý API Key an toàn cho Meshy v2 API (`https://api.meshy.ai/openapi/v2/text-to-3d`).
- Thiết lập hệ thống `Local Asset Vault & Cache` lưu trữ định danh theo hash (SHA-256 của prompt + seed + tham số), tránh gọi API trùng lặp, lưu trữ kèm metadata sinh học và thumbnail.
- Tự động hóa bộ chuẩn hóa hình học cho asset từ Meshy:
  + Dời tâm Pivot Point về đáy vật thể (`min_y = 0` / `min_z = 0`) để bám sát mặt địa hình, chống lún/lơ lửng.
  + Chuẩn hóa kích thước thực tế theo hệ mét (Metric scaling).
  + Tự động tạo các cấp độ chi tiết LOD (LOD0 ~10k, LOD1 ~2k, LOD2 ~300 tris / billboard).
  + Tự động sinh khối bao va chạm (Collision Primitives: Cylinder/AABB/Convex Hull).

### R3. Ràng buộc Bối cảnh Thiên nhiên Nguyên thủy & Phân tầng Sinh thái Hữu cơ (Primordial Nature & Organic Ecology)
- Động cơ sinh Prompt thông minh cho Meshy AI loại bỏ triệt để thiên kiến con người (Human Bias): áp dụng kỹ thuật positive descriptor chặt chẽ (cây cổ thụ ngàn năm, thân gỗ mục tự nhiên gãy đổ do bão, rễ bám khe đá, đá cuội bào mòn dòng chảy, địa y bám vách ẩm, tuyệt đối không vết cưa, đường mòn, phế tích).
- Thay thế toàn bộ các hình khối thô sơ trong `asset_fetcher.py` bằng các mẫu sinh học chân thực hoặc asset chất lượng cao từ Vault.
- Phân tầng sinh thái hữu cơ theo địa mạo (Ecological Stratification): rễ cây ăn sâu vào khe nứt địa chất, thân cây mục định hướng theo sườn dốc/dòng nước lũ, bãi cuội lòng suối tập trung theo trường vận tốc dòng chảy (`flow`), rêu mọc ưu tiên sườn dốc khuất nắng và độ ẩm cao.

### R4. Đồng bộ Ma trận Phân tán GPU Instancing & Bản đồ Cản trở Điều hướng (Instancing & Navigation Sync)
- Chuyển đổi phương pháp phân tán Geometry Nodes của Blender thành dữ liệu ma trận biến đổi thực thể GPU (`GPU Instancing Matrices: position, rotation quaternion, scale`) có thể nạp trực tiếp vào Three.js (`WorldVegetation.tsx`) và Bevy ECS với 1 draw call cho mỗi chủng loại.
- Sinh bản đồ cản trở điều hướng (Obstacle Grid & NavMesh Reachability) đồng bộ hoàn toàn giữa bán kính vật lý của cây cối/tảng đá với hệ thống di chuyển của sinh vật trong Anima-Engine (`navmeshCoverage >= 0.80`, tránh tình trạng sinh vật đi xuyên qua cây đá hoặc rơi khỏi thế giới).

### R5. Phản ánh Động lực học Môi trường (Ecological Dynamics & Seasonal State)
- Tham số hóa địa hình và thảm thực vật theo các biến số trạng thái sinh thái của Anima-Engine: mực nước động học (`water_level`), độ ẩm theo mùa (mùa mưa ngập bãi bồi, mùa khô trơ sỏi đá), chu kỳ suy giảm/tái sinh sinh khối thực vật (NPP Biomass).
- Cung cấp shader uniforms và thuộc tính đỉnh (vertex colors / mask planes) hỗ trợ hiệu ứng chuyển mùa thời gian thực trên WebGL/Three.js.

## Acceptance Criteria

### Tính Toàn vẹn Dữ liệu & Tương thích Anima-Engine
- [ ] File nhị phân `.anmw` sinh ra từ `terra_forge` giải mã thành công bởi cả Rust decoder (`world_artifact.rs`) và TypeScript decoder (`worldArtifact.ts`) với FNV-1a 32-bit checksum khớp 100%.
- [ ] `map_manifest.json` vượt qua toàn bộ các kiểm định của `validateMapManifest` và khớp với schema draft-07.
- [ ] Tọa độ thực thể và độ cao tuân thủ tuyệt đối `COORDINATE_CONTRACT.md` (X, Z trong [-100, 100], Y trong [0, 10], canonical scale 200.0).

### Hoạt động của Đường ống Meshy AI & Asset Vault
- [ ] Meshy API Client gửi task Text-to-3D, tự động polling trạng thái cho đến khi hoàn thành, tải `.glb` về local vault an toàn.
- [ ] Cache hit test: Cùng một prompt + seed không gửi request lặp lại sang Meshy, nạp trực tiếp từ Local Vault trong thời gian < 50ms.
- [ ] Mọi asset từ Meshy sau xử lý đều có đáy chạm mặt đất (`min_y == 0`), có ít nhất 2 cấp độ LOD và có collider primitive.

### Bối cảnh Nguyên thủy & Sinh thái
- [ ] 100% prompt sinh asset và bản đồ vượt qua bộ lọc kiểm duyệt không chứa vết cưa, đường xẻ gỗ, kiến trúc nhân tạo.
- [ ] Thảm thực vật và vật thể hữu cơ bám dính tự nhiên trên địa hình theo trường độ ẩm, hướng nắng và dòng chảy thủy văn.

### Hiệu năng Render & Điều hướng
- [ ] Dữ liệu phân tán xuất ra định dạng mảng ma trận nhị phân / JSON tương thích với Three.js `InstancedMesh`.
- [ ] Navmesh BFS đạt độ phủ `navmeshCoverage >= 0.80`, không có thực thể cây/đá nào tạo xung đột không đi được tại các vị trí sinh vật xuất phát.
- [ ] Toàn bộ test suite tự động vượt qua 100%.

## 2026-09-10T05:12:31Z

# Teamwork Project Prompt — Draft

> Status: Launched — Delegated to teamwork_preview
> Goal: Execute full AI-driven Primordial Abiotic 3D Map creation
> Requested team: Full team (3D Graphics/Simulation Architect, AI 3D Generative Engineer, Procedural Geologist, QA Verification Specialist)

Tạo lại toàn bộ bản đồ 3D thiên nhiên sơ khai (Primordial Nature) cho dự án Genesis_Zero bằng việc kết hợp AI tạo sinh 3D (Meshy AI v2) và động cơ mô phỏng địa chất/thủy văn chuyên sâu của terra_forge. Bản đồ tập trung 100% vào địa hình, núi non hiểm trở, hệ thống thủy văn (sông, suối, thác nước, hồ trung tâm, bãi cát/sỏi), và hệ thống hang động Karst ngầm; tạm thời chưa đưa thực vật (cây cối) và động vật vào giai đoạn này để tập trung tối đa chi tiết và độ tinh xảo cho nền tảng thế giới.

Working directory: E:\tool\mcp\terra_forge
Target directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: benchmark
Meshy API Key: msy_yFOKAOFOk9yjKUcwuk9rlkb0lTyuWMI0sT1T

## Requirements

### R1. Tạo Hình Địa Mạo & Cấu Trúc Núi Bằng AI & Mô Phỏng Địa Chất Cao Cấp (Geological Topography & AI Crags)
- Sử dụng Meshy AI v2 để tạo sinh các khối núi đá hiểm trở (horn peaks, crags, basalt columns, phong hóa tự nhiên) và đưa vào Local Asset Vault với đầy đủ chuẩn hóa hình học (bottom pivot min_y = 0.0, metric scaling, collision primitives).
- Mô phỏng địa chất đa tầng: bedrock nếp uốn (strata folding), đứt gãy kiến tạo tự nhiên, xói mòn thủy lực sâu (hydraulic droplet erosion) và xói mòn sườn dốc (thermal talus erosion) tạo nên các vách đá dựng đứng và thung lũng sâu chân thực.
- Xuất lưới địa hình độ phân giải cao kết hợp micro-roughness và shader triplanar đá cổ đại PBR.

### R2. Hệ Thống Thủy Văn Hoàn Chỉnh: Sông, Suối, Thác Nước, Hồ & Bãi Cát Bờ Vịnh (Comprehensive Hydrology & Sedimentology)
- Dựng hệ thống thủy văn 4 tầng liên tục:
  1. Thác nước và suối nguồn từ đỉnh núi cao đổ xuống.
  2. Đoạn sông uốn khúc tự nhiên (river meanders) với rãnh lòng sông khoét sâu (parabolic channel carving).
  3. Lòng hồ trung tâm sâu với gờ chắn nước tự nhiên (natural retaining berm).
  4. Vịnh cửa sông đổ ra biển, thềm cát ngập nước và bãi bồi ven bờ (riparian sandbanks & pebble deposits).
- Tạo sinh các khối đá cuội bào mòn dòng chảy và bãi cát lòng sông chân thực từ Meshy AI / Vault.
- Shader mặt nước PBR hỗ trợ độ sâu quang học (volume absorption depth color), bọt sóng va chạm bờ đá (contact foam) và vec-tơ dòng chảy (flow direction).

### R3. Hệ Thống Hang Động Karst Ngầm Kỳ Vĩ (Subterranean Karst Cavern System)
- Thiết kế hệ thống hang Karst ngầm tự nhiên ăn sâu vào lòng núi đá:
  - Cửa hang tự nhiên với vòm đá gồ ghề (rocky arch entrance) bám vách núi.
  - Trần hang với chuỗi nhũ đá (stalactites), măng đá (stalagmites) và cột đá vôi kết tinh (columns).
  - Hồ nước ngầm tĩnh lặng trong hang với mực nước liên thông thủy văn.
  - Vỉa khoáng thạch hoặc nấm phát quang nguyên thủy (bioluminescent cavern minerals) tạo điểm nhấn huyền bí.
- Mô hình các cấu trúc karst được sinh và tối ưu hình học qua Meshy AI và procedural geometry.

### R4. Chuẩn Hóa Dữ Liệu & Tương Thích Tuyệt Đối Anima-Engine (Genesis_Zero Integration)
- Xuất nhị phân `WorldArtifact` v2 (`world_256.anmw`) với FNV-1a checksum chuẩn xác, bao gồm 5 tầng trường dữ liệu: `elevation`, `moisture`, `temperature`, `flow`, `biome` (22 canonical biomes).
- Xuất `map_manifest.json` chuẩn schema của Genesis_Zero.
- Xuất bản đồ 3D hoàn chỉnh sang cả 2 định dạng:
  - `assets/blender_map/ecosystem_map.glb` (Three.js thời gian thực cho `viewer.html`).
  - `assets/blender_map/ecosystem_map.blend` (File master Blender 4.5/5.x với Cycles/Eevee shader).
- Đảm bảo lưới điều hướng (NavMesh BFS) đạt độ phủ >= 80.0% trên toàn bộ bề mặt đất liền có thể đi lại, xác định rõ điểm xuất phát (spawn position) an toàn.

### R5. Loại Trừ Triệt Để Sinh Vật & Thực Vật (Pure Abiotic World Foundation)
- Tuyệt đối KHÔNG phân tán cây cối, bụi cỏ, hoa màu, hoa quả hay thú vật/sinh vật trong giai đoạn này.
- Dành 100% dung lượng đa giác (polygon budget), bộ nhớ texture và năng lực tính toán cho độ chi tiết của đá, cát, trầm tích, dòng chảy và hang động.

## Acceptance Criteria

### Tính Thẩm Mỹ & Độ Chi Tiết 3D
- [ ] Địa hình hiển thị rõ nét các nếp gấp địa tầng, đỉnh núi nhọn sắc sảo, vách đá phong hóa tự nhiên và bờ biển cát thoai thoải.
- [ ] Dòng sông có lòng rãnh sâu, dòng suối từ núi cao đổ vào hồ có phân tầng vận tốc dòng chảy (`flow`).
- [ ] Hang động ngầm Karst có đầy đủ cửa hang, nhũ đá, măng đá, hồ ngầm và vật liệu phát quang.
- [ ] 0% cây cối và 0% động vật trên toàn bản đồ.
- [ ] Render 4 góc nhìn chuẩn thị giác (Isometric toàn cảnh, góc Đông Bắc, Top-down, Cận cảnh mép nước/hang động) thể hiện rõ chiều sâu và độ chi tiết ấn tượng.

### Tương Thích & Tính Toàn Vẹn Hệ Thống
- [ ] `world_256.anmw` giải mã thành công, FNV-1a checksum khớp, tuân thủ khế ước `COORDINATE_CONTRACT.md` (X, Z trong [-100, 100], Y trong [0, 10]).
- [ ] `map_manifest.json` vượt qua kiểm định schema.
- [ ] `ecosystem_map.glb` tải mượt mà trên `viewer.html` ở 60 FPS, camera tự động căn giữa toàn cảnh.
- [ ] NavMesh BFS đạt `navmeshCoverage >= 0.80`.

## 2026-09-10T11:07:26Z

# Teamwork Project Prompt — Draft

> Status: Launched — Delegated to teamwork_preview
> Goal: Execute multi-agent AAA Primordial Abiotic 3D Map creation
> Requested team: Full team (3D Simulation Architect, AI Generative 3D Artist, Procedural Geologist, WebGL Graphics Engineer, QA Victory Auditor)

Tái cấu trúc và nâng cấp toàn diện bản đồ 3D thiên nhiên sơ khai (Primordial Nature) cho Genesis_Zero lên chuẩn chất lượng game AAA: khắc phục triệt để hiện tượng bậc thang (staircasing) và các hình khối thô sơ (khối núi nón trơn, hang cục tròn); kết hợp mô phỏng địa chất xói mòn sâu với các mô hình 3D tạo sinh trực tiếp từ Meshy AI v2 (khối núi đá granite hiểm trở, vòm hang Karst & nhũ đá vôi, bãi đá cuội lòng suối, vách đá bờ biển); thiết kế hệ thống thủy văn 4 tầng liền mạch (thác, sông uốn khúc, hồ sâu, vịnh biển) không bị các tấm phẳng cắt ngang; phủ vật liệu PBR địa tầng tự nhiên và tối ưu Three.js WebGL 60 FPS cho viewer.html.

Working directory: E:\tool\mcp\terra_forge
Target directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: benchmark
Meshy API Key: msy_yFOKAOFOk9yjKUcwuk9rlkb0lTyuWMI0sT1T

## Requirements

### R1. Tái Thiết Kế Địa Mạo & Loại Bỏ Triệt Để Bậc Thang (Organic Topography & Anti-Staircasing)
- Khử bỏ 100% các vết khấc bậc thang (stepping/terracing artifacts) trên toàn bộ bề mặt địa hình; áp dụng bộ lọc làm mịn hữu cơ (Laplacian & Bilateral surface smoothing) kết hợp Ridged Multi-Fractal Noise và mô phỏng xói mòn thủy lực (Hydraulic Droplet Erosion) để tạo nên các sườn núi tự nhiên, rãnh xói mòn sâu và bãi bồi trầm tích chân thực.
- Thay thế hoàn toàn các khối núi hình nón trơn nhẵn bằng cấu trúc địa chất sắc sảo: đỉnh sừng (horn peaks), sống núi lởm chởm (aretes), vách đá đứt gãy kiến tạo với nếp uốn địa tầng rõ rệt.

### R2. Tích Hợp Mô Hình 3D Thực Tế Từ Meshy AI v2 (Meshy AI Abiotic Generation & Asset Vault)
- Gọi trực tiếp API Meshy v2 (`https://api.meshy.ai/openapi/v2/text-to-3d`) để tạo sinh các mô hình 3D địa chất chất lượng cao (lưới hình học chi tiết + texture PBR):
  1. *Khối vách đá granite cổ đại phong hóa lởm chởm (Weathered granite crags & sharp jagged peaks)*.
  2. *Cửa vòm đá hang Karst tự nhiên khoét sâu vào lòng núi (Natural rocky karst arch cavern entrance)*.
  3. *Chuỗi nhũ đá và măng đá vôi ngầm (Limestone stalactites & stalagmites cluster)*.
  4. *Cụm đá cuội lòng suối bào mòn dòng chảy và bãi đá ven vịnh biển (Fluvial riverbed boulders & coastal rocks)*.
- Chuẩn hóa hình học tự động (`min_y = 0.0`, kích thước thực tế theo hệ mét, trích xuất va chạm) và lưu trữ vào Local Asset Vault (`terra_forge/assets/vault/`).
- Ghép nối liền mạch (seamless boolean/geometry blend) các asset từ Meshy AI vào địa hình tổng thể, chấm dứt hoàn toàn tình trạng cửa hang là khối tròn/lồi lõm thô sơ gắn vào sườn núi.

### R3. Hệ Thống Thủy Văn Liền Mạch & Mặt Nước Chân Thực (Seamless Hydrology & PBR Water)
- Thiết kế lòng sông và đáy hồ có tiết diện cong tự nhiên (parabolic carved bed), chấm dứt tình trạng các tấm mặt nước phẳng hình chữ nhật cắt ngang địa hình tạo rìa góc nhọn thô kệch.
- Hệ thống lưới mặt nước liên tục 4 tầng: thác nước từ sườn dốc đổ vào hồ trung tâm sâu, kênh thoát nước uốn khúc tự nhiên đổ ra vịnh biển góc đông nam.
- Shader nước Three.js và Blender hỗ trợ: độ sâu quang học (nước sâu xanh thẫm, nước nông trong vắt), bọt trắng va chạm ven bờ đá (contact foam) và độ phản xạ PBR chuẩn.

### R4. Hệ Thống Vật Liệu & Màu Sắc Địa Tầng PBR (PBR Strata & Texture Mapping)
- Phủ vật liệu địa tầng tự nhiên: vân đá granite phong hóa, cát sỏi ven hồ/biển, rêu ẩm thung lũng và tuyết đỉnh núi. Bề mặt thể hiện rõ độ nhám (roughness) và vi cấu trúc gồ ghề dưới mọi góc chiếu sáng.
- Bãi cát ven hồ và vịnh biển có độ chuyển màu mượt mà sang đá ngầm và trầm tích ướt.
- Tuyệt đối tuân thủ nguyên tắc **100% Abiotic**: 0% cây cối nhân tạo/hoạt họa, 0% công trình kiến trúc, 0% động vật trong giai đoạn này để tập trung trọn vẹn ngân sách đa giác và bộ nhớ cho địa mạo.

### R5. Chuẩn Hóa Dữ Liệu & Khế Ước Genesis_Zero (Anima-Engine Parity)
- Cập nhật file nhị phân `world_256.anmw` (256x256, 5 lớp dữ liệu: `elevation`, `moisture`, `temperature`, `flow`, `biome`), FNV-1a checksum chuẩn xác.
- Xuất file master `assets/blender_map/ecosystem_map.blend` và mô hình thời gian thực `assets/blender_map/ecosystem_map.glb`.
- Tối ưu `viewer.html` đạt 60 FPS mượt mà trên WebGL, tự động nạp bản đồ mới không bị lưu cache cũ, camera tự động căn chỉnh và hỗ trợ đầy đủ 4 góc nhìn chuẩn thị giác.
- Độ phủ điều hướng NavMesh BFS $\ge 80.0\%$ trên phần đất liền đi lại được.

## Acceptance Criteria

### Tính Thẩm Mỹ & Độ Tinh Xảo 3D
- [ ] Không còn bất kỳ vết khấc bậc thang nhân tạo nào trên bề mặt địa hình; sườn núi và rãnh xói mòn hiển thị mịn màng và tự nhiên.
- [ ] Các asset 3D độc lập (Vách đá crag, Cửa hang Karst, Nhũ đá, Bãi đá cuội) được tạo sinh thành công từ Meshy AI API và tích hợp hữu cơ vào bản đồ.
- [ ] Cửa hang Karst và lòng hang có hình khối vòm đá tự nhiên với nhũ đá bên trong, không còn là khối xám thô ráp.
- [ ] Mặt nước sông hồ kết nối liền mạch với địa hình, không bị viền phẳng đa giác đâm xuyên thô kệch.
- [ ] Ảnh chụp từ 4 góc nhìn chuẩn (Toàn cảnh, Đông Bắc, Top-down, Cận cảnh hang/mép nước) đạt độ chi tiết cao, chân thực chuẩn AAA, màu sắc hài hòa.

### Tương Thích & Tính Toàn Vẹn Hệ Thống
- [ ] `ecosystem_map.glb` nạp mượt mà trên `viewer.html` ở 60 FPS với thời gian tải < 3s, hiển thị đầy đủ màu sắc vật liệu PBR và hiệu ứng nước.
- [ ] `world_256.anmw` giải mã thành công với FNV-1a checksum hợp lệ, tuân thủ `COORDINATE_CONTRACT.md`.
- [ ] `map_manifest.json` khớp với schema draft-07.
- [ ] Toàn bộ test suite tự động vượt qua 100%.

## 2026-09-18T03:59:32Z

Nghiên cứu nâng cấp, phát triển toàn diện dự án Genesis_Zero: rà soát và khắc phục triệt để lỗi hệ thống, tối ưu hóa hiệu năng tính toán và hiển thị (simulation/WebGL/memory), cùng nâng cấp chất lượng kiến trúc để dự án đạt trạng thái vận hành tốt nhất.

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: development

## Requirements

### R1. Comprehensive Defect Detection & Bug Remediation
Conduct an exhaustive audit of the codebase (`genesis`, `scripts`, `tests`, `web`, `tools`) to detect and fix runtime errors, test failures, race conditions, edge case exceptions, and platform encoding issues (Windows UTF-8). All existing functionality must be preserved without regressions.

### R2. Performance & Resource Optimization
Profile and optimize critical performance paths including terrain/erosion/hydrology simulation loops, agent simulation ticks, asset ingestion/mesh handling, and WebGL viewer payload/render responsiveness. Provide concrete, measurable speedups or memory footprint reductions.

### R3. Architectural Upgrade & Maintainability
Refactor fragile modules, tighten interface contracts, streamline CLI/server runtime pipelines, and deliver an actionable architectural upgrade roadmap documenting all enhancements and future scaling pathways.

## Acceptance Criteria

### Automated Verification
- [ ] `python scripts/ci_quick.py` passes 100% (exit code 0) within baseline timing bounds.
- [ ] `python scripts/ci_smoke.py` passes 100% (exit code 0) without unhandled exceptions.
- [ ] The existing test baseline (1679+ passing tests) maintains zero regressions across `pytest` test suites.
- [ ] Core CLI entrypoints (`python -m genesis.run`, `python scripts/launch.py --help`, `python scripts/preflight.py`) execute cleanly without encoding errors or tracebacks.

### Optimization & Quality Verification
- [ ] Performance optimizations are benchmarked and verified with before/after execution metrics or profiling logs.
- [ ] Binary map artifacts (`.anmw`), manifests (`map_manifest.json`), and schema validators retain strict data format compliance.
- [ ] WebGL viewer (`assets/blender_map/viewer.html` / `web/`) remains fully functional with zero broken asset links or console errors.

### Deliverables & Reporting
- [ ] A detailed optimization and upgrade report documenting all bugs resolved, performance gains achieved, and architectural enhancements made.

## 2026-09-18T09:32:26Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Comprehensively upgrade, optimize, and modernize the Genesis_Zero project across all dimensions: performance, architecture, feature capabilities, and reliability, bringing it to a state-of-the-art production standard.

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: development

## Requirements

### R1. Performance & Optimization
Analyze and refactor the core logic to maximize execution speed and minimize resource consumption.

### R2. Architecture & Modernization
Update project dependencies to their latest stable versions and restructure the codebase to adhere to modern industry best practices.

### R3. Reliability
Ensure robust error handling throughout the application and implement a comprehensive test suite.

## Acceptance Criteria

### Verification: Quality & Modernization
- [ ] All code passes static analysis (e.g., `ruff check`, `mypy`) with zero errors.
- [ ] Dependency manager (e.g., `uv` or `pip`) reports no highly vulnerable or severely outdated dependencies.

### Verification: Reliability
- [ ] The `pytest` test suite executes successfully with no failing tests.
- [ ] Code coverage is maintained or improved compared to the current baseline.

## 2026-09-19T15:27:10Z

Thực hiện nghiên cứu toàn diện dự án Genesis_Zero, đề xuất các giải pháp nâng cấp (hiệu năng, kiến trúc, CI/CD) và **trực tiếp thực hiện việc chỉnh sửa mã nguồn** để áp dụng các nâng cấp này.

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: benchmark

## Requirements

### R1. Phân tích và lập kế hoạch
Quét mã nguồn dự án Genesis_Zero, nhận diện điểm nghẽn và technical debt. Lập một bản kế hoạch nâng cấp (`upgrade_plan.md`) ngắn gọn trước khi thực thi.

### R2. Thực thi nâng cấp mã nguồn
Trực tiếp sửa đổi, tái cấu trúc (refactor) và viết thêm mã nguồn mới để áp dụng các giải pháp đã đề xuất. Nâng cấp các thư viện/framework nếu cần thiết.

### R3. Tối ưu hóa CI/CD
Cập nhật hoặc tạo mới các file cấu hình CI/CD (ví dụ: GitHub Actions, GitLab CI, Dockerfile) theo tiêu chuẩn mới.

### R4. Tài liệu hóa
Cập nhật README.md hoặc tạo tài liệu giải thích các thay đổi kiến trúc và cách chạy/deploy dự án sau khi nâng cấp.

## Verification Resources
Dự án có sẵn các công cụ để tự kiểm chứng:
- Chạy `make test` hoặc `pytest` để chạy bộ unit test hiện có.
- Chạy `make lint` để kiểm tra lỗi cú pháp/chuẩn mã nguồn (sử dụng `ruff`).
- Có thể dùng `make preflight` để kiểm tra độ sẵn sàng của hệ thống.

## Acceptance Criteria

### Tính toàn vẹn của mã nguồn
- [ ] Mã nguồn sau khi nâng cấp phải vượt qua `make test` (chạy thành công các test case hiện có).
- [ ] Vượt qua kiểm tra của linter bằng lệnh `make lint` mà không báo lỗi nghiêm trọng.
- [ ] Các tính năng cốt lõi của dự án chạy bình thường.

### CI/CD
- [ ] File cấu hình CI/CD phải hợp lệ và tương thích với kiến trúc mới.

## 2026-09-20T04:52:03Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Delegate to teamwork_preview
> Requested team: Full team

Nâng cấp dự án bản đồ thế giới sinh vật 3D trở nên chân thực, đẹp mắt và hoàn thiện nhất, tham khảo các dự án mã nguồn mở để chuẩn bị cho việc đóng gói. Dự án là một bản demo chất lượng cao (Proof of Concept). Nhóm agent toàn diện (Full team) sẽ tự quyết định nền tảng (Web/Desktop) và công nghệ phù hợp nhất.

Working directory: ~/teamwork_projects/genesis_zero
Integrity mode: demo

## Requirements

### R1. Xây dựng môi trường 3D chân thực
Phát triển bản demo thế giới sinh vật 3D với mức độ chi tiết cao. Trọng tâm là chất lượng thị giác chân thực, áp dụng các kỹ thuật render hiện đại (vật liệu vật lý, ánh sáng phức tạp, bóng đổ).

### R2. Kiến trúc chuẩn mã nguồn mở và đóng gói
Thiết lập cấu trúc thư mục và mã nguồn theo chuẩn của các dự án mã nguồn mở chất lượng cao. Mã nguồn phải có tính mô-đun, dễ mở rộng và đi kèm với các tập lệnh (scripts) đóng gói/build rõ ràng để sẵn sàng phát hành.

### R3. Lựa chọn công nghệ tối ưu
Nhóm tự nghiên cứu, đánh giá và quyết định bộ công cụ/framework đồ họa tốt nhất (VD: WebGL/Three.js, Babylon.js, hoặc framework phù hợp) để đạt được mục tiêu thị giác và hiệu năng của bản demo.

## Acceptance Criteria

### Khả năng hoạt động và đóng gói
- [ ] Dự án có thể cài đặt các phụ thuộc (dependencies) và build hoặc khởi động thành công bằng kịch bản tự động (automated script) mà không văng lỗi (zero errors).
- [ ] Tồn tại các file cấu hình rõ ràng cho việc đóng gói dự án (ví dụ: kịch bản build cho production).

### Chất lượng đồ họa (Đánh giá bằng Code Analysis)
- [ ] Kịch bản phân tích mã (code analysis script) xác nhận sự hiện diện của các cấu hình ánh sáng tiên tiến (ví dụ: bật bóng đổ - shadows, ánh sáng môi trường/định hướng).
- [ ] Mã nguồn cấu hình môi trường/sinh vật có sử dụng hệ thống vật liệu vật lý (PBR - Physically Based Rendering) hoặc các kỹ thuật shader nâng cao tương đương.

### Đánh giá kiến trúc (Agent-as-judge)
- [ ] Một Agent độc lập đánh giá cấu trúc dự án và xác nhận mã nguồn được chia tách thành các mô-đun logic hợp lý (tách biệt giữa assets, rendering logic, và entity/creature logic).

## 2026-09-20T18:01:54Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: Đội ngũ đầy đủ (Full Team: chuyên gia kiến trúc, lập trình, adversarial review và kiểm thử độc lập)

Nghiên cứu, nâng cấp toàn diện và tối ưu hóa hệ sinh thái Genesis Zero: cải tiến trí tuệ sinh vật LLM trong việc khám phá luật ẩn, tối đa hóa thông lượng vòng lặp mô phỏng, nâng tầm đồ họa 3D WebGL Three.js đạt chuẩn mực thị giác chân thực, và củng cố độ ổn định hạ tầng mạng đa điểm theo chuẩn mực nghiên cứu & production.

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: development

## Requirements

### R1. Trí Tuệ Sinh Vật & Cơ Chế Khám Phá Định Luật Ẩn (LLM & Agent Cognition)
Nâng cấp khả năng tư duy và chiến lược sinh tồn của sinh vật, cho phép hình thành giả thuyết khoa học và suy luận chính xác các định luật vật lý ngẫu nhiên ẩn giấu của thế giới. Cung cấp bộ công cụ đo lường và benchmark A/B định lượng so sánh hiệu quả giữa các mô hình trí tuệ (Frontier LLM, Local LLM, Reflex Strategist) với đầy đủ cơ chế bảo vệ bí mật luật ẩn (bất biến B-05 và B-10).

### R2. Tối Ưu Hóa Thông Lượng & Hiệu Năng Vòng Lặp Mô Phỏng (Simulation Engine Throughput)
Loại bỏ các điểm nghẽn hiệu năng trong vòng lặp 6 pha của simulation engine (tối ưu hóa phép tính khoảng cách Chebyshev, kiểm tra địa hình đi được, tạo context đánh giá LawDSL và quản lý bộ nhớ). Đảm bảo tốc độ tính toán nhanh vượt bậc trong chế độ headless nhưng bảo toàn tuyệt đối 100% tính tất định (bất biến B-02 Seed Determinism).

### R3. Nâng Tầm Trải Nghiệm & Độ Chân Thực Trình Hiển Thị 3D Spectator (WebGL 3D Fidelity)
Nâng cấp trình hiển thị WebGL Three.js với vật liệu PBR cao cấp, bóng đổ mềm, hiệu ứng nước và khí quyển thời tiết chân thực, chuyển động animation sinh vật mượt mà, và hệ thống âm thanh tổng hợp Web Audio phản hồi theo sự kiện chiến đấu/sinh tồn. Đảm bảo toàn bộ kiến trúc đồ họa tuân thủ nghiêm ngặt nguyên tắc Zero-CDN (chạy 100% offline) kèm cơ chế dự phòng (fallback) tự động.

### R4. Hạ Tầng Mạng Đồng Bộ & Chuẩn Mực Triển Khai Production (Network & Code Quality)
Đảm bảo luồng truyền phát WebSocket `/v1/spectate` đồng bộ mượt mà với nhiều spectator đồng thời mà không làm giảm tốc độ của engine mô phỏng. Củng cố chất lượng toàn bộ codebase đạt chuẩn kiểm thử tĩnh nghiêm ngặt (Ruff, Mypy), tỷ lệ bao phủ test suite cao, và hỗ trợ khởi chạy 1-chạm đa nền tảng (Windows, macOS, Linux, Docker).

## Acceptance Criteria

### Tính Tất Định & Bất Biến Cốt Lõi (Invariants & Integrity)
- [ ] Tất cả các bài kiểm tra determinism (`tests/test_determinism.py`) vượt qua 100% với cùng seed và map đầu vào (bảo toàn bất biến B-02).
- [ ] Các bài kiểm thử bảo mật luật ẩn và cách ly trọng tài (`tests/test_score.py`, `tests/test_victory.py`) vượt qua 100% (bảo toàn bất biến B-05 và B-10).
- [ ] Toàn bộ test suite hiện có (1889+ tests) cùng các test mới được thực thi tự động qua pytest mà không có bất kỳ failure nào.

### Thông Lượng Mô Phỏng (Simulation Throughput)
- [ ] Tốc độ mô phỏng headless (`python -m genesis.run --seed 42 --ticks 400 --no-render`) đạt thông lượng tối thiểu >= 900 ticks/giây trên môi trường tiêu chuẩn.
- [ ] Hồ sơ profiling định lượng (cProfile) chứng minh giảm thiểu tối thiểu 50% thời gian tích lũy tại các hàm nút thắt (`dist`, `passable`, `build_ctx`).

### Đánh Giá Trí Tuệ & Khám Phá Luật (AI Benchmarking)
- [ ] Kịch bản đánh giá A/B benchmark (`scripts/b10_ab.py` hoặc suite tương đương) hoàn tất 5 seed kiểm chuẩn độc lập mà không gặp lỗi runtime, dead-lock hay rò rỉ bộ nhớ.
- [ ] Sinh vật ứng dụng cơ chế suy luận giả thuyết ghi nhận tỷ lệ phát hiện chính xác định luật ẩn cao hơn tối thiểu 20% so với baseline ngẫu nhiên.

### Đồ Họa 3D WebGL & Zero-CDN (Graphics & Modularity)
- [ ] Các kịch bản kiểm định kiến trúc và đồ họa (`python scripts/analyze_graphics_code.py` và `python scripts/verify_modular_architecture.py`) vượt qua 100% các tiêu chí đánh giá.
- [ ] Kịch bản kiểm tra offline (`python scripts/verify_zero_cdn.py`) xác nhận 0 dependency từ external CDN.

### Chuẩn Mực Mã Nguồn & Đóng Gói (Code Quality & Build)
- [ ] `uv run ruff check .` và `uv run mypy genesis/` vượt qua 100% không phát sinh lỗi hoặc cảnh báo vi phạm kiểu dữ liệu.
- [ ] Kịch bản đóng gói phân phối (`python scripts/build_dist.py`) tạo thành công wheel package và sdist sạch, cài đặt và kiểm thử hoạt động bình thường.

## 2026-09-21T01:18:42Z

# Teamwork Project Prompt — Draft

> Status: Draft  
> Goal: Craft prompt → get user approval → delegate to teamwork_preview  
> Requested team: Đội ngũ đầy đủ (Full Team: chuyên gia kiến trúc, chuyên gia mô phỏng, kỹ sư LLM Reasoning, chuyên gia đồ họa 3D WebGL, kỹ sư hệ thống & kiểm thử độc lập)

Nghiên cứu, thiết kế và nâng cấp toàn diện dự án Genesis Zero lên thế hệ mới (Genesis Zero Gen 22 — Frontier Epistemology & Deep Ecological Evolution): hiện thực hóa chu trình tư duy khoa học chủ động (Active Scientific Method) giúp LLM suy luận chính xác các định luật ẩn, mở rộng thế giới sinh thái động với trường pheromone hóa sinh và đa quần xã (multi-biome), nâng cấp trình diễn họa 3D WebGL Three.js đạt chuẩn điện ảnh với chế độ tương tác "God-Mode", thiết lập đấu trường giải đấu đa mô hình (Multi-Model Tournament Arena) cùng bộ xuất dữ liệu nghiên cứu khoa học mở (Open Science Dataset Exporter), và duy trì 100% các bất biến cốt lõi (B-02 Seed Determinism, B-05 Secrecy, B-10 Referee Isolation, Zero-CDN).

Working directory: e:\Project\01_AI_Agents\Genesis_Zero
Integrity mode: development

## Requirements

### R1. Chu Trình Suy Luận Khoa Học Chủ Động & Đột Phá Khám Phá Luật (Active Epistemology & Scientific Method)
Xây dựng cơ chế tư duy khoa học 2 tầng (Dual-Memory Cognitive Architecture) gồm bộ đệm trải nghiệm (Episodic Buffer) và sổ tay giả thuyết Bayes (Semantic Hypothesis Ledger). Nâng cấp hành vi thử nghiệm chủ động (Falsification Loop): sinh vật chủ động kích hoạt các hành vi kiểm chứng có đối chứng để loại trừ tương quan giả trước khi ghi vào Sổ Luật (Codex). Tích hợp bộ tiền kiểm cú pháp nhận thức (Cognitive Schema Validator) ngăn chặn 100% lỗi cú pháp và thiếu trường (`mag`, `dur`) khi gọi `CODEX_OP`. Xây dựng bộ công cụ giải đấu đa mô hình (`scripts/arena_tournament.py`) đo lường định lượng tỷ lệ phát hiện luật ($M$), độ trễ nhận thức ($t_{\text{discover}}$) và độ trễ hành vi thích ứng ($\Delta t_{\text{exploit}}$) giữa các dòng mô hình (Frontier Thinking, Open-Weights, Small Local).

### R2. Động Lực Học Sinh Thái Đa Tầng, Trường Pheromone & Đa Quần Xã (Chemical Ecology & World Scaling)
Mở rộng môi trường mô phỏng với lưới khuếch tán hóa sinh liên tục (Continuous Pheromone Field: mùi thức ăn, tín hiệu nguy hiểm, pheromone bầy đàn) cho phép sinh vật định hướng theo gradient hóa học. Mở rộng kích thước bản đồ lên quy mô đa quần xã (Meso-Scale Multi-Biome: 32x32 và 48x48) với địa hình cao độ, đầm lầy, rạn san hô, hẻm núi ngầm và chu kỳ vi khí hậu thời tiết. Thiết lập lưới dinh dưỡng bảo toàn năng lượng (Trophic Food Web & Energy Entropy) và cây phả hệ tiến hóa (Phylogenetic Cladogram) trực quan hóa sự phân nhánh loài qua hàng trăm thế hệ.

### R3. Đồ Họa 3D WebGL Điện Ảnh & Phòng Thí Nghiệm Tương Tác "God Mode" (Photorealistic WebGL & Interactive Spectator)
Nâng tầm trải nghiệm WebGL Three.js với camera góc nhìn sinh vật (Creature POV Follow-Cam) tích hợp màn hình HUD hiển thị nón thị giác, chỉ số sinh tồn và luồng suy nghĩ LLM theo thời gian thực; kèm chế độ đạo diễn tự động (Director Mode) lia máy tới các pha kịch tính. Nâng cấp shader PBR với mặt nước phản chiếu và tán xạ caustics, tia nắng thể tích (god rays), hiệu ứng phát quang sinh học ban đêm, bão thời tiết hạt (particle weather storms) và sóng xung kích vũ trụ khi luật được giải mã. Phát triển bảng điều khiển "God Mode" cho phép can thiệp thả tài nguyên, bão sét, đột biến thử nghiệm và chuyển đổi góc nhìn toàn tri/sương mù tri giác (Fog-of-War). Duy trì nghiêm ngặt 100% Offline Zero-CDN và tăng tốc render InstancedMesh.

### R4. Hạ Tầng Đấu Trường Phân Tán & Bộ Dữ Liệu Nghiên Cứu Mở (Distributed Arena & Open Science Benchmark)
Xây dựng cổng kết nối đấu trường nhiều người chơi (Multi-Tenant Arena Gateway `/v1/arena`) cho phép các nhà nghiên cứu bên ngoài cắm các agent LLM độc lập vào tranh tài với cơ chế xác thực chống gian lận và hệ thống xếp hạng Elo. Phát triển công cụ xuất dữ liệu nghiên cứu khoa học mở (`scripts/export_scientific_dataset.py`) ghi nhận toàn bộ quỹ đạo tư duy `(observation, internal_reasoning, action, outcome, ground_truth_match)` theo định dạng chuẩn Parquet / HuggingFace Dataset. Tối ưu hóa engine mô phỏng hàng loạt (Batch Vectorized Parallel Worlds) đạt thông lượng > 15,000 ticks/giây trên nhiều luồng song song.

### R5. Kỷ Luật Kỹ Thuật, Kiểm Thử Kháng Biến & Đóng Gói Phân Phối (Architecture & Quality Assurance)
Bảo toàn tuyệt đối 100% các bất biến hệ thống: B-02 Seed Determinism (khớp 100% byte-for-byte), B-05 Law Secrecy (0 rò rỉ danh tính luật ẩn ra client/spectator), B-10 Referee Isolation (0 import sim trong score/victory), W-18 Passability SSoT. Vượt qua 100% bộ kiểm thử hiện có (2,071+ tests) cùng các kịch bản kiểm thử adversarial mới. Đạt chuẩn 100% Ruff và Mypy không lỗi. Cập nhật các kịch bản khởi chạy 1-chạm đa nền tảng (`run.ps1`, `run.sh`, `run.bat`, Docker Compose).

## Acceptance Criteria

### Nhận Thức Khoa Học & Giải Đấu LLM (Epistemology & AI Benchmarking)
- [ ] Bộ tiền kiểm nhận thức đảm bảo 100% các thao tác `CODEX_OP` từ agent đều tuân thủ đầy đủ schema và từ vựng của cấp độ `brain`, triệt tiêu 100% lỗi điểm 0 do thiếu trường cấu trúc.
- [ ] Cơ chế thử nghiệm chủ động (Falsification Loop) giúp sinh vật có tỷ lệ phát hiện chính xác định luật ẩn ($M \ge 0.5$) trên các bài test định lượng.
- [ ] Kịch bản `scripts/arena_tournament.py` thực thi thành công giải đấu đối đầu tự động trên 5+ seed kiểm chuẩn giữa Frontier model, Open model và Reflex baseline, xuất báo cáo so sánh đầy đủ các chỉ số nhận thức.

### Mô Phỏng Sinh Thái & Thế Giới Đa Quần Xã (Ecology & Scaling)
- [ ] Trường pheromone 2D hoạt động chính xác với phương trình khuếch tán và bay hơi, bảo toàn tính tất định B-02.
- [ ] Bản đồ đa quần xã (Multi-Biome 32x32) tạo địa hình phong phú, phân tầng sinh thái hợp lý và tuân thủ biên tuần hoàn (toroidal wrap).
- [ ] Cây phả hệ tiến hóa (Phylogenetic Cladogram) ghi nhận và xuất dữ liệu phân nhánh loài, khoảng cách di truyền chính xác qua các thế hệ.

### Đồ Họa 3D, God-Mode & Zero-CDN (Graphics & Experience)
- [ ] Trình hiển thị 3D hỗ trợ mượt mà các chế độ camera: Orbit, Creature Follow-Cam (với HUD sinh tồn & suy nghĩ LLM), và Director Mode.
- [ ] Áp dụng kỹ thuật InstancedMesh giảm tối thiểu 80% số draw calls của thảm thực vật và địa hình diorama, duy trì 60 FPS ổn định.
- [ ] Bảng điều khiển God Mode tương tác trực tiếp với thế giới mô phỏng và hỗ trợ bật/tắt Fog-of-War mượt mà.
- [ ] Duy trì 100% Zero-CDN: 0 liên kết ngoài, 0 thư viện CDN phụ thuộc, âm thanh Web Audio hoàn toàn thủ tục.

### Đấu Trường Mạng & Bộ Dữ Liệu Nghiên Cứu (Network & Open Science)
- [ ] Endpoint `/v1/arena` hỗ trợ kết nối agent bên ngoài, xác thực hạn mức token và ghi nhận bảng xếp hạng Elo.
- [ ] Kịch bản xuất dữ liệu `scripts/export_scientific_dataset.py` trích xuất thành công dataset chuẩn Parquet/JSONL với đầy đủ quỹ đạo nhận thức.
- [ ] Hệ thống mô phỏng song song đa thế giới đạt tốc độ tổng hợp >= 10,000 ticks/giây trong môi trường benchmark đa nhân.

### Độ Tin Cậy & Toàn Vẹn Mã Nguồn (Integrity & Testing)
- [ ] 100% test suite (2,071+ tests và test mới) vượt qua với 0 failure và 0 error.
- [ ] `uv run ruff check .` và `uv run mypy genesis/` đạt 0 cảnh báo và 0 lỗi.
- [ ] Bảo toàn 100% bất biến B-02, B-05, B-10 và W-18 được xác nhận bởi các bài kiểm tra chuyên biệt.



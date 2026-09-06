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

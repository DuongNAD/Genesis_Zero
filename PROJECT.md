# Project: Genesis_Zero AAA Primordial Abiotic 3D Map

## v1.0 Release Baseline (verification pending, 2026-09-17)

Verification state at the v1.0 gate, kept separate from the terra_forge milestones above:

**Verified on this machine (Windows, Python 3.11):**
- `scripts/ci_smoke.py` — exit 0, `match = 1.000` trên 150 dòng (model giả biết trước đáp án; chứng minh bộ chấm B-10 bắt được lời giải đúng, không phải số đo của model thật).
- `scripts/ci_quick.py` — bộ hợp đồng offline (< 60 s): adapter frontier, health/ready, chuẩn bị luật nền bất đồng bộ, telemetry envelope, dossier mapping, budget tách thinking.
- `tests/test_challenger_m5_launchers.py` — 24 passed / 1 skipped trên Windows sau bản vá mã hoá (UTF-8 ở cả child lẫn reader). Hợp đồng `run_web_server` được khoá bằng unit test: KeyboardInterrupt → thoát 0 kèm thông báo; child tự thoát → giữ nguyên mã lỗi; env phát UTF-8. Skip duy nhất là gửi SIGINT thật theo pid (POSIX-only; Ctrl+C console Windows chưa được xác minh độc lập).
- Hardening cp1252 áp dụng ở cả ba điểm vào CLI: `genesis.run`, `scripts/launch.py`, `scripts/preflight.py` (reconfigure UTF-8 trước khi Rich dựng Console; tiến trình con phát UTF-8 qua env).

**Measurement protocol (chưa có số — cần endpoint/model thật):**
- `scripts/b10_ab.py --plan` khoá giao thức 5 seed (7, 9, 42, 55, 101), thứ tự nhánh xen kẽ, giữ nguyên bộ chấm; `--plan` không gọi model.
- Mỗi nhánh ghi log/truth/CSV thô; số `LLM_MISS` được điều tra riêng và biến kết quả thành `degraded_model_calls` — tuyệt đối không đọc miss thành "model không quy nạp được".

**Skips có lý do (không phải pass ảo):** `tests/test_adversarial_preview_fauna.py` bỏ 6 test gắn với asset legacy (blend không còn armature Stag/Eagle, GLB không còn animation/skin, ảnh render_preview.png đã bị xoá khỏi revision hiện tại).

---

## Architecture
Combining Meshy AI v2 Text-to-3D and the `terra_forge` geological/hydrological simulation engine to generate an organic, 100% abiotic 3D world diorama and simulation environment for `Genesis_Zero` and `Anima-Engine` adhering to AAA production standards.

### Subsystems & Data Flow
1. **Topography & Geomorphology Subsystem (`terra_forge/core/heightfield.py`, `terra_forge/core/erosion.py`)**:
   - $C^2$ quintic Hermite Perlin gradient noise and Ridged Multi-Fractal (RMF) bedrock foundation.
   - Alpine Matterhorn horn peak synthesis with knife-edge radiating aretes and glacial cirque hollows.
   - Two-stage Anti-Staircasing: Pre-erosion 7x7 edge-preserving Bilateral filter ($\sigma_s=2.5, \sigma_r=1.8$) and Post-erosion Taubin/Laplacian surface relaxation.
   - Slice-accelerated droplet hydraulic erosion with bilinear termination deposition (zero single-cell needle spikes) and 24-iteration thermal talus weathering.
2. **AI Generative & Asset Vault Subsystem (`terra_forge/ai/`, `assets/vault/`, `terra_forge/blender/`)**:
   - Meshy AI v2 Client with exponential backoff, rate limiting, and safe secret masking (`msy_yFOKAOFOk9yjKUcwuk9rlkb0lTyuWMI0sT1T`).
   - `AbioticType` taxonomy expansion including `KarstArch`.
   - Local Asset Vault caching 4 target AAA asset types:
     1) Weathered granite crags & sharp jagged peaks (`RockCrag` / `HornPeak`)
     2) Natural rocky karst arch cavern entrance (`KarstArch`)
     3) Limestone stalactites & stalagmites cluster (`Stalactite` / `Stalagmite`)
     4) Fluvial riverbed boulders & coastal rocks (`RiverPebble` / `RiparianSandbank`)
   - Geometric normalization: bottom pivot `min_y = 0.0`, metric scaling, cylinder/AABB/convex hull colliders, 3-tier LODs.
   - Seamless geometry blending: boolean difference carve on terrain for cave portal, flange overlap + `DATA_TRANSFER` normal transfer, negative embed depth ($-0.8\text{m}$) for crags, and riverbed boulder scattering along flow vectors with 25% embed.
3. **Hydrology & Optical Water Subsystem (`terra_forge/core/hydrology.py`, `terra_forge/blender/water_builder.py`)**:
   - Continuous 4-tier hydrology: Mountain Cascades $\to$ Valley Meander $\to$ Central Lake $\to$ Outlet Gorge & Bay.
   - Parabolic carved channel bed with 3D conforming river ribbon ($0.08\text{m} - 0.20\text{m}$ clearance) and smoothstep lake blending; central lake cradled in $+1.2\text{m}$ moraine retaining berm. Zero flat plane intersecting artifacts.
   - Optical water shader with Beer-Lambert depth absorption and contact foam margin.
4. **PBR Strata & Abiotic Subsystem (`terra_forge/blender/shaders.py`, `assets/blender_map/viewer.html`)**:
   - Object-space triplanar multi-splatting ($p=6.0$, coarse Perlin perturbation) for 5 geological classes: Cliff Bedrock, Scree Talus, Humus Soil & Valley Moss, Coastal Sand, Alpine Snow.
   - Strict 100% abiotic compliance: 0% flora, 0% fauna, 0% architecture.
5. **Data Standardization & Deliverables Subsystem (`terra_forge/core/`, `assets/blender_map/`)**:
   - `WorldArtifact` v2 (`world_256.anmw`, 36-byte header, FNV-1a 32-bit checksum `0x861B9B50`, 5 layers: elevation, moisture, temperature, flow, biome).
   - `map_manifest.json` compliant with Anima-Engine Draft-07 JSON schema.
   - Production scene export (`ecosystem_map.blend`, `ecosystem_map.glb` at 60 FPS).
   - NavMesh BFS reachability $\ge 80.0\%$ (100% achieved).
   - Offline `viewer.html` with zero external CDN dependencies.
   - 4 visual acceptance renders (Overview, NE, Top-down, Closeup water/cavern).

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Anti-Staircasing Bilateral Filter | 7x7 edge-preserving bilateral filter melting contour terraces while preserving aretes and scarps | M1 | Survey 11-1 |
| 2 | Post-Erosion Taubin/Laplacian Filter | Discrete Laplacian surface relaxation removing micro-rills and single-cell spikes without shrinkage | M1 | Survey 11-1 |
| 3 | C2 Quintic Perlin & Ridged Multi-Fractal | Vectorized 2D gradient noise + RMF producing crisp, jagged alpine rock ribs | M1 | Survey 11-1 |
| 4 | Matterhorn Horn Peak & Arete Synthesis | Pyramidal horn with trihedral knife-edge aretes, glacial cirque headwalls, and cusp profiles | M1 | Survey 11-1 |
| 5 | Accelerated Droplet Hydraulic Erosion | Slice-accelerated droplet erosion (60k-80k droplets) with 2x2 bilinear termination deposition | M1 | Survey 11-1 |
| 6 | Abiotic Preset Anti-Staircasing Config | Set `terrace_enabled: false`, `terrace_blend: 0.0`, and activate RMF + horn peaks | M1 | Survey 11-1 |
| 7 | KarstArch Taxonomy Expansion | Add `KarstArch = 9` to `AbioticType` enum with geological profile | M2 | Survey 11-2 |
| 8 | Meshy AI v2 Batch Ingestion Pipeline | Ingestion CLI generating 4 target assets via Meshy API into Local Asset Vault | M2 | Survey 11-2 |
| 9 | Asset Normalization & LOD Generation | Bottom pivot `min_y=0.0`, metric scaling, cylinder/AABB/convex hull colliders, 3-tier LODs | M2 | Survey 11-2 |
| 10 | Seamless Cave Boolean Carve & Normal Transfer | Boolean difference carve on terrain + flange overlap + `DATA_TRANSFER` normal transfer | M2 | Survey 11-2 |
| 11 | Weathered Granite Crag Deep Embed | Spawn crags with negative embed depth ($-0.8\text{m}$) and surrounding scree talus | M2 | Survey 11-2 |
| 12 | Fluvial Riverbed Boulder Placement | Scatter pebbles/boulders along parabolic channel bed aligned with flow velocity field | M2 | Survey 11-2 |
| 13 | Continuous 4-Tier Hydrology Network | Cascades $\to$ Valley meander $\to$ Central lake $\to$ Outlet gorge and bay | M3 | Survey 11-3 |
| 14 | Parabolic Carved Riverbed & Retaining Berm | Parabolic bed incision + 3D conforming river ribbon + $+1.2\text{m}$ moraine retaining berm | M3 | Survey 11-3 |
| 15 | Optical Depth Water Shader & Contact Foam | Beer-Lambert depth absorption, contact foam margin, flow vectors | M3 | Survey 11-3 |
| 16 | 5-Class Triplanar PBR Strata Shader | Object-space normal-exponent triplanar shader blending bedrock, scree, moss, sand, snow | M4 | Survey 11-3 |
| 17 | 100% Abiotic Integrity Enforcement | Exactly 0% flora, 0% fauna, 0% architecture across meshes, manifests, and presets | M4 | Survey 11-3 |
| 18 | Binary WorldArtifact v2 (.anmw) | 36-byte header, FNV-1a 32-bit checksum, 5 layers, 22 canonical biomes | M5 | Survey 11-3 |
| 19 | Map Manifest Schema (Draft-07) | `map_manifest.json` compliant with schema, matching modelAsset SHA-256 and bytes | M5 | Survey 11-3 |
| 20 | Dual Scene Export (GLB & Blend) | `ecosystem_map.glb` (60 FPS WebGL) and `ecosystem_map.blend` in `assets/blender_map` | M5 | Survey 11-3 |
| 21 | NavMesh BFS Reachability ($\ge 80\%$) | 4-connected BFS reachability validator and safe spawn point definition | M5 | Survey 11-3 |
| 22 | 60 FPS WebGL Offline Viewer | `viewer.html` with zero external CDN dependencies, local Three.js, camera controls | M5 | Survey 11-3 |
| 23 | 4 Visual Acceptance Renders | 1280x720 illuminated renders (Overview, NE angle, Top-down, Closeup water/cavern) | M5 | Survey 11-3 |
| 24 | E2E Integration Test Suite | Tiers 1-4 comprehensive opaque-box test suite passing 100% | M6 | Survey 11-3 |
| 25 | Forensic Integrity Audit | Systematic checks ensuring zero dummy implementations or hardcoded bypasses | M6 | Teamwork Audit |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Organic Topography & Anti-Staircasing | Features 1-6: Bilateral/Laplacian filters, RMF noise, Matterhorn peaks/aretes, accelerated erosion, preset config | none | DONE |
| M2 | Meshy AI v2 Abiotic 3D Generation & Asset Vault | Features 7-12: KarstArch taxonomy, Meshy v2 ingestion, normalizer/LODs, boolean carve, normal transfer, crag/boulder placement | M1 | DONE |
| M3 | Seamless Hydrology & PBR Water | Features 13-15: Continuous 4-tier hydrology, parabolic bed, retaining berm, optical water shader | M1, M2 | DONE |
| M4 | PBR Strata & Abiotic Verification | Features 16-17: 5-class triplanar PBR strata shader, micro-roughness, 100% abiotic enforcement | M1, M3 | DONE |
| M5 | Anima-Engine Parity & 60 FPS WebGL Deliverables | Features 18-23: WorldArtifact v2 (.anmw), manifest, GLB & blend export, 60 FPS viewer, NavMesh BFS >=80%, 4 renders | M3, M4 | DONE |
| M6 | Final E2E Verification & Forensic Integrity Audit | Features 24-25: 100% pass of E2E test suite (Tiers 1-4 + Tier 5) + Forensic Auditor certification | M5 | DONE |

---

## Interface Contracts

### M1 ↔ M2 (Heightfield & Asset Integration)
- Heightfield array: `hf.Z` (shape `(256, 256)`, float64 in world coordinates $[0.0, 30.0]\text{m}$).
- Feature invariants: 0 terrace step contours on mountain slopes; cliff faces maintain sharp slope gradient $|\nabla Z| > 1.0$.
- Cave entrance site: `config.cavern.entrance_pos` coordinates $(x_e, y_e, z_e)$ where cliff wall is localized.

### M2 ↔ M3 (Asset Vault & Scene Assembly)
- Vault entries: `LocalAssetVault` index contains validated entries for `RockCrag`, `KarstArch`, `Stalactite`, `Stalagmite`, `RiverPebble`.
- Normalized geometry contract: All meshes satisfy `min_y == 0.0`, metric scaling, collision primitives, and LOD0/1/2.
- Placement contract: Boulders placed along river spline where `water_depth > 0.0` and `flow > 0.3`.

### M3 ↔ M4 (Hydrology & Shading)
- Conforming water ribbon: `Water_River_Meander` hugs heightfield bed with $0.08\text{m} - 0.20\text{m}$ clearance, smoothstep into `lake_level`.
- Lake cradle: Moraine retaining berm crests at $\text{lake\_level} + 1.2\text{m}$.
- PBR material coupling: Shaders sample `moisture`, `sediment`, `scree_talus`, and `water_depth` layers.

### M4 ↔ M5 (Scene Delivery & Data Standards)
- Binary export: `WorldArtifact(width=256, height=256, sea_level=0.0, world_scale=200.0, layers=[elevation, moisture, temp, flow, biome])`.
- Checksum: FNV-1a 32-bit computed over bytes 36 to EOF.
- Scene delivery: `assets/blender_map/ecosystem_map.glb` ($\le 10\text{MB}$, $\le 300\text{k}$ tris, 60 FPS) and `assets/blender_map/ecosystem_map.blend`.
- NavMesh contract: 4-connected BFS reachability over walkable land cells $\ge 80.0\%$.

---

## Code Layout
- `E:\tool\mcp\terra_forge\terra_forge\core\`: `heightfield.py`, `erosion.py`, `hydrology.py`, `world_artifact.py`, `manifest.py`.
- `E:\tool\mcp\terra_forge\terra_forge\ai\`: `meshy_client.py`, `vault.py`, `normalizer.py`, `lod.py`.
- `E:\tool\mcp\terra_forge\terra_forge\blender\`: `runner.py`, `mesh_builder.py`, `water_builder.py`, `cave_builder.py`, `shaders.py`, `exporter.py`.
- `E:\tool\mcp\terra_forge\terra_forge\schema\presets\`: `genesis_primordial_abiotic.json`.
- `E:\tool\mcp\terra_forge\terra_forge\navigation\`: `navmesh.py`.
- `e:\Project\01_AI_Agents\Genesis_Zero\assets\blender_map\`: `ecosystem_map.glb`, `ecosystem_map.blend`, `viewer.html`, acceptance renders.
- `e:\Project\01_AI_Agents\Genesis_Zero\assets\`: `world_256.anmw`, `map_manifest.json`.
- `E:\tool\mcp\terra_forge\tests\`: Unit, integration, E2E, and regression test suites.

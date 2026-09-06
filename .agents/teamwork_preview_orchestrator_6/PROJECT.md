# Project: Genesis Zero — Botanical Research & 3D Modeling Pipeline

## Architecture Overview
The Genesis Zero Botanical Research and 3D Modeling Pipeline establishes an end-to-end photorealistic ecological asset generation and verification system. It unifies international botanical taxonomy standards (APG IV, POWO Kew, WFO, GBIF, CoL, vncreatures), standardized multi-angle visual reference generation (4-angle Turnarounds), automated Blender 3D procedural modeling with biological PBR/SSS shaders, master catalog documentation sync, real-time Web 3D viewing, and zero-defect automated testing.

```
+---------------------------------------------------------------------------------------------------+
|                                  R1: Botanical Taxonomy Layer                                     |
|  International APG IV Standardization | Databases: POWO Kew, WFO, GBIF, CoL, vncreatures          |
|  6 Ecological Layers: Canopy, Shrubs/Ferns, Herbs/Wildflowers, Aquatic, Succulents, Endemic       |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                 R2: Visual Reference Layer                                        |
|  Standardized 4-Angle Turnaround Concept Sheets (web/flora_images/<species_slug>_turnaround.jpg)  |
|  Upper 55%: 3/4 Front Perspective Hero View | Lower 40%: Front, Side, Top-Down Orthographic       |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                  R3: 3D Asset Engine (Blender)                                    |
|  Clean Quad-Dominant Manifold Topology (0 ngons, 100% smooth shading, 0 loose vertices)           |
|  Biological PBR Materials: Foliage/Petal SSS (translucency) + Procedural Trunk/Bark Bump          |
|  Dual Export: Master .blend (assets/flora/<cat>/<slug>.blend) + glTF 2.0 .glb                     |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                R4: Catalog & Web Viewer Layer                                     |
|  Master Catalog: docs/flora/README.md & Species Specs: docs/flora/species/<slug>.md               |
|  Web Viewer: web/flora_viewer.html ('4 Góc 📷' badge, Turnaround modal, Three.js 360° viewport)   |
|  Offline Base64 Model Store: web/flora_models_data.js                                             |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                            R5: Automated Verification & Audit Suite                               |
|  CLI Runner: python scripts/verify_flora_pipeline.py | Pytest: tests/test_flora_assets.py        |
|  glTF 2.0 Binary Validation | Image Verification | Metadata Integrity | Exit Code 0               |
+---------------------------------------------------------------------------------------------------+
```

## Feature Inventory
Every feature identified during the Survey phase is mapped to an assigned milestone:

| # | Feature | Description | Milestone | Source | Status |
|---|---------|-------------|-----------|--------|--------|
| 1 | APG IV Molecular Taxonomy | Standardization of order, family, genus, species binomial & author citations | M1 | Survey 1 | DONE |
| 2 | Open Database Cross-Referencing | Persistent IDs from POWO Kew, WFO, GBIF, CoL, and vncreatures | M1 | Survey 1 | DONE |
| 3 | 6-Tier Ecological Stratification | Coverage of Canopy, Shrubs/Ferns, Herbs/Flowers, Aquatic, Succulents, Endemic | M1 | Survey 1 | DONE |
| 4 | Species Markdown Specifications | Detailed anatomy, dimensions, relative links in docs/flora/species/<slug>.md | M1 | Survey 1 | DONE |
| 5 | Master Catalog Table Update | Comprehensive APG IV & database ID cross-reference table in docs/flora/README.md | M1 | Survey 1 | DONE |
| 6 | 4-Angle Turnaround Format | Upper 55% 3/4 perspective, lower 40% 3 orthographic views (Front/Side/Top) | M2 | Survey 3 | DONE |
| 7 | Turnaround Sheet Asset Presence | Valid 1024x1024 JPEG files in web/flora_images/<slug>_turnaround.jpg | M2 | Survey 3 | DONE |
| 8 | Pitcher Plant Mesh Remediation | Remove/remediate 18 loose tendril vertices in flora_builder.py & regenerate | M3 | Survey 2 | DONE |
| 9 | Quad-Dominant Manifold Topology | 0 ngons, 0 loose vertices, 0 non-manifold edges, 100% smooth shading | M3 | Survey 2 | DONE |
| 10 | Biological PBR Materials | Principled BSDF with SSS (subsurface weight 0.35-0.65) and procedural bark bump | M3 | Survey 2 | DONE |
| 11 | Dual .blend & .glb Export | Export valid .blend and glTF 2.0 .glb to assets/flora/<cat>/<slug>.* | M3 | Survey 2 | DONE |
| 12 | glTF 2.0 Binary Conformance | glTF magic, version 2, JSON chunk 0, BIN chunk 1, valid buffer views | M3 | Survey 2 | DONE |
| 13 | Web Viewer '4 Góc 📷' Badges | Render badge on plant cards with turnaround images in web/flora_viewer.html | M4 | Survey 3 | DONE |
| 14 | Turnaround Sheet Modal Popup | Interactive dialog modal displaying full turnaround sheet with metadata | M4 | Survey 3 | DONE |
| 15 | Three.js 360° Real-time Viewport | Orbit controls, turntable auto-rotation, wireframe, Studio/Sunset/Night lights | M4 | Survey 3 | DONE |
| 16 | Offline Base64 Data Sync | Update web/flora_models_data.js with latest GLB binaries (including weeping willow) | M4 | Survey 3 | DONE |
| 17 | Standalone Verification CLI | scripts/verify_flora_pipeline.py validating metadata, images, 3D, and web | M5 | Survey 3 | DONE |
| 18 | Automated Pytest Suite | tests/test_flora_assets.py integrated into project test harness with Exit Code 0 | M5 | Survey 3 | DONE |
| 19 | Zero False Negatives in Tests | Accommodate Blender 5.2.1 LTS zstandard compressed .blend headers (0x28B52FFD) | M5 | Survey 3 | DONE |
| 20 | Adversarial & Forensic Integrity | Zero tolerance for dummy implementations, verifying genuine assets & logic | M5 | Survey 2,3 | DONE |

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Botanical Taxonomy & Catalog Sync | Standardize APG IV taxonomy & cross-reference IDs (POWO, WFO, GBIF, CoL, vncreatures) for 10 core + 2 supplementary species across 6 ecological tiers. Update docs/flora/species/<slug>.md and docs/flora/README.md. | Survey complete | DONE |
| M2 | Visual Reference Turnaround Validation | Verify and ensure standardized 4-angle turnaround concept sheets in web/flora_images/<slug>_turnaround.jpg and docs/flora/images/. | M1 | DONE |
| M3 | 3D Mesh Remediation & Blender PBR Pipeline | Remediate 18 loose vertices in carnivorous_pitcher_plant in flora_builder.py and 1,980 incontiguous edges in weeping willow; regenerate .blend & .glb; verify 100% smooth shading, quad dominance, SSS materials, and glTF 2.0 binary chunks. | M1 | DONE |
| M4 | Web Viewer & Base64 Data Sync | Synchronize web/flora_viewer.html data model, '4 Góc 📷' badge logic, turnaround sheet modal, Three.js 360° viewport, and refresh web/flora_models_data.js base64 data to byte-exact parity. | M2, M3 | DONE |
| M5 | Automated Verification Suite & QA | Create scripts/verify_flora_pipeline.py and tests/test_flora_assets.py. Verify metadata integrity, images, .blend and .glb files, glTF 2.0 validation, and web viewer sync with Exit Code 0. | M1, M2, M3, M4 | DONE |

## Code Layout
- `docs/flora/README.md`: Master Botanical Catalog and APG IV Cross-Reference Table
- `docs/flora/species/<slug>.md`: Per-species morphological, anatomical, and PBR markdown specification
- `docs/flora/images/<slug>_turnaround.jpg`: High-resolution turnaround concept sheets
- `web/flora_images/<slug>_turnaround.jpg`: Web-accessible turnaround sheets
- `web/flora_viewer.html`: Interactive Three.js 3D flora inspector and turnaround modal
- `web/flora_models_data.js`: Offline base64 binary glTF model store
- `assets/flora/<category>/<slug>.blend`: Master Blender 5.2.1 LTS source files with procedural shaders
- `assets/flora/<category>/<slug>.glb`: Runtime glTF 2.0 binary models with embedded PBR factors
- `assets/flora/generators/flora_builder.py`: Procedural Blender geometry and material generation engine
- `assets/flora/generators/generate_willow_realistic.py`: Remediated high-detail willow generator
- `scripts/verify_flora_pipeline.py`: Standalone CLI verification script (90/90 checks pass, Exit Code 0)
- `tests/test_flora_assets.py`: Pytest automated verification suite (61/61 tests pass, Exit Code 0)

## Target Species Matrix (10 Core + 2 Supplementary Across 6 Ecological Layers)
1. **Canopy Megatrees**:
   - `canopy_ancient_oak`: *Quercus robur* L. (POWO: 296681-1, GBIF: 2878688)
   - `canopy_giant_sequoia`: *Sequoiadendron giganteum* (Lindl.) J.Buchholz (POWO: 263309-1, GBIF: 2684031)
   - `canopy_baobab`: *Adansonia digitata* L. (POWO: 558628-1, GBIF: 3152222)
   - `canopy_weeping_willow`: *Salix babylonica* L. (POWO: 778931-1, GBIF: 5372958)
2. **Shrubs & Ferns**:
   - `understory_tree_fern`: *Cyathea cooperi* (F.Muell.) Domin (POWO: 17068550-1, GBIF: 7299946, vncreatures VNC0422)
3. **Aquatic & Wetland**:
   - `aquatic_water_lily`: *Nymphaea alba* L. (POWO: 605417-1, GBIF: 2882443)
   - `aquatic_sacred_lotus`: *Nelumbo nucifera* Gaertn. (POWO: 605335-1, GBIF: 2888881, vncreatures VNC0198)
4. **Desert & Succulents**:
   - `succulent_saguaro_cactus`: *Carnegiea gigantea* (Engelm.) Britton & Rose (POWO: 62495-2, GBIF: 3084347)
5. **Carnivorous & Bioluminescent Cave**:
   - `carnivorous_venus_flytrap`: *Dionaea muscipula* J.Ellis (POWO: 321332-1, GBIF: 3190710)
   - `carnivorous_pitcher_plant`: *Nepenthes rajah* Hook.f. (POWO: 603798-1, GBIF: 3702131, vncreatures VNC0318)
   - `cave_bioluminescent_mushroom`: *Mycena chlorophos* (Berk. & M.A.Curtis) Sacc. (IndexFungorum: 198547, GBIF: 2527097)
6. **Endemic & Wildflower Layers (Supplementary)**:
   - `grass_alpine_tussock` / Wildflower: *Leucanthemum vulgare* Lam. (GBIF: 3142270)
   - Endemic Vietnam: *Paphiopedilum vietnamense* O.Gruss & Perner (vncreatures: VNC0014, GBIF: 2818985)

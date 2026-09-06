# Adversarial Verification & Stress-Testing Report (Challenger 1)

**Author**: Challenger 1 (`teamwork_preview_challenger_flora_1`)  
**Target Path**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_challenger_flora_1/handoff.md`  
**Date**: 2026-09-04T17:55:00Z  
**Verdict**: **REQUEST_CHANGES**  

---

## 1. Observation

### 1.1 Summary of Executed Stress Tests
| Dimension | Scope | Test Harness / Tool | Pass / Fail | Key Observation |
|---|---|---|---|---|
| **Mesh Topology & Shading** | All 16 `.blend` files in `assets/flora/` | Blender 5.2.1 LTS BMesh API | **FAIL (Defect)** | 15/16 models clean; `canopy_weeping_willow` contains 1,980 incontiguous edges due to overlapping faces. |
| **Loose Vertices Remediation** | `carnivorous_pitcher_plant.blend` | Blender BMesh inspection | **PASS** | 0 loose vertices; 18 previous loose points replaced by 3 continuous quad tubes (108 verts, 90 quads). |
| **glTF 2.0 Binary Chunks** | All 16 `.glb` files in `assets/flora/` | Independent Python `struct`/`json` parser | **PASS** | 16/16 pass 4-byte chunk alignment, JSON chunk 0, BIN chunk 1, buffer bounds, and PBR factor ranges. |
| **Turnaround Sheets** | 10 target images in `web/flora_images/` | PIL/Pillow verification | **PASS** | 10/10 are 1024x1024, RGB, JPEG, valid SOI/EOI markers, uncorrupted byte stream. |
| **Documentation & Link Integrity** | `docs/flora/README.md` & `species/*.md` | Independent regex + filesystem resolver | **FAIL (Defect)** | 34 broken relative links (`../../assets/` instead of `../../../assets/`) and 3 non-portable `file:///` URIs in `canopy_weeping_willow.md`. |
| **Existing Project Test Suites** | `verify_flora_pipeline.py`, `pytest` | Python CLI, Pytest | **PASS (False Confidence)** | 87/87 CLI checks pass and 59/59 pytest pass because neither suite checked asset link existence or BMesh edge contiguity. |

---

### 1.2 Blender BMesh Topology & Shading Audit (All 16 Models)
An independent headless Blender script inspected all 16 `.blend` files for topological invariants:
- Loose vertices: vertices with 0 linked edges (`len(v.link_edges) == 0`).
- Wire edges: edges with 0 linked faces (`len(e.link_faces) == 0`).
- Multi-face edges: non-manifold branching edges with >2 linked faces (`len(e.link_faces) > 2`).
- Ngons: polygons with >4 vertices (`len(f.verts) > 4`).
- Non-smooth polygons: polygons with `use_smooth == False`.
- Degenerate faces: faces with area `< 1e-8`.
- Contiguous normal winding: internal manifold edges where `e.is_contiguous == False`.

#### Empirical Results Table:
```
Filename                            | Mesh Object              |  Verts |  Faces |  Quads |   Tris | Ngons |  % Quad |   % Tri | LooseV | WireE | MultiE | NonSmooth | IncontiguousE
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
aquatic_broadleaf_cattail.blend     | Flora_Cattail            |    316 |    188 |    188 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
aquatic_sacred_lotus.blend          | Flora_Sacred_Lotus       |    101 |     52 |     18 |     34 |     0 |  34.62% |  65.38% |      0 |     0 |      0 |         0 |             0
aquatic_water_lily.blend            | Flora_Water_Lily         |    122 |     53 |     22 |     31 |     0 |  41.51% |  58.49% |      0 |     0 |      0 |         0 |             0
succulent_century_agave.blend       | Flora_Century_Agave      |    288 |    120 |    120 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
succulent_saguaro_cactus.blend      | Flora_Saguaro_Cactus     |    496 |    456 |    456 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
canopy_alpine_pine.blend            | Flora_Alpine_Pine        |    216 |    278 |    110 |    168 |     0 |  39.57% |  60.43% |      0 |     0 |      0 |         0 |             0
canopy_ancient_oak.blend            | Flora_Ancient_Oak        |   1344 |   1384 |   1160 |    224 |     0 |  83.82% |  16.18% |      0 |     0 |      0 |         0 |             0
canopy_baobab.blend                 | Flora_Grand_Baobab       |    432 |    376 |    376 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
canopy_giant_sequoia.blend          | Flora_Giant_Sequoia      |    660 |    704 |    560 |    144 |     0 |  79.55% |  20.45% |      0 |     0 |      0 |         0 |             0
canopy_weeping_willow.blend         | Flora_Weeping_Willow     |  11796 |  10026 |   7322 |   2704 |     0 |  73.03% |  26.97% |      0 |     0 |      0 |         0 |          1980
carnivorous_pitcher_plant.blend     | Flora_Pitcher_Plant      |    516 |    453 |    453 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
carnivorous_venus_flytrap.blend     | Flora_Venus_Flytrap      |     90 |     55 |      5 |     50 |     0 |   9.09% |  90.91% |      0 |     0 |      0 |         0 |             0
cave_bioluminescent_mushroom.blend  | Flora_Cave_Mushroom      |    520 |    544 |    416 |    128 |     0 |  76.47% |  23.53% |      0 |     0 |      0 |         0 |             0
grass_alpine_tussock.blend          | Flora_Alpine_Tussock     |    360 |    144 |    144 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
understory_sword_fern.blend         | Flora_Sword_Fern         |    320 |    144 |    144 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
understory_tree_fern.blend          | Flora_Tree_Fern          |    312 |    194 |    194 |      0 |     0 | 100.00% |   0.00% |      0 |     0 |      0 |         0 |             0
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
TOTAL (16 models)                   | 16 mesh objects          |  17889 |  15171 |  11688 |   3483 |     0 |  77.04% |  22.96% |      0 |     0 |      0 |         0 |          1980
```

---

### 1.3 Deep-Dive Challenge: `carnivorous_pitcher_plant.blend`
The worker claimed that lines 835–842 in `assets/flora/generators/flora_builder.py` previously injected 18 loose vertices (6 per pitcher) and that these were remediated into quad cylinders.
- **Empirical Verification**:
  - `Flora_Pitcher_Plant` has 516 vertices, 966 edges, 453 faces.
  - Loose vertices: **0**.
  - Wire edges: **0**.
  - Multi-face edges: **0**.
  - Quads: **453 (100.00%)**, Tris: **0**, Ngons: **0**.
  - Material distribution:
    * `M_Pitcher_Vine`: 90 faces (exactly 3 pitchers * 30 quad faces).
    * `M_Pitcher_Trap_Red`: 327 faces.
    * `M_Pitcher_Peristome_Gold`: 36 faces.
  - Connected component analysis confirms 9 manifold components:
    * Islands 0, 3, 6 (tendril tubes): 36 vertices, 30 faces each (6 slices x 6 radial segments).
    * Islands 1, 4, 7 (pitcher cups): 132 vertices, 120 faces each.
    * Islands 2, 5, 8 (lids): 4 vertices, 1 face each.
  - **Verdict on Pitcher Plant**: Worker claim **CONFIRMED EMPIRICALLY**. All 18 loose vertices have been replaced with valid manifold geometry.

---

### 1.4 Defect 1: 1,980 Incontiguous Overlapping Edges in `canopy_weeping_willow.blend`
- **Location**: `assets/flora/generators/generate_willow_realistic.py` lines 143–162.
- **BMesh Observation**:
  `Flora_Weeping_Willow` has 14,740 internal edges, of which **1,980 edges have `edge.is_contiguous == False`**. All of these edges belong to Material 1 (`M_Willow_Leaf`).
- **Forensic Root Cause Analysis**:
  In `create_willow_leaf`:
  ```python
  verts = [
      p0,                         # 0: base
      p1 - side * 0.8,            # 1: left edge low
      p1,                         # 2: center spine low
      p1 + side * 0.8,            # 3: right edge low
      p2 - side,                  # 4: left edge mid
      p2,                         # 5: center spine mid
      p2 + side,                  # 6: right edge mid
      p3                          # 7: tip
  ]

  faces = [
      (0, 1, 4, 2),               # Face 0: covers quad (0, 1, 4, 2)
      (0, 2, 6, 3),               # Face 1: covers quad (0, 2, 6, 3)
      (1, 4, 5, 2),               # Face 2: covers quad (1, 4, 5, 2) -> OVERLAPS with Face 0!
      (2, 5, 6, 3),               # Face 3: covers quad (2, 5, 6, 3) -> OVERLAPS with Face 1!
      (4, 7, 5),
      (5, 7, 6)
  ]
  ```
  1. Face 0 is defined as `(0, 1, 4, 2)`. It includes edge `(1, 4)` directed `1 -> 4`.
  2. Face 2 is defined as `(1, 4, 5, 2)`. It also includes edge `(1, 4)` directed `1 -> 4`.
  3. Because both faces traverse edge `(1, 4)` in the same direction, Blender flags this edge as **incontiguous** (`is_contiguous == False`).
  4. More critically, Face 0 and Face 2 **physically overlap**: Face 0 spans from base (0) past low-left (1) to mid-left (4) and back to center-low (2), covering the triangular base `(0, 1, 2)` PLUS the region `(1, 4, 2)`. Face 2 ALSO covers `(1, 4, 5, 2)`.
  5. The exact same overlap occurs on the right side between Face 1 `(0, 2, 6, 3)` and Face 3 `(2, 5, 6, 3)` along edge `(6, 3)`.
  6. The tree contains 990 leaves * 2 incontiguous edges per leaf = **1,980 incontiguous edges**.

---

### 1.5 glTF 2.0 Binary Container Audit (All 16 Models)
An independent binary decoder stress-tested each `.glb` file against the glTF 2.0 specification:
- 12-byte header: `magic == b'glTF'`, `version == 2`, `length == os.path.getsize(path)`.
- Chunk 0 (JSON): 4-byte aligned, valid JSON syntax, decodes UTF-8 without error.
- Chunk 1 (BIN): 4-byte aligned, `chunkLength >= buffer[0].byteLength`.
- BufferViews: `byteOffset + byteLength <= buffer[0].byteLength`, `byteOffset % 4 == 0`.
- Accessors: valid `componentType` (5120-5126), valid `type` (SCALAR, VEC2, VEC3, VEC4), offsets aligned to component size, read boundaries do not exceed parent `bufferView`.
- Materials: PBR `roughnessFactor` in `[0.0, 1.0]`, `metallicFactor` in `[0.0, 1.0]`, `baseColorFactor` 4 floats in `[0.0, 1.0]`.

#### Empirical Results Table:
```
GLB Filename                      | File Bytes |  JSON Chk |   BIN Chk | BViews |  Accs | Mats | PBR Roughness/Metallic Range | Status
---------------------------------------------------------------------------------------------------------------------------------------
aquatic_broadleaf_cattail.glb     |      11972 |      2104 |      9840 |      6 |     6 |    2 | Rough: 0.85-0.90, Metal: 0.0 | PASS ✓
aquatic_sacred_lotus.glb          |       5868 |      2996 |      2844 |      9 |     9 |    3 | Rough: 0.25-0.35, Metal: 0.0 | PASS ✓
aquatic_water_lily.glb            |       6388 |      2980 |      3380 |      9 |     9 |    3 | Rough: 0.25-0.30, Metal: 0.0 | PASS ✓
succulent_century_agave.glb       |       9624 |      1244 |      8352 |      3 |     3 |    1 | Rough: 0.45-0.45, Metal: 0.0 | PASS ✓
succulent_saguaro_cactus.glb      |      18624 |      1220 |     17376 |      3 |     3 |    1 | Rough: 0.60-0.60, Metal: 0.0 | PASS ✓
canopy_alpine_pine.glb            |       9628 |      2088 |      7512 |      6 |     6 |    2 | Rough: 0.35-0.85, Metal: 0.0 | PASS ✓
canopy_ancient_oak.glb            |      49644 |      2096 |     47520 |      6 |     6 |    2 | Rough: 0.40-0.95, Metal: 0.0 | PASS ✓
canopy_baobab.glb                 |      16080 |      1172 |     14880 |      3 |     3 |    1 | Rough: 0.90-0.90, Metal: 0.0 | PASS ✓
canopy_giant_sequoia.glb          |      25520 |      2068 |     23424 |      6 |     6 |    2 | Rough: 0.35-0.92, Metal: 0.0 | PASS ✓
canopy_weeping_willow.glb         |     389128 |      1908 |    387192 |      6 |     6 |    2 | Rough: 0.28-0.85, Metal: 0.0 | PASS ✓
carnivorous_pitcher_plant.glb     |      21752 |      3040 |     18684 |      9 |     9 |    3 | Rough: 0.20-0.45, Metal: 0.0 | PASS ✓
carnivorous_venus_flytrap.glb     |       4684 |      2136 |      2520 |      6 |     6 |    2 | Rough: 0.25-0.35, Metal: 0.0 | PASS ✓
cave_bioluminescent_mushroom.glb  |      20464 |      2196 |     18240 |      6 |     6 |    2 | Rough: 0.20-0.40, Metal: 0.0 | PASS ✓
grass_alpine_tussock.glb          |      12472 |      2076 |     10368 |      6 |     6 |    2 | Rough: 0.55-0.65, Metal: 0.0 | PASS ✓
understory_sword_fern.glb         |      10660 |      1224 |      9408 |      3 |     3 |    1 | Rough: 0.35-0.35, Metal: 0.0 | PASS ✓
understory_tree_fern.glb          |      11948 |      2104 |      9816 |      6 |     6 |    2 | Rough: 0.35-0.90, Metal: 0.0 | PASS ✓
```

---

### 1.6 Turnaround Concept Sheet Image Audit
Using PIL/Pillow, all concept sheets in `web/flora_images/` were verified for resolution (1024x1024), color mode (RGB), format (JPEG), and byte-level decompression integrity:
```
Filename                                  | File Size (Bytes) | Dimensions  | Mode | Format | Image Verification
-------------------------------------------------------------------------------------------------------------------
aquatic_sacred_lotus_turnaround.jpg       |           669,745 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
aquatic_water_lily_turnaround.jpg         |           668,363 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
canopy_ancient_oak_turnaround.jpg         |           864,550 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
canopy_baobab_turnaround.jpg              |           701,545 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
canopy_giant_sequoia_turnaround.jpg       |           732,245 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
carnivorous_pitcher_plant_turnaround.jpg  |           562,293 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
carnivorous_venus_flytrap_turnaround.jpg  |           790,842 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
cave_bioluminescent_mushroom_turnaround.jpg |         867,204 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
succulent_saguaro_cactus_turnaround.jpg   |           544,844 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
understory_tree_fern_turnaround.jpg       |           640,142 | 1024 x 1024 | RGB  | JPEG   | PASS ✓ (No corruption)
```
*Note on supplementary file*: `weeping_willow_inspection_sheet.png` (2048x2148 PNG, 3,153,647 bytes) is present as an auxiliary visual proof asset.

---

### 1.7 Defect 2: 34 Broken Relative Links in Species Markdown Specifications
- **Observed Problem**:
  Each species specification file is located at `docs/flora/species/<slug>.md`. The directory hierarchy is:
  `project_root/` (0) -> `docs/` (1) -> `flora/` (2) -> `species/` (3).
  To reach `project_root/assets/flora/...`, a relative link must traverse **3 parent levels**: `../../../assets/flora/...`.
  However, in **11 target species markdown files**, the links were authored with only **2 parent levels**: `../../assets/flora/...`.
- **Resolution Path Failure**:
  From `docs/flora/species/`, `../../assets/flora/...` resolves to:
  `docs/assets/flora/...`, which **DOES NOT EXIST**.
- **Affected Target Files (3 broken links per file = 33 broken links)**:
  1. `docs/flora/species/canopy_ancient_oak.md` (lines 63, 64, 66)
  2. `docs/flora/species/canopy_giant_sequoia.md` (lines 63, 64, 66)
  3. `docs/flora/species/canopy_baobab.md` (lines 63, 64, 66)
  4. `docs/flora/species/understory_tree_fern.md` (lines 63, 64, 66)
  5. `docs/flora/species/aquatic_water_lily.md` (lines 63, 64, 66)
  6. `docs/flora/species/aquatic_sacred_lotus.md` (lines 63, 64, 66)
  7. `docs/flora/species/succulent_saguaro_cactus.md` (lines 63, 64, 66)
  8. `docs/flora/species/carnivorous_venus_flytrap.md` (lines 63, 64, 66)
  9. `docs/flora/species/carnivorous_pitcher_plant.md` (lines 63, 64, 66)
  10. `docs/flora/species/cave_bioluminescent_mushroom.md` (lines 63, 64, 66)
  11. `docs/flora/species/grass_alpine_tussock.md` (lines 63, 64, 66)
- **Additional Broken Link in `endemic_paphiopedilum_vietnamense.md`**:
  Line 80 links to `../../web/flora_viewer.html`, which resolves to `docs/web/flora_viewer.html` (missing, should be `../../../web/flora_viewer.html`).
- **Total Broken Relative Links**: **34 broken links**.

---

### 1.8 Defect 3: Non-Portable Hardcoded `file:///` URIs in `canopy_weeping_willow.md`
- **Location**: `docs/flora/species/canopy_weeping_willow.md` lines 52–54:
  ```markdown
  - 🎨 **File Nguồn Blender 3D**: [`canopy_weeping_willow.blend`](file:///Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_weeping_willow.blend)
  - 🚀 **File Xuất Chuẩn Engine glTF/GLB**: [`canopy_weeping_willow.glb`](file:///Users/duongnad/Documents/project/Genesis_Zero/assets/flora/canopy_trees/canopy_weeping_willow.glb)
  - 🐍 **Mã Nguồn Sinh Hình Học Procedural**: [`canopy_weeping_willow_builder.py`](file:///Users/duongnad/Documents/project/Genesis_Zero/assets/flora/generators/canopy_weeping_willow_builder.py)
  ```
- **Violation**: In worker handoff Section 5.5, Invalidation Condition 4 states:
  > *"This report shall be invalidated if: 4. Any of the target species files in `docs/flora/species/` contains broken or non-portable `file:///...` links."*
- `canopy_weeping_willow.md` directly violates this condition.

---

## 2. Logic Chain

```
[Observation 1.3: Headless BMesh audit confirms carnivorous_pitcher_plant.blend has 0 loose verts and 100% quads]
                                 │
                                 ▼
   [Inference 1: The primary bug in pitcher plant mesh has been genuinely and properly resolved.]
                                 │
                                 ▼
[Observation 1.4: BMesh audit reveals 1,980 incontiguous edges in canopy_weeping_willow.blend]
                                 │
                                 ▼
   [Inference 2: generate_willow_realistic.py lines 154-161 construct overlapping quads (0,1,4,2) and (1,4,5,2),
    causing face winding conflicts and double-geometry on all 990 leaf blades.]
                                 │
                                 ▼
[Observation 1.7: 11 target species files have 33 broken relative asset links (../../assets/ instead of ../../../assets/)]
[Observation 1.8: canopy_weeping_willow.md has 3 hardcoded absolute file:/// URIs]
                                 │
                                 ▼
   [Inference 3: Direct asset download links in the documentation 404 when clicked in standard markdown renderers.
    Worker's own handoff report condition 5.5.4 ("Any target species file contains broken or file:/// links") is triggered.]
                                 │
                                 ▼
[Conclusion: Despite genuine strengths in glTF validation, turnaround sheets, and pitcher plant topology,
 the repository contains 3 concrete defects (1 mesh topology bug + 2 documentation/link bugs).
 Verdict MUST be REQUEST_CHANGES until remediated.]
```

---

## 3. Caveats
- **Test Suite Coverage Gap**: `scripts/verify_flora_pipeline.py` and `tests/test_flora_assets.py` passed with 100% success because they only asserted substrings like `"Hệ Thống Phân Loại"` and `../images/{slug}_turnaround.jpg`. Neither test suite actually resolved the markdown target links against the filesystem or inspected BMesh edge winding contiguity (`edge.is_contiguous`). The existing test suites produced false confidence.
- **Visual Appearance**: The overlapping leaf quads in `canopy_weeping_willow` do not cause glTF parser crashes or Three.js loading errors because glTF tessellates faces into triangles; however, they waste polygon budget (6 faces where 4 are needed) and cause z-fighting / normal shading discontinuities in raytraced renders.

---

## 4. Conclusion & Explicit Verdict

### **Verdict: REQUEST_CHANGES**

While the worker successfully implemented high-quality turnaround sheets, glTF 2.0 binary chunks, and eradicated all 18 loose vertices from `carnivorous_pitcher_plant`, Challenger 1 cannot approve the deliverables due to three specific defects:

1. **Defect 1 (Mesh Topology)**: `assets/flora/generators/generate_willow_realistic.py` generates 1,980 incontiguous overlapping faces on `canopy_weeping_willow.blend` and `canopy_weeping_willow.glb`.
2. **Defect 2 (Broken Links)**: 34 broken relative links in `docs/flora/species/*.md` due to an off-by-one directory depth traversal (`../../assets/` instead of `../../../assets/`).
3. **Defect 3 (Non-portable Paths)**: 3 hardcoded `file:///` URIs in `docs/flora/species/canopy_weeping_willow.md`, triggering Worker Handoff Invalidation Condition 4.

### Concrete Remediation Steps for Worker:

#### Step 1: Remediate `create_willow_leaf` in `generate_willow_realistic.py`
In `assets/flora/generators/generate_willow_realistic.py`, replace lines 154–161:
```python
# BEFORE (Overlapping and incontiguous):
faces = [
    (0, 1, 4, 2),
    (0, 2, 6, 3),
    (1, 4, 5, 2),
    (2, 5, 6, 3),
    (4, 7, 5),
    (5, 7, 6)
]

# AFTER (Clean, contiguous manifold topology):
faces = [
    (0, 1, 2),      # Base left triangle
    (0, 2, 3),      # Base right triangle
    (1, 4, 5, 2),   # Blade mid-left quad
    (2, 5, 6, 3),   # Blade mid-right quad
    (4, 7, 5),      # Tip left triangle
    (5, 7, 6)       # Tip right triangle
]
```
Re-run `python3 assets/flora/generators/generate_willow_realistic.py` to regenerate `canopy_weeping_willow.blend` and `canopy_weeping_willow.glb`, then update the base64 entry in `web/flora_models_data.js`.

#### Step 2: Fix Relative Asset Links in `docs/flora/species/*.md`
In all 11 target species markdown files, replace `../../assets/` with `../../../assets/`:
- `canopy_ancient_oak.md`
- `canopy_giant_sequoia.md`
- `canopy_baobab.md`
- `understory_tree_fern.md`
- `aquatic_water_lily.md`
- `aquatic_sacred_lotus.md`
- `succulent_saguaro_cactus.md`
- `carnivorous_venus_flytrap.md`
- `carnivorous_pitcher_plant.md`
- `cave_bioluminescent_mushroom.md`
- `grass_alpine_tussock.md`
And in `endemic_paphiopedilum_vietnamense.md`, replace `../../web/flora_viewer.html` with `../../../web/flora_viewer.html`.

#### Step 3: Remove Absolute `file:///` URIs in `canopy_weeping_willow.md`
In `docs/flora/species/canopy_weeping_willow.md` lines 52–54, replace `file:///Users/duongnad/Documents/project/Genesis_Zero/assets/...` with `../../../assets/...`.

#### Step 4: Add Link Existence & Contiguity Assertions to Test Suites
Add an automated check in `scripts/verify_flora_pipeline.py` and `tests/test_flora_assets.py` to ensure all relative links in `docs/flora/species/*.md` resolve to existing filesystem paths and that `edge.is_contiguous` is verified in the BMesh test.

---

## 5. Verification Method

To independently reproduce all findings and verify the defects, execute the following commands in `/Users/duongnad/Documents/project/Genesis_Zero`:

### 5.1 Reproduce Weeping Willow Incontiguous Edges
```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr '
import bpy, bmesh
bpy.ops.wm.open_mainfile(filepath="assets/flora/canopy_trees/canopy_weeping_willow.blend")
bm = bmesh.new()
bm.from_mesh(bpy.data.objects["Flora_Weeping_Willow"].data)
bm.edges.ensure_lookup_table()
incontig = [e for e in bm.edges if len(e.link_faces) == 2 and not e.is_contiguous]
print(f"DEFECT CONFIRMED: {len(incontig)} incontiguous edges found in weeping willow!")
assert len(incontig) == 0, f"Failed with {len(incontig)} incontiguous edges"
'
```
*Observed output*: Exits with assertion error reporting `1980 incontiguous edges`.

### 5.2 Reproduce Broken Relative Links in Species Documentation
```bash
python3 -c '
import os, re
broken = []
for f in ["canopy_ancient_oak.md", "carnivorous_pitcher_plant.md", "cave_bioluminescent_mushroom.md"]:
    path = os.path.join("docs/flora/species", f)
    text = open(path).read()
    for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        if not link.startswith("http") and not link.startswith("#") and not link.startswith("file:"):
            res = os.path.normpath(os.path.join("docs/flora/species", link))
            if not os.path.exists(res):
                broken.append((f, link, res))
print(f"DEFECT CONFIRMED: {len(broken)} broken links found in sample target species:")
for f, l, r in broken:
    print(f"  {f}: {l} -> {r}")
assert len(broken) == 0, "Broken links exist!"
'
```
*Observed output*: Reports broken links resolving to non-existent `docs/assets/flora/...`.

### 5.3 Reproduce Hardcoded `file:///` URIs in Weeping Willow Spec
```bash
grep -n "file:///" docs/flora/species/canopy_weeping_willow.md
```
*Observed output*: Lines 52, 53, 54 printed.

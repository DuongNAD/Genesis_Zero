# TEST READY — 3D Photorealistic Creature Ecosystem E2E Test Suite

**Track**: 3D Photorealistic Creature Ecosystem Overhaul (`Milestone E2E & R1-R6`)  
**Status**: `TEST_READY` (Test Suite & Standalone Verification Runner fully implemented and verified)  
**Execution Commands**:  
- Standalone CLI Runner: `python3 scripts/verify_creatures_pipeline.py`  
- Automated Pytest Suite: `pytest -v tests/test_creature_assets.py`  
**Target Environment**: macOS Apple Silicon Metal, Blender 5.2.1 LTS, Python 3.11/3.13  

---

## 1. Test Suite Architecture & Summary Table

The 3D Creature Fauna verification infrastructure provides rigorous, opaque-box, requirement-driven validation across all 10 target species (`sand_skink`, `snow_ferret`, `alpine_ibex`, `meadow_hare`, `marsh_croc`, `abyssal_hunter`, `storm_eagle`, `giant_tarantula`, `armored_sentinel`, `carnivore_apex`). Derived directly from `ORIGINAL_REQUEST.md` (§ `2026-09-05T05:16:35Z`), `PROJECT.md`, and `TEST_INFRA.md`, the verification system spans 6 core quality dimensions:

| Dimension | Scope & Verification Invariants | Standalone CLI Check | Pytest Suite Implementation |
| :--- | :--- | :--- | :--- |
| **Dim 1: Taxonomy & Biological Traits** | Validates domain (`CAN`, `NUOC`, `TROI`), 6 traits (`brain`, `attack`, `armor`, `speed`, `sense`, `stomach`). Founder species sum == 12, each in [0, 5]. Specialist & Evo sum in [16, 23], each in [0, 7]. Validates `docs/creatures/README.md` catalog documentation. | `verify_taxonomy_and_metadata()` | `TestCreatureTaxonomyAndMetadata`<br>• `test_creature_metadata_and_traits`<br>• `test_creature_catalog_readme_structure` |
| **Dim 2: 4-Angle Concept Turnaround Sheets** | Checks `web/creature_images/<species>_turnaround.jpg` and `docs/creatures/images/<species>_turnaround.jpg`. Asserts JPEG binary markers (SOI `0xFFD8`, EOI `0xFFD9`), file size > 20 KB, and dimensions >= 1024x1024 across all views. | `verify_turnaround_images()` | `TestCreatureTurnaroundImages`<br>• `test_creature_turnaround_images` (parameterized for 10 species) |
| **Dim 3: 3D Model Master Deliverables** | Asserts existence and integrity of `assets/creatures/<species>.blend` (magic `b"BLEN"` or zstandard frame `b"\x28\xb5\x2f\xfd"`, size > 1 KB) and `assets/creatures/<species>.glb` (magic `b"glTF"`, version 2, total_len == file_size). | `verify_3d_model_deliverables()` | `TestCreatureThreeDDeliverables`<br>• `test_creature_blend_and_glb_files` (parameterized for 10 species) |
| **Dim 4: glTF 2.0 Rigging & 8 Animations** | Parses glTF 2.0 Chunk 0 JSON metadata. Asserts `skins` array > 0, joints referencing valid node indices. Asserts exactly 8 canonical action clips (`Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death`) with non-empty samplers and channels targeting valid armature nodes. | `verify_gltf2_skinning_and_animations()` | `TestCreatureGltfSkinningAnd8Animations`<br>• `test_creature_gltf_skinning_and_8_animations` (parameterized for 10 species) |
| **Dim 5: Headless Blender BMesh Topology** | Executes headless `/Applications/Blender.app/Contents/MacOS/Blender -b --python-expr "..."`. Checks all 10 `.blend` files with BMesh: asserts 0 loose vertices, 0 incontiguous edges, 0 multi-face/wire edges, 0 ngons (>4 vertices), and 100% smooth shading polygons (`poly.use_smooth = True`). | `verify_bmesh_manifold_topology()` | `TestCreatureBlenderBMeshTopology`<br>• `test_creature_bmesh_manifold_topology` (batch headless Blender execution) |
| **Dim 6: Web Viewer & Zero-CORS Offline Sync** | Validates `web/creature_viewer.html` catalog entries, 8 animation buttons, `SkeletonHelper` overlay toggle, turnaround modal. Validates `web/creature_models_data.js` offline base64 strings: decodes payload and verifies exact byte-level SHA256 checksum match with disk `.glb`. | `verify_web_viewer_sync()` | `TestCreatureWebViewerIntegration`<br>• `test_creature_web_viewer_html_elements`<br>• `test_creature_offline_base64_sha256_sync` |

---

## 2. 10 Target Species Specification & Coverage

| Species ID / Code | Domain | Common Name (VN / EN) | Tier | Biological Trait Vector (B, Atk, Arm, Spd, Sen, Sto) | Sum | Expected 3D Deliverables |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| `sand_skink` (L1) | `CAN` | Thằn Lằn Cát / Sand Skink | Founder T1 | `[4, 3, 1, 2, 1, 1]` | 12 | `sand_skink.blend`, `.glb`, `_turnaround.jpg` |
| `snow_ferret` (L2) | `CAN` | Chồn Tuyết / Snow Ferret | Founder T1 | `[3, 4, 2, 1, 2, 0]` | 12 | `snow_ferret.blend`, `.glb`, `_turnaround.jpg` |
| `alpine_ibex` (L3) | `CAN` | Dê Sừng Núi / Alpine Ibex | Founder T1 | `[3, 1, 1, 3, 3, 1]` | 12 | `alpine_ibex.blend`, `.glb`, `_turnaround.jpg` |
| `meadow_hare` (L4) | `CAN` | Thỏ Đồng Cỏ / Meadow Hare | Founder T1 | `[1, 1, 5, 1, 2, 2]` | 12 | `meadow_hare.blend`, `.glb`, `_turnaround.jpg` |
| `marsh_croc` (L5) | `CAN` | Cá Sấu Đầm Lầy / Marsh Croc | Founder T1 | `[0, 2, 0, 5, 3, 2]` | 12 | `marsh_croc.blend`, `.glb`, `_turnaround.jpg` |
| `abyssal_hunter` (W1) | `NUOC` | Cá Săn Vực Sâu / Abyssal Hunter | Founder T1 | `[1, 1, 0, 5, 4, 1]` | 12 | `abyssal_hunter.blend`, `.glb`, `_turnaround.jpg` |
| `storm_eagle` (A1) | `TROI` | Đại Bàng Bão Táp / Storm Eagle | Founder T1 | `[2, 2, 0, 4, 4, 0]` | 12 | `storm_eagle.blend`, `.glb`, `_turnaround.jpg` |
| `giant_tarantula` | `CAN` | Nhện Khổng Lồ / Giant Tarantula | Specialist T2 | `[2, 4, 2, 3, 4, 1]` | 16 | `giant_tarantula.blend`, `.glb`, `_turnaround.jpg` |
| `armored_sentinel` | `CAN` | Sentinel Cơ Khí / Armored Sentinel | Specialist T2 | `[3, 3, 6, 1, 3, 0]` | 16 | `armored_sentinel.blend`, `.glb`, `_turnaround.jpg` |
| `carnivore_apex` (L1_Evo) | `CAN` | Quái Thú Apex / Carnivore Apex | Super Apex T3 | `[5, 6, 3, 4, 3, 2]` | 23 | `carnivore_apex.blend`, `.glb`, `_turnaround.jpg` |

---

## 3. Requirement & Acceptance Criteria Traceability Matrix

| Requirement | Acceptance Criteria | Verification Implementation | Invariants Checked |
| :--- | :--- | :--- | :--- |
| **R1: Morphology & Anatomy** | AC 388, 389, 390 | `verify_taxonomy_and_metadata()`<br>`test_creature_metadata_and_traits`<br>`test_creature_bmesh_manifold_topology` | Domain validity, 6-trait bounded sums, 0 loose vertices, 0 non-manifold edges, 0 ngons (>4 verts), 100% smooth shading. |
| **R2: Armature Rig & 8 Action Clips** | AC 393, 394, 395, 396 | `verify_gltf2_skinning_and_animations()`<br>`test_creature_gltf_skinning_and_8_animations` | Armature skins > 0, valid node references, exactly 8 action clips (`Idle_Normal`, `Idle_Alert`, `Walk`, `Run`, `Attack`, `Hurt_Defend`, `Eat`, `Death`), samplers > 0, channels > 0. |
| **R3: Organic Shaders & PBR** | AC 389, 391 | `verify_3d_model_deliverables()`<br>`test_creature_blend_and_glb_files` | Principled BSDF materials, valid container structures, binary mesh primitives and materials arrays in glTF 2.0. |
| **R4: 4-Angle Concept Turnaround Sheets** | AC 398, 399, 400 | `verify_turnaround_images()`<br>`test_creature_turnaround_images` | Web and docs image files exist, JPEG SOI/EOI markers, size > 20 KB, dimensions >= 1024x1024. |
| **R5: Interactive 3D Web Viewer** | AC 402, 403, 404, 405 | `verify_web_viewer_sync()`<br>`test_creature_web_viewer_html_elements`<br>`test_creature_offline_base64_sha256_sync` | 10 species cards in HTML, 8-anim action buttons, skeleton toggle, turnaround modal, byte-exact SHA256 base64 offline sync. |
| **R6: Automated Verification Pipeline** | AC 407, 408, 409 | `scripts/verify_creatures_pipeline.py`<br>`tests/test_creature_assets.py` | Standalone CLI exits code 0 on 100% pass; pytest test suite passes all 6 dimensions. |

---

## 4. How to Run

### Standalone CLI Verification Runner
```bash
# Run full 6-dimension pipeline audit
python3 scripts/verify_creatures_pipeline.py

# Run with verbose test-by-test output
python3 scripts/verify_creatures_pipeline.py --verbose

# Run without headless Blender (skips BMesh topology check)
python3 scripts/verify_creatures_pipeline.py --skip-blender
```

### Pytest Automated Test Suite
```bash
# Run complete test suite with verbose output
pytest -v tests/test_creature_assets.py

# Run specific dimension tests
pytest -v tests/test_creature_assets.py -k "TestCreatureTaxonomyAndMetadata"
pytest -v tests/test_creature_assets.py -k "TestCreatureTurnaroundImages"
pytest -v tests/test_creature_assets.py -k "TestCreatureThreeDDeliverables"
pytest -v tests/test_creature_assets.py -k "TestCreatureGltfSkinningAnd8Animations"
pytest -v tests/test_creature_assets.py -k "TestCreatureBlenderBMeshTopology"
pytest -v tests/test_creature_assets.py -k "TestCreatureWebViewerIntegration"

# Run for a single species
pytest -v tests/test_creature_assets.py -k "sand_skink"
```

---

## 5. Test Verification Quality & Integrity Checklist

- [x] **No Mock Facades / Genuine Verification Logic**: Every test directly inspects physical deliverables on disk: parses real glTF 2.0 binary chunk headers and JSON metadata, executes actual headless Blender 5.2.1 BMesh topological queries, checks genuine JPEG SOI/EOI bytes and image dimensions, and calculates real SHA256 hashes of base64 payloads.
- [x] **Zero Hardcoded Passing State**: The suite fails immediately and accurately when deliverables or animations are missing (e.g. failing on old 1-animation models and missing assets as observed during initial preflight).
- [x] **Authoritative Derivation**: All invariants, species lists, trait limits, animation names, and dimension thresholds are derived strictly from `ORIGINAL_REQUEST.md` (§ `2026-09-05T05:16:35Z`), `PROJECT.md`, and `TEST_INFRA.md`.
- [x] **Blender 5.2.1 LTS Compatibility**: Executes natively via `/Applications/Blender.app/Contents/MacOS/Blender -b --python-expr` with PATH fallback.
- [x] **Code Quality & Linter Compliance**: Formatted and verified with `python3 -m ruff check` (0 errors, 0 warnings).

# E2E Test Infra: Genesis Zero Creature Ecosystem Overhaul

## Test Philosophy
- Requirement-driven, opaque-box & structural asset validation.
- Validates 6 comprehensive dimensions:
  1. Biological Traits & Taxonomic Integrity.
  2. Concept Turnaround Image Format (JPEG SOI \xff\xd8, EOI \xff\xd9, dimensions ≥ 1024x1024, size > 20KB).
  3. 3D Model Artifacts (.blend with BLEN header/zstd, .glb with glTF v2 header).
  4. glTF 2.0 Skinning & 8-Animation Channel Verification (Armature node, skins array, exactly 8 animation clips with valid samplers and keyframe channels).
  5. Blender Headless BMesh Topology (0 loose vertices, 0 non-manifold edges, 0 ngons > 4 vertices, 100% smooth shading).
  6. Web Viewer & Zero-CORS Data Sync (presence in `web/creature_viewer.html` and matching hash in `web/creature_models_data.js`).

## 10 Target Species Coverage
1. `sand_skink` (Land L1)
2. `snow_ferret` (Land L2)
3. `alpine_ibex` (Land L3)
4. `meadow_hare` (Land L4)
5. `marsh_croc` (Land L5)
6. `abyssal_hunter` (Water W1)
7. `storm_eagle` (Air A1)
8. `giant_tarantula` (Special Arachnid)
9. `armored_sentinel` (Special Biomechanical)
10. `carnivore_apex` (Evolutionary Apex L1_Evo)

## Test Runners
- Standalone CLI: `python3 scripts/verify_creatures_pipeline.py` (Exit code 0 on 100% pass)
- Pytest Suite: `pytest tests/test_creature_assets.py -v`

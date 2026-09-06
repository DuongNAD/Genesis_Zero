# Genesis Zero Flora Pipeline Plan

## Goal
Execute the end-to-end botanical research and 3D modeling pipeline per ORIGINAL_REQUEST.md (2026-09-04T17:31:35Z):
1. R1: Query & standardize APG IV botanical taxonomy from POWO Kew, WFO, GBIF, CoL, vncreatures for 5-10 representative species across diverse ecological layers.
2. R2: Generate standardized 4-angle turnaround concept sheets (3/4 Perspective, Front, Side, Top-Down Orthographic) at `web/flora_images/<species_slug>_turnaround.jpg` (or `.png`).
3. R3: 3D model in Blender with clean quad-dominant manifold topology, biological PBR materials with SSS (subsurface scattering) for foliage/petals and procedural bark bump. Export master `.blend` to `assets/flora/<category>/<species_slug>.blend` and runtime glTF 2.0 `.glb` to `assets/flora/<category>/<species_slug>.glb`.
4. R4: Synchronize Master Catalog `docs/flora/README.md` and species specs `docs/flora/species/<slug>.md`. Integrate into `web/flora_viewer.html` and `web/flora_models_data.js` with '4 Góc 📷' badge, turnaround sheet modal, and real-time 360° Three.js viewport.
5. R5: Automated verification suite (Python/pytest, e.g. `python scripts/verify_flora_pipeline.py` or `pytest tests/test_flora_assets.py`) checking metadata integrity, existence/validity of all images, .blend and .glb files (glTF 2.0 validation), and web viewer sync with Exit Code 0.

## Execution Phases & Milestones

### Phase 0: Survey & Scoping
- Spawn 3 parallel explorers to inspect:
  1. Explorer 1: Botanical taxonomy requirements, target species list across ecological layers, existing docs in `docs/flora/`.
  2. Explorer 2: Existing 3D assets, Blender environment, Python scripts for Blender export, glTF 2.0 validation tools, directory structure under `assets/flora/`.
  3. Explorer 3: Web viewer architecture (`web/flora_viewer.html`, `web/flora_models_data.js`, `web/flora_images/`), existing turnaround assets, and test verification scripts.
- Synthesize findings into `PROJECT.md` with full Feature Inventory, Architecture, Code Layout, and Milestones.

### Milestone 1 (M1): Botanical Taxonomy Research & Specification
- Query & standardize 5-10 representative species covering:
  - Canopy trees (Cây đại thụ)
  - Shrubs / Ferns (Cây bụi / Dương xỉ)
  - Herbs / Wildflowers (Thảo mộc / Hoa dại)
  - Aquatic / Wetland (Thủy sinh / Đầm lầy)
  - Desert / Succulents (Sa mạc / Mọng nước)
  - Endemic / Iconic species (Cây đặc hữu)
- Full taxonomic fields (APG IV, Scientific name, Family, Morphological dimensions H x Spread, Ecology/Habitat, POWO/GBIF/CoL references).
- Output: `docs/flora/species/<slug>.md` and draft catalog.

### Milestone 2 (M2): Multi-Angle Turnaround Concept Sheets (4-Angle)
- Generate standardized turnaround sheets:
  - Top half: 3/4 Front Perspective view.
  - Bottom half: 3 Orthographic views (Front, Side, Top-Down).
- Stored at `web/flora_images/<species_slug>_turnaround.jpg` (or `.png`).

### Milestone 3 (M3): Photorealistic 3D Modeling & PBR / glTF Export
- Scripted / procedural / assisted Blender generation with clean manifold topology.
- Principled BSDF PBR with Subsurface Scattering (SSS) for leaves/petals and procedural bump for bark.
- Export `.blend` to `assets/flora/<category>/<species_slug>.blend`.
- Export glTF 2.0 `.glb` to `assets/flora/<category>/<species_slug>.glb`.

### Milestone 4 (M4): Catalog & Web Viewer Synchronization
- Update `docs/flora/README.md` with complete taxonomy table, links to images, .blend and .glb.
- Update `web/flora_models_data.js` and `web/flora_viewer.html`:
  - Species cards with '4 Góc 📷' badge.
  - Turnaround modal popup displaying full sheet.
  - Real-time 360° Three.js 3D viewer loading `.glb`.

### Milestone 5 (M5): Automated Verification Suite & Quality Assurance
- Automated test script `scripts/verify_flora_pipeline.py` or `pytest tests/test_flora_assets.py`.
- Tests: taxonomy metadata integrity, image existence & dimensions, .blend files, .glb files (glTF 2.0 validation), web viewer sync.
- Verification must pass with Exit Code 0 and 100% quality standards.

### Gate Checks
- For each milestone: Explorer recommendations -> Worker execution -> 2 Reviewers -> 2 Challengers -> Forensic Auditor (zero tolerance) -> Gate verdict.

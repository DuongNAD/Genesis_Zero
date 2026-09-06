# BRIEFING — 2026-09-04T17:34:00Z

## Mission
Discover and document all botanical taxonomy requirements, APG IV standards, species selections (5-10 species across diverse ecological layers), and markdown catalog specifications for Genesis Zero.

## 🔒 My Identity
- Archetype: Specification Miner
- Roles: Botanical Spec Miner, Teamwork specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_spec_miner_survey6_1
- Original parent: c05f63b1-b12c-4ff5-856e-f6a353dc920f
- Milestone: Botanical Research & 3D Modeling Pipeline (R1 & R4)

## 🔒 Key Constraints
- Specification Miner role: Discover and document features by probing authoritative specification; do NOT implement anything.
- High accuracy botanical taxonomy adhering to APG IV standards and reputable databases (POWO Kew, WFO, GBIF, CoL, vncreatures).
- Target set: 5-10 representative species covering canopy trees, shrubs/ferns, herbs/wildflowers, aquatic/wetland, desert/succulents, and endemic species.
- Provide full structural specification for `docs/flora/species/<slug>.md` and `docs/flora/README.md`.
- Handoff report format: Observation, Logic Chain, Caveats, Conclusion, Verification Method.

## Current Parent
- Conversation ID: c05f63b1-b12c-4ff5-856e-f6a353dc920f
- Updated: 2026-09-04T17:34:00Z

## Task Summary
- **What to build**: Specification report and taxonomy documentation plan for botanical research and catalog.
- **Success criteria**: Detailed taxonomic profile of 5-10 species across 6 ecological layers with POWO/WFO/GBIF references, anatomical dimensions, markdown catalog templates, edge case analysis, and actionable handoff report.
- **Interface contracts**: `docs/flora/README.md`, `docs/flora/species/<slug>.md`, `web/flora_models_data.js`, `web/flora_viewer.html`.
- **Code layout**: Markdown docs under `docs/flora/`, assets under `assets/flora/`, viewer under `web/`.

## Key Decisions Made
- Discovered and cataloged existing repository flora assets: 100 species in `docs/flora/species/`, 16 3D models (.blend & .glb) in `assets/flora/`, 10 4-angle turnaround images in `web/flora_images/` & `docs/flora/images/`, and interactive Three.js spectator in `web/flora_viewer.html`.
- Identified taxonomic gaps: current markdown docs lack APG IV clades/orders, author citations, database cross-references (POWO Kew, WFO, GBIF, CoL, vncreatures), and native geographic coordinates.
- Selected and verified 10 core representative species across the 6 required ecological layers with full APG IV phylogeny and cross-reference keys, plus 2 supplemental species for wildflowers and Vietnamese endemics.
- Standardized the exact markdown structure for `docs/flora/species/<slug>.md` and the master catalog `docs/flora/README.md`.
- Formulated an automated verification test plan ensuring 100% data and asset integrity.

## Artifact Index
- DISPATCH.md — Assignment and instructions
- BRIEFING.md — Persistent situational awareness
- progress.md — Liveness heartbeat and step tracking
- handoff.md — Comprehensive handoff report with 5-component structure and specification tables

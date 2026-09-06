# Task Assignment: 3D Assets, Blender Pipeline & Material Architecture

## Context
You are the 3D Pipeline Explorer for the Genesis Zero botanical research and 3D modeling pipeline.
Your working directory: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_2`
Project root: `/Users/duongnad/Documents/project/Genesis_Zero`

## Mandatory Reading
Read `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically see entry under `## 2026-09-04T17:31:35Z`).

## Mission & Objectives
Investigate all requirements, tools, and existing codebase/assets for Blender 3D modeling, PBR materials, and glTF 2.0 export (R3):
1. Inspect existing assets in `assets/flora/`, `models/`, or any 3D files (`.blend`, `.glb`, `.gltf`, textures).
2. Inspect scripts/tools in `scripts/`, `tools/`, or elsewhere in the repo used to run Blender headless / programmatic modeling / export. Check what Blender version or Python environment is installed and available on this macOS system.
3. Determine how to achieve the required 3D quality standards:
   - Clean quad-dominant manifold topology, smooth shading.
   - Biological PBR materials with Subsurface Scattering (SSS) for foliage/petals and procedural bump/displacement for bark.
   - Dual export: master `.blend` to `assets/flora/<category>/<species_slug>.blend` and runtime `.glb` (glTF 2.0) to `assets/flora/<category>/<species_slug>.glb`.
4. Check glTF 2.0 validation requirements and tools (e.g. `gltf-validator`, pygltflib, trimesh, or custom validators).
5. Document constraints, file path conventions, and technical steps for the worker.

## Output Requirements
Write your detailed findings and report to `/Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey6_2/handoff.md`.
Follow the Handoff Protocol: Observation, Logic Chain, Caveats, Conclusion, Verification Method.
When finished, send a completion message to the parent orchestrator.

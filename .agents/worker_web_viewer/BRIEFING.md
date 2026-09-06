# BRIEFING — 2026-09-05T07:35:45Z

## Mission
Implement scripts/sync_all_creature_models_to_js.py and web/creature_viewer.html with Cyberpunk HUD aesthetic, 10 species cards, 3D viewport, 8 animation controls, traits HUD, 4-angle sheet modal, and zero-CORS offline execution via web/creature_models_data.js.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_web_viewer
- Original parent: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Milestone: Web Creature Viewer Implementation

## 🔒 Key Constraints
- Exclusive file ownership: web/creature_viewer.html, scripts/sync_all_creature_models_to_js.py, web/creature_models_data.js.
- DO NOT CHEAT: All implementations genuine, real base64 encoding and real Three.js rendering, no dummy facades.
- DO NOT invoke subagents.
- Zero-CORS offline execution support (decode base64 from window.CREATURE_MODELS_BASE64 with URL fallback).
- Use local vendor/three.min.js and vendor/GLTFLoader.js.
- Must communicate via send_message to parent (id: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1).

## Current Parent
- Conversation ID: 89c6e5ac-69f1-4bc0-87e9-af2f048ab4f1
- Updated: not yet

## Task Summary
- **What to build**:
  1. `scripts/sync_all_creature_models_to_js.py` to scan `assets/creatures/*.glb`, encode to base64, write `web/creature_models_data.js`.
  2. `web/creature_viewer.html`: Cyberpunk HUD styling matching Genesis Zero visual aesthetics, 10 species cards grouped by category, Three.js 3D viewport with studio lighting, shadow plane, mouse/touch orbit controls, 8-animation control bar with 0.2s cross-fading, playback speed controls, SkeletonHelper overlay, Biological traits HUD, high-res turnaround sheet modal, offline base64 loading.
  3. Execute sync script and verify clean loading without console errors.
- **Success criteria**: Python sync script works, models encoded, web viewer loads offline and displays models with animations, turnaround sheets, traits HUD, clean UI.
- **Interface contracts**: window.CREATURE_MODELS_BASE64 data contract, Three.js GLTFLoader.parse API.
- **Code layout**: scripts/, web/, assets/creatures/.

## Key Decisions Made
- [TBD]

## Artifact Index
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_web_viewer/DISPATCH.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_web_viewer/progress.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_web_viewer/BRIEFING.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_web_viewer/handoff.md

## Change Tracker
- **Files modified**: None yet
- **Build status**: Pending
- **Pending issues**: None

## Quality Status
- **Build/test result**: Untested
- **Lint status**: Clean
- **Tests added/modified**: Pending

## Loaded Skills
- None

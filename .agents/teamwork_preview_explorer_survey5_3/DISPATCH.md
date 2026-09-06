# Task Assignment: Camera Rig, GLB Export & Spectator Survey

Assigned to: teamwork_preview_explorer_survey5_3
Orchestrator: teamwork_preview_orchestrator_5
Project Root: /Users/duongnad/Documents/project/Genesis_Zero
Authoritative Request: /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (Section ## 2026-09-04T03:13:33Z)
Working Directory: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_3
Target Output: /Users/duongnad/Documents/project/Genesis_Zero/.agents/teamwork_preview_explorer_survey5_3/handoff.md

## 2026-09-04T03:15:27Z
OBJECTIVE:
Investigate requirement R5 (24-Angle Camera Rig & GLTF Export Pipeline for Game) and 3D Spectator compatibility for Genesis Zero.
Specifically examine:
1. Existing 3D spectator implementation in `/Users/duongnad/Documents/project/Genesis_Zero/web/watch3d.html` and `web/watch3d.js`, Three.js loader version, glTF loading capabilities, and how map models are consumed.
2. The exact camera positions, rotations, focal lengths, and naming for the 24-angle Camera Rig:
   - 4 Isometric angles (Iso NW, NE, SE, SW)
   - Top-down orthographic
   - 4 Cardinal side views (North, East, South, West)
   - Cross-section cutaway views (A-A, B-B)
   - Detailed close-ups (Lake, Waterfall, Lowland Forest, Subterranean Cave, River Meander, etc.)
3. Automated verification script design:
   - Script to render all 24 camera angles headlessly via Blender.
   - Image analysis / visual check assertions (depth gradients, lighting, shader appearance).
4. Export pipeline to `models/genesis_diorama.glb`:
   - Blender glTF export settings (geometry, materials, textures, animations/instances, compression).
   - Verification that the generated GLB is well under size limits and loads cleanly in Three.js without missing textures.


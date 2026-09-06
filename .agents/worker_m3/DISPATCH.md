## 2026-09-03T02:54:42+07:00
You are Worker M3 for Milestone 3: 3D Visualizer & Compact Map Experience (R3).
Your working directory is /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3/.
You MUST read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_3/handoff.md and analysis.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your write ownership:
- `web/watch3d.html`
- `web/watch3d.js`
- `net/match.py` (only if necessary for spectator frame formatting)
- `genesis/mesh_prompts.py`

Tasks:
1. Compact Diorama Framing:
   - In `web/watch3d.js`, build a compact, framed diorama island base with stylized bezel border, water floor shader/plane, and well-proportioned terrain mesh.
   - Set up intuitive camera presets (Isometric, Top-Down Tactical, Follow Creature) with smooth damping and bounds.
2. 3-Tier Elevation Ecosystem:
   - Position entities at distinct vertical elevations:
     - Airborne sky ($y=2.5$ for `Domain.TROI`, e.g. `A1`)
     - Tree canopy ($y=1.45$ for climbing creatures with `speed >= 3` on `TREE` tiles)
     - Ground terrain ($y=0.25$ for `Domain.CAN` on `PLAIN`, `ROCK`, `BUSH`, `FIRE`, `CAVE`)
     - Submerged water ($y=-0.25$ for `Domain.NUOC`, e.g. `W1` in `WATER`/`DEEP`)
3. Food and Corpse Rendering:
   - Process `frame.plants` to render vibrant fruits/algae matching plant kinds.
   - Process `frame.corpses` to render skeletal remains that visually decay.
4. Procedural 3D Biological Morphology:
   - Construct procedural Three.js geometry in `makeBody()` that visually expresses both:
     - 6 numeric traits (`brain`, `attack`, `armor`, `speed`, `sense`, `stomach`)
     - 12 biological features (`genesis/features.py`: `CANH_BAY` wings, `VAY_BOI` fins, `NOC_DOC` venom barb, `GIAP_CUNG` carapace, `DAO_HANG` claws, `DA_DOI_MAU` camouflage, `MAT_KHAM` eyes, `VAP_HAM` jaws, `VOI_HUT` proboscis, `CO_QUAN_PHAT_SANG` bioluminescence, `TU_BAO` spore sac, `MANG_THO` gills).
5. Real-Time Law Journal HUD & Dynamic Events:
   - In `web/watch3d.html` / `web/watch3d.js`, create a real-time Law Journal / Codex HUD overlay showing active hypothesis slots, score metrics, and discovery status.
   - On `LAW_FIRED` events, spawn multi-particle shockwaves and elemental pulse effects.
   - In `REVEAL` phase, display the 3 victory podiums (Nhà khoa học, Kẻ sống sót, Người đầu tiên) with revealed laws.
6. Zero External CDN Rule:
   - Preserve 100% offline self-containment using `web/vendor/three.min.js`. Do NOT add any `http://` or `https://` script tags (must strictly pass `test_spectate.py`).
7. Run test verification:
   - `pytest tests/test_spectate.py tests/test_mesh.py -v`
   - `pytest tests/e2e -v`
   - `python scripts/preflight.py`
8. Write `handoff.md` to /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m3/handoff.md and report to parent.

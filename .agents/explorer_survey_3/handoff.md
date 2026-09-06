# Handoff Report — Explorer 3: R3 (3D Visualizer & Compact Map Experience)

## 1. Observation
1. **Visualizer Core Implementation**:
   - `web/watch3d.html` (52 lines) loads `web/vendor/three.min.js`, `web/vendor/GLTFLoader.js`, and `web/watch3d.js` without external CDNs or build tooling.
   - `web/watch3d.js` (288 lines) establishes a Three.js scene (`Scene`, `PerspectiveCamera(48)`, `WebGLRenderer`, `HemisphereLight`, `DirectionalLight`, `Fog(0x06080f, 26, 62)`).
   - In `web/watch3d.js:176`, all organism bodies are hardcoded to ground elevation `g.position.set(c.x + 0.5, TERRAIN.P.h, c.y + 0.5)`.
   - In `web/watch3d.js:240-257`, `onFrame(frame)` processes `frame.terrain`, `frame.creatures`, and `frame.events`, but completely omits `frame.plants` (fruits) and `frame.corpses` (remains), leaving food and death remains invisible.
   - In `web/watch3d.js:122-168`, `makeBody(c)` constructs procedural primitives for 6 numeric traits (`brain`, `attack`, `armor`, `speed`, `sense`, `stomach`), but completely ignores the 3 domain archetypes (`genesis/domain.py: Domain.NUOC`, `CAN`, `TROI`) and the 12 biological features (`genesis/features.py:72-154`).
   - In `web/watch3d.js:203-209`, `drawHearing` instantiates `new THREE.BufferGeometry().setFromPoints(...)` on every frame inside `requestAnimationFrame(loop)`, causing garbage collection churn.
   - In `web/watch3d.js:213-223`, `addSpark` renders a single flat wireframe ring (`RingGeometry(0.2, 0.28)`) for `LAW_FIRED` events without multi-particle shockwaves or elemental cues.
   - In `web/watch3d.html:35-42`, the UI header only contains basic text counters (`phase`, `tick`, `alive`, `map`) and an event sidebar (`#log`). There is no Law Journal / Codex HUD, no creature inspection card, no tactical minimap, and no victory ceremony for the `REVEAL` phase (`genesis/victory.py`).

2. **Telemetry & Server Routing**:
   - `net/routes_spectate.py:42-81` manages WebSocket `/v1/spectate` by subscribing an `asyncio.Queue` to `runner.subscribers` without modifying the simulation runner.
   - `net/match.py:553-590` produces the frame payload containing `t`, `phase`, `w`, `h`, `creatures`, `plants`, `corpses`, `map`, `terrain` (tick 0 or backlog prepended), and `events`.
   - `tests/test_spectate.py` verifies 13 tests checking no-law leaks during `RUNNING`, proper reveal in `REVEAL`, strict trait-only sizing, and zero CDN / HTTP links. Running `PYTHONPATH=. pytest tests/test_spectate.py -v` passes 13/13 tests in 2.42s.

## 2. Logic Chain
1. From **Observation 1**, `watch3d.js` only implements basic procedural spheres and cones for the 6 traits and places every entity at ground height `TERRAIN.P.h` ($y=0.10$).
2. By comparing **Observation 1** with the simulation model in `genesis/domain.py` and `genesis/features.py`, the simulation has 3 distinct environmental tiers (Water, Land, Sky) and 12 biological features that alter movement and sensory mechanics. Because `watch3d.js` does not differentiate elevation or features, a bird (`A1`), a fish (`W1`), and a land predator (`L1`) appear identically flattened on the ground, misrepresenting the simulation's rich ecology to human spectators.
3. From **Observation 1**, `watch3d.js` fails to read `frame.plants` and `frame.corpses`, which are actively transmitted by `net/match.py:581-582`. Consequently, feeding and predation events occur at seemingly empty tiles, breaking visual causality.
4. From **Observation 1**, `watch3d.js` creates temporary geometries in its animation loop and lacks interactive raycasting, camera presets, diorama island framing, day/night lighting, Law Journal Codex HUD, and victory podiums.
5. Therefore, upgrading the 3D visualizer requires five concrete enhancements: (1) Compact diorama island base with framed bezels and water shader; (2) True 3-tier elevation positioning ($y_{\text{sky}}=2.5$, $y_{\text{tree}}=1.45$, $y_{\text{ground}}=0.25$, $y_{\text{water}}=-0.25$); (3) Domain-specific 3D silhouettes with 12 procedural biological feature attachments and smooth movement lerping; (4) Rendering food fruits, algae, and corpses; (5) Interactive Law Journal Codex HUD, dynamic law activation shockwaves, creature inspection card, and REVEAL victory podium.

## 3. Caveats
- **Meshy 3D Text-to-Mesh vs Procedural Fallback**: While `net/mesh.py` and `genesis/mesh_prompts.py` support offline/online GLB generation via MeshyAI API, client browsers in local/offline environments will rely 100% on procedural Three.js geometry. The procedural generation in `watch3d.js` must therefore be fully self-sufficient and visually expressive.
- **Three.js Version**: The bundled library in `web/vendor/three.min.js` is Three.js r128 (UMD). Advanced post-processing passes must remain compatible with r128 without introducing new external packages.

## 4. Conclusion
The Genesis Zero 3D visualizer is architecturally well-isolated (clean WebSocket telemetry, zero CDN dependencies, strict simulation decoupling), but currently functions as a barebones prototype. Addressing the identified gaps—namely 3-tier elevation rendering, 12 biological features, missing plant/corpse rendering, Law Journal Codex overlay, diorama framing, and smooth entity interpolation—will elevate the spectator experience to a compelling, compact, and vivid 3D showcase as mandated by Requirement R3.

## 5. Verification Method
- **Run Spectate & Mesh Test Suite**:
  ```bash
  PYTHONPATH=. pytest tests/test_spectate.py tests/test_mesh.py -v
  ```
- **Inspect Key Visualizer Files**:
  - `web/watch3d.html`
  - `web/watch3d.js`
  - `genesis/mesh_prompts.py`
  - `net/routes_spectate.py`
- **Invalidation Conditions**:
  - Any 3D visualizer change introducing external CDN URLs (`http://` or `https://`) in `web/watch3d.html` or `web/watch3d.js` (violates `test_spectate.py:test_6_no_cdn_or_external_urls`).
  - Sizing creatures based on model parameters rather than biological trait vectors (violates `test_spectate.py:test_5_watch_js_no_model_size_dependence`).
  - Revealing hidden law descriptions before the `REVEAL` phase (violates `test_spectate.py:test_1_spectate_running_no_law_leak`).

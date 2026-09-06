# Handoff Report: Interactive 3D Spectator, Procedural Audio, Replay Timeline & Launcher (R3, R4, R5)

**Agent**: Explorer 3 (3D Spectator & Procedural Audio Specialist)  
**Date**: 2026-09-03  
**Status**: Hard Handoff (Task Complete)  
**Target File**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_spectator_1/handoff.md`  
**Reference Analysis**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_spectator_1/analysis.md`

---

## 1. Observation

1. **Current 3D Spectator Implementation**:
   - `web/watch3d.html` (lines 169-328): Currently contains 3D canvas container, header with camera controls (`btn-cam-iso`, `btn-cam-top`, `btn-cam-free`), hearing/journal/minimap toggles, left journal panel, right event log, minimap, and creature inspection card. It has no timeline scrubber controls, no playback speed selectors, no audio controls, and no weather HUD indicators.
   - `web/watch3d.js` (lines 61-98, 1024-1065, 1068-1136): Operates Three.js r128 with static ambient/sun/hemi lighting and fixed fog (`scene.fog = new THREE.Fog(0x06080f, 32, 75)`). Frames received from WebSocket `/v1/spectate` immediately drive `syncBodies()`, `syncPlantsAndCorpses()`, and event logs. There is no historical frame ring buffer, no procedural audio synthesis, and no weather-dependent particle system.
   - `web/vendor/`: Contains `three.min.js` (603,445 bytes) and `GLTFLoader.js` (96,550 bytes). No audio files exist in repo.
2. **Server Telemetry & Frame Buffering**:
   - `net/match.py` (lines 527-534, 551-591): `MatchRunner._publish()` appends every telemetry frame to `self.frames: list[dict]` and raw events to `self._frame_raw: list[list[dict]]`. `self.frame()` serializes tick state including `t`, `phase`, `w`, `h`, `creatures`, `plants`, `corpses`, `terrain_delta`, and `events`.
   - `net/routes_spectate.py` (lines 29, 55-57): `QUEUE_MAX = 256`. On client connect, `backlog = list((runner.reveal_frames() if reveal else runner.frames)[-QUEUE_MAX:])` pushes up to 256 previous frames to late joiners.
3. **Launcher & Operational Tooling**:
   - `run.sh` (lines 14-53): Automatically detects Python >= 3.11, auto-creates `.venv`, installs requirements, and executes `python scripts/launch.py "$@"`.
   - `scripts/launch.py` (lines 198-232, 292, 313-316): Provides `--web` flag which starts `uvicorn net.server:app --port 8000` and automatically triggers `webbrowser.open("http://127.0.0.1:8000/watch/watch3d.html")`.
   - `net/server.py` (lines 59-62): Mounts `/watch` directly to `web/` (`app.mount("/watch", StaticFiles(directory=str(_WEB), html=True), name="watch")`), allowing offline local asset loading.
4. **Test Infrastructure & Zero-CDN Invariants**:
   - `tests/test_spectate.py` (lines 138-148, 258-274): Strictly forbids `http://`, `https://`, and `//` in `web/watch3d.html` and `web/watch3d.js`. Requires local `web/vendor/three.min.js`.
   - Full test suite baseline: Executed `pytest` across the entire repository with output `890 passed, 1 skipped in 92.25s (0:01:32)`. Zero test failures.

---

## 2. Logic Chain

1. **Procedural Web Audio Without Assets (R3)**:
   - *From Observation 1 & 4*: The repository contains zero external audio files, and test assertions in `tests/test_spectate.py` fail if external HTTP/HTTPS URLs are referenced.
   - *Deduction*: All sound effects must be synthesized directly via the browser's native Web Audio API (`AudioContext`, `OscillatorNode`, `BiquadFilterNode`, `GainNode`, and dynamic noise buffers).
   - *Design*: Implement distinct procedural sound profiles for:
     - Organism movement: Domain-differentiated (water droplet sweep for NUOC, ground rustle for CAN, air whoosh for TROI). Throttled to max 1 per 60ms to prevent cacophony.
     - Law discovery: 4-oscillator harmonic major chord with sweeping resonant shimmer and sub-bass impact for `LAW_FIRED` events.
     - Creature death: Sawtooth pitch-bend plunge from 240 Hz down to 42 Hz with decaying low-pass filter for `DEATH` events.
     - Weather transitions: Ambient drone / filter sweeps triggered when `frame.weather.phase` transitions.
   - Master chain includes a `DynamicsCompressorNode` (-6dB threshold) to prevent digital clipping when multiple events fire simultaneously.

2. **Interactive Match Timeline Scrubber (R3)**:
   - *From Observation 1 & 2*: Currently the client displays incoming frames live and discards prior frame state. `net/match.py` already records historical frames in `self.frames`.
   - *Deduction*: Client-side scrub responsiveness must be instant (< 1ms). Making network calls to fetch historical ticks would create scrub lag and stutter.
   - *Design*: The client maintains a ring buffer `historyBuffer` (capacity 1200 frames, ~1.8 MB memory). A floating bottom dock `#timeline-dock` provides:
     - Play/Pause toggle (spacebar shortcut)
     - Speed toggles: 1x, 2x, 5x
     - Rewind -10 ticks / Forward +10 ticks
     - Range slider bound to `[min_buffered_tick, max_buffered_tick]`
     - LIVE sync button returning instantly to the real-time stream.
   - When scrubbing, an `isInstant = true` flag assigns entity positions directly, bypassing the 0.18 lerp damping to prevent unnatural stretching.

3. **Visual Atmospheric Cues & Weather Synchronization (R3)**:
   - *From Observation 1 & peer Explorer 2 design*: The simulation engine broadcasts `frame.weather` with `phase`, `cycle_progress`, and `modifiers`.
   - *Deduction*: The 3D scene can dynamically reflect the weather state in real time without external texture assets.
   - *Design*: Three.js scene fog, sky background color, and sun/hemi lighting smoothly lerp towards target profiles for each weather phase (CLEAR, NIGHT, STORM, SOLAR_FLARE, TOXIC_SPORES).
   - Dedicated procedural `THREE.Points` particle systems render:
     - Storm: Diagonal falling rain streaks (900 points) + occasional lightning intensity pulse.
     - Solar flare: Rising radiant glowing embers (450 points).
     - Toxic spores: Swirling emerald/purple spore mist (500 points).
     - Night: Deep indigo atmosphere with enhanced creature emissive/eye glow.

4. **Replay Buffer Integration & Telemetry Compatibility (R4)**:
   - *From Observation 2*: Late joiners currently receive up to 256 backlog frames via `routes_spectate.py` (`QUEUE_MAX = 256`).
   - *Deduction*: Increasing `QUEUE_MAX` to `1000` (or match tick limit) allows a late joiner to receive the entire match history upon connecting.
   - *Deduction*: Extending the `/v1/spectate` schema to include `weather` object and creature generational attributes (`gen`, `parent_id`) maintains full backward compatibility because all existing keys (`t`, `phase`, `creatures`, `plants`, `corpses`, `events`, `terrain`) remain intact.

5. **Launcher Verification & Operational Friction (R5)**:
   - *From Observation 3*: `run.sh` and `scripts/launch.py --web` already mount `/watch` and point to `web/watch3d.html`.
   - *Deduction*: Because all new audio and particle features are pure code inside `web/watch3d.html` and `web/watch3d.js` referencing only local `web/vendor/three.min.js`, the launcher boots the entire enhanced experience with zero additional flags, zero external internet connection, and zero friction.

---

## 3. Caveats

1. **Browser Autoplay Policies**:
   - Modern browsers (Chrome, Safari, Firefox) mandate a user gesture (mouse click or keypress) before an `AudioContext` transitions from `"suspended"` to `"running"`.
   - *Mitigation*: Audio initialization is handled via a global `unlockAudio()` listener on first click/keydown, and audio calls are guarded with state checks so they fail silently without crashing the visualizer.
2. **Memory Footprint of Multi-Thousand Tick Matches**:
   - Storing 5000+ uncompressed frames in JavaScript could consume 10-15 MB of heap memory.
   - *Mitigation*: The client ring buffer enforces a ceiling of 1200 frames (`MAX_HISTORY`). This provides ~2-4 minutes of continuous scrubbing while keeping memory under 2 MB.
3. **No Caveats on Core Mechanics**:
   - Zero-CDN offline requirements, Three.js diorama coordinates, and Web Audio synthesis are fully compatible with all target operating systems (macOS, Linux, Windows).

---

## 4. Conclusion

1. The architectural design for R3, R4, and R5 is fully articulated and ready for implementation.
2. `web/watch3d.html` and `web/watch3d.js` will receive:
   - An interactive timeline scrubber dock (Play/Pause, 1x/2x/5x, rewind, slider, LIVE button).
   - A zero-dependency procedural Web Audio engine (movement, shockwaves, death, weather shifts).
   - A dynamic weather visualizer (sky/lighting lerping and procedural particle rain/embers/spores).
   - An inspection card enhancement displaying creature generational lineage (`gen`, `parent_id`).
3. `net/routes_spectate.py` will have its backlog queue capacity expanded to support deeper initial replay hydration.
4. `run.sh` and `scripts/launch.py --web` remain completely valid and operational for single-command launching.
5. All 890 existing tests remain green, and the proposed extensions introduce zero breaking schema changes.

---

## 5. Verification Method

### 5.1 Programmatic Verification Commands
Execute the complete test suite to confirm baseline preservation:
```bash
# 1. Verify 100% test pass rate across entire repository
pytest

# 2. Specifically verify spectator offline & zero-CDN compliance
pytest tests/test_spectate.py -v

# 3. Specifically verify E2E Tier 1 3D visualizer features (F3.1 - F3.6)
pytest -o pythonpath=. tests/e2e/test_e2e_tier1_features.py -k "F3" -v
```

### 5.2 Files to Inspect
1. `web/watch3d.html`: Inspect `#timeline-dock` layout, audio volume slider, and absence of external script tags.
2. `web/watch3d.js`: Inspect Web Audio API synthesis functions (`playMoveSound`, `playLawShockwaveSound`, `playDeathSound`, `playWeatherShiftSound`), particle emitter update loops, and timeline scrubber state machine.
3. `net/routes_spectate.py`: Inspect `QUEUE_MAX` and backlog frame delivery logic.
4. `scripts/launch.py`: Inspect `--web` launcher target path and execution.

### 5.3 Invalidation Conditions
The technical design would be invalidated if:
1. Any external audio file (`.mp3`, `.wav`) or external CDN link is introduced into `web/`.
2. Browser AudioContext restrictions cause uncaught promise rejections that halt the Three.js render loop.
3. Timeline scrubbing introduces frame desynchronization or breaks referee scoring pipelines.
4. Pytest test suite experiences any failure or collection regression below the 890-test benchmark.

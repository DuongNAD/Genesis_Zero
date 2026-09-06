# Dispatch Assignment: Worker M4_SPECTATOR (Interactive 3D Spectator & Procedural Audio Specialist)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z` - R3 & R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Architectural Survey Report: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_spectator_1/handoff.md`
- Existing Visualizer: `web/watch3d.html` and `web/watch3d.js`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Exclusively Owned Files
- `web/watch3d.html`
- `web/watch3d.js`
- `tests/test_spectate_ui.py` (new test suite)
- `README.md` (only if total test count changes)

## Core Implementation Requirements

### 1. `web/watch3d.html` Enhancements
- **Timeline Dock (`#timeline-dock`)**:
  - Floating bottom dock styled cleanly with the existing cyberpunk/dark theme.
  - Play/Pause toggle button (`#btn-playback-toggle`) with icon/text and Spacebar hotkey.
  - Speed selector buttons: 1x (`#btn-speed-1x`), 2x (`#btn-speed-2x`), 5x (`#btn-speed-5x`).
  - Rewind -10 ticks (`#btn-rewind-10`) and Forward +10 ticks (`#btn-forward-10`).
  - Timeline range slider (`#timeline-slider`, `<input type="range" min="0" max="0" value="0">`).
  - Tick display label (`#timeline-tick-display`, e.g. `Tick 150 / 150`).
  - LIVE sync button (`#btn-live-sync`) that returns immediately to real-time stream.
- **Procedural Audio Controls**:
  - Sound toggle button (`#btn-audio-toggle`) with mute/unmute icon and master volume slider (`#audio-volume-slider`, range 0 to 1).
- **Weather HUD Indicator**:
  - In top header, add `#weather-badge` showing active weather icon/name (e.g. `☀️ CLEAR`, `🌙 NIGHT`, `⛈️ STORM`, `🔥 SOLAR FLARE`, `☣️ TOXIC SPORES`, `🧲 MAGNETIC SHIFT`), cycle progress bar, and active environmental modifiers tooltip/pill.
- **Creature Inspection Card**:
  - Add fields for Generation (`gen`), Parent ID (`parent_id`), Lineage path, and Trait deltas (`d_tr`).
- **CRITICAL ZERO-CDN CONSTRAINT**:
  - Strictly ZERO `http://`, `https://`, or `//` URLs in `web/watch3d.html`.
  - All assets must be loaded locally from `/watch/vendor/` or inline CSS/JS.

### 2. `web/watch3d.js` Enhancements
- **Client Frame History Ring Buffer (`historyBuffer`)**:
  - Ring buffer capacity: 1200 frames (`MAX_HISTORY = 1200`).
  - Store frames indexed by tick `t`.
  - Maintain `isPaused`, `playbackSpeed` (1x, 2x, 5x), `scrubTick`, `isLive` state.
  - When scrubbed or paused, render the target historical frame instantly (`isInstant = true` so entity positions snap directly without 0.18 lerp latency).
  - Update slider min, max, and current value smoothly as new frames arrive.
- **Procedural Web Audio Engine**:
  - Zero audio files, zero external CDNs. Native browser `AudioContext`.
  - Global `unlockAudio()` listener on first click/keypress to comply with browser autoplay policies.
  - Master chain with `DynamicsCompressorNode` (-6dB threshold) and master gain.
  - Synthesizers:
    - Movement clicks/rustles/whooshes (throttled to avoid stutter).
    - `LAW_FIRED`: Resonant 4-oscillator major chord with harmonic shimmer and low-end impact.
    - `DEATH`: Sawtooth pitch plunge (240Hz down to 40Hz) with decaying low-pass filter.
    - `REPRODUCE`: Ascending arpeggio chime.
    - `COMBAT_HIT` / `ATTACK`: Quick white noise punch / snap.
    - Weather transitions: Ambient drone / filter sweep when weather changes.
- **Weather Atmosphere & Particle Systems**:
  - Smooth lerping of scene fog, background color, ambient light, and directional sunlight according to active weather state:
    - CLEAR: Warm bright sunlight, soft blue sky.
    - NIGHT: Deep dark indigo, lowered ambient light, boosted creature eye emissive glow.
    - STORM / RAIN: Slate gray sky, dense fog, vertical falling rain streaks via `THREE.Points` (800 particles).
    - SOLAR FLARE: Amber-red glow, rising fiery embers via `THREE.Points` (400 particles).
    - TOXIC SPORES: Sickly neon green/purple mist, swirling drifting spores via `THREE.Points` (500 particles).
    - MAGNETIC SHIFT: Shifting cyan/magenta atmospheric pulses.
  - Render loop animates particles continuously.

### 3. Tests & Verification
- Create `tests/test_spectate_ui.py`:
  - Verify `web/watch3d.html` contains `#timeline-dock`, `#btn-playback-toggle`, `#timeline-slider`, `#btn-audio-toggle`, `#weather-badge`.
  - Verify `web/watch3d.js` defines `historyBuffer`, Web Audio synthesis methods (`AudioContext`, `playLawFired`, `playDeath`, `playReproduce`, `playWeatherShift`), weather particle systems, and zero external URLs.
  - Assert zero `http://` or `https://` in both HTML and JS.
- If adding `tests/test_spectate_ui.py` increments total test count, update `README.md` lines 131 and 185 to keep `test_readme_khop_thuc_te.py` passing!
- Run `pytest tests/test_spectate.py tests/test_spectate_ui.py -v`.
- Run full repository `pytest -q` (100% pass required).
- Run `ruff check` on python test files.

## Output Requirements
Deliver handoff report to `handoff.md` with:
1. Observation (files modified, features implemented, test results).
2. Logic Chain.
3. Caveats.
4. Conclusion.
5. Verification commands and exact outputs.
Notify parent via `send_message`.

## 2026-09-03T08:39:25Z
You are Worker M4_SPECTATOR (Interactive 3D Spectator & Procedural Audio Specialist) for Genesis Zero.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_spectator_1/handoff.md
- Existing visualizer code in `web/watch3d.html` and `web/watch3d.js`

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement:
1. `web/watch3d.html`: Timeline dock (#timeline-dock) with play/pause, speed controls (1x, 2x, 5x), rewind/forward, range scrubber slider, tick display, LIVE button. Audio toggle & volume slider. Weather HUD badge. Generational lineage metadata in creature inspection card. Strictly zero external CDN links.
2. `web/watch3d.js`: Client frame ring buffer (1200 frames capacity), instant timeline scrubbing, procedural Web Audio API sound generator (movement, shockwaves, death plunge, reproduction arpeggio, combat hits, weather shift drone; zero external audio files), dynamic weather lighting/fog lerping, and Three.js particle systems for Rain, Spore Storm, Solar Flare, and Magnetic Shift.
3. Tests in `tests/test_spectate_ui.py` verifying UI elements, procedural audio functions, particle systems, and zero-CDN invariant.
4. If test count changes, update README.md lines 131 and 185 to keep `test_readme_khop_thuc_te.py` passing.
5. Verify `pytest tests/test_spectate.py tests/test_spectate_ui.py -v`, full `pytest -q`, and `ruff check`.
6. Write handoff report to `handoff.md` and notify parent via `send_message`.


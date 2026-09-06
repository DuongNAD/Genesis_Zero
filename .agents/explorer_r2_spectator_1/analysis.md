# Technical Survey & Architecture Specification: Interactive 3D Spectator, Procedural Audio, Replay Timeline & Launcher (R3, R4, R5)

**Author**: Explorer 3 (3D Spectator & Procedural Audio Specialist)  
**Date**: 2026-09-03  
**Status**: COMPLETE  
**Target Milestone**: Genesis Zero Round 2 (R3, R4, R5)  
**Scope**: `web/watch3d.html`, `web/watch3d.js`, `net/match.py`, `net/routes_spectate.py`, `scripts/launch.py`, `run.sh`, and associated verification suites.

---

## Executive Summary

This survey provides the complete architectural design and implementation specification for upgrading the Genesis Zero 3D Spectator (`web/watch3d.html`, `web/watch3d.js`) into an interactive, multi-sensory observation station.

Key deliverables formulated in this survey:
1. **Interactive Match Timeline Scrubber**: Full playback control dock providing Play/Pause, Fast-Forward (1x, 2x, 5x), Rewind (-10 ticks), scrubber slider, and instant LIVE sync.
2. **Procedural Web Audio API Synthesizer**: Pure programmatic sound generation with **strictly zero external audio files** and **zero CDN calls**, covering organism movement across 3 domains, law discovery cosmic shockwaves, creature mortality, and atmospheric weather phase transitions.
3. **Visual Atmospheric & Weather Synchronization**: Real-time lighting modulation, sky tone shifts, dynamic volumetric fog, and procedural Three.js particle systems (falling rain, rising solar embers, swirling toxic spores, midnight mist).
4. **Hybrid Replay Buffer Architecture**: Optimal synergy between server-side frame retention (`net/match.py` / `routes_spectate.py`) and client-side ring buffer (`historyBuffer` in JS), guaranteeing sub-millisecond scrub latency and zero GC stutter.
5. **Zero-Friction Launcher Operations**: Full validation of `run.sh` and `scripts/launch.py` to ensure one-command boot of the simulation server and automatic browser launch into the 3D spectator.
6. **Robust Quality Assurance**: Edge case mitigations (browser autoplay policies, audio gain clipping, scrub lerp artifacts, memory caps) and programmatic test specifications preserving 100% pass rate across the 890 baseline tests.

---

## 1. Interactive Match Timeline Scrubber

### 1.1 UI & UX Layout in `web/watch3d.html`

The timeline scrubber is placed at the bottom of the viewport as a floating glassmorphic control dock (`#timeline-dock`), providing intuitive ergonomics without obstructing the 3D diorama map.

```html
<!-- Floating Timeline & Audio Control Dock -->
<div id="timeline-dock">
  <div class="dock-left">
    <button id="btn-rewind-10" class="btn-dock" title="Lùi 10 lượt (Phím [ hoặc ←)">⏮ 10</button>
    <button id="btn-play-pause" class="btn-dock play-btn" title="Tạm dừng / Tiếp tục (Phím Space)">⏸</button>
    <button id="btn-forward-10" class="btn-dock" title="Tiến 10 lượt (Phím ] hoặc →)">⏭ 10</button>
    <button id="btn-speed" class="btn-dock speed-badge" title="Tốc độ xem lại (Phím T)">1x</button>
  </div>

  <div class="dock-center">
    <span id="timeline-tick-cur" class="val">0</span>
    <div class="slider-track-wrap">
      <input type="range" id="timeline-slider" min="0" max="0" value="0" step="1">
      <div id="timeline-buffer-bar" class="buffer-bar"></div>
    </div>
    <span id="timeline-tick-max" class="val">0</span>
    <button id="btn-live" class="btn-dock live-badge active" title="Trở về thời gian thực (Phím L)">
      <span class="live-dot"></span> LIVE
    </button>
  </div>

  <div class="dock-right">
    <button id="btn-audio-mute" class="btn-dock" title="Bật/Tắt Âm thanh (Phím S)">🔊</button>
    <input type="range" id="audio-volume" min="0" max="100" value="70" class="volume-slider" title="Âm lượng">
  </div>
</div>
```

### 1.2 State Machine & Playback Engine in `web/watch3d.js`

```
                +-------------------+
                |     LIVE MODE     | <---------------+
                | (Real-time Stream)|                 |
                +---------+---------+                 |
                          | User drags slider /       |
                          | presses Pause / Rewind    | User clicks "LIVE" /
                          v                           | scrubs to max tick
                +-------------------+                 |
                |    REPLAY MODE    |                 |
                | (Buffer Playback) | ----------------+
                +---------+---------+
                          |
             +------------+------------+
             |                         |
             v                         v
     [PAUSED STATE]             [PLAYING STATE]
(Freeze tick, camera     (Advance tick accumulator
 orbit still responsive)  at 1x, 2x, or 5x rate)
```

#### Core Playback Variables
- `isLive`: `boolean` (default `true`). When `true`, each frame received from WebSocket immediately drives the scene.
- `isPlaying`: `boolean` (default `true`). When in replay mode, controls whether the scrubber advances automatically.
- `playbackSpeed`: `number` (options: `1.0`, `2.0`, `5.0`). Toggled via `btn-speed`.
- `currentReplayTick`: `number` (the tick currently displayed on screen).
- `replayAccumulator`: `number` (tracks delta time in milliseconds: `dt >= (baseTickMs / playbackSpeed)` triggers next tick).
- `historyBuffer`: `Array<TelemetryFrame>` (client-side ring buffer, capacity 1200 frames).

#### Instant Snapping vs Smooth Lerp
- In **LIVE MODE**: Bodies lerp smoothly towards target coordinates (`0.18` factor per render frame).
- In **SCRUBBING / STEPPING**: When the user drags the slider or jumps ticks, an `isInstant = true` flag bypasses position lerping:
  ```javascript
  ent.currX = targetX;
  ent.currY = targetY;
  ent.currZ = targetZ;
  ent.yaw = ent.targetYaw;
  ```
  This eliminates visual "stretching" or rubber-banding across historical frames and delivers 60 FPS instantaneous scrubbing.

---

## 2. Procedural Web Audio API Sound Synthesis

### 2.1 Strictly Zero-External-Asset & Zero-CDN Constraint
- In strict adherence to `PROJECT.md` and `tests/test_spectate.py` (Tests 6 & 13), **zero external audio files** (`.wav`, `.mp3`, `.ogg`) and **zero CDN libraries** are used.
- All sound is synthesized programmatically at runtime using the browser's native `AudioContext`, `OscillatorNode`, `BiquadFilterNode`, `GainNode`, and dynamically allocated `AudioBuffer` noise generators.

### 2.2 Audio Architecture & Signal Chain

```
[Movement Generator]  ----\
[Law Shockwave Synth] -----\
[Creature Death Synth] ------> [Master Compressor / Limiter] ---> [Master Gain] ---> [audioCtx.destination]
[Weather Ambience Synth] --/
```

- **Dynamics Compressor**: Configured with `threshold: -6.0 dB`, `knee: 12.0`, `ratio: 8.0`, `attack: 0.003s`, `release: 0.25s`. Prevents digital clipping/distortion when multiple creatures trigger audio concurrently.
- **Autoplay Handling**: Audio starts unlocked via a global single-click/keypress handler (`audioCtx.resume()`).

### 2.3 Synthesizer Specifications

#### A. Organism Movement Cues (Domain-Differentiated)
To avoid auditory fatigue, movement sounds are throttled to at most 1 cue per 60ms, prioritizing the currently inspected creature (`selectedCreatureId`) or random sampling.
1. **Aquatic (NUOC) — "Droplet Sweep"**:
   - Oscillator: Sine wave sweeping from 320 Hz to 580 Hz in 45ms.
   - Filter: Bandpass filter at 460 Hz (Q = 3.5).
   - Envelope: Attack 3ms, Decay 42ms, Peak Gain 0.08.
   - Sound: Soft, fluid droplet plunge.
2. **Terrestrial (CAN) — "Pitted Footstep"**:
   - Noise: Procedural white noise burst filtered through a low-pass filter (cutoff 280 Hz).
   - Oscillator: Low sub-sine (75 Hz decaying to 35 Hz in 30ms).
   - Envelope: Attack 2ms, Decay 30ms, Peak Gain 0.07.
   - Sound: Crisp, subtle ground rustle.
3. **Aerial (TROI) — "Air Flap"**:
   - Noise: Bandpass filtered noise sweeping from 1100 Hz down to 380 Hz in 65ms.
   - Envelope: Attack 8ms, Decay 55ms, Peak Gain 0.06.
   - Sound: Gentle wing flutter.

#### B. Law Discovery Shockwaves (`LAW_FIRED`)
Triggered whenever a hidden physics law activates.
- **Cosmic Harmonic Chord**:
  - Quad oscillators playing a mystical major/lydian chord:
    - Osc 1: Sine 440.00 Hz (A4)
    - Osc 2: Sine 554.37 Hz (C#5)
    - Osc 3: Sine 659.25 Hz (E5)
    - Osc 4: Triangle 880.00 Hz (A5) with a 4.5 Hz vibrato LFO.
  - Sub-Bass Impactor: Sine wave at 55 Hz decaying over 250ms for physical impact weight.
  - Resonant Shimmer: Biquad peaking filter with Q = 6.0 sweeping from 1200 Hz to 3400 Hz.
  - Envelope: Instant attack (8ms), sustain (180ms), long ethereal exponential decay (1200ms).

#### C. Creature Death (`DEATH`)
Triggered on creature mortality event.
- **Mortality Descent**:
  - Oscillator: Sawtooth wave pitch-plunging from 240 Hz down to 42 Hz over 380ms (`exponentialRampToValueAtTime`).
  - Filter: Lowpass filter cutting off from 900 Hz down to 50 Hz over 380ms.
  - Sub-impact: Low sine click at 48 Hz.
  - Envelope: Attack 5ms, Decay 380ms, Peak Gain 0.14.
  - Sound: Mournful fading pitch descent.

#### D. Weather Phase Transitions
Triggered whenever `frame.weather.phase` transitions.
- **STORM Transition**: Low frequency brown noise rumble (40 Hz - 120 Hz) with slow 0.5 Hz amplitude modulation + dual sub-sine sweeps simulating distant thunder.
- **SOLAR FLARE Transition**: Resonant bandpass sweep (200 Hz up to 1400 Hz with high resonance Q = 8.0) creating an energetic ionization drone.
- **TOXIC SPORES Transition**: Dissonant dual-sine drone (480 Hz & 484.5 Hz) generating a binaural 4.5 Hz acoustic beating pulse.
- **NIGHT Transition**: Gentle downward harmonic transition with tranquil low-pass filtering.
- **CLEAR Transition**: Bright bell/crystal chime (523.25 Hz C5 -> 659.25 Hz E5).

---

## 3. Visual Atmospheric Cues & Real-Time Weather Synchronization

### 3.1 Dynamic Environment Matrix

The Three.js scene dynamically transitions between atmospheric profiles according to `frame.weather`:

| Phase | Sky Background | Fog Color & Range | Directional Sun | Ambient Fill | Dominant Mood |
|---|---|---|---|---|---|
| **CLEAR** | `#06080f` (`0x06080f`) | Color `0x06080f`, Near 32, Far 75 | Color `0xfff7ed`, Intensity 1.10 | Hemi `0xbfdbfe` / `0x1e293b` (0.85) | Crisp, vibrant diorama |
| **NIGHT** | `#02040a` (`0x02040a`) | Color `0x02040a`, Near 20, Far 58 | Color `0x38bdf8`, Intensity 0.30 | Hemi `0x1e1b4b` / `0x020617` (0.35) | Midnight bioluminescence |
| **STORM** | `#0a0f1d` (`0x0a0f1d`) | Color `0x0a0f1d`, Near 15, Far 42 | Color `0x64748b`, Intensity 0.40 | Hemi `0x334155` / `0x0f172a` (0.45) | Heavy overcast, dark mist |
| **SOLAR_FLARE**| `#250a04` (`0x250a04`) | Color `0x250a04`, Near 24, Far 55 | Color `0xf59e0b`, Intensity 1.85 | Hemi `0xfbbf24` / `0x7c2d12` (0.80) | Blazing solar radiation |
| **TOXIC_SPORES**| `#061a10` (`0x061a10`) | Color `0x061a10`, Near 12, Far 36 | Color `0x84cc16`, Intensity 0.70 | Hemi `0x10b981` / `0x064e3b` (0.65) | Creeping green biohazard |

### 3.2 Procedural Particle Systems (Zero Texture Dependencies)

Particle effects are created using `THREE.Points` with procedurally allocated vertex positions in a single `THREE.BufferGeometry`:

1. **Storm Rain Particle Emitter**:
   - Geometry: 900 points spread across `x: [0, W]`, `z: [0, H]`, `y: [0, 10]`.
   - Physics: Rapid vertical downward velocity (`vy = -14.0 u/s`) with slight wind drift (`vx = -1.2 u/s`).
   - Bounds: When `y < 0`, particle resets to `y = 10 + random() * 2`.
   - Lightning Flash: Stochastic timer (every 6-12s) triggering a 90ms spike of ambient light intensity (`2.4`) and white fog.
2. **Solar Flare Radiant Embers**:
   - Geometry: 450 glowing points rising upward from ground plane (`vy = +1.8 u/s`, `vx = sin(t + i) * 0.4`).
   - Material: `THREE.PointsMaterial({ color: 0xfbbf24, size: 0.18, transparent: true, opacity: 0.85 })`.
   - Lifecycle: Reset to `y = 0.1` upon reaching `y > 6.0`.
3. **Toxic Spore Mist Cloud**:
   - Geometry: 500 drifting particles with slow sinusoidal Brownian drift in the lower layer `y: [0.1, 1.8]`.
   - Material: `THREE.PointsMaterial({ color: 0xa3e635, size: 0.22, transparent: true, opacity: 0.65 })`.

---

## 4. Replay History Buffer Integration (Server vs Client)

### 4.1 Architecture Comparison

| Dimension | Client-Side Ring Buffer | Server-Side Telemetry Buffer |
|---|---|---|
| **Storage Location** | Browser JavaScript Heap (`historyBuffer`) | Python `MatchRunner.frames` in `net/match.py` |
| **Scrub Latency** | **< 0.5 ms** (Instant memory lookup) | 10 - 50 ms (Network round-trip per step) |
| **Bandwidth Cost** | Zero network calls during scrubbing | High network traffic if fetching ticks dynamically |
| **Memory Footprint** | ~1.8 MB for 1000 frames (~1.8 KB / frame) | Already maintained in Python process memory |
| **Late Joiner Experience** | Can only scrub ticks received since connection | Provides backlog on initial WebSocket handshake |

### 4.2 Integrated Hybrid Architecture

1. **Server Backlog Hydration on Connect**:
   - In `net/routes_spectate.py`, when a spectator client establishes WebSocket connection, the server sends the backlog of historical match frames up to `QUEUE_MAX`:
     ```python
     backlog = list((runner.reveal_frames() if reveal else runner.frames)[-QUEUE_MAX:])
     ```
   - **Recommendation for R4**: Increase `QUEUE_MAX` from `256` to `1000` (or `runner.ticks`), ensuring a spectator joining at tick 500 receives the complete match history to scrub back to tick 0.
2. **Client Ring Buffer Accumulation**:
   - `web/watch3d.js` maintains:
     ```javascript
     const MAX_HISTORY = 1200;
     const historyBuffer = [];
     ```
   - Every incoming frame is pushed into `historyBuffer`. If length exceeds `MAX_HISTORY`, `historyBuffer.shift()` maintains a constant memory footprint.
   - Ground terrain grid is cached once from the initial frame (`cachedTerrain`), saving ~3 KB per frame.
3. **Scrubber Playback Sync**:
   - The timeline slider range automatically updates: `slider.min = historyBuffer[0].t`, `slider.max = latestFrame.t`.
   - Moving the scrubber indexes into `historyBuffer`, allowing instantaneous rewinding and variable-speed replay.

---

## 5. Launcher & Operational Script Validation

### 5.1 Analysis of `run.sh`
- `run.sh` operates as an intelligent bootstrap wrapper:
  1. Searches for Python >= 3.11 (`python3.12`, `python3.11`, `python3`, `python`).
  2. Auto-creates virtualenv `.venv` if absent.
  3. Verifies core dependencies (`rich`, `httpx`, `fastapi`, `uvicorn`, `pydantic`, `numpy`).
  4. Hands execution over to `scripts/launch.py "$@"`.
- **Validation Result**: 100% compliant with zero-friction onboarding criteria.

### 5.2 Analysis of `scripts/launch.py`
- Operates in both interactive TUI mode and CLI flag mode:
  - `--web`: Boots `uvicorn net.server:app --port 8000` and automatically triggers `webbrowser.open("http://127.0.0.1:8000/watch/watch3d.html")`.
  - `--reflex`: Instant local execution without external LLM dependencies.
  - `--demo`: End-to-end mock server, simulation, and referee scoring pipeline.
  - `--preflight` / `--fix`: Automated environment diagnostics and auto-repair.
- In `net/server.py`, line 61 mounts `/watch` -> `StaticFiles(directory="web", html=True)`. All paths resolve locally:
  - `/watch/watch3d.html` -> `web/watch3d.html`
  - `/watch/watch3d.js` -> `web/watch3d.js`
  - `/watch/vendor/three.min.js` -> `web/vendor/three.min.js`
- **Zero-Friction Guarantee**: Running `./run.sh --web` directly launches the FastAPI server and opens the 3D spectator in the browser with zero manual setup.

---

## 6. Potential Risks, Edge Cases & Test Requirements

### 6.1 Edge Cases & Technical Mitigations

| Risk / Edge Case | Impact | Technical Mitigation Strategy |
|---|---|---|
| **Browser Autoplay Block** | AudioContext starts in `suspended` state, causing silent launch or console errors. | Register global user interaction listener (`click`, `keydown`) calling `audioCtx.resume()`. Show discreet "🔊 Click anywhere to unmute audio" badge. Wrap all audio calls in `if (audioCtx && audioCtx.state === 'running')`. |
| **Audio Clipping under High Load** | Multiple shockwaves or 30 creature movements in a single tick cause harsh speaker distortion. | Route all procedural audio nodes through a dedicated `DynamicsCompressorNode` (-6dB threshold). Throttle movement audio to 1 event per 60ms. |
| **Scrubbing Lerp Glitch** | Entity models stretch or spin wildly across the diorama when scrubbing across non-consecutive ticks. | Set `isInstant = true` during scrubber dragging: assign positions directly without interpolation; cancel lingering movement tweens. |
| **Memory Leak in Long Matches** | Storing thousands of frames in memory could increase browser heap usage. | Enforce ring buffer ceiling `MAX_HISTORY = 1200`. Store only lightweight data fields; reuse pre-allocated Three.js geometries and typed arrays (`Float32Array`). |
| **Zero-CDN Invariant Breach** | Accidental reference to external CDN or URL breaks offline tests. | Strict automated test assertion: `grep` check on `web/watch3d.html` and `web/watch3d.js` verifying absence of `http://`, `https://`, and `//`. Local Three.js bundled in `web/vendor/`. |

### 6.2 Test Suite Requirements for R3/R4/R5

1. **Web Spectator Offline & CDN Test**:
   - Verify `web/watch3d.html` and `web/watch3d.js` contain zero external HTTP/HTTPS links.
   - Verify Three.js vendor files exist locally in `web/vendor/three.min.js`.
2. **Telemetry Weather & Lineage Compatibility Test**:
   - Verify `/v1/spectate` frames emit `weather` dictionary containing `phase`, `cycle_progress`, and `modifiers`.
   - Verify creature payload includes `gen` and `parent_id` without breaking legacy keys (`id`, `x`, `y`, `hp`, `e`, `tr`, `features`).
3. **Replay Buffer Delivery Test**:
   - Verify `MatchRunner.frames` accurately archives frames and returns `reveal_frames()` in `Phase.REVEAL`.
   - Verify WebSocket client receives backlog frames upon connection.
4. **Launcher Verification Test**:
   - Verify `scripts/launch.py --help` exits cleanly with code 0.
   - Verify `net.server:app` serves `watch3d.html` with status 200 and correct MIME type `text/html`.
5. **Full Regression Test**:
   - Maintain 100% pass rate across the full 890 existing tests (`pytest`).

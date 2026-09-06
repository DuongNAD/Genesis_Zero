# Dispatch Assignment: Reviewer 2 (Milestone M4_SPECTATOR)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z` - R3 & R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M4 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md`
- Visualizer files: `web/watch3d.html` and `web/watch3d.js`

## Review Objectives
1. **JavaScript Architecture & Playback State Machine**:
   - Inspect `web/watch3d.js` for `historyBuffer` with `MAX_HISTORY = 1200` ring buffer bounding.
   - Inspect timeline scrubber implementation: `renderHistoricalFrame`, `isInstant` snapping (bypassing 0.18 lerp latency during scrub), `isLive`, `isPaused`, `playbackSpeed` (1x, 2x, 5x), and spacebar hotkey.
2. **Procedural Web Audio API Engine**:
   - Inspect procedural sound synthesis: `AudioContext`, `DynamicsCompressorNode` (-6dB threshold), user gesture `unlockAudio()` listener.
   - Inspect synthesizers: `playMoveSound`, `playLawFired`, `playDeath`, `playReproduce`, `playWeatherShift`, `playCombatHit`. Confirm zero audio files or external audio network calls.
3. **Weather Visualizer & Particle Systems**:
   - Inspect lighting & fog lerping across weather states (`CLEAR`, `NIGHT`, `SPORE_STORM`, `SOLAR_FLARE`, `MAGNETIC_SHIFT`, `STORM`).
   - Inspect `THREE.Points` particle systems: Rain (800 particles), Solar Flare (400 particles), Spores (500 particles), and Magnetic Shift (300 particles). Confirm safe animation within render `loop()`.
4. **Test Execution**:
   - Run `pytest tests/test_spectate_ui.py -v`.
   - Run `pytest -o pythonpath=. tests/e2e/test_e2e_tier1_features.py -k "F3" -v`.
5. **Verdict**:
   - Write comprehensive review to `handoff.md` with explicit verdict: **`APPROVE`** or **`REQUEST_CHANGES`**.
   - Notify parent via `send_message`.

## 2026-09-03T08:53:12Z
You are Reviewer 2 for Milestone M4_SPECTATOR.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m4_spectator_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/reviewer_m4_spectator_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md
- `web/watch3d.html` and `web/watch3d.js`

Review JavaScript architecture, historyBuffer ring buffer (1200 frames), instant snapping logic, procedural Web Audio API engine (synthesizers for movement, shockwave, death, reproduce, combat, weather shifts; zero audio files), dynamic weather lighting/fog lerping, and Three.js particle systems. Run tests (`pytest tests/test_spectate_ui.py tests/e2e/test_e2e_tier1_features.py -k "F3" -v`). Deliver your verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent via send_message.

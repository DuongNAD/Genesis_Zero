# Survey Task: Interactive 3D Spectator, Procedural Audio, Timeline Replay & Launcher (R3, R4, R5)

## Objectives
1. Read `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (specifically section `## 2026-09-03T04:57:00Z`).
2. Read `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md` and `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`.
3. Investigate the spectator, networking, launcher, and test infrastructure:
   - `web/watch3d.html`
   - `web/watch3d.js`
   - `web/vendor/` (verify Zero-CDN offline requirements)
   - `net/match.py` (replay history buffer, buffer limits, scrubbing support)
   - `scripts/launch.py` and `run.sh`
   - `tests/test_spectate.py` and `tests/e2e/test_e2e_tier1_features.py`
4. Formulate architectural and technical requirements for R3, R4, R5:
   - Interactive match timeline scrubber: Play/Pause, Fast-Forward (1x, 2x, 5x), rewind, and scrub through buffered match ticks.
   - Procedural Web Audio API sound synthesis: dynamic sound synthesis for movement, law discovery shockwaves, creature death, weather shifts. Strictly zero external audio files and zero CDN calls.
   - Visual atmospheric cues: dynamic lighting tone, sky color, particle systems (fog, rain, storm particles, flare glow) synchronized with weather state in real time.
   - Replay history buffer in server telemetry (`/v1/spectate`) or client-side ring buffer for timeline scrubbing.
   - Launcher updates: ensuring `run.sh` and `scripts/launch.py` seamlessly boot server and spectator with zero friction.
   - Test patterns and regression prevention requirements for all UI, audio, replay, and launcher mechanics.
5. Write your comprehensive analysis to `analysis.md` and final handoff to `handoff.md` in your directory.

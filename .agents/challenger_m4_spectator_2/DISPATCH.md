# Dispatch Assignment: Challenger 2 (Milestone M4_SPECTATOR)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z` - R3 & R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M4 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md`
- Visualizer files: `web/watch3d.html` and `web/watch3d.js`

## Challenger Objectives
1. **Procedural Web Audio & Particle Safety Adversarial Testing**:
   - Audio safety:
     - Verify zero sound files (`.mp3`, `.wav`, `.ogg`, `.flac`, `.aac`) exist in `web/` or anywhere in repo.
     - Verify that all sound synthesis uses native `AudioContext` and handles locked/suspended states gracefully without throwing uncaught exceptions.
     - Verify audio master compressor prevents clipping and volume slider clamps within `[0.0, 1.0]`.
   - Weather particles & atmospheric lerp safety:
     - Simulate 100 rapid weather transitions (switching between CLEAR, NIGHT, SPORE_STORM, SOLAR_FLARE, MAGNETIC_SHIFT, STORM every tick).
     - Verify particle buffers do not leak memory, particle counts remain bounded, and visibility flags toggle cleanly.
2. **Implementation**:
   - Write and execute an adversarial test module `tests/test_challenger_m4_audio_particles.py`.
   - If adding test file changes total test count, ensure `README.md` lines 131 and 185 stay synchronized with `test_readme_khop_thuc_te.py`.
3. **Execution**:
   - Run `pytest tests/test_challenger_m4_audio_particles.py -v`.
   - Run `pytest tests/test_spectate_ui.py -v`.
4. **Verdict**:
    - Deliver empirical results and verdict (**`APPROVE`** or **`REQUEST_CHANGES`**) in `handoff.md` and notify parent via `send_message`.

## 2026-09-03T08:53:12Z
You are Challenger 2 for Milestone M4_SPECTATOR.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m4_spectator_2
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m4_spectator_2/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md
- `web/watch3d.html` and `web/watch3d.js`

Adversarially stress test procedural Web Audio API parameters, zero-sound-file invariant, audio compressor clipping safety, and weather particle system memory/lifecycle safety under 100 rapid weather switches. Write adversarial test suite in `tests/test_challenger_m4_audio_particles.py`. Execute tests. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent via send_message.

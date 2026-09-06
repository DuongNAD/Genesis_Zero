# Dispatch Assignment: Challenger 1 (Milestone M4_SPECTATOR)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z` - R3 & R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M4 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md`
- Visualizer files: `web/watch3d.html` and `web/watch3d.js`

## Challenger Objectives
1. **Adversarial Scrubber & Replay Buffer Stress Testing**:
   - Test boundary conditions on `historyBuffer`:
     - Empty buffer behavior (tick 0, connect before ticks start).
     - Buffer saturation: 1200+ frames (verify sliding window FIFO drop without memory leak).
     - Out-of-bounds scrub requests: tick < min_buffered, tick > max_buffered.
     - Rapid scrub thrashing: jumping randomly between ticks 100 times in 10ms.
     - Playback speed transitions: toggling between 1x, 2x, 5x during active match.
     - Live resync: resuming live stream from deep history (`goToLive`).
2. **Implementation**:
   - Write and execute an adversarial test module `tests/test_challenger_m4_scrubber.py`.
   - If adding test file changes total test count, ensure `README.md` lines 131 and 185 stay synchronized with `test_readme_khop_thuc_te.py`.
3. **Execution**:
   - Run `pytest tests/test_challenger_m4_scrubber.py -v`.
   - Run `pytest tests/test_spectate_ui.py -v`.
4. **Verdict**:
   - Deliver empirical results and verdict (**`APPROVE`** or **`REQUEST_CHANGES`**) in `handoff.md` and notify parent via `send_message`.

## 2026-09-03T08:53:12Z
You are Challenger 1 for Milestone M4_SPECTATOR.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m4_spectator_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/challenger_m4_spectator_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md
- `web/watch3d.html` and `web/watch3d.js`

Adversarially stress test timeline scrubber boundary cases (empty buffer, saturation beyond 1200 frames, out-of-bounds scrub requests, rapid scrub thrashing, 1x/2x/5x speed transitions, live sync resumption). Write adversarial test suite in `tests/test_challenger_m4_scrubber.py`. Execute tests. Deliver empirical results and verdict (APPROVE or REQUEST_CHANGES) in handoff.md and notify parent via send_message.

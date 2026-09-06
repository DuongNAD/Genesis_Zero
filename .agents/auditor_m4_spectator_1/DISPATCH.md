# Dispatch Assignment: Forensic Auditor (Milestone M4_SPECTATOR)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z` - R3 & R5)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md`
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Worker M4 Handoff: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md`
- Visualizer files: `web/watch3d.html` and `web/watch3d.js`

## Forensic Audit Protocol (Checks 1 to 6)
You must execute an uncompromising, independent integrity forensics audit on the Milestone M4_SPECTATOR codebase:

1. **Check 1: Hardcoding & Determinism Audit**:
   - Inspect `web/watch3d.html` and `web/watch3d.js` for any hardcoded simulation states, fake frames, or mock responses.
2. **Check 2: Facade & Dummy Verification**:
   - Verify that `#timeline-dock`, procedural Web Audio synthesizers, and weather particle systems are genuine, functioning implementations, not empty stubs or dummy facades.
3. **Check 3: Attestation Artifact Integrity**:
   - Verify that no synthetic or fabricated test outputs exist in the repository.
4. **Check 4: Full Repository Test Suite & Verification (Zero-Failure Invariant)**:
   - Run `pytest tests/test_spectate.py tests/test_spectate_ui.py -v`.
   - Run `pytest tests/test_readme_khop_thuc_te.py -v`.
   - Run `pytest -q` across the entire repository to verify that all tests pass with 0 failures and 0 collection errors.
   - Verify that `tests/test_readme_khop_thuc_te.py` thresholds were NOT relaxed.
5. **Check 5: Information Leak Scans**:
   - Confirm that spectator client does not leak secret law tokens prior to `REVEAL` phase.
6. **Check 6: Zero-CDN & Dependency Isolation (Offline Invariant)**:
   - Perform strict AST/regex scan on `web/watch3d.html` and `web/watch3d.js` to assert that zero `http://`, `https://`, or `//` URLs exist.
   - Confirm that all assets load locally from `web/vendor/`.
   - Confirm zero external audio files (`.mp3`, `.wav`, etc.) exist.

## Output Requirements
Deliver a comprehensive audit report to `handoff.md` in your working directory with an explicit verdict: **`CLEAN`** or **`INTEGRITY VIOLATION`**.
Notify parent via `send_message`.

## 2026-09-03T08:53:12Z
You are the Forensic Auditor for Milestone M4_SPECTATOR.
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m4_spectator_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/auditor_m4_spectator_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m4_spectator_1/handoff.md
- `web/watch3d.html` and `web/watch3d.js`

Perform forensic integrity analysis across Checks 1 to 6 on Milestone M4_SPECTATOR:
1. Hardcoding/mock absence.
2. Facade/dummy absence.
3. Attestation artifact integrity.
4. Full repository test suite (100% pass rate, 0 failures, README sync).
5. Information leak scan.
6. Zero-CDN and dependency isolation (strictly 0 external URLs, 0 audio files).
Deliver handoff report with explicit verdict (CLEAN or INTEGRITY VIOLATION) in handoff.md and notify parent via send_message.

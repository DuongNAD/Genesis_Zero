## 2026-09-10T05:24:00Z

Task: E2E Testing Track — Comprehensive Opaque-Box Test Suite (Tiers 1-4)
Working Directory: e:\Project\01_AI_Agents\Genesis_Zero\.agents\teamwork_preview_test_writer_e2e\
Test Infrastructure Plan: e:\Project\01_AI_Agents\Genesis_Zero\TEST_INFRA.md
Project Scope Document: e:\Project\01_AI_Agents\Genesis_Zero\PROJECT.md
Original Request: e:\Project\01_AI_Agents\Genesis_Zero\.agents\ORIGINAL_REQUEST.md (§ 2026-09-10T05:12:31Z)
Simulation Engine: E:\tool\mcp\terra_forge
Target Workspace: e:\Project\01_AI_Agents\Genesis_Zero

Write Ownership:
- E:\tool\mcp\terra_forge\tests\e2e\
- e:\Project\01_AI_Agents\Genesis_Zero\TEST_READY.md

Objectives:
1. Review `TEST_INFRA.md`, `PROJECT.md`, and `ORIGINAL_REQUEST.md`.
2. Implement comprehensive opaque-box test suites in `E:\tool\mcp\terra_forge\tests\e2e\`:
   - `test_tier1_feature_coverage.py`: >= 5 tests per feature covering all 23 core features in isolation (happy path, self-contained).
   - `test_tier2_boundary_corner.py`: >= 5 boundary and corner case tests per feature (limits, extremes, empty inputs, max size, slope cuts, water levels).
   - `test_tier3_pairwise_combinations.py`: Cross-feature combinatorial interactions (geology + erosion, hydrology + lake berm, karst + water level, artifact + manifest + navmesh).
   - `test_tier4_workload_scenarios.py`: 5 realistic full application scenarios:
     1. Full Abiotic Primordial Map Generation & Validation
     2. Pure Abiotic Invariant Audit (strictly 0% flora, 0% fauna, 0% human structures)
     3. Continuous Hydrological Drainage & Retaining Berm Integrity
     4. Karst Cavern Structural Clearance & Arch Entrance
     5. Three.js Viewer Load & 60 FPS Offline Verification
3. Execute the full E2E test suite using `uv run pytest E:\tool\mcp\terra_forge\tests\e2e\ -v`.
4. When all test cases are implemented and passing (or establishing clear regression baselines), publish `e:\Project\01_AI_Agents\Genesis_Zero\TEST_READY.md` conforming to the template in `PROJECT.md`.
5. Write your handoff report to `e:\Project\01_AI_Agents\Genesis_Zero\.agents\teamwork_preview_test_writer_e2e\handoff.md`.

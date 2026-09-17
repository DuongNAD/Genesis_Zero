# E2E Test Infra: Genesis_Zero Primordial Abiotic 3D Map

## Test Philosophy
- Opaque-box, requirement-driven. Derived strictly from `ORIGINAL_REQUEST.md` (§ 2026-09-10T05:12:31Z) and user-facing specifications, not internal implementation details.
- Pure abiotic invariant enforcement: strict assertions verifying 0% flora, 0% fauna, 0% human structures.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial Testing + Real-World Workload Testing.

---

## Feature Inventory & Test Matrix
| # | Feature | Requirement | Tier 1 (Feature) | Tier 2 (Boundary) | Tier 3 (Pairwise) |
|---|---------|-------------|:----------------:|:-----------------:|:-----------------:|
| 1 | Meshy v2 Client & Rate Limiting | R1 | 5 | 5 | ✓ |
| 2 | Local Asset Vault & SHA-256 Cache | R1 | 5 | 5 | ✓ |
| 3 | Geometry Normalization & Colliders | R1 | 5 | 5 | ✓ |
| 4 | 3-Tier LOD Generation | R1 | 5 | 5 | ✓ |
| 5 | Strict Abiotic Filtering (0% flora/fauna) | R5 | 5 | 5 | ✓ |
| 6 | Abiotic Asset Catalog & Vault Population | R1, R2, R3 | 5 | 5 | ✓ |
| 7 | Multi-Tier Geological Topography | R1 | 5 | 5 | ✓ |
| 8 | Hydraulic Droplet Erosion & Mass Conservation | R1 | 5 | 5 | ✓ |
| 9 | Thermal Talus Erosion & Scree | R1 | 5 | 5 | ✓ |
| 10 | Pure Abiotic Preset & Heightfield Pipeline | R1, R5 | 5 | 5 | ✓ |
| 11 | Triplanar Rock PBR Shading | R1 | 5 | 5 | ✓ |
| 12 | 4-Tier Continuous Hydrology | R2 | 5 | 5 | ✓ |
| 13 | Parabolic Channel Carving & Lake Berms | R2 | 5 | 5 | ✓ |
| 14 | PBR Optical Water Shader | R2 | 5 | 5 | ✓ |
| 15 | Subterranean Karst Cavern Chamber & Speleothems | R3 | 5 | 5 | ✓ |
| 16 | Karst Rocky Arch Tunnel Entrance | R3 | 5 | 5 | ✓ |
| 17 | Bioluminescent Cavern Minerals & Lighting | R3 | 5 | 5 | ✓ |
| 18 | Binary WorldArtifact v2 (.anmw, FNV-1a) | R4 | 5 | 5 | ✓ |
| 19 | Map Manifest Schema (Draft-07) & Hash Match | R4 | 5 | 5 | ✓ |
| 20 | Dual Scene Export (GLB & Blend) | R4 | 5 | 5 | ✓ |
| 21 | NavMesh BFS Coverage (>= 80.0%) & Spawn Point | R4 | 5 | 5 | ✓ |
| 22 | 4 Visual Acceptance Renders | AC | 5 | 5 | ✓ |
| 23 | 3D Viewer 60 FPS & Offline Vendor Assets | R4 | 5 | 5 | ✓ |

---

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Abiotic Primordial Map Generation & Validation | F1, F2, F3, F5, F7, F8, F9, F10, F12, F13, F15, F18, F19, F20, F21 | High |
| 2 | Pure Abiotic Invariant Audit (0% Flora, 0% Fauna) | F5, F6, F10, F20 | High |
| 3 | Continuous Hydrological Drainage & Berm Integrity | F7, F8, F12, F13, F14, F18, F21 | High |
| 4 | Karst Cavern Structural Clearance & Arch Entrance | F7, F15, F16, F17, F20 | Medium |
| 5 | Three.js Viewer Load & 60 FPS Offline Verification | F20, F23 | Medium |

---

## Coverage Thresholds
- Tier 1: $\ge 5$ test cases per feature (23 features $\times 5 = 115$ test cases).
- Tier 2: $\ge 5$ boundary/corner cases per feature (23 features $\times 5 = 115$ test cases).
- Tier 3: Pairwise coverage of major feature interactions ($\ge 25$ test cases).
- Tier 4: $\ge 5$ realistic end-to-end workload scenarios.
- Total Target: $\ge 260$ comprehensive E2E test assertions.

---

## Test Architecture & Invocation
- Location: `E:\tool\mcp\terra_forge\tests\e2e\`
- Test Runner Command:
  ```powershell
  uv run pytest E:\tool\mcp\terra_forge\tests\e2e\ -v
  ```
- Signal: When all tests are generated and verified, E2E Testing Track will publish `TEST_READY.md` at project root.

# E2E Test Infra: Genesis Zero

## Test Philosophy
- **Opaque-Box & Requirement-Driven**: Tests are derived strictly from `ORIGINAL_REQUEST.md` and user-facing contracts. No internal monkey-patching or white-box reliance on private variables.
- **Progressive Testability**: Baseline features can be tested independently of higher-level visualizer or multi-model server states.
- **Robustness & Adversarial Defense**: Negative tests verify strict rejection of malformed inputs, hostile law probes, and graceful degradation on hardware/network constraints.
- **Zero-Flakiness**: Deterministic seeding, explicit timeouts, and isolated temporary resources.

## Feature Inventory & Test Mapping
| # | Feature ID | Feature Description | Tier 1 (Coverage) | Tier 2 (Boundary) | Tier 3 (Cross-Feature) | Tier 4 (Scenario) |
|---|------------|---------------------|:-----------------:|:-----------------:|:----------------------:|:-----------------:|
| 1 | F1.1 | Pytest discovery via pythonpath | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 2 | F1.2 | Domain-aware creature passability & respawn | 5 tests | 5 tests | Pairwise | Scenario 2 |
| 3 | F1.3 | Hostile probe defense & law leak prevention | 5 tests | 5 tests | Pairwise | Scenario 3 |
| 4 | F1.4 | Referee scoring & Law Journal discovery | 5 tests | 5 tests | Pairwise | Scenario 4 |
| 5 | F1.5 | Gate generation performance & timing stability | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 6 | F1.6 | Full test suite clean execution | 5 tests | 5 tests | Pairwise | Scenario 5 |
| 7 | F2.1 | 1-Command cross-platform launcher scripts | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 8 | F2.2 | Automated venv and dependency bootstrap | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 9 | F2.3 | Preflight auto-remediation `--fix` | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 10 | F2.4 | Multi-backend LLM adapter & Reflex fallback | 5 tests | 5 tests | Pairwise | Scenario 4 |
| 11 | F2.5 | Quickstart onboarding verification (<3 mins) | 5 tests | 5 tests | Pairwise | Scenario 1 |
| 12 | F3.1 | Compact diorama map framing & camera presets | 5 tests | 5 tests | Pairwise | Scenario 5 |
| 13 | F3.2 | 3-tier elevation ecosystem rendering | 5 tests | 5 tests | Pairwise | Scenario 2 |
| 14 | F3.3 | Plants/fruits & corpse remains telemetry & rendering | 5 tests | 5 tests | Pairwise | Scenario 2 |
| 15 | F3.4 | 3D morphology for traits & 12 bio-features | 5 tests | 5 tests | Pairwise | Scenario 2 |
| 16 | F3.5 | Real-time Law Journal HUD & event shockwaves | 5 tests | 5 tests | Pairwise | Scenario 4 |
| 17 | F3.6 | Zero external CDN dependency constraint | 5 tests | 5 tests | Pairwise | Scenario 5 |

## Test Architecture
- **Runner**: `pytest tests/e2e -v` (or integrated into master `pytest`)
- **Location**: `tests/e2e/`
  - `test_e2e_tier1_features.py`: Independent happy-path validation for all 17 features.
  - `test_e2e_tier2_boundaries.py`: Extreme limits, invalid parameters, edge conditions, corrupted states.
  - `test_e2e_tier3_combinations.py`: Pairwise interactions (e.g. Hostile probe during REVEAL phase, Water creature teleportation during law event, Offline reflex with multi-backend launcher).
  - `test_e2e_tier4_scenarios.py`: Full end-to-end lifecycle matches from launcher bootstrap to match conclusion and 3D visualizer telemetry consumption.

## Real-World Application Scenarios (Tier 4)
| # | Scenario Name | Features Exercised | Description |
|---|---------------|--------------------|-------------|
| 1 | Zero-Friction First Run | F2.1, F2.2, F2.3, F2.5, F1.1 | Clean setup run with auto-venv, preflight verification, and launch in under 3 minutes. |
| 2 | Multi-Tier Ecology Simulation | F1.2, F3.2, F3.3, F3.4 | Complete match with Land (L1), Water (W1), and Air (A1) species, verifying correct passability, respawn, trait rendering, and food consumption. |
| 3 | Hostile Adversarial Defense | F1.3, F1.6 | Simulated adversary attempting prompt injections, direct law queries, and out-of-turn requests; server cleanly repels all probes. |
| 4 | Law Discovery & Journal Scoring | F1.4, F2.4, F3.5 | Match running with LLM/Reflex, triggering hidden physics laws, recording discoveries in Law Journal, and computing referee scores. |
| 5 | Full Web Visualizer Spectate Loop | F3.1, F3.5, F3.6, F1.6 | Client connects to `/v1/spectate`, receives full stream across LOBBY, RUNNING, REVEAL, verifying diorama assets and zero CDN links. |
| 6 | Offline Auto-Fallback Resilience | F2.4, F2.1, F1.4 | Starting match without local LLM running; system automatically falls back to Reflex controller with clear notifications and completes match. |

## Coverage Thresholds
- **Tier 1**: ≥5 distinct test cases per feature (85+ total)
- **Tier 2**: ≥5 boundary & negative test cases per feature (85+ total)
- **Tier 3**: ≥17 cross-feature pairwise interaction tests
- **Tier 4**: ≥6 full application workflow scenarios
- **Acceptance Criteria**: 100% test pass rate with exit code 0.

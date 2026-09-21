# Project: Genesis Zero — Generation 21 Ecosystem Upgrade & Optimization

## Architecture
Genesis Zero is an artificial life simulation sandbox where creatures possess cognitive strategies (LLM, local model, or reflex) attempting to survive and deduce hidden physical laws of the environment.
- **Simulation Engine**: 6-phase discrete deterministic tick loop in `genesis/tick.py`, backed by 2D toroidal grid `genesis/world.py`.
- **Cognition & Strategy**: 2-tempo loop in `genesis/strategy/`, asynchronous model queries with token billing and circuit breaker, AST-isolated scoring in `genesis/score.py` and `genesis/victory.py`.
- **3D Spectator**: Three.js WebGL rendering with PBR materials, soft shadows, dynamic water/weather, rigged fauna, and procedural Web Audio, 100% offline Zero-CDN compliant.
- **Network & Delivery**: FastAPI + WebSocket `/v1/spectate` non-blocking telemetry broadcast, cross-platform 1-touch launchers, and distribution packaging.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Chebyshev Dist Lookup Table | Precomputed 2D table `_dist_table[24][24]` reducing `dist` cumulative time by > 60% | M1 | Survey 21-2 |
| 2 | Passable Fast Check & Respawn Cache | In-bounds coord check and creature passable cell caching in `try_respawn`, eliminating 79.5k redundant scans | M1 | Survey 21-2 |
| 3 | LawDSL Context Builder Optimization | Stack integer counters, subject dict caching, and direct recent pass-through in `build_ctx` | M1 | Survey 21-2 |
| 4 | Engine Throughput Profiling & Benchmarking | Benchmark script demonstrating >= 900 ticks/s and >= 50% cumulative bottleneck reduction | M1 | Survey 21-2 |
| 5 | 3-Way A/B Benchmark Script | Extend `scripts/b10_ab.py` to compare Frontier LLM vs Local LLM vs Reflex Strategist across 5 seeds | M2 | Survey 21-1 |
| 6 | CI Benchmark Regression Test | New test `tests/test_b10_ab.py` validating mock transport, `--plan` mode, and CLI options | M2 | Survey 21-1 |
| 7 | Active Hypothesis Exploration Heuristic | Tune `genesis/reflex.py` to encourage empirical testing of active hunches | M2 | Survey 21-1 |
| 8 | Code Quality & Ruff Remediation | Resolve 47 lint issues in `tests/` and `scripts/` so `ruff check .` passes with 0 errors | M3 | Survey 21-3 |
| 9 | Test Count & Documentation Synchronization | Update `README.md` test count to reflect 2060 discovered tests via `scripts/count_tests.py --update` | M3 | Survey 21-3 |
| 10 | 3D Graphics & Zero-CDN Verification | Verify `scripts/verify_zero_cdn.py`, `scripts/analyze_graphics_code.py`, `scripts/verify_modular_architecture.py` | M3 | Survey 21-3 |
| 11 | WebSocket Multi-Client Synchronization Check | Validate non-blocking queue isolation in `/v1/spectate` under simulated slow client conditions | M4 | Survey 21-3 |
| 12 | Distribution Packaging & Wheel Validation | Run `scripts/build_dist.py` and verify production wheel and sdist installation | M4 | Survey 21-3 |
| 13 | Full Regression Test Suite Execution | Execute all 2060+ tests, determinism tests, score/victory tests with 100% pass rate | M4 | Survey 21-3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Simulation Engine Throughput Optimization (R2) | Features 1, 2, 3, 4: Chebyshev lookup table, passable caching in `try_respawn`, `build_ctx` stack counters & caching, engine benchmark >= 900 ticks/s and >= 50% cumtime reduction, 100% B-02 determinism pass | none | IN_PROGRESS |
| M2 | LLM Cognition & 3-Way A/B Benchmark Suite (R1) | Features 5, 6, 7: 3-way benchmarking (Frontier vs Local vs Reflex) in `scripts/b10_ab.py`, CI test `tests/test_b10_ab.py`, hypothesis exploration heuristic, 100% B-05/B-10 secrecy pass | none | IN_PROGRESS |
| M3 | Code Quality, Lint Remediation & Documentation Sync (R4) | Features 8, 9, 10: resolve 47 lint errors in `tests/` and `scripts/` for 100% `ruff check .` pass, sync test count in `README.md` (2060 tests), verify Zero-CDN and graphics scripts | none | IN_PROGRESS |
| M4 | Packaging, Multi-Client Sync & Full E2E Acceptance (R3, R4) | Features 11, 12, 13: WebSocket spectate sync validation, wheel/sdist packaging via `scripts/build_dist.py`, 100% pass on 2060+ tests, final forensic integrity audit | M1, M2, M3 | PLANNED |

## Interface Contracts

### M1 ↔ Engine & Invariants
- `World.dist(pos1, pos2)`: Must return integer Chebyshev distance identical to `max(abs(x1-x2), abs(y1-y2))` on toroidal wrap.
- `World.passable(pos, creature)`: Must return identical boolean to original passable logic.
- `lawhook.build_ctx(...)`: Must return identical dictionary keys and values for LawDSL condition evaluation.
- Determinism Contract: Bitwise identical JSONL telemetry stream across 400 ticks with seed 42 (`tests/test_determinism.py`).

### M2 ↔ Benchmark & Secrecy
- `scripts/b10_ab.py`: CLI contract supports `--url`, `--model`, `--out`, `--plan`, `--local-url`, `--local-model`.
- Invariants B-05 & B-10: 0 simulation imports in `genesis/score.py` and `genesis/victory.py`, zero prompt leak of internal tokens, reflex score <= 0.15 (0.00).

### M3 ↔ CI & Linter
- `ruff check .`: Returns exit code 0 across all files in workspace.
- `mypy genesis/` & `mypy net/`: Returns exit code 0.
- `scripts/count_tests.py`: Returns exit code 0 and confirms `README.md` test count matches test collection.

### M4 ↔ Packaging & Acceptance
- `scripts/build_dist.py`: Produces `.whl` and `.tar.gz` in `dist/` containing `web/` and `assets/`.
- Full pytest test suite (2060+ tests): Exit code 0 with 0 failures.

## Code Layout
- Exclusive Write Ownership:
  - Worker M1: `genesis/world.py`, `genesis/creature.py`, `genesis/lawhook.py`, `scripts/benchmark_engine.py`
  - Worker M2: `scripts/b10_ab.py`, `tests/test_b10_ab.py`, `genesis/reflex.py`
  - Worker M3: `tests/` (lint fixes), `scripts/` (lint fixes), `README.md`
  - Worker M4: `scripts/build_dist.py`, `dist/`, final verification scripts

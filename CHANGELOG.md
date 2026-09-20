# Changelog

All notable changes to Genesis Zero will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-20 (Generation 17 Modernization)

### Added
- **Production Multi-Stage Dockerization**:
  - Multi-stage `Dockerfile` leveraging official `astral-sh/uv` builder and lightweight `python:3.11-slim` runtime.
  - Non-root security user `genesis` (UID 1000) with pre-created runtime directories (`/app/runs`, `/app/data/mesh_cache`, `/app/data/models`).
  - Automated container healthcheck pinging `http://localhost:8000/v1/healthz`.
  - Comprehensive `.dockerignore` excluding caches, local secrets (`.env*`), debug logs, and build artifacts.
- **Docker Compose Multi-Service Orchestrator** (`docker-compose.yml`):
  - `match-server`: Simulation backend and Three.js spectator on port `8000:8000`.
  - `mock-llm`: Lightweight mock LLM server (`scripts/fake_model_server.py`) on port `8099:8099` with configurable host binding (`0.0.0.0:8099`) and automated dependency ordering.
- **Modern CI/CD Infrastructure**:
  - GitHub Actions 7-stage workflow (`.github/workflows/ci.yml`):
    1. *Stage 1: Lint* (`ruff check`)
    2. *Stage 2: Typecheck* (`mypy`)
    3. *Stage 3: Security Audit* (`uv audit`)
    4. *Stage 4: Matrix Testing* across Ubuntu, Windows, and macOS on Python 3.11 & 3.12
    5. *Stage 5: Coverage Gate* (enforcing $\ge 90.0\%$ test coverage)
    6. *Stage 6: E2E Smoke Simulation* (`scripts/ci_smoke.py`, checking `match == 1.000`)
    7. *Stage 7: Docker Build Verification* with automated `/v1/healthz` ping
  - GitLab CI pipeline (`.gitlab-ci.yml`) offering 5-stage parity for enterprise self-hosted instances.
- **In-Memory Zero-I/O Referee Scoring Architecture**:
  - `genesis/score.py:score_records()`: Pure in-memory truth-table evaluator calculating creature hypothesis accuracy (`match`), latency (`t_discover`), and rewards (`R_i`, `R_survive`) directly from memory.
  - `genesis/victory.py:victory_standings_from_data()`: Decoupled standings generator computing the three independent titles (`NHA_KHOA_HOC`, `KE_SONG_SOT`, `NGUOI_DAU_TIEN`).
  - Eliminated disk read roundtrips in `net/match.py:compute_victory()`, mitigating Windows `WinError 32` file-locking races and speeding up match completion.
  - Preserved strict Invariant B-10: Scoring modules remain strictly isolated from simulation execution modules (verified via AST in `tests/test_score.py::test_khong_import_sim`).
- **Comprehensive Technical Documentation**:
  - `docs/ARCHITECTURE.md`: Subsystem topology, 6-phase lifecycle flowchart, zero-I/O scoring architecture, and performance optimization details with Mermaid diagrams.
  - `docs/DEPLOYMENT.md`: Production deployment guide detailing Docker single-container runs, Docker Compose multi-service setup, reverse proxying (Nginx/Caddy), environment variables, and Linux host volume mount permissions.
- **Standardized `BaseStrategist` Class**:
  - Added `class BaseStrategist` in `genesis/strategy/base.py` providing no-op default implementations for all cognitive lifecycle methods (`begin_tick`, `take_says`, `take_shift`, `observe`).

### Changed
- **Core Simulation Performance Optimizations** (Average throughput: **854.77 ticks/sec**, 2.25x speedup over baseline):
  - *Single-Pass Monotonic Chebyshev Distance*: In `genesis/lawhook.py:build_ctx`, unified 3 separate radius loops into a single pass with `range(max(1, d), 4)` accumulation, reducing `world.dist()` calls by 66.7% while safely handling $d=0$ coincident entity positions.
  - *Pointer Identity Passability Caching*: In `genesis/world.py:passable` and `touchable`, replaced dataclass value equality `==` with reference pointer identity `cached[0] is traits and cached[1] is kit`, eliminating 191,551 redundant `Traits.__eq__` invocations per match.
  - *Fast RNG Seed Derivation*: In `genesis/tick.py:creature_rng`, replaced MD5 hex string slicing with direct byte unpacking `int.from_bytes(digest[:8], "big")`, maintaining bit-identical determinism (Invariant B-02) without string allocations.
  - *Precomputed Static Tile Pools*: In `genesis/world.py:World.__init__`, precalculated `plain_tiles` and `water_tiles` as immutable tuples, cutting 460,800 full-grid iterations per match during plant and algae generation.
  - *Single-Pass Greedy Pathfinding*: In `genesis/reflex.py`, optimized candidate neighbor evaluation to compute distance once per passable tile.
- **Architectural & Type Safety Modernization**:
  - Refactored `Strategist` Protocol in `genesis/strategy/base.py` with optional lifecycle hooks, preserving backward compatibility with duck-typed adversarial stubs.
  - Normalized `take_shift` return signature to `tuple[str, str] | None` matching trait swap semantics.
  - Removed hardcoded local Windows path (`E:/tool/mcp/terra_forge`) from `pyproject.toml` `mypy_path` in favor of portable relative paths.
  - Added `typecheck` target (`mypy genesis net client`) and universal lockfile flags (`--all-extras --universal`) to `Makefile`.
  - Synchronized `README.md` test collection metrics via `scripts/count_tests.py --update-readme` to 1,889 tests across 124 files.

### Fixed
- Fixed 0 ruff lint violations across all modules (`genesis`, `net`, `tests`, `scripts`, `client`, `tools`).
- Fixed 0 mypy static typing errors across `genesis`, `net`, and `client`.
- 100% test pass rate maintained with 0 failures and 0 errors across 1,889 collected tests.
- Mitigated potential `WinError 32` file locking errors on Windows when computing match results concurrently.

---

## [1.0.0] - 2026-09-17 (Baseline Release)

### Added
- Toroidal 24×24 multi-agent simulation sandbox with 3-tier ecology (Water, Land, Air) and Karst cave networks.
- LawDSL v5 hidden physical law generator and evaluator.
- Generational evolution with stochastic genetic mutation and trait shifts.
- Real-time 3D WebGL diorama spectator (`web/watch3d.html`) with Three.js rendering and procedural Web Audio.
- Multi-client FastAPI match coordinator with hostile probe filtering.
- Initial test suite establishing baseline of 1,833 collected tests.

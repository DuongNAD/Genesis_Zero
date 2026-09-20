# Genesis Zero — Comprehensive Architectural Upgrade Roadmap

**Document Version**: 2.0.0  
**Target Sandbox**: Genesis Zero Multi-Agent Evolutionary Simulation  
**Status**: Active Strategy  
**Last Updated**: 2026-09-18  

---

## Executive Summary

Genesis Zero has matured from an experimental LLM physical-induction sandbox into a full-scale multi-agent evolutionary ecosystem featuring:
- Deterministic 6-phase world simulation with hidden physical law generation (LawDSL).
- Multi-tier spatial biomes (water, land, air, subterranean karst caves).
- Generational reproduction with stochastic genetic mutation and trait shift dynamics.
- Real-time 3D WebGL isometric spectator with procedural audio synthesis.
- Multi-client HTTP/WebSocket networking with zero-information-leakage telemetry.

This document articulates the long-term architectural transformation of Genesis Zero across three progressive phases, transitioning the codebase from a single-process simulation into a horizontally scalable, GPU-accelerated, distributed AI research environment.

```
+----------------------------------------------------------------------------------------------------+
|                                    ARCHITECTURAL ROADMAP OVERVIEW                                  |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  PHASE 1: Core Modularization & Maintainability (M1 - M3, Completed)                              |
|  * Packaging standardization: Root net_config.py -> net/config.py with root compatibility shim    |
|  * God module decomposition: genesis/strategist.py -> genesis/strategy/ modular package            |
|  * Platform centralization: genesis/platform.py (Windows UTF-8 console, subprocess env, python)    |
|  * Automated log hygiene: runs/ retention pruning & rotation script (scripts/prune_runs.py)       |
|  * Telemetry formalization: docs/TELEMETRY_CONTRACT.md canonical schema & legacy dual-key alias   |
|                                                                                                    |
|  PHASE 2: Simulation Scaling, Asynchronous Physics & High-Throughput Networking (Intermediate)    |
|  * Multi-match concurrency: net/state.py MatchManager hosting independent parallel match rooms     |
|  * In-memory referee scoring: zero-I/O victory computation without disk roundtrips                 |
|  * Spatial partitioning: QuadTree / Spatial Hash grid for O(1) collision and line-of-sight checks |
|  * Async LLM streaming pipeline: batch token queueing and adaptive HTTP keep-alive connection pool|
|  * Pydantic V2 state serialization: binary checkpointing (SimState.to_bytes / from_bytes)         |
|                                                                                                    |
|  PHASE 3: AAA Asset Streaming, GPU Compute Shaders & Distributed Multi-Agent Training (Advanced)  |
|  * GPU Compute Shaders: WebGPU / Vulkan accelerated terrain erosion and hydrology flow fields      |
|  * Procedural Asset Pipeline: Unified tools/blender CLI consolidating 12+ procedural generators    |
|  * Distributed Multi-Agent Rollout: Ray/Celery distributed worker fleet for multi-epoch RL training|
|  * Dynamic Level-of-Detail (LOD): Hierarchical octree mesh streaming for infinite landscape view   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## Phase 1: Core Modularization & Maintainability (M1 – M3)

### 1.1 Objectives Achieved
- **Clean Packaging Namespacing**:
  - Relocated root `net_config.py` into canonical package module `net/config.py`.
  - Installed a lightweight backward-compatible root shim `net_config.py` re-exporting all constants and defaults (`MATCH_PORT`, `SPECTATE_PORT`, `DEFAULT_HOST`), maintaining 100% compatibility with legacy scripts and tests.
  - Updated `pyproject.toml` to maintain clean distribution packaging.
- **Decomposition of `genesis/strategist.py` Monolith**:
  - Refactored the 1,409-line monolith into structured, single-responsibility modules under `genesis/strategy/`:
    - `genesis/strategy/base.py`: Protocol `Strategist`, `ActiveGoal`, `payload_to_goal`.
    - `genesis/strategy/reflex.py`: Pure-instinct heuristic goal selection `ReflexStrategist`.
    - `genesis/strategy/remote.py`: Thread-safe multi-client queue reader `RemoteClientStrategist`.
    - `genesis/strategy/llm.py`: Local LLM client orchestration, circuit breaker, slot management, and sensory field notes `LlmStrategist`.
    - `genesis/strategy/law_schema.py`: Constrained grammar generation (`legal_args`, `schema_for`).
  - Preserved 100% symbol re-exports in facade `genesis/strategist.py` with zero regressions across 1,700+ tests.
- **Centralized Platform & Console Utilities**:
  - Introduced `genesis/platform.py` unifying Windows UTF-8 console stream reconfiguration (`configure_console_encoding`), subprocess environment injection (`utf8_subprocess_env`), and Python interpreter resolution (`find_python_executable`).
  - Refactored entrypoints (`scripts/launch.py`, `scripts/preflight.py`, `genesis/run.py`) to eliminate duplicated encoding boilerplate.
- **Automated Disk Hygiene**:
  - Implemented `genesis/util/log_cleanup.py` and `scripts/prune_runs.py` providing automated pruning of orphaned run JSONL and truth files with configurable `--keep` (default 50) and `--max-days` retention policies.
- **Telemetry Schema Formalization**:
  - Published authoritative `docs/TELEMETRY_CONTRACT.md` detailing the envelope, frame, dossier, and event payloads with canonical keys and legacy aliases.

---

## Phase 2: Simulation Scaling, Asynchronous Physics & High-Throughput Networking

### 2.1 Multi-Match Concurrent Engine (`MatchManager`)
- **Current Limitation**: `net/state.py` exposes a single global `runner = MatchRunner()`, restricting a Genesis Zero server instance to exactly one active match.
- **Target Architecture**:
  - Replace the global singleton with `MatchManager`:
    ```python
    class MatchManager:
        def __init__(self) -> None:
            self._matches: dict[str, MatchRunner] = {}
        
        def create_match(self, seed: int, map_name: str) -> MatchRunner: ...
        def get_match(self, match_id: str) -> MatchRunner | None: ...
        def list_active_matches(self) -> list[MatchSummary]: ...
    ```
  - Expose room-scoped endpoints:
    - `GET /v1/matches` — List active simulation rooms.
    - `POST /v1/matches` — Provision custom match instance.
    - `WS /v1/matches/{match_id}/spectate` — Room-specific spectator stream.
    - `POST /v1/matches/{match_id}/decision` — Room-specific client actions.

### 2.2 In-Memory Scoring & Victory Pipeline
- **Current Limitation**: `compute_victory()` flushes simulation logs and truth files to disk, and then immediately re-opens and parses them via `from_files(log_p, truth_p)`.
- **Target Architecture**:
  - Add in-memory scoring evaluator `genesis.score::score_records(records: list[dict], truth: dict) -> list[dict]`.
  - Maintain an append-only in-memory telemetry buffer in `MatchRunner`.
  - Eliminate file I/O latency, lock contention, and Windows file-sharing violations during rapid match cycling.

### 2.3 Spatial Partitioning & Grid Optimizations
- **Current Limitation**: Proximity and line-of-sight checks iterate over all active creatures ($O(N^2)$).
- **Target Architecture**:
  - Implement a 2D Spatial Hash Grid (`genesis/spatial.py`) indexing organisms by grid cells ($4 \times 4$ blocks).
  - Reduce creature neighbor queries from $O(N)$ to $O(1 + k)$ where $k$ is local cell occupancy.
  - Accelerate large-scale simulations ($N \ge 100$ organisms per match).

### 2.4 State Serialization & Checkpointing
- **Target Architecture**:
  - Implement deterministic binary snapshotting (`SimState.to_bytes() / SimState.from_bytes()`).
  - Enable instantaneous match save/resume, state replay debugging, and seamless live server migration without interrupting connected clients.

---

## Phase 3: AAA Asset Streaming, GPU Compute Shaders & Distributed Multi-Agent Training

### 3.1 WebGPU & Compute Shader Acceleration
- **Target Architecture**:
  - Port hydraulic droplet erosion and thermal talus relaxation kernels from CPU/NumPy to WebGPU compute shaders in `web/` and Vulkan/CUDA shaders in `terra_forge/`.
  - Achieve real-time procedural terrain deformation ($> 100,000\text{ drops/sec}$) responding dynamically to weather rainstorm events during live matches.

### 3.2 Unified Procedural Asset Toolchain
- **Current Limitation**: Over 12 individual generator scripts (`generate_canopy_trees_*.py`, `generate_arid_succulents.py`, `generate_aquatic_wetland.py`) duplicate Blender material and mesh boilerplate.
- **Target Architecture**:
  - Consolidate under a unified Blender procedural generator CLI:
    ```bash
    python -m tools.blender.generator --biome alpine --density high --export-glb
    ```
  - Standardize material graphs into reusable node groups (`tools/blender/materials/`) supporting triplanar slope blending, subsurface scattering (SSS), and vertex-color baking.

### 3.3 Distributed Multi-Agent Rollout Fleet
- **Target Architecture**:
  - Interface Genesis Zero with Ray or Celery distributed task queues.
  - Enable massive parallel rollouts across compute clusters:
    - 50 concurrent headless simulation instances collecting cognitive field notes.
    - Asynchronous training of LoRA adapters and cognitive models (Qwen / Llama) on empirical law induction tasks.
    - Automated benchmark evaluation tracking player Elo ratings and physical discovery speeds.

---

## Milestones & Implementation Matrix

| Phase | Milestone | Focus Areas | Key Deliverables | Verification Gateway |
|---|---|---|---|---|
| **Phase 1** | M1: Defect Remediation | UTF-8, Preflight, Windows streams | UTF-8 stream hardening, LLM active probe | `python scripts/ci_quick.py` |
| **Phase 1** | M2: Performance | NavMesh, FNV-1a JIT, Vectorization | 2,079x spawn mask speedup, JIT checksum | `python scripts/ci_smoke.py` |
| **Phase 1** | M3: Architecture | Packaging, Strategy decomposition | `net/config.py`, `genesis/strategy/`, docs | 100% test pass, clean imports |
| **Phase 2** | M4: Multi-Match | MatchManager, Multi-room server | `/v1/matches/{id}`, Room WebSocket | Multi-room concurrency test |
| **Phase 2** | M5: In-Memory Referee | Zero-I/O scoring, Spatial hash | `score_records()`, Spatial Hash Grid | Benchmark match cycle latency |
| **Phase 3** | M6: GPU Compute | WebGPU shaders, Erosion runtime | Real-time droplet shader, 60 FPS viewer | WebGL frame rate benchmark |
| **Phase 3** | M7: Distributed RL | Ray cluster rollout, LoRA training | Headless batch workers, LoRA trainer | Multi-epoch convergence suite |

---

## Conclusion

The Genesis Zero architectural roadmap establishes a disciplined, phased pathway from an initial standalone experimental sandbox to a robust, enterprise-grade multi-agent simulation platform. By adhering strictly to interface contracts, non-breaking modularization, and deterministic empirical testing, Genesis Zero guarantees world-class performance and architectural elegance across all future evolutionary milestones.

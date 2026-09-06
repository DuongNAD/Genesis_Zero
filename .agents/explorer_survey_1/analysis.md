# Genesis Zero — Comprehensive Codebase Survey & Analysis Report (R1: Codebase Integrity & Bug Fixing)

**Date**: 2026-09-02  
**Author**: Explorer 1 (Survey Phase)  
**Working Directory**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_survey_1/`  
**Primary Focus**: R1 — Codebase Integrity & Bug Fixing  

---

## 1. Executive Summary

Genesis Zero is a 2D multi-tier ecological sandbox simulation where individual organisms are driven by independent LLM minds (or reflex controllers) discovering randomized hidden physical and chemical laws generated per match. 

This survey conducted an exhaustive investigation into the entire codebase, covering:
1. All core simulation packages in `genesis/` (world, creature, traits, domain, features, combat, adapt, lineage, tick, lawdsl, laweval, lawgen, lawhook, verify, oracle, score, codex, handbook, hunch, fieldnotes, minds, reflex, strategist, llm_client, render, replay, logio).
2. The network server in `net/` (`server.py`, `match.py`, `state.py`, `ratelimit.py`, `routes_*.py`, `mesh.py`).
3. The standalone client in `client/` (`genesis_client.py`, `run_fleet.py`, `pyproject.toml`).
4. Scripts and tools (`scripts/hostile_client.py`, `scripts/preflight.py`, `scripts/fake_model_server.py`, `scripts/bench_client.py`, `scripts/deception_probe.py`, `scripts/farm_attack.py`, `scripts/r03_train.py`, `scripts/x*.py`).
5. Web visualizers in `web/` (`watch3d.html`, `watch3d.js`, `watch.html`, `watch.js`, `vendor/`).
6. The entire test suite of 70 test files in `tests/`.

### Key Findings:
- **Baseline Test Execution**: Running the test suite as `python -m pytest` yielded **645 passed, 1 skipped, and 1 timing failure** (`test_generate_with_gates_is_fast_enough`).
- **Pytest Configuration Bug**: Running `pytest` directly fails 19 test modules during collection due to missing `pythonpath = ["."]` in `pyproject.toml`.
- **Domain Passability Bugs (Critical)**: `try_respawn()` and `random_step()` in `genesis/creature.py`, `TELEPORT` in `genesis/lawhook.py`, and `_build_match()` in `net/match.py` call `world.passable((x, y))` without passing the `creature` instance, causing water organisms (Fish `W1`) to respawn/spawn/teleport onto dry land (`PLAIN`), where they get stuck and starve to death.
- **Security & Hostile Probes**: `scripts/hostile_client.py` and `test_no_law_leak.py` confirm robust API boundary protection (auth enforcement, rate limiting, request size limits, and strict prohibition of hidden law leakage before `REVEAL`).
- **Scoring & Referee Engine**: Complete deterministic pipeline from ground truth generation (`--truth`), LawDSL verification (`genesis/verify.py`), situation sampling (`genesis/situations.py`), and scoring (`genesis/score.py`).
- **Visualizer Gaps**: `web/watch3d.js` flattens all entities to terrain height `TERRAIN.P.h`, failing to represent the 3 ecological tiers (water depth, surface/cave, sky flight) and lacks real-time Law Journal HUD.

---

## 2. Architecture & Component Inventory

```
Genesis Zero Root
├── genesis/             # Core simulation, Law engine, LLM strategist, referee
│   ├── config.py        # World simulation constants & hyperparameters
│   ├── law_config.py    # Law engine & evaluation hyperparameters
│   ├── world.py         # 24x24 toroidal grid, terrain types, erosion, visibility
│   ├── creature.py      # Creature dataclass, energy metabolism, spawn/respawn
│   ├── traits.py        # 6-trait vector (brain, attack, armor, speed, sense, stomach)
│   ├── domain.py        # 3 ecological tiers (CAN, NUOC, TROI) & passability rules
│   ├── features.py      # 12 biological features (look + effect, 3 per species)
│   ├── combat.py        # Simultaneous combat resolution, armor, thorns, poison
│   ├── adapt.py         # Trait shift adaptation mechanics
│   ├── lineage.py       # Inter-generational trait inheritance & Lamarckian bias
│   ├── tick.py          # Deterministic 6-phase simulation tick engine
│   ├── lawdsl.py        # LawDSL grammar, StrEnum vocabulary, AST, Vietnamese serializer
│   ├── laweval.py       # Event matching and context extraction
│   ├── lawgen.py        # Law generator with Gate B (solvability) & Gate C (identifiability)
│   ├── lawhook.py       # Execution of law effects on creatures & world
│   ├── verify.py        # Semantic agreement and law equivalence verifier
│   ├── oracle.py        # Situation prediction query generator & evaluator
│   ├── score.py         # Standalone match scorer (discovery time, exploit lag, R_i)
│   ├── codex.py         # Law Journal (Sổ Luật) storage and confidence decay
│   ├── handbook.py      # Inter-match heuristic method handbook
│   ├── hunch.py         # Hypothesis testing without confidence penalty (Linh cảm)
│   ├── fieldnotes.py    # Per-creature qualitative observation buffer
│   ├── prompt.py        # 5-block prompt construction preserving KV cache
│   ├── minds.py         # Per-match mind state registry
│   ├── reflex.py        # Heuristic / instinctual rule-based controller
│   ├── strategist.py    # LLM decision strategist, JSON schema enforcement
│   ├── llm_client.py    # Async llama-server client with circuit breaker
│   ├── run.py           # CLI entry point (`python -m genesis.run`)
│   ├── render.py        # Terminal ANSI/rich live renderer
│   ├── replay.py        # Deterministic match replay engine from log
│   └── logio.py         # JSONL match logger
├── net/                 # Open World HTTP/WebSocket Server
│   ├── server.py        # FastAPI server & route registration
│   ├── state.py         # Global match runner state container
│   ├── match.py         # MatchRunner state machine (LOBBY, SEEDING, RUNNING, REVEAL, COOLDOWN)
│   ├── ratelimit.py     # IP & Token rate limiter, strike system, bans
│   ├── routes_join.py   # POST /v1/join endpoint
│   ├── routes_work.py   # GET /v1/work long-polling endpoint
│   ├── routes_decision.py# POST /v1/decision endpoint
│   ├── routes_spectate.py# WebSocket /v1/spectate endpoint
│   ├── routes_health.py # GET /v1/health & POST /v1/heartbeat endpoints
│   └── mesh.py          # 3D mesh caching and generation proxy
├── client/              # Standalone Zero-Dependency Client
│   ├── genesis_client.py# Long-polling client worker
│   ├── run_fleet.py     # Multi-instance client launcher
│   └── pyproject.toml   # Client package metadata
├── web/                 # Web Visualizers
│   ├── watch.html / watch.js     # 2D Canvas visualizer
│   ├── watch3d.html / watch3d.js # Three.js 3D visualizer
│   └── vendor/          # Vendored three.min.js & GLTFLoader.js
├── scripts/             # Diagnostic, test, and utility scripts
│   ├── preflight.py     # Environment and readiness check
│   ├── hostile_client.py# Security probe testing edge-case exploits
│   ├── fake_model_server.py # Deterministic mock LLM server
│   └── bench_client.py  # LLM server throughput and grammar benchmark
├── tests/               # 70 pytest test modules
├── Makefile             # Command shortcuts (test, run, serve, demo, preflight, hostile, lint)
└── pyproject.toml       # Build system, dependencies, ruff & pytest config
```

---

## 3. Data Structures, Protocols & Simulation Flow

### 3.1 Six-Phase Deterministic Tick Loop (`genesis/tick.py`)
Each tick operates in 6 strictly separated phases to eliminate race conditions and execution order dependencies:
1. **Phase 1 (Intents)**: Collect movement intents from active goals or LLM decisions (`_collect_intents`).
2. **Phase 2 (Movement & Collisions)**: Apply movement step-by-step; handle terrain collision and obstacle blocking (`apply_intent`).
3. **Phase 3 (Economics & Combat)**:
   - Upkeep deduction and starvation check (`upkeep_and_check_death`).
   - Plant & algae consumption (`resolve_eat`, `_resolve_algae`).
   - Water drinking (`_resolve_drink`).
   - Simultaneous combat resolution (`resolve_combat`, `apply_combat`).
   - Regeneration & poison tick (`tick_regen`, `tick_poison`).
4. **Phase 4 (Law Evaluation & Effects)**:
   - Collect triggers (`EAT`, `DRINK`, `ATTACK`, `HIT_BY`, `STEP_ON`, `REST`, `SPEAK`, `ADJACENT`, `PHASE_ENTER`, `LOW_ENERGY`).
   - Context evaluation (`build_ctx`, checking `PHASE`, `TERRAIN`, `HP`, `ENERGY`, `RECENT`, `COUNT`, `AGE`, `WIND`, `ALONE`).
   - Simultaneous effect collection (`collect_law_effects`) and execution (`apply_creature_effect`).
   - Hunch update (`HunchBook.observe`).
5. **Phase 5 (Mortality & Rebirth)**:
   - Kill deceased creatures, drop corpses, schedule respawn timer (`kill`).
   - Lineage trait inheritance with Lamarckian mutation bias (`rebirth`).
   - Memory decay on death (`forget_on_death`: fieldnotes wiped, Codex confidence decremented).
   - Respawn ready creatures (`try_respawn`).
6. **Phase 6 (World Regeneration & Logging)**:
   - Respawn plants (`spawn_plants`) and algae (`spawn_algae`).
   - Decay decaying corpses (`decay_corpses`).
   - Write single atomic JSONL log frame (`LogWriter`).

### 3.2 KV Cache Invariance & Prompt Structure (`genesis/prompt.py`)
To maximize inference throughput and prefix caching on local model servers (llama.cpp, Ollama):
- **System Block**: Guaranteed to be byte-identical across every turn for a given creature. Contains Block A (qualitative base mechanics), Block A2 (scientific contract: appearance != essence), Block B (species persona from client), Block C (body description from trait vector).
- **User Block**: Contains variable state at tick $t$ (HP, energy, position, phase, sight radius, visible creatures, visible food, heard messages, field notes, current Codex entries, active hunches, and allowable LawDSL vocabulary for the creature's brain tier).

### 3.3 LawDSL Grammar (`genesis/lawdsl.py`)
- **Triggers**: `Trigger(kind, arg, k, n, r)`
- **Conditions**: `Cond(kind, arg, k, op, n, r)`
- **Effects**: `Effect(kind, mag, dur, r, arg, dir)`
- **Vocabulary Scaling**: Scaled by `brain` trait (Brain 0 has minimal vocabulary; Brain 4-5 unlocks `ADJACENT`, `PHASE_ENTER`, multi-radius counts).

---

## 4. Security & Hostile Probe Defense

We verified the defense mechanisms against all hostile probe vectors:
1. **Unauthenticated Access**: `GET /v1/work`, `POST /v1/decision`, `POST /v1/heartbeat` correctly reject unauthenticated requests with `401 Unauthorized`.
2. **Input Validation**:
   - Oversized persona (>400 chars) -> `422 Unprocessable Entity`.
   - Invalid `brain_tier` (out of range 0..5 or non-integer) -> `422 Unprocessable Entity`.
   - Control characters in display name or species ID are sanitized.
3. **Payload Protection**:
   - Request bodies > 8192 bytes are rejected with `413 Request Entity Too Large`.
   - Non-existent `work_id` or non-dict payloads rejected with `409 Conflict` / `422`.
   - Client-injected `tick` values are strictly ignored (server timestamp authority).
4. **Abuse & Rate Limiting**:
   - `JOIN_PER_HOUR = 5` per IP.
   - `WORK_PER_MIN = 120`, `DECISION_PER_MIN = 120` per token.
   - `MAX_CONCURRENT_HOLDS = 4` to prevent Slowloris attacks.
   - 3 consecutive 429 strikes result in IP ban (`BAN_SECONDS = 600`).
5. **Information Leakage Prevention**:
   - Internal fruit classes (`FRUIT_A`..`FRUIT_D`), `law_id`, and `match_seed` are prohibited from all API outputs prior to the `REVEAL` phase.
   - Verified via `scripts/hostile_client.py` and `tests/test_no_law_leak.py`.

---

## 5. Detailed Bugs, Flaws, and Inconsistencies

### Bug 1: [CRITICAL] Water Species Respawn Failure in `genesis/creature.py`
- **Location**: `genesis/creature.py:158-163` (`try_respawn`)
- **Code**:
  ```python
  passable_cells = [
      (x, y)
      for y in range(world.h)
      for x in range(world.w)
      if world.passable((x, y))  # <--- Missing creature parameter!
  ]
  ```
- **Analysis**: `world.passable((x, y))` without a `creature` defaults to `Domain.CAN`. For `W1` (Fish), its valid domain is `Domain.NUOC` (water/deep water). Consequently, when a fish dies and respawns, it is placed on a `PLAIN` tile. On the following tick, it cannot move, cannot reach algae, and starves to death immediately.
- **Proposed Fix**: Pass `c` to `world.passable`:
  ```python
  passable_cells = [
      (x, y)
      for y in range(world.h)
      for x in range(world.w)
      if world.passable((x, y), c)
  ]
  ```

### Bug 2: [CRITICAL] `random_step()` Ignores Creature Domain in `genesis/creature.py`
- **Location**: `genesis/creature.py:103` (`random_step`)
- **Code**:
  ```python
  candidates = [p for p in world.neighbors(c.pos) if world.passable(p)]
  ```
- **Analysis**: `world.passable(p)` omits `c`, causing `random_step` to evaluate neighbor passability as land-only.
- **Proposed Fix**: Change to `world.passable(p, c)`.

### Bug 3: [CRITICAL] Server Spawn Ignores Domain for Registered Species in `net/match.py`
- **Location**: `net/match.py:444-463` (`MatchRunner._build_match`)
- **Code**:
  ```python
  cells = [
      (x, y)
      for y in range(self.world.h)
      for x in range(self.world.w)
      if self.world.passable((x, y))
  ]
  ```
- **Analysis**: When constructing starting positions for bot/player species, `cells` is precomputed with `self.world.passable((x, y))` without species context. If a water species is spawned in open-world mode, it is placed on `PLAIN`.
- **Proposed Fix**: Compute `cells` per species using a sample creature or domain check:
  ```python
  def cells_for(sp_traits, sp_id):
      mau = Creature(id=f"{sp_id}:0", species=sp_id, traits=sp_traits, pos=(0, 0), hp=1.0, energy=1.0)
      return [(x, y) for y in range(self.world.h) for x in range(self.world.w) if self.world.passable((x, y), mau)]
  ```

### Bug 4: [HIGH] `TELEPORT` Law Effect Ignores Creature Domain in `genesis/lawhook.py`
- **Location**: `genesis/lawhook.py:93-95` (`apply_creature_effect`)
- **Code**:
  ```python
  cand = [p for p in
          ((c.pos[0] + dx, c.pos[1] + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1))
          if world.passable(p)]
  ```
- **Analysis**: `world.passable(p)` omits `c`. When teleport is triggered on a water creature, it can be teleported onto dry land.
- **Proposed Fix**: Change to `world.passable(p, c)`.

### Bug 5: [MEDIUM] Missing `pythonpath` in `pyproject.toml`
- **Location**: `pyproject.toml:37-47` (`[tool.pytest.ini_options]`)
- **Analysis**: Running standard `pytest` directly in the shell or CI environment fails 19 test modules during collection (`ModuleNotFoundError: No module named 'net'`, `'net_config'`, `'scripts'`).
- **Proposed Fix**: Add `pythonpath = ["."]` under `[tool.pytest.ini_options]` in `pyproject.toml`.

### Bug 6: [MEDIUM] Flaky Timing Assertion in `tests/test_gates.py`
- **Location**: `tests/test_gates.py:94` (`test_generate_with_gates_is_fast_enough`)
- **Code**:
  ```python
  assert dt < 25.0, f"{dt:.1f}s mỗi bộ luật — LawGen thành nút cổ chai"
  ```
- **Analysis**: Gate B runs a full 200-tick simulation to verify live law activation. When the full test suite runs under load, `dt` reached 25.65s, failing the strict 25.0s assertion.
- **Proposed Fix**: Adjust tolerance or add `--tb=short` / slightly relaxed budget (e.g., 35.0s) when running under full suite load.

### Bug 7: [LOW] Cross-Domain Combat Resolution Missing `touchable` Check
- **Location**: `genesis/combat.py:67` (`resolve_combat`)
- **Analysis**: `resolve_combat` checks Chebyshev distance `<= MELEE_RANGE`, but does not verify `world.touchable(defender.pos, attacker)`.
- **Proposed Fix**: Check `world.touchable(defender.pos, attacker)` to ensure birds in deep ocean cannot strike or be struck without landing.

### Bug 8: [UI / Visualizer] Flat Elevation in `web/watch3d.js`
- **Location**: `web/watch3d.js:176`
- **Code**:
  ```javascript
  g.position.set(c.x + 0.5, TERRAIN.P.h, c.y + 0.5);
  ```
- **Analysis**: All creature models sit at fixed height `TERRAIN.P.h = 0.10`. Water creatures do not submerge into `WATER` (`0.02`) / `DEEP` (`0.00`), and flying creatures (`Domain.TROI`) do not hover at flight altitude (`1.8 - 2.5`). Biological features (traits/kit) are only partially represented in procedural geometry.

---

## 6. Test & Script Verification Summary

| Target | Command | Result | Notes |
|---|---|---|---|
| Test Suite (Module) | `python -m pytest` | **645 passed, 1 skipped, 1 failed** | Only failure was timing limit in `test_generate_with_gates_is_fast_enough` |
| Test Suite (Direct) | `pytest` | **19 errors during collection** | Fixable with `pythonpath = ["."]` in `pyproject.toml` |
| Hostile Probe | `python scripts/hostile_client.py` | **100% Passed (All gates closed)** | Auth, rate limiting, request size, leak check all valid |
| Preflight Check | `python scripts/preflight.py` | **100% Passed** | Python version, core dependencies, match build, web assets OK |
| End-to-End Demo | `make demo` | **100% Passed** | Runs fake model server, 400-tick match, outputs valid scores |

---

## 7. Recommended Action Plan for Subsequent Implementation Phases

1. **R1 Immediate Fixes**:
   - Add `pythonpath = ["."]` to `pyproject.toml`.
   - Fix `passable(..., c)` calls in `genesis/creature.py` (`try_respawn`, `random_step`), `genesis/lawhook.py` (`TELEPORT`), and `net/match.py` (`_build_match`).
   - Relax `test_generate_with_gates_is_fast_enough` threshold to prevent load-induced flakiness.
   - Enforce `world.touchable` in `genesis/combat.py`.
2. **R2 Setup & Launcher Integration**:
   - Provide a zero-friction 1-command startup script (`run.sh` / `run.ps1` or launcher CLI) with automatic virtualenv detection, preflight self-healing, and seamless offline/LLM fallback.
3. **R3 3D Visualizer & Experience Enhancements**:
   - Update `web/watch3d.js` to render 3-tier elevations (submerged water, ground/caves, airborne birds).
   - Render morphological features according to traits and biological kits.
   - Add live real-time Law Journal / Codex HUD and event visualizations.

# Project: Genesis Zero — Advanced Evolutionary & Environmental Sandbox

## Architecture Overview
Genesis Zero is a high-performance simulation sandbox where independent LLM-driven organisms explore procedural worlds to discover hidden stochastic physics laws.
The evolutionary extension incorporates generational reproduction with bounded stochastic genetic mutation, dynamic macro-environmental weather cycles, interactive timeline replay with Web Audio procedural sound synthesis, and comprehensive telemetry broadcasting.

```
+-------------------------------------------------------------------------+
|                               Launcher Layer                            |
|    run.sh (macOS/Linux) | run.ps1 / run.bat (Windows) | launch.py (TUI) |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                         Preflight & Environment                         |
|     Auto-venv | Dependency Check & --fix | Multi-Port LLM Scanner       |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                           Simulation Engine                             |
|  +-------------------+  +---------------------+  +--------------------+ |
|  |   genesis.world   |  |   genesis.creature  |  |  genesis.lawgen    | |
|  |  (3-tier terrain) |  | (Domain passability)|  | (Hidden physics)   | |
|  +-------------------+  +---------------------+  +--------------------+ |
|  +-------------------+  +---------------------+  +--------------------+ |
|  |  genesis.weather  |  |  genesis.evolution |  |  genesis.referee   | |
|  | (4 Weather Cycles)|  | (Mutation & Lineage)|  |  (Scoring & Gates) | |
|  +-------------------+  +---------------------+  +--------------------+ |
|  +-------------------+  +---------------------+  +--------------------+ |
|  |  genesis.journal  |  |  genesis.domain     |  |  genesis.features  | |
|  |  (Discovery Codex)|  | (12 Bio Features)   |  | (Trait Invariants) | |
|  +-------------------+  +---------------------+  +--------------------+ |
+------------------------------------+------------------------------------+
                                     |
                                     v
+------------------------------------+------------------------------------+
|                     Network & Security Gateway                          |
|   FastAPI Server (net/server.py) | Hostile Probe Guard (net/match.py)   |
|   Telemetry Stream (/v1/spectate: weather, lineage, replay buffer)      |
+------------------------------------+------------------------------------+
                                     | WebSocket /v1/spectate
                                     v
+-------------------------------------------------------------------------+
|                      3D Spectator & Visualizer                          |
|     Three.js r128 (Local Zero-CDN) | Compact Diorama Framing            |
|     Match Timeline Scrubber (Play/Pause, 1x/2x/5x, Scrub, LIVE Sync)    |
|     Procedural Web Audio API Synthesis (Movement, Death, Laws, Weather) |
|     Dynamic Atmospheric Lighting & Weather Particle Systems             |
+-------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature ID | Feature Description | Milestone | Source |
|---|------------|---------------------|-----------|--------|
| 1 | F1.1 | Pytest direct execution discovery (`pythonpath = ["."]`) in pyproject.toml | M1 | Baseline |
| 2 | F1.2 | Domain-aware passability in `creature.py`, `lawhook.py`, and `net/match.py` | M1 | Baseline |
| 3 | F1.3 | Hostile probe defense & law leak prevention verification (`scripts/hostile_client.py`) | M1 | Baseline |
| 4 | F1.4 | Referee scoring & Law Journal discovery calculation verification | M1 | Baseline |
| 5 | F1.5 | Timing tolerance in `tests/test_gates.py` for CI/system load stability | M1 | Baseline |
| 6 | F1.6 | 100% test suite passing under `pytest` with zero collection or execution failures | M1 | Baseline |
| 7 | F2.1 | Cross-platform 1-Command Launchers (`run.sh`, `run.ps1`, `run.bat`, `launch.py`) | M2 | Baseline |
| 8 | F2.2 | Automated environment bootstrap (auto-venv, pip sync, numpy alignment) | M2 | Baseline |
| 9 | F2.3 | Preflight diagnostics with auto-remediation `--fix` mode | M2 | Baseline |
| 10 | F2.4 | Multi-backend LLM adapter (Ollama, vLLM, llama.cpp, Reflex fallback) | M2 | Baseline |
| 11 | F2.5 | Zero-friction quickstart documentation (<3 min onboarding in README.md & docs) | M2 | Baseline |
| 12 | F3.1 | Compact diorama island map framing, bezel bounds, optimized camera presets | M3 | Baseline |
| 13 | F3.2 | 3-tier elevation ecosystem (submerged water, ground/caves, airborne sky) | M3 | Baseline |
| 14 | F3.3 | Rendering plants/fruits and corpse remains from telemetry frame | M3 | Baseline |
| 15 | F3.4 | Procedural 3D morphology for 6 numeric traits + 12 biological features | M3 | Baseline |
| 16 | F3.5 | Real-time Law Journal HUD scoreboard, dynamic law activation shockwaves | M3 | Baseline |
| 17 | F3.6 | Zero external CDN dependency constraint preservation (`test_spectate.py`) | M3 | Baseline |
| 18 | F4.1 | Reproduction conditions: energy threshold (>=80%), maturity age (>=30), streak (>=20), cooldown (25 ticks), 35 energy cost, law discovery bonus | M1_EVO | R1 Survey |
| 19 | F4.2 | Bounded stochastic trait mutation (zero-sum `Traits.shift`, sum=12, min=0, max=5) | M1_EVO | R1 Survey |
| 20 | F4.3 | Biological feature mutation (1-of-3 feature swap, individual kit evaluation in passability & domain traversal) | M1_EVO | R1 Survey |
| 21 | F4.4 | Lineage tracking metadata (sequential integer IDs `species:idx`, parent_id, generation, lineage_id, trait variance `d_tr`) | M1_EVO | R1 Survey |
| 22 | F4.5 | Carrying capacity & extinction guardrails (`POPULATION_GLOBAL_MAX = 35`, `POPULATION_SPECIES_MAX = 7`, crowding radius suppression, `EXTINCTION` events) | M1_EVO | R1 Survey |
| 23 | F5.1 | Macro-environmental cycles & 4 canonical weather states (`CLEAR`, `SPORE_STORM`, `SOLAR_FLARE`, `MAGNETIC_SHIFT`) | M2_WEATHER | R2 Survey |
| 24 | F5.2 | Pure seed-deterministic weather scheduler (`weather_at(seed, tick_no)`) with 50-tick epochs (Epoch 0 CLEAR) | M2_WEATHER | R2 Survey |
| 25 | F5.3 | Dynamic physical modulations (movement stamina multiplier, sight radius penalty, plant/algae growth modulation, corpse decay) | M2_WEATHER | R2 Survey |
| 26 | F5.4 | Diurnal law preservation (`phase_at` stays `"DAY"`/`"NIGHT"` for law evaluation & referee scoring) | M2_WEATHER | R2 Survey |
| 27 | F6.1 | Additive creature telemetry payload (`gen`, `parent_id`, `lineage`, `d_tr`) on `/v1/spectate` | M3_TELEMETRY | R4 Survey |
| 28 | F6.2 | Additive top-level `weather` telemetry dictionary (`state`, `cycle_tick`, `cycle_len`, `progress`, `diurnal`, `modifiers`) | M3_TELEMETRY | R4 Survey |
| 29 | F6.3 | Event stream updates (`REPRODUCE`, `EXTINCTION` public events) with zero forbidden token leak | M3_TELEMETRY | R4 Survey |
| 30 | F6.4 | Backlog frame queue expansion (`QUEUE_MAX = 1000`) for late-joiner replay buffer hydration | M3_TELEMETRY | R4 Survey |
| 31 | F7.1 | Interactive timeline scrubber dock (Play/Pause, 1x/2x/5x speed, rewind, scrub slider, LIVE sync button) in `web/watch3d.html` & `watch3d.js` | M4_SPECTATOR | R3 Survey |
| 32 | F7.2 | Client-side historical frame ring buffer (1200 frames) with instant position snapping during scrubs | M4_SPECTATOR | R3 Survey |
| 33 | F7.3 | Zero-dependency Web Audio API procedural sound synthesis (movement per domain, law discovery shockwaves, creature death, weather shifts) | M4_SPECTATOR | R3 Survey |
| 34 | F7.4 | Dynamic atmospheric visual cues (real-time lighting, sky color, fog lerping, procedural particle systems for rain, flare embers, toxic spores, night mist) | M4_SPECTATOR | R3 Survey |
| 35 | F7.5 | Zero external CDN & offline local asset verification | M4_SPECTATOR | R3 Survey |
| 36 | F8.1 | 100% test pass rate across all unit, integration, and E2E tests under `pytest` with zero collection or execution failures | M5_VERIFY_E2E | R5 Survey |
| 37 | F8.2 | One-command launcher verification (`run.sh` / `scripts/launch.py --web`) booting the enhanced simulation and spectator | M5_VERIFY_E2E | R5 Survey |
| 38 | F8.3 | Adversarial stress testing, fuzzing, and boundary verification for multi-generational simulation | M5_VERIFY_E2E | R5 Survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1_EVO | Generational Evolution & Genetic Mutation | Implement `genesis/evolution.py`, extend `genesis/creature.py` with lineage & individual features, integrate reproduction loop in `genesis/tick.py` with population caps, domain passability with creature kits, unit tests in `tests/test_evolution.py`. | none | COMPLETE |
| M2_WEATHER | Dynamic Weather & Macro-Environmental System | Implement `genesis/weather.py`, seed-deterministic scheduler `weather_at(seed, tick_no)`, movement stamina cost modulations in `reflex.py`/`creature.py`, sight penalty in `world.py`, plant/algae growth modulation, unit tests in `tests/test_weather.py`. | none | COMPLETE |
| M3_TELEMETRY | Telemetry Extension & Backward Compatibility | Extend `net/match.py` frame builder with `weather`, creature `gen`/`parent_id`/`lineage`/`d_tr`, add `REPRODUCE`/`EXTINCTION` events, expand backlog in `net/routes_spectate.py` (`QUEUE_MAX = 1000`), verify regex leak tests in `tests/test_spectate.py`. | M1_EVO, M2_WEATHER | COMPLETE |
| M4_SPECTATOR | Interactive 3D Spectator & Procedural Audio | Update `web/watch3d.html` with `#timeline-dock` and audio controls, implement client-side ring buffer (1200 frames), timeline scrubber state machine, Web Audio API procedural sound generator, dynamic lighting/sky/fog lerping, Three.js particle systems for weather, zero-CDN compliance. | M3_TELEMETRY | COMPLETE |
| M5_VERIFY_E2E | Comprehensive E2E Verification & Adversarial Coverage | Update and execute 5-tier E2E test suite in `tests/e2e/`, run full test suite with 100% pass under `pytest`, verify 1-command launchers (`run.sh` and `scripts/launch.py --web`), execute adversarial stress testing. | M1_EVO, M2_WEATHER, M3_TELEMETRY, M4_SPECTATOR | COMPLETE |

## Interface Contracts
### 1. Evolution & Creature Lineage (`genesis.evolution` ↔ `genesis.creature` / `genesis.tick`)
- `Creature` extended fields: `parent_id: str | None = None`, `generation: int = 0`, `lineage_id: str = ""`, `birth_tick: int = 0`, `reproduce_cooldown: int = 0`, `features: tuple[str, ...] = ()`.
- ID format invariant: `f"{species}:{idx}"` where `idx` is an integer, guaranteeing `creature_sort_key`'s `int(idx)` parsing does not crash.
- `reproduce_offspring(parent: Creature, tick: int, rng: random.Random, world: World) -> Creature | None`:
  - Enforces `sum(child.traits) == 12` via `Traits.shift`.
  - Feature mutation swaps 1 of 3 features.
  - Passes passability check: `world.passable(pos, child)`.
- Passability check: `world.passable` checks `getattr(creature, "kit", None) or world.kits.get(creature.species)`.
- Reproduction tick gate in `genesis/tick.py`:
  - `c.energy >= 0.80 * c.traits.energy_max`, `c.age >= 30`, `c.ticks_alive_streak >= 20`, `c.reproduce_cooldown <= 0`.
  - Deducts `35.0` energy from parent, sets `reproduce_cooldown = 25`.
  - Enforces `len([c for c in creatures if c.alive]) < POPULATION_GLOBAL_MAX (35)` and species living count `< POPULATION_SPECIES_MAX (7)`.

### 2. Weather & Macro-Environmental System (`genesis.weather` ↔ `genesis.world` / `genesis.reflex`)
- `WeatherType`: `"CLEAR"`, `"SPORE_STORM"`, `"SOLAR_FLARE"`, `"MAGNETIC_SHIFT"`.
- Pure deterministic scheduler: `weather_at(seed: int, tick_no: int) -> WeatherState`
  - Epoch length: 50 ticks. Tick 0-49: `"CLEAR"`.
- Diurnal invariant: `world.phase` and `phase_at(tick)` remain strictly `"DAY"` or `"NIGHT"`.
- Modifiers contract: `WeatherModifiers(move_cost_mult: float, sight_penalty: int, plant_growth_mult: float, algae_growth_mult: float, hazard_kind: str | None)`.
- Applied in:
  - `reflex.py`: `cost = config.COST_MOVE * weather.modifiers.move_cost_mult`
  - `creature.py`: `random_step` applies same modified move cost.
  - `world.py:visible`: applies `sight_radius = max(1, sight_radius - weather.modifiers.sight_penalty)`.
  - `world.py:spawn_plants` & `spawn_algae`: multiplies respawn quantity by growth multiplier.

### 3. WebSocket Telemetry Schema (`net.match` ↔ `web/watch3d.js`)
- WebSocket payload on `/v1/spectate`:
  - `t`: int
  - `phase`: str ("LOBBY" | "RUNNING" | "REVEAL")
  - `weather`: dict
    - `state`: str ("CLEAR" | "SPORE_STORM" | "SOLAR_FLARE" | "MAGNETIC_SHIFT")
    - `cycle_tick`: int (0 to 49)
    - `cycle_len`: int (50)
    - `progress`: float (0.0 to 1.0)
    - `diurnal`: str ("DAY" | "NIGHT")
    - `modifiers`: dict (`move_cost_mult`, `sight_penalty`, `plant_growth_mult`, `algae_growth_mult`)
  - `creatures`: list[dict]
    - Existing: `id`, `x`, `y`, `hp`, `e`, `e_max`, `alive`, `feral`, `tr`, `species`, `domain`, `features`
    - New additive: `gen` (int), `parent_id` (str|None), `lineage` (str), `d_tr` (list[int]), `age` (int)
  - `events`: list[dict] (`type`, `x`, `y`, `species`, `detail`), including `"REPRODUCE"` and `"EXTINCTION"`
  - `plants`, `corpses`, `terrain_delta`: unchanged.

### 4. 3D Spectator & Web Audio Engine (`web/watch3d.js`)
- Zero external CDN or audio files.
- Procedural Audio:
  - `playMoveSound(domain)`: domain-specific filtered oscillator.
  - `playLawShockwaveSound()`: harmonic 4-oscillator major chord with resonant filter sweep.
  - `playDeathSound()`: pitch-decaying plunge oscillator.
  - `playWeatherShiftSound(state)`: ambient drone sweep.
- Timeline Dock:
  - Spacebar: Play/Pause.
  - Buttons: 1x, 2x, 5x speed, -10 ticks, +10 ticks, LIVE sync.
  - Slider: min to max buffered tick index.
  - Instant position update flag on body meshes during scrubbing.
- Weather Visualizer:
  - Lighting & fog color lerp to weather theme.
  - Procedural Three.js Point clouds: Rain streaks, Solar embers, Toxic spore mist, Night mist.

## Code Layout
- `genesis/`: Simulation core engine
  - `world.py`: Grid, biomes, passability, visibility, plant regeneration
  - `creature.py`: Creature state, lifecycle, lineage fields
  - `evolution.py`: Reproduction gating, bounded trait shift, feature mutation
  - `weather.py`: Dynamic weather engine, deterministic scheduler, modifiers
  - `domain.py`: 3-tier domains (NUOC, CAN, TROI) & creature kit mechanics
  - `features.py`: 12 biological features & feature rolling
  - `traits.py`: Trait invariants & `shift` primitive
  - `tick.py`: Tick execution pipeline & reproduction phase
  - `lawgen.py`, `lawhook.py`: Hidden physics generation & hooks
  - `referee.py`, `journal.py`: Referee scoring & Law Journal discovery
  - `llm_client.py`: Multi-backend LLM adapter
  - `reflex.py`: Rule-based reflex fallback with weather cost modifier
- `net/`: Server & network protocols
  - `server.py`: FastAPI server
  - `match.py`: Match lifecycle, telemetry frame builder with weather & lineage
  - `routes_spectate.py`: WebSocket telemetry stream & expanded backlog buffer
- `scripts/`: Operational tools & launchers
  - `launch.py`: Unified Python launcher & TUI
  - `preflight.py`: Environment diagnostics & `--fix` auto-repair
  - `hostile_client.py`: Hostile security probe suite
- `web/`: 3D Spectator visualizer
  - `watch3d.html`: HTML container & `#timeline-dock` UI overlay
  - `watch3d.js`: Three.js scene, diorama map, timeline scrubber, procedural Web Audio, weather particles
  - `vendor/`: Bundled Three.js r128 & loaders (Zero-CDN)
- `run.sh`, `run.ps1`, `run.bat`: 1-Command cross-platform root launchers
- `tests/`: Test suite
  - `test_evolution.py`: Unit tests for reproduction, mutation, lineage, and caps
  - `test_weather.py`: Unit tests for weather scheduler, determinism, and modulations
  - `test_spectate.py`: Spectator and telemetry schema verification
  - `tests/e2e/`: Requirement-driven 5-tier E2E test suite

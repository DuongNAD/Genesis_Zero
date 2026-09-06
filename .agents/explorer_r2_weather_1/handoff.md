# Handoff Report: Dynamic Environmental System & Weather Phenomena (R2)

**Agent**: Explorer 2 (Dynamic Weather & Environment Specialist)  
**Date**: 2026-09-03  
**Handoff Type**: Hard (Task Complete)  
**Workspace Path**: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1`

---

## 1. Observation

1. **Diurnal Phase Mechanics**:
   - `genesis/world.py:459-463`:
     ```python
     def phase_at(tick: int) -> str:
         """Trả 'DAY' hoặc 'NIGHT' theo chu kỳ law_config.PHASE_LEN."""
         phase_idx = (tick // law_config.PHASE_LEN) % 2
         return "DAY" if phase_idx == 0 else "NIGHT"
     ```
   - `genesis/law_config.py:4`: `PHASE_LEN = 40` ticks.
   - `tests/test_surface.py:47-53`: Directly asserts `phase_at(0) == "DAY"`, `phase_at(39) == "DAY"`, `phase_at(40) == "NIGHT"`, `phase_at(79) == "NIGHT"`.
   - `genesis/situations.py:21`: `_PHASES = ("DAY", "NIGHT")`.
   - `genesis/validate.py:70-71`: `ARG_DOMAIN["PHASE"] = ("DAY", "NIGHT")`, `ARG_DOMAIN["PHASE_ENTER"] = ("DAY", "NIGHT")`.
2. **Passability Architecture**:
   - `genesis/world.py:273-296`: `passable(pos, creature=None)` wraps coordinates and delegates exclusively to `genesis/domain.py:can_enter(domain_of(creature.species), terrain, creature.traits, world.kits.get(creature.species))`.
   - `genesis/domain.py:61-68`: `_BASE` gives unconditioned passability per domain (`NUOC`: `WATER`, `DEEP`; `CAN`: `PLAIN`, `BUSH`, `WATER`; `TROI`: all terrain).
   - `genesis/domain.py:71-74`: `_GATED` gates `TREE` behind `speed >= CLIMB_SPEED` and `FIRE` behind `armor >= FIRE_ARMOR`.
3. **Movement & Energy Costs**:
   - `genesis/reflex.py:302`: `c.energy -= config.COST_MOVE` (flat `0.5` per step in `apply_intent`).
   - `genesis/creature.py:107`: `c.energy -= config.COST_MOVE` in `random_step`.
   - `genesis/creature.py:125`: `c.energy -= c.traits.upkeep * kit.upkeep_mult` in `upkeep_and_check_death`.
4. **Plant & Algae Regeneration**:
   - `genesis/world.py:395-397`: `n = min(max(1, round(config.PLANT_RESPAWN * scale)), room, len(candidates))` in `spawn_plants`.
   - `genesis/world.py:367`: `n = min(config.ALGAE_RESPAWN, room, len(candidates))` in `spawn_algae`.
   - `genesis/world.py:404-411`: `decay_corpses` removes corpses older than `config.CORPSE_DECAY` (15 ticks).
5. **Sensory & Visibility Mechanics**:
   - `genesis/world.py:425-429`:
     ```python
     sight_radius = obs.traits.sight_radius
     if world.phase == "NIGHT":
         kit = world.kits.get(obs.species)
         if not (kit is not None and getattr(kit, "night_sight", False)):
             sight_radius = max(1, sight_radius - config.NIGHT_SIGHT_PENALTY)
     ```
   - `genesis/speech.py:9-14`: Full speech heard within `sight_radius` of listener; acoustic `signal` heard within `2 * sight_radius`.
6. **Spectator Frame & Law Leak Restrictions**:
   - `net/match.py:564-592`: `frame(tick_no, events)` returns top-level keys `t`, `phase`, `w`, `h`, `creatures`, `plants`, `corpses`, `terrain_delta`, `map`, `terrain`, `events`.
   - `tests/test_spectate.py:24`: `FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")`.
   - `tests/test_spectate.py:53`: Enforces `assert not m, f"Khung rò rỉ token cấm {m.group(0)!r}: {text}"` on serialized JSON of frames in `RUNNING` phase.
   - `tests/test_spectate.py:102`: `assert frame["phase"] == "RUNNING"`.
7. **Referee Isolation & Test State**:
   - `genesis/score.py:6-9` and `tests/test_score.py:70-80`: AST validation verifies `score.py` does not import `world`, `tick`, `creature`, `strategist`, `run`, or `lawhook`.
   - Baseline test execution: `pytest` passed 100% across all test suites (including 208 E2E tests).

---

## 2. Logic Chain

1. **Preservation of Diurnal Laws (Step 1 -> Rule 1)**:
   Because `phase_at(tick)` is tied to `TriggerKind.PHASE_ENTER`, `CondKind.PHASE`, `situations.py`, and `test_surface.py` (Observation 1), altering `phase_at` or `world.phase` to return weather strings like `"SOLAR_FLARE"` will break hidden law truth tables, referee verification, and unit tests.
   *Inference*: The simulation must maintain `phase_at(tick)` as `"DAY"`/`"NIGHT"`, and implement dynamic weather as a separate `WeatherEngine` that operates alongside diurnal illumination.

2. **Seed-Deterministic Scheduling (Step 2 -> Rule 2)**:
   Simulation determinism relies on isolated RNG streams (Observation 7). Consuming numbers from `world.rng` for weather changes will alter the RNG sequence for `spawn_plants` and entity movement, causing desynchronization across identical seeds.
   *Inference*: Weather epoch sequences must be derived either via pure arithmetic modulo logic or through a dedicated RNG stream seeded with `hashlib.md5(f"weather:{seed}")`. A pure function `weather_at(seed, tick)` enables instant, zero-drift scrubbing in the interactive timeline visualizer (R3).

3. **Safe Simulation Modulations (Step 3 -> Rule 3)**:
   Land creatures require `PLAIN` to forage and water creatures require `WATER`/`DEEP` to survive (Observations 2, 4). If weather completely closes off these biomes, organisms die of starvation within 20 ticks.
   *Inference*: Modulations should alter movement stamina costs (`COST_MOVE * move_cost_mult`), plant/algae growth rates (`plant_growth_mult`, `algae_growth_mult`), and sight radius (`sight_penalty`), while keeping terrain passability changes non-catastrophic (e.g. shallow water freezes but deep water remains open).

4. **Spectator Schema Extension & Security (Step 4 -> Rule 4)**:
   `test_spectate.py` asserts `frame["phase"] == "RUNNING"` and scans all frame text against `FORBIDDEN_RUNNING_PATTERN` (Observation 6).
   *Inference*:
   - Weather must be placed in a dedicated dictionary `frame["weather"]` rather than replacing `frame["phase"]`.
   - Weather telemetry must strictly avoid the substrings `POISON`, `DAMAGE`, `HEAL`, `SPREAD`, `FRUIT_[A-D]`, and `law_id`. Using identifiers `{"CLEAR", "SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT"}` with modifier keys `{"move_cost_mult", "sight_penalty", "plant_growth_mult", "algae_growth_mult", "hazard"}` guarantees zero regex collisions.

---

## 3. Caveats

- **Network Mode**: Investigation was performed in local read-only mode without mutating application source code.
- **Micro-Climate / Localized Cells**: This design specifies macro-environmental cycles affecting the entire grid or specific biomes globally. Localized micro-climate cells (e.g., cellular automata moving clouds) were evaluated but deprioritized as they introduce high bandwidth overhead on `/v1/spectate` (sending per-cell weather grids) compared to global macro-phases.
- **LLM Prompt Integration**: Weather description in `genesis/prompt.py` can optionally describe the weather to LLM agents (e.g. "trời đang bão bào tử"), but should only use descriptive Vietnamese text without leaking DSL keywords.

---

## 4. Conclusion

1. Implement `genesis/weather.py` with `WeatherType` (`CLEAR`, `SPORE_STORM`, `SOLAR_FLARE`, `MAGNETIC_SHIFT`), `WeatherModifiers`, and `WeatherEngine`.
2. Seed-deterministic scheduling should use 50-tick epochs with Epoch 0 guaranteed as `CLEAR` for exploration onboarding.
3. Modulations apply cleanly to:
   - Movement costs in `genesis/reflex.py:apply_intent` and `genesis/creature.py:random_step`.
   - Sight radius in `genesis/world.py:visible`.
   - Plant & algae respawn rates in `genesis/world.py:spawn_plants` and `spawn_algae`.
   - Corpse decay in `genesis/world.py:decay_corpses`.
4. WebSocket `/v1/spectate` telemetry is extended with a new top-level `weather` dictionary containing `state`, `cycle_tick`, `cycle_len`, `progress`, `diurnal`, and `modifiers`.
5. 100% backward compatibility is guaranteed for referee scoring and existing spectator clients.

---

## 5. Verification Method

### Test Commands
Execute the full test suite and spec-specific verification tests:
```bash
# 1. Run all existing tests to verify baseline zero regression:
pytest -q

# 2. Run E2E requirement-driven tests:
pytest -o pythonpath=. tests/e2e -v

# 3. Run spectator and no-law-leak tests:
pytest tests/test_spectate.py tests/test_no_law_leak.py -v

# 4. Run referee scoring tests:
pytest tests/test_score.py tests/test_gates.py -v
```

### Invalidation Conditions
- Any test in `test_spectate.py` fails due to regex token matching in `frame` (e.g. if the word `POISON` is present).
- Any test in `test_score.py` fails or detects simulation imports.
- Any test in `test_surface.py` fails because `phase_at()` returns anything other than `"DAY"` or `"NIGHT"`.
- Total test pass count drops below 100%.

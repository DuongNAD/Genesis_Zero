# Implementation Task: Milestone M2_WEATHER (Dynamic Environmental System & Weather Phenomena)

## Mandatory References
- Authoritative User Request: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md` (read section `## 2026-09-03T04:57:00Z`)
- Global Architecture & Interface Contracts: `/Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md` (specifically § Milestones and § Interface Contracts § 2)
- E2E Test Suite Status: `/Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md`
- Weather Exploration Survey: `/Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1/handoff.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Requirements & Implementation Plan
1. **Module `genesis/weather.py`**:
   - Define `WeatherType` enum or string literals: `"CLEAR"`, `"RAIN"`, `"SPORE_STORM"`, `"SOLAR_FLARE"`, `"MAGNETIC_SHIFT"`.
   - Define `WeatherModifiers` dataclass:
     - `move_cost_mult: float` (CLEAR: 1.0, RAIN: 1.3, SPORE_STORM: 1.5, SOLAR_FLARE: 1.4, MAGNETIC_SHIFT: 1.2)
     - `sight_penalty: int` (CLEAR: 0, RAIN: 1, SPORE_STORM: 2, SOLAR_FLARE: 1, MAGNETIC_SHIFT: 0)
     - `plant_mult: float` (CLEAR: 1.0, RAIN: 1.5, SPORE_STORM: 0.5, SOLAR_FLARE: 0.7, MAGNETIC_SHIFT: 1.0)
     - `algae_mult: float` (CLEAR: 1.0, RAIN: 1.4, SPORE_STORM: 0.8, SOLAR_FLARE: 0.5, MAGNETIC_SHIFT: 1.1)
   - Define `WeatherState` dataclass:
     - `name: str`
     - `tick_in_cycle: int`
     - `cycle_len: int` (default 50 ticks)
     - `progress: float` (0.0 to 1.0)
     - `modifiers: WeatherModifiers`
   - Implement deterministic scheduler: `weather_at(seed: int, tick: int) -> WeatherState`:
     - Must be completely deterministic from `(seed, tick)` without consuming from `world.rng` (use pure math or a dedicated hash-seeded PRNG stream).
     - Epoch 0 (ticks 0-49) must always be `"CLEAR"` for clean onboarding.
     - Subsequent epochs cycle or select pseudo-randomly deterministically.
   - Provide helper `to_dict(weather_state: WeatherState) -> dict` for telemetry.

2. **Integration into Simulation**:
   - `genesis/world.py`:
     - Store current `weather: WeatherState` on `World` (initialized via `weather_at(seed, 0)`).
     - In `World.visible(obs)`: apply `weather.modifiers.sight_penalty` to effective sight radius:
       `sight_radius = max(1, sight_radius - getattr(getattr(self, 'weather', None), 'modifiers', None).sight_penalty if hasattr(self, 'weather') and self.weather else sight_radius)` (ensure backwards compatible if `weather` is None).
     - In `World.spawn_plants` and `World.spawn_algae`: scale candidate spawn counts by `weather.modifiers.plant_mult` and `weather.modifiers.algae_mult`.
   - `genesis/reflex.py:apply_intent`:
     - In movement intent handling: multiply `config.COST_MOVE` by `weather.modifiers.move_cost_mult` when moving.
   - `genesis/creature.py:random_step`:
     - Multiply `config.COST_MOVE` by `weather.modifiers.move_cost_mult` when moving.
   - `genesis/tick.py`:
     - At start of `tick()`, update `world.weather = weather_at(state.match_seed, tick_no)`.

3. **Telemetry & Security Invariants**:
   - In `net/match.py:frame()`:
     - Add `"weather": world.weather.to_dict()` if `world.weather` is present.
     - CRITICAL: Ensure NO forbidden tokens (`POISON`, `DAMAGE`, `HEAL`, `SPREAD`, `FRUIT_[A-D]`, `law_id`) appear anywhere in the weather telemetry payload! Use only safe names: `"CLEAR"`, `"RAIN"`, `"SPORE_STORM"`, `"SOLAR_FLARE"`, `"MAGNETIC_SHIFT"`.
   - In `genesis/world.py`:
     - `phase_at(tick)` MUST REMAIN UNTOUCHED returning `"DAY"` or `"NIGHT"`. Do NOT replace diurnal phases with weather names!

4. **Testing in `tests/test_weather.py`**:
   - Test seed-determinism: identical `(seed, tick)` yields identical `WeatherState`.
   - Test Epoch 0 is CLEAR.
   - Test cycle transitions every 50 ticks.
   - Test movement cost modulation (stamina deducted reflects weather modifier).
   - Test sight radius reduction under spore storm and solar flare.
   - Test plant and algae growth rate scaling.
   - Test serialization and no forbidden token leaks.

5. **Verification**:
   - Run `pytest tests/test_weather.py -v`.
   - Run `pytest tests/test_spectate.py tests/test_no_law_leak.py -v` (confirm zero regex leaks).
   - Run `pytest tests/test_surface.py tests/test_score.py -v` (confirm zero regression on diurnal laws and referee scoring).
   - Run full repository pytest: `pytest -q` (confirm 100% pass rate).
   - Run `ruff check genesis/weather.py genesis/tick.py genesis/world.py genesis/reflex.py genesis/creature.py net/match.py tests/test_weather.py`.

Write your comprehensive handoff report to `handoff.md` in your working directory and notify parent via `send_message`.

## 2026-09-03T07:29:08Z
You are Worker M2_WEATHER (Dynamic Environmental System & Weather Specialist).
Your working directory is: /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1
Read your dispatch assignment in /Users/duongnad/Documents/project/Genesis_Zero/.agents/worker_m2_weather_1/DISPATCH.md.
Also read:
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/ORIGINAL_REQUEST.md (specifically section ## 2026-09-03T04:57:00Z)
- /Users/duongnad/Documents/project/Genesis_Zero/PROJECT.md
- /Users/duongnad/Documents/project/Genesis_Zero/TEST_READY.md
- /Users/duongnad/Documents/project/Genesis_Zero/.agents/explorer_r2_weather_1/handoff.md

Implement the dynamic weather system in `genesis/weather.py`, integrate into simulation in `genesis/world.py`, `genesis/tick.py`, `genesis/reflex.py`, and `genesis/creature.py`, add telemetry in `net/match.py`, and write comprehensive unit tests in `tests/test_weather.py`.
Verify that `pytest tests/test_weather.py -v`, `pytest tests/test_spectate.py -v`, and full `pytest -q` pass with 100% success.
Write your handoff report to `handoff.md` in your working directory and notify parent via send_message when done.

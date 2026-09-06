# Architectural & Technical Survey: Dynamic Environmental System & Weather Phenomena (R2 & Weather Telemetry)

**Agent**: Explorer 2 (Dynamic Weather & Environment Specialist)  
**Date**: 2026-09-03  
**Status**: Comprehensive Investigation Complete  
**Scope**: Simulation World Engine (`genesis/`), Networking & Telemetry (`net/`), Law Verification & Referee Scoring (`genesis/score.py`, `genesis/verify.py`), Spectator Visualizer Contracts (`web/watch3d.js`).

---

## Executive Summary

Genesis Zero currently models the environment in a minimal, single-variable diurnal loop: `world.phase` alternates strictly between `"DAY"` and `"NIGHT"` every 40 ticks (`law_config.PHASE_LEN = 40`), and `world.wind` is picked once from `["N", "E", "S", "W"]` at match creation. While this satisfies the basic requirement for the hidden physics law `TriggerKind.PHASE_ENTER` and `CondKind.PHASE`, the simulation lacks dynamic macro-environmental pressure, terrain flux, or atmospheric variation.

Requirement **R2** (Dynamic Environmental System & Weather Phenomena) calls for periodic macro-environmental cycles—such as day/night illumination cycles, toxic spore storms, solar flares, and magnetic shifts—that dynamically modulate terrain passability, resource depletion/growth rates, creature stamina costs, and sensory ranges across the grid in a seed-deterministic manner, broadcasting live environmental telemetry over WebSocket `/v1/spectate`.

This investigation formulates the complete architectural and technical design for R2 while strictly enforcing:
1. **100% Backward Compatibility**: Keeping the hidden law system (`laweval.py`, `situations.py`, `verify.py`, `score.py`) and existing diurnal tests completely unbroken.
2. **Zero Law-Leak Regex Collisions**: Complying with `tests/test_spectate.py`'s forbidden token guard (`FORBIDDEN_RUNNING_PATTERN`).
3. **Seed Determinism & Replay Fidelity**: Ensuring zero RNG pollution of simulation entities and zero-drift timeline scrubbing in the interactive 3D spectator (R3).

---

## 1. Macro-Environmental Cycles & Phases

### 1.1 Architectural Decoupling: Diurnal Law Phase vs. Weather Engine

An essential architectural insight discovered during our codebase inspection is that `world.phase` (`"DAY"` / `"NIGHT"`) is deeply coupled with the hidden law system:
- `genesis/lawdsl.py`: `TriggerKind.PHASE_ENTER` takes `arg in ("DAY", "NIGHT")`, `CondKind.PHASE` takes `arg in ("DAY", "NIGHT")`.
- `genesis/validate.py`: `ARG_DOMAIN["PHASE"] = ("DAY", "NIGHT")`, `ARG_DOMAIN["PHASE_ENTER"] = ("DAY", "NIGHT")`.
- `genesis/situations.py`: Generates truth-table situations using `_PHASES = ("DAY", "NIGHT")`.
- `genesis/verify.py` & `genesis/score.py`: Score matching relies on AST truth-table evaluation over these situations.
- `tests/test_surface.py`: Explicitly asserts `assert phase_at(0) == "DAY"` and `assert phase_at(40) == "NIGHT"`.

**Architectural Rule**: `phase_at(tick)` and the diurnal illumination cycle must continue to return `"DAY"` and `"NIGHT"`. The new dynamic environmental phenomena must be introduced via a dedicated **Weather Engine** (`genesis/weather.py`), which coordinates with diurnal illumination while governing macro-environmental states.

### 1.2 Four Macro-Environmental Phenomena

We define four canonical macro-environmental weather states:

| Weather State | Identifier | Atmospheric Narrative | Diurnal Behavior | Primary Gameplay Impact |
|---|---|---|---|---|
| **Calm / Clear** | `CLEAR` | Standard temperate climate with clear skies and mild breezes. | Normal `DAY` / `NIGHT` transition. | Baseline simulation conditions; optimal foraging and observation. |
| **Toxic Spore Storm** | `SPORE_STORM` | Dense fungal spore haze clouds the atmosphere with airborne particulates. | Dim daylight; pitch-black night with bio-luminescent fog. | Reduced sight radius; increased movement cost on plains/bushes; plant withering but algae blooms. |
| **Solar Flare** | `SOLAR_FLARE` | High-energy coronal mass ejection bombards the grid with heat and radiation. | Blinding golden daylight; vibrant auroral radiation at night. | Elevated stamina/movement costs; rapid corpse decay; accelerated photosynthesis/plant regeneration. |
| **Magnetic Shift** | `MAGNETIC_SHIFT` | Planetary geomagnetic polarity fluctuation induces electromagnetic static. | Shifting atmospheric violet/cyan auroral curtains. | Scrambled hearing and directional sensing; charged rock passability resistance; fluctuating wind vectors. |

---

## 2. Seed-Deterministic Phase Transitions & Duration Tracking

### 2.1 Determinism Architecture: Zero RNG Pollution

The simulation engine maintains absolute determinism across all entities using isolated RNG streams:
- World generation: `rng = random.Random(seed)` (`genesis/tick.py:84`).
- Surface permutation: `s_rng = random.Random(hash("surface:{seed}"))` (`genesis/tick.py:90`).
- Creature actions: `creature_rng(match_seed, tick_no, creature_id)` (`genesis/tick.py:67`).

If weather transitions consume random numbers from `world.rng` during the match loop, plant spawning (`spawn_plants(world, rng, tick)`) and terrain erosion will immediately desynchronize!

**Design**: The Weather Engine schedule must be derived using an independent deterministic generator:
```python
def weather_schedule(seed: int, ticks_total: int = 200, cycle_len: int = 50) -> list[WeatherState]:
    """Generates the deterministic sequence of weather epochs for a match."""
    w_rng = random.Random(int(hashlib.md5(f"weather:{seed}".encode()).hexdigest()[:16], 16))
    ...
```

### 2.2 Pure Function vs. Stateful Progression

To support the interactive 3D spectator's scrubbing and rewind features (R3), the weather at any tick `t` can be evaluated as a pure function:

$$\text{epoch\_idx} = \lfloor t / \text{cycle\_len} \rfloor$$
$$\text{cycle\_tick} = t \pmod{\text{cycle\_len}}$$
$$\text{progress} = \frac{\text{cycle\_tick}}{\text{cycle\_len}}$$

For a standard 200-tick match (`net_config.OPEN_MATCH_TICKS = 200`) with `cycle_len = 50`:
- **Epoch 0 (ticks 0–49)**: Always `CLEAR` (baseline orientation, law discovery setup).
- **Epoch 1 (ticks 50–99)**: Phenomenon A (e.g. `SPORE_STORM`).
- **Epoch 2 (ticks 100–149)**: Phenomenon B (e.g. `SOLAR_FLARE`).
- **Epoch 3 (ticks 150–199)**: Phenomenon C (e.g. `MAGNETIC_SHIFT`).

Because `weather_at(seed, tick)` is pure and arithmetic:
1. Replays can jump to any arbitrary tick instantaneously without re-simulating intermediate ticks.
2. Spectator clients can smoothly interpolate lighting, particle density, and fog transitions using `progress` (0.0 to 1.0).

---

## 3. Mechanics for Dynamic Simulation Modulations

### 3.1 Modulations Overview

```
                          +-------------------------+
                          |   Active Weather State  |
                          +------------+------------+
                                       |
         +-----------------+-----------+-----------+-----------------+
         |                 |                       |                 |
         v                 v                       v                 v
+-----------------+ +---------------+     +-----------------+ +---------------+
| Passability &   | | Resource      |     | Stamina &       | | Sensory &     |
| Terrain Gating  | | Growth/Decay  |     | Movement Costs  | | Visibility    |
+-----------------+ +---------------+     +-----------------+ +---------------+
| - Shallow water | | - Plant rate  |     | - Move cost mult| | - Sight radius|
|   freezing      | | - Algae bloom |     | - Upkeep mult   | | - Hearing dist|
| - Bush friction | | - Corpse decay|     | - Heat drain    | | - Static blur |
+-----------------+ +---------------+     +-----------------+ +---------------+
```

### 3.2 Detailed Mechanics by Subsystem

#### A. Terrain Passability Modulations (`genesis/world.py` & `genesis/domain.py`)
- **Current Mechanism**: `world.passable(pos, creature)` calls `can_enter(domain, terrain, traits, kit)`. Land (`CAN`) can traverse `PLAIN`, `BUSH`, and shallow `WATER`. Water (`NUOC`) can traverse `WATER` and `DEEP`. Air (`TROI`) can fly over all terrains.
- **Weather Modulations**:
  1. **Storm Turbulence (`SPORE_STORM`)**: Heavy fungal spore density increases air friction over open ground. High-elevation movement for `TROI` requires `speed >= 3` or costs extra energy.
  2. **Frozen Water Shallows (`COLD_SNAP` / Extreme weather variant)**: When shallow `WATER` freezes, land creatures (`CAN`) can walk across it without drowning, while aquatic creatures (`NUOC`) are temporarily barred from frozen shallows and must retreat to `DEEP`.
  3. **Scorched Rock (`SOLAR_FLARE`)**: Thermal radiance on `ROCK` requires `armor >= 2` to traverse without suffering an immediate heat exhaustion energy drain.
- **Safety Invariant**: Crucially, modulations must **never** eliminate all passable cells for any living species (e.g., `DEEP` water must never freeze, and `PLAIN` must never become 100% blocked), preventing unavoidable extinction cascades.

#### B. Resource Depletion & Plant Regeneration (`genesis/world.py`)
- **Current Mechanism**:
  - Plants on `PLAIN`: `spawn_plants(world, rng, tick)` spawns $n = \min(\text{round}(\text{PLANT\_RESPAWN} \times \text{scale}), \text{room}, \text{candidates})$.
  - Algae on `WATER`/`DEEP`: `spawn_algae(world, rng, tick)` spawns $n = \min(\text{ALGAE\_RESPAWN}, \text{room}, \text{candidates})$.
  - Corpses: `decay_corpses(world, tick)` decays after `CORPSE_DECAY = 15` ticks.
- **Weather Modulations**:
  - `SPORE_STORM`: Fungal spores choke standard vegetation (`plant_growth_mult = 0.5`), but induce rampant aquatic nutrient bloom (`algae_growth_mult = 1.8`).
  - `SOLAR_FLARE`: Solar radiation supercharges photosynthesis on `PLAIN` (`plant_growth_mult = 1.6`), but scorches organic remains, accelerating corpse decay (`corpse_decay_ticks = 8`, rot 2x faster).
  - `MAGNETIC_SHIFT`: Stable standard growth (`plant_growth_mult = 1.0`, `algae_growth_mult = 1.0`).

#### C. Stamina & Movement Costs (`genesis/reflex.py` & `genesis/creature.py`)
- **Current Mechanism**:
  - `apply_intent()`: `c.energy -= config.COST_MOVE` (flat `0.5` per step).
  - `random_step()`: `c.energy -= config.COST_MOVE`.
  - `upkeep_and_check_death()`: `c.energy -= c.traits.upkeep * kit.upkeep_mult`.
- **Weather Modulations**:
  - `cost_move_effective = config.COST_MOVE * weather.move_cost_mult`.
  - `CLEAR`: `move_cost_mult = 1.0` (0.5 energy/step).
  - `SPORE_STORM`: `move_cost_mult = 1.4` (0.7 energy/step through thick spore clouds).
  - `SOLAR_FLARE`: `move_cost_mult = 1.5` (0.75 energy/step due to thermal exhaustion). Base metabolic upkeep multiplied by `1.2x`.
  - `MAGNETIC_SHIFT`: `move_cost_mult = 1.0`, but crossing `ROCK` or moving against wind polarity imposes a +0.2 stamina penalty.

#### D. Sensory Ranges & Visibility (`genesis/world.py` & `genesis/speech.py`)
- **Current Mechanism**:
  - `visible()`: `sight_radius = obs.traits.sight_radius`. If `world.phase == "NIGHT"` and without `night_sight`, penalized by `NIGHT_SIGHT_PENALTY`.
  - `hearers()`: Full text heard within `sight_radius`; signal heard within `2 * sight_radius`.
- **Weather Modulations**:
  - `SPORE_STORM`: Particulate smog enforces a `-1` sight radius penalty (clamped to `max(1, sight_radius - 1)`). Creatures with `feel_radius` (`RAU_CAM_UNG`) or `sense >= 3` mitigate this penalty.
  - `SOLAR_FLARE`: Glare limits night-vision advantages; speech acoustic transmission is standard.
  - `MAGNETIC_SHIFT`: Geomagnetic static disrupts acoustic/telepathic signals: `hear_signal` range reduced from `2 * sight_radius` to `1.5 * sight_radius`.

---

## 4. WebSocket `/v1/spectate` Schema Extensions

### 4.1 Telemetry Contract & Backward Compatibility

In `net/match.py`, `MatchRunner.frame(tick_no, events)` builds the broadcast dictionary for `/v1/spectate`.

Existing clients (and `tests/test_spectate.py:test_3_spectate_frame_schema`) require the top-level keys:
- `t`: int
- `phase`: str (`"RUNNING"`, `"LOBBY"`, `"REVEAL"`, `"COOLDOWN"`) — **MUST NOT BE OVERWRITTEN**
- `creatures`: list[dict]
- `plants`: list[list[int]]
- `corpses`: list[list[int]]
- `terrain_delta`: list
- `events`: list[dict]

### 4.2 Proposed Schema Extension: `weather` Object

We extend the frame by adding a dedicated `weather` dictionary:

```json
{
  "t": 68,
  "phase": "RUNNING",
  "w": 24,
  "h": 24,
  "creatures": [...],
  "plants": [...],
  "corpses": [...],
  "terrain_delta": [],
  "map": "DONG_CO",
  "terrain": null,
  "events": [...],
  "weather": {
    "state": "SPORE_STORM",
    "cycle_tick": 18,
    "cycle_len": 50,
    "progress": 0.36,
    "diurnal": "DAY",
    "modifiers": {
      "move_cost_mult": 1.4,
      "sight_penalty": 1,
      "plant_growth_mult": 0.5,
      "algae_growth_mult": 1.8,
      "hazard": "SPORES"
    }
  }
}
```

### 4.3 Strict Law-Leak Security Compliance

`tests/test_spectate.py` (line 24) enforces the regex check:
```python
FORBIDDEN_RUNNING_PATTERN = re.compile(r"law_id|POISON|DAMAGE|HEAL|SPREAD|FRUIT_[A-D]")
```
This regex is executed across the serialized JSON string of the entire frame during `RUNNING` phase.

**Security Constraints for Weather Telemetry**:
- Never use the substring `POISON` (e.g. use `"TOXIC_SPORES"` or `"SPORES"` or `"BIO_HAZARD"`, never `"POISON_STORM"` or `"POISON"`).
- Never use `DAMAGE` (use `"move_cost_mult"`, `"exhaustion"`).
- Never use `HEAL` (use `"growth_mult"`).
- Never use `SPREAD` or `FRUIT_A..D`.
- Never use `law_id`.

By selecting token identifiers:
`{"CLEAR", "SPORE_STORM", "SOLAR_FLARE", "MAGNETIC_SHIFT"}` with modifier tags `{"SPORES", "SOLAR", "MAGNETIC", "CALM"}`, the schema is guaranteed to be 100% compliant with zero leak detections.

---

## 5. Backward Compatibility & Referee Scoring Guarantees

### 5.1 Referee Scoring Invariant Protection

In `genesis/score.py` and `genesis/verify.py`:
- Invariant 1: `score.py` never imports `world.py`, `tick.py`, or `creature.py` (strictly enforced by AST test `test_khong_import_sim`).
- `score.py` scores offline by reading JSONL log files.
- In `genesis/logio.py`, `EVENT_KINDS` defines permitted event kinds.
- Adding a `"WEATHER_CHANGE"` event to `EVENT_KINDS` in `logio.py`:
  ```python
  EVENT_KINDS = frozenset({
      ...
      "PHASE_CHANGE",
      "WEATHER_CHANGE",
      ...
  })
  ```
  allows the simulation to log weather shifts without interfering with `score.py`'s scoring logic (which ignores unrecognized event kinds and only tallies `CODEX_OP`, `RUN_START`, `RUN_END`, and specific action markers).

### 5.2 Spectator Client Backward Compatibility

- Existing 2D spectator (`web/watch.html`, `web/watch.js`): Ignores unrecognized keys in `frame`, continuing to draw the grid and creatures seamlessly.
- New 3D spectator (`web/watch3d.js`): Consumes `frame.weather` to dynamically alter:
  1. Directional light and ambient light color/intensity (warm gold for solar flare, sickly green-violet for spore storm, shifting cyan for magnetic shift).
  2. Skybox background tint and fog density.
  3. Particle emitter systems (drifting green spores, solar radiation rays, shimmering magnetic auroras).
  4. Web Audio procedural sound synthesis triggers when `frame.weather.progress == 0.0`.

---

## 6. Risk Analysis & Test Strategy

### 6.1 Failure Modes & Mitigations

| Risk / Edge Case | Likelihood | Impact | Architectural Mitigation |
|---|---|---|---|
| **RNG Pollution Desynchronization** | High | Severe | Generate weather schedules from independent hash stream `hashlib.md5(f"weather:{seed}")`, never touching `world.rng`. |
| **Species Trap / Mass Starvation** | Med | Critical | Never allow terrain gating to close off 100% of a species' core habitat (e.g., `DEEP` water never freezes; `PLAIN` never completely blocks land). |
| **Forbidden Token Telemetry Leak** | Med | Critical | Ban all forbidden substrings (`POISON`, `DAMAGE`, `HEAL`, `SPREAD`, `FRUIT_`, `law_id`) from weather state and modifier dictionaries. |
| **Scrubbing Desync in Replay Buffer** | Low | Med | Weather state is a pure function of `(seed, tick_no)`, allowing identical evaluation during forward, backward, or scrubbed playback. |
| **Extreme Stamina Depletion Floor** | Low | High | Movement cost multiplier clamped between `[0.8, 1.5]`, preventing sudden zero-energy death spikes. |

### 6.2 Test Suite Specification

A robust test suite should be implemented under `tests/test_weather.py`:
1. `test_weather_determinism`: Given seed $S$, tick $T$, weather state and progress are identical across multiple isolated runs.
2. `test_weather_cycle_progression`: Verify epoch transitions at expected tick intervals and verify `0.0 <= progress <= 1.0`.
3. `test_weather_modulates_movement_cost`: Assert creature energy deduction during `SOLAR_FLARE` exceeds `CLEAR`.
4. `test_weather_modulates_visibility`: Assert sight radius in `SPORE_STORM` reflects spore fog penalty with trait mitigation.
5. `test_weather_modulates_plant_growth`: Assert plant regeneration rate follows `plant_growth_mult`.
6. `test_spectate_weather_telemetry_schema`: Assert `/v1/spectate` frames contain valid `weather` object with expected keys and types.
7. `test_weather_no_law_leak`: Assert `FORBIDDEN_RUNNING_PATTERN.search(json.dumps(frame))` returns `None` across all weather states.
8. `test_e2e_regression`: Execute full 208-test E2E suite (`pytest tests/e2e`) to guarantee 0 regressions across all existing features.

---

## 7. Concrete Code Implementation Proposal

### 7.1 Proposed Module: `genesis/weather.py`

```python
"""Genesis Zero — Dynamic Environmental Weather System (R2)."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from genesis.world import phase_at


class WeatherType(StrEnum):
    CLEAR = "CLEAR"
    SPORE_STORM = "SPORE_STORM"
    SOLAR_FLARE = "SOLAR_FLARE"
    MAGNETIC_SHIFT = "MAGNETIC_SHIFT"


@dataclass(frozen=True)
class WeatherModifiers:
    move_cost_mult: float = 1.0
    upkeep_mult: float = 1.0
    sight_penalty: int = 0
    plant_growth_mult: float = 1.0
    algae_growth_mult: float = 1.0
    corpse_decay_ticks: int = 15
    hazard: str = "CALM"

    def to_dict(self) -> dict[str, Any]:
        return {
            "move_cost_mult": round(self.move_cost_mult, 2),
            "sight_penalty": self.sight_penalty,
            "plant_growth_mult": round(self.plant_growth_mult, 2),
            "algae_growth_mult": round(self.algae_growth_mult, 2),
            "hazard": self.hazard,
        }


WEATHER_PROFILES: dict[WeatherType, WeatherModifiers] = {
    WeatherType.CLEAR: WeatherModifiers(
        move_cost_mult=1.0,
        upkeep_mult=1.0,
        sight_penalty=0,
        plant_growth_mult=1.0,
        algae_growth_mult=1.0,
        corpse_decay_ticks=15,
        hazard="CALM",
    ),
    WeatherType.SPORE_STORM: WeatherModifiers(
        move_cost_mult=1.4,
        upkeep_mult=1.1,
        sight_penalty=1,
        plant_growth_mult=0.5,
        algae_growth_mult=1.8,
        corpse_decay_ticks=15,
        hazard="SPORES",
    ),
    WeatherType.SOLAR_FLARE: WeatherModifiers(
        move_cost_mult=1.5,
        upkeep_mult=1.2,
        sight_penalty=0,
        plant_growth_mult=1.6,
        algae_growth_mult=0.8,
        corpse_decay_ticks=8,
        hazard="SOLAR",
    ),
    WeatherType.MAGNETIC_SHIFT: WeatherModifiers(
        move_cost_mult=1.1,
        upkeep_mult=1.0,
        sight_penalty=0,
        plant_growth_mult=1.0,
        algae_growth_mult=1.0,
        corpse_decay_ticks=15,
        hazard="MAGNETIC",
    ),
}

DEFAULT_CYCLE_LEN = 50


class WeatherEngine:
    """Seed-deterministic weather cycle tracker."""

    def __init__(self, seed: int, cycle_len: int = DEFAULT_CYCLE_LEN) -> None:
        self.seed = seed
        self.cycle_len = cycle_len
        # Generate predictable sequence of phenomena:
        # Epoch 0 is CLEAR. Epoch 1..N cycle through randomized non-CLEAR phenomena.
        s_seed = int(hashlib.md5(f"weather:{seed}".encode()).hexdigest()[:16], 16)
        rng = random.Random(s_seed)
        phenomena = [WeatherType.SPORE_STORM, WeatherType.SOLAR_FLARE, WeatherType.MAGNETIC_SHIFT]
        rng.shuffle(phenomena)
        self.sequence: list[WeatherType] = [WeatherType.CLEAR] + phenomena + [WeatherType.CLEAR]

    def state_at(self, tick: int) -> tuple[WeatherType, WeatherModifiers, float, int]:
        """Returns (weather_type, modifiers, progress, cycle_tick)."""
        epoch = (tick // self.cycle_len) % len(self.sequence)
        w_type = self.sequence[epoch]
        cycle_tick = tick % self.cycle_len
        progress = round(cycle_tick / float(self.cycle_len), 4)
        return w_type, WEATHER_PROFILES[w_type], progress, cycle_tick

    def telemetry_dict(self, tick: int) -> dict[str, Any]:
        w_type, mods, progress, cycle_tick = self.state_at(tick)
        return {
            "state": w_type.value,
            "cycle_tick": cycle_tick,
            "cycle_len": self.cycle_len,
            "progress": progress,
            "diurnal": phase_at(tick),
            "modifiers": mods.to_dict(),
        }
```

### 7.2 Integration Points in Existing Codebase

1. **`genesis/world.py`**:
   - Attach `self.weather = WeatherEngine(seed)` to `World`.
   - Update `visible()`: incorporate `self.weather.state_at(tick)[1].sight_penalty`.
   - Update `spawn_plants()`: scale by `weather_mods.plant_growth_mult`.
   - Update `spawn_algae()`: scale by `weather_mods.algae_growth_mult`.
   - Update `decay_corpses()`: use `weather_mods.corpse_decay_ticks`.
2. **`genesis/reflex.py` & `genesis/creature.py`**:
   - Scale movement energy cost: `cost = config.COST_MOVE * weather_mods.move_cost_mult`.
3. **`net/match.py`**:
   - In `MatchRunner.frame()`: inject `"weather": self.world.weather.telemetry_dict(tick_no) if self.world else None`.
   - In `_seed_match()`: instantiate `world.weather`.
4. **`genesis/logio.py`**:
   - Add `"WEATHER_CHANGE"` to `EVENT_KINDS`.
5. **`web/watch3d.js`**:
   - Read `frame.weather` and trigger procedural visual/audio weather cues.

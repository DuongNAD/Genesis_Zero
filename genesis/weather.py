"""Mô đun quản lý thời tiết và các hiện tượng môi trường vĩ mô (Milestone M2_WEATHER).

Hệ thống thời tiết chu kỳ seed-deterministic:
- WeatherType: CLEAR, RAIN, SPORE_STORM, SOLAR_FLARE, MAGNETIC_SHIFT
- WeatherModifiers: move_cost_mult, sight_penalty, plant_mult, algae_mult
- WeatherState: name, tick_in_cycle, cycle_len, progress, modifiers
- weather_at(seed, tick, cycle_len=50): hàm thuần tất định theo (seed, tick),
  Epoch 0 (0-49) luôn là CLEAR cho onboarding sạch.
- to_dict(weather_state): xuất payload telemetry an toàn, không chứa token cấm.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


class WeatherType(str, Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    SPORE_STORM = "SPORE_STORM"
    SOLAR_FLARE = "SOLAR_FLARE"
    MAGNETIC_SHIFT = "MAGNETIC_SHIFT"


@dataclass(frozen=True)
class WeatherModifiers:
    move_cost_mult: float
    sight_penalty: int
    plant_mult: float
    algae_mult: float
    hazard_kind: str | None = None

    @property
    def plant_growth_mult(self) -> float:
        return self.plant_mult

    @property
    def algae_growth_mult(self) -> float:
        return self.algae_mult


WEATHER_MODIFIERS: dict[str, WeatherModifiers] = {
    WeatherType.CLEAR.value: WeatherModifiers(
        move_cost_mult=1.0,
        sight_penalty=0,
        plant_mult=1.0,
        algae_mult=1.0,
    ),
    WeatherType.RAIN.value: WeatherModifiers(
        move_cost_mult=1.3,
        sight_penalty=1,
        plant_mult=1.5,
        algae_mult=1.4,
    ),
    WeatherType.SPORE_STORM.value: WeatherModifiers(
        move_cost_mult=1.5,
        sight_penalty=2,
        plant_mult=0.5,
        algae_mult=0.8,
    ),
    WeatherType.SOLAR_FLARE.value: WeatherModifiers(
        move_cost_mult=1.4,
        sight_penalty=1,
        plant_mult=0.7,
        algae_mult=0.5,
    ),
    WeatherType.MAGNETIC_SHIFT.value: WeatherModifiers(
        move_cost_mult=1.2,
        sight_penalty=0,
        plant_mult=1.0,
        algae_mult=1.1,
    ),
}

CYCLE_WEATHERS: tuple[str, ...] = (
    WeatherType.RAIN.value,
    WeatherType.SPORE_STORM.value,
    WeatherType.SOLAR_FLARE.value,
    WeatherType.MAGNETIC_SHIFT.value,
)


@dataclass
class WeatherState:
    name: str
    tick_in_cycle: int
    cycle_len: int = 50
    progress: float = 0.0
    modifiers: WeatherModifiers = WeatherModifiers(1.0, 0, 1.0, 1.0)

    @property
    def state(self) -> str:
        return self.name

    @property
    def cycle_tick(self) -> int:
        return self.tick_in_cycle

    def to_dict(self, diurnal: str | None = None) -> dict:
        d = {
            "name": self.name,
            "state": self.name,
            "tick_in_cycle": self.tick_in_cycle,
            "cycle_tick": self.tick_in_cycle,
            "cycle_len": self.cycle_len,
            "progress": round(self.progress, 4),
            "modifiers": {
                "move_cost_mult": self.modifiers.move_cost_mult,
                "sight_penalty": self.modifiers.sight_penalty,
                "plant_mult": self.modifiers.plant_mult,
                "algae_mult": self.modifiers.algae_mult,
                "plant_growth_mult": self.modifiers.plant_growth_mult,
                "algae_growth_mult": self.modifiers.algae_growth_mult,
            },
        }
        if diurnal is not None:
            d["diurnal"] = diurnal
        return d


def to_dict(weather_state: WeatherState, diurnal: str | None = None) -> dict:
    """Chuyển WeatherState sang dict tương thích JSON."""
    return weather_state.to_dict(diurnal=diurnal)


def weather_at(seed: int, tick: int, cycle_len: int = 50) -> WeatherState:
    """Xác định trạng thái thời tiết tại một tick cụ thể một cách tất định.

    - Epoch 0 (ticks 0 đến cycle_len - 1): luôn là CLEAR.
    - Các epoch tiếp theo: xác định theo hash md5(f"weather:{seed}:{epoch}").
    - Hoàn toàn không đụng vào world.rng hay global RNG.
    """
    safe_cycle_len = max(1, cycle_len)
    safe_tick = max(0, tick)
    epoch = safe_tick // safe_cycle_len
    tick_in_cycle = safe_tick % safe_cycle_len
    progress = tick_in_cycle / safe_cycle_len

    if epoch == 0:
        name = WeatherType.CLEAR.value
    else:
        digest = hashlib.md5(f"weather:{seed}:{epoch}".encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % len(CYCLE_WEATHERS)
        name = CYCLE_WEATHERS[idx]

    modifiers = WEATHER_MODIFIERS.get(
        name,
        WEATHER_MODIFIERS[WeatherType.CLEAR.value],
    )
    return WeatherState(
        name=name,
        tick_in_cycle=tick_in_cycle,
        cycle_len=safe_cycle_len,
        progress=progress,
        modifiers=modifiers,
    )

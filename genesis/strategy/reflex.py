"""Genesis Zero — genesis/strategy/reflex.py
Hiện thực chiến lược phản xạ bản năng (ReflexStrategist).
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from genesis.reflex import ActiveGoal, choose_goal

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World


class ReflexStrategist:
    """Tầng chiến lược mặc định: gọi tầng phản xạ bản năng choose_goal."""

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        if current is not None and current.ttl > 0:
            return None
        if rng is None:
            rng = random.Random(0)
        return choose_goal(c, world, seen, rng)


__all__ = ["ReflexStrategist"]

"""Genesis Zero — genesis/strategy/base.py
Giao diện chiến lược (Strategist Protocol) và các cấu trúc mục tiêu chung.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from genesis.reflex import ActiveGoal, Goal

if TYPE_CHECKING:
    from genesis.creature import Creature
    from genesis.world import World


def payload_to_goal(payload: dict | None) -> ActiveGoal | None:
    """Đổi payload 'decide' đã hợp lệ thành ActiveGoal.

    Dùng chung cho tầng LLM sống (B-05) và replay (B-06) — hai đường phải đi
    qua đúng một hàm, nếu không replay sẽ "khớp" trên một phép biến đổi khác.
    """
    if not isinstance(payload, dict):
        return None
    try:
        goal = Goal(payload["goal"])
        ttl = int(payload["ttl"])
    except (KeyError, ValueError, TypeError):
        return None
    target = payload.get("target") or None
    return ActiveGoal(goal=goal, target=target, ttl=ttl)


@runtime_checkable
class Strategist(Protocol):
    """Giao diện chiến lược chung cho mọi nguồn quyết định.

    Chỉ duy nhất `decide` là bắt buộc để hỗ trợ duck-typing trong test suite.
    Các phương thức vòng đời (lifecycle) là tuỳ chọn:
    - begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None
    - take_says(self) -> dict[str, Any]
    - take_shift(self, c: Creature) -> tuple[str, str] | None
    - observe(self, tick_no: int, world: World, creatures: list[Creature],
              events: dict[str, list[dict]], state: Any) -> None
    """

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        """Ý đồ mới cho sinh vật c, hoặc None để giữ ý đồ cũ.

        Được gọi **mỗi tick cho mỗi con còn sống**, không phải chỉ khi ý đồ cũ
        hết hạn. Tầng LLM cần thế: quyết định của nó về tới lúc nào thì đè lúc
        ấy (B-05 bất biến 1), chứ không chờ hết `ttl`. Tầng nào không muốn đè
        thì trả `None` — `current` chính là để nó biết mà trả `None`.
        """
        ...


class BaseStrategist:
    """Lớp cơ sở cung cấp no-op default implementations cho toàn bộ lifecycle."""

    def begin_tick(self, creatures: list[Creature], world: World, tick_no: int) -> None:
        pass

    def decide(
        self,
        c: Creature,
        world: World,
        seen: list[Creature],
        rng: random.Random | None = None,
        tick_no: int = 0,
        current: ActiveGoal | None = None,
    ) -> ActiveGoal | None:
        return None

    def take_says(self) -> dict[str, Any]:
        return {}

    def take_shift(self, c: Creature) -> tuple[str, str] | None:
        return None

    def observe(
        self,
        tick_no: int,
        world: World,
        creatures: list[Creature],
        events: dict[str, list[dict]],
        state: Any,
    ) -> None:
        pass


__all__ = [
    "ActiveGoal",
    "BaseStrategist",
    "Goal",
    "Strategist",
    "payload_to_goal",
]

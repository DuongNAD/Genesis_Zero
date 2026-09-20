"""Genesis Zero — strategist: tầng chiến lược và các hiện thực ra quyết định.

Mô-đun này đã được phân rã thành gói mô-đun `genesis.strategy/` (Feature 17 / Milestone M3).
File này đóng vai trò facade tương thích ngược 100%, tái xuất toàn bộ các symbol
để toàn bộ mã nguồn hiện tại trong `genesis/`, `scripts/`, `net/` và `tests/`
tiếp tục hoạt động mà không cần thay đổi đường dẫn import.
"""

from __future__ import annotations

from genesis.strategy import (
    _BAND_NOTE,
    _CLAIM_TAIL,
    _OUTCOME_VN,
    _PHASE_NOTE,
    _RECENT_NOTE,
    ARGLESS_KINDS_FOR_TEST,
    SURFACE_KINDS,
    ActiveGoal,
    BaseStrategist,
    Goal,
    LlmStrategist,
    ReflexStrategist,
    RemoteClientStrategist,
    Strategist,
    _arg_options,
    _budget,
    _effect_schema,
    _kind_arg_schema,
    ctx_to_pairs,
    legal_args,
    payload_to_goal,
    schema_for,
)

__all__ = [
    "ARGLESS_KINDS_FOR_TEST",
    "SURFACE_KINDS",
    "_BAND_NOTE",
    "_CLAIM_TAIL",
    "_OUTCOME_VN",
    "_PHASE_NOTE",
    "_RECENT_NOTE",
    "ActiveGoal",
    "BaseStrategist",
    "Goal",
    "LlmStrategist",
    "ReflexStrategist",
    "RemoteClientStrategist",
    "Strategist",
    "_arg_options",
    "_budget",
    "_effect_schema",
    "_kind_arg_schema",
    "ctx_to_pairs",
    "legal_args",
    "payload_to_goal",
    "schema_for",
]

# Invariant Contract Note (B-14 / Feature 17):
# Prioritized decision hierarchy and operations implemented in genesis.strategy.llm:
#   1. kind = "codex"
#   2. kind = "hunch"
# Recorded operations:
#   HUNCH_OP: self._write(tick_no, "HUNCH_OP", c, ...)


"""Genesis Zero — genesis/strategy package.

Gói chiến lược phân rã từ monolith genesis/strategist.py:
- base: Strategist Protocol, payload_to_goal
- law_schema: legal_args, schema_for, LawDSL JSON Schema builders
- reflex: ReflexStrategist
- remote: RemoteClientStrategist
- llm: LlmStrategist và các tiện ích kết nối LLM
"""

from __future__ import annotations

from genesis.strategy.base import (
    ActiveGoal,
    BaseStrategist,
    Goal,
    Strategist,
    payload_to_goal,
)
from genesis.strategy.law_schema import (
    ARGLESS_KINDS_FOR_TEST,
    SURFACE_KINDS,
    _arg_options,
    _effect_schema,
    _kind_arg_schema,
    legal_args,
    schema_for,
)
from genesis.strategy.llm import (
    _BAND_NOTE,
    _CLAIM_TAIL,
    _OUTCOME_VN,
    _PHASE_NOTE,
    _RECENT_NOTE,
    LlmStrategist,
    _budget,
    ctx_to_pairs,
)
from genesis.strategy.reflex import ReflexStrategist
from genesis.strategy.remote import RemoteClientStrategist

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

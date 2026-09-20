"""Unit tests for genesis/oracle_run.py."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from genesis.lawdsl import Dur, Effect, EffectKind, Law, Mag, Trigger, TriggerKind
from genesis.oracle_run import _answer_to_effect, run_oracle


def test_answer_to_effect_valid():
    d = {
        "kind": "DAMAGE",
        "mag": "BIG",
        "dur": "LONG",
        "r": 2,
        "arg": "FRUIT_RED",
        "dir": "NORTH",
    }
    eff = _answer_to_effect(d)
    assert eff is not None
    assert eff.kind == EffectKind.DAMAGE
    assert eff.mag == Mag.BIG
    assert eff.dur == Dur.LONG
    assert eff.r == 2
    assert eff.arg == "FRUIT_RED"
    assert eff.dir == "NORTH"


def test_answer_to_effect_malformed_and_none():
    assert _answer_to_effect(None) is None
    assert _answer_to_effect("invalid") is None
    assert _answer_to_effect({}) is None
    assert _answer_to_effect({"kind": None}) is None
    assert _answer_to_effect({"kind": ""}) is None

    # Invalid kind (ValueError)
    assert _answer_to_effect({"kind": "UNKNOWN_KIND"}) is None

    # Invalid mag (ValueError)
    assert _answer_to_effect({"kind": "DAMAGE", "mag": "ULTRA"}) is None

    # Invalid dur (ValueError)
    assert _answer_to_effect({"kind": "DAMAGE", "dur": "ETERNAL"}) is None

    # Dict that raises TypeError or KeyError on access
    class BadDict(dict):
        def __getitem__(self, key):
            if key == "kind":
                return "DAMAGE"
            raise TypeError("bad type")

    assert _answer_to_effect(BadDict()) is None


@pytest.mark.asyncio
async def test_run_oracle_empty_laws_or_no_slots():
    strategist = MagicMock()
    creatures = [MagicMock(id="c1", species="L1")]
    world = MagicMock()

    # Empty laws
    assert await run_oracle(strategist, creatures, world, [], 1, 42) == {}

    # Strategist without matching creature slot
    strategist.slots = {}
    law = Law(
        trigger=Trigger(kind=TriggerKind.DRINK),
        conds=(),
        effect=Effect(kind=EffectKind.DAMAGE),
    )
    assert await run_oracle(strategist, creatures, world, [law], 1, 42) == {}


@pytest.mark.asyncio
async def test_run_oracle_execution_loop(monkeypatch):
    from genesis.tick import build_match

    world, cs, _, _ = build_match(seed=1)
    c1, c2 = cs[0], cs[1]
    creatures = [c1, c2]

    law = Law(
        trigger=Trigger(kind=TriggerKind.DRINK),
        conds=(),
        effect=Effect(kind=EffectKind.DAMAGE, mag=Mag.MED, dur=Dur.SHORT),
    )
    laws = [law]

    strategist = MagicMock()
    strategist.slots = {c1.id: 0, c2.id: 1}
    strategist.base_url = "http://fake-llm:8080"
    strategist.transport = None
    strategist.timeout = 10.0
    strategist._call_ms = 100.0
    strategist._ensure_slots_for = AsyncMock(return_value=2)
    strategist.build_prompt = MagicMock(return_value=("system prompt", "user prompt"))

    mock_log = MagicMock()

    # Mock ask to return valid answer for c1, and None for c2
    call_count = 0

    async def mock_ask(base_url, slot, system, body, budget, schema, client=None):
        nonlocal call_count
        call_count += 1
        if slot == 0:
            return {
                "json": {
                    "answers": [
                        {
                            "q": 0,
                            "effect": {"kind": "DAMAGE", "mag": "MED", "dur": "SHORT"},
                        }
                    ]
                }
            }
        return None

    monkeypatch.setattr("genesis.oracle_run.ask", mock_ask)

    out = await run_oracle(
        strategist=strategist,
        creatures=creatures,
        world=world,
        laws=laws,
        tick_no=10,
        seed=42,
        log=mock_log,
    )

    assert c1.id in out
    assert isinstance(out[c1.id], float)
    # mock_log wrote individual law and summary ORACLE logs
    assert mock_log.write.call_count >= 2

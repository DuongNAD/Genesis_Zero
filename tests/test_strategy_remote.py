"""Tests for genesis/strategy/remote.py (RemoteClientStrategist)."""

from __future__ import annotations

import collections
import queue
from unittest.mock import MagicMock

from genesis import speech
from genesis.reflex import ActiveGoal
from genesis.strategy.remote import RemoteClientStrategist


def _make_mock_creature(cid: str = "c1", adapt_points: int = 10) -> MagicMock:
    c = MagicMock()
    c.id = cid
    c.adapt_points = adapt_points
    return c


def test_remote_strategist_init():
    strat_default = RemoteClientStrategist()
    assert strat_default.queue == {}
    assert strat_default.pending_say == {}
    assert strat_default.want_shift == set()

    q_dict = {"c1": []}
    strat_custom = RemoteClientStrategist(q_dict)
    assert strat_custom.queue is q_dict


def test_remote_strategist_take_says():
    strat = RemoteClientStrategist()
    say1 = speech.Say("c1", "hello")
    strat.pending_say["c1"] = say1

    out = strat.take_says()
    assert out == {"c1": say1}
    assert strat.pending_say == {}

    # Second call returns empty
    assert strat.take_says() == {}


def test_remote_strategist_take_shift_branches():
    strat = RemoteClientStrategist()
    c = _make_mock_creature("c1", 10)

    # 1. No choice yet: registers into want_shift and records adapt_points
    assert strat.take_shift(c) is None
    assert "c1" in strat.want_shift
    assert strat._shift_asked["c1"] == 10

    # 2. Already asked at same adapt_points: returns None immediately
    strat.want_shift.clear()
    assert strat.take_shift(c) is None
    assert "c1" not in strat.want_shift

    # 3. Points changed: asks again
    c.adapt_points = 20
    assert strat.take_shift(c) is None
    assert "c1" in strat.want_shift
    assert strat._shift_asked["c1"] == 20

    # 4. Choice present in shift_choice: pops and clears _shift_asked
    strat.shift_choice["c1"] = ("brain", "speed")
    choice = strat.take_shift(c)
    assert choice == ("brain", "speed")
    assert "c1" not in strat.shift_choice
    assert "c1" not in strat._shift_asked


def test_remote_strategist_decide_branches():
    world = MagicMock()
    c = _make_mock_creature("c1")

    # 1. c.id not in queue
    strat = RemoteClientStrategist({})
    assert strat.decide(c, world, []) is None

    # 2. val is ActiveGoal
    g1 = MagicMock(spec=ActiveGoal)
    strat = RemoteClientStrategist({"c1": g1})
    res = strat.decide(c, world, [])
    assert res is g1
    assert "c1" not in strat.queue

    # 3. val is list: non-empty then empty
    g2 = MagicMock(spec=ActiveGoal)
    strat = RemoteClientStrategist({"c1": [g2]})
    assert strat.decide(c, world, []) is g2
    assert strat.decide(c, world, []) is None  # now list is empty

    # 4. val is collections.deque: non-empty then empty
    g3 = MagicMock(spec=ActiveGoal)
    dq: collections.deque = collections.deque([g3])
    strat = RemoteClientStrategist({"c1": dq})
    assert strat.decide(c, world, []) is g3
    assert strat.decide(c, world, []) is None  # now deque is empty

    # 5. val is queue.Queue: non-empty then empty (queue.Empty caught)
    g4 = MagicMock(spec=ActiveGoal)
    q: queue.Queue = queue.Queue()
    q.put(g4)
    strat = RemoteClientStrategist({"c1": q})
    assert strat.decide(c, world, []) is g4
    assert strat.decide(c, world, []) is None  # empty queue

    # 6. val is fallback object (not None and not the above types)
    fallback_obj = object()
    strat = RemoteClientStrategist({"c1": fallback_obj})
    assert strat.decide(c, world, []) is fallback_obj
    assert "c1" not in strat.queue

    # 7. val is None
    strat = RemoteClientStrategist({"c1": None})
    assert strat.decide(c, world, []) is None

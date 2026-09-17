"""Offline v1 contract tests; no real model, Blender or expensive law gates."""
import asyncio
import json
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

from genesis.llm_client import ask
from genesis.prompt import completion_budget
from genesis.tick import build_match
from net import match, server, state
from net.match import MatchRunner, Phase, Registration


@pytest.mark.parametrize("content", ['{"goal":"REST"}', '<think>{"wrong":1}</think>{"goal":"REST"}'])
def test_frontier_separates_reasoning(content):
    def respond(req):
        body = json.loads(req.content)
        assert req.url.path == "/v1/chat/completions"
        assert body["max_completion_tokens"] == 164
        assert "max_tokens" not in body and "temperature" not in body
        assert req.headers["Authorization"] == "Bearer test-only"
        return httpx.Response(200, json={"choices": [{"message": {
            "content": content, "reasoning_content": "not JSON"}, "finish_reason": "stop"}],
            "usage": {"completion_tokens": 60, "completion_tokens_details": {"reasoning_tokens": 50}}})
    result = asyncio.run(ask("http://test/v1", backend="frontier", model="test",
                            thinking_tokens=100, max_tokens=64, api_key="test-only",
                            transport=httpx.MockTransport(respond)))
    assert result["json"] == {"goal": "REST"}
    assert result["n"] == 60 and result["thinking_tokens"] == 50
    assert result["answer_tokens"] == 10 and "think" not in result["raw"]


@pytest.mark.parametrize("content", [None, "<think>unfinished", "[]", "not JSON"])
def test_frontier_invalid_is_miss(content):
    response = {"choices": [{"message": {"content": content}}]}
    assert asyncio.run(ask("http://test", backend="frontier",
                          transport=httpx.MockTransport(lambda r: httpx.Response(200, json=response)))) is None


def test_budget():
    assert completion_budget(64, 2048) == 2112
    with pytest.raises(ValueError):
        completion_budget(0)


def test_health_and_dossier(monkeypatch):
    runner = MatchRunner(log_dir=None)
    monkeypatch.setattr(state, "runner", runner)
    client = TestClient(server.app)
    assert client.get("/v1/healthz").status_code == 200
    assert client.get("/v1/readyz").status_code == 200
    runner.preparing = True
    assert client.get("/v1/readyz").status_code == 503
    assert client.get("/v1/healthz").status_code == 200
    runner.preparing = False
    runner.world, runner.creatures, runner.state, runner.rng = build_match(9)
    c = runner.creatures[0]
    c.generation = 3
    runner.registrations["test"] = Registration("test", "token", c.species, "test", "", "test", 1, 1, traits=c.traits)
    frame = runner.frame(0, [])
    assert frame["schema_version"] == "1.0"
    assert frame["match_id"] == runner.match_id
    data = client.get("/v1/spectate/dossier").json()
    profile = next(p for p in data["creatures"] if p["id"] == c.id)
    expected = next(p for p in frame["creatures"] if p["id"] == c.id)
    assert profile["gen"] == 3
    assert profile["features"] == expected["features"]
    assert profile["domain"] == expected["domain"]
    assert profile["e_max"] == c.traits.energy_max
    assert profile["dt_traits"] == expected["d_tr"]


def test_preparation_keeps_loop_responsive(monkeypatch):
    started, release = threading.Event(), threading.Event()
    owner = threading.get_ident()
    def generate(seed, arm):
        assert threading.get_ident() != owner
        started.set()
        if not release.wait(5):
            raise RuntimeError("test worker was not released")
        return []
    monkeypatch.setattr(match, "generate_cached", generate)
    async def check():
        runner = MatchRunner(log_dir=None)
        runner.phase = Phase.SEEDING
        task = asyncio.create_task(runner.seed_match_async())
        try:
            for _ in range(100):
                if started.is_set():
                    break
                await asyncio.sleep(.01)
            assert started.is_set() and runner.preparing
            assert runner.world is None
        finally:
            release.set()
            await task
        assert runner.world is not None and not runner.preparing
    asyncio.run(check())


def test_preparation_error_is_visible(monkeypatch):
    def fail(*a, **kw):
        raise RuntimeError("gate failed")
    monkeypatch.setattr(match, "generate_cached", fail)
    runner = MatchRunner(log_dir=None)
    with pytest.raises(RuntimeError, match="gate failed"):
        asyncio.run(runner.seed_match_async())
    assert runner.preparation_failed and not runner.preparing
    assert runner.world is None

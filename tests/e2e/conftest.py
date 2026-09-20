"""Genesis Zero — Conftest and Shared Fixtures for 4-Tier E2E Test Suite.

Provides isolated test environments, deterministic simulation runners,
mock network servers, and schema verification utilities.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient

from genesis import config
from genesis.creature import Creature
from genesis.domain import Domain
from genesis.traits import Traits
from net import server, state
from net.match import MatchRunner

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the absolute path to the Genesis Zero project root."""
    return PROJECT_ROOT


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide an isolated temporary workspace directory."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.fixture
def mock_runner(temp_workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[MatchRunner, None, None]:
    """Provide an isolated MatchRunner instance bound to net.state."""
    runner = MatchRunner(
        seed=12345,
        ticks=100,
        tick_ms=1,
        log_dir=temp_workspace / "runs",
    )
    monkeypatch.setattr(state, "runner", runner)
    yield runner


@pytest.fixture
def test_client(mock_runner: MatchRunner) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient bound to the isolated mock runner."""
    from net.ratelimit import reset
    reset()
    if hasattr(server, "limiter"):
        server.limiter._hits.clear()
        server.limiter._strikes.clear()
        server.limiter._banned_until.clear()
    with TestClient(server.app) as client:
        yield client


@pytest.fixture
def species_factory():
    """Factory helper to build well-formed Creature instances across 3 domains."""
    def _create(
        domain: Domain = Domain.CAN,
        species_id: str = "L1",
        pos: tuple[int, int] = (5, 5),
        brain: int = 2,
        attack: int = 2,
        armor: int = 2,
        speed: int = 2,
        sense: int = 2,
        stomach: int = 2,
    ) -> Creature:
        traits = Traits(
            brain=brain,
            attack=attack,
            armor=armor,
            speed=speed,
            sense=sense,
            stomach=stomach,
        )
        return Creature(
            id=f"{species_id}:0",
            species=species_id,
            traits=traits,
            pos=pos,
            hp=config.HP_MAX,
            energy=traits.energy_max,
        )
    return _create


@pytest.fixture
def sample_species_payloads() -> dict[str, dict[str, Any]]:
    """Return sample registration payloads for Land, Water, and Sky species."""
    return {
        "land": {
            "display_name": "Sói Xám",
            "persona": "Săn mồi theo bầy trên đồng cỏ",
            "model_name": "llama-3-8b",
            "params_b": 8,
            "brain_tier": 3,
            "league": "LEAGUE_LLM",
            "pop_request": 2,
        },
        "water": {
            "display_name": "Cá Ngừ",
            "persona": "Bơi sâu săn mồi trong lòng đại dương",
            "model_name": "qwen-7b",
            "params_b": 7,
            "brain_tier": 2,
            "league": "LEAGUE_LLM",
            "pop_request": 2,
        },
        "sky": {
            "display_name": "Đại Bàng",
            "persona": "Bay lượn trên cao quan sát con mồi",
            "model_name": "mistral-7b",
            "params_b": 7,
            "brain_tier": 4,
            "league": "LEAGUE_LLM",
            "pop_request": 2,
        },
    }

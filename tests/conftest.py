"""Fixture dùng chung."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

PKG_DIR = Path(__file__).resolve().parent.parent / "genesis"


@pytest.fixture
def rng() -> random.Random:
    """Bộ sinh ngẫu nhiên cố định cho test. Không bao giờ dùng random toàn cục."""
    return random.Random(1234)


@pytest.fixture
def tmp_run(tmp_path: Path) -> Path:
    d = tmp_path / "runs"
    d.mkdir()
    return d


@pytest.fixture(scope="session")
def pkg_dir() -> Path:
    return PKG_DIR

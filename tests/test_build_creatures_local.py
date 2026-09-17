"""Contracts for the existing standalone local Blender pipeline."""
import inspect

from scripts import build_creatures


def test_main_signature():
    assert callable(build_creatures.main)
    assert not inspect.signature(build_creatures.main).parameters


def test_explicit_blender_override(tmp_path, monkeypatch):
    binary = tmp_path / "Blender folder" / "blender.exe"
    binary.parent.mkdir()
    binary.touch()
    monkeypatch.setenv("GENESIS_BLENDER_BIN", str(binary))
    assert build_creatures.find_blender() == str(binary)

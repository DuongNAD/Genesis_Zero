"""Empirical Adversarial Stress Test Suite for Milestone M3 (Architectural Upgrade & Maintainability).

Challenger: teamwork_preview_challenger_m3_1
Target:
- Genesis_Zero Milestone M3 Architectural Refactoring
- Packaging & Configuration Standardization (net/config.py vs net_config.py)
- God Module Decomposition (genesis/strategist.py -> genesis/strategy/)
- Centralized Platform Utilities (genesis/platform.py)
- Automated Log Pruning (genesis/util/log_cleanup.py & scripts/prune_runs.py)
- Protocol Contracts & Subclassing Extensibility
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, ClassVar, cast
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ==============================================================================
# 1. Compatibility Stress Testing: genesis.strategist Facade & Package
# ==============================================================================

class TestStrategistFacadeCompatibility:
    """Adversarial stress testing of symbol resolution, equality, and re-export integrity."""

    EXPECTED_SYMBOLS: ClassVar[list[str]] = [
        "ARGLESS_KINDS_FOR_TEST",
        "ActiveGoal",
        "Goal",
        "LlmStrategist",
        "ReflexStrategist",
        "RemoteClientStrategist",
        "SURFACE_KINDS",
        "Strategist",
        "_BAND_NOTE",
        "_CLAIM_TAIL",
        "_OUTCOME_VN",
        "_PHASE_NOTE",
        "_RECENT_NOTE",
        "_arg_options",
        "_budget",
        "_effect_schema",
        "_kind_arg_schema",
        "ctx_to_pairs",
        "legal_args",
        "payload_to_goal",
        "schema_for",
    ]

    def test_all_expected_symbols_importable_and_identical(self) -> None:
        """Verify that every single expected symbol can be imported from both paths with exact identity."""
        import genesis.strategist as legacy_strat
        import genesis.strategy as modern_strat

        for sym in self.EXPECTED_SYMBOLS:
            assert hasattr(legacy_strat, sym), f"genesis.strategist missing symbol {sym}"
            assert hasattr(modern_strat, sym), f"genesis.strategy missing symbol {sym}"

            legacy_val = getattr(legacy_strat, sym)
            modern_val = getattr(modern_strat, sym)
            assert legacy_val is modern_val, f"Symbol {sym} identity mismatch between legacy and modern"

    def test_dunder_all_consistency(self) -> None:
        """Verify __all__ in legacy and modern packages match exactly."""
        import genesis.strategist as legacy_strat
        import genesis.strategy as modern_strat

        legacy_all = sorted(legacy_strat.__all__)
        modern_all = sorted(modern_strat.__all__)
        assert legacy_all == modern_all, f"__all__ mismatch: {legacy_all} vs {modern_all}"
        for sym in self.EXPECTED_SYMBOLS:
            assert sym in legacy_all, f"{sym} not declared in __all__"

    def test_dynamic_from_import_star(self) -> None:
        """Verify that 'from genesis.strategist import *' introduces all public symbols."""
        namespace: dict[str, Any] = {}
        exec("from genesis.strategist import *", namespace)
        for sym in self.EXPECTED_SYMBOLS:
            if not sym.startswith("_"):
                assert sym in namespace, f"Public symbol {sym} missing from import *"

    def test_subclassing_and_runtime_checkable_protocol(self) -> None:
        """Verify that user-defined subclasses and structural duck-typing satisfy Strategist."""
        from genesis.strategist import (
            ReflexStrategist,
            Strategist,
        )

        # 1. Custom Reflex Subclass
        class CustomReflex(ReflexStrategist):
            def __init__(self, multiplier: float = 1.5):
                super().__init__()
                self.multiplier = multiplier

            def decide(self, creature, world, creatures, rng, laws, tick_no=0):
                action = super().decide(creature, world, creatures, rng, laws, tick_no)
                return action

        cr = CustomReflex()
        assert isinstance(cr, ReflexStrategist)
        assert isinstance(cr, Strategist)

        # 2. Custom Structural Strategist (No inheritance, pure duck-typing)
        class DuckStrategist:
            def decide(self, creature, world, creatures, rng, laws, tick_no=0):
                return None

            def observe(self, creature, action, result, world, creatures, laws, tick_no=0):
                pass

        duck = DuckStrategist()
        assert isinstance(duck, Strategist)

        # 3. Defective Strategist missing decide should NOT satisfy Strategist
        class MissingDecideStrategist:
            def observe(self, creature, action, result, world, creatures, laws, tick_no=0):
                pass

        inc = MissingDecideStrategist()
        assert not isinstance(inc, Strategist)


# ==============================================================================
# 2. Compatibility Stress Testing: net_config vs net.config
# ==============================================================================

class TestNetConfigEquivalence:
    """Adversarial stress testing of net_config root shim and net.config package."""

    def test_all_constants_and_types_identical(self) -> None:
        """Every exported attribute in net.config must exist and be identical in net_config."""
        import net_config
        from net import config

        assert hasattr(net_config, "__all__")
        assert hasattr(config, "__all__")
        assert set(net_config.__all__) == set(config.__all__)

        for attr in config.__all__:
            val_shim = getattr(net_config, attr)
            val_canonical = getattr(config, attr)
            assert val_shim == val_canonical, f"Value mismatch for {attr}: {val_shim} != {val_canonical}"
            assert val_shim is val_canonical, f"Identity mismatch for {attr}: {val_shim} is not {val_canonical}"

    def test_clean_subprocess_import_isolation(self) -> None:
        """Verify that a fresh Python process can import net_config and net.config without side effects."""
        code = (
            "import net_config\n"
            "from net import config\n"
            "assert net_config.MATCH_PORT == config.MATCH_PORT == 8000\n"
            "assert net_config.DEFAULT_HOST == config.DEFAULT_HOST == '127.0.0.1'\n"
            "assert net_config.MAP_ROTATION == config.MAP_ROTATION\n"
            "print('SUCCESS')\n"
        )
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert res.returncode == 0, f"Subprocess import failed: {res.stderr}"
        assert "SUCCESS" in res.stdout


# ==============================================================================
# 3. Platform Utilities Edge Case Stress Testing: genesis.platform
# ==============================================================================

class TestPlatformUtilitiesEdgeCases:
    """Adversarial testing of configure_console_encoding, utf8_subprocess_env, and find_python_executable."""

    def test_configure_console_encoding_broken_streams(self) -> None:
        """Verify configure_console_encoding is impervious to broken/mocked/missing streams."""
        from genesis.platform import configure_console_encoding

        # Test case A: sys.stdout is None
        with patch.object(sys, "stdout", None), patch.object(sys, "stderr", None):
            configure_console_encoding()  # Should not raise

        # Test case B: Stream without reconfigure method (e.g. io.StringIO)
        dummy_stream = io.StringIO()
        with patch.object(sys, "stdout", dummy_stream), patch.object(sys, "stderr", dummy_stream):
            configure_console_encoding()  # Should not raise

        # Test case C: Stream whose reconfigure raises OSError/ValueError
        failing_stream = MagicMock()
        failing_stream.reconfigure.side_effect = OSError("Mocked OS Error")
        with patch.object(sys, "stdout", failing_stream), patch.object(sys, "stderr", failing_stream):
            configure_console_encoding()  # Gracefully swallowed

        # Test case D: Stream whose reconfigure raises ValueError
        failing_stream2 = MagicMock()
        failing_stream2.reconfigure.side_effect = ValueError("Mocked Value Error")
        with patch.object(sys, "stdout", failing_stream2), patch.object(sys, "stderr", failing_stream2):
            configure_console_encoding()  # Gracefully swallowed

    def test_utf8_subprocess_env_mutations_and_isolation(self) -> None:
        """Verify utf8_subprocess_env handles empty dicts, overrides, and preserves base environment."""
        from genesis.platform import utf8_subprocess_env

        # 1. base_env is None -> clones os.environ
        env1 = utf8_subprocess_env(None)
        assert env1["PYTHONIOENCODING"] == "utf-8"
        assert env1["PYTHONUTF8"] == "1"
        assert len(env1) >= len(os.environ)

        # 2. Mutating returned env must NOT mutate os.environ
        env1["NEW_CANARY_VAR"] = "SHOULD_NOT_LEAK"
        assert "NEW_CANARY_VAR" not in os.environ

        # 3. Empty base_env
        env_empty = utf8_subprocess_env({})
        assert env_empty == {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

        # 4. Overriding conflicting settings
        bad_env = {"PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0", "APP_MODE": "TEST"}
        env_fixed = utf8_subprocess_env(bad_env)
        assert env_fixed["PYTHONIOENCODING"] == "utf-8"
        assert env_fixed["PYTHONUTF8"] == "1"
        assert env_fixed["APP_MODE"] == "TEST"
        # Ensure original input dict was not mutated
        assert bad_env["PYTHONIOENCODING"] == "cp1252"
        assert bad_env["PYTHONUTF8"] == "0"

        # 5. Unicode values in base_env
        unicode_env = {"VIETNAMESE_KEY": "Sinh vật kỳ bí 🐉"}
        env_u = utf8_subprocess_env(unicode_env)
        assert env_u["VIETNAMESE_KEY"] == "Sinh vật kỳ bí 🐉"

    def test_find_python_executable_edge_cases(self) -> None:
        """Verify find_python_executable under broken sys.executable or missing PATH."""
        from genesis.platform import find_python_executable

        # Case 1: Normal execution
        exe = find_python_executable()
        assert Path(exe).is_file()

        # Case 2: sys.executable is empty string -> falls back to shutil.which
        with patch.object(sys, "executable", ""):
            exe2 = find_python_executable()
            assert exe2 is not None
            assert len(exe2) > 0

        # Case 3: sys.executable is nonexistent file -> falls back to shutil.which
        with patch.object(sys, "executable", "C:\\nonexistent\\dummy\\python_fake.exe"):
            exe3 = find_python_executable()
            assert exe3 is not None
            assert len(exe3) > 0

        # Case 4: Both sys.executable and shutil.which fail -> returns fallback "python"
        with patch.object(sys, "executable", ""), patch("shutil.which", return_value=None):
            exe4 = find_python_executable()
            assert exe4 == "python"


# ==============================================================================
# 4. Law Schema & Payload Boundary Stress Testing
# ==============================================================================

class TestLawSchemaAndGoalStress:
    """Stress test LawDSL JSON Schema generation and payload_to_goal with hostile inputs."""

    def test_payload_to_goal_hostile_inputs(self) -> None:
        """payload_to_goal must be completely resilient against non-dict, missing, and malformed inputs."""
        from genesis.strategy.base import payload_to_goal

        # Non-dict inputs
        assert payload_to_goal(None) is None
        assert payload_to_goal(cast(Any, 123)) is None
        assert payload_to_goal(cast(Any, "GOAL")) is None
        assert payload_to_goal(cast(Any, ["REST"])) is None
        assert payload_to_goal(cast(Any, True)) is None

        # Dict missing required fields or invalid types
        assert payload_to_goal({}) is None
        assert payload_to_goal({"goal": None}) is None
        assert payload_to_goal({"goal": "NONEXISTENT_GOAL"}) is None
        assert payload_to_goal({"goal": "REST", "ttl": "five"}) is None
        assert payload_to_goal({"goal": "REST", "ttl": None}) is None

        # Valid payload with extra unexpected keys (should be ignored gracefully)
        payload = {"goal": "REST", "ttl": 3, "extra_junk": "malicious_payload", "attack": True}
        goal = payload_to_goal(payload)
        assert goal is not None
        assert goal.ttl == 3

    def test_schema_for_and_legal_args_boundary(self) -> None:
        """Test legal_args and schema_for with empty, unknown, and edge case kinds."""
        from genesis.strategy.law_schema import (
            _arg_options,
            legal_args,
            schema_for,
        )

        # None should return all standard legal args across kinds
        all_args = legal_args(None)
        assert isinstance(all_args, list)
        assert len(all_args) > 0

        # With mock surface map
        mock_sm = MagicMock()
        mock_sm.cls_to_surface = {"c1": "qu\u1ea3 t\xedm", "c2": "l\xe1 xanh"}
        mapped_args = legal_args(mock_sm)
        assert "qu\u1ea3 t\xedm" in mapped_args
        assert "l\xe1 xanh" in mapped_args

        # _arg_options for surface kinds vs static kinds
        assert _arg_options("UNKNOWN_KIND_XYZ") is None
        assert _arg_options("EAT", None) is None
        assert _arg_options("EAT", mock_sm) == ["l\xe1 xanh", "qu\u1ea3 t\xedm", "CORPSE"]

        # Valid kinds with Traits
        from genesis.traits import Traits
        sample_traits = Traits(2, 2, 2, 2, 2, 2)
        for valid_kind in ("decide", "codex", "oracle", "shift", "hunch"):
            schema = schema_for(sample_traits, valid_kind)
            assert isinstance(schema, dict)
            assert schema.get("type") == "object"
            assert "properties" in schema

        # Invalid kind raises ValueError
        with pytest.raises(ValueError, match="không hợp lệ"):
            schema_for(sample_traits, "completely_invalid_kind")


# ==============================================================================
# 5. Log Cleanup & Pruning Edge Case Stress Testing: genesis.util.log_cleanup
# ==============================================================================

class TestLogCleanupAdversarial:
    """Stress test log pruning against edge cases, protected folders, and malformed names."""

    def test_prune_nonexistent_and_empty_dirs(self) -> None:
        from genesis.util.log_cleanup import prune_run_logs

        # Non-existent directory
        assert prune_run_logs(runs_dir="nonexistent_runs_dir_12345") == []

        # Empty directory
        with tempfile.TemporaryDirectory() as tmp:
            assert prune_run_logs(runs_dir=tmp) == []

    def test_prune_protects_directories_and_foreign_files(self) -> None:
        from genesis.util.log_cleanup import prune_run_logs

        with tempfile.TemporaryDirectory() as tmp:
            tmppath = Path(tmp)

            # Protected subdirectories (e.g. runs/baselines/, runs/open/)
            subdir = tmppath / "baselines"
            subdir.mkdir()
            nested_file = subdir / "42-1789700000.jsonl"
            nested_file.write_text("{}", encoding="utf-8")

            # Protected foreign metadata files
            meta1 = tmppath / "test_inventory.json"
            meta1.write_text("{}", encoding="utf-8")
            meta2 = tmppath / "README.md"
            meta2.write_text("documentation", encoding="utf-8")
            meta3 = tmppath / "summary.csv"
            meta3.write_text("col1,col2", encoding="utf-8")

            # Prune with keep_last=0 (aggressive)
            pruned = prune_run_logs(runs_dir=tmppath, keep_last=0, dry_run=False)
            assert pruned == []

            # Verify files still exist
            assert nested_file.is_file()
            assert meta1.is_file()
            assert meta2.is_file()
            assert meta3.is_file()

    def test_prune_with_max_age_days(self) -> None:
        from genesis.util.log_cleanup import prune_run_logs

        with tempfile.TemporaryDirectory() as tmp:
            tmppath = Path(tmp)
            now = time.time()

            # Create 1 fresh file (1 hour old)
            fresh = tmppath / "fresh-1000.jsonl"
            fresh.write_text("fresh", encoding="utf-8")
            os.utime(fresh, (now - 3600, now - 3600))

            # Create 1 old file (10 days old)
            old = tmppath / "old-2000.jsonl"
            old.write_text("old", encoding="utf-8")
            os.utime(old, (now - 10 * 86400, now - 10 * 86400))

            # Prune with max_age_days=5 (keep_last=50)
            pruned = prune_run_logs(runs_dir=tmppath, keep_last=50, max_age_days=5.0, dry_run=False)
            assert len(pruned) == 1
            assert pruned[0].name == "old-2000.jsonl"
            assert fresh.is_file()
            assert not old.is_file()


# ==============================================================================
# 6. End-to-End Simulation Integration with Subclasses & Duck-typing
# ==============================================================================

class TestSimulationIntegrationWithStrategistExtensions:
    """Verify that extended/subclassed strategists seamlessly integrate into the live simulation tick loop."""

    def test_custom_reflex_subclass_in_tick_loop(self) -> None:
        from genesis.strategist import ReflexStrategist
        from genesis.tick import build_match, tick

        # Custom subclass instrumenting decisions
        decision_count = 0

        class InstrumentedReflex(ReflexStrategist):
            def decide(self, c, world, seen, rng=None, tick_no=0, current=None):
                nonlocal decision_count
                decision_count += 1
                return super().decide(c, world, seen, rng, tick_no, current)

        strat = InstrumentedReflex()
        world, creatures, state, rng = build_match(seed=42)

        # Run 5 simulation ticks
        for t in range(5):
            tick(world, creatures, t, rng, state, laws=None, strategist=strat)

        assert decision_count > 0, "InstrumentedReflex.decide was never invoked during tick loop!"

    def test_duck_typed_strategist_in_tick_loop(self) -> None:
        from genesis.reflex import ActiveGoal, Goal
        from genesis.strategist import Strategist
        from genesis.tick import build_match, tick

        called_ticks: list[int] = []

        class DuckTypedPacer:
            def decide(self, creature, world, creatures, rng, tick_no=0, current=None):
                called_ticks.append(tick_no)
                return ActiveGoal(goal=Goal.REST, target=None, ttl=2)

        pacer = DuckTypedPacer()
        assert isinstance(pacer, Strategist)

        world, creatures, state, rng = build_match(seed=99)
        for t in range(3):
            tick(world, creatures, t, rng, state, laws=None, strategist=pacer)

        assert len(called_ticks) >= 3, "DuckTypedPacer was not called for each creature/tick"

    def test_cli_prune_runs_execution(self) -> None:
        """Verify scripts/prune_runs.py runs cleanly as a CLI entrypoint."""
        res = subprocess.run(
            [sys.executable, "scripts/prune_runs.py", "--dry-run", "--keep", "100"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert res.returncode == 0
        assert "[DRY-RUN]" in res.stdout
        assert "Sẽ xoá" in res.stdout or "Không có file log nào" in res.stdout


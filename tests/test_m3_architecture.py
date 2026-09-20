"""Unit and integration tests for Milestone M3 (Architectural Upgrade & Maintainability).

Tests Features 16-21:
- Feature 16: net/config.py relocation & root net_config.py shim parity
- Feature 17: genesis/strategy/ decomposition & genesis/strategist.py facade re-exports
- Feature 18: genesis/platform.py centralized utilities
- Feature 19: genesis/util/log_cleanup.py & prune_runs.py rotation
- Feature 20: docs/TELEMETRY_CONTRACT.md compliance
- Feature 21: docs/ARCHITECTURAL_ROADMAP.md completeness
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestFeature16NetConfigPackaging:
    """Feature 16: Packaging & Configuration Standardization."""

    def test_net_config_root_shim_exports(self) -> None:
        import net_config
        from net import config

        assert hasattr(net_config, "MATCH_PORT")
        assert hasattr(config, "MATCH_PORT")
        assert net_config.MATCH_PORT == config.MATCH_PORT
        assert net_config.SPECTATE_PORT == config.SPECTATE_PORT
        assert net_config.DEFAULT_HOST == config.DEFAULT_HOST

        # Ensure all core protocol constants are identical
        assert net_config.TICK_MS_DEFAULT == config.TICK_MS_DEFAULT
        assert net_config.LATE_TOLERANCE == config.LATE_TOLERANCE
        assert net_config.MAP_ROTATION == config.MAP_ROTATION
        assert net_config.LAW_NOVELTY_WINDOW == config.LAW_NOVELTY_WINDOW
        assert net_config.MESHY_URL == config.MESHY_URL

    def test_net_init_exposes_config(self) -> None:
        import net
        assert hasattr(net, "config")
        assert net.config.MATCH_PORT == 8000


class TestFeature17StrategistDecomposition:
    """Feature 17: Decompose God Module genesis/strategist.py."""

    def test_facade_re_exports_and_protocol_compliance(self) -> None:
        from genesis.strategist import (
            ARGLESS_KINDS_FOR_TEST,
            SURFACE_KINDS,
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

        assert issubclass(ReflexStrategist, object)
        assert isinstance(ReflexStrategist(), Strategist)
        assert isinstance(RemoteClientStrategist({}), Strategist)
        assert isinstance(LlmStrategist("http://127.0.0.1:8080", []), Strategist)

        # Verify helpers
        assert callable(legal_args)
        assert callable(schema_for)
        assert callable(payload_to_goal)
        assert callable(ctx_to_pairs)
        assert callable(_budget)
        assert callable(_arg_options)
        assert callable(_effect_schema)
        assert callable(_kind_arg_schema)
        assert isinstance(SURFACE_KINDS, frozenset)
        assert isinstance(ARGLESS_KINDS_FOR_TEST, frozenset)

    def test_modular_package_direct_imports(self) -> None:
        from genesis.strategy.base import Strategist as BaseStrategist
        from genesis.strategy.law_schema import legal_args as ls_legal_args
        from genesis.strategy.llm import LlmStrategist as ModularLlm
        from genesis.strategy.reflex import ReflexStrategist as ModularReflex
        from genesis.strategy.remote import RemoteClientStrategist as ModularRemote

        assert isinstance(ModularReflex(), BaseStrategist)
        assert isinstance(ModularRemote({}), BaseStrategist)
        assert isinstance(ModularLlm("http://127.0.0.1:8080", []), BaseStrategist)

        # Ensure schema functions return identical results
        assert ls_legal_args() == ls_legal_args(None)

    def test_payload_to_goal_functionality(self) -> None:
        from genesis.reflex import Goal
        from genesis.strategy.base import payload_to_goal

        assert payload_to_goal(None) is None
        assert payload_to_goal({}) is None
        assert payload_to_goal({"goal": "INVALID", "ttl": 5}) is None

        valid = payload_to_goal({"goal": "REST", "ttl": 3})
        assert valid is not None
        assert valid.goal == Goal.REST
        assert valid.ttl == 3
        assert valid.target is None

        hunt = payload_to_goal({"goal": "HUNT", "ttl": 4, "target": "L2:1"})
        assert hunt is not None
        assert hunt.goal == Goal.HUNT
        assert hunt.target == "L2:1"


class TestFeature18PlatformUtilities:
    """Feature 18: Centralized Platform & Console Utilities."""

    def test_utf8_subprocess_env(self) -> None:
        from genesis.platform import utf8_subprocess_env

        env = utf8_subprocess_env()
        assert env["PYTHONIOENCODING"] == "utf-8"
        assert env["PYTHONUTF8"] == "1"

        # Preserves custom base_env
        base = {"CUSTOM_VAR": "TEST_123"}
        env_custom = utf8_subprocess_env(base)
        assert env_custom["CUSTOM_VAR"] == "TEST_123"
        assert env_custom["PYTHONUTF8"] == "1"

    def test_find_python_executable(self) -> None:
        from genesis.platform import find_python_executable

        exe = find_python_executable()
        assert exe
        assert Path(exe).is_file()
        assert "python" in Path(exe).name.lower()

    def test_configure_console_encoding_safe(self) -> None:
        from genesis.platform import configure_console_encoding

        # Must execute without raising exceptions regardless of terminal state
        configure_console_encoding()


class TestFeature19LogRotation:
    """Feature 19: Automated Log Rotation & Pruning."""

    def test_prune_run_logs_in_temp_directory(self) -> None:
        from genesis.util.log_cleanup import is_run_log_file, prune_run_logs

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create 10 mock run files
            files: list[Path] = []
            for i in range(10):
                p = tmppath / f"42-178970{i:04d}.jsonl"
                p.write_text(f'{{"tick": {i}}}\n', encoding="utf-8")
                # Associate a truth file for i=0
                if i == 0:
                    (tmppath / f"42-178970{i:04d}.truth.json").write_text("{}", encoding="utf-8")
                # Stagger mtime
                os.utime(p, (time.time() - (10 - i) * 100, time.time() - (10 - i) * 100))
                files.append(p)

            # Also create a non-run file that must NOT be pruned
            meta = tmppath / "test_inventory.json"
            meta.write_text("{}", encoding="utf-8")

            # Check is_run_log_file
            assert is_run_log_file(files[0]) is True
            assert is_run_log_file(meta) is False

            # Test dry_run keeping 5 files
            dry_pruned = prune_run_logs(runs_dir=tmppath, keep_last=5, dry_run=True)
            # Expecting 5 oldest jsonl files + 1 truth file = 6 files
            assert len(dry_pruned) == 6
            # Confirm files still exist
            assert files[0].is_file()

            # Test real prune keeping 5 files
            pruned = prune_run_logs(runs_dir=tmppath, keep_last=5, dry_run=False)
            assert len(pruned) == 6
            assert not files[0].is_file()
            assert not (tmppath / "42-1789700000.truth.json").is_file()
            assert meta.is_file()  # protected


class TestFeature20And21Documentation:
    """Features 20 and 21: Documentation deliverables."""

    def test_telemetry_contract_published(self) -> None:
        doc = ROOT / "docs" / "TELEMETRY_CONTRACT.md"
        assert doc.is_file()
        content = doc.read_text(encoding="utf-8")
        assert "CreatureTelemetry" in content
        assert "/v1/spectate" in content
        assert "/v1/spectate/dossier" in content
        assert "schema_version" in content

    def test_architectural_roadmap_published(self) -> None:
        doc = ROOT / "docs" / "ARCHITECTURAL_ROADMAP.md"
        assert doc.is_file()
        content = doc.read_text(encoding="utf-8")
        assert "Phase 1" in content
        assert "Phase 2" in content
        assert "Phase 3" in content
        assert "MatchManager" in content
        assert "WebGPU" in content

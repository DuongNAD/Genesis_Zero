"""Adversarial stress and schema conformance test suite for Milestone M3 Gate.

Empirical verification of:
1. Log Rotation Stress & Directory Immunity:
   - >100 mock JSONL run logs with diverse timestamps (ancient, interleaved, future).
   - Exactly target number of most recent runs are preserved.
   - Paired .truth.json handling.
   - Subdirectory immunity (baselines/, handbooks/, open/, nested directories).
   - Metadata file immunity (test_inventory.json, configs, dotfiles).
   - Read-only file handling and PermissionError resilience.
   - CLI error codes on failure and exit 0 on success.
2. Telemetry Schema Validation:
   - Strict conformance against docs/TELEMETRY_CONTRACT.md.
   - Frame schema, CreatureTelemetry schema, envelope schema.
   - Dossier dual-key compatibility (e/energy, tr/traits, d_tr/dt_traits).
   - Security invariants: zero hidden-law leakage during RUNNING, zero seed exposure.
   - Public event whitelist sanitization.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from genesis.platform import find_python_executable
from genesis.util.log_cleanup import is_run_log_file, prune_run_logs
from net import server, state
from net.match import MatchRunner, Phase, _public_event
from net.telemetry import envelope

# ============================================================================
# Section 1: Log Rotation Stress & Immunity Testing
# ============================================================================


class TestLogRotationStressAndImmunity:
    """Stress testing log rotation logic and verifying strict directory/metadata immunity."""

    def test_log_rotation_120_files_exact_preservation(self) -> None:
        """Create 120 mock run files (>100) with ancient and staggered timestamps.

        Verify:
        - Exactly keep_last (e.g. 35) most recent runs are preserved.
        - Exactly 85 oldest runs are pruned.
        - Paired .truth.json for pruned files are deleted.
        - Paired .truth.json for preserved files remain intact.
        - Subdirectories and metadata files remain completely untouched.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)

            # 1. Setup protected subdirectories with sensitive content
            protected_subdirs = ["baselines", "handbooks", "open", "nested/deep/store"]
            subdir_files: dict[str, bytes] = {}
            for sdir in protected_subdirs:
                pdir = runs_dir / sdir
                pdir.mkdir(parents=True, exist_ok=True)
                for fname in ["record_01.jsonl", "truth.json", "manifest.txt"]:
                    fpath = pdir / fname
                    content = f"PROTECTED SUBDIR CONTENT: {sdir}/{fname}\n".encode("utf-8")
                    fpath.write_bytes(content)
                    subdir_files[str(fpath.relative_to(runs_dir))] = content

            # 2. Setup protected metadata files in root of runs_dir
            meta_inventory = runs_dir / "test_inventory.json"
            meta_inventory_content = b'{"status": "CANONICAL_TEST_INVENTORY", "tests": 1679}'
            meta_inventory.write_bytes(meta_inventory_content)

            meta_summary = runs_dir / "summary.csv"
            meta_summary_content = b"seed,score,status\n42,1.0,PASS\n"
            meta_summary.write_bytes(meta_summary_content)

            dot_hidden = runs_dir / ".hidden_run.jsonl"
            dot_hidden_content = b'{"hidden": true}\n'
            dot_hidden.write_bytes(dot_hidden_content)

            # 3. Create 120 mock run log files with timestamps spanning decades
            # (from ancient 1995 up to current time)
            base_time = 800000000.0  # ~1995
            total_runs = 120
            keep_target = 35
            run_files: list[Path] = []

            for i in range(total_runs):
                # Varied naming styles compliant with Genesis Zero runs
                if i % 3 == 0:
                    filename = f"42-{int(base_time + i * 10000)}.jsonl"
                elif i % 3 == 1:
                    filename = f"m_{i:05d}.jsonl"
                else:
                    filename = f"run_batch_{i:04d}.jsonl"

                p = runs_dir / filename
                p.write_text(f'{{"run_idx": {i}, "tick": 100}}\n', encoding="utf-8")
                # Assign monotonic mtime so index matches recency
                mtime = base_time + i * 10000.0
                os.utime(p, (mtime, mtime))
                run_files.append(p)

                # Pair half the runs with .truth.json
                if i % 2 == 0:
                    truth = runs_dir / f"{p.stem}.truth.json"
                    truth.write_text(f'{{"truth_for": "{p.stem}"}}\n', encoding="utf-8")

            assert len(run_files) == 120

            # 4. Dry-run execution first: verify nothing is deleted
            dry_pruned = prune_run_logs(runs_dir=runs_dir, keep_last=keep_target, dry_run=True)
            # 120 - 35 = 85 jsonl files to delete.
            # Plus truth files for pruned files: exactly half of 85 = 43 truth files (indices 0, 2, ..., 84)
            expected_deleted_count = (120 - keep_target) + len(
                [i for i in range(120 - keep_target) if i % 2 == 0]
            )
            assert len(dry_pruned) == expected_deleted_count
            # Verify no file was actually deleted during dry-run
            assert run_files[0].is_file()
            assert meta_inventory.is_file()

            # 5. Live execution
            actual_pruned = prune_run_logs(runs_dir=runs_dir, keep_last=keep_target, dry_run=False)
            assert len(actual_pruned) == expected_deleted_count

            # 6. Verify exact preservation invariant
            remaining_jsonl = [p for p in runs_dir.iterdir() if is_run_log_file(p)]
            assert len(remaining_jsonl) == keep_target, (
                f"Expected exactly {keep_target} run logs, got {len(remaining_jsonl)}"
            )

            # The 35 most recent runs (indices 85 to 119) MUST still exist
            for i in range(120 - keep_target, 120):
                assert run_files[i].is_file(), f"Expected recent run {run_files[i].name} to be kept"
                if i % 2 == 0:
                    truth = runs_dir / f"{run_files[i].stem}.truth.json"
                    assert truth.is_file(), f"Expected truth {truth.name} to be kept"

            # The 85 oldest runs (indices 0 to 84) MUST be gone
            for i in range(0, 120 - keep_target):
                assert not run_files[i].is_file(), f"Expected old run {run_files[i].name} to be pruned"
                if i % 2 == 0:
                    truth = runs_dir / f"{run_files[i].stem}.truth.json"
                    assert not truth.is_file(), f"Expected truth {truth.name} to be pruned"

            # 7. Verify strict immunity of protected metadata files
            assert meta_inventory.is_file()
            assert meta_inventory.read_bytes() == meta_inventory_content
            assert meta_summary.is_file()
            assert meta_summary.read_bytes() == meta_summary_content
            assert dot_hidden.is_file()
            assert dot_hidden.read_bytes() == dot_hidden_content

            # 8. Verify strict immunity of protected subdirectories and their contents
            for rel_path, expected_bytes in subdir_files.items():
                full_path = runs_dir / rel_path
                assert full_path.is_file(), f"Subdirectory file {rel_path} was corrupted or deleted"
                assert full_path.read_bytes() == expected_bytes, (
                    f"Content mismatch in subdirectory file {rel_path}"
                )

    def test_log_rotation_max_age_override(self) -> None:
        """Verify that max_age_days prunes ancient files even when keep_last would retain them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)
            now = time.time()

            # Create 10 files: 5 files from 30 days ago, 5 files from 1 hour ago
            for i in range(5):
                p = runs_dir / f"ancient_{i:02d}.jsonl"
                p.write_text("{}", encoding="utf-8")
                ancient_time = now - (30 * 86400.0) - (i * 100)
                os.utime(p, (ancient_time, ancient_time))

            for i in range(5):
                p = runs_dir / f"recent_{i:02d}.jsonl"
                p.write_text("{}", encoding="utf-8")
                recent_time = now - 3600.0 - (i * 10)
                os.utime(p, (recent_time, recent_time))

            # Keep last is 20 (larger than total 10 files), but max_age_days is 7
            pruned = prune_run_logs(runs_dir=runs_dir, keep_last=20, max_age_days=7.0)

            # Exactly the 5 ancient files should be pruned
            assert len(pruned) == 5
            pruned_names = {p.name for p in pruned}
            assert pruned_names == {f"ancient_{i:02d}.jsonl" for i in range(5)}

            # Recent files must remain
            remaining = {p.name for p in runs_dir.iterdir() if p.is_file()}
            assert remaining == {f"recent_{i:02d}.jsonl" for i in range(5)}

    def test_log_rotation_read_only_graceful_handling(self) -> None:
        """Verify that read-only files causing PermissionError are handled gracefully without aborting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)
            now = time.time()

            # Create 3 old files
            f1 = runs_dir / "old_01.jsonl"
            f2 = runs_dir / "old_readonly.jsonl"
            f3 = runs_dir / "old_03.jsonl"

            for f, offset in [(f1, 300), (f2, 200), (f3, 100)]:
                f.write_text("{}", encoding="utf-8")
                t = now - 10000.0 + offset
                os.utime(f, (t, t))

            # Make f2 read-only
            f2.chmod(stat.S_IREAD)

            try:
                # Attempt to prune all 3 files (keep_last=0)
                pruned = prune_run_logs(runs_dir=runs_dir, keep_last=0)

                # f1 and f3 must be pruned; f2 failed deletion so it's skipped gracefully
                assert f1 not in runs_dir.iterdir()
                assert f3 not in runs_dir.iterdir()
                assert f2.is_file(), "Read-only file should still exist due to OS permission guard"

                pruned_names = {p.name for p in pruned}
                assert "old_01.jsonl" in pruned_names
                assert "old_03.jsonl" in pruned_names
                assert "old_readonly.jsonl" not in pruned_names
            finally:
                # Re-enable write permissions so tempfile cleanup succeeds on Windows
                f2.chmod(stat.S_IWRITE)

    def test_log_rotation_directory_with_jsonl_suffix_immunity(self) -> None:
        """A directory named 'fake.jsonl/' must never be classified as a run log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)
            fake_dir = runs_dir / "suspicious.jsonl"
            fake_dir.mkdir()
            nested_file = fake_dir / "payload.txt"
            nested_file.write_text("critical nested payload", encoding="utf-8")

            assert is_run_log_file(fake_dir) is False

            pruned = prune_run_logs(runs_dir=runs_dir, keep_last=0)
            assert len(pruned) == 0
            assert fake_dir.is_dir()
            assert nested_file.is_file()

    def test_prune_runs_cli_stress(self) -> None:
        """Adversarial testing of scripts/prune_runs.py CLI behavior and exit codes."""
        py = find_python_executable()
        cli_script = ROOT / "scripts" / "prune_runs.py"

        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)

            # Populate with 15 files
            for i in range(15):
                p = runs_dir / f"m_{i:05d}.jsonl"
                p.write_text("{}", encoding="utf-8")
                t = 1000000.0 + i * 10
                os.utime(p, (t, t))

            # 1. Test --dry-run CLI
            cmd_dry = [py, str(cli_script), "--runs-dir", str(runs_dir), "--keep", "5", "--dry-run"]
            res_dry = subprocess.run(cmd_dry, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_dry.returncode == 0
            assert "[DRY-RUN]" in res_dry.stdout
            assert "10 file log" in res_dry.stdout
            # Ensure files were NOT deleted
            assert len(list(runs_dir.glob("*.jsonl"))) == 15

            # 2. Test actual CLI prune
            cmd_live = [py, str(cli_script), "--runs-dir", str(runs_dir), "--keep", "5"]
            res_live = subprocess.run(cmd_live, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_live.returncode == 0
            assert "Đã xoá 10 file log" in res_live.stdout
            assert len(list(runs_dir.glob("*.jsonl"))) == 5

            # 3. Test empty runs directory
            res_empty = subprocess.run(cmd_live, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_empty.returncode == 0
            assert "0 file cần dọn dẹp" in res_empty.stdout

            # 4. Test non-existent directory -> graceful notice, exit code 0
            cmd_missing = [py, str(cli_script), "--runs-dir", str(runs_dir / "nonexistent_dir")]
            res_missing = subprocess.run(cmd_missing, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_missing.returncode == 0
            assert "không tồn tại" in res_missing.stdout

            # 5. Test unrecognized argument -> non-zero exit code
            cmd_bad_arg = [py, str(cli_script), "--nonexistent-arg"]
            res_bad_arg = subprocess.run(cmd_bad_arg, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_bad_arg.returncode != 0

            # 6. Test invalid type for --keep -> non-zero exit code
            cmd_bad_val = [py, str(cli_script), "--keep", "invalid_not_number"]
            res_bad_val = subprocess.run(cmd_bad_val, capture_output=True, text=True, encoding="utf-8", errors="replace")
            assert res_bad_val.returncode != 0


# ============================================================================
# Section 2: Telemetry Schema Validation (docs/TELEMETRY_CONTRACT.md)
# ============================================================================


class TestTelemetryContractSchemaValidation:
    """Strict empirical validation against docs/TELEMETRY_CONTRACT.md specification."""

    def test_envelope_schema_conformance(self) -> None:
        """Verify envelope(match_id) contains canonical keys and zero sensitive data."""
        env = envelope("m_test_99")
        assert env["schema_version"] == "1.0"
        assert env["match_id"] == "m_test_99"
        # Invariant: No seed or law leakage
        assert "seed" not in env
        assert "laws" not in env
        assert set(env.keys()) == {"schema_version", "match_id"}

    def test_tick_frame_schema_and_types(self) -> None:
        """Verify real-time tick frame emitted by runner.frame conforms to Section 3."""
        runner = MatchRunner(seed=2026, ticks=50, tick_ms=1, log_dir=None)
        runner.stopped = True

        while runner.phase is not Phase.RUNNING:
            runner.advance_phase()
        runner.step()

        # Contract Section 3 top-level keys
        expected_keys = {
            "schema_version",
            "match_id",
            "t",
            "phase",
            "w",
            "h",
            "map",
            "creatures",
            "plants",
            "corpses",
            "terrain_delta",
            "terrain",
            "weather",
            "events",
        }

        # Check frame on tick 1
        frame_1 = runner.frame(1, [])
        assert set(frame_1.keys()) == expected_keys
        assert frame_1["schema_version"] == "1.0"
        assert isinstance(frame_1["match_id"], str)
        assert frame_1["t"] == 1
        assert frame_1["phase"] == "RUNNING"
        assert frame_1["w"] == 24
        assert frame_1["h"] == 24
        assert isinstance(frame_1["map"], str)
        assert isinstance(frame_1["creatures"], list)
        assert isinstance(frame_1["plants"], list)
        assert isinstance(frame_1["corpses"], list)
        assert isinstance(frame_1["weather"], dict)
        assert isinstance(frame_1["events"], list)

        # Section 1 & 3 Invariant: Terrain is sent on tick 0, None on tick > 0
        assert frame_1["terrain"] is None

        frame_0 = runner.frame(0, [])
        assert isinstance(frame_0["terrain"], list)
        assert len(frame_0["terrain"]) == 24
        assert all(isinstance(row, str) and len(row) == 24 for row in frame_0["terrain"])

        # Invariant: Zero seed exposure in public frame
        assert "seed" not in frame_1
        assert "world_seed" not in frame_1

    def test_creature_telemetry_schema_and_types(self) -> None:
        """Verify CreatureTelemetry records in live frame conform strictly to Section 4."""
        runner = MatchRunner(seed=2026, ticks=50, tick_ms=1, log_dir=None)
        runner.stopped = True

        while runner.phase is not Phase.RUNNING:
            runner.advance_phase()
        runner.step()

        frame = runner.frame(1, [])
        creatures = frame["creatures"]
        assert len(creatures) > 0, "Expected living organisms in RUNNING match"

        expected_creature_keys = {
            "id",
            "species",
            "domain",
            "x",
            "y",
            "hp",
            "e",
            "e_max",
            "alive",
            "feral",
            "tr",
            "features",
            "gen",
            "parent_id",
            "lineage",
            "d_tr",
            "age",
        }

        for c in creatures:
            assert set(c.keys()) == expected_creature_keys
            assert isinstance(c["id"], str)
            assert isinstance(c["species"], str)
            # In the contract table, domains are described as CAN, THUY, KHONG,
            # but runtime Domain enum in genesis.domain uses ("CAN", "NUOC", "TROI").
            assert c["domain"] in ("CAN", "NUOC", "TROI", "THUY", "KHONG")
            assert isinstance(c["x"], int) and 0 <= c["x"] < 24
            assert isinstance(c["y"], int) and 0 <= c["y"] < 24
            assert isinstance(c["hp"], (int, float))
            assert isinstance(c["e"], (int, float))
            assert isinstance(c["e_max"], (int, float))
            assert isinstance(c["alive"], bool)
            assert isinstance(c["feral"], bool)
            assert isinstance(c["tr"], list) and len(c["tr"]) == 6
            assert all(isinstance(v, int) for v in c["tr"])
            assert isinstance(c["features"], list)
            assert isinstance(c["gen"], int) and c["gen"] >= 0
            assert c["parent_id"] is None or isinstance(c["parent_id"], str)
            assert isinstance(c["lineage"], str)
            assert isinstance(c["d_tr"], list) and len(c["d_tr"]) == 6
            assert all(isinstance(v, int) for v in c["d_tr"])
            assert isinstance(c["age"], int) and c["age"] >= 0

    def test_dossier_dual_key_compatibility_and_schema(self) -> None:
        """Verify HTTP /v1/spectate/dossier conforms to Section 5 with dual-key compatibility."""
        runner = MatchRunner(seed=2026, ticks=50, tick_ms=1, log_dir=None)
        runner.stopped = True
        state.runner = runner

        while runner.phase is not Phase.RUNNING:
            runner.advance_phase()
        runner.step()

        with TestClient(server.app) as client:
            resp = client.get("/v1/spectate/dossier")
            assert resp.status_code == 200
            data = resp.json()

            # Verify dossier top-level fields
            expected_dossier_keys = {
                "schema_version",
                "match_id",
                "phase",
                "tick",
                "species",
                "creatures",
            }
            assert set(data.keys()) == expected_dossier_keys
            assert data["schema_version"] == "1.0"
            assert data["phase"] == "RUNNING"
            assert data["tick"] == 1

            # Verify species roster
            assert len(data["species"]) > 0
            for sp in data["species"]:
                expected_sp_keys = {
                    "species",
                    "founder_traits",
                    "features",
                    "creatures_count",
                    "alive_count",
                    "max_gen",
                }
                assert set(sp.keys()) == expected_sp_keys
                assert isinstance(sp["founder_traits"], list)

            # Verify dual-key compatibility guarantee on every creature
            assert len(data["creatures"]) > 0
            for c in data["creatures"]:
                # 1. Canonical 'e' vs Legacy 'energy':
                # Note: 'e' is rounded to 1 decimal place via creature_telemetry,
                # while legacy 'energy' preserves raw c.energy float.
                assert "e" in c and "energy" in c
                assert abs(c["e"] - c["energy"]) < 0.1
                assert c["e"] == round(c["energy"], 1)

                # 2. Canonical 'tr' vs Legacy 'traits'
                assert "tr" in c and "traits" in c
                assert c["tr"] == c["traits"]

                # 3. Canonical 'd_tr' vs Legacy 'dt_traits'
                assert "d_tr" in c and "dt_traits" in c
                assert c["d_tr"] == c["dt_traits"]

                # 4. Inferred rules structure
                assert "inferred_rules" in c
                assert isinstance(c["inferred_rules"], list)

    def test_security_hidden_law_masking_during_running(self) -> None:
        """Verify that during RUNNING phase, LAW_FIRED events strictly mask secret laws as '?'."""
        runner = MatchRunner(seed=2026, ticks=50, tick_ms=1, log_dir=None)
        runner.stopped = True

        while runner.phase is not Phase.RUNNING:
            runner.advance_phase()

        # Simulate a LAW_FIRED event
        raw_event = {
            "kind": "LAW_FIRED",
            "creature_id": "L1:0",
            "law_id": "SECRET_POISON_LAW",
            "pos": [12, 14],
            "effect": "INSTANT_DAMAGE_99",
        }

        frame = runner.frame(10, [raw_event])
        public_events = frame["events"]
        assert len(public_events) == 1
        ev = public_events[0]

        # Invariant: law must be "?" during RUNNING
        assert ev["k"] == "LAW_FIRED"
        assert ev["who"] == "L1:0"
        assert ev["law"] == "?"
        assert ev["pos"] == [12, 14]

        # Sensitive attributes must NEVER leak into public event
        assert "law_id" not in ev
        assert "SECRET_POISON_LAW" not in str(ev)
        assert "effect" not in ev
        assert "INSTANT_DAMAGE_99" not in str(ev)

    def test_security_law_disclosure_in_reveal_phase(self) -> None:
        """Verify that during REVEAL phase, LAW_FIRED events disclose the canonical translation."""
        runner = MatchRunner(seed=2026, ticks=50, tick_ms=1, log_dir=None)
        runner.stopped = True

        # Advance to REVEAL phase
        while runner.phase is not Phase.REVEAL:
            runner.advance_phase()

        pub_laws = runner.laws_public()
        assert len(pub_laws) > 0
        first_law = pub_laws[0]
        law_id = first_law["law_id"]
        expected_desc = first_law["vi"]

        raw_event = {
            "kind": "LAW_FIRED",
            "creature_id": "L1:0",
            "law_id": law_id,
            "pos": [5, 5],
        }

        frame = runner.frame(200, [raw_event])
        ev = frame["events"][0]
        assert ev["k"] == "LAW_FIRED"
        assert ev["who"] == "L1:0"
        assert ev["law"] == expected_desc
        assert ev["law"] != "?"

    def test_public_event_whitelist_defense(self) -> None:
        """Verify that hostile / untrusted keys in event dicts are stripped by whitelist."""
        hostile_event = {
            "kind": "MOVE",
            "creature_id": "L1:0",
            "from": [1, 1],
            "to": [1, 2],
            "UNTRUSTED_INTERNAL_SEED": 999999,
            "ADMIN_FLAG": True,
            "DEBUG_TRACE": "MEMORY_LEAK_DETECTION",
        }

        sanitized = _public_event(hostile_event, reveal=False, pub={})
        assert "UNTRUSTED_INTERNAL_SEED" not in sanitized
        assert "ADMIN_FLAG" not in sanitized
        assert "DEBUG_TRACE" not in sanitized
        assert sanitized["k"] == "MOVE"
        assert sanitized["who"] == "L1:0"

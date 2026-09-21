"""Genesis Zero — tests/test_adversarial_m2_packaging.py: Packaging Stress & Tarball Integrity Test Suite.

Empirically challenges the distribution packaging (.whl and .tar.gz), ensuring:
1. Wheel (.whl) total file count exceeds 500.
2. Sdist (.tar.gz) total file count exceeds 700.
3. Critical assets exist in both archives:
   - ecosystem_map.glb, watch3d.html, three.min.js, RenderEngine.js, CreatureController.js, genesis/run.py, net/server.py
4. Zero files in either archive are 0 bytes (non-zero size bound).
5. No foreign artifacts (.agents, tests/, .git, __pycache__) leak into the wheel.
6. Repeated build idempotence and clean_artifacts resilience under dirty and locked file scenarios.
7. Package metadata configuration in pyproject.toml and MANIFEST.in.
"""

from __future__ import annotations

import shutil
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"


def get_wheel_path() -> Path:
    wheels = list(DIST_DIR.glob("*.whl"))
    assert wheels, f"No .whl found in {DIST_DIR}"
    return wheels[0]


def get_sdist_path() -> Path:
    sdists = list(DIST_DIR.glob("*.tar.gz"))
    assert sdists, f"No .tar.gz found in {DIST_DIR}"
    return sdists[0]


class TestWheelIntegrity:
    """Stress tests and verifies binary wheel (.whl) contents and invariants."""

    def test_wheel_exists_and_file_count(self) -> None:
        whl = get_wheel_path()
        with zipfile.ZipFile(whl, "r") as zf:
            members = zf.namelist()
            total_count = len(members)
            assert total_count > 500, f"Wheel file count {total_count} is <= 500 (expected > 500)"

    @pytest.mark.parametrize(
        "expected_path, min_bytes",
        [
            ("web/watch3d.html", 10_000),
            ("web/watch3d.js", 5_000),
            ("web/vendor/three.min.js", 500_000),
            ("web/vendor/SkeletonUtils.js", 1_000),
            ("web/vendor/GLTFLoader.js", 10_000),
            ("web/modules/render/RenderEngine.js", 1_000),
            ("web/modules/render/SceneManager.js", 1_000),
            ("web/modules/render/LightingRig.js", 1_000),
            ("web/modules/render/MaterialLibrary.js", 1_000),
            ("web/modules/render/WeatherAtmosphere.js", 1_000),
            ("web/modules/entities/CreatureController.js", 1_000),
            ("web/modules/entities/CreatureStateMachine.js", 1_000),
            ("web/modules/entities/AnimationDispatcher.js", 1_000),
            ("web/modules/entities/SpatialSynchronizer.js", 1_000),
            ("web/modules/assets/AssetLoader.js", 1_000),
            ("web/modules/assets/AssetCache.js", 1_000),
            ("web/modules/assets/AssetManifest.js", 1_000),
            ("web/modules/simulation/TelemetryClient.js", 1_000),
            ("web/modules/simulation/ReplayBuffer.js", 1_000),
            ("web/modules/simulation/EventBus.js", 1_000),
            ("web/modules/audio/AudioSynthesizer.js", 1_000),
            ("assets/blender_map/ecosystem_map.glb", 5_000_000),
            ("assets/blender_map/ecosystem_map.blend", 5_000_000),
            ("assets/genesis_lizard.glb", 10_000),
            ("assets/genesis_spider.glb", 10_000),
            ("assets/world_256.anmw", 100_000),
            ("assets/map_manifest.json", 100),
            ("genesis/run.py", 1_000),
            ("net/server.py", 1_000),
            ("net_config.py", 400),
        ],
    )
    def test_critical_assets_exist_and_non_zero_in_wheel(self, expected_path: str, min_bytes: int) -> None:
        whl = get_wheel_path()
        with zipfile.ZipFile(whl, "r") as zf:
            info_map = {zi.filename: zi.file_size for zi in zf.infolist()}
            assert expected_path in info_map, f"Critical asset '{expected_path}' missing from wheel!"
            actual_size = info_map[expected_path]
            assert actual_size >= min_bytes, (
                f"Asset '{expected_path}' size ({actual_size} bytes) below threshold ({min_bytes} bytes)!"
            )

    def test_zero_byte_audit_in_wheel(self) -> None:
        """Assert that no file inside the wheel is 0 bytes."""
        whl = get_wheel_path()
        with zipfile.ZipFile(whl, "r") as zf:
            zero_files = [
                zi.filename for zi in zf.infolist()
                if zi.file_size == 0 and not zi.filename.endswith("/")
            ]
            assert len(zero_files) == 0, f"Found 0-byte files in wheel: {zero_files}"

    def test_no_forbidden_leaks_in_wheel(self) -> None:
        """Assert tests, .agents, .git, or dev cache do NOT leak into binary wheel."""
        whl = get_wheel_path()
        with zipfile.ZipFile(whl, "r") as zf:
            members = zf.namelist()
            forbidden = [
                m for m in members
                if ".agents" in m
                or m.startswith("tests/")
                or ".git" in m
                or ".pytest_cache" in m
                or "__pycache__" in m
            ]
            assert len(forbidden) == 0, f"Wheel contains forbidden leaked files: {forbidden[:5]}"


class TestSdistIntegrity:
    """Stress tests and verifies source distribution (.tar.gz) contents and invariants."""

    def test_sdist_exists_and_file_count(self) -> None:
        sdist = get_sdist_path()
        with tarfile.open(sdist, "r:gz") as tf:
            members = tf.getnames()
            total_count = len(members)
            assert total_count > 700, f"Sdist file count {total_count} is <= 700 (expected > 700)"

    @pytest.mark.parametrize(
        "expected_path, min_bytes",
        [
            ("web/watch3d.html", 10_000),
            ("web/vendor/three.min.js", 500_000),
            ("web/vendor/SkeletonUtils.js", 1_000),
            ("web/modules/render/RenderEngine.js", 1_000),
            ("web/modules/entities/CreatureController.js", 1_000),
            ("assets/blender_map/ecosystem_map.glb", 5_000_000),
            ("genesis/run.py", 1_000),
            ("net/server.py", 1_000),
            ("MANIFEST.in", 50),
            ("pyproject.toml", 1_000),
            ("README.md", 500),
            ("LICENSE", 100),
            ("run.bat", 200),
            ("run.sh", 200),
        ],
    )
    def test_critical_assets_exist_and_non_zero_in_sdist(self, expected_path: str, min_bytes: int) -> None:
        sdist = get_sdist_path()
        with tarfile.open(sdist, "r:gz") as tf:
            sdist_members = {m.name: m.size for m in tf.getmembers()}
            # Member paths in sdist start with prefix like 'genesis_zero-1.0.0/'
            exact_target = f"genesis_zero-1.0.0/{expected_path}"
            assert exact_target in sdist_members, f"Critical asset '{exact_target}' missing from sdist!"
            actual_size = sdist_members[exact_target]
            assert actual_size >= min_bytes, (
                f"Asset '{exact_target}' in sdist size ({actual_size} bytes) below threshold ({min_bytes} bytes)!"
            )


    def test_zero_byte_audit_in_sdist(self) -> None:
        """Assert that no regular file inside sdist is 0 bytes."""
        sdist = get_sdist_path()
        with tarfile.open(sdist, "r:gz") as tf:
            zero_files = [
                m.name for m in tf.getmembers()
                if m.isreg() and m.size == 0
            ]
            assert len(zero_files) == 0, f"Found 0-byte regular files in sdist: {zero_files}"

    def test_no_agents_leakage_in_sdist(self) -> None:
        """Assert .agents directory does NOT leak into sdist."""
        sdist = get_sdist_path()
        with tarfile.open(sdist, "r:gz") as tf:
            leaks = [m.name for m in tf.getmembers() if ".agents" in m.name]
            assert len(leaks) == 0, f"Sdist contains forbidden .agents leaks: {leaks}"


class TestBuildAndCleanRobustness:
    """Adversarial stress-testing of build_dist.py clean_artifacts and file-lock behaviors."""

    def test_clean_artifacts_logic_on_dirty_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify clean_artifacts removes dirty files in dist/ and build/ without error."""
        import scripts.build_dist as bd

        # Monkeypatch ROOT to isolated tmp_path
        monkeypatch.setattr(bd, "ROOT", tmp_path)

        dummy_dist = tmp_path / "dist"
        dummy_build = tmp_path / "build"
        dummy_egg = tmp_path / "genesis_zero.egg-info"
        dummy_dist.mkdir(parents=True, exist_ok=True)
        dummy_build.mkdir(parents=True, exist_ok=True)
        dummy_egg.mkdir(parents=True, exist_ok=True)

        dirty_dist_file = dummy_dist / "junk_test_file.tmp"
        dirty_build_file = dummy_build / "temp_cache.bin"
        dirty_egg_file = dummy_egg / "SOURCES.txt"
        dirty_dist_file.write_bytes(b"dirty dist content")
        dirty_build_file.write_bytes(b"dirty build content")
        dirty_egg_file.write_bytes(b"dummy egg")

        assert dirty_dist_file.exists()
        assert dirty_build_file.exists()
        assert dirty_egg_file.exists()

        # Run clean_artifacts in isolated tmp_path
        bd.clean_artifacts()

        # Verify dirty files and directories were removed
        assert not dummy_dist.exists()
        assert not dummy_build.exists()
        assert not dummy_egg.exists()

    def test_clean_artifacts_idempotence(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling clean_artifacts consecutively when dirs are already gone must not raise."""
        import scripts.build_dist as bd

        monkeypatch.setattr(bd, "ROOT", tmp_path)
        bd.clean_artifacts()
        bd.clean_artifacts()  # Should cleanly succeed with zero errors


    def test_file_lock_handling_resilience(self, tmp_path: Path) -> None:
        """Stress-test file lock handling on Windows using shutil.rmtree(ignore_errors=True)."""
        lock_dir = tmp_path / "mock_dist"
        lock_dir.mkdir()
        locked_file = lock_dir / "active_package.whl"
        locked_file.write_bytes(b"simulated wheel in use")

        # Open file with exclusive lock
        with open(locked_file, "r+b") as locked_handle:
            # Invoking rmtree with ignore_errors=True must not raise an unhandled exception
            shutil.rmtree(lock_dir, ignore_errors=True)
            # On Windows, locked file remains while handle is open
            if sys.platform == "win32":
                assert locked_file.exists(), "Locked file was unexpectedly deleted while open!"

        # Once handle is closed, removal succeeds completely
        shutil.rmtree(lock_dir, ignore_errors=True)
        assert not lock_dir.exists(), "Directory should be cleaned after file handle closure!"


class TestPackagingConfigurationContracts:
    """Verifies pyproject.toml and MANIFEST.in configuration contracts."""

    def test_manifest_in_contracts(self) -> None:
        manifest_path = ROOT / "MANIFEST.in"
        assert manifest_path.exists(), "MANIFEST.in is missing!"
        content = manifest_path.read_text(encoding="utf-8")
        assert "graft web" in content, "MANIFEST.in missing 'graft web'"
        assert "graft assets" in content, "MANIFEST.in missing 'graft assets'"

    def test_pyproject_package_data_contracts(self) -> None:
        pyproject_path = ROOT / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml is missing!"
        content = pyproject_path.read_text(encoding="utf-8")
        assert 'include = ["genesis*", "net*", "client*", "web*", "assets*"]' in content
        assert '"*"' in content
        assert '"web/**/*"' in content or '"assets/**/*"' in content

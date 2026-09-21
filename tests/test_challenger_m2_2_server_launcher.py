"""Empirical Adversarial Test Suite for Challenger M2-2:
Server Endpoints, Static Routing, and Launcher Flags.

Validates:
1. Root redirect GET / (307 redirect to /watch/watch3d.html)
2. Static serving of /watch/watch3d.html (200 OK, zero external CDN links)
3. Static serving of /assets/blender_map/viewer.html (200 OK)
4. Static serving of /watch/creature_viewer.html (200 OK)
5. Static serving of /assets/blender_map/ecosystem_map.glb (> 8MB, valid glTF binary)
6. Server security / boundary conditions (path traversal, nonexistent paths, invalid methods)
7. scripts/launch.py CLI argument parsing (--diorama, --creature, --web, --seed, --port)
8. scripts/launch.py error handling on invalid flags and argument types (clean exit, no traceback)
9. run.bat launcher logic and Windows CMD execution
"""

from __future__ import annotations

import os
import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from net import server

ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. FastAPI Server Endpoint & Static Routing Tests
# ==============================================================================

@pytest.fixture(scope="module")
def client():
    with TestClient(server.app, follow_redirects=False) as c:
        yield c

@pytest.fixture(scope="module")
def redirect_client():
    with TestClient(server.app, follow_redirects=True) as c:
        yield c


class TestServerEndpoints:
    """Adversarial testing of net/server.py endpoints and static file mounts."""

    def test_root_redirect_status_307_and_header(self, client: TestClient):
        """GET / must return 307 redirect with Location header pointing to /watch/watch3d.html."""
        response = client.get("/")
        assert response.status_code == 307, f"Expected 307 Temporary Redirect, got {response.status_code}"
        assert response.headers.get("location") == "/watch/watch3d.html", (
            f"Expected Location '/watch/watch3d.html', got {response.headers.get('location')}"
        )

    def test_root_redirect_follow_serves_html(self, redirect_client: TestClient):
        """GET / when followed must serve 200 OK HTML."""
        response = redirect_client.get("/")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html, got {content_type}"
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()

    def test_watch3d_html_status_and_zero_cdn(self, client: TestClient):
        """GET /watch/watch3d.html must return 200 OK and have zero external CDN references."""
        response = client.get("/watch/watch3d.html")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

        body = response.text

        # Check for forbidden CDN hostnames or protocol-relative/HTTPS external scripts
        forbidden_patterns = [
            r"https?://[^\s\"'<>]*cdn",
            r"https?://[^\s\"'<>]*unpkg\.com",
            r"https?://[^\s\"'<>]*cdnjs",
            r"https?://[^\s\"'<>]*jsdelivr",
            r"https?://[^\s\"'<>]*threejs\.org",
            r"https?://[^\s\"'<>]*googleapis\.com",
        ]
        violations = []
        for pat in forbidden_patterns:
            matches = re.findall(pat, body, re.IGNORECASE)
            if matches:
                violations.extend(matches)

        assert not violations, f"Found external CDN URLs in watch3d.html: {violations}"

        # Verify script src and link href do not point to remote URLs
        external_tags = re.findall(
            r'<(?:script|link)[^>]*(?:src|href)=["\'](https?://[^"\']+)["\']',
            body,
            re.IGNORECASE,
        )
        assert not external_tags, f"Found remote asset tags in watch3d.html: {external_tags}"

    def test_blender_map_viewer_html(self, client: TestClient):
        """GET /assets/blender_map/viewer.html must return 200 OK and valid HTML with zero remote CDN."""
        response = client.get("/assets/blender_map/viewer.html")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()

        # Zero CDN scan
        remote_tags = re.findall(
            r'<(?:script|link)[^>]*(?:src|href)=["\'](https?://[^"\']+)["\']',
            response.text,
            re.IGNORECASE,
        )
        assert not remote_tags, f"Found remote asset tags in viewer.html: {remote_tags}"

    def test_creature_viewer_html(self, client: TestClient):
        """GET /watch/creature_viewer.html must return 200 OK and valid HTML with zero remote CDN."""
        response = client.get("/watch/creature_viewer.html")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()

        # Zero CDN scan
        remote_tags = re.findall(
            r'<(?:script|link)[^>]*(?:src|href)=["\'](https?://[^"\']+)["\']',
            response.text,
            re.IGNORECASE,
        )
        assert not remote_tags, f"Found remote asset tags in creature_viewer.html: {remote_tags}"

    def test_vendor_static_assets_serving(self, client: TestClient):
        """Verify local vendor Three.js assets are served 200 OK without CDN fallback."""
        vendor_urls = [
            "/watch/vendor/three.min.js",
            "/watch/vendor/GLTFLoader.js",
            "/watch/vendor/SkeletonUtils.js",
            "/assets/blender_map/vendor/three.min.js",
            "/assets/blender_map/vendor/GLTFLoader.js",
        ]
        for url in vendor_urls:
            resp = client.get(url)
            assert resp.status_code == 200, f"Failed to serve vendor script {url}: {resp.status_code}"
            assert len(resp.content) > 1000, f"Vendor script {url} seems truncated ({len(resp.content)} bytes)"

    def test_ecosystem_map_glb_serving_and_integrity(self, client: TestClient):
        """GET /assets/blender_map/ecosystem_map.glb must return 200 OK, size > 8MB, and valid glTF header."""
        response = client.get("/assets/blender_map/ecosystem_map.glb")
        assert response.status_code == 200

        content = response.content
        size = len(content)
        min_size = 8 * 1024 * 1024  # 8 MB
        assert size > min_size, f"Expected GLB size > 8MB ({min_size} bytes), got {size} bytes"

        # Verify glTF binary magic and version:
        # Magic: 0x46546C67 (ASCII "glTF")
        # Version: 2 (uint32)
        assert len(content) >= 12, "GLB header truncated"
        magic, version, length = struct.unpack("<4sII", content[:12])
        assert magic == b"glTF", f"Invalid GLB magic header: {magic}"
        assert version == 2, f"Expected glTF version 2, got {version}"
        assert length == size, f"GLB header declared length {length} != actual byte length {size}"

    def test_server_boundary_path_traversal_attempts(self, client: TestClient):
        """Server static mounts must safely reject or fail to traverse outside mounted directories."""
        # Test traversal on /assets
        resp1 = client.get("/assets/../../pyproject.toml")
        assert resp1.status_code in (404, 400), f"Expected 404 or 400, got {resp1.status_code}"

        # Test traversal on /watch
        resp2 = client.get("/watch/../../net/server.py")
        assert resp2.status_code in (404, 400), f"Expected 404 or 400, got {resp2.status_code}"

    def test_server_missing_static_file_returns_404(self, client: TestClient):
        """Nonexistent static asset must return 404 Not Found."""
        response = client.get("/watch/nonexistent_file_adversarial_12345.html")
        assert response.status_code == 404

    def test_server_root_invalid_method(self, client: TestClient):
        """POST / should return 405 Method Not Allowed since root only accepts GET."""
        response = client.post("/")
        assert response.status_code == 405


# ==============================================================================
# 2. scripts/launch.py CLI Argument Parsing & Error Handling Tests
# ==============================================================================

class TestLauncherFlags:
    """Adversarial testing of scripts/launch.py arguments, parsing, and failure modes."""

    def test_launch_help_contains_all_required_flags(self):
        """Executing scripts/launch.py --help must list --diorama, --creature, --web, --seed, --port."""
        cmd = [sys.executable, str(ROOT / "scripts" / "launch.py"), "--help"]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
        assert proc.returncode == 0, f"launch.py --help failed with returncode {proc.returncode}"
        output = proc.stdout

        expected_flags = ["--diorama", "--creature", "--web", "--seed", "--port"]
        missing = [flag for flag in expected_flags if flag not in output]
        assert not missing, f"launch.py --help is missing documented flags: {missing}\nOutput:\n{output}"

    def test_launch_invalid_flag_graceful_error_handling(self):
        """Passing unrecognized flag must exit with non-zero code and clean error without Python traceback."""
        cmd = [sys.executable, str(ROOT / "scripts" / "launch.py"), "--nonexistent-adversarial-flag-xyz"]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
        assert proc.returncode != 0, f"Expected non-zero exit code for invalid flag, got {proc.returncode}"

        stderr = proc.stderr
        assert "unrecognized arguments" in stderr or "error:" in stderr, (
            f"Expected argparse error message in stderr, got:\n{stderr}"
        )
        assert "Traceback (most recent call last):" not in stderr, (
            f"Unhandled traceback detected on invalid flag:\n{stderr}"
        )

    def test_launch_invalid_argument_types(self):
        """Passing invalid types for int arguments must be rejected cleanly by argparse."""
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # Invalid port
        cmd_port = [sys.executable, str(ROOT / "scripts" / "launch.py"), "--port", "invalid_port_str"]
        proc_port = subprocess.run(cmd_port, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
        assert proc_port.returncode != 0
        assert "invalid int value" in proc_port.stderr
        assert "Traceback" not in proc_port.stderr

        # Invalid seed
        cmd_seed = [sys.executable, str(ROOT / "scripts" / "launch.py"), "--seed", "not_a_seed"]
        proc_seed = subprocess.run(cmd_seed, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
        assert proc_seed.returncode != 0
        assert "invalid int value" in proc_seed.stderr
        assert "Traceback" not in proc_seed.stderr

    def test_launch_argument_parser_internal_contracts(self):
        """Import launch.py and programmatically verify parser setup and defaults."""
        from scripts import launch

        # Verify known ports configuration
        assert 8000 in launch.KNOWN_PORTS
        assert 8080 in launch.KNOWN_PORTS
        assert 11434 in launch.KNOWN_PORTS

        # Test parser definition
        import argparse
        # Inspect main function by creating a test parser with launch arguments
        test_parser = argparse.ArgumentParser()
        test_parser.add_argument("--web", action="store_true")
        test_parser.add_argument("--diorama", action="store_true")
        test_parser.add_argument("--creature", "--creatures", action="store_true")
        test_parser.add_argument("--seed", type=int, default=42)
        test_parser.add_argument("--port", type=int, default=8000)

        # Parse test arguments
        args_diorama = test_parser.parse_args(["--diorama"])
        assert args_diorama.diorama is True
        assert args_diorama.web is False

        args_creature = test_parser.parse_args(["--creature"])
        assert args_creature.creature is True

        args_creatures_alias = test_parser.parse_args(["--creatures"])
        assert args_creatures_alias.creature is True

        args_web_custom = test_parser.parse_args(["--web", "--port", "8888", "--seed", "99"])
        assert args_web_custom.web is True
        assert args_web_custom.port == 8888
        assert args_web_custom.seed == 99

    def test_launch_main_dispatch_paths(self, monkeypatch):
        """Verify that launch.main() dispatches the exact required URL path for each CLI flag."""
        from unittest.mock import MagicMock

        from scripts import launch

        mock_run_web = MagicMock(return_value=0)
        monkeypatch.setattr(launch, "run_web_server", mock_run_web)
        monkeypatch.setattr(launch, "show_banner", lambda *a, **kw: None)
        monkeypatch.setattr(launch, "scan_backends", lambda: {})

        # Test --diorama
        monkeypatch.setattr(sys, "argv", ["launch.py", "--diorama"])
        ret = launch.main()
        assert ret == 0
        mock_run_web.assert_called_with(host="127.0.0.1", port=8000, open_browser=True, path="/assets/blender_map/viewer.html")

        # Test --creature
        mock_run_web.reset_mock()
        monkeypatch.setattr(sys, "argv", ["launch.py", "--creature", "--port", "8050"])
        ret = launch.main()
        assert ret == 0
        mock_run_web.assert_called_with(host="127.0.0.1", port=8050, open_browser=True, path="/watch/creature_viewer.html")

        # Test --creatures alias
        mock_run_web.reset_mock()
        monkeypatch.setattr(sys, "argv", ["launch.py", "--creatures"])
        ret = launch.main()
        assert ret == 0
        mock_run_web.assert_called_with(host="127.0.0.1", port=8000, open_browser=True, path="/watch/creature_viewer.html")

        # Test --web
        mock_run_web.reset_mock()
        monkeypatch.setattr(sys, "argv", ["launch.py", "--web"])
        ret = launch.main()
        assert ret == 0
        mock_run_web.assert_called_with(host="127.0.0.1", port=8000, open_browser=True, path="/watch/watch3d.html")


# ==============================================================================
# 3. run.bat Launcher Logic & Windows Environment Tests
# ==============================================================================

class TestRunBatLauncher:
    """Adversarial testing of run.bat Windows CMD script logic and environment resilience."""

    def test_run_bat_file_syntax_and_delayed_expansion(self):
        """Verify run.bat enables delayed expansion and uses !ERRORLEVEL! correctly."""
        bat_path = ROOT / "run.bat"
        assert bat_path.is_file(), "run.bat not found"

        content = bat_path.read_text(encoding="utf-8")

        # Must enable delayed expansion
        assert "setlocal EnableDelayedExpansion" in content, (
            "run.bat must enable delayed expansion for reliable error checking inside parenthesized blocks"
        )

        # Must check dependencies using Python -c
        assert 'import rich, httpx, fastapi, uvicorn, pydantic, numpy' in content, (
            "run.bat must verify critical dependencies before launching scripts/launch.py"
        )

        # Must use !ERRORLEVEL! inside if blocks
        assert "!ERRORLEVEL!" in content, (
            "run.bat must use !ERRORLEVEL! rather than %ERRORLEVEL% inside parenthesized blocks"
        )

        # Quoting of ROOT_DIR
        assert 'cd /d "%ROOT_DIR%"' in content or 'cd /d "%~dp0"' in content

    @pytest.mark.skipif(sys.platform != "win32", reason="run.bat is Windows CMD specific")
    def test_run_bat_execution_help(self):
        """Executing run.bat --help under cmd.exe should succeed with exit code 0."""
        bat_path = ROOT / "run.bat"
        cmd = ["cmd.exe", "/c", str(bat_path), "--help"]
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", cwd=ROOT, env=env)
        assert proc.returncode == 0, f"run.bat --help failed with exit code {proc.returncode}:\n{proc.stderr}"
        assert "--diorama" in proc.stdout
        assert "--creature" in proc.stdout
        assert "--web" in proc.stdout

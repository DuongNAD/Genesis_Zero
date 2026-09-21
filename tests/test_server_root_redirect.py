"""Tests for net/server.py root route redirect and static asset mounts."""

from __future__ import annotations

from fastapi.testclient import TestClient

from net import server


def test_server_root_redirect():
    """Verify GET / returns a redirect response to /watch/watch3d.html."""
    with TestClient(server.app, follow_redirects=False) as client:
        response = client.get("/")
        assert response.status_code in (301, 302, 307), f"Unexpected status: {response.status_code}"
        assert response.headers["location"] == "/watch/watch3d.html"


def test_server_root_redirect_follow():
    """Verify GET / when following redirects successfully serves watch3d.html."""
    with TestClient(server.app, follow_redirects=True) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text


def test_server_static_mounts():
    """Verify static mounts /watch and /assets serve existing files."""
    with TestClient(server.app) as client:
        resp_watch = client.get("/watch/watch3d.html")
        assert resp_watch.status_code == 200

        resp_creatures = client.get("/watch/creature_viewer.html")
        assert resp_creatures.status_code == 200

        resp_assets = client.get("/assets/blender_map/viewer.html")
        assert resp_assets.status_code == 200

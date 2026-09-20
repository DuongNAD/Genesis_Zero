"""Tests for Milestone 3: CI/CD Modernization & Containerization Optimization.

Verifies:
1. .github/workflows/ci.yml: Modern 7-stage pipeline with OS/Python matrix and uv caching.
2. .github/workflows/test.yml: Legacy workflow decoupled from push/PR to prevent conflicts.
3. .gitlab-ci.yml: Production-grade 5-stage GitLab CI pipeline.
4. Dockerfile: Hardened multi-stage build with python:3.11-slim, non-root user genesis,
              pre-created volumes, curl, healthcheck, and uvicorn entrypoint.
5. .dockerignore: Proper exclusion rules.
6. docker-compose.yml: match-server and mock-llm service orchestration.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_github_actions_ci_workflow_structure():
    """Verify modern 7-stage GitHub Actions workflow structure and configuration."""
    ci_file = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_file.is_file(), "ci.yml must exist under .github/workflows/"

    content = ci_file.read_text(encoding="utf-8")

    # PyYAML safe_load validation
    import yaml
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "ci.yml must parse into a valid YAML dictionary"
    jobs = data.get("jobs", {})
    assert isinstance(jobs, dict), "ci.yml must contain a 'jobs' mapping"

    # 1. Triggers
    assert "'on':" in content or '"on":' in content, "ci.yml trigger key 'on' must be quoted for YAML 1.1 compatibility"
    assert "push:" in content, "Workflow must trigger on push"
    assert "pull_request:" in content, "Workflow must trigger on pull_request"
    assert "workflow_dispatch:" in content, "Workflow must support workflow_dispatch"

    # 2. Stages / Jobs
    required_stages = [
        "lint",
        "typecheck",
        "security",
        "matrix-test",
        "coverage",
        "smoke",
        "docker-build",
    ]
    for stage in required_stages:
        assert stage in jobs, f"Workflow jobs dictionary must define job '{stage}'"


    # 3. Matrix specification: OS & Python versions
    assert "ubuntu-latest" in content, "Matrix must include ubuntu-latest"
    assert "windows-latest" in content, "Matrix must include windows-latest"
    assert "macos-latest" in content, "Matrix must include macos-latest"
    assert '"3.11"' in content or "'3.11'" in content or "3.11" in content
    assert '"3.12"' in content or "'3.12'" in content or "3.12" in content

    # 4. Dependency caching with uv
    assert "astral-sh/setup-uv" in content, "Must use astral-sh/setup-uv"
    assert "enable-cache: true" in content, "Must enable uv dependency caching"

    # 5. Core execution commands
    assert "ruff check genesis net tests scripts client tools" in content, "Lint job must check specified packages"
    assert "mypy genesis net client" in content, "Typecheck job must verify genesis, net, client"
    assert "python scripts/ci_quick.py" in content, "Matrix test must run fast release contracts"
    assert "pytest -q" in content, "Matrix test must run pytest suite"
    assert "--cov-fail-under=90.0" in content, "Coverage job must enforce 90.0% threshold"
    assert "uv audit" in content, "Security audit must invoke uv audit"
    assert "python scripts/ci_smoke.py" in content, "Smoke test must execute ci_smoke.py"
    assert "/v1/healthz" in content, "Docker verification must check /v1/healthz"


def test_github_actions_test_legacy_decoupled():
    """Verify legacy test.yml workflow does not trigger conflicts on push/PR."""
    test_file = ROOT / ".github" / "workflows" / "test.yml"
    assert test_file.is_file(), "test.yml must exist"

    content = test_file.read_text(encoding="utf-8")
    # Verify push and pull_request triggers are not active
    lines = [line.strip() for line in content.splitlines()]
    assert "push:" not in lines, "Legacy test.yml should not trigger on push (handled by ci.yml)"
    assert "pull_request:" not in lines, "Legacy test.yml should not trigger on PR (handled by ci.yml)"
    assert "workflow_dispatch:" in lines, "Legacy test.yml should allow manual workflow_dispatch"


def test_gitlab_ci_pipeline_stages():
    """Verify GitLab CI configuration defines all 5 required stages."""
    gitlab_file = ROOT / ".gitlab-ci.yml"
    assert gitlab_file.is_file(), ".gitlab-ci.yml must exist in repository root"

    content = gitlab_file.read_text(encoding="utf-8")

    import yaml
    data = yaml.safe_load(content)
    assert isinstance(data, dict), ".gitlab-ci.yml must parse into a dictionary"
    assert data.get("stages") == ["lint", "typecheck", "test", "security", "build"], (
        f"Unexpected stages in .gitlab-ci.yml: {data.get('stages')}"
    )

    for stage in ["lint", "typecheck", "test", "security", "build"]:
        assert re.search(rf"-\s+['\"]?{stage}['\"]?", content), f"Stage '{stage}' must be in .gitlab-ci.yml stages"


    assert "ruff check genesis net tests scripts client tools" in content
    assert "mypy genesis net client" in content
    assert "python scripts/ci_quick.py" in content
    assert "--cov-fail-under=90.0" in content
    assert "uv audit" in content
    assert "docker build" in content


def test_dockerfile_multi_stage_and_security_hardening():
    """Verify Dockerfile multi-stage build and security specifications."""
    df_file = ROOT / "Dockerfile"
    assert df_file.is_file(), "Dockerfile must exist in repository root"

    content = df_file.read_text(encoding="utf-8")

    # Multi-stage with python:3.11-slim
    assert "FROM python:3.11-slim AS builder" in content, "Must declare builder stage with python:3.11-slim"
    assert "FROM python:3.11-slim AS runtime" in content, "Must declare runtime stage with python:3.11-slim"

    # uv in builder
    assert "astral-sh/uv" in content, "Builder stage must leverage uv"
    assert "uv venv" in content, "Builder stage must create virtualenv with uv"

    # Pre-created runtime directories
    for dir_path in ["/app/runs", "/app/data/mesh_cache", "/app/data/models"]:
        assert dir_path in content, f"Must pre-create directory {dir_path}"

    # Non-root user genesis UID 1000 and consolidated layer copy
    assert "groupadd -g 1000 genesis" in content, "Must create group genesis with GID 1000"
    assert "useradd -u 1000 -g genesis" in content, "Must create user genesis with UID 1000"
    assert "COPY --chown=genesis:genesis . /app" in content, "Must copy application with non-root ownership in single layer"
    assert "chown -R genesis:genesis /app/runs" in content, "Must ensure pre-created volume directories are owned by genesis"
    assert "USER genesis" in content, "Must switch to USER genesis"

    # Standard non-editable wheel install
    assert "uv pip install --no-cache --no-deps ." in content, "Must use standard wheel install"
    assert "-e ." not in content, "Must not use editable install in builder stage"

    # curl installed
    assert "curl" in content, "Runtime stage must install curl"

    # Port 8000 exposed
    assert "EXPOSE 8000" in content, "Must expose port 8000"

    # HEALTHCHECK pinging /v1/healthz
    assert "HEALTHCHECK" in content, "Must declare HEALTHCHECK"
    assert "/v1/healthz" in content, "Healthcheck must probe /v1/healthz"

    # Uvicorn entrypoint
    assert 'CMD ["uvicorn", "net.server:app", "--host", "0.0.0.0", "--port", "8000"]' in content, (
        "CMD must run uvicorn net.server:app on 0.0.0.0:8000"
    )


def test_dockerignore_exclusions():
    """Verify .dockerignore contains clean exclusions for repository cleanliness and secrets."""
    dign_file = ROOT / ".dockerignore"
    assert dign_file.is_file(), ".dockerignore must exist in repository root"

    content = dign_file.read_text(encoding="utf-8")

    required_patterns = [
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "runs/*.jsonl",
        ".agents",
        "renders",
        ".env",
        ".env.*",
        "!.env.example",
        "*.log",
        "scratch/",
    ]
    for pattern in required_patterns:
        assert pattern in content, f"Pattern '{pattern}' must be present in .dockerignore"


def test_docker_compose_services():
    """Verify docker-compose.yml defines match-server and mock-llm with required bindings."""
    dc_file = ROOT / "docker-compose.yml"
    assert dc_file.is_file(), "docker-compose.yml must exist in repository root"

    content = dc_file.read_text(encoding="utf-8")

    import yaml
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "docker-compose.yml must parse into a dictionary"
    services = data.get("services", {})
    assert "match-server" in services, "match-server must be defined in services"
    assert "mock-llm" in services, "mock-llm must be defined in services"

    # Service definitions
    assert "match-server:" in content, "docker-compose.yml must define match-server service"
    assert "mock-llm:" in content, "docker-compose.yml must define mock-llm service"

    # Port mappings
    assert "8000:8000" in content, "match-server must map port 8000:8000"
    assert services["match-server"].get("ports") == ["8000:8000"]

    # Environment
    assert "GENESIS_LLM_URL=http://mock-llm:8099" in content, (
        "match-server must set GENESIS_LLM_URL to mock-llm"
    )

    # Volume mounts
    assert "./data/mesh_cache:/app/data/mesh_cache" in content, "Must mount mesh_cache volume"
    assert "./runs:/app/runs" in content, "Must mount runs volume"

    # Container networking host binding
    mock_cmd = services["mock-llm"].get("command", [])
    assert "--host" in mock_cmd and "0.0.0.0" in mock_cmd, (
        "mock-llm command must pass --host 0.0.0.0 for cross-container reachability"
    )


def test_fake_model_server_configurable_host():
    """Verify fake_model_server.py CLI supports --host binding defaulting to 127.0.0.1."""
    fms_file = ROOT / "scripts" / "fake_model_server.py"
    assert fms_file.is_file(), "fake_model_server.py must exist under scripts/"
    content = fms_file.read_text(encoding="utf-8")

    assert "--host" in content, "fake_model_server.py must define --host argument"
    assert 'default="127.0.0.1"' in content, "fake_model_server.py --host must default to 127.0.0.1"
    assert "HTTPServer((a.host, a.port), Handler)" in content, (
        "fake_model_server.py must bind HTTPServer to (a.host, a.port)"
    )


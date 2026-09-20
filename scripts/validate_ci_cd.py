#!/usr/bin/env python3
"""Validation script for Genesis Zero CI/CD and Containerization artifacts.

Validates:
1. .github/workflows/ci.yml (7-stage pipeline, matrix, uv caching, coverage, smoke, security, docker)
2. .github/workflows/test.yml (no conflicting push/PR triggers)
3. .gitlab-ci.yml (stages: lint, typecheck, test, security, build)
4. Dockerfile (multi-stage python:3.11-slim, uv builder, non-root user genesis UID 1000,
              pre-created directories, curl, healthcheck /v1/healthz, uvicorn entrypoint)
5. .dockerignore (proper exclusions for git, venv, caches, agents, renders)
6. docker-compose.yml (match-server and mock-llm services, ports, environment, volumes)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")



def validate_yaml_syntax(path: Path) -> dict:
    """Validate YAML syntax using PyYAML safe_load if available, or basic structural checks."""
    content = path.read_text(encoding="utf-8")
    try:
        import yaml
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict in {path}, got {type(data)}")
        return data
    except ImportError:
        # Minimalist fallback parser if yaml is not yet installed
        print(f"[WARN] PyYAML not installed; falling back to structural check for {path.name}")
        lines = content.splitlines()
        assert len(lines) > 5, f"{path.name} is too short"
        return {"raw_lines": lines}


def validate_ci_workflow() -> None:
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), f"Missing {ci_path}"
    content = ci_path.read_text(encoding="utf-8")
    data = validate_yaml_syntax(ci_path)

    # 1. Triggers
    assert "'on':" in content or '"on":' in content, "Workflow must quote 'on' key for YAML 1.1 compatibility"
    assert "push:" in content
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content

    # 2. 7 Stages / Jobs verification
    required_jobs = ["lint", "typecheck", "security", "matrix-test", "coverage", "smoke", "docker-build"]
    for job in required_jobs:
        assert f"  {job}:" in content or f"    {job}:" in content or (isinstance(data.get("jobs"), dict) and job in data["jobs"]), f"Missing job '{job}' in ci.yml"

    # 3. Matrix verification
    assert "ubuntu-latest" in content
    assert "windows-latest" in content
    assert "macos-latest" in content
    assert '"3.11"' in content or "'3.11'" in content or "3.11" in content
    assert '"3.12"' in content or "'3.12'" in content or "3.12" in content

    # 4. Dependency caching with uv
    assert "astral-sh/setup-uv" in content
    assert "enable-cache: true" in content

    # 5. Commands
    assert "ruff check genesis net tests scripts client tools" in content
    assert "mypy genesis net client" in content
    assert "python scripts/ci_quick.py" in content
    assert "pytest -q" in content
    assert "--cov-fail-under=90.0" in content
    assert "uv audit" in content
    assert "python scripts/ci_smoke.py" in content
    assert "docker" in content
    assert "/v1/healthz" in content

    print("✓ .github/workflows/ci.yml: All 7 stages and requirements verified.")


def validate_legacy_test_workflow() -> None:
    test_path = ROOT / ".github" / "workflows" / "test.yml"
    assert test_path.exists(), f"Missing {test_path}"
    content = test_path.read_text(encoding="utf-8")
    # Verify no conflicting auto triggers on push/PR with ci.yml
    assert "push:" not in content or "#" in content.split("push:")[0].splitlines()[-1]
    assert "workflow_dispatch:" in content
    print("✓ .github/workflows/test.yml: Confirmed no conflicting triggers with ci.yml.")


def validate_gitlab_ci() -> None:
    gitlab_path = ROOT / ".gitlab-ci.yml"
    assert gitlab_path.exists(), f"Missing {gitlab_path}"
    content = gitlab_path.read_text(encoding="utf-8")
    validate_yaml_syntax(gitlab_path)

    # Stages
    for stage in ["lint", "typecheck", "test", "security", "build"]:
        assert f"- {stage}" in content or f"- '{stage}'" in content, f"Missing stage '{stage}' in .gitlab-ci.yml"

    assert "ruff check genesis net tests scripts client tools" in content
    assert "mypy genesis net client" in content
    assert "uv audit" in content
    assert "--cov-fail-under=90.0" in content
    assert "docker build" in content

    print("✓ .gitlab-ci.yml: 5-stage production pipeline verified.")


def validate_dockerfile() -> None:
    df_path = ROOT / "Dockerfile"
    assert df_path.exists(), f"Missing {df_path}"
    content = df_path.read_text(encoding="utf-8")

    # Multi-stage with python:3.11-slim
    assert "FROM python:3.11-slim AS builder" in content
    assert "FROM python:3.11-slim AS runtime" in content

    # uv builder
    assert "astral-sh/uv" in content
    assert "uv venv" in content

    # Non-editable wheel install
    assert "uv pip install --no-cache --no-deps ." in content
    assert "-e ." not in content

    # Pre-created directories
    assert "/app/runs" in content
    assert "/app/data/mesh_cache" in content
    assert "/app/data/models" in content

    # Non-root user genesis UID 1000 and consolidated layer copy
    assert "groupadd -g 1000 genesis" in content
    assert "useradd -u 1000 -g genesis" in content
    assert "COPY --chown=genesis:genesis . /app" in content
    assert "USER genesis" in content

    # curl installed
    assert "curl" in content

    # Port 8000
    assert "EXPOSE 8000" in content

    # Healthcheck /v1/healthz
    assert "HEALTHCHECK" in content
    assert "/v1/healthz" in content

    # Entrypoint/CMD uvicorn net.server:app
    assert 'CMD ["uvicorn", "net.server:app", "--host", "0.0.0.0", "--port", "8000"]' in content

    print("✓ Dockerfile: Multi-stage, non-root user, healthcheck, and entrypoint verified.")


def validate_dockerignore() -> None:
    dign_path = ROOT / ".dockerignore"
    assert dign_path.exists(), f"Missing {dign_path}"
    content = dign_path.read_text(encoding="utf-8")

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
    for pat in required_patterns:
        assert pat in content, f"Missing exclusion pattern '{pat}' in .dockerignore"

    print("✓ .dockerignore: Clean exclusions verified.")


def validate_docker_compose() -> None:
    dc_path = ROOT / "docker-compose.yml"
    assert dc_path.exists(), f"Missing {dc_path}"
    content = dc_path.read_text(encoding="utf-8")
    validate_yaml_syntax(dc_path)

    # Services
    assert "match-server:" in content
    assert "mock-llm:" in content

    # Ports & Environment & Volumes & Container Networking
    assert "8000:8000" in content
    assert "GENESIS_LLM_URL=http://mock-llm:8099" in content
    assert "./data/mesh_cache:/app/data/mesh_cache" in content
    assert "./runs:/app/runs" in content
    assert "--host" in content and "0.0.0.0" in content, "mock-llm must bind to 0.0.0.0 for cross-container networking"

    print("✓ docker-compose.yml: match-server and mock-llm configuration verified.")


def main() -> int:
    print("=== Validating CI/CD & Containerization Artifacts ===")
    validate_ci_workflow()
    validate_legacy_test_workflow()
    validate_gitlab_ci()
    validate_dockerfile()
    validate_dockerignore()
    validate_docker_compose()
    print("=== All Milestone 3 artifacts validated successfully! ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

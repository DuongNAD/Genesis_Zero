# syntax=docker/dockerfile:1
# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder stage
# Prepares virtual environment and dependencies with uv
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Copy uv binary from official astral-sh image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Configure uv environment
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Copy dependency definition files
COPY pyproject.toml README.md ./

# Create virtual environment and install production dependencies
RUN uv venv /opt/venv && \
    uv pip install --no-cache -r pyproject.toml

# Copy project source packages and install project metadata
COPY genesis ./genesis
COPY net ./net
COPY client ./client
COPY net_config.py ./

RUN uv pip install --no-cache --no-deps .

# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime stage
# Minimal footprint production runtime with non-root security hardening
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install curl for healthcheck inspection and clean apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root system user and group genesis (UID 1000)
RUN groupadd -g 1000 genesis && \
    useradd -u 1000 -g genesis -m -s /bin/bash genesis

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    PYTHONIOENCODING=utf-8

# Pre-create required runtime directories for simulation runs, mesh cache, and models
RUN mkdir -p /app/runs /app/data/mesh_cache /app/data/models && \
    chown -R genesis:genesis /app/runs /app/data/mesh_cache /app/data/models

# Copy application files with non-root ownership
COPY --chown=genesis:genesis . /app

# Switch to non-root user
USER genesis

# Expose HTTP and WebSocket server port
EXPOSE 8000

# Container healthcheck pinging /v1/healthz
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/healthz || exit 1

# Default execution entrypoint: Uvicorn server binding 0.0.0.0:8000
CMD ["uvicorn", "net.server:app", "--host", "0.0.0.0", "--port", "8000"]

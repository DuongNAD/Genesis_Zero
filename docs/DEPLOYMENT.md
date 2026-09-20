# Genesis Zero — Production Deployment & Containerization Guide

> **Document Version**: 1.1.0 (Generation 17)  
> **Status**: Production Operational Manual  
> **Target Audience**: DevOps Engineers, System Administrators, Simulation Operators  

---

## 1. Overview

Genesis Zero is architected for containerized deployment across local development, on-premise compute clusters, and cloud environments. The simulation engine runs as a lightweight, non-root ASGI service communicating with distributed LLM backends and streaming real-time diorama telemetry over WebSockets to web clients.

```
                    ┌──────────────────────────────────────────────┐
                    │               Host System                    │
                    │                                              │
[Browser Spectator] │  ┌─────────────────┐    ┌─────────────────┐  │
        │           │  │  match-server   │    │    mock-llm     │  │
        ├───────────┼─►│   (Port 8000)   │◄──►│   (Port 8099)   │  │
 (HTTP/WebSocket)   │  │  user: genesis  │    │  user: genesis  │  │
                    │  │   (UID 1000)    │    │   (UID 1000)    │  │
                    │  └────────┬────────┘    └─────────────────┘  │
                    │           │ Volume Mounts                    │
                    │           ▼                                  │
                    │     ./runs  ./data/mesh_cache                │
                    └──────────────────────────────────────────────┘
```

---

## 2. Quickstart with Docker Compose

The fastest way to deploy a fully functional, self-contained Genesis Zero environment (including both the simulation server and a mock LLM provider) is via Docker Compose:

### 2.1 Launching the Stack
```bash
# Clone the repository
git clone https://github.com/DuongNAD/Genesis_Zero.git
cd Genesis_Zero

# Build and start services in background
docker compose up --build -d
```

### 2.2 Verifying Service Health
Inspect running container statuses and healthchecks:
```bash
docker compose ps
```
Output:
```
NAME                   IMAGE                 COMMAND                  SERVICE        STATUS                    PORTS
genesis-match-server   genesis-zero:latest   "uvicorn net.server:…"   match-server   Up (healthy)              0.0.0.0:8000->8000/tcp
genesis-mock-llm       genesis-zero:latest   "python -u scripts/f…"   mock-llm       Up                        0.0.0.0:8099->8099/tcp
```

Access the services:
- **3D Spectator & Web Dashboard**: Open [http://localhost:8000](http://localhost:8000) or [http://localhost:8000/web/watch3d.html](http://localhost:8000/web/watch3d.html).
- **Health Probe**: [http://localhost:8000/v1/healthz](http://localhost:8000/v1/healthz).
- **Mock LLM Server**: [http://localhost:8099](http://localhost:8099).

### 2.3 Viewing Real-Time Logs
```bash
# Stream match-server logs
docker compose logs -f match-server

# Stream mock-llm logs
docker compose logs -f mock-llm
```

### 2.4 Stopping the Stack
```bash
docker compose down
```

---

## 3. Multi-Stage Dockerfile Architecture

The production `Dockerfile` implements a hardened multi-stage build design to minimize image size and eliminate attack surface.

### 3.1 Stage 1: Builder (`python:3.11-slim`)
- **Package Manager**: Copies the high-performance `uv` binary from `ghcr.io/astral-sh/uv:latest`.
- **Dependency Compilation**: Compiles bytecode ahead of time (`UV_COMPILE_BYTECODE=1`) and installs dependencies into `/opt/venv`.
- **Non-Editable Wheel Installation**: Builds and installs project packages as standard static wheels (`uv pip install --no-cache --no-deps .`), preventing invalid `.pth` path references across container stages.

### 3.2 Stage 2: Runtime (`python:3.11-slim`)
- **Minimal Dependencies**: Installs only `curl` for container health monitoring, removing build toolchains and package managers.
- **Non-Root Security Hardening**:
  - System group and user `genesis` are created with fixed `UID 1000` / `GID 1000`.
  - The container drops root privileges (`USER genesis`) before launching the ASGI server.
- **Volume Preparation**:
  - Pre-creates `/app/runs` (match telemetry logs), `/app/data/mesh_cache` (3D diorama cache), and `/app/data/models`.
  - Pre-allocates ownership to `genesis:genesis` so non-root write operations succeed without runtime permission errors.
- **Automated Healthcheck**:
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
      CMD curl -f http://localhost:8000/v1/healthz || exit 1
  ```
- **Network Interface Binding**: Binds Uvicorn to `0.0.0.0:8000` to allow ingress traffic from container networks.

---

## 4. Environment Variables Reference

Configure the runtime environment via `.env` or container orchestration settings:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | HTTP and WebSocket server listening port. |
| `HOST` | `0.0.0.0` | Network interface binding address. |
| `PYTHONUTF8` | `1` | Enforces UTF-8 encoding across standard streams on all OS platforms. |
| `PYTHONIOENCODING` | `utf-8` | Explicit encoding declaration for Python I/O channels. |
| `PYTHONUNBUFFERED` | `1` | Disables stream buffering for instant container log emission. |
| `GENESIS_LLM_URL` | `http://mock-llm:8099` | Endpoint URL for the active LLM decision backend. |
| `GENESIS_LLM_BACKEND` | `mock` | Active cognitive backend: `mock`, `frontier`, `ollama`, or `vllm`. |
| `GENESIS_LLM_MODEL` | `mock-7b` | Name of the targeted model (e.g. `qwen2.5:7b`, `llama3.1`). |
| `GENESIS_LLM_API_KEY` | *(empty)* | Optional Bearer token / API key for external LLM endpoints. |
| `MESHY_API_KEY` | *(empty)* | API key for Meshy v2 text-to-3d diorama mesh generation. |

---

## 5. Linux Host Mount Permissions & Volume Security

Because the container runs as non-root user `genesis` (`UID 1000`), bind mounts from a Linux host system require proper file ownership to avoid `PermissionError` when the server writes match logs or caches 3D diorama meshes.

### 5.1 Host Directory Preparation
Before starting the containers on a Linux host, ensure host mount paths match `UID 1000`:

```bash
# Create persistent host mount directories
mkdir -p ./runs ./data/mesh_cache ./data/models

# Assign ownership to UID 1000 (standard first non-root Linux user)
sudo chown -R 1000:1000 ./runs ./data/mesh_cache ./data/models

# Set read/write permissions for user and group
chmod -R 775 ./runs ./data/mesh_cache ./data/models
```

### 5.2 User Namespace Remapping (Advanced)
If your Linux Docker daemon uses User Namespace Remapping (`userns-remap`), adjust the host directory ownership to match the remapped subordinate UID range defined in `/etc/subuid`.

---

## 6. Standalone Docker Run Commands

If deploying without Docker Compose, execute the individual containers manually:

### 6.1 Building the Container Image
```bash
docker build -t genesis-zero:latest .
```

### 6.2 Running the Simulation Server
```bash
docker run -d \
  --name genesis-match-server \
  -p 8000:8000 \
  -e PYTHONUTF8=1 \
  -e PYTHONIOENCODING=utf-8 \
  -v "$(pwd)/runs:/app/runs" \
  -v "$(pwd)/data/mesh_cache:/app/data/mesh_cache" \
  --restart unless-stopped \
  genesis-zero:latest
```

### 6.3 Connecting to Local Ollama on Host
To route agent decisions to an Ollama instance running natively on the host machine:

- **Linux**: Pass `--add-host=host.docker.internal:host-gateway` and set `-e GENESIS_LLM_URL=http://host.docker.internal:11434/v1`.
- **macOS / Windows**: Set `-e GENESIS_LLM_URL=http://host.docker.internal:11434/v1`.

---

## 7. Production Reverse Proxy Configuration

In public or enterprise environments, place Genesis Zero behind an HTTPS reverse proxy supporting WebSocket connection upgrading.

### 7.1 Nginx Ingress Configuration
```nginx
upstream genesis_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name genesis.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name genesis.example.com;

    ssl_certificate /etc/letsencrypt/live/genesis.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/genesis.example.com/privkey.pem;

    # Client body size for map and artifact uploads
    client_max_body_size 50M;

    # Primary REST API and Static 3D Spectator
    location / {
        proxy_pass http://genesis_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Telemetry Stream (/v1/spectate)
    location /v1/spectate {
        proxy_pass http://genesis_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

### 7.2 Caddy Ingress Configuration
```caddy
genesis.example.com {
    reverse_proxy 127.0.0.1:8000
}
```
*(Caddy handles HTTPS certificates and WebSocket connection upgrading automatically without extra configuration).*

---

## 8. Monitoring & Health Probes

Genesis Zero exposes dedicated health endpoints:

- `GET /v1/healthz`: Instant liveness probe returning `{"status": "ok"}`. Used by Docker `HEALTHCHECK`, Kubernetes liveness probes, and load balancers.
- `GET /v1/readyz`: Readiness probe confirming simulation state initialization, terrain readiness, and law generation completion.

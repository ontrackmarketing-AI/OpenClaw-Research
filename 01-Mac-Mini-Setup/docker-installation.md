# Docker Installation for OpenClaw (Recommended Path)

## Overview

Docker is the recommended way to run OpenClaw on a Mac Mini M4. It provides:
- **Isolation:** OpenClaw runs in its own container with defined resource limits
- **Reproducibility:** The exact same environment every time
- **Easy updates:** Pull new image, restart, done
- **Persistent data:** Volume mounts keep your memory, config, and skills across updates
- **Multi-service orchestration:** Docker Compose manages OpenClaw + supporting services

This guide covers Docker Desktop installation, the docker-compose.yml configuration,
networking with Ollama, and day-to-day operations.

---

## 1. Install Docker Desktop for Mac

### Via Homebrew (Recommended)

```bash
brew install --cask docker
```

### Via Direct Download

Download Docker Desktop for Mac (Apple Silicon) from
[docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/).

### Post-Install Setup

1. Launch Docker Desktop from Applications
2. Complete the initial setup wizard
3. Sign in with a Docker Hub account (free tier is fine) or skip
4. Docker Desktop will start the Docker daemon automatically

### Verify Installation

```bash
docker --version
# Docker version 27.x.x, build xxxxxxx

docker compose version
# Docker Compose version v2.x.x

# Run a test container
docker run --rm hello-world
```

---

## 2. Configure Docker Desktop Resources

Open Docker Desktop > Settings (gear icon) > Resources:

### Recommended Resource Allocation

| Setting            | 16 GB Mac | 32 GB Mac | 64 GB Mac | Notes                        |
|--------------------|-----------|-----------|-----------|------------------------------|
| **CPUs**           | 4         | 6         | 8         | Leave cores for macOS + Ollama |
| **Memory**         | 6 GB      | 10 GB     | 16 GB     | OpenClaw + containers        |
| **Swap**           | 2 GB      | 4 GB      | 4 GB      | Safety net for memory spikes |
| **Disk image size**| 32 GB     | 64 GB     | 64 GB     | Docker images + volumes      |

> **Important:** Do not allocate all your RAM to Docker. Ollama runs natively on the host
> (not in Docker) and needs its own RAM for model loading. Leave at least 50% of total RAM
> for macOS + Ollama.

### Additional Settings

- **General:** Enable "Start Docker Desktop when you sign in to your computer" (for 24/7 operation)
- **General:** Enable "Use Virtualization framework" (better Apple Silicon performance)
- **General:** Enable "Use Rosetta for x86_64/amd64 emulation on Apple Silicon" (for any
  x86-only images)

---

## 3. Project Directory Setup

Create a dedicated directory for your OpenClaw Docker deployment:

```bash
mkdir -p ~/openclaw
cd ~/openclaw

# Create directories for persistent data
mkdir -p data/memory
mkdir -p data/skills
mkdir -p data/config
mkdir -p data/logs
```

---

## 4. docker-compose.yml

Create the main Docker Compose file:

```bash
nano ~/openclaw/docker-compose.yml
```

```yaml
# =============================================================================
# OpenClaw Docker Compose Configuration
# Mac Mini M4 - 24/7 Agent Server
# =============================================================================

version: "3.8"

services:
  # ---------------------------------------------------------------------------
  # OpenClaw Gateway - Core Agent Server
  # ---------------------------------------------------------------------------
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw-gateway
    restart: unless-stopped
    ports:
      - "18789:18789"   # Gateway WebSocket server
      - "3000:3000"     # Web UI
    env_file:
      - .env
    volumes:
      # Persistent data (survives container rebuilds)
      - ./data/memory:/app/data/memory
      - ./data/skills:/app/data/skills
      - ./data/config:/app/data/config
      - ./data/logs:/app/data/logs
    environment:
      - NODE_ENV=production
      - OPENCLAW_PORT=18789
      - OPENCLAW_HOST=0.0.0.0
      # Access Ollama running on the Mac host
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      # Ensures host.docker.internal resolves on all Docker versions
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 4G
        reservations:
          cpus: "1"
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  # ---------------------------------------------------------------------------
  # Redis - Optional: Session cache and pub/sub for multi-agent coordination
  # ---------------------------------------------------------------------------
  redis:
    image: redis:7-alpine
    container_name: openclaw-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

# ---------------------------------------------------------------------------
# Named Volumes
# ---------------------------------------------------------------------------
volumes:
  redis-data:
    driver: local
```

---

## 5. Environment File (.env)

Create the environment file (see [environment-variables.md](environment-variables.md) for the
complete reference):

```bash
nano ~/openclaw/.env
```

Minimal `.env` to get started:

```bash
# =============================================================================
# OpenClaw Environment Variables
# =============================================================================

# --- Core ---
OPENCLAW_PORT=18789
OPENCLAW_HOST=0.0.0.0
OPENCLAW_LOG_LEVEL=info

# --- LLM Providers (add at least one) ---
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# OPENAI_API_KEY=sk-xxxxx
OLLAMA_BASE_URL=http://host.docker.internal:11434

# --- Security ---
OPENCLAW_DISABLE_BONJOUR=1
# OPENCLAW_AUTH_TOKEN=your-secret-token-here

# --- Default Model ---
OPENCLAW_DEFAULT_MODEL=ollama/qwen3:14b
```

**Security:** Ensure `.env` is not committed to version control:

```bash
echo ".env" >> ~/openclaw/.gitignore
chmod 600 ~/openclaw/.env
```

---

## 6. Docker Networking with Ollama

OpenClaw runs inside Docker, but Ollama runs natively on the Mac host for direct access to
Apple Silicon's unified memory (which is essential for LLM performance).

### How It Works

```
+---------------------------+       +---------------------------+
| Docker Container          |       | Mac Host (native)         |
|                           |       |                           |
| OpenClaw Gateway :18789   | ----> | Ollama API :11434         |
|   uses                    |       |   loads models into       |
|   host.docker.internal    |       |   Apple Silicon unified   |
|   :11434                  |       |   memory                  |
+---------------------------+       +---------------------------+
```

The key is `host.docker.internal` -- this special hostname resolves to the Mac host from
inside Docker containers. The `extra_hosts` directive in the compose file ensures this works
reliably.

### Verify Connectivity

```bash
# From the host, verify Ollama is running
curl http://localhost:11434/api/tags

# From inside the container, verify it can reach Ollama
docker exec openclaw-gateway curl http://host.docker.internal:11434/api/tags
```

---

## 7. Starting and Stopping

### Start All Services (Detached)

```bash
cd ~/openclaw
docker compose up -d
```

Output:

```
[+] Running 3/3
 ✔ Network openclaw_default    Created
 ✔ Container openclaw-redis    Started
 ✔ Container openclaw-gateway  Started
```

### Stop All Services

```bash
cd ~/openclaw
docker compose down
```

### Restart a Single Service

```bash
docker compose restart openclaw
```

### Start with Build (after config changes)

```bash
docker compose up -d --force-recreate
```

---

## 8. Viewing Logs

### Follow All Logs (Real-time)

```bash
cd ~/openclaw
docker compose logs -f
```

### Follow Only OpenClaw Logs

```bash
docker compose logs -f openclaw
```

### View Last 100 Lines

```bash
docker compose logs --tail 100 openclaw
```

### View Logs Since a Timestamp

```bash
docker compose logs --since "2026-02-05T10:00:00" openclaw
```

### Check for Errors Only

```bash
docker compose logs openclaw 2>&1 | grep -i "error\|fatal\|exception"
```

---

## 9. Updating OpenClaw

### Standard Update Process

```bash
cd ~/openclaw

# Pull the latest image
docker compose pull

# Recreate containers with the new image (data volumes are preserved)
docker compose up -d

# Verify the new version is running
docker compose logs --tail 20 openclaw
```

### Pin to a Specific Version

If you want stability over bleeding-edge, pin the image version in `docker-compose.yml`:

```yaml
services:
  openclaw:
    image: openclaw/openclaw:1.5.2   # Instead of :latest
```

Then update deliberately:

```yaml
    image: openclaw/openclaw:1.6.0   # Edit to new version
```

```bash
docker compose up -d
```

---

## 10. Health Check Configuration

The health check in the compose file automatically monitors OpenClaw's status:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:18789/health"]
  interval: 30s      # Check every 30 seconds
  timeout: 10s       # Fail if no response in 10 seconds
  retries: 3         # Mark unhealthy after 3 consecutive failures
  start_period: 15s  # Wait 15 seconds before first check
```

### Check Container Health Status

```bash
# Quick status overview
docker compose ps

# Output shows health status:
# NAME                STATUS              PORTS
# openclaw-gateway    Up 2 hours (healthy)   0.0.0.0:18789->18789/tcp, 0.0.0.0:3000->3000/tcp
# openclaw-redis      Up 2 hours (healthy)   0.0.0.0:6379->6379/tcp

# Detailed health check output
docker inspect --format='{{json .State.Health}}' openclaw-gateway | jq .
```

### Auto-Restart Behavior

The `restart: unless-stopped` policy means:
- Container restarts automatically if it crashes
- Container restarts after Docker Desktop restarts (boot, update)
- Container does NOT restart if you manually stopped it with `docker compose stop`

---

## 11. Maintenance Commands

### View Resource Usage

```bash
# Real-time container resource usage
docker stats

# One-shot snapshot
docker stats --no-stream
```

### Shell Into the Container

```bash
# Open a shell inside the running container
docker exec -it openclaw-gateway /bin/sh

# Run a one-off command
docker exec openclaw-gateway node --version
```

### Clean Up Docker Resources

```bash
# Remove stopped containers, unused networks, dangling images
docker system prune

# Remove ALL unused images (reclaim disk space)
docker system prune -a

# Check Docker disk usage
docker system df
```

### Backup Persistent Data

```bash
# Create a timestamped backup of all OpenClaw data
tar -czf ~/openclaw-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C ~/openclaw data/

# Or backup specific directories
cp -r ~/openclaw/data/memory ~/openclaw-memory-backup-$(date +%Y%m%d)
```

---

## 12. Troubleshooting

### Container Will Not Start

```bash
# Check what went wrong
docker compose logs openclaw

# Common issues:
# - Port 18789 already in use: another process is on that port
#   Fix: lsof -i :18789 (find and kill the process)
# - .env file missing or malformed
# - Docker Desktop not running
```

### Cannot Connect to Ollama from Container

```bash
# Verify Ollama is running on host
curl http://localhost:11434/api/tags

# Verify from inside container
docker exec openclaw-gateway curl http://host.docker.internal:11434/api/tags

# If host.docker.internal does not resolve, check extra_hosts in compose file
# and ensure Docker Desktop is up to date
```

### Out of Memory

```bash
# Check container memory usage
docker stats --no-stream

# Increase memory limit in Docker Desktop settings
# Or reduce the deploy.resources.limits.memory in docker-compose.yml
```

### Slow Performance

```bash
# Check if Docker is using Virtualization framework
# Docker Desktop > Settings > General > "Use Virtualization framework" should be ON

# Check if file sharing is causing I/O bottleneck
# Docker Desktop > Settings > Resources > File sharing
# Ensure ~/openclaw is in the shared paths (should be by default)
```

---

## Next Steps

- [Environment Variables](environment-variables.md) - Full configuration reference
- [Verification Tests](verification-tests.md) - Test the complete installation
- [Native Installation](native-installation.md) - Alternative: install without Docker

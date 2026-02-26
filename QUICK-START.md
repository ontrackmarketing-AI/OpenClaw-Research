# OpenClaw Quick-Start: Mac Mini Setup

> Fast-track reference for getting OpenClaw running on a Mac Mini.
> For deep-dive details, see the guides in `01-Mac-Mini-Setup/`.

---

## Prerequisites Checklist

### Hardware Requirements

- [ ] Mac Mini (M2 or M4 recommended; M1 minimum)
- [ ] 16 GB RAM minimum (32 GB recommended for local LLM + agent workloads)
- [ ] 256 GB SSD minimum (512 GB+ recommended for Docker images, model files, vector DBs)
- [ ] Stable internet connection (initial pull of Docker images is ~8-12 GB)
- [ ] Ethernet cable recommended over Wi-Fi for reliability during long-running agent tasks

### Software Prerequisites (install before starting)

- [ ] macOS Sonoma 14.x or later (Sequoia 15.x preferred)
- [ ] Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- [ ] Docker Desktop for Mac: `brew install --cask docker` (allocate 8 GB+ RAM in Docker settings)
- [ ] Git: `brew install git`
- [ ] Node.js 20 LTS: `brew install node@20`
- [ ] Python 3.11+: `brew install python@3.11`
- [ ] Claude CLI (for Claude Code skills): `npm install -g @anthropic-ai/claude-code`

### Accounts and API Keys Required

| Service | Purpose | Where to Get |
|---------|---------|--------------|
| Anthropic API | Core LLM for agents | https://console.anthropic.com |
| OpenAI API | Fallback LLM / embeddings | https://platform.openai.com |
| Clay.com | Lead enrichment (Rise Local) | Existing account |
| GoHighLevel | CRM / marketing automation | Existing account |
| Airtable | Data management (active MCP) | Existing account |
| GitHub | Clone OpenClaw repo | https://github.com |
| Supabase | Database (currently disabled, optional) | Existing project: jitawzicdwgbhatvjblh |
| Docker Hub | Pull container images | https://hub.docker.com (free tier OK) |

---

## Step-by-Step Docker-Based Install (Recommended Path)

### Step 1: Clone the OpenClaw Repository

```bash
cd ~/Projects
git clone https://github.com/openclaw/openclaw.git
cd openclaw
```

### Step 2: Copy and Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your values (see template below), then:

```bash
# Validate the env file has no missing required vars
grep -c "CHANGE_ME" .env
# Should return 0 if all values are filled in
```

### Step 3: Build and Start Core Services

```bash
# Pull all images first (avoids timeout issues)
docker compose pull

# Start core infrastructure (database, redis, vector store)
docker compose up -d postgres redis qdrant

# Wait 10 seconds for databases to initialize
sleep 10

# Start the OpenClaw platform
docker compose up -d openclaw-api openclaw-web openclaw-worker
```

### Step 4: Run Database Migrations

```bash
docker compose exec openclaw-api python manage.py migrate
# Or if using Node-based backend:
# docker compose exec openclaw-api npx prisma migrate deploy
```

### Step 5: Create Your Admin User

```bash
docker compose exec openclaw-api python manage.py createsuperuser \
  --email your@email.com \
  --username admin
```

### Step 6: Start Additional Services (MCP Servers, N8N)

```bash
# Start n8n for workflow automation
docker compose up -d n8n

# Start MCP bridge (connects Claude Code skills to OpenClaw)
docker compose up -d mcp-bridge
```

---

## Environment Variable Template

Create your `.env` file with the following structure:

```bash
# =============================================================
# OpenClaw Core Configuration
# =============================================================
OPENCLAW_HOST=0.0.0.0
OPENCLAW_PORT=8080
OPENCLAW_ENV=production
OPENCLAW_SECRET_KEY=<generate-with: openssl rand -hex 32>
OPENCLAW_LOG_LEVEL=info

# =============================================================
# Database (PostgreSQL)
# =============================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=openclaw
POSTGRES_USER=openclaw
POSTGRES_PASSWORD=<strong-password-here>
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# =============================================================
# Redis (Queue + Cache)
# =============================================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password-here>
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/0

# =============================================================
# Vector Database (Qdrant)
# =============================================================
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=<optional-api-key>

# =============================================================
# LLM Providers
# =============================================================
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
# Local LLM (Ollama) - optional, for cost savings
OLLAMA_HOST=http://host.docker.internal:11434

# =============================================================
# Existing Service Integration
# =============================================================
# Clay.com (Rise Local Lead Creation)
CLAY_API_KEY=<your-clay-api-key>
CLAY_WORKSPACE_ID=<your-workspace-id>

# GoHighLevel
GHL_API_KEY=<your-ghl-api-key>
GHL_LOCATION_ID=<your-location-id>

# Airtable
AIRTABLE_API_KEY=<your-airtable-pat>
AIRTABLE_BASE_ID=<your-base-id>

# Supabase (disabled - uncomment when re-enabling)
# SUPABASE_URL=https://jitawzicdwgbhatvjblh.supabase.co
# SUPABASE_ANON_KEY=<your-anon-key>
# SUPABASE_SERVICE_KEY=<your-service-key>

# =============================================================
# N8N Workflow Engine
# =============================================================
N8N_HOST=n8n
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<strong-password-here>
N8N_ENCRYPTION_KEY=<generate-with: openssl rand -hex 16>

# =============================================================
# OnTrack Marketing (FastAPI backend)
# =============================================================
ONTRACK_API_URL=http://host.docker.internal:8000
ONTRACK_API_KEY=<your-ontrack-key>
```

---

## First-Run Verification Commands

Run each of these to confirm the platform is healthy:

```bash
# 1. Check all containers are running
docker compose ps
# Expected: All services show "Up" status, no "Restarting"

# 2. Verify API is responding
curl -s http://localhost:8080/health | jq .
# Expected: {"status": "healthy", "version": "x.x.x", ...}

# 3. Check database connectivity
docker compose exec openclaw-api python -c "from app.db import engine; print('DB OK')"
# Expected: "DB OK"

# 4. Verify Redis is reachable
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping
# Expected: PONG

# 5. Check Qdrant vector store
curl -s http://localhost:6333/collections | jq .
# Expected: JSON with collections list (may be empty on first run)

# 6. Verify N8N is accessible
curl -s http://localhost:5678/healthz
# Expected: {"status":"ok"}

# 7. Check web UI loads
open http://localhost:8080
# Expected: OpenClaw dashboard login page

# 8. Run the built-in self-test suite
docker compose exec openclaw-api python manage.py selftest
# Expected: All checks pass
```

---

## Common Troubleshooting

### Docker containers keep restarting

```bash
# Check logs for the failing container
docker compose logs --tail=50 openclaw-api

# Common fix: insufficient memory - increase Docker Desktop RAM allocation
# Docker Desktop > Settings > Resources > Memory > set to 8GB+
```

### Port conflicts (address already in use)

```bash
# Find what is using the port
lsof -i :8080
# Kill the process or change OPENCLAW_PORT in .env

# Common conflicts:
# 5432 - local PostgreSQL
# 6379 - local Redis
# 5678 - other n8n instance
# 8080 - other web servers
```

### Database migration fails

```bash
# Reset the database (DESTRUCTIVE - development only)
docker compose exec postgres psql -U openclaw -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec openclaw-api python manage.py migrate

# If using existing data, check migration version compatibility
docker compose exec openclaw-api python manage.py showmigrations
```

### Apple Silicon (M1/M2/M4) image compatibility

```bash
# If you see "exec format error" it means an x86 image without ARM build
# Force platform in docker-compose.yml for affected services:
#   platform: linux/amd64
# This runs under Rosetta 2 emulation (slower but works)
```

### Qdrant won't start (memory issues)

```bash
# Qdrant needs significant memory for vector operations
# In docker-compose.yml, add memory limits:
#   deploy:
#     resources:
#       limits:
#         memory: 2G

# Or reduce collection size in OpenClaw settings
```

### Cannot connect to Clay.com / GHL / Airtable APIs

```bash
# Verify API keys are valid
curl -H "Authorization: Bearer $CLAY_API_KEY" https://api.clay.com/v1/me
curl -H "Authorization: Bearer $GHL_API_KEY" https://rest.gohighlevel.com/v1/contacts/?limit=1
curl -H "Authorization: Bearer $AIRTABLE_API_KEY" https://api.airtable.com/v0/meta/bases

# If behind corporate firewall/VPN, ensure outbound HTTPS is allowed
# Check Docker DNS: add to docker-compose.yml under the service:
#   dns:
#     - 8.8.8.8
#     - 1.1.1.1
```

### N8N workflows not triggering

```bash
# Check n8n is in "production" mode (not "editor" only)
# Ensure webhook URLs point to the Mac Mini's IP, not localhost
# Verify: docker compose exec n8n n8n execute --id <workflow-id>
```

---

## Detailed Guides

For deeper coverage, see the following in `01-Mac-Mini-Setup/`:

| Guide | Covers |
|-------|--------|
| `hardware-requirements.md` | Detailed hardware specs, thermal management, monitoring |
| `network-configuration.md` | Static IP, firewall rules, remote access (SSH/VNC) |
| `docker-optimization.md` | Docker Desktop tuning for Apple Silicon, volume mounts, caching |
| `security-hardening.md` | TLS setup, secrets management, network isolation |
| `monitoring-setup.md` | Prometheus, Grafana, alerting for agent health |
| `backup-strategy.md` | Automated backups for databases, configs, and agent state |

---

*Last updated: 2026-02-05*
*Applies to: OpenClaw (check GitHub for latest version)*

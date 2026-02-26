# Phase 1 - Foundation (Week 1)

## Goal

Get the Mac Mini M4 Pro running OpenClaw in Docker, accessible via local network, with both local (Ollama) and API (Claude) models functional. By the end of this phase, you have a working AI agent platform you can interact with from your Windows PC.

---

## Prerequisites

| Item | Status | Notes |
|------|--------|-------|
| Mac Mini M4 Pro purchased | Pending | 24GB+ RAM recommended for local models |
| Monitor + keyboard (temporary) | Needed | Only for initial setup, then headless via SSH |
| Ethernet cable or stable Wi-Fi | Needed | Wired preferred for server reliability |
| Anthropic API key | Have | From existing Claude Code usage |
| This research knowledge base reviewed | In progress | Understand architecture before installing |

---

## Day 1-2: Mac Mini Hardware Setup

### Physical Setup

1. **Unbox and connect** monitor, keyboard, mouse, and ethernet cable
2. **Power on** and complete macOS Sequoia initial setup wizard
   - Create admin account (use a strong password, you will need it for SSH)
   - Skip Apple ID sign-in if you want to keep this a pure server (optional)
   - Select your time zone and language

### macOS Configuration for Always-On Server

Open **System Settings** and configure the following:

```
# Energy settings (System Settings > Energy Saver / Battery)
- Turn display off after: 10 minutes (or Never)
- Prevent automatic sleeping when display is off: ON
- Wake for network access: ON
- Start up automatically after a power failure: ON

# Lock Screen (System Settings > Lock Screen)
- Require password after screen saver begins: After 5 minutes
- Start Screen Saver when inactive: Never (for server use)

# Login (System Settings > Users & Groups > Login Options)
- Automatic login: Enable for your admin account
  (This ensures the Mac recovers from power failures unattended)
```

### Install Core Development Tools

Open Terminal and run the following commands in order:

```bash
# 1. Install Xcode Command Line Tools (required for Homebrew)
xcode-select --install
# Click "Install" when prompted, wait for completion (~5 minutes)

# 2. Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 3. Add Homebrew to PATH (Apple Silicon path)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# 4. Verify Homebrew installation
brew --version

# 5. Install essential tools
brew install git node@22 wget curl jq

# 6. Verify Node.js version (must be 22+)
node --version
# Expected: v22.x.x

# 7. Install Docker Desktop for Mac
brew install --cask docker

# 8. Launch Docker Desktop
open -a Docker
# Wait for Docker to fully start (whale icon in menu bar stops animating)

# 9. Verify Docker is running
docker --version
docker compose version
```

### Configure SSH for Remote Access

```bash
# 1. Enable Remote Login
# System Settings > General > Sharing > Remote Login: ON
# Or via command line:
sudo systemsetup -setremotelogin on

# 2. Find your Mac Mini's local IP address
ipconfig getifaddr en0    # Ethernet
# or
ipconfig getifaddr en1    # Wi-Fi

# 3. Note this IP address (e.g., 192.168.1.100)
# You will use this to connect from your Windows PC

# 4. Test SSH locally first
ssh localhost
# Should log you in without issues
```

### Set Static IP (Recommended)

Go to **System Settings > Network > Ethernet (or Wi-Fi) > Details > TCP/IP**:
- Configure IPv4: Manually
- IP Address: Choose an address outside your router's DHCP range (e.g., 192.168.1.200)
- Subnet Mask: 255.255.255.0
- Router: Your router's IP (e.g., 192.168.1.1)
- DNS: 1.1.1.1, 8.8.8.8

Alternatively, configure a DHCP reservation in your router's admin panel for the Mac Mini's MAC address.

### Test SSH from Windows PC

Open PowerShell on your Windows machine:

```powershell
# Test SSH connection
ssh yourusername@192.168.1.200

# If successful, you can now disconnect the monitor from the Mac Mini
# All remaining setup can be done via SSH
```

---

## Day 3-4: OpenClaw Installation

### Create Directory Structure

```bash
# SSH into Mac Mini from Windows PC
ssh yourusername@192.168.1.200

# Create OpenClaw directories
mkdir -p ~/.openclaw/{config,memory,skills,data,logs,assets}

# Verify structure
ls -la ~/.openclaw/
```

### Create docker-compose.yml

```bash
# Create the compose file
cat > ~/.openclaw/docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped
    ports:
      - "18789:18789"   # Gateway API
      - "3000:3000"     # Web UI
    volumes:
      - ./config:/app/config
      - ./memory:/app/memory
      - ./skills:/app/skills
      - ./data:/app/data
      - ./logs:/app/logs
      - ./assets:/app/assets
    env_file:
      - .env
    environment:
      - NODE_ENV=production
      - OPENCLAW_HOST=0.0.0.0
      - OPENCLAW_PORT=18789
    networks:
      - openclaw-network

networks:
  openclaw-network:
    driver: bridge
COMPOSE
```

### Create Initial .env File

```bash
cat > ~/.openclaw/.env << 'ENV'
# OpenClaw Environment Configuration
# Phase 1 - Minimal required variables

# Primary LLM (Claude API)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Local LLM (Ollama - configured in Day 5)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Web UI
OPENCLAW_WEB_UI=true
OPENCLAW_WEB_PORT=3000

# Logging
LOG_LEVEL=info
LOG_DIR=/app/logs

# Memory
MEMORY_DIR=/app/memory
ENV

# Secure the .env file
chmod 600 ~/.openclaw/.env
```

**Important:** Replace `sk-ant-your-key-here` with your actual Anthropic API key.

### Pull and Start OpenClaw

```bash
cd ~/.openclaw

# Pull the latest OpenClaw image
docker compose pull

# Start OpenClaw in detached mode
docker compose up -d

# Check container status
docker compose ps

# View startup logs (watch for errors)
docker compose logs -f --tail=50
# Press Ctrl+C to stop following logs
```

### Verify Gateway Running

```bash
# Test gateway API (port 18789)
curl -s http://localhost:18789/health | jq .
# Expected: {"status": "ok", ...}

# Test from Windows PC (replace IP)
# In PowerShell: Invoke-RestMethod http://192.168.1.200:18789/health
```

### Verify Web UI

1. Open browser on Windows PC
2. Navigate to `http://192.168.1.200:3000`
3. You should see the OpenClaw web interface
4. Test basic interaction: type a message and verify a response

### Test Basic Agent Interaction

```bash
# Test via CLI (from Mac Mini terminal)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, OpenClaw. What can you do?"}'

# Verify you get a coherent response from the Claude API
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Container won't start | Check `docker compose logs openclaw` for errors |
| Port already in use | `lsof -i :18789` to find conflicting process, kill it |
| Can't pull image | Verify Docker Desktop is running and has internet access |
| API key rejected | Double-check .env file, ensure no extra spaces or quotes around key |
| Web UI not loading | Verify port 3000 is mapped in docker-compose.yml, check firewall |

---

## Day 5: Ollama Setup

### Install Ollama

```bash
# Install Ollama via Homebrew
brew install ollama

# Start Ollama service
brew services start ollama

# Verify Ollama is running
curl http://localhost:11434/api/tags
# Should return JSON with empty models list initially
```

### Pull Initial Models

```bash
# Pull primary reasoning model (14B parameters, fits comfortably in 24GB RAM)
ollama pull qwen3:14b
# Download: ~8GB, takes 5-15 minutes depending on connection

# Pull embedding model for RAG (Phase 3 prerequisite)
ollama pull nomic-embed-text
# Download: ~274MB, quick download

# Verify models are available
ollama list
# Should show both models with their sizes
```

### Test Ollama Connectivity from Docker

```bash
# Test that Docker container can reach Ollama on the host
docker exec openclaw curl -s http://host.docker.internal:11434/api/tags | jq .
# Should return the model list

# If host.docker.internal doesn't work, use the Mac's IP directly
docker exec openclaw curl -s http://192.168.1.200:11434/api/tags | jq .
```

### Configure OpenClaw to Use Ollama

Update the `.env` file to include Ollama configuration:

```bash
# Add Ollama model configuration to .env
cat >> ~/.openclaw/.env << 'ENV'

# Ollama Local Models
OLLAMA_MODEL_CHAT=qwen3:14b
OLLAMA_MODEL_EMBED=nomic-embed-text
OLLAMA_ENABLED=true
ENV

# Restart OpenClaw to pick up changes
cd ~/.openclaw && docker compose restart
```

### Test Local Model Interactions

```bash
# Test Ollama directly
curl -X POST http://localhost:11434/api/generate \
  -d '{"model": "qwen3:14b", "prompt": "What is 2+2? Reply in one sentence.", "stream": false}'

# Test through OpenClaw (if model routing is configured)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?", "model": "local"}'
```

---

## Day 6-7: Initial Configuration

### Configure Model Routing

The goal is to use local models for simple, fast tasks and Claude API for complex reasoning. Update your OpenClaw configuration:

```bash
# Create model routing configuration
cat > ~/.openclaw/config/model-routing.json << 'JSON'
{
  "default_model": "claude-sonnet-4-20250514",
  "routing_rules": [
    {
      "name": "simple-questions",
      "conditions": {
        "estimated_complexity": "low",
        "task_types": ["classification", "extraction", "formatting", "summarization"]
      },
      "model": "ollama/qwen3:14b",
      "reason": "Simple tasks run locally to save API costs"
    },
    {
      "name": "complex-reasoning",
      "conditions": {
        "estimated_complexity": "high",
        "task_types": ["analysis", "planning", "code-generation", "multi-step"]
      },
      "model": "claude-sonnet-4-20250514",
      "reason": "Complex tasks need API model quality"
    },
    {
      "name": "embeddings",
      "conditions": {
        "task_types": ["embedding"]
      },
      "model": "ollama/nomic-embed-text",
      "reason": "Embeddings always run locally"
    }
  ],
  "fallback": {
    "model": "claude-sonnet-4-20250514",
    "reason": "Default to API model when unsure"
  }
}
JSON
```

### Test Multi-Model Setup

```bash
# Restart to load new config
cd ~/.openclaw && docker compose restart

# Test that both models respond correctly
# Simple task (should route to local)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize this in one sentence: OpenClaw is an AI agent platform."}'

# Complex task (should route to API)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a detailed marketing strategy for a local plumbing company targeting homeowners within 25 miles."}'
```

### Create First Custom Agent

```bash
# Create a basic assistant agent configuration
cat > ~/.openclaw/config/agents/assistant.json << 'JSON'
{
  "name": "Assistant",
  "description": "General purpose assistant for OnTrack Marketing operations",
  "system_prompt": "You are an AI assistant for OnTrack Marketing, a digital marketing agency focused on local service businesses (plumbers, solar installers, dentists, lawyers). You help with lead management, content creation, research, and marketing operations. Be concise and actionable in your responses.",
  "model": "auto",
  "tools": [],
  "memory": {
    "enabled": true,
    "auto_save": true
  }
}
JSON
```

### Document Everything

Create a setup log capturing what was done, any issues encountered, and the current state:

```bash
# Create a setup log
cat > ~/.openclaw/SETUP-LOG.md << 'LOG'
# OpenClaw Setup Log

## Phase 1: Foundation

### Date Started: [FILL IN]
### Date Completed: [FILL IN]

### What Was Installed
- macOS Sequoia on Mac Mini M4 Pro
- Homebrew, Git, Node.js 22, Docker Desktop
- OpenClaw via Docker Compose
- Ollama with qwen3:14b and nomic-embed-text

### Configuration
- OpenClaw gateway: port 18789
- OpenClaw web UI: port 3000
- Ollama: port 11434
- Mac Mini IP: [FILL IN]
- SSH access: enabled

### Issues Encountered
- [Document any issues here]

### Verification Results
- [ ] Docker container running
- [ ] Web UI accessible from Windows PC
- [ ] Claude API responding
- [ ] Ollama local model responding
- [ ] Model routing working
- [ ] Custom agent created

### Notes
- [Any additional notes]
LOG
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| OpenClaw container running | `docker compose ps` shows "Up" | [ ] |
| Gateway responsive | `curl localhost:18789/health` returns OK | [ ] |
| Web UI accessible | Browse to `http://mac-mini-ip:3000` | [ ] |
| Claude API working | Send complex question, get quality response | [ ] |
| Ollama running | `ollama list` shows models | [ ] |
| Local model working | Send simple question to local model | [ ] |
| Model routing configured | Simple tasks go local, complex go API | [ ] |
| SSH access from Windows | `ssh user@mac-mini-ip` connects | [ ] |
| Custom agent created | Agent responds with marketing context | [ ] |

---

## Rollback Plan

If major issues arise during Phase 1:

1. **Docker image issue**: Downgrade to a previous version
   ```bash
   docker compose down
   # Edit docker-compose.yml to specify older version tag
   docker compose pull
   docker compose up -d
   ```

2. **Ollama issues**: Uninstall and reinstall
   ```bash
   brew services stop ollama
   brew uninstall ollama
   rm -rf ~/.ollama
   brew install ollama
   ```

3. **Complete restart**: Reset Docker and start fresh
   ```bash
   docker compose down -v
   docker system prune -a
   # Re-run Day 3-4 steps
   ```

4. **Hardware issue**: Mac Mini can be returned within Apple's return window

---

## Time Estimate

| Task | Estimated Time | Actual Time |
|------|---------------|-------------|
| Hardware setup | 1-2 hours | |
| macOS configuration | 30 minutes | |
| Tool installation | 1 hour | |
| SSH setup | 30 minutes | |
| OpenClaw installation | 1-2 hours | |
| Ollama setup | 1 hour (plus download time) | |
| Configuration and testing | 2-3 hours | |
| Documentation | 1 hour | |
| **Total** | **7-10 hours** | |

---

## Next Phase

Once all success criteria are met, proceed to [Phase 2 - Security Hardening](phase-2-security.md). Do not skip security -- you will be putting API keys and client data on this machine.

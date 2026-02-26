# Native Installation for OpenClaw (npm Alternative)

## Overview

While Docker is the recommended deployment method, OpenClaw can also be installed natively
via npm. This approach runs OpenClaw directly on the host macOS system without
containerization.

### When to Choose Native Over Docker

| Factor                      | Native (npm)                          | Docker                              |
|-----------------------------|---------------------------------------|--------------------------------------|
| **Setup simplicity**        | Simpler, fewer layers                 | More moving parts                    |
| **Ollama access**           | Direct localhost, no network bridge   | Requires host.docker.internal        |
| **Hardware access**         | Direct Apple Silicon access           | Virtualization layer (minor overhead)|
| **Resource overhead**       | Lower (no Docker daemon, VM)          | Docker Desktop uses 2-4 GB RAM      |
| **Isolation**               | Runs as your user, shared filesystem  | Containerized, limited access        |
| **Security**                | Less isolated                         | Better sandboxing                    |
| **Updates**                 | npm update, manual restart            | Pull image, recreate container       |
| **Multi-service management**| Manual or PM2                         | Docker Compose handles everything    |
| **Portability**             | Tied to host Node.js version          | Consistent across environments       |

**Bottom line:** Choose native if you want the simplest possible setup, need the lowest
overhead, or have limited RAM (16 GB) where Docker's overhead matters. Choose Docker for
production-grade isolation and easier management.

---

## 1. Prerequisites

Verify your environment before installing OpenClaw:

```bash
# Node.js 22+ is required
node --version
# Must show v22.x.x or higher

# npm should be 10+ (comes with Node 22)
npm --version
# Must show 10.x.x or higher

# Alternatively, check if pnpm is available (faster, saves disk space)
pnpm --version
# Optional, but recommended
```

If Node.js is not installed or is the wrong version, see
[macOS Preparation](macos-preparation.md) section 4.

### Install pnpm (Optional but Recommended)

```bash
# pnpm is faster and more disk-efficient than npm
npm install -g pnpm

# Or via Homebrew
brew install pnpm
```

---

## 2. Install OpenClaw

### Via npm (Standard)

```bash
npm install -g openclaw@latest
```

### Via pnpm (Faster)

```bash
pnpm install -g openclaw@latest
```

### Verify Installation

```bash
openclaw --version
# Should print the installed version

which openclaw
# Should show the global install path, e.g., ~/.nvm/versions/node/v22.x.x/bin/openclaw
```

---

## 3. Initial Configuration

OpenClaw stores its configuration in `~/.openclaw/`.

### Create the Configuration Directory

```bash
# OpenClaw typically creates this on first run, but you can set it up ahead of time
mkdir -p ~/.openclaw
```

### Create the Environment File

```bash
nano ~/.openclaw/.env
```

Add your configuration (see [environment-variables.md](environment-variables.md) for the full
reference):

```bash
# =============================================================================
# OpenClaw Configuration - Native Installation
# =============================================================================

# --- Core ---
OPENCLAW_PORT=18789
OPENCLAW_HOST=0.0.0.0
OPENCLAW_LOG_LEVEL=info

# --- LLM Providers ---
# ANTHROPIC_API_KEY=sk-ant-xxxxx
# OPENAI_API_KEY=sk-xxxxx
OLLAMA_BASE_URL=http://localhost:11434

# --- Security ---
OPENCLAW_DISABLE_BONJOUR=1
# OPENCLAW_AUTH_TOKEN=your-secret-token-here

# --- Default Model ---
OPENCLAW_DEFAULT_MODEL=ollama/qwen3:14b

# --- Memory ---
OPENCLAW_MEMORY_DIR=~/.openclaw/memory
OPENCLAW_SQLITE_PATH=~/.openclaw/memory/openclaw.db
```

Secure the file:

```bash
chmod 600 ~/.openclaw/.env
```

---

## 4. Start OpenClaw

### Basic Start (Foreground)

```bash
openclaw start
```

This runs OpenClaw in the foreground, printing logs to the terminal. The Gateway WebSocket
server starts on port 18789, and the Web UI on port 3000.

Press `Ctrl+C` to stop.

### Start with Specific Config

```bash
# Point to a specific .env file
openclaw start --env ~/.openclaw/.env

# Start with verbose logging
OPENCLAW_LOG_LEVEL=debug openclaw start

# Start on a different port
OPENCLAW_PORT=9999 openclaw start
```

---

## 5. Process Management with PM2

For 24/7 operation, you need a process manager that:
- Keeps OpenClaw running if it crashes
- Starts OpenClaw automatically on system boot
- Provides log management and monitoring

**PM2** is the standard Node.js process manager.

### Install PM2

```bash
npm install -g pm2
```

### Start OpenClaw Under PM2

```bash
# Start OpenClaw as a managed process
pm2 start openclaw --name openclaw -- start

# Verify it is running
pm2 status

# Output:
# ┌─────┬──────────┬─────────────┬─────────┬─────────┬──────────┬────────┬──────┬───────────┬──────────┐
# │ id  │ name     │ namespace   │ version │ mode    │ pid      │ uptime │ ↺    │ status    │ cpu      │
# ├─────┼──────────┼─────────────┼─────────┼─────────┼──────────┼────────┼──────┼───────────┼──────────┤
# │ 0   │ openclaw │ default     │ N/A     │ fork    │ 12345    │ 5s     │ 0    │ online    │ 2%       │
# └─────┴──────────┴─────────────┴─────────┴─────────┴──────────┴────────┴──────┴───────────┴──────────┘
```

### PM2 Ecosystem File (Recommended)

For more control, create a PM2 ecosystem file:

```bash
nano ~/openclaw-ecosystem.config.js
```

```javascript
module.exports = {
  apps: [
    {
      name: "openclaw",
      script: "openclaw",
      args: "start",
      cwd: process.env.HOME,

      // Environment variables
      env: {
        NODE_ENV: "production",
        OPENCLAW_PORT: 18789,
        OPENCLAW_HOST: "0.0.0.0",
        OPENCLAW_LOG_LEVEL: "info",
        OLLAMA_BASE_URL: "http://localhost:11434",
        OPENCLAW_DISABLE_BONJOUR: "1",
      },

      // Restart policy
      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",
      restart_delay: 5000,        // Wait 5 seconds between restart attempts

      // Memory management
      max_memory_restart: "2G",   // Restart if memory exceeds 2 GB

      // Logging
      log_file: "~/.openclaw/logs/combined.log",
      out_file: "~/.openclaw/logs/out.log",
      error_file: "~/.openclaw/logs/error.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,

      // Watch for config changes (optional)
      watch: false,
    },
  ],
};
```

Start with the ecosystem file:

```bash
pm2 start ~/openclaw-ecosystem.config.js

# Or if already running, restart with new config
pm2 restart ~/openclaw-ecosystem.config.js
```

### Auto-Start on Boot

This is the critical step for 24/7 operation:

```bash
# Generate the startup script for macOS
pm2 startup

# PM2 will print a command like:
# sudo env PATH=$PATH:/Users/you/.nvm/versions/node/v22.x.x/bin pm2 startup launchd -u you --hp /Users/you
# RUN THAT COMMAND (copy-paste what PM2 prints)

# Save the current process list (so PM2 knows what to start on boot)
pm2 save
```

After running these commands, OpenClaw will automatically start when the Mac Mini boots up.

### Verify Auto-Start Works

```bash
# Reboot the Mac Mini
sudo reboot

# After reboot, SSH back in and check
pm2 status
# OpenClaw should show as "online"
```

---

## 6. PM2 Day-to-Day Commands

| Task                        | Command                           |
|-----------------------------|-----------------------------------|
| View all processes          | `pm2 status` or `pm2 list`       |
| View OpenClaw logs          | `pm2 logs openclaw`              |
| View last 200 log lines     | `pm2 logs openclaw --lines 200`  |
| Restart OpenClaw            | `pm2 restart openclaw`           |
| Stop OpenClaw               | `pm2 stop openclaw`              |
| Delete from PM2             | `pm2 delete openclaw`            |
| Monitor (real-time dashboard)| `pm2 monit`                     |
| Detailed process info       | `pm2 describe openclaw`          |
| Flush logs                  | `pm2 flush openclaw`             |
| Reset restart counter       | `pm2 reset openclaw`             |

---

## 7. Updating OpenClaw

### Standard Update

```bash
# Stop the current instance
pm2 stop openclaw

# Update the package
npm update -g openclaw@latest

# Restart
pm2 restart openclaw

# Verify the new version
openclaw --version
pm2 logs openclaw --lines 10
```

### Update to a Specific Version

```bash
pm2 stop openclaw
npm install -g openclaw@1.6.0
pm2 restart openclaw
```

### Rollback if Update Causes Issues

```bash
pm2 stop openclaw
npm install -g openclaw@1.5.2    # Previous working version
pm2 restart openclaw
```

---

## 8. Log Management

Without Docker's built-in log rotation, you need to manage logs yourself.

### PM2 Built-in Log Rotation

```bash
# Install PM2 log rotation module
pm2 install pm2-logrotate

# Configure rotation
pm2 set pm2-logrotate:max_size 50M       # Rotate when log reaches 50 MB
pm2 set pm2-logrotate:retain 10           # Keep 10 rotated files
pm2 set pm2-logrotate:compress true       # Compress old logs
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:rotateInterval '0 0 * * *'  # Rotate daily at midnight
```

### Manual Log Cleanup

```bash
# Check log sizes
du -sh ~/.openclaw/logs/*

# Flush all PM2 logs
pm2 flush

# Or truncate a specific log
> ~/.openclaw/logs/combined.log
```

---

## 9. Security Considerations for Native Install

Running OpenClaw natively means it operates with your user's full filesystem access. Take
these precautions:

### File Permissions

```bash
# Secure the config directory
chmod 700 ~/.openclaw
chmod 600 ~/.openclaw/.env

# Secure any API keys
chmod 600 ~/.openclaw/config/*
```

### Firewall

Ensure OpenClaw only listens on intended interfaces:

```bash
# In .env, bind to all interfaces only if you need remote access
OPENCLAW_HOST=0.0.0.0

# For local-only (most secure, but no remote access to the agent)
OPENCLAW_HOST=127.0.0.1
```

### Dedicated User (Advanced)

For stronger isolation, create a dedicated macOS user for OpenClaw:

```bash
# Create a user (via System Settings or command line)
sudo dscl . -create /Users/openclaw
sudo dscl . -create /Users/openclaw UserShell /bin/zsh
sudo dscl . -create /Users/openclaw UniqueID 550
sudo dscl . -create /Users/openclaw PrimaryGroupID 20
sudo dscl . -create /Users/openclaw NFSHomeDirectory /Users/openclaw
sudo mkdir -p /Users/openclaw
sudo chown openclaw:staff /Users/openclaw

# Then install Node.js and OpenClaw under that user
sudo -u openclaw bash -c 'curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash'
sudo -u openclaw bash -c 'source ~/.nvm/nvm.sh && nvm install 22 && npm install -g openclaw@latest pm2'
```

---

## 10. Monitoring

### Quick Health Check Script

Create a monitoring script:

```bash
nano ~/check-openclaw.sh
```

```bash
#!/bin/bash
# Quick health check for native OpenClaw installation

echo "=== OpenClaw Health Check ==="
echo ""

# PM2 Status
echo "--- PM2 Process Status ---"
pm2 jlist | jq '.[] | select(.name == "openclaw") | {name, status: .pm2_env.status, uptime: .pm2_env.pm_uptime, restarts: .pm2_env.restart_time, memory: .monit.memory, cpu: .monit.cpu}'
echo ""

# Health endpoint
echo "--- Gateway Health ---"
curl -s http://localhost:18789/health | jq . 2>/dev/null || echo "FAILED: Gateway not responding"
echo ""

# Ollama status
echo "--- Ollama Status ---"
curl -s http://localhost:11434/api/tags | jq '.models | length' 2>/dev/null && echo " models available" || echo "FAILED: Ollama not responding"
echo ""

# Port check
echo "--- Port Status ---"
lsof -i :18789 -P -n | head -3
echo ""

# Disk space
echo "--- Disk Space ---"
df -h / | tail -1 | awk '{print "Used: " $3 " / " $2 " (" $5 " full)"}'
echo ""

# Memory
echo "--- Memory Pressure ---"
memory_pressure | head -1
```

```bash
chmod +x ~/check-openclaw.sh
```

Run anytime: `~/check-openclaw.sh`

---

## Next Steps

- [Environment Variables](environment-variables.md) - Full configuration reference
- [Verification Tests](verification-tests.md) - Test the complete installation
- [Docker Installation](docker-installation.md) - Alternative: containerized deployment

# Docker Hardening for OpenClaw

> Docker is the RECOMMENDED installation method for OpenClaw. Running OpenClaw on bare metal gives the agent direct access to your host operating system, files, and credentials. Docker provides a security boundary -- not perfect, but significantly better than nothing.

---

## Why Docker Is Non-Negotiable for Security

| Bare Metal Risk | Docker Mitigation |
|---|---|
| Agent can access all files on your Mac Mini | Agent only sees mounted volumes |
| Agent can run any command as your user | Agent runs as non-root with dropped capabilities |
| Agent can read macOS Keychain | Agent has no access to host keychain |
| Agent can install software system-wide | Read-only filesystem prevents persistent changes |
| Agent can access host network | Isolated Docker network; no host networking |
| Compromised agent = compromised host | Compromised agent = compromised container (recoverable) |

**Bottom line:** Docker will not prevent all attacks, but it makes the difference between "wipe and rebuild your entire Mac" and "delete the container and restart."

---

## Security Directives Reference

### 1. Run as Non-Root User

By default, containers run as root. This is dangerous -- if the agent escapes the container, it escapes as root.

```yaml
services:
  openclaw:
    user: "1000:1000"  # Run as non-root UID/GID
```

**Why this matters:** Even inside the container, root can modify system files, install packages, and potentially exploit kernel vulnerabilities. A non-root user has limited blast radius.

**Verify it works:**
```bash
docker exec openclaw whoami
# Should NOT return "root"
docker exec openclaw id
# Should return uid=1000 gid=1000
```

---

### 2. Read-Only Filesystem

Prevent the agent from writing to the container filesystem. This stops malware installation, configuration tampering, and persistent backdoors.

```yaml
services:
  openclaw:
    read_only: true
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
      - /var/tmp:size=50M,noexec,nosuid,nodev
```

**What `tmpfs` does:** Some applications need to write temporary files. `tmpfs` provides a RAM-based writable directory that:
- Is destroyed when the container stops (no persistence for malware)
- Has size limits (prevents disk-filling attacks)
- Has `noexec` flag (prevents executing binaries written to it)
- Has `nosuid` flag (prevents privilege escalation)

**Note:** OpenClaw may need write access to specific directories (data, logs, workspace). Mount those as named volumes rather than making the entire filesystem writable.

---

### 3. Drop All Capabilities

Linux capabilities are fine-grained root powers. Drop them all, then add back only what is strictly needed.

```yaml
services:
  openclaw:
    cap_drop:
      - ALL
    cap_add: []  # Add specific capabilities ONLY if OpenClaw fails without them
```

**Capabilities you are dropping (and why that is good):**

| Capability | What It Allows | Why Drop It |
|---|---|---|
| NET_RAW | Raw socket access | Prevents network sniffing/spoofing |
| SYS_ADMIN | Broad system administration | Prevents mount, namespace, and cgroup manipulation |
| NET_ADMIN | Network configuration | Prevents firewall/routing changes |
| SYS_PTRACE | Process tracing | Prevents debugging/inspecting other processes |
| MKNOD | Device file creation | Prevents device access |
| DAC_OVERRIDE | Bypass file permissions | Prevents reading files the user should not access |

**If OpenClaw fails to start after dropping all capabilities:** Add back one at a time and document which were needed and why. Common requirements:
- `CHOWN` -- if the entrypoint needs to fix file ownership
- `SETUID`/`SETGID` -- if the entrypoint switches users

---

### 4. No New Privileges

Prevent processes inside the container from gaining additional privileges through setuid binaries or other escalation techniques.

```yaml
services:
  openclaw:
    security_opt:
      - no-new-privileges:true
```

**What this prevents:** Even if an attacker gets code execution inside the container, they cannot use setuid/setgid binaries (like `sudo`, `su`, or custom exploits) to escalate to root.

---

### 5. Resource Limits

Prevent runaway containers from consuming all host resources (e.g., an infinite loop in an agent).

```yaml
services:
  openclaw:
    deploy:
      resources:
        limits:
          memory: 4G      # Hard cap; container killed if exceeded (OOM)
          cpus: "2.0"     # Max 2 CPU cores
        reservations:
          memory: 1G      # Guaranteed minimum
          cpus: "0.5"     # Guaranteed minimum
    # Also set pids limit to prevent fork bombs
    pids_limit: 200
```

**Tuning guidance:**
- **Memory:** OpenClaw with browser control needs 2-4 GB. Start with 4G and monitor with `docker stats`.
- **CPU:** 2 cores is generous for most agent tasks. Reduce to 1.0 if you need host resources for other work.
- **PIDs:** 200 is generous. A fork bomb or runaway process spawner will hit this before damaging the host.

---

### 6. Network Isolation

Never use `network_mode: host`. Always use a custom bridge network.

```yaml
networks:
  openclaw-net:
    driver: bridge
    internal: false  # Set to true if OpenClaw does not need internet access
    # (unlikely -- it needs to call APIs)

services:
  openclaw:
    networks:
      - openclaw-net
    # NEVER do this:
    # network_mode: host  # DANGEROUS: container shares host network stack
```

**Why `host` networking is dangerous:**
- Container can bind to any port on the host
- Container can see all host network traffic
- Container can access services bound to localhost on the host
- Completely defeats network isolation

**If OpenClaw needs to communicate with other containers** (e.g., a database):
```yaml
services:
  openclaw:
    networks:
      - openclaw-net

  postgres:
    networks:
      - openclaw-net
    # Postgres only accessible from openclaw-net, not from host or internet
```

---

## Volume Mount Security

### Principles
1. Mount only directories the agent actually needs
2. Use `:ro` (read-only) for everything the agent should not modify
3. Never mount the Docker socket (`/var/run/docker.sock`) -- this gives full host control
4. Never mount your home directory or root filesystem

### Safe Volume Configuration

```yaml
volumes:
  openclaw-data:      # Named volume for persistent data
  openclaw-workspace:  # Named volume for agent workspace

services:
  openclaw:
    volumes:
      # Agent data (read-write, agent needs to persist state)
      - openclaw-data:/app/data

      # Agent workspace (read-write, agent works here)
      - openclaw-workspace:/app/workspace

      # Configuration (read-only, agent should not modify config)
      - ./config:/app/config:ro

      # Skills (read-only unless you want the agent to create skills)
      - ./skills:/app/skills:ro

      # DANGEROUS - DO NOT DO THESE:
      # - /:/host              # Host root filesystem
      # - ~/:/home/user        # Your entire home directory
      # - /var/run/docker.sock:/var/run/docker.sock  # Docker socket
      # - .env:/app/.env       # Mount env file directly (use env_file instead)
```

### Docker Socket Warning

```
NEVER mount the Docker socket into the OpenClaw container.

/var/run/docker.sock gives FULL CONTROL over Docker on the host.
An agent with Docker socket access can:
  - Start new privileged containers
  - Mount the host filesystem
  - Execute commands on the host
  - Effectively become root on your Mac Mini

This is equivalent to giving the agent root access to your machine.
```

---

## Secrets Management

### Option 1: Environment File (Simpler, Good Enough for Personal Use)

```yaml
services:
  openclaw:
    env_file:
      - .env  # Contains API keys
```

Your `.env` file:
```bash
# .env - NEVER commit this to git
GHL_API_KEY=your-ghl-key-here
CLAY_API_KEY=your-clay-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
CLAUDE_API_KEY=sk-ant-your-key-here
AIRTABLE_API_KEY=pat-your-key-here
```

**Security measures for `.env`:**
```bash
# Set restrictive permissions (macOS/Linux)
chmod 600 .env

# Verify permissions
ls -la .env
# Should show: -rw------- (only owner can read/write)

# Add to .gitignore (CRITICAL)
echo ".env" >> .gitignore

# Verify it is ignored
git status  # .env should NOT appear
```

### Option 2: Docker Secrets (More Secure, More Complex)

Docker secrets are stored encrypted and only mounted as files inside containers that need them.

```yaml
secrets:
  ghl_api_key:
    file: ./secrets/ghl_api_key.txt
  claude_api_key:
    file: ./secrets/claude_api_key.txt
  supabase_key:
    file: ./secrets/supabase_key.txt

services:
  openclaw:
    secrets:
      - ghl_api_key
      - claude_api_key
      - supabase_key
    environment:
      # Tell the app to read from secret files
      GHL_API_KEY_FILE: /run/secrets/ghl_api_key
      CLAUDE_API_KEY_FILE: /run/secrets/claude_api_key
      SUPABASE_KEY_FILE: /run/secrets/supabase_key
```

**Note:** Docker secrets in `docker compose` (non-Swarm) are essentially bind-mounted files. The security improvement is marginal over `env_file` for personal use. The real benefit comes in Swarm mode where secrets are encrypted in transit and at rest. For personal deployment, `env_file` with proper permissions is sufficient.

---

## Container Scanning

### Trivy (Recommended -- Free, Fast, Comprehensive)

```bash
# Install Trivy
brew install trivy

# Scan the OpenClaw image for vulnerabilities
trivy image openclaw/openclaw:latest

# Scan with severity filter (only HIGH and CRITICAL)
trivy image --severity HIGH,CRITICAL openclaw/openclaw:latest

# Scan your docker-compose.yml for misconfigurations
trivy config docker-compose.yml

# Scan before every update
trivy image openclaw/openclaw:new-version
```

### Docker Scout (Built into Docker Desktop)

```bash
# Quick vulnerability overview
docker scout quickview openclaw/openclaw:latest

# Detailed CVE list
docker scout cves openclaw/openclaw:latest

# Compare two versions before upgrading
docker scout compare openclaw/openclaw:new-version --to openclaw/openclaw:current-version
```

### Scanning Schedule

| When | What to Scan | Tool |
|---|---|---|
| Before first deployment | OpenClaw image + all dependency images | Trivy |
| Before every update | New image version vs. current | Docker Scout compare |
| Weekly (automated) | All running images | Trivy (cron job) |
| After security advisory | Specific image/CVE | Trivy with `--severity CRITICAL` |

---

## Complete Hardened docker-compose.yml

```yaml
# docker-compose.yml -- Hardened OpenClaw Deployment
# Last reviewed: [DATE]
#
# SECURITY NOTES:
# - All capabilities dropped; add back ONLY if OpenClaw fails to start
# - Filesystem is read-only; tmpfs for temp files
# - Non-root user; no privilege escalation
# - Resource limits prevent runaway processes
# - Network isolated; no host networking
# - Secrets via env_file with chmod 600

version: "3.8"

networks:
  openclaw-net:
    driver: bridge

volumes:
  openclaw-data:
  openclaw-workspace:
  openclaw-logs:

services:
  openclaw:
    image: openclaw/openclaw:latest  # Pin to specific version in production
    container_name: openclaw
    restart: unless-stopped

    # --- USER ---
    user: "1000:1000"

    # --- FILESYSTEM ---
    read_only: true
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
      - /var/tmp:size=50M,noexec,nosuid,nodev

    # --- CAPABILITIES ---
    cap_drop:
      - ALL
    # cap_add:
    #   - CHOWN      # Uncomment ONLY if entrypoint needs it
    #   - SETUID     # Uncomment ONLY if entrypoint needs it
    #   - SETGID     # Uncomment ONLY if entrypoint needs it

    # --- PRIVILEGES ---
    security_opt:
      - no-new-privileges:true

    # --- RESOURCES ---
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: "2.0"
        reservations:
          memory: 1G
          cpus: "0.5"
    pids_limit: 200

    # --- NETWORK ---
    networks:
      - openclaw-net
    ports:
      - "127.0.0.1:3000:3000"    # Web UI -- localhost only
      - "127.0.0.1:18789:18789"  # Gateway -- localhost only
    # NOTE: Binding to 127.0.0.1 means only local access.
    # Tailscale will provide remote access securely.

    # --- VOLUMES ---
    volumes:
      - openclaw-data:/app/data
      - openclaw-workspace:/app/workspace
      - openclaw-logs:/app/logs
      - ./config:/app/config:ro
      - ./skills:/app/skills:ro

    # --- SECRETS ---
    env_file:
      - .env

    # --- ENVIRONMENT ---
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info  # Not debug (debug may log sensitive data)
      - OPENCLAW_DISABLE_BONJOUR=1  # Prevent network discovery

    # --- HEALTH CHECK ---
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # --- LOGGING ---
    logging:
      driver: "json-file"
      options:
        max-size: "10m"   # Rotate logs at 10 MB
        max-file: "3"     # Keep 3 rotated log files
        # Total max log storage: 30 MB
```

---

## Logging Security

### Problem: Sensitive Data in Logs

Agent logs can contain:
- API keys (if the agent prints environment variables)
- Client data (names, emails, phone numbers from GHL)
- Conversation content (potentially confidential)
- Internal system paths and configurations

### Solutions

**1. Set log level to `info` (not `debug`) in production:**
```yaml
environment:
  - LOG_LEVEL=info
```
Debug logging often includes full request/response bodies that contain API keys and personal data.

**2. Configure log rotation (already in the compose file above):**
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```
This prevents unbounded log growth and limits the window of sensitive data exposure.

**3. Review logs for sensitive data:**
```bash
# Search for potential API key leaks in logs
docker logs openclaw 2>&1 | grep -i "api.key\|api_key\|secret\|token\|password\|sk-ant\|pat-"

# If you find sensitive data in logs, the agent or a skill is logging it.
# Fix the source, then clear old logs:
docker compose down
docker volume rm $(docker volume ls -q -f name=openclaw-logs)
docker compose up -d
```

**4. If you need to forward logs to a service (e.g., for monitoring):**
- Filter sensitive patterns before forwarding
- Use a log aggregator that supports redaction rules
- Never forward debug-level logs externally

---

## Post-Deployment Verification

Run these checks after deploying the hardened configuration:

```bash
# 1. Verify non-root user
docker exec openclaw id
# Expected: uid=1000 gid=1000

# 2. Verify read-only filesystem
docker exec openclaw touch /test-file 2>&1
# Expected: "Read-only file system" error

# 3. Verify tmpfs is writable (agent needs temp files)
docker exec openclaw touch /tmp/test-file
# Expected: success (no error)

# 4. Verify capabilities are dropped
docker exec openclaw cat /proc/1/status | grep -i cap
# CapBnd should be 0000000000000000 (or very low)

# 5. Verify resource limits
docker stats openclaw --no-stream
# Memory limit should show 4GiB

# 6. Verify network isolation
docker exec openclaw ping -c 1 host.docker.internal 2>&1
# This tests if the container can reach the host; behavior depends on config

# 7. Verify ports are bound to localhost only
docker port openclaw
# Should show 127.0.0.1:3000 and 127.0.0.1:18789 (NOT 0.0.0.0)
```

---

## Quick Reference: Security Directives

| Directive | What It Does | Priority |
|---|---|---|
| `user: "1000:1000"` | Non-root execution | CRITICAL |
| `read_only: true` | Immutable filesystem | HIGH |
| `cap_drop: [ALL]` | Remove all Linux capabilities | HIGH |
| `no-new-privileges:true` | Block privilege escalation | HIGH |
| `memory: 4G` | Hard memory limit | MEDIUM |
| `cpus: "2.0"` | CPU throttle | MEDIUM |
| `pids_limit: 200` | Fork bomb protection | MEDIUM |
| `127.0.0.1:PORT:PORT` | Localhost-only port binding | CRITICAL |
| `tmpfs` with `noexec` | Safe temp storage | MEDIUM |
| `logging.max-size` | Log rotation | MEDIUM |

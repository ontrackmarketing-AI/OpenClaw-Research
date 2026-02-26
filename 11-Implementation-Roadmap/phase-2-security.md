# Phase 2 - Security Hardening (Week 1-2)

## Goal

Secure the OpenClaw installation so you can trust it with API keys, client data, and automated operations. By the end of this phase, all access is restricted to your devices via Tailscale VPN, credentials are properly isolated, and sensitive operations require your explicit approval.

---

## Why This Phase Matters

OpenClaw will hold:
- API keys worth hundreds of dollars per month (Anthropic, Clay, GHL)
- Client business data (contact info, revenue data, marketing performance)
- Automated actions that cost money (API calls, sending messages)

A misconfigured system could expose these to the internet or allow runaway spending. Spend the time to lock it down properly now.

---

## Day 1-2: Docker Hardening

### Update docker-compose.yml with Security Directives

Replace your Phase 1 docker-compose.yml with this hardened version:

```bash
cat > ~/.openclaw/docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    container_name: openclaw
    restart: unless-stopped

    # Run as non-root user
    user: "1000:1000"

    # Security options
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if binding to ports < 1024

    # Read-only root filesystem where possible
    read_only: true
    tmpfs:
      - /tmp:size=100M,noexec,nosuid

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '4.0'        # Max 4 CPU cores (M4 Pro has 12-14)
          memory: 8G          # Max 8GB RAM (machine has 24GB+)
        reservations:
          cpus: '1.0'
          memory: 2G

    ports:
      - "127.0.0.1:18789:18789"   # Gateway - localhost only
      - "127.0.0.1:3000:3000"     # Web UI - localhost only
    # NOTE: Binding to 127.0.0.1 means ONLY the Mac Mini itself
    # can access these ports. Tailscale will handle remote access.

    volumes:
      - ./config:/app/config:ro        # Config is read-only
      - ./memory:/app/memory:rw        # Memory needs write access
      - ./skills:/app/skills:ro        # Skills are read-only
      - ./data:/app/data:rw            # Data needs write access
      - ./logs:/app/logs:rw            # Logs need write access
      - ./assets:/app/assets:ro        # Assets are read-only

    env_file:
      - .env

    environment:
      - NODE_ENV=production
      - OPENCLAW_HOST=0.0.0.0
      - OPENCLAW_PORT=18789

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18789/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"

    networks:
      - openclaw-network

networks:
  openclaw-network:
    driver: bridge
    internal: false  # Needs internet for API calls
COMPOSE
```

### Test Hardened Configuration

```bash
cd ~/.openclaw

# Stop the current container
docker compose down

# Fix permissions for the non-root user
sudo chown -R 1000:1000 ~/.openclaw/memory
sudo chown -R 1000:1000 ~/.openclaw/data
sudo chown -R 1000:1000 ~/.openclaw/logs

# Start with hardened config
docker compose up -d

# Verify container is running
docker compose ps

# Check health
docker compose logs --tail=20

# Test gateway still works
curl -s http://localhost:18789/health | jq .

# Test web UI still works (from Mac Mini's browser or via SSH tunnel)
# From Windows: ssh -L 3000:localhost:3000 user@mac-mini-ip
# Then browse to http://localhost:3000
```

### Verify Security Restrictions

```bash
# Verify running as non-root
docker exec openclaw whoami
# Should NOT be "root"

# Verify resource limits
docker stats openclaw --no-stream
# Should show memory limit of 8GB

# Verify ports are localhost-only
# From Windows PC, try direct access (should FAIL):
# curl http://192.168.1.200:18789/health
# This should timeout or refuse connection

# Verify read-only mounts
docker exec openclaw touch /app/config/test-file 2>&1
# Should get "Read-only file system" error

docker exec openclaw touch /app/memory/test-file 2>&1
# Should succeed (memory is writable)
docker exec openclaw rm /app/memory/test-file
```

---

## Day 3: Tailscale VPN

### Install Tailscale on Mac Mini

```bash
# Install Tailscale
brew install tailscale

# Start Tailscale service
sudo tailscaled &

# Authenticate (this will open a browser URL)
tailscale up

# Follow the URL to authenticate with your Tailscale account
# If no account, create one at https://tailscale.com (free for personal use)

# Verify Tailscale is running
tailscale status
# Note the Tailscale IP (e.g., 100.x.y.z)

# Get the MagicDNS hostname
tailscale status | grep $(hostname)
# Note the hostname (e.g., mac-mini.tailnet-name.ts.net)
```

### Install Tailscale on Windows PC

1. Download Tailscale from https://tailscale.com/download/windows
2. Install and sign in with the same account used on Mac Mini
3. Verify connection:

```powershell
# In PowerShell on Windows
tailscale status

# Test connectivity to Mac Mini via Tailscale
ping mac-mini  # or whatever hostname shows in tailscale status

# Test OpenClaw access via Tailscale
# Since we bound ports to 127.0.0.1, we need Tailscale Funnel or SSH tunnel
ssh -L 3000:localhost:3000 -L 18789:localhost:18789 user@mac-mini
# Now browse to http://localhost:3000 on Windows
```

### Install Tailscale on Phone

1. Install Tailscale from App Store (iOS) or Play Store (Android)
2. Sign in with same account
3. Verify connection: should see Mac Mini in device list

### Alternative: Bind Ports to Tailscale IP

Instead of SSH tunnels, you can bind OpenClaw ports to the Tailscale interface:

```bash
# Find your Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)
echo "Tailscale IP: $TAILSCALE_IP"

# Update docker-compose.yml ports to bind to Tailscale IP
# Replace the ports section with:
#    ports:
#      - "${TAILSCALE_IP}:18789:18789"
#      - "${TAILSCALE_IP}:3000:3000"
```

This makes OpenClaw accessible only via Tailscale, without needing SSH tunnels.

### Configure Tailscale ACLs

Log into https://login.tailscale.com/admin/acls and add restrictive rules:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": ["*:*"]
    }
  ],
  "tagOwners": {
    "tag:server": ["autogroup:owner"]
  }
}
```

This restricts access to only your devices. If you later add team members, create specific ACL rules for them.

### Verify Tailscale Access

```bash
# From Windows via Tailscale:
curl http://mac-mini:18789/health
# Should work

# From outside Tailscale (e.g., phone with Tailscale OFF):
# Try accessing http://192.168.1.200:18789
# Should FAIL (ports bound to localhost/Tailscale only)
```

---

## Day 4: Credential Management

### Create Dedicated API Keys

Do NOT reuse your personal API keys. Create new, limited keys for OpenClaw.

#### Anthropic API Key
1. Go to https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Name: `openclaw-production`
4. Set a spend limit: start with $50/month
5. Copy the key

#### GoHighLevel API Key
1. In GHL, go to Settings > API Keys
2. Create a new sub-account level key (not agency level)
3. Name: `openclaw-automation`
4. Permissions: only what OpenClaw needs (contacts, pipelines, conversations)
5. Copy the key

#### Clay.com API Key
1. Go to Clay workspace settings
2. Create an API key with budget limit
3. Name: `openclaw-enrichment`
4. Set monthly credit limit (e.g., 1000 credits)
5. Copy the key

#### Other Services
Create minimal-permission keys for each service:
- **ZeroBounce**: API key with limited credits
- **Google Places**: API key with daily quota limits
- **Any other services**: always minimum necessary permissions

### Update .env with Dedicated Credentials

```bash
# Back up existing .env
cp ~/.openclaw/.env ~/.openclaw/.env.backup

# Create new .env with all credentials
cat > ~/.openclaw/.env << 'ENV'
# ===========================================
# OpenClaw Production Environment
# Created: [DATE]
# Last Updated: [DATE]
# ===========================================

# Primary LLM - Claude API (dedicated key with $50/mo limit)
ANTHROPIC_API_KEY=sk-ant-openclaw-dedicated-key-here

# Local LLM - Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL_CHAT=qwen3:14b
OLLAMA_MODEL_EMBED=nomic-embed-text
OLLAMA_ENABLED=true

# GoHighLevel CRM (sub-account key, limited permissions)
GHL_API_KEY=your-ghl-sub-account-key-here
GHL_LOCATION_ID=your-location-id

# Clay.com Enrichment (budget-limited key)
CLAY_API_KEY=your-clay-budget-limited-key-here

# ZeroBounce Email Verification
ZEROBOUNCE_API_KEY=your-zerobounce-key-here

# Web UI
OPENCLAW_WEB_UI=true
OPENCLAW_WEB_PORT=3000

# Security
OPENCLAW_DISABLE_BONJOUR=1
OPENCLAW_AUTH_ENABLED=true
OPENCLAW_AUTH_SECRET=generate-a-random-64-char-string-here

# Logging
LOG_LEVEL=info
LOG_DIR=/app/logs

# Memory
MEMORY_DIR=/app/memory
ENV

# Secure the .env file (owner read/write only)
chmod 600 ~/.openclaw/.env

# Verify permissions
ls -la ~/.openclaw/.env
# Should show: -rw------- 1 yourusername ...
```

### Generate Auth Secret

```bash
# Generate a secure random string for OPENCLAW_AUTH_SECRET
openssl rand -hex 32
# Copy the output and paste into .env as OPENCLAW_AUTH_SECRET value
```

### Test All Integrations with New Credentials

```bash
# Restart OpenClaw with new credentials
cd ~/.openclaw && docker compose down && docker compose up -d

# Test Claude API
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test: respond with OK if you can hear me"}'

# Test Ollama
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?", "model": "local"}'

# Test GHL connection (when CRM skill is configured)
# Test Clay connection (when enrichment skill is configured)
# These will be validated in Phase 4 when skills are built
```

---

## Day 5: Network and Access Security

### Enable macOS Firewall

```bash
# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Enable stealth mode (don't respond to pings from unknown sources)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on

# Allow SSH (for your access)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/ssh

# Verify firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### Disable mDNS/Bonjour Discovery

This prevents OpenClaw from advertising itself on your local network:

```bash
# Already set in .env:
# OPENCLAW_DISABLE_BONJOUR=1

# Also disable at the OS level if desired
sudo defaults write /Library/Preferences/com.apple.mDNSResponder.plist NoMulticastAdvertisements -bool true
```

### Configure OpenClaw Authentication

Ensure the web UI requires login. This was configured in .env:
- `OPENCLAW_AUTH_ENABLED=true`
- `OPENCLAW_AUTH_SECRET=<your-generated-secret>`

Test authentication:
1. Open web UI at http://localhost:3000
2. Should see a login screen
3. Enter your configured credentials
4. Verify access is granted

### Verify No Public Exposure

```bash
# Check what ports are listening and on which interfaces
sudo lsof -i -P -n | grep LISTEN

# Verify OpenClaw ports are NOT on 0.0.0.0
# They should be on 127.0.0.1 or your Tailscale IP only

# Check from external device (phone without Tailscale):
# Try: http://192.168.1.200:3000
# Should NOT be accessible

# Check from an online port scanner (optional):
# Go to https://www.yougetsignal.com/tools/open-ports/
# Enter your public IP and check ports 3000, 18789
# Should show "Closed"
```

---

## Day 6-7: Human-in-the-Loop (HITL) Setup

### Why HITL is Critical

OpenClaw can take actions that:
- Cost money (API calls, sending messages)
- Affect clients (updating CRM data, sending emails)
- Are irreversible (deleting data, publishing content)

You MUST approve sensitive operations before they execute.

### Configure Action Approval

Create an approval configuration that defines which actions need human approval:

```bash
cat > ~/.openclaw/config/hitl-config.json << 'JSON'
{
  "approval_required": {
    "always": [
      "send_email",
      "send_sms",
      "send_whatsapp",
      "publish_content",
      "delete_contact",
      "bulk_update",
      "create_payment",
      "deploy_website",
      "linkedin_outreach",
      "api_call_over_1_dollar"
    ],
    "conditional": [
      {
        "action": "create_contact",
        "condition": "batch_size > 10",
        "reason": "Bulk contact creation needs review"
      },
      {
        "action": "update_contact",
        "condition": "fields_changed includes 'email' or 'phone'",
        "reason": "Contact info changes need review"
      },
      {
        "action": "enrichment",
        "condition": "estimated_cost > 5.00",
        "reason": "Expensive enrichment batches need approval"
      }
    ],
    "never_required": [
      "read_contact",
      "search_contacts",
      "generate_report",
      "memory_operations",
      "local_model_queries"
    ]
  },
  "notification_channel": "telegram",
  "approval_timeout_minutes": 60,
  "default_on_timeout": "deny"
}
JSON
```

### Set Up Telegram Notifications

Telegram is the recommended notification channel because it works on all your devices and supports interactive buttons for approval.

```bash
# 1. Create a Telegram bot
# Open Telegram and message @BotFather
# Send: /newbot
# Name: OpenClaw Approvals
# Username: openclaw_approvals_bot (must be unique)
# Copy the bot token

# 2. Get your Telegram chat ID
# Message your new bot with /start
# Then visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
# Find your chat_id in the response

# 3. Add to .env
cat >> ~/.openclaw/.env << 'ENV'

# Telegram Notifications (HITL approvals)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
TELEGRAM_CHAT_ID=your-chat-id-here
NOTIFICATION_CHANNEL=telegram
ENV

# 4. Restart OpenClaw
cd ~/.openclaw && docker compose restart
```

### Test Approval Flow End-to-End

```bash
# Trigger an action that requires approval
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Send a test email to test@example.com saying hello"}'

# Expected flow:
# 1. OpenClaw recognizes this needs approval (send_email is in "always" list)
# 2. You receive a Telegram notification with details
# 3. Telegram shows Approve / Deny buttons
# 4. You tap Approve
# 5. OpenClaw executes the action (or simulates in test mode)
# 6. Confirmation sent back to Telegram

# Verify: check Telegram for the notification
# Verify: tap Approve and check OpenClaw logs
docker compose logs --tail=20 | grep -i approval
```

### Configure Emergency Stop

```bash
cat > ~/.openclaw/config/emergency-stop.json << 'JSON'
{
  "emergency_stop": {
    "telegram_command": "/stop",
    "web_ui_button": true,
    "api_endpoint": "/api/emergency-stop",
    "actions_on_stop": [
      "cancel_all_pending_actions",
      "pause_all_scheduled_tasks",
      "send_confirmation_notification",
      "log_stop_event"
    ],
    "resume_requires": "manual_web_ui_confirmation"
  }
}
JSON
```

Test emergency stop:
1. Send `/stop` to the Telegram bot
2. Verify all pending actions are cancelled
3. Verify scheduled tasks are paused
4. Resume via web UI

### Document Security Configuration

```bash
cat > ~/.openclaw/SECURITY-CONFIG.md << 'LOG'
# OpenClaw Security Configuration

## Access Control
- All ports bound to localhost or Tailscale IP only
- Web UI requires authentication
- Tailscale VPN required for all remote access
- macOS firewall enabled with stealth mode

## Credentials
- All API keys are OpenClaw-dedicated (not personal keys)
- Anthropic: $50/month spend limit
- Clay: credit-limited workspace
- GHL: sub-account level permissions only
- .env file: chmod 600 (owner read/write only)

## Human-in-the-Loop
- All outbound communications require approval
- All destructive operations require approval
- Expensive operations (>$5) require approval
- Approval via Telegram with 60-minute timeout
- Default on timeout: DENY

## Emergency Stop
- Telegram: /stop command
- Web UI: emergency stop button
- API: POST /api/emergency-stop
- Requires manual web UI confirmation to resume

## Docker Security
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped all capabilities (except NET_BIND_SERVICE)
- Resource limits: 4 CPUs, 8GB RAM
- no-new-privileges flag enabled

## Network
- mDNS/Bonjour disabled
- No ports exposed to public internet
- Firewall stealth mode enabled

## Review Schedule
- Monthly security audit (1st of each month)
- Credential rotation: quarterly
- Access log review: weekly
LOG
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| Docker running as non-root | `docker exec openclaw whoami` != root | [ ] |
| Read-only config mount | `docker exec openclaw touch /app/config/x` fails | [ ] |
| Resource limits set | `docker stats` shows limits | [ ] |
| Ports not publicly accessible | Cannot access from non-Tailscale device | [ ] |
| Tailscale VPN working | Access from Windows and phone via Tailscale | [ ] |
| Dedicated API keys configured | Each service has its own key | [ ] |
| .env file secured | `ls -la .env` shows `-rw-------` | [ ] |
| Web UI authentication working | Login required to access UI | [ ] |
| Firewall enabled | `socketfilterfw --getglobalstate` shows enabled | [ ] |
| mDNS disabled | `OPENCLAW_DISABLE_BONJOUR=1` in .env | [ ] |
| HITL configured | Approval required for sensitive actions | [ ] |
| Telegram notifications working | Receive approval requests on phone | [ ] |
| Emergency stop working | `/stop` command halts all operations | [ ] |

---

## Next Phase

With security hardened, proceed to [Phase 3 - Memory System & RAG](phase-3-memory-rag.md). The security foundation built here protects everything you add from this point forward.

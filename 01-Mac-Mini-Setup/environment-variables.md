# Environment Variables Reference for OpenClaw

## Overview

OpenClaw is configured primarily through environment variables stored in a `.env` file. This
document provides the complete reference for all configuration variables, organized by
category. Each variable includes its purpose, default value, whether it is required, and
example usage.

---

## Where to Store Your .env File

| Installation Method | .env Location                  | Notes                               |
|---------------------|-------------------------------|--------------------------------------|
| Docker Compose      | `~/openclaw/.env`             | Referenced by `env_file:` in compose |
| Native (npm)        | `~/.openclaw/.env`            | Loaded by OpenClaw on startup        |
| PM2 Ecosystem       | Defined in ecosystem.config.js | Variables in the `env:` block       |

### Security Rules

1. **Never commit `.env` to version control.** Add it to `.gitignore`.
2. **Set restrictive permissions:** `chmod 600 .env`
3. **Use `.env.example` as a template** -- commit this with placeholder values for reference.
4. **For production secrets,** see the credential management practices at the end of this
   document.

---

## Complete .env Template

Copy this template and fill in the values relevant to your setup. Lines starting with `#` are
comments. Uncomment variables as needed.

```bash
# =============================================================================
# OPENCLAW ENVIRONMENT CONFIGURATION
# =============================================================================
# Copy this file to .env and fill in your values.
# Required variables are marked with [REQUIRED].
# All others are optional with sensible defaults.
# =============================================================================


# =============================================================================
# CORE SETTINGS
# =============================================================================

# Port for the Gateway WebSocket server [REQUIRED]
OPENCLAW_PORT=18789

# Host/interface to bind to
# Use 0.0.0.0 for all interfaces (needed for Docker or remote access)
# Use 127.0.0.1 for local-only access (most secure)
OPENCLAW_HOST=0.0.0.0

# Logging level: error, warn, info, debug, trace
OPENCLAW_LOG_LEVEL=info

# Node environment
NODE_ENV=production


# =============================================================================
# LLM PROVIDERS
# =============================================================================
# Configure at least one LLM provider. You can configure multiple and switch
# between them per-agent or per-skill.

# --- Anthropic (Claude) ---
# Get your key at: https://console.anthropic.com/
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- OpenAI (GPT-4, etc.) ---
# Get your key at: https://platform.openai.com/api-keys
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Ollama (Local LLMs) ---
# For native install, Ollama is on localhost:
OLLAMA_BASE_URL=http://localhost:11434
# For Docker install, use the host bridge:
# OLLAMA_BASE_URL=http://host.docker.internal:11434

# --- Google Gemini ---
# Get your key at: https://aistudio.google.com/app/apikey
# GOOGLE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- OpenRouter (Multi-provider proxy) ---
# Get your key at: https://openrouter.ai/keys
# OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Custom OpenAI-compatible endpoint ---
# For self-hosted models (vLLM, text-generation-inference, etc.)
# CUSTOM_LLM_BASE_URL=http://localhost:8080/v1
# CUSTOM_LLM_API_KEY=not-needed


# =============================================================================
# MODEL SELECTION
# =============================================================================
# Default model used when no specific model is requested.
# Format: provider/model-name

# Default model for general agent tasks
OPENCLAW_DEFAULT_MODEL=ollama/qwen3:14b

# Optional: Override models for specific task types
# OPENCLAW_TRIAGE_MODEL=ollama/qwen3:8b
# OPENCLAW_REASONING_MODEL=ollama/deepseek-r1:14b
# OPENCLAW_CODE_MODEL=ollama/codellama:13b
# OPENCLAW_EMBEDDING_MODEL=ollama/nomic-embed-text


# =============================================================================
# SECURITY
# =============================================================================

# Disable Bonjour/mDNS service advertisement
# Set to 1 on servers to prevent the Mac from advertising OpenClaw on the network
OPENCLAW_DISABLE_BONJOUR=1

# Authentication token for the Gateway API
# All clients must include this token to connect
# Generate with: openssl rand -hex 32
# OPENCLAW_AUTH_TOKEN=your-64-char-hex-token-here

# CORS allowed origins (comma-separated)
# OPENCLAW_CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Rate limiting (requests per minute per client)
# OPENCLAW_RATE_LIMIT=60

# Enable/disable the Web UI
# OPENCLAW_WEB_UI_ENABLED=true


# =============================================================================
# MEMORY AND STORAGE
# =============================================================================

# Directory for agent memory storage
# Docker: mapped via volume mount in docker-compose.yml
# Native: defaults to ~/.openclaw/memory
OPENCLAW_MEMORY_DIR=~/.openclaw/memory

# SQLite database path for structured memory
OPENCLAW_SQLITE_PATH=~/.openclaw/memory/openclaw.db

# Memory search strategy: sqlite, vector, hybrid
# OPENCLAW_MEMORY_STRATEGY=hybrid

# Maximum memory entries to retain (0 = unlimited)
# OPENCLAW_MEMORY_MAX_ENTRIES=100000


# =============================================================================
# CHANNEL INTEGRATIONS
# =============================================================================
# OpenClaw can connect to messaging platforms as communication channels.
# Configure the tokens for each channel you want to use.

# --- WhatsApp (via WhatsApp Business API / Cloud API) ---
# WHATSAPP_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# WHATSAPP_PHONE_NUMBER_ID=123456789012345
# WHATSAPP_VERIFY_TOKEN=your-webhook-verify-token
# WHATSAPP_WEBHOOK_URL=https://yourdomain.com/webhook/whatsapp

# --- Telegram ---
# Get a bot token from @BotFather on Telegram
# TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# --- Discord ---
# Create a bot at: https://discord.com/developers/applications
# DISCORD_BOT_TOKEN=MTIzxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# DISCORD_CLIENT_ID=123456789012345678

# --- Slack ---
# Create a Slack app at: https://api.slack.com/apps
# SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
# SLACK_SIGNING_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# SLACK_APP_TOKEN=xapp-x-xxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx

# --- Email (IMAP/SMTP) ---
# EMAIL_IMAP_HOST=imap.gmail.com
# EMAIL_IMAP_PORT=993
# EMAIL_SMTP_HOST=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_USER=your-email@gmail.com
# EMAIL_PASSWORD=your-app-password
# EMAIL_FROM_NAME=OpenClaw Agent


# =============================================================================
# THIRD-PARTY INTEGRATIONS
# =============================================================================
# API keys for services that OpenClaw skills can interact with.

# --- GoHighLevel (GHL) ---
# AGENCY_API_KEY=your-ghl-agency-api-key
# GHL_API_KEY=your-ghl-location-api-key
# GHL_LOCATION_ID=your-ghl-location-id

# --- Clay ---
# CLAY_API_KEY=your-clay-api-key

# --- Supabase ---
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx
# SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx

# --- Airtable ---
# AIRTABLE_API_KEY=patXXXXXXXXXXXXXX.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Notion ---
# NOTION_API_KEY=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- GitHub ---
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Serper (Web Search) ---
# SERPER_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Firecrawl (Web Scraping) ---
# FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- AWS ---
# AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
# AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# AWS_REGION=us-east-1

# --- Stripe ---
# STRIPE_SECRET_KEY=<your-stripe-secret-key>
# STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx


# =============================================================================
# PERFORMANCE AND LIMITS
# =============================================================================

# Maximum concurrent agent sessions
# Adjust based on your hardware and expected load
OPENCLAW_MAX_CONCURRENT_AGENTS=5

# Memory limit for the Node.js process (in MB)
# Default is typically fine; increase if you see OOM errors
OPENCLAW_MEMORY_LIMIT=2048

# Agent execution timeout (in seconds)
# Maximum time an agent can run a single task before being terminated
# OPENCLAW_AGENT_TIMEOUT=300

# WebSocket ping interval (in seconds)
# OPENCLAW_WS_PING_INTERVAL=30

# Maximum message size (in bytes)
# OPENCLAW_MAX_MESSAGE_SIZE=10485760

# Worker thread pool size
# OPENCLAW_WORKER_THREADS=4


# =============================================================================
# SKILL CONFIGURATION
# =============================================================================

# Directory for custom skills
# OPENCLAW_SKILLS_DIR=~/.openclaw/skills

# Enable/disable specific built-in skills
# OPENCLAW_ENABLE_WEB_BROWSING=true
# OPENCLAW_ENABLE_CODE_EXECUTION=true
# OPENCLAW_ENABLE_FILE_OPERATIONS=true

# Sandboxed code execution
# OPENCLAW_CODE_SANDBOX=true
# OPENCLAW_CODE_TIMEOUT=30


# =============================================================================
# OBSERVABILITY
# =============================================================================

# Enable structured JSON logging (useful for log aggregation)
# OPENCLAW_JSON_LOGS=false

# Enable request/response logging (verbose, for debugging)
# OPENCLAW_LOG_REQUESTS=false

# Webhook for alerts (e.g., Slack incoming webhook for error notifications)
# OPENCLAW_ALERT_WEBHOOK=<your-slack-webhook-url>
```

---

## Variable Quick Reference

### Required Variables

These must be set for OpenClaw to function:

| Variable              | Purpose                              | Example                       |
|-----------------------|--------------------------------------|-------------------------------|
| `OPENCLAW_PORT`       | Gateway WebSocket port               | `18789`                       |
| At least one LLM key  | LLM provider for agent intelligence | `OLLAMA_BASE_URL` or an API key |

### Most Important Optional Variables

| Variable                        | Default     | Purpose                                  |
|---------------------------------|-------------|------------------------------------------|
| `OPENCLAW_HOST`                 | `0.0.0.0`  | Network interface to bind                |
| `OPENCLAW_LOG_LEVEL`            | `info`      | Logging verbosity                        |
| `OPENCLAW_DEFAULT_MODEL`        | (none)      | Default LLM for agent tasks              |
| `OPENCLAW_AUTH_TOKEN`           | (none)      | API authentication (strongly recommended)|
| `OPENCLAW_DISABLE_BONJOUR`     | `0`         | Disable network service advertisement   |
| `OPENCLAW_MEMORY_DIR`          | `~/.openclaw/memory` | Agent memory storage path       |
| `OPENCLAW_MAX_CONCURRENT_AGENTS`| `5`        | Parallel agent session limit             |

---

## Credential Management Best Practices

### Do Not Put Secrets in These Places

- **Git repositories** (even private ones -- secrets leak in history)
- **Docker images** (baked-in secrets persist in image layers)
- **Shell history** (avoid `export API_KEY=xxx` directly in terminal)
- **Shared documents or chat** (Slack, email, etc.)

### Recommended Practices

1. **Use `.env` files with restrictive permissions:**
   ```bash
   chmod 600 ~/.openclaw/.env
   ```

2. **Use `.env.example` for documentation:**
   Create a `.env.example` with placeholder values and commit it. Never commit `.env`.

3. **Rotate API keys periodically:**
   Set a quarterly reminder to rotate Anthropic, OpenAI, and other API keys.

4. **Use environment-specific files:**
   ```
   .env.development   # Local development values
   .env.production    # Production secrets (chmod 600)
   .env.example       # Template with placeholders (committed to git)
   ```

5. **For team environments, use a secrets manager:**
   - macOS Keychain (for single-machine setups)
   - 1Password CLI or Bitwarden CLI (for team access)
   - HashiCorp Vault (for enterprise setups)

6. **Audit which keys have access to what:**
   - Create dedicated API keys for OpenClaw (not your personal keys)
   - Use the minimum required permissions/scopes
   - Label keys clearly (e.g., "OpenClaw Mac Mini Production")

---

## Generating Secure Tokens

```bash
# Generate a 64-character hex token for OPENCLAW_AUTH_TOKEN
openssl rand -hex 32

# Generate a random password for database or service accounts
openssl rand -base64 24

# Generate a UUID
uuidgen
```

---

## Next Steps

- [Verification Tests](verification-tests.md) - Test your configuration
- [Docker Installation](docker-installation.md) - Docker-specific .env usage
- [Native Installation](native-installation.md) - Native-specific .env usage

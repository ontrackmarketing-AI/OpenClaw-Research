# Phase 1: Secure Infrastructure - Research

**Researched:** 2026-02-28
**Domain:** Docker orchestration, container security, n8n workflow proxy, VPN networking, cost controls, context window safety
**Confidence:** HIGH

## Summary

Phase 1 builds the hardened Docker stack (OpenClaw, PostgreSQL 16, Redis 7, Qdrant, n8n) on the Mac Mini M4 Pro, then layers on six security controls: VPN-gated access (Tailscale), API key isolation (n8n proxy), HITL tier enforcement, cost circuit breakers, content sanitization, and context window safety. The machine already has Docker 29.2.1, Tailscale (connected at 100.80.182.102 as `brysons-mac-mini`), and Ollama 0.17.4 installed -- but no Ollama models are pulled yet, no Docker containers are running, and no n8n instance exists on this machine.

The critical architecture insight is that the agent process must never hold external API keys. All external service calls route through n8n webhook proxy workflows that inject credentials from n8n's encrypted credential store. The agent sees only the n8n webhook URLs. This creates a single choke point for sanitization (SECR-05), audit logging, and emergency cutoff (`docker compose stop` kills all external access instantly).

**Primary recommendation:** Build the Docker Compose stack first with all security directives baked in from day one (no "harden later" approach), then layer proxy workflows, HITL policy, and safety controls on top.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Single `docker-compose.yml` with all services (OpenClaw, PostgreSQL, Redis, Qdrant, n8n) on `openclaw-net` bridge
- Ollama already running on host -- Phase 1 only configures container access to host Ollama (no install needed)
- Bind mounts to `~/.openclaw/data/` for all persistent data (PostgreSQL, Redis, Qdrant) -- operator can see and backup files directly
- Web UI = existing Next.js dashboard at `~/.openclaw/dashboard/` (port 3000) -- Phase 1 makes it accessible via Tailscale, no new UI built
- API keys stored in n8n's built-in encrypted credentials store -- agent never sees keys
- Agent calls proxy workflows via webhook triggers (HTTP endpoints on n8n)
- Shared sanitizer sub-workflow called by all 6 proxy workflows before hitting external APIs (SECR-05) -- single place to update injection rules
- Proxy workflows for services with available API keys are fully configured; services without keys get stub workflows returning mock data
- In Phase 1, no approval path exists (Telegram is Phase 3) -- RED and YELLOW actions are logged and blocked, never executed
- All YELLOW-tier actions default to RED (blocked) until Telegram enables real approval flows
- Tier classifications stored in YAML config file at `~/.openclaw/config/`
- DELETE = RED is hardcoded in application code -- cannot be overridden via config file (SECR-07)
- Local counter (SQLite or file) checked before every Anthropic API call, with daily reconciliation against Anthropic's usage API to correct drift
- When any limit is hit ($50/month, 50 tool calls/session, 30-min timeout): graceful degrade -- agent completes current action, then stops accepting new work and logs the event
- Minimal set of 3-5 pinned directives for context window safety: HITL enforcement, DELETE rule, cost limits, no autonomous external messages
- Emergency stop = `docker compose stop` -- keys are behind n8n proxy so stopping containers effectively cuts all agent access to external services

### Claude's Discretion
- Exact container resource limits and PID configurations within INFR-02 hardening spec
- Checkpoint summarization implementation details (every 20 turns per SECR-04)
- Verification loop mechanics for pinned directive survival checks
- Tailscale ACL configuration specifics

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFR-01 | OpenClaw running in Docker with PostgreSQL 16, Redis 7, Qdrant, and n8n on openclaw-net bridge | Docker Compose multi-service stack patterns; official images for postgres:16, redis:7-alpine, qdrant/qdrant, n8nio/n8n |
| INFR-02 | All containers hardened (non-root UID 1000, read-only FS, tmpfs noexec, all caps dropped, PID limit 200) | Docker security directives documented in Architecture Patterns; OWASP Docker Security Cheat Sheet confirms approach |
| INFR-03 | All Docker ports bound to 127.0.0.1 only -- no public exposure | Port binding syntax `127.0.0.1:PORT:PORT`; Tailscale serve proxies to localhost |
| INFR-04 | Ollama running on host with qwen3:14b and nomic-embed-text models loaded | Ollama 0.17.4 already installed; models need `ollama pull`; containers reach host via `host.docker.internal` |
| INFR-05 | Tailscale VPN configured with ACLs restricting access to ports 3000, 18789, 5678, 22 | Tailscale already connected; `tailscale serve` for localhost forwarding; ACLs via admin console |
| SECR-01 | n8n security proxy operational -- agent never holds external API keys; 6 proxy workflows | n8n webhook trigger + HTTP Request node pattern; n8n encrypted credentials store; agent calls webhooks only |
| SECR-02 | HITL approval via Telegram with RED/GREEN/YELLOW tiers | Phase 1 implements tier classification and enforcement (block RED+YELLOW, allow GREEN); Telegram approval deferred to Phase 3 |
| SECR-03 | Cost circuit breakers active -- $50/month Anthropic hard cap, 50 tool calls/session, 30-min timeout | Local SQLite counter + Anthropic Usage API (`/v1/organizations/usage_report/messages`) for daily reconciliation |
| SECR-04 | Context window safety -- pinned directives with markers, checkpoint summarization every 20 turns, verification every 10 turns | Pinned directive pattern with `[PINNED -- DO NOT SUMMARIZE]` markers; verification loop checks directive presence |
| SECR-05 | Content sanitization in n8n proxy -- strip prompt injection attempts | Shared n8n sub-workflow sanitizer; regex-based stripping of injection patterns; critical given recent n8n CVEs |
| SECR-06 | Emergency stop procedure tested -- `docker compose stop openclaw` with key revocation within 5 min | Keys never in agent env (behind n8n proxy); `docker compose stop` = instant cutoff; revocation procedure documented |
| SECR-07 | DELETE operations always require HITL approval -- this rule never relaxes | Hardcoded in application code; config file cannot override; RED tier classification |
</phase_requirements>

## Standard Stack

### Core

| Component | Version/Image | Purpose | Why Standard |
|-----------|--------------|---------|--------------|
| Docker Compose | v2 (bundled with Docker 29.2.1) | Multi-service orchestration | Already installed; native multi-container management |
| PostgreSQL | `postgres:16-alpine` | Session persistence, agent state, audit logs | Official image; alpine for smaller attack surface; UID 999 by default |
| Redis | `redis:7-alpine` | Caching, pub/sub message bus, rate limiting | Official image; alpine variant; `--requirepass` for auth |
| Qdrant | `qdrant/qdrant:latest` | Vector database for future memory/RAG (Phase 2 prep) | Official image; runs non-root; ports 6333/6334 |
| n8n | `n8nio/n8n:latest` (pin to >= 2.5.2) | API proxy, workflow automation, credential store | **CRITICAL: Must be >= 2.5.2 due to CVE-2026-25049 (CVSS 9.4)** |
| Ollama | 0.17.4 (host) | Local LLM inference | Already installed on host; containers access via `host.docker.internal:11434` |
| Tailscale | Installed (host) | VPN mesh, `tailscale serve` for port forwarding | Already connected as `brysons-mac-mini` at 100.80.182.102 |
| Next.js Dashboard | Existing at `~/.openclaw/dashboard/` | Web UI (dev/setup) | Already built; Phase 1 just makes it Tailscale-accessible |

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| SQLite (file) | Local cost counter for circuit breakers (SECR-03) | Every Anthropic API call; daily reconciliation |
| YAML (file) | HITL tier classification config | Action classification lookup |
| Anthropic Admin API | Usage/cost reconciliation | Daily cron or on-demand drift correction |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Bind mounts | Docker named volumes | Named volumes are more portable but operator cannot directly see/backup files; user chose bind mounts |
| n8n credential store | HashiCorp Vault | Vault is overkill for single-user; n8n credential encryption is sufficient |
| SQLite cost counter | Redis counter | Redis adds dependency complexity; SQLite file is simpler and survives container restarts via bind mount |
| `postgres:16-alpine` | `postgres:16` (full) | Full image has more tools but larger attack surface; alpine is preferred for hardened deployments |

### Installation

```bash
# Pull required Docker images
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull qdrant/qdrant:latest
docker pull n8nio/n8n:latest  # Verify version >= 2.5.2

# Pull Ollama models (host, not Docker)
ollama pull qwen3:14b
ollama pull nomic-embed-text
```

## Architecture Patterns

### Recommended Project Structure

```
~/.openclaw/
├── docker-compose.yml          # Single compose file (all services)
├── .env                        # n8n credentials only (chmod 600)
├── config/
│   ├── hitl-tiers.yaml         # RED/YELLOW/GREEN action classifications
│   ├── cost-limits.yaml        # Circuit breaker thresholds
│   └── pinned-directives.yaml  # Context safety directives
├── data/
│   ├── postgres/               # PostgreSQL data (bind mount)
│   ├── redis/                  # Redis persistence (bind mount)
│   ├── qdrant/                 # Qdrant vector data (bind mount)
│   ├── n8n/                    # n8n workflow data (bind mount)
│   └── cost-tracker.db         # SQLite cost counter
├── dashboard/                  # Existing Next.js app (port 3000)
├── logs/                       # Centralized log output
├── memory/                     # Agent memory (Phase 2)
└── skills/                     # Agent skills (future phases)
```

### Pattern 1: Hardened Container Security Directives

**What:** Every container in the compose file gets the same security baseline.
**When to use:** All containers, no exceptions.

```yaml
# Applied to EVERY service in docker-compose.yml
services:
  any-service:
    user: "1000:1000"             # Non-root
    read_only: true               # Immutable filesystem
    security_opt:
      - no-new-privileges:true    # Block privilege escalation
    cap_drop:
      - ALL                       # Drop all Linux capabilities
    tmpfs:
      - /tmp:size=100M,noexec,nosuid,nodev
    pids_limit: 200               # Fork bomb protection
    deploy:
      resources:
        limits:
          memory: 4G              # Hard ceiling (tune per service)
          cpus: "2.0"
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

**Source:** OWASP Docker Security Cheat Sheet, project blueprint `02-Security/docker-hardening.md`

### Pattern 2: n8n API Proxy Workflow

**What:** Agent calls n8n webhook -> sanitizer sub-workflow strips injection -> HTTP Request node calls external API with credentials from n8n store -> response returned to agent.
**When to use:** Every external API call the agent makes.

```
Agent HTTP POST -> n8n Webhook Trigger
                      |
                      v
               Sanitizer Sub-Workflow
               (shared by all 6 proxies)
                      |
                      v
               HTTP Request Node
               (credentials from n8n store)
                      |
                      v
               Respond to Webhook
               (sanitized response -> agent)
```

The 6 proxy workflows:
1. Clay enrichment API
2. GHL contacts API
3. GHL messages API
4. Email sending API (SendGrid/Mailgun)
5. DataForSEO API
6. Serper API

Services without available API keys get stub workflows that return mock/empty data with a `"status": "stub"` field so the agent can handle gracefully.

### Pattern 3: Tailscale Serve for Localhost Access

**What:** Docker ports bind to `127.0.0.1`, Tailscale serve proxies tailnet traffic to localhost.
**When to use:** All services that need remote access from the Windows PC.

```bash
# Bind Docker ports to localhost only (in docker-compose.yml)
ports:
  - "127.0.0.1:3000:3000"    # Dashboard
  - "127.0.0.1:18789:18789"  # OpenClaw Gateway
  - "127.0.0.1:5678:5678"    # n8n UI

# Then use Tailscale serve to make them accessible via tailnet
tailscale serve --bg 3000     # Dashboard -> https://brysons-mac-mini.ts.net
tailscale serve --bg 5678     # n8n -> https://brysons-mac-mini.ts.net:5678
tailscale serve --bg 18789    # Gateway -> https://brysons-mac-mini.ts.net:18789
```

**Important:** `tailscale serve` provides HTTPS automatically with valid Let's Encrypt certificates. Traffic is encrypted end-to-end. Only devices on the tailnet can access these endpoints.

**Source:** [Tailscale Serve documentation](https://tailscale.com/docs/features/tailscale-serve)

### Pattern 4: HITL Tier Enforcement (Phase 1 -- No Telegram)

**What:** Every agent action is classified by tier before execution. In Phase 1, RED and YELLOW are blocked (logged but never executed). GREEN proceeds automatically.
**When to use:** Before every agent action.

```yaml
# ~/.openclaw/config/hitl-tiers.yaml
tiers:
  RED:  # ALWAYS blocked in Phase 1 (approval path comes in Phase 3)
    - send_email
    - send_sms
    - send_ghl_message
    - delete_*           # Wildcard: any delete operation (SECR-07 hardcoded)
    - publish_content
    - bulk_update
    - create_payment
    - modify_agent_config
    - export_data

  YELLOW:  # Defaults to RED until Telegram approval exists
    - ghl_contact_create
    - clay_enrich_single
    - airtable_record_update
    - file_create_workspace

  GREEN:  # Auto-approved
    - read_*
    - query_*
    - memory_write
    - generate_draft
    - local_model_query
    - log_event
    - internal_calculation
```

### Pattern 5: Cost Circuit Breaker

**What:** Local SQLite counter tracks Anthropic API usage. Checked before every call. Daily reconciliation against Anthropic's Usage API corrects drift.
**When to use:** Before every Anthropic API call.

```
Before API call:
  1. Read local counter (SQLite)
  2. Check: monthly_spend < $50?
  3. Check: session_tool_calls < 50?
  4. Check: session_duration < 30 min?
  5. If ANY check fails: graceful degrade
     - Complete current action
     - Stop accepting new work
     - Log the circuit breaker event
  6. If all pass: make API call, update counter

Daily reconciliation:
  1. Call Anthropic Usage API: GET /v1/organizations/usage_report/messages
  2. Compare local counter to API-reported usage
  3. If drift > 5%: correct local counter to match API
  4. Log reconciliation result
```

**Source:** [Anthropic Usage and Cost API documentation](https://docs.anthropic.com/en/api/usage-cost-api) -- requires Admin API key (`sk-ant-admin-...`)

### Pattern 6: Context Window Safety

**What:** Pinned directives survive context compaction. Verification loop checks they are still present.
**When to use:** Every agent session.

```
Pinned Directives (3-5 max):
  [PINNED -- DO NOT SUMMARIZE]
  1. All RED-tier and YELLOW-tier actions are BLOCKED. Log and refuse.
  2. DELETE operations ALWAYS require HITL approval. No exceptions.
  3. Cost limits: $50/month, 50 tool calls/session, 30-min timeout.
  4. Never send external messages autonomously.
  [END PINNED]

Checkpoint Summarization (every 20 turns):
  - Summarize conversation history (turns 1-20)
  - Keep pinned directives verbatim (never summarize)
  - Replace old turns with summary + pinned directives

Verification Loop (every 10 turns):
  - Parse current context for pinned directive markers
  - Compare against known directive list
  - If ANY directive missing: HALT session immediately
  - Log: which directive was lost, at what turn count
```

### Anti-Patterns to Avoid

- **"Harden later" approach:** Never deploy an unhardened compose file intending to add security later. Bake all security directives in from the first `docker compose up`.
- **Agent holds API keys in env vars:** The entire proxy architecture exists to prevent this. Never pass external API keys to the OpenClaw container's environment.
- **Host networking (`network_mode: host`):** Completely defeats container network isolation. Always use the `openclaw-net` bridge.
- **Mounting Docker socket:** `/var/run/docker.sock` gives full host control. Never mount it into any container.
- **Running n8n < 2.5.2:** CVE-2026-25049 (CVSS 9.4) allows RCE via expression sandbox escape in webhook workflows. Since our entire security model depends on n8n as a proxy, this is a critical dependency.
- **Trusting the macOS firewall alone:** Docker bypasses pf/firewall on macOS in some configurations. The primary defense is `127.0.0.1` port binding + Tailscale serve.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API key isolation | Custom proxy server | n8n webhook workflows + credential store | n8n handles encryption, credential rotation UI, and workflow logic; building a custom proxy duplicates all of this |
| VPN access | WireGuard manual config | Tailscale (already installed) | Tailscale handles NAT traversal, key management, ACLs, MagicDNS, and cert provisioning automatically |
| Container orchestration | Shell scripts for multi-container | Docker Compose | Compose handles service ordering, networking, health checks, restart policies natively |
| Cost tracking API | Scraping Anthropic dashboard | Anthropic Admin API (`/v1/organizations/usage_report/messages`) | Official API provides programmatic access with 5-minute data freshness |
| Content sanitization | Custom NLP pipeline | Regex-based sanitizer in n8n Function node | Prompt injection patterns are well-documented; regex catches the common vectors (hidden text, instruction overrides, base64 commands) without the complexity of an NLP model |
| Certificate management | Self-signed certs + trust store | Tailscale serve (auto-provisions Let's Encrypt certs) | Zero configuration; valid certs; automatic renewal |

**Key insight:** The n8n proxy pattern is the linchpin. It simultaneously solves credential isolation, content sanitization, audit logging, and emergency cutoff. Resist the temptation to add a separate proxy layer -- n8n already provides everything needed.

## Common Pitfalls

### Pitfall 1: n8n Version Vulnerability (CVE-2026-25049)

**What goes wrong:** Deploying n8n < 2.5.2 exposes the proxy to remote code execution via expression sandbox escape. Since our architecture routes ALL external API calls through n8n, a compromised n8n instance means a compromised proxy -- the attacker can read all credentials and execute arbitrary commands.
**Why it happens:** Using `n8nio/n8n:latest` without verifying the actual version; or pinning to an older version.
**How to avoid:** Pin to a specific version >= 2.5.2 in docker-compose.yml: `image: n8nio/n8n:2.5.2`. Verify after pull with `docker exec n8n n8n --version`.
**Warning signs:** n8n container version does not match expected pinned version after a `docker compose pull`.
**Source:** [CVE-2026-25049 advisory](https://community.n8n.io/t/security-bulletin-february-25-2026/270324)

### Pitfall 2: Docker Port Binding on macOS

**What goes wrong:** On macOS, Docker Desktop can sometimes expose ports despite `127.0.0.1` binding, depending on Docker Desktop version and configuration.
**Why it happens:** Docker Desktop for Mac uses a Linux VM; port forwarding behavior can differ from native Linux Docker.
**How to avoid:** After `docker compose up`, verify with `lsof -i -P -n | grep LISTEN` that ports show `127.0.0.1`, not `*` or `0.0.0.0`. Test from another device on the LAN to confirm ports are unreachable.
**Warning signs:** Can access Docker ports from another device on the local network without Tailscale.

### Pitfall 3: Bind Mount Permissions with Non-Root Containers

**What goes wrong:** Containers running as UID 1000 cannot write to bind-mounted directories owned by the host user (typically UID 501 on macOS).
**Why it happens:** macOS UID for the default user is 501; Docker's non-root UID 1000 has no write permission.
**How to avoid:** Either `chown -R 1000:1000 ~/.openclaw/data/` on the directories, or run containers as UID 501 to match the macOS user. The PostgreSQL official image runs as UID 999 by default -- test if it needs adjustment.
**Warning signs:** Container exits with permission denied errors on startup.

### Pitfall 4: Ollama Host Access from Docker

**What goes wrong:** Containers cannot reach Ollama on the host at `host.docker.internal:11434`.
**Why it happens:** `host.docker.internal` is a Docker Desktop feature; may need explicit configuration. Also, if Ollama binds to `127.0.0.1` only, Docker containers cannot reach it.
**How to avoid:** Verify Ollama is listening on `0.0.0.0:11434` (default behavior). Test from inside a container: `docker exec <container> curl http://host.docker.internal:11434/api/tags`.
**Warning signs:** Connection refused or timeout when containers try to reach Ollama.

### Pitfall 5: Anthropic Admin API Key Requirement

**What goes wrong:** The cost reconciliation logic calls the Anthropic Usage API, but this requires an Admin API key (`sk-ant-admin-...`), not a regular API key.
**Why it happens:** Admin keys are provisioned separately from regular API keys; the operator may not realize they need a different key type.
**How to avoid:** Provision an Admin API key from the Anthropic Console (Settings > Admin API Keys). Store it separately from the regular API key -- it should only be used for cost reconciliation, not for LLM calls.
**Warning signs:** 401/403 errors when calling `/v1/organizations/usage_report/messages`.

### Pitfall 6: n8n Webhook URL Stability

**What goes wrong:** n8n webhook URLs change when workflows are deactivated/reactivated or when using test vs production mode.
**Why it happens:** n8n generates different URLs for test and production webhook triggers. Deactivating a workflow stops its production webhook.
**How to avoid:** Always use production webhooks (not test webhooks). Keep proxy workflows permanently active. Document the webhook paths in a config file the agent reads.
**Warning signs:** Agent gets 404 or connection refused when calling n8n proxy; works in n8n test mode but fails in production.

### Pitfall 7: Context Window Verification False Positives

**What goes wrong:** Verification loop incorrectly detects a missing pinned directive because the check is too brittle (exact string match fails due to whitespace changes during summarization).
**Why it happens:** When the context is summarized, surrounding whitespace or formatting may shift, causing exact string matching to fail even though the directive content is preserved.
**How to avoid:** Use a robust matching strategy: check for the presence of key phrases from each directive rather than exact string matching. For example, check for "DELETE operations" and "HITL approval" rather than the full sentence.
**Warning signs:** Sessions halt unexpectedly with "pinned directive missing" despite directives being visually present in the context.

## Code Examples

### Docker Compose Multi-Service Stack (Hardened)

```yaml
# ~/.openclaw/docker-compose.yml
# All services on openclaw-net, hardened, localhost-only ports

version: "3.8"

networks:
  openclaw-net:
    driver: bridge

services:
  postgres:
    image: postgres:16-alpine
    container_name: openclaw-postgres
    restart: unless-stopped
    user: "999:999"  # postgres default UID
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:size=64M,noexec,nosuid,nodev
      - /run/postgresql:size=16M  # postgres needs this for socket
    environment:
      POSTGRES_USER: openclaw
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      POSTGRES_DB: openclaw
    volumes:
      - ~/.openclaw/data/postgres:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - openclaw-net
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    pids_limit: 100
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U openclaw"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: openclaw-redis
    restart: unless-stopped
    user: "999:999"
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:size=32M,noexec,nosuid,nodev
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --save 60 1000
      --loglevel warning
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - ~/.openclaw/data/redis:/data
    ports:
      - "127.0.0.1:6379:6379"
    networks:
      - openclaw-net
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "0.5"
    pids_limit: 50
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  qdrant:
    image: qdrant/qdrant:latest
    container_name: openclaw-qdrant
    restart: unless-stopped
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    tmpfs:
      - /tmp:size=64M,noexec,nosuid,nodev
    volumes:
      - ~/.openclaw/data/qdrant:/qdrant/storage
    ports:
      - "127.0.0.1:6333:6333"
      - "127.0.0.1:6334:6334"
    networks:
      - openclaw-net
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
    pids_limit: 100
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  n8n:
    image: n8nio/n8n:2.5.2  # PINNED: CVE-2026-25049 patched
    container_name: openclaw-n8n
    restart: unless-stopped
    user: "1000:1000"
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_AUTH_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_AUTH_PASSWORD}
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_HOST=0.0.0.0
      - WEBHOOK_URL=http://localhost:5678/
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - GENERIC_TIMEZONE=America/Chicago
    volumes:
      - ~/.openclaw/data/n8n:/home/node/.n8n
    ports:
      - "127.0.0.1:5678:5678"
    networks:
      - openclaw-net
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.5"
    pids_limit: 150
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5678/healthz || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

**Note:** The OpenClaw container itself is omitted from this example because the project treats this Mac as the agent (Claude Code runs on the host). The Docker stack provides supporting services. If a containerized OpenClaw gateway is needed, add it with the same hardening pattern.

### n8n Sanitizer Sub-Workflow (Pseudocode)

```javascript
// Shared sanitizer sub-workflow -- called by all 6 proxy workflows
// Input: { "payload": { ... raw data from agent ... } }
// Output: { "sanitized": { ... cleaned data ... }, "flags": [...] }

function sanitize(input) {
  const flags = [];
  let text = JSON.stringify(input.payload);

  // 1. Strip common prompt injection patterns
  const injectionPatterns = [
    /ignore\s+(all\s+)?previous\s+instructions/gi,
    /you\s+are\s+now\s+/gi,
    /system\s*:\s*/gi,
    /\[INST\]/gi,
    /<<SYS>>/gi,
    /<\|im_start\|>/gi,
    /```\s*bash\s*\n.*curl.*\|.*bash/gis,
    /base64\s*-d/gi,
  ];

  for (const pattern of injectionPatterns) {
    if (pattern.test(text)) {
      flags.push({ type: 'injection_detected', pattern: pattern.source });
      text = text.replace(pattern, '[REDACTED]');
    }
  }

  // 2. Strip invisible Unicode characters
  text = text.replace(/[\u200B-\u200F\u2028-\u202F\u2060-\u206F\uFEFF]/g, '');

  // 3. Strip HTML/CSS that could hide content
  text = text.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
  text = text.replace(/<[^>]+style\s*=\s*["'][^"']*display\s*:\s*none[^"']*["'][^>]*>[\s\S]*?<\/[^>]+>/gi, '');
  text = text.replace(/<[^>]+style\s*=\s*["'][^"']*font-size\s*:\s*0[^"']*["'][^>]*>[\s\S]*?<\/[^>]+>/gi, '');

  // 4. Truncate oversized payloads
  const MAX_PAYLOAD_SIZE = 50000; // 50KB
  if (text.length > MAX_PAYLOAD_SIZE) {
    flags.push({ type: 'truncated', original_size: text.length });
    text = text.substring(0, MAX_PAYLOAD_SIZE);
  }

  return {
    sanitized: JSON.parse(text),
    flags: flags,
    was_modified: flags.length > 0
  };
}
```

### Tailscale ACL Configuration

```jsonc
// Tailscale Admin Console > Access Controls
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:owner"],
      "dst": [
        "brysons-mac-mini:22",     // SSH
        "brysons-mac-mini:3000",   // Dashboard
        "brysons-mac-mini:5678",   // n8n
        "brysons-mac-mini:18789"   // OpenClaw Gateway
      ]
    }
  ],
  "tagOwners": {
    "tag:server": ["autogroup:owner"]
  }
}
```

### HITL Tier Enforcement (Application Code Pattern)

```typescript
// Pseudocode for HITL enforcement in agent action pipeline
import { parse as parseYaml } from 'yaml';

interface ActionRequest {
  action: string;
  params: Record<string, unknown>;
  source: string;
}

type Tier = 'RED' | 'YELLOW' | 'GREEN';

function classifyAction(action: string, tiers: Record<Tier, string[]>): Tier {
  // Hardcoded rule: DELETE = RED, always (SECR-07)
  if (action.toLowerCase().includes('delete')) {
    return 'RED';
  }

  // Check config-based tiers
  for (const [tier, patterns] of Object.entries(tiers)) {
    for (const pattern of patterns) {
      if (pattern.endsWith('*')) {
        if (action.startsWith(pattern.slice(0, -1))) return tier as Tier;
      } else if (action === pattern) {
        return tier as Tier;
      }
    }
  }

  // Default: treat unknown actions as RED (fail-secure)
  return 'RED';
}

function enforceHITL(request: ActionRequest, tiers: Record<Tier, string[]>): {
  allowed: boolean;
  reason: string;
} {
  const tier = classifyAction(request.action, tiers);

  if (tier === 'GREEN') {
    return { allowed: true, reason: 'GREEN tier: auto-approved' };
  }

  // Phase 1: RED and YELLOW are blocked (no approval path yet)
  return {
    allowed: false,
    reason: `${tier} tier: blocked (approval channel not yet available)`,
  };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| n8n expression sandbox (pre-2.5.2) | Hardened expression evaluation (2.5.2+) | Feb 2026 | CVE-2026-25049 patched; must use >= 2.5.2 |
| Anthropic cost tracking via dashboard | Admin API for programmatic cost tracking | 2025 | Enables automated circuit breaker reconciliation |
| Docker `version: "3.8"` in compose | `version` key deprecated in Compose v2 | 2024 | Compose v2 ignores it; can remove but harmless to keep |
| Tailscale serve as beta | Tailscale serve GA | 2025 | Stable `tailscale serve --bg` for persistent port forwarding |
| Manual SSL cert management | Tailscale serve auto-provisions certs | 2025 | Zero-config HTTPS for all served ports |

**Deprecated/outdated:**
- `version` key in docker-compose.yml: Docker Compose v2 ignores it but does not error. Can be omitted.
- `deploy.resources` in Compose without Swarm: Docker Compose v2 now supports `deploy.resources` outside of Swarm mode (previously Swarm-only).

## Open Questions

1. **OpenClaw Gateway Docker Image**
   - What we know: The blueprint references `openclaw/openclaw:latest` as a Docker image. The project directory has a Next.js dashboard but no gateway container.
   - What's unclear: Does a published OpenClaw Docker image exist, or does the agent run as Claude Code on the host? The current setup (Claude Code on Mac) suggests the agent IS the host process.
   - Recommendation: Treat the Mac as the agent. The Docker stack provides supporting services (DB, cache, vector store, n8n proxy). The "OpenClaw container" in the blueprint may be aspirational. Build the stack without it; add later if an image materializes.

2. **n8n Read-Only Filesystem Compatibility**
   - What we know: n8n writes workflow data, credentials, and execution logs to `~/.n8n`.
   - What's unclear: Whether n8n can run with `read_only: true` if `~/.n8n` is a bind mount. The n8n container may also need to write to other internal paths.
   - Recommendation: Test with `read_only: true` + bind mount for `~/.n8n` + tmpfs for `/tmp`. If n8n fails, identify additional writable paths using `docker diff` after a test run, then add targeted tmpfs mounts.

3. **PostgreSQL Alpine UID Mismatch**
   - What we know: `postgres:16-alpine` runs as UID 70 (not 999 as in some documentation). The standard `postgres:16` uses UID 999.
   - What's unclear: The exact UID of the Alpine variant vs standard variant may have changed between releases.
   - Recommendation: After pulling the image, verify with `docker run --rm postgres:16-alpine id` and adjust the `user:` directive and `chown` commands accordingly.

4. **Anthropic Admin API Key Provisioning**
   - What we know: The Usage API requires an Admin API key. Only organization admins can provision these.
   - What's unclear: Whether the operator's Anthropic account has admin-level access to provision Admin API keys.
   - Recommendation: Attempt to provision an Admin API key from the Anthropic Console. If the account lacks admin permissions, fall back to local-only cost tracking without reconciliation (still functional, just no drift correction).

5. **Dashboard Accessibility via Tailscale Serve**
   - What we know: The existing Next.js dashboard runs at port 3000. Tailscale serve can proxy to it.
   - What's unclear: Whether the Next.js dev server or a production build should be served. Dev server has hot-reload but is not hardened.
   - Recommendation: Build and serve the production Next.js build (`next build && next start`). Do not expose the dev server via Tailscale.

## Sources

### Primary (HIGH confidence)
- [Docker Security - OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) - Container hardening directives
- [Tailscale Serve documentation](https://tailscale.com/docs/features/tailscale-serve) - Localhost port forwarding to tailnet
- [Tailscale Serve examples](https://tailscale.com/kb/1313/serve-examples) - Configuration patterns
- [Anthropic Usage and Cost API](https://docs.anthropic.com/en/api/usage-cost-api) - Programmatic cost tracking
- [Anthropic Admin API - Get Messages Usage Report](https://docs.anthropic.com/en/api/admin-api/usage-cost/get-messages-usage-report) - Usage endpoint details
- [n8n Webhook node documentation](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) - Webhook trigger patterns
- [Qdrant Installation Guide](https://qdrant.tech/documentation/guides/installation/) - Docker setup
- [Redis Docker Hub](https://hub.docker.com/_/redis) - Official image configuration
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres) - Official image, UID handling

### Secondary (MEDIUM confidence)
- [n8n Security Bulletin: February 25, 2026](https://community.n8n.io/t/security-bulletin-february-25-2026/270324) - CVE-2026-25049 patch details
- [n8n API Key Proxy community template](https://community.n8n.io/t/api-key-proxy-for-ai-agents-openrouter-openai-compatible/262590) - Proxy pattern validation
- [n8n Secure Webhook template](https://n8n.io/workflows/5174-creating-a-secure-webhook-must-have/) - Webhook authentication patterns
- Project blueprint documents (02-Security/*, 06-Integrations/n8n/*, 11-Implementation-Roadmap/phase-1-foundation.md, phase-2-security.md) - Architecture decisions and patterns

### Tertiary (LOW confidence)
- n8n read-only filesystem compatibility: Not verified with official docs; needs empirical testing
- PostgreSQL Alpine UID: Varies between releases; needs verification with actual pulled image
- Specific Qdrant hardening: Qdrant docs do not extensively cover non-root or read-only; needs testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components are well-documented official Docker images with established patterns
- Architecture: HIGH - n8n proxy pattern validated by community templates; Docker security directives from OWASP; Tailscale serve documented
- Pitfalls: HIGH - CVE-2026-25049 confirmed by NVD and n8n security bulletin; macOS Docker port binding known issue; permission issues well-documented
- Cost controls: MEDIUM - Anthropic Usage API is documented but Admin API key provisioning needs verification for this specific account
- Context safety: MEDIUM - Pinned directive pattern is sound but verification loop implementation details are discretionary (no standard library)

**Research date:** 2026-02-28
**Valid until:** 2026-03-14 (14 days -- n8n security landscape is actively evolving)

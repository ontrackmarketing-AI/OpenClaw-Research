# Phase 1: Secure Infrastructure - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Docker stack running on Mac Mini M4 Pro with PostgreSQL 16, Redis 7, Qdrant, and n8n — all hardened, VPN-gated, with security controls (n8n API proxy, HITL tiers, cost circuit breakers, context safety). No API call executes without passing through security controls. No external-facing features — this is the foundation that all subsequent phases build on.

</domain>

<decisions>
## Implementation Decisions

### Docker & service layout
- Single `docker-compose.yml` with all services (OpenClaw, PostgreSQL, Redis, Qdrant, n8n) on `openclaw-net` bridge
- Ollama already running on host — Phase 1 only configures container access to host Ollama (no install needed)
- Bind mounts to `~/.openclaw/data/` for all persistent data (PostgreSQL, Redis, Qdrant) — operator can see and backup files directly
- Web UI = existing Next.js dashboard at `~/.openclaw/dashboard/` (port 3000) — Phase 1 makes it accessible via Tailscale, no new UI built

### n8n proxy design
- API keys stored in n8n's built-in encrypted credentials store — agent never sees keys
- Agent calls proxy workflows via webhook triggers (HTTP endpoints on n8n)
- Shared sanitizer sub-workflow called by all 6 proxy workflows before hitting external APIs (SECR-05) — single place to update injection rules
- Proxy workflows for services with available API keys are fully configured; services without keys get stub workflows returning mock data

### HITL tier boundaries
- In Phase 1, no approval path exists (Telegram is Phase 3) — RED and YELLOW actions are logged and blocked, never executed
- All YELLOW-tier actions default to RED (blocked) until Telegram enables real approval flows
- Tier classifications stored in YAML config file at `~/.openclaw/config/`
- DELETE = RED is hardcoded in application code — cannot be overridden via config file (SECR-07)

### Cost & safety controls
- Local counter (SQLite or file) checked before every Anthropic API call, with daily reconciliation against Anthropic's usage API to correct drift
- When any limit is hit ($50/month, 50 tool calls/session, 30-min timeout): graceful degrade — agent completes current action, then stops accepting new work and logs the event
- Minimal set of 3-5 pinned directives for context window safety: HITL enforcement, DELETE rule, cost limits, no autonomous external messages
- Emergency stop = `docker compose stop` — keys are behind n8n proxy so stopping containers effectively cuts all agent access to external services

### Claude's Discretion
- Exact container resource limits and PID configurations within INFR-02 hardening spec
- Checkpoint summarization implementation details (every 20 turns per SECR-04)
- Verification loop mechanics for pinned directive survival checks
- Tailscale ACL configuration specifics

</decisions>

<specifics>
## Specific Ideas

- Agent process must never be able to read external API keys from its environment or filesystem — n8n proxy is the only path to external services
- Success criteria #3 is a simulation test: a RED-tier action (like a delete request) must be blocked with no approval path that bypasses HITL
- Success criteria #5 is a 55-turn context exhaustion test — all pinned safety directives must survive compaction

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-secure-infrastructure*
*Context gathered: 2026-02-28*

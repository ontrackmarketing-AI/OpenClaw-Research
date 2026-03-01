---
phase: 01-secure-infrastructure
verified: 2026-03-01T00:50:53Z
status: gaps_found
score: 13/17 must-haves verified
re_verification: false
gaps:
  - truth: "Every container runs as non-root with read-only filesystem, all caps dropped, PID limits set"
    status: failed
    reason: "Qdrant container (openclaw-qdrant) runs as root (uid=0, gid=0). Docker inspect shows Config.User=0:0 and exec confirms uid=0(root). The compose file intentionally omits user: for Qdrant but the official image runs as root by default."
    artifacts:
      - path: "~/.openclaw/docker-compose.yml"
        issue: "No user: directive for qdrant service; qdrant/qdrant:latest image defaults to root"
    missing:
      - "Add user: directive for qdrant or use a non-root Qdrant image variant"
      - "Alternatively document formally as an accepted risk with rationale in the compose file comments"

  - truth: "A RED-tier action (e.g., delete_contact) is blocked and logged with no path to execute it"
    status: partial
    reason: "SECR-02 is claimed Complete in REQUIREMENTS.md and Plan 02 includes SECR-02 in its requirements list. The requirement text is 'HITL approval via Telegram with RED/GREEN/YELLOW tiers'. Phase 1 delivers tier classification and blocking enforcement -- RED and YELLOW actions are blocked correctly. However the Telegram approval channel for YELLOW/RED escalation does not exist. The plan explicitly notes YELLOW defaults to RED 'until Phase 3 Telegram approval channel exists'. This means the classification half of SECR-02 is done but the approval-routing half is not built. REQUIREMENTS.md marking SECR-02 Complete for Phase 1 is premature."
    artifacts:
      - path: "~/.openclaw/src/hitl/enforce.ts"
        issue: "Blocks RED/YELLOW correctly but returns 'approval channel not yet available' -- no actual approval path wired"
    missing:
      - "Telegram bot (Phase 3 scope) -- SECR-02 approval channel"
      - "Update REQUIREMENTS.md traceability to reflect SECR-02 is partial at Phase 1 and will be completed in Phase 3"

human_verification:
  - test: "Access n8n dashboard from Windows machine via Tailscale"
    expected: "https://brysons-mac-mini.tail96c7b7.ts.net/ serves n8n login page; port 5678 unreachable from non-Tailscale device (phone on home WiFi)"
    why_human: "Cannot verify remote connectivity or port blocking from external networks programmatically"
  - test: "Tailscale ACL enforcement"
    expected: "INFR-05 requires ACLs restricting ports 3000, 18789, 5678, 22. ACLs were deferred as optional for single-user personal tailnet. Human should confirm whether this is acceptable or ACLs should be configured."
    why_human: "ACL configuration and enforcement requires Tailscale admin console access and a test device outside the tailnet"
---

# Phase 1: Secure Infrastructure Verification Report

**Phase Goal:** Stand up hardened Docker infrastructure (PostgreSQL, Redis, Qdrant, n8n), implement HITL tier enforcement with n8n API proxy layer, build cost circuit breakers, context window safety, and emergency stop procedure.
**Verified:** 2026-03-01T00:50:53Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

The must-haves are drawn directly from the three plan frontmatter blocks plus the five ROADMAP success criteria.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | docker compose up starts all 4 services without errors | VERIFIED | All 4 containers running+healthy: postgres, redis, qdrant, n8n |
| 2 | All container ports are bound to 127.0.0.1 only | VERIFIED | lsof confirms 127.0.0.1 on all 5 ports (5432, 6379, 6333, 6334, 5678) |
| 3 | Every container runs non-root with read-only FS, caps dropped, PID limits | FAILED | postgres=UID 70, redis=UID 999, n8n=UID 1000: non-root. Qdrant=root (UID 0). read_only=true, cap_drop=ALL, no-new-privileges confirmed on all 4. PID limits enforced (100/50/150/100). |
| 4 | Ollama responds from inside a Docker container via host.docker.internal:11434 | VERIFIED | docker exec openclaw-n8n wget to host.docker.internal:11434/api/tags returns model list |
| 5 | qwen3:14b and nomic-embed-text models are loaded and respond | VERIFIED | Both models present in Ollama model list; container connectivity confirmed |
| 6 | Dashboard and n8n ports accessible via Tailscale from Windows machine | HUMAN NEEDED | Tailscale serve active (https://brysons-mac-mini.tail96c7b7.ts.net/ -> 127.0.0.1:5678). Human confirmed in SUMMARY but needs re-test |
| 7 | Agent can call all 6 n8n proxy webhook endpoints and receive responses | VERIFIED | All 6 proxies (clay, ghl-contacts, ghl-messages, email, dataforseo, serper) return structured stub responses |
| 8 | All external API requests pass through sanitizer -- injection patterns stripped | VERIFIED | Test payload with "ignore all previous instructions" returned with flag injection:ignore_previous_instructions and text [REDACTED] |
| 9 | A RED-tier action is blocked and logged with no path to execute | PARTIAL | classify.ts correctly returns RED for delete_contact; enforceHITL blocks it. But SECR-02 Telegram approval channel is not built |
| 10 | A GREEN-tier action executes automatically without requiring approval | VERIFIED | read_contacts maps to GREEN, enforceHITL returns allowed=true |
| 11 | DELETE operations are classified as RED regardless of YAML config | VERIFIED | Hardcoded check before config lookup in classify.ts line 31; 28/28 tests pass |
| 12 | YELLOW-tier actions default to blocked (treated as RED) | VERIFIED | YELLOW returns allowed=false with "blocked (approval channel not yet available)" |
| 13 | Cost tracker module built and enforces limits when called | VERIFIED | 8/8 tracker tests pass: $50/mo, 50 tool calls, 30-min timeout all enforced |
| 14 | $50/month, 50 tool calls/session, 30-min timeout enforced | VERIFIED | checkLimits() blocks on all three thresholds; circuit breaker events logged to SQLite |
| 15 | Pinned safety directives present in every agent session | VERIFIED | 4 directives in pinned-directives.yaml; getPinnedDirectives() formats correct block with markers |
| 16 | 55-turn context exhaustion test confirms directives survive compaction | VERIFIED | context-guard.test.ts 55-turn simulation passes; all directives detected at turns 10, 20, 30, 40, 50, 55 |
| 17 | docker compose stop cuts all agent access to external services | VERIFIED | emergency-stop.sh calls docker compose stop; docs document < 30 second isolation |

**Score:** 13/17 truths verified (2 failed/partial, 2 human-needed)

### Required Artifacts

| Artifact | Status | Details |
|----------|--------|---------|
| `~/.openclaw/docker-compose.yml` | VERIFIED | 177-line compose file with openclaw-net, all 4 services, hardening directives, env var interpolation |
| `~/.openclaw/.env` | VERIFIED | chmod 600 (-rw-------), 5 required keys present (POSTGRES_PASSWORD, REDIS_PASSWORD, N8N_AUTH_USER, N8N_AUTH_PASSWORD, N8N_ENCRYPTION_KEY) |
| `~/.openclaw/data/` | VERIFIED | All 4 data dirs exist with content: postgres/base/, redis/, qdrant/collections/, n8n/config/ |
| `~/.openclaw/data/cost-tracker.db` | VERIFIED | SQLite DB with 3 tables: usage, sessions, circuit_breaker_events |
| `~/.openclaw/config/hitl-tiers.yaml` | VERIFIED | Contains RED, YELLOW, GREEN tiers with action lists and DELETE wildcard |
| `~/.openclaw/src/hitl/classify.ts` | VERIFIED | Exports classifyAction; hardcoded DELETE=RED check on line 31 before config lookup |
| `~/.openclaw/src/hitl/enforce.ts` | VERIFIED | Exports enforceHITL, classifyAction; structured JSON logging to stdout; loadTierConfig present |
| `~/.openclaw/src/hitl/types.ts` | VERIFIED | Exports Tier, ActionRequest, HITLResult, TierConfig |
| `~/.openclaw/src/cost/tracker.ts` | VERIFIED | Exports checkLimits, recordUsage, getMonthlySpend, getSessionStats, logCircuitBreakerEvent, initDB |
| `~/.openclaw/src/cost/reconcile.ts` | VERIFIED | Exports reconcileCosts; degrades gracefully without ANTHROPIC_ADMIN_API_KEY |
| `~/.openclaw/config/cost-limits.yaml` | VERIFIED | Contains monthly_cap_usd: 50, session_tool_call_limit: 50, session_timeout_minutes: 30 |
| `~/.openclaw/config/pinned-directives.yaml` | VERIFIED | 4 directives with keyword arrays; checkpoint_interval: 20; verification_interval: 10 |
| `~/.openclaw/src/safety/context-guard.ts` | VERIFIED | Exports verifyDirectives, getPinnedDirectives, checkpointSummarize, shouldCheckpoint, shouldVerify, handleVerificationFailure, loadDirectives |
| `~/.openclaw/docs/emergency-stop.md` | VERIFIED | Documents quick stop, full shutdown, resume procedure, key revocation |
| `~/.openclaw/scripts/emergency-stop.sh` | VERIFIED | Executable (-rwxr-xr-x); calls docker compose -f ~/.openclaw/docker-compose.yml stop |
| `~/.openclaw/scripts/verify-infra.sh` | VERIFIED | 21-check script covering containers, port binding, hardening, Ollama models, Tailscale |
| `~/.openclaw/config/proxy-endpoints.yaml` | VERIFIED | All 6 proxy webhook URLs documented with n8n workflow IDs |
| `n8n workflows (6 proxy + sanitizer)` | VERIFIED | 6 active proxy workflows respond to POST; inline sanitizer detects and strips injection patterns |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| docker-compose.yml | .env | ${VAR} interpolation | VERIFIED | 5 ${...} references confirmed: POSTGRES_PASSWORD, REDIS_PASSWORD, N8N_AUTH_USER, N8N_AUTH_PASSWORD, N8N_ENCRYPTION_KEY |
| docker-compose.yml services | ~/.openclaw/data/* | bind mount volumes | VERIFIED | All 4 services bind-mount to /Users/b2/.openclaw/data/{service}/ |
| containers | host Ollama | host.docker.internal:11434 | VERIFIED | verify-infra.sh and manual exec confirm container->host Ollama connectivity |
| agent action pipeline | enforce.ts | enforceHITL() | PARTIAL | enforceHITL() exists and works; not yet wired into an agent API call pipeline (Phase 2 prerequisite, by design) |
| enforce.ts | hitl-tiers.yaml | loadTierConfig() | VERIFIED | loadTierConfig reads YAML via yaml package; classify.ts consumes TierConfig |
| classify.ts | DELETE hardcode | action.includes('delete') -> RED | VERIFIED | Line 31: `if (action.toLowerCase().includes('delete')) { return 'RED'; }` |
| agent | n8n proxy webhooks | HTTP POST to localhost:5678/webhook/ | VERIFIED | proxy-endpoints.yaml documents all 6 URLs; all 6 respond to POST |
| tracker.ts | cost-tracker.db | better-sqlite3 read/write | VERIFIED | `cost-tracker.db` path referenced line 12; initDB() creates tables |
| tracker.ts | cost-limits.yaml | YAML config on init | VERIFIED | DEFAULT_CONFIG_PATH points to cost-limits.yaml; loaded via parseYaml |
| context-guard.ts | pinned-directives.yaml | loadDirectives() | VERIFIED | DEFAULT_CONFIG_PATH points to pinned-directives.yaml; parseYaml loads it |
| emergency-stop.sh | docker compose | docker compose -f ~/.openclaw/docker-compose.yml stop | VERIFIED | Line 6 of emergency-stop.sh matches the required command |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INFR-01 | 01-01-PLAN | PostgreSQL 16, Redis 7, Qdrant, n8n on openclaw-net bridge | SATISFIED | All 4 containers running healthy on openclaw-net |
| INFR-02 | 01-01-PLAN | All containers hardened (non-root UID 1000, read-only FS, tmpfs noexec, all caps dropped, PID limit 200) | PARTIAL | read-only FS: all 4. cap_drop ALL: all 4. no-new-privileges: all 4. tmpfs noexec: confirmed. Non-root: postgres(70), redis(999), n8n(1000) -- non-root. Qdrant runs as root(0) -- FAILS non-root requirement. PID limits enforced but differ from spec (100/50/150/100 vs stated 200). |
| INFR-03 | 01-01-PLAN | All Docker ports bound to 127.0.0.1 only | SATISFIED | lsof confirms 127.0.0.1 on all 5 ports |
| INFR-04 | 01-01-PLAN | Ollama with qwen3:14b and nomic-embed-text loaded | SATISFIED | Both models present and reachable from host and containers |
| INFR-05 | 01-01-PLAN | Tailscale VPN configured with ACLs restricting ports 3000, 18789, 5678, 22 | PARTIAL | Tailscale serve active for port 5678. ACLs deliberately deferred (personal single-user tailnet). Requirement text says "ACLs restricting access" -- not fully satisfied as written. Documented as acceptable by plan decision. |
| SECR-01 | 01-02-PLAN | n8n security proxy operational -- agent never holds external API keys; 6 proxy workflows | SATISFIED | All 6 proxies active and responding; .env has no external API keys; proxy-endpoints.yaml documents URLs |
| SECR-02 | 01-02-PLAN | HITL approval via Telegram with RED/GREEN/YELLOW tiers | PARTIAL | Tier classification (RED/YELLOW/GREEN) is fully implemented and tested (28 tests pass). Telegram approval channel is NOT built -- this is Phase 3 scope. REQUIREMENTS.md marks this Complete prematurely. The enforcement blocks RED/YELLOW but there is no approval routing path. |
| SECR-03 | 01-03-PLAN | Cost circuit breakers: $50/mo, 50 tool calls, 30-min timeout, $100/mo Clay, 100 emails/day | SATISFIED | All 3 Anthropic limits enforced; Clay and email limits configured in cost-limits.yaml; 8/8 tests pass |
| SECR-04 | 01-03-PLAN | Context window safety: pinned directives, checkpoint every 20 turns, verify every 10 turns | SATISFIED | 4 directives with [PINNED] markers; shouldCheckpoint(20)=true; shouldVerify(10)=true; 55-turn simulation passes |
| SECR-05 | 01-02-PLAN | Content sanitization in n8n proxy -- strips prompt injection from inputs | SATISFIED | Inline sanitizer in each proxy workflow; injection test confirmed flag + [REDACTED] output |
| SECR-06 | 01-03-PLAN | Emergency stop tested -- docker compose stop with key revocation < 5 minutes | SATISFIED | emergency-stop.sh executable; docs describe < 30 second stop; key revocation procedure documented |
| SECR-07 | 01-02-PLAN | DELETE operations always require HITL approval -- this rule never relaxes | SATISFIED | Hardcoded in classify.ts line 31 before config lookup; unit tests verify it cannot be overridden via YAML |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `~/.openclaw/src/hitl/enforce.ts` | `"approval channel not yet available"` in reason string | Info | Expected -- this is a documented Phase 1 limitation. Approval channel is Phase 3 scope. |
| `~/.openclaw/config/proxy-endpoints.yaml` | All 6 proxies have `status: stub` | Info | Expected -- stubs are by design until API keys are configured. Each proxy responds correctly with structured stub JSON. |
| `~/.openclaw/docker-compose.yml` | Qdrant service has no `user:` directive | Blocker | Qdrant runs as root (uid=0). Violates INFR-02 non-root requirement. |

### Human Verification Required

#### 1. Tailscale Remote Access from Windows

**Test:** From the Windows machine connected to Tailscale, open a browser and navigate to `https://brysons-mac-mini.tail96c7b7.ts.net/`. Also attempt to connect to `http://<mac-mini-lan-ip>:5678` from a device NOT on Tailscale (phone on cell data).
**Expected:** n8n login page loads via Tailscale URL. Direct LAN access to port 5678 is refused.
**Why human:** Remote connectivity from external networks cannot be verified programmatically from this machine.

#### 2. Tailscale ACL Decision

**Test:** Review whether Tailscale ACLs should be configured for INFR-05 compliance.
**Expected:** Either configure ACLs in Tailscale admin console (ports 3000, 18789, 5678, 22 restricted to autogroup:owner), or formally accept the deferred state as sufficient for a personal single-user tailnet.
**Why human:** ACL configuration requires Tailscale admin console access. The decision on whether this gap is acceptable requires operator judgment.

### Gaps Summary

Two substantive gaps block full goal achievement:

**Gap 1 -- Qdrant Root User (INFR-02):** The Qdrant container runs as root (uid=0). The compose file intentionally omits a `user:` directive because the plan stated "the official image handles its own user." In practice, the official `qdrant/qdrant:latest` image runs as root. This contradicts INFR-02's non-root hardening requirement. Fix: add `user: "1000:1000"` to the qdrant service and pre-chown the data directory, or use a rootless Qdrant variant.

**Gap 2 -- SECR-02 Telegram Approval Not Built (SECR-02):** REQUIREMENTS.md marks SECR-02 as Complete for Phase 1, and Plan 02 claims SECR-02 in its requirements list. The requirement text is "HITL approval via Telegram with RED/GREEN/YELLOW tiers." Phase 1 delivers the classification and blocking half (tiers, enforce.ts, 28 passing tests). The approval mechanism (Telegram bot, inline buttons, YELLOW escalation path) is Phase 3 scope and does not exist. This is a requirements-tracking gap: SECR-02 is partially satisfied in Phase 1 (classification layer) and will be completed in Phase 3 (approval channel). The REQUIREMENTS.md traceability table should reflect this split.

**Non-blocking discrepancies:**

- **INFR-02 PID limits:** Requirement says "PID limit 200" but actual limits are 100/50/150/100 (per-service, more restrictive than the stated cap). This is safer than the requirement, not a regression.
- **INFR-05 ACLs deferred:** Tailscale serve is active. ACLs are intentionally deferred for a personal single-user tailnet. This is a documented decision in the plan, not an oversight. Needs human confirmation to close.
- **INFR-02 "non-root UID 1000":** The requirement text appears to use UID 1000 as an example, not a literal requirement for all services. Services correctly use their native non-root UIDs (postgres:70, redis:999). Only Qdrant is a true violation (root).

---

_Verified: 2026-03-01T00:50:53Z_
_Verifier: Claude (gsd-verifier)_

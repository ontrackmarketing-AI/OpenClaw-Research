---
phase: 01-secure-infrastructure
plan: 01
subsystem: infra
tags: [docker, postgres, redis, qdrant, n8n, ollama, tailscale, security-hardening]

# Dependency graph
requires:
  - phase: none
    provides: "First phase -- no dependencies"
provides:
  - "Hardened Docker stack (PostgreSQL 16, Redis 7, Qdrant, n8n) on openclaw-net bridge"
  - "Ollama with qwen3:14b and nomic-embed-text models accessible from containers"
  - "Tailscale serve for VPN-gated remote access to n8n"
  - "Infrastructure verification script (21 automated checks)"
affects: [01-02-PLAN, 01-03-PLAN, 02-memory-model-routing, all-subsequent-phases]

# Tech tracking
tech-stack:
  added: [docker-compose, postgres-16-alpine, redis-7-alpine, qdrant, n8n-2.5.2, ollama, tailscale-serve]
  patterns: [localhost-only-port-binding, non-root-containers, read-only-fs, cap-drop-all, pids-limit, tmpfs-for-writable-paths]

key-files:
  created:
    - "~/.openclaw/docker-compose.yml"
    - "~/.openclaw/.env"
    - "~/.openclaw/data/postgres/"
    - "~/.openclaw/data/redis/"
    - "~/.openclaw/data/qdrant/"
    - "~/.openclaw/data/n8n/"
    - "~/.openclaw/scripts/verify-infra.sh"
  modified: []

key-decisions:
  - "Pinned n8n to v2.5.2 for CVE-2026-25049 patching"
  - "All ports bound to 127.0.0.1 only -- defense in depth with Tailscale"
  - "ACLs deferred -- personal tailnet, defense-in-depth only (no multi-user risk)"
  - "Tailscale serve points root path to n8n (port 5678) -- dashboard not yet running"
  - "Qdrant and n8n given tmpfs mounts for read-only FS compatibility"

patterns-established:
  - "Localhost-only port binding: All Docker services bind to 127.0.0.1, never 0.0.0.0"
  - "Container hardening baseline: non-root user, read-only FS, cap_drop ALL, no-new-privileges, PID limits"
  - "Verification scripts: Automated checks for infrastructure state at ~/.openclaw/scripts/"
  - "Secrets in .env with chmod 600: Generated passwords and encryption keys never in compose file"

requirements-completed: [INFR-01, INFR-02, INFR-03, INFR-04, INFR-05]

# Metrics
duration: cross-session
completed: 2026-02-28
---

# Phase 1 Plan 01: Docker Stack and Infrastructure Summary

**Hardened Docker stack (PostgreSQL 16, Redis 7, Qdrant, n8n 2.5.2) with localhost-only ports, Ollama models (qwen3:14b + nomic-embed-text), and Tailscale VPN-gated access**

## Performance

- **Duration:** Cross-session (checkpoint-gated)
- **Started:** 2026-02-28
- **Completed:** 2026-02-28
- **Tasks:** 3 (2 automated + 1 human-verify checkpoint)
- **Files created:** 7 (docker-compose.yml, .env, 4 data dirs, verify-infra.sh)

## Accomplishments
- Stood up 4 hardened Docker containers (postgres, redis, qdrant, n8n) on openclaw-net bridge -- all healthy
- All ports bound to 127.0.0.1 only -- zero LAN exposure confirmed
- Every container runs non-root with read-only FS, all capabilities dropped, no-new-privileges, PID limits enforced
- Pulled and verified Ollama models: qwen3:14b (inference) and nomic-embed-text (embeddings)
- Containers can reach Ollama via host.docker.internal:11434
- Tailscale serve configured for n8n remote access (https://brysons-mac-mini.tail96c7b7.ts.net/)
- Verification script passes 21/21 automated checks
- Human verified: n8n accessible from Windows machine via Tailscale

## Task Commits

Tasks modified infrastructure files at `~/.openclaw/` (outside this git repo). Commits tracked below are the documentation commit for this plan.

1. **Task 1: Create hardened Docker Compose stack** - Infrastructure files at ~/.openclaw/ (docker-compose.yml, .env, data dirs)
2. **Task 2: Pull Ollama models and configure Tailscale serve** - Scripts at ~/.openclaw/scripts/verify-infra.sh
3. **Task 3: Verify infrastructure from Windows machine** - Human checkpoint (approved)

## Files Created/Modified
- `~/.openclaw/docker-compose.yml` - Multi-service Docker Compose stack with full hardening on openclaw-net bridge
- `~/.openclaw/.env` - Generated secrets (Postgres password, Redis password, n8n auth, encryption key) with chmod 600
- `~/.openclaw/data/postgres/` - PostgreSQL persistent data directory
- `~/.openclaw/data/redis/` - Redis persistent data directory
- `~/.openclaw/data/qdrant/` - Qdrant vector storage directory
- `~/.openclaw/data/n8n/` - n8n workflow and config data directory
- `~/.openclaw/scripts/verify-infra.sh` - 21-check infrastructure verification script

## Decisions Made
- **n8n pinned to v2.5.2**: Specific version pin to address CVE-2026-25049 -- no "latest" tag
- **Localhost-only port binding**: All Docker ports use 127.0.0.1:PORT:PORT -- Tailscale is the only remote access path
- **ACLs deferred**: Personal tailnet with single user -- ACL configuration is a defense-in-depth measure, not a security gate
- **Tailscale serve root to n8n**: Port 3000 dashboard not yet running (future phase), so root path serves n8n on port 5678
- **Qdrant no user directive**: Official Qdrant image manages its own user -- added tmpfs mounts for read-only FS compatibility
- **n8n read-only FS with tmpfs**: n8n needed tmpfs mounts for writable paths to work with read-only filesystem

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Docker Compose v2 pids_limit syntax**
- **Found during:** Task 1
- **Issue:** Compose v2 requires integer pids_limit (not the deploy.resources syntax)
- **Fix:** Used top-level `pids_limit: N` directive directly on each service
- **Verification:** `docker compose config` validates successfully

**2. [Rule 3 - Blocking] Qdrant read-only FS tmpfs mounts**
- **Found during:** Task 1
- **Issue:** Qdrant needs writable paths beyond /tmp for operation with read-only filesystem
- **Fix:** Added targeted tmpfs mounts for Qdrant's writable paths
- **Verification:** Container starts and passes healthcheck with read_only: true

**3. [Rule 3 - Blocking] n8n read-only FS tmpfs mounts**
- **Found during:** Task 1
- **Issue:** n8n requires additional writable paths for operation with read-only filesystem
- **Fix:** Added tmpfs mounts for n8n's required writable directories
- **Verification:** Container starts and passes healthcheck

**4. [Rule 3 - Blocking] Container healthcheck tools**
- **Found during:** Task 1
- **Issue:** Some healthcheck commands needed adjustment for Alpine-based images
- **Fix:** Adjusted healthcheck commands to work with available tools in each container
- **Verification:** All 4 containers report healthy status

---

**Total deviations:** 4 auto-fixed (all Rule 3 - blocking issues)
**Impact on plan:** All auto-fixes were necessary to make the Docker stack operational with full security hardening. No scope creep.

## Issues Encountered
- None beyond the auto-fixed deviations above

## User Setup Required

**Tailscale ACLs (optional, defense-in-depth):**
- Location: Tailscale Admin Console > Access Controls
- Task: Restrict access to ports 3000, 18789, 5678, 22 for brysons-mac-mini to autogroup:owner only
- Status: Deferred (personal tailnet, single user -- not a blocking security concern)

## Next Phase Readiness
- Docker stack is running and ready for Plan 01-02 (n8n proxy workflows and HITL tier enforcement)
- PostgreSQL, Redis, and Qdrant are available on localhost for any service that needs them
- n8n is accessible and ready for workflow creation
- Ollama models are loaded and accessible from both host and containers
- No blockers for subsequent plans

## Self-Check: PASSED

All files verified:
- FOUND: ~/.openclaw/docker-compose.yml
- FOUND: ~/.openclaw/.env
- FOUND: ~/.openclaw/scripts/verify-infra.sh
- FOUND: ~/.openclaw/data/postgres/
- FOUND: ~/.openclaw/data/redis/
- FOUND: ~/.openclaw/data/qdrant/
- FOUND: ~/.openclaw/data/n8n/
- FOUND: .planning/phases/01-secure-infrastructure/01-01-SUMMARY.md

---
*Phase: 01-secure-infrastructure*
*Completed: 2026-02-28*

---
phase: 01-secure-infrastructure
plan: 03
subsystem: safety
tags: [cost-tracking, circuit-breaker, sqlite, pinned-directives, context-guard, emergency-stop, safety]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure
    provides: "Docker stack (01-01) with PostgreSQL, Redis, Qdrant, n8n running on openclaw-net"
provides:
  - "Cost circuit breaker module (checkLimits, recordUsage, getMonthlySpend, getSessionStats) with SQLite tracking"
  - "Reconciliation module for syncing local cost counter against Anthropic Usage API"
  - "Pinned safety directives with keyword-based verification loop"
  - "Context guard with checkpoint summarization and session halt on directive loss"
  - "Emergency stop script and documentation"
affects: [02-memory-model-routing, all-subsequent-phases]

# Tech tracking
tech-stack:
  added: [better-sqlite3, tsconfig.json]
  patterns: [circuit-breaker-pattern, keyword-based-directive-verification, structured-json-logging, graceful-degrade-on-limit-breach]

key-files:
  created:
    - "~/.openclaw/src/cost/types.ts"
    - "~/.openclaw/src/cost/tracker.ts"
    - "~/.openclaw/src/cost/reconcile.ts"
    - "~/.openclaw/src/cost/__tests__/tracker.test.ts"
    - "~/.openclaw/config/cost-limits.yaml"
    - "~/.openclaw/data/cost-tracker.db"
    - "~/.openclaw/src/safety/types.ts"
    - "~/.openclaw/src/safety/context-guard.ts"
    - "~/.openclaw/src/safety/__tests__/context-guard.test.ts"
    - "~/.openclaw/config/pinned-directives.yaml"
    - "~/.openclaw/docs/emergency-stop.md"
    - "~/.openclaw/scripts/emergency-stop.sh"
    - "~/.openclaw/tsconfig.json"
  modified:
    - "~/.openclaw/package.json"
    - "~/.openclaw/package-lock.json"

key-decisions:
  - "Used better-sqlite3 for synchronous SQLite access -- no async overhead for pre-call limit checks"
  - "Keyword-based directive verification (2-of-3 threshold) instead of exact string matching -- tolerates summarization whitespace changes"
  - "Reconciliation degrades gracefully when ANTHROPIC_ADMIN_API_KEY is not set -- local-only tracking still works"
  - "Circuit breaker logs structured JSON to stderr for observability integration"
  - "Test suite uses chmodSync to make emergency-stop.sh executable within the test itself"

patterns-established:
  - "Circuit breaker pattern: checkLimits() returns {allowed, reason, current, limits} -- callers complete current action then stop"
  - "Structured JSON logging: all safety events emit JSON with level, component, action, timestamp for observability"
  - "Keyword-based verification: context guard checks for 2+ keywords per directive, not exact text match"
  - "Checkpoint summarization: pinned directives re-injected at context compaction boundaries"
  - "Graceful degradation: modules work with reduced functionality when optional config (API keys) is missing"

requirements-completed: [SECR-03, SECR-04, SECR-06]

# Metrics
duration: 7min
completed: 2026-02-28
---

# Phase 1 Plan 03: Cost Circuit Breakers and Context Safety Summary

**SQLite-backed cost circuit breaker ($50/mo, 50 tool calls, 30min timeout) with keyword-verified pinned safety directives and emergency stop procedure**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-28T22:30:56Z
- **Completed:** 2026-02-28T22:37:30Z
- **Tasks:** 2
- **Files created:** 13

## Accomplishments
- Built cost circuit breaker module with SQLite tracking: enforces $50/month cap, 50 tool calls per session, and 30-minute session timeout
- Implemented graceful degrade behavior: agent completes current action, stops accepting new work, logs circuit breaker event with structured JSON
- Created reconciliation module that syncs local spend counter against Anthropic Usage API (degrades gracefully without admin key)
- Configured 4 pinned safety directives (HITL enforcement, DELETE rule, cost limits, no autonomous messages) with verification every 10 turns
- Built context guard with robust keyword-based matching that tolerates whitespace/formatting changes from summarization
- Verified 55-turn context exhaustion simulation -- all directives survive compaction at turns 10, 20, 30, 40, 50, 55
- Created emergency stop script and documentation for immediate agent isolation via docker compose stop
- All 18 tests pass (8 cost tracker + 10 context guard)

## Task Commits

Tasks modified infrastructure files at `~/.openclaw/` (outside this git repo). Commits tracked below are the documentation commit for this plan.

1. **Task 1: Build cost circuit breaker module with SQLite tracking** -- Infrastructure files at ~/.openclaw/ (types.ts, tracker.ts, reconcile.ts, cost-limits.yaml, cost-tracker.db, tests)
2. **Task 2: Implement context window safety and emergency stop** -- Infrastructure files at ~/.openclaw/ (context-guard.ts, types.ts, pinned-directives.yaml, emergency-stop.sh, emergency-stop.md, tests)

## Files Created/Modified
- `~/.openclaw/src/cost/types.ts` -- CostLimits, LimitCheckResult, UsageRecord type definitions
- `~/.openclaw/src/cost/tracker.ts` -- Cost tracking module: initDB, checkLimits, recordUsage, getMonthlySpend, getSessionStats, logCircuitBreakerEvent
- `~/.openclaw/src/cost/reconcile.ts` -- Reconciliation module: reconcileCosts against Anthropic Usage API
- `~/.openclaw/src/cost/__tests__/tracker.test.ts` -- 8 tests covering all limit types, circuit breaker logging, monthly spend isolation
- `~/.openclaw/config/cost-limits.yaml` -- Circuit breaker thresholds ($50/mo, 50 tool calls, 30min, Clay $100/mo, email 100/day)
- `~/.openclaw/data/cost-tracker.db` -- SQLite database with usage, sessions, circuit_breaker_events tables
- `~/.openclaw/src/safety/types.ts` -- PinnedDirective, DirectiveConfig, VerificationResult type definitions
- `~/.openclaw/src/safety/context-guard.ts` -- Context guard: loadDirectives, getPinnedDirectives, verifyDirectives, shouldCheckpoint, shouldVerify, handleVerificationFailure, checkpointSummarize
- `~/.openclaw/src/safety/__tests__/context-guard.test.ts` -- 10 tests including 55-turn simulation, whitespace tolerance, HALT signal emission
- `~/.openclaw/config/pinned-directives.yaml` -- 4 pinned directives with keyword lists, checkpoint/verification intervals
- `~/.openclaw/docs/emergency-stop.md` -- Emergency stop procedure documentation (quick stop, full shutdown, resume, key revocation)
- `~/.openclaw/scripts/emergency-stop.sh` -- Executable emergency stop script (docker compose stop)
- `~/.openclaw/tsconfig.json` -- TypeScript configuration for the project

## Decisions Made
- **better-sqlite3 for synchronous access:** checkLimits() is called before every API call -- synchronous access avoids async overhead in the hot path
- **Keyword-based verification (2-of-3 threshold):** Exact string matching is fragile when context gets summarized; keyword matching tolerates whitespace and minor rewording
- **Graceful degradation for reconciliation:** System works without ANTHROPIC_ADMIN_API_KEY -- local cost tracking still enforces limits, just without API drift correction
- **Structured JSON logging:** All circuit breaker and safety events emit JSON to stderr with level, component, action fields for future observability pipeline integration
- **chmodSync in test:** Test itself sets execute permission on emergency-stop.sh, avoiding dependency on pre-test chmod step

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tsconfig.json**
- **Found during:** Task 1
- **Issue:** No TypeScript configuration existed for the project; needed for tsx to properly resolve imports and compile
- **Fix:** Created ~/.openclaw/tsconfig.json with ES2022 target, ESNext module, bundler resolution
- **Files modified:** ~/.openclaw/tsconfig.json
- **Verification:** All tests compile and run successfully

---

**Total deviations:** 1 auto-fixed (Rule 3 - blocking)
**Impact on plan:** Minimal -- tsconfig.json is a standard project requirement. No scope creep.

## Issues Encountered
- None beyond the auto-fixed deviation above

## User Setup Required

**Anthropic Admin API Key (optional, for cost reconciliation):**
- **Env var:** ANTHROPIC_ADMIN_API_KEY
- **Source:** Anthropic Console > Settings > Admin API Keys (requires org admin access)
- **Impact if missing:** Cost tracking works with local-only counters; reconciliation against Anthropic Usage API is skipped with a warning log
- **Status:** Optional -- system fully functional without it

## Next Phase Readiness
- Cost circuit breaker module is ready for Phase 2 pipeline integration (checkLimits() wired into agent API call path)
- Pinned directives are ready for injection into agent system prompt
- Context guard verification loop ready for integration into agent turn counter
- Emergency stop procedure documented and script tested
- No blockers for subsequent plans

## Self-Check: PASSED

All files verified:
- FOUND: ~/.openclaw/data/cost-tracker.db
- FOUND: ~/.openclaw/src/cost/types.ts
- FOUND: ~/.openclaw/src/cost/tracker.ts
- FOUND: ~/.openclaw/src/cost/reconcile.ts
- FOUND: ~/.openclaw/src/cost/__tests__/tracker.test.ts
- FOUND: ~/.openclaw/config/cost-limits.yaml
- FOUND: ~/.openclaw/src/safety/types.ts
- FOUND: ~/.openclaw/src/safety/context-guard.ts
- FOUND: ~/.openclaw/src/safety/__tests__/context-guard.test.ts
- FOUND: ~/.openclaw/config/pinned-directives.yaml
- FOUND: ~/.openclaw/docs/emergency-stop.md
- FOUND: ~/.openclaw/scripts/emergency-stop.sh (executable)
- FOUND: ~/.openclaw/tsconfig.json
- FOUND: .planning/phases/01-secure-infrastructure/01-03-SUMMARY.md

---
*Phase: 01-secure-infrastructure*
*Completed: 2026-02-28*

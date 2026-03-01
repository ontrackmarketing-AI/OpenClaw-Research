---
phase: 02-memory-and-model-routing
plan: 02
subsystem: model-routing
tags: [ollama, claude, anthropic-sdk, prompt-caching, model-router, task-classifier, fallback-chain, cost-tracking]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure
    provides: "Docker services (Ollama), better-sqlite3, cost-tracker database and circuit breaker"
  - phase: 02-memory-and-model-routing
    plan: 01
    provides: "Memory system (persistent.ts loadMemory, daily-log.ts logEntry, types.ts LogEntry)"
provides:
  - "4-tier model routing: Ollama (free) -> Haiku (standard) -> Sonnet (reasoning) -> Opus (client-facing)"
  - "Task classifier with keyword matching and priority ordering (opus > sonnet > ollama, default haiku)"
  - "Automatic fallback chain with structured JSON logging of escalation events"
  - "Prompt caching with cache_control ephemeral, static-first ordering, and cache hit ratio tracking"
  - "Cost tracker integration: every router call records to Phase 1 circuit breaker database"
  - "Daily cost summary formatted per-model with token counts, logged to daily log system"
affects: [03-integrations, 04-task-management, 05-skills, 06-communication]

# Tech tracking
tech-stack:
  added: []
  patterns: ["4-tier model routing with keyword classification and automatic fallback", "Prompt caching with static-first system prompt ordering", "Cost tracker integration bridging router to Phase 1 circuit breaker", "Structured JSON stderr logging with component/action fields across all router modules"]

key-files:
  created:
    - "~/.openclaw/config/model-routing.yaml"
    - "~/.openclaw/src/router/types.ts"
    - "~/.openclaw/src/router/classifier.ts"
    - "~/.openclaw/src/router/router.ts"
    - "~/.openclaw/src/router/prompt-cache.ts"
    - "~/.openclaw/src/router/cost-tracker-integration.ts"
    - "~/.openclaw/src/router/__tests__/classifier.test.ts"
    - "~/.openclaw/src/router/__tests__/router.test.ts"
    - "~/.openclaw/src/router/__tests__/prompt-cache.test.ts"
  modified: []

key-decisions:
  - "Opus > sonnet > ollama priority in classifier -- client-facing tasks always route to highest quality tier first"
  - "checkLimits() called before every model call -- circuit breaker enforced at router entry point"
  - "Prompt caching uses static-first ordering (base prompt + MEMORY.md before dynamic context) for cache stability"
  - "Daily cost summary format: 'Today: $X.XX total -- Haiku $X.XX (NNK tok), Sonnet $X.XX (NNK tok)'"

patterns-established:
  - "Task classification: keyword matching against config YAML with tier priority ordering"
  - "Fallback chain: iterate through fallback_order from classified tier, skip unhealthy, escalate on failure"
  - "Prompt caching: buildCachedSystemPrompt() with static prefix, getCacheConfig() for tier thresholds, trackCachePerformance() for hit ratios"
  - "Cost integration: recordModelUsage() bridges ModelCallResult to Phase 1 UsageRecord"

requirements-completed: [MODL-01, MODL-02, MODL-03, MODL-04]

# Metrics
duration: 8min
completed: 2026-03-01
---

# Phase 2 Plan 2: Model Router Summary

**4-tier model routing (Ollama/Haiku/Sonnet/Opus) with keyword-based task classification, automatic fallback chain, prompt caching for Claude tiers, and Phase 1 cost tracker integration with daily summaries**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-01T03:38:28Z
- **Completed:** 2026-03-01T03:47:00Z
- **Tasks:** 2/2
- **Files created:** 9 (5 modules + 1 config + 3 test suites)
- **Total tests:** 101 (41 classifier + 21 router + 39 prompt-cache/cost), all passing

## Accomplishments
- YAML-configured 4-tier model routing: Ollama qwen3:14b (free classification), Haiku (standard), Sonnet (reasoning), Opus (client-facing)
- Task classifier with opus > sonnet > ollama priority ordering, haiku as default for unmatched tasks
- Automatic fallback chain: health-check Ollama, escalate through tiers on failure, structured JSON WARN logging for every fallback
- Prompt caching for Claude tiers: static-first system prompt ordering, cache_control ephemeral, per-tier minimum token thresholds, cache hit ratio tracking
- Cost tracker integration: every router call records to Phase 1 SQLite database, circuit breaker ($50/month cap) checked before every model call
- Daily cost summary: per-model token counts and costs formatted as "Today: $0.40 total -- Haiku $0.28 (1.2M tok), Sonnet $0.12 (40K tok)", logged to daily log system

## Task Commits

Each task was committed atomically:

1. **Task 1: Create types, config, classifier, and router with fallback chain** - `efe6d71` (feat)
2. **Task 2: Add prompt caching, cost tracker integration, daily cost summary** - `3498cfa` (feat)

Note: Commits are in the `~/.openclaw` git repository (source code repo), not the research repo.

## Files Created/Modified
- `~/.openclaw/config/model-routing.yaml` - 4-tier definitions with model IDs, cost rates, classification keywords, cache thresholds
- `~/.openclaw/src/router/types.ts` - ModelTier, TaskClass, RoutingResult, ModelCallResult, TierConfig, RouterConfig
- `~/.openclaw/src/router/classifier.ts` - loadRouterConfig(), classifyTask() with opus > sonnet > ollama priority, CLASSIFICATION_RULES
- `~/.openclaw/src/router/router.ts` - healthCheck(), callTier() (Ollama + Claude dispatch), routeAndCall() with fallback chain, limit checks, usage recording
- `~/.openclaw/src/router/prompt-cache.ts` - buildCachedSystemPrompt(), getCacheConfig(), trackCachePerformance()
- `~/.openclaw/src/router/cost-tracker-integration.ts` - recordModelUsage(), getDailyCostSummary(), logDailyCostSummary()
- `~/.openclaw/src/router/__tests__/classifier.test.ts` - 41 tests for config loading, classification, priority, context strings
- `~/.openclaw/src/router/__tests__/router.test.ts` - 21 tests for routing, fallback, all-exhaust, structured logging
- `~/.openclaw/src/router/__tests__/prompt-cache.test.ts` - 39 tests for caching, cost recording, daily summary, token formatting

## Decisions Made
- **Opus > sonnet > ollama classification priority**: When a task matches both opus and sonnet keywords (e.g. "analyze the client proposal"), opus wins because client-facing quality is the higher priority.
- **checkLimits() at router entry**: Circuit breaker is enforced once before any tier is attempted, not per-tier. If limits are exceeded, no model call is made at all.
- **Static-first system prompt ordering**: Base prompt and MEMORY.md content form the cacheable prefix. Dynamic context (time, session) comes last so it does not break the cache.
- **Daily cost summary format**: Matches user specification exactly: "Today: $0.42 total -- Haiku $0.28 (1.2M tok), Sonnet $0.12 (40K tok), Opus $0.02 (2K tok), Ollama $0.00 (500K tok)"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test expectations for classifier priority ordering**
- **Found during:** Task 1 (classifier tests)
- **Issue:** Test expected "analyze this proposal for gaps" to route to sonnet, but "proposal" is an opus keyword and opus has higher priority
- **Fix:** Updated test expectations to match actual priority behavior; added separate pure-sonnet test case
- **Files modified:** src/router/__tests__/classifier.test.ts, src/router/__tests__/router.test.ts
- **Verification:** All 62 classifier+router tests pass
- **Committed in:** efe6d71 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test expectations)
**Impact on plan:** Test expectations corrected to match the classifier's documented priority behavior. No scope creep.

## Issues Encountered
None - both tasks completed without blocking issues.

## User Setup Required
None - no external service configuration required. Ollama and Qdrant are already running from Phase 1. Anthropic API key (ANTHROPIC_API_KEY) is needed at runtime for Claude tiers but is already configured.

## Next Phase Readiness
- Phase 2 complete: Memory system + Model router both operational
- All subsequent phases can use routeAndCall() for cost-effective LLM calls
- Daily cost summaries available via logDailyCostSummary()
- Prompt caching reduces cost for repeated system prompt patterns
- Kimi and Gemini deferred as planned -- only core 4-tier stack implemented

## Self-Check: PASSED

- All 9 files verified present
- Both task commits verified (efe6d71, 3498cfa)
- All 101 tests passing (41 classifier + 21 router + 39 prompt-cache/cost)
- Config YAML valid: 4 tiers, fallback_order correct

---
*Phase: 02-memory-and-model-routing*
*Completed: 2026-03-01*

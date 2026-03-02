---
phase: 06-per-task-rag
plan: 01
subsystem: memory
tags: [qdrant, rag, task-isolation, write-gates, cron, telegram-callbacks, dedup, outcome-indexing]

# Dependency graph
requires:
  - phase: 02-memory-and-model-routing
    provides: "Qdrant client factory, EMBEDDING_DIM, embed(), deterministicId() patterns"
  - phase: 03-telegram-command-channel
    provides: "Telegram callback handler registration, registerCallbacks(), escapeMarkdownV2()"
provides:
  - "Per-task Qdrant collections (5 types) with isolated outcome storage"
  - "Outcome indexing pipeline with dedup and pollution filtering"
  - "Write gate lifecycle (pending -> confirmed/rejected)"
  - "Nightly promotion cron at 2 AM with quality gate"
  - "Telegram operator validation via validate-outcome: callback"
  - "getPendingReviewSummary() for weekly check-in surfacing"
  - "postExecutionHook() convenience wrapper for skill integrations"
affects: [06-per-task-rag-plan-02, skill-execution-hooks, checkin-engine]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-task collection isolation in Qdrant (one collection per skill type)"
    - "Write gate pattern: pending -> confirmed via TTL + quality gate or operator validation"
    - "Outcome pollution filter: shouldIndex() rejects routine successes"
    - "Dedup via cosine similarity threshold (0.95) with frequency counter increment"
    - "Dynamic import for cross-module graceful degradation in callbacks.ts"

key-files:
  created:
    - "~/.openclaw/src/task-rag/types.ts"
    - "~/.openclaw/src/task-rag/collection-manager.ts"
    - "~/.openclaw/src/task-rag/outcome-indexer.ts"
    - "~/.openclaw/src/task-rag/write-gates.ts"
    - "~/.openclaw/config/task-rag.yaml"
    - "~/.openclaw/src/task-rag/__tests__/collection-manager.test.ts"
    - "~/.openclaw/src/task-rag/__tests__/outcome-indexer.test.ts"
    - "~/.openclaw/src/task-rag/__tests__/write-gates.test.ts"
  modified:
    - "~/.openclaw/src/telegram/callbacks.ts"

key-decisions:
  - "Custom test runner (npx tsx) instead of vitest -- matches existing project test pattern from Phase 2"
  - "Dynamic import for write-gates in callbacks.ts -- graceful degradation if task-rag module not yet loaded"
  - "shouldIndex() rejects routine successes with no correction/pattern -- prevents outcome index pollution"
  - "Quality gate on auto-promotion: only success=true or has operator_correction qualifies"
  - "Task type included in deterministicOutcomeId hash input -- prevents cross-collection ID collisions"

patterns-established:
  - "Per-task collection naming: task-{type} (e.g., task-email-triage)"
  - "Outcome lifecycle: skill execution -> shouldIndex filter -> dedup check -> pending upsert -> TTL/operator promotion -> confirmed"
  - "Write gate quality gate: failed outcomes without corrections stay pending indefinitely"

requirements-completed: [PRAG-01, PRAG-02, PRAG-04]

# Metrics
duration: 6min
completed: 2026-03-02
---

# Phase 6 Plan 1: Per-Task RAG Core Summary

**Per-task Qdrant collections with outcome indexing pipeline, dedup filtering, write gate lifecycle, and Telegram operator validation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-02T21:59:52Z
- **Completed:** 2026-03-02T22:05:53Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- 5 per-task Qdrant collections defined with 768-dim Cosine vectors and 3 payload indexes each (status, indexed_at, success)
- Outcome indexer filters routine successes, deduplicates near-identical outcomes via 0.95 cosine threshold, and indexes actionable outcomes with "pending" status
- Write gate promotion runs nightly at 2 AM with quality gate (success=true OR operator_correction required for auto-promotion)
- Operator can confirm/reject outcomes via Telegram inline buttons (validate-outcome: callback with dynamic import)
- 93 total test assertions passing across 3 test suites

## Task Commits

Each task was committed atomically:

1. **Task 1: Create types, config, and collection manager** - `2a4d2cf` (feat)
2. **Task 2: Create outcome indexer with dedup** - `7b015d6` (feat)
3. **Task 3: Create write gates with promotion cron and Telegram validation** - `3259673` (feat)

## Files Created/Modified
- `~/.openclaw/src/task-rag/types.ts` - OutcomeRecord, TaskType, WriteGateStatus, TASK_COLLECTIONS, OutcomePayload, TaskRagConfig
- `~/.openclaw/config/task-rag.yaml` - 5 task types with collection names, recall limits, write gate settings, dedup config
- `~/.openclaw/src/task-rag/collection-manager.ts` - Qdrant collection lifecycle with ensureTaskCollection, ensureAllCollections, getCollectionName
- `~/.openclaw/src/task-rag/outcome-indexer.ts` - indexOutcome, buildOutcomeNarrative, shouldIndex, postExecutionHook, checkDuplicate, deterministicOutcomeId
- `~/.openclaw/src/task-rag/write-gates.ts` - promotePendingEntries, operatorValidateOutcome, getPendingReviewSummary, scheduleWriteGatePromotion
- `~/.openclaw/src/task-rag/__tests__/collection-manager.test.ts` - 27 assertions for collection lifecycle
- `~/.openclaw/src/task-rag/__tests__/outcome-indexer.test.ts` - 35 assertions for outcome indexing
- `~/.openclaw/src/task-rag/__tests__/write-gates.test.ts` - 31 assertions for write gate lifecycle
- `~/.openclaw/src/telegram/callbacks.ts` - Extended with validate-outcome: callback handler for operator confirm/reject

## Decisions Made
- **Custom test runner pattern:** Used npx tsx with custom assert() function (matching Phase 2 pattern) instead of vitest (not installed in project). All tests follow the same structure: assert/passed/failed counters with process.exit(1) on failure.
- **Dynamic import for write-gates in callbacks.ts:** Uses `await import('../task-rag/write-gates.js')` to ensure graceful degradation if the task-rag module hasn't loaded yet.
- **shouldIndex() as pollution filter:** Routine successes (success=true, no correction, no pattern) are never indexed, preventing the outcome collections from filling with unactionable data.
- **Quality gate on auto-promotion:** The nightly cron checks `success === true OR operator_correction truthy` before promoting pending entries. Failed outcomes without corrections stay pending indefinitely until operator review.
- **Task type in hash input:** deterministicOutcomeId includes taskType in the djb2 hash to prevent cross-collection ID collisions when the same session produces outcomes across multiple task types.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used project's existing test runner pattern instead of vitest**
- **Found during:** Task 1 (test creation)
- **Issue:** Plan specified vitest, but vitest is not installed in the project. All existing tests use custom assert() pattern with npx tsx.
- **Fix:** Created tests following existing project convention (custom assert, npx tsx runner)
- **Files modified:** All 3 test files
- **Verification:** All 93 assertions pass across 3 test suites
- **Committed in:** 2a4d2cf, 7b015d6, 3259673

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Test runner adaptation ensures consistency with existing codebase. No functional impact -- all planned test cases are covered.

## Issues Encountered
None -- all 3 tasks executed cleanly with all tests passing on first run.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Per-task RAG core is complete. Plan 06-02 (recall pipeline) can now build on these collections and types.
- postExecutionHook() is ready for skill integration wiring.
- getPendingReviewSummary() is ready for Phase 4 check-in engine weekly surfacing.
- Telegram validate-outcome: callback is registered and will work once outcomes start flowing.

## Self-Check: PASSED

All 9 files verified present. All 3 task commits verified (2a4d2cf, 7b015d6, 3259673).

---
*Phase: 06-per-task-rag*
*Completed: 2026-03-02*

---
phase: 06-per-task-rag
plan: 02
subsystem: memory
tags: [qdrant, rag, pre-task-recall, client-knowledge, prompt-cache, dedup, cross-workflow]

# Dependency graph
requires:
  - phase: 06-per-task-rag-plan-01
    provides: "Per-task Qdrant collections, outcome indexer, write gates, types, collection-manager"
  - phase: 02-memory-and-model-routing
    provides: "embed(), createQdrantClient(), createOllamaClient(), EMBEDDING_DIM, buildCachedSystemPrompt()"
provides:
  - "Pre-task recall from task-specific collections with confirmed 2x weighting"
  - "Formatted lessons injection after prompt cache breakpoint"
  - "Cross-workflow client knowledge indexing with dedup per contact_id"
  - "Semantic query ('what do we know about [client]?') and direct lookup by contact_id"
  - "Auto-indexing of client knowledge from postExecutionHook when contact info present"
  - "Config-driven recall limits per task type (proposal-gen: 5, check-in: 1, others: 3)"
affects: [skill-execution-hooks, checkin-engine, prompt-construction, client-context-queries]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-task recall with write gate status weighting (confirmed 1.0x, pending 0.5x)"
    - "Lessons injection after prompt cache breakpoint (dynamicContext position)"
    - "Client knowledge dedup via 0.90 cosine similarity with source field merging"
    - "buildClientKnowledgeFromOutcome task-type-specific formatters"
    - "Auto-indexing client knowledge from postExecutionHook when contact info present"

key-files:
  created:
    - "~/.openclaw/src/task-rag/pre-task-recall.ts"
    - "~/.openclaw/src/task-rag/client-knowledge.ts"
    - "~/.openclaw/src/task-rag/__tests__/pre-task-recall.test.ts"
    - "~/.openclaw/src/task-rag/__tests__/client-knowledge.test.ts"
  modified:
    - "~/.openclaw/src/task-rag/collection-manager.ts"
    - "~/.openclaw/src/task-rag/outcome-indexer.ts"
    - "~/.openclaw/src/task-rag/__tests__/collection-manager.test.ts"

key-decisions:
  - "Recall lessons placed after prompt cache breakpoint (dynamicContext) -- preserves cache stability for repeated calls"
  - "Client knowledge dedup threshold 0.90 (lower than outcome 0.95) -- client knowledge is more varied across sources"
  - "postExecutionHook auto-indexes client knowledge -- no manual wiring needed by skill callers"
  - "formatLessons priority order: errors > corrections > patterns > successes with 2000-char cap"
  - "skipOllama defaults to true for pre-execution hook -- classification tasks don't benefit from recall"

patterns-established:
  - "Pre-task recall: recallForTask -> formatLessons -> preExecutionHook -> inject into dynamicContext"
  - "Client knowledge lifecycle: skill execution -> postExecutionHook -> buildClientKnowledgeFromOutcome -> indexClientKnowledge with dedup"
  - "Source merging on duplicate: existing source 'email-triage' + new 'proposal-gen' -> 'email-triage,proposal-gen'"

requirements-completed: [PRAG-03, PRAG-05]

# Metrics
duration: 7min
completed: 2026-03-02
---

# Phase 6 Plan 2: Pre-Task Recall and Client Knowledge Summary

**Pre-task recall with confirmed 2x weighting and lessons injection after cache breakpoint, plus cross-workflow client knowledge RAG with dedup and auto-indexing from skill executions**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-02T22:09:19Z
- **Completed:** 2026-03-02T22:15:52Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Pre-task recall queries task-specific Qdrant collections with confirmed entries weighted 2x over pending, then formats prioritized lessons (errors > corrections > patterns > successes) capped at ~500 tokens
- Client knowledge collection with 4 payload indexes (contact_id, knowledge_type, status, indexed_at) supports both semantic search and direct contact_id lookup
- postExecutionHook in outcome-indexer auto-indexes client knowledge when contactId and contactName are present -- no manual wiring needed by callers
- Dedup per contact_id at 0.90 cosine threshold merges the source field on duplicate instead of creating redundant entries
- 98 new test assertions across 2 test suites (42 pre-task-recall + 56 client-knowledge), all Plan 01 tests updated and passing (192 total across 5 suites)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pre-task recall module** - `1cfead6` (feat)
2. **Task 2: Create client knowledge collection and cross-workflow indexing** - `63b7af3` (feat)

## Files Created/Modified
- `~/.openclaw/src/task-rag/pre-task-recall.ts` - recallForTask, formatLessons, preExecutionHook, loadRecallConfig with confirmed 2x weighting
- `~/.openclaw/src/task-rag/client-knowledge.ts` - indexClientKnowledge, queryClientKnowledge, buildClientKnowledgeFromOutcome, deterministicClientKnowledgeId, checkClientKnowledgeDuplicate
- `~/.openclaw/src/task-rag/__tests__/pre-task-recall.test.ts` - 42 assertions: recall weighting, filter, config limits, lessons formatting, hook injection
- `~/.openclaw/src/task-rag/__tests__/client-knowledge.test.ts` - 56 assertions: collection creation, indexing, dedup, semantic/direct query, postExecutionHook wiring
- `~/.openclaw/src/task-rag/collection-manager.ts` - Added CLIENT_KNOWLEDGE_COLLECTION, ensureClientKnowledgeCollection (4 indexes), updated ensureAllCollections
- `~/.openclaw/src/task-rag/outcome-indexer.ts` - Extended postExecutionHook with contactName parameter and auto-indexClientKnowledge wiring
- `~/.openclaw/src/task-rag/__tests__/collection-manager.test.ts` - Updated ensureAllCollections test for 6 collections (5 task + 1 client-knowledge)

## Decisions Made
- **Recall lessons after cache breakpoint:** Lessons are injected as dynamicContext in buildCachedSystemPrompt(), preserving the cacheable prefix (base prompt + memory) across calls. This is the critical design choice for cost efficiency.
- **Client knowledge dedup threshold 0.90:** Lower than outcome dedup (0.95) because the same knowledge expressed differently across sources should still be caught as duplicate. Example: "Acme prefers email" from email-triage and "Acme communication preference: email" from check-in.
- **Auto-index from postExecutionHook:** Skills don't need to manually call indexClientKnowledge. When contactId and contactName are present, the hook automatically builds and indexes client knowledge. Zero-effort integration for future skills.
- **formatLessons priority order:** Errors and corrections are the most valuable for improving task execution. Success patterns are lowest priority and first to be dropped when hitting the 2000-char cap.
- **skipOllama defaults to true:** Ollama-tier tasks are classification tasks that don't benefit from recall (no past outcomes improve keyword matching). Saves an embedding call per Ollama-tier execution.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated collection-manager tests for new client-knowledge collection**
- **Found during:** Task 2 (verification)
- **Issue:** Plan 01's collection-manager.test.ts expected 5 createCollection calls and 15 index calls, but ensureAllCollections now creates 6 collections (5 task + 1 client-knowledge) with 19 indexes (5*3 + 1*4)
- **Fix:** Updated assertions to expect 6 collections and 19 indexes, added assertion for client-knowledge collection presence
- **Files modified:** ~/.openclaw/src/task-rag/__tests__/collection-manager.test.ts
- **Verification:** All 28 collection-manager test assertions pass
- **Committed in:** 63b7af3

---

**Total deviations:** 1 auto-fixed (1 bug -- test assertion update for intentional behavior change)
**Impact on plan:** Expected consequence of extending ensureAllCollections. No scope creep.

## Issues Encountered
None -- both tasks executed cleanly with all tests passing.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 6 (Per-Task RAG) is now complete. Both plans delivered:
  - Plan 01: per-task collections, outcome indexing, write gates, Telegram validation
  - Plan 02: pre-task recall with weighting, client knowledge RAG with dedup
- Full recall pipeline: skill execution -> postExecutionHook -> outcome indexing + client knowledge -> pre-task recall on next execution
- 192 total test assertions across 5 suites, all passing
- Ready for skill integration: any skill calling postExecutionHook gets both outcome indexing and client knowledge automatically

## Self-Check: PASSED

All 7 files verified present. Both task commits verified (1cfead6, 63b7af3).

---
*Phase: 06-per-task-rag*
*Completed: 2026-03-02*

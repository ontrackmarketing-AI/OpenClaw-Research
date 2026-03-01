---
phase: 02-memory-and-model-routing
plan: 01
subsystem: memory
tags: [sqlite, fts5, qdrant, ollama, nomic-embed-text, rrf, vector-search, compaction]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure
    provides: "Docker services (Qdrant, Ollama), better-sqlite3, cost-tracker patterns"
provides:
  - "Persistent MEMORY.md with topic sections, auto-compaction, and overflow files"
  - "SQLite FTS5 full-text search with BM25 ranking and porter unicode61 tokenizer"
  - "Qdrant vector search with nomic-embed-text 768-dim embeddings (cosine similarity)"
  - "Hybrid RRF search with query-adaptive weights (exact/conceptual/mixed)"
  - "Daily log writing to date-stamped markdown files"
  - "Tiered log compaction: daily->weekly (30d) and weekly->monthly (90d)"
affects: [02-02-model-routing, 03-integrations, 04-task-management, 05-skills]

# Tech tracking
tech-stack:
  added: ["@qdrant/js-client-rest@1.17.0", "ollama@0.6.3", "@anthropic-ai/sdk@0.78.0", "node-cron@3.0.3", "@types/node-cron"]
  patterns: ["Hybrid RRF search with query-adaptive weights", "Structural compaction preserving significant entries", "Topic-based MEMORY.md with overflow files", "Content-hash deduplication for indexing"]

key-files:
  created:
    - "~/.openclaw/src/memory/types.ts"
    - "~/.openclaw/src/memory/persistent.ts"
    - "~/.openclaw/src/memory/daily-log.ts"
    - "~/.openclaw/src/memory/fts5-index.ts"
    - "~/.openclaw/src/memory/vector-search.ts"
    - "~/.openclaw/src/memory/hybrid-search.ts"
    - "~/.openclaw/src/memory/compaction.ts"
    - "~/.openclaw/src/memory/__tests__/persistent.test.ts"
    - "~/.openclaw/src/memory/__tests__/fts5-index.test.ts"
    - "~/.openclaw/src/memory/__tests__/vector-search.test.ts"
    - "~/.openclaw/src/memory/__tests__/hybrid-search.test.ts"
    - "~/.openclaw/src/memory/__tests__/compaction.test.ts"
  modified:
    - "~/.openclaw/package.json"

key-decisions:
  - "Structural compaction (no LLM) for log and memory compaction -- avoids model dependency until router available in 02-02"
  - "Content-hash deduplication for FTS5 indexing -- skip re-index if content unchanged"
  - "Deterministic IDs for Qdrant points from path+chunkIndex hash -- enables consistent upsert/delete"
  - "Initialized git repo at ~/.openclaw for source code version control"

patterns-established:
  - "Hybrid search: classify query type, apply adaptive weights, run FTS5+Qdrant in parallel, merge with RRF"
  - "Log compaction: preserve decision/error/interaction/cost entries, drop routine actions, keep day bookends"
  - "Memory overflow: sections exceeding 500 tokens move to overflow files with summary reference in MEMORY.md"
  - "Structured JSON stderr logging with component/action fields across all memory modules"

requirements-completed: [MEMR-01, MEMR-02, MEMR-03, MEMR-04, MEMR-05]

# Metrics
duration: 9min
completed: 2026-03-01
---

# Phase 2 Plan 1: Memory System Summary

**7-module TypeScript memory system with FTS5 keyword search, Qdrant vector search, hybrid RRF merge with query-adaptive weights, and tiered log compaction**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-01T03:24:12Z
- **Completed:** 2026-03-01T03:34:00Z
- **Tasks:** 3/3
- **Files created:** 12 (7 modules + 5 test suites)
- **Total tests:** 120 (108 unit + 12 integration), all passing

## Accomplishments
- Persistent MEMORY.md with topic-section organization, auto-compaction at 4000-token threshold, and overflow files for large sections
- SQLite FTS5 full-text search with BM25 ranking, porter unicode61 tokenizer, content-hash dedup, and ~200-token paragraph chunking
- Qdrant vector search with nomic-embed-text 768-dim embeddings, 0.7 cosine similarity threshold, and deterministic point IDs
- Hybrid RRF search that classifies queries as exact/conceptual/mixed and applies adaptive weights (0.7 FTS5 for names, 0.7 vector for concepts)
- Daily log writing to date-stamped files with tiered compaction: daily to weekly after 30 days, weekly to monthly after 90 days
- Comprehensive test coverage: 120 tests across 5 test suites, all passing without external services (except integration tests which pass with Docker stack)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install deps, create types, persistent memory, daily log** - `5daf9b1` (feat)
2. **Task 2: Build FTS5 index, Qdrant vector search, hybrid RRF merge** - `c9b6f1c` (feat)
3. **Task 3: Build log compaction scheduler** - `0b5f2ab` (feat)

Note: Commits are in the `~/.openclaw` git repository (source code repo), not the research repo.

## Files Created/Modified
- `~/.openclaw/src/memory/types.ts` - Shared types: MemoryEntry, SearchResult, LogEntry, QueryType, CompactionResult, MemoryConfig
- `~/.openclaw/src/memory/persistent.ts` - MEMORY.md read/write/compact with 4000-token budget, topic sections, overflow files
- `~/.openclaw/src/memory/daily-log.ts` - Date-stamped daily log entries at logs/YYYY/MM/DD.md
- `~/.openclaw/src/memory/fts5-index.ts` - SQLite FTS5 with documents+chunks tables, porter unicode61 tokenizer, BM25 search
- `~/.openclaw/src/memory/vector-search.ts` - Qdrant collection management, Ollama embedding, cosine similarity search
- `~/.openclaw/src/memory/hybrid-search.ts` - Query classification, adaptive RRF weights, parallel search + merge
- `~/.openclaw/src/memory/compaction.ts` - Cron-scheduled log compaction: daily->weekly (30d), weekly->monthly (90d)
- `~/.openclaw/src/memory/__tests__/persistent.test.ts` - 31 tests for memory load/append/compact
- `~/.openclaw/src/memory/__tests__/fts5-index.test.ts` - 20 tests for FTS5 tables, indexing, search
- `~/.openclaw/src/memory/__tests__/vector-search.test.ts` - 12 integration tests for embedding, collection, round-trip
- `~/.openclaw/src/memory/__tests__/hybrid-search.test.ts` - 34 tests for query classification, weights, RRF fusion
- `~/.openclaw/src/memory/__tests__/compaction.test.ts` - 23 tests for daily/weekly/monthly compaction
- `~/.openclaw/package.json` - Added @qdrant/js-client-rest, ollama, @anthropic-ai/sdk, node-cron

## Decisions Made
- **Structural compaction (no LLM) for initial implementation**: Log compaction uses rule-based filtering (keep decision/error/interaction/cost, drop routine actions) rather than LLM summarization. LLM-based compaction can be added when the model router (Plan 02-02) is available.
- **Content-hash deduplication for FTS5 indexing**: Documents are re-indexed only when content changes, avoiding unnecessary re-chunking and FTS5 rebuilds.
- **Deterministic IDs for Qdrant points**: Hash of path+chunkIndex produces consistent numeric IDs, enabling idempotent upserts and reliable deletes by path.
- **Initialized git at ~/.openclaw**: The source code directory now has version control for per-task atomic commits.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all tasks completed without issues. Both Qdrant and Ollama Docker services were running and integration tests passed on first attempt.

## User Setup Required
None - no external service configuration required. Qdrant and Ollama are already running from Phase 1.

## Next Phase Readiness
- Memory system complete and ready for all subsequent phases
- Plan 02-02 (Model Router) can now use the memory system for context retrieval
- FTS5 + Qdrant + Hybrid search APIs ready for skill development in later phases
- Log compaction scheduler can be started when the agent process begins

## Self-Check: PASSED

- All 13 files verified present
- All 3 task commits verified (5daf9b1, c9b6f1c, 0b5f2ab)
- All 120 tests passing (108 unit + 12 integration)
- Qdrant openclaw-memory collection verified (status: green, 768-dim Cosine)
- All 4 new npm dependencies verified in package.json

---
*Phase: 02-memory-and-model-routing*
*Completed: 2026-03-01*

---
phase: 04-task-management-and-context-capture
plan: 01
subsystem: task-management
tags: [notion, todo, transcript, fellow, apple-notes, llm-extraction, dedup, applescript]

# Dependency graph
requires:
  - phase: 03-telegram-command-channel
    provides: Gmail poller with email triage, Notion action log, Telegram bot, LLM router
provides:
  - Notion todo database CRUD with dedup by sourceId
  - Central todo aggregator (single entry point for all sources)
  - LLM-powered transcript extraction pipeline (decisions, action items, open questions)
  - Fellow REST API client for meeting transcript processing
  - Apple Notes reader via AppleScript for call transcript processing
  - Email-to-todo wiring from existing Gmail poller
affects: [04-02, 04-03, 05-proposal-pipeline, 06-per-task-rag]

# Tech tracking
tech-stack:
  added: [fellow-rest-api, applescript-via-osascript]
  patterns: [fire-and-forget-todo-creation, sourceId-dedup, llm-json-extraction-with-fence-stripping, chunked-transcript-processing]

key-files:
  created:
    - ~/.openclaw/src/todo/types.ts
    - ~/.openclaw/src/todo/notion-todo.ts
    - ~/.openclaw/src/todo/aggregator.ts
    - ~/.openclaw/src/todo/__tests__/aggregator.test.ts
    - ~/.openclaw/src/transcripts/types.ts
    - ~/.openclaw/src/transcripts/extractor.ts
    - ~/.openclaw/src/transcripts/fellow.ts
    - ~/.openclaw/src/transcripts/apple-notes.ts
    - ~/.openclaw/src/transcripts/__tests__/extractor.test.ts
  modified:
    - ~/.openclaw/src/gmail/poller.ts

key-decisions:
  - "Fellow REST API (not MCP) for programmatic scheduled transcript access"
  - "AppleScript via osascript for Apple Notes access -- no third-party dependency"
  - "Single aggregator entry point for all todo sources -- enforces dedup consistently"
  - "Fire-and-forget error handling on Notion writes -- log errors, never throw"
  - "LLM extraction uses Haiku tier via routeAndCall for cost efficiency"
  - "Chunked extraction for long transcripts (>32000 chars) with merge and dedup"

patterns-established:
  - "sourceId dedup pattern: {source}:{id}:action:{index} for all todo sources"
  - "LLM JSON extraction with markdown code fence stripping"
  - "Graceful degradation: missing API keys or permissions log warning and return 0"
  - "State file pattern: ~/.openclaw/data/{service}-state.json for checkpoint timestamps"

requirements-completed: [TASK-01, TASK-02, TASK-03]

# Metrics
duration: cross-session
completed: 2026-03-02
---

# Phase 4 Plan 01: Todo Aggregation and Transcript Pipeline Summary

**Notion todo database with sourceId dedup, LLM transcript extraction pipeline for Fellow meetings and Apple Notes calls, and email-to-todo wiring from Gmail poller**

## Performance

- **Duration:** Cross-session (Tasks 1-2 executed, Task 3 checkpoint approved)
- **Started:** 2026-03-02
- **Completed:** 2026-03-02T16:13:53Z
- **Tasks:** 3 (2 auto + 1 checkpoint approved)
- **Files modified:** 10

## Accomplishments
- Notion todo database with full CRUD (create, query, dedup check) and 7 properties (Task, Priority, Source, Status, Due Date, Context, Source ID)
- Central aggregator with sourceId-based deduplication -- all todo sources (email, Fellow, Apple Notes, iMessage, manual, check-in) go through a single createTodo() entry point
- LLM-powered transcript extraction pipeline that produces structured JSON (decisions, action items, open questions) from any text input, with chunking for long transcripts
- Fellow REST API client that fetches meetings since last check, extracts content, and creates todos with proper sourceIds
- Apple Notes reader via AppleScript that searches for call transcripts and processes them through the same extraction pipeline
- Email-to-todo wiring in the Gmail poller -- actionable triage results automatically become todos with source 'email'

## Task Commits

Each task was committed atomically:

1. **Task 1: Create todo types, Notion todo database module, and aggregator with dedup** - `51aeb80` (feat)
2. **Task 2: Create transcript extraction pipeline, Fellow client, Apple Notes reader, and email-to-todo wiring** - `55ed2cc` (feat)
3. **Task 3: Verify Notion todo database and transcript pipeline** - checkpoint:human-verify (approved)

## Files Created/Modified
- `~/.openclaw/src/todo/types.ts` - TodoItem, TodoSource, TodoPriority, TodoStatus, TodoQuery type definitions
- `~/.openclaw/src/todo/notion-todo.ts` - Notion todo database CRUD with createNotionTodo, todoExists (dedup), queryTodos
- `~/.openclaw/src/todo/aggregator.ts` - Central createTodo entry point with dedup check and action log cross-logging
- `~/.openclaw/src/todo/__tests__/aggregator.test.ts` - Unit tests for aggregator dedup, Notion page construction, query parsing
- `~/.openclaw/src/transcripts/types.ts` - ExtractedContent, ActionItem, Decision, OpenQuestion, TranscriptSource, AppleNote types
- `~/.openclaw/src/transcripts/extractor.ts` - LLM extraction pipeline with chunking, code fence stripping, and merge
- `~/.openclaw/src/transcripts/fellow.ts` - Fellow REST API client with state tracking and meeting processing
- `~/.openclaw/src/transcripts/apple-notes.ts` - AppleScript-based Notes reader with search and transcript processing
- `~/.openclaw/src/transcripts/__tests__/extractor.test.ts` - Unit tests for extraction, code fence handling, chunking, merge
- `~/.openclaw/src/gmail/poller.ts` - Modified to wire actionable emails into todo aggregator

## Decisions Made
- **Fellow REST API over MCP:** Chose direct REST API for programmatic scheduled access rather than MCP, since this runs on a timer not interactively
- **AppleScript via osascript:** Used native AppleScript execution through child_process rather than any third-party Apple Notes library -- avoids dependencies and works reliably on macOS
- **Single aggregator pattern:** All todo sources must go through aggregator.createTodo() -- ensures dedup is consistently applied regardless of source
- **Fire-and-forget on Notion writes:** Following the action-log.ts pattern, Notion API failures are logged but never thrown -- prevents upstream callers from breaking
- **Haiku tier for extraction:** Transcript extraction uses routeAndCall which routes to Haiku for cost efficiency -- extraction is a standard task, not reasoning-intensive
- **Chunked extraction with merge:** Transcripts over ~32000 chars are split into chunks, extracted separately, and merged with dedup on task text

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** The plan's `user_setup` section specifies:
- **Notion Todo Database:** Create a database titled "OpenClaw Todos" in the same workspace as the Action Log, connect the OpenClaw integration, set `NOTION_TODO_DB_ID` env var
- **Fellow API:** Enable Developer API in Fellow Workspace Settings > Security, generate Personal API Key, set `FELLOW_API_KEY` env var
- **Apple Notes Automation:** Grant Automation permission for Terminal/Node to control Notes.app in System Settings > Privacy & Security > Automation

## Next Phase Readiness
- Todo aggregator is ready for Plan 04-02 (BlueBubbles iMessage) to wire iMessage context as another todo source
- Todo aggregator is ready for Plan 04-03 (Proactive check-ins) to query open todos via queryTodos() for context assembly
- Transcript extraction pipeline is reusable by any future source that produces text content
- Email-to-todo wiring is live and will activate as soon as the Gmail poller runs

## Self-Check: PASSED

- All 10 files verified present on disk
- Commit 51aeb80 (Task 1) verified in git log
- Commit 55ed2cc (Task 2) verified in git log
- Task 3 checkpoint approved by operator

---
*Phase: 04-task-management-and-context-capture*
*Completed: 2026-03-02*

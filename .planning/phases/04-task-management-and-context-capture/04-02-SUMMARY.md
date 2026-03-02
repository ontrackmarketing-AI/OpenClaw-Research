---
phase: 04-task-management-and-context-capture
plan: 02
subsystem: communication
tags: [bluebubbles, imessage, privacy, polling, context-extraction, node-cron, todo-enrichment]

# Dependency graph
requires:
  - phase: 04-task-management-and-context-capture
    plan: 01
    provides: Notion todo aggregator (createTodo), todo types (TodoItem, TodoSource)
  - phase: 02-memory-and-model-routing
    provides: Model router (routeAndCall) for LLM-powered topic summarization
provides:
  - BlueBubbles REST client with abstraction layer for backend swapping
  - Privacy-preserving iMessage poller (business contacts only, no raw text persisted)
  - LLM-powered context extraction producing 5-10 word topic summaries
  - Actionable iMessage-to-todo pipeline via central aggregator
  - In-memory business context cache for check-in engine consumption
affects: [04-03, 06-per-task-rag]

# Tech tracking
tech-stack:
  added: [bluebubbles-rest-api]
  patterns: [privacy-preserving-context-extraction, business-contact-whitelist, abstraction-layer-for-backend-swap, in-memory-context-cache]

key-files:
  created:
    - ~/.openclaw/src/imessage/types.ts
    - ~/.openclaw/src/imessage/client.ts
    - ~/.openclaw/src/imessage/poller.ts
    - ~/.openclaw/src/imessage/context.ts
    - ~/.openclaw/src/imessage/__tests__/poller.test.ts
  modified: []

key-decisions:
  - "BlueBubbles REST API with abstraction layer -- client.ts is the only file that changes if backend swaps to chat.db relay"
  - "Business contact whitelist via BUSINESS_CONTACTS env var -- personal messages never processed or stored"
  - "LLM topic extraction via Ollama tier (free) -- 5-10 word summaries, raw message text never persisted"
  - "In-memory context cache (max 50 entries) for check-in engine -- no disk persistence of message content"
  - "Graceful degradation without BlueBubbles -- all methods return empty, no crash"

patterns-established:
  - "Privacy-preserving extraction: LLM produces summaries, raw text discarded immediately"
  - "Abstraction layer pattern: single-file swap point for external service backends"
  - "Business contact whitelist: BUSINESS_CONTACTS env var parsed once, applied to all polling"

requirements-completed: [COMM-05, COMM-06]

# Metrics
duration: cross-session
completed: 2026-03-02
---

# Phase 4 Plan 02: iMessage Context via BlueBubbles Summary

**BlueBubbles REST client with privacy-preserving poller, LLM topic extraction, and iMessage-to-todo pipeline**

## Performance

- **Duration:** cross-session
- **Started:** 2026-03-02
- **Completed:** 2026-03-02
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 5

## Accomplishments
- BlueBubbles REST client with abstraction layer enabling backend swap without touching poller or context logic
- Privacy-preserving context extraction -- raw iMessage text never persisted, only 5-10 word LLM topic summaries
- Business contact whitelist filtering ensures personal messages are never processed
- Actionable messages automatically create Notion todos via the central aggregator with source 'imessage'
- In-memory context cache (max 50 entries) available for check-in engine to query recent business conversations
- 20 tests covering all behaviors including privacy verification

## Task Commits

Each task was committed atomically:

1. **Task 1: Create iMessage types, BlueBubbles client, poller, and context extractor** - `b43e170` (feat)
2. **Task 2: Verify iMessage integration setup and privacy** - checkpoint:human-verify (approved)

## Files Created/Modified
- `~/.openclaw/src/imessage/types.ts` - BBMessage, MessageContext, iMessageConfig type definitions
- `~/.openclaw/src/imessage/client.ts` - BlueBubbles REST client with abstraction layer, 5s timeout, graceful degradation
- `~/.openclaw/src/imessage/context.ts` - Privacy-preserving context extraction, LLM topic summarization, todo creation for actionable messages
- `~/.openclaw/src/imessage/poller.ts` - Periodic polling via node-cron, state persistence in imessage-state.json, re-export of getRecentBusinessContext
- `~/.openclaw/src/imessage/__tests__/poller.test.ts` - 20 tests covering filtering, privacy, actionable detection, caching, and graceful degradation

## Decisions Made
- BlueBubbles REST API with abstraction layer -- client.ts is the only file that changes if backend swaps to chat.db relay (June 2026 Apple API deprecation contingency)
- Business contact whitelist via BUSINESS_CONTACTS env var -- personal messages never processed or stored
- LLM topic extraction via Ollama tier (free) -- 5-10 word summaries only, raw message text discarded after extraction
- In-memory context cache (max 50 entries) for check-in engine -- no disk persistence of message content
- Graceful degradation without BlueBubbles password -- all methods log warning and return empty arrays

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** The following environment variables must be set before iMessage polling will function:

- `BLUEBUBBLES_URL` -- BlueBubbles server URL (default: http://localhost:1234)
- `BLUEBUBBLES_PASSWORD` -- BlueBubbles server password set during installation
- `BUSINESS_CONTACTS` -- Comma-separated phone numbers or email addresses of business contacts

BlueBubbles must be installed on the Mac where Messages.app is active. Download from bluebubbles.app.

## Next Phase Readiness
- iMessage context cache (`getRecentBusinessContext`) is ready for 04-03 check-in engine to consume
- Todo pipeline is complete -- all sources (email, Fellow, Apple Notes, iMessage) feed into the central aggregator
- BlueBubbles June 2026 deprecation noted -- abstraction layer in client.ts enables backend swap

## Self-Check: PASSED

- All 5 created files verified on disk
- Commit b43e170 verified in git history

---
*Phase: 04-task-management-and-context-capture*
*Completed: 2026-03-02*

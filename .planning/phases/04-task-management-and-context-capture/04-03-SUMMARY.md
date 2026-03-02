---
phase: 04-task-management-and-context-capture
plan: 03
subsystem: checkin, telegram
tags: [cron, sqlite, node-cron, grammy, llm-personalization, adaptive-timing, proactive-checkin]

# Dependency graph
requires:
  - phase: 03-telegram-command-channel
    provides: Telegram bot framework (grammY), sendMessage, escapeMarkdownV2, registerCommands, registerCallbacks
  - phase: 04-01
    provides: queryTodos, createTodo, TodoItem types from Notion todo aggregator
provides:
  - Proactive check-in engine with 5 daily time slots and cron scheduling
  - Adaptive timing that drops low-engagement slots after 14 days (30% threshold, min 2 slots)
  - Anti-repetition template selection (last 10 tracked, no repeat within 3 days)
  - Parallel context assembly from todos, calendar, iMessage, approvals, and memory with 2s timeout
  - LLM-personalized check-in messages via model router
  - Telegram delivery with inline response buttons (Got it / Snooze / + Todo)
  - /checkin on-demand command
  - SQLite engagement tracking (checkin.db)
affects: [06-per-task-rag, 07-ocr-screen-watching]

# Tech tracking
tech-stack:
  added: [node-cron]
  patterns: [adaptive-timing-with-engagement-tracking, anti-repetition-template-pools, parallel-context-assembly-with-timeout, cron-based-slot-scheduling]

key-files:
  created:
    - ~/.openclaw/src/checkin/types.ts
    - ~/.openclaw/src/checkin/templates.ts
    - ~/.openclaw/src/checkin/adaptive.ts
    - ~/.openclaw/src/checkin/context-assembler.ts
    - ~/.openclaw/src/checkin/engine.ts
    - ~/.openclaw/src/checkin/__tests__/adaptive.test.ts
    - ~/.openclaw/src/checkin/__tests__/engine.test.ts
  modified:
    - ~/.openclaw/src/telegram/commands.ts
    - ~/.openclaw/src/telegram/callbacks.ts

key-decisions:
  - "node-cron for slot scheduling -- lightweight, no external dependency, cron expressions match plan spec"
  - "SQLite checkin.db separate from approvals.db and cost.db -- dedicated file for check-in engagement isolation"
  - "Dynamic import for iMessage context -- graceful degradation if 04-02 module not available"
  - "2-second timeout on remote context sources -- check-ins send even if calendar/iMessage/memory are slow"
  - "LLM personalization via routeAndCall with Haiku tier -- cost-efficient for daily recurring task"

patterns-established:
  - "Adaptive timing: track engagement per slot, drop below threshold after minimum data points, enforce floor"
  - "Anti-repetition: pool-based template selection with SQLite history, LRU fallback when all recently used"
  - "Parallel context assembly: local sources first (always fast), remote sources via Promise.allSettled with timeout"
  - "Calendar-aware deferral: check isOperatorBusy before sending, retry after 15 minutes"

requirements-completed: [TASK-04, TASK-05, TASK-06]

# Metrics
duration: cross-session
completed: 2026-03-02
---

# Phase 4 Plan 3: Proactive Check-in Engine Summary

**Proactive check-in engine with 5 daily cron slots, adaptive engagement-based timing, anti-repetition template pools, parallel context assembly from 5 sources, LLM personalization, and Telegram inline button responses**

## Performance

- **Duration:** cross-session
- **Started:** 2026-03-02
- **Completed:** 2026-03-02
- **Tasks:** 3 (2 auto + 1 checkpoint:human-verify)
- **Files created/modified:** 9

## Accomplishments
- Check-in engine schedules 5 weekday slots (8am, 10am, 1pm, 3pm, 5pm) via node-cron with daily adaptive recalculation
- Context assembler fetches open todos, pending approvals, calendar events, iMessage context, and MEMORY.md in parallel with 2-second timeouts on remote sources
- Anti-repetition system tracks last 10 template IDs in SQLite and prevents same template within 3 days, with LRU fallback
- Adaptive timing drops slots below 30% response rate after 10+ data points, enforcing minimum 2 slots (morning + evening)
- LLM personalizes each check-in message using template skeleton + assembled context via model router
- Calendar-aware deferral: checks isOperatorBusy() before sending, retries in 15 minutes if operator is in a meeting
- Inline Telegram buttons (Got it / Snooze 1hr / + Todo) track engagement and create actions
- /checkin command provides on-demand check-ins that bypass the busy check

## Task Commits

Each task was committed atomically:

1. **Task 1: Create check-in types, templates, adaptive timing, and context assembler** - `1e07849` (feat)
2. **Task 2: Create check-in engine, wire Telegram commands and callbacks** - `6825d8b` (feat)
3. **Task 3: Verify check-in engine sends personalized messages via Telegram** - checkpoint:human-verify (approved)

## Files Created/Modified
- `src/checkin/types.ts` - CheckinSlot, EngagementRecord, CheckinContext, TemplateEntry type definitions with weekday cron schedules
- `src/checkin/templates.ts` - Template pools (4-6 per slot) with anti-repetition selection using SQLite history
- `src/checkin/adaptive.ts` - SQLite engagement tracking: initCheckinDB, recordCheckin, recordResponse, getSlotEngagement, getActiveSlots
- `src/checkin/context-assembler.ts` - Parallel context fetching from todos, calendar, iMessage, approvals, memory with 2s timeout
- `src/checkin/engine.ts` - Check-in orchestrator: startCheckinEngine, stopCheckinEngine, triggerCheckin, executeCheckin with LLM personalization
- `src/checkin/__tests__/adaptive.test.ts` - Tests for engagement tracking, slot adaptation, template anti-repetition
- `src/checkin/__tests__/engine.test.ts` - Tests for engine flow, busy deferral, on-demand trigger, cron lifecycle
- `src/telegram/commands.ts` - Extended with /checkin command and updated /help text
- `src/telegram/callbacks.ts` - Extended with checkin:ack, checkin:snooze, checkin:todo callback handlers

## Decisions Made
- **node-cron for slot scheduling** -- lightweight, no external dependency, cron expressions match the plan spec exactly
- **SQLite checkin.db separate from approvals.db and cost.db** -- dedicated file for check-in engagement isolation, consistent with project pattern
- **Dynamic import for iMessage context** -- graceful degradation if 04-02 module not available yet (parallel wave execution)
- **2-second timeout on remote context sources** -- check-ins always send on time even if calendar/iMessage/memory APIs are slow
- **LLM personalization via routeAndCall** -- uses existing model router for cost-efficient Haiku-tier personalization

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. The check-in engine uses existing Telegram bot token, Notion API key, and Google Calendar credentials already configured in previous phases.

## Next Phase Readiness
- Phase 4 is now fully complete -- all 3 plans (todo aggregation, iMessage context, proactive check-ins) delivered
- Phase 5 (Proposal Pipeline) can begin -- it depends on Phase 4 for context assembly and todo integration
- The check-in engine provides the proactive engagement layer that Phase 7 (OCR Screen Watching) will enrich with screen context

## Self-Check: PASSED

- All 9 files verified present in ~/.openclaw repo
- Commit 1e07849 (Task 1) verified in git history
- Commit 6825d8b (Task 2) verified in git history
- Task 3 checkpoint approved by operator

---
*Phase: 04-task-management-and-context-capture*
*Completed: 2026-03-02*

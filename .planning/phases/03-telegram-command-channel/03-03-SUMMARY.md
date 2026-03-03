---
phase: 03-telegram-command-channel
plan: 03
subsystem: communication
tags: [google-calendar, freebusy, notion, action-log, calendar-awareness, deferral, fire-and-forget]

# Dependency graph
requires:
  - plan: 03-01
    provides: "Telegram bot, callbacks.ts, approval queue, enforceHITLAsync"
  - plan: 03-02
    provides: "Gmail OAuth2 client, email triage, calendar extractor, ExtractedCalendarEvent, poller"
provides:
  - "Google Calendar event insertion via shared Gmail OAuth2 client"
  - "Calendar-aware message deferral using freebusy.query"
  - "Notion Action Log database with automatic logging of all agent actions"
  - "Fire-and-forget logging pattern (never blocks primary workflow)"
  - "cal:add / cal:skip Telegram callback handlers for calendar event confirmation"
  - "Deferred message queue with periodic flush when operator becomes free"
affects: [04-task-management, 05-proposal-pipeline]

# Tech tracking
tech-stack:
  added: ["@notionhq/client"]
  patterns: [freebusy-query, calendar-aware-deferral, fire-and-forget-logging, notion-data-source-id, pending-event-map]

key-files:
  created:
    - "~/.openclaw/src/calendar/client.ts"
    - "~/.openclaw/src/calendar/awareness.ts"
    - "~/.openclaw/src/calendar/__tests__/awareness.test.ts"
    - "~/.openclaw/src/notion/types.ts"
    - "~/.openclaw/src/notion/client.ts"
    - "~/.openclaw/src/notion/action-log.ts"
    - "~/.openclaw/src/notion/__tests__/action-log.test.ts"
  modified:
    - "~/.openclaw/src/telegram/callbacks.ts"
    - "~/.openclaw/src/telegram/bot.ts"
    - "~/.openclaw/src/gmail/poller.ts"

key-decisions:
  - "Shared OAuth2 client between Gmail and Calendar -- scopes requested together in 03-02"
  - "freebusy.query for busy detection -- lightweight, no event detail exposure"
  - "Fire-and-forget Notion logging -- logAction never throws, errors logged to stderr only"
  - "In-memory Map<string, ExtractedCalendarEvent> for pending calendar events -- simple, sufficient for single-operator use"
  - "data_source_id for Notion page creation -- per 2025-09-03 API version requirement"
  - "15-minute minimum gap threshold for getNextFreeSlot"
  - "Notion database created via MCP API with all properties configured programmatically"

patterns-established:
  - "Calendar callback pattern: cal:add:{messageId} / cal:skip:{messageId} data format"
  - "Calendar-aware sendMessage wrapper: checks isOperatorBusy() before non-urgent sends"
  - "Deferred message flush: periodic check (5min interval) sends queued messages when free"
  - "Notion action log: every agent action logged with type, status, source, timestamp"
  - "storePendingCalendarEvent / retrievePendingCalendarEvent for cross-module event passing"

requirements-completed: [COMM-03, COMM-07, COMM-08]

# Metrics
duration: ~cross-session
completed: 2026-03-01
---

# Phase 3 Plan 03: Calendar, Calendar Awareness, and Notion Action Log Summary

**Google Calendar event insertion, calendar-aware message deferral, and Notion action logging for centralized visibility**

## Performance

- **Duration:** Cross-session (code + Notion MCP setup + human verification)
- **Started:** 2026-03-01
- **Completed:** 2026-03-01
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 10 (7 created, 3 modified)

## Accomplishments

- Google Calendar event insertion via Telegram inline buttons -- operator taps "Add to Calendar" and event appears in Google Calendar
- Calendar-aware deferral checks operator's freebusy status before sending non-urgent messages; deferred messages flush when operator becomes free
- Notion Action Log database created and configured with 5 properties (Action, Type, Status, Source, Timestamp) and 6 type options + 3 status options
- All agent actions (email triage, calendar adds, HITL approvals/rejections) logged to Notion automatically
- Fire-and-forget logging pattern ensures Notion failures never block primary workflows
- 205 total tests passing across all 6 test suites (31 awareness + 39 action-log + 36 bot + 39 triage + 32 approval-queue + 28 classify)

## Task Commits

1. **Task 1: Create Google Calendar client, calendar awareness, and Notion action log** - `66dbf5e` (feat)
2. **Task 2: Wire calendar callbacks, deferral, and Notion logging into Telegram bot** - `f3c1df8` (feat)
3. **Task 3: End-to-end verification** - checkpoint (human-verify, approved)

## Files Created/Modified

- `src/calendar/client.ts` - createCalendarClient(), insertCalendarEvent() using shared Gmail OAuth2
- `src/calendar/awareness.ts` - isOperatorBusy(), getNextFreeSlot(), shouldDeferMessage() via freebusy.query
- `src/calendar/__tests__/awareness.test.ts` - 31 tests covering busy detection, gap finding, deferral logic, event formatting
- `src/notion/types.ts` - LogActionType, LogEntry, NotionConfig type definitions
- `src/notion/client.ts` - createNotionClient(), getDataSourceId() with module-level caching
- `src/notion/action-log.ts` - logAction(), logBatch() with fire-and-forget error handling
- `src/notion/__tests__/action-log.test.ts` - 39 tests covering page creation, error swallowing, batch processing, property mapping
- `src/telegram/callbacks.ts` - Added cal:add/cal:skip handlers, storePendingCalendarEvent(), logAction() calls on approve/reject
- `src/telegram/bot.ts` - Added calendar-aware sendMessage() wrapper with deferred message queue and periodic flush
- `src/gmail/poller.ts` - Added logAction() calls after triage, storePendingCalendarEvent() for inline buttons, sendMessage() wrapper usage

## Deviations from Plan

### Setup via MCP

**1. [Setup] Notion database created via MCP instead of manual UI**
- **Found during:** Task 3 (human verification)
- **Issue:** Notion integration had no page access -- needed to connect via browser
- **Fix:** Used Chrome browser automation to connect OpenClaw integration to the database page, then used Notion MCP API (update-a-data-source) to configure all 5 properties and select options programmatically
- **Impact:** Faster and more precise than manual UI setup; verified with test entry via API

**Total deviations:** 1 (setup method change, no code impact)

## User Setup Completed

- Notion internal integration "OpenClaw" connected to Action Log database page
- Database schema configured: Action (title), Type (select with 6 options), Status (select with 3 options), Source (rich_text), Timestamp (date)
- NOTION_ACTION_LOG_DB_ID added to ~/.openclaw/.env
- Test entry written and verified via MCP API
- Database ID: 3173b89b-6e27-807d-9a2c-f2d872f7b1b9

## Phase 3 Complete

This plan completes Phase 3 (Telegram Command Channel). All 3 plans delivered:

| Plan | Deliverable | Requirements |
|------|------------|-------------|
| 03-01 | Telegram bot + HITL approval queue | COMM-04, COMM-02 |
| 03-02 | Gmail OAuth2 + email triage | COMM-01, COMM-03 |
| 03-03 | Calendar insertion + awareness + Notion log | COMM-03, COMM-07, COMM-08 |

**Phase 3 requirements completed:** COMM-01, COMM-02, COMM-03, COMM-04, COMM-07, COMM-08, SECR-02

## Self-Check: PASSED

- All 10 files verified (7 created, 3 modified): FOUND
- Commit 66dbf5e (Task 1): FOUND
- Commit f3c1df8 (Task 2): FOUND
- Notion database accessible via MCP API: VERIFIED
- Test entry in Notion Action Log: VERIFIED
- 205 tests passing across 6 suites: VERIFIED

---
*Phase: 03-telegram-command-channel*
*Completed: 2026-03-01*

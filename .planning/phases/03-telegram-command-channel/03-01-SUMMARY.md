---
phase: 03-telegram-command-channel
plan: 01
subsystem: communication
tags: [telegram, grammy, hitl, approval-queue, sqlite, inline-keyboard, markdownv2]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure
    provides: "HITL tier classification (classify.ts, enforce.ts) and structured JSON logging pattern"
  - phase: 02-memory-and-model-routing
    provides: "Cost tracker (getDailyCostSummary) for /status command"
provides:
  - "Telegram bot with /start, /help, /status commands and operator whitelist"
  - "SQLite-backed HITL approval queue with race condition protection"
  - "YELLOW-tier async approval via Telegram inline buttons (approve/reject)"
  - "enforceHITLAsync function for Telegram dispatch of YELLOW-tier actions"
  - "executeApprovedAction stub for future skill dispatch wiring"
affects: [03-02, 03-03, 04-task-management, 05-proposal-pipeline]

# Tech tracking
tech-stack:
  added: [grammy]
  patterns: [telegram-inline-keyboard, sqlite-approval-queue, async-hitl-dispatch, markdownv2-escaping]

key-files:
  created:
    - "~/.openclaw/src/telegram/bot.ts"
    - "~/.openclaw/src/telegram/commands.ts"
    - "~/.openclaw/src/telegram/callbacks.ts"
    - "~/.openclaw/src/telegram/formatters.ts"
    - "~/.openclaw/src/telegram/types.ts"
    - "~/.openclaw/src/telegram/__tests__/bot.test.ts"
    - "~/.openclaw/src/hitl/__tests__/approval-queue.test.ts"
  modified:
    - "~/.openclaw/src/hitl/types.ts"
    - "~/.openclaw/src/hitl/enforce.ts"
    - "~/.openclaw/src/hitl/approval-queue.ts"
    - "~/.openclaw/src/hitl/__tests__/classify.test.ts"

key-decisions:
  - "grammY for Telegram bot framework -- lightweight, TypeScript-native, well-documented"
  - "SQLite approvals.db separate from cost.db -- dedicated file for approval queue isolation"
  - "Synchronous enforceHITL preserved for backward compatibility; enforceHITLAsync added for Telegram dispatch"
  - "executeApprovedAction is a logging stub -- real skill dispatch wires in when email/task skills are built"
  - "Updated classify.test.ts assertions for new YELLOW behavior (intentional change, not regression)"

patterns-established:
  - "Telegram inline keyboard pattern: approve:{id} / reject:{id} callback data format"
  - "Approval queue atomic claim: UPDATE WHERE status='pending' returns affected rows for race condition protection"
  - "MarkdownV2 escaping: all 18 special characters escaped via escapeMarkdownV2() utility"
  - "Async HITL pattern: enforceHITLAsync dispatches to Telegram, returns approvalId for tracking"

requirements-completed: [COMM-04, COMM-02]

# Metrics
duration: ~10min
completed: 2026-03-01
---

# Phase 3 Plan 01: Telegram Bot and HITL Approval Queue Summary

**grammY Telegram bot with operator whitelist, /start /help /status commands, and SQLite-backed YELLOW-tier approval queue with inline approve/reject buttons**

## Performance

- **Duration:** ~10 min (2 tasks auto + 1 checkpoint)
- **Started:** 2026-03-01
- **Completed:** 2026-03-01
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 15 (9 created, 6 modified including package.json/lock)

## Accomplishments

- Telegram bot with grammY framework responding to /start, /help, /status commands with operator-only whitelist middleware
- SQLite-backed approval queue storing YELLOW-tier actions with atomic claim protection against race conditions (double-tap on approve/reject)
- YELLOW-tier actions now dispatch to Telegram as inline keyboard messages instead of being blocked -- completes the SECR-02 approval channel deferred from Phase 1
- 96 total tests passing (36 bot + 32 approval queue + 28 classify with updated assertions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Telegram bot with command handlers and user whitelist** - `67a7420` (feat)
2. **Task 2: Create HITL approval queue and wire YELLOW-tier to Telegram** - `6b6876c` (feat)
3. **Task 3: Verify Telegram bot is running and HITL approval works** - checkpoint (human-verify, approved)

## Files Created/Modified

- `src/telegram/bot.ts` - Bot factory with createBot(), startBot(), getBotInstance(), operator whitelist middleware
- `src/telegram/commands.ts` - /start, /help, /status command handlers with MarkdownV2 formatting
- `src/telegram/callbacks.ts` - Approve/reject callback query handlers, executeApprovedAction stub
- `src/telegram/formatters.ts` - escapeMarkdownV2, formatApprovalMessage, formatStatusMessage utilities
- `src/telegram/types.ts` - BotConfig, BotStatus type definitions
- `src/telegram/__tests__/bot.test.ts` - 36 tests covering formatting, config, whitelist, commands
- `src/hitl/approval-queue.ts` - SQLite-backed queue: initApprovalDB, savePendingApproval, getPendingApproval, updateApprovalStatus, getPendingCount, requestApproval
- `src/hitl/types.ts` - Extended with ApprovalStatus, ApprovalRequest, ApprovalCallback, approvalId on HITLResult
- `src/hitl/enforce.ts` - YELLOW returns "queued for Telegram approval"; added enforceHITLAsync for async dispatch
- `src/hitl/__tests__/approval-queue.test.ts` - 32 tests covering DB operations, race conditions, status transitions
- `src/hitl/__tests__/classify.test.ts` - Updated 8 YELLOW-tier assertions for new "queued" behavior
- `package.json` / `package-lock.json` - Added grammy dependency

## Decisions Made

- **grammY over Telegraf**: grammY is actively maintained, TypeScript-native, and lighter weight -- aligns with project preference for modern TS libraries
- **Separate approvals.db**: Approval queue uses its own SQLite database (~/.openclaw/data/approvals.db) rather than sharing cost.db -- isolates concerns and avoids locking contention
- **Dual enforce functions**: Kept synchronous `enforceHITL` for backward compatibility (returns status without dispatching); added `enforceHITLAsync` that actually sends to Telegram -- callers choose which path they need
- **Stub executeApprovedAction**: Logs approval to stderr as structured JSON but does not execute real actions -- real skill dispatch (email sending, task creation) wires in when those skills are built in later phases
- **classify.test.ts assertion updates**: Changed YELLOW-tier test expectations from "blocked" to "queued for Telegram approval" -- this is an intentional behavior change, not a regression

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated classify.test.ts assertions for YELLOW behavior change**
- **Found during:** Task 2 (HITL approval queue wiring)
- **Issue:** Changing YELLOW-tier from "blocked" to "queued for Telegram approval" caused 8 existing classify tests to fail
- **Fix:** Updated test assertions to match new YELLOW behavior -- the old "blocked" message was intentionally replaced
- **Files modified:** src/hitl/__tests__/classify.test.ts
- **Verification:** All 28 classify tests pass with updated assertions
- **Committed in:** 6b6876c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix -- test assertions for intentional behavior change)
**Impact on plan:** Necessary consequence of the planned YELLOW-tier behavior change. No scope creep.

## Issues Encountered

None -- plan executed cleanly.

## User Setup Required

**External services require manual configuration.** The Telegram bot requires:
- `TELEGRAM_BOT_TOKEN` -- obtain from BotFather on Telegram via /newbot command
- `TELEGRAM_OPERATOR_ID` -- send /start to @userinfobot on Telegram to get numeric user ID

These must be set as environment variables before starting the bot.

## Next Phase Readiness

- Telegram bot infrastructure is complete and ready for 03-02 (Gmail triage) to send email summaries through the bot
- Approval queue is ready for any YELLOW-tier action to be dispatched -- future skills just call `enforceHITLAsync`
- `executeApprovedAction` stub is the wiring point for real skill execution (email sending, calendar events, etc.)
- SECR-02 Telegram approval channel is now delivered -- requirement can be marked as complete after 03-02/03-03 finish the remaining COMM requirements

## Self-Check: PASSED

- All 11 files verified (7 created, 4 modified): FOUND
- Commit 67a7420 (Task 1): FOUND
- Commit 6b6876c (Task 2): FOUND

---
*Phase: 03-telegram-command-channel*
*Completed: 2026-03-01*

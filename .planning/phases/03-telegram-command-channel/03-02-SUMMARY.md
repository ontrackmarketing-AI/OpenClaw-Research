---
phase: 03-telegram-command-channel
plan: 02
subsystem: communication
tags: [gmail, oauth2, email-triage, llm-classification, haiku, calendar-extraction, poller, historyid, markdownv2, cliproxyapi]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure
    provides: "Structured JSON logging pattern"
  - phase: 02-memory-and-model-routing
    provides: "Model router with routeAndCall() and Haiku tier classification"
  - plan: 03-01
    provides: "Telegram bot, escapeMarkdownV2, registerCommands, InlineKeyboard"
provides:
  - "Gmail OAuth2 client with auto-refresh tokens"
  - "Email triage engine classifying emails via Haiku tier (actionable/informational/spam/calendar-event)"
  - "Calendar event extraction from email text via LLM"
  - "Periodic inbox polling with historyId deduplication"
  - "/triage command for on-demand inbox scan"
  - "/quiet command stub for quiet hours configuration"
  - "Google Cloud project with 9+ APIs enabled (Gmail, Calendar, Drive, Sheets, Meet, etc.)"
  - "CLIProxyAPI integration for using Claude Code OAuth as standard API endpoint"
affects: [03-03, 04-task-management]

# Tech tracking
tech-stack:
  added: [googleapis, cliproxyapi]
  patterns: [oauth2-desktop-flow, email-classification, metadata-only-fetch, historyid-dedup, markdown-code-fence-strip, telegram-message-chunking]

key-files:
  created:
    - "~/.openclaw/src/gmail/types.ts"
    - "~/.openclaw/src/gmail/client.ts"
    - "~/.openclaw/src/gmail/triage.ts"
    - "~/.openclaw/src/gmail/poller.ts"
    - "~/.openclaw/src/gmail/auth-setup.ts"
    - "~/.openclaw/src/gmail/__tests__/triage.test.ts"
    - "~/.openclaw/src/calendar/types.ts"
    - "~/.openclaw/src/calendar/extractor.ts"
    - "~/.openclaw/config/google-credentials.json"
    - "~/.openclaw/config/google-tokens.json"
  modified:
    - "~/.openclaw/src/telegram/commands.ts"
    - "~/.openclaw/config/model-routing.yaml"

key-decisions:
  - "CLIProxyAPI for model access -- uses Claude Code OAuth as standard Anthropic API endpoint via local proxy on port 8317"
  - "Metadata-only Gmail fetch (format: 'metadata') -- respects rate limits per research Pitfall 6"
  - "Sequential email processing -- single user, 10-20 emails max, rate-limit friendly"
  - "Strip markdown code fences from LLM JSON responses -- Haiku wraps JSON in ```json blocks"
  - "Chunk Telegram messages over 4000 chars to stay under 4096 limit"
  - "Max 20 emails per triage run -- keeps latency and cost reasonable"
  - "Google Cloud project 'OpenClaw' under heliumsolutions.io org with 9+ APIs enabled"
  - "Single OAuth2 credential for all Google APIs (Desktop app type)"

patterns-established:
  - "JSON code fence stripping: content.replace(/^```(?:json)?\\s*\\n?/, '').replace(/\\n?```\\s*$/, '') before JSON.parse"
  - "Telegram message chunking: split by newlines at 4000 char boundary"
  - "Lazy Gmail auth initialization in /triage command handler"
  - "historyId-based polling: save after triage, use for incremental fetches"

requirements-completed: [COMM-01, COMM-03]

# Metrics
duration: ~cross-session (manual setup + debugging)
completed: 2026-03-01
---

# Phase 3 Plan 02: Gmail OAuth2 and Email Triage Summary

**Gmail OAuth2 client, LLM-powered email triage via Haiku tier through CLIProxyAPI, calendar event extraction, periodic polling, /triage command**

## Performance

- **Duration:** Cross-session (included manual Google Cloud setup, CLIProxyAPI setup, and debugging)
- **Started:** 2026-03-01
- **Completed:** 2026-03-01
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files modified:** 12 (10 created, 2 modified)

## Accomplishments

- Gmail OAuth2 client with auto-refresh tokens shared across Gmail and Calendar APIs
- Email triage classifies inbox emails via Haiku tier into actionable/informational/spam/calendar-event categories
- Calendar event extraction parses meeting details from email text via LLM
- Periodic polling with historyId deduplication (daily at 08:00 via node-cron)
- /triage command triggers on-demand inbox scan with formatted MarkdownV2 results
- Google Cloud project created with 9+ APIs enabled (Gmail, Calendar, Drive, Sheets, Meet, Docs, Search Console, Analytics, YouTube)
- CLIProxyAPI installed and configured as local proxy (port 8317) to use Claude Code subscription for API calls

## Task Commits

1. **Task 1: Gmail OAuth2 client, email triage engine, calendar extractor** - `1b90595` (feat)
2. **Task 2: Email poller with historyId dedup, /triage and /quiet commands** - `afd9fb9` (feat)
3. **Task 3: Verify Gmail OAuth2 setup and email triage** - checkpoint (human-verify, approved after fixes)
   - Bug fix commit: `0a5d28d` -- strip markdown code fences from JSON, chunk long messages

## Deviations from Plan

### Auto-fixed Issues

**1. [Bug] Haiku wraps JSON in markdown code fences**
- **Found during:** Task 3 (human verification)
- **Issue:** Haiku returns `\`\`\`json {...} \`\`\`` instead of raw JSON, causing JSON.parse to fail on every classification
- **Fix:** Added code fence stripping in triage.ts and extractor.ts before JSON.parse
- **Committed in:** 0a5d28d

**2. [Bug] Telegram message too long for 201-email inbox**
- **Found during:** Task 3 (human verification)
- **Issue:** Formatted MarkdownV2 summary exceeded Telegram's 4096 char limit
- **Fix:** Added message chunking in poller.ts (split at 4000 chars by line), reduced maxResults from 50 to 20
- **Committed in:** 0a5d28d

**3. [Setup] CLIProxyAPI required for model access**
- **Found during:** Task 3 (human verification)
- **Issue:** No ANTHROPIC_API_KEY available -- user uses Claude Code OAuth, not a direct API key
- **Fix:** Installed CLIProxyAPI (brew), authenticated with Claude OAuth, configured as local proxy on port 8317
- **Impact:** ANTHROPIC_BASE_URL=http://127.0.0.1:8317 with proxy API key in .env

**Total deviations:** 3 auto-fixed (2 bugs, 1 setup requirement)

## User Setup Completed

- Google Cloud project "OpenClaw" (grounded-apogee-488920-v4) created under heliumsolutions.io
- OAuth consent screen configured (Internal, bryson@heliumsolutions.io)
- OAuth 2.0 Desktop client created ("OpenClaw Agent")
- Credentials saved to ~/.openclaw/config/google-credentials.json
- OAuth tokens obtained and saved to ~/.openclaw/config/google-tokens.json
- CLIProxyAPI installed, authenticated, and running as background service

## Next Phase Readiness

- Gmail client and OAuth2 tokens ready for 03-03 to share for Calendar event insertion
- Calendar event extraction provides ExtractedCalendarEvent objects for 03-03 to insert
- Inline "Add to Calendar" / "Skip" buttons already sent for calendar-event emails -- 03-03 wires the callback handlers
- CLIProxyAPI proxy provides model access for all future LLM calls

## Self-Check: PASSED

- All 12 files verified (10 created, 2 modified): FOUND
- Commit 1b90595 (Task 1): FOUND
- Commit afd9fb9 (Task 2): FOUND
- Commit 0a5d28d (bug fixes): FOUND

---
*Phase: 03-telegram-command-channel*
*Completed: 2026-03-01*

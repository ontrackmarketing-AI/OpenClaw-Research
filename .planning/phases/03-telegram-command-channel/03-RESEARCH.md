# Phase 3: Telegram Command Channel - Research

**Researched:** 2026-03-01
**Domain:** Telegram Bot API, Gmail API, Google Calendar API, Notion API, HITL approval workflows
**Confidence:** HIGH

## Summary

Phase 3 transforms the agent from a background system into an interactive assistant the operator can communicate with in real time. The core is a Telegram bot that serves as the primary command interface -- delivering email triage summaries, presenting approve/reject buttons for HITL decisions, extracting calendar events from emails, respecting meeting schedules, and logging everything to Notion.

The standard stack is grammY (Telegram bot framework), googleapis (Gmail + Calendar), and @notionhq/client (Notion SDK). All three are mature, actively maintained, TypeScript-native libraries with strong ecosystem support. grammY is the clear winner over Telegraf and node-telegram-bot-api for new TypeScript projects -- it has better types, active maintenance, and a robust plugin system. The googleapis package provides a unified OAuth2 client for both Gmail and Calendar APIs. The Notion SDK recently underwent a breaking change (API version 2025-09-03) requiring `data_source_id` instead of `database_id` for page creation and queries -- this must be accounted for by using @notionhq/client v5+.

**Primary recommendation:** Use grammY with long polling for development and Tailscale Funnel webhooks for production. Use Gmail polling via `history.list` (not Cloud Pub/Sub push notifications) to avoid infrastructure complexity. Extend the existing HITL `enforce.ts` to support async Telegram approval for YELLOW-tier actions.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COMM-01 | User can receive email triage summary via Telegram -- Gmail inbox scanned, actionable items surfaced with sender, subject, and suggested action | Gmail API `messages.list` + `messages.get` with `gmail.readonly` scope; LLM classification via model router; grammY message formatting with MarkdownV2 |
| COMM-02 | User can approve/reject agent-proposed email actions via inline Telegram buttons | grammY InlineKeyboard with callback queries; extend HITL enforce.ts to support async approval via Telegram; `editMessageText` to update status after decision |
| COMM-03 | Agent extracts calendar events from emails and proposes adding them to Google Calendar | LLM extraction of date/time/title from email body; Google Calendar API `events.insert` with `calendar.events` scope; Telegram confirmation flow with inline buttons |
| COMM-04 | Telegram bot serves as primary command interface -- HITL approvals, agent queries, status updates, quiet hours | grammY Bot class with command handlers, callback query handlers, user whitelist via `allowed_users`, quiet hours config |
| COMM-07 | Agent respects Google Calendar -- no check-ins during meetings, defers non-urgent actions to free slots | Google Calendar API `freebusy.query` or `events.list` for current time window; schedule deferral logic before sending Telegram messages |
| COMM-08 | Notion integration for centralized task/action logging -- all agent actions and captured items visible in one place | Notion API v2025-09-03 with @notionhq/client v5+; single database (action log) with data_source_id; page creation for each logged action |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| grammy | 1.40.x | Telegram bot framework -- bot lifecycle, message handling, inline keyboards, callback queries | Best TypeScript support, active maintenance, superior to Telegraf (lagging types) and NTBA (no TS). Plugin ecosystem for sessions, menus, conversations. |
| googleapis | 171.x | Gmail API + Google Calendar API -- unified OAuth2 client, message listing, calendar queries, event creation | Official Google client for Node.js. Single package covers both Gmail and Calendar. TypeScript types included. |
| @notionhq/client | 5.9.x | Notion API SDK -- page creation, database queries, property updates | Official Notion SDK. v5 required for API version 2025-09-03 (data_source_id migration). |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @grammyjs/runner | latest | Concurrent update processing for grammY | If webhook throughput becomes a bottleneck (unlikely for single-user) |
| node-cron | 3.x | Already in project -- schedule email triage polling and calendar checks | Cron-based scheduling for periodic Gmail polling |
| yaml | 2.x | Already in project -- parse config files | Configuration management |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| grammY | Telegraf | Telegraf has larger ecosystem but weaker TypeScript types and lags behind Bot API versions. Only viable if existing Telegraf codebase. |
| grammY | node-telegram-bot-api (NTBA) | NTBA is simpler but has no TypeScript support and EventEmitter architecture does not scale beyond 50 lines. |
| googleapis (Gmail) | Cloud Pub/Sub push notifications | Push is faster but requires Google Cloud project with Pub/Sub infrastructure, topic/subscription management, 7-day renewal. Polling with `history.list` is simpler for single-user. |
| @notionhq/client | Notion MCP server | The official Notion MCP server (@notionhq/notion-mcp-server) exists but adds indirection. Direct SDK calls are simpler for page creation and database queries. |
| googleapis | @googleapis/calendar + @googleapis/gmail | Subpackages exist but the unified `googleapis` package is more convenient -- single OAuth2 client for both. |

**Installation:**
```bash
cd ~/.openclaw && npm install grammy googleapis @notionhq/client
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── telegram/
│   ├── bot.ts              # Bot instance, middleware, command registration
│   ├── commands.ts          # /start, /help, /status, /triage handlers
│   ├── callbacks.ts         # Inline keyboard callback query handlers
│   ├── formatters.ts        # MarkdownV2 message formatting utilities
│   └── types.ts             # Telegram-specific type definitions
├── gmail/
│   ├── client.ts            # Gmail API client with OAuth2
│   ├── triage.ts            # Email triage logic -- scan, classify, summarize
│   ├── poller.ts            # Periodic inbox polling with history tracking
│   └── types.ts             # Email-related types
├── calendar/
│   ├── client.ts            # Google Calendar API client (shares OAuth2 with Gmail)
│   ├── awareness.ts         # Meeting detection -- is user busy right now?
│   ├── extractor.ts         # Extract calendar events from email text
│   └── types.ts             # Calendar-related types
├── notion/
│   ├── client.ts            # Notion API client initialization
│   ├── action-log.ts        # Log agent actions to Notion database
│   └── types.ts             # Notion-related types
├── hitl/                    # [EXISTING] -- extend for Telegram approval
│   ├── classify.ts          # [EXISTING] -- no changes needed
│   ├── enforce.ts           # [MODIFY] -- add async approval path for YELLOW tier
│   ├── approval-queue.ts    # [NEW] -- pending approval storage + Telegram dispatch
│   └── types.ts             # [MODIFY] -- add ApprovalRequest, ApprovalStatus types
└── router/                  # [EXISTING] -- used by email triage for LLM classification
```

### Pattern 1: HITL Approval via Telegram (YELLOW Tier)

**What:** When a YELLOW-tier action is detected, instead of blocking outright (current behavior), queue it and send a Telegram message with approve/reject inline buttons. On callback, execute or discard the action.

**When to use:** Every YELLOW-tier action after Phase 3 is complete.

**Example:**
```typescript
// Source: grammY docs + existing enforce.ts pattern
import { InlineKeyboard } from 'grammy';
import type { ActionRequest, ApprovalRequest } from './types.js';

// In approval-queue.ts
export async function requestApproval(
  request: ActionRequest,
  bot: Bot
): Promise<string> {
  const approvalId = crypto.randomUUID();

  // Store pending approval
  await savePendingApproval({
    id: approvalId,
    request,
    status: 'pending',
    createdAt: new Date(),
  });

  // Build inline keyboard
  const keyboard = new InlineKeyboard()
    .text('Approve', `approve:${approvalId}`)
    .text('Reject', `reject:${approvalId}`);

  // Send to operator
  await bot.api.sendMessage(
    OPERATOR_CHAT_ID,
    formatApprovalMessage(request),
    { reply_markup: keyboard, parse_mode: 'MarkdownV2' }
  );

  return approvalId;
}

// In callbacks.ts -- handle the button press
bot.callbackQuery(/^(approve|reject):(.+)$/, async (ctx) => {
  const [, decision, approvalId] = ctx.match!;
  const approval = await getPendingApproval(approvalId);

  if (!approval || approval.status !== 'pending') {
    await ctx.answerCallbackQuery({ text: 'Already processed' });
    return;
  }

  if (decision === 'approve') {
    await executeAction(approval.request);
    await updateApprovalStatus(approvalId, 'approved');
    await ctx.editMessageText('Approved and executed.');
  } else {
    await updateApprovalStatus(approvalId, 'rejected');
    await ctx.editMessageText('Rejected and discarded.');
  }

  await ctx.answerCallbackQuery();
});
```

### Pattern 2: Email Triage with LLM Classification

**What:** Poll Gmail inbox periodically, classify emails using the model router, generate a triage summary, and send it to Telegram.

**When to use:** Daily email triage (COMM-01).

**Example:**
```typescript
// Source: googleapis docs + model router pattern
import { google } from 'googleapis';

async function triageInbox(auth: OAuth2Client): Promise<TriageResult[]> {
  const gmail = google.gmail({ version: 'v1', auth });

  // Get unread messages since last triage
  const response = await gmail.users.messages.list({
    userId: 'me',
    q: 'is:unread in:inbox after:' + lastTriageDate(),
    maxResults: 50,
  });

  const results: TriageResult[] = [];
  for (const msg of response.data.messages ?? []) {
    const full = await gmail.users.messages.get({
      userId: 'me',
      id: msg.id!,
      format: 'metadata',
      metadataHeaders: ['From', 'Subject', 'Date'],
    });

    const headers = full.data.payload?.headers ?? [];
    const from = headers.find(h => h.name === 'From')?.value ?? '';
    const subject = headers.find(h => h.name === 'Subject')?.value ?? '';

    // Use model router for classification
    const classification = await router.route({
      task: 'email-triage',
      prompt: `Classify this email. From: ${from}, Subject: ${subject}.
               Categories: actionable, informational, spam, calendar-event.
               Suggest one action: reply, archive, forward, add-calendar, ignore.`,
    });

    results.push({ messageId: msg.id!, from, subject, ...classification });
  }

  return results;
}
```

### Pattern 3: Calendar Event Extraction from Email

**What:** When the triage classifier identifies a "calendar-event" email, extract event details using LLM and propose adding it to Google Calendar via Telegram.

**When to use:** COMM-03 calendar event extraction.

**Example:**
```typescript
// Extract event details via LLM, then propose
async function proposeCalendarEvent(email: TriageResult): Promise<void> {
  const extraction = await router.route({
    task: 'calendar-extraction',
    prompt: `Extract calendar event from this email:
             From: ${email.from}
             Subject: ${email.subject}
             Body: ${email.snippet}
             Return JSON: { title, date, time, duration, location }`,
  });

  const keyboard = new InlineKeyboard()
    .text('Add to Calendar', `cal:add:${email.messageId}`)
    .text('Skip', `cal:skip:${email.messageId}`);

  await bot.api.sendMessage(OPERATOR_CHAT_ID,
    formatCalendarProposal(extraction),
    { reply_markup: keyboard, parse_mode: 'MarkdownV2' }
  );
}

// On approval, insert event
bot.callbackQuery(/^cal:add:(.+)$/, async (ctx) => {
  const messageId = ctx.match![1];
  const event = await getStoredExtraction(messageId);

  const calendar = google.calendar({ version: 'v3', auth });
  await calendar.events.insert({
    calendarId: 'primary',
    requestBody: {
      summary: event.title,
      start: { dateTime: event.startDateTime },
      end: { dateTime: event.endDateTime },
      location: event.location,
    },
  });

  await ctx.editMessageText('Event added to Google Calendar.');
  await ctx.answerCallbackQuery();
});
```

### Pattern 4: Notion Action Logging

**What:** Every agent action (email triage decision, HITL approval, calendar event added, etc.) is logged to a Notion database as a page.

**When to use:** COMM-08 centralized task logging.

**Example:**
```typescript
// Source: @notionhq/client v5 docs (API 2025-09-03)
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_API_KEY,
  notionVersion: '2025-09-03',
});

async function logAction(action: LogEntry): Promise<void> {
  await notion.pages.create({
    parent: {
      type: 'data_source_id',
      data_source_id: ACTION_LOG_DATA_SOURCE_ID
    },
    properties: {
      'Action': { title: [{ text: { content: action.description } }] },
      'Type': { select: { name: action.type } },
      'Status': { select: { name: action.status } },
      'Source': { rich_text: [{ text: { content: action.source } }] },
      'Timestamp': { date: { start: action.timestamp.toISOString() } },
    },
  });
}
```

### Anti-Patterns to Avoid

- **Storing Gmail OAuth tokens in plain text:** Tokens contain refresh credentials. Store in encrypted file or credential manager. Never commit to git.
- **Polling Gmail every minute:** Wasteful for single user. Every 5-15 minutes is sufficient. Use `historyId` to fetch only changes since last poll.
- **Blocking the Telegram bot loop for API calls:** All Gmail/Calendar/Notion API calls must be async. grammY handles this naturally with async middleware, but be careful with synchronous operations.
- **Sending raw LLM output to Telegram:** MarkdownV2 requires escaping special characters (`_*[]()~>#+\-=|{}.!`). Always format through a sanitizer before sending.
- **Using Cloud Pub/Sub for Gmail push:** Adds Google Cloud project dependency, topic/subscription management, and 7-day renewal cron. For a single user checking email a few times daily, `history.list` polling is simpler and sufficient.
- **Using Notion API v2022-06-28 or earlier:** The 2025-09-03 breaking change means `database_id` parents no longer work if a second data source is added. Use `data_source_id` from the start to avoid future breakage.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram bot framework | Custom HTTP webhook handler | grammY | Handles update types, middleware, session, keyboard builders, callback routing, error handling, retry logic |
| Gmail OAuth2 flow | Manual token exchange + refresh | googleapis OAuth2Client | Handles token refresh, expiry detection, retry on 401, scope management |
| MarkdownV2 escaping | Custom regex escaper | grammY's `fmt` helper or a dedicated function | Telegram MarkdownV2 has 18+ special characters that need escaping in specific contexts |
| Approval queue persistence | In-memory Map | SQLite table (better-sqlite3 already installed) | Approvals must survive process restarts; in-memory state is lost on crash |
| Email deduplication | Custom tracking | Gmail `historyId` | Gmail's history API already tracks what changed since your last check |
| Calendar busy detection | Parsing event lists | Google Calendar `freebusy.query` | Handles recurring events, all-day events, multi-calendar, timezone conversion |

**Key insight:** This phase integrates 4 external APIs (Telegram, Gmail, Google Calendar, Notion). Each has its own auth model, rate limits, and error patterns. Using official SDKs avoids reinventing error handling, pagination, and auth token management.

## Common Pitfalls

### Pitfall 1: Gmail OAuth2 Consent Screen Complexity
**What goes wrong:** Google requires OAuth consent screen configuration for Gmail scopes. `gmail.readonly` is a restricted scope requiring Google verification for apps with 100+ users.
**Why it happens:** Google treats email access as sensitive data.
**How to avoid:** For personal/internal use, set the OAuth consent screen to "Internal" (Google Workspace) or "External" with test users. Add your own Google account as a test user. No verification needed for fewer than 100 test users.
**Warning signs:** "Access blocked" error during OAuth flow; "App not verified" warning screen.

### Pitfall 2: Telegram MarkdownV2 Formatting Crashes
**What goes wrong:** Sending unescaped special characters in MarkdownV2 mode causes Telegram API to reject the message with "Bad Request: can't parse entities."
**Why it happens:** MarkdownV2 requires escaping: `_ * [ ] ( ) ~ > # + - = | { } . !` -- but only outside of code blocks and links. Email subjects and sender names often contain these characters.
**How to avoid:** Always pass message text through an escaping function before sending. Consider using HTML parse mode instead of MarkdownV2 (simpler escaping rules). Or use grammY's `fmt` tagged template.
**Warning signs:** Bot silently fails to send certain email triage summaries; intermittent "can't parse entities" errors in logs.

### Pitfall 3: Google OAuth2 Token Storage and Refresh
**What goes wrong:** OAuth2 tokens expire (access token: 1 hour, refresh token: 6 months of inactivity). If the refresh token is lost or the token file is corrupted, the entire OAuth flow must be redone interactively.
**Why it happens:** Token files stored insecurely or not persisted across container restarts.
**How to avoid:** Store tokens in a persistent, encrypted file at `~/.openclaw/config/google-tokens.json`. The googleapis `OAuth2Client` automatically refreshes access tokens if the refresh token is valid. Implement a "re-auth" command in Telegram for when refresh tokens expire.
**Warning signs:** Sudden 401 errors from Gmail/Calendar after months of working fine.

### Pitfall 4: Notion API 2025-09-03 Breaking Change
**What goes wrong:** Creating pages with `parent: { database_id: '...' }` works initially but breaks if the Notion database gets a second data source added (a normal Notion operation).
**Why it happens:** Notion API 2025-09-03 introduced `data_source_id` as the new parent reference type. Older API versions fail on multi-source databases.
**How to avoid:** Use @notionhq/client v5+ and always use `data_source_id` for page creation. Call `notion.databases.retrieve()` first to get the `data_sources` array, then use the first data source ID.
**Warning signs:** "database_id is not a valid parent type" errors; pages stop being created after Notion UI changes.

### Pitfall 5: Approval Queue Race Conditions
**What goes wrong:** Operator taps approve/reject button twice quickly, or the same approval is processed concurrently, leading to double execution.
**Why it happens:** Telegram can deliver duplicate callback queries. Network retries can cause duplicate processing.
**How to avoid:** Use SQLite transactions with `UPDATE ... WHERE status = 'pending'` to atomically claim an approval. Check affected row count -- if 0, the approval was already processed. Always call `ctx.answerCallbackQuery()` to dismiss the loading indicator.
**Warning signs:** Actions executed twice; "Already processed" messages appearing inconsistently.

### Pitfall 6: Gmail Rate Limits on Message Fetching
**What goes wrong:** Fetching full message bodies for 50+ emails sequentially hits Gmail's quota (250 quota units per user per second, each `messages.get` costs 5 units).
**Why it happens:** Naive implementation fetches each email individually in a loop.
**How to avoid:** Use `format: 'metadata'` with `metadataHeaders` for triage (only need From, Subject, Date). Batch requests using `gmail.users.messages.batchGet` when full body is needed. Rate-limit to 10 concurrent requests.
**Warning signs:** 429 "Rate Limit Exceeded" errors; email triage takes minutes instead of seconds.

## Code Examples

Verified patterns from official sources:

### grammY Bot Initialization with Polling
```typescript
// Source: grammy.dev/guide/getting-started
import { Bot } from 'grammy';

const bot = new Bot(process.env.TELEGRAM_BOT_TOKEN!);

// Restrict to allowed users
bot.use(async (ctx, next) => {
  const allowedUsers = [Number(process.env.TELEGRAM_OPERATOR_ID)];
  if (ctx.from && allowedUsers.includes(ctx.from.id)) {
    await next();
  } else {
    // Silently ignore unauthorized users
  }
});

bot.command('start', (ctx) => ctx.reply('OpenClaw agent ready.'));
bot.command('status', async (ctx) => {
  // Gather system status...
  await ctx.reply('All systems operational.');
});

// Start with long polling (development)
bot.start();
```

### Gmail OAuth2 Client Setup
```typescript
// Source: googleapis npm docs + Google OAuth2 quickstart
import { google } from 'googleapis';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const SCOPES = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/calendar.events',
  'https://www.googleapis.com/auth/calendar.readonly',
];

function createOAuth2Client() {
  const credentials = JSON.parse(
    readFileSync('~/.openclaw/config/google-credentials.json', 'utf-8')
  );
  const { client_id, client_secret, redirect_uris } = credentials.installed;

  const oauth2Client = new google.auth.OAuth2(
    client_id, client_secret, redirect_uris[0]
  );

  // Load saved tokens
  const tokenPath = '~/.openclaw/config/google-tokens.json';
  if (existsSync(tokenPath)) {
    const tokens = JSON.parse(readFileSync(tokenPath, 'utf-8'));
    oauth2Client.setCredentials(tokens);
  }

  // Auto-save refreshed tokens
  oauth2Client.on('tokens', (tokens) => {
    const existing = existsSync(tokenPath)
      ? JSON.parse(readFileSync(tokenPath, 'utf-8'))
      : {};
    writeFileSync(tokenPath, JSON.stringify({ ...existing, ...tokens }));
  });

  return oauth2Client;
}
```

### Google Calendar Busy Check
```typescript
// Source: Google Calendar API freebusy reference
async function isOperatorBusy(auth: OAuth2Client): Promise<boolean> {
  const calendar = google.calendar({ version: 'v3', auth });
  const now = new Date();
  const fiveMinLater = new Date(now.getTime() + 5 * 60 * 1000);

  const response = await calendar.freebusy.query({
    requestBody: {
      timeMin: now.toISOString(),
      timeMax: fiveMinLater.toISOString(),
      items: [{ id: 'primary' }],
    },
  });

  const busy = response.data.calendars?.primary?.busy ?? [];
  return busy.length > 0;
}
```

### Notion Page Creation (API v2025-09-03)
```typescript
// Source: @notionhq/client v5 docs, Notion API upgrade guide
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_API_KEY,
  notionVersion: '2025-09-03',
});

// One-time: get data_source_id from database
async function getDataSourceId(databaseId: string): Promise<string> {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  // @ts-expect-error -- v5 type may vary
  return db.data_sources[0].data_source_id;
}

// Create action log entry
async function createActionLog(
  dataSourceId: string,
  entry: { action: string; type: string; status: string; source: string }
): Promise<void> {
  await notion.pages.create({
    parent: { type: 'data_source_id', data_source_id: dataSourceId },
    properties: {
      'Action': { title: [{ text: { content: entry.action } }] },
      'Type': { select: { name: entry.type } },
      'Status': { select: { name: entry.status } },
      'Source': { rich_text: [{ text: { content: entry.source } }] },
      'Timestamp': { date: { start: new Date().toISOString() } },
    },
  });
}
```

### MarkdownV2 Escape Utility
```typescript
// Source: Telegram Bot API docs, MarkdownV2 specification
function escapeMarkdownV2(text: string): string {
  return text.replace(/([_*\[\]()~`>#+\-=|{}.!\\])/g, '\\$1');
}

function formatTriageSummary(results: TriageResult[]): string {
  const lines = results.map((r, i) => {
    const from = escapeMarkdownV2(r.from);
    const subject = escapeMarkdownV2(r.subject);
    const action = escapeMarkdownV2(r.suggestedAction);
    return `${i + 1}\\. *${from}*\n   ${subject}\n   _Action: ${action}_`;
  });

  return `*Email Triage Summary*\n\n${lines.join('\n\n')}`;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| node-telegram-bot-api (EventEmitter) | grammY (middleware, type-safe) | 2021+ | Better TypeScript, plugin ecosystem, active maintenance |
| Telegraf v3 (JavaScript) | grammY or Telegraf v4 (TypeScript) | 2022+ | Type safety, but Telegraf v4 types are complex |
| Notion API `database_id` parent | Notion API `data_source_id` parent | 2025-09-03 | Breaking: must use v5 SDK, `data_source_id` for all page creation |
| Gmail polling entire inbox | Gmail `history.list` with historyId tracking | Always available | Efficient: only fetches changes since last check |
| Gmail Cloud Pub/Sub push (complex) | Gmail polling for personal use (simple) | N/A | Google recommends polling for user-owned devices |
| Telegram polling for production | Telegram webhooks via Tailscale Funnel | 2023+ (Funnel GA) | Lower latency, no polling loop, but requires HTTPS |

**Deprecated/outdated:**
- Notion API versions before 2025-09-03: Will break if databases get multiple data sources. Use current version.
- node-telegram-bot-api: Last meaningful update years ago. Not recommended for new projects.
- `gmail.users.watch` without Pub/Sub infrastructure: Cannot do push without Cloud Pub/Sub topic/subscription. Not worth the complexity for personal use.

## Open Questions

1. **Gmail OAuth consent screen type**
   - What we know: "Internal" type requires Google Workspace. "External" works with test users (max 100, no verification needed).
   - What's unclear: Whether the operator's Google account is Workspace or personal Gmail.
   - Recommendation: Plan for "External" consent screen with test user. Add operator's email as test user during setup. This works for both Workspace and personal accounts.

2. **Notion database schema**
   - What we know: Need a centralized action log database. @notionhq/client v5 with data_source_id.
   - What's unclear: Whether the operator already has a Notion workspace and preferred database structure.
   - Recommendation: Create a dedicated "OpenClaw Action Log" database with standard properties (Action, Type, Status, Source, Timestamp). Provide a setup script that creates the database if it does not exist.

3. **Telegram bot delivery method for production**
   - What we know: Tailscale Funnel can expose HTTPS endpoints. n8n can relay webhooks. Long polling works but is slightly slower.
   - What's unclear: Whether Tailscale Funnel is already configured on the Mac Mini.
   - Recommendation: Start with long polling (zero infrastructure). Add webhook mode as optional upgrade. Both are supported by grammY with a config toggle.

4. **Email triage frequency and trigger**
   - What we know: Success criteria says "daily email triage summary." The operator may want it more frequently.
   - What's unclear: Preferred schedule -- morning only, or multiple times per day.
   - Recommendation: Default to once daily (8:00 AM) with configurable cron. The operator can also trigger on-demand via `/triage` Telegram command.

5. **Gmail credential routing through n8n proxy**
   - What we know: SECR-01 requires all external API calls to go through n8n proxy. The existing `proxy-email` stub exists.
   - What's unclear: Whether Gmail API OAuth2 (which requires ongoing token refresh) fits the n8n proxy pattern naturally, or should be an exception.
   - Recommendation: Gmail OAuth2 tokens are managed by the agent directly (not through n8n proxy) because: (a) the agent needs to call `history.list` frequently, (b) OAuth2 token refresh is tightly coupled to the googleapis client, (c) the n8n proxy is designed for simple API-key-based services. Document this as a deliberate exception to SECR-01 -- the Gmail tokens are still stored securely, just not proxied through n8n.

## Integration Points with Existing Code

### HITL System (Phase 1)

The existing `enforce.ts` returns `{ allowed: false, tier: 'YELLOW', reason: 'blocked (approval channel not yet available)' }` for YELLOW-tier actions. Phase 3 must:

1. **Extend `HITLResult` type** to include an optional `approvalId` field.
2. **Modify `enforceHITL`** to dispatch YELLOW-tier actions to the Telegram approval queue instead of blocking outright.
3. **Add an `approval-queue.ts` module** that stores pending approvals in SQLite (better-sqlite3 already installed) and dispatches Telegram messages.
4. **Wire callback handlers** in the Telegram bot to resolve pending approvals.
5. **RED tier remains always blocked** -- no approval path, ever. This is unchanged.

### Model Router (Phase 2)

The email triage classifier and calendar event extractor use the model router:

- **Email classification** (actionable/informational/spam/calendar-event): Route to Haiku tier (standard classification task).
- **Calendar event extraction** (title/date/time/duration): Route to Haiku tier (structured extraction).
- **Triage summary formatting**: Route to Ollama tier (simple formatting, free).

### Memory System (Phase 2)

- **Daily logs** should record email triage results, approval decisions, and calendar events added.
- **MEMORY.md** should store the operator's email triage preferences as they develop (e.g., "always archive newsletters").
- **historyId** for Gmail polling should be persisted in a dedicated config file, not in memory.

## Sources

### Primary (HIGH confidence)
- [grammY official docs](https://grammy.dev/) - Bot setup, inline keyboards, callback queries, plugins, TypeScript patterns
- [grammY framework comparison](https://grammy.dev/resources/comparison) - grammY vs Telegraf vs NTBA detailed comparison
- [Gmail API push notifications](https://developers.google.com/workspace/gmail/api/guides/push) - Cloud Pub/Sub setup, history.list, notification format
- [Notion API 2025-09-03 upgrade guide](https://developers.notion.com/docs/upgrade-guide-2025-09-03) - Breaking changes, data_source_id migration, SDK v5
- [Google Calendar freebusy API](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy) - Free/busy query endpoint
- [googleapis GitHub](https://github.com/googleapis/google-api-nodejs-client) - Official Node.js client, OAuth2 patterns

### Secondary (MEDIUM confidence)
- [npm trends: grammy vs telegraf vs NTBA](https://npmtrends.com/grammy-vs-node-telegram-bot-api-vs-telegraf-vs-telegram-bot-api) - Download statistics (grammy ~137K/week, telegraf ~138K/week, NTBA ~158K/week)
- [Tailscale Funnel docs](https://tailscale.com/kb/1223/funnel) - HTTPS exposure for webhook endpoints
- [Gmail OAuth2 scopes reference](https://developers.google.com/workspace/gmail/api/auth/scopes) - Scope permissions and restrictions
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) - v5.9.0 latest, 2025-09-03 API support

### Tertiary (LOW confidence)
- Gmail `history.list` vs Cloud Pub/Sub for personal use: Based on Google's own recommendation ("poll-based sync for user-owned devices") but specific performance characteristics for single-user are not benchmarked. Needs validation during implementation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - grammY, googleapis, @notionhq/client are all official/recommended libraries with active maintenance, verified via npm and official docs
- Architecture: HIGH - Patterns follow existing codebase conventions (TypeScript, better-sqlite3, model router), grammY inline keyboard approve/reject is a standard documented pattern
- Pitfalls: HIGH - Gmail OAuth2 complexity, Notion breaking change, MarkdownV2 escaping are well-documented issues with clear solutions
- Integration: HIGH - Existing HITL enforce.ts, model router, and memory system have clear extension points documented in Phase 1/2 summaries

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable libraries, Notion API version is fixed)

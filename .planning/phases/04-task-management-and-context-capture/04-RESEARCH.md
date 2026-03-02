# Phase 4: Task Management and Context Capture - Research

**Researched:** 2026-03-01
**Domain:** Notion todo database, Fellow API, Apple Notes access, BlueBubbles iMessage relay, proactive check-in engine with adaptive timing
**Confidence:** HIGH (core stack verified), MEDIUM (Fellow MCP, Apple Notes), LOW (BlueBubbles deprecation timeline)

## Summary

Phase 4 builds the operator's single source of truth for tasks by aggregating todo items from email triage (Phase 3), meeting transcripts (Fellow), call transcripts (Apple Notes), and iMessage context (BlueBubbles), all into a Notion todo database. The proactive check-in engine then surfaces this context 3-5 times daily via Telegram, adapting its timing based on operator engagement over a 14-day window.

The core architecture extends the existing Notion module (action-log pattern from Phase 3) to a richer todo database with priority, source, due date, assignee, and context properties. Fellow provides meeting transcripts via its MCP server (5 read-only tools including `get_meeting_transcript` and `get_action_items`), which avoids the REST API complexity. Apple Notes call transcripts are accessed via AppleScript/JXA on the Mac Mini. BlueBubbles provides iMessage read access via REST API on the Mac Mini, though the June 2026 Apple private API deprecation is a material risk. The check-in engine uses node-cron (already installed) for scheduling, SQLite for engagement tracking, and the model router (Haiku tier) for personalized message generation.

**Primary recommendation:** Use Fellow MCP for meeting transcripts (simplest integration path), AppleScript via child_process for Apple Notes (lightweight, no additional dependencies), BlueBubbles REST API for iMessage with a chat.db fallback plan, and node-cron + SQLite for the adaptive check-in engine. Extend the existing Notion module with a separate todo-list.ts alongside the action-log.ts.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TASK-01 | Centralized todo list in Notion populated automatically from email, meetings, iMessage, and screen observations | Notion API `pages.create` with todo database (extended properties: Priority, Source, Due Date, Assignee, Context). Existing @notionhq/client v5.11+ and `createNotionClient()` from Phase 3. Email todos come from the existing triage engine (03-02). |
| TASK-02 | Fellow meeting transcripts pulled and processed -- decisions, action items, open questions extracted | Fellow MCP server provides `get_meeting_transcript`, `get_action_items`, `search_meetings`. LLM extraction via Haiku tier for structured output (decisions, actions, questions). |
| TASK-03 | Apple Notes call transcripts pulled and processed with same extraction quality as Fellow | AppleScript access to Notes.app via `child_process.execFile('osascript', ...)`. JXA (JavaScript for Automation) for reading note content. Same LLM extraction pipeline as Fellow transcripts. |
| TASK-04 | 3-5 proactive check-ins per day via Telegram -- morning priorities, midday status, evening wrap-up | node-cron (already installed) schedules 5 daily slots. Context assembly pulls from Notion todos, calendar, memory, pending approvals, iMessage. Telegram bot (03-01) delivers messages. |
| TASK-05 | Check-in timing adapts over 14 days based on operator responses -- low-engagement slots dropped | SQLite table tracks check-in sent/responded/ignored per slot. After 14 days with 10+ data points, slots below 30% response rate are dropped. Min 2, max 5 per day. |
| TASK-06 | Check-in templates have anti-repetition logic -- track last 10, never repeat within 3 days | Template pool per time slot (4-6 templates each). SQLite tracks last 10 template IDs with timestamps. Selection filters out templates used in last 3 days. LLM personalizes selected template with current context. |
| COMM-05 | Agent reads iMessage conversations via BlueBubbles relay (read-only, business contacts only) | BlueBubbles REST API on Mac Mini: `GET /api/v1/message` with query filters. Authenticated via `password` query parameter. Webhook subscriptions for real-time new message events. Contact whitelist/blacklist filtering. |
| COMM-06 | iMessage context enriches todo items and check-in suggestions | iMessage poller extracts sender and topic summary (LLM Haiku tier), cross-references against CRM contacts, creates enriched todo items ("John from Acme texted about the invoice"). Privacy: metadata stored, content processed in memory only. |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @notionhq/client | 5.11.x | Notion API SDK -- todo database pages, queries, property updates | Already installed (Phase 3). Same client, new database. Handles data_source_id migration. |
| grammy | 1.41.x | Telegram bot -- check-in delivery, inline keyboards for quick responses | Already installed (Phase 3). Reuse bot instance for check-in messages. |
| node-cron | 3.x | Schedule check-in slots at fixed times | Already installed (Phase 3). Standard cron scheduling. |
| better-sqlite3 | 12.x | Engagement tracking, template history, check-in state | Already installed (Phase 1). Synchronous, zero-config, survives restarts. |
| googleapis | 171.x | Google Calendar freebusy check before check-ins | Already installed (Phase 3). Shared OAuth2 client. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Fellow MCP | Latest | Meeting transcript and action item retrieval | When Fellow workspace is connected. Provides 5 read-only tools. |
| httpx (or fetch) | Built-in | BlueBubbles REST API calls | For iMessage message polling and conversation queries. Node 22 native fetch is sufficient. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Fellow MCP | Fellow REST API (httpx + Bearer token) | REST API requires manual endpoint wiring, pagination, error handling. MCP server wraps all this. Use REST only if MCP is unavailable. |
| AppleScript for Apple Notes | apple-notes MCP server (community) | Community MCP (siddhant-k-code/apple-notes) adds a dependency on an unmaintained server. Direct AppleScript via child_process is simpler and has no external dependency. |
| BlueBubbles REST API | Direct chat.db relay (FastAPI on Mac Mini) | chat.db relay is already designed in the blueprint (07-Channel-Setup/imessage/) and avoids BlueBubbles dependency entirely. Requires Full Disk Access. Use as fallback if BlueBubbles is unavailable or deprecated. |
| node-cron | macOS LaunchAgent | LaunchAgent survives process restarts but requires plist management. node-cron keeps scheduling inside the TypeScript codebase. Since the bot process is already long-running, node-cron is simpler. |
| SQLite for engagement tracking | In-memory Map | In-memory state is lost on process restart. Engagement data must persist across 14+ days for adaptive timing to work. SQLite is the clear choice. |

**Installation:**
```bash
# No new packages needed -- all dependencies are already installed from Phases 1-3
# Fellow MCP configuration is done in Claude/Cursor settings, not npm
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── todo/
│   ├── aggregator.ts        # Central todo creation -- receives from all sources
│   ├── notion-todo.ts       # Notion todo database CRUD operations
│   ├── types.ts             # TodoItem, TodoSource, TodoPriority types
│   └── __tests__/
│       └── aggregator.test.ts
├── transcripts/
│   ├── fellow.ts            # Fellow MCP integration for meeting transcripts
│   ├── apple-notes.ts       # AppleScript-based Apple Notes reader
│   ├── extractor.ts         # LLM extraction: decisions, actions, questions
│   ├── types.ts             # TranscriptSource, ExtractedContent types
│   └── __tests__/
│       ├── extractor.test.ts
│       └── apple-notes.test.ts
├── imessage/
│   ├── client.ts            # BlueBubbles REST client (or chat.db relay)
│   ├── poller.ts            # Periodic iMessage polling with ROWID tracking
│   ├── context.ts           # Context extraction -- sender, topic summary
│   ├── types.ts             # iMessage types
│   └── __tests__/
│       └── poller.test.ts
├── checkin/
│   ├── engine.ts            # Check-in orchestrator -- schedule, context, send
│   ├── scheduler.ts         # node-cron schedule management
│   ├── context-assembler.ts # Parallel context fetching from all sources
│   ├── templates.ts         # Template pools per time slot
│   ├── adaptive.ts          # Engagement tracking and slot adaptation
│   ├── types.ts             # CheckinSlot, EngagementRecord types
│   └── __tests__/
│       ├── engine.test.ts
│       ├── adaptive.test.ts
│       └── templates.test.ts
├── telegram/                # [EXISTING] -- extend with check-in callbacks
├── notion/                  # [EXISTING] -- extend with todo-list module
├── gmail/                   # [EXISTING] -- triage results feed todo aggregator
├── calendar/                # [EXISTING] -- awareness.ts reused for check-in timing
└── router/                  # [EXISTING] -- LLM calls for extraction and check-in gen
```

### Pattern 1: Todo Aggregation from Multiple Sources

**What:** A central `aggregator.ts` receives todo items from all sources (email triage, Fellow, Apple Notes, iMessage) in a normalized format and writes them to the Notion todo database. Each source calls `aggregator.createTodo()` with source metadata.

**When to use:** Every time a new todo item is extracted from any source.

**Example:**
```typescript
// Source: Notion SDK docs + existing action-log pattern
import { createNotionClient, getDataSourceId } from '../notion/client.js';
import type { TodoItem } from './types.js';

export async function createTodo(item: TodoItem): Promise<void> {
  const notion = createNotionClient();
  const dataSourceId = await getDataSourceId(
    process.env.NOTION_TODO_DB_ID!,
    notion
  );

  await notion.pages.create({
    parent: {
      type: 'database_id' as any,
      database_id: dataSourceId,
    },
    properties: {
      'Task': { title: [{ text: { content: item.title } }] },
      'Priority': { select: { name: item.priority } },
      'Source': { select: { name: item.source } },
      'Status': { select: { name: 'open' } },
      'Due Date': item.dueDate
        ? { date: { start: item.dueDate.toISOString() } }
        : { date: null },
      'Context': {
        rich_text: [{ text: { content: item.context || '' } }],
      },
      'Source ID': {
        rich_text: [{ text: { content: item.sourceId || '' } }],
      },
    },
  });
}

// Types
export interface TodoItem {
  title: string;
  priority: 'high' | 'medium' | 'low';
  source: 'email' | 'fellow' | 'apple-notes' | 'imessage' | 'manual';
  dueDate?: Date;
  context?: string;           // e.g., "From meeting with Acme Corp"
  sourceId?: string;          // Dedup key: email messageId, Fellow note ID, etc.
}
```

### Pattern 2: Transcript Extraction via LLM

**What:** Both Fellow transcripts and Apple Notes call transcripts go through the same LLM extraction pipeline. The extractor sends the transcript text to Haiku tier and receives structured JSON with decisions, action items, and open questions.

**When to use:** After pulling any transcript from Fellow MCP or Apple Notes.

**Example:**
```typescript
// Source: existing model router pattern from Phase 2
import type { ExtractedContent } from './types.js';

const EXTRACTION_PROMPT = `Extract structured information from this meeting/call transcript.

Return JSON with:
{
  "decisions": [{"decision": "...", "context": "..."}],
  "action_items": [{"task": "...", "assignee": "...", "due": "..."}],
  "open_questions": [{"question": "...", "context": "..."}]
}

Rules:
- Extract ALL action items, even implicit ones ("I'll send that over")
- Assignee should be the person's name if mentioned, "operator" if the user
- Due dates should be ISO format if explicit, null if not mentioned
- Decisions are anything that was agreed upon or concluded
- Open questions are unresolved items needing follow-up

Transcript:
`;

export async function extractFromTranscript(
  text: string,
  source: string
): Promise<ExtractedContent> {
  const result = await router.routeAndCall({
    task: 'transcript-extraction',
    prompt: EXTRACTION_PROMPT + text,
    responseFormat: 'json',
  });

  const parsed = JSON.parse(
    result.content.replace(/^```(?:json)?\s*\n?/, '').replace(/\n?```\s*$/, '')
  );

  return {
    decisions: parsed.decisions || [],
    actionItems: parsed.action_items || [],
    openQuestions: parsed.open_questions || [],
    source,
    extractedAt: new Date(),
  };
}
```

### Pattern 3: Adaptive Check-in Scheduling

**What:** The check-in engine tracks which time slots get operator responses. Over a 14-day window, slots with <30% response rate are disabled. Engagement data persists in SQLite.

**When to use:** TASK-05 adaptive timing requirement.

**Example:**
```typescript
// Source: better-sqlite3 pattern from Phase 1
import Database from 'better-sqlite3';

const db = new Database(
  path.join(process.env.HOME!, '.openclaw/data/checkin.db')
);

// Schema
db.exec(`
  CREATE TABLE IF NOT EXISTS checkin_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    template_id TEXT NOT NULL,
    responded INTEGER DEFAULT 0,
    responded_at TEXT,
    response_latency_sec INTEGER
  );
  CREATE INDEX IF NOT EXISTS idx_checkin_slot ON checkin_history(slot);
  CREATE INDEX IF NOT EXISTS idx_checkin_sent ON checkin_history(sent_at);
`);

export function getSlotEngagement(
  slot: string,
  windowDays: number = 14
): { sent: number; responded: number; rate: number } {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - windowDays);

  const row = db.prepare(`
    SELECT
      COUNT(*) as sent,
      SUM(responded) as responded
    FROM checkin_history
    WHERE slot = ? AND sent_at > ?
  `).get(slot, cutoff.toISOString()) as any;

  const sent = row.sent || 0;
  const responded = row.responded || 0;
  return {
    sent,
    responded,
    rate: sent > 0 ? responded / sent : 0,
  };
}

export function getActiveSlots(
  minDataPoints: number = 10,
  dropThreshold: number = 0.30
): string[] {
  const allSlots = ['morning', 'late_morning', 'after_lunch', 'afternoon', 'evening'];
  const active: string[] = [];

  for (const slot of allSlots) {
    const engagement = getSlotEngagement(slot);
    // Keep slot if insufficient data or above threshold
    if (engagement.sent < minDataPoints || engagement.rate >= dropThreshold) {
      active.push(slot);
    }
  }

  // Enforce min 2, max 5
  if (active.length < 2) {
    return allSlots.slice(0, 2); // Keep morning + late_morning
  }
  return active.slice(0, 5);
}
```

### Pattern 4: Template Anti-Repetition

**What:** Track the last 10 templates used and prevent any template from being used again within 3 days. The LLM then personalizes the selected template with current context.

**When to use:** TASK-06 anti-repetition requirement.

**Example:**
```typescript
export function selectTemplate(slot: string): string {
  const pool = TEMPLATE_POOLS[slot];
  if (!pool || pool.length === 0) throw new Error(`No templates for slot: ${slot}`);

  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 3);

  // Get recently used template IDs
  const recentIds = db.prepare(`
    SELECT DISTINCT template_id FROM checkin_history
    WHERE sent_at > ?
    ORDER BY sent_at DESC
    LIMIT 10
  `).all(cutoff.toISOString())
    .map((r: any) => r.template_id);

  // Filter out recently used
  const available = pool.filter(t => !recentIds.includes(t.id));

  // If all used recently, pick the oldest-used one
  if (available.length === 0) {
    return pool[0].template; // Will be personalized by LLM anyway
  }

  // Random selection from available pool
  const selected = available[Math.floor(Math.random() * available.length)];
  return selected.template;
}
```

### Pattern 5: iMessage Context Extraction

**What:** Poll BlueBubbles for new messages, extract sender and topic summary via LLM, cross-reference against business contacts, and surface relevant context in check-ins and as todo items.

**When to use:** COMM-05 and COMM-06 iMessage integration.

**Example:**
```typescript
// BlueBubbles REST API client
const BB_URL = process.env.BLUEBUBBLES_URL || 'http://localhost:1234';
const BB_PASSWORD = process.env.BLUEBUBBLES_PASSWORD;

export async function getNewMessages(sinceDate: Date): Promise<BBMessage[]> {
  const response = await fetch(
    `${BB_URL}/api/v1/message?password=${BB_PASSWORD}&after=${sinceDate.getTime()}&limit=50`,
    { method: 'GET' }
  );
  const data = await response.json();
  return data.data || [];
}

// Context extraction (privacy-preserving)
export async function extractMessageContext(
  messages: BBMessage[],
  businessContacts: string[]
): Promise<MessageContext[]> {
  const relevant = messages.filter(
    m => !m.isFromMe && businessContacts.includes(m.handle?.address)
  );

  const contexts: MessageContext[] = [];
  for (const msg of relevant) {
    // Use LLM to extract topic -- do NOT persist message text
    const topic = await router.routeAndCall({
      task: 'imessage-context',
      prompt: `Summarize the topic of this message in 5-10 words.
               Do NOT include the full message text.
               Sender: ${msg.handle?.address}
               Message: ${msg.text}`,
    });

    contexts.push({
      sender: msg.handle?.address || 'unknown',
      topicSummary: topic.content,
      timestamp: new Date(msg.dateCreated),
      chatGuid: msg.chats?.[0]?.guid,
    });
  }

  return contexts;
}
```

### Anti-Patterns to Avoid

- **Storing iMessage content in any database:** Privacy requirement (COMM-05). Process in memory, surface metadata only. Never persist message text to Notion, SQLite, or any file.
- **Single Notion database for both action log and todos:** Keep them separate. Action log tracks what the agent DID; todo list tracks what NEEDS to be done. Different schemas, different query patterns.
- **Polling Fellow API on a timer:** Fellow has an MCP server -- use it for on-demand retrieval. For real-time awareness, configure Fellow webhooks via n8n (fires on "meeting recap created").
- **Running all context sources sequentially:** Context assembly for check-ins must be parallel with timeouts. A slow Fellow API call should not delay a calendar-aware check-in. Use `Promise.allSettled()` with 2-second timeout.
- **Sending raw LLM output in check-ins:** Always pass through the MarkdownV2 escaper from Phase 3 (`escapeMarkdownV2()`). LLM-generated text frequently contains special characters that break Telegram formatting.
- **Scheduling check-ins during quiet hours or meetings:** Always check `isOperatorBusy()` (Phase 3 calendar awareness) and quiet hours config before sending. Defer, don't drop.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Meeting transcript retrieval | Custom Fellow REST client with auth, pagination, error handling | Fellow MCP server (5 tools) | MCP handles auth, pagination, error handling. 5 lines of config vs 200+ lines of REST client code. |
| Apple Notes access | Custom SQLite reader for Notes database | AppleScript via `osascript` | Notes.app SQLite DB is undocumented, encrypted on newer macOS. AppleScript is the supported access path. |
| iMessage relay service | Custom FastAPI service polling chat.db | BlueBubbles REST API (or blueprint chat.db relay as fallback) | BlueBubbles handles message parsing, attributed body decoding, attachment handling, and provides webhooks. |
| Cron scheduling | Custom setTimeout chains | node-cron (already installed) | Handles timezone, day-of-week, missed executions gracefully. |
| Todo deduplication | Custom hash table | Source ID property in Notion + query before insert | Notion database query with `sourceId` filter prevents duplicate entries without maintaining local state. |
| Check-in engagement tracking | In-memory counters | SQLite table | Must survive restarts and accumulate over 14+ days. In-memory is guaranteed to lose data. |

**Key insight:** This phase is an integration phase, not a build-from-scratch phase. Every external data source (Fellow, Apple Notes, BlueBubbles) has an existing access mechanism. The value is in the aggregation pipeline and the adaptive check-in engine, not in building new API clients.

## Common Pitfalls

### Pitfall 1: Fellow MCP/API Workspace Admin Requirement
**What goes wrong:** Developer API is not enabled by default in Fellow. Attempting to use the MCP server or REST API fails with authentication errors.
**Why it happens:** Fellow requires a workspace admin to toggle "Allow users to create MCP connections" in Workspace Settings > Security before any user can generate API keys or connect MCP.
**How to avoid:** Before any Fellow integration work: verify admin access, enable Developer API in workspace settings, generate a personal API key, test with a simple `search_meetings` call.
**Warning signs:** 401/403 errors on all Fellow endpoints; MCP connection fails silently.

### Pitfall 2: Apple Notes Automation Permissions
**What goes wrong:** AppleScript commands to Notes.app fail with "Not authorized to send Apple events to Notes" error.
**Why it happens:** macOS requires explicit Automation permission in System Settings > Privacy & Security > Automation for the calling process (Terminal, Node.js, or the OpenClaw process) to control Notes.app.
**How to avoid:** During setup, trigger one manual AppleScript call from the OpenClaw process. macOS will prompt for permission. Grant it. Verify with a simple `osascript -e 'tell application "Notes" to count notes'` call.
**Warning signs:** AppleScript commands time out or return empty results without error.

### Pitfall 3: BlueBubbles Private API Deprecation Risk
**What goes wrong:** Apple terminates support for private iMessage APIs in June 2026, breaking BlueBubbles functionality.
**Why it happens:** BlueBubbles uses a helper bundle that injects into the iMessage process via private APIs. Apple has indicated these APIs will be restricted.
**How to avoid:** Plan A: BlueBubbles REST API. Plan B: Direct chat.db relay (already designed in the blueprint at `07-Channel-Setup/imessage/imessage-relay-architecture.md`). The chat.db approach reads SQLite directly and does not use private APIs -- it survives any API deprecation. Build the iMessage client abstraction layer so the backend can be swapped without changing the rest of the system.
**Warning signs:** BlueBubbles updates stop working after macOS update; "helper bundle not loaded" errors.

### Pitfall 4: Check-in Spam During Calendar Events
**What goes wrong:** Check-ins fire during meetings because the calendar check fails or times out, annoying the operator.
**Why it happens:** Google Calendar `freebusy.query` returns an error (token expired, network issue) and the check-in engine sends anyway.
**How to avoid:** If the calendar check fails, DEFER the check-in (do not send it). "When in doubt, stay quiet" is safer than "when in doubt, send it." Log the deferral. The operator would rather miss a check-in than be interrupted during a meeting.
**Warning signs:** Operator says "stop" or "too many" -- indicates check-ins are poorly timed.

### Pitfall 5: Notion Todo Duplication
**What goes wrong:** The same action item from a Fellow meeting appears as 3 separate Notion todo entries because the transcript was processed multiple times.
**Why it happens:** Fellow MCP returns the same transcript on repeated calls. Without deduplication, each call creates new todos.
**How to avoid:** Use a `sourceId` property in the Notion todo database. For Fellow items: `fellow:{note_id}:{action_item_index}`. For email: `email:{message_id}`. Before creating a todo, query Notion for existing entries with the same `sourceId`. Skip if found.
**Warning signs:** Duplicate entries in the Notion todo database; operator manually deletes duplicates.

### Pitfall 6: LLM Extraction Quality Inconsistency
**What goes wrong:** LLM extraction from transcripts produces different quality results depending on transcript length and format. Long transcripts (60+ minutes) get truncated; short ones produce sparse output.
**Why it happens:** Context window limits and varying transcript quality (Fellow produces clean structured text; Apple Notes may have OCR artifacts from Plaud).
**How to avoid:** For long transcripts (>8000 tokens), chunk into 15-minute segments and extract from each chunk separately, then merge. For Apple Notes transcripts, add a preprocessing step that cleans OCR artifacts before extraction. Always validate extraction output (must have at least one field populated).
**Warning signs:** Empty `action_items` arrays; nonsensical `decisions` text.

### Pitfall 7: Engagement Tracking Cold Start
**What goes wrong:** Adaptive timing drops slots too aggressively in the first 14 days because insufficient data makes rates unreliable.
**Why it happens:** With only 3-5 data points per slot, a single missed check-in pushes the rate below 30%.
**How to avoid:** Require a minimum of 10 data points before adapting. During the first 14 days, run all 5 slots regardless of response rates. Log a "learning phase" message to the operator on day 1.
**Warning signs:** Check-in frequency drops to 2/day within the first week.

## Code Examples

Verified patterns from official sources and existing codebase:

### Apple Notes Access via AppleScript

```typescript
// Source: macOS Automation docs + Node.js child_process
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

/**
 * Get recent notes from Apple Notes app.
 *
 * Requires: System Settings > Privacy & Security > Automation
 * permission for the calling process.
 */
export async function getRecentNotes(
  limit: number = 10
): Promise<AppleNote[]> {
  const script = `
    tell application "Notes"
      set noteList to {}
      set noteCount to count of notes
      set maxCount to ${limit}
      if noteCount < maxCount then set maxCount to noteCount
      repeat with i from 1 to maxCount
        set n to note i
        set noteInfo to {id of n, name of n, ¬
          modification date of n as string, ¬
          plaintext of n}
        set end of noteList to noteInfo
      end repeat
      return noteList
    end tell
  `;

  const { stdout } = await execFileAsync('osascript', ['-e', script], {
    timeout: 10000,
  });

  return parseAppleScriptOutput(stdout);
}

/**
 * Search Apple Notes by keyword.
 */
export async function searchNotes(keyword: string): Promise<AppleNote[]> {
  const script = `
    tell application "Notes"
      set matchingNotes to {}
      repeat with n in notes
        if plaintext of n contains "${keyword.replace(/"/g, '\\"')}" then
          set end of matchingNotes to {id of n, name of n, ¬
            modification date of n as string, ¬
            plaintext of n}
        end if
      end repeat
      return matchingNotes
    end tell
  `;

  const { stdout } = await execFileAsync('osascript', ['-e', script], {
    timeout: 30000,
  });

  return parseAppleScriptOutput(stdout);
}
```

### Check-in Context Assembly (Parallel with Timeout)

```typescript
// Source: existing calendar awareness pattern + blueprint context-sources.md
export async function assembleCheckinContext(
  slot: string
): Promise<CheckinContext> {
  const context: Partial<CheckinContext> = {};

  // Phase 1: Local sources (always available, fast)
  const [todos, history, memory] = await Promise.all([
    queryNotionTodos({ status: 'open', limit: 10 }),
    getCheckinHistory(slot),
    loadMemoryMd(),
  ]);

  context.pendingTodos = todos;
  context.checkinHistory = history;
  context.memory = memory;

  // Phase 2: Remote sources with 2s timeout
  const remoteResults = await Promise.allSettled([
    withTimeout(fetchCalendarEvents(), 2000),
    withTimeout(fetchPendingApprovals(), 2000),
    withTimeout(fetchRecentImessages(), 2000),
  ]);

  context.calendar = remoteResults[0].status === 'fulfilled'
    ? remoteResults[0].value : null;
  context.pendingApprovals = remoteResults[1].status === 'fulfilled'
    ? remoteResults[1].value : null;
  context.recentMessages = remoteResults[2].status === 'fulfilled'
    ? remoteResults[2].value : null;

  // Phase 3: Derive summary fields
  context.recentOpenings = getRecentOpenings(context.checkinHistory!);

  return context as CheckinContext;
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('timeout')), ms)
    ),
  ]);
}
```

### Notion Todo Database Schema

```typescript
// Source: @notionhq/client v5 docs
// Database properties for the todo list
const TODO_DB_SCHEMA = {
  'Task': { type: 'title' },
  'Priority': {
    type: 'select',
    options: [
      { name: 'high', color: 'red' },
      { name: 'medium', color: 'yellow' },
      { name: 'low', color: 'green' },
    ],
  },
  'Status': {
    type: 'select',
    options: [
      { name: 'open', color: 'blue' },
      { name: 'in-progress', color: 'yellow' },
      { name: 'done', color: 'green' },
      { name: 'cancelled', color: 'gray' },
    ],
  },
  'Source': {
    type: 'select',
    options: [
      { name: 'email', color: 'purple' },
      { name: 'fellow', color: 'blue' },
      { name: 'apple-notes', color: 'orange' },
      { name: 'imessage', color: 'green' },
      { name: 'manual', color: 'gray' },
      { name: 'check-in', color: 'pink' },
    ],
  },
  'Due Date': { type: 'date' },
  'Context': { type: 'rich_text' },
  'Source ID': { type: 'rich_text' },
};
```

### Fellow MCP Integration

```typescript
// Source: Fellow MCP server docs (help.fellow.ai)
// Fellow MCP provides 5 tools -- no custom client needed

// Usage via MCP tool calls:
// 1. search_meetings({ query: "acme", after: "2026-02-28" })
// 2. get_meeting_transcript({ meetingId: "abc123" })
// 3. get_action_items({ meetingId: "abc123" })
// 4. get_meeting_summary({ meetingId: "abc123" })
// 5. get_meeting_participants({ meetingId: "abc123" })

// Wrapper for programmatic use:
export async function processNewMeetings(): Promise<void> {
  // Search for meetings since last check
  const lastCheck = getLastFellowCheckTime();
  const meetings = await fellowMcp.searchMeetings({
    after: lastCheck.toISOString(),
  });

  for (const meeting of meetings) {
    // Get transcript
    const transcript = await fellowMcp.getMeetingTranscript({
      meetingId: meeting.id,
    });

    // Extract structured content
    const extracted = await extractFromTranscript(
      transcript.text,
      `fellow:${meeting.id}`
    );

    // Create todos for each action item
    for (const [i, item] of extracted.actionItems.entries()) {
      await createTodo({
        title: item.task,
        priority: item.due ? 'high' : 'medium',
        source: 'fellow',
        dueDate: item.due ? new Date(item.due) : undefined,
        context: `Meeting: ${meeting.title}. Assignee: ${item.assignee || 'operator'}`,
        sourceId: `fellow:${meeting.id}:action:${i}`,
      });
    }

    // Log decisions and open questions to Notion too
    for (const [i, decision] of extracted.decisions.entries()) {
      await createTodo({
        title: `Decision: ${decision.decision}`,
        priority: 'low',
        source: 'fellow',
        context: decision.context,
        sourceId: `fellow:${meeting.id}:decision:${i}`,
      });
    }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fellow REST API (manual) | Fellow MCP server (5 tools) | 2025+ | MCP eliminates custom REST client boilerplate; auth handled by MCP connection |
| Direct chat.db access | BlueBubbles REST API | 2022+ | Cleaner API, webhook support, no Full Disk Access needed; but depends on private API |
| LaunchAgent for scheduling | node-cron in-process | N/A | Both are valid; node-cron keeps logic in TypeScript; LaunchAgent survives process crashes |
| Template rotation via random seed | SQLite-tracked anti-repetition | N/A | Deterministic 3-day cooldown vs probabilistic rotation |
| Notion `database_id` parent | Notion `data_source_id` parent | 2025-09-03 | Must use @notionhq/client v5+ with data_source_id for page creation |

**Deprecated/outdated:**
- `macpymessenger` (AppleScript iMessage wrapper): Unmaintained, no REST API, blocking calls. Use BlueBubbles.
- `imsg-plus` CLI: No webhook delivery, not suitable for always-on agents.
- Notion API versions before 2025-09-03: Will break with multi-data-source databases.

## Open Questions

1. **Fellow workspace admin access**
   - What we know: Fellow API requires admin to enable "Developer API" in workspace security settings. The operator uses Fellow for meetings.
   - What's unclear: Whether the operator has admin access or needs to request it. Also unclear if Fellow MCP requires a paid workspace tier.
   - Recommendation: Verify admin access before planning. If Fellow API is unavailable, fall back to manual transcript paste via Telegram (operator sends transcript text, agent processes it). STATE.md already flags this as a concern.

2. **BlueBubbles vs direct chat.db relay**
   - What we know: BlueBubbles provides REST API + webhooks on macOS. The blueprint already has a complete chat.db relay design (07-Channel-Setup/imessage/). The June 2026 Apple deprecation is flagged in STATE.md.
   - What's unclear: Whether BlueBubbles is already installed on the Mac Mini. Whether the deprecation will actually happen or is delayed.
   - Recommendation: Build the iMessage client with an abstraction layer that supports both backends. Start with BlueBubbles if installed; implement chat.db relay as fallback. The abstraction costs 30 minutes of additional development but provides complete deprecation insurance.

3. **iMessage -- Mac Mini vs iMac location**
   - What we know: The blueprint architecture shows the iMessage relay running on the iMac (where Messages.app syncs), not the Mac Mini. However, BlueBubbles runs on the machine where Messages.app is active.
   - What's unclear: Whether Messages.app is active on the Mac Mini (agent machine) or only on the iMac (work machine). The agent machine IS the Mac Mini per CLAUDE.md.
   - Recommendation: If Messages.app runs on the Mac Mini, BlueBubbles can be installed directly -- no Tailscale relay needed. If only on the iMac, use the chat.db relay pattern over Tailscale (already designed). Confirm the Messages.app location before implementation.

4. **Check-in response tracking mechanism**
   - What we know: The engine needs to know if the operator responded to a check-in within 2 hours to track engagement.
   - What's unclear: How to correlate a Telegram text reply to the specific check-in that prompted it. grammY does not natively link a text message to a previous bot message.
   - Recommendation: Two approaches: (a) Use inline keyboard buttons on every check-in so responses are callbacks with known IDs, or (b) track by time window -- any operator message within 2 hours of a check-in counts as a response. Option (b) is simpler and good enough for engagement tracking.

5. **Notion todo database creation**
   - What we know: Phase 3 created the Action Log database manually via MCP. We need a second database for todos.
   - What's unclear: Whether the operator wants the todo database in the same Notion workspace/page, or a separate one.
   - Recommendation: Same workspace, separate database page. Create programmatically during setup (like the action log). Provide `NOTION_TODO_DB_ID` env var.

## Integration Points with Existing Code

### Telegram Bot (Phase 3, 03-01)
- **Check-in delivery:** Use `bot.api.sendMessage()` for check-in messages. Use `InlineKeyboard` for quick-response buttons.
- **Calendar-aware sending:** Use `sendMessage()` wrapper from 03-03 that checks `isOperatorBusy()` before sending.
- **Check-in callbacks:** Register new callback patterns `checkin:*` in `callbacks.ts` alongside existing `approve:*`, `reject:*`, `cal:*`.

### Email Triage Engine (Phase 3, 03-02)
- **Email-to-todo:** After email triage classifies an email as "actionable", extract the action item and call `aggregator.createTodo()` with source "email" and sourceId `email:{messageId}`.
- **Triage results in check-ins:** Context assembler queries recent triage results to include "5 emails triaged this morning" in check-in messages.

### Calendar Awareness (Phase 3, 03-03)
- **Check-in deferral:** Reuse `isOperatorBusy()` from `awareness.ts` before every check-in send.
- **Calendar context in check-ins:** Reuse `fetchCalendarEvents()` pattern for "You have 3 meetings today" context.

### Notion Action Log (Phase 3, 03-03)
- **Separate database:** Todo database is distinct from action log. Shared client via `createNotionClient()`.
- **Cross-logging:** When a todo is created from a transcript, also log the extraction action to the action log.

### Model Router (Phase 2, 02-02)
- **Transcript extraction:** Route to Haiku tier (structured extraction, moderate complexity).
- **Check-in generation:** Route to Haiku tier (short conversational text, low complexity).
- **iMessage topic summary:** Route to Ollama tier (simple 5-word summary, free).

### Memory System (Phase 2, 02-01)
- **Check-in history:** Could be stored in MEMORY.md but SQLite is better for 14-day engagement tracking (structured queries).
- **Context in check-ins:** Load MEMORY.md as part of context assembly for check-in personalization.

## Sources

### Primary (HIGH confidence)
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) - v5.11.0, TypeScript SDK, data_source_id support
- [Notion API docs](https://developers.notion.com/reference/post-page) - Page creation, database properties, property types
- [grammY docs](https://grammy.dev/) - Bot API, inline keyboards, callback queries
- [node-cron npm](https://www.npmjs.com/package/node-cron) - v3.x cron scheduling
- [better-sqlite3 npm](https://www.npmjs.com/package/better-sqlite3) - Synchronous SQLite for Node.js
- [macOS Automation AppleScript](https://www.macosxautomation.com/applescript/notes/index.html) - Notes.app AppleScript dictionary
- Phase 3 summaries (03-01, 03-02, 03-03) - Existing Telegram bot, Gmail triage, Notion action log, calendar awareness

### Secondary (MEDIUM confidence)
- [Fellow Developer API](https://developers.fellow.ai/reference/introduction) - REST endpoints for recordings, notes, action items, webhooks
- [Fellow MCP Server](https://help.fellow.ai/en/articles/12622641-fellow-s-mcp-server) - 5 read-only tools: search_meetings, get_meeting_transcript, get_action_items, get_meeting_summary, get_meeting_participants
- [Fellow API setup](https://help.fellow.ai/en/articles/11817206-developer-api) - Admin toggle, API key generation, 90-day audit trail
- [BlueBubbles REST API](https://docs.bluebubbles.app/server/developer-guides/rest-api-and-webhooks) - REST endpoints, webhook events, authentication via password query param
- [BlueBubbles Postman collection](https://documenter.getpostman.com/view/765844/UV5RnfwM) - Full endpoint reference
- Blueprint docs: `08-Capabilities-Deep-Dive/proactive-checkins/` - Check-in engine design, conversational design, context sources
- Blueprint docs: `07-Channel-Setup/imessage/` - iMessage relay architecture, chat.db schema, privacy considerations

### Tertiary (LOW confidence)
- BlueBubbles June 2026 Apple deprecation: Based on community reports and STATE.md flag. No official Apple announcement URL verified. Needs validation during implementation.
- Fellow MCP availability on paid-only workspaces: Not confirmed whether free tier supports MCP connections. Needs validation during setup.
- apple-notes MCP server (siddhant-k-code): Community project, not verified for current macOS. AppleScript direct access is preferred.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed from Phases 1-3. No new npm dependencies required. Notion, grammY, node-cron, better-sqlite3, googleapis all verified and working.
- Architecture: HIGH - Patterns extend existing codebase conventions (TypeScript, SQLite, model router, fire-and-forget Notion logging). Todo aggregation follows the action-log pattern.
- Fellow integration: MEDIUM - MCP server is documented and verified, but workspace admin access has not been confirmed. REST API fallback is well-documented.
- Apple Notes: MEDIUM - AppleScript access is a standard macOS pattern, but Automation permissions require manual setup and vary by macOS version.
- BlueBubbles/iMessage: MEDIUM - REST API is documented, but June 2026 deprecation risk creates uncertainty. Chat.db relay fallback is fully designed in the blueprint.
- Proactive check-ins: HIGH - Check-in engine design is well-documented in the blueprint with concrete templates, scheduling, and adaptation rules.
- Pitfalls: HIGH - Fellow admin requirement, AppleScript permissions, BlueBubbles deprecation, calendar check failures, todo deduplication are all well-understood risks with clear mitigations.

**Research date:** 2026-03-01
**Valid until:** 2026-03-31 (stable libraries, but monitor BlueBubbles deprecation news closely)

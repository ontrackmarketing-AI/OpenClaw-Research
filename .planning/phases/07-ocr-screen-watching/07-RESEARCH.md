# Phase 7: OCR Screen Watching - Research

**Researched:** 2026-03-02
**Domain:** Screen capture, OCR text extraction, vector-indexed storage, privacy filtering, cross-machine data sync
**Confidence:** MEDIUM-HIGH

## Summary

Phase 7 implements a continuous screen capture pipeline on the operator's Windows desktop that extracts text via OCR, syncs it to Supabase with pgvector embeddings, and exposes it to the OpenClaw agent on the Mac Mini. This enables recall queries ("what was I working on for [client]?"), enriches proactive check-ins with current work context, and supports pause/resume via Telegram commands.

The architecture spans two machines: a Python daemon on Windows handles capture, OCR, and local storage with a sync service pushing text to Supabase. The Mac Mini generates embeddings via Ollama (nomic-embed-text, already running from Phase 2) and queries Supabase for the agent. The blueprint docs in `08-Capabilities-Deep-Dive/screen-database/` provide a complete reference implementation covering capture, sync, storage, query, and privacy. Phase 7 realizes these blueprints.

**Primary recommendation:** Build a custom Python capture daemon using mss + Tesseract + SQLite on Windows, syncing OCR text to Supabase via the REST API. Generate embeddings on the Mac Mini using Ollama. Expose a `screen_recall` tool and integrate screen context into the existing check-in context assembler.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OCRW-01 | Windows Python daemon captures screen every 30 seconds via mss, OCR processes via Tesseract | Standard stack (mss, pytesseract, SQLite), capture pipeline architecture, Windows service deployment patterns |
| OCRW-02 | Captured text stored in Supabase with pgvector embeddings for semantic search | Supabase schema design, pgvector indexing, hybrid search RPC function, embedding pipeline via Ollama |
| OCRW-03 | Sensitive content classifier filters out password managers, banking, and personal apps before any capture reaches agent | Privacy overlay pattern (excluded apps list, title patterns, incognito detection), configurable YAML exclusions |
| OCRW-04 | Agent can answer "what was I working on for [client]?" by querying screen history | screen_recall tool definition, hybrid search (vector + FTS), query interface patterns, context truncation |
| OCRW-05 | Screen context enriches proactive check-ins -- agent knows current work context when sending messages | Check-in context assembler integration point identified (context-assembler.ts), dynamic import pattern already established by iMessage module |
</phase_requirements>

## Standard Stack

### Core (Windows Daemon)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mss | 10.x | Cross-platform screenshot capture via DMA | Pure Python, no dependencies, 10-30ms per capture, handles multi-monitor natively |
| pytesseract | 0.3.13+ | Python wrapper for Tesseract OCR engine | Mature wrapper, used by blueprint; Tesseract 5.x LSTM engine is standard for screen text |
| Tesseract OCR | 5.x | OCR engine (installed separately via winget) | Open source, free, 95-98% accuracy on clean screen text, UB-Mannheim Windows builds |
| Pillow (PIL) | 11.x | Image conversion (mss BGRA -> RGB for Tesseract) | Standard image library, required by pytesseract |
| pygetwindow | 0.0.9+ | Active window title and app name detection | Simple, Windows-native, sufficient for title extraction |
| pystray | 0.19.5+ | System tray icon for pause/resume/status | Standard system tray library, threading-compatible, supports Windows/macOS/Linux |
| httpx | 0.28.x | Async HTTP client for Supabase REST API sync | Modern async HTTP client, connection pooling, retry support |
| better-sqlite3 (Python: sqlite3) | stdlib | Local capture database with FTS5 | Built-in Python stdlib; FTS5 for local keyword search; offline resilience |

### Core (Mac Mini - Agent Side, TypeScript)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @supabase/supabase-js | 2.x | Supabase client for querying screen_captures table and calling RPC functions | Official client, TypeScript-native, handles auth/REST/realtime |
| ollama (existing) | already installed | Embedding generation via nomic-embed-text (768-dim) | Already running on Mac Mini from Phase 2; $0 cost per embedding |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PyWinCtl | 0.4+ | Cross-platform window management (alternative to pygetwindow) | If pygetwindow has issues; more actively maintained, more features |
| Pillow image preprocessing | via Pillow | Grayscale conversion, basic sharpening for OCR accuracy | Only if OCR accuracy on screen text needs improvement |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tesseract | PaddleOCR | Better accuracy on complex layouts, but heavier install (PyTorch/PaddlePaddle), GPU preferred, overkill for screen text |
| Tesseract | EasyOCR | Better on multi-language, but slower without GPU, heavier dependencies |
| Tesseract | Windows Native OCR API | Faster and more accurate, but requires NPU hardware (Copilot+ PC) for new API; legacy `Windows.Media.Ocr.OcrEngine` is an option but harder to access from Python |
| Custom daemon | ScreenPipe | Full-featured (MCP server, audio capture, better OCR), but Windows stability issues (DB lock errors, UI freezes), $400 lifetime or build from source |
| Supabase | Direct Qdrant push | Avoid new service, but Qdrant is already used for memory/task-RAG (different concern); Supabase provides SQL + pgvector + REST API + retention management in one service |
| httpx (Python sync) | supabase-py | Official Supabase Python client, but httpx gives more control over batch inserts, retry logic, and sync patterns |

**Installation (Windows):**
```powershell
# Install Tesseract OCR
winget install UB-Mannheim.TesseractOCR

# Install Python dependencies
pip install mss pytesseract Pillow pygetwindow pystray httpx pyyaml
```

**Installation (Mac Mini - package.json addition):**
```bash
npm install @supabase/supabase-js
```

## Architecture Patterns

### Recommended Project Structure

```
# Windows machine: ~/openclaw-capture/
openclaw-capture/
├── capture/
│   ├── daemon.py          # Main capture loop (mss + pygetwindow + tesseract)
│   ├── privacy.py         # Exclusion filters (apps, titles, incognito)
│   └── dedup.py           # Content hash deduplication
├── sync/
│   ├── supabase_sync.py   # Batch sync unsynced captures to Supabase REST API
│   └── offline_queue.py   # Offline handling (synced=0 accumulates, catches up)
├── tray/
│   └── tray_app.py        # System tray icon (pause/resume/delete/status)
├── config/
│   └── screen_capture.yaml  # Exclusion lists, intervals, Supabase creds
├── main.py                # Entry point: starts capture + sync + tray threads
└── requirements.txt

# Mac Mini: ~/.openclaw/src/screen/ (new module)
src/screen/
├── embed-worker.ts        # Background job: fetch unembedded captures, generate embeddings via Ollama, update Supabase
├── query.ts               # screen_recall tool implementation (hybrid search via Supabase RPC)
├── checkin-context.ts     # Screen context source for check-in assembler
├── telegram-commands.ts   # /screen pause|resume|delete|status Telegram handlers
├── types.ts               # Shared types (ScreenCapture, SearchResult)
└── __tests__/
    ├── query.test.ts
    └── embed-worker.test.ts
```

### Pattern 1: Capture-Sync-Embed Pipeline (Three-Stage Async)

**What:** The pipeline is split into three independent stages that run asynchronously: (1) capture on Windows stores to local SQLite, (2) sync service pushes unsynced rows to Supabase, (3) embed worker on Mac Mini generates embeddings for unembedded rows.

**When to use:** Always -- this is the core architecture.

**Why:** Each stage is independently resilient. If Supabase is down, captures continue locally. If Ollama is busy, text is still searchable via FTS. No single failure blocks the pipeline.

```
Windows:                          Cloud:              Mac Mini:
[mss capture] -> [SQLite]  --->  [Supabase]  <---  [Embed Worker]
  30s interval    (local)    60s   (pgvector)         (Ollama)
                  synced=0 -> synced=1         embedding IS NULL -> embedding SET
```

### Pattern 2: Privacy-First Capture (Filter Before Store)

**What:** The privacy filter runs BEFORE the screenshot is captured or OCR is performed. If the active window matches an excluded app or title pattern, the entire capture cycle is skipped -- no screenshot taken, no image saved, no OCR text generated.

**When to use:** Every capture cycle.

**Why:** Filtering after capture creates a window where sensitive data exists in memory. Filtering before capture means sensitive content never enters the pipeline at any stage.

```python
# Privacy check FIRST, before mss.grab()
window_title, app_name = get_active_window()
if should_skip(app_name, window_title):
    time.sleep(CAPTURE_INTERVAL)
    continue  # No screenshot, no OCR, no storage
# Only now: capture, OCR, store
```

### Pattern 3: Telegram Command Relay (Mac-to-Windows Control)

**What:** The /screen Telegram commands (pause, resume, delete, status) are received by the Telegram bot on the Mac Mini, which then relays the command to the Windows daemon. The relay mechanism uses a Supabase table (`screen_commands`) as a command queue that the Windows daemon polls.

**When to use:** For all pause/resume/delete/status commands.

**Why:** The Mac Mini runs the Telegram bot (Phase 3). The Windows daemon cannot run a Telegram bot independently. A command queue in Supabase provides reliable, asynchronous communication without requiring a direct TCP connection from Mac to Windows.

```
Operator -> Telegram -> Mac Mini Bot -> Supabase screen_commands table
                                            |
Windows Daemon (polls every 10s) <---------+
```

**Alternative:** Direct HTTP call from Mac Mini to Windows via Tailscale. Simpler but requires the Windows daemon to expose an HTTP endpoint and be discoverable. The Supabase queue is more resilient to connectivity gaps.

### Pattern 4: Dynamic Import for Screen Context (Existing Pattern)

**What:** The check-in context assembler already uses dynamic imports for optional modules (iMessage in 04-02). Screen context follows the same pattern.

**When to use:** When integrating screen context into check-in engine.

```typescript
// In context-assembler.ts -- same pattern as fetchRecentImessages()
async function fetchRecentScreenActivity(): Promise<ScreenContextSummary | null> {
  try {
    const screenModule = await import('../screen/checkin-context.js').catch(() => null);
    if (!screenModule || !screenModule.getRecentScreenContext) {
      log('INFO', 'screen_module_not_available', {
        reason: '07 not yet complete or module missing',
      });
      return null;
    }
    return screenModule.getRecentScreenContext(120); // last 2 hours
  } catch (err) {
    log('WARN', 'screen_context_fetch_failed', {
      error: err instanceof Error ? err.message : String(err),
    });
    return null;
  }
}
```

### Anti-Patterns to Avoid

- **Storing screenshots in Supabase:** Images are 100-150 MB/day. Only store OCR text + metadata remotely. Images stay on Windows (30-day retention) for manual review if needed.
- **Generating embeddings on Windows:** Ollama runs on Mac Mini. Do not install a separate embedding model on Windows -- it wastes resources and complicates the architecture.
- **Blocking on sync failure:** The capture loop must never block or crash if Supabase is unreachable. Local SQLite is the source of truth. Sync catches up when connectivity resumes.
- **OCR on every pixel change:** Use content hash deduplication. If the screen text hasn't changed, skip the capture. This reduces storage by 40-60%.
- **Running Tesseract on full resolution:** For 4K monitors, downscale to 1920px width before OCR. Tesseract accuracy on screen text barely changes, but processing time drops significantly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Screenshot capture | Custom Win32 API calls | mss library | mss handles DMA, multi-monitor, BGRA format natively in pure Python |
| OCR text extraction | Custom ML model or cloud API | Tesseract 5.x via pytesseract | Screen text is clean rendered text -- Tesseract's sweet spot. No need for PaddleOCR/cloud APIs |
| System tray icon | Custom Win32 tray code | pystray | Handles icon, menu, threading, click events on Windows/macOS/Linux |
| Vector similarity search | Custom cosine similarity in code | Supabase pgvector + RPC function | pgvector handles indexing (IVFFlat), similarity calculation, and filtering in SQL |
| Hybrid search (vector + FTS) | Custom RRF merger | Supabase SQL function with combined_score | Single query returns weighted hybrid results; no application-level merging |
| Command relay (Mac to Windows) | Custom WebSocket or TCP server | Supabase table as command queue | Both machines already connect to Supabase; no new network path needed |

**Key insight:** The heaviest engineering in this phase is NOT the capture pipeline (blueprint provides a working implementation). It's the integration points: Telegram commands, check-in context, Supabase schema/RPC, and the embed worker. Reuse existing patterns and don't build infrastructure that Supabase already provides.

## Common Pitfalls

### Pitfall 1: Supabase Project Still Paused
**What goes wrong:** The Supabase project (ID: jitawzicdwgbhatvjblh) is currently paused per STATE.md. The free tier pauses after 7 days of inactivity.
**Why it happens:** The project was never actively used after initial creation.
**How to avoid:** Reactivate BEFORE Phase 7 planning. Verify the project is restorable (90-day window from pause date). If free tier is insufficient (500 MB covers only 1-4 months of OCR data), upgrade to Pro ($25/month, 8 GB). Pro tier projects never auto-pause.
**Warning signs:** `supabase` integration shows `"status": "disabled"` in integrations.json. Environment variables SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are empty in .env.template.

### Pitfall 2: Tesseract OCR Accuracy on UI Elements
**What goes wrong:** Tesseract struggles with certain UI elements: small font sizes, colored text on colored backgrounds, icons with text, progress bars with percentages.
**Why it happens:** Tesseract's LSTM engine is optimized for document text (black on white). Screen UIs have varied fonts, sizes, colors, and layouts.
**How to avoid:** Preprocess screenshots: convert to grayscale, increase contrast, optionally downscale from 4K to 1920px width. Accept that OCR accuracy on screen text will be ~90-95% rather than document-level ~97%. This is sufficient for context and search.
**Warning signs:** OCR text contains lots of garbled characters or missed text blocks. Test with actual screenshots from the operator's workflow.

### Pitfall 3: Storage Growth Exceeds Supabase Plan
**What goes wrong:** With 30-second intervals over 8 hours, ~500-700 captures/day (after dedup) generates ~4-12 MB/day of OCR text + embeddings. Over 90 days, this reaches 360-1080 MB -- exceeding the free tier's 500 MB.
**Why it happens:** Embeddings (768-dim float32 = ~3 KB each) add up. OCR text from content-heavy screens can be 5+ KB per capture.
**How to avoid:** Use Pro tier ($25/month, 8 GB). Implement 90-day retention policy with daily cleanup cron. Generate daily summaries before purging raw captures. Monitor storage via Supabase dashboard.
**Warning signs:** Supabase storage usage approaching tier limit. Slow query performance as table grows past 500K rows without proper indexing.

### Pitfall 4: Windows Daemon Dies Silently
**What goes wrong:** The Python capture daemon crashes (unhandled exception, Tesseract timeout, out of memory) and nobody notices because it runs headless.
**Why it happens:** Long-running Python processes need robust error handling. Tesseract can hang on certain image inputs. System tray apps can fail on Windows sleep/wake.
**How to avoid:** Use NSSM (Non-Sucking Service Manager) to run as a Windows service with auto-restart. Add heartbeat: daemon writes a timestamp to a status file every capture cycle. Mac Mini can check for stale heartbeats and alert via Telegram. Catch ALL exceptions in the capture loop with continue (never let the loop break).
**Warning signs:** Gap in capture timestamps. sync_count not incrementing. System tray icon disappears.

### Pitfall 5: Embedding Pipeline Bottleneck
**What goes wrong:** The embed worker on Mac Mini falls behind because Ollama nomic-embed-text takes ~50ms per embedding, and there are 500+ unembedded captures from a full workday.
**Why it happens:** If the embed worker runs infrequently or on a small batch size, a backlog accumulates.
**How to avoid:** Run the embed worker as a recurring cron job every 5 minutes with a batch size of 100. At 50ms each, 100 embeddings take ~5 seconds -- well within the 5-minute window. Monitor unembedded row count.
**Warning signs:** Growing count of rows where `embedding IS NULL` in Supabase.

### Pitfall 6: Privacy Filter Bypass via Window Title Changes
**What goes wrong:** The privacy filter checks the active window title at capture time, but the user could switch apps between the title check and the screenshot (race condition).
**Why it happens:** The window check and screenshot are separate calls (~10-30ms apart). User can switch windows in that gap.
**How to avoid:** Check the active window TWICE: once before capture, once after OCR but before storage. If the post-capture check shows a sensitive app, discard the capture. Also scan the OCR text itself for sensitive patterns (credit card numbers, SSNs) as a secondary filter.
**Warning signs:** OCR text contains "1Password" or "Chase" even though those apps are in the exclusion list.

## Code Examples

### Supabase Schema (Verified from Blueprint)

```sql
-- Source: 08-Capabilities-Deep-Dive/screen-database/storage-indexing.md
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE screen_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    captured_at TIMESTAMPTZ NOT NULL,
    source_device TEXT NOT NULL DEFAULT 'windows_desktop',
    monitor_index INTEGER DEFAULT 0,
    window_title TEXT,
    app_name TEXT,
    ocr_text TEXT NOT NULL,
    content_hash TEXT,
    embedding vector(768),
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Command queue for Telegram -> Windows relay
CREATE TABLE screen_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command TEXT NOT NULL,       -- 'pause', 'resume', 'delete_last_30m', 'delete_today', 'status'
    args JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',  -- 'pending', 'executed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_screen_captures_time ON screen_captures(captured_at DESC);
CREATE INDEX idx_screen_captures_app ON screen_captures(app_name);
CREATE INDEX idx_screen_captures_hash ON screen_captures(content_hash);
CREATE INDEX idx_screen_captures_unembedded
    ON screen_captures(captured_at ASC)
    WHERE embedding IS NULL;

-- Vector index (IVFFlat, 50 lists for expected <1M rows)
CREATE INDEX idx_screen_captures_embedding
    ON screen_captures USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- Full-text search
CREATE INDEX idx_screen_captures_text
    ON screen_captures USING GIN (to_tsvector('english', ocr_text));

-- RLS: only service role can access
ALTER TABLE screen_captures ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON screen_captures FOR ALL USING (false);

ALTER TABLE screen_commands ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON screen_commands FOR ALL USING (false);
```

### Hybrid Search RPC Function (Verified from Blueprint)

```sql
-- Source: 08-Capabilities-Deep-Dive/screen-database/storage-indexing.md
CREATE OR REPLACE FUNCTION search_screen_captures(
    query_text TEXT,
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    time_start TIMESTAMPTZ DEFAULT NULL,
    time_end TIMESTAMPTZ DEFAULT NULL,
    filter_app TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    captured_at TIMESTAMPTZ,
    window_title TEXT,
    app_name TEXT,
    ocr_text TEXT,
    vector_similarity FLOAT,
    text_rank FLOAT,
    combined_score FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.id,
        sc.captured_at,
        sc.window_title,
        sc.app_name,
        sc.ocr_text,
        1 - (sc.embedding <=> query_embedding) AS vector_similarity,
        ts_rank(to_tsvector('english', sc.ocr_text),
                plainto_tsquery('english', query_text)) AS text_rank,
        (0.6 * (1 - (sc.embedding <=> query_embedding)) +
         0.4 * ts_rank(to_tsvector('english', sc.ocr_text),
                       plainto_tsquery('english', query_text))) AS combined_score
    FROM screen_captures sc
    WHERE
        (1 - (sc.embedding <=> query_embedding)) > match_threshold
        AND (time_start IS NULL OR sc.captured_at >= time_start)
        AND (time_end IS NULL OR sc.captured_at <= time_end)
        AND (filter_app IS NULL OR sc.app_name ILIKE '%' || filter_app || '%')
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;
```

### Embedding Worker (TypeScript, Mac Mini Side)

```typescript
// Source: Architecture pattern derived from 08-Capabilities-Deep-Dive/screen-database/data-pipeline.md
// embed-worker.ts -- runs as cron on Mac Mini every 5 minutes

import { createClient } from '@supabase/supabase-js';

const BATCH_SIZE = 100;

interface UnembeddedCapture {
  id: string;
  app_name: string;
  window_title: string;
  ocr_text: string;
}

export async function embedUnembeddedCaptures(
  supabase: ReturnType<typeof createClient>
): Promise<number> {
  // Fetch captures missing embeddings
  const { data: captures, error } = await supabase
    .from('screen_captures')
    .select('id, app_name, window_title, ocr_text')
    .is('embedding', null)
    .order('captured_at', { ascending: true })
    .limit(BATCH_SIZE);

  if (error || !captures?.length) return 0;

  for (const capture of captures) {
    const text = `${capture.app_name}: ${capture.window_title}\n${capture.ocr_text}`;

    // Generate embedding via Ollama (already running on Mac Mini)
    const resp = await fetch('http://localhost:11434/api/embed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'nomic-embed-text', input: text }),
    });
    const result = await resp.json();
    const embedding = result.embeddings[0];

    // Update Supabase with embedding
    await supabase
      .from('screen_captures')
      .update({ embedding })
      .eq('id', capture.id);
  }

  return captures.length;
}
```

### Telegram /screen Command Handler

```typescript
// Source: Pattern derived from existing commands.ts structure
// telegram-commands.ts (screen module)

import type { Bot } from 'grammy';
import { createClient } from '@supabase/supabase-js';
import { escapeMarkdownV2 } from '../telegram/formatters.js';

export function registerScreenCommands(bot: Bot): void {
  bot.command('screen', async (ctx) => {
    const msgText = ctx.message?.text || '';
    const args = msgText.replace(/^\/screen\s*/, '').trim();
    const subcommand = args.split(/\s+/)[0]?.toLowerCase() || 'status';

    const supabase = createClient(
      process.env.SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );

    switch (subcommand) {
      case 'pause':
      case 'resume':
        await supabase.from('screen_commands').insert({
          command: subcommand,
          status: 'pending',
        });
        await ctx.reply(
          escapeMarkdownV2(`Screen capture ${subcommand} command sent.`),
          { parse_mode: 'MarkdownV2' }
        );
        break;

      case 'delete': {
        const timeArg = args.replace('delete', '').trim(); // "30m", "today"
        await supabase.from('screen_commands').insert({
          command: `delete_${timeArg.replace(/\s+/g, '_')}`,
          status: 'pending',
        });
        await ctx.reply(
          escapeMarkdownV2(`Delete command queued: ${timeArg}`),
          { parse_mode: 'MarkdownV2' }
        );
        break;
      }

      case 'status':
      default: {
        const { count } = await supabase
          .from('screen_captures')
          .select('*', { count: 'exact', head: true });
        const { data: pending } = await supabase
          .from('screen_commands')
          .select('command')
          .eq('status', 'pending');

        await ctx.reply(
          escapeMarkdownV2(
            `Screen captures: ${count ?? 0} total\n` +
            `Pending commands: ${pending?.length ?? 0}`
          ),
          { parse_mode: 'MarkdownV2' }
        );
        break;
      }
    }
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Windows Recall (NPU-only) | Custom daemon or ScreenPipe | 2024-2025 | Windows Recall requires Copilot+ PC hardware; not available on standard desktops |
| Rewind (screen recording + search) | Discontinued (Meta acquired Limitless Dec 2025) | Dec 2025 | No longer viable; screen capture disabled Dec 19, 2025 |
| ScreenPipe (MCP server) | Active development, v0.3.x, $2.8M funding Jul 2025 | 2025-2026 | Most feature-rich option but Windows stability concerns remain; worth revisiting in 3-6 months |
| IVFFlat vector indexing | HNSW available in pgvector 0.5+ | 2024 | HNSW provides better recall at slightly higher memory; IVFFlat is fine for <1M rows |
| pytesseract only | PaddleOCR / EasyOCR alternatives | 2024-2025 | PaddleOCR offers better accuracy on complex layouts; Tesseract still optimal for clean screen text |

**Deprecated/outdated:**
- **Rewind/Limitless**: Acquired by Meta, screen capture discontinued Dec 2025. Not viable.
- **Windows.Media.Ocr legacy API**: Still works but harder to access from Python. The newer WinAI Text Recognition API requires NPU hardware.
- **Supabase vecs Python client**: Still maintained but supabase-py or direct REST API is simpler for batch inserts.

## Open Questions

1. **Supabase Project Recovery**
   - What we know: Project jitawzicdwgbhatvjblh is paused. Free tier pauses after 7 days of inactivity. Projects are restorable within 90 days.
   - What's unclear: How long it has been paused. Whether it's still within the 90-day restore window. Whether to restore on free tier or upgrade to Pro.
   - Recommendation: Attempt restore BEFORE planning. If restore fails, create a new project. Budget for Pro tier ($25/month) since free tier (500 MB) is marginal for 90 days of captures.

2. **IVFFlat vs HNSW Indexing**
   - What we know: Blueprint uses IVFFlat with 50 lists. HNSW (available in pgvector 0.5+) provides better recall at higher memory.
   - What's unclear: Whether Supabase's pgvector version supports HNSW. What the row count will look like after 90 days (~45K-60K rows).
   - Recommendation: Start with IVFFlat (proven in blueprint). At <100K rows, IVFFlat with 50 lists is sufficient. Evaluate HNSW only if query accuracy is unsatisfactory.

3. **ScreenPipe vs Custom Build Decision Point**
   - What we know: ScreenPipe v0.3.x has MCP server, audio capture, better OCR. Custom build is simpler, more stable, lighter.
   - What's unclear: ScreenPipe Windows stability in March 2026 (may have improved since blueprint research).
   - Recommendation: Build custom for Phase 7 (lower risk, faster). Leave a note to evaluate ScreenPipe in 3-6 months. The architecture supports swapping the capture backend without changing the query/embed/integration layers.

4. **OCR Text Post-Processing for Sensitive Data**
   - What we know: Privacy filter skips capture when excluded apps are active. But what if sensitive data appears in non-excluded apps (e.g., a credit card number in a Chrome tab)?
   - What's unclear: How aggressive the post-OCR text scanning should be. Regex patterns for PII (SSN, credit card, etc.) can produce false positives.
   - Recommendation: Implement a lightweight post-OCR regex scanner for high-confidence patterns (credit card regex, SSN regex). Log filtered captures but do not store the OCR text. Err on the side of filtering (better to lose a capture than to store a credit card number).

## Sources

### Primary (HIGH confidence)
- `08-Capabilities-Deep-Dive/screen-database/windows-capture-pipeline.md` - Full capture service implementation with Python code
- `08-Capabilities-Deep-Dive/screen-database/data-pipeline.md` - Sync architecture (Windows to Supabase), embedding pipeline
- `08-Capabilities-Deep-Dive/screen-database/storage-indexing.md` - Supabase schema, chunking, hybrid search RPC function
- `08-Capabilities-Deep-Dive/screen-database/query-interface.md` - Agent tool definition, check-in integration, example interactions
- `08-Capabilities-Deep-Dive/screen-database/privacy-security.md` - Exclusion lists, encryption, RLS, Telegram controls, legal considerations
- `08-Capabilities-Deep-Dive/screen-database/tool-comparison.md` - ScreenPipe vs Windows Recall vs OpenRecall vs custom build evaluation
- `08-Capabilities-Deep-Dive/document-processing/ocr-engine-selection.md` - Tesseract vs cloud OCR detailed comparison with benchmarks
- `11-Implementation-Roadmap/phase-12-screen-database.md` - Original 3-week implementation plan
- `~/.openclaw/src/checkin/context-assembler.ts` - Existing check-in context pattern (dynamic import, 2s timeout, graceful degradation)
- `~/.openclaw/src/telegram/commands.ts` - Existing Telegram command registration pattern
- `~/.openclaw/config/integrations.json` - Supabase MCP server config (paused status confirmed)

### Secondary (MEDIUM confidence)
- [python-mss documentation](https://python-mss.readthedocs.io/) - v10.x confirmed, multi-monitor support, pure Python
- [PyPI mss](https://pypi.org/project/mss/) - Latest version details
- [Supabase pgvector docs](https://supabase.com/docs/guides/database/extensions/pgvector) - Extension setup, vector columns, indexing
- [Supabase Python client reference](https://supabase.com/docs/reference/python/introduction) - Batch insert patterns
- [pystray documentation](https://pystray.readthedocs.io/en/latest/usage.html) - System tray API, threading model
- [Supabase pausing documentation](https://supabase.com/docs/guides/troubleshooting/pausing-pro-projects-vNL-2a) - Restore window, Pro tier behavior
- [ScreenPipe GitHub](https://github.com/screenpipe/screenpipe) - v0.3.x, MCP server, $2.8M funding Jul 2025

### Tertiary (LOW confidence)
- ScreenPipe Windows stability claims - Multiple web sources mention improvement but no authoritative benchmarks found. Recommend testing before committing.
- PaddleOCR vs Tesseract accuracy on screen text specifically - Benchmarks exist for document OCR but not for rendered screen text. Tesseract assumption based on blueprint and clean-text reasoning.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Blueprint provides working code, libraries are mature and well-documented, versions verified via PyPI/npm
- Architecture: HIGH - Blueprint covers all architectural components end-to-end. Integration points with existing codebase (check-in assembler, Telegram commands) are clearly identified
- Pitfalls: MEDIUM-HIGH - Privacy and storage pitfalls are well-documented in blueprint. Supabase paused-project blocker is the highest-risk item. Windows daemon stability is a known concern with established mitigations (NSSM, heartbeat monitoring)

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (30 days -- stable technology, main risk is Supabase project state)

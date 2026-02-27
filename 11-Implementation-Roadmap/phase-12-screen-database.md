# Phase 12 - OCR Screen Database (Week 12-14)

> **Depends on:** Phase 5 (Supabase operational), Phase 2 (Network connectivity)

## Goal

Deploy continuous screen capture + OCR on the Windows desktop, synced to Supabase, searchable by the OpenClaw agent. Enables "What was I looking at when working on X?" queries.

---

## Prerequisites

- [ ] Supabase active with pgvector extension enabled (Phase 5)
- [ ] Python 3.11+ installed on Windows desktop
- [ ] Tesseract OCR installed on Windows
- [ ] Ollama running on Mac Mini for embedding generation (Phase 3)

---

## Week 12: Windows Capture Service

### Day 1-2: Core Capture Pipeline

1. Install dependencies on Windows: `pip install mss pygetwindow pytesseract pillow`
2. Install Tesseract OCR from UB Mannheim builds
3. Deploy the capture service: screenshot → active window detection → OCR → SQLite
4. Configure 30-second capture interval
5. Test: run for 1 hour, verify captures in local SQLite

### Day 3-4: Privacy Filters

1. Configure excluded applications list (password managers, banking apps)
2. Implement private browsing detection (InPrivate, Incognito, Private Browsing)
3. Add user-configurable exclusion patterns via YAML config
4. Test: open 1Password, verify capture is skipped; open Chrome Incognito, verify skipped
5. Deploy system tray controls (pause/resume/status indicator)

### Day 5: Content Deduplication

1. Implement MD5 content hash deduplication (skip if screen hasn't changed)
2. Test: leave a static screen for 5 minutes, verify only 1 capture stored
3. Verify dedup reduces storage by ~40-60% vs capturing every frame

---

## Week 13: Data Pipeline + Embeddings

### Day 1-2: Supabase Sync

1. Create `screen_captures` table in Supabase (see schema-design.md)
2. Deploy the sync service: batch upload unsynced captures every 60 seconds
3. Test: capture on Windows → verify row appears in Supabase within 2 minutes
4. Test offline handling: disconnect internet, capture continues locally, sync catches up on reconnect

### Day 3-4: Embedding Pipeline

1. Deploy the embedding generation job on Mac Mini
2. Fetch unembedded captures from Supabase → generate embeddings via Ollama (nomic-embed-text) → update Supabase
3. Test: verify embeddings are 768-dim float32 vectors
4. Create the `search_screen_captures` RPC function for hybrid search

### Day 5: Query Testing

1. Accumulate 1-2 days of captures
2. Test natural language queries: "What was I working on in Excel?"
3. Test time-based queries: "What was on my screen at 2 PM yesterday?"
4. Test app-based filters: "Show me everything from VS Code today"
5. Tune similarity threshold (start at 0.7, adjust based on result quality)

---

## Week 14: Agent Integration + Polish

### Day 1-2: Agent Tool Registration

1. Register `screen_recall` tool in OpenClaw's tool registry
2. Test agent queries via Telegram: user asks recall question → agent searches → returns answer
3. Integrate with proactive check-ins: check-in engine reads recent screen activity for context

### Day 3: Retention + Summaries

1. Implement daily summary generation (end-of-day Haiku summarization)
2. Write daily summaries to `memory/logs/YYYY/MM/DD.md`
3. Configure retention: 30 days for raw images (Windows), 90 days for OCR text (Supabase)
4. Test retention cleanup: manually age a test capture, verify it gets cleaned up

### Day 4-5: Windows Service + Go-Live

1. Set up the capture service as a Windows Task Scheduler job (or NSSM service) for auto-start on boot
2. Configure Telegram `/screen` commands (pause, resume, delete, status)
3. Full end-to-end test: capture → sync → embed → query → answer
4. Monitor for 1 week: storage growth, sync reliability, query quality

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Capture reliability | > 95% of expected captures recorded (accounting for dedup) |
| Sync latency | < 2 minutes from capture to Supabase |
| Embedding latency | < 5 minutes from sync to embedded |
| Query relevance | > 70% of top-5 results are relevant (manual evaluation of 20 queries) |
| Storage growth | < 15 MB/day in Supabase |
| Privacy compliance | 0 captures of excluded apps in database |

---

## Reference Docs

- [Tool Comparison](../08-Capabilities-Deep-Dive/screen-database/tool-comparison.md)
- [Windows Capture Pipeline](../08-Capabilities-Deep-Dive/screen-database/windows-capture-pipeline.md)
- [Data Pipeline](../08-Capabilities-Deep-Dive/screen-database/data-pipeline.md)
- [Storage & Indexing](../08-Capabilities-Deep-Dive/screen-database/storage-indexing.md)
- [Query Interface](../08-Capabilities-Deep-Dive/screen-database/query-interface.md)
- [Privacy & Security](../08-Capabilities-Deep-Dive/screen-database/privacy-security.md)

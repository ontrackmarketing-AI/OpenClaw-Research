---
phase: 07-ocr-screen-watching
plan: 01
subsystem: screen-capture
tags: [python, mss, pytesseract, qdrant, better-sqlite3, ollama, nomic-embed-text, http-receiver]

requires:
  - phase: 06-task-rag
    provides: Qdrant client utilities (createQdrantClient, embed) and collection patterns
provides:
  - Windows screen capture daemon with privacy-first OCR pipeline
  - Mac HTTP receiver for capture ingestion (port 7890)
  - Local SQLite storage for screen captures on both Windows and Mac
  - Qdrant screen-captures collection with 768-dim embeddings
  - Embed worker that reads local SQLite and upserts to Qdrant
  - Command relay (Telegram -> Mac SQLite -> Windows polls)
affects: [07-02, check-in, telegram]

tech-stack:
  added: [mss, pytesseract, pygetwindow, pystray, httpx]
  patterns: [privacy-first capture (filter before screenshot), HTTP receiver for cross-machine sync, local-first with Qdrant vectors]

key-files:
  created:
    - openclaw-capture/main.py
    - openclaw-capture/capture/daemon.py
    - openclaw-capture/capture/privacy.py
    - openclaw-capture/capture/dedup.py
    - openclaw-capture/sync/mac_sync.py
    - openclaw-capture/sync/offline_queue.py
    - openclaw-capture/tray/tray_app.py
    - openclaw-capture/config/screen_capture.yaml
    - ~/.openclaw/src/screen/local-db.ts
    - ~/.openclaw/src/screen/receiver.ts
    - ~/.openclaw/src/screen/collection-init.ts
    - ~/.openclaw/src/screen/embed-worker.ts
    - ~/.openclaw/src/screen/types.ts
  modified:
    - ~/.openclaw/package.json

key-decisions:
  - "Replaced Supabase with local Qdrant + SQLite + HTTP receiver — user uses 5G with rotating IPs, everything stays local"
  - "Mac HTTP receiver on port 7890 using node:http (no Express) — minimal dependencies"
  - "mDNS hostname (Brysons-Mac-mini.local) instead of hardcoded IP for cross-machine discovery"
  - "Embed worker reuses shared embed() from vector-search.ts — consistent with Phase 6 patterns"

patterns-established:
  - "Privacy-first capture: should_skip() called BEFORE mss.grab() — no screenshot taken for excluded apps"
  - "Cross-machine sync via HTTP receiver on local network with mDNS discovery"
  - "Screen capture Qdrant collection follows same 768-dim Cosine pattern as task-rag collections"

requirements-completed: [OCRW-01, OCRW-02, OCRW-03]

duration: 45min
completed: 2026-03-03
---

# Phase 07 Plan 01: Screen Capture Pipeline Summary

**Windows capture daemon with privacy filtering, Mac HTTP receiver, local SQLite storage, and Qdrant embedding pipeline via Ollama**

## Performance

- **Duration:** ~45 min
- **Tasks:** 3 (2 auto + 1 human-verify checkpoint)
- **Files created:** 14
- **Files modified:** 1

## Accomplishments
- Windows Python daemon captures screen every 30s with privacy-first filtering (password managers, banking, personal apps, incognito, PII regex redaction)
- Content hash deduplication prevents storing identical consecutive screenshots (SHA-256)
- Mac HTTP receiver on port 7890 ingests captures from Windows via mDNS hostname
- Embed worker generates 768-dim vectors via Ollama nomic-embed-text, stores in Qdrant screen-captures collection
- System tray icon with pause/resume/delete/status/quit controls
- Command relay: Telegram -> Mac SQLite commands table -> Windows daemon polls and executes

## Task Commits

1. **Task 1: Windows capture daemon** - `d6c3967` (feat)
2. **Task 2: Supabase schema + embed worker** - `a14a975` + `7530f56` (feat, later reworked)
3. **Deviation: Replace Supabase with local Qdrant** - `e4fdc0f` + `41b3417` (refactor)
4. **Fix: mDNS hostname** - `342ce59` (fix)
5. **Task 3: Human verification** - approved (captures confirmed flowing)

## Deviations from Plan

### Major Deviation: Supabase -> Local Qdrant + SQLite

- **Found during:** Task 3 checkpoint (user feedback)
- **Issue:** Plan specified Supabase for storage and embeddings. User clarified: project uses Qdrant, everything local.
- **Fix:** Complete rework — created Mac HTTP receiver, local SQLite layer, rewrote embed worker to use Qdrant
- **Additional fix:** User has 5G with rotating IP — switched from hardcoded IP to mDNS hostname (Brysons-Mac-mini.local)
- **Impact:** Better architecture — no cloud dependency, consistent with existing Qdrant patterns from Phase 6

## Issues Encountered
- Port 7890 already in use on second start attempt (receiver was already running from first attempt)
- `@supabase/supabase-js` removed from package.json (only screen module used it)

## Next Phase Readiness
- Captures flowing from Windows to Mac (7+ confirmed)
- Qdrant collection ready for vector search
- Plan 07-02 can build query layer, check-in integration, and Telegram /screen command

---
*Phase: 07-ocr-screen-watching*
*Completed: 2026-03-03*

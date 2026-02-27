# OCR Screen Database -- Tool Comparison

> **Status:** Research | **Last Updated:** 2026-02-26
> **Applies to:** User's Windows desktop (standard PC, no Copilot+ NPU)

---

## 1. Requirements

The user needs continuous screen capture + OCR on their Windows desktop, flowing into a searchable database that the OpenClaw agent can query. Key question: "What was I looking at when I was working on X?"

**Hard requirements:**
- Runs on a standard Windows desktop (no NPU / Copilot+ hardware)
- Provides an API or queryable data store for external access
- Local-first (data does not leave the user's machines)
- Captures at configurable intervals (5-30 seconds)
- Handles multi-monitor setups

---

## 2. Tool Comparison

| Dimension | ScreenPipe | Windows Recall | OpenRecall | Custom (mss+Tesseract+SQLite) |
|-----------|-----------|---------------|------------|-------------------------------|
| **Status** | Active, experimental on Windows | Production (Copilot+ only) | Early-stage (v0.1) | N/A (build yourself) |
| **Runs on standard desktop** | Yes | **No** (requires NPU) | Yes | Yes |
| **Windows stability** | Experimental; known DB lock bugs | Production | Basic but functional | Depends on implementation |
| **OCR engine** | Windows Native OCR / Tesseract | Proprietary NPU model | CLIP + basic OCR | Tesseract 5.x (LSTM) |
| **External query API** | Yes (`localhost:3030/search`) | **No** public query API | **No** (browser UI only) | Yes (you build it) |
| **Storage format** | SQLite + MP4 (local) | Encrypted proprietary DB | SQLite + PNG (unencrypted) | SQLite + JPEG/PNG |
| **Encryption at rest** | No | Yes (BitLocker + Windows Hello) | No (planned) | You implement |
| **Privacy model** | Local-first; optional cloud | Local, opt-in | Fully local | Fully local |
| **Pricing** | Free (OSS core); ~$400 lifetime binary | Free (Copilot+ PC required) | Free (OSS) | Free (OSS deps) |
| **Storage (8 hrs/day, 30s interval)** | ~1-3 GB/day (MP4) | ~2.3 GB/day | ~0.3-0.7 GB/day (PNG) | ~0.1-0.15 GB/day (JPEG) |
| **Maturity** | Medium (v0.x, active but unstable) | High (Microsoft-backed) | Low (proof-of-concept) | Depends on build quality |
| **MCP server support** | Yes (built-in) | No | No | You build it |

---

## 3. Eliminated Options

### Windows Recall -- Eliminated

**Reason:** Requires a Copilot+ PC with NPU (40+ TOPS). The user's standard Windows desktop does not have the required hardware. There is no software upgrade path. Additionally, Recall provides no public query API for external processes.

### Limitless (formerly Rewind) -- Eliminated

**Reason:** Meta acquired Limitless in December 2025. Screen and audio capture was disabled December 19, 2025. The service is being wound down. Not viable for any new use case.

---

## 4. Viable Options (Ranked)

### Option 1: ScreenPipe (Recommended if stability improves)

**Pros:**
- REST API at `localhost:3030` enables direct querying from Mac Mini
- MCP server support for AI agent integration
- Active development community
- Captures both screen OCR and audio transcription
- Handles multi-monitor natively

**Cons:**
- Windows version has known stability issues (DB lock errors, UI freezes)
- $400 one-time or $39/month for the desktop binary (OSS core is free but requires building from source)
- MP4 storage is heavier than necessary for OCR-only use

**Verdict:** Best feature set but Windows stability is a risk. Monitor the project; if stability improves, this becomes the clear winner.

### Option 2: Custom Build (mss + Tesseract + SQLite) -- Recommended now

**Pros:**
- Complete control over capture frequency, storage format, API design
- Mature, stable dependencies (mss, pytesseract, sqlite3 all production-grade)
- Lightest storage footprint (~100-150 MB/day with JPEG compression)
- Can expose exactly the API the Mac Mini needs (FastAPI REST or direct Supabase push)
- No licensing cost
- Can add FTS5 and vector embeddings natively in SQLite

**Cons:**
- Must build and maintain the capture service yourself
- Tesseract OCR accuracy is lower than native Windows OCR for complex UI elements
- No audio transcription (screen only)
- Must implement multi-monitor handling manually

**Verdict:** Most pragmatic option. Small Python service (~200 lines) covers the core use case. Extend as needed.

### Option 3: OpenRecall -- Not recommended yet

**Pros:**
- Free, open source, works on any Windows PC
- Uses CLIP embeddings for semantic search

**Cons:**
- No external query API (browser UI only)
- v0.1 maturity -- not production-ready
- No encryption
- Limited OCR accuracy
- No active maintainer guarantees

**Verdict:** Watch this project. If it adds a REST API and stabilizes, it becomes a viable alternative to the custom build.

---

## 5. Recommendation

**Short term (now):** Build a custom Python capture service using `mss` + Tesseract + SQLite. This is ~4-8 hours of development for a solid MVP that covers the core use case.

**Medium term (3-6 months):** Evaluate ScreenPipe Windows stability. If it reaches production quality, migrate to ScreenPipe for its superior feature set (MCP server, audio capture, better OCR).

**Long term:** If Windows Recall opens a public query API or the user upgrades to Copilot+ hardware, reconsider Recall as the lowest-maintenance option.

---

## Next Steps

- [Windows Capture Pipeline](windows-capture-pipeline.md) -- Custom build implementation
- [Data Pipeline](data-pipeline.md) -- Getting data from Windows to Mac Mini
- [Storage & Indexing](storage-indexing.md) -- Database schema and search

# Stack Research

**Domain:** Autonomous AI agent platform — operator automation layer on OpenClaw
**Researched:** 2026-02-28
**Confidence:** HIGH (core infrastructure verified via PyPI/official docs), MEDIUM (integration patterns), LOW (OpenClaw internals marked inline)

---

## Context

This is a brownfield build. The OpenClaw platform (v2026.2.25+) plus Docker infrastructure (PostgreSQL 16, Redis 7, Qdrant, n8n) is already specified in the PRD. This research covers the **operator automation layer** added on top: email triage, iMessage management, OCR screen watching, document generation, and per-task RAG. Every library version below is verified against PyPI or official docs as of 2026-02-28.

---

## Recommended Stack

### Core Platform (Pre-Decided, Locked)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| OpenClaw | v2026.2.25+ | Agent runtime — skills, channels, MCP, memory | Already designed; v2026.2.25 mandatory (patches CVE-2026-27001 directory injection) |
| Node.js | 22+ (LTS) | OpenClaw runtime requirement | OpenClaw uses Vitest vmForks on Node 22/23; confirmed in AGENTS.md |
| TypeScript | Latest via pnpm | OpenClaw skill language | Skills are source-published TypeScript, not bundled JS |
| Docker Compose | Latest stable | Container orchestration | Security isolation, reproducible deployment, non-root containers |
| PostgreSQL | 16 | Persistent relational storage for OpenClaw | PRD-specified; long-term support, pgvector support |
| Redis | 7 | Session state, pub/sub, job queue | PRD-specified; append-only persistence for durability |
| Qdrant | Latest stable | Vector similarity search | PRD-specified; 768-dim cosine, per-task collections, 4x perf vs alternatives |
| n8n | Latest stable | API security proxy + workflow orchestration | Agent never holds external API keys; mediates all writes |
| Ollama | Latest stable | Local model inference | Free inference; qwen3:14b (9.3GB, 40K ctx), nomic-embed-text v1.5 (768-dim) |
| Tailscale | Latest stable | VPN access control | Replaces public exposure; ACL-controlled ports 3000/18789/5678/22 |

### Operator Automation Layer (This Build)

#### Email Triage — Gmail

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| google-api-python-client | 2.190.0 | Gmail REST API access (read, label, draft, send) | HIGH — verified PyPI 2026-02-12 |
| google-auth-oauthlib | Latest | OAuth 2.0 desktop flow for credential management | HIGH — official Google requirement |
| google-auth-httplib2 | Latest | HTTP transport for Google auth | HIGH — official Google requirement |

**Rationale:** Official Google recommendation for Python Gmail access. OAuth 2.0 desktop flow with stored token.json is the correct pattern for a local agent (not service account — no domain admin required). Request only `gmail.readonly` + `gmail.modify` scopes; do not request `gmail.labels` unless label management is needed. Token refresh is automatic. Rate limit awareness: sending costs 100 quota units; reads cost far less.

**Do NOT use:** `simplegmail`, `EZGmail`, or any unofficial wrapper. They abstract away error handling needed for an autonomous agent and lag behind Google API changes.

#### iMessage Management — BlueBubbles

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| bluebubbles-server (macOS app) | Latest | REST API + webhooks over iMessage database | HIGH — official OpenClaw channel |
| httpx | 0.28.1 | Async REST client to call BlueBubbles API | HIGH — verified PyPI 2024-12-06 |

**Rationale:** BlueBubbles is the **only** production-viable iMessage integration for OpenClaw in 2026. OpenClaw's own docs explicitly recommend it over the legacy `imsg` channel. It runs as a macOS server app on the agent machine, exposes REST endpoints (`GET /api/v1/ping`, `POST /message/text`), and delivers incoming messages via webhooks. macOS Sequoia 15 is fully supported; macOS Tahoe 26 works with caveats (Edit broken, group icon sync unreliable).

**Critical warning:** Apple has stated it will terminate support for non-compliant applications using private iMessage APIs in June 2026. BlueBubbles uses the private API via its helper app. Monitor BlueBubbles releases closely after May 2026. imsg-plus is an alternative CLI but lacks webhook delivery making it unsuitable for always-on agents.

**Configuration:**
```json
{
  "channels": {
    "bluebubbles": {
      "enabled": true,
      "serverUrl": "http://localhost:1234",
      "password": "strong-random-password",
      "webhookPath": "/bluebubbles-webhook"
    }
  }
}
```

#### OCR Screen Watching — Mac Vision Framework

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| ocrmac | 1.0.1 | Python wrapper for Apple Vision OCR on macOS | HIGH — verified PyPI 2026-01-08 |
| mss | 10.1.0 | Ultra-fast screenshot capture (15-20x faster than Pillow) | HIGH — verified PyPI 2025-08-16 |

**Rationale:** `ocrmac` wraps Apple's native `VNRecognizeTextRequest` via PyObjC. On Apple Silicon, this runs on the Neural Engine — measured at ~207ms per frame on M3 Max. Since macOS Sonoma, `ocrmac` also supports LiveText (stronger than VisionKit OCR). `mss` uses CoreGraphics natively on macOS, capturing screens without any external dependencies. Together they are the correct stack for the Mac Mini M4 Pro.

**Do NOT use:** `pytesseract` on macOS. It runs on CPU, achieves ~80% accuracy on real-world screenshots vs Apple Vision's near-perfect quality on macOS native UI, and has no Neural Engine access.

**Do NOT use:** `pyautogui` for capture. It is slow and adds a dependency chain (Pillow, etc.) that mss eliminates.

**Cross-machine pattern:** The Mac Mini cannot directly see the Windows desktop screen pixels. The agent machine must receive screenshots from Windows. Recommended pattern: a lightweight Windows-side Python script (mss + requests) running as a Windows startup task, POSTing compressed screenshots to the agent's FastAPI endpoint on a configurable interval. The OpenClaw agent then runs ocrmac on received images.

#### Document Generation — Gamma MCP

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| gamma-mcp-server (official) | Latest | Create presentations via Gamma API through MCP | MEDIUM — official MCP from developers.gamma.app |

**Rationale:** Gamma has an official MCP server documented at `developers.gamma.app/docs/gamma-mcp-server`. Multiple open-source implementations exist on GitHub (`statechangelabs/gamma-app-mcp`, `CryptoJym/gamma-mcp-server`). OpenClaw natively supports MCP servers declared in `openclaw.yaml` — no custom code needed. The workflow is: meeting transcript → Claude analysis → slide outline → Gamma MCP `create_presentation` call with saved theme ID.

**Warning:** Gamma MCP API access is not yet broadly available as of 2026-02-28. You must request access via their API Slack channel. Have a fallback ready (manual Gamma workflow).

#### Notion Integration

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| notion-client | 3.0.0 | Official Notion API SDK (sync + async) | HIGH — verified PyPI 2026-02-16 |

**Rationale:** `notion-client` is the official Notion API SDK maintained by ramnes (community) with Notion's endorsement. Version 3.0.0 released 2026-02-16 is current. Use the async client (`AsyncClient`) for non-blocking database operations. Use for: creating todo items, logging action items, updating knowledge base pages, syncing meeting outputs.

**Authentication:** Use an internal integration token (not OAuth) for single-workspace operator use. Keep token in `.env`, inject via Docker Compose.

#### Memory — Hybrid Search (File-First)

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| qdrant-client | 1.17.0 | Python client for Qdrant vector store | HIGH — verified PyPI 2026-02-19 |
| sqlite-vec | Latest stable | SQLite extension for vector storage (local, no server) | MEDIUM — active development, breaking changes expected |

**Rationale:** Two-tier memory. Primary: MEMORY.md (file-based, markdown, human-readable). Index tier: SQLite FTS5 (BM25 keyword) + Qdrant (768-dim cosine vector). Hybrid search via Reciprocal Rank Fusion (k=60, weights 0.6 vector / 0.4 BM25). nomic-embed-text v1.5 generates 768-dim embeddings; cosine similarity threshold 0.7. Per-task Qdrant collections isolate error/success patterns by task type (gmail-triage, imessage-draft, proposal-gen, etc.).

**Warning on sqlite-vec:** Still in active development with breaking changes expected. Use Qdrant as the authoritative vector store; sqlite-vec is optional for in-process local queries only.

#### Notification & HITL — Telegram

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| python-telegram-bot | 22.6 | Async Telegram Bot API for HITL approval flow | HIGH — verified PyPI 2026-01-24 |

**Rationale:** python-telegram-bot 22.6 provides a pure async interface (Python 3.10+) with inline keyboards for approve/reject callbacks. Pattern: RED actions (DELETE, send external email, push to CRM) generate Telegram messages with `[APPROVE]` / `[REJECT]` inline buttons. YELLOW actions auto-execute after 5-minute timeout. GREEN actions execute immediately. The bot polls or uses webhook — for a local agent behind Tailscale, long-polling is simpler than hosting a webhook endpoint.

#### Service Layer — FastAPI

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| fastapi | 0.134.0 | Async REST API for internal agent endpoints | HIGH — verified PyPI 2026-02-27 |
| uvicorn | Latest | ASGI server for FastAPI | HIGH — standard FastAPI production server |

**Rationale:** FastAPI 0.134.0 is the current standard for Python async microservices. Used for: receiving OCR screenshots from Windows agent script, receiving n8n webhook callbacks, exposing OpenClaw skill trigger endpoints. Not public-facing — all traffic via Tailscale VPN, localhost binding only.

#### HTTP Client

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| httpx | 0.28.1 | Async HTTP client for all outbound API calls | HIGH — verified PyPI 2024-12-06 |

**Rationale:** httpx provides sync + async APIs with HTTP/2 support. Use `AsyncClient` with connection pooling for high-frequency API calls (BlueBubbles, n8n, Fellow). Use within FastAPI's async context.

#### AI Model Routing

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| anthropic | 0.84.0 | Official Anthropic Python SDK (Claude API) | HIGH — verified PyPI 2026-02-25 |

**Rationale:** anthropic 0.84.0 supports prompt caching (v0.83.0+, no longer needs beta prefix). Cache duration: 5 min standard, 1 hr at extra cost. Cache writing costs 25% more than base input; cache reads cost 10% of base. System prompt caching achieves 60-90% input token reduction on repeat calls. Use `cache_control: {"type": "ephemeral"}` on stable prompt blocks. 4-tier routing: Ollama qwen3:14b → Claude Haiku 4.5 → Claude Sonnet 4.5 → Claude Opus 4.6 (free/~50%/~15%/~5% split by task complexity).

#### Fellow Integration

| Integration | Method | Confidence |
|-------------|--------|------------|
| Fellow REST API | Direct HTTP (httpx) with Bearer token | MEDIUM — Fellow API documented, requires admin toggle |

**Rationale:** Fellow provides a REST API for transcripts, notes, and action items. Admin enables Developer API in Workspace Settings → Security; each user creates personal key under User Settings → Developer Tools. Webhooks fire on meeting recap, action item created, decision logged. Use httpx AsyncClient + n8n webhook proxy pattern (agent never holds Fellow API key directly).

#### Apple Notes Integration

| Integration | Method | Confidence |
|-------------|--------|------------|
| Apple Notes MCP Server | MCP via OpenClaw | MEDIUM — community MCP server, AppleScript-backed |

**Rationale:** Use the community Apple Notes MCP server (`siddhant-k-code/apple-notes`) via OpenClaw's native MCP support. It provides read/search via AppleScript bridge. Apple Notes requires Automation permission in System Settings → Privacy & Security → Automation. For transcript extraction (auto-added by Plaud/manual), search notes by keyword or date.

#### GoHighLevel Integration

| Integration | Method | Confidence |
|-------------|--------|------------|
| GoHighLevel MCP (existing TypeScript) | Direct MCP via OpenClaw | HIGH — existing code in repo |
| GoHighLevel Official MCP | HTTP-based MCP (hosted) | MEDIUM — GoHighLevel's own MCP server now live |

**Rationale:** The existing TypeScript GHL MCP server is production-ready. Reads go direct; writes (contact updates, opportunity pushes) route via n8n proxy to maintain the "agent never holds external API keys" invariant. GoHighLevel's official hosted MCP is an alternative but its 269+ tools are likely more than needed and API key control is better maintained via n8n.

#### Clay.com Integration

| Integration | Method | Confidence |
|-------------|--------|------------|
| Clay REST API via n8n proxy | n8n webhook trigger → Clay table → n8n callback | MEDIUM — verified pattern from Clay community |

**Rationale:** Clay has no Python SDK. All enrichment goes through n8n: agent triggers n8n webhook → n8n HTTP action pushes lead to Clay table → Clay runs waterfall → Clay HTTP action POSTs result back to n8n → n8n sends to agent. This keeps Clay API key in n8n (not in agent), respects the $100/mo credit cap, and matches the existing waterfall pattern.

#### Airtable Integration

| Integration | Method | Confidence |
|-------------|--------|------------|
| airtable-mcp-server | MCP via OpenClaw (npm package 1.9.6) | HIGH — active MCP, 23 days ago update |

**Rationale:** The npm `airtable-mcp-server` v1.9.6 is actively maintained and already integrated (per PROJECT.md: "Airtable MCP: Active and working"). Declare in `openclaw.yaml` under `mcp_servers`.

#### Testing

| Tool | Version | Purpose | Confidence |
|------|---------|---------|------------|
| vitest | Latest | OpenClaw skill unit testing | HIGH — OpenClaw's own test framework |
| pytest | Latest | Python automation layer testing | HIGH — standard Python testing |
| pytest-asyncio | Latest | Async test support for FastAPI/httpx | HIGH — standard async test pattern |

---

## Installation

### Python Automation Layer

```bash
# Core AI + API
pip install anthropic==0.84.0
pip install google-api-python-client==2.190.0 google-auth-oauthlib google-auth-httplib2
pip install notion-client==3.0.0
pip install python-telegram-bot==22.6
pip install qdrant-client==1.17.0
pip install httpx==0.28.1
pip install fastapi==0.134.0 uvicorn[standard]

# OCR + screen capture (macOS only)
pip install ocrmac==1.0.1
pip install mss==10.1.0

# Testing
pip install pytest pytest-asyncio
```

### OpenClaw Skills (TypeScript)

```bash
# Runs inside OpenClaw's pnpm workspace
pnpm install
pnpm test           # Vitest suite
pnpm test:coverage  # With V8 coverage (target: 80%+ per PROJECT.md)
```

### Docker Compose Core (from PRD)

```yaml
# Key versions from PRD
postgres:16-alpine
redis:7-alpine
qdrant/qdrant:latest
n8nio/n8n:latest
ollama/ollama:latest   # Pull: qwen3:14b, nomic-embed-text:v1.5
tailscale/tailscale:latest
```

### Ollama Models

```bash
ollama pull qwen3:14b           # 9.3GB, 40K context, primary free inference
ollama pull nomic-embed-text    # v1.5, 768-dim, 8192 context (note: Ollama page says 2K but HuggingFace confirms 8192)
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| iMessage | BlueBubbles REST + httpx | imsg-plus CLI | imsg-plus has no webhook delivery; unsuitable for always-on agents |
| iMessage | BlueBubbles | macpymessenger (AppleScript) | No REST API; AppleScript is blocking; unreliable for concurrent agent use |
| OCR (macOS) | ocrmac (Apple Vision) | pytesseract | ~80% accuracy on native UI; CPU-only; no Neural Engine access on M4 Pro |
| OCR (macOS) | ocrmac | EasyOCR | ~3x slower; GPU memory overhead competes with LLM inference |
| Gmail | google-api-python-client | simplegmail | Unofficial; lags API; inadequate error handling for autonomous agent |
| Vector store | Qdrant | Chroma | Qdrant 4x higher RPS; production-grade persistence; better filtering |
| Vector store | Qdrant | pgvector (Supabase) | Supabase paused; pgvector in separate Postgres adds complexity vs dedicated Qdrant |
| HTTP client | httpx | aiohttp | httpx has sync+async in one package; cleaner API; built-in HTTP/2 |
| HTTP client | httpx | requests | requests is sync-only; blocks async event loop |
| HITL channel | Telegram | Slack | Telegram bot API is free and simpler; operator preference noted in PRD |
| Notion SDK | notion-client 3.0.0 | notion-py (jamalex) | notion-py is unmaintained (archived); uses private API |
| Embeddings | nomic-embed-text v1.5 | OpenAI text-embedding-3-small | nomic is free (Ollama local), comparable quality; avoids per-token cost |
| Service layer | FastAPI | Flask | Flask is sync; FastAPI async is needed for concurrent agent + webhook handling |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| pytesseract on macOS | ~80% accuracy on UI screenshots; CPU-bound; no Apple Silicon advantage | ocrmac (Apple Vision Framework via PyObjC) |
| simplegmail / EZGmail | Unofficial wrappers with incomplete error handling; will break autonomously | google-api-python-client (official) |
| notion-py (jamalex/notion-py) | Archived, uses private Notion API, will break on API updates | notion-client 3.0.0 (official SDK) |
| ClawHub community skills (auto-install) | 17% flagged as malicious; RCE risk | Whitelist-only: manually review all skill code before installing |
| Supabase pgvector (current state) | Project paused (ID: jitawzicdwgbhatvjblh); adds external dependency | Qdrant (local Docker, already in stack) |
| aiohttp as HTTP client | Requires separate sync library for non-async contexts; less ergonomic | httpx (sync + async unified) |
| Custom iMessage database reader | chat.db requires Full Disk Access; breaks on macOS updates; no write capability | BlueBubbles REST API |
| Chroma vector store | Lower RPS than Qdrant; less mature filtering; Qdrant already in PRD | Qdrant |
| Direct Clay API from agent | Agent would hold Clay API key; violates security model | n8n proxy pattern (key stays in n8n) |

---

## Stack Patterns by Variant

**If the operator is on macOS Tahoe 26:**
- BlueBubbles "Edit message" will be broken — skip Edit functionality in iMessage skill
- Monitor BlueBubbles release notes closely for Tahoe fixes

**If the operator acquires a Plaud device (planned):**
- Plaud auto-transcribes to Apple Notes — Apple Notes MCP becomes higher priority
- Expand the call-processing skill to ingest Plaud note format

**If Gamma MCP access is denied:**
- Fall back to Gamma's web UI with a manual "propose this outline" Telegram notification to operator
- Do not attempt browser automation (Playwright) — too fragile for production

**If Fellow API access is unavailable:**
- Use Fellow's Zapier integration (webhook → n8n → agent) as interim
- Fellow + Zapier fires on "meeting recap created" → n8n triggers agent transcript processing skill

**If Anthropic rate limits are hit ($50/mo cap exceeded):**
- Route all triage tasks to Ollama qwen3:14b (free)
- Reserve Claude Haiku for classification, Sonnet for drafting, Opus for proposals only

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| python-telegram-bot 22.6 | Python 3.10–3.14 | Requires Python 3.10+; asyncio-only |
| qdrant-client 1.17.0 | Python 3.10+ | Released 2026-02-19; requires Python 3.10+ |
| anthropic 0.84.0 | Python 3.9+ | Prompt caching GA (no beta prefix needed); released 2026-02-25 |
| ocrmac 1.0.1 | macOS 13+, Python 3.x | macOS Sonoma+ recommended for LiveText; M4 Pro tested on Sonoma |
| mss 10.1.0 | macOS/Windows/Linux, Python 3.9+ | No external dependencies; CoreGraphics on macOS |
| fastapi 0.134.0 | Python 3.8+, Pydantic v2 | Released 2026-02-27; requires uvicorn[standard] for WebSocket |
| notion-client 3.0.0 | Python 3.8+ | Released 2026-02-16; sync + async clients |
| nomic-embed-text v1.5 | Ollama latest, 768-dim | Ollama doc says 2K ctx; HuggingFace confirms 8192 token actual input window |
| qwen3:14b | Ollama latest, ~9.3GB VRAM | Mac Mini M4 Pro 48GB easily handles this + Docker services (~11GB) |

---

## Sources

- PyPI/anthropic 0.84.0 — https://pypi.org/project/anthropic/ (verified 2026-02-28)
- PyPI/google-api-python-client 2.190.0 — https://pypi.org/project/google-api-python-client/ (verified 2026-02-28)
- PyPI/notion-client 3.0.0 — https://pypi.org/project/notion-client/ (verified 2026-02-28)
- PyPI/python-telegram-bot 22.6 — https://pypi.org/project/python-telegram-bot/ (verified 2026-02-28)
- PyPI/qdrant-client 1.17.0 — https://pypi.org/project/qdrant-client/ (verified 2026-02-28)
- PyPI/httpx 0.28.1 — https://pypi.org/project/httpx/ (verified 2026-02-28)
- PyPI/fastapi 0.134.0 — https://pypi.org/project/fastapi/ (verified 2026-02-28)
- PyPI/ocrmac 1.0.1 — https://pypi.org/project/ocrmac/ (verified 2026-02-28)
- PyPI/mss 10.1.0 — https://pypi.org/project/mss/ (verified 2026-02-28)
- Ollama/qwen3 — https://ollama.com/library/qwen3 (14b = 9.3GB, 40K ctx)
- Ollama/nomic-embed-text — https://ollama.com/library/nomic-embed-text (v1.5 latest)
- HuggingFace/nomic-embed-text-v1.5 — https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 (768-dim, 8192 ctx, Matryoshka)
- OpenClaw BlueBubbles docs — https://docs.openclaw.ai/channels/bluebubbles (official channel docs)
- OpenClaw AGENTS.md — https://github.com/openclaw/openclaw/blob/main/AGENTS.md (Node 22+, Vitest, pnpm)
- Gamma MCP docs — https://developers.gamma.app/docs/gamma-mcp-server (official, access required)
- Fellow API blog — https://fellow.ai/blog/fellow-api/ (REST API, webhooks, action items)
- Anthropic prompt caching — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (GA, 0.83.0+)
- BlueBubbles REST API — https://docs.bluebubbles.app/server/developer-guides/rest-api-and-webhooks
- sqlite-vec hybrid search — https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html (MEDIUM confidence — breaking changes expected)
- Apple Vision OCR PyObjC — https://yasoob.me/posts/how-to-use-vision-framework-via-pyobjc/ (MEDIUM confidence)
- Clay + n8n pattern — https://intelligentresourcing.co/clay-workflow-expert/clay-n8n-api-workflows-automating-gtm-processes-with-enrichment-and-orchestration (MEDIUM)

---

*Stack research for: OpenClaw operator automation layer — email, iMessage, OCR, document generation, per-task RAG*
*Researched: 2026-02-28*

# Architecture Research

**Domain:** Autonomous AI marketing assistant layered on OpenClaw platform
**Researched:** 2026-02-28
**Confidence:** HIGH — based on 175+ existing research documents, full PRD, and designed system

---

## Standard Architecture

### System Overview

The architecture has two physical machines and five logical layers. The Mac Mini is the agent brain; the Windows desktop is the work surface. Everything flows through cloud connectors and an n8n security proxy. The OpenClaw gateway sits at the center of all agent coordination.

```
WINDOWS DESKTOP (Work Machine)
+--------------------------------------------------------+
|  Screen Capture Service (Python daemon)                |
|  mss + pytesseract → SQLite (local) → Supabase (sync) |
|                                                        |
|  Work apps: GHL, Gmail, Notion, browser, n8n           |
+--------------------------|-----------------------------+
                           | OCR text + metadata
                           | (HTTPS to Supabase)
                           v
              +---------------------------+
              |    SUPABASE (Cloud)       |
              |  screen_captures table    |
              |  pgvector 768-dim         |
              |  evolution_metrics        |
              |  evolution_proposals      |
              +-------------|-------------+
                            | SQL + RPC queries
                            v
MAC MINI M4 PRO (Agent Machine — always-on)
+========================================================+
|                                                        |
|  LAYER 1: OpenClaw Gateway (Port 18789)                |
|  +-----------------+  +---------------+               |
|  | Session Manager |  | Agent Router  |               |
|  | Tool Dispatcher |  | Skill Loader  |               |
|  | Memory Indexer  |  | Plugin Host   |               |
|  +-----------------+  +---------------+               |
|           |                    |                      |
|  LAYER 2: Specialized Agent Pool                       |
|  +----------+ +---------+ +-----------+ +----------+  |
|  | Triage   | | Proposal| | Screen    | | Evolve   |  |
|  | Agent    | | Agent   | | Watcher   | | Agent    |  |
|  +----------+ +---------+ +-----------+ +----------+  |
|           |                    |                      |
|  LAYER 3: Tool Registry (MCP + REST adapters)          |
|  +--------+ +------+ +------+ +-------+ +--------+   |
|  | GHL    | | Clay | | n8n  | |Gamma  | |Airtable|   |
|  | MCP    | | REST | | MCP  | | MCP   | | MCP    |   |
|  +--------+ +------+ +------+ +-------+ +--------+   |
|           |                                           |
|  LAYER 4: n8n Security Proxy (Port 5678)               |
|  Mediates all external writes. Agent never holds keys. |
|                                                        |
|  LAYER 5: Memory System                                |
|  +------------+ +-----------+ +------------------+    |
|  | MEMORY.md  | | SQLite    | | Qdrant Vector    |    |
|  | (4K token  | | FTS5      | | (768-dim, nomic) |    |
|  |  hot load) | | index.db  | | Per-task stores  |    |
|  +------------+ +-----------+ +------------------+    |
|                                                        |
|  Ollama (local inference: qwen3:14b, nomic-embed-text) |
+========================================================+
           |
           | Tailscale VPN (encrypted mesh)
           v
     Operator access: Telegram, Web UI (port 3000)
```

---

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **OpenClaw Gateway** | Central message bus, session management, agent routing, tool dispatch | All agents, all tools, all channels |
| **Triage Agent** | Email and iMessage scanning, classification, surface action items | Gmail MCP, iMessage relay, Notion MCP, Telegram |
| **Proposal Agent** | Meeting transcript processing, discovery form generation, Gamma deck creation | Apple Notes MCP, Fellow API, Gamma MCP, GHL MCP |
| **Screen Watcher Agent** | Interprets OCR screen context, detects work patterns, proactive suggestions | Supabase (screen_captures), Google Calendar, Telegram |
| **Check-in Agent** | 3-5 daily Telegram messages, calendar-aware scheduling, response tracking | Google Calendar, Telegram, Memory system |
| **Evolve Agent** | Weekly metrics analysis, prompt proposals, skill gap detection | Supabase (evolution_metrics), all skill prompts, Telegram |
| **n8n Security Proxy** | Mediates all external writes (email send, GHL write, Clay enrichment, social post) | External APIs (holds keys), OpenClaw (receives instructions) |
| **Windows Capture Service** | Screenshot every 30s, OCR via Tesseract, dedup by content hash, push to Supabase | Supabase (push), local SQLite (buffer) |
| **Memory System (SQLite)** | FTS5 keyword search + sqlite-vec vector search + MEMORY.md hot tier | All agents (read/write), Ollama (embedding generation) |
| **Per-Task RAG Stores** | Isolated Qdrant collections per task type (email-triage, proposal-gen, lead-enrichment) | Owning agent only — prevents cross-contamination |
| **Ollama (local)** | Free local inference for triage/classification; embedding generation (nomic-embed-text) | All agents via model router |
| **Model Router** | 4-tier routing: Ollama → Haiku → Sonnet → Opus by task complexity | All agents, cost circuit breakers |

---

## Recommended Project Structure

```
~/.openclaw/
├── config/
│   ├── agents/                  # YAML agent definitions (one per specialized agent)
│   │   ├── triage.yaml
│   │   ├── proposal.yaml
│   │   ├── screen-watcher.yaml
│   │   ├── checkin.yaml
│   │   └── evolve.yaml
│   ├── model-routing.yaml       # 4-tier model routing rules
│   ├── approval-policy.yaml     # HITL tier classifications (RED/YELLOW/GREEN)
│   └── integrations.json        # MCP server configs (no secrets here)
├── memory/
│   ├── MEMORY.md                # Hot-loaded persistent agent memory (< 4K tokens)
│   ├── index.db                 # SQLite: FTS5 + sqlite-vec + memory_entries
│   ├── config.yaml              # Hybrid search weights, compaction schedule
│   └── logs/YYYY/MM/DD.md       # Daily session logs
├── skills/
│   ├── email-triage/            # Skill: scan inbox, classify, extract actions
│   ├── proposal-pipeline/       # Skill: transcript → form → Gamma deck
│   ├── lead-enrichment/         # Skill: Clay waterfall enrichment pattern
│   ├── ghl-crm/                 # Skill: CRM contact and pipeline management
│   └── screen-recall/           # Skill: query Supabase screen database
├── prompts/                     # Git-tracked prompt files (self-evolution rewrites here)
│   ├── system-prompt.md
│   └── skill-prompts/
├── docker-compose.yml           # OpenClaw + PostgreSQL + Redis + Qdrant + n8n
└── .env                         # Secrets (not git-tracked)

# Windows machine (separate)
~/AppData/Local/OpenClaw/
├── screen_db.sqlite             # Local capture buffer (synced to Supabase)
├── captures/                    # JPEG screenshots (30-day retention)
└── screen_capture.py            # Capture daemon
```

### Structure Rationale

- **agents/ separate from skills/**: Agents are long-lived YAML configs that define behavior. Skills are packaged capabilities agents invoke. One-to-many relationship.
- **memory/index.db + MEMORY.md split**: Hot tier (MEMORY.md, always in context) vs searchable cold tier (SQLite). Different access patterns, different cost profiles.
- **prompts/ git-tracked**: Self-evolution system rewrites prompts. Git gives rollback safety without extra infrastructure.
- **n8n in same Docker network**: Proxy pattern — agent and n8n share a private bridge network, n8n is the only one with external API keys.

---

## Architectural Patterns

### Pattern 1: n8n Security Proxy

**What:** Agent never holds external API keys. All writes (send email, write GHL, post social) go through n8n workflow endpoints that inject credentials at execution time.

**When to use:** Every external write operation. Read operations (GHL MCP reads, Airtable MCP reads) can go direct.

**Trade-offs:**
- Pro: Compromised agent cannot exfiltrate credentials or act autonomously on external systems
- Pro: n8n provides audit log, rate limiting, and retry logic on every external call
- Con: Extra hop adds ~100-200ms latency per call
- Con: n8n must be healthy for any write to succeed (mitigated: reads still work)

**Example n8n proxy workflow:**
```
Webhook trigger (from OpenClaw agent)
    ↓
Validate request (check source IP = Mac Mini on Tailscale)
    ↓
Inject credentials (GHL API key from n8n credential store)
    ↓
Call external API (GoHighLevel, Clay, Gmail send, etc.)
    ↓
Return result to agent via webhook response
```

### Pattern 2: Per-Task RAG Isolation

**What:** Each task type (email-triage, proposal-generation, lead-enrichment, crm-management) has its own Qdrant collection. Errors, successful patterns, and outcomes are indexed separately per task type.

**When to use:** Any recurring agent task that should improve over time. Do NOT merge task stores.

**Trade-offs:**
- Pro: Lead enrichment error patterns don't pollute proposal generation memory
- Pro: Query cost is proportional to task size, not total knowledge base
- Con: Cross-task insight (e.g., "a pattern from email triage applies to proposal writing") requires explicit agent reasoning
- Con: More Qdrant collections to manage

**Example:**
```python
# When indexing an email triage outcome:
qdrant.upsert(
    collection_name="task-email-triage",  # NOT "global-knowledge"
    points=[{
        "id": outcome_id,
        "vector": embed(outcome_text),
        "payload": {"task": "email-triage", "success": True, "pattern": "..."}
    }]
)

# On next email triage run, agent queries only its own history:
results = qdrant.search(collection_name="task-email-triage", query_vector=embed(current_context))
```

### Pattern 3: OCR Bridge (Cross-Machine Visibility)

**What:** Windows desktop runs a Python capture daemon (mss + pytesseract). Every 30 seconds: screenshot, OCR, deduplicate by content hash, write to local SQLite, batch-sync to Supabase. Mac Mini reads from Supabase to understand Windows work context.

**When to use:** Any time the agent needs to know what the operator is doing on Windows. This is the only viable cross-machine visibility mechanism without agent access to the Windows filesystem.

**Trade-offs:**
- Pro: Zero Windows-side OpenClaw installation required; just a Python script
- Pro: Supabase provides 90-day searchable history with vector similarity
- Pro: Privacy filter skips password managers, incognito windows, banking apps
- Con: 30-second granularity; not real-time (acceptable for proactive suggestions, not copilot mode)
- Con: OCR text quality degrades on complex UI (charts, icons, diagrams)
- Con: Supabase free tier insufficient beyond ~1-4 months; Pro tier ($25/mo) required

**Data flow:**
```
Windows (every 30s):
  mss.grab() → PIL Image → pytesseract → OCR text
  → hash check (skip if unchanged)
  → SQLite insert (local buffer, synced=0)
  → Supabase push (batch 50, every 60s)

Mac Mini (on demand or scheduled):
  Ollama embed(query) → Supabase RPC search_screen_captures()
  → ranked results by (0.6 * vector_sim + 0.4 * text_rank)
  → agent context window
```

### Pattern 4: Meeting-to-Proposal Workflow Orchestration

**What:** Multi-step pipeline triggered by call transcript availability. Each step has a clear input/output contract and HITL gate before the next step begins.

**When to use:** Any multi-step workflow where intermediate outputs are human-reviewable and where partial failure should not cascade.

**Trade-offs:**
- Pro: Operator reviews at natural checkpoints (after form creation, before proposal send)
- Pro: Each step is independently retryable without restarting the whole pipeline
- Con: Requires Telegram bot to be reliably connected (critical notification path)
- Con: Human approval latency introduces pipeline delay (acceptable given business impact)

**Workflow:**
```
1. Trigger: Transcript available (Apple Notes MCP detects new note OR Fellow webhook)
        ↓
2. Proposal Agent: Extract key discussion points (Ollama qwen3:14b — free tier)
        ↓
3. Agent: Generate discovery form questions (Haiku — fast and cheap)
        ↓ [HITL GATE: Telegram approval "Review form questions?"]
4. Operator approves form → Agent creates form (Airtable or GHL form via n8n proxy)
        ↓
5. Prospect fills form (external, no agent involvement)
        ↓
6. Trigger: Form submission webhook → n8n → OpenClaw
        ↓
7. Proposal Agent: Assemble presentation brief (Sonnet — quality matters here)
        ↓
8. Agent: Call Gamma MCP generate() with brief + saved theme ID
        ↓ [HITL GATE: Telegram "Review deck at gamma.app/docs/... Approve to export?"]
9. Operator approves → Agent exports PDF → delivers via GHL email (n8n proxy)
```

### Pattern 5: Proactive Task Detection (Screen + Calendar)

**What:** Check-in engine combines OCR screen context, Google Calendar, and memory to generate contextually relevant proactive messages. Not reactive (waiting for a question) — pushes to the operator.

**When to use:** 3-5 times per day at scheduled slots. Defer if user is in a calendar event.

**Trade-offs:**
- Pro: Surfaces relevant work context without operator asking
- Pro: Adaptive scheduling — drops slots with <30% response rate after 14 days
- Con: Requires reliable Telegram delivery (offline = missed check-in)
- Con: Calendar integration adds OAuth complexity in setup

**Context assembly:**
```
On check-in trigger (e.g., 8:30 AM):
  1. Check Google Calendar → any events in next 5 min? → defer 30 min if yes
  2. Query Supabase screen_captures → what was operator working on last 2 hours?
  3. Query MEMORY.md → active projects, open action items
  4. Query Notion MCP → open todos assigned to today
  5. LLM (Ollama qwen3:14b) → generate contextual check-in message
  6. Telegram → send message, await response (2 hour window)
  7. Log outcome → feed adaptive timing model
```

---

## Data Flow

### Primary Flows

**Flow 1: Email Triage (Automated)**
```
Google Calendar: no current meeting
        ↓
Gmail MCP: fetch unread emails (last 4 hours)
        ↓
Triage Agent (Haiku): classify each email
  → ACTIONABLE: extract action item + deadline → Notion todo
  → INFORMATIONAL: tag + archive
  → URGENT: Telegram alert to operator
        ↓
Per-task RAG (task-email-triage): index outcome
        ↓
Daily log: append triage session summary
```

**Flow 2: Lead Pipeline (Full Automation with HITL)**
```
GHL webhook (new lead) → n8n → OpenClaw trigger
        ↓
Lead Enrichment Agent: Clay waterfall via n8n proxy
  (company → person → tech stack → social → intent)
        ↓ [HITL: "Enrich this lead? Cost ~$0.50" — auto-approve after day 30]
Lead Scoring: Ollama (local, free) scores against 15-signal model
        ↓
GHL write via n8n proxy: update contact fields, set pipeline stage
        ↓
If score ≥ threshold: Telegram → "High-value lead: [name]. Generate pitch deck?"
```

**Flow 3: Screen-Driven Proactive Suggestion**
```
Screen Watcher Agent (runs every 15 min):
  Supabase query: last 15 min of screen_captures
        ↓
  Pattern detection (Ollama): "User is looking at GHL leads > 10 min"
        ↓
  If pattern matches known opportunity:
    Check memory: "Have I suggested this recently?" → skip if yes
        ↓
    Generate suggestion (Haiku) → Telegram: "Looks like you're reviewing leads.
    Want me to run enrichment on the unprocessed ones? (14 in queue)"
```

**Flow 4: Self-Evolution Loop (Weekly)**
```
Sunday 3 AM: Evolve Agent trigger
        ↓
Query Supabase (evolution_metrics): last 7 days by skill
  → success rate, HITL approval rate, error types, cost per call
        ↓
Evaluation (Sonnet): "Which skills are underperforming?"
        ↓
Generate proposals (Sonnet): prompt rewrites, model switches, new skill gaps
        ↓
Git branch: evolution/YYYYMMDD-[description]
Apply changes to prompts/ directory
        ↓
Telegram: "Weekly evolution report: 3 improvements proposed. [Review]"
        ↓
48h measurement: compare metrics → auto-rollback if regression
        ↓
If improved: git merge to main
If regressed: git branch delete, revert
```

### State Management

```
MEMORY.md (hot, always in context)
    ↑ append (session end)
    ↑ compaction (weekly, HITL approval)

SQLite index.db (cold, on-demand)
    ↑ ingestion (file watcher, 5 min intervals)
    ↓ hybrid search (FTS5 + sqlite-vec)

Per-task Qdrant collections (persistent, growing)
    ↑ outcome indexing (after each task execution)
    ↓ pre-task recall (before each task starts)

Supabase (remote, screen + evolution data)
    ↑ Windows push (60s batch)
    ↑ Evolve agent metrics write (per session)
    ↓ Screen watcher queries (on demand)
    ↓ Evolution evaluation queries (weekly)
```

---

## Build Order (Dependency Graph)

The build order is determined by dependencies between components. Each phase unlocks subsequent capabilities.

```
Phase 1: Infrastructure Foundation
  Docker stack (OpenClaw + Qdrant + n8n + Redis)
  Ollama + nomic-embed-text + qwen3:14b
  Tailscale VPN
  HITL policy config (approval-policy.yaml)
  [Unlocks: everything]

Phase 2: Security Hardening
  n8n security proxy (6 proxy workflows)
  Container hardening (non-root, read-only FS)
  Cost circuit breakers
  [Required before: any external API calls]

Phase 3: Memory System
  MEMORY.md + daily logs
  SQLite FTS5 + sqlite-vec hybrid search
  Memory compaction schedule
  [Required before: per-task RAG, learning loop]

Phase 4: Core Skills + Integrations
  GHL MCP connect
  Airtable MCP (already active)
  Clay REST adapter via n8n proxy
  6 existing skills → OpenClaw format
  [Required before: lead pipeline, triage workflows]

Phase 5: Notification Channel
  Telegram bot
  HITL approval flow (inline buttons)
  Quiet hours + calendar check
  [Required before: any HITL-gated workflow]

Phase 6: Email + Calendar Triage
  Gmail MCP integration
  Google Calendar MCP
  Email triage agent (classify → Notion todo)
  [Depends on: Phase 3 memory, Phase 5 Telegram]

Phase 7: Proposal Pipeline
  Apple Notes MCP (transcript ingestion)
  Fellow API adapter (meeting recordings)
  Gamma MCP integration (saved themes)
  Proposal agent (transcript → form → deck → HITL)
  [Depends on: Phase 5 Telegram, Phase 4 GHL]

Phase 8: iMessage Triage
  iMessage relay setup (requires iMac or Mac Mini access)
  iMessage triage agent
  [Depends on: Phase 5 Telegram for notifications]

Phase 9: Proactive Check-ins
  Check-in engine (LaunchAgent cron triggers)
  Context assembly (screen + calendar + memory)
  Adaptive timing model
  [Depends on: Phase 3 memory, Phase 5 Telegram, Phase 6 Calendar]

Phase 10: OCR Screen Watcher
  Windows capture daemon install
  Supabase screen_captures schema
  Embedding pipeline (Mac Mini → Supabase)
  Screen watcher agent
  [Depends on: Phase 3 memory, Phase 5 Telegram, Supabase active]

Phase 11: Per-Task RAG (Learning Flywheel)
  Qdrant collections per task type
  Outcome indexing on every skill execution
  Pre-task recall injection
  [Depends on: Phase 4+ skills running, Phase 3 memory]

Phase 12: Self-Evolution
  evolution_metrics table (Supabase)
  Weekly evaluation agent
  Prompt version control (git-tracked)
  Auto-rollback mechanism
  [Depends on: all prior phases generating metrics]
```

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single operator (current) | Monolith — all agents on one Mac Mini, one Qdrant instance, SQLite memory |
| 2-5 operators | Separate Qdrant namespace per operator, shared gateway, individual MEMORY.md per operator |
| Small team (5-20) | External Postgres for sessions, Redis for caching, separate n8n instance per operator context |
| Agency-wide (20+) | Multi-instance gateway behind load balancer, per-team n8n proxies, managed Qdrant cluster |

### Scaling Priorities

1. **First bottleneck:** Qdrant vector search latency as per-task collections grow beyond ~100K vectors. Fix: increase Qdrant memory allocation, tune HNSW index parameters (M=16, ef_construction=128 is a good start).
2. **Second bottleneck:** Ollama inference throughput. One Sonnet call blocks qwen3:14b queue. Fix: priority queue by tier — Sonnet calls get dedicated queue, Ollama gets separate process.

---

## Anti-Patterns

### Anti-Pattern 1: Global Knowledge Base (One RAG for Everything)

**What people do:** Index all agent learning into a single Qdrant collection or SQLite table because it seems simpler.

**Why it's wrong:** Email triage errors ("don't respond to newsletters") bleed into proposal generation context. Lead enrichment patterns corrupt screen watcher recall. The noise floor rises as tasks accumulate, reducing precision across all tasks.

**Do this instead:** Per-task Qdrant collections. The isolation cost is minimal (Qdrant is efficient); the precision gain is substantial.

### Anti-Pattern 2: Agent Holds External API Keys

**What people do:** Pass GHL API key, Clay key, Gmail OAuth tokens directly to the OpenClaw agent via environment variables so it can call APIs directly.

**Why it's wrong:** A prompt injection attack (e.g., a malicious email the triage agent reads) can exfiltrate all secrets. There is no audit trail. Rate limits aren't enforced centrally.

**Do this instead:** n8n security proxy. Agent sends a structured instruction to n8n; n8n injects credentials from its own credential store and makes the external call. Agent never sees the key.

### Anti-Pattern 3: Skipping HITL for "Low-Risk" External Messages

**What people do:** Auto-approve email drafts because "the agent usually writes good emails" and the approval step is slow.

**Why it's wrong:** The Meta incident demonstrated this exactly: a compaction bug dropped safety directives and the agent deleted 200+ emails autonomously. "Usually good" is not "never catastrophic."

**Do this instead:** Keep RED tier actions requiring approval forever. Use YELLOW tier (approve-first-N with expiry) as the relaxation path for genuinely low-risk message patterns only.

### Anti-Pattern 4: Synchronous OCR Blocking Agent Context

**What people do:** Have the Screen Watcher agent wait for each Supabase query to complete before generating its proactive message, then wait for Telegram delivery, creating a sequential blocking chain.

**Why it's wrong:** If Supabase is slow (cold connection, query latency), the entire check-in chain stalls. Calendar check blocks OCR query which blocks context assembly which blocks message generation.

**Do this instead:** Parallel context assembly. Trigger Supabase query, Google Calendar query, and MEMORY.md read concurrently (asyncio.gather). Join results, then generate message. Total latency = slowest single query, not sum of all.

### Anti-Pattern 5: Treating n8n as the Agent

**What people do:** Build all the intelligence into n8n workflows because n8n has the credentials and is already connected to external services. OpenClaw becomes just a text generator.

**Why it's wrong:** n8n workflows are brittle, hard to debug, and have no memory or learning capability. The proposal pipeline becomes hundreds of n8n nodes with no per-task improvement loop.

**Do this instead:** OpenClaw agents hold reasoning, memory, and orchestration. n8n is a dumb credential-holding proxy — it executes simple API calls when told to, nothing more.

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| GoHighLevel | MCP (read) + n8n proxy (write) | MCP server built in TypeScript; writes via 3 n8n workflows |
| Clay.com | REST adapter via n8n proxy | $100/mo cap enforced at n8n level |
| Airtable | MCP (read + write) | Already active; low-risk writes allowed direct |
| Supabase | MCP (read) + direct client (write from Mac Mini) | pgvector for screen DB; evolution metrics |
| Gmail | MCP (read) + n8n proxy (send) | OAuth 2.0; send is RED tier HITL |
| Google Calendar | MCP (read only) | For meeting detection; no write needed initially |
| Gamma | MCP (generate + status + themes) | $10-20/mo Plus tier; HITL before any delivery |
| Apple Notes | MCP or AppleScript bridge | Read-only; transcript ingestion |
| Fellow | Webhook (push when recording ready) | n8n receives, routes to OpenClaw |
| Notion | MCP (read + write todos) | Action items + knowledge base |
| Telegram | Bot API (direct) | Primary HITL channel; no proxy needed (outbound only) |
| n8n | MCP (execute workflows) | Agent instructs n8n; n8n executes with real creds |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Gateway ↔ Agents | Internal pub/sub bus + WebSocket | JSON-RPC 2.0 framing |
| Agents ↔ Tools | MCP protocol (stdio or SSE) | Tool Dispatcher mediates |
| Agents ↔ Memory | Direct SQLite read/write | Via memory API, not raw SQL |
| Agent ↔ n8n proxy | HTTP POST to n8n webhook (Tailscale) | Structured payload: action + params |
| Mac Mini ↔ Supabase | HTTPS (direct Supabase client) | For screen data and evolution metrics |
| Windows ↔ Supabase | HTTPS (sync service, batch 50 rows/60s) | OCR text push; no Mac Mini in this path |
| Evolve Agent ↔ Git | Shell exec git commands in ~/.openclaw | Branch-per-proposal, merge on approval |

---

## Sources

All findings drawn from existing OpenClaw research documents (HIGH confidence — these are the authored design specs):

- `00-Foundation/openclaw-architecture.md` — Gateway, agent pool, tool system design
- `04-Memory-and-RAG/memory-architecture.md` — File-first memory, SQLite FTS5, compaction
- `04-Memory-and-RAG/hybrid-search.md` — RRF fusion, sqlite-vec, search weights
- `04-Memory-and-RAG/visibility-strategy.md` — Two-machine access layer design
- `06-Integrations/integration-architecture.md` — MCP + REST + webhook patterns, n8n proxy
- `08-Capabilities-Deep-Dive/screen-database/windows-capture-pipeline.md` — mss + pytesseract pipeline
- `08-Capabilities-Deep-Dive/screen-database/data-pipeline.md` — Windows → Supabase sync
- `08-Capabilities-Deep-Dive/screen-database/storage-indexing.md` — Supabase schema, hybrid search RPC
- `08-Capabilities-Deep-Dive/proactive-checkins/checkin-engine.md` — Scheduling, calendar-aware deferral
- `08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md` — Gamma MCP tools, HITL flow
- `02-Security/human-in-the-loop.md` — RED/YELLOW/GREEN tier classification
- `12-Self-Evolution/evolution-architecture.md` — Observe-Evaluate-Propose-Act loop
- `.planning/PROJECT.md` — Full requirements, constraints, decisions

---

*Architecture research for: OpenClaw autonomous AI marketing assistant*
*Researched: 2026-02-28*

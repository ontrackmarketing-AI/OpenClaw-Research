# Requirements: OpenClaw

**Defined:** 2026-02-28
**Core Value:** The agent removes redundant tasks from the operator's day by watching, learning, and autonomously executing -- getting better at each task every time it does it.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Infrastructure

- [x] **INFR-01**: OpenClaw v2026.2.25+ running in Docker with PostgreSQL 16, Redis 7, Qdrant, and n8n on openclaw-net bridge
- [x] **INFR-02**: All containers hardened (non-root UID 1000, read-only FS, tmpfs noexec, all caps dropped, PID limit 200)
- [x] **INFR-03**: All Docker ports bound to 127.0.0.1 only -- no public exposure
- [x] **INFR-04**: Ollama running on host with qwen3:14b and nomic-embed-text models loaded
- [x] **INFR-05**: Tailscale VPN configured with ACLs restricting access to ports 3000, 18789, 5678, 22

### Security

- [x] **SECR-01**: n8n security proxy operational -- agent never holds external API keys; 6 proxy workflows (Clay, GHL contacts, GHL messages, email, DataForSEO, Serper)
- [x] **SECR-02** (Partial): HITL approval via Telegram with RED/GREEN/YELLOW tiers -- RED: send messages, delete data, financial >$5, publish content; GREEN: reads, drafts, memory writes, logs; YELLOW: context-dependent with approval thresholds. **Phase 1: tier classification and blocking. Phase 3: Telegram approval channel.**
- [x] **SECR-03**: Cost circuit breakers active -- $50/month Anthropic hard cap, 50 tool calls/session, 30-minute session timeout, $100/month Clay credit cap, 100 emails/day limit
- [x] **SECR-04**: Context window safety -- pinned directives with [PINNED -- DO NOT SUMMARIZE] markers, checkpoint summarization every 20 turns, verification check every 10 turns
- [x] **SECR-05**: Content sanitization in n8n proxy -- strip prompt injection attempts from email/OCR inputs before they reach the agent
- [x] **SECR-06**: Emergency stop procedure tested -- `docker compose stop openclaw` with key revocation within 5 minutes
- [x] **SECR-07**: DELETE operations always require HITL approval -- this rule never relaxes

### Memory

- [x] **MEMR-01**: MEMORY.md persistent agent memory with 4,000 token budget and auto-compaction
- [x] **MEMR-02**: SQLite FTS5 full-text search index (porter unicode61 tokenizer) for keyword matching
- [x] **MEMR-03**: Qdrant vector collection (768-dim, nomic-embed-text embeddings, cosine similarity 0.7 threshold) for semantic search
- [x] **MEMR-04**: Hybrid search merging vector + FTS5 via Reciprocal Rank Fusion (0.6 vector / 0.4 FTS5 weights)
- [x] **MEMR-05**: Daily log directory with compaction (daily -> weekly summaries after 30 days)

### Communication

- [ ] **COMM-01**: User can receive email triage summary via Telegram -- Gmail inbox scanned, actionable items surfaced with sender, subject, and suggested action
- [ ] **COMM-02**: User can approve/reject agent-proposed email actions via inline Telegram buttons
- [ ] **COMM-03**: Agent extracts calendar events from emails and proposes adding them to Google Calendar
- [ ] **COMM-04**: Telegram bot serves as primary command interface -- HITL approvals, agent queries, status updates, quiet hours
- [ ] **COMM-05**: Agent reads iMessage conversations via BlueBubbles relay (read-only, business contacts only)
- [ ] **COMM-06**: iMessage context enriches todo items and check-in suggestions -- "John from Acme texted about the invoice" becomes actionable
- [ ] **COMM-07**: Agent respects Google Calendar -- no check-ins during meetings, defers non-urgent actions to free slots
- [ ] **COMM-08**: Notion integration for centralized task/action logging -- all agent actions and captured items visible in one place

### Task Management

- [ ] **TASK-01**: User has a centralized todo list in Notion populated automatically from email, meetings, iMessage, and screen observations
- [ ] **TASK-02**: Meeting transcripts from Fellow are pulled and processed -- decisions, action items, and open questions extracted
- [ ] **TASK-03**: Call transcripts from Apple Notes are pulled and processed -- same extraction as Fellow
- [ ] **TASK-04**: Agent sends proactive check-ins 3-5 times daily via Telegram -- morning priorities, midday status, evening wrap-up
- [ ] **TASK-05**: Check-ins adapt over a 14-day window based on operator engagement -- learns which time slots get responses
- [ ] **TASK-06**: Check-in templates have anti-repetition logic -- track last 10, never repeat within 3 days

### Proposals

- [ ] **PROP-01**: Agent processes a meeting recording into a slide outline using Claude analysis
- [ ] **PROP-02**: Agent generates a discovery form from meeting context and sends it to the prospect for deeper information
- [ ] **PROP-03**: Agent generates a Gamma presentation using the saved theme from discovery form responses + meeting context
- [ ] **PROP-04**: User reviews Gamma preview link via Telegram before any proposal is delivered -- always HITL Tier 1
- [ ] **PROP-05**: Moving a lead to "qualified" in GHL automatically triggers a tailored pitch deck draft via Gamma MCP
- [ ] **PROP-06**: CRM-triggered decks include industry-specific context pulled from client knowledge RAG

### Model Routing

- [x] **MODL-01**: 4-tier model routing -- Ollama qwen3:14b (free, ~30% traffic) for classification/formatting -> Claude Haiku 4.5 (~50%) for standard tasks -> Claude Sonnet 4.5 (~15%) for reasoning -> Claude Opus 4.6 (~5%) for client-facing quality
- [x] **MODL-02**: Kimi and Gemini available as additional model options for specific task types
- [x] **MODL-03**: Automatic fallback chain -- if a tier fails, escalate to next tier with error handling
- [x] **MODL-04**: Prompt caching enabled for system prompts -- 60-90% input token cost reduction

### Per-Task RAG

- [ ] **PRAG-01**: Separate Qdrant collection per task type (email-triage, proposal-gen, form-gen, lead-enrich, check-in, etc.)
- [ ] **PRAG-02**: Every task execution indexes its outcome -- errors, token usage, successful patterns, operator corrections
- [ ] **PRAG-03**: Before executing a repeated task, agent queries its task-specific RAG for past mistakes and successful approaches
- [ ] **PRAG-04**: RAG write gates -- outcomes enter as `pending` status, graduate to `confirmed` only after operator validation or 7-day no-complaint window
- [ ] **PRAG-05**: Client knowledge indexed and retrievable across all workflows -- past interactions, preferences, project history

### OCR Screen Watching

- [ ] **OCRW-01**: Windows Python daemon captures screen every 30 seconds via mss, OCR processes via Tesseract
- [ ] **OCRW-02**: Captured text stored in Supabase with pgvector embeddings for semantic search
- [ ] **OCRW-03**: Sensitive content classifier filters out password managers, banking, and personal apps before any capture reaches agent
- [ ] **OCRW-04**: Agent can answer "what was I working on for [client]?" by querying screen history
- [ ] **OCRW-05**: Screen context enriches proactive check-ins -- agent knows current work context when sending messages

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Self-Evolution

- **SEVL-01**: Weekly Evolve Agent evaluates prompt performance across all skills using accumulated metrics
- **SEVL-02**: Agent proposes prompt rewrites with A/B testing -- 48-hour monitoring with auto-rollback on regression
- **SEVL-03**: Skill auto-generation from gap detection -- intent clustering on `missing_capability` events -> LLM generates YAML + implementation
- **SEVL-04**: Git-tracked prompt versions in `~/.openclaw/` for rollback safety

### Lead Pipeline

- **LEAD-01**: Clay.com waterfall enrichment via n8n proxy
- **LEAD-02**: Lead scoring logic migrated from existing n8n workflows
- **LEAD-03**: Qualified leads auto-pushed to GHL with sequence trigger
- **LEAD-04**: End-to-end: trigger -> enrich -> score -> CRM push -> outreach sequence -> log

### Advanced Features

- **ADVN-01**: Screen-to-todo task detection -- agent offers to take over work detected via OCR
- **ADVN-02**: Autonomous email sending for pre-approved templates (post 90-day HITL period)
- **ADVN-03**: WhatsApp channel integration

## Out of Scope

| Feature | Reason |
|---------|--------|
| Autonomous email sending without HITL | Meta email deletion incident; external messages are permanent and reputation-affecting |
| Auto-installing ClawHub skills | 17% malicious rate; whitelist-only with manual code review |
| Real-time voice interaction | Agent on Mac Mini, operator on Windows; text channels are more appropriate |
| Client-facing chatbot | Operator is the client relationship; agent handles internal ops only |
| Mobile app | Telegram covers mobile use case; web UI via Tailscale covers dashboard |
| Custom LLM fine-tuning | Per-task RAG achieves similar accuracy at fraction of cost/complexity |
| Publicly exposed web UI | 135K+ instances exposed with defaults; Tailscale VPN mandatory |
| Slack/Discord as primary channel | Telegram is chosen, hardened, documented; optional passive broadcast only |
| Automatic proposal delivery | Proposals represent agency reputation; always HITL Tier 1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-03 | Phase 1 | Complete |
| INFR-04 | Phase 1 | Complete |
| INFR-05 | Phase 1 | Complete |
| SECR-01 | Phase 1 | Complete |
| SECR-02 | Phase 1, Phase 3 | Partial -- Phase 1 delivers tier classification and enforcement (classify.ts, enforce.ts, 28 tests). Phase 3 delivers Telegram approval channel for YELLOW escalation. |
| SECR-03 | Phase 1 | Complete |
| SECR-04 | Phase 1 | Complete |
| SECR-05 | Phase 1 | Complete |
| SECR-06 | Phase 1 | Complete |
| SECR-07 | Phase 1 | Complete |
| MEMR-01 | Phase 2 | Complete |
| MEMR-02 | Phase 2 | Complete |
| MEMR-03 | Phase 2 | Complete |
| MEMR-04 | Phase 2 | Complete |
| MEMR-05 | Phase 2 | Complete |
| COMM-01 | Phase 3 | Pending |
| COMM-02 | Phase 3 | Pending |
| COMM-03 | Phase 3 | Pending |
| COMM-04 | Phase 3 | Pending |
| COMM-05 | Phase 4 | Pending |
| COMM-06 | Phase 4 | Pending |
| COMM-07 | Phase 3 | Pending |
| COMM-08 | Phase 3 | Pending |
| TASK-01 | Phase 4 | Pending |
| TASK-02 | Phase 4 | Pending |
| TASK-03 | Phase 4 | Pending |
| TASK-04 | Phase 4 | Pending |
| TASK-05 | Phase 4 | Pending |
| TASK-06 | Phase 4 | Pending |
| PROP-01 | Phase 5 | Pending |
| PROP-02 | Phase 5 | Pending |
| PROP-03 | Phase 5 | Pending |
| PROP-04 | Phase 5 | Pending |
| PROP-05 | Phase 5 | Pending |
| PROP-06 | Phase 5 | Pending |
| MODL-01 | Phase 2 | Complete |
| MODL-02 | Phase 2 | Complete |
| MODL-03 | Phase 2 | Complete |
| MODL-04 | Phase 2 | Complete |
| PRAG-01 | Phase 6 | Pending |
| PRAG-02 | Phase 6 | Pending |
| PRAG-03 | Phase 6 | Pending |
| PRAG-04 | Phase 6 | Pending |
| PRAG-05 | Phase 6 | Pending |
| OCRW-01 | Phase 7 | Pending |
| OCRW-02 | Phase 7 | Pending |
| OCRW-03 | Phase 7 | Pending |
| OCRW-04 | Phase 7 | Pending |
| OCRW-05 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 51 total
- Mapped to phases: 51
- Unmapped: 0

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after roadmap creation*

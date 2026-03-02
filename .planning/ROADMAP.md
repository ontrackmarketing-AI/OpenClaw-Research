# Roadmap: OpenClaw

## Overview

OpenClaw delivers an always-on AI agent that progressively takes over the operator's repetitive work -- email, proposals, todos, lead processing, and meeting follow-ups. The build order is dependency-driven: secure infrastructure first, then memory and model routing, then the Telegram command channel that gates all subsequent workflows, then the operator-facing features (email/task management, proposals, learning, and screen watching) in order of daily value delivered.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Secure Infrastructure** - Docker stack, security hardening, n8n proxy, HITL policy, cost circuit breakers, and Tailscale VPN
- [x] **Phase 2: Memory and Model Routing** - Three-tier memory system, hybrid search, daily log compaction, and 4-tier model routing with fallback chain
- [x] **Phase 3: Telegram Command Channel** - Telegram bot as primary interface, email triage with approve/reject, calendar event extraction, Notion task logging
- [x] **Phase 4: Task Management and Context Capture** - Centralized todo list, meeting/call transcript processing, iMessage context, proactive check-ins with adaptive timing
- [x] **Phase 5: Proposal Pipeline** - Meeting-to-proposal automation with fact extraction, discovery forms, Gamma presentation generation, and CRM-triggered decks
- [x] **Phase 6: Per-Task RAG** - Self-improvement flywheel with per-task vector collections, outcome indexing, pre-task recall, write gates, and client knowledge retrieval
- [ ] **Phase 7: OCR Screen Watching** - Windows screen capture daemon, semantic search over screen history, sensitive content filtering, and context-enriched agent awareness

## Phase Details

### Phase 1: Secure Infrastructure
**Goal**: Agent platform is running, hardened, and safe to connect to external services -- no API call can execute without passing through security controls
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-03, INFR-04, INFR-05, SECR-01, SECR-02, SECR-03, SECR-04, SECR-05, SECR-06, SECR-07
**Success Criteria** (what must be TRUE):
  1. Operator can access OpenClaw web UI and n8n dashboard via Tailscale VPN from the Windows machine -- all ports refuse connections from non-Tailscale IPs
  2. All 6 n8n proxy workflows respond to test requests -- agent process cannot read any external API key from its own environment or filesystem
  3. A simulated RED-tier action (e.g., delete request) is blocked with no approval path that bypasses HITL -- YELLOW and GREEN tiers route correctly
  4. Anthropic API calls halt when the $50/month cap or 50-tool-call session limit is reached -- circuit breaker triggers are visible in logs
  5. A 55-turn context exhaustion test confirms all pinned safety directives survive compaction -- verification loop halts the session if any directive disappears
**Plans**: 3 plans in 2 waves

Plans:
- [x] 01-01-PLAN.md -- Docker stack (PostgreSQL, Redis, Qdrant, n8n), Ollama models, Tailscale serve [Wave 1]
- [x] 01-02-PLAN.md -- n8n proxy workflows (6 proxies + sanitizer), HITL tier enforcement [Wave 2]
- [x] 01-03-PLAN.md -- Cost circuit breakers, context window safety, emergency stop [Wave 2]

### Phase 2: Memory and Model Routing
**Goal**: Agent has persistent memory with hybrid search and intelligent model selection -- every subsequent skill can store, recall, and route requests cost-effectively
**Depends on**: Phase 1
**Requirements**: MEMR-01, MEMR-02, MEMR-03, MEMR-04, MEMR-05, MODL-01, MODL-02, MODL-03, MODL-04
**Success Criteria** (what must be TRUE):
  1. Agent can write to MEMORY.md and retrieve relevant context in subsequent sessions -- memory persists across container restarts
  2. A keyword search (FTS5) and a semantic search (Qdrant) both return relevant results from stored content -- hybrid search via RRF returns better results than either alone
  3. Daily logs older than 30 days are automatically compacted into weekly summaries without manual intervention
  4. A classification task routes to Ollama qwen3:14b (free), a standard task routes to Haiku, and a reasoning task routes to Sonnet -- fallback chain engages when a tier is unavailable
  5. Prompt caching is active on system prompts -- API billing confirms reduced input token costs on repeated calls
**Plans**: 2 plans in 2 waves

Plans:
- [x] 02-01-PLAN.md -- Memory system: MEMORY.md persistent storage, daily logs, FTS5 keyword search, Qdrant vector search, hybrid RRF merge, log compaction [Wave 1]
- [x] 02-02-PLAN.md -- Model routing: 4-tier classifier (Ollama/Haiku/Sonnet/Opus), fallback chain, prompt caching, cost tracker integration [Wave 2]

### Phase 3: Telegram Command Channel
**Goal**: Operator can interact with the agent through Telegram for approvals, email triage, calendar awareness, and centralized task logging -- this is the agent's voice
**Depends on**: Phase 2
**Requirements**: COMM-01, COMM-02, COMM-03, COMM-04, COMM-07, COMM-08
**Success Criteria** (what must be TRUE):
  1. Operator receives a daily email triage summary in Telegram showing sender, subject, and suggested action for each actionable email
  2. Operator can tap inline approve/reject buttons on agent-proposed email actions and the agent executes or discards accordingly
  3. Agent proposes calendar events extracted from emails -- operator confirms via Telegram and the event appears in Google Calendar
  4. Agent defers non-urgent notifications when Google Calendar shows the operator is in a meeting
  5. All agent-captured actions and items are logged to Notion and visible in a single centralized view
**Plans**: 3 plans in 3 waves

Plans:
- [x] 03-01-PLAN.md -- Telegram bot with grammY (commands, user whitelist, MarkdownV2 formatters) and HITL approval queue (SQLite-backed, YELLOW-tier async approval via inline buttons) [Wave 1]
- [x] 03-02-PLAN.md -- Gmail OAuth2 client, email triage engine with LLM classification (Haiku tier), calendar event extraction, periodic polling with historyId, /triage command [Wave 2]
- [x] 03-03-PLAN.md -- Google Calendar event insertion with Telegram confirmation, calendar-aware message deferral (freebusy.query), Notion action log database integration [Wave 3]

### Phase 4: Task Management and Context Capture
**Goal**: Operator has a single, automatically populated todo list enriched by meetings, calls, iMessage, and adaptive check-ins -- nothing falls through the cracks
**Depends on**: Phase 3
**Requirements**: TASK-01, TASK-02, TASK-03, TASK-04, TASK-05, TASK-06, COMM-05, COMM-06
**Success Criteria** (what must be TRUE):
  1. Todo list in Notion is automatically populated from email, meeting transcripts, call transcripts, and iMessage -- operator sees items appear without manual entry
  2. Fellow meeting transcripts are pulled and processed -- decisions, action items, and open questions appear as structured Notion entries
  3. Apple Notes call transcripts are pulled and processed with the same extraction quality as Fellow
  4. Operator receives 3-5 proactive check-ins per day via Telegram -- morning priorities, midday status, evening wrap-up -- with no repeated template within 3 days
  5. Check-in timing adapts over 14 days based on which time slots get operator responses -- low-engagement slots are dropped automatically
**Plans**: 3 plans in 2 waves

Plans:
- [x] 04-01-PLAN.md -- Notion todo database, central aggregator with dedup, transcript extraction pipeline (Fellow REST + Apple Notes AppleScript), email-to-todo wiring [Wave 1]
- [x] 04-02-PLAN.md -- BlueBubbles REST client with abstraction layer, privacy-preserving iMessage poller, context extraction for todo enrichment and check-in awareness [Wave 2]
- [x] 04-03-PLAN.md -- Proactive check-in engine with 5 daily slots, adaptive timing (14-day engagement tracking), anti-repetition templates, parallel context assembly, LLM personalization, Telegram delivery with response buttons [Wave 2]

### Phase 5: Proposal Pipeline
**Goal**: Agent automates the meeting-to-proposal workflow -- from transcript analysis through discovery form to Gamma presentation -- with HITL gates at every external touchpoint
**Depends on**: Phase 4
**Requirements**: PROP-01, PROP-02, PROP-03, PROP-04, PROP-05, PROP-06
**Success Criteria** (what must be TRUE):
  1. Agent produces a slide outline from a meeting recording using Claude analysis -- outline includes key pain points, proposed services, and pricing structure
  2. Agent generates a discovery form from meeting context and the operator can send it to the prospect for deeper information gathering
  3. After discovery form responses come back, agent generates a Gamma presentation using the saved theme -- presentation is viewable via preview link
  4. Operator reviews every proposal via Telegram preview link before any delivery -- no proposal reaches a prospect without explicit HITL approval
  5. Moving a lead to "qualified" in GHL automatically triggers a tailored pitch deck draft that includes industry-specific context from client knowledge RAG
**Plans**: 2 plans in 2 waves

Plans:
- [ ] 05-01-PLAN.md -- Proposal types, meeting transcript analyzer (Sonnet), discovery form generator, Gamma MCP client, content assembler, SQLite proposal state machine, pipeline orchestrator, Telegram HITL approval with Approve/Edit/Reject buttons, /proposal command [Wave 1]
- [ ] 05-02-PLAN.md -- CRM-triggered pitch decks via GHL OpportunityStageUpdate webhook (n8n relay), industry context retrieval from hybrid search with hardcoded fallback pain points, webhook deduplication, Gamma generation with HITL approval [Wave 2]

### Phase 6: Per-Task RAG
**Goal**: Agent gets measurably better at each task over time -- every execution produces indexed learning data that improves the next execution of the same task type
**Depends on**: Phase 2, Phase 3 (skills must be running to generate data)
**Requirements**: PRAG-01, PRAG-02, PRAG-03, PRAG-04, PRAG-05
**Success Criteria** (what must be TRUE):
  1. Each task type (email-triage, proposal-gen, form-gen, lead-enrich, check-in) has its own isolated Qdrant collection -- collections are queryable independently
  2. Every skill execution automatically indexes its outcome -- errors, token usage, patterns, and operator corrections are stored
  3. Before executing a repeated task, agent retrieves and applies relevant past outcomes -- observable as different behavior on second execution vs. first
  4. New RAG entries start as "pending" and graduate to "confirmed" only after operator validation or a 7-day no-complaint window
  5. Client knowledge (past interactions, preferences, project history) is retrievable across all workflows -- asking "what do we know about [client]?" returns comprehensive context
**Plans**: 2 plans in 2 waves

Plans:
- [ ] 06-01-PLAN.md -- Per-task Qdrant collection manager (5 task-type collections with payload indexes), outcome indexer with dedup and shouldIndex filter, write gate lifecycle (pending->confirmed promotion cron at 2 AM, operator Telegram validation, quality gate for auto-promotion) [Wave 1]
- [ ] 06-02-PLAN.md -- Pre-task recall (query past outcomes, weight confirmed 2x, format lessons, inject after cache breakpoint), client knowledge collection (cross-workflow indexing with contact_id dedup, semantic and direct queries) [Wave 2]

### Phase 7: OCR Screen Watching
**Goal**: Agent can see what the operator is working on via Windows screen capture and uses that context to provide proactive, relevant assistance
**Depends on**: Phase 3 (Telegram for pause command), Phase 4 (check-ins to enrich)
**Requirements**: OCRW-01, OCRW-02, OCRW-03, OCRW-04, OCRW-05
**Success Criteria** (what must be TRUE):
  1. Windows Python daemon captures the screen every 30 seconds and OCR-processed text is stored in Supabase with pgvector embeddings
  2. Sensitive content (password managers, banking, personal apps) is filtered out before any capture reaches the agent or is stored
  3. Operator can ask "what was I working on for [client]?" and get an accurate summary drawn from screen capture history
  4. Proactive check-ins reference current screen context -- agent knows the operator is in GHL vs. writing an email vs. browsing
  5. Operator can pause and resume OCR capture at any time via a Telegram command
**Plans**: TBD

Plans:
- [ ] 07-01: Windows capture daemon and sensitive content filter
- [ ] 07-02: Screen history search and context-enriched check-ins

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Secure Infrastructure | 3/3 | Complete | 2026-02-28 |
| 2. Memory and Model Routing | 2/2 | Complete | 2026-03-01 |
| 3. Telegram Command Channel | 3/3 | Complete | 2026-03-01 |
| 4. Task Management and Context Capture | 3/3 | Complete | 2026-03-02 |
| 5. Proposal Pipeline | 0/2 | Not started | - |
| 6. Per-Task RAG | 0/2 | Not started | - |
| 7. OCR Screen Watching | 0/2 | Not started | - |

# Project Research Summary

**Project:** OpenClaw Operator Automation Layer — OnTrack Marketing AI Agent
**Domain:** Autonomous AI marketing assistant for solo operator (brownfield, always-on, two-machine)
**Researched:** 2026-02-28
**Confidence:** HIGH (platform design, stack, features, pitfalls all verified; MEDIUM on Gamma MCP availability and sqlite-vec stability)

## Executive Summary

OpenClaw is an existing agent runtime platform that needs an operator automation layer built on top of it — not a new AI product from scratch. The stack is largely pre-decided: OpenClaw on Node.js 22, Docker Compose with PostgreSQL 16 / Redis 7 / Qdrant / n8n, and Ollama for local inference using qwen3:14b and nomic-embed-text v1.5. The operator automation layer adds specific workflow skills (email triage, iMessage management, OCR screen watching, document generation, per-task RAG) via Python services and OpenClaw skills authored in TypeScript. The critical architectural insight is that the agent machine (Mac Mini M4 Pro) and the work machine (Windows desktop) are physically separate, which forces all cross-machine visibility through cloud APIs, OCR relay pipelines, and Tailscale VPN — there is no shared filesystem.

The recommended build order is dependency-driven and non-negotiable: infrastructure and security hardening must precede any external API integrations, which must precede automation skills, which must precede learning systems (per-task RAG) and advanced intelligence (self-evolution). The n8n security proxy pattern — where the agent never holds external API keys and all writes flow through n8n — is a hard design invariant that cannot be relaxed. HITL approval via Telegram is similarly non-negotiable for the first 90 days and must be treated as a safety primitive, not a UX nicety. Skipping or weakening either of these creates documented, high-severity failure modes.

The highest-severity risk is context window compaction silently dropping safety directives, which caused the documented Meta email deletion incident (200+ emails deleted autonomously). The second highest is indirect prompt injection via email or document content — OWASP's #1 LLM vulnerability, present in 73% of assessed production systems. Both risks have concrete mitigations (pinned directives with verification loops; content-wrapper trust boundaries) that must be implemented in Phase 2 before any external content reaches the agent. Proposals, email sends, and all external writes to clients must remain RED-tier HITL permanently through the supervised period, with no exceptions.

## Key Findings

### Recommended Stack

The operator automation layer is built in two languages: TypeScript for OpenClaw skills (compiled in the OpenClaw pnpm workspace, tested with Vitest) and Python for automation services (email OAuth, OCR, Telegram HITL, FastAPI endpoints). The core infrastructure is Docker-compose-based and already specified in the PRD — the only open decisions are the Python library selections for each workflow domain.

All Python library versions are verified against PyPI as of 2026-02-28. The OCR stack (ocrmac 1.0.1 + mss 10.1.0) is macOS-specific and correct for the M4 Pro hardware — pytesseract is explicitly ruled out due to CPU-only operation and 80% accuracy on native UI. BlueBubbles is the only viable iMessage integration in 2026 but carries an active risk flag: Apple has announced termination of private iMessage API support in June 2026. The Gamma MCP is real but access-gated; a manual fallback workflow must be planned from day one.

**Core technologies:**
- **OpenClaw v2026.2.25+**: Agent runtime (skills, channels, MCP, memory) — mandatory minimum version patches CVE-2026-27001
- **Node.js 22 / TypeScript**: OpenClaw skill language — required by OpenClaw's Vitest vmForks infrastructure
- **Docker Compose (Postgres 16 / Redis 7 / Qdrant / n8n / Ollama)**: Container stack — pre-decided in PRD; Ollama handles free local inference (qwen3:14b 40K ctx, nomic-embed-text 768-dim)
- **FastAPI 0.134.0 + uvicorn**: Internal service layer for OCR relay endpoint and n8n webhook callbacks — async is required
- **google-api-python-client 2.190.0**: Gmail access via OAuth 2.0 desktop flow — official SDK, no unofficial wrappers
- **BlueBubbles + httpx 0.28.1**: iMessage REST API — only viable option; monitor for June 2026 Apple deprecation
- **ocrmac 1.0.1 + mss 10.1.0**: macOS OCR via Apple Vision Framework — Neural Engine acceleration on M4 Pro; Apple Vision quality vastly exceeds pytesseract on native UI
- **python-telegram-bot 22.6**: Async Telegram Bot for HITL — inline keyboards, approval callbacks, quiet hours
- **anthropic 0.84.0**: Claude API with prompt caching GA — 4-tier model routing (Ollama free / Haiku / Sonnet / Opus)
- **notion-client 3.0.0**: Official Notion SDK for todo management — use async client
- **qdrant-client 1.17.0**: Per-task RAG vector stores — isolated collections per task type
- **Tailscale**: VPN mesh for all agent-machine access — mandatory; no public exposure

**See STACK.md for full library list, version compatibility matrix, and alternatives considered.**

### Expected Features

The agent must feel like a genuine always-on assistant, not a prompted tool. The table-stakes features are the daily workflows the operator currently does manually. Differentiators are where OpenClaw beats every SaaS alternative — specifically cross-machine context (screen + iMessage), end-to-end pipeline automation, and the self-improvement flywheel. Several commonly-requested features (autonomous email sending, auto-installing community skills, voice interaction) are explicitly anti-features for this deployment and must be deferred or excluded.

**Must have (table stakes — launch blockers):**
- Email triage and summarization — agent is useless without this; covers 60%+ of daily work context
- Lead pipeline end-to-end — the revenue-generating workflow; validates core infrastructure
- Telegram HITL with tiered approval — non-negotiable safety primitive before any autonomous writes
- Meeting transcript processing (Fellow + Apple Notes) — removes 20-30 min of manual post-meeting work
- Todo list population from multiple sources (Notion as destination) — the "capture everything once" expectation
- Proactive check-ins (3 daily, time-of-day + memory-based) — establishes the always-on relationship
- Cost circuit breakers ($50/mo Anthropic cap, 50 tool calls/session, 30-min timeout) — must precede any autonomous execution

**Should have (v1.x — add after validation):**
- Gamma proposal pipeline — Fellow transcript to Gamma deck; highest business value per hour saved
- iMessage context awareness — makes check-ins contextually relevant instead of generic
- Google Calendar awareness — prevents mis-timed notifications and check-ins
- Per-task RAG — start indexing immediately after launch so the flywheel begins accumulating data
- 4-tier model routing — engage when Anthropic costs approach $30/month

**Defer to v2+ (requires 90-day supervised period first):**
- OCR screen database (Windows capture + searchable history) — high privacy surface; validate iMessage integration first
- Proactive task detection from screen — requires mature OCR database
- Self-evolution (prompt optimization) — requires 60+ days of stable instrumented execution data across all core skills
- Skill auto-generation — depends on self-evolution infrastructure

**Anti-features (do not build):**
- Autonomous email sends without HITL — documented as catastrophic failure mode
- Auto-installing ClawHub community skills — 17% flagged malicious
- Real-time voice interaction — inappropriate for always-on Mac Mini context
- Client-facing chatbot — operator must remain the client relationship owner
- Publicly exposed web UI — actively exploited attack pattern across OpenClaw deployments

**See FEATURES.md for full prioritization matrix, dependency graph, and competitor comparison.**

### Architecture Approach

The system is a two-machine, five-layer architecture where the Mac Mini M4 Pro is the agent brain and the Windows desktop is the work surface. The OpenClaw Gateway sits at the center of all coordination. n8n is the security proxy mediating all external writes — it is a dumb credential holder, not an intelligence layer. Memory is three-tiered: MEMORY.md hot context (always in context window), SQLite FTS5 + sqlite-vec for cold keyword search, and per-task Qdrant collections for task-specific vector recall. The Windows-to-Mac-Mini cross-machine bridge is OCR + cloud APIs only — no direct filesystem access.

**Major components:**
1. **OpenClaw Gateway (Port 18789)** — Central message bus, session management, agent routing, tool dispatch; all agents communicate through this
2. **n8n Security Proxy (Port 5678)** — Mediates every external write; agent sends structured instructions, n8n injects credentials; agent never sees keys
3. **Specialized Agent Pool** — Triage Agent, Proposal Agent, Screen Watcher Agent, Check-in Agent, Evolve Agent; each with a specific YAML definition and focused responsibility
4. **Memory System** — Three-tier: MEMORY.md (hot, 4K token limit), SQLite index.db (FTS5 + sqlite-vec), per-task Qdrant collections (isolated by task type)
5. **Windows Capture Service** — Lightweight Python daemon (mss + ocrmac → local SQLite → Supabase batch sync); the only cross-machine visibility mechanism
6. **Model Router** — 4-tier routing (Ollama → Haiku → Sonnet → Opus); tracks cost against $50/mo cap; enforces circuit breakers

The most important patterns: per-task RAG isolation (separate Qdrant collections per task type — never a single global knowledge base), n8n proxy for all writes (never direct), parallel async context assembly for check-ins (asyncio.gather, not sequential blocking), and HITL as a state machine with async queue (never synchronous in the request path).

**See ARCHITECTURE.md for build order dependency graph, all data flows, anti-patterns, and integration boundary table.**

### Critical Pitfalls

Six documented critical pitfalls with verified sources — each has a concrete prevention strategy and a specific phase where it must be addressed.

1. **Context compaction silently drops safety directives** — Embed safety directives at TOP of every system prompt inside `[PINNED — DO NOT SUMMARIZE]` markers; add a verification loop that halts the session if any pinned directive disappears. Test with a 55-turn deliberate context exhaustion test before production cutover. (Phase 2 + Phase 7 gate)

2. **Indirect prompt injection via email, transcripts, and OCR captures** — All external content enters the agent's context inside typed XML wrappers (`<email_content>`, `<ocr_capture>`, etc.); the pinned system prompt explicitly classifies these zones as data-not-instructions; n8n strips common injection patterns before content reaches OpenClaw. (Phase 2; never relax)

3. **Per-task RAG feedback loop poisoning** — Never write a task outcome to the RAG database without an outcome verification gate (operator-approved for proposals; GHL record created for enrichment). Tag patterns as `pending` / `confirmed` / `rejected`; retrieval weights accordingly. Separate error patterns from success patterns in different collections. (Phase 3 design must include the gate)

4. **Sending to wrong email/iMessage recipient** — Contact disambiguation is mandatory before any send: if more than one GHL contact matches, halt and ask. Display full recipient address (not just name) in every HITL notification. HITL timeout behavior is auto-reject, never auto-approve. (Phase 5 GHL wrapper + Phase 6 HITL UI)

5. **Proposal automation hallucinating client data** — Extract facts with a confidence level (`confirmed` / `inferred` / `unknown`) before Gamma rendering. Insert `[CONFIRM: X]` placeholders for any `unknown` fact; populate via discovery form. Never generate the Gamma deck until all gaps are filled. HITL review before rendering (not after). (Phase 5 pipeline design + Phase 7 gap-filling test)

6. **OCR capturing sensitive content into agent context** — Run every OCR capture through a pre-processing classifier (work-relevant / sensitive-block / ignore) using local Ollama before it reaches the agent. OCR data is session-scoped only — never persist to MEMORY.md, SQLite, or Qdrant. Build "pause OCR" command into Telegram interface from first deployment. (Phase 5; never deploy OCR without the filter)

**See PITFALLS.md for recovery strategies, technical debt patterns, integration gotchas, and "looks done but isn't" verification checklist.**

## Implications for Roadmap

Research across all four files produces a clear, dependency-driven phase sequence. The existing 13-phase roadmap in `11-Implementation-Roadmap/` is structurally sound. The additions from this research are primarily the explicit safety gates between phases and the identification of which phases need deeper research before planning.

### Phase 1: Infrastructure Foundation
**Rationale:** Every component depends on the Docker stack, Ollama, and Tailscale. Nothing runs without this. Cost circuit breakers belong here — they must exist before any agent runs, even in testing.
**Delivers:** OpenClaw + Postgres + Redis + Qdrant + n8n + Ollama running; Tailscale VPN; Anthropic spend limit and 50-tool-call/30-min circuit breakers configured; qwen3:14b and nomic-embed-text pulled.
**Stack:** Docker Compose stack from STACK.md; Tailscale; Ollama models.
**Avoids:** Runaway API cost loop (circuit breakers must precede everything).

### Phase 2: Security Hardening
**Rationale:** n8n security proxy and HITL safety infrastructure are prerequisites for all external integrations. Pinned directive configuration and content sanitization belong here — they cannot be retrofitted after the agent has processed real email.
**Delivers:** n8n proxy workflows for all 6 write domains (GHL, Clay, Gmail send, social, Airtable write, Supabase write); container hardening (non-root, read-only FS); pinned safety directives with verification loop; n8n content sanitization pipeline; HITL approval policy YAML (RED/YELLOW/GREEN tiers).
**Stack:** n8n, Docker hardening, approval-policy.yaml.
**Avoids:** Pitfalls 1 (context compaction) and 2 (prompt injection) — both must be configured here before any external content is processed.

### Phase 3: Memory System
**Rationale:** Per-task RAG, proactive check-ins, and self-evolution all require stable memory before they deliver value. The RAG database write gates (outcome verification, confidence scoring, pattern separation) must be designed here — they cannot be added after bad patterns have already been indexed.
**Delivers:** MEMORY.md + daily log structure; SQLite FTS5 + sqlite-vec hybrid search; memory compaction schedule; per-task Qdrant collections schema (email-triage, proposal-gen, lead-enrichment, crm-management); outcome verification gate and confidence tagging in the RAG write path.
**Stack:** qdrant-client 1.17.0; sqlite-vec; nomic-embed-text for embedding generation.
**Avoids:** Pitfall 3 (RAG poisoning feedback loop) — the write gate must be built here.

### Phase 4: Core Skills and Integrations
**Rationale:** GHL, Airtable, and Clay are the revenue-critical integrations. All downstream automation depends on them. The Clay connector via n8n proxy is the primary gap from the current state.
**Delivers:** GHL MCP connected (reads direct, writes via n8n proxy); Airtable MCP confirmed operational; Clay REST adapter via n8n proxy with $100/mo cap enforcement; 6 existing skills migrated to OpenClaw skill format.
**Stack:** Existing TypeScript GHL MCP; airtable-mcp-server npm 1.9.6; Clay n8n pattern from STACK.md.
**Avoids:** Agent holding external API keys (n8n proxy required for all Clay and GHL writes).

### Phase 5: Notification Channel (Telegram HITL)
**Rationale:** Every HITL-gated workflow depends on Telegram. Must be functional before email triage or proposal pipeline is enabled. Inline buttons, quiet hours, and the async state machine for approvals are all required here.
**Delivers:** Telegram bot with inline approve/reject buttons; tiered HITL state machine (async queue, never synchronous in request path); quiet hours; calendar-aware deferral; full recipient display in all approval notifications; HITL timeout set to auto-reject.
**Stack:** python-telegram-bot 22.6.
**Avoids:** Pitfall 4 (wrong recipient sends) — full recipient display in notifications; auto-reject timeout behavior required here.

### Phase 6: Email and Calendar Triage
**Rationale:** Email triage is the highest-value daily workflow and validates the full integration stack (Gmail OAuth, n8n proxy, Notion todo write, Telegram HITL, memory). Calendar awareness prevents mis-timed interventions and is low complexity.
**Delivers:** Gmail OAuth integration; email triage agent (classify → extract action items → Notion todo); Google Calendar MCP for meeting detection; email send blocked at RED-tier HITL permanently; contact disambiguation in GHL wrapper before any send is possible.
**Stack:** google-api-python-client 2.190.0; google-auth-oauthlib; notion-client 3.0.0.
**Avoids:** Pitfall 4 (contact disambiguation gate before any send action).

### Phase 7: Proposal Pipeline
**Rationale:** Meeting-to-proposal is the highest per-hour business value workflow. Depends on Fellow/Apple Notes, Gamma MCP, GHL for delivery, and Telegram for approval. Gamma MCP access must be confirmed or fallback designed.
**Delivers:** Fellow API adapter (or Zapier fallback); Apple Notes MCP for transcript ingestion; fact extraction with confidence step (confirmed/inferred/unknown); discovery form generation with gap-filling via form; Gamma MCP integration with saved theme; HITL gate before Gamma rendering and before delivery; proposal PDF export via GHL email through n8n proxy.
**Stack:** gamma-mcp-server (official); httpx 0.28.1 for Fellow API; Apple Notes MCP.
**Avoids:** Pitfall 5 (hallucinated proposal data) — fact confidence step and discovery form are mandatory before any Gamma call.
**Research flag:** Gamma MCP access is gated; confirm API access or design fallback before planning this phase.

### Phase 8: iMessage Triage
**Rationale:** iMessage context enriches check-ins and captures client conversation threads. Depends on Physical Mac Mini access for Full Disk Access permission setup. BlueBubbles + macOS Tahoe 26 compatibility must be confirmed.
**Delivers:** BlueBubbles server configured on Mac Mini; iMessage relay via httpx; read-only triage agent; contact scope limited to business contacts (not personal); iMessage sends permanently RED-tier HITL.
**Stack:** BlueBubbles + httpx 0.28.1.
**Avoids:** Pitfall 2 (wrong iMessage recipient — personal vs. business contacts must be scoped); monitor BlueBubbles releases for June 2026 Apple API deprecation.

### Phase 9: Proactive Check-ins
**Rationale:** Check-ins establish the always-on relationship with the operator. Require memory (Phase 3) and Telegram (Phase 5) and Calendar (Phase 6). Start with time-of-day + memory context; screen data enhances later.
**Delivers:** Check-in engine with LaunchAgent cron (5 daily slots); template pool with anti-repetition logic (no repeat in 3 days, track last 10); calendar-aware deferral (skip if meeting in next 5 minutes); adaptive timing model (drop slots with <30% response rate after 14 days); Notion MCP integration for open todo context.
**Stack:** python-telegram-bot 22.6; Google Calendar MCP; notion-client 3.0.0.

### Phase 10: OCR Screen Watcher
**Rationale:** Cross-machine visibility is the unique differentiator for proactive task detection. High complexity and high privacy surface — defer until iMessage integration is proven and operator is comfortable with cross-machine data capture. Supabase must be active and paid tier ($25/mo).
**Delivers:** Windows capture daemon (mss + pytesseract → local SQLite → Supabase batch push); sensitive-content pre-processing classifier (Ollama) before any capture reaches the agent; "pause OCR" Telegram command; screen watcher agent on Mac Mini querying Supabase; OCR data session-scoped only (never persisted to MEMORY.md or Qdrant).
**Stack:** mss 10.1.0 (Windows daemon); ocrmac 1.0.1 (Mac Mini); Supabase; FastAPI endpoint for capture relay.
**Avoids:** Pitfall 6 (OCR sensitive content) — classifier must be deployed before first real capture.
**Research flag:** Supabase tier and pricing need confirmation; Windows-side OCR dependency chain needs validation before planning.

### Phase 11: Per-Task RAG (Learning Flywheel)
**Rationale:** Start indexing as early as possible so the flywheel accumulates data. Depends on Phase 3 (memory) and Phase 4+ (skills running). The write gates designed in Phase 3 apply here.
**Delivers:** Outcome indexing on every skill execution (email-triage, proposal-gen, lead-enrichment, crm-management collections); pre-task recall injection into agent context; monthly RAG audit workflow; 90-day staleness archival policy.
**Stack:** qdrant-client 1.17.0; per-task collection schema from Phase 3.

### Phase 12: Self-Evolution
**Rationale:** Requires all prior phases generating stable, instrumented metrics. 90-day HITL period must be complete before enabling prompt self-rewriting. One bad prompt rewrite could silently degrade all skills.
**Delivers:** evolution_metrics table in Supabase; weekly Evolve Agent (Sunday 3AM trigger); prompt version control (Git branching in ~/.openclaw/); auto-rollback mechanism (48h measurement + regression detection); operator-approved prompt merge workflow; Git version control for ~/.openclaw/ (required for safe rollback).
**Stack:** anthropic 0.84.0 (Sonnet for evaluation); Supabase; Git.
**Avoids:** Pitfall 3 (RAG poisoning applies equally to prompt evolution — constitutional review layer is mandatory).

### Phase Ordering Rationale

- **Infrastructure before security before integrations:** The n8n proxy and HITL infrastructure must exist before any external API call is made. There is no safe shortcut here — the pitfalls are documented and severe.
- **Memory before RAG before self-evolution:** The learning flywheel requires a correctly-designed write gate. Getting the gate wrong and then adding more data is worse than starting later with a correct gate.
- **HITL before email/iMessage before proposals:** Every external communication channel must have HITL in place before the skill that uses it. Building skills without their safety infrastructure is the pattern that produced every documented AI agent incident.
- **Core skills before enriched context:** Email triage and the lead pipeline deliver immediate daily value. Screen watching and advanced check-ins are enhancers, not foundations.
- **Self-evolution last, deliberately:** The system needs 90+ days of stable operation before it can safely evaluate and modify its own behavior. Deploying this early would introduce noise before the signal is established.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 7 (Proposal Pipeline):** Gamma MCP API access is gated — must confirm access before planning. Fellow API requires admin toggle; confirm availability. If either is unavailable, fallback workflows must be designed.
- **Phase 8 (iMessage):** BlueBubbles macOS Tahoe 26 compatibility has known issues (Edit broken, group icon sync unreliable). June 2026 Apple API deprecation timeline creates a hard deadline for this phase. Validate BlueBubbles release cadence before committing.
- **Phase 10 (OCR Screen Watcher):** Windows-side capture toolchain needs validation in context of the specific Windows environment. Supabase Pro tier cost and data retention limits need confirmation. Two-machine networking for OCR relay needs proof-of-concept before planning.

**Phases with well-documented patterns (skip research-phase):**
- **Phase 1 (Infrastructure):** Docker stack is fully specified in PRD. All versions confirmed.
- **Phase 2 (Security):** n8n proxy pattern is fully designed; HITL policy is documented. Standard implementation.
- **Phase 3 (Memory):** Memory architecture is extensively documented in 04-Memory-and-RAG/. Design is complete.
- **Phase 5 (Telegram HITL):** python-telegram-bot patterns are standard and well-documented. Straightforward implementation.
- **Phase 6 (Email/Calendar):** Gmail OAuth + Google Calendar MCP are standard patterns. Well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Core Python libraries all verified against PyPI 2026-02-28. Platform decisions are pre-made in PRD. Only MEDIUM areas: Gamma MCP access (gated, not broadly available), sqlite-vec (breaking changes expected). |
| Features | HIGH | Operator requirements are fully documented in 175+ research files, PRD, and GAP-ANALYSIS.md. Feature priorities are grounded in specific workflows, not speculation. |
| Architecture | HIGH | Architecture is drawn entirely from authored design specs (openclaw-architecture.md, memory-architecture.md, evolution-architecture.md, visibility-strategy.md). Not inferred — designed. |
| Pitfalls | HIGH | All critical pitfalls have verified sources: Meta email incident (documented), prompt injection (OWASP 2025, Lakera), RAG poisoning (USENIX Security 2025), cost loops ($47K incident documented). |

**Overall confidence:** HIGH

### Gaps to Address

- **Gamma MCP access:** Must request access via Gamma's API Slack channel before Phase 7. If denied, fallback workflow (manual Gamma + Telegram "propose outline" notification) must be designed into Phase 7 planning.
- **BlueBubbles June 2026 Apple deprecation:** Monitor BlueBubbles releases after May 2026. Phase 8 must be completed before June or have a contingency alternative ready (imsg-plus lacks webhooks; no other option is currently viable).
- **sqlite-vec stability:** Used in Phase 3 for in-process local queries. If breaking changes cause issues, fall back to Qdrant as the sole vector store and skip sqlite-vec entirely — Qdrant is the authoritative store regardless.
- **Supabase status:** Project ID jitawzicdwgbhatvjblh is paused (per MEMORY.md). Phase 10 (OCR screen database) and Phase 12 (self-evolution metrics) both depend on Supabase being active and on the Pro tier. Confirm status and cost before committing to those phases.
- **Fellow API admin toggle:** Fellow requires workspace admin to enable Developer API. Confirm access level before Phase 7 planning.
- **nomic-embed-text context window:** Ollama documentation says 2K context; HuggingFace confirms 8192 actual input window. Treat 8192 as the functional limit but validate this in Phase 3 testing before relying on it for long document embeddings.

## Sources

### Primary (HIGH confidence — official docs, verified PyPI, authored design specs)
- PyPI verified packages (2026-02-28): anthropic 0.84.0, google-api-python-client 2.190.0, notion-client 3.0.0, python-telegram-bot 22.6, qdrant-client 1.17.0, httpx 0.28.1, fastapi 0.134.0, ocrmac 1.0.1, mss 10.1.0
- OpenClaw AGENTS.md — Node 22+, Vitest, pnpm workspace requirements
- OpenClaw BlueBubbles docs — official channel integration docs
- Anthropic prompt caching docs — GA in anthropic 0.83.0+, cache_control syntax confirmed
- META email deletion incident — documented context compaction failure (Summer Yue)
- OWASP LLM01:2025 Prompt Injection — official classification, 73% production rate
- PoisonedRAG (USENIX Security 2025) — 97% attack success rate on RAG systems
- Authored design specs: 00-Foundation/, 04-Memory-and-RAG/, 06-Integrations/, 08-Capabilities-Deep-Dive/, 02-Security/, 12-Self-Evolution/ — full system design

### Secondary (MEDIUM confidence — community consensus, documented patterns)
- Gamma MCP server — developers.gamma.app/docs/gamma-mcp-server (official but access-gated)
- Fellow API — fellow.ai/blog/fellow-api/ (documented, requires admin toggle)
- Clay + n8n pattern — community verified pattern from intelligentresourcing.co
- sqlite-vec hybrid search — alexgarcia.xyz blog (MEDIUM — breaking changes expected)
- Apple Vision OCR PyObjC — yasoob.me (MEDIUM — community documentation)
- Ollama qwen3:14b — ollama.com/library/qwen3 (verified; Ollama doc vs HuggingFace ctx window discrepancy noted)

### Tertiary (LOW confidence — inference or single source)
- BlueBubbles June 2026 Apple API deprecation — Apple statement referenced in STACK.md; exact scope and enforcement TBD
- $47K multi-agent API cost loop — techstartups.com (single source; directionally credible)
- 47% AI hallucination decision-making stat — CIO article (single source; consistent with other research)

---
*Research completed: 2026-02-28*
*Ready for roadmap: yes*

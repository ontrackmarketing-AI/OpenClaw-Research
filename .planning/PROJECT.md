# OpenClaw

## What This Is

An always-on AI agent platform running on a dedicated Mac Mini M4 Pro (48GB RAM, 1TB SSD) that autonomously manages email, iMessage, todo lists, proposals, discovery forms, lead enrichment, and research for OnTrack Marketing — a digital marketing agency serving local service businesses (plumbing, solar, dental, legal). The agent watches the operator's Windows desktop via OCR, learns from work patterns, and progressively takes over repetitive tasks using recursive self-improvement through per-task vector storage and RAG. Built on the open-source OpenClaw platform (v2026.2.25+, 145K GitHub stars) with Docker-based deployment, n8n security proxy pattern, and a 90-day supervised HITL period.

## Core Value

The agent removes redundant tasks from the operator's day by watching, learning, and autonomously executing — getting better at each task every time it does it.

## Requirements

### Validated

<!-- Inferred from existing codebase — 175+ research docs, architecture designed, full PRD written -->

- ✓ Gateway-centric architecture with WebSocket server (port 18789) — designed
- ✓ MCP-first tool integration protocol — designed
- ✓ Plugin architecture for extensible channels, tools, memory backends — designed
- ✓ File-first memory design with hybrid search (vector + FTS5) — designed
- ✓ Multi-agent capable with inter-agent delegation (max 3 levels) — designed
- ✓ Agent configuration via YAML with skills and permissions — designed
- ✓ Session management with tiered context (pinned → recent → summarized → searchable) — designed
- ✓ Channel abstraction layer for multi-platform messaging — designed
- ✓ Full PRD with 7-phase deployment plan, security hardening, HITL tiers — written
- ✓ GoHighLevel MCP server built (TypeScript) — existing code
- ✓ Airtable MCP integration active — existing
- ✓ Next.js setup/ops dashboard (port 3000) — existing
- ✓ 6 Claude Code skills built (supabase-ops, ghl-form-connect, clay-enrichment, data-formatter, smb-local-marketing, lead-pipeline) — existing

### Active

<!-- Current scope. Building toward these. -->

**Foundation & Security (from PRD Phases 1-2):**
- [ ] Docker-based deployment — OpenClaw + PostgreSQL 16 + Redis 7 + Qdrant + n8n on openclaw-net bridge
- [ ] Security hardening — non-root containers, read-only FS, dropped capabilities, localhost-only binding
- [ ] Tailscale VPN — secure remote access with ACLs (ports 3000, 18789, 5678, 22)
- [ ] n8n security proxy — agent never holds external API keys; 6 proxy workflows for Clay, GHL, email, DataForSEO, Serper
- [ ] HITL approval system — RED/GREEN/YELLOW action tiers via Telegram notifications
- [ ] Cost circuit breakers — $50/mo Anthropic cap, 50 tool calls/session, 30-min timeout, $100/mo Clay cap
- [ ] Context window safety — pinned directives, checkpoint summarization every 20 turns, verification every 10 turns

**Memory & RAG (from PRD Phase 3 + user requirements):**
- [ ] Memory system — MEMORY.md + SQLite FTS5 + Qdrant vector (768-dim, nomic-embed-text, cosine 0.7 threshold)
- [ ] Hybrid search — vector + FTS5 merged via Reciprocal Rank Fusion (0.6/0.4 weights)
- [ ] Per-task RAG — vector storage per task type; errors, patterns, outcomes indexed for recursive improvement
- [ ] Client knowledge RAG — everything about each client stored and retrievable across all workflows
- [ ] Business rules RAG — operator's processes, preferences, decision patterns encoded
- [ ] Daily log compaction — daily logs → weekly summaries after 30 days

**Skills (from PRD Phase 4):**
- [ ] Skill conversion — 6 Claude Code skills → OpenClaw AgentSkills format (supabase-ops → ghl-form-connect → clay-enrichment → data-formatter → smb-local-marketing → lead-pipeline)
- [ ] Unit tests — 80%+ coverage with mocked APIs via vitest

**Integrations (from PRD Phase 5 + user requirements):**
- [ ] GoHighLevel MCP — read: direct, write: via n8n proxy
- [ ] Clay.com — waterfall enrichment pattern via n8n proxy
- [ ] Airtable MCP — via @airtable/mcp-server
- [ ] Supabase — re-enable with pgvector + RLS
- [ ] Lead pipeline — trigger → enrich → score → CRM push → log (end-to-end)
- [ ] Gmail + Google Calendar — email triage, calendar event creation from emails
- [ ] iMessage — triage texts, draft responses, flag important conversations
- [ ] Fellow — video meeting recordings and transcripts
- [ ] Apple Notes — call transcripts (auto-added on transcription)
- [ ] Gamma MCP — proposal generation with saved themes
- [ ] Notion — centralized todo list, action log, knowledge base
- [ ] GitHub — project management, code repos
- [ ] Vercel — deployment management
- [ ] GA4 + Search Console — marketing analytics
- [ ] Warp terminal — desired integration with OpenClaw
- [ ] Claude Code — development tool integration

**Channels (from PRD Phase 6):**
- [ ] Telegram bot — HITL approval notifications, primary notification channel
- [ ] Web UI — accessible via Tailscale from all devices
- [ ] Optional: Slack/Discord for status updates

**Operator Workflows (from user questioning):**
- [ ] Email triage — scan inbox, surface actionable items, add calendar events, propose task execution
- [ ] iMessage management — triage, draft responses, flag important
- [ ] Todo list management — populated from emails/meetings/screen observations, centralized in Notion
- [ ] Call recording processing — pull transcripts from Fellow + Apple Notes, extract action items
- [ ] Discovery form generation — create client intake forms from meeting recordings
- [ ] Proposal pipeline — meeting recording → discovery form → Gamma presentation with saved theme
- [ ] OCR screen watcher — capture Windows desktop, detect work context, surface proactive suggestions
- [ ] Active copilot mode — real-time suggestions and task takeover offers
- [ ] Background recorder mode — log work sessions to build pattern knowledge base
- [ ] Proactive task detection — identify help opportunities from screen + calendar context
- [ ] Research capability — autonomous web research for prospects, competitors, market data

**Model Routing (from PRD + user requirements):**
- [ ] 4-tier routing — Ollama qwen3:14b (free, ~30% traffic) → Claude Haiku 4.5 (~50%) → Claude Sonnet 4.5 (~15%) → Claude Opus 4.6 (~5%)
- [ ] Additional models — Kimi and Gemini for specific task types
- [ ] Prompt caching — 60-90% input token cost reduction on system prompts
- [ ] Automatic fallback chain with error handling

**Testing & Cutover (from PRD Phase 7):**
- [ ] Security test battery — 7 prompt injection tests, CVE regression, container verification
- [ ] Context window safety test — 55-turn test, all safety directives survive
- [ ] Cost safety tests — all circuit breakers verified
- [ ] 2-week parallel running — 10%/90% → 50/50 → 100% cutover
- [ ] 90-day supervised HITL period

### Out of Scope

- Mobile app — Mac Mini is the agent; operator uses Windows desktop
- Public-facing web UI — all access via Tailscale VPN only
- Real-time voice interaction — text channels and automation
- Client-facing chatbot — operator-side only
- Custom LLM training/fine-tuning — using existing models via API
- ClawHub community skills — whitelist only, 17% malicious rate makes auto-install dangerous

## Context

**Business:** OnTrack Marketing provides digital marketing for local service businesses (plumbing, solar, dental, legal). The operator handles sales calls, client onboarding, campaign management, and reporting. Most time is spent on repetitive tasks: email, proposals, forms, todo management, and lead processing.

**Full PRD:** `/Users/b2/openclaw-prd.md` (105KB, 11 sections covering architecture, security, setup, implementation, integrations, testing, deployment, operations, troubleshooting)

**Two-machine setup:**
- **Agent machine:** Mac Mini M4 Pro 48GB/1TB (dedicated AI server, runs OpenClaw 24/7 via Docker)
- **Work machine:** Windows desktop (where operator does daily work, right next to Mac Mini)
- Connection: OCR scanning from Mac Mini observing Windows screen; shared cloud tools (Gmail, GHL, Notion, etc.)

**Existing infrastructure:**
- GoHighLevel — CRM, client pipelines, communication (MCP server built in TypeScript)
- Clay.com — Lead enrichment, waterfall pattern, $100/mo credit cap
- n8n — Workflow automation (existing `rise-local-n8n` project on Windows, migrating to Docker on Mac Mini)
- Airtable — Content calendar, tracking (MCP active)
- Fellow — Video meeting recordings and transcripts
- Apple Notes — Call transcripts (auto-added when transcribing); getting Plaud later
- Gamma — Proposal/presentation generation (MCP server, saved themes)
- GitHub — All projects
- Vercel — Deployments
- GA4 + Search Console — Marketing analytics
- Warp — Terminal
- Claude Code — Development tool
- Supabase — Paused (project ID: jitawzicdwgbhatvjblh), re-enable with pgvector + RLS

**Meeting-to-proposal flow (current manual process):**
1. Sales/discovery call (Fellow or manual transcription → Apple Notes)
2. Claude analyzes recording → slide outline
3. Discovery form created and sent for deeper info
4. Prospect fills out form
5. Gamma MCP generates proposal with saved theme
6. Operator reviews and sends

**Self-improvement design:**
Every task execution produces learning data. Errors, token waste, successful patterns, and outcomes are stored in per-task vector databases. On repeat execution, the agent queries its own history to avoid past mistakes and replicate successful approaches. Flywheel: more usage → better performance → less operator intervention.

**Security context (from PRD):**
- CVE-2026-25253 (CVSS 8.8): RCE via auth token exfiltration — patched v2026.1.29+
- CVE-2026-27001 (HIGH): Directory name injection into system prompts — patched v2026.2.25+
- Meta incident: Context window compaction dropped safety directives, deleted 200+ emails
- 17% of ClawHub skills flagged as malicious
- 135,000+ instances publicly exposed with default configs
- Governance transition: Peter Steinberger → OpenAI, foundation governance uncertain

**Cost projection:** $489/month total. Break-even at 2 saved hours/month. Projected savings: 44 hours/month.

## Constraints

- **Hardware:** Mac Mini M4 Pro 48GB RAM, 1TB SSD — Docker services ~11GB + Ollama 8-16GB = 19-27GB
- **Two machines:** Agent can't directly control Windows desktop; relies on OCR + cloud APIs
- **Cost:** $50/mo Anthropic hard cap, $100/mo Clay cap, prefer Ollama for high-volume tasks
- **Security:** OpenClaw v2026.2.25+ mandatory, all ports localhost-only, Tailscale VPN required
- **Privacy:** Client data stays local or in controlled services — no third-party AI training
- **Existing tools:** Integrate with current stack (GHL, Clay, n8n, Airtable), not replace
- **HITL:** 90-day supervised period, DELETE always requires approval, RED tier never relaxed without explicit decision
- **Version:** Pin to v2026.2.25+, monitor governance transition, maintain fork-readiness

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dedicated Mac Mini as agent machine | Isolation from work machine, 24/7 uptime, M4 Pro for local inference | — Pending |
| Docker-based deployment | Container isolation, reproducible, security hardening via compose | — Pending |
| n8n as security proxy | Agent never holds external API keys; all writes mediated | — Pending |
| OCR for cross-machine visibility | Two separate physical machines, best available cross-machine solution | — Pending |
| Notion for todo/action log | No fixed system today; Notion provides structured DB + API access | — Pending |
| Per-task RAG over single knowledge base | Different tasks have different error patterns; isolation prevents cross-contamination | — Pending |
| Multi-model (Claude/Kimi/Gemini/Ollama) | 4-tier cost optimization — free local for triage, cheap API for standard, expensive for reasoning | — Pending |
| File-first memory with hybrid search | Designed in research docs; Markdown as source of truth with SQLite + Qdrant index | — Pending |
| Gamma MCP for proposals | Already in use manually; automate existing workflow | — Pending |
| Tailscale VPN only | 135K+ instances publicly exposed; never expose gateway or web UI | — Pending |
| 90-day HITL supervised period | Meta email deletion incident proves autonomous agents need guardrails | — Pending |
| Whitelist-only skills | 17% ClawHub malicious rate; manual code review all skills | — Pending |

---
*Last updated: 2026-02-27 after initialization (incorporating full PRD from openclaw-prd.md)*

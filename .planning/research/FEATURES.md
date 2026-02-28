# Feature Research

**Domain:** Autonomous AI marketing assistant for solo operator (always-on, operator-facing, brownfield deployment)
**Researched:** 2026-02-28
**Confidence:** HIGH — operator workflows and toolstack are fully documented in 175+ research files; web research confirms market patterns.

---

## Context: What Makes This Domain Unique

This is not a general-purpose chatbot or team productivity tool. It is a solo-operator AI agent layer for a digital marketing agency with specific characteristics:

- **Single operator.** No team coordination, no multi-user permissions, no shared inboxes. Every feature serves one person.
- **Brownfield.** GoHighLevel, Clay.com, n8n, Airtable, Fellow, Gamma, and Notion already exist. The agent adds orchestration — it does not replace the stack.
- **Two-machine constraint.** The agent runs on a Mac Mini. The operator works on a Windows PC. Cross-machine interaction is OCR + cloud APIs only. No direct Windows control.
- **Always-on expectation.** The agent should be observing, learning, and acting 24/7 — not just responding to prompts.
- **90-day supervised period.** Trust is earned incrementally. No autonomous external actions without HITL approval during this window.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that make the agent feel like "an actual assistant" rather than "a prompt box." Missing any of these makes the product feel incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Email triage and summarization** | Email is the primary async work channel; without this, the agent misses 60%+ of daily work context | MEDIUM | Gmail API; read/summarize/label. No autonomous send — that requires HITL. Action items extracted into todo list. |
| **Todo list population from multiple sources** | Operators expect "capture everything once" — todos from emails, meetings, texts should converge automatically | MEDIUM | Notion as destination (API-based). Sources: email, meeting transcripts, iMessage context, screen observations. |
| **Meeting transcript processing** | Fellow/Apple Notes transcripts already exist; not processing them is wasted data | MEDIUM | Pull from Fellow API + Apple Notes; extract decisions, action items, open questions. |
| **Telegram command interface** | Primary human-agent channel for HITL, queries, and control; already chosen in PRD | LOW | Already designed. Quiet hours, inline approval buttons, command routing. |
| **Proactive status notifications** | Agent working silently with no output = operator distrust. Visibility is table stakes. | LOW | Push updates on completed actions, pending approvals, and detected opportunities via Telegram. |
| **HITL approval for all external actions** | Meta email deletion incident (200+ emails) proves this is mandatory, not optional | MEDIUM | Tiered: RED (always approve) / GREEN (auto-approve) / YELLOW (context-dependent). Inline Telegram buttons. |
| **Cost circuit breakers** | Runaway API loops at $200+/day are a documented OpenClaw failure mode | LOW | $50/month Anthropic cap, 50 tool calls/session, 30-minute timeout. Already designed in PRD. |
| **Calendar awareness for scheduling** | Without calendar integration, the agent schedules actions during meetings or off-hours | LOW | Google Calendar API. Block actions during meetings, skip check-ins, defer notifications. |
| **Persistent memory across sessions** | "I already told you that" is a fatal UX failure for an always-on assistant | MEDIUM | File-first memory (MEMORY.md) + hybrid search (SQLite FTS5 + Qdrant). Already designed. |
| **Lead pipeline end-to-end** | The core revenue-generating workflow must work before anything else | HIGH | Clay.com enrichment → scoring → GHL push → sequence trigger. Currently partial (Clay connector missing). |

### Differentiators (Competitive Advantage)

Features that go beyond what Lindy, Zapier Agents, or generic AI assistants offer. These are where OpenClaw creates operator-specific value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Meeting-to-proposal pipeline** | Converts a sales call into a Gamma presentation draft in one flow — 90 min of manual work → 5 min of agent work | HIGH | Fellow transcript → Claude analysis → discovery form generation → Gamma MCP presentation. HITL review before delivery. Each step is partially built; connecting them is the differentiation. |
| **iMessage context awareness** | Client texts create follow-up tasks and check-in context automatically — no manual capture | HIGH | FastAPI relay on Mac Mini reading chat.db via Tailscale. Read-only, privacy-filtered. Detection latency < 10 seconds. Requires macOS Full Disk Access. |
| **OCR screen watching (work context database)** | Agent knows what the operator was working on — "What was I looking at for Acme Corp?" becomes answerable | HIGH | 30-second Windows screen capture → Tesseract OCR → Supabase with pgvector. Searchable across time. Enables proactive suggestions based on active work context. |
| **Proactive check-ins with adaptive timing** | Agent initiates contact 3-5x daily based on time of day, pending work, and calendar — not just reactive | MEDIUM | LaunchAgent cron (5 slots), template pools per time slot, anti-repetition logic, response-rate adaptation over 14-day window. Learns which slots the operator actually engages with. |
| **Per-task RAG for recursive self-improvement** | Every task execution trains future performance on that task type — flywheel that compounds | HIGH | Separate Qdrant collection per task type. Errors, patterns, successful approaches indexed. On repeat execution, agent queries its own history before acting. Unique among deployment-level AI assistants. |
| **Prompt optimization with A/B testing** | Agent proposes and tests its own improvements, operator approves — continuous quality lift with no manual tuning | HIGH | Weekly evaluation agent. Constitutional self-critique. 48-hour rollback monitoring. Metric-driven (success rate, approval rate, latency). Requires all core skills to be stable first (Phase 13). |
| **Skill auto-generation from gap detection** | Agent identifies repeated failed requests, proposes new skills, human approves — capability expansion without manual development | HIGH | Intent clustering on `missing_capability` events → LLM generates YAML + implementation → security scan → HITL approval. Requires Phase 13. |
| **4-tier model routing** | Automatically assigns each task to the cheapest capable model — significant cost savings without quality loss | MEDIUM | Ollama qwen3:14b (free, ~30%) → Claude Haiku 4.5 (~50%) → Claude Sonnet 4.5 (~15%) → Opus 4.6 (~5%). Kimi and Gemini for specific domains. |
| **CRM-triggered presentation generation** | Moving a lead to "qualified" in GHL automatically drafts a pitch deck tailored to their industry | MEDIUM | GHL webhook → Gamma MCP generate → Telegram preview → approve → export PDF → deliver. Removes a multi-hour manual workflow. |
| **Screen-to-todo task detection** | Agent observes what the operator is working on and offers to take over or assist with detected tasks | HIGH | Requires OCR screen DB (Phase 12). Completes the "passive observer → active assistant" loop. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem useful but create disproportionate problems for this specific deployment.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Autonomous email sending without HITL** | "Save me the approval step" | Meta email incident: context compaction dropped safety directives, 200+ emails deleted. External messages are permanent and reputation-affecting. | GREEN-tier HITL for draft review with one-tap approve in Telegram. Keeps speed, adds safety net. |
| **Auto-installing ClawHub community skills** | "Discover and use new capabilities automatically" | 17% of ClawHub skills contain malicious code. Auto-install = supply chain attack vector. | Whitelist-only: agent proposes skills from ClawHub with code review summary, operator approves manually. |
| **Real-time voice interaction** | "Just talk to the agent like Siri" | The agent runs 24/7 on a Mac Mini next to a Windows desktop. Voice creates ambient listening risk and privacy concerns. The operator isn't sitting at the Mac Mini — text channels are more appropriate. | Telegram text commands with fast response. Good UX without ambient microphone. |
| **Client-facing chatbot** | "Let clients interact with the agent directly" | Operator is the client relationship owner. Agent acting as client-facing rep without operator context creates liability and service quality risk. | Agent handles internal operations only. Operator remains the client-facing party. |
| **Mobile app** | "I want to interact from my phone" | Telegram already works on mobile. A native mobile app duplicates the notification and command interface for no benefit. | Telegram bot covers mobile use case. Web UI (Tailscale-accessible) covers desktop dashboarding. |
| **Custom LLM fine-tuning** | "Train the model on my data for better accuracy" | Fine-tuning requires significant labeled data, infrastructure, and expertise. Per-task RAG achieves similar task-specific accuracy improvements at a fraction of the cost and complexity. | Per-task RAG vector stores + prompt caching. Achieves domain adaptation without fine-tuning overhead. |
| **Slack/Discord as primary channel** | "More familiar interface" | Telegram is already chosen, hardened (quiet hours, HITL inline buttons), and documented. Adding another channel = split notification attention + double the integration surface. | Telegram exclusively. Optional Slack/Discord for passive status broadcast only (no action-required messages). |
| **Publicly exposed web UI** | "Easier access without VPN" | 135,000+ OpenClaw instances are publicly exposed with default configs — this is an actively exploited attack pattern. | Tailscale VPN mandatory. All interfaces accessible from all devices via Tailscale mesh. |
| **Automatic proposal delivery to clients** | "Save the review step" | Proposals represent the agency's reputation. A hallucinated claim or wrong client name in a Gamma deck is a sales disaster. | Always HITL Tier 1 for client-facing delivery. Operator reviews Gamma preview link before anything is sent. |

---

## Feature Dependencies

```
[Gmail Integration]
    └──requires──> [Google OAuth / API credentials]
    └──enables──> [Email Triage]
                      └──requires──> [Gmail Integration]
                      └──enables──> [Todo Population from Email]

[Memory System (MEMORY.md + SQLite + Qdrant)]
    └──required by──> [Per-task RAG]
    └──required by──> [Proactive Check-ins]
    └──required by──> [iMessage Context Awareness]
    └──required by──> [Screen-to-Todo Detection]

[Telegram Bot (HITL)]
    └──required by──> [All external actions]
    └──required by──> [Proactive Check-ins]
    └──required by──> [Gamma presentation approval]
    └──required by──> [Self-Evolution proposals]

[n8n Security Proxy]
    └──required by──> [Lead Pipeline]
    └──required by──> [Gmail send (via proxy)]
    └──required by──> [GHL write operations]
    └──required by──> [Clay.com enrichment]

[Lead Pipeline]
    └──requires──> [GHL MCP]
    └──requires──> [Clay.com connector via n8n]
    └──requires──> [Airtable MCP]

[Meeting-to-Proposal Pipeline]
    └──requires──> [Fellow API or Apple Notes integration]
    └──requires──> [Gamma MCP]
    └──requires──> [Telegram HITL (approval before delivery)]
    └──requires──> [Memory System (client context)]

[Proactive Check-ins]
    └──requires──> [Telegram Bot]
    └──requires──> [Memory System]
    └──enhances with──> [Google Calendar awareness]
    └──enhances with──> [iMessage context]
    └──enhances with──> [Screen activity context]

[OCR Screen Database]
    └──requires──> [Supabase (pgvector)]
    └──requires──> [Ollama on Mac Mini (embedding generation)]
    └──requires──> [Windows capture service (Python, Tesseract)]
    └──enables──> [Proactive task detection]
    └──enables──> [Screen-to-todo]
    └──enriches──> [Proactive Check-ins]

[iMessage Integration]
    └──requires──> [Tailscale VPN (cross-machine networking)]
    └──requires──> [Full Disk Access on Mac Mini]
    └──enriches──> [Proactive Check-ins]

[Per-task RAG]
    └──requires──> [Memory System]
    └──requires──> [Qdrant]
    └──feeds──> [Self-Evolution / Prompt Optimization]

[Self-Evolution]
    └──requires──> [All core skills operational and instrumented]
    └──requires──> [Supabase (metrics tables)]
    └──requires──> [Telegram HITL]
    └──requires──> [Git version control for ~/.openclaw/]

[Cost Circuit Breakers]
    └──required by (must precede)──> [Any autonomous execution]
    └──protects against──> [Lead Pipeline runaway]
    └──protects against──> [Self-Evolution runaway]
```

### Dependency Notes

- **HITL is a horizontal dependency.** Every feature that takes external action or produces operator-visible output depends on the Telegram HITL system. It must be implemented early and never bypassed.
- **Memory system is the learning substrate.** Per-task RAG, proactive check-ins, and self-evolution all require the memory system to be stable and populated before they deliver value.
- **OCR screen database is an enhancer, not a blocker.** Check-ins and todo population work without screen data, but are significantly more contextually relevant with it.
- **n8n security proxy is non-negotiable.** The agent must never hold external API keys directly. Every write operation to GHL, Clay, email goes through n8n. This is a hard dependency for the lead pipeline and email features.
- **Self-evolution conflicts with early-phase deployment.** Skill auto-generation and prompt rewriting require stable baseline metrics. Deploying self-evolution before 90-day HITL period is complete would be counterproductive — the system wouldn't have enough signal to evaluate changes reliably.

---

## MVP Definition

### Launch With (v1) — Operator Layer

The minimum set that makes the agent genuinely useful in daily work and validates the brownfield integration approach.

- [ ] **Email triage** — Scan Gmail inbox, surface actionable items, extract action items to Notion todo. The first thing the operator checks every morning becomes semi-automated. Core daily value.
- [ ] **Lead pipeline end-to-end** — Clay enrichment → GHL push → sequence trigger. Revenue-generating; validates core infrastructure (n8n proxy, GHL MCP, Clay connector). Already partially built.
- [ ] **Telegram HITL** — Inline approve/reject for all external actions. Non-negotiable for safe operation. Required before any autonomous write actions.
- [ ] **Meeting transcript processing** — Fellow + Apple Notes → action items → Notion todo. Removes 20-30 min of manual post-meeting work.
- [ ] **Proactive check-ins (basic)** — 3 daily messages (morning, midday, evening). No calendar integration yet, no iMessage context. Just time-of-day + memory-based context. Establishes the always-on relationship.
- [ ] **Notion todo management** — Centralized task list populated from email, meetings, and Telegram. Operator sees one place for all captured tasks.
- [ ] **Cost circuit breakers** — $50/mo Anthropic cap, 50 tool calls/session, 30-min timeout. Must be active before any autonomous execution.

### Add After Validation (v1.x) — Enriched Context

Add once core workflows are running reliably (estimated: 6-8 weeks post-launch).

- [ ] **Gamma proposal pipeline** — Meeting recording → discovery form → Gamma presentation. Adds when operator has used the agent for 2+ sales cycles and wants to accelerate the proposal step.
- [ ] **iMessage integration** — Read-only relay for conversation context. Add when check-ins feel generic; iMessage context makes them feel contextually aware.
- [ ] **Google Calendar awareness** — Block check-ins during meetings, add calendar context. Add when operator complains about poorly-timed check-ins.
- [ ] **Per-task RAG** — Start indexing execution outcomes. Add immediately after v1 goes live — the sooner it starts accumulating data, the sooner it improves.
- [ ] **4-tier model routing** — Route triage tasks to Ollama, reserve Claude for reasoning. Add when Anthropic costs approach $30/month.

### Future Consideration (v2+) — Autonomous Intelligence

Defer until the system has 90+ days of stable operation and the operator trusts the agent's judgment.

- [ ] **OCR screen database** — Continuous Windows screen capture + searchable history. High complexity (14-20 hours), high privacy surface. Defer until iMessage integration is proven and operator is comfortable with cross-machine data capture.
- [ ] **Proactive task detection from screen** — Agent offers to take over work in progress. Requires OCR screen database to be mature.
- [ ] **Self-evolution (prompt optimization)** — Agent rewrites its own prompts based on metrics. Requires 60+ days of instrumented execution data and all core skills stable.
- [ ] **Skill auto-generation** — Agent proposes and implements new skills for repeated gaps. Requires self-evolution infrastructure. Phase 13 dependency.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Email triage | HIGH | MEDIUM | P1 |
| Lead pipeline end-to-end | HIGH | HIGH | P1 |
| Telegram HITL | HIGH | LOW | P1 |
| Meeting transcript processing | HIGH | MEDIUM | P1 |
| Cost circuit breakers | HIGH | LOW | P1 |
| Notion todo management | HIGH | MEDIUM | P1 |
| Proactive check-ins (basic) | HIGH | MEDIUM | P1 |
| Gamma proposal pipeline | HIGH | HIGH | P2 |
| iMessage integration | MEDIUM | HIGH | P2 |
| Google Calendar awareness | MEDIUM | LOW | P2 |
| Per-task RAG | HIGH | HIGH | P2 |
| 4-tier model routing | MEDIUM | MEDIUM | P2 |
| OCR screen database | MEDIUM | HIGH | P3 |
| Proactive task detection | HIGH | HIGH | P3 |
| Self-evolution (prompt optimization) | HIGH | HIGH | P3 |
| Skill auto-generation | HIGH | HIGH | P3 |
| Competitor analysis capability | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch — agent is useless without these
- P2: Should have, add when core is stable — meaningfully increases value
- P3: Future consideration, defer until 90-day HITL period complete

---

## Competitor Feature Analysis

This is a bespoke deployment, not a commercial product. The relevant comparison is against what a solo operator would otherwise do manually or with generic AI tools.

| Feature | Generic AI Assistant (ChatGPT/Claude) | Lindy / Zapier Agents | OpenClaw Operator Layer |
|---------|----------------------------------------|----------------------|-------------------------|
| Email triage | Manual prompt per session; no persistent state | Auto-triage available; no per-operator learning | Auto-triage with per-task RAG; learns operator's priorities over time |
| Meeting-to-proposal | Manual copy-paste transcript → prompt → manual Gamma | Not connected end-to-end | Automated pipeline: Fellow → analysis → form → Gamma → HITL |
| Todo management | No integration with operator's actual tools | Zapier can write to Notion; no intelligent extraction | Extracts todos from email, transcripts, texts, screen; writes to Notion |
| iMessage awareness | None | None | Read-only relay via Tailscale + chat.db; privacy-filtered |
| Screen context | None | None | OCR capture every 30s, searchable via pgvector |
| Self-improvement | None (stateless) | Basic workflow logging | Per-task RAG + prompt optimization + skill auto-gen |
| Cost management | Token-by-token billing; no circuit breakers | Per-action pricing; no local inference option | 4-tier routing with Ollama (free); hard $50/mo Anthropic cap |
| Security | Cloud-only; API keys in third-party system | API keys held by third party | Keys in n8n proxy on local machine; no cloud holds operator's credentials |
| HITL integration | No native approval flow | Zapier Approval steps; email-based | Telegram inline buttons; tiered (RED/GREEN/YELLOW) |

**Where OpenClaw wins:** Per-operator learning, end-to-end pipeline automation, cross-machine context (screen + iMessage), local inference cost optimization, and the self-evolution flywheel. These are not available from any SaaS alternative.

**Where OpenClaw loses (initially):** Setup complexity (14-18 weeks vs. day-one SaaS), requires operator technical involvement, and no fallback if Mac Mini goes down.

---

## Complexity Notes by Feature

### HIGH Complexity Features — Require Special Attention

**Lead pipeline end-to-end:** Revenue-generating. Run old system in parallel for 2+ weeks before cutover. Clay.com connector is the custom build (4h); scoring logic migration from n8n is the risk (4h).

**Meeting-to-proposal pipeline:** Spans 5+ systems (Fellow, Apple Notes, Claude analysis, Gamma MCP, GHL, Telegram). Each handoff is a failure point. Build and test each segment independently before connecting.

**Per-task RAG:** The schema design (separate Qdrant collections per task type vs. metadata-filtered single collection) is the key architectural decision. Separate collections avoid cross-contamination; metadata filtering is simpler. Documented decision: separate collections.

**OCR screen database:** Two-machine complication — capture runs on Windows, embedding and search run on Mac Mini, sync goes through Supabase. Three potential failure points. Privacy filter for excluded apps (password managers, banking) must work before any data is captured.

**iMessage integration:** macOS Full Disk Access permission is a manual step with no automation path. Requires physical access to the Mac Mini at setup time. `attributedBody` BLOB handling for Ventura+ is non-trivial.

**Self-evolution:** Do not attempt before 90-day HITL period. Requires instrumented metrics across all core skills, constitutional review layer, regression detection with auto-rollback, and Git version control for `~/.openclaw/`. One bad prompt rewrite could silently degrade all skills.

### MEDIUM Complexity — Standard Patterns

**Email triage:** Gmail API is well-documented. The operator-specific logic (what counts as "actionable" for this agency) requires tuning based on actual email patterns.

**Proactive check-ins:** LaunchAgent scheduling is simple. The value is in the template system and anti-repetition logic (track last 10, never repeat in 3 days). Calendar integration is optional initially.

**Gamma proposal pipeline:** Gamma MCP tools are documented. The complexity is assembling the full pipeline and handling HITL at the right step (preview before delivery, not before generation).

### LOW Complexity — Build Early

**Telegram HITL, cost circuit breakers, calendar awareness:** Well-documented, standard patterns. Build these first — they are prerequisites for everything else and low risk.

---

## Sources

- PROJECT.md (operator requirements, infrastructure decisions, toolstack)
- PRD `/Users/b2/openclaw-prd.md` (security context, HITL design, cost projections)
- Phase 9-13 roadmap files (proactive check-ins, Gamma, iMessage, screen DB, self-evolution)
- GAP-ANALYSIS.md (existing ecosystem, what is built vs. missing, effort estimates)
- `08-Capabilities-Deep-Dive/proactive-checkins/checkin-engine.md` (check-in engine design)
- `08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md` (Gamma MCP tools and HITL flow)
- `08-Capabilities-Deep-Dive/document-processing/implementation-guide.md` (OCR pipeline architecture)
- WebSearch: autonomous AI assistant features for solo operators (2026)
- WebSearch: AI agent email triage marketing agency (2026)
- WebSearch: iMessage management AI assistant (2026)
- WebSearch: meeting-to-proposal pipeline automation Fellow + Gamma (2026)
- WebSearch: HITL patterns for AI agents solo operator (2026)
- WebSearch: per-task RAG self-improving AI agents (2026)

---
*Feature research for: OpenClaw Operator Layer — autonomous AI marketing assistant*
*Researched: 2026-02-28*

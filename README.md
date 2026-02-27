# OpenClaw Research & Setup Knowledge Base

> **Project Goal**: Build the most elite OpenClaw autonomous AI agent platform, integrated with your existing marketing/lead-gen ecosystem, running 24/7 on a Mac Mini.

---

## What Is OpenClaw?

OpenClaw (formerly Clawdbot -> Moltbot -> OpenClaw) is the **#1 trending open-source AI agent platform** with 145K+ GitHub stars, 30K+ Discord members, and 3,000+ community-built skills. Created by Peter Steinberger (Austrian engineer).

**Key difference from chatbots**: OpenClaw *does things* - books flights, manages CRM, sends messages, controls browsers, generates leads, builds presentations. It runs 24/7 as an autonomous agent.

**Architecture**: Gateway-centric WebSocket server (port 18789) orchestrating agents, sessions, channels (WhatsApp/Telegram/Discord/Slack), tools, and skills. File-first memory with hybrid vector + FTS5 search in SQLite. Model-agnostic (Claude, GPT, Ollama local models).

---

## Navigation

### Root Files
| File | Purpose |
|------|---------|
| [README.md](README.md) | This file - master index |
| [QUICK-START.md](QUICK-START.md) | Fast-track Mac Mini setup reference |
| [GAP-ANALYSIS.md](GAP-ANALYSIS.md) | What you have vs what OpenClaw needs |
| [MIGRATION-CHECKLIST.md](MIGRATION-CHECKLIST.md) | Windows -> Mac Mini transition tracker |

### Research Sections

| # | Section | Description | Files |
|---|---------|-------------|-------|
| 00 | [Foundation](00-Foundation/) | Architecture, concepts, history, comparisons | 4 |
| 01 | [Mac Mini Setup](01-Mac-Mini-Setup/) | Hardware, OS, Docker, env vars, verification | 7 |
| 02 | [Security](02-Security/) | Threat model, Docker hardening, VPN, credentials, HITL | 7 |
| 03 | [LLM Strategy](03-LLM-Strategy/) | Model routing, Ollama, Claude API, cost optimization | 5 |
| 04 | [Memory & RAG](04-Memory-and-RAG/) | File-first memory, hybrid search, embeddings, sector knowledge | 10 |
| 05 | [Skills Development](05-Skills-Development/) | Skills architecture, ClawHub, custom skills, Gamma skill | 13 |
| 06 | [Integrations](06-Integrations/) | GHL, Clay, Supabase, n8n, Airtable, existing projects | 20 |
| 07 | [Channel Setup](07-Channel-Setup/) | WhatsApp, Telegram, Discord, Slack, web UI, iMessage | 10 |
| 08 | [Capabilities Deep Dive](08-Capabilities-Deep-Dive/) | Presentations, CRM, enrichment, screen DB, check-ins, scraping | 32 |
| 09 | [Legal & Compliance](09-Legal-Compliance/) | Privacy law, ToS compliance, scraping legality | 5 |
| 10 | [Cost Analysis](10-Cost-Analysis/) | Infrastructure, API, stack costs, ROI | 5 |
| 11 | [Implementation Roadmap](11-Implementation-Roadmap/) | 13-phase rollout plan, week-by-week | 13 |
| 12 | [Self-Evolution](12-Self-Evolution/) | Prompt optimization, skill auto-generation, safety guardrails | 5 |

---

## Your Existing Ecosystem (Already ~70% Built)

| Tool/Project | Status | OpenClaw Role |
|-------------|--------|---------------|
| **Ralph** (v0.9.9) | Active | Co-exists as dev loop agent |
| **Rise Local Lead Creation** | Active | Lead pipeline feeds OpenClaw enrichment |
| **GoHighLevel MCP** | Built (`Desktop/GoHighLevel-MCP`) | Direct reuse as OpenClaw tool |
| **OnTrack Marketing** | Built (FastAPI/Next.js/PostgreSQL/Redis/Qdrant) | RAG integration |
| **RAFE + Obsidian** | Active | Knowledge base sync |
| **N8N Workflows** | Active (`Desktop/rise-local-n8n`) | Workflow orchestration bridge |
| **Supabase** | Configured but disabled (`jitawzicdwgbhatvjblh`) | Reactivate for pgvector RAG |
| **Airtable MCP** | Active | Direct reuse as OpenClaw tool |
| **Claude Code Skills** | 6 active skills | Migrate to OpenClaw skill format |
| **Marketing Stack** | $156-206/mo | Integrate APIs into OpenClaw |

---

## Critical Security Warning

OpenClaw's own docs say: **"There is no 'perfectly secure' setup."**

Three major risks:
1. **Root Risk** - Host compromise if not containerized
2. **Agency Risk** - AI takes unintended destructive actions autonomously
3. **Keys Risk** - Credential leakage (GHL, Clay, Supabase, Claude API keys)

**Non-negotiable mitigations**: Docker isolation, Tailscale VPN, Human-in-the-Loop for sensitive actions, dedicated credentials, regular audits. See [02-Security/](02-Security/) for full details.

---

## Implementation Timeline

| Phase | Focus | Timeline |
|-------|-------|----------|
| 1 | Mac Mini + Docker + OpenClaw install | Week 1 |
| 2 | Security hardening, Tailscale, credentials | Week 1-2 |
| 3 | Memory system + sector RAG | Week 2-3 |
| 4 | Core skills (CRM, enrichment, presentations) | Week 3-4 |
| 5 | Connect GHL, Clay, n8n, Supabase | Week 4-5 |
| 6 | Channels (WhatsApp, Telegram, web UI) | Week 5-6 |
| 7 | Advanced (LinkedIn, scraping, websites) | Week 6-8 |
| 8 | Performance tuning, cost optimization | Ongoing |
| 9 | Proactive check-ins (Telegram, 3-5x/day) | Week 9-10 |
| 10 | Gamma presentation automation | Week 10-11 |
| 11 | iMessage integration (read-only relay) | Week 11-12 |
| 12 | OCR screen database (Windows capture) | Week 12-14 |
| 13 | Self-evolution (prompt optimization, skill auto-gen) | Week 14-18 |

See [11-Implementation-Roadmap/](11-Implementation-Roadmap/) for detailed phase plans.

---

## Key Research Gaps (Flagged Throughout Files)

- Exact OpenClaw version compatibility with existing MCP servers
- Mac Mini M4 specific performance benchmarks for your workload
- Cost modeling for your specific API usage patterns
- Testing OpenClaw skill migration from Claude Code skill format
- Tailscale setup specifics for your network topology
- ScreenPipe Windows stability for potential replacement of custom capture pipeline
- Gamma API rate limits and pricing tiers under load
- Google Calendar API integration for check-in calendar awareness
- DSPy integration feasibility for automated prompt optimization
- ClawHub API documentation for programmatic skill discovery

---

## Quick Links

- **OpenClaw GitHub**: https://github.com/openclaw/openclaw
- **OpenClaw Docs**: https://docs.openclaw.sh
- **ClawHub Skills**: https://clawhub.openclaw.sh
- **Discord Community**: https://discord.gg/openclaw
- **Peter Steinberger (Creator)**: @steipete on Twitter/X

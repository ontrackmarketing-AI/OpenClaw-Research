# Codebase Structure

**Analysis Date:** 2026-02-27

## Directory Layout

```
/Users/b2/OpenClaw-Research/
├── 00-Foundation/                    # Core architecture, concepts, version history, comparisons
├── 01-Mac-Mini-Setup/                # Hardware, OS setup, Docker, env vars, verification
├── 02-Security/                      # Threat model, hardening, VPN, credentials, HITL
├── 03-LLM-Strategy/                  # Model routing, Ollama local models, Claude API, cost optimization
├── 04-Memory-and-RAG/                # File-first memory, hybrid search, embeddings, sector knowledge
├── 05-Skills-Development/            # Skills architecture, ClawHub, custom skills, Gamma skill
├── 06-Integrations/                  # MCP + REST integrations for GHL, Clay, Supabase, n8n, Airtable
├── 07-Channel-Setup/                 # WhatsApp, Telegram, Discord, Slack, web UI, iMessage guides
├── 08-Capabilities-Deep-Dive/        # 14 capability modules (presentations, CRM, content, enrichment, etc.)
├── 09-Legal-Compliance/              # Privacy law, ToS compliance, scraping legality
├── 10-Cost-Analysis/                 # Infrastructure, API, and stack costs, ROI calculations
├── 11-Implementation-Roadmap/        # 13-phase rollout plan (Foundation through Self-Evolution)
├── 12-Self-Evolution/                # Prompt optimization, skill auto-generation, safety guardrails
├── .planning/                        # GSD project state (created by /gsd:new-project)
├── .planning/codebase/               # Codebase analysis documents (this directory)
├── CLAUDE.md                         # Project instructions and GSD framework reference
├── GAP-ANALYSIS.md                   # 15 gap analysis items between current state and OpenClaw needs
├── MIGRATION-CHECKLIST.md            # 213 checklist items across 8 phases (Windows → Mac transition)
├── QUICK-START.md                    # Fast-track Mac Mini setup reference
├── README.md                         # Master index with navigation table, existing ecosystem, timeline
└── .git/                             # Git repository
```

---

## Directory Purposes

**00-Foundation/**
- Purpose: Core OpenClaw platform architecture, foundational concepts, version history
- Contains: 4 markdown files
- Key files:
  - `core-concepts.md` (640 lines) -- Skills, Memory, Channels, Agents, Tools, Sessions, Gateway
  - `openclaw-architecture.md` (649 lines) -- Detailed system architecture, deployment, configuration
  - `version-history.md` (12,700 bytes) -- Release timeline and evolution
  - `vs-existing-tools.md` (19,709 bytes) -- Comparison with Ralph, Claude Code, N8N

**01-Mac-Mini-Setup/**
- Purpose: Hardware provisioning and OS-level setup for the agent machine
- Contains: 7 files covering Mac Mini M4 Pro, macOS, Docker, networking, verification
- Key areas: Hardware specs, Docker installation, environment variables, system verification

**02-Security/**
- Purpose: Threat model, security hardening, credentials management, Human-in-the-Loop (HITL)
- Contains: 7 files covering Docker hardening, Tailscale VPN, API key management, HITL workflows

**03-LLM-Strategy/**
- Purpose: Model selection, routing logic, Ollama local models, Claude API integration, cost optimization
- Contains: 5 files covering model provider strategy, Claude API specifics, cost analysis

**04-Memory-and-RAG/**
- Purpose: Persistent memory system design, RAG pipeline, sector knowledge ingestion
- Contains: 10 files including visibility-strategy.md, memory-architecture.md, knowledge-ingestion.md
- Structure:
  - `memory-architecture.md` -- File-first design, SQLite + vector storage, hybrid search
  - `visibility-strategy.md` -- Two-machine access patterns (Layer 1: local files, Layer 2: git, Layer 3: MCP/APIs, Layer 4: memory logs)
  - `sector-knowledge/` -- Industry-specific (Plumbing, Solar, Dental, Legal) RAG fragments
- Dependency: Critical for agent context injection

**05-Skills-Development/**
- Purpose: Custom skill creation, ClawHub integration, skill architecture
- Contains: 13 files including skill-architecture.md, custom-skills.md, gamma-skill.md
- Key file: `priority-skills/` subdirectory with 9 priority skills

**06-Integrations/**
- Purpose: MCP + REST integration patterns for external platforms and tools
- Contains: 20 files across 11 integration categories
- Structure:
  - `airtable/` -- MCP adapter for content calendar, lead tracking
  - `gohighlevel/` -- MCP adapter for CRM (contacts, pipelines, campaigns)
  - `n8n/` -- Workflow orchestration bridge (running on Windows)
  - `supabase/` -- pgvector + screen database (currently paused)
  - `clay-enrichment/` -- Lead enrichment data connector
  - `wordpress/`, `apollo/`, `seo-tools/`, `plaud/`, `content-pipeline/` -- Supporting integrations
  - `existing-projects/` -- Bridge for Ralph, Rise Local, OnTrack Marketing
  - `integration-architecture.md` -- MCP + REST + webhook design patterns
- Note: Layer 3 of visibility strategy; primary method for agent accessing remote work

**07-Channel-Setup/**
- Purpose: Communication channel configuration (WhatsApp, Telegram, Discord, Slack, web UI, iMessage)
- Contains: 10 files with setup guides for each platform
- Key subdirectory: `imessage/` for iOS message relay

**08-Capabilities-Deep-Dive/**
- Purpose: Detailed implementation guides for 14+ agent capabilities
- Contains: 16 capability directories (presentations, CRM, enrichment, content, etc.)
- Structure:
  - `advertising/` -- Ad management and campaign automation
  - `competitor-intelligence/` -- Competitive analysis tools
  - `content-factory/` -- Content generation and scheduling
  - `crm-management/` -- CRM workflow automation
  - `document-processing/` -- OCR and document handling
  - `gamification/` -- Engagement and reward systems
  - `lead-enrichment/` -- Data enrichment for leads
  - `linkedin/` -- LinkedIn automation (aimfox, expandi, page-growth)
  - `presentations/` -- Gamma presentation generation
  - `proactive-checkins/` -- Automated check-in system
  - `screen-database/` -- OCR'd screenshot database
  - `social-monitoring/` -- Social media tracking
  - `voice-bot/` -- Voice interaction capabilities
  - `website-building/` -- Website generation and optimization

**09-Legal-Compliance/**
- Purpose: Privacy law, ToS compliance, scraping legality, regulatory considerations
- Contains: 5 files covering GDPR, CCPA, scraping laws, ToS requirements

**10-Cost-Analysis/**
- Purpose: Infrastructure, API, and stack costs; ROI modeling
- Contains: 5 files with cost breakdowns (infrastructure, Claude API, marketing stack, hosting)

**11-Implementation-Roadmap/**
- Purpose: 13-phase rollout plan with week-by-week execution details
- Contains: 13 files (one per phase) from Foundation through Self-Evolution
- Structure: Each phase file contains detailed tasks, success criteria, verification steps
- Key phases:
  - Phase 1: Foundation (Mac Mini, Docker, OpenClaw install)
  - Phase 2: Security (Hardening, Tailscale, credentials)
  - Phase 3: Memory & RAG (Hybrid search setup, sector knowledge)
  - Phase 4: Core Skills (CRM, enrichment, presentations)
  - Phase 5: Integrations (GHL, Clay, n8n, Supabase)
  - Phase 6: Channels (WhatsApp, Telegram, web UI)
  - Phase 7: Advanced (LinkedIn, scraping, websites)
  - Phase 8: Optimization (Performance tuning, cost optimization)
  - Phase 9-13: Proactive check-ins, Gamma, iMessage, Screen DB, Self-Evolution

**12-Self-Evolution/**
- Purpose: Automated prompt optimization, skill auto-generation, safety guardrails
- Contains: 5 files covering evolution architecture, notification system, prompt optimization, safety

**.planning/codebase/**
- Purpose: GSD codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md)
- Contains: Analysis documents generated by `/gsd:map-codebase` (this directory)
- Usage: Referenced by `/gsd:plan-phase` and `/gsd:execute-phase` to understand codebase patterns

---

## Key File Locations

**Entry Points:**
- `README.md` -- Master index with navigation and project context
- `QUICK-START.md` -- Fast-track setup reference for Mac Mini deployment
- `CLAUDE.md` -- GSD framework reference and project instructions

**Configuration & Reference:**
- `GAP-ANALYSIS.md` -- 15 identified gaps between current state and OpenClaw readiness
- `MIGRATION-CHECKLIST.md` -- 213 checklist items for Windows → Mac transition across 8 phases

**Core Architecture:**
- `00-Foundation/core-concepts.md` -- Fundamental concepts (Skills, Memory, Channels, Agents, Tools, Sessions, Gateway)
- `00-Foundation/openclaw-architecture.md` -- System architecture, deployment models, resource requirements
- `04-Memory-and-RAG/visibility-strategy.md` -- Two-machine data access patterns (critical for integration design)
- `04-Memory-and-RAG/memory-architecture.md` -- File-first memory, hybrid search, SQLite indexing

**Integration Design:**
- `06-Integrations/integration-architecture.md` -- MCP + REST + webhook patterns
- `06-Integrations/gohighlevel/` -- CRM integration implementation
- `06-Integrations/airtable/` -- Content & lead tracking integration
- `06-Integrations/n8n/` -- Workflow orchestration bridge

**Implementation Phases:**
- `11-Implementation-Roadmap/phase-1-foundation.md` (14,535 lines) -- Week 1 setup
- `11-Implementation-Roadmap/phase-5-integrations.md` (25,720 lines) -- Integration rollout (Weeks 4-5)
- `11-Implementation-Roadmap/phase-3-memory-rag.md` (22,055 lines) -- Memory system setup

**Capability Deep-Dives:**
- `08-Capabilities-Deep-Dive/presentations/` -- Gamma API integration for auto-generated presentations
- `08-Capabilities-Deep-Dive/crm-management/` -- GoHighLevel workflow automation
- `08-Capabilities-Deep-Dive/proactive-checkins/` -- Scheduled check-in capability (Telegram, 3-5x/day)

---

## Naming Conventions

**Files:**
- Hyphenated lowercase (e.g., `core-concepts.md`, `memory-architecture.md`)
- Phase files: `phase-N-name.md` (e.g., `phase-3-memory-rag.md`)
- Integration subdirectories: `service-name/` (e.g., `gohighlevel/`, `clay-enrichment/`)
- Capability subdirectories: `feature-name/` (e.g., `crm-management/`, `screen-database/`)

**Directories:**
- Section directories: `NN-Section-Name/` (zero-padded number + hyphenated title)
- Integration categories: `service-name/` (lowercase, hyphenated)
- Feature deep-dives: `feature-name/` (lowercase, hyphenated)
- Top-level metadata: Hidden (`.*`) for git/system files, root markdown files for navigation

**Markdown Headers:**
- H1: Document title (single per file)
- H2: Major sections (Architecture Overview, Gateway Server, etc.)
- H3: Subsections (WebSocket Server, Session Architecture, etc.)
- H4+: Detailed breakdowns (code examples, configuration snippets)

---

## Where to Add New Code

**Research Documentation:**
- New capability research: Create `08-Capabilities-Deep-Dive/{feature-name}/` directory with markdown files
- New integration guide: Create `06-Integrations/{service-name}/` directory with architecture + config + examples
- Phase updates: Add new phase file to `11-Implementation-Roadmap/phase-N.md`
- Example: To document a new feature, create folder and write markdown following existing capability patterns

**Configuration Files (When Agent Runs):**
- Agent definitions: `~/.openclaw/agents/{agent-name}.yaml` (YAML format)
- Skills: `~/.openclaw/skills/{skill-name}/skill.yaml` (manifest) + `prompts/`, `tools/`, `config/`
- Integrations: `~/.openclaw/config/integrations.json` (MCP server + API adapter configs)
- Memory config: `~/.openclaw/memory/config.yaml` (watch paths, vector model, search strategy)
- Permissions: `~/.openclaw/tool-permissions.yaml` or agent-level overrides

**Skill Development:**
- Location: `05-Skills-Development/` for research + tutorials
- Priority skills: `05-Skills-Development/priority-skills/` for 9 core skills
- Custom skill template: `skill.yaml` (manifest) + `prompts/system.md` + `tools/` (implementations) + `config/defaults.yaml`

---

## Special Directories

**`.planning/`:**
- Purpose: GSD project state and analysis
- Subdirectories:
  - `codebase/` -- Codebase analysis documents (ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md)
  - `sprints/` -- Active sprint files (to be created)
  - `archive/` -- Completed sprint history
- Contents: Machine-readable project state (current.md pointer, index.md master map, log.md standup log)
- Generated: Created by `/gsd:new-project`
- Committed: Yes (tracked in git)

**.git/**
- Purpose: Git version control
- Contents: Repository metadata, commit history, remote tracking
- Committed: Yes (git internals)
- Note: Push/pull via GitHub for cross-machine synchronization

**`04-Memory-and-RAG/sector-knowledge/`:**
- Purpose: Industry-specific knowledge for RAG ingestion
- Contents: Sector-specific markdown files (Plumbing, Solar, Dental, Legal)
- Generated: Manually researched and written
- Ingested: During Phase 3 (Memory & RAG) by agent memory system
- Pattern: File-first storage, hybrid-searchable by sector

**`.claude/` (on agent machine):**
- Purpose: Claude Code session memory and project state
- Contents: Session transcripts, memory files, project metadata
- Not git-tracked in OpenClaw-Research (separate Claude Code project)
- Interaction: Referenced in visibility-strategy.md (Layer 1 local watch)

---

## Document Organization Philosophy

**Layered Structure:**
1. **Master index** (README.md) -- Start here for navigation
2. **Section directories** (00-Foundation, 01-Mac-Mini-Setup, etc.) -- Grouped by topic
3. **Detailed guides** (phase files, capability deep-dives) -- Implementation instructions
4. **Analysis documents** (.planning/codebase/) -- Generated patterns and conventions

**Content Guidelines:**
- **Markdown-first:** All content authored in Markdown for readability and version control
- **Cross-referencing:** Links between related docs using relative paths
- **Examples before theory:** Code examples and concrete patterns before abstract concepts
- **Current state only:** Describes what IS, not what WAS or could be
- **Prescriptive language:** "Use X pattern" rather than "X pattern is used"

**For Future Implementation:**
- When adding new capabilities: Create `08-Capabilities-Deep-Dive/{name}/` with research + integration steps
- When adding new integrations: Create `06-Integrations/{service}/` with MCP patterns + config examples
- When updating implementation: Modify relevant phase files in `11-Implementation-Roadmap/`
- When documenting skills: Update `05-Skills-Development/{skill-name}/` with architecture + examples

---

*Structure analysis: 2026-02-27*

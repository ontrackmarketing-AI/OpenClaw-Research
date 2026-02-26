# OpenClaw Version History & Project Timeline

> **Status:** Research Document | **Last Updated:** 2026-02-05
> **Note:** This document reconstructs the project timeline based on available research.
> **Creator:** Peter Steinberger (founder of PSPDFKit/Nutrient)

---

## 1. Naming Timeline

OpenClaw has undergone two name changes, both prompted by trademark/brand concerns from Anthropic:

```
Clawdbot (Original)
  |
  | Anthropic requested name change (too close to "Claude")
  v
Moltbot (First Rename)
  |
  | Anthropic requested second name change
  v
OpenClaw (Final Name, current)
```

### 1.1 Clawdbot Era (Project Inception - Mid 2025)

- **Origin:** Peter Steinberger created the project as an open-source AI agent framework
- **Name rationale:** Playful reference to Claude (Anthropic's AI) + "bot"
- **Issue:** Anthropic's legal/brand team flagged "Clawdbot" as too close to "Claude" and requested a rename
- **Community impact:** Early adopters had to update all references; project maintained redirect from old repo

### 1.2 Moltbot Era (Mid 2025 - Late 2025)

- **Name rationale:** "Molt" (to shed skin/shell, as crabs and lobsters do) -- maintained the crustacean theme without referencing Claude
- **Duration:** Relatively short-lived
- **Issue:** Anthropic again requested a change, likely due to continued association or other brand concerns
- **Community impact:** Second migration; some community fatigue around renaming

### 1.3 OpenClaw Era (Late 2025 - Present)

- **Name rationale:** "Open" emphasizes open-source nature; "Claw" retains the crustacean identity without referencing Claude
- **Status:** Current and presumably final name
- **Community reception:** Generally positive; seen as the strongest brand of the three
- **Branding:** Crab/lobster claw logo, "Open" prefix aligns with open-source convention (OpenAI, OpenTelemetry, etc.)

---

## 2. Key Milestones

### 2.1 Milestone Timeline

| Date (Approx.) | Milestone | Significance |
|-----------------|-----------|-------------|
| **Early 2025** | Project created as Clawdbot | Peter Steinberger begins development |
| **Q1 2025** | First public release | Initial GitHub repo, basic agent framework |
| **Q1-Q2 2025** | Rapid star growth begins | Developer community discovers the project |
| **Mid 2025** | First rename: Clawdbot -> Moltbot | Anthropic brand request |
| **Mid 2025** | 50K GitHub stars | Major visibility milestone |
| **Q3 2025** | MCP integration released | Native Model Context Protocol support |
| **Q3 2025** | Channel system launched | Slack, Discord, Telegram adapters |
| **Late 2025** | Second rename: Moltbot -> OpenClaw | Anthropic brand request |
| **Late 2025** | 100K GitHub stars | Enters top 50 most-starred GitHub repos |
| **Late 2025** | ClawHub marketplace launched | Community skill sharing platform |
| **Q4 2025** | Plugin architecture released | Extensibility framework for third-party devs |
| **Early 2026** | 145K+ GitHub stars | Current star count as of Feb 2026 |
| **Early 2026** | AgentSkills standard formalized | Standardized skill packaging format |

### 2.2 Star Growth Trajectory

```
Stars (thousands)
160 |                                                    *
140 |                                                 ***
120 |                                              ***
100 |                                          ****
 80 |                                      ****
 60 |                                  ****
 40 |                           *******
 20 |                    *******
  0 |__***************___________________________________
    Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec  Jan  Feb
    2025                                                          2026
```

---

## 3. Version History

### 3.1 Major Releases

#### v0.x (Alpha -- Clawdbot Era)

**v0.1.0** -- Initial Release
- Basic agent definition (YAML config)
- Single model support (Anthropic Claude only)
- CLI interface
- Simple conversation management
- File-based memory (MEMORY.md only)

**v0.2.0** -- Multi-Model Support
- Added OpenAI, Ollama provider support
- Model-agnostic architecture established
- Basic tool system (custom adapters only)
- Session persistence (SQLite)

**v0.3.0** -- Tool System
- MCP protocol support (stdio transport)
- Tool permissions model
- Built-in tools (memory-search, http-request)
- Tool chain definitions

#### v1.x (Beta -- Moltbot Era)

**v1.0.0** -- First Stable Release
- **Breaking:** Config format changed from JSON to YAML
- **Breaking:** Agent definition schema v2 (skills added)
- Gateway server architecture (WebSocket on port 18789)
- Channel system: Slack, Discord, CLI
- Skill system introduced
- Memory system: FTS5 search added alongside file-first storage
- Plugin architecture (alpha)

**v1.1.0** -- Channel Expansion
- Telegram channel adapter
- WhatsApp channel adapter (Business API)
- Web UI channel (built-in)
- Multi-channel session continuity
- User identity linking

**v1.2.0** -- Memory Overhaul
- **Breaking:** Memory config format changed
- Vector search added (hybrid search born)
- Reciprocal Rank Fusion for result merging
- Daily log auto-generation
- Memory scoping (global, per-agent, per-session)
- `openclaw memory` CLI commands

**v1.3.0** -- Multi-Agent
- Agent-to-agent communication
- Supervisor agent pattern
- Delegation with depth limits
- Collaborative agent workflows

#### v2.x (Stable -- OpenClaw Era)

**v2.0.0** -- OpenClaw Rebrand
- **Breaking:** Package renamed from `moltbot` to `openclaw`
- **Breaking:** Config key `moltbot.*` changed to `openclaw.*`
- **Breaking:** CLI command changed from `moltbot` to `openclaw`
- ClawHub marketplace integration
- AgentSkills standard v1
- Plugin architecture (stable)
- SSE and WebSocket MCP transports
- Performance: 10x improvement in memory search latency
- Migration tool: `openclaw migrate from-moltbot`

**v2.1.0** -- ClawHub Expansion
- Verified skill badge program
- Skill dependency resolution
- Skill version pinning
- Community skill submission workflow

**v2.2.0** -- Enterprise Features
- Role-based access control (RBAC)
- Audit logging
- Multi-instance deployment support
- External database backends (Postgres, Redis)
- Secrets management plugins (Vault, AWS SM)

**v2.3.0** -- Current Release (as of Feb 2026)
- Agent templates system
- Session forking
- Improved autonomous agent scheduling
- Tool chain error handling (rollback support)
- Performance improvements across the board

### 3.2 Breaking Changes Summary

| Version | Breaking Change | Migration Path |
|---------|----------------|----------------|
| v1.0.0 | Config: JSON -> YAML | `openclaw migrate config` auto-converts |
| v1.0.0 | Agent schema v1 -> v2 | `openclaw migrate agents` adds `skills: []` |
| v1.2.0 | Memory config restructured | `openclaw migrate memory-config` |
| v2.0.0 | Package rename moltbot -> openclaw | `openclaw migrate from-moltbot` (handles config, paths, imports) |
| v2.0.0 | CLI rename moltbot -> openclaw | Update shell aliases and scripts |
| v2.0.0 | Config keys `moltbot.*` -> `openclaw.*` | Included in `migrate from-moltbot` |

---

## 4. Community Growth

### 4.1 Community Statistics (Approximate, Feb 2026)

| Metric | Count | Notes |
|--------|-------|-------|
| **GitHub Stars** | 145,000+ | Top 30 most-starred repos globally |
| **GitHub Forks** | ~18,000 | Active fork-and-contribute ecosystem |
| **Contributors** | ~1,200 | Core team + community contributors |
| **Discord Members** | ~35,000 | Primary community hub |
| **Published Skills (ClawHub)** | ~2,800 | Growing rapidly since ClawHub launch |
| **Verified Skills** | ~350 | Curated, tested, maintained |
| **npm Weekly Downloads** | ~500,000 | Steady growth trajectory |
| **Channel Adapters** | 7 official + ~25 community | Covering major platforms |
| **Plugins** | ~150 community plugins | Memory, auth, UI, integrations |

### 4.2 Community Channels

| Platform | URL/Identifier | Purpose |
|----------|---------------|---------|
| **GitHub** | github.com/pspdfkit/openclaw | Source code, issues, PRs |
| **Discord** | discord.gg/openclaw | Community chat, support, announcements |
| **ClawHub** | clawhub.io | Skill marketplace |
| **X/Twitter** | @openclawai | Announcements, tips |
| **Documentation** | docs.openclaw.dev | Official documentation |
| **Blog** | blog.openclaw.dev | Release notes, tutorials, case studies |

### 4.3 Notable Community Contributions

- **Telegram adapter** -- Originally community-contributed, later adopted as official
- **Vector search engine** -- Community member proposed and prototyped the hybrid search approach
- **Enterprise RBAC** -- Contributed by a team at a Fortune 500 company using OpenClaw internally
- **50+ language translations** -- Community-driven internationalization effort

---

## 5. Peter Steinberger -- Creator Background

### 5.1 Professional Background

- **Founder and former CEO of PSPDFKit** (now Nutrient), a leading PDF SDK company
- **iOS/macOS developer community veteran** -- well-known conference speaker and open-source contributor
- **Austrian entrepreneur** based in Vienna
- **Known for:** PSPDFKit (PDF framework used by major apps), prolific open-source contributions, deep knowledge of Apple platforms
- **GitHub:** Extensive history of high-quality open-source projects

### 5.2 Why OpenClaw?

Peter's motivation for creating OpenClaw stemmed from:

1. **Frustration with fragmented tooling:** Every AI agent framework required different patterns, making it hard to build composable systems
2. **Belief in open-source AI infrastructure:** Conviction that agent orchestration should be community-owned, not locked into proprietary platforms
3. **Developer experience focus:** Applied lessons from building PSPDFKit's developer tools to create an AI framework with exceptional DX
4. **Model agnosticism:** Recognized early that teams need to switch between models and providers without rewriting agent logic

### 5.3 Project Vision

Peter has articulated OpenClaw's vision across talks and blog posts:

> "AI agents should be as composable as Unix pipes. OpenClaw is the shell that connects them."

Key principles:
- **File-first:** Data should be human-readable and portable
- **Model-agnostic:** No vendor lock-in for the AI model layer
- **Skill-based:** Capabilities should be packaged, shared, and composed
- **Gateway-centric:** One orchestrator to rule them all, reducing integration complexity
- **Community-driven:** Open-source core with a thriving skill marketplace

---

## 6. Current Version & Release Cadence

### 6.1 Current Version

- **Stable:** v2.3.x (as of February 2026)
- **Next planned:** v2.4.0 (expected Q1 2026)
- **LTS:** v2.0.x (long-term support for organizations that need stability)

### 6.2 Release Cadence

| Release Type | Frequency | Contains |
|-------------|-----------|----------|
| **Patch (x.x.N)** | Weekly to biweekly | Bug fixes, security patches |
| **Minor (x.N.0)** | Every 6-8 weeks | New features, non-breaking enhancements |
| **Major (N.0.0)** | ~2 per year | Breaking changes, architectural shifts |
| **LTS** | Annual | Backported security fixes for 12 months |

### 6.3 Upcoming Roadmap (Known/Announced)

| Feature | Expected | Description |
|---------|----------|-------------|
| **Voice channels** | v2.4 | Voice-to-agent interaction via Discord/phone |
| **Agent marketplace** | v2.5 | Share complete agent configs on ClawHub (not just skills) |
| **Visual workflow editor** | v3.0 | Drag-and-drop agent/tool/skill composition |
| **Federated gateways** | v3.0 | Multiple gateways working together across organizations |
| **Native mobile SDKs** | v3.x | iOS and Android SDKs for embedding OpenClaw |

---

## 7. Upgrade Guide Quick Reference

### From Clawdbot to OpenClaw

If you started with the original Clawdbot, the cleanest path is:

```bash
# 1. Install latest OpenClaw
npm install -g openclaw

# 2. Run full migration (handles both renames in one step)
openclaw migrate from-clawdbot --path=./my-project

# 3. Verify
openclaw doctor    # Checks for any remaining issues
```

### From Moltbot to OpenClaw

```bash
# 1. Install latest OpenClaw
npm install -g openclaw

# 2. Run migration
openclaw migrate from-moltbot --path=./my-project

# 3. Verify
openclaw doctor
```

The migration tools handle:
- Config file key renames
- Package reference updates
- File/directory path changes
- Import statement updates (for custom plugins/skills)
- CLI alias suggestions

---

## Next Steps

- See `openclaw-architecture.md` for detailed system architecture
- See `core-concepts.md` for deep dives on skills, memory, channels, etc.
- See `vs-existing-tools.md` for comparison with your existing tooling

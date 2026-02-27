# Work Visibility Strategy: Two-Machine Architecture

## The Problem

How does OpenClaw see and access everything you work on -- code, documents, notes, research, media, designs, browser activity, conversations, and communications -- when your work lives on a **different machine** than the agent?

## The Setup

- **Agent machine (Mac Mini M4 Pro)**: Runs OpenClaw, memory system, Claude Code. This IS the agent. Rarely used directly by the human.
- **Work machine (Windows PC)**: Where the human does daily work. Code projects, browser, GHL, n8n, file editing, screen activity.
- **Cloud services**: GoHighLevel, Airtable, Clay, Supabase, GitHub -- accessible from either machine.

## Key Insight

**Git committing everything is NOT the universal answer.** It's right for ~20% of work (code + docs needing version history). For an agent machine that doesn't hold the work files, the strategy is even more cloud/API-centric.

---

## 4 Access Layers (Adapted for Two-Machine Setup)

### Layer 1: Local File Watch (Agent Machine Only)

**Scope:** Only files that live on this Mac.

**What's here:**
- `~/.openclaw/memory/**/*.md` -- OpenClaw's own memory and logs
- `~/OpenClaw-Research/**/*.md` -- The blueprint/research project
- `~/repos/**/*` -- Any git repos cloned here for agent work
- `~/.claude/projects/**/*.md` -- Claude Code session memory

**What's NOT here:** Most work files. They're on the Windows machine.

**Config:** `~/.openclaw/memory/config.yaml` → `watch_paths`

**How it works:**
- OpenClaw's file watcher detects changes and re-indexes automatically
- Files get extracted → cleaned → chunked → embedded → indexed into SQLite FTS5
- Default refresh: every 300 seconds

### Layer 2: Git Repos (Shared via GitHub)

**Scope:** Code projects and documentation that benefit from version history.

**How the bridge works:**
1. Human writes code on Windows, pushes to GitHub
2. Agent machine pulls from GitHub (or watches for pushes)
3. OpenClaw indexes the local clone via Layer 1 watch paths

**What to git-track:**
- OpenClaw-Research (already tracked -- the blueprint)
- GoHighLevel-MCP (clone to `~/repos/GoHighLevel-MCP`)
- rise-local-n8n config (clone to `~/repos/rise-local-n8n`)
- Any new code projects

**What NOT to git-track:**
- PDFs, images, large media (use cloud storage or Supabase)
- CRM data, lead lists (live API access is better)
- Browser activity (Screen DB handles this)

### Layer 3: MCP + API Connectors (Primary Access Method)

**Scope:** Cloud services, remote machine data, live SaaS tools.

This is the **dominant layer** for a two-machine setup. Since the agent can't watch remote files directly, it accesses remote work through APIs.

| Connector | What It Sees | Status |
|-----------|-------------|--------|
| **GoHighLevel MCP** | CRM contacts, pipelines, opportunities, campaigns | Built, needs connecting |
| **Airtable MCP** | Content calendar, lead tracking, project data | Active |
| **n8n MCP** | Automation workflows, execution logs | Running on Windows |
| **Supabase MCP** | Screen captures, vector embeddings, structured data | Paused |
| **Clay REST adapter** | Lead enrichment data | Planned |
| **GitHub** (git pull) | Code repos, PRs, issues | Standard git |
| **Screen Database** | OCR'd screenshots from Windows desktop | Phase 12 |
| **iMessage Relay** | Read-only message history from iMac | Phase 11 |

**Config:** `~/.openclaw/config/integrations.json`

**Future connectors (Phase 5+):**
- Google Drive MCP -- docs, spreadsheets, presentations
- Notion MCP -- if used for documentation
- Slack/Discord -- channel integrations for team comms
- Email MCP -- inbox monitoring and drafting

### Layer 4: MEMORY.md + Daily Logs (Automatic)

**Scope:** What OpenClaw has learned, patterns, preferences, active context.

This is built into OpenClaw's core and works automatically:
- `~/.openclaw/memory/MEMORY.md` -- loaded every session, updated with learned facts
- `~/.openclaw/memory/logs/YYYY/MM/DD.md` -- auto-generated daily activity logs
- SQLite index at `~/.openclaw/memory/index.db` -- searchable structured data

No special setup needed beyond the config files already created.

---

## What Goes Where: Quick Reference (Two-Machine Version)

| Work Type | Access Method | Lives On |
|-----------|--------------|----------|
| Code projects | Layer 2 (git) + Layer 1 (local clone) | Windows → GitHub → Mac |
| OpenClaw Research docs | Layer 1 (direct) + Layer 2 (git) | Mac (this machine) |
| CRM data (GHL) | Layer 3 (GHL MCP) | Cloud |
| Lead enrichment | Layer 3 (Clay API) | Cloud |
| Automation workflows | Layer 3 (n8n MCP) | Windows (via Tailscale) |
| Content calendar | Layer 3 (Airtable MCP) | Cloud |
| Browser activity | Layer 3 (Screen DB → Supabase) | Windows → Cloud |
| iMessage history | Layer 3 (iMessage relay) | iMac → Mac |
| Learned preferences | Layer 4 (automatic) | Mac (this machine) |
| PDFs, reports | Layer 1 (if synced) or Layer 3 (cloud) | Depends |
| Meeting notes | Layer 3 (cloud) or Layer 2 (git) | Depends |

---

## Bridging the Gap: Getting Files from Windows to Mac

For files that don't fit neatly into git or cloud APIs, there are 4 options (pick the one that fits your workflow):

### Option A: Tailscale + SSH/SFTP (Recommended)
- Both machines on Tailscale already (planned in Phase 2)
- Mount Windows folders via SSHFS over Tailscale
- OpenClaw reads remote files as if they were local
- **Pros:** No sync overhead, real-time access, works with any file type
- **Cons:** Requires Windows machine to be on

### Option B: Syncthing (For specific folders)
- Real-time bidirectional file sync between machines
- Sync specific project folders to `~/synced/` on Mac
- OpenClaw watches `~/synced/` via Layer 1
- **Pros:** Works offline, automatic, peer-to-peer
- **Cons:** Consumes disk on both machines, need to choose what to sync

### Option C: Cloud Storage MCP (For documents)
- Google Drive or OneDrive MCP connector
- OpenClaw queries documents via API without local copies
- **Pros:** No local storage needed, always current
- **Cons:** Requires internet, API rate limits

### Option D: Git repos (For code and text)
- Push from Windows, pull on Mac
- Already the standard for code projects
- **Pros:** Version history, standard workflow
- **Cons:** Only good for text-based files, manual push required

---

## Implementation Files

| File | Purpose | Location |
|------|---------|----------|
| `config.yaml` | Memory system config + watch paths | `~/.openclaw/memory/config.yaml` |
| `MEMORY.md` | Persistent agent memory | `~/.openclaw/memory/MEMORY.md` |
| `integrations.json` | MCP server + API adapter configs | `~/.openclaw/config/integrations.json` |
| `.env.template` | API key template (copy to .env) | `~/.openclaw/.env.template` |

---

## Related Documentation
- [Memory Architecture](memory-architecture.md) -- File-first memory system design
- [Knowledge Ingestion](knowledge-ingestion.md) -- Ingestion pipeline for all file types
- [Integration Architecture](../06-Integrations/integration-architecture.md) -- MCP + REST + webhook design
- [Screen Database](../08-Capabilities-Deep-Dive/screen-database/) -- Browser/screen capture pipeline
- [Phase 5: Integrations](../11-Implementation-Roadmap/phase-5-integrations.md) -- Integration rollout plan

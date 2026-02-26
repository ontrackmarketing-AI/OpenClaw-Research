# Migration Checklist: Windows to Mac Mini

> Track every step of the Windows -> Mac Mini migration.
> Check off items as you complete them. Add dates in the Notes column for audit trail.

---

## Phase 1: Pre-Migration Preparation

### 1.1 Inventory and Documentation

- [ ] Document all running services on Windows (ports, dependencies, startup order)
- [ ] Screenshot or export all n8n workflow configurations from `Desktop/rise-local-n8n`
- [ ] Export all n8n credentials (Settings > Export > include credentials)
- [ ] Document GoHighLevel MCP server configuration from `Desktop/GoHighLevel-MCP`
- [ ] List all Claude Code skills and their file locations (`clay-enrichment`, `lead-pipeline`, `supabase-ops`, `obsidian-helix`, `ghl-form-connect`, `smb-local-marketing`)
- [ ] Record current Ralph v0.9.9 configuration and any custom settings
- [ ] Export Airtable MCP server configuration (connection strings, base IDs)
- [ ] Document OnTrack Marketing stack: FastAPI config, Next.js env, PostgreSQL connection, Redis config, Qdrant collections
- [ ] Screenshot or note RAFE Obsidian vault structure and any custom plugins
- [ ] Record all current monthly costs and billing cycles for the $156-206/mo marketing stack
- [ ] Verify Supabase project status (jitawzicdwgbhatvjblh) -- confirm disabled, note any data to preserve

### 1.2 Backup Everything

- [ ] Full backup of `C:\Users\Owner\OneDrive\Desktop\GoHighLevel-MCP\` to external drive or cloud
- [ ] Full backup of `C:\Users\Owner\OneDrive\Desktop\rise-local-n8n\` to external drive or cloud
- [ ] Full backup of `C:\Users\Owner\OneDrive\Desktop\OpenClaw-Research\` to external drive or cloud
- [ ] Export all Airtable bases as CSV (for disaster recovery)
- [ ] Backup RAFE Obsidian vault (entire folder, including `.obsidian/` config)
- [ ] Backup Ralph configuration and any local state files
- [ ] Backup OnTrack Marketing codebase (git push all branches to remote)
- [ ] Export any local PostgreSQL databases (`pg_dump` for each database)
- [ ] Export Docker volumes if any contain persistent data
- [ ] Backup `.env` files from ALL projects (store securely, not in git)
- [ ] Backup Claude Code skill files and any associated configuration
- [ ] Verify all backups are complete and readable (spot-check 3-4 files)

### 1.3 Network and Access Preparation

- [ ] Determine Mac Mini's IP address (static IP recommended: System Settings > Network > Configure IPv4 > Manually)
- [ ] Ensure Mac Mini is on the same network as any local services it needs to reach
- [ ] Set up SSH access on Mac Mini: `sudo systemsetup -setremotelogin on`
- [ ] Test SSH from Windows: `ssh user@<mac-mini-ip>`
- [ ] Configure firewall rules on Mac Mini (System Settings > Network > Firewall)
- [ ] If using a domain, update DNS records to point to Mac Mini IP
- [ ] Verify outbound internet access from Mac Mini (API calls to Clay, GHL, Airtable, Anthropic, OpenAI)

---

## Phase 2: Data Transfer

### 2.1 Configuration Files

- [ ] Transfer all `.env` files via secure method (SCP or encrypted zip, NOT email/Slack)
  ```bash
  scp -r /path/to/env-files user@mac-mini-ip:~/migration/env-files/
  ```
- [ ] Transfer GoHighLevel MCP server code: `Desktop/GoHighLevel-MCP/` -> Mac Mini `~/Projects/GoHighLevel-MCP/`
- [ ] Transfer n8n data directory: `Desktop/rise-local-n8n/` -> Mac Mini `~/Projects/rise-local-n8n/`
- [ ] Transfer OpenClaw Research knowledge base (or sync via OneDrive)
- [ ] Transfer Claude Code skill definitions to Mac Mini `~/.claude/skills/` or equivalent
- [ ] Transfer RAFE Obsidian vault to Mac Mini (preserve folder structure exactly)

### 2.2 API Keys and Secrets

- [ ] Verify Anthropic API key works from Mac Mini: `curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages -d '{"model":"claude-sonnet-4-20250514","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'`
- [ ] Verify OpenAI API key works from Mac Mini
- [ ] Verify Clay.com API key works from Mac Mini
- [ ] Verify GoHighLevel API key works from Mac Mini
- [ ] Verify Airtable Personal Access Token works from Mac Mini
- [ ] Check if any API keys are IP-restricted (update allowed IPs if so)
- [ ] Update any webhook URLs that point to the Windows machine's IP to Mac Mini's IP
- [ ] Regenerate any secrets that should not be shared between machines (session keys, encryption keys)

### 2.3 Code Repositories

- [ ] Clone all git repositories to Mac Mini:
  ```bash
  cd ~/Projects
  git clone <ralph-repo-url>
  git clone <ontrack-marketing-repo-url>
  git clone <ghl-mcp-repo-url>
  git clone <openclaw-repo-url>
  ```
- [ ] Verify all branches and tags are present: `git branch -a` in each repo
- [ ] Confirm no uncommitted changes were left on Windows (check `git status` on Windows first)
- [ ] Transfer any local-only repos that are not on a remote (use `git bundle` or direct copy)

### 2.4 Database Data

- [ ] Export Windows PostgreSQL data (if any local databases):
  ```bash
  pg_dump -U postgres -F c ontrack_db > ontrack_db.dump
  pg_dump -U postgres -F c n8n_db > n8n_db.dump
  ```
- [ ] Transfer dump files to Mac Mini
- [ ] Note: Supabase data stays in the cloud (project jitawzicdwgbhatvjblh) -- no transfer needed
- [ ] Note: Airtable data stays in the cloud -- no transfer needed
- [ ] Export any Redis data that needs preservation (typically ephemeral, likely skip)
- [ ] Export Qdrant collections if OnTrack has trained embeddings:
  ```bash
  curl http://localhost:6333/collections/<collection>/points/scroll -d '{"limit":10000}' > qdrant_export.json
  ```

---

## Phase 3: Mac Mini Software Installation

### 3.1 System Basics

- [ ] Update macOS to latest version (System Settings > Software Update)
- [ ] Install Xcode Command Line Tools: `xcode-select --install`
- [ ] Install Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- [ ] Add Homebrew to PATH (follow post-install instructions for Apple Silicon):
  ```bash
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
  ```
- [ ] Install essential CLI tools: `brew install git curl wget jq htop`

### 3.2 Docker Environment

- [ ] Install Docker Desktop: `brew install --cask docker`
- [ ] Launch Docker Desktop and complete first-run setup
- [ ] Configure Docker resources (Docker Desktop > Settings > Resources):
  - [ ] CPUs: at least 4 (6+ recommended)
  - [ ] Memory: 8 GB minimum (12-16 GB recommended)
  - [ ] Swap: 2 GB
  - [ ] Disk image size: 64 GB minimum
- [ ] Enable Rosetta emulation for x86 images (Settings > General > Use Rosetta)
- [ ] Verify Docker works: `docker run hello-world`
- [ ] Install Docker Compose (included with Docker Desktop, verify): `docker compose version`

### 3.3 Runtime Environments

- [ ] Install Node.js 20 LTS: `brew install node@20`
- [ ] Verify: `node --version` (should show v20.x)
- [ ] Install Python 3.11: `brew install python@3.11`
- [ ] Verify: `python3.11 --version`
- [ ] Install pip packages globally or set up virtualenvs: `pip3 install virtualenv`
- [ ] Install Rust (if needed for any native builds): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### 3.4 AI and Agent Tools

- [ ] Install Claude CLI: `npm install -g @anthropic-ai/claude-code`
- [ ] Verify Claude CLI: `claude --version`
- [ ] Configure Claude CLI with API key: `claude config set api_key <key>`
- [ ] Install Ollama (for local LLM inference): `brew install ollama`
- [ ] Start Ollama: `ollama serve` (or set up as background service)
- [ ] Pull recommended models:
  ```bash
  ollama pull llama3.1:8b       # General purpose
  ollama pull mistral:7b        # Fast reasoning
  ollama pull nomic-embed-text  # Embeddings
  ```
- [ ] Verify Ollama: `ollama run llama3.1:8b "Hello, test"`

### 3.5 Database and Storage Tools

- [ ] PostgreSQL client (for connecting to databases): `brew install postgresql@16`
- [ ] Redis client: `brew install redis`
- [ ] Note: PostgreSQL server, Redis server, and Qdrant will run in Docker, not natively

### 3.6 Development Tools

- [ ] Install VS Code (optional, for remote editing): `brew install --cask visual-studio-code`
- [ ] Install Obsidian (for RAFE dashboard): `brew install --cask obsidian`
- [ ] Configure Obsidian to open the migrated RAFE vault
- [ ] Install any Obsidian community plugins that were active on Windows

---

## Phase 4: Service Reconfiguration

### 4.1 OpenClaw Platform (Docker)

- [ ] Clone OpenClaw repo to `~/Projects/openclaw/`
- [ ] Copy `.env` template and fill in all values (see QUICK-START.md)
- [ ] Run `docker compose pull` to download all images
- [ ] Start infrastructure: `docker compose up -d postgres redis qdrant`
- [ ] Wait 15 seconds, then start application: `docker compose up -d openclaw-api openclaw-web openclaw-worker`
- [ ] Run database migrations
- [ ] Create admin user
- [ ] Verify web UI loads at `http://localhost:8080`
- [ ] Run self-test: `docker compose exec openclaw-api python manage.py selftest`

### 4.2 N8N Workflows

- [ ] Start n8n container: `docker compose up -d n8n` (or standalone Docker)
- [ ] Access n8n at `http://localhost:5678`
- [ ] Import workflow JSON files from Windows backup
- [ ] Import credentials (or re-enter manually if export was not possible)
- [ ] Update all webhook URLs to use Mac Mini IP/hostname instead of Windows IP
- [ ] Test each workflow manually:
  - [ ] Rise Local lead creation workflow
  - [ ] Any scheduled/cron workflows
  - [ ] Any webhook-triggered workflows
- [ ] Activate all workflows once verified
- [ ] Register n8n with OpenClaw's workflow engine configuration

### 4.3 GoHighLevel MCP Server

- [ ] Navigate to `~/Projects/GoHighLevel-MCP/`
- [ ] Run `npm install` (recompiles native modules for macOS/ARM)
- [ ] Update `.env` with GHL API credentials
- [ ] Start the MCP server: `npm start` (or configure as Docker service)
- [ ] Test MCP operations:
  - [ ] List contacts
  - [ ] Create test contact
  - [ ] Delete test contact
- [ ] Register with OpenClaw MCP Bridge:
  ```json
  {
    "name": "ghl-mcp",
    "url": "http://localhost:<GHL_MCP_PORT>",
    "protocol": "mcp"
  }
  ```
- [ ] Verify OpenClaw can call GHL MCP tools

### 4.4 Airtable MCP

- [ ] Verify Airtable MCP is configured in OpenClaw's MCP Bridge config
- [ ] Test from OpenClaw: list bases, list tables, CRUD on a test record
- [ ] Verify all existing bases are accessible
- [ ] Confirm any automation that reads/writes Airtable still works end-to-end

### 4.5 Claude Code Skills Migration

- [ ] Copy skill files to Mac Mini Claude config directory
- [ ] Register each skill with OpenClaw's Skill Registry:
  - [ ] `clay-enrichment` -- test with a sample lead
  - [ ] `lead-pipeline` -- test full pipeline flow (use test data, not production)
  - [ ] `supabase-ops` -- test basic operations (low risk since Supabase is disabled)
  - [ ] `obsidian-helix` -- test read/write to RAFE vault
  - [ ] `ghl-form-connect` -- test form submission to GHL
  - [ ] `smb-local-marketing` -- test with a sample business profile
- [ ] Verify skills work both standalone (Claude CLI) and through OpenClaw agent pipelines

### 4.6 OnTrack Marketing Stack

- [ ] Clone OnTrack repo to `~/Projects/ontrack-marketing/`
- [ ] Set up Python virtualenv: `python3.11 -m venv venv && source venv/bin/activate`
- [ ] Install FastAPI dependencies: `pip install -r requirements.txt`
- [ ] Configure Next.js frontend: `cd frontend && npm install`
- [ ] Update `.env` files for both backend and frontend
- [ ] Start services (via Docker Compose or manually):
  - [ ] FastAPI backend on configured port
  - [ ] Next.js frontend on configured port
  - [ ] Verify PostgreSQL connection (shared with OpenClaw or separate)
  - [ ] Verify Redis connection
  - [ ] Verify Qdrant connection and existing collections
- [ ] Run OnTrack's test suite if available
- [ ] Register OnTrack API endpoints as OpenClaw tools

### 4.7 RAFE + Obsidian

- [ ] Open migrated RAFE vault in Obsidian on Mac Mini
- [ ] Verify all notes, sessions, decisions render correctly
- [ ] Test MCP tools: `get_doc`, `list_docs`, `update_doc`, `log_session`
- [ ] Verify RAFE MCP is registered with OpenClaw
- [ ] Run a test session log to confirm write operations work
- [ ] Check that all internal links (`[[...]]`) resolve correctly

---

## Phase 5: Post-Migration Verification

### 5.1 Smoke Tests (run ALL of these)

- [ ] **OpenClaw health:** `curl http://localhost:8080/health` returns healthy
- [ ] **Database:** Connect to PostgreSQL, run `SELECT 1;`
- [ ] **Redis:** `redis-cli ping` returns PONG
- [ ] **Qdrant:** `curl http://localhost:6333/collections` returns valid JSON
- [ ] **N8N:** All workflows show active status, test trigger one manually
- [ ] **GHL MCP:** List contacts succeeds
- [ ] **Airtable MCP:** List bases succeeds
- [ ] **Claude CLI:** `claude "Hello, test"` returns response
- [ ] **Ollama:** `ollama run llama3.1:8b "test"` returns response
- [ ] **OnTrack API:** `curl http://localhost:<port>/health` returns OK
- [ ] **OnTrack Frontend:** Opens in browser without errors
- [ ] **RAFE Obsidian:** Can read and write notes via MCP

### 5.2 Integration Tests

- [ ] **End-to-end lead pipeline:** Create a test lead -> Clay enrichment -> GHL push -> verify in GHL
- [ ] **Agent pipeline:** Ask OpenClaw to perform a multi-step task that uses 2+ tools
- [ ] **Workflow trigger:** Trigger an n8n webhook and verify it completes
- [ ] **Skill execution:** Run each Claude Code skill through OpenClaw and verify output
- [ ] **Memory/RAG:** Store data in OpenClaw memory, then retrieve it via semantic search
- [ ] **Cost tracking:** Verify API call logging is working (for cost optimization later)

### 5.3 Performance Baseline

- [ ] Record API response times for key operations:
  - [ ] OpenClaw agent task execution: ___ms
  - [ ] N8N workflow trigger to completion: ___ms
  - [ ] Clay.com enrichment call: ___ms
  - [ ] GHL contact creation: ___ms
  - [ ] Qdrant vector search: ___ms
- [ ] Record Docker resource usage: `docker stats --no-stream` (save output)
- [ ] Record Mac Mini system metrics: CPU%, Memory%, Disk% under load
- [ ] Compare performance to Windows baseline (if recorded)

### 5.4 Security Verification

- [ ] All `.env` files have restricted permissions: `chmod 600 .env` in each project
- [ ] No secrets committed to git: `git log --all --diff-filter=A -- "*.env"` returns nothing
- [ ] Docker containers are not running as root where avoidable
- [ ] Firewall only exposes necessary ports (80, 443, SSH)
- [ ] API keys have minimum required scopes (review each service)
- [ ] HTTPS configured for any externally-accessible endpoints

---

## Phase 6: Parallel Running Period (1-2 Weeks)

- [ ] Keep Windows machine running as fallback for 1-2 weeks
- [ ] Route 10% of traffic/tasks to Mac Mini initially, increase gradually
- [ ] Monitor error rates on Mac Mini vs Windows
- [ ] Log any discrepancies between the two environments
- [ ] After 1 week with zero issues, route 100% to Mac Mini
- [ ] After 2 weeks stable, proceed to Windows decommission

---

## Phase 7: Rollback Plan

> If critical issues arise after migration, follow this plan to restore service on Windows.

### Immediate Rollback (< 5 minutes)

- [ ] All original services still exist on Windows (nothing was deleted)
- [ ] To rollback: simply start services on Windows machine again
- [ ] Update any DNS/webhook URLs back to Windows IP
- [ ] Notify any dependent systems of the rollback

### Rollback Triggers (any of these = immediate rollback)

- Revenue-generating lead pipeline is down for > 30 minutes
- Data corruption detected in any database
- API key or security compromise detected
- More than 3 critical errors in first 24 hours that cannot be resolved

### Rollback Steps

1. [ ] Stop all services on Mac Mini: `docker compose down`
2. [ ] Start services on Windows (reverse of shutdown order)
3. [ ] Update webhook URLs to Windows IP
4. [ ] Verify Windows services are healthy (run smoke tests)
5. [ ] Document what went wrong and why
6. [ ] Create fix plan before attempting migration again
7. [ ] Do NOT delete any data on Mac Mini -- it may be useful for debugging

### Post-Rollback Recovery

- [ ] Root-cause the failure (check Mac Mini logs: `docker compose logs > migration-failure.log`)
- [ ] Fix the issue in a test environment first
- [ ] Re-attempt migration only after the fix is validated
- [ ] Consider incremental migration (one service at a time) if full migration failed

---

## Phase 8: Windows Decommission (After Successful Migration)

> Only proceed after 2+ weeks of stable Mac Mini operation.

- [ ] Final backup of Windows machine (full disk image recommended)
- [ ] Verify no services are still dependent on Windows machine
- [ ] Verify no cron jobs or scheduled tasks still run on Windows
- [ ] Transfer any remaining files (documents, media, etc.)
- [ ] Revoke any API keys that were Windows-specific
- [ ] Update documentation to reflect Mac Mini as primary
- [ ] Consider keeping Windows as cold backup for 30 more days
- [ ] After 30 days, repurpose or decommission Windows machine

---

## Migration Log

| Date | Phase | Action | Status | Notes |
|------|-------|--------|--------|-------|
| 2026-02-05 | Pre-migration | Created migration checklist | Done | |
| | | | | |
| | | | | |
| | | | | |

---

*Last updated: 2026-02-05*
*Total estimated migration time: 2-3 days of focused work + 2 weeks parallel running*

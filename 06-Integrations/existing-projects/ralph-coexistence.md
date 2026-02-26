# Ralph AI Dev Loop v0.9.9 -- Coexistence with OpenClaw

## Overview

Ralph is an autonomous AI development loop (v0.9.9) that handles code generation, testing, deployment, and git operations. OpenClaw is an autonomous business operations agent handling CRM, lead generation, presentations, client communication, and marketing. These two systems have complementary but occasionally overlapping domains. This document defines how they coexist on the same Mac Mini, communicate when needed, and how to handle the overlap zones.

---

## Role Separation Matrix

| Domain | Ralph | OpenClaw | Notes |
|---|---|---|---|
| Code generation | Primary | Never | Ralph writes application code, refactors, fixes bugs |
| Unit/integration testing | Primary | Never | Ralph runs test suites, writes test cases |
| Git operations | Primary | Never | Ralph commits, branches, merges, manages PRs |
| CI/CD deployment | Primary | Never | Ralph triggers builds, monitors pipelines |
| Code refactoring | Primary | Never | Ralph handles architecture decisions in code |
| CRM management | Never | Primary | OpenClaw manages GHL, client records, deal stages |
| Lead generation | Never | Primary | OpenClaw runs Rise Local pipeline, enrichment, outreach |
| Presentation creation | Never | Primary | OpenClaw generates slide decks, proposals |
| Client communication | Never | Primary | OpenClaw drafts emails, manages follow-ups |
| Marketing campaigns | Never | Primary | OpenClaw plans, executes, tracks marketing |
| Content writing | Never | Primary | OpenClaw generates blog posts, social content, emails |
| Website building | Overlap | Overlap | See resolution below |
| Data analysis | Secondary | Primary | OpenClaw leads; Ralph assists with data pipeline code |
| API integration | Secondary | Primary | OpenClaw designs integrations; Ralph writes adapter code |
| Documentation | Secondary | Primary | OpenClaw writes docs; Ralph generates API docs from code |

### Resolving the Website Building Overlap

Both Ralph and OpenClaw can build websites, but they approach it differently:

- **Ralph's approach:** Writes code from scratch or scaffolds frameworks (Next.js, React, etc.). Better for custom web applications with complex logic, authentication, database interactions.
- **OpenClaw's approach:** Uses templates, low-code builders, or generates static sites. Better for landing pages, marketing sites, portfolio sites, simple client websites.

**Decision rule:**
- If the site requires a backend, database, or custom application logic -> **Ralph builds it**
- If the site is primarily presentational (landing page, marketing site, brochure site) -> **OpenClaw builds it**
- If unclear, default to **OpenClaw** for the initial version (faster delivery), then hand off to **Ralph** if it needs to evolve into a full application

---

## Running Simultaneously on Mac Mini

### Resource Allocation

**Mac Mini specs assumption:** M2/M4 with 16-32 GB unified memory, 256-512 GB SSD.

| Resource | Ralph Allocation | OpenClaw Allocation | System Reserve |
|---|---|---|---|
| RAM (16 GB total) | 5 GB | 5 GB | 6 GB (OS + services) |
| RAM (32 GB total) | 10 GB | 10 GB | 12 GB (OS + services) |
| CPU cores | 4 performance cores | 4 efficiency cores | Shared as needed |
| Disk I/O | Standard priority | Standard priority | -- |
| Network | Unrestricted | Unrestricted | -- |
| GPU (Neural Engine) | Low priority | Low priority | Available for local LLM inference |

### Process Management

**Option A: Docker Compose (Recommended)**

Both Ralph and OpenClaw run as Docker containers with resource limits defined in `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ralph:
    build: ./ralph
    container_name: ralph-dev-loop
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 5G
          cpus: '4.0'
    volumes:
      - ./ralph-workspace:/workspace
      - ./shared-data:/shared  # Shared filesystem
      - /var/run/docker.sock:/var/run/docker.sock  # If Ralph needs Docker access
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    networks:
      - agent-network

  openclaw:
    build: ./openclaw
    container_name: openclaw-agent
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 5G
          cpus: '4.0'
    volumes:
      - ./openclaw-workspace:/workspace
      - ./shared-data:/shared  # Shared filesystem
    ports:
      - "8080:8080"  # OpenClaw web UI if applicable
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - GHL_API_KEY=${GHL_API_KEY}
      - AIRTABLE_PAT=${AIRTABLE_PAT}
    networks:
      - agent-network

  n8n:
    image: n8nio/n8n
    container_name: n8n-middleware
    restart: unless-stopped
    ports:
      - "5678:5678"
    volumes:
      - ./n8n-data:/home/node/.n8n
      - ./shared-data:/shared
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASS}
    networks:
      - agent-network

networks:
  agent-network:
    driver: bridge
```

**Option B: Native processes with launchd**

If not using Docker, use macOS `launchd` plists to manage both as background services with resource limits via `ulimit` and process priority via `nice`.

### Monitoring Resource Usage

Set up a lightweight monitoring script that checks every 60 seconds:

```bash
#!/bin/bash
# monitor-agents.sh -- runs via cron every minute

RALPH_MEM=$(docker stats ralph-dev-loop --no-stream --format "{{.MemUsage}}" | cut -d'/' -f1)
OPENCLAW_MEM=$(docker stats openclaw-agent --no-stream --format "{{.MemUsage}}" | cut -d'/' -f1)

# Log to shared location
echo "$(date -Iseconds) | Ralph: $RALPH_MEM | OpenClaw: $OPENCLAW_MEM" >> /shared/resource-log.csv

# Alert if either exceeds 80% of limit
# (implement threshold check and Slack notification here)
```

---

## Communication Between Ralph and OpenClaw

### Channel 1: Shared Filesystem

**Path:** `/shared` (mounted in both containers)

**Structure:**
```
/shared/
  ralph-to-openclaw/
    pending/        # Ralph drops files here
    processed/      # OpenClaw moves files here after reading
  openclaw-to-ralph/
    pending/        # OpenClaw drops files here
    processed/      # Ralph moves files here after reading
  schemas/          # Shared JSON schemas for message formats
  logs/             # Shared activity logs
```

**Message format (JSON):**
```json
{
  "id": "msg-20260205-001",
  "from": "ralph",
  "to": "openclaw",
  "timestamp": "2026-02-05T14:30:00Z",
  "type": "notification",
  "priority": "normal",
  "subject": "deployment_complete",
  "payload": {
    "project": "ontrack-marketing",
    "version": "2.1.0",
    "environment": "staging",
    "url": "https://staging.ontrack.example.com",
    "changelog": "Added new analytics endpoint, fixed auth bug"
  }
}
```

**Polling:** Each agent checks its `pending/` directory every 30 seconds. File-based communication is simple, reliable, and requires no additional infrastructure.

### Channel 2: n8n as Middleware (Preferred for Complex Workflows)

n8n acts as the routing layer between Ralph and OpenClaw:

**Pattern 1: Ralph triggers OpenClaw action**
```
Ralph writes to filesystem -> n8n File Trigger watches directory
  -> n8n parses message -> n8n calls OpenClaw webhook
  -> OpenClaw performs action (e.g., notify client of deployment)
  -> OpenClaw returns result to n8n -> n8n logs result
```

**Pattern 2: OpenClaw triggers Ralph action**
```
OpenClaw needs code change -> OpenClaw calls n8n webhook
  -> n8n validates request -> n8n writes task file to Ralph's pending directory
  -> Ralph picks up task -> Ralph executes (code gen, test, deploy)
  -> Ralph writes completion message -> n8n routes back to OpenClaw
```

**Pattern 3: Coordinated workflow (e.g., new client onboarding)**
```
New client signed (GHL webhook to n8n)
  -> n8n Step 1: OpenClaw creates Airtable base, sets up CRM record
  -> n8n Step 2: Ralph scaffolds client project repo, deploys staging site
  -> n8n Step 3: OpenClaw sends welcome email with staging link
  -> n8n Step 4: Both agents log to RAFE Obsidian via n8n
```

**Key n8n workflows to build:**

| Workflow Name | Trigger | Ralph Action | OpenClaw Action |
|---|---|---|---|
| New Client Onboard | GHL webhook | Scaffold repo, deploy staging | Create Airtable base, send welcome email |
| Deployment Notification | Ralph filesystem write | (source) | Notify client, update CRM |
| Bug Report Intake | OpenClaw receives client email | Create issue, start fix | Acknowledge to client, track in CRM |
| Weekly Status | Cron (Monday 8 AM) | Generate code metrics | Generate business metrics, compile report |
| Website Request | Client request via GHL | Build if complex app | Build if landing page |

### Channel 3: Supabase as Shared Database

**Shared tables in Supabase:**

```sql
-- Table for inter-agent task requests
CREATE TABLE agent_tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    from_agent TEXT NOT NULL CHECK (from_agent IN ('ralph', 'openclaw', 'human')),
    to_agent TEXT NOT NULL CHECK (to_agent IN ('ralph', 'openclaw', 'human')),
    task_type TEXT NOT NULL,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'in_progress', 'completed', 'failed', 'cancelled')),
    payload JSONB NOT NULL DEFAULT '{}',
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accepted_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- Table for shared state
CREATE TABLE agent_state (
    agent_name TEXT PRIMARY KEY,
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'busy', 'error', 'offline')),
    current_task UUID REFERENCES agent_tasks(id),
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    capabilities JSONB DEFAULT '[]',
    resource_usage JSONB DEFAULT '{}'
);

-- Table for shared knowledge/context
CREATE TABLE shared_context (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    context_type TEXT NOT NULL,  -- 'client', 'project', 'decision', 'metric'
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(context_type, key)
);

-- Enable realtime for task notifications
ALTER PUBLICATION supabase_realtime ADD TABLE agent_tasks;
ALTER PUBLICATION supabase_realtime ADD TABLE agent_state;
```

**Usage pattern:**
- Ralph and OpenClaw both subscribe to `agent_tasks` via Supabase Realtime
- When a new task appears with `to_agent = 'ralph'`, Ralph picks it up
- Heartbeat: each agent updates `agent_state.last_heartbeat` every 60 seconds
- If heartbeat is stale (> 5 minutes), n8n triggers an alert

---

## Migration Path: Consolidation Options

### Option A: Keep Both (Recommended for Now)

**Rationale:**
- Ralph is optimized for code development workflows (v0.9.9 is mature)
- OpenClaw is optimized for business operations workflows
- Forcing one system to do both creates a jack-of-all-trades, master-of-none
- The communication layer (n8n + Supabase) is lightweight and reliable
- Total resource footprint is manageable on a Mac Mini with 32 GB RAM

**When to re-evaluate:** After 3 months of running both. Metrics to track:
- How often do they need to communicate? (If rarely, keep separate. If constantly, consider merging.)
- Are there tasks that fall through the cracks between them?
- Is the Mac Mini running out of resources?

### Option B: Migrate Ralph Capabilities into OpenClaw

**When this makes sense:**
- OpenClaw's skill system matures enough to handle code generation well
- You want a single agent that does everything
- Resource constraints force consolidation

**Migration steps:**
1. Create OpenClaw skills that replicate Ralph's core capabilities:
   - `skill_code_generate`: wraps Claude API with coding system prompts
   - `skill_git_operations`: wraps git CLI commands
   - `skill_test_runner`: wraps pytest/vitest/etc.
   - `skill_deploy`: wraps Docker/CI commands
2. Run both in parallel for 2 weeks, comparing output quality
3. Gradually shift tasks from Ralph to OpenClaw skills
4. Decommission Ralph when all tasks are handled by OpenClaw

**Risk:** OpenClaw may not match Ralph's depth in code development workflows. Ralph v0.9.9 has nearly a full version of iteration on code-specific heuristics.

### Option C: Migrate OpenClaw Capabilities into Ralph

**When this makes sense:**
- Ralph is clearly the stronger agent
- Business operations can be handled as "just another type of code/automation task"

**This is not recommended** because Ralph's architecture is optimized for code, not for multi-channel business communication, CRM management, and client-facing operations.

---

## Operational Runbook

### Starting Both Agents

```bash
# From the project root
docker compose up -d

# Verify both are running
docker compose ps

# Check logs
docker compose logs -f ralph-dev-loop
docker compose logs -f openclaw-agent
```

### Stopping Gracefully

```bash
# Stop OpenClaw first (business operations can wait)
docker compose stop openclaw-agent

# Wait for Ralph to finish current task
docker compose exec ralph-dev-loop cat /workspace/.current-task
# If idle:
docker compose stop ralph-dev-loop

# Stop everything
docker compose down
```

### Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Both agents slow | RAM exhaustion | Check `docker stats`, reduce memory limits, restart the one with memory leak |
| Messages not flowing | n8n down or misconfigured | Check n8n UI at localhost:5678, verify webhook URLs |
| Ralph not picking up tasks | Polling stopped | Restart Ralph container; check `/shared/openclaw-to-ralph/pending/` for stuck files |
| OpenClaw not responding | API rate limit or crash | Check OpenClaw logs; verify Anthropic API key has quota |
| Supabase connection errors | Network or auth issue | Verify `SUPABASE_URL` and `SUPABASE_KEY` env vars; check Supabase dashboard status |

### Health Check Endpoints

Set up simple health check endpoints for both agents:

```python
# Each agent exposes a /health endpoint
# n8n periodically pings both

# Expected response:
{
    "agent": "ralph",  # or "openclaw"
    "status": "healthy",
    "version": "0.9.9",
    "uptime_seconds": 86400,
    "current_task": null,  # or task description
    "memory_usage_mb": 3200,
    "last_activity": "2026-02-05T14:25:00Z"
}
```

---

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-02-05 | Keep Ralph and OpenClaw as separate systems | Different strengths; communication layer is lightweight; Mac Mini has sufficient resources |
| 2026-02-05 | Use n8n as primary communication middleware | Already deployed; visual workflow builder; handles webhooks natively |
| 2026-02-05 | Supabase as shared database | Already used by Rise Local; real-time subscriptions enable responsive task routing |
| 2026-02-05 | Website building: OpenClaw for landing pages, Ralph for apps | Clear domain split avoids conflict; decision rule is simple to apply |

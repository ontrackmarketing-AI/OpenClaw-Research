# Phase 5 - Integrations (Week 4-5)

## Goal

Connect OpenClaw to every tool in your existing ecosystem so data flows bidirectionally between systems. By the end of this phase, n8n can trigger OpenClaw skills, OpenClaw can query Airtable, Rise Local pipeline runs through OpenClaw, and Ralph/RAFE coexist peacefully on the same machine.

---

## Integration Architecture Overview

```
                    +-------------------+
                    |    OpenClaw        |
                    |  (Mac Mini M4 Pro) |
                    +--------+----------+
                             |
       +---------------------+---------------------+
       |         |           |          |           |
   +---v---+ +---v---+ +----v----+ +---v---+ +----v----+
   |  n8n  | |Airtable| |Supabase| |  GHL  | | Ralph/  |
   |       | |       | |        | |       | | RAFE    |
   +---+---+ +-------+ +--------+ +-------+ +---------+
       |
       v
  Rise Local Pipeline
```

Each integration follows the same pattern:
1. Configure the connection (API keys, MCP server, webhook URL)
2. Test basic operations (CRUD, read/write)
3. Build bidirectional workflows
4. Set up error handling and monitoring
5. Document the integration

---

## Day 1-2: n8n Integration

### Connect n8n MCP to OpenClaw

Your n8n instance is already running. Now connect it to OpenClaw for bidirectional communication.

#### OpenClaw triggering n8n workflows

```bash
mkdir -p ~/.openclaw/skills/n8n-integration

cat > ~/.openclaw/skills/n8n-integration/config.json << 'JSON'
{
  "skill_name": "n8n-integration",
  "description": "Trigger and manage n8n automation workflows from OpenClaw",
  "version": "1.0.0",
  "connection": {
    "n8n_base_url": "http://localhost:5678",
    "n8n_api_key": "${N8N_API_KEY}",
    "webhook_base_url": "http://localhost:5678/webhook"
  },
  "workflows": {
    "rise_local_pipeline": {
      "webhook_path": "/webhook/rise-local-trigger",
      "description": "Trigger the Rise Local lead discovery pipeline",
      "input_schema": {
        "industry": "string",
        "location": "string",
        "max_leads": "number"
      }
    },
    "daily_report": {
      "webhook_path": "/webhook/daily-report",
      "description": "Generate and send daily operations report",
      "input_schema": {
        "report_type": "string",
        "date": "string"
      }
    },
    "content_publish": {
      "webhook_path": "/webhook/content-publish",
      "description": "Publish content to social media channels",
      "input_schema": {
        "content": "string",
        "channels": "array",
        "schedule_time": "string"
      },
      "hitl_required": true
    }
  }
}
JSON
```

#### n8n triggering OpenClaw skills

Create a webhook endpoint in OpenClaw that n8n can call:

```bash
# Add n8n API key to .env
cat >> ~/.openclaw/.env << 'ENV'

# n8n Integration
N8N_API_KEY=your-n8n-api-key-here
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_SECRET=generate-a-shared-secret-here
ENV
```

#### Build n8n Workflow: n8n -> OpenClaw

In n8n, create a workflow with these nodes:

1. **Webhook Trigger** (receives external events)
2. **HTTP Request** node pointing to OpenClaw:
   - URL: `http://localhost:18789/api/skills/invoke`
   - Method: POST
   - Headers: `Authorization: Bearer ${OPENCLAW_AUTH_SECRET}`
   - Body:
     ```json
     {
       "skill": "lead-enrichment",
       "action": "enrichLead",
       "params": {
         "business_name": "{{$json.business_name}}",
         "location": "{{$json.location}}"
       }
     }
     ```
3. **IF** node (check enrichment score)
4. **GHL** node (create contact if score is warm/hot)
5. **Slack/Telegram** notification node

#### Test Bidirectional Communication

```bash
# Test: OpenClaw -> n8n (trigger a workflow)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Trigger the Rise Local pipeline for plumbers in Houston, TX, max 10 leads"}'

# Verify: Check n8n execution history at http://localhost:5678

# Test: n8n -> OpenClaw (trigger a skill via webhook)
curl -X POST http://localhost:18789/api/skills/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-auth-secret" \
  -d '{"skill": "lead-enrichment", "action": "enrichLead", "params": {"business_name": "Test Plumbing", "location": "Houston, TX"}}'
```

#### Configure Error Handling

```bash
cat > ~/.openclaw/skills/n8n-integration/error-handling.json << 'JSON'
{
  "retry_policy": {
    "max_retries": 3,
    "backoff_ms": [1000, 5000, 15000],
    "retry_on": ["timeout", "5xx", "connection_refused"]
  },
  "dead_letter": {
    "enabled": true,
    "store_in": "sqlite",
    "alert_after": 3,
    "notification_channel": "telegram"
  },
  "monitoring": {
    "log_all_requests": true,
    "alert_on_failure_rate": 0.1,
    "health_check_interval_seconds": 60
  }
}
JSON
```

---

## Day 3-4: Airtable Integration

### Verify Airtable MCP Connection

Your Airtable MCP is already configured. Verify it works with OpenClaw.

```bash
# Test: List all bases
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all my Airtable bases"}'

# Test: Read records from an existing base
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the last 5 records from my [base name] table"}'
```

### Set Up Content Calendar Base

If you do not already have a content calendar in Airtable, create one:

```bash
# Create via Airtable MCP or manually in Airtable UI
# Required tables and fields:

# Table: Content Calendar
# Fields:
#   - Title (single line text)
#   - Type (single select: blog, social, email, video)
#   - Status (single select: idea, drafting, review, scheduled, published)
#   - Channel (multi-select: website, facebook, instagram, linkedin, email)
#   - Publish Date (date)
#   - Author (single line text)
#   - Content (long text)
#   - Client (linked record to Clients table)
#   - Notes (long text)
#   - Created By (single line text: "manual" or "openclaw")

# Table: Clients
# Fields:
#   - Name (single line text)
#   - Industry (single select: plumbing, solar, dental, legal, other)
#   - GHL Contact ID (single line text)
#   - Status (single select: active, inactive, prospect)
#   - Monthly Budget (currency)
```

### Build Content Calendar Skill

```bash
mkdir -p ~/.openclaw/skills/content-calendar

cat > ~/.openclaw/skills/content-calendar/config.json << 'JSON'
{
  "skill_name": "content-calendar",
  "description": "Manage content calendar in Airtable: create, schedule, and track content",
  "version": "1.0.0",
  "airtable": {
    "base_name": "Marketing Operations",
    "table_name": "Content Calendar",
    "clients_table": "Clients"
  },
  "capabilities": [
    {
      "name": "add_content",
      "description": "Add a new content item to the calendar",
      "hitl_required": false,
      "params": ["title", "type", "channel", "publish_date", "client"]
    },
    {
      "name": "schedule_content",
      "description": "Schedule existing content for a specific date",
      "hitl_required": false,
      "params": ["record_id", "publish_date"]
    },
    {
      "name": "generate_content_ideas",
      "description": "Generate content ideas for a client based on their industry and RAG data",
      "hitl_required": false,
      "params": ["client", "count", "channels"]
    },
    {
      "name": "weekly_content_report",
      "description": "Show this week's content schedule",
      "hitl_required": false,
      "params": ["week_start"]
    },
    {
      "name": "publish_content",
      "description": "Mark content as published and trigger distribution",
      "hitl_required": true,
      "params": ["record_id"]
    }
  ]
}
JSON
```

### Test Content Calendar Operations

```bash
# Test: Add content
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a blog post to next weeks content calendar: \"5 Signs You Need a New Water Heater\" for ABC Plumbing, to be published on the website and Facebook"}'

# Test: Generate content ideas
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate 5 blog post ideas for a plumbing company targeting homeowners. Add them all to the content calendar as ideas."}'

# Test: Weekly report
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me what content is scheduled for this week across all clients"}'
```

---

## Day 5-6: Supabase Integration

### Verify Supabase MCP Connection

Supabase was reactivated in Phase 3. Now build operational database capabilities.

```bash
# Test basic Supabase connectivity
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Query the Supabase documents table and tell me how many records are stored"}'
```

### Build Database Operations Skill

```bash
mkdir -p ~/.openclaw/skills/database-ops

cat > ~/.openclaw/skills/database-ops/config.json << 'JSON'
{
  "skill_name": "database-ops",
  "description": "Manage data in Supabase: queries, analytics, data sync",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "query",
      "description": "Run a read-only query against Supabase",
      "hitl_required": false,
      "allowed_tables": ["documents", "enrichment_results", "pipeline_runs", "cost_tracking"]
    },
    {
      "name": "insert",
      "description": "Insert records into Supabase",
      "hitl_required": "batch_size > 50",
      "allowed_tables": ["documents", "enrichment_results", "pipeline_runs", "cost_tracking"]
    },
    {
      "name": "analytics",
      "description": "Run analytics queries (aggregations, trends)",
      "hitl_required": false
    },
    {
      "name": "backup_before_write",
      "description": "Automatically create a snapshot before destructive operations",
      "auto_trigger": true,
      "applies_to": ["update", "delete"]
    }
  ],
  "tables": {
    "enrichment_results": {
      "description": "Stored lead enrichment data",
      "columns": ["id", "business_name", "location", "enrichment_data", "score", "tier", "cost", "created_at"]
    },
    "pipeline_runs": {
      "description": "Pipeline execution history",
      "columns": ["id", "pipeline_name", "status", "leads_found", "leads_enriched", "leads_qualified", "total_cost", "started_at", "completed_at"]
    },
    "cost_tracking": {
      "description": "API cost tracking by service, skill, and date",
      "columns": ["id", "service", "skill", "operation", "cost", "timestamp"]
    }
  }
}
JSON
```

### Create Supabase Tables

Run these in Supabase SQL Editor:

```sql
-- Enrichment results table
CREATE TABLE enrichment_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_name TEXT NOT NULL,
  location TEXT,
  enrichment_data JSONB DEFAULT '{}',
  score INTEGER,
  tier TEXT CHECK (tier IN ('hot', 'warm', 'cold')),
  cost DECIMAL(10,4) DEFAULT 0,
  ghl_contact_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pipeline runs tracking
CREATE TABLE pipeline_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_name TEXT NOT NULL,
  trigger_source TEXT, -- 'manual', 'scheduled', 'n8n', 'openclaw'
  status TEXT CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
  leads_found INTEGER DEFAULT 0,
  leads_enriched INTEGER DEFAULT 0,
  leads_qualified INTEGER DEFAULT 0,
  total_cost DECIMAL(10,4) DEFAULT 0,
  error_message TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Cost tracking
CREATE TABLE cost_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service TEXT NOT NULL, -- 'anthropic', 'clay', 'zerobounce', 'google_places'
  skill TEXT, -- 'lead-enrichment', 'crm-management', etc.
  operation TEXT, -- 'chat', 'enrich', 'verify_email', etc.
  cost DECIMAL(10,4) NOT NULL,
  metadata JSONB DEFAULT '{}',
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_enrichment_tier ON enrichment_results(tier);
CREATE INDEX idx_enrichment_created ON enrichment_results(created_at);
CREATE INDEX idx_pipeline_status ON pipeline_runs(status);
CREATE INDEX idx_cost_service ON cost_tracking(service);
CREATE INDEX idx_cost_timestamp ON cost_tracking(timestamp);
CREATE INDEX idx_cost_skill ON cost_tracking(skill);

-- Useful view: daily cost summary
CREATE VIEW daily_costs AS
SELECT
  DATE(timestamp) as date,
  service,
  skill,
  COUNT(*) as operations,
  SUM(cost) as total_cost
FROM cost_tracking
GROUP BY DATE(timestamp), service, skill
ORDER BY date DESC, total_cost DESC;
```

### Test Database Operations

```bash
# Test: Insert enrichment result
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Log this enrichment result to Supabase: ABC Plumbing in Austin, TX scored 72 (hot tier), cost $0.06"}'

# Test: Query analytics
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my total enrichment cost this week? Break it down by service."}'

# Test: Pipeline tracking
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all pipeline runs from the last 7 days with their status and lead counts"}'
```

---

## Day 7-8: Rise Local Pipeline Integration

### Connect Rise Local to OpenClaw

The Rise Local lead pipeline currently runs through n8n. Now route it through OpenClaw for intelligent decision-making at each step.

```bash
cat > ~/.openclaw/skills/rise-local/config.json << 'JSON'
{
  "skill_name": "rise-local-pipeline",
  "description": "Automated lead discovery, enrichment, and qualification for local service businesses",
  "version": "2.0.0",
  "pipeline_stages": [
    {
      "stage": "discovery",
      "description": "Find businesses matching target criteria",
      "trigger": "manual or scheduled",
      "tools": ["google_places"],
      "output": "list of business names + basic info"
    },
    {
      "stage": "enrichment",
      "description": "Waterfall enrichment of discovered businesses",
      "trigger": "auto after discovery",
      "tools": ["lead-enrichment skill"],
      "output": "enriched lead data + score"
    },
    {
      "stage": "qualification",
      "description": "AI-powered qualification based on score + RAG context",
      "trigger": "auto after enrichment",
      "tools": ["llm + rag"],
      "output": "qualified/disqualified with reasoning"
    },
    {
      "stage": "crm_entry",
      "description": "Create qualified leads as contacts in GHL",
      "trigger": "auto after qualification (hot/warm only)",
      "tools": ["crm-management skill"],
      "output": "GHL contact IDs"
    },
    {
      "stage": "outreach_prep",
      "description": "Generate personalized outreach materials",
      "trigger": "auto for hot leads only",
      "tools": ["presentation-gen skill", "llm"],
      "output": "pitch deck + personalized email draft",
      "hitl_required": true
    }
  ],
  "scheduling": {
    "enabled": true,
    "cron": "0 8 * * 1-5",
    "description": "Run weekdays at 8 AM",
    "default_params": {
      "industries": ["plumbing", "solar"],
      "locations": ["Austin, TX", "Dallas, TX", "Houston, TX"],
      "max_leads_per_run": 20
    }
  },
  "cost_limits": {
    "per_run": 10.00,
    "daily": 25.00,
    "monthly": 500.00
  }
}
JSON
```

### Map Pipeline to n8n Webhooks

Create n8n workflow nodes that OpenClaw orchestrates:

```bash
# Pipeline orchestration flow:
# 1. OpenClaw receives "run pipeline" command
# 2. OpenClaw calls n8n webhook to trigger Google Places discovery
# 3. n8n returns discovered businesses to OpenClaw
# 4. OpenClaw runs enrichment skill on each lead
# 5. OpenClaw scores and qualifies leads
# 6. OpenClaw creates GHL contacts for qualified leads
# 7. OpenClaw generates outreach materials for hot leads
# 8. OpenClaw sends HITL notification for outreach approval
# 9. All results logged to Supabase

# Test the full pipeline
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Run the Rise Local pipeline for plumbers in San Antonio, TX. Find up to 10 businesses, enrich them, and create contacts for any that score warm or hot."}'
```

### Configure Automated Daily Runs

```bash
# Create a cron job on the Mac Mini for daily pipeline execution
# (Or use n8n's built-in scheduling)

# Option 1: macOS launchd
cat > ~/Library/LaunchAgents/com.openclaw.daily-pipeline.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.daily-pipeline</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/curl</string>
        <string>-X</string>
        <string>POST</string>
        <string>http://localhost:18789/api/skills/invoke</string>
        <string>-H</string>
        <string>Content-Type: application/json</string>
        <string>-d</string>
        <string>{"skill": "rise-local-pipeline", "action": "run", "params": {"use_defaults": true}}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw-pipeline.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw-pipeline-error.log</string>
</dict>
</plist>
PLIST

# Load the schedule
launchctl load ~/Library/LaunchAgents/com.openclaw.daily-pipeline.plist

# Verify it's scheduled
launchctl list | grep openclaw
```

### Monitor Pipeline Execution

```bash
# After a pipeline run, check results
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the results of the most recent pipeline run: how many leads found, enriched, qualified, and added to CRM? What was the total cost?"}'

# Check cost tracking
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me pipeline costs for this week broken down by day and service"}'
```

---

## Day 9-10: Ralph and RAFE Integration

### Configure Ralph Coexistence

Ralph (your AI dev loop) and OpenClaw both run on the Mac Mini. They need to share resources without conflict.

```bash
cat > ~/.openclaw/config/resource-allocation.json << 'JSON'
{
  "resource_sharing": {
    "description": "Resource allocation between OpenClaw and Ralph on Mac Mini M4 Pro",
    "total_resources": {
      "cpu_cores": 14,
      "ram_gb": 24,
      "gpu_cores": 20
    },
    "allocation": {
      "openclaw": {
        "cpu_cores": 4,
        "ram_gb": 8,
        "description": "Docker container limits set in docker-compose.yml"
      },
      "ollama": {
        "cpu_cores": 4,
        "ram_gb": 10,
        "gpu_cores": 20,
        "description": "Ollama needs GPU for model inference. Shared with Ralph when both need local models"
      },
      "ralph": {
        "cpu_cores": 4,
        "ram_gb": 4,
        "description": "Ralph's processes when running dev loops"
      },
      "system_reserve": {
        "cpu_cores": 2,
        "ram_gb": 2,
        "description": "macOS and background processes"
      }
    },
    "conflict_resolution": {
      "ollama_contention": "Queue requests, first-come-first-served. Both use same Ollama instance.",
      "memory_pressure": "OpenClaw defers to Ralph during active dev sessions. Set OpenClaw to batch mode.",
      "scheduling": "Heavy OpenClaw pipelines run overnight (2-6 AM) when Ralph is idle"
    }
  }
}
JSON
```

### Connect RAFE Obsidian MCP to OpenClaw

Your RAFE Obsidian vault contains project knowledge, decisions, and session logs. OpenClaw should be able to read this and contribute to it.

```bash
# Add RAFE connection to .env
cat >> ~/.openclaw/.env << 'ENV'

# RAFE Obsidian Integration
RAFE_VAULT_PATH=/path/to/your/rafe/vault
RAFE_MCP_ENABLED=true
ENV

# Create integration configuration
cat > ~/.openclaw/skills/rafe-integration/config.json << 'JSON'
{
  "skill_name": "rafe-integration",
  "description": "Bidirectional knowledge sync with RAFE Obsidian vault",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "read_doc",
      "description": "Read a document from the RAFE vault",
      "hitl_required": false
    },
    {
      "name": "log_session",
      "description": "Log an OpenClaw work session to RAFE",
      "hitl_required": false,
      "auto_trigger": "on_session_end"
    },
    {
      "name": "log_decision",
      "description": "Log an important decision to RAFE _DECISIONS.md",
      "hitl_required": false
    },
    {
      "name": "read_decisions",
      "description": "Read past decisions from RAFE for context",
      "hitl_required": false
    },
    {
      "name": "sync_knowledge",
      "description": "Sync relevant knowledge between OpenClaw memory and RAFE vault",
      "hitl_required": false,
      "direction": "bidirectional"
    }
  ],
  "auto_behaviors": [
    {
      "trigger": "session_end",
      "action": "Log session summary to RAFE including: work done, decisions made, issues encountered"
    },
    {
      "trigger": "important_decision",
      "action": "Log decision to RAFE _DECISIONS.md with context and rationale"
    },
    {
      "trigger": "daily_8am",
      "action": "Read RAFE for any new tasks or context updates relevant to OpenClaw operations"
    }
  ]
}
JSON
```

### Test RAFE Integration

```bash
# Test: Read from RAFE
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Read the latest decisions from the RAFE vault. What was the most recent architectural decision?"}'

# Test: Log session to RAFE
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Log a session to RAFE: Today I configured the n8n and Airtable integrations for OpenClaw. The Rise Local pipeline is now running through OpenClaw with automated daily scheduling."}'

# Test: Knowledge sync
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check RAFE for any updates about the OpenClaw project that I should know about"}'
```

### Document Integration Architecture

```bash
cat > ~/.openclaw/INTEGRATION-MAP.md << 'MD'
# OpenClaw Integration Map

## Active Integrations

### n8n (Bidirectional)
- OpenClaw -> n8n: Triggers workflows via webhook
- n8n -> OpenClaw: Invokes skills via API
- Use case: Rise Local pipeline orchestration
- Status: Active

### Airtable (Bidirectional via MCP)
- Read: Query content calendars, client data
- Write: Create content items, update schedules
- Use case: Content calendar management
- Status: Active

### Supabase (Bidirectional via MCP)
- Read: Analytics queries, cost tracking
- Write: Enrichment results, pipeline logs, cost entries
- Use case: Operational database and analytics
- Status: Active

### GoHighLevel (Bidirectional via MCP)
- Read: Search contacts, pipeline data
- Write: Create/update contacts, manage opportunities
- Use case: CRM management
- Status: Active

### RAFE Obsidian (Bidirectional via MCP)
- Read: Decisions, project context, task lists
- Write: Session logs, decisions, knowledge updates
- Use case: Project knowledge management
- Status: Active

### Ralph (Coexistence)
- Resource sharing via allocation config
- Shared Ollama instance
- No direct API integration (independent systems)
- Status: Active

## Data Flow Diagram

```
New Lead Discovered (n8n or manual)
  |
  v
OpenClaw: Enrich (Clay + Google + ZeroBounce)
  |
  v
OpenClaw: Score (15-signal system)
  |
  +--> Supabase: Store enrichment result
  |
  v
OpenClaw: Qualify (hot/warm/cold)
  |
  +--> GHL: Create contact (warm/hot)
  |    +--> Airtable: Update pipeline tracking
  |
  v (hot leads only)
OpenClaw: Generate pitch deck
  |
  +--> HITL: Approve outreach
  |
  v
n8n: Send email/LinkedIn (after approval)
  |
  +--> RAFE: Log session and results
```

## Error Handling
- All integrations retry 3x with exponential backoff
- Failed operations logged to Supabase cost_tracking
- Telegram alerts for repeated failures
- Dead letter queue for unprocessable items
MD
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| n8n -> OpenClaw working | n8n webhook triggers OpenClaw skill | [ ] |
| OpenClaw -> n8n working | Natural language triggers n8n workflow | [ ] |
| Airtable read working | Can query content calendar | [ ] |
| Airtable write working | Can create content items | [ ] |
| Supabase queries working | Can query enrichment results and costs | [ ] |
| Supabase writes working | Pipeline results logged automatically | [ ] |
| Rise Local pipeline runs | Full pipeline: discover -> enrich -> qualify -> CRM | [ ] |
| Daily pipeline scheduled | Runs at 8 AM weekdays | [ ] |
| Cost tracking working | All API costs logged to Supabase | [ ] |
| Ralph coexistence stable | Both systems run without resource conflicts | [ ] |
| RAFE read working | Can read decisions and context from vault | [ ] |
| RAFE write working | Sessions and decisions logged to vault | [ ] |
| Integration map documented | INTEGRATION-MAP.md complete and accurate | [ ] |

---

## Next Phase

With all integrations connected, proceed to [Phase 6 - Channels](phase-6-channels.md) to set up multi-platform access via web UI, Telegram, Slack, and WhatsApp.

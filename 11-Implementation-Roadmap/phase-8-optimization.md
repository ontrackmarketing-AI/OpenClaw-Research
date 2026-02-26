# Phase 8 - Optimization (Ongoing)

## Goal

Continuously improve OpenClaw's performance, reduce costs, expand capabilities, and maintain reliability. This phase has no end date -- it is the operational rhythm that keeps the platform valuable and efficient.

---

## This Phase Is Different

Phases 1-7 were project-like: defined scope, clear deliverables, done when complete. Phase 8 is an ongoing discipline with recurring activities organized by cadence: weekly, monthly, quarterly, and as-needed.

---

## Performance Optimization (Month 2)

### Profile Agent Execution Times

Before optimizing, measure what is actually slow.

```bash
# Enable detailed timing logs
cat > ~/.openclaw/config/performance-config.json << 'JSON'
{
  "performance": {
    "timing": {
      "enabled": true,
      "log_all_requests": true,
      "slow_threshold_ms": 5000,
      "alert_threshold_ms": 30000
    },
    "metrics_collection": {
      "enabled": true,
      "store_in": "supabase",
      "table": "performance_metrics",
      "retention_days": 90
    }
  }
}
JSON
```

Create the metrics table:

```sql
-- Run in Supabase SQL Editor

CREATE TABLE performance_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill TEXT NOT NULL,
  action TEXT NOT NULL,
  model_used TEXT,

  -- Timing
  total_duration_ms INTEGER,
  llm_duration_ms INTEGER,
  api_duration_ms INTEGER,
  db_duration_ms INTEGER,

  -- Token usage
  input_tokens INTEGER,
  output_tokens INTEGER,

  -- Cost
  estimated_cost DECIMAL(10,4),

  -- Context
  channel TEXT,
  success BOOLEAN DEFAULT true,
  error_message TEXT,

  timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_perf_skill ON performance_metrics(skill);
CREATE INDEX idx_perf_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_perf_model ON performance_metrics(model_used);

-- Useful views
CREATE VIEW skill_performance_summary AS
SELECT
  skill,
  action,
  model_used,
  COUNT(*) as invocations,
  AVG(total_duration_ms)::INTEGER as avg_duration_ms,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_duration_ms)::INTEGER as p95_duration_ms,
  AVG(input_tokens)::INTEGER as avg_input_tokens,
  AVG(output_tokens)::INTEGER as avg_output_tokens,
  SUM(estimated_cost) as total_cost,
  AVG(estimated_cost) as avg_cost,
  COUNT(*) FILTER (WHERE NOT success) as error_count
FROM performance_metrics
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY skill, action, model_used
ORDER BY total_cost DESC;
```

### Run Performance Audit

After 1-2 weeks of metrics collection:

```bash
# Get performance summary
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Run a performance audit. Show me: 1) Slowest skills by average duration, 2) Most expensive skills by total cost, 3) Skills with highest error rates, 4) Opportunities to move API calls to local models."}'
```

### Optimize Slow Skills

Common optimization strategies ranked by impact:

| Strategy | Impact | Effort | When to Use |
|----------|--------|--------|-------------|
| **Caching** | High | Low | Repeated queries for same data |
| **Prompt reduction** | High | Medium | Context windows exceeding 50K tokens |
| **Model downgrade** | High | Low | Simple tasks using Claude when Ollama suffices |
| **Batching** | Medium | Medium | Multiple API calls that could be combined |
| **Parallel execution** | Medium | Medium | Independent API calls running sequentially |
| **Precomputation** | Medium | High | Expensive calculations that can be done ahead of time |

### Implement Caching Layer

```bash
cat > ~/.openclaw/config/cache-config.json << 'JSON'
{
  "cache": {
    "enabled": true,
    "backend": "sqlite",
    "database": "/app/data/cache.db",
    "strategies": [
      {
        "skill": "lead-enrichment",
        "action": "google_places_lookup",
        "ttl_hours": 168,
        "description": "Cache Google Places results for 7 days (business data changes slowly)"
      },
      {
        "skill": "lead-enrichment",
        "action": "website_analysis",
        "ttl_hours": 72,
        "description": "Cache website analysis for 3 days"
      },
      {
        "skill": "competitor-intel",
        "action": "website_snapshot",
        "ttl_hours": 24,
        "description": "Cache competitor snapshots for 1 day (checked daily)"
      },
      {
        "skill": "crm-management",
        "action": "search_contacts",
        "ttl_hours": 1,
        "description": "Cache CRM search results for 1 hour"
      },
      {
        "skill": "rag",
        "action": "embedding_lookup",
        "ttl_hours": 720,
        "description": "Cache embedding search results for 30 days (content rarely changes)"
      }
    ],
    "eviction": {
      "max_size_mb": 500,
      "strategy": "lru"
    },
    "monitoring": {
      "log_hit_rate": true,
      "alert_on_low_hit_rate": 0.3
    }
  }
}
JSON
```

### Tune Model Routing

After collecting real usage data, refine which tasks go to local vs API models:

```bash
# Query actual model usage patterns
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze the last 30 days of model usage. For each skill, show: which model was used, average quality rating (if available), and cost. Recommend which skills could switch from Claude API to Ollama without quality loss."}'
```

Expected optimization targets:
- **Move to Ollama**: Classification, extraction, formatting, simple summarization, email parsing
- **Keep on Claude API**: Complex reasoning, multi-step planning, creative writing, code generation
- **Hybrid**: Start with Ollama, escalate to Claude if confidence is low

### Optimize Context Window Usage

```bash
cat > ~/.openclaw/config/context-optimization.json << 'JSON'
{
  "context_optimization": {
    "max_context_tokens": {
      "ollama_qwen3_14b": 32000,
      "claude_sonnet": 200000
    },
    "strategies": [
      {
        "name": "memory_compaction",
        "description": "Summarize old memory entries to save context space",
        "trigger": "memory_tokens > 8000",
        "action": "summarize entries older than 7 days, keep recent entries verbatim",
        "target_reduction": "50%"
      },
      {
        "name": "rag_result_pruning",
        "description": "Only include the most relevant RAG results",
        "trigger": "rag_results > 5",
        "action": "Keep top 5 results, summarize rest into one-line descriptions",
        "target_reduction": "60%"
      },
      {
        "name": "conversation_trimming",
        "description": "Trim old conversation turns",
        "trigger": "conversation_tokens > 10000",
        "action": "Summarize turns older than 5 exchanges, keep recent verbatim",
        "target_reduction": "40%"
      },
      {
        "name": "tool_result_compression",
        "description": "Compress verbose tool outputs",
        "trigger": "tool_result_tokens > 2000",
        "action": "Extract key fields only, discard raw API responses",
        "target_reduction": "70%"
      }
    ]
  }
}
JSON
```

### SQLite/pgvector Index Tuning

After accumulating real query patterns:

```sql
-- Run ANALYZE to update query planner statistics
ANALYZE documents;
ANALYZE enrichment_results;
ANALYZE performance_metrics;
ANALYZE cost_tracking;

-- Check index usage (Supabase)
SELECT
  schemaname,
  relname AS table,
  indexrelname AS index,
  idx_scan AS times_used,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Identify missing indexes (look for sequential scans on large tables)
SELECT
  relname AS table,
  seq_scan,
  seq_tup_read,
  idx_scan,
  idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 100
ORDER BY seq_tup_read DESC;

-- Tune ivfflat lists parameter based on data size
-- Rule of thumb: lists = sqrt(num_rows)
-- If documents table has 10,000 rows, lists should be ~100
-- Recreate index if needed:
-- DROP INDEX documents_embedding_idx;
-- CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## Cost Optimization (Month 2-3)

### Build Cost Dashboard

```bash
cat > ~/.openclaw/config/cost-dashboard.json << 'JSON'
{
  "cost_dashboard": {
    "refresh_interval_seconds": 300,
    "views": [
      {
        "name": "daily_breakdown",
        "query": "SELECT DATE(timestamp) as date, service, SUM(cost) as total FROM cost_tracking WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY date, service ORDER BY date DESC",
        "chart_type": "stacked_bar"
      },
      {
        "name": "cost_per_skill",
        "query": "SELECT skill, COUNT(*) as operations, SUM(cost) as total_cost, AVG(cost) as avg_cost FROM cost_tracking WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY skill ORDER BY total_cost DESC",
        "chart_type": "table"
      },
      {
        "name": "cost_per_lead",
        "query": "SELECT DATE(created_at) as date, COUNT(*) as leads, SUM(cost) as total_cost, AVG(cost) as avg_cost_per_lead FROM enrichment_results WHERE created_at > NOW() - INTERVAL '30 days' GROUP BY date ORDER BY date DESC",
        "chart_type": "line"
      },
      {
        "name": "model_costs",
        "query": "SELECT model_used, COUNT(*) as calls, SUM(estimated_cost) as total_cost FROM performance_metrics WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY model_used ORDER BY total_cost DESC",
        "chart_type": "pie"
      },
      {
        "name": "budget_tracker",
        "thresholds": {
          "daily": 25.00,
          "weekly": 125.00,
          "monthly": 500.00
        },
        "chart_type": "gauge"
      }
    ],
    "alerts": [
      {
        "name": "daily_budget_80",
        "condition": "daily_cost > daily_budget * 0.8",
        "action": "telegram_notification",
        "message": "Daily cost is at 80% of budget (${{current}} of ${{budget}})"
      },
      {
        "name": "daily_budget_100",
        "condition": "daily_cost >= daily_budget",
        "action": "pause_expensive_operations",
        "message": "Daily budget reached! Pausing expensive operations."
      },
      {
        "name": "anomaly_detection",
        "condition": "hourly_cost > 3x_average_hourly_cost",
        "action": "telegram_alert",
        "message": "Cost anomaly detected: ${{current}} this hour vs ${{average}} average"
      }
    ]
  }
}
JSON
```

### Monthly Cost Review Process

Run this on the 1st of each month:

```bash
# Generate comprehensive cost report
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate the monthly cost report for last month. Include: 1) Total spend by service (Anthropic, Clay, ZeroBounce, Twilio, etc.), 2) Cost per lead (enrichment cost / leads generated), 3) Cost per client action (CRM updates, emails, etc.), 4) Comparison to previous month, 5) Top 5 most expensive operations, 6) Recommendations for cost reduction. Target: 20-30% reduction from initial levels."
  }'
```

### Cost Reduction Strategies (Prioritized)

| Strategy | Estimated Savings | Implementation Effort |
|----------|------------------|----------------------|
| Move simple LLM tasks to Ollama | 30-40% of API costs | Low - update model routing |
| Implement prompt caching (Anthropic) | 10-20% of API costs | Low - enable in config |
| Cache enrichment results | 20-30% of enrichment costs | Low - already configured |
| Batch enrichment (fewer API calls) | 10-15% of enrichment costs | Medium - update pipeline |
| Optimize prompt lengths | 10-20% of API costs | Medium - rewrite prompts |
| Negotiate volume discounts | 5-15% | Low - contact providers |

### Implement Prompt Caching

Anthropic supports prompt caching for frequently used system prompts. This can significantly reduce costs for repetitive operations.

```bash
# Add to .env
cat >> ~/.openclaw/.env << 'ENV'

# Anthropic Prompt Caching
ANTHROPIC_PROMPT_CACHING=true
ANTHROPIC_CACHE_TTL_SECONDS=300
ENV

# Identify cacheable prompts (system prompts used frequently)
# - CRM management system prompt (used for every CRM interaction)
# - Lead enrichment system prompt (used for every enrichment)
# - Content generation system prompt (used for every content task)
# These prompts should be designated as cache-eligible in skill configs
```

---

## Capability Expansion (Month 3+)

### Add New Sector Knowledge Bases

As you onboard clients in new industries, add sector-specific knowledge:

```bash
# Template for a new sector knowledge base
cat > ~/.openclaw/memory/knowledge/SECTOR-TEMPLATE.md << 'MD'
# [Industry] - Marketing Knowledge Base

## Market Overview
- Market size
- Number of businesses
- Average revenue
- Growth trends

## Customer Profile
- Primary demographics
- Decision triggers
- Research behavior
- Common objections

## Marketing Channels (Effectiveness Ranked)
1. [Channel] - [notes]
2. [Channel] - [notes]
(etc.)

## Pain Points
- "Quote from typical prospect"
(etc.)

## Pricing Benchmarks
- Service pricing for this industry
- What competitors charge
- Value-based pricing opportunities

## Key Metrics
- Cost per lead range
- Conversion rates
- Average job/case/appointment value
- Customer lifetime value

## Competitive Landscape
- Major platforms (Angi, Thumbtack, Avvo, Zocdoc, etc.)
- Pricing on those platforms
- Differentiation strategies
MD
```

Planned sector knowledge bases:

| Sector | Priority | Timeline | Data Source |
|--------|----------|----------|-------------|
| Healthcare (medical practices) | High | Month 3 | Research + client data |
| Real estate | Medium | Month 4 | Research + partnerships |
| Home services (HVAC, electrical, roofing) | High | Month 3 | Extension of plumbing data |
| Restaurants/food service | Low | Month 5+ | Research |
| Professional services (accounting, consulting) | Medium | Month 4 | Research |

### Explore ClawHub for Community Skills

```bash
# Search ClawHub for useful skills
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Search ClawHub for skills related to: 1) email marketing automation, 2) social media posting, 3) invoice generation, 4) appointment scheduling. List the top-rated options for each."}'

# Install a community skill
curl -X POST http://localhost:18789/api/skills/install \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "clawhub/skill-name", "version": "latest"}'
```

### Multi-Agent Workflows

As you build confidence, set up specialized agents that collaborate:

```bash
cat > ~/.openclaw/config/multi-agent.json << 'JSON'
{
  "agents": {
    "lead_hunter": {
      "description": "Discovers and enriches new leads",
      "skills": ["lead-enrichment", "competitor-intel"],
      "model": "auto",
      "schedule": "daily at 8 AM"
    },
    "content_creator": {
      "description": "Generates marketing content",
      "skills": ["content-calendar", "presentation-gen", "website-gen"],
      "model": "claude-sonnet",
      "schedule": "on-demand"
    },
    "crm_manager": {
      "description": "Manages CRM operations and follow-ups",
      "skills": ["crm-management", "n8n-integration"],
      "model": "auto",
      "schedule": "continuous"
    },
    "analyst": {
      "description": "Generates reports and insights",
      "skills": ["database-ops", "competitor-intel"],
      "model": "claude-sonnet",
      "schedule": "weekly on Fridays"
    }
  },
  "collaboration": {
    "lead_hunter -> crm_manager": "Pass qualified leads for CRM entry",
    "lead_hunter -> content_creator": "Request pitch decks for hot leads",
    "analyst -> lead_hunter": "Adjust targeting based on conversion data",
    "analyst -> content_creator": "Suggest content based on performance data"
  }
}
JSON
```

---

## Reliability (Ongoing)

### Error Rate Monitoring

```bash
cat > ~/.openclaw/config/reliability-config.json << 'JSON'
{
  "reliability": {
    "health_checks": {
      "interval_seconds": 60,
      "checks": [
        {"name": "openclaw_gateway", "url": "http://localhost:18789/health", "timeout_ms": 5000},
        {"name": "ollama", "url": "http://localhost:11434/api/tags", "timeout_ms": 5000},
        {"name": "n8n", "url": "http://localhost:5678/healthz", "timeout_ms": 5000},
        {"name": "docker", "command": "docker ps --filter name=openclaw --format '{{.Status}}'"}
      ],
      "alert_on_failure": true,
      "alert_channel": "telegram",
      "auto_restart": {
        "enabled": true,
        "max_restarts": 3,
        "cooldown_minutes": 5
      }
    },
    "error_tracking": {
      "alert_threshold": {
        "errors_per_hour": 10,
        "error_rate": 0.1
      },
      "categories": ["api_failure", "timeout", "auth_error", "rate_limit", "skill_error"]
    }
  }
}
JSON
```

### Automated Health Check Script

```bash
cat > ~/.openclaw/scripts/health-check.sh << 'BASH'
#!/bin/bash
# OpenClaw Health Check Script
# Run via cron or launchd every 5 minutes

LOG_FILE="$HOME/.openclaw/logs/health-check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ALERT_NEEDED=false
ISSUES=""

# Check OpenClaw gateway
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:18789/health 2>/dev/null)
if [ "$HTTP_CODE" != "200" ]; then
  ISSUES="${ISSUES}\n- OpenClaw gateway: HTTP $HTTP_CODE"
  ALERT_NEEDED=true
fi

# Check Ollama
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:11434/api/tags 2>/dev/null)
if [ "$HTTP_CODE" != "200" ]; then
  ISSUES="${ISSUES}\n- Ollama: HTTP $HTTP_CODE"
  ALERT_NEEDED=true
fi

# Check Docker container status
CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' openclaw 2>/dev/null)
if [ "$CONTAINER_STATUS" != "running" ]; then
  ISSUES="${ISSUES}\n- Docker container: $CONTAINER_STATUS"
  ALERT_NEEDED=true
  # Attempt auto-restart
  docker compose -f $HOME/.openclaw/docker-compose.yml up -d
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
  ISSUES="${ISSUES}\n- Disk usage: ${DISK_USAGE}%"
  ALERT_NEEDED=true
fi

# Check memory pressure
MEM_PRESSURE=$(memory_pressure 2>/dev/null | grep "System-wide" | awk '{print $NF}')

# Log results
echo "$TIMESTAMP | Gateway: $HTTP_CODE | Ollama: $HTTP_CODE | Docker: $CONTAINER_STATUS | Disk: ${DISK_USAGE}%" >> $LOG_FILE

# Alert if needed
if [ "$ALERT_NEEDED" = true ]; then
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d chat_id="${TELEGRAM_CHAT_ID}" \
    -d text="OpenClaw Health Alert ($TIMESTAMP):$(echo -e $ISSUES)" \
    -d parse_mode="Markdown"
fi
BASH

chmod +x ~/.openclaw/scripts/health-check.sh
```

Schedule the health check:

```bash
# Run every 5 minutes via launchd
cat > ~/Library/LaunchAgents/com.openclaw.health-check.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.health-check</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/yourusername/.openclaw/scripts/health-check.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>EnvironmentVariables</key>
    <dict>
        <key>TELEGRAM_BOT_TOKEN</key>
        <string>your-bot-token</string>
        <key>TELEGRAM_CHAT_ID</key>
        <string>your-chat-id</string>
    </dict>
</dict>
</plist>
PLIST

launchctl load ~/Library/LaunchAgents/com.openclaw.health-check.plist
```

### Backup Strategy

```bash
cat > ~/.openclaw/scripts/backup.sh << 'BASH'
#!/bin/bash
# OpenClaw Backup Script
# Run weekly via launchd

BACKUP_DIR="$HOME/.openclaw/backups"
DATE=$(date '+%Y-%m-%d')
BACKUP_PATH="$BACKUP_DIR/openclaw-backup-$DATE"

mkdir -p "$BACKUP_PATH"

# Backup configuration
cp -r $HOME/.openclaw/config "$BACKUP_PATH/config"

# Backup memory (excluding large embedding databases)
cp -r $HOME/.openclaw/memory "$BACKUP_PATH/memory"

# Backup skills
cp -r $HOME/.openclaw/skills "$BACKUP_PATH/skills"

# Backup .env (encrypted)
openssl enc -aes-256-cbc -salt -in $HOME/.openclaw/.env -out "$BACKUP_PATH/env.enc" -pass pass:your-backup-password

# Backup SQLite databases
cp $HOME/.openclaw/data/memory.db "$BACKUP_PATH/memory.db"
cp $HOME/.openclaw/data/cache.db "$BACKUP_PATH/cache.db" 2>/dev/null

# Compress
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "openclaw-backup-$DATE"
rm -rf "$BACKUP_PATH"

# Keep only last 4 weekly backups
find "$BACKUP_DIR" -name "openclaw-backup-*.tar.gz" -mtime +28 -delete

# Log
echo "$(date '+%Y-%m-%d %H:%M:%S') | Backup created: $BACKUP_PATH.tar.gz ($(du -sh "$BACKUP_PATH.tar.gz" | awk '{print $1}'))" >> $HOME/.openclaw/logs/backup.log
BASH

chmod +x ~/.openclaw/scripts/backup.sh
```

### Disaster Recovery Document

```bash
cat > ~/.openclaw/DISASTER-RECOVERY.md << 'MD'
# OpenClaw Disaster Recovery Procedure

## Scenario 1: OpenClaw Container Crash
1. Check logs: `docker compose logs --tail=50`
2. Restart: `docker compose restart`
3. If restart fails: `docker compose down && docker compose up -d`
4. If image is corrupted: `docker compose pull && docker compose up -d`

## Scenario 2: Mac Mini Hardware Failure
1. Obtain replacement Mac Mini
2. Install macOS, Homebrew, Docker, Ollama (Phase 1 steps)
3. Install Tailscale and authenticate
4. Restore from latest backup:
   ```
   tar -xzf openclaw-backup-YYYY-MM-DD.tar.gz
   cp -r config/ ~/.openclaw/config/
   cp -r memory/ ~/.openclaw/memory/
   cp -r skills/ ~/.openclaw/skills/
   openssl enc -d -aes-256-cbc -in env.enc -out ~/.openclaw/.env -pass pass:your-backup-password
   cp memory.db ~/.openclaw/data/memory.db
   ```
5. Start OpenClaw: `cd ~/.openclaw && docker compose up -d`
6. Pull Ollama models: `ollama pull qwen3:14b && ollama pull nomic-embed-text`
7. Verify all integrations (n8n, Airtable, GHL, etc.)
8. Estimated recovery time: 2-4 hours

## Scenario 3: Data Corruption
1. Stop OpenClaw: `docker compose down`
2. Restore databases from backup
3. Restart: `docker compose up -d`
4. Re-index knowledge base: `curl -X POST http://localhost:18789/api/knowledge/reindex`

## Scenario 4: API Key Compromise
1. Immediately rotate all API keys:
   - Anthropic: https://console.anthropic.com/settings/keys
   - GHL: Settings > API Keys
   - Clay: Workspace settings
   - ZeroBounce: Account settings
2. Update .env with new keys
3. Restart OpenClaw
4. Review logs for unauthorized usage
5. Check billing for unexpected charges

## Backup Locations
- Local: ~/.openclaw/backups/ (weekly, last 4 weeks)
- Supabase: All operational data (always available)
- Manual: Quarterly export to external drive (recommended)
MD
```

### Dependency Update Schedule

| Dependency | Update Frequency | How to Update |
|-----------|-----------------|---------------|
| OpenClaw | Monthly (check releases) | `docker compose pull && docker compose up -d` |
| Ollama | Monthly | `brew upgrade ollama` |
| Ollama models | Quarterly | `ollama pull qwen3:14b` (re-pull updates the model) |
| Docker Desktop | Monthly | `brew upgrade --cask docker` |
| macOS | As needed (security patches) | System Settings > Software Update |
| Node.js | Quarterly | `brew upgrade node@22` |
| n8n | Monthly | Depends on your n8n installation method |

---

## Metrics to Track

### Weekly Metrics Dashboard

| Metric | Where to Find | Target |
|--------|--------------|--------|
| Leads processed | `SELECT COUNT(*) FROM enrichment_results WHERE created_at > NOW() - INTERVAL '7 days'` | 50-100/week |
| Hot leads generated | `SELECT COUNT(*) FROM enrichment_results WHERE tier = 'hot' AND created_at > NOW() - INTERVAL '7 days'` | 10-20/week |
| CRM contacts created | GHL dashboard or `cost_tracking WHERE skill = 'crm-management'` | 20-50/week |
| API cost total | `SELECT SUM(cost) FROM cost_tracking WHERE timestamp > NOW() - INTERVAL '7 days'` | < $50/week |
| Cost per lead | Total enrichment cost / leads processed | < $0.50 |
| Agent error rate | `SELECT COUNT(*) FILTER (WHERE NOT success) / COUNT(*) FROM performance_metrics` | < 5% |
| Average response time | `SELECT AVG(total_duration_ms) FROM performance_metrics` | < 5000ms |
| Ollama utilization | Percentage of requests handled by local model | > 40% |

### Monthly Metrics

| Metric | How to Measure | Goal |
|--------|---------------|------|
| Lead-to-client conversion | Track manually: leads contacted vs deals closed | > 5% |
| Time saved per week | Self-assessment: tasks automated vs manual time | 10+ hours |
| Revenue attributed to OpenClaw | New clients from enriched leads | Track from Month 3 |
| Total infrastructure cost | Sum all costs: API + hosting + tools | < $300/month |
| Cost per client acquired | Total OpenClaw cost / new clients | < $100 |
| Knowledge base quality | Manual spot-check: ask 10 questions, rate relevance | > 80% relevant |
| Uptime | Health check logs: minutes healthy / total minutes | > 99% |

### Track Manually Initially

Create a simple weekly tracking spreadsheet or Airtable base:

```
Week | Leads Found | Leads Enriched | Hot Leads | CRM Entries | Presentations | Emails Sent | API Cost | Time Saved (est.) | Notes
```

This data becomes invaluable for quarterly reviews and business decisions.

---

## Quarterly Review Template

Run this review at the end of each quarter (March, June, September, December):

```bash
cat > ~/.openclaw/QUARTERLY-REVIEW-TEMPLATE.md << 'MD'
# OpenClaw Quarterly Review - Q[X] [YEAR]

## Performance Summary

### What Worked Well
- [Bullet points of successes]

### What Needs Improvement
- [Bullet points of areas for improvement]

### Key Metrics This Quarter
| Metric | Q[X-1] | Q[X] | Change |
|--------|--------|------|--------|
| Total leads processed | | | |
| Hot leads generated | | | |
| New clients attributed | | | |
| Total API cost | | | |
| Cost per lead | | | |
| Time saved (estimated hours) | | | |
| Uptime | | | |
| Error rate | | | |

### Cost vs Value Assessment
- Total OpenClaw cost this quarter: $[X]
- Estimated revenue from OpenClaw-sourced leads: $[X]
- ROI: [X]%
- Time saved value (at $[hourly rate]/hr): $[X]

### Security Audit Results
- [ ] All API keys rotated this quarter
- [ ] Access logs reviewed (no unauthorized access)
- [ ] Tailscale ACLs up to date
- [ ] HITL configuration reviewed (no gaps)
- [ ] Backup tested (restore from backup verified)
- [ ] Dependencies updated (no known vulnerabilities)

### New Capabilities to Add Next Quarter
1. [Capability] - [Expected impact] - [Effort estimate]
2. [Capability] - [Expected impact] - [Effort estimate]
3. [Capability] - [Expected impact] - [Effort estimate]

### Roadmap Updates
- [Any changes to the implementation roadmap]
- [New phases to add]
- [Phases to adjust or remove]

### Action Items
- [ ] [Action 1] - Owner - Due date
- [ ] [Action 2] - Owner - Due date
- [ ] [Action 3] - Owner - Due date
MD
```

---

## Success Criteria (Ongoing)

Phase 8 succeeds when you observe these trends over time:

| Trend | Indicator | Measurement |
|-------|-----------|-------------|
| Declining cost per operation | Cost/lead, cost/action decreasing month over month | Monthly cost report |
| Increasing efficiency | More leads processed with same or less cost | Weekly metrics |
| Expanding capabilities | New skills and integrations added each quarter | Quarterly review |
| High reliability | Uptime > 99%, error rate < 5% | Health check logs |
| Positive ROI | Revenue from OpenClaw leads > total OpenClaw cost | Quarterly review |
| Time savings | Consistent 10+ hours/week saved | Self-tracking |
| Growing knowledge base | RAG quality improving, fewer irrelevant results | Monthly spot checks |
| Security maintained | No incidents, regular audits passing | Monthly audits |

---

## Ongoing Cadence Summary

| Cadence | Activity |
|---------|----------|
| **Daily** | Check Telegram summary, review pending approvals, glance at dashboard |
| **Weekly** | Review metrics, check error rates, verify backups ran |
| **Monthly** | Cost report, security audit, dependency updates, model routing review |
| **Quarterly** | Full quarterly review, roadmap update, capability planning |
| **Annually** | Major version upgrades, infrastructure review, strategic planning |

---

This is the final phase of the implementation roadmap, but it is the beginning of the operational lifecycle. The work you put into optimization, monitoring, and continuous improvement determines whether OpenClaw becomes a true competitive advantage or just another tool collecting dust.

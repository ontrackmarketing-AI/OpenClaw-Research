# Phase 6 - Channels (Week 5-6)

## Goal

Access OpenClaw from multiple platforms: polished web UI, Telegram bot for mobile, Slack for team collaboration, and optionally WhatsApp for client communication. By the end of this phase, you can interact with OpenClaw from any device, anywhere, with consistent context across channels.

---

## Why Multi-Channel Matters

Different situations call for different interfaces:
- **Web UI**: Detailed work sessions at your desk (reports, pipeline review, complex tasks)
- **Telegram**: Quick commands from your phone (check lead status, approve actions, get alerts)
- **Slack**: Team collaboration (share results, delegate tasks, discuss strategy)
- **WhatsApp**: Client-facing communication (automated responses, appointment scheduling)

---

## Day 1-2: Web UI Polish

### Configure Web UI Authentication

The web UI was set up in Phase 1 and secured in Phase 2. Now make it useful for daily operations.

```bash
# Verify authentication is working
# Browse to http://mac-mini:3000 (via Tailscale)
# Should see login screen

# If you need to reset credentials:
cat >> ~/.openclaw/.env << 'ENV'

# Web UI Credentials
OPENCLAW_WEB_USERNAME=admin
OPENCLAW_WEB_PASSWORD=your-secure-password-here
ENV

cd ~/.openclaw && docker compose restart
```

### Customize Dashboard

Create a dashboard configuration tailored to your marketing operations:

```bash
cat > ~/.openclaw/config/dashboard.json << 'JSON'
{
  "dashboard": {
    "title": "OnTrack Marketing - OpenClaw Dashboard",
    "refresh_interval_seconds": 30,
    "widgets": [
      {
        "type": "status",
        "title": "System Status",
        "position": {"row": 1, "col": 1, "width": 4},
        "data_sources": [
          {"name": "OpenClaw", "endpoint": "/health"},
          {"name": "Ollama", "endpoint": "http://host.docker.internal:11434/api/tags"},
          {"name": "n8n", "endpoint": "http://localhost:5678/healthz"}
        ]
      },
      {
        "type": "counter",
        "title": "Leads Today",
        "position": {"row": 1, "col": 5, "width": 2},
        "query": "SELECT COUNT(*) FROM enrichment_results WHERE DATE(created_at) = CURRENT_DATE",
        "source": "supabase"
      },
      {
        "type": "counter",
        "title": "API Spend Today",
        "position": {"row": 1, "col": 7, "width": 2},
        "query": "SELECT COALESCE(SUM(cost), 0) FROM cost_tracking WHERE DATE(timestamp) = CURRENT_DATE",
        "source": "supabase",
        "format": "currency"
      },
      {
        "type": "counter",
        "title": "Hot Leads This Week",
        "position": {"row": 1, "col": 9, "width": 2},
        "query": "SELECT COUNT(*) FROM enrichment_results WHERE tier = 'hot' AND created_at > NOW() - INTERVAL '7 days'",
        "source": "supabase"
      },
      {
        "type": "table",
        "title": "Recent Pipeline Runs",
        "position": {"row": 2, "col": 1, "width": 6},
        "query": "SELECT pipeline_name, status, leads_found, leads_qualified, total_cost, started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 5",
        "source": "supabase"
      },
      {
        "type": "list",
        "title": "Pending Approvals",
        "position": {"row": 2, "col": 7, "width": 5},
        "data_source": "hitl_pending",
        "actions": ["approve", "deny"]
      },
      {
        "type": "chart",
        "title": "Daily Lead Volume (30 days)",
        "position": {"row": 3, "col": 1, "width": 6},
        "chart_type": "line",
        "query": "SELECT DATE(created_at) as date, COUNT(*) as leads FROM enrichment_results WHERE created_at > NOW() - INTERVAL '30 days' GROUP BY DATE(created_at) ORDER BY date",
        "source": "supabase"
      },
      {
        "type": "chart",
        "title": "Cost by Service (30 days)",
        "position": {"row": 3, "col": 7, "width": 5},
        "chart_type": "pie",
        "query": "SELECT service, SUM(cost) as total FROM cost_tracking WHERE timestamp > NOW() - INTERVAL '30 days' GROUP BY service",
        "source": "supabase"
      }
    ]
  }
}
JSON
```

### Test from All Devices via Tailscale

| Device | Access Method | URL | Test |
|--------|---------------|-----|------|
| Windows PC | Tailscale direct | `http://mac-mini:3000` | Login, view dashboard, send message |
| iPhone/Android | Tailscale app | `http://mac-mini:3000` | Login from mobile browser, verify responsive |
| iPad (if applicable) | Tailscale app | `http://mac-mini:3000` | Verify tablet layout |

### Bookmark Quick-Access URLs

Set up bookmarks on all devices:
- Dashboard: `http://mac-mini:3000/dashboard`
- Chat: `http://mac-mini:3000/chat`
- Skills: `http://mac-mini:3000/skills`
- Logs: `http://mac-mini:3000/logs`
- Settings: `http://mac-mini:3000/settings`

---

## Day 3-4: Telegram Bot

This becomes your primary mobile interface -- quick commands, notifications, and HITL approvals all in one place.

### Create the Bot

1. Open Telegram on your phone
2. Search for `@BotFather` and start a conversation
3. Send `/newbot`
4. Choose a name: `OnTrack OpenClaw`
5. Choose a username: `ontrack_openclaw_bot` (must be unique and end in `bot`)
6. BotFather will give you a **bot token** -- save it securely

### Configure Bot in OpenClaw

```bash
# Update .env with bot token (if not already added in Phase 2)
# The TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID should already be in .env from Phase 2 HITL setup

# Create Telegram channel configuration
cat > ~/.openclaw/config/telegram-config.json << 'JSON'
{
  "telegram": {
    "enabled": true,
    "bot_username": "ontrack_openclaw_bot",
    "allowed_users": ["your_telegram_user_id"],
    "commands": [
      {
        "command": "/start",
        "description": "Start the bot and see welcome message",
        "handler": "welcome"
      },
      {
        "command": "/status",
        "description": "System status: OpenClaw, Ollama, n8n health",
        "handler": "system_status"
      },
      {
        "command": "/leads",
        "description": "Today's lead summary: counts by tier, cost",
        "handler": "lead_summary"
      },
      {
        "command": "/pipeline",
        "description": "Latest pipeline run results",
        "handler": "pipeline_status"
      },
      {
        "command": "/costs",
        "description": "Today's and this week's API spending",
        "handler": "cost_report"
      },
      {
        "command": "/report",
        "description": "Generate a full daily/weekly report",
        "handler": "generate_report",
        "args": ["daily|weekly"]
      },
      {
        "command": "/stop",
        "description": "Emergency stop: cancel all pending actions",
        "handler": "emergency_stop"
      },
      {
        "command": "/help",
        "description": "List all available commands",
        "handler": "help"
      }
    ],
    "natural_language": {
      "enabled": true,
      "description": "Any message that is not a command is treated as a natural language request to OpenClaw"
    },
    "notifications": {
      "hitl_approvals": true,
      "pipeline_completions": true,
      "error_alerts": true,
      "daily_summary": {
        "enabled": true,
        "time": "18:00",
        "timezone": "America/Chicago"
      },
      "cost_alerts": {
        "daily_threshold": 20.00,
        "monthly_threshold": 400.00
      }
    },
    "message_formatting": {
      "max_message_length": 4096,
      "use_markdown": true,
      "truncate_with_link": true
    }
  }
}
JSON
```

### Register Bot Commands with BotFather

Send this to @BotFather to register your command menu:

```
/setcommands

status - System status overview
leads - Today's lead summary
pipeline - Latest pipeline results
costs - API spending report
report - Generate daily or weekly report
stop - Emergency stop all operations
help - List available commands
```

### Test Telegram Bot

Open your bot in Telegram and test each capability:

```
# 1. Start the bot
/start
# Expected: Welcome message with overview of capabilities

# 2. Check system status
/status
# Expected: Health of OpenClaw, Ollama, n8n with green/red indicators

# 3. Check leads
/leads
# Expected: Today's lead count by tier, total cost, top hot leads

# 4. Natural language request
Enrich "Quick Fix Plumbing" in Denver, CO
# Expected: Full enrichment results with score

# 5. Check costs
/costs
# Expected: Today's spend by service, weekly total, budget remaining

# 6. Test HITL approval
# (Trigger an action that needs approval from the web UI)
# Expected: Approval notification with Approve/Deny inline buttons

# 7. Emergency stop
/stop
# Expected: Confirmation that all pending actions are cancelled
```

### Configure Daily Summary Notification

The bot should automatically send you a daily summary at 6 PM:

```
Daily Summary - OnTrack Marketing
==================================
Leads Discovered: 15
Leads Enriched: 12
Hot Leads: 3 | Warm: 5 | Cold: 4
New GHL Contacts: 8
Pipeline Runs: 2 (both successful)

Costs Today: $4.82
  - Anthropic: $3.20
  - Clay: $1.20
  - ZeroBounce: $0.42

Pending Approvals: 2
  - Outreach email to Quick Fix Plumbing (waiting 3 hours)
  - Pitch deck for Metro Dental (waiting 1 hour)

Top Hot Lead: Quick Fix Plumbing (Denver, CO)
  Score: 78 | Email verified | No website
```

---

## Day 5-6: Slack App (If Using Slack)

Skip this step if you are a solo operator without a team Slack. Come back to it when you hire help.

### Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. App Name: `OpenClaw`
4. Workspace: Your team workspace
5. Under "OAuth & Permissions", add these scopes:
   - `chat:write` (send messages)
   - `commands` (slash commands)
   - `incoming-webhook` (post to channels)
   - `users:read` (identify who is messaging)

### Configure Slash Commands

Under "Slash Commands", create:

| Command | Request URL | Description |
|---------|------------|-------------|
| `/openclaw` | `http://mac-mini:18789/api/slack/command` | Send a request to OpenClaw |
| `/leads` | `http://mac-mini:18789/api/slack/leads` | Today's lead summary |
| `/pipeline` | `http://mac-mini:18789/api/slack/pipeline` | Pipeline status |

Note: Slack commands require a public URL. Options:
- **Tailscale Funnel**: `tailscale funnel 18789` (exposes securely via Tailscale)
- **n8n relay**: n8n receives the Slack webhook (public) and forwards to OpenClaw (internal)
- **ngrok**: `ngrok http 18789` (for testing only, not production)

Recommended: Use n8n as a relay to avoid exposing OpenClaw directly.

### Configure OpenClaw Slack Integration

```bash
cat >> ~/.openclaw/.env << 'ENV'

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_ID=your-app-id
SLACK_CHANNEL_GENERAL=#openclaw-general
SLACK_CHANNEL_ALERTS=#openclaw-alerts
SLACK_CHANNEL_APPROVALS=#openclaw-approvals
ENV

cat > ~/.openclaw/config/slack-config.json << 'JSON'
{
  "slack": {
    "enabled": true,
    "channels": {
      "general": {
        "name": "#openclaw-general",
        "purpose": "General OpenClaw updates and interactions"
      },
      "alerts": {
        "name": "#openclaw-alerts",
        "purpose": "Error alerts and system notifications"
      },
      "approvals": {
        "name": "#openclaw-approvals",
        "purpose": "HITL approval requests with interactive buttons"
      }
    },
    "approval_workflow": {
      "channel": "#openclaw-approvals",
      "button_style": true,
      "thread_replies": true,
      "mention_on_timeout": true
    }
  }
}
JSON
```

### Test Slack Integration

```
# In Slack:
/openclaw What are today's hot leads?
# Expected: Bot responds with lead summary

/leads
# Expected: Formatted lead report in channel

# Test approval flow:
# Trigger a HITL action from web UI or Telegram
# Expected: Approval message appears in #openclaw-approvals with buttons
```

---

## Day 7-8: WhatsApp (If Needed for Client Communication)

This is optional and most relevant if you plan to use OpenClaw for client-facing automation. Implement only when you have a specific use case.

### Set Up Twilio Account

1. Create account at https://www.twilio.com
2. Activate WhatsApp sandbox (for testing) or purchase a number
3. Note your Account SID, Auth Token, and WhatsApp number

### Configure WhatsApp in OpenClaw

```bash
cat >> ~/.openclaw/.env << 'ENV'

# WhatsApp via Twilio (optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
ENV

cat > ~/.openclaw/config/whatsapp-config.json << 'JSON'
{
  "whatsapp": {
    "enabled": false,
    "provider": "twilio",
    "webhook_url": "https://your-n8n-webhook-url/whatsapp-incoming",
    "templates": {
      "appointment_reminder": "Hi {{name}}, this is a reminder about your appointment on {{date}} at {{time}}. Reply CONFIRM to confirm or RESCHEDULE to change.",
      "lead_followup": "Hi {{name}}, thanks for reaching out to {{business}}. We'd love to help with {{service}}. When is a good time to chat?",
      "review_request": "Hi {{name}}, thanks for choosing {{business}}! If you had a great experience, we'd appreciate a review: {{review_link}}"
    },
    "auto_responses": {
      "business_hours": "9:00-17:00",
      "timezone": "America/Chicago",
      "out_of_hours_message": "Thanks for reaching out! We'll get back to you during business hours (9 AM - 5 PM CT).",
      "default_response": "Thanks for your message. A team member will respond shortly."
    },
    "routing": {
      "keywords": {
        "appointment": "route_to_scheduling",
        "price|cost|quote": "route_to_sales",
        "help|support|problem": "route_to_support"
      },
      "default": "route_to_general"
    },
    "hitl_required": true,
    "message_logging": true
  }
}
JSON
```

### Configure Webhook via n8n Relay

Since OpenClaw is not publicly accessible (by design), use n8n as a relay:

1. Create n8n workflow:
   - **Trigger**: Webhook (public URL that Twilio can reach)
   - **Process**: Parse incoming WhatsApp message
   - **Forward**: HTTP Request to OpenClaw `http://localhost:18789/api/whatsapp/incoming`
   - **Response**: Return OpenClaw's response to Twilio

2. Set the n8n webhook URL as the Twilio webhook for incoming messages

### Test WhatsApp Flow

1. Send a WhatsApp message to your Twilio number from your phone
2. Verify n8n receives it (check execution history)
3. Verify OpenClaw processes it (check logs)
4. Verify response sent back via WhatsApp
5. Test auto-responses outside business hours
6. Test keyword routing

---

## Day 9-10: Channel Testing and Optimization

### Cross-Channel Context Test

The most important test: does context persist across channels?

```bash
# Step 1: Start a conversation on web UI
# "I'm working on a strategy for Metro Dental in Phoenix"

# Step 2: Continue on Telegram
# "What were we working on for Metro Dental?"
# Expected: Agent recalls the strategy work from the web session

# Step 3: Ask for details on Slack (if configured)
# "/openclaw What's the status of the Metro Dental project?"
# Expected: Agent provides context from both previous interactions
```

### Channel-Specific Behavior Configuration

```bash
cat > ~/.openclaw/config/channel-behaviors.json << 'JSON'
{
  "channel_behaviors": {
    "web_ui": {
      "response_format": "detailed",
      "include_metadata": true,
      "max_response_length": "unlimited",
      "tone": "professional_detailed",
      "features": ["file_uploads", "inline_charts", "code_blocks", "tables"]
    },
    "telegram": {
      "response_format": "concise",
      "include_metadata": false,
      "max_response_length": 4000,
      "tone": "professional_brief",
      "features": ["inline_buttons", "notifications"],
      "formatting": "telegram_markdown"
    },
    "slack": {
      "response_format": "standard",
      "include_metadata": true,
      "max_response_length": 3000,
      "tone": "professional_collaborative",
      "features": ["blocks", "buttons", "threads"],
      "formatting": "slack_mrkdwn"
    },
    "whatsapp": {
      "response_format": "minimal",
      "include_metadata": false,
      "max_response_length": 1600,
      "tone": "friendly_professional",
      "features": ["templates", "quick_replies"],
      "formatting": "plain_text"
    }
  }
}
JSON
```

### Create Usage Guide

```bash
cat > ~/.openclaw/CHANNEL-GUIDE.md << 'MD'
# OpenClaw Channel Guide

## Web UI (http://mac-mini:3000)
Best for: Detailed work sessions, reports, complex tasks
Access: Tailscale VPN required (any device with a browser)
Features: Full dashboard, file uploads, charts, code blocks

### Common Tasks on Web UI
- Review daily dashboard and metrics
- Run and monitor pipeline executions
- Review and approve pending HITL actions
- Generate and download presentations
- Deep-dive into lead enrichment data

## Telegram Bot (@ontrack_openclaw_bot)
Best for: Quick commands, mobile access, notifications, HITL approvals
Access: Telegram app on any device (no VPN needed for the bot itself)

### Quick Commands
- `/status` - Is everything running?
- `/leads` - How many leads today?
- `/costs` - What have I spent?
- `/pipeline` - Latest pipeline results
- `/stop` - Emergency stop

### Natural Language
Just type any message to the bot:
- "Enrich ABC Plumbing in Austin TX"
- "How many hot leads this week?"
- "Create a contact for John Smith"

### Notifications You Will Receive
- HITL approval requests (tap Approve/Deny)
- Pipeline completion notifications
- Error alerts
- Daily summary at 6 PM

## Slack (#openclaw channels)
Best for: Team collaboration, shared visibility
Access: Slack workspace

### Slash Commands
- `/openclaw <request>` - Any request to OpenClaw
- `/leads` - Lead summary
- `/pipeline` - Pipeline status

### Channels
- #openclaw-general: Updates and interactions
- #openclaw-alerts: Error notifications
- #openclaw-approvals: HITL approval requests

## WhatsApp (optional, client-facing)
Best for: Client communication, automated responses
Access: Twilio WhatsApp number

### Automated Flows
- Appointment reminders
- Lead follow-ups
- Review requests
- Out-of-hours auto-response
MD
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| Web UI authenticated and accessible | Login from Windows via Tailscale | [ ] |
| Dashboard showing real data | Widgets display leads, costs, pipeline status | [ ] |
| Dashboard responsive on mobile | Access from phone browser | [ ] |
| Telegram bot responds to commands | `/status` returns system health | [ ] |
| Telegram natural language works | Free-text query returns useful response | [ ] |
| Telegram HITL buttons work | Approve/Deny buttons function correctly | [ ] |
| Telegram daily summary sent | Receive 6 PM summary automatically | [ ] |
| Cross-channel context maintained | Start on web, continue on Telegram | [ ] |
| Channel-specific formatting works | Telegram concise, web detailed | [ ] |
| Slack connected (if applicable) | Slash commands work in team workspace | [ ] |
| WhatsApp receiving (if applicable) | Inbound messages processed | [ ] |
| Channel guide documented | All channels documented with usage tips | [ ] |

---

## Channel Priority

If you are limited on time, implement in this order:

1. **Web UI** (already exists from Phase 1, just polish)
2. **Telegram** (highest value: mobile access + HITL + notifications)
3. **Slack** (only if you have a team)
4. **WhatsApp** (only when you have a client-facing use case)

---

## Next Phase

With multi-channel access working, proceed to [Phase 7 - Advanced Capabilities](phase-7-advanced.md) for LinkedIn outreach, competitive intelligence, and website generation.

# Slack App Channel -- OpenClaw Setup Guide

## Why Slack for Your Agency

Slack is the gold standard for professional team communication. If your agency team already uses Slack (or your clients do), integrating OpenClaw as a Slack app gives you:

- **Professional context** -- Slack is where work happens. Your agent lives alongside your team conversations, not in a separate app.
- **Rich UI** -- Slack Blocks provide the richest interactive message format of any channel: buttons, dropdowns, date pickers, modal forms, sections with images, and more.
- **Workflow integration** -- Slack's built-in workflow builder can trigger and be triggered by OpenClaw agents.
- **Approval workflows** -- Human-in-the-loop approvals via Slack messages with Approve/Deny buttons are natural and effective.
- **Enterprise adoption** -- Many clients use Slack. A shared Slack channel with an AI agent can deliver exceptional client service.

Slack is the recommended channel for team-internal agent interactions and professional workflows.

---

## Architecture Overview

```
User sends message in Slack
        |
        v
Slack servers detect event
        |
        v
Slack sends HTTP POST to your Events API endpoint (webhook)
  - Event: message, app_mention, reaction_added, slash command, etc.
        |
        v
OpenClaw Slack Adapter
  - Verifies request signature using signing secret
  - Parses event payload
  - Normalizes message
  - Routes to appropriate agent
        |
        v
Agent processes and responds
        |
        v
OpenClaw sends response via Slack Web API (using bot token)
  - Text, blocks, modals, file uploads
        |
        v
User sees response in Slack
```

**Important:** Unlike Discord (which uses a persistent WebSocket), Slack uses webhooks. Your OpenClaw instance must be reachable from the internet for Slack to deliver events. Use Tailscale Funnel, n8n relay, or another tunneling solution.

---

## Setup Steps

### Step 1: Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps).
2. Click **Create New App**.
3. Choose **From scratch** (not from manifest, though we will cover manifests later).
4. Name it "OpenClaw Agent" (or your preferred name).
5. Select the workspace you want to develop in.
6. Click **Create App**.

### Step 2: Configure Bot Permissions (OAuth Scopes)

1. In the app settings, go to **OAuth & Permissions**.
2. Scroll to **Scopes > Bot Token Scopes**.
3. Add the following scopes:

| Scope | Purpose |
|-------|---------|
| `chat:write` | Send messages as the bot |
| `channels:read` | List and get info about public channels |
| `channels:history` | Read messages in public channels the bot is in |
| `groups:read` | List and get info about private channels the bot is in |
| `groups:history` | Read messages in private channels the bot is in |
| `im:read` | Read info about DM conversations with the bot |
| `im:history` | Read DM messages with the bot |
| `files:read` | Access files shared in conversations |
| `files:write` | Upload and share files |
| `reactions:read` | See reactions on messages |
| `reactions:write` | Add reactions to messages |
| `users:read` | Get user info (names, emails) |
| `users:read.email` | Get user email addresses |
| `commands` | Register and respond to slash commands |
| `app_mentions:read` | Receive events when the bot is @mentioned |

### Step 3: Install the App to Your Workspace

1. In **OAuth & Permissions**, click **Install to Workspace**.
2. Review the permissions and click **Allow**.
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`). Save it securely.

### Step 4: Get the Signing Secret

1. In the app settings, go to **Basic Information**.
2. Under **App Credentials**, find the **Signing Secret**.
3. Copy and save it. This is used to verify that webhook requests genuinely come from Slack.

### Step 5: Configure Event Subscriptions

Events let Slack notify your bot when things happen (messages, mentions, reactions).

1. Go to **Event Subscriptions** in the app settings.
2. Toggle **Enable Events** to ON.
3. Set the **Request URL** to your webhook endpoint:
   ```
   https://your-domain.ts.net/webhooks/slack/events
   ```
   Slack will send a verification challenge to this URL. Your OpenClaw instance must be running and reachable to pass verification.

4. Under **Subscribe to bot events**, add:

| Event | When It Fires |
|-------|--------------|
| `message.channels` | Message posted in a public channel the bot is in |
| `message.groups` | Message posted in a private channel the bot is in |
| `message.im` | Direct message to the bot |
| `app_mention` | Bot is @mentioned in any channel |
| `reaction_added` | Someone reacts to a message (useful for approval workflows) |

5. Click **Save Changes**.

### Step 6: Configure Slash Commands

1. Go to **Slash Commands** in the app settings.
2. Click **Create New Command**.
3. Create the following commands:

**Command: /openclaw**
```
Command:        /openclaw
Request URL:    https://your-domain.ts.net/webhooks/slack/commands
Short Description: Interact with the AI agent
Usage Hint:     [ask|report|lead|status|task] [details]
```

**Or create individual commands:**

```
/ask        - Ask the AI agent a question
             URL: https://your-domain.ts.net/webhooks/slack/commands
             Hint: [your question]

/report     - Generate a report
             URL: https://your-domain.ts.net/webhooks/slack/commands
             Hint: [weekly|monthly|pipeline] [options]

/lead       - Manage leads
             URL: https://your-domain.ts.net/webhooks/slack/commands
             Hint: [lookup|create|update] [details]

/status     - Check project and system status
             URL: https://your-domain.ts.net/webhooks/slack/commands
```

### Step 7: Configure Interactivity (for Buttons and Modals)

1. Go to **Interactivity & Shortcuts** in the app settings.
2. Toggle **Interactivity** to ON.
3. Set the **Request URL** to:
   ```
   https://your-domain.ts.net/webhooks/slack/interactions
   ```
4. Optionally configure shortcuts (global shortcuts appear in the lightning bolt menu).

### Step 8: Configure OpenClaw

```bash
# Environment variables
SLACK_ENABLED=true
SLACK_BOT_TOKEN=<your-slack-bot-token>
SLACK_SIGNING_SECRET=abcdef1234567890abcdef1234567890
SLACK_APP_TOKEN=xapp-1-A1234567890-1234567890123-abcdef  # Only needed for Socket Mode
```

Configuration file:

```yaml
channels:
  slack:
    enabled: true
    bot_token: "${SLACK_BOT_TOKEN}"
    signing_secret: "${SLACK_SIGNING_SECRET}"
    webhook_paths:
      events: /webhooks/slack/events
      commands: /webhooks/slack/commands
      interactions: /webhooks/slack/interactions
    default_agent: team-assistant

    # Channel restrictions
    allowed_channels:
      - "#agent-chat"
      - "#lead-alerts"
      - "#daily-reports"
      - "#approvals"

    # Response behavior
    response_settings:
      respond_to_mentions: true       # @OpenClaw Agent what's the status?
      respond_to_dms: true            # Direct messages
      respond_to_commands: true       # Slash commands
      respond_in_threads: true        # Thread replies
      auto_thread: true               # Automatically reply in threads (keeps channels clean)
      unfurl_links: false             # Don't auto-preview links in bot messages

    # Appearance
    bot_profile:
      display_name: "OpenClaw Agent"
      icon_emoji: ":robot_face:"      # Or set a custom icon in app settings
```

### Step 9: Alternative -- Socket Mode (No Public URL Needed)

If you cannot expose a public webhook URL, Slack offers **Socket Mode** as an alternative. Instead of Slack sending webhooks to your server, your bot connects to Slack via WebSocket (similar to Discord).

1. In app settings, go to **Socket Mode** and enable it.
2. Generate an **App-Level Token** with the `connections:write` scope.
3. Set the token in OpenClaw:

```yaml
channels:
  slack:
    mode: socket           # Instead of webhook mode
    app_token: "${SLACK_APP_TOKEN}"   # xapp-... token
    bot_token: "${SLACK_BOT_TOKEN}"   # xoxb-... token
```

**Socket Mode trade-offs:**
- Pro: No public URL needed. Works behind NAT/firewall without tunneling.
- Con: Not recommended for production at scale. Websocket connections can drop.
- Con: Some Slack features may behave differently in Socket Mode.

**Recommendation:** Use webhooks via Tailscale Funnel for production. Use Socket Mode for development or if you cannot set up webhooks.

### Step 10: Test the Integration

1. Invite the bot to a channel: `/invite @OpenClaw Agent` in the channel.
2. @mention the bot: `@OpenClaw Agent what can you do?`
3. Try a slash command: `/openclaw ask What is the pipeline status?`
4. Send a DM to the bot.
5. Check that thread replies work.
6. Verify button interactions if you have approval workflows configured.

---

## Slack Blocks: Rich UI Elements

Slack Blocks are the most powerful messaging format available in any channel. They let you create structured, interactive messages.

### Example: Lead Notification with Actions

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "New Lead: John Smith"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Company:*\nAcme Corporation"
        },
        {
          "type": "mrkdwn",
          "text": "*Source:*\nGoogle Ads - SEO Campaign"
        },
        {
          "type": "mrkdwn",
          "text": "*Email:*\njohn@acme.com"
        },
        {
          "type": "mrkdwn",
          "text": "*Lead Score:*\n85/100 :star:"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Message:*\n> Interested in SEO services for our B2B SaaS product. Budget: $5k-10k/month. Looking to start in Q2."
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Add to CRM" },
          "style": "primary",
          "action_id": "lead_add_crm",
          "value": "lead_12345"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Schedule Call" },
          "action_id": "lead_schedule",
          "value": "lead_12345"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Disqualify" },
          "style": "danger",
          "action_id": "lead_disqualify",
          "value": "lead_12345"
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Received via OpenClaw | Jan 15, 2025 at 10:30 AM"
        }
      ]
    }
  ]
}
```

### Example: Daily Report

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Daily Report - January 15, 2025"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Pipeline Summary*\n:green_circle: 5 new leads\n:large_blue_circle: 12 active opportunities\n:yellow_circle: 3 pending proposals\n:red_circle: 1 at-risk deal"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Tasks Due Today*\n- [ ] Review Acme Corp proposal (assigned: @alice)\n- [ ] Send TechStart monthly report (assigned: @bob)\n- [x] Update campaign budgets (completed)"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Campaign Performance*\n:chart_with_upwards_trend: Google Ads: CTR 3.2% (+0.4%), CPC $1.85 (-$0.15)\n:chart_with_upwards_trend: Meta Ads: ROAS 4.2x (+0.3x), Spend $2,450\n:chart_with_downwards_trend: LinkedIn: CTR 0.8% (-0.1%), needs attention"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "View Full Report" },
          "action_id": "view_full_report",
          "url": "https://your-domain.ts.net/reports/daily/2025-01-15"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Ask a Question" },
          "action_id": "ask_about_report"
        }
      ]
    }
  ]
}
```

### Example: Approval Workflow

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Approval Required: Blog Post"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Client:* Acme Corporation\n*Title:* \"10 SEO Strategies for B2B SaaS in 2025\"\n*Author:* AI-generated, reviewed by @alice\n*Word Count:* 2,847"
      },
      "accessory": {
        "type": "button",
        "text": { "type": "plain_text", "text": "Preview" },
        "url": "https://docs.google.com/document/d/xxx"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Approve" },
          "style": "primary",
          "action_id": "approve_content",
          "value": "content_12345"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "Request Changes" },
          "style": "danger",
          "action_id": "request_changes",
          "value": "content_12345"
        },
        {
          "type": "static_select",
          "placeholder": { "type": "plain_text", "text": "Assign Reviewer" },
          "action_id": "assign_reviewer",
          "options": [
            { "text": { "type": "plain_text", "text": "Alice" }, "value": "alice" },
            { "text": { "type": "plain_text", "text": "Bob" }, "value": "bob" },
            { "text": { "type": "plain_text", "text": "Carol" }, "value": "carol" }
          ]
        }
      ]
    }
  ]
}
```

---

## Home Tab

Slack apps can have a custom Home tab that appears when users click on the app in the sidebar. This provides a dashboard-like experience.

```yaml
# Configure in OpenClaw
channels:
  slack:
    home_tab:
      enabled: true
      sections:
        - type: status          # System status, active agents
        - type: quick_actions   # Common actions as buttons
        - type: recent_activity # Last 5 agent interactions
        - type: pipeline        # Current lead/deal pipeline summary
```

The Home tab updates dynamically. When a user opens it, OpenClaw generates the current view based on live data.

---

## Use Cases for Your Agency

### 1. Agency Team Communication

The primary use case is giving your entire team access to the AI agent within Slack:
- Team members @mention the bot for questions about projects, clients, or campaigns.
- Bot responds in threads to keep channels clean.
- Slash commands provide structured access to specific functions.

### 2. Lead Alerts and Management

When a new lead arrives (from your website, ad campaigns, or referrals):
- Agent posts to `#lead-alerts` with full details and action buttons.
- Team member clicks "Add to CRM" or "Schedule Call."
- Agent executes the action and updates the message to reflect the status.

### 3. Daily/Weekly Reports

Scheduled automated reports:
- Agent posts daily pipeline summary to `#daily-reports` at 9 AM.
- Agent posts weekly performance report every Monday morning.
- Reports include rich formatting with metrics, charts (as images), and action items.

### 4. Approval Workflows (Human-in-the-Loop)

Critical for any AI-assisted workflow -- the agent does the work, a human approves:
- Content approval: Blog posts, social media posts, email campaigns.
- Budget approval: Campaign spend changes above a threshold.
- Client communication: Review outbound messages to clients before sending.
- Lead qualification: Agent scores a lead, human confirms or overrides.

### 5. Client Workspace (Slack Connect)

If your clients use Slack, you can use **Slack Connect** to create shared channels:
- Create a shared channel with the client's Slack workspace.
- Add the OpenClaw bot to the shared channel.
- Client can interact with the agent for status updates, without leaving their Slack.
- This is a premium, high-touch client experience.

---

## Event Subscriptions Detail

| Event | Trigger | Use Case |
|-------|---------|----------|
| `message.channels` | Any message in a public channel the bot is in | General agent interaction |
| `message.groups` | Any message in a private channel the bot is in | Private team conversations |
| `message.im` | Direct message to the bot | One-on-one agent interaction |
| `app_mention` | Bot is @mentioned | Primary trigger for agent in channels |
| `reaction_added` | Emoji reaction on a message | Quick approval (thumbsup = approve) |
| `file_shared` | File shared in a channel with the bot | Process uploaded documents |
| `member_joined_channel` | New member joins a channel | Onboarding message |

---

## Cost Considerations

### Slack Pricing (Affects Your Team, Not the Bot)

| Tier | Cost | Limitations |
|------|------|-------------|
| Free | $0 | 90-day message history, 10 integrations, no Slack Connect |
| Pro | $7.25/user/month | Full history, unlimited integrations, Slack Connect |
| Business+ | $12.50/user/month | Advanced admin, compliance features |
| Enterprise Grid | Custom pricing | Organization-wide deployment |

**The OpenClaw bot itself adds no Slack cost.** Slack does not charge per-message for bots. The cost is entirely your Slack workspace subscription.

**For a 5-person agency team:**
- Free tier: $0/month (but 90-day message limit is restrictive)
- Pro tier: $36.25/month (recommended)

### API Rate Limits

| Endpoint | Limit |
|----------|-------|
| Web API (most methods) | Tier 2: 20 requests/minute |
| chat.postMessage | Tier 4: 1 message/second per channel |
| Incoming webhooks | 1 request/second |
| Events API | 30,000 events/hour |
| Slash commands | No specific limit (but responses must be within 3 seconds, or use deferred response) |

---

## App Manifest (Alternative Setup)

Instead of configuring everything through the UI, you can define your entire Slack app as a manifest:

```yaml
# slack-app-manifest.yaml
display_information:
  name: OpenClaw Agent
  description: AI-powered assistant for agency operations
  background_color: "#1a1a2e"

features:
  bot_user:
    display_name: OpenClaw Agent
    always_online: true
  slash_commands:
    - command: /openclaw
      url: https://your-domain.ts.net/webhooks/slack/commands
      description: Interact with the AI agent
      usage_hint: "[ask|report|lead|status] [details]"
      should_escape: false

oauth_config:
  scopes:
    bot:
      - chat:write
      - channels:read
      - channels:history
      - groups:read
      - groups:history
      - im:read
      - im:history
      - files:read
      - files:write
      - reactions:read
      - reactions:write
      - users:read
      - users:read.email
      - commands
      - app_mentions:read

settings:
  event_subscriptions:
    request_url: https://your-domain.ts.net/webhooks/slack/events
    bot_events:
      - message.channels
      - message.groups
      - message.im
      - app_mention
      - reaction_added
  interactivity:
    is_enabled: true
    request_url: https://your-domain.ts.net/webhooks/slack/interactions
  org_deploy_enabled: false
  socket_mode_enabled: false
  token_rotation_enabled: false
```

To use the manifest:
1. Go to [api.slack.com/apps](https://api.slack.com/apps).
2. Click **Create New App > From an app manifest**.
3. Paste the YAML manifest.
4. Review and create.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Events not arriving | Webhook URL not reachable or not verified | Check Tailscale Funnel is running, verify URL responds to Slack challenge |
| "not_authed" error | Invalid or expired bot token | Re-install app to workspace, get new token |
| "missing_scope" error | Bot lacks required permission | Add scope in OAuth & Permissions, re-install app |
| Messages not appearing | Bot not invited to channel | Use `/invite @OpenClaw Agent` in the channel |
| Slash command timeout | Response took longer than 3 seconds | Implement deferred response (respond_later pattern) |
| Blocks rendering incorrectly | Invalid block structure | Use Slack Block Kit Builder to validate: app.slack.com/block-kit-builder |
| Bot responds to itself | Not filtering bot messages | Check for `bot_id` in event payload and ignore |
| Duplicate events | Slack retries on slow response | Respond with 200 immediately, process async; implement dedup by event ID |

---

## Security Best Practices

1. **Always verify the signing secret.** Every incoming request from Slack includes a signature. Verify it to prevent spoofed requests.
2. **Store tokens securely.** Bot token and signing secret in environment variables, never in code.
3. **Restrict channel access.** Configure `allowed_channels` so the bot only operates where intended.
4. **Audit interactions.** Log all bot interactions with user identity and timestamp.
5. **Rotate tokens periodically.** Slack allows token rotation; enable it for production.
6. **Least privilege scopes.** Only request the OAuth scopes you actually need.
7. **Slack Connect caution.** If using shared channels with clients, be careful about what data the agent can access and share.

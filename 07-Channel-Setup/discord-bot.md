# Discord Bot Channel -- OpenClaw Setup Guide

## Why Discord for Your Agency

Discord is a strong choice for team communication and community building. Originally designed for gaming communities, Discord has evolved into a general-purpose collaboration platform used by businesses, developer communities, and creator groups. For your marketing agency, Discord serves two potential purposes:

1. **Internal team workspace** -- An alternative to Slack where your team interacts with the OpenClaw agent, collaborates on projects, and receives notifications.
2. **Client community** -- If you build or manage community spaces for clients, a Discord bot provides agent-powered engagement.

Discord is free, supports rich message formatting through embeds, offers threaded conversations, and has a mature bot ecosystem. However, it is less "professional" than Slack in perception, so it works best for teams that already use Discord or for community-facing use cases.

---

## Architecture Overview

```
User sends message in Discord channel
        |
        v
Discord Gateway (WebSocket connection)
  - Discord pushes events to your bot in real-time
  - No webhook needed: Discord bots use a persistent WebSocket
        |
        v
OpenClaw Discord Adapter
  - Receives MESSAGE_CREATE event
  - Checks if message is directed at the bot (mention, command, or configured channel)
  - Normalizes message
  - Routes to appropriate agent
        |
        v
Agent processes and responds
        |
        v
OpenClaw sends response via Discord REST API
  - Text, embeds, components (buttons, selects), files
        |
        v
User sees response in Discord
```

**Key architectural difference from other channels:** Discord bots maintain a persistent WebSocket connection to Discord's gateway, rather than receiving webhooks. This means your bot is always connected and receives events in real-time. No public URL is required for receiving messages (unlike WhatsApp and Telegram webhooks). However, the bot process must be running continuously to maintain the connection.

---

## Setup Steps

### Step 1: Create a Discord Application

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications).
2. Log in with your Discord account.
3. Click **New Application**.
4. Name it something like "OpenClaw Agent" or "YourAgency Bot."
5. Optionally add a description and icon.
6. Note the **Application ID** (also called Client ID) -- you will need it later.

### Step 2: Create a Bot User

1. In your application settings, click **Bot** in the left sidebar.
2. Click **Add Bot** (or it may already be created).
3. Under the bot's username, click **Reset Token** to generate a new bot token.
4. **Copy and save this token immediately.** It is shown only once. If you lose it, you must reset it.
5. Configure these settings under the Bot page:
   - **Public Bot:** Turn OFF if you want only you to be able to add it to servers.
   - **Requires OAuth2 Code Grant:** Leave OFF.
   - **Message Content Intent:** Turn ON (required to read message content). You must also enable this in the "Privileged Gateway Intents" section.
   - **Server Members Intent:** Turn ON if you need to see member lists.

### Step 3: Set Bot Permissions

Your bot needs specific permissions to function. The required permissions are:

| Permission | Why Needed |
|-----------|------------|
| Send Messages | Bot needs to respond in channels |
| Read Messages/View Channels | Bot needs to see messages directed at it |
| Embed Links | Bot sends rich embed messages |
| Attach Files | Bot sends documents, images, reports |
| Add Reactions | Bot can react to acknowledge messages |
| Use Slash Commands | Bot registers and responds to /commands |
| Read Message History | Bot can reference earlier messages for context |
| Manage Threads | Bot can create and participate in threads |
| Send Messages in Threads | Bot responds within threads |

**Permission integer:** `277025770560` (this encodes all the permissions above).

### Step 4: Generate Invite URL and Add to Server

1. In the application settings, go to **OAuth2 > URL Generator**.
2. Under **Scopes**, select:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, select the permissions listed above (or enter the permission integer).
4. Copy the generated URL. It looks like:
   ```
   https://discord.com/api/oauth2/authorize?client_id=YOUR_APP_ID&permissions=277025770560&scope=bot%20applications.commands
   ```
5. Open this URL in your browser.
6. Select the server you want to add the bot to.
7. Click **Authorize**.
8. The bot appears in your server's member list (offline until you start it).

### Step 5: Get Your Server (Guild) ID

1. In Discord, go to **Settings > Advanced** and enable **Developer Mode**.
2. Right-click your server name in the left sidebar.
3. Click **Copy Server ID**.
4. This is your Guild ID (e.g., `1234567890123456789`).

### Step 6: Configure OpenClaw

```bash
# Environment variables
DISCORD_ENABLED=true
DISCORD_BOT_TOKEN=<your-discord-bot-token>
DISCORD_GUILD_ID=1234567890123456789
```

Configuration file:

```yaml
channels:
  discord:
    enabled: true
    bot_token: "${DISCORD_BOT_TOKEN}"
    guild_id: "${DISCORD_GUILD_ID}"
    default_agent: team-assistant

    # Channel restrictions: only respond in these channels
    allowed_channels:
      - name: "agent-chat"          # A dedicated channel for agent interaction
      - name: "lead-alerts"         # Notifications channel
      - name: "daily-reports"       # Automated reports

    # How the bot responds
    response_settings:
      respond_to_mentions: true     # @OpenClaw Agent what's the status?
      respond_to_dms: true          # Direct messages to the bot
      respond_to_commands: true     # Slash commands
      respond_in_threads: true      # Continue conversations in threads
      auto_thread: false            # Automatically create threads for conversations

    # Slash commands to register
    slash_commands:
      - name: ask
        description: "Ask the AI agent a question"
        options:
          - name: question
            description: "Your question"
            type: STRING
            required: true
      - name: report
        description: "Generate a report"
        options:
          - name: type
            description: "Report type"
            type: STRING
            required: true
            choices:
              - name: "Weekly Performance"
                value: weekly
              - name: "Monthly Summary"
                value: monthly
              - name: "Lead Pipeline"
                value: pipeline
      - name: lead
        description: "Look up or create a lead"
        options:
          - name: action
            description: "Action to take"
            type: STRING
            required: true
            choices:
              - name: "Look Up"
                value: lookup
              - name: "Create New"
                value: create
          - name: name
            description: "Lead name or company"
            type: STRING
            required: true
      - name: status
        description: "Check system and project status"
```

### Step 7: Test the Bot

1. Start OpenClaw with Discord channel enabled.
2. The bot should appear as "Online" in your server's member list.
3. Go to the `#agent-chat` channel (or whichever channel you configured).
4. Type `@OpenClaw Agent hello` -- the bot should respond.
5. Try `/ask question: What is the status of active projects?` -- slash command should work.
6. Try `/report type: weekly` -- should generate a report.
7. Send a DM to the bot -- should respond if DMs are enabled.
8. Check that the bot does NOT respond in channels not listed in `allowed_channels`.

---

## Bot Capabilities

### Embeds (Rich Cards)

Discord embeds are the equivalent of Slack blocks or email HTML -- they create visually rich, structured messages.

```yaml
# Agent sends an embed for a lead notification
response:
  type: embed
  embed:
    title: "New Lead: John Smith"
    description: "Submitted via website contact form"
    color: 0x00ff00    # Green sidebar
    fields:
      - name: "Company"
        value: "Acme Corporation"
        inline: true
      - name: "Source"
        value: "Google Ads Campaign"
        inline: true
      - name: "Email"
        value: "john@acme.com"
        inline: true
      - name: "Message"
        value: "Interested in SEO services for our B2B SaaS product. Budget: $5k-10k/month."
        inline: false
    footer:
      text: "Lead Score: 85/100 | Priority: High"
    timestamp: "2025-01-15T10:30:00Z"
```

### Components (Buttons and Select Menus)

```yaml
# Agent sends action buttons
response:
  text: "How should I handle this lead?"
  components:
    - type: ACTION_ROW
      components:
        - type: BUTTON
          style: PRIMARY
          label: "Add to CRM"
          custom_id: "lead_add_crm_12345"
        - type: BUTTON
          style: SUCCESS
          label: "Schedule Call"
          custom_id: "lead_schedule_12345"
        - type: BUTTON
          style: DANGER
          label: "Disqualify"
          custom_id: "lead_disqualify_12345"
    - type: ACTION_ROW
      components:
        - type: STRING_SELECT
          custom_id: "lead_assign_12345"
          placeholder: "Assign to team member..."
          options:
            - label: "Alice"
              value: "alice"
            - label: "Bob"
              value: "bob"
            - label: "Carol"
              value: "carol"
```

### Threads

Threads keep conversations organized. The bot can:
- Create a thread from a message for extended discussion.
- Respond within existing threads.
- Auto-archive threads after inactivity.

```yaml
# Agent creates a thread for a detailed conversation
response:
  action: create_thread
  thread_name: "Lead Discussion: Acme Corp"
  initial_message: "Let's discuss how to handle the Acme Corp lead. Here's what I know..."
```

### File Sharing

The bot can send files (reports, documents, images):

```yaml
response:
  text: "Here's your weekly performance report:"
  files:
    - path: "/tmp/reports/weekly-performance-2025-01-15.pdf"
      filename: "weekly-performance.pdf"
    - path: "/tmp/charts/traffic-chart.png"
      filename: "traffic-chart.png"
```

---

## Channel Management: Organizing Your Server

For an effective agency setup, structure your Discord server with dedicated channels:

```
YOUR AGENCY SERVER
|
|-- CATEGORY: OpenClaw Agent
|   |-- #agent-chat         (General agent interaction, team-wide)
|   |-- #lead-alerts        (Agent posts new leads here automatically)
|   |-- #daily-reports      (Automated daily/weekly reports)
|   |-- #approvals          (Items needing human approval, with buttons)
|   |-- #errors-and-logs    (Agent error notifications)
|
|-- CATEGORY: Projects
|   |-- #project-acme       (Client-specific channel)
|   |-- #project-techstart  (Client-specific channel)
|
|-- CATEGORY: Team
|   |-- #general            (Team chat, bot not active here)
|   |-- #random             (Off-topic, bot not active here)
```

Configure `allowed_channels` so the bot only operates in the channels where it belongs.

---

## Role-Based Access

Discord's role system lets you control who can interact with the bot and what they can do.

```yaml
channels:
  discord:
    role_permissions:
      admin:                        # Discord role name
        allowed_commands: all
        can_configure: true
        can_view_memory: true
      manager:
        allowed_commands:
          - ask
          - report
          - lead
          - status
        can_configure: false
        can_view_memory: false
      team_member:
        allowed_commands:
          - ask
          - status
        can_configure: false
        can_view_memory: false
```

This ensures that only authorized team members can run sensitive commands (like viewing lead details or generating reports).

---

## Use Cases for Your Agency

### 1. Team Workspace

Use Discord as your agency's internal communication hub with AI assistance:
- Team asks the agent questions in `#agent-chat`.
- Agent posts lead alerts in `#lead-alerts` with action buttons.
- Agent generates daily reports in `#daily-reports` every morning.
- Approval requests go to `#approvals` with Approve/Deny buttons.

### 2. Client Community

If you manage communities for clients (or your own agency community):
- Bot moderates and answers questions.
- Bot provides onboarding information to new members.
- Bot collects feedback via polls and surveys.

### 3. Development and Testing

Discord is a convenient environment for testing agent interactions:
- Create a `#testing` channel for development.
- Test new skills and responses before deploying to production channels.
- Use threads to isolate test conversations.
- Review bot behavior in real-time with your team.

---

## Rate Limits

Discord has layered rate limits:

| Scope | Limit |
|-------|-------|
| Global | 50 requests per second |
| Per channel | 5 messages per second |
| Per guild (server) | Varies by endpoint |
| Slash command response | Must respond within 3 seconds (can defer for longer processing) |
| Interaction followup | 15 minutes after initial interaction |

**Handling rate limits in OpenClaw:**
- OpenClaw's Discord adapter should implement automatic rate limit handling.
- If the agent tries to send too many messages too quickly, the adapter queues them and sends at the maximum allowed rate.
- For slash commands that take more than 3 seconds to process (e.g., generating a report), the adapter sends a "thinking..." deferred response, then follows up with the actual response when ready.

---

## Advantages

- **Free** -- No per-message cost, no subscription required for bot usage.
- **Rich formatting** -- Embeds create professional, structured messages.
- **Threads** -- Keep conversations organized without cluttering the main channel.
- **Components** -- Buttons and select menus for structured interactions.
- **Real-time** -- WebSocket connection means instant message delivery.
- **Slash commands** -- Discoverable, typed commands with autocomplete.
- **Roles** -- Built-in permission system for access control.
- **Persistent connection** -- No webhook setup needed; bot connects directly.

---

## Limitations

- **Perception** -- Discord is perceived as less professional than Slack. May not be appropriate for client-facing communication.
- **No modals** -- Unlike Slack, Discord bots cannot open form modals (as of current API). Complex data entry requires multi-message flows.
- **Gateway connection** -- Bot must maintain a persistent WebSocket connection. If the connection drops, there is a brief period where messages are missed.
- **Slash command registration** -- Global commands can take up to 1 hour to propagate. Guild commands are instant.
- **File size limit** -- 25 MB for free servers, 50 MB with Nitro boosts.
- **Message length** -- 2000 characters per message, 4096 characters for embed descriptions. Long reports must be split or sent as files.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Bot shows offline | Process not running or WebSocket disconnected | Restart OpenClaw, check logs for connection errors |
| Slash commands not showing | Commands not registered or still propagating | Register as guild commands for instant availability |
| "Missing Permissions" error | Bot lacks required permissions | Re-invite with correct permission integer |
| Bot responds in wrong channels | `allowed_channels` not configured | Set channel restrictions in config |
| "Interaction failed" on buttons | Response took too long (>3s) | Implement deferred response pattern |
| Can't read messages | Message Content Intent not enabled | Enable in Discord Developer Portal > Bot > Privileged Intents |
| Rate limited | Sending too many messages | Implement queue with rate limit handling |
| Bot can't DM users | User has DMs disabled for server members | Cannot override, provide guidance to enable DMs |

---

## Security Notes

1. **Bot token** -- Treat it like a password. Never commit to git. Store in environment variables.
2. **Channel restrictions** -- Always configure `allowed_channels`. Do not let the bot respond everywhere.
3. **Role-based access** -- Use Discord roles to restrict who can run which commands.
4. **Audit logging** -- Log all bot interactions for review.
5. **Private bot** -- Disable "Public Bot" in the Developer Portal so only you can add it to servers.
6. **Intents** -- Only enable the gateway intents you actually need. Enabling unnecessary privileged intents is a security risk and may cause your bot to be flagged for review by Discord.

# Telegram Bot Channel -- OpenClaw Setup Guide

## Why Telegram Is Your Best Personal Channel

Telegram is the single best channel to set up after the Web UI. Here is why:

- **Completely free.** No per-message charges, no monthly fees, no limits on usage.
- **Easiest to set up.** A working Telegram bot takes under 15 minutes from scratch.
- **Rich features.** Inline keyboards, commands, file sharing, markdown formatting, polls, and more.
- **Excellent mobile experience.** Telegram's app is fast, reliable, and available on every platform (iOS, Android, desktop, web).
- **Group support.** Add your bot to team group chats for shared agent access.
- **High rate limits.** 30 messages per second is more than enough for any personal or small-team use.
- **Privacy-respecting.** Bots in groups only see messages directed at them (via @mention or /command).

For your daily workflow, Telegram becomes the fastest way to interact with your OpenClaw agent: ask a question, create a task, check a lead, get a report -- all from your phone in seconds.

---

## Setup Steps

### Step 1: Create a Bot via @BotFather

@BotFather is Telegram's official bot for managing bots. You interact with it like a regular chat.

1. Open Telegram (mobile or desktop).
2. Search for `@BotFather` and start a conversation.
3. Send the command: `/newbot`
4. BotFather asks for a display name. Enter something like: `OpenClaw Assistant`
5. BotFather asks for a username. It must end in `bot`. Enter something like: `YourAgency_OpenClaw_bot`
6. BotFather responds with your **bot token**. It looks like: `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
7. **Save this token securely.** Anyone with this token can control your bot. Treat it like a password.

**Optional but recommended -- configure the bot profile:**

```
/setdescription    -> "AI assistant for [Your Agency Name]. Manages tasks,
                      reports, leads, and client communications."
/setabouttext      -> "Powered by OpenClaw. Ask me anything about your
                      projects, clients, and campaigns."
/setuserpic        -> Upload your agency logo or an appropriate avatar.
```

### Step 2: Define Bot Commands

Commands give users a quick way to invoke specific actions. Define them through BotFather:

1. Send `/setcommands` to @BotFather.
2. Select your bot.
3. Send the command list in this format:

```
help - Show available commands and how to use this bot
status - Check system status and active agents
report - Generate a report (usage: /report [type] [period])
lead - Look up or create a lead (usage: /lead [name or action])
task - Create or check tasks (usage: /task [description])
client - Look up client information (usage: /client [name])
remind - Set a reminder (usage: /remind [time] [message])
search - Search across all your data (usage: /search [query])
```

These commands will appear as autocomplete suggestions when users type `/` in the chat with your bot.

### Step 3: Configure OpenClaw

Set the environment variable or configuration:

```bash
# Environment variable
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Or in the configuration file:

```yaml
channels:
  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    webhook_path: /webhooks/telegram
    default_agent: personal-assistant   # Which agent handles Telegram messages
    parse_mode: MarkdownV2              # Response formatting (MarkdownV2 or HTML)
    allowed_users:                       # Optional: restrict to specific users
      - 123456789                        # Your Telegram user ID
      - 987654321                        # Team member's Telegram user ID
    group_settings:
      respond_to_mentions: true          # Respond when @mentioned in groups
      respond_to_replies: true           # Respond when someone replies to the bot
      respond_to_all: false              # Do NOT respond to every message in groups
    commands:
      help:
        description: "Show available commands"
        agent_action: show_help
      status:
        description: "Check system status"
        agent_action: system_status
      report:
        description: "Generate a report"
        agent_action: generate_report
      lead:
        description: "Look up or create a lead"
        agent_action: manage_lead
      task:
        description: "Create or check tasks"
        agent_action: manage_task
```

### Step 4: Set Up the Webhook

OpenClaw needs to receive messages from Telegram. There are two methods:

**Method A: Webhook (Recommended for Production)**

Telegram sends an HTTPS POST to your server whenever someone messages your bot.

```bash
# OpenClaw typically registers the webhook automatically on startup.
# If you need to set it manually:
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.ts.net/webhooks/telegram",
    "allowed_updates": ["message", "callback_query", "inline_query"],
    "secret_token": "your-webhook-secret"
  }'
```

Your webhook URL must be HTTPS. Options:
- **Tailscale Funnel:** `tailscale funnel 443 /webhooks/telegram=http://localhost:8080/webhooks/telegram`
- **n8n relay:** Route through your n8n instance.

**Method B: Long Polling (Easier for Development)**

Instead of receiving webhooks, OpenClaw periodically asks Telegram for new messages. No public URL needed.

```yaml
channels:
  telegram:
    mode: polling        # Instead of webhook
    poll_interval: 1000  # Check every 1 second (in milliseconds)
```

Polling is simpler (no public URL required) but slightly slower and less efficient. Use it for local development, switch to webhooks for production.

### Step 5: Find Your Telegram User ID

To restrict the bot to only respond to you (security measure), you need your Telegram user ID:

1. Message `@userinfobot` on Telegram.
2. It responds with your user ID (a number like `123456789`).
3. Add this to `allowed_users` in the config.

Alternatively, check the OpenClaw logs when you first message your bot. The incoming message payload includes your user ID.

### Step 6: Test the Bot

1. Open Telegram and find your bot by its username (e.g., `@YourAgency_OpenClaw_bot`).
2. Send `/start` -- the bot should respond with a welcome message.
3. Send a plain text message -- the agent should process it and respond.
4. Test `/help` -- should show the command list.
5. Send an image -- verify the agent receives it (check logs).
6. Send a document -- verify document handling.
7. Test inline keyboard responses if your agent sends them.

---

## Bot Capabilities and Message Types

### Sending Text with Formatting

Telegram supports two formatting modes. MarkdownV2 is recommended:

```markdown
*bold text*
_italic text_
__underline__
~strikethrough~
||spoiler||
`inline code`
```pre-formatted code block```
[link text](https://example.com)
```

### Inline Keyboards (Buttons)

Your agent can send messages with interactive button rows:

```yaml
# Agent response with inline keyboard
response:
  text: "New lead: John Smith from Acme Corp. How should I handle this?"
  reply_markup:
    inline_keyboard:
      - - text: "Add to CRM"
          callback_data: "lead_action:add_crm:12345"
        - text: "Schedule Call"
          callback_data: "lead_action:schedule:12345"
      - - text: "Send Info Pack"
          callback_data: "lead_action:info_pack:12345"
        - text: "Not Qualified"
          callback_data: "lead_action:disqualify:12345"
```

When you tap a button, Telegram sends a `callback_query` to OpenClaw with the `callback_data` value. The agent processes it accordingly.

### Reply Keyboards (Quick Replies)

For simpler interactions, show a custom keyboard:

```yaml
response:
  text: "What type of report do you need?"
  reply_markup:
    keyboard:
      - - text: "Weekly Performance"
        - text: "Monthly Summary"
      - - text: "Client Report"
        - text: "Lead Pipeline"
    resize_keyboard: true
    one_time_keyboard: true
```

### File and Media Handling

| Content Type | Send | Receive | Max Size |
|-------------|------|---------|----------|
| Photos | Yes | Yes | 10 MB |
| Documents | Yes | Yes | 50 MB |
| Audio | Yes | Yes | 50 MB |
| Video | Yes | Yes | 50 MB |
| Voice notes | Yes | Yes | 50 MB |
| Stickers | Yes | Yes | N/A |
| Location | Yes | Yes | N/A |
| Contact | Yes | Yes | N/A |
| Polls | Yes (create) | Yes (results) | N/A |

---

## Group Chat Support

Adding your bot to a Telegram group gives your entire team shared access to the agent.

### How to Add the Bot to a Group

1. Open the group in Telegram.
2. Tap the group name to open settings.
3. Tap "Add Members."
4. Search for your bot by username.
5. Add it to the group.

### Group Privacy Mode

By default, Telegram bots in groups only see:
- Messages that start with a `/command`
- Messages that `@mention` the bot
- Replies to the bot's own messages

This is called **privacy mode** and it is enabled by default. It means the bot does not see every message in the group, only those directed at it. This is good for privacy but limits the bot's ability to participate in general conversation.

**To disable privacy mode** (so the bot sees all messages):
1. Message @BotFather: `/setprivacy`
2. Select your bot.
3. Choose "Disable."

**Recommendation:** Keep privacy mode enabled for most groups. Use @mentions when you want the bot to respond. This prevents the agent from trying to process every casual message in the group.

### Group Configuration in OpenClaw

```yaml
channels:
  telegram:
    group_settings:
      respond_to_mentions: true     # @bot_name what's the status?
      respond_to_replies: true      # Reply to a bot message to continue the thread
      respond_to_commands: true     # /report weekly
      respond_to_all: false         # Do NOT respond to every message
      quiet_hours:                  # Don't send proactive messages during these hours
        start: "22:00"
        end: "08:00"
        timezone: "America/New_York"
```

---

## Use Cases for Your Agency

### 1. Personal Assistant (Primary Use)

Your most frequent interaction with OpenClaw will likely be through Telegram on your phone:

- "What meetings do I have today?"
- "Create a task: review Acme Corp proposal by Friday"
- "What's the latest on the TechStart campaign?"
- "Send me the monthly report summary"
- "/lead John Smith" -- quick lead lookup
- Send a screenshot of an ad for the agent to analyze

### 2. Team Group Agent

Create a Telegram group with your team and add the bot:

- Team members @mention the bot for questions
- Bot posts daily summaries to the group (scheduled)
- "/status" shows current project pipeline
- Bot alerts the group about new leads or urgent issues

### 3. Notification Channel

Agent proactively sends you important alerts:

- New high-value lead came in
- Client responded to a proposal
- Campaign budget threshold reached
- Scheduled task reminder
- Error alerts from other integrations

### 4. Quick Data Entry

Use Telegram to quickly capture information on the go:

- Forward an email screenshot for the agent to extract and log contact info
- Voice note with meeting notes for the agent to transcribe and create tasks
- Quick text: "Log call with Sarah at Acme, discussed Q2 budget, she'll send brief by Wed"

---

## Advantages Over Other Channels

| Advantage | Detail |
|-----------|--------|
| Zero cost | No per-message fees, no monthly subscription, no phone number needed |
| Instant setup | Under 15 minutes from zero to working bot |
| Speed | Telegram delivers messages faster than any other platform |
| Rich features | Keyboards, buttons, file sharing, formatting, polls, locations |
| Multi-device | Seamlessly use on phone, tablet, and desktop simultaneously |
| No 24h window | Unlike WhatsApp, you can message anytime without templates |
| Cloud-based | Message history syncs across all devices |
| API quality | Telegram Bot API is well-documented and reliable |
| Bot ecosystem | Huge community, many examples and libraries |

---

## Limitations

- **30 messages per second** -- Global rate limit across all conversations. More than sufficient for personal and team use, but could be a constraint if you somehow serve thousands of users.
- **20 messages per minute per group** -- Cannot flood a group chat.
- **No voice/video calls** -- Bots cannot initiate or join Telegram voice/video calls.
- **No Stories** -- Bots cannot post to Telegram Stories.
- **File size limits** -- 50 MB for documents, 10 MB for photos.
- **Less professional than Slack** -- Telegram is perceived as a personal messenger. Use Slack for professional team communication and client-facing channels.
- **No built-in approval workflows** -- Unlike Slack's modals and workflows, Telegram relies on inline keyboards for structured interactions.

---

## Security Considerations

1. **Restrict allowed users.** Always configure `allowed_users` with specific Telegram user IDs. Without this, anyone who finds your bot can interact with your agent.
2. **Bot token security.** Store the token in environment variables or a secrets manager, never in plain text config files committed to git.
3. **Webhook secret.** When using webhooks, set a `secret_token` so OpenClaw can verify requests genuinely come from Telegram.
4. **Group access.** Be deliberate about which groups you add the bot to. Remove it from groups it no longer needs to be in.
5. **Privacy mode.** Keep privacy mode enabled in groups unless you have a specific reason to disable it.

---

## Recommended as Primary Personal Channel

Among all the channels OpenClaw supports, Telegram is the recommended primary personal channel because:

1. You can set it up today in 15 minutes for free.
2. It works on your phone, making your agent accessible anywhere.
3. The rich feature set (buttons, files, formatting) provides a great user experience.
4. No message costs means you can interact as much as you want without worrying about bills.
5. Group support means your team can share the same bot.
6. The 24/7 availability (no session windows like WhatsApp) means the agent can always reach you.

Set this up immediately after the Web UI. It will become your most-used channel.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Bot not responding | Webhook not set or wrong URL | Check `getWebhookInfo` API, verify URL is correct |
| Bot responds slowly | Using polling with long interval | Switch to webhooks, or reduce poll interval |
| No messages in groups | Privacy mode enabled | @mention the bot, or disable privacy mode via BotFather |
| "Unauthorized" error | Invalid or expired bot token | Regenerate token via BotFather `/token` |
| Formatting broken | Wrong parse mode | Use MarkdownV2 and escape special characters: `_*[]()~>#+\-=\|{}.!` |
| Can't send files | File too large | Compress or split files, respect 50 MB limit |
| Bot added to unwanted group | Anyone can add bots to groups | Check `allowed_users` or group whitelist in config |

**Useful Telegram Bot API debugging commands:**

```bash
# Check webhook status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# Get bot info
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"

# Remove webhook (to switch to polling)
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/deleteWebhook"

# Send a test message to yourself
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": YOUR_USER_ID, "text": "Test message from OpenClaw"}'
```

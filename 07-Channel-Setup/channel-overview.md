# Channel Overview -- OpenClaw Multi-Channel Architecture

## What Channels Are in OpenClaw

Channels are the communication endpoints through which humans interact with OpenClaw agents. A channel can be a messaging platform (WhatsApp, Telegram), a collaboration tool (Slack, Discord), the built-in web UI, or traditional communication mediums (SMS, email). OpenClaw treats all channels uniformly through an abstraction layer, meaning your agents do not need to know or care which platform a message originated from. The same agent logic, skills, and memory work identically regardless of whether the user typed a message in Telegram or clicked a button in Slack.

---

## Channel Abstraction: How OpenClaw Normalizes Messages

OpenClaw implements a **channel adapter pattern**. Each supported platform has a dedicated adapter that handles the platform-specific protocol (webhooks, WebSockets, polling) and converts inbound messages into a normalized internal format. This means:

- A WhatsApp text message, a Telegram text message, and a Slack message all become the same internal `TextMessage` object.
- An image sent via Discord and an image sent via WhatsApp both become an `ImageMessage` with a URL and optional caption.
- Platform-specific features (Slack blocks, Telegram inline keyboards, Discord embeds) are mapped to a generic `RichMessage` schema, with graceful fallback to plain text on platforms that lack those features.

**Normalized message schema (conceptual):**

```
InboundMessage {
  channel: "whatsapp" | "telegram" | "discord" | "slack" | "web" | "sms" | "email"
  sender_id: string           // platform-specific user identifier
  conversation_id: string     // thread, group, or DM identifier
  message_type: "text" | "image" | "document" | "location" | "action" | "command"
  content: string | object    // text body or structured payload
  metadata: {
    platform_message_id: string
    timestamp: ISO8601
    reply_to: string | null
    attachments: Attachment[]
  }
}
```

When an agent responds, the outbound message goes through the reverse process: the adapter takes the normalized response and converts it into platform-native formatting (Slack blocks, Telegram Markdown, WhatsApp template, Discord embed, etc.).

---

## Channel Architecture: Message Flow

The end-to-end message flow is:

```
User sends message on platform (e.g., WhatsApp)
        |
        v
Platform delivers to webhook/WebSocket endpoint
        |
        v
Channel Adapter (e.g., Twilio WhatsApp adapter)
  - Authenticates the request (signature verification)
  - Parses platform-specific payload
  - Normalizes into InboundMessage
        |
        v
Message Router
  - Identifies which agent should handle this message
  - Resolves conversation context (existing session or new)
  - Loads relevant memory/context
        |
        v
Agent Processing
  - Agent receives normalized message + context
  - Invokes LLM with system prompt, memory, skills
  - Produces response (text, actions, rich content)
        |
        v
Response Router
  - Takes agent output
  - Determines response channel (same as inbound, or cross-channel if configured)
        |
        v
Channel Adapter (outbound)
  - Converts normalized response to platform format
  - Handles platform constraints (message length, media types)
  - Sends via platform API
        |
        v
User receives response on their platform
```

**Key implementation detail:** The webhook endpoints for each channel must be reachable from the internet. For a self-hosted setup on a Mac Mini behind NAT, this means either:

- **Tailscale Funnel** -- Expose a specific port through your Tailscale network to the public internet. Recommended for direct webhook delivery.
- **n8n relay** -- Use an n8n workflow on a cloud instance as a relay. The n8n instance receives the webhook, processes or forwards it to your Mac Mini over Tailscale.
- **Cloudflare Tunnel** -- Alternative to Tailscale Funnel if you prefer Cloudflare's infrastructure.

---

## Supported Channels

| Channel | Cost | Setup Difficulty | Best For | Rate Limits |
|---------|------|-----------------|----------|-------------|
| **Web UI** | Free | None (built-in) | Testing, management, admin | Unlimited (local) |
| **Slack** | Free (Slack free tier) or $7.25/user/mo | Medium | Team collaboration, professional use | 1 msg/sec per channel, 50K events/hr |
| **WhatsApp** | $0.005--0.08/msg (Twilio) | Hard | Client communication, external contacts | 80 msg/sec (Twilio), 250 msg/sec (Meta) |
| **Telegram** | Free | Easy | Personal use, quick access, team groups | 30 msg/sec, 20 msg/min to same group |
| **Discord** | Free | Medium | Community, team workspace | 50 req/sec global, 5/sec per channel |
| **SMS** | $0.0079/msg (Twilio) | Medium | Alerts, fallback, non-smartphone users | 1 msg/sec per number |
| **Email** | Free (SMTP) or varies | Medium | Formal communication, long-form, documents | Varies by provider |

---

## Multi-Channel Conversations: Shared Context

One of OpenClaw's most powerful features is **cross-channel context continuity**. A single contact (identified by email, phone, or a unified profile) can interact with the same agent across multiple channels while maintaining a single conversation thread.

**How it works:**

1. **Contact resolution** -- When a message arrives, OpenClaw resolves the sender to a unified contact record. A WhatsApp number, Telegram username, and Slack user ID can all map to the same contact.
2. **Shared memory** -- The agent's memory (short-term conversation context + long-term knowledge) is tied to the contact, not the channel. If a client asks about project status on WhatsApp in the morning, then follows up on Slack in the afternoon, the agent remembers both interactions.
3. **Channel preference** -- Each contact can have a preferred channel for outbound messages. If the agent needs to proactively notify a client, it uses their preferred channel.

**Configuration for contact unification:**

```yaml
# In OpenClaw config
contacts:
  unification:
    match_by:
      - phone_number    # matches WhatsApp and SMS
      - email           # matches Email and Slack (if email linked)
      - custom_id       # your CRM identifier
    auto_link: true     # automatically link when same phone/email detected
```

---

## Channel Configuration: Per-Channel Settings

Each channel is configured in the OpenClaw configuration file (typically `config.yaml` or environment variables). The general structure is:

```yaml
channels:
  web:
    enabled: true
    port: 3000
    auth:
      username: admin
      password: "${WEB_UI_PASSWORD}"

  whatsapp:
    enabled: true
    provider: twilio
    account_sid: "${TWILIO_ACCOUNT_SID}"
    auth_token: "${TWILIO_AUTH_TOKEN}"
    phone_number: "+1234567890"
    webhook_path: /webhooks/whatsapp

  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    webhook_path: /webhooks/telegram

  discord:
    enabled: true
    bot_token: "${DISCORD_BOT_TOKEN}"
    guild_id: "${DISCORD_GUILD_ID}"
    allowed_channels:
      - "general"
      - "agent-chat"

  slack:
    enabled: true
    bot_token: "${SLACK_BOT_TOKEN}"
    signing_secret: "${SLACK_SIGNING_SECRET}"
    webhook_path: /webhooks/slack

  sms:
    enabled: false
    provider: twilio
    # Same Twilio credentials as WhatsApp

  email:
    enabled: false
    imap:
      host: imap.gmail.com
      port: 993
      username: "${EMAIL_ADDRESS}"
      password: "${EMAIL_APP_PASSWORD}"
    smtp:
      host: smtp.gmail.com
      port: 587
      username: "${EMAIL_ADDRESS}"
      password: "${EMAIL_APP_PASSWORD}"
```

---

## Channel Priority: Recommended Setup Order

Set up channels in this order, from easiest/most useful to most complex:

### 1. Web UI (Day 1 -- Immediate)

- **Why first:** It is built-in, requires zero external configuration, and gives you immediate access to test everything.
- **Use it for:** Agent configuration, skill testing, memory inspection, debugging, admin tasks.
- **Time to set up:** 0 minutes (it starts with OpenClaw).

### 2. Telegram Bot (Day 1 -- 15 minutes)

- **Why second:** Completely free, takes under 15 minutes, and gives you a mobile-accessible personal assistant channel immediately.
- **Use it for:** Personal assistant queries, quick lookups, task creation on the go, testing agent responses from a real messaging app.
- **Time to set up:** 10-15 minutes.

### 3. Slack App (Week 1 -- 30 minutes)

- **Why third:** If you have a team, Slack is where professional collaboration happens. Rich formatting, threads, and workflow integration make it the best team channel.
- **Use it for:** Team-wide agent access, daily reports, lead alerts, approval workflows.
- **Time to set up:** 20-30 minutes.

### 4. WhatsApp Business (Week 2 -- 1-2 hours)

- **Why fourth:** Client-facing communication is critical but requires more setup (Twilio account, phone number, message templates, compliance). Get your internal channels working first.
- **Use it for:** Client status updates, appointment reminders, lead nurture sequences, approval requests.
- **Time to set up:** 1-2 hours (including Twilio setup and template approval).

### 5. Discord Bot (When Needed)

- **Why fifth:** Only needed if you run a community server or prefer Discord for team chat. Lower priority than the above.
- **Use it for:** Community engagement, team workspace (alternative to Slack), development testing.
- **Time to set up:** 20-30 minutes.

### 6. SMS and Email (When Needed)

- **Why last:** These are supplementary channels for specific use cases (SMS alerts, email reports). Not needed for core functionality.
- **Time to set up:** 30-60 minutes each.

---

## Channel-Specific Features

Not all channels support the same features. Here is what each channel can do:

| Feature | Web UI | WhatsApp | Telegram | Discord | Slack | SMS | Email |
|---------|--------|----------|----------|---------|-------|-----|-------|
| Plain text | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Rich formatting | HTML | Limited | Markdown | Markdown | Blocks | No | HTML |
| Images | Yes | Yes | Yes | Yes | Yes | MMS | Attachments |
| Documents/Files | Yes | Yes | Yes | Yes | Yes | No | Attachments |
| Buttons/Actions | Yes | Yes (3 max) | Yes (inline KB) | Yes (components) | Yes (blocks) | No | No |
| Cards/Embeds | Yes | No | No | Yes (embeds) | Yes (blocks) | No | HTML |
| Dropdown menus | Yes | Yes (lists) | No | Yes (select) | Yes (select) | No | No |
| Threads | No | No | Yes (reply) | Yes | Yes | No | Yes (reply) |
| Reactions | No | Yes (limited) | Yes | Yes | Yes | No | No |
| Voice/Audio | No | Yes | Yes | Yes | Yes (Huddle) | No | No |
| Slash commands | N/A | No | Yes | Yes | Yes | No | No |
| Typing indicator | Yes | Yes | Yes | Yes | No | No | No |
| Read receipts | No | Yes | Yes | No | No | No | Varies |

---

## Rate Limits Per Channel

Rate limits affect how quickly your agent can respond and how many concurrent conversations it can handle:

- **Web UI:** No external rate limits. Limited only by your server resources.
- **Telegram:** 30 messages per second overall. 20 messages per minute to the same group. 1 message per second to the same user in a group.
- **Slack:** 1 message per second per channel. Burst of up to 20 messages. 50,000 events per hour per workspace.
- **Discord:** 50 requests per second globally. 5 messages per second per channel. Additional limits on specific endpoints.
- **WhatsApp (Twilio):** 80 messages per second per account. Template messages may have daily limits based on quality rating (starts at 250/day, scales to unlimited).
- **SMS (Twilio):** 1 message per second per phone number. Can increase with additional numbers.
- **Email:** Varies by provider. Gmail: 500/day (free), 2000/day (Workspace). Amazon SES: 50,000/day.

---

## Cost Considerations

| Channel | Setup Cost | Ongoing Cost | Notes |
|---------|-----------|--------------|-------|
| Web UI | $0 | $0 | Included with OpenClaw |
| Telegram | $0 | $0 | Completely free, no limits on messages |
| Discord | $0 | $0 | Free for bot usage |
| Slack | $0 (free tier) | $7.25/user/mo (Pro) | Free tier: 90-day message history, 10 integrations |
| WhatsApp | ~$1/mo (Twilio number) | $0.005-0.08/msg | Meta direct API is cheaper at scale but harder to set up |
| SMS | ~$1/mo (Twilio number) | $0.0079/msg outbound | Same Twilio number can do SMS + WhatsApp |
| Email | $0 (existing provider) | $0 | Uses your existing email account via IMAP/SMTP |

**Monthly cost estimate for a marketing agency (moderate use):**

- Telegram + Discord + Web UI: $0/month
- Slack Pro (5 team members): ~$36/month
- WhatsApp (500 messages/month): ~$5-10/month
- Twilio phone number: ~$1/month
- **Total: approximately $42-47/month for all channels**

---

## iMessage Integration (Read-Only)

OpenClaw can read iMessage/SMS conversations from the user's iMac via a lightweight relay service over Tailscale. This is a **read-only** integration -- the agent cannot send messages through iMessage. Replies go through Telegram or Twilio.

**Architecture:** A FastAPI service on the iMac reads `~/Library/Messages/chat.db` (SQLite) and serves message data over Tailscale to the Mac Mini.

**Use cases:**
- Surface incoming messages in proactive check-ins
- Cross-reference message senders with CRM contacts
- Provide conversation context when user asks "What did X say about Y?"

**Key constraints:**
- Requires Full Disk Access (TCC) on the iMac
- Read-only (no sending via chat.db)
- Privacy-sensitive: message content processed in memory only, not persisted

**Full documentation:**
- [chat.db Schema](imessage/chat-db-schema.md)
- [Relay Architecture](imessage/imessage-relay-architecture.md)
- [Privacy Considerations](imessage/privacy-considerations.md)

---

## Next Steps

Set up each channel by following the dedicated guides in this section:

1. [Web Interface](web-interface.md) -- Start here, no setup required
2. [Telegram Bot](telegram-bot.md) -- Quick, free, personal assistant
3. [Slack App](slack-app.md) -- Professional team channel
4. [WhatsApp Business](whatsapp-business.md) -- Client communication
5. [Discord Bot](discord-bot.md) -- Community and team alternative
6. [iMessage](imessage/) -- Read-only iMessage/SMS relay from iMac

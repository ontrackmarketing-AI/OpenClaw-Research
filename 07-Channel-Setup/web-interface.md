# Web Interface -- OpenClaw Built-in UI Guide

## Overview

The OpenClaw web interface is the primary management and interaction surface for your entire OpenClaw system. It is a built-in web application that runs alongside the OpenClaw gateway on your Mac Mini, accessible through a browser. Unlike the messaging channels (WhatsApp, Telegram, Slack, Discord), the web UI is not a communication channel for clients -- it is your command center for configuring, monitoring, testing, and managing everything.

**Access URL:** `http://localhost:3000` from the Mac Mini itself, or `https://mac-mini.tailnet-name.ts.net:3000` from any device on your Tailscale network.

The web UI requires zero external setup. It starts automatically when OpenClaw starts. This makes it the first "channel" you use and the one you will return to daily for administration.

---

## Accessing the Web Interface

### Local Access (Mac Mini)

Open a browser on the Mac Mini and navigate to:
```
http://localhost:3000
```

This is immediate and requires no configuration.

### Remote Access via Tailscale

From any device connected to your Tailscale network (laptop, phone, tablet, another computer):
```
https://mac-mini.tailnet-name.ts.net:3000
```

Replace `mac-mini.tailnet-name.ts.net` with your actual Tailscale machine name and tailnet domain. You can find this by running `tailscale status` on the Mac Mini.

### HTTPS Configuration

For production use, especially when accessing remotely, configure HTTPS:

**Option A: Tailscale HTTPS (Recommended)**

Tailscale can automatically provision TLS certificates for your machine:

```bash
# On the Mac Mini
tailscale cert mac-mini.tailnet-name.ts.net
```

This generates a valid TLS certificate trusted by all major browsers. Configure OpenClaw to use it:

```yaml
web:
  https:
    enabled: true
    cert_file: /path/to/mac-mini.tailnet-name.ts.net.crt
    key_file: /path/to/mac-mini.tailnet-name.ts.net.key
```

**Option B: Tailscale Funnel (Public Access)**

If you want to access the web UI from outside your Tailscale network (not recommended for admin UI, but possible):

```bash
tailscale funnel 443 /=http://localhost:3000
```

**Option C: Reverse Proxy (Caddy or nginx)**

If you run a reverse proxy on the Mac Mini:

```
# Caddyfile example
mac-mini.tailnet-name.ts.net {
    reverse_proxy localhost:3000
}
```

Caddy automatically handles TLS certificates.

---

## Authentication

The web interface must be protected with authentication. Do not leave it open, even on your Tailscale network.

### Basic Configuration

```yaml
web:
  enabled: true
  port: 3000
  auth:
    enabled: true
    method: password          # Options: password, oauth, tailscale
    username: admin
    password: "${WEB_UI_PASSWORD}"   # Set via environment variable
    session_timeout: 24h      # Re-login required after 24 hours
```

### Authentication Methods

**Method 1: Username/Password (Simple)**

```yaml
auth:
  method: password
  username: admin
  password: "${WEB_UI_PASSWORD}"
```

Set the password via environment variable:
```bash
export WEB_UI_PASSWORD="a-strong-random-password-here"
```

**Method 2: Tailscale Authentication (Recommended)**

If you access the UI exclusively through Tailscale, you can use Tailscale's built-in identity:

```yaml
auth:
  method: tailscale
  allowed_users:
    - "your-email@gmail.com"      # Your Tailscale identity
    - "teammate@company.com"       # Team member's Tailscale identity
```

This leverages Tailscale's existing authentication and avoids managing separate credentials.

**Method 3: OAuth (Advanced)**

For team access with SSO:

```yaml
auth:
  method: oauth
  provider: google              # or github, okta, etc.
  client_id: "${OAUTH_CLIENT_ID}"
  client_secret: "${OAUTH_CLIENT_SECRET}"
  allowed_emails:
    - "you@youragency.com"
    - "teammate@youragency.com"
```

---

## Features and Sections

### 1. Chat Interface

The chat interface is a conversational UI for interacting directly with any of your configured agents. Think of it as the most direct, unrestricted way to talk to your agents.

**What you can do:**
- Select which agent to chat with from a dropdown or sidebar.
- Send text messages, upload files, paste images.
- View rich responses (formatted text, tables, charts, lists).
- See the agent's "thinking" process if verbose mode is enabled.
- Switch between conversations (each has its own thread/session).
- Export conversation history.

**Why it matters:**
- Fastest way to test new agent configurations.
- No platform restrictions (no rate limits, no template requirements, no formatting limitations).
- Full access to all agent capabilities without channel adapter limitations.

### 2. Agent Management

This is where you create, configure, start, stop, and monitor your agents.

**Agent list view:**
- See all configured agents with their status (running, stopped, error).
- Quick actions: start, stop, restart, edit.
- Resource usage per agent (memory, active conversations).

**Agent configuration:**
- System prompt editor with syntax highlighting.
- LLM provider and model selection.
- Temperature and other generation parameters.
- Skill assignments (which skills this agent can use).
- Channel assignments (which channels this agent responds on).
- Memory configuration (short-term window, long-term retrieval settings).
- Behavior rules (rate limits, fallback responses, escalation triggers).

**Agent creation wizard:**
- Step-by-step guided setup for new agents.
- Template selection (start from pre-built agent templates).
- Test conversation before activating.

### 3. Skill Browser

Skills are the capabilities you give your agents (CRM access, email sending, calendar management, web search, etc.). The skill browser lets you manage them.

**What you can do:**
- Browse available skills (built-in and community).
- Install new skills from a registry or by URL.
- Configure skill-specific settings (API keys, endpoints, permissions).
- Test individual skills in isolation (call a skill directly, see its output).
- Enable/disable skills per agent.
- View skill documentation and usage examples.
- Monitor skill performance (latency, error rates, usage counts).

### 4. Memory Viewer

The memory viewer gives you visibility into what your agents know and remember.

**Short-term memory (conversation context):**
- View the current context window for active conversations.
- See exactly what the LLM receives as context.
- Identify when context is being truncated or summarized.

**Long-term memory (vector store / RAG):**
- Browse stored memory entries.
- Search memory by keyword, date, or source.
- Edit or delete incorrect memories.
- View memory embeddings and similarity scores.
- Force re-indexing of memory entries.
- Import/export memory data.

**Why this matters:**
- Debug why an agent "forgot" something or gave a wrong answer.
- Correct inaccurate information the agent has stored.
- Understand what the agent's knowledge base actually contains.

### 5. Session History

Review past conversations across all channels.

**What you can do:**
- Browse all past sessions, filtered by agent, channel, contact, or date.
- Read full conversation transcripts.
- See which skills were invoked during the conversation.
- View agent reasoning (if logged).
- Identify conversations that went wrong (for improvement).
- Export conversations for training data or audit purposes.
- Search across all conversations for specific topics or keywords.

### 6. Settings

Central configuration management for the entire OpenClaw system.

**Sections:**
- **General:** System name, timezone, default language.
- **LLM Providers:** Configure API keys and settings for OpenAI, Anthropic, local models, etc.
- **Channels:** Enable/disable and configure each channel (detailed in other files in this section).
- **Skills:** Global skill settings, API keys shared across skills.
- **Memory:** Vector store configuration, retention policies, embedding model.
- **Security:** Authentication, API keys, webhook secrets, encryption.
- **Integrations:** Third-party service connections (CRM, calendar, email).
- **Backups:** Backup schedule, restore points, export/import.
- **Updates:** Check for and install OpenClaw updates.

### 7. Logs

Real-time log viewer for debugging and monitoring.

**Log levels:**
- **Error:** Failures, exceptions, broken integrations.
- **Warning:** Degraded performance, approaching limits, fallback behaviors.
- **Info:** Normal operations (message received, response sent, skill invoked).
- **Debug:** Detailed internal state (LLM prompts, API payloads, timing data).

**Features:**
- Real-time streaming (logs appear as they happen).
- Filter by level, agent, channel, skill, or timestamp.
- Search within logs.
- Download log files for offline analysis.
- Log retention settings (how long to keep logs).

### 8. Dashboard

System overview and health monitoring.

**Widgets:**
- **System Status:** CPU, memory, disk usage on the Mac Mini.
- **Active Agents:** Which agents are running, their current state.
- **Conversation Metrics:** Messages today, active conversations, average response time.
- **Channel Status:** Is each channel connected and healthy?
- **Recent Activity Feed:** Last N events across all channels.
- **Error Summary:** Recent errors that need attention.
- **Resource Usage:** LLM API costs (today, this week, this month), token usage per agent.
- **Uptime:** How long the system has been running.

---

## Customization

### Theme and Appearance

```yaml
web:
  theme:
    mode: dark                # dark or light
    primary_color: "#1a73e8"  # Brand color
    font: "Inter"             # UI font
  branding:
    logo: /assets/logo.png    # Your agency logo
    title: "YourAgency AI"    # Appears in browser tab and header
    favicon: /assets/favicon.ico
```

### Layout Preferences

- **Sidebar:** Collapsible, shows agents, channels, and quick links.
- **Chat position:** Full page or side panel.
- **Dashboard layout:** Customizable widget grid (drag and drop).
- **Compact mode:** Reduce whitespace for information-dense view.

---

## Mobile Access

The web UI is responsive and works on mobile devices. When accessing via Tailscale on your phone:

1. Install the Tailscale app on your phone.
2. Log in to your Tailscale account.
3. Open your mobile browser.
4. Navigate to `https://mac-mini.tailnet-name.ts.net:3000`.
5. Log in with your credentials.

**Mobile-specific considerations:**
- Chat interface works well on small screens.
- Dashboard widgets stack vertically on mobile.
- Settings and configuration forms are usable but work better on desktop.
- File upload works from mobile (camera, gallery, files app).

**Tip:** Add the URL to your phone's home screen for quick access. On iOS, use Safari's "Add to Home Screen" feature. On Android, use Chrome's "Add to home screen." This creates an app-like shortcut.

---

## Use Cases

### 1. Primary Management Interface

The web UI is your daily control panel:
- Start each day by checking the Dashboard for system health.
- Review the Activity Feed for overnight events.
- Check Error Summary for anything that needs attention.
- Use Chat to test or interact with agents as needed.

### 2. Testing New Skills and Configurations

Before deploying changes to production channels:
- Edit agent configuration in the web UI.
- Test the new configuration via the Chat interface.
- Verify skill behavior in the Skill Browser's test mode.
- Review Memory Viewer to confirm knowledge is loaded correctly.
- Only after testing works in the web UI should you push changes to external channels.

### 3. Monitoring Agent Activity

Ongoing operational awareness:
- Dashboard shows real-time metrics.
- Session History lets you review any conversation.
- Logs provide deep debugging capability.
- Set up dashboard alerts for anomalies (high error rate, slow response time, unexpected topics).

### 4. Manual Intervention

When the agent needs human help:
- Session History shows conversations flagged for review.
- You can join a conversation and respond directly through the web UI.
- Override agent responses when needed.
- Correct agent memory when you spot inaccuracies.
- Escalation workflows route difficult conversations to the web UI for human handling.

### 5. Onboarding New Team Members

When adding someone to your agency:
- Create their account in Settings > Security.
- Walk them through the Dashboard and Chat interface.
- Let them explore agent capabilities in a safe testing environment before they interact through external channels.

---

## Performance

The web UI is designed to be lightweight:

- **Server-side resource usage:** Minimal. The web server is a thin layer on top of the OpenClaw gateway.
- **Client-side:** Modern single-page application. Works in any recent browser (Chrome, Firefox, Safari, Edge).
- **Concurrent users:** Supports multiple simultaneous users (your team can all be logged in at once).
- **No external dependencies:** The web UI does not require any external CDN, analytics, or tracking services. Everything runs locally.

**Browser requirements:**
- Chrome 90+ (recommended)
- Firefox 90+
- Safari 15+
- Edge 90+

---

## Configuration Reference

Full web interface configuration:

```yaml
web:
  enabled: true
  port: 3000
  host: "0.0.0.0"              # Listen on all interfaces (needed for Tailscale access)

  # HTTPS
  https:
    enabled: false              # Set to true for production
    cert_file: ""
    key_file: ""

  # Authentication
  auth:
    enabled: true
    method: password            # password, tailscale, or oauth
    username: admin
    password: "${WEB_UI_PASSWORD}"
    session_timeout: "24h"
    max_sessions: 5             # Max concurrent login sessions

  # Appearance
  theme:
    mode: dark
    primary_color: "#1a73e8"
  branding:
    logo: ""
    title: "OpenClaw"
    favicon: ""

  # Features
  features:
    chat: true
    agent_management: true
    skill_browser: true
    memory_viewer: true
    session_history: true
    settings: true
    logs: true
    dashboard: true

  # Performance
  performance:
    log_buffer_size: 1000       # Number of log lines to keep in memory for live view
    session_page_size: 50       # Conversations per page in history
    dashboard_refresh: 30       # Dashboard refresh interval in seconds

  # Security
  security:
    cors_origins: []            # Allowed CORS origins (empty = same-origin only)
    rate_limit: 100             # Max requests per minute per IP
    content_security_policy: true
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Cannot access from other devices | Listening on 127.0.0.1 only | Set `host: "0.0.0.0"` in config |
| Cannot access via Tailscale | Tailscale not running or port blocked | Verify `tailscale status`, check firewall allows port 3000 |
| Login not working | Wrong credentials or expired session | Check environment variable for password, clear browser cookies |
| Page loads but is blank | JavaScript error in browser | Check browser console (F12), try a different browser |
| Slow performance | Too many log entries or large session history | Reduce `log_buffer_size`, increase `dashboard_refresh` interval |
| HTTPS certificate error | Certificate expired or wrong domain | Regenerate Tailscale cert, ensure domain matches |
| Mobile layout broken | Browser zoom or old browser version | Reset zoom to 100%, update browser |
| Changes not saving | Permission issue on config file | Check file permissions on the Mac Mini |
| Dashboard not updating | WebSocket connection lost | Refresh the page, check that the OpenClaw process is running |

---

## Security Checklist

Before considering the web interface production-ready:

- [ ] Authentication is enabled (never leave it open).
- [ ] A strong, unique password is set via environment variable.
- [ ] HTTPS is configured (either via Tailscale certs or reverse proxy).
- [ ] The UI is only accessible via Tailscale (not exposed to the public internet) unless you have a specific reason.
- [ ] Session timeout is configured (24 hours recommended).
- [ ] Browser access is from trusted devices only.
- [ ] Bookmark the Tailscale HTTPS URL on your devices for quick, secure access.

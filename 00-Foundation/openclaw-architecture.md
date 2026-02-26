# OpenClaw Architecture Reference

> **Status:** Research Document | **Last Updated:** 2026-02-05
> **Applies to:** OpenClaw (formerly Clawdbot -> Moltbot -> OpenClaw)
> **Source:** github.com/pspdfkit/openclaw (145K+ stars)

---

## 1. Architectural Overview

OpenClaw is a **gateway-centric, model-agnostic AI agent platform** designed to orchestrate multiple agents, tools, channels, and memory systems through a single unified server. The architecture prioritizes extensibility, developer experience, and production-grade reliability.

### High-Level Architecture Diagram (Text)

```
                        +---------------------+
                        |    Channel Layer     |
                        | WhatsApp | Telegram  |
                        | Discord  | Slack     |
                        | Web UI   | Custom    |
                        +--------+------------+
                                 |
                          WebSocket / HTTP
                                 |
                        +--------v------------+
                        |   GATEWAY SERVER    |
                        |   (Port 18789)      |
                        |                     |
                        |  - Session Manager  |
                        |  - Agent Router     |
                        |  - Tool Dispatcher  |
                        |  - Skill Loader     |
                        |  - Memory Indexer   |
                        |  - Plugin Host      |
                        +----+----+----+------+
                             |    |    |
              +--------------+    |    +---------------+
              |                   |                    |
     +--------v------+   +-------v--------+   +-------v--------+
     |  Agent Pool   |   |  Tool Registry |   |  Memory Store  |
     |               |   |                |   |                |
     | - Agent Defs  |   | - MCP Servers  |   | - MEMORY.md    |
     | - Templates   |   | - Adapters     |   | - Daily Logs   |
     | - Runtimes    |   | - Permissions  |   | - SQLite/FTS5  |
     +---------------+   +----------------+   | - Vector Index |
                                              +----------------+
```

---

## 2. Gateway Server Architecture

The Gateway is the **central nervous system** of OpenClaw. Every message, tool call, agent invocation, and memory operation flows through it.

### 2.1 WebSocket Server (Port 18789)

- **Default port:** `18789` (configurable via `OPENCLAW_PORT` env var or `gateway.port` in config)
- **Protocol:** WebSocket with JSON-RPC 2.0 message framing
- **Connection types:**
  - **Channel connections:** Inbound from channel adapters (WhatsApp, Slack, etc.)
  - **Agent connections:** Internal connections from running agent processes
  - **Tool connections:** MCP server connections for tool availability
  - **Client connections:** Web UI, CLI, and third-party integrations
- **Connection lifecycle:**
  1. Client connects via `ws://localhost:18789/ws`
  2. Authentication handshake (API key or token)
  3. Session initialization or resumption
  4. Bidirectional message streaming
  5. Graceful disconnect with session persistence

### 2.2 HTTP API Layer

Alongside WebSocket, the Gateway exposes a REST API:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/agents` | GET/POST | List and create agents |
| `/api/v1/sessions` | GET/POST | Manage sessions |
| `/api/v1/channels` | GET/POST/DELETE | Channel configuration |
| `/api/v1/tools` | GET | List available tools |
| `/api/v1/skills` | GET/POST | Skill management |
| `/api/v1/memory/search` | POST | Hybrid memory search |
| `/api/v1/health` | GET | Server health check |
| `/api/v1/config` | GET/PUT | Runtime configuration |

### 2.3 Internal Message Bus

The Gateway uses an **internal pub/sub message bus** for inter-component communication:

- **Topics:** `agent.*`, `session.*`, `channel.*`, `tool.*`, `memory.*`, `system.*`
- **Pattern:** Observer pattern with typed event handlers
- **Backpressure:** Built-in queue limits per subscriber with configurable overflow strategies (drop-oldest, block, error)

---

## 3. Agent System

### 3.1 Agent Definition

Agents are defined as YAML or JSON configuration files:

```yaml
# agents/research-assistant.yaml
name: research-assistant
version: "1.0.0"
description: "Deep research agent with web access"

model:
  provider: anthropic         # or openai, ollama, custom
  model: claude-sonnet-4-20250514
  temperature: 0.3
  max_tokens: 8192

system_prompt: |
  You are a research assistant specializing in...

skills:
  - web-search
  - document-analysis
  - citation-manager

tools:
  - mcp://filesystem
  - mcp://web-browser
  - custom://internal-wiki

memory:
  enabled: true
  scope: per-session          # per-session | per-agent | global
  search_strategy: hybrid     # vector | fts5 | hybrid

permissions:
  internet_access: true
  file_write: false
  execute_code: false

channels:
  - slack:#research
  - web-ui
```

### 3.2 Agent Lifecycle

1. **Registration:** Agent config loaded into Gateway's Agent Registry
2. **Instantiation:** On first message, Gateway spawns agent runtime with allocated resources
3. **Warm state:** Agent maintains conversation context and loaded skills
4. **Idle timeout:** After configurable inactivity (default 15 min), agent suspends to disk
5. **Resumption:** On next message, agent restores from persisted state
6. **Termination:** Manual shutdown or resource limits exceeded

### 3.3 Agent Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Interactive** | Responds to user messages, waits for input | Chat assistants, support bots |
| **Autonomous** | Runs on schedule or trigger, acts independently | Monitoring, data pipelines, scheduled reports |
| **Collaborative** | Multiple agents working together via message passing | Complex workflows, review chains |
| **Supervisor** | Oversees other agents, routes tasks, handles escalation | Multi-agent orchestration |

### 3.4 Agent Templates

OpenClaw ships with built-in templates and supports custom templates:

- `openclaw template list` -- show available templates
- `openclaw template create --from=research-assistant my-agent` -- scaffold from template
- Templates are stored in `~/.openclaw/templates/` or project-local `.openclaw/templates/`

---

## 4. Session Management

### 4.1 Session Architecture

Sessions are the **contextual container** for a conversation between a user and one or more agents.

```
Session
  +-- session_id (UUID)
  +-- created_at (timestamp)
  +-- last_active (timestamp)
  +-- channel_id (which channel started this)
  +-- agent_id (primary agent assigned)
  +-- user_id (authenticated user)
  +-- context_window[]
  |     +-- message_id
  |     +-- role (user | assistant | system | tool)
  |     +-- content
  |     +-- timestamp
  |     +-- metadata{}
  +-- state{}
  |     +-- key-value pairs for session variables
  +-- memory_scope
  +-- tools_active[]
```

### 4.2 Context Management

- **Sliding window:** Configurable context window size (default: last 50 messages or 100K tokens)
- **Summarization:** When context exceeds limits, older messages are summarized by a background agent
- **Pinned messages:** Critical context can be pinned so it is never summarized away
- **Cross-session memory:** Via the Memory system (see core-concepts.md), sessions can access long-term knowledge

### 4.3 Session Persistence

Sessions are persisted to:
1. **In-memory cache** (hot sessions, sub-millisecond access)
2. **SQLite database** (`~/.openclaw/data/sessions.db`) for durability
3. **Optional:** External database (Postgres, Redis) for multi-instance deployments

### 4.4 Session Commands

```bash
openclaw session list                     # List active sessions
openclaw session inspect <session-id>     # View session details
openclaw session export <session-id>      # Export session as JSON
openclaw session resume <session-id>      # Re-attach to a session
openclaw session delete <session-id>      # Delete session and data
```

---

## 5. Channel System

### 5.1 Channel Abstraction Layer

Channels are **adapters** that normalize messages from external platforms into OpenClaw's internal message format. This allows agents to be written once and deployed to any channel.

```
External Platform          Channel Adapter          Internal Format
+-----------+           +----------------+        +---------------+
| WhatsApp  | --------> | WhatsApp       | -----> |               |
| API       |           | Adapter        |        |  OpenClaw     |
+-----------+           +----------------+        |  Message      |
                                                  |  {            |
+-----------+           +----------------+        |    type,      |
| Telegram  | --------> | Telegram       | -----> |    content,   |
| Bot API   |           | Adapter        |        |    sender,    |
+-----------+           +----------------+        |    channel,   |
                                                  |    metadata,  |
+-----------+           +----------------+        |    timestamp  |
| Discord   | --------> | Discord        | -----> |  }            |
| Bot       |           | Adapter        |        |               |
+-----------+           +----------------+        +---------------+
```

### 5.2 Supported Channels

| Channel | Status | Features | Config Key |
|---------|--------|----------|------------|
| **Web UI** | Built-in | Full featured, rich media, streaming | `channels.web` |
| **Slack** | Official | Threads, reactions, file upload, slash commands | `channels.slack` |
| **Discord** | Official | Threads, reactions, voice (beta), slash commands | `channels.discord` |
| **Telegram** | Official | Groups, inline queries, file sharing | `channels.telegram` |
| **WhatsApp** | Official | Business API, media messages, templates | `channels.whatsapp` |
| **CLI** | Built-in | Terminal-based interaction | `channels.cli` |
| **API** | Built-in | Raw HTTP/WebSocket for custom integrations | `channels.api` |
| **Custom** | Plugin | Build your own channel adapter | `channels.custom.*` |

### 5.3 Channel Configuration Example

```yaml
# openclaw.config.yaml - channels section
channels:
  slack:
    enabled: true
    bot_token: "${SLACK_BOT_TOKEN}"
    app_token: "${SLACK_APP_TOKEN}"
    default_agent: general-assistant
    channel_routing:
      "#engineering": code-reviewer
      "#support": support-agent
      "DM": personal-assistant

  discord:
    enabled: true
    bot_token: "${DISCORD_BOT_TOKEN}"
    guild_id: "123456789"
    default_agent: general-assistant

  web:
    enabled: true
    port: 3000
    cors_origins: ["https://mysite.com"]
    auth: api-key
```

### 5.4 Multi-Channel Conversations

A single session can span multiple channels. For example, a user starts a conversation on Slack and continues it on the web UI. The Gateway maintains session continuity through user identity mapping.

---

## 6. Tool System

### 6.1 MCP Protocol Integration

OpenClaw is a **first-class MCP (Model Context Protocol) client and server**. Tools are connected via MCP for standardized communication.

```
+-------------------+       MCP (stdio/SSE)       +------------------+
|   OpenClaw        | <-------------------------> |  MCP Server      |
|   Gateway         |       JSON-RPC 2.0          |  (filesystem,    |
|   (MCP Client)    |                             |   browser, etc.) |
+-------------------+                             +------------------+
```

### 6.2 Tool Registration

Tools can be registered in three ways:

1. **MCP servers** (recommended):
   ```yaml
   tools:
     filesystem:
       type: mcp
       command: "npx @modelcontextprotocol/server-filesystem"
       args: ["/allowed/path"]

     browser:
       type: mcp
       url: "http://localhost:3001/sse"
   ```

2. **Custom adapters** (for non-MCP tools):
   ```yaml
   tools:
     internal-api:
       type: custom
       adapter: "./adapters/internal-api.js"
       config:
         base_url: "https://api.internal.com"
   ```

3. **Inline tools** (simple function definitions):
   ```yaml
   tools:
     calculator:
       type: inline
       handler: |
         function calculate(expression) {
           return eval(expression);
         }
   ```

### 6.3 Tool Permissions

Every tool has a permission model:

```yaml
tool_permissions:
  filesystem:
    read: true
    write: false
    allowed_paths: ["/home/user/documents"]
    denied_paths: ["/etc", "/root"]

  web-browser:
    allowed_domains: ["*.example.com"]
    require_confirmation: true    # User must approve each use

  code-execution:
    enabled: false                # Globally disabled
```

### 6.4 Tool Chains

Tools can be chained together in predefined sequences:

```yaml
tool_chains:
  research-and-summarize:
    steps:
      - tool: web-search
        output: search_results
      - tool: web-browser
        input: "{{ search_results[0].url }}"
        output: page_content
      - tool: summarizer
        input: "{{ page_content }}"
        output: summary
```

---

## 7. Skill System

### 7.1 AgentSkills Standard

Skills are **packaged, reusable capabilities** that agents can load. They bundle prompts, tools, and logic into a single installable unit.

```
skill/
  +-- skill.yaml          # Skill manifest (name, version, dependencies)
  +-- prompts/
  |     +-- system.md     # System prompt additions
  |     +-- examples.md   # Few-shot examples
  +-- tools/
  |     +-- custom-tool.js  # Custom tool implementations
  +-- config/
  |     +-- defaults.yaml   # Default configuration
  +-- README.md
```

### 7.2 Skill Manifest (skill.yaml)

```yaml
name: code-reviewer
version: "2.1.0"
description: "Automated code review with style checking"
author: "openclaw-community"
license: MIT

requires:
  openclaw: ">=1.5.0"
  tools:
    - mcp://filesystem
    - mcp://git

provides:
  tools:
    - review-code
    - check-style
    - suggest-fix

config:
  language: auto-detect
  severity_threshold: warning
  max_file_size: 100000
```

### 7.3 ClawHub (Skill Marketplace)

- **URL:** https://clawhub.io
- **CLI:** `openclaw skill search <query>` / `openclaw skill install <name>`
- **Publishing:** `openclaw skill publish` (requires ClawHub account)
- **Categories:** Coding, Research, Writing, Data, DevOps, Marketing, Custom
- **Quality tiers:** Community, Verified, Official
- **As of early 2026:** 2,800+ published skills

---

## 8. Plugin Architecture

### 8.1 Plugin Types

| Plugin Type | Purpose | Hook Points |
|-------------|---------|-------------|
| **Channel Plugin** | Add new communication channels | Message ingress/egress |
| **Tool Plugin** | Add new tool capabilities | Tool registry |
| **Memory Plugin** | Custom memory backends | Memory read/write/search |
| **Auth Plugin** | Custom authentication | Connection handshake |
| **Middleware Plugin** | Transform messages in transit | Message pipeline |
| **UI Plugin** | Extend the web interface | Web UI rendering |

### 8.2 Plugin Lifecycle

```
Install -> Register -> Initialize -> Active -> Suspend -> Uninstall
             |                          |
             +--- Config validation     +--- Hot-reload supported
```

### 8.3 Plugin Development

```javascript
// plugins/my-plugin/index.js
export default class MyPlugin {
  static meta = {
    name: 'my-plugin',
    version: '1.0.0',
    type: 'middleware',
    hooks: ['message:before', 'message:after']
  };

  async onMessageBefore(message, context) {
    // Transform message before agent sees it
    message.content = message.content.trim();
    return message;
  }

  async onMessageAfter(response, context) {
    // Transform response before sending to channel
    return response;
  }
}
```

---

## 9. Data Flow: End-to-End Message Processing

### 9.1 Inbound Message Flow

```
1. User sends message on Slack
     |
2. Slack Channel Adapter receives webhook
     |
3. Adapter normalizes to OpenClaw Message format
     |
4. Gateway receives message on internal bus
     |
5. Session Manager:
     +-- Find or create session
     +-- Load context window
     +-- Attach memory context (hybrid search)
     |
6. Agent Router:
     +-- Determine target agent (from channel config or session)
     +-- Check agent availability
     +-- Queue if agent is busy
     |
7. Agent Runtime:
     +-- Load system prompt + skill prompts
     +-- Inject context window + memory results
     +-- Send to LLM provider
     |
8. LLM Response:
     +-- If tool call: dispatch to Tool Dispatcher
     |     +-- Execute tool via MCP or adapter
     |     +-- Return result to Agent Runtime
     |     +-- Loop back to step 7 (agent continues)
     +-- If final response: continue to step 9
     |
9. Response Processing:
     +-- Update session context
     +-- Index in memory system
     +-- Transform for target channel
     |
10. Slack Channel Adapter sends response back to user
```

### 9.2 Autonomous Agent Flow

```
1. Cron trigger or event fires
     |
2. Gateway creates internal session (no user)
     |
3. Agent executes predefined task
     |
4. Results sent to configured output:
     +-- Channel message (e.g., daily report to #general)
     +-- File write
     +-- API call
     +-- Another agent (chaining)
```

---

## 10. Key Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `openclaw.config.yaml` | Project root or `~/.openclaw/` | Main configuration: gateway, channels, defaults |
| `agents/*.yaml` | `~/.openclaw/agents/` or project `.openclaw/agents/` | Agent definitions |
| `skills/*/skill.yaml` | `~/.openclaw/skills/` | Installed skill manifests |
| `plugins/*/plugin.yaml` | `~/.openclaw/plugins/` | Plugin configurations |
| `.env` or `openclaw.env` | Project root | Secret keys, API tokens, environment-specific config |
| `tool-permissions.yaml` | Project root or `~/.openclaw/` | Tool access control rules |
| `memory.config.yaml` | `~/.openclaw/` | Memory system settings (vector model, chunk size, etc.) |
| `sessions.db` | `~/.openclaw/data/` | SQLite database for session persistence |
| `memory.db` | `~/.openclaw/data/` | SQLite database for memory index (FTS5 + vector) |

### 10.1 Minimal Configuration Example

```yaml
# openclaw.config.yaml
gateway:
  port: 18789
  host: "0.0.0.0"
  log_level: info

defaults:
  model:
    provider: anthropic
    model: claude-sonnet-4-20250514
  memory:
    enabled: true
    search_strategy: hybrid

channels:
  web:
    enabled: true
    port: 3000
  cli:
    enabled: true

tools:
  filesystem:
    type: mcp
    command: "npx @modelcontextprotocol/server-filesystem"
    args: ["./workspace"]
```

---

## 11. Deployment Topology

### 11.1 Single Machine (Development)

```
[Gateway + Agents + Tools + Memory] -- all in one process
```

### 11.2 Production (Multi-Instance)

```
                    Load Balancer
                         |
          +--------------+--------------+
          |              |              |
     Gateway #1     Gateway #2     Gateway #3
          |              |              |
          +--------------+--------------+
                         |
                  Shared Storage
              (Postgres + Redis + S3)
```

### 11.3 Resource Requirements

| Component | Min RAM | Recommended RAM | CPU | Storage |
|-----------|---------|-----------------|-----|---------|
| Gateway | 256MB | 1GB | 1 core | 100MB |
| Per Agent (idle) | 50MB | 128MB | - | - |
| Per Agent (active) | 128MB | 512MB | 0.5 core | - |
| Memory DB (SQLite) | 64MB | 256MB | - | Varies |
| Memory DB (Vector) | 512MB | 2GB | 1 core | Varies |

---

## 12. Security Model

- **API key authentication** for all connections
- **Role-based access control (RBAC)** for agents, tools, and channels
- **Tool sandboxing** via permission manifests
- **Secrets management** via environment variables or external vaults (HashiCorp Vault, AWS Secrets Manager supported via plugins)
- **Audit logging** of all tool executions and agent actions
- **Rate limiting** per user, per channel, per agent

---

## Next Steps

- See `core-concepts.md` for detailed explanations of each subsystem
- See `version-history.md` for release timeline and breaking changes
- See `vs-existing-tools.md` for comparison with Ralph, Claude Code, N8N, etc.

# OpenClaw Core Concepts

> **Status:** Research Document | **Last Updated:** 2026-02-05
> **Applies to:** OpenClaw platform (all versions)
> **Prerequisite:** Read `openclaw-architecture.md` first for structural context

---

## 1. Skills

### 1.1 What Is a Skill?

A **Skill** is OpenClaw's fundamental unit of reusable agent capability. Unlike a raw tool (which provides a single function), a skill packages together:

- **Prompts:** System prompt additions, few-shot examples, and instructions that shape how the agent uses the skill
- **Tools:** Zero or more tool definitions specific to the skill
- **Configuration:** Default settings, user-overridable parameters
- **Dependencies:** Other skills or tools required

Think of a skill as the difference between handing someone a hammer (a tool) versus teaching them carpentry (a skill). The skill includes the knowledge of *when* and *how* to use the tools.

### 1.2 Skill Lifecycle

```
1. DISCOVERY
   +-- Browse ClawHub (clawhub.io)
   +-- `openclaw skill search "code review"`
   +-- Community recommendations

2. INSTALLATION
   +-- `openclaw skill install code-reviewer`
   +-- Dependencies auto-resolved
   +-- Config defaults applied
   +-- Installed to ~/.openclaw/skills/code-reviewer/

3. CONFIGURATION
   +-- Edit skill config: `openclaw skill config code-reviewer`
   +-- Override defaults per-agent in agent YAML
   +-- Environment-specific settings via .env

4. ATTACHMENT
   +-- Add skill name to agent's `skills:` list
   +-- Skill prompts injected into agent's system prompt
   +-- Skill tools registered in agent's tool set

5. RUNTIME
   +-- Agent receives message
   +-- Skill prompts guide agent behavior
   +-- Agent calls skill-provided tools as needed
   +-- Skill may maintain internal state per-session

6. UPDATE
   +-- `openclaw skill update code-reviewer`
   +-- Semantic versioning respected
   +-- Breaking changes flagged with migration guides

7. REMOVAL
   +-- `openclaw skill uninstall code-reviewer`
   +-- Cleanup of config, cached data
   +-- Agent configs referencing it will warn on next load
```

### 1.3 Skill Categories

| Category | Examples | Description |
|----------|----------|-------------|
| **Coding** | code-reviewer, test-writer, refactorer | Software development capabilities |
| **Research** | web-researcher, paper-analyzer, fact-checker | Information gathering and analysis |
| **Writing** | blog-writer, email-composer, translator | Content creation |
| **Data** | csv-analyzer, sql-query, chart-generator | Data processing and visualization |
| **DevOps** | deploy-manager, log-analyzer, incident-responder | Infrastructure management |
| **Marketing** | seo-optimizer, social-scheduler, analytics-reporter | Marketing automation |
| **Custom** | User-built skills for specific workflows | Domain-specific capabilities |

### 1.4 Writing a Custom Skill

```yaml
# skill.yaml
name: my-custom-skill
version: "1.0.0"
description: "Does something specific for my workflow"

requires:
  openclaw: ">=1.5.0"

provides:
  tools:
    - my-custom-tool

config:
  api_endpoint:
    type: string
    required: true
    description: "API endpoint for the service"
  max_retries:
    type: number
    default: 3
```

```markdown
<!-- prompts/system.md -->
## Custom Skill Instructions

When the user asks you to [specific task], follow these steps:
1. First, use the `my-custom-tool` to [action]
2. Analyze the results looking for [criteria]
3. Present findings in [format]

Always [important behavioral rule].
Never [safety constraint].
```

---

## 2. Memory

### 2.1 File-First Philosophy

OpenClaw's memory system follows a **file-first** approach. This means:

- **Human-readable by default:** All memory is stored as Markdown files that you can read, edit, and version-control with standard tools
- **No vendor lock-in:** Your data is never trapped in a proprietary database format
- **Git-compatible:** Memory files can be committed to version control for history and collaboration
- **AI and human accessible:** Both agents and humans can read and write the same files

### 2.2 Memory Architecture

```
Memory System
  |
  +-- File Layer (Primary Source of Truth)
  |     +-- MEMORY.md              Global persistent memory
  |     +-- daily/
  |     |     +-- 2026-02-05.md    Daily interaction logs
  |     |     +-- 2026-02-04.md
  |     +-- topics/
  |     |     +-- project-alpha.md Topic-specific memory
  |     |     +-- user-preferences.md
  |     +-- sessions/
  |           +-- <session-id>.md  Session transcripts
  |
  +-- Index Layer (Derived, Rebuildable)
  |     +-- memory.db (SQLite)
  |           +-- FTS5 full-text index
  |           +-- Vector embeddings table
  |           +-- Metadata table (timestamps, tags, links)
  |
  +-- Cache Layer (Ephemeral)
        +-- Recent query results
        +-- Hot memory fragments
        +-- Embedding cache
```

### 2.3 MEMORY.md Structure

The root `MEMORY.md` file serves as the agent's long-term knowledge base:

```markdown
# Agent Memory

## User Preferences
- Prefers concise responses
- Uses TypeScript for all new projects
- Timezone: US Eastern

## Project Context
- Currently working on: OpenClaw integration
- Tech stack: Next.js, Supabase, n8n
- Deployment target: Vercel + Railway

## Key Decisions
- 2026-01-15: Chose Supabase over Firebase for auth
- 2026-01-20: Adopted monorepo structure with Turborepo

## Learned Patterns
- User always wants code examples with explanations
- When asked about architecture, include diagrams
```

### 2.4 Hybrid Search (Vector + FTS5)

OpenClaw uses **hybrid search** combining two complementary approaches:

| Aspect | Vector Search | FTS5 Full-Text Search |
|--------|--------------|----------------------|
| **Strength** | Semantic similarity ("things that mean the same") | Exact keyword matching ("find this specific term") |
| **Weakness** | May miss exact terms | Misses semantic relationships |
| **Speed** | Slower (embedding + ANN) | Very fast (SQLite native) |
| **Storage** | Large (embeddings per chunk) | Compact (inverted index) |
| **Best for** | "What do I know about deployment?" | "Find all mentions of Supabase" |

**Hybrid search process:**

```
User query: "How did we configure the database?"
     |
     +-- Vector search: finds semantically related chunks
     |   (e.g., "Chose Supabase", "database schema design", "migration strategy")
     |
     +-- FTS5 search: finds exact keyword matches
     |   (e.g., "database connection string in .env", "database backup script")
     |
     +-- Reciprocal Rank Fusion (RRF): merges and re-ranks results
     |
     +-- Top-K results returned to agent as context
```

### 2.5 Memory Configuration

```yaml
# memory.config.yaml
memory:
  enabled: true

  file_store:
    root: "~/.openclaw/memory"     # Where files are stored
    daily_logs: true                # Auto-create daily logs
    max_file_size: 100KB            # Split large files

  index:
    database: "~/.openclaw/data/memory.db"
    fts5:
      enabled: true
      tokenizer: "porter unicode61"  # Stemming + unicode support
    vector:
      enabled: true
      model: "text-embedding-3-small"  # OpenAI embedding model
      dimensions: 1536
      chunk_size: 512                 # Tokens per chunk
      chunk_overlap: 64               # Overlap between chunks

  search:
    strategy: hybrid                  # vector | fts5 | hybrid
    top_k: 10                         # Results to return
    rrf_k: 60                         # RRF constant
    min_relevance: 0.3                # Minimum score threshold

  auto_index:
    enabled: true
    watch_paths: ["~/.openclaw/memory/**/*.md"]
    reindex_interval: 300             # Seconds between reindex sweeps
```

### 2.6 Memory Operations

```bash
# CLI commands
openclaw memory search "database configuration"     # Search memory
openclaw memory add "User prefers dark mode"         # Add to MEMORY.md
openclaw memory reindex                              # Rebuild all indexes
openclaw memory stats                                # Show memory statistics
openclaw memory export --format=json                 # Export for backup
```

**Programmatic access (from skills/plugins):**

```javascript
// Inside a skill or plugin
const results = await context.memory.search("database configuration", {
  strategy: "hybrid",
  topK: 5,
  scope: "global"  // or "session", "agent"
});

await context.memory.remember("The user's database is hosted on Supabase", {
  tags: ["infrastructure", "database"],
  importance: "high"
});
```

---

## 3. Channels

### 3.1 Abstraction Layer

The Channel system provides a **unified interface** so that agents never need to know which platform a user is communicating from. The abstraction normalizes:

- **Message format:** Text, images, files, reactions, threads -- all mapped to a common schema
- **User identity:** Cross-platform user resolution (same person on Slack and Discord)
- **Capabilities:** Rich features gracefully degrade (e.g., Slack blocks become plain text on Telegram)
- **Rate limits:** Per-platform rate limiting handled at the adapter level

### 3.2 Message Routing

```
Incoming message
     |
     v
Channel Adapter (normalize)
     |
     v
Gateway Router
     |
     +-- Check channel_routing config (channel -> agent mapping)
     |
     +-- Check session state (existing session with assigned agent?)
     |
     +-- Check user preferences (preferred agent for this user?)
     |
     +-- Fallback to default_agent
     |
     v
Target Agent
```

**Routing priority (highest to lowest):**

1. Explicit session assignment (user already in conversation with specific agent)
2. Channel routing rules (`#engineering` -> `code-reviewer`)
3. User-level agent preference
4. Channel default agent
5. Global default agent

### 3.3 Multi-Channel Conversations

A single conversation can span platforms through **user identity linking:**

```yaml
# User identity mapping
users:
  john-doe:
    slack: "U12345678"
    discord: "john#1234"
    telegram: "@johndoe"
    email: "john@example.com"
```

When John sends a message on Slack and then switches to Discord, OpenClaw recognizes the same user and continues the same session (if configured to do so).

### 3.4 Channel Events

Channels emit standardized events:

| Event | Description | Example |
|-------|-------------|---------|
| `message:received` | New message from user | Text, image, file |
| `message:edited` | User edited a message | Updated content |
| `message:deleted` | User deleted a message | Message ID |
| `reaction:added` | User reacted to a message | Emoji, message ID |
| `thread:started` | New thread created | Parent message ID |
| `user:joined` | User joined channel/group | User info |
| `user:left` | User left channel/group | User info |
| `typing:started` | User started typing | Channel, user |

---

## 4. Agents

### 4.1 Autonomous vs. Interactive Agents

**Interactive Agents:**
- Wait for user input before acting
- Maintain conversation context
- Typical use: chat assistants, support bots, pair programming
- Session lifecycle tied to user interaction

**Autonomous Agents:**
- Run on triggers (cron, webhook, event)
- No user interaction during execution
- Typical use: monitoring, scheduled reports, data pipelines
- Session lifecycle tied to task completion

**Hybrid Agents:**
- Start autonomously but can request human input
- Escalation to human when confidence is low
- Typical use: approval workflows, supervised automation

### 4.2 Agent Templates

Templates are **pre-configured agent blueprints** for common use cases:

| Template | Description | Included Skills |
|----------|-------------|-----------------|
| `general-assistant` | All-purpose chat assistant | web-search, calculator, file-reader |
| `code-reviewer` | Automated code review | code-review, git-integration, style-checker |
| `research-assistant` | Deep web research | web-research, citation-manager, summarizer |
| `support-agent` | Customer support automation | knowledge-base, ticket-manager, escalation |
| `data-analyst` | Data analysis and visualization | csv-analyzer, sql-query, chart-generator |
| `devops-engineer` | Infrastructure management | deploy-manager, log-analyzer, alert-handler |

### 4.3 Agent Communication (Multi-Agent)

Agents can communicate with each other via the Gateway's message bus:

```yaml
# Agent A delegates to Agent B
agent_communication:
  enabled: true
  allowed_targets:
    - code-reviewer        # Can ask code-reviewer for reviews
    - data-analyst         # Can ask data-analyst for analysis
  max_delegation_depth: 3  # Prevent infinite loops
```

```
User -> Agent A: "Review the latest PR and analyze its performance impact"
         |
         +-- Agent A -> Agent B (code-reviewer): "Review PR #42"
         |                  |
         |                  +-- Returns: review results
         |
         +-- Agent A -> Agent C (data-analyst): "Analyze perf data for PR #42"
         |                  |
         |                  +-- Returns: performance analysis
         |
         +-- Agent A combines results and responds to User
```

---

## 5. Tools

### 5.1 MCP Integration

OpenClaw implements the **Model Context Protocol (MCP)** as its primary tool interface. This means:

- Any MCP-compatible server works as an OpenClaw tool out of the box
- OpenClaw itself can act as an MCP server, exposing its capabilities to other MCP clients
- Tool discovery, schema negotiation, and invocation follow the MCP standard

**Supported MCP transports:**
- **stdio:** Local process communication (most common for local tools)
- **SSE (Server-Sent Events):** HTTP-based, for remote or shared tool servers
- **WebSocket:** For persistent, bidirectional tool connections

### 5.2 Tool Permissions Model

Permissions are defined at three levels:

```
Global Permissions (tool-permissions.yaml)
  |
  +-- Agent-Level Overrides (agent config)
  |     |
  |     +-- Session-Level Overrides (runtime, user-granted)
```

**Permission types:**

| Permission | Description | Default |
|------------|-------------|---------|
| `enabled` | Whether the tool is available at all | true |
| `require_confirmation` | User must approve each invocation | false |
| `rate_limit` | Max invocations per minute | unlimited |
| `allowed_args` | Whitelist of allowed argument patterns | all |
| `denied_args` | Blacklist of denied argument patterns | none |
| `timeout` | Max execution time per invocation | 30s |
| `sandbox` | Run in isolated environment | false |

### 5.3 Tool Chains

Tool chains define **predetermined sequences of tool calls** that can be triggered as a single action:

```yaml
tool_chains:
  deploy-pipeline:
    description: "Full deployment pipeline"
    steps:
      - name: "Run tests"
        tool: code-executor
        args:
          command: "npm test"
        on_failure: abort

      - name: "Build"
        tool: code-executor
        args:
          command: "npm run build"
        on_failure: abort

      - name: "Deploy to staging"
        tool: deploy-manager
        args:
          target: staging
        on_failure: rollback

      - name: "Run smoke tests"
        tool: code-executor
        args:
          command: "npm run test:smoke"
        on_failure: rollback

      - name: "Deploy to production"
        tool: deploy-manager
        args:
          target: production
        require_confirmation: true
```

### 5.4 Built-in Tools

OpenClaw ships with several built-in tools that do not require MCP servers:

| Tool | Description |
|------|-------------|
| `memory-search` | Search the memory system |
| `memory-write` | Write to memory |
| `agent-delegate` | Delegate task to another agent |
| `session-state` | Read/write session variables |
| `channel-send` | Send message to a specific channel |
| `schedule-task` | Schedule a future task |
| `http-request` | Make HTTP requests (with permission controls) |

---

## 6. Sessions

### 6.1 Context Management

Sessions manage the **conversational context** between a user and an agent. Context includes:

- **Message history:** The actual conversation messages
- **System context:** Agent instructions, skill prompts, tool schemas
- **Memory context:** Retrieved memory fragments relevant to the current conversation
- **State variables:** Key-value pairs for tracking session state (e.g., current step in a workflow)
- **Active tools:** Which tools are currently available in this session

### 6.2 Context Window Strategy

OpenClaw uses a **tiered context management** approach:

```
Tier 1: Always Present (pinned)
  +-- System prompt
  +-- Active skill instructions
  +-- Pinned messages / key context

Tier 2: Recent (sliding window)
  +-- Last N messages (configurable, default 50)
  +-- Recent tool results

Tier 3: Summarized (compressed)
  +-- Older messages, summarized by background agent
  +-- Summary updated incrementally as new messages push old ones out

Tier 4: Searchable (on-demand)
  +-- Full session history (in memory DB)
  +-- Retrievable via memory search when needed
```

### 6.3 Session Persistence

Sessions are automatically persisted and can survive:

- **Gateway restart:** Sessions reload from SQLite
- **Network disconnection:** Client reconnects and resumes
- **Agent crash:** Session state preserved, agent restarts with same context
- **Machine reboot:** Full session recovery from disk

### 6.4 Session Forking

Sessions can be **forked** to explore different conversation branches:

```bash
openclaw session fork <session-id>           # Creates a copy of the session
openclaw session fork <session-id> --at=15   # Fork from message #15
```

This is useful for:
- Testing different approaches to a problem
- "What if" scenarios
- Reverting to an earlier point in a conversation

---

## 7. Gateway

### 7.1 Central Orchestrator Role

The Gateway is responsible for:

1. **Connection management:** Accepting and maintaining WebSocket connections from all components
2. **Message routing:** Directing messages between channels, agents, and tools
3. **Session lifecycle:** Creating, maintaining, persisting, and destroying sessions
4. **Agent scheduling:** Managing agent pool, spawning, suspending, and resuming agents
5. **Tool dispatch:** Routing tool calls to the correct MCP server or adapter
6. **Memory coordination:** Triggering memory indexing and search operations
7. **Plugin hosting:** Loading and managing plugin lifecycle
8. **Configuration management:** Runtime config updates without restart
9. **Health monitoring:** Tracking component health, auto-restart on failure
10. **Metrics and logging:** Centralized observability

### 7.2 Gateway Configuration

```yaml
gateway:
  port: 18789
  host: "0.0.0.0"
  log_level: info              # debug | info | warn | error

  performance:
    max_connections: 1000
    message_queue_size: 10000
    worker_threads: 4

  security:
    api_key_required: true
    cors_origins: ["*"]
    rate_limit:
      global: 1000/min
      per_user: 100/min

  persistence:
    database: "~/.openclaw/data/gateway.db"
    backup_interval: 3600      # Seconds

  health:
    check_interval: 30         # Seconds
    auto_restart: true
    max_restart_attempts: 3
```

---

## 8. Glossary of OpenClaw Terms

| Term | Definition |
|------|-----------|
| **Agent** | An AI entity configured with a model, skills, tools, and permissions. The core execution unit. |
| **AgentSkills** | The standard format for packaging reusable agent capabilities. |
| **Channel** | An adapter that connects an external platform (Slack, Discord, etc.) to the Gateway. |
| **Channel Adapter** | The code module that translates between a platform's API and OpenClaw's internal message format. |
| **ClawHub** | The official marketplace for discovering, sharing, and installing skills. |
| **Context Window** | The set of messages and context currently visible to an agent in a conversation. |
| **Gateway** | The central WebSocket server that orchestrates all OpenClaw components. |
| **Hybrid Search** | The combined vector + FTS5 search strategy used by the memory system. |
| **MCP (Model Context Protocol)** | The standardized protocol for tool communication, originally created by Anthropic. |
| **Memory** | The persistent knowledge system that stores and retrieves information across sessions. |
| **MEMORY.md** | The root Markdown file serving as the primary long-term memory store. |
| **Plugin** | An extension module that adds capabilities to the Gateway (channels, tools, auth, etc.). |
| **RRF (Reciprocal Rank Fusion)** | The algorithm used to merge results from vector and FTS5 search. |
| **Session** | A conversational context container linking a user, agent, channel, and message history. |
| **Skill** | A packaged, reusable bundle of prompts, tools, and config that gives an agent a specific capability. |
| **Skill Manifest** | The `skill.yaml` file that defines a skill's metadata, dependencies, and configuration. |
| **Tool** | A function that an agent can invoke to interact with external systems. |
| **Tool Chain** | A predefined sequence of tool invocations executed as a single workflow. |
| **Tool Permission** | Access control rules governing which tools an agent can use and how. |

---

## Next Steps

- **Architecture details:** `openclaw-architecture.md` for system structure and config files
- **Version history:** `version-history.md` for release timeline
- **Comparison:** `vs-existing-tools.md` for how OpenClaw relates to Ralph, Claude Code, N8N

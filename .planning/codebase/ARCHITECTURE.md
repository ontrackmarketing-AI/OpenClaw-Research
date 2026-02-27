# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Gateway-Centric AI Agent Platform with Modular Abstraction Layers

**Key Characteristics:**
- **Central orchestration** through a WebSocket Gateway (port 18789) that coordinates all components
- **Plugin architecture** allowing extensible channels, tools, memory backends, and custom adapters
- **Layer-based abstraction** separating concerns across channel adapters, session management, agent runtime, and tool dispatch
- **File-first memory** design storing all persistent knowledge as Markdown files with hybrid search (vector + FTS5)
- **MCP-first tool integration** where Model Context Protocol is the standard for tool communication
- **Multi-agent capable** with inter-agent communication, delegation, and collaborative workflows

---

## Layers

**Gateway Layer:**
- Purpose: Central orchestrator managing all component communication, message routing, session lifecycle, and distributed coordination
- Location: `00-Foundation/openclaw-architecture.md` (architecture reference), `01-Mac-Mini-Setup/` (deployment)
- Contains: WebSocket server (port 18789), HTTP REST API, internal message bus, health monitoring, plugin hosting
- Depends on: Agent pool, tool registry, memory system, channel adapters
- Used by: All external and internal components (channels, agents, tools, clients)
- Key configs: `~/.openclaw/` directory structure (not present locally, defined in research docs)

**Channel Abstraction Layer:**
- Purpose: Normalize messages from external platforms (Slack, Discord, Telegram, WhatsApp, web UI, CLI) into unified internal format
- Location: `00-Foundation/core-concepts.md` (Channel section, 3.1-3.4), `07-Channel-Setup/` (setup guides for each channel)
- Contains: Platform adapters, message normalization logic, multi-channel user identity mapping, event emission
- Depends on: Gateway for message routing and session attachment
- Used by: Gateway (receives normalized messages), Sessions (message context)
- Pattern: Each platform gets an adapter (e.g., `WhatsApp Adapter → Normalizer → OpenClaw Message → Gateway`)

**Session & Context Layer:**
- Purpose: Maintain conversational context for each user-agent interaction, including message history, state variables, and memory context
- Location: `00-Foundation/core-concepts.md` (Sessions section, 6.1-6.4), `00-Foundation/openclaw-architecture.md` (Session Management, 4.1-4.4)
- Contains: Session objects (user, agent, channel, message history), context window management, summarization strategy, persistence layer
- Depends on: Memory system (for on-demand history search), Agent runtime (for execution context)
- Used by: Agent runtime, Channel adapters (resume sessions)
- Persistence: SQLite (`~/.openclaw/data/sessions.db`), memory cache, optional external (Postgres/Redis for multi-instance)
- Pattern: Tiered context (pinned system prompt → recent 50 messages → summarized older messages → searchable full history)

**Agent Runtime Layer:**
- Purpose: Execute AI reasoning over system prompts, skill instructions, context, and memory, orchestrating tool calls
- Location: `00-Foundation/core-concepts.md` (Agents section, 4.1-4.3), `00-Foundation/openclaw-architecture.md` (Agent System, 3.1-3.4)
- Contains: Agent configuration (model, skills, tools, permissions), prompt assembly, LLM integration, tool dispatching, session management
- Depends on: Skills (for prompt injection), Tool registry (for invocation), Memory system (for context retrieval)
- Used by: Gateway (receives messages, returns responses), Session layer (context injection)
- Lifecycle: Registration → Instantiation (first message) → Warm state → Idle suspend (15 min) → Resumption → Termination
- Types: Interactive (user-waiting), Autonomous (cron/event-triggered), Hybrid (escalating)

**Memory Layer:**
- Purpose: Persistent knowledge storage with file-first design, hybrid search (vector + FTS5), and automatic indexing
- Location: `04-Memory-and-RAG/` directory (all core docs), `00-Foundation/core-concepts.md` (Memory section, 2.1-2.6)
- Contains: MEMORY.md (root persistent file), daily logs directory, SQLite with FTS5 + vector embeddings, chunk cache
- Depends on: File system (primary source), embedding model (OpenAI or configured), watch paths for auto-index
- Used by: Agent runtime (query), Session layer (context injection), Daily log system (auto-append)
- Search strategy: Hybrid (semantic vector search + exact FTS5 keyword search merged via Reciprocal Rank Fusion)
- Config: `~/.openclaw/memory/config.yaml` (chunk size, vector model, watch paths, reindex interval)

**Tool & Skill Layer:**
- Purpose: Package reusable capabilities (skills with prompts + tools) and dispatch tool invocations via MCP
- Location: `00-Foundation/core-concepts.md` (Skills section 1.1-1.4, Tools section 5.1-5.4), `08-Capabilities-Deep-Dive/` (capability implementations)
- Contains: Skill manifests (skill.yaml), prompt templates, tool definitions, MCP server adapters, permission models
- Depends on: MCP protocol for tool communication, Agent runtime for skill injection
- Used by: Agent runtime (skill prompts injected into system prompt), Tool dispatcher (MCP invocation)
- Tool registration: MCP servers (recommended), custom adapters, inline functions
- Permission model: Enabled/disabled, require_confirmation, rate_limit, allowed/denied args, timeout, sandbox flags
- Tool chains: Predefined sequences of tool calls executed as single workflow

**Plugin Layer:**
- Purpose: Extend Gateway functionality without core modification (channels, tools, auth, memory backends, middleware)
- Location: `00-Foundation/openclaw-architecture.md` (Plugin Architecture, 8.1-8.3)
- Contains: Plugin manifest (plugin.yaml), hook implementations, lifecycle management
- Depends on: Gateway event system for hook registration
- Used by: Gateway (loads and manages plugin lifecycle)
- Types: Channel plugins, tool plugins, memory plugins, auth plugins, middleware, UI extensions

---

## Data Flow

**Interactive Message Flow (User → Agent → Response):**

1. User sends message on external platform (e.g., Slack)
2. Platform webhook delivered to Channel Adapter
3. Adapter normalizes to OpenClaw message format
4. Gateway receives message on internal bus (topic: `channel.*`)
5. Session Manager: Find or create session, load context window, attach memory context via hybrid search
6. Agent Router: Determine target agent (from channel config, session, or user preference)
7. Agent Runtime: Load system prompt + skill prompts, inject context window + memory results, send to LLM
8. **Tool Loop (if LLM requests tool call):**
   - Tool Dispatcher routes to correct MCP server or adapter
   - Tool executes, returns result to Agent Runtime
   - Agent incorporates result and requests next step from LLM (loop)
9. **Final Response:**
   - Update session context with new messages
   - Index response in memory system
   - Transform for target channel (strip Slack blocks if Telegram, etc.)
10. Channel Adapter sends response back to user

**Autonomous Agent Flow (Cron/Event → Task → Output):**

1. External trigger fires (cron job, webhook, event from message bus)
2. Gateway creates internal session (anonymous user, autonomous agent assigned)
3. Agent executes predefined task (no user input waiting)
4. Results sent to configured output: channel message, file write, API call, or another agent

**State Management:**

- **Session state:** Message history, context window, state variables (key-value), tool results
- **Agent state:** Loaded skills, active tools, model config, resource allocations
- **Memory state:** Indexed chunks (SQLite FTS5 + vector table), watch paths tracking, embeddings cache
- **Tool state:** MCP connections, permission overrides per session, rate limit counters

---

## Key Abstractions

**Message (Internal Format):**
- Purpose: Normalized representation of any platform's message
- Contains: type, content, sender, channel, metadata, timestamp
- Produced by: Channel adapters
- Consumed by: Gateway, Session manager, Agent runtime
- Pattern: Each channel normalizes to this schema; agents never see platform-specific formats

**Session:**
- Purpose: Container for a conversational context between user(s) and agent(s)
- Contains: session_id, user_id, agent_id, channel_id, message history, state variables, context window
- Lifecycle: Created on first message, persisted to SQLite, can be resumed/forked
- Persistence strategy: Hot cache (in-memory) → Cold storage (SQLite) → Optional external (Postgres)

**Skill:**
- Purpose: Packaged reusable capability bundling prompts, tools, and configuration
- Contains: skill.yaml manifest, system.md (prompt), examples.md (few-shot), tools/, config/
- Lifecycle: Discovered via ClawHub, installed to `~/.openclaw/skills/`, attached to agent's skills list
- Injection mechanism: Skill's system.md concatenated into agent's system prompt

**Tool (via MCP):**
- Purpose: Function that agent can invoke to interact with external systems
- Protocol: Model Context Protocol (JSON-RPC 2.0 over stdio/SSE/WebSocket)
- Discovery: MCP server advertises available tools, Gateway negotiates schema
- Permission model: Three-level hierarchy (global → agent → session overrides)

**Memory Fragment:**
- Purpose: Indexed unit of persistent knowledge (chunks of Markdown files)
- Storage: File (primary source of truth) + SQLite (FTS5 index + vector embeddings)
- Search: Hybrid approach merging vector similarity (semantic) + FTS5 keywords (exact)
- Retrieval: Via `memory-search` tool or background context injection into agent

**Agent Configuration:**
- Purpose: Define agent's behavior, model, skills, tools, permissions
- Format: YAML file in `~/.openclaw/agents/` or project `.openclaw/agents/`
- Contains: name, model (provider + model name), system_prompt, skills[], tools[], permissions{}, channels[]
- Lifecycle: Loaded on startup, hot-reloadable via API

---

## Entry Points

**Gateway WebSocket Server:**
- Location: Port 18789 (configurable)
- Triggers: Client connection (channel, agent, web UI, CLI, third-party)
- Responsibilities: Accept WebSocket, authenticate, create/resume session, route messages, coordinate responses
- Protocol: WebSocket with JSON-RPC 2.0 message framing

**HTTP REST API:**
- Location: Same gateway server, multiple endpoints (`/api/v1/*`)
- Triggers: REST requests from web UI, CLI, external integrations
- Responsibilities: Agent CRUD, session inspection, skill management, memory search, health checks
- Common endpoints: `/api/v1/agents`, `/api/v1/sessions`, `/api/v1/tools`, `/api/v1/memory/search`

**Channel Adapters (Platform-Specific):**
- Location: Separate for each platform (Slack, Discord, Telegram, WhatsApp, Web, CLI)
- Triggers: Platform webhooks or polling (depending on adapter)
- Responsibilities: Receive platform messages, normalize to internal format, send to Gateway
- Example: Slack adapter receives webhook → normalizes → sends to Gateway on internal bus

**Autonomous Triggers:**
- Location: External cron, webhooks, message bus events
- Triggers: Time-based (cron), event-based (webhook from external service), message bus event
- Responsibilities: Create internal session, execute agent task, deliver output

**CLI:**
- Location: `openclaw` command-line tool
- Triggers: User types `openclaw` commands
- Responsibilities: Parse command, call REST API or WebSocket, display results
- Example: `openclaw session list`, `openclaw memory search "database"`

---

## Error Handling

**Strategy:** Three-tier error recovery with user-facing degradation

**Tier 1 - Agent Level:**
- Tool call fails: Agent logs failure, continues with next step (may retry)
- Model API error: Exponential backoff, eventual timeout with user notification
- Skill missing: Agent notified, may skip skill functionality or escalate

**Tier 2 - Session Level:**
- Session state corrupted: Recreate from SQLite backup, resume from last saved message
- Memory search timeout: Return empty results, continue without memory context
- Tool dispatcher unavailable: Queue tool calls, retry on reconnection

**Tier 3 - Gateway Level:**
- Gateway crash: Sessions persist in SQLite; on restart, hot-load active sessions
- Persistent failure: Health monitor triggers auto-restart (configurable max attempts)
- User loses connection: Client can reconnect and resume session by session_id

**Patterns:**
- **Graceful degradation:** If memory is unavailable, agent operates without context injection
- **Async retry:** Failed tool calls queued for later retry (configurable backoff strategy)
- **User notification:** Errors surfaced to user in natural language, e.g., "I couldn't access the database, let me try again"
- **Audit trail:** All errors logged with context for debugging

---

## Cross-Cutting Concerns

**Logging:**
- Framework: Structured logging (JSON-based)
- Levels: debug, info, warn, error
- Flow: Each component logs entry/exit and key decisions
- Aggregation: Centralized logging via Gateway's logging module
- Config: `gateway.log_level` in main config

**Validation:**
- Input: All external messages validated against schema before processing
- Tool calls: Permission checks before dispatch, argument whitelist/blacklist enforcement
- Config: Agent/skill/tool configs validated on load, hot-reload validated before applying

**Authentication:**
- API key required on all Gateway connections
- Session tokens issued after first auth, used for reconnection
- Per-agent permissions checked before tool invocation
- Optional: OAuth support via auth plugins

**Rate Limiting:**
- Global: Per-user limit (configurable, e.g., 100 messages/min)
- Per-tool: Rate limit overrides at global/agent/session level
- Per-channel: Platform-specific limits (e.g., Slack rate limits)
- Enforcement: At Gateway level, returns 429 if exceeded

**Observability:**
- Metrics: Message count, tool execution time, memory search latency, agent resource usage
- Health checks: Gateway → agents, tools, memory system (periodic)
- Audit logging: All tool invocations, auth failures, permission denials logged with user/timestamp

---

*Architecture analysis: 2026-02-27*

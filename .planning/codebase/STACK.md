# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- TypeScript - OpenClaw core codebase, MCP servers (GoHighLevel-MCP)
- Node.js/JavaScript - Gateway server, agents, web UI, CLI tools
- Python - REST API adapters, data processing (e.g., Clay enrichment, lead enrichment pipelines)
- Bash/Shell - Configuration, installation scripts, operational scripts

**Secondary:**
- SQL - PostgreSQL queries (Supabase), SQLite queries (local memory storage)
- YAML - Agent definitions, skill manifests, configuration files
- JSON - Configuration, MCP messages, data serialization

## Runtime

**Environment:**
- Node.js 22+ (required for OpenClaw core and npm-based tools)
- macOS (M4 Pro Mac Mini as primary deployment target)
- Docker (containerization layer for isolated deployments)
- Docker Desktop v27+ with Apple Silicon support

**Package Manager:**
- npm 10+ (standard Node.js package manager)
- pnpm (optional, faster alternative to npm)
- Homebrew (macOS package manager for CLI tools, Docker, Ollama)

## Frameworks

**Core:**
- OpenClaw (v1.5+) - Gateway-centric AI agent platform with WebSocket server (port 18789), MCP protocol support
- OpenAI-compatible API protocol - Ollama exposes LLMs via OpenAI API format at port 11434

**Testing:**
- Jest (implied, standard Node.js testing framework)
- Vitest (modern TypeScript test runner, not confirmed in scope)

**Build/Dev:**
- npm scripts (build, start commands)
- PM2 - Process manager for 24/7 operation, auto-restart, log rotation
- Docker Compose v2+ - Multi-service orchestration (OpenClaw + supporting services)

**Web/UI:**
- Next.js (dashboard at ~/.openclaw/dashboard, port 3000)
- React (web UI components)

## Key Dependencies

**Critical:**
- `@modelcontextprotocol/*` - MCP protocol client/server implementations
- `@airtable/mcp-server` - Airtable MCP integration
- OpenClaw CLI (`openclaw` npm package) - Core gateway and agent runtime
- Ollama - Local LLM inference engine (runs natively, not in container)
- PM2 - Process management and auto-restart

**Infrastructure:**
- PostgreSQL 15 (via Supabase) - RAG storage, persistent data
- SQLite + FTS5 - Local memory indexing, hybrid search (file-first approach in `~/.openclaw/memory/`)
- Redis (optional, for distributed deployments)
- MCP Servers (stdio-based):
  - GoHighLevel-MCP (`Desktop/GoHighLevel-MCP`, TypeScript, custom-built)
  - n8n MCP (`Desktop/rise-local-n8n`, running on Windows machine)
  - Airtable MCP (via @airtable/mcp-server)
  - Supabase MCP (custom, project ID: `jitawzicdwgbhatvjblh`)

**LLM Models (via Ollama):**
- `qwen3:14b` - Primary recommendation, 8.5 GB disk, 9 GB RAM, strong tool use
- `qwen3:8b` - Smaller, faster, for triage tasks
- `deepseek-r1:14b` - Complex reasoning (optional)
- `codellama:13b` - Code generation (optional)
- `nomic-embed-text` - Embeddings for RAG
- `mxbai-embed-large` - Alternative embedding model

**Cloud LLM Providers (APIs):**
- Anthropic Claude API - Claude Haiku 4.5 (cheap), Claude Sonnet 4.5 (reasoning)
- OpenAI API - gpt-4o-mini (cheap), gpt-4o (premium)
- Google Gemini API (optional)
- OpenRouter API - Multi-provider proxy

## Configuration

**Environment:**
- Managed via `.env` file at `~/.openclaw/.env` (native) or `~/openclaw/.env` (Docker)
- Required vars: `OPENCLAW_PORT`, LLM provider keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`), `OLLAMA_BASE_URL`
- Optional vars: `OPENCLAW_HOST`, `OPENCLAW_LOG_LEVEL`, `OPENCLAW_AUTH_TOKEN`, memory settings
- Secrets never stored in code; injected via environment at runtime

**Build:**
- `openclaw.config.yaml` or `~/.openclaw/config.json` - Gateway configuration (channels, agents, tools, memory)
- `agents/*.yaml` - Agent definitions (in `~/.openclaw/agents/` or project-local)
- `skills/*/skill.yaml` - Installed skill manifests
- `plugins/*/plugin.yaml` - Plugin configurations
- `tool-permissions.yaml` - Tool access control rules
- `memory.config.yaml` - Memory system settings (vector model, chunk size, search strategy)
- PM2 ecosystem file (`~/openclaw-ecosystem.config.js`) - Process management for native install
- Docker Compose file (`~/openclaw/docker-compose.yml`) - Container orchestration

## Platform Requirements

**Development:**
- macOS 12+ (Apple Silicon M4 Pro recommended for Mac Mini)
- 32-64 GB RAM (6-10 GB for Docker, rest for Ollama and macOS)
- Docker Desktop (if containerized) OR native Node.js 22+
- Ollama service running on host (port 11434)
- Optional: Tailscale VPN for secure remote access

**Production:**
- Mac Mini M4 Pro (specified in roadmap)
- 24/7 uptime via PM2 (native) or Docker (containerized)
- Tailscale Funnel or n8n relay for webhook-based integrations
- Network: local development, remote access via VPN only (not public internet)

## Storage

**Local:**
- `~/.openclaw/memory/` - File-first memory (markdown files + SQLite index)
- `~/.openclaw/data/sessions.db` - SQLite sessions database
- `~/.openclaw/data/memory.db` - SQLite memory index with FTS5 and pgvector embedding support
- `~/.openclaw/logs/` - PM2 logs (with rotation via pm2-logrotate module)

**Remote:**
- Supabase PostgreSQL (project `jitawzicdwgbhatvjblh`) - RAG storage with pgvector, realtime subscriptions
- Airtable - Content calendar, tracking (via API)

**Ephemeral:**
- In-memory cache (OpenClaw Gateway) - Hot sessions, sub-millisecond access
- Redis (optional, distributed deployments) - Session/state cache

---

*Stack analysis: 2026-02-27*

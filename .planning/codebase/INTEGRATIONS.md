# External Integrations

**Analysis Date:** 2026-02-27

## APIs & External Services

**CRM & Lead Management:**
- GoHighLevel - CRM operations, contacts, pipelines, lead management
  - SDK/Client: Custom TypeScript MCP server (`Desktop/GoHighLevel-MCP`)
  - Auth: `GHL_API_KEY`, `GHL_LOCATION_ID` env vars
  - API Base: `https://services.leadconnectorhq.com` (GHL API v2)
  - Transport: MCP stdio protocol
  - Status: Built, ready for integration

- Nutshell (legacy) - CRM predecessor being migrated to GHL
  - Auth: API keys via credential management
  - Status: Data migration in progress to GHL

- Apollo (lead data enrichment) - Prospect research, email finding
  - SDK/Client: REST API adapter
  - Auth: `APOLLO_API_KEY`
  - Status: Integration available via REST adapter

**Lead Enrichment & Verification:**
- Clay.com - Contact enrichment, company data, technographic data
  - SDK/Client: REST API adapter (Python, builds lead schema normalization)
  - Auth: `CLAY_API_KEY`
  - Base URL: `https://api.clay.com/v1`
  - Endpoints: `/enrichments` (POST), table operations
  - Status: Medium priority for building adapter

**Content & Workflow Automation:**
- n8n - Workflow orchestration, automation engine
  - SDK/Client: n8n MCP server (running on Windows machine `Desktop/rise-local-n8n`)
  - Transport: MCP stdio protocol
  - API: REST API for workflow execution, node search, templates
  - Status: Active, running on Windows; ready to integrate
  - Use: Lead discovery pipelines, content generation workflows

- Airtable - Content calendar, tracking, client data management
  - SDK/Client: Airtable MCP server (`@airtable/mcp-server` npm package)
  - Auth: `AIRTABLE_API_KEY`
  - Transport: MCP stdio protocol
  - Status: Currently active in Claude Code; ready for direct reuse
  - Tables: Content calendar, client bases (from `06-Integrations/airtable/client-bases.md`)

**Content Generation & Distribution:**
- OnTrack Marketing (internal) - Content generation and distribution platform
  - SDK/Client: FastAPI backend + custom REST API bridge
  - Tech Stack: FastAPI (Python), Next.js (UI), PostgreSQL, Redis, Qdrant (vector DB)
  - Auth: API keys via credential management
  - Status: Built, needs OpenClaw integration bridge
  - Priority: P2 (medium-term)

- WordPress - Blog hosting and content deployment
  - SDK/Client: REST API (WordPress REST API endpoint)
  - Auth: Application passwords or API keys
  - Endpoints: `/wp-json/wp/v2/posts`, `/wp-json/wp/v2/pages`
  - Status: Integration documented for chatbot deployment
  - Use: Content publication, blog automation

**SEO & Analytics:**
- Google Search Console - Search performance, indexing data
  - SDK/Client: REST API adapter
  - Auth: OAuth2 flow (via Google Workspace credentials)
  - Status: Integration documented for SEO monitoring

- Semrush - SEO analysis, keyword research, competitor tracking
  - SDK/Client: REST API adapter
  - Auth: `SEMRUSH_API_KEY`
  - Status: Integration available for competitor intelligence

- CallRail - Call tracking and analytics
  - SDK/Client: REST API adapter
  - Auth: API key authentication
  - Webhooks: Event-based integration for call logging
  - Status: Documented for content pipeline integration

**Communication & Channels:**
- Twilio - WhatsApp Business, SMS delivery
  - SDK/Client: REST API
  - Auth: Account SID + Auth Token
  - Endpoints: `/Messages` (POST for sending), Webhooks for receiving
  - Status: Recommended for WhatsApp Business API access
  - Config: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`
  - Protocol: HTTP webhooks (requires Tailscale Funnel or relay)

- Meta WhatsApp Cloud API - Direct WhatsApp Business integration
  - SDK/Client: REST API
  - Auth: Business Account ID, access tokens
  - Alternative to: Twilio (direct integration option)
  - Status: Documented but Twilio recommended for easier setup

- Discord - Team communication, bot integration
  - SDK/Client: Discord.js (Node.js library) or REST API
  - Auth: Bot token via Discord Developer Portal
  - Transport: WebSocket (persistent connection, no webhooks needed)
  - Status: Documented, channel adapter available

- Slack - Team communication, bot integration
  - SDK/Client: @slack/bolt Node.js framework or REST API
  - Auth: Bot token + App token
  - Transport: Webhooks (Events API) or Socket Mode (WebSocket alternative)
  - Status: Documented, channel adapter available

- Telegram - Bot messaging, group chat
  - SDK/Client: Telegram Bot API (REST)
  - Auth: Bot token from @BotFather
  - Transport: Polling or webhooks
  - Status: Documented, channel adapter available

- Plaud - Voice note transcription API
  - SDK/Client: REST API
  - Auth: API key authentication
  - Webhooks: Event notifications for transcription completion
  - Status: Integration documented for voice processing

**LLM & AI Providers:**
- Anthropic Claude API - Model provider
  - Auth: `ANTHROPIC_API_KEY`
  - Models: Claude Haiku 4.5 (tier 2, cheap), Claude Sonnet 4.5 (tier 3, reasoning)
  - Base URL: `https://api.anthropic.com/v1`
  - Status: Primary LLM provider

- OpenAI API - Model provider (alternative)
  - Auth: `OPENAI_API_KEY`
  - Models: gpt-4o-mini (tier 2, cheap), gpt-4o (tier 3)
  - Base URL: `https://api.openai.com/v1`
  - Status: Supported as alternative

- Google Gemini API - Model provider (optional)
  - Auth: `GOOGLE_API_KEY`
  - Status: Supported but not primary

- OpenRouter API - Multi-model proxy
  - Auth: `OPENROUTER_API_KEY`
  - Status: Optional multi-provider access layer

**Local LLM:**
- Ollama - Local model serving
  - Base URL: `http://localhost:11434` (native) or `http://host.docker.internal:11434` (Docker)
  - API Protocol: OpenAI-compatible REST API
  - Models available: qwen3:14b (primary), qwen3:8b, deepseek-r1:14b, codellama, nomic-embed-text
  - Status: Always available, zero API cost

## Data Storage

**Databases:**
- Supabase (PostgreSQL 15)
  - Project ID: `jitawzicdwgbhatvjblh`
  - Connection: `postgresql://postgres:[password]@db.jitawzicdwgbhatvjblh.supabase.co:5432/postgres`
  - Client: Supabase SDK or direct psql
  - Extensions: pgvector (for RAG embeddings)
  - Status: Currently paused; reactivation planned (P1)
  - Use: RAG storage, hybrid vector + FTS search

- SQLite (local, file-first)
  - Paths: `~/.openclaw/data/sessions.db`, `~/.openclaw/data/memory.db`
  - Storage: Local filesystem (no network)
  - Extensions: FTS5 (full-text search)
  - Status: Always active, default memory backend
  - Use: Local sessions, memory indexing, hybrid search

- Airtable (cloud database + spreadsheet)
  - Connection: REST API via `@airtable/mcp-server`
  - Auth: `AIRTABLE_API_KEY`
  - Use: Content calendars, client data, tracking
  - Status: Active

- Redis (distributed, optional)
  - Purpose: Session cache, state management (multi-instance deployments only)
  - Status: Not required for single-machine setup

**File Storage:**
- Local filesystem only - `~/.openclaw/memory/` (Markdown files)
- OnTrack Marketing internal storage (image assets, generated content)
- Airtable attachments (documents, media)
- No external cloud storage (S3, etc.) currently integrated

**Caching:**
- In-memory cache (OpenClaw Gateway) - Hot sessions
- No Redis in basic setup; optional for scale

## Authentication & Identity

**Auth Provider:**
- Custom (OpenClaw API key-based)
  - Implementation: Environment variable `OPENCLAW_AUTH_TOKEN`
  - All clients must include token in WebSocket connection handshake
  - Generate: `openssl rand -hex 32`

**OAuth2 Integrations (external):**
- Google OAuth - For Google Search Console access
- Meta OAuth - For WhatsApp Cloud API
- Slack OAuth - For Slack app authentication
- Discord OAuth - For Discord bot authentication

**Credential Management:**
- Environment variables (`.env` file at `~/.openclaw/.env`)
- Encrypted credential storage (future: Supabase vault or external HashiCorp Vault)
- Per-request injection: Credentials added to tool calls before sending, never logged
- Credential rotation metadata tracked for expiry alerts

## Monitoring & Observability

**Error Tracking:**
- None detected (application-level logging only)
- Future: Sentry integration possible

**Logs:**
- File-based: PM2 logs at `~/.openclaw/logs/` (combined.log, out.log, error.log)
- Format: JSON-RPC message logging, agent execution traces, tool call results
- Rotation: pm2-logrotate module (50 MB per file, 10 files retained, daily rotation)
- Web UI: Real-time streaming via OpenClaw web interface (port 3000)

**Health Monitoring:**
- Gateway health endpoint: `GET http://localhost:18789/health`
- Integration health: Per-integration status checked periodically
- Memory usage: PM2 max_memory_restart limit (2 GB)
- Custom monitoring: Bash script examples provided for port checks, disk space, memory pressure

## CI/CD & Deployment

**Hosting:**
- Mac Mini M4 Pro (on-premises, 24/7 local server)
- Alternative: Cloud deployment via Docker (not primary, but supported)

**CI Pipeline:**
- None configured (research documentation only, not production code)
- Future: Possible GitHub Actions for skill validation

**Process Management:**
- PM2 (native install): Auto-restart, log rotation, boot persistence
- Docker Compose (containerized): Service orchestration, restart policies
- Both support 24/7 uptime and graceful updates

## Environment Configuration

**Required env vars:**
- `OPENCLAW_PORT` - Gateway port (default: 18789)
- `OPENCLAW_HOST` - Bind address (default: 0.0.0.0)
- `OPENCLAW_LOG_LEVEL` - Log verbosity (error, warn, info, debug, trace)
- At least one LLM provider key: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `OLLAMA_BASE_URL`
- `OLLAMA_BASE_URL` - Ollama service URL (`http://localhost:11434`)

**Integration-specific:**
- `GHL_API_KEY`, `GHL_LOCATION_ID` - GoHighLevel
- `AIRTABLE_API_KEY` - Airtable
- `CLAY_API_KEY` - Clay.com
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` - Twilio
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` - Slack
- `DISCORD_BOT_TOKEN` - Discord
- `TELEGRAM_BOT_TOKEN` - Telegram

**Secrets location:**
- `.env` file (local, native install): `~/.openclaw/.env`
- Docker environment: `~/openclaw/.env` (passed via docker-compose.yml)
- PM2 ecosystem file: Environment block in `~/openclaw-ecosystem.config.js`
- Git: Never committed; use `.env.example` as template

## Webhooks & Callbacks

**Incoming:**
- Slack Events API - Webhook for messages, mentions, reactions
  - URL: `https://[your-domain]/slack/events` (via Tailscale Funnel or relay)
  - Events: `message.app_home`, `app_mention`, `message.channels`, `message.groups`, `message.im`
  - Verification: Signing secret verification required for each request

- Twilio WhatsApp - Webhook for incoming messages
  - URL: `https://[your-domain]/whatsapp/webhook` (via Tailscale Funnel or n8n relay)
  - Messages: Inbound WhatsApp messages, delivery status updates
  - Verification: Twilio auth token verification

- CallRail - Webhook for call events
  - URL: Endpoint registered in CallRail dashboard
  - Events: Call completion, call recording ready
  - Status: Documented for integration

- Plaud - Webhook for transcription completion
  - URL: Registered in Plaud settings
  - Events: Transcription ready, audio processed
  - Status: Documented for voice processing

**Outgoing:**
- n8n workflows - Trigger external automations
  - Method: REST API call to n8n webhook endpoint
  - Payloads: Structured JSON with lead data, content, task info
  - Status: Primary orchestration bridge

- GoHighLevel - CRM updates via API
  - Method: REST API calls (via GHL MCP server)
  - Triggers: Lead created, contact updated, pipeline moved
  - Status: Bidirectional MCP integration

- Slack - Message send, updates, attachments
  - Method: REST API (`chat.postMessage`, `chat.update`)
  - Status: Outbound from OpenClaw to Slack

- Twilio - WhatsApp message send
  - Method: REST API (`/Messages` endpoint)
  - Status: Outbound from OpenClaw to Twilio

- Airtable - Record creation, updates
  - Method: REST API via MCP server
  - Status: Integrated

---

*Integration audit: 2026-02-27*

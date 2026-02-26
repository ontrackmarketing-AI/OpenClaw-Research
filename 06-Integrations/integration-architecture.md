# Integration Architecture

> How OpenClaw connects to external tools and services across your ecosystem.

## Overview

OpenClaw acts as an intelligent orchestration layer that connects to your existing tools through three primary mechanisms: MCP (Model Context Protocol) servers, REST API adapters, and webhook listeners. The goal is zero-rework reuse of what you have already built.

---

## Connection Methods

### 1. MCP (Model Context Protocol) Integration

MCP is the primary integration method. OpenClaw runs as an MCP **client** that consumes tool definitions from MCP **servers**. Each MCP server exposes a set of tools that OpenClaw can call during skill execution.

**How it works:**
1. OpenClaw loads MCP server configurations from its settings file
2. Each MCP server declares its available tools (name, description, input schema)
3. When an OpenClaw skill needs an external action, it calls the appropriate MCP tool
4. The MCP server executes the operation and returns results to OpenClaw
5. OpenClaw processes the response and continues the skill workflow

**Your existing MCP servers that plug directly in:**

| MCP Server | Location | Status | Tools Provided |
|---|---|---|---|
| GoHighLevel MCP | `Desktop/GoHighLevel-MCP` | TypeScript, built | CRM operations, contacts, pipelines |
| n8n MCP | Docker `Desktop/rise-local-n8n` | Running | Workflow execution, node search, templates |
| Airtable MCP | Claude Code config | Active, working | Base/table CRUD, record search |
| Supabase MCP | Claude Code config | Disabled (project paused) | Database queries, RPC calls |
| RAFE Obsidian MCP | Claude Code config | Active | Documentation read/write, session logging |

**Configuration pattern (in OpenClaw settings):**
```json
{
  "mcp_servers": [
    {
      "name": "gohighlevel",
      "type": "stdio",
      "command": "node",
      "args": ["C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP/dist/index.js"],
      "env": {
        "GHL_API_KEY": "${GHL_API_KEY}",
        "GHL_LOCATION_ID": "${GHL_LOCATION_ID}"
      }
    },
    {
      "name": "airtable",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@airtable/mcp-server"],
      "env": {
        "AIRTABLE_API_KEY": "${AIRTABLE_API_KEY}"
      }
    }
  ]
}
```

### 2. REST API Adapters

For tools that do not have MCP servers, OpenClaw uses REST API adapters. These are lightweight wrapper functions that translate OpenClaw tool calls into HTTP requests.

**Adapter structure:**
```python
class ClayAPIAdapter:
    def __init__(self, api_key: str):
        self.base_url = "https://api.clay.com/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def enrich_lead(self, company_domain: str) -> dict:
        """Call Clay enrichment API and return structured data."""
        response = await httpx.post(
            f"{self.base_url}/enrichments",
            headers=self.headers,
            json={"domain": company_domain}
        )
        return self._normalize_response(response.json())

    def _normalize_response(self, raw: dict) -> dict:
        """Map Clay response fields to OpenClaw standard lead schema."""
        return {
            "company_name": raw.get("company", {}).get("name"),
            "employee_count": raw.get("company", {}).get("size"),
            "industry": raw.get("company", {}).get("industry"),
            "technologies": raw.get("tech_stack", []),
            # ... more field mappings
        }
```

**When to use REST adapters instead of MCP:**
- The external API is simple (1-3 endpoints)
- No existing MCP server and building one is overkill
- You need custom response transformation
- The API uses non-standard auth (OAuth2 flows, signed requests)

### 3. Webhook Listeners

For event-driven integrations where external tools push data to OpenClaw.

**Architecture:**
```
External Service (GHL, n8n, form)
  -> Webhook POST to endpoint
  -> OpenClaw Gateway receives event
  -> Event router maps to skill
  -> Skill executes with event data
```

**Webhook endpoint options (given your local-first setup):**
1. **Tailscale Funnel** - Expose a local port to the internet via Tailscale. Best for development and small scale.
2. **n8n as relay** - n8n receives webhooks (it already has a public URL if configured) and forwards to OpenClaw. Best because n8n can pre-process and buffer.
3. **Cloudflare Tunnel** - Free, fast, reliable. Expose a local endpoint globally.

---

## Authentication Flow

Credentials are never stored in OpenClaw code or skill definitions. They follow this hierarchy:

1. **Environment variables** - API keys set as env vars, referenced by `${VARIABLE_NAME}` in config
2. **Credential store** - Encrypted credential storage (Supabase vault or local encrypted file)
3. **Per-request injection** - OpenClaw injects credentials when calling tools, before the request leaves the system

**Credential passing sequence:**
```
Skill requests tool call
  -> OpenClaw resolves tool to MCP server or adapter
  -> Credential manager looks up required credentials for that integration
  -> Credentials injected into the tool call context (env vars for MCP, headers for REST)
  -> Tool executes with credentials
  -> Credentials never logged or stored in memory/RAG
```

**Credential rotation:**
- Store API keys with expiry metadata
- OpenClaw alerts when credentials are approaching expiry
- For OAuth2 integrations, refresh tokens are handled by the adapter layer

---

## Data Flow

The complete data flow for an OpenClaw tool call:

```
1. User or trigger initiates task
2. OpenClaw agent plans execution (selects skills + tools)
3. For each tool call:
   a. Agent formats tool input per MCP/adapter schema
   b. Tool call dispatched to integration layer
   c. Integration layer adds auth, rate-limit checks, retry logic
   d. Request sent to external service
   e. Response received
   f. Response validated and normalized to OpenClaw schema
   g. Normalized data returned to agent
4. Agent processes all tool results
5. Agent produces final output or triggers next step
```

**Data normalization is critical.** Every integration must map its response to OpenClaw's standard schemas:
- `LeadRecord`: standard lead/contact fields
- `EnrichmentResult`: enrichment data with confidence scores
- `ContentItem`: content pieces for calendar/publishing
- `WorkflowResult`: execution status and outputs from n8n

---

## Error Handling Across Integrations

Every integration call is wrapped in a standard error handler:

| Error Type | Handling Strategy |
|---|---|
| **Network timeout** | Retry with exponential backoff (3 attempts, 1s/2s/4s) |
| **Rate limit (429)** | Queue and retry after `Retry-After` header value |
| **Auth failure (401/403)** | Log, alert user, do not retry (credentials need refresh) |
| **Server error (5xx)** | Retry up to 3 times, then fail gracefully with partial results |
| **Invalid response** | Log the raw response, return error to agent, agent can decide to retry or skip |
| **MCP server crash** | Restart MCP server process, retry once, then fail with clear error |

**Graceful degradation:** If a non-critical integration fails (e.g., social profile enrichment), OpenClaw continues with partial data rather than failing the entire workflow.

---

## Integration Registry

OpenClaw maintains a runtime registry of all available integrations:

```python
INTEGRATION_REGISTRY = {
    "gohighlevel": {
        "type": "mcp",
        "status": "active",
        "tools": ["create_contact", "update_contact", "search_contacts", "create_opportunity", ...],
        "health_check": "last_successful_call < 5min",
        "priority": "P0"
    },
    "clay": {
        "type": "rest_adapter",
        "status": "active",
        "tools": ["enrich_company", "enrich_person", "create_table", "add_row"],
        "health_check": "api_ping",
        "priority": "P0"
    },
    "supabase": {
        "type": "mcp",
        "status": "disabled",
        "tools": ["query", "insert", "update", "rpc"],
        "health_check": null,
        "priority": "P1 (reactivate when ready for RAG)"
    },
    # ... etc
}
```

**Health monitoring:** OpenClaw periodically checks each integration's health and marks unavailable integrations. Skills check the registry before calling tools and handle unavailability gracefully.

---

## Priority Order for Integrating Your Tools

Based on your current ecosystem and OpenClaw's needs:

| Priority | Integration | Reason | Effort |
|---|---|---|---|
| **P0** | GHL MCP | Core CRM, contacts, pipelines - every lead workflow needs this | Low (MCP exists) |
| **P0** | n8n MCP | Workflow orchestration backbone, already running | Low (MCP exists) |
| **P0** | Airtable MCP | Already active, content calendar, tracking | Zero (working now) |
| **P0** | Clay API adapter | Enrichment is core to the value prop | Medium (build adapter) |
| **P1** | RAFE Obsidian MCP | Documentation and session logging | Zero (working now) |
| **P1** | Supabase MCP | RAG storage, persistent data | Low (reactivate project) |
| **P1** | Rise Local pipeline | Lead discovery feeds into enrichment | Medium (connect existing) |
| **P2** | OnTrack Marketing | Content generation and distribution | Medium (build API bridge) |
| **P2** | Ralph AI dev loop | Development automation | Low (already integrated with Claude Code) |

**Integration sprint plan:**
- **Week 1:** Verify GHL MCP + n8n MCP + Airtable MCP work through OpenClaw. Build Clay adapter.
- **Week 2:** Reactivate Supabase. Connect Rise Local pipeline. Set up webhooks.
- **Week 3:** Build OnTrack bridge. Test full lead-to-close workflow.

---

## RESEARCH GAPS

- [ ] Exact MCP protocol version supported by OpenClaw (v1.0 vs draft)
- [ ] Whether OpenClaw supports dynamic tool registration (adding MCP servers at runtime)
- [ ] Maximum concurrent MCP server connections
- [ ] Whether OpenClaw can act as MCP server (not just client) for other tools to call it
- [ ] Performance benchmarks for MCP vs REST adapter calls

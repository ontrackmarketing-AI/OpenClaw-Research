# GoHighLevel MCP Server Reuse

> Connecting your existing GHL MCP server to OpenClaw for CRM operations.

---

## Your Existing GHL MCP Server

**Location:** `C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP`
**Language:** TypeScript
**Transport:** stdio (standard MCP pattern)
**Purpose:** Expose GoHighLevel CRM operations as MCP tools that any MCP client can call.

This server was built specifically for your workflow and already handles authentication, API versioning, and error responses for GHL API v2.

---

## Connecting to OpenClaw

### Step 1: Verify the MCP Server Builds and Runs

```bash
cd C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP
npm install
npm run build
# Test: node dist/index.js (should start and wait for MCP client connection)
```

### Step 2: Add to OpenClaw MCP Configuration

In your OpenClaw settings file (typically `~/.openclaw/config.json` or `openclaw.config.json`):

```json
{
  "mcpServers": {
    "gohighlevel": {
      "command": "node",
      "args": ["C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP/dist/index.js"],
      "env": {
        "GHL_API_KEY": "${GHL_API_KEY}",
        "GHL_LOCATION_ID": "${GHL_LOCATION_ID}",
        "GHL_BASE_URL": "https://services.leadconnectorhq.com"
      }
    }
  }
}
```

### Step 3: Set Environment Variables

Ensure these are set in your shell profile or `.env` file:

```bash
export GHL_API_KEY="your-ghl-api-key-here"
export GHL_LOCATION_ID="your-location-id-here"
```

**Getting your API key:**
1. Log into GoHighLevel
2. Go to Settings > Business Profile > API Keys (or Settings > Developer > API Keys)
3. Create a new API key with appropriate scopes
4. Copy the key (it is only shown once)

**Getting your Location ID:**
1. In GHL, go to Settings > Business Profile
2. The Location ID is in the URL or on the Business Profile page
3. Format: alphanumeric string like `abc123def456`

### Step 4: Test the Connection

From OpenClaw, try a simple operation:

```
"List all contacts in GoHighLevel"
```

OpenClaw should:
1. Recognize this requires the GHL MCP server
2. Call the appropriate tool (e.g., `search_contacts` or `list_contacts`)
3. Return results from your GHL account

---

## MCP Server Capabilities (Expected)

Based on typical GHL MCP implementations, your server likely supports:

### Core Contact Operations
| Tool | Description | GHL API Endpoint |
|---|---|---|
| `create_contact` | Create a new contact | POST /contacts/ |
| `get_contact` | Get contact by ID | GET /contacts/{id} |
| `update_contact` | Update contact fields | PUT /contacts/{id} |
| `delete_contact` | Delete a contact | DELETE /contacts/{id} |
| `search_contacts` | Search contacts by query | GET /contacts/search |

### Pipeline / Opportunity Operations
| Tool | Description | GHL API Endpoint |
|---|---|---|
| `create_opportunity` | Create deal in pipeline | POST /opportunities/ |
| `update_opportunity` | Update deal status/stage | PUT /opportunities/{id} |
| `get_pipelines` | List all pipelines | GET /opportunities/pipelines |

### Other Operations (may or may not exist)
| Tool | Description | Likely Status |
|---|---|---|
| `add_tag` | Add tag to contact | May exist |
| `remove_tag` | Remove tag from contact | May exist |
| `create_task` | Create a task | May not exist |
| `list_appointments` | Get appointments | May not exist |
| `send_message` | Send SMS/email | May not exist |
| `create_note` | Add note to contact | May not exist |
| `get_conversations` | List conversations | May not exist |

**RESEARCH GAP:** The exact tool list must be audited by reading the MCP server source code or running a tool listing command.

---

## Auditing the MCP Server

### Method 1: Read the Source Code

```bash
# Look at the MCP tool definitions
cat C:/Users/Owner/OneDrive/Desktop/GoHighLevel-MCP/src/index.ts
# Or wherever tools are registered
```

Look for patterns like:
```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      { name: "create_contact", description: "...", inputSchema: {...} },
      // ... more tools
    ]
  };
});
```

### Method 2: Use MCP Inspector

```bash
npx @modelcontextprotocol/inspector node dist/index.js
```

This opens a browser UI showing all available tools, their schemas, and lets you test them.

### Method 3: Ask Claude Code

With the GHL MCP configured in Claude Code, simply ask:
```
"What tools does the GoHighLevel MCP server provide?"
```

---

## Gaps: GHL API Capabilities Not in Your MCP Server

The GHL API v2 supports significantly more than basic CRUD. Operations likely missing from your MCP server:

### High-Value Missing Operations

1. **Workflow triggers** - Start/stop GHL workflows programmatically
   - `POST /contacts/{id}/workflow/{workflowId}`
   - Critical for automated nurture sequences

2. **Custom field management** - Create and list custom fields
   - `GET /locations/{locationId}/customFields`
   - `POST /locations/{locationId}/customFields`
   - Needed for dynamic field creation during onboarding

3. **Calendar operations** - Full appointment management
   - `GET /calendars/`
   - `POST /calendars/events`
   - Needed for booking automation

4. **Campaign management** - Email/SMS campaign operations
   - Trigger campaigns, check status, get results

5. **Form and survey data** - Read form submissions
   - `GET /forms/submissions`
   - Important for lead capture processing

6. **Conversation management** - Full messaging capability
   - `GET /conversations/`
   - `POST /conversations/messages`
   - Needed for AI-powered responses

7. **Reporting** - Pull analytics data
   - Pipeline reports, email stats, call logs

### Enhancement Plan

**Phase 1 (Immediate - with OpenClaw launch):**
- Ensure contact CRUD works perfectly
- Add opportunity/pipeline management if missing
- Add tag management if missing

**Phase 2 (Week 2-3):**
- Add workflow trigger capability
- Add custom field management
- Add calendar/appointment operations

**Phase 3 (Month 2):**
- Add conversation management
- Add campaign triggers
- Add reporting data pulls

---

## Configuration Reference

### GHL API Scopes Needed

When creating your API key, ensure these scopes are enabled:

| Scope | Operations |
|---|---|
| `contacts.readonly` | Search, get contacts |
| `contacts.write` | Create, update, delete contacts |
| `opportunities.readonly` | List pipelines, get deals |
| `opportunities.write` | Create, update deals |
| `locations/tags.readonly` | List tags |
| `locations/tags.write` | Create, add, remove tags |
| `locations/customFields.readonly` | List custom fields |
| `locations/customFields.write` | Create custom fields |
| `calendars.readonly` | List calendars, appointments |
| `calendars.write` | Create appointments |
| `workflows.readonly` | List workflows |

### Sub-Account Considerations

If you manage multiple GHL sub-accounts (one per client):
- Each sub-account has its own Location ID
- API keys can be scoped to specific sub-accounts
- OpenClaw should support switching Location ID per client context
- Consider a configuration pattern:

```json
{
  "clients": {
    "client_a": {
      "ghl_location_id": "loc_abc123",
      "ghl_api_key": "${GHL_API_KEY_CLIENT_A}"
    },
    "client_b": {
      "ghl_location_id": "loc_def456",
      "ghl_api_key": "${GHL_API_KEY_CLIENT_B}"
    }
  }
}
```

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| MCP server fails to start | Missing dependencies | Run `npm install` in GHL MCP directory |
| Auth errors (401) | Invalid or expired API key | Regenerate in GHL dashboard |
| Missing tools | MCP server doesn't expose them | Add tool handlers to server code |
| Timeout errors | GHL API is slow | Increase timeout in MCP client config |
| Rate limiting (429) | Too many API calls | Add rate limiting to MCP server |

---

## RESEARCH GAPS

- [ ] **CRITICAL:** Audit the actual tool list in GoHighLevel-MCP/src by reading the source code
- [ ] Verify GHL API key scopes and permissions
- [ ] Test each operation end-to-end through OpenClaw
- [ ] Determine if the MCP server handles GHL API pagination
- [ ] Check if the MCP server handles rate limiting gracefully
- [ ] Verify error responses are properly formatted for MCP protocol

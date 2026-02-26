# n8n MCP Server Reuse

> Connecting your existing n8n instance to OpenClaw via the n8n MCP server.

---

## Your Existing n8n Setup

| Property | Value |
|---|---|
| **Location** | `C:/Users/Owner/OneDrive/Desktop/rise-local-n8n` |
| **Runtime** | Docker container |
| **Status** | Running |
| **MCP Server** | Configured and available in Claude Code |
| **Custom Nodes** | Installed in Docker container |
| **Port** | Typically 5678 (verify in docker-compose.yml) |
| **Existing Workflows** | Lead processing, enrichment, email automation |

---

## n8n MCP Server

The n8n MCP server provides programmatic access to your n8n instance through the Model Context Protocol. This means any MCP client (Claude Code, OpenClaw) can:

- List all workflows
- Execute workflows by ID or name
- Get workflow execution results
- Search for nodes and templates
- Manage workflow state (activate/deactivate)

### How It Works

```
OpenClaw (MCP Client)
  -> n8n MCP Server (translates MCP calls to n8n API calls)
  -> n8n REST API (http://localhost:5678/api/v1)
  -> n8n Instance (executes the workflow)
  -> Results returned through the chain
```

---

## Connecting to OpenClaw

### Step 1: Verify n8n Is Running

```bash
# Check if n8n Docker container is running
docker ps | grep n8n

# Or check the API directly
curl http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: your-api-key"
```

### Step 2: Get or Create n8n API Key

1. Open n8n UI at `http://localhost:5678`
2. Go to **Settings** > **API** (or **Settings** > **n8n API**)
3. Generate a new API key if one does not exist
4. Copy the key and store as environment variable:

```bash
export N8N_API_KEY="your-n8n-api-key"
export N8N_API_URL="http://localhost:5678"
```

### Step 3: Add n8n MCP to OpenClaw Configuration

```json
{
  "mcpServers": {
    "n8n": {
      "command": "npx",
      "args": ["-y", "@n8n/mcp-server"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    }
  }
}
```

**Note:** Verify the exact npm package name for the n8n MCP server. It may be `@n8n/mcp-server`, `n8n-mcp`, or available through a different mechanism. Check the n8n documentation or your existing Claude Code configuration.

### Step 4: Test the Connection

From OpenClaw, try:
```
"List all workflows in n8n"
```

Expected response: A list of your n8n workflows with their IDs, names, and active status.

---

## Available Operations via MCP

Based on the n8n MCP server capabilities (verify by listing tools):

### Workflow Management

| Tool | Description | Example Use |
|---|---|---|
| `list_workflows` | Get all workflows | "Show me all available automation workflows" |
| `get_workflow` | Get workflow details by ID | "Get the details of workflow #5" |
| `execute_workflow` | Trigger workflow execution | "Run the lead enrichment workflow" |
| `activate_workflow` | Enable a workflow | "Turn on the daily report workflow" |
| `deactivate_workflow` | Disable a workflow | "Pause the email sender workflow" |

### Execution Management

| Tool | Description | Example Use |
|---|---|---|
| `get_executions` | List recent executions | "Show recent workflow runs" |
| `get_execution` | Get specific execution details | "What was the result of execution #123?" |

### Node Discovery

| Tool | Description | Example Use |
|---|---|---|
| `search_nodes` | Find available n8n nodes | "What nodes are available for Slack?" |
| `get_node` | Get node details and config | "How do I configure the HTTP Request node?" |

### Template Search

| Tool | Description | Example Use |
|---|---|---|
| `search_templates` | Find workflow templates | "Find templates for lead enrichment" |
| `get_template` | Get template details | "Show me template #1234" |

---

## Configuration Details

### n8n API URL

The URL depends on your Docker setup:

| Scenario | API URL |
|---|---|
| Docker on same machine | `http://localhost:5678` |
| Docker with custom port | `http://localhost:YOUR_PORT` |
| Tailscale network | `http://your-hostname:5678` |
| Behind reverse proxy | `https://n8n.yourdomain.com` |

**Check your docker-compose.yml:**
```bash
# In your rise-local-n8n directory
cat docker-compose.yml | grep -A5 "ports"
```

### n8n API Authentication

The n8n API uses an API key passed in the `X-N8N-API-KEY` header. The MCP server handles this automatically when configured with the `N8N_API_KEY` environment variable.

### Network Considerations

Since both n8n and OpenClaw run locally:
- No firewall issues (localhost to localhost)
- No Tailscale configuration needed
- Docker container must expose the API port
- If n8n runs in Docker, ensure the port mapping is correct: `5678:5678`

---

## Testing: Trigger a Simple Workflow

### Create a Test Workflow

If you don't have a simple test workflow, create one in n8n:

1. Open n8n UI
2. Create new workflow
3. Add a **Webhook** trigger node (or **Manual Trigger** for testing)
4. Add a **Set** node that sets `{"message": "Hello from n8n!", "timestamp": "{{ $now }}"}`
5. Save and activate the workflow
6. Note the workflow ID

### Execute via OpenClaw

```
"Execute n8n workflow [ID] and show me the result"
```

### Execute via Direct API (for debugging)

```bash
curl -X POST "http://localhost:5678/api/v1/workflows/[WORKFLOW_ID]/execute" \
  -H "X-N8N-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"data": {"test": true}}'
```

---

## Custom Nodes in Your Setup

Your rise-local-n8n Docker container includes custom nodes. These are specialized nodes you've built or installed for specific operations.

**To check installed custom nodes:**
1. Open n8n UI
2. Look at the node panel on the left
3. Custom/community nodes are usually marked with a different icon

**Custom nodes work through MCP** as long as they are part of workflows. The MCP server executes the entire workflow; it does not call individual nodes directly.

**Common custom nodes in local marketing setups:**
- Google Places node (lead discovery)
- Clay enrichment node
- Custom webhook processors
- Data transformation nodes

---

## Key Workflows to Connect

These are the workflows in your n8n instance that OpenClaw should be able to trigger:

| Workflow | Purpose | OpenClaw Trigger |
|---|---|---|
| Lead Discovery | Scrape Google Places for businesses | "Find [industry] businesses in [location]" |
| Lead Enrichment | Run enrichment pipeline on a lead | "Enrich this lead: [domain]" |
| Email Sequence | Start/manage email outreach | "Start nurture sequence for [contact]" |
| Competitor Scrape | Monitor competitor websites | "Check competitors for [business]" |
| Daily Report | Generate daily metrics summary | Scheduled, but can be triggered manually |
| Content Publish | Post content to social platforms | "Publish this content to [platform]" |
| Webhook Relay | Receive and forward external webhooks | Automatic (listens for incoming) |

---

## Performance Considerations

| Factor | Detail |
|---|---|
| **Execution time** | Simple workflows: < 1 second. Complex enrichment: 30-120 seconds. |
| **Concurrent executions** | n8n free/community: typically 5-20 concurrent. Self-hosted: configurable. |
| **Memory** | Docker container should have at least 1GB RAM allocated |
| **Timeout** | Default n8n timeout is 300 seconds. Adjust for long-running workflows. |
| **Rate limits** | n8n API itself has no rate limit, but workflows may call rate-limited external APIs |

---

## RESEARCH GAPS

- [ ] **CRITICAL:** List all tools exposed by the n8n MCP server (`npx @n8n/mcp-server --list-tools` or similar)
- [ ] Verify the exact npm package name for the n8n MCP server
- [ ] List all existing workflows in your n8n instance with their IDs
- [ ] Identify which custom nodes are installed in your Docker container
- [ ] Test workflow execution through MCP and measure latency
- [ ] Verify n8n API key exists and has proper permissions
- [ ] Check Docker resource allocation for n8n container

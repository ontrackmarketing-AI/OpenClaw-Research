# Airtable MCP Reuse

> Leveraging your already-active Airtable MCP server with OpenClaw.

---

## Current Status

| Property | Value |
|---|---|
| **MCP Server** | Fully configured and active in Claude Code |
| **Status** | Working - no setup needed |
| **Authentication** | AIRTABLE_API_KEY environment variable (already set) |
| **Available Tools** | list_bases, list_tables, create_table, create_field, update_field, list_records, create_record, update_record, delete_record, search_records, get_record |

This is the only integration that requires **zero work** to connect to OpenClaw. The Airtable MCP server is already active, authenticated, and fully functional.

---

## Connecting to OpenClaw

### Step 1: Verify Current Configuration

The Airtable MCP is already configured. Verify by asking Claude Code:
```
"List my Airtable bases"
```

If this returns your bases, the MCP is working and will work identically through OpenClaw.

### Step 2: Add to OpenClaw Config (If Not Already There)

If OpenClaw has its own MCP configuration separate from Claude Code:

```json
{
  "mcpServers": {
    "airtable": {
      "command": "npx",
      "args": ["-y", "@airtable/mcp-server"],
      "env": {
        "AIRTABLE_API_KEY": "${AIRTABLE_API_KEY}"
      }
    }
  }
}
```

### Step 3: Test

```
"List all tables in my Airtable bases"
"Search for records in [table name] where [field] contains [value]"
```

---

## Available Operations

### Base and Table Operations

| Operation | Tool Name | Description | Example |
|---|---|---|---|
| List bases | `list_bases` | Get all accessible Airtable bases | "Show me my Airtable bases" |
| List tables | `list_tables` | Get tables in a specific base | "What tables are in base X?" |
| Create table | `create_table` | Create a new table with fields | "Create a leads table with name, email, score fields" |
| Create field | `create_field` | Add a field to existing table | "Add a 'lead_score' number field to the leads table" |
| Update field | `update_field` | Modify field properties | "Rename the 'score' field to 'lead_score'" |

### Record Operations

| Operation | Tool Name | Description | Example |
|---|---|---|---|
| List records | `list_records` | Get records from a table | "Show me all records in the content calendar" |
| Get record | `get_record` | Get a specific record by ID | "Get record rec123 from the leads table" |
| Create record | `create_record` | Add a new record | "Add a new content item: blog post about dental marketing" |
| Update record | `update_record` | Modify a record | "Update record rec123: set status to 'published'" |
| Delete record | `delete_record` | Remove a record | "Delete record rec123 from the drafts table" |
| Search records | `search_records` | Find records by field value | "Find all records where industry is 'dental'" |

---

## Current Bases and Tables

### Auditing Your Existing Data

To understand what data you already have in Airtable, run through this checklist:

```
Step 1: "List all my Airtable bases"
  -> Note each base name and ID

Step 2: For each base: "List all tables in base [base_id]"
  -> Note table names and field structures

Step 3: For key tables: "List records in [base_id] / [table_name] (limit 5)"
  -> Understand the data format and content
```

### Expected Bases (Based on Your Ecosystem)

You likely have bases for some or all of these purposes:

| Base | Expected Tables | Purpose |
|---|---|---|
| Project Management | Tasks, Milestones, Resources | Tracking development work |
| Content Management | Content Calendar, Templates, Assets | Marketing content pipeline |
| Client Tracking | Clients, Deliverables, Invoices | Client relationship management |
| Lead Pipeline | Leads, Enrichment Results, Campaigns | Lead tracking (may overlap with GHL) |
| Research | Competitors, Industry Data, Tools | Market intelligence |

---

## Use Cases via OpenClaw

### 1. Content Calendar Management

Airtable is ideal for content calendar because of its grid/kanban views and collaboration features.

**OpenClaw operations:**
- Generate content ideas and create records in the calendar
- Update content status as it progresses (idea -> draft -> review -> published)
- Query upcoming content for scheduling
- Track performance metrics after publishing

**Example interaction:**
```
User: "Create a content plan for next week targeting dental practices"

OpenClaw:
1. Generates 5 content pieces using AI
2. For each piece, calls Airtable MCP:
   create_record(base_id, "Content Calendar", {
     "Title": "5 Ways to Get More Dental Patients Online",
     "Platform": "LinkedIn",
     "Content Type": "Educational",
     "Due Date": "2024-01-08",
     "Status": "Drafted",
     "Industry": "Dental",
     "Draft Copy": "..."
   })
3. Returns: "Created 5 content items in your content calendar"
```

### 2. Client Tracking

Track client status, deliverables, and satisfaction.

**OpenClaw operations:**
- Create new client records when deals close
- Update deliverable status
- Generate client reports from Airtable data
- Track client satisfaction and renewal dates

### 3. Project Management

Track OpenClaw development tasks and milestones.

**OpenClaw operations:**
- Create tasks from development sessions
- Update task status (in progress, complete, blocked)
- Query upcoming milestones
- Generate progress reports

### 4. Lead Pipeline Tracking (Interim Before Supabase)

Before Supabase is reactivated, Airtable can serve as interim lead storage.

**OpenClaw operations:**
- Store enriched lead data
- Track lead status through the pipeline
- Search for leads by industry, score, status
- Generate lead reports

**Airtable as interim lead storage:**
```python
# Store enriched lead in Airtable
await airtable_mcp.create_record(
    base_id=LEADS_BASE_ID,
    table_name="Leads",
    fields={
        "Company Name": lead["company_name"],
        "Email": lead["email"],
        "Phone": lead["phone"],
        "Industry": lead["industry"],
        "Lead Score": lead["lead_score"],
        "Score Tier": lead["score_tier"],
        "Pain Signals": ", ".join(lead["pain_signals"]),
        "Status": "New",
        "GHL Contact ID": lead["ghl_contact_id"],
        "Enrichment Date": datetime.now().isoformat(),
    }
)
```

**Limitation:** Airtable is not ideal for large-scale lead storage (rate limits, query limitations, cost at scale). Migrate to Supabase when ready.

---

## Configuration

### AIRTABLE_API_KEY (Already Set)

Your API key is already configured as an environment variable. No action needed.

**If you need to regenerate:**
1. Go to [https://airtable.com/create/tokens](https://airtable.com/create/tokens)
2. Create a new personal access token
3. Scopes needed: `data.records:read`, `data.records:write`, `schema.bases:read`, `schema.bases:write`
4. Update environment variable: `export AIRTABLE_API_KEY="pat_xxx"`

### Rate Limits

| Limit | Value | Notes |
|---|---|---|
| API calls per second | 5 per base | Shared across all API keys |
| Records per request | 100 (list), 10 (create/update) | Pagination required for large tables |
| Records per table | 100,000 (Pro), 50,000 (Team) | Check your plan |
| Attachment size | 5 MB per file | For content assets |

**Rate limit handling:** The Airtable MCP server should handle rate limiting internally. If you hit limits, add delays between operations or batch requests.

---

## Testing Checklist

After configuring in OpenClaw, verify each operation:

- [ ] `list_bases` - Returns your bases
- [ ] `list_tables` - Returns tables for a specific base
- [ ] `create_record` - Creates a test record
- [ ] `search_records` - Finds the test record
- [ ] `update_record` - Modifies the test record
- [ ] `delete_record` - Removes the test record
- [ ] `create_table` - Creates a new test table (if needed)
- [ ] `create_field` - Adds a field to a table

---

## Airtable vs Supabase: When to Use Which

| Scenario | Airtable | Supabase |
|---|---|---|
| Content calendar | Best (visual UI, collaboration) | Possible but overkill |
| Client tracking | Good (spreadsheet-like) | Good (relational queries) |
| Lead storage (< 1000) | Fine (quick, visual) | Fine |
| Lead storage (> 1000) | Slow, expensive | Much better (PostgreSQL) |
| RAG documents | Not suitable | Required (pgvector) |
| Audit logs | Possible but clunky | Better (SQL queries, indexes) |
| Real-time events | Not supported | Supabase Realtime |
| Complex queries | Limited (formula fields) | Full SQL power |
| Collaboration | Excellent (sharing, views) | Limited (dashboard only) |

**Strategy:** Use Airtable for human-facing data (content calendar, client tracking, project management). Use Supabase for machine-facing data (leads at scale, RAG, audit logs, analytics).

---

## RESEARCH GAPS

- [ ] Audit existing Airtable bases and tables to understand current data
- [ ] Determine if a content calendar table already exists or needs creation
- [ ] Check Airtable plan limits (records per table, API rate)
- [ ] Test MCP operations through OpenClaw (not just Claude Code)
- [ ] Design content calendar table schema if it does not exist yet

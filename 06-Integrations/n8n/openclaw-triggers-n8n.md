# OpenClaw Triggers n8n Workflows

> Pattern: OpenClaw agent decides to run an n8n workflow as part of a task.

---

## Overview

This is the most common integration pattern: OpenClaw is working on a task (e.g., enriching a lead, generating a report) and needs n8n to execute a specific workflow as one step in the process.

```
User asks OpenClaw to do something
  -> OpenClaw plans the execution
  -> OpenClaw identifies that an n8n workflow is needed
  -> OpenClaw triggers the n8n workflow with data
  -> n8n executes (possibly calling external APIs)
  -> Results returned to OpenClaw
  -> OpenClaw continues with the results
```

---

## Three Methods for Triggering n8n

### Method 1: Webhook Trigger (Simplest)

OpenClaw sends an HTTP POST to an n8n webhook URL. The n8n workflow has a Webhook trigger node as its entry point.

**n8n workflow setup:**
1. Create workflow with **Webhook** trigger node
2. Set webhook path (e.g., `/webhook/enrich-lead`)
3. Add processing nodes
4. End with a **Respond to Webhook** node (returns data to caller)

**OpenClaw calls it:**
```python
async def trigger_n8n_webhook(webhook_path: str, payload: dict) -> dict:
    """Trigger n8n workflow via webhook and wait for response."""
    n8n_base_url = os.environ.get("N8N_API_URL", "http://localhost:5678")
    webhook_url = f"{n8n_base_url}/webhook/{webhook_path}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
```

**Example: Trigger lead enrichment**
```python
result = await trigger_n8n_webhook("enrich-lead", {
    "domain": "smithdental.com",
    "company_name": "Smith Family Dental",
    "phone": "+15125551234",
    "category": "dentist",
    "city": "Austin",
    "state": "TX"
})
# result = {"enriched_data": {...}, "score": 75, "tier": "warm"}
```

**Pros:**
- Simple to implement
- n8n workflow is self-contained
- Synchronous: OpenClaw waits for the response
- No API key needed for webhook endpoints (though you should add auth)

**Cons:**
- Webhook URL must be discoverable (hardcoded or configured)
- Timeout risk for long-running workflows
- Must create a Webhook trigger node in every workflow

### Method 2: n8n REST API (Most Flexible)

OpenClaw uses the n8n API to execute any workflow by its ID, without requiring a Webhook trigger node.

**API endpoint:**
```
POST /api/v1/workflows/{workflowId}/execute
```

**OpenClaw calls it:**
```python
async def execute_n8n_workflow(workflow_id: str, input_data: dict = None) -> dict:
    """Execute an n8n workflow via REST API."""
    n8n_url = os.environ.get("N8N_API_URL", "http://localhost:5678")
    n8n_api_key = os.environ.get("N8N_API_KEY")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{n8n_url}/api/v1/workflows/{workflow_id}/execute",
            headers={
                "X-N8N-API-KEY": n8n_api_key,
                "Content-Type": "application/json"
            },
            json={"data": input_data or {}}
        )
        response.raise_for_status()
        return response.json()
```

**Example:**
```python
# Trigger workflow #5 (Lead Enrichment Pipeline)
result = await execute_n8n_workflow("5", {
    "domain": "smithdental.com",
    "enrichment_level": "full"
})
```

**Pros:**
- Can trigger ANY workflow (not just those with Webhook triggers)
- Supports passing input data
- API key provides security
- Can query execution status afterward

**Cons:**
- Requires knowing the workflow ID
- Requires n8n API key
- May not return results synchronously (depends on n8n version)

### Method 3: MCP Tool Call (Most Integrated)

OpenClaw uses the n8n MCP server to call an `execute_workflow` tool. This is the most natural integration since OpenClaw already uses MCP for everything.

**OpenClaw skill definition:**
```python
# In an OpenClaw skill, the agent naturally calls the n8n MCP tool:
# "I need to enrich this lead. Let me call the n8n execute_workflow tool."

# The MCP server translates this to an API call internally.
# OpenClaw sees it as just another tool call.
```

**How the agent uses it:**
```
Agent thinking: "I need to run the enrichment workflow in n8n for smithdental.com"
Agent action: Call tool "execute_workflow" with:
  - workflow_id: "5"
  - data: {"domain": "smithdental.com"}
Agent receives: workflow execution result
Agent continues: "The enrichment returned a score of 75, which is Warm tier..."
```

**Pros:**
- Most natural integration (just another tool call for the agent)
- MCP handles serialization, error wrapping, retries
- No HTTP client code needed in skills
- Consistent with how OpenClaw uses all other tools

**Cons:**
- Depends on MCP server being reliable
- May have limitations on what the MCP server exposes
- Less control over timeouts and retry behavior

---

## Passing Data to n8n

### Input Data Format

n8n workflows receive data differently depending on the trigger type:

**Webhook trigger:**
```json
{
  "body": {
    "domain": "smithdental.com",
    "company_name": "Smith Family Dental"
  },
  "headers": { ... },
  "params": { ... }
}
```
Access in n8n nodes: `{{ $json.body.domain }}`

**API execution:**
```json
{
  "data": {
    "domain": "smithdental.com",
    "company_name": "Smith Family Dental"
  }
}
```
Access in n8n nodes: `{{ $execution.customData.domain }}` or `{{ $json.domain }}`

### Complex Data

For enrichment workflows that need multiple data points:

```python
payload = {
    "lead": {
        "domain": "smithdental.com",
        "company_name": "Smith Family Dental",
        "phone": "+15125551234",
        "google_place_id": "ChIJ...",
        "category": "dentist",
    },
    "enrichment_config": {
        "stages": ["tech_stack", "contact_finding", "email_validation"],
        "skip_seo": True,  # Cost optimization: skip expensive SEO enrichment
        "max_credits": 10,
    },
    "callback_url": "http://localhost:8080/webhook/enrichment-complete",  # Optional
}
```

---

## Synchronous vs Asynchronous Execution

### Synchronous (Wait for Completion)

Use when OpenClaw needs the result to continue its work.

```python
async def enrich_lead_sync(lead_data: dict) -> dict:
    """Trigger enrichment and wait for result."""
    try:
        result = await trigger_n8n_webhook("enrich-lead", lead_data)
        return {"status": "success", "data": result}
    except httpx.TimeoutException:
        return {"status": "timeout", "data": None}
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": str(e)}
```

**Timeout strategy:**
- Simple workflows (data transformation, lookups): 30-second timeout
- Medium workflows (API calls, enrichment): 120-second timeout
- Complex workflows (multi-step enrichment, scraping): 300-second timeout

### Asynchronous (Fire and Forget)

Use when OpenClaw does not need the result immediately.

```python
async def trigger_and_forget(workflow_id: str, data: dict):
    """Trigger workflow without waiting for result."""
    # Method A: Fire and forget via API
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{N8N_URL}/api/v1/workflows/{workflow_id}/execute",
            headers={"X-N8N-API-KEY": N8N_API_KEY},
            json={"data": data}
        )

    # When the workflow completes, it will:
    # 1. Write results to Supabase (triggering Realtime event)
    # 2. OR call an OpenClaw webhook endpoint
    # 3. OR update an Airtable record
```

**When to use async:**
- Batch processing (enriching 100 leads - do not wait for each one)
- Scheduled tasks (daily reports - no one is waiting)
- Long-running operations (competitor analysis that takes 10+ minutes)
- When results are written to a shared data store (Supabase, Airtable)

---

## Example: OpenClaw -> n8n "Enrich Lead" Workflow

### Full Flow

```python
async def openclaw_enrich_lead(lead_data: dict) -> dict:
    """
    OpenClaw skill: Enrich a lead using n8n + Clay pipeline.

    1. Send lead data to n8n enrichment workflow
    2. n8n calls Clay API for each enrichment stage
    3. n8n returns enriched data
    4. OpenClaw scores the lead
    5. OpenClaw creates/updates GHL contact
    """

    # Step 1: Trigger n8n enrichment
    enriched = await trigger_n8n_webhook("enrich-lead", {
        "domain": lead_data["website"],
        "company_name": lead_data["company_name"],
        "phone": lead_data.get("phone"),
        "category": lead_data.get("industry"),
    })

    if not enriched or enriched.get("status") == "error":
        return {"status": "enrichment_failed", "error": enriched.get("error")}

    # Step 2: Score the lead locally (faster than doing it in n8n)
    score_result = calculate_lead_score(enriched["data"])

    # Step 3: Build GHL contact
    ghl_contact = build_ghl_contact_from_enrichment(enriched["data"])
    ghl_contact["customFields"]["lead_score"] = score_result["score"]
    ghl_contact["tags"] = build_tags(score_result)

    # Step 4: Create in GHL via MCP
    ghl_result = await ghl_mcp.create_contact(ghl_contact)

    # Step 5: Store in Supabase for persistence
    await supabase.table("leads").insert({
        **lead_data,
        "enrichment_data": enriched["data"],
        "lead_score": score_result["score"],
        "score_tier": score_result["tier"],
        "pain_signals": score_result["signals"],
        "ghl_contact_id": ghl_result["id"],
        "status": "enriched",
        "enriched_at": datetime.utcnow().isoformat(),
    }).execute()

    return {
        "status": "success",
        "score": score_result["score"],
        "tier": score_result["tier"],
        "ghl_contact_id": ghl_result["id"],
        "pain_signals": score_result["signals"],
    }
```

---

## Error Handling

### Timeout Handling

```python
async def trigger_with_retry(webhook_path: str, payload: dict,
                              max_retries: int = 3, timeout: int = 120) -> dict:
    """Trigger n8n with retry logic."""
    for attempt in range(max_retries):
        try:
            return await trigger_n8n_webhook(webhook_path, payload)
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                await asyncio.sleep(wait_time)
                continue
            return {"status": "timeout", "attempts": max_retries}
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                # Server error, retry
                await asyncio.sleep(2 ** attempt)
                continue
            # Client error, do not retry
            return {"status": "error", "code": e.response.status_code, "detail": str(e)}
    return {"status": "max_retries_exceeded"}
```

### Workflow Failure Detection

```python
async def check_execution_status(execution_id: str) -> dict:
    """Check if a workflow execution succeeded or failed."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{N8N_URL}/api/v1/executions/{execution_id}",
            headers={"X-N8N-API-KEY": N8N_API_KEY}
        )
        execution = response.json()

    return {
        "id": execution["id"],
        "status": execution.get("status"),  # "success", "error", "running"
        "finished": execution.get("finished"),
        "error_message": execution.get("data", {}).get("error", {}).get("message"),
    }
```

---

## Monitoring

### Check Recent Executions

```python
async def get_recent_executions(workflow_id: str = None, limit: int = 10) -> list:
    """Get recent workflow executions for monitoring."""
    params = {"limit": limit}
    if workflow_id:
        params["workflowId"] = workflow_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{N8N_URL}/api/v1/executions",
            headers={"X-N8N-API-KEY": N8N_API_KEY},
            params=params,
        )
        return response.json().get("data", [])
```

### Health Check

```python
async def n8n_health_check() -> dict:
    """Check if n8n is running and responsive."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{N8N_URL}/api/v1/workflows",
                headers={"X-N8N-API-KEY": N8N_API_KEY}
            )
            workflows = response.json()
            return {
                "status": "healthy",
                "workflow_count": len(workflows.get("data", [])),
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## RESEARCH GAPS

- [ ] Verify n8n API execution endpoint returns results synchronously vs async
- [ ] Test webhook vs API execution performance difference
- [ ] Determine maximum payload size for n8n webhooks
- [ ] Check n8n execution timeout configuration in your Docker setup
- [ ] Verify MCP tool call maps correctly to n8n API execution
- [ ] Test concurrent workflow executions from OpenClaw

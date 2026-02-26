# n8n Triggers OpenClaw

> Pattern: n8n workflow detects an event and triggers an OpenClaw skill or action.

---

## Overview

This is the reverse integration pattern: n8n is running scheduled jobs, monitoring webhooks, or processing data streams, and it needs OpenClaw to perform an intelligent action (analyze, generate, decide).

```
External event (webhook, schedule, email, database change)
  -> n8n workflow receives the event
  -> n8n pre-processes the data
  -> n8n sends request to OpenClaw
  -> OpenClaw executes a skill (AI analysis, content generation, etc.)
  -> OpenClaw returns result to n8n
  -> n8n takes the next action (send email, update CRM, post content)
```

---

## Three Methods for n8n to Trigger OpenClaw

### Method 1: HTTP Request Node (Most Common)

n8n's HTTP Request node calls OpenClaw's API endpoint.

**n8n workflow setup:**
1. Trigger node (webhook, cron, database trigger, etc.)
2. Processing nodes (transform data, filter, prepare payload)
3. **HTTP Request node** -> OpenClaw API endpoint
4. Post-processing nodes (handle response, update CRM, send notification)

**HTTP Request node configuration:**
```json
{
  "node": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://localhost:8080/api/v1/skills/execute",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer {{ $env.OPENCLAW_API_KEY }}"
        },
        {
          "name": "Content-Type",
          "value": "application/json"
        }
      ]
    },
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "skill",
          "value": "analyze-lead"
        },
        {
          "name": "input",
          "value": "={{ JSON.stringify($json) }}"
        }
      ]
    },
    "options": {
      "timeout": 120000
    }
  }
}
```

### Method 2: WebSocket Node (For Real-Time Communication)

If OpenClaw supports WebSocket connections, n8n can send messages through a persistent connection.

```json
{
  "node": "n8n-nodes-base.websocket",
  "parameters": {
    "url": "ws://localhost:8080/ws",
    "message": "={{ JSON.stringify({skill: 'analyze-lead', data: $json}) }}"
  }
}
```

**When to use WebSocket:**
- High-frequency triggers (multiple events per second)
- When persistent connection reduces overhead
- When you need bidirectional real-time communication

**Note:** WebSocket support depends on OpenClaw having a WebSocket server endpoint. This may not be available initially; start with HTTP Request.

### Method 3: Webhook Relay (For External Events)

n8n receives a webhook from an external service and relays it to OpenClaw. This is critical for services that cannot reach OpenClaw directly (because it runs locally).

```
External Service (GHL, Clay, Stripe, etc.)
  -> Sends webhook to n8n (publicly accessible)
  -> n8n receives and validates
  -> n8n forwards to OpenClaw (local network)
  -> OpenClaw processes
  -> OpenClaw response -> n8n -> back to external service (if needed)
```

**Relay workflow in n8n:**
```
[Webhook Node] -> [Switch Node (route by event type)] -> [HTTP Request to OpenClaw] -> [Respond to Webhook]
```

---

## Use Cases

### Use Case 1: Form Submission -> Lead Processing

```
Prospect fills out form on GHL landing page
  -> GHL fires webhook to n8n
  -> n8n receives form data
  -> n8n calls OpenClaw: "Process this new lead"
  -> OpenClaw:
    1. Enriches the lead via Clay
    2. Scores the lead
    3. Creates GHL contact with enriched data
    4. Determines appropriate pipeline stage
    5. Returns result
  -> n8n receives result
  -> n8n sends confirmation email to prospect
  -> n8n notifies sales rep if Hot lead
```

**n8n workflow design:**
```
[Webhook Trigger: /webhook/ghl-form]
  -> [Set Node: Extract form fields]
  -> [HTTP Request: POST to OpenClaw /api/v1/skills/execute]
     Body: {"skill": "process-new-lead", "input": {"name": "{{$json.name}}", ...}}
  -> [IF Node: Check if lead is Hot]
     -> True: [Slack Node: Alert sales rep]
     -> False: [No operation]
  -> [HTTP Request: Send confirmation email via GHL]
```

### Use Case 2: Scheduled Job -> Daily Report

```
n8n cron trigger fires at 8:00 AM every weekday
  -> n8n calls OpenClaw: "Generate daily pipeline report"
  -> OpenClaw:
    1. Queries GHL for pipeline status
    2. Queries Airtable for content calendar status
    3. Queries Supabase for enrichment stats
    4. Generates natural language summary
    5. Returns formatted report
  -> n8n receives report
  -> n8n formats as email
  -> n8n sends to team distribution list
```

**n8n workflow design:**
```
[Cron Trigger: weekdays 8:00 AM]
  -> [HTTP Request: POST to OpenClaw /api/v1/skills/execute]
     Body: {"skill": "daily-pipeline-report", "input": {"date": "today"}}
  -> [Set Node: Format email HTML]
  -> [Email Node: Send to team@company.com]
```

### Use Case 3: Email Monitor -> AI Analysis

```
n8n IMAP trigger detects new email in inbox
  -> n8n extracts email content
  -> n8n calls OpenClaw: "Analyze this email"
  -> OpenClaw:
    1. Classifies email (lead inquiry, support, spam, vendor, etc.)
    2. Extracts key information (company name, needs, urgency)
    3. Determines appropriate response
    4. Drafts a response if it's a lead inquiry
    5. Returns classification + draft response
  -> n8n receives analysis
  -> n8n routes based on classification:
    - Lead inquiry: Create GHL contact, send draft response for review
    - Support request: Create support ticket
    - Spam: Archive
```

### Use Case 4: Competitor Monitoring -> Alert

```
n8n scheduled workflow (weekly)
  -> n8n scrapes competitor websites / checks Google rankings
  -> n8n calls OpenClaw: "Analyze these competitor changes"
  -> OpenClaw:
    1. Compares new data with previous snapshots
    2. Identifies significant changes
    3. Generates analysis report
    4. Suggests strategic responses
    5. Returns report
  -> n8n stores new snapshot in Supabase
  -> n8n formats report
  -> n8n sends to team via Slack/email
```

### Use Case 5: Social Listening -> Content Suggestion

```
n8n RSS/webhook monitors industry news feeds
  -> New article/trend detected
  -> n8n calls OpenClaw: "Should we create content about this?"
  -> OpenClaw:
    1. Analyzes the trending topic
    2. Checks if it's relevant to target industries
    3. If relevant, generates content brief
    4. Suggests platform, format, and angle
    5. Returns content brief or "skip" recommendation
  -> If content suggested:
    -> n8n creates Airtable record in content calendar
    -> n8n notifies content team
```

---

## OpenClaw API Endpoint Design

For n8n to call OpenClaw, OpenClaw needs an API endpoint. Here is the recommended design:

### Endpoint: POST /api/v1/skills/execute

```python
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

app = FastAPI()

class SkillRequest(BaseModel):
    skill: str              # Skill name to execute
    input: dict             # Input data for the skill
    timeout: int = 120      # Max execution time in seconds
    async_mode: bool = False  # If True, return immediately with execution ID

class SkillResponse(BaseModel):
    status: str             # "success", "error", "timeout"
    execution_id: str       # For tracking
    result: dict | None     # Skill output
    duration_ms: int        # Execution time
    error: str | None       # Error message if failed

@app.post("/api/v1/skills/execute", response_model=SkillResponse)
async def execute_skill(request: SkillRequest):
    """Execute an OpenClaw skill. Called by n8n or other automation tools."""

    # Validate skill exists
    skill = skill_registry.get(request.skill)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{request.skill}' not found")

    # Execute
    start_time = time.time()
    try:
        if request.async_mode:
            execution_id = await skill.execute_async(request.input)
            return SkillResponse(
                status="accepted",
                execution_id=execution_id,
                result=None,
                duration_ms=0,
                error=None
            )
        else:
            result = await asyncio.wait_for(
                skill.execute(request.input),
                timeout=request.timeout
            )
            duration = int((time.time() - start_time) * 1000)
            return SkillResponse(
                status="success",
                execution_id=str(uuid4()),
                result=result,
                duration_ms=duration,
                error=None
            )
    except asyncio.TimeoutError:
        return SkillResponse(
            status="timeout",
            execution_id=str(uuid4()),
            result=None,
            duration_ms=request.timeout * 1000,
            error=f"Skill execution timed out after {request.timeout}s"
        )
    except Exception as e:
        return SkillResponse(
            status="error",
            execution_id=str(uuid4()),
            result=None,
            duration_ms=int((time.time() - start_time) * 1000),
            error=str(e)
        )
```

### Endpoint: GET /api/v1/skills/execute/{execution_id}

For async mode, n8n can poll for results:

```python
@app.get("/api/v1/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get the status and result of an async skill execution."""
    execution = await execution_store.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404)
    return execution
```

---

## Authentication: Securing the OpenClaw API

n8n must authenticate when calling OpenClaw to prevent unauthorized access.

### API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="Authorization")

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify the API key from the Authorization header."""
    expected_key = f"Bearer {os.environ.get('OPENCLAW_API_KEY')}"
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.post("/api/v1/skills/execute")
async def execute_skill(request: SkillRequest, _=Security(verify_api_key)):
    # ... skill execution logic
```

**n8n configuration:**
- Store `OPENCLAW_API_KEY` as an n8n credential
- Reference in HTTP Request node: `Authorization: Bearer {{ $credentials.openclaw.apiKey }}`

### Network-Level Security

Since both n8n and OpenClaw run locally:
- API is only accessible on `localhost` or Tailscale network
- No public exposure needed
- Firewall rules can restrict access to known IPs

---

## Payload Format: How to Structure Messages for OpenClaw

### Standard Payload Structure

```json
{
  "skill": "analyze-lead",
  "input": {
    "lead": {
      "company_name": "Smith Family Dental",
      "domain": "smithdental.com",
      "category": "dentist",
      "city": "Austin",
      "state": "TX"
    },
    "options": {
      "enrichment_level": "full",
      "include_competitors": true,
      "max_credits": 15
    }
  },
  "context": {
    "trigger": "n8n",
    "workflow_id": "5",
    "execution_id": "abc123",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Response Handling in n8n

**Success path:**
```
[HTTP Request Node] -> response.status = "success"
  -> [Set Node: Extract result data]
  -> [Continue workflow with result]
```

**Error path:**
```
[HTTP Request Node] -> response.status = "error"
  -> [IF Node: Check error type]
  -> [Error handling: retry, log, alert]
```

**n8n error handling:**
```json
{
  "node": "n8n-nodes-base.httpRequest",
  "continueOnFail": true,
  "parameters": {
    "options": {
      "timeout": 120000,
      "retry": {
        "enabled": true,
        "maxRetries": 3,
        "retryInterval": 5000
      }
    }
  }
}
```

---

## Response Handling: What n8n Does with OpenClaw's Response

### Pattern A: Direct Action

OpenClaw returns a specific action, n8n executes it:

```json
// OpenClaw response
{
  "status": "success",
  "result": {
    "action": "create_contact",
    "contact_data": { "firstName": "John", "email": "john@smithdental.com", ... },
    "pipeline_stage": "New Lead",
    "tags": ["score:hot", "industry:dental"]
  }
}
```

n8n takes the response and creates the GHL contact, sets the pipeline stage, and adds tags.

### Pattern B: Content Pass-Through

OpenClaw generates content, n8n publishes it:

```json
// OpenClaw response
{
  "status": "success",
  "result": {
    "content": "5 Ways to Attract New Dental Patients...",
    "platform": "linkedin",
    "hashtags": ["#dentalmarketing", "#localbusiness"],
    "recommended_post_time": "2024-01-02T10:00:00Z"
  }
}
```

n8n schedules the post via Buffer/LinkedIn API at the recommended time.

### Pattern C: Decision Routing

OpenClaw makes a decision, n8n routes accordingly:

```json
// OpenClaw response
{
  "status": "success",
  "result": {
    "classification": "hot_lead",
    "confidence": 0.92,
    "recommended_action": "immediate_call",
    "talking_points": ["Website needs redesign", "No Google reviews", "Competitor doing ads"],
    "draft_email": "Hi John, I noticed..."
  }
}
```

n8n routes the lead based on classification: Hot -> Slack alert, Warm -> email sequence, Cold -> drip campaign.

---

## RESEARCH GAPS

- [ ] Design and implement the OpenClaw API endpoint (FastAPI gateway)
- [ ] Determine if OpenClaw will run as a persistent daemon (always listening) or on-demand
- [ ] Test latency of n8n -> OpenClaw -> n8n round trip
- [ ] Define the complete list of skills that n8n should be able to trigger
- [ ] Build n8n credential type for OpenClaw API key
- [ ] Create n8n workflow templates for each use case above

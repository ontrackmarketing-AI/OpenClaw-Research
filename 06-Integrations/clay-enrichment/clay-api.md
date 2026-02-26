# Clay.com API Integration

> Connecting Clay's enrichment platform to OpenClaw for automated lead data enrichment.

---

## Clay.com API Overview

Clay is a data enrichment platform that provides access to 75+ data providers through a single API. Instead of managing individual API keys for Apollo, Clearbit, Hunter, ZeroBounce, BuiltWith, and others, Clay acts as a unified enrichment layer with waterfall logic built in.

**Base URL:** `https://api.clay.com/v1` (verify current URL from Clay docs)
**Authentication:** Bearer token (API key)
**Format:** JSON REST API
**Rate limits:** Vary by plan; typically 100-500 requests/minute

---

## Authentication

### Getting Your API Key

1. Log into Clay.com dashboard
2. Navigate to **Settings** > **API** (or **Integrations** > **API Access**)
3. Generate a new API key
4. Store securely as environment variable: `CLAY_API_KEY`

### Usage in OpenClaw

```python
import httpx

class ClayClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.clay.com/v1"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,  # Clay enrichments can be slow
        )
```

---

## Core API Operations

### 1. Table Management

Clay organizes data into tables. Each enrichment campaign lives in a table.

```python
async def create_table(self, name: str, columns: list[dict]) -> dict:
    """Create a new Clay table for an enrichment campaign."""
    response = await self.client.post(
        f"{self.base_url}/tables",
        json={
            "name": name,
            "columns": columns,  # e.g., [{"name": "Company Domain", "type": "text"}]
        }
    )
    return response.json()
    # Returns: {"id": "tbl_abc123", "name": "Q1 HVAC Leads", ...}

async def list_tables(self) -> list[dict]:
    """List all tables in the workspace."""
    response = await self.client.get(f"{self.base_url}/tables")
    return response.json()["tables"]

async def get_table(self, table_id: str) -> dict:
    """Get table details including columns and row count."""
    response = await self.client.get(f"{self.base_url}/tables/{table_id}")
    return response.json()
```

### 2. Row Operations

Rows are individual records (leads/companies) in a table.

```python
async def add_row(self, table_id: str, data: dict) -> dict:
    """Add a single row to a Clay table."""
    response = await self.client.post(
        f"{self.base_url}/tables/{table_id}/rows",
        json={"data": data}
    )
    return response.json()
    # Returns: {"id": "row_xyz789", "data": {...}, "status": "pending"}

async def add_rows_bulk(self, table_id: str, rows: list[dict]) -> dict:
    """Add multiple rows at once (more efficient for batch imports)."""
    response = await self.client.post(
        f"{self.base_url}/tables/{table_id}/rows/bulk",
        json={"rows": [{"data": row} for row in rows]}
    )
    return response.json()
    # Returns: {"created": 50, "errors": []}

async def get_row(self, table_id: str, row_id: str) -> dict:
    """Get a single row with all enrichment data."""
    response = await self.client.get(
        f"{self.base_url}/tables/{table_id}/rows/{row_id}"
    )
    return response.json()

async def get_rows(self, table_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    """Get rows from a table with pagination."""
    response = await self.client.get(
        f"{self.base_url}/tables/{table_id}/rows",
        params={"limit": limit, "offset": offset}
    )
    return response.json()["rows"]
```

### 3. Enrichment Triggers

Trigger Clay's enrichment columns on specific rows.

```python
async def trigger_enrichment(self, table_id: str, row_id: str, column_id: str = None) -> dict:
    """Trigger enrichment for a specific row (all columns or specific column)."""
    payload = {"rowId": row_id}
    if column_id:
        payload["columnId"] = column_id

    response = await self.client.post(
        f"{self.base_url}/tables/{table_id}/enrich",
        json=payload
    )
    return response.json()
    # Returns: {"status": "enriching", "estimatedCompletion": "2024-01-01T00:00:00Z"}

async def get_enrichment_status(self, table_id: str, row_id: str) -> dict:
    """Check if enrichment is complete for a row."""
    row = await self.get_row(table_id, row_id)
    return {
        "status": row.get("enrichmentStatus", "unknown"),
        "completed_columns": [c for c in row.get("columns", {}) if c.get("status") == "complete"],
        "pending_columns": [c for c in row.get("columns", {}) if c.get("status") == "pending"],
    }
```

### 4. Polling for Enrichment Completion

```python
async def wait_for_enrichment(self, table_id: str, row_id: str,
                                timeout: int = 120, poll_interval: int = 5) -> dict:
    """Poll until enrichment is complete or timeout."""
    import asyncio

    start_time = time.time()
    while time.time() - start_time < timeout:
        status = await self.get_enrichment_status(table_id, row_id)

        if not status["pending_columns"]:
            # All columns complete
            return await self.get_row(table_id, row_id)

        await asyncio.sleep(poll_interval)

    raise TimeoutError(f"Enrichment not complete after {timeout}s for row {row_id}")
```

---

## Waterfall Enrichment

Clay's killer feature: for any data point (e.g., "find email for John Smith at Acme Corp"), Clay automatically tries multiple providers in sequence until one succeeds.

**Example waterfall for email finding:**
1. Apollo.io - Try first (often has direct emails)
2. Hunter.io - Check domain patterns
3. Clearbit - Match by name + company
4. Lusha - Try direct contacts database
5. ContactOut - LinkedIn-sourced data
6. RocketReach - Aggregated sources

**You do not configure the waterfall** - Clay manages provider ordering based on success rates. You simply define the enrichment column type (e.g., "Find Work Email") and Clay handles the rest.

**Waterfall columns available:**
| Column Type | What It Finds | Typical Providers |
|---|---|---|
| Find Work Email | Business email address | Apollo, Hunter, Clearbit, Lusha |
| Find Phone Number | Direct phone number | Apollo, Lusha, ContactOut |
| Company Enrichment | Company details, size, revenue | Clearbit, Apollo, Crunchbase |
| Tech Stack | Technologies used | BuiltWith, Wappalyzer |
| Social Profiles | LinkedIn, Twitter, Facebook | Various social data providers |
| Job Title | Current role and title | Apollo, LinkedIn |
| Catch-All Detection | Is the domain a catch-all? | Specialized providers |

---

## Rate Limits and Usage Quotas

| Plan | API Calls/min | Credits/month | Tables | Rows/table |
|---|---|---|---|---|
| Starter | ~60 | 5,000 | 10 | 10,000 |
| Explorer | ~100 | 25,000 | 50 | 50,000 |
| Pro | ~300 | 100,000 | Unlimited | 100,000 |
| Enterprise | Custom | Custom | Unlimited | Unlimited |

**Handling rate limits in OpenClaw:**
```python
async def _make_request(self, method: str, url: str, **kwargs) -> dict:
    """Make API request with rate limit handling."""
    response = await self.client.request(method, url, **kwargs)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))
        logger.warning(f"Clay rate limited. Retrying in {retry_after}s")
        await asyncio.sleep(retry_after)
        response = await self.client.request(method, url, **kwargs)

    response.raise_for_status()
    return response.json()
```

---

## Credit System

Clay uses credits for enrichment. Each enrichment type has a different credit cost.

| Enrichment Type | Approximate Credit Cost | Notes |
|---|---|---|
| Basic company lookup | 1 credit | Company name, domain, industry |
| Email finding (waterfall) | 2-5 credits | Cost depends on how many providers tried |
| Phone finding | 3-5 credits | Often more expensive than email |
| Full company enrichment | 5-10 credits | Complete profile with all fields |
| Tech stack detection | 2-3 credits | BuiltWith/Wappalyzer data |
| Social profile finding | 1-2 credits | LinkedIn, Twitter URLs |

**Credit monitoring:**
```python
async def get_credit_balance(self) -> dict:
    """Check remaining Clay credits."""
    response = await self.client.get(f"{self.base_url}/account/credits")
    return response.json()
    # Returns: {"remaining": 15000, "used": 10000, "total": 25000, "resetDate": "..."}

async def check_credits_before_enrichment(self, estimated_credits: int) -> bool:
    """Verify enough credits before starting enrichment."""
    balance = await self.get_credit_balance()
    if balance["remaining"] < estimated_credits:
        logger.error(f"Insufficient Clay credits: {balance['remaining']} < {estimated_credits}")
        return False
    return True
```

---

## Webhook Callbacks

Clay can notify your endpoint when enrichments complete, avoiding the need to poll.

### Setting Up Webhooks

```python
async def register_webhook(self, table_id: str, webhook_url: str, events: list[str]) -> dict:
    """Register a webhook for enrichment completion events."""
    response = await self.client.post(
        f"{self.base_url}/webhooks",
        json={
            "tableId": table_id,
            "url": webhook_url,
            "events": events,  # e.g., ["row.enrichment.complete", "row.created"]
        }
    )
    return response.json()
```

### Webhook Payload (Expected)

```json
{
  "event": "row.enrichment.complete",
  "tableId": "tbl_abc123",
  "rowId": "row_xyz789",
  "data": {
    "company_name": "Acme Corp",
    "email": "john@acme.com",
    "phone": "+15551234567",
    "employee_count": 50,
    "tech_stack": ["WordPress", "Google Analytics", "Mailchimp"]
  },
  "creditsUsed": 8,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Processing in OpenClaw

```python
@app.post("/webhook/clay")
async def handle_clay_webhook(request: Request):
    """Process Clay enrichment completion webhook."""
    payload = await request.json()

    if payload["event"] == "row.enrichment.complete":
        enriched_data = payload["data"]

        # Map to GHL contact fields
        ghl_contact = map_enrichment_to_ghl(enriched_data)

        # Score the lead
        score = calculate_pain_score(enriched_data)
        ghl_contact["customFields"]["lead_score"] = score

        # Create or update in GHL
        await create_or_update_ghl_contact(ghl_contact)

        # Track credit usage
        await track_credit_usage(payload["creditsUsed"])

    return {"status": "processed"}
```

---

## Python/JS SDK Availability

As of the knowledge cutoff, Clay does not have an official Python or JavaScript SDK. Integration is done via direct REST API calls.

**Recommendation:** Build a lightweight Python wrapper class (as shown above) that encapsulates all needed operations. This becomes your de facto SDK.

**Community alternatives:** Check PyPI for `clay-api` or similar unofficial packages, but verify maintenance status before depending on them.

---

## Integration with OpenClaw: Clay as a Tool

Register Clay operations as tools available to OpenClaw skills:

```python
# In OpenClaw skill definition
CLAY_TOOLS = [
    {
        "name": "clay_enrich_company",
        "description": "Enrich a company using Clay's waterfall enrichment. Input: company domain. Output: enriched company data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Company website domain"},
            },
            "required": ["domain"]
        }
    },
    {
        "name": "clay_find_email",
        "description": "Find the work email for a person at a company. Input: name, company domain. Output: email address.",
        "input_schema": {
            "type": "object",
            "properties": {
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "company_domain": {"type": "string"},
            },
            "required": ["first_name", "last_name", "company_domain"]
        }
    },
    {
        "name": "clay_check_credits",
        "description": "Check remaining Clay enrichment credits.",
        "input_schema": {"type": "object", "properties": {}}
    },
]
```

---

## RESEARCH GAPS

- [ ] **CRITICAL:** Verify Clay API base URL and exact endpoint paths (docs may have changed)
- [ ] Get Clay API key and test basic table/row operations
- [ ] Confirm webhook support and exact event names
- [ ] Determine exact credit costs per enrichment type on your plan
- [ ] Check if Clay supports synchronous enrichment (immediate response) vs async only
- [ ] Verify bulk row import limits and performance
- [ ] Test waterfall enrichment completion times for planning timeout values

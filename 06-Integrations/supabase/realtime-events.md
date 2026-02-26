# Supabase Realtime Events

> Using Supabase Realtime to trigger OpenClaw actions when database records change.

---

## What is Supabase Realtime?

Supabase Realtime is a WebSocket-based system that broadcasts database changes to connected clients in real time. When a row is inserted, updated, or deleted, all subscribed clients receive the change notification instantly.

This enables event-driven architecture: instead of polling the database for changes, OpenClaw listens for events and reacts immediately.

---

## Use Cases for OpenClaw

### 1. New Lead Inserted -> Trigger Enrichment

```
External source inserts lead into `leads` table
  -> Supabase Realtime fires INSERT event
  -> OpenClaw listener receives the event
  -> OpenClaw triggers enrichment pipeline
  -> Enriched data written back to `leads` table
  -> GHL contact created
```

**Why this matters:** Leads can come from multiple sources (n8n scraping, form submissions, manual entry, CSV import). Regardless of source, the enrichment pipeline triggers automatically.

### 2. Contact Updated -> Sync to GHL

```
Contact record updated in Supabase
  -> Realtime fires UPDATE event
  -> OpenClaw listener receives changed fields
  -> OpenClaw pushes changes to GHL via MCP
  -> Sync timestamp updated
```

### 3. Document Added -> Trigger Embedding Generation

```
New document inserted into `documents` table (without embedding)
  -> Realtime fires INSERT event
  -> OpenClaw listener detects empty embedding field
  -> Generates embedding via Ollama/OpenAI
  -> Updates the document record with embedding vector
```

**This decouples document storage from embedding generation.** Anyone (or any tool) can add documents; embeddings are generated asynchronously.

### 4. Competitor Data Changed -> Generate Alert

```
New competitor snapshot inserted into `competitor_data` table
  -> Realtime fires INSERT event
  -> OpenClaw compares new snapshot with previous
  -> If significant changes detected (rating dropped, new competitor appeared):
    -> Generate alert message
    -> Send to Slack/email/Airtable
```

### 5. Lead Score Changed -> Route to Pipeline

```
Lead record updated with new lead_score
  -> Realtime fires UPDATE event with old and new values
  -> OpenClaw checks: did score tier change? (e.g., warm -> hot)
  -> If tier changed: update GHL pipeline stage, create tasks, send alerts
```

---

## Configuration

### Enable Realtime on Specific Tables

In Supabase Dashboard:
1. Go to **Database** > **Replication**
2. Under "Realtime", toggle ON for the tables you want to monitor
3. Select which event types to broadcast: INSERT, UPDATE, DELETE

Or via SQL:

```sql
-- Enable realtime on the leads table
ALTER PUBLICATION supabase_realtime ADD TABLE leads;

-- Enable realtime on the documents table
ALTER PUBLICATION supabase_realtime ADD TABLE documents;

-- Enable realtime on the contacts table
ALTER PUBLICATION supabase_realtime ADD TABLE contacts;

-- Enable realtime on the competitor_data table
ALTER PUBLICATION supabase_realtime ADD TABLE competitor_data;

-- Verify which tables have realtime enabled
SELECT * FROM pg_publication_tables WHERE pubname = 'supabase_realtime';
```

### Tables to Enable Realtime On

| Table | INSERT | UPDATE | DELETE | Reason |
|---|---|---|---|---|
| `leads` | Yes | Yes | No | Trigger enrichment, score routing |
| `contacts` | Yes | Yes | No | GHL sync |
| `documents` | Yes | No | No | Embedding generation |
| `competitor_data` | Yes | No | No | Change alerts |
| `content_calendar` | Yes | Yes | No | Publishing triggers |
| `sessions` | No | No | No | No real-time need |
| `skill_logs` | No | No | No | No real-time need |
| `enrichment_cache` | No | No | No | No real-time need |

---

## Client Setup: Subscribing from OpenClaw

### Python Client (using supabase-py)

```python
from supabase import create_client, Client
import asyncio

supabase: Client = create_client(
    "https://jitawzicdwgbhatvjblh.supabase.co",
    SUPABASE_SERVICE_ROLE_KEY
)

class RealtimeListener:
    """Listen for Supabase Realtime events and dispatch to handlers."""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.handlers = {}

    def register_handler(self, table: str, event: str, handler):
        """Register a handler for a specific table + event combination."""
        key = f"{table}:{event}"
        self.handlers[key] = handler

    async def start(self):
        """Start listening to all registered channels."""

        # Subscribe to leads table
        self.supabase.channel("leads-changes").on(
            "postgres_changes",
            {"event": "INSERT", "schema": "public", "table": "leads"},
            self._on_lead_inserted
        ).on(
            "postgres_changes",
            {"event": "UPDATE", "schema": "public", "table": "leads"},
            self._on_lead_updated
        ).subscribe()

        # Subscribe to documents table
        self.supabase.channel("documents-changes").on(
            "postgres_changes",
            {"event": "INSERT", "schema": "public", "table": "documents"},
            self._on_document_inserted
        ).subscribe()

        # Subscribe to competitor data
        self.supabase.channel("competitor-changes").on(
            "postgres_changes",
            {"event": "INSERT", "schema": "public", "table": "competitor_data"},
            self._on_competitor_data_added
        ).subscribe()

    def _on_lead_inserted(self, payload):
        """Handle new lead insertion."""
        new_record = payload["new"]
        lead_id = new_record["id"]
        print(f"New lead detected: {new_record.get('company_name')} (ID: {lead_id})")

        # Trigger enrichment if not already enriched
        if new_record.get("status") == "new":
            asyncio.create_task(self.trigger_enrichment(lead_id))

    def _on_lead_updated(self, payload):
        """Handle lead record update."""
        old_record = payload["old"]
        new_record = payload["new"]

        # Check if score tier changed
        old_tier = old_record.get("score_tier")
        new_tier = new_record.get("score_tier")
        if old_tier != new_tier and new_tier:
            asyncio.create_task(self.handle_tier_change(
                new_record["id"], old_tier, new_tier
            ))

    def _on_document_inserted(self, payload):
        """Handle new document - generate embedding if missing."""
        new_record = payload["new"]
        if new_record.get("embedding") is None:
            asyncio.create_task(self.generate_embedding(new_record["id"]))

    def _on_competitor_data_added(self, payload):
        """Handle new competitor snapshot."""
        new_record = payload["new"]
        asyncio.create_task(self.analyze_competitor_change(new_record))

    async def trigger_enrichment(self, lead_id: str):
        """Trigger the full enrichment pipeline for a new lead."""
        # Call OpenClaw enrichment skill
        pass  # Implementation in enrichment skill

    async def handle_tier_change(self, lead_id: str, old_tier: str, new_tier: str):
        """Handle lead score tier change - update pipeline routing."""
        pass  # Implementation in pipeline automation

    async def generate_embedding(self, document_id: str):
        """Generate and store embedding for a new document."""
        pass  # Implementation in RAG pipeline

    async def analyze_competitor_change(self, snapshot: dict):
        """Analyze competitor snapshot against previous data."""
        pass  # Implementation in competitor analysis skill
```

---

## Event Types

| Event | Payload Content | Available Fields |
|---|---|---|
| **INSERT** | `payload.new` = full new record | All columns of the inserted row |
| **UPDATE** | `payload.old` = previous values, `payload.new` = updated values | Both old and new column values |
| **DELETE** | `payload.old` = deleted record | All columns of the deleted row |

**Important:** For UPDATE events, `payload.old` only contains primary key columns by default. To get full old record, you must set `REPLICA IDENTITY FULL` on the table:

```sql
-- Enable full old record in UPDATE events
ALTER TABLE leads REPLICA IDENTITY FULL;
ALTER TABLE contacts REPLICA IDENTITY FULL;
```

---

## Filtering: Only Trigger on Specific Conditions

Supabase Realtime supports server-side filtering to reduce noise:

```python
# Only listen for leads with status = 'new'
supabase.channel("new-leads").on(
    "postgres_changes",
    {
        "event": "INSERT",
        "schema": "public",
        "table": "leads",
        "filter": "status=eq.new",
    },
    handle_new_lead
).subscribe()

# Only listen for hot leads
supabase.channel("hot-leads").on(
    "postgres_changes",
    {
        "event": "UPDATE",
        "schema": "public",
        "table": "leads",
        "filter": "score_tier=eq.hot",
    },
    handle_hot_lead
).subscribe()
```

---

## Alternative: n8n as Intermediate

If running a persistent WebSocket listener in OpenClaw is complex, use n8n as the event handler:

```
Supabase Realtime event
  -> n8n "Supabase Trigger" node (listens for changes)
  -> n8n processes the event (filtering, transformation)
  -> n8n "HTTP Request" node calls OpenClaw API
  -> OpenClaw executes the appropriate skill
```

**Advantages of n8n as intermediate:**
- n8n is already running 24/7 in Docker
- n8n has built-in retry and error handling
- n8n can batch events (wait 30 seconds, process all accumulated events)
- n8n can filter events without OpenClaw involvement
- Visual workflow makes event routing transparent

**n8n Supabase trigger configuration:**
```json
{
  "node": "n8n-nodes-base.supabaseTrigger",
  "parameters": {
    "supabaseUrl": "https://jitawzicdwgbhatvjblh.supabase.co",
    "table": "leads",
    "event": "INSERT",
    "conditions": {
      "status": "new"
    }
  }
}
```

---

## Architecture Decision: Direct vs n8n Intermediate

| Factor | Direct Realtime | n8n Intermediate |
|---|---|---|
| Latency | ~100ms | ~500ms-1s |
| Complexity | Must run persistent listener | n8n handles it |
| Reliability | Depends on OpenClaw uptime | n8n has retry logic |
| Filtering | Client-side or Supabase filter | n8n conditional nodes |
| Monitoring | Must build | n8n execution history |
| Scalability | Good | Good |

**Recommendation:** Start with n8n as intermediate (simpler to set up and monitor). Move to direct Realtime connection when OpenClaw has a persistent daemon process.

---

## Implementation Priority

| Use Case | Priority | Route |
|---|---|---|
| New lead -> enrichment | P1 | n8n intermediate |
| Document -> embedding | P1 | n8n intermediate |
| Lead score change -> routing | P2 | n8n intermediate |
| Contact update -> GHL sync | P2 | Direct or n8n |
| Competitor change -> alert | P3 | n8n intermediate |

---

## RESEARCH GAPS

- [ ] Verify Supabase Python client supports Realtime subscriptions (supabase-py v2+)
- [ ] Test Realtime latency between Supabase cloud and your local environment
- [ ] Determine if n8n has a native Supabase Realtime trigger node
- [ ] Test REPLICA IDENTITY FULL performance impact on frequently updated tables
- [ ] Determine maximum concurrent Realtime subscriptions on free tier (listed as 200)
- [ ] Evaluate if Supabase Database Webhooks (separate from Realtime) would be simpler for some use cases

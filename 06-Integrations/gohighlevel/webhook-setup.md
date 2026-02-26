# GoHighLevel Webhook Setup

> Receiving real-time events from GoHighLevel in OpenClaw for event-driven automation.

---

## GHL Webhook Events

GoHighLevel can send webhooks for a wide range of events. The most useful for OpenClaw:

### Contact Events
| Event | Trigger | Use Case |
|---|---|---|
| `ContactCreate` | New contact created in GHL | Trigger enrichment if not already enriched |
| `ContactUpdate` | Contact record modified | Sync changes to OpenClaw memory |
| `ContactDelete` | Contact removed | Clean up related data |
| `ContactDndUpdate` | Do-Not-Disturb status changed | Stop/start automated outreach |
| `ContactTagUpdate` | Tag added or removed | Update segmentation in OpenClaw |

### Opportunity Events
| Event | Trigger | Use Case |
|---|---|---|
| `OpportunityCreate` | New deal created | Initialize pipeline tracking |
| `OpportunityStageUpdate` | Deal moves stages | Trigger stage-specific automations |
| `OpportunityStatusUpdate` | Deal won/lost/abandoned | Update reporting, trigger win/loss workflows |
| `OpportunityMonetaryValueUpdate` | Deal value changed | Update revenue forecasts |

### Appointment Events
| Event | Trigger | Use Case |
|---|---|---|
| `AppointmentCreate` | Appointment booked | Generate meeting prep brief |
| `AppointmentUpdate` | Appointment rescheduled | Update calendar and prep |
| `AppointmentDelete` | Appointment cancelled | Alert sales rep, re-engage |

### Communication Events
| Event | Trigger | Use Case |
|---|---|---|
| `InboundMessage` | Contact sends message (SMS/email/chat) | Analyze sentiment, auto-respond or route |
| `OutboundMessage` | Message sent from GHL | Track outreach activity |
| `NoteCreate` | Note added to contact | Update OpenClaw context |

### Form Events
| Event | Trigger | Use Case |
|---|---|---|
| `FormSubmission` | Form submitted on landing page | Enrich and qualify the new lead |
| `SurveySubmission` | Survey completed | Add responses to contact record |

---

## Webhook URL: OpenClaw Gateway Endpoint

OpenClaw needs a reachable URL for GHL to send webhooks to.

### The Local-First Problem

Your setup runs locally (Tailscale network). GHL webhooks need a publicly reachable URL. Three solutions:

### Option 1: Tailscale Funnel (Recommended for development)

Tailscale Funnel exposes a local port to the internet through Tailscale's infrastructure.

```bash
# Expose OpenClaw webhook listener on port 8080
tailscale funnel 8080

# This gives you a URL like:
# https://your-machine.tailnet-name.ts.net/
```

**Pros:** Simple, secure (HTTPS by default), no external infrastructure
**Cons:** Tied to your machine being on, URL changes if Tailscale config changes
**Best for:** Development and testing

### Option 2: n8n as Webhook Relay (Recommended for production)

Use n8n (which may already have a reachable URL) to receive webhooks and forward to OpenClaw.

```
GHL webhook -> n8n webhook trigger node -> n8n processes/validates -> HTTP Request node -> OpenClaw local endpoint
```

**n8n workflow design:**
1. **Webhook node:** Receives POST from GHL, URL like `https://your-n8n.domain.com/webhook/ghl-events`
2. **Switch node:** Route based on event type (contact, opportunity, appointment, etc.)
3. **HTTP Request node:** Forward processed event to OpenClaw at `http://localhost:PORT/webhook/ghl`
4. **Error handling:** If OpenClaw is down, queue the event for retry

**Pros:** n8n can pre-process, filter, and buffer events. Already running in your stack.
**Cons:** Adds a hop. n8n must be publicly reachable or use its own tunnel.
**Best for:** Production use with event pre-processing.

### Option 3: Cloudflare Tunnel (Recommended for always-on production)

```bash
# Install cloudflared
cloudflared tunnel create openclaw-webhooks
cloudflared tunnel route dns openclaw-webhooks webhooks.yourdomain.com

# Run the tunnel
cloudflared tunnel --config config.yml run openclaw-webhooks
```

**config.yml:**
```yaml
tunnel: openclaw-webhooks
credentials-file: /path/to/credentials.json
ingress:
  - hostname: webhooks.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

**Pros:** Reliable, fast, free, custom domain
**Cons:** Requires Cloudflare account, slight setup overhead
**Best for:** Always-on production webhooks

---

## Webhook Configuration in GHL

### Via GHL Dashboard

1. Log into GoHighLevel
2. Navigate to **Settings** > **Webhooks** (or **Settings** > **Developer** > **Webhooks**)
3. Click **Add Webhook**
4. Enter your webhook URL (from Tailscale Funnel, n8n, or Cloudflare Tunnel)
5. Select the events you want to receive
6. Save

### Via GHL API (Programmatic)

```python
async def register_ghl_webhooks(ghl_adapter, webhook_url: str):
    """Register all needed webhooks in GHL programmatically."""
    events_to_register = [
        "ContactCreate",
        "ContactUpdate",
        "ContactTagUpdate",
        "OpportunityCreate",
        "OpportunityStageUpdate",
        "OpportunityStatusUpdate",
        "AppointmentCreate",
        "InboundMessage",
        "FormSubmission",
    ]

    for event in events_to_register:
        result = await ghl_adapter.create_webhook({
            "url": webhook_url,
            "event": event,
            "active": True,
        })
        print(f"Registered webhook for {event}: {result.get('id')}")
```

---

## Security

### Webhook Signature Verification

GHL may include a signature header for webhook validation. Verify it to prevent spoofed requests.

```python
import hmac
import hashlib

def verify_ghl_webhook(request_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify the GHL webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        request_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature_header, expected_signature)
```

### IP Allowlisting

If your webhook endpoint supports it, restrict incoming requests to GHL's IP ranges. Check GHL documentation for their outbound IP addresses.

### HTTPS Required

Always use HTTPS for webhook endpoints. All three options above (Tailscale Funnel, Cloudflare Tunnel, n8n with TLS) provide HTTPS by default.

### Rate Limiting

Protect your webhook endpoint from floods:
```python
from collections import defaultdict
from time import time

rate_limiter = defaultdict(list)
MAX_REQUESTS_PER_MINUTE = 60

def check_rate_limit(source_ip: str) -> bool:
    """Simple sliding window rate limiter."""
    now = time()
    window = [t for t in rate_limiter[source_ip] if now - t < 60]
    rate_limiter[source_ip] = window
    if len(window) >= MAX_REQUESTS_PER_MINUTE:
        return False
    rate_limiter[source_ip].append(now)
    return True
```

---

## Event Processing

### Webhook Receiver Architecture

```python
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

@app.post("/webhook/ghl")
async def receive_ghl_webhook(request: Request):
    """Main webhook endpoint for GHL events."""
    body = await request.body()
    payload = await request.json()

    # 1. Verify signature
    signature = request.headers.get("X-GHL-Signature", "")
    if not verify_ghl_webhook(body, signature, GHL_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 2. Extract event type
    event_type = payload.get("type") or payload.get("event")

    # 3. Route to handler
    handler = EVENT_HANDLERS.get(event_type)
    if handler:
        await handler(payload)
    else:
        logger.warning(f"Unhandled GHL event type: {event_type}")

    # 4. Always return 200 quickly (process async if needed)
    return {"status": "received"}
```

### Event-to-Action Mapping

```python
EVENT_HANDLERS = {
    "ContactCreate": handle_new_contact,
    "ContactUpdate": handle_contact_update,
    "ContactTagUpdate": handle_tag_change,
    "OpportunityStageUpdate": handle_stage_change,
    "OpportunityStatusUpdate": handle_deal_status,
    "AppointmentCreate": handle_appointment_booked,
    "InboundMessage": handle_inbound_message,
    "FormSubmission": handle_form_submission,
}
```

---

## Example Flows

### Flow 1: Form Submitted -> Enrich -> Create Contact

```
1. Prospect fills out form on GHL landing page
2. GHL fires FormSubmission webhook to OpenClaw
3. OpenClaw receives form data: name, email, phone, business name
4. OpenClaw triggers enrichment skill:
   a. Clay API: enrich company by domain
   b. Clay API: find additional contacts
   c. BuiltWith: detect technology stack
5. OpenClaw runs pain scoring on enriched data
6. If qualified (score >= 40):
   a. Create GHL contact with enriched fields + tags
   b. Place in pipeline at "New Lead"
   c. If Hot (80+): alert sales rep immediately
   d. If Warm/Cold: start appropriate nurture sequence
7. If disqualified (score < 40):
   a. Create contact with tag `score:disqualified`
   b. Add to long-term re-engagement list
```

### Flow 2: Appointment Booked -> Generate Prep Brief

```
1. Prospect books appointment via GHL calendar
2. GHL fires AppointmentCreate webhook to OpenClaw
3. OpenClaw retrieves full contact data from GHL
4. OpenClaw generates meeting prep brief:
   a. Contact summary (name, company, role)
   b. Pain points detected during enrichment
   c. Technology gaps (current stack vs what you offer)
   d. Competitor analysis (who else is marketing to them)
   e. Suggested talking points
   f. Objection preparation
   g. Recommended proposal approach
5. Brief is:
   a. Added as note on GHL contact
   b. Emailed to the assigned sales rep
   c. Stored in Airtable for reference
```

### Flow 3: Contact Replies -> Sentiment Analysis -> Route Response

```
1. Prospect replies to outreach email/SMS
2. GHL fires InboundMessage webhook to OpenClaw
3. OpenClaw analyzes message:
   a. Sentiment: positive, negative, neutral, question
   b. Intent: interested, not interested, asking for info, scheduling
   c. Urgency: high (wants to talk now), medium, low
4. Based on analysis:
   a. Positive + high urgency: Alert sales rep immediately, suggest booking link
   b. Positive + low urgency: Queue for follow-up within 24h
   c. Question: Generate draft response, queue for human review
   d. Negative: Tag as not interested, move to Lost, schedule re-engagement in 90 days
   e. Unsubscribe request: Process DND update, remove from sequences
5. Update contact tags and pipeline stage accordingly
```

---

## Tailscale Funnel Considerations

Since your infrastructure runs on Tailscale, here are specific considerations:

**Setup for webhook receiving:**
```bash
# On your Mac Mini (or wherever OpenClaw runs):
tailscale funnel --bg 8080

# This creates a persistent HTTPS endpoint
# URL format: https://your-hostname.tailnet-xxxx.ts.net:443/
```

**Limitations:**
- Only HTTPS (port 443 externally, maps to your local port)
- Must be enabled per machine in Tailscale ACLs
- One funnel per machine unless you use path-based routing
- Your machine must be running for webhooks to be received

**Path-based routing for multiple services:**
```bash
# OpenClaw webhooks
tailscale funnel /webhook/ghl 8080
# n8n webhooks
tailscale funnel /webhook/n8n 5678
```

**Production recommendation:** Use n8n as the webhook relay. n8n can queue events if OpenClaw is temporarily down, and n8n may already have a more stable endpoint configured.

---

## Testing Webhooks

### Manual Test

```bash
# Send a test webhook to your endpoint
curl -X POST https://your-webhook-url/webhook/ghl \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ContactCreate",
    "contactId": "test123",
    "firstName": "Test",
    "lastName": "User",
    "email": "test@example.com"
  }'
```

### GHL Test Events

GHL dashboard may have a "Test Webhook" button that sends a sample payload.

### Webhook.site

For debugging, temporarily point GHL webhooks to `https://webhook.site/your-unique-id` to inspect the exact payload format before coding handlers.

---

## RESEARCH GAPS

- [ ] Confirm exact webhook event names in GHL API v2 (names above are estimates)
- [ ] Determine if GHL includes a signature header for webhook verification
- [ ] Check if GHL supports webhook retry on failure (and how many times)
- [ ] Test Tailscale Funnel latency for real-time webhook processing
- [ ] Verify GHL webhook payload format for each event type
- [ ] Determine if GHL supports webhook filters (receive only specific events at specific URLs)

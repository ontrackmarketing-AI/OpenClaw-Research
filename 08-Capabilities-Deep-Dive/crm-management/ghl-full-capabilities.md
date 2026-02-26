# GoHighLevel API: Complete Capability Reference for OpenClaw

## Overview

GoHighLevel (GHL) is the core CRM platform for the agency's client management, lead tracking, communications, and pipeline automation. This document provides a comprehensive reference of all GHL API capabilities relevant to OpenClaw integration, identifying which are already implemented in the MCP server and which represent gaps to be filled.

## API Fundamentals

### Authentication

```
Base URL: https://services.leadconnectorhq.com
Auth: Bearer token (API key per location or agency-level)
Headers:
  Authorization: Bearer {api_key}
  Content-Type: application/json
  Version: 2021-07-28  (API version header)
```

### Rate Limits

| Scope | Limit | Window |
|-------|-------|--------|
| Per location | 100 requests | Per minute |
| Bulk operations | 10 requests | Per minute |
| Webhook events | No limit on receiving | N/A |

**Rate limit handling:** Implement exponential backoff with retry. Track request counts per location per minute. Queue requests when approaching limits.

```python
import time
from collections import defaultdict

class GHLRateLimiter:
    def __init__(self, max_per_minute=95):  # leave 5 request buffer
        self.max_per_minute = max_per_minute
        self.request_log = defaultdict(list)

    async def acquire(self, location_id):
        now = time.time()
        # Clean old entries
        self.request_log[location_id] = [
            t for t in self.request_log[location_id] if now - t < 60
        ]
        if len(self.request_log[location_id]) >= self.max_per_minute:
            wait_time = 60 - (now - self.request_log[location_id][0])
            await asyncio.sleep(wait_time)
        self.request_log[location_id].append(time.time())
```

## Contact Management

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Create contact | POST | `/contacts/` | Returns contact ID |
| Get contact | GET | `/contacts/{contactId}` | Full contact object |
| Update contact | PUT | `/contacts/{contactId}` | Partial update supported |
| Delete contact | DELETE | `/contacts/{contactId}` | Permanent deletion |
| Search contacts | GET | `/contacts/search` | By email, phone, name, tags |
| List contacts | GET | `/contacts/` | Paginated, filterable |
| Add tag | POST | `/contacts/{contactId}/tags` | Array of tag names |
| Remove tag | DELETE | `/contacts/{contactId}/tags` | Specific tag removal |
| Add note | POST | `/contacts/{contactId}/notes` | Text notes |
| Get notes | GET | `/contacts/{contactId}/notes` | Paginated |
| Create task | POST | `/contacts/{contactId}/tasks` | With due date, assignee |
| Get tasks | GET | `/contacts/{contactId}/tasks` | Filterable by status |
| Update task | PUT | `/contacts/{contactId}/tasks/{taskId}` | Status, details |
| Set DND | PUT | `/contacts/{contactId}/dnd` | Do Not Disturb settings |

### Custom Fields

```python
# Get all custom fields for a location
GET /locations/{locationId}/customFields

# Custom field types supported:
# - TEXT, LARGE_TEXT, NUMERICAL, PHONE, EMAIL, URL
# - DATE, CHECKBOX, DROPDOWN, RADIO, TEXTAREA
# - MONETARY, FILE_UPLOAD

# Create custom field
POST /locations/{locationId}/customFields
{
    "name": "Pain Score",
    "dataType": "NUMERICAL",
    "placeholder": "0-100"
}

# Set custom field value on contact
PUT /contacts/{contactId}
{
    "customField": {
        "pain_score": 85,
        "enrichment_date": "2026-01-15",
        "website_technology": "WordPress",
        "estimated_revenue": 250000
    }
}
```

### Contact Object Structure

```json
{
    "id": "abc123",
    "locationId": "loc456",
    "firstName": "John",
    "lastName": "Smith",
    "name": "John Smith",
    "email": "john@abcplumbing.com",
    "phone": "+15551234567",
    "companyName": "ABC Plumbing",
    "address1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "postalCode": "78701",
    "website": "https://abcplumbing.com",
    "source": "website_form",
    "tags": ["plumber", "high_value", "needs_seo"],
    "customField": {
        "pain_score": 85,
        "employee_count": "10-25",
        "annual_revenue": "$500K-$1M"
    },
    "dateAdded": "2026-01-15T10:30:00Z",
    "dateUpdated": "2026-01-20T14:15:00Z",
    "dnd": false,
    "assignedTo": "user_789"
}
```

## Opportunities / Pipelines

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get pipelines | GET | `/opportunities/pipelines` | List all pipelines |
| Create opportunity | POST | `/opportunities/` | With pipeline and stage |
| Get opportunity | GET | `/opportunities/{opportunityId}` | Full opportunity object |
| Update opportunity | PUT | `/opportunities/{opportunityId}` | Stage, value, status |
| Delete opportunity | DELETE | `/opportunities/{opportunityId}` | Permanent |
| Search opportunities | GET | `/opportunities/search` | By pipeline, stage, status |

### Pipeline Configuration

```python
# Standard agency pipeline stages:
PIPELINE_STAGES = {
    "new_lead": {"name": "New Lead", "position": 0},
    "qualified": {"name": "Qualified", "position": 1},
    "contacted": {"name": "Contacted", "position": 2},
    "meeting_scheduled": {"name": "Meeting Scheduled", "position": 3},
    "proposal_sent": {"name": "Proposal Sent", "position": 4},
    "negotiation": {"name": "Negotiation", "position": 5},
    "closed_won": {"name": "Closed Won", "position": 6},
    "closed_lost": {"name": "Closed Lost", "position": 7}
}
```

### Opportunity Object

```json
{
    "id": "opp123",
    "name": "ABC Plumbing - SEO Package",
    "monetaryValue": 2500,
    "pipelineId": "pipe456",
    "pipelineStageId": "stage789",
    "status": "open",
    "contactId": "abc123",
    "assignedTo": "user_789",
    "source": "inbound_lead",
    "customFields": {
        "service_type": "SEO",
        "contract_length": "12 months",
        "lead_source": "Google Ads"
    },
    "dateAdded": "2026-01-15T10:30:00Z",
    "lastStatusChangeAt": "2026-01-18T09:00:00Z"
}
```

## Conversations (Messaging)

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get conversations | GET | `/conversations/` | List conversations |
| Get conversation | GET | `/conversations/{conversationId}` | Full thread |
| Send SMS | POST | `/conversations/messages` | type: "SMS" |
| Send email | POST | `/conversations/messages` | type: "Email" |
| Send WhatsApp | POST | `/conversations/messages` | type: "WhatsApp" (if configured) |
| Get messages | GET | `/conversations/{conversationId}/messages` | Message history |

### Sending a Message

```python
# Send SMS
POST /conversations/messages
{
    "type": "SMS",
    "contactId": "abc123",
    "message": "Hi John, this is [Agent] from [Agency]. We've prepared your monthly report..."
}

# Send Email
POST /conversations/messages
{
    "type": "Email",
    "contactId": "abc123",
    "subject": "Your January Performance Report",
    "message": "<html><body>Hi John, ...</body></html>",
    "emailFrom": "reports@agency.com"
}
```

## Calendars and Appointments

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get calendars | GET | `/calendars/` | List calendar types |
| Get calendar | GET | `/calendars/{calendarId}` | Calendar details |
| Get free slots | GET | `/calendars/{calendarId}/free-slots` | Available times |
| Create appointment | POST | `/calendars/events/appointments` | Book a time |
| Get appointment | GET | `/calendars/events/appointments/{eventId}` | Appointment details |
| Update appointment | PUT | `/calendars/events/appointments/{eventId}` | Reschedule |
| Delete appointment | DELETE | `/calendars/events/appointments/{eventId}` | Cancel |
| Get events | GET | `/calendars/events` | List events |

### Booking an Appointment

```python
POST /calendars/events/appointments
{
    "calendarId": "cal_001",
    "locationId": "loc_456",
    "contactId": "abc123",
    "startTime": "2026-02-10T14:00:00Z",
    "endTime": "2026-02-10T14:30:00Z",
    "title": "Strategy Call - ABC Plumbing",
    "appointmentStatus": "confirmed",
    "assignedUserId": "user_789",
    "notes": "Discuss SEO proposal and Q1 marketing plan"
}
```

## Workflows

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get workflows | GET | `/workflows/` | List all workflows |
| Add contact to workflow | POST | `/contacts/{contactId}/workflow/{workflowId}` | Trigger enrollment |
| Remove from workflow | DELETE | `/contacts/{contactId}/workflow/{workflowId}` | Stop workflow |

### Integration Pattern

Workflows in GHL are configured via the UI, but OpenClaw can trigger them via API:

```python
# Trigger the "New Lead Onboarding" workflow
POST /contacts/{contactId}/workflow/wf_onboarding_001

# Trigger the "Re-engagement Sequence" workflow
POST /contacts/{contactId}/workflow/wf_reengagement_001

# Trigger the "Post-Meeting Follow-Up" workflow
POST /contacts/{contactId}/workflow/wf_postmeeting_001
```

## Forms and Surveys

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get forms | GET | `/forms/` | List all forms |
| Get form submissions | GET | `/forms/submissions` | Filter by form ID |
| Get surveys | GET | `/surveys/` | List all surveys |
| Get survey submissions | GET | `/surveys/submissions` | Filter by survey ID |

## Social and GMB

### Google My Business

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get GMB locations | GET | `/social-media-posting/google/locations` | Linked GMB accounts |
| Create GMB post | POST | `/social-media-posting/` | Post to GMB |
| Get posts | GET | `/social-media-posting/` | List scheduled/published |

### GMB Post Example

```python
POST /social-media-posting/
{
    "locationId": "loc_456",
    "type": "google",
    "googleBusinessLocationId": "gmb_123",
    "title": "Winter Special!",
    "summary": "20% off all plumbing services this February. Call now!",
    "callToAction": {
        "actionType": "CALL",
        "url": "tel:+15551234567"
    },
    "scheduledAt": "2026-02-01T09:00:00Z"
}
```

## Reporting and Analytics

### Available via API

| Report Type | Endpoint | Data Available |
|-------------|----------|----------------|
| Pipeline report | Custom query via opportunities search | Stage counts, values, velocity |
| Contact report | Custom query via contacts search | Source distribution, tag analysis |
| Conversation report | Custom aggregation from messages | Response times, message counts |
| Attribution | `/reporting/attribution` | Source attribution for conversions |

### Building Custom Reports

GHL's reporting API is limited. For comprehensive reporting, combine:

1. **Contact queries** with date range and tag filters to count leads by source
2. **Opportunity queries** with pipeline/stage filters to calculate conversion rates
3. **Conversation queries** to measure response times and engagement
4. **External data** (Google Analytics, DataForSEO) for complete picture

## Payments

### Endpoints

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Create invoice | POST | `/payments/invoices` | With line items |
| Get invoices | GET | `/payments/invoices` | Filterable |
| Create payment link | POST | `/payments/custom-provider/checkout` | One-time or recurring |
| Get transactions | GET | `/payments/transactions` | Payment history |
| Get subscriptions | GET | `/payments/subscriptions` | Recurring payments |

## Websites and Funnels

### Endpoints (Limited)

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| Get funnels | GET | `/funnels/` | List funnels |
| Get funnel pages | GET | `/funnels/{funnelId}/pages` | Page list |
| Get websites | GET | `/websites/` | List websites |

Note: Full page builder functionality is not available via API. Website/funnel management is primarily through the GHL UI.

## Webhook Events

### Available Webhook Triggers

Configure webhooks to receive real-time notifications:

| Event | Trigger | Use in OpenClaw |
|-------|---------|-----------------|
| ContactCreate | New contact created | Trigger enrichment flow |
| ContactUpdate | Contact field changed | Update related records |
| ContactDelete | Contact removed | Clean up linked data |
| ContactDndUpdate | DND status changed | Pause outreach sequences |
| ContactTagUpdate | Tags added/removed | Trigger tag-based workflows |
| OpportunityCreate | New deal created | Pipeline tracking |
| OpportunityStageUpdate | Deal moved stages | Trigger stage-specific actions |
| OpportunityStatusUpdate | Deal won/lost | Revenue tracking, follow-up |
| OpportunityMonetaryValueUpdate | Deal value changed | Revenue forecasting |
| AppointmentCreate | Meeting booked | Send prep materials |
| AppointmentUpdate | Meeting rescheduled | Update calendar, notify |
| AppointmentDelete | Meeting cancelled | Trigger re-engagement |
| InboundMessage | SMS/email received | Auto-respond, escalate |
| OutboundMessage | Message sent | Track communication |
| TaskCreate | Task created | Team notification |
| TaskComplete | Task completed | Update tracking |
| FormSubmission | Form submitted | Process lead data |
| SurveySubmission | Survey completed | Process feedback |
| InvoicePaid | Payment received | Update deal status |

### Webhook Configuration

```python
# Webhook payload structure (inbound)
{
    "type": "ContactCreate",
    "locationId": "loc_456",
    "contactId": "abc123",
    "timestamp": "2026-01-15T10:30:00Z",
    "data": {
        "firstName": "John",
        "lastName": "Smith",
        "email": "john@abcplumbing.com",
        "phone": "+15551234567",
        "source": "website_form"
    }
}

# OpenClaw webhook handler
async def handle_ghl_webhook(event):
    if event["type"] == "ContactCreate":
        await trigger_enrichment_flow(event["contactId"])
    elif event["type"] == "OpportunityStageUpdate":
        await handle_stage_change(event["data"])
    elif event["type"] == "AppointmentCreate":
        await send_meeting_prep(event["data"])
```

## MCP Server Implementation Status

### Currently Implemented (Verify Against Actual MCP Server)

| Capability | Status | Notes |
|------------|--------|-------|
| Contact CRUD | Likely implemented | Core functionality |
| Contact search | Likely implemented | By email, phone |
| Tag management | Likely implemented | Add/remove tags |
| Note creation | Possibly implemented | Check MCP tools |
| Opportunity CRUD | Possibly implemented | Check pipeline tools |
| Pipeline queries | Possibly implemented | Check available tools |
| Send SMS | Possibly implemented | Check messaging tools |
| Send Email | Possibly implemented | Check messaging tools |

### Gaps to Fill (Likely Not Yet Implemented)

| Capability | Priority | Effort | Value |
|------------|----------|--------|-------|
| Calendar/appointment booking | High | Medium | Automate scheduling |
| Workflow triggering | High | Low | Activate GHL automations |
| Custom field management | Medium | Low | Dynamic field creation |
| GMB posting | Medium | Medium | Social media automation |
| Form submission retrieval | Medium | Low | Lead data processing |
| Invoice creation | Low | Medium | Payment automation |
| Webhook handler setup | High | High | Real-time event processing |
| Bulk contact operations | Medium | Medium | Batch enrichment |
| Conversation history | Medium | Low | Context for agents |
| Pipeline analytics queries | High | Medium | Reporting foundation |

### Recommended Implementation Order

1. **Webhook handler** -- enables real-time processing of GHL events
2. **Calendar booking** -- enables automated meeting scheduling
3. **Workflow triggering** -- enables enrollment in GHL automation sequences
4. **Pipeline analytics** -- enables reporting and pipeline management
5. **Conversation history** -- enables context-aware messaging
6. **GMB posting** -- enables social media management
7. **Form/survey retrieval** -- enables lead data processing
8. **Bulk operations** -- enables batch processing for efficiency

## SDK and Documentation References

- GHL API Documentation: https://highlevel.stoplight.io/docs/integrations
- GHL Developer Portal: https://marketplace.gohighlevel.com/
- API Changelog: Check for version updates and breaking changes
- Community: GHL developer community for integration patterns
- JavaScript SDK: Available for Node.js integrations (check npm for `@gohighlevel/sdk`)

## Error Handling

Common API errors and handling:

| Error Code | Meaning | Handling |
|------------|---------|----------|
| 400 | Bad request / validation error | Check request body, log details |
| 401 | Invalid or expired token | Refresh token or re-authenticate |
| 404 | Resource not found | Verify ID, may have been deleted |
| 422 | Unprocessable entity | Data format issue, check field types |
| 429 | Rate limit exceeded | Backoff and retry after delay |
| 500 | GHL server error | Retry with exponential backoff |

```python
async def ghl_request(method, endpoint, data=None, location_id=None):
    """GHL API request with error handling and rate limiting."""
    await rate_limiter.acquire(location_id)

    try:
        response = await httpx.request(
            method,
            f"https://services.leadconnectorhq.com{endpoint}",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Version": "2021-07-28"
            },
            json=data,
            timeout=30.0
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            await asyncio.sleep(retry_after)
            return await ghl_request(method, endpoint, data, location_id)

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"GHL API error: {e.response.status_code} - {e.response.text}")
        raise
```

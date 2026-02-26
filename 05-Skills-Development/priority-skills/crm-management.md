# CRM Management Skill (GoHighLevel)

## Goal

Build an OpenClaw skill that autonomously manages GoHighLevel (GHL) CRM operations: creating contacts, managing pipeline deals, scheduling appointments, sending communications, and triggering workflows. This is the central nervous system for client relationship management in the Rise Local pipeline.

---

## GHL API Capabilities

### Contact Management

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| Create Contact | `POST /contacts/` | Create new contact with name, email, phone, tags |
| Update Contact | `PUT /contacts/{id}` | Update any contact field |
| Get Contact | `GET /contacts/{id}` | Retrieve full contact record |
| Search Contacts | `GET /contacts/search` | Search by name, email, phone, tag |
| Delete Contact | `DELETE /contacts/{id}` | Remove contact (requires confirmation) |
| Add Tag | `POST /contacts/{id}/tags` | Add tags for segmentation |
| Remove Tag | `DELETE /contacts/{id}/tags/{tag}` | Remove a tag |
| Add Note | `POST /contacts/{id}/notes` | Add internal note to contact |
| List Contacts | `GET /contacts/` | Paginated contact list with filters |

### Pipeline Management

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| List Pipelines | `GET /pipelines/` | Get all pipelines and their stages |
| Get Pipeline | `GET /pipelines/{id}` | Get specific pipeline details |
| Create Opportunity | `POST /opportunities/` | Create a deal in a pipeline stage |
| Update Opportunity | `PUT /opportunities/{id}` | Update deal value, stage, status |
| Move Stage | `PUT /opportunities/{id}` | Change pipeline stage (update `stageId`) |
| Delete Opportunity | `DELETE /opportunities/{id}` | Remove a deal |
| List Opportunities | `GET /pipelines/{id}/opportunities` | Get all deals in a pipeline |

### Task Management

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| Create Task | `POST /contacts/{id}/tasks` | Create follow-up task for a contact |
| Update Task | `PUT /contacts/{id}/tasks/{taskId}` | Update task details or status |
| Complete Task | `PUT /contacts/{id}/tasks/{taskId}` | Mark task as completed |
| List Tasks | `GET /contacts/{id}/tasks` | Get all tasks for a contact |

### Appointment Scheduling

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| List Calendars | `GET /calendars/` | Get available calendars |
| Get Slots | `GET /calendars/{id}/free-slots` | Get available time slots |
| Book Appointment | `POST /calendars/events` | Book an appointment |
| Reschedule | `PUT /calendars/events/{id}` | Change appointment time |
| Cancel | `DELETE /calendars/events/{id}` | Cancel an appointment |

### Communication

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| Send SMS | `POST /contacts/{id}/messages` | Send SMS to contact |
| Send Email | `POST /contacts/{id}/messages` | Send email to contact |
| Get Conversations | `GET /conversations/` | List conversations |
| Get Messages | `GET /conversations/{id}/messages` | Get messages in a conversation |

### Workflow Triggers

| Operation | GHL API Endpoint | Description |
|-----------|-----------------|-------------|
| List Workflows | `GET /workflows/` | Get all workflows |
| Trigger Workflow | `POST /contacts/{id}/workflow/{workflowId}` | Add contact to workflow |
| Remove from Workflow | `DELETE /contacts/{id}/workflow/{workflowId}` | Remove contact from workflow |

---

## Reuse Existing GHL MCP Server

You already have a GHL MCP server at `Desktop/GoHighLevel-MCP`. The OpenClaw CRM skill should leverage this rather than re-implementing all API calls.

### Integration Approach

```
Option A: Direct MCP Server Usage
  OpenClaw loads GHL MCP as a tool provider
  Skill calls MCP tools directly via context.tools
  Pro: No code duplication
  Con: Depends on MCP compatibility with OpenClaw

Option B: Wrap MCP in Skill
  OpenClaw skill wraps GHL MCP server calls in TypeScript
  Skill adds validation, safety checks, and error handling on top
  Pro: Full control, better error handling
  Con: Some code duplication

Option C: Hybrid
  Use MCP server for basic CRUD
  Skill adds orchestration logic (multi-step operations, safety checks)
  Pro: Best of both worlds
  Con: Two layers of abstraction

Recommended: Option C (Hybrid)
```

---

## Skill Design: @yourname/ghl-crm

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/ghl-crm",
  "version": "1.0.0",
  "description": "Manage GoHighLevel CRM: contacts, pipelines, tasks, appointments, and communications",
  "commands": ["/crm", "/ghl", "/contact", "/pipeline", "/deal"],
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": [
          "create_contact", "update_contact", "search_contacts", "get_contact",
          "create_deal", "update_deal", "move_deal_stage", "list_deals",
          "create_task", "complete_task", "list_tasks",
          "book_appointment", "reschedule_appointment", "cancel_appointment",
          "send_sms", "send_email",
          "trigger_workflow", "remove_from_workflow",
          "add_tag", "remove_tag", "add_note"
        ],
        "description": "CRM action to perform"
      }
    },
    "optional": {
      "contact_id": { "type": "string" },
      "contact_data": {
        "type": "object",
        "properties": {
          "firstName": { "type": "string" },
          "lastName": { "type": "string" },
          "email": { "type": "string" },
          "phone": { "type": "string" },
          "companyName": { "type": "string" },
          "website": { "type": "string" },
          "address": { "type": "string" },
          "city": { "type": "string" },
          "state": { "type": "string" },
          "tags": { "type": "array", "items": { "type": "string" } },
          "customFields": { "type": "object" }
        }
      },
      "pipeline_id": { "type": "string" },
      "stage_id": { "type": "string" },
      "deal_data": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "value": { "type": "number" },
          "status": { "type": "string", "enum": ["open", "won", "lost", "abandoned"] }
        }
      },
      "task_data": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "description": { "type": "string" },
          "dueDate": { "type": "string", "format": "date-time" },
          "assignedTo": { "type": "string" }
        }
      },
      "message": {
        "type": "object",
        "properties": {
          "type": { "type": "string", "enum": ["sms", "email"] },
          "subject": { "type": "string" },
          "body": { "type": "string" }
        }
      },
      "workflow_id": { "type": "string" },
      "search_query": { "type": "string" },
      "appointment_data": {
        "type": "object",
        "properties": {
          "calendarId": { "type": "string" },
          "startTime": { "type": "string", "format": "date-time" },
          "endTime": { "type": "string", "format": "date-time" },
          "title": { "type": "string" }
        }
      }
    }
  },
  "outputs": {
    "success": { "type": "boolean" },
    "record_id": { "type": "string", "description": "ID of created/updated record" },
    "data": { "type": "object", "description": "Response data from GHL" },
    "message": { "type": "string", "description": "Human-readable result description" }
  },
  "permissions": {
    "network": ["*.gohighlevel.com", "*.leadconnectorhq.com"],
    "environment": ["GHL_API_KEY", "GHL_LOCATION_ID"]
  }
}
```

### Execution Flow by Action

#### Create Contact

```
1. Validate required fields (at least name OR email OR phone)
2. Check for duplicates: search by email/phone
3. If duplicate found: return existing contact ID with warning
4. If no duplicate: create contact via GHL API
5. Optionally add tags
6. Optionally add to pipeline
7. Return contact ID and confirmation
```

#### Move Deal Through Pipeline

```
1. Get current deal status and stage
2. Validate target stage exists in pipeline
3. If stage is "won" or "lost": require explicit confirmation
4. Update opportunity with new stage ID
5. If stage change triggers follow-up: create task
6. Update memory with stage change event
7. Return confirmation with old stage -> new stage
```

#### Send Communication

```
1. Validate contact exists
2. Validate message content (not empty, appropriate length)
3. Check safety rules:
   - Is this a bulk send? -> Require approval
   - Is the content client-facing? -> Show preview for approval
   - Is it outside business hours? -> Warn and confirm
4. Send via GHL API
5. Log the communication in memory
6. Return confirmation with message ID
```

---

## Automation Scenarios

### Scenario 1: New Lead Arrives -> Full Onboarding

```
Trigger: New lead data from Rise Local pipeline or form submission

Step 1: Create Contact
  - Create GHL contact with all enriched data
  - Add tags: "new-lead", industry, source, score-tier
  - Add custom fields: pain_score, tech_stack, review_count

Step 2: Create Pipeline Opportunity
  - Add to "New Leads" pipeline
  - Set stage: "New / Uncontacted"
  - Set deal value: estimated based on industry average

Step 3: Trigger Outreach Workflow
  - Add contact to "New Lead Outreach" GHL workflow
  - Workflow handles: email drip, SMS follow-up, task creation

Step 4: Create Manual Task
  - "Review new lead: [Business Name] - Score: [X/100]"
  - Assigned to: account manager
  - Due: within 24 hours

Step 5: Update Memory
  - Log lead creation event
  - Link to enrichment data in Supabase
```

### Scenario 2: Deal Stalled -> Re-engagement

```
Trigger: Deal in pipeline stage for 7+ days without activity

Step 1: Check Deal Status
  - Query GHL for deal details
  - Verify no recent activity (messages, tasks, appointments)

Step 2: AI-Generate Follow-Up
  - Use context from deal history and contact info
  - Generate personalized follow-up message
  - Show to human for approval

Step 3: Send Follow-Up (after approval)
  - Send via preferred channel (SMS or email)
  - Log communication

Step 4: Create Review Task
  - "Stalled deal follow-up sent: [Business Name]"
  - "If no response in 3 days, consider phone call or moving to nurture"
  - Assigned to: account manager
  - Due: 3 days from now

Step 5: Update Pipeline
  - Add tag: "follow-up-sent"
  - Add note with follow-up details
```

### Scenario 3: Appointment Booked -> Prep Automation

```
Trigger: Appointment confirmed in GHL calendar

Step 1: Get Contact and Deal Info
  - Pull full contact record
  - Pull enrichment data from Supabase
  - Pull any previous communication history

Step 2: Generate Meeting Prep Document
  - Business overview (from enrichment)
  - Pain points identified (from scoring)
  - Competitor comparison (if available)
  - Recommended services and pricing
  - Talking points

Step 3: Create Prep Task
  - "Meeting prep for [Business Name] - [Date/Time]"
  - Attach prep document
  - Due: 1 hour before appointment

Step 4: Send Confirmation to Client
  - Automated confirmation email/SMS via GHL
  - Include: date/time, meeting link (if virtual), what to prepare

Step 5: Set Reminder
  - 24-hour reminder to client
  - 1-hour reminder to account manager with prep document
```

---

## Safety and Guardrails

### Operations Requiring Human Approval

| Operation | Why | Approval Method |
|-----------|-----|-----------------|
| **Bulk contact creation** (>5 at once) | Prevent accidental mass import | Prompt user with count and preview |
| **Contact deletion** | Irreversible data loss | Show contact details, confirm |
| **Client-facing messages** (SMS/email) | Brand/legal risk | Show preview, get explicit "send" |
| **Bulk tag operations** | Could break segmentation | Show affected count, confirm |
| **Pipeline stage: Won/Lost** | Business-critical status change | Show deal details, confirm |
| **Workflow trigger** (outreach) | Sends communications to real people | Show workflow name and target, confirm |

### Operations Allowed Without Approval

| Operation | Why Safe |
|-----------|----------|
| Contact search | Read-only |
| Get contact details | Read-only |
| List pipelines/deals | Read-only |
| Add internal note | Internal only, not client-facing |
| Create task | Internal only |
| Add tag (non-destructive) | Additive, easily reversible |

### Rate Limiting

```
GHL API Limits (per location):
  - Contact operations: ~100/minute
  - Message sending: Check GHL plan limits
  - Workflow triggers: ~50/minute

Skill-enforced limits:
  - Max 10 SMS per hour per contact (prevent spam)
  - Max 50 contacts created per batch operation
  - Max 5 pipeline stage changes per minute (prevent rapid cycling)
  - Cooldown: 24 hours between follow-up messages to same contact
```

### Audit Trail

Every CRM operation should be logged:

```json
{
  "timestamp": "2026-02-05T14:30:00Z",
  "action": "create_contact",
  "contact_id": "ghl-abc123",
  "details": {
    "name": "John Smith",
    "source": "rise-local-pipeline",
    "tags_added": ["new-lead", "plumber", "austin-tx"]
  },
  "initiated_by": "openclaw-agent",
  "approved_by": "human" | "auto",
  "result": "success"
}
```

---

## GHL API Configuration

### Required Configuration

```json
{
  "GHL_API_KEY": {
    "description": "GoHighLevel API key (v2)",
    "sensitive": true,
    "required": true
  },
  "GHL_LOCATION_ID": {
    "description": "GHL location/sub-account ID",
    "required": true
  },
  "GHL_API_VERSION": {
    "description": "GHL API version to use",
    "default": "2021-07-28"
  },
  "DEFAULT_PIPELINE_ID": {
    "description": "Default pipeline for new leads",
    "required": false
  },
  "DEFAULT_CALENDAR_ID": {
    "description": "Default calendar for appointments",
    "required": false
  }
}
```

### API Authentication

```typescript
// All GHL API calls use this header pattern
const headers = {
  'Authorization': `Bearer ${config.GHL_API_KEY}`,
  'Version': config.GHL_API_VERSION,
  'Content-Type': 'application/json'
};

// Base URL
const GHL_BASE_URL = 'https://services.leadconnectorhq.com';
```

---

## Integration with Other Skills

### Data Flow

```
lead-pipeline skill
  -> discovers and scores leads
  -> passes enriched lead data to ghl-crm skill
  -> ghl-crm creates contact, sets up pipeline, triggers workflow

presentation-generator skill
  -> generates pitch deck for a deal
  -> ghl-crm attaches to deal notes and creates prep task

competitor-scraping skill
  -> detects competitor changes
  -> ghl-crm updates relevant contact notes with competitive intel

database-ops skill
  -> stores enrichment data in Supabase
  -> ghl-crm links GHL contact ID to Supabase record ID
```

---

## Testing Plan

### Unit Tests

- Input validation for all 20+ actions
- Duplicate detection logic
- Safety check logic (bulk operation detection, business hours check)
- Rate limit enforcement

### Integration Tests (with GHL sandbox)

- Create contact -> verify in GHL
- Create deal -> move through stages -> verify
- Send test SMS/email -> verify delivery
- Book appointment -> verify in calendar
- Trigger workflow -> verify contact added

### End-to-End Tests

- Full new lead flow: discovery -> enrichment -> GHL contact -> pipeline -> workflow
- Stalled deal detection and follow-up
- Appointment booking and prep automation

---

*Last updated: 2026-02-05*
*Status: Skill design complete; leverages existing GHL MCP server at Desktop/GoHighLevel-MCP*

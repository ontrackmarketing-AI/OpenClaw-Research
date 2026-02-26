# Call Routing Logic

## Overview

This document defines the complete call routing logic for SW Recovery Services' AI voice bot. The system handles all inbound calls through a single phone number and must route calls based on three primary criteria: **deal size**, **department**, and **time of day**. Steven's rule is absolute: any $50M+ deal or Fortune 500 caller transfers directly to him.

The system serves 20 employees across multiple departments with individualized routing, availability detection, after-hours handling, and fallback chains.

---

## Deal Size Routing Rules

### Steven's Rule (Highest Priority)

This is the immutable top-level routing rule. It overrides all other routing logic.

```
IF deal_size >= $50,000,000 OR caller_is_fortune_500 == true:
    IMMEDIATELY warm_transfer to Steven
    DO NOT ask additional qualifying questions
    DO NOT route to anyone else first
```

**Detection Triggers for Steven's Rule**:
- Caller explicitly states a project value of $50M or higher
- Caller mentions a Fortune 500 company name (bot has Fortune 500 list in knowledge base)
- CRM lookup returns a contact/company tagged as "Fortune 500" or "Tier 1"
- Caller asks for Steven by name (always route to Steven regardless of deal size)

**Warm Transfer Protocol for Steven**:
1. Bot says: "This sounds like an excellent opportunity. Let me connect you with Steven, our lead recovery specialist, right away."
2. Place caller on brief hold with professional hold music/message
3. Dial Steven's direct line
4. When Steven answers, bot whispers: "Incoming call from [caller name] at [company]. Estimated deal: [$X]. Project type: [type]."
5. Connect caller to Steven
6. If Steven does not answer within 30 seconds:
   - Offer to book a meeting with Steven specifically
   - Take a detailed message marked "URGENT - Steven" in CRM
   - Send SMS notification to Steven's mobile

### Deal Size Tier Routing

| Tier | Deal Size | Routing Target | Fallback |
|------|-----------|----------------|----------|
| **Tier 1** | $50M+ / Fortune 500 | Steven (direct) | Book meeting with Steven |
| **Tier 2** | $10M - $49.9M | Senior Recovery Specialist | Next available senior rep |
| **Tier 3** | $1M - $9.9M | Recovery Specialist | Any available rep |
| **Tier 4** | < $1M | Junior Rep / Available Rep | Scheduling agent |
| **Unknown** | Caller won't specify | General intake rep | Qualify further, then route |

### Deal Size Qualification Questions

The Deal Qualification Agent asks these questions in order (stop when deal size becomes clear):

1. "Can you tell me a bit about your project? What kind of recovery or remediation work are you looking at?"
2. "Do you have an approximate scope or budget range for this project?"
3. "How large is the site or facility involved?"
4. "Is this a government contract, private sector, or insurance-driven project?"

**Implicit Size Indicators** (when caller won't give explicit numbers):
- Government Superfund site -> likely $10M+ (route Tier 2)
- Multi-state environmental cleanup -> likely $50M+ (route Tier 1)
- Single-site commercial remediation -> likely $1M-10M (route Tier 3)
- Residential or small commercial -> likely < $1M (route Tier 4)
- Fortune 500 company name mentioned -> always Tier 1 (Steven's Rule)

---

## Department Routing

### Department Directory

| Department | Extension | Primary Contact | Backup Contact | Hours |
|------------|-----------|-----------------|----------------|-------|
| **Executive / Steven** | 101 | Steven [Owner] | Executive Assistant | 7AM-7PM |
| **Sales / New Business** | 110 | Sales Lead | Available Sales Rep | 8AM-6PM |
| **Senior Recovery** | 120 | Senior Specialist 1 | Senior Specialist 2 | 8AM-6PM |
| **Recovery Operations** | 130 | Ops Manager | Field Supervisor | 7AM-7PM |
| **Accounting / Billing** | 140 | Accounting Lead | Accounting Staff | 8AM-5PM |
| **Legal / Compliance** | 150 | Legal Counsel | Compliance Officer | 9AM-5PM |
| **HR / Administration** | 160 | HR Manager | Office Manager | 8AM-5PM |
| **Field Operations** | 170 | Field Dispatch | On-Call Supervisor | 24/7 (on-call) |
| **Project Management** | 180 | PM Lead | Assigned PM | 8AM-6PM |
| **IT / Technical** | 190 | IT Manager | Help Desk | 8AM-5PM |

### Department Detection Logic

The bot identifies departments through natural language understanding:

```
Intent Mapping:
- "billing", "invoice", "payment", "account balance" --> Accounting (ext 140)
- "contract", "legal", "compliance", "insurance claim" --> Legal (ext 150)
- "new project", "quote", "bid", "proposal", "RFP" --> Sales (ext 110)
- "project status", "update", "timeline", "schedule" --> Project Management (ext 180)
- "emergency", "spill", "urgent site issue" --> Field Operations (ext 170)
- "employment", "hiring", "benefits", "HR" --> HR (ext 160)
- "IT", "system", "login", "technical issue" --> IT (ext 190)
- [person's name] --> Lookup in employee directory
```

### Person-by-Name Routing

When a caller asks for someone by name:

1. Fuzzy-match caller's spoken name against the 20-employee directory
2. If exact match: transfer to that person's extension
3. If multiple matches (e.g., "John" matches 2 employees): ask "Do you mean John in Sales or John in Operations?"
4. If no match: "I don't have anyone by that name. Can you tell me what department they're in?"
5. Always check availability before transferring

### Availability-Based Routing

```
check_availability(employee):
    1. Check employee's calendar (Google Calendar / Nutshell) for current time
    2. If in meeting / busy:
        - Check calendar for next available slot
        - Offer: "They're currently in a meeting until [time]. Would you like to:
          a) Leave a message
          b) Book a callback
          c) Speak with someone else in [department]"
    3. If on another call:
        - "They're currently on another call. Would you like to hold,
           leave a message, or book a callback?"
    4. If out of office / PTO:
        - Route to backup contact for that department
        - "They're out of the office today. Let me connect you with [backup name]."
    5. If available:
        - Transfer immediately
```

---

## After-Hours Handling

### Business Hours Definition

| Category | Hours | Days |
|----------|-------|------|
| **Full staff** | 8:00 AM - 5:00 PM ET | Monday - Friday |
| **Extended (Steven + Ops)** | 7:00 AM - 7:00 PM ET | Monday - Friday |
| **After hours** | 7:00 PM - 7:00 AM ET | Monday - Friday |
| **Weekend** | All day | Saturday - Sunday |
| **Holidays** | All day | Company holiday calendar |
| **Field Ops (on-call)** | 24/7 | Every day |

### After-Hours Call Flow

```
[Incoming Call During After-Hours]
    |
    v
[After-Hours Greeting Agent]
    "Thank you for calling SW Recovery Services. Our offices are currently
     closed. Our regular hours are 8 AM to 5 PM Eastern, Monday through Friday."
    |
    v
[Intent Classification]
    |
    +---> Emergency / Urgent
    |       |
    |       v
    |     "I understand this is urgent. Let me connect you with our
    |      on-call emergency team."
    |       |
    |       v
    |     [Transfer to On-Call Field Supervisor]
    |       |
    |       +--> If no answer after 45 seconds:
    |              Transfer to secondary on-call
    |              If still no answer: take message + send emergency SMS to all managers
    |
    +---> Schedule a Meeting
    |       |
    |       v
    |     [Scheduling Agent]
    |       +--> Check next-day availability
    |       +--> Book meeting
    |       +--> Send SMS confirmation
    |
    +---> Leave a Message
    |       |
    |       v
    |     [Message Agent]
    |       +--> Collect: name, company, phone, reason, urgency (1-5), best callback time
    |       +--> Save to Nutshell CRM as activity
    |       +--> Send notification email to relevant department
    |       +--> If urgency >= 4: also send SMS to department manager
    |
    +---> General Question
            |
            v
          [Knowledge Base Agent]
            +--> Answer from knowledge base
            +--> Offer to schedule a call for detailed discussion
```

### On-Call Rotation

| Time Period | Primary On-Call | Secondary On-Call | Escalation |
|-------------|-----------------|-------------------|------------|
| Weeknight (Mon-Thu) | Field Supervisor A | Ops Manager | Steven |
| Friday night | Field Supervisor B | Ops Manager | Steven |
| Saturday | Ops Manager | Field Supervisor A | Steven |
| Sunday | Field Supervisor A | Field Supervisor B | Steven |
| Holiday | Rotates weekly | Ops Manager | Steven |

The on-call schedule syncs with Google Calendar. The bot checks the on-call calendar in real-time to determine who to transfer to.

---

## DTMF Handling

While the AI bot handles most routing through natural language, DTMF (touch-tone) support is provided as a fallback for callers who prefer it or have difficulty with voice interaction.

### DTMF Menu (Activated by pressing any key during greeting)

```
"You've reached SW Recovery Services. You can speak naturally
 or press a number for the following options:

 Press 1 for Sales and New Business
 Press 2 for Project Status and Updates
 Press 3 for Accounting and Billing
 Press 4 for an Emergency or Urgent Matter
 Press 5 to Schedule a Meeting
 Press 6 to Leave a Message
 Press 0 to speak with an operator
 Press 9 to repeat these options"
```

### DTMF-to-Route Mapping

| Key | Route | Agent |
|-----|-------|-------|
| 1 | Sales | Deal Qualification Agent |
| 2 | Project Management | Client Lookup Agent |
| 3 | Accounting | Department Router (ext 140) |
| 4 | Emergency | Field Operations (ext 170) or on-call |
| 5 | Schedule | Scheduling Agent |
| 6 | Message | Message Agent |
| 0 | Operator | Available receptionist or Steven's assistant |
| 9 | Repeat | Replay DTMF menu |

### DTMF Detection Configuration (Vapi)

```json
{
  "dtmf": {
    "enabled": true,
    "timeout_ms": 5000,
    "inter_digit_timeout_ms": 3000,
    "max_digits": 1,
    "finish_on_key": "#"
  }
}
```

---

## Call Recording and Transcription

### Recording Policy

All calls are recorded for quality assurance and compliance purposes. The bot announces recording at the start of every call.

**Recording Announcement** (played before greeting):
> "This call may be recorded for quality assurance and training purposes."

### Recording Configuration

| Setting | Value |
|---------|-------|
| **Recording format** | WAV (high quality) + MP3 (compressed backup) |
| **Recording start** | After announcement, before greeting |
| **Recording end** | On call termination |
| **Storage** | AWS S3 / Vapi cloud storage |
| **Retention** | 90 days standard, 1 year for deals > $1M |
| **Access** | Management + assigned rep + legal |

### Transcription Pipeline

```
[Call Recording Completes]
    |
    v
[Vapi Post-Call Webhook fires]
    |
    v
[Transcription Processing]
    +--> Full transcript saved to Nutshell CRM (activity on contact)
    +--> AI summary generated (key points, action items, sentiment)
    +--> Deal size extracted and tagged
    +--> Follow-up tasks auto-created in Nutshell
    |
    v
[Notification]
    +--> Email summary to assigned rep
    +--> If deal > $10M: copy Steven on summary
    +--> If negative sentiment: flag for manager review
```

### Post-Call Webhook Payload

```json
{
  "event": "call.completed",
  "call_id": "call_abc123",
  "duration_seconds": 245,
  "caller_phone": "+15551234567",
  "direction": "inbound",
  "agents_used": ["greeting", "deal_qualification", "scheduling"],
  "routing_decision": {
    "tier": 2,
    "deal_size_estimate": "$15M",
    "routed_to": "senior_rep_1",
    "transfer_successful": true
  },
  "transcript": "...",
  "recording_url": "https://...",
  "summary": "Caller from Acme Corp inquiring about $15M remediation project...",
  "action_items": [
    "Send proposal template to john@acme.com",
    "Schedule site visit for next week"
  ],
  "sentiment": "positive",
  "nutshell_contact_id": "12345",
  "nutshell_lead_id": "67890"
}
```

---

## Edge Cases and Error Handling

### Scenario: Caller Refuses to Identify

```
IF caller_refuses_to_state_purpose after 2 attempts:
    "No problem at all. Let me connect you with a member of our team
     who can help."
    Route to general intake receptionist
    Flag call in CRM as "unqualified - caller declined to identify"
```

### Scenario: Multiple Routing Matches

```
IF caller_intent matches multiple departments:
    Prioritize by specificity:
    1. Person name match (most specific)
    2. Deal size routing (Steven's Rule check)
    3. Department keyword match
    4. General intake (least specific)
```

### Scenario: Transfer Fails (No Answer)

```
transfer_attempt(target, max_rings=6):
    1. Attempt transfer to target
    2. If no answer after max_rings (~30 seconds):
        a. Return to caller
        b. "I wasn't able to reach [name/department] right now."
        c. Offer options:
           - Try backup contact
           - Leave a voicemail
           - Book a callback
           - Try again in X minutes
    3. If transfer line is busy:
        - Same fallback as no answer
    4. Log failed transfer in CRM with timestamp
```

### Scenario: CRM Lookup Fails

```
IF nutshell_api_timeout OR nutshell_api_error:
    1. Continue routing without CRM data
    2. Use caller-provided information for deal size routing
    3. Play filler: "Let me look into that for you..."
    4. Retry CRM lookup in background
    5. If still failing: route based on verbal information only
    6. Flag in monitoring dashboard
```

### Scenario: Caller is Angry/Frustrated

```
IF sentiment_detection indicates frustration or anger:
    1. Acknowledge: "I completely understand your frustration."
    2. Do NOT ask additional qualifying questions
    3. Fast-track to a human: "Let me connect you with someone
       who can help you right away."
    4. Route to most senior available person in relevant department
    5. Tag call as "escalation" in CRM
```

### Scenario: Repeat Caller (Same Day)

```
IF caller_phone matches a call from earlier today:
    1. Retrieve previous call context from CRM
    2. "Welcome back. I see you called earlier about [topic].
        Would you like me to connect you with the same person?"
    3. Route to same rep/department as previous call
    4. Pass previous call context to receiving agent
```

---

## Routing Decision Matrix

| Priority | Condition | Action | Override? |
|----------|-----------|--------|-----------|
| **P0** | Caller asks for Steven by name | Transfer to Steven | Overrides all |
| **P0** | $50M+ deal or Fortune 500 | Transfer to Steven | Overrides all |
| **P1** | Emergency / spill / urgent | Transfer to on-call | Overrides hours |
| **P2** | Existing client with assigned rep | Transfer to rep | Standard routing |
| **P3** | Department request by name | Transfer to dept | Standard routing |
| **P3** | $10M-$49.9M deal | Transfer to senior rep | Standard routing |
| **P4** | $1M-$9.9M deal | Transfer to available rep | Standard routing |
| **P5** | < $1M deal | Transfer to junior rep | Standard routing |
| **P6** | General question | Knowledge base agent | No transfer needed |
| **P7** | After hours (non-emergency) | After-hours agent | Time-gated |

---

## API/Integration Details

### Nutshell CRM Integration Points

| Action | API Endpoint | Trigger |
|--------|-------------|---------|
| Contact lookup by phone | `POST /api/v1/contacts/search` | Every inbound call |
| Company lookup | `POST /api/v1/accounts/search` | New business calls |
| Create new lead | `POST /api/v1/leads` | Qualified new business |
| Log activity | `POST /api/v1/activities` | Every call (transcript + summary) |
| Get assigned rep | `GET /api/v1/leads/{id}` | Existing client calls |
| Update lead stage | `PUT /api/v1/leads/{id}` | After qualification |

### Vapi Configuration

```json
{
  "squad": {
    "name": "SW Recovery Inbound Squad",
    "members": [
      {
        "assistant_id": "greeting_agent",
        "entry_point": true,
        "handoff_tools": ["deal_qual", "client_lookup", "dept_router", "kb_agent", "after_hours"]
      },
      {
        "assistant_id": "deal_qualification_agent",
        "tools": ["nutshell_lookup", "nutshell_create_lead", "warm_transfer", "transfer_rep"]
      }
    ]
  },
  "telephony": {
    "provider": "twilio",
    "phone_number": "+1XXXXXXXXXX",
    "recording": true,
    "transcription": true
  }
}
```

---

## Cost Implications

### Routing Infrastructure Costs

| Component | Monthly Cost |
|-----------|-------------|
| Twilio phone number (1 inbound number) | $2/mo |
| Twilio inbound minutes (est. 2,000 min) | $17-28/mo |
| Nutshell CRM API calls (~5,000/mo) | Included in Nutshell plan |
| Vapi Squad orchestration | Included in per-minute pricing |
| Call recording storage (50GB/mo) | $5-10/mo |
| **Routing-specific total** | **$24-40/mo** |

The per-minute voice bot costs (LLM, STT, TTS) are covered in the platform-comparison.md and architecture-design.md documents.

---

## Estimated Build Hours

| Component | Hours | Description |
|-----------|-------|-------------|
| Routing decision engine | 8-10h | Priority matrix, deal size tiers, department mapping |
| Steven's Rule implementation | 2-3h | Fortune 500 list, CRM tagging, warm transfer flow |
| Employee directory + availability | 6-8h | 20 employees, calendars, backup chains |
| After-hours flow | 4-6h | On-call rotation, message taking, emergency escalation |
| DTMF menu integration | 2-3h | Touch-tone fallback menu |
| Call recording + transcription | 3-4h | Recording config, webhook, CRM logging |
| Edge case handling | 4-6h | Failed transfers, angry callers, repeat callers |
| Post-call processing | 4-6h | Summary generation, CRM activity, follow-up tasks |
| Testing all routing paths | 8-12h | Every tier, every department, every edge case |
| **Total** | **41-58h** | ~2 weeks with dedicated developer |

---

## Sources

- [Bland AI IVR Smart Call Routing](https://www.bland.ai/blogs/ai-powered-ivr-smart-call-routing)
- [Bland AI Inbound Call Handling](https://www.bland.ai/use-cases/inbound-call-handling)
- [Retell AI Voice Agents 2025](https://www.retellai.com/blog/ai-voice-agents-in-2025)
- [Nextiva Intelligent Call Routing](https://www.nextiva.com/blog/intelligent-call-routing.html)
- [Smith.ai Intelligent Call Routing](https://smith.ai/blog/intelligent-call-routing)
- [Vapi Squads Example](https://docs.vapi.ai/squads-example)
- [Twilio IVR Solutions](https://www.twilio.com/en-us/use-cases/ivr)

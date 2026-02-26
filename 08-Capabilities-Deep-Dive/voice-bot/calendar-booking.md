# Calendar Booking Integration

## Overview

This document defines how the AI voice bot books meetings for SW Recovery Services when staff are unavailable to take calls. The system integrates with **Google Calendar** (primary), **Nutshell Scheduler** (CRM-native), and optionally **Calendly** (for external-facing booking links). The bot must check real-time availability, book on behalf of the caller, send confirmations, and sync all booking data back to Nutshell CRM.

Calendar booking is a critical fallback in the call routing flow -- whenever a transfer fails or staff are unavailable, the Scheduling Agent takes over to ensure no opportunity is lost.

---

## Booking Flow Architecture

### When Calendar Booking Triggers

The Scheduling Agent activates when any of these conditions occur:

1. **Transfer fails**: Target employee does not answer after 6 rings (~30 seconds)
2. **Employee busy**: Calendar shows current meeting or DND status
3. **After hours**: Call comes in outside business hours
4. **Caller requests**: Caller explicitly asks to schedule a meeting
5. **Deal qualification complete**: High-value lead qualified but no immediate transfer available

### End-to-End Booking Flow

```
[Scheduling Agent Activated]
    |
    v
[Determine Target Rep]
    +--> From routing: specific person requested
    +--> From deal tier: assigned rep or round-robin
    +--> From department: department lead or available member
    |
    v
[Check Availability via Google Calendar API]
    +--> Look at next 5 business days
    +--> Find 3 available slots (30-min blocks)
    +--> Exclude lunch (12-1 PM), before 8 AM, after 5 PM
    |
    v
[Present Options to Caller]
    "I have a few times available for [rep name]:
     - Tomorrow, Tuesday, at 10:00 AM
     - Wednesday at 2:30 PM
     - Thursday at 9:00 AM
     Which works best for you?"
    |
    v
[Caller Selects a Time]
    |
    v
[Collect Booking Details]
    +--> Confirm caller name
    +--> Confirm email address (for calendar invite)
    +--> Confirm phone number (for callback)
    +--> Note: purpose of meeting (from earlier in call)
    |
    v
[Create Calendar Event]
    +--> Google Calendar: create event on rep's calendar
    +--> Include: caller name, company, phone, purpose, deal size
    +--> Add Google Meet / Zoom link (if virtual)
    +--> Set 15-min reminder for rep
    |
    v
[Create/Update Nutshell Records]
    +--> Create or update contact in Nutshell
    +--> Create lead if new business
    +--> Log scheduled meeting as activity
    +--> Set follow-up task for rep
    |
    v
[Send Confirmations]
    +--> Calendar invite to caller's email
    +--> SMS confirmation to caller's phone
    +--> Notification to rep (email + calendar alert)
    |
    v
[Confirm to Caller]
    "You're all set. I've booked a meeting with [rep name] on
     [day] at [time]. You'll receive a calendar invite and a
     text confirmation shortly. Is there anything else I can help with?"
```

---

## Google Calendar Integration

### API Configuration

**API**: Google Calendar API v3
**Auth**: OAuth 2.0 Service Account (server-to-server, no user consent needed)
**Scopes**: `https://www.googleapis.com/auth/calendar.events`, `https://www.googleapis.com/auth/calendar.readonly`

### Vapi Native Google Calendar Integration

Vapi provides a native Google Calendar integration that simplifies setup:

1. Connect Google Workspace account in Vapi Dashboard > Settings > Integrations
2. Grant calendar access for each rep's calendar
3. Use built-in tools: `checkCalendarAvailability` and `bookCalendarEvent`

**Vapi Google Calendar Tool Configuration**:
```json
{
  "type": "google_calendar",
  "function": {
    "name": "checkCalendarAvailability",
    "parameters": {
      "calendarId": "rep_email@swrecovery.com",
      "timeMin": "2026-02-14T08:00:00-05:00",
      "timeMax": "2026-02-20T17:00:00-05:00",
      "duration_minutes": 30
    }
  }
}
```

### Availability Check Logic

```python
def check_availability(rep_email, duration=30, days_ahead=5):
    """
    Check rep's calendar for available slots.
    Returns up to 3 available time slots.
    """
    now = datetime.now(tz=ET)
    end = now + timedelta(days=days_ahead)

    # Get existing events (busy times)
    busy_times = google_calendar.freebusy_query(
        calendar_id=rep_email,
        time_min=now,
        time_max=end
    )

    # Define available windows
    business_hours = {
        "start": time(8, 0),   # 8:00 AM
        "end": time(17, 0),    # 5:00 PM
        "lunch_start": time(12, 0),
        "lunch_end": time(13, 0)
    }

    available_slots = []
    for day in business_days(now, end):
        for slot in generate_slots(day, business_hours, duration):
            if not overlaps(slot, busy_times):
                available_slots.append(slot)
                if len(available_slots) >= 3:
                    return available_slots

    return available_slots
```

### Create Calendar Event

```json
{
  "summary": "Meeting: John Smith (Acme Corp) - Remediation Project",
  "description": "Booked by AI Voice Bot\n\nCaller: John Smith\nCompany: Acme Corp\nPhone: +1-555-123-4567\nPurpose: $15M remediation project discussion\nDeal Tier: 2\n\nNutshell Lead: #67890",
  "start": {
    "dateTime": "2026-02-15T10:00:00-05:00",
    "timeZone": "America/New_York"
  },
  "end": {
    "dateTime": "2026-02-15T10:30:00-05:00",
    "timeZone": "America/New_York"
  },
  "attendees": [
    {"email": "rep@swrecovery.com"},
    {"email": "john.smith@acme.com"}
  ],
  "conferenceData": {
    "createRequest": {
      "requestId": "bot-booking-uuid-123",
      "conferenceSolutionKey": {"type": "hangoutsMeet"}
    }
  },
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "email", "minutes": 60},
      {"method": "popup", "minutes": 15}
    ]
  }
}
```

---

## Nutshell Scheduler Integration

### What is Nutshell Scheduler

Nutshell Scheduler is a built-in meeting scheduling tool within Nutshell CRM. It creates shareable booking links (similar to Calendly) that sync directly with Google Calendar or Office 365 and automatically create/update CRM records.

### How the Bot Uses Nutshell Scheduler

**Method 1: Direct Calendar Booking (Primary)**
The bot books directly via Google Calendar API (as described above) and then syncs the booking data to Nutshell via API. This is the preferred method because the bot controls the entire flow.

**Method 2: Send Nutshell Scheduler Link (Fallback)**
If direct booking fails or the caller prefers to self-schedule:

```
Bot: "I can also send you a link to book directly with [rep name]'s
     calendar. Would you like me to text that to you?"

[If caller agrees]
    Send SMS to caller's phone:
    "Book a meeting with [Rep Name] at SW Recovery Services:
     https://app.nutshell.com/schedule/[rep-slug]"
```

### Nutshell Scheduler Features

| Feature | Capability |
|---------|------------|
| **Booking links** | Unique URL per rep (e.g., `/schedule/steven`) |
| **Calendar sync** | Real-time sync with Google Calendar + Office 365 |
| **Custom forms** | Attach intake form to collect project details |
| **Round-robin** | Auto-rotate bookings among team members |
| **Meeting types** | 15-min intro, 30-min consultation, 60-min deep dive |
| **Auto-CRM update** | New contacts/leads created automatically |
| **Zoom/Meet/Teams** | Auto-generate video meeting links |
| **Confirmation emails** | Automatic confirmation + reminder emails |

### Nutshell API for Booking Sync

After the bot books via Google Calendar, it syncs to Nutshell:

```
POST /api/v1/activities
{
  "activity": {
    "type": "meeting",
    "subject": "Scheduled: John Smith (Acme Corp) - Remediation",
    "start_time": "2026-02-15T10:00:00-05:00",
    "end_time": "2026-02-15T10:30:00-05:00",
    "contact_id": 12345,
    "lead_id": 67890,
    "assigned_to": "rep_user_id",
    "notes": "Booked by AI Voice Bot. $15M remediation project. Tier 2 deal."
  }
}
```

---

## Calendly Integration (Optional / Phase 2)

### When to Use Calendly

Calendly may be used as an alternative or supplement if:
- Some reps already use Calendly and prefer it over Nutshell Scheduler
- External-facing booking pages are needed (website, email signatures)
- Complex scheduling rules are needed (e.g., buffer times, meeting limits per day)

### Calendly + Voice Bot Integration

**Via Vapi Function Calling + n8n/Make.com**:

```
[Bot determines need to book meeting]
    |
    v
[Vapi calls custom function: "check_calendly_availability"]
    |
    v
[n8n webhook receives request]
    |
    v
[n8n calls Calendly API]
    +--> GET /scheduling_links (get rep's booking link)
    +--> GET /event_type_available_times (check availability)
    |
    v
[n8n returns available times to Vapi]
    |
    v
[Bot presents options to caller]
    |
    v
[Caller selects time]
    |
    v
[n8n calls Calendly API to book]
    +--> POST /scheduled_events/invitees
    |
    v
[Calendly sends confirmation email + calendar invite]
    |
    v
[Calendly webhook fires -> n8n -> Nutshell CRM update]
```

### Calendly API Endpoints

| Action | Endpoint | Method |
|--------|----------|--------|
| List event types | `/event_types` | GET |
| Check availability | `/event_type_available_times` | GET |
| List scheduled events | `/scheduled_events` | GET |
| Get invitee info | `/scheduled_events/{uuid}/invitees` | GET |
| Cancel event | `/scheduled_events/{uuid}/cancellation` | POST |

### Calendly + Nutshell Sync

Calendly has a native Nutshell integration:
- New Calendly bookings automatically create Nutshell contacts
- Meeting details sync as activities on the contact record
- Can be configured via Calendly's integration settings or via Zapier

---

## Rep Calendar Link Management

### Per-Rep Configuration

Each of the 20 employees needs their calendar configured for the voice bot:

| Rep | Google Calendar | Nutshell Scheduler | Meeting Duration | Buffer |
|-----|----------------|-------------------|-----------------|--------|
| Steven | steven@swrecovery.com | /schedule/steven | 30 min | 15 min |
| Sales Lead | sales@swrecovery.com | /schedule/sales | 30 min | 10 min |
| Senior Spec 1 | senior1@swrecovery.com | /schedule/senior1 | 30 min | 10 min |
| Accounting | accounting@swrecovery.com | /schedule/accounting | 15 min | 5 min |
| ... (16 more) | ... | ... | ... | ... |

### Meeting Types by Context

| Context | Duration | Type | Video Link |
|---------|----------|------|------------|
| **New business intro** | 30 min | Google Meet | Yes |
| **Project status check** | 15 min | Phone callback | No |
| **Detailed consultation** | 60 min | Google Meet | Yes |
| **Accounting/billing** | 15 min | Phone callback | No |
| **Emergency follow-up** | 30 min | Phone callback | No |
| **Steven (Tier 1 deal)** | 45 min | Google Meet | Yes |

### Round-Robin Assignment

When no specific rep is requested and the call is a general new business inquiry:

```
round_robin_assignment(department="sales"):
    1. Get list of available reps in department
    2. Check who has the fewest meetings today
    3. Check who was last assigned (rotate fairly)
    4. Assign to next rep in rotation who is available
    5. Book on their calendar
    6. Update rotation counter
```

Nutshell Scheduler has built-in round-robin that can handle this automatically when using the team booking link.

---

## Confirmation Messages

### SMS Confirmation (via Twilio)

Sent immediately after booking:

```
SW Recovery Services - Meeting Confirmed

You have a meeting scheduled with [Rep Name]:
Date: Tuesday, Feb 15, 2026
Time: 10:00 AM ET
Duration: 30 minutes
Location: Google Meet (link in calendar invite)

To reschedule, call us at (555) XXX-XXXX or reply RESCHEDULE.
```

### Email Confirmation

Sent via Google Calendar invite (automatic) + optional custom email:

```
Subject: Meeting Confirmed - SW Recovery Services

Dear [Caller Name],

Thank you for your interest in SW Recovery Services.
Your meeting has been confirmed:

With: [Rep Name], [Rep Title]
Date: Tuesday, February 15, 2026
Time: 10:00 AM - 10:30 AM ET
Join: [Google Meet Link]

If you need to reschedule, please call (555) XXX-XXXX
or use this link: [Nutshell Scheduler reschedule link]

We look forward to speaking with you.

Best regards,
SW Recovery Services
```

### Rep Notification

Sent to the rep via email/Slack when a meeting is booked:

```
New meeting booked by AI Voice Bot:

Caller: John Smith
Company: Acme Corp
Phone: +1-555-123-4567
Email: john.smith@acme.com
Purpose: $15M remediation project inquiry
Deal Tier: 2

Meeting: Feb 15, 2026 at 10:00 AM ET (30 min)
Google Meet: [link]
Nutshell Lead: [link to lead #67890]

Call recording: [link]
Call summary: Caller inquired about multi-site remediation project
for Acme Corp. Estimated $15M scope. Interested in discussing
timeline and capabilities.
```

---

## Rescheduling and Cancellation

### Reschedule Flow (Caller Calls Back)

```
[Caller says "I need to reschedule my meeting"]
    |
    v
[Bot looks up upcoming meetings by caller phone number]
    +--> Google Calendar API: search events by attendee email/phone
    +--> Nutshell: search activities by contact
    |
    v
[Found meeting]
    "I see you have a meeting with [rep] on [date] at [time].
     Would you like to reschedule?"
    |
    v
[Check new availability and rebook]
    +--> Cancel original event
    +--> Book new slot
    +--> Send updated confirmation
    +--> Update Nutshell activity
```

### Cancellation Flow

```
[Caller requests cancellation]
    |
    v
[Confirm cancellation]
    "Just to confirm, you'd like to cancel your meeting with
     [rep] on [date]?"
    |
    v
[Cancel]
    +--> Delete Google Calendar event
    +--> Update Nutshell activity (mark canceled)
    +--> Notify rep via email
    +--> "Your meeting has been canceled. Feel free to call back
          anytime if you'd like to reschedule."
```

### No-Show Handling

If a booked meeting is not attended:
1. Google Calendar event passes without joining
2. Automated follow-up triggered (24 hours later):
   - AI bot calls the contact to reschedule (outbound, if approved)
   - Or: automated email/SMS with rescheduling link
3. Nutshell activity updated: "No-show - follow up required"
4. Task created for rep: "Follow up with [contact] - missed meeting"

---

## API/Integration Details

### Integration Architecture

```
[Voice Bot (Vapi)]
    |
    +---> [Google Calendar API] -- check/book/cancel events
    |         |
    |         +--> OAuth 2.0 Service Account
    |         +--> Scopes: calendar.events, calendar.readonly
    |
    +---> [Nutshell CRM API] -- create contacts, leads, activities
    |         |
    |         +--> API Key auth
    |         +--> Endpoints: contacts, leads, activities
    |
    +---> [Twilio SMS API] -- send confirmations
    |         |
    |         +--> From: same inbound number
    |         +--> $0.0079/message
    |
    +---> [n8n / Make.com] -- workflow orchestration (if needed)
              |
              +--> Calendly API (optional)
              +--> Slack notifications (optional)
              +--> Custom webhook handlers
```

### Authentication Requirements

| Service | Auth Method | Setup |
|---------|-------------|-------|
| Google Calendar | OAuth 2.0 Service Account | One-time setup, no user consent |
| Nutshell CRM | API Key | Generated in Nutshell settings |
| Twilio SMS | Account SID + Auth Token | Existing Twilio account |
| Calendly (optional) | OAuth 2.0 or API Key | Personal access token |
| Vapi | API Key | Dashboard-generated |

---

## Cost Implications

### Monthly Booking Infrastructure Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Google Calendar API | Free | Included with Google Workspace |
| Nutshell Scheduler | Included | Part of Nutshell CRM subscription |
| Nutshell API calls | Included | No per-call API charges |
| Twilio SMS confirmations | ~$8-16/mo | ~1,000-2,000 confirmations at $0.0079/msg |
| Calendly (optional) | $0-12/mo | Free tier or Standard at $12/user/mo |
| n8n (if used) | $0-20/mo | Self-hosted free or cloud at $20/mo |
| **Total booking costs** | **$8-48/mo** | On top of base voice bot costs |

### One-Time Setup Costs
- Google Calendar API setup + OAuth: 2 hours
- Nutshell Scheduler configuration (20 reps): 3 hours
- Calendly setup (if used): 2 hours
- All costs are developer labor (no licensing fees)

---

## Estimated Build Hours

| Component | Hours | Description |
|-----------|-------|-------------|
| Google Calendar API integration | 4-6h | OAuth setup, availability check, event creation |
| Vapi Scheduling Agent prompt | 3-4h | Conversation flow, slot presentation, confirmation |
| Nutshell CRM sync | 3-4h | Contact/lead creation, activity logging |
| SMS confirmation flow | 2-3h | Twilio SMS integration, message templates |
| Rep calendar configuration | 3-4h | 20 calendars, meeting types, buffer times |
| Round-robin logic | 2-3h | Fair distribution, rotation tracking |
| Reschedule/cancel flows | 3-4h | Lookup, modify, notify workflows |
| Calendly integration (optional) | 4-6h | API integration via n8n, Nutshell sync |
| Testing (all booking paths) | 6-8h | Book, reschedule, cancel, no-show, edge cases |
| **Total** | **30-42h** | ~1.5-2 weeks with dedicated developer |

---

## Sources

- [Vapi Google Calendar Integration](https://docs.vapi.ai/tools/google-calendar)
- [Vapi + Google Calendar via n8n](https://n8n.io/workflows/8972-automated-voice-appointment-booking-with-vapi-ai-and-google-calendar/)
- [Nutshell Scheduler](https://www.nutshell.com/crm/meeting-scheduler)
- [Nutshell + Calendly Integration](https://calendly.com/integration/nutshell)
- [Retell AI Calendar Booking](https://www.retellai.com/features/book-appointments)
- [Retell AI + Cal.com](https://www.retellai.com/blog/cal-coms-preset-tools)
- [Bland AI Appointment Scheduling](https://www.bland.ai/blogs/ai-appointment-scheduler)
- [Calendly Inbound Booking with Vapi](https://medium.com/@alozie_igbokwe/building-an-calendly-inbound-appointment-booking-ai-phone-agent-with-vapi-part-3-validating-a-25605eea464b)

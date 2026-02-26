# WhatsApp Business Channel -- OpenClaw Setup Guide

## Why WhatsApp for Your Agency

WhatsApp is the most important client-facing channel for a marketing agency. With over 2 billion users worldwide, it is the messaging platform your clients are most likely to already use. Unlike email, WhatsApp messages get opened within minutes. Unlike phone calls, WhatsApp is asynchronous and creates a written record. For automated client communication -- status updates, approval requests, appointment reminders, lead notifications -- WhatsApp via OpenClaw is extremely effective.

**Key constraint:** WhatsApp Business API is not free. You must use an official Business Solution Provider (BSP) like Twilio, or connect directly through the Meta Cloud API. Twilio is recommended for ease of setup.

---

## Architecture Overview

```
Client sends WhatsApp message
        |
        v
WhatsApp servers (Meta infrastructure)
        |
        v
Twilio (Business Solution Provider)
  - Receives message from WhatsApp
  - Sends webhook POST to your configured URL
        |
        v
Your webhook endpoint (Tailscale Funnel or n8n relay)
        |
        v
OpenClaw WhatsApp Adapter
  - Validates Twilio signature
  - Normalizes message
  - Routes to appropriate agent
        |
        v
Agent processes and responds
        |
        v
OpenClaw sends response via Twilio API
        |
        v
Twilio delivers to WhatsApp
        |
        v
Client receives response on WhatsApp
```

---

## Setup Steps

### Step 1: Create a Twilio Account

1. Go to [twilio.com](https://www.twilio.com) and sign up for an account.
2. Verify your email and phone number.
3. Twilio gives you a free trial with approximately $15 in credit. This is enough for testing.
4. Navigate to the Twilio Console dashboard.
5. Note your **Account SID** and **Auth Token** from the dashboard. You will need both.

### Step 2: Get a WhatsApp-Enabled Phone Number

**For testing (free, immediate):**

1. In the Twilio Console, go to **Messaging > Try it out > Send a WhatsApp message**.
2. Twilio provides a sandbox number (typically `+1 415 523 8886`).
3. To join the sandbox, send "join [your-sandbox-keyword]" from your WhatsApp to this number.
4. The sandbox is limited: only pre-registered numbers can interact with it.
5. Good for development and testing. Not suitable for clients.

**For production (paid, requires approval):**

1. Go to **Phone Numbers > Manage > Buy a Number**.
2. Purchase a number that supports SMS (most US/UK numbers work).
3. Go to **Messaging > Senders > WhatsApp Senders**.
4. Submit a request to enable WhatsApp on your number.
5. You will need a Facebook Business Manager account linked to Meta/WhatsApp.
6. Approval can take 1-5 business days.
7. Once approved, the number can send and receive WhatsApp messages from any WhatsApp user.

### Step 3: Configure the Webhook URL

Twilio needs a publicly accessible URL to send incoming messages to. You have three options:

**Option A: Tailscale Funnel (Recommended)**

```bash
# On your Mac Mini, expose the OpenClaw webhook port
tailscale funnel 443 /webhooks/whatsapp=http://localhost:8080/webhooks/whatsapp

# This creates a public URL like:
# https://mac-mini.tailnet-name.ts.net/webhooks/whatsapp
```

**Option B: n8n Relay**

If you run n8n on a cloud server, create a workflow that:
1. Receives the Twilio webhook via an n8n Webhook node.
2. Forwards the request body to your Mac Mini's OpenClaw instance over Tailscale.
3. Returns the OpenClaw response back to Twilio.

This adds latency but gives you a stable public URL and the ability to log/transform messages in n8n.

**Option C: ngrok (Development Only)**

```bash
ngrok http 8080
# Provides a temporary public URL, changes every restart on free tier
```

**Configure the webhook in Twilio:**

1. Go to **Messaging > Senders > WhatsApp Senders** (or the sandbox configuration if testing).
2. Set "When a message comes in" to your webhook URL: `https://your-domain/webhooks/whatsapp`
3. Set HTTP method to POST.
4. Set "Status callback URL" to `https://your-domain/webhooks/whatsapp/status` (for delivery receipts).

### Step 4: Set Up Message Templates

WhatsApp requires pre-approved templates for any outbound messages (messages you initiate, not replies). This is a WhatsApp policy, not a Twilio limitation.

**Creating a template:**

1. In the Twilio Console, go to **Messaging > Content Template Builder**.
2. Or go to your Meta Business Manager and create templates there.
3. Templates have a name, language, category, and body with variable placeholders.

**Example templates for a marketing agency:**

```
Template: project_status_update
Category: UTILITY
Body: "Hi {{1}}, here's a quick update on your {{2}} project: {{3}}.
       Let me know if you have any questions!"

Template: appointment_reminder
Category: UTILITY
Body: "Hi {{1}}, this is a reminder about your meeting scheduled for
       {{2}} at {{3}}. Reply YES to confirm or RESCHEDULE to change."

Template: lead_notification
Category: UTILITY
Body: "New lead alert for {{1}}: {{2}} ({{3}}) submitted a form on
       your {{4}} campaign. Priority: {{5}}."

Template: monthly_report_ready
Category: UTILITY
Body: "Hi {{1}}, your {{2}} monthly report is ready. Key highlights:
       - Traffic: {{3}}
       - Leads: {{4}}
       - Conversions: {{5}}
       Full report: {{6}}"
```

**Template approval:**
- Templates are reviewed by Meta (usually within 24 hours).
- Keep templates professional and non-promotional for UTILITY category.
- MARKETING category templates have stricter review and higher per-message cost.
- Rejected templates can be edited and resubmitted.

### Step 5: Configure OpenClaw

Set the following environment variables or configuration values:

```bash
# Environment variables for OpenClaw
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=+14155238886     # Your Twilio WhatsApp number
WHATSAPP_WEBHOOK_PATH=/webhooks/whatsapp
WHATSAPP_STATUS_CALLBACK_PATH=/webhooks/whatsapp/status
```

Or in the OpenClaw configuration file:

```yaml
channels:
  whatsapp:
    enabled: true
    provider: twilio
    account_sid: "${TWILIO_ACCOUNT_SID}"
    auth_token: "${TWILIO_AUTH_TOKEN}"
    phone_number: "+14155238886"
    webhook_path: /webhooks/whatsapp
    status_callback_path: /webhooks/whatsapp/status
    default_agent: client-assistant    # Which agent handles WhatsApp messages
    templates:
      project_update: "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # Template SID
      appointment_reminder: "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      lead_notification: "HXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Step 6: Test the Integration

1. Send a WhatsApp message to your Twilio number (or sandbox number).
2. Check the OpenClaw logs for the incoming webhook.
3. Verify the agent receives the normalized message.
4. Confirm the response is delivered back to WhatsApp.
5. Test different message types: text, image, document.
6. Test a template message (outbound initiated by the agent).

---

## Message Types and How They Map

| WhatsApp Message Type | OpenClaw Normalized Type | Notes |
|-----------------------|--------------------------|-------|
| Text | `TextMessage` | Plain text, up to 4096 characters |
| Image | `ImageMessage` | JPEG, PNG. URL provided by Twilio |
| Document | `DocumentMessage` | PDF, DOCX, etc. URL provided by Twilio |
| Audio | `AudioMessage` | Voice notes. Can be transcribed by agent |
| Location | `LocationMessage` | Lat/long coordinates |
| Contact | `ContactMessage` | vCard format |
| Interactive (buttons) | `ActionMessage` | User tapped a button |
| Interactive (list) | `ActionMessage` | User selected from a list |

**Sending rich messages from OpenClaw:**

```yaml
# Agent can send button messages
response:
  type: interactive
  subtype: buttons
  body: "Your campaign report is ready. What would you like to do?"
  buttons:
    - id: view_report
      title: "View Report"
    - id: schedule_call
      title: "Schedule Call"
    - id: ask_question
      title: "Ask Question"

# Agent can send list messages
response:
  type: interactive
  subtype: list
  body: "Select a project to check status:"
  button: "View Projects"
  sections:
    - title: "Active Projects"
      rows:
        - id: proj_1
          title: "Website Redesign"
          description: "Client: Acme Corp"
        - id: proj_2
          title: "SEO Campaign"
          description: "Client: TechStart Inc"
```

---

## Session vs Template Messages

This is a critical concept for WhatsApp Business:

**Session messages (free-form):**
- Available for 24 hours after the customer sends you a message.
- You can send any text, image, document, buttons, lists -- no restrictions.
- The 24-hour window resets every time the customer sends a message.
- No pre-approval needed.

**Template messages (pre-approved):**
- Required when you want to initiate a conversation (no active session) or re-engage after 24 hours.
- Must use a pre-approved template with variable placeholders.
- Cost more per message than session messages.
- Must follow WhatsApp content guidelines.

**Practical implication for your agency:**
- When a client messages you, you have 24 hours of free-form conversation. Your agent can respond naturally.
- To send a proactive status update to a client who hasn't messaged recently, you must use a template.
- Design your workflows so that regular check-ins use templates, and detailed follow-ups happen within the session window.

---

## Cost Breakdown

**Twilio WhatsApp Pricing (as of 2025):**

| Component | Cost |
|-----------|------|
| Twilio phone number | ~$1.00/month |
| Utility conversation (24h window) | $0.005 - $0.025 (varies by country) |
| Marketing conversation (24h window) | $0.02 - $0.08 (varies by country) |
| Authentication conversation | $0.02 - $0.05 |
| Service conversation (customer-initiated) | Free (first 1,000/month), then $0.005 - $0.02 |

**Estimated monthly cost for an agency with 20 active clients:**

```
Phone number:                    $1.00
Customer-initiated (free tier):  $0.00  (first 1,000 conversations)
Utility templates (100/month):   $2.50  (status updates, reminders)
Marketing templates (50/month):  $4.00  (campaigns, reports)
-----------------------------------------------
Estimated total:                 ~$7.50/month
```

This is remarkably cheap for automated client communication.

---

## Use Cases for Your Marketing Agency

### 1. Client Status Updates

Agent proactively sends weekly status updates via template:
- Campaign performance summary
- Action items needing client input
- Upcoming deadlines

### 2. Approval Workflows

Agent sends approval requests via WhatsApp buttons:
- "New blog post draft ready. [Approve] [Request Changes] [View Draft]"
- Client taps a button, agent processes the response
- Much faster than email chains

### 3. Lead Notifications

When a new lead comes in (detected via CRM integration or form webhook):
- Agent sends lead details to client via template
- Client can respond with instructions ("call them", "add to nurture", "not qualified")
- Agent executes the instruction

### 4. Appointment Reminders

- Agent sends reminders 24h and 1h before scheduled calls
- Client confirms or reschedules via quick-reply buttons
- Agent updates the calendar accordingly

### 5. Automated Follow-Up Sequences

- After a client meeting, agent sends follow-up summary
- Scheduled check-ins at defined intervals
- Re-engagement messages for inactive clients

---

## Compliance and Policy

WhatsApp Business has strict policies. Violating them can result in account suspension.

**Mandatory requirements:**

1. **Opt-in:** You must obtain explicit opt-in from contacts before messaging them. Record when and how they opted in.
2. **Opt-out:** Provide a clear way to stop receiving messages (e.g., reply STOP). Honor opt-outs immediately.
3. **No spam:** Do not send unsolicited marketing messages to contacts who have not opted in.
4. **Accurate sender identity:** Your WhatsApp Business profile must accurately represent your business.
5. **Template compliance:** Templates must be truthful, not misleading, and follow Meta content policies.

**Best practices:**
- Always identify yourself/your agency in the first message.
- Keep messages concise and valuable.
- Respect timezone and business hours (configure agent to not send messages at 3am).
- Use UTILITY category for transactional messages, MARKETING only for actual marketing.
- Monitor your Quality Rating in Twilio/Meta dashboards. A low rating reduces your messaging limits.

---

## Alternative: Meta Cloud API (Direct)

Instead of using Twilio as an intermediary, you can connect directly to the WhatsApp Cloud API:

**Pros:**
- Lower per-message cost at scale (Meta charges conversation fees, but no Twilio markup).
- Direct access to all WhatsApp Business API features.
- No middleman.

**Cons:**
- More complex setup (Facebook Developer Account, Business Manager, Graph API).
- You handle webhook verification, signature validation, and API pagination yourself.
- Less documentation and community support compared to Twilio.
- Twilio adds reliability features (automatic retries, status callbacks, queue management).

**Recommendation:** Start with Twilio. It is simpler, well-documented, and the cost difference is minimal for an agency's message volume. Switch to Meta Cloud API later only if you scale to thousands of conversations per month and want to reduce costs.

---

## Testing with Twilio Sandbox

Before committing to a production setup, test everything with the free Twilio sandbox:

1. Go to Twilio Console > Messaging > Try it out > Send a WhatsApp message.
2. Follow the instructions to connect your personal WhatsApp to the sandbox.
3. Configure the sandbox webhook to point to your OpenClaw instance.
4. Send test messages and verify the full round-trip works.
5. Test edge cases: long messages, images, documents, rapid-fire messages.
6. Once satisfied, proceed with a production phone number.

**Sandbox limitations:**
- Only pre-joined numbers can interact with it.
- Cannot send template messages.
- Messages may have "Sent from your Twilio trial account" prefix.
- Not suitable for client-facing use.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not receiving messages | URL not reachable from internet | Verify Tailscale Funnel or n8n relay is running |
| 403 on webhook | Twilio signature validation failing | Check AUTH_TOKEN matches, ensure URL in Twilio matches exactly |
| Messages not delivering | 24h session expired | Use a template message instead of free-form |
| Template rejected | Policy violation | Review Meta template guidelines, adjust content |
| Slow responses | Multiple hops (Twilio > n8n > OpenClaw) | Reduce relay hops, use Tailscale Funnel directly |
| Media not downloading | Twilio media URL expired | Download media immediately on receipt, store locally |
| Rate limited | Too many messages too fast | Implement message queue with backoff |

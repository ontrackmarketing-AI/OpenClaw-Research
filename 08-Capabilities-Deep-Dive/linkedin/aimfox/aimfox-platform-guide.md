# AimFox Platform Guide

## Overview

AimFox is an AI-powered LinkedIn outreach and lead generation platform that automates connection requests, follow-up messaging, and lead management at scale. It layers onto LinkedIn to enable SW Recovery Services to run personalized outreach campaigns across multiple LinkedIn accounts from a single workspace.

For SW Recovery Services, AimFox is a **Phase 2 tool** that sits between LinkedIn (outreach channel) and Nutshell CRM (deal management). It automates the top-of-funnel prospecting workflow: find targets, send personalized connection requests, follow up with message sequences, and push qualified leads into the CRM pipeline.

**Key value proposition**: AimFox replaces manual LinkedIn prospecting (30-60 min/day per rep) with automated, personalized outreach that runs in the background while reps focus on closing deals.

---

## Core Features

### 1. Campaign Types

AimFox supports multiple campaign types to reach prospects through different LinkedIn touchpoints:

| Campaign Type | Description | Best Use Case |
|---------------|-------------|---------------|
| **Search Campaign** | Target prospects from LinkedIn people search results | Broad prospecting by title, industry, location |
| **List Campaign** | Upload custom CSV with LinkedIn profile URLs | ABM campaigns, imported Apollo/enrichment lists |
| **Event Campaign** | Engage attendees of LinkedIn Events you attend | Industry conferences, webinars, trade shows |
| **Post Campaign** | Target users who engaged with specific LinkedIn posts | Warm leads who already showed interest |
| **Multi-Account Campaign** | Run campaigns across multiple LinkedIn accounts simultaneously | Scale across team members |

### Search Campaign Flow
1. Define search criteria (job title, company size, industry, location)
2. AimFox pulls matching LinkedIn profiles
3. Send connection request with personalized note
4. On acceptance: trigger follow-up message sequence
5. On reply: stop sequence, alert rep for manual takeover

### List Campaign with Custom Variables
The most powerful campaign type for ABM (Account-Based Marketing):
- Upload CSV with LinkedIn profile URLs + custom fields (company, deal size, project type)
- Any CSV column becomes a merge variable in message templates
- Example: "Hi {{first_name}}, I noticed {{company}} has been expanding its environmental remediation work..."
- Integrates with Apollo, Clay, or any enrichment tool that exports CSV

### Event Campaign
- Target attendees of industry events (environmental remediation conferences, EPA events)
- Choose between connection request or message request (LinkedIn's built-in intro)
- Event campaigns convert at higher rates because of shared event context
- AimFox automatically detects event attendee lists

---

### 2. Message Sequencing

AimFox supports multi-step follow-up sequences after a connection request is accepted:

**Sequence Structure**:
```
Step 1: Connection Request (with optional note, max 300 chars)
    |
    +--> [Wait for acceptance]
    |
Step 2: Follow-up Message 1 (delay: 1-7 days after acceptance)
    |
    +--> [Wait period]
    |
Step 3: Follow-up Message 2 (delay: 3-7 days after Message 1)
    |
    +--> [Wait period]
    |
Step 4: Follow-up Message 3 (delay: 5-7 days, optional)
    |
    v
[Sequence complete OR reply detected --> stop]
```

**Key Sequencing Rules**:
- Sequences stop immediately when a prospect replies (avoids spammy out-of-context messages)
- Recommended: 2-3 follow-up messages maximum
- Each message can use personalization variables from the prospect's profile or custom CSV data
- Delays between messages should feel natural (not every 24 hours)
- Messages sent during safe hours based on prospect's timezone

**Example Sequence for SW Recovery Services**:

```
Connection Request Note:
"Hi {{first_name}}, I noticed {{company}}'s work in environmental
services. We're helping firms like yours with recovery solutions
that cut project timelines. Would love to connect."

Follow-up 1 (3 days after acceptance):
"Thanks for connecting, {{first_name}}! I wanted to share a quick
case study on how we helped a similar firm reduce remediation costs
by 30%. Would you be open to a 15-minute call this week?"

Follow-up 2 (5 days after Follow-up 1):
"Hi {{first_name}}, just following up on my last message. I know
you're busy — happy to work around your schedule. Here's my
calendar link if that's easier: [link]"
```

---

### 3. AI-Powered Personalization

AimFox uses AI to enhance message personalization:
- Analyzes prospect's LinkedIn profile (headline, summary, recent posts)
- Generates personalized icebreakers
- Adjusts messaging tone based on prospect's industry and seniority
- A/B tests different message variants within campaigns

---

### 4. Unibox (Unified Inbox)

Consolidates all LinkedIn conversations across all connected accounts into a single interface:
- View and respond to all LinkedIn DMs from one place
- Filter by campaign, account, status (replied, interested, not interested)
- Label and tag conversations (hot lead, nurture, not a fit)
- Assign conversations to team members
- Push qualified leads to CRM directly from inbox

---

### 5. Leads Database

Organizes all LinkedIn connections and campaign contacts:
- Categorize leads by status (new, contacted, replied, qualified, converted)
- Apply labels and notes to each lead
- Search and filter by any field
- Export leads to CSV for CRM import
- Track engagement history per lead

---

## Safety Limits and Compliance

### LinkedIn's Enforcement Landscape (2025-2026)

LinkedIn actively detects and restricts automation. The consequences are tiered:

| Violation Level | Consequence | Duration |
|-----------------|-------------|----------|
| **Soft warning** | Temporary action limit reduction | 24-48 hours |
| **Temporary block** | Cannot send connections/messages | Few hours to several days |
| **Account lock** | Must verify identity | 24 hours to several weeks |
| **Permanent ban** | Account terminated | Permanent |

### Safe Daily Limits

| Action | New Account (< 3 months) | Established Account | LinkedIn Premium / Sales Navigator |
|--------|--------------------------|--------------------|------------------------------------|
| **Connection requests** | 10-15/day | 20-30/day | 30-50/day |
| **Messages (1st degree)** | 30-50/day | 50-100/day | 75-150/day |
| **Profile views** | 50-80/day | 100-150/day | 150-250/day |
| **Weekly connection cap** | ~50/week | ~100/week | ~150-200/week |

### AimFox Safety Features

1. **Auto-limit detection**: AimFox checks LinkedIn's allowed maximum daily and never exceeds it
2. **Smart scheduling**: Actions spread throughout the day with random delays (mimics human behavior)
3. **Timezone-aware**: Messages sent during recipient's business hours
4. **Auto-stop on reply**: Sequences halt immediately when prospect responds
5. **Weekly limit awareness**: Distributes connection requests evenly across the week
6. **Activity patterns**: Randomized action intervals, not robotic fixed timing

### Warm-Up Strategy for New Accounts

For new or recently created LinkedIn accounts, a warm-up phase is critical:

| Week | Daily Connections | Daily Messages | Profile Views | Notes |
|------|-------------------|----------------|---------------|-------|
| **Week 1** | 3-5 | 5-10 | 20-30 | Manual activity mixed in |
| **Week 2** | 5-10 | 10-20 | 30-50 | Start first small campaign |
| **Week 3** | 10-15 | 20-40 | 50-80 | Increase gradually |
| **Week 4** | 15-20 | 30-50 | 80-100 | Approaching safe cruising speed |
| **Week 5+** | 20-30 | 50-80 | 100-150 | Full capacity (with Premium) |

**Warm-Up Best Practices**:
- Post content organically during warm-up (signals real user behavior)
- Accept incoming connections (boosts account health)
- Engage with others' posts (likes, comments) manually
- Keep connection request acceptance rate above 30%
- Personalize every connection note (templated spam gets flagged faster)
- Operate at ~50% of maximum allowed to stay safe

---

## API and Integration Details

### AimFox API

**Base URL**: `https://api.aimfox.com` (documented at https://docs.aimfox.com/)

**Authentication**: API Key (generated in Workspace Settings > Integrations)

**Permission Levels**:
- **Read-only**: GET requests only (pull leads, campaign stats)
- **Read-write**: Full access (create campaigns, manage leads, send messages)

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/leads` | GET | List all leads with filters |
| `/leads/{id}` | GET | Get lead details |
| `/leads/{id}/labels` | PUT | Add/update labels on a lead |
| `/leads/{id}/notes` | POST | Add note to a lead |
| `/campaigns` | GET | List all campaigns |
| `/campaigns/{id}` | GET | Campaign details + stats |
| `/campaigns/{id}/leads` | GET | Leads in a specific campaign |
| `/messages` | POST | Send message to a lead |
| `/accounts` | GET | List connected LinkedIn accounts |

### Webhook Events

AimFox webhooks fire on these events (configured in Workspace Settings):

| Event | Trigger | Use Case |
|-------|---------|----------|
| `connection.accepted` | Prospect accepts connection | Create contact in Nutshell CRM |
| `message.received` | Prospect replies to a message | Alert sales rep, create Nutshell activity |
| `message.sent` | Automated message delivered | Log outreach activity |
| `campaign.completed` | Campaign finishes running | Generate summary report |
| `account.login` | LinkedIn account logs in | Health monitoring |
| `account.logout` | LinkedIn account disconnected | Alert for re-authentication |

**Webhook Configuration**:
```json
{
  "url": "https://your-n8n-instance.com/webhook/aimfox",
  "events": ["connection.accepted", "message.received"],
  "auth": {
    "type": "bearer",
    "token": "your-secret-token"
  }
}
```

### CRM Sync Architecture (Nutshell + Later GoHighLevel)

**Current Phase (Phase 2): Nutshell CRM**

```
[AimFox Webhook: connection.accepted]
    |
    v
[n8n / Make.com Workflow]
    |
    +--> Extract lead data (name, company, title, LinkedIn URL)
    +--> Search Nutshell for existing contact
    |
    +--> IF contact exists:
    |       Update contact with LinkedIn profile URL
    |       Log activity: "LinkedIn connection accepted"
    |
    +--> IF new contact:
    |       Create contact in Nutshell
    |       Create lead with source: "LinkedIn Outreach"
    |       Assign to appropriate rep
    |
    v
[AimFox Webhook: message.received (reply)]
    |
    v
[n8n Workflow]
    +--> Update Nutshell lead stage: "Replied"
    +--> Create task for rep: "Follow up with LinkedIn reply from [name]"
    +--> Send Slack notification to rep
```

**Future Phase (Phase 3+): GoHighLevel Migration**

When migrating from Nutshell to GoHighLevel (GHL):
- Replace Nutshell API calls with GHL API calls in n8n workflows
- GHL has native webhook support for inbound data
- Same webhook events from AimFox, different destination endpoints
- AimFox itself does not need reconfiguration -- only the n8n/Make middleware

### Additional Integration Options

| Platform | Integration Method | Purpose |
|----------|-------------------|---------|
| **Zapier** | Native AimFox Zapier app | No-code CRM sync |
| **Make.com** | Native AimFox Make module | Visual workflow automation |
| **n8n** | Via webhooks + HTTP nodes | Self-hosted automation |
| **Slack** | Via webhook chain | Real-time reply notifications |
| **Instantly** | Native integration | Multi-channel (LinkedIn + email) |
| **Apollo** | CSV export -> List campaign | Enriched prospect lists |
| **Clay** | CSV export -> List campaign | AI-enriched targeting |

---

## Implementation Approach

### Phase 2 Rollout Plan

**Week 1: Setup and Configuration**
1. Create AimFox workspace
2. Connect Steven's LinkedIn account (or designated outreach account)
3. Install LinkedIn browser extension (if required)
4. Configure safety limits (conservative: 50% of max)
5. Set up webhook endpoints (n8n or Make.com)
6. Build Nutshell CRM sync workflow

**Week 2: Warm-Up and First Campaign**
1. Begin warm-up protocol (manual activity + small test campaign)
2. Create message templates for environmental remediation prospects
3. Launch test Search Campaign (50 prospects)
4. Monitor acceptance rates and reply rates
5. Adjust messaging based on initial results

**Week 3: Scale and Optimize**
1. Increase daily limits per warm-up schedule
2. Launch List Campaign with Apollo-enriched targets
3. Set up A/B testing on connection request notes
4. Configure Unibox for team inbox management
5. Train team on lead qualification from LinkedIn replies

**Week 4+: Full Production**
1. Run 2-3 concurrent campaigns
2. Add additional LinkedIn accounts (if scaling)
3. Set up Event Campaign for industry events
4. Build Post Campaign around company content engagement
5. Weekly performance review and optimization

### KPIs to Track

| Metric | Target | Source |
|--------|--------|--------|
| Connection request acceptance rate | > 30% | AimFox dashboard |
| Reply rate to sequences | > 10% | AimFox dashboard |
| Leads pushed to Nutshell CRM | 50+/month | Nutshell |
| Meetings booked from LinkedIn | 5-10/month | Calendar |
| LinkedIn account health | No restrictions | AimFox monitoring |
| Cost per qualified lead | < $20 | AimFox cost / qualified leads |

---

## Pricing

### AimFox Plans (as of 2025-2026)

| Plan | Price | Includes |
|------|-------|----------|
| **LinkedIn Outreach** | $99/month per seat | All CRM features, AI outreach, campaigns, Unibox, analytics |
| **14-Day Free Trial** | $0 | Full access to test the platform |

**Per seat** means per LinkedIn account managed. To run outreach from 3 LinkedIn accounts, you need 3 seats ($297/month).

### AppSumo Lifetime Deal (if available)

AimFox has historically offered lifetime deals on AppSumo. Check availability -- these can provide significant savings for small teams.

---

## Cost Implications

### Monthly Costs for SW Recovery Services

| Component | Cost | Notes |
|-----------|------|-------|
| AimFox (1 seat) | $99/mo | One LinkedIn account |
| AimFox (3 seats, team) | $297/mo | Steven + 2 reps |
| LinkedIn Sales Navigator | $99.99/mo per user | Recommended for higher limits + advanced search |
| n8n (CRM sync workflows) | $0-20/mo | Self-hosted free, cloud $20/mo |
| Make.com (alternative) | $9-16/mo | If using Make instead of n8n |
| **Total (1 seat)** | **$199-219/mo** | AimFox + Sales Navigator + automation |
| **Total (3 seats)** | **$597-637/mo** | Full team deployment |

### ROI Projection

| Metric | Conservative | Optimistic |
|--------|-------------|------------|
| Connections/month (1 seat) | 300-400 | 500-700 |
| Replies/month | 30-50 | 60-100 |
| Qualified leads/month | 10-15 | 20-35 |
| Meetings booked/month | 3-5 | 8-15 |
| Average deal size (SW Recovery) | $1M-10M | $10M-50M |
| Cost per meeting | $40-66 | $13-25 |

Even one closed deal per quarter from LinkedIn outreach would represent massive ROI against the $200-600/month investment.

---

## Estimated Build Hours

| Component | Hours | Description |
|-----------|-------|-------------|
| AimFox account setup + LinkedIn connection | 2-3h | Workspace, account linking, safety config |
| Warm-up protocol execution | 8-10h | Spread over 3-4 weeks (monitoring + manual activity) |
| Message template creation | 4-6h | Connection notes, sequence messages, A/B variants |
| CRM sync workflow (n8n/Make) | 6-8h | Webhook setup, Nutshell API, lead routing logic |
| First campaign setup + testing | 3-4h | Search campaign, target selection, launch |
| Unibox configuration + training | 2-3h | Filters, labels, team assignment rules |
| Performance dashboard setup | 2-3h | KPI tracking, weekly report templates |
| Team training (reps) | 2-3h | How to use Unibox, qualify LinkedIn replies |
| **Total** | **29-40h** | ~2 weeks with dedicated setup person |

*Note: The warm-up phase (8-10h) is spread over 3-4 weeks of calendar time, not continuous hours.*

---

## Sources

- [AimFox Platform](https://www.aimfox.com/)
- [AimFox Pricing](https://www.aimfox.com/pricing)
- [AimFox API Documentation](https://docs.aimfox.com/)
- [AimFox Webhooks Documentation](https://docs.aimfox.com/webhooks)
- [AimFox Help Center - Campaigns](https://help.aimfox.com/en/collections/9499726-campaigns)
- [AimFox Campaign Types](https://help.aimfox.com/en/articles/9409015-how-aimfox-campaigns-work)
- [AimFox Event Campaigns](https://help.aimfox.com/en/articles/9411418-event-campaign)
- [AimFox List Campaigns](https://help.aimfox.com/en/articles/9453324-list-campaigns-and-custom-variables)
- [AimFox API Integration Guide](https://help.aimfox.com/en/articles/10162205-aimfox-api-integration)
- [AimFox Make Integration](https://help.aimfox.com/en/articles/11537274-make-integration)
- [LinkedIn Automation Daily Limits 2025](https://blog.closelyhq.com/linkedin-automation-daily-limits-the-2025-safety-guidelines/)
- [LinkedIn Connection Request Limits](https://phantombuster.com/blog/social-selling/linkedin-connection-request-limit/)
- [Safe LinkedIn Automation 2025](https://salesflow.io/blog/the-ultimate-guide-to-safe-linkedin-automation-in-2025)
- [AimFox Review (SalesForge)](https://www.salesforge.ai/directory/sales-tools/aimfox)

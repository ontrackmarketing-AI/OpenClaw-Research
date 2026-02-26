# Expandi Platform Guide: LinkedIn Automation for Lead Generation

## Overview

Expandi is a cloud-based LinkedIn automation platform designed for sales teams, agencies, and lead generation professionals. It automates connection requests, message sequences, profile visits, and follow-ups without requiring browser extensions. Unlike browser-based tools (e.g., AimFox), Expandi runs entirely in the cloud with dedicated IP addresses, enabling 24/7 campaign execution.

For SW Recovery Services, Expandi enables scaled LinkedIn outreach to decision-makers at target companies, complementing the AimFox engagement strategy with automated multi-step sequences. While AimFox focuses on page growth and engagement, Expandi handles direct prospecting and lead generation at scale.

**Key distinction from AimFox**: Expandi is a cloud-based outbound prospecting tool (connection requests, sequences, InMail). AimFox is a browser-based engagement/growth tool (profile visits, endorsements, content engagement). They serve different but complementary purposes.

---

## API / Integration Details

### Webhooks

Expandi uses webhooks to push data to external systems when specific events occur:

**Outbound Webhooks (Expandi --> External)**
| Event Trigger | Data Sent | Use Case |
|--------------|-----------|----------|
| Connection accepted | Lead name, company, title, LinkedIn URL | Add to CRM pipeline |
| Message replied | Lead info + reply content | Alert sales team |
| Profile visited | Lead info | Tracking engagement |
| InMail sent | Lead info + message | Log outreach activity |
| Campaign completed | Campaign summary | Reporting |

**Webhook configuration**:
- Set up in Expandi dashboard under Settings > Webhooks
- Provide destination URL (Zapier webhook, CRM endpoint, etc.)
- Select trigger events
- "Send All At Once" feature with time delta batches webhook fires

**Reversed Webhooks (External --> Expandi)**
- Push data into Expandi campaigns from external systems
- Use case: When GHL CRM marks a lead as "ready for LinkedIn outreach," automatically add them to an Expandi campaign

### CRM Integrations

| Integration | Method | Notes |
|------------|--------|-------|
| HubSpot | Native + Zapier | Direct integration available |
| Pipedrive | Native + Zapier | Direct integration available |
| Salesforce | Zapier | Via webhook |
| GoHighLevel | Zapier | Webhook-based |
| Google Sheets | Zapier | Spreadsheet sync |
| Slack | Zapier | Notifications |
| Microsoft Teams | Zapier | Notifications |
| Gmail / Outlook | Native | Email sequence support |

### Zapier Integration Flow

```
Expandi Campaign Event (webhook)
  --> Zapier Catch Hook
  --> Parse lead data (name, email, company, LinkedIn URL)
  --> Create/update contact in GHL CRM
  --> Assign to pipeline stage
  --> Tag contact with "LinkedIn-Sourced"
  --> Notify sales team via Slack
```

---

## Features Deep Dive

### Smart Sequences

Smart sequences are Expandi's core automation feature, enabling multi-step, multi-channel outreach flows with conditional logic:

```
Step 1: View profile (Day 1)
  |
Step 2: Follow profile (Day 2)
  |
Step 3: Send connection request with personalized note (Day 3)
  |
  ├── IF accepted:
  │   Step 4a: Send welcome message (Day 4, +1 day after accept)
  │   Step 5a: Follow-up message (Day 7, +3 days)
  │   Step 6a: Value-add message with link (Day 10, +3 days)
  │   Step 7a: Final CTA message (Day 14, +4 days)
  │
  └── IF not accepted after 14 days:
      Step 4b: Send InMail (Day 17)
      Step 5b: Send email (if available) (Day 20)
```

**Sequence capabilities**:
- If/then branching based on lead actions (accept, reply, no response)
- Multi-channel: LinkedIn + Email + InMail in single flow
- Time delays between steps (customizable)
- Dynamic personalization (name, company, title, custom fields)
- Image and GIF personalization (visual attachments with lead's name)
- A/B testing for message variants
- Auto-pause when lead replies (prevent awkward overlaps)

### Multi-Account Management

- Manage multiple LinkedIn accounts from a single Expandi dashboard
- Each account gets its own dedicated IP address (country-specific)
- Separate campaigns, sequences, and analytics per account
- Agency dashboard for client account oversight
- Each account requires a separate $99/month subscription

### Account Warm-Up

Expandi's auto warm-up system gradually increases activity to establish account credibility:

| Week | Daily Activity | Notes |
|------|---------------|-------|
| Week 1 | 10-15 connection requests | Building baseline |
| Week 2 | 20-30 connection requests | Gradual increase |
| Week 3 | 40-60 connection requests | Approaching normal |
| Week 4+ | 60-100 connection requests | Full capacity |

**Safety features**:
- Dedicated country-based IP address per account
- Randomized delays between actions (mimics human behavior)
- Smart algorithms to avoid detection patterns
- Automatic daily limits enforcement
- Weekend activity reduction (configurable)
- Blackout hours (no activity during off-hours)

### LinkedIn Safety Limits

| Action | Daily Limit | Expandi Default | Notes |
|--------|------------|----------------|-------|
| Connection requests | 100 max | 60-80 recommended | LinkedIn's weekly limit ~100-200 |
| Profile views | 150-250 | Auto-managed | Varies by account age |
| Messages | 100-150 | Auto-managed | To existing connections |
| InMails | 25-50 | Depends on plan | LinkedIn premium required |
| Follow requests | 100+ | Auto-managed | Lower risk action |

### Campaign Types

| Campaign Type | Description | Best For |
|--------------|-------------|---------|
| Connector | Send connection requests with personalized notes | Initial outreach |
| Messenger | Send messages to existing connections | Follow-up nurturing |
| Open InMail | Send InMails (no connection required) | Premium outreach |
| Profile Visitor | Visit profiles to trigger curiosity | Pre-connection warming |
| Auto-Endorser | Endorse skills to get noticed | Relationship building |
| Smart Sequence | Multi-step flows with branching logic | Full outreach funnel |

### Personalization Features

- **Dynamic fields**: {first_name}, {company_name}, {job_title}, {location}
- **Custom fields**: Import custom data for personalization
- **Image personalization**: Generate images with lead's name/company overlaid
- **GIF personalization**: Custom animated GIFs with lead data
- **Conditional content**: Different message variants based on lead attributes
- **A/B testing**: Test multiple message versions for response rate optimization

---

## Expandi vs AimFox Comparison

| Feature | Expandi | AimFox |
|---------|---------|--------|
| **Architecture** | Cloud-based (runs 24/7) | Browser extension |
| **Primary use** | Outbound prospecting & sequences | Engagement & page growth |
| **Connection requests** | Automated with personalized notes | Automated |
| **Message sequences** | Multi-step smart sequences | Basic messaging |
| **Multi-channel** | LinkedIn + Email + InMail | LinkedIn only |
| **If/then logic** | Advanced branching | Limited |
| **Image/GIF personalization** | Built-in | Not available |
| **Warm-up** | Auto warm-up system | Manual |
| **Safety** | Dedicated IP, human-like delays | Geo-based IP, proxy |
| **Multi-account** | Dashboard for all accounts | Per-browser profile |
| **CRM integration** | Native + Zapier webhooks | Limited |
| **Analytics** | Comprehensive campaign analytics | Basic metrics |
| **Pricing** | $99/month per account | Varies |
| **Best for** | Lead gen, sales sequences | Profile growth, engagement |
| **Risk level** | Lower (cloud, dedicated IP) | Higher (browser extension) |
| **Established track record** | Yes, well-known | Newer, mixed reviews |

**Recommendation**: Use both tools for different purposes:
- **Expandi**: Outbound prospecting campaigns targeting decision-makers
- **AimFox**: Page growth, engagement, and warming up target accounts before Expandi outreach

---

## Implementation Approach

### Phase 1: Account Setup (Week 1)

1. **Create Expandi account**
   - Sign up at expandi.io
   - Connect Steven's LinkedIn account (or team accounts)
   - Select dedicated IP address (US-based)
   - Configure timezone and working hours
   - Set up 2FA for security

2. **Warm-up period**
   - Enable auto warm-up for 2-4 weeks before full campaigns
   - Start with 10-15 connection requests/day
   - Gradually increase over 4 weeks
   - Monitor acceptance rate (target: 30-50%)

### Phase 2: Campaign Setup (Week 2-3)

3. **Build target audiences**
   - Import leads from Sales Navigator searches
   - Upload CSV lists from Apollo or LinkedIn exports
   - Create audience segments by industry/title/company size
   - Exclude existing connections and past contacts

4. **Create smart sequences**
   - Design 3-4 sequence templates for different personas:
     - Template A: Decision-makers at target accounts
     - Template B: Past connections needing re-engagement
     - Template C: Event/conference attendees
     - Template D: Content engagers (people who liked/commented)

5. **Configure integrations**
   - Set up Zapier webhook connection
   - Map Expandi events to GHL CRM actions
   - Configure Slack notifications for replies
   - Set up Google Sheets logging for analytics

### Phase 3: Launch & Optimize (Week 3-4)

6. **Launch initial campaigns**
   - Start with smallest, most targeted audience
   - Monitor acceptance rates and reply rates daily
   - A/B test connection request messages
   - Adjust daily limits based on account health

7. **Optimize sequences**
   - Analyze which steps get highest response rates
   - Optimize timing between steps
   - Test different personalization approaches
   - Refine audience targeting based on results

### Phase 4: Scale (Month 2+)

8. **Multi-account expansion**
   - Add additional team member accounts if needed
   - Coordinate targeting to avoid overlap
   - Unified reporting across accounts
   - Share winning sequence templates

---

## Cost Implications

### Platform Costs

| Item | Cost | Notes |
|------|------|-------|
| Expandi Business plan | $99/month per account | Annual: $79/month |
| Additional accounts | $99/month each | Per LinkedIn account |
| LinkedIn Sales Navigator | $99-$150/month | Required for advanced search |
| Zapier (integrations) | $20-$70/month | Webhook processing |
| LinkedIn Premium (InMail) | $60-$120/month | For InMail campaigns |

### Cost Per Lead Estimate

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Connection acceptance rate | 25-40% | With personalization |
| Reply rate (from connections) | 10-25% | Industry dependent |
| Meeting booking rate | 2-5% | Of total outreach |
| Cost per connection | $0.50-$1.00 | Based on $99/mo + 100-200 connects |
| Cost per reply | $2-$5 | Based on reply rates |
| Cost per meeting | $15-$50 | Based on booking rate |

### Monthly Budget Recommendation

| Configuration | Monthly Cost | Notes |
|--------------|-------------|-------|
| Single account (basic) | $99 + $99 SN = $198 | Minimum viable setup |
| Single account (full) | $99 + $99 SN + $50 Zapier = $248 | With CRM integration |
| 2 accounts (team) | $198 + $99 SN + $50 Zapier = $347 | Expanded outreach |
| 3+ accounts (agency) | $297+ | Custom pricing available |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Expandi account setup and LinkedIn connection | 2 | Account creation, IP selection |
| Warm-up period monitoring (4 weeks) | 4 | Periodic checks, adjustments |
| Target audience building and import | 4-6 | SN searches, CSV prep, upload |
| Smart sequence design (3-4 templates) | 6-8 | Copy, branching logic, timing |
| Zapier/webhook integration to GHL | 4-6 | Webhook setup, field mapping |
| Slack notification setup | 1-2 | Alert configuration |
| Campaign launch and initial optimization | 4-6 | First campaign monitoring |
| A/B testing and iteration | 4-6 | Ongoing over first month |
| Analytics and reporting setup | 3-4 | Dashboard, tracking |
| **Total** | **32-44 hours** | Over 4-6 week ramp period |

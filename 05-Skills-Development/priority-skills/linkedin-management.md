# LinkedIn Management Skill

## Goal

Automate LinkedIn outreach and engagement for Rise Local's B2B prospecting, operating within LinkedIn's Terms of Service and legal boundaries. This skill handles connection requests, messaging sequences, content sharing, and engagement tracking.

---

## Official LinkedIn API Capabilities

### What You CAN Do with the Official API

#### Community Management API (Free with Approved App)

| Capability | Endpoint | Notes |
|------------|----------|-------|
| Get own profile | `GET /v2/me` | Basic profile info |
| Share posts on company page | `POST /v2/ugcPosts` | Text, images, articles, videos |
| Get company page analytics | `GET /v2/organizationalEntityShareStatistics` | Impressions, clicks, engagement |
| Comment on posts | `POST /v2/socialActions/{id}/comments` | On company page posts |
| React to posts | `POST /v2/socialActions/{id}/likes` | Like, celebrate, etc. |

#### Marketing Developer Platform (Requires Approval)

| Capability | Endpoint | Notes |
|------------|----------|-------|
| LinkedIn Ads management | `/v2/adAccounts` | Create/manage ad campaigns |
| Audience targeting | `/v2/adTargetingEntities` | Target by industry, title, company |
| Conversion tracking | `/v2/conversionActions` | Track ad conversions |
| Lead Gen Forms | `/v2/leadGenForms` | Collect leads from LinkedIn ads |
| Reporting | `/v2/adAnalytics` | Ad performance data |

#### Sales Navigator API (Requires Sales Navigator subscription + API access)

| Capability | Endpoint | Notes |
|------------|----------|-------|
| Advanced people search | Proprietary | Search by title, company, industry |
| InMail sending | Proprietary | Send messages to non-connections |
| Lead lists | Proprietary | Save and manage prospect lists |
| Account tracking | Proprietary | Monitor target companies |

### What You CANNOT Do with the Official API

- Send connection requests programmatically (not available via API)
- Send direct messages to connections (not available via standard API)
- Scrape profile data at scale
- Automate personal profile actions (liking, commenting as yourself)
- Access other users' full profile data without consent

---

## Unofficial Automation (Higher Risk)

### Browser Automation Approach

Using Playwright/Puppeteer to automate actions in the LinkedIn web interface:

**What it can do**:
- Send connection requests with personalized notes
- Send direct messages to connections
- View profiles (triggers "viewed your profile" notification)
- Like and comment on posts
- Search for people by criteria
- Extract profile data from search results

**Risks**:
| Risk | Severity | Mitigation |
|------|----------|------------|
| Account suspension | High | Rate limit aggressively, human-like delays |
| Permanent ban | Medium | Use secondary account, not your main |
| Legal action | Low (but real) | Stay under radar, no scraping at scale |
| Detection by LinkedIn | Medium | Randomize timing, use residential proxies |
| CAN-SPAM violations | Medium | Only message opt-in or business contacts |

### Third-Party Tools (Alternative to DIY Automation)

| Tool | What It Does | Cost | Risk Level |
|------|-------------|------|------------|
| **Phantombuster** | LinkedIn scraping, connection requests, messaging | $56-399/month | Medium |
| **Dux-Soup** | Profile visits, connection requests, messaging | $14-55/month | Medium |
| **Expandi** | Cloud-based LinkedIn automation | $99/month | Medium-Low (cloud-based) |
| **LinkedIn Helper** | Browser extension automation | $15-45/month | Medium |
| **Lemlist** | Multi-channel outreach including LinkedIn | $59-129/month | Low (official integrations) |

**IMPORTANT**: All unofficial automation tools violate LinkedIn's Terms of Service. Use at your own risk.

---

## Recommended Approach

### Strategy: Official API + Conservative Manual-Speed Automation + Human Oversight

```
Tier 1: Official API (Zero Risk)
  - Company page content posting and analytics
  - LinkedIn Ads for targeted paid outreach
  - Lead Gen Forms for capturing prospect info
  - Use for Rise Local's company presence and brand building

Tier 2: Semi-Automated with Human Oversight (Low-Medium Risk)
  - Agent prepares connection requests and messages (drafts)
  - Human reviews and sends manually (or clicks "approve" to send)
  - Agent tracks who was contacted and when
  - Agent generates personalized content based on prospect research
  - Strict rate limits: well below LinkedIn's detection thresholds

Tier 3: Automated Browser Actions (Higher Risk, Optional)
  - Only if the user explicitly opts in and accepts the risk
  - Uses Playwright with human-like behavior patterns
  - Residential proxy rotation
  - Random delays between actions (60-300 seconds)
  - Maximum 20-25 connection requests per day
  - Maximum 50 messages per day
  - 8-hour daily activity window (simulating human work hours)
  - Automatic pause if any unusual response from LinkedIn
```

---

## Outreach Workflow Design

### Step 1: Identify Targets

```
Input: Industry, location, title keywords, company size
Source: LinkedIn Sales Navigator search OR enriched lead data from lead-enrichment skill
Output: List of prospects with:
  - Name, title, company
  - LinkedIn profile URL
  - Mutual connections (if any)
  - Recent activity (posts, comments)
  - Company info (size, industry, recent news)
```

### Step 2: Research and Personalize

For each prospect, the agent researches:

```
1. Their LinkedIn profile:
   - Current role and responsibilities
   - Career history
   - Shared connections
   - Recent posts or articles
   - Skills and endorsements

2. Their company:
   - Company LinkedIn page
   - Recent company posts
   - Company website (from enrichment data)
   - Current tech stack (from BuiltWith)
   - Pain signals (from lead scoring)

3. Personalization hooks:
   - Mutual connection to reference
   - Recent post to comment on
   - Shared interest or background
   - Specific pain point based on research
   - Local connection (same city/area)
```

### Step 3: Connection Request (3-Touch Sequence)

**Touch 1: Connection Request (Day 0)**

```
Personalization template:
"Hi [First Name], I noticed [personalization hook - e.g., 'your recent post about
plumbing industry challenges']. I work with [industry] businesses in [city] to
[value proposition]. Would love to connect!"

Character limit: 300 characters
```

**Touch 2: Thank You Message (Day 1-2 after acceptance)**

```
"Thanks for connecting, [First Name]! I was looking at [company name]'s online
presence and noticed [specific observation from enrichment data - e.g., 'your
website loads in 8 seconds, which might be costing you leads'].

I helped [similar business] in [city] improve their [specific metric] by [result].
Would you be open to a quick chat about how we might do something similar for
[company name]?"
```

**Touch 3: Value-Add Follow-Up (Day 5-7 if no response)**

```
"Hi [First Name], I put together a quick analysis of [company name]'s digital
presence compared to your top competitors in [city]. A few things stood out.

Would it be helpful if I shared the highlights? No strings attached -- just
thought it might be useful as you plan for [current quarter/year]."
```

### Step 4: Content Sharing

Between outreach touches, share relevant content on the company page:

```
Content types:
  - Industry tips (e.g., "5 Ways Plumbers Can Get More Leads Online")
  - Case studies (anonymized client results)
  - Local market insights
  - Before/after website transformations
  - Client testimonials (with permission)
  - Industry news with commentary

Posting schedule:
  - 3-5 posts per week
  - Best times: Tuesday-Thursday, 8-10 AM or 12-1 PM
  - Mix of formats: text, image, carousel, video
```

### Step 5: Track Engagement

```
Track for each prospect:
  - Connection request: sent, accepted, pending, rejected
  - Messages: sent, read, replied
  - Content engagement: liked, commented, shared our posts
  - Profile views: did they view our profile after contact?
  - Meeting: scheduled, completed, no-show
  - Outcome: qualified, not interested, nurture, client
```

---

## Safety Limits

### Daily Maximums (Conservative)

| Action | Daily Limit | Rationale |
|--------|-------------|-----------|
| Connection requests | 20-25 | LinkedIn's soft limit is ~100/week; stay well under |
| Messages to connections | 50 | Avoid triggering spam detection |
| Profile views | 80 | Normal browsing pattern |
| Post likes | 30 | Natural engagement level |
| Comments | 10 | Quality over quantity |
| InMails (Sales Nav) | 25 | Plan-dependent limit |
| Company page posts | 2 | Quality content, not spam |

### Weekly Maximums

| Action | Weekly Limit |
|--------|-------------|
| Connection requests | 100 |
| New conversations started | 75 |
| Follow-up messages | 150 |

### Behavioral Patterns (Anti-Detection)

```
1. Random delays between actions:
   - Between connection requests: 120-300 seconds
   - Between messages: 60-180 seconds
   - Between profile views: 30-90 seconds

2. Activity windows:
   - Active only during business hours (8 AM - 6 PM local time)
   - Random start time each day (vary by 30-60 minutes)
   - Lunch break (12-1 PM): reduced activity
   - Never active on weekends (or minimal activity)

3. Gradual ramp-up:
   - Week 1: 5-10 connection requests/day
   - Week 2: 10-15 connection requests/day
   - Week 3: 15-20 connection requests/day
   - Week 4+: 20-25 connection requests/day

4. Account warming:
   - Before automation: spend 1-2 weeks with manual activity
   - Build connection base to 500+ before outreach
   - Engage with content regularly (organic activity)
```

---

## Skill Design: @yourname/linkedin-manager

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/linkedin-manager",
  "version": "1.0.0",
  "description": "LinkedIn outreach management with content posting and engagement tracking",
  "commands": ["/linkedin", "/outreach", "/li-post"],
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": [
          "draft_connection_request",
          "draft_message",
          "generate_post",
          "schedule_post",
          "research_prospect",
          "plan_sequence",
          "track_engagement",
          "generate_report"
        ]
      }
    },
    "optional": {
      "prospect": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "title": { "type": "string" },
          "company": { "type": "string" },
          "linkedin_url": { "type": "string" },
          "enrichment_data": { "type": "object" }
        }
      },
      "post_content": {
        "type": "object",
        "properties": {
          "topic": { "type": "string" },
          "format": { "type": "string", "enum": ["text", "image", "carousel", "article"] },
          "tone": { "type": "string", "enum": ["professional", "conversational", "thought-leader"] }
        }
      },
      "sequence_id": { "type": "string" },
      "date_range": { "type": "object" }
    }
  }
}
```

### Key Functions

**Draft Mode (Recommended Default)**:
The skill generates drafts that a human reviews and sends. This is the safest approach.

```
Agent generates:
  - Personalized connection request text (300 chars max)
  - Follow-up message sequence (3 touches)
  - Content posts for the company page

Human reviews:
  - Approves or edits each piece
  - Sends manually or clicks "approve to send"

Agent tracks:
  - What was sent, when, to whom
  - Responses received
  - Engagement metrics
```

---

## Legal Considerations

### LinkedIn Terms of Service

- **Prohibited**: Automated scraping, automated connection requests, automated messaging
- **Allowed**: Using official APIs as documented, manual use of the platform
- **Gray area**: Browser automation at "human speed" with human oversight

### CAN-SPAM and Business Communication Laws

- Connection requests are NOT emails, so CAN-SPAM does not directly apply
- However, if messages include commercial content, best practices apply
- Always include a way for the recipient to opt out
- Never misrepresent who you are

### Recommendations

1. **Default to draft mode** -- agent prepares, human sends
2. **Keep records** of all outreach for compliance
3. **Include opt-out** in every message sequence: "If this isn't relevant, no worries at all"
4. **Never scrape data** -- use official APIs and enrichment tools for prospect data
5. **Review 09-Legal-Compliance/linkedin-tos.md** for detailed analysis

---

## Integration with Other Skills

```
lead-enrichment skill
  -> Provides prospect data (company info, pain signals, tech stack)
  -> linkedin-manager uses this for personalization

presentation-generator skill
  -> Generates pitch decks referenced in outreach messages
  -> "I put together a quick analysis for [company]..."

ghl-crm skill
  -> Tracks LinkedIn outreach status in GHL pipeline
  -> Creates follow-up tasks when prospects respond
  -> Links LinkedIn conversation to GHL contact record

competitor-scraping skill
  -> Provides competitive intelligence for personalized messaging
  -> "I noticed [competitor] just launched a new website..."
```

---

## Metrics and Reporting

### Key Performance Indicators

| Metric | Target | Calculation |
|--------|--------|-------------|
| Connection acceptance rate | 30-40% | Accepted / Sent |
| Reply rate (1st message) | 15-25% | Replies / Messages sent |
| Meeting booking rate | 5-10% | Meetings / Connections made |
| Content engagement rate | 3-5% | Engagements / Impressions |
| Profile view increase | 50%+ | Week-over-week profile views |
| Lead-to-client conversion | 2-5% | Clients / Total outreach |

### Weekly Report Template

```markdown
## LinkedIn Outreach Report - Week of [Date]

### Connection Requests
- Sent: 85
- Accepted: 34 (40%)
- Pending: 42
- Rejected/Ignored: 9

### Messaging
- First messages sent: 30
- Replies received: 8 (27%)
- Meetings scheduled: 3 (10%)
- Positive responses (interested but not ready): 5

### Content Performance
- Posts published: 4
- Total impressions: 2,340
- Total engagements: 127 (5.4%)
- Profile views this week: 89 (+34% vs last week)

### Pipeline Impact
- New leads added to GHL: 8
- Deals created: 3
- Estimated pipeline value: $4,500

### Top Performing Content
1. "5 Warning Signs Your Website Is Losing Customers" - 890 impressions, 45 engagements
2. [Case study post] - 650 impressions, 38 engagements

### Next Week Plan
- Target: [industry] businesses in [new area]
- Content themes: [upcoming topics]
- Follow-up queue: 12 prospects due for Touch 2
```

---

## Research Gaps

- **LinkedIn API access requirements**: Need to apply for and get approved for Marketing Developer Platform access
- **Sales Navigator API access**: Need to verify pricing and approval process for API access
- **Current detection thresholds**: LinkedIn updates its anti-automation detection regularly; need to monitor current limits
- **Lemlist integration**: Evaluate whether Lemlist's official LinkedIn integration is sufficient to replace browser automation
- **Cost analysis**: Sales Navigator ($99/mo) + automation tool ($50-100/mo) vs. ROI from LinkedIn leads

---

*Last updated: 2026-02-05*
*Status: Skill design complete; legal review pending (see 09-Legal-Compliance/linkedin-tos.md)*

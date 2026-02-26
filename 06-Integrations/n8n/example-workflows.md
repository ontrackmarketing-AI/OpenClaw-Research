# Example Integrated Workflows (OpenClaw + n8n)

> Five production-ready workflow designs that demonstrate OpenClaw and n8n working together.

---

## Workflow 1: Lead Discovery and Enrichment Pipeline

**Purpose:** Find local businesses, enrich them with data, score them, and route to CRM.

### Trigger
- **Scheduled:** Daily at 6:00 AM (n8n Cron trigger)
- **Manual:** OpenClaw agent triggers via MCP tool call
- **Parameters:** Industry (e.g., "dentist"), Location (e.g., "Austin, TX"), Radius (e.g., 25 miles)

### Flow

```
[Cron Trigger / Manual Trigger]
  |
  v
[Google Places Search Node]
  - Input: industry keyword + location + radius
  - Output: list of businesses (name, address, phone, website, rating, reviews, place_id)
  - Pagination: handle nextPageToken for > 20 results
  |
  v
[Function Node: Pre-Filter]
  - Remove permanently closed businesses
  - Remove chains/franchises (name pattern match)
  - Remove businesses outside target area
  - Remove businesses already in database (check Supabase by google_place_id)
  - Output: filtered list of new businesses
  |
  v
[Split In Batches Node: Process 10 at a time]
  |
  v
[HTTP Request Node: Call OpenClaw Enrichment Skill]
  - POST to OpenClaw /api/v1/skills/execute
  - Body: {"skill": "enrich-lead", "input": {"domain": "{{$json.website}}", ...}}
  - Timeout: 120 seconds
  - Retry: 3 attempts
  |
  v
[Function Node: Score Lead]
  - Apply 15-signal pain scoring model
  - Calculate score tier (hot/warm/cold/disqualified)
  - Generate tags array
  |
  v
[Switch Node: Route by Score Tier]
  |
  |-- Hot (80-100):
  |     [GHL Create Contact Node]
  |     [GHL Create Opportunity Node: "New Lead" stage]
  |     [GHL Add Tags Node: "score:hot"]
  |     [Slack Notification Node: "Hot lead: {{$json.company_name}}"]
  |     [GHL Create Task Node: "Call within 1 hour"]
  |
  |-- Warm (60-79):
  |     [GHL Create Contact Node]
  |     [GHL Create Opportunity Node: "New Lead" stage]
  |     [GHL Add Tags Node: "score:warm"]
  |     [GHL Start Workflow Node: warm-nurture-sequence]
  |
  |-- Cold (40-59):
  |     [GHL Create Contact Node]
  |     [GHL Create Opportunity Node: "New Lead" stage]
  |     [GHL Add Tags Node: "score:cold"]
  |     [GHL Start Workflow Node: cold-drip-campaign]
  |
  |-- Disqualified (0-39):
        [Supabase Insert Node: Save to leads table with status "disqualified"]
        [No GHL action]
  |
  v
[Supabase Insert Node: Save all results to leads table]
  |
  v
[Summary Function Node: Count results per tier]
  |
  v
[Slack/Email Notification: "Discovery complete: X hot, Y warm, Z cold, W disqualified"]
```

### Expected Output
- 50-100 businesses discovered per search
- 30-50 after pre-filtering
- 5-8 Hot, 10-15 Warm, 10-15 Cold, 5-10 Disqualified
- All qualified leads in GHL with enriched data
- All results tracked in Supabase

### Error Handling
- Google Places API failure: retry 3x, then alert and skip
- Clay enrichment timeout: mark as "enrichment_incomplete", retry in next run
- GHL contact creation failure: log error, continue with next lead
- Entire workflow failure: send error alert to Slack

---

## Workflow 2: Content Calendar Automation

**Purpose:** OpenClaw generates a content plan, n8n schedules and publishes across platforms.

### Trigger
- **Scheduled:** Weekly (Monday 7:00 AM)
- **Manual:** "Generate content for this week"

### Flow

```
[Cron Trigger: Monday 7:00 AM]
  |
  v
[HTTP Request: Call OpenClaw Content Planning Skill]
  - POST to OpenClaw /api/v1/skills/execute
  - Body: {
      "skill": "generate-content-plan",
      "input": {
        "week_start": "{{$today.format('YYYY-MM-DD')}}",
        "industries": ["dental", "hvac", "legal"],
        "platforms": ["linkedin", "facebook", "blog"],
        "posts_per_platform": 3,
        "content_types": ["educational", "case_study", "industry_news"]
      }
    }
  - Timeout: 300 seconds (content generation takes time)
  |
  v
[Function Node: Parse Content Plan]
  - Extract individual content items from OpenClaw response
  - Each item: title, platform, content_type, draft_copy, publish_date, publish_time
  |
  v
[Split In Batches Node: Process each content item]
  |
  v
[Airtable Create Record Node]
  - Table: Content Calendar
  - Fields:
    - Title: {{$json.title}}
    - Platform: {{$json.platform}}
    - Content Type: {{$json.content_type}}
    - Draft Copy: {{$json.draft_copy}}
    - Publish Date: {{$json.publish_date}}
    - Status: "drafted"
    - Author: "OpenClaw AI"
  |
  v
[IF Node: Is publish date today or tomorrow?]
  |
  |-- Yes (immediate publishing):
  |     [Switch Node: Route by Platform]
  |     |-- LinkedIn:
  |     |     [HTTP Request: LinkedIn API post]
  |     |-- Facebook:
  |     |     [HTTP Request: Facebook Graph API post]
  |     |-- Blog:
  |           [HTTP Request: WordPress API create draft]
  |     [Airtable Update: Status = "published", Published URL = response URL]
  |
  |-- No (future date):
        [Schedule: Set delayed execution for publish date]
        [Or: Buffer API to schedule post]
  |
  v
[Slack Notification: "Content plan for the week created: X posts across Y platforms"]
```

### Expected Output
- 9-15 content pieces planned for the week
- Each saved in Airtable content calendar
- Immediate posts published
- Future posts scheduled via Buffer or platform APIs
- Team notified via Slack

---

## Workflow 3: Competitor Monitoring

**Purpose:** Track competitor changes weekly and alert on significant shifts.

### Trigger
- **Scheduled:** Weekly (Saturday 2:00 AM)

### Flow

```
[Cron Trigger: Saturday 2:00 AM]
  |
  v
[Supabase Query Node: Get all monitored competitors]
  - SELECT DISTINCT competitor_domain, competitor_name, industry
    FROM competitor_data
    WHERE competitor_type = 'direct'
  |
  v
[Split In Batches: Process each competitor]
  |
  v
[HTTP Request Node: Scrape competitor website]
  - Use headless browser or scraping API
  - Capture: page speed, content changes, new pages, pricing changes
  |
  v
[HTTP Request Node: Check Google Rankings]
  - DataForSEO or SEMrush API
  - Get: keyword rankings, organic traffic estimate, backlinks
  |
  v
[HTTP Request Node: Check Google Reviews]
  - Google Places API
  - Get: current rating, new reviews count, review sentiment
  |
  v
[HTTP Request Node: Check Social Media]
  - Get follower counts, recent posts, engagement rates
  |
  v
[Function Node: Build Snapshot]
  - Combine all data into a single snapshot object
  |
  v
[Supabase Insert Node: Save new snapshot]
  - Table: competitor_data
  |
  v
[HTTP Request: Call OpenClaw Analysis Skill]
  - POST to OpenClaw /api/v1/skills/execute
  - Body: {
      "skill": "analyze-competitor-changes",
      "input": {
        "competitor": "{{$json.competitor_name}}",
        "new_snapshot": {{$json.snapshot}},
        "industry": "{{$json.industry}}"
      }
    }
  |
  v
[Function Node: Check for Significant Changes]
  - Rating dropped > 0.3 points?
  - Ranking changed for key terms?
  - New content published?
  - New ad campaigns detected?
  - Social following changed significantly?
  |
  v
[IF Node: Significant changes detected?]
  |
  |-- Yes:
  |     [Email/Slack Alert Node]
  |     Message: "Competitor Update: [name] - [change summary]"
  |     Include: OpenClaw's strategic analysis
  |
  |-- No:
        [No action - quiet week for this competitor]
  |
  v
[After all competitors processed]
  |
  v
[HTTP Request: Call OpenClaw Weekly Summary Skill]
  - Generate aggregate competitor landscape report
  |
  v
[Email Node: Send weekly competitor report to team]
```

---

## Workflow 4: Client Onboarding

**Purpose:** When a deal is won in GHL, automate the onboarding process.

### Trigger
- **GHL Webhook:** `OpportunityStatusUpdate` where status = "won"

### Flow

```
[Webhook Trigger: GHL deal won]
  - Payload: opportunity ID, contact ID, deal value
  |
  v
[GHL API Node: Get full contact details]
  - Retrieve all contact fields, custom fields, tags
  |
  v
[HTTP Request: Call OpenClaw Onboarding Skill]
  - Body: {
      "skill": "generate-onboarding-plan",
      "input": {
        "client": {{$json.contact}},
        "deal_value": {{$json.deal.monetaryValue}},
        "services": {{$json.deal.customFields.services}},
        "industry": {{$json.contact.customFields.industry}}
      }
    }
  |
  v
[OpenClaw Returns: Onboarding plan with deliverables]
  |
  v
[Parallel Execution]
  |
  |-- Branch 1: Welcome Email Sequence
  |     [GHL Start Workflow Node: welcome-email-sequence]
  |     - Email 1: Welcome + what to expect (immediate)
  |     - Email 2: Onboarding questionnaire (day 1)
  |     - Email 3: Kickoff meeting agenda (day 2)
  |
  |-- Branch 2: Internal Setup
  |     [GHL Create Sub-Account Node: New client workspace]
  |     [Airtable Create Record: Client project tracker]
  |     [Airtable Create Record: Client deliverables checklist]
  |
  |-- Branch 3: Team Notification
  |     [Slack Node: #new-clients channel]
  |     Message: "New client: [company_name] - [deal_value] - [services]"
  |     [GHL Create Task: "Schedule kickoff call with [client]"]
  |
  |-- Branch 4: Reporting Setup
  |     [Supabase Insert: New client record]
  |     [Set up automated reporting workflow for this client]
  |
  v
[Merge Node: All branches complete]
  |
  v
[GHL Update Opportunity: Add onboarding start date]
[GHL Add Tag: "status:onboarding"]
```

---

## Workflow 5: Weekly Reporting

**Purpose:** Generate a comprehensive weekly report by pulling data from all integrated systems.

### Trigger
- **Scheduled:** Friday at 4:00 PM

### Flow

```
[Cron Trigger: Friday 4:00 PM]
  |
  v
[Parallel Data Collection]
  |
  |-- Branch 1: Pipeline Data
  |     [GHL API: Get all opportunities]
  |     [Function: Calculate pipeline metrics]
  |       - Total pipeline value
  |       - Deals per stage
  |       - New deals this week
  |       - Deals closed (won/lost)
  |       - Stage conversion rates
  |
  |-- Branch 2: Enrichment Stats
  |     [Supabase Query: Leads enriched this week]
  |     [Supabase Query: Credits used]
  |     [Function: Calculate enrichment metrics]
  |       - Leads discovered
  |       - Leads enriched
  |       - Score distribution (hot/warm/cold/disqualified)
  |       - Credits spent
  |       - Cost per enriched lead
  |
  |-- Branch 3: Content Performance
  |     [Airtable Query: Content published this week]
  |     [Function: Aggregate performance]
  |       - Posts published
  |       - Total views/engagement
  |       - Top performing content
  |
  |-- Branch 4: Activity Metrics
  |     [GHL API: Messages sent/received this week]
  |     [GHL API: Appointments this week]
  |     [Supabase Query: OpenClaw sessions this week]
  |
  v
[Merge Node: Combine all data]
  |
  v
[HTTP Request: Call OpenClaw Report Generation Skill]
  - POST to OpenClaw /api/v1/skills/execute
  - Body: {
      "skill": "generate-weekly-report",
      "input": {
        "pipeline_data": {{$node.pipeline.json}},
        "enrichment_data": {{$node.enrichment.json}},
        "content_data": {{$node.content.json}},
        "activity_data": {{$node.activity.json}},
        "week_ending": "{{$today.format('YYYY-MM-DD')}}"
      }
    }
  |
  v
[OpenClaw Returns: Formatted report with insights and recommendations]
  |
  v
[Function Node: Format as HTML email]
  - Header with logo
  - Executive summary
  - Pipeline section with charts (via QuickChart API)
  - Enrichment section
  - Content section
  - Recommendations section
  |
  v
[Email Node: Send to team@company.com]
  Subject: "Weekly Report - Week of [date] - [total pipeline value]"
  |
  v
[Slack Node: Post summary to #reports channel]
  - Abbreviated version with key metrics
  |
  v
[Supabase Insert: Archive report for historical tracking]
```

### Expected Report Content

```
WEEKLY REPORT - Week of January 1, 2024
========================================

EXECUTIVE SUMMARY
- Pipeline value: $125,000 across 45 active deals
- 12 new leads added this week (4 Hot, 5 Warm, 3 Cold)
- 2 deals closed: $4,500/mo combined
- Content: 8 posts published, 3,200 total views

PIPELINE HEALTH
- New Leads: 18 (+12 this week)
- Contacted: 15 (3 stale)
- Engaged: 8
- Meeting Booked: 4
- Proposal Sent: 3
- Won this week: 2 ($4,500/mo)
- Lost this week: 1

ENRICHMENT EFFICIENCY
- 65 leads discovered
- 38 enriched (27 filtered pre-enrichment)
- Credits used: 380 of 5,000 monthly
- Cost per enriched lead: $0.48
- Score distribution: 4 Hot, 12 Warm, 15 Cold, 7 Disqualified

RECOMMENDATIONS
1. Follow up on 3 stale deals in "Contacted" stage
2. HVAC leads showing higher conversion - increase discovery radius
3. Content about "dental marketing trends" had 5x average engagement
4. Consider increasing Clay credit budget (using 38% of monthly allocation)
```

---

## Workflow Design Principles

### For All Integrated Workflows

1. **Error nodes on every HTTP Request:** Always handle failures gracefully
2. **Timeout configuration:** Set appropriate timeouts (30s for simple, 120s for enrichment, 300s for content generation)
3. **Retry logic:** 3 retries with exponential backoff for transient failures
4. **Logging:** Save execution results to Supabase `sessions` table
5. **Notifications:** Alert on failures, summarize on success
6. **Idempotency:** Design workflows to be safe to re-run (dedup checks, upsert instead of insert)

### n8n Workflow Settings

```json
{
  "settings": {
    "executionTimeout": 600,
    "maxRetries": 3,
    "retryInterval": 5000,
    "saveExecutionProgress": true,
    "saveDataErrorExecution": "all",
    "saveDataSuccessExecution": "all"
  }
}
```

---

## RESEARCH GAPS

- [ ] Build and test each of the 5 workflows in n8n
- [ ] Determine optimal batch sizes for lead processing (10? 25? 50?)
- [ ] Benchmark end-to-end execution time for Workflow 1 (discovery pipeline)
- [ ] Test error recovery: what happens when OpenClaw is unavailable mid-workflow?
- [ ] Create n8n workflow templates that can be imported into any n8n instance
- [ ] Determine if n8n's built-in scheduling is reliable enough for production or if external cron is needed

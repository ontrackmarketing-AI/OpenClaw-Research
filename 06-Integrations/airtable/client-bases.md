# Client-Facing Airtable Bases

## Purpose

Airtable serves as the structured data layer for client deliverables within OpenClaw. Clients receive polished, read-only interfaces into their campaign data, performance metrics, and reports -- all populated and maintained automatically by OpenClaw automation pipelines. This eliminates manual reporting overhead and gives clients real-time visibility into their marketing operations.

---

## Base Templates by Client Type

### 1. Marketing Dashboard Base

**Use case:** Clients running paid ads, SEO campaigns, or multi-channel marketing.

**Tables:**

| Table Name | Fields | Purpose |
|---|---|---|
| Campaigns | Name, Channel (Google/Meta/LinkedIn), Status (Active/Paused/Complete), Start Date, End Date, Budget Allocated, Budget Spent, Linked Metrics | Master list of all campaigns |
| Performance Metrics | Campaign (linked), Date, Impressions, Clicks, CTR, CPC, Conversions, Conversion Rate, ROAS, Cost Per Conversion | Daily/weekly metric snapshots |
| Budget Tracking | Campaign (linked), Month, Planned Spend, Actual Spend, Variance, Variance %, Approval Status | Financial oversight per campaign |
| Channel Summary | Channel, Total Spend MTD, Total Conversions MTD, Blended CPA, Blended ROAS, Trend (Up/Down/Flat) | Rolled-up channel-level view |
| Action Items | Title, Priority (P0-P3), Owner, Status (Open/In Progress/Done), Due Date, Related Campaign | Tasks and recommendations |

**Key formulas:**
- CTR = Clicks / Impressions
- ROAS = Revenue / Ad Spend
- Variance % = (Actual Spend - Planned Spend) / Planned Spend * 100
- Blended CPA = Total Spend / Total Conversions

**Views to expose via Airtable Interface:**
- "Campaign Overview" -- Gallery view with campaign cards showing status and top-line metrics
- "This Month's Performance" -- Grid filtered to current month with conditional formatting on ROAS
- "Budget Health" -- Kanban grouped by variance status (Under Budget / On Track / Over Budget)

### 2. Content Library Base

**Use case:** Clients with ongoing content production (blogs, social, email, video).

**Tables:**

| Table Name | Fields | Purpose |
|---|---|---|
| Content Assets | Title, Type (Blog/Social/Email/Video/Infographic), Status (Idea/Draft/Review/Published/Archived), Author, Created Date, Published Date, URL, Linked Performance | Master content inventory |
| Content Calendar | Asset (linked), Scheduled Date, Channel, Time Slot, Approval Status, Notes | Publication scheduling |
| Performance | Asset (linked), Date, Views, Engagement Rate, Shares, Comments, Leads Generated, Attributed Revenue | Content performance tracking |
| Topics & Keywords | Topic Cluster, Primary Keyword, Search Volume, Difficulty, Current Ranking, Target Ranking, Related Assets (linked) | SEO keyword mapping |
| Brand Guidelines | Element (Voice, Tone, Colors, Fonts), Specification, Examples, Do's, Don'ts | Reference for content creation |

**Views to expose:**
- "Content Pipeline" -- Kanban by status showing what is in each stage
- "Publishing Calendar" -- Calendar view by scheduled date
- "Top Performers" -- Grid sorted by engagement rate, filtered to published content

### 3. Reporting Base

**Use case:** Automated weekly/monthly report data that feeds into Google Slides or PDF generation.

**Tables:**

| Table Name | Fields | Purpose |
|---|---|---|
| Report Periods | Period Name (e.g., "Week of Jan 6"), Start Date, End Date, Report Status (Draft/Final/Sent), Delivery Date | Report lifecycle tracking |
| KPI Snapshots | Period (linked), KPI Name, Current Value, Previous Value, Change %, Target, Status (On Track/At Risk/Off Track) | Point-in-time KPI captures |
| Highlights | Period (linked), Category (Win/Challenge/Recommendation), Description, Supporting Data, Priority | Narrative elements for reports |
| Comparative Data | Period (linked), Metric, This Period, Last Period, Same Period Last Year, QoQ Change, YoY Change | Trend and comparison data |
| Delivery Log | Period (linked), Recipient Email, Delivery Method (Email/Portal/Meeting), Sent Timestamp, Opened (Yes/No) | Tracks report distribution |

**Views to expose:**
- "Latest Report" -- Filtered to most recent period with all KPIs
- "Trend Dashboard" -- Grid showing comparative data across last 12 periods
- "Action Items" -- Filtered highlights showing only recommendations

---

## OpenClaw Automation Pipelines

### Auto-Populate Campaign Metrics

**Trigger:** Scheduled (daily at 6 AM, or on-demand via webhook).

**Flow:**
1. OpenClaw skill `fetch_campaign_metrics` calls GHL API and Google/Meta Ads APIs
2. Data is normalized into a standard schema (campaign, date, impressions, clicks, conversions, spend, revenue)
3. OpenClaw skill `airtable_upsert` pushes rows into the Performance Metrics table
4. Upsert logic: match on (Campaign + Date) -- update if exists, create if new
5. Channel Summary table is recalculated via Airtable rollup fields (no extra API call needed)

**n8n workflow design:**
```
Schedule Trigger (6 AM daily)
  -> HTTP Request: GHL API /campaigns/stats
  -> HTTP Request: Google Ads API /customers/{id}/googleAds:searchStream
  -> HTTP Request: Meta Marketing API /act_{id}/insights
  -> Code Node: normalize all responses to common schema
  -> Airtable Node: upsert to Performance Metrics table
  -> IF Node: check for anomalies (see below)
  -> Slack/Email: send anomaly alerts if triggered
```

**API credentials required:**
- GHL API key (stored in n8n credentials)
- Google Ads API OAuth2 token + developer token
- Meta Marketing API access token + ad account ID
- Airtable personal access token with write scope

### Generate Weekly Summaries

**Trigger:** Every Monday at 7 AM.

**Flow:**
1. OpenClaw skill `airtable_query` pulls last 7 days of Performance Metrics
2. OpenClaw skill `summarize_metrics` runs aggregation: totals, averages, top/bottom performers
3. OpenClaw skill `generate_narrative` uses Claude to write a 3-paragraph summary (wins, challenges, recommendations)
4. OpenClaw skill `airtable_create` inserts a new row in Highlights table with the narrative
5. OpenClaw skill `airtable_update` sets the Report Period status to "Draft"

**Summary template (fed to Claude):**
```
Given the following campaign metrics for {client_name} from {start_date} to {end_date}:
{metrics_json}

Write a concise weekly summary covering:
1. Top 3 wins (biggest improvements or best performers)
2. Top 2 challenges (declining metrics or underperformers)
3. 2-3 specific, actionable recommendations for next week

Use a professional but approachable tone. Reference specific numbers.
```

### Alert on Metric Anomalies

**Detection logic (runs during daily metric population):**

| Anomaly Type | Condition | Severity |
|---|---|---|
| Spend spike | Daily spend > 150% of daily budget | High |
| CTR crash | CTR drops > 40% vs 7-day average | High |
| Conversion drought | Zero conversions for 48+ hours on active campaign | Critical |
| CPC inflation | CPC increases > 30% vs 7-day average | Medium |
| ROAS decline | ROAS drops below 1.0 (spending more than earning) | Critical |
| Impression drop | Impressions drop > 60% vs 7-day average | Medium |

**Alert routing:**
- Critical: Slack DM to account manager + email to client (if opted in) + Airtable Action Item (P0)
- High: Slack channel notification + Airtable Action Item (P1)
- Medium: Airtable Action Item (P2) only, included in next weekly summary

**Implementation:**
```python
def detect_anomalies(current_metrics, historical_metrics):
    anomalies = []
    avg_7d = historical_metrics.rolling(7).mean()

    if current_metrics['spend'] > current_metrics['daily_budget'] * 1.5:
        anomalies.append({
            'type': 'spend_spike',
            'severity': 'high',
            'message': f"Daily spend ${current_metrics['spend']:.2f} exceeds 150% of ${current_metrics['daily_budget']:.2f} budget",
            'campaign': current_metrics['campaign_name']
        })

    if current_metrics['ctr'] < avg_7d['ctr'] * 0.6:
        anomalies.append({
            'type': 'ctr_crash',
            'severity': 'high',
            'message': f"CTR {current_metrics['ctr']:.2%} is down {((avg_7d['ctr'] - current_metrics['ctr']) / avg_7d['ctr'] * 100):.0f}% from 7-day avg",
            'campaign': current_metrics['campaign_name']
        })

    # ... additional checks for each anomaly type

    return anomalies
```

---

## Client-Facing Views via Airtable Interfaces

### Interface Design Principles

1. **No raw tables.** Clients see Interfaces (Airtable's dashboard builder), never the underlying grid.
2. **Top-down hierarchy.** Start with high-level KPIs, allow drill-down into campaigns, then into daily data.
3. **Color coding.** Green for on/above target, yellow for within 10% of target, red for below target.
4. **Limited controls.** Clients can filter by date range and campaign -- nothing else is interactive.

### Standard Interface Layout

**Page 1: Overview Dashboard**
- Header: Client logo, date range selector
- Row 1: 4 number blocks (Total Spend, Total Conversions, Blended CPA, Blended ROAS)
- Row 2: Chart -- spend vs conversions over time (line chart, dual axis)
- Row 3: Channel Summary table (read-only grid)

**Page 2: Campaign Detail**
- Campaign selector (dropdown linked record filter)
- Performance metrics grid for selected campaign
- Budget tracking bar chart (planned vs actual)
- Action items related to selected campaign

**Page 3: Content (if applicable)**
- Content calendar view
- Top performing content list
- Content pipeline kanban (read-only)

**Page 4: Reports Archive**
- List of all generated reports by period
- Each links to the full report PDF or Google Slide deck

---

## Permissions Model

| Role | Access Level | Can View | Can Edit | Notes |
|---|---|---|---|---|
| Client (stakeholder) | Read-only Interface | Interfaces only | Nothing | Shared via Airtable Interface link or email invite |
| Client (power user) | Read-only Base | All tables via grid | Nothing | For clients who want to export/analyze raw data |
| OpenClaw (automation) | Write via API | All tables | All tables | Uses Personal Access Token with `data.records:write` scope |
| Account Manager | Editor | All tables + Interfaces | All tables | Human oversight and manual adjustments |
| Admin (you) | Owner | Everything | Everything | Base creation, schema changes, permission management |

**Security considerations:**
- Airtable Personal Access Tokens are scoped to specific bases -- never use a token with access to all bases
- Rotate tokens quarterly; store in n8n credentials vault or environment variables
- Client Interface links can be password-protected (Airtable Pro/Enterprise feature)
- Audit log: Airtable Enterprise tracks who viewed what -- for smaller plans, log access via OpenClaw

---

## Template Creation Automation

### New Client Onboarding Flow

**Trigger:** New client record created in master CRM (GHL or Supabase).

**Automated steps:**

1. **Clone base template**
   - Use Airtable API: `POST /v0/meta/bases` with `workspaceId` and template configuration
   - Airtable does not natively support base cloning via API, so the workaround is:
     a. Maintain a "Golden Template" base for each client type
     b. Use a script that reads all table schemas from the template base
     c. Creates a new base with identical schema
     d. Copies any static reference data (e.g., brand guidelines, KPI targets)

2. **Customize for client**
   - Rename base to "{Client Name} - Marketing Dashboard"
   - Update Brand Guidelines table with client-specific info
   - Set budget targets in Budget Tracking table
   - Configure campaign names based on client's actual campaigns
   - Set KPI targets in Report Periods based on client goals

3. **Set up automation connections**
   - Store new base ID in client's record in Supabase: `client.airtable_base_id`
   - Create n8n sub-workflow for this client's metric population (parameterized by base ID)
   - Register webhook endpoints for this client's data sources

4. **Create and share Interface**
   - Build Interface pages using Airtable's Interface Designer (manual step for now; can be templated)
   - Generate share link
   - Send onboarding email to client with Interface link and walkthrough video

**Template cloning script (Python pseudocode):**
```python
import requests

AIRTABLE_API = "https://api.airtable.com/v0"
TOKEN = os.environ["AIRTABLE_PAT"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def clone_base_for_client(template_base_id, workspace_id, client_name, client_type):
    # Step 1: Read template schema
    schema = requests.get(
        f"{AIRTABLE_API}/meta/bases/{template_base_id}/tables",
        headers=HEADERS
    ).json()

    # Step 2: Create new base
    new_base = requests.post(
        f"{AIRTABLE_API}/meta/bases",
        headers=HEADERS,
        json={
            "name": f"{client_name} - {client_type} Dashboard",
            "workspaceId": workspace_id,
            "tables": [
                {
                    "name": table["name"],
                    "description": table.get("description", ""),
                    "fields": [
                        {"name": f["name"], "type": f["type"], "options": f.get("options", {})}
                        for f in table["fields"]
                        if f["type"] != "autoNumber"  # skip auto-generated fields
                    ]
                }
                for table in schema["tables"]
            ]
        }
    ).json()

    return new_base["id"]
```

### Template Maintenance

- **Version templates quarterly.** Review schema, add new fields clients have requested, remove unused ones.
- **Changelog:** Track template changes in RAFE Obsidian under `components/airtable-templates.md`.
- **Testing:** After any template change, clone a test base and run the full automation pipeline against it before updating the golden template.

---

## Cost Considerations

| Airtable Plan | Records/Base | Automations | Interfaces | Price/Seat/Month | Notes |
|---|---|---|---|---|---|
| Free | 1,000 | 100 runs/mo | 1 | $0 | Not viable for production |
| Team | 50,000 | 25,000 runs/mo | 10 | $20 | Good for small client bases |
| Business | 125,000 | 100,000 runs/mo | Unlimited | $45 | Recommended for OpenClaw operations |
| Enterprise | 500,000 | 500,000 runs/mo | Unlimited | Custom | Only if scaling past 20+ clients |

**Recommendation:** Start with Business plan ($45/seat/month). With OpenClaw automation handling most writes via API (which do not count against automation run limits), the 125K record limit per base is sufficient for most clients' first year of data. If a client accumulates more, archive old data quarterly.

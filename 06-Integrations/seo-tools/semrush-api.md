# SEMrush API Integration

## Overview

SEMrush is the primary SEO tool for SW Recovery Services -- Steven already has an active subscription. The SEMrush API enables programmatic access to keyword tracking, competitor analysis, ranking monitoring, domain analytics, and backlink auditing. By integrating the API with our n8n automation stack, we can build automated SEO reporting, competitor monitoring alerts, and content optimization workflows.

**Current status:** Steven has an existing SEMrush account. We need to be added as a user to access the API. API access is available on Business ($499.95/month) plans and above, or as a separate add-on.

**Key development:** In October 2025, SEMrush launched "Semrush One" which merges traditional SEO tools with AI Visibility tracking (monitoring how AI chatbots like ChatGPT and Perplexity reference/rank content). This is increasingly relevant for Steven's online presence.

### What We Can Automate
- Weekly/monthly keyword ranking reports delivered to Slack/email
- Competitor movement alerts (new keywords, ranking changes)
- Content gap analysis feeding the blog content pipeline
- Backlink monitoring and toxic link alerts
- Domain health scoring and technical SEO audit triggers

---

## API/Integration Details

### API Access and Authentication

**Base URL:** `https://api.semrush.com/`

**Authentication:** API key passed as a query parameter:
```
https://api.semrush.com/analytics/v1/?key={API_KEY}&type=domain_organic&domain=swrecovery.com
```

**Getting the API key:**
1. Log in to SEMrush
2. Navigate to the API section or subscription management
3. API key is tied to the account subscription
4. Rate limit: 10 requests/second, 10 simultaneous requests

### API Unit System

SEMrush API usage is measured in "API units" rather than flat-rate pricing. Unit costs vary by endpoint and data type:

| Report Type | Live Data Cost | Historical Data Cost |
|-------------|---------------|---------------------|
| Domain Overview (all databases) | 10 units/line | 50 units/line |
| Domain Organic Search Keywords | 10 units/line | 50 units/line |
| Keyword Overview | 10 units/line | 50 units/line |
| Backlinks Overview | 10 units/line | N/A |
| URL Organic Search Keywords | 10 units/line | 50 units/line |

**Unit pricing:** $20-250 per 1 million units depending on volume purchased. Typical small agency usage: 5-20M units/month.

### Core API Endpoints

#### 1. Domain Analytics

**Domain Overview:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=domain_ranks
  &domain=swrecovery.com
```
Returns: organic/paid traffic estimates, keyword counts, backlink counts, authority score.

**Domain Organic Search Keywords:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=domain_organic
  &domain=swrecovery.com
  &database=us
  &display_limit=100
  &display_sort=tr_desc
  &display_filter=%2B|Po|Lt|11
```
Returns: keywords the domain ranks for, position, search volume, traffic estimate, CPC, competition level.

**Useful filters:**
- `%2B|Po|Lt|11` -- position less than 11 (page 1)
- `%2B|Nq|Gt|100` -- search volume greater than 100
- `%2B|Tr|Gt|50` -- traffic estimate greater than 50

#### 2. Keyword Research

**Keyword Overview:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=phrase_all
  &phrase=debt+recovery+services
  &database=us
```
Returns: search volume, CPC, competition, number of results, keyword difficulty.

**Keyword Difficulty:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=phrase_kdi
  &phrase=debt+collection+agency
  &database=us
```
Returns: difficulty score (0-100) estimating effort to rank in top 10.

**Related Keywords:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=phrase_related
  &phrase=debt+recovery
  &database=us
  &display_limit=50
```

#### 3. Competitor Analysis

**Domain vs. Domain (Organic):**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=domain_domains
  &domains=swrecovery.com|vs|competitor1.com|vs|competitor2.com
  &database=us
```
Returns: common keywords, unique keywords per domain, overlap analysis.

**Organic Competitors:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=domain_organic_organic
  &domain=swrecovery.com
  &database=us
  &display_limit=20
```
Returns: list of competing domains with overlap metrics.

#### 4. Position Tracking (Project-Based)

Position Tracking requires a SEMrush Project and uses separate v3 endpoints:

```
GET https://api.semrush.com/management/v1/projects
  ?key={API_KEY}
```

**Get tracking results:**
```
GET https://api.semrush.com/tracking/v1/
  ?key={API_KEY}
  &project_id={PROJECT_ID}
  &type=overview
  &device_type=desktop
```
Returns: daily ranking data for tracked keywords, visibility score, estimated traffic.

**Tracked keyword positions:**
```
GET https://api.semrush.com/tracking/v1/
  ?key={API_KEY}
  &project_id={PROJECT_ID}
  &type=keywords
  &display_limit=100
```

#### 5. Backlink Analytics

**Backlinks Overview:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=backlinks_overview
  &target=swrecovery.com
  &target_type=root_domain
```
Returns: total backlinks, referring domains, authority score, follow/nofollow ratio.

**Backlinks List:**
```
GET https://api.semrush.com/analytics/v1/
  ?key={API_KEY}
  &type=backlinks
  &target=swrecovery.com
  &target_type=root_domain
  &display_limit=100
  &display_sort=page_ascore_desc
```
Returns: individual backlinks with source URL, anchor text, authority score, follow/nofollow, first/last seen dates.

**Toxic Backlinks (Audit):**
The backlink audit is project-based and runs via the SEMrush web interface or project API. The audit scores backlinks on toxicity (0-100) and flags links for disavow review.

### API Version Notes

- **v3 (current primary):** Most complete feature coverage. Used for analytics and project endpoints.
- **v4 (newer, limited):** Newer architecture but fewer reports than v3 currently. Expected to eventually replace v3. Use v3 for now.

---

## Implementation Approach

### N8N Automation Workflows

#### Workflow 1: Weekly Keyword Ranking Report

```
[Schedule Trigger: Monday 8 AM]
  -> [HTTP Request: Domain Organic Keywords (top 50)]
  -> [Filter: position changed vs. last week (compare with Supabase)]
  -> [Store current rankings in Supabase]
  -> [Format Slack message: rankings up/down/new]
  -> [Send to Slack #seo-reports channel]
  -> [Send email summary to Steven]
```

**Supabase table:**
```sql
CREATE TABLE seo_keyword_rankings (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    position INTEGER,
    previous_position INTEGER,
    search_volume INTEGER,
    traffic_estimate NUMERIC,
    url TEXT,
    database TEXT DEFAULT 'us',
    recorded_at DATE DEFAULT CURRENT_DATE,
    UNIQUE(keyword, database, recorded_at)
);
```

#### Workflow 2: Competitor Alert System

```
[Schedule Trigger: Daily 6 AM]
  -> [HTTP Request: Organic Competitors for swrecovery.com]
  -> [Compare with previous competitor list in Supabase]
  -> [Flag: new competitors, competitors gaining keywords]
  -> [HTTP Request: Domain vs Domain for top 3 competitors]
  -> [If significant changes: Slack alert]
  -> [Store competitor data in Supabase]
```

#### Workflow 3: Content Gap Analysis (Monthly)

```
[Schedule Trigger: 1st of month]
  -> [HTTP Request: Competitor organic keywords (top 5 competitors)]
  -> [HTTP Request: Our organic keywords]
  -> [Set Difference: keywords competitors rank for that we don't]
  -> [Filter: search volume > 100, difficulty < 60]
  -> [Store in Supabase "content_opportunities" table]
  -> [Send to content pipeline as blog topic suggestions]
  -> [Slack notification with top 20 opportunities]
```

#### Workflow 4: Backlink Monitor

```
[Schedule Trigger: Weekly]
  -> [HTTP Request: Backlinks Overview]
  -> [Compare metrics with previous week]
  -> [HTTP Request: New backlinks (sorted by date)]
  -> [Flag: lost high-authority backlinks, new toxic backlinks]
  -> [Store in Supabase]
  -> [Alert if authority score drops or toxic score increases]
```

### Integration with Content Pipeline

1. **Keyword-informed content:** SEMrush keyword data feeds the blog content pipeline
   - Content gap keywords become blog topic suggestions
   - Target keyword difficulty < 40 for new content (realistic for smaller sites)
   - Include secondary keywords from "related keywords" endpoint

2. **Post-publish tracking:** After a blog post goes live via WordPress REST API
   - Add target keyword to Position Tracking project
   - Monitor ranking progress over 30/60/90 days
   - Report on which content pieces are gaining traction

3. **SEO meta optimization:** Use keyword data to inform Yoast/Rank Math meta fields
   - Target keyword search volume and competition guide title tag optimization
   - Related keywords inform meta descriptions

### N8N Integration via RapidAPI (Alternative)

Several n8n community templates use SEMrush data via RapidAPI wrappers:
- **Backlink export to Google Sheets** -- automated backlink reporting
- **SEO competitor analysis logging** -- domain overview + organic competitors + keyword insights
- **Traffic tracking** -- website traffic insights via SEMrush Traffic API

These can accelerate initial setup if direct API integration proves complex.

---

## Cost Implications

### SEMrush Subscription (Steven's Existing Account)

| Plan | Monthly Cost | API Units Included | Notes |
|------|-------------|-------------------|-------|
| Pro | $139.95/month | Not included | No API access |
| Guru | $249.95/month | Not included | No API access |
| Business | $499.95/month | Included (varies) | API access included |

**If Steven is on Pro or Guru:** API access requires upgrading to Business ($499.95/month) or purchasing API units separately.

**API unit add-on pricing:**

| Volume | Price per 1M Units |
|--------|-------------------|
| 1M units | $250 |
| 5M units | $200/M ($1,000 total) |
| 10M units | $150/M ($1,500 total) |
| 50M units+ | $20-50/M (enterprise) |

### Estimated Monthly API Usage

| Workflow | Frequency | Est. Lines/Run | Units/Run | Monthly Units |
|----------|-----------|----------------|-----------|---------------|
| Keyword rankings (top 100) | Weekly | 100 | 1,000 | 4,000 |
| Competitor analysis | Daily | 50 | 500 | 15,000 |
| Content gap (5 competitors) | Monthly | 500 | 5,000 | 5,000 |
| Backlink overview | Weekly | 10 | 100 | 400 |
| Backlink list (top 100) | Weekly | 100 | 1,000 | 4,000 |
| Keyword research (ad hoc) | ~20/month | 50 | 500 | 10,000 |
| **Total estimated** | | | | **~38,400 units/month** |

At ~38K units/month, this is well within even the smallest API unit package (1M units = $250). **Actual incremental cost: $0 if on Business plan, ~$250/year for unit add-on if on lower plan.**

### Adding Us as a User

Steven can add team members under his SEMrush subscription:
- Pro: 1 user (additional users $45/month each)
- Guru: 1 user (additional users $80/month each)
- Business: 1 user (additional users $100/month each)

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| API key setup and access verification | 1 | Get added to Steven's account, test API key |
| Supabase schema for SEO data | 2 | Keywords, rankings, competitors, backlinks tables |
| Weekly ranking report workflow (n8n) | 4 | API calls, comparison logic, Slack/email formatting |
| Competitor alert workflow (n8n) | 4 | Daily monitoring, change detection, alerting |
| Content gap analysis workflow (n8n) | 4 | Multi-competitor keyword comparison, opportunity scoring |
| Backlink monitoring workflow (n8n) | 3 | Overview tracking, new/lost link detection |
| Position Tracking project setup | 2 | Configure tracked keywords, devices, locations |
| Content pipeline integration | 3 | Feed keyword data into blog topic suggestions |
| Dashboard/reporting setup | 3 | Supabase views or simple dashboard for Steven |
| Testing and QA | 2 | Verify data accuracy, alert thresholds |
| **Total** | **28** | |

**Dependencies:** SEMrush account access (Steven adds us as user), n8n instance, Supabase instance, Slack workspace for alerts.

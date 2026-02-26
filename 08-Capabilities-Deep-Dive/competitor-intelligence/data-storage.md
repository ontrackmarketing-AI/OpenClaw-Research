# Data Storage for Competitive Intelligence

## Overview

Competitive intelligence generates a large volume of structured and semi-structured data: website snapshots, review counts, SEO rankings, social media metrics, detected changes, and generated alerts. This data needs to be stored reliably, queried efficiently, and presented in client-friendly formats.

This document defines the data model, storage architecture, schemas, retention policy, querying patterns, and client deliverable generation.

---

## Storage Architecture

The system uses a two-layer storage approach:

```
                   +--------------------------+
                   |   Playwright Scrapers    |
                   |   DataForSEO API Calls   |
                   |   Change Detection Logic |
                   +-------------|------------+
                                 |
                                 v
                   +--------------------------+
                   |       SUPABASE           |
                   |  (Primary Data Store)    |
                   |                          |
                   |  - competitors           |
                   |  - competitor_snapshots   |
                   |  - competitor_changes     |
                   |  - competitor_metrics     |
                   |  - competitor_alerts      |
                   +-----------|--------------+
                               |
                      Sync (n8n workflow)
                               |
                               v
                   +--------------------------+
                   |       AIRTABLE           |
                   |  (Client-Facing Views)   |
                   |                          |
                   |  - Competitor Dashboard  |
                   |  - Recent Changes Feed   |
                   |  - Monthly Report Data   |
                   +--------------------------+
```

### Why Two Systems?

| Requirement | Supabase | Airtable |
|---|---|---|
| Complex SQL queries | Excellent (PostgreSQL) | Limited |
| JSONB storage for snapshots | Native support | No |
| Historical data at scale | Handles millions of rows | Slows at 50k+ records |
| Real-time subscriptions | Built-in | Via webhooks only |
| Client-facing dashboards | Requires custom UI | Built-in views, sharing |
| Visual data management | Requires custom UI | Excellent (grid, gallery, kanban) |
| API access for n8n | REST and client libraries | REST API |
| Cost at scale | Predictable (DB storage) | Per-record pricing adds up |

**Decision:** Supabase is the system of record. It stores all raw data, full snapshots, and complete change history. Airtable receives a synced subset -- the most recent metrics, significant changes, and summary data -- formatted for client-facing dashboards and reporting.

---

## Data Model

### Entity Relationship

```
clients (external -- from CRM/main system)
  |
  |-- 1:N --> competitors
                |
                |-- 1:N --> competitor_snapshots  (periodic full data captures)
                |
                |-- 1:N --> competitor_changes    (detected changes with scores)
                |
                |-- 1:N --> competitor_metrics    (time-series metrics)
                |
                |-- 1:N --> competitor_alerts     (generated intelligence alerts)
```

### Table: competitors

The master record for each tracked competitor.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| client_id | UUID (FK) | Client this competitor belongs to |
| name | TEXT | Competitor business name |
| website | TEXT | Primary website URL |
| google_maps_url | TEXT | Google Maps listing URL |
| yelp_url | TEXT | Yelp profile URL |
| bbb_url | TEXT | BBB profile URL |
| facebook_url | TEXT | Facebook page URL |
| instagram_url | TEXT | Instagram profile URL |
| linkedin_url | TEXT | LinkedIn company page URL |
| twitter_url | TEXT | Twitter/X profile URL |
| category | TEXT | Business category (e.g., "Marketing Agency", "Plumber") |
| priority | TEXT | Monitoring priority: P1, P2, P3, P4 |
| notes | TEXT | Free-form notes about this competitor |
| is_active | BOOLEAN | Whether monitoring is currently enabled |
| created_at | TIMESTAMPTZ | When this competitor was added |
| updated_at | TIMESTAMPTZ | Last modification timestamp |

### Table: competitor_snapshots

Full data capture at a point in time. The `data` column is a JSONB blob containing everything scraped from all sources during that run.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| competitor_id | UUID (FK) | References competitors.id |
| snapshot_date | DATE | Date of the snapshot |
| source | TEXT | Source of this snapshot: "full", "website", "google_maps", etc. |
| data | JSONB | Complete scraped data (structure varies by source) |
| content_hash | TEXT | SHA-256 hash of key content for quick change detection |
| created_at | TIMESTAMPTZ | When this snapshot was stored |

**Example `data` JSONB structure:**

```json
{
  "website": {
    "title": "ABC Marketing Agency | Full-Service Digital Marketing",
    "metaDescription": "We help businesses grow with SEO, PPC, social media, and web design.",
    "pages": [
      {
        "url": "https://abcmarketing.com/services",
        "title": "Our Services",
        "headings": ["SEO", "PPC Management", "Social Media Marketing", "Web Design"],
        "contentHash": "a1b2c3d4..."
      },
      {
        "url": "https://abcmarketing.com/pricing",
        "title": "Pricing",
        "pricingData": ["SEO: $1,499/mo", "PPC: $999/mo + ad spend", "Social: $799/mo"],
        "contentHash": "e5f6g7h8..."
      }
    ],
    "teamMembers": [
      { "name": "John Smith", "role": "CEO & Founder" },
      { "name": "Jane Doe", "role": "Director of SEO" }
    ],
    "testimonialCount": 18,
    "techStack": {
      "cms": "WordPress",
      "analytics": "Google Analytics",
      "marketing": "HubSpot",
      "chat": "Intercom"
    }
  },
  "googleMaps": {
    "rating": 4.7,
    "reviewCount": 156,
    "photoCount": 42,
    "recentReviews": [
      {
        "author": "Mike R.",
        "rating": 5,
        "text": "Great agency, helped us double our leads!",
        "date": "2 weeks ago"
      }
    ]
  },
  "social": {
    "facebook": { "followers": 5200, "postsThisMonth": 8, "avgEngagement": 45 },
    "instagram": { "followers": 3100, "postsThisMonth": 12, "avgEngagement": 89 },
    "linkedin": { "followers": 1800, "postsThisMonth": 4 }
  },
  "hiring": {
    "openPositions": 3,
    "roles": ["SEO Specialist", "Account Manager", "Content Writer"],
    "source": "indeed"
  },
  "seo": {
    "domainAuthority": 42,
    "organicKeywords": 1250,
    "topKeywords": [
      { "keyword": "marketing agency phoenix", "position": 3 },
      { "keyword": "seo services phoenix", "position": 7 }
    ]
  }
}
```

### Table: competitor_changes

Individual detected changes with significance scores. Generated by the change detection logic (see `change-monitoring.md`).

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| competitor_id | UUID (FK) | References competitors.id |
| change_type | TEXT | Type of change (e.g., "pricing_change", "new_page", "rating_change") |
| source | TEXT | Data source where change was detected (e.g., "website", "google_maps") |
| description | TEXT | Human-readable description of the change |
| significance | INT | Significance score 1-10 (see change-monitoring.md scoring matrix) |
| details | JSONB | Structured details about the change (previous value, current value, etc.) |
| snapshot_id | UUID (FK) | References the snapshot that triggered this change detection |
| detected_at | TIMESTAMPTZ | When the change was detected |
| acknowledged | BOOLEAN | Whether a human has reviewed this change (default: false) |
| acknowledged_by | TEXT | Who reviewed it |
| acknowledged_at | TIMESTAMPTZ | When it was reviewed |

### Table: competitor_metrics

Time-series metrics for trend analysis. Extracted from snapshots into a flat, queryable format optimized for charting and aggregation.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| competitor_id | UUID (FK) | References competitors.id |
| metric_type | TEXT | Metric category (e.g., "review_count", "rating", "followers_facebook") |
| metric_value | NUMERIC | The numeric value |
| metric_metadata | JSONB | Additional context (e.g., which keyword for ranking metrics) |
| recorded_at | TIMESTAMPTZ | When this metric was recorded |

**Common metric_type values:**

| metric_type | Description | Unit |
|---|---|---|
| review_count_google | Total Google reviews | count |
| rating_google | Google Maps rating | stars (1-5) |
| review_count_yelp | Total Yelp reviews | count |
| rating_yelp | Yelp rating | stars (1-5) |
| followers_facebook | Facebook page followers | count |
| followers_instagram | Instagram followers | count |
| followers_linkedin | LinkedIn followers | count |
| posts_per_week_facebook | Facebook posting frequency | count/week |
| domain_authority | Moz/Ahrefs domain authority | score |
| organic_keywords | Number of organic keywords ranking | count |
| ranking_position | Position for a specific keyword | position (1-100+) |
| open_job_postings | Number of active job listings | count |

### Table: competitor_alerts

Generated intelligence alerts. Links to the changes that triggered them and stores the generated brief.

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique identifier |
| competitor_id | UUID (FK) | References competitors.id |
| client_id | UUID (FK) | Client to notify |
| alert_type | TEXT | "immediate", "daily_digest", "weekly_digest" |
| title | TEXT | Alert headline |
| brief | TEXT | Full intelligence brief (markdown) |
| change_ids | UUID[] | Array of competitor_changes IDs that triggered this alert |
| max_significance | INT | Highest significance score among triggering changes |
| delivered | BOOLEAN | Whether the alert has been sent |
| delivered_at | TIMESTAMPTZ | When the alert was delivered |
| delivered_via | TEXT[] | Channels used: ["email", "slack", "sms"] |
| created_at | TIMESTAMPTZ | When the alert was generated |

---

## Supabase Schema (SQL)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Competitors master table
CREATE TABLE competitors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID NOT NULL,
  name TEXT NOT NULL,
  website TEXT,
  google_maps_url TEXT,
  yelp_url TEXT,
  bbb_url TEXT,
  facebook_url TEXT,
  instagram_url TEXT,
  linkedin_url TEXT,
  twitter_url TEXT,
  category TEXT,
  priority TEXT DEFAULT 'P3' CHECK (priority IN ('P1', 'P2', 'P3', 'P4')),
  notes TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common queries
CREATE INDEX idx_competitors_client ON competitors(client_id);
CREATE INDEX idx_competitors_priority ON competitors(priority);
CREATE INDEX idx_competitors_active ON competitors(is_active);

-- Periodic data snapshots
CREATE TABLE competitor_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,
  source TEXT NOT NULL DEFAULT 'full',
  data JSONB NOT NULL,
  content_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_snapshots_competitor ON competitor_snapshots(competitor_id);
CREATE INDEX idx_snapshots_date ON competitor_snapshots(snapshot_date DESC);
CREATE INDEX idx_snapshots_competitor_date ON competitor_snapshots(competitor_id, snapshot_date DESC);
-- GIN index for JSONB queries
CREATE INDEX idx_snapshots_data ON competitor_snapshots USING GIN (data);

-- Detected changes
CREATE TABLE competitor_changes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL,
  source TEXT,
  description TEXT NOT NULL,
  significance INT NOT NULL CHECK (significance BETWEEN 1 AND 10),
  details JSONB,
  snapshot_id UUID REFERENCES competitor_snapshots(id),
  detected_at TIMESTAMPTZ DEFAULT NOW(),
  acknowledged BOOLEAN DEFAULT false,
  acknowledged_by TEXT,
  acknowledged_at TIMESTAMPTZ
);

CREATE INDEX idx_changes_competitor ON competitor_changes(competitor_id);
CREATE INDEX idx_changes_significance ON competitor_changes(significance DESC);
CREATE INDEX idx_changes_detected ON competitor_changes(detected_at DESC);
CREATE INDEX idx_changes_unacknowledged ON competitor_changes(acknowledged) WHERE acknowledged = false;

-- Time-series metrics (flat table for charting)
CREATE TABLE competitor_metrics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  metric_type TEXT NOT NULL,
  metric_value NUMERIC NOT NULL,
  metric_metadata JSONB,
  recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_competitor_type ON competitor_metrics(competitor_id, metric_type);
CREATE INDEX idx_metrics_recorded ON competitor_metrics(recorded_at DESC);
CREATE INDEX idx_metrics_type_date ON competitor_metrics(metric_type, recorded_at DESC);

-- Generated alerts
CREATE TABLE competitor_alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  client_id UUID NOT NULL,
  alert_type TEXT NOT NULL CHECK (alert_type IN ('immediate', 'daily_digest', 'weekly_digest')),
  title TEXT NOT NULL,
  brief TEXT NOT NULL,
  change_ids UUID[] DEFAULT '{}',
  max_significance INT,
  delivered BOOLEAN DEFAULT false,
  delivered_at TIMESTAMPTZ,
  delivered_via TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_client ON competitor_alerts(client_id);
CREATE INDEX idx_alerts_undelivered ON competitor_alerts(delivered) WHERE delivered = false;
CREATE INDEX idx_alerts_created ON competitor_alerts(created_at DESC);

-- Auto-update the updated_at timestamp on competitors
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_competitors_updated_at
  BEFORE UPDATE ON competitors
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

---

## Row Level Security (RLS)

Supabase supports RLS to ensure clients can only access their own competitive intelligence data. This is critical if you build a client-facing portal.

```sql
-- Enable RLS on all tables
ALTER TABLE competitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_alerts ENABLE ROW LEVEL SECURITY;

-- Policy: clients can only see their own competitors
CREATE POLICY "Clients see own competitors"
  ON competitors FOR SELECT
  USING (client_id = auth.uid());

-- Policy: snapshots visible only for client's competitors
CREATE POLICY "Clients see own snapshots"
  ON competitor_snapshots FOR SELECT
  USING (
    competitor_id IN (
      SELECT id FROM competitors WHERE client_id = auth.uid()
    )
  );

-- Repeat similar policies for changes, metrics, and alerts
-- Service role (used by n8n/backend) bypasses RLS
```

---

## Airtable Sync

An n8n workflow syncs key data from Supabase to Airtable on a schedule (every 6 hours or on significant change).

### Airtable Table Structure

**Competitors (Airtable)**

| Field | Type | Synced From |
|---|---|---|
| Name | Single line text | competitors.name |
| Website | URL | competitors.website |
| Category | Single select | competitors.category |
| Priority | Single select | competitors.priority |
| Google Rating | Number (1 decimal) | Latest snapshot: data.googleMaps.rating |
| Review Count | Number | Latest snapshot: data.googleMaps.reviewCount |
| Facebook Followers | Number | Latest snapshot: data.social.facebook.followers |
| Instagram Followers | Number | Latest snapshot: data.social.instagram.followers |
| Open Jobs | Number | Latest snapshot: data.hiring.openPositions |
| Last Scraped | Date | Latest snapshot: created_at |
| Supabase ID | Single line text | competitors.id (for linking) |

**Recent Changes (Airtable)**

| Field | Type | Synced From |
|---|---|---|
| Competitor | Link to Competitors | competitor_changes.competitor_id |
| Change Type | Single select | competitor_changes.change_type |
| Description | Long text | competitor_changes.description |
| Significance | Number | competitor_changes.significance |
| Detected | Date | competitor_changes.detected_at |
| Status | Single select | "New" / "Reviewed" / "Actioned" |

**Monthly Summary (Airtable)**

| Field | Type | Source |
|---|---|---|
| Competitor | Link to Competitors | Aggregated |
| Month | Date | Aggregated |
| Total Changes | Number | COUNT of changes |
| Significant Changes | Number | COUNT where significance >= 5 |
| Rating Delta | Number | Rating change from month start to end |
| Review Growth | Number | New reviews during month |
| Top Change | Long text | Highest significance change description |

### Sync Workflow (n8n)

```
[Schedule Trigger: every 6 hours]
  |
  v
[Supabase: Query latest metrics per competitor]
  |
  v
[Airtable: Search for existing record by Supabase ID]
  |
  v
[IF: Record exists?]
  |         |
  YES       NO
  |         |
  v         v
[Update]  [Create]
```

---

## Retention Policy

| Data Type | Retention | Archive Strategy |
|---|---|---|
| competitors | Permanent | N/A (master records always kept) |
| competitor_snapshots | 12 months active | Move to cold storage (S3/GCS as gzipped JSON) after 12 months |
| competitor_changes | 24 months active | Archive to cold storage after 24 months |
| competitor_metrics | 24 months active | Aggregate to monthly averages after 12 months, keep aggregates permanently |
| competitor_alerts | 12 months active | Delete after 12 months (change records are the system of record) |

### Archival Process

```sql
-- Archive snapshots older than 12 months
-- Step 1: Export to file (run via script, not SQL)
-- Step 2: Delete from active table
DELETE FROM competitor_snapshots
WHERE snapshot_date < NOW() - INTERVAL '12 months';

-- Aggregate old metrics to monthly averages
INSERT INTO competitor_metrics (competitor_id, metric_type, metric_value, metric_metadata, recorded_at)
SELECT
  competitor_id,
  metric_type,
  AVG(metric_value) AS metric_value,
  jsonb_build_object('aggregation', 'monthly_average', 'sample_count', COUNT(*)) AS metric_metadata,
  DATE_TRUNC('month', recorded_at) AS recorded_at
FROM competitor_metrics
WHERE recorded_at < NOW() - INTERVAL '12 months'
GROUP BY competitor_id, metric_type, DATE_TRUNC('month', recorded_at);

-- Then delete the granular old records
DELETE FROM competitor_metrics
WHERE recorded_at < NOW() - INTERVAL '12 months'
  AND (metric_metadata->>'aggregation') IS NULL;
```

---

## Querying Patterns

### OpenClaw Skill Queries

The `competitor_report` skill uses these queries to generate intelligence for the agent.

**Get competitor overview:**

```javascript
async function getCompetitorOverview(competitorId) {
  // Latest snapshot
  const { data: snapshot } = await supabase
    .from('competitor_snapshots')
    .select('*')
    .eq('competitor_id', competitorId)
    .order('snapshot_date', { ascending: false })
    .limit(1)
    .single();

  // Recent changes (last 30 days)
  const { data: changes } = await supabase
    .from('competitor_changes')
    .select('*')
    .eq('competitor_id', competitorId)
    .gte('detected_at', new Date(Date.now() - 30 * 86400000).toISOString())
    .order('significance', { ascending: false });

  // Key metrics trend (last 6 months)
  const { data: metrics } = await supabase
    .from('competitor_metrics')
    .select('*')
    .eq('competitor_id', competitorId)
    .in('metric_type', ['review_count_google', 'rating_google', 'followers_facebook', 'followers_instagram'])
    .gte('recorded_at', new Date(Date.now() - 180 * 86400000).toISOString())
    .order('recorded_at', { ascending: true });

  return { snapshot: snapshot?.data, changes, metrics };
}
```

**Compare two competitors:**

```javascript
async function compareCompetitors(competitorIdA, competitorIdB) {
  const [overviewA, overviewB] = await Promise.all([
    getCompetitorOverview(competitorIdA),
    getCompetitorOverview(competitorIdB)
  ]);

  return {
    competitorA: overviewA,
    competitorB: overviewB,
    comparison: {
      ratingDiff: (overviewA.snapshot?.googleMaps?.rating || 0) - (overviewB.snapshot?.googleMaps?.rating || 0),
      reviewCountDiff: (overviewA.snapshot?.googleMaps?.reviewCount || 0) - (overviewB.snapshot?.googleMaps?.reviewCount || 0),
      followersDiff: {
        facebook: (overviewA.snapshot?.social?.facebook?.followers || 0) - (overviewB.snapshot?.social?.facebook?.followers || 0),
        instagram: (overviewA.snapshot?.social?.instagram?.followers || 0) - (overviewB.snapshot?.social?.instagram?.followers || 0)
      }
    }
  };
}
```

**Get all competitors for a client with latest metrics:**

```sql
SELECT
  c.id,
  c.name,
  c.website,
  c.priority,
  c.category,
  (
    SELECT data->'googleMaps'->>'rating'
    FROM competitor_snapshots
    WHERE competitor_id = c.id
    ORDER BY snapshot_date DESC
    LIMIT 1
  ) AS current_rating,
  (
    SELECT (data->'googleMaps'->>'reviewCount')::int
    FROM competitor_snapshots
    WHERE competitor_id = c.id
    ORDER BY snapshot_date DESC
    LIMIT 1
  ) AS current_review_count,
  (
    SELECT COUNT(*)
    FROM competitor_changes
    WHERE competitor_id = c.id
      AND detected_at >= NOW() - INTERVAL '30 days'
      AND significance >= 5
  ) AS significant_changes_30d
FROM competitors c
WHERE c.client_id = 'client-uuid-here'
  AND c.is_active = true
ORDER BY c.priority, c.name;
```

---

## Visualization

### Charts from Stored Data

The metrics table supports these chart types for client reports:

**1. Review Growth Over Time (Line Chart)**
```sql
SELECT
  recorded_at::date AS date,
  metric_value AS review_count
FROM competitor_metrics
WHERE competitor_id = 'uuid'
  AND metric_type = 'review_count_google'
  AND recorded_at >= NOW() - INTERVAL '6 months'
ORDER BY date;
```

**2. Rating Comparison Across Competitors (Bar Chart)**
```sql
SELECT
  c.name,
  m.metric_value AS rating
FROM competitor_metrics m
JOIN competitors c ON c.id = m.competitor_id
WHERE c.client_id = 'client-uuid'
  AND m.metric_type = 'rating_google'
  AND m.recorded_at = (
    SELECT MAX(recorded_at)
    FROM competitor_metrics
    WHERE competitor_id = m.competitor_id AND metric_type = 'rating_google'
  )
ORDER BY m.metric_value DESC;
```

**3. Social Media Follower Growth (Multi-line Chart)**
```sql
SELECT
  recorded_at::date AS date,
  metric_type,
  metric_value
FROM competitor_metrics
WHERE competitor_id = 'uuid'
  AND metric_type IN ('followers_facebook', 'followers_instagram', 'followers_linkedin')
  AND recorded_at >= NOW() - INTERVAL '6 months'
ORDER BY date, metric_type;
```

**4. Change Activity Heatmap (Calendar Heatmap)**
```sql
SELECT
  detected_at::date AS date,
  COUNT(*) AS change_count,
  MAX(significance) AS max_significance
FROM competitor_changes
WHERE competitor_id = 'uuid'
  AND detected_at >= NOW() - INTERVAL '12 months'
GROUP BY date
ORDER BY date;
```

Charts can be rendered using:
- **Chart.js** in a client portal
- **Airtable charts** extension for the synced data
- **Google Sheets** via n8n export for simple sharing
- **Python (matplotlib/plotly)** for PDF report generation

---

## Client Deliverable: Monthly Competitive Intelligence Report

The monthly report is the primary client deliverable. It is generated automatically from stored data and reviewed by the account manager before delivery.

### Report Structure

```
MONTHLY COMPETITIVE INTELLIGENCE REPORT
Client: [Client Name]
Period: [Month Year]
Prepared by: [Agency Name] via OpenClaw

EXECUTIVE SUMMARY
- [2-3 sentence overview of the competitive landscape this month]
- [Key takeaway for the client]

COMPETITOR SCORECARD
| Competitor | Rating | Reviews | FB Followers | IG Followers | Changes | Threat Level |
|---|---|---|---|---|---|---|
| Competitor A | 4.7 (=) | 156 (+12) | 5,200 (+300) | 3,100 (+200) | 8 | High |
| Competitor B | 4.3 (-0.1) | 89 (+5) | 2,100 (+50) | 1,800 (+80) | 3 | Medium |
| Competitor C | 4.9 (+0.1) | 210 (+18) | 8,500 (+600) | 5,200 (+400) | 12 | High |

SIGNIFICANT CHANGES THIS MONTH
1. [Competitor A] launched a new PPC management service (Significance: 6/10)
   - Impact: Direct competition with our PPC offering
   - Recommendation: Highlight our PPC case studies and results in upcoming content

2. [Competitor C] increased Google review count by 18 (vs. their avg of 8/month)
   - Impact: Likely running a review generation campaign; widening reputation gap
   - Recommendation: Accelerate client's review generation efforts

3. [Competitor A] hired a Director of SEO from [Known Agency]
   - Impact: Signals investment in SEO capability; expect improved organic presence
   - Recommendation: Strengthen client's technical SEO and content strategy

TREND ANALYSIS
- [Review growth chart: 6-month trend for all competitors]
- [Social media follower growth chart]
- [SEO ranking movement chart for key terms]

RECOMMENDATIONS
1. [Specific action item based on competitive intelligence]
2. [Specific action item based on competitive intelligence]
3. [Specific action item based on competitive intelligence]

APPENDIX
- Full change log for each competitor
- Data sources and methodology
```

### Report Generation Flow

```
[Scheduled trigger: 1st of each month]
  |
  v
[Supabase: Query all data for client's competitors for past month]
  |
  v
[Code Node: Calculate deltas, rankings, summaries]
  |
  v
[AI Node (Claude/GPT): Generate executive summary, analysis, recommendations]
  |
  v
[Chart generation: Create trend charts as images]
  |
  v
[Template: Assemble into formatted report (PDF or Google Doc)]
  |
  v
[Email: Send to account manager for review]
  |
  v
[After review: Send to client]
```

The OpenClaw agent can also generate ad-hoc reports on demand: "Generate a competitive intelligence report for Client X focusing on the past two weeks of changes."

---

## Integration Points

- **Playwright scraping** (`playwright-scraping.md`): Writes snapshots to `competitor_snapshots` and extracted metrics to `competitor_metrics`.
- **Change monitoring** (`change-monitoring.md`): Reads from `competitor_snapshots` to detect changes, writes to `competitor_changes` and `competitor_alerts`.
- **DataForSEO**: SEO metrics are written to `competitor_metrics` with appropriate `metric_type` values.
- **n8n workflows**: Orchestrate the full pipeline -- scrape, store, detect, alert, sync to Airtable, generate reports.
- **OpenClaw skills**: `competitor_report`, `competitor_compare`, `competitor_lookup` all query this data layer.

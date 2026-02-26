# Google Search Console API Integration

## Overview

Google Search Console (GSC) provides direct data from Google about how a site performs in organic search. Unlike SEMrush (which estimates traffic from its own crawl data), GSC provides **actual** click, impression, CTR, and position data as reported by Google. This makes it the authoritative source for search performance metrics.

For SW Recovery Services, the GSC API enables:
- **Performance reporting** -- real clicks, impressions, CTR, and average position by query, page, device, and country
- **URL inspection** -- check how Google sees specific pages (indexing status, crawl info, mobile usability, rich results)
- **Sitemap management** -- programmatically submit and monitor sitemaps
- **Indexing requests** -- notify Google of new or updated content for faster crawling
- **Automated reporting** -- scheduled GSC data pulls feeding dashboards and Slack alerts

GSC data combined with SEMrush data gives a complete SEO picture: GSC for actual performance, SEMrush for competitive intelligence and keyword opportunity discovery.

---

## API/Integration Details

### Authentication: OAuth 2.0

The GSC API requires OAuth 2.0 authentication (no API keys). This involves a one-time setup in Google Cloud Console.

#### Setup Steps

1. **Create a Google Cloud Project:**
   - Go to https://console.cloud.google.com/
   - Create a new project (e.g., "SW Recovery SEO Automation")
   - Enable the "Google Search Console API" in the API Library

2. **Create OAuth 2.0 Credentials:**
   - Navigate to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Application type: "Web application" (for n8n) or "Desktop app" (for scripts)
   - Add authorized redirect URI: `https://your-n8n-instance.com/rest/oauth2-credential/callback`
   - Download the `client_id` and `client_secret`

3. **Configure OAuth Consent Screen:**
   - Set up the consent screen (internal or external)
   - Add scope: `https://www.googleapis.com/auth/webmasters` (read/write) or `https://www.googleapis.com/auth/webmasters.readonly` (read-only)
   - For internal use, "Internal" type avoids Google review

4. **Authorize in n8n:**
   - Create a "Google Search Console" credential in n8n
   - Enter client ID and client secret
   - Click "Sign in with Google" and authorize with Steven's Google account (must be a verified owner/user in GSC)
   - n8n stores the refresh token for ongoing access

#### Scopes

| Scope | Access Level |
|-------|-------------|
| `webmasters.readonly` | Read search analytics, sitemaps, URL inspection |
| `webmasters` | Full read/write (includes sitemap submission, property management) |

**Recommendation:** Use `webmasters` (full access) scope to enable sitemap submission and property management.

### API Endpoints

**Base URL:** `https://searchconsole.googleapis.com/`

#### 1. Search Analytics (Performance Data)

This is the most valuable endpoint -- actual Google search performance data.

**Endpoint:** `POST /webmasters/v3/sites/{siteUrl}/searchAnalytics/query`

**Request body:**
```json
{
  "startDate": "2026-01-01",
  "endDate": "2026-02-13",
  "dimensions": ["query", "page", "device", "country"],
  "dimensionFilterGroups": [{
    "filters": [{
      "dimension": "country",
      "expression": "usa"
    }]
  }],
  "rowLimit": 1000,
  "startRow": 0,
  "dataState": "final",
  "type": "web"
}
```

**Response:**
```json
{
  "rows": [
    {
      "keys": ["debt recovery services", "https://swrecovery.com/services", "DESKTOP", "usa"],
      "clicks": 45,
      "impressions": 1200,
      "ctr": 0.0375,
      "position": 8.2
    }
  ],
  "responseAggregationType": "byProperty"
}
```

**Available dimensions:**
- `query` -- search terms users typed
- `page` -- URL that appeared in results
- `device` -- DESKTOP, MOBILE, TABLET
- `country` -- country code
- `date` -- individual dates (for time series)
- `searchAppearance` -- rich result types (FAQ, review, etc.)

**Data availability:**
- Data is available from 16 months ago up to ~2-3 days ago
- Fresh data may be in "all" state (includes unfinalized data); "final" state is delayed ~3 days
- Maximum 25,000 rows per request (use `startRow` for pagination)

#### 2. URL Inspection

Check how Google indexes and renders a specific URL.

**Endpoint:** `POST /v1/urlInspection/index:inspect`

**Request body:**
```json
{
  "inspectionUrl": "https://swrecovery.com/blog/debt-recovery-tips",
  "siteUrl": "https://swrecovery.com/",
  "languageCode": "en-US"
}
```

**Response includes:**
- Index status (indexed, not indexed, error)
- Crawl status (last crawl date, crawl allowed/blocked)
- Mobile usability (mobile-friendly, issues)
- Rich results (structured data validation)
- Page resource details (referring page, last crawl)

**Rate limits:** 2,000 inspections/day, 600/minute.

**Use cases:**
- Verify new blog posts are indexed after publication
- Debug indexing issues automatically
- Monitor mobile usability across key pages

#### 3. Sitemaps

**List sitemaps:**
```
GET /webmasters/v3/sites/{siteUrl}/sitemaps
```

**Submit a sitemap:**
```
PUT /webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}
```
Example: `PUT /webmasters/v3/sites/https%3A%2F%2Fswrecovery.com/sitemaps/https%3A%2F%2Fswrecovery.com%2Fsitemap.xml`

**Delete a sitemap:**
```
DELETE /webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}
```

**Get sitemap status:**
```
GET /webmasters/v3/sites/{siteUrl}/sitemaps/{feedpath}
```
Returns: last submitted, last downloaded, warnings, errors, indexed URL count vs. submitted count.

#### 4. Indexing API (Separate API)

The Indexing API is a separate Google API (not part of GSC API) that notifies Google about URL changes for faster crawling. Originally limited to job postings and livestream video, but increasingly used for general content.

**Endpoint:** `POST https://indexing.googleapis.com/v3/urlNotifications:publish`

**Request:**
```json
{
  "url": "https://swrecovery.com/blog/new-post",
  "type": "URL_UPDATED"
}
```

**Types:** `URL_UPDATED` (new or changed content), `URL_DELETED` (removed content).

**Rate limit:** 200 requests/day by default (can request increase).

**Authentication:** Requires a Google Cloud service account with Search Console access, not OAuth user credentials.

**Practical note:** The Indexing API is most effective for time-sensitive content. For regular blog posts, normal sitemap submission is sufficient -- Google crawls sitemap-listed URLs within hours to days.

### Sites Management

**List verified properties:**
```
GET /webmasters/v3/sites
```

**Add a site:**
```
PUT /webmasters/v3/sites/{siteUrl}
```

**Remove a site:**
```
DELETE /webmasters/v3/sites/{siteUrl}
```

---

## Implementation Approach

### Phase 2 Integration Plan

#### Step 1: Google Cloud and OAuth Setup
1. Create Google Cloud project with Steven's Google account (or organization account)
2. Enable Search Console API and Indexing API
3. Create OAuth 2.0 credentials
4. Authorize n8n with the credentials
5. Verify API access with a test Search Analytics query

#### Step 2: Automated Performance Reporting (n8n)

**Weekly Performance Report Workflow:**
```
[Schedule Trigger: Monday 7 AM]
  -> [HTTP Request: Search Analytics - last 7 days, by query]
  -> [HTTP Request: Search Analytics - previous 7 days, by query (comparison)]
  -> [Code Node: Calculate week-over-week changes]
  -> [Store in Supabase: weekly_search_performance table]
  -> [Format report: top queries, biggest gainers/losers, total clicks/impressions]
  -> [Send to Slack #seo-reports]
  -> [Send email digest to Steven]
```

**Supabase schema:**
```sql
CREATE TABLE gsc_search_performance (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    page TEXT,
    device TEXT,
    clicks INTEGER,
    impressions INTEGER,
    ctr NUMERIC(6,4),
    position NUMERIC(6,2),
    date DATE NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(query, page, device, date)
);

CREATE TABLE gsc_page_performance (
    id SERIAL PRIMARY KEY,
    page TEXT NOT NULL,
    total_clicks INTEGER,
    total_impressions INTEGER,
    avg_ctr NUMERIC(6,4),
    avg_position NUMERIC(6,2),
    period_start DATE,
    period_end DATE,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Step 3: Post-Publish Index Verification

**New Content Indexing Workflow:**
```
[Webhook: triggered when WordPress publishes a post]
  -> [Wait 24 hours]
  -> [HTTP Request: URL Inspection for the new post URL]
  -> [If not indexed: send Indexing API notification]
  -> [Wait 48 hours]
  -> [HTTP Request: URL Inspection again]
  -> [If still not indexed: Slack alert for manual review]
  -> [Log indexing status to Supabase]
```

#### Step 4: Sitemap Management

1. Ensure WordPress generates an XML sitemap (Yoast SEO or Rank Math handles this)
2. Submit sitemap via API after initial setup
3. Monitor sitemap status weekly:
   - Check indexed vs. submitted URL count
   - Alert if indexed count drops significantly
   - Alert on sitemap errors or warnings

#### Step 5: Combined GSC + SEMrush Reporting

Create a unified SEO dashboard that merges:
- **GSC data:** Actual clicks, impressions, CTR, position (ground truth)
- **SEMrush data:** Estimated traffic, keyword difficulty, competitor rankings (intelligence)

```
[Weekly unified report]
  -> Query: "debt recovery services"
    -> GSC: 45 clicks, 1200 impressions, position 8.2
    -> SEMrush: difficulty 62, volume 2,400, competitor #1 at position 3
    -> Insight: "We're on page 1 but CTR is low. Consider improving title tag."
```

### Data Freshness and Limitations

| Data Type | Freshness | Retention |
|-----------|-----------|-----------|
| Search Analytics | 2-3 day delay (final) | 16 months |
| URL Inspection | Real-time (current Google index) | N/A (live query) |
| Sitemaps | Near real-time | Current state only |
| Indexing API | Processed within hours | N/A (notification only) |

**Row limits:**
- Search Analytics: 25,000 rows per request (paginate with `startRow`)
- URL Inspection: 2,000 requests/day
- Indexing API: 200 requests/day (default)

---

## Cost Implications

| Item | Cost | Notes |
|------|------|-------|
| Google Search Console | Free | Always free from Google |
| Google Search Console API | Free | No per-request charges |
| Google Cloud Project | Free | No charges for API enablement alone |
| Indexing API | Free | No per-request charges |
| OAuth setup | Free | One-time configuration |
| n8n (for automation) | $0 (self-hosted) | Already in the stack |
| Supabase (data storage) | $0-25/month | Free tier likely sufficient for SEO data |

**Total incremental cost: $0**

The GSC API is entirely free. The only costs are the infrastructure to run automation (n8n, Supabase), which are already budgeted in the stack.

### Comparison with Paid Alternatives

Some teams use paid tools to access GSC data more easily:

| Tool | What It Does | Monthly Cost | Our Approach |
|------|-------------|-------------|--------------|
| Databox | GSC dashboard widgets | $72-290/month | Build our own in Supabase/dashboard |
| Supermetrics | GSC -> Google Sheets connector | $29-99/month | n8n does this natively |
| SEOmonitor | GSC + rank tracking | $69-299/month | Already have SEMrush |

**Verdict:** Direct API integration via n8n gives us everything these tools provide at $0 additional cost.

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Google Cloud project and OAuth setup | 2 | Project creation, API enablement, credential generation |
| n8n OAuth credential configuration | 1 | Connect n8n to GSC via OAuth |
| Weekly performance report workflow | 4 | Search Analytics queries, comparison logic, formatting |
| Post-publish indexing workflow | 3 | URL Inspection + Indexing API integration |
| Sitemap monitoring workflow | 2 | Weekly sitemap status checks and alerts |
| Supabase schema for GSC data | 2 | Tables, indexes, views |
| Combined GSC + SEMrush reporting | 3 | Unified dashboard/report merging both data sources |
| Indexing API setup (service account) | 2 | Separate auth for Indexing API |
| Testing and QA | 2 | Verify data accuracy, alert thresholds, pagination |
| **Total** | **21** | |

**Dependencies:** Steven's Google account access (or delegation to our Google account), n8n instance running, Supabase instance, SEMrush integration (for combined reporting), WordPress site live with Yoast/Rank Math for sitemap generation.

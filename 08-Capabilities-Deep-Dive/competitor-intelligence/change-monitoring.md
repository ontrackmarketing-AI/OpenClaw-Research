# Change Monitoring for Competitive Intelligence

## Overview

Competitive intelligence is only valuable if it is current. A one-time snapshot of a competitor's website, reviews, and social media tells you where they are today. Change monitoring tells you where they are going. This document covers how to detect, classify, score, and alert on competitor changes over time.

The core loop is:

1. **Scrape** -- Collect current data (see `playwright-scraping.md`).
2. **Compare** -- Diff current data against the most recent stored snapshot.
3. **Score** -- Assign a significance score to each detected change.
4. **Store** -- Record the change in the `competitor_changes` table (see `data-storage.md`).
5. **Alert** -- Notify the operator or generate an intelligence brief for high-significance changes.
6. **Repeat** -- Run on a schedule appropriate to the competitor's priority.

---

## What to Monitor

### 1. Website Content Changes

**What:** New pages, removed pages, pricing updates, service additions or removals, copy changes, new case studies, new blog posts.

**Why it matters:** A competitor adding a new service page signals market expansion. A pricing change signals repositioning. Removing a service page may indicate they are narrowing focus or abandoning a line of business.

**How to detect:**
- Crawl the full sitemap periodically and compare page lists.
- For key pages (homepage, services, pricing, about), store a content hash and full text. Compare hashes to detect any change, then diff the full text to see what changed.
- Track page titles and meta descriptions for SEO positioning shifts.

**Example diff logic:**

```javascript
const crypto = require('crypto');

function contentHash(text) {
  // Normalize whitespace before hashing to avoid false positives
  const normalized = text.replace(/\s+/g, ' ').trim().toLowerCase();
  return crypto.createHash('sha256').update(normalized).digest('hex');
}

function detectWebsiteChanges(currentSnapshot, previousSnapshot) {
  const changes = [];

  // Compare page lists
  const currentPages = new Set(currentSnapshot.pages.map(p => p.url));
  const previousPages = new Set(previousSnapshot.pages.map(p => p.url));

  for (const url of currentPages) {
    if (!previousPages.has(url)) {
      changes.push({
        changeType: 'new_page',
        description: `New page added: ${url}`,
        significance: 5,
        details: { url }
      });
    }
  }

  for (const url of previousPages) {
    if (!currentPages.has(url)) {
      changes.push({
        changeType: 'removed_page',
        description: `Page removed: ${url}`,
        significance: 5,
        details: { url }
      });
    }
  }

  // Compare content of key pages
  for (const currentPage of currentSnapshot.pages) {
    const previousPage = previousSnapshot.pages.find(p => p.url === currentPage.url);
    if (previousPage) {
      const currentHash = contentHash(currentPage.content);
      const previousHash = contentHash(previousPage.content);

      if (currentHash !== previousHash) {
        const significance = classifyContentChange(currentPage, previousPage);
        changes.push({
          changeType: 'content_changed',
          description: `Content changed on ${currentPage.url}`,
          significance,
          details: {
            url: currentPage.url,
            previousTitle: previousPage.title,
            currentTitle: currentPage.title,
            previousHash,
            currentHash
          }
        });
      }
    }
  }

  return changes;
}

function classifyContentChange(current, previous) {
  // Check for pricing changes (high significance)
  if (current.url.includes('pricing') || current.url.includes('price')) return 8;
  // Check for service page changes
  if (current.url.includes('service')) return 5;
  // Check for title change (moderate)
  if (current.title !== previous.title) return 4;
  // Default: minor content change
  return 2;
}
```

### 2. Google Maps Changes

**What:** Review velocity (new reviews per week), rating changes, new photos uploaded by the business, new Google Posts, updated business hours, new Q&A entries, changes to business description or categories.

**Why it matters:** A sudden spike in new reviews may indicate a review generation campaign. A rating drop may indicate service quality issues. New Google Posts show active local SEO investment. Category changes signal service repositioning.

**What to track specifically:**
- `reviewCount`: Total number of reviews (track delta per period)
- `averageRating`: Overall star rating (track to one decimal)
- `reviewVelocity`: Reviews per week (calculated from reviewCount deltas)
- `photoCount`: Number of photos (new photos = active profile management)
- `googlePostCount`: Number of Google Business Profile posts
- `responseRate`: Percentage of reviews with owner responses

### 3. Social Media Changes

**What:** Posting frequency shifts, new campaign themes, follower growth rate, engagement rate changes, new platform presence (e.g., competitor starts a TikTok account), content type shifts (more video, more carousels).

**Why it matters:** Increased posting frequency or a shift to video content signals a marketing investment. Follower growth rate spikes may indicate paid promotion. A new platform presence signals audience expansion.

**Metrics to track:**
- Posts per week (by platform)
- Follower count (weekly delta and growth rate percentage)
- Average engagement per post (likes + comments + shares / followers)
- Content type distribution (text, image, video, carousel)
- Top-performing posts (for content strategy analysis)

### 4. Technology Stack Changes

**What:** CMS changes (switched from WordPress to Webflow), new marketing tools (added HubSpot tracking, switched to Klaviyo), new analytics tools, new chat widgets, new forms providers.

**Why it matters:** Technology changes reveal strategic shifts. Adopting HubSpot suggests an inbound marketing strategy. Switching from WordPress to a headless CMS suggests a focus on performance and modern development. Adding a chat widget suggests a lead capture focus.

**How to detect:**
- **BuiltWith API:** Provides technology profiles for any website and can send change alerts.
- **Wappalyzer (open source):** Detect technologies by analyzing page source, headers, and JavaScript globals.
- **Manual check:** Look for common script tags, meta tags, and cookies.

```javascript
async function detectTechStack(page) {
  const techSignals = {};

  // Check for common platforms
  const pageSource = await page.content();

  // CMS detection
  if (pageSource.includes('wp-content')) techSignals.cms = 'WordPress';
  else if (pageSource.includes('Squarespace')) techSignals.cms = 'Squarespace';
  else if (pageSource.includes('wix.com')) techSignals.cms = 'Wix';
  else if (pageSource.includes('webflow')) techSignals.cms = 'Webflow';
  else if (pageSource.includes('shopify')) techSignals.cms = 'Shopify';

  // Analytics detection
  if (pageSource.includes('gtag') || pageSource.includes('google-analytics')) techSignals.analytics = 'Google Analytics';
  if (pageSource.includes('hotjar')) techSignals.heatmapping = 'Hotjar';
  if (pageSource.includes('segment.com') || pageSource.includes('analytics.js')) techSignals.cdp = 'Segment';

  // Marketing tools
  if (pageSource.includes('hubspot')) techSignals.marketing = 'HubSpot';
  if (pageSource.includes('marketo')) techSignals.marketing = 'Marketo';
  if (pageSource.includes('mailchimp')) techSignals.email = 'Mailchimp';
  if (pageSource.includes('klaviyo')) techSignals.email = 'Klaviyo';

  // Chat widgets
  if (pageSource.includes('intercom')) techSignals.chat = 'Intercom';
  if (pageSource.includes('drift')) techSignals.chat = 'Drift';
  if (pageSource.includes('tawk.to')) techSignals.chat = 'Tawk.to';
  if (pageSource.includes('livechat')) techSignals.chat = 'LiveChat';

  return techSignals;
}
```

### 5. SEO Changes

**What:** Ranking position changes for target keywords, new keywords the competitor is ranking for, lost keywords, new backlinks acquired, domain authority changes, new content published.

**Why it matters:** SEO changes directly impact market visibility. A competitor climbing for your client's top keywords is an immediate competitive threat. New content targeting new keywords signals expansion into new topics or markets.

**How to detect:**
- **DataForSEO API:** Track keyword rankings, backlinks, and organic visibility over time. DataForSEO provides historical data and ranking change alerts.
- **Regular rank tracking:** Query DataForSEO weekly for a set of tracked keywords and store the positions.

```javascript
async function trackSEOChanges(competitorDomain, keywords) {
  // Using DataForSEO SERP API
  const results = [];

  for (const keyword of keywords) {
    const response = await fetch('https://api.dataforseo.com/v3/serp/google/organic/live/advanced', {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(`${DATAFORSEO_LOGIN}:${DATAFORSEO_PASSWORD}`).toString('base64')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify([{
        keyword,
        location_code: 2840, // United States
        language_code: 'en',
        device: 'desktop'
      }])
    });

    const data = await response.json();
    const items = data.tasks?.[0]?.result?.[0]?.items || [];

    const competitorResult = items.find(item =>
      item.type === 'organic' && item.domain === competitorDomain
    );

    results.push({
      keyword,
      position: competitorResult?.rank_absolute || null,
      url: competitorResult?.url || null,
      title: competitorResult?.title || null
    });
  }

  return results;
}
```

### 6. Advertising Changes

**What:** New ads appearing in Meta (Facebook/Instagram) Ad Library, new Google Ads visible in the Google Ads Transparency Center, ad copy changes, new creative assets, estimated ad spend changes.

**Why it matters:** Advertising activity reveals where a competitor is investing budget and what messages they are testing. A competitor launching Google Ads for keywords they previously only targeted organically signals escalation. New Facebook ad creatives reveal their positioning and offers.

**How to monitor:**
- **Meta Ad Library** (`facebook.com/ads/library`): Search by advertiser name. All active ads are publicly visible. Scrape periodically to track new creatives and ad duration.
- **Google Ads Transparency Center** (`adstransparency.google.com`): Search by advertiser. Shows all active and recent ads across Google properties.
- **DataForSEO:** Provides paid search data including ad copies and estimated spend.

### 7. Team Changes

**What:** New hires, departures, leadership changes, organizational restructuring.

**Why it matters:** A competitor hiring a VP of Sales signals aggressive growth. A competitor losing their lead developer may indicate internal problems. Hiring patterns reveal strategic priorities (see `playwright-scraping.md` job board section).

**How to monitor:**
- LinkedIn company pages show recent hires publicly.
- Job posting analysis (covered in `playwright-scraping.md`).
- Press releases announcing leadership changes.

### 8. Press and News Mentions

**What:** Press releases, news articles mentioning the competitor, award announcements, partnership announcements, funding rounds.

**Why it matters:** Press activity reveals strategic moves -- partnerships, market expansions, product launches, or crises. A competitor winning a "Best Agency" award strengthens their positioning. A lawsuit or negative press may present an opportunity.

**How to monitor:**
- **Google Alerts:** Free. Set up alerts for competitor brand names. Delivers email digests.
- **News API / Google News scraping:** Programmatic monitoring for higher volume.
- **Industry publication monitoring:** Track relevant blogs and news sites via RSS.

---

## Monitoring Methods

### Periodic Scraping + Diff (Primary Method)

This is the core approach for most data sources. Scrape the current state, compare to the previous stored snapshot, and record differences.

```javascript
async function monitorCompetitor(competitorId) {
  // 1. Get previous snapshot from Supabase
  const { data: previousSnapshot } = await supabase
    .from('competitor_snapshots')
    .select('*')
    .eq('competitor_id', competitorId)
    .order('snapshot_date', { ascending: false })
    .limit(1)
    .single();

  // 2. Scrape current data
  const currentData = await scrapeAllSources(competitorId);

  // 3. Store new snapshot
  const { data: newSnapshot } = await supabase
    .from('competitor_snapshots')
    .insert({
      competitor_id: competitorId,
      snapshot_date: new Date().toISOString().split('T')[0],
      data: currentData
    })
    .select()
    .single();

  // 4. Detect changes
  if (previousSnapshot) {
    const changes = detectAllChanges(currentData, previousSnapshot.data);

    // 5. Store changes
    if (changes.length > 0) {
      await supabase
        .from('competitor_changes')
        .insert(changes.map(change => ({
          competitor_id: competitorId,
          change_type: change.changeType,
          description: change.description,
          significance: change.significance,
          detected_at: new Date().toISOString()
        })));
    }

    // 6. Alert on significant changes
    const significantChanges = changes.filter(c => c.significance >= 5);
    if (significantChanges.length > 0) {
      await generateIntelligenceBrief(competitorId, significantChanges);
    }

    return { competitorId, changesDetected: changes.length, significantChanges: significantChanges.length };
  }

  return { competitorId, changesDetected: 0, message: 'First snapshot -- no comparison available' };
}
```

### RSS Feeds (Blog Monitoring)

Many competitor blogs have RSS/Atom feeds. Monitor them for new content without scraping.

```javascript
const Parser = require('rss-parser');
const parser = new Parser();

async function checkBlogUpdates(feedUrl, lastChecked) {
  const feed = await parser.parseURL(feedUrl);
  const newPosts = feed.items.filter(item => {
    const pubDate = new Date(item.pubDate || item.isoDate);
    return pubDate > new Date(lastChecked);
  });

  return newPosts.map(post => ({
    title: post.title,
    link: post.link,
    pubDate: post.pubDate || post.isoDate,
    summary: post.contentSnippet?.substring(0, 300)
  }));
}
```

### Google Alerts (Free Keyword Monitoring)

Set up Google Alerts for:
- Competitor brand name (exact match: `"Competitor Name"`)
- Competitor brand + key terms: `"Competitor Name" pricing`, `"Competitor Name" reviews`
- Competitor owner/CEO name

Google Alerts deliver email digests. An n8n workflow can parse incoming alert emails and store the mentions in Supabase.

### DataForSEO (Ranking and SEO Changes)

Use DataForSEO's Rank Tracker and SERP APIs to track keyword positions over time. Store weekly ranking snapshots and calculate position changes.

```javascript
async function weeklyRankingCheck(competitorDomain, trackedKeywords) {
  const currentRankings = await trackSEOChanges(competitorDomain, trackedKeywords);

  // Get last week's rankings from Supabase
  const { data: previousRankings } = await supabase
    .from('competitor_metrics')
    .select('*')
    .eq('competitor_domain', competitorDomain)
    .eq('metric_type', 'seo_rankings')
    .order('recorded_at', { ascending: false })
    .limit(1)
    .single();

  const changes = [];
  for (const current of currentRankings) {
    const previous = previousRankings?.data?.rankings?.find(r => r.keyword === current.keyword);
    if (previous && previous.position !== current.position) {
      const delta = previous.position - current.position; // positive = improved
      changes.push({
        keyword: current.keyword,
        previousPosition: previous.position,
        currentPosition: current.position,
        delta,
        significance: Math.abs(delta) >= 10 ? 8 : Math.abs(delta) >= 5 ? 5 : 2
      });
    }
  }

  return changes;
}
```

### BuiltWith API (Technology Change Alerts)

```javascript
async function checkTechChanges(domain) {
  const response = await fetch(
    `https://api.builtwith.com/v21/api.json?KEY=${BUILTWITH_API_KEY}&LOOKUP=${domain}`,
    { method: 'GET' }
  );
  const data = await response.json();

  // Compare with previously stored tech profile
  // BuiltWith provides "FirstDetected" and "LastDetected" dates for each technology
  // Technologies with recent "FirstDetected" dates are new additions
  // Technologies with recent "LastDetected" dates (but not current) were removed

  return data;
}
```

---

## Change Scoring System

Every detected change receives a significance score from 1 to 10. This score determines whether it triggers an alert and how prominently it appears in intelligence reports.

### Scoring Matrix

| Score | Level | Examples | Alert? |
|---|---|---|---|
| 1 | Trivial | Typo fix, image swap, footer update, minor CSS change | No |
| 2 | Minor | Blog post published, social media post, minor copy edit | No |
| 3 | Noteworthy | New team member added, new testimonial, new photo on Google Maps | No (logged) |
| 4 | Notable | New blog category, changed meta descriptions, response to review | Weekly digest |
| 5 | Moderate | New service page, pricing change, new Google Post campaign, new ad creative | Daily alert |
| 6 | Significant | New product/service launch, new technology adopted, 10+ position SEO jump | Daily alert |
| 7 | Important | Rebrand initiated, significant hiring surge (5+ new roles), major rating change | Immediate alert |
| 8 | High | Complete pricing overhaul, major partnership announced, leadership change | Immediate alert |
| 9 | Critical | Competitor acquired, major pivot, lawsuit filed, data breach | Immediate alert |
| 10 | Urgent | Direct attack on client (negative campaign, poaching employees, undercutting) | Immediate alert + call |

### Automated Scoring Rules

```javascript
function scoreChange(changeType, details) {
  const rules = {
    // Website changes
    'new_page': () => {
      if (details.url?.includes('pricing') || details.url?.includes('service')) return 6;
      if (details.url?.includes('blog') || details.url?.includes('post')) return 2;
      if (details.url?.includes('careers') || details.url?.includes('jobs')) return 4;
      return 3;
    },
    'removed_page': () => {
      if (details.url?.includes('service')) return 6;
      return 3;
    },
    'content_changed': () => {
      if (details.url?.includes('pricing')) return 7;
      if (details.url?.includes('service')) return 5;
      if (details.url?.includes('about') || details.url?.includes('team')) return 4;
      return 2;
    },
    'pricing_change': () => 7,

    // Review changes
    'rating_change': () => {
      const delta = Math.abs(details.previousRating - details.currentRating);
      if (delta >= 0.5) return 7;
      if (delta >= 0.2) return 5;
      return 3;
    },
    'review_velocity_spike': () => {
      if (details.velocityIncrease >= 300) return 7; // 3x normal velocity
      if (details.velocityIncrease >= 200) return 5; // 2x normal velocity
      return 3;
    },

    // SEO changes
    'ranking_change': () => {
      const delta = Math.abs(details.positionDelta);
      if (delta >= 20) return 8;
      if (delta >= 10) return 6;
      if (delta >= 5) return 4;
      return 2;
    },
    'new_keyword': () => details.position <= 10 ? 6 : 3,
    'lost_keyword': () => 2,
    'new_backlink': () => details.domainAuthority >= 50 ? 5 : 2,

    // Social media changes
    'follower_spike': () => details.growthRate >= 20 ? 6 : 3, // 20%+ growth in a week
    'posting_frequency_change': () => details.increase >= 100 ? 5 : 2, // doubled posting
    'new_platform': () => 5,

    // Technology changes
    'new_technology': () => {
      if (['HubSpot', 'Marketo', 'Salesforce'].includes(details.technology)) return 6;
      return 3;
    },
    'technology_removed': () => 3,

    // Advertising changes
    'new_ad_campaign': () => 5,
    'ad_spend_increase': () => details.increasePercent >= 50 ? 7 : 4,

    // Team changes
    'new_hire': () => {
      if (details.role?.match(/vp|director|chief|cto|cmo|cfo/i)) return 8;
      if (details.role?.match(/manager|lead/i)) return 5;
      return 3;
    },
    'departure': () => {
      if (details.role?.match(/vp|director|chief|cto|cmo|cfo/i)) return 8;
      return 4;
    },

    // Press/News
    'press_release': () => 5,
    'news_mention': () => details.sentiment === 'negative' ? 7 : 4,
    'award': () => 5,
    'partnership': () => 7,
    'funding': () => 9,
    'acquisition': () => 10
  };

  const scoreFn = rules[changeType];
  return scoreFn ? scoreFn() : 3; // Default score of 3 for unknown change types
}
```

---

## Alerting

### Intelligence Brief Generation

When significant changes are detected (score >= 5), OpenClaw generates a structured intelligence brief.

**Brief format:**

```
COMPETITIVE INTELLIGENCE ALERT
Client: [Client Name]
Competitor: [Competitor Name]
Date: [Detection Date]
Priority: [High/Medium based on score]

CHANGES DETECTED:
1. [Change description] (Significance: X/10)
   - Details: [Specifics]
   - Impact: [What this means for the client]
   - Recommended action: [What the client should consider doing]

2. [Change description] (Significance: X/10)
   ...

CONTEXT:
- [Competitor] has made [N] total changes in the past 30 days.
- Their overall trajectory suggests: [growing/stable/declining/pivoting]

RECOMMENDED NEXT STEPS:
- [Action item 1]
- [Action item 2]
```

### Alert Delivery Channels

| Priority | Channel | Timing |
|---|---|---|
| Score 1-3 | Logged only (no notification) | N/A |
| Score 4 | Weekly digest email | Monday morning |
| Score 5-6 | Daily alert email | Morning of detection |
| Score 7-8 | Immediate email + Slack notification | Within minutes |
| Score 9-10 | Immediate email + Slack + SMS/call | Within minutes |

### n8n Alert Workflow

1. **Trigger:** New row in `competitor_changes` table (Supabase webhook or polling).
2. **Filter:** Check significance score.
3. **Branch by priority:**
   - Score 1-3: No action (already stored).
   - Score 4: Add to weekly digest queue (Airtable record).
   - Score 5-6: Generate brief via OpenAI/Claude, send email via SendGrid/Gmail.
   - Score 7+: Generate brief, send email, send Slack message, optionally send SMS via Twilio.

---

## Monitoring Frequency

Not all competitors need the same monitoring cadence. Prioritize based on threat level and client importance.

| Priority | Frequency | Description |
|---|---|---|
| **P1 -- Primary** | Daily | Top 3 direct competitors. Same market, same services, same geography. These are the businesses most likely to steal your client's customers. |
| **P2 -- Secondary** | Twice weekly | Next 5-7 competitors. Same market but different specialization, adjacent geography, or slightly different target audience. |
| **P3 -- Tertiary** | Weekly | Broader market players. Larger agencies that could move into the local market, or smaller newcomers that might grow. |
| **P4 -- Watchlist** | Bi-weekly | Not current threats but worth tracking. New entrants, businesses in adjacent industries that might expand. |

### Frequency by Data Source

| Data Source | P1 | P2 | P3 | P4 |
|---|---|---|---|---|
| Website content | Daily | 2x/week | Weekly | Bi-weekly |
| Google Maps | Daily | 2x/week | Weekly | Bi-weekly |
| Social media | Daily | 2x/week | Weekly | Monthly |
| SEO rankings | Weekly | Weekly | Bi-weekly | Monthly |
| Job postings | Weekly | Weekly | Bi-weekly | Monthly |
| Technology stack | Weekly | Bi-weekly | Monthly | Monthly |
| Advertising | 2x/week | Weekly | Bi-weekly | Monthly |
| Press/News | Daily (Google Alerts) | Daily (Google Alerts) | Weekly | Monthly |

---

## Historical Tracking

All changes are stored in Supabase with full history. This enables:

### Trend Analysis

```sql
-- Review velocity trend for a competitor over the past 6 months
SELECT
  DATE_TRUNC('week', snapshot_date) AS week,
  (data->'googleMaps'->>'reviewCount')::int AS review_count
FROM competitor_snapshots
WHERE competitor_id = 'uuid-here'
  AND snapshot_date >= NOW() - INTERVAL '6 months'
ORDER BY week;
```

### Change Frequency Analysis

```sql
-- How often does this competitor make significant changes?
SELECT
  DATE_TRUNC('month', detected_at) AS month,
  COUNT(*) AS total_changes,
  COUNT(*) FILTER (WHERE significance >= 5) AS significant_changes
FROM competitor_changes
WHERE competitor_id = 'uuid-here'
  AND detected_at >= NOW() - INTERVAL '12 months'
GROUP BY month
ORDER BY month;
```

### Competitor Activity Timeline

```sql
-- Full timeline of competitor activity
SELECT
  detected_at,
  change_type,
  description,
  significance
FROM competitor_changes
WHERE competitor_id = 'uuid-here'
ORDER BY detected_at DESC
LIMIT 50;
```

This timeline becomes a key component of the monthly competitive intelligence report delivered to clients. It answers the question: "What has our competitor been doing, and what does it mean for us?"

---

## Integration with Other System Components

- **Playwright scraping** (`playwright-scraping.md`): Provides the raw data that change monitoring compares.
- **Data storage** (`data-storage.md`): Defines the schema where snapshots and changes are persisted.
- **DataForSEO integration** (`dataforseo-seo.md`): Provides SEO-specific metrics for ranking change detection.
- **OpenClaw skill**: The `competitor_monitor` skill orchestrates the full monitoring loop and can be triggered by schedule or by the agent on demand.
- **Client reporting**: Monthly intelligence reports pull from the change history to show competitor activity trends, significant moves, and recommended responses.

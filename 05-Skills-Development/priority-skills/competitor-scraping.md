# Competitor Scraping and Intelligence Skill

## Goal

Build an OpenClaw skill that performs automated competitive intelligence gathering for Rise Local clients. Monitor competitors' websites, reviews, social media, ad activity, and SEO performance, then surface actionable insights when significant changes are detected.

---

## Legal Framework

**CRITICAL**: All competitor intelligence gathering must comply with applicable laws. Before implementing, review `09-Legal-Compliance/web-scraping-law.md` in detail.

### Key Legal Principles

| Principle | Implication |
|-----------|-------------|
| **Public data is generally fair game** | Websites, social media, reviews, ad libraries are public |
| **robots.txt must be respected** | If a site blocks crawlers, do not crawl it |
| **CFAA (Computer Fraud and Abuse Act)** | Do not bypass authentication, access private areas, or circumvent technical barriers |
| **Copyright** | Collect metadata and summaries, not full content reproduction |
| **Rate limiting** | Do not overload competitor servers; space requests out |
| **Terms of Service** | Review each platform's ToS; some prohibit automated access |
| **hiQ v. LinkedIn (2022)** | Scraping publicly available data is generally permissible, but the legal landscape continues to evolve |

### Safe vs Risky Activities

| Activity | Risk Level | Notes |
|----------|-----------|-------|
| Checking competitor website for changes | Low | Public data, respect robots.txt |
| Reading Google reviews | Low | Publicly accessible |
| Checking Facebook Ad Library | Low | Public transparency tool |
| Checking Google Ads Transparency Center | Low | Public transparency tool |
| Monitoring SEO rankings | Low | Using DataForSEO API (legitimate service) |
| Scraping competitor pricing | Medium | Public data but ToS may prohibit |
| Monitoring social media posts | Low-Medium | Public posts, API preferred over scraping |
| Automated form submissions | High | Do not do this |
| Bypassing login walls | High | Illegal under CFAA |
| Scraping customer data/emails | High | Privacy violations, potentially illegal |

---

## Data to Collect

### 1. Website Changes

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| New pages added | Sitemap diff | Weekly | New services, products, locations |
| Pricing changes | Page content diff | Weekly | Competitive pricing intelligence |
| New testimonials | Testimonial page diff | Bi-weekly | Social proof changes |
| Design changes | Visual diff (screenshot comparison) | Monthly | Rebrand or refresh indicators |
| Technology changes | BuiltWith monitoring | Monthly | New tools adoption |
| Page speed changes | Lighthouse audit | Monthly | Performance investment |
| Content additions | Blog/news page monitoring | Weekly | Content strategy insights |

### 2. Google My Business (Google Business Profile)

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| New reviews | Google Places API | Daily-Weekly | Review velocity, sentiment |
| Rating changes | Google Places API | Weekly | Reputation trends |
| Review responses | Google Places API | Weekly | Customer service quality |
| Business posts | Google Places API | Weekly | Promotional activity |
| Photo additions | Google Places API | Monthly | Visual marketing investment |
| Hours changes | Google Places API | Monthly | Service expansion/contraction |
| Category changes | Google Places API | Monthly | New service areas |

### 3. Social Media Activity

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| Post frequency | Platform APIs / page scraping | Weekly | Content investment level |
| Engagement rates | Platform APIs | Weekly | Audience connection |
| New campaigns | Ad library monitoring | Weekly | Marketing spend indicators |
| Follower growth | Platform APIs | Monthly | Brand growth trajectory |
| Content themes | Post content analysis | Monthly | Messaging strategy |

### 4. Advertising Activity

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| **Facebook/Meta Ads** | Facebook Ad Library API | Weekly | Ad creative, spend estimates, targeting |
| **Google Ads** | Google Ads Transparency Center | Weekly | Active ad campaigns, ad copy |
| **Google LSA** | SERP monitoring | Weekly | Local Services Ads presence |
| **Estimated ad spend** | DataForSEO / SEMrush data | Monthly | Marketing budget indicators |

### 5. SEO Metrics

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| Keyword rankings | DataForSEO | Weekly | SERP position changes |
| Organic traffic estimate | DataForSEO | Monthly | Traffic growth/decline |
| Backlink profile | DataForSEO | Monthly | Link building activity |
| New content | Sitemap / blog monitoring | Weekly | Content marketing strategy |
| Page authority changes | DataForSEO | Monthly | SEO investment effectiveness |
| Local pack rankings | DataForSEO SERP API | Weekly | Local SEO performance |

### 6. Technology Stack Changes

| Data Point | Method | Frequency | Why It Matters |
|------------|--------|-----------|----------------|
| CMS changes | BuiltWith API | Monthly | Website rebuild/migration |
| New marketing tools | BuiltWith API | Monthly | Marketing sophistication |
| New analytics | BuiltWith API | Monthly | Measurement investment |
| Chat widget added | BuiltWith API | Monthly | Customer service investment |
| Booking system added | BuiltWith API | Monthly | Service delivery investment |

---

## Tools and Data Sources

### Playwright (Browser Automation)

**Use for**: JavaScript-heavy sites, visual screenshots, content that requires rendering.

```typescript
// Example: Screenshot comparison for visual changes
import { chromium } from 'playwright';

async function captureCompetitorPage(url: string, outputPath: string) {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto(url, { waitUntil: 'networkidle' });
  await page.screenshot({ path: outputPath, fullPage: true });

  // Extract key content
  const title = await page.title();
  const h1 = await page.locator('h1').first().textContent();
  const metaDesc = await page.getAttribute('meta[name="description"]', 'content');

  await browser.close();
  return { title, h1, metaDesc, screenshotPath: outputPath };
}
```

### DataForSEO API

**Use for**: SEO metrics, SERP tracking, keyword rankings, backlink analysis.

```typescript
// Example: Get competitor domain overview
async function getDomainOverview(domain: string) {
  const response = await fetch('https://api.dataforseo.com/v3/dataforseo_labs/google/domain_rank_overview/live', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${Buffer.from(`${login}:${password}`).toString('base64')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify([{ target: domain, location_code: 2840 }]) // US
  });
  return response.json();
}
```

### Google Alerts (Free Monitoring)

**Use for**: Brand mention monitoring, news monitoring.

**Setup**:
1. Create Google Alerts for each competitor name
2. Set delivery to: RSS feed
3. Skill monitors RSS feeds for new alerts
4. When new mention detected, classify and alert

### Page Change Detection Services

| Service | What It Does | Cost |
|---------|-------------|------|
| **Visualping** | Visual + content monitoring of web pages | Free (5 pages), $13+/month |
| **ChangeTower** | Page change monitoring with diffs | Free (5 pages), $15+/month |
| **Distill.io** | Browser-based page monitoring | Free (25 monitors), $15+/month |
| **Custom (DIY)** | Build with Playwright + diff library | Free (server costs only) |

**Recommendation**: Build a custom monitoring system using Playwright for flexibility, supplemented by free tier of Visualping for visual monitoring.

---

## Skill Design: @yourname/competitor-intel

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/competitor-intel",
  "version": "1.0.0",
  "description": "Automated competitive intelligence gathering and monitoring",
  "commands": ["/competitor", "/comp-intel", "/monitor-competitor"],
  "inputs": {
    "required": {
      "action": {
        "type": "string",
        "enum": [
          "add_competitor",
          "remove_competitor",
          "scan_now",
          "get_report",
          "get_changes",
          "compare",
          "full_audit"
        ]
      }
    },
    "optional": {
      "competitor_url": { "type": "string", "format": "uri" },
      "competitor_name": { "type": "string" },
      "data_points": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["website", "reviews", "social", "ads", "seo", "tech_stack"]
        },
        "default": ["website", "reviews", "seo"]
      },
      "client_url": {
        "type": "string",
        "description": "Client's URL for comparison"
      },
      "date_range": {
        "type": "object",
        "properties": {
          "from": { "type": "string", "format": "date" },
          "to": { "type": "string", "format": "date" }
        }
      },
      "alert_threshold": {
        "type": "string",
        "enum": ["any_change", "significant_only", "major_only"],
        "default": "significant_only"
      }
    }
  },
  "outputs": {
    "report": { "type": "object", "description": "Competitive intelligence report" },
    "changes": { "type": "array", "description": "Detected changes since last scan" },
    "alerts": { "type": "array", "description": "Significant changes requiring attention" },
    "comparison": { "type": "object", "description": "Side-by-side comparison with client" }
  },
  "permissions": {
    "network": [
      "api.dataforseo.com",
      "api.builtwith.com",
      "maps.googleapis.com",
      "www.facebook.com",
      "adstransparency.google.com",
      "*"
    ],
    "environment": [
      "DATAFORSEO_LOGIN",
      "DATAFORSEO_PASSWORD",
      "BUILTWITH_API_KEY",
      "GOOGLE_PLACES_API_KEY",
      "SUPABASE_URL",
      "SUPABASE_ANON_KEY"
    ]
  },
  "tools": {
    "required": ["web_fetch", "browser", "file_write"],
    "optional": ["code_execution"]
  },
  "dependencies": {
    "skills": {
      "@yourname/database-ops": "^1.0.0"
    }
  }
}
```

### Execution Flow: Competitor Scan

```
Step 1: Retrieve Competitor Baseline
  - Load previous scan data from Supabase
  - If first scan: establish baseline (no diff possible)

Step 2: Website Scan
  - Fetch competitor sitemap (sitemap.xml)
  - Diff sitemap pages against previous scan (new pages, removed pages)
  - For key pages (homepage, pricing, services): fetch content and diff
  - Screenshot key pages for visual comparison
  - Check robots.txt for changes

Step 3: Reviews Scan
  - Google Places API: get current rating, review count, recent reviews
  - Diff against previous: new reviews, rating changes
  - Sentiment analysis on new reviews (positive/negative/neutral)

Step 4: SEO Scan
  - DataForSEO: domain overview (authority, traffic, keywords)
  - Diff against previous: ranking changes, traffic changes
  - Track specific keywords relevant to client

Step 5: Tech Stack Scan
  - BuiltWith API: current technology profile
  - Diff against previous: new technologies, removed technologies

Step 6: Ad Activity Scan
  - Facebook Ad Library: check for active ads
  - Google Ads Transparency: check for active search ads
  - Capture ad creative and copy

Step 7: Score Changes
  For each change detected, assign significance:
    - Major: New website launch, significant pricing change, new service offering
    - Significant: New reviews spike, ranking change for target keywords, new ad campaign
    - Minor: Small content update, single new review, tech stack addition

Step 8: Generate Report
  - Structured report with all findings
  - Highlight significant changes
  - Actionable recommendations for client

Step 9: Store Results
  - Save current scan data to Supabase (becomes baseline for next scan)
  - Update competitor tracking history
  - If significant changes: trigger alert
```

---

## Change Detection and Diffing

### Content Diff Algorithm

```typescript
// Simplified content diff approach
interface ContentDiff {
  page: string;
  changeType: 'added' | 'removed' | 'modified';
  previousContent: string;
  currentContent: string;
  changePercentage: number;
  summary: string; // AI-generated summary of the change
}

function detectContentChanges(
  previous: PageContent[],
  current: PageContent[]
): ContentDiff[] {
  const diffs: ContentDiff[] = [];

  // Check for new pages
  for (const page of current) {
    const prev = previous.find(p => p.url === page.url);
    if (!prev) {
      diffs.push({
        page: page.url,
        changeType: 'added',
        previousContent: '',
        currentContent: page.textContent,
        changePercentage: 100,
        summary: `New page added: ${page.title}`
      });
    } else {
      // Calculate text similarity
      const similarity = calculateSimilarity(prev.textContent, page.textContent);
      if (similarity < 0.95) { // More than 5% different
        diffs.push({
          page: page.url,
          changeType: 'modified',
          previousContent: prev.textContent,
          currentContent: page.textContent,
          changePercentage: Math.round((1 - similarity) * 100),
          summary: '' // AI generates this later
        });
      }
    }
  }

  // Check for removed pages
  for (const page of previous) {
    if (!current.find(p => p.url === page.url)) {
      diffs.push({
        page: page.url,
        changeType: 'removed',
        previousContent: page.textContent,
        currentContent: '',
        changePercentage: 100,
        summary: `Page removed: ${page.title}`
      });
    }
  }

  return diffs;
}
```

### Visual Diff (Screenshot Comparison)

```typescript
// Use pixelmatch or similar library for visual comparison
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

function compareScreenshots(
  previousPath: string,
  currentPath: string,
  diffOutputPath: string
): { diffPercentage: number; diffPixels: number } {
  const img1 = PNG.sync.read(fs.readFileSync(previousPath));
  const img2 = PNG.sync.read(fs.readFileSync(currentPath));
  const diff = new PNG({ width: img1.width, height: img1.height });

  const diffPixels = pixelmatch(
    img1.data, img2.data, diff.data,
    img1.width, img1.height,
    { threshold: 0.1 }
  );

  fs.writeFileSync(diffOutputPath, PNG.sync.write(diff));

  const totalPixels = img1.width * img1.height;
  return {
    diffPercentage: (diffPixels / totalPixels) * 100,
    diffPixels
  };
}
```

---

## Storage Schema (Supabase)

```sql
-- Competitors being tracked
CREATE TABLE competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID REFERENCES clients(id),
  name TEXT NOT NULL,
  website TEXT NOT NULL,
  google_place_id TEXT,
  social_urls JSONB,
  tracking_config JSONB, -- which data points to monitor
  scan_frequency TEXT DEFAULT 'weekly',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  last_scanned_at TIMESTAMPTZ,
  UNIQUE(client_id, website)
);

-- Scan history
CREATE TABLE competitor_scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id UUID REFERENCES competitors(id),
  scan_date TIMESTAMPTZ DEFAULT NOW(),
  scan_type TEXT, -- full, website_only, seo_only, etc.

  -- Website data
  sitemap_pages JSONB,
  page_contents JSONB, -- key page content snapshots
  screenshot_paths JSONB,

  -- Reviews
  google_rating DECIMAL(2,1),
  google_review_count INTEGER,
  recent_reviews JSONB,

  -- SEO
  domain_authority INTEGER,
  organic_traffic_estimate INTEGER,
  keyword_rankings JSONB,
  backlink_count INTEGER,

  -- Tech stack
  tech_stack JSONB,

  -- Ads
  active_facebook_ads JSONB,
  active_google_ads JSONB,
  estimated_ad_spend DECIMAL(10,2),

  -- Metadata
  scan_duration_seconds INTEGER,
  scan_cost DECIMAL(6,4),
  errors JSONB
);

-- Change alerts
CREATE TABLE competitor_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id UUID REFERENCES competitors(id),
  scan_id UUID REFERENCES competitor_scans(id),
  severity TEXT CHECK (severity IN ('major', 'significant', 'minor')),
  category TEXT, -- website, reviews, seo, ads, tech_stack
  title TEXT NOT NULL,
  description TEXT,
  data JSONB, -- detailed change data
  acknowledged BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitor_alerts_unack ON competitor_alerts(competitor_id, acknowledged) WHERE NOT acknowledged;
CREATE INDEX idx_competitor_scans_date ON competitor_scans(competitor_id, scan_date DESC);
```

---

## Ethical Guidelines

### Do

- Respect robots.txt directives
- Use official APIs when available (Google Places, Facebook Ad Library)
- Rate limit requests (max 1 request/second per domain)
- Collect only publicly available information
- Store data responsibly with access controls
- Provide factual analysis, not speculation
- Credit sources in reports

### Do Not

- Bypass authentication or access private areas
- Overload competitor servers (DoS-like behavior)
- Scrape personal employee data
- Copy competitor content verbatim (copyright)
- Submit fake reviews or forms
- Impersonate competitor employees or customers
- Share raw scraped data outside your organization
- Monitor competitors' internal tools (even if accidentally accessible)

---

## Report Template

### Monthly Competitive Intelligence Report

```markdown
# Competitive Intelligence Report
**Client**: [Client Name]
**Period**: [Month Year]
**Competitors Monitored**: [Count]

## Executive Summary
[2-3 sentence overview of the most important competitive changes this month]

## Key Alerts
- [MAJOR] [Competitor A] launched a completely redesigned website
- [SIGNIFICANT] [Competitor B] started running Google Ads for "[target keyword]"
- [SIGNIFICANT] [Competitor C] received 15 new Google reviews (avg 4.9 stars)

## Competitor-by-Competitor Analysis

### [Competitor A]
**Website**: [url]
- Website changes: [summary]
- Reviews: [current rating] ([change]) | [review count] ([change])
- SEO: Domain Authority [score] ([change]) | Estimated traffic: [number]
- Active ads: [yes/no] | Estimated spend: [$amount]
- Tech changes: [any new tools detected]

### [Competitor B]
[Same structure]

## Comparative Dashboard

| Metric | [Client] | [Comp A] | [Comp B] | [Comp C] |
|--------|----------|----------|----------|----------|
| Google Rating | 4.6 | 4.8 | 4.2 | 4.5 |
| Review Count | 85 | 127 | 43 | 92 |
| Domain Authority | 22 | 35 | 18 | 28 |
| Est. Monthly Traffic | 450 | 1,200 | 200 | 680 |
| Page Speed Score | 72 | 88 | 45 | 65 |
| Active Ad Campaigns | 1 | 3 | 0 | 2 |

## Recommendations
1. [Specific action based on competitive intelligence]
2. [Specific action based on competitive intelligence]
3. [Specific action based on competitive intelligence]

## Data Sources
- Google Places API (reviews, ratings)
- DataForSEO (SEO metrics, rankings)
- BuiltWith (technology detection)
- Facebook Ad Library (ad monitoring)
- Direct website monitoring (content changes)
```

---

*Last updated: 2026-02-05*
*Status: Skill design complete; legal review required before implementation (see 09-Legal-Compliance/web-scraping-law.md)*

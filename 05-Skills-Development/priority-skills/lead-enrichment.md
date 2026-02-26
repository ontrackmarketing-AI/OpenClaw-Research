# Lead Enrichment Skill

## Goal

Build an OpenClaw skill that performs automated, multi-source lead enrichment. Given a business name, URL, or basic contact info, the skill orchestrates API calls across multiple data providers in a waterfall pattern, returning a comprehensive enriched lead profile ready for scoring and CRM ingestion.

---

## Data Sources

### Primary Sources (You Have Access To)

#### 1. Clay.com -- Waterfall Enrichment (Primary)

- **What it does**: Clay is an enrichment platform that chains multiple data providers together in a "waterfall" -- if provider A does not have the data, it tries provider B, then C, etc.
- **Your existing skill**: `clay-enrichment` Claude Code skill already integrates with Clay
- **Key capabilities**:
  - Create enrichment tables programmatically
  - Add leads to tables for enrichment
  - Run waterfall across 50+ data providers
  - Pull enriched results back via API
- **Data returned**: Email addresses, phone numbers, company info, social profiles, technographics
- **Cost**: Clay pricing is per-credit; each enrichment uses 1-5 credits depending on depth
- **API**: REST API at `api.clay.com`

#### 2. Apollo.io -- Contact and Company Data

- **What it does**: B2B contact database with email finding, company data, and prospecting
- **Key capabilities**:
  - Find emails by name + company
  - Company search by domain
  - Contact enrichment by email or LinkedIn URL
  - Bulk enrichment via API
- **Data returned**: Work email, personal email, phone, title, company info, social links, company revenue/employee count
- **Cost**: Free tier (300 credits/month), paid plans from $49/month
- **API**: REST API at `api.apollo.io/v1`

#### 3. ZeroBounce -- Email Verification

- **What it does**: Validates email addresses for deliverability before you send outreach
- **Key capabilities**:
  - Single email validation
  - Bulk email validation
  - Email scoring (quality assessment)
  - Catch-all detection
- **Data returned**: Validation status (valid/invalid/catch-all/unknown), sub-status, domain info
- **Cost**: ~$0.008 per validation (pay-as-you-go)
- **API**: REST API at `api.zerobounce.net/v2`

#### 4. BuiltWith -- Technology Stack Detection

- **What it does**: Detects what technologies a website uses (CMS, analytics, ads, etc.)
- **Key capabilities**:
  - Full technology profile for any domain
  - Category filtering (e.g., "only show analytics tools")
  - Historical technology changes
  - Competitor comparison
- **Data returned**: Technology list with categories, first/last detected dates, version info
- **Relevant signals for scoring**:
  - Has Google Analytics? (indicates tracking awareness)
  - Has Facebook Pixel? (indicates paid advertising)
  - CMS type (WordPress, Wix, Squarespace, custom)
  - Has SSL? (basic security)
  - Call tracking software? (indicates marketing sophistication)
- **Cost**: Free tier (limited), paid from $295/month for API access
- **API**: REST API at `api.builtwith.com/v21`

#### 5. Google Places API -- Business Discovery

- **What it does**: Find businesses by industry and location, get details, reviews, and photos
- **Key capabilities**:
  - Nearby search by keyword and location
  - Place details (address, phone, website, hours, reviews)
  - Review data (count, rating, individual reviews)
  - Photos
- **Data returned**: Business name, address, phone, website, rating, review count, categories, operating hours, photos
- **Cost**: $0.032 per Nearby Search, $0.017 per Place Details call
- **API**: REST API (Maps Platform)
- **Your existing integration**: Used in the `lead-pipeline` skill for business discovery

#### 6. DataForSEO -- SEO Metrics and Rankings

- **What it does**: Provides SEO data: rankings, backlinks, keyword positions, domain authority
- **Key capabilities**:
  - Domain overview (authority, backlinks, organic traffic estimate)
  - Keyword rankings for a domain
  - Backlink profile
  - On-page SEO audit
  - SERP tracking
- **Data returned**: Domain rank, backlink count, organic keywords, estimated traffic, top keywords
- **Relevant signals for scoring**:
  - Domain authority (low = opportunity)
  - Organic traffic (low = needs SEO)
  - Number of indexed pages
  - Page speed metrics
- **Cost**: Pay-per-task pricing, roughly $0.01-0.05 per request depending on type
- **API**: REST API at `api.dataforseo.com`

### Potential Additional Sources

| Source | Data | Cost | Priority |
|--------|------|------|----------|
| **Clearbit** | Company enrichment (size, revenue, industry, tech) | $99+/month | Medium |
| **Hunter.io** | Email finding and verification | Free 25/month, $49/month | Low (Clay covers this) |
| **LinkedIn Sales Navigator** | Professional contact data | $99+/month | Low (manual process) |
| **Crunchbase** | Company funding, investors, growth data | $29+/month | Low |
| **SimilarWeb** | Website traffic and engagement metrics | $125+/month | Low |

---

## Waterfall Enrichment Strategy

The waterfall approach tries multiple data sources in a priority order for each data point, stopping when the data is found. This maximizes data coverage while minimizing cost.

### Full Enrichment Pipeline

```
Input: Business name, URL, and/or basic contact info

Stage 1: Business Discovery (if only name/location provided)
  Source: Google Places API
  Data: Name, address, phone, website, category, rating, review count
  Cost: ~$0.05 per business
  Skip if: URL already provided

Stage 2: Basic Web Presence Analysis
  Source: Direct website crawl (Playwright or fetch)
  Data: Page title, meta description, contact info, social links
  Cost: Free (just HTTP requests)
  Process:
    - Fetch homepage HTML
    - Extract meta tags, social links, contact info
    - Check mobile responsiveness
    - Check SSL certificate
    - Measure page load time

Stage 3: Technology Stack Detection
  Source: BuiltWith API
  Data: CMS, analytics, ads, marketing tools, hosting
  Cost: ~$0.10 per lookup (depends on plan)
  Relevant signals:
    - CMS type -> complexity of potential project
    - Analytics presence -> marketing awareness
    - Ad pixels -> paid advertising usage
    - Call tracking -> lead tracking sophistication

Stage 4: Contact Finding (Waterfall)
  Source 1: Clay.com waterfall (uses multiple providers internally)
  Source 2: Apollo.io (if Clay doesn't return result)
  Source 3: Direct website scraping (contact page, about page)
  Data: Owner/decision-maker name, email, phone, LinkedIn
  Cost: $0.05-0.20 per contact (varies by provider)
  Waterfall logic:
    1. Try Clay enrichment first (best coverage via waterfall)
    2. If no email found: try Apollo by company domain
    3. If still no email: scrape website contact/about pages
    4. If still no email: try pattern matching (firstname@domain.com)

Stage 5: Email Verification
  Source: ZeroBounce
  Data: Email validity, catch-all detection, deliverability score
  Cost: ~$0.008 per email
  Rules:
    - Only verify emails found in Stage 4
    - Mark invalid emails as "do not contact"
    - Flag catch-all emails as "uncertain"

Stage 6: SEO and Online Presence Scoring
  Source: DataForSEO
  Data: Domain authority, organic traffic, rankings, page speed
  Cost: ~$0.02-0.05 per lookup
  Relevant signals:
    - Low domain authority = opportunity for SEO services
    - Low organic traffic = opportunity for content/SEO
    - Poor page speed = opportunity for website rebuild
    - Few indexed pages = thin content, opportunity

Stage 7: Pain Scoring (Your 15-Signal System)
  Source: Aggregation of all above data
  Process: Run the 15-signal scoring algorithm from Rise Local
  Output: Pain score (0-100), individual signal values, recommended services
```

### The 15-Signal Scoring System (from Rise Local)

| # | Signal | Source | Weight | Scoring Logic |
|---|--------|--------|--------|---------------|
| 1 | No website | Google Places | High | No website listed = max pain |
| 2 | Poor website (slow, not mobile-friendly) | Direct crawl | High | PageSpeed < 50 = high pain |
| 3 | No SSL certificate | Direct crawl | Medium | HTTP only = medium pain |
| 4 | No Google Analytics | BuiltWith | Medium | No tracking = opportunity |
| 5 | No Facebook Pixel | BuiltWith | Medium | No paid ads tracking = opportunity |
| 6 | Old/outdated CMS | BuiltWith | Medium | Old WordPress, Flash, etc. |
| 7 | Low Google rating | Google Places | Low | < 4.0 stars = needs review management |
| 8 | Few Google reviews | Google Places | Medium | < 20 reviews = opportunity |
| 9 | No review response | Google Places | Medium | Doesn't respond to reviews |
| 10 | Low domain authority | DataForSEO | High | DA < 20 = needs SEO |
| 11 | Low organic traffic | DataForSEO | High | < 100 visits/month = needs SEO |
| 12 | No call tracking | BuiltWith | Low | No CallRail/similar = not tracking leads |
| 13 | No online scheduling | Website crawl | Low | No booking widget |
| 14 | Competitors ranking higher | DataForSEO | Medium | Local competitors outranking |
| 15 | No social media presence | Website crawl | Low | No linked social profiles |

### Scoring Formula

```
Each signal scores 0 (no issue) to the signal's weight value (max issue).
Total pain score = sum(signal_scores) / max_possible * 100

Example weights:
  High = 10 points
  Medium = 6 points
  Low = 3 points

Max possible = 4*10 + 7*6 + 4*3 = 40 + 42 + 12 = 94 points

Score interpretation:
  80-100: Critical pain - hot lead, needs everything
  60-79:  High pain - strong lead, multiple opportunities
  40-59:  Medium pain - some opportunities
  20-39:  Low pain - well-managed, fewer opportunities
  0-19:   Minimal pain - already sophisticated
```

---

## Skill Design: @yourname/lead-enrichment

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/lead-enrichment",
  "version": "1.0.0",
  "description": "Multi-source lead enrichment with waterfall lookup and pain scoring",
  "commands": ["/enrich", "/enrich-lead", "/lookup"],
  "inputs": {
    "required": {},
    "oneOf": [
      { "business_name": { "type": "string" }, "location": { "type": "string" } },
      { "website": { "type": "string", "format": "uri" } },
      { "email": { "type": "string", "format": "email" } }
    ],
    "optional": {
      "depth": {
        "type": "string",
        "enum": ["basic", "standard", "full"],
        "default": "standard",
        "description": "basic=discovery only, standard=+tech+contact, full=+SEO+scoring"
      },
      "skip_stages": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Stages to skip (e.g., ['seo', 'email_verification'])"
      },
      "industry": {
        "type": "string",
        "description": "Business industry for context-aware scoring"
      },
      "batch": {
        "type": "array",
        "description": "Array of leads for batch enrichment"
      }
    }
  },
  "outputs": {
    "enriched_lead": {
      "type": "object",
      "properties": {
        "business": { "type": "object" },
        "contact": { "type": "object" },
        "tech_stack": { "type": "object" },
        "seo_metrics": { "type": "object" },
        "pain_score": { "type": "integer" },
        "pain_signals": { "type": "object" },
        "recommended_services": { "type": "array" }
      }
    },
    "enrichment_sources": { "type": "object", "description": "Which sources provided which data" },
    "cost": { "type": "number", "description": "Estimated cost of this enrichment" }
  },
  "permissions": {
    "network": [
      "api.clay.com",
      "api.apollo.io",
      "api.zerobounce.net",
      "api.builtwith.com",
      "maps.googleapis.com",
      "api.dataforseo.com",
      "*"
    ],
    "environment": [
      "CLAY_API_KEY",
      "APOLLO_API_KEY",
      "ZEROBOUNCE_API_KEY",
      "BUILTWITH_API_KEY",
      "GOOGLE_PLACES_API_KEY",
      "DATAFORSEO_LOGIN",
      "DATAFORSEO_PASSWORD"
    ]
  },
  "dependencies": {
    "skills": {
      "@yourname/clay-enrichment": "^1.0.0",
      "@yourname/database-ops": "^1.0.0"
    }
  }
}
```

---

## Cost per Lead Estimate

| Depth | Stages | Est. Cost per Lead | Data Returned |
|-------|--------|-------------------|---------------|
| **Basic** | Discovery + Web Crawl | $0.05-0.10 | Name, address, phone, website, basic web analysis |
| **Standard** | Basic + Tech Stack + Contact Finding | $0.15-0.30 | Above + tech stack, owner email/phone |
| **Full** | Standard + Email Verification + SEO + Scoring | $0.25-0.50 | Above + verified email, SEO metrics, pain score |

### Batch Discounts

- Clay.com: Bulk enrichment is cheaper per lead than individual lookups
- Apollo.io: Bulk API calls have higher rate limits
- DataForSEO: Task-based pricing with bulk discounts

### Monthly Cost Projections

| Volume | Depth | Monthly Cost |
|--------|-------|-------------|
| 100 leads | Standard | $15-30 |
| 500 leads | Standard | $75-150 |
| 100 leads | Full | $25-50 |
| 500 leads | Full | $125-250 |
| 1,000 leads | Full | $250-500 |

---

## Integration with Rise Local Pipeline

### How Enrichment Fits in the Pipeline

```
Step 1: Business Discovery (Google Places)
  lead-pipeline skill discovers businesses by industry + location
  Output: Array of basic business profiles (name, address, phone, website)

Step 2: Enrichment (this skill)
  Each discovered business is enriched:
    - Tech stack analysis
    - Contact finding (owner email/phone)
    - Email verification
    - SEO metrics
    - Pain scoring
  Output: Fully enriched lead profiles with pain scores

Step 3: Qualification
  lead-pipeline skill filters by pain score threshold (default: 60+)
  Output: Qualified leads ready for outreach

Step 4: CRM Ingestion
  ghl-crm skill creates contacts in GoHighLevel
  Enrichment data stored in custom fields and notes

Step 5: Outreach
  Qualified leads receive personalized outreach via GHL workflows
```

### Supabase Storage Schema

Enriched lead data is stored in Supabase for historical tracking and deduplication:

```sql
CREATE TABLE enriched_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_name TEXT NOT NULL,
  website TEXT,
  google_place_id TEXT UNIQUE,

  -- Business Info
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  phone TEXT,
  category TEXT,

  -- Google Reviews
  google_rating DECIMAL(2,1),
  google_review_count INTEGER,

  -- Contact Info
  contact_name TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  contact_linkedin TEXT,
  email_verified BOOLEAN,
  email_verification_status TEXT,

  -- Tech Stack (JSON)
  tech_stack JSONB,
  cms TEXT,
  has_analytics BOOLEAN,
  has_facebook_pixel BOOLEAN,
  has_call_tracking BOOLEAN,

  -- SEO Metrics
  domain_authority INTEGER,
  organic_traffic_estimate INTEGER,
  indexed_pages INTEGER,
  page_speed_score INTEGER,

  -- Scoring
  pain_score INTEGER,
  pain_signals JSONB,
  recommended_services TEXT[],

  -- Pipeline
  enrichment_depth TEXT,
  enrichment_cost DECIMAL(6,4),
  enrichment_sources JSONB,
  ghl_contact_id TEXT,
  pipeline_stage TEXT,

  -- Metadata
  first_enriched_at TIMESTAMPTZ DEFAULT NOW(),
  last_enriched_at TIMESTAMPTZ DEFAULT NOW(),
  enrichment_version TEXT,

  -- Deduplication
  UNIQUE(website),
  UNIQUE(contact_email) WHERE contact_email IS NOT NULL
);

CREATE INDEX idx_enriched_leads_pain_score ON enriched_leads(pain_score DESC);
CREATE INDEX idx_enriched_leads_city_state ON enriched_leads(city, state);
CREATE INDEX idx_enriched_leads_category ON enriched_leads(category);
```

---

## Deduplication Strategy

### When to Skip Enrichment

Before enriching a lead, check if it already exists:

```
1. Check by website URL (normalized: strip www, trailing slash, protocol)
2. Check by Google Place ID (if available)
3. Check by business name + city + state (fuzzy match)
4. Check by contact email (if provided)

If match found:
  - If last enriched < 30 days ago: return cached data
  - If last enriched 30-90 days ago: re-enrich only SEO metrics (most likely to change)
  - If last enriched > 90 days ago: full re-enrichment
  - Always re-verify email if > 30 days old
```

### URL Normalization

```typescript
function normalizeUrl(url: string): string {
  let normalized = url.toLowerCase().trim();
  normalized = normalized.replace(/^https?:\/\//, '');
  normalized = normalized.replace(/^www\./, '');
  normalized = normalized.replace(/\/$/, '');
  return normalized;
}

// "https://www.AcmePlumbing.com/" -> "acmeplumbing.com"
// "http://acmeplumbing.com" -> "acmeplumbing.com"
```

---

## Error Handling per Source

| Source | Common Errors | Handling |
|--------|--------------|----------|
| Google Places | Rate limit (429) | Exponential backoff, retry 3x |
| Clay.com | Table not found | Create table, then retry |
| Apollo.io | No results | Mark as "contact not found", continue |
| ZeroBounce | Invalid email format | Skip verification, mark as "unverified" |
| BuiltWith | Domain not found | Mark as "no tech data", continue |
| DataForSEO | Domain too new | Mark as "insufficient SEO data", continue |

### Partial Results

If some sources fail but others succeed, the skill should:
1. Return whatever data was successfully collected
2. Include a `sources_failed` field listing which sources failed and why
3. Set `enrichment_depth` to reflect actual depth achieved
4. Adjust `cost` to reflect only successful API calls
5. Allow retry of failed sources: `/enrich --retry-failed lead-id-123`

---

## Example Usage

### Single Lead Enrichment

```
/enrich
  website: "https://acmeplumbing.com"
  depth: full
  industry: plumber
```

### Batch Enrichment

```
/enrich
  batch: [
    { "business_name": "Acme Plumbing", "location": "Austin, TX" },
    { "business_name": "Best Rooter", "location": "Austin, TX" },
    { "website": "https://austinplumber.com" }
  ]
  depth: standard
  industry: plumber
```

### Re-enrichment

```
/enrich
  website: "https://acmeplumbing.com"
  depth: full
  --force  # Ignore deduplication, re-enrich everything
```

---

*Last updated: 2026-02-05*
*Status: Skill design complete; integrates with existing clay-enrichment and lead-pipeline skills*

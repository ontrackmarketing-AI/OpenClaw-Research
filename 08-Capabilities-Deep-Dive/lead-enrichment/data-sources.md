# Lead Enrichment Data Sources

## Overview

No single data source provides complete information about a business lead. A comprehensive enrichment strategy requires combining multiple sources, each with distinct strengths in coverage, accuracy, cost, and speed. This document catalogs every data source relevant to OpenClaw's lead enrichment pipeline and provides actionable guidance on integration, cost management, and source selection.

---

## Primary Data Sources

### 1. Google Places API (Google Maps Platform)

**What it provides:**
- Business name, address, phone number (NAP)
- Business category and subcategories
- Operating hours and seasonal hours
- Google Maps rating (1-5 stars) and total review count
- Individual review text, author, and rating
- Website URL
- Photos (exterior, interior, menu, etc.)
- Place ID (stable identifier for future lookups)
- Business status (operational, temporarily closed, permanently closed)
- Price level indicator

**Coverage:** Strongest for local/service businesses in the US. Over 200 million places globally. Excellent for home services, restaurants, healthcare, legal, and retail.

**Accuracy:** Very high for NAP data -- businesses actively manage their Google Business Profiles. Reviews are real-time. Hours may lag behind actual changes by days.

**API Details:**
- Place Search: find businesses by query + location
- Place Details: full data for a specific Place ID
- Nearby Search: radius-based discovery
- Text Search: natural language queries

**Cost:**
- Place Search: $0.032 per request
- Place Details (Basic): $0.017 per request
- Place Details (Contact): $0.003 per request
- Place Details (Atmosphere): $0.005 per request
- Free tier: $200/month credit (~6,000 basic detail requests)
- Effective cost per lead: ~$0.003-0.05 depending on fields requested

**Rate Limits:** 100 requests per second per project. Daily quota configurable.

**Integration Notes:**
- Requires Google Cloud project with Places API enabled
- API key authentication (restrict by IP and referrer)
- Response includes `place_id` -- use this as stable key across requests
- Pagination via `next_page_token` for search results (max 60 results per query)

**OpenClaw Integration:**
```
Tool: google_places_search
Input: query (e.g., "plumber"), location (lat/lng), radius (meters)
Output: array of businesses with basic info + place_id

Tool: google_places_details
Input: place_id
Output: full business profile
```

---

### 2. Clay.com (Waterfall Enrichment Platform)

**What it provides:**
- Contact finding across 75+ data providers in sequence
- Email addresses (personal and business)
- Phone numbers (direct dial, mobile, office)
- LinkedIn profile URLs
- Job titles and company roles
- Company data (size, revenue, industry)
- Technology stack data
- Social media profiles
- Custom enrichment via AI (Clay's AI agent can research anything)

**Coverage:** Broad -- the waterfall approach means if one provider misses, the next tries. Best for B2B contact data. Weaker for very small local businesses with no web presence.

**Accuracy:** Varies by provider in the waterfall. Clay's approach improves overall accuracy by cross-referencing multiple sources. Email accuracy is typically 85-95% before verification.

**Your Existing Integration:** You already have a Clay account and are familiar with the platform. This is a core advantage.

**API Details:**
- Clay provides a REST API for programmatic table operations
- Enrichment can be triggered via API or webhook
- Clay "Claygent" AI agent can perform custom research tasks

**Cost:**
- Starter: $149/month (2,400 credits)
- Explorer: $349/month (6,000 credits)
- Pro: $800/month (unlimited tables, 24,000 credits)
- Credits: each enrichment step costs 1-5 credits depending on provider
- Effective cost per contact: $0.15-0.50 depending on waterfall depth

**Rate Limits:** Depends on plan. API calls are rate-limited but sufficient for agency volumes.

**Integration Notes:**
- Clay tables can be created and populated via API
- Webhook triggers allow OpenClaw to initiate enrichment
- Results can be exported or sent to downstream systems via Clay's integrations
- Clay's AI agent is powerful for custom research that APIs can't handle

**OpenClaw Integration:**
```
Tool: clay_enrich_contact
Input: company_name, website, location (any available seed data)
Output: enriched contact record with email, phone, LinkedIn, etc.

Tool: clay_ai_research
Input: research_prompt, target_info
Output: custom research results (e.g., "find the owner of this plumbing company")
```

---

### 3. ZeroBounce (Email Verification)

**What it provides:**
- Email validity status: valid, invalid, catch-all, spamtrap, abuse, do-not-mail, unknown
- Deliverability score (0-100)
- Email provider/host
- First seen / last seen dates
- Gender guess based on first name
- Location data associated with email
- Free email detection (Gmail, Yahoo, etc.)
- Disposable email detection

**Coverage:** Verifies any email address worldwide. Does not find emails -- only verifies ones you already have.

**Accuracy:** Industry-leading 98%+ accuracy on valid/invalid classification. Catch-all domains remain uncertain by nature.

**Your Existing Integration:** You already use ZeroBounce for email verification.

**API Details:**
- Single email verification: real-time, ~1-3 second response
- Batch verification: upload CSV, process async
- AI scoring: predictive deliverability score

**Cost:**
- Pay-as-you-go: $0.008 per email verification
- Bulk plans: 2,000 for $16 ($0.008/ea), 10,000 for $64 ($0.0064/ea)
- Monthly plans available for consistent volume

**Rate Limits:** 20 requests per second on single verify. Batch has no per-second limit.

**Integration Notes:**
- Simple REST API with API key authentication
- Only verify emails you actually plan to use (cost optimization)
- Cache verification results -- valid emails don't need re-verification for 30-90 days
- Catch-all results: treat as "maybe" -- send but expect some bounces

**OpenClaw Integration:**
```
Tool: zerobounce_verify
Input: email_address
Output: status (valid/invalid/catch-all/etc.), score, details
```

---

### 4. BuiltWith (Technology Detection)

**What it provides:**
- Complete technology stack of any website:
  - CMS: WordPress, Wix, Squarespace, Shopify, custom
  - Analytics: Google Analytics (GA4 vs UA), Hotjar, Mixpanel
  - Advertising: Google Ads, Facebook Pixel, LinkedIn Insight
  - Marketing: Mailchimp, HubSpot, Marketo, ActiveCampaign
  - Chat: Intercom, Drift, LiveChat, Tawk.to
  - Hosting: AWS, Cloudflare, Vercel, GoDaddy
  - Ecommerce: Shopify, WooCommerce, BigCommerce
  - Frameworks: React, Vue, Angular, jQuery
  - CDN, SSL, payment processors, and more
- Technology spending estimate
- Technology change history

**Coverage:** Any website with detectable technologies. Tracks 100,000+ web technologies across 250M+ websites.

**Accuracy:** Very high for detectable technologies (JavaScript libraries, meta tags, DNS records, HTTP headers). Cannot detect server-side-only technologies.

**API Details:**
- Domain API: full technology profile for a domain
- Technology API: list all sites using a specific technology
- Keywords API: technology lookup by keyword

**Cost:**
- Basic API: $295/month (500 lookups)
- Pro API: $495/month (unlimited lookups)
- Per-lookup pricing: ~$0.10-0.59 depending on plan
- Free alternative: BuiltWith free lookup (manual, limited)

**Rate Limits:** Varies by plan. Pro plan has generous limits.

**Integration Notes:**
- Technology detection is key for lead scoring -- it reveals marketing sophistication
- WordPress sites without SEO plugins = high-value target
- Sites already running Google Ads = may not need basic services but could need optimization
- No analytics = strong signal they need help

**OpenClaw Integration:**
```
Tool: builtwith_lookup
Input: domain (e.g., "acmeplumbing.com")
Output: technology stack categorized by type
```

**Cost Optimization:** Before paying for BuiltWith API, try free detection methods:
- Wappalyzer browser extension data (limited API available)
- Custom Playwright scraper checking for common tech signatures
- Check page source for common script tags (GA, FB pixel, etc.)

---

### 5. DataForSEO (SEO and Search Data)

**What it provides:**
- **SERP data:** Google search results for any query/location
- **Keyword data:** search volume, CPC, competition, keyword suggestions
- **Backlink data:** referring domains, anchor text, authority metrics
- **On-page SEO audit:** technical issues, content analysis, page speed
- **Domain analytics:** traffic estimates, top keywords, competitor overlap
- **Google Maps SERP:** local pack results for queries
- **Business data:** Google Business Profile data via their API

**Coverage:** Global coverage for SERP and keyword data. Backlink database covers billions of pages.

**Accuracy:** SERP data is real-time and highly accurate. Traffic estimates are modeled and approximate. Keyword volume data is sourced from Google and reliable.

**Your Existing Integration:** You have a $49/month DataForSEO plan.

**API Details:**
- Task-based async API (POST task, GET results)
- Real-time API for immediate results (costs more credits)
- Multiple API endpoints organized by data type

**Cost:**
- Your plan: $49/month (prepaid balance, pay per task)
- SERP API: ~$0.002-0.004 per result
- Keyword data: ~$0.05 per keyword batch
- Backlinks: ~$0.02 per domain
- On-page audit: ~$0.05 per page
- Effective per-lead cost: ~$0.05-0.15 for SEO health check

**Rate Limits:** 2,000 requests per minute for most endpoints.

**Integration Notes:**
- Use SERP API to check where a business ranks for their key terms
- On-page audit reveals specific issues you can pitch fixing
- Backlink profile shows authority and link-building opportunities
- Combine with keyword data to identify opportunity gaps

**OpenClaw Integration:**
```
Tool: dataforseo_serp_check
Input: keyword, location, domain
Output: ranking position, SERP features, competitors

Tool: dataforseo_site_audit
Input: domain
Output: SEO issues, scores, recommendations

Tool: dataforseo_keywords
Input: seed_keywords, location
Output: keyword suggestions with volume and difficulty
```

---

### 6. Serper (Google Search API)

**What it provides:**
- Google Search results (organic, paid, featured snippets, knowledge panels)
- Google News results
- Google Images results
- Google Maps results
- People Also Ask data
- Related searches
- Real-time results matching what users actually see

**Coverage:** Any Google search query, any location. Real-time.

**Accuracy:** Extremely high -- returns actual Google SERP data.

**Your Existing Integration:** You have an active Serper plan.

**API Details:**
- Simple REST API: POST query, GET results
- Location targeting via `gl` (country) and `location` parameters
- Returns structured JSON with all SERP elements

**Cost:**
- Free tier: 2,500 queries
- Starter: $50/month (50,000 queries)
- Per-query cost: ~$0.001

**Rate Limits:** Generous -- varies by plan.

**Integration Notes:**
- Faster and cheaper than DataForSEO for simple SERP checks
- Use Serper for quick "does this business rank?" checks
- Use DataForSEO for deeper SEO analysis
- Excellent for competitive research: search competitor keywords

**OpenClaw Integration:**
```
Tool: serper_search
Input: query, location, type (search/news/images/maps)
Output: SERP results with titles, URLs, snippets, positions
```

---

### 7. LinkedIn Sales Navigator

**What it provides:**
- Advanced people search with 30+ filters
- Company search with firmographic filters
- Lead recommendations based on your ideal customer profile
- InMail messaging to non-connections
- CRM integration (Salesforce, HubSpot)
- Real-time alerts on lead activity (job changes, posts, mentions)
- Account mapping (organizational charts)

**Coverage:** 900M+ members globally. Best for B2B, professional services, and decision-maker identification.

**Accuracy:** High -- data is self-reported by users. Job titles and company associations are generally current.

**API Details:**
- Sales Navigator API requires partnership agreement
- Limited to approved use cases
- Most agencies use Sales Navigator UI manually or via semi-automated tools

**Cost:**
- Sales Navigator Core: $99/month (billed annually)
- Sales Navigator Advanced: $149/month
- Sales Navigator Advanced Plus: $1,600/year
- Per-lead cost: effectively $0.50-2.00 depending on volume

**Rate Limits:** API access is restricted. UI usage has implicit limits (connection requests, messages).

**Integration Notes:**
- Expensive but valuable for B2B lead identification
- Not required for local service businesses (Google Places is better)
- Consider only if targeting B2B clients or larger companies
- OpenClaw can help research profiles, but sending messages requires human review

---

### 8. Clearbit (now part of HubSpot)

**What it provides:**
- Company enrichment: industry, size, revenue, tech stack, social profiles, description
- Person enrichment: name, title, company, social profiles, location
- Reveal: identify anonymous website visitors by company
- Prospector: find contacts matching your ICP at target companies

**Coverage:** Strong for tech companies and larger businesses. Weaker for small local businesses.

**Accuracy:** High for company data. Person data accuracy varies (75-90%).

**API Details:**
- REST API with API key
- Enrichment API: pass email or domain, get full profile
- Since HubSpot acquisition, increasingly tied to HubSpot ecosystem

**Cost:**
- Now bundled with HubSpot plans in many cases
- Standalone API: pricing varies, typically $99-999/month
- Per-enrichment cost: ~$0.10-0.25

**Integration Notes:**
- Less relevant for local service businesses than for SaaS/B2B
- Company enrichment useful for larger targets
- Consider as supplement, not primary source

---

### 9. Crunchbase

**What it provides:**
- Company profile: description, founding date, headquarters, employee count
- Funding history: rounds, amounts, investors, valuations
- Leadership: founders, CEO, key executives
- Acquisitions and IPOs
- News and press mentions
- Technology categories

**Coverage:** Strong for startups and funded companies. Limited for small local businesses.

**Cost:**
- Basic API: $29/month (200 calls/minute)
- Pro: $49/month
- Enterprise: custom pricing

**Integration Notes:**
- Most useful if targeting funded companies or tech businesses
- Not relevant for typical local service business leads
- Skip this source for home services pipeline

---

### 10. FullContact

**What it provides:**
- Identity resolution: match email/phone/social to a unified person profile
- Social profiles: LinkedIn, Twitter, Facebook, GitHub
- Demographic data: age range, gender, location
- Company association
- Professional history

**Coverage:** 300M+ profiles in the US. Strongest for consumer/individual data.

**Cost:**
- Free tier: 100 matches/month
- Starter: $99/month (2,500 matches)
- Per-match: ~$0.04-0.10

**Integration Notes:**
- Useful for resolving contact identity when you have partial data
- Can turn an email into a full social profile
- Moderate priority -- Clay waterfall often covers this

---

### 11. Google Business Profile API (via Google My Business)

**What it provides:**
- Manage GBP listings (your own or clients')
- Read reviews and respond
- Post updates, offers, events
- Access insights: search queries, views, actions
- Manage photos, hours, attributes

**Coverage:** Only for businesses you manage/own. Not for competitor research (use Places API for that).

**Cost:** Free

**Integration Notes:**
- Requires business verification/ownership
- Essential for client management once onboarded
- Not a lead enrichment source -- a client management tool

---

## Source Comparison Matrix

| Source | Coverage (Local Biz) | Accuracy | Cost/Lead | Speed | API Quality |
|--------|---------------------|----------|-----------|-------|-------------|
| Google Places | Excellent | Very High | $0.003-0.05 | Fast | Excellent |
| Clay.com | Good | High | $0.15-0.50 | Moderate | Good |
| ZeroBounce | N/A (verify only) | Very High | $0.008 | Fast | Excellent |
| BuiltWith | Good | Very High | $0.10-0.59 | Fast | Good |
| DataForSEO | Good | High | $0.05-0.15 | Moderate | Good |
| Serper | Good | Very High | $0.001 | Very Fast | Excellent |
| LinkedIn Sales Nav | Fair | High | $0.50-2.00 | Manual | Limited |
| Clearbit | Fair | High | $0.10-0.25 | Fast | Good |
| Crunchbase | Poor | High | $0.15-0.25 | Fast | Good |
| FullContact | Fair | Moderate | $0.04-0.10 | Fast | Good |

---

## Recommended Stack for Your Agency

### Tier 1: Essential (use for every lead)
1. **Google Places API** -- business discovery and basic data
2. **Website scraping (Playwright)** -- extract info from business website (free)
3. **DataForSEO** -- SEO health assessment (already paying)
4. **ZeroBounce** -- email verification (already using)

### Tier 2: Enrichment (use for qualified leads)
5. **Clay.com waterfall** -- contact finding (already using)
6. **BuiltWith / Wappalyzer** -- technology detection
7. **Serper** -- competitive SERP analysis (already using)

### Tier 3: Optional (use for high-value targets)
8. **LinkedIn Sales Navigator** -- decision-maker identification
9. **Clearbit** -- deep company enrichment

### Not Recommended for Your Use Case
- Crunchbase (targets funded startups, not local businesses)
- FullContact (Clay covers most of this)

---

## Data Source Integration Architecture

```
Lead Discovery (Google Places / Serper)
    |
    v
Basic Enrichment (Website scrape + BuiltWith)
    |
    v
SEO Analysis (DataForSEO)
    |
    v
Lead Scoring (apply score based on collected signals)
    |
    v  [Only if score in target range: 30-60]
Contact Finding (Clay waterfall)
    |
    v
Email Verification (ZeroBounce)
    |
    v
Enriched Lead Ready for Outreach
```

This architecture minimizes cost by filtering leads before expensive enrichment steps. Only leads that score within the target range proceed to contact finding, which is the most expensive step.

---

## Data Freshness and Caching Strategy

| Source | Cache Duration | Reason |
|--------|---------------|--------|
| Google Places | 7 days | Business info changes slowly |
| Website scrape | 14 days | Websites don't change often |
| BuiltWith | 30 days | Tech stacks change slowly |
| DataForSEO | 7 days | Rankings fluctuate weekly |
| Clay contacts | 90 days | Contact info is relatively stable |
| ZeroBounce | 60 days | Email validity rarely flips quickly |
| Serper SERP | 1 day | SERPs change constantly |

Caching reduces API costs by 30-50% for businesses in your ongoing territory coverage.

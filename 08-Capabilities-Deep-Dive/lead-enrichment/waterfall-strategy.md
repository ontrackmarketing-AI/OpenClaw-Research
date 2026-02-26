# Waterfall Enrichment Strategy

## Overview

Waterfall enrichment is a sequential data collection strategy where multiple sources are queried in a specific order, each adding data the previous source could not provide. The key principle: start with the cheapest, broadest sources and progressively move to more expensive, specialized ones. Stop enriching when sufficient data is collected or the lead is disqualified.

No single enrichment provider has complete data on any business. Google Places might have the phone number but not the owner's email. Clay might find the email but not the technology stack. DataForSEO reveals SEO health but not review sentiment. The waterfall combines all of these into a single, comprehensive lead record.

---

## Why Waterfall Matters

**Problem without waterfall:**
- You pay for expensive enrichment on every lead, including garbage
- You get incomplete data from a single source
- You waste credits on leads that will never convert
- Different sources have different strengths (coverage varies by industry, geography, company size)

**With waterfall:**
- Cost per lead drops 40-60% through pre-filtering
- Data completeness reaches 85-95% vs 50-70% from single source
- Each step adds only the data previous steps missed
- Expensive steps only run for qualified leads

---

## The OpenClaw Enrichment Waterfall

### Step 1: Google Places Discovery (Cost: ~$0.003/lead)

**Purpose:** Business basics -- confirm the business exists and get seed data.

**Data collected:**
- Business name (canonical, as listed on Google)
- Full address (street, city, state, ZIP)
- Phone number (primary)
- Website URL
- Google rating (1-5 stars)
- Total review count
- Business category (e.g., "Plumber", "HVAC Contractor")
- Operating hours
- Business status (open, temporarily closed, permanently closed)
- Place ID (for future lookups)

**Stop condition:** If business is permanently closed, has <3 reviews, or has no website, consider disqualifying immediately (unless your service includes building their web presence from scratch).

**Data quality notes:**
- Google Places data is self-managed by businesses and generally accurate
- Phone number may be a tracking number rather than direct line
- Website URL may be a Facebook page or Yelp listing (common for very small businesses)

**Implementation:**
```python
# Pseudocode for Step 1
result = google_places_details(place_id)
lead.name = result.name
lead.address = result.formatted_address
lead.phone = result.formatted_phone_number
lead.website = result.website
lead.google_rating = result.rating
lead.google_reviews = result.user_ratings_total
lead.category = result.types[0]
lead.hours = result.opening_hours
lead.enrichment_status = "step_1_complete"
```

---

### Step 2: Website Scrape (Cost: $0/lead -- self-hosted Playwright)

**Purpose:** Extract data directly from the business's website.

**Data collected:**
- Email address(es) found on site (mailto: links, text patterns)
- Social media links (Facebook, Instagram, LinkedIn, Twitter/X, YouTube)
- About page content (for AI analysis of business maturity)
- Service list / service pages
- Team/staff page (indicates company size)
- Contact form presence (vs just phone/email)
- Physical location(s) mentioned
- Service area mentioned
- Certifications, licenses, awards displayed
- Testimonials/reviews displayed on site
- Blog presence and last post date
- Call-to-action types (call now, book online, get quote, etc.)

**Stop condition:** If website is parked, under construction, or a single-page placeholder, flag as "minimal web presence" -- this is actually a strong lead signal (they need website help).

**Technical implementation:**
- Use Playwright (headless Chrome) for JavaScript-rendered sites
- Parse HTML for structured data (emails, phone patterns, social links)
- Screenshot the homepage for visual analysis (AI can assess design quality)
- Check robots.txt and sitemap.xml existence
- Measure page load time
- Run on your own infrastructure -- zero per-lead cost beyond compute

**Data extraction patterns:**
```
Email: regex for *@*.* in page text and mailto: hrefs
Phone: regex for (xxx) xxx-xxxx and xxx-xxx-xxxx patterns
Social: check for known social media domain patterns in all links
Services: look for /services/ pages or service-related headings
Team: look for /team/ or /about/ pages with multiple names
```

---

### Step 3: Technology Detection (Cost: ~$0.10/lead with BuiltWith, $0 with custom)

**Purpose:** Understand the business's current technology stack to assess digital sophistication and identify sales angles.

**Data collected:**
- CMS platform (WordPress, Wix, Squarespace, Shopify, custom)
- Analytics installed (Google Analytics GA4, Universal Analytics, none)
- Advertising pixels (Google Ads, Facebook Pixel, LinkedIn Insight Tag)
- Marketing tools (Mailchimp, HubSpot, ActiveCampaign, etc.)
- Chat widgets (Intercom, Drift, LiveChat, Tawk.to)
- Booking/scheduling tools (Calendly, Acuity, ServiceTitan)
- Review management (BirdEye, Podium, etc.)
- SSL certificate provider
- Hosting provider
- CDN usage

**What technology signals mean:**
| Finding | Implication | Sales Angle |
|---------|------------|-------------|
| No analytics | Not tracking visitors | "You don't know how many people visit your site" |
| WordPress + no updates | Security risk | "Your site may be vulnerable" |
| No Google Ads pixel | Not running paid ads | "Your competitors are advertising, you're not" |
| No chat widget | Missing lead capture | "Visitors leave without contacting you" |
| Wix/Squarespace | Limited customization | "You're held back by template limitations" |
| No email marketing | No nurture sequence | "You're losing repeat business" |

**Cost optimization:** Build a lightweight custom detector before paying for BuiltWith:
```javascript
// Custom tech detection via Playwright
const page = await browser.newPage();
await page.goto(url);
const html = await page.content();

const tech = {
  hasGA4: html.includes('gtag') || html.includes('G-'),
  hasFBPixel: html.includes('fbq(') || html.includes('facebook.com/tr'),
  hasGoogleAds: html.includes('googleads') || html.includes('conversion.js'),
  isWordPress: html.includes('wp-content') || html.includes('wp-includes'),
  isWix: html.includes('wix.com') || html.includes('wixsite'),
  isSquarespace: html.includes('squarespace'),
  hasChat: html.includes('intercom') || html.includes('drift') || html.includes('tawk'),
  hasMailchimp: html.includes('mailchimp') || html.includes('mc.js'),
};
```

This custom approach catches 70-80% of what BuiltWith catches at zero marginal cost. Reserve BuiltWith API for leads where you need deeper analysis.

---

### Step 4: SEO Health Assessment (Cost: ~$0.05/lead via DataForSEO)

**Purpose:** Evaluate the business's search engine visibility and identify specific SEO issues to pitch.

**Data collected:**
- Domain authority / trust score
- Total organic keywords ranking
- Estimated monthly organic traffic
- Top 10 ranking keywords (and positions)
- Top competitors in same local SERP
- Technical SEO issues (broken links, missing meta, slow speed, no mobile optimization)
- Local SEO signals (NAP consistency, local citations)
- Backlink count and quality
- Content analysis (thin content, missing H1s, duplicate title tags)

**What SEO signals mean:**
| Finding | Implication | Sales Angle |
|---------|------------|-------------|
| 0 organic keywords | Invisible in search | "Nobody can find you on Google" |
| <1000 monthly visits | Low traffic | "Your competitors get 10x more traffic" |
| No local citations | Weak local SEO | "You're not showing up in map searches" |
| Slow page speed | Bad user experience | "50% of visitors leave before your page loads" |
| No structured data | Missing rich snippets | "Your search listing looks plain vs competitors" |

**Stop condition:** If a business already ranks #1 for their main keywords and has strong organic traffic, they may not need your SEO services. Score adjusts upward (less likely to need you).

---

### Step 5: Contact Finding via Clay Waterfall (Cost: ~$0.15-0.50/lead)

**Purpose:** Find the owner/decision-maker's direct contact information.

**This step only runs for leads that scored in the target range (30-60) after Steps 1-4.**

**Clay's internal waterfall (in order):**
1. LinkedIn profile match (via company name + role)
2. Apollo.io database lookup
3. Hunter.io email finder
4. RocketReach
5. Lusha
6. ContactOut
7. Kaspr
8. Snov.io
9. FindThatLead
10. Custom Clay AI agent research

**Data collected:**
- Owner/decision-maker name
- Direct email address
- Direct phone number (mobile preferred)
- LinkedIn profile URL
- Job title
- How long in role

**Clay configuration for your use case:**
- Target roles: Owner, President, CEO, Managing Partner, Founder
- For small businesses (<10 employees), the owner is usually the right contact
- For larger businesses, target VP Marketing or Marketing Director
- Set Clay to stop after finding verified email + LinkedIn profile

---

### Step 6: Email Verification via ZeroBounce (Cost: ~$0.008/email)

**Purpose:** Verify that found email addresses are deliverable before outreach.

**This step only runs for emails found in Step 5 (or Step 2 website scrape).**

**Verification results and actions:**
| Status | Meaning | Action |
|--------|---------|--------|
| Valid | Email exists, server accepts mail | Proceed to outreach |
| Invalid | Email doesn't exist or bounces | Remove from list, try alternate |
| Catch-all | Domain accepts all emails, can't confirm specific address | Proceed with caution |
| Spamtrap | Known spam trap address | DO NOT send -- remove immediately |
| Abuse | Known complainer | DO NOT send -- remove immediately |
| Do Not Mail | Requested removal | DO NOT send -- respect preference |
| Unknown | Server didn't respond to verification | Retry once, then proceed with caution |

**Implementation:**
```python
# Only verify emails we intend to use
if lead.email and lead.score >= 30 and lead.score <= 60:
    result = zerobounce_verify(lead.email)
    lead.email_status = result.status
    lead.email_score = result.zerobounce_score

    if result.status in ['spamtrap', 'abuse', 'do_not_mail']:
        lead.email = None  # Clear bad email
        lead.email_status = 'disqualified'
```

---

### Step 7: Social Profile Enrichment (Cost: $0 -- public data scraping)

**Purpose:** Complete the lead profile with social media presence data.

**Data collected:**
- LinkedIn company page: follower count, posting frequency, employee count
- Facebook business page: likes, rating, posting frequency, ad library check
- Instagram: follower count, posting frequency, content quality
- YouTube: subscriber count, video count, last upload date
- Twitter/X: follower count, posting frequency
- Nextdoor business page presence

**What social signals mean:**
| Finding | Implication |
|---------|------------|
| No Facebook page | Missing major local marketing channel |
| Facebook with <100 likes | Minimal social investment |
| Instagram active, others dead | Selective social presence |
| No social profiles at all | Extreme marketing gap |
| Active on all platforms | May not need social help |

---

## Data Merge Logic

When multiple sources provide the same data field, use this priority order:

**Business name:** Google Places > Website > Clay
**Address:** Google Places > Website > Clay
**Phone:** Website (if direct) > Google Places > Clay
**Email:** Clay (verified) > Website scrape > Google Places
**Website:** Google Places > Clay > Manual search
**Social profiles:** Website (links section) > Clay > Manual search

**Conflict resolution rules:**
1. If phone numbers differ, store both -- Google may have tracking number, website may have direct line
2. If addresses differ slightly, prefer Google Places (standardized format)
3. If business name differs, prefer Google Places (canonical listing name)
4. If emails differ, verify both with ZeroBounce and keep all valid ones
5. Flag conflicts for human review when they involve key outreach data

---

## Enrichment Status Tracking

Each lead record maintains an enrichment status:

```
enrichment_status: {
  step_1_google_places: "complete" | "failed" | "pending",
  step_2_website_scrape: "complete" | "failed" | "skipped" | "pending",
  step_3_tech_detection: "complete" | "failed" | "skipped" | "pending",
  step_4_seo_analysis: "complete" | "failed" | "skipped" | "pending",
  step_5_contact_finding: "complete" | "failed" | "skipped" | "pending",
  step_6_email_verification: "complete" | "failed" | "skipped" | "pending",
  step_7_social_profiles: "complete" | "failed" | "skipped" | "pending",
  overall: "partial" | "complete" | "disqualified",
  last_enriched: "2026-02-05T10:30:00Z",
  total_cost: 0.47,
  errors: []
}
```

---

## Cost Per Lead at Each Waterfall Level

| After Step | Cumulative Cost | Data Completeness | Decision Possible |
|-----------|----------------|-------------------|-------------------|
| Step 1 (Google Places) | $0.003 | 25% | Basic qualification |
| Step 2 (Website scrape) | $0.003 | 40% | Website quality assessment |
| Step 3 (Tech detection) | $0.10 | 55% | Technology gap analysis |
| Step 4 (SEO analysis) | $0.15 | 70% | Full scoring possible |
| Step 5 (Contact finding) | $0.40 | 90% | Ready for outreach prep |
| Step 6 (Email verify) | $0.41 | 92% | Ready for email outreach |
| Step 7 (Social profiles) | $0.41 | 95% | Fully enriched lead |

**The critical insight:** After Step 4, you can score the lead and decide whether to invest in Steps 5-7. This means 40-60% of leads get filtered out at the $0.15 level, never reaching the $0.40+ level. This cuts your average cost per lead significantly.

---

## Caching and Re-enrichment

**Cache rules:**
- Google Places data: cache for 7 days
- Website scrape data: cache for 14 days
- Tech detection: cache for 30 days
- SEO data: cache for 7 days (rankings change frequently)
- Contact data: cache for 90 days
- Email verification: cache for 60 days

**Re-enrichment triggers:**
- Lead re-enters pipeline (e.g., revisits your website)
- Manual request for refresh
- Score decay timer expires (re-score every 90 days for active leads)
- Major event detected (new reviews, website change, etc.)

**Implementation:** Store `last_enriched_at` timestamp per source. On re-enrichment, only re-run sources whose cache has expired.

---

## Async Enrichment Architecture

Enrichment runs asynchronously to avoid blocking the pipeline:

```
1. Lead enters pipeline (e.g., from Google Places discovery)
2. Step 1 runs immediately (fast, cheap)
3. Steps 2-4 queued as background jobs (complete within minutes)
4. After Steps 1-4 complete: scoring runs automatically
5. If score qualifies: Steps 5-7 queued
6. When complete: lead marked "enrichment_complete"
7. Lead enters outreach queue
```

**Job queue implementation:**
- Use n8n workflows for orchestration
- Each step is a separate workflow node
- Error handling: retry failed steps up to 3 times, then mark as "failed"
- Status updates: webhook notifications on completion/failure
- Monitoring: dashboard shows enrichment queue depth, completion rates, error rates

---

## Waterfall Performance Metrics

Track these metrics to optimize the waterfall over time:

| Metric | Target | Action if Below |
|--------|--------|----------------|
| Step 1 success rate | >95% | Check Google API quota/key |
| Step 2 success rate | >80% | Improve scraper resilience |
| Step 3 success rate | >85% | Add fallback tech detection |
| Step 4 success rate | >90% | Check DataForSEO balance |
| Step 5 email found rate | >60% | Adjust Clay waterfall providers |
| Step 6 email valid rate | >75% | Check Clay data quality |
| Average cost per lead | <$0.50 | Tighten pre-filtering |
| Average enrichment time | <5 min | Optimize async pipeline |
| Filter rate (Steps 1-4) | 40-60% | Adjust scoring thresholds |

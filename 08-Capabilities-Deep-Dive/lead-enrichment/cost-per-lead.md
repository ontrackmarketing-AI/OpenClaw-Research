# Cost Per Lead Analysis

## Overview

Understanding the cost per lead (CPL) at each stage of the enrichment pipeline is critical for profitability. This document provides a detailed breakdown of every cost component, volume-based projections, optimization strategies, and ROI calculations specific to your agency's use case.

---

## Cost Breakdown by Enrichment Step

### Step 1: Google Places Discovery

| Item | Cost | Notes |
|------|------|-------|
| Place Search request | $0.032 | Returns up to 20 results per query |
| Place Details (Basic) | $0.017 | Name, address, business status |
| Place Details (Contact) | $0.003 | Phone, website, hours |
| Place Details (Atmosphere) | $0.005 | Rating, reviews, price level |
| **Effective cost per lead** | **~$0.003-0.05** | Depends on fields requested |

**Free tier impact:** Google provides $200/month free credit. At ~$0.03/lead for full details, that's ~6,600 free lookups per month. For most agency volumes, Google Places is effectively free.

**Optimization:** Use Place Search to find batches of 20 businesses per query ($0.032 for 20 = $0.0016 each). Only call Place Details for businesses that pass initial category/location filters.

---

### Step 2: Website Scraping

| Item | Cost | Notes |
|------|------|-------|
| Playwright scrape | $0.00 | Self-hosted, no per-request cost |
| Compute (VPS) | ~$5-20/month | Shared with other workloads |
| Proxy (if needed) | $0-50/month | Only if sites block datacenter IPs |
| **Effective cost per lead** | **$0.00** | Marginal cost is zero |

**Infrastructure:** Run Playwright on your existing infrastructure. A $20/month VPS can handle hundreds of scrapes per day. No external API cost.

**Optimization:** Set a 15-second timeout per site. Skip scraping if the website URL from Google Places is clearly not a real site (e.g., facebook.com, yelp.com links). Cache results for 14 days.

---

### Step 3: Technology Detection

| Item | Cost | Notes |
|------|------|-------|
| BuiltWith API (if used) | ~$0.10-0.59/lookup | Depends on plan |
| Custom detection (Playwright) | $0.00 | Built into Step 2 scrape |
| Wappalyzer API (alternative) | ~$0.01/lookup | Cheaper alternative |
| **Effective cost per lead** | **$0.00-0.10** | $0 if using custom detection |

**Recommendation:** Build custom tech detection into Step 2 (website scrape). Check for the 20 most common technologies via page source analysis. This covers 80% of what BuiltWith provides at zero marginal cost. Reserve BuiltWith API for edge cases or periodic validation of your custom detection accuracy.

**Custom detection covers:**
- Google Analytics (GA4 and Universal)
- Google Tag Manager
- Google Ads conversion tag
- Facebook Pixel
- WordPress, Wix, Squarespace, Shopify
- Mailchimp, HubSpot
- Intercom, Drift, Tawk.to, LiveChat
- jQuery, React, Vue (framework indicators)
- SSL/HTTPS

---

### Step 4: SEO Health Assessment

| Item | Cost | Notes |
|------|------|-------|
| DataForSEO domain overview | ~$0.02 | Basic domain metrics |
| DataForSEO keyword rankings | ~$0.02-0.05 | Top keywords for domain |
| DataForSEO on-page audit | ~$0.05 | Technical SEO issues |
| DataForSEO backlinks summary | ~$0.02 | Backlink profile overview |
| **Effective cost per lead** | **~$0.05-0.15** | Depends on depth |

**Your plan:** $49/month DataForSEO balance. At $0.10/lead, that covers ~490 leads per month before you need to top up. This is likely sufficient for your initial volume.

**Optimization:** Run a lightweight SEO check first (domain overview only, $0.02). Only run the full audit ($0.15) for leads that pass initial scoring from Steps 1-3.

---

### Step 5: Contact Finding (Clay Waterfall)

| Item | Cost | Notes |
|------|------|-------|
| Clay credits (basic enrichment) | ~$0.06/credit | Varies by plan |
| Average credits per contact | 3-8 credits | Depends on waterfall depth |
| **Effective cost per contact** | **$0.15-0.50** | Most expensive step |

**This is the gating cost.** Contact finding is the most expensive step. The entire waterfall strategy exists to ensure you only spend these credits on leads worth pursuing.

**Optimization:**
- Set Clay waterfall to stop after finding verified email + LinkedIn (don't run all 10+ providers)
- Skip this step entirely for leads scoring outside 30-60 range
- Use website-scraped emails first (free) before Clay waterfall
- Cache Clay results for 90 days

---

### Step 6: Email Verification (ZeroBounce)

| Item | Cost | Notes |
|------|------|-------|
| Single email verification | $0.008 | Standard pay-as-you-go |
| Bulk rate (10K+) | $0.0064 | Volume discount |
| **Effective cost per lead** | **~$0.008** | Only for leads with found emails |

**Optimization:** Only verify emails you plan to send to. If a lead has a website-scraped email AND a Clay-found email, verify both ($0.016 total) and use the valid one.

---

### Step 7: Social Profile Enrichment

| Item | Cost | Notes |
|------|------|-------|
| Public profile scraping | $0.00 | Self-hosted, public data |
| **Effective cost per lead** | **$0.00** | All social data is publicly available |

---

## Total Cost Per Fully Enriched Lead

### Scenario A: Full Pipeline (all steps)

| Step | Cost |
|------|------|
| Google Places | $0.03 |
| Website scrape | $0.00 |
| Tech detection (custom) | $0.00 |
| SEO assessment | $0.10 |
| Contact finding (Clay) | $0.30 |
| Email verification | $0.008 |
| Social profiles | $0.00 |
| **Total** | **$0.44** |

### Scenario B: Pre-filtered Pipeline (skip expensive steps for unqualified leads)

Assume 50% of leads are filtered out after Steps 1-4 (before expensive contact finding):

| Step | Leads Processed | Cost/Lead | Total Cost |
|------|----------------|-----------|------------|
| Google Places | 100 | $0.03 | $3.00 |
| Website scrape | 100 | $0.00 | $0.00 |
| Tech detection | 100 | $0.00 | $0.00 |
| SEO assessment | 100 | $0.10 | $10.00 |
| **Scoring filter** | **50 pass** | -- | -- |
| Contact finding | 50 | $0.30 | $15.00 |
| Email verification | 50 | $0.008 | $0.40 |
| Social profiles | 50 | $0.00 | $0.00 |
| **Total for 100 leads** | -- | -- | **$28.40** |
| **Average cost per lead** | -- | **$0.28** | -- |
| **Cost per qualified lead** | -- | **$0.57** | -- |

The pre-filtering reduces average cost per lead from $0.44 to $0.28 -- a 36% reduction.

---

## Volume Scenarios

### 100 Leads Per Month (Starting Phase)

| Item | Monthly Cost |
|------|-------------|
| Google Places API | $3.00 (covered by free tier) |
| Website scraping compute | $5.00 (shared VPS) |
| DataForSEO | $10.00 (from $49 balance) |
| Clay enrichment (50 qualified) | $15.00 |
| ZeroBounce (50 emails) | $0.40 |
| **Total monthly enrichment** | **$33.40** |
| **Existing tool subscriptions** | **$49 (DataForSEO) + Clay plan** |

### 500 Leads Per Month (Growth Phase)

| Item | Monthly Cost |
|------|-------------|
| Google Places API | $15.00 (mostly covered by free tier) |
| Website scraping compute | $10.00 (may need dedicated capacity) |
| DataForSEO | $49.00 (may need top-up) |
| Clay enrichment (250 qualified) | $75.00 |
| ZeroBounce (250 emails) | $2.00 |
| **Total monthly enrichment** | **$151.00** |
| **Cost per lead (average)** | **$0.30** |
| **Cost per qualified lead** | **$0.60** |

### 1,000 Leads Per Month (Scale Phase)

| Item | Monthly Cost |
|------|-------------|
| Google Places API | $30.00 |
| Website scraping compute | $20.00 |
| DataForSEO | $100.00 (need higher plan) |
| Clay enrichment (500 qualified) | $150.00 |
| ZeroBounce (500 emails) | $4.00 |
| **Total monthly enrichment** | **$304.00** |
| **Cost per lead (average)** | **$0.30** |
| **Cost per qualified lead** | **$0.61** |

### 5,000 Leads Per Month (Agency Scale)

| Item | Monthly Cost |
|------|-------------|
| Google Places API | $150.00 |
| Website scraping compute | $50.00 (dedicated server) |
| DataForSEO | $200.00 |
| Clay enrichment (2,500 qualified) | $750.00 |
| ZeroBounce (2,500 emails) | $16.00 |
| **Total monthly enrichment** | **$1,166.00** |
| **Cost per lead (average)** | **$0.23** |
| **Cost per qualified lead** | **$0.47** |

Volume discounts kick in at scale: Clay credits cost less per credit on higher plans, ZeroBounce offers bulk pricing, DataForSEO has unlimited plans.

---

## Cost Optimization Strategies

### 1. Pre-filter Aggressively (saves 40-60%)
Before running any paid enrichment:
- Filter by geography (only your service areas)
- Filter by business category (only industries you serve)
- Filter by Google rating (skip <3.0 stars -- reputation problems are hard to fix)
- Filter by review count (skip <3 reviews -- too new/small)
- Expected filter rate: 40-60% eliminated before paid steps

### 2. Batch Processing (saves 10-20%)
- Run enrichment in daily batches rather than real-time
- Batch API calls get volume discounts
- ZeroBounce batch verification: $0.0064 vs $0.008 (20% savings)
- DataForSEO task-based API is cheaper than real-time API

### 3. Cache Aggressively (saves 30-50% on repeat lookups)
- Business data doesn't change daily
- Cache Google Places: 7 days
- Cache website scrapes: 14 days
- Cache tech detection: 30 days
- Cache Clay contacts: 90 days
- If same business appears in multiple searches, use cached data

### 4. Tiered Enrichment (saves 20-30%)
- Tier 1 (free): Google Places + website scrape + custom tech detection
- Tier 2 (cheap): DataForSEO SEO check ($0.10)
- Tier 3 (expensive): Clay contact finding ($0.30)
- Only advance to next tier if previous tier data qualifies the lead

### 5. DIY Where Possible (saves $0.10-0.50/lead)
- Custom Playwright tech detection instead of BuiltWith ($0.10 saved)
- Custom email finding via website scraping before Clay ($0.30 saved for 20-30% of leads)
- Custom LinkedIn lookup via public profile URLs ($0.10 saved)

---

## ROI Calculation

### Assumptions
- Average client value: $3,000/month retainer
- Average client lifetime: 8 months (conservative)
- Client lifetime value (LTV): $24,000
- Outreach-to-meeting conversion: 3% (of qualified leads contacted)
- Meeting-to-client conversion: 25%
- Overall funnel: 0.75% of qualified leads become clients

### ROI at 500 Leads/Month

| Metric | Value |
|--------|-------|
| Leads enriched | 500 |
| Qualified leads (50%) | 250 |
| Leads contacted (outreach) | 250 |
| Meetings booked (3%) | 7.5 |
| New clients (25% close rate) | 1.9 |
| Monthly revenue from new clients | $5,700 |
| Monthly enrichment cost | $151 |
| **ROI (revenue / cost)** | **37.7x** |
| **LTV of clients acquired** | **$45,600** |
| **LTV ROI** | **302x** |

### Break-Even Analysis

How many clients do you need to cover enrichment costs?

| Monthly Volume | Monthly Enrichment Cost | Clients Needed (at $3K/mo) | Clients Expected |
|---------------|------------------------|---------------------------|-----------------|
| 100 leads | $33 | 0.01 clients | 0.4 clients |
| 500 leads | $151 | 0.05 clients | 1.9 clients |
| 1,000 leads | $304 | 0.10 clients | 3.8 clients |
| 5,000 leads | $1,166 | 0.39 clients | 18.8 clients |

**At every volume level, expected client acquisition far exceeds the break-even threshold.** Even at pessimistic conversion rates (half the assumed rates), the ROI remains strongly positive.

### Sensitivity Analysis

What if conversion rates are lower than expected?

| Outreach-to-Meeting Rate | Meeting-to-Client Rate | Clients per 500 Leads | Monthly Revenue | ROI |
|-------------------------|----------------------|---------------------|----------------|-----|
| 3% (base) | 25% (base) | 1.9 | $5,700 | 37.7x |
| 2% (pessimistic) | 20% (pessimistic) | 1.0 | $3,000 | 19.9x |
| 1% (very pessimistic) | 15% (worst case) | 0.4 | $1,125 | 7.5x |
| 5% (optimistic) | 30% (good) | 3.8 | $11,250 | 74.5x |

**Even in the worst-case scenario (1% meeting rate, 15% close rate), ROI is 7.5x.** Lead enrichment is not the bottleneck -- outreach quality and sales skills are.

---

## Cost Tracking Implementation

Track per-lead costs in your database for ongoing optimization:

```sql
-- Lead cost tracking table
CREATE TABLE lead_enrichment_costs (
    lead_id UUID REFERENCES leads(id),
    step VARCHAR(50),
    provider VARCHAR(50),
    cost_usd DECIMAL(6,4),
    credits_used INTEGER,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN,
    cached BOOLEAN DEFAULT FALSE
);

-- Monthly cost summary query
SELECT
    DATE_TRUNC('month', timestamp) as month,
    step,
    COUNT(*) as total_lookups,
    SUM(CASE WHEN cached THEN 0 ELSE cost_usd END) as actual_cost,
    SUM(cost_usd) as would_have_cost_without_cache,
    ROUND(AVG(cost_usd), 4) as avg_cost_per_lookup,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
FROM lead_enrichment_costs
GROUP BY DATE_TRUNC('month', timestamp), step
ORDER BY month DESC, step;

-- Per-lead total cost query
SELECT
    l.id,
    l.business_name,
    l.score,
    SUM(lec.cost_usd) as total_enrichment_cost,
    l.became_client,
    l.client_monthly_value
FROM leads l
JOIN lead_enrichment_costs lec ON l.id = lec.lead_id
GROUP BY l.id, l.business_name, l.score, l.became_client, l.client_monthly_value
ORDER BY total_enrichment_cost DESC;
```

### Airtable Tracking Alternative

If using Airtable instead of Supabase:
- Create an "Enrichment Costs" table linked to Leads table
- Fields: Lead (linked record), Step, Provider, Cost, Credits, Timestamp, Success, Cached
- Use Airtable rollup field on Leads table to sum total enrichment cost per lead
- Create an Airtable view filtered by month for cost reporting

---

## Monthly Cost Budget Template

| Category | Budget | Notes |
|----------|--------|-------|
| Google Places API | $0-30 | Free tier covers most |
| DataForSEO | $49-100 | Your existing plan |
| Clay.com | $149-349 | Depends on volume |
| ZeroBounce | $16-64 | Pay-as-you-go |
| Serper | $0-50 | Free tier may suffice |
| Infrastructure (VPS) | $20-50 | Playwright hosting |
| **Total monthly budget** | **$234-643** | **Scales with volume** |

Start with the lower end. Scale up only when lead volume justifies it. The beauty of pay-per-use APIs is that costs scale linearly with volume -- no large upfront commitments.

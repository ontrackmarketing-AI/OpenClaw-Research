# Clay Enrichment Cost Optimization

> Strategies to maximize enrichment value while minimizing Clay credit spend.

---

## Clay Credit Cost Breakdown

### Estimated Credit Costs Per Enrichment Type

| Enrichment Type | Credits | Notes |
|---|---|---|
| Company lookup (basic) | 1 | Name, domain, industry, size |
| Email finding (waterfall) | 2-5 | Tries multiple providers, cost varies by difficulty |
| Phone number finding | 3-5 | Direct/mobile numbers cost more |
| Full company enrichment | 5-10 | All available company data |
| Tech stack detection | 2-3 | CMS, analytics, ad tech |
| Social profile discovery | 1-2 | LinkedIn, Facebook, Instagram URLs |
| Email validation | 1 | ZeroBounce/NeverBounce verification |
| Job title/role | 1-2 | Current position and seniority |
| Revenue estimate | 2-3 | Annual revenue range |

### Full Pipeline Cost Per Lead

| Enrichment Stage | Credits | Cumulative |
|---|---|---|
| Stage 1: Google Places (free) | 0 | 0 |
| Stage 2: Tech detection | 2 | 2 |
| Stage 3: Contact finding | 4 | 6 |
| Stage 4: Email validation | 1 | 7 |
| Stage 5: Social profiles | 2 | 9 |
| Stage 6: Review analysis | 1 | 10 |
| Stage 7: SEO data | 3 | 13 |
| **Total (full pipeline)** | **~13** | |

---

## Optimization Strategy 1: Pre-Filter Before Enriching

**Impact: Saves 30-50% of credits by eliminating unqualified leads at Stage 1 (free).**

The Google Places API call costs fractions of a penny and provides enough data for basic qualification. Apply strict pre-filters before spending any Clay credits.

```python
def should_enrich(google_places_data: dict, target_criteria: dict) -> tuple[bool, str]:
    """Decide whether to spend credits on this lead."""

    # Hard disqualifiers (free to check)
    if not google_places_data.get("phone") and not google_places_data.get("website"):
        return False, "No phone or website - unreachable"

    if google_places_data.get("business_status") == "CLOSED_PERMANENTLY":
        return False, "Permanently closed"

    if google_places_data.get("category") not in target_criteria["target_industries"]:
        return False, f"Wrong industry: {google_places_data.get('category')}"

    # Chain detection (simple heuristic)
    chain_patterns = ["McDonald", "Subway", "Starbucks", "Walmart", "CVS", "Walgreens"]
    name = google_places_data.get("name", "")
    if any(chain in name for chain in chain_patterns):
        return False, "National chain detected"

    # Geographic filter
    if google_places_data.get("state") not in target_criteria.get("target_states", []):
        return False, "Outside service area"

    return True, "Passed pre-filters"
```

**Expected savings:**
- 1000 leads discovered via Google Places
- 400 eliminated by pre-filters (40%)
- 600 proceed to paid enrichment
- Credits saved: 400 * 13 avg = **5,200 credits saved**

---

## Optimization Strategy 2: Staged Enrichment

**Impact: Saves 20-30% of credits by stopping enrichment early for leads that fail mid-pipeline.**

Do not run all enrichment stages on every lead. Run cheap stages first, evaluate, and only proceed to expensive stages for leads that remain qualified.

```python
async def staged_enrichment(clay_client, lead: dict) -> dict:
    """Run enrichment in stages with qualification gates."""

    # Stage 2: Tech detection (2 credits)
    tech_data = await clay_client.enrich_tech_stack(lead["domain"])
    lead.update(tech_data)
    preliminary_score = quick_score(lead)

    if preliminary_score < 20:
        lead["enrichment_stopped_at"] = "stage_2"
        lead["stop_reason"] = f"Low preliminary score: {preliminary_score}"
        return lead  # Saved ~11 credits

    # Stage 3: Contact finding (4 credits)
    contact_data = await clay_client.find_contacts(lead["domain"], lead.get("name"))
    lead.update(contact_data)

    if not contact_data.get("email") and not contact_data.get("phone"):
        lead["enrichment_stopped_at"] = "stage_3"
        lead["stop_reason"] = "No contact info found"
        return lead  # Saved ~7 credits

    # Stage 4: Email validation (1 credit) - only if email found
    if contact_data.get("email"):
        validation = await clay_client.validate_email(contact_data["email"])
        lead.update(validation)

        if validation.get("status") == "invalid":
            lead["email"] = None  # Remove invalid email
            # Continue anyway - might have phone

    # Stage 5: Social profiles (2 credits)
    social = await clay_client.find_social_profiles(lead["domain"])
    lead.update(social)

    # Stage 6: Review analysis (1 credit)
    reviews = await clay_client.analyze_reviews(lead.get("google_place_id"))
    lead.update(reviews)

    # Stage 7: SEO data (3 credits) - ONLY for leads scoring 60+
    current_score = calculate_lead_score(lead)["score"]
    if current_score >= 60:
        seo_data = await clay_client.get_seo_data(lead["domain"])
        lead.update(seo_data)
    else:
        lead["seo_skipped"] = True
        # Saved 3 credits on cold leads

    return lead
```

**Expected savings per 600 enriched leads:**
- 100 stopped at Stage 2: saved 100 * 11 = 1,100 credits
- 50 stopped at Stage 3: saved 50 * 7 = 350 credits
- 250 cold leads skip SEO: saved 250 * 3 = 750 credits
- **Total saved: ~2,200 credits** (on top of pre-filter savings)

---

## Optimization Strategy 3: Cache Results

**Impact: Saves 100% of credits on repeat lookups.**

Never re-enrich a business that was enriched recently. Store enrichment results with timestamps and check before spending credits.

```python
class EnrichmentCache:
    """Cache enrichment results to avoid duplicate credit spend."""

    def __init__(self, storage):
        self.storage = storage  # Supabase, Airtable, or local SQLite
        self.ttl_days = {
            "tech_stack": 90,      # Tech changes slowly
            "contact_info": 60,    # People change jobs
            "social_profiles": 90, # Social accounts are stable
            "reviews": 30,         # Reviews change more often
            "seo_data": 30,        # SEO fluctuates
        }

    async def get_cached(self, domain: str, data_type: str) -> dict | None:
        """Check cache for recent enrichment data."""
        cached = await self.storage.get_enrichment(domain, data_type)
        if not cached:
            return None

        age_days = (datetime.utcnow() - cached["enriched_at"]).days
        if age_days > self.ttl_days.get(data_type, 60):
            return None  # Cache expired

        return cached["data"]

    async def store(self, domain: str, data_type: str, data: dict):
        """Store enrichment results in cache."""
        await self.storage.upsert_enrichment({
            "domain": domain,
            "data_type": data_type,
            "data": data,
            "enriched_at": datetime.utcnow().isoformat(),
        })

# Usage in enrichment pipeline:
async def enrich_with_cache(clay_client, cache: EnrichmentCache, lead: dict) -> dict:
    """Enrich using cache where possible."""
    domain = lead["domain"]

    # Check cache for tech stack
    cached_tech = await cache.get_cached(domain, "tech_stack")
    if cached_tech:
        lead.update(cached_tech)
        # Saved 2 credits
    else:
        tech_data = await clay_client.enrich_tech_stack(domain)
        lead.update(tech_data)
        await cache.store(domain, "tech_stack", tech_data)

    # ... repeat pattern for each enrichment type
    return lead
```

**Expected savings:**
- If 15% of leads are re-enrichments (re-scraping same area): saves 15% * 13 credits * count
- For 600 leads: ~90 cached hits * 13 credits = **~1,170 credits saved**

---

## Optimization Strategy 4: Batch Processing

**Impact: Potential 10-20% efficiency gain.**

Clay may offer better rates or performance for bulk operations vs individual API calls.

```python
async def batch_enrich(clay_client, leads: list[dict], batch_size: int = 50) -> list[dict]:
    """Process enrichment in batches for efficiency."""

    # Create a Clay table for this batch
    table = await clay_client.create_table(
        name=f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
        columns=[
            {"name": "Company Domain", "type": "text"},
            {"name": "Company Name", "type": "text"},
            {"name": "Phone", "type": "text"},
        ]
    )

    # Add all rows at once (single API call)
    rows = [{"Company Domain": l["domain"], "Company Name": l["name"],
             "Phone": l.get("phone", "")} for l in leads]
    await clay_client.add_rows_bulk(table["id"], rows)

    # Trigger enrichment on the table (Clay processes internally)
    await clay_client.trigger_table_enrichment(table["id"])

    # Wait for completion
    enriched_rows = await clay_client.wait_for_table_completion(
        table["id"], timeout=300
    )

    return enriched_rows
```

---

## Optimization Strategy 5: Fallback to Direct APIs

**Impact: Can reduce costs by 50-70% for specific enrichment types when Clay credits are expensive.**

For some data points, direct API calls to individual providers may be cheaper than Clay credits.

| Data Type | Clay Cost | Direct API Cost | Cheaper Option |
|---|---|---|---|
| Tech stack | 2-3 credits | BuiltWith: ~$0.01/lookup | Direct (at scale) |
| Email validation | 1 credit | ZeroBounce: ~$0.007/email | Direct |
| Google reviews | 1-2 credits | Google Places: ~$0.005 | Direct |
| Email finding | 2-5 credits | Hunter: $0.01-0.03/search | Clay (waterfall value) |
| Company data | 5-10 credits | Clearbit: $0.10-0.50/lookup | Depends on volume |
| SEO data | 2-3 credits | DataForSEO: $0.002-0.01 | Direct |

**Hybrid approach:**
- Use Clay waterfall ONLY for email/phone finding (where waterfall adds real value)
- Use direct APIs for tech stack, email validation, reviews, SEO (cheaper individually)

```python
async def hybrid_enrichment(lead: dict) -> dict:
    """Use the cheapest provider for each data type."""

    # Direct APIs (cheaper for these specific lookups)
    lead["tech_stack"] = await builtwith_api.detect(lead["domain"])
    lead["google_reviews"] = await google_places_api.get_reviews(lead["place_id"])
    lead["seo_data"] = await dataforseo_api.get_rankings(lead["domain"])

    # Clay waterfall (better for contact finding due to waterfall)
    contact = await clay_client.find_contact(lead["domain"], lead.get("owner_name"))
    lead.update(contact)

    # Direct API for validation (cheaper)
    if lead.get("email"):
        lead["email_valid"] = await zerobounce_api.validate(lead["email"])

    return lead
```

---

## Monthly Budget Planning

### Scenario: 500 Leads Discovered Per Month

| Item | Count | Credits | Cost |
|---|---|---|---|
| Leads discovered | 500 | 0 | $0 (Google Places) |
| Pre-filter eliminated | -200 | 0 | $0 saved |
| Leads entering enrichment | 300 | | |
| Stopped at Stage 2 | -50 | 100 | |
| Stopped at Stage 3 | -25 | 150 | |
| Full enrichment (Stages 2-6) | 225 | 2,250 | |
| SEO data (Hot+Warm only) | 90 | 270 | |
| Cache hits avoided | -45 | 0 | -585 saved |
| **Total credits used** | | **~2,770** | |

**Monthly credit costs by plan:**

| Plan | Credits/mo | Price/mo | Cost per enriched lead |
|---|---|---|---|
| Starter (5K credits) | 5,000 | $149 | ~$0.50 |
| Explorer (25K credits) | 25,000 | $349 | ~$0.44 |
| Pro (100K credits) | 100,000 | $800 | ~$0.23 |

**For 500 leads/month, the Starter plan (5,000 credits at $149/mo) is sufficient** with optimization strategies applied.

Without optimization: 500 * 13 = 6,500 credits (would need Explorer plan).
With optimization: ~2,770 credits (comfortable on Starter plan).

**Savings: $200/month** by applying optimization strategies.

---

## Credit Monitoring and Alerts

```python
class CreditMonitor:
    """Track and alert on Clay credit usage."""

    def __init__(self, clay_client, alert_threshold: float = 0.8):
        self.clay = clay_client
        self.alert_threshold = alert_threshold
        self.daily_usage = []

    async def check_credits(self) -> dict:
        """Check credit balance and usage rate."""
        balance = await self.clay.get_credit_balance()
        remaining = balance["remaining"]
        total = balance["total"]
        used = balance["used"]
        usage_pct = used / total if total > 0 else 0

        status = {
            "remaining": remaining,
            "used": used,
            "total": total,
            "usage_percentage": usage_pct,
            "days_until_reset": balance.get("daysUntilReset", "unknown"),
        }

        # Calculate burn rate
        if self.daily_usage:
            avg_daily = sum(self.daily_usage) / len(self.daily_usage)
            days_remaining = remaining / avg_daily if avg_daily > 0 else float("inf")
            status["avg_daily_usage"] = avg_daily
            status["estimated_days_until_empty"] = days_remaining

        # Alert if approaching limit
        if usage_pct >= self.alert_threshold:
            status["alert"] = f"WARNING: {usage_pct*100:.0f}% of credits used"
            await self.send_alert(status)

        return status

    async def track_usage(self, credits_used: int, enrichment_type: str):
        """Track credit usage for a specific enrichment."""
        self.daily_usage.append(credits_used)
        # Log to Airtable or Supabase for reporting
        await self.log_usage(credits_used, enrichment_type)
```

---

## ROI Tracking

The ultimate measure: are enrichment credits generating more revenue than they cost?

```python
def calculate_enrichment_roi(monthly_data: dict) -> dict:
    """Calculate ROI on Clay enrichment spend."""
    credits_spent = monthly_data["credits_used"]
    credit_cost = monthly_data["plan_cost"]  # Monthly plan cost
    leads_enriched = monthly_data["leads_enriched"]
    meetings_booked = monthly_data["meetings_from_enriched_leads"]
    deals_closed = monthly_data["deals_closed"]
    revenue_from_deals = monthly_data["total_deal_value"]

    cost_per_enriched_lead = credit_cost / leads_enriched if leads_enriched > 0 else 0
    cost_per_meeting = credit_cost / meetings_booked if meetings_booked > 0 else 0
    cost_per_deal = credit_cost / deals_closed if deals_closed > 0 else 0
    roi = ((revenue_from_deals - credit_cost) / credit_cost) * 100 if credit_cost > 0 else 0

    return {
        "monthly_spend": credit_cost,
        "leads_enriched": leads_enriched,
        "cost_per_enriched_lead": f"${cost_per_enriched_lead:.2f}",
        "cost_per_meeting": f"${cost_per_meeting:.2f}",
        "cost_per_deal": f"${cost_per_deal:.2f}",
        "revenue_generated": f"${revenue_from_deals:,.0f}",
        "roi_percentage": f"{roi:.0f}%",
    }
```

**Target benchmarks:**
- Cost per enriched lead: < $1.00
- Cost per meeting booked: < $25.00
- Cost per deal closed: < $150.00
- ROI: > 500% (each $1 in enrichment cost generates $5+ in revenue)

---

## RESEARCH GAPS

- [ ] Verify exact credit costs per enrichment type on your specific Clay plan
- [ ] Test direct API costs vs Clay for tech stack and email validation
- [ ] Determine if Clay offers volume discounts or annual pricing
- [ ] Build the credit monitoring dashboard (Airtable or Supabase)
- [ ] Set up A/B test: full enrichment vs staged enrichment to compare lead quality
- [ ] Calculate actual ROI after first month of enriched lead outreach

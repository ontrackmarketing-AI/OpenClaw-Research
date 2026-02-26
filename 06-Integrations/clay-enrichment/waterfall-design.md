# Waterfall Enrichment Design

> The multi-stage enrichment sequence that transforms a raw business listing into a fully qualified, actionable lead.

---

## Enrichment Philosophy

Not every lead deserves full enrichment. Clay credits cost money, and time spent enriching unqualified leads is wasted. The waterfall design follows these principles:

1. **Cheapest data first** - Start with free/cheap sources, escalate to expensive ones only for qualified leads
2. **Fail fast** - If early signals disqualify a lead, stop enrichment immediately
3. **Map everything** - Every data point maps to a specific GHL field and influences the lead score
4. **Cache aggressively** - Never re-enrich a business that was enriched in the last 90 days

---

## Enrichment Sequence

### Stage 1: Basic Business Data (Cost: ~$0, Google Places API)

**Source:** Google Places API (you already have this in Rise Local pipeline)

**Data collected:**
| Field | Example | GHL Mapping |
|---|---|---|
| Business name | "Smith Family Dental" | `companyName` |
| Address | "123 Main St, Austin, TX 78701" | `address1`, `city`, `state`, `postalCode` |
| Phone | "+15125551234" | `phone` |
| Website | "www.smithdental.com" | `website` |
| Category | "Dentist" | `customField.industry` |
| Google rating | 4.2 | `customField.google_rating` |
| Review count | 87 | `customField.review_count` |
| Place ID | "ChIJ..." | `customField.google_place_id` |
| Business hours | Mon-Fri 8-5 | Not mapped (used for scoring) |
| Photos count | 15 | Not mapped (used for scoring) |

**Decision point after Stage 1:**
- No website and no phone? **DISQUALIFY** (cannot contact or assess)
- Wrong category for target vertical? **DISQUALIFY** (wrong industry)
- Google rating below 2.0? **FLAG** (may have fundamental business problems)
- Proceed to Stage 2 for all others

**Estimated cost:** $0.002-0.005 per lookup (Google Places API pricing)

### Stage 2: Technology Detection (Cost: ~1-2 Clay credits)

**Source:** BuiltWith API (via Clay waterfall)

**Data collected:**
| Field | Example | Scoring Impact |
|---|---|---|
| CMS | WordPress 5.x | +5 if outdated, -5 if modern |
| Analytics | None detected | +10 (major pain point) |
| Ad pixels | No Facebook Pixel | +5 (not running ads) |
| Chat widget | None | +5 (missing engagement tool) |
| SSL certificate | Yes/No | +10 if no SSL |
| CDN | None | +3 (performance opportunity) |
| Email provider | Gmail (not business) | +3 (unprofessional email) |
| E-commerce | None | Neutral |
| CRM/booking | None detected | +8 (no system for leads) |
| Speed/perf tools | None | +3 (speed opportunity) |

**Decision point after Stage 2:**
- Modern tech stack with CRM, analytics, and ads running? **LOWER PRIORITY** (less pain, harder sell)
- No analytics, no CRM, outdated CMS? **HIGH VALUE** (lots of pain, easy wins to sell)
- Proceed to Stage 3 for leads scoring 30+ after first two stages

### Stage 3: Contact Finding (Cost: ~3-5 Clay credits via waterfall)

**Source:** Clay waterfall across Apollo, Hunter, Clearbit, Lusha, ContactOut, RocketReach

**Goal:** Find the business owner or decision-maker's direct contact information.

**Data collected:**
| Field | Example | GHL Mapping |
|---|---|---|
| Owner/decision-maker name | "Dr. John Smith" | `firstName`, `lastName` |
| Work email | "john@smithdental.com" | `email` |
| Personal email | "jsmith@gmail.com" | `customField.personal_email` |
| Direct phone | "+15125559876" | Override `phone` if mobile |
| Job title | "Owner / Lead Dentist" | `customField.job_title` |
| LinkedIn URL | "linkedin.com/in/drjohnsmith" | `customField.social_linkedin` |

**Decision point after Stage 3:**
- No email AND no direct phone found? **FLAG** (can still reach via business phone, but lower priority)
- Email found but might be generic (info@, hello@)? Continue to Stage 4 for validation
- Direct owner email found? **HIGH VALUE** (can send personalized outreach)

### Stage 4: Email Validation (Cost: ~1 Clay credit)

**Source:** ZeroBounce or NeverBounce (via Clay)

**Data collected:**
| Field | Result | Action |
|---|---|---|
| Email status | Valid | Proceed with outreach |
| Email status | Invalid | Remove email, try alternate |
| Email status | Catch-all | Risky but usable, note in record |
| Email status | Disposable | **DISQUALIFY** this email |
| Email status | Abuse/spam trap | **DO NOT SEND** |

**Decision point after Stage 4:**
- Valid email? Proceed to Stage 5
- Invalid email, no phone? Attempt to find alternate email
- All emails invalid? Use phone-only outreach path

### Stage 5: Social Profiles (Cost: ~1-2 Clay credits)

**Source:** Various social data providers via Clay

**Data collected:**
| Field | Example | GHL Mapping |
|---|---|---|
| LinkedIn (business) | "linkedin.com/company/smith-dental" | `customField.social_linkedin_company` |
| Facebook page | "facebook.com/SmithDentalAustin" | `customField.social_facebook` |
| Instagram | "@smithdentalatx" | `customField.social_instagram` |
| Twitter/X | "@SmithDental" | `customField.social_twitter` |
| YouTube | "youtube.com/@smithdental" | Not mapped unless relevant |

**Scoring impact:**
- No social profiles at all: +10 (major pain, easy service to sell)
- Facebook only, inactive: +5 (partial presence, room to improve)
- Active on 3+ platforms: -5 (already investing in social, harder sell on basics)

### Stage 6: Review Deep Dive (Cost: ~1-2 Clay credits or custom scrape)

**Source:** Google Reviews data, Yelp, industry-specific review sites

**Data collected:**
| Field | Example | Scoring Impact |
|---|---|---|
| Average rating | 3.8/5 | +5 if below 4.0 |
| Total reviews | 23 | +8 if fewer than 20 |
| Recent review trend | Declining | +5 (business may be struggling) |
| Negative review themes | "Long wait", "Hard to book" | Specific pain points for outreach |
| Response rate | 10% of reviews have owner reply | +5 if low (reputation management opportunity) |
| Yelp rating | 3.5/5 | Additional data point |

### Stage 7: SEO and Visibility (Cost: ~2-3 Clay credits or DataForSEO API)

**Source:** DataForSEO, SEMrush, or Ahrefs data via Clay or direct API

**Data collected:**
| Field | Example | Scoring Impact |
|---|---|---|
| Domain authority | 15 | +5 if below 20 |
| Organic traffic estimate | 200/mo | +8 if below 500/mo |
| Top ranking keywords | 3 keywords in top 10 | -3 (some SEO investment) |
| Local pack ranking | Not in top 3 | +10 (major visibility gap) |
| Backlink count | 45 | Baseline metric |
| Page speed score | 35/100 | +5 if below 50 |
| Mobile-friendly | No | +10 (critical issue) |

---

## Complete Enrichment Flow with Decision Gates

```
START: Raw business listing (name, address, category)
  |
  v
[Stage 1: Google Places] -- Cost: ~$0.003
  |
  |-- DISQUALIFY if: no phone AND no website
  |-- DISQUALIFY if: wrong industry category
  |-- FLAG if: Google rating < 2.0
  |
  v
[Stage 2: Tech Detection] -- Cost: ~1-2 credits
  |
  |-- LOWER PRIORITY if: modern stack + CRM + analytics + ads
  |-- Continue if: cumulative score >= 30
  |-- DEFER if: cumulative score 20-29 (backlog for later)
  |
  v
[Stage 3: Contact Finding] -- Cost: ~3-5 credits
  |
  |-- FLAG if: no email and no direct phone found
  |-- Continue with best available contact info
  |
  v
[Stage 4: Email Validation] -- Cost: ~1 credit
  |
  |-- Remove invalid emails
  |-- Note catch-all domains
  |
  v
[Stage 5: Social Profiles] -- Cost: ~1-2 credits
  |
  |-- Update scoring based on social presence
  |
  v
[Stage 6: Review Analysis] -- Cost: ~1-2 credits
  |
  |-- Extract pain points from negative reviews
  |-- Update score based on reputation signals
  |
  v
[Stage 7: SEO Data] -- Cost: ~2-3 credits (ONLY for Hot/Warm leads)
  |
  |-- Final scoring adjustment
  |
  v
FINAL: Fully enriched lead with score -> Route to GHL pipeline
```

---

## Data Mapping Summary

Complete mapping from enrichment data to GHL contact record:

```python
def build_ghl_contact_from_enrichment(enrichment: dict) -> dict:
    """Build a complete GHL contact from all enrichment stages."""
    return {
        # Core fields
        "firstName": enrichment.get("owner_first_name", ""),
        "lastName": enrichment.get("owner_last_name", ""),
        "email": enrichment.get("validated_email", ""),
        "phone": enrichment.get("direct_phone") or enrichment.get("business_phone", ""),
        "companyName": enrichment.get("business_name", ""),
        "website": enrichment.get("website", ""),
        "address1": enrichment.get("address", ""),
        "city": enrichment.get("city", ""),
        "state": enrichment.get("state", ""),
        "postalCode": enrichment.get("zip", ""),
        "source": "OpenClaw Enrichment Pipeline",

        # Custom fields
        "customFields": {
            "lead_score": enrichment.get("final_score", 0),
            "industry": enrichment.get("category", ""),
            "google_rating": enrichment.get("google_rating", 0),
            "review_count": enrichment.get("review_count", 0),
            "tech_stack": ", ".join(enrichment.get("technologies", [])),
            "website_score": enrichment.get("website_score", 0),
            "social_linkedin": enrichment.get("linkedin_url", ""),
            "social_facebook": enrichment.get("facebook_url", ""),
            "social_instagram": enrichment.get("instagram_handle", ""),
            "employee_count": enrichment.get("employee_count", 0),
            "annual_revenue": enrichment.get("revenue_estimate", 0),
            "pain_signals": ", ".join(enrichment.get("pain_signals", [])),
            "enrichment_date": datetime.utcnow().isoformat(),
        },

        # Tags
        "tags": build_tags_from_enrichment(enrichment),
    }
```

---

## Cost Optimization Through Decision Gates

**Worst case (no gates):** All 7 stages on every lead = ~12-18 credits per lead

**With decision gates:**
- 40% disqualified at Stage 1 (free): 0 credits wasted
- 15% deferred at Stage 2: 1-2 credits spent
- Remaining 45% get full enrichment: 10-15 credits
- Stage 7 only on Hot/Warm (top 30%): saves 2-3 credits on Cold leads

**Effective cost with gates:** ~5-7 credits per lead on average (vs 12-18 without gates)

**Monthly budget example for 500 leads discovered:**
- 200 disqualified at Stage 1: $0
- 75 deferred at Stage 2: 150 credits
- 225 fully enriched: 2,250 credits
- 135 get SEO data (Stages 1-7): 400 credits
- **Total: ~2,800 credits for 500 leads** (vs 9,000 without gates)

---

## RESEARCH GAPS

- [ ] Verify exact credit costs per enrichment type on your Clay plan
- [ ] Test waterfall completion times for each stage
- [ ] Determine if Clay supports conditional enrichment (skip columns based on previous column results)
- [ ] Verify Google Places API pricing for your usage volume
- [ ] Test DataForSEO API as alternative to Clay for SEO data (may be cheaper)
- [ ] Determine optimal cache duration (90 days suggested, may vary by data type)

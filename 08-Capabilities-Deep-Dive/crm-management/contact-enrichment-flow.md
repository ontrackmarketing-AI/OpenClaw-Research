# Contact Enrichment Flow: Raw Lead to Enriched GHL Contact

## Overview

This document defines the complete end-to-end flow for transforming a raw lead into a fully enriched, scored, and properly categorized GoHighLevel contact. The flow covers every step from initial lead arrival through data validation, multi-source enrichment, verification, scoring, CRM population, pipeline assignment, and team notification. Target completion time for the full flow is under 5 minutes per lead.

## Flow Diagram

```
Lead Arrives (Form / Scraper / Manual / Referral / Ad)
    |
    v
[1] Basic Validation & Deduplication
    |
    v
[2] Business Enrichment (Google Places, BuiltWith, Company Data)
    |
    v
[3] Contact Enrichment (Clay Waterfall: Owner Email/Phone)
    |
    v
[4] Email Verification (ZeroBounce)
    |
    v
[5] Pain Scoring (15-Signal Analysis)
    |
    v
[6] GHL Contact Creation (Map All Fields)
    |
    v
[7] Pipeline Assignment (Score + Source Based)
    |
    v
[8] Tag Application (Industry, Source, Score, Needs)
    |
    v
[9] Task Creation (Follow-Up Tasks for Team)
    |
    v
[10] Notification (Alert Team for High-Value Leads)
    |
    v
[11] Workflow Enrollment (GHL Automation Sequences)
```

## Step 1: Basic Validation and Deduplication

### Purpose
Confirm the lead represents a real business and is not already in the CRM.

### Process

```python
async def validate_and_deduplicate(lead: dict) -> dict:
    """
    Validate lead data and check for duplicates.
    Returns: validated lead dict or raises DuplicateError/InvalidError.
    """
    result = {"valid": False, "duplicate": False, "errors": []}

    # --- Data Normalization ---
    lead["business_name"] = normalize_business_name(lead.get("business_name", ""))
    lead["phone"] = normalize_phone(lead.get("phone", ""))
    lead["email"] = normalize_email(lead.get("email", ""))
    lead["website"] = normalize_url(lead.get("website", ""))

    # --- Required Field Validation ---
    if not lead.get("business_name"):
        result["errors"].append("Missing business name")
    if not lead.get("phone") and not lead.get("email") and not lead.get("website"):
        result["errors"].append("No contact method (need phone, email, or website)")

    if result["errors"]:
        result["valid"] = False
        return result

    # --- Deduplication Check ---
    # Search GHL by phone
    if lead.get("phone"):
        existing = await ghl.search_contacts(phone=lead["phone"])
        if existing:
            result["duplicate"] = True
            result["existing_contact_id"] = existing[0]["id"]
            return result

    # Search GHL by email
    if lead.get("email"):
        existing = await ghl.search_contacts(email=lead["email"])
        if existing:
            result["duplicate"] = True
            result["existing_contact_id"] = existing[0]["id"]
            return result

    # Search GHL by business name (fuzzy match)
    if lead.get("business_name"):
        existing = await ghl.search_contacts(company=lead["business_name"])
        if existing:
            # Fuzzy match: check if business name is >85% similar
            for contact in existing:
                similarity = fuzz.ratio(
                    lead["business_name"].lower(),
                    (contact.get("companyName") or "").lower()
                )
                if similarity > 85:
                    result["duplicate"] = True
                    result["existing_contact_id"] = contact["id"]
                    result["similarity"] = similarity
                    return result

    result["valid"] = True
    return result
```

### Duplicate Handling

| Scenario | Action |
|----------|--------|
| Exact phone match | Skip creation, update existing contact with new data |
| Exact email match | Skip creation, update existing contact |
| Business name >85% similar | Flag for manual review |
| Different person, same company | Create new contact, link to company |
| No match found | Proceed with enrichment |

### Error Handling
- Log all validation failures with reason
- Store invalid leads in a "review queue" for manual inspection
- Track validation failure rates by lead source (quality indicator)

## Step 2: Business Enrichment

### Purpose
Gather comprehensive business information from public sources.

### Data Sources and Priority Order

```python
async def enrich_business(lead: dict) -> dict:
    """Enrich with business-level data from multiple sources."""
    enriched = {}

    # Source 1: Google Places API
    # Cost: ~$0.003 per request (Place Details)
    if lead.get("business_name") and lead.get("city"):
        places_data = await google_places.find_place(
            query=f"{lead['business_name']} {lead['city']} {lead.get('state', '')}",
            fields=["place_id", "name", "formatted_address", "formatted_phone_number",
                     "website", "rating", "user_ratings_total", "types",
                     "business_status", "opening_hours"]
        )
        if places_data:
            enriched["google_rating"] = places_data.get("rating")
            enriched["review_count"] = places_data.get("user_ratings_total")
            enriched["google_place_id"] = places_data.get("place_id")
            enriched["verified_address"] = places_data.get("formatted_address")
            enriched["verified_phone"] = places_data.get("formatted_phone_number")
            enriched["verified_website"] = places_data.get("website")
            enriched["business_status"] = places_data.get("business_status")
            enriched["business_categories"] = places_data.get("types", [])

    # Source 2: BuiltWith (Website Technology)
    # Cost: depends on plan, ~$0.01-0.05 per lookup
    if enriched.get("verified_website") or lead.get("website"):
        website = enriched.get("verified_website") or lead["website"]
        tech_data = await builtwith.lookup(website)
        if tech_data:
            enriched["website_platform"] = tech_data.get("cms")  # WordPress, Wix, etc.
            enriched["has_analytics"] = "google-analytics" in tech_data.get("analytics", [])
            enriched["has_ads"] = any(
                ad in tech_data.get("advertising", [])
                for ad in ["google-ads", "facebook-pixel"]
            )
            enriched["tech_stack"] = tech_data.get("technologies", [])

    # Source 3: DataForSEO (SEO Data)
    # Cost: varies by endpoint, ~$0.01-0.05 per lookup
    if enriched.get("verified_website") or lead.get("website"):
        domain = extract_domain(enriched.get("verified_website") or lead["website"])
        seo_data = await dataforseo.domain_overview(domain)
        if seo_data:
            enriched["organic_traffic"] = seo_data.get("estimated_traffic")
            enriched["domain_authority"] = seo_data.get("domain_rank")
            enriched["total_keywords"] = seo_data.get("total_keywords")
            enriched["top_keywords"] = seo_data.get("top_keywords", [])[:5]

    # Source 4: Social Media Presence
    # Check for social media profiles
    enriched["social_profiles"] = await find_social_profiles(
        business_name=lead["business_name"],
        website=enriched.get("verified_website") or lead.get("website")
    )

    return enriched
```

### Business Enrichment Data Map

| Data Point | Source | GHL Custom Field | Relevance |
|-----------|--------|-------------------|-----------|
| Google Rating | Google Places | `google_rating` | Quality indicator |
| Review Count | Google Places | `review_count` | Online reputation |
| Place ID | Google Places | `google_place_id` | GMB management |
| Address | Google Places | Standard address fields | Verification |
| Website Platform | BuiltWith | `website_platform` | Service opportunity |
| Has Google Analytics | BuiltWith | `has_analytics` | Service gap |
| Has Paid Ads | BuiltWith | `has_paid_ads` | Current marketing |
| Organic Traffic | DataForSEO | `organic_traffic` | SEO opportunity |
| Domain Authority | DataForSEO | `domain_authority` | SEO baseline |
| Social Presence | Multi-source | `social_platforms` | Social opportunity |

## Step 3: Contact Enrichment (Clay Waterfall)

### Purpose
Find the business owner's direct email address and phone number using a multi-provider waterfall approach.

### Process

```python
async def enrich_contact_info(lead: dict, business_data: dict) -> dict:
    """
    Use Clay-style waterfall to find owner contact info.
    Try multiple providers in sequence, stop when verified data found.
    """
    contact = {}

    # Waterfall for email
    email_providers = [
        ("apollo", apollo_find_email),
        ("hunter", hunter_find_email),
        ("snov", snov_find_email),
        ("dropcontact", dropcontact_find_email),
    ]

    for provider_name, provider_func in email_providers:
        try:
            result = await provider_func(
                company_name=lead["business_name"],
                domain=extract_domain(business_data.get("verified_website", lead.get("website", ""))),
                first_name=lead.get("first_name"),
                last_name=lead.get("last_name")
            )
            if result and result.get("email"):
                contact["owner_email"] = result["email"]
                contact["email_source"] = provider_name
                contact["owner_name"] = result.get("full_name")
                contact["owner_title"] = result.get("title")
                break
        except Exception as e:
            logger.warning(f"Email provider {provider_name} failed: {e}")
            continue

    # Waterfall for phone (if not already available)
    if not lead.get("phone"):
        phone_providers = [
            ("apollo", apollo_find_phone),
            ("lusha", lusha_find_phone),
        ]
        for provider_name, provider_func in phone_providers:
            try:
                result = await provider_func(
                    name=contact.get("owner_name", lead.get("business_name")),
                    company=lead["business_name"],
                    email=contact.get("owner_email")
                )
                if result and result.get("phone"):
                    contact["owner_phone"] = result["phone"]
                    contact["phone_source"] = provider_name
                    break
            except Exception as e:
                logger.warning(f"Phone provider {provider_name} failed: {e}")
                continue

    # LinkedIn profile (useful for outreach)
    try:
        linkedin = await find_linkedin_profile(
            name=contact.get("owner_name"),
            company=lead["business_name"]
        )
        if linkedin:
            contact["linkedin_url"] = linkedin["url"]
    except Exception:
        pass

    return contact
```

### Cost per Provider (Approximate)

| Provider | Cost per Lookup | Success Rate | Best For |
|----------|----------------|--------------|----------|
| Apollo | $0.03-0.05 | 60-70% | General B2B |
| Hunter.io | $0.03 | 50-60% | Email by domain |
| Snov.io | $0.02-0.04 | 45-55% | Email sequences |
| Dropcontact | $0.05-0.10 | 55-65% | EU contacts |
| Lusha | $0.10-0.25 | 65-75% | Direct phone |

## Step 4: Email Verification

### Purpose
Validate email addresses before adding to CRM to maintain deliverability and avoid bounce penalties.

```python
async def verify_email(email: str) -> dict:
    """
    Verify email using ZeroBounce.
    Cost: ~$0.008-0.01 per verification.
    """
    result = await zerobounce.validate(email)

    return {
        "email": email,
        "status": result["status"],           # valid, invalid, catch-all, unknown
        "sub_status": result.get("sub_status"), # e.g., "mailbox_not_found"
        "is_deliverable": result["status"] == "valid",
        "is_catch_all": result["status"] == "catch-all",
        "is_disposable": result.get("disposable", False),
        "is_free_email": result.get("free_email", False),
        "mx_found": result.get("mx_found", False),
        "smtp_provider": result.get("smtp_provider"),
        "confidence_score": calculate_email_confidence(result)
    }

def calculate_email_confidence(verification_result):
    """Score email quality 0-100."""
    if verification_result["status"] == "valid":
        return 95
    elif verification_result["status"] == "catch-all":
        return 60  # might work, risky
    elif verification_result["status"] == "unknown":
        return 30  # unreliable
    else:
        return 0   # invalid
```

### Email Verification Decision Matrix

| Status | Confidence | Action |
|--------|------------|--------|
| Valid | 95 | Add to CRM, include in outreach |
| Catch-all | 60 | Add to CRM, note as catch-all, include cautiously |
| Unknown | 30 | Add to CRM, do not include in mass email, try manual verify |
| Invalid | 0 | Do not add, log failure, try next provider in waterfall |
| Disposable | 0 | Flag as suspicious, do not use |

## Step 5: Pain Scoring (15-Signal Analysis)

### Purpose
Score each lead on a 0-100 scale based on signals that indicate marketing pain and readiness to buy.

```python
async def calculate_pain_score(lead: dict, business_data: dict, contact_data: dict) -> dict:
    """
    Calculate pain score based on 15 signals.
    Returns: score (0-100) and breakdown.
    """
    signals = {}
    total_score = 0

    # --- Online Presence Signals (35 points max) ---

    # 1. No website or poor website (0-10)
    if not business_data.get("verified_website"):
        signals["no_website"] = 10
    elif business_data.get("website_platform") in ["wix", "squarespace-free"]:
        signals["basic_website"] = 5
    else:
        signals["has_website"] = 0

    # 2. Low Google rating (0-8)
    rating = business_data.get("google_rating", 0)
    if rating == 0:
        signals["no_google_rating"] = 8
    elif rating < 3.5:
        signals["low_rating"] = 6
    elif rating < 4.0:
        signals["avg_rating"] = 4
    elif rating < 4.5:
        signals["good_rating"] = 2
    else:
        signals["excellent_rating"] = 0

    # 3. Low review count (0-7)
    reviews = business_data.get("review_count", 0)
    if reviews < 5:
        signals["very_few_reviews"] = 7
    elif reviews < 20:
        signals["few_reviews"] = 5
    elif reviews < 50:
        signals["moderate_reviews"] = 3
    else:
        signals["many_reviews"] = 0

    # 4. No Google Analytics (0-5)
    if not business_data.get("has_analytics"):
        signals["no_analytics"] = 5
    else:
        signals["has_analytics"] = 0

    # 5. No paid ads running (0-5)
    if not business_data.get("has_paid_ads"):
        signals["no_ads"] = 5
    else:
        signals["has_ads"] = 0

    # --- SEO Signals (25 points max) ---

    # 6. Low organic traffic (0-8)
    traffic = business_data.get("organic_traffic", 0)
    if traffic < 50:
        signals["very_low_traffic"] = 8
    elif traffic < 200:
        signals["low_traffic"] = 6
    elif traffic < 1000:
        signals["moderate_traffic"] = 3
    else:
        signals["good_traffic"] = 0

    # 7. Low domain authority (0-7)
    da = business_data.get("domain_authority", 0)
    if da < 10:
        signals["very_low_da"] = 7
    elif da < 20:
        signals["low_da"] = 5
    elif da < 30:
        signals["moderate_da"] = 3
    else:
        signals["good_da"] = 0

    # 8. Few ranking keywords (0-5)
    keywords = business_data.get("total_keywords", 0)
    if keywords < 10:
        signals["very_few_keywords"] = 5
    elif keywords < 50:
        signals["few_keywords"] = 3
    else:
        signals["good_keywords"] = 0

    # 9. Outdated website platform (0-5)
    platform = business_data.get("website_platform", "")
    if platform in ["flash", "html-static", "frontpage"]:
        signals["outdated_platform"] = 5
    elif platform in ["wordpress"] and not business_data.get("has_ssl"):
        signals["insecure_wordpress"] = 3
    else:
        signals["ok_platform"] = 0

    # --- Social Signals (15 points max) ---

    # 10. No social media presence (0-5)
    social = business_data.get("social_profiles", {})
    if not social:
        signals["no_social"] = 5
    elif len(social) < 2:
        signals["minimal_social"] = 3
    else:
        signals["has_social"] = 0

    # 11. Inactive social media (0-5)
    # Check last post date if available
    signals["social_activity"] = 3  # default: assume moderate need

    # 12. No GMB optimization (0-5)
    if not business_data.get("google_place_id"):
        signals["no_gmb"] = 5
    else:
        signals["has_gmb"] = 0

    # --- Business Signals (25 points max) ---

    # 13. Business size (0-8)
    # Larger businesses = bigger contracts = higher value
    employee_count = business_data.get("employee_count", 0)
    if employee_count > 50:
        signals["large_business"] = 8
    elif employee_count > 20:
        signals["medium_business"] = 6
    elif employee_count > 5:
        signals["small_business"] = 4
    else:
        signals["micro_business"] = 2

    # 14. Competitive industry (0-7)
    industry = lead.get("industry", "")
    high_competition = ["plumbing", "hvac", "dental", "legal", "roofing", "real_estate"]
    medium_competition = ["landscaping", "electrical", "auto_repair", "veterinary"]
    if industry in high_competition:
        signals["high_competition"] = 7
    elif industry in medium_competition:
        signals["medium_competition"] = 5
    else:
        signals["low_competition"] = 3

    # 15. Lead source quality (0-10)
    source = lead.get("source", "")
    if source in ["referral", "inbound_call"]:
        signals["high_intent_source"] = 10
    elif source in ["website_form", "google_ad"]:
        signals["medium_intent_source"] = 7
    elif source in ["scraper", "cold_list"]:
        signals["low_intent_source"] = 3
    else:
        signals["unknown_source"] = 5

    # --- Calculate Total ---
    total_score = sum(signals.values())
    # Normalize to 0-100 (max theoretical = 100)
    normalized_score = min(total_score, 100)

    # Determine tier
    if normalized_score >= 75:
        tier = "hot"
    elif normalized_score >= 50:
        tier = "warm"
    elif normalized_score >= 25:
        tier = "cool"
    else:
        tier = "cold"

    return {
        "score": normalized_score,
        "tier": tier,
        "signals": signals,
        "top_pain_points": get_top_pain_points(signals, 3)
    }

def get_top_pain_points(signals, top_n):
    """Extract the top N highest-scoring pain signals."""
    sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
    return [{"signal": name, "score": score} for name, score in sorted_signals[:top_n]]
```

## Step 6: GHL Contact Creation

### Purpose
Create the fully enriched contact in GoHighLevel with all gathered data properly mapped.

### Field Mapping

```python
async def create_ghl_contact(lead: dict, business_data: dict,
                              contact_data: dict, pain_data: dict) -> str:
    """Create enriched contact in GHL. Returns contact ID."""

    contact_payload = {
        # Standard fields
        "firstName": contact_data.get("owner_name", "").split()[0] if contact_data.get("owner_name") else lead.get("first_name", ""),
        "lastName": " ".join(contact_data.get("owner_name", "").split()[1:]) if contact_data.get("owner_name") else lead.get("last_name", ""),
        "email": contact_data.get("owner_email") or lead.get("email"),
        "phone": contact_data.get("owner_phone") or lead.get("phone"),
        "companyName": lead.get("business_name"),
        "website": business_data.get("verified_website") or lead.get("website"),
        "address1": business_data.get("verified_address", lead.get("address", "")),
        "city": lead.get("city"),
        "state": lead.get("state"),
        "postalCode": lead.get("zip"),
        "source": lead.get("source", "enrichment_flow"),

        # Custom fields
        "customField": {
            # Pain scoring
            "pain_score": pain_data["score"],
            "pain_tier": pain_data["tier"],
            "top_pain_1": pain_data["top_pain_points"][0]["signal"] if pain_data["top_pain_points"] else "",
            "top_pain_2": pain_data["top_pain_points"][1]["signal"] if len(pain_data["top_pain_points"]) > 1 else "",
            "top_pain_3": pain_data["top_pain_points"][2]["signal"] if len(pain_data["top_pain_points"]) > 2 else "",

            # Business data
            "google_rating": business_data.get("google_rating"),
            "review_count": business_data.get("review_count"),
            "google_place_id": business_data.get("google_place_id"),
            "website_platform": business_data.get("website_platform"),
            "has_analytics": business_data.get("has_analytics", False),
            "has_paid_ads": business_data.get("has_paid_ads", False),
            "organic_traffic": business_data.get("organic_traffic"),
            "domain_authority": business_data.get("domain_authority"),

            # Contact data
            "owner_title": contact_data.get("owner_title"),
            "linkedin_url": contact_data.get("linkedin_url"),
            "email_verified": contact_data.get("email_verified", False),
            "email_confidence": contact_data.get("email_confidence", 0),

            # Enrichment metadata
            "enrichment_date": datetime.now().isoformat(),
            "enrichment_sources": ",".join(get_enrichment_sources(business_data, contact_data)),
            "enrichment_cost": calculate_enrichment_cost(business_data, contact_data)
        }
    }

    result = await ghl.create_contact(contact_payload)
    return result["contact"]["id"]
```

## Step 7: Pipeline Assignment

```python
async def assign_to_pipeline(contact_id: str, pain_data: dict, lead: dict):
    """Assign contact to appropriate pipeline and stage based on score and source."""

    # Determine pipeline
    if lead.get("source") in ["referral", "inbound_call", "website_form"]:
        pipeline_id = PIPELINES["inbound"]
    else:
        pipeline_id = PIPELINES["outbound"]

    # Determine initial stage
    if pain_data["tier"] == "hot":
        stage_id = STAGES["qualified"]        # skip "new lead", already qualified
    elif pain_data["tier"] == "warm":
        stage_id = STAGES["new_lead"]         # standard entry point
    else:
        stage_id = STAGES["nurture"]          # low priority, nurture first

    # Calculate deal value estimate
    estimated_value = estimate_deal_value(lead.get("industry"), pain_data["score"])

    await ghl.create_opportunity({
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "contactId": contact_id,
        "name": f"{lead['business_name']} - Marketing Services",
        "monetaryValue": estimated_value,
        "source": lead.get("source"),
        "status": "open"
    })
```

## Step 8: Tag Application

```python
async def apply_tags(contact_id: str, lead: dict, business_data: dict, pain_data: dict):
    """Apply comprehensive tags for segmentation and automation."""

    tags = []

    # Industry tag
    if lead.get("industry"):
        tags.append(f"industry:{lead['industry']}")

    # Source tag
    tags.append(f"source:{lead.get('source', 'unknown')}")

    # Score tier tag
    tags.append(f"score:{pain_data['tier']}")

    # Needs-based tags (from pain signals)
    needs_map = {
        "no_website": "needs:website",
        "basic_website": "needs:website_upgrade",
        "low_rating": "needs:reputation_management",
        "very_few_reviews": "needs:review_generation",
        "no_analytics": "needs:analytics_setup",
        "no_ads": "needs:paid_advertising",
        "very_low_traffic": "needs:seo",
        "low_traffic": "needs:seo",
        "no_social": "needs:social_media",
        "no_gmb": "needs:gmb_optimization",
    }

    for signal in pain_data.get("signals", {}):
        if signal in needs_map and pain_data["signals"][signal] > 0:
            tags.append(needs_map[signal])

    # Enrichment status tag
    tags.append("enriched")
    if business_data.get("email_verified"):
        tags.append("email_verified")

    await ghl.add_tags(contact_id, tags)
```

## Step 9: Task Creation

```python
async def create_follow_up_tasks(contact_id: str, pain_data: dict, lead: dict):
    """Create follow-up tasks based on lead priority."""

    tasks = []

    if pain_data["tier"] == "hot":
        tasks.append({
            "title": f"URGENT: Call {lead['business_name']} - Hot Lead (Score: {pain_data['score']})",
            "dueDate": (datetime.now() + timedelta(hours=2)).isoformat(),
            "description": f"High-value lead. Top pain points: {', '.join([p['signal'] for p in pain_data['top_pain_points']])}",
            "assignedTo": get_agent_for_industry(lead.get("industry"))
        })
    elif pain_data["tier"] == "warm":
        tasks.append({
            "title": f"Follow up with {lead['business_name']} - Warm Lead",
            "dueDate": (datetime.now() + timedelta(days=1)).isoformat(),
            "description": f"Score: {pain_data['score']}. Review profile and send personalized outreach.",
            "assignedTo": get_agent_for_industry(lead.get("industry"))
        })
    else:
        tasks.append({
            "title": f"Review {lead['business_name']} for nurture sequence",
            "dueDate": (datetime.now() + timedelta(days=3)).isoformat(),
            "description": f"Low priority (Score: {pain_data['score']}). Add to email nurture if appropriate.",
            "assignedTo": "nurture_team"
        })

    for task in tasks:
        await ghl.create_task(contact_id, task)
```

## Step 10: Team Notification

```python
async def notify_team(contact_id: str, lead: dict, pain_data: dict, business_data: dict):
    """Send notifications for high-value leads."""

    if pain_data["tier"] == "hot":
        # Immediate Slack notification
        message = f"""
*New Hot Lead!* (Score: {pain_data['score']}/100)

*Business:* {lead['business_name']}
*Industry:* {lead.get('industry', 'Unknown')}
*Source:* {lead.get('source', 'Unknown')}
*Rating:* {business_data.get('google_rating', 'N/A')} ({business_data.get('review_count', 0)} reviews)

*Top Pain Points:*
{chr(10).join(['- ' + p['signal'].replace('_', ' ').title() for p in pain_data['top_pain_points']])}

*Action:* Call within 2 hours
*GHL Link:* https://app.gohighlevel.com/contacts/{contact_id}
        """
        await slack.send_message(channel="#hot-leads", message=message)

        # Also send Telegram notification to the assigned agent
        agent = get_agent_for_industry(lead.get("industry"))
        await telegram.send_message(
            chat_id=agent["telegram_id"],
            message=f"Hot lead: {lead['business_name']} (Score: {pain_data['score']}). Check Slack for details."
        )

    elif pain_data["tier"] == "warm":
        # Daily digest (batch warm leads together)
        await add_to_daily_digest(contact_id, lead, pain_data)
```

## Step 11: Manual Review Triggers

Certain conditions should pause the automated flow and flag for human review:

| Condition | Why | Action |
|-----------|-----|--------|
| Business name fuzzy match 70-85% | Possible duplicate, not certain | Queue for manual dedup check |
| Catch-all email detected | May not reach the right person | Flag for manual email research |
| Pain score exactly 50 | Borderline qualification | Human reviews before pipeline assignment |
| Missing critical fields after enrichment | Incomplete profile | Queue for manual enrichment |
| Conflicting data between sources | Address mismatch, name mismatch | Human resolves conflicts |
| Competitor business detected | Do not add competitor to pipeline | Flag for exclusion review |
| Known spam domain/phone | Potential junk lead | Auto-reject but log for review |

## Cost Per Lead Through Full Flow

### Cost Breakdown

| Step | Service | Cost per Lead | Notes |
|------|---------|---------------|-------|
| Validation | Internal | $0.00 | GHL API calls only |
| Google Places | Google API | $0.003 | Place Details request |
| BuiltWith | BuiltWith API | $0.02 | Depends on plan |
| DataForSEO | DataForSEO | $0.03 | Domain overview |
| Clay Waterfall | Multi-provider | $0.05-0.15 | Average across providers |
| Email Verification | ZeroBounce | $0.008 | Per verification |
| GHL API | GHL | $0.00 | Included in subscription |
| **Total** | | **$0.11-0.21** | **Per enriched lead** |

### At Scale

| Volume | Cost Range | Monthly Budget |
|--------|-----------|----------------|
| 100 leads/month | $11-21 | ~$20 |
| 500 leads/month | $55-105 | ~$100 |
| 1,000 leads/month | $110-210 | ~$200 |
| 5,000 leads/month | $550-1,050 | ~$800 (volume discounts) |

## Timing Targets

| Step | Target Time | Notes |
|------|-------------|-------|
| Validation + Dedup | <5 seconds | GHL search API |
| Business Enrichment | <30 seconds | Parallel API calls |
| Contact Enrichment | <60 seconds | Waterfall (sequential) |
| Email Verification | <10 seconds | Single API call |
| Pain Scoring | <2 seconds | Local computation |
| GHL Contact Creation | <5 seconds | Single API call |
| Pipeline + Tags + Tasks | <10 seconds | Multiple API calls |
| Notifications | <5 seconds | Async, non-blocking |
| **Total** | **<2 minutes** | **Most cases; up to 5 min if waterfall is slow** |

## Monitoring and Observability

Track these metrics to ensure flow health:

- **Enrichment rate:** percentage of leads successfully enriched at each step
- **Email find rate:** percentage of leads where a valid email is found
- **Average pain score:** trending average across all leads (quality indicator)
- **Cost per lead:** actual cost trending over time
- **Flow completion rate:** percentage that make it through all 11 steps
- **Error rate by step:** identify which step fails most often
- **Time per step:** identify bottlenecks
- **Duplicate rate:** percentage of leads that are duplicates (source quality indicator)

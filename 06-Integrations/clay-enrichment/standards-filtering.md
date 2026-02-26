# Lead Qualification Standards and Filtering

> The 15-signal pain scoring model and qualification framework for filtering leads before and after enrichment.

---

## Pain Scoring Model Overview

Every lead receives a score from 0-100 based on 15 signals that indicate how much the business needs digital marketing help. Higher scores mean more pain (more likely to buy).

**Scoring philosophy:** We are not scoring how "good" the business is. We are scoring how much they NEED our services. A thriving business with great marketing scores LOW (they do not need us). A struggling business with no online presence scores HIGH (they desperately need us).

---

## The 15 Pain Signals

### Category 1: Website Quality (Max 25 points)

| Signal | Points | Detection Method | Criteria |
|---|---|---|---|
| **1. No website** | 10 | Google Places data | No website URL in listing |
| **2. Not mobile-friendly** | 5 | Google PageSpeed API / BuiltWith | Mobile score < 50 or no responsive design |
| **3. Slow page speed** | 5 | Google PageSpeed API | Performance score < 50 |
| **4. No SSL (HTTP)** | 3 | URL check | Website loads on HTTP, not HTTPS |
| **5. Outdated design** | 2 | BuiltWith CMS version / manual flag | WordPress < 5.0, or template from pre-2018 |

**Scoring logic:**
```python
def score_website(enrichment: dict) -> tuple[int, list[str]]:
    """Score website quality signals. Returns (points, pain_signals)."""
    points = 0
    signals = []

    if not enrichment.get("website"):
        points += 10
        signals.append("no-website")
        return points, signals  # No website means other checks are N/A

    if enrichment.get("mobile_score", 100) < 50:
        points += 5
        signals.append("not-mobile-friendly")

    if enrichment.get("page_speed_score", 100) < 50:
        points += 5
        signals.append("slow-website")

    if not enrichment.get("has_ssl", True):
        points += 3
        signals.append("no-ssl")

    if enrichment.get("cms_version_outdated", False):
        points += 2
        signals.append("outdated-design")

    return points, signals
```

### Category 2: Online Presence (Max 25 points)

| Signal | Points | Detection Method | Criteria |
|---|---|---|---|
| **6. GMB not claimed/optimized** | 5 | Google Places data | Missing hours, photos, or description |
| **7. Few/no reviews** | 8 | Google Places data | Fewer than 20 Google reviews |
| **8. Low review rating** | 5 | Google Places data | Average rating below 4.0 |
| **9. No social media presence** | 7 | Clay social enrichment | No Facebook, Instagram, or LinkedIn found |

**Scoring logic:**
```python
def score_online_presence(enrichment: dict) -> tuple[int, list[str]]:
    """Score online presence signals."""
    points = 0
    signals = []

    # GMB optimization check
    gmb_fields = ["business_hours", "business_description", "photos_count"]
    missing_gmb = sum(1 for f in gmb_fields if not enrichment.get(f))
    if missing_gmb >= 2:
        points += 5
        signals.append("gmb-not-optimized")

    # Review signals
    review_count = enrichment.get("review_count", 0)
    if review_count < 20:
        points += 8
        signals.append("few-reviews")

    google_rating = enrichment.get("google_rating", 5.0)
    if google_rating < 4.0:
        points += 5
        signals.append("low-rating")

    # Social media presence
    social_fields = ["facebook_url", "instagram_handle", "linkedin_url"]
    found_social = sum(1 for f in social_fields if enrichment.get(f))
    if found_social == 0:
        points += 7
        signals.append("no-social-presence")

    return points, signals
```

### Category 3: Advertising Activity (Max 15 points)

| Signal | Points | Detection Method | Criteria |
|---|---|---|---|
| **10. No ad pixels detected** | 8 | BuiltWith tech detection | No Facebook Pixel, Google Ads tag, etc. |
| **11. Not running Google Ads** | 7 | SEMrush/DataForSEO or ad pixel check | No active paid search campaigns detected |

**Scoring logic:**
```python
def score_advertising(enrichment: dict) -> tuple[int, list[str]]:
    """Score advertising activity signals."""
    points = 0
    signals = []

    tech_stack = enrichment.get("technologies", [])
    ad_techs = ["Facebook Pixel", "Google Ads", "Google Tag Manager", "Bing Ads", "LinkedIn Insight"]
    has_ad_tech = any(t in tech_stack for t in ad_techs)

    if not has_ad_tech:
        points += 8
        signals.append("no-ad-pixels")

    if not enrichment.get("running_google_ads", False):
        points += 7
        signals.append("no-google-ads")

    return points, signals
```

### Category 4: Technology Stack (Max 20 points)

| Signal | Points | Detection Method | Criteria |
|---|---|---|---|
| **12. Outdated CMS** | 7 | BuiltWith | Old WordPress, Wix, GoDaddy builder, etc. |
| **13. No analytics** | 8 | BuiltWith tech detection | No Google Analytics or similar |
| **14. No chat/booking tool** | 5 | BuiltWith tech detection | No live chat, chatbot, or online booking |

**Scoring logic:**
```python
def score_technology(enrichment: dict) -> tuple[int, list[str]]:
    """Score technology stack signals."""
    points = 0
    signals = []

    tech_stack = enrichment.get("technologies", [])

    # CMS check
    outdated_cms = ["Wix", "Weebly", "GoDaddy Website Builder", "Squarespace"]
    old_wordpress = enrichment.get("wordpress_version", "999") < "6.0"
    if any(cms in tech_stack for cms in outdated_cms) or old_wordpress:
        points += 7
        signals.append("outdated-cms")

    # Analytics check
    analytics_tools = ["Google Analytics", "GA4", "Mixpanel", "Hotjar", "Matomo"]
    has_analytics = any(t in tech_stack for t in analytics_tools)
    if not has_analytics:
        points += 8
        signals.append("no-analytics")

    # Chat/booking check
    chat_tools = ["Intercom", "Drift", "LiveChat", "Tidio", "Calendly", "Acuity"]
    has_chat = any(t in tech_stack for t in chat_tools)
    if not has_chat:
        points += 5
        signals.append("no-chat-booking")

    return points, signals
```

### Category 5: Business Characteristics (Max 15 points)

| Signal | Points | Detection Method | Criteria |
|---|---|---|---|
| **15. Sweet spot business size** | 0-15 | Clay company enrichment | Ideal: 5-50 employees, $500K-$10M revenue |

**Scoring logic:**
```python
def score_business_characteristics(enrichment: dict) -> tuple[int, list[str]]:
    """Score business size and characteristics."""
    points = 0
    signals = []

    employees = enrichment.get("employee_count", 0)
    revenue = enrichment.get("annual_revenue", 0)

    # Sweet spot: businesses big enough to afford services, small enough to need help
    if 5 <= employees <= 50:
        points += 8  # Ideal size
        signals.append("ideal-size")
    elif 1 <= employees <= 4:
        points += 4  # Small but possible
        signals.append("small-business")
    elif employees > 50:
        points += 2  # Larger, may have in-house marketing
        signals.append("mid-size-business")
    # employees == 0 means unknown, no points

    # Revenue sweet spot
    if 500000 <= revenue <= 10000000:
        points += 7  # Can afford services
        signals.append("good-revenue-range")
    elif 100000 <= revenue < 500000:
        points += 3  # Tight budget but possible
    elif revenue > 10000000:
        points += 2  # May have in-house team

    return points, signals
```

---

## Complete Scoring Function

```python
def calculate_lead_score(enrichment: dict) -> dict:
    """Calculate complete lead score from all 15 signals."""
    total_points = 0
    all_signals = []

    # Run all category scorers
    categories = [
        ("website", score_website),
        ("online_presence", score_online_presence),
        ("advertising", score_advertising),
        ("technology", score_technology),
        ("business", score_business_characteristics),
    ]

    category_scores = {}
    for category_name, scorer in categories:
        points, signals = scorer(enrichment)
        total_points += points
        all_signals.extend(signals)
        category_scores[category_name] = points

    # Cap at 100
    total_points = min(total_points, 100)

    # Determine tier
    if total_points >= 80:
        tier = "hot"
    elif total_points >= 60:
        tier = "warm"
    elif total_points >= 40:
        tier = "cold"
    else:
        tier = "disqualified"

    return {
        "score": total_points,
        "tier": tier,
        "signals": all_signals,
        "category_scores": category_scores,
        "signal_count": len(all_signals),
    }
```

---

## Filter Stages

### Pre-Enrichment Filters (Save Credits)

Applied BEFORE spending Clay credits. Uses only free/cheap data (Google Places):

| Filter | Criteria | Action |
|---|---|---|
| Wrong industry | Category does not match target vertical | SKIP, do not enrich |
| No contact info | No phone AND no website | SKIP, cannot reach |
| Permanently closed | Google Places status = closed | SKIP |
| Chain/franchise | Part of a national chain (detected by name pattern) | SKIP (decision made at corporate) |
| Already in CRM | Email or phone matches existing GHL contact | SKIP enrichment, update if stale |
| Recently enriched | Same business enriched within last 90 days | SKIP, use cached data |
| Geographic mismatch | Outside target service area | SKIP |

**Pre-filter savings:** Typically eliminates 30-50% of leads before any credits are spent.

### Post-Enrichment Filters (Quality Gates)

Applied AFTER enrichment, based on full data:

| Filter | Criteria | Action |
|---|---|---|
| Score too low | Total score < 40 | Tag as disqualified, do not pursue |
| Invalid email | ZeroBounce says email is invalid | Flag, attempt alternate contact |
| Already has agency | LinkedIn shows marketing agency relationship | Lower priority |
| Bankruptcy/closure signals | Financial distress indicators | SKIP |
| Competitor client | Currently uses a competitor's services | Tag differently, competitive displacement pitch |

---

## Disqualification Criteria

Hard disqualification (never pursue):
- Wrong industry (plumber when targeting dentists)
- Business is permanently closed
- National chain or franchise (no local decision-maker)
- Government or non-profit entity (different sales cycle)
- Already a client

Soft disqualification (low priority, may revisit):
- Score below 40 (not enough pain signals)
- No email and no direct phone (only business phone)
- Already has a marketing agency (harder but not impossible sell)
- Very small business (1-2 employees, revenue under $100K)

---

## Qualification Tiers

| Tier | Score Range | % of Leads | Action | Response Time |
|---|---|---|---|---|
| **Hot** | 80-100 | ~10-15% | Immediate personal outreach | Within 1 hour |
| **Warm** | 60-79 | ~20-25% | Personalized email sequence + follow-up call | Within 24 hours |
| **Cold** | 40-59 | ~25-30% | Automated nurture drip campaign | Within 48 hours |
| **Disqualified** | 0-39 | ~30-45% | Do not pursue, archive for potential future review | N/A |

---

## Routing Rules

### Hot Leads (80-100)
```python
async def route_hot_lead(ghl_adapter, contact_id: str, score_data: dict):
    """Route a hot lead for immediate action."""
    # 1. Add to pipeline as high priority
    await ghl_adapter.create_opportunity({
        "contactId": contact_id,
        "pipelineStageId": get_stage_id("New Lead"),
        "monetaryValue": estimate_deal_value(score_data),
        "status": "open",
    })
    # 2. Tag appropriately
    await ghl_adapter.add_tags(contact_id, ["score:hot", "action:call-now"])
    # 3. Create urgent task for sales rep
    await ghl_adapter.create_task({
        "contactId": contact_id,
        "title": f"HOT LEAD - Call within 1 hour (Score: {score_data['score']})",
        "dueDate": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "priority": "high",
    })
    # 4. Send alert (SMS/Slack/email to sales rep)
    await send_hot_lead_alert(contact_id, score_data)
```

### Warm Leads (60-79)
```python
async def route_warm_lead(ghl_adapter, contact_id: str, score_data: dict):
    """Route a warm lead to personalized nurture."""
    await ghl_adapter.create_opportunity({
        "contactId": contact_id,
        "pipelineStageId": get_stage_id("New Lead"),
        "monetaryValue": estimate_deal_value(score_data),
    })
    await ghl_adapter.add_tags(contact_id, ["score:warm", "sequence:warm-nurture"])
    # Start personalized email sequence based on pain signals
    pain_signals = score_data["signals"]
    sequence_id = select_nurture_sequence(pain_signals)
    await ghl_adapter.start_workflow(contact_id, sequence_id)
```

### Cold Leads (40-59)
```python
async def route_cold_lead(ghl_adapter, contact_id: str, score_data: dict):
    """Route a cold lead to long-term nurture."""
    await ghl_adapter.create_opportunity({
        "contactId": contact_id,
        "pipelineStageId": get_stage_id("New Lead"),
        "monetaryValue": estimate_deal_value(score_data) * 0.5,  # Lower expected value
    })
    await ghl_adapter.add_tags(contact_id, ["score:cold", "sequence:cold-drip"])
    # Start generic drip campaign
    await ghl_adapter.start_workflow(contact_id, COLD_DRIP_WORKFLOW_ID)
```

---

## RESEARCH GAPS

- [ ] Validate the 15 signals against actual conversion data (which signals best predict closing?)
- [ ] Determine optimal score thresholds (80/60/40) through A/B testing
- [ ] Build a feedback loop: when deals close or are lost, update the scoring model weights
- [ ] Test pre-enrichment filter accuracy (are we incorrectly disqualifying good leads?)
- [ ] Determine if industry-specific scoring weights are needed (dental vs HVAC vs legal)

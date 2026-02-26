# Lead Scoring System

## Overview

The lead scoring system determines which businesses are ideal prospects for your marketing agency. It extends the Rise Local 15-signal pain scoring framework into a comprehensive, data-driven scoring model. The core insight is counterintuitive: **higher scores indicate MORE marketing sophistication**, meaning the business is LESS likely to need your services. Your ideal clients are in the "awareness gap" -- they have a real business but weak digital presence.

---

## Scoring Philosophy

Traditional lead scoring in SaaS rates leads higher when they show buying intent (visited pricing page, downloaded whitepaper). Agency lead scoring is different: you are identifying businesses that **don't know they have a problem**. A plumber with no website and 3 Google reviews isn't searching for a marketing agency -- but they desperately need one.

**Key principle:** You are scoring the business's marketing maturity, NOT their intent to buy your services. Low-to-mid scores are your targets. High scores mean they already have it figured out (or have an agency).

---

## Signal Categories and Scoring

### Category 1: Digital Presence (0-25 points)

These signals measure the quality and completeness of the business's online presence.

| Signal | Points | How to Detect | Data Source |
|--------|--------|---------------|-------------|
| Website exists and loads successfully | 5 | HTTP request returns 200, page renders content | Playwright scrape |
| Website is mobile-friendly (responsive design) | 5 | Viewport meta tag, responsive CSS, Google Mobile-Friendly test | Playwright + Lighthouse |
| SSL/HTTPS enabled | 3 | URL scheme is https://, valid certificate | HTTP request |
| Page speed score >50 (Google PageSpeed) | 3 | Lighthouse performance score | Lighthouse API or DataForSEO |
| Has blog or content section | 3 | Detect /blog, /news, /articles pages or blog-like content | Playwright scrape |
| Modern, professional design (not default template) | 3 | AI visual analysis of screenshot, or check for customized CSS | Playwright screenshot + AI |
| Has chat widget or live chat | 3 | Detect Intercom, Drift, Tawk.to, LiveChat, or similar | BuiltWith or custom detection |

**Detection implementation details:**

**Website exists (5 points):**
```python
try:
    response = requests.get(website_url, timeout=10, allow_redirects=True)
    if response.status_code == 200 and len(response.text) > 500:
        score += 5  # Real website with content
    elif response.status_code == 200:
        score += 2  # Exists but minimal content (parked/placeholder)
except:
    score += 0  # No website or unreachable
```

**Mobile-friendly (5 points):**
- Check for `<meta name="viewport"` tag
- Check for responsive CSS media queries
- Or use Google's Mobile-Friendly Test API
- Modern site builders (Wix, Squarespace, WordPress themes) are almost always mobile-friendly
- Hand-coded sites from pre-2015 often are not

**Modern design (3 points):**
- This is the most subjective signal
- Automated approach: take screenshot, check for common outdated patterns
  - Flash content (dead giveaway)
  - Fixed-width layout (<960px centered)
  - Tiny fonts, crowded layout
  - GIF animations, hit counters, "Under Construction" banners
  - Copyright year >3 years old in footer
- AI approach: send screenshot to Claude Vision API with prompt "Rate this website's design modernity on a scale of 1-10. Consider layout, typography, color scheme, and overall professionalism."
- Score 3 if AI rates >= 6/10

---

### Category 2: Online Marketing (0-25 points)

These signals measure active marketing efforts.

| Signal | Points | How to Detect | Data Source |
|--------|--------|---------------|-------------|
| Google Analytics installed (GA4 or UA) | 5 | Detect gtag.js, analytics.js, or GA4 measurement ID | BuiltWith or page source |
| Running Google Ads (active campaigns) | 5 | Google Ads conversion tag on site, or detected via Serper ad results | BuiltWith + Serper |
| Running Facebook/Meta Ads | 5 | Facebook Pixel detected on site, or check Meta Ad Library | BuiltWith + Meta Ad Library API |
| Has email capture / newsletter signup | 5 | Detect Mailchimp, Constant Contact, ConvertKit, or email input forms | Page source analysis |
| Active social media presence | 5 | Social profiles linked from site, with recent posts (within 30 days) | Website scrape + social API |

**Detection implementation details:**

**Google Analytics (5 points):**
```javascript
// Check page source for GA tags
const hasGA4 = html.includes('gtag') && html.includes('G-');
const hasUA = html.includes('analytics.js') || html.includes('UA-');
const hasGTM = html.includes('googletagmanager.com');
score += (hasGA4 || hasUA || hasGTM) ? 5 : 0;
```

**Google Ads (5 points):**
- Method 1: Check for Google Ads conversion tag on website
- Method 2: Search for the business on Google and check if they appear in paid results
  ```
  serper_search(query="plumber in [their city]")
  check if business domain appears in paid_results
  ```
- Method 3: Check for `googleads.g.doubleclick.net` in network requests

**Facebook Ads (5 points):**
- Method 1: Check for Facebook Pixel on website (`fbq('init'`)
- Method 2: Check Meta Ad Library for active ads from that business
  - Meta Ad Library is publicly searchable: `https://www.facebook.com/ads/library/`
  - Search by business name or page name

**Email capture (5 points):**
- Look for email input fields with subscribe/newsletter context
- Detect known providers: Mailchimp embed forms, ConvertKit forms, etc.
- Check for popup/modal with email capture (common pattern)
- Look for text patterns: "Subscribe", "Newsletter", "Get updates", "Join our list"

**Active social media (5 points):**
- Find social links on website
- For each linked profile, check last post date
- Active = at least one platform with post in last 30 days
- Partially active = posts in last 90 days (3 points)
- Inactive = no posts in 90+ days (0 points)

---

### Category 3: Reputation (0-25 points)

These signals measure the business's public reputation and review presence.

| Signal | Points | How to Detect | Data Source |
|--------|--------|---------------|-------------|
| Google review count > 20 | 5 | Google Places API review count | Google Places |
| Google rating > 4.0 stars | 5 | Google Places API rating | Google Places |
| BBB accredited or A+ rating | 5 | BBB website lookup | Serper search or BBB API |
| Responds to Google reviews | 5 | Check review responses in Google Places data | Google Places API (review replies) |
| Listed on Yelp, Angi, HomeAdvisor, or similar directories | 5 | Search for business on these platforms | Serper search |

**Detection implementation details:**

**Google reviews (5 points):**
```python
if lead.google_reviews > 20:
    score += 5
elif lead.google_reviews > 10:
    score += 3
elif lead.google_reviews > 5:
    score += 1
```

**Google rating (5 points):**
```python
if lead.google_rating >= 4.5:
    score += 5
elif lead.google_rating >= 4.0:
    score += 4
elif lead.google_rating >= 3.5:
    score += 2
# Below 3.5: 0 points (reputation problem, different kind of lead)
```

**BBB rating (5 points):**
- Search Serper: `"[business name]" site:bbb.org`
- If found, check rating (A+, A, B, etc.)
- A+ or A = 5 points, B = 3 points, C or below = 1 point
- Not listed = 0 points (not negative, just not present)

**Review responses (5 points):**
- Google Places API returns owner_response for each review
- If >50% of reviews have owner responses: 5 points
- If 25-50%: 3 points
- If <25%: 1 point
- If 0%: 0 points
- This signal indicates active reputation management

**Directory listings (5 points):**
- Search for business on major directories
- Yelp, Angi, HomeAdvisor, Thumbtack, Houzz (industry-dependent)
- Listed on 3+: 5 points
- Listed on 1-2: 3 points
- Not listed: 0 points

---

### Category 4: Business Signals (0-25 points)

These signals assess the business's size, stability, and sophistication.

| Signal | Points | How to Detect | Data Source |
|--------|--------|---------------|-------------|
| Revenue estimate > $500K/year | 5 | Company databases, employee count proxy | Clay/Clearbit, or estimate from employees |
| 5+ employees | 5 | LinkedIn company page, team page on website, or data providers | Clay, LinkedIn, website scrape |
| 3+ years in business | 5 | Google Places "years in business", website copyright date, state records | Google Places, website scrape |
| Licensed/insured verified | 5 | State licensing database, website claims | State API or website scrape |
| Multiple locations or large service area | 5 | Google Places for multiple listings, or website mentions multiple areas | Google Places, website scrape |

**Detection implementation details:**

**Revenue estimate (5 points):**
- Direct revenue data is hard to get for private small businesses
- Proxy methods:
  - Employee count x average revenue per employee for industry
  - Home services: $100K-200K revenue per employee is typical
  - 5 employees ~ $500K-1M revenue
- Clay or Clearbit may have revenue estimates for some businesses

**Employee count (5 points):**
- LinkedIn company page employee count
- Team/about page on website (count names/photos)
- Job listings on Indeed/Glassdoor (indicates hiring = growth)
- Google Places sometimes includes this

**Years in business (5 points):**
- Google Places "opened" date
- Website footer copyright year (e.g., "(c) 2018" = at least 8 years)
- State business registration databases
- BBB profile often includes establishment date

**Licensed/insured (5 points):**
- Many states have online license verification databases
- Website may claim "Licensed and Insured" (common in home services)
- Check for specific license numbers displayed on website
- This is more about business legitimacy than marketing sophistication

**Multiple locations (5 points):**
- Multiple Google Places listings for same business name
- Website mentions multiple offices or "Serving [list of cities]"
- Multiple phone numbers for different locations

---

## Composite Score Interpretation

| Score Range | Label | Interpretation | Action |
|------------|-------|---------------|--------|
| 0-14 | Too Small | Very small or new business, likely can't afford services | Disqualify |
| 15-29 | Struggling | Business exists but minimal everything -- highest need, may lack budget | Nurture list |
| 30-45 | **Sweet Spot (Low)** | Real business with significant gaps -- ideal prospects | **Priority outreach** |
| 46-60 | **Sweet Spot (High)** | Established business with specific gaps -- ideal prospects | **Priority outreach** |
| 61-75 | Moderate | Decent marketing, but room for improvement | Secondary outreach |
| 76-89 | Sophisticated | Strong marketing presence, likely has an agency | Low priority |
| 90-100 | Well-Marketed | Excellent marketing across all channels | Disqualify (or pitch premium) |

**The ideal client profile in detail (score 30-60):**
- Has a real business with employees and revenue
- Has a website, but it's outdated, slow, or not mobile-friendly
- Has some Google reviews but not actively managed
- Does NOT have Google Analytics or conversion tracking
- Does NOT run paid advertising
- Has no blog or content marketing
- Social media profiles exist but are inactive or inconsistent
- Is not listed on major directories beyond Google

This is the business owner who knows they "should do something about marketing" but hasn't prioritized it.

---

## Scoring Logic Implementation

```python
def calculate_lead_score(lead_data):
    score = 0
    signals = {}

    # Category 1: Digital Presence (0-25)
    dp_score = 0

    if lead_data.get('website_exists'):
        dp_score += 5
        signals['website_exists'] = True

    if lead_data.get('mobile_friendly'):
        dp_score += 5
        signals['mobile_friendly'] = True

    if lead_data.get('has_ssl'):
        dp_score += 3
        signals['has_ssl'] = True

    if lead_data.get('page_speed_score', 0) > 50:
        dp_score += 3
        signals['good_page_speed'] = True

    if lead_data.get('has_blog'):
        dp_score += 3
        signals['has_blog'] = True

    if lead_data.get('modern_design'):
        dp_score += 3
        signals['modern_design'] = True

    if lead_data.get('has_chat'):
        dp_score += 3
        signals['has_chat'] = True

    # Category 2: Online Marketing (0-25)
    om_score = 0

    if lead_data.get('has_google_analytics'):
        om_score += 5
        signals['has_analytics'] = True

    if lead_data.get('running_google_ads'):
        om_score += 5
        signals['running_google_ads'] = True

    if lead_data.get('running_facebook_ads'):
        om_score += 5
        signals['running_facebook_ads'] = True

    if lead_data.get('has_email_capture'):
        om_score += 5
        signals['has_email_capture'] = True

    if lead_data.get('social_media_active'):
        om_score += 5
        signals['social_active'] = True

    # Category 3: Reputation (0-25)
    rep_score = 0

    reviews = lead_data.get('google_review_count', 0)
    if reviews > 20:
        rep_score += 5
    elif reviews > 10:
        rep_score += 3
    elif reviews > 5:
        rep_score += 1
    signals['google_reviews'] = reviews

    rating = lead_data.get('google_rating', 0)
    if rating >= 4.5:
        rep_score += 5
    elif rating >= 4.0:
        rep_score += 4
    elif rating >= 3.5:
        rep_score += 2
    signals['google_rating'] = rating

    if lead_data.get('bbb_accredited'):
        rep_score += 5
        signals['bbb_accredited'] = True

    if lead_data.get('responds_to_reviews'):
        rep_score += 5
        signals['responds_to_reviews'] = True

    directory_count = lead_data.get('directory_listing_count', 0)
    if directory_count >= 3:
        rep_score += 5
    elif directory_count >= 1:
        rep_score += 3
    signals['directory_listings'] = directory_count

    # Category 4: Business Signals (0-25)
    biz_score = 0

    if lead_data.get('estimated_revenue', 0) > 500000:
        biz_score += 5
        signals['revenue_over_500k'] = True

    if lead_data.get('employee_count', 0) >= 5:
        biz_score += 5
        signals['5plus_employees'] = True

    if lead_data.get('years_in_business', 0) >= 3:
        biz_score += 5
        signals['3plus_years'] = True

    if lead_data.get('licensed_insured'):
        biz_score += 5
        signals['licensed_insured'] = True

    if lead_data.get('multiple_locations'):
        biz_score += 5
        signals['multiple_locations'] = True

    # Composite
    score = dp_score + om_score + rep_score + biz_score

    return {
        'total_score': score,
        'category_scores': {
            'digital_presence': dp_score,
            'online_marketing': om_score,
            'reputation': rep_score,
            'business_signals': biz_score,
        },
        'signals': signals,
        'qualification': classify_lead(score),
    }

def classify_lead(score):
    if score < 15:
        return 'disqualified_too_small'
    elif score < 30:
        return 'nurture'
    elif score <= 60:
        return 'priority_target'
    elif score <= 75:
        return 'secondary_target'
    elif score < 90:
        return 'low_priority'
    else:
        return 'disqualified_too_sophisticated'
```

---

## Pain Points by Missing Signal

The scoring system also generates specific **pain point narratives** based on which signals are missing. These power personalized outreach:

| Missing Signal | Pain Point Narrative |
|---------------|---------------------|
| No website | "Potential customers searching for [service] in [city] can't find you online" |
| Not mobile-friendly | "Over 60% of local searches happen on phones -- your site doesn't work on mobile" |
| No SSL | "Google marks your site as 'Not Secure' -- this scares away potential customers" |
| No analytics | "You have no idea how many people visit your site or where they come from" |
| No Google Ads | "Your competitors are paying to appear above you in search results" |
| No chat | "Visitors to your site have no way to quickly ask a question -- they leave" |
| Few reviews | "Customers choose businesses with more reviews -- your competitors have 3x more" |
| Low rating | "Your [3.2] star rating is costing you customers who filter for 4+ stars" |
| No review responses | "Unanswered reviews signal to customers that you don't care about feedback" |
| No blog | "You're missing out on ranking for dozens of long-tail keywords in your area" |

---

## Score Decay and Re-scoring

Businesses change over time. A lead scored 6 months ago may have improved (hired an agency) or degraded (website went down).

**Re-scoring schedule:**
- Priority targets (30-60): re-score every 60 days
- Nurture list (15-29): re-score every 90 days
- Secondary targets (61-75): re-score every 120 days
- Disqualified: re-score every 180 days (businesses can grow/shrink)

**Score change alerts:**
- If a priority target's score increases by >15 points, they may have hired an agency -- move to low priority
- If a previously disqualified-too-small business's score increases to 30+, they've grown -- add to outreach
- If a low-priority lead's score drops by >15 points (website went down, reviews tanked), they may now need help

**Implementation:**
```python
# Re-scoring job runs on schedule
for lead in leads_due_for_rescore():
    old_score = lead.score
    new_data = run_enrichment_waterfall(lead, use_cache=False)
    new_score = calculate_lead_score(new_data)

    if abs(new_score.total_score - old_score) > 15:
        alert_score_change(lead, old_score, new_score)

    lead.score = new_score.total_score
    lead.score_details = new_score
    lead.last_scored = datetime.now()
    lead.save()
```

---

## Scoring Calibration

The scoring thresholds (30-60 sweet spot) are starting points. Calibrate based on actual conversion data:

1. Track which scored leads become clients
2. After 50+ conversions, analyze the score distribution of converted leads
3. Adjust thresholds: if most clients came from 25-50 range, shift the sweet spot down
4. Review individual signal weights: if "has blog" rarely correlates with conversion, reduce its weight

**Calibration query:**
```sql
SELECT
  score_at_outreach,
  COUNT(*) as total_leads,
  SUM(CASE WHEN became_client THEN 1 ELSE 0 END) as conversions,
  ROUND(SUM(CASE WHEN became_client THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as conversion_rate
FROM leads
WHERE outreach_date IS NOT NULL
GROUP BY score_at_outreach / 10 * 10  -- Group by 10-point ranges
ORDER BY score_at_outreach;
```

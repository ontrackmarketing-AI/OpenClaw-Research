# Meta Ads Retargeting: Marketing API, Custom Audiences & Conversions API

## Overview

Meta Ads (Facebook & Instagram) retargeting enables SW Recovery Services to re-engage website visitors, CRM contacts, and social media engagers with targeted ads across Facebook, Instagram, Messenger, and the Audience Network. With an average 4.2x ROAS for retargeting campaigns (2026 benchmark) and retargeted visitors being 43% more likely to convert, Meta remains a critical channel for B2B lead nurturing.

**Use case for OpenClaw**: Sync GHL CRM contacts into Meta Custom Audiences, install the Meta Pixel + Conversions API for website tracking, and run retargeting campaigns to nurture leads through the sales pipeline.

---

## API / Integration Details

### Meta Marketing API (v24.0, 2026)

**Base URL**: `https://graph.facebook.com/v24.0/`

**Authentication**: System User access token with `ads_management`, `ads_read`, and `business_management` permissions.

**Key endpoints**:

| Endpoint | Purpose |
|----------|---------|
| `act_{ad_account_id}/customaudiences` | Create/manage Custom Audiences |
| `act_{ad_account_id}/campaigns` | Campaign CRUD operations |
| `act_{ad_account_id}/adsets` | Ad set management (targeting, budget) |
| `act_{ad_account_id}/ads` | Ad creative management |
| `{pixel_id}/events` | Server-side event tracking (CAPI) |
| `act_{ad_account_id}/insights` | Performance reporting |

### Meta Pixel

The Meta Pixel is a JavaScript snippet installed on all website pages to track user actions:

```html
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{PIXEL_ID}');
fbq('track', 'PageView');
</script>
```

**Standard events to track**:
- `PageView` - All page visits
- `Lead` - Form submission / inquiry
- `Contact` - Phone call click or chat initiation
- `CompleteRegistration` - Account/consultation signup
- `ViewContent` - Services page views (with content_name parameter)

### Conversions API (CAPI)

Server-side event tracking that sends data directly from your server to Meta's server, bypassing browser limitations (ad blockers, cookie restrictions).

**Setup requirements**:
1. Generate a CAPI Access Token in Events Manager
2. Send events via POST to `https://graph.facebook.com/v24.0/{PIXEL_ID}/events`
3. Include user identification parameters for matching

```python
# Example CAPI event
import requests
import hashlib
import time

payload = {
    "data": [{
        "event_name": "Lead",
        "event_time": int(time.time()),
        "action_source": "website",
        "event_source_url": "https://swrecovery.com/contact",
        "user_data": {
            "em": [hashlib.sha256(email.lower().encode()).hexdigest()],
            "ph": [hashlib.sha256(phone.encode()).hexdigest()],
            "client_ip_address": request.remote_addr,
            "client_user_agent": request.headers.get('User-Agent'),
            "fbc": request.cookies.get('_fbc'),
            "fbp": request.cookies.get('_fbp')
        },
        "custom_data": {
            "currency": "USD",
            "value": deal_value
        }
    }],
    "access_token": CAPI_ACCESS_TOKEN
}

response = requests.post(
    f"https://graph.facebook.com/v24.0/{PIXEL_ID}/events",
    json=payload
)
```

**Event Match Quality (EMQ)**:
- Score from 1-10 indicating how well events can be matched to real users
- Target EMQ of 6+ for good performance
- Include as many user identifiers as possible: email, phone, external_id, fbp, fbc
- Higher EMQ = better attribution, optimization, and audience quality

**Best practice**: Run Pixel + CAPI simultaneously with event deduplication (use `event_id` parameter) for maximum data quality.

### Custom Audiences

| Audience Type | Source | Min Size | Retention |
|--------------|--------|----------|-----------|
| Website Custom Audience | Pixel events | 100 users | Up to 180 days |
| Customer List | CRM upload (hashed) | 100 matched | Until updated |
| Engagement Audience | FB/IG interactions | 100 users | Up to 365 days |
| Video Viewers | Video watch % | 100 users | Up to 365 days |
| Lead Form Audience | Lead Ad submissions | 100 users | Up to 90 days |
| Lookalike Audience | Seed audience | N/A | Auto-refreshed |

**2025-2026 compliance changes**:
- Since September 2025, Meta proactively disables Custom Audiences containing sensitive health or financial data
- Audiences named with terms like "diabetes" or "high income" are automatically flagged and rejected
- From January 2026, `lookalike_spec` field is mandatory for creating new Lookalike Audiences
- Stricter enforcement on data containing sensitive categories

### Customer List Upload

```python
# Create Custom Audience from CRM contacts
audience = {
    "name": "SW Recovery - Hot Leads Q1 2026",
    "subtype": "CUSTOM",
    "description": "Leads from GHL with deal value > $50K",
    "customer_file_source": "USER_PROVIDED_ONLY"
}

# Upload hashed user data
users_payload = {
    "payload": {
        "schema": ["EMAIL", "PHONE", "FN", "LN"],
        "data": [
            [sha256(email), sha256(phone), sha256(first_name), sha256(last_name)]
            # ... more rows
        ]
    }
}
```

---

## Implementation Approach

### Phase 1: Tracking Infrastructure (Week 1)

1. **Install Meta Pixel**
   - Add base pixel code to all SW Recovery website pages
   - Configure standard events (Lead, Contact, ViewContent)
   - Verify pixel firing via Meta Pixel Helper browser extension

2. **Set up Conversions API**
   - Generate CAPI access token in Events Manager
   - Implement server-side event tracking (via GTM Server-Side or custom middleware)
   - Configure event deduplication with matching `event_id`
   - Validate EMQ score target of 6+

3. **Domain verification**
   - Verify swrecovery.com domain in Business Manager
   - Configure Aggregated Event Measurement (AEM) priorities
   - Set up 8 prioritized conversion events

### Phase 2: Audience Building (Week 2)

4. **Create website Custom Audiences**
   - All visitors (30/60/90 day windows)
   - Services page visitors
   - Contact page visitors (high intent)
   - Converters (for exclusion and lookalike seeding)

5. **CRM audience sync**
   - Export GHL contacts by pipeline stage
   - Hash PII data (SHA-256: email, phone, name)
   - Upload via Marketing API Custom Audiences endpoint
   - Create audiences:
     - Active leads (pipeline stage: qualification+)
     - Past clients (closed-won, last 2 years)
     - Cold leads (no activity > 90 days)

6. **Lookalike Audiences**
   - Create 1%, 3%, 5% lookalikes from best customers
   - Create lookalike from highest-value deals
   - Use `lookalike_spec` field (mandatory since Jan 2026)

### Phase 3: Campaign Launch (Week 3)

7. **Retargeting campaign structure**
   ```
   Campaign: SW Recovery Retargeting
   ├── Ad Set: Website Visitors (30 days)
   │   ├── Ad: Testimonial carousel
   │   └── Ad: Case study video
   ├── Ad Set: High Intent (Contact page visitors)
   │   ├── Ad: Direct CTA - "Schedule Your Consultation"
   │   └── Ad: Urgency messaging
   ├── Ad Set: CRM Hot Leads
   │   ├── Ad: Personalized offer
   │   └── Ad: Social proof (results)
   └── Ad Set: Past Clients (Referral/Upsell)
       ├── Ad: Referral program
       └── Ad: New service announcement
   ```

8. **Ad creative development**
   - Image ads (1080x1080, 1200x628)
   - Video ads (15-30 second testimonials/case studies)
   - Carousel ads (multiple services/results)
   - Lead Form ads for direct in-platform capture

### Phase 4: Automation & Optimization (Week 4+)

9. **Automated audience refresh**
   ```
   GHL CRM Webhook --> Make.com / n8n --> Meta Marketing API
        (contact stage change)          (add/remove from audience)
   ```

10. **Campaign rules**
    - Auto-pause ad sets with CPA > $X threshold
    - Scale budget for ad sets with ROAS > 3x
    - Rotate creatives every 2 weeks to prevent fatigue
    - Frequency cap: max 3 impressions/user/day

---

## GHL to Meta Ads Integration

### Recommended Approach: Make.com / n8n Workflow

```
Trigger: GHL contact enters pipeline stage
  --> Hash contact email (SHA-256)
  --> POST to Meta Custom Audiences API
  --> Add user to appropriate audience
  --> Log sync event for audit trail
```

**Alternative**: Use a Customer Data Platform (CDP) like Segment or Hightouch for multi-platform audience sync (Meta + Google + LinkedIn from single source).

---

## Cost Implications

### Platform Costs

| Item | Cost | Notes |
|------|------|-------|
| Meta Marketing API | Free | No API usage fees |
| Meta Pixel | Free | JavaScript tracking |
| Meta ad spend (retargeting) | $500-$2,000/month | Recommended starting budget |
| Make.com / n8n (automation) | $10-$50/month | Webhook processing |

### Retargeting Performance Benchmarks

| Metric | Average | Top Performers | Notes |
|--------|---------|---------------|-------|
| CTR (retargeting) | 0.7-1.5% | 2-3% | 10x higher than cold display |
| CPC (retargeting) | $0.50-$2.00 | $0.30-$0.80 | Lower than prospecting |
| CPM | $8-$15 | $5-$10 | Retargeting audiences |
| Conversion rate | 3-8% | 10%+ | vs 1-2% cold traffic |
| ROAS | 4.2x average | 8-12x | 2026 retargeting benchmark |

### Monthly Budget Recommendation

| Phase | Monthly Spend | Focus |
|-------|-------------|-------|
| Testing (Month 1-2) | $500-$1,000 | Pixel data collection, audience building |
| Scaling (Month 3-4) | $1,000-$2,000 | Optimize winning audiences/creatives |
| Mature (Month 5+) | $1,500-$3,000 | Full funnel with lookalikes |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Business Manager / Events Manager setup | 2 | Domain verification, pixel creation |
| Meta Pixel installation (website) | 2-3 | Base code, standard events |
| Conversions API setup | 4-6 | Server-side tracking, deduplication |
| Custom Audience creation | 3-4 | Website, CRM, engagement audiences |
| CRM sync automation (GHL --> Meta) | 4-6 | Make.com/n8n workflow |
| Campaign structure and setup | 4-6 | Ad sets, targeting, budgets |
| Ad creative development | 6-8 | Images, videos, carousels, copy |
| Lookalike audience creation | 2 | Seed audiences, expansion testing |
| Testing and QA | 3-4 | Pixel validation, audience matching |
| **Total** | **30-41 hours** | |

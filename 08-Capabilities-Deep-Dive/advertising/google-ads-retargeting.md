# Google Ads API: Retargeting, Audience Creation & Campaign Automation

## Overview

Google Ads retargeting enables SW Recovery Services to re-engage website visitors, past leads, and CRM contacts with targeted display, search, and video ads. The Google Ads API (v23, released January 2026) provides programmatic control over audience creation, campaign management, conversion tracking, and budget optimization. This document covers technical implementation, API integration, and automation strategies.

**Use case for OpenClaw**: Automatically create retargeting audiences from GHL CRM data (e.g., leads who visited the site but did not convert, contacts from specific pipeline stages) and serve them tailored ads across Google's network.

---

## API / Integration Details

### Google Ads API v23 (January 2026)

**Base URL**: `https://googleads.googleapis.com/v23/`

**Authentication**: OAuth 2.0 with a developer token, client ID, client secret, and refresh token. Requires a Google Ads Manager account linked to the target ad account.

**Key endpoints for retargeting**:

| Endpoint | Purpose |
|----------|---------|
| `customers/{id}/userLists` | Create/manage remarketing lists |
| `customers/{id}/customerMatchUserListMetadata` | Upload CRM data (Customer Match) |
| `customers/{id}/campaigns` | Create/manage campaigns |
| `customers/{id}/adGroups` | Ad group management |
| `customers/{id}/ads` | Ad creative management |
| `customers/{id}/campaignBudgets` | Budget allocation |
| `AudienceInsightsService.GenerateAudienceDefinition` | NEW: AI-powered natural language audience building |

**v23 Notable Features**:
- Monthly release cadence (previously quarterly)
- AI-powered natural language audience building via `GenerateAudienceDefinition`
- Enhanced Performance Max reporting with ad network type breakdowns
- Granular invoice data at campaign level
- Precise datetime scheduling replacing legacy date-only fields
- New `LIFE_EVENT_USER_INTEREST` audience dimension

**Migration deadline**: API v19 reaches end-of-life February 11, 2026. All requests to v19 endpoints will fail after that date.

### Audience Segment Types

| Segment Type | Description | Data Source |
|-------------|-------------|-------------|
| Website Visitors | Users who visited specific pages | Google Tag / GTM |
| Customer Match | CRM email/phone/address lists | Upload via API |
| Custom Audiences | Interest-based or search-term audiences | Keywords/URLs |
| Similar Audiences | Users similar to existing lists | ML-generated |
| Lookalike Segments | Extended reach beyond similar | Algorithm |
| Combined Segments | Boolean combinations of lists | Multiple sources |

### Google Tag Setup

The Google Tag (gtag.js) is the single foundational tracking snippet that powers all Google Ads tracking:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=AW-XXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'AW-XXXXXXXXX');
</script>
```

**Functions handled by the Google Tag**:
- First-party cookie management
- Remarketing audience building
- Conversion tracking foundation
- Cross-domain tracking

**Google Tag Manager (GTM) alternative**:
- Install GTM container on all pages
- Create a Google Ads Remarketing tag (no Conversion Label needed)
- Set trigger to fire on all pages
- Create separate Conversion Tracking tags with Conversion ID + Label for each conversion action

### Conversion Tracking Setup

```
Google Tag Manager Container
├── Google Ads Remarketing Tag (all pages)
├── Google Ads Conversion Tag: Form Submit (thank you page)
├── Google Ads Conversion Tag: Phone Call (click-to-call)
└── Google Ads Conversion Tag: Chat Start (bot interaction)
```

Each conversion tag requires:
- **Conversion ID**: From Google Ads account (shared across all conversions)
- **Conversion Label**: Unique per conversion action
- **Conversion Value**: Optional, can be dynamic (deal size)

---

## Implementation Approach

### Phase 1: Tracking Foundation (Week 1)

1. **Install Google Tag on SW Recovery website**
   - Add gtag.js snippet to all pages via GTM or directly
   - Configure enhanced conversions for improved attribution
   - Set up cross-domain tracking if multiple domains exist

2. **Define conversion actions**
   - Form submission (lead inquiry)
   - Phone call from website
   - Chat/bot interaction initiated
   - Page visit duration (engaged visit > 30 seconds)

3. **Create base remarketing audiences**
   - All website visitors (last 30/60/90 days)
   - Specific page visitors (services pages, contact page)
   - Converters (for exclusion from prospecting)

### Phase 2: CRM Integration (Week 2)

4. **Customer Match setup**
   - Export contact lists from GHL CRM
   - Format as hashed email addresses (SHA-256)
   - Upload via `OfflineUserDataJobService` API endpoint
   - Create audiences by pipeline stage:
     - "Hot leads" (deals > $50K)
     - "Nurture" (initial inquiry, no deal yet)
     - "Past clients" (for referral/upsell campaigns)

5. **Automated sync pipeline**
   ```
   GHL CRM --> Webhook/API --> Middleware --> Google Ads API
        (contact enters stage)              (add to audience list)
   ```

### Phase 3: Campaign Automation (Week 3)

6. **Create retargeting campaigns**
   - Display remarketing (banner ads across Google Display Network)
   - Search remarketing (RLSA - bid adjustments for past visitors)
   - YouTube remarketing (video ads to website visitors)

7. **Budget management via API**
   ```python
   # Example: Create a campaign budget
   campaign_budget = client.get_type("CampaignBudget")
   campaign_budget.name = "SW Recovery Retargeting Budget"
   campaign_budget.amount_micros = 50_000_000  # $50/day
   campaign_budget.delivery_method = (
       client.enums.BudgetDeliveryMethodEnum.STANDARD
   )
   ```

8. **Automated rules**
   - Pause campaigns if CPA exceeds threshold
   - Increase budget for high-performing audiences
   - Rotate ad creatives based on performance
   - Alert on spend anomalies

### Phase 4: Optimization (Ongoing)

9. **Performance Max campaigns**
   - Leverage v23 enhanced reporting for network-level insights
   - Use AI-powered audience suggestions
   - Monitor auction insights for competitive intelligence

10. **Reporting integration**
    - Pull performance data via API into reporting dashboard
    - Track ROAS by audience segment
    - Attribution modeling across touchpoints

---

## GHL to Google Ads Integration Options

### Option A: Direct API Integration (Custom)
- Build middleware that listens for GHL webhooks
- On contact status change, update Google Ads Customer Match lists
- Pros: Real-time sync, full control
- Cons: Development time, maintenance burden

### Option B: Zapier / Make.com Bridge
- Trigger: GHL contact enters specific pipeline stage
- Action: Add hashed email to Google Ads Customer Match list
- Pros: No-code, fast setup
- Cons: Zapier costs, slight delay, rate limits

### Option C: Third-Party CDP (Segment, Hightouch)
- Sync CRM data to Google Ads audiences via customer data platform
- Pros: Scalable, multi-platform sync
- Cons: Additional SaaS cost, complexity

**Recommended**: Start with Option B (Zapier) for quick wins, migrate to Option A as volume grows.

---

## Cost Implications

### Platform Costs

| Item | Cost | Notes |
|------|------|-------|
| Google Ads API | Free | No API usage fees |
| Google Tag Manager | Free | Tag management platform |
| Google Ads spend (retargeting) | $500-$2,000/month | Depends on audience size |
| Zapier integration (if used) | $20-$70/month | 2,000-5,000 tasks/month |

### Typical Retargeting CPCs and CPMs

| Campaign Type | Average CPC | Average CPM | Notes |
|--------------|------------|------------|-------|
| Display Remarketing | $0.25-$1.50 | $2-$10 | Banner ads |
| Search RLSA | $2-$8 | N/A | Bid modifier on search |
| YouTube Remarketing | $0.10-$0.30 | $5-$15 | Video ads |
| Performance Max | Varies | Varies | ML-optimized |

### Expected Performance

| Metric | Benchmark | Notes |
|--------|-----------|-------|
| Retargeting CTR | 0.7-1.5% | vs 0.07% for standard display |
| Conversion rate | 2-5x higher | vs cold traffic |
| CPA reduction | 30-50% | vs non-retargeted campaigns |
| ROAS | 3-5x | Varies by industry |

### Monthly Budget Recommendation

| Phase | Monthly Spend | Focus |
|-------|-------------|-------|
| Testing (Month 1-2) | $500-$1,000 | Audience building, baseline data |
| Scaling (Month 3-4) | $1,000-$2,000 | Optimize winning audiences |
| Mature (Month 5+) | $1,500-$3,000 | Full funnel retargeting |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Google Ads account setup and linking | 2 | Manager account, API access |
| Google Tag / GTM installation | 3-4 | Tag setup, conversion actions |
| Conversion tracking configuration | 3-4 | Define actions, test tracking |
| Audience segment creation | 3-4 | Website visitors, Customer Match |
| GHL-to-Google Ads sync (Zapier) | 4-6 | Webhook setup, audience sync |
| Campaign creation (Display + RLSA) | 4-6 | Ad groups, creatives, targeting |
| Ad creative development | 4-6 | Banner sizes, copy, responsive ads |
| Reporting dashboard setup | 3-4 | API data pull, visualization |
| Testing and QA | 3-4 | Pixel validation, audience verification |
| **Total** | **29-38 hours** | |

# LinkedIn Ads: Campaign Manager API, Matched Audiences & Lead Gen Forms

## Overview

LinkedIn is the premier B2B advertising platform, providing access to 1B+ professional members with granular targeting by job title, company size, industry, seniority, and skills. For SW Recovery Services, LinkedIn Ads enables precise targeting of decision-makers at companies that may need recovery services, asset management, or related financial services.

**Use case for OpenClaw**: Run retargeting campaigns to website visitors and CRM contacts via Matched Audiences, capture leads directly through Lead Gen Forms (2-3x higher conversion than landing pages), and layer account-based marketing (ABM) targeting on top of company lists.

---

## API / Integration Details

### LinkedIn Marketing API (v202601)

**Base URL**: `https://api.linkedin.com/rest/`

**Authentication**: OAuth 2.0 with 3-legged authorization flow. Requires app creation in LinkedIn Developer Portal with Marketing Developer Platform product added.

**Access requirements**:
- Create LinkedIn app in Developer Portal
- Add "Marketing Developer Platform" product
- Complete access form with use case (Campaign Management, Reporting, or Page Management)
- Audiences API is a separate private API requiring additional approval
- DMP Segment APIs require separate application from Marketing API access

**API version header**: `LinkedIn-Version: 202601` (January 2026 release)

**Key endpoints**:

| Endpoint | Purpose |
|----------|---------|
| `/adAccounts` | Ad account management |
| `/adCampaignGroups` | Campaign group CRUD |
| `/adCampaigns` | Campaign management |
| `/adCreatives` | Creative/ad management |
| `/adTargetingEntities` | Targeting facets (job title, company, etc.) |
| `/adAnalytics` | Reporting and metrics |
| `/dmpSegments` | DMP segment management (Matched Audiences) |
| `/adForms` | Lead Gen Form management |
| `/adFormResponses` | Retrieve Lead Gen Form submissions |

**v202601 notable updates**:
- New Event and Video Watch Time metrics for `/adAnalytics` endpoint
- DMP Segment List Uploads via CSV files sunset September 16, 2025 (use Streaming API instead)
- Enhanced conversion tracking capabilities

### Matched Audiences

Matched Audiences enable retargeting and account-based targeting on LinkedIn:

**Website Retargeting**
- Install LinkedIn Insight Tag on all website pages
- Create audience segments based on page visits, URL rules
- Minimum audience size: 300 members
- Retention window: up to 180 days

```html
<!-- LinkedIn Insight Tag -->
<script type="text/javascript">
_linkedin_partner_id = "PARTNER_ID";
window._linkedin_data_partner_ids = window._linkedin_data_partner_ids || [];
window._linkedin_data_partner_ids.push(_linkedin_partner_id);
</script>
<script type="text/javascript">
(function(l) {
if (!l){window.lintrk = function(a,b){window.lintrk.q.push([a,b])};
window.lintrk.q=[]}
var s = document.getElementsByTagName("script")[0];
var b = document.createElement("script");
b.type = "text/javascript";b.async = true;
b.src = "https://snap.licdn.com/li.lms-analytics/insight.min.js";
s.parentNode.insertBefore(b, s);})(window.lintrk);
</script>
```

**Contact List Targeting**
- Upload SHA256-hashed email addresses
- Via Streaming API (POST individual records) or batch upload
- Minimum match: 300 LinkedIn members
- Match rate typically 30-60% for B2B email lists
- Rate limit: 1-minute rate limit per user for streaming APIs

```python
# Upload contact to DMP segment via Streaming API
import requests

headers = {
    "Authorization": f"Bearer {access_token}",
    "LinkedIn-Version": "202601",
    "Content-Type": "application/json"
}

payload = {
    "elements": [{
        "userIds": [{
            "idType": "SHA256_EMAIL",
            "idValue": sha256_hash_of_email
        }]
    }]
}

response = requests.post(
    f"https://api.linkedin.com/rest/dmpSegments/{segment_id}/users",
    headers=headers,
    json=payload
)
```

**Company List Targeting (ABM)**
- Upload company names or company domains
- LinkedIn matches to company pages
- Layer with job title, seniority, function targeting
- Minimum: 300 matched companies
- Ideal for targeting specific accounts with recovery service needs

**Lead Gen Form Audiences**
- Retarget users who opened but did not submit a Lead Gen Form
- Target users who submitted forms for follow-up campaigns
- Available for up to 90 days

### Lead Gen Forms

Lead Gen Forms are pre-filled forms that appear natively in the LinkedIn feed, eliminating the need for a landing page:

**Key advantages**:
- Pre-populated with member's LinkedIn profile data (name, email, job title, company)
- 2-3x higher conversion rate than landing pages
- Verified professional data (vs self-reported)
- No landing page development needed
- Mobile-optimized natively

**Form fields available**:
| Auto-filled | Custom Fields |
|------------|--------------|
| First name | Custom text fields |
| Last name | Custom checkbox |
| Email address | Custom dropdown |
| Phone number | Custom multi-select |
| Job title | Hidden fields |
| Company name | Custom consent checkbox |
| Company size | |
| Industry | |
| City/State | |

**Form configuration via API**:
```json
{
  "name": "SW Recovery - Free Consultation",
  "headline": "Schedule Your Free Recovery Assessment",
  "description": "Our experts will evaluate your situation and provide a customized recovery plan.",
  "privacyPolicyUrl": "https://swrecovery.com/privacy",
  "thankYouMessage": "Thank you! Our team will contact you within 24 hours.",
  "questions": [
    {
      "questionType": "CUSTOM",
      "customQuestionText": "What is your estimated recovery amount?",
      "answerType": "SINGLE_LINE_TEXT",
      "required": true
    },
    {
      "questionType": "CUSTOM",
      "customQuestionText": "Best time to reach you?",
      "answerType": "DROPDOWN",
      "answerOptions": ["Morning", "Afternoon", "Evening"],
      "required": false
    }
  ]
}
```

**Lead Gen Form --> CRM Integration**:
- Native integrations: HubSpot, Salesforce, Marketo
- Via API: Poll `/adFormResponses` endpoint for new submissions
- Via Zapier/Make.com: Webhook trigger on new lead
- GHL integration: Use Zapier to route LinkedIn leads into GHL pipeline

### Conversion Tracking

LinkedIn Conversions API enables server-side conversion tracking:

| Method | Setup | Reliability |
|--------|-------|------------|
| Insight Tag (client-side) | JavaScript on website | Subject to ad blockers |
| Conversions API (server-side) | Server-to-server events | Higher reliability |
| Both (recommended) | Dual tracking | Best attribution |

---

## Implementation Approach

### Phase 1: Tracking Setup (Week 1)

1. **Install LinkedIn Insight Tag**
   - Add to all SW Recovery website pages via GTM or direct
   - Configure URL-based audience rules
   - Verify tag firing via LinkedIn Tag Validator

2. **Set up conversion tracking**
   - Define conversion events (form submit, phone call, chat)
   - Configure both Insight Tag and Conversions API
   - Set attribution windows (30-day click, 7-day view)

### Phase 2: Audience Building (Week 2)

3. **Create Matched Audiences**
   - Website Retargeting: All visitors, services page visitors, high-intent visitors
   - Contact Upload: GHL CRM contacts (hashed emails via Streaming API)
   - Company List: Target companies by domain from CRM

4. **ABM targeting layers**
   - Upload target company list (top 100-500 target accounts)
   - Layer with decision-maker criteria:
     - Job functions: Finance, Operations, Legal, C-Suite
     - Seniority: Director, VP, C-level
     - Company size: 50-5,000 employees (mid-market focus)

### Phase 3: Campaign Launch (Week 3)

5. **Campaign structure**
   ```
   Campaign Group: SW Recovery LinkedIn
   ├── Campaign: Website Retargeting
   │   ├── Single Image Ad: "Still considering recovery options?"
   │   └── Video Ad: Client success story
   ├── Campaign: ABM - Target Accounts
   │   ├── Sponsored Content: Industry insights
   │   └── Lead Gen Form: Free consultation offer
   ├── Campaign: CRM Nurture
   │   ├── Message Ad: Direct InMail offer
   │   └── Carousel Ad: Service showcase
   └── Campaign: Lead Gen Forms
       ├── Form: Free Recovery Assessment
       └── Form: Download Case Study
   ```

6. **Ad format selection**
   | Format | Best For | Avg CTR |
   |--------|---------|---------|
   | Single Image | Retargeting, awareness | 0.4-0.6% |
   | Video | Storytelling, testimonials | 0.3-0.5% |
   | Carousel | Multiple services/results | 0.5-0.7% |
   | Message Ads | Direct outreach, offers | 30-50% open rate |
   | Lead Gen Forms | Lead capture | 2-3x vs landing pages |
   | Document Ads | Thought leadership | 0.4-0.8% |

### Phase 4: Automation (Week 4+)

7. **Lead routing automation**
   ```
   LinkedIn Lead Gen Form submission
     --> Zapier/Make.com webhook
     --> Create contact in GHL CRM
     --> Assign to pipeline stage
     --> Trigger follow-up sequence
     --> Notify sales team via Slack
   ```

8. **Audience refresh automation**
   - Weekly CRM contact sync to LinkedIn Matched Audiences
   - Remove converted leads from retargeting audiences
   - Add new leads to nurture audiences

---

## Cost Implications

### Platform Costs

| Item | Cost | Notes |
|------|------|-------|
| LinkedIn Marketing API | Free | With approved access |
| LinkedIn Insight Tag | Free | JavaScript tracking |
| Minimum daily budget | $10/day | LinkedIn minimum |
| Recommended starting budget | $50-$100/day | For meaningful data |
| Zapier (Lead Gen routing) | $20-$70/month | Webhook processing |

### LinkedIn Ad Cost Benchmarks (2026)

| Metric | Average | Range | Notes |
|--------|---------|-------|-------|
| CPC | $8-$10 (US) | $2.59-$12+ | Varies by targeting |
| CPM | $33-$55 | $31-$100 | Higher for C-suite targeting |
| Cost per lead (Lead Gen Forms) | $25-$75 | $15-$150 | Industry dependent |
| Cost per InMail send | $0.50-$1.00 | Varies | Message Ads |
| Minimum CPC bid | $2.00 | Fixed | Platform minimum |
| Minimum CPM bid | $2.00 | Fixed | Platform minimum |

**LinkedIn vs other platforms**: LinkedIn CPC ($8-$10) is significantly higher than Facebook ($0.50-$2.00) or Google Display ($0.50-$1.50), but lead quality for B2B is substantially higher, often yielding better cost-per-qualified-lead ratios.

### Monthly Budget Recommendation

| Phase | Monthly Spend | Focus |
|-------|-------------|-------|
| Testing (Month 1-2) | $1,500-$3,000 | Audience building, form testing |
| Scaling (Month 3-4) | $3,000-$5,000 | Optimize winners, ABM expansion |
| Mature (Month 5+) | $3,000-$7,000 | Full funnel ABM + retargeting |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| LinkedIn Campaign Manager account setup | 2 | Billing, API access request |
| Insight Tag installation | 2 | GTM or direct, verification |
| Conversion tracking configuration | 2-3 | Events, attribution windows |
| Matched Audiences creation | 4-6 | Website, contact, company lists |
| Lead Gen Form design and setup | 3-4 | Forms, custom fields, privacy |
| Campaign creation and targeting | 4-6 | Ad sets, audience layers, bids |
| Ad creative development | 6-8 | Images, video, carousels, copy |
| Lead routing automation (Zapier/GHL) | 4-6 | Webhook, CRM mapping, sequences |
| Conversions API setup | 3-4 | Server-side tracking |
| Testing and QA | 3-4 | Tag validation, lead flow |
| **Total** | **33-45 hours** | |

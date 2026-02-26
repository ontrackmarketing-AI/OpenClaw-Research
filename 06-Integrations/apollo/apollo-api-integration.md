# Apollo.io API Integration: Enrichment & Search

## Overview

Apollo.io is a sales intelligence platform with 275M+ contacts and 73M+ companies. Their API
provides enrichment (add data to known contacts), search (find new leads), and intent data.
For OpenClaw, Apollo serves as the enrichment engine — when a new contact enters Nutshell CRM,
Apollo fills in title, company, LinkedIn, revenue, employee count, tech stack, and more.

**Primary Use Cases:**
1. **Contact Enrichment**: New lead enters Nutshell -> Apollo fills missing fields (title, company, LinkedIn, phone)
2. **Company Enrichment**: Identify company size, revenue, funding, tech stack for deal scoring
3. **Lead Discovery**: Search Apollo's database for prospects matching ideal customer profile
4. **Bulk Enrichment**: Enrich entire contact lists during import or periodic refresh

**API Base URL:** `https://api.apollo.io/api/v1/`

---

## API/Integration Details

### Authentication

Apollo supports two authentication methods:

```bash
# Method 1: Bearer Token (recommended for OAuth flows)
Authorization: Bearer YOUR_ACCESS_TOKEN

# Method 2: API Key Header
x-api-key: YOUR_API_KEY
```

API keys are generated in Apollo Settings > Integrations > API.

### Core Endpoints

#### 1. People Enrichment (Single)

**Endpoint:** `POST https://api.apollo.io/api/v1/people/match`

Enrich a single person by providing identifying information. Apollo matches against its database
and returns the full profile.

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `first_name` | string | No* | Person's first name |
| `last_name` | string | No* | Person's last name |
| `name` | string | No* | Full name (alternative to first/last) |
| `email` | string | No* | Email address |
| `hashed_email` | string | No* | MD5 or SHA-256 hashed email |
| `organization_name` | string | No* | Employer name |
| `domain` | string | No* | Company domain (e.g., `apollo.io`) |
| `id` | string | No* | Apollo person ID (if known) |
| `linkedin_url` | string | No* | LinkedIn profile URL |
| `reveal_personal_emails` | boolean | No | Include personal emails (costs extra credits) |
| `reveal_phone_number` | boolean | No | Include phone numbers (async via webhook) |
| `webhook_url` | string | Cond. | Required if `reveal_phone_number=true` |

*At least one identifier required. More identifiers = better match accuracy.

**Example Request:**
```bash
curl -X POST "https://api.apollo.io/api/v1/people/match" \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "first_name": "Tim",
    "last_name": "Zheng",
    "domain": "apollo.io"
  }'
```

**Response Fields (key fields):**
```json
{
  "person": {
    "id": "5f2b...",
    "first_name": "Tim",
    "last_name": "Zheng",
    "name": "Tim Zheng",
    "title": "Founder & CEO",
    "headline": "CEO at Apollo.io",
    "email": "tim@apollo.io",
    "email_status": "verified",
    "linkedin_url": "https://www.linkedin.com/in/timzheng",
    "photo_url": "https://...",
    "city": "San Francisco",
    "state": "California",
    "country": "United States",
    "seniority": "founder",
    "departments": ["c_suite"],
    "functions": ["entrepreneurship"],
    "is_likely_to_engage": true,
    "employment_history": [
      {
        "organization_name": "Apollo.io",
        "title": "Founder & CEO",
        "start_date": "2015-01-01",
        "current": true
      }
    ],
    "organization": {
      "name": "Apollo.io",
      "website_url": "http://www.apollo.io",
      "industry": "information technology & services",
      "estimated_num_employees": 1600,
      "annual_revenue": 100000000
    }
  }
}
```

#### 2. Bulk People Enrichment

**Endpoint:** `POST https://api.apollo.io/api/v1/people/bulk_match`

Enrich up to 10 people per request. Same parameters as single enrichment but wrapped in `details` array.

**Request:**
```json
{
  "details": [
    { "first_name": "Tim", "last_name": "Zheng", "domain": "apollo.io" },
    { "first_name": "John", "last_name": "Doe", "email": "john@example.com" }
  ],
  "reveal_personal_emails": false,
  "reveal_phone_number": false
}
```

**Response:**
```json
{
  "status": "success",
  "total_requested_enrichments": 2,
  "unique_enriched_records": 2,
  "missing_records": 0,
  "credits_consumed": 2,
  "matches": [ /* array of person objects */ ]
}
```

**Batch Size Limit:** 10 people per request. For larger lists, loop with rate limiting.

#### 3. Organization Enrichment

**Endpoint:** `GET https://api.apollo.io/api/v1/organizations/enrich`

Enrich a company by domain or name.

**Request Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | string | Company domain (e.g., `apollo.io`) |
| `organization_name` | string | Company name |

**Response Fields (key fields):**
```json
{
  "organization": {
    "id": "5e66...",
    "name": "Apollo.io",
    "website_url": "http://www.apollo.io",
    "industry": "information technology & services",
    "estimated_num_employees": 1600,
    "annual_revenue": 100000000,
    "total_funding": 251200000,
    "latest_funding_stage": "Series D",
    "linkedin_url": "https://www.linkedin.com/company/apolloio",
    "phone": "+1-415-...",
    "city": "San Francisco",
    "state": "California",
    "country": "United States",
    "technologies": ["google_analytics", "hubspot", "salesforce", "..."],
    "keywords": ["sales engagement", "sales intelligence", "..."]
  }
}
```

#### 4. Bulk Organization Enrichment

**Endpoint:** `POST https://api.apollo.io/api/v1/organizations/bulk_enrich`

Enrich up to 10 companies per request. Domains passed as array.

#### 5. People Search (Discovery)

**Endpoint:** `POST https://api.apollo.io/api/v1/mixed_people/api_search`

Search Apollo's database for people matching criteria. Does NOT return emails/phones
(use enrichment endpoints for that). Does NOT consume credits.

**Key Filters:**
- Name, title, company, domain
- Location (city, state, country)
- Seniority level, department, function
- Company size, revenue, industry
- Technologies used

**Limits:** 100 results per page, max 500 pages (50,000 total results).

### Rate Limits

Apollo uses fixed-window rate limiting. Limits vary by plan:

| Plan | Per Minute | Per Hour | Per Day | Notes |
|------|-----------|----------|---------|-------|
| Free | 50 | 100 | 600 | Limited enrichment credits |
| Basic | 100 | 300 | 2,000 | Reasonable for small teams |
| Professional | 200 | 600 | 5,000 | Best for automation |
| Organization | 200+ | Custom | Custom | Enterprise SLA |

*These are approximate limits based on community reports. Exact limits shown
in Apollo dashboard under Settings > API Usage.*

**Bulk endpoint throttling**: Bulk endpoints are throttled to 50% of the single
endpoint's per-minute rate. Hourly and daily limits are shared (100% of individual).

**Rate Limit Response:**
```
HTTP 429 Too Many Requests
```

### Credit System

Apollo uses a credit-based system. Each enrichment consumes credits:

| Action | Credit Cost |
|--------|-------------|
| People enrichment | 1 credit |
| Organization enrichment | 1 credit |
| People search | 0 credits (free) |
| Reveal personal email | 1 additional credit |
| Reveal phone number | 1 additional credit |
| Email waterfall | Additional credits |

**Credit Allocations by Plan:**
| Plan | Monthly Credits | Price |
|------|----------------|-------|
| Free | 10,000 | $0 |
| Basic | 60,000 | $49/user/mo |
| Professional | 120,000 | $79/user/mo |
| Organization | Custom | $119+/user/mo |

---

## Implementation Approach

### Phase 1: Single Contact Enrichment (Week 1)
1. Set up Apollo API key in environment variables
2. Create n8n workflow: Nutshell new contact -> Apollo people/match -> Update Nutshell
3. Map Apollo fields to Nutshell custom fields:
   - `title` -> Nutshell "Job Title"
   - `linkedin_url` -> Nutshell "LinkedIn"
   - `organization.industry` -> Nutshell "Industry"
   - `organization.estimated_num_employees` -> Nutshell "Company Size"
   - `organization.annual_revenue` -> Nutshell "Revenue"
4. Handle non-matches gracefully (flag for manual enrichment)

### Phase 2: Bulk Enrichment (Week 2)
1. Create scheduled n8n workflow for nightly batch enrichment
2. Query Nutshell for contacts missing key fields
3. Batch into groups of 10, call `/people/bulk_match`
4. Implement rate limiting (respect per-minute caps)
5. Update Nutshell contacts with enriched data
6. Log enrichment results (matched/unmatched/errors)

### Phase 3: Company Intelligence (Week 2-3)
1. Auto-enrich company data when new organization created in Nutshell
2. Store tech stack, funding, employee count for deal scoring
3. Feed company data into AI voice bot for contextual conversations
4. Build ICP scoring model based on enriched company attributes

### n8n Workflow Example (Single Enrichment)
```
Trigger: Nutshell Webhook (new contact created)
  |
  v
Extract: first_name, last_name, email, company from Nutshell payload
  |
  v
HTTP Request: POST apollo.io/api/v1/people/match
  |
  v
IF: person.id exists (match found)
  |-- YES --> Map fields + Update Nutshell Contact
  |-- NO  --> Tag contact "needs-manual-enrichment" in Nutshell
```

---

## Cost Implications

### Apollo Subscription
| Plan | Price | Credits/mo | Best For |
|------|-------|-----------|----------|
| Free | $0 | 10,000 | Testing/proof of concept |
| Basic | $49/user/mo | 60,000 | Low-volume enrichment |
| Professional | $79/user/mo | 120,000 | Automation workflows |
| Organization | $119+/user/mo | Custom | High-volume operations |

### Projected Usage (Steven's Business)
- New contacts/month: ~50-100
- Company enrichments/month: ~30-50
- Bulk refresh (quarterly): ~500 contacts
- **Monthly credits needed: ~200-700**
- **Recommended plan: Free tier** (10,000 credits is more than sufficient)

### Infrastructure Costs
| Item | Cost | Notes |
|------|------|-------|
| n8n processing | $0 | Self-hosted on Mac Mini |
| API calls | $0 | Free tier covers projected volume |
| Supabase storage | Negligible | Enrichment cache in existing DB |

**Total incremental cost: $0/month** on Free tier for current volume.

---

## Estimated Build Hours

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1: Single Enrichment | API setup, n8n workflow, Nutshell mapping | 6-8 |
| Phase 2: Bulk Enrichment | Batch workflow, rate limiting, scheduling | 6-8 |
| Phase 3: Company Intelligence | Org enrichment, scoring model, bot integration | 8-10 |
| Testing & QA | Match accuracy validation, error handling | 4-6 |
| **Total** | | **24-32 hours** |

### Dependencies
- Apollo API key (free tier available)
- Nutshell CRM API credentials
- n8n instance with HTTP request capability
- Field mapping document (Apollo -> Nutshell custom fields)

### Risks
- Apollo match rates vary by data quality (email gives best results)
- Free tier rate limits may throttle bulk operations
- Credit costs increase if revealing personal emails/phones
- Apollo data freshness varies (some records may be outdated)

---

## References

- [Apollo API Overview](https://docs.apollo.io/docs/api-overview)
- [People Enrichment](https://docs.apollo.io/reference/people-enrichment)
- [Bulk People Enrichment](https://docs.apollo.io/reference/bulk-people-enrichment)
- [Organization Enrichment](https://docs.apollo.io/reference/organization-enrichment)
- [People API Search](https://docs.apollo.io/reference/people-api-search)
- [API Pricing](https://docs.apollo.io/docs/api-pricing)
- [Rate Limits](https://docs.apollo.io/reference/rate-limits)
- [View API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

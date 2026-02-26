# Apollo-Nutshell Contact Enrichment Sync

## Overview

This document details the automated pipeline that enriches Nutshell CRM contacts using
Apollo.io's enrichment API. When a new contact is created in Nutshell (manually, via web form,
or through CallRail), the system automatically queries Apollo to fill in missing professional
data — job title, LinkedIn URL, company details, revenue, employee count, and tech stack.

**Problem Solved:**
Steven enters leads into Nutshell with minimal information (often just name + phone or email).
Without enrichment, the CRM is a glorified address book. With Apollo enrichment, every contact
becomes a full profile that informs deal scoring, conversation context, and outreach strategy.

**Sync Architecture:**
```
Nutshell CRM (new/updated contact)
    |
    | Webhook trigger
    v
n8n Automation
    |
    | POST /api/v1/people/match
    v
Apollo.io Enrichment API
    |
    | Enriched data returned
    v
n8n Field Mapper
    |
    | PUT /api/v1/contacts/{id}
    v
Nutshell CRM (contact updated with enriched fields)
    |
    +---> AI Voice Bot (updated context)
    +---> Deal Scoring Engine (updated attributes)
```

---

## API/Integration Details

### Nutshell CRM Webhook Setup

Nutshell supports webhooks for contact lifecycle events. Configure via:
- **Nutshell Settings > Integrations > Webhooks**
- Alternatively, use Zapier/Pipedream as an intermediary if native webhooks are limited

**Trigger Events:**
| Event | Description | Enrichment Action |
|-------|-------------|-------------------|
| Contact Created | New contact added to CRM | Full enrichment (all fields) |
| Contact Updated | Existing contact modified | Conditional enrichment (only if key fields empty) |
| Lead Created | New lead/opportunity | Enrich associated contact + company |

**Nutshell Webhook Payload (expected structure):**
```json
{
  "event": "contact.created",
  "data": {
    "id": 12345,
    "name": { "first": "John", "last": "Smith" },
    "emails": [{ "address": "john@acme.com", "type": "work" }],
    "phones": [{ "number": "+15551234567", "type": "mobile" }],
    "company": { "name": "Acme Corp" },
    "custom_fields": {}
  }
}
```

### Apollo Enrichment Request

Using the People Match endpoint with available identifiers:

```python
import requests

def enrich_contact(contact: dict) -> dict:
    """Enrich a Nutshell contact via Apollo."""
    payload = {}

    # Map Nutshell fields to Apollo parameters
    if contact.get('name', {}).get('first'):
        payload['first_name'] = contact['name']['first']
    if contact.get('name', {}).get('last'):
        payload['last_name'] = contact['name']['last']
    if contact.get('emails'):
        payload['email'] = contact['emails'][0]['address']
    if contact.get('company', {}).get('name'):
        payload['organization_name'] = contact['company']['name']

    response = requests.post(
        'https://api.apollo.io/api/v1/people/match',
        headers={'x-api-key': APOLLO_API_KEY},
        json=payload
    )

    if response.status_code == 200:
        return response.json().get('person', {})
    return {}
```

### Field Mapping: Apollo -> Nutshell

| Apollo Field | Nutshell Field | Type | Notes |
|-------------|----------------|------|-------|
| `person.title` | Job Title | Standard | e.g., "VP of Operations" |
| `person.headline` | LinkedIn Headline | Custom | Professional summary |
| `person.linkedin_url` | LinkedIn URL | Custom | Profile link |
| `person.city` | City | Standard | Contact location |
| `person.state` | State | Standard | Contact state |
| `person.seniority` | Seniority Level | Custom | founder/c_suite/vp/director/manager |
| `person.departments` | Department | Custom | Array: sales, engineering, etc. |
| `organization.name` | Company Name | Standard | Verify/update |
| `organization.industry` | Industry | Custom | e.g., "construction", "real estate" |
| `organization.estimated_num_employees` | Company Size | Custom | Integer |
| `organization.annual_revenue` | Annual Revenue | Custom | Integer (USD) |
| `organization.total_funding` | Total Funding | Custom | If relevant |
| `organization.website_url` | Company Website | Custom | URL |
| `organization.technologies` | Tech Stack | Custom | Array of tool names |
| `enrichment_date` | Last Enriched | Custom | Timestamp of enrichment |
| `enrichment_source` | Enrichment Source | Custom | "Apollo.io" |

### Nutshell Custom Fields Setup

Before the sync works, create these custom fields in Nutshell:

```
Nutshell > Settings > Custom Fields > Contacts:
  - LinkedIn URL (URL type)
  - LinkedIn Headline (Text type)
  - Seniority Level (Dropdown: founder, c_suite, vp, director, manager, individual)
  - Department (Text type)
  - Industry (Text type)
  - Company Size (Number type)
  - Annual Revenue (Currency type)
  - Company Website (URL type)
  - Tech Stack (Text type - comma separated)
  - Last Enriched (Date type)
  - Enrichment Source (Text type)
```

### Nutshell Update API Call

```python
def update_nutshell_contact(contact_id: int, apollo_data: dict):
    """Push enriched data back to Nutshell."""
    person = apollo_data
    org = person.get('organization', {})

    update_payload = {
        "custom_fields": {
            "job_title": person.get('title', ''),
            "linkedin_url": person.get('linkedin_url', ''),
            "linkedin_headline": person.get('headline', ''),
            "seniority_level": person.get('seniority', ''),
            "department": ', '.join(person.get('departments', [])),
            "industry": org.get('industry', ''),
            "company_size": org.get('estimated_num_employees'),
            "annual_revenue": org.get('annual_revenue'),
            "company_website": org.get('website_url', ''),
            "tech_stack": ', '.join(org.get('technologies', [])[:10]),
            "last_enriched": datetime.utcnow().isoformat(),
            "enrichment_source": "Apollo.io"
        }
    }

    # Nutshell API call to update contact
    nutshell_api.edit_contact(contact_id, update_payload)
```

---

## Implementation Approach

### n8n Workflow Design

#### Workflow 1: Real-Time Enrichment (On Contact Creation)

```
[Webhook Trigger: Nutshell contact.created]
    |
    v
[Code Node: Extract identifiers]
    - first_name, last_name, email, company_name
    - Skip if contact already has enrichment_date set
    |
    v
[HTTP Request: Apollo /people/match]
    - Method: POST
    - Headers: x-api-key
    - Body: extracted identifiers
    |
    v
[IF Node: Match found?]
    |-- YES --> [Code Node: Map Apollo fields to Nutshell schema]
    |               |
    |               v
    |           [HTTP Request: Nutshell update contact]
    |               |
    |               v
    |           [Code Node: Log enrichment success]
    |
    |-- NO  --> [Code Node: Tag contact "enrichment-failed"]
                    |
                    v
                [HTTP Request: Nutshell add tag]
```

#### Workflow 2: Nightly Batch Enrichment

```
[Schedule Trigger: Daily at 2:00 AM]
    |
    v
[HTTP Request: Nutshell API - get contacts where enrichment_date is NULL]
    |
    v
[Code Node: Batch into groups of 10]
    |
    v
[Loop: For each batch]
    |
    v
[HTTP Request: Apollo /people/bulk_match]
    - Body: { "details": [batch of 10 contacts] }
    |
    v
[Code Node: Map results + update Nutshell contacts]
    |
    v
[Wait Node: 2 seconds (rate limiting)]
    |
    v
[Next batch...]
```

#### Workflow 3: Periodic Re-Enrichment (Monthly)

```
[Schedule Trigger: 1st of each month at 3:00 AM]
    |
    v
[HTTP Request: Nutshell - contacts where enrichment_date > 30 days ago]
    |
    v
[Same batch enrichment logic as Workflow 2]
```

### Enrichment Decision Logic

Not every contact needs enrichment. Apply these rules:

```python
def should_enrich(contact: dict) -> bool:
    """Determine if a contact needs Apollo enrichment."""

    # Skip if already enriched recently (within 30 days)
    if contact.get('last_enriched'):
        enriched_date = parse(contact['last_enriched'])
        if (datetime.utcnow() - enriched_date).days < 30:
            return False

    # Skip if no identifiers available
    has_email = bool(contact.get('emails'))
    has_name = bool(contact.get('name', {}).get('first'))
    has_company = bool(contact.get('company', {}).get('name'))

    if not has_email and not (has_name and has_company):
        return False  # Not enough data for a reliable match

    return True
```

### Match Confidence Handling

Apollo returns matches but does not provide a confidence score directly.
Implement your own confidence logic:

| Identifiers Provided | Expected Match Quality | Action |
|----------------------|----------------------|--------|
| Email only | High (95%+) | Auto-apply enrichment |
| Name + Company | Medium (70-85%) | Auto-apply, flag for review |
| Name + Domain | Medium (70-85%) | Auto-apply, flag for review |
| Name only | Low (<50%) | Skip or manual review only |
| LinkedIn URL | Very High (99%) | Auto-apply enrichment |

---

## Cost Implications

### Apollo Credit Usage Projection

| Scenario | Contacts/mo | Credits/mo | Plan Needed |
|----------|------------|-----------|-------------|
| Low volume | 30-50 | 30-50 | Free (10,000/mo) |
| Medium volume | 100-200 | 100-200 | Free (10,000/mo) |
| High volume + refresh | 500+ | 500-1,000 | Free (10,000/mo) |

**Steven's projected volume is well within the Free tier.** Apollo's 10,000 free credits/month
would support enriching ~10,000 contacts/month — far more than needed.

### Infrastructure Costs
| Component | Cost | Notes |
|-----------|------|-------|
| n8n workflows | $0 | Self-hosted |
| Nutshell API calls | $0 | Included in subscription |
| Apollo API calls | $0 | Free tier sufficient |
| Supabase logging | Negligible | Enrichment audit log |

**Total incremental cost: $0/month**

### When to Upgrade Apollo
- If revealing personal emails at scale (additional credits per reveal)
- If revealing phone numbers (additional credits + webhook requirement)
- If exceeding 600 API calls/day on Free tier
- If needing advanced filters in People Search

---

## Estimated Build Hours

| Task | Hours |
|------|-------|
| Nutshell custom field setup | 1-2 |
| Apollo API key + test enrichment | 1 |
| n8n Workflow 1: Real-time enrichment | 4-6 |
| n8n Workflow 2: Nightly batch | 4-6 |
| n8n Workflow 3: Monthly refresh | 2-3 |
| Field mapping + data transformation | 2-3 |
| Error handling + logging | 2-3 |
| Testing (match accuracy, edge cases) | 3-4 |
| **Total** | **19-28 hours** |

### Prerequisites
- [ ] Apollo API key (sign up at apollo.io, free tier)
- [ ] Nutshell CRM API credentials
- [ ] Nutshell custom fields created (see field mapping table above)
- [ ] n8n instance with HTTP Request and Code nodes
- [ ] Supabase table for enrichment audit log (optional but recommended)

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Apollo match rate < 70% | Poor data quality | Use email as primary identifier; fallback to name+company |
| Nutshell webhook unreliable | Missed enrichments | Nightly batch catches anything missed by real-time |
| Apollo rate limiting | Delayed batch processing | Implement exponential backoff; spread batches over time |
| Stale Apollo data | Inaccurate enrichment | Monthly re-enrichment cycle; manual review flag |
| Field mapping conflicts | Data overwrite | Only update empty fields; preserve manual edits |

---

## References

- [Apollo People Enrichment API](https://docs.apollo.io/reference/people-enrichment)
- [Apollo Bulk People Enrichment](https://docs.apollo.io/reference/bulk-people-enrichment)
- [Apollo Organization Enrichment](https://docs.apollo.io/reference/organization-enrichment)
- [Apollo Rate Limits](https://docs.apollo.io/reference/rate-limits)
- [Apollo API Pricing](https://docs.apollo.io/docs/api-pricing)
- [Nutshell CRM API Documentation](https://developers.nutshell.com/)
- [Nutshell Zapier Integration](https://zapier.com/apps/nutshell-crm/integrations)

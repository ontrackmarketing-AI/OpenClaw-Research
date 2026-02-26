# GoHighLevel Contact Sync

> How leads flow from discovery and enrichment into GoHighLevel contacts, and how data stays synchronized.

---

## Contact Creation Flow

The standard path from lead discovery to GHL contact:

```
Lead Source (Google Places, form, referral, manual)
  -> Pre-qualification filter (basic checks, save enrichment credits)
  -> Clay enrichment (waterfall: company data, contacts, tech stack, reviews)
  -> Pain scoring (15-signal model, 0-100 score)
  -> Qualification gate (score >= 40 continues, below = disqualified)
  -> Field mapping (enrichment fields -> GHL contact schema)
  -> Deduplication check (search GHL for existing contact by email/phone/domain)
  -> IF new: Create contact in GHL with all mapped fields + tags
  -> IF existing: Update contact with new/changed enrichment data
  -> Pipeline placement (Hot/Warm/Cold based on score tier)
  -> Notification (alert sales rep for Hot leads)
```

---

## Required Fields

### Minimum Fields for Contact Creation

| GHL Field | Source | Required | Notes |
|---|---|---|---|
| `firstName` | Clay enrichment / manual | Yes | Business owner or decision-maker first name |
| `lastName` | Clay enrichment / manual | Yes | Last name |
| `email` | Clay waterfall (Apollo, Hunter, Clearbit) | Yes (preferred) | Primary contact email |
| `phone` | Google Places / Clay | Preferred | Business phone, mobile preferred |
| `companyName` | Google Places / Clay | Yes | Business name |
| `website` | Google Places / Clay | Preferred | Business website URL |
| `source` | Automated from pipeline | Yes | How the lead was found |
| `tags` | Automated from scoring | Yes | Classification tags |

### Extended Fields (Custom Fields in GHL)

| Custom Field | Source | Type | Purpose |
|---|---|---|---|
| `lead_score` | Pain scoring model | Number (0-100) | Overall qualification score |
| `industry` | Google Places category | Single-line text | Business vertical |
| `employee_count` | Clay (LinkedIn/Clearbit) | Number | Company size |
| `annual_revenue` | Clay (estimated) | Number | Revenue estimate |
| `tech_stack` | BuiltWith via Clay | Multi-line text | CMS, analytics, tools used |
| `google_rating` | Google Places | Number | Google review rating (1-5) |
| `review_count` | Google Places | Number | Total Google reviews |
| `has_website` | Automated check | Checkbox | Whether business has a website |
| `website_score` | Automated analysis | Number (0-100) | Website quality score |
| `social_linkedin` | Clay | URL | LinkedIn profile URL |
| `social_facebook` | Clay | URL | Facebook page URL |
| `social_instagram` | Clay | URL | Instagram profile URL |
| `enrichment_date` | Automated timestamp | Date | When data was last enriched |
| `discovery_source` | Pipeline tracking | Dropdown | Google Places, referral, form, cold list |
| `pain_signals` | Pain scoring model | Multi-line text | JSON or comma-separated pain signals detected |
| `competitor_status` | Analysis | Dropdown | No agency, has agency, switching |

---

## Custom Fields Setup in GHL

Before contact sync can populate custom fields, they must exist in GHL.

**Automated setup via API:**
```python
async def ensure_custom_fields(ghl_adapter):
    """Create all required custom fields if they don't exist."""
    existing = await ghl_adapter.list_custom_fields()
    existing_names = {f["name"] for f in existing}

    required_fields = [
        {"name": "lead_score", "dataType": "NUMERICAL", "fieldKey": "lead_score"},
        {"name": "industry", "dataType": "TEXT", "fieldKey": "industry"},
        {"name": "employee_count", "dataType": "NUMERICAL", "fieldKey": "employee_count"},
        {"name": "annual_revenue", "dataType": "NUMERICAL", "fieldKey": "annual_revenue"},
        {"name": "tech_stack", "dataType": "LARGE_TEXT", "fieldKey": "tech_stack"},
        {"name": "google_rating", "dataType": "NUMERICAL", "fieldKey": "google_rating"},
        {"name": "review_count", "dataType": "NUMERICAL", "fieldKey": "review_count"},
        {"name": "website_score", "dataType": "NUMERICAL", "fieldKey": "website_score"},
        {"name": "enrichment_date", "dataType": "DATE", "fieldKey": "enrichment_date"},
        {"name": "pain_signals", "dataType": "LARGE_TEXT", "fieldKey": "pain_signals"},
    ]

    for field in required_fields:
        if field["name"] not in existing_names:
            await ghl_adapter.create_custom_field(field)
            print(f"Created custom field: {field['name']}")
```

---

## Deduplication Strategy

Before creating a new contact, always check for existing records to prevent duplicates.

### Dedup Search Order
1. **Email match** (highest confidence) - Search GHL contacts by email address
2. **Phone match** (high confidence) - Search by phone number (normalize format first)
3. **Company + Location match** (medium confidence) - Business name + city/zip
4. **Domain match** (medium confidence) - Website domain matches existing contact's website

### Dedup Logic
```python
async def find_existing_contact(ghl_adapter, lead_data: dict) -> str | None:
    """Search for existing contact. Returns contact ID if found, None if new."""

    # Priority 1: Email match
    if lead_data.get("email"):
        results = await ghl_adapter.search_contacts(
            query=lead_data["email"],
            field="email"
        )
        if results:
            return results[0]["id"]

    # Priority 2: Phone match
    if lead_data.get("phone"):
        normalized_phone = normalize_phone(lead_data["phone"])
        results = await ghl_adapter.search_contacts(
            query=normalized_phone,
            field="phone"
        )
        if results:
            return results[0]["id"]

    # Priority 3: Company name + location
    if lead_data.get("companyName") and lead_data.get("city"):
        results = await ghl_adapter.search_contacts(
            query=lead_data["companyName"]
        )
        for r in results:
            if r.get("city", "").lower() == lead_data["city"].lower():
                return r["id"]

    return None  # New contact

async def create_or_update_contact(ghl_adapter, lead_data: dict):
    """Create new contact or update existing one."""
    existing_id = await find_existing_contact(ghl_adapter, lead_data)

    if existing_id:
        await ghl_adapter.update_contact(existing_id, lead_data)
        return {"action": "updated", "contact_id": existing_id}
    else:
        result = await ghl_adapter.create_contact(lead_data)
        return {"action": "created", "contact_id": result["id"]}
```

---

## Tags Strategy

Tags are the primary mechanism for segmentation and automation in GHL.

### Tag Categories

**Source Tags** (how the lead was found):
- `source:google-places` - Discovered via Google Places scraping
- `source:form-submission` - Submitted a form on landing page
- `source:referral` - Referred by existing client
- `source:cold-list` - From purchased or scraped list
- `source:linkedin` - Found via LinkedIn outreach

**Industry Tags** (business vertical):
- `industry:dental` - Dental practices
- `industry:hvac` - HVAC companies
- `industry:legal` - Law firms
- `industry:restaurant` - Restaurants
- `industry:medical` - Medical practices
- `industry:home-services` - Plumbing, electrical, etc.

**Score Tags** (qualification tier):
- `score:hot` - Score 80-100, immediate outreach
- `score:warm` - Score 60-79, nurture sequence
- `score:cold` - Score 40-59, long-term nurture
- `score:disqualified` - Score 0-39, do not pursue

**Status Tags** (lifecycle stage):
- `status:new` - Just created, not contacted
- `status:contacted` - First outreach sent
- `status:engaged` - Responded positively
- `status:meeting-booked` - Discovery call scheduled
- `status:proposal-sent` - Proposal delivered
- `status:won` - Closed deal
- `status:lost` - Deal lost

**Pain Signal Tags** (specific pain points detected):
- `pain:no-website` - Business has no website
- `pain:slow-website` - Website loads slowly
- `pain:no-reviews` - Few or no online reviews
- `pain:bad-reviews` - Low average rating
- `pain:no-social` - Missing social media presence
- `pain:outdated-design` - Website looks outdated
- `pain:no-mobile` - Not mobile-friendly
- `pain:no-seo` - Not ranking for relevant keywords
- `pain:no-ads` - Not running any online ads

---

## Enrichment Data Mapping

### Clay Response -> GHL Contact Fields

```python
FIELD_MAPPING = {
    # Clay field path -> GHL field name
    "company.name": "companyName",
    "company.domain": "website",
    "company.industry": "customField.industry",
    "company.employee_count": "customField.employee_count",
    "company.estimated_revenue": "customField.annual_revenue",
    "company.phone": "phone",
    "company.address.street": "address1",
    "company.address.city": "city",
    "company.address.state": "state",
    "company.address.zip": "postalCode",
    "person.first_name": "firstName",
    "person.last_name": "lastName",
    "person.email": "email",
    "person.phone": "phone",  # Override with personal phone if available
    "person.linkedin_url": "customField.social_linkedin",
    "tech_stack.cms": "customField.tech_stack",
    "google_reviews.rating": "customField.google_rating",
    "google_reviews.count": "customField.review_count",
}

def map_enrichment_to_ghl(enrichment_data: dict) -> dict:
    """Transform Clay enrichment response to GHL contact payload."""
    ghl_contact = {}
    custom_fields = {}

    for clay_path, ghl_field in FIELD_MAPPING.items():
        value = get_nested(enrichment_data, clay_path)
        if value is None:
            continue

        if ghl_field.startswith("customField."):
            custom_field_key = ghl_field.split(".", 1)[1]
            custom_fields[custom_field_key] = value
        else:
            ghl_contact[ghl_field] = value

    if custom_fields:
        ghl_contact["customFields"] = custom_fields

    return ghl_contact
```

---

## Bulk Import

For importing CSV lists or batch-processing discovered leads:

```python
async def bulk_import_leads(ghl_adapter, leads: list[dict], batch_size: int = 10):
    """Import leads in batches with dedup and rate limiting."""
    results = {"created": 0, "updated": 0, "failed": 0, "errors": []}

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i + batch_size]

        for lead in batch:
            try:
                result = await create_or_update_contact(ghl_adapter, lead)
                results[result["action"]] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"lead": lead.get("email", "unknown"), "error": str(e)})

        # Rate limiting: GHL API allows ~100 requests/minute per location
        await asyncio.sleep(1)  # Pause between batches

    return results
```

**Rate limits:** GHL API typically allows ~100 requests per minute per location. For bulk imports of 1000+ contacts, implement proper rate limiting and progress tracking.

---

## Two-Way Sync

Changes in GHL should be reflected in OpenClaw's memory/database:

### GHL -> OpenClaw (via webhooks)
- Contact updated in GHL -> webhook fires -> OpenClaw updates local record
- Opportunity stage changed -> webhook fires -> OpenClaw updates pipeline state
- See `webhook-setup.md` for details

### OpenClaw -> GHL (via API)
- OpenClaw enriches data -> updates GHL contact via API
- OpenClaw scores lead -> updates lead_score custom field + score tag
- OpenClaw detects stage change trigger -> moves opportunity in GHL

### Sync Conflict Resolution
- **Last write wins** for most fields (timestamp-based)
- **GHL is source of truth** for: deal stage, appointment status, conversation history
- **OpenClaw is source of truth** for: enrichment data, lead score, pain signals

---

## Error Handling

| Scenario | Handling |
|---|---|
| Contact creation fails (400) | Log validation error, fix data, retry once |
| Duplicate detected after creation | Merge contacts in GHL, update OpenClaw reference |
| API rate limit (429) | Queue remaining contacts, retry after cooldown |
| Network timeout | Retry with exponential backoff (3 attempts) |
| Invalid custom field value | Coerce to correct type, skip field if impossible |
| Email validation fails | Create contact without email, tag as `needs:email` |
| GHL server error (500) | Retry up to 3 times, alert on persistent failure |

---

## RESEARCH GAPS

- [ ] Confirm exact GHL API rate limits for contact operations
- [ ] Determine if GHL supports bulk contact creation (single API call for multiple contacts)
- [ ] Verify custom field creation API works with your API key permissions
- [ ] Test dedup search accuracy with various query formats
- [ ] Determine how GHL handles custom field updates (merge vs overwrite)

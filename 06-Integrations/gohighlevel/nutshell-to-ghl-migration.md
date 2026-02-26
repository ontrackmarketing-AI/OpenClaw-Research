# Nutshell CRM to GoHighLevel Migration Plan

## Overview

This document details the migration plan for transferring 14,000+ contacts, deals, pipeline configurations, activities, and associated data from Nutshell CRM to GoHighLevel (GHL). The migration must preserve data integrity, maintain business continuity during transition, and establish GHL as the unified CRM platform for SW Recovery Services.

**Migration scope**:
- 14,000+ contacts (companies and people)
- Active deals and deal history
- Pipeline stages and configurations
- Custom fields and tags
- Activities and notes (where exportable)
- Email templates and sequences

**Key constraint**: Activities (calls, meetings, tasks) can only be created manually in Nutshell -- they are not included in CSV exports. Historical activity data must be migrated via API or accepted as a data loss trade-off.

---

## API / Integration Details

### Nutshell CRM Data Export Options

**Option 1: CSV Export (Simplest)**
- Available to all Nutshell users
- Export contacts (companies and people) as CSV files
- Export leads/deals with custom report filtering
- Saved lists can be exported directly
- Activities (calls, meetings, notes) are NOT included in CSV exports

**Option 2: Nutshell REST API (Most Complete)**
- Available on Enterprise plan ($79/user/month billed annually)
- Full programmatic access to all data objects
- Endpoints for contacts, leads, activities, notes, custom fields
- Developer documentation at developers.nutshell.com
- Read-only SQL access also available on Enterprise plan

**Option 3: JSON-RPC API (Legacy)**
- Available on all plans
- Older API format, still functional
- Can access contacts, leads, and some activity data
- Less documented than REST API

**Option 4: Zapier/Webhook Bridge**
- Available on all plans via Zapier integration
- Can trigger on Nutshell events and push to GHL
- Best for ongoing sync, not bulk migration
- Rate limited for large data sets

### Nutshell Data Objects

| Object | CSV Export | REST API | Notes |
|--------|-----------|----------|-------|
| Companies (Accounts) | Yes | Yes | Name, address, phone, web, custom fields |
| People (Contacts) | Yes | Yes | Name, email, phone, company association |
| Leads (Deals) | Yes | Yes | Name, value, stage, assignee, dates |
| Pipeline Stages | No | Yes | Stage names, order, probability |
| Activities | No | Yes (Enterprise) | Calls, meetings, tasks, emails |
| Notes | Partial | Yes (Enterprise) | Attached to contacts/leads |
| Custom Fields | Yes (values) | Yes | Field definitions + values |
| Tags | Yes | Yes | Contact/lead tags |
| Email Templates | No | Limited | Manual recreation needed |
| Automations | No | No | Manual recreation in GHL |
| Files/Attachments | No | Yes (Enterprise) | Manual download may be needed |

### GoHighLevel Import Capabilities

**CSV Import**
- File must be CSV format, under 50MB
- Import contacts with all standard and custom fields
- Import opportunities (deals) simultaneously with contacts
- Deduplication: Contact ID > Email > Phone matching order
- Custom field values can be mapped during import
- Tags can be assigned during import

**GHL API**
- RESTful API for programmatic data management
- Endpoints for contacts, opportunities, pipelines, custom fields
- Bulk operations supported with rate limiting
- API documentation at developers.gohighlevel.com

**GHL Standard Fields**

| Field | Type | Notes |
|-------|------|-------|
| First Name | Text | Required |
| Last Name | Text | Required |
| Email | Email | Primary identifier |
| Phone | Phone | Secondary identifier |
| Company Name | Text | Company association |
| Address (Street, City, State, Zip) | Text | Full address support |
| Tags | Multi-select | Comma-separated in CSV |
| Source | Text | Lead source tracking |
| Date Added | Date | Auto or manual |
| Assigned To | User | GHL user mapping |

**GHL Opportunity (Deal) Fields**

| Field | Type | Notes |
|-------|------|-------|
| Opportunity Name | Text | Deal name |
| Pipeline | Reference | Must exist before import |
| Stage | Reference | Must exist within pipeline |
| Monetary Value | Number | Deal value |
| Status | Enum | open, won, lost, abandoned |
| Contact | Reference | Linked via email/phone |
| Assigned To | User | Sales rep assignment |

---

## Field Mapping Matrix

### Contact Field Mapping

| Nutshell Field | GHL Field | Transform | Notes |
|---------------|-----------|-----------|-------|
| Company Name | Company Name | Direct | |
| First Name | First Name | Direct | |
| Last Name | Last Name | Direct | |
| Email (primary) | Email | Direct | Primary identifier for dedup |
| Phone (primary) | Phone | Format to E.164 | Strip non-numeric chars |
| Phone (secondary) | Additional Phone | Custom field | |
| Street Address | Address 1 | Direct | |
| City | City | Direct | |
| State | State | Direct | |
| Zip | Postal Code | Direct | |
| Job Title | Custom: Job Title | Custom field | GHL lacks native job title |
| Industry | Custom: Industry | Custom field | |
| Website | Website | Direct | |
| Owner/Assignee | Assigned To | Map users | Nutshell user --> GHL user |
| Tags | Tags | Comma-separated | |
| Created Date | Date Added | Format: YYYY-MM-DD | |
| Last Contacted | Custom: Last Contacted | Custom field | |
| Lead Status | Tags | Prefix: "Status: {value}" | |
| Custom Field 1-N | Custom Field 1-N | Create matching GHL fields | |

### Deal/Opportunity Field Mapping

| Nutshell Field | GHL Field | Transform | Notes |
|---------------|-----------|-----------|-------|
| Lead Name | Opportunity Name | Direct | |
| Lead Value | Monetary Value | Numeric only | Strip $ and commas |
| Pipeline | Pipeline | Create matching pipeline | Must exist before import |
| Stage | Stage | Map to GHL stages | Must exist within pipeline |
| Assigned To | Assigned To | Map users | |
| Close Date | Custom: Close Date | Format date | |
| Created Date | Custom: Created Date | Format date | |
| Win Probability | Custom: Probability | Percentage | |
| Status (Won/Lost/Open) | Status | Map values | open/won/lost/abandoned |
| Source | Source | Direct | |
| Description | Custom: Description | Text | |
| Contact Email | Contact (link) | Email match | Links deal to contact |

### User Mapping

| Nutshell User | GHL User | Notes |
|--------------|----------|-------|
| Steven [Last Name] | Steven [Last Name] | Primary owner |
| [Team Member 1] | [Team Member 1] | Create in GHL first |
| [Team Member 2] | [Team Member 2] | Create in GHL first |
| Unassigned | Default user | Catch-all assignment |

---

## Implementation Approach

### Pre-Migration (Week 1-2)

#### Step 1: Audit Nutshell Data

1. **Count records**
   - Total companies
   - Total people (contacts)
   - Total active leads/deals
   - Total closed leads (won + lost)
   - Total activities (calls, meetings, notes)
   - Total custom fields in use

2. **Data quality assessment**
   - Identify duplicate contacts (same email, different records)
   - Flag incomplete records (missing email/phone)
   - Review custom field usage (which ones are actually populated)
   - Identify orphaned records (contacts with no deals, deals with no contacts)
   - Check for data inconsistencies (formatting, invalid emails)

3. **Clean Nutshell data before export**
   - Merge duplicate contacts
   - Standardize phone number formats
   - Fill in missing critical fields where possible
   - Archive truly inactive records (no activity > 2 years)
   - Document any data that will be intentionally left behind

#### Step 2: Prepare GHL Environment

1. **Create GHL sub-account**
   - Set up SW Recovery Services sub-account
   - Configure business details, timezone, branding

2. **Create custom fields in GHL**
   - Mirror all Nutshell custom fields that will be imported
   - Create additional fields for metadata (Nutshell ID, migration date)
   - Field types must match (text, number, date, dropdown)

3. **Build pipelines in GHL**
   - Recreate Nutshell pipeline stages in exact order
   - Map stage names (can rename, but preserve logic)
   - Set stage probabilities if used
   - Create any additional pipelines needed for GHL workflows

4. **Create user accounts**
   - Set up all team members in GHL
   - Assign roles and permissions
   - Document user mapping for import

### Migration Execution (Week 3)

#### Step 3: Export from Nutshell

**CSV Export Process**:
1. Navigate to Nutshell > Companies > select all > Export CSV
2. Navigate to Nutshell > People > select all > Export CSV
3. Navigate to Nutshell > Reporting > customize lead report > Download lead list
4. For each export, verify column headers match expected fields
5. Save exports with clear naming: `nutshell_companies_YYYYMMDD.csv`, etc.

**API Export Process (Enterprise plan)**:
```python
# Pseudocode for Nutshell REST API export
import requests

BASE_URL = "https://app.nutshell.com/api/v1"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Export all contacts
contacts = []
page = 1
while True:
    response = requests.get(
        f"{BASE_URL}/contacts",
        headers=headers,
        params={"page": page, "per_page": 100}
    )
    data = response.json()
    contacts.extend(data["contacts"])
    if not data["has_more"]:
        break
    page += 1

# Export all leads/deals
leads = []
page = 1
while True:
    response = requests.get(
        f"{BASE_URL}/leads",
        headers=headers,
        params={"page": page, "per_page": 100}
    )
    data = response.json()
    leads.extend(data["leads"])
    if not data["has_more"]:
        break
    page += 1

# Export activities (Enterprise only)
activities = []
for contact in contacts:
    response = requests.get(
        f"{BASE_URL}/contacts/{contact['id']}/activities",
        headers=headers
    )
    activities.extend(response.json()["activities"])
```

#### Step 4: Transform Data

1. **Contact transformation**
   ```python
   # Transform Nutshell CSV to GHL import format
   import pandas as pd

   df = pd.read_csv("nutshell_contacts_export.csv")

   # Rename columns to match GHL
   column_mapping = {
       "First Name": "firstName",
       "Last Name": "lastName",
       "Email": "email",
       "Phone": "phone",
       "Company": "companyName",
       "Street": "address1",
       "City": "city",
       "State": "state",
       "Zip": "postalCode",
       # ... custom fields
   }
   df = df.rename(columns=column_mapping)

   # Format phone numbers
   df["phone"] = df["phone"].apply(format_phone_e164)

   # Add migration metadata
   df["tags"] = df["tags"].apply(
       lambda x: f"{x},migrated-from-nutshell" if x else "migrated-from-nutshell"
   )

   df.to_csv("ghl_contact_import.csv", index=False)
   ```

2. **Deal transformation**
   - Map Nutshell pipeline stages to GHL pipeline stages
   - Format monetary values (remove $, commas)
   - Map status values (Nutshell "Won" --> GHL "won")
   - Link deals to contacts via email address
   - Add "migrated-from-nutshell" tag

3. **Validation**
   - Verify row counts match expected totals
   - Spot-check 20-30 records across all fields
   - Validate email format compliance
   - Verify phone number formatting
   - Check custom field value mapping

#### Step 5: Import to GHL

1. **Import contacts first**
   - Upload transformed CSV to GHL Import tool
   - Map columns to GHL fields
   - Set deduplication rule (Email > Phone)
   - Run import in batches of 5,000 (to monitor for errors)
   - Verify imported count matches expected count
   - Spot-check 20 random records

2. **Import opportunities/deals**
   - Ensure pipelines and stages are created first
   - Upload deal CSV with contact email for linking
   - Map pipeline and stage columns
   - Verify deal-to-contact associations
   - Check pipeline view for correct staging

3. **Import activities (if available via API)**
   - Use GHL API to create notes on contacts
   - Include call logs, meeting notes, email history
   - Timestamp all activities with original dates
   - This is the most time-consuming step for large datasets

### Post-Migration Validation (Week 4)

#### Step 6: Verification

| Check | Method | Expected Result |
|-------|--------|----------------|
| Contact count | GHL Contacts > count | Match Nutshell total (minus intentional exclusions) |
| Deal count | GHL Opportunities > count | Match Nutshell lead total |
| Pipeline stages | GHL Pipelines > review | All stages present in correct order |
| Custom fields | Random sample of 50 | Values match Nutshell originals |
| Deal values | Sum all deal values | Total matches Nutshell pipeline value |
| User assignments | Filter by assignee | Correct user mapping |
| Tags | Filter by "migrated-from-nutshell" | All imported records tagged |
| Duplicate check | GHL dedup report | No unexpected duplicates |

#### Step 7: Parallel Running Period

**Duration**: 2-4 weeks of parallel operation

| Week | Nutshell | GHL | Team Action |
|------|---------|-----|-------------|
| Week 1 | Primary (read/write) | Secondary (read only) | Verify data in both systems |
| Week 2 | Primary (read/write) | Shadow (test workflows) | Test GHL automations |
| Week 3 | Read only | Primary (read/write) | Team switches to GHL |
| Week 4 | Archive | Primary | Full GHL operation |

**During parallel period**:
- Any new contacts/deals entered in both systems
- Team can compare data between systems
- Automations tested in GHL before going live
- Rollback plan: revert to Nutshell if critical issues found

### Cutover (End of Week 4)

#### Step 8: Final Cutover

1. **Final sync**: Export any new Nutshell records created during parallel period
2. **Import final delta**: Add new records to GHL
3. **Activate GHL automations**: Turn on workflows, sequences, notifications
4. **Deactivate Nutshell**: Set to read-only or suspend account
5. **Team announcement**: Communicate that GHL is now the official CRM
6. **Support period**: 2 weeks of high-touch support for team questions
7. **Nutshell archival**: Maintain Nutshell access for 90 days for reference

---

## Risk Mitigation

### Known Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during export | High | Export multiple times, verify counts, keep backups |
| Activity history not exportable (CSV) | Medium | Use API if on Enterprise plan, or accept partial history |
| Custom field mapping errors | Medium | Thorough pre-mapping, spot-check samples |
| Team adoption resistance | Medium | Training, parallel period, feedback channels |
| Duplicate records in GHL | Low-Medium | Clean data before import, use dedup settings |
| Pipeline stage mismatch | Low | Pre-create stages, validate mapping |
| Automation failures in GHL | Medium | Test in parallel period before cutover |
| Phone number formatting | Low | E.164 standardization in transform step |

### Rollback Plan

If critical issues are discovered post-cutover:
1. Nutshell remains accessible (read-only) for 90 days
2. GHL export to CSV is available for reverse migration
3. Any new GHL records can be exported and imported back to Nutshell
4. Decision to rollback must be made within 30 days of cutover

---

## Cost Implications

### Migration Costs

| Item | Cost | Notes |
|------|------|-------|
| Nutshell Enterprise (if API needed) | $79/user/month | Only if currently on lower plan |
| GHL subscription | Already active | Assuming GHL is already in use |
| Data transformation tools | $0 | Python/pandas (free) |
| Zapier (if used for sync) | $20-$70/month | During parallel period only |
| Professional migration service | $2,000-$5,000 | Optional, if outsourcing |

### Ongoing Cost Savings

| Item | Nutshell Cost | GHL Cost | Savings |
|------|-------------|----------|---------|
| CRM platform | $42-$79/user/month | Included in GHL | $42-$79/user/month |
| Email marketing | Separate tool | Included in GHL | Varies |
| SMS/calling | Separate tool | Included in GHL | Varies |
| Automation | Limited in Nutshell | Included in GHL | Significant |
| Forms/funnels | Separate tool | Included in GHL | Varies |

**Estimated annual savings**: $5,000-$15,000+ by consolidating tools into GHL (varies based on current Nutshell plan and other tools being replaced).

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Nutshell data audit and cleanup | 6-8 | Duplicates, formatting, completeness |
| GHL environment setup | 4-6 | Custom fields, pipelines, users |
| Field mapping documentation | 3-4 | Complete mapping matrix |
| Export from Nutshell | 3-4 | CSV + API exports, verification |
| Data transformation scripts | 6-8 | Python scripts, format conversion |
| Import to GHL (contacts) | 3-4 | Batch import, verification |
| Import to GHL (deals/opportunities) | 3-4 | Pipeline linking, verification |
| Activity migration (if API available) | 8-12 | Most time-intensive step |
| Post-migration verification | 4-6 | Spot checks, count validation |
| Parallel running oversight (2-4 weeks) | 8-12 | Monitoring, issue resolution |
| Team training on GHL | 4-6 | Workflow walkthroughs, Q&A |
| Final cutover execution | 3-4 | Last sync, activation, deactivation |
| Post-cutover support (2 weeks) | 4-6 | Team questions, issue resolution |
| **Total** | **59-84 hours** | Over 4-6 week migration period |

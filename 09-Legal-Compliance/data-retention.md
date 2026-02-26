# Data Retention Policy

## Overview

A data retention policy defines how long you keep different types of data, when and how you delete it, and how you handle deletion requests from data subjects. This is not just a legal requirement under GDPR, CCPA, and TDPSA -- it is also good operational hygiene. Keeping data longer than necessary increases your attack surface, storage costs, and liability.

This document defines retention periods for every data category in your OpenClaw system, the deletion procedures, and the practical implementation using your existing tool stack.

---

## 1. Data Categories and Retention Periods

### Lead Data (Enriched Business Information)

**What it includes:** Business contact names, email addresses, phone numbers, job titles, company names, company revenue, employee counts, industry classifications, website URLs, enrichment metadata from Clay.

| Status | Retention Period | Action at Expiry |
|--------|-----------------|------------------|
| Active lead (in outreach sequence or pipeline) | Retain indefinitely while active | N/A -- lead is being worked |
| Stale lead (no engagement in 12 months) | 12 months from last activity | Move to archive |
| Archived lead | 24 months from archive date | Permanently delete |
| Opted-out lead | Delete active data immediately; retain in suppression list indefinitely | Remove from all active systems; keep email in suppression list to prevent re-contact |

**Rationale:** 12 months of active retention gives you ample time to work leads through your pipeline. The 24-month archive allows for potential re-engagement campaigns or reference. After 36 months total (12 active + 24 archive), data is likely too stale to be useful.

**Storage locations:** Supabase (primary lead database), Airtable (campaign tracking), GHL (CRM contacts), Clay (enrichment results).

### Client Data (Your Agency's Client Information)

**What it includes:** Client business information, contracts, invoices, project deliverables, communication records, login credentials, campaign performance data.

| Status | Retention Period | Action at Expiry |
|--------|-----------------|------------------|
| Active client | Retain for duration of relationship | N/A |
| Former client | 3 years after end of relationship | Permanently delete non-essential data; retain financial records per tax requirements |
| Financial records (invoices, payments) | 7 years (IRS requirement) | Delete after 7 years |

**Rationale:** The 3-year post-relationship retention covers potential contract disputes (Texas statute of limitations for breach of contract is 4 years; 3 years provides reasonable coverage while allowing for any claims to surface). Financial records must be kept for 7 years per IRS requirements.

**Storage locations:** GHL (client sub-accounts), Airtable (project management), cloud storage (contracts, deliverables).

### Communication Logs (Emails and Messages)

**What it includes:** Outreach emails sent and received, LinkedIn messages, SMS messages, chat logs, email open/click tracking data.

| Type | Retention Period | Action at Expiry |
|------|-----------------|------------------|
| Outreach emails (sent) | 6 months | Delete email content; retain aggregate campaign metrics |
| Outreach emails (received replies) | 12 months | Delete after 12 months unless part of active deal |
| Email tracking data (opens, clicks) | 6 months | Delete granular tracking; retain aggregate stats |
| SMS messages | 6 months | Delete |
| LinkedIn messages | N/A (stored on LinkedIn, not in your system) | Do not export or store locally |

**Rationale:** Communication logs are voluminous and contain personal data. Six months is sufficient for campaign analysis and responding to any complaints. Aggregate metrics (open rates, click rates, response rates) are retained separately and do not contain personal data.

**Storage locations:** Email sending platform (Instantly, Smartlead, etc.), GHL (conversation logs), Supabase (tracking data).

### Agent Session Logs

**What it includes:** Logs of AI agent interactions, prompts sent to Claude, responses received, tool call records, error logs, debugging information.

| Type | Retention Period | Action at Expiry |
|------|-----------------|------------------|
| Agent session logs (detailed) | 30 days | Delete |
| Agent error logs | 90 days | Delete |
| Agent performance metrics (aggregate) | 12 months | Delete |

**Rationale:** Agent session logs can be extremely voluminous (each agent session may generate thousands of tokens of log data). Thirty days is sufficient for debugging and performance analysis. Error logs are retained longer (90 days) to identify recurring issues. Aggregate metrics (average response time, success rates, token usage) are retained for trend analysis.

**Storage locations:** Supabase (session logs), log files (if any), monitoring dashboards.

### Memory Files

**What it includes:** Agent memory documents, knowledge base entries, learned preferences, contextual information accumulated over time.

| Type | Retention Period | Action at Expiry |
|------|-----------------|------------------|
| Core memory files (agent identity, preferences, procedures) | Indefinite | Compact periodically (quarterly) |
| Episodic memory (session summaries, interaction context) | Indefinite, but compact quarterly | Remove entries older than 6 months that have not been referenced |
| Learned facts about contacts/companies | Follows lead data retention (12 months active) | Delete when associated lead data is deleted |

**Rationale:** Memory files are the accumulated knowledge of your AI agent system. Unlike transactional data, they improve with age as the system learns. However, they should be compacted periodically to remove outdated information, reduce file size, and maintain relevance.

**Compaction process:**
1. Review memory files quarterly.
2. Remove entries that reference contacts/companies no longer in your system.
3. Consolidate redundant or overlapping entries.
4. Remove specific personal data from memory entries (generalize where possible).
5. Document compaction date and what was removed.

**Storage locations:** File system (markdown memory files), Supabase (if using database-backed memory).

### Competitive Intelligence

**What it includes:** Competitor analysis, market research, pricing intelligence, technology stack data, service offering comparisons.

| Type | Retention Period | Action at Expiry |
|------|-----------------|------------------|
| Active competitive intelligence | 12 months | Archive or update |
| Archived competitive snapshots | 24 months from archive date | Delete |
| Market research reports | 24 months | Delete |

**Rationale:** Competitive intelligence has a limited shelf life. Market conditions, pricing, and competitor offerings change frequently. Data older than 12 months is likely misleading rather than helpful. Archived snapshots are retained for trend analysis but deleted after 24 months.

**Storage locations:** Airtable (competitive tracking), Supabase (research data), file system (reports).

### Analytics Data

**What it includes:** Campaign performance analytics, website analytics, pipeline metrics, revenue attribution, conversion rates, ROI calculations.

| Type | Retention Period | Action at Expiry |
|------|-----------------|------------------|
| Granular analytics (per-contact, per-email) | 6 months | Aggregate and delete granular data |
| Aggregate analytics (campaign-level, monthly) | 24 months | Delete |
| Financial analytics (revenue, costs, ROI) | 7 years (aligns with financial records) | Delete |

**Rationale:** Granular analytics contain personal data (which contact opened which email) and should be retained only as long as needed for campaign optimization. Aggregate analytics are useful for trend analysis and reporting. Financial analytics align with the 7-year tax record retention requirement.

**Storage locations:** GHL (campaign analytics), Supabase (custom analytics), Google Analytics (website), reporting dashboards.

---

## 2. Deletion Procedures

### Automated Retention Enforcement

Build an automated workflow that runs monthly to identify and delete expired data. This is your primary retention enforcement mechanism.

#### n8n Workflow Design: Monthly Retention Enforcement

```
Trigger: Schedule (1st of every month, 2:00 AM)
    |
    v
Step 1: Query Supabase for leads with last_activity_date > 12 months ago
    |
    v
Step 2: For each stale lead:
    a. Check if lead is in an active pipeline stage --> if yes, skip
    b. Move to archive table in Supabase (set archived_date = today)
    c. Update status in GHL to "Archived"
    d. Log the archival
    |
    v
Step 3: Query Supabase archive table for records with archived_date > 24 months ago
    |
    v
Step 4: For each expired archived lead:
    a. Delete from Supabase archive table
    b. Delete from GHL (or anonymize)
    c. Delete from Airtable (if present)
    d. Check Clay for any stored data (if applicable)
    e. Add email to suppression list (to prevent re-collection)
    f. Log the deletion
    |
    v
Step 5: Query communication logs older than 6 months
    |
    v
Step 6: Delete expired communication logs
    |
    v
Step 7: Query agent session logs older than 30 days
    |
    v
Step 8: Delete expired session logs
    |
    v
Step 9: Generate retention enforcement report
    a. Number of leads archived
    b. Number of leads permanently deleted
    c. Number of communication logs deleted
    d. Number of session logs deleted
    e. Any errors encountered
    |
    v
Step 10: Send report to admin (email or Slack notification)
```

#### Implementation Notes

- **Supabase queries:** Use SQL with date arithmetic to identify expired records efficiently.
  ```sql
  -- Find stale leads (no activity in 12 months)
  SELECT * FROM leads
  WHERE last_activity_date < NOW() - INTERVAL '12 months'
  AND status NOT IN ('active_pipeline', 'customer');

  -- Find expired archived leads
  SELECT * FROM leads_archive
  WHERE archived_date < NOW() - INTERVAL '24 months';
  ```

- **GHL deletion:** Use the GHL API to delete or anonymize contacts. If full deletion is not supported, overwrite personal data fields with placeholder values.

- **Airtable cleanup:** Use Airtable API to find and delete matching records. Match by email address or internal ID.

- **Suppression list:** Maintain a permanent suppression list (just email addresses) in Supabase. This list is checked before any new lead is added to the system. It prevents you from re-collecting and re-contacting deleted contacts.

### Manual Deletion (On Request)

When a data subject requests deletion of their data (under GDPR, CCPA, or TDPSA), follow this process:

#### Step-by-Step Deletion Request Process

**Step 1: Receive and Acknowledge (Within 48 hours)**

- Log the request in your deletion request tracker (Airtable or Supabase table).
- Record: requester name, email, date of request, source of request (email, web form, phone), applicable law (GDPR, CCPA, TDPSA).
- Send acknowledgment email to the requester confirming receipt and expected timeline (30 days).

**Step 2: Verify Identity (Within 5 business days)**

- Verify the requester is who they claim to be. For B2B contacts, this is usually straightforward (the request comes from the same email address you have on file).
- If you cannot verify identity, request additional information (but do not request more data than necessary for verification).

**Step 3: Search All Systems (Within 10 business days)**

Search for the data subject's information across all storage locations:

| System | Search Method | Data to Look For |
|--------|-------------|-----------------|
| Supabase | SQL query by email, name, phone | Lead records, analytics, logs |
| GHL | Contact search by email | Contact record, conversation logs, pipeline data |
| Airtable | Search by email/name | Campaign records, tracking data |
| Email platform | Search by email | Send history, tracking data |
| Memory files | Text search for name/email/company | Any references in agent memory |
| File system | Grep for email/name | Any files containing their data |
| Backups | Note for future backup purge | Flag for deletion in next backup rotation |

**Step 4: Delete from All Active Systems (Within 20 business days)**

- Delete or anonymize the contact in every system identified in Step 3.
- For systems that do not support deletion, overwrite personal data fields with "[DELETED]" or similar placeholder.
- Remove references from memory files.
- Add email to suppression list.

**Step 5: Confirm Deletion (Within 30 days of request)**

- Send confirmation to the requester that their data has been deleted from all active systems.
- Note any exceptions (e.g., data retained in backups that will be purged on next rotation, financial records retained for legal compliance).

**Step 6: Log Completion**

- Update the deletion request tracker with:
  - Date of completion.
  - Systems from which data was deleted.
  - Any data retained and the legal basis for retention.
  - Confirmation sent to requester (date and method).

### Cascading Deletion

When a lead is deleted (either by retention policy or by request), the deletion must cascade across all systems. This is critical because your data exists in multiple places.

**Cascading deletion checklist:**

```
[ ] Supabase: Delete lead record from leads table
[ ] Supabase: Delete from leads_archive table (if archived)
[ ] Supabase: Delete associated analytics/tracking records
[ ] Supabase: Delete from any vector embeddings (if using pgvector for RAG)
[ ] GHL: Delete contact record
[ ] GHL: Delete associated conversations
[ ] GHL: Delete from any workflows/automations
[ ] Airtable: Delete from any tables containing this contact
[ ] Email platform: Delete from contact lists and send history
[ ] Clay: Check for any stored enrichment data (usually transient)
[ ] Memory files: Search and remove any references
[ ] Agent session logs: Search and remove any references
[ ] Suppression list: ADD email to suppression list (to prevent re-collection)
```

---

## 3. Backup Considerations

### The Backup Problem

When you delete data from active systems, that data may still exist in backups. This creates a tension between data retention compliance and disaster recovery.

### Acceptable Backup Retention

Under GDPR, CCPA, and TDPSA, it is generally acceptable to retain deleted data in backups for a reasonable period, provided:

1. The backup retention period is defined and documented (e.g., 90 days).
2. Backups are encrypted and access-controlled.
3. You do not restore deleted data from backups (unless the entire system needs to be restored, in which case you must re-execute deletions after restoration).
4. You inform data subjects that their data may persist in backups for the defined period.

### Recommended Backup Retention

| System | Backup Frequency | Backup Retention |
|--------|-----------------|------------------|
| Supabase | Daily (automatic on paid plans) | 30 days (Supabase default) |
| GHL | Managed by GHL | Per GHL's retention policy |
| Airtable | Snapshot (manual or automated) | 30 days |
| File system (memory files, configs) | Weekly | 90 days |

### Post-Restoration Procedure

If you ever need to restore from a backup:

1. Restore the backup.
2. Check the deletion request log for any deletions that occurred after the backup date.
3. Re-execute those deletions.
4. Check the suppression list and remove any contacts that are on it from the restored data.

---

## 4. Data Inventory

Maintain a living data inventory document that maps every category of personal data to its storage location, purpose, legal basis, and retention period. This is required by GDPR (Article 30) and is a best practice under all privacy laws.

### Data Inventory Template

| Data Category | Data Elements | Storage Location(s) | Purpose | Legal Basis | Retention Period | Deletion Method |
|--------------|---------------|---------------------|---------|------------|-----------------|-----------------|
| Lead contacts | Name, email, phone, title | Supabase, GHL, Airtable | B2B outreach | Legitimate interest (GDPR), CAN-SPAM compliance | 12mo active + 24mo archive | Automated + manual |
| Company data | Name, revenue, size, industry, website | Supabase, Clay | Lead enrichment | Legitimate interest | Follows lead retention | Automated |
| Email communications | Email content, metadata, tracking | Email platform, GHL | Outreach campaigns | CAN-SPAM, legitimate interest | 6 months | Automated |
| Agent session logs | Prompts, responses, tool calls | Supabase, log files | Debugging, improvement | Internal operations | 30 days | Automated |
| Client data | Contracts, invoices, projects | GHL, Airtable, cloud storage | Service delivery | Contract performance | Duration + 3 years | Manual |
| Financial records | Invoices, payments, expenses | Accounting system | Tax compliance | Legal obligation | 7 years | Manual |
| Analytics | Campaign metrics, pipeline data | Supabase, GHL, dashboards | Performance analysis | Legitimate interest | 24 months (aggregate) | Automated |
| Memory files | Agent knowledge, preferences | File system, Supabase | AI agent operations | Internal operations | Indefinite (compacted quarterly) | Manual compaction |
| Competitive intel | Competitor data, market research | Airtable, Supabase | Strategy | Legitimate interest | 12mo active + 24mo archive | Automated |
| Suppression list | Email addresses only | Supabase | Prevent re-contact | Legal compliance | Indefinite | Never delete |

---

## 5. Practical Setup: Retention Enforcement Workflow

### Prerequisites

Before building the automated workflow:

1. **Add retention metadata fields to your Supabase schema:**
   - `created_at` (timestamp): When the record was created.
   - `last_activity_date` (timestamp): Last meaningful interaction (email opened, replied, meeting booked, etc.).
   - `archived_date` (timestamp, nullable): When the record was moved to archive.
   - `data_source` (text): Where the data came from (Clay, manual, web scraping, etc.).
   - `retention_category` (text): Which retention category applies.

2. **Create suppression list table in Supabase:**
   ```sql
   CREATE TABLE suppression_list (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       email TEXT NOT NULL UNIQUE,
       reason TEXT NOT NULL,  -- 'opt-out', 'deletion-request', 'bounce', 'spamtrap'
       added_date TIMESTAMP DEFAULT NOW(),
       source TEXT  -- 'manual', 'automated', 'request'
   );
   ```

3. **Create deletion request tracker in Supabase or Airtable:**
   ```sql
   CREATE TABLE deletion_requests (
       id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
       requester_name TEXT,
       requester_email TEXT NOT NULL,
       request_date TIMESTAMP DEFAULT NOW(),
       applicable_law TEXT,  -- 'GDPR', 'CCPA', 'TDPSA', 'general'
       status TEXT DEFAULT 'received',  -- 'received', 'verified', 'in-progress', 'completed'
       systems_searched TEXT[],
       systems_deleted_from TEXT[],
       completion_date TIMESTAMP,
       confirmation_sent BOOLEAN DEFAULT FALSE,
       notes TEXT
   );
   ```

4. **Create archive table in Supabase:**
   ```sql
   CREATE TABLE leads_archive (
       -- Same schema as leads table
       id UUID PRIMARY KEY,
       -- ... all lead fields ...
       archived_date TIMESTAMP DEFAULT NOW(),
       original_created_at TIMESTAMP,
       original_last_activity TIMESTAMP
   );
   ```

### n8n Workflow: Monthly Retention Enforcement

Build this workflow in n8n to run on the 1st of every month:

1. **Schedule Trigger:** Cron expression for 1st of month at 2:00 AM.
2. **Supabase Node:** Query for stale leads (last_activity > 12 months, status not in active pipeline).
3. **Loop Node:** For each stale lead:
   - Insert into `leads_archive` table.
   - Delete from `leads` table.
   - Update GHL contact status to "Archived" (GHL API call).
   - Log to retention enforcement log.
4. **Supabase Node:** Query for expired archives (archived_date > 24 months).
5. **Loop Node:** For each expired archive:
   - Delete from `leads_archive`.
   - Delete from GHL (API call).
   - Delete from Airtable (API call, search by email first).
   - Add email to `suppression_list`.
   - Log to retention enforcement log.
6. **Supabase Node:** Delete communication logs older than 6 months.
7. **Supabase Node:** Delete agent session logs older than 30 days.
8. **Summary Node:** Aggregate counts of actions taken.
9. **Notification Node:** Send summary report via email or webhook.

### n8n Workflow: Suppression List Check (Before Lead Creation)

Build this workflow to run every time a new lead is about to be added:

1. **Webhook Trigger:** Receives new lead data (email, name, company).
2. **Supabase Node:** Check if email exists in `suppression_list`.
3. **IF Node:** If email is in suppression list, reject the lead and return error.
4. **IF Node:** If email is not suppressed, allow lead creation to proceed.

---

## 6. Compliance Calendar

| Frequency | Task | Responsible |
|-----------|------|-------------|
| Monthly | Run automated retention enforcement workflow | Automated (n8n) |
| Monthly | Review and process any pending deletion requests | You (manual) |
| Quarterly | Compact memory files (remove stale entries) | You (manual) |
| Quarterly | Review suppression list for accuracy | You (manual) |
| Annually | Review retention periods (adjust if business needs change) | You (manual) |
| Annually | Update data inventory document | You (manual) |
| Annually | Review backup retention periods | You (manual) |
| As needed | Process individual deletion requests | You (manual, within 30 days) |

---

## 7. Summary

| Data Category | Active Retention | Archive Retention | Total Maximum | Deletion Method |
|--------------|-----------------|-------------------|---------------|-----------------|
| Lead data | 12 months | 24 months | 36 months | Automated monthly |
| Client data | Duration of relationship | 3 years post-relationship | Variable | Manual |
| Financial records | Active | 7 years | 7 years | Manual |
| Communication logs | 6 months | N/A | 6 months | Automated monthly |
| Agent session logs | 30 days | N/A | 30 days | Automated monthly |
| Agent error logs | 90 days | N/A | 90 days | Automated monthly |
| Memory files | Indefinite | N/A | Indefinite (compacted) | Manual quarterly |
| Competitive intel | 12 months | 24 months | 36 months | Automated monthly |
| Analytics (granular) | 6 months | N/A | 6 months | Automated monthly |
| Analytics (aggregate) | 24 months | N/A | 24 months | Automated monthly |
| Suppression list | Indefinite | N/A | Indefinite | Never delete |

The fundamental principle: **collect only what you need, keep it only as long as you need it, delete it when you are done, and be able to prove you did all of this.**

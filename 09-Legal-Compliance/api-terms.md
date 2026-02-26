# API Terms of Service Review

## Overview

Your OpenClaw system integrates with multiple third-party APIs. Each API has its own Terms of Service that govern how you can use it, what you can do with the data, and what restrictions apply. Violating API terms can result in service termination, loss of data, or legal action. This document reviews the key terms for every API in your stack and highlights the provisions most relevant to your operations.

**Key takeaway:** Most APIs are perfectly fine for your B2B marketing agency use case. The main rules to follow are: respect rate limits, do not resell raw data, do not use data for regulated purposes (like credit decisions), and do not build a competing product.

---

## 1. GoHighLevel (GHL) API

### Access Requirements
- You must be a GHL Agency account holder or a GHL SaaS plan holder.
- API access is included with your plan (Agency Unlimited or SaaS plans).
- API keys are per-location (sub-account) or per-agency.

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Rate Limits | 100 API requests per minute per location; burst limits may apply | Implement rate limiting in n8n workflows |
| Data Ownership | You own the data in your sub-accounts | Your lead data, client data, and communication logs belong to you |
| Reselling | Do not resell GHL services without being on SaaS plan | If offering CRM to clients, use SaaS Mode |
| Competition | Do not use the API to build a product that competes with GHL | Your automation system is a tool, not a competing CRM product |
| Sub-accounts | API access is scoped to your sub-accounts | Do not attempt to access other agencies' data |
| Webhooks | Available for real-time event notifications | Use for lead status changes, appointment bookings, etc. |

### Practical Considerations
- GHL's API documentation is at https://highlevel.stoplight.io/docs/integrations.
- The API is evolving rapidly. New endpoints are added frequently, and some older endpoints are deprecated.
- For your use case (managing leads, contacts, opportunities, automated workflows), the API is well-suited.
- GHL stores data on AWS infrastructure, primarily in the US.
- If you are processing EU client data in GHL, review their Data Processing Addendum (available on request or in your agency agreement).

### What to Watch For
- GHL has had API stability issues in the past. Build error handling and retry logic into your n8n workflows.
- Rate limits are enforced per location. If you manage multiple sub-accounts for clients, each has its own limit.
- GHL may update API terms with new feature releases. Review terms quarterly.

---

## 2. Clay.com API

### Access Requirements
- Clay API access is available on paid plans.
- Usage is credits-based. Each enrichment action (finding an email, company lookup, etc.) consumes credits.
- API key is available in your Clay account settings.

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Credits | Each API call consumes credits per your plan tier | Monitor credit usage; set alerts for low balance |
| Data Accuracy | Clay does not guarantee accuracy of enrichment data | Verify critical data before acting on it (especially emails via ZeroBounce) |
| FCRA Prohibition | Do NOT use Clay data for decisions regulated by the Fair Credit Reporting Act | Do not use for employment screening, credit decisions, tenant screening, or insurance underwriting |
| Data Caching | Results may be cached; same query may return cached result | Be aware that data freshness varies |
| Cross-User Data | Some enrichment results may be derived from shared data pools | Not unique to your account; cannot claim exclusivity |
| Reselling | Do not resell raw Clay data as a data product | Using enriched data in your agency services is fine; selling raw data exports is not |

### FCRA Restriction -- Important Detail

The Fair Credit Reporting Act (FCRA) regulates "consumer reports" used for employment, credit, insurance, and housing decisions. Clay explicitly states its data is not a consumer report and must not be used for FCRA-regulated purposes. This means:

- **Allowed:** Using Clay to find a VP of Marketing's email address for sales outreach.
- **Allowed:** Using Clay to enrich a lead list with company data (revenue, employee count, industry).
- **NOT Allowed:** Using Clay data to decide whether to extend credit to someone.
- **NOT Allowed:** Using Clay data to screen job applicants.
- **NOT Allowed:** Using Clay data for tenant screening.

For your B2B marketing use case, this restriction is unlikely to be an issue, but it is important to document.

### Practical Considerations
- Clay's enrichment waterfall pulls from multiple data sources (Apollo, Hunter, Clearbit, People Data Labs, etc.). Each source has its own accuracy and freshness characteristics.
- Build your Clay workflows to handle null/missing results gracefully.
- Use Clay's built-in integrations where possible rather than building custom API calls, as they handle authentication and pagination.

---

## 3. Supabase

### Access Requirements
- Free tier available; paid plans for production use.
- API keys include an `anon` key (client-safe, respects Row Level Security) and a `service_role` key (bypasses RLS, server-only).

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Fair Use | Free tier has fair use limits (500MB database, 1GB storage, 2M edge function invocations/month) | Use paid plan for production |
| Data Ownership | You own all data stored in your Supabase project | Full export capability at any time |
| Infrastructure | Do not mine, benchmark, or stress-test Supabase infrastructure | Normal application use is fine |
| Acceptable Use | No spam, no illegal content, no malware hosting | Standard compliance |
| Security | You are responsible for securing your API keys and access | Never expose `service_role` key in client code |
| Backups | Paid plans include automated backups; free tier does not | Use paid plan and verify backup schedule |

### Practical Considerations
- Supabase is built on PostgreSQL, so you have full SQL capabilities and can export your data at any time.
- Row Level Security (RLS) should be enabled on all tables containing sensitive data.
- The `service_role` key has full access to all data. Protect it like a database root password.
- Supabase edge functions have execution time limits and memory limits depending on your plan.
- For your memory system and lead storage, Supabase's pgvector extension is available for vector similarity search.

### Data Residency
- Supabase lets you choose your project region. For GDPR compliance (if applicable), you can choose an EU region.
- For your primary use (US-based agency, US-focused leads), choose a US region for lowest latency.

---

## 4. Anthropic (Claude) API

### Access Requirements
- API key from console.anthropic.com.
- Pay-per-use pricing based on input and output tokens.
- Rate limits based on your usage tier (increases with spend history).

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Acceptable Use Policy | No deception, illegal activity, malware, harassment, or content that exploits minors | Standard compliance |
| AI Disclosure | Disclose AI-generated content where legally required | Disclose in email footers or where required by law |
| Rate Limits | Requests per minute and tokens per minute limits apply | Implement queuing and retry logic |
| Spend Limits | Set spending limits in your account to prevent runaway costs | Configure monthly spend caps |
| Output Monitoring | Anthropic may review usage patterns for safety and abuse prevention | Be aware that prompts and outputs may be reviewed |
| Data Handling | Anthropic does not train on API inputs by default (as of current policy) | Review current data policy periodically |
| Competing Products | No restriction on building products using the API | Your automation system is fine |

### AI Disclosure Requirements

This is worth special attention. As of 2024-2025, there is no federal US law requiring disclosure of AI-generated content in all contexts. However:

- **FTC guidance:** The FTC has signaled that using AI to deceive consumers is an unfair or deceptive practice. If your AI-generated emails impersonate a real person or create false impressions, you risk FTC enforcement.
- **State laws:** Several states are considering or have passed AI disclosure laws. Colorado's AI Act (effective 2026) requires disclosure of high-risk AI systems. California has proposed similar legislation.
- **Practical guidance:** You do not need to stamp every email with "Written by AI," but you should:
  - Not claim a human wrote something that was AI-generated if someone asks.
  - Not use AI to generate fake testimonials, fake reviews, or fake endorsements.
  - Be transparent with your clients about your use of AI in your services.
  - Disclose AI involvement where any applicable law requires it.

### Practical Considerations
- Claude's context window and output limits vary by model. Plan your prompts accordingly.
- Implement proper error handling for rate limit errors (429 status codes) with exponential backoff.
- Store API responses in Supabase to avoid re-processing the same data.
- For your agent system, be mindful of token costs -- long memory files and system prompts add up.

---

## 5. Airtable API

### Access Requirements
- API access available on all plans (including free).
- Personal access tokens or OAuth 2.0 for authentication.
- Enterprise plans offer additional API features (audit logs, SCIM provisioning).

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Rate Limits | 5 API requests per second per base | Implement rate limiting; batch requests where possible |
| Data Ownership | You own all data in your bases | Full export capability |
| Competing Products | Do not use Airtable API to build a product that competes with Airtable | Your automation system is a tool, not a competing database product |
| Acceptable Use | No spam, no illegal content, no abuse | Standard compliance |
| Record Limits | 50,000 records per base on free/Plus plans; 500,000 on Pro; higher on Enterprise | Plan your data architecture accordingly |

### Practical Considerations
- The 5 requests/second rate limit is the most restrictive in your stack. Design your n8n workflows to batch API calls and include delays.
- Airtable's API supports filtering, sorting, and field selection, which reduces the number of calls needed.
- For large data operations, consider using Airtable's bulk create/update endpoints (up to 10 records per call).
- Airtable's webhook feature (Automations) can push data to your system, reducing the need for polling.
- If you hit record limits, consider whether Supabase (PostgreSQL) is a better fit for that data.

### Airtable vs. Supabase for Data Storage

For your OpenClaw system, the general guidance is:

- **Airtable:** Use for data that benefits from a spreadsheet-like interface, collaboration, and quick manual edits. Good for campaign tracking, content calendars, client deliverables.
- **Supabase:** Use for high-volume data that requires fast queries, joins, and programmatic access. Good for lead databases, memory storage, agent session logs.

---

## 6. DataForSEO API

### Access Requirements
- Account at dataforseo.com.
- Pay-per-task pricing (each API call consumes credits based on the endpoint).
- API credentials (login/password for basic auth).

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Data Use | Results are for your use only (internal business use or serving your clients) | Using data for your agency and clients is fine |
| Reselling | Do not resell raw DataForSEO data as a standalone data product | Incorporating results into your services is fine; selling raw API output is not |
| Rate Limits | Vary by plan; concurrent request limits apply | Monitor concurrency and implement queuing |
| Caching | DataForSEO caches results; you may receive cached data | Be aware data may not be real-time |
| Attribution | No requirement to attribute DataForSEO in your output | Use data freely in your reports and dashboards |

### What DataForSEO Replaces

DataForSEO provides authorized API access to data you would otherwise need to scrape:

| DataForSEO Endpoint | What It Replaces | Legal Benefit |
|---------------------|-----------------|---------------|
| SERP API | Scraping Google search results | Authorized access to search data |
| Google Maps API | Scraping Google Maps listings | Authorized access to business listings |
| Business Data API | Scraping business directories | Aggregated business data |
| Backlink API | Scraping link data | Authorized access to link data |
| Domain Analytics | Scraping SEO metrics | Authorized access to SEO data |

### Practical Considerations
- DataForSEO is one of the safest ways to get search engine data because they have agreements with data providers and handle the scraping compliance themselves.
- Use their batch endpoints for large queries to stay within rate limits.
- Cache results in Supabase to avoid redundant API calls and reduce costs.

---

## 7. ZeroBounce API

### Access Requirements
- Account at zerobounce.net.
- Per-credit pricing for email verification.
- API key authentication.

### Key Terms

| Area | Requirement | Your Compliance |
|------|------------|-----------------|
| Pricing | Per-credit for each email verified | Budget for verification costs in your pipeline |
| Accuracy | Results are guidance, not guarantee | Build your system to handle false positives/negatives |
| Anti-Spam | Do not use ZeroBounce to validate lists for spam campaigns | Your B2B outreach is legitimate marketing, not spam |
| Data Handling | ZeroBounce processes email addresses you submit | They see the emails you verify; review their privacy policy |
| Bulk Processing | Available via batch API endpoint | Use batch for efficiency when verifying large lists |

### Practical Considerations
- Always verify emails before sending outreach. Invalid emails hurt your sender reputation.
- ZeroBounce returns status codes (valid, invalid, catch-all, unknown, spamtrap, abuse, do_not_mail). Only send to "valid" addresses.
- "Catch-all" addresses accept all emails but may not deliver to the intended recipient. Consider them medium-risk for sending.
- "Spamtrap" and "abuse" addresses should be permanently suppressed.
- Re-verify emails periodically (every 3-6 months) because email validity changes over time.
- ZeroBounce also offers an email scoring API that predicts deliverability -- useful for prioritizing high-quality leads.

---

## 8. Additional APIs to Consider

### Instantly / Smartlead (Email Sending)

If you use these for cold email delivery:
- Must comply with CAN-SPAM (see data-privacy.md).
- Maintain sender reputation by warming up domains gradually.
- Follow their acceptable use policies (no spam, honor unsubscribes).
- Data (email accounts, contact lists, campaign data) belongs to you.

### Apollo.io (via Clay or direct)

- Usage governed by Apollo's terms.
- Data is for your business use; do not resell.
- Not a consumer report; do not use for FCRA purposes.
- Apollo sources data from public sources and user contributions.

### Google APIs (Maps, Places, Custom Search)

- Requires Google Cloud account and API key.
- Usage subject to Google API Services Terms.
- Rate limits and per-request pricing apply.
- Do not cache Google data for longer than allowed by the specific API's terms (often 30 days for Places API).
- Must display Google attribution if showing results to end users.

---

## 9. Cross-Cutting Compliance Requirements

### Rate Limit Strategy

Implement a unified rate limiting approach across all APIs:

```
API               | Limit              | Implementation
------------------|--------------------|---------------------------
GHL               | 100/min/location   | n8n rate limiter node
Clay              | Per plan           | Credit monitoring + alerts
Supabase          | Connection limits   | Connection pooling
Anthropic         | Tier-based RPM/TPM | Queue with exponential backoff
Airtable          | 5/sec              | Request queue with 200ms delay
DataForSEO        | Per plan           | Concurrency limiter
ZeroBounce        | Per plan           | Batch processing
```

### Data Residency and Cross-Border Transfer

| API | Data Location | EU Adequacy |
|-----|--------------|-------------|
| GHL | US (AWS) | DPA required for EU data |
| Clay | US | DPA required for EU data |
| Supabase | Configurable (US or EU) | Choose EU region if needed |
| Anthropic | US | Review current data processing terms |
| Airtable | US | DPA available on Enterprise |
| DataForSEO | EU (Lithuania-based) | EU-based, generally compliant |
| ZeroBounce | US | Review their privacy policy |

### Annual Review Process

Review API terms annually (or when notified of changes) for each service:

1. Check for updated Terms of Service.
2. Verify rate limits have not changed.
3. Confirm pricing model has not changed.
4. Review data processing terms for privacy compliance.
5. Verify your usage remains within acceptable use policies.
6. Document the review date and any required changes.

---

## 10. Summary

Your API usage for B2B marketing automation is well within the acceptable use boundaries of all the services in your stack. The main rules to follow:

1. **Respect rate limits** -- implement proper queuing, delays, and retry logic.
2. **Do not resell raw data** -- using data in your services is fine; selling data exports is not.
3. **Do not use for FCRA purposes** -- no credit decisions, employment screening, or tenant screening.
4. **Do not build competing products** -- your automation system is a tool that uses these services, not a competitor.
5. **Maintain DPAs** where required -- especially for handling client data or EU data.
6. **Monitor usage and costs** -- set alerts for credit depletion and spending limits.
7. **Review terms annually** -- API terms change, and you need to stay current.

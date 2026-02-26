# Data Privacy Laws and Compliance

## Overview

As a Texas-based marketing agency that collects business data, runs automation, scrapes websites, uses LinkedIn, and integrates third-party APIs, you operate under multiple overlapping data privacy regimes. This document covers every law relevant to your operations, what each requires of you, and the practical steps to stay compliant.

The core principle: **you can do B2B lead generation and outreach legally, but you must give people transparency, choice, and control over their data.**

---

## 1. GDPR (General Data Protection Regulation) -- European Union

### When It Applies to You

GDPR applies if you process personal data of individuals located in the EU, regardless of where your business is located. If your lead lists ever include contacts at EU-based companies, or if an EU resident visits your website, GDPR is in play.

- Collecting email addresses of EU-based business contacts triggers GDPR.
- Enriching data on EU contacts through Clay or other tools triggers GDPR.
- Sending cold outreach emails to EU business contacts triggers GDPR.

### Legal Basis for B2B Marketing

GDPR requires a "legal basis" for processing personal data. For B2B cold outreach, the most relevant basis is **Legitimate Interest** (Article 6(1)(f)):

- You have a legitimate interest in marketing your services to businesses.
- The processing (collecting business email, sending outreach) is necessary for that interest.
- The individual's rights do not override your interest (because you are contacting them in a professional capacity about professional topics).

**Important:** Legitimate interest is NOT a blank check. You must conduct a **Legitimate Interest Assessment (LIA)** and document it. The assessment should weigh your interest against the data subject's reasonable expectations and privacy.

### Key Rights You Must Honor

| Right | What It Means | Your Response Time |
|-------|---------------|-------------------|
| Right to Access | Person can request all data you hold on them | 30 days |
| Right to Rectification | Person can ask you to correct inaccurate data | 30 days |
| Right to Erasure ("Right to Be Forgotten") | Person can ask you to delete all their data | 30 days |
| Right to Object | Person can object to processing based on legitimate interest | Must stop processing immediately upon request |
| Right to Data Portability | Person can request data in machine-readable format | 30 days |

### Required Documentation

- **Record of Processing Activities (ROPA):** A written inventory of what personal data you process, why, how long you keep it, and who you share it with. This is mandatory under Article 30.
- **Data Processing Agreements (DPAs):** Written contracts with every vendor that processes EU personal data on your behalf (Clay, GHL, Supabase, Airtable, Anthropic, email providers).
- **Privacy Policy:** Must disclose your identity, what data you collect, why, legal basis, retention periods, and how to exercise rights.
- **Legitimate Interest Assessment:** Documented analysis for each processing activity based on legitimate interest.

### Consent for Cold Email Marketing

Under GDPR, cold B2B email is allowed under legitimate interest in most EU countries, but some member states (notably Germany) require explicit opt-in consent for any commercial email. The safest approach:

1. Use legitimate interest as your basis for initial contact.
2. Limit outreach to professional email addresses (not personal).
3. Include an easy opt-out in every message.
4. Stop immediately if someone objects.
5. If targeting Germany, Austria, or other strict-consent countries, obtain consent first or avoid cold email entirely.

### Penalties

- Up to 20 million EUR or 4% of global annual turnover, whichever is higher.
- In practice, enforcement against small US-based agencies is rare but not impossible. The bigger risk is reputational damage and losing access to EU markets.

---

## 2. CCPA / CPRA (California Consumer Privacy Act / California Privacy Rights Act)

### When It Applies to You

CCPA/CPRA applies if you do business in California AND meet any one of these thresholds:

- Annual gross revenue over $25 million, OR
- Buy, sell, or share the personal information of 100,000+ California residents/households/devices per year, OR
- Derive 50% or more of annual revenue from selling or sharing personal information.

Even if you do not meet these thresholds, if your **clients** are subject to CCPA and you process data on their behalf, you may be a "service provider" under CCPA and need to comply with service provider requirements.

### Key Requirements

**Notice at Collection:** Before or at the point of collecting personal information from California consumers, you must disclose what categories of data you collect and the purposes.

**Right to Know:** California consumers can request:
- What categories of personal information you have collected about them.
- The specific pieces of personal information you have collected.
- The sources from which you collected the information.
- The business purpose for collecting or selling.
- The categories of third parties with whom you share.

**Right to Delete:** Consumers can request deletion of their personal information, and you must also direct your service providers to delete it.

**Right to Opt-Out of Sale/Sharing:** If you "sell" or "share" personal data (which includes sharing data for cross-context behavioral advertising), you must offer a "Do Not Sell or Share My Personal Information" link.

**Service Provider Agreements:** If you use Clay, GHL, or any other vendor to process data of California consumers, you need written agreements that restrict how those vendors use the data.

### Practical Impact on Your Agency

- If you collect lead data on California-based businesses and those leads include personal information (names, emails, phone numbers), CCPA may apply depending on your thresholds.
- Your enrichment pipeline (Clay enriching leads) constitutes "collection" under CCPA.
- Sharing enriched lead data with clients could constitute "sale" or "sharing" under CPRA unless structured as a service provider relationship.

### Penalties

- $2,500 per unintentional violation.
- $7,500 per intentional violation.
- Private right of action for data breaches: $100-$750 per consumer per incident.

---

## 3. Texas Data Privacy and Security Act (TDPSA)

### Overview

The TDPSA became effective **July 1, 2024**. As a Texas-based business, this is your home-state privacy law and directly applicable to your operations.

### Who It Applies To

The TDPSA applies to entities that:
- Conduct business in Texas or produce products/services consumed by Texas residents, AND
- Process or engage in the sale of personal data, AND
- Are not a small business as defined by the SBA (unless selling sensitive data or biometric data).

**Important note for small businesses:** If your agency qualifies as an SBA-defined small business, you are largely exempt from TDPSA unless you sell sensitive personal data. However, you should still follow its principles as best practice and because your clients may require it.

### Consumer Rights Under TDPSA

| Right | Description |
|-------|-------------|
| Right to Access | Consumers can confirm whether you process their data and access it |
| Right to Correction | Consumers can correct inaccuracies |
| Right to Deletion | Consumers can request deletion of their personal data |
| Right to Data Portability | Consumers can obtain a portable copy of their data |
| Right to Opt-Out | Consumers can opt out of processing for targeted advertising, sale of data, or profiling |

### Data Protection Assessments

TDPSA requires **Data Protection Assessments** for high-risk processing activities, including:
- Processing personal data for targeted advertising.
- Selling personal data.
- Processing sensitive data.
- Profiling that presents a reasonably foreseeable risk of harm.

For your agency, this means if you are profiling leads for targeted outreach or selling lead lists, you should conduct and document a data protection assessment.

### 30-Day Cure Period

A distinctive feature of TDPSA: before the Texas Attorney General can bring an enforcement action, they must provide written notice of the alleged violation and give you **30 days to cure it**. This is more forgiving than GDPR, but you should not rely on it as a defense -- fix issues proactively.

### Enforcement

- Enforced exclusively by the Texas Attorney General.
- No private right of action (consumers cannot sue you directly under TDPSA).
- Civil penalties up to $7,500 per violation.

---

## 4. CAN-SPAM Act (Federal Email Law)

### Overview

The CAN-SPAM Act governs all commercial email messages sent to recipients in the United States. This is the most directly relevant law for your cold outreach operations.

### Requirements for Every Commercial Email

1. **Accurate Header Information:** The "From," "To," and routing information must be accurate. The "From" name and email must identify the person or business who initiated the message.

2. **Non-Deceptive Subject Lines:** The subject line must accurately reflect the content of the message. Do not use misleading subjects like "Re: Our conversation" if you never had a conversation.

3. **Identification as an Advertisement:** The message must clearly and conspicuously identify itself as an advertisement. This can be subtle (e.g., a small disclaimer at the bottom) but must be present.

4. **Physical Mailing Address:** Every commercial email must include a valid physical postal address. This can be:
   - Your current street address, OR
   - A registered PO Box, OR
   - A registered commercial mail receiving agency address.

5. **Opt-Out Mechanism:** Every email must include a clear, conspicuous, and functional mechanism for the recipient to opt out of future emails. Requirements:
   - Must be able to process opt-outs for at least 30 days after the email is sent.
   - Opt-out must be processed within **10 business days**.
   - You cannot require the recipient to pay a fee, provide information beyond email address, or take any steps beyond sending a reply email or visiting a single web page.
   - You cannot sell or transfer the email address of someone who has opted out.

6. **Monitoring Third Parties:** If you hire someone to handle your email marketing (or use automation), you are still legally responsible for compliance.

### What CAN-SPAM Does NOT Require

- **No opt-in required:** Unlike GDPR, CAN-SPAM does not require prior consent to send commercial emails. You can send cold emails to business contacts you have never interacted with.
- **No limit on volume:** There is no legal limit on how many emails you can send (but ISP/ESP reputation limits apply practically).

### Penalties

- Up to $51,744 per non-compliant email (as of 2024 adjustment).
- FTC enforcement, plus state attorneys general can bring actions.

### Practical Implementation for Your Agency

Every automated outreach email from your system must include:
```
[Your Agency Name]
[Your Physical Address]
If you no longer wish to receive these emails, click here to unsubscribe: [unsubscribe link]
```

Your GHL and email automation workflows must:
- Check the suppression/unsubscribe list before sending.
- Process unsubscribes within 10 business days (ideally instantly).
- Never email someone who has opted out.

---

## 5. Practical Implementation Checklist

### Privacy Policy

Create and publish a privacy policy for your agency website that covers:

- [ ] Your identity and contact information.
- [ ] What personal data you collect (names, business emails, phone numbers, company info, website behavior).
- [ ] How you collect it (direct collection, third-party enrichment via Clay, web scraping, LinkedIn research).
- [ ] Why you collect it (legitimate interest in B2B marketing, service delivery).
- [ ] Who you share it with (categories of recipients: email service providers, CRM, enrichment tools).
- [ ] How long you keep it (reference your data retention policy).
- [ ] Rights of data subjects (access, correction, deletion, opt-out).
- [ ] How to exercise those rights (email address, response time commitment).
- [ ] Cookie policy (if applicable to your website).

### Data Processing Agreements (DPAs)

Execute DPAs with every vendor that processes personal data on your behalf:

| Vendor | DPA Status | Notes |
|--------|-----------|-------|
| GoHighLevel | Review their DPA in your partner agreement | Covers CRM data, email sending, SMS |
| Clay.com | Check their Terms of Service for DPA provisions | Covers data enrichment |
| Supabase | Standard DPA available on their website | Covers database hosting |
| Airtable | Enterprise DPA available on request | Covers data storage |
| Anthropic (Claude) | Review API terms; usage policy covers data handling | Covers AI processing |
| DataForSEO | Check terms for data processing provisions | Covers SEO data |
| ZeroBounce | Review terms | Covers email verification |
| Email sending service (Instantly, Smartlead, etc.) | Must have DPA | Covers email delivery |

### Opt-Out Mechanisms

Implement opt-out handling across all communication channels:

- **Email:** Unsubscribe link in every email. Instant removal from active sequences. Sync unsubscribe across all sending platforms.
- **LinkedIn:** If someone asks you to stop messaging, stop immediately and note it in your CRM.
- **SMS (if applicable):** STOP keyword handling. Immediate removal from SMS lists.
- **Global suppression list:** Maintain a single source of truth for opted-out contacts that all systems check before sending.

### Data Retention Limits

Do not keep personal data longer than necessary for your business purpose. See the companion document `data-retention.md` for specific retention periods by data category.

### Right to Deletion Process

When someone requests deletion of their data:

1. **Acknowledge** the request within 48 hours.
2. **Search** all systems for their data: GHL, Supabase, Airtable, Clay, email platforms, memory files, backups.
3. **Delete** from all active systems within 30 days.
4. **Confirm** deletion to the requester.
5. **Log** the deletion request and completion in your deletion log.
6. **Add** their email to your global suppression list (so you do not re-collect their data).

---

## 6. Risk Assessment by Activity

| Activity | Primary Law | Risk Level | Mitigation |
|----------|------------|------------|------------|
| Cold email to US businesses | CAN-SPAM | Low | Include required elements, honor opt-outs |
| Cold email to EU businesses | GDPR | Medium | Legitimate interest assessment, easy opt-out |
| Cold email to CA businesses | CCPA/CPRA | Medium | Notice at collection, honor deletion requests |
| Enriching leads via Clay | TDPSA, CCPA, GDPR | Low-Medium | DPA with Clay, document purpose |
| Storing leads in Supabase/Airtable | TDPSA, CCPA, GDPR | Low | DPA, access controls, retention limits |
| Web scraping business data | See web-scraping-law.md | Medium | Scrape public data only, respect robots.txt |
| LinkedIn automation | LinkedIn ToS + GDPR/CCPA | High | See linkedin-tos.md |
| AI-generated outreach | CAN-SPAM, state laws | Low-Medium | Disclose AI where required, honest subjects |

---

## 7. Recommended Actions (Priority Order)

1. **Publish a privacy policy** on your agency website covering all required disclosures.
2. **Implement unsubscribe handling** across all email outreach with global suppression list sync.
3. **Include CAN-SPAM required elements** in every outreach email template.
4. **Execute or verify DPAs** with Clay, GHL, Supabase, Airtable, and email sending tools.
5. **Document your Legitimate Interest Assessment** for B2B cold outreach (especially if targeting EU).
6. **Build a right-to-deletion workflow** that can search and purge a contact across all systems.
7. **Set up data retention automation** (see data-retention.md) to purge stale data on schedule.
8. **Conduct a TDPSA data protection assessment** if you engage in targeted advertising or sell data.
9. **Train any team members** on privacy obligations and opt-out handling procedures.
10. **Review and update annually** as laws evolve (especially TDPSA regulations and new state laws).

---

## References

- GDPR Full Text: https://gdpr-info.eu/
- CCPA/CPRA Text: https://oag.ca.gov/privacy/ccpa
- TDPSA Text: https://capitol.texas.gov/tlodocs/88R/billtext/html/HB04611F.htm
- CAN-SPAM Act: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business
- ICO Legitimate Interest Guidance: https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/legitimate-interests/

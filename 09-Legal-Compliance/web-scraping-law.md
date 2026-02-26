# Web Scraping Legal Framework

## Overview

Web scraping is a core component of lead generation and competitive intelligence for your agency. You use scraping to collect business information from public websites, directories, and search results. This document covers the legal landscape for web scraping in the United States, the key court cases that define what is and is not permitted, and practical guidelines to keep your scraping operations legal and defensible.

**Bottom line:** Scraping publicly available business data is generally legal in the US, but you must follow specific practices to stay on the right side of the law.

---

## 1. Federal Law

### Computer Fraud and Abuse Act (CFAA)

The CFAA (18 U.S.C. Section 1030) is the primary federal law relevant to web scraping. Originally designed to criminalize computer hacking, it prohibits accessing a computer "without authorization" or "exceeding authorized access."

#### The Landmark Case: hiQ Labs v. LinkedIn (2022)

This is the most important case for your operations. Key facts and holdings:

- **hiQ Labs** scraped publicly available LinkedIn profile data to build workforce analytics products.
- **LinkedIn** sent a cease-and-desist letter and blocked hiQ's access.
- **hiQ sued** for a preliminary injunction, arguing LinkedIn could not prevent scraping of public data.
- **Ninth Circuit (2022):** Held that scraping publicly available data likely does NOT violate the CFAA because there is no "authorization" gate to bypass when data is public. The CFAA's "without authorization" concept applies to systems that require credentials (login, password).
- **Supreme Court:** Vacated and remanded in light of Van Buren v. United States (2021), which narrowed the CFAA's scope. On remand, the Ninth Circuit reaffirmed its position.
- **Final outcome:** hiQ eventually lost on other grounds and shut down, but the legal principle stands: **scraping data that is publicly accessible without authentication does not violate the CFAA.**

#### What This Means for You

- Scraping public web pages (company websites, public directories, Google search results) is NOT a CFAA violation.
- Scraping data behind a login (LinkedIn profiles when logged in, private databases) IS potentially a CFAA violation if you bypass or exceed access controls.
- The distinction is between public (no auth required) and private (auth required) data.

#### Van Buren v. United States (2021, Supreme Court)

The Supreme Court ruled that "exceeds authorized access" under the CFAA means accessing areas of a computer system that are off-limits, not using authorized access for unauthorized purposes. This narrowed the CFAA and made it harder to prosecute scraping of publicly available data.

### Copyright Law

- **Facts are not copyrightable.** Business names, addresses, phone numbers, email addresses, employee counts -- these are facts and cannot be copyrighted. You can freely collect and use factual information from websites.
- **Creative expression is copyrightable.** Website text, blog posts, marketing copy, images, and videos are copyrighted. Do not copy and republish substantial portions of copyrighted content.
- **Compilations may be copyrightable.** A database or directory that reflects creative selection, coordination, or arrangement may have thin copyright protection. However, you can still extract individual facts from such a compilation.
- **Practical impact:** You can scrape business facts (name, address, phone, industry, employee count) without copyright concern. Do not scrape and republish full articles, product descriptions, or creative content.

#### Feist Publications v. Rural Telephone (1991, Supreme Court)

The Supreme Court held that factual compilations are copyrightable only if they possess an original selection, coordination, or arrangement. A mere alphabetical listing of phone numbers is not copyrightable. This directly supports your ability to scrape factual business data.

### Trespass to Chattels

This common law tort theory has been applied to web scraping cases where scraping causes actual harm to the website's servers.

- **eBay v. Bidder's Edge (2000):** Court found trespass to chattels where automated scraping consumed a meaningful share of eBay's server capacity.
- **Modern application:** If your scraping is so aggressive that it degrades website performance, slows down the site for legitimate users, or causes the website owner to incur additional hosting costs, you could face a trespass to chattels claim.
- **Mitigation:** Rate-limit your scraping. One request every 2-5 seconds is conservative and safe. Never hammer a site with rapid-fire requests.

---

## 2. State Laws

### Texas Data Privacy and Security Act (TDPSA)

If you scrape data that includes personal information of Texas consumers, the TDPSA applies to your handling of that data. Key requirements:

- Provide transparency about data collection.
- Honor consumer rights (access, correction, deletion, opt-out).
- Conduct data protection assessments for high-risk processing.
- The TDPSA does not prohibit scraping itself, but it regulates what you do with the personal data you collect.

### California Consumer Privacy Act (CCPA/CPRA)

If your scraping collects personal information of California consumers:

- You must provide notice at the point of collection (or as soon as practicable).
- California consumers can request access to, deletion of, or opt-out of sale of their data.
- Scraping is considered "collection" under CCPA.

### Other State Privacy Laws

Virginia (VCDPA), Colorado (CPA), Connecticut (CTDPA), and a growing number of states have similar consumer privacy laws. If you scrape data about individuals in these states, you must comply with their respective requirements.

### Illinois Biometric Information Privacy Act (BIPA)

If your scraping ever involves collecting facial images, fingerprints, or other biometric data of Illinois residents, BIPA applies and requires prior informed consent. This is unlikely for your B2B use case but worth noting.

---

## 3. Terms of Service

### Legal Effect of Website Terms of Service

Most websites have Terms of Service (ToS) that prohibit scraping. The legal enforceability of these terms depends on how they are presented:

#### Clickwrap Agreements
- **What they are:** User must actively click "I agree" before accessing the site or service.
- **Enforceability:** Generally enforceable. Courts consistently uphold clickwrap agreements.
- **Example:** Creating an account on a platform and checking a box agreeing to terms.
- **Impact on you:** If you create an account on a site and agree to terms that prohibit scraping, scraping that site is a breach of contract (civil, not criminal).

#### Browsewrap Agreements
- **What they are:** Terms are posted on the site (often linked in the footer) but the user never actively agrees. Simply using the site is deemed acceptance.
- **Enforceability:** Often unenforceable, especially if the user did not have actual or constructive notice of the terms. Courts are split, but the trend favors users who never saw or agreed to the terms.
- **Example:** A link to "Terms of Use" in the footer of a business website.
- **Impact on you:** If a website only has browsewrap terms prohibiting scraping, those terms are likely unenforceable against you, especially for public data. However, this is not a guarantee, and some courts have enforced browsewrap terms where notice was sufficient.

#### Practical Guidance

- If you must create an account and agree to terms that prohibit scraping, **do not scrape that site** while logged in. The terms are enforceable.
- If a site only has browsewrap terms, the terms are likely unenforceable for scraping public data, but it is still good practice to respect them or at least document your reasoning for proceeding.
- **ToS violations are civil matters, not criminal.** Violating a website's ToS could lead to a cease-and-desist letter or a civil lawsuit for breach of contract, but not criminal prosecution.

---

## 4. Robots.txt

### What It Is

The `robots.txt` file is a text file at the root of a website (e.g., `https://example.com/robots.txt`) that tells web crawlers which parts of the site they should or should not access.

### Legal Status

- **Robots.txt is NOT legally binding.** It is a voluntary standard (the Robots Exclusion Protocol) and has no force of law.
- **However, courts may consider it.** In scraping-related lawsuits, courts have looked at whether the scraper respected robots.txt as evidence of good or bad faith.
- **Respecting robots.txt demonstrates good faith.** If you ever face a legal challenge, showing that you respected robots.txt strengthens your position.
- **Ignoring robots.txt demonstrates bad intent.** If you deliberately ignore robots.txt restrictions, it can be used against you to show you knew the site owner did not want scraping.

### Practical Guidance

- **Always check robots.txt** before scraping a new site.
- **Respect Disallow directives** for the paths you are targeting.
- **Document your robots.txt compliance** in your scraping logs.
- If robots.txt allows your target paths, proceed with confidence.
- If robots.txt disallows your target paths, think carefully about whether to proceed. You may still legally be able to scrape public data, but you lose the good-faith defense.

---

## 5. Safe Scraping Practices

Follow these practices to minimize legal risk and maximize defensibility:

### Technical Best Practices

1. **Only scrape publicly accessible pages.** Never scrape content behind authentication, paywalls, or access controls.

2. **Respect robots.txt.** Check it for every domain you scrape and honor the directives.

3. **Rate-limit requests.** Use conservative delays between requests:
   - Minimum: 1 request every 2 seconds.
   - Recommended: 1 request every 3-5 seconds.
   - For small/medium sites: 1 request every 5-10 seconds to be extra cautious.
   - Never send more than 1 concurrent request to a single domain.

4. **Identify yourself with a User-Agent string.** Use a descriptive User-Agent that includes your company name and a contact URL or email. Example:
   ```
   OpenClawBot/1.0 (+https://youragency.com/bot; contact@youragency.com)
   ```
   This demonstrates transparency and good faith. It also allows site owners to contact you if they have concerns.

5. **Do not circumvent access controls.** Never bypass CAPTCHAs, rate limiters, IP blocks, or other technical measures designed to prevent automated access.

6. **Cache results aggressively.** Store scraped data locally and do not re-scrape the same pages unnecessarily. If you need updated data, re-scrape at reasonable intervals (weekly or monthly, not hourly).

7. **Do not scrape personal data without a legitimate basis.** If you are collecting personal information (names, emails, phone numbers), ensure you have a legitimate purpose (B2B marketing under CAN-SPAM, legitimate interest under GDPR) and comply with applicable privacy laws.

8. **Minimize data collection.** Only scrape the specific data fields you need. Do not download entire websites or collect data "just in case."

### Operational Best Practices

9. **Keep records of what you scrape.** Document for each scraping target:
   - URL(s) scraped.
   - Date and time of scraping.
   - robots.txt status at time of scraping.
   - Data fields collected.
   - Purpose of collection.
   - Retention period.

10. **Respond promptly to cease-and-desist requests.** If a website owner contacts you and asks you to stop scraping, stop immediately. Document the request and your compliance.

11. **Do not republish scraped content.** Using scraped factual data to populate your CRM or enrich leads is fine. Republishing scraped articles, product descriptions, or creative content on your own site is copyright infringement.

12. **Use official APIs where available.** If a website offers an API for the data you need, use it instead of scraping. APIs are sanctioned access paths and eliminate most legal risk.

---

## 6. Risk Assessment by Target

### Low Risk (Generally Safe)

| Target | Notes |
|--------|-------|
| Public business websites (company info, team pages) | Factual data, publicly accessible, low enforcement risk |
| Google Search results (via API) | Use Google Custom Search API or DataForSEO; avoid scraping google.com directly |
| Google Maps / Google Business Profiles (via API) | Use Google Places API or DataForSEO; rich source of business data |
| Public business directories (BBB, Yelp public pages, industry directories) | Factual data; respect rate limits |
| Public government databases (Secretary of State, property records) | Public records; generally unrestricted |
| Conference/event speaker and attendee lists | Publicly posted; factual data |
| Press releases and news sites | Public content; collect facts, do not republish articles |
| Job posting sites (for hiring intent signals) | Public postings; factual data about company needs |

### Medium Risk (Proceed with Caution)

| Target | Notes |
|--------|-------|
| Scraping google.com directly (not via API) | Google's ToS prohibit it; use DataForSEO or Custom Search API instead |
| Crunchbase free tier | ToS restrict scraping; use their API for authorized access |
| Glassdoor | Aggressive anti-scraping measures; ToS prohibit |
| Reddit | Public data, but Reddit's terms restrict commercial scraping; use their API |

### High Risk (Avoid)

| Target | Risk | Notes |
|--------|------|-------|
| LinkedIn | Very High | Aggressive enforcement, sophisticated detection, legal history of suing scrapers |
| Facebook / Instagram | Very High | Meta aggressively enforces against scrapers, has filed numerous lawsuits |
| Twitter/X | High | API access heavily restricted; scraping blocked aggressively |
| Sites behind login walls | High | Potential CFAA violation if accessing beyond authorization |
| Sites with CAPTCHA or anti-bot measures | High | Circumventing access controls strengthens legal claims against you |
| Healthcare-related sites with patient data | Very High | HIPAA implications |
| Financial data behind paywalls | Very High | Potential SEC and copyright issues |

---

## 7. Legal Defense Documentation

If you are ever challenged on your scraping activities, having the following documentation ready is your best defense:

### Scraping Log Template

For each scraping target, maintain a record:

```
Target: [company-website.com]
Date: [2025-01-15]
Robots.txt checked: Yes - allowed for targeted paths
Data collected: Company name, address, phone, industry, employee count
Purpose: B2B lead generation for [client/internal use]
Volume: 150 pages, 1 request per 3 seconds
User-Agent: OpenClawBot/1.0 (+https://youragency.com/bot)
Data retention: 12 months, then archived for 24 months
Authentication bypassed: No
ToS reviewed: Browsewrap only, no clickwrap agreement
```

### Legitimate Purpose Documentation

Maintain a written document that explains:

- What data you scrape and why (B2B lead generation, competitive intelligence, market research).
- How the data is used (populating CRM, enriching leads, sending outreach).
- How you minimize impact on target websites (rate limiting, caching, respecting robots.txt).
- How you protect the data you collect (encryption, access controls, retention limits).
- How you handle cease-and-desist requests (immediate compliance).

---

## 8. Integration with Your OpenClaw Pipeline

### Recommended Scraping Architecture

1. **DataForSEO for search engine data.** Use their API instead of scraping Google directly. This is authorized API access and eliminates risk.

2. **Google APIs for Google data.** Places API for business listings, Custom Search API for web search results.

3. **Direct scraping for business websites.** When you need to scrape company websites (e.g., extracting team member names from About pages, service offerings, technology stack from job postings):
   - Implement rate limiting in your scraping service.
   - Use a proper User-Agent.
   - Check robots.txt.
   - Cache results in Supabase.

4. **Clay for data enrichment.** Clay handles the scraping and API calls for enrichment data (emails, phone numbers, company info). They assume the legal responsibility for their data collection methods. You are using their output, not scraping yourself.

5. **n8n for orchestration.** Use n8n to coordinate scraping jobs with rate limits, error handling, and logging.

### Data Flow for Scraped Data

```
Target Website --> Scraper (rate-limited) --> Raw Data --> Processing --> Supabase
                                                                          |
                                                            Clay Enrichment
                                                                          |
                                                                    GHL CRM
```

At each stage, apply:
- Data minimization (only collect what you need).
- Access controls (only authorized systems can read the data).
- Retention limits (delete when no longer needed).
- Logging (record what was collected, when, and why).

---

## 9. Summary of Key Legal Principles

| Principle | Status | Source |
|-----------|--------|--------|
| Scraping public data is not a CFAA violation | Established | hiQ v. LinkedIn, Van Buren v. US |
| Facts cannot be copyrighted | Established | Feist v. Rural Telephone |
| Overloading servers is actionable | Established | eBay v. Bidder's Edge |
| Clickwrap ToS are enforceable | Established | Multiple cases |
| Browsewrap ToS have questionable enforceability | Trend toward unenforceability | Multiple cases |
| Robots.txt is not legally binding | Established | Industry standard, no statutory basis |
| Respecting robots.txt shows good faith | Persuasive | Judicial consideration |
| Privacy laws apply to scraped personal data | Established | GDPR, CCPA, TDPSA |

---

## References

- hiQ Labs v. LinkedIn (9th Cir. 2022): https://law.justia.com/cases/federal/appellate-courts/ca9/17-16783/17-16783-2022-04-18.html
- Van Buren v. United States (S. Ct. 2021): https://www.supremecourt.gov/opinions/20pdf/19-783_k53l.pdf
- Feist Publications v. Rural Telephone (S. Ct. 1991): https://supreme.justia.com/cases/federal/us/499/340/
- CFAA Text (18 U.S.C. 1030): https://www.law.cornell.edu/uscode/text/18/1030
- Robots Exclusion Protocol: https://www.robotstxt.org/
- EFF Guide to CFAA: https://www.eff.org/issues/cfaa

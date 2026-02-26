# Competitive Intelligence: Legal and Ethical Framework

## Overview

Competitive intelligence gathering -- researching competitor businesses to inform your clients' marketing strategy -- is a core capability of any marketing agency. However, the methods used to gather this intelligence must stay within legal and ethical boundaries. This document covers the legal framework for web scraping and data collection, ethical guidelines for responsible intelligence gathering, safe and risky data sources, and practical recommendations for OpenClaw's competitive intelligence features.

**Important disclaimer: This document is informational research, not legal advice. Consult a licensed attorney for guidance specific to your situation and jurisdiction.**

---

## Key Legal Principles

### 1. Public Data is Generally Legal to Access

**Principle:** Information that is publicly available on the internet -- visible to anyone without a login, password, or special access -- is generally legal to access and collect.

**Supporting precedent:**
- **hiQ Labs v. LinkedIn (2022):** The Ninth Circuit confirmed that scraping publicly accessible data does not violate the Computer Fraud and Abuse Act (CFAA). Public means public.
- **Sandvig v. Barr (2020):** Court ruled that the CFAA does not criminalize violations of a website's Terms of Service when accessing otherwise public data.

**What qualifies as "public data":**
- Google Search results
- Google Maps / Google Business Profile listings
- Yelp business listings (public reviews, ratings)
- BBB business profiles
- Company websites (all pages accessible without login)
- Social media public posts (Facebook public pages, Instagram public profiles, Twitter/X public tweets)
- SEC filings and government records
- Press releases and news articles
- Patent databases
- Court records

**What does NOT qualify as "public data":**
- Content behind a login wall
- Content accessible only with a paid subscription
- Private messages or communications
- Data in password-protected areas
- Content explicitly restricted by authentication

### 2. Computer Fraud and Abuse Act (CFAA)

**What the CFAA prohibits:**
- Accessing a computer "without authorization" or "exceeding authorized access"
- Originally targeting hackers, but broadly applied to web scraping cases

**Current interpretation (post-Van Buren, 2021):**
- The Supreme Court in *Van Buren v. United States* narrowed the CFAA
- "Exceeds authorized access" means accessing areas of a computer you have no right to access at all -- not merely violating the way you are supposed to use data you can access
- This means: if data is public (no gate), accessing it is not a CFAA violation
- If you bypass authentication (passwords, IP blocks, CAPTCHAs designed to restrict access), you may be violating the CFAA

**Practical implication for OpenClaw:**
- Scraping public website data: NOT a CFAA violation
- Scraping data behind a login: POTENTIALLY a CFAA violation
- Circumventing technical access restrictions (IP blocks, CAPTCHAs): gray area, proceed with caution

### 3. Copyright Law

**Key principle:** Facts are not copyrightable. Creative expression is.

**What this means for competitive intelligence:**
- **Legal:** Collecting factual data about a competitor (prices, services offered, locations, hours, review scores, technology stack)
- **Legal:** Noting that a competitor's website has specific features or uses specific technology
- **Potentially illegal:** Copying large amounts of a competitor's website content (text, images, design)
- **Potentially illegal:** Reproducing competitor's marketing materials, ad copy, or creative content
- **Legal:** Summarizing or analyzing competitor content in your own words

**Safe practices:**
- Extract facts and data points, not creative content
- If you reference competitor content, summarize it, don't copy it verbatim
- Never use competitor images, logos, or design elements
- Attribute sources when sharing competitive analysis

### 4. Terms of Service (ToS)

**Legal status of ToS violations:**
- Violating a website's Terms of Service is generally NOT a criminal offense
- However, it CAN be a civil breach of contract issue
- Courts have been inconsistent on whether ToS violations create enforceable claims against scrapers
- In practice, companies rarely sue individual scrapers for ToS violations (they sue companies that build products on scraped data)

**Practical approach:**
- Respect ToS as a best practice, especially for platforms you use regularly
- If a website's ToS prohibits scraping, consider using their official API instead
- For one-off competitive research, ToS violations carry minimal practical risk
- For systematic, ongoing scraping of a specific site, ToS violations carry higher risk

### 5. Robots.txt

**What it is:** A file at the root of a website (`example.com/robots.txt`) that tells web crawlers which parts of the site they should or should not access.

**Legal status:** Robots.txt is NOT legally binding. It is a voluntary protocol. Ignoring it is not illegal per se.

**However:**
- Respecting robots.txt is an industry-standard best practice
- Courts have referenced robots.txt compliance as evidence of good faith (or non-compliance as evidence of bad faith)
- Major search engines respect robots.txt, and your crawlers should too
- Ignoring robots.txt while scraping could be used against you in a legal dispute

**Practical approach:** Respect robots.txt directives by default. If a page is disallowed in robots.txt, don't scrape it (use alternative methods like Google's cached version, or simply skip that data).

---

## Ethical Guidelines for Competitive Intelligence

### Core Principles

1. **Collect only publicly available data.**
   - If you can see it in a regular web browser without logging in, it is fair game
   - If you need to log in, pay, or use special access, it is not

2. **Respect robots.txt directives.**
   - Check robots.txt before scraping any website
   - Honor disallowed paths
   - This is both ethical and practical (builds good faith)

3. **Do not overload target servers.**
   - Space requests out (minimum 1-2 seconds between requests to the same domain)
   - Do not make hundreds of requests per minute to a single website
   - Use caching to avoid redundant requests
   - If a server returns 429 (rate limited) or 503 (overloaded), back off immediately

4. **Do not access password-protected or private areas.**
   - Even if you have a login (e.g., a free account), do not scrape data that requires authentication
   - Competitors' admin panels, dashboards, and member areas are off limits
   - Logging in solely to scrape data may violate both ToS and CFAA

5. **Do not misrepresent yourself.**
   - Do not create fake accounts to access competitor data
   - Do not pretend to be a customer to get pricing or internal information
   - Do not impersonate competitor employees or partners
   - Your scraper's User-Agent should identify itself honestly (or use a generic browser UA)

6. **Do not scrape personal data without legal basis.**
   - GDPR (EU) and CCPA (California) regulate personal data collection
   - Collecting names, emails, and phone numbers of individuals from public sources requires a legitimate business interest
   - Always provide an opt-out mechanism when contacting collected individuals
   - Do not build databases of personal data for sale or distribution
   - Store personal data only for as long as needed

7. **Store only what you need, delete when done.**
   - Do not hoard competitor data indefinitely
   - Delete raw scraped data after extracting the analysis you need
   - Keep summaries and insights, not raw data dumps
   - Implement data retention policies

8. **Be transparent with clients.**
   - Explain to clients how competitive intelligence is gathered
   - Clarify that all data comes from public sources
   - Do not present scraped data as "insider intelligence" or imply access to private information

---

## State-Specific Considerations

### Texas

**Texas Computer Crimes Act (Penal Code Chapter 33):**
- Prohibits accessing a computer, computer network, or computer system without owner consent
- Broader than CFAA in some respects
- Public websites generally have implied consent for access (that's why they're public)
- Scraping public websites is unlikely to violate this statute

**Texas Deceptive Trade Practices Act:**
- Prohibits false, misleading, or deceptive acts in trade or commerce
- Using deceptive means to gather competitive intelligence (e.g., posing as a customer) could trigger this
- Honest public data collection is not deceptive

### California

**California Computer Data Access and Fraud Act (Penal Code 502):**
- Similar to CFAA but at the state level
- Prohibits knowingly accessing a computer without permission
- Public data access is generally not "without permission"

**CCPA (California Consumer Privacy Act):**
- Applies to businesses collecting personal data of California residents
- Requires notice of data collection, right to opt-out, right to deletion
- If you collect competitor employee data (names, emails), CCPA may apply
- Practical risk is low for small-scale competitive research, higher for systematic data collection

### European Union

**GDPR (General Data Protection Regulation):**
- Applies to personal data of EU/EEA residents, regardless of where you are located
- Requires legal basis for processing personal data (consent, legitimate interest, contract, etc.)
- If your competitive intelligence involves EU person data, GDPR applies
- For most US-focused local business competition analysis, GDPR is not relevant
- If you expand to serve EU clients or research EU competitors, consult GDPR-specific guidance

---

## Safe Data Sources for Competitive Intelligence

These sources are publicly available, widely used, and carry minimal legal risk:

### Tier 1: Fully Safe (Public APIs and Search Results)

| Source | What You Can Gather | Risk Level |
|--------|-------------------|------------|
| **Google Search (Serper)** | Competitor rankings, ad presence, featured snippets, People Also Ask | None |
| **Google Maps / Places API** | Business info, reviews, ratings, hours, photos | None |
| **Google Business Profile** | Public GBP data for any business | None |
| **Yelp (public pages)** | Reviews, ratings, business info | None |
| **BBB (public pages)** | Business profiles, ratings, complaints | None |
| **Meta Ad Library** | All active Facebook/Instagram ads from any business | None |
| **Google Ads Transparency Center** | Active Google Ads from any business | None |
| **SEC Filings (EDGAR)** | Financial data for public companies | None |
| **State business registries** | Business registration, agent info, status | None |
| **Press releases** | Company announcements, product launches, hires | None |
| **Company blogs (public)** | Content strategy, topics, frequency | None |
| **Job postings (Indeed, LinkedIn)** | Hiring patterns, growth signals, technology stack hints | None |
| **Patent databases** | Innovation activity, product direction | None |

### Tier 2: Safe with Best Practices (Public Website Scraping)

| Source | What You Can Gather | Risk Level | Best Practices |
|--------|-------------------|------------|----------------|
| **Competitor websites** | Services, pricing, content, design, technology | Low | Respect robots.txt, rate limit requests |
| **Social media public pages** | Content strategy, engagement, follower counts | Low | Don't scrape personal profiles |
| **Industry directories** | Business listings, categorizations | Low | Check ToS, use API if available |
| **Review sites** | Customer sentiment, common complaints | Low | Aggregate data, don't copy reviews |
| **News sites** | Media mentions, press coverage | Low | Don't copy articles, summarize instead |
| **BuiltWith / Wappalyzer** | Technology stack detection | Low | Uses published detection methods |

### Tier 3: Use with Caution

| Source | What You Can Gather | Risk Level | Concerns |
|--------|-------------------|------------|----------|
| **LinkedIn public profiles** | Company info, employee counts, leadership | Medium | LinkedIn ToS prohibits scraping |
| **Private directories** | Business contact data | Medium | May require login, ToS restrictions |
| **Competitor pricing pages** | Pricing strategy, packages | Medium | Some sites block scraping of pricing |
| **App store reviews** | Product feedback, competitive weaknesses | Medium | Apple/Google ToS may restrict |

### Tier 4: Avoid

| Source | What You Would Gather | Risk Level | Why Avoid |
|--------|----------------------|------------|-----------|
| **Login-required data** | Internal information | High | Potential CFAA violation |
| **Paid databases (without subscription)** | Premium data | High | Unauthorized access |
| **Private employee social media** | Personal information | High | Privacy violation |
| **Internal documents** | Trade secrets, internal strategy | Very High | Trade secret theft, potential criminal liability |
| **Customer databases** | Client lists, contacts | Very High | Trade secret theft, privacy violation |
| **Hacking / unauthorized access** | Any internal data | Illegal | Federal crime under CFAA |

---

## Polite Scraping Practices

When scraping competitor websites or public data sources, follow these technical best practices:

### Rate Limiting

```python
import time
import random

def polite_request(url, session):
    """Make a request with polite delays."""
    # Random delay between 1-3 seconds
    delay = 1 + random.random() * 2
    time.sleep(delay)

    headers = {
        'User-Agent': 'OpenClawBot/1.0 (competitive-research; contact@youragency.com)',
        'Accept': 'text/html',
    }

    response = session.get(url, headers=headers, timeout=10)

    # Respect rate limiting
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return polite_request(url, session)  # Retry once

    return response
```

### Robots.txt Compliance

```python
from urllib.robotparser import RobotFileParser

def can_scrape(url, user_agent='*'):
    """Check if scraping is allowed by robots.txt."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return True  # If robots.txt is unavailable, assume allowed
```

### Request Spacing Guidelines

| Target Type | Minimum Delay Between Requests | Notes |
|-------------|-------------------------------|-------|
| Small business website | 3-5 seconds | These may have limited hosting |
| Large corporate website | 1-2 seconds | Better infrastructure |
| API endpoints | Per API rate limits | Follow documented limits |
| Search engines (Serper) | Per plan limits | Use your API, not direct scraping |
| Review sites (Yelp, BBB) | 2-3 seconds | Watch for blocking patterns |

### Caching

Cache all scraped data to avoid redundant requests:
- Cache competitor website data for 7 days
- Cache Google/Yelp review data for 3 days
- Cache technology detection for 30 days
- Cache SERP data for 1 day

---

## Competitive Intelligence Use Cases for OpenClaw

### 1. Competitor Website Audit (for client pitches)

**What:** Analyze a client's top 3-5 competitors' websites for strengths and weaknesses.

**Data collected (all public):**
- Website design quality and modernity
- Technology stack (CMS, analytics, ads, chat)
- SEO metrics (ranking keywords, domain authority, page speed)
- Content strategy (blog frequency, topics, depth)
- Conversion elements (CTAs, forms, chat, booking)
- Mobile responsiveness
- Local SEO signals (NAP, structured data, local content)

**Legal status:** Fully legal. All data from public websites and public APIs.

### 2. SERP Competitive Analysis

**What:** Analyze who ranks for the client's target keywords and why.

**Data collected:**
- Top 10 results for each target keyword (via Serper or DataForSEO)
- Competitor domain authority and backlink profiles
- Content type ranking (blog posts, service pages, directories)
- SERP features present (local pack, featured snippet, People Also Ask)
- Ad presence and estimated ad spend

**Legal status:** Fully legal. All data from search engine APIs.

### 3. Review Sentiment Analysis

**What:** Analyze competitor reviews to understand their strengths and weaknesses.

**Data collected:**
- Google review text, ratings, and dates
- Yelp review text, ratings, and dates
- Common praise themes (e.g., "fast response", "fair pricing")
- Common complaint themes (e.g., "expensive", "poor communication")
- Response patterns (do they respond to reviews?)

**Legal status:** Fully legal. Reviews are public data.

### 4. Advertising Intelligence

**What:** See what competitors are advertising and where.

**Data collected:**
- Google Ads: keywords they bid on (estimated via DataForSEO), ad copy visible in SERPs
- Facebook/Instagram Ads: all active ads visible in Meta Ad Library
- Ad spending estimates (rough, via third-party tools)
- Landing page analysis (where ads point to)

**Legal status:** Fully legal. Meta Ad Library and Google Ads Transparency Center are explicitly designed for public transparency. SERP ad data is public.

### 5. Content Gap Analysis

**What:** Identify content topics competitors cover that the client does not.

**Data collected:**
- Competitor blog posts and content pages (public URLs and titles)
- Topics covered and keyword targeting
- Content depth and quality assessment
- Publishing frequency

**Legal status:** Fully legal. Published content is public.

---

## Data Handling and Retention

### Collection Principles

1. **Minimize:** Collect only the data you need for the specific analysis
2. **Anonymize:** Where possible, work with aggregate data rather than individual records
3. **Secure:** Store collected data securely, restrict access to authorized personnel
4. **Expire:** Delete raw scraped data after analysis is complete
5. **Document:** Keep records of what was collected, from where, and when

### Retention Schedule

| Data Type | Retention Period | Reason |
|-----------|-----------------|--------|
| Competitor website screenshots | 30 days | Design comparison |
| SERP rankings data | 12 months | Trend tracking |
| Review data | 6 months | Sentiment tracking |
| Technology stack data | 6 months | Change tracking |
| Ad intelligence | 3 months | Campaign tracking |
| Raw scraped HTML | 7 days | Processing only, then delete |
| Competitive analysis reports | Indefinitely | Client deliverable |

### Handling Requests

If a competitor contacts you about data collection:
1. Respond professionally and promptly
2. Explain that you only collected publicly available data
3. Offer to remove any specific data they object to
4. Do not escalate or argue
5. Consult an attorney if they threaten legal action

---

## Practical Recommendations for OpenClaw

### Always Use

- Google Search API (Serper) for SERP analysis
- Google Places API for competitor business data
- DataForSEO for SEO metrics and keyword data
- Meta Ad Library API for Facebook/Instagram ad intelligence
- BuiltWith/Wappalyzer for technology detection
- Public website scraping with robots.txt compliance and rate limiting

### Use with Best Practices

- Competitor website scraping (respect robots.txt, rate limit, cache aggressively)
- Public social media page data (follower counts, post frequency -- not personal profiles)
- Review site data (aggregate analysis, not copying individual reviews)

### Avoid

- Scraping LinkedIn profiles (use official API or manual research)
- Accessing any data behind a login
- Creating fake accounts to access competitor information
- Copying competitor creative content (images, ad copy, design elements)
- Building databases of personal information about competitor employees
- Any activity that feels deceptive or that you would not want to explain to a client or a court

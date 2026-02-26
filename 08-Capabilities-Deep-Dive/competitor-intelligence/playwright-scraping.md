# Playwright Scraping for Competitive Intelligence

## Overview

Playwright is a browser automation framework that drives real browsers (Chromium, Firefox, WebKit) programmatically. For competitive intelligence, it is the tool of choice because competitor websites, Google Maps listings, review sites, and social media profiles all rely heavily on JavaScript rendering. Simple HTTP request libraries (like `requests` in Python or `axios` in Node) only fetch raw HTML and miss dynamically loaded content entirely. Playwright executes JavaScript just like a real user's browser, ensuring you capture the full page.

OpenClaw wraps Playwright automations as callable skills so that the AI agent can trigger scraping runs on demand or on a schedule, then pipe the extracted data into Supabase and Airtable for analysis and client reporting.

---

## Installation

### Node.js

```bash
npm install playwright
```

After installation, download browsers:

```bash
npx playwright install
```

This installs Chromium, Firefox, and WebKit binaries. To install only Chromium (sufficient for most scraping):

```bash
npx playwright install chromium
```

### Python

```bash
pip install playwright
python -m playwright install
```

### Stealth Plugin (Recommended)

For Node.js, install the stealth plugin to reduce detection:

```bash
npm install playwright-extra puppeteer-extra-plugin-stealth
```

---

## Why Playwright Over Alternatives

| Feature | Playwright | Puppeteer | Selenium | HTTP (requests/axios) |
|---|---|---|---|---|
| JS-rendered content | Yes | Yes | Yes | No |
| Multi-browser | Chromium, Firefox, WebKit | Chromium only | All (via drivers) | N/A |
| Speed | Fast | Fast | Slower | Fastest |
| Auto-wait for elements | Built-in | Manual | Manual | N/A |
| Headless mode | Yes | Yes | Yes | N/A |
| Screenshot/PDF capture | Built-in | Built-in | Limited | No |
| Maintained by | Microsoft | Google | Selenium Project | N/A |
| Language support | JS, Python, C#, Java | JS only | All major | All major |

**Key advantages for competitive intelligence:**

1. **JavaScript rendering** -- Competitor websites use React, Vue, Angular, or other frameworks. Pricing tables, testimonials, team bios, and service descriptions are often loaded dynamically. Playwright renders all of it.
2. **Multi-browser testing** -- Some sites render differently across browsers. WebKit support lets you see the Safari version.
3. **Built-in waiting** -- `page.waitForSelector()`, `page.waitForLoadState()`, and auto-wait on actions mean fewer race conditions and more reliable data extraction.
4. **Screenshots** -- Capture visual snapshots of competitor pages for change-monitoring archives and client reports.
5. **Network interception** -- Intercept API calls that competitor sites make to their backends, which sometimes expose structured data (pricing JSON, review data) that is easier to parse than HTML.

---

## Common Scraping Patterns

### 1. Business Website: Services, Pricing, Team, Testimonials

**Goal:** Extract what a competitor offers, how they price it, who works there, and what clients say.

```javascript
const { chromium } = require('playwright');

async function scrapeCompetitorWebsite(url) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  await page.goto(url, { waitUntil: 'networkidle' });

  // Extract page title and meta description
  const title = await page.title();
  const metaDescription = await page.$eval(
    'meta[name="description"]',
    el => el.getAttribute('content')
  ).catch(() => null);

  // Extract all headings for content structure
  const headings = await page.$$eval('h1, h2, h3', elements =>
    elements.map(el => ({
      tag: el.tagName,
      text: el.textContent.trim()
    }))
  );

  // Extract pricing (common patterns)
  const pricingData = await page.$$eval(
    '[class*="price"], [class*="pricing"], [data-price]',
    elements => elements.map(el => el.textContent.trim())
  ).catch(() => []);

  // Extract team members
  const teamMembers = await page.$$eval(
    '[class*="team"] [class*="member"], [class*="team"] [class*="card"]',
    elements => elements.map(el => ({
      name: el.querySelector('h3, h4, [class*="name"]')?.textContent?.trim(),
      role: el.querySelector('[class*="title"], [class*="role"], [class*="position"]')?.textContent?.trim()
    }))
  ).catch(() => []);

  // Extract testimonials
  const testimonials = await page.$$eval(
    '[class*="testimonial"], [class*="review"], blockquote',
    elements => elements.map(el => ({
      text: el.querySelector('p, [class*="text"], [class*="quote"]')?.textContent?.trim(),
      author: el.querySelector('[class*="author"], [class*="name"], cite')?.textContent?.trim()
    }))
  ).catch(() => []);

  // Extract contact info
  const pageText = await page.textContent('body');
  const emails = pageText.match(/[\w.-]+@[\w.-]+\.\w+/g) || [];
  const phones = pageText.match(/\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g) || [];

  // Take a screenshot for the archive
  await page.screenshot({ path: `screenshots/${new URL(url).hostname}-${Date.now()}.png`, fullPage: true });

  await browser.close();

  return {
    url,
    title,
    metaDescription,
    headings,
    pricingData,
    teamMembers,
    testimonials,
    contactInfo: { emails: [...new Set(emails)], phones: [...new Set(phones)] },
    scrapedAt: new Date().toISOString()
  };
}
```

**Navigating multi-page sites:** Many competitor websites spread information across `/services`, `/pricing`, `/about`, `/testimonials`, and `/contact` pages. Build a sitemap crawler first:

```javascript
async function discoverPages(baseUrl, page) {
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  const links = await page.$$eval('a[href]', (anchors, base) => {
    return anchors
      .map(a => new URL(a.href, base).href)
      .filter(href => href.startsWith(base) && !href.includes('#'))
      .filter((href, i, arr) => arr.indexOf(href) === i);
  }, baseUrl);
  return links;
}
```

### 2. Google Maps: Reviews, Ratings, Photos, Q&A, Popular Times

**Goal:** Track a competitor's local reputation, review velocity, and customer sentiment.

```javascript
async function scrapeGoogleMapsListing(placeUrl) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(placeUrl, { waitUntil: 'networkidle' });

  // Wait for the main content to load
  await page.waitForSelector('[data-attrid="title"], h1', { timeout: 10000 });

  // Extract business name
  const businessName = await page.$eval(
    'h1',
    el => el.textContent.trim()
  ).catch(() => null);

  // Extract overall rating
  const rating = await page.$eval(
    '[class*="rating"] span, [aria-label*="stars"]',
    el => el.textContent.trim()
  ).catch(() => null);

  // Extract review count
  const reviewCount = await page.$eval(
    'button[aria-label*="reviews"], [class*="review"] span',
    el => {
      const match = el.textContent.match(/[\d,]+/);
      return match ? parseInt(match[0].replace(',', '')) : null;
    }
  ).catch(() => null);

  // Scroll through reviews to load more
  const reviewsTab = await page.$('button[aria-label*="Reviews"]');
  if (reviewsTab) {
    await reviewsTab.click();
    await page.waitForTimeout(2000);

    // Scroll the reviews panel to load more
    for (let i = 0; i < 5; i++) {
      await page.evaluate(() => {
        const scrollable = document.querySelector('[class*="review"]')?.closest('[role="main"]');
        if (scrollable) scrollable.scrollTop += 1000;
      });
      await page.waitForTimeout(1500);
    }
  }

  // Extract individual reviews
  const reviews = await page.$$eval(
    '[data-review-id], [class*="review-card"]',
    elements => elements.slice(0, 20).map(el => ({
      author: el.querySelector('[class*="author"], [class*="name"]')?.textContent?.trim(),
      rating: el.querySelector('[aria-label*="star"]')?.getAttribute('aria-label'),
      text: el.querySelector('[class*="text"], [class*="body"]')?.textContent?.trim(),
      date: el.querySelector('[class*="date"], [class*="time"]')?.textContent?.trim()
    }))
  ).catch(() => []);

  await browser.close();

  return { businessName, rating, reviewCount, reviews, scrapedAt: new Date().toISOString() };
}
```

**Important:** Google Maps is heavily dynamic. Selectors change frequently. Maintain a selector configuration file that you can update without changing the core scraping logic:

```json
{
  "googleMaps": {
    "businessName": "h1",
    "rating": "[class*='rating'] span",
    "reviewCount": "button[aria-label*='reviews']",
    "reviewCard": "[data-review-id]",
    "lastUpdated": "2026-01-15"
  }
}
```

### 3. Yelp / BBB: Reviews, Ratings, Complaints, Accreditation

**Goal:** Assess competitor reputation on review platforms and check for unresolved complaints.

```javascript
async function scrapeYelpListing(yelpUrl) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(yelpUrl, { waitUntil: 'networkidle' });

  const businessName = await page.$eval('h1', el => el.textContent.trim()).catch(() => null);

  const rating = await page.$eval(
    '[class*="five-stars"], [aria-label*="star rating"]',
    el => el.getAttribute('aria-label') || el.textContent.trim()
  ).catch(() => null);

  const reviewCount = await page.$eval(
    'a[href*="review_count"], [class*="review-count"]',
    el => el.textContent.trim()
  ).catch(() => null);

  const categories = await page.$$eval(
    '[class*="category"] a, a[href*="/biz_photos"]',
    elements => elements.map(el => el.textContent.trim())
  ).catch(() => []);

  // Extract recent reviews
  const reviews = await page.$$eval(
    '[class*="review__"], li[class*="review"]',
    elements => elements.slice(0, 10).map(el => ({
      author: el.querySelector('[class*="user-name"], a[href*="/user_details"]')?.textContent?.trim(),
      rating: el.querySelector('[aria-label*="star"]')?.getAttribute('aria-label'),
      text: el.querySelector('p[class*="comment"], span[class*="raw"]')?.textContent?.trim(),
      date: el.querySelector('[class*="date"], span[class*="date"]')?.textContent?.trim()
    }))
  ).catch(() => []);

  await browser.close();

  return { businessName, rating, reviewCount, categories, reviews, source: 'yelp', scrapedAt: new Date().toISOString() };
}
```

**BBB-specific data points:** accreditation status (Yes/No), BBB rating (A+ through F), complaint count, complaint resolution rate, years in business. These are structured elements on the BBB profile page.

### 4. Social Media: Public Posts, Follower Counts, Engagement

**Goal:** Track competitor social media activity and performance.

```javascript
async function scrapePublicSocialProfile(profileUrl) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(profileUrl, { waitUntil: 'networkidle' });

  // Generic extraction -- adapt selectors per platform
  const followerCount = await page.$eval(
    '[title*="followers"], [class*="follower"] span, a[href*="followers"]',
    el => el.textContent.trim()
  ).catch(() => null);

  const postCount = await page.$eval(
    '[class*="post-count"], [title*="posts"]',
    el => el.textContent.trim()
  ).catch(() => null);

  // Extract recent public posts (Facebook pages, LinkedIn company pages)
  const recentPosts = await page.$$eval(
    '[class*="post"], [data-testid*="post"], article',
    elements => elements.slice(0, 5).map(el => ({
      text: el.querySelector('p, [class*="text"], [class*="content"]')?.textContent?.trim()?.substring(0, 500),
      engagement: el.querySelector('[class*="like"], [class*="reaction"]')?.textContent?.trim(),
      date: el.querySelector('time, [class*="timestamp"]')?.getAttribute('datetime') ||
            el.querySelector('time, [class*="timestamp"]')?.textContent?.trim()
    }))
  ).catch(() => []);

  await browser.close();

  return { profileUrl, followerCount, postCount, recentPosts, scrapedAt: new Date().toISOString() };
}
```

**Platform-specific notes:**
- **Facebook Pages:** Public pages are scrapable. Use `facebook.com/{page}/posts` for the feed.
- **LinkedIn Company Pages:** Public company pages show follower count, recent posts, employee count, and recent hires. Login walls may appear after a few pages -- rotate contexts.
- **Instagram:** Public profiles show post count, follower/following counts, and recent post thumbnails. Full post data requires scrolling and expanding.
- **Twitter/X:** Public profiles show follower counts and recent tweets. The platform aggressively rate-limits and requires login for deeper access.

### 5. Job Boards: Hiring Activity as a Growth Signal

**Goal:** Track what positions a competitor is hiring for, which indicates growth areas, new service lines, or internal challenges (high turnover roles).

```javascript
async function scrapeJobPostings(companyName) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Search Indeed for company job postings
  const searchUrl = `https://www.indeed.com/jobs?q=${encodeURIComponent(companyName)}&sort=date`;
  await page.goto(searchUrl, { waitUntil: 'networkidle' });

  const jobs = await page.$$eval(
    '.job_seen_beacon, [class*="jobCard"]',
    elements => elements.slice(0, 15).map(el => ({
      title: el.querySelector('h2 a, [class*="jobTitle"] a')?.textContent?.trim(),
      location: el.querySelector('[class*="companyLocation"], [class*="location"]')?.textContent?.trim(),
      snippet: el.querySelector('[class*="snippet"], [class*="description"]')?.textContent?.trim(),
      datePosted: el.querySelector('[class*="date"], [class*="posted"]')?.textContent?.trim(),
      link: el.querySelector('h2 a, [class*="jobTitle"] a')?.href
    }))
  ).catch(() => []);

  await browser.close();

  return {
    companyName,
    jobCount: jobs.length,
    jobs,
    hiringSignals: analyzeHiringSignals(jobs),
    scrapedAt: new Date().toISOString()
  };
}

function analyzeHiringSignals(jobs) {
  const signals = [];
  const titles = jobs.map(j => j.title?.toLowerCase() || '');

  if (titles.some(t => t.includes('sales') || t.includes('account executive'))) {
    signals.push('Expanding sales team -- likely pursuing growth');
  }
  if (titles.some(t => t.includes('developer') || t.includes('engineer'))) {
    signals.push('Hiring technical talent -- building or scaling product');
  }
  if (titles.some(t => t.includes('marketing') || t.includes('content'))) {
    signals.push('Investing in marketing -- likely increasing ad spend or content');
  }
  if (titles.some(t => t.includes('manager') || t.includes('director') || t.includes('vp'))) {
    signals.push('Hiring leadership -- organizational growth or restructuring');
  }
  if (jobs.length > 10) {
    signals.push('High volume hiring -- rapid growth phase');
  }

  return signals;
}
```

---

## Anti-Detection Best Practices

Scraping competitor websites requires care to avoid being blocked. These are not optional -- without them, scrapes will fail within days.

### 1. Rotate User Agents

```javascript
const userAgents = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/17.2'
];

const context = await browser.newContext({
  userAgent: userAgents[Math.floor(Math.random() * userAgents.length)],
  viewport: { width: 1920, height: 1080 },
  locale: 'en-US',
  timezoneId: 'America/New_York'
});
```

### 2. Add Realistic Delays

```javascript
// Random delay between 1-3 seconds between actions
async function humanDelay() {
  const delay = 1000 + Math.random() * 2000;
  await page.waitForTimeout(delay);
}

// Random delay between page navigations (3-7 seconds)
async function navigationDelay() {
  const delay = 3000 + Math.random() * 4000;
  await page.waitForTimeout(delay);
}
```

### 3. Use Stealth Plugin

```javascript
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const browser = await chromium.launch({ headless: true });
// Stealth plugin patches common detection vectors:
// - navigator.webdriver flag
// - Chrome DevTools Protocol detection
// - Headless Chrome indicators
// - WebGL vendor/renderer strings
```

### 4. Respect Rate Limits

- **Maximum 1 request per 3 seconds** to any single domain.
- **Maximum 50 pages per session** for Google properties.
- **Rotate IP addresses** using a proxy service if scraping at scale.
- **Back off on errors** -- if you get a 429 (rate limited) or CAPTCHA, wait 5-10 minutes before retrying.

```javascript
const rateLimiter = {
  lastRequest: {},
  async wait(domain, minDelayMs = 3000) {
    const now = Date.now();
    const last = this.lastRequest[domain] || 0;
    const elapsed = now - last;
    if (elapsed < minDelayMs) {
      await new Promise(resolve => setTimeout(resolve, minDelayMs - elapsed));
    }
    this.lastRequest[domain] = Date.now();
  }
};
```

---

## Data Extraction Techniques

### CSS Selectors

```javascript
// By class
const price = await page.$eval('.pricing-amount', el => el.textContent);

// By attribute
const rating = await page.$eval('[itemprop="ratingValue"]', el => el.content);

// By combined selectors
const serviceNames = await page.$$eval('.services-grid .card h3', els => els.map(el => el.textContent.trim()));
```

### XPath (When CSS Is Insufficient)

```javascript
// Find element containing specific text
const element = await page.$('xpath=//div[contains(text(), "Starting at")]');
const pricingText = await element?.textContent();

// Find element by complex hierarchy
const reviews = await page.$$('xpath=//div[@class="reviews"]//article');
```

### Structured Data Extraction

Many business websites embed structured data (JSON-LD, Microdata) that is easier to parse than HTML:

```javascript
async function extractStructuredData(page) {
  const jsonLd = await page.$$eval(
    'script[type="application/ld+json"]',
    scripts => scripts.map(s => {
      try { return JSON.parse(s.textContent); }
      catch { return null; }
    }).filter(Boolean)
  );
  return jsonLd; // May contain LocalBusiness, Organization, Product schemas
}
```

### Network Interception

Some sites load data via API calls that return clean JSON:

```javascript
const apiResponses = [];
page.on('response', async response => {
  const url = response.url();
  if (url.includes('/api/') || url.includes('/graphql')) {
    try {
      const json = await response.json();
      apiResponses.push({ url, data: json });
    } catch {}
  }
});

await page.goto(targetUrl, { waitUntil: 'networkidle' });
// apiResponses now contains any JSON API calls the page made
```

---

## Error Handling

### Timeouts

```javascript
try {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
} catch (error) {
  if (error.message.includes('Timeout')) {
    console.log(`Timeout loading ${url} -- retrying with domcontentloaded`);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  }
}
```

### CAPTCHA Detection

```javascript
async function detectCaptcha(page) {
  const captchaIndicators = [
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    '[class*="captcha"]',
    '#challenge-running',  // Cloudflare
    '[id*="captcha"]'
  ];

  for (const selector of captchaIndicators) {
    if (await page.$(selector)) {
      return true;
    }
  }
  return false;
}

// In your scraping flow:
if (await detectCaptcha(page)) {
  console.log('CAPTCHA detected -- backing off');
  await browser.close();
  // Log the failure, alert the operator, try again later
  return { error: 'captcha', url, timestamp: new Date().toISOString() };
}
```

### Blocked Requests

```javascript
page.on('response', response => {
  if (response.status() === 403 || response.status() === 429) {
    console.log(`Blocked/rate-limited: ${response.url()} (${response.status()})`);
  }
});
```

### Retry Logic

```javascript
async function scrapeWithRetry(url, scrapeFn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await scrapeFn(url);
    } catch (error) {
      console.log(`Attempt ${attempt} failed for ${url}: ${error.message}`);
      if (attempt < maxRetries) {
        const backoff = attempt * 5000 + Math.random() * 5000;
        await new Promise(resolve => setTimeout(resolve, backoff));
      } else {
        return { error: error.message, url, attempts: maxRetries };
      }
    }
  }
}
```

---

## Scheduling

### Via n8n (Recommended for OpenClaw)

Create an n8n workflow with:

1. **Schedule Trigger** -- Runs daily at 6 AM.
2. **Function Node** -- Generates the list of competitor URLs to scrape from Supabase.
3. **HTTP Request / Code Node** -- Calls a Playwright scraping microservice or runs inline code.
4. **Supabase Node** -- Stores the scraped data as a new snapshot.
5. **IF Node** -- Checks if any significant changes were detected compared to the previous snapshot.
6. **Notification Node** -- Sends alerts (email, Slack) for significant changes.

### Via Cron (Simpler Alternative)

```bash
# Run competitor scrape daily at 6 AM
0 6 * * * cd /path/to/scraper && node scrape-all-competitors.js >> /var/log/scraper.log 2>&1
```

---

## Output Format

All scraping functions should return structured JSON that matches the Supabase schema defined in `data-storage.md`:

```json
{
  "competitor_id": "uuid-here",
  "snapshot_date": "2026-02-05",
  "source": "website",
  "data": {
    "website": {
      "title": "Competitor Name - Best Marketing Agency",
      "services": ["SEO", "PPC", "Social Media", "Web Design"],
      "pricing": ["Starting at $999/mo", "Custom packages available"],
      "teamSize": 12,
      "testimonialCount": 24
    },
    "googleMaps": {
      "rating": 4.7,
      "reviewCount": 156,
      "recentReviews": []
    },
    "social": {
      "facebook": { "followers": 5200, "postsThisMonth": 8 },
      "instagram": { "followers": 3100, "postsThisMonth": 12 }
    },
    "hiring": {
      "openPositions": 3,
      "roles": ["SEO Specialist", "Account Manager", "Content Writer"]
    }
  },
  "scrapedAt": "2026-02-05T06:00:00Z"
}
```

This JSON is stored in the `competitor_snapshots.data` JSONB column in Supabase.

---

## Integration with OpenClaw

OpenClaw exposes Playwright scraping as a skill:

- **Skill name:** `competitor_scrape`
- **Parameters:** `competitor_id` (UUID), `sources` (array: `["website", "google_maps", "yelp", "social", "jobs"]`)
- **Behavior:** Runs the appropriate scraping functions, stores results in Supabase, triggers change detection (see `change-monitoring.md`), and returns a summary.
- **Invocation example:** "Scrape all data sources for competitor ABC Marketing and alert me to any changes since last week."

The skill handles browser lifecycle, error recovery, and data storage internally. The agent only needs to specify what to scrape and for whom.

---

## Legal and Ethical Considerations

**This section is critical. Violating these guidelines creates legal risk for the agency and its clients.**

1. **Always check `robots.txt`** before scraping any site. If a path is disallowed, do not scrape it.
2. **Respect Terms of Service** -- Google, Yelp, LinkedIn, and Facebook all prohibit automated scraping in their ToS. Understand the risk.
3. **Scrape only publicly available data** -- never attempt to bypass login walls, paywalls, or access controls.
4. **Do not overload servers** -- rate-limit all requests, use reasonable delays, and stop immediately if a site appears to be struggling.
5. **Do not store personal data** beyond what is publicly displayed (e.g., individual reviewer names from public reviews are acceptable; scraping private user profiles is not).
6. **Document your scraping practices** for each client engagement so there is a clear record of what was collected and how.
7. **See `legal-ethical.md`** in this section for the full legal analysis, including CFAA considerations, the hiQ v. LinkedIn precedent, and GDPR implications for international competitors.

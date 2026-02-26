# LinkedIn Official API Capabilities

## Overview

LinkedIn offers several official API products, each targeting different use cases. Using official APIs is the only zero-risk way to interact with LinkedIn programmatically. However, the APIs are limited in scope compared to what you can do manually in the LinkedIn interface. This document catalogs every available API product, what it can and cannot do, how to get access, and how to integrate it with OpenClaw.

---

## API Products

### 1. Sign In with LinkedIn (OpenID Connect)

**Purpose:** Allow users to authenticate with your application using their LinkedIn credentials.

**What it provides:**
- User authentication via OAuth 2.0
- Basic profile data: first name, last name, email address, profile picture
- OpenID Connect standard compliance

**Use case for your agency:**
- Not directly useful for lead generation or outreach
- Could be useful if building a client portal where clients log in via LinkedIn

**Access:** Available to all registered LinkedIn applications. No special review required.

**API endpoints:**
```
Authorization: https://www.linkedin.com/oauth/v2/authorization
Token: https://www.linkedin.com/oauth/v2/accessToken
UserInfo: https://api.linkedin.com/v2/userinfo
```

---

### 2. Share on LinkedIn API

**Purpose:** Post content to LinkedIn from your application.

**What it provides:**
- Create posts on personal profiles (with user authorization)
- Create posts on company/organization pages
- Share text, images, articles, and videos
- Delete posts you created via API

**What it does NOT provide:**
- Like, comment on, or share other people's posts
- Read feed or timeline data
- Access to post analytics (separate API)

**Use case for your agency:**
- **Content automation:** Schedule and publish thought leadership posts for your agency's LinkedIn presence
- **Client social management:** If you manage clients' LinkedIn company pages, automate posting
- **Authority building:** Regularly share industry insights, tips, case studies

**Access:** Requires LinkedIn Developer application with "Share on LinkedIn" product approved. Generally easy to get.

**API endpoints:**
```
Create Post: POST https://api.linkedin.com/v2/posts
Delete Post: DELETE https://api.linkedin.com/v2/posts/{post-id}
Upload Image: POST https://api.linkedin.com/v2/images?action=initializeUpload
Upload Video: POST https://api.linkedin.com/v2/videos?action=initializeUpload
```

**Example post creation:**
```json
POST /v2/posts
{
  "author": "urn:li:organization:12345",
  "commentary": "5 signs your plumbing business needs a marketing upgrade...",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED"
  },
  "lifecycleState": "PUBLISHED"
}
```

**OpenClaw integration:**
```
Tool: linkedin_post
Input: content_text, image_url (optional), organization_id (for company page)
Output: post_id, post_url
```

---

### 3. Marketing APIs

**Purpose:** Manage LinkedIn advertising campaigns programmatically.

**Sub-products:**

**Campaign Management:**
- Create, read, update, delete ad campaigns
- Manage campaign groups
- Set budgets, schedules, targeting
- Manage creative assets

**Audience Management:**
- Create matched audiences (email lists, company lists, website retargeting)
- Create lookalike audiences
- Manage audience segments

**Reporting and Analytics:**
- Campaign performance metrics (impressions, clicks, conversions, spend)
- Audience insights
- Conversion tracking

**Lead Gen Forms:**
- Access leads submitted via LinkedIn Lead Gen Forms
- Download lead data (name, email, company, job title, form answers)
- Sync leads to CRM

**What it does NOT provide:**
- Organic post analytics (separate product)
- Personal profile engagement data
- Competitor ad data

**Use case for your agency:**
- If you manage LinkedIn Ads for clients, automate campaign management
- Sync LinkedIn Lead Gen Form submissions to your CRM/pipeline
- Automate reporting for LinkedIn ad performance

**Access:** Requires LinkedIn Marketing Developer Platform agreement. Application review process can take 2-4 weeks. Must demonstrate legitimate advertising use case.

**Rate limits:** Vary by endpoint, generally 100-500 requests per day per application.

**Cost:** API access is free, but you pay for the ads themselves (CPC/CPM).

---

### 4. Sales Navigator API

**Purpose:** Programmatic access to LinkedIn Sales Navigator features.

**What it provides:**
- **Lead search:** Search for people matching criteria (industry, title, company size, location)
- **Account search:** Search for companies matching criteria
- **Lead recommendations:** AI-suggested leads based on your saved criteria
- **Lead/account saves:** Save leads and accounts to lists programmatically
- **CRM sync:** Two-way sync between Sales Navigator and CRM (Salesforce, HubSpot, MS Dynamics)
- **InMail status:** Check InMail credit balance and message status

**What it does NOT provide:**
- Send connection requests
- Send InMail messages via API (must use UI or Sales Navigator platform)
- Download profile data at scale (limited fields returned)
- Bypass search limits

**Use case for your agency:**
- **Lead discovery:** Find decision-makers at target companies matching your ICP
- **Contact enrichment:** Get LinkedIn profile data for leads in your pipeline
- **CRM integration:** Keep sales tools in sync with LinkedIn data

**Access requirements:**
- Active Sales Navigator subscription (Core: $99/month, Advanced: $149/month)
- Partnership agreement with LinkedIn for API access
- Not available to individual developers -- requires business relationship with LinkedIn

**This is the most restricted API.** Getting access typically requires being a LinkedIn partner or using an approved CRM integration (Salesforce, HubSpot, etc. already have this built in).

**Practical alternative:** If you cannot get direct API access, use Sales Navigator through its web interface and have OpenClaw assist with research and message drafting rather than direct API calls.

---

### 5. Company Pages API (Organization API)

**Purpose:** Manage LinkedIn Company/Organization pages.

**What it provides:**
- Read company page information (name, description, industry, size, logo)
- Read company page statistics (follower count, page views, visitor demographics)
- Post content to company page (via Share API)
- Read posts and their engagement (likes, comments, shares)
- Manage company page administrators

**What it does NOT provide:**
- Read other companies' page statistics
- Access competitor company data
- Post to personal profiles of administrators
- Message followers directly

**Use case for your agency:**
- Manage your agency's LinkedIn company page
- Post content, track engagement, grow following
- If managing client company pages, automate content posting

**Access:** Requires "Company Pages" product on your LinkedIn application. You must be an admin of the company page.

---

### 6. Community Management API

**Purpose:** Manage LinkedIn groups and community interactions.

**What it provides:**
- Create and manage LinkedIn groups
- Post to groups
- Moderate group content
- Read group membership and activity

**Use case for your agency:** Minimal. LinkedIn groups are not a high-impact marketing channel for local businesses. Low priority.

---

## Getting API Access

### Step 1: Create a LinkedIn Developer Application

1. Go to https://developer.linkedin.com/
2. Click "Create App"
3. Fill in application details:
   - App name (e.g., "OpenClaw Agency Platform")
   - LinkedIn company page (must have admin access)
   - App logo
   - Legal agreement acceptance
4. Application is created with basic permissions

### Step 2: Request API Products

Each API product must be individually requested:
1. In the developer portal, go to your app's "Products" tab
2. Select the product you need (e.g., "Share on LinkedIn", "Marketing APIs")
3. Some products grant instant access, others require review
4. Review process: 2-4 weeks, may require additional documentation

### Step 3: Configure OAuth 2.0

**OAuth 2.0 flow:**
```
1. Redirect user to LinkedIn authorization URL:
   https://www.linkedin.com/oauth/v2/authorization?
     response_type=code&
     client_id={client_id}&
     redirect_uri={redirect_uri}&
     scope=openid%20profile%20email%20w_member_social

2. User authorizes your app on LinkedIn

3. LinkedIn redirects to your redirect_uri with authorization code:
   https://yourdomain.com/callback?code={auth_code}

4. Exchange code for access token:
   POST https://www.linkedin.com/oauth/v2/accessToken
   Body: grant_type=authorization_code&code={auth_code}&
         client_id={client_id}&client_secret={client_secret}&
         redirect_uri={redirect_uri}

5. Response includes access_token (valid for 60 days)
   and refresh_token (valid for 365 days)
```

**Scopes available:**
| Scope | Access |
|-------|--------|
| `openid` | OpenID Connect authentication |
| `profile` | Basic profile (name, picture) |
| `email` | Email address |
| `w_member_social` | Post content on behalf of user |
| `r_organization_social` | Read company page data |
| `w_organization_social` | Post to company pages |
| `rw_organization_admin` | Manage company page admin settings |
| `r_ads` | Read ad account data |
| `rw_ads` | Manage ad campaigns |
| `r_liteprofile` | Basic profile for Sign In |

---

## Rate Limits

| API Product | Limit Type | Limit |
|-------------|-----------|-------|
| Share API | Daily limit | 100 posts/day per organization |
| Profile API | Daily limit | 500 requests/day per app |
| Company Pages API | Daily limit | 500 requests/day per app |
| Marketing APIs | Daily limit | 100-1000 requests/day (varies by endpoint) |
| Image upload | Daily limit | 100 uploads/day |

**Rate limit headers:**
```
X-Li-RateLimit-Limit: 500
X-Li-RateLimit-Remaining: 487
X-Li-RateLimit-Reset: 1706745600
```

Monitor these headers to avoid hitting limits. Implement exponential backoff on 429 responses.

---

## What You CAN Do via Official API

| Capability | API Product | Notes |
|-----------|-------------|-------|
| Post text/image/video to company page | Share API | Great for content marketing |
| Read company page analytics | Company Pages API | Track follower growth, engagement |
| Create LinkedIn ad campaigns | Marketing APIs | Full ad management |
| Download Lead Gen Form submissions | Marketing APIs | Sync leads to CRM |
| Search for people (Sales Navigator) | Sales Navigator API | Requires partnership |
| Authenticate users via LinkedIn | Sign In with LinkedIn | For web applications |

---

## What You CANNOT Do via Official API

| Desired Action | Status | Alternative |
|---------------|--------|-------------|
| Send connection requests | Not available | Manual via LinkedIn UI |
| Send direct messages | Not available | Manual via LinkedIn UI |
| Send InMail | Not available (API reads only) | Sales Navigator UI |
| Like or comment on posts | Not available | Manual or semi-automated |
| Scrape profiles at scale | Not available | Clay.com, Apollo.io |
| View who visited your profile | Not available | Sales Navigator UI |
| Search people (without Sales Nav) | Not available | Sales Navigator subscription |
| Export connections list | Not available | LinkedIn settings (manual CSV) |
| Automate engagement | Not available | Manual with OpenClaw drafting |

---

## Cost Summary

| Component | Cost | Notes |
|-----------|------|-------|
| LinkedIn Developer API access | Free | No charge for API usage itself |
| LinkedIn Company Page | Free | Must have company page |
| Sales Navigator Core | $99/month | Required for advanced search |
| Sales Navigator Advanced | $149/month | Team features, CRM sync |
| Sales Navigator API | Partnership required | Not available to all |
| LinkedIn Ads | CPC/CPM based | Typically $5-15 CPC for B2B |
| Premium Career/Business | $30-60/month | Not required for API |

**Recommendation for your agency:**
- Start with free API access (Share API + Company Pages)
- Add Sales Navigator Core ($99/month) if B2B lead generation becomes a priority
- Skip LinkedIn Ads unless you have clients specifically wanting LinkedIn advertising

---

## Integration with OpenClaw

### LinkedIn Posting Tool
```
Tool: linkedin_create_post
Authentication: OAuth 2.0 access token (stored securely)
Parameters:
  - content: string (post text)
  - image_url: string (optional, image to attach)
  - organization_id: string (company page URN)
  - visibility: "PUBLIC" | "CONNECTIONS"
Returns:
  - post_id: string
  - post_url: string
```

### LinkedIn Analytics Tool
```
Tool: linkedin_page_analytics
Authentication: OAuth 2.0 access token
Parameters:
  - organization_id: string
  - date_range: { start: date, end: date }
  - metrics: ["followerCount", "pageViews", "uniqueVisitors"]
Returns:
  - metrics data by date
```

### Content Calendar Automation
OpenClaw can manage a LinkedIn content calendar:
1. Generate weekly content ideas based on industry trends and agency expertise
2. Draft posts with AI-written copy
3. Schedule posts via the Share API (or queue for human review)
4. Track engagement via Company Pages API
5. Adjust content strategy based on what performs well

This is fully within LinkedIn's official API capabilities and carries zero risk.

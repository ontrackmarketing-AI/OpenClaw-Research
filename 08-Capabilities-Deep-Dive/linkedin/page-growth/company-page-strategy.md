# LinkedIn Company Page Growth Strategy

## Overview

This document outlines the strategy for growing SW Recovery Services' LinkedIn Company Page as a Phase 2 initiative that directly feeds Phase 3 paid advertising. A strong organic following creates a warm audience for retargeting, establishes industry authority, and provides social proof that amplifies every other marketing channel.

The strategy covers three interconnected goals:
1. **Build organic following** to 1,000+ followers (authority threshold for B2B)
2. **Drive consistent engagement** to expand algorithmic reach
3. **Create retargetable audiences** for Phase 3 LinkedIn Ads campaigns

LinkedIn is the primary B2B platform for environmental services, remediation, and enterprise recovery -- exactly where SW Recovery Services' ideal customers spend their professional time.

---

## LinkedIn Pages API Integration

### API Access and Authentication

**API Program**: LinkedIn Marketing API (Page Management product)
**Auth**: OAuth 2.0 with 3-legged flow for Page Admin access
**Version**: Marketing API v202511 (latest stable as of 2025)

**Required Permissions**:
- `w_organization_social` -- Create and manage company posts
- `r_organization_social` -- Read company page posts and engagement
- `r_organization_admin` -- Read page analytics and follower data
- `rw_organization_admin` -- Manage page settings

**Application Approval**: Requires LinkedIn Marketing Developer Platform application. Approval typically takes 5-15 business days. Must demonstrate legitimate use case (content management, analytics).

### Posts API

The LinkedIn Posts API enables programmatic content creation and management for Company Pages.

**Endpoint**: `POST https://api.linkedin.com/rest/posts`

**Supported Post Types**:

| Post Type | Content | Best Engagement Rate |
|-----------|---------|---------------------|
| **Text only** | Plain text (up to 3,000 chars) | 3.5-4.5% |
| **Single image** | Text + 1 image | 4.5-5.5% |
| **Multi-image** | Text + 2-10 images (carousel) | **6.60%** (highest) |
| **Video** | Text + native video | 5.60% |
| **Document** | Text + PDF/PPT (carousel document) | **5.85%** |
| **Article** | Long-form article | 3.0-4.0% |
| **Poll** | Question with 2-4 options | 5.0-6.0% |

**Create a Text + Image Post**:
```json
POST /rest/posts
{
  "author": "urn:li:organization:12345678",
  "commentary": "Our team just completed a major site remediation in Houston, reducing contamination levels by 95% in just 8 weeks. Here's how we did it... #EnvironmentalRemediation #Recovery",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  },
  "content": {
    "media": {
      "title": "Houston Site Remediation Case Study",
      "id": "urn:li:image:C4D10AQH..."
    }
  },
  "lifecycleState": "PUBLISHED",
  "isReshareDisabledByAuthor": false
}
```

**Upload Image Before Posting**:
```
1. POST /rest/images?action=initializeUpload
   Body: { "initializeUploadRequest": { "owner": "urn:li:organization:12345678" } }

2. PUT {uploadUrl} (returned from step 1)
   Body: [binary image data]

3. Use returned image URN in post creation
```

### Analytics API

**Organization Page Statistics**:
```
GET /rest/organizationalEntityShareStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:12345678
```

Returns:
- `totalShareStatistics` -- aggregate engagement metrics
- `shareCount` -- total posts
- `clickCount`, `commentCount`, `impressionCount`, `likeCount`, `shareCount`

**Follower Statistics**:
```
GET /rest/organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:12345678
```

Returns:
- Follower count over time
- Follower demographics (seniority, industry, function, location)
- Organic vs. paid follower growth

**Post-Level Analytics** (Member Post Analytics API, available since 2025):
- Individual post reach, impressions, reactions, comments, shares
- Video views and average watch time
- Click-through rate
- Engagement rate per post

---

## Content Posting Strategy

### Content Pillars for SW Recovery Services

| Pillar | % of Content | Examples | Goal |
|--------|-------------|----------|------|
| **Educational / Thought Leadership** | 40% | Industry trends, regulatory updates, remediation techniques | Build authority |
| **Case Studies / Results** | 25% | Before/after projects, client wins, metrics | Social proof |
| **Behind the Scenes / Culture** | 15% | Team photos, field work, company events | Humanize brand |
| **Engagement / Interactive** | 15% | Polls, questions, industry debates | Drive comments |
| **Promotional** | 5% | Service offerings, capabilities, contact info | Generate leads |

### Posting Frequency and Timing

| Metric | Recommended | Notes |
|--------|-------------|-------|
| **Posts per week** | 4 (Mon, Tue, Wed, Thu) | 25% higher engagement than daily posting |
| **Best posting time** | 7:30-8:30 AM ET (Tue-Thu) | Peak LinkedIn B2B activity |
| **Avoid** | Friday PM, weekends | Lowest B2B engagement |
| **Content lead time** | 2 weeks ahead | Batch creation for consistency |

### Content Format Priorities

Based on 2025 LinkedIn algorithm data, prioritize these formats:

1. **Multi-image carousels** (6.60% engagement) -- Use for case studies, step-by-step processes, before/after project photos
2. **Document carousels (PDF/PPT)** (5.85%) -- Use for educational content, guides, checklists
3. **Native video** (5.60%) -- Use for project walkthroughs, team introductions, expertise clips
4. **Polls** (5.0-6.0%) -- Use for industry questions, gauging audience interest
5. **Text + single image** (4.5-5.5%) -- Use for news, updates, quick tips

### Example Content Calendar (1 Week)

| Day | Format | Pillar | Topic |
|-----|--------|--------|-------|
| **Monday** | Multi-image carousel | Case Study | "How we remediated a 50-acre industrial site in 12 weeks" |
| **Tuesday** | Text + image | Educational | "3 regulatory changes every environmental firm should know about in 2026" |
| **Wednesday** | Poll | Engagement | "What's the biggest challenge in environmental remediation today?" |
| **Thursday** | Native video (60s) | Behind the Scenes | "A day in the field with our remediation team" |

---

## Engagement Automation

### Automated Posting Pipeline

```
[Content Creation (manual or AI-assisted)]
    |
    v
[Content Review + Approval (human)]
    |
    v
[Scheduling Tool]
    +--> Option A: Buffer / Hootsuite / Later (SaaS tools)
    +--> Option B: Custom via LinkedIn Posts API + n8n scheduler
    |
    v
[LinkedIn Posts API publishes at scheduled time]
    |
    v
[Post-Publish Automation]
    +--> Notify team via Slack: "New post is live, please engage!"
    +--> Steven + 3-4 key employees like/comment within first hour
    +--> Track performance via Analytics API at 24h and 7d marks
```

### Employee Advocacy Program

Employee engagement in the first hour is the single biggest lever for organic reach:

**Protocol**:
1. When new company post goes live, send Slack/email notification to advocacy group
2. 5-8 employees like the post within 30 minutes
3. 2-3 employees leave thoughtful comments (not just "Great post!")
4. 1-2 employees share the post to their personal feeds with added commentary
5. This signals to LinkedIn's algorithm that the post is high-quality, triggering broader distribution

**Employee Advocacy Tools** (optional):
- **DSMN8** -- Automated content sharing for employees
- **Hootsuite Amplify** -- Employee advocacy module
- **Manual Slack channel** -- "#linkedin-advocacy" with daily post links

### Comment Management

| Action | Method | Timing |
|--------|--------|--------|
| Reply to all comments | Manual (Page Admin) | Within 2-4 hours |
| Like all comments | Manual or automated | Within 1 hour |
| Follow up on interested comments | Manual DM or AimFox | Within 24 hours |
| Track leads from comments | n8n -> Nutshell | Automated |

---

## Follower Growth Strategy

### Organic Growth Tactics

#### 1. Invite Connections to Follow Page
- Each employee invites their LinkedIn connections to follow the company page
- LinkedIn allows 250 invites per month per employee
- With 10 active employees: 2,500 invites/month
- Expected conversion: 10-20% = 250-500 new followers/month

#### 2. Cross-Promote on Other Channels
- Add LinkedIn company page link to:
  - Email signatures (all 20 employees)
  - Website footer and "About" page
  - Other social media profiles
  - Business cards and proposals
  - Nutshell email templates

#### 3. Content-Driven Growth
- High-engagement posts (especially carousels and videos) get shown to non-followers
- Posts that receive comments from non-followers drive profile visits -> follows
- Target: 5-10 organic new followers per high-performing post

#### 4. Strategic Hashtag Use
- Use 3-5 relevant hashtags per post
- Mix of broad (#EnvironmentalServices, #Remediation) and niche (#SuperfundCleanup, #SoilRemediation)
- Follow and engage with industry hashtags to increase visibility

#### 5. LinkedIn Newsletters
- Launch a monthly LinkedIn Newsletter from the company page
- Subscribers get push notifications for each issue
- Newsletter subscribers count as engaged followers
- Content: industry insights, project highlights, regulatory updates

### Growth Milestones and Timeline

| Milestone | Target | Timeline | Strategy |
|-----------|--------|----------|----------|
| **100 followers** | Foundation | Month 1 | Employee invites + existing network |
| **250 followers** | Credibility | Month 2 | Content cadence + cross-promotion |
| **500 followers** | Momentum | Month 3-4 | Consistent posting + engagement |
| **1,000 followers** | Authority | Month 5-6 | Employee advocacy + newsletter |
| **2,500 followers** | Advertising ready | Month 8-10 | Organic + paid follower ads |
| **5,000 followers** | Industry presence | Month 12-18 | Full content engine + events |

---

## Audience Building for Paid LinkedIn Ads (Phase 3)

The organic follower growth in Phase 2 directly creates retargetable audiences for Phase 3 paid campaigns. Here is how they connect:

### Retargeting Audience Types

| Audience | Source | Minimum Size | Use in Ads |
|----------|--------|-------------|------------|
| **Company Page visitors** | People who viewed page | 300 members | Mid-funnel awareness |
| **Page CTA clickers** | Clicked "Contact" or "Visit Website" | 300 members | Bottom-funnel lead gen |
| **Post engagers** | Liked, commented, shared posts | 300 members | Warm audience retargeting |
| **Video viewers** | Watched 25%/50%/75%/97% of video | 300 members | Engagement-based retargeting |
| **Company page followers** | Current followers | Any size | Lookalike audience seed |
| **Website visitors** | LinkedIn Insight Tag on website | 300 members | Cross-channel retargeting |

### LinkedIn Insight Tag (Install in Phase 2)

The LinkedIn Insight Tag should be installed on the SW Recovery Services website during Phase 2, even before paid ads begin:

```html
<script type="text/javascript">
_linkedin_partner_id = "XXXXXXX";
window._linkedin_data_partner_ids = window._linkedin_data_partner_ids || [];
window._linkedin_data_partner_ids.push(_linkedin_partner_id);
</script>
<script type="text/javascript">
(function(l) { /* LinkedIn Insight Tag script */ })();
</script>
```

**Why install early**: The Insight Tag starts collecting website visitor data immediately. By the time Phase 3 paid ads launch, there will be 3-6 months of accumulated audience data for retargeting.

### Paid Ad Strategy Foundation (Phase 3 Preview)

| Campaign Type | Audience | Objective | Est. Budget |
|---------------|----------|-----------|-------------|
| **Follower Ads** | Lookalike of current followers | Grow page following | $500-1,000/mo |
| **Sponsored Content** | Industry targeting + retargeting | Brand awareness | $1,000-2,500/mo |
| **Lead Gen Forms** | Post engagers + page visitors | Direct lead capture | $1,500-3,000/mo |
| **Message Ads** | High-intent website visitors | Meeting booking | $500-1,000/mo |
| **Document Ads** | Industry professionals | Thought leadership | $750-1,500/mo |

### Audience Funnel Architecture

```
[Cold Audience -- Industry Targeting]
    |
    +--> Sponsored Content (educational posts, case studies)
    |
    v
[Warm Audience -- Engaged with Content]
    |
    +--> Retarget with deeper content (video, documents)
    |
    v
[Hot Audience -- Page Visitors + CTA Clickers]
    |
    +--> Lead Gen Forms, Message Ads, Meeting Booking
    |
    v
[Qualified Lead -> Nutshell CRM -> Sales Rep]
```

---

## Scheduling and Automation Tools

### Recommended Tool: Buffer

| Feature | Buffer (Free) | Buffer (Essentials) | Buffer (Team) |
|---------|--------------|---------------------|---------------|
| **Price** | $0 | $6/channel/mo | $12/channel/mo |
| **Scheduled posts** | 10 queued | Unlimited | Unlimited |
| **Analytics** | Basic | Full | Full + export |
| **Team members** | 1 | 1 | Unlimited |
| **Approval workflow** | No | No | Yes |
| **Best for** | Testing | Solo marketer | Team coordination |

### Alternative: Custom API Pipeline

For full control and integration with existing n8n workflows:

```
[Content Spreadsheet (Google Sheets)]
    |
    v
[n8n Scheduled Trigger (cron: Mon-Thu 7:30 AM)]
    |
    v
[n8n reads next scheduled post from spreadsheet]
    |
    v
[n8n uploads image via LinkedIn Images API]
    |
    v
[n8n creates post via LinkedIn Posts API]
    |
    v
[n8n sends Slack notification to advocacy channel]
    |
    v
[n8n logs post ID + timestamp to tracking sheet]
    |
    v
[n8n scheduled check at 24h: pull analytics, update tracking]
```

### Tool Comparison for LinkedIn Scheduling

| Tool | LinkedIn Pages Support | Price | API Access | Analytics |
|------|----------------------|-------|------------|-----------|
| **Buffer** | Yes | $0-12/mo | Yes | Good |
| **Hootsuite** | Yes | $99/mo | Yes | Excellent |
| **Later (getLate)** | Yes | $25/mo | Yes | Good |
| **SocialPilot** | Yes | $30/mo | Yes | Good |
| **Custom (n8n + API)** | Yes | $0-20/mo | Full control | Build your own |
| **Metricool** | Yes | $0-18/mo | Yes | Excellent |

**Recommendation**: Start with **Buffer Essentials** ($6/mo) for simplicity. Move to **custom API pipeline** in Phase 3 when content volume and team coordination increase.

---

## Content Performance Tracking

### Key Metrics Dashboard

| Metric | Target (Month 1-3) | Target (Month 4-6) | Source |
|--------|--------------------|--------------------|--------|
| **Follower count** | 250+ | 1,000+ | LinkedIn Analytics |
| **Engagement rate** | > 4% | > 5% | Post analytics |
| **Post impressions/week** | 2,000+ | 8,000+ | LinkedIn Analytics |
| **Profile views/week** | 100+ | 400+ | LinkedIn Analytics |
| **Website clicks/month** | 50+ | 200+ | LinkedIn Analytics |
| **Leads from LinkedIn** | 2-5/month | 10-20/month | Nutshell CRM |
| **Content publish rate** | 4 posts/week | 4 posts/week | Scheduling tool |

### Analytics Review Cadence

| Frequency | Review | Actions |
|-----------|--------|---------|
| **Daily** | Comment monitoring, reply to engagement | Maintain conversation |
| **Weekly** | Post performance, engagement trends | Adjust content mix |
| **Monthly** | Follower growth, audience demographics, top posts | Strategic content planning |
| **Quarterly** | ROI analysis, leads generated, audience quality | Budget and strategy review |

---

## API/Integration Details Summary

### Full Integration Architecture

```
[Content Creation]
    |
    v
[Scheduling Tool (Buffer or n8n)]
    |
    v
[LinkedIn Posts API] --> [Company Page Feed]
    |                          |
    v                          v
[LinkedIn Analytics API]   [Audience Engagement]
    |                          |
    v                          v
[Performance Dashboard]    [Retargetable Audiences]
    |                          |
    v                          v
[Monthly Reports]          [Phase 3 LinkedIn Ads]
                               |
                               v
                           [Lead Gen Forms]
                               |
                               v
                           [Nutshell CRM]
```

### Required API Applications

| API | Purpose | Approval Time |
|-----|---------|---------------|
| LinkedIn Marketing API | Posts, analytics, page management | 5-15 business days |
| LinkedIn Insight Tag | Website visitor tracking for retargeting | Instant (self-service) |
| Buffer API (optional) | Scheduling integration | Instant |
| Google Sheets API | Content calendar automation | Instant |

---

## Cost Implications

### Monthly Costs

| Component | Cost | Notes |
|-----------|------|-------|
| LinkedIn Company Page | Free | No cost for organic page |
| Buffer Essentials | $6/mo | 1 LinkedIn channel |
| LinkedIn API access | Free | Included with Marketing API approval |
| LinkedIn Insight Tag | Free | Self-service installation |
| n8n (if custom pipeline) | $0-20/mo | Self-hosted free |
| Content creation tools | $0-30/mo | Canva Pro for graphics |
| **Total (Phase 2 organic)** | **$6-56/mo** | Minimal cost, high ROI |
| **Phase 3 ad budget (preview)** | $3,000-8,000/mo | When paid campaigns begin |

### Content Creation Labor

| Activity | Hours/Week | Who |
|----------|-----------|-----|
| Content planning | 1-2h | Marketing lead |
| Content creation (posts) | 2-3h | Marketing lead or AI-assisted |
| Graphics/video production | 1-2h | Designer or Canva |
| Community management | 1-2h | Marketing lead |
| Analytics review | 0.5-1h | Marketing lead |
| **Total weekly labor** | **5.5-10h** | Manageable for 1 person |

---

## Estimated Build Hours

| Component | Hours | Description |
|-----------|-------|-------------|
| LinkedIn Company Page optimization | 2-3h | Banner, description, CTA, showcase pages |
| LinkedIn Marketing API application | 2-3h | Application, documentation, approval wait |
| Buffer/scheduling tool setup | 1-2h | Connect page, configure posting times |
| Content pillar + calendar design | 3-4h | Strategy, templates, first month planned |
| Employee advocacy program setup | 2-3h | Slack channel, guidelines, initial training |
| LinkedIn Insight Tag installation | 1-2h | Website tag, conversion tracking setup |
| n8n analytics pipeline (optional) | 4-6h | Automated analytics pull, dashboard |
| First month content creation | 8-12h | 16 posts (4/week x 4 weeks) with graphics |
| Performance tracking setup | 2-3h | Dashboard, KPIs, reporting templates |
| **Total** | **25-38h** | ~1.5-2 weeks with dedicated marketer |

---

## Sources

- [LinkedIn Posts API Documentation](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [LinkedIn Page Management API](https://developer.linkedin.com/product-catalog/marketing/page-management)
- [LinkedIn Posting API Guide](https://getlate.dev/blog/linkedin-posting-api)
- [LinkedIn Company Page Posting API Guide](https://getlate.dev/blog/linked-in-company-page-posting-api)
- [How to Grow LinkedIn Company Page (Sculpt)](https://wearesculpt.com/blog/grow-linkedin-company-page/)
- [LinkedIn Company Page Growth Guide (Impactable)](https://impactable.com/linkedin-company-page-growth-guide/)
- [LinkedIn Engagement Benchmarks 2026](https://contentin.io/blog/linkedin-engagement-benchmarks/)
- [LinkedIn Social Insider Benchmarks 2025](https://www.socialinsider.io/social-media-benchmarks/linkedin)
- [How to Grow Organic Following (LinkedIn Official)](https://www.linkedin.com/business/marketing/blog/social-media-marketing/how-to-grow-your-organic-following-on-linkedin)
- [LinkedIn Organic Reach for Company Pages](https://dsmn8.com/blog/linkedin-organic-reach-investigation/)
- [LinkedIn Retargeting with Matched Audiences](https://www.linkedin.com/help/lms/answer/a427551)
- [LinkedIn Website Retargeting Setup](https://www.linkedin.com/help/lms/answer/a420433)
- [Buffer LinkedIn Scheduling](https://buffer.com/linkedin)
- [LinkedIn Scheduling Tools Comparison](https://www.supergrow.ai/blog/linkedin-scheduling-tools)
- [LinkedIn Post Analytics API](https://thelinkedblog.com/2025/linkedin-unlocks-post-insights-for-creators-with-new-api-integration-3382/)

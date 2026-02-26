# Social Monitoring Platform Selection

## Overview

Social monitoring (also called social listening) tracks online mentions of a brand, competitors, keywords, and industry topics across social media, news, forums, blogs, and review sites. For SW Recovery Services, this capability enables:

- **Brand reputation management** -- catch negative mentions before they escalate
- **Competitor monitoring** -- track what competitors are doing and saying
- **Lead identification** -- find people discussing debt recovery needs online
- **Content intelligence** -- discover trending topics and sentiment around key industry terms
- **Crisis detection** -- real-time alerts for sudden spikes in negative mentions

This document evaluates four approaches: **Brandwatch** (enterprise), **Mention** (mid-market), **Brand24** (SMB-focused), and a **custom-built solution**.

---

## API/Integration Details

### Platform Comparison Matrix

| Feature | Brandwatch | Mention | Brand24 | Custom Build |
|---------|-----------|---------|---------|--------------|
| **Target market** | Enterprise | SMB to mid-market | SMB to mid-market | Any (we control scope) |
| **Pricing** | $800-5,000+/mo (custom) | $41-166+/mo | $99-499/mo | API costs only |
| **API available** | Yes (full) | Yes (full) | Limited | N/A (we build it) |
| **Sentiment accuracy** | 60-75% | Good (AI-based) | ~95% (deep learning) | Depends on LLM used |
| **Historical data** | Up to 3 years | Up to 2 years | Varies by plan | Only what we collect |
| **Sources monitored** | Social, news, forums, blogs, TV, radio | Social, news, forums, blogs | Social, news, forums, blogs, podcasts (enterprise) | Per-platform API limits |
| **Real-time alerts** | Yes | Yes | Yes | Yes (we build it) |
| **Emotion analysis** | Yes (advanced) | Yes (launched late 2024) | Basic sentiment only | LLM-powered (flexible) |
| **Free trial** | No (demo only) | 14-day free trial | 14-day free trial | N/A |
| **Contract** | Annual (non-refundable) | Monthly or annual | Monthly or annual (30-day guarantee) | No contract |

### Brandwatch

**Best for:** Large enterprises needing comprehensive social intelligence with deep historical data.

**Pricing tiers (estimated, not published):**
- Small/mid-size business: $800-1,200/month
- Mid-tier/agency: $2,000-3,500/month
- Enterprise/global: $5,000+/month
- Annual contracts standard, non-refundable

**Key capabilities:**
- 100M+ online sources including TV and radio monitoring
- 3-year historical data access
- AI-powered topic and trend detection
- Vizia real-time dashboards for presentations
- Consumer research surveys
- Image recognition (logo detection in social images)
- Extensive API for custom integrations

**API details:**
- Full REST API with comprehensive endpoint coverage
- Bulk data export capabilities
- Webhook support for real-time alerts
- Rate limits vary by plan

**Verdict for Steven:** Overkill. The pricing alone ($10K-60K+/year) is not justified for a single-location service business. The depth of analytics (TV monitoring, image recognition, consumer surveys) targets Fortune 500 brand management teams, not SMB reputation monitoring.

### Mention

**Best for:** SMBs and agencies needing solid monitoring with good API access and multi-channel support.

**Pricing tiers:**

| Plan | Monthly Cost | Alerts | Mentions/Month | Social Accounts | Users |
|------|-------------|--------|----------------|-----------------|-------|
| Solo | $41/month | 2 | 5,000 | 4 | 1 |
| Pro | $83/month | 5 | 10,000 | 10 | Unlimited |
| ProPlus | $149/month | 7 | 20,000 | 15 | Unlimited |
| Company | Custom | 10+ | 100,000+ | Unlimited | Unlimited |

**Key capabilities:**
- Real-time monitoring across social media, web, forums, and news
- Boolean search operators for precise keyword monitoring
- Sentiment analysis with emotion detection (launched late 2024)
- Share of voice metrics
- Auto-updating reports and dashboards
- Competitive analysis comparisons
- Influencer identification

**API details:**
- Full REST API for programmatic access
- Real-time mention streaming
- Alert management endpoints
- Mention retrieval with filtering and pagination
- Webhook notifications for new mentions

**Integrations:** Slack, Zapier, n8n (via HTTP requests), Buffer, Hootsuite.

**Verdict for Steven:** Solid mid-range option. The Pro plan at $83/month provides enough alerts and mentions for a single business. Good API for n8n integration. The emotion analysis feature is a nice addition.

### Brand24

**Best for:** Small businesses wanting powerful sentiment analysis at accessible pricing.

**Pricing tiers:**

| Plan | Monthly Cost (Annual) | Keywords | Mentions/Month | Users | Key Features |
|------|----------------------|----------|----------------|-------|-------------|
| Individual | $99/month | 3 | 2,000 | 1 | Basic monitoring, sentiment |
| Team | $179/month | 7 | 20,000 | Unlimited | Advanced analytics, AI reports |
| Pro | $249/month | 12 | 40,000 | Unlimited | Consulting, priority support |
| Enterprise | $499/month | 25 | 100,000 | Unlimited | All sources including podcasts |

**Key capabilities:**
- 95% sentiment analysis accuracy (deep learning + pretrained language models, improved June 2025)
- AI-powered brand reports and summaries
- Influence score for mention sources
- Discussion volume charts and trending topic detection
- Hashtag and keyword analytics
- Comparison reports for competitive analysis
- Slack integration built-in

**API details:**
- API access varies by plan (some sources report limited API availability)
- Data export in CSV, Excel, PDF formats
- Slack and email alert integrations
- Less developer-friendly than Mention for custom integrations

**Integrations:** Slack, Google Analytics, n8n (via webhooks/email parsing), social scheduling tools.

**Verdict for Steven:** Strong contender for value. The Team plan at $179/month gives 7 keywords (enough for brand + competitors + key industry terms) with excellent sentiment analysis. The 95% sentiment accuracy is the best in class for this price range. API limitations may require workarounds for deep n8n integration.

### Custom-Built Solution

**Best for:** Teams with development capacity who want full control and no recurring platform costs.

**Architecture:**
```
[n8n Scheduled Triggers]
  -> [Platform APIs: Twitter/X, Reddit, Google Alerts, NewsAPI]
  -> [LLM Sentiment Analysis (OpenAI/Claude)]
  -> [Supabase: mention storage, analytics]
  -> [Alerts: Slack, email]
  -> [Dashboard: custom or Supabase views]
```

**Data sources we can tap directly:**

| Source | API | Cost | Limitations |
|--------|-----|------|------------|
| Twitter/X API | v2 API | $100/month (Basic) or $5,000/month (Pro) | Basic: 10K tweets/month read. Very expensive for full monitoring. |
| Reddit API | Free tier | Free | Rate limited, good for industry forums |
| Google Alerts | Email-based (no API) | Free | Low volume, no sentiment, delayed |
| NewsAPI | REST API | Free (dev) / $449/month (business) | 100 requests/day free, no commercial use |
| Bing News Search API | Azure Cognitive Services | $3/1,000 calls | Good news coverage, affordable |
| Web scraping | Custom scrapers | Hosting costs only | Legal gray area, fragile, maintenance-heavy |

**LLM-powered sentiment analysis:**
```python
# Example: analyze mention sentiment with OpenAI
prompt = f"""Analyze the sentiment of this social media mention
about SW Recovery Services.
Classify as: positive, negative, neutral, or mixed.
Provide a confidence score (0-1) and brief explanation.

Mention: "{mention_text}"
"""
# Cost: ~$0.01-0.03 per mention with GPT-4o-mini
```

**Supabase schema for custom monitoring:**
```sql
CREATE TABLE social_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL, -- 'twitter', 'reddit', 'news', 'web'
    source_url TEXT,
    author TEXT,
    content TEXT NOT NULL,
    keyword_matched TEXT,
    sentiment TEXT, -- 'positive', 'negative', 'neutral', 'mixed'
    sentiment_score NUMERIC(4,3),
    influence_score INTEGER,
    created_at TIMESTAMPTZ,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE monitoring_keywords (
    id SERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    category TEXT, -- 'brand', 'competitor', 'industry'
    active BOOLEAN DEFAULT true
);

CREATE TABLE sentiment_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mention_id UUID REFERENCES social_mentions(id),
    alert_type TEXT, -- 'negative_spike', 'competitor_mention', 'lead_signal'
    sent_to TEXT, -- 'slack', 'email'
    sent_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Verdict for Steven:** Cost-effective for basic monitoring but coverage is limited. Twitter/X API pricing ($100-5,000/month) alone can exceed the cost of Brand24 or Mention while providing only one platform. Best as a supplement to a paid tool, not a replacement.

---

## Implementation Approach

### Recommended Strategy: Brand24 Team + Custom Supplements

**Primary tool:** Brand24 Team plan ($179/month) for broad monitoring and alerts.
**Supplements:** Custom n8n workflows for Reddit monitoring, Google Alerts parsing, and LLM-enhanced analysis.

#### Phase 2 Setup

**Week 1: Brand24 Configuration**
1. Set up Brand24 account on Team plan
2. Configure monitoring keywords:
   - Brand: "SW Recovery", "SW Recovery Services", "swrecovery.com"
   - Competitors: top 3 competitor brand names
   - Industry: "debt recovery [city]", "debt collection services", "collections agency"
3. Set up alert rules:
   - Immediate alert: any negative mention with influence score > 50
   - Daily digest: all mentions grouped by sentiment
   - Weekly report: competitor comparison and trending topics
4. Connect Slack integration for real-time alerts

**Week 2: N8N Integration**
1. Set up n8n workflow to pull Brand24 data (via webhooks, email parsing, or API if available)
2. Store mentions in Supabase for long-term analysis and custom reporting
3. Build custom sentiment enhancement: re-analyze mentions with LLM for deeper insights
4. Create lead detection workflow: flag mentions where people express need for debt recovery services

**Week 3: Custom Monitoring Supplements**
1. Reddit monitoring via API (free): track r/personalfinance, r/debt, r/smallbusiness for relevant discussions
2. Google Alerts via email parsing in n8n: supplement Brand24 with Google's news coverage
3. Review site monitoring: automate checking Google reviews, BBB, Yelp for new reviews

**Week 4: Reporting and Dashboards**
1. Build weekly social intelligence report combining Brand24 data + custom sources
2. Create Supabase views for: mention volume trends, sentiment over time, competitor share of voice
3. Automate monthly competitive social intelligence summary for Steven

#### Alert Escalation Rules

| Trigger | Action | Urgency |
|---------|--------|---------|
| Negative mention, influence > 50 | Slack DM to Steven + team channel | Immediate |
| Negative review on Google/BBB | Slack alert + add to CRM task | Within 1 hour |
| Competitor wins/losses mention | Weekly digest | Low |
| Lead signal ("need debt recovery help") | Create lead in Nutshell CRM | Within 1 hour |
| Mention volume spike (3x normal) | Slack alert + investigation trigger | Immediate |

### Alternative Strategy: Mention Pro

If Brand24's API limitations are a blocker, Mention Pro at $83/month is the fallback. Advantages: better API, lower cost. Disadvantages: lower sentiment accuracy, fewer mentions per month.

---

## Cost Implications

### Recommended Setup (Brand24 Team + Custom)

| Item | Monthly Cost | Annual Cost | Notes |
|------|-------------|-------------|-------|
| Brand24 Team plan | $179/month | $2,148/year | 7 keywords, 20K mentions, unlimited users |
| OpenAI API (sentiment enhancement) | $5-15/month | $60-180/year | ~500-1,500 mentions re-analyzed |
| Reddit API | $0 | $0 | Free tier sufficient |
| Google Alerts | $0 | $0 | Free |
| Supabase (data storage) | $0-25/month | $0-300/year | Free tier likely sufficient |
| n8n (automation) | $0 | $0 | Already in the stack |
| **Total** | **$184-219/month** | **$2,208-2,628/year** | |

### Alternative Options

| Option | Monthly Cost | Annual Cost | Pros | Cons |
|--------|-------------|-------------|------|------|
| Mention Pro | $83/month | $996/year | Cheapest full platform, good API | Lower sentiment accuracy |
| Brand24 Individual | $99/month | $1,188/year | Good sentiment, lower cost | Only 3 keywords, 2K mentions |
| Brand24 Team | $179/month | $2,148/year | Best sentiment, 7 keywords | Moderate cost, API limitations |
| Brandwatch | $800-5,000+/mo | $9,600-60,000+/yr | Most comprehensive | Overkill, expensive |
| Custom only | $5-115/month | $60-1,380/year | Full control, no platform cost | Limited coverage, high build time |

### Pricing Trends

- Brand24 has historically increased prices ~10-15% annually
- Mention appears stable with periodic feature additions
- Brandwatch continues to move upmarket after acquisition by Cision
- Custom approach costs scale with Twitter/X API pricing (which has increased significantly since Elon Musk's acquisition)

---

## Estimated Build Hours

### Brand24 Team + Custom Supplements (Recommended)

| Task | Hours | Notes |
|------|-------|-------|
| Brand24 account setup and keyword config | 2 | Account creation, keyword selection, alert rules |
| Slack integration setup | 1 | Connect Brand24 alerts to Slack channels |
| N8N workflow: Brand24 data ingestion | 4 | Webhook/email parsing, Supabase storage |
| N8N workflow: Reddit monitoring | 3 | API integration, keyword matching, sentiment |
| N8N workflow: Google Alerts parsing | 2 | Email trigger, content extraction, storage |
| N8N workflow: Review site monitoring | 3 | Google Reviews, BBB, Yelp automated checks |
| LLM sentiment enhancement | 2 | Re-analyze mentions with deeper AI analysis |
| Lead detection workflow | 3 | Identify potential leads from social mentions |
| Supabase schema and views | 2 | Tables, indexes, dashboard queries |
| Alert escalation configuration | 2 | Routing rules, Slack/email/CRM triggers |
| Weekly reporting automation | 3 | Combined report from all sources |
| Testing and QA | 2 | Verify alerts, sentiment accuracy, data flow |
| **Total** | **29** | |

### Mention Pro (Alternative)

| Task | Hours | Notes |
|------|-------|-------|
| Mention setup and keyword config | 2 | Same scope as Brand24 |
| API integration with n8n | 3 | Mention has better API, faster integration |
| Remaining tasks | 18 | Same as above minus Brand24-specific work |
| **Total** | **23** | |

**Dependencies:** Slack workspace, n8n instance, Supabase instance, Nutshell CRM (for lead creation from mentions), competitor list finalized with Steven.

**Recommendation:** Start with Brand24 Team plan. The 14-day free trial allows us to validate keyword coverage and sentiment accuracy before committing. If the API proves too limiting for n8n integration, fall back to Mention Pro. Defer Brandwatch evaluation unless SW Recovery scales to multiple locations or Steven specifically requests enterprise-grade intelligence.

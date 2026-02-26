# OpenClaw Total Cost of Ownership: Monthly Projection

## Overview

This document consolidates all costs into a single monthly projection for running the full OpenClaw system. It combines infrastructure (Mac Mini, electricity), existing services (DataForSEO, Serper, etc.), AI/LLM usage (Claude API + Ollama), enrichment (Clay.com), CRM (GoHighLevel), and new services added by OpenClaw (Twilio, Supabase Pro).

The goal is a clear, honest number: **what will you spend per month with OpenClaw fully operational?**

---

## Monthly Cost Breakdown by Category

### 1. Infrastructure -- $55-60/mo

| Item | Monthly Cost | How Calculated |
|------|-------------|---------------|
| Mac Mini M4 Pro 48GB/1TB (amortized over 36 months) | $50 | $1,799 / 36 = $49.97, rounded to $50 |
| UPS + peripherals (amortized over 36 months) | $3 | ~$100 / 36 = $2.78, rounded to $3 |
| Electricity (Mac Mini 24/7) | $4 | ~20W avg x 24h x 30d x $0.15/kWh = $2.16, rounded up for real-world variance |
| Internet (incremental) | $0 | Already paying for internet |
| **Infrastructure subtotal** | **$57/mo** | |

Use **$57/mo** as the infrastructure planning number.

### 2. Core Marketing APIs -- $149/mo

These are services you already pay for and will continue using at roughly the same level:

| Service | Monthly Cost | Role in OpenClaw |
|---------|-------------|-----------------|
| DataForSEO | $49 | SEO data for audit pipelines and lead qualification |
| Serper | $50 | Google Search results for research and enrichment |
| ZeroBounce | $25 | Email verification (using $25 as midpoint of $15-40 range) |
| Brevo | $15 | Email sending for outreach sequences (using midpoint) |
| Buffer | $10 | Social media scheduling (using midpoint) |
| **Core APIs subtotal** | **$149/mo** | |

### 3. AI and LLM -- $40/mo

| Service | Monthly Cost | Details |
|---------|-------------|--------|
| Claude API (Anthropic) | $40 | Model-routed: ~50% Haiku, 15% Sonnet, 5% Opus, 30% local. With prompt caching. Processes 500-1,000 leads/month plus content generation. |
| Ollama (local models) | $0 | Runs on Mac Mini. Handles classification, extraction, formatting, and development/testing. |
| **AI/LLM subtotal** | **$40/mo** | |

**Note**: $40/mo is the moderate estimate. Light usage could be $15-20; heavy usage with lots of Opus calls could reach $60-80. See `api-costs.md` for detailed token calculations.

### 4. Enrichment -- $99/mo

| Service | Monthly Cost | Details |
|---------|-------------|--------|
| Clay.com (Explorer plan) | $99 | 5,000 enrichment credits/month. Enough for ~1,000-2,500 leads depending on enrichment depth. |
| **Enrichment subtotal** | **$99/mo** | |

**Scaling note**: If you process more than 2,500 leads/month, upgrade to Clay Pro ($149/mo) for 10,000 credits.

### 5. CRM -- $97-297/mo

| Service | Monthly Cost | Details |
|---------|-------------|--------|
| GoHighLevel | $97-297 | Agency Starter ($97): manages your own clients. Agency Unlimited ($297): white-label, unlimited sub-accounts. |
| **CRM subtotal** | **$97-297/mo** | |

This is the biggest variable in your stack. The $200/mo difference between GHL plans significantly affects total cost.

### 6. New Services (Added by OpenClaw) -- $35/mo

| Service | Monthly Cost | Details |
|---------|-------------|--------|
| Twilio (WhatsApp Business) | $10 | ~400 conversations/month at $0.025/conversation average. Includes $1/mo phone number. |
| Supabase Pro | $25 | Upgraded from free tier for production use. 8GB database, 100GB storage, edge functions. |
| **New services subtotal** | **$35/mo** | |

**Note**: Supabase Pro might not be needed immediately. You can start on the free tier and upgrade when your lead database grows beyond 50K records or you need more than 500K edge function invocations/month. If staying on free tier, this subtotal drops to $10/mo.

### 7. Miscellaneous -- $12/mo

| Service | Monthly Cost | Details |
|---------|-------------|--------|
| Domain registrations (amortized) | $12 | ~10 domains at $12-15/year each = $120-150/yr / 12 |
| Cloudflare, GitHub, etc. | $0 | Free tiers |
| **Misc subtotal** | **$12/mo** | |

---

## Total Monthly Cost: Three Scenarios

### Scenario A: Conservative (GHL Starter, Free Tiers Where Possible)

| Category | Monthly Cost |
|----------|-------------|
| Infrastructure | $57 |
| Core Marketing APIs | $149 |
| AI/LLM | $40 |
| Enrichment (Clay Starter) | $49 |
| CRM (GHL Starter) | $97 |
| New Services (Twilio only, Supabase free) | $10 |
| Miscellaneous | $12 |
| **Total** | **$414/mo** |

### Scenario B: Moderate (Recommended Starting Point)

| Category | Monthly Cost |
|----------|-------------|
| Infrastructure | $57 |
| Core Marketing APIs | $149 |
| AI/LLM | $40 |
| Enrichment (Clay Explorer) | $99 |
| CRM (GHL Starter) | $97 |
| New Services (Twilio + Supabase Pro) | $35 |
| Miscellaneous | $12 |
| **Total** | **$489/mo** |

### Scenario C: Full Scale (GHL Unlimited, All Paid Tiers)

| Category | Monthly Cost |
|----------|-------------|
| Infrastructure | $57 |
| Core Marketing APIs | $149 |
| AI/LLM (higher volume) | $60 |
| Enrichment (Clay Pro) | $149 |
| CRM (GHL Unlimited) | $297 |
| New Services (Twilio + Supabase Pro) | $35 |
| Miscellaneous | $12 |
| Vercel Pro | $20 |
| Airtable Team | $20 |
| **Total** | **$799/mo** |

---

## Comparison: With vs Without OpenClaw

### Without OpenClaw (Current State)

| Category | Monthly Cost |
|----------|-------------|
| Core Marketing APIs | $149 |
| Clay.com | $99 |
| GHL (Starter) | $97 |
| Claude API (current light usage) | $15 |
| Miscellaneous | $12 |
| **Total without OpenClaw** | **$372/mo** |

### With OpenClaw (Scenario B)

| Category | Monthly Cost |
|----------|-------------|
| Everything above | $372 |
| Mac Mini (amortized + electricity) | $57 |
| Additional Claude API usage | $25 |
| Twilio (WhatsApp) | $10 |
| Supabase Pro | $25 |
| **Total with OpenClaw** | **$489/mo** |

### Net Additional Cost of OpenClaw

| Item | Monthly Cost |
|------|-------------|
| Mac Mini infrastructure | +$57 |
| Additional Claude API | +$25 |
| Twilio | +$10 |
| Supabase Pro | +$25 |
| **Net additional** | **+$117/mo** |

**After efficiency savings** (reduced ZeroBounce, smarter Clay usage, local model offloading): **net additional ~$85-100/mo**

---

## The Critical Question

**Does OpenClaw save you more than $100/mo in time and revenue?**

At even $50/hour for your time:
- You need to save just **2 hours per month** to break even on costs
- OpenClaw is projected to save **44 hours per month** (see `roi-calculation.md`)
- This is not close -- the ROI is overwhelmingly positive IF the system works as designed

The real risk is not the cost. It is the **implementation time** (60-90 hours to build and tune) and the **opportunity cost** of that setup period. Once running, the monthly economics strongly favor OpenClaw.

---

## Monthly Budget Allocation Plan

For practical budgeting, here is how to think about your monthly spend in buckets:

### Must-Have (Cannot Run OpenClaw Without These) -- $303/mo
- Mac Mini infrastructure: $57
- DataForSEO: $49
- Serper: $50
- Claude API: $40
- GHL (Starter): $97
- Miscellaneous: $12

### Should-Have (Significantly Improves Results) -- $134/mo
- Clay.com (Explorer): $99
- Supabase Pro: $25
- Twilio: $10

### Nice-to-Have (Can Add Later) -- $52-252/mo
- ZeroBounce: $25 (can manually verify small batches initially)
- Brevo: $15 (can use GHL's built-in email for small volumes)
- Buffer: $10 (can post manually initially)
- Vercel Pro: $20 (only if hosting client sites)
- Airtable Team: $20 (only if exceeding free tier)
- GHL Unlimited upgrade: +$200 (only when managing multiple client sub-accounts)

### Implementation Priority
1. **Month 1**: Must-Have only ($303/mo) -- get core pipeline working
2. **Month 2**: Add Should-Have ($437/mo) -- full enrichment and WhatsApp
3. **Month 3+**: Add Nice-to-Have as needed ($489-799/mo) -- scale based on results

---

## Cost Tracking Dashboard

Set up a simple monthly tracking spreadsheet or Airtable base:

| Metric | How to Track | Target |
|--------|------------|--------|
| Total monthly spend | Sum all service invoices | Under $500/mo (Scenario B) |
| Cost per qualified lead | Total spend / qualified leads generated | Under $2.00/lead |
| Claude API cost per 1K tokens | Anthropic dashboard | Under $5/1K tokens (blended) |
| Clay credits per lead | Credits used / leads enriched | Under 3 credits/lead |
| Infrastructure uptime | Mac Mini monitoring | 99%+ |
| Time saved per week | Self-reported log | 10+ hours/week |

### Monthly Review Process
1. First week of each month: export billing from all services
2. Calculate cost per lead for the previous month
3. Compare actual vs projected for each line item
4. Identify any service with >20% variance from projection
5. Adjust model routing, Clay usage, or Twilio volume as needed
6. Document changes in your session log

---

## Action Items

1. **Lock in your GHL plan**: This is the single biggest variable. Confirm whether you are on Starter ($97) or Unlimited ($297) and factor that into your budget.
2. **Set up billing alerts**: Configure spending limits on Claude API ($50/mo), Twilio ($25/mo), and Google Cloud ($10/mo).
3. **Start with Must-Have tier**: Do not subscribe to everything at once. Prove the core pipeline works before adding enrichment and outreach services.
4. **Track from day one**: Start your cost tracking spreadsheet before you spend anything on OpenClaw. You need a baseline to measure against.
5. **Review at 90 days**: After 3 months of operation, do a full cost-benefit analysis. Compare actual spend to these projections and adjust.

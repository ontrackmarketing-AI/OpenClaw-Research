# API and Service Costs: Monthly Projections for OpenClaw

## Overview

OpenClaw relies on a mix of paid APIs, freemium SaaS tools, and local infrastructure. This document provides detailed monthly cost projections for every API and service in the stack, shows how costs scale with usage, and identifies optimization strategies to keep spend under control.

The goal is not to eliminate API costs -- many of these services provide irreplaceable data or capabilities. The goal is to spend intelligently by routing work to the cheapest capable provider (local models when possible, tiered Claude models when needed, specialized APIs only for their unique data).

---

## Claude API (Primary Cloud LLM)

### Pricing (as of early 2026)
| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cache Write | Cache Read |
|-------|----------------------|----------------------|-------------|------------|
| Haiku 3.5 | $0.80 | $4.00 | $1.00 | $0.08 |
| Sonnet 4 | $3.00 | $15.00 | $3.75 | $0.30 |
| Opus 4 | $15.00 | $75.00 | $18.75 | $1.50 |

### Model Routing Strategy
Not every task needs Opus. OpenClaw should implement intelligent model routing:

| Task Type | Model | % of Total Requests |
|-----------|-------|-------------------|
| Lead classification (hot/warm/cold) | Haiku 3.5 | 30% |
| Data extraction from web pages | Haiku 3.5 | 20% |
| Email/message drafting | Sonnet 4 | 10% |
| Content creation (blog posts, social) | Sonnet 4 | 5% |
| Complex analysis and strategy | Opus 4 | 3% |
| Presentation generation | Opus 4 | 2% |
| Simple routing/formatting | Local (Ollama) | 30% |

**Effective split: 50% Haiku, 15% Sonnet, 5% Opus, 30% Local**

### Monthly Token Estimates
Assuming 500-1,000 leads processed per month with full enrichment pipeline:

| Activity | Input Tokens | Output Tokens |
|----------|-------------|---------------|
| Lead enrichment (500-1K leads) | 1.0-2.0M | 200-400K |
| Email/message generation | 300-600K | 150-300K |
| Content creation (blog, social) | 200-400K | 100-200K |
| Report generation | 200-400K | 100-200K |
| Ad hoc queries and analysis | 300-600K | 100-200K |
| **Total** | **2.0-4.0M** | **650K-1.3M** |

### Monthly Cost Calculation

**Without prompt caching:**
| Model | Input Cost | Output Cost | Subtotal |
|-------|-----------|-------------|----------|
| Haiku (50% of tokens) | 1.0-2.0M x $0.80/M = $0.80-1.60 | 325-650K x $4/M = $1.30-2.60 | $2.10-4.20 |
| Sonnet (15% of tokens) | 300-600K x $3/M = $0.90-1.80 | 97-195K x $15/M = $1.46-2.93 | $2.36-4.73 |
| Opus (5% of tokens) | 100-200K x $15/M = $1.50-3.00 | 32-65K x $75/M = $2.44-4.88 | $3.94-7.88 |
| Local Ollama (30%) | $0 | $0 | $0 |
| **Total without caching** | | | **$8.40-16.81** |

**With prompt caching (50-80% cache hit rate on system prompts and repeated context):**
- System prompts and enrichment templates are highly cacheable
- Estimated cache hit rate: 60-70% of input tokens
- Cached token cost is 90% cheaper (Haiku) to 90% cheaper (Opus)
- **Estimated savings: 40-60% on input token costs**

**Realistic monthly Claude API cost: $15-40/mo**

At higher volumes (2,000+ leads/month): $40-80/mo

### Cost Optimization Tactics
1. **Prompt caching**: Reuse system prompts aggressively. The OpenClaw enrichment pipeline uses the same system prompt for every lead -- cache it.
2. **Model routing**: Every request goes through a local classifier first. Only escalate to Sonnet/Opus when Haiku or local models cannot handle the task.
3. **Batch processing**: Group similar tasks and process them together to maximize cache hits.
4. **Output length control**: Set max_tokens appropriately. A lead classification needs 50 tokens, not 500.
5. **Local-first for development**: When building and testing prompts, use Ollama. Only switch to Claude API for production runs.

---

## Ollama (Local LLM via Mac Mini)

- **Monthly cost: $0**
- Runs on your Mac Mini hardware (cost covered in infrastructure-costs.md)
- Models are free to download (open weights: Llama, Mistral, Qwen, Phi, Gemma, DeepSeek)
- No per-token charges, no rate limits, no data leaving your machine
- Performance depends on model size and Mac Mini configuration

### Recommended Local Models for OpenClaw Tasks
| Model | Size | RAM Needed | Use Case |
|-------|------|-----------|----------|
| Llama 3.1 8B | 4.7GB (Q4) | ~6GB | Simple classification, routing |
| Mistral 7B Instruct | 4.1GB (Q4) | ~6GB | Data extraction, formatting |
| Qwen 2.5 14B | 8.5GB (Q4) | ~11GB | Content drafting, summarization |
| DeepSeek-R1 14B Distill | 8.5GB (Q4) | ~11GB | Reasoning tasks, analysis |
| Llama 3.1 70B | 40GB (Q4) | ~44GB | Complex tasks (stop other services first) |

---

## Data and Enrichment APIs

### DataForSEO -- $49/mo
- Your current plan. No change with OpenClaw.
- Provides: SERP data, keyword rankings, backlink data, domain metrics.
- Used in: SEO audit pipeline, competitor analysis, lead qualification (checking prospect's SEO health).
- Optimization: Cache results in Supabase to avoid re-fetching the same domains. Set TTL of 7-14 days for SEO metrics.

### Serper -- ~$50/mo
- Your current plan. No change with OpenClaw.
- Provides: Google Search API results (faster and cheaper than Google's official API for many use cases).
- Used in: Lead research, content research, competitive intelligence.
- Optimization: Deduplicate searches. If you are enriching 10 leads from the same industry, batch the industry research query once rather than per-lead.

### Clay.com -- $49-149/mo
- Depends on your current plan and credit usage.
- Provides: People and company enrichment, waterfall enrichment across 50+ data providers.
- Used in: Lead enrichment pipeline (finding emails, phone numbers, company details, tech stack).
- Plans:
  - Starter ($49/mo): 1,000 credits/mo -- enough for ~200-500 enriched leads
  - Explorer ($99/mo): 5,000 credits/mo -- enough for ~1,000-2,500 enriched leads
  - Pro ($149/mo): 10,000 credits/mo -- for high-volume prospecting
- Optimization: Use Clay's waterfall enrichment to try cheap providers first. Pre-filter leads with free data (Google Places, website scraping) before spending Clay credits.

### ZeroBounce -- $15-40/mo
- Your current usage. Email verification before sending.
- Pricing: Pay-as-you-go, roughly $0.008-0.01 per verification.
- At 1,500-4,000 verifications/month: $15-40.
- Used in: Email validation step before outreach sequences.
- Optimization: Only verify emails you actually plan to contact. If a lead scores below your threshold, skip verification.

---

## Communication and Outreach APIs

### Brevo (Email) -- Free to $25/mo
- Free tier: 300 emails/day (9,000/month).
- Starter plan ($25/mo): 20,000 emails/month, no daily limit.
- Used in: Email outreach sequences, nurture campaigns, transactional emails.
- If your volume stays under 9,000/month, the free tier works.
- Optimization: Segment your list aggressively. Only send to verified, qualified leads. This keeps volume (and cost) down while improving deliverability.

### Buffer (Social Media) -- Free to $15/mo
- Free plan: 3 channels, 10 scheduled posts per channel.
- Essentials ($6/mo per channel): unlimited scheduling, analytics.
- Used in: Social media content distribution (LinkedIn, Twitter/X, etc.).
- For 2-3 channels: $0-15/mo.

### Twilio (WhatsApp Business API) -- $5-20/mo
- **New cost with OpenClaw** (if you implement WhatsApp outreach).
- WhatsApp Business API pricing:
  - Conversation-based pricing: $0.005-0.08 per conversation (varies by category and country).
  - Marketing conversations (US): ~$0.025 each
  - Utility conversations (US): ~$0.015 each
  - Service conversations: free for 1,000/month, then ~$0.008 each
- Estimated volume: 200-800 conversations/month.
- **Estimated cost: $5-20/mo**
- Twilio account minimum: no monthly minimum, pay as you go.
- Twilio phone number: $1/mo for a US number (needed as sender).

---

## Platform and Infrastructure APIs

### Google APIs -- $0-10/mo
- **Google Places API**: $0.017 per request (after $200/mo free credit). Used for local business enrichment. At 500-2,000 requests/month: usually covered by free credit.
- **Google Slides API**: Free (part of Google Workspace). Used for presentation generation.
- **Google Sheets API**: Free. Used for data import/export.
- **Google My Business API**: Free. Used for local SEO data.
- Most usage stays within Google's $200/mo free Cloud credit.
- **Realistic cost: $0-5/mo** (only if you exceed free tier on Places API).

### Supabase -- $0-25/mo
- **Free tier**: 500MB database, 1GB file storage, 50,000 monthly active users, 500K edge function invocations.
- **Pro tier ($25/mo)**: 8GB database, 100GB file storage, no MAU limits.
- For initial OpenClaw deployment, the free tier is sufficient.
- Upgrade to Pro when your lead database exceeds ~50,000 records or you need more storage for cached API responses.
- **Planning cost: $0/mo initially, $25/mo when scaling**

### Airtable -- $0-20/mo
- Free tier: 1,000 records per base, 1GB attachments.
- Team plan ($20/user/mo): 50,000 records, 20GB attachments.
- Used in: Workflow tracking, pipeline management, possibly as a lightweight CRM layer.
- If you keep Airtable usage lightweight (dashboards, tracking), free tier works.
- **Planning cost: $0-20/mo**

### Vercel -- $0-20/mo
- Free tier (Hobby): sufficient for personal projects, client dashboards.
- Pro ($20/mo): commercial use, more bandwidth, analytics.
- Used in: Hosting client-facing dashboards, mini-sites, audit report pages.
- **Planning cost: $0/mo initially, $20/mo if hosting client sites**

### Tailscale -- $0/mo
- Free for personal use (up to 100 devices).
- Used in: Secure remote access to your Mac Mini from anywhere.
- Creates a private mesh VPN so you can SSH into your Mac Mini, access n8n dashboard, etc.
- **Cost: $0/mo**

---

## Total Monthly API/Service Cost Summary

### Conservative Estimate (Low Volume, Free Tiers)
| Category | Service | Monthly Cost |
|----------|---------|-------------|
| AI/LLM | Claude API | $15 |
| AI/LLM | Ollama | $0 |
| Data | DataForSEO | $49 |
| Data | Serper | $50 |
| Data | Clay.com (Starter) | $49 |
| Data | ZeroBounce | $15 |
| Comms | Brevo (free) | $0 |
| Comms | Buffer (free) | $0 |
| Comms | Twilio/WhatsApp | $5 |
| Platform | Google APIs | $0 |
| Platform | Supabase (free) | $0 |
| Platform | Airtable (free) | $0 |
| Platform | Vercel (free) | $0 |
| Platform | Tailscale | $0 |
| Content | Gamma (Plus) | $10 |
| **Total** | | **$193/mo** |

### Moderate Estimate (Growing Volume, Some Paid Tiers)
| Category | Service | Monthly Cost |
|----------|---------|-------------|
| AI/LLM | Claude API | $30 |
| AI/LLM | Ollama | $0 |
| Data | DataForSEO | $49 |
| Data | Serper | $50 |
| Data | Clay.com (Explorer) | $99 |
| Data | ZeroBounce | $25 |
| Comms | Brevo (Starter) | $25 |
| Comms | Buffer | $10 |
| Comms | Twilio/WhatsApp | $10 |
| Platform | Google APIs | $5 |
| Platform | Supabase (Pro) | $25 |
| Platform | Airtable (free) | $0 |
| Platform | Vercel (free) | $0 |
| Platform | Tailscale | $0 |
| Content | Gamma (Plus) | $10 |
| **Total** | | **$338/mo** |

### High Estimate (High Volume, Full Paid Tiers)
| Category | Service | Monthly Cost |
|----------|---------|-------------|
| AI/LLM | Claude API | $60 |
| AI/LLM | Ollama | $0 |
| Data | DataForSEO | $49 |
| Data | Serper | $50 |
| Data | Clay.com (Pro) | $149 |
| Data | ZeroBounce | $40 |
| Comms | Brevo (Starter) | $25 |
| Comms | Buffer | $15 |
| Comms | Twilio/WhatsApp | $20 |
| Platform | Google APIs | $10 |
| Platform | Supabase (Pro) | $25 |
| Platform | Airtable (Team) | $20 |
| Platform | Vercel (Pro) | $20 |
| Platform | Tailscale | $0 |
| Content | Gamma (Pro) | $20 |
| **Total** | | **$503/mo** |

---

## Cost Scaling Analysis

### How Costs Change With Volume

| Leads/Month | Claude API | Clay.com | ZeroBounce | Twilio | Other (flat) | Total APIs |
|-------------|-----------|---------|------------|--------|-------------|-----------|
| 250 | $10 | $49 | $10 | $3 | $109 | $181 |
| 500 | $20 | $49 | $15 | $5 | $109 | $198 |
| 1,000 | $30 | $99 | $25 | $10 | $109 | $273 |
| 2,000 | $50 | $149 | $35 | $15 | $114 | $363 |
| 5,000 | $80 | $149+ | $50 | $25 | $124 | $428+ |

**Key insight**: Most costs are flat (DataForSEO, Serper, infrastructure services). The variable costs are Claude API, Clay.com credits, ZeroBounce verifications, and Twilio conversations. This means doubling your lead volume does NOT double your total costs -- it increases total spend by roughly 20-40%.

### Cost Per Lead

| Volume | Total Monthly Cost | Cost Per Lead |
|--------|-------------------|---------------|
| 250 leads | ~$240 (incl. infra) | $0.96/lead |
| 500 leads | ~$255 | $0.51/lead |
| 1,000 leads | ~$330 | $0.33/lead |
| 2,000 leads | ~$420 | $0.21/lead |

Economies of scale are significant. The more leads you process, the cheaper each lead becomes because fixed costs are spread across more units.

---

## Gamma (AI Presentations) -- $10-20/mo

- **New cost with OpenClaw** (for autonomous presentation generation via Gamma MCP).
- Plus tier ($10/mo): Unlimited generations, unlimited AI images, PPTX/PDF export without watermark.
- Pro tier ($20/mo): Premium AI image models, custom branding, advanced features.
- **Recommendation:** Start with Plus ($10/mo). Upgrade to Pro if generating 10+ client-facing decks per month.
- Used in: Pitch decks, monthly reports, strategy proposals, competitor analyses.
- See [Gamma MCP Integration](../08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md) for details.

---

## Cost Monitoring and Alerts

### Set Up Spending Alerts For:
1. **Anthropic Console**: Set a monthly spending limit. Start at $50/mo and adjust.
2. **Clay.com**: Monitor credit usage weekly. Set alerts at 50% and 80% of monthly credits.
3. **Twilio**: Set a spending cap in the Twilio console. Start at $25/mo.
4. **Google Cloud**: The $200/mo free credit covers most usage, but set a budget alert at $10/mo just in case.
5. **ZeroBounce**: Monitor verification count. Only verify emails for qualified leads.

### Monthly Cost Review Checklist
- [ ] Check Anthropic API dashboard for token usage trends
- [ ] Review Clay.com credit consumption vs leads enriched
- [ ] Audit ZeroBounce verifications -- are you verifying junk leads?
- [ ] Check Twilio conversation logs -- are WhatsApp messages converting?
- [ ] Compare actual spend to budget and adjust model routing if needed

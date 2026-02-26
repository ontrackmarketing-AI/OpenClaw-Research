# Rise Local Lead Pipeline -- Integration with OpenClaw

## System Overview

Rise Local is a full lead generation pipeline that discovers local businesses, enriches their data with multi-source signals, scores them with a 15-signal pain model, and routes qualified leads into outreach sequences. The system is currently implemented as Python scripts orchestrated by n8n with Supabase as the data store.

**Current Pipeline Architecture:**
```
Discovery          Enrichment          Scoring           Outreach
(Google Places) -> (Clay/BuiltWith) -> (15-signal) ->  (Email sequences)
     |                  |                  |                 |
     v                  v                  v                 v
  Supabase           Supabase          Supabase          Supabase
  (raw leads)        (enriched)        (scored)          (outreach log)
     |                  |                  |                 |
     +------ n8n orchestrates all stages, triggers, retries ------+
```

---

## Pipeline Stages in Detail

### Stage 1: Discovery (Google Places API)

**Current implementation:**
- Python script: `discovery/google_places.py`
- Input: target industry, geographic area (city/zip/radius)
- Process: queries Google Places API with category keywords, paginates through all results
- Output: raw business records with name, address, phone, website, Google rating, review count, place ID
- Storage: `supabase.leads` table with `stage = 'discovered'`

**Volume:** Typically 200-500 leads per geographic search. Rate limited by Google Places API (depends on billing tier).

**Cost:** Google Places API: $17 per 1,000 requests (Nearby Search). A full city scan may cost $5-15.

### Stage 2: Enrichment (Clay + BuiltWith + Others)

**Current implementation:**
- Python script: `enrichment/clay_enricher.py` and `enrichment/builtwith_checker.py`
- Sources:
  1. **Clay:** Company data, employee count, revenue estimate, social profiles, tech stack
  2. **BuiltWith:** Website technology profiling (CMS, analytics, marketing tools, ecommerce platform)
  3. **Google PageSpeed Insights:** Site performance score, Core Web Vitals
  4. **Social media scraping:** Facebook page likes, Instagram followers, last post date
  5. **Domain WHOIS:** Domain age, registrar, SSL certificate status

**Enrichment data model (added fields):**
```json
{
  "employee_count": 12,
  "estimated_revenue": "$500K-$1M",
  "website_tech": ["WordPress", "WooCommerce", "Google Analytics"],
  "has_crm": false,
  "has_marketing_automation": false,
  "has_chatbot": false,
  "pagespeed_mobile": 42,
  "pagespeed_desktop": 67,
  "facebook_likes": 234,
  "instagram_followers": 890,
  "last_social_post_days_ago": 45,
  "domain_age_years": 3.2,
  "ssl_valid": true,
  "google_rating": 4.2,
  "google_review_count": 47
}
```

**Cost per lead:** Clay enrichment ~$0.05-0.10/lead, BuiltWith ~$0.02/lead, PageSpeed free, total ~$0.10-0.15/lead.

### Stage 3: Scoring (15-Signal Pain Model)

**Current implementation:**
- Python script: `scoring/pain_scorer.py`
- Calculates a composite "pain score" from 0-100 indicating how badly a business needs marketing help.

**The 15 Signals:**

| # | Signal | Weight | Scoring Logic | Max Points |
|---|---|---|---|---|
| 1 | No website or broken website | 10 | 10 if no site, 5 if site returns 4xx/5xx | 10 |
| 2 | Low PageSpeed mobile score | 7 | `max(0, (50 - pagespeed_mobile) / 50 * 7)` | 7 |
| 3 | No Google Analytics / Tag Manager | 5 | 5 if neither present in tech stack | 5 |
| 4 | Low Google rating (< 4.0) | 6 | `max(0, (4.0 - rating) / 4.0 * 6)` | 6 |
| 5 | Few Google reviews (< 20) | 6 | `max(0, (20 - review_count) / 20 * 6)` | 6 |
| 6 | No social media presence | 5 | 5 if no Facebook or Instagram found | 5 |
| 7 | Stale social media (no post in 30+ days) | 6 | 6 if > 60 days, 3 if 30-60 days | 6 |
| 8 | Low social following (< 500 combined) | 4 | `max(0, (500 - combined_followers) / 500 * 4)` | 4 |
| 9 | No CRM detected | 7 | 7 if no CRM in tech stack | 7 |
| 10 | No marketing automation | 7 | 7 if no email/marketing automation tool | 7 |
| 11 | No chatbot / live chat | 4 | 4 if no chatbot widget detected | 4 |
| 12 | Outdated CMS or no CMS | 5 | 5 if no CMS, 3 if outdated version | 5 |
| 13 | No SSL certificate | 5 | 5 if HTTP only or expired SSL | 5 |
| 14 | Old domain (> 5 years) without modern tools | 8 | 8 if domain > 5y old but scores high on signals 2-11 | 8 |
| 15 | Employee count in sweet spot (5-50) | 15 | 15 if 5-50 employees; 8 if 2-4 or 51-100; 0 otherwise | 15 |

**Total possible score: 100 points.**

**Score tiers:**
- 70-100: Hot lead (high pain, likely needs help urgently)
- 50-69: Warm lead (moderate pain, worth reaching out)
- 30-49: Cool lead (some pain, lower priority)
- 0-29: Cold lead (minimal pain, deprioritize or skip)

**Scoring function (current Python):**
```python
def calculate_pain_score(lead: dict) -> dict:
    score = 0
    breakdown = {}

    # Signal 1: Website presence
    if not lead.get('website'):
        breakdown['no_website'] = 10
        score += 10
    elif lead.get('website_status_code', 200) >= 400:
        breakdown['broken_website'] = 5
        score += 5

    # Signal 2: PageSpeed
    mobile_score = lead.get('pagespeed_mobile', 50)
    ps_pain = max(0, (50 - mobile_score) / 50 * 7)
    breakdown['pagespeed_pain'] = round(ps_pain, 1)
    score += ps_pain

    # Signal 3: Analytics
    tech = lead.get('website_tech', [])
    if not any(t in tech for t in ['Google Analytics', 'Google Tag Manager', 'Plausible', 'Matomo']):
        breakdown['no_analytics'] = 5
        score += 5

    # ... signals 4-15 follow same pattern ...

    # Signal 15: Employee sweet spot
    emp = lead.get('employee_count', 0)
    if 5 <= emp <= 50:
        breakdown['employee_sweet_spot'] = 15
        score += 15
    elif 2 <= emp <= 4 or 51 <= emp <= 100:
        breakdown['employee_adjacent'] = 8
        score += 8

    return {
        'pain_score': round(score, 1),
        'tier': classify_tier(score),
        'breakdown': breakdown,
        'top_pain_points': sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
    }
```

### Stage 4: Outreach (Email Sequences)

**Current implementation:**
- Python script: `outreach/email_sender.py`
- Email provider: likely Instantly, Smartlead, or custom SMTP
- Sequence: 3-touch email over 10 days
- Personalization: uses pain score breakdown to customize email copy

**Sequence structure:**
1. **Day 0 -- Initial outreach:** Highlights their top 2 pain points, offers free audit
2. **Day 3 -- Follow-up:** Shares a relevant case study or quick win tip
3. **Day 7 -- Final touch:** Urgency angle, limited-time offer, or alternate CTA (book a call)

---

## Integration with OpenClaw

### OpenClaw as Pipeline Orchestrator

Replace manual pipeline execution with OpenClaw as the autonomous orchestrator. OpenClaw decides when to run each stage, handles errors, and learns from results.

**Current state:** n8n triggers pipeline stages on a schedule or manually. Each stage is a separate n8n workflow.

**Target state:** OpenClaw has skills for each pipeline stage. It can:
- Autonomously decide which geographies/industries to target
- Run discovery when lead inventory is low
- Enrich leads in batches to manage API costs
- Score and route leads based on current capacity
- Launch and manage outreach sequences
- Learn from results (which lead profiles convert best)

### Skills Mapping

| Pipeline Stage | OpenClaw Skill Name | Input | Output | Dependencies |
|---|---|---|---|---|
| Discovery | `rise_local_discover` | Industry, geography, radius | Raw lead records in Supabase | Google Places API key |
| Enrichment | `rise_local_enrich` | Lead IDs to enrich | Enriched records in Supabase | Clay API, BuiltWith API |
| Scoring | `rise_local_score` | Lead IDs to score | Scored records with breakdown | None (pure computation) |
| Outreach | `rise_local_outreach` | Scored lead IDs, sequence template | Outreach log entries | Email provider credentials |
| Full Pipeline | `rise_local_full_run` | Industry, geography | End-to-end pipeline execution | All of the above |
| Analytics | `rise_local_analytics` | Date range, filters | Pipeline performance metrics | Supabase read access |

### Memory Integration

Pipeline results feed into OpenClaw's memory system so it can learn and improve over time.

**What gets stored in OpenClaw memory:**

| Memory Type | Content | Purpose |
|---|---|---|
| Episodic | "Ran pipeline for dentists in Austin TX, found 340 leads, 42 scored hot, 8 responded to outreach" | Track what was done and results |
| Semantic | "Dentists with 10-30 employees and no CRM respond best to email sequence A" | Learned patterns about what works |
| Procedural | "When enrichment fails for a lead, retry once after 1 hour, then mark as unenrichable" | Error handling knowledge |
| Statistical | Conversion rates by industry, geography, pain score tier | Quantitative performance data |

**Memory update triggers:**
- After each pipeline run: log the run parameters and top-line results
- After outreach responses come in: update conversion data and best-performing segments
- Monthly: synthesize a "what we learned" summary from the month's pipeline data

---

## Migration Plan

### Phase 1: Connect via n8n Webhooks (Immediate, Week 1)

**Goal:** OpenClaw can trigger existing pipeline stages without modifying the pipeline code.

**Implementation:**
1. Add webhook triggers to each existing n8n pipeline workflow
2. Create OpenClaw skills that call these webhooks

```python
# openclaw/skills/rise_local_webhook.py

class RiseLocalWebhookSkill:
    """Triggers Rise Local pipeline stages via n8n webhooks."""

    N8N_BASE = "http://localhost:5678/webhook"

    async def discover(self, industry: str, geography: str, radius_km: int = 25):
        return await self._trigger("rise-local-discover", {
            "industry": industry,
            "geography": geography,
            "radius_km": radius_km
        })

    async def enrich(self, lead_ids: list[str], sources: list[str] = None):
        return await self._trigger("rise-local-enrich", {
            "lead_ids": lead_ids,
            "sources": sources or ["clay", "builtwith", "pagespeed"]
        })

    async def score(self, lead_ids: list[str] = None, batch: str = "latest"):
        return await self._trigger("rise-local-score", {
            "lead_ids": lead_ids,
            "batch": batch
        })

    async def outreach(self, lead_ids: list[str], sequence_id: str):
        return await self._trigger("rise-local-outreach", {
            "lead_ids": lead_ids,
            "sequence_id": sequence_id
        })

    async def _trigger(self, webhook_path: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.N8N_BASE}/{webhook_path}",
                json=payload
            )
            response.raise_for_status()
            return response.json()
```

**n8n webhook setup for each workflow:**
- Add a Webhook node as the first node in each pipeline workflow
- Path: `rise-local-discover`, `rise-local-enrich`, `rise-local-score`, `rise-local-outreach`
- Method: POST
- Authentication: Header auth with shared secret

### Phase 2: Create OpenClaw Skills Wrapping Pipeline Scripts (Weeks 2-3)

**Goal:** OpenClaw directly executes pipeline logic via Python skill wrappers, bypassing n8n for individual stages.

**Implementation:**
1. Package each pipeline stage's Python script as an importable module
2. Create OpenClaw skills that import and call these modules directly
3. n8n remains as the fallback orchestrator but is no longer the primary path

```python
# openclaw/skills/rise_local_native.py

# Import existing pipeline modules
from rise_local.discovery.google_places import discover_leads
from rise_local.enrichment.clay_enricher import enrich_with_clay
from rise_local.enrichment.builtwith_checker import check_builtwith
from rise_local.scoring.pain_scorer import calculate_pain_score
from rise_local.outreach.email_sender import send_sequence

class RiseLocalNativeSkill:
    """Direct execution of Rise Local pipeline stages."""

    async def discover(self, industry: str, geography: str, radius_km: int = 25) -> dict:
        leads = await discover_leads(
            industry=industry,
            location=geography,
            radius=radius_km * 1000  # Convert to meters
        )
        # Store in Supabase
        stored = await self.supabase.table("leads").insert(leads).execute()
        # Log to OpenClaw memory
        await self.memory.log_episode(
            f"Discovered {len(leads)} {industry} leads in {geography}",
            metadata={"stage": "discovery", "count": len(leads)}
        )
        return {"leads_found": len(leads), "lead_ids": [l["id"] for l in stored.data]}

    async def enrich(self, lead_ids: list[str]) -> dict:
        results = {"enriched": 0, "failed": 0, "cost": 0.0}
        for lead_id in lead_ids:
            try:
                lead = await self.supabase.table("leads").select("*").eq("id", lead_id).single().execute()
                clay_data = await enrich_with_clay(lead.data)
                builtwith_data = await check_builtwith(lead.data.get("website"))

                merged = {**lead.data, **clay_data, **builtwith_data, "stage": "enriched"}
                await self.supabase.table("leads").update(merged).eq("id", lead_id).execute()

                results["enriched"] += 1
                results["cost"] += 0.12  # Approximate per-lead cost
            except Exception as e:
                results["failed"] += 1
                await self.memory.log_episode(
                    f"Enrichment failed for lead {lead_id}: {str(e)}",
                    metadata={"stage": "enrichment", "error": True}
                )

        return results

    async def score(self, lead_ids: list[str]) -> dict:
        scored = []
        for lead_id in lead_ids:
            lead = await self.supabase.table("leads").select("*").eq("id", lead_id).single().execute()
            score_result = calculate_pain_score(lead.data)
            await self.supabase.table("leads").update({
                "pain_score": score_result["pain_score"],
                "pain_tier": score_result["tier"],
                "pain_breakdown": score_result["breakdown"],
                "stage": "scored"
            }).eq("id", lead_id).execute()
            scored.append({"id": lead_id, **score_result})

        tier_counts = {}
        for s in scored:
            tier_counts[s["tier"]] = tier_counts.get(s["tier"], 0) + 1

        return {"scored": len(scored), "tier_distribution": tier_counts}
```

**Key changes from Phase 1:**
- No n8n in the critical path for individual stages
- OpenClaw has direct Supabase access for reads and writes
- Memory logging is integrated into each skill execution
- Error handling is more granular (per-lead instead of per-batch)

### Phase 3: Rewrite as Native OpenClaw Skills (Months 2-3)

**Goal:** Pipeline stages are fully native OpenClaw skills with enhanced capabilities that the original scripts did not have.

**Enhancements over original pipeline:**

| Enhancement | Description |
|---|---|
| Intelligent targeting | OpenClaw uses memory to choose which industries/geographies to target based on past conversion data |
| Adaptive scoring | Pain score weights adjust based on which signals correlate with actual conversions |
| Dynamic sequences | Outreach email copy is personalized per lead using Claude, not just template variables |
| Cost optimization | OpenClaw tracks per-lead enrichment costs and skips expensive sources for low-potential leads |
| Auto-retry with backoff | Failed enrichments are retried with exponential backoff, not just logged |
| Batch intelligence | OpenClaw groups similar leads for batch enrichment to reduce API calls |
| Feedback loop | When a lead converts (or does not), the outcome is fed back to improve scoring |

---

## 15-Signal Pain Scoring as OpenClaw Skill

Embed the full scoring logic as a first-class OpenClaw skill with the ability to evolve.

```python
# openclaw/skills/pain_scorer.py

class PainScorerSkill:
    """15-signal pain scoring with adaptive weights."""

    # Default weights (can be overridden by learned weights from memory)
    DEFAULT_WEIGHTS = {
        'no_website': 10,
        'low_pagespeed': 7,
        'no_analytics': 5,
        'low_rating': 6,
        'few_reviews': 6,
        'no_social': 5,
        'stale_social': 6,
        'low_following': 4,
        'no_crm': 7,
        'no_marketing_automation': 7,
        'no_chatbot': 4,
        'outdated_cms': 5,
        'no_ssl': 5,
        'old_domain_no_tools': 8,
        'employee_sweet_spot': 15
    }

    async def score(self, lead: dict, use_adaptive_weights: bool = True) -> dict:
        weights = self.DEFAULT_WEIGHTS.copy()

        if use_adaptive_weights:
            learned = await self.memory.get("pain_score_weights")
            if learned:
                weights.update(learned)

        # ... (full scoring logic as defined above) ...

        return {
            'pain_score': round(total, 1),
            'tier': self._classify(total),
            'breakdown': breakdown,
            'weights_used': 'adaptive' if use_adaptive_weights else 'default',
            'top_pain_points': sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:5],
            'recommended_angle': self._recommend_angle(breakdown)
        }

    def _recommend_angle(self, breakdown: dict) -> str:
        """Suggest the best outreach angle based on pain points."""
        top_pain = max(breakdown, key=breakdown.get) if breakdown else None

        angles = {
            'no_website': "You need an online presence -- we can get you a site in 7 days",
            'low_pagespeed': "Your website is slow and losing customers -- we can fix that fast",
            'no_analytics': "You're flying blind without analytics -- let us show you what's working",
            'low_rating': "Your online reputation needs attention -- we have a review strategy",
            'few_reviews': "More reviews = more customers -- we'll help you get 50+ reviews",
            'no_social': "Your competitors are on social media and you're not -- let's fix that",
            'stale_social': "Your social media has gone quiet -- we'll bring it back to life",
            'no_crm': "You're losing leads without a CRM -- we'll set one up and fill it",
            'no_marketing_automation': "Manual marketing is eating your time -- let's automate it",
            'employee_sweet_spot': "Your business is the perfect size for marketing ROI -- let's talk"
        }

        return angles.get(top_pain, "We can help grow your business with targeted marketing")

    async def update_weights_from_outcomes(self, outcomes: list[dict]):
        """Learn from conversion outcomes to adjust signal weights.

        outcomes format: [
            {"lead_id": "...", "pain_breakdown": {...}, "converted": True/False}
        ]
        """
        # Simple approach: signals present in converted leads get weight boost,
        # signals present in non-converted leads get weight reduction
        adjustments = {}
        for outcome in outcomes:
            for signal, value in outcome["pain_breakdown"].items():
                if signal not in adjustments:
                    adjustments[signal] = {"boost": 0, "reduce": 0}
                if outcome["converted"]:
                    adjustments[signal]["boost"] += 1
                else:
                    adjustments[signal]["reduce"] += 1

        new_weights = self.DEFAULT_WEIGHTS.copy()
        for signal, adj in adjustments.items():
            if signal in new_weights:
                ratio = adj["boost"] / max(adj["boost"] + adj["reduce"], 1)
                # Adjust weight: if ratio > 0.5, boost; if < 0.5, reduce
                new_weights[signal] *= (0.8 + 0.4 * ratio)  # Range: 0.8x to 1.2x

        await self.memory.set("pain_score_weights", new_weights)
        return new_weights
```

---

## Intelligent Routing Based on Enrichment Results

OpenClaw adds decision intelligence that the original pipeline lacked.

**Routing rules (implemented as OpenClaw skill logic):**

| Enrichment Result | Routing Decision |
|---|---|
| Lead has website + WordPress + no WooCommerce | Route to "website upgrade" sequence |
| Lead has website + very low PageSpeed | Route to "site speed" sequence |
| Lead has no social media at all | Route to "social media starter" sequence |
| Lead has social but stale (30+ days) | Route to "social media revival" sequence |
| Lead has no CRM + 10+ employees | Route to "CRM consultation" sequence (high value) |
| Lead has high pain score (70+) + phone number | Flag for manual phone outreach (highest conversion) |
| Lead has low pain score (< 30) | Skip outreach, add to nurture drip (low touch) |
| Lead already using competitor tools | Route to "switching" sequence with competitive comparison |

**Implementation as n8n workflow or OpenClaw skill:**

```python
async def route_lead(self, lead: dict, score_result: dict) -> dict:
    """Determine the best outreach strategy for a scored lead."""

    tier = score_result['tier']
    breakdown = score_result['breakdown']
    top_pain = score_result['top_pain_points'][0][0] if score_result['top_pain_points'] else None

    routing = {
        'lead_id': lead['id'],
        'tier': tier,
        'actions': []
    }

    if tier == 'hot' and lead.get('phone'):
        routing['actions'].append({
            'type': 'flag_for_call',
            'priority': 'high',
            'reason': f"Hot lead with phone number. Top pain: {top_pain}"
        })

    if tier in ('hot', 'warm'):
        sequence = self._select_sequence(breakdown)
        routing['actions'].append({
            'type': 'email_sequence',
            'sequence_id': sequence,
            'personalization': {
                'angle': score_result.get('recommended_angle', ''),
                'pain_points': [p[0] for p in score_result['top_pain_points'][:3]]
            }
        })

    if tier == 'cool':
        routing['actions'].append({
            'type': 'nurture_drip',
            'frequency': 'monthly',
            'reason': 'Low pain score, keep warm for future'
        })

    if tier == 'cold':
        routing['actions'].append({
            'type': 'skip',
            'reason': 'Pain score too low, not worth outreach cost'
        })

    return routing
```

---

## Cost Tracking

OpenClaw monitors per-lead costs across the entire pipeline.

**Cost centers:**

| Stage | Cost Item | Approximate Cost |
|---|---|---|
| Discovery | Google Places API | $0.017/request, ~$0.05/lead (with pagination) |
| Enrichment | Clay | $0.05-0.10/lead |
| Enrichment | BuiltWith | $0.02/lead |
| Enrichment | PageSpeed API | Free |
| Scoring | Computation only | $0.00 (local) |
| Outreach | Email sending | $0.001-0.01/email depending on provider |
| **Total per lead** | | **$0.10-0.20** |

**Cost tracking in Supabase:**

```sql
CREATE TABLE pipeline_costs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    stage TEXT NOT NULL,
    service TEXT NOT NULL,
    cost_usd DECIMAL(10, 6) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    batch_id UUID  -- Group costs by pipeline run
);

-- View: cost per lead
CREATE VIEW lead_costs AS
SELECT
    lead_id,
    SUM(cost_usd) as total_cost,
    COUNT(DISTINCT stage) as stages_completed,
    MAX(timestamp) as last_activity
FROM pipeline_costs
GROUP BY lead_id;

-- View: cost per batch/run
CREATE VIEW batch_costs AS
SELECT
    batch_id,
    COUNT(DISTINCT lead_id) as leads_processed,
    SUM(cost_usd) as total_cost,
    SUM(cost_usd) / COUNT(DISTINCT lead_id) as cost_per_lead,
    MIN(timestamp) as started_at,
    MAX(timestamp) as completed_at
FROM pipeline_costs
GROUP BY batch_id;
```

**OpenClaw cost monitoring skill:**
```python
async def check_pipeline_costs(self, period: str = "this_month") -> dict:
    """Check pipeline costs and alert if over budget."""
    costs = await self.supabase.rpc("get_pipeline_costs", {"period": period}).execute()

    budget = await self.memory.get("pipeline_monthly_budget") or 500.00  # Default $500/month

    return {
        "period": period,
        "total_spent": costs.data["total"],
        "budget": budget,
        "remaining": budget - costs.data["total"],
        "utilization": f"{costs.data['total'] / budget * 100:.1f}%",
        "cost_per_lead": costs.data["avg_per_lead"],
        "leads_processed": costs.data["lead_count"],
        "alert": costs.data["total"] > budget * 0.8  # Alert at 80% budget
    }
```

---

## Supabase Schema for Rise Local Pipeline

**Core tables (already exist, verify and augment as needed):**

```sql
-- Main leads table
CREATE TABLE leads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    google_place_id TEXT UNIQUE,
    business_name TEXT NOT NULL,
    industry TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    phone TEXT,
    website TEXT,
    email TEXT,
    -- Discovery data
    google_rating DECIMAL(2,1),
    google_review_count INTEGER,
    -- Enrichment data
    employee_count INTEGER,
    estimated_revenue TEXT,
    website_tech JSONB DEFAULT '[]',
    has_crm BOOLEAN,
    has_marketing_automation BOOLEAN,
    has_chatbot BOOLEAN,
    pagespeed_mobile INTEGER,
    pagespeed_desktop INTEGER,
    facebook_likes INTEGER,
    instagram_followers INTEGER,
    last_social_post_days_ago INTEGER,
    domain_age_years DECIMAL(4,1),
    ssl_valid BOOLEAN,
    -- Scoring data
    pain_score DECIMAL(5,1),
    pain_tier TEXT,
    pain_breakdown JSONB,
    -- Pipeline tracking
    stage TEXT DEFAULT 'discovered',
    batch_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    enriched_at TIMESTAMPTZ,
    scored_at TIMESTAMPTZ,
    outreach_started_at TIMESTAMPTZ,
    -- Outcome tracking
    responded BOOLEAN DEFAULT FALSE,
    converted BOOLEAN DEFAULT FALSE,
    conversion_value DECIMAL(10,2),
    notes TEXT
);

-- Indexes for common queries
CREATE INDEX idx_leads_stage ON leads(stage);
CREATE INDEX idx_leads_pain_tier ON leads(pain_tier);
CREATE INDEX idx_leads_industry_city ON leads(industry, city);
CREATE INDEX idx_leads_pain_score ON leads(pain_score DESC);
```

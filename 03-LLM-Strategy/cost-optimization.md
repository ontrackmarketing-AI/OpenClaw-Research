# Cost Optimization Strategy

## Overview

Without optimization, an active OpenClaw deployment can easily run $100-200+/month in API costs. With the strategies in this document, the target is $20-60/month for equivalent functionality. The key insight: most agent tasks do not require the most expensive model, and most tokens sent to the API are repetitive (system prompts, tool definitions) and can be cached.

This document prioritizes strategies by impact -- implement them in order for maximum ROI on your time.

---

## Baseline: Unoptimized Monthly Costs

Assumptions: moderate usage -- ~100 agent interactions/day, mix of lead gen, CRM management, and content generation.

| Cost Category                 | Monthly Estimate |
|-------------------------------|-----------------|
| All tasks on Sonnet 4.5       | $80-150         |
| All tasks on Opus 4.6         | $300-600+       |
| All tasks on Haiku 4.5        | $25-50          |

**Realistic unoptimized scenario** (Sonnet as default, occasional Opus): **$100-200/month**

---

## Optimization Strategies (Ordered by Impact)

### Strategy 1: Prompt Caching

**Impact: HIGH -- Saves 50-90% on cached tokens**
**Effort: LOW -- Configuration change, not code change**

Every OpenClaw request sends the same system prompt and tool definitions. Without caching, you pay full price for these tokens on every single request. With caching, you pay full price once and then 10% for subsequent requests (within a 5-minute window).

**Typical savings breakdown:**

| Component          | Tokens | Per-request cost (Sonnet) | With caching  |
|--------------------|--------|--------------------------|---------------|
| System prompt      | 1,500  | $0.0045                  | $0.00045      |
| Tool definitions   | 2,000  | $0.0060                  | $0.00060      |
| Few-shot examples  | 1,000  | $0.0030                  | $0.00030      |
| **Subtotal (prefix)** | 4,500 | **$0.0135/request**     | **$0.00135/request** |

At 3,000 requests/month: **$40.50 -> $4.05** (savings: $36.45/month)

**How to implement:**
1. Add `cache_control` markers to system prompts and tool definitions
2. Ensure requests from the same skill use the same prefix (don't randomize system prompts)
3. Monitor cache hit rates in logs
4. See `claude-api-config.md` for implementation details

---

### Strategy 2: Model Routing

**Impact: HIGH -- Saves 40-70% by using cheaper models for most tasks**
**Effort: MEDIUM -- Requires classifying tasks and configuring per-skill models**

The core of the routing strategy (detailed in `model-routing.md`):

| Task tier                    | % of tasks | Model           | Relative cost |
|------------------------------|-----------|-----------------|---------------|
| Simple (format, classify)    | 40%       | Ollama (free)   | $0            |
| Standard (enrich, generate)  | 40%       | Haiku 4.5       | 1x            |
| Complex (multi-step, creative)| 15%      | Sonnet 4.5      | 4x            |
| Critical (client-facing)     | 5%        | Opus 4.6        | 19x           |

**Savings calculation (3,000 tasks/month, avg 2K input + 1K output tokens):**

| Scenario          | Monthly cost |
|-------------------|-------------|
| All Sonnet        | $135.00     |
| With routing      | $38.40      |
| **Savings**       | **$96.60 (71.6%)** |

---

### Strategy 3: Local Models via Ollama

**Impact: HIGH for eligible tasks -- $0 marginal cost**
**Effort: MEDIUM -- Requires Ollama setup and model testing**

Every task handled by a local model costs nothing beyond electricity (~$5-10/month for the Mac Mini running 24/7). Target tasks for local models:

- Data formatting and normalization (JSON reshaping, phone number formatting)
- Basic classification (lead scoring rules, category assignment)
- Template filling (merge fields into templates)
- Embedding generation (for RAG/search)
- Simple extraction (name, email, company from text blocks)

**Projected local task volume:** 1,000-1,500 tasks/month
**API cost if these ran on Haiku instead:** $8-15/month
**Local cost:** $0

The savings here are modest in absolute terms but compound over time, and local models provide the critical benefit of zero-latency, zero-dependency inference -- they work even if Anthropic's API is down.

---

### Strategy 4: Batches API

**Impact: MEDIUM -- 50% discount on batch-eligible tasks**
**Effort: LOW -- Use batch endpoint instead of real-time endpoint**

Any task that doesn't need an immediate response can use the Batches API for a 50% discount. Candidate tasks:

| Task                        | Frequency       | Batch-eligible? |
|-----------------------------|----------------|-----------------|
| Overnight lead enrichment   | Daily          | Yes             |
| Weekly CRM data cleanup     | Weekly         | Yes             |
| Bulk email generation       | 2-3x/week      | Yes             |
| Report generation           | Weekly/monthly  | Yes             |
| Real-time chat responses    | Continuous      | No              |
| On-demand tool calls        | Ad-hoc          | No              |

**Estimated batch-eligible volume:** 30-40% of API calls
**Savings:** If $50/month in API calls are batch-eligible, that is $25/month saved.

---

### Strategy 5: Token Management

**Impact: MEDIUM -- Reduces tokens per request by 20-40%**
**Effort: MEDIUM -- Requires prompt engineering and configuration**

Every token sent or received costs money. Reducing token counts directly reduces costs.

**Techniques:**

1. **Trim conversation history aggressively.** Agents do not need the full conversation. Keep only the last 3-5 turns; summarize older turns.

2. **Compress context injection.** When injecting CRM data or memory into prompts, include only relevant fields, not entire records.
   ```
   BAD:  Include full CRM record (50+ fields, 2K tokens)
   GOOD: Include only relevant fields (5-10 fields, 200 tokens)
   ```

3. **Limit tool result size.** When a tool returns data, truncate or summarize before passing back to the model.
   ```
   BAD:  Return full API response (5K tokens)
   GOOD: Extract relevant fields (500 tokens)
   ```

4. **Use concise system prompts.** Write system prompts that are clear but not verbose. Every unnecessary word costs money across thousands of requests.

5. **Avoid redundant tool calls.** Cache tool results within a session so the agent doesn't call the same tool twice with the same parameters.

**Example savings:**
- Reducing average input tokens from 3,000 to 2,000 per request
- At 3,000 requests/month on Haiku: saves $2.40/month
- At 500 requests/month on Sonnet: saves $1.50/month
- Cumulative: ~$4-5/month (small but compounds)

---

### Strategy 6: Response Caching

**Impact: LOW-MEDIUM -- Eliminates redundant API calls entirely**
**Effort: MEDIUM -- Requires caching infrastructure**

Some queries are functionally identical and produce the same answer. Caching these at the application level means zero API cost for repeat queries.

**Good candidates for response caching:**
- Company lookup data (doesn't change frequently)
- Industry classification for a given company
- Standard CRM field descriptions
- Template generation for the same template type

**Implementation:**
- Use a local key-value store (Redis, SQLite, or even filesystem)
- Cache key = hash of (model + system_prompt + user_message + tools)
- TTL: 1 hour to 24 hours depending on data freshness needs
- Invalidation: Clear cache when underlying data changes

**Not good candidates:**
- Anything involving current/live data
- Creative content (you want variety)
- Personalized responses (different context each time)

---

### Strategy 7: Circuit Breakers

**Impact: LOW frequency but HIGH when it matters -- prevents cost catastrophes**
**Effort: LOW -- Simple configuration**

Runaway agents that enter infinite loops can burn through your entire monthly budget in minutes. Circuit breakers prevent this.

**Circuit breaker rules:**

| Rule                                  | Threshold          | Action                    |
|---------------------------------------|-------------------|---------------------------|
| Max tool calls per session            | 20 calls          | Stop agent, return error  |
| Max tokens per session                | 50K tokens         | Stop agent, return error  |
| Max cost per session                  | $1.00              | Stop agent, return error  |
| Max consecutive identical tool calls  | 3 identical calls  | Stop agent, return error  |
| Max session duration                  | 5 minutes          | Stop agent, return error  |
| Max daily spend per agent             | $10.00             | Disable agent until next day |
| Max monthly spend total               | Set in Anthropic console | API returns 403         |

**Implementation:** These should be enforced at the OpenClaw framework level, not at the API level. The Anthropic Console spend limit is a last-resort safety net.

---

## Projected Monthly Cost with All Optimizations

| Category                  | Unoptimized | Optimized    | Savings |
|---------------------------|-------------|-------------|---------|
| System prompt tokens      | $40.50      | $4.05        | $36.45  |
| Model routing (cheaper models) | --     | -$96.60 vs all-Sonnet | --  |
| Local model tasks         | $15.00      | $0.00        | $15.00  |
| Batch discount            | $25.00      | $12.50       | $12.50  |
| Token reduction           | --          | -$5.00       | $5.00   |
| Response caching          | --          | -$3.00       | $3.00   |

**Bottom line:**

| Scenario                    | Monthly Cost |
|-----------------------------|-------------|
| Unoptimized (all Sonnet)    | $135-200    |
| Partially optimized         | $50-80      |
| Fully optimized             | $20-40      |

**Target: $30/month** for a fully operational OpenClaw deployment handling ~100 agent tasks/day.

---

## Cost Monitoring and Tracking

### Per-Request Logging

Every API call should log:
- Timestamp
- Model used
- Skill/agent that made the call
- Input tokens, output tokens, cached tokens
- Calculated cost
- Whether the call succeeded or required fallback

### Dashboard Metrics (Build Over Time)

- **Daily spend** -- trend chart, alert if >2x average
- **Cost per task type** -- identify which skills cost the most
- **Model distribution** -- pie chart of calls by model (are you routing correctly?)
- **Cache hit rate** -- should be >80% for system prompt caching
- **Fallback rate** -- how often do local models fail and escalate to API?
- **Cost per lead** -- total API spend / leads generated (unit economics)

### Weekly Review Checklist

- [ ] Check total spend vs. budget
- [ ] Review top 5 most expensive skills -- can any be routed to a cheaper model?
- [ ] Check fallback logs -- are local models failing too often?
- [ ] Review any circuit breaker triggers -- what caused them?
- [ ] Validate cache hit rates -- are prompts staying stable?

---

## Cost Comparison: Common Tasks Before/After Optimization

| Task                          | Before (Sonnet, no caching) | After (optimized)          | Savings |
|-------------------------------|----------------------------|---------------------------|---------|
| Format 1 lead record          | $0.009                     | $0.000 (Ollama)           | 100%    |
| Enrich 1 lead (3 tool calls)  | $0.039                     | $0.012 (Haiku + caching)  | 69%     |
| Generate 1 outreach email     | $0.024                     | $0.007 (Haiku + caching)  | 71%     |
| Research report (10 tool calls)| $0.150                    | $0.105 (Sonnet + caching) | 30%     |
| Client proposal review        | $0.450                     | $0.420 (Opus, caching helps less) | 7%  |
| Batch enrich 100 leads        | $3.90                      | $0.60 (Haiku + batch + caching) | 85% |

---

## Implementation Priority

| Priority | Strategy           | Effort   | Impact   | When to Implement           |
|----------|--------------------|----------|----------|-----------------------------|
| 1        | Prompt caching     | Low      | High     | Day 1 -- immediate ROI      |
| 2        | Model routing      | Medium   | High     | Week 1 -- during skill setup|
| 3        | Spend limits       | Low      | Safety   | Day 1 -- prevent disasters  |
| 4        | Local models       | Medium   | High     | Week 1-2 -- with Ollama setup|
| 5        | Batches API        | Low      | Medium   | Week 2 -- for recurring tasks|
| 6        | Token management   | Medium   | Medium   | Ongoing -- optimize prompts |
| 7        | Response caching   | Medium   | Low-Med  | Month 2 -- after baseline data|
| 8        | Circuit breakers   | Low      | Safety   | Day 1 -- prevent disasters  |

---

## RESEARCH GAPS

- **OpenClaw cost tracking:** Does OpenClaw have built-in cost tracking per request, or does this need custom logging?
- **Prompt caching integration:** Does OpenClaw automatically use Anthropic prompt caching, or is manual configuration required?
- **Circuit breaker support:** Does OpenClaw have built-in circuit breakers for runaway agents?
- **Actual usage patterns:** The estimates above are based on projected usage. After 2-4 weeks of real usage, revisit these numbers with actual data.
- **OpenAI pricing comparison:** If using GPT-4o-mini as a Haiku alternative, compare actual costs and quality for common tasks.

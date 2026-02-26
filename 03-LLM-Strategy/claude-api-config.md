# Claude API Configuration for OpenClaw

## Overview

Claude (via the Anthropic API) is OpenClaw's primary cloud LLM provider. This document covers setup, model selection, rate limits, cost management, and advanced features like prompt caching and the Batches API.

You are currently paying for Claude API access directly through Anthropic. This gives you the most control over spend, rate limits, and feature access compared to using Claude through a third-party provider.

---

## API Setup

### 1. Generate API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API Keys** in the left sidebar
3. Click **Create Key**
4. Name it something descriptive: `openclaw-production` or `openclaw-dev`
5. Copy the key immediately -- it will not be shown again
6. Store securely (see Security section of this knowledge base)

### 2. Set Environment Variable

The API key must be available as an environment variable for OpenClaw to use.

**On Mac Mini (where OpenClaw runs):**
```bash
# Add to ~/.zshrc or ~/.bashrc
export ANTHROPIC_API_KEY="sk-ant-api03-your-key-here"

# Reload shell
source ~/.zshrc
```

**For n8n (if running as a service):**
Add to the n8n service configuration or .env file:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**For Docker-based deployment:**
```bash
docker run -e ANTHROPIC_API_KEY="sk-ant-api03-your-key-here" ...
```

### 3. Base URL Configuration

Default base URL: `https://api.anthropic.com`

If using a caching proxy (e.g., to cache responses locally), configure:
```
ANTHROPIC_BASE_URL=http://localhost:8080/v1
```

This is an advanced optimization -- start with the default URL.

---

## Available Models

### Model Comparison

| Model                          | API ID                          | Input Cost   | Output Cost  | Speed     | Quality   |
|--------------------------------|---------------------------------|-------------|-------------|-----------|-----------|
| Claude Opus 4.6               | `claude-opus-4-6`              | $15.00 / 1M | $75.00 / 1M | Slowest   | Best      |
| Claude Sonnet 4.5             | `claude-sonnet-4-5-20250929`   | $3.00 / 1M  | $15.00 / 1M | Fast      | Excellent |
| Claude Haiku 4.5              | `claude-haiku-4-5-20251001`    | $0.80 / 1M  | $4.00 / 1M  | Fastest   | Good      |

### When to Use Each Model

**Claude Haiku 4.5** -- The Workhorse (80% of API calls)
- Lead enrichment with standard tool use
- Email generation from templates
- Data summarization
- Standard chatbot responses
- CRM field extraction and population
- Basic content generation
- Any task where speed matters more than nuance

**Claude Sonnet 4.5** -- The All-Rounder (15% of API calls)
- Multi-step agentic workflows
- Complex tool chains (4+ sequential calls)
- Personalized content requiring creativity
- Analysis that requires nuanced judgment
- Tasks where Haiku produces unreliable results
- Default "upgrade" when Haiku is insufficient

**Claude Opus 4.6** -- The Expert (5% of API calls)
- Client-facing deliverables reviewed by no human
- Complex multi-document analysis and synthesis
- Novel problems outside trained patterns
- Final quality review of generated content
- High-stakes business analysis
- Tasks requiring the absolute best reasoning

---

## Rate Limits

Rate limits depend on your Anthropic usage tier. New accounts start at Tier 1.

### Rate Limits by Tier

| Tier   | Trigger (Spend)  | Requests/min | Input tokens/min | Output tokens/min |
|--------|------------------|-------------|------------------|-------------------|
| Tier 1 | $0 (new account) | 50          | 40,000           | 8,000             |
| Tier 2 | $40 spent        | 1,000       | 80,000           | 16,000            |
| Tier 3 | $200 spent       | 2,000       | 160,000          | 32,000            |
| Tier 4 | $2,000 spent     | 4,000       | 400,000          | 80,000            |

**Important:** These limits are per-model. Using Haiku does not count against your Sonnet limits.

**For OpenClaw:** You will likely start at Tier 1-2. The 50 req/min limit at Tier 1 can be a bottleneck for batch operations. Plan to reach Tier 2 ($40 spend) quickly to unlock 1,000 req/min.

### Handling Rate Limits in OpenClaw

```
Strategy:
1. Implement exponential backoff: wait 1s, 2s, 4s, 8s on 429 errors
2. Spread batch operations across time (don't send 100 requests simultaneously)
3. Use the Batches API for non-urgent bulk processing (separate rate limits)
4. Fallback to a different model if one model's rate limit is hit
```

---

## Spend Limits and Budget Management

### Setting Limits in Anthropic Console

1. Go to [console.anthropic.com](https://console.anthropic.com) -> **Plans & Billing**
2. Set a **monthly spend limit** -- this is a hard cap; API calls will fail once hit
3. Recommended initial limit: **$50/month** while testing, increase as needed
4. You can also set workspace-level limits if using multiple API keys

### Budget Monitoring

- Check spend in the Anthropic Console dashboard
- API responses include token usage in the response headers/body
- Build logging into OpenClaw to track per-task costs:

```
Per-request cost calculation:
  input_cost  = (input_tokens / 1,000,000) * model_input_price
  output_cost = (output_tokens / 1,000,000) * model_output_price
  total_cost  = input_cost + output_cost
```

### Budget Alerts

Anthropic Console supports email notifications when spend reaches certain thresholds. Set alerts at:
- 50% of monthly budget (early warning)
- 80% of monthly budget (action needed)
- 95% of monthly budget (critical)

---

## Extended Thinking

Extended thinking allows Claude to "think" before responding, producing higher quality output for complex reasoning tasks. Available on Sonnet 4.5 and Opus 4.6.

### When to Enable

- Complex multi-step analysis
- Tasks requiring mathematical or logical reasoning
- Ambiguous problems where the model needs to explore options
- Any task where a first-attempt answer is often wrong

### When NOT to Enable

- Simple formatting, extraction, or classification
- Speed-critical tasks (thinking adds 2-10 seconds)
- Tasks with clear, unambiguous instructions
- Haiku calls (not supported)

### Configuration

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 16000,
  "thinking": {
    "type": "enabled",
    "budget_tokens": 10000
  },
  "messages": [...]
}
```

**Cost note:** Thinking tokens count as output tokens. A 10K thinking budget at Sonnet pricing adds up to $0.15 per request. Use judiciously.

---

## Tool Use Configuration

Tool use is the backbone of OpenClaw agent functionality. Claude supports structured tool definitions that let agents call external functions.

### How OpenClaw Passes Tools to Claude

Tools are defined in the API request and Claude decides when/how to call them:

```json
{
  "model": "claude-haiku-4-5-20251001",
  "max_tokens": 4096,
  "tools": [
    {
      "name": "search_crm",
      "description": "Search the CRM for contacts matching a query. Returns matching contact records with name, email, company, and status.",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query (name, company, or email)"
          },
          "status_filter": {
            "type": "string",
            "enum": ["active", "lead", "prospect", "customer", "churned"],
            "description": "Filter by contact status"
          }
        },
        "required": ["query"]
      }
    }
  ],
  "messages": [
    {"role": "user", "content": "Find all active leads at Acme Corp"}
  ]
}
```

### Tool Use Best Practices for OpenClaw

1. **Write clear tool descriptions** -- Claude uses these to decide when to call each tool. Vague descriptions lead to wrong tool selections.
2. **Use specific parameter schemas** -- Enums, required fields, and descriptions help Claude fill parameters correctly.
3. **Limit tool count per request** -- Sending 50 tools increases input tokens significantly. Only include tools relevant to the current skill/task.
4. **Cache tool definitions** -- Use prompt caching (see below) since tool definitions are usually static.

---

## Prompt Caching

Prompt caching is one of the most impactful cost optimizations. It caches the prefix of your request (system prompt, tool definitions, few-shot examples) so you only pay full price once, then get a 90% discount on cached tokens.

### How It Works

1. First request: You pay full input price for all tokens
2. Subsequent requests (within 5 minutes): Cached prefix tokens cost only 10% of normal input price
3. Cache is keyed on the exact prefix -- any change to the cached portion invalidates it

### Implementation

Add `cache_control` markers to indicate what should be cached:

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "system": [
    {
      "type": "text",
      "text": "You are an OpenClaw sales agent...[long system prompt]...",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [
    {
      "name": "search_crm",
      "description": "...",
      "input_schema": {...},
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "messages": [...]
}
```

### Cost Impact

| Scenario                  | Without Caching | With Caching (after 1st req) |
|---------------------------|----------------|------------------------------|
| 3K system prompt tokens   | $0.009 (Sonnet)| $0.0009                      |
| 2K tool definition tokens | $0.006         | $0.0006                      |
| Per-request savings       | --             | ~$0.013 saved                |
| 1,000 requests/month      | $15.00         | $1.65                        |

**Cache write cost:** There is a 25% premium on the first request that writes to cache. This is quickly amortized over subsequent requests.

### What to Cache (Priority Order)

1. System prompt (almost always static)
2. Tool definitions (change rarely)
3. Few-shot examples (if used)
4. Common context/instructions per skill

---

## Batches API

For non-real-time processing, the Batches API offers a 50% discount on all token costs. Results are delivered within 24 hours (usually much faster).

### When to Use

- End-of-day lead enrichment batch
- Weekly CRM data cleanup
- Bulk content generation (e.g., 100 personalized emails)
- Report generation that doesn't need to be instant
- Any task where the user isn't waiting for an immediate response

### How It Works

1. Create a batch of up to 10,000 requests
2. Submit to the Batches API endpoint
3. Poll for completion (or use webhook callback)
4. Download results when ready

### Cost Savings Example

| Task                      | Standard Cost | Batch Cost (50% off) |
|---------------------------|--------------|----------------------|
| 500 lead enrichments/mo   | $19.50       | $9.75                |
| 200 email generations/mo  | $10.20       | $5.10                |
| Monthly batch savings     | --           | ~$14.85              |

---

## Error Handling

### Common Errors and Responses

| Error Code | Meaning              | Action                                           |
|-----------|----------------------|--------------------------------------------------|
| 400       | Bad request          | Check request format, tool schemas               |
| 401       | Invalid API key      | Verify ANTHROPIC_API_KEY is set correctly         |
| 403       | Forbidden            | Check if model is available on your plan          |
| 429       | Rate limited         | Implement backoff; consider model routing         |
| 500       | Server error         | Retry with exponential backoff                    |
| 529       | API overloaded       | Retry after delay; fall back to alternative model |

### Recommended Retry Strategy

```
attempt 1: immediate
attempt 2: wait 1 second
attempt 3: wait 2 seconds
attempt 4: wait 4 seconds
attempt 5: wait 8 seconds
attempt 6: FAIL -- fall back to alternative model or return error
```

### Fallback Order

```
Claude Sonnet 4.5 (primary)
  --> fails --> Claude Haiku 4.5 (cheaper, usually available)
  --> fails --> GPT-4o-mini (different provider, different rate limits)
  --> fails --> Ollama qwen3:14b (local, always available)
  --> fails --> Return error to user
```

---

## Quick Reference: API Request Template

```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 4096,
  "system": [
    {
      "type": "text",
      "text": "You are an OpenClaw agent. [skill-specific instructions]",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "tools": [...],
  "messages": [
    {"role": "user", "content": "User's request here"}
  ]
}
```

---

## Action Items

- [ ] Generate API key at console.anthropic.com
- [ ] Set ANTHROPIC_API_KEY environment variable on Mac Mini
- [ ] Set initial monthly spend limit to $50
- [ ] Configure budget alerts at 50%, 80%, 95%
- [ ] Test each model (Haiku, Sonnet, Opus) with a sample OpenClaw task
- [ ] Implement prompt caching for system prompts and tool definitions
- [ ] Evaluate Batches API for recurring bulk tasks

---

## RESEARCH GAPS

- **Exact rate limits for current tier:** Need to check what tier the current account is at and whether limits are sufficient for planned usage.
- **OpenClaw's API configuration syntax:** How exactly does OpenClaw specify which Claude model to use? Is it in a config file, per-skill, or passed dynamically?
- **Prompt caching with OpenClaw:** Does OpenClaw automatically use prompt caching, or does it need to be configured manually?
- **Batches API integration:** Does OpenClaw have native support for the Batches API, or would this need custom implementation?
- **Token counting:** Does OpenClaw track and report token usage per request? This is essential for cost monitoring.

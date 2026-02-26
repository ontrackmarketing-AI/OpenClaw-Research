# Model Routing Strategy

## Overview

Model routing is the single most impactful cost-optimization strategy for OpenClaw. The core idea: not every task needs a $15/M-token model. By intelligently routing tasks to the cheapest model that can handle them reliably, you reduce API spend by 60-80% with negligible quality loss.

OpenClaw is model-agnostic by design. It can call Claude (Anthropic API), GPT (OpenAI API), and local models via Ollama -- all within the same workflow. This means you can assign different models to different skills, agents, or even individual steps within a multi-step task.

---

## Routing Tiers

### Tier 1 -- Local / Free (Ollama)

**Cost:** $0 marginal (electricity only)
**Latency:** 50-200ms first token, depends on model size
**Best model:** `qwen3:14b` on Mac Mini M4

**Use for:**
- Data formatting and normalization (phone numbers, addresses, names)
- Template filling (email templates, CRM field population)
- Basic classification (lead hot/warm/cold, industry tagging, sentiment)
- Simple extraction (pull name and email from a block of text)
- Embedding generation for RAG (`nomic-embed-text` or `mxbai-embed-large`)
- JSON schema validation and transformation
- Language detection

**OpenClaw examples:**
- Formatting a scraped contact into CRM-ready JSON
- Classifying an inbound email as sales inquiry vs. support request
- Filling a Google Slides template with pre-approved content
- Generating embeddings for memory/knowledge indexing

**Reliability notes:**
- Local models occasionally produce malformed JSON or miss tool call syntax
- Always validate outputs; use structured output schemas when possible
- Keep prompts short and direct -- local models degrade with long context

---

### Tier 2 -- Cheap API

**Cost:** ~$0.80-$1.00 / M input tokens, ~$4.00 / M output tokens
**Latency:** 200-500ms first token
**Best models:** `claude-haiku-4-5` (Anthropic) or `gpt-4o-mini` (OpenAI)

**Use for:**
- Summarization (meeting notes, articles, long emails)
- Standard tool use with 1-3 tool calls per turn
- Content generation from structured data (LinkedIn posts from CRM data)
- Multi-field extraction from unstructured text
- Conversation handling for routine chatbot interactions
- Lead enrichment from provided context
- Translation tasks
- CRM data validation with reasoning

**OpenClaw examples:**
- Summarizing a prospect's LinkedIn profile for pre-call prep
- Generating a first-draft outreach email from a lead profile
- Running a 3-step enrichment chain: search -> extract -> format
- Handling standard customer chat responses

**Reliability notes:**
- Haiku 4.5 has strong tool use capabilities -- reliable for most agent tasks
- Good at following structured output formats
- May struggle with nuanced multi-step reasoning or ambiguous instructions
- Excellent cost/quality ratio for 80% of daily agent operations

---

### Tier 3 -- Premium API

**Cost:** ~$3.00 / M input tokens, ~$15.00 / M output tokens
**Latency:** 500ms-2s first token
**Best models:** `claude-sonnet-4-5` (Anthropic) or `gpt-4o` (OpenAI)

**Use for:**
- Multi-step reasoning with 4+ sequential tool calls
- Complex analysis (competitor research synthesis, market analysis)
- Content that requires nuance (personalized proposals, strategy documents)
- Agentic workflows where the model must plan and adapt
- Code generation for custom integrations or scripts
- Complex data transformation with business logic
- Tasks where Tier 2 models produce unreliable results

**OpenClaw examples:**
- Building a full prospect research report from multiple data sources
- Generating a personalized pitch deck narrative from CRM + market data
- Running a multi-step lead qualification workflow with branching logic
- Debugging or generating n8n workflow JSON
- Analyzing a batch of call transcripts for coaching insights

**Reliability notes:**
- Sonnet 4.5 is the workhorse -- best balance of speed, cost, and capability
- Handles complex tool chains reliably
- Enable extended thinking for particularly complex reasoning tasks
- Default choice when you are unsure which tier to use

---

### Tier 4 -- Best Available

**Cost:** ~$15.00 / M input tokens, ~$75.00 / M output tokens
**Latency:** 1-5s first token (longer with extended thinking)
**Best model:** `claude-opus-4-6` (Anthropic)

**Use for:**
- Client-facing deliverables that must be flawless (proposals, reports)
- Novel or ambiguous problems the system hasn't encountered before
- Complex multi-document analysis and synthesis
- High-stakes decisions (pricing strategy, contract review, compliance checks)
- Tasks where Tier 3 produces inconsistent or subpar results
- Final quality review of important outputs

**OpenClaw examples:**
- Writing a final client proposal that will be sent without human review
- Analyzing a complex deal structure with multiple stakeholders
- Generating a comprehensive market entry strategy
- Reviewing and polishing a batch of generated content for consistency

**Reliability notes:**
- Reserve for 5% or fewer of total tasks
- The cost difference is dramatic: one Opus call can cost as much as 20 Haiku calls
- Consider using Opus as a "reviewer" that checks Sonnet's output rather than doing all the work
- Enable extended thinking for maximum reasoning quality

---

## How OpenClaw Implements Routing

### Per-Skill Configuration

Each OpenClaw skill can specify its preferred model. This is the simplest approach.

```yaml
# Example skill configuration
skill: format_lead_data
  model: ollama/qwen3:14b       # Tier 1: simple formatting

skill: enrich_lead
  model: claude-haiku-4-5       # Tier 2: standard tool use

skill: generate_proposal
  model: claude-sonnet-4-5      # Tier 3: complex generation

skill: review_proposal
  model: claude-opus-4-6        # Tier 4: quality-critical review
```

### Per-Agent Configuration

Different agents can use different default models. A "data processing" agent might default to Haiku, while a "content creation" agent defaults to Sonnet.

### Dynamic Routing (Advanced)

A lightweight router (can itself be a local model or rule-based) examines the incoming task and selects the appropriate tier:

```
INPUT: task description + metadata
  |
  v
ROUTER (rule-based or lightweight LLM):
  - Check task type against routing table
  - Check required capabilities (tool use? long context? creativity?)
  - Check priority/urgency flags
  - Check cost budget remaining
  |
  v
OUTPUT: selected model + configuration
```

**Rule-based routing criteria:**
| Criterion               | Tier 1 (Local)    | Tier 2 (Haiku)   | Tier 3 (Sonnet) | Tier 4 (Opus) |
|------------------------|--------------------|-------------------|------------------|----------------|
| Tool calls needed      | 0-1                | 1-3               | 3-8              | 8+             |
| Input complexity       | Structured         | Semi-structured   | Unstructured     | Ambiguous      |
| Output quality bar     | Internal/draft     | Internal/good     | External/good    | External/best  |
| Reasoning steps        | 1                  | 1-2               | 3-5              | 5+             |
| Error tolerance        | Can retry          | Can retry         | Should succeed   | Must succeed   |

---

## Fallback Chains

When a model fails (timeout, malformed output, rate limit), OpenClaw should escalate to the next tier rather than failing the task entirely.

```
Tier 1 (Ollama qwen3:14b)
  |-- fails (malformed JSON, timeout, etc.)
  v
Tier 2 (Claude Haiku 4.5)
  |-- fails (rate limit, poor quality output)
  v
Tier 3 (Claude Sonnet 4.5)
  |-- fails (extremely rare at this point)
  v
Tier 4 (Claude Opus 4.6) -- last resort
  |-- fails
  v
ERROR: Return failure to user with context
```

**Implementation notes:**
- Log every fallback event -- frequent fallbacks mean the initial tier assignment is wrong
- Set a maximum fallback budget per task to prevent runaway costs
- Fallback should carry the original prompt + the error context from the failed attempt
- Consider a "retry at same tier" step before escalating (transient errors)

---

## Cost Savings Estimate

### Without routing (everything on Sonnet):

| Task type            | Monthly volume | Avg tokens/task | Monthly cost  |
|----------------------|---------------|-----------------|---------------|
| Data formatting      | 2,000         | 1K in / 500 out | $13.50        |
| Lead enrichment      | 500           | 3K in / 2K out  | $19.50        |
| Content generation   | 200           | 2K in / 3K out  | $10.20        |
| Analysis/proposals   | 50            | 5K in / 5K out  | $4.50         |
| Misc agent tasks     | 1,000         | 2K in / 1K out  | $21.00        |
| **Total**            |               |                 | **~$68.70**   |

### With routing:

| Task type            | Model          | Monthly cost  |
|----------------------|----------------|---------------|
| Data formatting      | Ollama (free)  | $0.00         |
| Lead enrichment      | Haiku 4.5      | $5.60         |
| Content generation   | Sonnet 4.5     | $10.20        |
| Analysis/proposals   | Opus 4.6       | $7.50         |
| Misc agent tasks     | Haiku 4.5      | $6.00         |
| **Total**            |                | **~$29.30**   |

**Savings: ~57% in this scenario.** With aggressive local model usage and prompt caching on top, savings reach 70-80%.

---

## Decision Flowchart for Model Selection

```
START: New task arrives
  |
  Is the task a simple format/transform/classify?
  |-- YES --> Tier 1: Ollama qwen3:14b
  |-- NO
  |
  Does the task require tool use?
  |-- NO --> Is it complex reasoning?
  |           |-- NO --> Tier 2: Haiku 4.5
  |           |-- YES --> Tier 3: Sonnet 4.5
  |-- YES
  |
  How many tool calls expected?
  |-- 1-3 simple calls --> Tier 2: Haiku 4.5
  |-- 3-8 calls or chained --> Tier 3: Sonnet 4.5
  |-- 8+ or novel chains --> Tier 4: Opus 4.6
  |
  Is the output client-facing / high-stakes?
  |-- YES --> Bump up one tier (min Tier 3)
  |-- NO --> Keep current tier
  |
  Is cost budget nearly exhausted?
  |-- YES --> Drop one tier, accept quality tradeoff
  |-- NO --> Proceed with selected tier
  |
  END: Route to selected model
```

---

## Action Items

- [ ] Define model assignments for each OpenClaw skill during initial setup
- [ ] Configure fallback chains in OpenClaw agent configuration
- [ ] Set up logging to track which tier handles each task
- [ ] Review fallback logs weekly; adjust tier assignments based on actual failure rates
- [ ] Establish monthly cost review to validate routing effectiveness

---

## RESEARCH GAPS

- **Dynamic routing implementation:** How exactly does OpenClaw configure model selection per skill? Need to review OpenClaw docs for the specific configuration syntax.
- **Fallback behavior:** Does OpenClaw have built-in fallback chains, or does this need custom implementation?
- **Quality measurement:** Need a systematic way to evaluate if cheaper models are producing acceptable quality for each task type.

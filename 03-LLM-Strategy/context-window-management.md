# Context Window Management

## Overview

Every LLM has a maximum context window -- the total number of tokens it can process in a single request (input + output combined). For agentic systems like OpenClaw, context management is critical because agents consume tokens from multiple sources simultaneously: system prompts, tool definitions, conversation history, memory injection, tool results, and the model's own response. Poor context management leads to truncated inputs, lost information, degraded reasoning, and unnecessarily high costs.

This document covers context window sizes, how OpenClaw agents consume context, and strategies for staying within limits while maximizing agent effectiveness.

---

## Context Window Sizes by Model

### Cloud Models

| Model                    | Context Window | Effective Usable* |
|--------------------------|---------------|-------------------|
| Claude Opus 4.6          | 200K tokens   | ~190K tokens      |
| Claude Sonnet 4.5        | 200K tokens   | ~190K tokens      |
| Claude Haiku 4.5         | 200K tokens   | ~190K tokens      |
| GPT-4o                   | 128K tokens   | ~120K tokens      |
| GPT-4o-mini              | 128K tokens   | ~120K tokens      |

*Effective usable = total window minus reserved space for the model's response (max_tokens setting).

### Local Models (Ollama)

| Model              | Default Context | Max Context (configurable) | Notes                           |
|--------------------|----------------|---------------------------|----------------------------------|
| qwen3:14b          | 32K tokens     | 128K tokens               | Quality degrades past 32K        |
| deepseek-r1:14b    | 64K tokens     | 64K tokens                | Chain-of-thought uses many tokens|
| llama3.3:70b       | 128K tokens    | 128K tokens               | Good long-context performance    |
| mistral-nemo:12b   | 128K tokens    | 128K tokens               | Trained for long context         |
| codellama:34b      | 16K tokens     | 16K tokens                | Short context, code-focused      |

**Important:** Just because a model supports 128K tokens doesn't mean it performs well at 128K. Most models degrade in quality (especially retrieval accuracy) when the context is very full. The "needle in a haystack" problem is real. Aim to use less than 50% of the context window for best results.

### Configuring Local Model Context in Ollama

```bash
# Create a Modelfile to set context window
cat > Modelfile << 'EOF'
FROM qwen3:14b
PARAMETER num_ctx 65536
EOF

ollama create qwen3-64k -f Modelfile
```

**RAM impact:** Larger context windows require more memory. Doubling the context window roughly doubles the KV-cache memory usage. On a 32GB Mac Mini, keep local model contexts at 32K or below unless you have tested the memory impact.

---

## Why Context Matters for Agents

An OpenClaw agent request is NOT just "user message -> model response." A typical agent turn includes all of these, competing for the same context window:

```
+--------------------------------------------------+
|                 CONTEXT WINDOW                     |
|                                                    |
|  [System Prompt]         ~1,000-2,000 tokens       |
|  [Tool Definitions]      ~1,000-3,000 tokens       |
|  [Memory/Knowledge]      ~1,000-4,000 tokens       |
|  [Conversation History]  ~2,000-8,000 tokens       |
|  [Current Tool Results]  ~1,000-8,000 tokens       |
|  [User's Current Message] ~100-500 tokens          |
|  [Reserved for Response]  ~2,000-4,000 tokens      |
|                                                    |
|  TOTAL: ~8,000-30,000 tokens per agent turn        |
+--------------------------------------------------+
```

**Key insight:** Even with a 200K context window, agents can hit practical limits quickly because:
1. Multi-turn conversations accumulate history
2. Tool results can be unexpectedly large (full API responses, long web pages)
3. Memory injection (RAG results) adds context each turn
4. Each tool call round-trip adds the tool result to the conversation

A 10-turn agent conversation with 3 tool calls per turn can easily reach 50-80K tokens.

---

## OpenClaw Context Management Strategies

### Strategy 1: Sliding Window

**How it works:** When conversation history approaches a threshold, drop the oldest messages to make room for new ones.

```
Turn 1:  [System] [Turn 1 messages]
Turn 5:  [System] [Turn 1-5 messages]
Turn 10: [System] [Turn 1-10 messages]  <-- approaching limit
Turn 11: [System] [Turn 4-11 messages]  <-- dropped turns 1-3
Turn 15: [System] [Turn 8-15 messages]  <-- dropped turns 4-7
```

**Pros:**
- Simple to implement
- Preserves most recent context (usually most relevant)
- Predictable memory usage

**Cons:**
- Loses early conversation context completely
- Agent may "forget" decisions made in early turns
- No prioritization -- important early messages are dropped along with unimportant ones

**Best for:** Simple, short-lived agent tasks where early context is not critical.

**Configuration guideline:** Set the sliding window to keep the last N messages where N is tuned so total history stays under 30-50% of the context window.

---

### Strategy 2: Summarization

**How it works:** Instead of dropping old messages, compress them into a summary that preserves key information in fewer tokens.

```
Turn 1-5:  [Full messages: 8,000 tokens]
            |
            v (summarize)
Summary:    [500 tokens capturing key decisions, data, and context]

Turn 6+:   [System] [Summary of turns 1-5] [Turn 6+ full messages]
```

**Pros:**
- Preserves important context from entire conversation
- More token-efficient than keeping full history
- Agent retains awareness of earlier decisions

**Cons:**
- Summarization itself costs tokens (an extra API call or local model call)
- Summary may miss details that become important later
- Adds latency (summarization step before each turn)

**Best for:** Long-running agent sessions where continuity matters (e.g., a multi-step research workflow that spans 20+ turns).

**Implementation approach:**
1. After every 5-10 turns, summarize the oldest non-summarized turns
2. Use a cheap model (Haiku or local) for summarization
3. Include in the summary: key decisions made, data gathered, current task state
4. Replace the original turns with the summary

---

### Strategy 3: Memory Offload

**How it works:** Write important information to a persistent store (file, database, or vector store) and retrieve only what is relevant for the current turn.

```
Agent discovers: "Prospect John Smith is CEO of Acme Corp, interested in enterprise plan"
  |
  v
Write to memory store: {entity: "John Smith", role: "CEO", company: "Acme Corp", interest: "enterprise"}
  |
  v
Later turn: Agent needs info about John Smith
  |
  v
Retrieve from memory: inject only John Smith's record into context (~200 tokens vs. replaying entire conversation)
```

**Pros:**
- Minimal context usage -- only relevant data is injected
- Persistent across sessions (agent remembers across conversations)
- Scales to unlimited information (limited only by storage, not context window)

**Cons:**
- Requires memory infrastructure (vector store, retrieval logic)
- Retrieval may miss relevant information if embeddings/search are imperfect
- More complex to implement than sliding window or summarization

**Best for:** OpenClaw's primary memory system. Essential for CRM data, prospect research, and any information that needs to persist beyond a single session.

---

### Strategy 4: Tool Result Truncation

**How it works:** When a tool returns data, truncate or filter it before injecting into the conversation context.

```
Tool returns: Full LinkedIn profile HTML (15,000 tokens)
  |
  v (truncation)
Injected: Name, title, company, recent 3 posts, key skills (800 tokens)
```

**Truncation rules by tool type:**

| Tool Type          | Full Result Size | Truncated Size | Strategy                            |
|--------------------|-----------------|----------------|-------------------------------------|
| Web scrape         | 5-20K tokens    | 500-2K tokens  | Extract relevant sections only      |
| API response       | 1-10K tokens    | 200-1K tokens  | Select relevant fields              |
| CRM query          | 500-5K tokens   | 200-500 tokens | Include only requested fields       |
| File read          | 1-50K tokens    | 500-2K tokens  | Extract relevant sections           |
| Search results     | 2-10K tokens    | 500-1K tokens  | Top 3-5 results, title + snippet    |

**Implementation:**
- Define max token limits per tool type
- Implement extraction/filtering logic in the tool handler (before returning to the model)
- When truncating, prefer structured extraction over blind character-limit truncation
- Include a note like "[truncated, full result available via tool_id:xyz]" so the agent knows data was cut

---

## Optimal Context Allocation

For a typical OpenClaw agent turn using a 200K-token cloud model, aim for this allocation:

```
+----------------------------------------------+
| Component              | Token Budget         |
|------------------------|----------------------|
| System prompt          | 1,000-2,000 tokens   |
| Tool definitions       | 1,000-2,000 tokens   |
| Memory context (RAG)   | 2,000-4,000 tokens   |
| Conversation history   | 4,000-8,000 tokens   |
| Current tool results   | 2,000-8,000 tokens   |
| User message           | 100-500 tokens       |
| RESERVED for response  | 2,000-4,000 tokens   |
|------------------------|----------------------|
| TOTAL per turn         | 12,000-28,000 tokens |
+----------------------------------------------+
```

**Why so conservative with a 200K window?** Two reasons:
1. **Cost:** Every token costs money. Using 28K tokens on Sonnet costs ~$0.084 input. Using 100K would cost ~$0.300. Keeping context lean saves 70% per request.
2. **Quality:** Models perform better with focused context. Injecting 100K tokens of marginally relevant data degrades the model's attention on what matters.

### For Local Models (32K context window)

Context is much more constrained. Aggressive management is mandatory:

```
+----------------------------------------------+
| Component              | Token Budget         |
|------------------------|----------------------|
| System prompt          | 500-800 tokens       |
| Tool definitions       | 500-1,000 tokens     |
| Memory context         | 500-1,000 tokens     |
| Conversation history   | 1,000-2,000 tokens   |
| Tool results           | 500-2,000 tokens     |
| User message           | 100-300 tokens       |
| RESERVED for response  | 1,000-2,000 tokens   |
|------------------------|----------------------|
| TOTAL per turn         | 4,000-9,000 tokens   |
+----------------------------------------------+
```

**Key difference:** Local models get shorter system prompts, fewer tools, less history, and smaller tool results. This means local models should handle simpler, more focused tasks (which aligns with the model routing strategy).

---

## Local Model Context Considerations

### Shorter Windows Require More Aggressive Management

With a 32K window (qwen3:14b default), you have roughly 1/6 the space of Claude. This means:

- **Limit tools per request:** Include only 2-5 tools relevant to the current task, not the full tool catalog.
- **Minimize history:** Keep only the last 2-3 turns for local models.
- **Truncate aggressively:** Tool results should be pre-processed to extract only the answer, not raw data.
- **Shorter system prompts:** Write local model prompts at 50% the length of cloud model prompts. Be direct. Cut examples.

### Context Window vs. Quality Tradeoff

```
Context usage:   0-30%    -> Excellent quality
                 30-60%   -> Good quality
                 60-80%   -> Degraded quality (especially for local models)
                 80-100%  -> Unreliable, high risk of missed information
```

**Rule of thumb:** If a task regularly pushes a local model past 60% context usage, route it to a cloud model instead.

---

## Long-Running Agent Sessions

Some agent workflows run for many turns (e.g., a research workflow that makes 20+ tool calls). These are the highest-risk scenarios for context window overflow.

### Context Rotation Strategy

```
Turns 1-5:   Normal operation, accumulate history
Turn 5:      Summarize turns 1-5 into a state summary (500 tokens)
Turns 6-10:  [State summary] + new turns
Turn 10:     Update state summary to include turns 6-10
Turns 11-15: [Updated state summary] + new turns
...repeat...
```

The "state summary" acts as a checkpoint. It should include:
- What task is being performed
- What data has been gathered so far
- What decisions have been made
- What remains to be done

### Session Splitting

For very long workflows, split into multiple independent sessions:

```
Session 1: Research phase
  - Gather data from multiple sources
  - Output: structured research document (written to file/memory)

Session 2: Analysis phase
  - Input: research document from Session 1
  - Analyze and synthesize
  - Output: analysis results

Session 3: Generation phase
  - Input: analysis results from Session 2
  - Generate final deliverable
```

Each session starts fresh with a clean context window, receiving only the relevant output from the previous session. This is more reliable than trying to maintain a single session across 50+ turns.

---

## Context Window Overflow: What Happens

When the input exceeds the model's context window:

| Provider   | Behavior                                                          |
|------------|-------------------------------------------------------------------|
| Anthropic  | Returns a 400 error: "prompt is too long"                         |
| OpenAI     | Returns a 400 error or silently truncates (model-dependent)       |
| Ollama     | Silently truncates the beginning of the context (dangerous!)      |

**Ollama's silent truncation is particularly dangerous** because the agent loses its system prompt and early instructions without any error. The model continues responding but may behave unpredictably. Always enforce context limits in OpenClaw's application layer, don't rely on the model provider.

### Prevention Checklist

- [ ] Count tokens before sending requests (use a tokenizer or estimate at ~4 chars/token)
- [ ] Set hard context budgets per component (system prompt, history, tools, etc.)
- [ ] Implement pre-request validation that rejects or trims oversized requests
- [ ] Log warnings when context usage exceeds 70% of the window
- [ ] For local models, enforce stricter limits (50% of nominal context window)

---

## Token Counting Quick Reference

Accurate token counting requires a tokenizer, but for estimation:

| Rule of Thumb                  | Tokens         |
|--------------------------------|---------------|
| 1 English word                 | ~1.3 tokens   |
| 1 character (average)          | ~0.25 tokens  |
| 1 line of code                 | ~10-15 tokens |
| 1 paragraph of text            | ~50-100 tokens|
| 1 page of text                 | ~300-500 tokens|
| 1 typical tool definition      | ~200-400 tokens|
| 1 typical system prompt        | ~500-2,000 tokens|
| 1 CRM contact record (full)   | ~200-500 tokens|
| 1 CRM contact record (minimal)| ~50-100 tokens |

For the Anthropic API specifically, use the `anthropic` Python library's token counting:
```python
import anthropic
client = anthropic.Anthropic()
count = client.count_tokens("Your text here")
```

---

## Action Items

- [ ] Define context budgets per component for cloud and local models
- [ ] Implement tool result truncation for all tools that can return large results
- [ ] Set up conversation summarization for sessions exceeding 5 turns
- [ ] Configure local model context windows in Ollama (Modelfile)
- [ ] Add pre-request context size validation to prevent overflow
- [ ] Design memory offload system for persistent information
- [ ] Test long-running agent workflows and verify context rotation works

---

## RESEARCH GAPS

- **OpenClaw's built-in context management:** Does OpenClaw handle context window limits automatically (sliding window, summarization), or does this need custom implementation? Need to check OpenClaw docs.
- **Token counting accuracy:** What tokenizer does OpenClaw use for local models? Anthropic's tokenizer (Claude) differs from LLaMA's tokenizer. Miscounting can cause unexpected truncation.
- **Ollama context behavior:** Verify exactly what happens when Ollama's context window is exceeded -- does it truncate from the beginning, middle, or return an error? This differs by version.
- **Memory offload implementation:** How does OpenClaw's memory system work? Does it use a vector store, flat files, or both? This determines how memory context injection is implemented.
- **Optimal context allocation:** The budgets above are starting estimates. After real usage, tune based on actual token counts and quality observations.

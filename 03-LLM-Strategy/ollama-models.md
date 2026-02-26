# Ollama Models for OpenClaw

## Overview

Running local models via Ollama on the Mac Mini M4 gives OpenClaw a zero-marginal-cost inference tier. This is critical for keeping API costs down -- every task handled locally is a task you do not pay Anthropic or OpenAI for.

The M4 chip (in the Mac Mini with 32-64GB unified memory) is currently one of the best consumer-grade platforms for local LLM inference. Its unified memory architecture means the GPU and CPU share the same memory pool, so large models can load entirely into memory without the PCIe bottleneck that limits desktop GPUs.

---

## Recommended Models (Ranked by Priority for OpenClaw)

### 1. qwen3:14b -- Primary Agent Model

**Why it's #1:** Best tool use / function calling capability at this parameter count. Qwen3 was specifically optimized for agentic tasks, including structured JSON output and function calling -- exactly what OpenClaw needs.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Parameters         | 14B                                      |
| VRAM needed        | ~10-12 GB (Q4_K_M)                       |
| Context window     | 32K tokens (default), 128K (extended)    |
| Strengths          | Tool use, structured output, instruction following |
| Weaknesses         | Can struggle with very creative/nuanced tasks |
| OpenClaw use cases | Data formatting, classification, tool calling, JSON generation |

```bash
ollama pull qwen3:14b
```

**Key feature:** Qwen3 supports a "thinking" mode where it reasons before answering, similar to Claude's extended thinking. This can be toggled with `/think` and `/no_think` in prompts. For agent tasks, `/no_think` is usually faster and sufficient.

---

### 2. deepseek-r1:14b -- Reasoning Specialist

**Why:** When a local task requires genuine multi-step reasoning (not just pattern matching), DeepSeek-R1 outperforms other models at this size. Its chain-of-thought approach produces more reliable answers for analytical tasks.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Parameters         | 14B (distilled from 671B MoE)            |
| VRAM needed        | ~10-12 GB (Q4_K_M)                       |
| Context window     | 64K tokens                               |
| Strengths          | Mathematical reasoning, logical analysis, step-by-step problem solving |
| Weaknesses         | Slower due to chain-of-thought; weaker at tool use than Qwen3 |
| OpenClaw use cases | Lead scoring logic, data analysis, complex classification rules |

```bash
ollama pull deepseek-r1:14b
```

**Note:** R1 always "thinks out loud" which increases output tokens. Budget extra time/tokens for its responses.

---

### 3. llama3.3:70b -- Highest Quality Local (64GB RAM Required)

**Why:** When you need near-API quality but want to stay local. Llama 3.3 70B is competitive with GPT-4o-mini on many benchmarks and handles complex tasks well. But it requires 64GB RAM to run smoothly.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Parameters         | 70B                                      |
| VRAM needed        | ~40-45 GB (Q4_K_M)                       |
| Context window     | 128K tokens                              |
| Strengths          | High quality across all tasks, strong instruction following |
| Weaknesses         | Slow on M4, requires 64GB Mac Mini, large disk footprint (~40GB) |
| OpenClaw use cases | Fallback for when 14B models fail, draft content generation, complex extraction |

```bash
ollama pull llama3.3:70b
```

**Important:** Only viable if you have the 64GB Mac Mini. With 32GB, this model will swap to disk and become unusable. If you have 32GB, skip this and rely on API models for Tier 2+ tasks.

---

### 4. mistral-nemo:12b -- Fast Simple Tasks

**Why:** Faster than Qwen3 for very simple tasks where you want minimal latency. Good as a "speed tier" for trivial formatting and classification.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Parameters         | 12B                                      |
| VRAM needed        | ~8-10 GB (Q4_K_M)                        |
| Context window     | 128K tokens                              |
| Strengths          | Fast, good multilingual support, decent instruction following |
| Weaknesses         | Weaker tool use than Qwen3, less precise on structured output |
| OpenClaw use cases | Simple text formatting, language detection, basic summarization |

```bash
ollama pull mistral-nemo:12b
```

---

### 5. codellama:34b -- Code Generation Specialist

**Why:** If OpenClaw needs to generate or modify code (n8n workflow JSON, scripts, API integrations), a code-specialized model outperforms general models.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Parameters         | 34B                                      |
| VRAM needed        | ~22-25 GB (Q4_K_M)                       |
| Context window     | 16K tokens                               |
| Strengths          | Code generation, code analysis, technical documentation |
| Weaknesses         | Limited context window, weaker at non-code tasks |
| OpenClaw use cases | Generating API integration code, debugging workflows, script writing |

```bash
ollama pull codellama:34b
```

**Note:** For most code tasks in OpenClaw, Qwen3:14b or Sonnet via API will be sufficient. Only pull CodeLlama if you have a specific, recurring code generation need and want to avoid API costs for it.

---

### 6. nomic-embed-text -- Local Embeddings (Fast)

**Why:** Essential for RAG (Retrieval Augmented Generation). Converts text into vector embeddings for semantic search across your knowledge base, CRM notes, and memory.

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Dimensions         | 384                                      |
| VRAM needed        | ~300 MB                                  |
| Speed              | Very fast, thousands of embeddings/second |
| Strengths          | Tiny, fast, good for real-time embedding |
| Weaknesses         | Lower dimensionality means less semantic precision |
| OpenClaw use cases | Memory indexing, document search, lead similarity matching |

```bash
ollama pull nomic-embed-text
```

---

### 7. mxbai-embed-large -- Local Embeddings (Quality)

**Why:** Higher quality embeddings than nomic. Use this when semantic precision matters (e.g., finding the most relevant CRM notes for a specific prospect).

| Attribute          | Value                                    |
|--------------------|------------------------------------------|
| Dimensions         | 1024                                     |
| VRAM needed        | ~700 MB                                  |
| Speed              | Fast, but slower than nomic              |
| Strengths          | Better semantic understanding, higher recall on search tasks |
| Weaknesses         | Larger vectors = more storage, slightly slower |
| OpenClaw use cases | High-quality document retrieval, semantic CRM search, knowledge base queries |

```bash
ollama pull mxbai-embed-large
```

**Recommendation:** Start with `nomic-embed-text` for speed. Switch to `mxbai-embed-large` if search quality is insufficient.

---

## Performance on Mac Mini M4

### Estimated Tokens/Second by Model Size

These are estimates based on available M3/M2 benchmarks, extrapolated for M4's improved memory bandwidth and neural engine. The M4 has ~120 GB/s memory bandwidth (base model) or ~273 GB/s (Pro/Max), which is the primary bottleneck for LLM inference.

| Model Size | Quantization | Est. tok/s (M4 base) | Est. tok/s (M4 Pro) | RAM Usage  |
|------------|-------------|----------------------|---------------------|------------|
| 7B         | Q4_K_M      | 40-60                | 55-80               | ~5-6 GB    |
| 12-14B     | Q4_K_M      | 20-35                | 35-50               | ~10-12 GB  |
| 34B        | Q4_K_M      | 10-15                | 18-25               | ~22-25 GB  |
| 70B        | Q4_K_M      | 5-8                  | 12-18               | ~40-45 GB  |

**For context:** 20 tok/s is comfortable for agent use (agents don't need real-time streaming). 10 tok/s is usable but noticeably slow. Below 5 tok/s is painful for interactive use but fine for background batch processing.

### Time-to-Complete Estimates (14B model, typical agent task)

| Task                     | Input tokens | Output tokens | Est. time |
|--------------------------|-------------|---------------|-----------|
| Format contact data      | 200         | 150           | ~5-7s     |
| Classify lead            | 300         | 50            | ~2-3s     |
| Fill email template      | 500         | 300           | ~10-15s   |
| Extract structured data  | 1,000       | 200           | ~7-10s    |
| Simple summarization     | 2,000       | 500           | ~15-25s   |

---

## Tool Use / Function Calling Comparison

Tool use is critical for OpenClaw agents. Not all local models handle it well.

| Model              | Tool Use Quality | Structured JSON | Multi-tool Chains | Notes                              |
|--------------------|-----------------|-----------------|--------------------|------------------------------------|
| qwen3:14b          | Strong          | Strong          | Moderate           | Best tool use at this size         |
| deepseek-r1:14b    | Weak            | Moderate        | Weak               | Reasoning-focused, not tool-focused|
| llama3.3:70b       | Strong          | Strong          | Strong             | Near-API quality tool use          |
| mistral-nemo:12b   | Moderate        | Moderate        | Weak               | Simpler tool calls only            |
| codellama:34b      | Weak            | Moderate        | Weak               | Code-focused, not agent-focused    |

**Recommendation:** Use `qwen3:14b` as the default local model for all tool-use tasks. Only fall back to others for specific non-tool tasks (reasoning with deepseek-r1, code with codellama).

---

## Quantization Guide

Quantization reduces model precision to save memory and increase speed, with a quality tradeoff.

### Common Quantization Levels

| Quantization | Bits/Weight | Quality Loss | Speed Gain | Memory Savings | Recommendation           |
|-------------|-------------|-------------|------------|----------------|--------------------------|
| Q4_K_M      | ~4.5        | Small       | Fastest    | ~60% vs FP16   | **Default choice**       |
| Q5_K_M      | ~5.5        | Minimal     | Fast       | ~50% vs FP16   | When quality matters more|
| Q8_0        | 8           | Negligible  | Moderate   | ~30% vs FP16   | If RAM allows            |
| FP16        | 16          | None        | Baseline   | None           | Almost never worth it    |

**For OpenClaw on M4:**
- **32GB Mac Mini:** Use Q4_K_M for everything. You need the memory savings.
- **64GB Mac Mini:** Use Q4_K_M for 70B models, Q5_K_M for 14B models. You can afford slightly better quality on smaller models.

### How to select quantization in Ollama:

Ollama's default `pull` command grabs a sensible default (usually Q4_K_M). To specify:

```bash
# Default (Q4_K_M usually)
ollama pull qwen3:14b

# Specific quantization (check Ollama library for available tags)
ollama pull qwen3:14b-q5_K_M
ollama pull qwen3:14b-q8_0
```

---

## Model Management

### Essential Commands

```bash
# Download a model
ollama pull qwen3:14b

# List installed models
ollama list

# Check running models (and memory usage)
ollama ps

# Remove a model (free disk space)
ollama rm codellama:34b

# Show model details
ollama show qwen3:14b

# Run interactive test
ollama run qwen3:14b "Format this as JSON: John Smith, john@example.com, Acme Corp"
```

### Disk Space Planning

| Model              | Disk Space (Q4_K_M) |
|--------------------|---------------------|
| qwen3:14b          | ~9 GB               |
| deepseek-r1:14b    | ~9 GB               |
| llama3.3:70b       | ~40 GB              |
| mistral-nemo:12b   | ~7 GB               |
| codellama:34b      | ~20 GB              |
| nomic-embed-text   | ~275 MB             |
| mxbai-embed-large  | ~670 MB             |
| **Total (all)**    | **~86 GB**          |

**Minimum recommended setup (32GB Mac Mini):**
- qwen3:14b (~9 GB)
- nomic-embed-text (~275 MB)
- Total: ~10 GB disk

**Full setup (64GB Mac Mini):**
- qwen3:14b + deepseek-r1:14b + llama3.3:70b + both embedding models
- Total: ~59 GB disk

### Keep Models Loaded

By default, Ollama unloads models after 5 minutes of inactivity. For frequently-used models, keep them loaded:

```bash
# Keep model loaded indefinitely (until Ollama restarts)
curl http://localhost:11434/api/generate -d '{"model": "qwen3:14b", "keep_alive": -1}'
```

This uses RAM but eliminates cold-start latency (which can be 5-15 seconds for a 14B model).

---

## Recommended Initial Setup

**Phase 1 (Day 1):**
```bash
ollama pull qwen3:14b          # Primary agent model
ollama pull nomic-embed-text   # Embeddings for RAG
```

**Phase 2 (After testing Phase 1):**
```bash
ollama pull deepseek-r1:14b    # For reasoning tasks
ollama pull mxbai-embed-large  # Better embeddings if needed
```

**Phase 3 (Only if 64GB RAM):**
```bash
ollama pull llama3.3:70b       # High-quality local fallback
```

---

## RESEARCH GAPS

- **Real M4 benchmarks:** All performance numbers above are estimates. Need to run actual benchmarks once the Mac Mini is set up. Key metrics: tokens/sec, time-to-first-token, memory usage under load.
- **Concurrent model loading:** How does performance degrade when two models are loaded simultaneously (e.g., qwen3 for agent tasks + nomic for embeddings)? Need to test.
- **Ollama tool use format:** Exactly how does Ollama expose tool use / function calling? Does OpenClaw's Ollama integration handle this natively, or does it need custom formatting?
- **Model updates:** Ollama models update frequently. Need a process for testing new model versions before deploying them in production agent workflows.
- **M4 Pro vs M4 base:** If the Mac Mini has M4 Pro, memory bandwidth roughly doubles, which would significantly improve all the performance estimates above. Confirm which M4 variant is being purchased.

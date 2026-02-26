# Ollama Local Models for OpenClaw

## Overview

Ollama lets you run open-weight LLMs entirely on your Mac Mini M4, eliminating API costs for
many agent tasks and providing zero-latency inference for local operations. OpenClaw integrates
with Ollama through its OpenAI-compatible API endpoint at `http://localhost:11434`.

This guide covers installation, recommended models for agent use, performance expectations on
Apple Silicon, and how to connect Ollama to OpenClaw.

---

## 1. Installing Ollama

### Option A: Homebrew (Recommended)

```bash
brew install ollama
```

### Option B: Direct Download

Download from [ollama.ai](https://ollama.ai) and install the macOS app. This installs both
the CLI and a menu bar app that manages the service.

### Option C: Manual Install

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Verify Installation

```bash
ollama --version
# ollama version 0.x.x
```

---

## 2. Starting the Ollama Service

Ollama runs as a background service that listens for API requests on port 11434.

### If installed via Homebrew:

```bash
# Start as a background service (persists across restarts)
brew services start ollama

# Verify it is running
brew services list | grep ollama

# Check the API is responsive
curl http://localhost:11434/api/tags
```

### If installed via the macOS app:

The Ollama menu bar app starts the service automatically. It will also launch at login by
default.

### Manual start (foreground, useful for debugging):

```bash
ollama serve
```

### Auto-start on boot (if using Homebrew services):

```bash
# This is already handled by brew services start, but verify:
brew services list
# ollama should show "started"
```

---

## 3. Recommended Models for OpenClaw

### Tier 1: Best Balance of Speed and Quality (14B Class)

These models are the sweet spot for most OpenClaw agent tasks on a Mac Mini M4 with 32-64 GB
RAM.

#### qwen3:14b -- Primary Recommendation for Tool Use

```bash
ollama pull qwen3:14b
```

- **Disk size:** ~8.5 GB
- **RAM usage:** ~9 GB loaded
- **Strengths:** Excellent at structured output (JSON), function/tool calling, following
  complex multi-step instructions. Qwen3 was specifically trained with agentic tool-use
  patterns, making it ideal as an OpenClaw agent brain.
- **Weaknesses:** Slightly weaker at creative writing compared to Llama. Not the strongest at
  pure code generation.
- **Best for:** General agent tasks, API orchestration, data extraction, structured workflows.

#### deepseek-r1:14b -- Best Reasoning

```bash
ollama pull deepseek-r1:14b
```

- **Disk size:** ~9 GB
- **RAM usage:** ~9 GB loaded
- **Strengths:** Exceptional chain-of-thought reasoning, strong at math and logic, excels at
  multi-step problem decomposition. DeepSeek-R1 uses a "thinking" approach that produces
  higher-quality outputs for complex tasks.
- **Weaknesses:** Slower than qwen3 due to the reasoning chain (generates more tokens
  internally). The thinking tokens add latency.
- **Best for:** Complex decision-making tasks, data analysis, planning, tasks requiring
  careful reasoning before acting.

### Tier 2: Maximum Quality (70B Class -- Requires 64GB+ RAM)

#### llama3.3:70b -- Highest Quality Local Option

```bash
ollama pull llama3.3:70b
```

- **Disk size:** ~40 GB
- **RAM usage:** ~42 GB loaded
- **Strengths:** Near-API-quality responses, excellent at nuanced conversation, strong code
  generation, broad knowledge. Performance rivals GPT-4-class models on many benchmarks.
- **Weaknesses:** Requires 64 GB RAM minimum (the model alone uses ~42 GB). Slower inference
  than 14B models. Cannot run alongside other large models.
- **Best for:** High-stakes agent tasks where quality matters more than speed. Customer-facing
  conversations, complex code generation, research tasks.

### Tier 3: Lightweight / Specialized

#### codellama:13b -- Code Generation

```bash
ollama pull codellama:13b
```

- **Disk size:** ~7 GB
- **RAM usage:** ~8 GB loaded
- **Strengths:** Specifically fine-tuned for code generation, completion, and explanation.
  Understands code structure deeply.
- **Weaknesses:** Weaker at general conversation and non-code tasks.
- **Best for:** Skills that generate or modify code, automated development workflows,
  code review agent tasks.

#### nomic-embed-text -- Local Embeddings for RAG

```bash
ollama pull nomic-embed-text
```

- **Disk size:** ~275 MB
- **RAM usage:** ~300 MB loaded
- **Strengths:** Fast local embeddings without API calls. 768-dimension vectors, 8192 token
  context. Great for building local RAG (Retrieval-Augmented Generation) pipelines.
- **Weaknesses:** Not a generation model -- only produces embeddings.
- **Best for:** OpenClaw memory search, document retrieval, semantic similarity for skill
  matching.

#### qwen3:8b -- Fast and Lightweight

```bash
ollama pull qwen3:8b
```

- **Disk size:** ~4.9 GB
- **RAM usage:** ~5.5 GB loaded
- **Strengths:** Very fast inference, low memory footprint. Good enough for simple tasks.
- **Weaknesses:** Noticeably less capable than 14B models. Struggles with complex
  multi-step instructions.
- **Best for:** High-throughput scenarios where you need fast responses on simple tasks,
  or as a "triage" model that routes to larger models when needed.

---

## 4. Pulling Models

```bash
# Pull all recommended models for a 64GB setup
ollama pull qwen3:14b
ollama pull deepseek-r1:14b
ollama pull llama3.3:70b
ollama pull nomic-embed-text

# For a 32GB setup (skip 70B)
ollama pull qwen3:14b
ollama pull deepseek-r1:14b
ollama pull codellama:13b
ollama pull nomic-embed-text

# List downloaded models
ollama list
```

---

## 5. Performance Benchmarks on Mac Mini M4

Token generation speed depends on the chip variant and memory bandwidth. Here are approximate
benchmarks for the Mac Mini M4 line:

### Token Generation Speed (tokens/second)

| Model             | M4 Base (120 GB/s) | M4 Pro (273 GB/s) | M4 Max (546 GB/s) |
|-------------------|--------------------:|-------------------:|-------------------:|
| qwen3:8b          | ~35 tok/s           | ~55 tok/s          | ~65 tok/s          |
| qwen3:14b         | ~20 tok/s           | ~38 tok/s          | ~50 tok/s          |
| deepseek-r1:14b   | ~18 tok/s           | ~35 tok/s          | ~45 tok/s          |
| codellama:13b     | ~22 tok/s           | ~40 tok/s          | ~52 tok/s          |
| llama3.3:70b      | N/A (needs 64GB)    | ~10 tok/s          | ~22 tok/s          |
| nomic-embed-text  | ~200 emb/s          | ~400 emb/s         | ~500 emb/s         |

> **Note:** These are approximate values for Q4_K_M quantization. Actual performance varies
> based on prompt length, concurrent load, and available memory. Benchmarks measured with a
> single concurrent request, no other load.

### What These Speeds Mean in Practice

- **35+ tok/s:** Feels instantaneous. Agent responses appear in under a second for short
  replies.
- **20-35 tok/s:** Very usable. A 200-token response takes 5-10 seconds.
- **10-20 tok/s:** Noticeable wait. A 500-token response takes 25-50 seconds. Still practical
  for background agent tasks.
- **Below 10 tok/s:** Slow for interactive use, but fine for batch/background processing.

---

## 6. Memory Usage and Model Loading Behavior

Ollama loads models into memory on first request and keeps them loaded (warm) for 5 minutes
by default. Understanding this is critical for a multi-model setup.

### Memory Per Model Size (Q4_K_M Quantization)

| Parameter Count | Approximate RAM When Loaded |
|-----------------|----------------------------:|
| 1-3B            | 1.5 - 2 GB                  |
| 7-8B            | 4 - 5.5 GB                  |
| 13-14B          | 8 - 9.5 GB                  |
| 30-34B          | 18 - 20 GB                  |
| 70B             | 40 - 42 GB                  |

### Configuring Keep-Alive Time

By default, Ollama unloads a model after 5 minutes of inactivity. For an always-on agent
server, you may want to keep your primary model warm:

```bash
# Keep models loaded for 1 hour (useful for active agent sessions)
# Set via environment variable before starting Ollama
export OLLAMA_KEEP_ALIVE=1h

# Or keep the primary model loaded indefinitely
export OLLAMA_KEEP_ALIVE=-1

# Add to your shell profile for persistence
echo 'export OLLAMA_KEEP_ALIVE=1h' >> ~/.zshrc
```

### Running Multiple Models

You CAN have multiple models loaded if you have enough RAM:

- **64 GB RAM:** qwen3:14b (9 GB) + deepseek-r1:14b (9 GB) + nomic-embed-text (0.3 GB) +
  macOS (4 GB) + OpenClaw (0.5 GB) = ~23 GB used, 41 GB free. Comfortable.
- **32 GB RAM:** qwen3:14b (9 GB) + nomic-embed-text (0.3 GB) + macOS (4 GB) + OpenClaw
  (0.5 GB) + Docker (3 GB) = ~17 GB used, 15 GB free. Workable but tight.

---

## 7. Configuring OpenClaw to Use Ollama

OpenClaw communicates with Ollama through its OpenAI-compatible API.

### Environment Variable

Add to your OpenClaw `.env` file:

```bash
# Point OpenClaw to local Ollama instance
OLLAMA_BASE_URL=http://localhost:11434

# If running OpenClaw in Docker and Ollama natively on the host:
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Specifying the Model in OpenClaw

In your OpenClaw configuration or when starting an agent session, specify the Ollama model:

```bash
# In .env or agent configuration
OPENCLAW_DEFAULT_MODEL=ollama/qwen3:14b

# Or configure per-skill overrides:
# Fast model for simple tasks
OPENCLAW_TRIAGE_MODEL=ollama/qwen3:8b
# Quality model for complex tasks
OPENCLAW_REASONING_MODEL=ollama/deepseek-r1:14b
# Code model for development tasks
OPENCLAW_CODE_MODEL=ollama/codellama:13b
```

### Verifying the Connection

```bash
# Test Ollama API directly
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:14b",
  "prompt": "Say hello in JSON format",
  "stream": false
}'

# Test via OpenAI-compatible endpoint (what OpenClaw uses)
curl http://localhost:11434/v1/chat/completions -d '{
  "model": "qwen3:14b",
  "messages": [{"role": "user", "content": "Hello, respond in one sentence."}]
}'
```

---

## 8. Custom Model Configuration (Modelfile)

You can create custom model configurations tuned for OpenClaw agent behavior:

```bash
# Create a Modelfile for an OpenClaw-optimized agent model
cat > ~/openclaw-agent.Modelfile << 'EOF'
FROM qwen3:14b

# System prompt optimized for tool use and structured output
SYSTEM """You are an AI agent operating within the OpenClaw platform. You have access to
tools and skills. Always respond with structured output when tools are available. Be concise,
accurate, and action-oriented. When uncertain, ask for clarification rather than guessing."""

# Parameters tuned for agent reliability (lower temperature = more deterministic)
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
PARAMETER repeat_penalty 1.1
EOF

# Build the custom model
ollama create openclaw-agent -f ~/openclaw-agent.Modelfile

# Test it
ollama run openclaw-agent "What tools do you have available?"
```

---

## 9. Monitoring and Maintenance

### Check Running Models

```bash
# List loaded (warm) models
ollama ps

# List all downloaded models
ollama list

# Show model details
ollama show qwen3:14b
```

### Update Models

```bash
# Pull latest version of a model
ollama pull qwen3:14b

# Update all models (no built-in command, use a loop)
for model in $(ollama list | tail -n +2 | awk '{print $1}'); do
  echo "Updating $model..."
  ollama pull "$model"
done
```

### Clean Up Unused Models

```bash
# Remove a model you no longer need
ollama rm codellama:13b

# Check disk usage
du -sh ~/.ollama/models/
```

### Monitor Resource Usage During Inference

```bash
# Watch CPU and memory in real time
top -l 1 -s 0 | grep -E "CPU|Mem|ollama"

# More detailed: use Activity Monitor or htop
brew install htop
htop -p $(pgrep ollama)
```

---

## Quick Reference Card

| Task                          | Command                                   |
|-------------------------------|-------------------------------------------|
| Start Ollama service          | `brew services start ollama`              |
| Stop Ollama service           | `brew services stop ollama`               |
| Pull a model                  | `ollama pull qwen3:14b`                   |
| List downloaded models        | `ollama list`                             |
| List loaded (warm) models     | `ollama ps`                               |
| Run interactive chat          | `ollama run qwen3:14b`                    |
| Remove a model                | `ollama rm modelname`                     |
| Test API                      | `curl http://localhost:11434/api/tags`    |
| Check Ollama version          | `ollama --version`                        |
| View model details            | `ollama show qwen3:14b`                   |

---

## Next Steps

- [Docker Installation](docker-installation.md) - Deploy OpenClaw via Docker (connects to Ollama)
- [Native Installation](native-installation.md) - Deploy OpenClaw via npm
- [Environment Variables](environment-variables.md) - Full configuration reference
- [Verification Tests](verification-tests.md) - Test that Ollama + OpenClaw work together

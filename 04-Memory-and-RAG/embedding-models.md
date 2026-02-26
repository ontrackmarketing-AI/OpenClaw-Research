# Embedding Models for OpenClaw RAG

## Overview

Embedding models convert text into dense numerical vectors that capture semantic meaning. Similar texts produce similar vectors, enabling semantic search. Choosing the right embedding model is a permanent decision for a given knowledge base -- you cannot mix embeddings from different models in the same vector index.

---

## Local Embedding Models (via Ollama)

These models run entirely on your machine. No API calls, no costs, no data leaving your network.

### nomic-embed-text -- RECOMMENDED for Local Use

| Property | Value |
|----------|-------|
| Dimensions | 768 |
| Max tokens | 8,192 |
| Model size | ~274 MB |
| Speed | ~500 embeddings/sec on CPU, ~2,000/sec on GPU |
| Quality | Strong performance on MTEB benchmark, competitive with commercial models |
| License | Apache 2.0 (fully open, commercial use OK) |

**Why this is the recommendation:**

- Best balance of quality, speed, and resource usage for local deployment.
- 768 dimensions is the sweet spot: enough to capture meaning, small enough for fast search and reasonable storage.
- 8,192 token context means you can embed larger chunks without truncation.
- Apache 2.0 license allows commercial use without restrictions.

**Setup:**

```bash
# Pull the model
ollama pull nomic-embed-text

# Test it
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "What is the cost per lead for HVAC companies?"
}'
```

**Python usage:**

```python
import requests
import numpy as np

def embed_text(text: str, model: str = "nomic-embed-text") -> np.ndarray:
    """Generate embedding using Ollama."""
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": model, "prompt": text}
    )
    return np.array(response.json()["embedding"], dtype=np.float32)

# Single text
embedding = embed_text("HVAC lead generation strategies")
print(f"Dimensions: {len(embedding)}")  # 768

# Batch processing
texts = ["text one", "text two", "text three"]
embeddings = [embed_text(t) for t in texts]
```

---

### mxbai-embed-large

| Property | Value |
|----------|-------|
| Dimensions | 1,024 |
| Max tokens | 512 |
| Model size | ~670 MB |
| Speed | ~200 embeddings/sec on CPU, ~800/sec on GPU |
| Quality | Higher quality than nomic on many benchmarks |
| License | Apache 2.0 |

**When to use:**

- When you need the highest quality local embeddings and can accept slower speed.
- Careful: only 512 token context means you must use smaller chunks.

**Tradeoffs vs nomic-embed-text:**

- Higher quality embeddings, especially for nuanced semantic relationships.
- 1,024 dimensions means ~33% more storage and slightly slower vector search.
- 512 token context limit is a real constraint -- chunks over ~400 words will be truncated.
- Slower: roughly 2.5x slower than nomic-embed-text.

```bash
ollama pull mxbai-embed-large
```

---

### all-minilm:l6-v2

| Property | Value |
|----------|-------|
| Dimensions | 384 |
| Max tokens | 256 |
| Model size | ~46 MB |
| Speed | ~2,000 embeddings/sec on CPU, ~8,000/sec on GPU |
| Quality | Decent for simple similarity tasks, weaker on nuanced queries |
| License | Apache 2.0 |

**When to use:**

- When speed is the primary concern and quality can be sacrificed.
- Prototyping and testing where you want fast iteration.
- Resource-constrained environments (the model is tiny at 46 MB).

**Tradeoffs:**

- 384 dimensions limits expressive power. Fine for straightforward "is this similar to that?" tasks.
- 256 token context means very small chunks only.
- Noticeably lower quality on complex semantic queries compared to nomic or mxbai.

```bash
ollama pull all-minilm:l6-v2
```

---

## API Embedding Models

These models run on cloud infrastructure. Higher quality, but require API keys, cost money per request, and send data over the network.

### Voyage-3.5-lite -- RECOMMENDED for API/Production

| Property | Value |
|----------|-------|
| Dimensions | 1,024 |
| Max tokens | 32,000 |
| Speed | ~1,000 embeddings/sec (API throughput) |
| Quality | Best-in-class for retrieval tasks on MTEB |
| Cost | ~$0.02 per 1M tokens |
| Provider | Voyage AI (voyageai.com) |

**Why this is the recommendation for API use:**

- Specifically optimized for retrieval/RAG tasks (not just general similarity).
- 32,000 token context means you can embed very large documents without chunking.
- Exceptionally low cost at $0.02/1M tokens.
- Consistently ranks at or near the top of MTEB retrieval benchmarks.

**Setup:**

```bash
pip install voyageai
```

```python
import voyageai

client = voyageai.Client(api_key="your-api-key")

# Single embedding
result = client.embed(["What is the cost per lead for HVAC?"], model="voyage-3.5-lite")
embedding = result.embeddings[0]  # 1024-dim list

# Batch embedding (up to 128 texts per call)
texts = ["text one", "text two", "text three"]
result = client.embed(texts, model="voyage-3.5-lite")
embeddings = result.embeddings  # list of 1024-dim lists
```

---

### OpenAI text-embedding-3-small

| Property | Value |
|----------|-------|
| Dimensions | 1,536 (configurable: 256-1,536) |
| Max tokens | 8,191 |
| Speed | ~3,000 embeddings/sec (API throughput) |
| Quality | Good general-purpose quality |
| Cost | ~$0.02 per 1M tokens |
| Provider | OpenAI |

**When to use:**

- When you are already using OpenAI's API and want to minimize vendor count.
- The configurable dimensions feature is useful: you can reduce to 512 or 256 dims to save storage while accepting some quality loss.

```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="HVAC lead generation strategies",
    dimensions=768  # optional: reduce from default 1536
)
embedding = response.data[0].embedding
```

---

### OpenAI text-embedding-3-large

| Property | Value |
|----------|-------|
| Dimensions | 3,072 (configurable: 256-3,072) |
| Max tokens | 8,191 |
| Speed | ~1,500 embeddings/sec (API throughput) |
| Quality | Highest quality in OpenAI's lineup |
| Cost | ~$0.13 per 1M tokens |
| Provider | OpenAI |

**When to use:**

- When you need the absolute highest quality from OpenAI and cost is not a concern.
- For high-stakes retrieval where missing a relevant document is costly.

**Tradeoff:** 6.5x more expensive than text-embedding-3-small and Voyage-3.5-lite. The quality improvement is marginal for most RAG use cases.

---

## Comparison Table

| Model | Dimensions | Max Tokens | Speed (CPU) | Quality | Cost | Best For |
|-------|-----------|------------|-------------|---------|------|----------|
| **nomic-embed-text** | 768 | 8,192 | ~500/sec | Good | Free | **Local default** |
| mxbai-embed-large | 1,024 | 512 | ~200/sec | Very Good | Free | High-quality local |
| all-minilm:l6-v2 | 384 | 256 | ~2,000/sec | Fair | Free | Prototyping |
| **Voyage-3.5-lite** | 1,024 | 32,000 | ~1,000/sec | Excellent | $0.02/1M tok | **Production API** |
| OAI embed-3-small | 1,536 | 8,191 | ~3,000/sec | Good | $0.02/1M tok | OpenAI ecosystem |
| OAI embed-3-large | 3,072 | 8,191 | ~1,500/sec | Very Good | $0.13/1M tok | Maximum quality |

---

## Decision Framework

### Local vs API

```
Do you need embeddings to work offline?
  YES -> Local (nomic-embed-text)
  NO  -> Continue

Is the data sensitive / can't leave your network?
  YES -> Local (nomic-embed-text)
  NO  -> Continue

Do you need best-in-class retrieval quality?
  YES -> API (Voyage-3.5-lite)
  NO  -> Local (nomic-embed-text) -- it's free and good enough

Are you processing >100K documents?
  YES -> API (faster batch throughput, no local compute strain)
  NO  -> Either works
```

### OpenClaw Recommended Setup

**For development and single-user use:** nomic-embed-text via Ollama.

- Zero cost, zero network dependency, good quality.
- 768 dimensions with sqlite-vec gives excellent search performance.

**For production multi-tenant (OnTrack Marketing):** Voyage-3.5-lite.

- Best retrieval quality, negligible cost.
- Use with Qdrant (existing setup) or Supabase pgvector.

---

## Embedding Consistency Rules

**CRITICAL: You cannot mix embeddings from different models in the same vector index.**

If you embed 10,000 chunks with nomic-embed-text and then switch to Voyage-3.5-lite, those 10,000 existing embeddings are invalid. The new query embeddings from Voyage will be in a completely different vector space and similarity scores will be meaningless.

**Rules:**

1. **Pick a model and commit to it** for each knowledge base / vector index.
2. **Record the model name** in the database or config:
   ```sql
   CREATE TABLE embedding_config (
       index_name TEXT PRIMARY KEY,
       model_name TEXT NOT NULL,
       dimensions INTEGER NOT NULL,
       created_at TEXT DEFAULT (datetime('now'))
   );
   ```
3. **If you must switch models**, you must re-embed every single document. Plan for this by keeping original text in the database alongside embeddings.
4. **Different indexes can use different models.** Your local SQLite can use nomic-embed-text while your Qdrant production instance uses Voyage-3.5-lite. Just never mix within a single index.

---

## Batch Embedding

Processing large document collections efficiently:

```python
import time
from typing import Generator

def batch_embed(
    texts: list[str],
    batch_size: int = 50,
    model: str = "nomic-embed-text",
    show_progress: bool = True,
) -> list[np.ndarray]:
    """
    Embed a list of texts in batches.

    For Ollama (local), batch_size controls how many sequential API calls
    we make before yielding. For API models, batch_size should match the
    provider's batch limit.
    """
    embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = [embed_text(t, model=model) for t in batch]
        embeddings.extend(batch_embeddings)

        if show_progress:
            done = min(i + batch_size, total)
            print(f"Embedded {done}/{total} ({done/total*100:.1f}%)")

        # Rate limiting for API models
        if model.startswith("voyage") or model.startswith("text-embedding"):
            time.sleep(0.1)  # avoid rate limits

    return embeddings
```

---

## Caching Embeddings

Do not re-embed documents that have not changed. Use content hashing:

```python
import hashlib

def content_hash(text: str) -> str:
    """SHA-256 hash of content for change detection."""
    return hashlib.sha256(text.encode()).hexdigest()

def needs_reembedding(text: str, stored_hash: str) -> bool:
    """Check if content has changed since last embedding."""
    return content_hash(text) != stored_hash
```

The SQLite `documents` table includes a `content_hash` column. During ingestion:

1. Compute hash of document content.
2. Check if a document with the same path and same hash already exists.
3. If yes, skip embedding. If no, re-embed and update.

This saves significant time and cost during incremental updates, especially with API models.

---

## Storage Requirements

Embedding storage per chunk:

| Model | Dimensions | Bytes per Embedding | 10K Chunks | 100K Chunks |
|-------|-----------|-------------------|------------|-------------|
| all-minilm | 384 | 1,536 bytes | ~15 MB | ~150 MB |
| nomic-embed-text | 768 | 3,072 bytes | ~30 MB | ~300 MB |
| mxbai-embed-large | 1,024 | 4,096 bytes | ~40 MB | ~400 MB |
| Voyage-3.5-lite | 1,024 | 4,096 bytes | ~40 MB | ~400 MB |
| OAI embed-3-small | 1,536 | 6,144 bytes | ~60 MB | ~600 MB |
| OAI embed-3-large | 3,072 | 12,288 bytes | ~120 MB | ~1.2 GB |

For a marketing agency with 10,000-50,000 chunks, nomic-embed-text at 768 dimensions keeps the vector index between 30-150 MB -- easily manageable on any modern machine.

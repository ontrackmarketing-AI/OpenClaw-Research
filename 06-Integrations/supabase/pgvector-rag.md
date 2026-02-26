# pgvector RAG Setup in Supabase

> Setting up vector search for Retrieval-Augmented Generation in OpenClaw using Supabase's pgvector extension.

---

## Why pgvector in Supabase?

OpenClaw needs to retrieve relevant documents, templates, case studies, and historical data to generate contextual outputs. Instead of sending everything to the LLM (expensive, hits context limits), RAG retrieves only the most relevant chunks.

**pgvector advantages:**
- Runs inside your existing Supabase PostgreSQL (no separate vector DB to manage)
- SQL-based: familiar querying, can combine vector search with standard filters
- Free on Supabase free tier (up to 500MB including vectors)
- Supports multiple distance metrics and index types

---

## Extension Setup

### Enable pgvector

```sql
-- Run in Supabase SQL editor or via migration
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
-- Should return one row with vector extension details
```

### Verify Version

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
-- Should be 0.5.0 or higher for HNSW support
```

---

## Embedding Storage

### Vector Dimensions by Model

| Embedding Model | Dimensions | Speed | Quality | Cost |
|---|---|---|---|---|
| `nomic-embed-text` (Ollama) | 768 | Fast (local) | Good | Free (local compute) |
| `text-embedding-3-small` (OpenAI) | 1536 | Fast (API) | Very good | $0.02/1M tokens |
| `text-embedding-3-large` (OpenAI) | 3072 | Fast (API) | Best | $0.13/1M tokens |
| `mxbai-embed-large` (Ollama) | 1024 | Fast (local) | Good | Free (local compute) |

**Recommendation for OpenClaw:** Start with `nomic-embed-text` (768 dimensions) via Ollama on your Mac Mini. It is free, fast, and runs locally. Switch to OpenAI embeddings only if quality is insufficient.

### Documents Table with Embeddings

The `documents` table (defined in `schema-design.md`) includes the embedding column:

```sql
-- The column is already defined in the schema:
-- embedding vector(768)    -- For nomic-embed-text

-- If you switch to OpenAI later, add a second column:
ALTER TABLE documents ADD COLUMN embedding_openai vector(1536);
```

---

## Generating Embeddings

### Using Ollama (Local, Free)

```python
import httpx

async def generate_embedding(text: str, model: str = "nomic-embed-text") -> list[float]:
    """Generate embedding using local Ollama instance."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30.0,
        )
        return response.json()["embedding"]
```

### Using OpenAI (Cloud, Paid)

```python
from openai import AsyncOpenAI

openai_client = AsyncOpenAI()

async def generate_embedding_openai(text: str) -> list[float]:
    """Generate embedding using OpenAI API."""
    response = await openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding
```

### Document Ingestion Pipeline

```python
async def ingest_document(supabase_client, content: str, metadata: dict):
    """Chunk, embed, and store a document."""

    # 1. Chunk the content
    chunks = chunk_text(content, chunk_size=500, overlap=100)

    # 2. Generate embeddings for each chunk
    for i, chunk in enumerate(chunks):
        embedding = await generate_embedding(chunk)

        # 3. Store in Supabase
        await supabase_client.table("documents").insert({
            "title": metadata.get("title", "Untitled"),
            "content": chunk,
            "content_type": metadata.get("type", "knowledge_base"),
            "industry": metadata.get("industry"),
            "tags": metadata.get("tags", []),
            "metadata": metadata,
            "embedding": embedding,
            "chunk_index": i,
            "source_document_id": metadata.get("source_id"),
        }).execute()

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
```

---

## Similarity Search

### Distance Metrics

| Operator | Metric | Use Case |
|---|---|---|
| `<=>` | Cosine distance | Best for normalized embeddings (most common) |
| `<->` | L2 (Euclidean) distance | Good for non-normalized embeddings |
| `<#>` | Inner product (negative) | Good when magnitude matters |

**Use cosine distance (`<=>`) for most cases.** It is the standard for text embeddings.

### RPC Function for Similarity Search

```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(768),
    match_count int DEFAULT 5,
    match_threshold float DEFAULT 0.7,
    filter_content_type text DEFAULT NULL,
    filter_industry text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    content_type text,
    industry text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.title,
        d.content,
        d.content_type,
        d.industry,
        d.metadata,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE
        d.status = 'active'
        AND (filter_content_type IS NULL OR d.content_type = filter_content_type)
        AND (filter_industry IS NULL OR d.industry = filter_industry)
        AND 1 - (d.embedding <=> query_embedding) > match_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### Calling from OpenClaw

```python
async def search_documents(supabase_client, query: str,
                            content_type: str = None,
                            industry: str = None,
                            count: int = 5) -> list[dict]:
    """Search documents using semantic similarity."""

    # 1. Generate embedding for the query
    query_embedding = await generate_embedding(query)

    # 2. Call the RPC function
    result = await supabase_client.rpc("match_documents", {
        "query_embedding": query_embedding,
        "match_count": count,
        "match_threshold": 0.7,
        "filter_content_type": content_type,
        "filter_industry": industry,
    }).execute()

    return result.data
```

### Example Usage in an OpenClaw Skill

```python
async def generate_proposal(lead: dict) -> str:
    """Generate a proposal using RAG to find relevant templates and case studies."""

    # Search for relevant case studies in the same industry
    case_studies = await search_documents(
        supabase,
        query=f"case study for {lead['industry']} marketing success",
        content_type="case_study",
        industry=lead["industry"],
        count=3,
    )

    # Search for proposal templates
    templates = await search_documents(
        supabase,
        query=f"proposal template for {lead['industry']} with {', '.join(lead['pain_signals'])}",
        content_type="template",
        count=2,
    )

    # Combine context for the LLM
    context = "\n\n---\n\n".join(
        [f"Case Study: {cs['title']}\n{cs['content']}" for cs in case_studies]
        + [f"Template: {t['title']}\n{t['content']}" for t in templates]
    )

    # Generate proposal with context
    proposal = await llm.generate(
        prompt=f"""Generate a proposal for {lead['company_name']} ({lead['industry']}).
        Pain points: {', '.join(lead['pain_signals'])}
        Lead score: {lead['lead_score']}

        Use these reference materials:
        {context}""",
    )

    return proposal
```

---

## Index Types

### IVFFlat (Recommended to Start)

**Inverted File Flat** - partitions vectors into lists, searches nearest lists.

```sql
CREATE INDEX idx_documents_embedding ON documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

**Tuning `lists` parameter:**
| Row Count | Recommended Lists |
|---|---|
| < 1,000 | Do not use index (sequential scan is fast enough) |
| 1,000 - 10,000 | 50-100 |
| 10,000 - 100,000 | 100-500 |
| 100,000 - 1,000,000 | 500-1,000 |

**Pros:** Faster to build, smaller index, good enough recall (95%+)
**Cons:** Must tune `lists` and `probes` parameters

**Query tuning:**
```sql
-- Set number of probes (more = better recall, slower)
SET ivfflat.probes = 10;  -- Default is 1, increase for better recall
```

### HNSW (For Production Quality)

**Hierarchical Navigable Small Worlds** - graph-based index with better recall.

```sql
CREATE INDEX idx_documents_embedding_hnsw ON documents
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Tuning parameters:**
| Parameter | Default | Description |
|---|---|---|
| `m` | 16 | Max connections per node. Higher = better recall, more memory |
| `ef_construction` | 64 | Build-time search width. Higher = better index, slower build |

**Query tuning:**
```sql
SET hnsw.ef_search = 40;  -- Default is 40. Higher = better recall, slower
```

**Pros:** Better recall (99%+), no tuning of `probes` needed
**Cons:** Slower to build, uses more memory

**Recommendation:** Start with IVFFlat. Switch to HNSW if recall quality is insufficient.

---

## Performance Tuning

### Connection Pooling

Supabase uses PgBouncer for connection pooling. For vector searches from OpenClaw:

```python
# Use the pooled connection string for high-frequency queries
SUPABASE_DB_URL = "postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
```

### Query Performance

```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT id, content, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM documents
WHERE status = 'active'
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

**Expected performance:**
| Row Count | IVFFlat (10 probes) | HNSW (ef=40) | No Index |
|---|---|---|---|
| 1,000 | < 5ms | < 5ms | < 10ms |
| 10,000 | < 10ms | < 10ms | < 50ms |
| 100,000 | < 50ms | < 20ms | < 500ms |
| 1,000,000 | < 100ms | < 50ms | Several seconds |

---

## Multi-Tenant: Sector-Based Filtering

Combine vector search with standard SQL filters for sector/industry-specific results:

```sql
-- Search for dental-specific case studies only
SELECT id, title, content,
    1 - (embedding <=> query_embedding) AS similarity
FROM documents
WHERE industry = 'dental'
    AND content_type = 'case_study'
    AND status = 'active'
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

**The `WHERE` clause filters BEFORE vector search**, which significantly reduces the search space and improves performance.

For large multi-tenant deployments, consider **partial indexes**:
```sql
-- Index only dental documents
CREATE INDEX idx_docs_dental_embedding ON documents
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50)
    WHERE industry = 'dental';
```

---

## Comparison: Supabase pgvector vs Local SQLite Vector Search

| Feature | Supabase pgvector | Local SQLite (sqlite-vss) |
|---|---|---|
| **Setup** | Extension enable, one command | Compile extension, more complex |
| **Performance** | Excellent with proper indexes | Good for small datasets |
| **Scalability** | Millions of vectors | Thousands of vectors |
| **Concurrent access** | Built-in | Limited |
| **SQL features** | Full PostgreSQL power | Basic SQL |
| **Cost** | Free tier or $25/mo | Free |
| **Maintenance** | Managed by Supabase | Self-managed |
| **Backup** | Automatic | Manual |
| **Network** | Requires API call | Local file, zero latency |

**When to use Supabase pgvector:**
- Production use with multiple concurrent users
- Large document collections (10K+ documents)
- Need for complex SQL queries combined with vector search
- Want managed backups and infrastructure

**When to use local SQLite:**
- Development and testing
- Single-user local operation
- Very small document collections
- Offline/air-gapped requirements

**Recommendation for OpenClaw:** Use Supabase pgvector for production RAG. Use local SQLite for fast development iteration and offline fallback.

---

## RESEARCH GAPS

- [ ] Benchmark nomic-embed-text vs OpenAI text-embedding-3-small for your specific use cases
- [ ] Determine optimal chunk size for different document types (case studies vs templates vs emails)
- [ ] Test IVFFlat vs HNSW performance with realistic data volumes
- [ ] Build the document ingestion pipeline and test with 100 documents
- [ ] Determine if Supabase free tier storage is sufficient for your expected vector count
- [ ] Evaluate whether hybrid search (vector + full-text) improves results

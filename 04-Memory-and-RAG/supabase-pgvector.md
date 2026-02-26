# Supabase pgvector for Production RAG

## Current Status

**Your Supabase project:** `jitawzicdwgbhatvjblh`
**Status:** Currently disabled/paused.
**Dashboard URL:** `https://supabase.com/dashboard/project/jitawzicdwgbhatvjblh`
**API URL (when active):** `https://jitawzicdwgbhatvjblh.supabase.co`

This project was set up previously and has pgvector capabilities. It can serve as the production vector store for OpenClaw's multi-sector RAG, complementing the local SQLite-based search used during development.

---

## When to Use Supabase pgvector vs Local SQLite

| Factor | Supabase pgvector | Local SQLite |
|--------|-------------------|-------------|
| **Access** | Any device, any network | Local machine only |
| **Latency** | 50-200ms (network round trip) | 5-50ms (disk only) |
| **Dataset size** | Millions of vectors easily | Practical limit ~500K vectors |
| **Multi-user** | Full concurrent read/write | Single-writer via WAL |
| **Cost** | Free tier or $25/mo Pro | Free |
| **Setup** | Requires account, API keys | Zero setup beyond install |
| **Offline** | No | Yes |
| **Backup** | Automatic daily (Supabase managed) | Manual (copy the .db file) |
| **Production readiness** | Yes, built for it | Development/single-agent use |

**Decision rule:**

- **Development, single agent, local use:** SQLite (simpler, faster, free).
- **Production, multi-device, client-facing, or shared agents:** Supabase pgvector.
- **Both:** Use SQLite locally for fast access, sync to Supabase for production. The ingestion pipeline can write to both.

---

## Reactivation Steps

### Step 1: Reactivate the Project

1. Go to `https://supabase.com/dashboard/project/jitawzicdwgbhatvjblh`.
2. If the project is paused, click "Restore project" (free tier projects pause after 7 days of inactivity).
3. Wait 2-5 minutes for the database to come back online.
4. Verify access by navigating to the SQL Editor in the dashboard.

**Note:** Free tier projects auto-pause after 7 days of no API requests. To prevent this, either:
- Set up a cron job that pings the API daily (a simple `SELECT 1` query via the REST API).
- Upgrade to Pro ($25/mo) for always-on.

### Step 2: Enable pgvector Extension

```sql
-- Run in Supabase SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;
```

This may already be enabled from your previous setup. The command is idempotent.

### Step 3: Verify pgvector is Working

```sql
-- Test vector operations
SELECT '[1,2,3]'::vector(3) <=> '[4,5,6]'::vector(3) AS cosine_distance;
-- Should return a numeric value (approximately 0.0254)
```

---

## Schema Design

### Core Documents Table

```sql
-- Main embeddings table for RAG
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(768),            -- match your embedding model dimensions
    sector TEXT NOT NULL DEFAULT 'general',
    doc_type TEXT DEFAULT 'knowledge', -- 'knowledge', 'case_study', 'template', 'compliance'
    source_path TEXT,                  -- original file path for sync tracking
    content_hash TEXT,                 -- SHA-256 for change detection
    chunk_index INTEGER DEFAULT 0,     -- position within source document
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (IVFFlat)
-- lists = sqrt(num_rows) is a good starting point; adjust as data grows
CREATE INDEX IF NOT EXISTS idx_documents_embedding
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Index for sector filtering (critical for multi-sector queries)
CREATE INDEX IF NOT EXISTS idx_documents_sector ON documents (sector);

-- Index for content hash lookups (for incremental updates)
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents (content_hash);

-- Index for JSONB metadata queries
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING gin (metadata);

-- Full-text search index (Postgres tsvector, equivalent to FTS5)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS fts tsvector
    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
CREATE INDEX IF NOT EXISTS idx_documents_fts ON documents USING gin (fts);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Why IVFFlat vs HNSW

Supabase pgvector supports two index types:

| Index Type | Build Time | Query Speed | Memory | Accuracy | Best For |
|-----------|-----------|-------------|--------|----------|----------|
| **IVFFlat** | Fast | Good | Low | Good (with enough probes) | <500K vectors, simpler setup |
| **HNSW** | Slow | Fastest | High | Excellent | >500K vectors, latency-critical |

For a marketing agency knowledge base (10K-100K vectors), IVFFlat is sufficient. Switch to HNSW if you exceed 500K vectors or need sub-10ms query times.

**To use HNSW instead:**

```sql
CREATE INDEX IF NOT EXISTS idx_documents_embedding_hnsw
    ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## Similarity Search Queries

### Basic Vector Similarity Search

```sql
-- Find the 10 most similar documents to a query embedding
-- The <=> operator computes cosine distance (0 = identical, 2 = opposite)
SELECT
    id,
    content,
    metadata,
    sector,
    1 - (embedding <=> $1::vector) AS similarity,  -- convert distance to similarity
    created_at
FROM documents
WHERE sector = $2                      -- filter by sector
    AND 1 - (embedding <=> $1::vector) > 0.5  -- minimum similarity threshold
ORDER BY embedding <=> $1::vector      -- sort by cosine distance (ascending = most similar)
LIMIT 10;
```

### Hybrid Search (Vector + Full-Text)

```sql
-- Combine vector similarity and full-text search
WITH vector_results AS (
    SELECT
        id,
        content,
        metadata,
        sector,
        1 - (embedding <=> $1::vector) AS similarity,
        ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS v_rank
    FROM documents
    WHERE sector = $3
    ORDER BY embedding <=> $1::vector
    LIMIT 20
),
fts_results AS (
    SELECT
        id,
        content,
        metadata,
        sector,
        ts_rank(fts, websearch_to_tsquery('english', $2)) AS text_rank,
        ROW_NUMBER() OVER (ORDER BY ts_rank(fts, websearch_to_tsquery('english', $2)) DESC) AS f_rank
    FROM documents
    WHERE sector = $3
        AND fts @@ websearch_to_tsquery('english', $2)
    LIMIT 20
),
combined AS (
    SELECT
        COALESCE(v.id, f.id) AS id,
        COALESCE(v.content, f.content) AS content,
        COALESCE(v.metadata, f.metadata) AS metadata,
        COALESCE(v.sector, f.sector) AS sector,
        -- RRF fusion score
        COALESCE(0.6 / (60 + v.v_rank), 0) +
        COALESCE(0.4 / (60 + f.f_rank), 0) AS rrf_score
    FROM vector_results v
    FULL OUTER JOIN fts_results f ON v.id = f.id
)
SELECT * FROM combined
ORDER BY rrf_score DESC
LIMIT 10;
```

---

## RPC Functions for OpenClaw Integration

Create server-side functions that OpenClaw can call via the Supabase REST API or client library.

### Search Function

```sql
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(768),
    query_text TEXT DEFAULT '',
    target_sector TEXT DEFAULT 'general',
    match_count INTEGER DEFAULT 10,
    similarity_threshold FLOAT DEFAULT 0.5,
    vector_weight FLOAT DEFAULT 0.6,
    fts_weight FLOAT DEFAULT 0.4
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    sector TEXT,
    similarity FLOAT,
    rrf_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        SELECT
            d.id,
            d.content,
            d.metadata,
            d.sector,
            1 - (d.embedding <=> query_embedding) AS sim,
            ROW_NUMBER() OVER (ORDER BY d.embedding <=> query_embedding) AS v_rank
        FROM documents d
        WHERE d.sector = target_sector
            AND 1 - (d.embedding <=> query_embedding) > similarity_threshold
        ORDER BY d.embedding <=> query_embedding
        LIMIT match_count * 2
    ),
    fts_results AS (
        SELECT
            d.id,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank(d.fts, websearch_to_tsquery('english', query_text)) DESC
            ) AS f_rank
        FROM documents d
        WHERE d.sector = target_sector
            AND query_text != ''
            AND d.fts @@ websearch_to_tsquery('english', query_text)
        LIMIT match_count * 2
    )
    SELECT
        vr.id,
        vr.content,
        vr.metadata,
        vr.sector,
        vr.sim AS similarity,
        (
            COALESCE(vector_weight / (60 + vr.v_rank), 0) +
            COALESCE(fts_weight / (60 + fr.f_rank), 0)
        )::FLOAT AS rrf_score
    FROM vector_results vr
    LEFT JOIN fts_results fr ON vr.id = fr.id
    ORDER BY rrf_score DESC
    LIMIT match_count;
END;
$$;
```

### Calling from OpenClaw (Python)

```python
from supabase import create_client
import numpy as np

SUPABASE_URL = "https://jitawzicdwgbhatvjblh.supabase.co"
SUPABASE_KEY = "your-anon-or-service-key"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def search_supabase(
    query_text: str,
    query_embedding: list[float],
    sector: str = "general",
    limit: int = 10,
) -> list[dict]:
    """Search Supabase pgvector for relevant documents."""
    result = supabase.rpc("search_documents", {
        "query_embedding": query_embedding,
        "query_text": query_text,
        "target_sector": sector,
        "match_count": limit,
        "similarity_threshold": 0.5,
    }).execute()

    return result.data

# Example usage
embedding = embed_text("What's the cost per lead for HVAC?")  # from your embedding function
results = search_supabase(
    query_text="cost per lead HVAC",
    query_embedding=embedding.tolist(),
    sector="smb-local-services",
)
for r in results:
    print(f"[{r['similarity']:.3f}] {r['content'][:100]}...")
```

### Calling from OpenClaw (JavaScript/n8n)

```javascript
// For use in n8n HTTP Request node or custom function
const response = await fetch(
  'https://jitawzicdwgbhatvjblh.supabase.co/rest/v1/rpc/search_documents',
  {
    method: 'POST',
    headers: {
      'apikey': 'your-anon-key',
      'Authorization': 'Bearer your-anon-key',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query_embedding: queryEmbeddingArray,  // 768-dim float array
      query_text: 'cost per lead HVAC',
      target_sector: 'smb-local-services',
      match_count: 10,
    }),
  }
);
const results = await response.json();
```

---

## Row Level Security for Multi-Tenant Data

If you eventually serve multiple agency clients from the same Supabase instance, RLS ensures data isolation.

```sql
-- Enable RLS on the documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see documents in their authorized sectors
CREATE POLICY "Users can view documents in their sectors"
    ON documents FOR SELECT
    USING (
        sector = ANY(
            (SELECT sectors FROM user_permissions WHERE user_id = auth.uid())
        )
    );

-- Policy: only service role can insert/update/delete
CREATE POLICY "Service role can manage all documents"
    ON documents FOR ALL
    USING (auth.role() = 'service_role');

-- User permissions table
CREATE TABLE user_permissions (
    user_id UUID REFERENCES auth.users(id),
    sectors TEXT[] NOT NULL DEFAULT ARRAY['general'],
    role TEXT DEFAULT 'viewer',  -- 'viewer', 'editor', 'admin'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

For OpenClaw's current single-user setup, RLS is not necessary. Add it when you start serving multiple clients or team members through the same database.

---

## Ingestion: Writing Documents to Supabase

```python
def upsert_document(
    content: str,
    embedding: list[float],
    sector: str,
    metadata: dict = None,
    source_path: str = None,
    chunk_index: int = 0,
) -> dict:
    """Insert or update a document chunk in Supabase."""
    import hashlib

    content_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check if this exact content already exists
    existing = supabase.table("documents").select("id").eq(
        "content_hash", content_hash
    ).eq("sector", sector).execute()

    record = {
        "content": content,
        "embedding": embedding,
        "sector": sector,
        "metadata": metadata or {},
        "source_path": source_path,
        "content_hash": content_hash,
        "chunk_index": chunk_index,
        "token_count": len(content.split()) * 1.3,  # rough estimate
    }

    if existing.data:
        # Update existing
        result = supabase.table("documents").update(record).eq(
            "id", existing.data[0]["id"]
        ).execute()
    else:
        # Insert new
        result = supabase.table("documents").insert(record).execute()

    return result.data[0]
```

---

## Cost Analysis

### Free Tier (Current)

| Resource | Free Tier Limit | Estimated Usage |
|----------|----------------|-----------------|
| Database size | 500 MB | ~100-200 MB for 50K vectors @ 768 dim |
| API requests | 500K/month | ~10K-50K search queries/month |
| Edge functions | 500K invocations | Used for custom search logic if needed |
| Bandwidth | 5 GB/month | ~1-2 GB for typical RAG query volume |
| Auto-pause | After 7 days inactive | Requires keep-alive ping |

**Verdict:** Free tier is sufficient for development and light production use with a single agency.

### Pro Plan ($25/month)

| Resource | Pro Limit | Why Upgrade |
|----------|-----------|-------------|
| Database size | 8 GB | Room for millions of vectors |
| API requests | Unlimited | No throttling concerns |
| No auto-pause | Always on | Reliable for production |
| Daily backups | 7-day retention | Data safety |
| Bandwidth | 250 GB/month | Handle more clients |

**When to upgrade:** When you have paying clients relying on the RAG system, or when you exceed free tier limits, or when you cannot tolerate the auto-pause behavior.

---

## Sync Strategy: Local SQLite to Supabase

For a dual-storage setup where you develop locally with SQLite and deploy to Supabase:

```python
def sync_to_supabase(local_db_path: str, sector: str):
    """
    Sync local SQLite knowledge base to Supabase.
    Only uploads new or changed documents.
    """
    import sqlite3

    local_db = sqlite3.connect(local_db_path)

    # Get all local chunks with their hashes
    local_chunks = local_db.execute("""
        SELECT c.id, c.content, c.embedding, d.content_hash, d.path, c.chunk_index
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
    """).fetchall()

    # Get all Supabase hashes for this sector
    remote_hashes = set()
    remote = supabase.table("documents").select("content_hash").eq(
        "sector", sector
    ).execute()
    for r in remote.data:
        remote_hashes.add(r["content_hash"])

    # Upload only new/changed chunks
    new_count = 0
    for chunk in local_chunks:
        chunk_id, content, embedding_blob, content_hash, path, chunk_index = chunk
        if content_hash not in remote_hashes:
            embedding_list = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
            upsert_document(
                content=content,
                embedding=embedding_list,
                sector=sector,
                source_path=path,
                chunk_index=chunk_index,
            )
            new_count += 1

    print(f"Synced {new_count} new chunks to Supabase for sector '{sector}'")
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "Could not find extension vector" | pgvector not enabled | Run `CREATE EXTENSION IF NOT EXISTS vector;` |
| Project paused/unreachable | Free tier auto-pause | Restore from dashboard, set up keep-alive ping |
| Slow vector queries (>500ms) | Missing or stale IVFFlat index | Run `REINDEX INDEX idx_documents_embedding;` |
| "wrong number of dimensions" error | Embedding dimensions mismatch | Ensure query embedding matches column definition (768) |
| RPC function not found | Function not created | Run the CREATE FUNCTION SQL above |
| Cosine distance returning unexpected values | Embeddings not normalized | Normalize embeddings before insertion, or use L2 distance instead |

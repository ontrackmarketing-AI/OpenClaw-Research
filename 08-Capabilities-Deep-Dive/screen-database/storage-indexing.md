# Screen Database -- Storage & Indexing Schema

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Data Pipeline](data-pipeline.md), [Supabase Schema](../../06-Integrations/supabase/schema-design.md)

---

## 1. Supabase Table Definition

```sql
-- Requires: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE screen_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Capture metadata
    captured_at TIMESTAMPTZ NOT NULL,
    source_device TEXT NOT NULL DEFAULT 'windows_desktop',
    monitor_index INTEGER DEFAULT 0,

    -- Context
    window_title TEXT,
    app_name TEXT,

    -- OCR content
    ocr_text TEXT NOT NULL,
    content_hash TEXT,          -- MD5 of OCR text for dedup

    -- Vector embedding (768-dim for nomic-embed-text via Ollama)
    embedding vector(768),

    -- Sync metadata
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_screen_captures_time ON screen_captures(captured_at DESC);
CREATE INDEX idx_screen_captures_app ON screen_captures(app_name);
CREATE INDEX idx_screen_captures_device ON screen_captures(source_device);
CREATE INDEX idx_screen_captures_hash ON screen_captures(content_hash);

-- Vector similarity search index
CREATE INDEX idx_screen_captures_embedding
    ON screen_captures USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- Full-text search
CREATE INDEX idx_screen_captures_text
    ON screen_captures USING GIN (to_tsvector('english', ocr_text));
```

---

## 2. Chunking Strategy

Screen captures are already natural chunks -- each capture is a single screenshot's worth of OCR text. No additional chunking is needed for most captures.

**Exception:** If a capture has very long OCR text (>2000 tokens, e.g., a document-heavy screen), split into overlapping chunks:

```python
def chunk_if_needed(ocr_text: str, max_tokens: int = 1500, overlap: int = 200) -> list:
    """Split long OCR text into overlapping chunks."""
    words = ocr_text.split()
    if len(words) <= max_tokens:
        return [ocr_text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks
```

**Embedding per chunk:** Each chunk gets its own embedding vector. The `screen_captures` table stores one row per chunk, with multiple rows sharing the same `captured_at` timestamp if chunked.

---

## 3. Hybrid Search (Vector + FTS)

### 3.1 Supabase RPC Function

```sql
CREATE OR REPLACE FUNCTION search_screen_captures(
    query_text TEXT,
    query_embedding vector(768),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    time_start TIMESTAMPTZ DEFAULT NULL,
    time_end TIMESTAMPTZ DEFAULT NULL,
    filter_app TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    captured_at TIMESTAMPTZ,
    window_title TEXT,
    app_name TEXT,
    ocr_text TEXT,
    vector_similarity FLOAT,
    text_rank FLOAT,
    combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.id,
        sc.captured_at,
        sc.window_title,
        sc.app_name,
        sc.ocr_text,
        1 - (sc.embedding <=> query_embedding) AS vector_similarity,
        ts_rank(to_tsvector('english', sc.ocr_text),
                plainto_tsquery('english', query_text)) AS text_rank,
        (0.6 * (1 - (sc.embedding <=> query_embedding)) +
         0.4 * ts_rank(to_tsvector('english', sc.ocr_text),
                       plainto_tsquery('english', query_text))) AS combined_score
    FROM screen_captures sc
    WHERE
        (1 - (sc.embedding <=> query_embedding)) > match_threshold
        AND (time_start IS NULL OR sc.captured_at >= time_start)
        AND (time_end IS NULL OR sc.captured_at <= time_end)
        AND (filter_app IS NULL OR sc.app_name ILIKE '%' || filter_app || '%')
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$;
```

### 3.2 Querying from OpenClaw

```python
async def search_screen_history(query: str, **filters) -> list:
    """Search screen capture database with hybrid vector + text search."""
    # Generate embedding for query
    query_embedding = ollama.embed(
        model="nomic-embed-text", input=query
    )["embeddings"][0]

    # Call Supabase RPC
    result = await supabase.rpc(
        "search_screen_captures",
        params={
            "query_text": query,
            "query_embedding": query_embedding,
            "match_threshold": 0.65,
            "match_count": 10,
            **filters,
        }
    )
    return result.data
```

---

## 4. Retention Policy

| Data Tier | Retention | What |
|-----------|-----------|------|
| Raw captures (images on Windows) | 30 days | JPEG files, deleted after 30 days |
| OCR text + metadata in Supabase | 90 days | Full text, searchable |
| Daily summaries | Indefinite | AI-generated summary of each day's activity |
| Embeddings | Same as OCR text | Deleted when OCR text is deleted |

### 4.1 Summary Generation

At end of day, generate a summary of screen activity:

```python
async def generate_daily_screen_summary(date: str) -> str:
    """Summarize a day's screen captures into a concise daily log."""
    captures = await supabase.table("screen_captures").select(
        "captured_at, app_name, window_title, ocr_text"
    ).gte("captured_at", f"{date}T00:00:00").lt(
        "captured_at", f"{date}T23:59:59"
    ).order("captured_at").execute()

    # Group by app
    by_app = {}
    for c in captures.data:
        app = c["app_name"] or "Unknown"
        by_app.setdefault(app, []).append(c)

    prompt = f"""Summarize this screen activity for {date}.
    Group by application. For each app, note what the user was working on.
    Keep it concise (under 500 words).

    Activity by app:
    {format_activity(by_app)}
    """

    summary = await llm.generate(prompt, model="haiku")
    return summary
```

Store summaries in the `memory/logs/` directory for long-term retention after raw data is purged.

---

## 5. Data Volume Projections

| Timeframe | OCR Text | Embeddings | Total Supabase |
|-----------|----------|------------|----------------|
| 1 day | ~5-10 MB | ~2 MB | ~7-12 MB |
| 1 week | ~35-70 MB | ~14 MB | ~50-85 MB |
| 1 month | ~150-300 MB | ~60 MB | ~210-360 MB |
| 3 months (with 90-day retention) | ~450-900 MB | ~180 MB | ~630-1080 MB |

**Supabase plan impact:** Free tier (500 MB) insufficient for 3 months. Pro tier ($25/mo, 8 GB) covers 12+ months easily. Already included in the infrastructure budget.

---

## Next Steps

- [Query Interface](query-interface.md) -- How OpenClaw agents query screen data
- [Data Pipeline](data-pipeline.md) -- Windows to Supabase sync
- [Privacy & Security](privacy-security.md) -- Access control and encryption

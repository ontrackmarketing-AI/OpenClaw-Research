-- OpenClaw Screen Capture Schema
-- Run this in the Supabase SQL Editor after enabling pgvector extension.
--
-- Tables: screen_captures (OCR text + embeddings), screen_commands (Telegram relay)
-- Features: pgvector 768-dim embeddings, hybrid search RPC, IVFFlat index, FTS, RLS

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Screen captures table
CREATE TABLE screen_captures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    captured_at TIMESTAMPTZ NOT NULL,
    source_device TEXT NOT NULL DEFAULT 'windows_desktop',
    monitor_index INTEGER DEFAULT 0,
    window_title TEXT,
    app_name TEXT,
    ocr_text TEXT NOT NULL,
    content_hash TEXT,
    embedding vector(768),
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Screen commands table (Telegram -> Windows daemon relay)
CREATE TABLE screen_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command TEXT NOT NULL,          -- 'pause', 'resume', 'delete_last_30m', 'delete_today', 'status'
    args JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending',  -- 'pending', 'executed', 'failed'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ
);

-- 4. Indexes for screen_captures

-- Time-based queries (recent captures, time range filters)
CREATE INDEX idx_screen_captures_time ON screen_captures(captured_at DESC);

-- App-based filtering
CREATE INDEX idx_screen_captures_app ON screen_captures(app_name);

-- Content hash for dedup verification
CREATE INDEX idx_screen_captures_hash ON screen_captures(content_hash);

-- Partial index for embed worker: find captures missing embeddings
CREATE INDEX idx_screen_captures_unembedded
    ON screen_captures(captured_at ASC)
    WHERE embedding IS NULL;

-- Vector index (IVFFlat, 50 lists for expected <1M rows)
-- NOTE: This index is most effective after ~10K+ rows exist.
-- For small tables, Postgres will use sequential scan anyway.
CREATE INDEX idx_screen_captures_embedding
    ON screen_captures USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 50);

-- Full-text search index on OCR text
CREATE INDEX idx_screen_captures_text
    ON screen_captures USING GIN (to_tsvector('english', ocr_text));

-- 5. Row Level Security: service role only

ALTER TABLE screen_captures ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON screen_captures
    FOR ALL USING (false);

ALTER TABLE screen_commands ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role only" ON screen_commands
    FOR ALL USING (false);

-- 6. Hybrid search RPC function
-- Combines vector similarity (0.6 weight) and FTS rank (0.4 weight)
-- with optional time range and app filters.

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
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.id,
        sc.captured_at,
        sc.window_title,
        sc.app_name,
        sc.ocr_text,
        (1 - (sc.embedding <=> query_embedding))::FLOAT AS vector_similarity,
        ts_rank(to_tsvector('english', sc.ocr_text),
                plainto_tsquery('english', query_text))::FLOAT AS text_rank,
        (0.6 * (1 - (sc.embedding <=> query_embedding)) +
         0.4 * ts_rank(to_tsvector('english', sc.ocr_text),
                       plainto_tsquery('english', query_text)))::FLOAT AS combined_score
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

-- 7. Cleanup function for retention management
-- Deletes captures older than the specified number of days.
-- Returns the count of rows deleted.

CREATE OR REPLACE FUNCTION cleanup_old_captures(
    retention_days INT DEFAULT 90
)
RETURNS INT
LANGUAGE plpgsql AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM screen_captures
    WHERE captured_at < NOW() - (retention_days || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

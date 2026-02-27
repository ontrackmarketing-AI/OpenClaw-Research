# Supabase Schema Design

> Database schema for all OpenClaw data storage in Supabase PostgreSQL.

---

## Schema Overview

```
public schema
  |-- leads                    (enriched lead records)
  |-- contacts                 (synced from GHL)
  |-- documents                (RAG document storage with embeddings)
  |-- sessions                 (OpenClaw session history)
  |-- skill_logs               (skill execution audit trail)
  |-- competitor_data          (competitive intelligence snapshots)
  |-- content_calendar         (marketing content schedule)
  |-- enrichment_cache         (cached enrichment results)
  |-- credit_usage             (Clay credit tracking)
  |-- pipeline_snapshots       (daily pipeline state for reporting)
  |-- screen_captures          (OCR screen capture data with pgvector embeddings)
```

---

## Table Definitions

### 1. leads

The primary table for all discovered and enriched leads.

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core contact info
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company_name TEXT NOT NULL,
    website TEXT,

    -- Address
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    country TEXT DEFAULT 'US',

    -- Classification
    industry TEXT,
    category TEXT,              -- Google Places category
    employee_count INTEGER,
    annual_revenue NUMERIC,

    -- Scoring
    lead_score INTEGER DEFAULT 0 CHECK (lead_score >= 0 AND lead_score <= 100),
    score_tier TEXT CHECK (score_tier IN ('hot', 'warm', 'cold', 'disqualified')),
    pain_signals TEXT[],        -- Array of detected pain signals

    -- External IDs
    ghl_contact_id TEXT,        -- GoHighLevel contact ID
    ghl_opportunity_id TEXT,    -- GoHighLevel opportunity ID
    google_place_id TEXT,       -- Google Places ID (for dedup)
    clay_row_id TEXT,           -- Clay enrichment row ID

    -- Enrichment data (flexible JSONB for varying enrichment results)
    enrichment_data JSONB DEFAULT '{}',
    tech_stack TEXT[],          -- Array of technologies detected
    social_profiles JSONB DEFAULT '{}',  -- {"linkedin": "url", "facebook": "url", ...}
    review_data JSONB DEFAULT '{}',      -- {"google_rating": 4.2, "review_count": 87, ...}
    seo_data JSONB DEFAULT '{}',         -- {"domain_authority": 15, "organic_traffic": 200, ...}

    -- Status tracking
    status TEXT DEFAULT 'new' CHECK (status IN (
        'new', 'enriching', 'enriched', 'qualified', 'contacted',
        'engaged', 'meeting_booked', 'proposal_sent', 'won', 'lost', 'disqualified'
    )),
    discovery_source TEXT,       -- google_places, form, referral, cold_list
    enrichment_stage TEXT,       -- Which enrichment stage was last completed

    -- Timestamps
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    enriched_at TIMESTAMPTZ,
    last_contacted_at TIMESTAMPTZ,
    last_activity_at TIMESTAMPTZ,
    ghl_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_leads_email ON leads(email) WHERE email IS NOT NULL;
CREATE INDEX idx_leads_phone ON leads(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_leads_company ON leads(company_name);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_industry ON leads(industry);
CREATE INDEX idx_leads_google_place ON leads(google_place_id) WHERE google_place_id IS NOT NULL;
CREATE INDEX idx_leads_ghl_contact ON leads(ghl_contact_id) WHERE ghl_contact_id IS NOT NULL;
CREATE INDEX idx_leads_enrichment_data ON leads USING GIN(enrichment_data);
CREATE INDEX idx_leads_pain_signals ON leads USING GIN(pain_signals);

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### 2. contacts

Synced from GoHighLevel. Represents the CRM view of a lead.

```sql
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ghl_contact_id TEXT UNIQUE NOT NULL,  -- GHL's ID, unique
    lead_id UUID REFERENCES leads(id),     -- Link back to lead record

    -- Mirror of GHL contact fields
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company_name TEXT,
    website TEXT,

    -- GHL-specific
    ghl_tags TEXT[],
    ghl_custom_fields JSONB DEFAULT '{}',
    ghl_pipeline_stage TEXT,
    ghl_opportunity_status TEXT,
    ghl_assigned_to TEXT,

    -- Sync metadata
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    sync_direction TEXT CHECK (sync_direction IN ('ghl_to_supabase', 'supabase_to_ghl', 'bidirectional')),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contacts_ghl_id ON contacts(ghl_contact_id);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_lead_id ON contacts(lead_id);

CREATE TRIGGER contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### 3. documents

RAG document storage with vector embeddings for semantic search.

```sql
-- Requires: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN (
        'industry_report', 'case_study', 'template', 'proposal',
        'email_template', 'knowledge_base', 'competitor_analysis',
        'client_notes', 'process_doc', 'training'
    )),

    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Flexible metadata: {"industry": "dental", "source": "manual"}
    tags TEXT[],
    industry TEXT,                 -- For sector-based filtering

    -- Embeddings (choose one dimension based on model)
    embedding vector(768),         -- For nomic-embed-text (local, free)
    -- embedding vector(1536),     -- For OpenAI text-embedding-3-small (cloud, costs)

    -- Chunking metadata
    source_document_id UUID,       -- Parent document if this is a chunk
    chunk_index INTEGER,           -- Position in original document
    chunk_overlap INTEGER DEFAULT 200,  -- Overlap with adjacent chunks

    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_type ON documents(content_type);
CREATE INDEX idx_documents_industry ON documents(industry);
CREATE INDEX idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);  -- Adjust lists based on row count

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### 4. sessions

OpenClaw session history for audit and replay.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session info
    session_type TEXT NOT NULL CHECK (session_type IN (
        'enrichment', 'content_generation', 'analysis', 'reporting',
        'pipeline_management', 'manual_query', 'scheduled_task'
    )),
    trigger_source TEXT,           -- 'manual', 'webhook', 'cron', 'n8n'

    -- Execution
    skill_name TEXT,               -- Which OpenClaw skill was invoked
    input_data JSONB DEFAULT '{}', -- What was passed in
    output_data JSONB DEFAULT '{}',-- What was produced

    -- Status
    status TEXT DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    error_message TEXT,

    -- Metrics
    duration_ms INTEGER,           -- Execution time in milliseconds
    tokens_used INTEGER,           -- LLM tokens consumed
    tool_calls_count INTEGER,      -- Number of external tool calls
    credits_used NUMERIC,          -- Clay credits or other resource costs

    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_type ON sessions(session_type);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);
CREATE INDEX idx_sessions_skill ON sessions(skill_name);
```

### 5. skill_logs

Detailed audit trail for individual skill and tool executions.

```sql
CREATE TABLE skill_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id),

    -- Execution detail
    skill_name TEXT NOT NULL,
    tool_name TEXT,                 -- MCP tool or API adapter called
    tool_input JSONB DEFAULT '{}',
    tool_output JSONB DEFAULT '{}',

    -- Status
    status TEXT DEFAULT 'success' CHECK (status IN ('success', 'failure', 'timeout', 'skipped')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Performance
    duration_ms INTEGER,

    -- Context
    lead_id UUID REFERENCES leads(id),  -- If this log is related to a specific lead

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_skill_logs_session ON skill_logs(session_id);
CREATE INDEX idx_skill_logs_skill ON skill_logs(skill_name);
CREATE INDEX idx_skill_logs_tool ON skill_logs(tool_name);
CREATE INDEX idx_skill_logs_lead ON skill_logs(lead_id) WHERE lead_id IS NOT NULL;
CREATE INDEX idx_skill_logs_created ON skill_logs(created_at DESC);
```

### 6. competitor_data

Competitive intelligence snapshots for clients and prospects.

```sql
CREATE TABLE competitor_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Target
    lead_id UUID REFERENCES leads(id),
    business_name TEXT NOT NULL,
    business_domain TEXT,
    industry TEXT,
    location TEXT,                  -- City, State

    -- Competitor info
    competitor_name TEXT NOT NULL,
    competitor_domain TEXT,
    competitor_type TEXT CHECK (competitor_type IN ('direct', 'indirect', 'agency')),

    -- Competitive data (point-in-time snapshot)
    snapshot_data JSONB NOT NULL DEFAULT '{}',
    /*
    Example snapshot_data:
    {
        "google_rating": 4.5,
        "review_count": 200,
        "organic_keywords": 150,
        "estimated_traffic": 5000,
        "ad_spend_estimate": 2000,
        "social_followers": {"facebook": 500, "instagram": 1200},
        "tech_stack": ["WordPress", "GA4", "Facebook Pixel"],
        "website_speed_score": 85
    }
    */

    -- Analysis
    competitive_advantage TEXT,     -- Where the competitor is stronger
    competitive_gap TEXT,           -- Where the prospect can win

    snapshot_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitor_lead ON competitor_data(lead_id);
CREATE INDEX idx_competitor_industry ON competitor_data(industry);
CREATE INDEX idx_competitor_date ON competitor_data(snapshot_date DESC);
```

### 7. content_calendar

Marketing content schedule (mirrors Airtable for persistence and queries).

```sql
CREATE TABLE content_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Content details
    title TEXT NOT NULL,
    content_type TEXT NOT NULL CHECK (content_type IN (
        'blog_post', 'social_post', 'email', 'video', 'infographic',
        'case_study', 'landing_page', 'ad_copy', 'newsletter'
    )),
    platform TEXT CHECK (platform IN (
        'linkedin', 'facebook', 'instagram', 'twitter', 'blog',
        'email', 'youtube', 'tiktok', 'google_ads', 'meta_ads'
    )),

    -- Content
    brief TEXT,                    -- Content brief / outline
    draft TEXT,                    -- Draft copy
    final_copy TEXT,               -- Approved final copy
    assets JSONB DEFAULT '[]',     -- [{"type": "image", "url": "..."}, ...]
    published_url TEXT,

    -- Schedule
    due_date DATE,
    publish_date DATE,
    publish_time TIME,

    -- Status
    status TEXT DEFAULT 'idea' CHECK (status IN (
        'idea', 'brief_created', 'drafted', 'in_review',
        'approved', 'scheduled', 'published', 'archived'
    )),

    -- Assignment
    author TEXT,
    reviewer TEXT,
    client_id UUID,               -- If content is for a specific client

    -- Performance (filled in after publishing)
    performance_data JSONB DEFAULT '{}',
    /*
    {
        "views": 1500,
        "clicks": 45,
        "engagement_rate": 3.2,
        "conversions": 2,
        "comments": 12,
        "shares": 8
    }
    */

    -- Metadata
    industry TEXT,                 -- Target industry for the content
    keywords TEXT[],               -- SEO keywords targeted
    campaign TEXT,                 -- Associated marketing campaign
    airtable_record_id TEXT,       -- Link to Airtable record if synced

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_status ON content_calendar(status);
CREATE INDEX idx_content_platform ON content_calendar(platform);
CREATE INDEX idx_content_due ON content_calendar(due_date);
CREATE INDEX idx_content_publish ON content_calendar(publish_date);
CREATE INDEX idx_content_type ON content_calendar(content_type);

CREATE TRIGGER content_calendar_updated_at
    BEFORE UPDATE ON content_calendar
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### 8. enrichment_cache (for cost optimization)

```sql
CREATE TABLE enrichment_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cache key
    domain TEXT NOT NULL,
    data_type TEXT NOT NULL CHECK (data_type IN (
        'tech_stack', 'contact_info', 'social_profiles',
        'reviews', 'seo_data', 'company_data'
    )),

    -- Cached data
    data JSONB NOT NULL DEFAULT '{}',

    -- TTL
    enriched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Source
    provider TEXT,                 -- 'clay', 'builtwith', 'google_places', etc.
    credits_cost NUMERIC DEFAULT 0,

    UNIQUE(domain, data_type)
);

CREATE INDEX idx_cache_domain ON enrichment_cache(domain);
CREATE INDEX idx_cache_type ON enrichment_cache(data_type);
CREATE INDEX idx_cache_expires ON enrichment_cache(expires_at);
```

### 9. credit_usage

Clay credit tracking for enrichment cost management.

```sql
CREATE TABLE credit_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Service
    service TEXT NOT NULL,          -- 'clay', 'zerobounce', etc.
    operation TEXT NOT NULL,        -- 'enrich_lead', 'verify_email', etc.

    -- Usage
    credits_used NUMERIC NOT NULL,
    cost_usd NUMERIC,

    -- Context
    lead_id UUID REFERENCES leads(id),
    session_id UUID REFERENCES sessions(id),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credit_service ON credit_usage(service);
CREATE INDEX idx_credit_created ON credit_usage(created_at DESC);
```

### 10. pipeline_snapshots

Daily pipeline state for reporting and trend analysis.

```sql
CREATE TABLE pipeline_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    snapshot_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Pipeline counts by stage
    stage_counts JSONB NOT NULL DEFAULT '{}',
    /*
    {
        "new": 45,
        "enriching": 12,
        "qualified": 28,
        "contacted": 15,
        "meeting_booked": 3,
        "proposal_sent": 2
    }
    */

    -- Metrics
    total_leads INTEGER,
    hot_leads INTEGER,
    warm_leads INTEGER,
    cold_leads INTEGER,
    conversion_rate NUMERIC,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(snapshot_date)
);

CREATE INDEX idx_snapshot_date ON pipeline_snapshots(snapshot_date DESC);
```

### 11. screen_captures

OCR screen capture data from the user's Windows desktop. Supports hybrid vector + full-text search for natural language recall queries.

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
    content_hash TEXT,              -- MD5 of OCR text for dedup

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

**RPC function for hybrid search:**

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
        sc.id, sc.captured_at, sc.window_title, sc.app_name, sc.ocr_text,
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

See [Screen Database Storage & Indexing](../../08-Capabilities-Deep-Dive/screen-database/storage-indexing.md) for full details on chunking, retention, and query patterns.

```

---

## Relationships

```
leads (1) --> (0..1) contacts           -- A lead may or may not be synced to GHL
leads (1) --> (0..N) competitor_data    -- A lead can have multiple competitor snapshots
leads (1) --> (0..N) skill_logs         -- Logs of operations on this lead
sessions (1) --> (0..N) skill_logs      -- A session contains multiple skill executions
documents (standalone)                  -- RAG documents, queried independently
content_calendar (standalone)           -- Content items, may link to clients
enrichment_cache (standalone)           -- Cache layer, queried by domain
screen_captures (standalone)            -- OCR screen data, queried by time/text/vector
credit_usage (standalone)               -- Credit tracking, linked to leads/sessions
pipeline_snapshots (standalone)         -- Daily pipeline state snapshots
```

---

## Row Level Security Policies

For now, OpenClaw uses the `service_role` key which bypasses RLS. When adding multi-tenant support:

```sql
-- Example RLS for future multi-tenant use
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only see their own leads"
    ON leads FOR SELECT
    USING (auth.uid() = owner_id);

CREATE POLICY "Users can only insert their own leads"
    ON leads FOR INSERT
    WITH CHECK (auth.uid() = owner_id);
```

**Current recommendation:** Keep RLS disabled while using `service_role` key. Enable when adding user authentication.

---

## Migrations Strategy

Use raw SQL files versioned in the repository:

```
migrations/
  001_initial_schema.sql       -- All CREATE TABLE statements
  002_add_indexes.sql          -- Additional indexes after testing
  003_enable_pgvector.sql      -- CREATE EXTENSION vector; + embedding indexes
  004_add_rpc_functions.sql    -- match_documents and other RPC functions
```

Apply via Supabase SQL editor or CLI:
```bash
# Using supabase CLI
supabase db push

# Or directly:
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

---

## RESEARCH GAPS

- [ ] Determine optimal vector dimensions (768 vs 1536) based on embedding model choice
- [ ] Benchmark IVFFlat vs HNSW index performance for expected data volume
- [ ] Decide on JSONB vs separate columns for frequently queried enrichment fields
- [ ] Plan for table partitioning if lead volume exceeds 1M records
- [ ] Design archival strategy for old leads and sessions
- [ ] Tune ivfflat `lists` parameter for screen_captures as data volume grows (currently 50, increase at ~10K+ rows)
- [ ] Evaluate screen_captures retention automation (auto-delete OCR text > 90 days, keep daily summaries)

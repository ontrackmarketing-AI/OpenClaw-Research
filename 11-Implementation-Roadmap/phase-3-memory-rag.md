# Phase 3 - Memory System & RAG (Week 2-3)

## Goal

Give OpenClaw persistent memory and the ability to retrieve relevant knowledge from your marketing documents, industry research, and past interactions. By the end of this phase, the agent can recall past conversations and answer questions using your proprietary knowledge base.

---

## Why Memory and RAG Matter

Without memory, every conversation starts from zero. Without RAG, your agent knows nothing about your specific business, clients, or industry expertise. This phase transforms OpenClaw from a generic chatbot into a knowledgeable marketing assistant that improves over time.

---

## Day 1-2: File-First Memory Setup

OpenClaw uses a file-first approach to memory: human-readable Markdown files that the agent can read and update. This is the foundation before adding database-backed search.

### Configure Memory Directory

```bash
# Directory was created in Phase 1, verify it exists
ls -la ~/.openclaw/memory/

# Create subdirectories for organized memory
mkdir -p ~/.openclaw/memory/{conversations,projects,clients,knowledge,daily-logs}
```

### Create Initial MEMORY.md

This is the agent's primary context file -- it reads this at the start of every session.

```bash
cat > ~/.openclaw/memory/MEMORY.md << 'MD'
# OpenClaw Memory - OnTrack Marketing

## About This Business
- **Company**: OnTrack Marketing
- **Focus**: Digital marketing for local service businesses
- **Target sectors**: Plumbing, Solar, Dental, Legal
- **Primary services**: Lead generation, CRM management, content marketing, website development
- **Tools**: GoHighLevel (CRM), Clay.com (enrichment), n8n (automation), Airtable (content/tracking)

## Key Contacts
- [Owner name and role]
- [Any team members]

## Active Projects
- Rise Local Lead Pipeline: Automated lead discovery and enrichment for local businesses
- OnTrack Marketing: Main marketing agency operations
- OpenClaw deployment: This AI agent platform (you are here)

## Business Rules
- All outbound communications must be approved by human (HITL)
- Lead enrichment budget: track costs per lead
- Client data is confidential -- never expose to other clients
- Preferred communication tone: professional but friendly

## Current Monthly Costs
- Marketing stack: $156-206/month
- OpenClaw infrastructure: [to be determined after Phase 1]

## Important Decisions
- Using Mac Mini M4 Pro as dedicated AI server
- Ollama for local models (cost savings on simple tasks)
- Claude API for complex reasoning tasks
- File-first memory with SQLite hybrid search
- Tailscale for secure remote access

## What I've Learned About Your Preferences
- [Agent will add observations here over time]
MD
```

### Set Up Daily Logging

Configure OpenClaw to automatically log daily activity:

```bash
cat > ~/.openclaw/config/memory-config.json << 'JSON'
{
  "memory": {
    "primary_file": "/app/memory/MEMORY.md",
    "auto_save": true,
    "daily_log": {
      "enabled": true,
      "directory": "/app/memory/daily-logs",
      "format": "YYYY-MM-DD.md",
      "auto_summarize": true,
      "summarize_after_days": 7
    },
    "conversation_memory": {
      "enabled": true,
      "directory": "/app/memory/conversations",
      "max_conversations": 100,
      "archive_after_days": 30
    },
    "context_injection": {
      "always_include": ["/app/memory/MEMORY.md"],
      "include_recent_logs": 3,
      "max_context_tokens": 4000
    }
  }
}
JSON
```

### Test Memory Persistence

```bash
# Restart OpenClaw to load memory config
cd ~/.openclaw && docker compose restart

# Have a conversation that should be remembered
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Remember that our best-performing client is ABC Plumbing in Austin, TX. They generate 50 leads per month."}'

# Start a new session and test recall
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What do you know about our best-performing client?"}'

# Should reference ABC Plumbing and the 50 leads/month figure

# Verify the memory file was updated
cat ~/.openclaw/memory/MEMORY.md
# Check for new entries

# Verify daily log was created
ls ~/.openclaw/memory/daily-logs/
cat ~/.openclaw/memory/daily-logs/$(date +%Y-%m-%d).md
```

---

## Day 3-4: SQLite Hybrid Search

File-based memory works for small amounts of data but does not scale. SQLite with FTS5 (full-text search) and vector search gives you fast retrieval over thousands of documents.

### Configure SQLite Database

```bash
cat > ~/.openclaw/config/search-config.json << 'JSON'
{
  "search": {
    "engine": "sqlite-hybrid",
    "database_path": "/app/data/memory.db",
    "fts5": {
      "enabled": true,
      "tokenizer": "porter unicode61",
      "rank_function": "bm25"
    },
    "vector": {
      "enabled": true,
      "extension": "sqlite-vec",
      "embedding_model": "ollama/nomic-embed-text",
      "embedding_dimensions": 768,
      "distance_metric": "cosine"
    },
    "hybrid": {
      "fts_weight": 0.3,
      "vector_weight": 0.7,
      "min_score": 0.1,
      "max_results": 10
    }
  }
}
JSON
```

### Initialize the Database

```bash
# Restart to load search config
cd ~/.openclaw && docker compose restart

# Verify database was created
ls -la ~/.openclaw/data/memory.db

# Test FTS5 search
curl -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "plumbing leads", "type": "keyword"}'

# Test vector search
curl -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "what marketing works for plumbers", "type": "semantic"}'

# Test hybrid search (combines both)
curl -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "best lead generation channels for local services", "type": "hybrid"}'
```

### Generate Embeddings for Existing Memory

```bash
# Trigger embedding generation for all existing memory files
curl -X POST http://localhost:18789/api/memory/reindex \
  -H "Content-Type: application/json" \
  -d '{"scope": "all"}'

# Monitor progress
docker compose logs -f --tail=20 | grep -i embed

# Verify embeddings were created
curl http://localhost:18789/api/memory/stats | jq .
# Should show document count, embedding count, index size
```

### Test Hybrid Search Quality

Run test queries and evaluate relevance of results:

```bash
# Test keyword search (should find exact matches)
curl -s -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ABC Plumbing", "type": "keyword"}' | jq '.results[:3]'

# Test semantic search (should find conceptually related content)
curl -s -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how to get more customers for service businesses", "type": "semantic"}' | jq '.results[:3]'

# Test hybrid (best of both)
curl -s -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "plumbing marketing strategy Austin", "type": "hybrid"}' | jq '.results[:3]'
```

---

## Day 5-6: Sector Knowledge Bases

This is where OpenClaw becomes genuinely useful. You are loading it with your marketing expertise and industry knowledge.

### Create SMB Local Services Knowledge Base

Organize knowledge by sector. Start with the data you already have from Rise Local.

```bash
# Create knowledge base directories
mkdir -p ~/.openclaw/memory/knowledge/{plumbing,solar,dental,legal,general-smb}
```

### Ingest Industry Knowledge

Create structured knowledge documents for each sector. Here is an example for plumbing:

```bash
cat > ~/.openclaw/memory/knowledge/plumbing/industry-overview.md << 'MD'
# Plumbing Industry - Marketing Knowledge Base

## Market Overview
- US plumbing market: $130B+ annually
- Average local plumber revenue: $500K-2M/year
- Highly fragmented: mostly small businesses (1-20 employees)
- Seasonal peaks: winter (frozen pipes), spring (remodeling)

## Customer Profile
- Primary: homeowners 35-65, household income $60K+
- Secondary: property managers, commercial buildings
- Decision triggers: emergencies (burst pipe), planned renovations, appliance installs
- Research behavior: Google search first, then reviews, then call

## Marketing Channels (Effectiveness Ranked)
1. **Google Business Profile** (highest ROI) - free, drives 60-70% of local leads
2. **Google Local Service Ads** - pay-per-lead, $15-50/lead
3. **Google Ads (Search)** - $8-25 CPC, high intent
4. **SEO / Content** - long-term investment, 6-12 month payoff
5. **Facebook Ads** - better for brand awareness than direct leads
6. **Nextdoor** - neighborhood-level targeting, good for trust
7. **Direct mail** - 1-3% response rate, good for service reminders
8. **Vehicle wraps** - one-time cost, constant brand exposure

## Pain Points (What Plumbers Complain About)
- "I get leads but they are price shoppers"
- "I can not keep up with Google reviews"
- "My website looks outdated"
- "I am paying too much for leads on HomeAdvisor/Angi"
- "I do not have time for social media"
- "My competitors rank above me on Google"

## Pricing Benchmarks
- Website: $2,000-5,000 (custom), $500-1,500 (template)
- SEO: $750-2,000/month
- Google Ads management: $500-1,500/month + ad spend
- Social media: $500-1,000/month
- Full service retainer: $2,000-5,000/month

## Key Metrics
- Cost per lead: $15-75 depending on channel
- Lead-to-appointment rate: 30-50%
- Appointment-to-job rate: 60-80%
- Average job value: $300 (repair) to $5,000+ (remodel/install)
- Customer lifetime value: $3,000-15,000 (repeat + referrals)

## Competitive Landscape
- HomeAdvisor/Angi: expensive leads, shared with competitors
- Thumbtack: lower quality leads, price-focused customers
- Yelp: declining, but reviews still matter
- Google LSA: growing, becoming mandatory for top visibility
MD
```

Repeat this process for solar, dental, and legal sectors using your existing Rise Local research data.

### Configure Chunking Pipeline

```bash
cat > ~/.openclaw/config/chunking-config.json << 'JSON'
{
  "chunking": {
    "strategy": "recursive",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "separators": ["\n## ", "\n### ", "\n\n", "\n", " "],
    "metadata_extraction": {
      "extract_title": true,
      "extract_headers": true,
      "extract_tags": true,
      "include_source_path": true
    },
    "file_types": {
      ".md": "markdown",
      ".txt": "plain_text",
      ".pdf": "pdf_extract",
      ".docx": "docx_extract"
    }
  }
}
JSON
```

### Embed and Index All Knowledge

```bash
# Trigger full indexing of knowledge base
curl -X POST http://localhost:18789/api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "directory": "/app/memory/knowledge",
    "recursive": true,
    "chunk_config": "default",
    "embed": true,
    "force_reindex": false
  }'

# Monitor ingestion progress
docker compose logs -f --tail=30 | grep -i "ingest\|chunk\|embed"

# Check ingestion stats
curl http://localhost:18789/api/knowledge/stats | jq .
# Expected: document count, chunk count, embedding count, index size
```

### Test Sector Retrieval

```bash
# Test: question about plumbing marketing
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What marketing channels work best for plumbers? Rank them by ROI."}' | jq .response

# Verify the answer references your knowledge base data, not just general LLM knowledge
# It should mention specific numbers like "$15-50/lead for LSA" from your knowledge base

# Test: cross-sector comparison
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Compare the average cost per lead for plumbing vs dental marketing."}' | jq .response
```

---

## Day 7-8: Supabase pgvector (Optional)

This step is optional for Phase 3. Start with local SQLite and only migrate to Supabase if you need cloud-based access or the dataset grows beyond what SQLite handles comfortably (typically 100K+ chunks).

### Reactivate Supabase Project

1. Log into https://supabase.com/dashboard
2. Find your paused project
3. Click "Restore project"
4. Wait for it to come back online (~2-5 minutes)

### Enable pgvector Extension

```sql
-- In Supabase SQL Editor:

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  metadata JSONB DEFAULT '{}',
  embedding vector(768),  -- matches nomic-embed-text dimensions
  source_path TEXT,
  chunk_index INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the vector similarity search index
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create full-text search index
CREATE INDEX ON documents USING gin (to_tsvector('english', content));

-- Create metadata index
CREATE INDEX ON documents USING gin (metadata);

-- Create the similarity search function
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(768),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.content,
    d.metadata,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM documents d
  WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create hybrid search function (FTS + vector)
CREATE OR REPLACE FUNCTION hybrid_search(
  query_text TEXT,
  query_embedding vector(768),
  fts_weight FLOAT DEFAULT 0.3,
  vector_weight FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  combined_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH fts_results AS (
    SELECT d.id, d.content, d.metadata,
           ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', query_text)) AS fts_score
    FROM documents d
    WHERE to_tsvector('english', d.content) @@ plainto_tsquery('english', query_text)
  ),
  vector_results AS (
    SELECT d.id, d.content, d.metadata,
           1 - (d.embedding <=> query_embedding) AS vector_score
    FROM documents d
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count * 3
  )
  SELECT
    COALESCE(f.id, v.id) AS id,
    COALESCE(f.content, v.content) AS content,
    COALESCE(f.metadata, v.metadata) AS metadata,
    (COALESCE(f.fts_score, 0) * fts_weight + COALESCE(v.vector_score, 0) * vector_weight) AS combined_score
  FROM fts_results f
  FULL OUTER JOIN vector_results v ON f.id = v.id
  ORDER BY combined_score DESC
  LIMIT match_count;
END;
$$;
```

### Add Supabase Credentials to OpenClaw

```bash
# Add to .env
cat >> ~/.openclaw/.env << 'ENV'

# Supabase (optional, for cloud RAG)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
ENV

cd ~/.openclaw && docker compose restart
```

### Compare SQLite vs Supabase RAG

```bash
# Run the same query against both backends
QUERY="What marketing channels work best for plumbers?"

# SQLite (local)
time curl -s -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"backend\": \"sqlite\"}" | jq '.results | length'

# Supabase (cloud)
time curl -s -X POST http://localhost:18789/api/search \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"backend\": \"supabase\"}" | jq '.results | length'

# Compare:
# - Latency: SQLite should be faster (no network round trip)
# - Quality: Should be similar (same embeddings)
# - Decision: Use SQLite as primary, Supabase for backup/scaling
```

### Decision Point

| Factor | SQLite (Local) | Supabase (Cloud) |
|--------|---------------|-----------------|
| Latency | ~5-20ms | ~100-300ms |
| Cost | Free | Free tier, then $25/mo |
| Capacity | Millions of rows | Billions of rows |
| Availability | Requires Mac Mini on | Always available |
| Backup | Manual | Automatic |
| **Recommendation** | **Primary** | **Backup / Scale-out** |

Start with SQLite. Move to Supabase if/when dataset exceeds 100K chunks or you need access when Mac Mini is offline.

---

## Day 9-10: Knowledge Ingestion Pipeline

### Build the Ingestion Pipeline

This pipeline handles: File upload -> Text extraction -> Chunking -> Embedding -> Storage

```bash
cat > ~/.openclaw/config/ingestion-pipeline.json << 'JSON'
{
  "ingestion": {
    "pipeline": [
      {
        "step": "extract",
        "config": {
          "pdf": {"engine": "pdf-parse", "ocr_fallback": true},
          "docx": {"engine": "mammoth"},
          "html": {"engine": "cheerio", "strip_scripts": true},
          "md": {"engine": "native"},
          "txt": {"engine": "native"}
        }
      },
      {
        "step": "clean",
        "config": {
          "remove_extra_whitespace": true,
          "normalize_unicode": true,
          "remove_headers_footers": true,
          "min_chunk_length": 50
        }
      },
      {
        "step": "chunk",
        "config": {
          "strategy": "recursive",
          "chunk_size": 512,
          "overlap": 50
        }
      },
      {
        "step": "embed",
        "config": {
          "model": "ollama/nomic-embed-text",
          "batch_size": 32,
          "dimensions": 768
        }
      },
      {
        "step": "store",
        "config": {
          "primary": "sqlite",
          "secondary": "supabase",
          "deduplicate": true
        }
      }
    ],
    "monitoring": {
      "log_progress": true,
      "alert_on_failure": true,
      "track_costs": true
    }
  }
}
JSON
```

### Ingest Existing Marketing Documents

Gather your existing documents and place them in the knowledge base:

```bash
# Create an inbox directory for documents to ingest
mkdir -p ~/.openclaw/memory/knowledge/_inbox

# Copy documents from your Windows PC via SCP
# From Windows PowerShell:
# scp -r "C:\Users\Owner\Documents\Marketing\*" user@mac-mini:~/.openclaw/memory/knowledge/_inbox/

# Or mount a shared folder between Windows and Mac Mini

# Trigger ingestion of the inbox
curl -X POST http://localhost:18789/api/knowledge/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "directory": "/app/memory/knowledge/_inbox",
    "recursive": true,
    "move_after_ingest": "/app/memory/knowledge/_processed",
    "embed": true
  }'
```

### Documents to Ingest (Checklist)

| Document Type | Source | Priority |
|--------------|--------|----------|
| Rise Local pipeline documentation | Existing project files | High |
| Industry pain points research | Your research notes | High |
| Pricing and packaging templates | OnTrack Marketing files | High |
| Competitor analysis reports | Existing research | Medium |
| Case studies and results | Client folders | Medium |
| Email templates | GHL templates | Medium |
| Blog posts and content | Website/content calendar | Low |
| Marketing channel playbooks | Personal knowledge | High |

### Verify Comprehensive Retrieval

After ingestion, test that the system can retrieve relevant information across all document types:

```bash
# Test retrieval across different knowledge areas

# 1. Industry knowledge
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the top 3 pain points for local plumbing businesses when it comes to marketing?"}'

# 2. Pricing knowledge
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I charge for a monthly SEO retainer for a plumbing company?"}'

# 3. Process knowledge
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Walk me through the Rise Local lead enrichment process step by step."}'

# 4. Cross-domain reasoning
curl -s -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "If a solar company has a $3000/month marketing budget, how would you allocate it across channels?"}'
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| MEMORY.md loaded at session start | Ask "what business am I in?" | [ ] |
| Memory persists across sessions | Tell it something, restart, ask about it | [ ] |
| Daily logs being created | Check `memory/daily-logs/` directory | [ ] |
| SQLite FTS5 working | Keyword search returns relevant results | [ ] |
| Vector search working | Semantic search returns conceptually related results | [ ] |
| Hybrid search working | Combined search beats either individually | [ ] |
| Sector knowledge indexed | At least plumbing sector fully loaded | [ ] |
| Knowledge retrieval accurate | RAG answers include specific numbers from your data | [ ] |
| Ingestion pipeline functional | Can ingest new documents end-to-end | [ ] |
| Embedding generation fast | nomic-embed-text generating on M4 Pro without lag | [ ] |

---

## Knowledge Base Size Estimates

| Content | Estimated Chunks | Estimated Storage |
|---------|-----------------|-------------------|
| MEMORY.md + daily logs | 50-100 | < 1MB |
| Industry knowledge (4 sectors) | 200-400 | 2-5MB |
| Marketing documents | 500-1000 | 5-10MB |
| Case studies | 100-200 | 1-3MB |
| Templates and playbooks | 200-400 | 2-5MB |
| **Total** | **1,050-2,100** | **10-24MB** |

This is well within SQLite's comfortable range. You would need 50-100x this volume before considering Supabase as primary.

---

## Next Phase

With memory and RAG working, proceed to [Phase 4 - Core Skills](phase-4-core-skills.md). Your agent now has the knowledge foundation to support intelligent CRM operations, lead enrichment, and content generation.

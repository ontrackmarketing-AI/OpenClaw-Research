# OnTrack Marketing -- Integration with OpenClaw

## System Overview

OnTrack Marketing is a multi-tenant marketing AI platform with full RAG (Retrieval-Augmented Generation) capabilities. It is a working product with real infrastructure.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.11+)
- **Frontend:** Next.js (React, TypeScript)
- **Database:** PostgreSQL (relational data, tenant management, user accounts)
- **Cache:** Redis (session management, rate limiting, query caching)
- **Vector Database:** Qdrant (document embeddings, semantic search, RAG retrieval)
- **Deployment:** Docker containers (all services compose together)

**Current RAG Capabilities:**
- Document ingestion pipeline: PDF, DOCX, TXT, CSV, HTML
- Chunking strategy: recursive character splitting with overlap (512 tokens, 50 token overlap)
- Embedding model: OpenAI `text-embedding-3-small` (1536 dimensions)
- Vector storage: Qdrant collections per tenant, with metadata filtering
- Retrieval: hybrid search (dense vector similarity + sparse keyword matching)
- Generation: Claude or GPT-4 with retrieved context injection
- Multi-tenant isolation: each tenant has its own Qdrant collection and PostgreSQL schema

---

## Integration Approaches

### Option 1: API Bridge (Recommended as Starting Point)

OpenClaw calls OnTrack Marketing's existing FastAPI endpoints to leverage its RAG capabilities without modifying OnTrack's internals.

**Architecture:**
```
OpenClaw Agent
    |
    v
OpenClaw Skill: "ontrack_rag_query"
    |
    v
HTTP Request to OnTrack Marketing API
    |
    v
FastAPI Backend
    |
    +-- PostgreSQL (tenant lookup, metadata)
    +-- Redis (cache check)
    +-- Qdrant (vector search)
    +-- LLM (generate answer from context)
    |
    v
Response back to OpenClaw
```

**Required API endpoints (verify these exist or create them):**

| Endpoint | Method | Purpose | Request Body |
|---|---|---|---|
| `/api/v1/documents/ingest` | POST | Upload and embed a document | `{ "tenant_id": "...", "file": binary, "metadata": {} }` |
| `/api/v1/query` | POST | RAG query -- search + generate | `{ "tenant_id": "...", "query": "...", "top_k": 5, "filters": {} }` |
| `/api/v1/search` | POST | Vector search only (no generation) | `{ "tenant_id": "...", "query": "...", "top_k": 10, "filters": {} }` |
| `/api/v1/collections` | GET | List available knowledge collections | Query param: `tenant_id` |
| `/api/v1/documents` | GET | List ingested documents | Query param: `tenant_id`, pagination |
| `/api/v1/health` | GET | Health check | -- |

**OpenClaw skill implementation:**

```python
# openclaw/skills/ontrack_rag.py

import httpx
from typing import Optional

ONTRACK_BASE_URL = "http://localhost:8000"  # Or Docker network URL
ONTRACK_API_KEY = os.environ["ONTRACK_API_KEY"]

class OnTrackRAGSkill:
    """Skill for querying OnTrack Marketing's RAG system."""

    name = "ontrack_rag_query"
    description = "Query the OnTrack Marketing knowledge base using RAG. Returns relevant information from ingested documents."

    async def execute(
        self,
        query: str,
        tenant_id: str = "default",
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ONTRACK_BASE_URL}/api/v1/query",
                json={
                    "tenant_id": tenant_id,
                    "query": query,
                    "top_k": top_k,
                    "filters": filters or {}
                },
                headers={"Authorization": f"Bearer {ONTRACK_API_KEY}"}
            )
            response.raise_for_status()
            return response.json()

    async def search_only(
        self,
        query: str,
        tenant_id: str = "default",
        top_k: int = 10
    ) -> list:
        """Vector search without generation -- useful when OpenClaw
        wants to handle the generation itself with its own prompt."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{ONTRACK_BASE_URL}/api/v1/search",
                json={
                    "tenant_id": tenant_id,
                    "query": query,
                    "top_k": top_k
                },
                headers={"Authorization": f"Bearer {ONTRACK_API_KEY}"}
            )
            response.raise_for_status()
            return response.json()["results"]

    async def ingest_document(
        self,
        file_path: str,
        tenant_id: str = "default",
        metadata: Optional[dict] = None
    ) -> dict:
        """Ingest a new document into OnTrack's RAG system."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, "rb") as f:
                response = await client.post(
                    f"{ONTRACK_BASE_URL}/api/v1/documents/ingest",
                    files={"file": f},
                    data={
                        "tenant_id": tenant_id,
                        "metadata": json.dumps(metadata or {})
                    },
                    headers={"Authorization": f"Bearer {ONTRACK_API_KEY}"}
                )
            response.raise_for_status()
            return response.json()
```

**Pros:**
- Zero changes to OnTrack Marketing codebase
- Clean separation of concerns
- OnTrack can be updated independently
- Multi-tenant isolation is preserved

**Cons:**
- Network latency between containers (minimal on same host)
- Dependency on OnTrack being running and healthy
- API rate limits may need tuning for OpenClaw's query volume

### Option 2: Shared Qdrant Access

OpenClaw connects directly to the same Qdrant instance that OnTrack uses, bypassing the FastAPI layer for reads.

**Architecture:**
```
OpenClaw Agent -----> Qdrant (direct connection, read-only)
                         ^
                         |
OnTrack Marketing -------+ (read-write)
```

**Implementation:**

```python
# openclaw/skills/direct_qdrant.py

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import openai  # For generating query embeddings

QDRANT_HOST = "localhost"  # Or Docker network hostname
QDRANT_PORT = 6333
EMBEDDING_MODEL = "text-embedding-3-small"

class DirectQdrantSkill:
    def __init__(self):
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.openai = openai.OpenAI()

    def embed_query(self, text: str) -> list[float]:
        response = self.openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    async def search(
        self,
        query: str,
        collection_name: str,  # Maps to tenant
        top_k: int = 10,
        score_threshold: float = 0.7
    ) -> list[dict]:
        query_vector = self.embed_query(query)

        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=score_threshold,
            with_payload=True
        )

        return [
            {
                "text": hit.payload.get("text", ""),
                "metadata": hit.payload.get("metadata", {}),
                "score": hit.score,
                "document_id": hit.payload.get("document_id", "")
            }
            for hit in results
        ]
```

**Pros:**
- Lower latency (no HTTP overhead)
- OpenClaw controls its own retrieval logic and prompting
- Can do complex vector queries that OnTrack's API may not expose

**Cons:**
- Tight coupling: if OnTrack changes its Qdrant schema, OpenClaw breaks
- Must use the exact same embedding model and parameters as OnTrack
- Write conflicts if both try to modify the same collection
- Loses OnTrack's caching layer (Redis)

**Safeguard:** If using this approach, OpenClaw should only have READ access to Qdrant collections. All writes should go through OnTrack's API.

### Option 3: Migration to OpenClaw Native Memory

Gradually move OnTrack's RAG knowledge into OpenClaw's own memory/knowledge system.

**Migration process:**

1. **Export all documents from OnTrack:**
   ```python
   # Script to export all documents and their chunks from OnTrack
   async def export_ontrack_knowledge(tenant_id: str):
       # Get all documents
       docs = await ontrack_api.get("/api/v1/documents", params={"tenant_id": tenant_id})

       for doc in docs:
           # Get the original file if stored
           original = await ontrack_api.get(f"/api/v1/documents/{doc['id']}/download")

           # Get all chunks with their embeddings
           chunks = await qdrant.scroll(
               collection_name=f"tenant_{tenant_id}",
               scroll_filter=Filter(
                   must=[FieldCondition(key="document_id", match=MatchValue(value=doc['id']))]
               ),
               with_vectors=True,
               with_payload=True
           )

           yield {
               "document": doc,
               "original_file": original,
               "chunks": chunks
           }
   ```

2. **Re-ingest into OpenClaw's memory system:**
   - If OpenClaw uses the same embedding model, vectors can be copied directly (no re-embedding cost)
   - If different embedding model, re-embed all chunks (cost: ~$0.02 per 1M tokens with `text-embedding-3-small`)

3. **Verify parity:**
   - Run 50 test queries against both systems
   - Compare top-5 results for overlap (should be > 80% match)
   - Compare generation quality side-by-side

4. **Cut over:**
   - Route all RAG queries to OpenClaw's native system
   - Keep OnTrack running in read-only mode for 2 weeks as fallback
   - Decommission OnTrack's RAG pipeline after validation period

**Pros:**
- Single system, simpler operations
- OpenClaw has full control over chunking, embedding, retrieval strategies
- No inter-service dependencies

**Cons:**
- Significant migration effort
- Risk of knowledge loss if migration is incomplete
- Loses OnTrack's battle-tested RAG pipeline
- Must rebuild multi-tenant isolation in OpenClaw

---

## Recommended Integration Timeline

| Phase | Timeframe | Action | Risk Level |
|---|---|---|---|
| Phase 1 | Week 1 | Deploy Option 1 (API Bridge) | Low |
| Phase 2 | Week 2-3 | Build and test OpenClaw skills wrapping OnTrack API | Low |
| Phase 3 | Month 2 | Evaluate if Option 1 meets all needs | -- |
| Phase 4 | Month 2-3 | If needed, begin Option 3 migration | Medium |
| Phase 5 | Month 3-4 | Complete migration, validate, decommission OnTrack RAG | Medium |

**Decision point at Phase 3:** If the API bridge handles all use cases well and OnTrack's RAG quality is good, there is no need to migrate. Only migrate if:
- You need tighter integration between RAG results and OpenClaw's decision-making
- OnTrack's maintenance overhead is too high
- You need RAG capabilities that OnTrack's API cannot expose

---

## What to Reuse from OnTrack

### Reuse Immediately

| Asset | Where It Lives | How OpenClaw Uses It |
|---|---|---|
| Qdrant embeddings | Qdrant collections | Query via API or direct access |
| Document processing pipeline | FastAPI `/ingest` endpoint | Call to ingest new documents |
| Sector knowledge | Embedded in Qdrant | Query for industry-specific context |
| Tenant management | PostgreSQL | Leverage for multi-client isolation |
| Redis caching | Redis instance | Benefit from cached query results via API |

### Reuse After Review

| Asset | Consideration |
|---|---|
| Chunking strategy (512 tokens, 50 overlap) | Good default; may want to experiment with larger chunks (1024) for some content types |
| Embedding model (text-embedding-3-small) | Cost-effective but consider `text-embedding-3-large` for higher accuracy on critical knowledge |
| Hybrid search (dense + sparse) | Keep this -- significantly better than pure dense search for keyword-heavy queries |
| Multi-tenant isolation | Essential for client data separation; replicate this in any migration |

### What OpenClaw Adds Beyond OnTrack

| Capability | OnTrack | OpenClaw |
|---|---|---|
| Autonomous agent loop | No (responds to queries) | Yes (plans, executes, reflects) |
| Multi-channel delivery | No (API only) | Yes (email, Slack, GHL, Airtable) |
| Tool orchestration | No | Yes (chains tools together) |
| Memory/learning | Static embeddings | Dynamic memory that evolves |
| Client communication | No | Drafts and sends communications |
| Campaign management | No | Full campaign lifecycle |
| Lead generation | No | Integrated with Rise Local pipeline |

---

## Deployment Architecture

### Docker Compose Setup (Both Services on Mac Mini)

```yaml
version: '3.8'

services:
  # --- OnTrack Marketing Stack ---
  ontrack-api:
    build: ./ontrack-marketing/backend
    container_name: ontrack-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ontrack:${PG_PASSWORD}@postgres:5432/ontrack
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - postgres
      - redis
      - qdrant
    networks:
      - backend

  ontrack-frontend:
    build: ./ontrack-marketing/frontend
    container_name: ontrack-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://ontrack-api:8000
    networks:
      - backend

  # --- Shared Infrastructure ---
  postgres:
    image: postgres:16
    container_name: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=ontrack
      - POSTGRES_PASSWORD=${PG_PASSWORD}
      - POSTGRES_DB=ontrack
    ports:
      - "5432:5432"
    networks:
      - backend

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    networks:
      - backend

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC
    volumes:
      - qdrantdata:/qdrant/storage
    networks:
      - backend

  # --- OpenClaw (connects to shared infra) ---
  openclaw:
    build: ./openclaw
    container_name: openclaw-agent
    environment:
      - ONTRACK_API_URL=http://ontrack-api:8000
      - ONTRACK_API_KEY=${ONTRACK_API_KEY}
      - QDRANT_HOST=qdrant  # Direct access if using Option 2
      - QDRANT_PORT=6333
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    networks:
      - backend

networks:
  backend:
    driver: bridge

volumes:
  pgdata:
  redisdata:
  qdrantdata:
```

### Resource Estimates

| Service | RAM | CPU | Disk |
|---|---|---|---|
| OnTrack API (FastAPI) | 512 MB | 1 core | Minimal |
| OnTrack Frontend (Next.js) | 256 MB | 0.5 core | Minimal |
| PostgreSQL | 1 GB | 1 core | 5-50 GB (depends on data volume) |
| Redis | 256 MB | 0.5 core | Minimal |
| Qdrant | 2-4 GB | 2 cores | 1-10 GB (depends on document count) |
| OpenClaw | 2-4 GB | 2 cores | Minimal |
| **Total** | **6-10 GB** | **7 cores** | **6-60 GB** |

**Fits comfortably on a Mac Mini with 16+ GB RAM.** If RAM is tight, Qdrant is the most memory-hungry service and can be configured with memory-mapped storage to reduce its RAM footprint.

---

## Authentication and Security

- **OnTrack API key:** Generate a dedicated API key for OpenClaw with appropriate scope (read + write on relevant endpoints). Do not reuse client-facing keys.
- **Qdrant access:** If using Option 2 (direct Qdrant), configure Qdrant's API key authentication. OpenClaw gets a read-only key.
- **PostgreSQL:** OpenClaw should NOT have direct PostgreSQL access. All relational data goes through OnTrack's API.
- **Redis:** OpenClaw does not need direct Redis access. Caching is handled transparently by OnTrack.
- **Network isolation:** All services communicate over the Docker bridge network. Only necessary ports are exposed to the host.

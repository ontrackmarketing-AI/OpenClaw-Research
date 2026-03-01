# Phase 2: Memory and Model Routing - Research

**Researched:** 2026-02-28
**Domain:** Persistent agent memory, hybrid search (FTS5 + vector), log compaction, LLM model routing, prompt caching
**Confidence:** HIGH

## Summary

Phase 2 builds the agent's brain and routing layer. The memory system stores persistent facts in MEMORY.md (loaded into every session), indexes all content into SQLite FTS5 for keyword search and Qdrant for semantic search, and merges results via Reciprocal Rank Fusion. Daily logs capture significant actions and compact into weekly summaries after 30 days. The model router classifies incoming tasks and dispatches them to the cheapest capable tier: Ollama qwen3:14b (free, classification/formatting), Claude Haiku 4.5 (standard), Claude Sonnet 4.5 (reasoning), or Claude Opus 4.6 (client-facing quality). Prompt caching on system prompts delivers 90% input token cost reduction on cache hits.

All infrastructure dependencies are already running from Phase 1: Qdrant container (healthy, no collections yet, port 6333), Ollama with qwen3:14b and nomic-embed-text models loaded, PostgreSQL, Redis, and the TypeScript project at `~/.openclaw/` with better-sqlite3, tsx, and yaml already installed. The existing codebase has established patterns for synchronous SQLite access (cost tracker), YAML config loading, structured JSON logging, and TypeScript module organization.

**Primary recommendation:** Build memory write/read first (MEMORY.md + daily logs), then layer FTS5 indexing, then Qdrant vector search, then RRF hybrid merge, then model routing and prompt caching. Each layer can be tested independently before integration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Hybrid auto-capture: auto-persist high-confidence items (client decisions, project facts, tool configs); explicit persist for subjective preferences and opinions; agent asks "should I remember this?" for borderline cases
- When MEMORY.md approaches 4,000 token budget, compress related entries into denser summaries -- nothing is truly lost, just condensed
- Organize memory by topic, not chronologically -- group related memories together (client prefs, project decisions, tool configs)
- MEMORY.md serves as an index with summaries; detailed context overflows into separate topic files (e.g., `clients.md`, `tools.md`)
- Smart prefetch: auto-search memory for tasks involving clients, projects, or past decisions; skip for generic/simple tasks (formatting, math, one-off questions); agent can always search on-demand
- When no relevant results found, agent briefly notes "I don't have prior context on X" and continues -- transparent but non-blocking
- Query-adaptive RRF weights: lean toward keyword (FTS5) for exact names/terms (client names, tool configs); lean toward semantic (Qdrant) for conceptual queries (past decisions about X); agent classifies the query type first
- Return top 3 results by default; agent can request more if confidence is low
- Daily logs capture significant actions only: tasks completed, decisions made, client interactions, errors encountered -- not every API call or file read
- Weekly compaction (after 30 days): preserve outcomes plus notable context -- what happened and why when it matters
- Further compaction: weekly summaries compact to monthly summaries after 90 days; monthly summaries persist indefinitely
- Proactively surface log insights: agent identifies trends and patterns from logs and surfaces them during check-ins or when contextually relevant
- Default to the most capable tier likely to succeed first try; agent learns over time which tasks can be safely downgraded to cheaper tiers
- Core 4-tier system: Ollama qwen3:14b (free, classification/formatting) -> Haiku (standard tasks) -> Sonnet (reasoning) -> Opus (client-facing quality)
- On fallback (tier unavailable): auto-escalate silently, log the event, surface in next check-in -- "Ollama was down for 2 hours, routed 15 tasks to Haiku instead"
- Daily cost summary: track tokens and costs per model per day, surface in daily log and weekly summaries

### Claude's Discretion
- Kimi and Gemini placement -- start with the core Claude + Ollama stack, add alternative models for specific niches as they prove useful during implementation
- Exact compaction algorithms and scheduling
- Embedding model configuration details for Qdrant
- Prompt caching implementation specifics
- FTS5 tokenizer tuning

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MEMR-01 | MEMORY.md persistent agent memory with 4,000 token budget and auto-compaction | File read/write module using Node.js `fs`; token counting via tiktoken or character estimate (1 token ~ 4 chars); compaction triggers LLM summarization when threshold exceeded; existing `~/.openclaw/memory/MEMORY.md` already has 80 lines of content |
| MEMR-02 | SQLite FTS5 full-text search index (porter unicode61 tokenizer) for keyword matching | better-sqlite3 v12.6.2 already installed; FTS5 is compiled into better-sqlite3 by default; `CREATE VIRTUAL TABLE ... USING fts5(content, tokenize='porter unicode61')` with BM25 ranking |
| MEMR-03 | Qdrant vector collection (768-dim, nomic-embed-text embeddings, cosine similarity 0.7 threshold) for semantic search | Qdrant v1.17.0 container running at 127.0.0.1:6333; `@qdrant/js-client-rest` v1.17.0 for TypeScript client; `ollama` npm v0.6.3 for embedding generation via nomic-embed-text (verified 768-dim); cosine distance collection with similarity threshold filter |
| MEMR-04 | Hybrid search merging vector + FTS5 via Reciprocal Rank Fusion (0.6 vector / 0.4 FTS5 weights) | RRF algorithm with k=60 constant; query-adaptive weights per user decision (keyword-heavy for exact terms, semantic-heavy for conceptual queries); custom implementation -- no library needed, ~50 lines of code |
| MEMR-05 | Daily log directory with compaction (daily -> weekly summaries after 30 days) | Log files at `~/.openclaw/memory/logs/YYYY/MM/DD.md`; compaction via LLM summarization (use Haiku for cost efficiency); `node-cron` for scheduling; weekly summaries at `logs/summaries/YYYY-WNN.md`; monthly compaction after 90 days |
| MODL-01 | 4-tier model routing -- Ollama qwen3:14b -> Haiku 4.5 -> Sonnet 4.5 -> Opus 4.6 | Router module with task classification (regex + keyword rules); `ollama` npm for local tier; `@anthropic-ai/sdk` v0.78.0 for Claude tiers; cost tracking integration with existing `~/.openclaw/src/cost/tracker.ts` |
| MODL-02 | Kimi and Gemini available as additional model options | Deferred to Claude's discretion -- start with core 4-tier stack per user decision; add when specific niches emerge |
| MODL-03 | Automatic fallback chain -- if a tier fails, escalate to next tier with error handling | Try/catch with tier escalation; health check pings for Ollama (`GET /api/tags`); Anthropic SDK handles retries internally; structured JSON logging for fallback events |
| MODL-04 | Prompt caching enabled for system prompts -- 60-90% input token cost reduction | Anthropic API supports `cache_control: {type: "ephemeral"}` at request level (automatic caching) or on individual content blocks; cache read tokens cost 10% of base input price; 5-minute TTL refreshed on each use; minimum cacheable: 1024 tokens for Sonnet/Haiku, 4096 for Opus |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| better-sqlite3 | 12.6.2 | FTS5 full-text search index, memory metadata | Already installed from Phase 1; synchronous API ideal for search; FTS5 compiled in by default |
| @qdrant/js-client-rest | 1.17.0 | Vector similarity search against Qdrant | Official TypeScript client; versioned to match Qdrant engine; REST API with full type safety |
| ollama | 0.6.3 | Local model inference (qwen3:14b) + embeddings (nomic-embed-text) | Official JS library; typed API for chat, generate, embed; custom host support |
| @anthropic-ai/sdk | 0.78.0 | Claude API calls (Haiku, Sonnet, Opus) with prompt caching | Official TypeScript SDK; native prompt caching support; streaming; automatic retries |
| yaml | 2.8.2 | Configuration file parsing | Already installed from Phase 1 |
| node-cron | 3.0.3 | Scheduling log compaction jobs | Lightweight cron-style scheduler; no daemon needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tiktoken | 1.0.19 | Accurate token counting for MEMORY.md budget | When char-based estimation is insufficient; counts tokens per model tokenizer |
| tsx | 4.21.0 | TypeScript execution (already installed) | Running all TypeScript modules directly |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Qdrant (external) | sqlite-vec (embedded) | sqlite-vec keeps everything in SQLite but lacks Qdrant's filtering, payload storage, and HNSW indexing performance; Qdrant is already running from Phase 1 and is the project's chosen vector store |
| better-sqlite3 FTS5 | PostgreSQL full-text search | PostgreSQL is running but better-sqlite3 is already integrated for cost tracking; keeping FTS5 in SQLite avoids adding PostgreSQL as a dependency for the memory module |
| ollama npm package | Direct HTTP to localhost:11434 | ollama package provides typed responses and embed() method; avoids manual JSON parsing |
| @anthropic-ai/sdk | Vercel AI SDK (@ai-sdk/anthropic) | Vercel AI SDK adds abstraction layer; direct Anthropic SDK gives full control over prompt caching, token counts, and cost tracking |
| node-cron | External cron (crontab) | node-cron keeps scheduling in the application; easier to manage lifecycle and test |
| tiktoken | Character estimate (1 token ~ 4 chars) | Character estimate is 80-90% accurate and zero-dependency; tiktoken is exact but adds a native dependency. Start with char estimate, upgrade if precision matters. |

### Installation

```bash
cd ~/.openclaw
npm install @qdrant/js-client-rest@1.17.0 ollama@0.6.3 @anthropic-ai/sdk@0.78.0 node-cron@3.0.3
npm install -D @types/node-cron
```

Optional (if accurate token counting needed):
```bash
npm install tiktoken@1.0.19
```

## Architecture Patterns

### Recommended Project Structure

```
~/.openclaw/src/
├── memory/
│   ├── types.ts                 # Memory types (MemoryEntry, SearchResult, LogEntry)
│   ├── persistent.ts            # MEMORY.md read/write/compact
│   ├── daily-log.ts             # Daily log write/read
│   ├── fts5-index.ts            # SQLite FTS5 indexing and search
│   ├── vector-search.ts         # Qdrant embeddings and search
│   ├── hybrid-search.ts         # RRF fusion of FTS5 + vector results
│   ├── compaction.ts            # Log compaction scheduler and logic
│   └── __tests__/
│       ├── persistent.test.ts
│       ├── fts5-index.test.ts
│       ├── vector-search.test.ts
│       ├── hybrid-search.test.ts
│       └── compaction.test.ts
├── router/
│   ├── types.ts                 # Router types (TaskClass, ModelTier, RoutingResult)
│   ├── classifier.ts            # Task classification (which tier?)
│   ├── router.ts                # Model dispatch with fallback chain
│   ├── prompt-cache.ts          # Prompt caching configuration
│   ├── cost-tracker-integration.ts  # Wire router to existing cost tracker
│   └── __tests__/
│       ├── classifier.test.ts
│       ├── router.test.ts
│       └── prompt-cache.test.ts
├── cost/                        # (existing from Phase 1)
│   ├── types.ts
│   ├── tracker.ts
│   └── reconcile.ts
├── hitl/                        # (existing from Phase 1)
│   ├── classify.ts
│   ├── enforce.ts
│   └── types.ts
└── safety/                      # (existing from Phase 1)
    ├── context-guard.ts
    └── types.ts
```

Additional config and data paths:
```
~/.openclaw/
├── memory/
│   ├── MEMORY.md                # (existing) Persistent agent memory
│   ├── index.db                 # (new) SQLite FTS5 search index
│   ├── config.yaml              # (existing) Memory configuration
│   ├── logs/
│   │   ├── 2026/02/28.md        # Daily logs
│   │   └── summaries/           # (new) Compacted weekly/monthly summaries
│   └── overflow/                # (new) Topic overflow files
│       ├── clients.md
│       ├── tools.md
│       └── projects.md
├── config/
│   ├── model-routing.yaml       # (new) Routing rules, tier definitions, cost rates
│   └── cost-limits.yaml         # (existing) Circuit breaker thresholds
└── data/
    ├── qdrant/                  # (existing) Qdrant persistent storage
    └── cost-tracker.db          # (existing) Cost tracking database
```

### Pattern 1: Memory Read/Write Lifecycle

**What:** MEMORY.md is read at session start, written to when persistent facts are learned, and compacted when it exceeds the token budget.
**When to use:** Every agent session.

```typescript
// Source: Project blueprint (04-Memory-and-RAG/memory-architecture.md)
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, dirname } from "path";

const MEMORY_PATH = join(process.env.HOME || "~", ".openclaw", "memory", "MEMORY.md");
const MAX_TOKENS = 4000;
const CHARS_PER_TOKEN = 4; // Conservative estimate

export interface MemoryEntry {
  key: string;
  value: string;
  category: "preference" | "fact" | "project" | "pattern" | "decision";
  confidence: "high" | "medium" | "low";
  source: string; // which session/action created this
  timestamp: string;
}

export function loadMemory(): string {
  if (!existsSync(MEMORY_PATH)) return "";
  return readFileSync(MEMORY_PATH, "utf-8");
}

export function estimateTokens(text: string): number {
  return Math.ceil(text.length / CHARS_PER_TOKEN);
}

export function shouldCompact(content: string): boolean {
  return estimateTokens(content) >= MAX_TOKENS;
}

export function appendToMemory(section: string, entry: string): void {
  let content = loadMemory();
  // Find the section and append, or create new section
  const sectionHeader = `## ${section}`;
  if (content.includes(sectionHeader)) {
    const idx = content.indexOf(sectionHeader);
    const nextSection = content.indexOf("\n## ", idx + sectionHeader.length);
    const insertPoint = nextSection === -1 ? content.length : nextSection;
    content = content.slice(0, insertPoint) + `- ${entry}\n` + content.slice(insertPoint);
  } else {
    content += `\n${sectionHeader}\n- ${entry}\n`;
  }
  writeFileSync(MEMORY_PATH, content, "utf-8");
}
```

### Pattern 2: FTS5 Index with better-sqlite3

**What:** SQLite FTS5 virtual table for keyword search over all memory content, with porter stemming and unicode support.
**When to use:** Every search query that includes specific names, terms, IDs, or technical keywords.

```typescript
// Source: better-sqlite3 docs + SQLite FTS5 documentation
import Database from "better-sqlite3";

const INDEX_DB_PATH = join(process.env.HOME || "~", ".openclaw", "memory", "index.db");

export function initFTS5Index(dbPath?: string): Database.Database {
  const db = new Database(dbPath || INDEX_DB_PATH);
  db.pragma("journal_mode = WAL");

  db.exec(`
    CREATE TABLE IF NOT EXISTS documents (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      path TEXT NOT NULL UNIQUE,
      content_hash TEXT NOT NULL,
      doc_type TEXT,
      updated_at TEXT DEFAULT (datetime('now')),
      token_count INTEGER
    );

    CREATE TABLE IF NOT EXISTS chunks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
      chunk_index INTEGER,
      content TEXT NOT NULL,
      token_count INTEGER,
      created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
      content,
      content='chunks',
      content_rowid='id',
      tokenize='porter unicode61'
    );

    -- Keep FTS5 in sync with chunks table
    CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
      INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
    END;

    CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
      INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
    END;

    CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
      INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
      INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
    END;
  `);

  return db;
}

export function searchFTS5(db: Database.Database, query: string, limit: number = 10) {
  // Escape FTS5 special characters
  const safeQuery = query.replace(/["\\'()*+\-:^{}~]/g, " ").trim();
  if (!safeQuery) return [];

  return db.prepare(`
    SELECT c.id, c.content, c.document_id, d.path, rank AS bm25_score
    FROM chunks_fts
    JOIN chunks c ON c.id = chunks_fts.rowid
    JOIN documents d ON d.id = c.document_id
    WHERE chunks_fts MATCH ?
    ORDER BY rank
    LIMIT ?
  `).all(safeQuery, limit);
}
```

### Pattern 3: Qdrant Vector Search

**What:** Embed queries and search the Qdrant collection for semantically similar content.
**When to use:** Conceptual queries, past decision lookups, "what do we know about X" queries.

```typescript
// Source: @qdrant/js-client-rest docs, ollama npm docs
import { QdrantClient } from "@qdrant/js-client-rest";
import { Ollama } from "ollama";

const COLLECTION_NAME = "openclaw-memory";
const EMBEDDING_DIM = 768;
const SIMILARITY_THRESHOLD = 0.7;

const qdrant = new QdrantClient({ url: "http://127.0.0.1:6333" });
const ollama = new Ollama({ host: "http://127.0.0.1:11434" });

export async function initCollection(): Promise<void> {
  const collections = await qdrant.getCollections();
  const exists = collections.collections.some(c => c.name === COLLECTION_NAME);
  if (!exists) {
    await qdrant.createCollection(COLLECTION_NAME, {
      vectors: { size: EMBEDDING_DIM, distance: "Cosine" },
    });
  }
}

export async function embed(text: string): Promise<number[]> {
  const response = await ollama.embed({
    model: "nomic-embed-text",
    input: text,
  });
  return response.embeddings[0];
}

export async function searchVector(
  query: string,
  limit: number = 10,
  threshold: number = SIMILARITY_THRESHOLD
) {
  const queryEmbedding = await embed(query);
  const results = await qdrant.search(COLLECTION_NAME, {
    vector: queryEmbedding,
    limit,
    score_threshold: threshold,
    with_payload: true,
  });
  return results;
}

export async function upsertChunk(
  id: number,
  text: string,
  metadata: Record<string, unknown>
): Promise<void> {
  const embedding = await embed(text);
  await qdrant.upsert(COLLECTION_NAME, {
    points: [{ id, vector: embedding, payload: { text, ...metadata } }],
  });
}
```

### Pattern 4: RRF Hybrid Search with Query-Adaptive Weights

**What:** Merge FTS5 keyword results and Qdrant vector results using Reciprocal Rank Fusion with weights that adapt based on query type.
**When to use:** Default search path -- every memory retrieval uses this.

```typescript
// Source: Project blueprint (04-Memory-and-RAG/hybrid-search.md)

interface SearchResult {
  id: number;
  content: string;
  path: string;
  rrf_score: number;
  sources: ("fts5" | "vector")[];
}

type QueryType = "exact" | "conceptual" | "mixed";

function classifyQuery(query: string): QueryType {
  // Exact: contains quoted strings, IDs, specific names, technical terms
  if (/["']/.test(query)) return "exact";
  if (/[A-Z]{2,}[-_]\d+/.test(query)) return "exact"; // e.g., MEMR-01, jitawzicdwgbhatvjblh
  if (/^(find|get|show|what is)\s/i.test(query)) return "mixed";
  // Conceptual: asks about topics, decisions, strategies
  if (/\b(how|why|what|strategy|decision|approach|pattern)\b/i.test(query)) return "conceptual";
  return "mixed";
}

function getWeights(queryType: QueryType): { vector: number; fts5: number } {
  switch (queryType) {
    case "exact": return { vector: 0.3, fts5: 0.7 };
    case "conceptual": return { vector: 0.7, fts5: 0.3 };
    case "mixed": return { vector: 0.6, fts5: 0.4 }; // default from config
  }
}

function reciprocalRankFusion(
  vectorResults: { id: number; score: number }[],
  fts5Results: { id: number; score: number }[],
  weights: { vector: number; fts5: number },
  k: number = 60
): Map<number, number> {
  const scores = new Map<number, number>();

  vectorResults.forEach((r, rank) => {
    const current = scores.get(r.id) || 0;
    scores.set(r.id, current + weights.vector * (1 / (k + rank + 1)));
  });

  fts5Results.forEach((r, rank) => {
    const current = scores.get(r.id) || 0;
    scores.set(r.id, current + weights.fts5 * (1 / (k + rank + 1)));
  });

  return scores;
}
```

### Pattern 5: Model Router with Fallback Chain

**What:** Classify task complexity and route to the cheapest capable model tier. On failure, escalate to the next tier.
**When to use:** Every LLM call the agent makes.

```typescript
// Source: Anthropic SDK docs, Ollama docs, project CONTEXT.md decisions

type ModelTier = "ollama" | "haiku" | "sonnet" | "opus";

interface RoutingResult {
  tier: ModelTier;
  model: string;
  reason: string;
  fallback_from?: ModelTier;
}

const TIER_CONFIG = {
  ollama: { model: "qwen3:14b", cost_per_mtok: 0 },
  haiku:  { model: "claude-haiku-4-5-20250929", cost_per_mtok: 1.0 },
  sonnet: { model: "claude-sonnet-4-5-20250929", cost_per_mtok: 3.0 },
  opus:   { model: "claude-opus-4-6-20250929", cost_per_mtok: 5.0 },
} as const;

const FALLBACK_ORDER: ModelTier[] = ["ollama", "haiku", "sonnet", "opus"];

function classifyTask(task: string, context?: string): ModelTier {
  const lower = task.toLowerCase();

  // Tier 1: Ollama (classification, formatting, simple extraction)
  if (/\b(classify|categorize|format|extract|parse|label|tag)\b/.test(lower)) return "ollama";

  // Tier 4: Opus (client-facing, proposals, important communications)
  if (/\b(client|proposal|presentation|pitch|outreach|external)\b/.test(lower)) return "opus";

  // Tier 3: Sonnet (reasoning, analysis, complex decisions)
  if (/\b(analyze|reason|compare|evaluate|strategy|decide|complex)\b/.test(lower)) return "sonnet";

  // Tier 2: Haiku (standard tasks -- default)
  return "haiku";
}
```

### Pattern 6: Prompt Caching on System Prompts

**What:** Enable prompt caching for system prompts that are sent with every API call, reducing input token costs by 90% on cache hits.
**When to use:** Every Claude API call.

```typescript
// Source: Anthropic prompt caching docs (platform.claude.com)
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic();

// Automatic caching -- simplest approach
// System prompt + MEMORY.md content gets cached automatically
async function callWithCaching(
  model: string,
  systemPrompt: string,
  messages: Anthropic.MessageParam[]
) {
  const response = await client.messages.create({
    model,
    max_tokens: 4096,
    cache_control: { type: "ephemeral" }, // automatic caching
    system: systemPrompt,
    messages,
  });

  // Track cache performance
  const usage = response.usage;
  console.error(JSON.stringify({
    level: "INFO",
    component: "prompt-cache",
    cache_read_tokens: usage.cache_read_input_tokens ?? 0,
    cache_creation_tokens: usage.cache_creation_input_tokens ?? 0,
    uncached_tokens: usage.input_tokens,
    output_tokens: usage.output_tokens,
  }));

  return response;
}
```

### Anti-Patterns to Avoid

- **Mixing embedding models in the same Qdrant collection:** nomic-embed-text produces 768-dim vectors. If you switch models, you must re-embed everything. Record the model name in collection metadata.
- **Storing embeddings in SQLite instead of Qdrant:** The blueprint mentions sqlite-vec, but Qdrant is already running and provides better HNSW indexing, payload filtering, and collection management. Use SQLite for FTS5 only, Qdrant for vectors.
- **Synchronous embedding calls in the search hot path:** Embedding via Ollama takes 5-20ms. For batch indexing, this adds up. Use async batch processing for indexing; single-call latency is acceptable for queries.
- **Compacting MEMORY.md without archiving the original:** Always write the pre-compaction version to `exports/MEMORY-YYYY-MM-DD.md` before overwriting.
- **Caching prompts shorter than the minimum:** Haiku/Sonnet require 1024+ tokens for caching; Opus requires 4096+. System prompts below these thresholds will silently skip caching with no error. Pad system prompts with MEMORY.md content to exceed minimums.
- **Sending DELETE operations through the model router without HITL check:** The router must respect the HITL tier system from Phase 1. Classify the action tier before routing the model call.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector similarity search | Custom cosine distance in SQLite | Qdrant collection with HNSW index | Qdrant handles indexing, filtering, pagination, and scales to millions of vectors; custom SQLite vector search is O(n) |
| Full-text search | Custom inverted index | SQLite FTS5 via better-sqlite3 | FTS5 handles tokenization, stemming, BM25 ranking, and sync triggers; building an inverted index is weeks of work |
| Embedding generation | Custom transformer model | Ollama nomic-embed-text | Model is already pulled and verified at 768 dimensions; embedding endpoint is a single HTTP call |
| Claude API with retries | Custom HTTP client with retry logic | @anthropic-ai/sdk | SDK handles retries, rate limiting, streaming, and TypeScript types automatically |
| Cron scheduling | setInterval/setTimeout chains | node-cron | Handles cron expression parsing, timezone awareness, and proper cleanup; setTimeout chains drift and leak |
| Token counting | Character-based math only | tiktoken (when precision matters) | BPE tokenization varies by model; character estimates diverge 10-20% on technical content |

**Key insight:** The memory system's value comes from the integration layer (how write/read/search/compact work together), not from the individual components. Every component has a mature, well-tested library. The custom code is the orchestration: when to search, what to persist, how to adapt weights, when to compact.

## Common Pitfalls

### Pitfall 1: FTS5 Content Sync Table Corruption

**What goes wrong:** The FTS5 `content='chunks'` syntax creates a "contentless" external-content FTS5 table that mirrors the `chunks` table. If you insert/update/delete chunks without the triggers firing, the FTS5 index becomes inconsistent.
**Why it happens:** Bulk imports using `.import`, direct SQL bypassing triggers, or forgetting `ON DELETE CASCADE`.
**How to avoid:** Always use the `chunks` table for mutations (never write directly to `chunks_fts`). If corruption occurs, rebuild with `INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')`.
**Warning signs:** FTS5 queries return results that don't exist in chunks table, or miss results that do exist.

### Pitfall 2: Qdrant Point ID Conflicts

**What goes wrong:** Qdrant uses point IDs to deduplicate. If you upsert a point with an ID that already exists, it silently replaces the existing point.
**Why it happens:** Using auto-increment IDs that reset, or using the same ID scheme across different document types.
**How to avoid:** Use a deterministic ID scheme: hash the document path + chunk index. Or use UUIDs. Record the mapping in the SQLite documents table.
**Warning signs:** Vector search returns fewer results than expected; recently indexed content is missing.

### Pitfall 3: Ollama Cold Start Latency

**What goes wrong:** First Ollama call after model unload takes 5-15 seconds to load qwen3:14b (9.3 GB) into memory. Subsequent calls are fast (<1s).
**Why it happens:** Ollama unloads models after idle timeout (default 5 minutes). The 14B parameter model is large.
**How to avoid:** Set `OLLAMA_KEEP_ALIVE` environment variable to extend the keep-alive time (e.g., `24h` for always-loaded). For the router, detect cold start latency and fall back to Haiku if Ollama takes >3 seconds.
**Warning signs:** Intermittent slow responses from the Ollama tier; consistent fast responses from Claude tiers.

### Pitfall 4: Prompt Cache Misses Due to Dynamic System Prompts

**What goes wrong:** Cache hit rate is near zero because the system prompt changes slightly on every call (e.g., current timestamp, session ID embedded in the prompt).
**Why it happens:** Any change to the cached prefix invalidates the cache. Dynamic content at the start of the system prompt prevents caching of everything after it.
**How to avoid:** Structure system prompts with static content first (personality, rules, MEMORY.md), then dynamic content (current time, session context) after the cache breakpoint. Use explicit cache breakpoints on the static portion.
**Warning signs:** `cache_read_input_tokens` is consistently 0 in API responses; `cache_creation_input_tokens` is high on every call.

### Pitfall 5: MEMORY.md Compaction Loses Nuance

**What goes wrong:** LLM-based compaction summarizes away important details -- "Client prefers email over phone for non-urgent items" becomes "Client communication preferences noted."
**Why it happens:** Generic summarization prompts don't emphasize preserving actionable details.
**How to avoid:** Use a specific compaction prompt: "Preserve all actionable specifics: names, IDs, preferences with details, decision rationale. Remove only truly redundant entries. Target: under 3,000 tokens." Always archive the original before compacting.
**Warning signs:** Agent asks the user about something that was previously in MEMORY.md.

### Pitfall 6: Query-Adaptive Weight Classification Errors

**What goes wrong:** A query like "find John Smith's contact" gets classified as conceptual (high vector weight) when it should be exact (high FTS5 weight), leading to irrelevant semantic matches instead of the exact contact record.
**Why it happens:** Simple keyword-based classification misses context. Proper names and specific identifiers should bias toward FTS5.
**How to avoid:** Start with conservative classification (default to mixed/balanced weights). Log classification decisions and their outcomes. Tune rules based on observed failures. The user's decision to "classify the query type first" implies this should be visible and correctable.
**Warning signs:** Exact name searches return conceptually related but wrong results.

## Code Examples

### Complete Memory Write Flow

```typescript
// Source: Project blueprint + Phase 2 architecture
import { loadMemory, appendToMemory, shouldCompact, estimateTokens } from "./persistent.js";
import { indexDocument } from "./fts5-index.js";
import { upsertChunk, embed } from "./vector-search.js";

export async function remember(
  key: string,
  value: string,
  category: MemoryEntry["category"],
  confidence: MemoryEntry["confidence"]
): Promise<void> {
  // 1. Append to MEMORY.md
  appendToMemory(categoryToSection(category), `${key}: ${value}`);

  // 2. Index in FTS5
  const db = initFTS5Index();
  indexDocument(db, {
    path: "MEMORY.md",
    content: `${key}: ${value}`,
    doc_type: "memory",
  });

  // 3. Embed and store in Qdrant
  await upsertChunk(
    hashId("MEMORY.md", key),
    `${key}: ${value}`,
    { category, confidence, source: "memory", key }
  );

  // 4. Check if compaction needed
  const content = loadMemory();
  if (shouldCompact(content)) {
    console.error(JSON.stringify({
      level: "INFO",
      component: "memory",
      action: "COMPACT_TRIGGERED",
      tokens: estimateTokens(content),
      threshold: 4000,
    }));
    // Compaction runs asynchronously -- archive + LLM summarize
  }
}
```

### Daily Log Entry

```typescript
// Source: Project blueprint (04-Memory-and-RAG/memory-architecture.md)
import { existsSync, mkdirSync, appendFileSync } from "fs";
import { join } from "path";

const LOGS_DIR = join(process.env.HOME || "~", ".openclaw", "memory", "logs");

export function logEntry(entry: {
  type: "action" | "decision" | "error" | "interaction";
  summary: string;
  details?: string;
}): void {
  const now = new Date();
  const year = now.getFullYear().toString();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const time = now.toTimeString().slice(0, 5);

  const logDir = join(LOGS_DIR, year, month);
  if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });

  const logFile = join(logDir, `${day}.md`);
  const line = `- **${time}** [${entry.type}] ${entry.summary}${
    entry.details ? `\n  ${entry.details}` : ""
  }\n`;

  appendFileSync(logFile, line, "utf-8");
}
```

### Model Router Dispatch

```typescript
// Source: Anthropic SDK docs, Ollama npm docs
import Anthropic from "@anthropic-ai/sdk";
import { Ollama } from "ollama";
import { recordUsage } from "../cost/tracker.js";

const anthropic = new Anthropic();
const ollamaClient = new Ollama({ host: "http://127.0.0.1:11434" });

export async function routeAndCall(
  task: string,
  messages: { role: string; content: string }[],
  systemPrompt: string,
  sessionId: string
): Promise<{ content: string; tier: ModelTier; cost: number }> {
  const tier = classifyTask(task);
  const tierIndex = FALLBACK_ORDER.indexOf(tier);

  for (let i = tierIndex; i < FALLBACK_ORDER.length; i++) {
    const currentTier = FALLBACK_ORDER[i];
    try {
      const result = await callTier(currentTier, messages, systemPrompt);

      // Record usage for cost tracking
      recordUsage({
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        model: TIER_CONFIG[currentTier].model,
        input_tokens: result.inputTokens,
        output_tokens: result.outputTokens,
        cost_usd: result.cost,
        tool_calls: 0,
      });

      if (i > tierIndex) {
        // Fallback occurred -- log it
        console.error(JSON.stringify({
          level: "WARN",
          component: "model-router",
          action: "FALLBACK",
          original_tier: tier,
          actual_tier: currentTier,
          reason: "previous_tier_unavailable",
        }));
      }

      return { content: result.content, tier: currentTier, cost: result.cost };
    } catch (err) {
      console.error(JSON.stringify({
        level: "ERROR",
        component: "model-router",
        action: "TIER_FAILED",
        tier: currentTier,
        error: (err as Error).message,
      }));
      // Continue to next tier in fallback chain
    }
  }

  throw new Error("All model tiers exhausted -- no response possible");
}

async function callTier(
  tier: ModelTier,
  messages: { role: string; content: string }[],
  systemPrompt: string
): Promise<{ content: string; inputTokens: number; outputTokens: number; cost: number }> {
  if (tier === "ollama") {
    const response = await ollamaClient.chat({
      model: TIER_CONFIG.ollama.model,
      messages: [
        { role: "system", content: systemPrompt },
        ...messages,
      ],
    });
    return {
      content: response.message.content,
      inputTokens: response.prompt_eval_count ?? 0,
      outputTokens: response.eval_count ?? 0,
      cost: 0, // Ollama is free
    };
  }

  // Claude tiers -- with prompt caching
  const config = TIER_CONFIG[tier];
  const response = await anthropic.messages.create({
    model: config.model,
    max_tokens: 4096,
    cache_control: { type: "ephemeral" },
    system: systemPrompt,
    messages: messages as Anthropic.MessageParam[],
  });

  const inputTokens = (response.usage.cache_read_input_tokens ?? 0)
    + (response.usage.cache_creation_input_tokens ?? 0)
    + response.usage.input_tokens;
  const outputTokens = response.usage.output_tokens;

  // Calculate cost using actual token breakdown
  const cacheReadCost = (response.usage.cache_read_input_tokens ?? 0) * config.cost_per_mtok * 0.1 / 1_000_000;
  const cacheWriteCost = (response.usage.cache_creation_input_tokens ?? 0) * config.cost_per_mtok * 1.25 / 1_000_000;
  const uncachedCost = response.usage.input_tokens * config.cost_per_mtok / 1_000_000;
  const outputCost = outputTokens * (config.cost_per_mtok * 5) / 1_000_000; // Output is 5x input for Claude
  const totalCost = cacheReadCost + cacheWriteCost + uncachedCost + outputCost;

  const contentBlock = response.content[0];
  const content = contentBlock.type === "text" ? contentBlock.text : "";

  return { content, inputTokens, outputTokens, cost: totalCost };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `cache_control` on content blocks | Automatic caching with top-level `cache_control` field | 2026 | Single field enables automatic cache management for growing conversations |
| `anthropic-beta: prompt-caching-2024-07-31` header required | Prompt caching is GA -- no beta header needed | Late 2025 | Simpler implementation; no beta flag management |
| sqlite-vss for vector search in SQLite | sqlite-vec (successor) | 2025 | sqlite-vec is more stable but Qdrant is still superior for production vector search |
| Ollama `embeddings` endpoint (singular text input) | Ollama `embed` endpoint (batch input support) | 2025 | ollama npm package uses `embed()` with `input` field instead of deprecated `embeddings()` |
| Claude 3.5 Sonnet as primary reasoning model | Claude Sonnet 4.5 / 4.6 | 2025-2026 | Improved reasoning, same pricing tier |
| Per-block explicit caching only | Automatic + explicit caching can combine | 2026 | Automatic caching uses 1 of 4 available breakpoint slots alongside explicit ones |

**Deprecated/outdated:**
- `ollama.embeddings()` method: Replaced by `ollama.embed()` with `input` parameter. The old method accepted `prompt` (singular); new method accepts `input` (string or array).
- `anthropic-beta: prompt-caching-2024-07-31` header: Prompt caching is now GA. No beta header needed.
- sqlite-vss: Replaced by sqlite-vec as the SQLite vector extension. Neither is needed here since Qdrant is the vector store.

## Open Questions

1. **Exact Anthropic model IDs for current Claude versions**
   - What we know: The models are Claude Haiku 4.5, Sonnet 4.5/4.6, and Opus 4.6. The SDK accepts model strings.
   - What's unclear: The exact model ID strings (e.g., `claude-haiku-4-5-20250929` vs `claude-haiku-4-5-latest`) may have updated since training data cutoff.
   - Recommendation: Use the Anthropic SDK's built-in model constants or check the API docs for current model IDs during implementation. The SDK will error with a clear message if the model ID is wrong.

2. **Ollama keep-alive behavior on Mac Mini M4 Pro**
   - What we know: qwen3:14b is 9.3 GB. The M4 Pro has 24 GB unified memory. Ollama unloads after idle timeout.
   - What's unclear: Whether keeping qwen3:14b permanently loaded impacts the Mac Mini's performance for other tasks (Docker containers, Qdrant, etc.).
   - Recommendation: Start with `OLLAMA_KEEP_ALIVE=1h`. Monitor memory pressure via `vm_stat` or Activity Monitor. If memory pressure is fine, extend to `24h`.

3. **MEMORY.md overflow file structure**
   - What we know: User wants topic overflow files (`clients.md`, `tools.md`). MEMORY.md acts as an index.
   - What's unclear: The exact trigger for overflowing to a separate file vs keeping in MEMORY.md. Is it per-topic token budgets, or total MEMORY.md size?
   - Recommendation: Overflow when MEMORY.md compaction moves content to a topic file. MEMORY.md keeps a 1-line summary reference: "## Clients\nSee overflow/clients.md for details." The overflow files have no token budget -- they are searched via FTS5/Qdrant, not loaded into every session.

4. **Cost rate accuracy for Opus 4.6**
   - What we know: Prompt caching docs show Opus 4.6 at $5/MTok input, $25/MTok output. Opus 4.1 and 4 are at $15/MTok input.
   - What's unclear: Whether Opus 4.6 pricing is confirmed at $5/MTok input (same as 4.5) or will change.
   - Recommendation: Configure rates in `model-routing.yaml` so they can be updated without code changes. Check the Anthropic pricing page during implementation.

## Sources

### Primary (HIGH confidence)
- [Anthropic Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- Automatic caching, explicit breakpoints, pricing table, minimum token requirements, TypeScript examples
- [@qdrant/js-client-rest on npm](https://www.npmjs.com/package/@qdrant/js-client-rest) -- v1.17.0, TypeScript client for Qdrant REST API
- [Qdrant JavaScript SDK GitHub](https://github.com/qdrant/qdrant-js) -- Collection creation, upsert, search with filters
- [Ollama JavaScript library GitHub](https://github.com/ollama/ollama-js) -- ollama npm v0.6.3, embed() method, custom host, TypeScript types
- [@anthropic-ai/sdk on npm](https://www.npmjs.com/package/@anthropic-ai/sdk) -- v0.78.0, messages.create, prompt caching support
- [SQLite FTS5 documentation](https://www.sqlite.org/fts5.html) -- porter unicode61 tokenizer, BM25 ranking, content-sync tables
- Project blueprint: `04-Memory-and-RAG/memory-architecture.md` -- File-first philosophy, MEMORY.md lifecycle, SQLite schema
- Project blueprint: `04-Memory-and-RAG/hybrid-search.md` -- RRF implementation, query-adaptive weights, FTS5 query syntax
- Project blueprint: `04-Memory-and-RAG/embedding-models.md` -- nomic-embed-text recommendation, 768-dim, embedding consistency rules

### Secondary (MEDIUM confidence)
- Anthropic prompt caching pricing multipliers: 1.25x for cache writes, 0.1x for cache reads -- confirmed by official docs
- better-sqlite3 FTS5 compiled-in support: Verified by Phase 1 usage; no extension loading needed
- Ollama embed() response format: `{ embeddings: [number[]] }` -- needs verification during implementation (API may use `embedding` singular)

### Tertiary (LOW confidence)
- Exact Claude model ID strings: May have updated since training cutoff; verify during implementation
- Ollama KEEP_ALIVE memory impact on M4 Pro with Docker stack: Needs empirical testing
- node-cron v3.0.3 ESM compatibility: Needs verification; may require `import { schedule } from 'node-cron'`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries verified via npm (exact versions), Qdrant and Ollama confirmed running locally, better-sqlite3 already in use
- Architecture: HIGH -- Patterns derived from project blueprint docs and official library documentation; integration with existing Phase 1 codebase verified
- Pitfalls: HIGH -- FTS5 sync, Qdrant IDs, Ollama cold start, and prompt cache miss scenarios are well-documented; compaction risks are common in summarization systems
- Model routing: MEDIUM -- Task classification rules are heuristic-based; will need tuning based on real usage patterns
- Cost calculations: MEDIUM -- Pricing multipliers confirmed from Anthropic docs but Opus 4.6 pricing needs verification

**Research date:** 2026-02-28
**Valid until:** 2026-03-14 (14 days -- Anthropic SDK and pricing may update; Ollama versions move quickly)

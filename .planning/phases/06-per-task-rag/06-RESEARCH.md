# Phase 6: Per-Task RAG - Research

**Researched:** 2026-03-02
**Domain:** Per-task vector collections, outcome indexing, pre-task recall, write gates with validation lifecycle, client knowledge RAG
**Confidence:** HIGH

## Summary

Phase 6 transforms the agent from one that executes tasks identically each time into one that measurably improves. The core mechanism: every skill execution produces a structured outcome record (errors, token usage, patterns, operator corrections) indexed into a task-type-specific Qdrant collection. Before executing a repeated task, the agent queries its per-task collection for past mistakes and successful patterns, injecting relevant history into the working context.

The existing infrastructure from Phase 2 provides nearly everything needed: Qdrant v1.17.0 is running at 127.0.0.1:6333 with the `@qdrant/js-client-rest` TypeScript client, `ollama` npm package generates 768-dim embeddings via nomic-embed-text, and the hybrid search system (FTS5 + Qdrant + RRF) handles semantic+keyword retrieval. The existing `openclaw-memory` collection holds general memory. Phase 6 creates additional task-specific collections alongside it, plus a `client-knowledge` collection for cross-workflow client context.

The key design choice is between many separate Qdrant collections vs. a single collection with payload-based multitenancy. Qdrant's official guidance recommends payload partitioning for >10 tenants to avoid per-collection overhead. With only 5-7 task types, separate collections are viable and provide the "isolated, queryable independently" isolation required by PRAG-01. The collection count is small enough (under 10) to avoid performance degradation.

Write gates (PRAG-04) are implemented as a `status` field on each Qdrant point's payload: new entries start as `"pending"` and graduate to `"confirmed"` after operator validation or 7-day no-complaint TTL expiry. A nightly job scans pending entries older than 7 days and promotes them. The agent weights confirmed entries higher than pending ones during pre-task recall.

**Primary recommendation:** Create one Qdrant collection per task type (5-7 collections total) with standardized payload schemas. Build a thin `outcome-indexer` module that all skills call after execution, and a `pre-task-recall` module that all skills call before execution. Write gates use payload status + indexed datetime field for efficient TTL queries. Client knowledge uses a dedicated collection with contactId-indexed payloads.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PRAG-01 | Separate Qdrant collection per task type (email-triage, proposal-gen, form-gen, lead-enrich, check-in, etc.) | Qdrant supports multiple collections with independent vector configs; 5-7 collections is well within the safe range (Qdrant guidance warns against 100+ collections, not single digits); @qdrant/js-client-rest v1.17.0 provides createCollection, getCollections, search per collection; existing vector-search.ts provides the initCollection pattern to extend |
| PRAG-02 | Every task execution indexes its outcome -- errors, token usage, successful patterns, operator corrections | Outcome record structure with standardized payload schema (task_type, input_summary, output_summary, success, error_type, token_usage, model_tier, operator_correction, timestamp); Qdrant upsert with deterministic IDs; embedding the outcome narrative via nomic-embed-text for semantic retrieval |
| PRAG-03 | Before executing a repeated task, agent queries its task-specific RAG for past mistakes and successful approaches | Pre-task recall module: embed the current task context, search the task-specific collection (limit 3-5, threshold 0.6), inject retrieved outcomes into the system prompt as "lessons learned"; query-adaptive weights from Phase 2 hybrid search apply here |
| PRAG-04 | RAG write gates -- outcomes enter as `pending` status, graduate to `confirmed` only after operator validation or 7-day no-complaint window | Payload field `status: "pending" | "confirmed" | "rejected"`; payload field `indexed_at` with datetime type; payload index on `status` (keyword) and `indexed_at` (datetime) for efficient filtering; nightly cron job (extend node-cron from Phase 2) promotes pending entries older than 7 days; operator can confirm/reject via Telegram inline buttons; pre-task recall weights confirmed 2x over pending |
| PRAG-05 | Client knowledge indexed and retrievable across all workflows -- past interactions, preferences, project history | Dedicated `client-knowledge` collection; payload indexed by `contact_id` (keyword) for per-client filtering; cross-workflow write: email triage, proposals, check-ins, and todos all contribute client knowledge entries; "what do we know about [client]?" query searches this collection with contact_id filter or semantic open search |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @qdrant/js-client-rest | 1.17.0 | Per-task Qdrant collections, upsert outcomes, search recall | Already installed from Phase 2; versioned to match Qdrant engine v1.17.0; TypeScript-native |
| ollama | 0.6.3 | Embedding outcome narratives via nomic-embed-text (768-dim) | Already installed from Phase 2; embed() method with batch support |
| better-sqlite3 | 12.6.2 | FTS5 indexing of outcomes for keyword search, write gate metadata tracking | Already installed from Phase 1; synchronous API for pre-call gate checks |
| node-cron | 3.0.3 | Scheduling nightly write gate promotion (pending -> confirmed after 7 days) | Already installed from Phase 2; used for log compaction on same schedule pattern |
| grammy | (installed) | Telegram inline buttons for operator validation of pending outcomes | Already installed from Phase 3; callback pattern established for HITL approval |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yaml | 2.8.2 | Configuration file parsing for task type definitions | Already installed; used for all config loading |
| tsx | 4.21.0 | TypeScript execution | Running all TypeScript modules directly |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Separate Qdrant collections per task | Single collection with payload partition (group_id multitenancy) | Single collection reduces Qdrant overhead but loses true isolation; PRAG-01 specifically requires "isolated, queryable independently"; with only 5-7 task types, separate collections have negligible overhead |
| Qdrant for write gate status tracking | SQLite table for gate metadata | SQLite would be faster for status queries but requires syncing two stores; keeping status in Qdrant payload means search and status live together; indexed keyword field on `status` gives sub-ms filtering |
| nomic-embed-text for outcome embeddings | Voyage-3.5-lite API | API embeddings would be higher quality but add cost ($0.02/1M tokens), network dependency, and latency; outcome records are short (<500 tokens each) so nomic quality is sufficient; keeps the system fully local |
| Qdrant for client knowledge | SQLite JSON store | Qdrant provides vector similarity for "what do we know about [client]?" conceptual queries; SQLite would only support keyword lookups; client knowledge benefits from semantic search |

### Installation

```bash
# No new packages needed -- all dependencies installed in Phases 1-3
# Verify existing packages:
cd ~/.openclaw && node -e "
const p = require('./package.json');
['@qdrant/js-client-rest', 'ollama', 'better-sqlite3', 'node-cron', 'grammy', 'yaml'].forEach(d => {
  console.log(d, p.dependencies[d] || p.devDependencies[d] || 'MISSING');
});
"
```

## Architecture Patterns

### Recommended Project Structure

```
~/.openclaw/src/
├── task-rag/
│   ├── types.ts                    # OutcomeRecord, TaskType, WriteGateStatus, ClientKnowledge
│   ├── collection-manager.ts       # Create/verify per-task Qdrant collections
│   ├── outcome-indexer.ts          # Index execution outcomes into task-specific collection
│   ├── pre-task-recall.ts          # Query past outcomes before execution
│   ├── write-gates.ts              # Pending->confirmed lifecycle, promotion cron, operator validation
│   ├── client-knowledge.ts         # Cross-workflow client knowledge indexing and retrieval
│   └── __tests__/
│       ├── collection-manager.test.ts
│       ├── outcome-indexer.test.ts
│       ├── pre-task-recall.test.ts
│       ├── write-gates.test.ts
│       └── client-knowledge.test.ts
├── memory/                         # (existing from Phase 2)
│   ├── vector-search.ts            # Re-used: embed(), Qdrant client instance
│   ├── hybrid-search.ts            # Re-used: hybridSearch() for client knowledge
│   └── fts5-index.ts               # Extended: outcome FTS5 indexing
├── router/                         # (existing from Phase 2)
│   └── router.ts                   # Extended: inject pre-task recall into system prompt
└── ...existing modules...
```

Config additions:
```
~/.openclaw/config/
├── task-rag.yaml                   # Task type definitions, collection names, write gate settings
└── model-routing.yaml              # (existing) -- unchanged
```

### Pattern 1: Per-Task Collection Lifecycle

**What:** Each task type gets its own Qdrant collection with standardized vector config but task-specific payload indexing.
**When to use:** At system initialization and when a new task type is registered.

```typescript
// Source: Qdrant JS client docs + Phase 2 vector-search.ts pattern
import { QdrantClient } from "@qdrant/js-client-rest";

const EMBEDDING_DIM = 768;
const qdrant = new QdrantClient({ url: "http://127.0.0.1:6333" });

// Task types map to collection names
const TASK_COLLECTIONS: Record<string, string> = {
  "email-triage": "task-email-triage",
  "proposal-gen": "task-proposal-gen",
  "form-gen": "task-form-gen",
  "lead-enrich": "task-lead-enrich",
  "check-in": "task-check-in",
};

async function ensureTaskCollection(taskType: string): Promise<void> {
  const collectionName = TASK_COLLECTIONS[taskType];
  if (!collectionName) throw new Error(`Unknown task type: ${taskType}`);

  const collections = await qdrant.getCollections();
  const exists = collections.collections.some(c => c.name === collectionName);

  if (!exists) {
    await qdrant.createCollection(collectionName, {
      vectors: { size: EMBEDDING_DIM, distance: "Cosine" },
    });

    // Index payload fields for efficient filtering
    await qdrant.createPayloadIndex(collectionName, {
      field_name: "status",
      field_schema: "keyword",
    });
    await qdrant.createPayloadIndex(collectionName, {
      field_name: "indexed_at",
      field_schema: "datetime",
    });
    await qdrant.createPayloadIndex(collectionName, {
      field_name: "success",
      field_schema: "bool",
    });
  }
}

async function ensureAllCollections(): Promise<void> {
  for (const taskType of Object.keys(TASK_COLLECTIONS)) {
    await ensureTaskCollection(taskType);
  }
  // Also ensure client-knowledge collection
  await ensureClientKnowledgeCollection();
}
```

### Pattern 2: Outcome Record Indexing

**What:** After every skill execution, produce a structured outcome record and index it into the appropriate task-type collection.
**When to use:** Called by every skill's post-execution hook.

```typescript
// Source: Project architecture + Qdrant upsert pattern from Phase 2
import { embed } from "../memory/vector-search.js";

interface OutcomeRecord {
  task_type: string;
  input_summary: string;       // What was the task about (e.g., "Triage 15 emails from inbox")
  output_summary: string;      // What was produced (e.g., "3 urgent, 8 routine, 4 archived")
  success: boolean;
  error_type?: string;         // "timeout", "api_failure", "wrong_output", "hallucination"
  error_message?: string;
  token_usage: { input: number; output: number; cost_usd: number };
  model_tier: string;          // "ollama", "haiku", "sonnet", "opus"
  operator_correction?: string; // If operator corrected the output, what was the correction
  patterns_observed?: string;   // Lessons learned from this execution
  contact_id?: string;         // If task was client-related
  session_id: string;
  timestamp: string;
}

async function indexOutcome(outcome: OutcomeRecord): Promise<number> {
  const collectionName = TASK_COLLECTIONS[outcome.task_type];
  if (!collectionName) throw new Error(`Unknown task type: ${outcome.task_type}`);

  // Build narrative for embedding
  const narrative = buildOutcomeNarrative(outcome);
  const embedding = await embed(narrative);

  // Deterministic ID from session + timestamp hash
  const pointId = deterministicId(outcome.session_id, outcome.timestamp);

  await qdrant.upsert(collectionName, {
    points: [{
      id: pointId,
      vector: embedding,
      payload: {
        ...outcome,
        status: "pending",         // Write gate: starts as pending
        indexed_at: new Date().toISOString(),
        narrative,                 // Store for debugging
      },
    }],
  });

  return pointId;
}

function buildOutcomeNarrative(outcome: OutcomeRecord): string {
  const parts = [
    `Task: ${outcome.task_type}`,
    `Input: ${outcome.input_summary}`,
    `Result: ${outcome.success ? "SUCCESS" : "FAILURE"}`,
  ];
  if (!outcome.success && outcome.error_type) {
    parts.push(`Error: ${outcome.error_type} - ${outcome.error_message}`);
  }
  parts.push(`Output: ${outcome.output_summary}`);
  if (outcome.operator_correction) {
    parts.push(`Correction: ${outcome.operator_correction}`);
  }
  if (outcome.patterns_observed) {
    parts.push(`Pattern: ${outcome.patterns_observed}`);
  }
  return parts.join(". ");
}
```

### Pattern 3: Pre-Task Recall

**What:** Before executing a task, query the task-specific collection for relevant past outcomes to inject as context.
**When to use:** At the start of every skill execution.

```typescript
// Source: Phase 2 hybrid-search.ts pattern + Qdrant search with filter

interface RecallResult {
  outcomes: OutcomeRecord[];
  lessons: string;              // Formatted for injection into system prompt
  recall_count: number;
}

async function recallForTask(
  taskType: string,
  currentContext: string,       // Description of the current task
  limit: number = 5,
  threshold: number = 0.6,
): Promise<RecallResult> {
  const collectionName = TASK_COLLECTIONS[taskType];
  if (!collectionName) return { outcomes: [], lessons: "", recall_count: 0 };

  const queryEmbedding = await embed(currentContext);

  // Search with status weighting: confirmed results scored higher
  const results = await qdrant.search(collectionName, {
    vector: queryEmbedding,
    limit: limit * 2,  // Fetch extra for post-filter scoring
    score_threshold: threshold,
    with_payload: true,
    filter: {
      should: [
        { key: "status", match: { value: "confirmed" } },
        { key: "status", match: { value: "pending" } },
      ],
    },
  });

  // Weight confirmed 2x over pending by boosting their scores
  const scored = results.map(r => ({
    ...r,
    adjusted_score: r.score * (r.payload?.status === "confirmed" ? 1.0 : 0.5),
  }));
  scored.sort((a, b) => b.adjusted_score - a.adjusted_score);

  const topResults = scored.slice(0, limit);
  const outcomes = topResults.map(r => r.payload as unknown as OutcomeRecord);

  // Format lessons for system prompt injection
  const lessons = formatLessons(outcomes, taskType);

  return { outcomes, lessons, recall_count: topResults.length };
}

function formatLessons(outcomes: OutcomeRecord[], taskType: string): string {
  if (outcomes.length === 0) return "";

  const lines = [`## Past ${taskType} Outcomes (${outcomes.length} relevant)`];

  for (const o of outcomes) {
    if (!o.success && o.error_type) {
      lines.push(`- AVOID: ${o.error_type} when handling "${o.input_summary}" -- ${o.error_message}`);
    }
    if (o.operator_correction) {
      lines.push(`- CORRECTION: Operator changed output for "${o.input_summary}" -- ${o.operator_correction}`);
    }
    if (o.patterns_observed) {
      lines.push(`- LEARNED: ${o.patterns_observed}`);
    }
    if (o.success && !o.operator_correction) {
      lines.push(`- SUCCESS PATTERN: "${o.input_summary}" -> ${o.output_summary}`);
    }
  }

  return lines.join("\n");
}
```

### Pattern 4: Write Gates with TTL Promotion

**What:** New outcomes enter as "pending" and graduate to "confirmed" after operator validation or 7-day no-complaint expiry.
**When to use:** Nightly cron job + operator Telegram callbacks.

```typescript
// Source: Phase 2 compaction.ts cron pattern + Phase 3 approval callback pattern

async function promotePendingEntries(): Promise<number> {
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  let promoted = 0;

  for (const collectionName of Object.values(TASK_COLLECTIONS)) {
    // Find pending entries older than 7 days
    const points = await qdrant.scroll(collectionName, {
      filter: {
        must: [
          { key: "status", match: { value: "pending" } },
          { key: "indexed_at", range: { lt: sevenDaysAgo } },
        ],
      },
      with_payload: true,
      limit: 100,
    });

    // Promote each to confirmed
    for (const point of points.points) {
      await qdrant.setPayload(collectionName, {
        payload: { status: "confirmed" },
        points: [point.id],
      });
      promoted++;
    }
  }

  // Also promote in client-knowledge collection
  // ... same pattern ...

  return promoted;
}

// Operator validation via Telegram -- extend existing callback pattern
async function operatorValidateOutcome(
  pointId: number,
  collectionName: string,
  decision: "confirm" | "reject"
): Promise<void> {
  const newStatus = decision === "confirm" ? "confirmed" : "rejected";
  await qdrant.setPayload(collectionName, {
    payload: { status: newStatus, validated_by: "operator", validated_at: new Date().toISOString() },
    points: [pointId],
  });
}
```

### Pattern 5: Client Knowledge Collection

**What:** A dedicated collection for client-specific knowledge that any workflow can write to and query.
**When to use:** After any client interaction across email, proposals, check-ins, todos.

```typescript
// Source: PRAG-05 + existing multi-sector RAG pattern from 04-Memory-and-RAG

const CLIENT_KNOWLEDGE_COLLECTION = "client-knowledge";

async function ensureClientKnowledgeCollection(): Promise<void> {
  const collections = await qdrant.getCollections();
  const exists = collections.collections.some(c => c.name === CLIENT_KNOWLEDGE_COLLECTION);

  if (!exists) {
    await qdrant.createCollection(CLIENT_KNOWLEDGE_COLLECTION, {
      vectors: { size: EMBEDDING_DIM, distance: "Cosine" },
    });
    await qdrant.createPayloadIndex(CLIENT_KNOWLEDGE_COLLECTION, {
      field_name: "contact_id",
      field_schema: "keyword",
    });
    await qdrant.createPayloadIndex(CLIENT_KNOWLEDGE_COLLECTION, {
      field_name: "knowledge_type",
      field_schema: "keyword",
    });
    await qdrant.createPayloadIndex(CLIENT_KNOWLEDGE_COLLECTION, {
      field_name: "status",
      field_schema: "keyword",
    });
  }
}

interface ClientKnowledgeEntry {
  contact_id: string;
  contact_name: string;
  knowledge_type: "interaction" | "preference" | "project" | "feedback" | "history";
  content: string;              // The knowledge itself
  source: string;               // "email-triage", "proposal-gen", "check-in", etc.
  timestamp: string;
}

async function indexClientKnowledge(entry: ClientKnowledgeEntry): Promise<void> {
  const embedding = await embed(entry.content);
  const pointId = deterministicId(entry.contact_id, entry.timestamp);

  await qdrant.upsert(CLIENT_KNOWLEDGE_COLLECTION, {
    points: [{
      id: pointId,
      vector: embedding,
      payload: {
        ...entry,
        status: "pending",
        indexed_at: new Date().toISOString(),
      },
    }],
  });
}

async function queryClientKnowledge(
  contactId?: string,
  query?: string,
  limit: number = 10,
): Promise<ClientKnowledgeEntry[]> {
  if (query) {
    // Semantic search -- "what do we know about [client]?"
    const queryEmbedding = await embed(query);
    const filter = contactId
      ? { must: [{ key: "contact_id", match: { value: contactId } }] }
      : undefined;

    const results = await qdrant.search(CLIENT_KNOWLEDGE_COLLECTION, {
      vector: queryEmbedding,
      limit,
      score_threshold: 0.5,
      with_payload: true,
      filter,
    });
    return results.map(r => r.payload as unknown as ClientKnowledgeEntry);
  } else if (contactId) {
    // Direct lookup by contact ID
    const results = await qdrant.scroll(CLIENT_KNOWLEDGE_COLLECTION, {
      filter: { must: [{ key: "contact_id", match: { value: contactId } }] },
      with_payload: true,
      limit,
    });
    return results.points.map(p => p.payload as unknown as ClientKnowledgeEntry);
  }
  return [];
}
```

### Anti-Patterns to Avoid

- **Indexing every single field as an outcome:** Only index actionable outcomes. Routine successful executions with no new pattern don't need embedding. Filter: index errors, operator corrections, and novel patterns. Skip routine successes unless they reveal a new approach.
- **Embedding raw LLM output as the outcome narrative:** The full LLM response is too noisy for meaningful similarity search. Build a concise structured narrative (input summary + result + error/correction) for the embedding. Store the full output in a separate payload field for reference.
- **Querying all collections for pre-task recall:** Only query the collection matching the current task type. Cross-task patterns belong in the general memory system (Phase 2), not in per-task RAG.
- **Promoting all pending entries without quality check:** The 7-day TTL is a "no-complaint" window, not a guaranteed quality stamp. Entries from sessions with known errors (operator explicitly rejected the session output) should NOT auto-promote -- check for rejection signals.
- **Storing client PII in uncontrolled Qdrant payloads:** Client knowledge entries should use contact_id (opaque identifier) not raw email addresses or phone numbers in indexed fields. Full contact details should be retrieved from GHL CRM on demand, not cached in vector payloads.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector similarity search per task | Custom cosine distance | Qdrant collection per task type | HNSW index, payload filtering, score thresholds all built-in |
| Embedding outcome narratives | Custom transformer | Ollama nomic-embed-text (768-dim) | Already running, zero cost, sufficient quality for 200-500 token outcome records |
| TTL-based promotion scheduling | Custom setTimeout chains | node-cron (existing) | Handles cron expressions, timezone, cleanup; extend existing compaction schedule |
| Operator validation UI | Custom web form | Telegram inline buttons (existing) | Phase 3 established callback pattern; extend to outcome validation |
| Client knowledge keyword search | Custom index | FTS5 via better-sqlite3 (existing) | FTS5 handles exact name matching; Qdrant handles semantic; hybrid gives best of both |
| Deterministic point IDs | UUID generation | Hash(path + chunkIndex) pattern (existing) | Phase 2 established the pattern; extend to Hash(sessionId + timestamp) for outcomes |

**Key insight:** Phase 6 is primarily an integration layer, not new infrastructure. The vector database, embedding pipeline, hybrid search, cron scheduling, and Telegram callbacks are all already built. The new code is the orchestration: what to record after each skill, what to recall before each skill, and how to manage the pending-to-confirmed lifecycle.

## Common Pitfalls

### Pitfall 1: Outcome Index Pollution from Repeated Identical Tasks

**What goes wrong:** Email triage runs 3x daily. After 30 days, you have 90 nearly identical "triage 15 emails" outcome records that dominate search results, drowning out rare but valuable error/correction records.
**Why it happens:** Naive "index everything" approach treats routine successes the same as novel outcomes.
**How to avoid:** Implement an outcome dedup filter: before indexing, check if a semantically similar successful outcome already exists (cosine similarity > 0.95 with same task_type). If so, increment a `frequency` counter on the existing point instead of creating a new one. Only index: (1) errors, (2) operator corrections, (3) outcomes with novel patterns, (4) first successful execution of a new input type.
**Warning signs:** Pre-task recall returns 5 identical "success" records with no actionable guidance.

### Pitfall 2: Pre-Task Recall Injection Bloating Context Window

**What goes wrong:** Injecting 5 past outcomes at 200 tokens each adds 1,000 tokens to every system prompt. With prompt caching, this dynamic content invalidates the cache on every call (different recalled outcomes per session).
**How to avoid:** Place recalled lessons AFTER the static cached system prompt, not within it. Use the Phase 2 prompt caching pattern: static base prompt + MEMORY.md (cacheable prefix) then dynamic context including recall results (after cache breakpoint). Limit recall injection to 3 results and cap at 500 tokens total. For the Ollama tier (free), skip recall injection entirely (classification tasks don't benefit from outcome history).
**Warning signs:** Prompt cache hit rate drops significantly after Phase 6 deployment; token costs increase despite caching.

### Pitfall 3: Write Gate Promotion During Active Error Streak

**What goes wrong:** Agent has a bad week (API outage, misconfigured prompt). 20 poor outcomes enter as "pending." After 7 days of no complaints (because the operator didn't notice), they all auto-promote to "confirmed" and poison future recall.
**Why it happens:** "No-complaint" assumes the operator reviews outcomes, but in practice many slip through unnoticed.
**How to avoid:** Add a quality gate to the promotion job: only promote entries where `success: true` OR `operator_correction` exists (corrections are valuable learning). Failed outcomes without corrections stay pending indefinitely until the operator reviews them. Surface un-reviewed failure outcomes in the weekly check-in summary.
**Warning signs:** Pre-task recall returns poor advice from auto-promoted failed outcomes.

### Pitfall 4: Collection Schema Drift Across Task Types

**What goes wrong:** Each task type evolves its payload schema independently. Email-triage adds a `sender_domain` field, proposal-gen adds a `slide_count` field, and the outcome-indexer breaks trying to handle a generic OutcomeRecord type.
**Why it happens:** TypeScript types diverge from what's actually in Qdrant payloads when task-specific fields are added ad-hoc.
**How to avoid:** Keep a strict base OutcomeRecord interface that all task types share. Task-specific extensions go in a `task_metadata: Record<string, unknown>` field that is stored but not indexed. Only index shared fields (status, indexed_at, success, task_type, contact_id).
**Warning signs:** TypeScript compilation passes but runtime Qdrant queries return unexpected payload shapes.

### Pitfall 5: Client Knowledge Conflation Between Contacts

**What goes wrong:** "John from Acme" and "John from Beta Corp" both get knowledge entries. A query for "what do we know about John?" returns mixed results from both contacts without clear attribution.
**Why it happens:** Semantic search on names without contact_id filtering.
**How to avoid:** Always pass `contact_id` when querying client knowledge for a specific person. Only use open semantic search (without contact_id filter) for broad queries like "which clients mentioned pricing concerns?" The contact_id field is indexed as a keyword for efficient exact-match filtering.
**Warning signs:** Client-specific queries return irrelevant results from other clients.

### Pitfall 6: Qdrant Point ID Collisions Across Collections

**What goes wrong:** Using the same ID scheme for all collections causes silent point overwrites if a session produces outcomes for multiple task types with the same hash.
**Why it happens:** Deterministic ID from `hash(sessionId + timestamp)` is the same across collections because the inputs are identical.
**How to avoid:** Include the task type in the hash input: `hash(taskType + sessionId + timestamp)`. Each collection has its own ID space, but using unique IDs prevents confusion during debugging and cross-collection operations.
**Warning signs:** Outcome records disappear after multi-task sessions; upsert silently replaces existing points.

## Code Examples

### Complete Outcome Indexing Flow (Post-Execution Hook)

```typescript
// Source: Pattern 2 above + integration with existing skill execution
import { indexOutcome } from "./outcome-indexer.js";
import { indexClientKnowledge } from "./client-knowledge.js";

// Called by every skill after execution
export async function postExecutionHook(
  taskType: string,
  input: { summary: string; contactId?: string; contactName?: string },
  result: { success: boolean; output: string; errorType?: string; errorMessage?: string },
  usage: { inputTokens: number; outputTokens: number; costUsd: number; modelTier: string },
  sessionId: string,
  operatorCorrection?: string,
): Promise<void> {
  // 1. Index the outcome into the task-specific collection
  await indexOutcome({
    task_type: taskType,
    input_summary: input.summary,
    output_summary: result.output.slice(0, 500), // Cap output summary
    success: result.success,
    error_type: result.errorType,
    error_message: result.errorMessage,
    token_usage: { input: usage.inputTokens, output: usage.outputTokens, cost_usd: usage.costUsd },
    model_tier: usage.modelTier,
    operator_correction: operatorCorrection,
    contact_id: input.contactId,
    session_id: sessionId,
    timestamp: new Date().toISOString(),
  });

  // 2. If client-related, also index client knowledge
  if (input.contactId && input.contactName) {
    const knowledgeContent = buildClientKnowledgeFromOutcome(taskType, input, result);
    if (knowledgeContent) {
      await indexClientKnowledge({
        contact_id: input.contactId,
        contact_name: input.contactName,
        knowledge_type: "interaction",
        content: knowledgeContent,
        source: taskType,
        timestamp: new Date().toISOString(),
      });
    }
  }
}
```

### Complete Pre-Task Recall Flow (Pre-Execution Hook)

```typescript
// Source: Pattern 3 above + integration with existing routeAndCall
import { recallForTask } from "./pre-task-recall.js";
import { buildCachedSystemPrompt } from "../router/prompt-cache.js";

// Called by every skill before execution
export async function preExecutionHook(
  taskType: string,
  currentContext: string,
  baseSystemPrompt: string,
): Promise<string> {
  // 1. Recall relevant past outcomes
  const recall = await recallForTask(taskType, currentContext);

  // 2. Inject lessons into system prompt (after cache breakpoint)
  if (recall.lessons) {
    return baseSystemPrompt + "\n\n" + recall.lessons;
  }

  return baseSystemPrompt;
}
```

### Write Gate Promotion Cron Job

```typescript
// Source: Pattern 4 above + Phase 2 compaction.ts cron pattern
import { schedule } from "node-cron";
import { promotePendingEntries } from "./write-gates.js";
import { logEntry } from "../memory/daily-log.js";

export function scheduleWriteGatePromotion(): ReturnType<typeof schedule> {
  // Run nightly at 2 AM (before compaction at 3 AM Sunday)
  return schedule("0 2 * * *", async () => {
    try {
      const promoted = await promotePendingEntries();
      if (promoted > 0) {
        logEntry({
          type: "action",
          summary: `Write gates: promoted ${promoted} pending outcomes to confirmed (7-day TTL expired)`,
        });
      }
    } catch (err) {
      console.error(JSON.stringify({
        level: "ERROR",
        component: "write-gates",
        action: "PROMOTION_FAILED",
        error: (err as Error).message,
      }));
    }
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Global RAG (one collection for everything) | Per-task collections with payload indexing | 2024-2025 | Isolated recall prevents cross-task pollution; each task type has its own learning curve |
| Manual feedback logging | Automatic outcome indexing with write gates | 2025 | Every execution automatically produces learning data without operator intervention |
| Keyword-only recall (FTS5) | Hybrid recall (vector + FTS5 via RRF) | Phase 2 (2026-03) | Conceptual "what went wrong with similar inputs?" queries work alongside exact error lookups |
| Static prompts for all executions | Dynamic prompts with injected past outcomes | 2025-2026 | Observable behavior change on second execution of same task type |
| Qdrant single collection with prefix naming | Qdrant per-collection with payload indexes | Qdrant 1.16+ (2025) | Payload indexes on keyword/datetime fields enable sub-ms filtering for write gate queries |

**Deprecated/outdated:**
- Large-scale separate collection patterns (100+ collections): Qdrant docs now recommend payload multitenancy for large tenant counts. Not relevant here (5-7 collections is fine).
- sqlite-vss for vector operations: Replaced by sqlite-vec, but neither is needed since Qdrant handles all vector operations.

## Open Questions

1. **Outcome dedup threshold tuning**
   - What we know: Cosine similarity > 0.95 should catch near-duplicate outcomes. The threshold needs to be strict enough to avoid false dedup (dropping legitimately different outcomes).
   - What's unclear: Whether 0.95 is correct for nomic-embed-text on short outcome narratives (~100-300 tokens). May need empirical tuning.
   - Recommendation: Start with 0.95, log dedup decisions for first 2 weeks, adjust if outcomes are incorrectly merged or if collections grow too fast.

2. **Optimal recall injection size**
   - What we know: 3 results at ~150 tokens each = ~450 tokens is manageable. The research suggests diminishing returns after 3-5 relevant examples.
   - What's unclear: Whether 3 is optimal or if some task types benefit from more context (e.g., proposal-gen may need 5 past outcomes, while check-in may need only 1).
   - Recommendation: Default to 3, make it configurable per task type in task-rag.yaml. Monitor prompt cache hit rates before and after Phase 6.

3. **Operator review UX for pending outcomes**
   - What we know: Telegram inline buttons work for HITL approval (established in Phase 3). Outcomes are less urgent than HITL actions.
   - What's unclear: Whether operators will actually review pending outcomes or if they'll all auto-promote via TTL. The UX for reviewing past outcomes is different from approving real-time actions.
   - Recommendation: Surface pending outcomes in the weekly check-in summary (Phase 4 check-in engine). "Last week: 12 new learnings indexed, 3 need your review: [Review]". Don't spam individual Telegram messages for each outcome.

4. **Client knowledge dedup across workflows**
   - What we know: Email triage, proposals, and check-ins may all record "Acme Corp prefers email communication" independently.
   - What's unclear: How to prevent 5 identical client knowledge entries from different sources.
   - Recommendation: Same dedup approach as outcomes: check semantic similarity before indexing. If a highly similar entry exists for the same contact_id, update the existing entry's `source` field to include the new source rather than creating a duplicate.

## Sources

### Primary (HIGH confidence)
- [Qdrant Collections Documentation](https://qdrant.tech/documentation/concepts/collections/) -- Collection creation, vector config, JS/TS client examples, management operations
- [Qdrant Multitenancy Guide](https://qdrant.tech/documentation/guides/multitenancy/) -- When to use multiple collections vs. payload partitioning; official recommendation for <10 tenants
- [Qdrant Payload Documentation](https://qdrant.tech/documentation/concepts/payload/) -- Payload types, indexing (keyword, datetime, bool), filtering syntax
- [Qdrant JS Client GitHub](https://github.com/qdrant/qdrant-js) -- @qdrant/js-client-rest v1.17.0 TypeScript API
- Phase 2 Research (02-RESEARCH.md) -- Qdrant client patterns, embed() usage, collection initialization, RRF hybrid search
- Phase 2 Plan 01 (02-01-PLAN.md) -- Memory system architecture, vector-search.ts exports, FTS5 index schema
- Phase 2 Plan 02 (02-02-PLAN.md) -- Model router, prompt caching patterns, cost tracker integration
- Project Blueprint: `04-Memory-and-RAG/memory-architecture.md` -- File-first philosophy, memory hierarchy, write patterns
- Project Blueprint: `04-Memory-and-RAG/hybrid-search.md` -- RRF implementation, query-adaptive weights
- Project Blueprint: `04-Memory-and-RAG/embedding-models.md` -- nomic-embed-text at 768-dim, embedding consistency rules

### Secondary (MEDIUM confidence)
- [Qdrant Create Payload Index API](https://api.qdrant.tech/api-reference/indexes/create-field-index) -- REST and client methods for indexing payload fields
- Phase 3 Summary (03-01-SUMMARY.md) -- Telegram callback pattern for inline approval/rejection
- Phase 4 Summary (04-01-SUMMARY.md) -- Todo aggregator dedup pattern, transcript extraction pipeline
- Phase 5 Summaries (05-01, 05-02) -- Proposal pipeline, industry-context.ts as swap point for Phase 6
- Project Blueprint: `12-Self-Evolution/evolution-architecture.md` -- Metrics collection schema (evolution_metrics table) informs outcome record structure
- [Self-Improving RAG Research](https://pub.towardsai.net/building-a-self-improving-rag-system-with-reinforcement-learning-dbf51df5a966) -- Feedback loop patterns for RAG systems

### Tertiary (LOW confidence)
- Optimal outcome dedup threshold (0.95): Needs empirical validation with nomic-embed-text on short texts
- Recall injection token budget (500 tokens): Based on general RAG best practices, may need per-task tuning
- 7-day TTL for write gate promotion: Chosen to balance timeliness with review opportunity; may need adjustment based on operator engagement patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and verified from Phases 1-3; no new dependencies needed
- Architecture: HIGH -- Patterns extend existing Phase 2 vector-search.ts and Phase 3 callback patterns; Qdrant collection management is well-documented
- Pitfalls: HIGH -- Outcome pollution, context bloat, and write gate promotion risks are well-understood from RAG system literature and project-specific context
- Write gates: MEDIUM -- The 7-day TTL and quality gate logic is sound architecturally but the operator review UX needs real-world validation
- Client knowledge: MEDIUM -- Dedup across workflows and contact_id indexing are straightforward, but query patterns for "what do we know about [client]?" need tuning

**Research date:** 2026-03-02
**Valid until:** 2026-03-16 (14 days -- Qdrant client may update; outcome patterns are project-specific and stable)

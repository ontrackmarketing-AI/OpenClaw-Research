# Memory Architecture

## File-First Philosophy

OpenClaw stores all persistent knowledge in plain files -- Markdown, JSON, and SQLite databases on disk. This is a deliberate architectural choice over cloud-hosted databases or opaque binary stores.

**Why files over databases for primary storage:**

- **Inspectable.** You can open any memory file in a text editor and read what the agent knows. No query language required, no admin panel, no credentials.
- **Portable.** Copy the memory directory to another machine and the agent works identically. No database migration scripts, no connection strings.
- **Version-controllable.** Memory files live in a directory that can be tracked with Git. You get full history of what the agent learned and when.
- **Resilient.** If a process crashes mid-write, you lose at most one file. There is no WAL corruption, no orphaned transactions, no recovery procedure beyond "check the last file."
- **Composable.** Other tools (grep, ripgrep, VS Code, Obsidian) can read and search the same files without any adapter layer.

The SQLite index is the sole exception: it exists as a performance optimization layer over the files, not as the source of truth. If the SQLite database is deleted, it can be fully rebuilt from the files.

---

## Core Components

### 1. MEMORY.md -- Persistent Agent Memory

`MEMORY.md` is the single most important file in the memory system. It is loaded into the system prompt at the start of every agent session.

**Location:** `~/.openclaw/memory/MEMORY.md`

**Contents:**

```markdown
# Agent Memory

## User Preferences
- Preferred LLM: Claude Opus 4 via API
- Coding style: TypeScript, functional, minimal dependencies
- Communication: direct, no fluff, technical depth preferred

## Active Projects
- OpenClaw: AI agent framework, Phase 2 (memory system)
- Rise Local: SMB lead gen pipeline using 15-signal pain scoring
- OnTrack Marketing: agency operations, Qdrant RAG for client knowledge

## Key Facts
- Supabase project ID: jitawzicdwgbhatvjblh (currently paused)
- Qdrant instance: OnTrack Marketing vector store, 768-dim embeddings
- Primary machine: Windows 11, WSL2 available
- n8n instance: running locally on port 5678

## Learned Patterns
- User prefers SQLite over Postgres for local tooling
- Always check MEMORY.md before suggesting tools the user already has
- User runs a marketing agency targeting SMB local services and solar
```

**Update rules:**

- Agents append to MEMORY.md when they learn something persistent about the user, the project, or the environment.
- Agents never delete from MEMORY.md without explicit user confirmation.
- MEMORY.md is kept under 4,000 tokens to avoid consuming too much context window. When it grows beyond that, a compaction pass runs (see Memory Compaction below).

**Loading behavior:**

1. Agent starts a session.
2. Agent reads `~/.openclaw/memory/MEMORY.md` into the system prompt.
3. Agent now has persistent context without the user re-explaining anything.

---

### 2. Daily Logs -- Timestamped Conversation and Action Logs

Every agent session produces a daily log file capturing what happened: queries asked, actions taken, tools called, errors encountered, and decisions made.

**Location:** `~/.openclaw/memory/logs/YYYY/MM/DD.md`

**Example:** `~/.openclaw/memory/logs/2026/02/05.md`

**Structure:**

```markdown
# 2026-02-05 Session Log

## Session 1 (09:15 - 10:42)
### Context
- Working on OpenClaw memory architecture docs
- User requested 10 files for 04-Memory-and-RAG section

### Actions
- Created memory-architecture.md
- Created hybrid-search.md
- Created embedding-models.md
- ...

### Decisions
- Chose SQLite over DuckDB for hybrid search (simpler deployment)
- Recommended nomic-embed-text for local embeddings (best balance)

### Errors
- None

## Session 2 (14:00 - 15:30)
### Context
- Debugging n8n workflow for lead scoring
...
```

**Why daily logs matter:**

- They provide an audit trail of everything the agent did.
- They feed the long-term memory system: the SQLite index ingests these logs so the agent can search its own history.
- They enable debugging: when an agent makes a mistake, you can trace back through the log to find what went wrong.
- They support continuity: a new session can read yesterday's log to pick up where things left off.

---

### 3. SQLite Index -- Structured Metadata and Search

The SQLite index is a single database file that provides fast, structured search over all memory content.

**Location:** `~/.openclaw/memory/index.db`

**Schema (core tables):**

```sql
-- Document registry: every file in the memory system
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,          -- relative path from memory root
    content_hash TEXT NOT NULL,          -- SHA-256 of file contents
    title TEXT,
    doc_type TEXT,                       -- 'memory', 'log', 'knowledge', 'note'
    sector TEXT,                         -- 'smb-local', 'solar', 'general'
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    token_count INTEGER
);

-- Chunks: document content split into searchable pieces
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,                -- position within document
    content TEXT NOT NULL,
    embedding BLOB,                     -- vector embedding (768-dim float32)
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

-- FTS5 full-text search index
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content='chunks',
    content_rowid='id',
    tokenize='porter unicode61'
);

-- Triggers to keep FTS5 in sync
CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
END;

CREATE TRIGGER chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content) VALUES ('delete', old.id, old.content);
    INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
END;

-- Memory entries: key-value style fast lookups
CREATE TABLE memory_entries (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    category TEXT,                       -- 'preference', 'fact', 'project', 'pattern'
    confidence REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    source TEXT                          -- which log/session created this
);
```

**Capabilities:**

- Full-text search via FTS5: `SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'solar lead cost'`
- Vector similarity search via sqlite-vec: find semantically similar content
- Structured queries: find all documents for a sector, find all logs from a date range
- Metadata lookups: retrieve facts by key from memory_entries

---

## Memory Hierarchy

OpenClaw uses a three-tier memory hierarchy, mirroring how human memory works:

```
+------------------------------------------------------------------+
|  WORKING MEMORY (Context Window)                                  |
|  - Current conversation messages                                  |
|  - System prompt (includes MEMORY.md)                             |
|  - Retrieved RAG results for current query                        |
|  - Capacity: ~128K-200K tokens depending on model                 |
|  - Lifetime: current request only                                 |
+------------------------------------------------------------------+
        |
        | Session ends -> summarize -> write to daily log
        v
+------------------------------------------------------------------+
|  SHORT-TERM MEMORY (Session State)                                |
|  - Current session's conversation history                         |
|  - Tool call results cached in session                            |
|  - Scratchpad notes the agent writes during a task                |
|  - Capacity: unlimited (but context window limits visibility)     |
|  - Lifetime: current session (hours)                              |
+------------------------------------------------------------------+
        |
        | Important facts -> MEMORY.md, session summary -> daily log
        v
+------------------------------------------------------------------+
|  LONG-TERM MEMORY (Files + SQLite Index)                          |
|  - MEMORY.md: critical persistent facts                           |
|  - Daily logs: complete session history                           |
|  - SQLite index: searchable structured data + embeddings          |
|  - Knowledge bases: sector-specific RAG content                   |
|  - Capacity: disk-limited (practically unlimited)                 |
|  - Lifetime: permanent until explicitly deleted                   |
+------------------------------------------------------------------+
```

**Data flow between tiers:**

1. **Session start:** MEMORY.md is loaded into working memory. Recent daily log entries may be loaded if relevant.
2. **During session:** Agent queries SQLite index to pull relevant long-term memories into working memory as needed.
3. **Session end:** Agent summarizes session, appends to daily log, and updates MEMORY.md if any persistent facts were learned.
4. **Background:** Compaction processes summarize old daily logs to free space while preserving key information.

---

## Memory Directory Structure

```
~/.openclaw/
  memory/
    MEMORY.md                       # Persistent agent memory (system prompt)
    index.db                        # SQLite index (FTS5 + vectors)
    config.yaml                     # Memory system configuration
    logs/
      2026/
        01/
          15.md                     # Daily log for Jan 15
          16.md
        02/
          05.md                     # Today's log
    knowledge/
      general/                      # Cross-sector knowledge
        marketing-fundamentals.md
        seo-best-practices.md
      smb-local-services/           # Sector-specific knowledge
        pain-points.md
        channel-effectiveness.md
        pricing-benchmarks.md
      solar-home-improvement/
        pain-points.md
        regulatory.md
        financing-options.md
      healthcare-dental/
        ...
    scratchpad/                     # Temporary working notes
      current-task.md
    exports/                        # Exported memory snapshots
```

---

## How Agents Read and Write Memory

### Reading Memory

Agents use a cascading read strategy:

```
1. Check MEMORY.md (always loaded, zero-cost)
     |
     v -- not found
2. Search SQLite FTS5 index (keyword search, <10ms)
     |
     v -- not found or need semantic match
3. Search SQLite vector index (embedding similarity, <50ms)
     |
     v -- not found
4. Search daily logs by date range (structured file scan)
     |
     v -- still not found
5. Report: "I don't have this information in memory"
```

### Writing Memory

Agents write memory through explicit operations:

| Operation | Target | When |
|-----------|--------|------|
| `memory.remember(key, value)` | MEMORY.md + memory_entries table | Agent learns a persistent fact |
| `memory.log(entry)` | Daily log file | Every significant action or decision |
| `memory.index(file)` | SQLite chunks + FTS5 + vectors | New document added to knowledge base |
| `memory.forget(key)` | MEMORY.md + memory_entries table | User requests removal (with confirmation) |
| `memory.update(key, value)` | MEMORY.md + memory_entries table | Fact changes (e.g., project status update) |

### Write Conflict Resolution

Since OpenClaw may eventually support multiple agents, writes use a simple strategy:

- MEMORY.md: append-only during sessions, compaction only runs single-threaded between sessions.
- Daily logs: each session gets its own section header, so concurrent writes append to different sections.
- SQLite: standard SQLite WAL mode handles concurrent reads with single-writer semantics.

---

## Memory Compaction

Over time, daily logs and MEMORY.md grow. Compaction keeps memory manageable.

### MEMORY.md Compaction

**Trigger:** MEMORY.md exceeds 4,000 tokens.

**Process:**

1. Read current MEMORY.md.
2. Send to LLM with prompt: "Summarize this memory file. Keep all critical facts, preferences, and active project details. Remove redundant entries, outdated information, and low-value observations. Target: under 3,000 tokens."
3. Human reviews the compacted version (or auto-approve if configured).
4. Write compacted version. Archive the original to `exports/MEMORY-YYYY-MM-DD.md`.

### Daily Log Compaction

**Trigger:** Daily logs older than 30 days.

**Process:**

1. Read logs older than 30 days.
2. For each week of old logs, generate a weekly summary (key decisions, outcomes, patterns).
3. Store weekly summaries in `logs/summaries/YYYY-WNN.md`.
4. Delete the original daily logs (their content is already indexed in SQLite).
5. Keep the SQLite index entries -- they still point to the summary files.

### SQLite Index Compaction

**Trigger:** Database exceeds configured size limit (default: 500 MB) or on manual request.

**Process:**

1. Identify chunks with low relevance scores (never retrieved, from deleted documents).
2. Remove orphaned chunks.
3. Run `VACUUM` to reclaim space.
4. Rebuild FTS5 index: `INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')`.

---

## Cross-Agent Memory

When multiple OpenClaw agents operate (e.g., a research agent and a coding agent), they share memory through the file system.

**Shared resources:**

- MEMORY.md: all agents read the same persistent memory.
- SQLite index: all agents query the same index (SQLite WAL mode supports concurrent reads).
- Knowledge bases: sector-specific files are accessible to any agent.

**Agent-specific resources:**

- Each agent can have its own scratchpad: `scratchpad/{agent-name}/`.
- Session context is not shared (each agent has its own conversation).

**Coordination pattern:**

1. Agent A writes a finding to the daily log and indexes it.
2. Agent B, in a later session, searches the index and finds Agent A's finding.
3. If Agent A discovers a persistent fact, it writes to MEMORY.md, which Agent B will see on its next session start.

There is no real-time message passing between agents. All coordination happens through the shared file system and SQLite index. This is intentional: it keeps the system simple and avoids the complexity of inter-process communication.

---

## Configuration

**File:** `~/.openclaw/memory/config.yaml`

```yaml
memory:
  # MEMORY.md settings
  persistent:
    max_tokens: 4000
    auto_compact: true
    compact_threshold: 4000  # tokens
    compact_target: 3000     # tokens after compaction

  # Daily log settings
  logs:
    retention_days: 30       # days before compaction
    summary_granularity: week  # 'day' or 'week' summaries

  # SQLite index settings
  index:
    db_path: index.db
    max_size_mb: 500
    embedding_model: nomic-embed-text  # via Ollama
    embedding_dimensions: 768
    fts5_tokenizer: "porter unicode61"

  # Search defaults
  search:
    vector_weight: 0.6       # weight for vector similarity in hybrid search
    fts5_weight: 0.4         # weight for FTS5 relevance
    max_results: 10
    similarity_threshold: 0.7

  # Compaction schedule
  compaction:
    schedule: "0 3 * * 0"    # every Sunday at 3 AM
    auto_approve: false       # require human review of compacted memory
```

---

## Implementation Priority

For the OpenClaw MVP, implement memory in this order:

1. **MEMORY.md read/write** -- highest value, simplest implementation. Just read a file into the system prompt and append to it.
2. **Daily logs** -- append-only file writes, straightforward.
3. **SQLite FTS5 index** -- enables keyword search over all memory content.
4. **SQLite vector search** -- enables semantic search, requires embedding pipeline.
5. **Compaction** -- quality-of-life improvement, not critical for initial use.
6. **Cross-agent coordination** -- only needed when running multiple agents.

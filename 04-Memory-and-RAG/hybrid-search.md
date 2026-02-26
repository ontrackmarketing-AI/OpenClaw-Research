# Hybrid Search: Vector Similarity + FTS5 Full-Text Search

## Why Hybrid Search

Neither vector search nor keyword search alone is sufficient for a knowledge system.

**Vector search** (semantic similarity) excels at finding content that is conceptually related even when different words are used. Ask "how to reduce customer churn" and it finds a document titled "improving client retention rates." But it fails at exact matches -- searching for "project jitawzicdwgbhatvjblh" returns garbage because embedding models treat that as noise.

**FTS5 full-text search** (keyword matching) excels at exact and partial phrase matching. Search for "jitawzicdwgbhatvjblh" and it finds exactly the document containing that string. But it fails at semantic understanding -- searching "reduce churn" won't find a document that only says "keep customers from leaving."

**Hybrid search** runs both, merges the results, and returns the best of both worlds. This is the approach OpenClaw uses.

---

## Architecture Overview

```
User Query: "What's the cost per lead for HVAC companies?"
         |
         v
+-------------------+
| Query Processor   |
| 1. Clean query    |
| 2. Generate embed |
+-------------------+
         |
    +----+----+
    |         |
    v         v
+--------+ +--------+
| Vector | | FTS5   |
| Search | | Search |
+--------+ +--------+
    |         |
    v         v
+-------------------+
| Result Merger     |
| (RRF Fusion)      |
+-------------------+
         |
         v
+-------------------+
| Ranked Results    |
| with scores       |
+-------------------+
```

---

## Vector Search Component

### How It Works

1. The user query is converted to an embedding vector using the same model that embedded the stored documents (e.g., nomic-embed-text, 768 dimensions).
2. The vector is compared against all stored chunk embeddings using cosine similarity.
3. Results are ranked by similarity score (0.0 = unrelated, 1.0 = identical).

### SQLite Vector Search with sqlite-vec

OpenClaw uses **sqlite-vec** (the successor to sqlite-vss) for vector search inside SQLite.

**Installation:**

```bash
# sqlite-vec is distributed as a loadable extension
# Python: pip install sqlite-vec
# Node.js: npm install sqlite-vec
```

**Setup:**

```sql
-- Load the extension (Python example)
-- import sqlite_vec
-- db.load_extension(sqlite_vec.loadable_path())

-- Create a virtual table for vector search
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[768]               -- match your embedding model dimensions
);

-- Insert embeddings (done during ingestion)
INSERT INTO vec_chunks (chunk_id, embedding)
VALUES (1, :embedding_blob);           -- embedding as raw bytes (768 floats)
```

**Query:**

```sql
-- Find the 10 most similar chunks to a query embedding
SELECT
    vc.chunk_id,
    vc.distance,                        -- L2 distance (lower = more similar)
    c.content,
    d.path,
    d.sector
FROM vec_chunks vc
JOIN chunks c ON c.id = vc.chunk_id
JOIN documents d ON d.id = c.document_id
WHERE embedding MATCH :query_embedding
    AND k = 10                          -- return top 10
ORDER BY vc.distance ASC;
```

**Distance to similarity conversion:**

sqlite-vec returns L2 (Euclidean) distance by default. To convert to a 0-1 similarity score:

```python
similarity = 1.0 / (1.0 + distance)
```

Alternatively, if you normalize your embeddings to unit vectors before storing, you can use:

```python
# For normalized vectors, L2 distance relates to cosine similarity:
cosine_similarity = 1.0 - (distance ** 2) / 2.0
```

### Vector Search Strengths

- Finds semantically related content even with different wording
- Handles synonyms, paraphrases, and conceptual matches
- Works across languages (if the embedding model is multilingual)

### Vector Search Weaknesses

- Cannot do exact string matching reliably
- Embeddings compress meaning -- nuance is lost
- Requires consistent embedding model (can't mix models)
- Slower than keyword search for large corpora

---

## FTS5 Full-Text Search Component

### How It Works

SQLite's FTS5 extension creates an inverted index of tokens (words) across all documents. When you search, it finds documents containing those tokens and ranks them using BM25 (a TF-IDF variant).

### Setup

The FTS5 virtual table is created alongside the chunks table (see memory-architecture.md for full schema):

```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content='chunks',
    content_rowid='id',
    tokenize='porter unicode61'
);
```

**Tokenizer choice:**

- `unicode61`: handles Unicode text correctly, lowercases, strips accents.
- `porter`: applies Porter stemming so "running" matches "run", "costs" matches "cost".
- Combined `porter unicode61`: both features enabled. This is the recommended setting.

### Query Syntax

FTS5 supports a rich query syntax:

```sql
-- Basic keyword search (implicit AND)
SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'HVAC cost per lead';

-- Phrase search (exact phrase)
SELECT * FROM chunks_fts WHERE chunks_fts MATCH '"cost per lead"';

-- Boolean operators
SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'HVAC AND (cost OR price) NOT residential';

-- Prefix search
SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'solar install*';

-- NEAR operator (words within N tokens of each other)
SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'NEAR(lead cost, 5)';

-- BM25 ranking (lower score = more relevant, it's negative)
SELECT
    c.id,
    c.content,
    rank AS bm25_score
FROM chunks_fts
JOIN chunks c ON c.id = chunks_fts.rowid
WHERE chunks_fts MATCH 'HVAC cost per lead'
ORDER BY rank;
```

### FTS5 Strengths

- Blazing fast: sub-millisecond for most queries, even on millions of rows
- Exact matching: finds specific IDs, names, technical terms
- Transparent ranking: BM25 scores are interpretable
- No external dependencies: built into SQLite

### FTS5 Weaknesses

- No semantic understanding: "reduce churn" won't match "keep customers"
- Sensitive to exact wording and spelling
- Stemming helps but is imperfect ("running" -> "run", but "better" doesn't stem to "good")

---

## Hybrid Scoring: Reciprocal Rank Fusion (RRF)

RRF is the standard method for combining results from multiple ranking systems. It is simple, effective, and does not require tuning score distributions.

### How RRF Works

1. Run vector search. Get ranked results: result_v1, result_v2, ..., result_vN.
2. Run FTS5 search. Get ranked results: result_f1, result_f2, ..., result_fN.
3. For each result, compute its RRF score based on its rank in each list.
4. Sort by combined RRF score.

**Formula:**

```
RRF_score(doc) = sum over all rankers of: 1 / (k + rank(doc))
```

Where `k` is a constant (typically 60) that prevents top-ranked results from dominating too aggressively.

### Implementation

```python
from collections import defaultdict

def reciprocal_rank_fusion(
    vector_results: list[dict],   # [{"id": 1, "score": 0.92}, ...]
    fts5_results: list[dict],     # [{"id": 3, "score": -1.5}, ...]
    k: int = 60,
    vector_weight: float = 0.6,
    fts5_weight: float = 0.4,
) -> list[dict]:
    """
    Merge vector and FTS5 results using weighted Reciprocal Rank Fusion.

    Args:
        vector_results: Results from vector similarity search, ordered by relevance.
        fts5_results: Results from FTS5 search, ordered by relevance.
        k: RRF constant (default 60). Higher values reduce the advantage of top ranks.
        vector_weight: Weight for vector search signal (default 0.6).
        fts5_weight: Weight for FTS5 search signal (default 0.4).

    Returns:
        Merged results sorted by combined RRF score (highest first).
    """
    scores = defaultdict(lambda: {"id": None, "rrf_score": 0.0, "sources": []})

    # Score vector results
    for rank, result in enumerate(vector_results, start=1):
        doc_id = result["id"]
        scores[doc_id]["id"] = doc_id
        scores[doc_id]["rrf_score"] += vector_weight * (1.0 / (k + rank))
        scores[doc_id]["sources"].append("vector")
        scores[doc_id]["vector_rank"] = rank
        scores[doc_id]["vector_score"] = result["score"]

    # Score FTS5 results
    for rank, result in enumerate(fts5_results, start=1):
        doc_id = result["id"]
        scores[doc_id]["id"] = doc_id
        scores[doc_id]["rrf_score"] += fts5_weight * (1.0 / (k + rank))
        scores[doc_id]["sources"].append("fts5")
        scores[doc_id]["fts5_rank"] = rank
        scores[doc_id]["fts5_score"] = result["score"]

    # Sort by RRF score descending
    merged = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    return merged
```

### Weighting Guidance

| Use Case | Vector Weight | FTS5 Weight | Rationale |
|----------|--------------|-------------|-----------|
| General knowledge queries | 0.6 | 0.4 | Semantic understanding matters more |
| Looking up specific entities | 0.3 | 0.7 | Exact name/ID matching matters more |
| Searching daily logs | 0.4 | 0.6 | Logs have specific dates, names, actions |
| Sector knowledge exploration | 0.7 | 0.3 | Conceptual similarity across industries |
| Code/config search | 0.2 | 0.8 | Exact syntax and identifiers matter most |

OpenClaw defaults to 0.6 vector / 0.4 FTS5, configurable per query or globally.

---

## Complete Query Pipeline

Here is the full pipeline from user query to ranked results:

```python
import sqlite3
import sqlite_vec
import numpy as np
from typing import Optional

class HybridSearch:
    def __init__(self, db_path: str, embed_fn):
        """
        Args:
            db_path: Path to SQLite database with vec0 and FTS5 tables.
            embed_fn: Function that takes a string and returns a numpy array embedding.
        """
        self.db = sqlite3.connect(db_path)
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.embed_fn = embed_fn

    def search(
        self,
        query: str,
        limit: int = 10,
        vector_weight: float = 0.6,
        fts5_weight: float = 0.4,
        similarity_threshold: float = 0.5,
        sector: Optional[str] = None,
    ) -> list[dict]:
        """
        Execute hybrid search combining vector similarity and FTS5.

        Args:
            query: Natural language search query.
            limit: Maximum number of results to return.
            vector_weight: Weight for vector search in RRF fusion.
            fts5_weight: Weight for FTS5 search in RRF fusion.
            similarity_threshold: Minimum vector similarity to include.
            sector: Optional sector filter (e.g., 'smb-local-services').

        Returns:
            List of result dicts with content, metadata, and scores.
        """
        # Step 1: Generate query embedding
        query_embedding = self.embed_fn(query)

        # Step 2: Vector search
        vector_results = self._vector_search(
            query_embedding, limit=limit * 2, sector=sector
        )

        # Step 3: FTS5 search
        fts5_results = self._fts5_search(query, limit=limit * 2, sector=sector)

        # Step 4: Filter by similarity threshold
        vector_results = [
            r for r in vector_results
            if r["similarity"] >= similarity_threshold
        ]

        # Step 5: Merge with RRF
        merged = reciprocal_rank_fusion(
            vector_results, fts5_results,
            vector_weight=vector_weight,
            fts5_weight=fts5_weight,
        )

        # Step 6: Enrich with full content and metadata
        results = []
        for item in merged[:limit]:
            chunk = self._get_chunk(item["id"])
            results.append({
                "chunk_id": item["id"],
                "content": chunk["content"],
                "document_path": chunk["path"],
                "sector": chunk["sector"],
                "rrf_score": item["rrf_score"],
                "sources": item["sources"],
            })

        return results

    def _vector_search(self, embedding, limit, sector=None):
        query = """
            SELECT vc.chunk_id, vc.distance
            FROM vec_chunks vc
            JOIN chunks c ON c.id = vc.chunk_id
            JOIN documents d ON d.id = c.document_id
            WHERE embedding MATCH ?
                AND k = ?
        """
        params = [embedding.tobytes(), limit]

        if sector:
            query += " AND d.sector = ?"
            params.append(sector)

        rows = self.db.execute(query, params).fetchall()
        return [
            {"id": row[0], "score": 1.0 / (1.0 + row[1]), "similarity": 1.0 / (1.0 + row[1])}
            for row in rows
        ]

    def _fts5_search(self, query, limit, sector=None):
        # Escape FTS5 special characters in query
        safe_query = self._escape_fts5(query)

        sql = """
            SELECT c.id, rank
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            JOIN documents d ON d.id = c.document_id
            WHERE chunks_fts MATCH ?
        """
        params = [safe_query]

        if sector:
            sql += " AND d.sector = ?"
            params.append(sector)

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        rows = self.db.execute(sql, params).fetchall()
        return [
            {"id": row[0], "score": abs(row[1])}  # BM25 rank is negative
            for row in rows
        ]

    def _escape_fts5(self, query: str) -> str:
        """Escape special FTS5 characters to prevent query syntax errors."""
        special = ['"', "'", "(", ")", "*", "+", "-", ":", "^", "{", "}", "~"]
        for char in special:
            query = query.replace(char, " ")
        return query.strip()

    def _get_chunk(self, chunk_id: int) -> dict:
        row = self.db.execute("""
            SELECT c.content, d.path, d.sector
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.id = ?
        """, [chunk_id]).fetchone()
        return {"content": row[0], "path": row[1], "sector": row[2]}
```

---

## Configuration Reference

```yaml
search:
  # Hybrid search settings
  vector_weight: 0.6              # 0.0-1.0, weight for vector results in RRF
  fts5_weight: 0.4                # 0.0-1.0, weight for FTS5 results in RRF
  rrf_k: 60                       # RRF constant, higher = less top-rank advantage

  # Vector search settings
  vector:
    similarity_threshold: 0.5     # minimum cosine similarity to include
    max_candidates: 50            # fetch more candidates than final limit for better fusion

  # FTS5 settings
  fts5:
    tokenizer: "porter unicode61" # stemming + unicode support
    max_candidates: 50

  # Result settings
  max_results: 10                 # final number of results returned
  include_metadata: true          # return document metadata with results
  deduplicate: true               # remove duplicate chunks from same document
```

---

## Performance Expectations

Benchmarks on a typical development machine (Intel i7, 32GB RAM, NVMe SSD):

| Corpus Size | FTS5 Latency | Vector Latency | Hybrid Total | Index Size |
|-------------|-------------|----------------|--------------|------------|
| 1,000 chunks | <1ms | 2-5ms | 5-10ms | ~5 MB |
| 10,000 chunks | 1-3ms | 10-20ms | 15-30ms | ~50 MB |
| 100,000 chunks | 3-10ms | 50-100ms | 60-120ms | ~500 MB |
| 1,000,000 chunks | 10-30ms | 200-500ms | 250-600ms | ~5 GB |

For a marketing agency knowledge base, you will likely have 10,000-50,000 chunks across all sectors, keeping hybrid search well under 100ms.

---

## When to Use Which Search Mode

| Scenario | Recommended Mode | Why |
|----------|-----------------|-----|
| "What do we know about HVAC marketing?" | Hybrid (default) | Combines semantic understanding with keyword matching |
| "Find the email from John about the solar proposal" | FTS5 only | Exact name and keyword matching is critical |
| "What strategies work for businesses like plumbers?" | Vector only | Semantic similarity to find related content about similar businesses |
| "project ID jitawzicdwgbhatvjblh" | FTS5 only | Exact string match required |
| "Show me everything related to lead generation costs" | Hybrid | "lead generation costs" benefits from both semantic and keyword matching |
| "What did we decide about the database schema last Tuesday?" | FTS5 first, then hybrid | Date + specific terms first, semantic if not enough results |

OpenClaw agents should default to hybrid search and only switch to single-mode when the query characteristics strongly favor one approach.

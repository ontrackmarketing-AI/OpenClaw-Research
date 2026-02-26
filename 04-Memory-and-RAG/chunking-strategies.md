# Chunking Strategies for RAG

## Why Chunking Matters

Embedding models and LLM context windows work best with focused, coherent pieces of text. A 10,000-word marketing guide embedded as a single vector produces a vague, unfocused embedding that matches everything weakly and nothing strongly. Split that same guide into 20 focused chunks of 500 words each, and each chunk produces a sharp embedding that matches relevant queries precisely.

Chunking is the process of splitting documents into these smaller pieces before embedding. The quality of your chunks directly determines the quality of your RAG retrieval.

**Bad chunking leads to:**
- Retrieving chunks that partially match but lack the critical context.
- Missing relevant information because it was split across two chunks.
- Wasting context window space on chunks with padding/boilerplate.
- Inconsistent retrieval quality across different document types.

**Good chunking leads to:**
- Each chunk is self-contained and answers a specific question.
- Relevant information is found reliably.
- Context window is used efficiently (only relevant content retrieved).
- Consistent performance across document types.

---

## Chunking Methods

### 1. Fixed-Size Chunking

Split text every N characters or tokens, regardless of content boundaries.

```python
def fixed_size_chunk(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # overlap for continuity
    return chunks
```

| Pros | Cons |
|------|------|
| Simplest to implement | Cuts sentences and paragraphs mid-thought |
| Predictable chunk sizes | Context lost at boundaries even with overlap |
| Fast processing | Quality varies wildly depending on where cuts fall |
| Works for any content | Headers and metadata may end up in wrong chunk |

**When to use:** Prototyping, or when document structure is completely unpredictable.

**When to avoid:** Production knowledge bases, structured documents, anything where context matters.

---

### 2. Sentence-Based Chunking

Split on sentence boundaries, grouping sentences until the chunk reaches a target size.

```python
import re

def sentence_chunk(text: str, max_tokens: int = 512, overlap_sentences: int = 2) -> list[str]:
    """Split text into chunks at sentence boundaries."""
    # Split into sentences (handles Mr., Dr., etc.)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_tokens = len(sentence.split())

        if current_size + sentence_tokens > max_tokens and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep last N sentences for overlap
            current_chunk = current_chunk[-overlap_sentences:] if overlap_sentences > 0 else []
            current_size = sum(len(s.split()) for s in current_chunk)

        current_chunk.append(sentence)
        current_size += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
```

| Pros | Cons |
|------|------|
| Never cuts mid-sentence | Chunk sizes vary more than fixed-size |
| Better coherence than fixed-size | Doesn't respect paragraph/section boundaries |
| Overlap at sentence level is natural | Long sentences can cause oversized chunks |
| Easy to implement | Still may split related paragraphs apart |

**When to use:** General-purpose text content, blog posts, articles.

---

### 3. Paragraph-Based Chunking

Split on paragraph breaks (double newlines), grouping paragraphs until the chunk reaches a target size.

```python
def paragraph_chunk(text: str, max_tokens: int = 1024, overlap_paragraphs: int = 1) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para_tokens = len(para.split())

        if current_size + para_tokens > max_tokens and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = current_chunk[-overlap_paragraphs:] if overlap_paragraphs > 0 else []
            current_size = sum(len(p.split()) for p in current_chunk)

        current_chunk.append(para)
        current_size += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
```

| Pros | Cons |
|------|------|
| Respects natural content structure | Paragraphs can vary widely in length |
| High coherence per chunk | Very short paragraphs may create tiny chunks |
| Good for well-structured documents | Does not handle header hierarchies |
| Authors already organized thoughts by paragraph | |

**When to use:** Marketing copy, case studies, well-formatted articles.

---

### 4. Semantic Chunking

Split when the topic changes, detected by measuring embedding similarity between consecutive segments.

```python
import numpy as np

def semantic_chunk(
    text: str,
    embed_fn,
    similarity_threshold: float = 0.75,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1024,
) -> list[str]:
    """
    Split text where topic changes, detected by embedding similarity.

    Args:
        text: Input text.
        embed_fn: Function that returns an embedding vector for a string.
        similarity_threshold: Below this, consider it a topic change.
        min_chunk_size: Minimum words per chunk (prevents tiny chunks).
        max_chunk_size: Maximum words per chunk (forces split even without topic change).
    """
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    if len(sentences) <= 1:
        return [text]

    # Get embeddings for each sentence
    embeddings = [embed_fn(s) for s in sentences]

    # Find topic boundaries
    chunks = []
    current_chunk = [sentences[0]]
    current_size = len(sentences[0].split())

    for i in range(1, len(sentences)):
        # Compute similarity between current sentence and previous
        sim = np.dot(embeddings[i], embeddings[i-1]) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i-1])
        )

        sentence_size = len(sentences[i].split())

        # Split if topic changed AND chunk is large enough, OR chunk is too large
        if (sim < similarity_threshold and current_size >= min_chunk_size) or \
           (current_size + sentence_size > max_chunk_size):
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
            current_size = sentence_size
        else:
            current_chunk.append(sentences[i])
            current_size += sentence_size

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
```

| Pros | Cons |
|------|------|
| Highest quality chunks (topic-coherent) | Requires embedding every sentence (slow, expensive) |
| Adapts to content structure automatically | Similarity threshold requires tuning |
| Best retrieval quality in benchmarks | Most complex to implement |
| Content-aware splitting | Embedding model affects chunking quality |

**When to use:** High-value knowledge bases where retrieval quality justifies the extra compute cost. Good for sector knowledge bases that will be queried repeatedly.

---

### 5. Recursive Character Splitting (LangChain Approach)

Try multiple separators in priority order: first try section headers, then paragraphs, then sentences, then words.

```python
def recursive_chunk(
    text: str,
    max_size: int = 512,
    overlap: int = 50,
    separators: list[str] = None,
) -> list[str]:
    """
    Recursively split text trying multiple separators.
    LangChain-style recursive character text splitter.
    """
    if separators is None:
        separators = [
            "\n## ",      # Markdown H2 headers
            "\n### ",     # Markdown H3 headers
            "\n\n",       # Paragraph breaks
            "\n",         # Line breaks
            ". ",         # Sentences
            " ",          # Words (last resort)
        ]

    def _split(text: str, sep_index: int = 0) -> list[str]:
        if len(text.split()) <= max_size:
            return [text.strip()] if text.strip() else []

        if sep_index >= len(separators):
            # Fallback: force split at max_size
            words = text.split()
            return [" ".join(words[i:i+max_size]) for i in range(0, len(words), max_size - overlap)]

        separator = separators[sep_index]
        parts = text.split(separator)

        if len(parts) == 1:
            # This separator didn't split anything; try the next one
            return _split(text, sep_index + 1)

        # Group parts into chunks that fit within max_size
        chunks = []
        current = []
        current_size = 0

        for part in parts:
            part_size = len(part.split())
            if current_size + part_size > max_size and current:
                chunks.append(separator.join(current))
                current = []
                current_size = 0

            if part_size > max_size:
                # This part is still too large; recurse with next separator
                if current:
                    chunks.append(separator.join(current))
                    current = []
                    current_size = 0
                chunks.extend(_split(part, sep_index + 1))
            else:
                current.append(part)
                current_size += part_size

        if current:
            chunks.append(separator.join(current))

        return [c.strip() for c in chunks if c.strip()]

    return _split(text)
```

| Pros | Cons |
|------|------|
| Adapts to document structure | More complex logic |
| Tries to preserve highest-level structure first | Separator list needs tuning per content type |
| Good default behavior for mixed content | May produce inconsistent chunk sizes |
| Battle-tested (widely used in LangChain/LlamaIndex) | |

**When to use:** General-purpose default for most content types. A solid choice when you don't know the document structure in advance.

---

## Recommended Settings

### The Sweet Spot: 512-1024 Tokens

Based on benchmarks across RAG systems:

| Chunk Size | Precision | Recall | Best For |
|-----------|-----------|--------|----------|
| 128 tokens | High | Low | Very specific factoid retrieval |
| 256 tokens | High | Medium | Short-form content, Q&A pairs |
| **512 tokens** | **Good** | **Good** | **General-purpose RAG (recommended default)** |
| **1024 tokens** | **Good** | **High** | **Longer documents, technical content** |
| 2048 tokens | Medium | High | Long-form analysis, but context window cost is high |

### Overlap Settings

Overlap ensures that information near chunk boundaries is not lost.

| Overlap | Effect | Recommendation |
|---------|--------|----------------|
| 0 tokens | Clean boundaries, risk missing context | Only if chunks are naturally bounded (headers, sections) |
| 50 tokens | Minimal safety net | Good for sentence-based chunking |
| **100 tokens** | **Good balance** | **Recommended default** |
| 200 tokens | Maximum context preservation | Use for critical knowledge where missing anything is costly |

**Rule of thumb:** Set overlap to 10-20% of chunk size.

---

## Chunking by Content Type

Different types of content in your marketing knowledge base need different chunking strategies.

### Marketing Copy (Blog posts, ad copy, landing pages)

```python
MARKETING_CONFIG = {
    "method": "paragraph",
    "max_tokens": 512,
    "overlap": 50,
    "separators": ["\n\n", "\n", ". "],
    "rationale": "Marketing copy is organized by persuasion points, each paragraph "
                 "typically covers one idea. 512 tokens captures a complete thought."
}
```

### Technical Documentation (Setup guides, API docs, process docs)

```python
TECHNICAL_CONFIG = {
    "method": "recursive",
    "max_tokens": 1024,
    "overlap": 100,
    "separators": ["\n## ", "\n### ", "\n\n", "\n", ". "],
    "rationale": "Technical docs have clear header hierarchy. Larger chunks preserve "
                 "step-by-step context. Headers are the best split points."
}
```

### Client Communications (Emails, meeting notes, chat logs)

```python
COMMUNICATION_CONFIG = {
    "method": "sentence",
    "max_tokens": 256,
    "overlap": 30,
    "separators": ["\n\n", "\n", ". "],
    "rationale": "Communications are often short and each message is self-contained. "
                 "Smaller chunks prevent mixing different conversation threads."
}
```

### Case Studies (Success stories, results reports)

```python
CASE_STUDY_CONFIG = {
    "method": "recursive",
    "max_tokens": 1024,
    "overlap": 100,
    "separators": ["\n## ", "\n### ", "\n\n"],
    "rationale": "Case studies have clear sections (situation, action, result). "
                 "Keeping each section as one chunk preserves the narrative."
}
```

### Sector Knowledge (Pain points, benchmarks, channel data)

```python
SECTOR_CONFIG = {
    "method": "paragraph",
    "max_tokens": 512,
    "overlap": 50,
    "separators": ["\n## ", "\n### ", "\n\n", "\n- "],
    "rationale": "Sector knowledge is often in bullet/list format. Each logical "
                 "group (a pain point + its context) should stay together."
}
```

---

## Metadata Preservation

Every chunk must carry metadata from its source document. Without metadata, you cannot trace a search result back to its origin or filter by category.

### Required Metadata Per Chunk

```python
chunk_metadata = {
    # Source tracking
    "source_path": "knowledge/smb-local-services/pain-points.md",
    "source_title": "SMB Local Services - Common Pain Points",
    "chunk_index": 3,           # 0-indexed position within the document
    "total_chunks": 12,         # total chunks from this document

    # Content classification
    "sector": "smb-local-services",
    "doc_type": "knowledge",    # knowledge, case_study, template, compliance
    "content_type": "pain_points",

    # Temporal
    "created_at": "2026-02-05",
    "updated_at": "2026-02-05",

    # Quality
    "token_count": 487,
    "content_hash": "a1b2c3d4...",  # for change detection
}
```

### How Metadata Is Stored

In SQLite:
```sql
INSERT INTO chunks (document_id, chunk_index, content, embedding, token_count)
VALUES (?, ?, ?, ?, ?);
-- Document-level metadata lives in the documents table
-- Chunk-level metadata lives in the chunks table
```

In Supabase:
```sql
INSERT INTO documents (content, embedding, metadata, sector)
VALUES ($1, $2, $3::jsonb, $4);
-- The JSONB metadata column holds flexible key-value pairs
```

---

## Tools and Libraries

### Python Libraries

| Library | Chunking Method | Best For |
|---------|----------------|----------|
| **LangChain** `RecursiveCharacterTextSplitter` | Recursive with configurable separators | General purpose, most flexible |
| **LangChain** `MarkdownHeaderTextSplitter` | Split on markdown headers | Structured markdown documents |
| **LlamaIndex** `SentenceSplitter` | Sentence-aware with overlap | Clean sentence boundaries |
| **LlamaIndex** `SemanticSplitterNodeParser` | Embedding-based semantic splitting | Highest quality, slower |
| **tiktoken** | Token counting for any OpenAI-compatible model | Accurate token measurement |
| Custom Python (examples above) | Any method | Full control, no dependencies |

### Quick Start with LangChain

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,             # target chunk size in characters
    chunk_overlap=100,          # overlap between chunks
    length_function=len,        # or use tiktoken for token counting
    separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
)

text = open("knowledge/smb-local-services/pain-points.md").read()
chunks = splitter.split_text(text)

# With metadata
from langchain.schema import Document
docs = splitter.split_documents([
    Document(page_content=text, metadata={"sector": "smb-local-services", "type": "pain_points"})
])
# Each resulting doc inherits and extends the metadata
```

### Quick Start with LlamaIndex

```python
from llama_index.core.node_parser import SentenceSplitter

parser = SentenceSplitter(
    chunk_size=512,
    chunk_overlap=100,
)

nodes = parser.get_nodes_from_documents(documents)
# Each node has text + metadata
```

---

## Testing Your Chunking

Before committing to a chunking strategy for a sector knowledge base, test it:

### Manual Review

```python
def review_chunks(chunks: list[str]):
    """Print chunks with separators for manual review."""
    for i, chunk in enumerate(chunks):
        print(f"\n{'='*60}")
        print(f"CHUNK {i+1} ({len(chunk.split())} words)")
        print(f"{'='*60}")
        print(chunk[:500])
        if len(chunk) > 500:
            print(f"... [{len(chunk) - 500} more characters]")
```

### Quality Checks

```python
def validate_chunks(chunks: list[str], min_words: int = 20, max_words: int = 1200):
    """Validate chunk quality."""
    issues = []
    for i, chunk in enumerate(chunks):
        word_count = len(chunk.split())
        if word_count < min_words:
            issues.append(f"Chunk {i}: too small ({word_count} words)")
        if word_count > max_words:
            issues.append(f"Chunk {i}: too large ({word_count} words)")
        if not chunk.strip():
            issues.append(f"Chunk {i}: empty")
        if chunk.strip().startswith(("- ", "* ", "| ")):
            issues.append(f"Chunk {i}: starts with list/table fragment (possible incomplete context)")

    if issues:
        print(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"All {len(chunks)} chunks passed validation.")

    # Statistics
    word_counts = [len(c.split()) for c in chunks]
    print(f"\nStatistics:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Min words: {min(word_counts)}")
    print(f"  Max words: {max(word_counts)}")
    print(f"  Avg words: {sum(word_counts) / len(word_counts):.0f}")
    print(f"  Median words: {sorted(word_counts)[len(word_counts)//2]}")
```

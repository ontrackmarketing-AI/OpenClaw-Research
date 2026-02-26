# Knowledge Ingestion Pipeline

## Pipeline Overview

Ingestion is the process of taking raw content (PDFs, web pages, markdown files, spreadsheets) and transforming it into searchable, embedded chunks stored in the vector database. Every document in the OpenClaw knowledge base passes through this pipeline.

```
Source Document
    |
    v
[1. EXTRACT] -- Pull text content from the source format
    |
    v
[2. CLEAN] -- Remove boilerplate, normalize formatting, extract metadata
    |
    v
[3. CHUNK] -- Split into appropriately-sized pieces (see chunking-strategies.md)
    |
    v
[4. EMBED] -- Generate vector embeddings for each chunk (see embedding-models.md)
    |
    v
[5. STORE] -- Write chunks + embeddings to SQLite and/or Supabase
    |
    v
[6. INDEX] -- Update FTS5 full-text index and metadata tables
    |
    v
[7. VERIFY] -- Quality checks: no empty chunks, embeddings valid, metadata complete
```

---

## Supported Source Formats

### PDF Documents

Industry reports, compliance guides, printed case studies, contracts.

**Library: PyMuPDF (fitz)**

```python
import fitz  # pip install pymupdf

def extract_pdf(file_path: str) -> dict:
    """Extract text and metadata from a PDF file."""
    doc = fitz.open(file_path)
    pages = []
    full_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({
            "page_number": page_num + 1,
            "text": text,
            "word_count": len(text.split()),
        })
        full_text.append(text)

    metadata = {
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "page_count": len(doc),
        "source_path": file_path,
        "format": "pdf",
    }

    doc.close()
    return {
        "text": "\n\n".join(full_text),
        "pages": pages,
        "metadata": metadata,
    }
```

**Alternative: pdfplumber** (better for tables and structured PDFs)

```python
import pdfplumber  # pip install pdfplumber

def extract_pdf_tables(file_path: str) -> list[dict]:
    """Extract tables from PDF as structured data."""
    tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_tables = page.extract_tables()
            for table in page_tables:
                tables.append({
                    "page": page.page_number,
                    "headers": table[0] if table else [],
                    "rows": table[1:] if table else [],
                })
    return tables
```

---

### Web Pages

Blog posts, competitor sites, industry articles, documentation.

**Library: Playwright + Readability**

```python
from playwright.sync_api import sync_playwright
from readability import Document as ReadabilityDoc  # pip install readability-lxml
import html2text

def extract_webpage(url: str) -> dict:
    """Extract clean text content from a web page."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=30000)

        # Get the full HTML
        html_content = page.content()
        title = page.title()

        browser.close()

    # Use readability to extract main content (removes nav, sidebar, ads)
    doc = ReadabilityDoc(html_content)
    clean_html = doc.summary()

    # Convert HTML to markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.body_width = 0  # no wrapping
    markdown_text = h.handle(clean_html)

    return {
        "text": markdown_text,
        "metadata": {
            "title": title or doc.title(),
            "source_url": url,
            "format": "web",
            "extracted_at": datetime.now().isoformat(),
        },
    }
```

**Simpler alternative for static pages:**

```python
import requests
from bs4 import BeautifulSoup

def extract_simple_webpage(url: str) -> dict:
    """Extract text from a simple web page without JavaScript rendering."""
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    text = soup.get_text(separator="\n", strip=True)
    title = soup.title.string if soup.title else ""

    return {
        "text": text,
        "metadata": {"title": title, "source_url": url, "format": "web"},
    }
```

---

### Markdown Files

Knowledge base documents, session logs, notes. The native format for OpenClaw.

```python
import re
from pathlib import Path

def extract_markdown(file_path: str) -> dict:
    """Extract text and metadata from a markdown file."""
    content = Path(file_path).read_text(encoding="utf-8")

    # Extract YAML frontmatter if present
    metadata = {}
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if frontmatter_match:
        import yaml
        metadata = yaml.safe_load(frontmatter_match.group(1)) or {}
        content = content[frontmatter_match.end():]

    # Extract title from first H1 header
    title_match = re.match(r'^#\s+(.+)', content, re.MULTILINE)
    if title_match and "title" not in metadata:
        metadata["title"] = title_match.group(1).strip()

    metadata["source_path"] = file_path
    metadata["format"] = "markdown"

    return {
        "text": content,
        "metadata": metadata,
    }
```

---

### Google Docs

Client-shared documents, collaborative proposals, strategy docs.

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def extract_google_doc(doc_id: str, credentials: Credentials) -> dict:
    """Extract text from a Google Doc via API."""
    service = build("docs", "v1", credentials=credentials)
    doc = service.documents().get(documentId=doc_id).execute()

    # Extract text from document body
    text_parts = []
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            for text_run in element["paragraph"].get("elements", []):
                if "textRun" in text_run:
                    text_parts.append(text_run["textRun"]["content"])

    return {
        "text": "".join(text_parts),
        "metadata": {
            "title": doc.get("title", ""),
            "doc_id": doc_id,
            "format": "google_doc",
        },
    }
```

---

### CSV / Excel Files

Pricing data, lead lists, campaign performance exports, benchmarks.

```python
import pandas as pd

def extract_csv(file_path: str, text_columns: list[str] = None) -> dict:
    """
    Extract searchable text from a CSV or Excel file.

    Converts each row into a text representation suitable for embedding.
    """
    if file_path.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    # If no text columns specified, use all string columns
    if text_columns is None:
        text_columns = df.select_dtypes(include=['object']).columns.tolist()

    # Convert each row to a searchable text block
    rows_as_text = []
    for _, row in df.iterrows():
        parts = []
        for col in df.columns:
            value = row[col]
            if pd.notna(value):
                parts.append(f"{col}: {value}")
        rows_as_text.append(" | ".join(parts))

    return {
        "text": "\n".join(rows_as_text),
        "metadata": {
            "source_path": file_path,
            "format": "csv" if file_path.endswith('.csv') else "excel",
            "row_count": len(df),
            "columns": list(df.columns),
        },
        "dataframe": df,  # keep structured data for direct queries
    }
```

---

### Email (IMAP Extraction)

Client communications, support threads, sales conversations.

```python
import imaplib
import email
from email.header import decode_header

def extract_emails(
    imap_server: str,
    username: str,
    password: str,
    folder: str = "INBOX",
    search_criteria: str = "ALL",
    max_emails: int = 100,
) -> list[dict]:
    """Extract emails from an IMAP mailbox."""
    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(username, password)
    mail.select(folder)

    _, message_numbers = mail.search(None, search_criteria)
    email_ids = message_numbers[0].split()[-max_emails:]  # most recent N

    emails = []
    for eid in email_ids:
        _, msg_data = mail.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="replace")

        emails.append({
            "text": f"Subject: {subject}\nFrom: {msg['From']}\nDate: {msg['Date']}\n\n{body}",
            "metadata": {
                "subject": subject,
                "from": msg["From"],
                "to": msg["To"],
                "date": msg["Date"],
                "format": "email",
            },
        })

    mail.close()
    mail.logout()
    return emails
```

---

## Extraction and Cleaning

### Standard Cleaning Pipeline

```python
import re

def clean_text(text: str) -> str:
    """
    Standard text cleaning for ingestion.
    Removes noise while preserving meaningful content.
    """
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)     # max 2 consecutive newlines
    text = re.sub(r' {2,}', ' ', text)          # max 1 consecutive space
    text = re.sub(r'\t', ' ', text)             # tabs to spaces

    # Remove common boilerplate patterns
    boilerplate_patterns = [
        r'Cookie\s+Policy.*?Accept',                           # cookie banners
        r'Subscribe to our newsletter.*?(?=\n\n)',             # newsletter CTAs
        r'Copyright \d{4}.*?All rights reserved\.?',           # copyright notices
        r'Share this (article|post|page).*?(?=\n)',            # social sharing
        r'Tags:.*?(?=\n)',                                      # tag lists
        r'Related (Articles|Posts|Content).*?(?=\n\n|\Z)',     # related content
        r'Comments \(\d+\).*?(?=\n\n|\Z)',                     # comment sections
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Normalize Unicode
    import unicodedata
    text = unicodedata.normalize('NFKC', text)

    # Remove null bytes and control characters (except newlines)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()
```

### Metadata Extraction

```python
from datetime import datetime

def extract_metadata(text: str, source_info: dict) -> dict:
    """Extract structured metadata from document text and source info."""
    metadata = {
        "source_path": source_info.get("source_path", ""),
        "source_url": source_info.get("source_url", ""),
        "format": source_info.get("format", "unknown"),
        "title": source_info.get("title", ""),
        "ingested_at": datetime.now().isoformat(),
        "word_count": len(text.split()),
        "char_count": len(text),
    }

    # Try to detect the date from content
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',                    # ISO date
        r'(\w+ \d{1,2},? \d{4})',                   # "January 15, 2026"
        r'(\d{1,2}/\d{1,2}/\d{4})',                 # MM/DD/YYYY
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text[:500])  # check first 500 chars
        if match:
            metadata["content_date"] = match.group(1)
            break

    # Detect author if possible
    author_patterns = [
        r'[Bb]y\s+([A-Z][a-z]+ [A-Z][a-z]+)',     # "By John Smith"
        r'[Aa]uthor:\s*(.+?)(?:\n|$)',               # "Author: John Smith"
    ]
    for pattern in author_patterns:
        match = re.search(pattern, text[:1000])
        if match:
            metadata["author"] = match.group(1).strip()
            break

    return metadata
```

---

## Batch Ingestion

Process multiple documents at once, with progress tracking and error handling.

```python
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class IngestionResult:
    path: str
    status: str           # 'success', 'skipped', 'error'
    chunks_created: int
    error_message: Optional[str] = None

class BatchIngester:
    def __init__(self, db, embed_fn, chunker, sector: str):
        self.db = db
        self.embed_fn = embed_fn
        self.chunker = chunker
        self.sector = sector
        self.results: list[IngestionResult] = []

    def ingest_directory(self, directory: str, pattern: str = "**/*.md") -> list[IngestionResult]:
        """
        Ingest all matching files from a directory.

        Args:
            directory: Path to the directory containing source documents.
            pattern: Glob pattern for files to ingest.

        Returns:
            List of IngestionResult for each file processed.
        """
        files = sorted(Path(directory).glob(pattern))
        total = len(files)
        print(f"Found {total} files to process in {directory}")

        for i, file_path in enumerate(files, 1):
            try:
                result = self._ingest_single(str(file_path))
                self.results.append(result)
                status_icon = {
                    "success": "+",
                    "skipped": "=",
                    "error": "!",
                }[result.status]
                print(f"  [{i}/{total}] {status_icon} {file_path.name} "
                      f"({result.chunks_created} chunks)")
            except Exception as e:
                result = IngestionResult(
                    path=str(file_path),
                    status="error",
                    chunks_created=0,
                    error_message=str(e),
                )
                self.results.append(result)
                print(f"  [{i}/{total}] ! {file_path.name} ERROR: {e}")

        # Summary
        success = sum(1 for r in self.results if r.status == "success")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        errors = sum(1 for r in self.results if r.status == "error")
        total_chunks = sum(r.chunks_created for r in self.results)
        print(f"\nDone: {success} ingested, {skipped} skipped, {errors} errors, "
              f"{total_chunks} total chunks")

        return self.results

    def _ingest_single(self, file_path: str) -> IngestionResult:
        """Ingest a single file."""
        # Read and hash content
        content = Path(file_path).read_text(encoding="utf-8")
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if already ingested with same content
        existing = self.db.execute(
            "SELECT id FROM documents WHERE path = ? AND content_hash = ?",
            [file_path, content_hash]
        ).fetchone()

        if existing:
            return IngestionResult(path=file_path, status="skipped", chunks_created=0)

        # Clean content
        cleaned = clean_text(content)
        metadata = extract_metadata(cleaned, {"source_path": file_path, "format": "markdown"})

        # Chunk
        chunks = self.chunker(cleaned)

        # Delete old version if content changed
        self.db.execute("DELETE FROM documents WHERE path = ?", [file_path])

        # Insert document record
        cursor = self.db.execute(
            "INSERT INTO documents (path, content_hash, title, doc_type, sector, token_count) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [file_path, content_hash, metadata.get("title", ""),
             "knowledge", self.sector, metadata["word_count"]]
        )
        doc_id = cursor.lastrowid

        # Embed and store chunks
        for idx, chunk_text in enumerate(chunks):
            embedding = self.embed_fn(chunk_text)
            self.db.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, embedding, token_count) "
                "VALUES (?, ?, ?, ?, ?)",
                [doc_id, idx, chunk_text, embedding.tobytes(), len(chunk_text.split())]
            )
            # sqlite-vec insert
            chunk_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
            self.db.execute(
                "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
                [chunk_id, embedding.tobytes()]
            )

        self.db.commit()
        return IngestionResult(path=file_path, status="success", chunks_created=len(chunks))
```

---

## Incremental Updates

Only re-process documents that have actually changed. This saves time and embedding costs.

### Change Detection Strategy

```python
def detect_changes(db, directory: str, pattern: str = "**/*.md") -> dict:
    """
    Compare filesystem state with database state to find changes.

    Returns:
        {
            "new": [list of new file paths],
            "modified": [list of modified file paths],
            "deleted": [list of deleted file paths (in DB but not on disk)],
            "unchanged": [list of unchanged file paths],
        }
    """
    # Get current files on disk
    disk_files = {}
    for path in Path(directory).glob(pattern):
        content = path.read_text(encoding="utf-8")
        disk_files[str(path)] = hashlib.sha256(content.encode()).hexdigest()

    # Get indexed files from database
    db_files = {}
    for row in db.execute("SELECT path, content_hash FROM documents").fetchall():
        db_files[row[0]] = row[1]

    changes = {
        "new": [],
        "modified": [],
        "deleted": [],
        "unchanged": [],
    }

    # Check disk files against database
    for path, disk_hash in disk_files.items():
        if path not in db_files:
            changes["new"].append(path)
        elif db_files[path] != disk_hash:
            changes["modified"].append(path)
        else:
            changes["unchanged"].append(path)

    # Check for deleted files (in DB but not on disk)
    for path in db_files:
        if path not in disk_files:
            changes["deleted"].append(path)

    print(f"Changes detected: {len(changes['new'])} new, "
          f"{len(changes['modified'])} modified, "
          f"{len(changes['deleted'])} deleted, "
          f"{len(changes['unchanged'])} unchanged")

    return changes
```

### Applying Incremental Updates

```python
def incremental_update(db, embed_fn, chunker, directory: str, sector: str):
    """Run incremental update: only process new and modified files."""
    changes = detect_changes(db, directory)

    ingester = BatchIngester(db, embed_fn, chunker, sector)

    # Process new files
    for path in changes["new"]:
        ingester._ingest_single(path)

    # Re-process modified files (delete old, insert new)
    for path in changes["modified"]:
        ingester._ingest_single(path)  # handles delete+reinsert internally

    # Remove deleted files from index
    for path in changes["deleted"]:
        db.execute("DELETE FROM documents WHERE path = ?", [path])

    db.commit()
    print(f"Incremental update complete for sector '{sector}'")
```

---

## Quality Checks

After ingestion, verify the data is valid and complete.

```python
def verify_ingestion(db, sector: str = None):
    """Run quality checks on ingested data."""
    issues = []
    warnings = []

    # Check 1: Empty chunks
    where_clause = f"AND d.sector = '{sector}'" if sector else ""
    empty = db.execute(f"""
        SELECT COUNT(*) FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE (c.content IS NULL OR c.content = '' OR length(c.content) < 10)
        {where_clause}
    """).fetchone()[0]
    if empty > 0:
        issues.append(f"{empty} empty or near-empty chunks found")

    # Check 2: Missing embeddings
    no_embedding = db.execute(f"""
        SELECT COUNT(*) FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.embedding IS NULL
        {where_clause}
    """).fetchone()[0]
    if no_embedding > 0:
        issues.append(f"{no_embedding} chunks without embeddings")

    # Check 3: Embedding dimension consistency
    sample = db.execute("""
        SELECT length(embedding) / 4 as dims FROM chunks
        WHERE embedding IS NOT NULL LIMIT 100
    """).fetchall()
    dims = set(row[0] for row in sample)
    if len(dims) > 1:
        issues.append(f"Inconsistent embedding dimensions: {dims}")

    # Check 4: FTS5 sync
    total_chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    total_fts = db.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    if total_chunks != total_fts:
        issues.append(f"FTS5 out of sync: {total_chunks} chunks vs {total_fts} FTS entries")

    # Check 5: Orphaned chunks (no parent document)
    orphaned = db.execute("""
        SELECT COUNT(*) FROM chunks c
        LEFT JOIN documents d ON d.id = c.document_id
        WHERE d.id IS NULL
    """).fetchone()[0]
    if orphaned > 0:
        warnings.append(f"{orphaned} orphaned chunks (no parent document)")

    # Check 6: Very large chunks
    oversized = db.execute(f"""
        SELECT COUNT(*) FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.token_count > 2000
        {where_clause}
    """).fetchone()[0]
    if oversized > 0:
        warnings.append(f"{oversized} chunks exceed 2000 tokens (may reduce retrieval quality)")

    # Report
    if issues:
        print(f"ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"  [ERROR] {issue}")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [WARN] {w}")
    if not issues and not warnings:
        print("All quality checks passed.")

    # Stats
    stats = db.execute(f"""
        SELECT
            COUNT(DISTINCT d.id) as doc_count,
            COUNT(c.id) as chunk_count,
            SUM(c.token_count) as total_tokens,
            AVG(c.token_count) as avg_chunk_tokens
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        {f"WHERE d.sector = '{sector}'" if sector else ""}
    """).fetchone()
    print(f"\nStats: {stats[0]} documents, {stats[1]} chunks, "
          f"{stats[2] or 0:,.0f} total tokens, {stats[3] or 0:.0f} avg tokens/chunk")
```

---

## OpenClaw Integration

### As an OpenClaw Skill

Ingestion can be exposed as an OpenClaw skill that agents or users can trigger:

```yaml
# ~/.openclaw/skills/ingest.yaml
name: ingest
description: Ingest documents into the knowledge base
triggers:
  - "ingest"
  - "add to knowledge base"
  - "index documents"
parameters:
  - name: source
    description: Path to file or directory to ingest
    required: true
  - name: sector
    description: Sector to assign (e.g., smb-local-services, solar-home-improvement)
    required: true
  - name: format
    description: Source format (auto-detected if not specified)
    required: false
```

### As a Scheduled Job (n8n)

Set up an n8n workflow to run ingestion on a schedule:

1. **Schedule Trigger:** Run daily at 2 AM.
2. **List Files:** Check monitored directories for new/changed files.
3. **For Each Changed File:**
   - Extract text (based on format).
   - Clean and chunk.
   - Embed via Ollama API.
   - Store in SQLite and/or Supabase.
4. **Notification:** Send summary to Slack/email (N files processed, M errors).

---

## Monitoring

### Ingestion Status Dashboard

Track ingestion health with a simple status table:

```sql
CREATE TABLE ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,              -- UUID for this ingestion run
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    sector TEXT,
    files_processed INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    files_errored INTEGER DEFAULT 0,
    chunks_created INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT DEFAULT 'running',     -- 'running', 'completed', 'failed'
    error_log TEXT                     -- JSON array of error messages
);
```

### Error Logging

```python
import json
from uuid import uuid4

class IngestionMonitor:
    def __init__(self, db, sector: str):
        self.db = db
        self.sector = sector
        self.run_id = str(uuid4())
        self.errors = []
        self.start_time = time.time()

        self.db.execute(
            "INSERT INTO ingestion_log (run_id, sector) VALUES (?, ?)",
            [self.run_id, sector]
        )
        self.db.commit()

    def log_error(self, file_path: str, error: str):
        self.errors.append({"file": file_path, "error": error})

    def complete(self, files_processed, files_skipped, files_errored, chunks_created, total_tokens):
        duration = time.time() - self.start_time
        self.db.execute("""
            UPDATE ingestion_log SET
                completed_at = datetime('now'),
                files_processed = ?,
                files_skipped = ?,
                files_errored = ?,
                chunks_created = ?,
                total_tokens = ?,
                duration_seconds = ?,
                status = ?,
                error_log = ?
            WHERE run_id = ?
        """, [files_processed, files_skipped, files_errored, chunks_created,
              total_tokens, duration,
              "completed" if not self.errors else "completed_with_errors",
              json.dumps(self.errors) if self.errors else None,
              self.run_id])
        self.db.commit()
```

---

## Quick Start: Ingest a Sector Knowledge Base

Step-by-step to ingest the SMB Local Services sector:

```bash
# 1. Ensure Ollama is running with the embedding model
ollama pull nomic-embed-text
ollama serve  # if not already running

# 2. Create the sector directory with knowledge files
mkdir -p ~/.openclaw/memory/knowledge/smb-local-services/documents/
# Place your markdown files here (pain-points.md, channel-effectiveness.md, etc.)

# 3. Run the ingestion script
python ingest_sector.py --sector smb-local-services \
    --source ~/.openclaw/memory/knowledge/smb-local-services/documents/ \
    --db ~/.openclaw/memory/knowledge/smb-local-services/index.db \
    --model nomic-embed-text

# 4. Verify
python verify_ingestion.py --db ~/.openclaw/memory/knowledge/smb-local-services/index.db
```

Expected output:
```
Found 8 files to process
  [1/8] + pain-points.md (12 chunks)
  [2/8] + channel-effectiveness.md (8 chunks)
  [3/8] + pricing-benchmarks.md (6 chunks)
  ...
Done: 8 ingested, 0 skipped, 0 errors, 62 total chunks
All quality checks passed.
Stats: 8 documents, 62 chunks, 24,180 total tokens, 390 avg tokens/chunk
```

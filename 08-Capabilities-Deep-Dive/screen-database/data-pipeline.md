# Screen Database -- Data Pipeline (Windows to Mac Mini)

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Windows Capture Pipeline](windows-capture-pipeline.md), [Network Security](../../02-Security/network-security.md)

---

## 1. Pipeline Architecture Options

```
Option A: Windows -> Supabase (Direct Push)
+----------+     HTTPS      +----------+     Query      +---------+
| Windows  | -------------> | Supabase | <------------- | Mac Mini|
| Capture  |   (internet)   | pgvector |   (Supabase    | OpenClaw|
+----------+                +----------+    client)      +---------+

Option B: Windows -> Mac Mini (Tailscale Push)
+----------+   Tailscale    +---------+
| Windows  | -------------> | Mac Mini|
| Capture  |   (VPN mesh)   | REST API|
+----------+                | OpenClaw|
                            +---------+

Option C: Hybrid (Text to Supabase, Images Local)
+----------+     HTTPS      +----------+
| Windows  | -- text/meta ->| Supabase |
| Capture  |                +----------+
|          |   Tailscale     +---------+
|          | -- images ----->| Mac Mini|
+----------+   (on request)  +---------+
```

---

## 2. Recommended: Option A (Direct to Supabase)

**Why Supabase direct:**
- Simplest architecture -- no custom API on Mac Mini
- Supabase provides pgvector for embedding search natively
- Data available even if Mac Mini is offline
- Built-in REST API and real-time subscriptions
- Row-level security for access control

**Trade-off:** Requires internet from the Windows machine. Data transits to Supabase cloud. This is acceptable because OCR text is your own screen activity (not third-party PII).

### 2.1 Push Implementation

```python
# sync_to_supabase.py -- runs on Windows alongside capture service
import httpx
import sqlite3
import os
from datetime import datetime

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
LOCAL_DB = os.path.expanduser("~/AppData/Local/OpenClaw/screen_db.sqlite")

BATCH_SIZE = 50
SYNC_INTERVAL = 60  # seconds

async def sync_unsynced_captures():
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT id, timestamp, window_title, app_name, monitor_index,
               ocr_text, content_hash
        FROM captures
        WHERE synced = 0
        ORDER BY id ASC
        LIMIT ?
    """, (BATCH_SIZE,))

    rows = cursor.fetchall()
    if not rows:
        return 0

    # Batch insert to Supabase
    records = [{
        "captured_at": row["timestamp"],
        "window_title": row["window_title"],
        "app_name": row["app_name"],
        "monitor_index": row["monitor_index"],
        "ocr_text": row["ocr_text"],
        "content_hash": row["content_hash"],
        "source_device": "windows_desktop",
    } for row in rows]

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/screen_captures",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=records,
        )
        resp.raise_for_status()

    # Mark as synced
    ids = [row["id"] for row in rows]
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"UPDATE captures SET synced = 1 WHERE id IN ({placeholders})", ids)
    conn.commit()
    conn.close()

    return len(rows)
```

### 2.2 Sync Loop

```python
import asyncio

async def sync_loop():
    while True:
        try:
            count = await sync_unsynced_captures()
            if count > 0:
                print(f"Synced {count} captures to Supabase")
        except Exception as e:
            print(f"Sync error: {e}")
        await asyncio.sleep(SYNC_INTERVAL)
```

---

## 3. Alternative: Option B (Tailscale Push)

If internet from Windows is not available or you prefer keeping data off the cloud:

```python
# Push to Mac Mini over Tailscale
MAC_MINI_URL = "https://mac-mini.tailnet-name.ts.net:8200"

async def push_to_mac_mini(records: list):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MAC_MINI_URL}/api/screen-captures",
            json=records,
            timeout=30,
        )
        resp.raise_for_status()
```

This requires a small FastAPI endpoint on the Mac Mini to receive and store the data.

---

## 4. Embedding Generation

OCR text needs vector embeddings for semantic search ("What was I looking at when working on the budget?").

### 4.1 Where to Generate Embeddings

| Option | Where | Cost | Latency |
|--------|-------|------|---------|
| Ollama on Mac Mini | Mac Mini (local) | $0 | ~50ms per chunk |
| Supabase Edge Function | Supabase cloud | ~$0.001/embed | ~100ms |
| OpenAI API | Cloud | ~$0.002 per 1K tokens | ~200ms |

**Recommendation:** Generate embeddings on the Mac Mini using Ollama (nomic-embed-text). The sync service pushes raw text; a background job on the Mac Mini generates embeddings and updates Supabase.

### 4.2 Embedding Pipeline on Mac Mini

```python
# embed_screen_captures.py -- runs on Mac Mini
import httpx
import ollama

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

async def embed_unembedded_captures():
    """Fetch captures without embeddings, generate, and update."""
    # Fetch unembedded records
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/screen_captures",
            params={
                "embedding": "is.null",
                "limit": 50,
                "order": "captured_at.asc",
            },
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
        )
        records = resp.json()

    for record in records:
        # Generate embedding via Ollama
        text = f"{record['app_name']}: {record['window_title']}\n{record['ocr_text']}"
        embedding = ollama.embed(model="nomic-embed-text", input=text)

        # Update Supabase
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{SUPABASE_URL}/rest/v1/screen_captures",
                params={"id": f"eq.{record['id']}"},
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                },
                json={"embedding": embedding["embeddings"][0]},
            )
```

---

## 5. Data Volume Estimates

| Metric | Value |
|--------|-------|
| Captures per day (8 hrs, 30s interval) | ~960 (with dedup: ~500-700) |
| OCR text per capture | ~1-5 KB |
| Text per day | ~2-10 MB |
| Embedding per capture (768-dim float32) | ~3 KB |
| Embeddings per day | ~1.5-2 MB |
| **Total Supabase storage per day** | ~4-12 MB |
| **Total Supabase storage per month** | ~120-360 MB |
| JPEG images (local Windows only) | ~100-150 MB/day |

Supabase free tier (500 MB) covers approximately 1-4 months of OCR text + embeddings. Images stay on the Windows machine and are not synced to Supabase.

---

## 6. Offline Handling

If the Windows machine loses internet:

1. Captures continue locally (SQLite on Windows always works)
2. Sync queue builds up (`synced = 0` rows accumulate)
3. When connectivity resumes, sync loop catches up in batches
4. No data loss -- local SQLite is the source of truth

---

## 7. Network Security

- **Windows to Supabase:** HTTPS (TLS 1.3). Supabase service key stored in Windows environment variable.
- **Windows to Mac Mini (Option B):** Tailscale WireGuard tunnel. No internet exposure.
- **Mac Mini to Supabase:** HTTPS with service key. Same credentials as other OpenClaw Supabase access.

See [Network Security](../../02-Security/network-security.md) for Tailscale configuration.

---

## Next Steps

- [Storage & Indexing](storage-indexing.md) -- Supabase schema and search
- [Query Interface](query-interface.md) -- How OpenClaw queries screen data
- [Privacy & Security](privacy-security.md) -- Encryption and access control

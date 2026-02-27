# Windows Screen Capture Pipeline

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Tool Comparison](tool-comparison.md)

---

## 1. Architecture

```
Windows Desktop
+--------------------------------------------------+
|  Screen Capture Service (Python, runs as daemon)  |
|                                                    |
|  1. mss captures screenshot every N seconds        |
|  2. pygetwindow gets active window title + app     |
|  3. pytesseract extracts text via Tesseract OCR    |
|  4. Store in local SQLite (text + metadata)        |
|  5. Push to Mac Mini / Supabase on schedule        |
+--------------------------------------------------+
```

---

## 2. Core Implementation

### 2.1 Capture Service

```python
# screen_capture.py -- runs on Windows desktop
import mss
import pytesseract
from PIL import Image
import sqlite3
import time
import io
import hashlib
import os
from datetime import datetime

# Configuration
CAPTURE_INTERVAL = 30  # seconds
DB_PATH = os.path.expanduser("~/AppData/Local/OpenClaw/screen_db.sqlite")
IMAGE_DIR = os.path.expanduser("~/AppData/Local/OpenClaw/captures/")
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
JPEG_QUALITY = 75

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            window_title TEXT,
            app_name TEXT,
            monitor_index INTEGER DEFAULT 0,
            ocr_text TEXT,
            image_path TEXT,
            content_hash TEXT,
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS captures_fts
        USING fts5(ocr_text, window_title, app_name,
                   content='captures', content_rowid='id',
                   tokenize='porter unicode61')
    """)
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS captures_ai AFTER INSERT ON captures BEGIN
            INSERT INTO captures_fts(rowid, ocr_text, window_title, app_name)
            VALUES (new.id, new.ocr_text, new.window_title, new.app_name);
        END
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_captures_timestamp
        ON captures(timestamp DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_captures_app
        ON captures(app_name)
    """)
    conn.commit()
    return conn

def get_active_window():
    """Get active window title and application name."""
    try:
        import pygetwindow as gw
        active = gw.getActiveWindow()
        if active:
            title = active.title or ""
            # Extract app name from window title (heuristic)
            app_name = title.split(" - ")[-1] if " - " in title else title
            return title, app_name
    except Exception:
        pass
    return "", ""

def should_skip(app_name: str, window_title: str) -> bool:
    """Privacy filter: skip sensitive windows."""
    EXCLUDED_APPS = [
        "1Password", "Bitwarden", "KeePass", "LastPass",
        "Bank", "banking", "Chase", "Wells Fargo", "Capital One",
    ]
    EXCLUDED_TITLES = [
        "password", "credential", "private browsing",
        "incognito", "sign in", "log in",
    ]

    app_lower = app_name.lower()
    title_lower = window_title.lower()

    for excluded in EXCLUDED_APPS:
        if excluded.lower() in app_lower:
            return True
    for excluded in EXCLUDED_TITLES:
        if excluded in title_lower:
            return True
    return False

def capture_screen(sct, monitor_index=0):
    """Capture a screenshot and extract OCR text."""
    monitors = sct.monitors[1:]  # Skip the "all monitors" entry
    if monitor_index >= len(monitors):
        return None, None, None

    monitor = monitors[monitor_index]
    screenshot = sct.grab(monitor)

    # Convert to PIL Image
    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    # Save as JPEG for storage efficiency
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_mon{monitor_index}.jpg"
    filepath = os.path.join(IMAGE_DIR, filename)
    img.save(filepath, "JPEG", quality=JPEG_QUALITY)

    # OCR
    ocr_text = pytesseract.image_to_string(img)

    # Content hash (for dedup / change detection)
    content_hash = hashlib.md5(ocr_text.encode()).hexdigest()

    return ocr_text, filepath, content_hash

def capture_loop():
    conn = init_db()
    last_hash = None

    with mss.mss() as sct:
        while True:
            try:
                window_title, app_name = get_active_window()

                # Privacy filter
                if should_skip(app_name, window_title):
                    time.sleep(CAPTURE_INTERVAL)
                    continue

                # Capture primary monitor
                ocr_text, image_path, content_hash = capture_screen(sct, 0)

                if not ocr_text:
                    time.sleep(CAPTURE_INTERVAL)
                    continue

                # Skip if screen hasn't changed (same content hash)
                if content_hash == last_hash:
                    time.sleep(CAPTURE_INTERVAL)
                    continue
                last_hash = content_hash

                # Store
                conn.execute("""
                    INSERT INTO captures
                    (timestamp, window_title, app_name, monitor_index,
                     ocr_text, image_path, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now().isoformat(),
                    window_title, app_name, 0,
                    ocr_text, image_path, content_hash
                ))
                conn.commit()

            except Exception as e:
                print(f"Capture error: {e}")

            time.sleep(CAPTURE_INTERVAL)

if __name__ == "__main__":
    capture_loop()
```

### 2.2 Multi-Monitor Support

```python
def capture_all_monitors(sct, conn):
    """Capture all monitors."""
    monitors = sct.monitors[1:]  # Skip "all monitors" entry
    window_title, app_name = get_active_window()

    if should_skip(app_name, window_title):
        return

    for i, monitor in enumerate(monitors):
        ocr_text, image_path, content_hash = capture_screen(sct, i)
        if ocr_text:
            conn.execute("""
                INSERT INTO captures
                (timestamp, window_title, app_name, monitor_index,
                 ocr_text, image_path, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                window_title, app_name, i,
                ocr_text, image_path, content_hash
            ))
    conn.commit()
```

---

## 3. Installation on Windows

```powershell
# Install Tesseract OCR
winget install UB-Mannheim.TesseractOCR

# Install Python dependencies
pip install mss pytesseract Pillow pygetwindow

# Verify Tesseract is accessible
tesseract --version
```

---

## 4. Running as a Windows Service

### Option A: Task Scheduler (simplest)

```powershell
# Create a scheduled task that runs at login
$action = New-ScheduledTaskAction -Execute "python" `
    -Argument "C:\Users\username\openclaw\screen_capture.py"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "OpenClaw Screen Capture" `
    -Action $action -Trigger $trigger -Settings $settings
```

### Option B: NSSM (Non-Sucking Service Manager)

```powershell
# Install NSSM
winget install nssm

# Register as Windows service
nssm install OpenClawCapture "C:\Python312\python.exe" `
    "C:\Users\username\openclaw\screen_capture.py"
nssm set OpenClawCapture AppDirectory "C:\Users\username\openclaw"
nssm start OpenClawCapture
```

---

## 5. Capture Frequency Strategies

| Strategy | Interval | Storage/Day | CPU Impact | Best For |
|----------|----------|-------------|-----------|----------|
| Fixed interval | 30 seconds | ~100-150 MB | Low (~2%) | Default, simple |
| On-change detection | Variable (check every 5s, capture on change) | ~50-100 MB | Medium (~5%) | Reduced storage |
| Active-only | 15 seconds when active, skip idle | ~60-100 MB | Low | Battery-conscious |
| Aggressive | 5 seconds | ~600-900 MB | High (~10%) | Maximum recall |

**Recommended:** Fixed 30-second interval with content hash deduplication. This balances recall coverage with storage efficiency.

---

## 6. Performance Considerations

| Operation | Time per Capture | Notes |
|-----------|-----------------|-------|
| Screenshot (mss) | ~10-30 ms | Very fast, DMA-based |
| OCR (Tesseract) | ~500-2000 ms | Main bottleneck; depends on text density |
| JPEG save | ~20-50 ms | At quality=75 |
| SQLite insert | ~1-5 ms | Including FTS5 trigger |
| **Total** | ~550-2100 ms | Well within 30-second interval |

**CPU overhead:** 2-5% average on a modern desktop. OCR runs in a separate thread to avoid blocking other processes.

---

## 7. Storage Management

### Retention Policy

```python
def cleanup_old_captures(conn, max_age_days=30, max_size_gb=10):
    """Remove old captures to manage disk space."""
    import shutil

    # Delete captures older than max_age_days
    cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()
    cursor = conn.execute(
        "SELECT image_path FROM captures WHERE timestamp < ?", (cutoff,)
    )
    for row in cursor:
        if row[0] and os.path.exists(row[0]):
            os.remove(row[0])
    conn.execute("DELETE FROM captures WHERE timestamp < ?", (cutoff,))
    conn.commit()
```

### Estimated Storage

| Duration | JPEG (30s interval) | PNG (30s interval) |
|----------|--------------------|--------------------|
| 1 day (8 hrs) | ~100-150 MB | ~300-700 MB |
| 1 week | ~0.7-1 GB | ~2-5 GB |
| 1 month | ~3-4.5 GB | ~9-21 GB |

**Recommendation:** Use JPEG at quality=75. Keep raw captures for 30 days, then delete images and retain only OCR text + metadata indefinitely.

---

## Next Steps

- [Data Pipeline](data-pipeline.md) -- Syncing data to Mac Mini
- [Storage & Indexing](storage-indexing.md) -- Supabase schema for search
- [Privacy & Security](privacy-security.md) -- Exclusion rules and encryption

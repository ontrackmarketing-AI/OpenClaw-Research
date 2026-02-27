# iMessage chat.db Schema Reference

> **Status:** Research | **Last Updated:** 2026-02-26
> **Applies to:** macOS Sequoia (15), macOS Sonoma (14), macOS Ventura (13)
> **Location:** `~/Library/Messages/chat.db`

---

## 1. Overview

Apple's Messages app stores all iMessage and SMS conversations in a SQLite database at `~/Library/Messages/chat.db`. This database operates in WAL (Write-Ahead Logging) mode, producing three files:

| File | Role |
|------|------|
| `chat.db` | Main database (may lag behind new writes) |
| `chat.db-shm` | Shared memory index |
| `chat.db-wal` | Write-ahead log (updated immediately on new messages) |

**Access constraint:** This file is TCC-protected. The process reading it must have Full Disk Access granted in System Settings. See section 7 for permissions setup.

**Read-only constraint:** OpenClaw reads this database. It never writes to it. Sending messages via chat.db is unreliable and unsupported -- use Twilio or Telegram for replies.

---

## 2. Core Tables

### 2.1 `message`

The primary table. One row per message (sent or received). Approximately 60 columns.

**Key columns:**

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER PK | Auto-incrementing. Use for new-message detection. |
| `guid` | TEXT UNIQUE | Apple's internal message GUID |
| `text` | TEXT | Plain-text body. May be NULL on macOS Ventura+ (see `attributedBody`) |
| `attributedBody` | BLOB | Binary plist (NSAttributedString). Populated when `text` is NULL |
| `handle_id` | INTEGER | FK -> `handle.ROWID`. 0 for outgoing messages (`is_from_me = 1`) |
| `date` | INTEGER | **Nanoseconds** since 2001-01-01 00:00:00 UTC (Apple epoch) |
| `date_read` | INTEGER | When message was read (same epoch) |
| `date_delivered` | INTEGER | When delivered (same epoch) |
| `date_edited` | INTEGER | Non-zero if edited (macOS Ventura+) |
| `is_from_me` | INTEGER | 1 = sent by local user, 0 = received |
| `is_read` | INTEGER | 1 = marked read |
| `service` | TEXT | `"iMessage"` or `"SMS"` |
| `cache_has_attachments` | INTEGER | 1 = has attachments (fast check without join) |
| `cache_roomnames` | TEXT | Group chat room identifier |
| `associated_message_guid` | TEXT | GUID of message this tapback/reaction targets |
| `associated_message_type` | INTEGER | Reaction type (2000=heart, 2001=thumbsup, etc.) |
| `thread_originator_guid` | TEXT | GUID of message being replied to (inline replies) |
| `balloon_bundle_id` | TEXT | Rich link / app extension bundle ID |
| `group_title` | TEXT | New group name (on rename events) |
| `item_type` | INTEGER | 0=message, 1=join, 2=leave, 3=group rename |
| `error` | INTEGER | Error code (0 = no error) |

**Reaction type mapping (`associated_message_type`):**

| Value | Reaction |
|-------|----------|
| 0 | None |
| 2000 | Heart |
| 2001 | Thumbs up |
| 2002 | Thumbs down |
| 2003 | Haha |
| 2004 | !! (emphasis) |
| 2005 | ? (question) |

### 2.2 `handle`

Unique contact identifiers (phone numbers, email addresses).

```sql
CREATE TABLE handle (
    ROWID              INTEGER PRIMARY KEY AUTOINCREMENT,
    id                 TEXT NOT NULL,       -- +15551234567 or email@example.com
    country            TEXT,                -- ISO country code
    service            TEXT NOT NULL,       -- "iMessage" or "SMS"
    uncanonicalized_id TEXT                 -- raw, non-E.164 form
);
```

### 2.3 `chat`

One row per conversation (1-to-1 or group).

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER PK | Chat identifier |
| `guid` | TEXT UNIQUE | Apple's internal chat GUID |
| `style` | INTEGER | 43 = direct message, 45 = group chat |
| `chat_identifier` | TEXT | Phone/email for DMs; group UUID for groups |
| `service_name` | TEXT | `"iMessage"` or `"SMS"` |
| `display_name` | TEXT | Human-readable group name (NULL for DMs) |
| `room_name` | TEXT | Group room identifier |

### 2.4 `attachment`

File attachments (images, videos, documents).

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER PK | Attachment identifier |
| `guid` | TEXT UNIQUE | Apple's internal GUID |
| `filename` | TEXT | Absolute path under `~/Library/Messages/Attachments/` |
| `mime_type` | TEXT | e.g., `image/jpeg`, `video/mp4` |
| `transfer_name` | TEXT | Original filename |
| `total_bytes` | INTEGER | File size |
| `created_date` | INTEGER | Apple epoch in **seconds** (not nanoseconds) |

### 2.5 Junction Tables

**`chat_message_join`** -- Links messages to conversations:

```sql
CREATE TABLE chat_message_join (
    chat_id    INTEGER REFERENCES chat(ROWID),
    message_id INTEGER REFERENCES message(ROWID),
    message_date INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, message_id)
);
```

**`chat_handle_join`** -- Links participants to conversations:

```sql
CREATE TABLE chat_handle_join (
    chat_id   INTEGER REFERENCES chat(ROWID),
    handle_id INTEGER REFERENCES handle(ROWID),
    PRIMARY KEY (chat_id, handle_id)
);
```

**`message_attachment_join`** -- Links messages to attachments:

```sql
CREATE TABLE message_attachment_join (
    message_id    INTEGER REFERENCES message(ROWID),
    attachment_id INTEGER REFERENCES attachment(ROWID),
    PRIMARY KEY (message_id, attachment_id)
);
```

---

## 3. Timestamp Format

All `date` columns in the `message` table use **Apple Core Data epoch: integer nanoseconds since 2001-01-01 00:00:00 UTC**.

The offset from Unix epoch (1970-01-01) is exactly **978,307,200 seconds**.

**SQL conversion:**

```sql
SELECT
    ROWID,
    text,
    datetime((date / 1000000000) + 978307200, 'unixepoch', 'localtime') AS readable_date
FROM message
ORDER BY date DESC
LIMIT 20;
```

**Python conversion:**

```python
import datetime

APPLE_EPOCH_OFFSET = 978307200

def apple_ts_to_datetime(ts: int) -> datetime.datetime:
    unix_seconds = (ts / 1_000_000_000) + APPLE_EPOCH_OFFSET
    return datetime.datetime.fromtimestamp(unix_seconds)
```

**Note:** `attachment.created_date` uses **seconds** (not nanoseconds). Add 978,307,200 directly without dividing.

---

## 4. Handling `attributedBody` (macOS Ventura+)

Starting with macOS Ventura, many messages store text in the `attributedBody` BLOB (NSAttributedString serialized as typedstream) while `text` is NULL. This affects messages with rich formatting, mentions, or link previews.

**Quick regex extraction:**

```python
import re

def extract_text_from_attributed_body(blob: bytes) -> str:
    if not blob:
        return ""
    decoded = blob.decode("utf-8", errors="replace")
    match = re.search(r"NSString\x01.(.+?)NSDictionary", decoded, re.DOTALL)
    if match:
        raw = match.group(1)
        return raw[6:-12]
    return ""

def get_message_text(text: str, attributed_body: bytes) -> str:
    """Get message text, handling both text and attributedBody columns."""
    if text:
        return text
    return extract_text_from_attributed_body(attributed_body)
```

**More accurate extraction:** Use the `python-typedstream` library (`pip install python-typedstream`) for proper NSArchiver deserialization.

---

## 5. Key Queries

**Recent messages with sender info:**

```sql
SELECT
    m.ROWID,
    datetime((m.date / 1000000000) + 978307200, 'unixepoch', 'localtime') AS sent_at,
    CASE WHEN m.is_from_me = 1 THEN 'me' ELSE h.id END AS sender,
    m.text,
    m.is_from_me,
    m.service
FROM message m
LEFT JOIN handle h ON m.handle_id = h.ROWID
ORDER BY m.date DESC
LIMIT 50;
```

**All messages in a conversation with a contact:**

```sql
SELECT m.ROWID, m.text, m.is_from_me,
    datetime((m.date / 1000000000) + 978307200, 'unixepoch', 'localtime') AS sent_at
FROM message m
LEFT JOIN handle h ON m.handle_id = h.ROWID
INNER JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
INNER JOIN chat c ON c.ROWID = cmj.chat_id
WHERE c.chat_identifier = '+15551234567'
ORDER BY m.date ASC;
```

**New messages since last poll:**

```sql
SELECT m.ROWID, m.text, m.attributedBody, m.date, m.is_from_me,
       m.cache_has_attachments, m.service, h.id AS sender
FROM message m
LEFT JOIN handle h ON m.handle_id = h.ROWID
WHERE m.ROWID > :last_seen_rowid
ORDER BY m.ROWID ASC;
```

**List all group chats:**

```sql
SELECT ROWID, display_name, chat_identifier, room_name
FROM chat
WHERE style = 45
ORDER BY ROWID DESC;
```

---

## 6. New Message Detection

### Recommended: Poll MAX(ROWID) every 2 seconds

```python
import sqlite3, time

DB_PATH = "/Users/username/Library/Messages/chat.db"
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
last_rowid = 0

while True:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.ROWID, m.text, m.attributedBody, m.date,
               m.is_from_me, h.id AS sender
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        WHERE m.ROWID > ?
        ORDER BY m.ROWID ASC
    """, (last_rowid,))
    for row in cursor.fetchall():
        last_rowid = row[0]
        process_message(row)
    time.sleep(2)
```

### Alternative: fswatch on WAL file

The default FSEvents backend does not detect SQLite WAL writes. Use the poll monitor:

```bash
fswatch -m poll_monitor ~/Library/Messages/chat.db-wal
```

**Recommendation:** Use ROWID polling. It is simpler, more reliable, and the 2-second latency is acceptable for a message relay.

---

## 7. macOS Permissions (Full Disk Access)

### Why FDA Is Required

`~/Library/Messages/` is TCC-protected under `kTCCServiceSystemPolicyAllFiles`. Without FDA, any process opening `chat.db` gets:

```
sqlite3.OperationalError: unable to open database file
```

### Granting FDA on macOS Sequoia

1. Open **System Settings > Privacy & Security > Full Disk Access**
2. Click `+` and add the process that will read chat.db:
   - Terminal.app: `/Applications/Utilities/Terminal.app`
   - Python directly: your venv python binary
   - A LaunchAgent service: the binary specified in the plist
3. Child processes inherit FDA from their parent terminal

### SIP Considerations

SIP does not protect `~/Library/Messages/`. You do not need to disable SIP. Only TCC (Full Disk Access) is required.

### Read-Only Access (Critical)

Always open the database in read-only mode:

```python
conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
```

This prevents accidental writes and avoids interfering with the Messages app's WAL checkpoint mechanism.

---

## References

- imessage-exporter (ReagentX): https://github.com/ReagentX/imessage-exporter
- Apple Core Data timestamp: https://www.epochconverter.com/coredata
- Deep Dive into iMessage: https://fatbobman.com/en/posts/deep-dive-into-imessage/
- fswatch WAL issue: https://github.com/emcrisostomo/fswatch/issues/150

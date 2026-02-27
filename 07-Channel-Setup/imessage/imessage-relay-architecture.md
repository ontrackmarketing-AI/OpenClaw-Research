# iMessage Relay Architecture

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [chat.db Schema](chat-db-schema.md), [Network Security](../../02-Security/network-security.md), [Tailscale VPN](../../02-Security/tailscale-vpn.md)

---

## 1. Architecture Overview

The iMessage relay is a lightweight service running on the **iMac** (where iMessage is synced) that reads `chat.db` and exposes new messages to the **Mac Mini** (where OpenClaw runs) over Tailscale.

```
iMac (iMessage synced)                    Mac Mini (OpenClaw)
+-----------------------------+           +----------------------------+
|  Messages.app               |           |  OpenClaw Agent            |
|       |                     |           |       |                    |
|       v                     |           |       v                    |
|  ~/Library/Messages/        |           |  iMessage Connector        |
|    chat.db                  |           |  (queries relay API)       |
|       |                     |           |       ^                    |
|       v                     |           |       |                    |
|  iMessage Relay Service     | Tailscale |       |                    |
|  (FastAPI, port 8199)      |<--------->|  REST API calls            |
|  - Polls MAX(ROWID)         |  VPN mesh |  over Tailscale            |
|  - Serves REST API          |           |                            |
+-----------------------------+           +----------------------------+
```

**Key design decisions:**
- **Pull model:** Mac Mini queries the iMac relay (not push). This avoids the iMac needing to know the Mac Mini's state.
- **Stateless relay:** The relay service is a thin REST wrapper around SQLite queries. It holds no state beyond the database connection.
- **Tailscale-only access:** The relay binds to `127.0.0.1` and is exposed via `tailscale serve`. No public internet exposure.

---

## 2. Relay Service (FastAPI on iMac)

### 2.1 Service Implementation

```python
# imessage_relay.py -- runs on the iMac
from fastapi import FastAPI, Query, HTTPException
from contextlib import asynccontextmanager
import sqlite3
import os
import re
from datetime import datetime

DB_PATH = os.path.expanduser("~/Library/Messages/chat.db")
APPLE_EPOCH_OFFSET = 978307200

app = FastAPI(title="iMessage Relay", docs_url=None, redoc_url=None)

def get_db():
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def apple_ts_to_iso(ts: int) -> str:
    if not ts:
        return None
    unix_seconds = (ts / 1_000_000_000) + APPLE_EPOCH_OFFSET
    return datetime.fromtimestamp(unix_seconds).isoformat()

def extract_text(text, attributed_body):
    if text:
        return text
    if not attributed_body:
        return ""
    try:
        decoded = attributed_body.decode("utf-8", errors="replace")
        match = re.search(r"NSString\x01.(.+?)NSDictionary", decoded, re.DOTALL)
        if match:
            return match.group(1)[6:-12]
    except Exception:
        pass
    return "[media/rich content]"

@app.get("/health")
async def health():
    return {"status": "ok", "db_exists": os.path.exists(DB_PATH)}

@app.get("/messages/since/{rowid}")
async def get_messages_since(rowid: int, limit: int = Query(default=100, le=500)):
    """Get messages with ROWID > the specified value."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.ROWID, m.text, m.attributedBody, m.date,
                   m.is_from_me, m.service, m.cache_has_attachments,
                   h.id AS sender_id, c.chat_identifier, c.display_name,
                   c.style AS chat_style
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            LEFT JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
            LEFT JOIN chat c ON c.ROWID = cmj.chat_id
            WHERE m.ROWID > ?
            ORDER BY m.ROWID ASC
            LIMIT ?
        """, (rowid, limit))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                "rowid": row["ROWID"],
                "text": extract_text(row["text"], row["attributedBody"]),
                "timestamp": apple_ts_to_iso(row["date"]),
                "is_from_me": bool(row["is_from_me"]),
                "service": row["service"],
                "has_attachments": bool(row["cache_has_attachments"]),
                "sender": row["sender_id"],
                "chat_identifier": row["chat_identifier"],
                "chat_name": row["display_name"],
                "is_group": row["chat_style"] == 45,
            })
        return {"messages": messages, "count": len(messages)}
    finally:
        conn.close()

@app.get("/messages/conversation/{chat_identifier}")
async def get_conversation(
    chat_identifier: str,
    limit: int = Query(default=50, le=200),
    since_rowid: int = Query(default=0)
):
    """Get messages from a specific conversation."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.ROWID, m.text, m.attributedBody, m.date,
                   m.is_from_me, m.service, h.id AS sender_id
            FROM message m
            LEFT JOIN handle h ON m.handle_id = h.ROWID
            INNER JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
            INNER JOIN chat c ON c.ROWID = cmj.chat_id
            WHERE c.chat_identifier = ? AND m.ROWID > ?
            ORDER BY m.date DESC
            LIMIT ?
        """, (chat_identifier, since_rowid, limit))

        messages = []
        for row in cursor.fetchall():
            messages.append({
                "rowid": row["ROWID"],
                "text": extract_text(row["text"], row["attributedBody"]),
                "timestamp": apple_ts_to_iso(row["date"]),
                "is_from_me": bool(row["is_from_me"]),
                "sender": row["sender_id"],
            })
        return {"messages": messages}
    finally:
        conn.close()

@app.get("/conversations")
async def list_conversations(limit: int = Query(default=20, le=100)):
    """List recent conversations."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.ROWID, c.chat_identifier, c.display_name,
                   c.service_name, c.style,
                   MAX(m.date) AS last_message_date
            FROM chat c
            LEFT JOIN chat_message_join cmj ON cmj.chat_id = c.ROWID
            LEFT JOIN message m ON m.ROWID = cmj.message_id
            GROUP BY c.ROWID
            ORDER BY last_message_date DESC
            LIMIT ?
        """, (limit,))

        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "id": row["chat_identifier"],
                "name": row["display_name"],
                "service": row["service_name"],
                "is_group": row["style"] == 45,
                "last_activity": apple_ts_to_iso(row["last_message_date"]),
            })
        return {"conversations": conversations}
    finally:
        conn.close()

@app.get("/max-rowid")
async def get_max_rowid():
    """Get the current maximum ROWID (for initial sync)."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(ROWID) as max_rowid FROM message")
        row = cursor.fetchone()
        return {"max_rowid": row["max_rowid"] or 0}
    finally:
        conn.close()
```

### 2.2 Running the Relay

```bash
# On the iMac

# Install dependencies
pip install fastapi uvicorn

# Run the relay (binds to localhost only)
uvicorn imessage_relay:app --host 127.0.0.1 --port 8199

# Expose via Tailscale serve (accessible only to your tailnet)
tailscale serve --bg 8199
```

### 2.3 LaunchAgent for Auto-Start

```xml
<!-- ~/Library/LaunchAgents/com.openclaw.imessage-relay.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.imessage-relay</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/uvicorn</string>
        <string>imessage_relay:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>8199</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourname/openclaw-relay</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/imessage-relay.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/imessage-relay.out</string>
</dict>
</plist>
```

---

## 3. OpenClaw Connector (Mac Mini Side)

The Mac Mini runs an OpenClaw connector that polls the iMac relay:

```python
# imessage_connector.py -- runs on Mac Mini as part of OpenClaw
import httpx
import asyncio

RELAY_URL = "https://imac.tailnet-name.ts.net"  # Tailscale hostname
POLL_INTERVAL = 5  # seconds

class iMessageConnector:
    def __init__(self, relay_url: str):
        self.relay_url = relay_url
        self.last_rowid = 0
        self.client = httpx.AsyncClient(timeout=10)

    async def initialize(self):
        """Get current max ROWID on startup (skip historical messages)."""
        resp = await self.client.get(f"{self.relay_url}/max-rowid")
        self.last_rowid = resp.json()["max_rowid"]

    async def poll(self):
        """Fetch new messages since last poll."""
        resp = await self.client.get(
            f"{self.relay_url}/messages/since/{self.last_rowid}"
        )
        data = resp.json()
        for msg in data["messages"]:
            self.last_rowid = max(self.last_rowid, msg["rowid"])
            await self.process_message(msg)

    async def process_message(self, msg: dict):
        """Process an incoming iMessage."""
        # Skip outgoing messages (from the user)
        if msg["is_from_me"]:
            return

        # Normalize to OpenClaw InboundMessage format
        normalized = {
            "channel": "imessage",
            "sender_id": msg["sender"],
            "conversation_id": msg["chat_identifier"],
            "message_type": "text",
            "content": msg["text"],
            "metadata": {
                "service": msg["service"],
                "is_group": msg["is_group"],
                "chat_name": msg["chat_name"],
                "has_attachments": msg["has_attachments"],
                "timestamp": msg["timestamp"],
            }
        }
        await openclaw.route_message(normalized)

    async def get_conversation(self, chat_id: str, limit: int = 50):
        """Retrieve conversation history for context."""
        resp = await self.client.get(
            f"{self.relay_url}/messages/conversation/{chat_id}",
            params={"limit": limit}
        )
        return resp.json()["messages"]

    async def run(self):
        """Main polling loop."""
        await self.initialize()
        while True:
            try:
                await self.poll()
            except Exception as e:
                log.error(f"iMessage poll failed: {e}")
            await asyncio.sleep(POLL_INTERVAL)
```

---

## 4. Network Security

### 4.1 Tailscale-Only Access

The relay binds to `127.0.0.1:8199` and is exposed only through Tailscale serve:

```bash
# On iMac
tailscale serve --bg 8199
# Now accessible at https://imac.tailnet-name.ts.net via Tailscale only
```

**Verification:**

```bash
# From a non-Tailscale device: should fail
curl https://imac-local-ip:8199/health  # Connection refused

# From Mac Mini (on Tailscale): should succeed
curl https://imac.tailnet-name.ts.net/health  # {"status": "ok"}
```

### 4.2 Tailscale ACLs

Restrict which devices can access the relay:

```json
// In Tailscale admin console -> Access Controls
{
  "acls": [
    {
      "action": "accept",
      "src": ["mac-mini"],
      "dst": ["imac:8199"]
    }
  ]
}
```

### 4.3 No API Keys Exposed

The relay does not expose any Apple credentials. It reads a local SQLite file and serves the data over Tailscale's encrypted WireGuard tunnel.

---

## 5. Reliability

| Concern | Mitigation |
|---------|-----------|
| iMac goes to sleep | Disable sleep in System Settings > Energy Saver, or use `caffeinate -s` |
| Messages.app not running | Not required -- chat.db is updated by the system regardless |
| Relay service crashes | LaunchAgent with `KeepAlive: true` restarts it automatically |
| Tailscale disconnects | Tailscale reconnects automatically; connector retries with backoff |
| Database locked | Read-only mode (`?mode=ro`) avoids lock contention |
| WAL not checkpointed | Read-only connection reads from WAL automatically |

---

## 6. Data Flow Summary

```
1. Someone sends you an iMessage/SMS
2. Messages.app on iMac writes to chat.db
3. Relay service (FastAPI) is polled by Mac Mini every 5 seconds
4. New messages returned as JSON over Tailscale HTTPS
5. OpenClaw connector normalizes to InboundMessage format
6. Agent processes: stores in memory, surfaces in check-ins, notifies via Telegram
7. If reply needed: agent drafts response, sends via Telegram/Twilio (NOT via chat.db)
```

---

## Next Steps

- [chat.db Schema](chat-db-schema.md) -- detailed table reference
- [Privacy Considerations](privacy-considerations.md) -- legal and ethical analysis
- [Network Security](../../02-Security/network-security.md) -- Tailscale and port security

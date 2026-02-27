# Phase 11 - iMessage Integration (Week 11-12)

> **Depends on:** Phase 2 (Tailscale VPN operational), Phase 3 (Memory system for context)

## Goal

Deploy a read-only iMessage relay on the iMac, accessible to OpenClaw on the Mac Mini over Tailscale. The agent can read recent conversations and use message context for check-ins and user queries.

---

## Prerequisites

- [ ] Tailscale mesh network connecting iMac and Mac Mini (Phase 2)
- [ ] Full Disk Access granted on iMac for the relay service
- [ ] iMessage synced and active on iMac
- [ ] Memory system operational (Phase 3)

---

## Week 11: iMac Relay Service

### Day 1-2: chat.db Access + Permissions

1. Grant Full Disk Access to Terminal (or Python) on the iMac via System Settings > Privacy & Security
2. Verify `chat.db` is readable: `sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message"`
3. Test key SQL queries: recent messages, conversation listing, max ROWID
4. Handle `attributedBody` BLOB extraction for macOS Ventura+ messages

### Day 3-4: FastAPI Relay Service

1. Deploy the FastAPI relay service on the iMac (port 8199)
2. Implement endpoints:
   - `GET /messages/since/{rowid}` -- poll for new messages
   - `GET /messages/conversation/{chat_identifier}` -- get conversation history
   - `GET /conversations` -- list recent conversations
   - `GET /health` -- health check
3. Expose via `tailscale serve --bg 8199`
4. Test from Mac Mini: `curl https://imac.tailnet.ts.net:8199/health`

### Day 5: LaunchAgent Auto-Start

1. Create LaunchAgent plist for automatic startup on boot
2. Test: reboot iMac, verify relay starts and is accessible
3. Add health monitoring (Mac Mini pings relay every 5 minutes)

---

## Week 12: OpenClaw Connector + Privacy

### Day 1-2: Mac Mini Connector

1. Build the OpenClaw connector that polls the relay for new messages (5-second interval)
2. Implement ROWID-based change detection (only fetch messages newer than last seen)
3. Test message ingestion flow: relay → connector → working memory (not persisted)
4. Build the `imessage_recent` tool for agent use

### Day 3: Privacy Controls

1. Implement contact filtering (whitelist/blacklist specific contacts)
2. Configure exclusion patterns (skip group chats, skip unknown numbers)
3. Verify: message content is processed in working memory only, NOT written to daily logs or Supabase
4. Test: agent can answer "What did John say about the meeting?" without persisting the message

### Day 4-5: Integration Testing + Go-Live

1. Test proactive check-in integration: check-in engine reads recent iMessage context
2. Test user queries: "Did anyone message me about the project?"
3. Test privacy boundaries: agent correctly refuses to share message content externally
4. Deploy and monitor

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Relay uptime | > 99% (health check passing) |
| Message detection latency | < 10 seconds from send to agent awareness |
| Privacy compliance | 0 instances of message content persisted or shared externally |
| Useful context provided | Agent references iMessage context in > 30% of relevant check-ins |

---

## Reference Docs

- [chat.db Schema](../07-Channel-Setup/imessage/chat-db-schema.md)
- [iMessage Relay Architecture](../07-Channel-Setup/imessage/imessage-relay-architecture.md)
- [Privacy Considerations](../07-Channel-Setup/imessage/privacy-considerations.md)
- [Network Security](../02-Security/network-security.md)

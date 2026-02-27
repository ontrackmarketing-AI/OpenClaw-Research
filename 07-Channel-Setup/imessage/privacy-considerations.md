# iMessage Integration -- Privacy Considerations

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [chat.db Schema](chat-db-schema.md), [Relay Architecture](imessage-relay-architecture.md), [Data Privacy](../../09-Legal-Compliance/data-privacy.md)

---

## 1. The Core Privacy Issue

Reading `chat.db` gives the agent access to **all** iMessage and SMS conversations -- not just the user's messages, but messages from every person who has ever communicated with the user. These other people did not consent to their messages being read by an AI agent.

This is fundamentally different from other OpenClaw data sources (CRM leads opted into a pipeline, web data is public). iMessage data is private, personal communication.

---

## 2. Legal Analysis

### 2.1 Federal Wiretap Law (18 U.S.C. 2511)

The federal Wiretap Act prohibits interception of electronic communications without consent. However, the **one-party consent** exception applies: if one party to the communication (the user) consents, the interception is legal in most states.

**Texas (user's state):** Texas is a **one-party consent** state (Tex. Penal Code 16.02). The user can legally record or access their own conversations without notifying the other party.

**Result:** Reading your own iMessage conversations is legal under federal and Texas law.

### 2.2 GDPR Implications

If any contacts are in the EU:
- Processing their message content triggers GDPR (personal data of EU residents)
- Legal basis: **Legitimate interest** (managing your own communications) -- arguable but weaker than for B2B outreach
- **Recommendation:** Do not store EU contacts' message content in any database. Process in memory only.

### 2.3 TDPSA (Texas Data Privacy and Security Act)

If contact information from iMessages is used for marketing purposes (e.g., extracting a phone number and adding it to a lead list), TDPSA's consent requirements may apply. Keep iMessage data separate from marketing data.

### 2.4 Apple Terms of Service

Apple's macOS Software License Agreement does not explicitly prohibit reading your own chat.db for personal use. However:
- Do not reverse-engineer the Messages app itself
- Do not distribute the relay tool commercially with the purpose of accessing Apple's systems
- Do not use the data to build a competing service

---

## 3. Ethical Framework

### 3.1 Principles

| Principle | Implementation |
|-----------|---------------|
| **Minimum necessary access** | Read only what the agent needs. Skip group chats unless relevant. |
| **No content storage** | Process messages in working memory. Do not persist full message content to databases. |
| **Surface metadata, not content** | Check-ins reference "Sarah messaged you about the project" -- not the full message text. |
| **User control** | User can disable iMessage reading at any time. Allow per-contact and per-group filtering. |
| **No forwarding** | Never forward message content to third parties, external services, or other people. |
| **No training** | Message content should not be used to fine-tune or train any model. |

### 3.2 What the Agent Should and Should Not Do

**Allowed:**
- Notify user that a message was received from a known contact
- Summarize unread message count and senders
- Pull conversation context when user explicitly asks ("What did Sarah say about the proposal?")
- Cross-reference sender against CRM contacts to identify business relevance
- Surface time-sensitive messages in proactive check-ins

**Not allowed:**
- Store full message text in Supabase, Airtable, or any persistent database
- Send message content to Claude API unless the user explicitly asks for analysis
- Forward or share message content with anyone other than the user
- Automatically respond to iMessages (the relay is read-only)
- Scrape phone numbers or emails from messages for marketing use
- Process messages from contacts the user has marked as excluded

---

## 4. Data Handling Rules

### 4.1 Content Flow

```
chat.db (iMac)
    |
    v
Relay API (returns JSON over Tailscale)
    |
    v
OpenClaw connector (processes in working memory)
    |
    v
Metadata stored: sender, timestamp, has_attachments, chat_id
Content NOT stored: message text discarded after processing
    |
    v
Agent surfaces insights: "3 new messages from known contacts"
```

### 4.2 What Gets Persisted

| Data | Stored? | Where | Retention |
|------|---------|-------|-----------|
| Message text | **No** | Working memory only | Discarded after session |
| Sender phone/email | Yes (if already in CRM) | Cross-reference only | N/A |
| Message timestamp | Yes | Daily logs (metadata) | 30 days |
| Conversation ID | Yes | Memory (for context retrieval) | Session only |
| Attachment filenames | No | Not transferred | N/A |
| Message count per contact | Yes | Daily summary | 30 days |

### 4.3 Contact Filtering

Allow the user to exclude specific contacts or groups:

```yaml
imessage:
  exclude_contacts:
    - "+15551234567"       # Specific phone number
    - "doctor@clinic.com"  # Specific email
  exclude_groups: true     # Skip all group chats
  exclude_patterns:
    - "*@*.gov"            # Government contacts
  include_only:            # If set, ONLY these contacts are processed
    # - "+15559876543"     # Uncomment to whitelist
```

---

## 5. Security Measures

### 5.1 Data in Transit

All data travels over Tailscale's WireGuard tunnel (encrypted, authenticated). No message content touches the public internet.

### 5.2 Data at Rest

No message content is written to disk on the Mac Mini. The relay reads from the existing chat.db on the iMac (which Apple manages).

### 5.3 Access Control

- Relay API accessible only via Tailscale (ACL restricted to Mac Mini)
- No authentication bypass possible (Tailscale identity verification)
- Read-only database access (no writes to chat.db)

### 5.4 Audit Trail

Log every relay query for accountability:

```json
{
    "timestamp": "2026-02-26T14:30:00Z",
    "action": "imessage_poll",
    "messages_returned": 3,
    "senders": ["redacted_hash_1", "redacted_hash_2"],
    "content_accessed": false,
    "purpose": "proactive_checkin_context"
}
```

Note: Log sender hashes (not raw phone numbers) for privacy in the audit trail.

---

## 6. User Disclosure Recommendations

While not legally required (one-party consent), consider:

1. **Informing close contacts:** "I use an AI assistant that can see my messages to help me stay on top of things."
2. **Business contacts:** Disclosure is not necessary for messages that are already business communication.
3. **Sensitive contacts (medical, legal, financial):** Consider excluding these contacts from processing.

---

## 7. Comparison to Similar Tools

| Tool | Approach | Privacy Stance |
|------|----------|---------------|
| Apple Intelligence (iOS 18) | On-device summarization of messages | Apple's own feature, no data leaves device |
| Bezel/Texts.com | Multi-platform message aggregation | Cloud processing, stores messages |
| **OpenClaw iMessage Relay** | Local read-only access, Tailscale-only, no content persistence | Most privacy-preserving approach |

---

## 8. Configuration Checklist

- [ ] Full Disk Access granted to the relay process on the iMac
- [ ] Relay binds to 127.0.0.1 only (Tailscale serve for remote access)
- [ ] Tailscale ACL restricts relay access to Mac Mini only
- [ ] Contact exclusion list configured (medical, legal, personal)
- [ ] Group chat exclusion enabled (unless needed)
- [ ] Content persistence disabled (no message text in databases)
- [ ] Audit logging enabled for relay queries
- [ ] User has reviewed and accepted the privacy implications

---

## Next Steps

- [Relay Architecture](imessage-relay-architecture.md) -- technical implementation
- [Data Privacy](../../09-Legal-Compliance/data-privacy.md) -- broader privacy law compliance
- [Network Security](../../02-Security/network-security.md) -- Tailscale security

# Context Sources for Proactive Check-ins

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Check-in Engine](checkin-engine.md), [Memory Architecture](../../04-Memory-and-RAG/memory-architecture.md)

---

## 1. Overview

Check-ins are only valuable if they are context-aware. This document maps every data source the check-in engine queries before generating a message, including priority, latency, and fallback behavior.

---

## 2. Context Source Matrix

| Source | Data Provided | Priority | Latency | Fallback |
|--------|--------------|----------|---------|----------|
| Agent Memory (MEMORY.md) | Active projects, preferences, key facts | Critical | <10ms | Never fails (local file) |
| Daily Logs | Today's session history, recent actions | High | <50ms | Skip if today's log empty |
| GHL CRM Pipeline | Lead status, overdue follow-ups, pipeline metrics | High | 200-500ms | Use cached data (15 min TTL) |
| Google Calendar API | Today's meetings, upcoming deadlines | High | 100-300ms | Skip calendar context |
| Pending HITL Approvals | Actions waiting for user approval | High | <50ms | Check OpenClaw queue |
| iMessage Relay (Capability 1) | Recent messages from contacts | Medium | 100-300ms | Skip if relay unavailable |
| Supabase (leads table) | New leads, lead scores, pipeline counts | Medium | 100-200ms | Use last cached snapshot |
| Airtable (content calendar) | Upcoming content due dates | Medium | 200-400ms | Skip content context |
| OCR Screen Database (Capability 5) | What user was working on | Low | 200-500ms | Skip screen context |
| Previous Check-in History | Response rates, ignored slots, recent openings | Critical | <10ms | Always available (local) |

---

## 3. Context Assembly Pipeline

```python
async def assemble_checkin_context(slot: str) -> dict:
    context = {}

    # Phase 1: Always-available local sources (parallel)
    memory_task = asyncio.create_task(load_memory_md())
    daily_log_task = asyncio.create_task(load_todays_log())
    history_task = asyncio.create_task(load_checkin_history())

    context["memory"] = await memory_task
    context["daily_log"] = await daily_log_task
    context["checkin_history"] = await history_task

    # Phase 2: Remote sources with timeout (parallel, 2-second timeout)
    remote_tasks = {
        "calendar": asyncio.create_task(fetch_calendar_events()),
        "pipeline": asyncio.create_task(fetch_ghl_pipeline_summary()),
        "pending_approvals": asyncio.create_task(fetch_pending_approvals()),
        "new_leads": asyncio.create_task(fetch_recent_leads()),
    }

    # Optional sources (only if capabilities are active)
    if config.imessage_relay_enabled:
        remote_tasks["imessage"] = asyncio.create_task(fetch_recent_imessages())
    if config.screen_database_enabled:
        remote_tasks["screen_context"] = asyncio.create_task(fetch_recent_screen_activity())

    done, pending = await asyncio.wait(
        remote_tasks.values(),
        timeout=2.0  # 2-second hard timeout
    )

    for name, task in remote_tasks.items():
        if task in done and not task.exception():
            context[name] = task.result()
        else:
            context[name] = None  # Graceful degradation

    # Phase 3: Derive summary fields
    context["pending_tasks"] = extract_pending_tasks(context)
    context["recent_activity"] = summarize_activity(context)
    context["pipeline_summary"] = format_pipeline(context.get("pipeline"))
    context["calendar_summary"] = format_calendar(context.get("calendar"))
    context["recent_openings"] = get_recent_openings(context["checkin_history"])
    context["recent_conversations"] = extract_conversations(context)

    return context
```

---

## 4. Source Details

### 4.1 Agent Memory (MEMORY.md)

Read `~/.openclaw/memory/MEMORY.md` for:
- Active projects and their current phase
- User preferences (work hours, communication style)
- Key facts (client names, important deadlines)
- Learned patterns (user tends to focus on X in the morning)

This is always loaded -- it is the foundation of every check-in.

### 4.2 Daily Logs

Read `~/.openclaw/memory/logs/YYYY/MM/DD.md` for:
- What the agent worked on today
- Actions taken, decisions made
- Errors encountered
- Tasks completed vs pending

Used for: "You've knocked out 3 tasks this morning" or "The enrichment batch from this morning finished."

### 4.3 GHL CRM Pipeline

```python
async def fetch_ghl_pipeline_summary() -> dict:
    """Fetch pipeline summary from GoHighLevel."""
    return {
        "total_leads": await ghl.count_contacts(status="active"),
        "new_today": await ghl.count_contacts(created_after=today()),
        "overdue_followups": await ghl.count_opportunities(
            followup_due_before=now(),
            status="open"
        ),
        "hot_leads": await ghl.get_opportunities(
            stage="qualified",
            sort_by="score",
            limit=3
        ),
        "stage_changes_today": await ghl.get_pipeline_activity(since=today()),
    }
```

Cache results for 15 minutes to avoid excessive API calls.

### 4.4 Google Calendar API

```python
async def fetch_calendar_events() -> list:
    """Fetch today's calendar events."""
    events = await google_calendar.list_events(
        time_min=start_of_day(),
        time_max=end_of_day(),
        single_events=True,
        order_by="startTime"
    )
    return [{
        "summary": e["summary"],
        "start": e["start"]["dateTime"],
        "end": e["end"]["dateTime"],
        "attendees_count": len(e.get("attendees", [])),
    } for e in events]
```

**Setup requirements:**
- Google Cloud project with Calendar API enabled
- OAuth 2.0 credentials (one-time setup, token stored in credential manager)
- Scopes: `calendar.readonly` (read-only access is sufficient)

**Alternative: Apple Calendar via CalDAV**
- If using iCal on the iMac, connect via CalDAV protocol
- Endpoint: `https://caldav.icloud.com/`
- Requires app-specific password from Apple ID settings

### 4.5 Pending HITL Approvals

Query OpenClaw's approval queue for actions waiting on user input:

```python
async def fetch_pending_approvals() -> list:
    return await openclaw.get_pending_approvals(
        status="pending",
        sort_by="created_at",
        limit=5
    )
```

Useful for: "You have 3 actions waiting for approval -- want to review them now?"

### 4.6 iMessage Relay (Capability 1)

If the iMessage integration is active, query recent messages:

```python
async def fetch_recent_imessages() -> list:
    return await imessage_relay.get_messages(
        since=last_checkin_time(),
        limit=10,
        exclude_group_chats=True  # Focus on direct messages
    )
```

Used for: "Sarah from Acme texted you about the proposal -- want me to pull context?"

**Privacy note:** Only surface message existence and sender, not full content, in check-ins. See [iMessage Privacy](../../07-Channel-Setup/imessage/privacy-considerations.md).

### 4.7 OCR Screen Database (Capability 5)

If the screen database is active, query what the user was recently working on:

```python
async def fetch_recent_screen_activity() -> dict:
    return await screen_db.query(
        time_range=(now() - timedelta(hours=2), now()),
        group_by="application",
        limit=5
    )
```

Used for: "Looks like you've been in Excel working on the budget -- need any data pulled?"

---

## 5. Context Priority by Time Slot

Not all sources are equally important at every time of day:

| Source | Morning | Late Morning | After Lunch | Afternoon | Evening |
|--------|---------|-------------|-------------|-----------|---------|
| Memory | High | High | High | High | High |
| Calendar | **Critical** | Medium | Medium | Low | Medium |
| Pipeline | High | Medium | High | Medium | Low |
| Tasks | High | **Critical** | Medium | **Critical** | Medium |
| Approvals | Medium | High | Medium | High | Low |
| iMessage | Medium | Low | Low | Low | Medium |
| Screen DB | Low | Medium | Medium | Medium | Low |
| Daily Log | Low | High | Medium | Medium | **Critical** |

---

## 6. Caching Strategy

To minimize API calls and latency:

| Source | Cache TTL | Storage |
|--------|-----------|---------|
| GHL Pipeline | 15 minutes | In-memory / Redis |
| Calendar Events | 30 minutes | In-memory |
| New Leads | 15 minutes | In-memory / Redis |
| Content Calendar | 1 hour | In-memory |
| iMessage | No cache (real-time) | N/A |
| Screen DB | 5 minutes | N/A |

The check-in engine runs 3-5 times per day, so aggressive caching is appropriate. Stale-by-minutes data is acceptable for conversational check-ins.

---

## 7. Graceful Degradation

If all remote sources fail (network issue, API down), the check-in engine still sends a message using only local sources:

```
Remote sources available: Full context check-in
Some remote sources fail: Partial context (skip unavailable data)
All remote sources fail:  Generic but personalized check-in from memory
Memory unavailable:       Skip check-in entirely (something is wrong)
```

The check-in should never fail silently. If it cannot generate a quality message, it logs the failure and skips rather than sending a generic "How's it going?"

---

## Next Steps

- [Check-in Engine](checkin-engine.md) -- scheduling and execution
- [Conversational Design](conversational-design.md) -- prompt templates
- [Telegram Bot](../../07-Channel-Setup/telegram-bot.md) -- delivery channel

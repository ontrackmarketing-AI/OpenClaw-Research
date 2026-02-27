# Screen Database -- Query Interface

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Storage & Indexing](storage-indexing.md), [Memory Architecture](../../04-Memory-and-RAG/memory-architecture.md)

---

## 1. Query Types

| Query Type | Example | Search Method |
|-----------|---------|---------------|
| Natural language recall | "What was I looking at when working on the budget?" | Hybrid (vector + FTS) |
| Time-based | "What was on my screen at 2:30 PM yesterday?" | Timestamp filter |
| App-based | "Show me everything from Excel today" | App name filter + time |
| Keyword | "Find any screen with 'Acme Corp' mentioned" | FTS5 keyword search |
| Activity summary | "What did I work on this morning?" | Time range + AI summary |

---

## 2. Agent Tool Definition

```yaml
# OpenClaw tool for screen database queries
name: screen_recall
description: >
  Search the user's screen capture database to find what they were
  looking at at a specific time or when working on a topic.
parameters:
  query:
    type: string
    description: Natural language description of what to find
    required: true
  time_range:
    type: object
    properties:
      start: { type: string, format: datetime }
      end: { type: string, format: datetime }
    required: false
  app_filter:
    type: string
    description: Filter by application name
    required: false
  limit:
    type: integer
    default: 5
    required: false
returns:
  type: array
  items:
    type: object
    properties:
      captured_at: { type: string }
      app_name: { type: string }
      window_title: { type: string }
      ocr_text: { type: string }
      relevance_score: { type: number }
```

---

## 3. Query Implementation

```python
class ScreenRecallTool:
    """OpenClaw tool for querying screen capture database."""

    async def execute(self, query: str, time_range: dict = None,
                      app_filter: str = None, limit: int = 5) -> list:
        # Generate query embedding
        query_embedding = ollama.embed(
            model="nomic-embed-text", input=query
        )["embeddings"][0]

        # Build search parameters
        params = {
            "query_text": query,
            "query_embedding": query_embedding,
            "match_threshold": 0.6,
            "match_count": limit,
        }

        if time_range:
            params["time_start"] = time_range.get("start")
            params["time_end"] = time_range.get("end")
        if app_filter:
            params["filter_app"] = app_filter

        # Execute hybrid search
        result = await supabase.rpc("search_screen_captures", params)

        # Format results for agent context
        formatted = []
        for r in result.data:
            formatted.append({
                "captured_at": r["captured_at"],
                "app_name": r["app_name"],
                "window_title": r["window_title"],
                "ocr_text": r["ocr_text"][:500],  # Truncate for context window
                "relevance_score": round(r["combined_score"], 3),
            })

        return formatted
```

---

## 4. Integration with Proactive Check-ins

The screen database feeds context to proactive check-ins:

```python
async def get_screen_context_for_checkin() -> str:
    """Get recent screen activity summary for check-in context."""
    # What was the user doing in the last 2 hours?
    recent = await supabase.table("screen_captures").select(
        "app_name, window_title"
    ).gte("captured_at", two_hours_ago()).order(
        "captured_at", desc=True
    ).limit(20).execute()

    if not recent.data:
        return None

    # Summarize by app
    apps = {}
    for r in recent.data:
        app = r["app_name"] or "Unknown"
        apps[app] = apps.get(app, 0) + 1

    top_apps = sorted(apps.items(), key=lambda x: x[1], reverse=True)[:3]
    return ", ".join(f"{app} ({count}x)" for app, count in top_apps)
```

This enables check-in messages like: "Looks like you've been in Excel and Chrome most of this afternoon. Working on the budget analysis?"

---

## 5. Integration with Agent Memory

Screen capture data enriches the agent's memory system:

1. **Daily summaries** are written to `memory/logs/YYYY/MM/DD.md` (alongside session logs)
2. **Key working contexts** are indexed in the SQLite memory index for retrieval
3. **Active project detection** -- if the user spends 3+ hours in a specific app/document, the agent infers an active project

---

## 6. Example Agent Interactions

**User asks a recall question:**
```
User: "What was I looking at when I was researching solar panel pricing?"
Agent: [searches screen_captures for "solar panel pricing"]
Agent: "Based on your screen history, you were researching solar panel pricing
        on February 20th around 2-3 PM. You had Chrome open on EnergySage.com
        and were comparing quotes in an Excel spreadsheet called
        'Solar_Cost_Analysis.xlsx'. Want me to pull that data?"
```

**Agent uses screen context in check-in:**
```
Agent (4:00 PM): "You've been in PowerPoint for the last 2 hours working on
                  what looks like the Acme presentation. How's it going?
                  Need any data pulled in?"
```

**User asks about recent work:**
```
User: "What did I work on this morning?"
Agent: [queries screen_captures for today 8AM-12PM, summarizes]
Agent: "This morning you spent about 2 hours in VS Code (looks like the
        lead pipeline project), 45 minutes in Chrome researching Clay.com
        API docs, and 30 minutes in Slack. You also had a 30-minute
        meeting on Zoom at 10 AM."
```

---

## Next Steps

- [Storage & Indexing](storage-indexing.md) -- Supabase schema
- [Privacy & Security](privacy-security.md) -- Access control
- [Context Sources](../proactive-checkins/context-sources.md) -- check-in integration

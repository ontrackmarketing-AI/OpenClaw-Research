# RAFE + Obsidian -- Integration with OpenClaw

## System Overview

RAFE is a development dashboard and knowledge base built on Obsidian with MCP (Model Context Protocol) integration. It currently provides session tracking, decision logging, research documentation, and task management through a structured Obsidian vault accessed via MCP tools.

**Current RAFE Capabilities:**

| Capability | MCP Tool | Description |
|---|---|---|
| Read documents | `get_doc` | Read any document from the vault with optional section headings |
| List documents | `list_docs` | Browse vault folders with optional metadata |
| Update documents | `update_doc` | Update specific sections or frontmatter with atomic writes |
| Create documents | `create_doc` | Create from templates: session, decision, component, phase, task, policy |
| Log sessions | `log_session` | Record development sessions with focus, completed items, decisions, issues |
| Log decisions | `log_decision` | Record architectural/design decisions with options, rationale, impact |
| Update tasks | `update_task_status` | Track task status: pending, in-progress, completed, blocked |

**Vault Structure (inferred from MCP tool parameters):**
```
RAFE Vault/
  _HOME.md                    # Dashboard / landing page
  _DECISIONS.md               # Master decision log
  .state/
    active-tasks.md           # Current task tracking
  sessions/
    2026/
      01/
        15.md                 # Session notes by date
      02/
        05.md
  phases/
    _INDEX.md                 # Phase overview
    phase-0-testing.md
    phase-1-foundation.md
    ...
  components/
    component-name.md         # Component documentation
  decisions/
    individual-decision.md    # Detailed decision records
  policies/
    policy-name.md            # Operational policies
```

---

## Integration Approaches

### Approach 1: Obsidian MCP as OpenClaw Tool

**Concept:** OpenClaw gains access to all RAFE MCP tools, treating Obsidian as a read/write knowledge store.

**Implementation:**

OpenClaw's tool registry includes the RAFE Obsidian MCP tools. When OpenClaw needs to read or write knowledge, it calls these tools directly.

**Tool mapping for OpenClaw:**

| OpenClaw Need | RAFE MCP Tool | Usage Example |
|---|---|---|
| Look up a past decision | `get_doc` | Read `_DECISIONS.md` or specific decision doc to check if something was already decided |
| Find current tasks | `update_task_status` (read) or `get_doc` | Read `.state/active-tasks.md` to see what is pending |
| Record a new decision | `log_decision` | After OpenClaw makes a business decision, log it to RAFE |
| Log a work session | `log_session` | After OpenClaw completes a batch of work, log what it did |
| Read research notes | `get_doc` | Pull context from research documents when making decisions |
| Update task progress | `update_task_status` | Mark tasks as in-progress or completed after execution |
| Browse available docs | `list_docs` | Discover what knowledge exists in a folder |
| Create new documentation | `create_doc` | Create component docs, task records, or policies |

**Configuration:**

OpenClaw needs the Obsidian MCP server endpoint configured in its tool sources:

```json
{
  "tool_sources": [
    {
      "type": "mcp",
      "name": "rafe-obsidian",
      "description": "RAFE knowledge base and development dashboard via Obsidian MCP",
      "server_url": "http://localhost:3456",  // Or wherever MCP server runs
      "tools": [
        "get_doc",
        "list_docs",
        "update_doc",
        "create_doc",
        "log_session",
        "log_decision",
        "update_task_status"
      ]
    }
  ]
}
```

**Pros:**
- Zero additional infrastructure -- uses existing MCP server
- All RAFE capabilities immediately available to OpenClaw
- Atomic writes mean no data corruption risk
- Template system provides consistent document structure

**Cons:**
- Obsidian MCP must be running for OpenClaw to access knowledge
- Latency: each knowledge lookup is an MCP call
- No batch operations (must read/write one document at a time)

### Approach 2: Knowledge Sync (RAFE -> OpenClaw Memory)

**Concept:** Periodically sync RAFE knowledge into OpenClaw's native memory system so OpenClaw can query it without MCP calls.

**What gets synced:**

| RAFE Source | Sync Target | Frequency | Format |
|---|---|---|---|
| `_DECISIONS.md` | OpenClaw semantic memory | Daily | Each decision as a separate memory entry |
| `sessions/` folder | OpenClaw episodic memory | After each session | Session summary as episode |
| `phases/` folder | OpenClaw semantic memory | Weekly | Current phase context and progress |
| `.state/active-tasks.md` | OpenClaw working memory | Every 30 minutes | Active tasks as context |
| `components/` folder | OpenClaw semantic memory | Weekly | Component documentation |
| `policies/` folder | OpenClaw procedural memory | On change | Policies as behavioral rules |

**Sync skill implementation:**

```python
# openclaw/skills/rafe_sync.py

class RAFESyncSkill:
    """Syncs RAFE Obsidian knowledge into OpenClaw memory."""

    async def sync_decisions(self):
        """Sync all decisions from RAFE into semantic memory."""
        decisions_doc = await self.mcp.call("rafe-obsidian", "get_doc", {
            "path": "_DECISIONS.md",
            "include_sections": True
        })

        # Parse each decision entry
        decisions = self._parse_decision_entries(decisions_doc["content"])

        for decision in decisions:
            await self.memory.upsert_semantic(
                key=f"decision:{decision['title']}",
                content=decision['full_text'],
                metadata={
                    "type": "decision",
                    "date": decision['date'],
                    "impact": decision['impact'],
                    "tags": decision.get('tags', []),
                    "source": "rafe"
                }
            )

        return {"synced_decisions": len(decisions)}

    async def sync_active_tasks(self):
        """Pull active tasks into working memory."""
        tasks_doc = await self.mcp.call("rafe-obsidian", "get_doc", {
            "path": ".state/active-tasks.md"
        })

        tasks = self._parse_tasks(tasks_doc["content"])

        await self.memory.set_working(
            key="active_tasks",
            value=tasks,
            metadata={"source": "rafe", "synced_at": datetime.utcnow().isoformat()}
        )

        return {"active_tasks": len(tasks)}

    async def sync_sessions(self, days_back: int = 7):
        """Sync recent session logs into episodic memory."""
        session_files = await self.mcp.call("rafe-obsidian", "list_docs", {
            "folder": "sessions",
            "recursive": True,
            "include_metadata": True
        })

        synced = 0
        for session_file in session_files:
            # Only sync sessions from the last N days
            session_date = self._extract_date_from_path(session_file["path"])
            if session_date and (datetime.utcnow() - session_date).days <= days_back:
                doc = await self.mcp.call("rafe-obsidian", "get_doc", {
                    "path": session_file["path"]
                })

                await self.memory.add_episode(
                    description=f"Development session on {session_date.strftime('%Y-%m-%d')}",
                    content=doc["content"],
                    metadata={
                        "type": "session",
                        "date": session_date.isoformat(),
                        "source": "rafe"
                    }
                )
                synced += 1

        return {"synced_sessions": synced}

    async def sync_policies(self):
        """Sync policies into procedural memory (behavioral rules)."""
        policy_files = await self.mcp.call("rafe-obsidian", "list_docs", {
            "folder": "policies",
            "include_metadata": True
        })

        for policy_file in policy_files:
            doc = await self.mcp.call("rafe-obsidian", "get_doc", {
                "path": policy_file["path"]
            })

            await self.memory.upsert_procedural(
                key=f"policy:{policy_file['name']}",
                content=doc["content"],
                metadata={
                    "type": "policy",
                    "source": "rafe",
                    "last_updated": policy_file.get("modified", "")
                }
            )

    async def full_sync(self):
        """Run all sync operations."""
        results = {}
        results["decisions"] = await self.sync_decisions()
        results["tasks"] = await self.sync_active_tasks()
        results["sessions"] = await self.sync_sessions()
        results["policies"] = await self.sync_policies()
        return results
```

**Sync scheduling (via n8n or OpenClaw scheduler):**
- Active tasks: every 30 minutes
- Decisions: daily at midnight
- Sessions: daily at midnight
- Policies: on file change (if file watcher available) or daily
- Full sync: weekly on Sunday night

### Approach 3: Bidirectional Integration (Recommended)

**Concept:** RAFE and OpenClaw form a bidirectional knowledge loop. RAFE is the documentation layer; OpenClaw is the operations layer. They keep each other informed.

**Data flow:**

```
RAFE (Documentation Layer)                OpenClaw (Operations Layer)
  |                                          |
  |-- Decisions, research, context --------> | (OpenClaw reads RAFE for context)
  |                                          |
  | <-------- Activity logs, outcomes -------| (OpenClaw writes to RAFE)
  |                                          |
  |-- Task updates, blockers --------------> | (RAFE informs OpenClaw of priorities)
  |                                          |
  | <-------- Task completions, metrics -----| (OpenClaw reports results to RAFE)
```

---

## What to Sync (Detailed)

### Decision Logs

**Direction:** RAFE -> OpenClaw (primary), OpenClaw -> RAFE (when OpenClaw makes decisions)

**Why OpenClaw needs decisions:**
- Avoid re-making decisions that were already made
- Understand constraints and rationale behind architectural choices
- Apply past decisions to new but similar situations

**Example usage:**
1. OpenClaw receives a request to set up a new integration
2. Before starting, it queries memory: "Have we decided on an integration approach for this?"
3. Finds a RAFE decision: "Use n8n as middleware for all inter-service communication"
4. Follows the established decision instead of proposing something different

**When OpenClaw logs decisions to RAFE:**
```python
# After OpenClaw makes an operational decision
await self.mcp.call("rafe-obsidian", "log_decision", {
    "title": "Use Sequence A for dentist leads in Texas",
    "context": "Testing showed Sequence A had 12% response rate vs Sequence B's 6% for dentist leads in Texas metro areas.",
    "options": [
        {
            "name": "Sequence A (pain-point focused)",
            "pros": ["12% response rate", "Higher quality responses"],
            "cons": ["More complex to personalize"]
        },
        {
            "name": "Sequence B (case-study focused)",
            "pros": ["Simpler template", "Reusable across industries"],
            "cons": ["6% response rate for this segment"]
        }
    ],
    "decision": "Use Sequence A for all dentist leads in Texas",
    "rationale": "2x response rate justifies the extra personalization effort. Personalization is automated by OpenClaw anyway.",
    "impact": "medium",
    "tags": ["outreach", "dentists", "texas", "rise-local"]
})
```

### Session History

**Direction:** RAFE -> OpenClaw

**Why OpenClaw needs session history:**
- Understand what was worked on recently (avoid duplicating effort)
- Pick up where previous sessions left off
- Context for current priorities and blockers

**Practical use:** When OpenClaw starts a new work cycle, it reads the last 3-5 session logs to build a working context of recent activity.

```python
# OpenClaw startup routine
async def build_working_context(self):
    """Build context from recent RAFE sessions."""
    recent_sessions = await self.rafe_sync.sync_sessions(days_back=5)

    # Summarize into a concise context prompt
    context = await self.llm.summarize(
        content=recent_sessions,
        prompt="Summarize the last 5 development sessions into a brief context update. "
               "Focus on: what was completed, what is in progress, any blockers, and stated next steps."
    )

    await self.memory.set_working("session_context", context)
```

### Research Notes

**Direction:** RAFE -> OpenClaw

**Why OpenClaw needs research notes:**
- Apply accumulated knowledge when making decisions
- Reference research when creating content or proposals
- Avoid redundant research on topics already investigated

**Specific documents to sync from the OpenClaw Research vault:**

| Document Path | OpenClaw Use |
|---|---|
| `phases/*` | Understand project phases, timelines, dependencies |
| `components/*` | Know what components exist and their status |
| Research documents in topic folders | Domain knowledge for content generation and decision-making |

### Task Status

**Direction:** Bidirectional

**RAFE -> OpenClaw:** OpenClaw reads active tasks to know its priorities.
**OpenClaw -> RAFE:** OpenClaw updates task status as it completes work.

```python
# OpenClaw reads its task queue from RAFE
async def get_my_tasks(self):
    tasks = await self.mcp.call("rafe-obsidian", "get_doc", {
        "path": ".state/active-tasks.md"
    })
    # Filter to tasks assigned to OpenClaw (if tagging is used)
    return self._filter_tasks(tasks["content"], assignee="openclaw")

# OpenClaw marks a task complete
async def complete_task(self, task_description: str, notes: str = ""):
    await self.mcp.call("rafe-obsidian", "update_task_status", {
        "task": task_description,
        "status": "completed",
        "notes": f"[OpenClaw] {notes}" if notes else "[OpenClaw] Completed automatically"
    })
```

---

## Implementation Plan

### Step 1: Add Obsidian MCP as OpenClaw Tool Source

**Actions:**
1. Verify RAFE Obsidian MCP server is running and accessible
2. Configure OpenClaw to connect to it (add to tool sources config)
3. Test basic operations: read a doc, list docs, update a doc
4. Verify write operations work correctly (create a test doc, then delete it)

**Verification script:**
```python
async def verify_rafe_connection():
    """Run after configuring MCP connection to verify it works."""
    tests = []

    # Test 1: Read home document
    try:
        home = await mcp.call("rafe-obsidian", "get_doc", {"path": "_HOME.md"})
        tests.append(("read_home", "pass", f"Got {len(home['content'])} chars"))
    except Exception as e:
        tests.append(("read_home", "fail", str(e)))

    # Test 2: List docs in root
    try:
        docs = await mcp.call("rafe-obsidian", "list_docs", {"folder": "."})
        tests.append(("list_root", "pass", f"Found {len(docs)} docs"))
    except Exception as e:
        tests.append(("list_root", "fail", str(e)))

    # Test 3: List sessions
    try:
        sessions = await mcp.call("rafe-obsidian", "list_docs", {
            "folder": "sessions",
            "recursive": True
        })
        tests.append(("list_sessions", "pass", f"Found {len(sessions)} sessions"))
    except Exception as e:
        tests.append(("list_sessions", "fail", str(e)))

    # Test 4: Read active tasks
    try:
        tasks = await mcp.call("rafe-obsidian", "get_doc", {
            "path": ".state/active-tasks.md"
        })
        tests.append(("read_tasks", "pass", f"Got {len(tasks['content'])} chars"))
    except Exception as e:
        tests.append(("read_tasks", "fail", str(e)))

    return tests
```

### Step 2: Create Sync Skill

**Actions:**
1. Implement `RAFESyncSkill` as shown in Approach 2 above
2. Register it in OpenClaw's skill registry
3. Run initial full sync to populate OpenClaw's memory with all RAFE knowledge
4. Set up scheduled sync (via n8n cron trigger or OpenClaw's internal scheduler)

**n8n sync workflow:**
```
Schedule Trigger (every 30 min for tasks, daily for full sync)
  -> Code Node: determine sync type based on schedule
  -> HTTP Request: call OpenClaw sync endpoint
  -> IF: check for errors
  -> Slack notification (if errors)
```

### Step 3: Create Logging Skill

**Actions:**
1. Implement OpenClaw-to-RAFE logging skill that writes OpenClaw's activities back to RAFE
2. Auto-log: every significant OpenClaw action (lead pipeline run, client email sent, report generated) creates a log entry
3. Session logs: at the end of each OpenClaw work cycle, create a session summary

```python
# openclaw/skills/rafe_logger.py

class RAFELoggerSkill:
    """Logs OpenClaw activities to RAFE Obsidian."""

    async def log_activity(self, focus: str, completed: list[str],
                           decisions: list[str] = None, issues: list[str] = None,
                           next_steps: list[str] = None):
        """Log an OpenClaw work session to RAFE."""
        await self.mcp.call("rafe-obsidian", "log_session", {
            "focus": f"[OpenClaw] {focus}",
            "completed": [f"[OpenClaw] {item}" for item in completed],
            "decisions": [f"[OpenClaw] {d}" for d in (decisions or [])],
            "issues": [f"[OpenClaw] {i}" for i in (issues or [])],
            "next_steps": next_steps or [],
            "notes": "Automatically logged by OpenClaw agent."
        })

    async def log_pipeline_run(self, pipeline_name: str, results: dict):
        """Log a pipeline execution to RAFE."""
        completed = [
            f"Ran {pipeline_name} pipeline",
            f"Processed {results.get('leads_processed', 'N/A')} leads",
            f"Cost: ${results.get('total_cost', 0):.2f}"
        ]
        if results.get('hot_leads', 0) > 0:
            completed.append(f"Found {results['hot_leads']} hot leads")

        await self.log_activity(
            focus=f"Pipeline execution: {pipeline_name}",
            completed=completed
        )

    async def log_client_interaction(self, client_name: str, interaction_type: str,
                                     summary: str):
        """Log a client interaction to RAFE."""
        await self.log_activity(
            focus=f"Client interaction: {client_name}",
            completed=[f"{interaction_type}: {summary}"]
        )
```

### Step 4: Build Context Injection

**Actions:**
1. When OpenClaw starts a task, it pulls relevant RAFE context into its prompt
2. Context is selected based on task type:
   - Code-related task: pull relevant component docs + recent decisions about that component
   - Client task: pull client-specific notes + relevant policies
   - Pipeline task: pull pipeline documentation + recent session logs about pipeline work

```python
# openclaw/context/rafe_context.py

class RAFEContextBuilder:
    """Builds relevant context from RAFE for OpenClaw tasks."""

    async def build_context_for_task(self, task: dict) -> str:
        """Assemble RAFE context relevant to the given task."""
        context_parts = []

        # Always include active tasks for awareness
        tasks = await self.mcp.call("rafe-obsidian", "get_doc", {
            "path": ".state/active-tasks.md"
        })
        context_parts.append(f"## Active Tasks\n{tasks['content']}")

        # Include recent decisions (last 10)
        decisions = await self.mcp.call("rafe-obsidian", "get_doc", {
            "path": "_DECISIONS.md"
        })
        recent_decisions = self._extract_last_n_decisions(decisions["content"], n=10)
        context_parts.append(f"## Recent Decisions\n{recent_decisions}")

        # Include task-specific context
        if "component" in task:
            component_doc = await self.mcp.call("rafe-obsidian", "get_doc", {
                "path": f"components/{task['component']}.md"
            })
            context_parts.append(f"## Component: {task['component']}\n{component_doc['content']}")

        if "phase" in task:
            phase_doc = await self.mcp.call("rafe-obsidian", "get_doc", {
                "path": f"phases/{task['phase']}.md"
            })
            context_parts.append(f"## Current Phase\n{phase_doc['content']}")

        # Last 3 session logs for recent activity context
        # (Implementation: list sessions folder, sort by date, read last 3)

        return "\n\n---\n\n".join(context_parts)
```

---

## Conflict Resolution

### The Problem

Both RAFE (through manual use or other agents) and OpenClaw may try to update the same document. For example:
- You manually update a task status in Obsidian while OpenClaw is also updating it via MCP
- Ralph logs a session at the same time OpenClaw logs one for the same date
- Two processes try to append to `_DECISIONS.md` simultaneously

### Resolution Strategy

**Principle: RAFE is source of truth for documentation. OpenClaw is source of truth for operations.**

| Data Type | Source of Truth | Conflict Resolution |
|---|---|---|
| Decision logs | RAFE | If conflict, RAFE version wins. OpenClaw re-reads after write to confirm. |
| Session logs | RAFE | OpenClaw always appends (never replaces). Multiple entries per day are fine. |
| Task status | OpenClaw | OpenClaw's task updates take priority (it knows what it actually completed). |
| Research notes | RAFE | OpenClaw reads only, never modifies research docs. |
| Component docs | RAFE | OpenClaw reads only, never modifies component docs. |
| Policies | RAFE | OpenClaw reads and follows policies, never modifies them. |
| Activity logs | OpenClaw | OpenClaw writes its own activity sections; RAFE does not modify them. |
| Metrics/analytics | OpenClaw | Operational data flows from OpenClaw to RAFE, not the other way. |

### Technical Safeguards

1. **Atomic writes:** RAFE MCP `update_doc` uses atomic writes. This prevents partial writes but does not prevent overwrite conflicts.

2. **Append-only pattern:** For shared documents like `_DECISIONS.md` and session logs, always use `mode: "append"` instead of `mode: "replace"`. This way, concurrent writes both succeed (both entries are added).

3. **Prefixing:** OpenClaw prefixes all its entries with `[OpenClaw]` so it is always clear which entries came from the agent vs. manual input.

4. **Read-before-write with check:**
```python
async def safe_update(self, path: str, section: str, new_content: str):
    """Read, check, then write with conflict detection."""
    # Read current state
    current = await self.mcp.call("rafe-obsidian", "get_doc", {"path": path})
    current_hash = hashlib.md5(current["content"].encode()).hexdigest()

    # Perform the update
    await self.mcp.call("rafe-obsidian", "update_doc", {
        "path": path,
        "section": section,
        "content": new_content,
        "mode": "replace"
    })

    # Verify the write succeeded as expected
    updated = await self.mcp.call("rafe-obsidian", "get_doc", {"path": path})

    if new_content not in updated["content"]:
        # Write may have been overwritten -- retry or alert
        await self.alert("RAFE write conflict detected", {
            "path": path,
            "section": section,
            "action": "Retrying in 5 seconds"
        })
        await asyncio.sleep(5)
        # Retry once
        await self.mcp.call("rafe-obsidian", "update_doc", {
            "path": path, "section": section, "content": new_content, "mode": "replace"
        })
```

5. **Write locking (advanced, optional):**
   - Use a Supabase row as a distributed lock: `locks` table with `resource_name` and `locked_by`
   - Before writing to a RAFE document, acquire lock; release after write
   - Timeout: 30 seconds (if lock is held longer, it is considered stale)

---

## Operational Recommendations

### Daily Workflow

1. **Morning (6 AM):** Full RAFE sync runs. OpenClaw starts the day with fresh context.
2. **During work:** OpenClaw reads RAFE as needed for specific tasks. Writes activity logs after completing significant work.
3. **Evening (10 PM):** OpenClaw logs a summary session to RAFE covering the day's activities.
4. **On demand:** Any time you manually update RAFE (add decisions, update tasks, write notes), OpenClaw picks it up within 30 minutes via the task sync or at the next daily sync.

### What NOT to Sync

- **Obsidian plugin settings or vault configuration** -- these are editor-specific, not knowledge
- **Draft or incomplete research notes** -- only sync finalized research
- **Temporary scratch notes** -- if you use Obsidian for quick jottings, keep those in a folder that is excluded from sync
- **Binary attachments** (images, PDFs in the vault) -- sync text content only

### Monitoring the Integration

Track these metrics to ensure the RAFE-OpenClaw integration is healthy:

| Metric | Target | Alert If |
|---|---|---|
| Sync latency (task sync) | < 1 minute | > 5 minutes |
| Sync latency (full sync) | < 5 minutes | > 15 minutes |
| Sync failures per day | 0 | > 3 |
| Write conflicts per week | 0 | > 2 |
| RAFE MCP server uptime | 99.9% | Any downtime > 10 minutes |
| OpenClaw context build time | < 3 seconds | > 10 seconds |
| Documents in sync | 100% of targeted docs | Any doc missed for > 24 hours |

### Cost Implications

The RAFE-OpenClaw integration has minimal direct cost:
- MCP calls are local (no API fees)
- Obsidian is free for local use
- The only cost is the LLM tokens used when OpenClaw processes RAFE content (summarization, context building)
- Estimated: 500-2,000 tokens per sync cycle for summarization = $0.01-0.05 per sync = $0.30-1.50/month

# Phase 2: Memory and Model Routing - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Give the agent persistent memory (write/recall across sessions), hybrid search (keyword + semantic), daily log compaction, and intelligent model routing with cost-aware tier selection and prompt caching. This is internal infrastructure — every subsequent phase depends on the agent being able to remember, search, and route requests cost-effectively. Restore, advanced RAG, and per-client memory scoping are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Memory write policy
- Hybrid auto-capture: auto-persist high-confidence items (client decisions, project facts, tool configs); explicit persist for subjective preferences and opinions; agent asks "should I remember this?" for borderline cases
- When MEMORY.md approaches 4,000 token budget, compress related entries into denser summaries — nothing is truly lost, just condensed
- Organize memory by topic, not chronologically — group related memories together (client prefs, project decisions, tool configs)
- MEMORY.md serves as an index with summaries; detailed context overflows into separate topic files (e.g., `clients.md`, `tools.md`)

### Search and retrieval
- Smart prefetch: auto-search memory for tasks involving clients, projects, or past decisions; skip for generic/simple tasks (formatting, math, one-off questions); agent can always search on-demand
- When no relevant results found, agent briefly notes "I don't have prior context on X" and continues — transparent but non-blocking
- Query-adaptive RRF weights: lean toward keyword (FTS5) for exact names/terms (client names, tool configs); lean toward semantic (Qdrant) for conceptual queries (past decisions about X); agent classifies the query type first
- Return top 3 results by default; agent can request more if confidence is low

### Log lifecycle
- Daily logs capture significant actions only: tasks completed, decisions made, client interactions, errors encountered — not every API call or file read
- Weekly compaction (after 30 days): preserve outcomes plus notable context — what happened and why when it matters
- Further compaction: weekly summaries compact to monthly summaries after 90 days; monthly summaries persist indefinitely
- Proactively surface log insights: agent identifies trends and patterns from logs and surfaces them during check-ins or when contextually relevant

### Model routing rules
- Default to the most capable tier likely to succeed first try; agent learns over time which tasks can be safely downgraded to cheaper tiers
- Core 4-tier system: Ollama qwen3:14b (free, classification/formatting) -> Haiku (standard tasks) -> Sonnet (reasoning) -> Opus (client-facing quality)
- On fallback (tier unavailable): auto-escalate silently, log the event, surface in next check-in — "Ollama was down for 2 hours, routed 15 tasks to Haiku instead"
- Daily cost summary: track tokens and costs per model per day, surface in daily log and weekly summaries

### Claude's Discretion
- Kimi and Gemini placement — start with the core Claude + Ollama stack, add alternative models for specific niches as they prove useful during implementation
- Exact compaction algorithms and scheduling
- Embedding model configuration details for Qdrant
- Prompt caching implementation specifics
- FTS5 tokenizer tuning

</decisions>

<specifics>
## Specific Ideas

- Memory overflow files should feel like natural extensions of MEMORY.md — same formatting, same topic-based organization, just deeper
- Cost summaries should look like: "Today: $0.42 total — Haiku $0.28, Sonnet $0.12, Opus $0.02, Ollama $0.00"
- Log compaction should preserve the "arc" of activity — not just isolated facts but the narrative thread

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-memory-and-model-routing*
*Context gathered: 2026-02-28*

# Self-Evolution Architecture

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Memory Architecture](../04-Memory-and-RAG/memory-architecture.md), [HITL](../02-Security/human-in-the-loop.md), [Skill Development](../05-Skills-Development/)

---

## 1. What Self-Evolution Means

Self-evolution is the agent's ability to improve itself over time -- rewriting prompts, creating new skills, discovering new tools, and expanding capabilities -- without requiring the user to manually reconfigure anything.

**Key distinction:** Self-evolution is NOT unsupervised autonomy. Every modification goes through a notification and approval pipeline. The agent proposes changes; the human decides.

---

## 2. Evolution Loop

The core cycle runs continuously:

```
+---> OBSERVE ----> EVALUATE ----> PROPOSE ----> NOTIFY ----> ACT ----> MEASURE ---+
|                                                                                    |
+------------------------------------------------------------------------------------+
```

| Stage | What Happens | Implementation |
|-------|-------------|----------------|
| **Observe** | Collect metrics from every agent session: success/failure, latency, cost, HITL approval rate, error types | Metrics table in Supabase + daily log entries |
| **Evaluate** | Analyze metrics against targets. Identify regressions, inefficiencies, repeated failures, missing capabilities | Scheduled evaluation agent (weekly cron) |
| **Propose** | Generate specific improvement proposals: prompt rewrites, new skill definitions, tool additions | LLM generates proposals with reasoning and expected impact |
| **Notify** | Send proposals to user via Telegram with category tags (informational, advisory, critical) | Telegram bot with inline approval buttons |
| **Act** | If approved, apply the change. If auto-approved (low-risk), apply with logging | Git-versioned changes to prompts/skills/config |
| **Measure** | Track metrics after the change. Compare to baseline. Auto-rollback if regression detected | A/B comparison over 48-hour window |

---

## 3. Evolution Subsystems

### 3.1 Prompt Optimization

The agent rewrites its own system prompts and skill prompts based on performance data.

**Approach:** Meta-prompting -- an LLM analyzes task outcomes and rewrites the prompt that produced them, targeting specific failure modes.

See [Prompt Optimization](prompt-optimization.md) for full details.

### 3.2 Skill Auto-Generation

The agent detects repeated requests for missing capabilities and scaffolds new skills.

**Approach:** Pattern detection in daily logs + skill scaffolding via `openclaw skill create` + test-before-deploy pipeline.

See [Skill Auto-Generation](skill-auto-generation.md) for full details.

### 3.3 Tool Discovery

The agent programmatically searches ClawHub and evaluates community-built skills for quality, safety, and relevance.

**Approach:** Scheduled ClawHub API queries filtered by the agent's current capability gaps + quality scoring + HITL approval before installation.

See [Skill Auto-Generation](skill-auto-generation.md) Section 5 for ClawHub integration.

### 3.4 Safety Guardrails

Immutable constraints that the evolution system cannot modify, rate limits on changes, and mandatory rollback on regression.

See [Safety Guardrails](safety-guardrails.md) for full details.

### 3.5 Notification System

Categorized Telegram notifications for all evolution activity.

See [Notification System](notification-system.md) for full details.

---

## 4. Metrics Collection

### 4.1 Core Metrics

```sql
-- Evolution metrics table (Supabase)
CREATE TABLE evolution_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Session context
    session_id UUID REFERENCES sessions(id),
    skill_name TEXT,
    action TEXT,

    -- Outcome
    success BOOLEAN NOT NULL,
    error_type TEXT,              -- 'hallucination', 'api_failure', 'timeout', 'wrong_output', etc.
    error_message TEXT,

    -- Performance
    duration_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC(10,6),

    -- Quality signals
    hitl_required BOOLEAN DEFAULT false,
    hitl_approved BOOLEAN,
    hitl_latency_seconds INTEGER,
    user_feedback TEXT,          -- 'positive', 'negative', 'neutral', NULL

    -- Model info
    model_used TEXT,
    prompt_version TEXT,         -- Git SHA or version tag of the prompt used

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_evo_metrics_skill ON evolution_metrics(skill_name);
CREATE INDEX idx_evo_metrics_success ON evolution_metrics(success);
CREATE INDEX idx_evo_metrics_created ON evolution_metrics(created_at DESC);
CREATE INDEX idx_evo_metrics_prompt ON evolution_metrics(prompt_version);
```

### 4.2 Derived Metrics (Computed Weekly)

| Metric | Calculation | Target | Action if Below Target |
|--------|------------|--------|----------------------|
| Task success rate | `successful / total` per skill | > 90% | Trigger prompt review |
| HITL approval rate | `approved / required` per skill | > 80% | Agent is proposing bad actions -- review prompts |
| Average latency | `AVG(duration_ms)` per skill | < 5000ms | Optimize prompt or switch model |
| Cost per operation | `AVG(cost_usd)` per skill | Varies by skill | Consider model downgrade or caching |
| Error frequency by type | `COUNT(error_type)` grouped | Trending down | Investigate persistent error categories |
| User feedback ratio | `positive / (positive + negative)` | > 75% | Review output quality |

### 4.3 Evaluation Agent

A dedicated evaluation agent runs weekly (Sunday 3 AM, same schedule as memory compaction):

```yaml
# evolution-evaluator.yaml
name: evolution-evaluator
trigger:
  cron: "0 3 * * 0"  # Every Sunday at 3 AM
steps:
  - query_metrics:
      sql: |
        SELECT skill_name,
               COUNT(*) as total,
               COUNT(*) FILTER (WHERE success) as successes,
               AVG(duration_ms) as avg_latency,
               AVG(cost_usd) as avg_cost,
               COUNT(*) FILTER (WHERE hitl_approved = false) as rejections
        FROM evolution_metrics
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY skill_name
  - analyze:
      model: claude-sonnet
      prompt: |
        Analyze these weekly agent metrics. For each skill:
        1. Is it meeting performance targets?
        2. Are there regression patterns?
        3. What specific improvements would help?
        Generate concrete proposals (prompt changes, model switches, caching opportunities).
  - generate_proposals:
      output: evolution_proposals table
  - notify:
      channel: telegram
      category: advisory
      message: "Weekly evolution report ready. {summary}. {proposal_count} improvements proposed."
```

---

## 5. Version Control for Agent Configuration

Every modifiable component is Git-versioned:

```
~/.openclaw/
  prompts/                    # System prompts (Git-tracked)
    system-prompt.md          # Main agent system prompt
    skill-prompts/
      lead-enrichment.md
      crm-management.md
      presentation-gen.md
      ...
  skills/                     # Skill definitions (Git-tracked)
    lead-enrichment.yaml
    crm-management.yaml
    ...
  config/                     # Agent configuration (Git-tracked)
    model-routing.yaml
    approval-policy.yaml
    ...
```

**Git workflow for changes:**

```bash
# Before any evolution change
cd ~/.openclaw
git checkout -b evolution/$(date +%Y%m%d)-prompt-optimization

# Apply changes
# ... (agent modifies files)

# Commit with metadata
git add -A
git commit -m "evolution: optimize lead-enrichment prompt

Metrics: success rate 82% -> target 90%
Change: added explicit output format instructions
Trigger: weekly evaluation 2026-02-23
Rollback: git revert HEAD"

# After 48-hour measurement period, if metrics improved:
git checkout main
git merge evolution/20260223-prompt-optimization

# If metrics regressed:
git checkout main
git branch -d evolution/20260223-prompt-optimization
```

---

## 6. Evolution Proposals Table

```sql
CREATE TABLE evolution_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Proposal details
    proposal_type TEXT NOT NULL CHECK (proposal_type IN (
        'prompt_rewrite', 'new_skill', 'tool_install',
        'model_switch', 'config_change', 'skill_retire'
    )),
    target TEXT NOT NULL,          -- skill name, prompt path, or config key
    description TEXT NOT NULL,     -- Human-readable description
    reasoning TEXT NOT NULL,       -- Why this change is proposed
    expected_impact TEXT,          -- Predicted improvement

    -- Change content
    diff TEXT,                     -- Unified diff of the proposed change
    new_content TEXT,              -- Full new content (for new skills)

    -- Approval
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'approved', 'rejected', 'applied', 'rolled_back'
    )),
    approved_by TEXT,             -- 'user' or 'auto'
    approved_at TIMESTAMPTZ,

    -- Measurement
    baseline_metrics JSONB,       -- Metrics before change
    post_change_metrics JSONB,    -- Metrics after change (filled after 48h)
    improvement_observed BOOLEAN, -- Did metrics improve?

    -- Git
    branch_name TEXT,             -- Git branch for this change
    commit_sha TEXT,              -- Git commit SHA

    created_at TIMESTAMPTZ DEFAULT NOW(),
    measured_at TIMESTAMPTZ       -- When post-change measurement completed
);

CREATE INDEX idx_proposals_status ON evolution_proposals(status);
CREATE INDEX idx_proposals_type ON evolution_proposals(proposal_type);
CREATE INDEX idx_proposals_created ON evolution_proposals(created_at DESC);
```

---

## 7. Implementation Priority

| Order | Component | Effort | Value |
|-------|-----------|--------|-------|
| 1 | Metrics collection (evolution_metrics table + logging) | 4-6h | Foundation -- everything depends on this |
| 2 | Weekly evaluation agent | 4-6h | Identifies improvement opportunities |
| 3 | Telegram notification integration | 2-3h | Keeps user informed |
| 4 | Prompt optimization (meta-prompting) | 8-12h | Highest ROI improvement mechanism |
| 5 | Git version control for prompts/skills | 4-6h | Enables safe rollback |
| 6 | Skill auto-generation | 8-12h | Expands capabilities |
| 7 | ClawHub tool discovery | 4-6h | Leverages community |
| 8 | Full A/B testing framework | 8-12h | Rigorous measurement |

**Total estimated effort:** 42-63 hours across 4-6 weeks

---

## Next Steps

- [Prompt Optimization](prompt-optimization.md) -- Meta-prompting and A/B testing
- [Skill Auto-Generation](skill-auto-generation.md) -- Detecting gaps and building new skills
- [Safety Guardrails](safety-guardrails.md) -- Immutable constraints and rollback
- [Notification System](notification-system.md) -- Telegram categories and approval flows

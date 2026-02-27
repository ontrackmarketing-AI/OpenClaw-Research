# Prompt Optimization

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Evolution Architecture](evolution-architecture.md), [Memory Architecture](../04-Memory-and-RAG/memory-architecture.md)

---

## 1. The Problem

Agent prompts degrade over time as the environment changes: new API formats, shifting user preferences, evolving data patterns. Manual prompt tuning is tedious and reactive. The agent should identify when prompts are underperforming and propose improvements.

---

## 2. Meta-Prompting Approach

Meta-prompting uses an LLM to rewrite the prompts used by another LLM (or itself). The meta-prompt receives:
- The current prompt
- Recent task outcomes (successes and failures)
- Specific failure examples with context
- Performance metrics

And produces a revised prompt targeting the identified failure modes.

### 2.1 Meta-Prompt Template

```markdown
You are a prompt optimization specialist. Your job is to improve an AI agent's
system prompt based on its recent performance data.

## Current Prompt
{current_prompt}

## Performance Summary (Last 7 Days)
- Success rate: {success_rate}% (target: {target}%)
- Common failure types: {failure_types}
- HITL rejection rate: {rejection_rate}%

## Failure Examples (5 most informative)
{failure_examples}

## Success Examples (3 representative)
{success_examples}

## Instructions
1. Identify specific patterns in the failures that the current prompt does not address.
2. Propose a revised prompt that:
   - Preserves all working behaviors (do not break what works)
   - Adds explicit instructions to prevent the identified failure modes
   - Keeps total length within 20% of the original
3. Explain each change you made and why.
4. Rate your confidence in the improvement (1-10).

## Output Format
### Analysis
[Your analysis of failure patterns]

### Revised Prompt
[The complete revised prompt]

### Change Log
- Change 1: [what changed] -- [why]
- Change 2: [what changed] -- [why]
...

### Confidence: [1-10]
```

### 2.2 Optimization Pipeline

```python
async def optimize_prompt(skill_name: str) -> dict:
    """Run prompt optimization for a specific skill."""

    # 1. Load current prompt
    current_prompt = load_prompt(f"prompts/skill-prompts/{skill_name}.md")

    # 2. Gather metrics
    metrics = await supabase.rpc("get_skill_metrics", {
        "skill": skill_name,
        "days": 7
    })

    # 3. Get failure examples
    failures = await supabase.table("evolution_metrics").select("*").eq(
        "skill_name", skill_name
    ).eq("success", False).order(
        "created_at", desc=True
    ).limit(5).execute()

    # 4. Get success examples for contrast
    successes = await supabase.table("evolution_metrics").select("*").eq(
        "skill_name", skill_name
    ).eq("success", True).order(
        "created_at", desc=True
    ).limit(3).execute()

    # 5. Run meta-prompt
    result = await llm.generate(
        model="claude-sonnet",
        system="You are a prompt optimization specialist.",
        prompt=META_PROMPT_TEMPLATE.format(
            current_prompt=current_prompt,
            success_rate=metrics["success_rate"],
            target=metrics["target"],
            failure_types=metrics["failure_types"],
            rejection_rate=metrics["rejection_rate"],
            failure_examples=format_examples(failures.data),
            success_examples=format_examples(successes.data),
        )
    )

    # 6. Parse and return proposal
    return {
        "skill_name": skill_name,
        "current_prompt": current_prompt,
        "revised_prompt": extract_revised_prompt(result),
        "change_log": extract_change_log(result),
        "confidence": extract_confidence(result),
        "metrics_snapshot": metrics,
    }
```

---

## 3. A/B Testing Framework

After a prompt change is proposed and approved, the system runs both versions for 48 hours to measure the impact.

### 3.1 A/B Test Design

```yaml
# ab-test-config.yaml
ab_testing:
  enabled: true
  default_duration_hours: 48
  min_samples_per_variant: 20   # Need at least 20 executions per variant
  traffic_split: 50             # 50% old prompt, 50% new prompt
  success_metric: task_success_rate
  secondary_metrics:
    - avg_latency_ms
    - avg_cost_usd
    - hitl_approval_rate
  auto_rollback_threshold: 0.10  # Rollback if new variant is >10% worse
  auto_promote_threshold: 0.05   # Auto-promote if new variant is >5% better
```

### 3.2 A/B Test Execution

```python
class PromptABTest:
    """Manages A/B testing of prompt variants."""

    def __init__(self, skill_name: str, variant_a: str, variant_b: str):
        self.skill_name = skill_name
        self.variant_a = variant_a  # Current prompt
        self.variant_b = variant_b  # Proposed prompt
        self.test_id = str(uuid4())
        self.started_at = datetime.utcnow()

    def select_variant(self) -> tuple[str, str]:
        """Select which prompt variant to use for this execution."""
        if random.random() < 0.5:
            return self.variant_a, "A"
        return self.variant_b, "B"

    async def record_result(self, variant_label: str, success: bool,
                            latency_ms: int, cost_usd: float):
        """Record the outcome of a test execution."""
        await supabase.table("ab_test_results").insert({
            "test_id": self.test_id,
            "skill_name": self.skill_name,
            "variant": variant_label,
            "success": success,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "created_at": datetime.utcnow().isoformat(),
        })

    async def evaluate(self) -> dict:
        """Evaluate test results after the test period."""
        results = await supabase.table("ab_test_results").select("*").eq(
            "test_id", self.test_id
        ).execute()

        a_results = [r for r in results.data if r["variant"] == "A"]
        b_results = [r for r in results.data if r["variant"] == "B"]

        a_success_rate = sum(1 for r in a_results if r["success"]) / len(a_results)
        b_success_rate = sum(1 for r in b_results if r["success"]) / len(b_results)

        improvement = b_success_rate - a_success_rate

        return {
            "test_id": self.test_id,
            "a_success_rate": a_success_rate,
            "b_success_rate": b_success_rate,
            "improvement": improvement,
            "recommendation": "promote" if improvement > 0.05
                            else "rollback" if improvement < -0.10
                            else "inconclusive",
            "a_samples": len(a_results),
            "b_samples": len(b_results),
        }
```

### 3.3 A/B Test Results Table

```sql
CREATE TABLE ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID NOT NULL,
    skill_name TEXT NOT NULL,
    variant TEXT NOT NULL CHECK (variant IN ('A', 'B')),
    success BOOLEAN NOT NULL,
    latency_ms INTEGER,
    cost_usd NUMERIC(10,6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ab_test_id ON ab_test_results(test_id);
CREATE INDEX idx_ab_skill ON ab_test_results(skill_name);
```

---

## 4. Prompt Versioning

Every prompt change is tracked:

```sql
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    change_reason TEXT,
    metrics_at_creation JSONB,     -- Metrics when this version was created
    metrics_after_48h JSONB,       -- Metrics 48 hours after deployment
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'testing', 'retired', 'rolled_back')),
    git_commit_sha TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(skill_name, version)
);

CREATE INDEX idx_prompt_versions_skill ON prompt_versions(skill_name);
CREATE INDEX idx_prompt_versions_status ON prompt_versions(status);
```

---

## 5. Optimization Triggers

| Trigger | Condition | Action |
|---------|-----------|--------|
| Success rate drop | Skill success rate drops below target for 3+ consecutive days | Queue prompt review |
| High rejection rate | HITL rejection rate > 20% for a skill | Queue prompt review |
| New error pattern | New error type appears 5+ times in a week | Queue targeted prompt fix |
| Cost spike | Cost per operation increases > 25% vs previous week | Review prompt length and model routing |
| User feedback | 3+ negative feedback signals for a skill | Queue prompt review |
| Scheduled | Weekly evaluation (Sunday 3 AM) | Review all skills against targets |

---

## 6. Research References

- **DSPy** (Stanford): Compiles declarative LM pipelines into optimized prompts. Uses bootstrapping and optimization to find effective prompt configurations automatically.
- **OPRO** (Google DeepMind): Optimization by PROmpting -- uses LLMs to iteratively generate and evaluate prompt candidates.
- **PromptBreeder** (DeepMind): Evolutionary approach where prompts mutate and are selected based on task performance.
- **Langfuse/LangSmith**: Production observability platforms that track prompt performance metrics, enabling data-driven optimization.

**OpenClaw approach:** Simpler than academic frameworks. Use meta-prompting (LLM rewrites prompts) with A/B testing for validation. No complex evolutionary algorithms -- direct performance feedback loop.

---

## Next Steps

- [Evolution Architecture](evolution-architecture.md) -- Overall system design
- [Safety Guardrails](safety-guardrails.md) -- Constraints on prompt changes
- [Notification System](notification-system.md) -- Alerting on optimization results

# Self-Evolution Safety Guardrails

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Evolution Architecture](evolution-architecture.md), [HITL](../02-Security/human-in-the-loop.md)

---

## 1. The Core Principle

As autonomy increases, guardrails must increase proportionally. Self-evolution grants the agent more power -- the ability to rewrite its own prompts, create new skills, install external tools. This demands stricter, not weaker, safety constraints.

**The lesson from the OpenClaw Gmail Incident (2026):** An agent given instructions to "suggest changes and wait for approval" instead bulk-trashed hundreds of emails without showing its plan. Approval gates must be enforced at the execution layer, not just the prompt layer.

---

## 2. Seven-Layer Safety Architecture

### Layer 1: Immutable Invariants

Properties the evolution system can NEVER modify, regardless of any optimization signal.

```yaml
# immutable-invariants.yaml (read-only, agent has no write access)
invariants:
  # HITL requirements
  - name: external_message_approval
    rule: "All external-facing messages (email, SMS, social) require human approval"
    enforceable: execution_layer
    modifiable: false

  - name: deletion_approval
    rule: "All delete operations require human approval"
    enforceable: execution_layer
    modifiable: false

  - name: financial_approval
    rule: "Operations with cost > $5 require human approval"
    enforceable: execution_layer
    modifiable: false

  # Budget limits
  - name: max_cost_per_operation
    rule: "No single operation may exceed $10 without approval"
    value: 10.00
    modifiable: false

  - name: daily_budget_cap
    rule: "Total daily spend cannot exceed $50"
    value: 50.00
    modifiable: false

  # Self-modification limits
  - name: prompt_change_rate
    rule: "Maximum 1 system prompt change per 24 hours"
    value: 1
    period: "24h"
    modifiable: false

  - name: skill_install_rate
    rule: "Maximum 3 new skill installations per week"
    value: 3
    period: "7d"
    modifiable: false

  - name: no_self_modify_invariants
    rule: "The evolution system cannot modify this invariants file"
    enforceable: file_permissions
    modifiable: false

  # Scope limits
  - name: no_credential_access
    rule: "Evolution system cannot access, modify, or create credentials"
    modifiable: false

  - name: no_security_config_changes
    rule: "Evolution system cannot modify security configurations (Docker, Tailscale, firewall)"
    modifiable: false

  - name: no_hitl_policy_weakening
    rule: "Evolution system cannot move any action from Tier 1 (always approve) to Tier 2 (auto-approve)"
    modifiable: false
```

**Enforcement:** Invariants are stored in a file with restricted permissions (`chmod 444`). The evolution engine reads them before applying any change and aborts if a violation would occur. A separate watchdog process monitors the invariants file for unauthorized modifications.

### Layer 2: Rate Limiting

```yaml
# evolution-rate-limits.yaml
rate_limits:
  prompt_changes:
    max_per_day: 1
    max_per_week: 3
    cooldown_after_rollback: 72h  # Wait 3 days after a rollback before trying again

  skill_installations:
    max_per_week: 3
    max_per_month: 8

  config_changes:
    max_per_day: 2
    max_per_week: 5

  model_routing_changes:
    max_per_week: 2

  total_modifications:
    max_per_day: 3
    max_per_week: 10
```

### Layer 3: Mandatory Rollback on Regression

```python
class RegressionDetector:
    """Monitor metrics after a change and auto-rollback if regression detected."""

    def __init__(self, proposal_id: str, baseline_metrics: dict):
        self.proposal_id = proposal_id
        self.baseline = baseline_metrics
        self.measurement_window = timedelta(hours=48)
        self.check_interval = timedelta(hours=4)

    async def monitor(self):
        """Check metrics every 4 hours for 48 hours."""
        start = datetime.utcnow()
        while datetime.utcnow() - start < self.measurement_window:
            await asyncio.sleep(self.check_interval.total_seconds())

            current = await get_current_metrics(self.proposal_id)

            # Check for regression
            if self.is_regression(current):
                await self.rollback()
                return "rolled_back"

        # After 48h with no regression, mark as successful
        return "promoted"

    def is_regression(self, current: dict) -> bool:
        """Detect if current metrics represent a regression."""
        checks = [
            # Success rate dropped more than 5 percentage points
            current["success_rate"] < self.baseline["success_rate"] - 0.05,
            # Approval rate dropped more than 10 percentage points
            current["approval_rate"] < self.baseline["approval_rate"] - 0.10,
            # Cost increased more than 25%
            current["avg_cost"] > self.baseline["avg_cost"] * 1.25,
            # Latency increased more than 50%
            current["avg_latency"] > self.baseline["avg_latency"] * 1.50,
        ]
        return any(checks)

    async def rollback(self):
        """Revert the change and notify user."""
        # Git revert
        proposal = await get_proposal(self.proposal_id)
        subprocess.run(["git", "revert", "--no-edit", proposal["commit_sha"]])

        # Update proposal status
        await supabase.table("evolution_proposals").update({
            "status": "rolled_back",
            "post_change_metrics": await get_current_metrics(self.proposal_id),
            "improvement_observed": False,
        }).eq("id", self.proposal_id).execute()

        # Notify user
        await telegram.send(
            category="critical",
            message=f"Auto-rollback: {proposal['description']}\n"
                    f"Reason: Metrics regressed below baseline.\n"
                    f"The change has been reverted."
        )
```

### Layer 4: Tiered Human Approval

| Change Type | Risk Level | Approval Required | Timeout Behavior |
|------------|------------|-------------------|------------------|
| Few-shot example swap | Low | Auto-approve if regression tests pass | N/A |
| Prompt instruction rewrite | Medium | Notify via Telegram, auto-approve after 24h if no objection | Apply after 24h |
| New skill creation (auto-generated) | Medium-High | Explicit approval via Telegram | Reject after 48h |
| Community skill installation | High | Explicit approval via Telegram | Reject after 48h |
| Model routing change | Medium | Notify, auto-approve after 12h | Apply after 12h |
| Permission scope change | Critical | Explicit approval, no auto-approve | Reject after 72h |

### Layer 5: Constitutional Self-Critique

Before finalizing any self-modification, a separate evaluator reviews the change:

```python
async def constitutional_review(proposal: dict) -> dict:
    """Review a proposed change against safety principles."""
    result = await llm.generate(
        model="claude-sonnet",
        prompt=f"""You are a safety reviewer for an AI agent's self-modification system.

Review this proposed change against the safety constitution below.

## Proposed Change
Type: {proposal['proposal_type']}
Target: {proposal['target']}
Description: {proposal['description']}
Diff: {proposal['diff']}

## Safety Constitution
1. The change must not weaken any human approval requirements.
2. The change must not expand the agent's access to external services.
3. The change must not increase financial risk beyond existing budgets.
4. The change must not enable the agent to send unsupervised communications.
5. The change must not modify security configurations.
6. The change must not degrade output quality for any existing capability.
7. The change must be fully reversible.

## Review
For each principle, state whether the change PASSES or FAILS, with reasoning.
Then give an overall verdict: APPROVE or REJECT.
"""
    )
    return parse_review_result(result)
```

### Layer 6: Canary Deployment

All changes go through a canary phase before full rollout:

```yaml
canary:
  traffic_percentage: 10        # 10% of requests use the new version
  min_observation_hours: 4      # Minimum observation before evaluation
  min_samples: 20               # Need at least 20 executions in canary
  promotion_criteria:
    success_rate_delta: ">= -0.02"  # No more than 2% worse
    latency_delta: "<= 1.20"        # No more than 20% slower
    cost_delta: "<= 1.15"           # No more than 15% more expensive
  auto_rollback_on_error_spike: true
```

### Layer 7: Audit Trail

Every self-modification is permanently logged:

```sql
CREATE TABLE evolution_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID REFERENCES evolution_proposals(id),

    -- What happened
    action TEXT NOT NULL,       -- 'proposed', 'approved', 'rejected', 'applied',
                                -- 'canary_started', 'promoted', 'rolled_back'
    actor TEXT NOT NULL,        -- 'system', 'user', 'auto-approve', 'regression-detector'

    -- Context
    details JSONB NOT NULL DEFAULT '{}',
    metrics_snapshot JSONB,

    -- Immutable
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Append-only: no UPDATE or DELETE allowed
REVOKE UPDATE, DELETE ON evolution_audit_log FROM openclaw_service;

CREATE INDEX idx_audit_proposal ON evolution_audit_log(proposal_id);
CREATE INDEX idx_audit_created ON evolution_audit_log(created_at DESC);
CREATE INDEX idx_audit_action ON evolution_audit_log(action);
```

---

## 3. Emergency Stop for Self-Evolution

If the evolution system behaves unexpectedly:

```bash
# Freeze all evolution activity
cat > ~/.openclaw/config/evolution-freeze.yaml << 'YAML'
evolution:
  frozen: true
  reason: "Manual freeze - investigating unexpected behavior"
  frozen_at: "2026-03-15T14:30:00Z"
  frozen_by: "user"
YAML

# Or via Telegram
# /evolution freeze
# /evolution unfreeze
```

When frozen:
- No new proposals are generated
- No pending proposals are applied
- Existing canary tests are halted and rolled back
- Metrics collection continues (for investigation)

---

## 4. What the Evolution System Cannot Do

Explicit prohibitions, enforced at the code level (not just prompt level):

| Prohibited Action | Why | Enforcement |
|-------------------|-----|-------------|
| Modify invariants file | Would remove safety constraints | File permissions (read-only) |
| Weaken HITL requirements | Could lead to unsupervised destructive actions | Invariant check before apply |
| Access credentials or API keys | Could enable unauthorized external access | Environment variable isolation |
| Modify Docker or network configuration | Could expand attack surface | No access to Docker socket |
| Create external network connections | Could exfiltrate data | Network policy enforcement |
| Modify the evolution engine itself | Recursive self-modification is unbounded | Code signing / integrity check |
| Override rate limits | Could enable rapid uncontrolled changes | Rate limits enforced in database |
| Delete audit logs | Would destroy accountability trail | REVOKE DELETE on audit table |

---

## 5. Security Checklist

- [ ] Invariants file created and permissions set to read-only
- [ ] Rate limits configured in evolution-rate-limits.yaml
- [ ] Regression detector active with 48-hour monitoring window
- [ ] Tiered approval system integrated with Telegram
- [ ] Constitutional review prompt tested and validated
- [ ] Canary deployment pipeline functional
- [ ] Audit log table created with DELETE revoked
- [ ] Emergency freeze command tested via Telegram
- [ ] Watchdog process monitoring invariants file integrity
- [ ] All evolution changes tracked in Git with signed commits

---

## Next Steps

- [Evolution Architecture](evolution-architecture.md) -- Overall system design
- [HITL](../02-Security/human-in-the-loop.md) -- Approval system integration
- [Notification System](notification-system.md) -- Evolution alerting

# Phase 13 - Self-Evolution (Week 14-18)

> **Depends on:** All previous phases (self-evolution benefits from all systems being stable and generating metrics)

## Goal

Deploy the self-evolution system that continuously improves the agent through prompt optimization, skill auto-generation, and tool discovery -- all within strict safety guardrails with human approval.

---

## Prerequisites

- [ ] All core skills operational and generating metrics (Phases 4-8)
- [ ] Telegram HITL approval flow working (Phase 6)
- [ ] Memory system and daily logs active (Phase 3)
- [ ] Supabase operational for metrics storage (Phase 5)
- [ ] Git initialized for `~/.openclaw/` directory (version control)

---

## Week 14-15: Metrics + Evaluation

### Week 14: Metrics Collection

1. Create `evolution_metrics` table in Supabase
2. Instrument all existing skills to emit metrics (success/failure, latency, cost, tokens, HITL approval)
3. Verify metrics are flowing: run 20+ skill executions, check Supabase
4. Create `evolution_proposals` table
5. Create `evolution_audit_log` table (with DELETE revoked)

### Week 15: Evaluation Agent

1. Build the weekly evaluation agent (cron: Sunday 3 AM)
2. Implement metrics aggregation queries (success rate, approval rate, cost, latency per skill)
3. Implement regression detection (compare current week vs 7-day rolling baseline)
4. Test: inject simulated metric degradation, verify evaluation agent flags it
5. Wire Telegram notification for weekly evolution report

---

## Week 16: Safety Guardrails + Prompt Optimization

### Day 1-2: Safety Infrastructure

1. Create `immutable-invariants.yaml` with read-only permissions
2. Implement rate limit enforcement (max 1 prompt change/day, 3/week)
3. Build the regression detector with 48-hour monitoring and auto-rollback
4. Test rollback: apply a deliberately bad prompt change, verify auto-rollback triggers

### Day 3-4: Constitutional Review

1. Implement the constitutional self-critique evaluator
2. Test with 5 benign and 5 adversarial proposals, verify correct classification
3. Wire constitutional review into the proposal pipeline (review before apply)

### Day 5-7: Meta-Prompting

1. Build the meta-prompt template for prompt optimization
2. Implement the optimization pipeline (gather metrics → select underperforming skill → run meta-prompt → generate proposal)
3. Test: identify a skill with < 90% success rate, generate an optimization proposal
4. Implement proposal notification via Telegram with inline approve/reject buttons
5. Test full flow: detect regression → propose fix → notify → approve → apply → monitor

---

## Week 17: A/B Testing + Skill Auto-Generation

### Day 1-3: A/B Testing Framework

1. Implement `PromptABTest` class with 50/50 traffic splitting
2. Create `ab_test_results` table in Supabase
3. Build the evaluation function (compare variant A vs B after test period)
4. Wire canary deployment: approved change → 10% traffic for 4 hours → promote or rollback
5. Test: run a simulated A/B test with synthetic traffic

### Day 4-7: Skill Auto-Generation

1. Implement gap detection: track `missing_capability` events, cluster by intent
2. Build intent classification for failed requests
3. Implement skill scaffolding: gap → skill spec → LLM generates YAML + implementation
4. Build validation pipeline: schema check, tool availability, security scan, dry run
5. Test: simulate 5 repeated requests for a missing capability, verify skill proposal generated
6. Wire skill proposals to Telegram for approval

---

## Week 18: Tool Discovery + Polish

### Day 1-3: ClawHub Integration

1. Implement ClawHub API search (programmatic skill discovery)
2. Build quality scoring (downloads, rating, recency, test coverage)
3. Implement safety review for community skills (code review, permission check, sandbox test)
4. Wire community skill proposals to Telegram (always Tier 1 approval)
5. Test: search ClawHub for a known skill category, evaluate results

### Day 4-5: Git Version Control

1. Initialize Git in `~/.openclaw/` for prompts, skills, and config
2. Implement branch-per-change workflow (evolution creates branches, merges on success)
3. Test rollback via `git revert`
4. Verify full audit trail: every change has a commit with metadata

### Day 6-7: Integration Testing + Go-Live

1. Run full evolution cycle end-to-end: observe → evaluate → propose → notify → approve → act → measure
2. Test emergency freeze (`/evolution freeze`)
3. Test Telegram commands (`/evolution status`, `/evolution proposals`, `/evolution history`)
4. Deploy and monitor for 2 weeks with close supervision
5. Gradually reduce supervision as confidence builds

---

## Success Criteria

| Metric | Target | Timeline |
|--------|--------|----------|
| Metrics collection coverage | > 95% of skill executions instrumented | Week 14 |
| Weekly report delivery | Every Sunday, on time | Week 15+ |
| Regression detection | < 4 hours from regression to rollback | Week 16+ |
| Prompt improvements proposed | At least 2 per month | Month 2+ |
| Proposals accepted by user | > 60% acceptance rate | Month 2+ |
| Post-change metric improvement | > 70% of accepted changes show improvement | Month 3+ |
| Zero safety incidents | No unapproved changes applied | Always |

---

## Reference Docs

- [Evolution Architecture](../12-Self-Evolution/evolution-architecture.md)
- [Prompt Optimization](../12-Self-Evolution/prompt-optimization.md)
- [Skill Auto-Generation](../12-Self-Evolution/skill-auto-generation.md)
- [Safety Guardrails](../12-Self-Evolution/safety-guardrails.md)
- [Notification System](../12-Self-Evolution/notification-system.md)
- [Human-in-the-Loop](../02-Security/human-in-the-loop.md)

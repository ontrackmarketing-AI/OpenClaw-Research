# Skill Auto-Generation

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Evolution Architecture](evolution-architecture.md), [Skills Architecture](../05-Skills-Development/)

---

## 1. The Problem

Users repeatedly ask the agent for capabilities it does not have. Each missing capability represents a manual development task. The agent should detect these patterns and propose (or create) new skills to fill the gap.

---

## 2. Gap Detection

### 2.1 Signal Sources

| Signal | How Detected | Example |
|--------|-------------|---------|
| **Explicit request failure** | Agent responds "I don't have a skill for that" | "Can you check my Google Ads performance?" |
| **Repeated similar requests** | Same intent detected 3+ times in 14 days | User asks about invoice generation weekly |
| **Workaround patterns** | User uses multi-step manual process that could be a skill | User manually copies data between Airtable and GHL |
| **Error patterns** | Agent attempts an action but fails due to missing tool | Agent tries to call a non-existent API endpoint |
| **HITL feedback** | User rejects an action and notes "you should be able to do X" | "No, don't send it that way -- use the calendar invite" |

### 2.2 Gap Detection Query

```sql
-- Find repeated capability gaps in the last 14 days
SELECT
    intent_category,
    COUNT(*) as request_count,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen,
    array_agg(DISTINCT user_query) as example_queries
FROM evolution_metrics
WHERE success = false
    AND error_type = 'missing_capability'
    AND created_at > NOW() - INTERVAL '14 days'
GROUP BY intent_category
HAVING COUNT(*) >= 3
ORDER BY request_count DESC;
```

### 2.3 Intent Classification

When a request fails, classify the intent for gap tracking:

```python
async def classify_failed_intent(user_query: str, error: str) -> str:
    """Classify a failed request into an intent category."""
    result = await llm.generate(
        model="haiku",  # Fast and cheap for classification
        prompt=f"""Classify this failed user request into a capability category.

User request: {user_query}
Error: {error}

Categories (use existing or create new):
- calendar_management
- invoice_generation
- social_media_posting
- google_ads_reporting
- appointment_scheduling
- document_generation
- data_import_export
- notification_management
- other: [describe]

Return ONLY the category name."""
    )
    return result.strip()
```

---

## 3. Skill Scaffolding

### 3.1 Scaffolding Pipeline

When a capability gap is confirmed (3+ requests, user agrees it would be useful):

```
1. ANALYZE gap: What exactly is the user trying to do?
2. RESEARCH tools: Does ClawHub have a relevant skill? Does an API exist?
3. DESIGN skill: Define inputs, outputs, steps, tools needed
4. SCAFFOLD code: Generate skill definition YAML + implementation
5. TEST locally: Run against test cases (synthetic or user-provided)
6. PROPOSE to user: Send via Telegram with description and test results
7. DEPLOY if approved: Register skill, monitor for 48 hours
```

### 3.2 Skill Generation Prompt

```markdown
You are an OpenClaw skill developer. Generate a complete skill definition
for the following capability gap.

## Capability Needed
{gap_description}

## User Request Examples
{example_queries}

## Available Tools and APIs
{available_tools}

## OpenClaw Skill Format
Skills are defined as YAML with the following structure:
- name: kebab-case skill name
- description: what the skill does
- triggers: how it is invoked (command, event, cron)
- parameters: input parameters with types and validation
- steps: ordered list of actions
- output: what the skill returns

## Requirements
- Use existing OpenClaw tools where possible (MCP servers, API adapters)
- If an external API is needed, specify which one and the required credentials
- Include error handling for common failure modes
- Include HITL gates for any external-facing actions
- Keep it simple -- prefer fewer steps over comprehensive coverage

## Output
Generate:
1. The complete skill YAML definition
2. Any helper functions needed
3. Test cases (3-5 examples with expected behavior)
4. Required setup steps (API keys, configurations)
```

### 3.3 Example Generated Skill

```yaml
# Auto-generated skill: google-ads-report
name: google-ads-report
description: >
  Pull Google Ads performance data and generate a summary report.
  Supports campaign-level and ad-group-level reporting.
version: 0.1.0
author: openclaw-evolution
generated: true
generation_date: 2026-03-15

triggers:
  - command: "/ads-report"
  - event: monthly_report_due
  - cron: "0 9 1 * *"  # 1st of each month at 9 AM

parameters:
  account_id:
    type: string
    description: Google Ads account ID
    required: true
  date_range:
    type: string
    description: "Date range (e.g., 'last_30_days', 'last_month', 'this_quarter')"
    default: "last_30_days"
  level:
    type: string
    enum: ["campaign", "ad_group", "keyword"]
    default: "campaign"

steps:
  - name: fetch_data
    tool: google-ads-api
    action: get_performance_report
    params:
      account_id: "{{account_id}}"
      date_range: "{{date_range}}"
      metrics: ["impressions", "clicks", "cost", "conversions", "cpa"]
      level: "{{level}}"

  - name: analyze
    model: claude-haiku
    prompt: |
      Analyze this Google Ads performance data and generate a concise report.
      Highlight: top performers, underperformers, trends, and recommendations.
      Data: {{fetch_data.result}}

  - name: deliver
    tool: telegram
    action: send_message
    params:
      text: "{{analyze.result}}"
    hitl: review  # User reviews before sending

output:
  type: report
  format: markdown
```

---

## 4. Test-Before-Deploy Pipeline

Every auto-generated skill must pass validation before being proposed to the user:

### 4.1 Validation Checks

| Check | What It Verifies | Fail Action |
|-------|-----------------|-------------|
| **Schema validation** | YAML structure matches OpenClaw skill schema | Reject and re-generate |
| **Tool availability** | All referenced tools exist in the agent's tool registry | Flag missing tools |
| **Parameter validation** | All parameters have types and descriptions | Fix and re-validate |
| **Dry run** | Execute with mock data, verify no runtime errors | Report errors to user |
| **Security scan** | No shell injection, no credential exposure, no unapproved API calls | Reject immediately |
| **Cost estimate** | Estimated cost per execution within budget | Flag if > $1/execution |

### 4.2 Validation Implementation

```python
async def validate_generated_skill(skill_yaml: str) -> dict:
    """Validate a generated skill before proposing to user."""
    results = {
        "passed": True,
        "checks": [],
        "warnings": [],
        "errors": [],
    }

    skill = yaml.safe_load(skill_yaml)

    # Schema validation
    schema_valid = validate_skill_schema(skill)
    results["checks"].append({"name": "schema", "passed": schema_valid})

    # Tool availability
    for step in skill.get("steps", []):
        if "tool" in step:
            tool_exists = check_tool_exists(step["tool"])
            if not tool_exists:
                results["warnings"].append(f"Tool '{step['tool']}' not found")

    # Security scan
    security_issues = scan_for_security_issues(skill_yaml)
    if security_issues:
        results["errors"].extend(security_issues)
        results["passed"] = False

    # Cost estimate
    estimated_cost = estimate_skill_cost(skill)
    if estimated_cost > 1.0:
        results["warnings"].append(
            f"Estimated cost per execution: ${estimated_cost:.2f}"
        )

    return results
```

---

## 5. ClawHub Tool Discovery

### 5.1 Automated ClawHub Search

When a capability gap is detected, search ClawHub before building from scratch:

```python
async def search_clawhub_for_gap(gap_description: str) -> list:
    """Search ClawHub for skills matching a capability gap."""
    # Generate search keywords from gap description
    keywords = await llm.generate(
        model="haiku",
        prompt=f"Extract 3-5 search keywords for this capability: {gap_description}"
    )

    # Search ClawHub API
    results = await clawhub.search(
        query=keywords,
        sort_by="rating",
        min_rating=4.0,
        min_installs=100,
        limit=5
    )

    # Score results for relevance and quality
    scored = []
    for skill in results:
        score = await evaluate_clawhub_skill(skill, gap_description)
        scored.append({**skill, "relevance_score": score})

    return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)
```

### 5.2 Quality Evaluation Criteria

| Criterion | Weight | How Evaluated |
|-----------|--------|--------------|
| Relevance to gap | 30% | LLM judges description match |
| Community rating | 20% | ClawHub star rating (4.0+ required) |
| Install count | 15% | Higher is better (social proof) |
| Last updated | 15% | Within last 6 months preferred |
| Security audit | 20% | Check for known vulnerabilities, code review |

### 5.3 Safety Review for Community Skills

Before installing any ClawHub skill, the agent performs:

1. **Code review** -- LLM reads the skill source code and flags suspicious patterns (network calls to unknown hosts, credential access, shell commands)
2. **Permission check** -- What tools/APIs does the skill require? Are they within the agent's allowed scope?
3. **Sandboxed test** -- Run the skill in a sandboxed environment with mock data
4. **Human approval** -- Always require HITL approval for community skill installation (Tier 1 action)

---

## 6. Skill Retirement

Skills that are no longer used or consistently underperform should be retired:

| Condition | Action |
|-----------|--------|
| Skill not invoked for 60+ days | Flag for review, notify user |
| Success rate < 50% for 30+ days | Flag for review or prompt optimization |
| Superseded by better skill | Propose replacement, retire old skill if approved |
| External API deprecated | Flag immediately, attempt migration or retire |

---

## Next Steps

- [Evolution Architecture](evolution-architecture.md) -- Overall system design
- [Safety Guardrails](safety-guardrails.md) -- Constraints on skill creation
- [Prompt Optimization](prompt-optimization.md) -- Improving existing skills

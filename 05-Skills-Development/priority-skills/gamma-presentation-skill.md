# Gamma Presentation Skill

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Gamma MCP Integration](../../08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md)

---

## 1. Skill Overview

| Field | Value |
|-------|-------|
| **Skill name** | `gamma-presentation` |
| **Category** | Content Generation |
| **Triggers** | Manual (Telegram command), CRM event, scheduled cron |
| **HITL** | Required (Tier 1 -- sends content to external contacts) |
| **Dependencies** | Gamma MCP, GHL API, Memory, Telegram |
| **Estimated cost per invocation** | $0.02-0.10 (LLM for outline) + Gamma generation (included in plan) |

---

## 2. Skill Definition

```yaml
name: gamma-presentation
description: Generate professional presentations using Gamma AI
version: 1.0.0

triggers:
  - type: command
    channel: telegram
    pattern: "/deck {client_name}"
  - type: command
    channel: telegram
    pattern: "/report {client_name}"
  - type: event
    source: ghl
    event: pipeline_stage_change
    conditions:
      new_stage: ["qualified", "proposal_sent"]
  - type: cron
    schedule: "0 9 1 * *"  # Monthly reports on the 1st
    action: monthly_report_batch

inputs:
  - name: client_name
    type: string
    required: true
    description: Client or prospect name
  - name: presentation_type
    type: enum
    values: [pitch_deck, monthly_report, strategy_proposal, campaign_brief, competitor_analysis]
    required: false
    default: auto_detect
  - name: theme_preference
    type: string
    required: false
    description: Visual style preference (e.g., professional, modern, colorful)

outputs:
  - name: gamma_url
    type: url
    description: Live preview URL
  - name: export_url
    type: url
    description: PPTX or PDF download URL
  - name: generation_id
    type: string
    description: Gamma generation ID for status tracking

approval:
  required: true
  tier: 1
  channel: telegram
  message_template: |
    Generated {presentation_type} for {client_name}.
    Preview: {gamma_url}
    [Approve & Send] [Edit First] [Reject]
```

---

## 3. Execution Flow

```
1. Receive trigger (command, event, or cron)
    |
2. Resolve client context
    - Look up client in GHL contacts/opportunities
    - Pull brand config from Airtable or memory
    - Gather relevant data (pipeline, metrics, pain points)
    |
3. Determine presentation type (if not specified)
    - Use TEMPLATE_SELECTION_RULES from templates.md
    - Context clues: "qualified" stage -> pitch_deck
    - Monthly trigger -> monthly_report
    |
4. Assemble content outline
    - Use LLM (Sonnet) to generate structured outline
    - Pull data from GHL, DataForSEO, memory
    - Format as Gamma-compatible inputText
    |
5. Select Gamma theme
    - Match client brand colors/style to Gamma themes
    - Fall back to professional default
    |
6. Call Gamma MCP generate
    - Pass inputText, theme, card options, export settings
    |
7. Poll get_generation_status until complete
    - Timeout after 5 minutes
    |
8. Post preview to Telegram for HITL approval
    - Include preview link, client name, deck type
    - Inline keyboard: [Approve & Send] [Edit] [Reject]
    |
9. On approval:
    - Export PPTX/PDF if needed
    - Deliver to client via configured channel
    - Log to session history and skill_logs
```

---

## 4. Template Type Auto-Detection

```python
DETECTION_RULES = {
    "pitch_deck": {
        "triggers": ["pitch", "sell", "prospect", "new client", "proposal for new"],
        "crm_stages": ["qualified", "discovery"],
    },
    "monthly_report": {
        "triggers": ["monthly", "report", "performance", "metrics", "how are we doing"],
        "crm_stages": [],
        "cron_match": True,
    },
    "strategy_proposal": {
        "triggers": ["strategy", "plan", "proposal", "approach"],
        "crm_stages": ["proposal_sent"],
    },
    "campaign_brief": {
        "triggers": ["campaign", "brief", "launch", "creative"],
        "crm_stages": [],
    },
    "competitor_analysis": {
        "triggers": ["competitor", "competitive", "landscape", "vs"],
        "crm_stages": [],
    },
}
```

---

## 5. Error Handling

| Error | Recovery |
|-------|----------|
| Client not found in CRM | Ask user to clarify via Telegram |
| Gamma generation fails | Retry once; fall back to python-pptx template |
| Theme match fails | Use Gamma default theme |
| Data source unavailable (GHL down) | Generate with available data, note gaps |
| User rejects presentation | Log rejection reason, offer to regenerate with different parameters |
| Export fails | Provide Gamma live link as fallback |

---

## 6. Metrics

| Metric | Target | Tracking |
|--------|--------|----------|
| Generation success rate | > 95% | skill_logs table |
| User approval rate | > 80% | HITL audit log |
| Average generation time | < 3 minutes | skill_logs.duration_ms |
| Cost per presentation | < $0.15 | LLM tokens + Gamma plan amortized |
| Client delivery rate (approved -> sent) | > 90% | Session tracking |

---

## Next Steps

- [Gamma MCP Integration](../../08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md) -- detailed integration architecture
- [Presentation Templates](../../08-Capabilities-Deep-Dive/presentations/templates.md) -- python-pptx template system (alternative path)
- [Custom Skill Guide](../custom-skill-guide.md) -- how to register this skill in OpenClaw

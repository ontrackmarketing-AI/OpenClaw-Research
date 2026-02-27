# Phase 10 - Gamma Presentation Automation (Week 10-11)

> **Depends on:** Phase 4 (Core skills framework), Phase 6 (Telegram for HITL)

## Goal

Enable the agent to autonomously create presentations using Gamma's MCP tools, triggered by CRM events, monthly schedules, or user commands via Telegram.

---

## Prerequisites

- [ ] OpenClaw skill framework operational (Phase 4)
- [ ] Telegram HITL approval working (Phase 6)
- [ ] Gamma account with MCP access configured

---

## Week 10: Gamma Integration

### Day 1-2: MCP Registration + Auth

1. Register Gamma MCP server in OpenClaw's tool registry
2. Configure authentication (API key or OAuth)
3. Test basic generation: `generate` → `get_generation_status` → verify output
4. Test theme listing: `get_themes` → verify theme IDs usable

### Day 3-4: Skill Definition

1. Create `gamma-presentation-skill.yaml` with triggers (command, event, cron)
2. Implement template type auto-detection (user context → presentation category)
3. Build HITL preview flow: generate → post Gamma URL to Telegram → user approves → deliver
4. Test error handling (generation timeout, API failure, invalid input)

### Day 5: Trigger Integration

1. Wire CRM stage change trigger (e.g., lead moves to "proposal_sent" → generate pitch deck)
2. Wire monthly cron trigger (e.g., 1st of month → generate monthly report)
3. Wire Telegram command trigger (`/presentation [topic]`)
4. Test all three trigger paths end-to-end

---

## Week 11: Polish + Export

### Day 1-2: Theme Selection + Quality

1. Implement theme selection logic (match client branding keywords to Gamma themes)
2. Test with 5 different presentation types, evaluate quality
3. Tune input text generation for each template category

### Day 3: Export + Delivery

1. Implement PPTX/PDF export for downloadable deliverables
2. Build delivery channels: Telegram file send, email attachment, Google Drive upload
3. Test export quality (fonts, images, formatting preserved)

### Day 4-5: Testing + Go-Live

1. Generate 10 test presentations across all template types
2. User review of output quality
3. Deploy skill and monitor first week

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Generation success rate | > 95% |
| User approval rate (HITL) | > 80% |
| Average generation time | < 2 minutes |
| Cost per presentation | < $2 |

---

## Reference Docs

- [Gamma MCP Integration](../08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md)
- [Gamma Presentation Skill](../05-Skills-Development/priority-skills/gamma-presentation-skill.md)
- [Presentation Templates](../08-Capabilities-Deep-Dive/presentations/templates.md)

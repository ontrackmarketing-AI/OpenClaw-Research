# Phase 9 - Proactive Check-ins (Week 9-10)

> **Depends on:** Phase 6 (Channels -- Telegram bot operational), Phase 3 (Memory system active)

## Goal

Deploy an agent that proactively reaches out via Telegram 3-5 times daily with context-aware messages, creating an ongoing conversational relationship rather than only responding to commands.

---

## Prerequisites

- [ ] Telegram bot running and responsive (Phase 6)
- [ ] Memory system operational with daily logs (Phase 3)
- [ ] HITL approval system functional (Phase 2)

---

## Week 9: Check-in Engine + Context Sources

### Day 1-2: LaunchAgent Scheduling

1. Create the check-in LaunchAgent plist with 5 daily triggers (8:30, 11:00, 13:30, 16:00, 18:30)
2. Configure quiet hours integration (22:00-08:00)
3. Test basic trigger → Telegram message flow
4. Verify LaunchAgent survives Mac Mini reboots

### Day 3-4: Context Assembly Pipeline

1. Build the parallel async context fetcher with 2-second timeout
2. Implement context sources:
   - Memory system (MEMORY.md + recent daily logs)
   - Pending HITL approvals
   - Recent session activity
3. Test graceful degradation (context source timeout → continue without it)

### Day 5: Response Tracking

1. Create response tracking in Supabase (check-in sent, responded, ignored, response latency)
2. Implement basic analytics: which check-in times get responses, which don't

---

## Week 10: Conversational Design + Calendar Integration

### Day 1-2: Template System

1. Build template pools per time slot (morning aspirational, midday tactical, afternoon problem-solving, evening reflective)
2. Implement anti-repetition system (track last 10 templates used, never repeat within 3 days)
3. Add LLM personalization pass (Haiku rewrites template with current context)
4. Test with 3 days of simulated check-ins

### Day 3-4: Calendar Integration (Optional)

1. Set up Google Calendar API access (OAuth2 or service account)
2. Implement calendar-aware scheduling (skip check-ins during meetings)
3. Add calendar context to check-in messages ("You have a meeting with Acme in 30 minutes")

### Day 5: Testing + Go-Live

1. Run full end-to-end test: LaunchAgent → context assembly → LLM personalization → Telegram delivery
2. Test quiet hours enforcement
3. Test response tracking
4. Deploy and monitor first week of live check-ins

---

## Success Criteria

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Check-ins delivered | 3-5 per day, every day | Supabase check-in log |
| Response rate | > 40% of check-ins get a reply | Response tracking |
| No spam complaints | User does not disable or mute | Self-reported |
| Context relevance | > 70% of check-ins reference relevant context | Manual review of first 20 |
| System reliability | < 2 missed check-ins per week | LaunchAgent + health check logs |

---

## Reference Docs

- [Check-in Engine](../08-Capabilities-Deep-Dive/proactive-checkins/checkin-engine.md)
- [Conversational Design](../08-Capabilities-Deep-Dive/proactive-checkins/conversational-design.md)
- [Context Sources](../08-Capabilities-Deep-Dive/proactive-checkins/context-sources.md)
- [Telegram Bot](../07-Channel-Setup/telegram-bot.md)

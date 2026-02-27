# Conversational Design for Proactive Check-ins

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Check-in Engine](checkin-engine.md), [Context Sources](context-sources.md)

---

## 1. Design Principles

1. **Never robotic.** Check-ins must feel like a capable assistant, not a notification bot. Vary language, structure, and tone.
2. **Context-first.** Every check-in references something specific -- a project, a deadline, a recent conversation. Generic "how's it going?" messages get ignored.
3. **Actionable.** Each check-in should invite a response. Ask a question, present a choice, or surface something that needs a decision.
4. **Concise.** Telegram messages should be 2-4 sentences. The user is on mobile. Respect their time.
5. **Varied.** Never send the same prompt twice in a week. Use a rotation pool with dynamic elements.

---

## 2. Prompt Templates by Time Slot

### 2.1 Morning (8:30 AM) -- Aspirational

**Goal:** Help the user set priorities and start the day with intention.

**Template pool (LLM selects and personalizes based on context):**

```
MORNING_TEMPLATES = [
    # Priority-focused
    "Morning. You've got {pending_tasks_count} tasks open. The biggest one looks like {top_task}. Want to tackle that first, or is there something more urgent?",

    # Calendar-aware
    "You have {meeting_count} meetings today, first one at {first_meeting_time}. Before that, any priorities you want to knock out?",

    # Pipeline-aware
    "{pipeline_stage_count} leads moved to {stage_name} yesterday. {hot_lead_name} looks promising -- want me to draft a follow-up?",

    # Reflection
    "Quick question before the day starts: what's the one thing that would make today a win?",

    # CRM-aware
    "Heads up -- {overdue_followup_count} follow-ups are overdue in GHL. Want me to draft those, or should we reprioritize?",

    # iMessage-aware (if Capability 1 is active)
    "Noticed {contact_name} messaged you last night about {topic_hint}. Want me to pull context on that before you reply?",
]
```

### 2.2 Late Morning (11:00 AM) -- Tactical

**Goal:** Check progress on morning priorities and surface blockers.

```
LATE_MORNING_TEMPLATES = [
    # Progress check
    "How's {morning_priority} going? Need me to look anything up or draft something?",

    # Proactive intel
    "While you're working, I found something relevant: {proactive_insight}. Useful or noise?",

    # Quick decision
    "Quick one -- {pending_approval_summary}. Approve, reject, or want more context?",

    # Resource offer
    "The {project_name} deadline is {days_until_deadline} days out. Want me to check what's still open on it?",
]
```

### 2.3 After Lunch (1:30 PM) -- Energizing

**Goal:** Re-engage after a natural break. Keep it light but productive.

```
AFTER_LUNCH_TEMPLATES = [
    # Momentum builder
    "Back at it. You knocked out {completed_today_count} tasks this morning. What's next on the list?",

    # Opportunity surface
    "New lead just came in: {new_lead_summary}. Score: {lead_score}/100. Worth pursuing?",

    # Content prompt
    "It's been {days_since_last_post} days since your last LinkedIn post. I've got a draft ready on {topic} if you want to review it.",

    # Low-effort ask
    "Anything from this morning's meetings I should capture or follow up on?",
]
```

### 2.4 Mid-Afternoon (4:00 PM) -- Problem-Solving

**Goal:** Surface blockers, check on deliverables, clear the path for end-of-day.

```
AFTERNOON_TEMPLATES = [
    # Blocker detection
    "Anything stuck or waiting on someone else right now? I can send a nudge or draft a follow-up.",

    # Deliverable check
    "The {deliverable_name} for {client_name} is due {due_description}. Status?",

    # Cost awareness
    "API spend today: ${today_api_spend}. We're {budget_status} for the month. Anything I should throttle?",

    # Competitive intel
    "Competitor update: {competitor_name} {competitor_change}. Want me to dig deeper?",
]
```

### 2.5 Evening (6:30 PM) -- Reflective

**Goal:** Capture the day's outcomes, decisions, and priorities for tomorrow.

```
EVENING_TEMPLATES = [
    # Day capture
    "Wrapping up. Anything important from today I should remember for tomorrow?",

    # Tomorrow planning
    "Tomorrow looks {tomorrow_density} based on your calendar. Top priority for the morning?",

    # Win recognition
    "Nice day -- {wins_summary}. Anything else to log before I update your daily summary?",

    # Open loop closure
    "You mentioned {open_item} earlier. Did that get resolved, or should I carry it to tomorrow?",

    # Weekly planning (Friday only)
    "End of the week. Want a quick summary of what we accomplished? I can draft your weekly review.",
]
```

---

## 3. Personalization via LLM

Templates are not sent verbatim. They are prompts for the LLM to generate a natural message:

```python
async def generate_checkin_message(slot: str, context: dict) -> str:
    template = select_template(slot, context)

    prompt = f"""Generate a brief, natural Telegram message for a proactive check-in.

Time slot: {slot}
Template guidance: {template}

Context:
- User's recent activity: {context['recent_activity']}
- Pending tasks: {context['pending_tasks']}
- Calendar today: {context['calendar_summary']}
- Recent conversations: {context['recent_conversations']}
- Pipeline status: {context['pipeline_summary']}

Rules:
- 2-4 sentences maximum
- Ask one clear question or present one decision
- Reference something specific from the context
- Conversational tone, not corporate
- Do not repeat the same opening as the last 3 check-ins
- Include an inline keyboard if a yes/no decision is appropriate

Last 3 check-in openings (avoid these): {context['recent_openings']}
"""

    message = await llm.generate(prompt, model="haiku")
    return message
```

**Model choice:** Use Haiku for check-in generation. It is fast, cheap, and the output quality is sufficient for short conversational messages. Cost: < $0.01/day for 5 check-ins.

---

## 4. Inline Keyboard Patterns

Some check-ins benefit from quick-tap responses instead of typing:

```python
# Decision check-in
{
    "text": "3 follow-ups overdue. Want me to draft and send them?",
    "reply_markup": {
        "inline_keyboard": [
            [
                {"text": "Draft for review", "callback_data": "checkin:draft_followups"},
                {"text": "Skip today", "callback_data": "checkin:skip_followups"}
            ],
            [
                {"text": "Show me the list", "callback_data": "checkin:list_followups"}
            ]
        ]
    }
}

# Priority check-in
{
    "text": "Top priority today?",
    "reply_markup": {
        "inline_keyboard": [
            [{"text": "Acme proposal", "callback_data": "checkin:priority:acme"}],
            [{"text": "Lead pipeline", "callback_data": "checkin:priority:pipeline"}],
            [{"text": "Something else", "callback_data": "checkin:priority:custom"}]
        ]
    }
}
```

---

## 5. Anti-Repetition System

To prevent the user from feeling like they are talking to a script:

1. **Template rotation:** Each slot has 4-6 templates. Track which were used in the last 7 days. Never repeat within 5 days.
2. **Opening variation:** Track the first 5 words of each check-in. Ensure no two consecutive check-ins start the same way.
3. **Context novelty:** Prefer templates that reference context the user has not seen in a check-in recently.
4. **Day-of-week flavor:** Monday mornings are more "planning" flavored. Friday evenings are more "review" flavored.
5. **Seasonal awareness:** Reference relevant dates (end of quarter, holidays) when applicable.

---

## 6. Handling Responses

### 6.1 User Responds with Text

Process the response as a normal Telegram message to the agent. The agent has the check-in context and can continue the conversation naturally.

### 6.2 User Taps an Inline Keyboard Button

Route the callback to the appropriate handler:

| Callback Pattern | Action |
|-----------------|--------|
| `checkin:draft_*` | Agent drafts content and sends for review |
| `checkin:skip_*` | Log the skip, carry to next check-in |
| `checkin:priority:*` | Update today's priorities in memory |
| `checkin:approve:*` | Execute the proposed action |
| `checkin:list_*` | Send detailed list as follow-up message |

### 6.3 User Ignores the Check-in

No follow-up for 2 hours. Mark as ignored in tracking. The next scheduled check-in proceeds normally.

### 6.4 User Says "Not now" or "Busy"

Acknowledge and suppress the next check-in (skip one slot). Resume on the following slot.

### 6.5 User Says "Stop" or "Too many"

Immediately reduce to minimum frequency (2/day) and ask the user to confirm their preferred schedule.

---

## 7. Conversation Continuity

When the user responds to a check-in, the agent should maintain context through the conversation:

```
Agent (6:30 PM): Wrapping up. You mentioned the Acme proposal needed revisions -- did that get done?
User: No, still working on pricing section
Agent: Got it. Want me to pull competitor pricing data for that industry? I can have it ready by morning.
User: Yeah that would help
Agent: On it. I'll have a comparison table in your morning check-in. Anything else for tonight?
```

The agent logs this exchange and the morning check-in the next day references the promised competitor data.

---

## Next Steps

- [Check-in Engine](checkin-engine.md) -- scheduling and execution mechanics
- [Context Sources](context-sources.md) -- where check-in data comes from

# Proactive Check-in Engine

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Telegram Bot](../../07-Channel-Setup/telegram-bot.md), [Memory Architecture](../../04-Memory-and-RAG/memory-architecture.md)

---

## 1. What This Is

The check-in engine sends the user 3-5 context-aware messages per day via Telegram. Rather than waiting for the user to initiate conversation, the agent proactively reaches out with relevant questions, summaries, and prompts based on time of day, recent activity, and pending work.

**Goal:** Keep the user engaged with their agent, surface important information before it is asked for, and capture context (decisions, priorities, blockers) that improves the agent's effectiveness throughout the day.

---

## 2. Timing Architecture

### 2.1 Trigger Mechanism

Two options for scheduling check-ins:

**Option A: macOS LaunchAgent (Recommended for simplicity)**

```xml
<!-- ~/Library/LaunchAgents/com.openclaw.checkin.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.checkin</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/openclaw</string>
        <string>run</string>
        <string>proactive-checkin</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <!-- Morning check-in: 8:30 AM -->
        <dict>
            <key>Hour</key><integer>8</integer>
            <key>Minute</key><integer>30</integer>
        </dict>
        <!-- Late morning: 11:00 AM -->
        <dict>
            <key>Hour</key><integer>11</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- After lunch: 1:30 PM -->
        <dict>
            <key>Hour</key><integer>13</integer>
            <key>Minute</key><integer>30</integer>
        </dict>
        <!-- Mid-afternoon: 4:00 PM -->
        <dict>
            <key>Hour</key><integer>16</integer>
            <key>Minute</key><integer>0</integer>
        </dict>
        <!-- Evening wrap: 6:30 PM -->
        <dict>
            <key>Hour</key><integer>18</integer>
            <key>Minute</key><integer>30</integer>
        </dict>
    </array>
</dict>
</plist>
```

```bash
# Install the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.openclaw.checkin.plist

# Verify it is loaded
launchctl list | grep openclaw.checkin
```

**Option B: OpenClaw Agent YAML Cron Trigger**

```yaml
# In the agent definition YAML
triggers:
  - type: cron
    schedule: "30 8,11 * * *"    # 8:30 AM, 11:00 AM
    action: proactive_checkin
    params:
      slot: morning
  - type: cron
    schedule: "30 13 * * *"      # 1:30 PM
    action: proactive_checkin
    params:
      slot: midday
  - type: cron
    schedule: "0 16 * * *"       # 4:00 PM
    action: proactive_checkin
    params:
      slot: afternoon
  - type: cron
    schedule: "30 18 * * *"      # 6:30 PM
    action: proactive_checkin
    params:
      slot: evening
```

**Recommendation:** Use Option A (LaunchAgent) for reliability -- it runs independent of the OpenClaw process, so check-ins still trigger even if the agent restarts.

### 2.2 Default Schedule

| Slot | Time | Purpose | Character |
|------|------|---------|-----------|
| Morning | 8:30 AM | Set the day's agenda | Aspirational |
| Late Morning | 11:00 AM | Check progress on morning priorities | Tactical |
| After Lunch | 1:30 PM | Re-engage after break | Energizing |
| Mid-Afternoon | 4:00 PM | Status check, surface blockers | Problem-solving |
| Evening | 6:30 PM | Capture the day, plan tomorrow | Reflective |

### 2.3 Quiet Hours

Respect the existing `quiet_hours` configuration from `telegram-bot.md`:

```yaml
quiet_hours:
  start: "22:00"
  end: "08:00"
  timezone: "America/New_York"
```

No check-ins fire between 10 PM and 8 AM. The morning check-in at 8:30 AM is the first contact after quiet hours end.

### 2.4 Calendar-Aware Scheduling

Before sending a check-in, the engine checks if the user is in a meeting:

```python
async def should_send_checkin(slot: str) -> bool:
    # Check Google Calendar for current events
    current_events = await google_calendar.get_events(
        time_min=now(),
        time_max=now() + timedelta(minutes=5)
    )

    if current_events:
        # User is in a meeting, defer by 30 minutes
        schedule_deferred_checkin(slot, delay_minutes=30)
        return False

    # Check if user responded to last check-in (avoid spamming)
    last_checkin = await memory.get_last_checkin()
    if last_checkin and not last_checkin.user_responded and last_checkin.age_minutes < 120:
        # Previous check-in was ignored and is less than 2 hours old
        return False

    return True
```

**Calendar integration options:**
- **Google Calendar API** via OAuth 2.0 -- best if user uses Google Calendar
- **Apple Calendar via CalDAV** -- works if user prefers Apple Calendar on the iMac
- **Both** -- query whichever has events, deduplicate

See [Context Sources](context-sources.md) for calendar API setup details.

---

## 3. Adaptive Timing

### 3.1 Response Pattern Learning

Track which check-in slots get responses and which are ignored:

```python
checkin_history = {
    "morning_0830": {"sent": 47, "responded": 38, "avg_response_min": 4.2},
    "late_morning_1100": {"sent": 47, "responded": 25, "avg_response_min": 12.1},
    "after_lunch_1330": {"sent": 45, "responded": 40, "avg_response_min": 2.8},
    "afternoon_1600": {"sent": 47, "responded": 30, "avg_response_min": 8.5},
    "evening_1830": {"sent": 42, "responded": 35, "avg_response_min": 5.1},
}
```

**Adaptation rules:**
- If a slot has < 30% response rate over 14 days, drop it from the schedule.
- If responses consistently come 15+ minutes after a slot, shift it later.
- If the user manually messages the agent at a consistent time, consider adding a new slot.
- Never exceed 5 check-ins per day. Never drop below 2.

### 3.2 Day-of-Week Patterns

Weekday check-ins are different from weekend check-ins:

| Day Type | Check-ins | Notes |
|----------|-----------|-------|
| Weekday | 3-5 | Full schedule |
| Saturday | 1-2 | Morning + optional evening |
| Sunday | 0-1 | Optional evening planning for the week |

---

## 4. Check-in Execution Flow

```
Cron / LaunchAgent fires
    |
    v
Load context sources (see context-sources.md)
    |
    v
Check quiet hours / calendar -> skip if blocked
    |
    v
Select conversational prompt (see conversational-design.md)
    |
    v
Generate personalized message via LLM
    |
    v
Send via Telegram Bot API
    |
    v
Log the check-in (timestamp, slot, message, context used)
    |
    v
Listen for response (up to 2 hours)
    |
    v
If response received:
    - Process and act on user's reply
    - Update memory with any new context
    - Update response tracking metrics
If no response:
    - Mark as ignored
    - Update adaptive timing model
```

---

## 5. Configuration

```yaml
proactive_checkins:
  enabled: true
  channel: telegram
  max_per_day: 5
  min_per_day: 2

  schedule:
    morning:
      time: "08:30"
      enabled: true
    late_morning:
      time: "11:00"
      enabled: true
    after_lunch:
      time: "13:30"
      enabled: true
    afternoon:
      time: "16:00"
      enabled: true
    evening:
      time: "18:30"
      enabled: true

  quiet_hours:
    start: "22:00"
    end: "08:00"
    timezone: "America/New_York"

  weekend:
    enabled: true
    max_per_day: 2
    slots: ["morning", "evening"]

  calendar_integration:
    enabled: true
    provider: google  # or apple, or both
    defer_minutes: 30  # delay if user is in a meeting

  adaptive:
    enabled: true
    learning_window_days: 14
    drop_threshold: 0.30  # drop slot if < 30% response rate
    min_data_points: 10   # need 10+ data points before adapting

  response_timeout_minutes: 120
```

---

## 6. HITL Considerations

Check-ins are outbound Telegram messages to the user. Per the [HITL policy](../../02-Security/human-in-the-loop.md):

- Check-ins are **informational messages to the user** (not external contacts), so they fall into Tier 2 (auto-approve) once the feature is configured and enabled.
- The user can disable check-ins entirely or per-slot via configuration.
- Check-ins never send messages to anyone other than the configured user Telegram ID.

---

## 7. Metrics

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Overall response rate | > 50% | Reduce frequency or improve prompts |
| Average response time | < 10 min | Prompts are engaging and timely |
| User-initiated "stop" rate | 0% | If user says "stop" or "too many", reduce immediately |
| Context accuracy | > 80% | Check-in references correct projects/tasks |

---

## Next Steps

- [Conversational Design](conversational-design.md) -- prompt templates for each time slot
- [Context Sources](context-sources.md) -- data sources that inform check-in content
- [Telegram Bot](../../07-Channel-Setup/telegram-bot.md) -- underlying delivery channel

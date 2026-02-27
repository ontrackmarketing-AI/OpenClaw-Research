# Self-Evolution Notification System

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Evolution Architecture](evolution-architecture.md), [Telegram Bot](../07-Channel-Setup/telegram-bot.md)

---

## 1. Purpose

The notification system keeps the user informed about all self-evolution activity. Every proposed change, auto-approved action, regression, and rollback is communicated via Telegram with appropriate urgency.

---

## 2. Notification Categories

| Category | Icon | When | User Action Required |
|----------|------|------|---------------------|
| **Informational** | `ℹ️` | Routine activity (metrics collected, prompt tested, background task complete) | None -- awareness only |
| **Advisory** | `📋` | Improvement proposed, weekly report ready, new skill candidate found | Review when convenient |
| **Approval** | `🔑` | Change requires explicit approval before deployment | Approve or reject |
| **Critical** | `🚨` | Regression detected, rollback triggered, error spike, budget threshold hit | Immediate attention |

---

## 3. Message Templates

### 3.1 Informational

```
ℹ️ Evolution Update

Weekly metrics collected for 12 skills.
• 11/12 meeting targets
• 1 flagged for review (lead-enrichment: 84% success, target 90%)

No action needed.
```

### 3.2 Advisory -- Improvement Proposed

```
📋 Improvement Proposed

Skill: lead-enrichment
Issue: Success rate 84% (target 90%)
Proposal: Rewrite prompt to add explicit output format instructions

Expected impact: +5-8% success rate
Risk: Low (prompt wording change only)
Confidence: 7/10

[View Diff] [Approve] [Reject] [Discuss]
```

### 3.3 Advisory -- Weekly Evolution Report

```
📋 Weekly Evolution Report (Feb 17-23)

Metrics Summary:
• Overall success rate: 91% (↑2%)
• Total cost: $14.20 (↓8%)
• HITL approval rate: 94%
• Errors: 23 (↓15%)

Changes This Week:
• ✅ Prompt optimized: crm-management (+6% success)
• ⏳ Testing: lead-enrichment prompt rewrite (day 1 of 2)
• ❌ Rolled back: presentation-gen model switch (latency regression)

Proposals Pending:
• 1 prompt rewrite (lead-enrichment)
• 1 new skill candidate (google-ads-report)

[View Full Report]
```

### 3.4 Approval -- Skill Installation

```
🔑 Approval Required

Action: Install community skill from ClawHub
Skill: clawhub/pdf-invoice-parser (v2.1.0)
Author: @data-tools-collective
Rating: 4.6/5 (230 installs)
Last updated: 2026-02-10

Why: Detected 7 requests for PDF invoice parsing in last 14 days.

Security Review:
• ✅ No network calls to external hosts
• ✅ No credential access
• ✅ Sandboxed test passed (3/3 test cases)
• ⚠️ Requires file system read access (expected for PDF parsing)

[Approve] [Reject] [View Code]
```

### 3.5 Critical -- Regression Rollback

```
🚨 Auto-Rollback Triggered

Skill: presentation-gen
Change: Switched model from claude-sonnet to ollama/qwen3:14b
Applied: Feb 22, 14:00
Rolled back: Feb 22, 18:00

Reason: Latency increased 180% (2.1s → 5.9s)
Metrics during canary:
• Success rate: 88% (baseline 91%) ⚠️
• Latency: 5,900ms (baseline 2,100ms) ❌
• Cost: $0.002/op (baseline $0.08/op) ✅

The change has been reverted. Agent is using the previous configuration.
Next retry eligible: Feb 25 (72h cooldown).
```

### 3.6 Critical -- Budget Alert

```
🚨 Daily Budget Alert

Current daily spend: $42.50 / $50.00 (85%)
Projected end-of-day: $58.00 (⚠️ over budget)

Top cost drivers today:
• lead-enrichment: $18.40 (43%)
• content-generation: $12.80 (30%)
• crm-management: $6.20 (15%)

Expensive operations have been paused.
Resume manually: /evolution resume-spending

[View Cost Dashboard]
```

---

## 4. Telegram Inline Keyboards

Approval messages include inline keyboards for quick responses:

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_approval_keyboard(proposal_id: str) -> InlineKeyboardMarkup:
    """Build inline keyboard for evolution proposal approval."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"evo_approve:{proposal_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"evo_reject:{proposal_id}"),
        ],
        [
            InlineKeyboardButton("📄 View Diff", callback_data=f"evo_diff:{proposal_id}"),
            InlineKeyboardButton("💬 Discuss", callback_data=f"evo_discuss:{proposal_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
```

### Callback Handling

```python
async def handle_evolution_callback(update, context):
    """Handle inline keyboard callbacks for evolution proposals."""
    query = update.callback_query
    action, proposal_id = query.data.split(":")

    if action == "evo_approve":
        await approve_proposal(proposal_id)
        await query.answer("Approved. Change will be deployed via canary.")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("✅ Proposal approved. Deploying to canary (10% traffic).")

    elif action == "evo_reject":
        await reject_proposal(proposal_id)
        await query.answer("Rejected.")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("❌ Proposal rejected. No changes applied.")

    elif action == "evo_diff":
        diff = await get_proposal_diff(proposal_id)
        await query.message.reply_text(f"```\n{diff}\n```", parse_mode="Markdown")

    elif action == "evo_discuss":
        await query.answer("Send your feedback as a reply to this message.")
```

---

## 5. Telegram Commands

| Command | Description |
|---------|-------------|
| `/evolution status` | Show current evolution state (active/frozen, pending proposals, active canaries) |
| `/evolution report` | Generate and send the weekly evolution report |
| `/evolution proposals` | List all pending proposals awaiting approval |
| `/evolution history` | Show recent evolution changes (last 10) |
| `/evolution freeze` | Freeze all evolution activity |
| `/evolution unfreeze` | Resume evolution activity |
| `/evolution resume-spending` | Resume paused expensive operations after budget alert |
| `/evolution rollback [id]` | Manually rollback a specific change |

---

## 6. Notification Frequency Limits

To avoid notification fatigue:

```yaml
notification_limits:
  informational:
    max_per_day: 3          # Batch informational messages
    quiet_hours: true        # Respect quiet hours (22:00-08:00)
  advisory:
    max_per_day: 5
    quiet_hours: true
  approval:
    max_per_day: 10         # Approval requests bypass batching
    quiet_hours: false       # Time-sensitive -- send during quiet hours
    reminder_after: 4h       # Remind if not responded in 4 hours
  critical:
    max_per_day: unlimited   # Always send critical alerts
    quiet_hours: false       # Always send immediately
    sound: true              # Enable notification sound
```

---

## 7. Notification Delivery Pipeline

```python
class EvolutionNotifier:
    """Manages evolution notifications via Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot = telegram.Bot(token=bot_token)
        self.chat_id = chat_id
        self.daily_counts = defaultdict(int)

    async def notify(self, category: str, message: str,
                     keyboard: InlineKeyboardMarkup = None,
                     proposal_id: str = None):
        """Send a categorized evolution notification."""

        # Check rate limits
        if not self._within_limits(category):
            await self._queue_for_batch(category, message)
            return

        # Check quiet hours (except critical and approval)
        if category in ("informational", "advisory") and self._is_quiet_hours():
            await self._queue_for_batch(category, message)
            return

        # Send
        await self.bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

        self.daily_counts[category] += 1

        # Log notification
        await supabase.table("evolution_audit_log").insert({
            "proposal_id": proposal_id,
            "action": f"notification_{category}",
            "actor": "system",
            "details": {"message_preview": message[:200]},
        })
```

---

## Next Steps

- [Evolution Architecture](evolution-architecture.md) -- Overall system design
- [Telegram Bot](../07-Channel-Setup/telegram-bot.md) -- Bot configuration
- [Safety Guardrails](safety-guardrails.md) -- What triggers critical alerts

# Human-in-the-Loop (HITL) for OpenClaw

> **HITL is your single most important safety mechanism.** Docker limits the blast radius of a compromised agent. Credential management limits what keys an attacker can steal. But HITL is the only control that prevents the agent from taking a catastrophic action in the first place. Every other control is reactive. HITL is proactive.

---

## What HITL Means in OpenClaw Context

Human-in-the-Loop means that certain agent actions require explicit human approval before they execute. The agent proposes an action, pauses, and waits for you to say "yes" or "no."

**Without HITL:**
```
Agent thinks: "I should send a follow-up email to all 2,000 leads in the database"
Agent does:   Sends 2,000 emails immediately
Result:       Half the emails contain hallucinated claims. Mass unsubscribes.
              Possible CAN-SPAM violations. Reputation damage.
```

**With HITL:**
```
Agent thinks: "I should send a follow-up email to all 2,000 leads in the database"
Agent asks:   "I'd like to send this follow-up email to 2,000 leads. Here's the draft.
               Approve? [Yes] [No] [Edit]"
You review:   See the hallucinated claim. Click [No]. Fix the template. Re-approve
              for a test segment of 10.
Result:       No damage. Caught before it happened.
```

---

## Action Classification: What Needs Approval?

### Tier 1: ALWAYS Require Approval (RED)

These actions are irreversible, external-facing, or financially impactful. No exceptions, no auto-approve, no "after the first 10 times."

| Action | Why Always Approve | Example |
|---|---|---|
| **Send external messages** (email, SMS, GHL messages) | Reputation damage; legal liability; cannot unsend | Agent drafts an email to a prospect |
| **Delete data** (database rows, files, records) | Irreversible data loss | Agent wants to "clean up" old leads |
| **Financial transactions** (API calls with cost > $5) | Direct financial impact | Agent runs a batch Clay enrichment on 500 leads |
| **Account/settings changes** (GHL pipelines, automation configs) | Can break existing workflows | Agent modifies a GHL automation |
| **Publish content** (social media, website, blog) | Public-facing; reputation risk | Agent posts to social media on your behalf |
| **Create new integrations** (connect new services, OAuth grants) | Expands attack surface | Agent tries to connect a new API |
| **Export data** (bulk downloads, CSV exports) | Data exfiltration risk | Agent exports full contact list |
| **Modify agent configuration** (change skills, update prompts) | Could disable safety controls | Agent modifies its own system prompt |

### Tier 2: Auto-Approve (GREEN)

These actions are safe to automate because they are internal, non-destructive, and easily reversible.

| Action | Why Auto-Approve | Example |
|---|---|---|
| **Read operations** (fetch data, query databases, browse web) | No side effects; information gathering only | Agent checks lead count in Supabase |
| **Internal data processing** (enrich, classify, score leads) | Stays within your systems; no external impact | Agent runs lead scoring on existing data |
| **Write to agent memory/workspace** | Agent's own working space; easily wiped | Agent saves research notes |
| **Generate drafts** (without sending) | Draft sits in queue until human reviews | Agent writes email templates for review |
| **Log and report** (create summaries, status updates) | Informational only | Agent generates daily activity report |
| **Internal calculations** (lead scoring, data analysis) | No external side effects | Agent calculates conversion rates |

### Tier 3: Conditional Approval (YELLOW)

These actions start as requiring approval but can be relaxed over time as you build trust.

| Action | Initial Policy | Relaxed Policy (after 30+ days) |
|---|---|---|
| **GHL contact creation** | Approve first 20 | Auto-approve if data matches expected schema |
| **Internal Slack/notification messages** | Approve first 10 | Auto-approve if message is under 500 chars |
| **Clay single-record enrichment** | Approve first 5 | Auto-approve if cost < $0.50 per record |
| **Airtable record updates** | Approve first 30 | Auto-approve for specific tables only |
| **File creation** (non-deletion) in workspace | Approve first 10 | Auto-approve in designated workspace directory |

**Rule for relaxation:** Only move an action from Yellow to Green after:
1. You have reviewed at least 20 approved instances manually
2. Zero instances were wrong or concerning
3. The action has clear, predictable parameters
4. The action is easily reversible if something goes wrong

---

## Configuring HITL in OpenClaw

### Where to Configure

OpenClaw's HITL configuration will depend on its specific implementation. Look for these settings (check OpenClaw documentation for exact paths):

```yaml
# Expected configuration location (verify in OpenClaw docs)
# config/approval-policy.yaml or similar

approval:
  default: require  # Default to requiring approval for unclassified actions

  rules:
    # Tier 1: Always require
    - action: "send_email"
      policy: always_require
    - action: "send_sms"
      policy: always_require
    - action: "delete_*"
      policy: always_require
    - action: "ghl.message.*"
      policy: always_require
    - action: "export_*"
      policy: always_require
    - action: "modify_config"
      policy: always_require

    # Tier 2: Auto-approve
    - action: "read_*"
      policy: auto_approve
    - action: "query_*"
      policy: auto_approve
    - action: "memory.write"
      policy: auto_approve
    - action: "generate_draft"
      policy: auto_approve

    # Tier 3: Conditional
    - action: "ghl.contact.create"
      policy: approve_first_n
      count: 20
    - action: "clay.enrich_single"
      policy: approve_if_cost_above
      threshold: 0.50
```

### Alternative: Skill-Level Configuration

If OpenClaw does not have a centralized approval policy, configure HITL at the skill level:

```javascript
// In each skill definition
module.exports = {
  name: "send-ghl-message",
  description: "Send a message via GoHighLevel",
  requiresApproval: true,  // HITL flag
  approvalMessage: (params) =>
    `Send "${params.message}" to ${params.contactName} (${params.contactId})?`,
  execute: async (params) => {
    // Only runs after human approval
  }
};
```

---

## Approval Mechanisms

### 1. Web UI Confirmation (Primary)

The OpenClaw web UI should display pending approvals prominently.

**What a good approval UI shows:**
- What action the agent wants to take
- Full parameters (who is the message going to, what does it say, what data is being modified)
- Why the agent wants to take this action (its reasoning)
- Cost estimate if applicable
- [Approve] [Reject] [Edit & Approve] buttons
- Timestamp and timeout indicator

### 2. Mobile Notification (For On-the-Go Approval)

Access the web UI from your phone via Tailscale (see `tailscale-vpn.md`):
- Receive a push notification when approval is needed
- Open the OpenClaw web UI on your phone
- Review and approve/reject

**Implementation options:**
- Tailscale + mobile browser (simplest)
- Slack integration for approval notifications (see below)
- Pushover or Ntfy.sh for push notifications

### 3. Slack Approval Flow (Recommended for Workflow Integration)

If you use Slack, route approvals through a dedicated Slack channel:

```
Agent wants to send email
    |
    v
OpenClaw posts to #agent-approvals Slack channel:
    "Agent requests approval:
     Action: Send email
     To: john@company.com
     Subject: Follow-up on our conversation
     Body: [preview]
     Cost: $0.00
     React with :white_check_mark: to approve
     React with :x: to reject"
    |
    v
You react with the appropriate emoji
    |
    v
Agent proceeds (or does not)
```

**Setting this up requires:** n8n or a custom webhook integration between OpenClaw and Slack.

---

## Timeout Behavior

**Critical question: What happens if you do not respond to an approval request?**

### Recommended Configuration

| Scenario | Timeout | Action on Timeout |
|---|---|---|
| Tier 1 actions (send message, delete, financial) | 24 hours | REJECT and notify human |
| Tier 3 actions (conditional) | 4 hours | REJECT and notify human |
| Batch plans (multiple actions) | 24 hours | REJECT entire batch |

**The default on timeout must ALWAYS be REJECT, not approve.** An unanswered approval should never result in the action being taken. The agent should queue the action and remind you, not proceed.

```yaml
timeout:
  default: 24h
  action_on_timeout: reject
  reminder_interval: 4h  # Remind every 4 hours that an action is pending
  max_pending: 50        # If more than 50 actions are pending, alert human
```

### What the Agent Does While Waiting

The agent should:
- Continue other work that does not require approval
- Queue the pending action
- Not re-request the same action (prevents notification spam)
- Not attempt to accomplish the same goal through a different (unapproved) method

---

## Audit Logging

Every action -- approved, rejected, auto-approved, or timed out -- must be logged.

### Log Format

```json
{
  "timestamp": "2025-01-15T14:32:00Z",
  "action": "send_email",
  "parameters": {
    "to": "john@company.com",
    "subject": "Follow-up",
    "body_preview": "Hi John, following up on..."
  },
  "approval_status": "approved",
  "approved_by": "user@example.com",
  "approval_method": "web_ui",
  "approval_latency_seconds": 45,
  "agent_reasoning": "Contact hasn't been reached in 7 days, per follow-up workflow",
  "execution_result": "success",
  "cost_incurred": 0.00
}
```

### What to Log

| Field | Purpose |
|---|---|
| Timestamp | When the action was requested and when it was approved/rejected |
| Action type | What the agent wanted to do |
| Parameters | Full details (who, what, where) |
| Approval status | approved, rejected, auto-approved, timed-out |
| Who approved | Your identity (for multi-user setups) |
| Approval method | Web UI, Slack, mobile, auto |
| Agent reasoning | Why the agent wanted to take this action |
| Execution result | Did the action succeed after approval? |
| Cost | Financial impact if any |

### Reviewing Audit Logs

**Weekly review (15 minutes):**
- Scan for rejected actions -- did the agent try anything concerning?
- Check auto-approved actions -- are the auto-approve rules still appropriate?
- Look for patterns -- is the agent repeatedly requesting the same action type?
- Verify costs -- do the logged costs match your API dashboards?

---

## Escalation Policy

When the agent is uncertain about an action, it should escalate to a human rather than guessing.

### When to Escalate

| Situation | Agent Should |
|---|---|
| Unclear instructions | Ask for clarification, not guess |
| Conflicting data | Present both sides, ask human to decide |
| High-stakes decision | Present options with pros/cons, ask human to choose |
| Error or unexpected result | Report the error, ask how to proceed |
| New scenario not covered by existing rules | Ask if this is within scope |

### Escalation Format

The agent should present escalations clearly:

```
ESCALATION REQUIRED

Situation: I found conflicting phone numbers for lead "John Smith":
  - GHL record: (555) 123-4567
  - Clay enrichment: (555) 987-6543
  - LinkedIn (scraped): (555) 123-4567

Options:
  A) Use GHL record (matches LinkedIn)
  B) Use Clay enrichment (most recent data source)
  C) Mark as "needs verification" and skip for now

My recommendation: Option A (GHL matches LinkedIn, 2 of 3 sources agree)

Please choose: [A] [B] [C]
```

---

## Batch Approval

For efficiency, the agent can request approval for a plan of multiple actions rather than each one individually.

### When to Use Batch Approval

| Scenario | Individual Approval | Batch Approval |
|---|---|---|
| Sending follow-up to 50 leads | Tedious (50 approvals) | Better (approve the plan once) |
| Running enrichment on 200 records | Impractical (200 approvals) | Better (approve the batch) |
| One-off email to a specific person | Better (single approval) | Unnecessary |

### Batch Approval Format

```
BATCH APPROVAL REQUEST

Plan: Send follow-up email to 47 leads who haven't responded in 7+ days

Template:
  Subject: "Quick follow-up - [Company Name]"
  Body: [template preview with merge fields]

Recipients (47 total):
  1. John Smith, Acme Corp, john@acme.com
  2. Jane Doe, BigCo Inc, jane@bigco.com
  ... (showing first 5 and last 5)
  46. Bob Wilson, StartupX, bob@startupx.com
  47. Alice Chen, TechCo, alice@techco.com

Estimated cost: $0.00 (email sending)
Estimated time: 15 minutes (rate-limited to avoid spam flags)

[Approve All] [Review Full List] [Reject] [Edit Template]
```

### Batch Safety Rules

1. Batch size limit: Maximum 100 actions per batch (configurable)
2. All actions in a batch must be the same type (cannot mix email sending with data deletion)
3. Human can view the full list before approving
4. Human can exclude specific items from the batch
5. If any item in the batch fails, the entire batch pauses and reports

---

## Emergency Stop

### How to Halt All Agent Activity Immediately

**Method 1: Docker (fastest, most reliable)**
```bash
# Stop the OpenClaw container immediately
docker compose stop openclaw

# Or if you want to kill it instantly (no graceful shutdown)
docker kill openclaw
```

**Method 2: Web UI**
If OpenClaw has an emergency stop button in the web UI, use it. But do not rely on this as your only stop mechanism -- if the agent has compromised the web UI, the stop button might not work.

**Method 3: Network Kill**
```bash
# Disconnect the container from all networks
docker network disconnect openclaw-net openclaw
```
This cuts off the agent from all external services immediately while keeping the container running (preserving logs for investigation).

**Method 4: Tailscale**
If you need to stop access from a specific device:
```bash
# Remove the Mac Mini from your tailnet (extreme measure)
tailscale down
```

### Emergency Stop Checklist

```
[ ] Stop OpenClaw container:      docker compose stop openclaw
[ ] Check for in-flight actions:  docker logs openclaw --tail 50
[ ] Revoke API keys if needed:    (see credential-management.md)
[ ] Investigate:                  docker logs openclaw > incident.log
[ ] Decide:                       Fix and restart? Or deeper investigation needed?
```

### Keep This Command Handy

Put this in a terminal alias, a desktop shortcut, or a bookmark:

```bash
# ~/.zshrc or ~/.bashrc on the Mac Mini
alias openclaw-stop='docker compose -f /path/to/openclaw/docker-compose.yml stop openclaw && echo "OpenClaw STOPPED"'
alias openclaw-kill='docker kill openclaw && echo "OpenClaw KILLED"'
alias openclaw-start='docker compose -f /path/to/openclaw/docker-compose.yml up -d openclaw && echo "OpenClaw STARTED"'
```

---

## Recommended HITL Configuration for Your Use Case

**Your use case:** AI-powered lead generation and outreach automation. Moderate risk -- you are contacting real people and spending real money on API credits.

### Phase 1: First 30 Days (High Supervision)

**Approve everything except reads.**

| Action | Policy |
|---|---|
| Read data from any source | Auto-approve |
| Write to agent workspace/memory | Auto-approve |
| Generate drafts (without sending) | Auto-approve |
| Create GHL contacts | Require approval |
| Send any message (email, SMS, GHL) | Require approval |
| Run Clay enrichment | Require approval |
| Modify Supabase data | Require approval |
| Update Airtable records | Require approval |
| Any delete operation | Require approval |
| Any cost > $1 | Require approval |

**Time commitment:** Expect 10-20 approval requests per day. Budget 15-30 minutes daily for reviews.

### Phase 2: Days 31-90 (Moderate Supervision)

After 30 days with zero incidents, relax selected controls.

| Action | Policy Change |
|---|---|
| Create GHL contacts (matching expected schema) | Auto-approve |
| Single Clay enrichment (< $0.50) | Auto-approve |
| Update Airtable records (specific tables) | Auto-approve |
| Send messages | STILL require approval |
| Delete operations | STILL require approval |
| Batch operations (> 10 items) | STILL require approval |

**Time commitment:** Expect 5-10 approval requests per day. Budget 10-15 minutes daily.

### Phase 3: Day 91+ (Calibrated Trust)

Only relax message sending after significant trust is established.

| Action | Policy Change |
|---|---|
| Send follow-up messages using APPROVED templates only | Auto-approve |
| New/custom messages | STILL require approval |
| Batch operations with APPROVED templates | Batch approval (approve the plan, not each message) |
| Delete operations | STILL require approval (forever) |
| Any new action type | STILL require approval |

**Time commitment:** Expect 2-5 approval requests per day. Budget 5-10 minutes daily.

**Delete operations should ALWAYS require approval. This rule should never be relaxed.**

---

## Metrics to Track

| Metric | What It Tells You | Action if Abnormal |
|---|---|---|
| Approval rate (% approved vs rejected) | If < 80% approved, agent is making bad decisions | Retrain/reconfigure the agent |
| Average approval latency | If > 4 hours, you are a bottleneck | Consider relaxing low-risk controls |
| Rejection reasons | Patterns in why you reject actions | Update agent instructions to prevent |
| Auto-approve incident rate | How often auto-approved actions cause issues | Tighten controls if > 0% |
| Timeout rate | If > 10%, you are missing approvals | Set up better notifications |

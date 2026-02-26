# GoHighLevel Pipeline Automation

> Automating deal movement, task creation, and reporting across GHL pipelines.

---

## Pipeline Structure

### Standard OpenClaw Sales Pipeline

```
Stage 1: New Lead (Score: 40+)
  -> Enrichment complete, basic qualification passed

Stage 2: Contacted (First outreach sent)
  -> Email/SMS/call made, waiting for response

Stage 3: Engaged (Prospect responded positively)
  -> Replied, showed interest, asked questions

Stage 4: Meeting Booked (Discovery call scheduled)
  -> Calendar appointment confirmed

Stage 5: Proposal Sent (Offer delivered)
  -> Custom proposal based on pain points

Stage 6: Negotiation (Discussing terms)
  -> Price, scope, timeline under discussion

Stage 7: Won (Deal closed)
  -> Contract signed, onboarding begins

Stage 8: Lost (Deal did not close)
  -> Reason logged, moved to re-engagement queue
```

### Pipeline Configuration in GHL

Create via GHL UI or API:
```python
pipeline_config = {
    "name": "OpenClaw Lead Pipeline",
    "stages": [
        {"name": "New Lead", "position": 0},
        {"name": "Contacted", "position": 1},
        {"name": "Engaged", "position": 2},
        {"name": "Meeting Booked", "position": 3},
        {"name": "Proposal Sent", "position": 4},
        {"name": "Negotiation", "position": 5},
        {"name": "Won", "position": 6},
        {"name": "Lost", "position": 7},
    ]
}
```

---

## Automated Stage Movement

### Trigger: Lead Score (from enrichment)

When a lead is scored, it enters the pipeline at the appropriate stage:

| Score Range | Pipeline Action |
|---|---|
| 80-100 (Hot) | Create opportunity in "New Lead" + flag for immediate outreach |
| 60-79 (Warm) | Create opportunity in "New Lead" + start nurture sequence |
| 40-59 (Cold) | Create opportunity in "New Lead" + long-term nurture |
| 0-39 | Do NOT create opportunity. Tag as disqualified. |

```python
async def place_in_pipeline(ghl_adapter, contact_id: str, lead_score: int, pipeline_id: str):
    """Create opportunity in pipeline based on lead score."""
    if lead_score < 40:
        return {"action": "disqualified", "reason": f"Score {lead_score} below threshold"}

    # Determine deal value estimate based on score and industry
    estimated_value = calculate_deal_value(lead_score)

    opportunity = await ghl_adapter.create_opportunity({
        "pipelineId": pipeline_id,
        "pipelineStageId": get_stage_id("New Lead"),
        "contactId": contact_id,
        "name": f"Lead - {contact_name}",
        "monetaryValue": estimated_value,
        "status": "open",
    })

    # Set follow-up based on temperature
    if lead_score >= 80:
        await create_urgent_task(ghl_adapter, contact_id, "Hot lead - call within 1 hour")
    elif lead_score >= 60:
        await start_nurture_sequence(ghl_adapter, contact_id, "warm-nurture")
    else:
        await start_nurture_sequence(ghl_adapter, contact_id, "cold-drip")

    return {"action": "placed", "opportunity_id": opportunity["id"]}
```

### Trigger: Engagement Actions

Monitor for prospect actions and move stages automatically:

| Action Detected | Stage Movement | Additional Actions |
|---|---|---|
| Email opened (3+ times) | Stay in "Contacted" | Increase engagement score |
| Link clicked | Stay in "Contacted" | Note which link, tag interest area |
| Email reply (positive) | Move to "Engaged" | Alert sales rep, log reply content |
| Email reply (negative/unsubscribe) | Move to "Lost" | Reason: "Not interested" |
| Form submitted | Move to "Engaged" | Process form data, update contact |
| Appointment booked | Move to "Meeting Booked" | Generate meeting prep brief |
| Proposal viewed | Stay in "Proposal Sent" | Note view time, pages viewed |
| Contract signed | Move to "Won" | Trigger onboarding workflow |

```python
ENGAGEMENT_RULES = {
    "email_opened": {
        "min_count": 3,
        "action": "increment_engagement_score",
        "stage_change": None,
    },
    "link_clicked": {
        "action": "tag_interest",
        "stage_change": None,
    },
    "email_replied_positive": {
        "action": "alert_sales_rep",
        "stage_change": "Engaged",
    },
    "form_submitted": {
        "action": "process_form_data",
        "stage_change": "Engaged",
    },
    "appointment_booked": {
        "action": "generate_meeting_prep",
        "stage_change": "Meeting Booked",
    },
    "proposal_viewed": {
        "action": "note_view_details",
        "stage_change": None,
    },
}

async def process_engagement_event(ghl_adapter, event: dict):
    """Process an engagement event and apply pipeline rules."""
    event_type = event["type"]
    contact_id = event["contactId"]
    opportunity_id = event.get("opportunityId")

    rule = ENGAGEMENT_RULES.get(event_type)
    if not rule:
        return

    # Execute the action
    action_fn = globals().get(rule["action"])
    if action_fn:
        await action_fn(ghl_adapter, contact_id, event)

    # Move pipeline stage if specified
    if rule.get("stage_change") and opportunity_id:
        await ghl_adapter.update_opportunity(opportunity_id, {
            "pipelineStageId": get_stage_id(rule["stage_change"])
        })
```

### Trigger: Time-Based Rules (Stale Deal Detection)

Deals sitting too long in a stage need attention:

| Stage | Stale After | Action |
|---|---|---|
| New Lead | 24 hours | Auto-send first outreach if not done |
| Contacted | 5 days | Send follow-up, escalate to manager |
| Engaged | 3 days | Suggest next touchpoint to sales rep |
| Meeting Booked | 1 day before meeting | Send meeting prep and reminder |
| Proposal Sent | 7 days | Send follow-up, offer incentive |
| Negotiation | 14 days | Escalate to senior closer |

```python
async def check_stale_deals(ghl_adapter, pipeline_id: str):
    """Run daily to detect and handle stale deals."""
    stale_rules = {
        "New Lead": timedelta(hours=24),
        "Contacted": timedelta(days=5),
        "Engaged": timedelta(days=3),
        "Proposal Sent": timedelta(days=7),
        "Negotiation": timedelta(days=14),
    }

    opportunities = await ghl_adapter.list_opportunities(pipeline_id)
    now = datetime.utcnow()
    stale_deals = []

    for opp in opportunities:
        stage_name = opp["stageName"]
        if stage_name not in stale_rules:
            continue

        last_activity = parse_datetime(opp.get("lastActivityAt", opp["createdAt"]))
        threshold = stale_rules[stage_name]

        if now - last_activity > threshold:
            stale_deals.append({
                "opportunity": opp,
                "stage": stage_name,
                "stale_for": str(now - last_activity),
                "recommended_action": get_stale_action(stage_name)
            })

    return stale_deals
```

### Trigger: Agent Analysis (AI Deal Readiness)

OpenClaw can analyze deal context and recommend stage changes:

```python
async def analyze_deal_readiness(openclaw_agent, opportunity: dict, contact: dict):
    """Use AI to evaluate if a deal is ready to advance."""
    context = f"""
    Contact: {contact['firstName']} {contact['lastName']} at {contact.get('companyName')}
    Current Stage: {opportunity['stageName']}
    Lead Score: {contact.get('customFields', {}).get('lead_score', 'unknown')}
    Pain Signals: {contact.get('customFields', {}).get('pain_signals', 'none detected')}
    Last Activity: {opportunity.get('lastActivityAt')}
    Notes: {opportunity.get('notes', 'No notes')}
    """

    analysis = await openclaw_agent.analyze(
        prompt=f"Based on this deal context, should this deal advance to the next stage? "
               f"What specific action should be taken next?\n\n{context}",
        output_schema={
            "should_advance": "boolean",
            "confidence": "float 0-1",
            "recommended_action": "string",
            "reasoning": "string"
        }
    )

    return analysis
```

---

## Pipeline Templates Per Industry Vertical

### Dental Practice Pipeline
```
New Lead -> Initial Outreach -> Practice Visit Scheduled -> Audit Presented ->
Proposal Sent -> Decision -> Won/Lost
```
- **Unique:** Audit includes website review, GMB analysis, patient acquisition cost analysis
- **Typical deal value:** $1,500-3,000/mo

### HVAC Company Pipeline
```
New Lead -> Phone Call -> Site Assessment -> Proposal -> Contract -> Won/Lost
```
- **Unique:** Seasonal urgency (pre-summer/pre-winter are hot periods)
- **Typical deal value:** $800-2,000/mo

### Law Firm Pipeline
```
New Lead -> Initial Consultation -> Needs Assessment -> Proposal ->
Partner Review -> Won/Lost
```
- **Unique:** Compliance-heavy, need to address bar association rules for advertising
- **Typical deal value:** $2,000-5,000/mo

### Restaurant Pipeline
```
New Lead -> Phone/Visit -> Menu/Photo Audit -> Proposal -> Trial Period -> Won/Lost
```
- **Unique:** Visual-heavy (photos, social), seasonal promotions important
- **Typical deal value:** $500-1,500/mo

---

## Task Automation on Stage Change

When an opportunity moves stages, create follow-up tasks automatically:

```python
STAGE_TASKS = {
    "Contacted": [
        {"title": "Follow up if no response in 48h", "dueIn": timedelta(hours=48)},
    ],
    "Engaged": [
        {"title": "Schedule discovery call", "dueIn": timedelta(hours=24)},
        {"title": "Send case study relevant to their industry", "dueIn": timedelta(hours=4)},
    ],
    "Meeting Booked": [
        {"title": "Prepare meeting brief with pain points", "dueIn": timedelta(hours=-2)},  # 2h before
        {"title": "Send meeting confirmation and agenda", "dueIn": timedelta(hours=-24)},
    ],
    "Proposal Sent": [
        {"title": "Follow up on proposal in 3 days", "dueIn": timedelta(days=3)},
        {"title": "Prepare negotiation talking points", "dueIn": timedelta(days=5)},
    ],
    "Won": [
        {"title": "Send welcome packet", "dueIn": timedelta(hours=1)},
        {"title": "Schedule onboarding kickoff", "dueIn": timedelta(days=1)},
        {"title": "Set up client sub-account in GHL", "dueIn": timedelta(days=1)},
    ],
}

async def create_stage_tasks(ghl_adapter, opportunity_id: str, new_stage: str, contact_id: str):
    """Create tasks when opportunity moves to a new stage."""
    tasks = STAGE_TASKS.get(new_stage, [])
    for task_template in tasks:
        due_date = datetime.utcnow() + task_template["dueIn"]
        await ghl_adapter.create_task({
            "title": task_template["title"],
            "contactId": contact_id,
            "dueDate": due_date.isoformat(),
            "assignedTo": get_assigned_rep(opportunity_id),
        })
```

---

## Reporting

### Key Pipeline Metrics to Track

| Metric | Calculation | Target |
|---|---|---|
| **Pipeline velocity** | Avg days from New Lead to Won | < 30 days |
| **Stage conversion rate** | % moving from each stage to next | > 50% per stage |
| **Win rate** | Won / (Won + Lost) | > 25% |
| **Average deal value** | Total revenue / Deals won | Industry dependent |
| **Lead-to-meeting rate** | Meetings booked / New leads | > 15% |
| **Proposal-to-close rate** | Won / Proposals sent | > 40% |
| **Stale deal count** | Deals past stale threshold | Trending to 0 |
| **Cost per acquisition** | Total spend / Deals won | < 1 month revenue |

### Integration with Rise Local Pain Scoring

The 15-signal pain scoring model feeds directly into pipeline placement:

**Signal categories that affect pipeline behavior:**
1. **Website signals** (no site, slow, not mobile, no SSL) -> Tag as `pain:website-issues`, higher urgency
2. **Review signals** (low rating, few reviews) -> Tag as `pain:reputation`, include in outreach messaging
3. **Technology signals** (outdated CMS, no analytics) -> Tag as `pain:tech-gap`, position as modernization
4. **Presence signals** (no social, unclaimed GMB) -> Tag as `pain:visibility`, focus on visibility pitch
5. **Competitive signals** (competitors doing better online) -> Tag as `pain:competitive-threat`, urgency pitch

Each pain signal detected adds points to the lead score and gets converted to a GHL tag for segmentation and personalized outreach messaging.

---

## RESEARCH GAPS

- [ ] Verify GHL API supports programmatic pipeline creation
- [ ] Determine if GHL webhooks fire on opportunity stage changes
- [ ] Test task creation API with due dates and assignments
- [ ] Confirm GHL workflow trigger API is available on your plan
- [ ] Check if GHL has built-in stale deal detection or if it must be custom

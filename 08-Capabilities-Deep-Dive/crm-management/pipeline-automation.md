# GHL Pipeline Automation via OpenClaw

## Overview

Pipeline automation transforms the CRM from a passive data store into an active deal management system. OpenClaw monitors pipeline activity, triggers automated transitions based on real events, detects stale deals, re-engages cold opportunities, and provides analytics on pipeline health. This document defines the pipeline architecture, automation rules, and OpenClaw skills needed for full pipeline management.

## Pipeline Design for Marketing Agency

### Primary Pipeline: Client Acquisition

```
Stage 0: New Lead
    -> Stage 1: Qualified
    -> Stage 2: Contacted
    -> Stage 3: Meeting Scheduled
    -> Stage 4: Proposal Sent
    -> Stage 5: Negotiation
    -> Stage 6a: Closed Won
    -> Stage 6b: Closed Lost
```

### Stage Definitions

| Stage | Entry Criteria | Exit Criteria | Owner | SLA |
|-------|---------------|---------------|-------|-----|
| New Lead | Contact created via enrichment flow | Enrichment complete, pain score assigned | System (auto) | 0-2 hours |
| Qualified | Pain score >= 50, email verified | First outreach sent | System (auto) | 24 hours |
| Contacted | First message sent (email/SMS/call) | Response received or meeting booked | Sales rep | 48 hours |
| Meeting Scheduled | Appointment booked in GHL calendar | Meeting completed | Sales rep | Varies (meeting date) |
| Proposal Sent | Proposal document generated and sent | Client responds to proposal | Sales rep | 72 hours |
| Negotiation | Client engaged in discussion | Agreement reached or lost | Account exec | 7 days |
| Closed Won | Contract signed, payment received | N/A (terminal) | Account exec | N/A |
| Closed Lost | Client declined or went silent | N/A (terminal) | System | N/A |

### Secondary Pipelines

**Upsell Pipeline:** For existing clients being offered additional services.

```
Identified Opportunity -> Presented -> Considering -> Closed Won / Closed Lost
```

**Referral Pipeline:** For tracking referral-sourced deals with different handling.

```
Referred -> Contacted -> Meeting -> Proposal -> Closed Won / Lost
```

**Re-engagement Pipeline:** For previously lost deals being re-approached.

```
Re-engaged -> Responded -> Meeting -> Proposal -> Closed Won / Lost
```

## Automated Stage Transitions

### New Lead -> Qualified (Fully Automated)

**Trigger:** Contact enrichment flow completes successfully.

```python
async def auto_qualify_lead(contact_id: str, enrichment_result: dict):
    """
    Automatically move lead from New Lead to Qualified
    if enrichment criteria are met.
    """
    pain_score = enrichment_result["pain_data"]["score"]
    email_verified = enrichment_result["contact_data"].get("email_verified", False)
    has_phone = bool(enrichment_result["contact_data"].get("owner_phone") or
                     enrichment_result["lead"].get("phone"))

    # Qualification criteria
    qualifies = (
        pain_score >= 50 and
        (email_verified or has_phone) and
        enrichment_result["business_data"].get("business_status") == "OPERATIONAL"
    )

    if qualifies:
        # Move to Qualified stage
        opportunity = await ghl.get_opportunity_by_contact(contact_id)
        if opportunity:
            await ghl.update_opportunity(opportunity["id"], {
                "pipelineStageId": STAGES["qualified"],
                "customFields": {
                    "qualified_date": datetime.now().isoformat(),
                    "qualification_method": "auto_enrichment"
                }
            })

            # Add note explaining qualification
            await ghl.add_note(contact_id,
                f"Auto-qualified: Pain score {pain_score}/100, "
                f"Email {'verified' if email_verified else 'unverified'}, "
                f"Phone {'available' if has_phone else 'unavailable'}"
            )
    else:
        # Move to nurture or keep as new lead
        reasons = []
        if pain_score < 50:
            reasons.append(f"Low pain score ({pain_score})")
        if not email_verified and not has_phone:
            reasons.append("No verified contact method")

        await ghl.add_note(contact_id,
            f"Did not auto-qualify: {'; '.join(reasons)}. Moved to nurture."
        )
        await ghl.add_tags(contact_id, ["nurture", "manual_review"])
```

### Qualified -> Contacted (Automated on Outreach)

**Trigger:** First outreach message sent (email, SMS, or call logged).

```python
async def on_outreach_sent(contact_id: str, message_type: str):
    """
    Automatically move deal from Qualified to Contacted
    when first outreach is sent.
    """
    opportunity = await ghl.get_opportunity_by_contact(contact_id)
    if not opportunity:
        return

    current_stage = opportunity["pipelineStageId"]
    if current_stage == STAGES["qualified"]:
        await ghl.update_opportunity(opportunity["id"], {
            "pipelineStageId": STAGES["contacted"],
            "customFields": {
                "first_outreach_date": datetime.now().isoformat(),
                "first_outreach_type": message_type
            }
        })

# Triggered by GHL webhook: OutboundMessage event
async def handle_outbound_message_webhook(event: dict):
    contact_id = event["data"]["contactId"]
    message_type = event["data"]["type"]  # SMS, Email, etc.
    await on_outreach_sent(contact_id, message_type)
```

### Contacted -> Meeting Scheduled (Automated on Booking)

**Trigger:** Appointment created in GHL calendar linked to the contact.

```python
async def on_appointment_booked(event: dict):
    """
    Automatically move deal to Meeting Scheduled
    when appointment is created for the contact.
    """
    contact_id = event["data"]["contactId"]
    appointment_date = event["data"]["startTime"]

    opportunity = await ghl.get_opportunity_by_contact(contact_id)
    if not opportunity:
        return

    current_stage = opportunity["pipelineStageId"]
    if current_stage in [STAGES["qualified"], STAGES["contacted"]]:
        await ghl.update_opportunity(opportunity["id"], {
            "pipelineStageId": STAGES["meeting_scheduled"],
            "customFields": {
                "meeting_date": appointment_date,
                "meeting_type": event["data"].get("calendarName", "strategy_call")
            }
        })

        # Create pre-meeting prep task
        await ghl.create_task(contact_id, {
            "title": f"Prepare for meeting with {opportunity['name']}",
            "dueDate": (parse_datetime(appointment_date) - timedelta(hours=2)).isoformat(),
            "description": "Review contact profile, enrichment data, and pain points. "
                           "Prepare talking points and relevant case studies.",
            "assignedTo": opportunity.get("assignedTo")
        })

# Triggered by GHL webhook: AppointmentCreate event
```

### Meeting Scheduled -> Proposal Sent (Automated on Proposal Generation)

**Trigger:** Proposal document generated and sent to client.

```python
async def on_proposal_sent(contact_id: str, proposal_url: str):
    """
    Move deal to Proposal Sent after proposal is generated and delivered.
    """
    opportunity = await ghl.get_opportunity_by_contact(contact_id)
    if not opportunity:
        return

    await ghl.update_opportunity(opportunity["id"], {
        "pipelineStageId": STAGES["proposal_sent"],
        "customFields": {
            "proposal_sent_date": datetime.now().isoformat(),
            "proposal_url": proposal_url
        }
    })

    # Schedule follow-up if no response in 48 hours
    await ghl.create_task(contact_id, {
        "title": f"Follow up on proposal - {opportunity['name']}",
        "dueDate": (datetime.now() + timedelta(hours=48)).isoformat(),
        "description": f"Proposal sent. Follow up if no response. Link: {proposal_url}",
        "assignedTo": opportunity.get("assignedTo")
    })
```

### Proposal Sent -> Negotiation (Manual)

**Trigger:** Sales rep manually moves when client responds to proposal with questions or counteroffers.

This stage requires human judgment -- the system cannot determine whether a client response constitutes "negotiation" vs. "rejection."

### Negotiation -> Closed Won / Closed Lost (Manual)

**Trigger:** Sales rep manually closes the deal.

On Closed Won:
```python
async def on_deal_won(opportunity_id: str):
    """Handle deal closed won."""
    opp = await ghl.get_opportunity(opportunity_id)
    contact_id = opp["contactId"]

    # Update opportunity
    await ghl.update_opportunity(opportunity_id, {
        "status": "won",
        "customFields": {
            "closed_date": datetime.now().isoformat(),
            "time_to_close": calculate_days_in_pipeline(opp)
        }
    })

    # Update contact tags
    await ghl.remove_tags(contact_id, ["prospect", "nurture"])
    await ghl.add_tags(contact_id, ["client", "active_client", f"service:{opp.get('service_type', 'general')}"])

    # Create onboarding tasks
    await create_onboarding_tasks(contact_id, opp)

    # Notify team
    await slack.send_message(
        channel="#wins",
        message=f"*Deal Won!* {opp['name']} - ${opp['monetaryValue']}/mo"
    )

    # Enroll in client onboarding workflow
    await ghl.add_to_workflow(contact_id, WORKFLOWS["client_onboarding"])
```

On Closed Lost:
```python
async def on_deal_lost(opportunity_id: str, loss_reason: str):
    """Handle deal closed lost."""
    opp = await ghl.get_opportunity(opportunity_id)
    contact_id = opp["contactId"]

    await ghl.update_opportunity(opportunity_id, {
        "status": "lost",
        "customFields": {
            "lost_date": datetime.now().isoformat(),
            "loss_reason": loss_reason,
            "time_in_pipeline": calculate_days_in_pipeline(opp)
        }
    })

    # Tag for re-engagement later
    await ghl.add_tags(contact_id, ["lost_deal", f"lost_reason:{loss_reason}"])

    # Schedule re-engagement in 90 days
    await ghl.create_task(contact_id, {
        "title": f"Re-engage {opp['name']} (lost 90 days ago)",
        "dueDate": (datetime.now() + timedelta(days=90)).isoformat(),
        "description": f"Previously lost. Reason: {loss_reason}. Check if situation has changed.",
        "assignedTo": opp.get("assignedTo")
    })
```

## Stale Deal Detection

### Configuration

```python
STALE_THRESHOLDS = {
    "new_lead": timedelta(days=1),          # Should be qualified within 1 day
    "qualified": timedelta(days=2),         # Should be contacted within 2 days
    "contacted": timedelta(days=5),         # Should get response within 5 days
    "meeting_scheduled": timedelta(days=7), # Meeting should happen within 7 days
    "proposal_sent": timedelta(days=5),     # Should get response within 5 days
    "negotiation": timedelta(days=10),      # Should close within 10 days
}
```

### Stale Deal Scanner

```python
async def scan_for_stale_deals():
    """
    Run daily (or every few hours) to detect stale deals.
    Triggered by cron job or scheduled task.
    """
    for stage_name, threshold in STALE_THRESHOLDS.items():
        stage_id = STAGES[stage_name]

        # Get all opportunities in this stage
        opportunities = await ghl.search_opportunities(
            pipelineStageId=stage_id,
            status="open"
        )

        for opp in opportunities:
            last_activity = parse_datetime(opp.get("lastStatusChangeAt") or opp["dateAdded"])
            time_in_stage = datetime.now() - last_activity

            if time_in_stage > threshold:
                await handle_stale_deal(opp, stage_name, time_in_stage)

async def handle_stale_deal(opportunity: dict, stage: str, time_stale: timedelta):
    """Handle a deal that has been in a stage too long."""
    contact_id = opportunity["contactId"]
    days_stale = time_stale.days

    # Add stale tag
    await ghl.add_tags(contact_id, [f"stale:{stage}"])

    # Create urgent task
    await ghl.create_task(contact_id, {
        "title": f"STALE DEAL: {opportunity['name']} stuck in {stage} for {days_stale} days",
        "dueDate": datetime.now().isoformat(),  # Due immediately
        "description": f"This deal has been in the '{stage}' stage for {days_stale} days, "
                       f"exceeding the {STALE_THRESHOLDS[stage].days}-day threshold. "
                       f"Take action: advance, re-engage, or close as lost.",
        "assignedTo": opportunity.get("assignedTo")
    })

    # Notify via Slack
    await slack.send_message(
        channel="#stale-deals",
        message=f"*Stale Deal Alert:* {opportunity['name']} has been in "
                f"'{stage}' for {days_stale} days. "
                f"Value: ${opportunity.get('monetaryValue', 0)}/mo. "
                f"Assigned to: {opportunity.get('assignedTo', 'Unassigned')}"
    )
```

## Automated Re-engagement

### For Stale "Contacted" Deals

```python
async def re_engage_stale_contacted(contact_id: str, opportunity: dict):
    """
    Send a follow-up message to contacts who haven't responded
    after initial outreach.
    """
    contact = await ghl.get_contact(contact_id)
    business_name = contact.get("companyName", "your business")

    # Check how many follow-ups already sent
    existing_tags = contact.get("tags", [])
    follow_up_count = sum(1 for t in existing_tags if t.startswith("followup:"))

    if follow_up_count >= 3:
        # Max follow-ups reached, move to nurture
        await ghl.update_opportunity(opportunity["id"], {
            "pipelineStageId": STAGES["closed_lost"],
            "customFields": {"loss_reason": "no_response_after_3_followups"}
        })
        await ghl.add_tags(contact_id, ["no_response", "lost_reason:unresponsive"])
        return

    # Send follow-up based on count
    templates = {
        0: "Hi {first_name}, I wanted to follow up on my previous message about improving {business_name}'s online presence. Have you had a chance to review it?",
        1: "Hi {first_name}, I know you're busy running {business_name}. I wanted to quickly share a case study of how we helped a similar {industry} business increase their leads by 40%. Would you be interested in a quick 15-minute chat?",
        2: "Hi {first_name}, last note from me! If {business_name}'s marketing is a priority, I'd love to connect. If not, no worries at all. Here's my calendar if you change your mind: {calendar_link}"
    }

    message = templates[follow_up_count].format(
        first_name=contact.get("firstName", "there"),
        business_name=business_name,
        industry=get_industry_from_tags(existing_tags),
        calendar_link=AGENCY_CALENDAR_LINK
    )

    await ghl.send_sms(contact_id, message)
    await ghl.add_tags(contact_id, [f"followup:{follow_up_count + 1}"])
    await ghl.add_note(contact_id, f"Auto follow-up #{follow_up_count + 1} sent")
```

### For Stale "Proposal Sent" Deals

```python
async def re_engage_stale_proposal(contact_id: str, opportunity: dict):
    """Follow up on an unanswered proposal."""
    contact = await ghl.get_contact(contact_id)
    proposal_url = opportunity.get("customFields", {}).get("proposal_url", "")

    message = (
        f"Hi {contact.get('firstName', 'there')}, I wanted to check in on the proposal "
        f"I sent over for {contact.get('companyName', 'your business')}. "
        f"Do you have any questions I can help address? Happy to hop on a quick call "
        f"to walk through anything."
    )

    await ghl.send_email(contact_id, {
        "subject": f"Following up on your marketing proposal",
        "message": message
    })
```

## Pipeline Analytics

### Key Metrics to Track

```python
async def calculate_pipeline_analytics(pipeline_id: str, period: str) -> dict:
    """Calculate comprehensive pipeline analytics."""

    opportunities = await ghl.search_opportunities(
        pipelineId=pipeline_id,
        dateRange=period
    )

    analytics = {
        "summary": {
            "total_deals": len(opportunities),
            "total_value": sum(o.get("monetaryValue", 0) for o in opportunities),
            "open_deals": len([o for o in opportunities if o["status"] == "open"]),
            "won_deals": len([o for o in opportunities if o["status"] == "won"]),
            "lost_deals": len([o for o in opportunities if o["status"] == "lost"]),
        },
        "conversion_rates": {},
        "stage_distribution": {},
        "velocity": {},
        "revenue_forecast": {}
    }

    # Stage distribution
    for stage_name, stage_id in STAGES.items():
        stage_deals = [o for o in opportunities if o["pipelineStageId"] == stage_id]
        analytics["stage_distribution"][stage_name] = {
            "count": len(stage_deals),
            "value": sum(o.get("monetaryValue", 0) for o in stage_deals)
        }

    # Conversion rates (stage to stage)
    total = len(opportunities)
    for i, (stage_name, stage_id) in enumerate(STAGES.items()):
        if i == 0:
            analytics["conversion_rates"][stage_name] = 100.0
        else:
            reached = len([o for o in opportunities
                          if stage_reached(o, stage_id)])
            analytics["conversion_rates"][stage_name] = (
                (reached / total * 100) if total > 0 else 0
            )

    # Average time in each stage (velocity)
    for stage_name in STAGES:
        times = get_time_in_stage(opportunities, stage_name)
        if times:
            analytics["velocity"][stage_name] = {
                "avg_days": sum(times) / len(times),
                "median_days": sorted(times)[len(times) // 2],
                "max_days": max(times)
            }

    # Revenue forecast
    analytics["revenue_forecast"] = {
        "weighted_pipeline": sum(
            o.get("monetaryValue", 0) * get_stage_probability(o["pipelineStageId"])
            for o in opportunities if o["status"] == "open"
        ),
        "best_case": sum(
            o.get("monetaryValue", 0)
            for o in opportunities if o["status"] == "open"
        ),
        "expected_closes_30_days": estimate_closes_in_period(opportunities, days=30)
    }

    return analytics

# Stage win probability for revenue weighting
STAGE_PROBABILITY = {
    "new_lead": 0.05,
    "qualified": 0.10,
    "contacted": 0.15,
    "meeting_scheduled": 0.30,
    "proposal_sent": 0.50,
    "negotiation": 0.75,
    "closed_won": 1.00,
    "closed_lost": 0.00
}
```

### Analytics Reporting

```python
async def generate_pipeline_report(pipeline_id: str, period: str) -> str:
    """Generate a formatted pipeline report for Slack/email delivery."""
    analytics = await calculate_pipeline_analytics(pipeline_id, period)

    report = f"""
Pipeline Report - {period}
{'=' * 40}

SUMMARY
  Total Deals: {analytics['summary']['total_deals']}
  Open: {analytics['summary']['open_deals']}
  Won: {analytics['summary']['won_deals']}
  Lost: {analytics['summary']['lost_deals']}
  Total Value: ${analytics['summary']['total_value']:,.0f}/mo

CONVERSION FUNNEL
{format_funnel(analytics['conversion_rates'])}

VELOCITY (Avg Days in Stage)
{format_velocity(analytics['velocity'])}

REVENUE FORECAST
  Weighted Pipeline: ${analytics['revenue_forecast']['weighted_pipeline']:,.0f}/mo
  Best Case: ${analytics['revenue_forecast']['best_case']:,.0f}/mo
  Expected Closes (30 days): {analytics['revenue_forecast']['expected_closes_30_days']}

STAGE DISTRIBUTION
{format_stage_distribution(analytics['stage_distribution'])}
    """
    return report
```

## Multi-Pipeline Management

### Pipeline Router

```python
async def route_to_pipeline(contact_id: str, lead: dict, pain_data: dict):
    """Route contact to the appropriate pipeline based on context."""

    source = lead.get("source", "")
    is_existing_client = "active_client" in (await ghl.get_contact(contact_id)).get("tags", [])

    if is_existing_client:
        pipeline_id = PIPELINES["upsell"]
        stage_id = UPSELL_STAGES["identified"]
    elif source == "referral":
        pipeline_id = PIPELINES["referral"]
        stage_id = REFERRAL_STAGES["referred"]
    elif lead.get("previously_lost"):
        pipeline_id = PIPELINES["re_engagement"]
        stage_id = REENGAGEMENT_STAGES["re_engaged"]
    else:
        pipeline_id = PIPELINES["client_acquisition"]
        stage_id = STAGES["new_lead"]

    await ghl.create_opportunity({
        "pipelineId": pipeline_id,
        "pipelineStageId": stage_id,
        "contactId": contact_id,
        "name": f"{lead['business_name']} - {get_service_label(pain_data)}",
        "monetaryValue": estimate_deal_value(lead.get("industry"), pain_data["score"]),
        "source": source,
        "status": "open"
    })
```

## OpenClaw Skills for Pipeline Management

### Skill: move_deal

```python
async def move_deal(contact_name: str, target_stage: str, notes: str = None):
    """Move a deal to a new pipeline stage."""
    # Find contact by name
    # Find associated opportunity
    # Validate stage transition is allowed
    # Move opportunity to new stage
    # Add notes if provided
    # Return confirmation
```

### Skill: create_task

```python
async def create_follow_up_task(contact_name: str, task_description: str,
                                 due_in_hours: int = 24):
    """Create a follow-up task for a contact."""
```

### Skill: send_followup

```python
async def send_followup(contact_name: str, message: str = None,
                        channel: str = "sms"):
    """Send a follow-up message to a contact. Auto-generates message if not provided."""
```

### Skill: generate_proposal

```python
async def generate_proposal(contact_name: str, services: list = None):
    """Generate a proposal presentation for a contact based on their pain points."""
    # Pull contact data and enrichment from GHL
    # Determine recommended services from pain points
    # Generate proposal presentation (see presentations/ docs)
    # Return proposal URL/file
```

### Skill: pipeline_status

```python
async def pipeline_status(pipeline: str = "acquisition"):
    """Get current pipeline status summary."""
    # Pull pipeline analytics
    # Format as readable summary
    # Include stale deal alerts
    # Return formatted report
```

## Automation Schedule

| Automation | Frequency | Time | Description |
|------------|-----------|------|-------------|
| Stale deal scan | Every 4 hours | Rolling | Detect deals stuck too long |
| Follow-up sequences | Daily | 9:00 AM | Send scheduled follow-ups |
| Pipeline analytics | Daily | 8:00 AM | Generate daily summary |
| Re-engagement check | Weekly | Monday 10:00 AM | Check 90-day old lost deals |
| Pipeline cleanup | Monthly | 1st of month | Archive old closed deals |

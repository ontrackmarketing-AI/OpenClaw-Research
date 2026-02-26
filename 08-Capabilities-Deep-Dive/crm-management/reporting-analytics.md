# CRM Reporting and Analytics via OpenClaw

## Overview

Reporting is one of the highest-value capabilities OpenClaw can provide. Instead of manually pulling data from multiple sources and assembling reports, OpenClaw automates the entire process: querying CRM data, combining it with analytics and enrichment data, generating visualizations, formulating actionable insights, and delivering polished reports on a schedule or on demand. This document defines the report types, data sources, delivery mechanisms, and implementation approach.

## Report Types

### 1. Daily Summary

**Purpose:** Quick snapshot of yesterday's CRM activity delivered each morning.

**Content:**
```
Daily CRM Summary - [Date]
==========================

NEW LEADS
  Total new contacts: 12
  By source:
    Google Ads: 5
    Website Form: 3
    Referral: 2
    Scraper: 2
  High-value leads (score >= 75): 3
    - ABC Plumbing (score: 87)
    - Smith HVAC (score: 79)
    - Quick Electric (score: 76)

PIPELINE ACTIVITY
  Deals moved forward: 4
    - Johnson Roofing: Contacted -> Meeting Scheduled
    - Metro Dental: Meeting -> Proposal Sent
    - Green Landscape: New Lead -> Qualified
    - River Auto: Qualified -> Contacted
  Deals closed: 1
    - Best Plumbers Inc: Closed Won ($2,500/mo)
  Deals lost: 0
  Stale deals: 2 (see alerts below)

TASKS
  Created: 8
  Completed: 6
  Overdue: 3

COMMUNICATIONS
  Emails sent: 15
  SMS sent: 8
  Calls logged: 4
  Responses received: 6

ALERTS
  - Metro Dental proposal unanswered for 4 days (threshold: 5)
  - River Auto has been in Contacted for 4 days (threshold: 5)
```

**Data Sources:**
- GHL Contacts API (new contacts, filtered by date)
- GHL Opportunities API (stage changes, closures)
- GHL Tasks API (task counts and statuses)
- GHL Conversations API (message counts)

**Implementation:**

```python
async def generate_daily_summary(date: str = None) -> dict:
    """Generate daily CRM summary for the specified date (defaults to yesterday)."""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    date_start = f"{date}T00:00:00Z"
    date_end = f"{date}T23:59:59Z"

    # Parallel data fetching
    new_contacts = await ghl.get_contacts(
        dateAdded_gte=date_start, dateAdded_lte=date_end
    )
    opportunities = await ghl.get_opportunities(
        lastStatusChangeAt_gte=date_start, lastStatusChangeAt_lte=date_end
    )
    tasks = await ghl.get_tasks(date_range=(date_start, date_end))

    # Process and structure
    summary = {
        "date": date,
        "new_leads": {
            "total": len(new_contacts),
            "by_source": group_by_source(new_contacts),
            "high_value": [c for c in new_contacts
                          if c.get("customField", {}).get("pain_score", 0) >= 75]
        },
        "pipeline": {
            "moved_forward": get_stage_advances(opportunities),
            "closed_won": [o for o in opportunities if o["status"] == "won"],
            "closed_lost": [o for o in opportunities if o["status"] == "lost"],
            "stale_alerts": await get_stale_deals()
        },
        "tasks": {
            "created": len([t for t in tasks if t["dateAdded"] >= date_start]),
            "completed": len([t for t in tasks if t.get("completedAt", "") >= date_start]),
            "overdue": len([t for t in tasks if t.get("dueDate", "") < date_start
                           and not t.get("completedAt")])
        }
    }

    return summary
```

### 2. Weekly Pipeline Report

**Purpose:** Comprehensive pipeline health assessment delivered every Monday.

**Content:**
- Pipeline snapshot: deals per stage, total value per stage
- Conversion rates: stage-to-stage conversion for the week
- Velocity: average days in each stage
- New deals entered pipeline
- Deals won/lost with details
- Revenue forecast: weighted and best-case
- Week-over-week comparison
- Stale deal list with recommended actions
- Top priority deals (highest value, closest to close)
- Charts: funnel visualization, pipeline value bar chart, trend lines

**Implementation:**

```python
async def generate_weekly_pipeline_report(week_ending: str = None) -> dict:
    """Generate comprehensive weekly pipeline report."""
    if not week_ending:
        # Default to last Sunday
        today = datetime.now()
        week_ending = (today - timedelta(days=today.weekday() + 1)).strftime("%Y-%m-%d")

    week_start = (parse_date(week_ending) - timedelta(days=6)).strftime("%Y-%m-%d")
    prev_week_start = (parse_date(week_start) - timedelta(days=7)).strftime("%Y-%m-%d")
    prev_week_end = (parse_date(week_start) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Current week data
    current = await calculate_pipeline_analytics(
        PIPELINES["client_acquisition"], f"{week_start}:{week_ending}"
    )

    # Previous week data (for comparison)
    previous = await calculate_pipeline_analytics(
        PIPELINES["client_acquisition"], f"{prev_week_start}:{prev_week_end}"
    )

    # Calculate week-over-week changes
    wow = {
        "new_deals": current["summary"]["total_deals"] - previous["summary"]["total_deals"],
        "value_change": current["summary"]["total_value"] - previous["summary"]["total_value"],
        "win_rate_change": (
            (current["summary"]["won_deals"] / max(current["summary"]["total_deals"], 1) * 100) -
            (previous["summary"]["won_deals"] / max(previous["summary"]["total_deals"], 1) * 100)
        )
    }

    # Generate charts
    charts = await generate_pipeline_charts(current, previous)

    return {
        "period": f"{week_start} to {week_ending}",
        "current": current,
        "previous": previous,
        "week_over_week": wow,
        "charts": charts,
        "stale_deals": await get_stale_deals_with_recommendations(),
        "top_priority": await get_top_priority_deals(limit=5),
        "insights": await generate_pipeline_insights(current, previous, wow)
    }
```

### 3. Monthly Performance Report

**Purpose:** Full performance review with trends, analysis, and strategic recommendations. This is the most comprehensive report, suitable for client-facing delivery or internal strategy review.

**Content:**
- Executive summary (3-5 key highlights, AI-generated)
- Lead generation: total leads, by source, by industry, trend vs. prior months
- Pipeline performance: win rate, deal velocity, average deal value
- Revenue: closed revenue, MRR growth, churn (if applicable)
- Channel performance: which marketing channels drive the best leads
- SEO performance: ranking changes, organic traffic trend, keyword opportunities
- Paid advertising: spend, CPC, CPL, ROAS by campaign
- Enrichment metrics: enrichment success rate, average pain score, cost per enriched lead
- Competitive landscape: competitor movements detected during the month
- Recommendations: 3-5 AI-generated, data-backed recommendations
- Next month goals: suggested targets based on trends

**Implementation:**

```python
async def generate_monthly_report(month: str, client_id: str = None) -> dict:
    """
    Generate comprehensive monthly report.
    month: "2026-01" format
    client_id: specific client or None for agency-wide
    """
    year, mo = month.split("-")
    start = f"{month}-01T00:00:00Z"
    end = f"{month}-{calendar.monthrange(int(year), int(mo))[1]}T23:59:59Z"

    # Previous month for comparison
    prev_month = (parse_date(f"{month}-01") - timedelta(days=1)).strftime("%Y-%m")
    prev_start = f"{prev_month}-01T00:00:00Z"
    prev_end = f"{prev_month}-{calendar.monthrange(*map(int, prev_month.split('-')))[1]}T23:59:59Z"

    # === Parallel Data Collection ===
    data = {}

    # GHL data
    data["contacts"] = await ghl.get_contacts(dateAdded_gte=start, dateAdded_lte=end)
    data["prev_contacts"] = await ghl.get_contacts(dateAdded_gte=prev_start, dateAdded_lte=prev_end)
    data["opportunities"] = await ghl.get_opportunities(dateRange=(start, end))
    data["prev_opportunities"] = await ghl.get_opportunities(dateRange=(prev_start, prev_end))

    # External data
    if client_id:
        client_config = await get_client_config(client_id)
        data["seo"] = await dataforseo.get_monthly_overview(client_config["domain"], month)
        data["analytics"] = await get_google_analytics(client_config["ga_property"], start, end)

    # === Analysis ===
    report = {
        "month": month,
        "executive_summary": [],  # AI-generated after analysis
        "lead_generation": analyze_lead_generation(data),
        "pipeline": await calculate_pipeline_analytics(PIPELINES["client_acquisition"], f"{start}:{end}"),
        "revenue": analyze_revenue(data["opportunities"], data["prev_opportunities"]),
        "channels": analyze_channel_performance(data["contacts"]),
        "enrichment": analyze_enrichment_metrics(data["contacts"]),
    }

    if client_id:
        report["seo"] = analyze_seo_performance(data.get("seo")),
        report["advertising"] = analyze_ad_performance(data.get("analytics"))

    # === AI-Generated Insights ===
    report["executive_summary"] = await generate_executive_summary(report)
    report["recommendations"] = await generate_recommendations(report)
    report["next_month_goals"] = await suggest_goals(report)

    # === Charts ===
    report["charts"] = await generate_monthly_charts(report, data)

    return report
```

### 4. Ad-Hoc Queries

**Purpose:** Answer specific questions about CRM data in natural language.

**Example Queries and Implementation:**

```python
# Natural language -> structured query mapping

QUERY_PATTERNS = {
    "how many leads came in last week": {
        "type": "count",
        "entity": "contacts",
        "date_range": "last_week",
        "response": "You received {count} new leads last week."
    },
    "how many leads from google": {
        "type": "count",
        "entity": "contacts",
        "filter": {"source": "google"},
        "response": "{count} leads came from Google ({period})."
    },
    "what's our conversion rate": {
        "type": "calculated",
        "formula": "won_deals / total_deals * 100",
        "response": "Your conversion rate is {rate}% ({won}/{total} deals)."
    },
    "who are our hottest leads": {
        "type": "query",
        "entity": "contacts",
        "sort": "pain_score_desc",
        "limit": 5,
        "filter": {"status": "open"},
        "response": "Top 5 hottest leads:\n{formatted_list}"
    },
    "how long does it take to close a deal": {
        "type": "calculated",
        "formula": "avg_days_in_pipeline(won_deals)",
        "response": "Average time to close: {avg_days} days (median: {median_days} days)."
    }
}

async def handle_ad_hoc_query(query: str) -> str:
    """
    Process a natural language CRM query.
    Uses AI to parse intent, then executes structured query.
    """
    # 1. AI parses the natural language query into structured parameters
    parsed = await ai_parse_query(query)

    # 2. Execute the appropriate GHL API calls
    if parsed["type"] == "count":
        result = await ghl.count_contacts(
            filters=parsed.get("filters", {}),
            date_range=parsed.get("date_range")
        )
        return format_count_response(parsed, result)

    elif parsed["type"] == "list":
        results = await ghl.search_contacts(
            filters=parsed.get("filters", {}),
            sort=parsed.get("sort"),
            limit=parsed.get("limit", 10)
        )
        return format_list_response(parsed, results)

    elif parsed["type"] == "calculated":
        data = await fetch_calculation_data(parsed)
        result = calculate_metric(parsed["formula"], data)
        return format_calculated_response(parsed, result)

    elif parsed["type"] == "comparison":
        current = await fetch_period_data(parsed["period_1"])
        previous = await fetch_period_data(parsed["period_2"])
        return format_comparison_response(parsed, current, previous)
```

## Data Sources Integration

### GHL API Data

| Data Point | API Endpoint | Refresh Rate |
|-----------|-------------|--------------|
| Contact list | GET /contacts/ | Real-time |
| Contact details | GET /contacts/{id} | Real-time |
| Opportunities | GET /opportunities/search | Real-time |
| Pipeline stages | GET /opportunities/pipelines | Real-time |
| Conversations | GET /conversations/ | Real-time |
| Tasks | GET /contacts/{id}/tasks | Real-time |
| Calendar events | GET /calendars/events | Real-time |

### Enrichment Data (Stored in GHL Custom Fields)

| Data Point | Custom Field | Source |
|-----------|-------------|--------|
| Pain score | pain_score | Enrichment flow |
| Google rating | google_rating | Google Places |
| Review count | review_count | Google Places |
| Website platform | website_platform | BuiltWith |
| Organic traffic | organic_traffic | DataForSEO |
| Domain authority | domain_authority | DataForSEO |
| Enrichment date | enrichment_date | Enrichment flow |

### External Analytics

| Source | Data Available | Integration Method |
|--------|---------------|-------------------|
| Google Analytics | Traffic, sessions, conversions, channels | GA4 API or DataForSEO |
| Google Ads | Clicks, impressions, CPC, conversions, spend | Google Ads API |
| Facebook Ads | Reach, clicks, leads, spend, ROAS | Facebook Marketing API |
| DataForSEO | Rankings, keywords, backlinks, competitors | DataForSEO REST API |
| Google Search Console | Impressions, clicks, CTR, positions | Search Console API |

## Report Delivery Channels

### Email Delivery

```python
async def deliver_report_email(report: dict, recipients: list,
                                report_type: str = "daily"):
    """Deliver report via email with formatted HTML and optional attachments."""

    # Generate HTML email body
    html_body = render_email_template(report, report_type)

    # Generate PDF attachment for monthly reports
    attachments = []
    if report_type == "monthly":
        pdf_path = await generate_report_pdf(report)
        attachments.append(pdf_path)

    # Generate presentation attachment if requested
    if report.get("include_presentation"):
        pptx_path = await generate_report_presentation(report)
        attachments.append(pptx_path)

    # Send via GHL or direct SMTP
    for recipient in recipients:
        await send_email(
            to=recipient,
            subject=f"{report_type.title()} Report - {report['period']}",
            html_body=html_body,
            attachments=attachments
        )
```

### Slack Delivery

```python
async def deliver_report_slack(report: dict, channel: str,
                                report_type: str = "daily"):
    """Deliver report as formatted Slack message."""

    if report_type == "daily":
        message = format_daily_summary_slack(report)
        await slack.send_message(channel=channel, message=message)

    elif report_type == "weekly":
        # Send summary as message
        message = format_weekly_summary_slack(report)
        await slack.send_message(channel=channel, message=message)

        # Upload charts as images
        for chart_name, chart_buffer in report.get("charts", {}).items():
            await slack.upload_file(
                channel=channel,
                file=chart_buffer,
                filename=f"{chart_name}.png",
                title=chart_name.replace("_", " ").title()
            )

    elif report_type == "monthly":
        # Send executive summary
        await slack.send_message(
            channel=channel,
            message=format_monthly_highlights_slack(report)
        )
        # Upload full report as PDF
        pdf = await generate_report_pdf(report)
        await slack.upload_file(channel=channel, file=pdf, filename="monthly_report.pdf")
```

### Telegram Delivery

```python
async def deliver_report_telegram(report: dict, chat_id: str,
                                   report_type: str = "daily"):
    """Deliver report via Telegram bot."""
    if report_type == "daily":
        message = format_daily_summary_telegram(report)
        await telegram.send_message(chat_id=chat_id, message=message, parse_mode="Markdown")
    elif report_type in ["weekly", "monthly"]:
        # Send summary text
        await telegram.send_message(chat_id=chat_id,
                                     message=format_summary_telegram(report))
        # Send key charts as photos
        for chart_name in ["funnel", "trends", "channels"]:
            if chart_name in report.get("charts", {}):
                await telegram.send_photo(
                    chat_id=chat_id,
                    photo=report["charts"][chart_name],
                    caption=chart_name.replace("_", " ").title()
                )
```

### Presentation Delivery

For monthly reports, generate a full presentation (see `presentations/templates.md`):

```python
async def deliver_report_presentation(report: dict, client_config: dict):
    """Generate and deliver monthly report as a presentation."""
    # Use the monthly_report template
    pptx_path = await generate_presentation({
        "type": "client_report",
        "client": client_config["name"],
        "template": "monthly_report",
        "data": report,
        "branding": client_config["brand"]
    })

    # Also create Google Slides version for sharing
    slides_url = await create_google_slides_report({
        "template_id": client_config.get("gslides_template_id"),
        "title": f"{client_config['name']} - {report['month']} Report",
        "data": report,
        "share_with": [client_config["contact_email"]]
    })

    return {"pptx": pptx_path, "slides_url": slides_url}
```

### Airtable Delivery

Store report data in Airtable for historical tracking and dashboard creation:

```python
async def store_report_airtable(report: dict, report_type: str):
    """Store report metrics in Airtable for tracking."""
    record = {
        "Report Date": report["period"],
        "Report Type": report_type,
        "Total Leads": report["lead_generation"]["total"],
        "Qualified Leads": report["lead_generation"]["qualified"],
        "Deals Won": report["pipeline"]["summary"]["won_deals"],
        "Revenue Won": report["revenue"]["total_won"],
        "Win Rate": report["pipeline"]["conversion_rates"].get("closed_won", 0),
        "Avg Deal Value": report["revenue"]["avg_deal_value"],
        "Pipeline Value": report["pipeline"]["summary"]["total_value"],
        "Top Source": report["channels"]["top_source"],
        "Report URL": report.get("report_url", ""),
    }

    await airtable.create_record(
        base_id=AIRTABLE_REPORTING_BASE,
        table_name="Monthly Reports",
        fields=record
    )
```

## Automated Scheduling

### Schedule Configuration

```python
REPORT_SCHEDULE = {
    "daily_summary": {
        "frequency": "daily",
        "time": "08:00",
        "timezone": "America/Chicago",
        "delivery": ["slack:#daily-report", "telegram:owner_chat"],
        "recipients": ["team@agency.com"]
    },
    "weekly_pipeline": {
        "frequency": "weekly",
        "day": "monday",
        "time": "08:00",
        "timezone": "America/Chicago",
        "delivery": ["slack:#weekly-pipeline", "email"],
        "recipients": ["team@agency.com", "leadership@agency.com"]
    },
    "monthly_performance": {
        "frequency": "monthly",
        "day": 1,  # 1st of each month
        "time": "09:00",
        "timezone": "America/Chicago",
        "delivery": ["email", "slack:#monthly-report", "airtable", "presentation"],
        "recipients": ["team@agency.com", "leadership@agency.com"]
    }
}
```

### Scheduler Implementation

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

def setup_report_schedules():
    """Set up all automated report schedules."""

    # Daily at 8 AM
    scheduler.add_job(
        run_daily_report,
        'cron',
        hour=8,
        minute=0,
        timezone='America/Chicago',
        id='daily_report'
    )

    # Weekly on Monday at 8 AM
    scheduler.add_job(
        run_weekly_report,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        timezone='America/Chicago',
        id='weekly_report'
    )

    # Monthly on the 1st at 9 AM
    scheduler.add_job(
        run_monthly_report,
        'cron',
        day=1,
        hour=9,
        minute=0,
        timezone='America/Chicago',
        id='monthly_report'
    )

    scheduler.start()

async def run_daily_report():
    """Execute daily report generation and delivery."""
    try:
        report = await generate_daily_summary()
        config = REPORT_SCHEDULE["daily_summary"]

        for delivery in config["delivery"]:
            if delivery.startswith("slack:"):
                channel = delivery.split(":")[1]
                await deliver_report_slack(report, channel, "daily")
            elif delivery.startswith("telegram:"):
                chat_id = delivery.split(":")[1]
                await deliver_report_telegram(report, chat_id, "daily")
            elif delivery == "email":
                await deliver_report_email(report, config["recipients"], "daily")

        logger.info(f"Daily report delivered successfully for {report['date']}")
    except Exception as e:
        logger.error(f"Daily report failed: {e}")
        await slack.send_message("#alerts", f"Daily report generation failed: {e}")
```

## Natural Language Queries

### Example Queries and Expected Responses

| Query | Data Needed | Response Format |
|-------|-------------|-----------------|
| "How many leads came in last week?" | Contacts by date | "Last week (Jan 20-26): 47 new leads, up 12% from the week before." |
| "What's our best lead source this month?" | Contacts by source | "Google Ads leads with 34 leads (42% of total), followed by SEO with 19 leads." |
| "Show me deals closing this week" | Opportunities in late stages | "3 deals expected to close this week: [list with values]" |
| "How is the pipeline looking?" | Full pipeline snapshot | Formatted pipeline summary with stage counts and values |
| "Compare January to December" | Two months of data | Side-by-side comparison with changes highlighted |
| "Which industry has the highest win rate?" | Opportunities by industry tag | "HVAC has the highest win rate at 28%, followed by Plumbing at 24%." |
| "Who hasn't been contacted yet?" | Open deals in New Lead/Qualified | "12 qualified leads haven't been contacted yet: [list]" |

### AI Query Parser

```python
async def parse_crm_query(natural_query: str) -> dict:
    """
    Use Claude/LLM to parse natural language CRM query into structured format.
    """
    system_prompt = """You are a CRM query parser. Convert natural language questions
    about CRM data into structured query parameters. Available entities: contacts,
    opportunities, tasks, conversations. Available filters: date_range, source,
    industry, stage, status, score_range, tags. Return JSON."""

    response = await llm.complete(
        system=system_prompt,
        user=natural_query,
        response_format="json"
    )

    return json.loads(response)
```

## Benchmarking and Comparison

### Period Comparison

```python
async def compare_periods(period_1: str, period_2: str) -> dict:
    """Compare two time periods across all metrics."""
    data_1 = await gather_all_metrics(period_1)
    data_2 = await gather_all_metrics(period_2)

    comparison = {}
    for metric in data_1:
        val_1 = data_1[metric]
        val_2 = data_2[metric]
        if isinstance(val_1, (int, float)) and isinstance(val_2, (int, float)):
            change = val_1 - val_2
            pct_change = ((val_1 - val_2) / val_2 * 100) if val_2 != 0 else 0
            comparison[metric] = {
                "current": val_1,
                "previous": val_2,
                "change": change,
                "pct_change": round(pct_change, 1),
                "direction": "up" if change > 0 else "down" if change < 0 else "flat"
            }

    return comparison
```

### Source Comparison

```python
async def compare_lead_sources(period: str) -> dict:
    """Compare performance across lead sources."""
    contacts = await ghl.get_contacts(date_range=period)
    opportunities = await ghl.get_opportunities(date_range=period)

    sources = {}
    for contact in contacts:
        source = contact.get("source", "unknown")
        if source not in sources:
            sources[source] = {"leads": 0, "qualified": 0, "won": 0, "revenue": 0, "cost": 0}
        sources[source]["leads"] += 1

        # Check if this contact has a won opportunity
        contact_opps = [o for o in opportunities if o["contactId"] == contact["id"]]
        for opp in contact_opps:
            if opp.get("status") == "won":
                sources[source]["won"] += 1
                sources[source]["revenue"] += opp.get("monetaryValue", 0)

    # Calculate derived metrics
    for source in sources:
        s = sources[source]
        s["conversion_rate"] = (s["won"] / s["leads"] * 100) if s["leads"] > 0 else 0
        s["avg_deal_value"] = (s["revenue"] / s["won"]) if s["won"] > 0 else 0
        s["cost_per_lead"] = (s["cost"] / s["leads"]) if s["leads"] > 0 else 0
        s["roi"] = ((s["revenue"] - s["cost"]) / s["cost"] * 100) if s["cost"] > 0 else 0

    return sources
```

## Actionable Insights Engine

The reporting system should not just present data but generate actionable recommendations.

```python
async def generate_recommendations(report: dict) -> list:
    """
    AI-generated recommendations based on report data.
    Each recommendation includes: finding, recommendation, expected impact, priority.
    """
    recommendations = []

    # Rule-based insights
    lead_data = report["lead_generation"]
    pipeline_data = report["pipeline"]

    # Insight: Lead source optimization
    sources = report.get("channels", {})
    if sources:
        best_source = max(sources.items(), key=lambda x: x[1].get("conversion_rate", 0))
        worst_source = min(sources.items(), key=lambda x: x[1].get("conversion_rate", 0))
        if best_source[1]["conversion_rate"] > worst_source[1]["conversion_rate"] * 2:
            recommendations.append({
                "finding": f"{best_source[0]} converts at {best_source[1]['conversion_rate']:.1f}%, "
                           f"while {worst_source[0]} converts at {worst_source[1]['conversion_rate']:.1f}%.",
                "recommendation": f"Consider reallocating budget from {worst_source[0]} to {best_source[0]}.",
                "expected_impact": "Improved overall conversion rate and lower cost per acquisition.",
                "priority": "high"
            })

    # Insight: Pipeline bottleneck
    velocity = pipeline_data.get("velocity", {})
    for stage, data in velocity.items():
        if data["avg_days"] > STALE_THRESHOLDS.get(stage, timedelta(days=999)).days * 0.8:
            recommendations.append({
                "finding": f"Deals are spending an average of {data['avg_days']:.1f} days in "
                           f"'{stage}', approaching the stale threshold.",
                "recommendation": f"Review and streamline the '{stage}' stage process. "
                                  f"Consider additional follow-up automation.",
                "expected_impact": "Faster pipeline velocity and improved close rate.",
                "priority": "medium"
            })

    # Insight: Win rate trend
    if report.get("revenue", {}).get("win_rate_change", 0) < -5:
        recommendations.append({
            "finding": f"Win rate declined by {abs(report['revenue']['win_rate_change']):.1f}% this month.",
            "recommendation": "Review recent lost deals for patterns. Consider updating proposal "
                              "templates or adjusting qualification criteria.",
            "expected_impact": "Stabilize or improve win rate to protect revenue growth.",
            "priority": "high"
        })

    # AI-generated insights for nuanced analysis
    ai_insights = await generate_ai_insights(report)
    recommendations.extend(ai_insights)

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return recommendations[:5]  # Top 5 recommendations

async def generate_ai_insights(report: dict) -> list:
    """Use LLM to generate nuanced insights that rule-based logic might miss."""
    prompt = f"""
    Analyze this CRM report data and generate 2-3 actionable insights:

    Lead Generation: {json.dumps(report.get('lead_generation', {}), indent=2)}
    Pipeline: {json.dumps(report.get('pipeline', {}).get('summary', {}), indent=2)}
    Revenue: {json.dumps(report.get('revenue', {}), indent=2)}
    Channel Performance: {json.dumps(report.get('channels', {}), indent=2)}

    For each insight, provide:
    1. Finding (specific data observation)
    2. Recommendation (actionable next step)
    3. Expected impact (what improvement to expect)
    4. Priority (high/medium/low)

    Focus on non-obvious patterns and strategic recommendations.
    """

    response = await llm.complete(system="You are a marketing analytics expert.", user=prompt)
    return parse_ai_insights(response)
```

## Multi-Source Comprehensive View

### Data Aggregation Layer

```python
async def build_comprehensive_view(client_id: str, period: str) -> dict:
    """
    Pull data from ALL sources to build a 360-degree view.
    Used for monthly reports and strategic reviews.
    """
    view = {}

    # CRM data (GHL)
    view["crm"] = {
        "contacts": await ghl.get_contacts(date_range=period),
        "opportunities": await ghl.get_opportunities(date_range=period),
        "conversations": await ghl.get_conversations_summary(date_range=period),
        "tasks": await ghl.get_tasks_summary(date_range=period)
    }

    # Enrichment data (stored in GHL custom fields, aggregated)
    view["enrichment"] = {
        "avg_pain_score": calculate_avg_pain_score(view["crm"]["contacts"]),
        "enrichment_success_rate": calculate_enrichment_rate(view["crm"]["contacts"]),
        "top_industries": get_industry_distribution(view["crm"]["contacts"]),
        "cost_per_enriched_lead": calculate_enrichment_cost(view["crm"]["contacts"])
    }

    # SEO data (DataForSEO)
    client_config = await get_client_config(client_id)
    if client_config.get("domain"):
        view["seo"] = await dataforseo.get_comprehensive_report(
            client_config["domain"], period
        )

    # Analytics data
    if client_config.get("ga_property"):
        view["analytics"] = await google_analytics.get_report(
            client_config["ga_property"], period
        )

    # Activity logs
    view["activity"] = {
        "emails_sent": count_messages(view["crm"]["conversations"], "Email", "outbound"),
        "sms_sent": count_messages(view["crm"]["conversations"], "SMS", "outbound"),
        "calls_made": count_messages(view["crm"]["conversations"], "Call", "outbound"),
        "responses_received": count_messages(view["crm"]["conversations"], type=None, direction="inbound")
    }

    return view
```

## Visualization Integration

All reports should leverage the chart generation capabilities documented in `presentations/data-visualization.md`. Key charts for each report type:

| Report | Charts Included |
|--------|----------------|
| Daily Summary | None (text-only for speed) |
| Weekly Pipeline | Funnel chart, pipeline value bar chart |
| Monthly Performance | Lead trend line, channel pie, funnel, revenue waterfall, competitor radar |
| Ad-Hoc | Depends on query type |

## Performance and Caching

```python
# Cache expensive computations
REPORT_CACHE = {}

async def get_or_generate_report(report_type: str, params: dict,
                                  cache_ttl: int = 3600) -> dict:
    """Cache reports to avoid regeneration for repeated requests."""
    cache_key = f"{report_type}:{json.dumps(params, sort_keys=True)}"

    if cache_key in REPORT_CACHE:
        cached = REPORT_CACHE[cache_key]
        if time.time() - cached["timestamp"] < cache_ttl:
            return cached["data"]

    # Generate fresh report
    generators = {
        "daily": generate_daily_summary,
        "weekly": generate_weekly_pipeline_report,
        "monthly": generate_monthly_report,
    }

    report = await generators[report_type](**params)

    REPORT_CACHE[cache_key] = {
        "data": report,
        "timestamp": time.time()
    }

    return report
```

## References

- GHL API documentation: https://highlevel.stoplight.io/docs/integrations
- Data visualization: see `../presentations/data-visualization.md`
- Presentation templates: see `../presentations/templates.md`
- Pipeline automation: see `pipeline-automation.md`
- Contact enrichment flow: see `contact-enrichment-flow.md`

# Airtable Content Calendar

> Managing marketing content creation, scheduling, and performance tracking through Airtable + OpenClaw.

---

## Content Calendar Table Structure

### Table: Content Calendar

| Field Name | Field Type | Options/Notes |
|---|---|---|
| **Title** | Single line text | Content headline or working title |
| **Content Type** | Single select | Blog Post, Social Post, Email, Video, Infographic, Case Study, Landing Page, Ad Copy, Newsletter |
| **Platform** | Single select | LinkedIn, Facebook, Instagram, Twitter/X, Blog, Email, YouTube, TikTok, Google Ads, Meta Ads |
| **Status** | Single select | Idea, Brief Created, Drafted, In Review, Approved, Scheduled, Published, Archived |
| **Due Date** | Date | When the content should be ready |
| **Publish Date** | Date | When the content goes live |
| **Publish Time** | Single line text | Time of day to publish (e.g., "10:00 AM EST") |
| **Author** | Single select | Team member or "OpenClaw AI" |
| **Reviewer** | Single select | Who reviews before publishing |
| **Industry** | Single select | Dental, HVAC, Legal, Restaurant, Medical, Home Services, General |
| **Brief** | Long text | Content brief, outline, key points to cover |
| **Draft Copy** | Long text | Full draft content |
| **Final Copy** | Long text | Approved, ready-to-publish content |
| **Hashtags** | Single line text | Comma-separated hashtags |
| **Keywords** | Single line text | SEO target keywords |
| **Assets** | Attachment | Images, videos, graphics |
| **Published URL** | URL | Link to published content |
| **Campaign** | Single line text | Associated marketing campaign name |
| **Client** | Linked record | If content is for a specific client |
| **Views** | Number | Post-publish metric |
| **Engagement** | Number | Likes, comments, shares combined |
| **Clicks** | Number | Click-throughs |
| **Conversions** | Number | Lead form fills, signups |
| **Engagement Rate** | Formula | `{Engagement} / {Views} * 100` |
| **Notes** | Long text | Internal notes, feedback |
| **Created** | Created time | Auto-populated |
| **Last Modified** | Last modified time | Auto-populated |

### Creating the Table via MCP

```python
# Create content calendar table if it doesn't exist
await airtable_mcp.create_table(
    base_id=CONTENT_BASE_ID,
    table_name="Content Calendar",
    fields=[
        {"name": "Title", "type": "singleLineText"},
        {"name": "Content Type", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Blog Post", "color": "blueLight2"},
                {"name": "Social Post", "color": "greenLight2"},
                {"name": "Email", "color": "yellowLight2"},
                {"name": "Video", "color": "redLight2"},
                {"name": "Infographic", "color": "purpleLight2"},
                {"name": "Case Study", "color": "cyanLight2"},
                {"name": "Landing Page", "color": "orangeLight2"},
                {"name": "Ad Copy", "color": "pinkLight2"},
                {"name": "Newsletter", "color": "grayLight2"},
            ]
        }},
        {"name": "Platform", "type": "singleSelect", "options": {
            "choices": [
                {"name": "LinkedIn"},
                {"name": "Facebook"},
                {"name": "Instagram"},
                {"name": "Twitter/X"},
                {"name": "Blog"},
                {"name": "Email"},
                {"name": "YouTube"},
                {"name": "TikTok"},
                {"name": "Google Ads"},
                {"name": "Meta Ads"},
            ]
        }},
        {"name": "Status", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Idea", "color": "grayLight2"},
                {"name": "Brief Created", "color": "yellowLight2"},
                {"name": "Drafted", "color": "blueLight2"},
                {"name": "In Review", "color": "orangeLight2"},
                {"name": "Approved", "color": "greenLight2"},
                {"name": "Scheduled", "color": "cyanLight2"},
                {"name": "Published", "color": "greenDark1"},
                {"name": "Archived", "color": "grayDark1"},
            ]
        }},
        {"name": "Due Date", "type": "date"},
        {"name": "Publish Date", "type": "date"},
        {"name": "Industry", "type": "singleSelect", "options": {
            "choices": [
                {"name": "Dental"},
                {"name": "HVAC"},
                {"name": "Legal"},
                {"name": "Restaurant"},
                {"name": "Medical"},
                {"name": "Home Services"},
                {"name": "General"},
            ]
        }},
        {"name": "Brief", "type": "multilineText"},
        {"name": "Draft Copy", "type": "multilineText"},
        {"name": "Final Copy", "type": "multilineText"},
        {"name": "Published URL", "type": "url"},
        {"name": "Views", "type": "number", "options": {"precision": 0}},
        {"name": "Engagement", "type": "number", "options": {"precision": 0}},
        {"name": "Clicks", "type": "number", "options": {"precision": 0}},
        {"name": "Notes", "type": "multilineText"},
    ]
)
```

---

## OpenClaw Content Automation

### 1. Generate Content Ideas

OpenClaw analyzes industry trends, competitor content, and past performance to suggest content ideas.

```python
async def generate_content_ideas(industry: str, platform: str, count: int = 5) -> list[dict]:
    """Generate content ideas using AI analysis."""

    # Gather context
    # 1. Check what's been published recently (avoid duplicates)
    recent_content = await airtable_mcp.list_records(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        max_records=20,
    )
    recent_titles = [r["fields"].get("Title", "") for r in recent_content]

    # 2. Check top-performing content (replicate success)
    top_performing = sorted(
        [r for r in recent_content if r["fields"].get("Views", 0) > 0],
        key=lambda r: r["fields"].get("Engagement", 0),
        reverse=True
    )[:5]

    # 3. Use RAG to find relevant industry trends
    trends = await search_documents(
        supabase,
        query=f"trending topics in {industry} marketing 2024",
        content_type="industry_report",
        count=3
    )

    # 4. Generate ideas via LLM
    ideas = await llm.generate(
        prompt=f"""Generate {count} content ideas for {industry} businesses on {platform}.

        Recently published (avoid similar topics):
        {chr(10).join(f'- {t}' for t in recent_titles[:10])}

        Top performing content (replicate these patterns):
        {chr(10).join(f'- {r["fields"].get("Title")} ({r["fields"].get("Views", 0)} views)'
                       for r in top_performing)}

        Current industry trends:
        {chr(10).join(f'- {t["content"][:200]}' for t in trends)}

        For each idea provide:
        1. Title
        2. Content type (educational, case study, industry news, how-to, listicle)
        3. Brief outline (3-5 bullet points)
        4. Target keywords (2-3)
        5. Estimated engagement potential (high/medium/low)
        """,
        output_format="json_list"
    )

    return ideas
```

### 2. Draft Content for Each Calendar Entry

```python
async def draft_content(record_id: str) -> str:
    """Generate a full draft for a content calendar entry."""

    # Get the content brief from Airtable
    record = await airtable_mcp.get_record(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        record_id=record_id,
    )
    fields = record["fields"]
    title = fields.get("Title", "")
    content_type = fields.get("Content Type", "Social Post")
    platform = fields.get("Platform", "LinkedIn")
    industry = fields.get("Industry", "General")
    brief = fields.get("Brief", "")

    # Get platform-specific guidelines
    guidelines = PLATFORM_GUIDELINES.get(platform, {})

    # Get relevant reference material via RAG
    references = await search_documents(
        supabase,
        query=f"{title} {industry} marketing",
        content_type="template" if content_type == "Email" else None,
        count=3
    )

    # Generate the draft
    draft = await llm.generate(
        prompt=f"""Write a {content_type} for {platform} about: {title}

        Industry: {industry}
        Brief: {brief}

        Platform guidelines:
        - Max length: {guidelines.get('max_length', 'No limit')}
        - Tone: {guidelines.get('tone', 'Professional')}
        - Include: {guidelines.get('include', 'Call to action')}

        Reference materials:
        {chr(10).join(f'---{chr(10)}{r["content"][:500]}' for r in references)}

        Write the complete content ready for publishing.
        Include suggested hashtags at the end if applicable.
        """
    )

    # Update the Airtable record with the draft
    await airtable_mcp.update_record(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        record_id=record_id,
        fields={
            "Draft Copy": draft,
            "Status": "Drafted",
        }
    )

    return draft
```

### 3. Schedule Publishing

```python
async def schedule_content(record_id: str, publish_date: str, publish_time: str):
    """Schedule content for publishing via n8n or Buffer API."""

    record = await airtable_mcp.get_record(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        record_id=record_id,
    )
    fields = record["fields"]

    # Update Airtable with schedule
    await airtable_mcp.update_record(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        record_id=record_id,
        fields={
            "Publish Date": publish_date,
            "Publish Time": publish_time,
            "Status": "Scheduled",
        }
    )

    # Trigger n8n workflow to handle actual publishing
    await trigger_n8n_webhook("schedule-content", {
        "content": fields.get("Final Copy") or fields.get("Draft Copy"),
        "platform": fields["Platform"],
        "publish_date": publish_date,
        "publish_time": publish_time,
        "hashtags": fields.get("Hashtags", ""),
        "airtable_record_id": record_id,
    })
```

### 4. Track Performance

```python
async def update_content_performance(record_id: str, metrics: dict):
    """Update content performance metrics after publishing."""
    await airtable_mcp.update_record(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        record_id=record_id,
        fields={
            "Views": metrics.get("views", 0),
            "Engagement": metrics.get("engagement", 0),
            "Clicks": metrics.get("clicks", 0),
            "Conversions": metrics.get("conversions", 0),
            "Status": "Published",
            "Published URL": metrics.get("url", ""),
        }
    )

async def analyze_content_performance():
    """Analyze performance across all published content and suggest optimizations."""

    # Get all published content with metrics
    records = await airtable_mcp.list_records(
        base_id=CONTENT_BASE_ID,
        table_name="Content Calendar",
        max_records=100,
    )

    published = [r for r in records if r["fields"].get("Status") == "Published"
                 and r["fields"].get("Views", 0) > 0]

    # Analyze patterns
    analysis = await llm.generate(
        prompt=f"""Analyze the performance of these published content pieces and provide insights:

        {chr(10).join(f'- {r["fields"]["Title"]} ({r["fields"]["Platform"]}): '
                       f'{r["fields"].get("Views", 0)} views, '
                       f'{r["fields"].get("Engagement", 0)} engagement, '
                       f'{r["fields"].get("Clicks", 0)} clicks'
                       for r in published)}

        Provide:
        1. Top 3 performing content pieces and why they worked
        2. Bottom 3 and what could improve
        3. Best performing platform
        4. Best performing content type
        5. Optimal posting patterns (day of week, time)
        6. Recommendations for next week's content
        """
    )

    return analysis
```

---

## Content Workflow: Full Lifecycle

```
1. IDEATION (OpenClaw generates)
   OpenClaw: "Here are 5 content ideas for dental practices this week"
   -> Creates Airtable records with Status: "Idea"

2. BRIEF CREATION (OpenClaw generates, human approves)
   OpenClaw: "Here's the brief for 'Top 5 Dental SEO Tips'"
   -> Updates record with Brief, Status: "Brief Created"

3. DRAFTING (OpenClaw generates)
   OpenClaw: "Here's the full draft for LinkedIn"
   -> Updates record with Draft Copy, Status: "Drafted"

4. REVIEW (Human reviews in Airtable)
   Human: Reviews in Airtable UI, makes edits, changes status to "Approved"
   -> Status: "In Review" -> "Approved"

5. SCHEDULING (OpenClaw or human)
   OpenClaw: "Scheduling for Thursday 10 AM"
   -> Updates Publish Date/Time, Status: "Scheduled"
   -> Triggers n8n publishing workflow

6. PUBLISHING (n8n executes)
   n8n: Posts to LinkedIn via API
   -> Updates Published URL, Status: "Published"

7. TRACKING (n8n collects, OpenClaw analyzes)
   n8n: Pulls metrics daily for 7 days post-publish
   -> Updates Views, Engagement, Clicks
   OpenClaw: Analyzes performance weekly
   -> Generates insights and recommendations
```

---

## Templates Per Content Type and Platform

### LinkedIn Post Template

```
Hook line (grab attention in first 2 lines)

[3-5 short paragraphs, each 1-2 sentences]

Key takeaway or call to action

---
#hashtag1 #hashtag2 #hashtag3

Character limit: 3,000 (but 1,300 is optimal)
Tone: Professional, educational, slightly conversational
Include: Personal insight or data point
```

### Facebook Post Template

```
[Engaging opening question or statement]

[2-3 paragraphs telling a story or sharing insight]

[Call to action: "Comment below", "Share if you agree", "Click the link"]

[Link if applicable]

Character limit: 63,206 (but 40-80 words is optimal)
Tone: Casual, community-oriented
Include: Question to drive comments, image or video
```

### Instagram Caption Template

```
[Strong opening line - visible before "more"]

[Story or educational content in 2-3 paragraphs]

[Call to action: "Save this post", "Tag someone who needs this"]

.
.
.
#hashtag1 #hashtag2 ... (up to 30 hashtags, 5-10 is optimal)

Character limit: 2,200
Tone: Visual, authentic, educational
Include: Emojis sparingly, line breaks for readability
```

### Blog Post Template

```
# [Title - Include Primary Keyword]

[Hook paragraph: problem statement or intriguing question]

## [Section 1: Problem/Context]
[2-3 paragraphs]

## [Section 2: Solution/Approach]
[2-3 paragraphs with actionable tips]

## [Section 3: Examples/Evidence]
[Case study, data, or examples]

## [Section 4: Implementation]
[Step-by-step guide or checklist]

## Conclusion
[Summary + strong CTA]

Word count: 800-1,500 words (optimal for SEO)
Tone: Authoritative, helpful
Include: Internal links, images, meta description
```

### Email Template

```
Subject: [Curiosity-driven, 6-10 words]
Preview text: [Complement subject line, 40-90 chars]

Hi [First Name],

[Opening: personal, relevant hook - 1-2 sentences]

[Body: value proposition or content - 2-3 short paragraphs]

[CTA: single, clear call to action]

[Button or link]

[Closing: friendly sign-off]

[Signature]

P.S. [Bonus tip or urgency element]

Character limit: Keep under 200 words for sales emails
Tone: Personal, conversational, helpful
Include: One clear CTA, no more than 2 links
```

---

## Scheduling Strategy: Optimal Posting Times

Based on general social media research (adjust based on your audience data):

| Platform | Best Days | Best Times (EST) | Frequency |
|---|---|---|---|
| LinkedIn | Tue, Wed, Thu | 8-10 AM, 12 PM | 3-5x/week |
| Facebook | Wed, Thu, Fri | 9 AM, 1 PM, 3 PM | 3-5x/week |
| Instagram | Mon, Wed, Fri | 11 AM, 2 PM, 7 PM | 3-7x/week |
| Twitter/X | Tue, Wed, Thu | 9 AM, 12 PM | 3-5x/day |
| Blog | Mon, Wed | 10 AM | 1-2x/week |
| Email | Tue, Thu | 10 AM, 2 PM | 1-2x/week |

**Platform-specific notes:**
- **LinkedIn:** Business hours, especially mid-week. Avoid weekends.
- **Facebook:** Slightly later in the day. Include images/video for better reach.
- **Instagram:** More flexible timing. Reels get 2x reach of static posts.
- **Blog:** Early in the week to capture weekday search traffic.
- **Email:** Tuesday and Thursday mornings have highest open rates.

**OpenClaw auto-scheduling logic:**
```python
OPTIMAL_TIMES = {
    "LinkedIn": {"days": ["Tuesday", "Wednesday", "Thursday"], "times": ["09:00", "12:00"]},
    "Facebook": {"days": ["Wednesday", "Thursday", "Friday"], "times": ["09:00", "13:00"]},
    "Instagram": {"days": ["Monday", "Wednesday", "Friday"], "times": ["11:00", "14:00"]},
    "Blog": {"days": ["Monday", "Wednesday"], "times": ["10:00"]},
    "Email": {"days": ["Tuesday", "Thursday"], "times": ["10:00"]},
}

def suggest_publish_time(platform: str, week_start: date) -> tuple[date, str]:
    """Suggest optimal publish date and time for a platform."""
    config = OPTIMAL_TIMES.get(platform, {"days": ["Wednesday"], "times": ["10:00"]})
    # Find the next available day from week_start
    for day_offset in range(7):
        candidate = week_start + timedelta(days=day_offset)
        if candidate.strftime("%A") in config["days"]:
            return candidate, config["times"][0]
    return week_start, "10:00"
```

---

## Performance Benchmarks

Track these metrics to evaluate content effectiveness:

| Metric | Good | Great | Industry Average |
|---|---|---|---|
| LinkedIn engagement rate | > 2% | > 5% | 1.5% |
| Facebook engagement rate | > 1% | > 3% | 0.5% |
| Instagram engagement rate | > 3% | > 6% | 2.5% |
| Blog bounce rate | < 60% | < 40% | 55% |
| Email open rate | > 25% | > 35% | 21% |
| Email click rate | > 3% | > 5% | 2.5% |

---

## RESEARCH GAPS

- [ ] Audit existing Airtable bases for a content calendar table (may already exist)
- [ ] Determine which social media APIs are available for automated posting
- [ ] Test Buffer API as scheduling intermediary
- [ ] Build the content performance collection workflow in n8n
- [ ] Determine if Instagram/Facebook API access requires business verification
- [ ] Create industry-specific content templates for top verticals (dental, HVAC, legal)

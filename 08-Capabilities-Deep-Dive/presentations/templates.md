# Presentation Template System for Marketing Agency

## Overview

A well-designed template system is the backbone of scalable, consistent, and professional presentation generation. Rather than building every presentation from scratch, OpenClaw uses pre-designed master templates that are dynamically populated with client-specific data, branding, and content. This approach ensures visual quality while enabling rapid automated generation.

## Template Categories

### 1. Pitch Deck

**Purpose:** Sell agency services to prospective clients.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | Agency name, tagline, prospect name | Agent input |
| 2. Problem | Pain points specific to prospect's industry | Pain scoring data |
| 3. Solution | Agency services overview | Static + customized |
| 4. Process | How the agency works (4-step visual) | Static |
| 5. Services | Specific services recommended | AI-selected based on prospect needs |
| 6. Case Study 1 | Similar client success story | Case study database |
| 7. Case Study 2 | Another success story | Case study database |
| 8. Results | Key metrics from case studies | Airtable metrics |
| 9. Pricing | Package options, investment levels | Pricing config |
| 10. Team | Key team members | Static |
| 11. Next Steps | Clear CTA, meeting scheduling link | GHL calendar link |
| 12. Contact | Contact details, social links | Static |

**Placeholders:**
```
{{prospect_name}}, {{prospect_industry}}, {{prospect_pain_1}}, {{prospect_pain_2}},
{{service_1}}, {{service_2}}, {{service_3}},
{{case_study_client}}, {{case_study_result}}, {{case_study_metric}},
{{package_basic_price}}, {{package_pro_price}}, {{package_premium_price}},
{{calendar_link}}, {{agent_name}}, {{agent_email}}, {{agent_phone}}
```

### 2. Client Monthly Report

**Purpose:** Report on monthly performance for active clients.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | Client name, report period, agency logo | Config |
| 2. Executive Summary | 3-5 key highlights in bullet points | AI-generated from data |
| 3. KPI Dashboard | Key metrics with MoM comparison | GHL + Analytics |
| 4. Lead Generation | Leads by source, trend chart | GHL contacts API |
| 5. Conversion Funnel | Lead -> Qualified -> Meeting -> Closed | GHL pipeline API |
| 6. Channel Performance | Breakdown by marketing channel | Google Analytics + Ads |
| 7. SEO Performance | Rankings, organic traffic, backlinks | DataForSEO API |
| 8. Paid Advertising | Ad spend, CPC, ROAS, conversions | Google Ads / Facebook Ads |
| 9. Social Media | Engagement, followers, top posts | Social APIs or manual |
| 10. Revenue Impact | Revenue attributed to marketing | GHL pipeline data |
| 11. Competitive Landscape | Competitor movements, opportunities | DataForSEO competitive data |
| 12. Recommendations | 3-5 actionable recommendations | AI-generated from analysis |
| 13. Next Month Plan | Planned activities and goals | Strategy document |
| 14. Thank You | Contact info, next meeting date | Config |

**Placeholders:**
```
{{client_name}}, {{report_period}}, {{report_date}},
{{highlight_1}}, {{highlight_2}}, {{highlight_3}},
{{total_leads}}, {{leads_change_pct}}, {{conversion_rate}}, {{conversion_change}},
{{total_revenue}}, {{revenue_change_pct}}, {{ad_spend}}, {{roas}},
{{chart_leads_trend}}, {{chart_funnel}}, {{chart_channel_breakdown}},
{{chart_seo_rankings}}, {{chart_ad_performance}},
{{recommendation_1}}, {{recommendation_2}}, {{recommendation_3}},
{{next_meeting_date}}, {{account_manager}}
```

### 3. Strategy Proposal

**Purpose:** Present a proposed marketing strategy to a prospective or existing client.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | Proposal title, client name, date | Input |
| 2. Situation Analysis | Current state, market position | Research data |
| 3. Goals & Objectives | SMART goals aligned with client needs | Discovery meeting notes |
| 4. Target Audience | Demographics, psychographics, personas | Industry research |
| 5. Channel Strategy | Recommended channels with rationale | AI recommendation |
| 6. SEO Strategy | Keyword targets, content plan, technical fixes | DataForSEO |
| 7. Paid Media Plan | Platform selection, budget allocation, targeting | Industry benchmarks |
| 8. Content Strategy | Content calendar, formats, distribution | AI-generated |
| 9. Social Media Plan | Platform presence, posting cadence, content types | Research |
| 10. Timeline | 90-day implementation roadmap | Template |
| 11. Budget Allocation | Spend breakdown by channel (pie chart) | Calculated |
| 12. Expected Results | Projected KPIs at 3, 6, 12 months | Modeling |
| 13. Investment | Agency fees and ad spend requirements | Pricing config |
| 14. Why Us | Differentiators, guarantees, testimonials | Static |
| 15. Next Steps | Agreement process, start date, onboarding | Template |

### 4. Campaign Brief

**Purpose:** Outline a specific campaign for client approval or internal execution.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | Campaign name, client, date | Input |
| 2. Campaign Overview | Goals, KPIs, timeline | Strategy document |
| 3. Target Audience | Who we are targeting and why | Research |
| 4. Key Message | Core message, supporting points, tone | Creative brief |
| 5. Channels | Which channels, why, budget per channel | Strategy |
| 6. Creative Direction | Visual style, examples, mood board | AI-generated or curated |
| 7. Content Calendar | Week-by-week content plan | Generated |
| 8. Budget | Detailed budget breakdown | Calculated |
| 9. Success Metrics | How we measure success | KPI definitions |
| 10. Approval | What needs client sign-off | Checklist |

### 5. Competitor Analysis

**Purpose:** Present competitive intelligence findings to a client.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | "Competitive Landscape: [Industry]" | Input |
| 2. Overview | Market map, key players identified | Research |
| 3-7. Competitor Profiles | One slide per top competitor with key data | DataForSEO, BuiltWith, web scraping |
| 8. Comparison Matrix | Side-by-side feature/service comparison table | Compiled data |
| 9. SWOT Analysis | Client strengths, weaknesses, opportunities, threats | AI analysis |
| 10. Digital Presence | SEO, social, ad spend comparison charts | DataForSEO |
| 11. Opportunity Map | Where client can differentiate/win | AI analysis |
| 12. Recommendations | Actionable competitive strategies | AI-generated |

### 6. Industry Overview

**Purpose:** Educate clients on industry trends and market opportunities.

| Slide | Content | Data Source |
|-------|---------|-------------|
| 1. Cover | "[Industry] Market Overview 2026" | Input |
| 2. Market Size | TAM, SAM, SOM with growth rates | Industry research |
| 3. Key Trends | 3-5 major trends affecting the industry | AI research |
| 4. Consumer Behavior | How customers find/choose providers | Survey data, Google Trends |
| 5. Digital Landscape | Online presence benchmarks | DataForSEO aggregate |
| 6. Local Competition | Number of competitors, saturation level | Google Places data |
| 7. Opportunity Areas | Underserved niches, emerging channels | Analysis |
| 8. Benchmarks | Industry average KPIs (CTR, CPC, conversion rates) | Benchmark databases |
| 9. Recommendations | How the client can capitalize on findings | AI-generated |

## Template Components (Standard Across All Templates)

### Cover Slide
- Client/prospect logo (dynamically injected)
- Presentation title
- Date
- Agency logo (bottom corner)
- Optional: subtitle or tagline

### Agenda Slide
- Numbered list of sections
- Visual timeline or step indicator
- Auto-generated from slide titles

### Content Slides
- Title area (top)
- Body area with bullets or paragraphs
- Optional icon or image area
- Consistent padding and margins

### Data Slides
- Title with metric name
- Large KPI number (hero stat)
- Comparison indicator (up/down arrow, percentage change)
- Supporting chart or table
- Data source citation (small text, bottom)

### CTA / Next Steps Slide
- Clear action items numbered
- Meeting scheduling link (GHL calendar)
- Contact information
- Urgency element (limited offer, timeline)

### Contact / Thank You Slide
- Agent name and title
- Phone, email
- Agency website
- Social media links
- QR code to scheduling page (optional)

## Brand Customization System

### Client Brand Config (Stored in Airtable or JSON)

```json
{
    "client_id": "abc_plumbing",
    "brand": {
        "name": "ABC Plumbing",
        "logo_url": "/assets/logos/abc_plumbing.png",
        "colors": {
            "primary": "#1B4D89",
            "secondary": "#E8F0FE",
            "accent": "#FF6B35",
            "text_dark": "#1A1A2E",
            "text_light": "#FFFFFF",
            "background": "#FAFAFA"
        },
        "fonts": {
            "heading": "Montserrat",
            "body": "Open Sans"
        },
        "style": "professional"
    }
}
```

### Dynamic Brand Injection

```python
def apply_branding(presentation, brand_config):
    """Apply client branding to all slides in a presentation."""
    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        # Apply brand fonts
                        if run.font.size and run.font.size >= Pt(20):
                            run.font.name = brand_config["fonts"]["heading"]
                        else:
                            run.font.name = brand_config["fonts"]["body"]

            # Replace logo placeholder
            if shape.name == "client_logo":
                # Replace with client logo image
                pass

    # Apply brand colors to chart series, table headers, etc.
    apply_brand_colors(presentation, brand_config["colors"])
```

## Data-Driven Slide Generation

### Pulling Live Data for Charts

```python
async def generate_report_data(client_id: str, period: str) -> dict:
    """Pull all data needed for monthly report slides."""
    data = {}

    # From GHL API
    data["leads"] = await ghl_api.get_contacts(
        location_id=client_id,
        date_range=period,
        group_by="source"
    )

    # From GHL Pipeline
    data["pipeline"] = await ghl_api.get_opportunities(
        location_id=client_id,
        date_range=period
    )

    # From Google Analytics (via DataForSEO or direct)
    data["traffic"] = await analytics.get_traffic(
        site=client_config["website"],
        period=period
    )

    # From DataForSEO
    data["seo"] = await dataforseo.get_rankings(
        domain=client_config["domain"],
        keywords=client_config["tracked_keywords"]
    )

    return data
```

## Template Storage and Management

### Directory Structure

```
/openclaw/assets/templates/
    pitch_deck/
        pitch_deck_v3.pptx          # Current production template
        pitch_deck_v2.pptx          # Previous version (kept for reference)
        pitch_deck_schema.json      # Required data fields and placeholders
    monthly_report/
        monthly_report_v2.pptx
        monthly_report_schema.json
    strategy_proposal/
        strategy_proposal_v1.pptx
        strategy_proposal_schema.json
    campaign_brief/
        campaign_brief_v1.pptx
        campaign_brief_schema.json
    competitor_analysis/
        competitor_analysis_v1.pptx
        competitor_analysis_schema.json
    industry_overview/
        industry_overview_v1.pptx
        industry_overview_schema.json
```

### Template Schema Example

```json
{
    "template_name": "monthly_report",
    "version": "2.0",
    "description": "Monthly client performance report",
    "slide_count": 14,
    "required_data": {
        "client_name": {"type": "string", "source": "config"},
        "report_period": {"type": "string", "source": "input"},
        "total_leads": {"type": "number", "source": "ghl_api"},
        "leads_change_pct": {"type": "string", "source": "calculated"},
        "chart_leads_trend": {"type": "image", "source": "generated_chart"},
        "recommendation_1": {"type": "string", "source": "ai_generated"}
    },
    "optional_data": {
        "seo_rankings": {"type": "table", "source": "dataforseo"},
        "social_metrics": {"type": "object", "source": "social_api"}
    }
}
```

## AI Template Selection

When the user requests a presentation without specifying which type, OpenClaw should intelligently select the appropriate template:

```python
TEMPLATE_SELECTION_RULES = {
    "pitch_deck": {
        "triggers": ["pitch", "sell", "prospect", "new client", "proposal for new"],
        "context": "prospect or potential client"
    },
    "monthly_report": {
        "triggers": ["monthly report", "performance report", "how are we doing", "metrics"],
        "context": "existing client with active campaigns"
    },
    "strategy_proposal": {
        "triggers": ["strategy", "marketing plan", "channel plan", "proposal"],
        "context": "planning new engagement or campaign"
    },
    "campaign_brief": {
        "triggers": ["campaign", "launch", "brief", "creative"],
        "context": "specific campaign planning"
    },
    "competitor_analysis": {
        "triggers": ["competitor", "competitive", "landscape", "market analysis"],
        "context": "competitive intelligence request"
    },
    "industry_overview": {
        "triggers": ["industry", "market overview", "trends", "benchmarks"],
        "context": "educational or research context"
    }
}
```

## Version Management

### Versioning Strategy

- Major version (v1 -> v2): significant layout or structure changes
- Store all versions; do not delete old templates
- Track which version was used for each generated presentation (for reproducibility)
- A/B test: generate the same report with two template versions and compare client engagement

### Template Update Workflow

1. Design new template version in PowerPoint or Google Slides
2. Save as `.pptx` to templates directory with incremented version
3. Update the schema JSON if placeholders changed
4. Update the active template reference in config
5. Test with sample data before production use
6. Log the template change in the decisions log

## Gamma AI Alternative

For presentations where design quality is the priority and strict template control is not required, OpenClaw can generate presentations through the **Gamma MCP integration** instead of python-pptx templates.

**When to use Gamma instead of templates:**
- Client-facing decks where visual design matters more than exact template control
- Quick turnaround requests (Gamma generates a full deck in under 3 minutes)
- Presentations for industries where you do not have a pre-built template
- When the user requests "make it look good" without specifying a template

**When to use python-pptx templates:**
- Strict branding requirements with pixel-precise layouts
- Recurring reports that must look identical month to month
- Offline generation without internet dependency
- Presentations that embed complex custom charts or data visualizations

See [Gamma MCP Integration](gamma-mcp-integration.md) for full details on the Gamma path, including trigger design, theme selection, and HITL approval flow.

See [Gamma Presentation Skill](../../05-Skills-Development/priority-skills/gamma-presentation-skill.md) for the OpenClaw skill definition.

---

## Quality Assurance Checklist

Before deploying a new template:

- [ ] All placeholder names are consistent with schema
- [ ] Fonts are embeddable or universally available
- [ ] Colors meet contrast accessibility standards (WCAG AA)
- [ ] Charts render correctly with sample data
- [ ] Client logo area accommodates various aspect ratios
- [ ] Slide dimensions are correct (16:9 widescreen)
- [ ] Print/PDF export looks acceptable
- [ ] No broken layouts at different content lengths
- [ ] Speaker notes are included where appropriate
- [ ] File size is reasonable (under 10 MB without images)
